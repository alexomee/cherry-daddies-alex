#!/usr/bin/env python3
"""Section-chunked, snippet-verified lyric aligner using Gemini Multimodal API.

Workflow:
  1. Parses raw lyrics into natural musical stanzas (separated by blank lines).
  2. Anchors section boundaries using arrangement cues (from mix.json) or Gemini macro pass.
  3. Aligns lines within local 30-75s section audio chunks (eliminating cumulative LLM drift).
  4. Runs automated micro-snippet verification on 4-second audio chunks to pin down exact syllable onsets.
  5. Applies stage lead-in (default 0.4s pre-roll) so subtitles flip slightly before the vocalist sings.
  6. Preserves stanza breaks in TSV so make_song_clip.py never pairs lines across verse/chorus boundaries.

Usage:
  python tools/lyric-launcher/align_gemini.py \
    --audio "music/songs/Беги от меня/auto-render/all.wav" \
    --lyrics /path/to/lyrics.txt \
    --song "music/songs/Беги от меня" \
    --out "tools/lyric-launcher/lyrics-timed/25.tsv"
"""
import argparse
import base64
import concurrent.futures
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-3.5-flash"


def get_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("AGENTIQA_GEMINI_API_KEY")
    if key:
        return key.strip()
    env_file = Path.home() / "projects/agentiqa/apps/desktop-next/.env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("AGENTIQA_GEMINI_API_KEY=") or line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise ValueError(
        "Gemini API key not found. Set GEMINI_API_KEY or AGENTIQA_GEMINI_API_KEY in environment."
    )


def extract_chunk_mp3(src_audio: Path, dst_mp3: Path, start_sec: float, dur_sec: float, bitrate="64k"):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{start_sec:.3f}", "-t", f"{dur_sec:.3f}",
         "-i", str(src_audio), "-ac", "1", "-b:a", bitrate, str(dst_mp3)],
        check=True
    )


def get_audio_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def parse_time_str(t_str: str) -> float:
    """Parse 'm:ss', 'mm:ss.ss' or plain seconds into float seconds."""
    t_str = t_str.strip()
    if ":" in t_str:
        parts = t_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return float(t_str)


def format_time_sec(sec: float) -> str:
    m = int(sec // 60)
    s = sec % 60
    return f"{m}:{s:05.2f}"


def call_gemini_json(prompt: str, audio_mp3: Path, model: str, key: str, timeout=60):
    with open(audio_mp3, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "audio/mp3", "data": b64}}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res_data = json.load(resp)
                txt = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(txt)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except Exception:
            if attempt < 3:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def parse_stanzas(raw_text: str) -> list[list[str]]:
    """Split lyrics into stanzas by double newlines."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", raw_text) if b.strip()]
    stanzas = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if lines:
            stanzas.append(lines)
    return stanzas


def get_cue_anchors(song_dir: Path) -> list[dict]:
    """Read arrangement cues from mix.json to serve as structural landmarks."""
    mix_path = song_dir / "mix.json"
    if not mix_path.is_file():
        return []
    try:
        data = json.loads(mix_path.read_text(encoding="utf-8"))
        cues = []
        for c in data.get("cues", []):
            sec = c.get("abs_sec")
            txt = c.get("text", "")
            if sec is not None:
                cues.append({"sec": float(sec), "text": txt})
        cues.sort(key=lambda x: x["sec"])
        return cues
    except Exception:
        return []


def find_macro_stanza_boundaries(audio_mp3: Path, total_dur: float, stanzas: list[list[str]], cues: list[dict], model: str, key: str) -> list[float]:
    """Find the coarse start time (seconds) for each stanza across the whole track."""
    stanza_previews = [
        f"Stanza {i}: first line: '{lines[0]}', last line: '{lines[-1]}'"
        for i, lines in enumerate(stanzas)
    ]
    
    cue_hints = ""
    if cues:
        cue_lines = [f"- {format_time_sec(c['sec'])} ({c['sec']:.1f}s): {c['text']}" for c in cues]
        cue_hints = "\nKNOWN ARRANGEMENT CUES & LANDMARKS:\n" + "\n".join(cue_lines) + "\n"

    prompt = f"""You are a musical arrangement director.
Song length: {format_time_sec(total_dur)} ({total_dur:.1f} seconds).

There are {len(stanzas)} lyric stanzas in this song:
{json.dumps(stanza_previews, ensure_ascii=False, indent=2)}
{cue_hints}
Task:
Listen to the audio. For EACH of the {len(stanzas)} stanzas, find the time (in format mm:ss.ss) when that stanza begins being sung.
Output format: JSON array of objects:
[
  {{"stanza_idx": 0, "start_time": "mm:ss.ss"}},
  ...
]
"""
    results = call_gemini_json(prompt, audio_mp3, model, key, timeout=60)
    boundaries = [0.0] * len(stanzas)
    for r in results:
        idx = int(r["stanza_idx"])
        if 0 <= idx < len(boundaries):
            boundaries[idx] = parse_time_str(r["start_time"])

    # Ensure strictly increasing
    for i in range(1, len(boundaries)):
        if boundaries[i] <= boundaries[i - 1]:
            boundaries[i] = boundaries[i - 1] + 15.0

    return boundaries


def align_single_stanza(stanza_idx: int, lines: list[str], chunk_start: float, chunk_dur: float, chunk_mp3: Path, model: str, key: str) -> list[dict]:
    """Align lines within a local audio chunk (zero cumulative drift)."""
    prompt = f"""This audio chunk starts at {format_time_sec(chunk_start)} ({chunk_start:.2f}s of the song) and lasts {chunk_dur:.1f} seconds.
Lines to align:
{chr(10).join(lines)}

Find the start timestamp of each line in seconds relative to 0.00s of this chunk.
Format: JSON array [{{"snippet_sec": <float>, "line": "..."}}]
"""
    res = call_gemini_json(prompt, chunk_mp3, model, key, timeout=60)
    out = []
    for item in res:
        snip_s = float(item.get("snippet_sec") or 0.0)
        abs_s = chunk_start + snip_s
        out.append({"stanza_idx": stanza_idx, "abs_sec": abs_s, "line": item.get("line") or ""})
    return out


def verify_line_snippet(src_audio: Path, cand_sec: float, line_text: str, tmpdir: Path, model: str, key: str) -> tuple[float, float]:
    """Extract a tight 4-second snippet around candidate timestamp and measure exact syllable onset."""
    snip_start = max(0.0, cand_sec - 1.5)
    snip_dur = 4.2
    snip_mp3 = tmpdir / f"snip_{cand_sec:.2f}.mp3"
    try:
        extract_chunk_mp3(src_audio, snip_mp3, snip_start, snip_dur)
    except Exception:
        return cand_sec, 0.0

    prompt = f"""Target line: "{line_text}".
In this 4.2-second audio snippet, at what exact second from 0.00s does the VERY FIRST SYLLABLE of "{line_text}" begin being sung?
If sung in this clip, return JSON: {{"found": true, "offset_sec": <float>}}
If not sung in this clip, return: {{"found": false}}"""

    try:
        data = call_gemini_json(prompt, snip_mp3, model, key, timeout=30)
        if data.get("found") and "offset_sec" in data:
            ver_sec = snip_start + float(data["offset_sec"])
            shift = ver_sec - cand_sec
            return ver_sec, shift
    except Exception:
        pass
    return cand_sec, 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audio", type=Path, required=True, help="playback all.wav or guide audio")
    ap.add_argument("--lyrics", type=Path, help="file containing plain lyric lines")
    ap.add_argument("--text", help="raw lyrics string (if not passing file)")
    ap.add_argument("--song", type=Path, help="song folder (e.g. music/songs/<Song>) for mix.json structure cues")
    ap.add_argument("--out", type=Path, required=True, help="output TSV path (lyrics-timed/NN.tsv)")
    ap.add_argument("--lead-in", type=float, default=0.40, help="stage pre-roll in seconds (default: 0.4s before vocal)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Gemini model (default: {DEFAULT_MODEL})")
    args = ap.parse_args()

    if not args.lyrics and not args.text:
        ap.error("Must provide either --lyrics <file> or --text '<lyrics>'")

    raw_lyrics = args.lyrics.read_text(encoding="utf-8") if args.lyrics else args.text
    stanzas = parse_stanzas(raw_lyrics)
    total_lines = sum(len(st) for st in stanzas)
    if not total_lines:
        sys.exit("Error: no lyric lines found")

    print(f"Loaded lyrics: {len(stanzas)} stanzas, {total_lines} total lines.")
    key = get_gemini_api_key()
    total_dur = get_audio_duration(args.audio)

    cues = []
    if args.song:
        cues = get_cue_anchors(args.song)
        if cues:
            print(f"Loaded {len(cues)} arrangement cue landmarks from {args.song / 'mix.json'}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        full_mp3 = tmp_dir / "full_track.mp3"
        print(f"Compressing audio track for macro pass: {args.audio} -> {full_mp3}")
        extract_chunk_mp3(args.audio, full_mp3, 0.0, total_dur)

        # Step 1: Find coarse stanza boundaries
        print(f"\n[Step 1/3] Determining coarse stanza boundaries ({len(stanzas)} stanzas)...")
        t0 = time.time()
        boundaries = find_macro_stanza_boundaries(full_mp3, total_dur, stanzas, cues, args.model, key)
        print(f"Stanza boundaries established in {time.time() - t0:.2f}s:")
        for idx, (b_sec, st) in enumerate(zip(boundaries, stanzas)):
            print(f"  Stanza {idx + 1:02d} @ {format_time_sec(b_sec)}: {st[0][:36]}")

        # Step 2: Sectional alignment within local chunks
        print(f"\n[Step 2/3] Aligning lines within local section chunks in parallel...")
        chunk_tasks = []
        for i, (b_sec, st) in enumerate(zip(boundaries, stanzas)):
            c_start = max(0.0, b_sec - 2.0)
            nxt_sec = boundaries[i + 1] if i + 1 < len(boundaries) else total_dur
            c_dur = max(6.0, (nxt_sec - c_start) + 3.0)
            c_mp3 = tmp_dir / f"chunk_{i}.mp3"
            extract_chunk_mp3(args.audio, c_mp3, c_start, c_dur)
            chunk_tasks.append((i, st, c_start, c_dur, c_mp3))

        t0 = time.time()
        st_aligned = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
            futs = {
                ex.submit(align_single_stanza, i, st, c_start, c_dur, c_mp3, args.model, key): i
                for (i, st, c_start, c_dur, c_mp3) in chunk_tasks
            }
            for fut in concurrent.futures.as_completed(futs):
                res = fut.result()
                s_id = res[0]["stanza_idx"] if res else futs[fut]
                print(f"  [Chunk {s_id + 1:02d}/{len(chunk_tasks):02d}] aligned ✓", flush=True)
                st_aligned.append(res)
        st_aligned.sort(key=lambda x: x[0]["stanza_idx"] if x else 0)
        print(f"Local chunk alignments finished in {time.time() - t0:.2f}s", flush=True)

        # Flatten candidate lines grouped by stanza
        stanzas_with_times = []
        for lines_out in st_aligned:
            stanzas_with_times.append(lines_out)

        # Step 3: Automated Micro-Snippet Verification (The Guardrail)
        print(f"\n[Step 3/3] Running automated micro-snippet verification on key audio snippets...", flush=True)
        lines_to_verify = []
        for s_idx, st_rows in enumerate(stanzas_with_times):
            for r_idx, row in enumerate(st_rows):
                # Verify first 2 lines of every stanza, plus any line with large gap
                if r_idx < 2 or (r_idx > 0 and (row["abs_sec"] - st_rows[r_idx - 1]["abs_sec"] > 4.5)):
                    lines_to_verify.append((s_idx, r_idx, row["abs_sec"], row["line"]))

        print(f"Verifying {len(lines_to_verify)} key line onsets on 4-second audio snippets...", flush=True)
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            ver_futs = {
                ex.submit(verify_line_snippet, args.audio, cand, line_tx, tmp_dir, args.model, key): (s_idx, r_idx)
                for (s_idx, r_idx, cand, line_tx) in lines_to_verify
            }
            for fut in concurrent.futures.as_completed(ver_futs):
                s_idx, r_idx = ver_futs[fut]
                ver_sec, shift = fut.result()
                old_sec = stanzas_with_times[s_idx][r_idx]["abs_sec"]
                line_tx = stanzas_with_times[s_idx][r_idx]["line"]
                if abs(shift) > 0.15:
                    print(f"  [Verified] \"{line_tx[:30]}\": {format_time_sec(old_sec)} -> {format_time_sec(ver_sec)} (shift {shift:+.2f}s) ✓", flush=True)
                    stanzas_with_times[s_idx][r_idx]["abs_sec"] = ver_sec

        print(f"Snippet verification guardrail finished in {time.time() - t0:.2f}s", flush=True)

    # Step 4: Apply Stage Lead-In and enforce strictly increasing timestamps
    cur_sec = -1.0
    final_output_blocks = []
    lead_in = args.lead_in

    for st_rows in stanzas_with_times:
        block_lines = []
        for row in st_rows:
            target_sec = max(0.0, row["abs_sec"] - lead_in)
            if target_sec <= cur_sec:
                target_sec = cur_sec + 0.4
            cur_sec = target_sec
            block_lines.append(f"{format_time_sec(target_sec)}\t{row['line']}")
        final_output_blocks.append("\n".join(block_lines))

    # Write output TSV with blank lines between stanzas
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(final_output_blocks) + "\n")

    print(f"\n✓ Successfully wrote {total_lines} lines across {len(stanzas)} stanzas to {args.out}")


if __name__ == "__main__":
    main()
