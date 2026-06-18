#!/usr/bin/env python3
"""Setlist data exporter.

Reads each song's mix.json and emits web/songs.json — the read-only reference
data (setlist order + per-song Cues / bass / pb-other display fields) that the
web dashboard (web/index.html) renders. User-editable data (todos, notes) lives
in the backend DB, not here.

Run:  python3 tools/setlist_dashboard.py
Out:  web/songs.json
"""
import json
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SONGS = REPO / "music" / "songs"
OUT = REPO / "web" / "songs.json"

# Setlist: display title/artist from here; `folder` = mix.json source (None => no data yet).
SETS = [
    {
        "name": "СЕТ 1",
        "subtitle": "Мировые танцевальные хиты",
        "cls": "set1",
        "songs": [
            ("Better Off Alone", "Alice Deejay", "Alice Deejay - Better Off Alone"),
            ("Around the World", "ATC", "A Touch of Class - Around the World (La La La La La)"),
            ("Whenever, Wherever", "Shakira", "Shakira - Whenever, Wherever"),
            ("Infinity 2008", "Guru Josh Project", "Guru Josh - Infinity 2008"),
            ("Mr. Saxobeat", "Alexandra Stan", "Alexandra Stan - Mr. Saxobeat"),
            ("Destination Calabria", "Alex Gaudino", "Alex Gaudino - Destination Calabria"),
            ("Adventure of a Lifetime", "Coldplay", "Coldplay - Adventure of a Lifetime"),
            ("Blinding Lights", "The Weeknd", "The Weeknd - Blinding Lights"),
            ("No Stress", "Laurent Wolf", "Laurent Wolf & Eric Carter - No Stress"),
            ("Freed From Desire", "Gala", "Gala - Freed from Desire"),
            ("Uptown Funk", "Mark Ronson", "Bruno Mars & Mark Ronson - Uptown Funk"),
        ],
    },
    {
        "name": "СЕТ 2",
        "subtitle": "",
        "cls": "set2",
        "songs": [
            ("Солнышко", "Демо", "Demo - Solnyshko"),
            ("Про красивую жизнь", "Банд'Эрос", "Band'Eros - Pro krasivuju zhizn'"),
            ("Мало тебя", "SEREBRO", "SEREBRO - Malo tebya"),
            ("Я устал", "Quest Pistols", "Quest Pistols - Я устал"),
            ("Now You're Gone", "Basshunter", "Basshunter - Now You're Gone"),
            ("S&M", "Rihanna", "Rihanna - S&M"),
            ("Beverly Hills", "Zivert", "Beverly Hills"),
            ("We Found Love", "Rihanna", "Rihanna & Calvin Harris - We Found Love"),
            ("Everytime We Touch", "Cascada", "Cascada - Everytime We Touch"),
            ("Heads Will Roll", "Yeah Yeah Yeahs", "Yeah Yeah Yeahs - Heads Will Roll"),
            ("I Love It", "Icona Pop", "Icona Pop & Charli XCX - I Love It"),
        ],
    },
    {
        "name": "на бис",
        "subtitle": "",
        "cls": "bis",
        "songs": [
            ("Мелом", "Пропаганда", None),
            ("Я сошла с ума", "ТАТУ", "t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)"),
        ],
    },
]

# Manual bass-player assignment for songs WITHOUT pb-bass (keyed by song folder / sid).
# Songs WITH pb-bass render "playback (<stem>)" automatically and ignore this.
BASS_ASSIGN = {
    # СЕТ 1
    "Alice Deejay - Better Off Alone": "Roma",
    "Guru Josh - Infinity 2008": "Roma",
    "Coldplay - Adventure of a Lifetime": "Roma (real bass-guitar)",
    "Laurent Wolf & Eric Carter - No Stress": "Alex",
    "Bruno Mars & Mark Ronson - Uptown Funk": "Roma (real bass-guitar)",
    # СЕТ 2
    "Demo - Solnyshko": "Alex",
    "Band'Eros - Pro krasivuju zhizn'": "Roma",
    "Quest Pistols - Я устал": "Roma",
    "Basshunter - Now You're Gone": "Roma",
    "Rihanna - S&M": "Alex",
    "Beverly Hills": "Alex",
    "Cascada - Everytime We Touch": "Roma",
}


def clean_stem(name: str) -> str:
    """05_Synth_Bass -> 'Synth Bass'; 10_Saxophone_(reverse) -> 'Saxophone (reverse)'."""
    import re
    s = re.sub(r"^\d+_", "", name)
    return s.replace("_", " ").strip()


def load_mix(folder):
    if not folder:
        return None
    p = SONGS / folder / "mix.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def group_items(group):
    """pb-bass / pb-other value -> (kind, [labels]). kind in stems|layers|None."""
    if not group:
        return (None, [])
    if isinstance(group, dict):
        if group.get("layers"):
            out = []
            for layer in group["layers"]:
                if isinstance(layer, str):
                    out.append(layer)
                elif isinstance(layer, dict):
                    out.append(layer.get("file", "?"))
            return ("layers", out)
        if group.get("stems"):
            return ("stems", [clean_stem(s) for s in group["stems"]])
    return (None, [])


def song_id(title, folder):
    """Stable key used by the backend DB. Folder if present, else marker by title."""
    return folder if folder else "NOFOLDER:" + title


def build_data():
    sets = []
    counts = {"total": 0, "data": 0, "cues": 0, "playback": 0, "other": 0}
    for st in SETS:
        songs = []
        for title, artist, folder in st["songs"]:
            counts["total"] += 1
            sid = song_id(title, folder)
            mix = load_mix(folder)
            if mix is None:
                songs.append({"sid": sid, "title": title, "artist": artist, "hasData": False})
                continue
            counts["data"] += 1

            cues = mix.get("cues") or []
            if cues:
                counts["cues"] += 1

            bkind, bitems = group_items(mix.get("pb-bass"))
            if bkind in ("layers", "stems"):
                counts["playback"] += 1
                bass = {"kind": "playback", "label": ", ".join(bitems)}
            else:
                bv = BASS_ASSIGN.get(sid, "")
                bass = {"kind": "assign", "who": bv} if bv else {"kind": "none"}

            okind, oitems = group_items(mix.get("pb-other"))
            if okind == "layers":
                counts["other"] += 1
                other = {"kind": "layers", "items": oitems}
            elif okind == "stems":
                counts["other"] += 1
                other = {"kind": "stems", "items": oitems}
            else:
                other = {"kind": "none"}

            songs.append({
                "sid": sid, "title": title, "artist": artist, "hasData": True,
                "cues": {"ready": bool(cues), "count": len(cues)},
                "bass": bass, "other": other,
            })
        sets.append({
            "name": st["name"], "subtitle": st["subtitle"], "cls": st["cls"], "songs": songs,
        })
    return {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "counts": counts,
        "sets": sets,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = build_data()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    c = data["counts"]
    print(f"wrote {OUT}")
    print(f"  {c['data']}/{c['total']} songs with data · {c['cues']} cues · "
          f"{c['playback']} bass playback · {c['other']} pb-other")


if __name__ == "__main__":
    main()
