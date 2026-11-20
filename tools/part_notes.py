#!/usr/bin/env python3
"""Which notes sound in a part of a song's stems, bar by bar (wiki/pipelines/part-transcription-guide.md).

Step one of writing a part out: a spectrum of the summed stems per bar (or per part of a bar),
the level of every semitone, local peaks only. It does not decide what is a note and what is a
harmonic or the tail of the previous chord - read the table with the rules of the guide.

    pn() { uv run -q --python 3.12 --with numpy --with soundfile --with scipy tools/part_notes.py "$@"; }
    pn "<song>" 9 25                           # keys + strings, one line per bar
    pn "<song>" 9 13 --stems strings --div 2   # half bars, one stem
    pn "<song>" 9 13 --track "A1 G1 E4 C5 C6"  # these notes every 1/8 bar: what enters together
    pn "<song>" 9 13 --take analysis/gm800-match/<song>/part-x.wav   # stem against a take of the
                                               # same bars: a note 6+ dB stronger in the stem is missing

Bars are mix.json bars (TO exclusive). Constant-tempo songs that have been rendered (timeline.json).
"""
import argparse, importlib.util, os, sys
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("gmm", os.path.join(REPO, "tools", "gm800_match.py"))
gmm = importlib.util.module_from_spec(_s); _s.loader.exec_module(gmm)
N = "C C# D D# E F F# G G# A A# B".split()
nm = lambda n: f"{N[n % 12]}{n // 12 - 1}"
p2n = lambda s: N.index(s[:-1]) + 12 * (int(s[-1]) + 1)
LO, HI = 24, 97                      # C1 .. C7


def stems_sum(song, stems):
    import soundfile as sf
    x, sr = 0, None
    for st in stems:
        y, sr = sf.read(os.path.join(song.dir, st + ".wav"), always_2d=True)
        x = x + y.mean(1)
    return x, sr


def note_levels(seg, sr, nfft=32768):
    """dB of the strongest bin within +-0.3 semitone of every note LO..HI."""
    if len(seg) < nfft:
        seg = np.pad(seg, (0, nfft - len(seg)))
    w, acc, k = np.hanning(nfft), 0, 0
    for i in range(0, len(seg) - nfft + 1, nfft // 8):
        acc = acc + np.abs(np.fft.rfft(seg[i:i + nfft] * w)); k += 1
    mag, df, out = acc / k / (nfft / 4), sr / nfft, {}
    for n in range(LO, HI):
        f = 440 * 2 ** ((n - 69) / 12)
        i0, i1 = int(round(f * 2 ** (-0.3 / 12) / df)), int(round(f * 2 ** (0.3 / 12) / df))
        out[n] = 20 * np.log10(mag[i0:i1 + 1].max() + 1e-12)
    return out


def table(song, x, sr, b0, b1, div, floor):
    print(f"notes within {floor} dB of the loudest of the window, local peaks only (dB to the loudest)")
    for bar in range(b0, b1):
        for h in range(div):
            t0 = song.t_stem(bar + h / div)
            L = note_levels(x[int((t0 + 0.03) * sr):int((t0 + song.bar / div - 0.03) * sr)], sr); mx = max(L.values())
            top = [n for n in sorted(L) if L[n] > mx - floor and L[n] >= L.get(n - 1, -999) and L[n] >= L.get(n + 1, -999)]
            print(f"  bar {bar:3}.{h * 4 // div + 1}  max {mx:6.1f}  " + " ".join(f"{nm(n)}{L[n] - mx:+.0f}" for n in top))


def track(song, x, sr, b0, b1, notes):
    nfft = 16384; w = np.hanning(nfft); df = sr / nfft
    print("level of each note every 1/8 bar, dB (which notes enter and leave together)")
    print("bar.beat " + " ".join(f"{nm(n):>5}" for n in notes))
    for bar in range(b0, b1):
        for k in range(8):
            i = int(song.t_stem(bar + (k + 0.5) / 8) * sr) - nfft // 2
            mag = np.abs(np.fft.rfft(x[i:i + nfft] * w)) / (nfft / 4); row = []
            for n in notes:
                f = 440 * 2 ** ((n - 69) / 12)
                i0, i1 = int(round(f * 2 ** (-0.3 / 12) / df)), int(round(f * 2 ** (0.3 / 12) / df))
                row.append(20 * np.log10(mag[i0:i1 + 1].max() + 1e-12))
            print(f"{bar:3}.{k / 2 + 1:3.1f}  " + " ".join(f"{v:5.0f}" for v in row))


def against_take(song, x, sr, b0, b1, take, floor):
    """Stem vs a GM-800 take of the same bars, note by note, both relative to their loudest note."""
    import soundfile as sf
    from scipy.signal import resample_poly
    y, ysr = sf.read(take, always_2d=True); y = y.mean(1)
    if ysr != sr:
        y = resample_poly(y, sr, ysr)
    print(f"stem / take / difference, dB to the loudest note of the bar; '<<' = {6}+ dB stronger in the stem")
    for bar in range(b0, b1):
        t0 = song.t_stem(bar); a = int((bar - b0) * song.bar * sr)
        A = note_levels(x[int((t0 + 0.4) * sr):int((t0 + song.bar - 0.05) * sr)], sr)
        B = note_levels(y[a + int(0.4 * sr):a + int((song.bar - 0.05) * sr)], sr)
        ra, rb = max(A.values()), max(B.values()); rows = []
        for n in range(LO + 12, HI):
            sa, sb = A[n] - ra, B[n] - rb
            if max(sa, sb) > -floor and A[n] >= A.get(n - 1, -999) and A[n] >= A.get(n + 1, -999):
                rows.append(f"{nm(n)} {sa:+.0f}/{sb:+.0f}{' <<' if sa - sb >= 6 else ''}")
        print(f"  bar {bar:3}: " + "  ".join(rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("song"); ap.add_argument("b0", type=int); ap.add_argument("b1", type=int)
    ap.add_argument("--stems", default="keys+strings", help="stems to sum, e.g. keys+strings (default)")
    ap.add_argument("--div", type=int, default=1, help="windows per bar (1 = whole bar)")
    ap.add_argument("--floor", type=float, default=26.0, help="show notes within this many dB of the loudest")
    ap.add_argument("--track", help='notes to follow every 1/8 bar, e.g. "A1 G1 C5"')
    ap.add_argument("--take", help="a take of the same bars (wav that starts on the bar line of FROM)")
    a = ap.parse_args()
    song = gmm.Song(a.song); x, sr = stems_sum(song, a.stems.split("+"))
    if a.track:
        return track(song, x, sr, a.b0, a.b1, [p2n(s) for s in a.track.split()])
    if a.take:
        return against_take(song, x, sr, a.b0, a.b1, a.take, a.floor - 4)
    table(song, x, sr, a.b0, a.b1, a.div, a.floor)


if __name__ == "__main__":
    sys.exit(main())
