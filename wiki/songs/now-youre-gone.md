---
type: song
updated: 2026-07-10
title: Now You're Gone
artist: Basshunter
set: СЕТ 2 #5
---

# Basshunter — Now You're Gone

## Сводка

- **Источник:** JamZone (стемы `NN_Name.m4a`, есть `01_Click.m4a`) — не Moises.
- **bpm:** ~149.02 (из `01_Click.m4a` через `fit_grid`; см. `auto-render/timeline.json`: `bpm 149.0199`, `bar_sec 1.610523`, `offset_sec 1.313572`).
- **pitch_semitones:** нет в `mix.json` → 0 (родная тональность, не транспонируется).
- **Особых полей mix.json нет:** `cue_step`/`count_in`/`tempo_zone`/`click`/`layers` не заданы. `pb-bass: null`.
- Файл: `music/songs/Basshunter - Now You're Gone/mix.json`. Структура секций: `music/songs/Basshunter - Now You're Gone/structure.txt`.

## Плейбек и рендер

Стемы (JamZone `.m4a`): `01_Click`, `02_Electronic_Drum_Kit`, `03_Synth_Bass_1`, `04_Synth_Bass_2`, `05_Synthesizer`, `06_Synth_Voice`, `07_Synth_Lead`, `08_Noise_effects`, `09_Backing_Vocals`, `10_Lead_Vocal`.

- **pb-other:** `["08_Noise_effects"]` (задано 2026-06-13). **pb-bass:** `null` (басовый минус в плейбек не идёт — бас живой).
- **layers:** нет.
- **players** (кто играет живьём):
  - `steve` → `02_Electronic_Drum_Kit`
  - `tanya` → `10_Lead_Vocal`
  - `alex` → `07_Synth_Lead`
  - `roma` → `05_Synthesizer`, `06_Synth_Voice`
- **practice-миксы** отрендерены на всех четверых: `auto-render/practice-{alex,roma,steve,tanya}.mp3`.
- Рендеры: `auto-render/{all,click,cues,pb-other}.wav`, `auto-render/cue_preview.mp3`, `auto-render/timeline.json`. Также `auto-render/16-lyric-review.mp4` (lyric-клип-ревью).

См. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md), [pipelines/mainstage-rig.md](../pipelines/mainstage-rig.md).

## Cue

13 cue (`mix.json` → `cues`), с абсолютными секундами (`abs_sec`). Спецполей нет (`cue_step`/`count_in`/`count` не используются). Все — обычные `in`/`stop` по правилам cue-системы:

- bar 2.3 `Now you're gone vocal in` (стартовый, `chord: C#4`) · bar 12 `drums in` · bar 20 `stop and solo in` · bar 29 `drum stop` · bar 42 `break in` · bar 46 `stop` · bar 48 `solo start in` · bar 56 `stop` · bar 57.3 `vocal in` · bar 66 `bass in` · bar 74.3 `vocal-with-solo in` · bar 83 `keep going` · bar 90 `end stop`.

Дефисные `vocal-with-solo` — одно слово. См. [pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-11:** cue Basshunter (+ Cascada/WFL/Infinity) вручную в Logic; автоген cue удалён.
- **2026-06-13:** `pb-other = 08_Noise_effects`.
- **2026-06-18/19:** новые рендеры (timeline) + players (SET 2 финализирован: alex=synth lead в этой песне).
- **Гоча оцифровки cue (CLAUDE.md, раздел «Оцифровка старых cue»):** NYG — один из двух проверенных прецедентов (второй — Infinity 2008). Ключевой урок: **бонс cue-трека начался на 1 долю РАНЬШЕ такта 1** — смещение таймлайна mp3↔сетка НЕ предполагать, а мерить по жёсткому стем-якорю (онсет барабанов/баса на барлайне). Кажущаяся «другая конвенция отсчёта» = на самом деле смещение.

## Открытое

- Нет открытых TODO в mix.json/памяти. `pb-bass: null` — осознанно (бас живой), не пробел.
