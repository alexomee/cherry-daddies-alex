import json, os, subprocess

EDIT = os.path.expanduser("~/Downloads/rehearsal-reels")
DL = os.path.expanduser("~/Downloads")
os.makedirs(EDIT, exist_ok=True)
os.makedirs(f"{EDIT}/seg2", exist_ok=True)
snaps = {s["id"]: s for s in json.load(open("/tmp/reels/snap/_snap.json")) if s.get("found")}

# (id, short top-title)  — order = comedic flow
LINEUP = [
    ("meta",     "Зачем мы это снимаем"),
    ("vtoraya",  "«Сыграй повеселее»"),
    ("cmdq",     "Случайно нажал Command+Q"),
    ("neochen",  "«Кому это вообще надо»"),
    ("mediator", "Стив и слово «медиатор»"),
    ("drama",    "«Просто послушай меня!»"),
]
OFF = {"IMG_2562": 480, "IMG_2563": 480, "IMG_2564": 480, "IMG_2567": 440}
PAD = 0.13
X = 0.28
W, H, FPS = 1080, 1920, 30
BANDH = 960
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIALB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
SRC = {v: f"{DL}/{v}.MOV" for v in ["IMG_2562", "IMG_2563", "IMG_2564", "IMG_2567"]}
SRCDUR = {"IMG_2562": 2652.0, "IMG_2563": 3674.0, "IMG_2564": 2292.0, "IMG_2567": 4197.0}
VENC = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-fps_mode", "cfr", "-x264-params", "keyint=60:scenecut=0"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def dur(p):
    for args in (["-show_entries", "format=duration"],
                 ["-select_streams", "v:0", "-show_entries", "stream=duration"]):
        try:
            v = subprocess.check_output(["ffprobe", "-v", "error", *args, "-of", "csv=p=0", p], text=True).strip()
            if v and v != "N/A":
                return float(v)
        except Exception:
            pass
    # fallback: decode and count
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                          "-show_entries", "stream=nb_read_frames,r_frame_rate", "-of", "csv=p=0", p],
                         text=True, capture_output=True).stdout.strip().split(",")
    nb = int(out[0]); num, den = out[1].split("/"); return nb * float(den) / float(num)


def esc(t):  # drawtext text escaping
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


def norm_segment(idx, cid, title):
    s = snaps[cid]
    off = OFF[s["video"]]
    a = max(0.0, s["abs_start"] - PAD)
    e = min(SRCDUR[s["video"]] - 0.05, s["abs_end"] + PAD)
    if e <= a:
        raise SystemExit(f"BAD BOUNDS {cid}: {a}-{e} (src {SRCDUR[s['video']]})")
    seg_dur = e - a
    out = f"{EDIT}/seg2/seg_{idx}.mp4"
    title_draw = (f"drawtext=fontfile='{ARIALB}':text='{esc(title)}':fontcolor=white:fontsize=52:"
                  f"x=(w-text_w)/2:y=300:box=1:boxcolor=black@0.32:boxborderw=22:"
                  f"shadowcolor=black@0.7:shadowx=2:shadowy=2")
    vf = (f"[0:v]scale={W}:{H},setsar=1,fps={FPS},split=2[bg][fg];"
          f"[bg]scale=1296:2304,crop={W}:{H},boxblur=26:2,eq=brightness=-0.10[bgb];"
          f"[fg]crop={W}:{BANDH}:0:{off}[fgc];"
          f"[bgb][fgc]overlay=(W-w)/2:(H-h)/2,{title_draw}[v];"
          f"[0:a:0]afade=t=in:st=0:d=0.03,afade=t=out:st={seg_dur-0.03:.3f}:d=0.03[a]")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC[s["video"]],
                    "-t", f"{seg_dur:.3f}", "-filter_complex", vf, "-map", "[v]", "-map", "[a]",
                    *VENC, *AENC, out, "-y"], check=True)
    return out, dur(out), a


def make_intro(idx):
    out = f"{EDIT}/seg2/seg_{idx}.mp4"
    d = 1.6
    draw = (f"drawtext=fontfile='{ARIALB}':text='БУДНИ':fontcolor=white:fontsize=130:x=(w-text_w)/2:y=h/2-200,"
            f"drawtext=fontfile='{ARIALB}':text='КАВЕР-ГРУППЫ':fontcolor=white:fontsize=130:x=(w-text_w)/2:y=h/2-40,"
            f"drawtext=fontfile='{ARIALB}':text='без купюр':fontcolor=0xFF5A00:fontsize=70:x=(w-text_w)/2:y=h/2+160")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error",
                    "-f", "lavfi", "-i", f"color=c=0x0A0A0A:s={W}x{H}:r={FPS}:d={d}",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-t", f"{d}", "-vf", draw, *VENC, *AENC, "-shortest", out, "-y"], check=True)
    return out, dur(out)


def ass_ts(t):
    if t < 0: t = 0
    cs = int(round(t * 100)); h = cs // 360000; cs -= h * 360000
    m = cs // 6000; cs -= m * 6000; s = cs // 100; cs -= s * 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


segs = []
p, d = make_intro(0); segs.append((p, d, None, None))
for i, (cid, title) in enumerate(LINEUP, start=1):
    p, d, a = norm_segment(i, cid, title)
    segs.append((p, d, snaps[cid], a))
    print(f"seg{i} {cid}: {d:.2f}s")

durs = [d for (_, d, _, _) in segs]
N = len(segs)
S = [0.0] * N
acc = 0.0
for k in range(1, N):
    acc += durs[k - 1]; S[k] = acc - k * X
total = sum(durs) - (N - 1) * X
print(f"total ~ {total:.2f}s")

ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       f"Style: Def,Arial,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,470,1",
       "", "[Events]",
       "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for k in range(1, N):
    s = segs[k][2]; a = segs[k][3]; seg_dur = durs[k]
    for ln in s.get("lines", []):
        fs = ln["start"] - a; fe = ln["end"] - a
        fs = max(0.0, fs); fe = min(seg_dur, fe)
        if fe - fs < 0.3: fe = min(seg_dur, fs + 1.0)
        if fe <= 0.05 or fs >= seg_dur - 0.05: continue
        ass.append(f"Dialogue: 0,{ass_ts(S[k]+fs)},{ass_ts(S[k]+fe)},Def,,0,0,0,,{ln['text'].strip()}")
assfile = f"{EDIT}/master_v2.ass"
open(assfile, "w").write("\n".join(ass))

inputs = []
for (p, _, _, _) in segs: inputs += ["-i", p]
fc = []
vprev = "0:v"; acc = 0.0
for k in range(1, N):
    acc += durs[k - 1]; off = acc - k * X
    fc.append(f"[{vprev}][{k}:v]xfade=transition=fade:duration={X}:offset={off:.3f}[vx{k}]"); vprev = f"vx{k}"
aprev = "0:a"
for k in range(1, N):
    fc.append(f"[{aprev}][{k}:a]acrossfade=d={X}:c1=tri:c2=tri[ax{k}]"); aprev = f"ax{k}"
fc.append(f"[{vprev}]ass='{assfile}'[vout]")
out = f"{EDIT}/cherry_reel_v2.mp4"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
                "-map", "[vout]", "-map", f"[{aprev}]", *VENC, *AENC, "-movflags", "+faststart", out, "-y"], check=True)
print("RENDERED:", out, f"{dur(out):.2f}s")
