#!/usr/bin/env python3
"""DERIVED status of every song's pipeline stage — from real artifacts, never hand-typed.

Scans music/songs/*/ (stems, structure, cues.json, cue render, logic-render/ bounces),
~/Music/Logic/*.logicx (manual Logic cues), and the Stage Traxx 4 library (what's actually
loaded). Prints the true per-song stage so a fresh session never trusts a stale board.

  stages:  ❌ none → 🧩 stems → 🎙 cue → 🎚 bounced → ✅ in StageTraxx

Usage:
    jamzone_status.py              # print the table
    jamzone_status.py --write      # also regenerate the status block in music/SONGS.md
"""
import os, sys, glob, json, re, sqlite3

SONGS = os.path.expanduser("~/projects/cherry-daddies/music/songs")
LOGIC = os.path.expanduser("~/Music/Logic")
ST_DB = os.path.expanduser("~/Library/Containers/de.dikant.StageTraxx4/Data/"
                           "Library/Application Support/StageTraxx4/music_library.sqlite")
BOARD = os.path.expanduser("~/projects/cherry-daddies/music/SONGS.md")

def st_loaded():
    out = {}
    try:
        con = sqlite3.connect(f"file:{ST_DB}?mode=ro", uri=True)
        for title, n in con.execute("SELECT s.title, count(t.id) FROM song s "
                                     "LEFT JOIN track t ON t.songID=s.id GROUP BY s.id"):
            out[title.lower()] = n
        con.close()
    except Exception: pass
    return out

def logic_projects():
    return [os.path.splitext(os.path.basename(p))[0].lower()
            for p in glob.glob(os.path.join(LOGIC, "*.logicx"))]

def scan():
    st = st_loaded(); logics = logic_projects(); rows = []
    for d in sorted(glob.glob(os.path.join(SONGS, "*"))):
        if not os.path.isdir(d): continue
        base = os.path.basename(d); title = base.split(" - ")[-1]
        stems = len(glob.glob(os.path.join(d, "[0-9][0-9]_*.m4a")))
        ext   = os.path.isdir(os.path.join(d, "aligned"))
        struct = os.path.exists(os.path.join(d, "structure.txt"))
        try: ncues = len(json.load(open(os.path.join(d, "cues.json"))))
        except Exception: ncues = 0
        bounces = sorted({os.path.basename(p)[:-4]
                          for sub, ext in (("auto-render", "*.aif"), ("logic-render", "*.mp3"))
                          for p in glob.glob(os.path.join(d, sub, ext))})
        has_core = any(b.startswith("click") for b in bounces) and \
                   any(b.startswith("cue") for b in bounces) and \
                   any(b.startswith("pb-other") for b in bounces)
        in_st = st.get(title.lower())
        logic = any(title.lower() in lp or lp in title.lower() for lp in logics)
        # highest stage reached
        if in_st:                 stage = "✅ StageTraxx"
        elif has_core:            stage = "🎚 bounced"
        elif ncues or logic:      stage = "🎙 cue"
        elif stems or ext:        stage = "🧩 stems"
        else:                     stage = "❌ none"
        rows.append(dict(song=base, stems=(stems or ("ext" if ext else 0)), struct=struct,
                         cues=ncues, logic=logic, bounces=bounces, in_st=in_st, stage=stage))
    return rows

def table(rows):
    out = [f"{'song':44} {'stage':14} stems str cue logic  bounce / ST"]
    order = {"✅ StageTraxx":0,"🎚 bounced":1,"🎙 cue":2,"🧩 stems":3,"❌ none":4}
    for r in sorted(rows, key=lambda r: (order[r["stage"]], r["song"])):
        b = ",".join(x.replace("pb-","") for x in r["bounces"]) or "—"
        st = f"  ▶ST:{r['in_st']}tr" if r["in_st"] else ""
        out.append(f"{r['song'][:44]:44} {r['stage']:12} {str(r['stems']):>5} "
                   f"{'Y' if r['struct'] else '-':>3} {r['cues'] or '-':>3} {'Y' if r['logic'] else '-':>5}  {b}{st}")
    return "\n".join(out)

def main():
    rows = scan()
    counts = {}
    for r in rows: counts[r["stage"]] = counts.get(r["stage"], 0) + 1
    summary = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
    print(table(rows)); print("\n" + summary)
    if "--write" in sys.argv and os.path.exists(BOARD):
        txt = open(BOARD).read()
        block = ("<!-- STATUS:auto (jamzone_status.py --write) — НЕ редактировать руками -->\n"
                 f"_Сгенерировано из артефактов. Сводка: {summary}_\n\n```\n{table(rows)}\n```\n"
                 "<!-- /STATUS:auto -->")
        if "<!-- STATUS:auto" in txt:
            txt = re.sub(r"<!-- STATUS:auto.*?<!-- /STATUS:auto -->", block, txt, flags=re.S)
        else:
            txt = block + "\n\n" + txt
        open(BOARD, "w").write(txt); print("\n→ updated SONGS.md status block")

if __name__ == "__main__":
    main()
