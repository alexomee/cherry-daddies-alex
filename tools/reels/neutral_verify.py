import base64, json, os, subprocess, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")
snaps = {s["id"]: s for s in json.load(open("/tmp/reels/snap/_snap.json"))}

CHECK = ["vtoraya", "cmdq", "neochen", "meta", "drama", "pad", "dostavki", "50cent"]
EXPECT = {
    "vtoraya": "просьба сыграть вторую ноту/часть повеселее",
    "cmdq": "случайно закрыл проект Command+Q, всё вылетело",
    "neochen": "хотите послушать запись — не очень",
    "meta": "контент для рилса набран / зачем это записывали",
    "drama": "Roma, just listen to me, it's on the keys channel",
    "pad": "Steve: Ah the pad, not part",
    "dostavki": "заговор забирать чужие доставки чтобы починили приложение",
    "50cent": "Greg/караоке за 300-350 евро, he knows 50 Cent in Berlin",
}
# NEUTRAL prompt — no hint what to find
PROMPT = """Транскрибируй ДОСЛОВНО всё, что РЕАЛЬНО говорят в этом аудио-клипе (RU и EN как есть).
Не додумывай и не добавляй то, чего нет. Верни ТОЛЬКО JSON:
{"speech": true/false, "transcript": "сплошной дословный текст, или пусто если речи нет"}"""


def verify(cid):
    s = snaps[cid]
    a = max(0, s["abs_start"] - 1.0); dur = (s["abs_end"] - s["abs_start"]) + 2.0
    clip = f"/tmp/reels/snap/{cid}_chk.mp3"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a}", "-t", f"{dur}",
                    "-i", f"{DL}/{s['video']}.MOV", "-map", "0:a:0", "-vn", "-ac", "1", "-b:a", "64k", clip, "-y"], check=True)
    b64 = base64.b64encode(open(clip, "rb").read()).decode()
    body = {"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.0}}
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
    return cid, g.get("speech"), g.get("transcript", "")


res = {}
with ThreadPoolExecutor(max_workers=5) as ex:
    for fut in as_completed([ex.submit(verify, c) for c in CHECK]):
        cid, sp, tr = fut.result()
        res[cid] = (sp, tr)

for cid in CHECK:
    sp, tr = res[cid]
    print(f"\n### {cid}  speech={sp}")
    print(f"  EXPECT: {EXPECT[cid]}")
    print(f"  HEARD : {tr[:260]}")
