#!/usr/bin/env python3
"""Smells Like Teen Spirit: synth-pop bass instead of the bass guitar - audition variants by ear.

The bass line is taken from the JamZone bass stem on the click grid (the song is click: follow, so
tools/part_notes.py does not apply), then three lines are written over the same harmony and played
by a plain software synth (saw + sub through a 24 dB low-pass with a per-note envelope). The sound
is a sketch: the final sound comes from the GM-800, this only picks the line.

  A  the bass guitar line as it is, synth sound
  B  octave eighths low-low-high-high, the pattern of the intro of «Я устал»
  B2 the same without the sixteenth figure, brighter, and the same even eighths and sound in the chorus
     (Alex 2026-11-20: «убери шестнадцатые и сделай поярче», «в припеве должны также продолжаться ровные»)
  C  off-beat eurodance bass (eighths in the verse, rolling sixteenths in the chorus)

  uv run -q --python 3.12 --with numpy --with scipy --with librosa --with numba --with pyloudnorm \
      python tools/synth_bass_audition.py [--bars 1 54] [--scan]

Writes analysis/teen-spirit-synth-bass/*.mp3 (context = drums + guitars + vocal, and bass alone)
and notes.json (the three lines as [bar, sixteenth, length in sixteenths, midi]). Nothing in music/.
"""
import sys, os, json, argparse, subprocess, numpy as np, librosa, pyloudnorm
from numba import njit
from scipy.signal import butter, sosfilt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "jamzone"))
import jamzone_render as jr
SR = jr.SR
SONG = os.path.join(ROOT, "music", "songs", "Nirvana - Smells Like Teen Spirit")
OUT = os.path.join(ROOT, "analysis", "teen-spirit-synth-bass")
F1, AB1, BB1, DB2 = 29, 32, 34, 37
LOOP = [(F1, BB1), (AB1, DB2)]                 # root of each half bar, bars alternate from bar 2
PRE = [(26, 34), (62, 70), (114, 122)]         # pre-choruses (JamZone sections), TO exclusive
VERSE = [(18, 26), (54, 62), (106, 114)]
VARS = ("V1", "V2", "V3", "V4")              # quiet variations of B2 (Alex 2026-11-20: less looped, not overdone)
RIFF = [(46, 50), (82, 86)]
# ARR = the arrangement of the whole song (Alex 2026-11-20: «скомпонуй по своему усмотрению, интересно, но не чересчур»):
# the variations placed by section, so that no two verses are the same and the motor only runs full where the band is loud
SECT = [(6, 14, "intro"), (14, 18, "vamp"), (18, 26, "verse1"), (26, 34, "pre"), (34, 46, "chorus"), (50, 54, "vamp"),
        (54, 62, "verse2"), (62, 70, "pre"), (70, 82, "chorus"), (86, 102, "solo"), (102, 106, "intro"), (106, 114, "verse3"),
        (114, 122, "pre"), (122, 134, "chorus"), (134, 142, "outro")]                    # the post-chorus riff: every variant plays the original line
GM_ATTACK = 0.007                              # s: the tones of scene 25 speak this late (prep_teen_spirit_bass.py)
NAMES = "C C# D D# E F F# G G# A A# B".split()
def nn(m): return f"{NAMES[m % 12]}{m // 12 - 1}"
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def inr(b, rs): return any(a <= b < e for a, e in rs)

def grid():
    on = jr.met_onsets(jr.decode(f"{SONG}/01_Click.m4a").mean(1))
    b = list(on); step = float(np.diff(on)[-8:].mean())
    while len(b) < 4 * 152 + 1: b.append(b[-1] + step)
    b = np.array(b)
    s16 = np.concatenate([b[i] + (b[i + 1] - b[i]) * np.arange(4) / 4 for i in range(len(b) - 1)])
    return b, s16                               # s16[(bar-1)*16 + k] = time of sixteenth k of the bar

def transcribe(y, s16):
    """Notes of the bass stem: [slot, length in slots, midi]. Onsets snapped to sixteenths; pitch = pyin median
    over the note, then a fifth/octave-down check (pyin often locks on the 3rd harmonic of F1..A#1)."""
    sr = 11025; hop = 64
    x = librosa.resample(y, orig_sr=SR, target_sr=sr)
    f0, _, _ = librosa.pyin(x, fmin=32, fmax=260, sr=sr, frame_length=2048, hop_length=hop)
    tt = librosa.times_like(f0, sr=sr, hop_length=hop)
    rms = librosa.feature.rms(y=x, frame_length=512, hop_length=hop)[0]
    db = 20 * np.log10(rms / rms.max() + 1e-9)
    on = librosa.onset.onset_detect(y=x, sr=sr, hop_length=hop, units="time", backtrack=False, delta=0.06, wait=5)
    slots = sorted({int(np.argmin(np.abs(s16 - t))) for t in on})
    notes = []
    for i, s in enumerate(slots):
        a = s16[s]; e_slot = slots[i + 1] if i + 1 < len(slots) else s + 8
        k = s
        while k < e_slot and db[(tt >= s16[k]) & (tt < s16[k + 1])].max(initial=-99) > -32: k += 1
        if k == s: continue
        e = s16[k]
        m = (tt >= a + 0.025) & (tt < e - 0.01); f = f0[m]; f = f[~np.isnan(f)]
        if len(f) < 3: continue
        p = int(round(librosa.hz_to_midi(np.median(f))))
        seg = x[int((a + 0.02) * sr):int(e * sr)]
        if len(seg) > 0.17 * sr:
            n = 1 << 16; X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
            def mag(fr): i0 = int(round(fr * n / sr)); return X[max(0, i0 - 3):i0 + 4].max()
            harm = lambda q: mag(hz(q)) + mag(2 * hz(q)) + mag(3 * hz(q))
            for down in (7, 12):                # true note lower: its own fundamental is present in the spectrum
                if p - down >= 28 and mag(hz(p - down)) > 0.3 * mag(hz(p)) and harm(p - down) > harm(p): p -= down; break
        notes.append([s, k - s, p])
    return notes

def bar_energy(b16, loud_env, bars):
    """0 quiet, 1 pre-chorus, 2 loud (distorted rhythm guitars present)."""
    e = {}
    for b in bars:
        a, z = int(b16[(b - 1) * 16] * SR), int(b16[b * 16] * SR)
        e[b] = 1 if inr(b, PRE) else (2 if loud_env[a:z].mean() > 0.25 else 0)
    return e

def lines(orig, bars, energy, active):
    """Variant note lists as [slot, len, midi]. B and C follow the root loop where the bass guitar plays the loop;
    the riff bars, the pick-up into bar 6 and the last held note come from the original line."""
    by_bar = {}
    for s, l, p in orig: by_bar.setdefault(s // 16 + 1, []).append([s, l, p])
    out = {"A": [n for b in bars for n in by_bar.get(b, [])], "B": [], "B2": [], "C": [], **{k: [] for k in VARS}, "ARR": [], "ARR2": [], "ARR3": []}
    for b in bars:
        own = by_bar.get(b, [])
        if b < 6 or inr(b, RIFF) or b >= 142:
            out["B"] += own; out["C"] += own
            s0 = (b - 1) * 16; fs = F1 + 1      # B2 = the line that goes to the playback: these bars written by hand
            if b == 5: cell = [(12, 4, F1)]     # (the transcription of them moves a sixteenth from run to run)
            elif b == 142: cell = [(0, 32, F1)] # the last hit rings for two bars, like the guitars
            elif inr(b, RIFF) and (b - [r for r in RIFF if r[0] <= b < r[1]][0][0]) % 2 == 0:
                cell = [(0, 4, F1), (4, 2, F1), (6, 2, fs), (8, 2, fs), (10, 2, fs)]
            elif inr(b, RIFF): cell = [(0, 4, 36), (4, 2, 36), (6, 2, 36), (8, 2, BB1), (10, 2, BB1), (12, 2, 33), (14, 2, AB1)]
            else: cell = []
            for key in ("B2", "ARR", "ARR2", "ARR3") + VARS: out[key] += [[s0 + k, l, p] for k, l, p in cell]
            continue
        for half, root in enumerate(LOOP[b % 2]):
            s0 = (b - 1) * 16 + half * 8
            if active[s0:s0 + 8].mean() < 0.5: continue
            hi = root + 12; e = energy[b]
            fill = (b % 2 == 1 and half == 1)   # the D-flat cell closes the two-bar loop: the sixteenth figure of «Я устал»
            if fill: cell = [(0, 2, root), (2, 2, root), (4, 1, hi), (5, 1, hi), (6, 2, hi)]
            else:    cell = [(0, 2, root), (2, 2, root), (4, 2, hi), (6, 2, hi)]
            out["B"] += [[s0 + k, l, p] for k, l, p in cell]
            base = ((0, root), (2, root), (4, hi), (6, hi))
            out["B2"] += [[s0 + k, 2, p] for k, p in base]
            c = (b % 2) * 2 + half; j = (b - 6) // 2        # cell of the two-bar loop (F, Bb, Ab, Db); loop number
            thin, most = ((0, root), (4, hi)), ((0, root), (2, root), (4, hi))
            push = ((0, root), (2, root), (6, hi))          # nothing on the beat, the octave on the off-beat
            walk = ((0, root), (2, root), (4, hi), (6, 36 if c == 3 else 33))   # the bass guitar's own passing notes:
            # C before the loop starts again, A before A-flat
            v1 = thin if e == 0 else most if e == 1 else base           # density follows the sections
            v2 = push if (c in (1, 3) and e < 2) or (c == 3 and e == 2) else base
            v3 = walk if c == 3 or (c == 1 and j % 2 == 1) else base
            if e == 0: v4 = most if any(a + 4 <= b < z for a, z in VERSE) else thin   # verse: first half thin
            elif e == 1: v4 = walk if c == 3 else base
            else: v4 = walk if c == 3 else push if (c == 1 and j % 2 == 1) else base
            for key, cell in zip(VARS, (v1, v2, v3, v4)): out[key] += [[s0 + k, 2, p] for k, p in cell]
            a0, _, sec = next(x for x in SECT if x[0] <= b < x[1]); pos = b - a0; lp = pos // 2   # bar and loop in the section
            if sec == "vamp": cell = thin
            elif sec == "verse1": cell = thin if pos < 4 else most                    # wakes up: thin -> a breath on the last eighth
            elif sec == "verse2": cell = most if pos < 4 else push if c in (1, 3) else base   # busier than verse 1
            elif sec == "verse3": cell = thin if pos < 4 else push if c in (1, 3) else most   # drops again before the last chorus
            elif sec == "pre": cell = walk if c == 3 else base                        # full motor, C leads back to F
            elif sec in ("chorus", "outro"): cell = walk if c == 3 else push if (c == 1 and lp % 2 == 1) else base
            elif sec == "solo": cell = walk if (c == 3 and lp % 2 == 1) else base     # plain ground under the guitar solo
            else: cell = walk if c == 3 else base                                     # loud intro
            out["ARR"] += [[s0 + k, 2, p] for k, p in cell]
            # ARR2 (Alex after hearing ARR: «одиночные нигде не нужны, основной паттерн прямые, каждые 4 такта небольшая
            # вариация типа синкопы»): straight everywhere, the last cell of every 4th bar varies - syncopation and the
            # passing C in turn. In the playback it is spliced from the B2 and ARR takes (prep_teen_spirit_bass.py splice)
            ph = (b - 6) // 4
            cell = base if not (c == 3 and (b - 6) % 4 == 3) else push if ph % 2 == 0 else walk
            out["ARR2"] += [[s0 + k, 2, p] for k, p in cell]
            # ARR3 = ARR2 + the quiet bars after the first chorus riff (50-53, before verse 2) on alternating octaves
            # low-high-low-high, the disco bass (Alex: «в проигрыше после припева перед 2 куплетом что-то поинтереснее,
            # потом опять ровно»); the passing C leads into the verse
            if 50 <= b < 54: cell = ((0, root), (2, hi), (4, root), (6, 36 if (b == 53 and half == 1) else hi))
            out["ARR3"] += [[s0 + k, 2, p] for k, p in cell]
            if e == 0:   cell = [(2, 2, root), (6, 2, root)]
            elif e == 1: cell = [(2, 2, root), (6, 2, hi)]
            else:        cell = [(1, 1, root), (2, 1, hi), (3, 1, root), (5, 1, root), (6, 1, hi), (7, 1, root)]
            out["C"] += [[s0 + k, l, p] for k, l, p in cell]
    return out

@njit(cache=True)
def lp24(x, fc, q, sr):
    y = np.empty_like(x); a = b = c = d = 0.0
    for i in range(len(x)):
        g = np.tan(np.pi * fc[i] / sr)
        k = 1.41; a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2
        v3 = x[i] - b; v1 = a1 * a + a2 * v3; v2 = b + a2 * a + a3 * v3; a = 2 * v1 - a; b = 2 * v2 - b
        k = 1 / q; a1 = 1 / (1 + g * (g + k)); a2 = g * a1; a3 = g * a2
        w3 = v2 - d; w1 = a1 * c + a2 * w3; w2 = d + a2 * c + a3 * w3; c = 2 * w1 - c; d = 2 * w2 - d
        y[i] = w2
    return y

def synth(notes, s16, energy, n, sweep, bright=False):
    """saw + detuned saw + sub sine -> 24 dB low-pass, cutoff falls per note; louder sections open the filter and
    add drive. sweep: slow movement of the cutoff over 8 bars (the filter of the «Я устал» intro moves)."""
    finc = np.zeros(n); amp = np.zeros(n); fc = np.full(n, 120.0); drv = np.ones(n); sub = np.zeros(n)
    for s, l, p in notes:
        a, z = int(s16[s] * SR), int(s16[s + l] * SR); b = s // 16 + 1; e = energy.get(b, 0)
        z = a + max(int(0.06 * SR), int((z - a) * (0.82 if l <= 2 else 0.96)))
        z = min(z, n); m = z - a
        if m <= 0: continue
        t = np.arange(m) / SR
        base, amt, tau, lvl, dr = [(190, 1000, 0.09, 1.0, 1.0), (240, 1500, 0.11, 0.9, 1.6), (330, 2900, 0.16, 0.8, 2.6)][e]
        if bright:                              # one sound through verse and chorus: the chorus only opens a little further
            base, amt, tau, lvl, dr = [(320, 2100, 0.12, 1.0, 1.5), (360, 2600, 0.13, 0.97, 1.6), (400, 3200, 0.14, 0.94, 1.8)][e]
        if sweep: amt *= 1.0 + (0.25 if bright else 0.55) * np.sin(2 * np.pi * (s / 16) / 8 - np.pi / 2)
        acc = 1.0 if s % 4 == 0 else (0.94 if bright else 0.86)
        env = np.minimum(1, t / 0.003) * (0.62 + 0.38 * np.exp(-t / 0.14)); r = min(m, int(0.035 * SR)); env[-r:] *= np.linspace(1, 0, r)
        f = hz(p)
        finc[a:z] = f / SR; amp[a:z] = env * lvl * acc; fc[a:z] = base + amt * acc * np.exp(-t / tau) + 2.2 * f; drv[a:z] = dr
        sub[a:z] = (2 * f if f < 60 else f) / SR    # below 60 Hz a PA has little: the sine doubles the 2nd harmonic there
    ph = np.cumsum(finc)
    x = 0.6 * (2 * (ph % 1) - 1) + 0.4 * (2 * ((ph * 1.006) % 1) - 1)
    y = lp24(x * amp, np.minimum(fc, 9000.0), 3.2 if bright else 2.4, float(SR)) + 0.45 * np.sin(2 * np.pi * np.cumsum(sub)) * amp
    y = np.tanh(y * drv) / np.tanh(drv)
    y = sosfilt(butter(2, 48, "highpass", fs=SR, output="sos"), y)
    if bright:                                  # an even motor: every note as loud as the others (heard level: the
        w = sosfilt(butter(1, 120, "highpass", fs=SR, output="sos"), y); seg = []   # lows weigh less), within 6 dB
        for s, l, p in notes:
            a, z = int(s16[s] * SR), min(int(s16[s + l] * SR), n)
            if z - a > 64: seg.append((a, z, np.sqrt((w[a:z] ** 2).mean()) + 1e-9))
        med = np.median([r for _, _, r in seg])
        for a, z, r in seg: y[a:z] *= np.clip(med / r, 0.5, 2.0)
    return y.astype(np.float32)

def mp3(path, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                          "-c:a", "libmp3lame", "-q:a", "2", path], stdin=subprocess.PIPE)
    p.communicate(x.astype(np.float32).tobytes())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bars", nargs=2, type=int, default=[1, 54]); ap.add_argument("--scan", action="store_true")
    ap.add_argument("--out", default="", help="subfolder of the audition folder (a full-song pass keeps the first audition)")
    ap.add_argument("--gm800-only", action="store_true", help="no sketch-synth takes: only the gm800-*.wav of the folder")
    ap.add_argument("--notes-only", action="store_true", help="write notes.json only (for tools/synth_bass_gm800.py)")
    a = ap.parse_args(); b0, b1 = a.bars; bars = range(b0, b1)
    beats, s16 = grid()
    bass = jr.decode(f"{SONG}/03_Bass.m4a").mean(1)
    orig = transcribe(bass, s16)
    stems = sorted(f for f in os.listdir(SONG) if f.endswith(".m4a"))
    rhythm = sum(jr.decode(f"{SONG}/{f}").mean(1) for f in stems if "Rhythm" in f)
    w = int(0.4 * SR); env = np.sqrt(np.convolve(rhythm ** 2, np.ones(w) / w, mode="same")); env /= np.percentile(env, 99)
    energy = bar_energy(s16, env, range(1, 148))
    w = int(0.02 * SR); benv = np.sqrt(np.convolve(bass ** 2, np.ones(w) / w, mode="same")); benv /= benv.max()
    active = np.array([benv[int(s16[k] * SR):int(s16[k + 1] * SR)].max() > 0.02 for k in range(147 * 16)])
    if a.scan:
        by = {}
        for s, l, p in orig: by.setdefault(s // 16 + 1, []).append((s % 16, l, p))
        for b in range(1, 148):
            row = ["."] * 16
            for k, l, p in by.get(b, []):
                row[k] = nn(p)
                for j in range(k + 1, min(16, k + l)): row[j] = "~"
            print(f"{b:3d} e{energy[b]} " + " ".join("|" * (i % 4 == 0) + f"{c:3s}" for i, c in enumerate(row)))
        return
    out_dir = os.path.join(OUT, a.out) if a.out else OUT; os.makedirs(out_dir, exist_ok=True)
    v = lines(orig, bars, energy, active)
    t0, t1 = s16[(b0 - 1) * 16], s16[(b1 - 1) * 16]; i0, i1 = int(t0 * SR), int(t1 * SR)
    marks = [[b, round(float(s16[(b - 1) * 16] - t0), 3)] for b in bars]
    json.dump({"bars": [b0, b1], "bar_sec": marks, "slot_sec": [round(float(s16[k] - t0), 4) for k in range((b0 - 1) * 16, (b1 - 1) * 16 + 1)], "energy": {str(b): energy[b] for b in bars},
               "lines": {k: [[s // 16 + 1, s % 16, l, p] for s, l, p in ns] for k, ns in v.items()}},
              open(f"{out_dir}/notes.json", "w"))
    if a.notes_only:
        print(f"notes -> {out_dir}/notes.json"); return
    ctx = sum(jr.decode(f"{SONG}/{f}").mean(1) for f in stems if "Click" not in f and "Bass" not in f)[i0:i1]
    ref = bass[i0:i1]; meter = pyloudnorm.Meter(SR); target = meter.integrated_loudness(ref)
    takes = {}
    for key in ([] if a.gm800_only else v):
        y = synth(v[key], s16, energy, len(bass), sweep=(key == "B"), bright=(key == "B2"))[i0:i1]
        takes[key] = y * 10 ** ((target - meter.integrated_loudness(y)) / 20)
    names = {"0": "original", "A": "A-same-line", "B": "B-ya-ustal-octaves", "B2": "B2-bright-no-16ths", "C": "C-offbeat"}
    gm_gain = None
    for f in sorted(os.listdir(out_dir)):           # takes of the GM-800 (tools/synth_bass_gm800.py): gm800-<line>-s<scene>.wav,
        if f.startswith("gm800-") and f.endswith(".wav"):   # sample 0 = the bar line of the first bar
            y = jr.decode(f"{out_dir}/{f}").mean(1)[int(GM_ATTACK * SR):][:i1 - i0]; y = np.pad(y, (0, i1 - i0 - len(y)))
            key = f[6:-4]; names[key] = key + "-gm800"
            if gm_gain is None or not a.gm800_only:     # variations keep their own loudness against the first take
                gm_gain = 10 ** ((target - meter.integrated_loudness(y)) / 20)   # (B2 sorts first): thinner = quieter
            takes[key] = y * gm_gain
    mixes = {"0": ctx + ref, **{k: ctx + y for k, y in takes.items()}}
    g = 0.89 / max(np.abs(m).max() for m in mixes.values()); gs = 0.89 / max(np.abs(ref).max(), max(np.abs(y).max() for y in takes.values()))
    for k, m in mixes.items(): mp3(f"{out_dir}/ctx-{names[k]}.mp3", m * g)
    mp3(f"{out_dir}/solo-original.mp3", ref * gs)
    for k, y in takes.items(): mp3(f"{out_dir}/solo-{names[k]}.mp3", y * gs)
    print(f"bars {b0}-{b1 - 1}, {t1 - t0:.1f} s, bass {target:.1f} LUFS; notes " + " ".join(f"{k} {len(n)}" for k, n in v.items()) + f" -> {out_dir}")

if __name__ == "__main__":
    main()
