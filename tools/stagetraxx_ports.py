#!/usr/bin/env python3
"""Stage Traxx output routing for audio interfaces whose ID depends on the USB port.

Stage Traxx keeps the bus -> output map per device UID (prefs `audio_busDeviceSettings`).
For the Rubix24 the UID carries the USB location ID, so the same box in another port (or
another socket of a hub) is a new device with no routing:

    AppleUSBAudioEngine:Roland:Rubix24:100000:1,2    Mac port drd0, direct
    AppleUSBAudioEngine:Roland:Rubix24:1100000:1,2   Mac port drd1, direct
    AppleUSBAudioEngine:Roland:Rubix24:130000:1,2    drd0 -> hub socket 3

This tool copies the known Rubix24 routing to every UID it can get: each root USB port of
the Mac (read from ioreg) direct, and through a one-level hub (sockets 1..HUB_SOCKETS).
Entries for devices not plugged in are harmless; Stage Traxx keeps them.

  tools/stagetraxx_ports.py                   # check: where is the Rubix, is it routed, is it the output
  tools/stagetraxx_ports.py --apply --quit --launch   # write routing for all ports (closes Stage Traxx)

FLOW 8 and POD Go are not affected: their UIDs carry a serial number, not the port.
"""
import argparse, datetime, json, os, plistlib, re, shutil, subprocess, sys, time

PREFS = os.path.expanduser(
    "~/Library/Containers/de.dikant.StageTraxx4/Data/Library/Preferences/de.dikant.StageTraxx4.plist")
KEY = "audio_busDeviceSettings"
UID_FMT = "AppleUSBAudioEngine:Roland:Rubix24:{loc:x}:1,2"
UID_RE = re.compile(r"^AppleUSBAudioEngine:Roland:Rubix24:([0-9a-f]+):1,2$", re.I)
PRODUCT = "Rubix24"
HUB_SOCKETS = 7   # current hub has 4; a few more cost nothing
APP = "Stage Traxx 4"


def ioreg():
    return subprocess.run(["ioreg", "-p", "IOService", "-l", "-w0"],
                          capture_output=True, text=True, check=True).stdout


def root_ports(text):
    """location IDs of the Mac's own USB 2.0 root ports (the Rubix is a USB 2.0 device)."""
    locs = {int(m.group(1), 16) for m in re.finditer(r"\+-o usb-drd\d+-port-hs@([0-9a-fA-F]+)\s", text)}
    if not locs:
        sys.exit("no usb-drd*-port-hs root ports in ioreg — unknown Mac layout, fix root_ports()")
    return sorted(locs)


def all_locations(roots):
    out = []
    for r in roots:
        out.append(r)
        out += [r | (s << 16) for s in range(1, HUB_SOCKETS + 1)]
    return out


def plugged_location(text):
    """locationID of the connected Rubix24, or None."""
    for block in re.split(r"\n(?=[ |]*\+-o )", text):
        if re.search(rf'"USB Product Name" = "{PRODUCT}"', block):
            m = re.search(r'"locationID" = (\d+)', block)
            if m:
                return int(m.group(1))
    return None


def coreaudio():
    """[(name, uid)] of CoreAudio devices + the default output's name — the real UIDs Stage Traxx keys on."""
    import ctypes as C
    ca = C.cdll.LoadLibrary("/System/Library/Frameworks/CoreAudio.framework/CoreAudio")
    cf = C.cdll.LoadLibrary("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    cf.CFStringGetCString.argtypes = [C.c_void_p, C.c_char_p, C.c_long, C.c_uint32]
    cf.CFRelease.argtypes = [C.c_void_p]

    class Addr(C.Structure):
        _fields_ = [("sel", C.c_uint32), ("scope", C.c_uint32), ("elem", C.c_uint32)]

    def cc(s):
        return int.from_bytes(s.encode(), "big")

    def get(obj, sel, buf, size):
        a, n = Addr(cc(sel), cc("glob"), 0), C.c_uint32(size)
        return ca.AudioObjectGetPropertyData(obj, C.byref(a), 0, None, C.byref(n), buf), n.value

    def string(obj, sel):
        ref = C.c_void_p()
        if get(obj, sel, C.byref(ref), C.sizeof(ref))[0] or not ref.value:
            return ""
        out = C.create_string_buffer(512)
        cf.CFStringGetCString(ref, out, 512, 0x08000100)
        cf.CFRelease(ref)
        return out.value.decode()

    ids = (C.c_uint32 * 64)()
    _, n = get(1, "dev#", ids, C.sizeof(ids))
    devs = [(string(i, "lnam"), string(i, "uid ")) for i in ids[:n // 4]]
    dflt = C.c_uint32()
    get(1, "dOut", C.byref(dflt), 4)
    return devs, string(dflt.value, "lnam")


def load():
    d = plistlib.load(open(PREFS, "rb"))
    return d, json.loads(d[KEY])


def template(buses):
    """bus -> routing of an already-configured Rubix24 UID; all known ones must agree."""
    known = sorted({u for b in buses for u in b["outputAssignments"] if UID_RE.match(u)})
    if not known:
        sys.exit("no Rubix24 routing in Stage Traxx prefs — set it once in Stage Traxx first")
    tpl = {}
    for b in buses:
        maps = [b["outputAssignments"][u] for u in known if u in b["outputAssignments"]]
        strip = [{k: v for k, v in m.items() if k not in ("uid",)} for m in maps]
        if any(s != strip[0] for s in strip):
            sys.exit(f"bus {b['busIndex'] + 1}: known Rubix24 UIDs disagree {known} — fix by hand")
        tpl[b["busIndex"]] = strip[0]
    return known, tpl


def app_running():
    return subprocess.run(["pgrep", "-f", f"{APP}.app/Contents/MacOS"], capture_output=True).returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write routing for every port (default: check only)")
    ap.add_argument("--quit", action="store_true", help="close Stage Traxx if it runs")
    ap.add_argument("--launch", action="store_true", help="start Stage Traxx after writing")
    a = ap.parse_args()

    text = ioreg()
    d, buses = load()
    known, tpl = template(buses)
    locs = all_locations(root_ports(text))
    want = [UID_FMT.format(loc=l) for l in locs]
    missing = [u for u in want if any(u not in b["outputAssignments"] for b in buses)]

    print("bus -> Rubix24 output:", ", ".join(f"{i + 1}->{tpl[i]['name'].replace('Rubix24 ', '')}"
                                             for i in sorted(tpl)[:4]))
    print(f"ports covered: {len(want) - len(missing)}/{len(want)}")
    devs, out = coreaudio()
    live = [u for n, u in devs if UID_RE.match(u)]
    loc = plugged_location(text)
    if not live:
        print("Rubix24: not connected")
    for uid in live:
        ok = all(uid in b["outputAssignments"] for b in buses)
        where = f" (USB {loc:#010x})" if loc is not None else ""
        print(f"Rubix24: {uid}{where} -> {'routed' if ok else 'NOT ROUTED: run --apply --quit --launch'}")
        if uid not in want:
            print(f"  ! real UID is not one of the {len(want)} computed — UID_FMT/locations are off, fix them")
    print(f"default output: {out}" + ("" if out == PRODUCT or not live else
                                      "  <- NOT Rubix24: pick it in Stage Traxx Settings -> Audio output device"))

    if not a.apply:
        if missing:
            print("\ncheck only — re-run with --apply to route all ports.")
        return
    if not missing:
        print("nothing to write.")
    else:
        if app_running():
            if not a.quit:
                sys.exit(f"{APP} is running — close it or pass --quit (it rewrites prefs on quit).")
            subprocess.run(["osascript", "-e", f'tell application "{APP}" to quit'])
            for _ in range(20):
                if not app_running():
                    break
                time.sleep(0.5)
            else:
                sys.exit(f"{APP} did not quit.")
            d, buses = load()   # re-read what it saved on quit
        bak = f"{PREFS}.bak-ports-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        shutil.copy2(PREFS, bak)
        for b in buses:
            for u in want:
                b["outputAssignments"].setdefault(u, dict(tpl[b["busIndex"]], uid=u))
        raw = json.dumps(buses, ensure_ascii=False, separators=(",", ":")).encode()
        subprocess.run(["defaults", "write", PREFS[:-len(".plist")], KEY, "-data", raw.hex()], check=True)
        _, back = load()
        if any(u not in b["outputAssignments"] for b in back for u in want):
            sys.exit(f"readback failed — restore {bak}")
        print(f"backup: {bak}\nwritten: {len(missing)} new port(s), {len(want)} total")
    if a.launch and not app_running():
        subprocess.run(["open", "-a", APP], check=True)
        print(f"{APP} launched")


if __name__ == "__main__":
    main()
