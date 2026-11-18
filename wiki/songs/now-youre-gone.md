---
type: song
updated: 2026-11-18
title: Now You're Gone
artist: Basshunter
set: СЕТ 2 #5
---

# Basshunter — Now You're Gone

## Сводка

- **Источник:** JamZone (стемы `NN_Name.m4a`, есть `01_Click.m4a`) — не Moises.
- **bpm:** ~149.02 (из `01_Click.m4a` через `fit_grid`; см. `auto-render/timeline.json`: `bpm 149.0199`, `bar_sec 1.610523`, `offset_sec 1.313572`).
- **pitch_semitones:** нет в `mix.json` → 0 (родная тональность, не транспонируется).
- **Спецполя mix.json:** `podgo: "31D"` (MUTE гитары), `gm800` по тактам (см. ниже). `cue_step`/`count_in`/`tempo_zone`/`click`/`layers` не заданы.
- Файл: `music/songs/Basshunter - Now You're Gone/mix.json`. Структура секций: `music/songs/Basshunter - Now You're Gone/structure.txt`.

## Плейбек и рендер

Стемы (JamZone `.m4a`): `01_Click`, `02_Electronic_Drum_Kit`, `03_Synth_Bass_1`, `04_Synth_Bass_2`, `05_Synthesizer`, `06_Synth_Voice`, `07_Synth_Lead`, `08_Noise_effects`, `09_Backing_Vocals`, `10_Lead_Vocal`.

- **pb-other:** `08_Noise_effects`, `05_Synthesizer`, `06_Synth_Voice`, `04_Synth_Bass_2` (+4.6 дБ). **pb-bass:** только `03_Synth_Bass_1` (−1.4 дБ, −18.7 LUFS, пик −6.7 dBFS).
- `04_Synth_Bass_2` — синт, а не бас (Alex, 2026-11-18): перенесён из pb-bass в pb-other. Сначала с тем же −1.4 дБ, потом +6 дБ → +4.6: на репетиции синт в басу звучал очень тихо, pb-bass поднимали на +6 дБ (Alex). pb-other: пик −3.55 dBFS, RMS −21.9 (было −24.7).
- **GM-800:** 22 U R GONE SOLO (такт 1) → 23 U R GONE BR (58, бридж) → 22 (75). BR = бридж после 2-го соло (заметка «br aft 2nd solo»).
- **layers:** нет.
- **players** (кто играет живьём):
  - `steve` → `02_Electronic_Drum_Kit`
  - `tanya` → `10_Lead_Vocal`
  - `alex` → `07_Synth_Lead`
- Партии Ромы (`05_Synthesizer`, `06_Synth_Voice`) с 2026-11-17 в pb-other, `players.roma` убран.
- **practice-миксы:** `auto-render/practice-{alex,steve,tanya}.mp3`.
- Рендеры: `auto-render/{all,click,cues,pb-other,pb-bass}.wav`, `auto-render/cue_preview.mp3`, `auto-render/timeline.json`. Также `auto-render/16-lyric-review.mp4` (lyric-клип-ревью).

См. [pipelines/jamzone-render.md](../pipelines/jamzone-render.md), [pipelines/stagetraxx-rig.md](../pipelines/stagetraxx-rig.md), [pipelines/gm-800.md](../pipelines/gm-800.md).

## Cue

13 cue (`mix.json` → `cues`), с абсолютными секундами (`abs_sec`). Спецполей нет (`cue_step`/`count_in`/`count` не используются). Все — обычные `in`/`stop` по правилам cue-системы:

- bar 2.3 `Now you're gone vocal in` (стартовый, `chord: C#4`) · bar 12 `drums in` · bar 20 `stop and solo in` · bar 29 `drum stop` · bar 42 `break in` · bar 46 `stop` · bar 48 `solo start in` · bar 56 `stop` · bar 57.3 `vocal in` · bar 66 `bass in` · bar 74.3 `vocal-with-solo in` · bar 83 `keep going` · bar 90 `end stop`.

Дефисные `vocal-with-solo` — одно слово. См. [pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-11:** cue Basshunter (+ Cascada/WFL/Infinity) вручную в Logic; автоген cue удалён.
- **2026-06-13:** `pb-other = 08_Noise_effects`.
- **2026-06-18/19:** новые рендеры (timeline) + players (SET 2 финализирован: alex=synth lead в этой песне).
- **2026-11-17:** синты Ромы и бас (`03`+`04`) в плейбек, POD Go 31D.
- **2026-11-18:** GM-800 сцены 22→23→22; `04_Synth_Bass_2` из pb-bass в pb-other, затем +6 дБ (+4.6). Stage Traxx синкан, дорожки сверены с рендером.
- **Гоча оцифровки cue (CLAUDE.md, раздел «Оцифровка старых cue»):** NYG — один из двух проверенных прецедентов (второй — Infinity 2008). Ключевой урок: **бонс cue-трека начался на 1 долю РАНЬШЕ такта 1** — смещение таймлайна mp3↔сетка НЕ предполагать, а мерить по жёсткому стем-якорю (онсет барабанов/баса на барлайне). Кажущаяся «другая конвенция отсчёта» = на самом деле смещение.

## Открытое

- Если Alex играет партию `05_Synthesizer` в бридже на BR, она задваивается с pb-other. Не подтверждено.
