---
type: song
updated: 2026-10-28
title: Медляк
artist: Mr. Credo
set: tryout batch 2026-09
---

# Медляк (Mr. Credo)

Tryout 2026-09. Moises стемы (G minor, 105 bpm). В плейбеке: `pb-other` (`backing_vocals`, `strings`, `keys`), `pb-drums` (drums для репетиций), `pb-bass` (`bass`).

## Сводка

- **bpm:** 105.0 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 105.0`), дрейф оригинальной записи минимальный (0–36 мс за 4.5 мин).
- **pitch_semitones:** 0 (G minor).
- **pb-other:** `backing_vocals` (+0.5 dB), `keys` (+0.5 dB), `strings` (+2.5 dB) — `keys` объединены в `pb-other`, уровень поднят на +4 dB (итоговый `auto-render/pb-other.wav` −20.69 dBFS gated RMS, пик −0.4 dBFS).
- **pb-drums:** `drums` (барабаны для репетиций без барабанщика).
- **pb-bass:** `bass` (`gain_db: -2.0`).
- **players:** steve: `drums`; tanya: `vocals`.
- **mix.json:** `music/songs/Mr. Credo - Медляк/mix.json`
- **Рендер:** OFF +4.229 с, lead +2 такта под стартовую фразу, длина 269.7 с (118 тактов).

## Cue

6 cue:
1. `bar 1.1` (4.571 с) — `"Медляк synth in"` → «Медляк» + «synth in ready go», на 1.1 вступает аккордеонный синт.
2. `bar 9.1` (22.857 с) — `"drums in"` → «drums in ready go», на 9.1 вступают барабаны и бас.
3. `bar 17.1` (41.143 с) — `"verse in"` → «verse in ready go», на 17.1 вступает куплет («Сегодня в белом танце кружимся...»).
4. `bar 81.1` (187.429 с / 3:07.43) — `"stop"` → «stop in 3 · 3 2 1», отсчёт «3 2 1» на долях `80.2–80.4`, событие на последнем ударе бочки `81.1` перед брейкдауном без барабанов.
5. `bar 96.1` (221.714 с / 3:41.71) — `"drum in"` → «drum in ready go», на `96.1` возвращаются барабаны после брейкдауна.
6. `bar 113.1` (260.571 с / 4:20.57) — `"end in"` (`count: true`) → «end in 3 · 3 2 1», отсчёт «3 2 1» на долях `112.2–112.4`, событие на последнем финальном ударе барабанов `113.1`.

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`, `all.wav`
- `pb-other.wav`, `pb-drums.wav`, `pb-bass.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`, `pb-bass.mp3`
- `practice-steve.mp3`, `practice-tanya.mp3`
