#!/usr/bin/env python3
"""«Другая нота» v2 — динамичная версия.
- 5 бит (джамп-каты, офтоп вырезан), непрерывное аудио ВНУТРИ бита (фейды только на стыках бит).
- Реакшн-вставки (зум Рома/барабанщик/кот) поверх непрерывного диалога + рисованные бейджи.
- Субтитры по говорящему разным цветом (Таня белый, гитарист жёлтый, Рома голубой).
- whoosh на джамп-катах.
Запуск: python3 build_vtoraya_v2.py
"""
import json, os, subprocess

# Пути: стейт/ассеты ← репо (версионируются/регенерируются), рендеры → ~/Downloads (тяжёлое, вне git)
REPO = os.path.expanduser("~/projects/cherry-daddies")
CONTENT = f"{REPO}/content/rehearsal-reels"        # стейт: _*.json, ctatxt/, assets/
ASSETS = f"{CONTENT}/assets"                        # badges/ emoji/ whoosh.wav (regen: tools/reels/setup_assets.sh)
WORK = os.path.expanduser("~/Downloads/rehearsal-reels")   # рендеры + seg-интермедиаты (вне git)
DL = os.path.expanduser("~/Downloads")
EDIT = WORK
SEG = f"{WORK}/segV3"
os.makedirs(SEG, exist_ok=True)
SRC = f"{DL}/IMG_2562.MOV"
BADGES = f"{ASSETS}/emoji"
WHOOSH = f"{ASSETS}/whoosh.wav"
W, H, FPS = 1080, 1920, 30
ARIALB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
CTADIR = f"{CONTENT}/ctatxt"
TITLE = "«Сыграй повеселее»"
VENC = ["-c:v", "libx264", "-crf", "19", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-fps_mode", "cfr", "-x264-params", "keyint=120:scenecut=0", "-an"]

BEATS = {0: (865.0, 876.5), 1: (879.0, 890.5), 2: (893.5, 909.5), 3: (957.5, 969.5),
         4: (970.5, 978.8), 5: (1210.0, 1228.0)}  # beat5 = аутро-CTA (анонс концерта)
# (beat, src_start, src_end, view, badge-emoji-codepoint)
SHOTS = [
    (0, 865.0, 873.2, "wide", None),       # вопрос / повеселее / сильно отличается
    (0, 873.2, 876.5, "roma", "1f914"),    # «У Тани важнее вопрос» → реакция Рома 🤔
    (1, 879.0, 890.5, "roma", None),       # большой план Рома (бикеринг)
    (2, 893.5, 895.5, "roma", None),       # ...держится до «послушайте»
    (2, 895.5, 902.0, "wide", None),       # «послушайте, состоит из двух частей, первая похожа»
    (2, 902.0, 906.2, "drum", "1f928"),    # барабанщик ДЛИННЕЕ 🤨 (не втыкает русский)
    (2, 906.2, 909.5, "wide", None),       # «должна быть другая?»
    (3, 957.5, 969.5, "wide", None),       # слушают оригинал
    (4, 970.5, 973.0, "wide", None),       # теперь звучит
    (4, 973.0, 974.8, "roma", "1f605"),    # ниже играл → Рома 😅
    (4, 974.8, 976.6, "cat", "1f3b6"),     # кот 🎶
    (4, 976.6, 978.8, "wide", None),
    (5, 1210.0, 1228.0, "cta", None),      # аутро: We Found Love + анонс концерта
]
CROPS = {"roma": (370, 498, 430, 764), "drum": (690, 488, 430, 764), "cat": (95, 1051, 320, 569)}
COL = {"Таня": r"&H00FFFFFF", "гитарист": r"&H0000FFFF", "Рома": r"&H00FFFF00", "барабанщик": r"&H00FFFFFF"}
BADGE_XY = (770, 430)

caps = {int(k): v for k, v in json.load(open(f"{CONTENT}/_beat_caps.json")).items()}
# beat0 гитарист: пользовательская формулировка
caps[0] = [l for l in caps[0] if l["speaker"] != "гитарист"]
caps[0].append({"abs_start": 873.2, "abs_end": 875.6, "speaker": "гитарист", "text": "У Тани важнее вопрос"})
caps[5] = []  # финал — без диалога (музыка/вокал)


def dur(p):
    for a in (["-show_entries", "format=duration"], ["-select_streams", "v:0", "-show_entries", "stream=duration"]):
        try:
            v = subprocess.check_output(["ffprobe", "-v", "error", *a, "-of", "csv=p=0", p], text=True).strip()
            if v and v != "N/A":
                return float(v)
        except Exception:
            pass
    return 0.0


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")


TITLE_DRAW = (f"drawtext=fontfile='{ARIALB}':text='{esc(TITLE)}':fontcolor=white:fontsize=50:"
              f"x=(w-text_w)/2:y=330:box=1:boxcolor=black@0.34:boxborderw=22:shadowcolor=black@0.7:shadowx=2:shadowy=2")

CTA_DRAW = (
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l1.txt':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=330:box=1:boxcolor=0xE6177B@0.85:boxborderw=20:shadowcolor=black@0.6:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{ARIAL}':textfile='{CTADIR}/l2.txt':fontcolor=white:fontsize=33:x=(w-text_w)/2:y=440:box=1:boxcolor=black@0.45:boxborderw=12,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l3.txt':fontcolor=white:fontsize=66:x=(w-text_w)/2:y=1500:box=1:boxcolor=black@0.5:boxborderw=18:shadowcolor=black@0.7:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l4.txt':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=1600:box=1:boxcolor=black@0.5:boxborderw=14,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l5.txt':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=1685:box=1:boxcolor=0xE6177B@0.9:boxborderw=18")


def encode_shot(i, b, s, e, view, badge):
    out = f"{SEG}/s_{i:02d}.mp4"
    d = e - s
    if view == "wide":
        vf = (f"[0:v]fps={FPS},setsar=1,split=2[s1][s2];"
              f"[s1]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
              f"[s2]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.10[bg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{TITLE_DRAW}[v]")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                        "-filter_complex", vf, "-map", "[v]", *VENC, out, "-y"], check=True)
    elif view == "cta":
        vf = (f"[0:v]fps={FPS},setsar=1,scale={W}:{H}:force_original_aspect_ratio=decrease,"
              f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,{CTA_DRAW}[v]")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                        "-filter_complex", vf, "-map", "[v]", *VENC, out, "-y"], check=True)
    else:
        cx, cy, cw, ch = CROPS[view]
        base = f"[0:v]fps={FPS},setsar=1,crop={cw}:{ch}:{cx}:{cy},scale={W}:{H},setsar=1,{TITLE_DRAW}"
        if badge:
            bx, by = BADGE_XY
            vf = base + f"[base];[1:v]scale=240:-1,format=rgba[bdg];[base][bdg]overlay={bx}:{by}[v]"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                            "-i", f"{BADGES}/{badge}.png",
                            "-filter_complex", vf, "-map", "[v]", *VENC, out, "-y"], check=True)
        else:
            vf = base + "[v]"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC,
                            "-filter_complex", vf, "-map", "[v]", *VENC, out, "-y"], check=True)
    return out, dur(out)


# --- stage C: video subclips ---
vparts = []
for i, (b, s, e, view, badge) in enumerate(SHOTS):
    p, d = encode_shot(i, b, s, e, view, badge)
    vparts.append(p)
    print(f"shot {i:02d} beat{b} {view:5} {d:.2f}s")

# --- stage D: concat video-only ---
listf = f"{SEG}/list.txt"
open(listf, "w").write("\n".join(f"file '{p}'" for p in vparts))
video_only = f"{SEG}/video_only.mp4"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0", "-i", listf,
                "-c", "copy", video_only, "-y"], check=True)

# --- stage A/B: per-beat continuous audio (fades at beat edges) -> master ---
beat_dur = {}
awavs = []
for b in sorted(BEATS):
    bs, be = BEATS[b]; bd = be - bs; beat_dur[b] = bd
    aw = f"{SEG}/a_{b}.wav"
    af = f"afade=t=in:st=0:d=0.03,afade=t=out:st={bd-0.03:.3f}:d=0.03"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{bs:.3f}", "-i", SRC, "-t", f"{bd:.3f}",
                    "-map", "0:a:0", "-af", af, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", aw, "-y"], check=True)
    awavs.append(aw)
alist = f"{SEG}/alist.txt"
open(alist, "w").write("\n".join(f"file '{p}'" for p in awavs))
master = f"{SEG}/master.wav"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0", "-i", alist,
                "-c", "copy", master, "-y"], check=True)

# beat output start times (cumulative)
O = {}; acc = 0.0
for b in sorted(BEATS):
    O[b] = acc; acc += beat_dur[b]
total = acc
boundaries = [O[b] + beat_dur[b] for b in sorted(BEATS)][:-1]  # jump-cut times (end of beats 0..3)


def ass_ts(t):
    if t < 0: t = 0
    cs = int(round(t * 100)); h = cs // 360000; cs -= h * 360000
    m = cs // 6000; cs -= m * 6000; s = cs // 100; cs -= s * 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       f"Style: Def,Arial,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,80,80,250,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for b in sorted(BEATS):
    bs, be = BEATS[b]
    for ln in sorted(caps[b], key=lambda x: x["abs_start"]):
        os_ = (ln["abs_start"] - bs) + O[b]
        oe_ = (ln["abs_end"] - bs) + O[b]
        oe_ = min(oe_, O[b] + beat_dur[b])
        if oe_ - os_ < 0.3: oe_ = os_ + 1.0
        color = COL.get(ln["speaker"], r"&H00FFFFFF")
        txt = "{\\c" + color + "&}" + ln["text"].strip()
        ass.append(f"Dialogue: 0,{ass_ts(os_)},{ass_ts(oe_)},Def,,0,0,0,,{txt}")
assfile = f"{EDIT}/vtoraya_v3.ass"
open(assfile, "w").write("\n".join(ass))

# --- stage E: final = video + master audio + whoosh at boundaries + subtitles ---
inputs = ["-i", video_only, "-i", master]
for _ in boundaries:
    inputs += ["-i", WHOOSH]
fc = []
wl = []
for j, bt in enumerate(boundaries):
    ms = max(0, int((bt - 0.05) * 1000))
    fc.append(f"[{2+j}:a]adelay={ms}:all=1,volume=0.5[w{j}]"); wl.append(f"[w{j}]")
fc.append(f"[1:a]{''.join(wl)}amix=inputs={1+len(boundaries)}:normalize=0:dropout_transition=0[a]")
fc.append(f"[0:v]ass='{assfile}'[v]")
out = f"{EDIT}/cherry_vtoraya_v3.mp4"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
                "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", "-shortest", out, "-y"], check=True)
print(f"\ntotal ~{total:.2f}s  RENDERED: {out}  {dur(out):.2f}s")
