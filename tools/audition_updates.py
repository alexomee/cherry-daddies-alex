#!/usr/bin/env python3
"""Ledger of pb-audition updates for web/audition.html ("последнее обновление" + archive by date).

  python3 tools/audition_updates.py              # compare web/songs.json with the ledger, append changes
  python3 tools/audition_updates.py --backfill   # rebuild the ledger from the git history of web/songs.json

An update = a song whose pb-audition content hash (songs.json `versions["pb-audition"]`) changed, i.e. what a
listener hears changed. Songs are matched by slug; only songs of the "12.12 all" set are tracked.

Ledger: web/audition-updates.json
  {"hashes": {slug: hash}, "updates": [{"date": "YYYY-MM-DD", "songs": [{slug, sid, title, artist, ts, new}]}]}
`updates` newest first. setlist_dashboard.py calls update() after writing songs.json.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SONGS_JSON = REPO / "web" / "songs.json"
LEDGER = REPO / "web" / "audition-updates.json"
SET = "12.12 all"


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout


def audition_songs(data):
    """slug -> song record for every song that has a pb-audition version (any set)."""
    out = {}
    for st in data.get("sets", []):
        for s in st.get("songs", []):
            v = (s.get("versions") or {}).get("pb-audition")
            if s.get("slug") and v:
                out.setdefault(s["slug"], s)
    return out


def set_slugs(data):
    for st in data.get("sets", []):
        if st.get("name") == SET:
            return [s["slug"] for s in st["songs"] if s.get("slug")]
    return []


def empty():
    return {"hashes": {}, "updates": []}


def load():
    try:
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty()


def save(led):
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def record(led, data, ts, tracked):
    """Append every tracked song whose hash differs from the ledger. Returns the number of changes."""
    songs = audition_songs(data)
    date = time.strftime("%Y-%m-%d", time.localtime(ts))
    n = 0
    for slug in tracked:
        s = songs.get(slug)
        if not s:
            continue
        h = s["versions"]["pb-audition"]
        old = led["hashes"].get(slug)
        if old == h:
            continue
        led["hashes"][slug] = h
        if not led["updates"] or led["updates"][0]["date"] != date:
            led["updates"].insert(0, {"date": date, "songs": []})
        day = led["updates"][0]["songs"]
        day[:] = [x for x in day if x["slug"] != slug]          # one line per song per day, the latest
        day.append({"slug": slug, "sid": s.get("sid"), "title": s.get("title"), "artist": s.get("artist"),
                    "ts": int(ts), "new": old is None})
        n += 1
    return n



def update(data=None):
    if data is None:
        data = json.loads(SONGS_JSON.read_text(encoding="utf-8"))
    led = load()
    n = record(led, data, time.time(), set_slugs(data))
    save(led)
    return n


def backfill():
    now = json.loads(SONGS_JSON.read_text(encoding="utf-8"))
    tracked = set_slugs(now)
    led = empty()
    log = git("log", "--reverse", "--format=%H %at", "--", "web/songs.json").split()
    commits = list(zip(log[0::2], log[1::2]))
    for sha, at in commits:
        try:
            data = json.loads(git("show", f"{sha}:web/songs.json"))
        except ValueError:
            continue
        record(led, data, int(at), tracked)
    record(led, now, time.time(), tracked)          # the working copy (renders not committed yet)
    # the first day pb-audition existed is the ledger's start: songs seen for the first time then are not news
    if led["updates"]:
        first = led["updates"][-1]
        first["songs"] = [x for x in first["songs"] if not x["new"]]
        led["updates"] = [d for d in led["updates"] if d["songs"]]
    save(led)
    print(f"backfill: {len(commits)} commits, {len(led['updates'])} dates, {len(led['hashes'])} songs")


if __name__ == "__main__":
    if "--backfill" in sys.argv[1:]:
        backfill()
    else:
        print(f"audition updates: {update()} changed")
