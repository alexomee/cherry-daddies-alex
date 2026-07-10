---
type: song
updated: 2026-07-10
title: Infinity 2008
artist: Guru Josh Project
set: СЕТ 1 #4
---

# Infinity 2008 — Guru Josh Project

Позиция: **СЕТ 1 «Мировые танцевальные хиты», #4** (`web/songs.json`, `sets[0].songs[3]`; sid `Guru Josh - Infinity 2008`, slug `38db2519ed89`).

## Сводка

- **Источник — JamZone**, не Moises (см. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md)). Стемы — `.m4a` с номерными именами, есть `01_Click.m4a`.
- **bpm 128** (из `music/songs/Guru Josh - Infinity 2008/auto-render/timeline.json`; в `mix.json` поле `bpm` отсутствует — JamZone-темп берётся из клика). `bar_sec 1.875`, `offset_sec -0.295125`.
- **Тональность / `pitch_semitones` — не задан** (JamZone-стемы уже в исходной тональности, питч-пасс не применяется).
- **Особых полей нет:** нет `layers`, `cue_step`, `count_in`, `tempo_zone`, `click`. Только `pb-other`, `pb-bass`, `players`, `cues`.
- Структура (18 секций) — `music/songs/Guru Josh - Infinity 2008/structure.txt`: Precount → Intro → Verse/Chorus ×6 с тремя Instrumental-вставками → Outro.

## Плейбек и рендер

Файл микса: `music/songs/Guru Josh - Infinity 2008/mix.json`.

- **pb-other:** `08_Arpeggiator`, `03_Noise_effects`, `07_Synth_Keys`.
- **pb-bass:** `04_Synth_Bass` с `gain_db -3`.
- Стемы (все `.m4a`): `02_Electronic_Drum_Kit`, `03_Noise_effects`, `04_Synth_Bass`, `05_Synthesizer`, `06_Synth_Pad`, `07_Synth_Keys`, `08_Arpeggiator`, `09_Alto_Saxophone`, `10_Lead_Vocal` + `01_Click`.
- `layers` — нет.

**Рендеры** (`music/songs/Guru Josh - Infinity 2008/auto-render/`, от 2026-06-21): `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json` + `04-lyric-review.mp4` (лирик-клип, см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md)).

**players** (`mix.json`) и practice-миксы (см. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md)):

| Игрок | Партия (стем) | practice-микс |
|---|---|---|
| roma | `05_Synthesizer` | `auto-render/practice-roma.mp3` |
| steve | `02_Electronic_Drum_Kit` | `auto-render/practice-steve.mp3` |
| tanya | `10_Lead_Vocal` | `auto-render/practice-tanya.mp3` |
| alex | `06_Synth_Pad` | `auto-render/practice-alex.mp3` |

## Cue

**16 cue** (совпадает с `web/songs.json` `cues.count: 16`, `ready: true`). См. [../pipelines/cue-system.md](../pipelines/cue-system.md).

- Стартовый: bar 3 «Infinity pad in».
- `sax in` — 4 раза (bar 7.3, 32.3, 57.3, 87.3), все на долю 3 (затакт саксофона).
- `main in` ×4 (bar 23, 38, 43, 78), `drums in` ×2 (bar 13, 63), `keys in` (bar 73), `keep going` (bar 48), `slow part` (bar 53), `main-with-sax in` (bar 93).
- Финал: bar 103 «**end stop**» (→ «end stop in 3» + отсчёт 3-2-1).
- Без счётных полей (`count`), без `cue_step`, без `count_in`.

## История и гочи

- **2026-06-11** — cue для Infinity сделаны **вручную в Logic**, автоген удалён (батч репетиции; борд под список). Первый структурный проход cue.
- **2026-06-11** — прецедент оцифровки старых Logic-cue (`<Song> cues.mp3` → `mix.json`) **проверен на Infinity 2008** (`CLAUDE.md`): смещение mp3↔сетка = 0 (t=0 mp3 = первый клик = такт 1); измерять по жёсткому стем-якорю, не предполагать.
- **2026-06-13** — pb-other зафиксирован = арпеджиатор + fx (`08_Arpeggiator`, `03_Noise_effects`); позже добавлен `07_Synth_Keys`.
- **2026-06-19** — проставлены `players`: **alex → synth pad, synth keys** (по git-сообщению).
- **2026-06-21** — последний полный рендер (все `auto-render/`).
- Память `pb-other-loudness-ceiling`: Infinity — богатый мультиэлементный микс, уже ниже потолка громкости pb-other → фильтр-потолок его не трогает (0 изменений).

## Открытое

- ⚠️ **Расхождение players.** Git-коммит 2026-06-19 гласит «alex → synth pad, **synth keys**», но текущий `mix.json` даёт alex только `06_Synth_Pad`, а `07_Synth_Keys` сидит в `pb-other` (не как живая партия). Уточнить: alex играет и Synth Keys живьём (тогда стем надо убрать из pb-other и добавить в `players`), или коммит-заголовок неточен.
