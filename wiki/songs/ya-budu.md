---
type: song
updated: 2026-10-05
title: Я буду
artist: 5sta Family & 23:45
set: tryout batch 2026-09
---

# Я буду (5sta Family & 23:45)

Tryout 2026-09. 2026-10-05: по указанию Alex `pb-other` скомпонован из оригинальных стемов (guitars, piano, keys, other — где `other` заглушен с 0:13), а из караоке-минусовки взяты `backing_vocals` (вариант `redacted`, точно сфазирован с оригиналом) и `bass` (жирный суб-бас из минусовки, скомпенсирован по фазе). Барабаны, метроном и вокал — из оригинального импорта. В плейбеке: `pb-other` (`backing_vocals` [караоке redacted], `guitars`, `piano`, `keys`, `other` [до 0:13]), `pb-drums` (drums), `pb-bass` (`bass` из караоке). Живые партии: Alex (акустическая/электро гитара), Roma (`keys`), Steve (`drums`), Tanya (`vocals`). Шина `pb-other-keys` удалена.

## Сводка

- **bpm:** 90.0 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 90.0`), дрейф оригинальной записи отсутствует (±6 мс выровнены RubberBand в 0).
- **pitch_semitones:** 0 (A minor).
- **pb-other:** `backing_vocals` (караоке redacted), `guitars`, `piano`, `keys`, `other` (вступительный синт-хук `other` звучит с 0:00 до 0:13, после 0:13 заглушен).
- **pb-drums:** `drums` (установка для репетиций).
- **pb-bass:** `bass` (из караоке-минусовки, скомпенсирован на 20 мс и отварплен).
- **players:** alex: `guitars`, roma: `keys`, steve: `drums`, tanya: `vocals`.
- **mix.json:** `music/songs/5sta Family & 23:45 - Я буду/mix.json`
- **Рендер:** OFF +5.241 с, lead +1 такт под стартовую фразу, длина 189.3 с (71 такт).

## Cue

3 cue:
1. `bar 1.1` (5.333 с) — `"Я буду all in"` → «Я буду» + «all in ready go», на 1.1 вступают drums и keys (интро).
2. `bar 9.1` (26.667 с) — `"chorus in"` → «chorus in ready go», на 9.1 вступает припев («Малыш, ты меня не знаешь...»).
3. `bar 17.1` (48.000 с) — `"verse in"` → «verse in ready go», на 17.1 вступает куплет (рэп «Зачем ему все эти деньги...»).

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`, `all.wav`
- `pb-other.wav`, `pb-drums.wav`, `pb-bass.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`, `pb-bass.mp3`
- `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`
