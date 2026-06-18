import base64, glob, json, os, subprocess, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")
ASR = "/tmp/reels/asr"
os.makedirs("/tmp/reels/snap", exist_ok=True)

# (id, video, win_start, win_end, desc) — window to listen; Gemini picks funniest core inside
GOLD = [
    ("meta",     "IMG_2562", 1124, 1148, "мета: 'контент для рилса уже набран / можно выключать камеру' и 'бля, зачем вы это записывали?'"),
    ("vtoraya",  "IMG_2562",  860,  880, "девушка просит сделать вторую сыгранную ноту/часть 'повеселее', она сильно отличается"),
    ("cmdq",     "IMG_2564", 1570, 1592, "случайно нажал Command+Q, всё вылетело, 'серьёзно? ... бывает'"),
    ("neochen",  "IMG_2564", 2308, 2326, "'хотите послушать что получилось?' — 'не очень' — 'не очень, ага, кому это надо'"),
    ("mediator", "IMG_2563", 2350, 2445, "перевод для Стива слова 'медиатор' (pick), и шутка 'медиатор это чувак который всех разводит'"),
    ("pad",      "IMG_2562", 2270, 2315, "Стив не понимает part/pad, в итоге 'Ah, the pad! not part' — языковой барьер про драм-пэд"),
    ("dostavki", "IMG_2567", 1592, 1640, "заговор забирать чужие доставки еды/воды чтобы приложение починили навигацию"),
    ("50cent",   "IMG_2563", 1430, 1525, "Стив: Грег предложил караоке-аппарат и микрофоны за 300-350 евро, 'he knows 50 Cent in Berlin'"),
    ("drama",    "IMG_2567",  180,  390, "Стив эмоционально по-английски 'just fucking listen to me, it's on the keys channel' (Рома/'Drama')"),
]

PROMPT = """Аудио-клип с репетиции русскоязычной кавер-группы (есть англоязычный Стив). Клип начинается с t=0.
Найди в нём САМЫЙ смешной короткий фрагмент по теме: «{desc}».

Верни ТОЛЬКО JSON:
{{
 "found": true/false,
 "is_talk": true/false,
 "core_start": сек,   // от начала клипа: начало смешного фрагмента (не более ~16 сек длиной)
 "core_end": сек,
 "title": "цепляющая подпись рилса, рус, до 6 слов",
 "lines": [ {{"start":сек,"end":сек,"text":"дословно, RU+EN как есть, чисто, 2-7 слов"}} ]  // время от начала КЛИПА
}}
Если фрагмента нет — found=false."""


def words_for(video):
    ws = []
    for jf in sorted(glob.glob(f"{ASR}/{video}_*.json")):
        off = int(os.path.basename(jf).rsplit("_", 1)[1].split(".")[0])
        d = json.load(open(jf))
        for s in d.get("segments", []):
            for w in s.get("words", []):
                ws.append((w["start"] + off, w["end"] + off))
    ws.sort()
    return ws


def snap_start(t, words):
    cands = [a for (a, b) in words if abs(a - t) <= 1.6]
    return min(cands, key=lambda a: abs(a - t)) if cands else t


def snap_end(t, words):
    cands = [b for (a, b) in words if abs(b - t) <= 1.6]
    return min(cands, key=lambda b: abs(b - t)) if cands else t


def gemini(path, desc):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {"contents": [{"parts": [{"text": PROMPT.format(desc=desc)},
            {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    data = json.dumps(body).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = json.load(urllib.request.urlopen(req, timeout=180))
            return json.loads(resp["candidates"][0]["content"]["parts"][0]["text"])
        except Exception:
            if attempt < 4:
                time.sleep(4 * (attempt + 1)); continue
            raise


WORDS = {}


def process(item):
    cid, video, ws_, we_, desc = item
    if video not in WORDS:
        WORDS[video] = words_for(video)
    clip = f"/tmp/reels/snap/{cid}.mp3"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(ws_), "-t", str(we_ - ws_),
                    "-i", f"{DL}/{video}.MOV", "-vn", "-ac", "1", "-b:a", "64k", clip, "-y"], check=True)
    g = gemini(clip, desc)
    if not g.get("found"):
        return {"id": cid, "video": video, "found": False}
    cs = ws_ + float(g["core_start"]); ce = ws_ + float(g["core_end"])
    cs_s = snap_start(cs, WORDS[video]); ce_s = snap_end(ce, WORDS[video])
    lines = []
    for ln in g.get("lines", []):
        lines.append({"start": ws_ + float(ln["start"]), "end": ws_ + float(ln["end"]), "text": ln["text"]})
    return {"id": cid, "video": video, "found": True, "is_talk": g.get("is_talk"),
            "title": g.get("title", ""), "abs_start": round(cs_s, 2), "abs_end": round(ce_s, 2),
            "gem_start": round(cs, 2), "gem_end": round(ce, 2), "lines": lines}


def mmss(x):
    x = int(round(float(x))); return f"{x//60:02d}:{x%60:02d}"


results = []
# preload words sequentially to avoid races
for v in set(g[1] for g in GOLD):
    WORDS[v] = words_for(v)
with ThreadPoolExecutor(max_workers=5) as ex:
    for fut in as_completed([ex.submit(process, it) for it in GOLD]):
        results.append(fut.result())

results.sort(key=lambda r: [g[0] for g in GOLD].index(r["id"]))
json.dump(results, open("/tmp/reels/snap/_snap.json", "w"), ensure_ascii=False, indent=1)
for r in results:
    if not r.get("found"):
        print(f"[{r['id']}] ✗ not found"); continue
    snapd = f"snap {mmss(r['abs_start'])}-{mmss(r['abs_end'])} ({r['abs_end']-r['abs_start']:.1f}s)"
    print(f"\n[{r['id']}] {r['video']} {snapd}  «{r['title']}»  talk={r['is_talk']}")
    for ln in r["lines"]:
        print(f"     {ln['text']}")
