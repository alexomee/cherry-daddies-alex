#!/usr/bin/env python3
"""Add steve (drums) + tanya (lead vocals) to a song's mix.json `players`.

Targeted text insertion — does NOT reflow the file (preserves cue formatting).
Merges into an existing one-line `players` object, or inserts a new `players`
line before `cues` if absent. Idempotent (skips if steve already present).

Usage:  python3 tools/add_practice_players.py "<folder>" ["<folder>" ...]
        python3 tools/add_practice_players.py --all
"""
import os
import re
import sys
import json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs")

AUDIO = (".m4a", ".mp3", ".wav", ".aif", ".aiff")
DRUM = re.compile(r"drum", re.I)
LEAD = re.compile(r"lead.?vocal", re.I)


def stems_of(folder):
    out = []
    for f in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, f)) and os.path.splitext(f)[1].lower() in AUDIO:
            out.append(os.path.splitext(f)[0])
    return out


def roles(folder):
    stems = stems_of(folder)
    drums = [s for s in stems if DRUM.search(s)]
    leads = [s for s in stems if LEAD.search(s) or s == "vocals"]
    return drums, leads


def edit(folder):
    mj = os.path.join(folder, "mix.json")
    if not os.path.isfile(mj):
        return f"SKIP (no mix.json): {os.path.basename(folder)}"
    drums, leads = roles(folder)
    if not drums or not leads:
        return f"SKIP (drums={drums} leads={leads}): {os.path.basename(folder)}"
    text = open(mj, encoding="utf-8").read()
    if re.search(r'"steve"\s*:', text):
        return f"already done: {os.path.basename(folder)}"

    steve = json.dumps(drums, ensure_ascii=False)
    tanya = json.dumps(leads, ensure_ascii=False)
    inject = f'"steve": {steve}, "tanya": {tanya}'

    m = re.search(r'"players"\s*:\s*\{', text)
    if m:
        # insert right after the opening brace of the existing players object
        pos = m.end()
        rest = text[pos:].lstrip()
        sep = "" if rest.startswith("}") else ", "
        new = text[:pos] + inject + sep + text[pos:]
    else:
        # insert a new players line before "cues"
        c = re.search(r'^(\s*)"cues"\s*:', text, re.M)
        if not c:
            return f"SKIP (no players and no cues anchor): {os.path.basename(folder)}"
        indent = c.group(1)
        line = f'{indent}"players": {{{inject}}},\n'
        new = text[:c.start()] + line + text[c.start():]

    # validate it still parses
    try:
        json.loads(new)
    except Exception as e:
        return f"FAIL (would break JSON): {os.path.basename(folder)} — {e}"
    open(mj, "w", encoding="utf-8").write(new)
    return f"OK {os.path.basename(folder)} -> steve={drums} tanya={leads}"


def main(argv):
    if argv == ["--all"]:
        targets = [os.path.join(SONGS, d) for d in sorted(os.listdir(SONGS))
                   if os.path.isdir(os.path.join(SONGS, d))]
    else:
        targets = [os.path.join(SONGS, d) for d in argv]
    for t in targets:
        print(edit(t))


if __name__ == "__main__":
    main(sys.argv[1:])
