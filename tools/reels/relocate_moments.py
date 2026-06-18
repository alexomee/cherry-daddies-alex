import base64, json, os, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")
WIN = "/tmp/reels/win"
os.makedirs(WIN, exist_ok=True)
SRCDUR = {"IMG_2621": 5646.15, "IMG_2622": 5439.45}
PAD = 60.0          # window half-width around Gemini guess
MINSCORE = 7

mom = []
d = json.load(open("/tmp/reels/work/_work.json"))
for v in d["moments"]:
    for m in d["moments"][v]:
        if int(m.get("score", 0)) >= MINSCORE:
            mom.append(m)
# order: score desc, then source time
mom.sort(key=lambda m: (-int(m.get("score", 0)), m["video"], m["g_start"]))
for i, m in enumerate(mom):
    m["id"] = i + 1
print(f"{len(mom)} moments to relocate", file=sys.stderr)

PROMPT = """Тебе дан короткий аудио-фрагмент с репетиции кавер-группы. Найди в нём конкретный момент:
ЦИТАТА: «{quote}»
КОНТЕКСТ: {why}

Если этот момент РЕАЛЬНО есть в аудио — верни точные секунды НАЧАЛА и КОНЦА самого яркого/смешного куска (длительность 4-12с, чтобы момент был понятен целиком, с маленьким запасом ~0.5с по краям). Также верни дословно, что реально слышно.
Если момента в этом аудио НЕТ — found=false.
Время в СЕКУНДАХ от начала ЭТОГО фрагмента (число). Верни ТОЛЬКО JSON: {{"found": true/false, "start_sec": N, "end_sec": N, "heard": "дословный текст"}}"""


def gem(b64, prompt):
    body = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}],
            "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
    data = json.dumps(body).encode()
    for a in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}), timeout=200))
            return json.loads(r["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and a < 5:
                time.sleep(5 * (a + 1)); continue
            raise
        except Exception:
            if a < 5:
                time.sleep(4 * (a + 1)); continue
            raise


def relocate(m):
    v = m["video"]
    dur = SRCDUR[v]
    ws = max(0.0, m["g_start"] - PAD)
    we = min(dur, m["g_end"] + PAD)
    wlen = we - ws
    clip = f"{WIN}/m{m['id']:02d}.mp3"
    if not os.path.exists(clip) or os.path.getsize(clip) < 1000:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ws}", "-t", f"{wlen}",
                        "-i", f"{DL}/{v}.MOV", "-vn", "-ac", "1", "-b:a", "64k", clip, "-y"], check=True)
    b64 = base64.b64encode(open(clip, "rb").read()).decode()
    g = gem(b64, PROMPT.format(quote=m.get("quote", ""), why=m.get("why", "")))
    out = dict(m)
    if g.get("found") and g.get("end_sec") is not None:
        a = float(g["start_sec"]); b = float(g["end_sec"])
        if b <= a:
            b = a + 6.0
        out["abs_start"] = max(0.0, ws + a)
        out["abs_end"] = min(dur, ws + b)
        out["found"] = True
        out["heard"] = g.get("heard", "")
    else:
        # fallback: padded original guess
        out["abs_start"] = max(0.0, m["g_start"] - 1.5)
        out["abs_end"] = min(dur, m["g_end"] + 1.5)
        if out["abs_end"] - out["abs_start"] < 6:
            out["abs_end"] = min(dur, out["abs_start"] + 8)
        out["found"] = False
        out["heard"] = g.get("heard", "")
    return out


res = [None] * len(mom)
with ThreadPoolExecutor(max_workers=5) as ex:
    futs = {ex.submit(relocate, m): m["id"] for m in mom}
    for fut in as_completed(futs):
        mid = futs[fut]
        try:
            r = fut.result()
            res[mid - 1] = r
            print(f"  #{mid:02d} found={r['found']} {r['abs_start']:.1f}-{r['abs_end']:.1f}", file=sys.stderr)
        except Exception as e:
            print(f"  #{mid:02d} FAIL {e}", file=sys.stderr)

res = [r for r in res if r]
json.dump(res, open("/tmp/reels/win/_moments_loc.json", "w"), ensure_ascii=False, indent=1)
print(f"\nwrote /tmp/reels/win/_moments_loc.json  ({len(res)} clips, {sum(r['found'] for r in res)} found / {sum(not r['found'] for r in res)} fallback)", file=sys.stderr)
