"""Build the public GitHub Pages artifact from Pages CMS content."""

import json
import re
from datetime import date
from pathlib import Path
from shutil import copyfile
from unicodedata import normalize
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


def journal_entries():
    entries = []
    used_slugs = set()
    for path in sorted((CONTENT / "writing").glob("*.json")):
        entry = read(path)
        if entry.get("status") != "published":
            continue
        filename_slug = normalize("NFKD", path.stem).encode("ascii", "ignore").decode()
        slug = entry.get("slug") or re.sub(r"[^a-z0-9]+", "-", filename_slug.lower()).strip("-")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"{path.name}: use lowercase letters, numbers and single hyphens for the Journal slug")
        if slug in used_slugs:
            raise ValueError(f"{path.name}: the Journal slug '{slug}' is already in use")
        used_slugs.add(slug)
        try:
            published = date.fromisoformat(str(entry.get("publication_date"))[:10]).isoformat()
        except ValueError as error:
            raise ValueError(f"{path.name}: publication_date must be a valid YYYY-MM-DD date") from error
        entries.append({
            **entry,
            "publication_date": published,
            "url": f"/journal/{slug}/",
            "legacy_name": path.stem if not path.stem.startswith(".") else "",
            "cover_src": image(entry.get("cover")),
            "body_html": richtext(entry.get("body")),
        })
    return sorted(entries, key=lambda entry: (entry["publication_date"], entry["url"]), reverse=True)


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
    writing = journal_entries()
    projects = sorted(records("projects"), key=order_key)
    photos = []
    for item in sorted(records("photos"), key=order_key):
        source = image(item.get("image"))
        if source:
            photos.append({**item, "image": source})
    env.globals.update(
        site_url=SITE_URL, profile=profile, portrait=image(profile.get("photo")) or PORTRAIT_FALLBACK,
        year=date.today().year, socials=socials, projects=projects, photos=photos,
    )

    output_file("index.html", text=env.get_template("home.html").render(
        timeline=timeline(),
        achievements=sorted(records("achievements"), key=lambda item: item.get("event_date") or "", reverse=True),
        publications=sorted(records("publications"), key=lambda item: item.get("year") or 0, reverse=True),
        writing=writing,
    ))
    output_file("journal/index.html", text=env.get_template("journal.html").render(entries=writing))
    article = env.get_template("article.html")
    redirect = env.get_template("redirect.html")
    for item in writing:
        output_file(f"{item['url'].lstrip('/')}index.html", text=article.render(article=item))
        if item["legacy_name"]:
            output_file(
                f"writing/{item['legacy_name']}/index.html",
                text=redirect.render(target=item["url"]),
            )
    output_file("writing/index.html", text=redirect.render(target="/journal/"))

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
