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

NOTES.json (lives in the song's parts/ folder, bars = mix.json bars):
    {"stems": ["keys", "strings"],
     "voices": {"low": {"at": [9, 13, 17, 21], "bars": 4,
                        "notes": [[1, 1, 4, "A1 A3"], [2, 1, 4, "A1 A3"], ...]}}}
    note = [bar inside the pattern, beat, length in beats, pitches]; "at" = bars where the pattern starts.

Notes go straight to the part's own MIDI channel at sounding pitch (the part's octave shift,
measured by a probe note, is taken out), not through the guitar strings: the playback does not
have to be playable. NOTE SOURCE goes to USB for the run and is always put back; scene 1 (MUTE)
is loaded at the end. Nothing is written to the GM-800's memory.
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
    a = ap.parse_args()
    if a.cmd == "probe":
        return cmd_probe(a.scenes)
    song = gmm.Song(a.song)
    part = json.load(open(a.notes, encoding="utf-8"))
    b0, b1 = a.bars or part.get("bars")
    if a.cmd == "take":
        cmd_take(song, a.notes, a.voice, a.scene, [int(v) for v in a.parts.split(",") if v], b0, b1)
    else:
        cmd_preview(song, a.notes, b0, b1)


if __name__ == "__main__":
    sys.exit(main())
