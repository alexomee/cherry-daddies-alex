---
type: song
updated: 2026-07-10
title: Destination Calabria
artist: Alex Gaudino
set: "СЕТ 1 #6"
---

# Destination Calabria — Alex Gaudino

Позиция: СЕТ 1 #6 (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Alex Gaudino - Destination Calabria/`

## Сводка

- Источник — **JamZone** (стемы `01_Click.m4a` … `09_Lead_Vocal.m4a`), не Moises. См. [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md).
- **bpm ≈ 128.23** (из `auto-render/timeline.json`, `bar_sec 1.871657`, `offset_sec -0.300794`). В `mix.json` bpm не задан — берётся из `01_Click.m4a`.
- **pitch_semitones нет** — JamZone-стемы уже в тональности группы, питч не применяется.
- **`"click": "follow"`** — клик/cue-сетка строятся по метроному JamZone (переменный темп, фаза перезахватывается фитом онсетов). tempo_zone/cue_step/count_in — нет.
- Структура (`structure.txt`): Precount, Intro, Instrumental, Verse, Chorus, Instrumental 2, Verse 2, Chorus 2, Instrumental 3, Break, Chorus 3, Chorus 4, Outro.

## Плейбек и рендер

- `pb-other`: `04_Sound_Effects`, `06_Synth_Brass`.
- `pb-bass`: `05_Synth_Bass` (`gain_db -3`).
- Перкуссия `03_Percussion` **не** в миксе (правило: вся перкуссия кроме кита — вон из плейбека, [../pipelines/jamzone-render.md](../pipelines/jamzone-render.md)).
- layers — нет.
- Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3` (2026-06-20).
- **players** (кто играет живьём): `steve`=`02_Electronic_Drum_Kit`, `tanya`=`09_Lead_Vocal`, `alex`=`07_Baritone_Saxophone`, `roma`=`08_Tenor_Saxophone`. Practice-миксы на всех четверых: `practice-steve.mp3`, `practice-tanya.mp3`, `practice-alex.mp3`, `practice-roma.mp3`. См. [../pipelines/mainstage-rig.md](../pipelines/mainstage-rig.md).
- `auto-render/06-lyric-review.mp4` (2026-06-22) — клип для ревью лирики, см. [../pipelines/lyric-launcher.md](../pipelines/lyric-launcher.md).

## Cue

15 cue (`mix.json`). Стартовый: bar 3 «Destination Calabria bass in ready go». Дальше: `all in`, `verse in` (×2), несколько `stop` (bars 27/52/63) и `end stop` (bar 96), `more synths in`, `sax solo in` (bar 65). Хвост песни размечен по **доле 2**: `crash in` (73.2), `vocal in` (74.2), `all in` (75.2), `outro in` (87.2) — см. правило cue на beat-разрешении. cue_step/count_in/счётных входов (`count`) нет. Каждый cue несёт `abs_sec`. Про раскрытие текста cue — [../pipelines/cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-18** — новые рендеры (timeline) + апдейты mix.json (общий проход по песням).
- **2026-06-19** — заведены `players`: alex — баритон-сакс, roma — тенор-сакс (Calabria в проходе по 7 песням).
- **2026-06-20** — последний ре-рендер `auto-render/` (все wav + cue_preview).
- **2026-06-22** — добавлен `06-lyric-review.mp4`.

## Открытое

- Нет.
