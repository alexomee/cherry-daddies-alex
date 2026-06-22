#!/usr/bin/env python3
"""Publish the lyric-review package (index.html + every NN.mp4 in the staging dir)
to R2 under temp/<folder>/ on releases.agentiqa.com.

R2 creds are read from the agentiqa doc into env (never written to disk), exactly
like tools/sync_site.py. Content-Type is set by extension (tools/r2_upload_files.cjs)
so the gallery + clips stream inline. Use a NEW versioned <folder> each round —
overwriting an old key serves a stale object off the Cloudflare edge cache.

  build_review_site.py cherry-lyric-review-2026-06-22 /tmp/review_pkg/index.html
  publish_review.py    cherry-lyric-review-2026-06-22 [/tmp/review_pkg]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
AG = Path.home() / "projects" / "agentiqa"
DOC = AG / "docs" / "plans" / "2026-03-09-preview-release.md"
UPLOADER = REPO / "tools" / "r2_upload_files.cjs"


def creds_env():
    env = dict(os.environ)
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(R2_(?:ENDPOINT|ACCESS_KEY_ID|SECRET_ACCESS_KEY|BUCKET_NAME))=(.*)$', line.strip())
        if m:
            env[m.group(1)] = m.group(2)
    env["R2_PUBLIC_URL"] = "https://releases.agentiqa.com"
    env["NODE_PATH"] = str(AG / "node_modules")          # so require('aws-sdk') resolves
    for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"):
        if not env.get(k):
            sys.exit(f"missing {k} in {DOC}")
    return env


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: publish_review.py <folder> [staging_dir=/tmp/review_pkg]")
    folder = sys.argv[1]
    staging = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/review_pkg")
    files = sorted(staging.glob("*.mp4"), key=lambda p: p.name) + [staging / "index.html"]
    man = [{"file": str(f), "key": f"temp/{folder}/{f.name}"} for f in files if f.exists()]
    if not any(m["key"].endswith("index.html") for m in man):
        sys.exit(f"no index.html in {staging} — run build_review_site.py first")
    mf = "/tmp/review_upload_manifest.json"
    json.dump(man, open(mf, "w"))
    print(f"uploading {len(man)} files -> temp/{folder}/")
    subprocess.run(["node", str(UPLOADER), mf], env=creds_env(), cwd=str(REPO), check=True)
    os.remove(mf)
    print(f"\npublic: https://releases.agentiqa.com/temp/{folder}/index.html")


if __name__ == "__main__":
    main()
