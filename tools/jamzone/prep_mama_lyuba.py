#!/usr/bin/env python3
"""«Мама Люба»: the Moises synths (keys + wind + strings) written out as notes for the GM-800
(wiki/pipelines/part-transcription-guide.md, Alex 2026-11-20: «сними и запиши партию клавиш»; scope =
all three synth stems, everything goes to the playback, Alex plays guitar; sounds picked by me).

  python3 tools/jamzone/prep_mama_lyuba.py notes      # -> parts/synths.notes.json (voices + layer takes)
  gmp record "Мама Люба" "music/songs/Мама Люба/parts/synths.notes.json"   # takes from the GM-800
  python3 tools/jamzone/prep_mama_lyuba.py calibrate  # each voice vs the stems where it plays -> GAIN below
  gmp layer "Мама Люба" "music/songs/Мама Люба/parts/synths.notes.json"    # -> parts/pb-synths.wav
  python3 tools/jamzone/prep_mama_lyuba.py fx         # keys+wind+strings inside the FX windows only -> parts/pb-fx.wav
(python3 = uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with pyloudnorm ...; gmp: see
tools/gm800_part.py)

All notes are in the BAND key (pitch_semitones -2: the stems are in Bbm, the band plays G#m), bars =
mix.json bars. Read off the stems with tools/part_notes.py (--roll / --period) and a pyin pass on the
wind stem; Moises spread ONE layered synth over keys, wind and strings, so the parts are musical
parts of the sum, not one per stem:

  pad      big chord, 2-bar rhythm G#m (beats 1-2) / B (3 - 4.2) / C# (4.3 - end of the next bar)
           (= the brass track of the MIDI from the web): intro 1-6, choruses 36-51 70-85 110-117,
           under the solo 86-93 118-125; intro 7 E, 8-11 C#; final hit 126.
  padlow   the root an octave below (G#2 / B2 / C#3) with the pad.
  bass     intro only (the bass stem is silent there): G#1 / B1 / C#2, C#2 held 8-11.
  stab     F3 F#4 G#4 B4 D#5 on 4.3 of every odd bar of the verses (13-35, 53-67), into the downbeat.
  pluck    G#5 (1) / C#5 (1.3) with a dotted-eighth echo, bars 21 25 29 33.
  lead     the hook in the RHYTHM OF THE MIDI (Alex 2026-11-20), a stack of octaves (+ fifth) in the record:
           solo 86-93 and 118-125 H1 H2 H1 H4, kick stop 94-101 K1 K2 K1 K4, variation 102-107 K1 K2, build
           108-109 B1 B2, last chorus 110-117 H1 H2 ... H4 (no hook there in the MIDI; kept from the record).
  FX       impacts / noise / the final fall are not notes: kept as cut stems (pb-fx) in their windows.
"""
import json, os, subprocess, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SONG = os.path.join(REPO, "music", "songs", "Мама Люба")
PART = os.path.join(SONG, "parts", "synths.notes.json")
NAMES = "C C# D D# E F F# G G# A A# B".split()


def midi(s):
    return NAMES.index(s[:-1]) + 12 * (int(s[-1]) + 1)


def name(m):
    return f"{NAMES[m % 12]}{m // 12 - 1}"


def ev(bar, q, l16, pitches):
    """bar inside the pattern, 16th index 0-15, length in 16ths -> notes.json note."""
    return [bar, 1 + q / 4, l16 / 4, pitches]


# ---- the hook (16th, length in 16ths, root in octave 4) ----------------------------------------
# RHYTHM FROM THE MIDI (Alex 2026-11-20, after an A/B of a plain render: «да, по миди»): G# short (a 16th) on the
# offbeat 16ths, brass track 6 of ~/Downloads/mama_ljuba_[lakhin_juriy].mid. MIDI bars -> ours: solo 78-85 -> 86-93
# (and 118-125), kick stop 86-89 -> 94-101 (x2, the MIDI has 4 bars), variation 90-95 -> 102-107, build 96-97 ->
# 108-109. The MIDI's last chorus has no hook (a half-note brass line); ours keeps the hook there in the solo rhythm.
_G6 = [(1, 1, "G#4"), (3, 1, "G#4"), (5, 1, "G#4"), (7, 1, "G#4"), (9, 1, "G#4"), (11, 1, "G#4")]
H1 = [(0, 1, "F#4")] + _G6 + [(12, 1, "A#4"), (13, 1, "B4"), (14, 1, "A#4"), (15, 1, "G#4")]
H2 = [(0, 1, "F#4")] + _G6 + [(12, 1, "F4"), (13, 1, "F#4"), (14, 1, "F4"), (15, 1, "D#4")]
H4 = [(0, 1, "A#4"), (1, 1, "B4"), (2, 1, "G#4"), (3, 1, "F#4"), (4, 2, "G#4"), (6, 1, "F#4"), (7, 1, "F4"),
      (8, 2, "F#4"), (10, 1, "F4"), (11, 1, "D#4"), (12, 2, "F4"), (14, 1, "D#4"), (15, 1, "C#4")]
# kick stop / variation: the turn is ONE held note with a bend in the record (Alex 2026-11-20: «во втором проходе,
# где длинные остановки на нотах, в оригинале что-то типа бенда»; pyin, 6 ms: flat to 12.6, up ~65 cents to the
# next semitone by 13.3, held, back at 14.0, flat to 15). The GM-800 ignores MIDI bend here: `layer` bends the take.
BEND = {"bend": [[0, 0], [0.6, 0], [1.3, 65], [1.95, 65], [2.0, 0], [3.0, 0]]}
K1 = [(0, 1, "F#4")] + _G6 + [(12, 3, "A#4", BEND), (15, 1, "G#4")]
K2 = [(0, 1, "F#4")] + _G6 + [(12, 3, "F4", BEND), (15, 1, "D#4")]
K4 = [(0, 2, "A#4")] + H4[2:]
B1 = [(0, 1, "F#4"), (1, 1, "G#4"), (3, 1, "G#4"), (5, 1, "G#4"), (7, 1, "G#4"), (8, 1, "F#4"), (9, 1, "G#4"),
      (11, 1, "G#4"), (13, 1, "G#4"), (15, 1, "G#4")]
B2 = [(0, 1, "F#4"), (1, 1, "G#4"), (3, 1, "G#4"), (4, 1, "F#4"), (5, 1, "G#4"), (7, 1, "G#4"), (8, 1, "F#4"),
      (9, 1, "G#4"), (11, 1, "G#4")]
# The record's lead: root (G#4 on the sweep's best tone), a fifth above and an octave below, each a take of
# its own - the lead tones are MONO (a chord sent to one sounds only one note). Gains to the root's.
LEAD_LAYERS = {"lead": 0, "lead5": 7, "leadsub": -12}
REL = {"lead5": -4.0, "leadsub": -6.0, "pluck_echo": -8.0}
GROUP = {"lead5": "lead", "leadsub": "lead"}


LEGATO = 0.5          # 16ths a legato note is held past the next note's start (voice_line cuts 30 ms: ~30 ms overlap)


def lead_notes(bars, shift=0):
    out = []
    for i, pat in enumerate(bars, 1):
        for q, l, r, *opt in pat:
            o = opt[0] if opt else None
            n = ev(i, q, l + (LEGATO if o == "L" else 0), name(midi(r) + shift))
            out.append(n + [o] if isinstance(o, dict) else n)
    return out


def lead_voices(suffix, at, n, bars):
    return {lv + suffix: {"at": at, "bars": n, "notes": lead_notes(bars, sh)} for lv, sh in LEAD_LAYERS.items()}


# ---- chords -------------------------------------------------------------------------------------
PAD = {"G#m": "G#3 D#4 G#4 B4 D#5 G#5", "B": "F#3 B3 D#4 F#4 B4 D#5 F#5", "C#": "G#3 C#4 F4 G#4 C#5 F5 G#5",
       "E": "G#3 B3 E4 G#4 B4 E5 F#5 G#5"}
LOW = {"G#m": "G#2", "B": "B2", "C#": "C#3", "E": "E3"}
BASS = {"G#m": "G#1", "B": "B1", "C#": "C#2"}
P_RHYTHM = [("G#m", 1, 0, 8), ("B", 1, 8, 6), ("C#", 1, 14, 18)]          # 2-bar pattern
P_AT = [1, 3, 5] + list(range(36, 52, 2)) + list(range(70, 86, 2)) + list(range(86, 94, 2)) \
       + list(range(110, 118, 2)) + list(range(118, 126, 2))


# ---- the playback layer: one ROM tone per voice (TEMP scene over INIT slot 33, no scene kept: nobody
# plays these live), takes over the contiguous bars of each voice, gains = the voice at the stem's level
# voice group -> tone, or [(tone, dB to the group), ...] for a layered sound (gm800_part.py sweep, 2026-11-20:
# lead 206 tones of Synth Lead + Synth Brass, pad 154 of Synth Brass + Synth Pad/Str, bass 116 Synth Bass,
# pluck 56 Synth Pluck; scores and the checks in wiki/songs/serebro-mama-lyuba.md)
SOUND = {"pad": [(256, 0.0), (287, -3.0)], "padlow": [(256, 0.0), (287, -3.0)],   # Bright Brass Oct + Aurora Pad
         "stab": 256, "lead": 922, "bass": 129, "pluck": 354}                     # Wave Shape Ld, XMod Rubber Bass,
                                                                                   # Lo-Fi Comp Pluck
TRANSPOSE = {}        # voice -> semitones sent off the written pitch (a tone that sounds an octave low: 12)
GAIN = {"pad": 10.6, "padlow": 12.1, "lead": 17.5, "stab": 7.2, "pluck": 6.1, "bass": -2.3}   # `calibrate`, 2026-11-20 (v2: MIDI hook, chords back to back)
DUCK = {"stem": "drums", "db": 7, "release_ms": 70}     # the record's sidechain on the synths
# per section, against the stems there after `calibrate` (the record mixes the same part differently):
# the hook sits low under the vocal in 110-117 and 102-109, the intro is a bit hotter, the final hit quiet
ADJ = {"intro": 2.1, "var": -4.1, "build": -4.1, "chorus": -6.8, "end": -10.4,
       "lead": 1.5, "lead5": 1.5, "leadsub": 1.5}      # by voice name: the hook of the two solos
INTRO_TO = 12


def spans(v):
    """contiguous [from, to) bar ranges a voice plays in."""
    out = []
    for a in sorted(v["at"]):
        b = a + v["bars"]
        if out and out[-1][1] == a:
            out[-1][1] = b
        else:
            out.append([a, b])
    return out


def layer(voices):
    takes = []
    for vn, v in voices.items():
        base = vn.split("_")[0]; grp = GROUP.get(base, base)
        snd = SOUND.get(vn) or SOUND.get(grp)
        if not snd:
            continue
        tr = TRANSPOSE.get(vn, TRANSPOSE.get(grp, TRANSPOSE.get(base, 0)))
        for tone, rel in (snd if isinstance(snd, list) else [(snd, 0.0)]):
            g = GAIN.get(grp, 0.0) + REL.get(vn, REL.get(base, 0.0)) + rel
            suf = vn.split("_")[1] if "_" in vn and vn != "pluck_echo" else ""
            for a, b in spans(v):
                adj = ADJ.get(vn, ADJ.get(suf, ADJ["intro"] if a < INTRO_TO else 0.0))
                takes.append({"voice": vn, "tone": tone, "base": 33, "bars": [a, b], "gain_db": round(g + adj, 1)}
                             | ({"transpose": tr} if tr else {}))
    return {"file": "pb-synths", "duck": DUCK, "takes": takes}


# the chords follow each other with no hole (Alex 2026-11-20: «третья нота в основном риффе — обрыв, должно быть
# легато»: with the default 30 ms gap Bright Brass Oct drops 15-19 dB before every chord); each chord is still struck
GAP = 0.002


def chord_voice(table, at, extra=()):
    notes = [ev(b, q, l, table[c]) for c, b, q, l in P_RHYTHM]
    return {"at": at, "bars": 2, "gap": GAP, "notes": notes}


def build():
    voices = {
        "pad": chord_voice(PAD, P_AT),
        "padlow": chord_voice(LOW, P_AT),
        "pad_intro": {"gap": GAP, "at": [7], "bars": 5, "notes": [ev(1, 0, 14, PAD["E"]), ev(1, 14, 66, PAD["C#"])]},
        "padlow_intro": {"gap": GAP, "at": [7], "bars": 5, "notes": [ev(1, 0, 14, LOW["E"]), ev(1, 14, 66, LOW["C#"])]},
        "pad_end": {"gap": GAP, "at": [126], "bars": 1, "notes": [ev(1, 0, 8, PAD["G#m"])]},
        "padlow_end": {"gap": GAP, "at": [126], "bars": 1, "notes": [ev(1, 0, 8, LOW["G#m"])]},
        "bass": {"at": [1, 3, 5], "bars": 2, "gap": GAP, "notes": [ev(b, q, l, BASS[c]) for c, b, q, l in P_RHYTHM]},
        "bass_intro": {"gap": GAP, "at": [7], "bars": 5, "notes": [ev(1, 14, 66, BASS["C#"])]},
        "stab": {"at": list(range(13, 36, 2)) + list(range(53, 68, 2)), "bars": 2,      # 2: one take a verse
                 "notes": [ev(1, 14, 2, "F3 F#4 G#4 B4 D#5")]},
        "pluck": {"at": [21, 25, 29, 33], "bars": 4, "notes": [ev(1, 0, 1, "G#5"), ev(1, 2, 1, "C#5")]},
        "pluck_echo": {"at": [21, 25, 29, 33], "bars": 4,
                       "notes": [ev(1, q, 1, n) for q, n in ((3, "G#5"), (5, "C#5"), (6, "G#5"), (8, "C#5"), (9, "G#5"))]},
    }
    voices.update(lead_voices("", [86, 90, 118, 122], 4, [H1, H2, H1, H4]))
    voices.update(lead_voices("_kick", [94, 98], 4, [K1, K2, K1, K4]))
    voices.update(lead_voices("_chorus", [110], 8, [H1, H2, H1, H2, H1, H2, H1, H4]))
    voices.update(lead_voices("_var", [102, 104, 106], 2, [K1, K2]))
    voices.update(lead_voices("_build", [108], 2, [B1, B2]))
    voices.update(lead_voices("_end", [126], 1, [[(0, 4, "G#4")]]))
    part = {
        "_about": "Synths of «Мама Люба» (Moises keys + wind + strings) written out for the GM-800; generated by "
        "tools/jamzone/prep_mama_lyuba.py notes (edit there, not here). Band key (G#m), mix.json bars. "
        "Not checked by ear yet; sounds chosen by Claude by patch (Alex 2026-11-20).",
        "stems": ["keys", "wind", "strings"],
        "voices": voices,
    }
    if SOUND:
        part["layer"] = layer(voices)
    return part


def cmd_notes():
    part = build()
    os.makedirs(os.path.dirname(PART), exist_ok=True)
    with open(PART, "w", encoding="utf-8") as f:
        f.write("{\n")
        items = list(part.items())
        for i, (k, v) in enumerate(items):
            if k == "voices":
                f.write(' "voices": {\n')
                vs = list(v.items())
                for j, (vn, vv) in enumerate(vs):
                    gap = f'"gap": {vv["gap"]}, ' if "gap" in vv else ""
                    f.write(f'  {json.dumps(vn)}: {{{gap}"at": {json.dumps(vv["at"])}, "bars": {vv["bars"]}, "notes": [\n')
                    f.write(",\n".join("   " + json.dumps(n, ensure_ascii=False) for n in vv["notes"]))
                    f.write("]}" + ("," if j < len(vs) - 1 else "") + "\n")
                f.write(" }" + ("," if i < len(items) - 1 else "") + "\n")
            elif k == "layer":
                head = {kk: vv for kk, vv in v.items() if kk != "takes"}
                f.write(f' "layer": {json.dumps(head)[:-1]}, "takes": [\n')
                f.write(",\n".join("   " + json.dumps(t) for t in v["takes"]))
                f.write("]}" + ("," if i < len(items) - 1 else "") + "\n")
            else:
                f.write(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" + ("," if i < len(items) - 1 else "") + "\n")
        f.write("}\n")
    n = sum(len(v["notes"]) * len(v["at"]) for v in part["voices"].values())
    print(f"{len(part['voices'])} voices, {n} note events -> {PART}")


# ---- FX: what in the synth stems is not notes ---------------------------------------------------
# (from, to) in bars (fractions = beats/4), stem kept there; "lp" = low-passed (the boom under the hook)
FX_KEEP = [(12, 36), (52, 70)]                       # verses + guitar break: impacts, noise, the bar-4 hit
FX_CUT = [(b + 0.6875, b + 1.0) for b in list(range(13, 36, 2)) + list(range(53, 68, 2))] \
       + [(b, b + 0.9375) for b in (21, 25, 29, 33)]   # the written stab (from 4.3) and pluck bars
FX_LOW = [(b, b + 0.5) for b in (102, 104, 106, 108)]  # the boom on the downbeats of 102-109 (G#1-A#2)
FX_TAIL = [(126.375, 130)]                            # the final fall after the written hit
XF = 0.010


def cmd_fx():
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt
    tl = json.load(open(os.path.join(SONG, "auto-render", "timeline.json")))
    mix = json.load(open(os.path.join(SONG, "mix.json")))
    bar = tl["bar_sec"]; c = mix["cues"][0]
    t_stem = lambda b: c["abs_sec"] - (c["bar"] - 1) * bar + (b - 1) * bar - tl["offset_sec"]
    x, sr = 0, None
    for s in ("keys", "wind", "strings"):
        y, sr = sf.read(os.path.join(SONG, s + ".mp3"), always_2d=True)
        x = x + y
    n = len(x); f = int(XF * sr)

    def mask(spans):
        m = np.zeros(n)
        for a, b in spans:
            i, j = int(t_stem(a) * sr), min(n, int(t_stem(b) * sr))
            m[i:j] = 1
            m[max(0, i - f):i] = np.linspace(0, 1, i - max(0, i - f)); m[j:j + f] = np.maximum(m[j:j + f], np.linspace(1, 0, len(m[j:j + f])))
        return m
    keep = mask(FX_KEEP) * (1 - mask(FX_CUT)) + mask(FX_TAIL)
    low = sosfiltfilt(butter(4, 150, "lowpass", fs=sr, output="sos"), x, axis=0)
    out = x * keep[:, None] + low * mask(FX_LOW)[:, None]
    dst = os.path.join(SONG, "parts", "pb-fx.wav")
    sf.write(dst, out.astype(np.float32), sr, subtype="FLOAT")
    r = lambda y: 10 * np.log10(np.mean(y ** 2) + 1e-20)
    print(f"-> {dst}: {r(out) - r(x):+.1f} dB of the synth stems' energy kept")


# ---- calibrate: every voice at the level of the stems where it plays ------------------------------
# voice -> (windows [(from, to) bars], band Hz or None); the stems there hold (almost) only that part
STAB_W = [(b + 0.6875, b + 1.0) for b in list(range(13, 36, 2)) + list(range(53, 68, 2))]
CAL = {"pad": ([(36, 52)], (180, 12000)), "padlow": ([(36, 52)], (40, 180)),
       "lead": ([(94, 102)], None), "stab": (STAB_W, None),
       "pluck": ([(b, b + 0.9375) for b in (21, 25, 29, 33)], (400, 12000)), "bass": ([(1, 7)], (30, 90))}


def cmd_calibrate():
    import importlib.util
    import soundfile as sf
    import pyloudnorm as pyln
    from scipy.signal import butter, sosfiltfilt, resample_poly
    sys.argv = sys.argv[:1]
    spec = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
    gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
    song = gp.gmm.Song("Мама Люба"); part = json.load(open(PART, encoding="utf-8")); lay = part["layer"]
    stem, sr = 0, None
    for s in part["stems"]:
        y, sr = sf.read(song.stem(s), always_2d=True); stem = stem + y.mean(1)
    duck = gp.duck_gain(song, lay["duck"], len(stem), sr)
    meter = pyln.Meter(sr)

    def level(x, wins, band):
        if band:
            x = sosfiltfilt(butter(4, band, "bandpass", fs=sr, output="sos"), x)
        seg = np.concatenate([x[int(song.t_stem(a) * sr):int(song.t_stem(b) * sr)] for a, b in wins])
        return meter.integrated_loudness(np.stack([seg, seg], 1))
    print("voice      stem   take   gain (dB, LUFS of the windows)")
    for vn, (wins, band) in CAL.items():
        buf = np.zeros(len(stem))
        for tk in lay["takes"]:
            base = tk["voice"].split("_")[0]
            if GROUP.get(base, base) != vn:
                continue                                  # takes carry GAIN + their relative gain: keep the latter
            x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).mean(1).astype(np.float64) \
                * 10 ** ((tk["gain_db"] - GAIN.get(vn, 0.0)) / 20)
            if sr != gp.SR:
                x = resample_poly(x, sr, gp.SR)
            a = int(round(song.t_stem(tk["bars"][0]) * sr)); m = min(len(x), len(buf) - a)
            buf[a:a + m] += x[:m]
        ls, lt = level(stem, wins, band), level(buf * duck, wins, band)
        print(f"  {vn:8} {ls:6.1f} {lt:6.1f}  {ls - lt:+5.1f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "notes":
        cmd_notes()
    elif cmd == "calibrate":
        cmd_calibrate()
    elif cmd == "fx":
        cmd_fx()
    else:
        sys.exit(__doc__)
