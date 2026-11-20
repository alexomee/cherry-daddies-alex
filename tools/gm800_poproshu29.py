#!/usr/bin/env python3
"""GM-800 slot 29 POPROSHU TEBYA * (Alex's lead / solo scene in «Попрошу тебя»): too dry next to the record (Alex
2026-11-20: «слишком сухо звучит, наверное надо какой-то эффект добавить»). Tests effect variants in the TEMP scene
on the lead of bars 77-80 (MIDI track «Клавиши», where the record's keys stem holds the lead alone) and compares
them with the record; `store` writes the chosen one into the slot (backups with time, read back).

    gm9() { uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with sounddevice \\
            --with python-rtmidi --with pyloudnorm --with librosa --with mido tools/gm800_poproshu29.py "$@"; }
    gm9 test                       # every variant of VARIANTS, takes + table against the record
    gm9 store NAME                 # that variant into slot 29's memory

Scene 29 as found (2026-11-20): parts 1-2 Harpsichord 1 (oct +1 / 0), PLAY FEEL 2, TEMPO 120 (the song is 140),
Chorus/Delay on (SDD-320) but every part's send 0, Reverb on (level 70), sends 30. FX1 = the SuperFilter of bars
94-101 (gm800_superfilter.py) is not touched.
"""
import argparse, importlib.util, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
sys.argv, _argv = sys.argv[:1], sys.argv
gp = importlib.util.module_from_spec(_s); _s.loader.exec_module(gp)
sys.argv = _argv
gmm = gp.gmm; SR = gp.SR
SLOT, TEMP, VEL = 29, 0x10, 80
MIDI = os.path.join(REPO, "music", "songs", "Вирус - Попрошу тебя", "parts", "poproshu-midifind.mid")
NOTE = {"1/16": 6, "1/16.": 8, "1/8": 9, "1/8.": 11, "1/4": 12}
# name -> (delay note or None, delay LEVEL, feedback %, C/D send of the parts, reverb send of the parts[, TONE MODIFY
# deltas of parts 1-2 {"decay", "release", "cutoff"} against the scene's own values])
VARIANTS = {"asis": None,
            "dly8": ("1/8", 40, 20, 127, 30),
            "dly16d": ("1/16.", 40, 20, 127, 30),
            "rev80": (None, 0, 0, 0, 80),
            "dly8rev60": ("1/8", 40, 20, 127, 60),
            "long": (None, 0, 0, 0, 30, {"decay": 40, "release": 50}),
            "d16long": ("1/16.", 60, 30, 127, 30, {"decay": 30, "release": 40}),
            "d8long": ("1/8", 60, 30, 127, 30, {"decay": 30, "release": 40}),
            "d16longdark": ("1/16.", 60, 30, 127, 30, {"decay": 30, "release": 40, "cutoff": -8}),
            "mid16": ("1/16.", 40, 20, 127, 30, {"decay": 20, "release": 25}),
            "mid8": ("1/8", 40, 20, 127, 30, {"decay": 15, "release": 20}),
            "mid": (None, 0, 0, 0, 30, {"decay": 25, "release": 30})}
MOD = {"cutoff": 0x03, "decay": 0x06, "release": 0x07}
BASE = {1: {"cutoff": 59, "decay": 64, "release": 64}, 2: {"cutoff": 64, "decay": 64, "release": 64}}   # read 2026-11-20


def n4(v):
    return [(v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15]


def set_temp(dt, v, parts=(0, 1)):
    if v is None:
        return
    note, level, fb, cd_send, rev_send, *mod = v
    dt([TEMP, 0x00, 0x00, 0x1C], n4(140))                     # scene TEMPO = the song (was 120)
    for k, dv in (mod[0] if mod else {}).items():             # TONE MODIFY of parts 1-2 (longer decay/release ...)
        for p in parts:
            dt([TEMP, 0x02, 0x10 + p, MOD[k]], [max(0, min(127, BASE[p + 1][k] + dv))])
    cd = [TEMP, 0x03, 0x00]
    if note:
        dt(cd + [0x01], [4]); time.sleep(0.4)                  # Chorus/Delay type DELAY (unit fills its defaults)
        dt(cd + [0x00], [1]); dt(cd + [0x02], n4(level))
        for i, x in ((1, 1), (3, NOTE[note]), (4, fb), (5, 13)):   # Sync ON, note, feedback, HF damp 4 kHz
            dt(cd + [0x0A + 4 * (i - 1)], n4(x + 32768))
    for p in parts:
        dt([TEMP, 0x02, p, 0x0A], [cd_send]); dt([TEMP, 0x02, p, 0x0B], [rev_send])
    time.sleep(0.4)


def lead_line(song, b0=77, b1=81):
    import mido
    m = mido.MidiFile(MIDI); tpb = m.ticks_per_beat; tick = 0; on = {}; line = []
    for msg in m.tracks[2]:                                    # «Клавиши»
        tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            on[msg.note] = tick
        elif msg.type in ("note_off", "note_on") and msg.note in on:
            t0 = on.pop(msg.note); pos = t0 / tpb / 4 + 1 + 2     # our bar = MIDI bar + 2
            if b0 <= pos < b1:
                line.append(((pos - b0) * song.bar, msg.note, (tick - t0) / tpb * song.bar / 4 - 0.02))
    return sorted(line)


def take(rig, song, line, tag):
    sp = [x for x in gp.scene_parts(rig, gp.tone_names()) if x[2]]
    shifts = {ch: sh for _, ch, *_ in sp for sh in [gp.probe_shift(rig, ch)] if sh is not None}
    ref = min(shifts.values()); time.sleep(1.5); gmm.VEL = VEL
    x = gp.play(rig, [(t, n - ref, d, ch) for t, n, d in line for ch in shifts], tail=2.5)
    out = os.path.join(song.out, f"scene29-{tag}.wav"); gmm.save(out, x)
    return out


def metrics(song, path, b0=77, b1=81):
    """dip between notes (median over the 16ths of the bars: quietest 10 ms vs loudest, dB), score, centroid."""
    dur = (b1 - b0) * song.bar
    ref = song.read("keys.wav", song.t_stem(b0), song.t_stem(b0) + dur + 1).mean(1)
    x = path if isinstance(path, np.ndarray) else gmm.read_wav(path).mean(1)

    def dip(y):
        s16 = song.bar / 16; n = int(0.01 * SR); out = []
        for k in range(int((b1 - b0) * 16)):
            seg = y[int(k * s16 * SR):int((k + 1) * s16 * SR)]
            e = [np.sqrt(np.mean(seg[i:i + n] ** 2)) + 1e-9 for i in range(0, len(seg) - n, n)]
            out.append(20 * np.log10(min(e) / max(e)))
        return float(np.median(out))

    def cent(y):
        F = np.abs(np.fft.rfft(y * np.hanning(len(y)))); f = np.fft.rfftfreq(len(y), 1 / SR)
        return float((F * f).sum() / F.sum())
    R = gp.cqt_db(ref[:int(dur * SR)])
    sc = gp.sweep_score(R, gp.cqt_db(x[:int(dur * SR)]), song.semi)[0]
    return dip(x[:int(dur * SR)]), sc, cent(x[:int(dur * SR)]), dip(ref[:int(dur * SR)]), cent(ref[:int(dur * SR)])


def cmd_test(names):
    song = gmm.Song("Попрошу"); line = lead_line(song); res = {}
    with gmm.Rig() as rig:
        for nm in names:
            rig.load(SLOT); set_temp(rig.g.dt, VARIANTS[nm]); res[nm] = take(rig, song, line, nm)
    rd = None
    for nm, p in res.items():
        d, sc, ce, rd, rc = metrics(song, p)
        print(f"  {nm:10} dip between notes {d:6.1f} dB   score {sc:.3f}   centroid {ce:5.0f} Hz")
    print(f"  {'record':10} dip between notes {rd:6.1f} dB                  centroid {rc:5.0f} Hz")


def cmd_store(name):
    sx = gmm.Sx()
    try:
        stamp = time.strftime("%H%M%S")
        before, pb = gmm.backup(sx, SLOT, f"before-fx-{stamp}")
        if len(before) != 88 or not gmm.scene_name(before).startswith("POPROSHU"):
            raise SystemExit(f"slot {SLOT}: '{gmm.scene_name(before)}' / {len(before)} blocks: not writing")
        for m in ([0xB1, 0, 0], [0xB1, 32, 0], [0xC1, SLOT - 1]):
            sx.o.send_message(m)
        time.sleep(1.5)
        set_temp(lambda ad, d: sx.dt(ad, d, 0.08), VARIANTS[name]); time.sleep(0.5)
        new = sx.dump([TEMP, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        sx.write(gmm.slot_base(SLOT), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, SLOT, f"after-fx-{stamp}")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {SLOT} '{gmm.scene_name(after)}': {name}, 88 blocks written, mismatches {bad or 'none'}\n"
              f"  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC1, 0])
    finally:
        sx.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("test"); p.add_argument("names", nargs="*", default=list(VARIANTS))
    p = sub.add_parser("store"); p.add_argument("name", choices=list(VARIANTS))
    a = ap.parse_args()
    cmd_test(a.names) if a.cmd == "test" else cmd_store(a.name)
