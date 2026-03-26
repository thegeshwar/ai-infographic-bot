"""Push a generated post to the Y Vault API on VPS."""
import json
import subprocess
import sys
from pathlib import Path

import httpx


def push(meta_path: str, api_url: str, api_key: str):
    meta = json.loads(Path(meta_path).read_text())
    meta_dir = Path(meta_path).parent
    images = sorted(meta_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    image_filename = images[0].name if images else ""

    payload = {
        "hook": meta.get("hook", ""),
        "headline": meta.get("headline", ""),
        "caption": meta.get("caption", ""),
        "hashtags": meta.get("hashtags", []),
        "body": meta.get("body", []),
        "insight": meta.get("insight", ""),
        "source": meta.get("source", ""),
        "source_url": meta.get("source_url", ""),
        "pillar": meta.get("pillar", ""),
        "template": meta.get("strategy", {}).get("template", ""),
        "html": meta.get("html", ""),
        "image_filename": image_filename,
    }

    if images:
        img_path = images[0]
        subprocess.run([
            "scp", str(img_path),
            "oracle:/opt/y-vault/web/static/images/" + image_filename
        ], check=True)

    resp = httpx.post(
        api_url + "/api/ingest",
        json=payload,
        headers={"Authorization": "Bearer " + api_key},
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    print("Post ingested: id=" + str(result["post_id"]) + ", headline=" + payload["headline"][:50])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m web.push_post <path/to/meta.json> [api_url] [api_key]")
        sys.exit(1)
    url = sys.argv[2] if len(sys.argv) > 2 else "https://y.thegeshwar.com"
    key = sys.argv[3] if len(sys.argv) > 3 else "CHANGE_ME"
    push(sys.argv[1], url, key)
