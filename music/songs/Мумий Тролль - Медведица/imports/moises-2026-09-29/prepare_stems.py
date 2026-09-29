"""Prepare the imported Moises stems on Медведица's existing 130 BPM grid.

Raw zip members stay under raw/. Both vocal and guitar sources remain separate
WAVs; their names group them into the web renderer's vocal/guitars categories.
The archive's 443 Hz label is recorded as metadata; no pitch shift is applied.
"""
from pathlib import Path
import json
import shutil
import subprocess
import sys

import numpy as np

IMPORT = Path(__file__).resolve().parent
REPO = IMPORT.parents[4]
sys.path.insert(0, str(REPO / "tools/jamzone"))
from jamzone_render import decode, SR
from jamzone_warp_ext import grid_dev, warp_interp, warp_rubberband

STEMS = {
    "female_vocals": "female_lead_vocal",
    "male_vocals": "male_lead_vocal",
    "drums": "drums", "bass": "bass",
    "lead_guitars": "lead_guitars", "rhythm_guitars": "rhythm_guitars",
    "keys": "keys", "other": "other", "metronome": "metronome",
}


def main():
    if not shutil.which("rubberband"):
        raise SystemExit("RubberBand required; no varispeed fallback")
    dest = Path(sys.argv[1]).resolve()
    dest.mkdir(parents=True, exist_ok=False)
    reference = decode(str(IMPORT / "raw/metronome.mp3"))
    grid, dev, on, indices = grid_dev(reference.mean(1), 130)
    assert len(on) == 502 and np.array_equal(indices, np.arange(502))
    n_in = len(reference)
    n_out = n_in - round(float(dev[-1]) * SR)
    np.savetxt(dest / "warp-map.csv", np.column_stack([indices, on, grid + dev, grid]),
               delimiter=",", header="beat,raw_onset_sec,smoothed_source_sec,target_sec",
               comments="", fmt=["%d", "%.9f", "%.9f", "%.9f"])
    for source, name in STEMS.items():
        audio = decode(str(IMPORT / "raw" / (source + ".mp3")))
        assert len(audio) == n_in, source
        warped = (warp_interp(audio, grid, dev, n_out) if source == "metronome"
                  else warp_rubberband(audio, grid, dev, n_out))
        subprocess.run([
            "ffmpeg", "-v", "error", "-n", "-f", "f32le", "-ar", str(SR),
            "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", str(dest / (name + ".wav")),
        ], input=warped.astype(np.float32).tobytes(), check=True)
        print(f"prepared {name}.wav ({n_out / SR:.3f}s)", flush=True)
    info = {
        "bpm": 130, "pitch_semitones": 0, "engine": "RubberBand R2",
        "smoothing": "7-beat Hann", "first_raw_click_sec": float(on[0]),
        "downbeat_click_index": 0, "source_samples": n_in, "output_samples": n_out,
        "drift_range_ms": [float(dev.min() * 1000), float(dev.max() * 1000)],
        "stems": STEMS, "count_in": "excluded from music; rendered by cue pipeline",
    }
    (dest / "warp-info.json").write_text(json.dumps(info, indent=2) + "\n")


if __name__ == "__main__":
    main()
