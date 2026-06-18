import base64, json, os, subprocess, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")

BEATS = {0: (865.0, 876.5), 1: (879.0, 890.5), 2: (893.5, 909.5), 3: (957.5, 969.5), 4: (970.5, 978.8)}

PROMPT = """Аудио с репетиции кавер-группы. Диаризуй ДОСЛОВНО (RU).
Роли: "Таня" (вокалистка, жен. голос, недовольна нотой), "гитарист" (муж, комментирует/защищает), "Рома" (клавишник, муж, играет — его критикуют), "барабанщик" (молчит обычно).
Верни ТОЛЬКО JSON: {"lines":[{"start":сек,"end":сек,"speaker":"Таня|гитарист|Рома|барабанщик","text":"дословно, чисто, без оговорок-повторов"}]} — время от начала клипа.
Передавай реплики коротко (2-7 слов на строку, для субтитров). Если кто-то говорит что часть/нота ПРАВИЛЬНАЯ — так и пиши 'правильная' (не 'не правильная')."""


def run(idx):
    bs, be = BEATS[idx]
    clip = f"/tmp/reels/snap/beat{idx}_d.mp3"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(bs), "-t", str(be - bs),
                    "-i", f"{DL}/IMG_2562.MOV", "-map", "0:a:0", "-vn", "-ac", "1", "-b:a", "64k", clip, "-y"], check=True)
    b64 = base64.b64encode(open(clip, "rb").read()).decode()
    body = {"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    for attempt in range(5):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=180))
            g = json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
            break
        except Exception:
            if attempt < 4:
                time.sleep(4 * (attempt + 1)); continue
            raise
    # to absolute source time
    for ln in g.get("lines", []):
        ln["abs_start"] = round(bs + float(ln["start"]), 2)
        ln["abs_end"] = round(bs + float(ln["end"]), 2)
    return idx, g.get("lines", [])


res = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    for fut in as_completed([ex.submit(run, i) for i in BEATS]):
        idx, lines = fut.result()
        res[idx] = lines

json.dump(res, open("/tmp/reels/snap/_beat_caps.json", "w"), ensure_ascii=False, indent=1)
for i in sorted(res):
    print(f"=== beat{i} ===")
    for ln in res[i]:
        print(f"  {ln['abs_start']:.1f}-{ln['abs_end']:.1f} [{ln['speaker']:11}] {ln['text']}")
