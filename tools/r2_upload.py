#!/usr/bin/env python3
# One-off wrapper: build mix manifest from songs.json, read 4 R2 creds from the
# agentiqa doc into env (NOT written to disk), run the node uploader. Delete after.
import json, os, re, subprocess

REPO = "/Users/alex/projects/cherry-daddies"
AG = os.path.expanduser("~/projects/agentiqa")
DOC = os.path.join(AG, "docs/plans/2026-03-09-preview-release.md")

env = dict(os.environ)
for line in open(DOC, encoding="utf-8"):
    m = re.match(r'^(R2_(?:ENDPOINT|ACCESS_KEY_ID|SECRET_ACCESS_KEY|BUCKET_NAME))=(.*)$', line.strip())
    if m:
        env[m.group(1)] = m.group(2)
env["R2_PUBLIC_URL"] = "https://releases.agentiqa.com"
env["NODE_PATH"] = os.path.join(AG, "node_modules")   # so require('aws-sdk') resolves
for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"):
    assert env.get(k), f"missing {k} in doc"

songs = json.load(open(os.path.join(REPO, "web/songs.json"), encoding="utf-8"))
man = []
for st in songs["sets"]:
    for s in st["songs"]:
        if not s.get("hasData") or not s.get("slug"):
            continue
        slug = s["slug"]
        ar = os.path.join(REPO, "music/songs", s["sid"], "auto-render")
        for p in s.get("practice", []):
            if p == "all":
                f, key = os.path.join(ar, "cue_preview.mp3"), f"cherry-dash/{slug}/all.mp3"
            else:
                f, key = os.path.join(ar, f"practice-{p}.mp3"), f"cherry-dash/{slug}/practice-{p}.mp3"
            if os.path.isfile(f):
                man.append({"file": f, "key": key})

json.dump(man, open("/tmp/r2_manifest.json", "w"))
total_mb = sum(os.path.getsize(x["file"]) for x in man) / 1e6
print(f"manifest: {len(man)} files, {total_mb:.0f} MB -> bucket {env['R2_BUCKET_NAME']} key cherry-dash/<slug>/")

subprocess.run(
    ["node", os.path.join(REPO, "tools/r2_upload_mixes.cjs"), "/tmp/r2_manifest.json"],
    env=env, cwd=REPO, check=True,
)
