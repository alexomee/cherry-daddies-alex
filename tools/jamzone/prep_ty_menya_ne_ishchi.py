#!/usr/bin/env python3
"""One-off stem prep for «Вирус — Ты меня не ищи» (12.12 new songs, 2026-11-11). Rebuildable.

  python3 tools/jamzone/prep_ty_menya_ne_ishchi.py stems   # moises-orig/*.mp3 -> root *.wav + metronome.wav
  python3 tools/jamzone/prep_ty_menya_ne_ishchi.py fx      # processed stems -> parts/pb-fx.wav (stem frame)
  python3 tools/jamzone/prep_ty_menya_ne_ishchi.py keys    # keys+strings (live keys muted) -> parts/pb-keys.wav
then: python3 tools/jamzone/jamzone_render.py "Вирус - Ты меня не ищи"

Measured on the raw Moises stems (wiki/songs/virus-ty-menya-ne-ishchi.md):
  * tempo is dead-constant 137.59 bpm (lstsq ±5ms) -> NO warp; filename "138bpm" is rounded.
  * Moises metronome LAGS the drums by ~34ms -> grid phase taken from the drum 50%-attack,
    metronome.wav is synthesized on that grid (first click = bar 1.1).
  * the record inserts an extra 1/8 at the bar-66 break (stop 66.1 -> verse 67.1 = 4.5 beats):
    grid C (after) = grid A (before) + 0.494 beat. Compressed to 4 beats with rubberband ONLY
    inside the break (stop crash and verse-2 vocal pickup untouched) -> constant 4/4 click.
  * intro cut: bar 1.1 = raw click k=35 (Logic 01:00:15.652).
Beat index k below = raw Moises click index; bar = (k-35)//4 + 1.
"""
import os, sys, subprocess, tempfile
import numpy as np

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/Вирус - Ты меня не ищи")
SRC = os.path.join(SONG, "moises-orig")
BPM = 137.59
B = 60.0 / BPM
PRE = 0.05            # s of pre-roll before bar 1.1 (faded in)
# drum-aligned source grids (raw Moises timeline)
bA, pA = 0.4360621839096415, 0.40556970699827544     # before the break
bC, pC = 0.4360996976337763, 0.6099314870556765     # after the break (C299 = verse-2 downbeat)
M = 0.03              # s kept untouched after the stop beat (crash attack)
FADE_IN = 0.015
XF = 0.012            # crossfade between identity and rubberband output

tA = lambda k: pA + k*bA
tC = lambda k: pC + k*bC
tout = lambda k: PRE + (k - 35)*B

STEMS = ["backing_vocals", "bass", "drums", "guitars", "keys", "other", "piano", "strings", "vocals"]

def decode(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", path], input=x.astype(np.float32).tobytes(), check=True)

def rubberband_map(a, keyframes, n_out):
    with tempfile.TemporaryDirectory() as td:
        fin, fout, fmap = (os.path.join(td, n) for n in ("in.wav", "out.wav", "map.txt"))
        with open(fmap, "w") as f:
            for s, t in keyframes: f.write(f"{s} {t}\n")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", fin], input=a.astype(np.float32).tobytes(), check=True)
        r = subprocess.run(["rubberband", "-2", "-M", fmap, "-t", f"{n_out/len(a):.8f}", fin, fout],
                           capture_output=True, text=True)
        if r.returncode: raise RuntimeError(r.stderr)
        out = decode(fout)
    if len(out) < n_out: out = np.vstack([out, np.zeros((n_out-len(out), 2), np.float32)])
    return out[:n_out]

S = lambda t: int(round(t*SR))
# source anchors
s0 = tA(35) - PRE                 # cut point (intro removed)
c1 = tA(295) + M                  # compression start (after stop crash attack)
c2 = tC(298.25)                   # compression end (before verse-2 vocal pickup)
w0, w1 = tA(293.0), tC(300.0)     # rubberband context window
# output anchors (part1 identity: out = src - s0)
o_c1 = c1 - s0
o_c2 = tout(298.25)               # constant grid position of C298.25
shift3 = o_c2 - c2                # part3: out = src + shift3
# raw Moises seconds -> processed timeline: identity before the break, shifted after it
raw2out = lambda r: r - s0 if r < c1 else r + shift3
print(f"cut {s0:.4f}s | compress src {c1:.4f}-{c2:.4f} ({c2-c1:.4f}s) -> {o_c2-o_c1:.4f}s "
      f"(ratio {(o_c2-o_c1)/(c2-c1):.4f}) | part1 grid err @k295 {((tA(295)-s0)-tout(295))*1000:+.1f}ms")

xa, xb = tA(294.75), tC(298.40)   # crossfade points (src): identity -> RB, RB -> identity
def process(a):
    n_src = len(a)
    n_out = S(n_src/SR + shift3)
    out = np.zeros((n_out, 2), np.float32)
    # window through rubberband; map is identity (in window coords) outside [c1, c2]
    win = a[S(w0):S(w1)]
    o_w0 = w0 - s0                               # window start in output time (part 1 identity)
    o_w1 = w1 + shift3                           # window end in output time (part 3 identity)
    kf = [(0, 0), (S(c1-w0), S(o_c1-o_w0)), (S(c2-w0), S(o_c2-o_w0)), (len(win), S(o_w1-o_w0))]
    rb = rubberband_map(win, kf, S(o_w1-o_w0))
    # part 1 (identity) up to crossfade A
    p1 = a[S(s0):S(xa)].copy()
    out[:len(p1)] = p1
    # rubberband region between crossfades (output coords)
    oa, ob = xa - s0, xb + shift3
    rb_seg = rb[S(oa-o_w0):S(ob-o_w0)]
    st = S(oa)
    n = min(len(rb_seg), n_out-st)
    seg = rb_seg[:n].copy()
    x = S(XF); ramp = np.linspace(0, 1, x)[:, None]
    seg[:x] = seg[:x]*ramp + a[S(xa):S(xa)+x]*(1-ramp)          # fade orig -> rb
    out[st:st+n] = seg
    # part 3 (identity) from crossfade B, crossfaded with rb tail
    p3 = a[S(xb):]
    st3 = S(ob)
    m = min(len(p3), n_out-st3)
    tail = rb[S(ob-o_w0):S(ob-o_w0)+x]
    p3 = p3[:m].copy()
    p3[:x] = p3[:x]*ramp + tail[:x]*(1-ramp)                    # fade rb -> orig
    out[st3:st3+m] = p3
    fi = S(FADE_IN); out[:fi] *= np.linspace(0, 1, fi)[:, None]
    return out

def metronome(n_out, last_k):
    out = np.zeros((n_out, 2), np.float32)
    L = S(0.03); t = np.arange(L)/SR
    hit = (np.sin(2*np.pi*2000*t)*np.exp(-t/0.006)).astype(np.float32)*0.8
    k = 35
    while k <= last_k:
        s = S(tout(k))
        if s+L > n_out: break
        out[s:s+L, 0] += hit; out[s:s+L, 1] += hit; k += 1
    return out

LEAD = 0.02                       # pre-roll before the beat (keeps the attack)

def cut(x, t0, t1, fi=0.005, fo=0.015):
    seg = x[S(t0):S(t1)].copy()
    a, b = S(fi), S(fo)
    seg[:a] *= np.linspace(0, 1, a)[:, None]
    seg[-b:] *= np.linspace(1, 0, b)[:, None]
    return seg

def do_stems():
    n_out = None
    for nm in STEMS:
        a = decode(os.path.join(SRC, nm + ".mp3"))
        o = process(a)
        n_out = len(o)
        write_wav(os.path.join(SONG, nm + ".wav"), o)
        print(f"  ✓ {nm}.wav  {len(o)/SR:.3f}s  peak {np.abs(o).max():.3f}")
    last_k = int(np.floor((n_out/SR - PRE)/B)) + 35
    write_wav(os.path.join(SONG, "metronome.wav"), metronome(n_out, last_k))
    print(f"  ✓ metronome.wav  synthetic, {BPM} bpm, first click {PRE:.3f}s")

def do_fx():
    drums, keys, vocals = (decode(os.path.join(SONG, n + ".wav")) for n in ("drums", "keys", "vocals"))
    out = np.zeros_like(drums)
    def put(seg, t):
        s = S(t); out[s:s+len(seg)] += seg

    # F1: drum fill of the bar-8 stop (raw 28.696-29.491 = k65 .. k66.70)
    frag = cut(drums, tout(65) - LEAD, tout(66.70))
    put(frag, tout(65) - LEAD)
    print(f"  fx fill @ bar 8.3 stop -> verse (original position): t={tout(65):.3f}")
    # F1b (2026-11-12, Alex): 4-beat stops use the record's OWN drums of that bar, in place
    # ("4 gunshots": boomy hit on every beat). Raw Moises seconds -> processed timeline:
    # identity before the break (out = raw - s0), shifted after it (out = raw + shift3).
    for label, r0, r1 in [("bar 57.1-58.1", 113.339, 115.070),     # 01:01:53.339-01:01:55.070
                          ("bar 107.1-108.1", 200.761, 202.500)]:  # 01:03:20.761-01:03:22.500
        o0, o1 = raw2out(r0), raw2out(r1)
        put(cut(drums, o0, o1), o0)
        print(f"  drums (original) @ {label} : raw {r0}-{r1} -> {o0:.3f}-{o1:.3f}s")
    # F1c (2026-11-12, Alex): the bar-66 break gets the SAME 4 shots (bar-57 drums), not the
    # bar-8 fill x2. Same offset to the beat as at bar 57 (shot 1 on 66.1).
    o0, o1 = raw2out(113.339), raw2out(115.070)
    t66 = tout(295) + (o0 - tout(259))
    put(cut(drums, o0, o1), t66)
    print(f"  4 shots (bar-57 drums) @ bar 66.1-67.1 : {t66:.3f}-{t66 + o1 - o0:.3f}s")
    # F2 (2026-11-12, Alex, 2nd spec): Moises keys in the break, raw 129.073-130.931 (in the source
    # this is the vocal shout "Take it out!", whisper 129.1-130.5). The keys stem itself is muted
    # there in pb-other (mix.json "mute"), so this fx copy is the only keys in the break.
    k0, k1 = raw2out(129.073), raw2out(130.931)
    put(cut(keys, k0, k1, fo=0.025), k0)
    print(f"  keys @ bar 66.1-66.4& : raw 129.073-130.931 -> {k0:.3f}-{k1:.3f}s")
    # F3: ending keys + vocals (raw 230.435-232.328 = C527 .. C531.34)
    put(cut(keys + vocals, tout(527) - LEAD, tout(531.34), fo=0.12), tout(527) - LEAD)
    print(f"  keys+vocals @ bar 124.1-125.1.34 : {tout(527):.3f}-{tout(531.34):.3f}s")

    pk = float(np.abs(out).max())
    if pk > 0.98: out *= 0.98/pk; print(f"  peak guard {pk:.3f} -> 0.98")
    os.makedirs(os.path.join(SONG, "parts"), exist_ok=True)
    dst = os.path.join(SONG, "parts", "pb-fx.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", dst], input=out.astype(np.float32).tobytes(), check=True)
    print(f"  ✓ {dst}  {len(out)/SR:.3f}s  peak {np.abs(out).max():.3f}")

# pb-keys (2026-11-12, Alex): Moises keys + strings for pb-other; keys MUTED where the keyboardist
# plays live. Raw Moises seconds (Logic 01:00:00 base); None = till the end. Strings never muted.
KEYS_MUTES = [(85.175, 130.909),       # 01:01:25.175-01:02:10.909  synth solo .. break (bars 40.4.4-66.4.8)
              (188.164, None)]         # 01:03:08.164-end            solo drums-half .. end (bar 99.4-)
MUTE_XF = 0.015                        # same 15 ms edge fades as jamzone_render mutes

def do_keys():
    keys, strings = (decode(os.path.join(SONG, n + ".wav")) for n in ("keys", "strings"))
    n = len(keys)
    for r0, r1 in KEYS_MUTES:
        a = S(raw2out(r0)); b = n if r1 is None else S(raw2out(r1)); f = S(MUTE_XF)
        keys[a-f:a] *= np.linspace(1, 0, f)[:, None]
        keys[a:b] = 0
        if b + f <= n: keys[b:b+f] *= np.linspace(0, 1, f)[:, None]
        print(f"  keys muted raw {r0}-{r1 or 'end'} -> {a/SR:.3f}-{b/SR:.3f}s")
    out = keys + strings[:n]
    pk = float(np.abs(out).max())
    dst = os.path.join(SONG, "parts", "pb-keys.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", dst], input=out.astype(np.float32).tobytes(), check=True)
    print(f"  ✓ {dst}  {n/SR:.3f}s  peak {pk:.3f} (float wav, no gain change)")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else ""
    if step == "stems": do_stems()
    elif step == "fx": do_fx()
    elif step == "keys": do_keys()
    else: sys.exit(__doc__)
