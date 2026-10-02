#!/usr/bin/env python3
"""Prepare -> review -> approve -> save; optionally deliver one song to the rig.

See docs/vocalist-workflow.md. All Git pushes are ordinary (never forced).
Local audio paths/previews live in .local; portable review receipts are versioned.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import make_song_clip as maker
from make_review_video import combined_ass, _maxvol

FIELDS = "set song clip pc_field source cat factory_dir bed_dir concert_patch".split()
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aif", ".aiff", ".flac"}


def run(args, cwd=None):
    p = subprocess.run([str(x) for x in args], cwd=cwd, capture_output=True, text=True)
    if p.returncode:
        raise ValueError(f"{' '.join(str(x) for x in args[:3])} failed:\n{p.stderr.strip()}")
    return p.stdout.strip()


def git(repo, *args):
    return run(["git", "-C", repo, *args])


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def inside(root, relative):
    p = (root / relative).resolve()
    if not relative or Path(relative).is_absolute() or not p.is_relative_to(root.resolve()):
        raise ValueError(f"path must stay inside repository: {relative!r}")
    return p


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    temp.replace(path)


def read_json(path):
    if not path.is_file():
        raise ValueError(f"missing {path}; run the preceding workflow step")
    return json.loads(path.read_text())


def read_manifest(path=None, text=None):
    if text is None:
        text = path.read_text()
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    if reader.fieldnames != FIELDS:
        raise ValueError("unexpected songs.tsv columns")
    rows = list(reader)
    clips, pcs, titles = set(), set(), set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("malformed songs.tsv row")
        n, pc = int(row["clip"]), int(row["pc_field"])
        if not 1 <= n <= 127 or pc != n + 1 or n in clips or pc in pcs or not row["song"].strip():
            raise ValueError("invalid/duplicate clip or PC in songs.tsv")
        if row["song"].casefold() in titles:
            raise ValueError("duplicate song name in songs.tsv")
        clips.add(n); pcs.add(pc); titles.add(row["song"].casefold())
    return rows


def selected(rows, n):
    return next((r for r in rows if int(r["clip"]) == n), None)


def write_manifest(path, rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    # Validate before changing the on-disk file.
    read_manifest(text=out.getvalue())
    path.write_text(out.getvalue())


def duration(path):
    value = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                       "-of", "csv=p=0", path]))
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"invalid media duration: {path}")
    return value


def branch(repo):
    return git(repo, "symbolic-ref", "--short", "HEAD")


def refresh(repo):
    """Fetch and fast-forward only. Never reset, stash, or resolve divergence."""
    name = branch(repo)
    git(repo, "fetch", "origin")
    remote = git(repo, "ls-remote", "origin", f"refs/heads/{name}")
    if not remote:
        return
    upstream = remote.split()[0]
    # It may have advanced since fetch; fetch the branch again rather than guess.
    git(repo, "fetch", "origin", name)
    upstream = git(repo, "rev-parse", "FETCH_HEAD")
    head = git(repo, "rev-parse", "HEAD")
    base = git(repo, "merge-base", head, upstream)
    if base == head:
        git(repo, "merge", "--ff-only", upstream)
    elif base != upstream:
        raise ValueError(f"diverged branches in {repo}; resolve with Alex, then retry")


def push_verified(repo):
    name, commit = branch(repo), git(repo, "rev-parse", "HEAD")
    try:
        git(repo, "push", "-u", "origin", f"HEAD:refs/heads/{name}")
        git(repo, "fetch", "origin", name)
        git(repo, "merge-base", "--is-ancestor", commit, "FETCH_HEAD")
    except ValueError as e:
        raise ValueError(f"push NOT confirmed; local commit {commit} retained. Retry after fixing access/network.\n{e}") from e
    print(f"Saved on remote: {git(repo, 'remote', 'get-url', 'origin')} @ {commit}")
    return commit


def no_staging(repo):
    if git(repo, "diff", "--cached", "--name-only"):
        raise ValueError(f"existing staged changes in {repo}; inspect them before saving")


def commit_paths(repo, paths, message):
    no_staging(repo)
    git(repo, "add", "--", *paths)
    if git(repo, "diff", "--cached", "--name-only"):
        git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def render_review(canvas, ass, audio, output):
    with tempfile.TemporaryDirectory() as tmp:
        subtitles = combined_ass(str(ass), duration(audio), tmp)
        run(["mpv", canvas, f"--audio-file={audio}", "--aid=1", f"--sub-files={subtitles}",
             f"--o={output}", "--ovc=libx264", "--oac=aac", "--no-config", "--really-quiet"])


def mix_review_audio(guide, bed, output):
    """Guide + the actual rig's click/cues, peak normalized together to -1 dBFS.

    The guide must already be on the playback timeline (no stretching here).
    Human review checks its alignment against these real stage cues.
    """
    inputs, gains = [guide], [.85]
    for name, boost in [("click.wav", 10), ("cues.wav", 5)]:
        path = bed / name
        if path.is_file() and path.resolve() != guide.resolve():
            inputs.append(path)
            gains.append(.85 * 10 ** (boost / 20))
    if len(inputs) == 1:
        raise ValueError("rig click/cues missing (or selected as guide); supply a music/vocal reference")
    filters = ";".join(f"[{i}:a]volume={gain}[a{i}]" for i, gain in enumerate(gains)) + ";"
    filters += "".join(f"[a{i}]" for i in range(len(inputs)))
    filters += f"amix=inputs={len(inputs)}:duration=first:normalize=0"
    peak = _maxvol(filters + ",volume=-12dB,volumedetect", [str(p) for p in inputs]) + 12
    if not math.isfinite(peak):
        raise ValueError("review audio is silent")
    command = ["ffmpeg", "-y", "-v", "error"]
    for path in inputs:
        command += ["-i", path]
    run(command + ["-filter_complex", filters + f",volume={-1 - peak:.3f}dB[m]",
                   "-map", "[m]", output])


class Workspace:
    def __init__(self, root, rig=None):
        self.root = Path(root).resolve()
        self.here = self.root / "tools/lyric-launcher"
        self.rig = Path(rig or os.environ.get("CHERRY_RIG_REPO") or
                        self.root.parent / "cherry-daddies-2000").expanduser().resolve()

    def row(self, n):
        row = selected(read_manifest(self.here / "songs.tsv"), n)
        if not row:
            raise ValueError(f"clip {n:02} missing in songs.tsv; register the new song first")
        return row

    def local(self, n):
        return self.here / ".local" / f"{n:02}.json"

    def receipt(self, n):
        return self.here / "reviews" / f"{n:02}.json"

    def source_files(self, n):
        row = self.row(n)
        paths = []
        for folder, extensions in [("lyrics-timed", ["tsv", "raw.json", "review.txt"]),
                                   ("lyrics-manual", ["txt"]), ("overrides", ["tsv"])]:
            paths += [self.here / folder / f"{n:02}.{ext}" for ext in extensions]
        if row["factory_dir"]:
            song = inside(self.root, row["factory_dir"])
            paths += [song / "mix.json", song / "auto-render/timeline.json"]
        paths += [self.here / name for name in ["make_song_clip.py", "make_static_clip.py", "lyric_workflow.py"]]
        return {str(p.relative_to(self.root)): sha(p) for p in paths if p.is_file()}

    def clip_files(self, n):
        return {ext: sha(self.here / "clips" / f"{n:02}.{ext}") for ext in ["ass", "mp4"]}

    def rig_snapshot(self, n):
        row = self.row(n)
        rows = read_manifest(self.rig / "lyrics/songs.tsv")
        old = selected(rows, n)
        if old and any(old[k] != row[k] for k in ["song", "pc_field", "bed_dir", "concert_patch"]):
            raise ValueError("rig mapping changed/collides with this song; reconcile with keyboardist")
        if any(r["song"].casefold() == row["song"].casefold() and int(r["clip"]) != n for r in rows):
            raise ValueError("song already has a different clip number in rig")
        bed = inside(self.rig, row["bed_dir"])
        files = sorted(p for p in bed.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES)
        if not files:
            raise ValueError(f"rig playback audio missing: {bed}; download it / prepare the song first")
        files += [self.rig / "lyrics/clips" / f"{n:02}.{ext}" for ext in ["ass", "mp4"]]
        return {"row": old, "files": {str(p.relative_to(self.rig)): sha(p) if p.is_file() else None for p in files}}

    def build(self, n, audio, offset=None):
        row, audio = self.row(n), Path(audio).expanduser().resolve()
        manifest_before = (self.here / "songs.tsv").read_bytes()
        sources_before, audio_before = self.source_files(n), sha(audio)
        snapshot = self.rig_snapshot(n)
        dur = duration(audio)
        bed = inside(self.rig, row["bed_dir"])
        rig_duration = max(duration(p) for p in bed.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES)
        if abs(dur - rig_duration) > .25:
            raise ValueError(f"reference audio ({dur:.2f}s) differs from rig playback ({rig_duration:.2f}s); align the reference first")
        timed = self.here / "lyrics-timed" / f"{n:02}.tsv"
        manual = self.here / "lyrics-manual" / f"{n:02}.txt"
        out = self.here / "clips"
        out.mkdir(parents=True, exist_ok=True)
        # Any interrupted/failed rebuild must not leave a usable old build receipt.
        self.local(n).unlink(missing_ok=True)
        tiles = None
        if timed.is_file():
            lines, offset = maker.parse_lines_table(timed), 0.0
            row["source"] = "dynamic"
        elif row["source"] == "jamzone":
            if offset is None:
                timeline = inside(self.root, row["factory_dir"]) / "auto-render/timeline.json"
                offset = read_json(timeline)["offset_sec"]
            tiles_path = Path(maker.JAMS) / row["cat"] / "tiles.json"
            tiles = {"cat": row["cat"], "sha256": sha(tiles_path)}
            words, _ = maker.lead_words(maker.dj(row["cat"], "tiles.json"))
            lines = maker.pack_lines(maker.collapse_letter_runs(maker.group_lines(words)))
        elif manual.is_file():
            import make_static_clip as static
            text = manual.read_text().splitlines()
            if not any(s.strip() for s in text):
                raise ValueError("empty static lyrics")
            cols, size = static.layout(static.collapse_consecutive(static.dedup_repeats(text)))
            static.ass(out / f"{n:02}.ass", row["song"], cols, size)
            row["source"] = "static"
            lines, offset = None, 0.0
        else:
            raise ValueError("no lyrics; transcribe audio or download the JamZone song first")
        if lines is not None:
            override = self.here / "overrides" / f"{n:02}.tsv"
            if override.is_file():
                lines = maker.apply_overrides(lines, offset, override)
            previous = -1
            if not lines or not math.isfinite(offset):
                raise ValueError("empty lyrics / invalid offset")
            for start, end, text in lines:
                t = start + offset
                if not math.isfinite(t) or not math.isfinite(end) or not 0 <= t < dur or t <= previous or not text.strip():
                    raise ValueError(f"invalid/out-of-range lyric at {t}: {text}")
                previous = t
            maker.make_ass(out / f"{n:02}.ass", row["song"], lines, dur, offset)
        maker.make_black(out / f"{n:02}.mp4", dur)
        if ((self.here / "songs.tsv").read_bytes() != manifest_before
                or self.source_files(n) != sources_before or sha(audio) != audio_before
                or self.rig_snapshot(n) != snapshot
                or (tiles and sha(tiles_path) != tiles["sha256"])):
            raise ValueError("inputs changed during encoding; stale build discarded, run build again")
        rows = read_manifest(self.here / "songs.tsv")
        rows = [row if int(r["clip"]) == n else r for r in rows]
        write_manifest(self.here / "songs.tsv", rows)
        state = {"schema": 1, "row": row, "sources": sources_before, "clips": self.clip_files(n),
                 "audio_sha256": audio_before, "audio_duration": dur, "offset_sec": offset,
                 "jamzone": tiles, "rig": snapshot}
        write_json(self.local(n), {"audio_path": str(audio), "build": state})
        print(f"Built {n:02} {row['song']}; next: review")
        return state

    def validate_build(self, n):
        local = read_json(self.local(n))
        state = local["build"]
        if state["row"] != self.row(n) or state["sources"] != self.source_files(n) or state["clips"] != self.clip_files(n):
            raise ValueError("sources/clip changed: stale build; rebuild and review again")
        audio = Path(local["audio_path"])
        if sha(audio) != state["audio_sha256"]:
            raise ValueError("reference audio changed: stale build")
        if state["jamzone"]:
            tile = Path(maker.JAMS) / state["jamzone"]["cat"] / "tiles.json"
            if sha(tile) != state["jamzone"]["sha256"]:
                raise ValueError("JamZone tiles changed: stale build")
        if abs(duration(self.here / "clips" / f"{n:02}.mp4") - state["audio_duration"]) > .25:
            raise ValueError("clip duration changed")
        return local

    def review(self, n):
        local = self.validate_build(n)
        refresh(self.rig)
        if self.rig_snapshot(n) != local["build"]["rig"]:
            raise ValueError("rig changed since build; rebuild against current playback")
        output = self.here / ".local" / f"{n:02}-review.mp4"
        mixed = self.here / ".local" / f"{n:02}-review.wav"
        mix_review_audio(Path(local["audio_path"]), inside(self.rig, self.row(n)["bed_dir"]), mixed)
        render_review(self.here / "clips" / f"{n:02}.mp4", self.here / "clips" / f"{n:02}.ass",
                      mixed, output)
        # Recheck after rendering, before attaching a receipt to these bytes.
        self.validate_build(n)
        receipt = {"build": local["build"], "preview_sha256": sha(output), "approved_by": None}
        write_json(self.receipt(n), receipt)
        print(f"Review words, repeats and playback sync: {output}")
        return output

    def check(self, n, require_approval=True):
        local = self.validate_build(n)
        receipt = read_json(self.receipt(n))
        if receipt["build"] != local["build"]:
            raise ValueError("stale review; generate and watch a new preview")
        preview = self.here / ".local" / f"{n:02}-review.mp4"
        if not preview.is_file() or sha(preview) != receipt["preview_sha256"]:
            raise ValueError("preview missing/changed; regenerate review")
        if require_approval and not receipt["approved_by"]:
            raise ValueError("human review required: ask vocalist to watch and confirm preview")
        refresh(self.rig)
        current = self.rig_snapshot(n)
        expected = receipt["build"]["rig"]
        if current != expected:
            # Our own delivery changes the selected clips/row. That does not
            # invalidate the approved content, but any subsequent audio change does.
            delivered_path = self.rig / "lyrics/deliveries" / f"{n:02}.json"
            delivered = read_json(delivered_path) if delivered_path.is_file() else {}
            after_our_delivery = dict(expected["files"])
            for ext, digest in receipt["build"]["clips"].items():
                after_our_delivery[f"lyrics/clips/{n:02}.{ext}"] = digest
            if not (current == {"row": receipt["build"]["row"], "files": after_our_delivery}
                    and delivered.get("receipt_sha256") == sha(self.receipt(n))
                    and delivered.get("clips") == receipt["build"]["clips"]):
                raise ValueError("rig song/audio changed since review; rebuild and review again")
        return receipt

    def approve(self, n, reviewer):
        if not reviewer.strip():
            raise ValueError("reviewer name required")
        receipt = self.check(n, require_approval=False)
        receipt["approved_by"] = reviewer.strip()
        write_json(self.receipt(n), receipt)
        print(f"Review confirmed by {reviewer}; next: save")

    def save_paths(self, n):
        paths = [self.here / "songs.tsv", self.here / "clips" / f"{n:02}.ass", self.receipt(n)]
        for folder, suffixes in [("lyrics-timed", ["tsv", "raw.json", "review.txt"]),
                                 ("lyrics-manual", ["txt"]), ("overrides", ["tsv"])]:
            paths += [self.here / folder / f"{n:02}.{s}" for s in suffixes]
        # Include tracked deletions as well as present files.
        return [str(p.relative_to(self.root)) for p in paths
                if p.exists() or git(self.root, "ls-files", "--", str(p.relative_to(self.root)))]

    def save(self, n, message):
        no_staging(self.root)
        refresh(self.root)
        receipt = self.check(n)
        manifest_path = str((self.here / "songs.tsv").relative_to(self.root))
        previous = read_manifest(text=git(self.root, "show", f"HEAD:{manifest_path}"))
        current = read_manifest(self.here / "songs.tsv")
        if [r for r in previous if int(r["clip"]) != n] != [r for r in current if int(r["clip"]) != n]:
            raise ValueError("other songs.tsv rows changed; save/reconcile those separately")
        paths = self.save_paths(n)
        dependencies = [p for p in receipt["build"]["sources"] if p not in paths]
        if dependencies and git(self.root, "status", "--porcelain", "--", *dependencies):
            raise ValueError("audio recipe/generator changes need their own reviewed commit before lyric save")
        commit_paths(self.root, paths, message)
        return push_verified(self.root)

    def deliver(self, n, apply=False, message=None):
        receipt = self.check(n)
        paths = self.save_paths(n)
        if git(self.root, "status", "--porcelain", "--", *paths):
            raise ValueError("save and commit the source before delivery")
        source = git(self.root, "log", "-1", "--format=%H", "--", str(self.receipt(n).relative_to(self.root)))
        if not source:
            raise ValueError("save the reviewed source first")
        git(self.root, "fetch", "origin", branch(self.root))
        try:
            git(self.root, "merge-base", "--is-ancestor", source, "FETCH_HEAD")
        except ValueError as e:
            raise ValueError("source commit not on remote; run save first") from e
        if git(self.rig, "status", "--porcelain"):
            raise ValueError("rig has local changes; inspect/save them before delivery")
        refresh(self.rig)
        target_manifest = self.rig / "lyrics/songs.tsv"
        rows, row = read_manifest(target_manifest), self.row(n)
        target_receipt = self.rig / "lyrics/deliveries" / f"{n:02}.json"
        provenance = {"source_commit": source, "source_remote": git(self.root, "remote", "get-url", "origin"),
                      "receipt_sha256": sha(self.receipt(n)), "clips": receipt["build"]["clips"],
                      "approved_by": receipt["approved_by"], "wiring": "existing mapping; runtime not checked" if receipt["build"]["rig"]["row"] else "needs verification in MainStage"}
        current_rig = self.rig_snapshot(n)
        old_audio = {p: h for p, h in receipt["build"]["rig"]["files"].items() if not p.startswith("lyrics/clips/")}
        current_audio = {p: h for p, h in current_rig["files"].items() if not p.startswith("lyrics/clips/")}
        if old_audio != current_audio:
            raise ValueError("rig audio changed since review; rebuild and review again")
        same_delivery = (target_receipt.is_file() and read_json(target_receipt) == provenance
                         and selected(rows, n) == row
                         and all((self.rig / "lyrics/clips" / f"{n:02}.{ext}").is_file()
                                 and sha(self.rig / "lyrics/clips" / f"{n:02}.{ext}") == digest
                                 for ext, digest in provenance["clips"].items()))
        if same_delivery:
            # A previous push may have failed; don't create another commit.
            if apply:
                return push_verified(self.rig)
            return git(self.rig, "rev-parse", "HEAD")
        if current_rig != receipt["build"]["rig"]:
            raise ValueError("rig song/audio changed since review; fetch, rebuild and review again")
        print(f"Deliver only {n:02} {row['song']}: ass + mp4 + selected manifest row; source {source}")
        if not apply:
            print("Dry-run. Use --apply to commit and push this delivery.")
            return None
        no_staging(self.rig)
        outputs = []
        for ext in ["ass", "mp4"]:
            target = self.rig / "lyrics/clips" / f"{n:02}.{ext}"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.here / "clips" / target.name, target)
            outputs.append(str(target.relative_to(self.rig)))
        if selected(rows, n):
            rows = [row if int(r["clip"]) == n else r for r in rows]
        else:
            rows.append(row)
        write_manifest(target_manifest, rows)
        write_json(target_receipt, provenance)
        outputs += [str(target_manifest.relative_to(self.rig)), str(target_receipt.relative_to(self.rig))]
        commit_paths(self.rig, outputs, f"{message or ('lyrics: ' + row['song'])}\n\nSource-commit: {source}")
        result = push_verified(self.rig)
        print("Rig GitHub updated. Keyboardist still needs to Pull; MainStage wiring: " + provenance["wiring"])
        return result

    def doctor(self):
        missing = []
        for tool in ["git", "gh", "uv", "ffmpeg", "ffprobe", "mpv"]:
            print(f"{tool}: {shutil.which(tool) or 'MISSING'}")
            if not shutil.which(tool):
                missing.append(tool)
        print(f"Main repository: {self.root}")
        print(f"Rig repository: {self.rig}")
        print(f"JamZone downloads: {maker.JAMS} ({'found' if Path(maker.JAMS).is_dir() else 'not found'})")
        for repo in [self.root, self.rig]:
            try:
                print(f"{repo.name}: {git(repo, 'remote', 'get-url', 'origin')}")
                git(repo, "ls-remote", "origin", "HEAD")
                for key in ["user.name", "user.email"]:
                    if not git(repo, "config", "--get", key):
                        missing.append(f"{repo.name}: {key}")
            except ValueError as e:
                missing.append(str(e))
        if missing:
            raise ValueError("setup incomplete: " + "; ".join(missing))
        print("Tools/read access OK. Write access is confirmed by the actual push.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--rig", type=Path)
    subs = ap.add_subparsers(dest="command", required=True)
    subs.add_parser("doctor")
    subs.add_parser("sync")
    for cmd in ["build", "review", "approve", "check", "save", "deliver"]:
        sub = subs.add_parser(cmd)
        sub.add_argument("index", type=int)
        if cmd == "build":
            sub.add_argument("--audio", type=Path, required=True)
            sub.add_argument("--offset", type=float)
        if cmd == "approve":
            sub.add_argument("--reviewer", required=True)
        if cmd in ["save", "deliver"]:
            sub.add_argument("--message", default=None)
        if cmd == "deliver":
            sub.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    ws = Workspace(args.root, args.rig)
    try:
        if args.command == "doctor":
            ws.doctor()
        elif args.command == "sync":
            refresh(ws.root); refresh(ws.rig)
        elif args.command == "build":
            ws.build(args.index, args.audio, args.offset)
        elif args.command == "review":
            ws.review(args.index)
        elif args.command == "approve":
            ws.approve(args.index, args.reviewer)
        elif args.command == "check":
            ws.check(args.index); print("Checks and review receipt OK")
        elif args.command == "save":
            ws.save(args.index, args.message or f"lyrics: {ws.row(args.index)['song']}")
        else:
            ws.deliver(args.index, args.apply, args.message)
    except (ValueError, OSError, KeyError) as e:
        ap.exit(1, f"NOT COMPLETED: {e}\n")


if __name__ == "__main__":
    main()
