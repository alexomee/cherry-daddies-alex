#!/usr/bin/env python3
"""Play a written keys part on the GM-800 and record it (wiki/pipelines/gm-800-parts.md).

A part that was a cut Moises stem in the playback is written out as notes, the GM-800 plays it
from MIDI over USB on the chosen scene parts, and the recording becomes the playback layer -
the same sound Alex plays live on that scene.

    gmp() { uv run -q --python 3.12 --with sounddevice --with numpy --with scipy --with python-rtmidi \
            --with soundfile --with pyloudnorm tools/gm800_part.py "$@"; }
    gmp probe 57 51                          # parts of the scenes: tone, switch, level, octave
    gmp take "<song>" NOTES.json low 57      # voice "low" on scene 57, every part that is on
    gmp take "<song>" NOTES.json low 57 --parts 1,3 [--bars 9 13]   # only these parts
    gmp preview "<song>" NOTES.json [--bars 9 13]                   # stem vs takes, mp3, same loudness
    gmp record "<song>" NOTES.json           # every take of the "layer" spec, time-locked (see below)
    gmp layer "<song>" NOTES.json            # takes -> parts/<file>.wav (stem frame), offline
    gmp balance 51 3:127 1:110,60,30,15      # loudness of part 1 at these PART LEVELs against part 3 at 127
    gmp tones "<song>" A6 223,224,886 [--base 33]   # one held note on ROM tones: harmonics, attack, pitch
    gmp loudness 30 34 [--phrase "A3 C4 E4 A4"]   # scenes against each other: same phrase, LUFS by USB
    gmp scene 32 51 "NE ISHI PAD" --parts 3:127,1:24 --octave 1     # new scene in an INIT slot
    gmp copy 147 34 "NE ISHI SOLO 2"         # a scene as it is into an INIT slot (scenes above 128
                                             # can't be called by a plain PC: wiki/pipelines/gm-800.md)
    gmp part 30:1 34:4 [--level 127]        # one part of a scene into a part of another scene
                                             # (tone, modify, MFX, output; the target's strings stay)

NOTES.json (lives in the song's parts/ folder, bars = mix.json bars):
    {"stems": ["keys", "strings"],
     "voices": {"low": {"at": [9, 13, 17, 21], "bars": 4,
                        "notes": [[1, 1, 4, "A1 A3"], [2, 1, 4, "A1 A3"], ...]}}}
    note = [bar inside the pattern, beat, length in beats, pitches]; "at" = bars where the pattern starts.

Notes go straight to the part's own MIDI channel at sounding pitch (the part's octave shift,
measured by a probe note, is taken out), not through the guitar strings: the playback does not
have to be playable. NOTE SOURCE goes to USB for the run and is always put back; scene 1 (MUTE)
is loaded at the end. Nothing is written to the GM-800's memory - except `scene`, which writes one
user slot (must be INIT unless --force; SysEx dumps before/after in gear/gm-800/backups/sysex/).

The playback layer is described in NOTES.json:
    "layer": {"file": "pb-keys-pad", "takes": [
        {"voice": "low", "scene": 57, "parts": [3], "bars": [9, 25], "gain_db": -6.0},
        {"voice": "line", "tone": 272, "base": 33, "bars": [41, 57], "gain_db": 0, "fade": [54, 56.25]}]}
(a take is a scene, whole or some of its parts, or one ROM tone in part 1 of an INIT scene - for
a part nobody plays live, so no scene is kept for it)
`record` plays each take and cuts it so that sample 0 is the bar line of its first bar: the USB
record chain has a latency that changes from run to run, so every take starts with a short note
on a sharp scene (SYNC_SCENE), its onset gives the latency of this very recording, then the
target scene is loaded and the part starts SYNC_T0 seconds in. `layer` sums the takes with their
gains at their bars into parts/<file>.wav in the stem frame (a "frame": "stem" layer of mix.json).

`scene` = the template scene with only the listed parts on, at the given PART LEVELs, their
TONE MOD > OCT SHIFT set (ToneModifyCommon +02: so that a part written high sits in a comfortable
guitar position; the scene's own Common OCTAVE SHIFT does not move MIDI notes, so it can't be
checked from here and is left alone) and a new name. `balance` finds the PART LEVEL that puts one part N dB under another: PART LEVEL
is not in dB, so it is measured (a held chord, each part alone, LUFS of the USB take).
Output: analysis/gm800-match/<song>/part-*.wav (not in git).
"""
import argparse, csv, importlib.util, json, os, subprocess, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("gmm", os.path.join(REPO, "tools", "gm800_match.py"))
gmm = importlib.util.module_from_spec(_s); _s.loader.exec_module(gmm)
SR = gmm.SR
NAMES = "C C# D D# E F F# G G# A A# B".split()
FLAT = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}


def midi_of(s):
    name, octv = s[:-1], int(s[-1])
    return NAMES.index(FLAT.get(name, name)) + 12 * (octv + 1)


def tone_names():
    out = {}
    for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t"):
        out[(int(r[2]), int(r[3]), int(r[4]))] = (int(r[0]), r[1])
    return out


def probe_shift(rig, ch):
    """Octave shift of the part on MIDI channel `ch`, in semitones (None = silent)."""
    p = rig.play([(0.0, 45, 1.0)], lambda n: [ch], tail=0.3)[int(0.4 * SR):int(0.95 * SR)].mean(1)
    if np.sqrt((p ** 2).mean()) < 1e-4:
        return None
    return int(round((12 * np.log2(gmm.f0_of(p) / 440) + 69 - 45) / 12)) * 12


def scene_parts(rig, tones):
    """[(part, ch, on, tone no, tone name, level)] of the loaded scene, parts 1-4."""
    out = []
    for p in range(4):
        ts = rig.g.rq([0x10, 0x02, p, 0], 12)
        if not ts:
            continue
        num, name = tones.get((ts[0], ts[1], ts[2] + 1), (0, f"? {ts[0]}/{ts[1]}/{ts[2] + 1}"))
        out.append((p + 1, rig.part_ch[p], bool(ts[4]) and not ts[8], num, name, ts[6]))
    return out


def cmd_probe(scenes):
    tones = tone_names()
    with gmm.Rig() as rig:
        for sc in scenes:
            nm, _ = rig.load(sc)
            lvl = rig.g.rq([0x10, 0, 0, 0x13], 1)
            print(f"scene {sc} '{nm}'  scene level {lvl[0] if lvl else '?'}")
            for p, ch, on, num, name, level in scene_parts(rig, tones):
                sh = probe_shift(rig, ch) if on else None
                print(f"   part {p}  ch {ch + 1:2}  {'ON ' if on else 'off'}  tone {num:4} {name:18} "
                      f"level {level:3}  octave {'silent' if sh is None else f'{sh // 12:+d}'}", flush=True)


def voice_line(song, part, voice, b0, b1):
    """[(seconds from bar b0, midi, seconds)] of a voice inside bars [b0, b1)."""
    v = part["voices"][voice]; beat = song.bar / 4; line = []
    gap = v.get("gap", 0.03)            # s of silence before the next note; a brass with a short release opens
    for at in v["at"]:                  # an audible hole with 30 ms: chords played back to back use 0.002, and a
        for bar, bt, ln, pitches, *_ in v["notes"]:   # NEGATIVE gap overlaps the next chord (legato: no hole
            pos = at + bar - 1 + (bt - 1) / 4          # while the next attack builds up). 5th element = options
            if b0 <= pos < b1:
                for s in pitches.split():
                    line.append(((pos - b0) * song.bar, midi_of(s), ln * beat - gap))
    line.sort()
    if gap < 0:                         # an overlap must not run into the same pitch struck again: its note-off
        nxt = {}                        # would cut the new note - such a note ends 2 ms before it instead
        for i in range(len(line) - 1, -1, -1):
            t, n, d = line[i]
            if n in nxt and t + d > nxt[n] - 0.002:
                line[i] = (t, n, nxt[n] - 0.002 - t)
            nxt[n] = t
    return line


def voice_bends(song, part, voice, b0, b1):
    """Bends of a voice inside bars [b0, b1): [[(seconds from bar b0, semitones), ...], ...], one curve a note.
    A note may carry {"bend": [[16ths from the note start, cents], ...]} as its 5th element; the GM-800 ignores
    MIDI pitch bend in the TEMP scene (measured 2026-11-20), so `layer` bends the recorded take instead."""
    v = part["voices"][voice]; out = []
    for at in v["at"]:
        for n in v["notes"]:
            opt = n[4] if len(n) > 4 and isinstance(n[4], dict) else {}
            pos = at + n[0] - 1 + (n[1] - 1) / 4
            if opt.get("bend") and b0 <= pos < b1:
                t0 = (pos - b0) * song.bar
                out.append([(t0 + q * song.bar / 16, c / 100) for q, c in opt["bend"]])
    return out


PITCHMAP_EARLY = 0.064    # s: a step in a rubberband 4.0 --pitchmap is half way 64 ms BEFORE its frame (measured
                          # 2026-11-20 on a 220 Hz saw, 48 kHz), and smoothed over ~40 ms


def voice_gains(song, part, voice, b0, b1):
    """[(seconds from bar b0, seconds, dB)] of the notes of a voice that carry {"gain_db": x} (5th element):
    the take is turned down/up over that note, like playing it softer (a chord of a brass that comes out
    louder than in the record)."""
    v = part["voices"][voice]; out = []
    for at in v["at"]:
        for n in v["notes"]:
            opt = n[4] if len(n) > 4 and isinstance(n[4], dict) else {}
            pos = at + n[0] - 1 + (n[1] - 1) / 4
            if opt.get("gain_db") and b0 <= pos < b1:
                out.append(((pos - b0) * song.bar, n[2] * song.bar / 4, opt["gain_db"]))
    return out


def apply_gains(x, spans, sr, ramp=0.008):
    if not spans:
        return x
    g = np.zeros(len(x)); r = int(ramp * sr)
    for t0, d, db in spans:
        i, j = int(t0 * sr), int((t0 + d) * sr); w = np.zeros(len(x)); w[i:j] = 1
        w[max(0, i - r):i] = np.linspace(0, 1, i - max(0, i - r)); w[j:j + r] = np.linspace(1, 0, len(w[j:j + r]))
        g += w * db
    return x * (10 ** (g / 20))[:, None]


def apply_bends(x, curves, sr):
    """Bend the take x (stereo, sample 0 = its first bar) along the curves with rubberband --pitchmap; the
    bent audio replaces the take only inside each curve (+-15 ms, 10 ms crossfades). The rubberband delay
    is measured against the take (cross-correlation outside the curves) and taken out."""
    import tempfile, soundfile as sf
    if not curves:
        return x
    step = int(0.004 * sr); pts = [(0, 0.0)]
    early = int(PITCHMAP_EARLY * sr)       # rubberband applies the map this much ahead: write it that much later
    for cv in curves:
        (ta, _), (tb, _) = cv[0], cv[-1]
        for i in range(int(ta * sr), int(tb * sr) + step, step):
            t = i / sr; ts = [p[0] for p in cv]; vs = [p[1] for p in cv]
            pts.append((i + early, float(np.interp(t, ts, vs))))
        pts.append((int(tb * sr) + step + early, 0.0))
    pts = sorted(dict(pts).items())
    with tempfile.TemporaryDirectory() as td:
        fi, fo, fm = (os.path.join(td, n) for n in ("in.wav", "out.wav", "map.txt"))
        sf.write(fi, x.astype(np.float32), sr, subtype="FLOAT")
        open(fm, "w").write("".join(f"{i} {v:.4f}\n" for i, v in pts))
        r = subprocess.run(["rubberband", "--pitchmap", fm, fi, fo], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("rubberband: " + r.stderr[-300:])
        y, _ = sf.read(fo, always_2d=True)
    # delay of the realtime engine: correlate the envelopes before the first curve
    k = int(min(curves[0][0][0], 4.0) * sr)
    if k > sr // 2:
        a, b = np.abs(x[:k].mean(1)), np.abs(y[:k + sr // 4].mean(1))
        c = [np.dot(a[:k - sr // 20], b[d:d + k - sr // 20]) for d in range(0, sr // 20, 8)]
        lag = int(np.argmax(c)) * 8
    else:
        lag = 0
    y = np.vstack([y[lag:], np.zeros((lag, 2))])[:len(x)]
    if len(y) < len(x):
        y = np.vstack([y, np.zeros((len(x) - len(y), 2))])
    out = x.copy(); f = int(0.010 * sr)
    for cv in curves:
        i, j = int((cv[0][0] - 0.015) * sr), int((cv[-1][0] + 0.015 + PITCHMAP_EARLY) * sr)
        w = np.zeros(len(x)); w[i:j] = 1; w[i - f:i] = np.linspace(0, 1, f); w[j:j + f] = np.linspace(1, 0, f)
        out = out * (1 - w[:, None]) + y * w[:, None]
    print(f"   bent {len(curves)} notes (rubberband delay {lag / sr * 1000:.1f} ms taken out)")
    return out


def take_path(song, part_file, voice, scene, parts, b0, b1):
    base = os.path.basename(part_file).replace(".notes.json", "").replace(".json", "")
    tag = "all" if not parts else "p" + "".join(map(str, parts))
    return os.path.join(song.out, f"part-{base}-{voice}-s{scene:03d}-{tag}-{b0}-{b1}.wav")


def cmd_take(song, part_file, voice, scene, parts, b0, b1, as_played=False, vel=None):
    part = json.load(open(part_file, encoding="utf-8")); tones = tone_names()
    line = voice_line(song, part, voice, b0, b1)
    if not line:
        raise SystemExit(f"voice '{voice}' has no notes in bars {b0}-{b1}")
    with gmm.Rig() as rig:
        nm, _ = rig.load(scene)
        sp = [x for x in scene_parts(rig, tones) if (x[0] in parts if parts else x[2])]
        shifts = {}
        for p, ch, on, num, name, level in sp:
            sh = probe_shift(rig, ch)
            print(f"scene {scene} '{nm}' part {p}: tone {num} {name}, level {level}, "
                  f"octave {'silent' if sh is None else f'{sh // 12:+d}'}", flush=True)
            if sh is not None:
                shifts[ch] = sh
        if not shifts:
            raise SystemExit("no sounding part")
        if as_played:                                       # every part the same note, as on the guitar
            ref = min(shifts.values()); shifts = {ch: ref for ch in shifts}
        if vel:
            gmm.VEL = vel                                   # how hard: a resonant poly opens its filter with it
        time.sleep(1.5)                                     # let the probe tails die
        ev = [(t, n - sh, d, ch) for t, n, d in line for ch, sh in shifts.items()]
        x = play(rig, ev)
    out = take_path(song, part_file, voice, scene, parts, b0, b1)
    if vel:
        out = out.replace(".wav", f"-v{vel}.wav")
    gmm.save(out, x)
    print(f"{len(line)} notes x {len(shifts)} parts -> {out}  LUFS {gmm.lufs(x):.1f}  peak "
          f"{20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS")


def play(rig, ev, tail=2.5):
    """ev = [(t, midi, dur, channel)] -> stereo USB take that starts at t = 0."""
    dur = max(t + d for t, _, d, _ in ev) + tail
    rec = rig.sd.rec(int((dur + 0.4) * SR), SR, channels=2, device=rig.dev)
    t0 = time.perf_counter() + 0.4
    seq = sorted([(t, 0x90, n, ch) for t, n, d, ch in ev] + [(t + d, 0x80, n, ch) for t, n, d, ch in ev],
                 key=lambda e: (e[0], e[1] == 0x90))
    for t, st, n, ch in seq:
        while time.perf_counter() < t0 + t:
            time.sleep(0.0005)
        rig.g.out.send_message([st | ch, n, gmm.VEL if st == 0x90 else 0])
    rig.sd.wait()
    return rec[int(0.4 * SR):]


SYNC_SCENE, SYNC_AT, SYNC_T0 = 7, 0.3, 3.0     # sharp bass scene; marker time; part start (s)


def rec_path(song, part_file, tk):
    base = os.path.basename(part_file).replace(".notes.json", "")
    if tk.get("tone"):
        src = f"t{tk['tone']:04d}"
    else:
        src = f"s{tk['scene']:03d}-" + ("all" if not tk.get("parts") else "p" + "".join(map(str, tk["parts"])))
    return os.path.join(song.out, f"rec-{base}-{tk['voice']}-{src}-{tk['bars'][0]}-{tk['bars'][1]}.wav")


def cmd_record(song, part_file, only=None, tail=4.0):
    part = json.load(open(part_file, encoding="utf-8")); tones = tone_names()
    with gmm.Rig() as rig:
        for i, tk in enumerate(part["layer"]["takes"]):
            if only is not None and i not in only:
                continue
            b0, b1 = tk["bars"]; tr = tk.get("transpose", 0)          # semitones: a tone that sounds an octave off
            line = [(t, n + tr, d) for t, n, d in voice_line(song, part, tk["voice"], b0, b1)]
            tone_msg = None
            if tk.get("tone"):                               # a ROM tone in part 1 of the TEMP scene
                scene = tk.get("base", 33); nm, _ = rig.load(scene)
                if "INIT" not in nm.upper():
                    raise SystemExit(f"take {i}: base scene {scene} is '{nm}', not INIT")
                r = next(r for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t") if int(r[0]) == tk["tone"])
                rig.tone(int(r[2]), int(r[3]), int(r[4])); nm = f"{r[0]} {r[1]}"
                body = [0x10, 0x02, 0x00, 0x00, int(r[2]), int(r[3]), int(r[4]) - 1]
                tone_msg = gmm.HDR + [0x12] + body + [gmm.csum(body), 0xF7]
                sp = [(1, rig.part_ch[0], True, tk["tone"], r[1], 0)]
            else:
                scene = tk["scene"]; nm, _ = rig.load(scene)
                sp = [x for x in scene_parts(rig, tones) if (x[0] in tk["parts"] if tk.get("parts") else x[2])]
            shifts = {}
            for pnum, ch, on, num, name, level in sp:
                sh = probe_shift(rig, ch)
                if sh is not None:
                    shifts[ch] = sh
            if not shifts or not line:
                raise SystemExit(f"take {i}: nothing to play")
            if tk.get("as_played") and shifts:       # the scene as Alex plays it: every part gets the same note
                ref = min(shifts.values())           # (its lowest part sounds at the written pitch, the parts
                shifts = {ch: ref for ch in shifts}  # shifted up stay above it, as on the guitar)
            rig.load(SYNC_SCENE)
            msgs = [(SYNC_AT, [0x90 | ch, 45, 110]) for ch in rig.part_ch[:4]]
            msgs += [(SYNC_AT + 0.08, [0x80 | ch, 45, 0]) for ch in rig.part_ch[:4]]
            msgs += [(SYNC_AT + 0.5, [0xC0 | (rig.scene_ch - 1), scene - 1])]     # bank 0 is set: rig.load
            if tone_msg:
                msgs += [(SYNC_AT + 1.4, tone_msg)]
            for t, n, d in line:
                for ch, sh in shifts.items():
                    msgs += [(SYNC_T0 + t, [0x90 | ch, n - sh, tk.get("vel", gmm.VEL)]), (SYNC_T0 + t + d, [0x80 | ch, n - sh, 0])]
            dur = SYNC_T0 + (b1 - b0) * song.bar + tail
            rec = rig.sd.rec(int((dur + 0.4) * SR), SR, channels=2, device=rig.dev)
            t0 = time.perf_counter() + 0.4
            for t, m in sorted(msgs, key=lambda e: (e[0], e[1][0] & 0xF0 == 0x90)):
                while time.perf_counter() < t0 + t:
                    time.sleep(0.0005)
                rig.g.out.send_message(m)
            rig.sd.wait(); x = rec[int(0.4 * SR):]
            env = np.abs(x[:int((SYNC_AT + 0.45) * SR)]).max(1); pk = env.max()
            if pk < 1e-3:
                raise SystemExit(f"take {i}: no sync note in the recording")
            on = int(np.argmax(env > 0.2 * pk)) / SR; lat = on - SYNC_AT
            if not -0.01 < lat < 0.2:
                raise SystemExit(f"take {i}: sync onset at {on:.3f} s, latency {lat * 1000:.0f} ms - not plausible")
            y = x[int(round((SYNC_T0 + lat) * SR)):]
            out = rec_path(song, part_file, tk); gmm.save(out, y)
            print(f"take {i}: {tk['voice']} bars {b0}-{b1} on scene {scene} '{nm}' parts "
                  f"{[q[0] for q in sp]}: latency {lat * 1000:.1f} ms, LUFS {gmm.lufs(y):.1f}, peak "
                  f"{20 * np.log10(np.abs(y).max() + 1e-9):.1f} -> {os.path.basename(out)}", flush=True)


def cmd_layer(song, part_file):
    import soundfile as sf
    from scipy.signal import resample_poly
    part = json.load(open(part_file, encoding="utf-8")); lay = part["layer"]
    info = sf.info(song.stem(part.get("stems", ["keys"])[0])); sr = info.samplerate
    out = np.zeros((info.frames, 2), dtype=np.float64)
    for tk in lay["takes"]:
        x = gmm.read_wav(rec_path(song, part_file, tk)).astype(np.float64) * 10 ** (tk.get("gain_db", 0) / 20)
        x = apply_gains(x, voice_gains(song, part, tk["voice"], *tk["bars"]), SR)
        x = apply_bends(x, voice_bends(song, part, tk["voice"], *tk["bars"]), SR)
        n = int(0.3 * SR); x[-n:] *= np.linspace(1, 0, n)[:, None]; x[:48] *= np.linspace(0, 1, 48)[:, None]
        if tk.get("fade"):                                   # [from bar, to bar]: linear fade to silence
            f0, f1 = (int((b - tk["bars"][0]) * song.bar * SR) for b in tk["fade"])
            x[f0:f1] *= np.linspace(1, 0, f1 - f0)[:, None]; x[f1:] = 0
        if sr != SR:
            x = resample_poly(x, sr, SR, axis=0)
        a = int(round(song.t_stem(tk["bars"][0]) * sr)); m = min(len(x), len(out) - a)
        out[a:a + m] += x[:m]
    if lay.get("duck"):                                      # sidechain pumping of the record, keyed by its kick
        out *= duck_gain(song, lay["duck"], len(out), sr)[:, None]
    dst = os.path.join(song.dir, "parts", lay["file"] + ".wav")
    sf.write(dst, out.astype(np.float32), sr, subtype="FLOAT")
    print(f"{len(lay['takes'])} takes -> {dst}  peak {20 * np.log10(np.abs(out).max() + 1e-9):.1f} dBFS")


def duck_gain(song, spec, n, sr):
    """Gain curve (stem frame) that ducks the layer on every kick of the record, like the sidechain
    the producer put on the synths. spec = {"stem": "drums", "db": 7, "release_ms": 120, "lowpass": 150,
    "advance_ms": 0}:
    kick = the low band of the drum stem, a peak follower (5 ms attack, release_ms) normalised to the
    typical kick (90th percentile of its peaks); gain = -db x kick (clipped to 1). Where the record has
    no kick (a kick stop) nothing ducks."""
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt, resample_poly, find_peaks
    y, ysr = sf.read(song.stem(spec.get("stem", "drums")), always_2d=True)
    y = sosfiltfilt(butter(4, spec.get("lowpass", 150), "lowpass", fs=ysr, output="sos"), y.mean(1))
    if ysr != sr:
        y = resample_poly(y, sr, ysr)
    k = sr // 1000; m = len(y) // k; ms = k / sr * 1000     # ~1 ms steps (exactly k samples)
    e = np.abs(y[:m * k]).reshape(m, k).max(1)
    env = np.zeros(m); a = np.exp(-ms / 5.0); r = np.exp(-ms / spec.get("release_ms", 120)); v = 0.0
    for i in range(m):                            # peak follower: fast attack, exponential release (ms steps)
        c = a if e[i] > v else r
        v = c * v + (1 - c) * e[i]
        env[i] = v
    pk, _ = find_peaks(env, distance=int(200 / ms), height=env.max() * 0.1)
    ref = np.percentile(env[pk], 90) if len(pk) else env.max()
    g = 10 ** (-spec.get("db", 7) * np.clip(env / ref, 0, 1) / 20)
    adv = int(spec.get("advance_ms", 0) / 1000 * sr)       # a compressor's lookahead: duck that much before the kick
    g = np.interp(np.arange(n) + adv, (np.arange(m) + 0.5) * k, g, right=1.0)
    return g


def note_profile(x, f0, hold):
    """Harmonics 2-4 (dB to the fundamental), seconds to reach -6 dB of the sustain level, pitch
    offset in cents and level wobble (dB, std) of a held note."""
    m = x.mean(1); a, b = int(0.8 * SR), int((hold - 0.2) * SR); seg = m[a:b] * np.hanning(b - a)
    mag = np.abs(np.fft.rfft(seg)); fr = np.fft.rfftfreq(b - a, 1 / SR)

    def pk(f):
        k = (fr > f * 0.97) & (fr < f * 1.03); i = int(np.argmax(mag[k]))
        return 20 * np.log10(mag[k][i] + 1e-12), fr[k][i]
    l1, f1 = pk(f0); hs = [pk(f0 * h)[0] - l1 for h in (2, 3, 4)]
    n = int(0.02 * SR); env = np.array([np.sqrt(np.mean(m[i:i + n] ** 2)) for i in range(0, int(hold * SR) - n, n)])
    sus = np.median(env[int(0.8 / 0.02):]); att = float(np.argmax(env > sus * 0.5)) * 0.02
    wob = float(np.std(20 * np.log10(env[int(0.8 / 0.02):] + 1e-9)))
    return hs, att, 1200 * np.log2(f1 / f0), wob


def cmd_tones(song, note, nums, base, hold=4.0):
    """One held note on ROM tones (part 1 of the TEMP scene over an INIT scene; nothing is written)."""
    tab = {int(r[0]): r for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t")}
    n = midi_of(note); f0 = 440 * 2 ** ((n - 69) / 12)
    with gmm.Rig() as rig:
        nm, _ = rig.load(base)
        if "INIT" not in nm.upper():
            raise SystemExit(f"scene {base} is '{nm}', not INIT")
        ch = rig.part_ch[0]
        print(f"note {note} ({f0:.0f} Hz), {hold} s:  h2 h3 h4 (dB) | attack s | cents | wobble dB | LUFS")
        for num in nums:
            r = tab[num]; rig.tone(int(r[2]), int(r[3]), int(r[4]))
            x = play(rig, [(0.0, n, hold, ch)], tail=2.0)
            if np.abs(x).max() < 1e-4:
                print(f"  {num:4} {r[1]:18} silent"); continue
            hs, att, cents, wob = note_profile(x, f0, hold)
            gmm.save(os.path.join(song.out, f"tone-{note}-{num:04d}.wav"), x)
            print(f"  {num:4} {r[1]:18} {hs[0]:5.0f} {hs[1]:5.0f} {hs[2]:5.0f} | {att:5.2f} | {cents:+5.0f} | {wob:4.1f} | "
                  f"{gmm.lufs(x[:int(hold * SR)]):6.1f}", flush=True)


def cmd_loudness(scenes, phrase, parts=None):
    """The same short phrase on every scene (each sounding part, at sounding pitch): LUFS of the
    USB take. For 'make scene X n dB quieter' and 'is the new scene level with the old one'."""
    ns = [midi_of(s) for s in phrase.split()]
    line = [(0.5 * i, n, 0.4) for i, n in enumerate(ns[:-1])] + [(0.5 * (len(ns) - 1), ns[-1], 1.2)]
    end = line[-1][0] + 1.3; tones = tone_names()
    with gmm.Rig() as rig:
        for sc in scenes:
            nm, _ = rig.load(sc)
            sp = [x for x in scene_parts(rig, tones) if (x[0] in parts if parts else x[2])]
            sh = {ch: (probe_shift(rig, ch) or 0) for _p, ch, *_ in sp}; time.sleep(1.2)
            x = play(rig, [(t, n - v, d, ch) for t, n, d in line for ch, v in sh.items()], tail=1.0)
            lvl = rig.g.rq([0x10, 0, 0, 0x13], 1)
            print(f"scene {sc} '{nm}' scene level {lvl[0] if lvl else '?'}, parts {[q[0] for q in sp]}: "
                  f"LUFS {gmm.lufs(x[:int(end * SR)]):.1f}  peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f}", flush=True)


def cmd_balance(tpl, ref, part, chord="E4 A4 C5"):
    (rp, rl), (pp, levels) = ref, part
    line = [(0.0, midi_of(n), 3.0) for n in chord.split()]
    with gmm.Rig() as rig:
        nm, _ = rig.load(tpl)

        def one(p, level):
            rig.g.dt([0x10, 0x02, p - 1, 0x06], [level]); time.sleep(0.2)
            sh = probe_shift(rig, rig.part_ch[p - 1]) or 0; time.sleep(1.2)
            x = play(rig, [(t, n - sh, d, rig.part_ch[p - 1]) for t, n, d in line], tail=1.0)
            return gmm.lufs(x[int(0.5 * SR):int(3.0 * SR)])
        l0 = one(rp, rl)
        print(f"scene {tpl} '{nm}': part {rp} at level {rl}: {l0:.1f} LUFS (USB, chord {chord})")
        for v in levels:
            l = one(pp, v)
            print(f"   part {pp} at level {v:3}: {l:6.1f} LUFS   {l - l0:+.1f} dB to part {rp}", flush=True)


def cmd_scene(slot, tpl, name, parts, octave, force=False):
    """parts = {part: PART LEVEL}; every other part (1-4, R) is switched off."""
    sx = gmm.Sx()
    try:
        before, pb = gmm.backup(sx, slot, "before")
        if len(before) != 88:
            raise SystemExit(f"slot {slot}: read {len(before)} of 88 blocks, not writing")
        if "INIT" not in gmm.scene_name(before).upper() and not force:
            raise SystemExit(f"slot {slot} is '{gmm.scene_name(before)}', not INIT: refusing (--force to overwrite)")
        ch = 2                                               # Scene Rx channel (gm-800.md)
        sx.o.send_message([0xB0 | (ch - 1), 0, 0]); sx.o.send_message([0xB0 | (ch - 1), 32, 0])   # bank 0
        sx.o.send_message([0xC0 | (ch - 1), tpl - 1]); time.sleep(2.5)
        for p in range(1, 6):
            sx.dt([0x10, 0x02, p - 1, 0x04], [1 if p in parts else 0])
            if p in parts:
                sx.dt([0x10, 0x02, p - 1, 0x06], [parts[p]]); sx.dt([0x10, 0x02, p - 1, 0x08], [0])
                sx.dt([0x10, 0x02, 0x10 + p - 1, 0x02], [32 + octave])     # TONE MOD > OCT SHIFT
        time.sleep(2.5)
        # A scene with heavy tones keeps sending partial blocks on its own for a while: keep only
        # the 88 blocks of the standard layout (the keys of the slot dump), same sizes.
        new = {k: v for k, v in sx.dump([0x10, 0x00]).items() if k in before and len(v) == len(before[k])}
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        new["00 00 00"][3:19] = list(name.ljust(16)[:16].encode("ascii"))
        sx.write(gmm.slot_base(slot), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, slot, "after")
        bad = [k for k in new if after.get(k) != new[k]]
        c = after["00 00 00"]
        print(f"slot {slot}: '{gmm.scene_name(before)}' -> '{gmm.scene_name(after)}' = scene {tpl}, parts "
              f"{ {p: after[f'02 {p - 1:02X} 00'][6] for p in parts} }, part octave "
              f"{ {p: after[f'02 {0x10 + p - 1:02X} 00'][2] - 32 for p in parts} }, scene level {c[0x13]}; "
              f"88 blocks written, mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC0 | (ch - 1), 0])              # leave the synth on MUTE
    finally:
        sx.close()


def cmd_copy(src, slot, name, force=False):
    """Scene `src` as stored in memory -> user slot `slot` (INIT unless --force), renamed."""
    sx = gmm.Sx()
    try:
        before, pb = gmm.backup(sx, slot, "before")
        if len(before) != 88:
            raise SystemExit(f"slot {slot}: read {len(before)} of 88 blocks, not writing")
        if "INIT" not in gmm.scene_name(before).upper() and not force:
            raise SystemExit(f"slot {slot} is '{gmm.scene_name(before)}', not INIT: refusing (--force to overwrite)")
        new = sx.dump(gmm.slot_base(src))
        if len(new) != 88 or set(new) != set(before):
            raise SystemExit(f"scene {src}: read {len(new)} blocks, not writing")
        old = gmm.scene_name(new)
        new["00 00 00"][3:19] = list(name.ljust(16)[:16].encode("ascii"))
        sx.write(gmm.slot_base(slot), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, slot, "after")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {slot}: '{gmm.scene_name(before)}' -> '{gmm.scene_name(after)}' = copy of scene {src} '{old}'; "
              f"88 blocks written, mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
    finally:
        sx.close()


# One part = these blocks (group 02: xP, P = part index; 05 P0 = the part's MFX). The string
# block (02 2P: mutes, levels, pans per string) is left to the target scene.
PART_BLOCKS = ["02 0{p} 00", "02 0{e} 00", "02 1{p} 00", "02 3{p} 00", "02 4{p} 00", "02 5{p} 00",
               "02 6{p} 00", "02 7{p} 00", "05 {p}0 00"]


def cmd_part(src, dst, level=None):
    """Part `src` = (scene, part) -> part `dst` = (scene, part) in memory, switched on. The target
    part's strings and the scene's control functions are not touched. Backups before/after."""
    (s_sc, s_p), (d_sc, d_p) = src, dst
    sx = gmm.Sx()
    try:
        a = sx.dump(gmm.slot_base(s_sc)); before, pb = gmm.backup(sx, d_sc, "before")
        if len(a) != 88 or len(before) != 88:
            raise SystemExit(f"read {len(a)} / {len(before)} of 88 blocks, not writing")
        new = {}
        for k in PART_BLOCKS:
            ks = k.format(p=s_p - 1, e=f"{8 + s_p - 1:X}"); kd = k.format(p=d_p - 1, e=f"{8 + d_p - 1:X}")
            if len(a[ks]) != len(before[kd]):
                raise SystemExit(f"block {ks} -> {kd}: sizes differ")
            new[kd] = list(a[ks])
        ts = new[f"02 0{d_p - 1} 00"]; ts[4], ts[8] = 1, 0
        if level is not None:
            ts[6] = level
        sx.write(gmm.slot_base(d_sc), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, d_sc, "after")
        bad = [k for k in new if after.get(k) != new[k]]
        other = [k for k in before if k not in new and after.get(k) != before[k]]
        print(f"scene {s_sc} '{gmm.scene_name(a)}' part {s_p} -> scene {d_sc} '{gmm.scene_name(after)}' part {d_p}: "
              f"{len(new)} blocks written, part level {after[f'02 0{d_p - 1} 00'][6]}, mismatches {bad or 'none'}, "
              f"other blocks changed {other or 'none'}\n  backups: {pb}\n           {pa}")
    finally:
        sx.close()


def cmd_preview(song, part_file, b0, b1):
    """mp3 of the stem part and of every take of these bars, all at the stem's loudness."""
    import glob
    part = json.load(open(part_file, encoding="utf-8"))
    t0, t1 = song.t_stem(b0), song.t_stem(b1) + 2.5
    ref = sum(song.read(f"{s}.wav", t0, t1) for s in part.get("stems", ["keys", "strings"]))
    L = gmm.lufs(ref)
    out = os.path.join(song.out, "preview-part"); os.makedirs(out, exist_ok=True)

    def mp3(name, x):
        tmp = os.path.join(out, name + ".wav"); gmm.save(tmp, x)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-b:a", "192k",
                        os.path.join(out, name + ".mp3")], check=True)
        os.remove(tmp)
        print("  ", os.path.join(out, name + ".mp3"))

    mp3(f"00-stem-{b0}-{b1}", ref)
    base = os.path.basename(part_file).replace(".notes.json", "")
    takes = sorted(glob.glob(os.path.join(song.out, f"part-{base}-*-{b0}-{b1}.wav")))
    for i, p in enumerate(takes, 1):
        x = gmm.read_wav(p)
        g = 10 ** ((L - gmm.lufs(x)) / 20)
        mp3(f"{i:02d}-" + os.path.basename(p)[len(f"part-{base}-"):-4], x * g)
    return takes


def cqt_db(x, floor=60.0):
    """log-CQT, 3 bins a semitone C1..B7 at 22050 Hz, hop 256; dB above (max - floor), >= 0."""
    import librosa
    from scipy.signal import resample_poly
    y = resample_poly(x, 22050, SR).astype(np.float32)
    C = np.abs(librosa.cqt(y, sr=22050, hop_length=256, fmin=librosa.note_to_hz("C1"), n_bins=36 * 7,
                           bins_per_octave=36))
    D = 20 * np.log10(C + 1e-9)
    return np.maximum(D - (D.max() - floor), 0)


def band_pass(x, band):
    if not band:
        return x
    from scipy.signal import butter, sosfiltfilt
    lo, hi = band
    return sosfiltfilt(butter(4, [lo, min(hi, SR / 2 - 100)], "bandpass", fs=SR, output="sos"), x)


def sweep_score(R, T, semi):
    """Stem CQT R (original key) vs take CQT T (band key): the take is moved by -semi semitones (and
    an octave either way: some ROM tones sound an octave off). Cosine of the mean spectra (timbre and
    voicing) and of the whole time-frequency picture (attacks, length, rhythm). -> (score, spec, tf, oct)"""
    n = min(R.shape[1], T.shape[1]); R, T = R[:, :n], T[:, :n]
    best = None
    for o in (-1, 0, 1):
        k = 3 * (-semi + 12 * o); Ts = np.zeros_like(T)
        if k >= 0:
            Ts[k:] = T[:T.shape[0] - k]
        else:
            Ts[:k] = T[-k:]
        cos = lambda a, b: float(np.dot(a.ravel(), b.ravel()) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        sp, tf = cos(R.mean(1), Ts.mean(1)), cos(R, Ts)
        s = (0.5 * sp + 0.5 * tf, sp, tf, -o)
        if best is None or s[0] > best[0]:
            best = s
    return best


HISTORY = os.path.join(REPO, "gear", "gm-800", "tone-sweeps.json")


def history():
    return json.load(open(HISTORY, encoding="utf-8")) if os.path.exists(HISTORY) else {"tones": {}}


def history_add(song, role, voices, b0, b1, rows):
    """Every sweep leaves its ranking here (one run per song/role/voices/bars, replaced on a rescore):
    the next part of the same role starts from the tones that ranked high before (--from-history)."""
    h = history(); key = (song.name, role, "+".join(voices), [b0, b1])
    for i, (sc, num, nm, cat, sp, tf, o) in enumerate(rows, 1):
        t = h["tones"].setdefault(str(num), {"name": nm, "cat": cat, "runs": []})
        t["runs"] = [r for r in t["runs"] if (r["song"], r["role"], r["voices"], r["bars"]) != key]
        t["runs"].append({"song": song.name, "role": role, "voices": key[2], "bars": key[3],
                          "score": round(sc, 3), "rank": i, "of": len(rows), "oct": o})
    h["tones"] = dict(sorted(h["tones"].items(), key=lambda kv: int(kv[0])))
    with open(HISTORY, "w", encoding="utf-8") as f:
        f.write('{"about": "GM-800 ROM tones ranked by gm800_part.py sweep against song stems (rank 1 = closest); '
                'tools/gm800_part.py --from-history reads it", "tones": {\n')
        f.write(",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in h["tones"].items()))
        f.write("\n}}\n")


def history_top(role, n):
    """The n tones that ranked best in earlier sweeps of this role (mean percentile over the runs)."""
    best = []
    for num, t in history()["tones"].items():
        ps = [1 - (r["rank"] - 1) / max(1, r["of"]) for r in t["runs"] if r["role"] == role]
        if ps:
            best.append((sum(ps) / len(ps), int(num)))
    return [num for _, num in sorted(best, reverse=True)[:n]]


def cmd_sweep(song, part_file, voices, b0, b1, nums, base, tail, band, rescore=False, role=None, transpose=0, vel=None):
    """The voice(s) of bars [b0, b1) on ROM tones (part 1 of the TEMP scene over an INIT scene, nothing
    written), each take scored against the summed stems of the part (sweep_score). Takes are kept:
    --rescore ranks them again without the GM-800 (e.g. with another --band)."""
    import glob
    part = json.load(open(part_file, encoding="utf-8"))
    line = sorted((t, n + transpose, d) for t, n, d in sum((voice_line(song, part, v, b0, b1) for v in voices), []))
    if not line:
        raise SystemExit(f"no notes of {voices} in bars {b0}-{b1}")
    dur = (b1 - b0) * song.bar + tail
    ref = sum(song.read(f"{s}.wav", song.t_stem(b0), song.t_stem(b0) + dur) for s in part["stems"]).mean(1)
    R = cqt_db(band_pass(ref, band))
    base_nm = os.path.basename(part_file).replace(".notes.json", "")
    tag = f"sweep-{base_nm}-{'+'.join(voices)}-{b0}-{b1}" + (f"-tr{transpose:+d}" if transpose else "")
    tab = {int(r[0]): r for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t")}
    path = lambda num: os.path.join(song.out, f"{tag}-t{num:04d}.wav")
    if vel:
        gmm.VEL = vel
    if not rescore:
        with gmm.Rig() as rig:
            nm, _ = rig.load(base)
            if "INIT" not in nm.upper():
                raise SystemExit(f"scene {base} is '{nm}', not INIT")
            ch = rig.part_ch[0]
            for i, num in enumerate(nums, 1):
                r = tab[num]; want = [int(r[2]), int(r[3]), int(r[4]) - 1]
                for attempt in range(4):                     # a PC from elsewhere (Stage Traxx being launched by
                    rig.tone(*want[:2], want[2] + 1)         # another session, 2026-11-20) replaces the TEMP scene
                    x = play(rig, [(t, n, d, ch) for t, n, d in line], tail=tail + 0.3)   # mid-run: every take
                    got = rig.g.rq([0x10, 0x02, 0x00, 0x00], 3)                           # after it came out
                    if got and list(got[:3]) == want and "INIT" in rig.g.name().upper():  # silent. So check
                        break                                                             # the scene is still
                    print(f"      {num}: the scene changed under the take (tone {list(got[:3]) if got else None}, "
                          f"wanted {want}) - scene {base} again, take repeated", flush=True)   # ours, else redo
                    rig.load(base)
                else:
                    raise SystemExit(f"tone {num}: the scene keeps changing - something is sending PCs to the GM-800")
                gmm.save(path(num), x)
                print(f"  {i:3}/{len(nums)} {num:4} {r[1]}", flush=True)
            time.sleep(0.2)
    rows = []
    for p in sorted(glob.glob(os.path.join(song.out, f"{tag}-t*.wav"))):
        num = int(p[-8:-4]); x = gmm.read_wav(p).mean(1)[:int(dur * SR)]
        if np.sqrt((x ** 2).mean()) < 1e-4:
            continue
        sc, sp, tf, o = sweep_score(R, cqt_db(band_pass(x, band)), song.semi)
        rows.append((sc, num, tab[num][1], tab[num][5], sp, tf, o))
    rows.sort(reverse=True)
    print(f"{tag}: {len(rows)} takes, best first (spec = mean spectrum, tf = time x frequency; oct = the tone "
          f"sounds that many octaves off the note sent)")
    for sc, num, nm, cat, sp, tf, o in rows[:30]:
        print(f"  {num:4} {nm:22} {cat:18} score {sc:.3f}  spec {sp:.3f}  tf {tf:.3f}  oct {o:+d}")
    json.dump([{"tone": r[1], "name": r[2], "cat": r[3], "score": r[0], "spec": r[4], "tf": r[5], "oct": r[6]} for r in rows],
              open(os.path.join(song.out, tag + ".json"), "w"), ensure_ascii=False, indent=0)
    role = role or voices[0].split("_")[0]
    history_add(song, role, voices, b0, b1, rows)
    print(f"ranking kept in {os.path.relpath(HISTORY, REPO)} as role '{role}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sweep")
    p.add_argument("song"); p.add_argument("notes"); p.add_argument("voices", help="voice[,voice...]")
    p.add_argument("--bars", type=int, nargs=2, required=True)
    p.add_argument("--cat", default="", help="tone categories, e.g. 35,36 (gear/gm-800/tones.tsv)")
    p.add_argument("--tones", default="", help="tone numbers, e.g. 645,119")
    p.add_argument("--base", type=int, default=33); p.add_argument("--tail", type=float, default=1.0)
    p.add_argument("--band", default="", help="compare inside LO-HI Hz only, e.g. 40-200")
    p.add_argument("--rescore", action="store_true", help="rank the kept takes again, no GM-800")
    p.add_argument("--role", default="", help="what the part is (lead, pad, stab, pluck, bass...): key of the "
                   "history; default = first voice without its _suffix")
    p.add_argument("--vel", type=int, default=0, help="MIDI velocity of the takes (default 100)")
    p.add_argument("--transpose", type=int, default=0, help="send the notes this many semitones off (a tone "
                   "that sounds an octave low: 12); the take is then compared at the written pitch")
    p.add_argument("--from-history", type=int, default=0, metavar="N",
                   help="add the N tones that ranked best for this role in earlier sweeps (gear/gm-800/tone-sweeps.json)")
    p = sub.add_parser("probe"); p.add_argument("scenes", type=int, nargs="+")
    p = sub.add_parser("take")
    p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice"); p.add_argument("scene", type=int)
    p.add_argument("--parts", default=""); p.add_argument("--bars", type=int, nargs=2)
    p.add_argument("--vel", type=int, default=0, help="MIDI velocity (default gm800_match.VEL = 100)")
    p.add_argument("--as-played", action="store_true", help="every part gets the same note (the scene as played "
                   "on the guitar: parts shifted by octaves stay shifted); default = each part at the written pitch")
    p = sub.add_parser("preview")
    p.add_argument("song"); p.add_argument("notes"); p.add_argument("--bars", type=int, nargs=2)
    p = sub.add_parser("record"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("--only", default="")
    p = sub.add_parser("layer"); p.add_argument("song"); p.add_argument("notes")
    p = sub.add_parser("tones"); p.add_argument("song"); p.add_argument("note"); p.add_argument("nums")
    p.add_argument("--base", type=int, default=33)
    p = sub.add_parser("part"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--level", type=int)
    p = sub.add_parser("copy"); p.add_argument("src", type=int); p.add_argument("slot", type=int)
    p.add_argument("name"); p.add_argument("--force", action="store_true")
    p = sub.add_parser("loudness"); p.add_argument("scenes", type=int, nargs="+")
    p.add_argument("--phrase", default="A3 C4 E4 A4"); p.add_argument("--parts", default="")
    p = sub.add_parser("balance")
    p.add_argument("template", type=int); p.add_argument("ref"); p.add_argument("part")
    p.add_argument("--chord", default="E4 A4 C5")
    p = sub.add_parser("scene")
    p.add_argument("slot", type=int); p.add_argument("template", type=int); p.add_argument("name")
    p.add_argument("--parts", required=True); p.add_argument("--octave", type=int, default=0)
    p.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.cmd == "probe":
        return cmd_probe(a.scenes)
    if a.cmd == "part":
        return cmd_part(tuple(int(v) for v in a.src.split(":")), tuple(int(v) for v in a.dst.split(":")), a.level)
    if a.cmd == "copy":
        return cmd_copy(a.src, a.slot, a.name, a.force)
    if a.cmd == "loudness":
        return cmd_loudness(a.scenes, a.phrase, [int(v) for v in a.parts.split(",") if v] or None)
    if a.cmd == "balance":
        rp, rl = a.ref.split(":"); pp, lv = a.part.split(":")
        return cmd_balance(a.template, (int(rp), int(rl)), (int(pp), [int(v) for v in lv.split(",")]), a.chord)
    if a.cmd == "scene":
        parts = {int(k): int(v) for k, v in (x.split(":") for x in a.parts.split(","))}
        return cmd_scene(a.slot, a.template, a.name, parts, a.octave, a.force)
    song = gmm.Song(a.song)
    if a.cmd == "sweep":
        nums = [int(v) for v in a.tones.split(",") if v]
        cats = {c for c in a.cat.split(",") if c}
        nums += [int(r[0]) for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t")
                 if r[5].split(":")[0] in cats]
        role = a.role or a.voices.split(",")[0].split("_")[0]
        if a.from_history:
            nums += [n for n in history_top(role, a.from_history) if n not in nums]
        if not nums and not a.rescore:
            raise SystemExit("no tones: --cat, --tones or --from-history (an empty history for this role?)")
        band = tuple(float(v) for v in a.band.split("-")) if a.band else None
        return cmd_sweep(song, a.notes, a.voices.split(","), a.bars[0], a.bars[1], nums, a.base, a.tail, band,
                         a.rescore, role, a.transpose, a.vel or None)
    if a.cmd == "tones":
        return cmd_tones(song, a.note, [int(v) for v in a.nums.split(",")], a.base)
    if a.cmd == "record":
        return cmd_record(song, a.notes, [int(v) for v in a.only.split(",") if v] or None)
    if a.cmd == "layer":
        return cmd_layer(song, a.notes)
    part = json.load(open(a.notes, encoding="utf-8"))
    b0, b1 = a.bars or part.get("bars")
    if a.cmd == "take":
        cmd_take(song, a.notes, a.voice, a.scene, [int(v) for v in a.parts.split(",") if v], b0, b1, a.as_played,
                 a.vel or None)
    else:
        cmd_preview(song, a.notes, b0, b1)


if __name__ == "__main__":
    sys.exit(main())
