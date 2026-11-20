#!/usr/bin/env python3
"""Plain offline render of a MIDI file's bars, or of notes.json voices, to mp3 - for an A/B of rhythm and notes
by ear, not of sound (wiki/pipelines/part-transcription-guide.md; «Мама Люба» 2026-11-20: the hook from the stem
against the MIDI from the web, both through the same simple synth).

  uv run -q --python 3.12 --with numpy --with scipy --with mido python tools/midi_preview.py \
      midi  ~/Downloads/song.mid 78 98 -2 /tmp/midi-solo.mp3       # MIDI bars 78-97, all tracks, -2 semitones
  ... python tools/midi_preview.py notes "music/songs/<song>/parts/x.notes.json" 86 110 0 /tmp/my-solo.mp3

Bars are those of the source (MIDI bars count from 1 at tick 0, 4/4; notes.json = mix.json bars). Tempo is constant:
BPM env var (default 127.5) (the MIDI's own tempo map is ignored). GM-ish timbres by program family,
channel 10 = simple synthesized drums; notes.json voices: bass*, lead*, the rest as brass. Mono mp3, peak -1 dB.
"""
import os, sys, json, subprocess, numpy as np, mido
from scipy.signal import butter, sosfilt
SR = 44100; rng = np.random.default_rng(1)
def env(n, a=0.005, r=0.06, dec=None):
    t = np.arange(n) / SR; e = np.minimum(1, t / a)
    if dec: e = e * np.exp(-t / dec)
    rn = int(r * SR); 
    if n > rn: e[-rn:] *= np.linspace(1, 0, rn)
    return e
def osc(kind, f, n):
    t = np.arange(n) / SR; ph = (f * t) % 1
    if kind == "saw": return 2 * ph - 1
    if kind == "square": return np.where(ph < 0.5, 1.0, -1.0)
    if kind == "tri": return 2 * np.abs(2 * ph - 1) - 1
    return np.sin(2 * np.pi * f * t)
def lp(x, fc): return sosfilt(butter(2, fc, "lowpass", fs=SR, output="sos"), x)
def tone(prog, f, dur, vel):
    n = int((dur + 0.06) * SR); g = vel / 127
    if 32 <= prog <= 39: x = lp(osc("saw", f, n), 700) * env(n, r=0.04) * 0.9
    elif 24 <= prog <= 31: x = lp(osc("square", f, n), 1800) * env(n) * 0.25
    elif 56 <= prog <= 63 or 80 <= prog <= 87: x = lp(osc("saw", f, n) + 0.5 * osc("saw", f * 1.003, n), 5000) * env(n, r=0.05) * 0.45
    elif 64 <= prog <= 71: x = lp(osc("tri", f, n) + 0.3 * osc("saw", f, n), 3000) * env(n, a=0.02) * 0.4
    elif 16 <= prog <= 23: x = (osc("sine", f, n) + 0.5 * osc("sine", 2 * f, n) + 0.3 * osc("sine", 3 * f, n)) * env(n) * 0.2
    else: x = osc("sine", f, n) * env(n) * 0.2
    return x * g
def drum(note, vel):
    g = vel / 127
    if note in (35, 36):
        n = int(0.3 * SR); t = np.arange(n) / SR; f = 50 + 90 * np.exp(-t / 0.03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * g
    if note in (38, 40, 39):
        n = int(0.2 * SR); t = np.arange(n) / SR
        return (lp(rng.standard_normal(n), 6000) * 0.5 + 0.4 * np.sin(2 * np.pi * 190 * t)) * np.exp(-t / 0.06) * g * 0.8
    if note in (42, 44, 46):
        n = int((0.25 if note == 46 else 0.05) * SR); t = np.arange(n) / SR
        x = rng.standard_normal(n); x = x - lp(x, 7000)
        return x * np.exp(-t / (0.12 if note == 46 else 0.015)) * g * 0.35
    if note in (49, 57, 51, 55):
        n = int(1.2 * SR); t = np.arange(n) / SR; x = rng.standard_normal(n); x = x - lp(x, 4000)
        return x * np.exp(-t / 0.4) * g * 0.25
    n = int(0.2 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (80 + note) * t) * np.exp(-t / 0.08) * g * 0.4
def place(buf, x, t):
    a = int(t * SR); m = min(len(x), len(buf) - a)
    if a >= 0 and m > 0: buf[a:a + m] += x[:m]
mode, src, b0, b1, semi, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
bpm = float(os.environ.get("BPM", 127.5)); bar = 240 / bpm      # BPM=... to override
buf = np.zeros(int(((b1 - b0) * bar + 2) * SR))
if mode == "midi":
    m = mido.MidiFile(src); tpb = m.ticks_per_beat
    for tr in m.tracks:
        tick = 0; prog = {}; on = {}
        for msg in tr:
            tick += msg.time
            if msg.type == "program_change": prog[msg.channel] = msg.program
            elif msg.type == "note_on" and msg.velocity > 0: on[(msg.channel, msg.note)] = (tick, msg.velocity)
            elif msg.type in ("note_off", "note_on") and (msg.channel, msg.note) in on:
                t0, v = on.pop((msg.channel, msg.note)); pos = t0 / tpb / 4 + 1
                if not (b0 <= pos < b1): continue
                t = (pos - b0) * bar; d = (tick - t0) / tpb * 60 / bpm
                if msg.channel == 9: place(buf, drum(msg.note, v), t)
                else: place(buf, tone(prog.get(msg.channel, 0), 440 * 2 ** ((msg.note + semi - 69) / 12), d, v), t)
else:                                              # notes.json voices (band key), prog per voice group
    part = json.load(open(src)); N = "C C# D D# E F F# G G# A A# B".split()
    mid = lambda s: N.index(s[:-1]) + 12 * (int(s[-1]) + 1)
    for vn, v in part["voices"].items():
        prog = 33 if vn.startswith("bass") else 81 if vn.startswith("lead") else 61
        gain = {"lead5": 10 ** (-4 / 20), "leadsub": 10 ** (-6 / 20)}.get(vn.split("_")[0], 1.0) * (0.6 if vn.startswith("pad") else 1.0)
        for at in v["at"]:
            for bb, bt, ln, p in v["notes"]:
                pos = at + bb - 1 + (bt - 1) / 4
                if not (b0 <= pos < b1): continue
                for s in p.split():
                    place(buf, gain * tone(prog, 440 * 2 ** ((mid(s) - 69) / 12), ln * bar / 4 - v.get("gap", 0.03), 100), (pos - b0) * bar)
buf = buf / (np.abs(buf).max() + 1e-9) * 0.9
subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "192k", out],
               input=buf.astype(np.float32).tobytes(), check=True)
print(out, f"{len(buf) / SR:.1f} s")
