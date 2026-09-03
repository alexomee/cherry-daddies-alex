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
import hashlib
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SONGS = REPO / "music" / "songs"
OUT = REPO / "web" / "songs.json"
HASH_CACHE = REPO / "web" / ".mix-hashes.json"   # {path: {sig:[size,mtime_ns], hash}}; local, gitignored

_hcache = None


def _load_hcache():
    global _hcache
    if _hcache is None:
        try:
            _hcache = json.loads(HASH_CACHE.read_text())
        except Exception:
            _hcache = {}
    return _hcache


def mix_version(path: Path):
    """Content hash (10 hex) of a mix file for cache-busting the R2 URL.
    Cached by (size, mtime) so re-hashing only happens when the file changes."""
    c = _load_hcache()
    try:
        stt = path.stat()
    except FileNotFoundError:
        return None
    key = str(path)
    sig = [stt.st_size, int(stt.st_mtime_ns)]
    ent = c.get(key)
    if ent and ent.get("sig") == sig:
        return ent["hash"]
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()[:10]
    c[key] = {"sig": sig, "hash": digest}
    return digest


def _save_hcache():
    if _hcache is not None:
        HASH_CACHE.write_text(json.dumps(_hcache))

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
            ("Мелом", "Пропаганда", "Мелом"),
            ("Я сошла с ума", "ТАТУ", "t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)"),
        ],
    },
    {
        "name": "НА ПРОБУ",
        "subtitle": "новые песни — черновые авто-рендеры",
        "cls": "tryout",
        "songs": [
            ("Мама Люба", "SEREBRO", "Мама Люба"),
            ("Кислотный DJ", "Мари Краймбрери", "Кислотный DJ"),
            ("Такая любовь", "", "Такая любовь"),
            ("Солнце", "Елена Терлеева", "Елена Терлеева - Солнце"),
            ("Беги от меня", "", "Беги от меня"),
            ("Медведица", "Мумий Тролль", "Мумий Тролль - Медведица"),
            ("Кукла колдуна", "Король и Шут", "Король и Шут - Кукла колдуна"),
            ("Ту-лу-ла", "Чичерина", "Чичерина - Ту-лу-ла"),
            ("Rock & Roll Queen", "The Subways", "The Subways - Rock & Roll Queen"),
        ],
    },
    {
        "name": "Архив",
        "subtitle": "снято с программы",
        "cls": "archived",
        "songs": [
            ("Eva 2.0", "", "Eva 2.0"),
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
    "Cascada - Everytime We Touch": "Roma",
    # на бис
    "Мелом": "Roma",  # roma plays bass live (players.roma = ['bass'])
    # tryout
    "Кислотный DJ": "Alex",  # alex plays bass live (pb-bass removed)
    "Eva 2.0": "Alex",       # alex plays bass live (pb-bass removed)
    "Елена Терлеева - Солнце": "Roma (real bass-guitar)",  # pb-bass removed, roma plays real bass
}


def mix_file(p: str) -> str:
    """dashboard mix id -> file in auto-render/. 'all' = full mix, 'drums' = the pb-drums
    playback track (rehearsal without the drummer), anything else = that player's practice mix."""
    return {"all": "cue_preview.mp3", "drums": "pb-drums.mp3"}.get(p, f"practice-{p}.mp3")


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


def slug_of(sid):
    """Stable ascii slug for R2 audio keys / URLs. Unguessable (mild privacy)."""
    import hashlib
    return hashlib.sha1(sid.encode("utf-8")).hexdigest()[:12]


def build_data():
    sets = []
    counts = {"total": 0, "data": 0, "cues": 0, "playback": 0, "other": 0, "practice": 0}
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
            # cue list for the dashboard: time (abs_sec, render/player timeline) + text + bar.
            # "snap" (render snap_sec = 1 bar before the cue's first spoken word) is the seek target
            # so clicking a cue in the web player replays the WHOLE cue, not just its event beat.
            cue_list = [
                {"t": round(c["abs_sec"], 3), "text": c.get("text", ""), "bar": c.get("bar"),
                 **({"snap": round(c["snap_sec"], 3)} if isinstance(c.get("snap_sec"), (int, float)) else {})}
                for c in cues if isinstance(c.get("abs_sec"), (int, float))
            ]

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

            # Mixes available in auto-render/: "all" = full mix (cue_preview.mp3), "drums" =
            # the pb-drums playback track (kit alone + click + cues, for rehearsals without the
            # drummer), then per-player practice mixes (practice-<player>.mp3 = all minus theirs).
            ar = SONGS / folder / "auto-render"
            practice = []
            if (ar / "cue_preview.mp3").is_file():
                practice.append("all")
            if (ar / "pb-drums.mp3").is_file():
                practice.append("drums")
            practice += [
                p for p in ("alex", "steve", "roma", "tanya", "trio")
                if (ar / f"practice-{p}.mp3").is_file()
            ]
            if any(p not in ("all", "drums") for p in practice):
                counts["practice"] += 1

            # content-hash version per mix (for ?v= cache-busting on R2)
            versions = {}
            for p in practice:
                v = mix_version(ar / mix_file(p))
                if v:
                    versions[p] = v

            songs.append({
                "sid": sid, "slug": slug_of(sid), "title": title, "artist": artist, "hasData": True,
                "cues": {"ready": bool(cues), "count": len(cues), "list": cue_list},
                "bass": bass, "other": other, "practice": practice, "versions": versions,
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
    _save_hcache()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    c = data["counts"]
    print(f"wrote {OUT}")
    print(f"  {c['data']}/{c['total']} songs with data · {c['cues']} cues · "
          f"{c['playback']} bass playback · {c['other']} pb-other · "
          f"{c['practice']} with practice mix")


if __name__ == "__main__":
    main()
