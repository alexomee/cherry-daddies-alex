#!/usr/bin/env python3
"""Sync the hosted dashboard after a re-render.

  python3 tools/sync_site.py              # regen songs.json -> upload ONLY changed mixes to R2 -> deploy
  python3 tools/sync_site.py --no-deploy  # regen + upload, skip vercel deploy
  python3 tools/sync_site.py --bootstrap  # seed upload-state from current R2 (no upload) + deploy

Change detection is by content hash (songs.json `versions`, written by setlist_dashboard.py).
State of what's on R2 lives in web/.r2-uploaded.json (key -> hash). Only mixes whose hash
changed are re-uploaded; the page's ?v=<hash> then busts the Cloudflare edge cache for exactly
those. Upload happens BEFORE deploy so the new ?v always resolves to fresh origin content.

R2 creds are read from the agentiqa doc into env (never written to disk).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOLS = REPO / "tools"
WEB = REPO / "web"
SONGS = REPO / "music" / "songs"
SONGS_JSON = WEB / "songs.json"
STATE = WEB / ".r2-uploaded.json"
AG = Path.home() / "projects" / "agentiqa"
DOC = AG / "docs" / "plans" / "2026-03-09-preview-release.md"
TMP_MANIFEST = "/tmp/r2_sync_manifest.json"


def creds_env():
    env = dict(os.environ)
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(R2_(?:ENDPOINT|ACCESS_KEY_ID|SECRET_ACCESS_KEY|BUCKET_NAME))=(.*)$', line.strip())
        if m:
            env[m.group(1)] = m.group(2)
    env["R2_PUBLIC_URL"] = "https://releases.agentiqa.com"
    env["NODE_PATH"] = str(AG / "node_modules")   # so require('aws-sdk') resolves
    for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"):
        if not env.get(k):
            sys.exit(f"missing {k} in {DOC}")
    return env


def mix_file(p):
    """same mapping the dashboard uses (kept in step with tools/setlist_dashboard.py)."""
    return {"all": "cue_preview.mp3", "drums": "pb-drums.mp3"}.get(p, f"practice-{p}.mp3")


def desired():
    """key -> {file, ver} for every mix listed in songs.json."""
    d = json.loads(SONGS_JSON.read_text(encoding="utf-8"))
    out = {}
    for st in d["sets"]:
        for s in st["songs"]:
            if not s.get("hasData") or not s.get("slug"):
                continue
            ar = SONGS / s["sid"] / "auto-render"
            vers = s.get("versions") or {}
            for p in s.get("practice", []):
                src = mix_file(p)                       # all -> cue_preview.mp3, drums -> pb-drums.mp3
                out_name = "all.mp3" if p == "all" else src
                f = ar / src
                ver = vers.get(p)
                if ver and f.is_file():
                    out[f"cherry-dash/{s['slug']}/{out_name}"] = {"file": str(f), "ver": ver}
            svers = s.get("stem_versions") or {}
            sdir = ar / "stems"
            for st in s.get("stems", []):
                cid = st["id"]
                sf = sdir / f"{cid}.mp3"
                ver = svers.get(cid)
                if ver and sf.is_file():
                    out[f"cherry-dash/{s['slug']}/stems/{cid}.mp3"] = {"file": str(sf), "ver": ver}
    return out


def main():
    args = sys.argv[1:]
    subprocess.run([sys.executable, str(TOOLS / "setlist_dashboard.py")], check=True)
    want = desired()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    if "--bootstrap" in args:
        STATE.write_text(json.dumps({k: v["ver"] for k, v in want.items()}, indent=0))
        print(f"bootstrapped {len(want)} keys from current R2 (no upload)")
    else:
        changed = {k: v for k, v in want.items() if state.get(k) != v["ver"]}
        print(f"{len(changed)} changed mix(es) of {len(want)}")
        if changed:
            json.dump([{"file": v["file"], "key": k} for k, v in changed.items()],
                      open(TMP_MANIFEST, "w"))
            subprocess.run(["node", str(TOOLS / "r2_upload_mixes.cjs"), TMP_MANIFEST],
                           env=creds_env(), cwd=str(REPO), check=True)
            for k, v in changed.items():
                state[k] = v["ver"]
            STATE.write_text(json.dumps(state, indent=0))
            os.remove(TMP_MANIFEST)

    if "--no-deploy" in args:
        print("skipped deploy (--no-deploy)")
    else:
        subprocess.run(["vercel", "deploy", "--prod", "--yes"], cwd=str(WEB), check=True)


if __name__ == "__main__":
    main()
