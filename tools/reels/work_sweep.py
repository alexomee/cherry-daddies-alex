import base64, json, os, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
HOME = os.path.expanduser("~")
DL = f"{HOME}/Downloads"
AUD = "/tmp/reels/audio"
OUT = "/tmp/reels/work"
os.makedirs(AUD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

VIDEOS = ["IMG_2621", "IMG_2622"]
CHUNK = 900      # 15 min
OVERLAP = 20
STEP = CHUNK - OVERLAP

PROMPT = """Ты слушаешь аудио с репетиции русскоязычной кавер-группы Cherry Daddies (играют хиты 2000-х). Участники играют песни и МЕЖДУ дублями разбирают, что у кого не получается и что надо отрепетировать.

СОСТАВ (атрибутируй по имени если названо, иначе по роли):
- Таня — вокалистка
- Рома — клавишник (MainStage, ведёт плейбек/клик/cue)
- гитарист
- барабанщик
- Стив (Steve) — англоязычный участник (часто языковой барьер)
- встречаются имена: Артур, Саша, Грег (Greg)

ТРИ ЗАДАЧИ. Время в СЕКУНДАХ от начала клипа (число).

1. "map" — грубая карта аудио: сегменты {start_sec, end_sec, type ("music"|"talk"|"mixed"), song (название песни если играют/обсуждают, иначе ""), desc}.

2. "work" — РАБОЧИЕ моменты: всё, где обсуждают что надо доработать/отрепетировать, разбирают ошибку, дают указание, договариваются о структуре/аранжировке/темпе/тональности/переходах, фиксируют проблему. Каждый:
   {start_sec, end_sec, who (КОМУ адресовано / кто должен поработать: имя или роль, или "вся группа"), song (песня к которой относится, или ""), topic (о чём: вступление/концовка/темп/тональность/громкость/структура/синхрон/слова/звук/оборудование/...), action (КОНКРЕТНО что сделать/отрепетировать — императивно), quote (дословная ключевая реплика, RU+EN как есть), severity (1-5: 5=критично/много раз повторяли)}.
   Будь дотошным: рабочих моментов обычно МНОГО. Не выдумывай — только то, что реально сказано.

3. "moments" — смешные/цепляющие куски для коротких рилсов: шутки, смех, факапы, споры, мемные фразы, неловкие паузы, языковой барьер Стива. Каждый: {start_sec, end_sec, category (шутка|смех|факап|спор|фраза|инсайт|другое), quote (дословно), why (почему смешно/цепляет), score (1-10, 8+ только реально яркое)}.

Верни ТОЛЬКО JSON: {"map":[...], "work":[...], "moments":[...]}."""


def duration(path):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], text=True).strip())


def plan_chunks(dur):
    chunks, i = [], 0
    while i * STEP < dur:
        start = i * STEP
        ln = min(CHUNK, dur - start)
        if ln < 60 and i > 0:
            break
        chunks.append((start, ln))
        i += 1
    return chunks


def extract(video, start, ln):
    out = f"{AUD}/{video}_{int(start):05d}.mp3"
    if not os.path.exists(out) or os.path.getsize(out) < 1000:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-t", str(ln),
             "-i", f"{DL}/{video}.MOV", "-vn", "-ac", "1", "-b:a", "64k", out, "-y"],
            check=True)
    return out


def gemini(audio_path):
    with open(audio_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = {
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.3},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    data = json.dumps(body).encode()
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = json.load(urllib.request.urlopen(req, timeout=400))
            txt = resp["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(txt)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 5:
                time.sleep(6 * (attempt + 1)); continue
            raise
        except Exception:
            if attempt < 5:
                time.sleep(4 * (attempt + 1)); continue
            raise


def process(video, start, ln):
    cache = f"{OUT}/{video}_{int(start):05d}.json"
    if os.path.exists(cache):
        return video, start, json.load(open(cache))
    audio = extract(video, start, ln)
    res = gemini(audio)
    json.dump(res, open(cache, "w"), ensure_ascii=False)
    return video, start, res


tasks = []
for v in VIDEOS:
    dur = duration(f"{DL}/{v}.MOV")
    for (start, ln) in plan_chunks(dur):
        tasks.append((v, start, ln))
print(f"{len(tasks)} chunks across {len(VIDEOS)} videos", file=sys.stderr)

work = {v: [] for v in VIDEOS}
moments = {v: [] for v in VIDEOS}
amap = {v: [] for v in VIDEOS}
with ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(process, v, s, l): (v, s) for (v, s, l) in tasks}
    for fut in as_completed(futs):
        v, s = futs[fut]
        try:
            video, start, res = fut.result()
            for w in res.get("work", []):
                w["g_start"] = float(w.get("start_sec", 0)) + start
                w["g_end"] = float(w.get("end_sec", 0)) + start
                w["video"] = video
                work[video].append(w)
            for m in res.get("moments", []):
                m["g_start"] = float(m.get("start_sec", 0)) + start
                m["g_end"] = float(m.get("end_sec", 0)) + start
                m["video"] = video
                moments[video].append(m)
            for seg in res.get("map", []):
                seg["g_start"] = float(seg.get("start_sec", 0)) + start
                seg["g_end"] = float(seg.get("end_sec", 0)) + start
                seg["video"] = video
                amap[video].append(seg)
            print(f"  ok {v}@{int(s)}: work={len(res.get('work',[]))} moments={len(res.get('moments',[]))}", file=sys.stderr)
        except Exception as e:
            print(f"  FAIL {v}@{int(s)}: {e}", file=sys.stderr)


def dedup(items, thr=10):
    items = sorted(items, key=lambda x: x["g_start"])
    keep = []
    for it in items:
        dup = next((k for k in keep if abs(k["g_start"] - it["g_start"]) < thr
                    and k.get("who", k.get("category")) == it.get("who", it.get("category"))), None)
        if dup:
            if it.get("severity", it.get("score", 0)) > dup.get("severity", dup.get("score", 0)):
                keep[keep.index(dup)] = it
        else:
            keep.append(it)
    return keep


for v in VIDEOS:
    work[v] = dedup(work[v])
    moments[v] = dedup(moments[v])

json.dump({"work": work, "moments": moments, "map": amap},
          open(f"{OUT}/_work.json", "w"), ensure_ascii=False, indent=1)
print(f"\nwrote {OUT}/_work.json", file=sys.stderr)
print(f"TOTAL work items: {sum(len(work[v]) for v in VIDEOS)}, moments: {sum(len(moments[v]) for v in VIDEOS)}", file=sys.stderr)
