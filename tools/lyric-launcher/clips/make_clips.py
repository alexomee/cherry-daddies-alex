#!/usr/bin/env python3
"""Generate POC clips: NN.mp4 (black surface) + NN.ass (timed lyrics).

The launcher loads NN.mp4 on Program Change N and attaches NN.ass; mpv's
own libass renders the lyric lines on the clip's timeline. This mirrors the
real design: background = video, lyrics = an editable subtitle track (no
re-encode to change words). ffmpeg here only makes a plain black clip
(this build has no drawtext/subtitles filters, but libx264 works).
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720

# demo songs: (PC number, title, [(start_sec, line), ...], duration)
SONGS = [
    (1, "SONG 1", [(1.0, "line one - enters at 1s"),
                   (4.0, "line two - at 4s"),
                   (7.0, "line three - at 7s")], 10),
    (2, "SONG 2", [(1.0, "verse line A (1s)"),
                   (3.0, "verse line B (3s)"),
                   (6.0, "chorus hits (6s)")], 10),
    (3, "SONG 3", [(2.0, "intro phrase (2s)"),
                   (4.0, "build up (4s)"),
                   (8.0, "drop (8s)")], 10),
]

ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial,54,&H0000FFFF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,0,8,40,40,40,1
Style: Now,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,4,0,5,60,60,40,1
Style: Next,Arial,44,&H00AAAAAA,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,60,60,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def t(sec):
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def dialogue(start, end, style, text, margin_v=None):
    mv = "" if margin_v is None else str(margin_v)
    mvfield = mv if mv else "0"
    return f"Dialogue: 0,{t(start)},{t(end)},{style},,0,0,{mvfield},,{text}\n"


def make_ass(path, title, lines, dur):
    body = ASS_HEAD.format(w=W, h=H)
    # persistent title, top
    body += dialogue(0, dur, "Title", title)
    # each line shows from its cue; the *current* line is big-centered ("Now"),
    # the upcoming one is dim below ("Next"). Karaoke-ish reveal = sync proof.
    for i, (start, line) in enumerate(lines):
        nxt = lines[i + 1][0] if i + 1 < len(lines) else dur
        body += dialogue(start, nxt, "Now", line)          # current line, centered
        if i + 1 < len(lines):
            body += dialogue(start, nxt, "Next", lines[i + 1][1], margin_v=120)
    with open(path, "w") as f:
        f.write(body)


def make_black(path, dur):
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={dur}:r=30",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", path],
        check=True)


def main():
    for pc, title, lines, dur in SONGS:
        mp4 = os.path.join(HERE, f"{pc:02d}.mp4")
        ass = os.path.join(HERE, f"{pc:02d}.ass")
        make_black(mp4, dur)
        make_ass(ass, title, lines, dur)
        print(f"wrote {os.path.basename(mp4)} + {os.path.basename(ass)}")


if __name__ == "__main__":
    main()
