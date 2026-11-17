#!/usr/bin/env python3
"""BOSS GM-800 liveset (.tsl) tool: list, diff and build scene layouts.

A .tsl from BOSS TONE STUDIO (Librarian → Export → EXPORT TO FILE) is JSON:
    {"name", "formatRev", "device": "GM-800", "data": [[scene, ...]]}
    scene = {"memo": str, "paramSet": {"User_Scene%Common": [hex bytes], ...}}
A full device import has 150 scenes; list position = scene slot (1-based).
Scene name = User_Scene%Common bytes 3..18 (16 ASCII chars, space padded).

    gm800_tsl.py ls  FILE [--factory FILE]   slots, names, content hash, factory match, dups
    gm800_tsl.py diff A B                    slot-by-slot comparison (by content hash)
    gm800_tsl.py build PLAN.json [-o OUT]    assemble a liveset from a slot plan

Plan (paths relative to the plan file):
    {"name": "2026-11-17 target",
     "sources": {"dev": "backups/2026-11-17-device.tsl", "fac": "backups/2026-06-16-factory.tsl"},
     "slots": [{"slot": "1", "from": "dev:150", "rename": "MUTE"},
               {"slot": "2-31", "from": "dev:1-12,13,14"},
               {"slot": "51-150", "from": "fac:1-100"}],
     "fill": "dev:55"}          # empty slots get a copy of this scene (INIT)
Write the result to the unit: Librarian → Import → IMPORT FROM FILE, then
Export → EXPORT TO GM-800. Re-import from the unit and `diff` against the plan output.
"""
import argparse, copy, hashlib, json, os, sys

SLOTS = 150
NAME = slice(3, 19)


def load(path):
    d = json.load(open(os.path.expanduser(path)))
    if d.get("device") != "GM-800":
        sys.exit(f"{path}: device={d.get('device')!r}, expected GM-800")
    return d


def scenes(d):
    return d["data"][0]


def name(s):
    return bytes(int(h, 16) for h in s["paramSet"]["User_Scene%Common"][NAME]).decode("ascii", "replace").rstrip()


def chash(s):
    return hashlib.md5(json.dumps(s["paramSet"], sort_keys=True).encode()).hexdigest()[:8]


def set_name(s, new):
    if len(new) > 16 or not all(32 <= ord(c) < 127 for c in new):
        sys.exit(f"bad scene name {new!r}: max 16 ASCII chars")
    s["paramSet"]["User_Scene%Common"][NAME] = [f"{ord(c):02X}" for c in new.ljust(16)]


def rng(spec):
    out = []
    for part in str(spec).split(","):
        a, _, b = part.strip().partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def cmd_ls(a):
    sc = scenes(load(a.file))
    fac = {}
    if a.factory:
        fac = {chash(s): i for i, s in enumerate(scenes(load(a.factory))[:100], 1)}
    seen = {}
    for i, s in enumerate(sc, 1):
        h = chash(s)
        tag = f"=F{fac[h]}" if h in fac else ""
        dup = f"dup-of-{seen[h]}" if h in seen else ""
        seen.setdefault(h, i)
        print(f"{i:3}  {name(s):<16}  {h}  {tag:<5} {dup}")


def cmd_diff(a):
    A, B = scenes(load(a.a)), scenes(load(a.b))
    same = 0
    for i in range(max(len(A), len(B))):
        x = A[i] if i < len(A) else None
        y = B[i] if i < len(B) else None
        if x and y and chash(x) == chash(y):
            same += 1
            continue
        fx = f"{name(x)} {chash(x)}" if x else "—"
        fy = f"{name(y)} {chash(y)}" if y else "—"
        print(f"{i + 1:3}  {fx:<26} -> {fy}")
    print(f"identical: {same}/{max(len(A), len(B))}")


def cmd_build(a):
    plan = json.load(open(a.plan))
    base = os.path.dirname(os.path.abspath(a.plan))
    src = {k: scenes(load(os.path.join(base, p))) for k, p in plan["sources"].items()}

    def pick(ref):
        key, _, nums = ref.partition(":")
        return [src[key][n - 1] for n in rng(nums)]

    out = [None] * SLOTS
    for row in plan["slots"]:
        slots, picked = rng(row["slot"]), pick(row["from"])
        if len(slots) != len(picked):
            sys.exit(f"slot {row['slot']}: {len(slots)} slots but {len(picked)} scenes from {row['from']}")
        for n, s in zip(slots, picked):
            if out[n - 1] is not None:
                sys.exit(f"slot {n} assigned twice")
            s = copy.deepcopy(s)
            if row.get("rename"):
                set_name(s, row["rename"])
            out[n - 1] = s
    filler = pick(plan["fill"])[0]
    out = [s if s is not None else copy.deepcopy(filler) for s in out]
    res = {"name": plan["name"], "formatRev": "0000", "device": "GM-800", "data": [out]}
    dst = a.out or os.path.join(base, "livesets", plan["name"].replace(" ", "-") + ".tsl")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        json.dump(res, f, separators=(",", ":"))
    print(f"wrote {dst}  ({len(out)} scenes)")
    for i, s in enumerate(out, 1):
        print(f"{i:3}  {name(s)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ls"); p.add_argument("file"); p.add_argument("--factory"); p.set_defaults(fn=cmd_ls)
    p = sub.add_parser("diff"); p.add_argument("a"); p.add_argument("b"); p.set_defaults(fn=cmd_diff)
    p = sub.add_parser("build"); p.add_argument("plan"); p.add_argument("-o", "--out"); p.set_defaults(fn=cmd_build)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
