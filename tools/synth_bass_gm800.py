#!/usr/bin/env python3
"""A line of tools/synth_bass_audition.py played by the GM-800 on a scene and recorded over USB.

    uv run -q --python 3.12 --with sounddevice --with numpy --with scipy --with python-rtmidi \
        --with soundfile --with pyloudnorm python tools/synth_bass_gm800.py B2 25 [--parts 1,2] [--vel 100]

The song is click: follow, so gm800_part.py (constant bar length) does not apply: the notes carry their own
times (notes.json "slot_sec", sixteenths on the click grid). Same time lock as `gm800_part.py record`: a short
note on a sharp scene first, its onset gives the latency of this recording. Every part of the scene gets the
same note, the lowest part at the written pitch (the scene as it sounds from the guitar, moved to the bass
register). Writes analysis/teen-spirit-synth-bass/gm800-<line>-s<scene>.wav, sample 0 = the first bar line;
the audition script picks it up. NOTE SOURCE goes to USB for the run and is put back; scene 1 MUTE after.
"""
import argparse, importlib.util, json, os, time
import numpy as np
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("gmp", os.path.join(REPO, "tools", "gm800_part.py"))
gmp = importlib.util.module_from_spec(_s); _s.loader.exec_module(gmp)
gmm = gmp.gmm; SR = gmm.SR
OUT = os.path.join(REPO, "analysis", "teen-spirit-synth-bass")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("line"); ap.add_argument("scene", type=int)
    ap.add_argument("--parts", default=""); ap.add_argument("--vel", type=int, default=gmm.VEL)
    ap.add_argument("--gap", type=float, default=0.03, help="s of silence before the next note")
    a = ap.parse_args(); parts = [int(x) for x in a.parts.split(",") if x]
    d = json.load(open(f"{OUT}/notes.json")); b0 = d["bars"][0]; ss = d["slot_sec"]
    line = []
    for bar, k, ln, p in d["lines"][a.line]:
        i = (bar - b0) * 16 + k; j = min(i + ln, len(ss) - 1)
        line.append((ss[i], p, max(0.05, ss[j] - ss[i] - a.gap)))
    tones = gmp.tone_names()
    with gmm.Rig() as rig:
        nm, _ = rig.load(a.scene)
        sp = [x for x in gmp.scene_parts(rig, tones) if (x[0] in parts if parts else x[2])]
        shifts = {}
        for pn, ch, on, num, name, level in sp:
            sh = gmp.probe_shift(rig, ch)
            print(f"scene {a.scene} '{nm}' part {pn}: tone {num} {name}, level {level}, octave "
                  f"{'silent' if sh is None else f'{sh // 12:+d}'}", flush=True)
            if sh is not None:
                shifts[ch] = sh
        if not shifts:
            raise SystemExit("no sounding part")
        ref = min(shifts.values()); time.sleep(1.5)
        rig.load(gmp.SYNC_SCENE); AT, T0 = gmp.SYNC_AT, gmp.SYNC_T0
        msgs = [(AT, [0x90 | ch, 45, 110]) for ch in rig.part_ch[:4]]
        msgs += [(AT + 0.08, [0x80 | ch, 45, 0]) for ch in rig.part_ch[:4]]
        msgs += [(AT + 0.5, [0xC0 | (rig.scene_ch - 1), a.scene - 1])]
        for t, n, dur in line:
            for ch in shifts:
                msgs += [(T0 + t, [0x90 | ch, n - ref, a.vel]), (T0 + t + dur, [0x80 | ch, n - ref, 0])]
        total = T0 + ss[-1] + 2.0
        rec = rig.sd.rec(int((total + 0.4) * SR), SR, channels=2, device=rig.dev)
        t0 = time.perf_counter() + 0.4
        for t, m in sorted(msgs, key=lambda e: (e[0], e[1][0] & 0xF0 == 0x90)):
            while time.perf_counter() < t0 + t:
                time.sleep(0.0005)
            rig.g.out.send_message(m)
        rig.sd.wait(); x = rec[int(0.4 * SR):]
    env = np.abs(x[:int((AT + 0.45) * SR)]).max(1); pk = env.max()
    if pk < 1e-3:
        raise SystemExit("no sync note in the recording")
    lat = int(np.argmax(env > 0.2 * pk)) / SR - AT
    if not -0.01 < lat < 0.2:
        raise SystemExit(f"latency {lat * 1000:.0f} ms - not plausible")
    y = x[int(round((T0 + lat) * SR)):]
    out = f"{OUT}/gm800-{a.line}-s{a.scene:03d}" + (f"-p{''.join(map(str, parts))}" if parts else "") + ".wav"
    gmm.save(out, y)
    print(f"{len(line)} notes x {len(shifts)} parts, latency {lat * 1000:.1f} ms, LUFS {gmm.lufs(y):.1f}, "
          f"peak {20 * np.log10(np.abs(y).max() + 1e-9):.1f} dBFS -> {out}")


if __name__ == "__main__":
    main()
