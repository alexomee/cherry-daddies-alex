#!/usr/bin/env python3
"""Generate every JamZone lyric clip at its mirrored set number.

Reads songs.tsv and, for each row with source=jamzone, runs make_song_clip.py
with --cat / --index=<clip> / --song=<F + factory_dir> / --title=<song>.
Clip number mirrors the set number (manifest `clip` column).

Run: tools/lyric-launcher/.venv/bin/python tools/lyric-launcher/build_all_clips.py
"""
import csv
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# repo F root = tools/lyric-launcher/../..
REPO_F = os.path.dirname(os.path.dirname(HERE))
PY = os.path.join(HERE, ".venv", "bin", "python")
MAKER = os.path.join(HERE, "make_song_clip.py")
MANIFEST = os.path.join(HERE, "songs.tsv")


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    jam = [r for r in rows if r["source"] == "jamzone"]
    print(f"{len(jam)} jamzone rows\n")

    failures = []
    for r in jam:
        clip = int(r["clip"])
        cat = r["cat"]
        song = os.path.join(REPO_F, r["factory_dir"])
        title = r["song"]
        print(f"=== clip {clip:02d}  {title}  ({cat}) ===")
        proc = subprocess.run(
            [PY, MAKER, "--cat", cat, "--index", str(clip),
             "--song", song, "--title", title],
            capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        if proc.returncode != 0:
            sys.stdout.write(proc.stderr)
            print(f"!!! FAILED clip {clip:02d} ({title})")
            failures.append((clip, title))
        print()

    if failures:
        print(f"{len(failures)} FAILURES: " +
              ", ".join(f"{c:02d} {t}" for c, t in failures))
        sys.exit(1)
    print(f"OK — generated {len(jam)} jamzone clips")


if __name__ == "__main__":
    main()
