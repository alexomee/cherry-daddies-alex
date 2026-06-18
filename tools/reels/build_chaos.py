#!/usr/bin/env python3
"""Мультигэг-рилс «обычная репетиция кавер-группы» — динамичная сборка.

Гибрид build_gag.py + build_reel_v2.py:
- мультисорс (4 видео, incl горизонт 2567) → aspect-aware fit+blur (горизонт не сплющивается);
- ВНУТРИ гэга: непрерывное аудио + видео-субклипы (джамп-кат wide↔зум на человека);
- МЕЖДУ гэгами: slide-переход (xfade) + acrossfade аудио + whoosh-SFX;
- speed-ramp на сетап-гэгах (uniform на одношотовых wide);
- субтитры цветом по языку (англ.=Стив оранж, рус=белый);
- финал — CTA-аутро (анонс концерта, ctatxt/).

Запуск: python3 tools/reels/build_chaos.py
"""
import os, subprocess

REPO = os.path.expanduser("~/projects/cherry-daddies")
CONTENT = f"{REPO}/content/rehearsal-reels"
ASSETS = f"{CONTENT}/assets"
CTADIR = f"{CONTENT}/ctatxt"
WORK = os.path.expanduser("~/Downloads/rehearsal-reels")
DL = os.path.expanduser("~/Downloads")
SEG = f"{WORK}/segChaos"
os.makedirs(SEG, exist_ok=True)
WHOOSH = f"{ASSETS}/whoosh.wav"
EMOJI = f"{ASSETS}/emoji"
BADGE_XY = (770, 430)
W, H, FPS = 1080, 1920, 30
X = 0.30                  # длительность slide-перехода
WHV = 0.45                # громкость whoosh
CLEAN = os.environ.get("CLEAN") == "1"   # вариация: пиип поверх мата + маска в субтитрах
BEEP_HZ, BEEP_VOL = 1000, 0.33
BEEPSND = f"{ASSETS}/censor.wav"         # кастомный звук цензуры (TV); нет файла → синус
USE_SND = os.path.exists(BEEPSND)
CENSOR_SAMP = 35520                       # длина censor.wav в семплах @48k (для лупа длинных спанов)
ARIALB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
SRC = {v: f"{DL}/{v}.MOV" for v in ["IMG_2562", "IMG_2563", "IMG_2564", "IMG_2567"]}
SRCDUR = {"IMG_2562": 2652.0, "IMG_2563": 3674.0, "IMG_2564": 2292.0, "IMG_2567": 4197.0}
TRANS = ["slideleft", "slideright", "slideup", "smoothup", "slideleft", "slideright", "slideup", "smoothup", "circleopen"]
VENC = ["-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-fps_mode", "cfr", "-x264-params", "keyint=120:scenecut=0", "-an"]

# crop-боксы людей (проверены тест-вырезами)
ROMA_P = (370, 498, 430, 764)    # Рома, портрет 2562/2563/2564
DRUM_P = (690, 488, 430, 764)    # барабанщик/Стив, портрет
STEVE_H = (1450, 120, 360, 640)  # Стив (лысый, за кит), горизонт 2567
ROMA_H = (830, 80, 360, 640)     # Рома (клавиши), горизонт 2567
GUIT_2564 = (0, 470, 430, 764)   # гитарист стоит слева (ракурс 2273-2280, neochen)

ORANGE = r"&H0000A5FF"  # Стив (англ.)
WHITE = r"&H00FFFFFF"
CYAN = r"&H00FFFF00"    # Рома (клавишник)
YELLOW = r"&H0000FFFF"  # гитарист

# матерные слова (CLEAN): пиип-тон поверх + маска в субтитрах.
# Хранятся ТОЧНЫЕ word-границы (abs, виспер large-v3 + prime-prompt). Пип = [ws+LEAD, we+TAIL]:
# LEAD пропускает первую букву (слышно «б…»), TAIL плотно закрывает хвост. Коротко, точно по слову.
BEEP_LEAD, BEEP_TAIL = 0.05, 0.04
BEEPS = {
    "play_normal": [(1833.44, 1833.62)],                    # блять («сыграем блять нормально»)
    "letsdo":      [(1842.86, 1843.14)],                    # блять («нормально блять работать»)
    "drama":       [(354.92, 355.26)],                      # fucking
    "metronom":    [(913.08, 913.66)],                      # блядь
    "zaryadka":    [(2710.84, 2711.20), (2716.74, 2717.88)],  # нихуя, бляять
}
MASK = {"fucking": "f***", "блять": "б***", "блядь": "б***",
        "Нихуя": "Н***", "Бляяять": "Б***"}
# локальный буст промямленных слов (abs-окно, +дБ) — применяется в ОБЕИХ версиях
BOOST = {"letsdo": [(1843.18, 1844.05, 6.0)]}  # «работать» тихое/смазанное

# Каждый гэг: src, a, e (abs сек источника), title, speed, shots, lines.
# shots: (rel_start, rel_end, view, crop|None) — rel к a (РЕАЛЬНОЕ время, до speed).
#   view: "wide" | "zoom" | "cta".  rel_end=None → до e.
# lines: (abs_start, abs_end, text) в исходных секундах.
GAGS = [
    dict(id="play_normal", src="IMG_2564", a=1832.2, e=1836.9,
         title="Один разочек нормально, можно?", speed=1.2,
         shots=[(0.0, None, "wide", None)],
         lines=[(1832.6, 1834.3, "Давайте сейчас сыграем, блять, нормально"),
                (1834.3, 1835.6, "один разочек хотя бы, можно?"),
                (1835.6, 1836.8, "Давай. Let's try.")]),
    dict(id="letsdo", src="IMG_2564", a=1835.6, e=1845.9,
         title="Не трай — давайте ДУ!", speed=1.0,
         shots=[(0.0, 4.2, "wide", None), (4.2, None, "zoom", DRUM_P, "1f928")],
         lines=[(1836.3, 1838.0, "Не трай, давайте ду."),
                (1838.0, 1839.6, "Let's do."),
                (1839.6, 1841.0, "Do what?"),
                (1841.0, 1843.6, "Нормально, блять, работать."),
                (1843.8, 1845.8, "Normal what?")]),
    dict(id="drama", src="IMG_2567", a=344.0, e=359.8,
         title="Roma, just LISTEN to me!", speed=1.0,
         shots=[(0.0, 9.0, "wide", None), (9.0, 14.6, "zoom", STEVE_H, "1f624"), (14.6, None, "wide", None)],
         lines=[(350.0, 351.5, "That was the playback?"),
                (351.5, 353.0, "No, it..."),
                (353.0, 356.2, "Roma! Sometimes just fucking listen to me."),
                (356.2, 358.6, "I'm telling you it's on the keys channel.")]),
    dict(id="cmdq", src="IMG_2564", a=1575.6, e=1586.0,
         title="Случайно нажал Command+Q", speed=1.0,
         shots=[(0.0, 5.8, "wide", None), (5.8, None, "zoom", ROMA_P, "1f605")],
         lines=[(1577.0, 1579.0, "Всё вылетело?"),
                (1579.0, 1580.0, "Да."),
                (1580.0, 1581.0, "Серьёзно?"),
                (1581.0, 1583.5, "А, нажал Command+Q?"),
                (1583.5, 1585.0, "Бывает.")]),
    dict(id="metronom", src="IMG_2567", a=904.5, e=914.6,
         title="«Тоже мне, отмазался»", speed=1.15,
         shots=[(0.0, None, "wide", None)],
         lines=[(905.5, 906.9, "Ну и что, что без метронома?"),
                (906.9, 909.0, "У тебя же арпеджиатор как метроном."),
                (911.5, 913.6, "Тоже мне, отмазался, блядь.")]),
    dict(id="zaryadka", src="IMG_2563", a=2706.8, e=2718.4,
         title="«Нихуя, у меня зарядка»", speed=1.0,
         shots=[(0.0, 9.5, "wide", None), (9.5, None, "zoom", ROMA_P, "1f62b")],
         lines=[(2708.4, 2710.45, "Рома: «когда сядет ноутбук — пойдём домой»", WHITE),
                (2710.55, 2711.95, "А я говорю: «Нихуя, у меня зарядка»", WHITE),
                (2712.35, 2713.2, "А он говорит: «Не надо!»", CYAN),
                (2714.0, 2716.6, "Я надеюсь, это твоя зарядка", WHITE),
                (2716.7, 2717.9, "Бляяять", CYAN)]),
    dict(id="neochen", src="IMG_2564", a=2273.3, e=2280.3,
         title="«Послушать? — Не очень»", speed=1.0,
         shots=[(0.0, 3.0, "wide", None), (3.0, 5.2, "zoom", GUIT_2564, "1f644"), (5.2, None, "wide", None)],
         lines=[(2274.5, 2276.5, "О, хотите послушать, что получилось?", WHITE),
                (2276.5, 2278.0, "Не очень.", YELLOW),
                (2278.0, 2280.0, "Кому это надо.", WHITE)]),
]
CTA = dict(id="cta", src="IMG_2564", a=84.0, e=105.0, speed=1.0,  # финал: перформанс песни + анонс концерта
           audio_src=f"{ASSETS}/final_solnyshko.wav")  # студийная Солнышко, выровнена video84->Солнышко96.20 (хрома)


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


def title_draw(title):
    return (f"drawtext=fontfile='{ARIALB}':text='{esc(title)}':fontcolor=white:fontsize=50:"
            f"x=(w-text_w)/2:y=300:box=1:boxcolor=black@0.34:boxborderw=22:"
            f"shadowcolor=black@0.7:shadowx=2:shadowy=2")


CTA_DRAW = (
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l1.txt':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=330:box=1:boxcolor=0xE6177B@0.85:boxborderw=20:shadowcolor=black@0.6:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{ARIAL}':textfile='{CTADIR}/l2.txt':fontcolor=white:fontsize=33:x=(w-text_w)/2:y=440:box=1:boxcolor=black@0.45:boxborderw=12,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l3.txt':fontcolor=white:fontsize=66:x=(w-text_w)/2:y=1500:box=1:boxcolor=black@0.5:boxborderw=18:shadowcolor=black@0.7:shadowx=2:shadowy=2,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l4.txt':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=1600:box=1:boxcolor=black@0.5:boxborderw=14,"
    f"drawtext=fontfile='{ARIALB}':textfile='{CTADIR}/l5.txt':fontcolor=white:fontsize=58:x=(w-text_w)/2:y=1685:box=1:boxcolor=0xE6177B@0.9:boxborderw=18")


def view_filter(view, crop, draw, speed, lbl):
    sp = "" if abs(speed - 1.0) < 1e-3 else f"setpts=PTS/{speed},"
    if view == "wide":
        return (f"[0:v]fps={FPS},setsar=1,{sp}split=2[s1][s2];"
                f"[s1]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
                f"[s2]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.10[bg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,{draw}[{lbl}]")
    if view == "cta":
        return (f"[0:v]fps={FPS},setsar=1,{sp}scale={W}:{H}:force_original_aspect_ratio=decrease,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,{CTA_DRAW}[{lbl}]")
    cx, cy, cw, ch = crop
    return f"[0:v]fps={FPS},setsar=1,{sp}crop={cw}:{ch}:{cx}:{cy},scale={W}:{H},setsar=1,{draw}[{lbl}]"


def encode_shot(tag, src, s, e, view, crop, draw, speed, badge=None):
    out = f"{SEG}/sh_{tag}.mp4"
    d = e - s
    ins = ["-ss", f"{s:.3f}", "-t", f"{d:.3f}", "-i", SRC[src]]
    if badge:
        fc = (view_filter(view, crop, draw, speed, "base") +
              f";[1:v]scale=240:-1,format=rgba[bdg];[base][bdg]overlay={BADGE_XY[0]}:{BADGE_XY[1]}[v]")
        ins += ["-i", f"{EMOJI}/{badge}.png"]
    else:
        fc = view_filter(view, crop, draw, speed, "v")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *ins,
                    "-filter_complex", fc, "-map", "[v]", *VENC, out, "-y"], check=True)
    return out


def build_gag_seg(gi, g):
    """Видео-субклипы (с зумами) → concat; непрерывное аудио (atempo при speed) → mux. Возврат seg-файл + dur."""
    a, e, sp = g["a"], g["e"], g["speed"]
    is_cta = g.get("id") == "cta"
    ttl = g.get("title", "")
    if CLEAN:
        for bad, m in MASK.items():
            ttl = ttl.replace(bad, m)
    draw = None if is_cta else title_draw(ttl)
    vparts = []
    if is_cta:
        vparts.append(encode_shot(f"{gi:02d}_0", g["src"], a, e, "cta", None, None, sp))
    else:
        for si, sh in enumerate(g["shots"]):
            rs, re_, view, crop = sh[0], sh[1], sh[2], sh[3]
            badge = sh[4] if len(sh) > 4 else None
            ss = a + rs
            se = a + (re_ if re_ is not None else (e - a))
            se = min(se, SRCDUR[g["src"]] - 0.03)
            vparts.append(encode_shot(f"{gi:02d}_{si}", g["src"], ss, se, view, crop, draw, sp, badge))
    # concat video-only
    gvid = f"{SEG}/g_{gi:02d}_v.mp4"
    if len(vparts) == 1:
        gvid = vparts[0]
    else:
        lf = f"{SEG}/g_{gi:02d}.txt"
        open(lf, "w").write("\n".join(f"file '{p}'" for p in vparts))
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0", "-i", lf,
                        "-c", "copy", gvid, "-y"], check=True)
    # continuous audio (+ пиип поверх мата в CLEAN)
    ad = (e - a)
    odur = ad / sp
    gaud = f"{SEG}/g_{gi:02d}_a.wav"
    tempo = f"atempo={sp}," if abs(sp - 1.0) > 1e-3 else ""
    fades = f"afade=t=in:st=0:d=0.03,afade=t=out:st={odur-0.03:.3f}:d=0.03"
    boost = "".join(f"volume={g_db}dB:enable='between(t,{(bs-a)/sp:.3f},{(be-a)/sp:.3f})',"
                    for bs, be, g_db in BOOST.get(g["id"], []))
    asrc = g.get("audio_src")
    beeps = BEEPS.get(g["id"], []) if CLEAN else []
    if asrc:   # внешнее аудио (студийная запись), уже выровнено и нормализовано — берём 1:1 с фейдами
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", "0", "-i", asrc, "-t", f"{ad:.3f}",
                        "-map", "0:a:0", "-af", fades, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", gaud, "-y"], check=True)
    elif beeps:
        spans = [((ws + BEEP_LEAD - a) / sp, (we + BEEP_TAIL - a) / sp) for ws, we in beeps]
        enable = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in spans)
        ins = ["-ss", f"{a:.3f}", "-t", f"{ad:.3f}", "-i", SRC[g["src"]]]
        fc = [f"[0:a]{tempo}{boost}volume=0:enable='{enable}',{fades}[sp]"]
        mix = ["[sp]"]
        for k, (s, e) in enumerate(spans):
            d = e - s
            if USE_SND:
                ins += ["-i", BEEPSND]
                fc.append(f"[{1+k}:a]aloop=loop=-1:size={CENSOR_SAMP},atrim=0:{d:.3f},asetpts=PTS-STARTPTS,"
                          f"afade=t=in:st=0:d=0.004,afade=t=out:st={max(d-0.004,0.0):.3f}:d=0.004,"
                          f"aresample=48000,adelay={int(s*1000)}:all=1,volume={BEEP_VOL}[b{k}]")
            else:
                ins += ["-f", "lavfi", "-i", f"sine=frequency={BEEP_HZ}:duration={d:.3f}:sample_rate=48000"]
                fc.append(f"[{1+k}:a]adelay={int(s*1000)}:all=1,volume={BEEP_VOL}[b{k}]")
            mix.append(f"[b{k}]")
        fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:dropout_transition=0[a]")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *ins, "-filter_complex", ";".join(fc),
                        "-map", "[a]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", gaud, "-y"], check=True)
    else:
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{a:.3f}", "-i", SRC[g["src"]], "-t", f"{ad:.3f}",
                        "-map", "0:a:0", "-af", tempo + boost + fades, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", gaud, "-y"], check=True)
    # mux
    seg = f"{SEG}/seg_{gi:02d}.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", gvid, "-i", gaud,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                    "-shortest", seg, "-y"], check=True)
    return seg, dur(seg)


def ass_ts(t):
    if t < 0: t = 0
    cs = int(round(t * 100)); h = cs // 360000; cs -= h * 360000
    m = cs // 6000; cs -= m * 6000; s = cs // 100; cs -= s * 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def line_color(text):
    lat = sum(ch.isascii() and ch.isalpha() for ch in text)
    cyr = sum('а' <= ch.lower() <= 'я' or ch.lower() == 'ё' for ch in text)
    return ORANGE if lat > cyr else WHITE


# ---- build all gag segments ----
ALL = GAGS + [CTA]
segs = []
for gi, g in enumerate(ALL):
    p, d = build_gag_seg(gi, g)
    segs.append((p, d, g))
    print(f"seg{gi:02d} {g['id']:12} {d:.2f}s  speed={g['speed']}")

durs = [d for (_, d, _) in segs]
N = len(segs)
# позиции стыков (как в build_reel_v2): S[k] — старт seg k в финальном таймлайне
S = [0.0] * N
acc = 0.0
for k in range(1, N):
    acc += durs[k - 1]; S[k] = acc - k * X
total = sum(durs) - (N - 1) * X
print(f"total ~ {total:.2f}s")

# ---- subtitles (по seg, с учётом speed маппинг line→seg-время) ----
ass = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0", "",
       "[V4+ Styles]",
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
       f"Style: Def,Arial,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,90,90,300,1",
       "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
for k in range(N):
    g = segs[k][2]; seg_dur = durs[k]
    if g.get("id") == "cta":
        continue
    a, sp = g["a"], g["speed"]
    for ln in g["lines"]:
        ls, le, text = ln[0], ln[1], ln[2]
        col = ln[3] if len(ln) > 3 else line_color(text)
        fs = (ls - a) / sp
        fe = (le - a) / sp
        fs = max(0.0, fs); fe = min(seg_dur, fe)
        if fe - fs < 0.3: fe = min(seg_dur, fs + 1.0)
        if fe <= 0.05 or fs >= seg_dur - 0.05: continue
        shown = text.strip()
        if CLEAN:
            for bad, m in MASK.items():
                shown = shown.replace(bad, m)
        txt = "{\\c" + col + "&}" + shown
        ass.append(f"Dialogue: 0,{ass_ts(S[k]+fs)},{ass_ts(S[k]+fe)},Def,,0,0,0,,{txt}")
assfile = f"{WORK}/chaos_v4{'_clean' if CLEAN else ''}.ass"
open(assfile, "w").write("\n".join(ass))

# ---- final: xfade(slide) video + acrossfade audio + whoosh на стыках + subs ----
inputs = []
for (p, _, _) in segs:
    inputs += ["-i", p]
for _ in range(N - 1):
    inputs += ["-i", WHOOSH]
fc = []
vprev = "0:v"; acc = 0.0
for k in range(1, N):
    acc += durs[k - 1]; off = acc - k * X
    tr = TRANS[(k - 1) % len(TRANS)]
    fc.append(f"[{vprev}][{k}:v]xfade=transition={tr}:duration={X}:offset={off:.3f}[vx{k}]"); vprev = f"vx{k}"
aprev = "0:a"
for k in range(1, N):
    fc.append(f"[{aprev}][{k}:a]acrossfade=d={X}:c1=tri:c2=tri[ax{k}]"); aprev = f"ax{k}"
# whoosh при каждом переходе
wl = []
for j in range(N - 1):
    inp = N + j
    ms = max(0, int((S[j + 1] - 0.04) * 1000))
    fc.append(f"[{inp}:a]adelay={ms}:all=1,volume={WHV}[w{j}]"); wl.append(f"[w{j}]")
fc.append(f"[{aprev}]{''.join(wl)}amix=inputs={N}:normalize=0:dropout_transition=0[a]")
fc.append(f"[{vprev}]ass='{assfile}'[vout]")
out = f"{WORK}/cherry_chaos_v4{'_clean' if CLEAN else ''}.mp4"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
                "-map", "[vout]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                "-movflags", "+faststart", "-shortest", out, "-y"], check=True)
print(f"\nRENDERED: {out}  {dur(out):.2f}s")
