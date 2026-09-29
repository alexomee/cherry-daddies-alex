#!/usr/bin/env python3
"""Stage sheet — BIG. One full page per set, song name + notes only, font
auto-fitted as large as possible.

Reads:
  web/songs.json        -> ordered sets/songs
  web/data/dashboard.db -> per-song notes (verbatim)

Each set = one A4 landscape page. Rows split the page into equal heights; a
browser-side binary search blows up each cell's font until it just fits.

Usage: python3 tools/stage_sheet.py [--out PATH] [--portrait]
"""
import json, sqlite3, subprocess, html, re, sys, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(ROOT, "web", "songs.json")
DB = os.path.join(ROOT, "web", "data", "dashboard.db")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

OUT = os.path.join(ROOT, "stage-sheet.pdf")
if "--out" in sys.argv:
    OUT = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
LAND = "--portrait" not in sys.argv
PAGE_W, PAGE_H = (297, 210) if LAND else (210, 297)


def load_state():
    con = sqlite3.connect(DB)
    raw = con.execute("SELECT data FROM app_state").fetchone()[0]
    con.close()
    return json.loads(raw)


def note_for(songs, sid):
    rec = dict(songs.get(sid, {}))
    notes = (rec.get("notes") or "").strip()
    alt = "NOFOLDER:" + sid
    if alt in songs:  # merge stray duplicate (e.g. Мелом)
        an = (songs[alt].get("notes") or "").strip()
        if an and an not in notes:
            notes = (notes + "\n" + an).strip() if notes else an
    # tighten so font can be BIG: drop blank lines + consecutive dups
    out = []
    for ln in notes.splitlines():
        ln = ln.strip()
        if ln and (not out or ln != out[-1]):
            out.append(ln)
    return "\n".join(out)


def fmt_note(text):
    s = html.escape(text)
    s = re.sub(r"\bMUTE GUITAR\b", '<i class="mute">MUTE GUITAR</i>', s)
    s = re.sub(r"(?<!\">)(?<!MUTE )\bGUITAR(\s*32D)?\b",
               lambda m: '<i class="gtr">' + m.group(0) + "</i>", s)
    return s.replace("\n", "<br>")


def main():
    data = json.load(open(SONGS))
    songs = load_state().get("songs", {})

    pages = []
    for s in data["sets"]:
        rows = []
        for i, song in enumerate(s["songs"], 1):
            note = note_for(songs, song["sid"])
            note_html = fmt_note(note) if note else ""
            rows.append(
                '<div class="row">'
                f'<div class="cell num"><span>{i}</span></div>'
                f'<div class="cell name"><span>{html.escape(song["title"])}</span></div>'
                f'<div class="cell note"><span>{note_html}</span></div>'
                "</div>")
        pages.append(
            f'<section class="page"><div class="tag">{html.escape(s["name"])}</div>'
            f'<div class="rows">{"".join(rows)}</div></section>')

    doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
<style>
@page {{ size: A4 {'landscape' if LAND else 'portrait'}; margin: 0; }}
* {{ box-sizing: border-box; margin:0; padding:0;
     -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
html,body {{ font-family:-apple-system,"Helvetica Neue",Arial,sans-serif;
            color:#fff; background:#000; }}
.page {{ position:relative; width:{PAGE_W}mm; height:{PAGE_H}mm; padding:7mm 9mm;
        background:#000; color:#fff;
        display:flex; flex-direction:column; page-break-after:always; overflow:hidden; }}
.page:last-child {{ page-break-after:auto; }}
.tag {{ position:absolute; top:2.5mm; right:6mm; font-size:9px; font-weight:800;
       letter-spacing:2px; color:#bcc1cc; text-transform:uppercase; z-index:2; }}
.rows {{ flex:1; overflow:hidden; }}      /* fitter maximizes font until this fills */
.row {{ display:flex; align-items:center; padding:3px 0;
       border-bottom:1.5px solid #333; }}
.row:last-child {{ border-bottom:none; }}
.cell {{ display:flex; align-items:center; min-width:0; }}
.cell>span {{ display:block; width:100%; line-height:1.05; }}
.num {{ width:7%; }}
.num>span {{ font-weight:800; color:#b3b9c6; text-align:center; }}
.name {{ width:42%; padding-right:5mm; }}
.name>span {{ font-weight:800; letter-spacing:-0.5px; }}
.note {{ flex:1; border-left:1.5px solid #333; padding-left:5mm; }}
.note>span {{ font-weight:700; white-space:pre-wrap;
             font-family:"SF Mono",Menlo,ui-monospace,monospace; }}
.gtr {{ color:#2ecc40; font-style:normal; }}
.mute {{ color:#ff4136; font-style:normal; }}
</style></head><body>
{''.join(pages)}
<script>
// ONE font size for titles AND notes; rows grow with content; blow it up
// until the page is full. Notes end up exactly as big as the song titles.
function fitPage(p){{
  var box=p.querySelector('.rows');
  var spans=p.querySelectorAll('.name>span, .note>span, .num>span');
  var lo=8, hi=240, best=8;
  while(lo<=hi){{ var m=(lo+hi)>>1;
    spans.forEach(function(s){{ s.style.fontSize=m+'px'; }});
    if(box.scrollHeight<=box.clientHeight){{best=m;lo=m+1;}} else hi=m-1; }}
  spans.forEach(function(s){{ s.style.fontSize=best+'px'; }});
}}
function run(){{ document.querySelectorAll('.page').forEach(fitPage); document.title='ready'; }}
window.addEventListener('load', run);
</script>
</body></html>"""

    htmlpath = os.path.join(ROOT, "stage-sheet.html")
    open(htmlpath, "w").write(doc)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=10000",
                    f"--print-to-pdf={OUT}", "file://" + htmlpath],
                   check=True, capture_output=True)
    os.remove(htmlpath)
    print("PDF:", OUT, "·", len(data["sets"]), "sets ·",
          datetime.date.today().isoformat())


if __name__ == "__main__":
    main()
