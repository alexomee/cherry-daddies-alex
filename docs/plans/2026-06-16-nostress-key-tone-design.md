# No Stress — in-ear key tone for vocalist

**Date:** 2026-06-16

## Goal

Give the vocalist a pitch reference before the first entry in "No Stress", same as
"Rihanna - S&M" already has.

## Mechanism (existing, unchanged)

`jamzone_render.py` supports a `"chord": ["<note>"]` field on a cue. The render
plays `_chord_clip` — a soft synth tone — ringing one full bar before the cue's
spoken block, in the cue (in-ear) track only. The cue track is never pitch-shifted,
so the note is authored directly in the **band key**.

S&M precedent: first cue carries `"chord": ["C#4"]` (`pitch_semitones: -2`).

## Decision

- **Note: `A4`.** Measured first sung note of the lead vocal stem
  (`07_Lead_Vocal.m4a`, onset 3.84 s, f0 = 441 Hz ≈ A4 +4 cents). The phrase
  centers A4–A#4; A4 is the entry note.
- **Single note** (not a triad), mirroring S&M.
- No Stress has no `pitch_semitones` → band plays original key → `A4` is literal.

## Change

`mix.json`, first cue (`bar 3, "No Stress vocal in"`):

```json
{"bar": 3, "text": "No Stress vocal in", "chord": ["A4"], "abs_sec": ...}
```

## Side effect (expected, same as S&M)

The chord rings a bar before the block, so the render front-pads a count-in bar.
Render writes new `abs_sec`; mix.json bar numbers unchanged.

## Verify

`jamzone_render.py "Laurent Wolf & Eric Carter - No Stress"` → listen
`auto-render/cue_preview.*`: A4 tone rings the bar before "No Stress vocal in",
fades into the spoken block, vocalist enters on pitch.
