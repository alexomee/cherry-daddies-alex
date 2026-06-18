import json, os, subprocess, sys, textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont

DL = os.path.expanduser("~/Downloads")
SEG = "/tmp/reels/review/seg"
CARD = "/tmp/reels/review/card"
os.makedirs(SEG, exist_ok=True)
os.makedirs(CARD, exist_ok=True)
SRCJSON = sys.argv[1] if len(sys.argv) > 1 else "/tmp/reels/win/_moments_loc.json"
OUT = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else "~/Downloads/rehearsal-reels/cherry_funny_review_v1.mp4")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

W, H = 1280, 720

FONTS = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
FONTS_B = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]
FONT = next(f for f in FONTS if os.path.exists(f))
FONTB = next(f for f in FONTS_B if os.path.exists(f))


def fnt(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz)


def vlabel(v):
    return {"IMG_2621": "вид1", "IMG_2622": "вид2"}[v]


def mmss(s):
    s = int(round(s)); return f"{s//60:02d}:{s%60:02d}"


def draw_center(d, cy, text, font, fill):
    bb = d.textbbox((0, 0), text, font=font)
    w = bb[2] - bb[0]; h = bb[3] - bb[1]
    d.text(((W - w) // 2, cy), text, font=font, fill=fill)
    return h


def make_card(m):
    img = Image.new("RGB", (W, H), (17, 18, 22))
    d = ImageDraw.Draw(img)
    cat = m.get("category", "")
    src = m.get("video")
    meta = f"[{m.get('score')}/10 · {cat}]   {vlabel(src)} {mmss(m.get('g_start',0))}"
    # number
    draw_center(d, 70, f"#{m['id']:02d}", fnt(150, True), (255, 220, 90))
    # meta
    draw_center(d, 250, meta, fnt(44, True), (180, 200, 255))
    if not m.get("found"):
        draw_center(d, 312, "≈ позиция приблизительная", fnt(30), (255, 120, 120))
    # quote wrapped
    q = (m.get("quote") or "").strip()
    lines = []
    for para in q.split("\n"):
        lines += textwrap.wrap(para, width=42) or [""]
    f = fnt(46)
    y = 380
    for ln in lines[:6]:
        bb = d.textbbox((0, 0), ln, font=f)
        d.text(((W - (bb[2]-bb[0])) // 2, y), ln, font=f, fill=(240, 240, 240))
        y += 58
    img.save(f"{CARD}/card_{m['id']:02d}.png")


def make_badge(m):
    bw, bh = 168, 78
    img = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=16, fill=(0, 0, 0, 170))
    f = fnt(50, True)
    t = f"#{m['id']:02d}"
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((bw - (bb[2]-bb[0])) // 2, (bh - (bb[3]-bb[1])) // 2 - 6), t, font=f, fill=(255, 220, 90, 255))
    img.save(f"{CARD}/badge_{m['id']:02d}.png")


VENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]


def card_dur(m):
    q = m.get("quote") or ""
    return min(3.2, 1.5 + 0.022 * len(q))


def enc_card(m):
    png = f"{CARD}/card_{m['id']:02d}.png"
    out = f"{SEG}/{m['id']:03d}a_card.mp4"
    dur = card_dur(m)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-loop", "1", "-t", f"{dur}", "-i", png,
                    "-f", "lavfi", "-t", f"{dur}", "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", f"scale={W}:{H},format=yuv420p", *VENC, "-shortest", out, "-y"], check=True)
    return out


def enc_clip(m):
    src = f"{DL}/{m['video']}.MOV"
    a = max(0.0, m["abs_start"] - 0.25)
    ln = (m["abs_end"] - m["abs_start"]) + 0.5
    badge = f"{CARD}/badge_{m['id']:02d}.png"
    out = f"{SEG}/{m['id']:03d}b_clip.mp4"
    vf = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[v];[v][1:v]overlay=24:24[o]"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                    "-ss", f"{a}", "-t", f"{ln}", "-i", src,
                    "-i", badge,
                    "-filter_complex", vf, "-map", "[o]", "-map", "0:a:0",
                    *VENC, out, "-y"], check=True)
    return out


def build_one(m):
    make_card(m); make_badge(m)
    enc_card(m); enc_clip(m)
    return m["id"]


mom = json.load(open(SRCJSON))
mom = [m for m in mom if m.get("found", True)]
mom.sort(key=lambda m: m["id"])
print(f"building {len(mom)} review segments from {SRCJSON}", file=sys.stderr)

with ThreadPoolExecutor(max_workers=4) as ex:
    for fut in as_completed([ex.submit(build_one, m) for m in mom]):
        try:
            print(f"  seg #{fut.result():02d} ok", file=sys.stderr)
        except Exception as e:
            print(f"  FAIL {e}", file=sys.stderr)

# concat list in order
lst = "/tmp/reels/review/concat.txt"
with open(lst, "w") as f:
    for m in mom:
        f.write(f"file '{SEG}/{m['id']:03d}a_card.mp4'\n")
        f.write(f"file '{SEG}/{m['id']:03d}b_clip.mp4'\n")
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", lst, "-c", "copy", OUT, "-y"], check=True)

dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", OUT], text=True).strip())
print(f"\nWROTE {OUT}  ({dur/60:.1f} min, {len(mom)} clips)", file=sys.stderr)

# index file
idx = OUT.replace(".mp4", "_index.txt")
with open(idx, "w") as f:
    for m in mom:
        tag = "" if m.get("found") else "  [≈approx]"
        f.write(f"#{m['id']:02d}  [{m.get('score')}/10 {m.get('category')}]  {vlabel(m['video'])} {mmss(m.get('g_start',0))}{tag}\n")
        f.write(f"      «{m.get('quote')}»\n")
        f.write(f"      → {m.get('why')}\n")
print(f"WROTE {idx}", file=sys.stderr)
