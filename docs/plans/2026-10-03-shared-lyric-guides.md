# Shared lyric guides implementation plan

**Goal:** Publish every song's clean `auto-render/all.wav` to the existing R2,
and let Tanya's agent fetch just the selected song and produce an audible review.

**Approved design (Alex, 2026-10-03):** Use `releases.agentiqa.com`, public by
link. No extra repository, no audio in ordinary Git history. Extend the existing
publication cycle, maintain a portable catalogue in this repository. Preserve
the stage rig and require Tanya's explicit confirmation before approval.

**Architecture:** Content-addressed WAV URLs under `cherry-dash`, a versioned
`music/guide-catalog.json` with hashes, sizes, timeline and render fingerprints.
Publishing uploads and verifies bytes before updating the catalogue. The lyric
workflow checks the selected guide against the rig, downloads atomically into
its ignored cache, then builds/reviews using actual rig click/cues.

**Tech stack:** Python 3.12 stdlib, existing Node/aws-sdk R2 uploader, ffmpeg,
ffprobe, mpv; pytest and temporary Git repositories for tests. No Homebrew needed
on Tanya's already-configured Intel Mac.

## 1. Catalogue and publication

- Add `tools/guide_catalog.py`, share existing R2 credentials/uploader.
- Enumerate all song directories with mix.json, report missing all.wav rather
  than omit a song silently. Include render click/playback fingerprints and
  timeline; keep audio URL immutable by SHA-256.
- Extend `tools/sync_site.py`: normal publication includes guides;
  `--guides-only` publishes just WAVs without regenerating/deploying the site.
- Test corrupt HTTP downloads, reuse of cache, changed render versions and
  missing media. Upload all available guides and verify HTTP bytes/types.

## 2. On-demand workflow

- Add `guide NN` and `preview NN` commands to `lyric_workflow.py`; make build's
  explicit audio optional. Resolve by factory_dir, never by setlist position.
- Materialize only selected rig audio and selected lyric metadata from sparse
  checkout; never disable sparse checkout or fetch every media blob.
- Verify published hashes and rig timeline fingerprints; refuse stale/missing
  guides with exact filename and repair command. Require both real click/cues.
- Use published timeline for JamZone offset when local timeline is absent.
- Fix the existing empty factory_dir for Мелом in the main manifest only.
- Test selective download, sparse checkout, stale guide, absent cues and an
  actual short mpv preview. Run existing lyric workflow regressions.

## 3. Document the permanent process

- Update `.agents/skills/tanya-texts/SKILL.md`, `docs/vocalist-workflow.md`,
  `docs/tanya-start.md`, `CLAUDE.md`, and relevant wiki pages.
- Describe publisher render → publish → commit/push catalogue and recipient
  sync → preview NN → corrections → explicit confirmation.
- Clarify that silent stage clips are not synchronization review videos.

## 4. Verify clip 13

- Record actual signal reconstruction/cross-correlation evidence (early,
  middle, late), original stem offset and exact rig file hashes.
- Fetch the published guide through the same command Tanya will use; build the
  full review, verify video/audio streams, duration and visible subtitles.
- Leave approval empty; report software checks separately from human review.
- Review diff; commit/push only task files in the main repository so Tanya can
  obtain the new process. Confirm remote commit. No rig commits or delivery.
