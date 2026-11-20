#!/usr/bin/env python3
"""GM-800 slot 28 POPROSHU TEBYA («Попрошу тебя», the keys stabs Alex plays) made fuller, like the record's
detuned supersaw with its 1/8 echo (Alex 2026-11-20: «звучит гораздо беднее оригинала… пресет + 316 с эхом
сделай»). Sweep of 32 saw tones layered onto the preset: 316 Trance Syn Poly 6 dB under the preset was closest
to the record (wiki/songs/virus-poproshu-tebya.md).

    gm8() { uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with sounddevice \\
            --with python-rtmidi --with pyloudnorm --with librosa tools/gm800_poproshu28.py "$@"; }
    gm8 test --part 4 [--echo 40] [--level L]   # builds it in the TEMP scene only and records bars 3-6
    gm8 store --part 4 --level L --echo E       # the same into slot 28's memory (backups before/after)

What it sets (TEMP first; `store` writes the whole TEMP scene into the slot, like gm800_match.py build):
  * part --part = 316 Trance Syn Poly, its TONE MOD OCT SHIFT set to 0 (the replaced Saw Seq part had +2 and a
    new tone keeps the part's modify), PART LEVEL
    --level (PART LEVEL is ~40·lg: measured), pan centre, all strings as before;
  * scene Chorus/Delay: ON, type DELAY, Dly Sync ON, Dly Note 1/8, Feedback +15 %, HF Damp 4 kHz, LEVEL --echo,
    every sounding part's CHO/DLY SEND 127. System C/D PREFERENCE is SCENE (read 2026-11-20): only this scene.
Takes go to analysis/gm800-match/Вирус - Попрошу тебя/scene28-*.wav.
"""
import argparse, csv, importlib.util, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
sys.argv, _argv = sys.argv[:1], sys.argv
gp = importlib.util.module_from_spec(_s); _s.loader.exec_module(gp)
sys.argv = _argv
gmm = gp.gmm; SR = gp.SR
SLOT, TONE = 28, 316
NOTE_1_8, HF_4K = 9, 13          # Note list index of 1/8; HF Damp list 200 250 315 400 500 630 800 1k 1k25 1k6 2k 2k5 3k15 4k ...
TEMP = 0x10


def n4(v):
    return [(v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15]


def set_temp(dt, part, level, echo, nosend=()):
    """Scene 28 is loaded in TEMP; put 316 into `part` and the 1/8 echo on. dt(addr, data) = a DT1 sender."""
    r = next(r for r in csv.reader(open(gmm.TONES, encoding="utf-8"), delimiter="\t") if int(r[0]) == TONE)
    p = part - 1
    dt([TEMP, 0x02, p, 0x00], [int(r[2]), int(r[3]), int(r[4]) - 1]); time.sleep(0.6)
    dt([TEMP, 0x02, p, 0x04], [1]); dt([TEMP, 0x02, p, 0x06], [level]); dt([TEMP, 0x02, p, 0x09], [64])
    dt([TEMP, 0x02, 0x10 + p, 0x02], [32])      # TONE MOD OCT SHIFT 0: the Saw Seq part had +2 and the tone keeps it
    if echo:
        cd = [TEMP, 0x03, 0x00]
        dt(cd + [0x01], [4]); time.sleep(0.4)                            # type DELAY (unit fills its defaults)
        dt(cd + [0x00], [1])                                             # switch on
        dt(cd + [0x02], n4(echo))                                        # LEVEL
        for i, v in ((1, 1), (3, NOTE_1_8), (4, 15), (5, HF_4K)):       # Sync ON, 1/8, feedback +15 %, HF 4 kHz
            dt(cd + [0x0A + 4 * (i - 1)], n4(v + 32768))   # Param n = 0A + 4(n-1) (label on its last nibble)
        for q in range(4):
            dt([TEMP, 0x02, q, 0x0A], [0 if q + 1 in nosend else 127])   # CHO/DLY SEND (none from --nosend parts)
    time.sleep(0.4)


def rhythm_line(song):
    part = json.load(open(os.path.join(song.dir, "parts", "rhythm.notes.json"), encoding="utf-8"))
    test = {"voices": {"t": {"at": [1], "bars": 200, "notes": []}}}
    # bars 3-6 of the record's progression, in the voicing of rhythm.notes.json (Cm Ab Eb Bb)
    sys.path.insert(0, os.path.join(REPO, "tools", "jamzone"))
    sp = importlib.util.spec_from_file_location("pp", os.path.join(REPO, "tools", "jamzone", "prep_poproshu_tebya.py"))
    pp = importlib.util.module_from_spec(sp); sp.loader.exec_module(pp)
    st = pp.midi_stabs()
    for bar in range(3, 7):
        for q, c in st.get(bar, []):
            test["voices"]["t"]["notes"].append([bar, 1 + q / 4, pp.STAB / 4, pp.VOICING[c]])
    return gp.voice_line(song, test, "t", 3, 7)


def take(rig, song, line, vel, tag):
    tones = gp.tone_names()
    sp = [x for x in gp.scene_parts(rig, tones) if x[2]]
    shifts = {}
    for pnum, ch, on, num, name, level in sp:
        sh = gp.probe_shift(rig, ch)
        if sh is not None:
            shifts[ch] = sh
    ref = min(shifts.values()); time.sleep(1.5)
    gmm.VEL = vel
    x = gp.play(rig, [(t, n - ref, d, ch) for t, n, d in line for ch in shifts], tail=2.0)
    out = os.path.join(song.out, f"scene28-{tag}.wav"); gmm.save(out, x)
    print(f"  parts {[(q[0], q[3], q[4], q[5]) for q in sp]} -> {os.path.basename(out)}  LUFS {gmm.lufs(x):.1f}")
    return x


def cmd_test(a):
    song = gmm.Song("Попрошу"); line = rhythm_line(song)
    with gmm.Rig() as rig:
        rig.load(SLOT)
        set_temp(rig.g.dt, a.part, a.level, a.echo, a.nosend)
        got = rig.g.rq([TEMP, 0x02, a.part - 1, 0x00], 12); cdv = rig.g.rq([TEMP, 0x03, 0x00, 0x00], 0x1D)
        print(f"TEMP: part {a.part} = {got[:3]} level {got[6]} pan {got[9]} send {got[10]}; C/D sw/type {cdv[:2]} "
              f"level {cdv[2:6]} params {[cdv[10 + 4 * i:14 + 4 * i] for i in range(5)]}")
        take(rig, song, line, a.vel, f"p{a.part}-l{a.level}-e{a.echo}-v{a.vel}" + (f"-ns{''.join(map(str, a.nosend))}" if a.nosend else ""))
        if a.alone:                                    # the 316 part alone, for its level
            for q in range(4):
                if q != a.part - 1:
                    rig.g.dt([TEMP, 0x02, q, 0x04], [0])
            take(rig, song, line, a.vel, f"p{a.part}-alone-l{a.level}-v{a.vel}")


def cmd_store(a):
    sx = gmm.Sx()
    try:
        before, pb = gmm.backup(sx, SLOT, f"before-enrich-{time.strftime('%H%M%S')}")
        if len(before) != 88 or gmm.scene_name(before)[:8] != "POPROSHU":
            raise SystemExit(f"slot {SLOT}: '{gmm.scene_name(before)}' / {len(before)} blocks: not writing")
        ch = 2                                         # Scene Rx channel (gm-800.md): bank 0, then the PC
        for m in ([0xB0 | (ch - 1), 0, 0], [0xB0 | (ch - 1), 32, 0], [0xC0 | (ch - 1), SLOT - 1]):
            sx.o.send_message(m)
        time.sleep(1.5)
        set_temp(lambda ad, d: sx.dt(ad, d, 0.08), a.part, a.level, a.echo, a.nosend)
        time.sleep(0.5)
        new = sx.dump([TEMP, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        sx.write(gmm.slot_base(SLOT), new); time.sleep(0.5)
        after, pa = gmm.backup(sx, SLOT, f"after-enrich-{time.strftime('%H%M%S')}")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {SLOT} '{gmm.scene_name(after)}': 88 blocks written, mismatches {bad or 'none'}\n"
              f"  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC0 | 1, 0])                # leave the synth on scene 1 MUTE
    finally:
        sx.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nm in ("test", "store"):
        p = sub.add_parser(nm)
        p.add_argument("--part", type=int, default=4); p.add_argument("--level", type=int, default=100)
        p.add_argument("--echo", type=int, default=40); p.add_argument("--vel", type=int, default=63)
        p.add_argument("--alone", action="store_true")
        p.add_argument("--nosend", default="", help="parts with no echo, e.g. 3")
    a = ap.parse_args()
    a.nosend = tuple(int(v) for v in a.nosend.split(",") if v)
    cmd_test(a) if a.cmd == "test" else cmd_store(a)
