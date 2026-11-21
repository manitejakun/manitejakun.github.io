"""Build the public GitHub Pages artifact from Pages CMS content."""

import json
import re
from datetime import date
from pathlib import Path
from shutil import copyfile
from urllib.parse import unquote, urlsplit

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUTPUT = ROOT / "_site"
SITE_URL = "https://maniteja.me"
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
PORTRAIT_FALLBACK = "/images/profile.svg"
markdown = MarkdownIt("commonmark", {"html": False}).enable("table")
media = set()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def records(collection):
    return [
        {**read(path), "slug": path.stem}
        for path in sorted((CONTENT / collection).glob("*.json"))
    ]


def web_url(value):
    value = (value or "").strip()
    try:
        parts = urlsplit(value)
        if parts.scheme in {"https", "http"} and parts.hostname and not re.search(r"[\s\\]", value):
            return value
    except ValueError:
        pass
    return ""


def local_media(value, folder, extensions):
    path = unquote(value or "")
    if not path.startswith(f"/media/{folder}/") or re.search(r"[?#\\\x00]", path):
        return ""
    relative = Path(path.lstrip("/"))
    if ".." in relative.parts or any(part.startswith(".") for part in relative.parts):
        return ""
    source = ROOT / relative
    if source.suffix.lower() not in extensions or not source.is_file():
        return ""
    media.add(relative)
    return value


def image(value):
    return local_media(value, "images", IMAGE_TYPES)


def pdf(value):
    return local_media(value, "documents", {".pdf"})


def render_markdown_image(tokens, index, options, env):
    token = tokens[index]
    if not image(token.attrGet("src")):
        return ""
    token.attrSet("loading", "lazy")
    token.attrSet("decoding", "async")
    return markdown.renderer.image(tokens, index, options, env)


markdown.renderer.rules["image"] = render_markdown_image


def richtext(value):
    return Markup(markdown.render(value or ""))


def date_label(value, style="%d %b %Y"):
    if not value:
        return ""
    try:
        return date.fromisoformat(str(value)[:10]).strftime(style).lstrip("0")
    except ValueError:
        return ""


def order_key(item):
    value = item.get("order")
    return (100 if value is None or value == "" else float(value)), item["slug"]


def timeline():
    education = [
        {
            **item, "kind": "Education", "title": item["degree"],
            "organization": item["institution"], "detail": item.get("department"),
            "start": item.get("start_year"),
            "end": item.get("end_year"),
        }
        for item in records("education")
    ]
    experience = [
        {
            **item, "kind": "Experience", "title": item["position"],
            "detail": item.get("employment_type"),
            "start": date_label(item.get("start_date"), "%b %Y"),
            "end": date_label(item.get("end_date"), "%b %Y"),
        }
        for item in records("experience")
    ]
    return sorted(education + experience, key=order_key)


def output_file(relative, *, text=None):
    target = OUTPUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if text is None:
        copyfile(ROOT / relative, target)
    else:
        target.write_text(text, encoding="utf-8")


def build():
    if OUTPUT.exists():
        from shutil import rmtree
        rmtree(OUTPUT)
    media.clear()

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters.update(
        web_url=web_url, image=image, pdf=pdf, markdown=richtext, date_label=date_label,
    )
    profile = read(CONTENT / "profile.json")
    socials = read(CONTENT / "social.json")
    writing = sorted(
        (item for item in records("writing") if item.get("status") == "published"),
        key=lambda item: item.get("publication_date") or "",
        reverse=True,
    )
    photos = []
    for item in sorted(records("photos"), key=order_key):
        source = image(item.get("image"))
        if source:
            photos.append({**item, "image": source})
    env.globals.update(
        site_url=SITE_URL, profile=profile, portrait=image(profile.get("photo")) or PORTRAIT_FALLBACK,
        year=date.today().year,
    )

    output_file("index.html", text=env.get_template("home.html").render(
        socials=socials,
        timeline=timeline(),
        projects=sorted(records("projects"), key=order_key),
        achievements=sorted(records("achievements"), key=lambda item: item.get("event_date") or "", reverse=True),
        publications=sorted(records("publications"), key=lambda item: item.get("year") or 0, reverse=True),
        writing=writing,
        photos=photos,
    ))
    article = env.get_template("article.html")
    for item in writing:
        output_file(f"writing/{item['slug']}/index.html", text=article.render(article=item))

    for relative in (
        "CNAME", "style.css", "interactions.js", "images/favicon.svg", "images/profile.svg",
        "images/social.svg", "images/sculpture.webp", "fonts/inter-latin.woff2",
        "fonts/caveat-latin.woff2", "fonts/OFL-Inter.txt", "fonts/OFL-Caveat.txt",
    ):
        output_file(relative)
    for relative in sorted(media):
        output_file(relative)


if __name__ == "__main__":
    build()
