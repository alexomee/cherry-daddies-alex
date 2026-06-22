#!/usr/bin/env python3
"""Build the vocalist lyric-review gallery (index.html) for the R2 temp package.

One sticky <video> player + a tap-list of every setlist song (from songs.tsv),
each pointing at <base>/NN.mp4 — the make_review_video.py clips. The vocalist
watches on her phone and cites edits by "song + M:SS".

  build_review_site.py cherry-lyric-review-2026-06-22 [/tmp/review_pkg/index.html]

Then upload index.html + the NN.mp4 review clips to temp/<folder>/ on R2
(releases.agentiqa.com). Versioned folder per round (Cloudflare edge-cache: a
fresh key is served fresh; overwriting an old key serves stale — see CLAUDE.md).
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "songs.tsv")
HOST = "https://releases.agentiqa.com/temp"

TEMPLATE = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cherry Daddies - Lyric Review</title>
<style>
 *{box-sizing:border-box}
 body{margin:0;background:#0e0e0e;color:#eee;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
 video{width:100%;max-height:56vh;background:#000;position:sticky;top:0;z-index:10;display:block}
 header{padding:14px 16px 4px}
 h1{font-size:1.15rem;margin:.1em 0;color:#f5c518}
 .ver{color:#6a6a6a;font-size:.72rem;font-weight:400}
 .hint{color:#9aa;font-size:.82rem;line-height:1.45}
 ol{list-style:none;margin:8px 0 40px;padding:0}
 li{border-bottom:1px solid #1d1d1d}
 a{display:flex;gap:12px;padding:13px 16px;color:#eee;text-decoration:none;align-items:center}
 a:active,a.active{background:#16263f}
 .n{color:#f5c518;font-weight:700;min-width:1.7em;text-align:right;font-variant-numeric:tabular-nums}
 .t{flex:1;font-size:1.02rem}
 .now{color:#7fd1ff;font-size:.8rem}
</style></head><body>
<video id="p" controls playsinline preload="metadata"></video>
<header>
 <h1>Cherry Daddies - Lyric Review <span class="ver">{ver}</span></h1>
 <div class="hint">Tap a song to play. Sing the <b>bright two lines</b> (top &rarr; bottom); the <b>grey pair below</b> previews what's next. Clock top-right.<br>
 To request a change, message me the <b>song + M:SS timecode</b> (e.g. "Beverly Hills 3:14 - line should be ...").</div>
 <div class="now" id="now"></div>
</header>
<ol id="list"></ol>
<script>
const songs={songs};
const p=document.getElementById('p'),L=document.getElementById('list'),now=document.getElementById('now');
songs.forEach(s=>{
 const li=document.createElement('li'),a=document.createElement('a');a.href='#';
 a.innerHTML='<span class="n">'+s.n+'</span><span class="t">'+s.t+'</span>';
 a.onclick=e=>{e.preventDefault();
  document.querySelectorAll('#list a').forEach(x=>x.classList.remove('active'));
  a.classList.add('active');now.textContent='Now: '+s.n+' '+s.t;
  p.src=s.u;p.play();window.scrollTo({top:0,behavior:'smooth'});};
 li.appendChild(a);L.appendChild(li);
});
</script></body></html>"""


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: build_review_site.py <folder> [out.html]")
    folder = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/review_pkg/index.html"
    base = f"{HOST}/{folder}"
    ver = folder.rsplit("review-", 1)[-1] if "review-" in folder else folder
    rows = sorted(csv.DictReader(open(TSV, encoding="utf-8"), delimiter="\t"),
                  key=lambda r: int(r["clip"]))
    songs = [{"n": r["clip"], "t": r["song"], "u": f"{base}/{r['clip']}.mp4"} for r in rows]
    html = TEMPLATE.replace("{songs}", json.dumps(songs, ensure_ascii=False)).replace("{ver}", ver)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out}  ({len(songs)} songs, base {base})")


if __name__ == "__main__":
    main()
