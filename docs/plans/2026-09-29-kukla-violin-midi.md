# Kukla Violin MIDI Implementation Plan

**Goal:** Produce an editable, two-voice violin MIDI draft aligned with the existing auto-render audio.

**Architecture:** Local Basic Pitch inference on the lossless strings stem, spectral checks and conservative note cleanup, voice assignment, MIDI export with the measured render offset, and a resynthesized comparison. This is a one-off media deliverable rather than a new renderer feature.

**Tech Stack:** Python 3.11, Basic Pitch ONNX, librosa/scipy/numpy, pretty_midi/mido, soundfile, ffmpeg.

---

### 1. Inspect source and infer candidates

- Check source metadata and read mix/timeline configuration.
- Use an isolated temporary Python environment; do not change application dependencies.
- Save model activations and permissive note candidates outside git; inspect pitch/activity distributions and spectrograms.

### 2. Refine and split voices

- Create `music/songs/Король и Шут - Кукла колдуна/transcription/violin-v1/transcribe.py`.
- Check source support for simultaneous fundamentals; remove obvious spill/overtones and vibrato fragmentation.
- Assign at most two simultaneous voices; retain uncertainty in a review table rather than inventing harmony.

### 3. Export and verify

- Write combined two-track MIDI and separate per-voice MIDI, 148.6 BPM, 4/4; shift notes by `offset_sec`.
- Resynthesize MIDI and create a source/MIDI comparison WAV for audition in Logic.
- Read back exports and verify timing, tracks, note ranges, overlaps and source support.
- Document import steps, limitations and review locations in the output README; update the song wiki and log.
