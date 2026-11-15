#!/usr/bin/env python3
"""pb-rhythm-guitar for «Kings of Leon — Sex on Fire» (JamZone cat_20791, 12.12 new songs). Rebuildable.

  python3 tools/jamzone/prep_sex_on_fire.py rhythm   # -> parts/pb-rhythm-guitar.wav
then: python3 tools/jamzone/jamzone_render.py "Kings of Leon - Sex on Fire"

Alex 2026-11-15: playback rhythm guitar = JamZone Rhythm Guitar LEFT everywhere, EXCEPT the choruses
and the bridge, where it is ONLY the RIGHT one.
  * Sections from JamZone structure.json, all exactly on click bar lines (+3 ms):
    Chorus 35-42, Chorus 2 59-74, Chorus 3 91-98 + Bridge 99-114 + Chorus 4 115-end -> RIGHT;
    intro / verses (bars 1-34, 43-58, 75-90) -> LEFT. Bar n starts at click onset 4*(n-1)
    (bar 1 = first precount click, same numbering as mix.json with click: follow).
  * Both guitars play straight through every boundary (no gap to hide a switch in), so the switch is
    an equal-power crossfade of XF seconds ENDING on the bar line: the incoming guitar's downbeat
    attack is intact, the outgoing one is gone by the downbeat.
  * Output is the stems' own timeline (stem frame, t=0 = raw stem 0), unity gain (level = gain_db
    in mix.json). It is DERIVED from the song's own stems -> mix.json layer "derived": true
    (only in pb-other, not doubled into all / site stems).
"""
import os, sys, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jamzone_render as jr

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/Kings of Leon - Sex on Fire")
LEFT, RIGHT = "05_Rhythm_Electric_Guitar_(left)", "06_Rhythm_Electric_Guitar_(right)"
RIGHT_BARS = [(35, 43), (59, 75), (91, None)]      # [from, to) bars on RIGHT; None = to the end
XF = 0.020                                         # crossfade length (s), ends on the bar line

def decode(p, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()

def do_rhythm():
    on = jr.onsets(decode(os.path.join(SONG, "01_Click.m4a"), 1)[:, 0])
    bar_t = lambda b: float(on[4 * (b - 1)])
    L = decode(os.path.join(SONG, LEFT + ".m4a")); R = decode(os.path.join(SONG, RIGHT + ".m4a"))
    n = max(len(L), len(R)); L = np.pad(L, ((0, n - len(L)), (0, 0))); R = np.pad(R, ((0, n - len(R)), (0, 0)))
    w = np.zeros(n, np.float32)                    # weight of RIGHT (0 = LEFT only, 1 = RIGHT only)
    f = int(round(XF * SR)); ramp = np.linspace(0, 1, f, dtype=np.float32)
    for b0, b1 in RIGHT_BARS:
        s0 = int(round(bar_t(b0) * SR)); s1 = int(round(bar_t(b1) * SR)) if b1 else n
        w[s0:s1] = 1.0
        w[s0 - f:s0] = ramp                        # L -> R, done by the downbeat of b0
        if b1: w[s1 - f:s1] = 1.0 - ramp           # R -> L, done by the downbeat of b1
        print(f"  RIGHT bars {b0}-{(b1 - 1) if b1 else 'end'}: {bar_t(b0):7.3f}s - "
              f"{(bar_t(b1) if b1 else n / SR):7.3f}s")
    gL = np.cos(w * np.pi / 2)[:, None]; gR = np.sin(w * np.pi / 2)[:, None]   # equal power (uncorrelated)
    out = L * gL + R * gR
    os.makedirs(os.path.join(SONG, "parts"), exist_ok=True)
    dst = os.path.join(SONG, "parts", "pb-rhythm-guitar.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", dst], input=out.astype(np.float32).tobytes(), check=True)
    print(f"  ✓ {dst}  ({n / SR:.2f}s, peak {np.abs(out).max():.3f}, stem frame, unity gain)")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "rhythm": do_rhythm()
    else: sys.exit(__doc__)
