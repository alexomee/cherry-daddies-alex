#!/usr/bin/env python3
"""Assign Roma's live parts = every synth/key stem NOT in playback and NOT played by Alex.

Reproduces the existing manual roma assignments exactly (verified), and fills in
songs where roma is currently unset. Targeted text insertion into the existing
one-line `players` object (no file reflow). Skips songs that already have roma
or where there is no live synth for him.

Usage:  python3 tools/set_roma_players.py            # dry-run (prints plan)
        python3 tools/set_roma_players.py --apply     # write + print changed list
"""
import os
import re
import sys
import json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs")
AUDIO = (".m4a", ".mp3", ".wav", ".aif", ".aiff")
MOISES = set("bass drums keys other guitars vocals metronome".split())
SYNTH = re.compile(r"synth|organ|piano|keys|arp|pad|string|vibe|bell|rhodes|wurl|mellotron|keyboard", re.I)
NOTSYNTH = re.compile(r"bass|lead.?vocal|back.*vocal|^vocals$|drum|percussion|click|metronome|guitar|charango|saxophone|flute|brass|noise|sound_effect|sample", re.I)


def stems_of(folder):
    return [os.path.splitext(f)[0] for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f)) and os.path.splitext(f)[1].lower() in AUDIO]


def is_synthkey(name, moises):
    if moises:
        return name in ("keys", "other")
    if NOTSYNTH.search(name):
        return False
    return bool(SYNTH.search(name))


def roma_for(folder, mix):
    stems = stems_of(folder)
    moises = bool(set(stems) & MOISES)
    pb = []
    for g in ("pb-other", "pb-bass"):
        pb += (mix.get(g) or {}).get("stems", [])
    alex = set((mix.get("players") or {}).get("alex") or [])
    # keep mix.json stem order
    return [s for s in stems if is_synthkey(s, moises) and s not in pb and s not in alex]


def main(apply):
    changed = []
    for d in sorted(os.listdir(SONGS)):
        folder = os.path.join(SONGS, d)
        mj = os.path.join(folder, "mix.json")
        if not os.path.isfile(mj):
            continue
        mix = json.loads(open(mj, encoding="utf-8").read())
        players = mix.get("players") or {}
        if players.get("roma") is not None:
            print(f"keep   {d}  (roma already: {players['roma']})")
            continue
        roma = roma_for(folder, mix)
        if not roma:
            print(f"skip   {d}  (no live synth for roma)")
            continue
        print(f"ADD    {d}  -> roma={roma}")
        changed.append(d)
        if apply:
            text = open(mj, encoding="utf-8").read()
            inject = f'"roma": {json.dumps(roma, ensure_ascii=False)}'
            m = re.search(r'"players"\s*:\s*\{', text)
            if m:
                pos = m.end()
                rest = text[pos:].lstrip()
                sep = "" if rest.startswith("}") else ", "
                new = text[:pos] + inject + sep + text[pos:]
            else:
                c = re.search(r'^(\s*)"cues"\s*:', text, re.M)
                indent = c.group(1)
                new = text[:c.start()] + f'{indent}"players": {{{inject}}},\n' + text[c.start():]
            json.loads(new)  # validate
            open(mj, "w", encoding="utf-8").write(new)
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {len(changed)} songs -> {changed}")
    return changed


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
