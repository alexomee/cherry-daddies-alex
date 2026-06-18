import base64, json, os, subprocess, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")
SRC = f"{DL}/IMG_2562.MOV"
WIN = 40
START, END = 978, 1520  # пост-арка
os.makedirs("/tmp/reels/sing", exist_ok=True)

PROMPT = """Аудио с репетиции кавер-группы (клип с t=0). Это спор про «вторую часть/ноту» уже позади.
Меня интересует ТОЛЬКО: поёт ли вокалистка (Таня, женский голос) ВЖИВУЮ мелодию песни под живую игру клавиш — то есть РЕАЛЬНОЕ исполнение этой части, а не разговор/смех/отсчёт и не запись-плейбэк.
Верни ТОЛЬКО JSON:
{"sings_live": true/false, "clarity": 1-10 (насколько чисто слышно её вокал+мелодию), "keys": true/false,
 "span_start": сек, "span_end": сек (лучший 4-8с фрагмент её живого пения в этом клипе, время от начала клипа; если нет — null),
 "what": "что поёт/что происходит"}"""


def run(ws):
    clip = f"/tmp/reels/sing/w_{ws}.mp3"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(ws), "-t", str(WIN),
                    "-i", SRC, "-map", "0:a:0", "-vn", "-ac", "1", "-b:a", "64k", clip, "-y"], check=True)
    b64 = base64.b64encode(open(clip, "rb").read()).decode()
    body = {"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    for attempt in range(5):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=120))
            g = json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
            break
        except Exception:
            if attempt < 4:
                time.sleep(4 * (attempt + 1)); continue
            raise
    g["ws"] = ws
    return g


windows = list(range(START, END, WIN))
res = []
with ThreadPoolExecutor(max_workers=6) as ex:
    for fut in as_completed([ex.submit(run, w) for w in windows]):
        res.append(fut.result())
res.sort(key=lambda x: x["ws"])


def mmss(x):
    x = int(round(float(x))); return f"{x//60:02d}:{x%60:02d}"


json.dump(res, open("/tmp/reels/sing/_scan.json", "w"), ensure_ascii=False, indent=1)
print("== SINGING CANDIDATES (sings_live, sorted by clarity) ==")
cand = [r for r in res if r.get("sings_live") and r.get("span_start") is not None]
for r in sorted(cand, key=lambda x: -x.get("clarity", 0)):
    a0 = r["ws"] + float(r["span_start"]); a1 = r["ws"] + float(r["span_end"])
    print(f"  clarity {r.get('clarity')}/10  keys={r.get('keys')}  {mmss(a0)}-{mmss(a1)} (abs {a0:.0f}-{a1:.0f})")
    print(f"     {r.get('what','')}")
print("\n== windows with NO live singing ==")
print("  " + ", ".join(mmss(r["ws"]) for r in res if not (r.get("sings_live") and r.get("span_start") is not None)))
