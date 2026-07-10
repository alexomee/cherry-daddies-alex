---
type: song
updated: 2026-07-10
title: I Love It
artist: Icona Pop & Charli XCX
set: СЕТ 2 #11
---

# I Love It — Icona Pop & Charli XCX

Позиция: **СЕТ 2 #11** (последняя в сете; сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`, `sid: "Icona Pop & Charli XCX - I Love It"`).

Папка: `/Users/alex/projects/cherry-daddies/music/songs/Icona Pop & Charli XCX - I Love It/`

## Сводка

- Источник — **JamZone** (не Moises): есть `01_Click.m4a` метроном + именованные стемы `02..12`. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm 126.0** — в `mix.json` НЕ задан; берётся из `fit_grid` по `01_Click.m4a`, зафиксирован в `auto-render/timeline.json` (`bpm: 126.0`, `bar_sec: 1.904762`, `offset_sec: -0.28443`).
- **pitch_semitones НЕ задан** (0) — JamZone-стемы уже в тональности группы, питч не применяется.
- Спецполей нет: `cue_step`, `count_in`, `tempo_zone`, `click`, `layers` — **отсутствуют**.
- Структура (`structure.txt`): Precount / Intro / Verse / Chorus / Verse2 / Chorus2 / Bridge / Chorus3 / Verse3 / Chorus4 / Bridge2 / Chorus5.

## Плейбек и рендер

Группы в `mix.json`:
- **pb-other**: `11_Backing_Vocals`, `03_Noise_effects`
- **pb-bass**: `04_Synth_Bass`

Стемы вне плейбека (живые партии, см. players ниже) — драм-кит, вокал, синты, гитар-синты.

`layers` нет. `replaces` нет.

Рендеры в `auto-render/` (все от 2026-06-20 14:18): `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3`, `timeline.json`.

**players** (кто играет живьём):
- `steve` → `02_Electronic_Drum_Kit`
- `tanya` → `12_Lead_Vocal`
- `alex` → `05_Synthesizer`, `08_Synth_Lead`, `09_Guitar_Synth_1`, `10_Guitar_Synth_2` (2 синта + 2 гитар-синта — коммит 2026-06-19)
- `roma` → `06_Synth_Pad`, `07_Synth_Strings`

practice-миксы (2026-06-20): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).

## Cue

**13 cues** (`mix.json`), заданы `bar`/`beat` + `abs_sec`. Спецполей нет (без `count`, `step`). См. [../pipelines/cue-system.md](../pipelines/cue-system.md).

- Стартовый: bar 3 «I Love It synth in».
- Секционные in: voice in (7), main in (15, 39, 71), verse in (19, 47), bridge in (30.3, 62.3), chorus in (54.3).
- Стопы: bar 14 «all stop», bar 83 «end stop» (оба разворачиваются в «… stop in 3» + 3-2-1).
- bar 69 «keep going».
- Часть входов на **beat 3** (bridge 30.3 / 62.3, chorus 54.3).

## История и гочи

- **2026-06-13** — cue оцифрованы из старого cue-трека: коммит «Cues: оцифровка 4 старых cue-треков + черновики 6 новых» указывает «I Love It (13)» — 13 cue восстановлены. Тогда же введена семантика `bar 1.1 = муз. даунбит` и cue-сетка от `OFF+db0`. Легаси-артефакты песни: `cue_track.wav`, `cues.json` (старый формат `{t,bar,name,src,id}`) — сохранены в папке, но рендер идёт от `mix.json`.
- **2026-06-18** — песня заведена/обновлена в общем коммите «songs: new renders + mix.json updates + new songs + layers».
- **2026-06-19** — финальное распределение players по СЕТ 2: «Icona (2 synths + 2 guitar-synths)» — партии alex.
- **2026-06-20** — последний рендер (все `auto-render/*` от этой даты).
- Артефакты lyric-launcher: `22_lyrics_review.tsv`/`.txt` и `auto-render/22-lyric-review.mp4` (клип №22 в риге). См. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md).

## Открытое

- В памяти агента и `CLAUDE.md` отдельных прецедентов по этой песне НЕТ — гочей, специфичных для неё, не зафиксировано.
- Префикс `22_` в именах lyric-review файлов (номер клипа в риге) не совпадает с позицией сета (#11) — ожидаемо (нумерация клипов сквозная по всем сетам), но стоит держать в уме при деплое клипов.
