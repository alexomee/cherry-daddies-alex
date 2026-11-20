#!/usr/bin/env python3
"""One-off stem prep for «МакSим — Знаешь ли ты» (12.12, 2026-11-20). Rebuildable.

  python3 tools/jamzone/prep_znaesh_li_ty.py import <moises.zip>   # zip -> song root *.wav (renamed, unchanged)
                                                                   #   + moises-orig/ (Moises metronome, count-in)
  python3 tools/jamzone/prep_znaesh_li_ty.py metronome             # synthetic metronome.wav on the drum grid
then: python3 tools/jamzone/jamzone_render.py "МакSим - Знаешь ли ты"

Source: Moises «Знаешь ли ты _minus_-Db minor-64bpm-441hz.zip» — a MINUS (no lead vocal): its «Vocals» stem is
the backing vocals only -> backing_vocals.wav (back-vox role, ceiling-leveled by the render).

Measured on the raw stems (wiki/songs/maksim-znaesh-li-ty.md):
  * tempo dead-constant 63.855 bpm: drum transients (knock 150-1k / snare 1-5k / hats 6-16k spectral flux,
    beat-synchronous fold per 16 beats) sit on one straight line through the whole drum part, ±1 ms, all
    bands agree -> no warp.
  * the Moises metronome is NOT usable: it LAGS the drums by ~37 ms at 84 s growing to ~52 ms at 219 s
    (its own tempo is 63.848, and its intervals are quantized to 20 ms frames: 0.942 / 0.922 s), and
    its first click (raw 1.135 s) is beat 2, not a downbeat: chord changes land on Moises click k%4 == 3
    and the snare on k%4 == 0/2 (= beats 2/4). So bar 1.1 = raw Moises beat k = -1, where the piano
    starts (raw ~0.15 s).
  * no padding/trim: bar 1.1 sits at raw P0 - B = 0.165 s; the stems stay byte-identical to Moises.
Beat index k = raw Moises click index (k=0 at its first click); bar = (k+1)//4 + 1.
"""
import os, sys, glob, shutil, subprocess, zipfile
import numpy as np

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/МакSим - Знаешь ли ты")
ORIG = os.path.join(SONG, "moises-orig")
BPM = 63.855
B = 60.0 / BPM
P0 = 1.10415                      # raw time of k=0 on the DRUM grid (Moises' own click there: 1.135 s)
K_BAR1 = -1                       # raw beat index of bar 1.1

# Moises file tag -> stem name in the song folder (None = kept out of the stem glob, in moises-orig/)
NAMES = {"Bass": "bass", "Drums": "drums", "Keys": "keys", "Piano": "piano", "Strings": "strings",
         "Other": "other", "Vocals": "backing_vocals", "Metronome": None, "Count-in": None}

S = lambda t: int(round(t * SR))
tk = lambda k: P0 + k * B          # raw beat k -> seconds (stems are not shifted)


def do_import(zp):
    os.makedirs(ORIG, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            tag = next((t for t in NAMES if f"_minus_-{t}-" in base), None)
            if tag is None:
                sys.exit(f"unknown file in zip: {base}")
            dst = os.path.join(SONG, NAMES[tag] + ".wav") if NAMES[tag] else \
                os.path.join(ORIG, tag.lower() + ".wav")
            with z.open(info) as src, open(dst, "wb") as out:
                shutil.copyfileobj(src, out)
            print(f"  ✓ {base} -> {os.path.relpath(dst, SONG)}")


def n_samples(p):
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True).stdout
    return S(float(d))


def do_metronome():
    n = n_samples(os.path.join(SONG, "drums.wav"))
    out = np.zeros((n, 2), np.float32)
    L = S(0.03); t = np.arange(L) / SR
    hit = (np.sin(2 * np.pi * 2000 * t) * np.exp(-t / 0.006)).astype(np.float32) * 0.8
    k = K_BAR1
    while S(tk(k)) + L <= n:
        s = S(tk(k)); out[s:s+L] += hit[:, None]; k += 1
    p = os.path.join(SONG, "metronome.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", p], input=out.tobytes(), check=True)
    print(f"  ✓ metronome.wav  synthetic {BPM} bpm, first click (bar 1.1) {tk(K_BAR1):.4f}s, "
          f"{k - K_BAR1} clicks, drums/bass in bar 24.1 = {tk(91):.3f}s")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "import" and len(sys.argv) > 2:
        do_import(sys.argv[2])
    elif cmd == "metronome":
        do_metronome()
    else:
        sys.exit(__doc__)
