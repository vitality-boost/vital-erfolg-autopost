#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vital.erfolg - vollautomatischer Instagram-Poster.
Laeuft OHNE PC/Claude, z.B. taeglich per GitHub Actions.

Postet GENAU EIN Item aus vital_erfolg_queue.json auf Instagram.
Nur Instagram, niemals Facebook.

Benoetigte Umgebungsvariablen:
  COMPOSIO_API_KEY   (Pflicht)  - dein Composio API-Key
  COMPOSIO_USER_ID   (optional) - Composio user/entity id, Standard "default"
  GITHUB_REPOSITORY  (auto)     - wird von GitHub Actions gesetzt ("user/repo")
  GITHUB_REF_NAME    (auto)     - Branch-Name, Standard "main"
"""
import os
import sys
import json
import time
import subprocess
import datetime
import urllib.request
from pathlib import Path

from PIL import Image
import ve_render                      # deine Render-Engine (gleicher Ordner)
from composio import Composio

# ---------------------------------------------------------------- Konstanten
IG_USER_ID = "27271701115790072"      # Account-Alias "vital.erfolg"
HERE       = Path(__file__).resolve().parent
QUEUE      = HERE / "vital_erfolg_queue.json"
RENDER_DIR = HERE / "rendered"

API_KEY = os.environ.get("COMPOSIO_API_KEY")
USER_ID = os.environ.get("COMPOSIO_USER_ID", "default")
if not API_KEY:
    sys.exit("FEHLER: Umgebungsvariable COMPOSIO_API_KEY fehlt.")

REPO     = os.environ.get("GITHUB_REPOSITORY", "")
REF      = os.environ.get("GITHUB_REF_NAME", "main")
RAW_BASE = os.environ.get("RAW_BASE") or (
    f"https://raw.githubusercontent.com/{REPO}/{REF}/rendered" if REPO else ""
)

composio = Composio(api_key=API_KEY)

# ---------------------------------------------------------------- Helfer
def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=HERE)

def git_commit_push(paths, message):
    run(["git", "add", *paths])
    run(["git",
         "-c", "user.name=vital-autopost",
         "-c", "user.email=bot@vital.erfolg",
         "commit", "-m", message, "--allow-empty"])
    run(["git", "push"])

def execute(slug, arguments):
    """Fuehrt einen Composio-Tool-Call aus und gibt data zurueck."""
    res = composio.tools.execute(slug, arguments=arguments, user_id=USER_ID)
    d = res if isinstance(res, dict) else getattr(res, "__dict__", {}) or {}
    ok   = d.get("successful", d.get("success"))
    data = d.get("data")
    if ok is False:
        raise RuntimeError(f"{slug} fehlgeschlagen: {d.get('error') or d}")
    return data

def wait_public(url, tries=20, delay=3):
    """Wartet, bis eine URL oeffentlich (HTTP 200) erreichbar ist."""
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(delay)
    return False

# ---------------------------------------------------------------- Hauptlogik
def main():
    data = json.loads(QUEUE.read_text(encoding="utf-8"))
    item = next((x for x in data if x.get("status") == "queued"), None)
    if not item:
        print("Warteschlange leer - bitte neue Posts erstellen.")
        return

    fmt = item.get("format")
    print(f"Poste Item: {item['id']}  Format: {fmt}")

    if not RAW_BASE:
        sys.exit("FEHLER: GITHUB_REPOSITORY/RAW_BASE fehlt - Bilder koennen nicht gehostet werden.")

    # 1) Rendern (PNG) -> JPG konvertieren
    RENDER_DIR.mkdir(exist_ok=True)
    paths = ve_render.render_item(item, str(RENDER_DIR), "auto")
    jpg_names = []
    for p in paths:
        jp = p[:-4] + ".jpg"
        Image.open(p).convert("RGB").save(jp, "JPEG", quality=92)
        jpg_names.append(Path(jp).name)

    # 2) Bilder ins Repo pushen, damit Instagram sie abrufen kann
    git_commit_push(["rendered"], f"render {item['id']}")

    urls = [f"{RAW_BASE}/{n}" for n in jpg_names]
    for u in urls:
        if not wait_public(u):
            sys.exit(f"FEHLER: Bild nicht oeffentlich erreichbar: {u}")

    caption = item["caption"]

    # 3) Posten
    if fmt == "carousel":
        children = []
        for u in urls:
            cd = execute("INSTAGRAM_POST_IG_USER_MEDIA", {
                "ig_user_id": IG_USER_ID, "image_url": u, "is_carousel_item": True,
            })
            children.append(cd["id"])
        parent = execute("INSTAGRAM_POST_IG_USER_MEDIA", {
            "ig_user_id": IG_USER_ID, "media_type": "CAROUSEL",
            "children": children, "caption": caption,
        })
        pub = execute("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {
            "ig_user_id": IG_USER_ID, "creation_id": parent["id"], "max_wait_seconds": 90,
        })
    else:
        cont = execute("INSTAGRAM_POST_IG_USER_MEDIA", {
            "ig_user_id": IG_USER_ID, "image_url": urls[0], "caption": caption,
        })
        pub = execute("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {
            "ig_user_id": IG_USER_ID, "creation_id": cont["id"], "max_wait_seconds": 60,
        })

    media_id = pub["id"]

    # 4) Permalink holen
    perm = execute("INSTAGRAM_GET_IG_MEDIA", {
        "ig_media_id": media_id, "fields": "permalink",
    })
    permalink = perm.get("permalink", "")
    print(f"Gepostet: {item['id']} -> {permalink}")

    # 5) Queue aktualisieren + committen
    item["status"]    = "posted"
    item["permalink"] = permalink
    item["posted_at"] = datetime.date.today().isoformat()
    QUEUE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    git_commit_push(["vital_erfolg_queue.json"], f"posted {item['id']}")

    remaining = sum(1 for x in data if x.get("status") == "queued")
    print(f"Fertig. Noch {remaining} Item(s) in der Warteschlange.")
    if remaining <= 2:
        print("HINWEIS: Warteschlange fast leer - neue Posts erstellen.")

if __name__ == "__main__":
    main()
