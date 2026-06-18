#!/usr/bin/env python3
"""Eyeball-verify each generated JamZone clip in a headless mpv.

For every jamzone clip in songs.tsv, launch a windowed (off-stage) mpv with
the clip's .ass attached, seek to a moment when a real lyric line is on
screen (start of the 2nd/3rd `Now` Dialogue + 1s), and screenshot the burned
subtitle to /tmp/clip_<NN>.png. The PNGs are for a human to eyeball.

Run: tools/lyric-launcher/.venv/bin/python tools/lyric-launcher/verify_clips.py
"""
import csv
import json
import os
import re
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = os.path.join(HERE, "clips")
MANIFEST = os.path.join(HERE, "songs.tsv")
SOCK = "/tmp/vc.sock"


def ass_to_sec(ts):
    # H:MM:SS.cc
    h, m, rest = ts.split(":")
    s, cs = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100.0


def pick_seek(ass_path):
    """Start time of the 2nd or 3rd `Now` Dialogue + 1s (a lyric on screen)."""
    nows = []
    with open(ass_path, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("Dialogue:"):
                continue
            # Dialogue: Layer,Start,End,Style,...
            parts = line.split(",", 9)
            if len(parts) < 4:
                continue
            start, style = parts[1].strip(), parts[3].strip()
            if style == "Now":
                nows.append(ass_to_sec(start))
    if not nows:
        return None
    idx = 2 if len(nows) >= 3 else (1 if len(nows) >= 2 else 0)
    return nows[idx] + 1.0


def ipc(sock, cmd):
    sock.sendall((json.dumps({"command": cmd}) + "\n").encode())
    time.sleep(0.05)


def shoot(mp4, ass, png, seek):
    if os.path.exists(SOCK):
        os.remove(SOCK)
    proc = subprocess.Popen(
        ["mpv", "--idle", "--force-window", "--keep-open", "--mute",
         "--no-terminal", "--geometry=640x360",
         f"--input-ipc-server={SOCK}"],
    )
    try:
        # wait for socket
        for _ in range(100):
            if os.path.exists(SOCK):
                break
            time.sleep(0.05)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        for _ in range(100):
            try:
                s.connect(SOCK)
                break
            except OSError:
                time.sleep(0.05)
        ipc(s, ["loadfile", mp4, "replace", "-1", f"sub-files=%{len(ass)}%{ass}"])
        time.sleep(0.8)
        ipc(s, ["set_property", "pause", False])
        time.sleep(0.3)
        ipc(s, ["seek", str(seek), "absolute", "exact"])
        time.sleep(0.8)
        ipc(s, ["screenshot-to-file", png, "subtitles"])
        time.sleep(0.6)
        s.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if os.path.exists(SOCK):
            os.remove(SOCK)


def main():
    with open(MANIFEST, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["source"] == "jamzone"]

    made = []
    for r in rows:
        nn = f"{int(r['clip']):02d}"
        mp4 = os.path.join(CLIPS, f"{nn}.mp4")
        ass = os.path.join(CLIPS, f"{nn}.ass")
        png = f"/tmp/clip_{nn}.png"
        if not (os.path.exists(mp4) and os.path.exists(ass)):
            print(f"clip {nn} {r['song']}: MISSING mp4/ass")
            continue
        seek = pick_seek(ass)
        if seek is None:
            print(f"clip {nn} {r['song']}: no Now lines, skipping")
            continue
        if os.path.exists(png):
            os.remove(png)
        shoot(mp4, ass, png, seek)
        ok = os.path.exists(png)
        print(f"clip {nn} {r['song']}: seek {seek:.1f}s -> {png} {'OK' if ok else 'NO PNG'}")
        if ok:
            made.append(png)

    print(f"\n{len(made)} screenshots written")
    for p in made:
        print(f"  {p}")


if __name__ == "__main__":
    main()
