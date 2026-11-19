#!/usr/bin/env python3
"""GM-800: a scene-wide resonant low-pass (FX1 = SuperFilter) whose cutoff follows a MIDI CC, so
Stage Traxx can sweep it from the song (mix.json "gm800_cc" with "ramp": true).
Made for «Попрошу тебя», slot 29, bars 94-101 (wiki/songs/virus-poproshu-tebya.md).

    uv run --python 3.12 --with python-rtmidi --with sounddevice --with numpy \\
        tools/gm800_superfilter.py apply [--slot 29] [--cc 81] [--res 70] [--gain 5] [--parts 1,2]
    ... tools/gm800_superfilter.py restore gear/gm-800/backups/<file>.json

apply writes into the slot's MEMORY by SysEx (like the slot-27 ASSIGNs, wiki gm-800):
  * FX STRUCTURE = PARALLEL (FX1 must not feed the scene's FX2),
  * the given parts' OUTPUT = FX1,
  * FX1 (scene Mfx 6) = SUPERFILTER: LPF, slope -24 dB, cutoff 127, resonance --res, gain --gain
    (the resonance costs ~5 dB of passband level), no modulation; stored SWITCHED OFF. The block
    is first set up in the temp scene (the unit fills the type's defaults) and then copied byte
    for byte into the slot,
  * ASSIGN 1 = CC#<cc> -> FX1 SPR FILTR CUTOFF (target 407), 0..127 over ACT 0..127, MOMENT,
  * ASSIGN 2 = CC#<cc> -> SCENE FX1 SWITCH (target 361): CC 0..126 = ON, 127 = OFF. Even fully open
    the filter colours the sound (res 70: bump at ~6.4 kHz, -7 dB at 10 kHz, -5 dB overall), so
    "open" = no filter at all, the scene sounds exactly as before (measured).
Every block it touches is saved first to gear/gm-800/backups/slot<NN>-superfilter-<time>.json
(restore puts them back). Verified by reading the slot back after reloading the scene.

Calibration (2026-11-19, saw chord via USB, -12 dB point; same through the ASSIGN):
cutoff 32 ~220 Hz, 40 ~250, 48 ~300, 56 ~480, 64 ~670, 72 ~1 kHz, 80 ~1.4 kHz, 88 ~2 kHz,
96 ~3.1 kHz, 104 ~4.4 kHz, ~15.5 steps per octave; resonance 50 -> +5..+8 dB, 80 -> up to +10 dB.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_levels import GM800, SYS_MIDI      # noqa: E402  (Roland SysEx RQ1/DT1 helpers)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUPS = os.path.join(REPO, "gear", "gm-800", "backups")
TEMP = [0x10, 0x00, 0x00, 0x00]
SUPERFILTER = 5                               # Mfx TYPE (MIDI Implementation enumeration)
TARGET_FX1_SF_CUTOFF = 407                    # ASSIGN TARGET TABLE: FX1 SPR FILTR CUTOFF
TARGET_FX1_SW = 361                           # ASSIGN TARGET TABLE: SCENE FX1 SWITCH
MFX_SIZE, ASSIGN_SIZE = 0x84, 0x1D


def slot_base(n):
    v = (n - 1) * 0x10                        # 7-bit address arithmetic
    return [0x40 + v // 128, v % 128, 0, 0]


def at(base, a, b, c):
    return [base[0], base[1] + a, b, c]


def n4(v):                                    # 4-nibble field: value + 32768
    v += 32768
    return [(v >> 12) & 15, (v >> 8) & 15, (v >> 4) & 15, v & 15]


def blocks(base, parts):
    """name -> (address, size) of everything apply touches."""
    out = {"common": (at(base, 0x00, 0x00, 0x00), 0x29),
           "fx1": (at(base, 0x05, 0x50, 0x00), MFX_SIZE),
           "assign1": (at(base, 0x01, 0x00, 0x00), ASSIGN_SIZE),
           "assign2": (at(base, 0x01, 0x01, 0x00), ASSIGN_SIZE)}
    for p in parts:
        out[f"part{p}_output"] = (at(base, 0x02, 0x08 + p - 1, 0x00), 1)
    return out


def rq_ok(g, addr, size):
    for _ in range(5):
        d = g.rq(addr, size)
        if d is not None and len(d) == size:
            return list(d)
        time.sleep(0.2)
    raise SystemExit(f"no answer for {addr} — is the GM-800 connected?")


def dt_ok(g, addr, data):
    """DT1, read back, retry: a lone DT1 is sometimes lost (seen 2026-11-19)."""
    for _ in range(10):
        g.dt(addr, data)
        time.sleep(0.15)
        if rq_ok(g, addr, len(data)) == list(data):
            return
    raise SystemExit(f"write to {addr} did not stick")


def assign_block(cc, old, target, lo, hi, act_lo=0, act_hi=127):
    """SW on, TARGET, MIN lo, MAX hi, SOURCE CC#cc, MOMENT, ACT act_lo..act_hi, RISE/FALL 0; the
    MIDI-out fields after them (bytes 19..28) stay as they were."""
    src = 13 + cc - 1 if cc <= 31 else 44 + cc - 64          # CC#1-31 -> 13.., CC#64-95 -> 44..
    head = ([1] + n4(target - 32768) + n4(lo) + n4(hi)       # TARGET is a plain number
            + [src, 1, act_lo, act_hi, 0, 0])
    return head + list(old[len(head):ASSIGN_SIZE])


def apply(a):
    g = GM800()
    sysb = g.rq(SYS_MIDI, 0x10)
    if not sysb:
        raise SystemExit("GM-800 does not answer SysEx")
    scene_ch = sysb[0] + 1
    parts = [int(p) for p in a.parts.split(",")]
    base = slot_base(a.slot)
    bl = blocks(base, parts)
    backup = {k: {"addr": addr, "data": rq_ok(g, addr, size)} for k, (addr, size) in bl.items()}
    name = bytes(backup["common"]["data"][3:19]).decode("ascii", "replace")
    os.makedirs(BACKUPS, exist_ok=True)
    path = os.path.join(BACKUPS, f"slot{a.slot:02d}-superfilter-{time.strftime('%Y%m%d-%H%M%S')}.json")
    json.dump({"slot": a.slot, "name": name, "blocks": backup}, open(path, "w"), indent=1)
    print(f"slot {a.slot} «{name.strip()}»: backup -> {os.path.relpath(path, REPO)}")
    try:
        # 1) the FX1 block, built in the temp scene so the unit fills SuperFilter's defaults
        g.scene(a.slot, scene_ch)
        tfx = at(TEMP, 0x05, 0x50, 0x00)
        g.dt(tfx, [SUPERFILTER, 1]); time.sleep(0.3)
        for i, v in ((1, 0), (2, 1), (3, 127), (4, a.res), (5, a.gain), (6, 0)):  # LPF -24 dB open reso gain, mod off
            g.dt([tfx[0], tfx[1], tfx[2], 0x04 + 4 * (i - 1)], n4(v))
        time.sleep(0.2)
        fx1 = rq_ok(g, tfx, MFX_SIZE)
        fx1[2] = fx1[3] = 0                    # FX1 sends to chorus/delay and reverb: off
        fx1[1] = 0                             # stored OFF: ASSIGN 2 switches it on (CC < 127)
        # 2) into the slot's memory
        dt_ok(g, at(base, 0x00, 0x00, 0x21), [1])                        # FX STRUCTURE = PARALLEL
        for p in parts:
            dt_ok(g, bl[f"part{p}_output"][0], [1])                      # part OUTPUT = FX1
        dt_ok(g, bl["fx1"][0], fx1)
        asg = assign_block(a.cc, backup["assign1"]["data"], TARGET_FX1_SF_CUTOFF, 0, 127)
        asg2 = assign_block(a.cc, backup["assign2"]["data"], TARGET_FX1_SW, 1, 0, 126, 127)
        g.dt(bl["assign1"][0], asg); time.sleep(0.3)                     # group parameter: one DT1
        g.dt(bl["assign2"][0], asg2); time.sleep(0.3)
        # 3) reload and verify
        g.scene(a.slot, scene_ch)
        got = {k: rq_ok(g, addr, size) for k, (addr, size) in bl.items()}
        ok = (got["common"][0x21] == 1 and all(got[f"part{p}_output"] == [1] for p in parts)
              and got["fx1"] == fx1 and got["assign1"] == asg and got["assign2"] == asg2)
        print(f"written: PARALLEL, parts {parts} -> FX1, FX1 SuperFilter LPF -24 dB res {a.res} gain "
              f"+{a.gain} (stored off), ASSIGN 1 CC#{a.cc} -> cutoff 0..127, ASSIGN 2 CC#{a.cc} 127 -> FX1 off"
              f" | read back after reload: {'OK' if ok else 'MISMATCH'}")
        if not ok:
            raise SystemExit("verification failed — restore from the backup")
    finally:
        g.close()


def restore(a):
    b = json.load(open(a.file))
    g = GM800()
    try:
        for k, v in b["blocks"].items():
            if k.startswith("assign"):
                g.dt(v["addr"], v["data"]); time.sleep(0.3)
            else:
                dt_ok(g, v["addr"], v["data"])
            print("restored", k)
    finally:
        g.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("apply")
    p.add_argument("--slot", type=int, default=29)
    p.add_argument("--cc", type=int, default=81)
    p.add_argument("--res", type=int, default=70)
    p.add_argument("--gain", type=int, default=5)
    p.add_argument("--parts", default="1,2")
    p = sp.add_parser("restore")
    p.add_argument("file")
    a = ap.parse_args()
    if a.cmd == "apply":
        if not (1 <= a.cc <= 31 or 64 <= a.cc <= 95) or 71 <= a.cc <= 79:
            raise SystemExit("--cc must be 1..31 or 64..95, not 71..79")
        apply(a)
    else:
        restore(a)
