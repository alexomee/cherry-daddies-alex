#!/usr/bin/env python3
"""Render a written-out part through the ZENOLOGY plugin instead of the GM-800 (wiki/todo.md, Alex 2026-11-20:
«чтобы GM-800 не отнимать»). ZEN-Core is the engine of both; whether a tone sounds the same is measured, not
assumed (`compare`).

    zr() { uv run -q --python 3.12 --with pedalboard --with mido --with numpy --with soundfile --with scipy \
           --with librosa --with pyobjc-framework-Cocoa tools/zenology_render.py "$@"; }
    zr pick 330                      # opens the plugin window: choose the tone there, close the window ->
                                     #   gear/zenology/states/t0330.bin (the whole plugin state)
    zr render 330 "<song>" NOTES.json riff 105 109 out.wav [--vel 100]   # a voice of notes.json, bars [b0, b1)
    zr compare 330 "<song>" NOTES.json riff 105 109                      # against the GM-800 sweep take of the
                                     #   same tone and bars: spectrum, time x frequency, level; A/B wav pair

The plugin does not follow the GM-800's bank / program numbers when it runs without a window (measured
2026-11-20), so a tone is chosen ONCE by hand in the window and kept as a state file. Sample 0 of a render is the
bar line of b0, as in a GM-800 take; there is no USB latency to take out.
"""
import argparse, importlib.util, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = "/Library/Audio/Plug-Ins/VST3/Roland/ZENOLOGY.vst3"
STATES = os.path.join(REPO, "gear", "zenology", "states")
SR = 48000                                   # same as the GM-800 takes


def state_path(tag):
    return os.path.join(STATES, f"t{int(tag):04d}.bin" if str(tag).isdigit() else f"{tag}.bin")


def plugin(tag=None):
    from pedalboard import load_plugin
    p = load_plugin(PLUGIN)
    if tag is not None:
        p.raw_state = open(state_path(tag), "rb").read()
    return p


def cmd_pick(tag):
    p = plugin(); os.makedirs(STATES, exist_ok=True)
    keep_on_top()
    print(f"ZENOLOGY window is open: choose the tone for '{tag}', then CLOSE the window.", flush=True)
    p.show_editor()                          # blocks until the window is closed
    open(state_path(tag), "wb").write(p.raw_state)
    print("saved", state_path(tag), len(p.raw_state), "bytes")


def keep_on_top():
    """The editor of a plugin hosted by a bare python process has no Dock icon and cannot be brought to the front:
    once another window is clicked it is lost behind it (2026-11-20). So: a regular app (Dock icon, Cmd-Tab) and
    every window of it floating above the others, set by a timer that runs inside the editor's own run loop."""
    from AppKit import NSApplication, NSTimer, NSRunLoop, NSRunLoopCommonModes
    app = NSApplication.sharedApplication(); app.setActivationPolicy_(0)
    state = {"n": 0}
    def tick(_):
        for w in app.windows():
            if w.level() != 3:
                w.setLevel_(3); w.setHidesOnDeactivate_(False)
        if state["n"] < 3:
            app.activateIgnoringOtherApps_(True)
        state["n"] += 1
    t = NSTimer.timerWithTimeInterval_repeats_block_(0.5, True, tick)
    NSRunLoop.mainRunLoop().addTimer_forMode_(t, NSRunLoopCommonModes)


def gp_song(song):
    s = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
    gp = importlib.util.module_from_spec(s); s.loader.exec_module(gp)
    return gp, gp.gmm.Song(song)


def render(tag, song, notes, voice, b0, b1, vel=100, tail=1.0):
    from mido import Message
    gp, sg = gp_song(song); part = json.load(open(notes, encoding="utf-8")); p = plugin(tag)
    p([], duration=0.5, sample_rate=SR)                          # let the state settle
    ev = []
    for t, n, d in gp.voice_line(sg, part, voice, b0, b1):
        ev += [Message("note_on", note=n, velocity=vel, time=t), Message("note_off", note=n, time=t + d)]
    ev.sort(key=lambda m: (m.time, m.type == "note_on"))
    x = p(ev, duration=(b1 - b0) * sg.bar + tail, sample_rate=SR, reset=False)
    return x.T.astype(np.float32), gp, sg


def cmd_render(a):
    import soundfile as sf
    x, _, _ = render(a.tag, a.song, a.notes, a.voice, a.b0, a.b1, a.vel)
    sf.write(a.out, x, SR, subtype="FLOAT"); print(a.out, f"{len(x) / SR:.1f} s, peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS")


def cmd_compare(a):
    import soundfile as sf, librosa
    x, gp, sg = render(a.tag, a.song, a.notes, a.voice, a.b0, a.b1, a.vel)
    base = os.path.basename(a.notes).replace(".notes.json", "")
    ref = os.path.join(sg.out, f"sweep-{base}-{a.voice}-{a.b0}-{a.b1}-t{int(a.gm or a.tag):04d}.wav")
    y = sf.read(ref, always_2d=True)[0].astype(np.float32); n = int((a.b1 - a.b0) * sg.bar * SR)
    xm, ym = x[:n].mean(1), y[:n].mean(1); rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-12
    F = lambda v: np.abs(librosa.cqt(librosa.resample(v, orig_sr=SR, target_sr=22050), sr=22050, hop_length=256,
                                     fmin=librosa.note_to_hz("C2"), n_bins=96))
    A, B = F(xm / rms(xm)), F(ym / rms(ym)); cos = lambda u, v: float((u * v).sum() / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12))
    best = max((cos(np.log1p(30 * A[:, max(0, l):A.shape[1] + min(0, l)]), np.log1p(30 * B[:, max(0, -l):B.shape[1] + min(0, -l)])), l) for l in range(-8, 9))
    sa, sb = 20 * np.log10(A.mean(1) + 1e-9), 20 * np.log10(B.mean(1) + 1e-9)
    print(f"ZENOLOGY '{a.tag}' against the GM-800 take {os.path.basename(ref)}")
    print(f"  mean spectrum, cosine      {cos(A.mean(1), B.mean(1)):.3f}   (1 = the same tone)")
    print(f"  time x frequency, cosine   {best[0]:.3f}   at lag {best[1] * 256 / 22050 * 1000:+.0f} ms (the GM-800 take carries its USB latency)")
    print(f"  level                      ZENOLOGY {20 * np.log10(rms(xm)):.1f} dB, GM-800 {20 * np.log10(rms(ym)):.1f} dB")
    print(f"  spectrum difference by octave (ZENOLOGY - GM-800, dB, both at the same RMS): "
          + "  ".join(f"C{2 + k}: {np.mean(sa[12 * k:12 * k + 12]) - np.mean(sb[12 * k:12 * k + 12]):+.1f}" for k in range(8)))
    out = os.path.join(sg.out, "zenology"); os.makedirs(out, exist_ok=True)
    for nm, v in (("zenology", x[:n]), ("gm800", y[:n])):
        v = v / rms(v.mean(1)) * 0.05; k = int(0.008 * SR); v[:k] *= np.linspace(0, 1, k)[:, None]; v[-k:] *= np.linspace(1, 0, k)[:, None]
        sf.write(os.path.join(out, f"{a.voice}-{a.tag}-{nm}.wav"), v, SR, subtype="PCM_16")
    print("  A/B, same loudness:", out)


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick"); p.add_argument("tag")
    for nm in ("render", "compare"):
        p = sub.add_parser(nm); p.add_argument("tag"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice")
        p.add_argument("b0", type=int); p.add_argument("b1", type=int)
        if nm == "render":
            p.add_argument("out")
        else:
            p.add_argument("--gm", default="", help="GM-800 tone number of the sweep take to compare with (default: the tag)")
        p.add_argument("--vel", type=int, default=100)
    a = ap.parse_args()
    return cmd_pick(a.tag) if a.cmd == "pick" else cmd_render(a) if a.cmd == "render" else cmd_compare(a)


if __name__ == "__main__":
    sys.exit(main())
