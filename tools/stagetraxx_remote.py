#!/usr/bin/env python3
"""Stage Traxx remote actions for the Ampero Control foot controller.

Stage Traxx 4 keeps key/MIDI -> action assignments in its prefs, key `remote_triggerMappings`
(JSON as Data, not in iCloud). A MIDI CC trigger looks like (learned in the UI 2026-11-20):

    {"id": "<UUID>", "isEnabled": true, "action": "nextSong",
     "trigger": {"midiCC": {"channel": 16, "controller": 23, "value": 127}}}

`channel` is 1-based. One CC may carry several entries: Stage Traxx gets one action per entry.

Ampero Control (Hotone EC-4), bank 00, every switch Mode Single, CH 16, CC, value 127,
Output To USB. Programmed only from the Ampero Control app (Bluetooth); USB is plain MIDI.

  tools/stagetraxx_remote.py                       # show what is assigned vs wanted
  tools/stagetraxx_remote.py --apply --quit --launch

Keyboard assignments are kept; every MIDI CC entry on CHANNEL is replaced by FOOTSWITCHES.
"""
import argparse, datetime, json, os, plistlib, shutil, subprocess, sys, time, uuid

PREFS = os.path.expanduser(
    "~/Library/Containers/de.dikant.StageTraxx4/Data/Library/Preferences/de.dikant.StageTraxx4.plist")
DOMAIN = "de.dikant.StageTraxx4"
KEY = "remote_triggerMappings"
APP = "Stage Traxx 4"
CHANNEL = 16
VALUE = 127

# footswitch -> (CC, Stage Traxx actions in order). Action raw values: see wiki/pipelines/stagetraxx-rig.md
FOOTSWITCHES = {
    "FS1 стоп и в начало":   (20, ["stopPlayback", "rewind"]),
    "FS2 предыдущая песня":  (21, ["selectionUp", "triggerSelection"]),
    "FS3 пауза / старт":     (22, ["startStop"]),
    "FS4 следующая песня":   (23, ["nextSong"]),
}


def load():
    """Current mappings (via cfprefsd, so a running Stage Traxx's latest writes are seen)."""
    raw = subprocess.run(["defaults", "export", DOMAIN, "-"], capture_output=True, check=True).stdout
    data = plistlib.loads(raw).get(KEY)
    return json.loads(data) if data else []


def is_ours(m):
    cc = m.get("trigger", {}).get("midiCC")
    return cc is not None and cc.get("channel") == CHANNEL


def wanted():
    out = []
    for _, (cc, actions) in FOOTSWITCHES.items():
        for a in actions:
            out.append({"id": str(uuid.uuid4()).upper(), "isEnabled": True, "action": a,
                        "trigger": {"midiCC": {"channel": CHANNEL, "controller": cc, "value": VALUE}}})
    return out


def sig(m):
    cc = m["trigger"]["midiCC"]
    return (cc["controller"], cc.get("value"), m["action"], m.get("isEnabled", True))


def app_running():
    return subprocess.run(["pgrep", "-f", f"{APP}.app/Contents/MacOS"], capture_output=True).returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the footswitch assignments")
    ap.add_argument("--quit", action="store_true", help="close Stage Traxx if it runs")
    ap.add_argument("--launch", action="store_true", help="start Stage Traxx after writing")
    a = ap.parse_args()

    cur = load()
    want = wanted()
    have = sorted(sig(m) for m in cur if is_ours(m))
    need = sorted(sig(m) for m in want)
    for name, (cc, actions) in FOOTSWITCHES.items():
        got = [m["action"] for m in cur if is_ours(m) and m["trigger"]["midiCC"]["controller"] == cc]
        mark = "ok" if got == actions else f"now {got or 'nothing'}"
        print(f"{name:24} CC{cc} ch{CHANNEL} -> {' + '.join(actions):32} {mark}")
    other = [m for m in cur if not is_ours(m)]
    print("kept:", ", ".join(f"{m['action']}" for m in other) or "nothing")

    if not a.apply:
        if have != need:
            print("\ncheck only — re-run with --apply --quit --launch.")
        return
    if have == need:
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
            cur = load()
            other = [m for m in cur if not is_ours(m)]
        bak = f"{PREFS}.bak-remote-{datetime.datetime.now():%Y%m%d-%H%M%S}"
        shutil.copy2(PREFS, bak)
        new = other + want
        raw = json.dumps(new, ensure_ascii=False, separators=(",", ":")).encode()
        subprocess.run(["defaults", "write", DOMAIN, KEY, "-data", raw.hex()], check=True)
        back = load()
        if sorted(sig(m) for m in back if is_ours(m)) != need or len(back) != len(new):
            sys.exit(f"readback failed — restore {bak}")
        print(f"backup: {bak}\nwritten: {len(want)} MIDI entries, {len(other)} kept")
    if a.launch and not app_running():
        subprocess.run(["open", "-a", APP], check=True)
        print(f"{APP} launched")


if __name__ == "__main__":
    main()
