"""Run behind HTTPS on studio.maniteja.me with a persistent private volume."""
import base64
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
from datetime import date
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Flask, abort, jsonify, redirect, request, send_file, session
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
OWNER = "manitejakun"
REPO = f"https://api.github.com/repos/{OWNER}/{OWNER}.github.io"
ORIGIN = "https://studio.maniteja.me"
app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ["SESSION_SECRET"], SESSION_COOKIE_SECURE=True,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=10_000_000)

def remote(url, data=None, token=None, method=None):
    headers = {"Accept":"application/json","User-Agent":"Maniteja-Studio","Content-Type":"application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(url, data=json.dumps(data).encode() if data else None,
                         headers=headers, method=method), timeout=20) as response:
        return json.load(response)

def db():
    conn = sqlite3.connect(os.environ["STUDIO_DATABASE"], timeout=20)
    conn.execute("CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY, data TEXT, image BLOB)")
    return conn

@app.before_request
def guard():
    if request.path not in ("/login","/callback") and session.get("owner") != OWNER:
        if request.path == "/": return redirect("/login")
        abort(401)
    if request.method != "GET" and request.headers.get("Origin") != ORIGIN:
        abort(403)

@app.after_request
def private(response):
    response.headers.update({"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow",
                             "X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer",
                             "X-Frame-Options":"DENY"})
    return response

@app.get("/login")
def login():
    session.clear()
    session["state"] = secrets.token_urlsafe(32)
    return redirect("https://github.com/login/oauth/authorize?" + urlencode({
        "client_id":os.environ["GITHUB_CLIENT_ID"],"redirect_uri":ORIGIN+"/callback","state":session["state"]}))

@app.get("/callback")
def callback():
    state = session.pop("state", None)
    if not state or not hmac.compare_digest(state, request.args.get("state","")): abort(403)
    result = remote("https://github.com/login/oauth/access_token", {
        "client_id":os.environ["GITHUB_CLIENT_ID"],"client_secret":os.environ["GITHUB_CLIENT_SECRET"],
        "code":request.args.get("code"),"redirect_uri":ORIGIN+"/callback"})
    if not result.get("access_token"): abort(403)
    if remote("https://api.github.com/user",token=result["access_token"])["login"].lower()!=OWNER: abort(403)
    session.clear()
    session["owner"]=OWNER
    return redirect("/")

@app.post("/logout")
def logout():
    session.clear()
    return "",204

@app.get("/")
def editor(): return send_file(ROOT/"editor.html")

@app.get("/editor.js")
def script(): return send_file(ROOT/"editor.js")

@app.route("/draft/<uuid:key>", methods=["GET","PUT"])
def draft(key):
    with db() as conn:
        if request.method=="PUT":
            payload=request.get_json()
            if not isinstance(payload,dict): abort(400)
            conn.execute("INSERT INTO drafts(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                         (str(key),json.dumps(payload)))
            return "",204
        row=conn.execute("SELECT data FROM drafts WHERE id=?",(str(key),)).fetchone()
        if not row: abort(404)
        return jsonify(json.loads(row[0]))

@app.get("/drafts")
def drafts():
    with db() as conn:
        return jsonify([{"id":k,"title":json.loads(v).get("title") or "Untitled"} for k,v in conn.execute("SELECT id,data FROM drafts ORDER BY rowid DESC")])

@app.route("/cover/<uuid:key>",methods=["GET","PUT"])
def cover(key):
    with db() as conn:
        if request.method=="GET":
            row=conn.execute("SELECT image FROM drafts WHERE id=?",(str(key),)).fetchone()
            if not row or not row[0]: abort(404)
            return send_file(io.BytesIO(row[0]),mimetype="image/webp")
        source=Image.open(request.stream)
        if source.width*source.height>24_000_000: abort(413)
        image=ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1800,1800))
        output=io.BytesIO()
        image.save(output,"WEBP",quality=85)
        if not conn.execute("UPDATE drafts SET image=? WHERE id=?",(output.getvalue(),str(key))).rowcount: abort(404)
        return "",204

@app.post("/publish/<uuid:key>")
def publish(key):
    with db() as conn:
        row=conn.execute("SELECT data,image FROM drafts WHERE id=?",(str(key),)).fetchone()
        if not row: abort(404)
        post=json.loads(row[0])
        slug=post.get("slug","")
        if not re.fullmatch("[a-z0-9]+(?:-[a-z0-9]+)*",slug) or not post.get("body") or not post.get("title"): abort(400)
        date.fromisoformat(post["publication_date"])
        entry={field:post.get(field,"") for field in ("slug","publication_date","title","subtitle","description","cover_alt","cover_caption","body","cover","tags")}
        entry["status"]="published"
        token=os.environ["PUBLISH_KEY"]
        def git(path, data=None, method=None):
            return remote(REPO+path,data,token,method)
        head=git("/git/ref/heads/main")["object"]["sha"]
        tree=git("/git/commits/"+head)["tree"]["sha"]
        path="content/writing/"+slug+".json"
        try: existing=git("/contents/"+path+"?ref="+head)["sha"]
        except HTTPError as err:
            if err.code != 404: raise
            existing=None
        elements=[]
        if row[1]:
            import hashlib
            asset="media/images/"+hashlib.sha256(row[1]).hexdigest()+".webp"
            entry["cover"]="/"+asset
        raw=json.dumps(entry,ensure_ascii=False,indent=2)+"\n"
        import hashlib
        data=raw.encode()
        sha=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        if existing != sha:
            if existing != post.get("source_sha"): abort(409)
            if row[1]:
                blob=git("/git/blobs",{"content":base64.b64encode(row[1]).decode(),"encoding":"base64"})
                elements.append({"path":asset,"mode":"100644","type":"blob","sha":blob["sha"]})
            elements.append({"path":path,"mode":"100644","type":"blob","content":raw})
            new_tree=git("/git/trees",{"base_tree":tree,"tree":elements})["sha"]
            head=git("/git/commits",{"message":"Publish Journal: "+slug,"tree":new_tree,"parents":[head]})["sha"]
            try: git("/git/refs/heads/main",{"sha":head,"force":False},"PATCH")
            except HTTPError as err: abort(409 if err.code in (409,422) else 502)
        post.update(source_sha=sha,cover=entry["cover"])
        conn.execute("UPDATE drafts SET data=? WHERE id=?",(json.dumps(post),str(key)))
        return jsonify(sha=sha,commit=head)

@app.get("/published")
def published():
    prefix=REPO+"/contents/content/writing"
    files=remote(prefix,token=os.environ["PUBLISH_KEY"])
    posts=[]
    for item in files:
        if not item["name"].endswith(".json"): continue
        data=remote(prefix+"/"+item["name"],token=os.environ["PUBLISH_KEY"])
        entry=json.loads(base64.b64decode(data["content"]))
        if entry.get("status")=="published":
            posts.append(dict(entry,slug=entry.get("slug") or item["name"][:-5],source_sha=data["sha"]))
    return jsonify(posts)

@app.get("/preview/<uuid:key>")
def preview(key):
    from jinja2 import Environment,FileSystemLoader,select_autoescape
    import build
    with db() as conn:
        row=conn.execute("SELECT data,image IS NOT NULL FROM drafts WHERE id=?",(str(key),)).fetchone()
    if not row: abort(404)
    post=json.loads(row[0])
    post.update(url="/preview/"+str(key),body_html=build.richtext(post.get("body","")),
                cover_src="/cover/"+str(key) if row[1] else (post.get("cover") or ""))
    env=Environment(loader=FileSystemLoader(ROOT.parent/"templates"),autoescape=select_autoescape())
    env.filters.update(date_label=build.date_label,web_url=build.web_url)
    html=env.get_template("article.html").render(article=post,profile=build.read(build.CONTENT/"profile.json"),
        socials={},site_url="https://maniteja.me",portrait="",projects=[],photos=[],year=date.today().year)

    return html.replace('href="/journal/">← Back to Journal', f'href="/#{key}">← Back to draft')

@app.get("/<path:asset>")
def assets(asset):
    if asset in ("style.css","studio/studio.css") or asset.startswith(("fonts/","images/","media/images/")):
        from flask import send_from_directory
        return send_from_directory(ROOT.parent,asset)
    abort(404)

@app.get("/deployment/<sha>")
def deployment(sha):
    if not re.fullmatch("[0-9a-f]{40}",sha): abort(404)
    result=remote(REPO+"/actions/workflows/pages.yml/runs?event=push&head_sha="+sha)
    runs=result.get("workflow_runs",[])
    if not runs: return jsonify(state="queued")
    run=runs[0]
    state=run.get("conclusion") or run["status"]
    slug=request.args.get("slug","")
    if state=="success" and re.fullmatch("[a-z0-9]+(?:-[a-z0-9]+)*",slug):
        url="https://maniteja.me/journal/"+slug+"/"
        try:
            with urlopen(url,timeout=8) as response:
                if response.status==200: return jsonify(state=state,live=url)
        except OSError: pass
    return jsonify(state=state)
