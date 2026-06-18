# lyric-launcher — synced lyrics on the stage monitor (POC)

Paint song lyrics on a stage monitor, frame-synced to the song, driven from
the keyboardist's MainStage laptop. No second GUI app, no license.

## How it works

```
MainStage patch / pad  --MIDI Program Change-->  launcher.py  --IPC-->  mpv (fullscreen on monitor)
                                                      |
                                                      +-- loads clips/NN.mp4  (the surface = the clock)
                                                      +-- attaches clips/NN.ass (timed lyric lines)
```

- One persistent **mpv** window, fullscreen on display 2, muted (band audio
  stays in MainStage). It idles on black until a song is selected.
- A **Program Change N** over MIDI -> launcher loads `clips/NN.mp4` from t=0
  and attaches `clips/NN.ass`. **mpv's own libass renders the lyrics** — so
  lyrics are an editable subtitle track; change words without re-encoding.
- Sync = the clip is pre-rendered on the song's timeline; both audio and the
  lyric clip are linear media on one machine, so they don't drift within a
  song. Tightness = how close the PC fires to the playback start.

Why subtitles, not burned-in text: this machine's `ffmpeg` is a stripped
build with no `drawtext`/subtitle filters. mpv ships its own libass, so it
renders `.ass` live. Bonus — lyrics stay editable.

## Files

| file | role |
|------|------|
| `launcher.py` | the listener. Opens MIDI in + drives mpv over a unix-socket IPC. |
| `send_pc.py` | POC test sender — plays MainStage's role (fire a Program Change). |
| `clips/make_clips.py` | generates demo `NN.mp4` (black) + `NN.ass` (timed lyrics). |
| `clips/NN.mp4` + `NN.ass` | one pair per song, keyed by Program Change number. |

Python deps live in `.venv` (`mido`, `python-rtmidi`). `mpv` + `ffmpeg` via brew.

## POC quickstart (no MainStage needed)

```bash
cd tools/lyric-launcher
python3 clips/make_clips.py            # build demo clips (once)

# terminal 1 — start the launcher (dev: small window on the main screen)
.venv/bin/python launcher.py --windowed

# terminal 2 — fire songs
.venv/bin/python send_pc.py 1          # -> SONG 1 clip plays from 0
.venv/bin/python send_pc.py 2          # swap to SONG 2
.venv/bin/python send_pc.py --blank    # blank the screen (MIDI note 60)
```

Validated end-to-end: PC -> launcher -> mpv swaps clip + lyric track, lines
appear on their cues. (mpv commands are one-way; the launcher does not depend
on reading IPC replies.)

## MainStage sync — what we learned (important)

We tested every way to make the lyrics auto-follow MainStage's playback. MainStage
is a poor sync source:
- **No song position.** It never sends Song Position Pointer — scrub/seek is invisible.
- **Transport is unreliable.** `start`/`stop`/`continue` sometimes arrive, sometimes
  not (especially once MIDI clock is on).
- **Clock is free-running.** With "send MIDI clock" enabled it streams continuously at
  the *concert tempo* regardless of play/stop — useless for detecting transport, and it
  must be set to the song bpm or it drifts against the clip.
- **Native display is unusable.** A Parameter Text control bound to Playback ▸ Status ▸
  Current Marker Name *does* import our embedded WAV markers and follow the playhead, but
  it auto-scales the font per line and abbreviates long values ("W,W'MTo") — fine for a
  short section tag, useless for full lyric lines. (Embedded-marker pipeline:
  `embed_markers.py`.)

**Conclusion: don't chase MainStage. Use a deterministic trigger.** A single MIDI note
(or Program Change) fires the clip instantly and reliably — that always worked. The clip
then free-runs; as long as the MainStage patch **tempo = song bpm**, the bed, the
arpeggiators, and the lyric clip all run at one speed and stay locked for the whole song.

Fully automatic + scrub-aware would require a real clock master (Ableton Live clocking
MainStage); MainStage alone can't do it.

## Trigger model (current)

- **GO note** (`--go-note`, default 21 = A0) → play the armed song from 0.
- **STOP note** (`--stop-note`, default 23 = B0) → reset to the title screen (rewind to
  0, paused, ready for the next GO).
- **Program Change N** → play clip NN from 0; **PC 0** → reset to title. (Use whichever
  your rig sends most easily — notes are easiest for MainStage to forward.)
- The musical keybed is ignored. `--default-clip N` arms a song at startup.
- `--chase-clock` (optional) drift-locks to MainStage's MIDI clock — only correct if the
  patch tempo equals the song bpm, else it yanks. Usually unnecessary: matched tempo +
  free-run from 0 stays locked on its own.

## Stage setup (real use)

**1. Display.** System Settings -> Displays -> arrange as **Extended** (not
mirrored). Run fullscreen on the monitor:

```bash
.venv/bin/python launcher.py --screen 1        # 0 = laptop, 1 = stage monitor
```

**2. MIDI route — two options:**

- **Virtual port (no setup):** the launcher creates a CoreMIDI destination
  named **`LyricLauncher`** (visible to every app). Point MainStage's MIDI
  output at it.
- **IAC bus (classic):** Audio MIDI Setup -> MIDI Studio -> IAC Driver ->
  enable. Then `launcher.py --port "IAC Driver Bus 1"` and send from MainStage
  to that bus.

**3. Make MainStage fire a Program Change per song — two patterns:**

- **Trigger pad (most robust):** add a screen control / hardware pad that
  sends **Program Change N** out to `LyricLauncher` (via an *External
  Instrument* channel strip routed to that port). Keyboardist hits it when the
  song starts — same gesture can also start the Playback plugin, so lyrics and
  backing track launch together.
- **Auto on patch select:** if you wire the patch's *External Instrument*
  output to send its program number to `LyricLauncher` on activation, choosing
  the patch fires the lyric clip automatically. (Verify behavior on your
  MainStage version — patch-change MIDI-out is less standard than the pad.)

Map `NN` (clip / Program Change) to your MainStage patch order.

## Next step — real lyric clips

Lyrics + timing already exist in JamZone — **no whisper, no transcription.**
JamZone's `tiles.json` stores, per syllable: `text`, `start`, `end` (seconds),
plus per-tile `sectionCaption`, `bpm`, `subBeats`. That's the data the app uses
to highlight words live. The lead-voice reader already exists:
`~/.claude/skills/jamzone-lyrics/scripts/jamzone_lyrics.py` (`words_of_group()`
returns `(start, word)` for the detected lead colour).

Real generator, per song:
- background `mp4` (black, or a looped visual / static image as video) the
  length of the song, and
- an `.ass` built from `tiles.json`: group `(start, end, word)` into lines
  (capital-word heuristic, same as the booklet) → `Dialogue` start = first
  word's `start`. Per-syllable `start/end` also enables true karaoke highlight
  (ASS `\k`), not just line reveal.

**Timeline caveat:** `tiles.json` times are on the raw stem timeline
(t=0 = song start). If MainStage plays the **auto-render** (with a count-in/lead
at the front), shift every `.ass` time by that render's count-in OFF — same
render-vs-stem frame issue as the rest of the pipeline. If it plays raw stems,
no shift.

The launcher and MIDI wiring above stay exactly the same.
