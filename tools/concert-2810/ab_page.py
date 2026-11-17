#!/usr/bin/env python3
"""Build analysis/concert-2810/index.html — A/B listening page from results.json."""
import json, os, html
OUT = "/Users/alex/projects/cherry-daddies/analysis/concert-2810"
R = json.load(open(OUT + "/results.json"))
ORDER = ["Кукла колдуна", "Pretty Fly", "Медведица", "Ту-лу-ла", "Солнце", "Кислотный DJ", "Beverly Hills", "Про красивую жизнь",
         "Я устал", "Мало тебя", "Беги от меня (бис)", "Солнышко", "Медляк", "Такая любовь (S1)", "Такая любовь (бис)"]
VERDICT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "verdicts.json"))) if os.path.exists(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "verdicts.json")) else {}

def chips(items, cls):
    out = []
    for it in items:
        t = it[0].split(" ")[0]; extra = ""
        if len(it) > 2 and it[2]: extra = " · уже в плейбеке: " + ", ".join(x.split(":", 1)[1] for x in it[2])
        out.append(f'<button class="chip {cls}" data-t="{t}">{html.escape(it[0])} · {it[1]} т.{html.escape(extra)}</button>')
    return "".join(out)

cards = []
for take in ORDER:
    r = R.get(take)
    if not r: continue
    slug = os.path.basename(r["files"]); t = r["timing"]; q = r["quality"]; n = r["notes"]; c = r["coverage"]
    part = "бас" if r["kind"] == "bass" else "клавиши"
    def tline(x):
        return "—" if not x else f'задержка {x["latency_ms"]:+.0f} мс, разброс {x["spread_ms"]:.0f} мс, ровно {x["tight_pct"]}%'
    loose = [(w[0], f"{w[1]:+d} мс / ±{w[2]}") for w in (t["concert"] or {}).get("loose_4bar", [])] if t["concert"] else []
    v = VERDICT.get(take, {})
    A = "Слой Ромы" if "Такая любовь" in take else "Стем"
    cards.append(f"""
<section class="card" data-slug="{slug}">
  <header><h2>{html.escape(take)}</h2><span class="tag {r['kind']}">{part}</span>{f'<span class="verdict v-{v.get("cls","")}">{html.escape(v.get("text",""))}</span>' if v else ''}</header>
  {f'<p class="note">{html.escape(v.get("note",""))}</p>' if v.get("note") else ''}
  <div class="player">
    <div class="seg" role="group">
      <button class="src on" data-src="ab-stem">{A} в миксе</button><button class="src" data-src="ab-concert">Концерт в миксе</button>
      <button class="src" data-src="solo-stem">{A} соло</button><button class="src" data-src="solo-concert">Концерт соло</button>
    </div>
    <button class="play">▶</button><input class="pos" type="range" min="0" max="1000" value="0"><span class="time">0:00</span>
  </div>
  <dl class="m">
    <dt>Ноты</dt><dd>совпадение {n['mean_sim']:.2f}, тактов ниже 0.6: {n['pct_bars_low']}%</dd>
    <dt>Покрытие</dt><dd>концерт {c['concert_bars']} / {A.lower()} {c['stem_bars']} из {c['bars']} тактов</dd>
    <dt>Тайминг</dt><dd>концерт: {tline(t['concert'])}<br>{A.lower()}: {tline(t['stem'])}</dd>
    <dt>Запись</dt><dd>тишина {q['silence_dbfs']:.0f} dBFS, пик {q['peak_dbfs']:.1f} dBFS{', <b>клиппинг: ' + str(q['clip_runs']) + ' срезов</b>' if q['clip_runs'] else ''}; громкость концерт {r['lufs']['concert']:.1f} / {A.lower()} {r['lufs']['stem']:.1f} LUFS</dd>
    <dt>Синхронизация</dt><dd>клики {r['map']['clicks_matched']}, p90 {r['map']['p90_ms']} мс{f", темп концерта ×{r['map']['tempo_ratio']} (растянут под рендер)" if abs(r['map']['tempo_ratio'] - 1) > 0.002 else ''}{f"; концерт сдвинут на {r['concert_shift_ms_applied_in_ab']:+.0f} мс" if r['concert_shift_ms_applied_in_ab'] else ''}</dd>
  </dl>
  <div class="flags">
    {(f'<span class="lbl">Рома играл, в {"слое" if A != "Стем" else "стеме"} тихо:</span>' + chips(r['concert_only'], 'c-only')) if r['concert_only'] else ''}
    {(f'<span class="lbl">В {"слое" if A != "Стем" else "стеме"} есть, Рома молчал:</span>' + chips(r['stem_only'], 's-only')) if r['stem_only'] else ''}
    {('<span class="lbl">Другие ноты:</span>' + chips(n['low_runs'], 'low')) if n['low_runs'] else ''}
    {('<span class="lbl">Неровно по клику (4 такта):</span>' + ''.join(f'<button class="chip loose" data-t="{w[0]}">{w[0]} · {html.escape(w[1])}</button>' for w in loose)) if loose else ''}
  </div>
</section>""")

page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Концерт или стем</title>
<style>
:root{{--bg:#f7f6f3;--card:#fff;--fg:#1d1d1f;--mut:#6b6b70;--line:#e3e1dc;--acc:#2f5bd3;--bass:#8a4fd3;--keys:#c7781a;--good:#1f8a4c;--warn:#b5651d;--bad:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--card:#1f1f22;--fg:#ececee;--mut:#9a9aa1;--line:#333338;--acc:#7c9dff;--bass:#b48cff;--keys:#f0a24b;--good:#4fc27f;--warn:#e39a4d;--bad:#ff6b5e}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,system-ui,sans-serif}}
main{{max-width:980px;margin:0 auto;padding:24px 16px 80px}} h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 20px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:0 0 14px}}
.card header{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}} h2{{font-size:18px;margin:0}}
.tag{{font-size:12px;padding:2px 8px;border-radius:99px;color:#fff}} .tag.bass{{background:var(--bass)}} .tag.keys{{background:var(--keys)}}
.verdict{{font-size:13px;font-weight:600}} .v-good{{color:var(--good)}} .v-warn{{color:var(--warn)}} .v-bad{{color:var(--bad)}}
.note{{color:var(--mut);margin:6px 0 0}}
.player{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}}
.seg{{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}}
.src{{border:0;background:transparent;color:var(--fg);padding:7px 10px;font:inherit;font-size:13px;cursor:pointer}} .src.on{{background:var(--acc);color:#fff}}
.play{{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:8px;width:38px;height:34px;cursor:pointer}}
.pos{{flex:1;min-width:160px}} .time{{font-variant-numeric:tabular-nums;color:var(--mut);min-width:44px}}
dl.m{{display:grid;grid-template-columns:110px 1fr;gap:4px 12px;margin:6px 0 10px;font-size:14px}} dt{{color:var(--mut)}} dd{{margin:0}}
.flags{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}} .lbl{{color:var(--mut);font-size:13px;margin-left:4px}}
.chip{{border:1px solid var(--line);background:transparent;color:var(--fg);border-radius:99px;padding:3px 9px;font-size:12.5px;cursor:pointer}}
.chip.c-only{{border-color:var(--keys)}} .chip.s-only{{border-color:var(--acc)}} .chip.low{{border-color:var(--bad)}} .chip.loose{{border-color:var(--warn)}}
@media (max-width:600px){{dl.m{{grid-template-columns:1fr}} dt{{margin-top:6px}}}}
</style></head><body><main>
<h1>Концерт 28.10 или стем: партии Ромы</h1>
<p class="sub">Переключатель меняет источник с той же секунды. «В миксе» — вся группа (как в плейбеке, без клика) с партией из стема (в Такой любви — из слоя Ромы) или с концерта; громкость концертной партии подогнана под стем. Чипы — переход к месту.</p>
{''.join(cards)}
</main>
<script>
const fmt=t=>Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');
const parse=s=>{{const [m,x]=s.split(':');return (+m)*60+parseFloat(x)}};
let current=null;
document.querySelectorAll('.card').forEach(card=>{{
  const slug=card.dataset.slug, a=new Audio(), play=card.querySelector('.play'), pos=card.querySelector('.pos'), tm=card.querySelector('.time');
  let src='ab-stem'; a.preload='none'; a.src=encodeURIComponent(slug)+'/'+src+'.mp3';
  const setSrc=s=>{{const t=a.currentTime, p=!a.paused; src=s; a.src=encodeURIComponent(slug)+'/'+s+'.mp3';
    a.addEventListener('loadedmetadata',()=>{{a.currentTime=t; if(p) a.play();}},{{once:true}}); a.load();
    card.querySelectorAll('.src').forEach(b=>b.classList.toggle('on',b.dataset.src===s));}};
  card.querySelectorAll('.src').forEach(b=>b.onclick=()=>setSrc(b.dataset.src));
  play.onclick=()=>{{ if(a.paused){{ if(current&&current!==a) current.pause(); current=a; a.play(); }} else a.pause(); }};
  a.onplay=()=>play.textContent='❚❚'; a.onpause=()=>play.textContent='▶';
  a.ontimeupdate=()=>{{ if(a.duration) pos.value=a.currentTime/a.duration*1000; tm.textContent=fmt(a.currentTime); }};
  pos.oninput=()=>{{ if(a.duration) a.currentTime=pos.value/1000*a.duration; }};
  card.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{{ const go=()=>{{a.currentTime=Math.max(0,parse(c.dataset.t)-2); if(current&&current!==a) current.pause(); current=a; a.play();}};
    if(a.readyState<1){{ a.addEventListener('loadedmetadata',go,{{once:true}}); a.load(); }} else go(); }});
  document.addEventListener('keydown',e=>{{ if(current!==a) return; if(e.key==='a'||e.key==='ф') setSrc(src==='ab-stem'?'ab-concert':src==='ab-concert'?'ab-stem':src==='solo-stem'?'solo-concert':'solo-stem'); }});
}});
</script></body></html>"""
open(OUT + "/index.html", "w").write(page)
print("wrote", OUT + "/index.html", len(cards), "cards")
