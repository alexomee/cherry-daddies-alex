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

podgo [preset ...] [--reuse-di]: record one dry guitar take from USB in 3/4 (voice prompt),
then for every POD Go preset used in mix.json (key "podgo"): select it by Program Change, ask by
voice to set its Input block to "USB 3/4" (per preset, by hand, not saved), wait until a probe
comes back processed, re-amp the take and record USB in 1/2.

Output: analysis/level-audit/live/{gm800,podgo}/*.wav + gm800.json / podgo.json, table on stdout.
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
EXTRA_CC = {}                     # scene -> [(cc, value)] sent on the Scene Rx channel after loading it


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


def string_of(note):
    """0-based string a note sits on in standard tuning (0 = high E ... 5 = low E)."""
    return 0 if note >= 64 else 1 if note >= 59 else 2 if note >= 55 else 3 if note >= 50 else 4 if note >= 45 else 5


def part_routes(g, part_ch):
    """string -> MIDI channels of the parts that string plays. MIDI notes ignore a part's
    STRING MUTE (it belongs to the GK input), so a scene that splits one tone over parts by
    string (e.g. part 3 = 6th string, part 4 = 5th) would sound doubled if every part got
    every note. Read the loaded scene's string mutes and route each note like the pickup would."""
    routes, desc = {st: [] for st in range(6)}, {}
    for p, ch in enumerate(part_ch):
        ts, sc = g.rq([0x10, 0x02, p, 0], 12), g.rq([0x10, 0x02, 0x20 + p, 0], 14)
        if not ts or not sc:
            for st in routes:                                # no answer: old behaviour
                routes[st].append(ch)
            continue
        for st in range(6):
            if not sc[st]:
                routes[st].append(ch)
        desc[p + 1] = {"sw": ts[4], "level": ts[6], "strings": "".join(str(st + 1) for st in range(6) if not sc[st]),
                       "string_levels": list(sc[7:13])}
    return routes, desc


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
            for cc, val in EXTRA_CC.get(sc, []):             # e.g. an ASSIGN that swaps parts
                g.out.send_message([0xB0 | (scene_ch - 1), cc, val])
            time.sleep(0.2 if EXTRA_CC.get(sc) else 0)
            nm = g.name()
            routes, pinfo = part_routes(g, part_ch)
            rec = sd.rec(int(total * SR), SR, channels=2, device=dev)
            t0 = time.time(); time.sleep(0.3); marks = []
            for label, notes, hold in PHRASE:
                a = time.time() - t0
                for n in notes:
                    for ch in routes[string_of(n)]:
                        g.out.send_message([0x90 | ch, n, VEL])
                time.sleep(hold)
                for n in notes:
                    for ch in routes[string_of(n)]:
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
            res[sc] = {"name": nm, "parts": pinfo, "I": lufs_fold(path), "seg": seg, "peak": round(float(
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
    jp = os.path.join(OUT, "gm800.json")                    # a partial run keeps the other scenes
    old = json.load(open(jp))["scenes"] if os.path.exists(jp) else {}
    old.update({str(k): v for k, v in res.items()})
    text = json.dumps({"date": time.strftime("%Y-%m-%d %H:%M"), "vel": VEL, "phrase": PHRASE,
                       "scenes": dict(sorted(old.items(), key=lambda kv: int(kv[0])))},
                      ensure_ascii=False, indent=1)          # serialise first: a failure must not
    open(jp, "w").write(text)                                # truncate the previous results
    return res


# ---- POD Go: re-amp one dry take through every preset ------------------------------------------
PODGO_CH = 3                      # POD Go MIDI base channel (tools/stagetraxx_sync.py PODGO_CHANNEL)
DI_SEC, PROBE_SEC, WAIT_SEC = 15.0, 1.5, 150


def say(text):
    subprocess.run(["say", "-v", "Milena", text])      # default output (the FLOW 8 at home)


def used_presets():
    pr = set()
    for p in glob.glob(os.path.join(REPO, "music", "songs", "*", "mix.json")):
        g = json.load(open(p)).get("podgo")
        pr |= {g} if isinstance(g, str) else {x["preset"] for x in g or []}
    return sorted(pr)


def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def podgo(presets):
    """Dry guitar comes to the Mac on USB in 3/4, processed sound on 1/2; a signal sent to USB
    out 3/4 is processed only while the preset's Input block = USB 3/4 (set by hand, per preset,
    not saved). So: record one dry take, then for each preset wait until the probe comes back."""
    dev = audio_in("POD Go")
    mo = rtmidi.MidiOut(); mo.open_port(mo.get_ports().index("POD Go"))
    outdir = os.path.join(OUT, "podgo"); os.makedirs(outdir, exist_ok=True)
    di_path = os.path.join(outdir, "di.wav")
    if "--reuse-di" in sys.argv and os.path.exists(di_path):
        with wave.open(di_path) as w:
            di = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32767
    else:
        say("Вход на гитаре. Играй пятнадцать секунд. Начинай.")
        rec = sd.rec(int(DI_SEC * SR), SR, channels=4, device=dev, blocking=True)
        say("Стоп.")
        di = rec[:, 2].copy()
        print(f"DI take: USB in 3 {db(rec[:, 2])} dB, in 4 {db(rec[:, 3])} dB, peak "
              f"{round(float(20 * np.log10(np.abs(di).max() + 1e-12)), 1)} dBFS; processed 1/2 {db(rec[:, :2])} dB", flush=True)
        if db(di) < -70:
            say("Сухой сигнал не пришёл. Останавливаюсь.")
            raise SystemExit("no dry signal on USB in 3/4 - nothing recorded, stopping")
        write_wav(di_path, di[:, None])
    env = np.convolve(di ** 2, np.ones(int(PROBE_SEC * SR)), "valid")
    p0 = int(env.argmax()); probe = di[p0:p0 + int(PROBE_SEC * SR)]   # loudest stretch of the take

    def reamp(x):
        play = np.zeros((len(x) + int(0.5 * SR), 4), np.float32)
        play[:len(x), 2] = play[:len(x), 3] = x
        return sd.playrec(play, SR, channels=4, device=(dev, dev), blocking=True)[:, :2]

    res = {"di": {"I": lufs_fold(di_path)}}
    spoken = {"A": "А", "B": "Бэ", "C": "Цэ", "D": "Дэ"}
    for pr in presets:
        pc = (int(pr[:2]) - 1) * 4 + "ABCD".index(pr[2])
        mo.send_message([0xC0 | (PODGO_CH - 1), pc]); time.sleep(1.2)
        say(f"Пресет {int(pr[:2])} {spoken[pr[2]]}. Переключи вход на ю эс би три четыре.")
        t0, hits = time.time(), 0
        while time.time() - t0 < WAIT_SEC and hits < 2:
            lvl = db(reamp(probe))
            hits = hits + 1 if lvl > -55 else 0
        if hits < 2:
            print(f"preset {pr}: no signal back in {WAIT_SEC}s - skipped", flush=True)
            say("Не дождался. Пропускаю."); res[pr] = None; continue
        out = reamp(di)
        path = os.path.join(outdir, f"preset-{pr}.wav"); write_wav(path, out)
        fold = out.mean(1)
        res[pr] = {"I": lufs_fold(path), "rms": db(fold), "peak": round(float(20 * np.log10(np.abs(out).max() + 1e-12)), 1),
                   "fold_loss": round(db(np.sqrt((out ** 2).mean(1))) - db(fold), 1)}
        res[pr]["gain_vs_di"] = round(res[pr]["I"] - res["di"]["I"], 1) if res[pr]["I"] and res["di"]["I"] else None
        print(f"preset {pr}: I {res[pr]['I']}  rms {res[pr]['rms']}  peak {res[pr]['peak']}  "
              f"vs DI {res[pr]['gain_vs_di']}  fold {res[pr]['fold_loss']}", flush=True)
        say("Записал.")
    say("Готово. Все пресеты записаны.")
    jp = os.path.join(OUT, "podgo.json")
    old = json.load(open(jp))["presets"] if os.path.exists(jp) else {}
    old.update(res)
    json.dump({"date": time.strftime("%Y-%m-%d %H:%M"), "presets": old}, open(jp, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    if len(sys.argv) >= 2 and sys.argv[1] == "gm800":
        gm800([int(a) for a in args] or used_scenes())
    elif len(sys.argv) >= 2 and sys.argv[1] == "podgo":
        podgo(args or used_presets())
    else:
        raise SystemExit(__doc__)
