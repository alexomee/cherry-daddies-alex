#!/usr/bin/env python3
"""Auto-discover a repeating song's sung structure and time the lyrics.

For static (manual-lyric) songs whose recording repeats sections (so a single
forced-alignment of the studio sheet crams the start and stretches the end).
We detect the voiced blocks in the vocal stem and force-align the FULL studio
lyrics against EACH block independently; the lines actually sung in a block
match with high probability, the rest get squished/low-prob and are dropped.
A chorus-repeat block independently re-matches the chorus lines, so repeats are
discovered from the audio with no structure hint.

Run with the model loaded once:
  uv run --with stable-ts --python 3.12 python auto_align.py \
      --stem vocals.wav --lyrics studio.txt --offset 0.488 --out 12.tsv

whisper free-transcription fails on these stems; alignment (given the text)
does not. Times are stem-relative; we add offset_sec for the render timeline.
"""
import argparse, re, subprocess, sys
import numpy as np

PUNCT = re.compile(r"[^0-9a-zа-яё]+", re.IGNORECASE)
norm = lambda t: PUNCT.sub("", t.lower())
def toks(s): return [norm(t) for t in re.split(r"[\s\-–—]+", s) if norm(t)]
def eq(a, b): return a == b or (len(a) >= 4 and len(b) >= 4 and a[:4] == b[:4])


def decode(path, sr=16000):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1",
                        "-ar", str(sr), "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32), sr


def voiced_blocks(x, sr, win=0.25, thr_db=-42, merge_gap=3.0, min_len=2.0):
    """List of (start_s, end_s) sung spans in stem time."""
    h = int(win * sr)
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i+h]**2)) + 1e-9)
                   for i in range(0, len(x) - h, h)])
    v = db > thr_db
    spans, st = [], None
    for i, on in enumerate(v):
        t = i * win
        if on and st is None: st = t
        if not on and st is not None: spans.append([st, t]); st = None
    if st is not None: spans.append([st, len(x) / sr])
    # merge close spans, drop short
    out = []
    for s in spans:
        if out and s[0] - out[-1][1] <= merge_gap: out[-1][1] = s[1]
        else: out.append(s)
    return [tuple(s) for s in out if s[1] - s[0] >= min_len]


def nw(K, W):
    """Needleman-Wunsch token match -> [(ki, wi)] monotonic matched pairs."""
    n, m = len(K), len(W)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1): dp[i][0] = -i
    for j in range(1, m + 1): dp[0][j] = -j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = max(dp[i-1][j-1] + (2 if eq(K[i-1], W[j-1]) else -1),
                           dp[i-1][j] - 1, dp[i][j-1] - 1)
    pairs, i, j = [], n, m
    while i > 0 and j > 0:
        if dp[i][j] == dp[i-1][j-1] + (2 if eq(K[i-1], W[j-1]) else -1):
            if eq(K[i-1], W[j-1]): pairs.append((i-1, j-1))
            i, j = i-1, j-1
        elif dp[i][j] == dp[i-1][j] - 1: i -= 1
        else: j -= 1
    return pairs[::-1]


def lines_in_block(model, audio, lines, line_tok, line_first, min_frac=0.5, min_prob=0.30):
    """Force-align full lyrics to one block's audio; return [(line_idx, start_s)]
    for lines that actually match (enough words, decent probability)."""
    res = model.align(audio, "\n".join(lines), language="ru")
    W, wt, wp = [], [], []
    for s in res.segments:
        for w in s.words:
            t = norm(w.word)
            if t: W.append(t); wt.append(w.start); wp.append(w.probability or 0.0)
    if not W: return []
    # flat known tokens with line idx + position of each line's first token
    K, kline = [], []
    for li, ln in enumerate(lines):
        for t in toks(ln): K.append(t); kline.append(li)
    pairs = nw(K, W)
    per = {}                      # line -> [starts], [probs]
    for ki, wi in pairs:
        per.setdefault(kline[ki], [[], []])
        per[kline[ki]][0].append(wt[wi]); per[kline[ki]][1].append(wp[wi])
    cand = []
    for li, (sts, ps) in per.items():
        nwords = sum(1 for t in toks(lines[li]))
        if len(sts) >= max(1, min_frac * nwords) and np.mean(ps) >= min_prob:
            cand.append((li, min(sts), float(np.mean(ps))))
    cand.sort()                                  # by line index
    if not cand:
        return []
    # keep the longest contiguous-by-line-index run (gap<=1); a real sung section
    # is consecutive studio lines. Isolated weak matches (e.g. the common first
    # line leaking in) form length-1 runs and lose to the real section.
    runs, cur = [], [cand[0]]
    for c in cand[1:]:
        if c[0] - cur[-1][0] <= 1: cur.append(c)
        else: runs.append(cur); cur = [c]
    runs.append(cur)
    # a real sung section is >=2 consecutive studio lines; keep those. A lone
    # line is kept only if very confident (a genuine 1-line hook), else it is a
    # weak false match (e.g. the common first line) and dropped.
    keep = [r for r in runs if len(r) >= 2 or (r[0][2] >= 0.6)]
    out = [(li, st) for r in keep for (li, st, _) in r]
    out.sort(key=lambda e: e[1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", required=True)
    ap.add_argument("--lyrics", required=True)
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="large-v3")
    args = ap.parse_args()

    import stable_whisper
    lines = [l.strip() for l in open(args.lyrics, encoding="utf-8") if l.strip()]
    x, sr = decode(args.stem)
    blocks = voiced_blocks(x, sr)
    print(f"{len(blocks)} voiced blocks; {len(lines)} studio lines", file=sys.stderr)
    model = stable_whisper.load_model(args.model)

    seq = []                      # (stem_start, text)
    for (a, b) in blocks:
        pad = 0.3
        seg = x[int(max(0, a - pad) * sr): int((b + pad) * sr)]
        base = max(0, a - pad)
        got = lines_in_block(model, seg, lines, None, None)
        for li, st in got:
            seq.append((base + st, lines[li]))
        print(f"  block {a:6.1f}-{b:6.1f}: {len(got)} lines", file=sys.stderr)

    seq.sort(key=lambda e: e[0])
    # drop near-duplicate consecutive (same text within 1.2s = boundary overlap)
    clean = []
    for t, txt in seq:
        if clean and clean[-1][1] == txt and t - clean[-1][0] < 1.2: continue
        clean.append((t, txt))
    with open(args.out, "w", encoding="utf-8") as f:
        for t, txt in clean:
            r = t + args.offset
            f.write(f"{int(r//60)}:{r%60:05.2f}\t{txt}\n")
    print(f"wrote {args.out}: {len(clean)} timed lines", file=sys.stderr)


if __name__ == "__main__":
    main()
