#!/usr/bin/env python3
"""Local song transcription -> raw JSON + playback-time TSV. No OpenAI API key.

Apple Silicon:
  uv run --python 3.12 --with mlx-whisper transcribe_lyrics.py vocals.wav \
    --offset 3.187 --out lyrics-timed/14.tsv
Other machines: replace --with mlx-whisper with --with faster-whisper.
An existing Whisper-compatible JSON can be imported with --from-json.
"""
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path


def timed_lines(result, offset):
    """Keep repeats; flag uncertainty; split only at measured word timestamps."""
    if not math.isfinite(offset):
        raise ValueError("offset must be finite")
    rows, notes = [], []
    for seg in result.get("segments", []):
        start = float(seg["start"]) + offset
        if seg.get("no_speech_prob", 0) > .8:
            notes.append(f"{start:.2f}s: skipped probable silence: {seg.get('text', '')}")
            continue
        if seg.get("avg_logprob", 0) < -1 or seg.get("compression_ratio", 0) > 2.4:
            notes.append(f"{start:.2f}s: check uncertain/repetitive recognition against audio")
        words = seg.get("words") or []
        if words:
            chunks, current, first = [], [], None
            for word in words:
                text = word["word"].strip()
                if not text:
                    continue
                ts = float(word["start"]) + offset
                if current and (len(" ".join(current + [text])) > 58 or ts - first > 6):
                    chunks.append((first, " ".join(current)))
                    current, first = [], None
                if first is None:
                    first = ts
                current.append(text)
                if word.get("probability", 1) < .4:
                    notes.append(f"{ts:.2f}s: check word {text!r}")
            if current:
                chunks.append((first, " ".join(current)))
        else:
            chunks = [(start, seg.get("text", "").strip())]
        for ts, text in chunks:
            text = " ".join(text.split())
            if not text:
                continue
            ts = round(ts, 2)
            if not math.isfinite(ts) or ts < 0:
                raise ValueError("recognition falls before playback start; check offset")
            if rows and ts <= rows[-1][0]:
                raise ValueError("non-increasing recognition timestamps; inspect raw JSON")
            rows.append((ts, text))
    if not rows:
        raise ValueError("no speech recognized; inspect audio and raw JSON")
    return rows, notes


def recognize(audio, backend, model, language):
    if backend == "mlx":
        import mlx_whisper
        model = model or "mlx-community/whisper-large-v3-turbo"
        result = mlx_whisper.transcribe(str(audio), path_or_hf_repo=model,
                                       language=language, word_timestamps=True,
                                       condition_on_previous_text=False)
    else:
        from faster_whisper import WhisperModel
        model = model or "large-v3"
        segments, info = WhisperModel(model, device="cpu", compute_type="int8").transcribe(
            str(audio), language=language, word_timestamps=True,
            condition_on_previous_text=False)
        result = {"language": info.language, "segments": []}
        for seg in segments:
            item = seg._asdict()
            item["words"] = [w._asdict() for w in seg.words or []]
            result["segments"].append(item)
    return result, model


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("audio", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--offset", type=float, required=True,
                    help="stem -> playback seconds; explicitly use 0 for playback-frame audio")
    ap.add_argument("--language", default="ru")
    ap.add_argument("--backend", choices=["auto", "mlx", "faster"], default="auto")
    ap.add_argument("--model")
    ap.add_argument("--from-json", type=Path, help="import existing Whisper-compatible recognition")
    ap.add_argument("--replace", action="store_true", help="explicitly replace an existing draft")
    args = ap.parse_args()
    raw_path = args.out.with_suffix(".raw.json")
    notes_path = args.out.with_suffix(".review.txt")
    if not args.replace and any(p.exists() for p in (args.out, raw_path, notes_path)):
        ap.error("output exists; preserve edits or explicitly use --replace")
    if not args.audio.is_file():
        ap.error(f"audio missing: {args.audio}")
    backend = args.backend
    if backend == "auto":
        backend = "mlx" if platform.system() == "Darwin" and platform.machine() == "arm64" else "faster"
    if args.from_json:
        result, model = json.loads(args.from_json.read_text()), "imported-json"
    else:
        try:
            result, model = recognize(args.audio, backend, args.model, args.language)
        except ImportError:
            ap.error(f"install backend with uv run --python 3.12 --with {'mlx-whisper' if backend == 'mlx' else 'faster-whisper'} ...")
    result["provenance"] = {
        "audio_name": args.audio.name,
        "audio_sha256": hashlib.file_digest(args.audio.open("rb"), "sha256").hexdigest(),
        "backend": backend, "model": model, "language": args.language,
        "offset_sec": args.offset, "output_frame": "playback",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    try:
        rows, notes = timed_lines(result, args.offset)
    except ValueError as e:
        ap.error(f"{e}; raw recognition saved to {raw_path}")
    args.out.write_text("".join(f"{int(t // 60)}:{t % 60:05.2f}\t{text}\n" for t, text in rows))
    notes_path.write_text("DRAFT — listen to the full preview, including repeats.\n" +
                          "\n".join(notes or ["No automatic flags; human review still required."]) + "\n")
    print(f"DRAFT: {len(rows)} lines -> {args.out}; {len(notes)} review flags -> {notes_path}")


if __name__ == "__main__":
    main()
