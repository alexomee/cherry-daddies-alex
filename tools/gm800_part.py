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
    gmp scene 32 51 "NE ISHI PAD" --parts 3:127,1:24 --octave 1     # new scene in an INIT slot

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
    "layer": {"file": "pb-keys-verse", "takes": [
        {"voice": "low", "scene": 57, "parts": [3], "bars": [9, 25], "gain_db": -6.0}, ...]}
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
    for at in v["at"]:
        for bar, bt, ln, pitches in v["notes"]:
            pos = at + bar - 1 + (bt - 1) / 4
            if b0 <= pos < b1:
                for s in pitches.split():
                    line.append(((pos - b0) * song.bar, midi_of(s), ln * beat - 0.03))
    return sorted(line)


def take_path(song, part_file, voice, scene, parts, b0, b1):
    base = os.path.basename(part_file).replace(".notes.json", "").replace(".json", "")
    tag = "all" if not parts else "p" + "".join(map(str, parts))
    return os.path.join(song.out, f"part-{base}-{voice}-s{scene:03d}-{tag}-{b0}-{b1}.wav")


def cmd_take(song, part_file, voice, scene, parts, b0, b1):
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
        time.sleep(1.5)                                     # let the probe tails die
        ev = [(t, n - sh, d, ch) for t, n, d in line for ch, sh in shifts.items()]
        x = play(rig, ev)
    out = take_path(song, part_file, voice, scene, parts, b0, b1)
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
    tag = "all" if not tk.get("parts") else "p" + "".join(map(str, tk["parts"]))
    return os.path.join(song.out, f"rec-{base}-{tk['voice']}-s{tk['scene']:03d}-{tag}-{tk['bars'][0]}-{tk['bars'][1]}.wav")


def cmd_record(song, part_file, only=None, tail=4.0):
    part = json.load(open(part_file, encoding="utf-8")); tones = tone_names()
    with gmm.Rig() as rig:
        for i, tk in enumerate(part["layer"]["takes"]):
            if only is not None and i not in only:
                continue
            b0, b1 = tk["bars"]; line = voice_line(song, part, tk["voice"], b0, b1)
            nm, _ = rig.load(tk["scene"])
            sp = [x for x in scene_parts(rig, tones) if (x[0] in tk["parts"] if tk.get("parts") else x[2])]
            shifts = {}
            for pnum, ch, on, num, name, level in sp:
                sh = probe_shift(rig, ch)
                if sh is not None:
                    shifts[ch] = sh
            if not shifts or not line:
                raise SystemExit(f"take {i}: nothing to play")
            rig.load(SYNC_SCENE)
            msgs = [(SYNC_AT, [0x90 | ch, 45, 110]) for ch in rig.part_ch[:4]]
            msgs += [(SYNC_AT + 0.08, [0x80 | ch, 45, 0]) for ch in rig.part_ch[:4]]
            msgs += [(SYNC_AT + 0.5, [0xC0 | (rig.scene_ch - 1), tk["scene"] - 1])]
            for t, n, d in line:
                for ch, sh in shifts.items():
                    msgs += [(SYNC_T0 + t, [0x90 | ch, n - sh, gmm.VEL]), (SYNC_T0 + t + d, [0x80 | ch, n - sh, 0])]
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
            print(f"take {i}: {tk['voice']} bars {b0}-{b1} on scene {tk['scene']} '{nm}' parts "
                  f"{[q[0] for q in sp]}: latency {lat * 1000:.1f} ms, LUFS {gmm.lufs(y):.1f}, peak "
                  f"{20 * np.log10(np.abs(y).max() + 1e-9):.1f} -> {os.path.basename(out)}", flush=True)


def cmd_layer(song, part_file):
    import soundfile as sf
    from scipy.signal import resample_poly
    part = json.load(open(part_file, encoding="utf-8")); lay = part["layer"]
    info = sf.info(os.path.join(song.dir, part.get("stems", ["keys"])[0] + ".wav")); sr = info.samplerate
    out = np.zeros((info.frames, 2), dtype=np.float64)
    for tk in lay["takes"]:
        x = gmm.read_wav(rec_path(song, part_file, tk)).astype(np.float64) * 10 ** (tk.get("gain_db", 0) / 20)
        n = int(0.3 * SR); x[-n:] *= np.linspace(1, 0, n)[:, None]; x[:48] *= np.linspace(0, 1, 48)[:, None]
        if sr != SR:
            x = resample_poly(x, sr, SR, axis=0)
        a = int(round(song.t_stem(tk["bars"][0]) * sr)); m = min(len(x), len(out) - a)
        out[a:a + m] += x[:m]
    dst = os.path.join(song.dir, "parts", lay["file"] + ".wav")
    sf.write(dst, out.astype(np.float32), sr, subtype="FLOAT")
    print(f"{len(lay['takes'])} takes -> {dst}  peak {20 * np.log10(np.abs(out).max() + 1e-9):.1f} dBFS")


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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe"); p.add_argument("scenes", type=int, nargs="+")
    p = sub.add_parser("take")
    p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice"); p.add_argument("scene", type=int)
    p.add_argument("--parts", default=""); p.add_argument("--bars", type=int, nargs=2)
    p = sub.add_parser("preview")
    p.add_argument("song"); p.add_argument("notes"); p.add_argument("--bars", type=int, nargs=2)
    p = sub.add_parser("record"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("--only", default="")
    p = sub.add_parser("layer"); p.add_argument("song"); p.add_argument("notes")
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
    if a.cmd == "balance":
        rp, rl = a.ref.split(":"); pp, lv = a.part.split(":")
        return cmd_balance(a.template, (int(rp), int(rl)), (int(pp), [int(v) for v in lv.split(",")]), a.chord)
    if a.cmd == "scene":
        parts = {int(k): int(v) for k, v in (x.split(":") for x in a.parts.split(","))}
        return cmd_scene(a.slot, a.template, a.name, parts, a.octave, a.force)
    song = gmm.Song(a.song)
    if a.cmd == "record":
        return cmd_record(song, a.notes, [int(v) for v in a.only.split(",") if v] or None)
    if a.cmd == "layer":
        return cmd_layer(song, a.notes)
    part = json.load(open(a.notes, encoding="utf-8"))
    b0, b1 = a.bars or part.get("bars")
    if a.cmd == "take":
        cmd_take(song, a.notes, a.voice, a.scene, [int(v) for v in a.parts.split(",") if v], b0, b1)
    else:
        cmd_preview(song, a.notes, b0, b1)


if __name__ == "__main__":
    sys.exit(main())
