import base64, json, os, re, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import mlx_whisper

KEY = subprocess.check_output(
    "grep '^AGENTIQA_GEMINI_API_KEY=' ~/projects/agentiqa/apps/desktop-next/.env | cut -d= -f2-",
    shell=True, text=True).strip()
MODEL = "gemini-3.5-flash"
DL = os.path.expanduser("~/Downloads")
NAR = "/tmp/reels/narrow"
os.makedirs(NAR, exist_ok=True)
SRCDUR = {"IMG_2621": 5646.15, "IMG_2622": 5439.45}
WHMODEL = "mlx-community/whisper-large-v3-turbo"

# ---- user feedback (review v1) ----
REMOVE = {2, 5, 8, 9}
QUOTE_FIX = {1: "Surprisingly Tanya SOUNDS very nice. — Did you need the word 'surprisingly' in that sentence?"}
EXTRA_LEAD = {1: 24.0, 6: 13.0, 7: 13.0}
TIGHTEN = {12: 3.0}
PAD = float(os.environ.get("VFIX_PAD", "45"))
SUBSET = os.environ.get("VFIX_IDS", "")   # "" = all; else comma ids: force re-transcribe + merge
CENTER = os.environ.get("VFIX_CENTER", "g")   # "g"=sweep g_start, "reloc"=v1 relocate abs_start


def win_bounds(m):
    v = m["video"]; dur = SRCDUR[v]
    if CENTER == "reloc" and m.get("abs_start"):
        c0 = m["abs_start"]; c1 = m.get("abs_end", c0)
    else:
        c0 = m["g_start"]; c1 = m["g_end"]
    a = c0 - PAD; b = c1 + PAD
    if a >= dur - 5:                       # guess past EOF -> last 120s
        a = dur - 120; b = dur
    return max(0.0, a), min(dur, b)


def transcribe_window(m):
    v = m["video"]; a, b = win_bounds(m)
    clip = f"{NAR}/g{m['id']:02d}.mp3"
    js = f"{NAR}/g{m['id']:02d}.json"
    if not os.path.exists(js):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a}", "-t", f"{b-a}",
                        "-i", f"{DL}/{v}.MOV", "-vn", "-ac", "1", "-ar", "16000", "-b:a", "128k", clip, "-y"], check=True)
        r = mlx_whisper.transcribe(clip, path_or_hf_repo=WHMODEL, word_timestamps=True)
        json.dump(r, open(js, "w"), ensure_ascii=False)
    return m["id"]


def load_words(mid, win_start):
    j = json.load(open(f"{NAR}/g{mid:02d}.json"))
    out = []
    for s in j.get("segments", []):
        for w in s.get("words", []):
            st = w.get("start")
            if st is None:
                continue
            en = w.get("end"); en = en if en is not None else st
            out.append((round(st + win_start, 2), round(en + win_start, 2), w.get("word", "").strip()))
    return out, j.get("language", "")


PROMPT = """Тебе дан ТАЙМ-КОДИРОВАННЫЙ транскрипт короткого куска аудио репетиции кавер-группы (формат «секунда:слово», секунды АБСОЛЮТНЫЕ от начала видео; может быть RU и EN вперемешку, англ. иногда искажён).

Найди в нём конкретный СМЕШНОЙ момент:
ЦИТАТА: «{quote}»
ПОЧЕМУ СМЕШНО: {why}

Верни ТОЛЬКО JSON:
{{"found": true/false,
  "punch_start": <абс.сек первого слова соли>, "punch_end": <абс.сек последнего слова соли>,
  "clip_start": <абс.сек начала клипа: включи естественный заход ~5-8с перед солью, начни с границы фразы>,
  "clip_end": <абс.сек конца клипа, ~1с после соли>,
  "said": "что реально слышно в районе соли"}}

found=false, если сути момента в транскрипте НЕТ (только обрывок/не та речь). Бери времена ИЗ транскрипта, не выдумывай.

ТРАНСКРИПТ:
{transcript}"""


def gem(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}],
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


def analyze(m):
    mid = m["id"]; v = m["video"]; dur = SRCDUR[v]
    if mid in QUOTE_FIX:
        m["quote"] = QUOTE_FIX[mid]
    a, _ = win_bounds(m)
    words, lang = load_words(mid, a)
    out = dict(m); out["asr_lang"] = lang
    if len(words) < 3:
        out["found"] = False; out["note"] = f"sparse asr ({len(words)}w)"; return out
    tr = " ".join(f"{w[0]}:{w[2]}" for w in words)
    g = gem(PROMPT.format(quote=m.get("quote", ""), why=m.get("why", ""), transcript=tr))
    out["said"] = g.get("said", "")
    if not g.get("found"):
        out["found"] = False; out["note"] = "not in transcript"; return out
    ps = float(g.get("punch_start", 0)); pe = float(g.get("punch_end", 0))
    cs = float(g.get("clip_start", ps)); ce = float(g.get("clip_end", pe))
    if mid in EXTRA_LEAD:
        cs = ps - EXTRA_LEAD[mid]
    if mid in TIGHTEN:
        cs = max(cs, ps - TIGHTEN[mid])
    if ps > 0:
        cs = min(cs, ps - 1.0)
    starts = [w[0] for w in words]; ends = [w[1] for w in words]
    cs = min(starts, key=lambda x: abs(x - max(0.0, cs)))
    ce = min(ends, key=lambda x: abs(x - min(dur, ce)))
    if ce - cs < 3:
        ce = min(dur, cs + 5)
    out["abs_start"] = round(cs, 2); out["abs_end"] = round(ce, 2)
    out["punch_start"] = round(ps, 2); out["punch_end"] = round(pe, 2)
    out["found"] = True
    return out


loc = json.load(open("/tmp/reels/win/_moments_loc.json"))
loc = [m for m in loc if m["id"] not in REMOVE]
if SUBSET:
    ids = {int(x) for x in SUBSET.split(",") if x.strip()}
    loc = [m for m in loc if m["id"] in ids]
    for m in loc:                          # force re-transcribe at new PAD
        for ext in ("mp3", "json"):
            p = f"{NAR}/g{m['id']:02d}.{ext}"
            if os.path.exists(p):
                os.remove(p)
    print(f"SUBSET redo {sorted(ids)} at PAD={PAD}", file=sys.stderr)
print(f"{len(loc)} gags (removed {sorted(REMOVE)})", file=sys.stderr)

# phase 1: transcribe narrow windows IN-PROCESS (model loads once, serial)
print("phase 1: transcribing narrow windows (in-process)...", file=sys.stderr)
for m in loc:
    try:
        transcribe_window(m)
        print(f"  asr g{m['id']:02d} ok", file=sys.stderr)
    except Exception as e:
        print(f"  asr g{m['id']:02d} ERR {e}", file=sys.stderr)

# phase 2: gemini transcript-anchored bounds
print("phase 2: analyzing transcripts...", file=sys.stderr)
res = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(analyze, m): m["id"] for m in loc}
    for fut in as_completed(futs):
        mid = futs[fut]
        try:
            r = fut.result(); res.append(r)
            st = f"{r.get('abs_start')}-{r.get('abs_end')}" if r.get("found") else f"NOT FOUND ({r.get('note','')})"
            print(f"  #{mid:02d} [{r.get('asr_lang','')}] {st}", file=sys.stderr)
        except Exception as e:
            print(f"  #{mid:02d} ERR {e}", file=sys.stderr)

FIXP = "/tmp/reels/win/_moments_fix.json"
if SUBSET and os.path.exists(FIXP):
    merged = {r["id"]: r for r in json.load(open(FIXP))}
    for r in res:
        merged[r["id"]] = r
    res = list(merged.values())
res.sort(key=lambda m: m["id"])
json.dump(res, open(FIXP, "w"), ensure_ascii=False, indent=1)
nf = [r["id"] for r in res if not r.get("found")]
print(f"\nwrote _moments_fix.json  found={sum(r.get('found',False) for r in res)}/{len(res)}  NOT-FOUND={nf}", file=sys.stderr)
