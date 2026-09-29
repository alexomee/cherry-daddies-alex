"""Reproduce the requested short ending after music bar 77's downbeat.

Reads the immutable pre-edit WAV snapshot, preserves the final hit, fades
80–260 ms after that beat, then silences all musical stems. The render's
cut_after_last_cue=1 retains one bar for the click/cue tail.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

SONG = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools/jamzone"))
from jamzone_render import SR, decode, onsets


def main():
    original = SONG / "versions/2026-09-29-before-cues-v1"
    bpm = json.loads((original / "mix.json").read_text())["bpm"]
    db = float(onsets(decode(str(original / "metronome.wav")).mean(1))[0])
    event = db + 76 * 4 * 60 / bpm
    fade_start = round((event + .080) * SR)
    fade_end = round((event + .260) * SR)
    report = {
        "source": str(original.relative_to(REPO)), "bpm": bpm,
        "final_event_bar": 77, "final_event_stem_sec": event,
        "fade_start_stem_sec": fade_start / SR,
        "silence_from_stem_sec": fade_end / SR,
        "source_sha256": {},
    }
    for name in ["bass", "drums", "guitars", "vocals"]:
        src = original / (name + ".wav")
        report["source_sha256"][src.name] = hashlib.sha256(src.read_bytes()).hexdigest()
        audio = decode(str(src))
        audio[fade_start:fade_end] *= np.linspace(1, 0, fade_end - fade_start, dtype=np.float32)[:, None]
        audio[fade_end:] = 0
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR),
            "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", str(SONG / (name + ".wav")),
        ], input=audio.astype(np.float32).tobytes(), check=True)
        print(f"{name}: final hit {event:.6f}s, silent from {fade_end / SR:.6f}s")
    (SONG / "ending-edit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
