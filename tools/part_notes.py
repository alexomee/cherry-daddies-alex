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
Notes are named in the BAND key (pitch_semitones of mix.json applied), the key of notes.json and
of the GM-800 layer (a layer is never pitched); --track takes band-key notes too.
Stems: <stem>.wav, else the Moises <stem>.mp3.
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
        y, sr = sf.read(song.stem(st), always_2d=True)
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


def key_note(song):
    if song.semi:
        print(f"note names in the BAND key: the stems are in the original key, pitch_semitones {song.semi:+g} applied")


def table(song, x, sr, b0, b1, div, floor):
    key_note(song)
    print(f"notes within {floor} dB of the loudest of the window, local peaks only (dB to the loudest)")
    for bar in range(b0, b1):
        for h in range(div):
            t0 = song.t_stem(bar + h / div)
            L = note_levels(x[int((t0 + 0.03) * sr):int((t0 + song.bar / div - 0.03) * sr)], sr); mx = max(L.values())
            top = [n for n in sorted(L) if L[n] > mx - floor and L[n] >= L.get(n - 1, -999) and L[n] >= L.get(n + 1, -999)]
            print(f"  bar {bar:3}.{h * 4 // div + 1}  max {mx:6.1f}  " + " ".join(f"{nm(n + song.semi)}{L[n] - mx:+.0f}" for n in top))


def track(song, x, sr, b0, b1, notes):
    nfft = 16384; w = np.hanning(nfft); df = sr / nfft
    key_note(song)
    print("level of each note every 1/8 bar, dB (which notes enter and leave together)")
    print("bar.beat " + " ".join(f"{nm(n + song.semi):>5}" for n in notes))
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
    key_note(song)     # the take is in the band key: stem note n is compared with take note n + semi
    print(f"stem / take / difference, dB to the loudest note of the bar; '<<' = {6}+ dB stronger in the stem")
    for bar in range(b0, b1):
        t0 = song.t_stem(bar); a = int((bar - b0) * song.bar * sr)
        A = note_levels(x[int((t0 + 0.4) * sr):int((t0 + song.bar - 0.05) * sr)], sr)
        B = note_levels(y[a + int(0.4 * sr):a + int((song.bar - 0.05) * sr)], sr)
        ra, rb = max(A.values()), max(B.values()); rows = []
        for n in range(LO + 12, HI):
            sa, sb = A[n] - ra, B.get(n + song.semi, -999) - rb
            if max(sa, sb) > -floor and A[n] >= A.get(n - 1, -999) and A[n] >= A.get(n + 1, -999):
                rows.append(f"{nm(n + song.semi)} {sa:+.0f}/{sb:+.0f}{' <<' if sa - sb >= 6 else ''}")
        print(f"  bar {bar:3}: " + "  ".join(rows))


def roll(song, x, sr, b0, b1, floor, per=4, period=0):
    """Piano roll by 16ths (CQT, 3 bins a semitone): rows = notes, columns = 16ths, '|' = bar line.
    Level to the loudest cell of the block of `per` bars: '#' within 6 dB, '=' 12, '-' 20, '.' floor;
    a capital ('@' 'O' 'o') = the note rose 5+ dB against the previous 16th (an attack)."""
    import librosa
    from scipy.signal import resample_poly
    y = resample_poly(x, 22050, sr).astype(np.float32); hop = 128; bpo = 36
    C = np.abs(librosa.cqt(y, sr=22050, hop_length=hop, fmin=librosa.note_to_hz("C1"), n_bins=bpo * 6,
                           bins_per_octave=bpo, filter_scale=1.5))
    S = np.stack([C[max(0, 3 * k - 1):3 * k + 2].max(0) for k in range(72)])        # semitone k = C1 + k
    D = 20 * np.log10(S + 1e-9); fps = 22050 / hop
    key_note(song)
    if period:
        return roll_period(song, D, fps, b0, b1, floor, period)
    for a in range(b0, b1, per):
        bars = range(a, min(a + per, b1)); cells = []
        for bar in bars:
            for q in range(16):
                t0 = song.t_stem(bar + q / 16); t1 = song.t_stem(bar + (q + 1) / 16)
                cells.append(D[:, int((t0 + 0.012) * fps):max(int((t0 + 0.012) * fps) + 1, int(t1 * fps))].max(1))
        M = np.stack(cells, 1); ref = M.max()
        rows = [k for k in range(71, -1, -1) if M[k].max() > ref - floor
                and (M[k] >= np.maximum(M[k - 1] if k else -999, M[k + 1] if k < 71 else -999) - 0.5).any()]
        print(f"bars {bars[0]}-{bars[-1]}   (1 . . . 2 . . . 3 . . . 4 . . . per bar; ref {ref:.0f} dB)")
        for k in rows:
            s = ""
            for c in range(M.shape[1]):
                v = M[k, c] - ref; up = c > 0 and M[k, c] - M[k, c - 1] >= 5
                ch = ("@" if up else "#") if v > -6 else ("O" if up else "=") if v > -12 else \
                     ("o" if up else "-") if v > -20 else "." if v > -floor else " "
                s += ("|" if c % 16 == 0 else "") + ch
            print(f"{nm(24 + k + song.semi):>4} {s}|")


def cells_of(song, D, fps, bars):
    out = []
    for bar in bars:
        for q in range(16):
            t0 = song.t_stem(bar + q / 16); t1 = song.t_stem(bar + (q + 1) / 16)
            out.append(D[:, int((t0 + 0.012) * fps):max(int((t0 + 0.012) * fps) + 1, int(t1 * fps))].max(1))
    return np.stack(out, 1)


def roll_period(song, D, fps, b0, b1, floor, period):
    """The bars folded by `period` bars: median level of each note on each 16th over the passes, and
    an attack mark where the note rises 5+ dB on that 16th in at least half of the passes (capital).
    Shows what repeats in every pass; one-off fills fall out."""
    passes = [cells_of(song, D, fps, range(a, a + period)) for a in range(b0, b1 - period + 1, period)]
    P = np.stack(passes); M = np.median(P, 0); ref = M.max()
    up = np.zeros_like(P, dtype=bool); up[:, :, 1:] = (P[:, :, 1:] - P[:, :, :-1]) >= 5
    U = up.mean(0) >= 0.5
    print(f"bars {b0}-{b1 - 1} folded by {period}: {len(passes)} passes (median; capital = attack in >= half; ref {ref:.0f} dB)")
    rows = [k for k in range(71, -1, -1) if M[k].max() > ref - floor
            and (M[k] >= np.maximum(M[k - 1] if k else -999, M[k + 1] if k < 71 else -999) - 0.5).any()]
    for k in rows:
        s = ""
        for c in range(M.shape[1]):
            v = M[k, c] - ref; u = U[k, c]
            ch = ("@" if u else "#") if v > -6 else ("O" if u else "=") if v > -12 else \
                 ("o" if u else "-") if v > -20 else "." if v > -floor else " "
            s += ("|" if c % 16 == 0 else "") + ch
        print(f"{nm(24 + k + song.semi):>4} {s}|")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("song"); ap.add_argument("b0", type=int); ap.add_argument("b1", type=int)
    ap.add_argument("--stems", default="keys+strings", help="stems to sum, e.g. keys+strings (default)")
    ap.add_argument("--div", type=int, default=1, help="windows per bar (1 = whole bar)")
    ap.add_argument("--floor", type=float, default=26.0, help="show notes within this many dB of the loudest")
    ap.add_argument("--track", help='notes to follow every 1/8 bar, e.g. "A1 G1 C5"')
    ap.add_argument("--take", help="a take of the same bars (wav that starts on the bar line of FROM)")
    ap.add_argument("--roll", action="store_true", help="piano roll by 16ths (needs librosa)")
    ap.add_argument("--per", type=int, default=4, help="--roll: bars per block")
    ap.add_argument("--period", type=int, default=0, help="--roll: fold the bars by this many (median of passes)")
    a = ap.parse_args()
    song = gmm.Song(a.song); x, sr = stems_sum(song, a.stems.split("+"))
    if a.roll:
        return roll(song, x, sr, a.b0, a.b1, a.floor, a.per, a.period)
    if a.track:
        return track(song, x, sr, a.b0, a.b1, [p2n(s) - song.semi for s in a.track.split()])   # band key in
    if a.take:
        return against_take(song, x, sr, a.b0, a.b1, a.take, a.floor - 4)
    table(song, x, sr, a.b0, a.b1, a.div, a.floor)


if __name__ == "__main__":
    sys.exit(main())
