import base64, json, math, os, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
HOME = os.path.expanduser("~")
DL = f"{HOME}/Downloads"
AUD = "/tmp/reels/audio"
OUT = "/tmp/reels/out"
os.makedirs(AUD, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

VIDEOS = ["IMG_2562", "IMG_2563", "IMG_2564", "IMG_2567"]
CHUNK = 900      # 15 min
OVERLAP = 20
STEP = CHUNK - OVERLAP

PROMPT = """Ты слушаешь аудио с репетиции русскоязычной музыкальной кавер-группы: участники играют песни и болтают между дублями.

Две задачи:
1. Грубая КАРТА аудио — раздели на сегменты по типу: "music" (играют/поют песню), "talk" (разговоры без музыки), "mixed" (говорят поверх музыки). Каждый сегмент: {start_sec, end_sec, type, desc}.
2. МОМЕНТЫ для смешных/интересных коротких рилсов: шутки, смех, факапы, забавные споры, мемные фразы, неловкие паузы, абсурдные просьбы. Каждый: {start_sec, end_sec, category (шутка|смех|факап|спор|фраза|инсайт|другое), quote (дословно), why (почему смешно/цепляет), score (1-10)}.

Время в СЕКУНДАХ от начала клипа (число). Строго к score: 8+ только реально яркое, годное в рилс.
Верни ТОЛЬКО JSON: {"map":[...], "moments":[...]}."""


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
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.4},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    data = json.dumps(body).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = json.load(urllib.request.urlopen(req, timeout=300))
            txt = resp["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(txt)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(5 * (attempt + 1)); continue
            raise
        except Exception:
            if attempt < 4:
                time.sleep(3 * (attempt + 1)); continue
            raise


def process(video, start, ln):
    cache = f"{OUT}/{video}_{int(start):05d}.json"
    if os.path.exists(cache):
        return video, start, json.load(open(cache))
    audio = extract(video, start, ln)
    res = gemini(audio)
    json.dump(res, open(cache, "w"), ensure_ascii=False)
    return video, start, res


# build task list
tasks = []
for v in VIDEOS:
    dur = duration(f"{DL}/{v}.MOV")
    for (start, ln) in plan_chunks(dur):
        tasks.append((v, start, ln))
print(f"{len(tasks)} chunks across {len(VIDEOS)} videos", file=sys.stderr)

results = {v: [] for v in VIDEOS}
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(process, v, s, l): (v, s) for (v, s, l) in tasks}
    for fut in as_completed(futs):
        v, s = futs[fut]
        try:
            video, start, res = fut.result()
            for m in res.get("moments", []):
                m["g_start"] = float(m["start_sec"]) + start
                m["g_end"] = float(m["end_sec"]) + start
                m["video"] = video
                results[video].append(m)
            print(f"  ok {v}@{int(s)}: {len(res.get('moments',[]))} moments", file=sys.stderr)
        except Exception as e:
            print(f"  FAIL {v}@{int(s)}: {e}", file=sys.stderr)

# dedup overlap: same video, within 8s start, keep higher score
def dedup(ms):
    ms = sorted(ms, key=lambda x: x["g_start"])
    keep = []
    for m in ms:
        dup = next((k for k in keep if abs(k["g_start"] - m["g_start"]) < 8), None)
        if dup:
            if m.get("score", 0) > dup.get("score", 0):
                keep[keep.index(dup)] = m
        else:
            keep.append(m)
    return keep

for v in VIDEOS:
    results[v] = dedup(results[v])

json.dump(results, open(f"{OUT}/_all.json", "w"), ensure_ascii=False, indent=1)


def mmss(s):
    s = int(round(s)); return f"{s//60:02d}:{s%60:02d}"

allm = [m for v in VIDEOS for m in results[v]]
print(f"\n==== {len(allm)} unique moments. TOP (score>=7) by video ====\n")
for v in VIDEOS:
    top = sorted([m for m in results[v] if m.get("score", 0) >= 7], key=lambda x: -x["score"])
    print(f"### {v}  ({len(results[v])} total, {len(top)} strong)")
    for m in top:
        print(f"  [{m.get('score')}/10] {mmss(m['g_start'])}-{mmss(m['g_end'])} «{m.get('category','')}»")
        print(f"        {m.get('quote','')}")
        print(f"        → {m.get('why','')}")
    print()
