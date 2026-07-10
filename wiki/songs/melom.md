---
type: song
updated: 2026-07-10
title: Мелом
artist: Пропаганда
set: на бис #1
---

# Мелом (Пропаганда)

## Сводка

- **bpm:** 120
- **pitch_semitones:** 0 — тональность Bb minor (из имён Moises-стемов), питч не нужен.
- **Позиция:** единственная песня блока «на бис» (`web/songs.json`).
- Особых полей в `mix.json` нет: **`cue_step`, `count_in`, `tempo_zone` отсутствуют**; поля `click` тоже нет (по умолчанию рендер строит клик из сетки).
- `mix.json`: `/Users/alex/projects/cherry-daddies/music/songs/Мелом/mix.json`

## Плейбек и рендер

- **Живой квартет — плейбека нет.** `pb-other: null`, `pb-bass: null`: в плейбек/превью не идёт ни один аккомпанирующий стем. Рантайм в MainStage = **только click + cues** (см. [mainstage-rig](../pipelines/mainstage-rig.md)).
- **layers нет.**
- **Стемы (Moises)** в `/Users/alex/projects/cherry-daddies/music/songs/Мелом/`: `bass`, `drums`, `guitars`, `keys`, `other`, `vocals`, `backing_vocals`, `metronome`. Оригиналы Moises (`Bb minor / 120bpm / 442hz`, id `OaXj5OMqYtE`) в `moises-orig/`. См. [moises-import](../pipelines/moises-import.md).
- **players:** `alex → guitars`, `roma → bass`, `steve → drums`, `tanya → vocals`.
- **practice-миксы** в `auto-render/`: `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (каждый = микс без своих стемов + клик + cue).
- **Рендеры** в `/Users/alex/projects/cherry-daddies/music/songs/Мелом/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `timeline.json` (offset 3.97 с, bar = 2.0 с, 120 bpm). См. [jamzone-render](../pipelines/jamzone-render.md).

## Cue

- **10 cue** (`ready: true` в `web/songs.json`). Устройство cue — [cue-system](../pipelines/cue-system.md).
- Список: bar 1 «Мелом guitar in» (старт), bar 29 «drums stop», bar 41 «bass-only in», bar 45 «all in», bar 53 «drums stop», bar 61 «drums in», bar 69 «drums stop», bar 73 «drums in», bar 81 «keep going», bar 89 «guitar only ready go».
- Много drum stop/in — структура с чередованием «барабаны стоп / вступают».
- **Два `raw: true` cue** (произносятся дословно, без разворота по правилам): bar 81 «keep going» и bar 89 «guitar only ready go».
- Счётных входов (`count: true`) нет; `cue_step` не задан.

## Тексты на сцене

- **static-клип** (весь текст на экране, не караоке) — единственная static-песня в риге. Клип set 23, исходник `lyrics-manual/23.txt`; генерится `make_static_clip.py`. См. [lyric-launcher](../pipelines/lyric-launcher.md).

## История и гочи

- **2026-06-20** — песня добавлена как реальная песня сета 23 (коммит «Мелом (Пропаганда): finish encore song + t.A.T.u. cleanup»): 10 cue, pitch 0 (Bb minor), players на 4 живых участника, плейбек = click+cues, static lyric-клип 23. В том же коммите: сгенерён review-видео `auto-render/23-lyric-review.mp4`.
- **2026-06-20** — все 24 сета разведены в `2000.concert` (`wire_concert.py`), включая Мелом (set 23).

## Открытое

- Нет открытых TODO в источниках на 2026-07-10.
