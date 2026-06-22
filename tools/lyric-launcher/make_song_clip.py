#!/usr/bin/env python3
"""Build a real lyric clip (NN.mp4 + NN.ass) for one song from JamZone tiles.

Lyrics + per-syllable timing come straight from JamZone's tiles.json (the data
the app uses to highlight words). Times are shifted by the render's offset_sec
(auto-render/timeline.json) so the clip sits on the SAME timeline MainStage
plays (click / pb-other / all.wav share it).

Usage:
  make_song_clip.py --cat cat_7372 --index 10 \
      --song "/Users/alex/projects/cherry-daddies/music/songs/Alice Deejay - Better Off Alone" \
      --title "Better Off Alone"

Writes clips/<NN>.mp4 (black, song length) + clips/<NN>.ass (timed lines).
"""
import argparse
import json
import os
import subprocess
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
JAMS = os.path.expanduser(
    "~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
    "Application Support/com.recisio.jamzone.ios/jams")
W, H = 1280, 720


def key_for(cat):
    return hashlib.md5(cat.encode()).hexdigest().encode().hex()


def dj(cat, name):
    d = open(os.path.join(JAMS, cat, name), "rb").read()
    out = subprocess.run(["openssl", "enc", "-aes-256-cbc", "-d", "-K", key_for(cat),
                          "-iv", d[:16].hex()], input=d[16:], capture_output=True).stdout
    return json.loads(out)


def lead_color(tiles):
    """Lead voice = colour in the most distinct sections; tie-break syllables."""
    info = {}
    for t in tiles:
        cap = t.get("sectionCaption") or ""
        w = t.get("words")
        if not isinstance(w, dict):
            continue
        for col, groups in w.items():
            secs, n = info.setdefault(col, [set(), 0])[0:2]
            info[col][0].add(cap)
            info[col][1] += sum(len(g.get("syllabes", [])) for g in groups)
    if not info:
        return None
    return max(info, key=lambda c: (len(info[c][0]), info[c][1]))


def words_for_color(tiles, color):
    """Flat [(start, end, word)] for one voice, time-ordered (whole words)."""
    out = []
    for t in tiles:
        w = t.get("words")
        if not isinstance(w, dict):
            continue
        for col, groups in w.items():
            if col != color:
                continue
            for g in groups:
                cur = {}  # word_id -> [start, end, text]
                order = []
                for s in g.get("syllabes", []):
                    wid = s.get("word_id")
                    st = s.get("start"); en = s.get("end", st)
                    if wid not in cur:
                        cur[wid] = [st, en, ""]; order.append(wid)
                    cur[wid][0] = min(cur[wid][0], st) if cur[wid][0] is not None else st
                    cur[wid][1] = max(cur[wid][1] or st, en or st)
                    cur[wid][2] += s.get("text", "")
                for wid in order:
                    st, en, tx = cur[wid]
                    if st is not None:
                        out.append((st, en, tx))
    out.sort(key=lambda e: e[0])
    return out


def syllables_per_color(tiles):
    n = {}
    for t in tiles:
        w = t.get("words")
        if not isinstance(w, dict):
            continue
        for col, groups in w.items():
            n[col] = n.get(col, 0) + sum(len(g.get("syllabes", [])) for g in groups)
    return n


def lead_words(tiles, frac=0.5, dedup_sec=0.25):
    """Merged lead lyric stream. Duets (e.g. t.A.T.u.) split verses across two
    colours while singing choruses in unison, so a single lead colour drops a
    whole verse. Take every colour with >= frac of the busiest colour's
    syllables (co-leads, not sparse backing) and merge; collapse near-simultaneous
    identical words (the unison choruses) so they show once.
    Returns (words=[(start,end,text)], colors_used)."""
    syl = syllables_per_color(tiles)
    if not syl:
        return [], []
    mx = max(syl.values())
    cols = sorted((c for c, n in syl.items() if n >= frac * mx),
                  key=lambda c: -syl[c])
    if len(cols) <= 1:
        return words_for_color(tiles, cols[0]), cols
    merged = sorted((w for c in cols for w in words_for_color(tiles, c)),
                    key=lambda e: e[0])
    out = []
    for st, en, tx in merged:
        key = tx.strip().lower()
        if any(abs(ost - st) <= dedup_sec and otx.strip().lower() == key
               for ost, _, otx in out[-8:]):
            continue
        out.append((st, en, tx))
    return out, cols


def parse_time(s):
    """Parse 'm:ss.s' (e.g. '0:21.0') OR plain seconds into a float of seconds."""
    s = s.strip()
    if ":" in s:
        mm, ss = s.rsplit(":", 1)
        return int(mm) * 60 + float(ss)
    return float(s)


def parse_lines_table(path):
    """Parse a manual '<time>\\t<line>' TSV into [(start, end, text), ...].

    time = 'm:ss.s' or plain seconds (playback seconds, used directly — no
    offset). Each line's end = the next line's start; the last line's end =
    its own start + 3.0s. Blank lines are skipped.
    """
    rows = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            time_s, _, text = line.partition("\t")
            rows.append((parse_time(time_s), text.strip()))
    out = []
    for i, (st, tx) in enumerate(rows):
        en = rows[i + 1][0] if i + 1 < len(rows) else st + 3.0
        out.append((st, en, tx))
    return out


def apply_overrides(lines, offset, path):
    """Surgical per-song line fixes the extraction can't get right on its own —
    e.g. a duet merge (t.A.T.u.) picking the wrong voice's line for a repeat.
    overrides/<NN>.tsv rows (tab-separated), <time> = PLAYBACK time the vocalist
    cites ('m:ss.s' or seconds); '#' lines and blanks ignored:
        replace <time> <text>   replace the line nearest <time> (KEEP its timing)
        insert  <time> <text>   add a line starting at <time>
        delete  <time>          drop the line nearest <time>
    """
    lines = list(lines)
    for raw in open(path, encoding="utf-8"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.rstrip("\n").split("\t")
        op = parts[0].strip().lower()
        ts = parts[1].strip()
        tstem = parse_time(ts) - offset                  # playback -> stem time
        text = parts[2].strip() if len(parts) > 2 else ""
        if op == "insert":
            lines.append((tstem, tstem + 3.0, text))
            lines.sort(key=lambda e: e[0])
            print(f"  override insert @{ts}: {text!r}")
            continue
        if not lines:
            continue
        i = min(range(len(lines)), key=lambda k: abs(lines[k][0] - tstem))
        st, en, old = lines[i]
        if op == "replace":
            lines[i] = (st, en, text)
            print(f"  override replace @{ts} (was {old!r}) -> {text!r}")
        elif op == "delete":
            del lines[i]
            print(f"  override delete @{ts}: {old!r}")
        else:
            print(f"  override SKIP unknown op {op!r}")
    return lines


def group_lines(words):
    """Break into lines: JamZone capitalises the first word of each lyric line."""
    lines = []
    cur = []
    for st, en, tx in words:
        if cur and tx[:1].isupper():
            lines.append(cur); cur = []
        cur.append((st, en, tx))
    if cur:
        lines.append(cur)
    # -> (start, end, text) per line
    return [(ln[0][0], ln[-1][1], " ".join(w[2] for w in ln)) for ln in lines]


def collapse_letter_runs(lines, min_run=3):
    """A spelled chant (S&M's 'S S S M M M ...') comes through as many one-letter
    screens. Collapse a run of >= min_run single-letter lines into one screen of
    the distinct letters, '&'-joined ('S','M' -> 'S&M'), spanning the whole run."""
    out, i, n = [], 0, len(lines)
    while i < n:
        if len(lines[i][2].strip()) == 1 and lines[i][2].strip().isalpha():
            j = i
            seen = []
            while j < n and len(lines[j][2].strip()) == 1 and lines[j][2].strip().isalpha():
                L = lines[j][2].strip().upper()
                if L not in seen:
                    seen.append(L)
                j += 1
            if j - i >= min_run:
                out.append((lines[i][0], lines[j - 1][1], "&".join(seen)))
                i = j
                continue
        out.append(lines[i])
        i += 1
    return out


def pack_lines(lines, min_sec=2.0):
    """Kill single-word flashes: while a screen is ONE word and shows for < min_sec
    (gap to the next line), merge the next line into it. Stops at >=2 words, so a
    held single word (>= min_sec) is left alone and merges produce short readable
    phrases ('Mister'+'Saxobeat' -> 'Mister Saxobeat'; 'And'+next -> 'And ...')."""
    if not lines:
        return []
    out = []
    cs, ce, ct = lines[0]
    for st, en, tx in lines[1:]:
        if len(ct.split()) == 1 and (st - cs) < min_sec:
            ct, ce = ct + " " + tx, en
        else:
            out.append((cs, ce, ct))
            cs, ce, ct = st, en, tx
    out.append((cs, ce, ct))
    return out


ASS_HEAD = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial,46,&H0000D7FF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,3,0,8,40,40,30,1
Style: Pair,Arial,54,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,4,0,5,80,80,40,1
"""


def t(sec):
    sec = max(0.0, sec)
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def esc(s):
    return s.replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def build_pairs(lines, max_gap=6.0):
    """Page-flip pairing (vocalist asked for two lines at once, less eye-jumping):
    group consecutive lines two-at-a-time, but NEVER pair across an interval >
    max_gap seconds to the next line (a section boundary / instrumental break) —
    that line shows alone so the next pair starts clean on the new section. Odd
    trailing line = singleton. The metric is the start-to-start interval, which
    works for both the JamZone path (real syllable times) and the manual --lines
    path (where each line's end is just the next line's start, so an end-based gap
    would always be zero and never split)."""
    pairs, i, n = [], 0, len(lines)
    while i < n:
        if i + 1 < n and (lines[i + 1][0] - lines[i][0]) <= max_gap:
            pairs.append([lines[i], lines[i + 1]]); i += 2
        else:
            pairs.append([lines[i]]); i += 1
    return pairs


def make_ass(path, title, lines, dur, offset, lead=5.0, max_gap=6.0):
    """Two-line page-flip layout: lines shown in pairs (both equal weight, centred);
    the screen flips once per pair so the eye jumps half as often. Each pair holds
    until the next pair begins; the first pair gets a `lead`-second read-ahead."""
    body = ASS_HEAD.format(w=W, h=H)

    def dlg(start, end, style, text, mv=0):
        return f"Dialogue: 0,{t(start)},{t(end)},{style},,0,0,{mv},,{esc(text)}\n"

    body += "[Events]\n"
    body += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    body += dlg(0, dur, "Title", title)
    pairs = build_pairs(lines, max_gap)
    for k, pr in enumerate(pairs):
        s = pr[0][0] + offset
        nxt = (pairs[k + 1][0][0] + offset) if k + 1 < len(pairs) else (pr[-1][1] + offset + 3)
        if k == 0:                       # read-ahead before the very first line is sung
            s = max(0, s - lead)
        body += dlg(s, nxt, "Pair", "\\N".join(p[2] for p in pr))
    with open(path, "w") as f:
        f.write(body)


def make_black(path, dur):
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={dur:.3f}:r=30",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", path],
        check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", help="JamZone cat id (required unless --lines)")
    ap.add_argument("--index", type=int, required=True, help="Program Change number / clip NN")
    ap.add_argument("--song", required=True, help="song folder (for auto-render/timeline.json + length)")
    ap.add_argument("--title", required=True)
    ap.add_argument("--lines", help="manual <time>\\t<line> TSV; bypasses JamZone tiles (offset=0)")
    args = ap.parse_args()
    if not args.lines and not args.cat:
        ap.error("--cat is required unless --lines is given")

    allwav = os.path.join(args.song, "auto-render", "all.wav")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", allwav], capture_output=True, text=True).stdout.strip())

    if args.lines:
        # Manual front-end: times are already playback-relative, so offset=0.
        offset = 0.0
        lines = parse_lines_table(args.lines)
        print(f"manual lines: {len(lines)} lines (offset 0)")
        print(f"song length {dur:.2f}s")
    else:
        tl = json.load(open(os.path.join(args.song, "auto-render", "timeline.json")))
        offset = tl.get("offset_sec", 0.0)
        tiles = dj(args.cat, "tiles.json")
        words, cols = lead_words(tiles)
        lines = group_lines(words)
        raw = len(lines)
        lines = pack_lines(collapse_letter_runs(lines))
        print(f"lead colour(s) {','.join(cols)}: {len(words)} words -> "
              f"{raw} lines -> {len(lines)} packed (no 1-word flashes)")
        print(f"offset_sec {offset:+.4f}  song length {dur:.2f}s")
    ov = os.path.join(HERE, "overrides", f"{args.index:02d}.tsv")
    if os.path.exists(ov):
        lines = apply_overrides(lines, offset, ov)
    for st, en, tx in lines[:6]:
        print(f"  [{t(st+offset)}] {tx}")

    mp4 = os.path.join(HERE, "clips", f"{args.index:02d}.mp4")
    ass = os.path.join(HERE, "clips", f"{args.index:02d}.ass")
    make_black(mp4, dur)
    make_ass(ass, args.title, lines, dur, offset)
    print(f"wrote {mp4}")
    print(f"wrote {ass}")


if __name__ == "__main__":
    main()
