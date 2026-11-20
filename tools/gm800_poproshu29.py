#!/usr/bin/env python3
"""GM-800 slot 29 POPROSHU TEBYA * (Alex's lead / solo scene in «Попрошу тебя»): too dry next to the record (Alex
2026-11-20: «слишком сухо звучит, наверное надо какой-то эффект добавить»). Tests effect variants in the TEMP scene
on the lead of bars 77-80 (MIDI track «Клавиши», where the record's keys stem holds the lead alone) and compares
them with the record; `store` writes the chosen one into the slot (backups with time, read back).

    gm9() { uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with sounddevice \\
            --with python-rtmidi --with pyloudnorm --with librosa --with mido tools/gm800_poproshu29.py "$@"; }
    gm9 test                       # every variant of VARIANTS, takes + table against the record
    gm9 store NAME                 # that variant into slot 29's memory
    gm9 layer-test [--level L] [--alone]   # 198 Fat Mask Dist Ld in part 3 (TEMP), lead 77-80 vs the record
    gm9 layer-store --level L              # the layer into slot 29's memory
    gm9 match-test                 # part 3 (198) with the harpsichord's play settings, legato line, before/after
    gm9 match-store                # those settings into slot 29's memory
    gm9 level-test 127 100 80      # harpsichord alone vs the whole scene at these SCENE LEVELs (LUFS)
    gm9 level-store L              # SCENE LEVEL into slot 29's memory

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


# ---- the layer (Alex 2026-11-20: «проблема в тоне… в оригинале явно что-то трубное или saw-ное» → «198 пила»):
# 198 Fat Mask Dist Ld in part 3 (was off: MK-80 Chorus EP), over the harpsichord. Short list of 51 tones (brass
# categories, cut short, + 13 leads of the sweep journal) as a layer on scene 29: 198 at +3 dB to the harpsichord
# was closest to the record's lead in 77-78 (0.908 vs 0.870 alone; gap between notes -6.4 vs -12.0 dB).
LAYER_PART, LAYER_TONE = 3, 198


def set_layer(dt, level):
    import csv
    r = next(r for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t") if int(r[0]) == LAYER_TONE)
    p = LAYER_PART - 1
    dt([TEMP, 0x02, p, 0x00], [int(r[2]), int(r[3]), int(r[4]) - 1]); time.sleep(0.6)
    for off, v in ((0x04, 1), (0x06, level), (0x08, 0), (0x09, 64), (0x0A, 0), (0x0B, 30)):   # on, level, unmuted,
        dt([TEMP, 0x02, p, off], [v])                                                      # centre, sends as 1-2
    dt([TEMP, 0x02, 0x08 + p, 0x00], [1])             # OUTPUT = FX1, like parts 1-2 (the 94-101 filter sweep)
    dt([TEMP, 0x02, 0x10 + p, 0x02], [32])            # TONE MOD OCT SHIFT 0
    time.sleep(0.4)


def cmd_layer_test(level, alone):
    song = gmm.Song("Попрошу"); line = lead_line(song)
    with gmm.Rig() as rig:
        rig.load(SLOT); set_layer(rig.g.dt, level)
        print("part 3:", rig.g.rq([TEMP, 0x02, LAYER_PART - 1, 0x00], 12), "out", rig.g.rq([TEMP, 0x02, 0x08 + LAYER_PART - 1, 0], 1),
              "oct", rig.g.rq([TEMP, 0x02, 0x10 + LAYER_PART - 1, 0x02], 1))
        if alone:
            for q in (0, 1):
                rig.g.dt([TEMP, 0x02, q, 0x04], [0])
            p = take(rig, song, line, f"layer198-alone-l{level}")
        else:
            p = take(rig, song, line, f"layer198-l{level}")
    d, sc, ce, rd, rc = metrics(song, p)
    print(f"  {os.path.basename(p)}: LUFS {gmm.lufs(gmm.read_wav(p)):.1f}  dip {d:.1f} dB  score {sc:.3f}  centroid {ce:.0f} Hz"
          f"  (record: dip {rd:.1f}, centroid {rc:.0f})")


# ---- the layer plays together with the harpsichord (Alex 2026-11-20: «звуки как будто не вместе играют, атака разная?»).
# Same MIDI clock: onsets equal (< 1 ms), pitch steady. The difference is in ToneOthers (02 6P): 198 came with its lead
# defaults (CHROMATIC OFF, MONO, LEGATO ON, PORTA ON time 3), the harpsichord parts are CHROMATIC TYPE2, POLY, HOLD 3,
# legato/porta off. From the guitar the strings overlap: 198 then slides into the next note without a new attack while
# the harpsichord plucks every note. `match` copies parts 1-2's play settings to part 3.
OTHERS = 0x60                                          # SceneToneOthers P: chromatic, mono/poly, hold, legato, porta sw,
                                                       # porta time, porta type, unison, bend range (+ fixed 0)


def set_match(rig_or_dt, src=0):
    """Part 3's ToneOthers = part `src`+1's (read from TEMP). rig_or_dt = (rq, dt)."""
    rq, dt = rig_or_dt
    v = rq([TEMP, 0x02, OTHERS + src, 0], 9)
    dt([TEMP, 0x02, OTHERS + LAYER_PART - 1, 0], v); time.sleep(0.3)
    return v


def legato_line(line, over=0.03):
    """Each note held until the next note-on + `over` s, like ringing strings."""
    return [(t, n, (line[i + 1][0] - t + over) if i + 1 < len(line) else d) for i, (t, n, d) in enumerate(line)]


def retrig(song, x, line):
    """Per note of the layer alone: rise of the envelope at the note-on (dB: max of 0-30 ms vs 15 ms before)."""
    y = x.mean(1) if x.ndim > 1 else x; n = int(0.002 * SR); out = []
    for t, m, d in line[1:]:
        a = int(t * SR)
        pre = np.sqrt(np.mean(y[a - int(0.015 * SR):a] ** 2)) + 1e-9
        post = max(np.sqrt(np.mean(y[i:i + n] ** 2)) for i in range(a, a + int(0.03 * SR), n))
        out.append(20 * np.log10(post / pre))
    return np.array(out)


def cmd_match_test():
    song = gmm.Song("Попрошу"); line = legato_line(lead_line(song)); res = {}
    with gmm.Rig() as rig:
        for tag in ("before", "after"):
            rig.load(SLOT)
            if tag == "after":
                print("part 3 ToneOthers <- part 1:", set_match((rig.g.rq, rig.g.dt)))
            print(f"{tag}: part 3 ToneOthers", rig.g.rq([TEMP, 0x02, OTHERS + LAYER_PART - 1, 0], 9))
            res[tag] = take(rig, song, line, f"legato-{tag}")
            for q in (0, 1):
                rig.g.dt([TEMP, 0x02, q, 0x04], [0])
            res[tag + "-198"] = take(rig, song, line, f"legato-{tag}-198alone")
    for tag in ("before", "after"):
        r = retrig(song, gmm.read_wav(res[tag + "-198"]), line)
        print(f"  198 alone, {tag:6}: new attack per note (rise dB) median {np.median(r):5.1f}, "
              f"notes with a rise < 3 dB: {int((r < 3).sum())} of {len(r)}")


def cmd_match_store():
    sx = gmm.Sx()
    try:
        stamp = time.strftime("%H%M%S")
        before, pb = gmm.backup(sx, SLOT, f"before-match-{stamp}")
        if len(before) != 88 or not gmm.scene_name(before).startswith("POPROSHU"):
            raise SystemExit(f"slot {SLOT}: '{gmm.scene_name(before)}' / {len(before)} blocks: not writing")
        for m in ([0xB1, 0, 0], [0xB1, 32, 0], [0xC1, SLOT - 1]):
            sx.o.send_message(m)
        time.sleep(1.5)
        src = before.get("02 60 00")                      # part 1's ToneOthers in the slot (Sx has no single read)
        if not src:
            raise SystemExit(f"slot {SLOT}: no block 02 60 00 in the dump ({sorted(before)[:5]}...)")
        v = list(src[:9]); sx.dt([TEMP, 0x02, OTHERS + LAYER_PART - 1, 0], v, 0.3); time.sleep(0.5)
        new = sx.dump([TEMP, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        sx.write(gmm.slot_base(SLOT), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, SLOT, f"after-match-{stamp}")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {SLOT} '{gmm.scene_name(after)}': part 3 ToneOthers = {v}, 88 blocks written, "
              f"mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC1, 0])
    finally:
        sx.close()


# ---- SCENE LEVEL (Alex 2026-11-20: «громче получилось? убавь»): the 198 layer made the scene louder than the
# harpsichord alone, which Alex's live level was set with. SceneCommon 0x13 = SCENE LEVEL (keeps the part balance).
SCENE_LEVEL = [TEMP, 0x00, 0x00, 0x13]


def cmd_level_test(levels):
    """Harpsichord alone at the stored scene level (the reference) and the whole scene at each of `levels`."""
    song = gmm.Song("Попрошу"); line = lead_line(song); res = []
    with gmm.Rig() as rig:
        rig.load(SLOT); sl = rig.g.rq(SCENE_LEVEL, 1)[0]
        rig.g.dt([TEMP, 0x02, LAYER_PART - 1, 0x04], [0]); time.sleep(0.3)
        ref = gmm.lufs(gmm.read_wav(take(rig, song, line, f"level-harp-alone-sl{sl}")))
        print(f"stored SCENE LEVEL {sl}; harpsichord alone {ref:.1f} LUFS")
        for lv in levels:
            rig.load(SLOT); rig.g.dt(SCENE_LEVEL, [lv]); time.sleep(0.3)
            x = gmm.lufs(gmm.read_wav(take(rig, song, line, f"level-all-sl{lv}")))
            res.append((lv, x)); print(f"  scene level {lv:3}: {x:.1f} LUFS ({x - ref:+.1f} dB to the harpsichord alone)")
    return ref, res


def cmd_level_store(level):
    sx = gmm.Sx()
    try:
        stamp = time.strftime("%H%M%S")
        before, pb = gmm.backup(sx, SLOT, f"before-level-{stamp}")
        if len(before) != 88 or not gmm.scene_name(before).startswith("POPROSHU"):
            raise SystemExit(f"slot {SLOT}: '{gmm.scene_name(before)}' / {len(before)} blocks: not writing")
        for m in ([0xB1, 0, 0], [0xB1, 32, 0], [0xC1, SLOT - 1]):
            sx.o.send_message(m)
        time.sleep(1.5)
        sx.dt(SCENE_LEVEL, [level], 0.3); time.sleep(0.5)
        new = sx.dump([TEMP, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        sx.write(gmm.slot_base(SLOT), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, SLOT, f"after-level-{stamp}")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {SLOT} '{gmm.scene_name(after)}': SCENE LEVEL {before['00 00 00'][0x13]} -> {after['00 00 00'][0x13]}, "
              f"88 blocks written, mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC1, 0])
    finally:
        sx.close()


def cmd_layer_store(level):
    sx = gmm.Sx()
    try:
        stamp = time.strftime("%H%M%S")
        before, pb = gmm.backup(sx, SLOT, f"before-layer198-{stamp}")
        if len(before) != 88 or not gmm.scene_name(before).startswith("POPROSHU"):
            raise SystemExit(f"slot {SLOT}: '{gmm.scene_name(before)}' / {len(before)} blocks: not writing")
        for m in ([0xB1, 0, 0], [0xB1, 32, 0], [0xC1, SLOT - 1]):
            sx.o.send_message(m)
        time.sleep(1.5)
        set_layer(lambda ad, d: sx.dt(ad, d, 0.08), level); time.sleep(0.5)
        new = sx.dump([TEMP, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        sx.write(gmm.slot_base(SLOT), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, SLOT, f"after-layer198-{stamp}")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {SLOT} '{gmm.scene_name(after)}': part 3 = {LAYER_TONE} level {level}, 88 blocks written, "
              f"mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC1, 0])
    finally:
        sx.close()


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
    p = sub.add_parser("layer-test"); p.add_argument("--level", type=int, default=100); p.add_argument("--alone", action="store_true")
    p = sub.add_parser("layer-store"); p.add_argument("--level", type=int, required=True)
    sub.add_parser("match-test"); sub.add_parser("match-store")
    p = sub.add_parser("level-test"); p.add_argument("levels", type=int, nargs="+")
    p = sub.add_parser("level-store"); p.add_argument("level", type=int)
    a = ap.parse_args()
    if a.cmd == "level-test":
        cmd_level_test(a.levels)
    elif a.cmd == "level-store":
        cmd_level_store(a.level)
    elif a.cmd == "match-test":
        cmd_match_test()
    elif a.cmd == "match-store":
        cmd_match_store()
    elif a.cmd == "test":
        cmd_test(a.names)
    elif a.cmd == "store":
        cmd_store(a.name)
    elif a.cmd == "layer-test":
        cmd_layer_test(a.level, a.alone)
    else:
        cmd_layer_store(a.level)
