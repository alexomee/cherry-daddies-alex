#!/usr/bin/env python3
"""Measure the output level of the live rig's sounds without playing them by hand
(wiki/pipelines/level-anchors.md, "живая сторона").

    uv run --python 3.12 --with sounddevice --with numpy --with python-rtmidi \\
        tools/live_levels.py gm800 [scene ...]

gm800: for every GM-800 scene used in mix.json (key "gm800"; scene 1 = MUTE is skipped) or the
scenes given: select it by Program Change (Scene Rx channel), play one fixed MIDI phrase on the
part channels over USB, record the GM-800's own USB audio (channels 1/2) and measure it.
The GM-800 plays MIDI notes only when MENU > MIDI > NOTE SOURCE = USB, so the script switches
that system setting by SysEx for the run and ALWAYS puts the previous value back (GK IN on stage).
While it runs the guitar does not trigger the synth, and the phrase is audible on the outputs.

Output: analysis/level-audit/live/gm800/scene-NN.wav + gm800.json, table on stdout.
Levels: I = integrated LUFS of the mono fold + 3.01 (same metric as tools/level_audit.py);
seg = plain RMS dBFS of the fold while the notes of that segment are held.
"""
import glob, json, os, re, subprocess, sys, time, wave
import numpy as np, sounddevice as sd, rtmidi

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "analysis", "level-audit", "live")
SR = 48000
HDR = [0xF0, 0x41, 0x10, 0x00, 0x00, 0x00, 0x00, 0x26]      # Roland, dev 10, model GM-800
SYS_MIDI = [0x00, 0x00, 0x06, 0x00]                          # SystemMidi block; +08 = NOTE SOURCE
NOTE_SRC_USB = 2
VEL = 100
# (label, notes, hold seconds): guitar range, low strings -> high strings -> a chord
PHRASE = [("low", [40], 0.8), ("low", [45], 0.8), ("mid", [50], 0.8), ("mid", [55], 0.8),
          ("high", [59], 0.8), ("high", [64], 0.8), ("chord", [40, 47, 52], 1.4)]
GAP, TAIL = 0.25, 1.0


def csum(body):
    return (128 - sum(body) % 128) % 128


class GM800:
    def __init__(self):
        self.out, self.inp = rtmidi.MidiOut(), rtmidi.MidiIn()
        self.out.open_port(self.out.get_ports().index("GM-800"))
        self.inp.open_port(self.inp.get_ports().index("GM-800"))
        self.inp.ignore_types(sysex=False, timing=True, active_sense=True)

    def rq(self, addr, size, wait=0.5):
        while self.inp.get_message():
            pass
        body = list(addr) + [0, 0, (size >> 7) & 0x7F, size & 0x7F]
        self.out.send_message(HDR + [0x11] + body + [csum(body), 0xF7])
        t0 = time.time()
        while time.time() - t0 < wait:
            m = self.inp.get_message()
            if m and m[0][0] == 0xF0 and m[0][8] == 0x12 and m[0][9:13] == list(addr):
                return m[0][13:-2]
            time.sleep(0.005)
        return None

    def dt(self, addr, data):
        body = list(addr) + list(data)
        self.out.send_message(HDR + [0x12] + body + [csum(body), 0xF7])
        time.sleep(0.05)

    def scene(self, n, ch):
        self.out.send_message([0xC0 | (ch - 1), n - 1])
        time.sleep(0.8)

    def name(self):
        d = self.rq([0x10, 0, 0, 0], 16)
        return bytes(b for b in (d or []) if b >= 32).decode("ascii", "replace").strip()


def audio_in(name):
    for i, d in enumerate(sd.query_devices()):
        if d["name"].startswith(name) and d["max_input_channels"] > 0:
            return i
    raise SystemExit(f"audio device {name} not found")


def used_scenes():
    sc = set()
    for p in glob.glob(os.path.join(REPO, "music", "songs", "*", "mix.json")):
        g = json.load(open(p)).get("gm800")
        sc |= {g} if isinstance(g, int) else {x["scene"] for x in g or []}
    return sorted(sc - {1})


def lufs_fold(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-af",
                          "pan=mono|c0=0.5*c0+0.5*c1,ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"I:\s*(-?\d+\.\d+) LUFS", err[err.rfind("Summary:"):])
    return round(float(m.group(1)) + 3.01, 1) if m else None


def db(x):
    return round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1)


def gm800(scenes):
    g = GM800()
    sysb = g.rq(SYS_MIDI, 0x10)
    if not sysb:
        raise SystemExit("GM-800 does not answer SysEx (is BOSS Tone Studio holding the port?)")
    scene_ch, part_ch, src0 = sysb[0] + 1, [b for b in sysb[1:5]], sysb[8]
    dev = audio_in("GM-800")
    outdir = os.path.join(OUT, "gm800"); os.makedirs(outdir, exist_ok=True)
    total = sum(h + GAP for _, _, h in PHRASE) + TAIL + 0.3
    res = {}
    try:
        g.dt(SYS_MIDI[:3] + [0x08], [NOTE_SRC_USB])
        for sc in scenes:
            g.scene(sc, scene_ch)
            nm = g.name()
            rec = sd.rec(int(total * SR), SR, channels=2, device=dev)
            t0 = time.time(); time.sleep(0.3); marks = []
            for label, notes, hold in PHRASE:
                a = time.time() - t0
                for ch in part_ch:
                    for n in notes:
                        g.out.send_message([0x90 | ch, n, VEL])
                time.sleep(hold)
                for ch in part_ch:
                    for n in notes:
                        g.out.send_message([0x80 | ch, n, 0])
                marks.append((label, a, time.time() - t0)); time.sleep(GAP)
            sd.wait()
            fold = rec.mean(1)
            seg = {}
            for label in ("low", "mid", "high", "chord"):
                parts = [fold[int(a * SR):int(b * SR)] for l, a, b in marks if l == label]
                seg[label] = db(np.concatenate(parts))
            path = os.path.join(outdir, f"scene-{sc:02d}.wav")
            with wave.open(path, "wb") as w:
                w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
                w.writeframes((np.clip(rec, -1, 1) * 32767).astype("<i2").tobytes())
            stereo = db(np.sqrt((rec ** 2).mean(1)))
            res[sc] = {"name": nm, "I": lufs_fold(path), "seg": seg, "peak": round(float(
                20 * np.log10(np.abs(rec).max() + 1e-12)), 1), "fold_loss": round(stereo - db(fold), 1)}
            r = res[sc]
            print(f"scene {sc:2} {nm:16} I {r['I']}  low {seg['low']:6} mid {seg['mid']:6} "
                  f"high {seg['high']:6} chord {seg['chord']:6}  peak {r['peak']:6} fold {r['fold_loss']}",
                  flush=True)
    finally:
        g.dt(SYS_MIDI[:3] + [0x08], [src0])
        back = g.rq(SYS_MIDI, 0x10)
        g.scene(1, scene_ch)                                 # leave the synth on MUTE
        print(f"NOTE SOURCE restored to {back[8] if back else '?'} (was {src0}); scene 1 (MUTE) loaded")
    json.dump({"date": time.strftime("%Y-%m-%d %H:%M"), "vel": VEL, "phrase": PHRASE, "scenes": res},
              open(os.path.join(OUT, "gm800.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "gm800":
        raise SystemExit(__doc__)
    gm800([int(a) for a in sys.argv[2:]] or used_scenes())
