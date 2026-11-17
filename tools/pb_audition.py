#!/usr/bin/env python3
"""pb-audition.mp3 = everything the stage plays + lead vocal, to listen on a phone (site "pb audition" button).

usage: tools/pb_audition.py [song substring ...]     (no args = every song of the program, see below)
Mix (Alex, 2026-11-17): pb-other + pb-bass at unity, click -3 dB, cues -3 dB, lead vocal stem
(auto-render/stems/vocal.mp3, already in band key) -3 dB. Length = click.wav (render length).
If the sum clips, the whole mix is lowered together (level differences stay). Songs without
pb-other/pb-bass get no file (nothing to audition). jamzone_render.py calls this after each render.
Only songs of the current program get it (Alex, 2026-11-17): the 28.10 Music Hall sets + the "new songs"
sets of web/songs.json; a stale file of any other song is removed."""
import os, subprocess, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs"); SR = 44100
PARTS = [("pb-other.wav", 0.0), ("pb-bass.wav", 0.0), ("click.wav", -3.0), ("cues.wav", -3.0), ("stems/vocal.mp3", -3.0)]

def dec(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2)

def targets():
    import json
    d = json.load(open(os.path.join(REPO, "web", "songs.json"), encoding="utf-8"))
    return {s["sid"] for st in d["sets"] if str(st.get("cls", "")).startswith("musichall") or "new" in st["name"].lower()
            for s in st["songs"] if s.get("sid")}

def build(sid, tg=None):
    ar = os.path.join(SONGS, sid, "auto-render")
    if sid not in (tg if tg is not None else targets()):
        if os.path.exists(os.path.join(ar, "pb-audition.mp3")): os.remove(os.path.join(ar, "pb-audition.mp3"))
        return None
    if not os.path.exists(os.path.join(ar, "click.wav")): return None
    if not any(os.path.exists(os.path.join(ar, f)) for f in ("pb-other.wav", "pb-bass.wav")): return None
    n = len(dec(os.path.join(ar, "click.wav"))); mix = np.zeros((n, 2), np.float32); used = []
    for f, db in PARTS:
        p = os.path.join(ar, f)
        if not os.path.exists(p): continue
        x = dec(p)[:n]; mix[:len(x)] += x * 10 ** (db / 20); used.append(f.split("/")[-1].split(".")[0])
    pk = float(np.abs(mix).max()); g = 0.97 / pk if pk > 0.97 else 1.0
    out = os.path.join(ar, "pb-audition.mp3")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-b:a", "192k", out], input=(mix * g).astype(np.float32).tobytes(), check=True)
    return f"{'+'.join(used)}" + (f", lowered {20*np.log10(g):.1f} dB" if g < 1 else "")

if __name__ == "__main__":
    q = sys.argv[1:]; tg = targets()
    for sid in sorted(os.listdir(SONGS)):
        if q and not any(a in sid for a in q): continue
        if not os.path.isdir(os.path.join(SONGS, sid)): continue
        r = build(sid, tg)
        if r: print(f"pb-audition: {sid}: {r}", flush=True)
