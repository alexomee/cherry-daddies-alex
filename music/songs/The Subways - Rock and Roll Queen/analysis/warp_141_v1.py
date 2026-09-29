"""Reproduce the 141-BPM rehearsal source from untouched JamZone cat_67531.

Uses the same pitch-preserving RubberBand/Hann-smoothed map as Кукла колдуна.
Run with an unused output directory; original AAC stems are read-only.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

SOURCE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools/jamzone"))
from jamzone_render import SR, decode, onsets
from jamzone_warp_ext import grid_dev, warp_rubberband
import jamzone_click as click

BPM = 141.0


def write_audio(path, audio):
    subprocess.run([
        "ffmpeg", "-v", "error", "-n", "-f", "f32le", "-ar", str(SR),
        "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", str(path),
    ], input=audio.astype(np.float32).tobytes(), check=True)


def main():
    if not shutil.which("rubberband"):
        raise SystemExit("RubberBand required: no varispeed fallback")
    dest = Path(sys.argv[1]).resolve()
    dest.mkdir(parents=True, exist_ok=False)
    metro = decode(str(SOURCE / "01_Click.m4a"))
    original_onsets = onsets(metro.mean(1))
    assert len(original_onsets) == 377
    # JamZone's eight-click precount is ~155 BPM. Remove it, keeping 0.4 s
    # before the actual music downbeat; the render will supply a new 141 count-in.
    trim = round((original_onsets[8] - 0.4) * SR)
    metro = metro[trim:]
    # The last fast precount pulse falls just inside that 0.4-s margin.
    # Remove it from the analysis reference, not from the musical stems.
    metro[:round(0.3 * SR)] = 0
    grid, deviation, measured, indices = grid_dev(metro.mean(1), BPM)
    assert np.array_equal(indices, np.arange(369))
    n_in = len(metro)
    n_out = n_in - round(float(deviation[-1]) * SR)
    source_times = grid + deviation
    assert np.all(np.diff(source_times) > 0)
    np.savetxt(dest / "warp-map.csv", np.column_stack([
        indices, measured + trim / SR, source_times + trim / SR, grid,
    ]), delimiter=",", header="beat,original_click_sec,smoothed_source_sec,target_sec",
        comments="", fmt=["%d", "%.9f", "%.9f", "%.9f"])

    sources = {}
    for path in sorted(SOURCE.glob("[0-9][0-9]_*.m4a")):
        sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.name == "01_Click.m4a":
            continue
        audio = decode(str(path))[trim:]
        # A few AAC stems differ by encoder-padding samples. A common input
        # and output length keeps the time map identical for all six stems.
        if len(audio) < n_in:
            audio = np.pad(audio, ((0, n_in - len(audio)), (0, 0)))
        audio = audio[:n_in]
        warped = warp_rubberband(audio, grid, deviation, n_out)
        write_audio(dest / (path.stem + ".wav"), warped)
        print(f"warped {path.name}: {n_out / SR:.3f}s", flush=True)

    # Clean constant click, rather than the time-stretched, jittery JZ click.
    samples = [click.wav_read(click.DB), click.wav_read(click.BT)]
    clean = np.zeros((n_out, 2), np.float32)
    for k in range(int((n_out / SR - grid[0]) * BPM / 60) + 1):
        hit = samples[0 if k % 4 == 0 else 1]
        hit = hit / max(float(np.abs(hit).max()), 1e-9) * (0.9 if k % 4 == 0 else 0.55)
        start = round((grid[0] + k * 60 / BPM) * SR)
        count = min(len(hit), n_out - start)
        if count > 0:
            clean[start:start + count] += hit[:count, None]
    write_audio(dest / "metronome.wav", clean)
    report = {
        "source_cat": "cat_67531", "bpm": BPM, "engine": "RubberBand R2",
        "smoothing": "7-beat Hann, jamzone_warp_ext.grid_dev",
        "pitch_semitones": 0, "trim_source_sec": trim / SR,
        "input_samples": n_in, "output_samples": n_out,
        "downbeat_source_sec": float(original_onsets[8]),
        "downbeat_warped_sec": float(grid[0]),
        "unsmoothed_minus_smoothed_ms_quantiles": np.quantile(
            (measured - source_times) * 1000, [0, .05, .5, .95, 1]).tolist(),
        "source_sha256": sources,
    }
    (dest / "warp-info.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
