---
type: song
updated: 2026-09-12
title: Кукла колдуна
artist: Король и Шут
set: tryout batch 2026-09
---

# Кукла колдуна (Король и Шут)

Tryout 2026-09. Moises-стемы (D minor, 148.6 bpm). В плейбеке: `pb-other` (`backing_vocals` + `strings` со скрипичной темой), альтернативная дорожка `pb-other-keys` (включает `keys`), `pb-drums` (барабаны для репетиций), бас живой (`pb-bass: null`, Roma).

## Сводка

- **bpm:** 148.6 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 148.6`) с использованием RubberBand (timemap, engine R2). Ранее наивный линейный ресемпл (`np.interp`) вызывал varispeed-колебания высоты тона скрипки до ±60 центов из-за плавающего живого темпа записи 1999 года; после исправления RubberBand сохраняет оригинальную высоту нот без фальши.
- **pitch_semitones:** 0 (D minor).
- **pb-other:** `backing_vocals` (хор, подпевки) + `strings` (скрипка).
- **pb-other-keys:** `backing_vocals` + `strings` + `keys`.
- **pb-drums:** `drums` (установка для репетиций без барабанщика).
- **pb-bass:** null (живой бас, Roma).
- **players:** alex: `guitars`, roma: `bass`, steve: `drums`, tanya: `vocals`.
- **mix.json:** `music/songs/Король и Шут - Кукла колдуна/mix.json`
- **Рендер:** OFF +3.058 с, lead +1 такт под стартовую фразу, длина 205.1 с (127 тактов).

## Cue

3 cue:
1. `bar 1.1` (3.230 с) — `"Кукла колдуна strings in"` → «Кукла колдуна» + «strings in ready go», на 1.1 вступают акустическая гитара и скрипка (`strings`).
2. `bar 8.1` (14.536 с) — `"drums in"` → «drums in ready go», на 8.1 вступают барабаны и полный бэнд.
3. `bar 17.1` (29.071 с) — `"verse in"` → «verse in ready go», на 17.1 вступает куплет («Крик подобен грому...»).

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`, `all.wav`
- `pb-other.wav`, `pb-other-keys.wav`, `pb-drums.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`, `pb-other-keys.mp3`
- `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`
