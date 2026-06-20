#!/usr/bin/env python3
"""Force-align KNOWN lyrics to a vocal stem's whisper word-timestamps -> a
`<time>\\t<line>` TSV that make_song_clip.py --lines turns into a timed clip.

For static songs (manual lyrics, no JamZone tiles) that DO have an isolated
Moises `vocals` stem. We already know the exact words, so this is alignment,
not transcription: whisper (run on the vocal stem) gives word start times; we
Needleman-Wunsch-align the known lyric tokens onto whisper's token stream
(fuzzy, stem-prefix tolerant of Russian inflection) and read each line's start
off its first matched word.

whisper times are on the STEM timeline; the clip lives on the render timeline,
so we add offset_sec (auto-render/timeline.json) before writing.

  align_lyrics.py --whisper vocals.json --lyrics 14.txt --offset 3.187 --out 14.tsv
"""
import argparse
import json
import re
import sys

PUNCT = re.compile(r"[^0-9a-zа-яё]+", re.IGNORECASE)


def norm(tok):
    return PUNCT.sub("", tok.lower())


def tokenize(text):
    # hyphens split (мало-мало-мало -> three tokens), drop empties
    return [norm(t) for t in re.split(r"[\s\-–—]+", text) if norm(t)]


def eq(a, b):
    if a == b:
        return True
    return len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4]


def whisper_words(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for seg in d.get("segments", []):
        for w in seg.get("words", []):
            t = norm(w.get("word", ""))
            st = w.get("start")
            if t and st is not None:
                out.append((t, float(st)))
    return out


def known_tokens(lines):
    """[(token, line_idx)] over all non-blank lyric lines."""
    out = []
    for i, ln in enumerate(lines):
        for t in tokenize(ln):
            out.append((t, i))
    return out


def align(kt, ww):
    """Needleman-Wunsch. Returns matched pairs [(ki, wi)] (monotonic)."""
    K = [t for t, _ in kt]
    W = [t for t, _ in ww]
    n, m = len(K), len(W)
    NEG = -10 ** 9
    # dp rows kept small via two-row? need backtrack -> full table (n,m <= few hundred)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = -i
    for j in range(1, m + 1):
        dp[0][j] = -j
    for i in range(1, n + 1):
        ki = K[i - 1]
        for j in range(1, m + 1):
            mm = dp[i - 1][j - 1] + (2 if eq(ki, W[j - 1]) else -1)
            dp[i][j] = max(mm, dp[i - 1][j] - 1, dp[i][j - 1] - 1)
    pairs = []
    i, j = n, m
    while i > 0 and j > 0:
        if dp[i][j] == dp[i - 1][j - 1] + (2 if eq(K[i - 1], W[j - 1]) else -1):
            if eq(K[i - 1], W[j - 1]):
                pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif dp[i][j] == dp[i - 1][j] - 1:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--whisper", required=True, help="whisper json with word timestamps")
    ap.add_argument("--lyrics", required=True, help="known lyrics, one line per screen")
    ap.add_argument("--offset", type=float, default=0.0, help="stem->render offset_sec")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lines = [ln.rstrip() for ln in open(args.lyrics, encoding="utf-8")]
    lines = [ln for ln in lines if ln.strip()]
    kt = known_tokens(lines)
    ww = whisper_words(args.whisper)
    if not ww:
        sys.exit("no whisper words found")
    pairs = align(kt, ww)

    # first matched whisper start per line
    line_start = {}
    for ki, wi in pairs:
        li = kt[ki][1]
        st = ww[wi][1]
        if li not in line_start or st < line_start[li]:
            line_start[li] = st

    # fill gaps: interpolate between known neighbours; clamp monotonic
    starts = [line_start.get(i) for i in range(len(lines))]
    for i in range(len(starts)):
        if starts[i] is None:
            p = next((k for k in range(i - 1, -1, -1) if starts[k] is not None), None)
            q = next((k for k in range(i + 1, len(starts)) if starts[k] is not None), None)
            if p is not None and q is not None:
                starts[i] = starts[p] + (starts[q] - starts[p]) * (i - p) / (q - p)
            elif p is not None:
                starts[i] = starts[p] + 1.0
            elif q is not None:
                starts[i] = max(0.0, starts[q] - 1.0)
            else:
                starts[i] = 0.0
    for i in range(1, len(starts)):
        if starts[i] < starts[i - 1]:
            starts[i] = starts[i - 1]

    matched = len(set(li for _, li in [(kt[k][0], kt[k][1]) for k, _ in pairs]))
    with open(args.out, "w", encoding="utf-8") as f:
        for i, ln in enumerate(lines):
            t = starts[i] + args.offset
            f.write(f"{int(t // 60)}:{t % 60:05.2f}\t{ln.strip()}\n")
    print(f"{len(pairs)} word matches; {matched}/{len(lines)} lines anchored; wrote {args.out}")


if __name__ == "__main__":
    main()
