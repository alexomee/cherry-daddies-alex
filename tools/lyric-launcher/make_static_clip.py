#!/usr/bin/env python3
"""Static full-lyrics clip (NN.mp4 + NN.ass) — the fallback for songs with no
JamZone timing. Shows the WHOLE song on one screen the moment the set is armed:
columns, the repeated chorus collapsed to `…  ×N`, auto-fit font. No timing.

Usage:
  make_static_clip.py --index 12 --title "Солнышко" --lyrics solnyshko.txt
Lyrics file = plain text, one line per line (blank lines are ignored — repeats
are detected automatically). Writes clips/<NN>.mp4 + clips/<NN>.ass.
"""
import argparse
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720
DUR = 6.0  # static — arm pauses it on frame 0


def longest_repeat(lines):
    """Find the longest block (len>=2) that occurs 2+ times (non-overlapping).
    Returns (length, [start indices]) or None."""
    n = len(lines)
    best_len, best_starts = 0, None
    for i in range(n):
        for j in range(i + 1, n):
            k = 0
            while j + k < n and lines[i + k] == lines[j + k] and i + k < j:
                k += 1
            if k >= 2 and k > best_len:
                # collect all non-overlapping occurrences of this exact block
                block = lines[i:i + k]
                starts, p = [], 0
                while p + k <= n:
                    if lines[p:p + k] == block:
                        starts.append(p); p += k
                    else:
                        p += 1
                if len(starts) >= 2:
                    best_len, best_starts = k, starts
    return (best_len, best_starts) if best_starts else None


def dedup_repeats(lines):
    """Collapse repeated blocks (the chorus) to a single occurrence marked ×N,
    with blank-line separators around them for readability."""
    lines = [l for l in lines if l.strip()]  # flatten: drop blanks
    blanks = set()                            # indices (in current list) to blank-pad
    while True:
        r = longest_repeat(lines)
        if not r:
            break
        L, starts = r
        count = len(starts)
        lines[starts[0] + L - 1] = lines[starts[0] + L - 1] + f"  ×{count}"
        for p in sorted(starts[1:], reverse=True):
            del lines[p:p + L]
        # mark stanza breaks around the kept block
        s = starts[0]
        blanks.update({s, s + L})
        # rebuild with explicit blank markers, then re-detect (positions shifted)
        out, marked = [], set()
        for idx, l in enumerate(lines):
            if idx in blanks and out and out[-1] != "":
                out.append("")
            out.append(l)
        lines = out
        blanks = set()  # already materialised
    return lines


def collapse_consecutive(lines):
    out, i = [], 0
    while i < len(lines):
        if lines[i] == "":
            out.append(""); i += 1; continue
        n = 1
        while i + n < len(lines) and lines[i + n] == lines[i]:
            n += 1
        out.append(f"{lines[i]}  ×{n}" if n > 1 else lines[i])
        i += n
    while out and out[-1] == "":
        out.pop()
    return out


def esc(s):
    return s.replace("{", "(").replace("}", ")").strip()


def ass(path, title, columns, fontsize):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial,40,&H0000D7FF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,0,8,40,40,20,1
Style: Lyr,Arial,{fontsize},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    end = "9:59:59.99"
    body = head
    body += f"Dialogue: 0,0:00:00.00,{end},Title,,0,0,0,,{esc(title)}\n"
    topy = 84
    for x, col in columns:
        text = "\\N".join(esc(l) if l else "" for l in col)
        body += f"Dialogue: 0,0:00:00.00,{end},Lyr,,0,0,0,,{{\\pos({x},{topy})}}{text}\n"
    open(path, "w").write(body)


def layout(lines):
    """Columns + fontsize to fit one 720p screen. Splits between columns on a
    blank line where possible."""
    avail_h = H - 100
    for ncol in (1, 2, 3):
        per = (len(lines) + ncol - 1) // ncol
        fs = int(min(46, avail_h / (max(per, 1) * 1.18)))
        if fs >= 22 or ncol == 3:
            fs = max(15, fs)
            margin, gap = 70, 36
            colw = (W - 2 * margin - (ncol - 1) * gap) // ncol
            cols, start = [], 0
            for k in range(ncol):
                end = start + per
                # nudge the split to the nearest blank line within +/-2
                if k < ncol - 1:
                    for d in (0, 1, -1, 2, -2):
                        if 0 < end + d < len(lines) and lines[end + d] == "":
                            end = end + d + 1; break
                chunk = lines[start:end]
                while chunk and chunk[0] == "":
                    chunk = chunk[1:]
                if chunk:
                    cols.append((margin + k * (colw + gap), chunk))
                start = end
            return cols, fs
    return [(70, lines)], 22


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--lyrics", required=True, help="plain-text lyrics file")
    args = ap.parse_args()

    raw = [l.rstrip() for l in open(args.lyrics, encoding="utf-8")]
    lines = collapse_consecutive(dedup_repeats(raw))

    cols, fs = layout(lines)
    mp4 = os.path.join(HERE, "clips", f"{args.index:02d}.mp4")
    asp = os.path.join(HERE, "clips", f"{args.index:02d}.ass")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={DUR}:r=30",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", mp4], check=True)
    ass(asp, args.title, cols, fs)
    print(f"clip {args.index:02d}: {len([l for l in lines if l])} lyric lines, "
          f"{len(cols)} col(s), font {fs}")


if __name__ == "__main__":
    main()
