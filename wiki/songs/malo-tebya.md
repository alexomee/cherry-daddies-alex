---
type: song
updated: 2026-07-10
title: Мало тебя
artist: SEREBRO
set: "СЕТ 2 #3"
---

# Мало тебя — SEREBRO

Внешняя песня (Moises-стемы). Сетлист: СЕТ 2, позиция #3 (после «Про красивую жизнь», перед «Я устал») — сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`.

Пайплайн: см. [moises-import.md](../pipelines/moises-import.md), [jamzone-render.md](../pipelines/jamzone-render.md), [cue-system.md](../pipelines/cue-system.md).

## Сводка

- **bpm:** 130.000 (lstsq-среднее реального метронома, ±20мс; медиана 130.40 давала дрейф 685мс — «раз» уезжал).
- **pitch_semitones:** −2 (плейбек транспонируется в тональность группы; rubberband CLI R3 + формант).
- **Особые поля:** `pb-other: null` (нет other-группы в плейбеке). `pb-bass` содержит только `layers` (стемов нет). Нет `cue_step`, `count_in`, `tempo_zone`, `click` (константная сетка).

## Плейбек и рендер

Файл: `/Users/alex/projects/cherry-daddies/music/songs/SEREBRO - Malo tebya/mix.json`.

- **Стемы Moises** (`music/songs/SEREBRO - Malo tebya/`): `bass.mp3`, `drums.mp3`, `guitars.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3`.
- **Layer (pb-bass):** `parts/malo-bass.aif` (`file: malo-bass`), **frame `stem`** (записан под сырые Moises-стемы → кладётся на OFF), `replaces: ["bass"]` (живой бас вместо студийного — студийный `bass` выкидывается из `all`/превью), `gain_db: -3`. Хрома −2 = уже в ключе группы → **без питча**. Прецедент задокументирован в `CLAUDE.md` (раздел layers). См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **players:** `alex → guitars`, `roma → ["other","keys"]`, `steve → drums`, `tanya → vocals`.
- **Practice-миксы** (`auto-render/`): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (каждый = весь микс минус стемы игрока + клик + cue). См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **Рендеры** (`auto-render/`): `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json` (последний рендер 2026-06-25). Также `preview.mp3` (2026-06-12, старый) и lyric-launcher видео `14-TIMED-prototype.mp4`, `14-lyric-review.mp4`.

## Cue

16 cue (стартовый = «Мало тебя guitar in ready go», bar 1.1 = музыкальный даунбит). Полный список в `mix.json`:

- Секционные входы: `voice in` (5), `bass in` (13, 53), `drums in` (17), `solo in` (37, 77, 95), `verse in` (45), `kick in` (47), `bridge in` (85), `snare in` (91), `chorus in` (103).
- **Счётный вход:** `pause in` (bar 60, beat 4, `"count": true`) → «pause in 3» + отсчёт «3 2 1».
- **Стопы:** `all stop` (bar 94, 119) → «all stop in 3» + 3-2-1.
- Позиции с `abs_sec` (кэш render-времён). Семантика `bar 1.1 = муз. даунбит` введена 2026-06-13; SEREBRO перенумерована на −1 такт под неё (render-времена воспроизведены точно: 3.692/3.871).

## История и гочи

- **2026-06-12:** добавлен `pitch_semitones: -2`; bpm зафиксирован как ровно 130.000 (не медиана 130.40 — та дрейфила); первичная разметка 16 cue.
- **2026-06-13:** cue перенумерованы −1 такт под новую семантику `bar 1.1 = муз. даунбит` (общий проход по внешним песням; render-времена сохранены точно).
- **2026-06-15:** записан layer `parts/malo-bass.aif` (frame stem, replaces bass).
- **2026-06-18:** новые рендеры + layers; **2026-06-18:** введены practice-`<player>`.mp3.
- **2026-06-25:** последний ре-рендер (`mix.json` mtime, все `auto-render/*.wav` от 22:26–22:30).
- **Память:** Moises-песни (Pro krasivuju, Я устал, Beverly Hills, Malo) имеют слитые `keys`/`other` — общий синт нельзя выделить стемом, нужен layer (`practice-mix-players.md`). Malo — среди dynamic force-aligned RU лирик-клипов lyric-launcher (`lyric-launcher-stage-monitor.md`); клип №14. См. [lyric-launcher.md](../pipelines/lyric-launcher.md).

## Открытое

- В корне папки лежит `bass-bandkey_synth.wav` (19МБ, 2026-06-15), НЕ упомянут в `mix.json` и НЕ в `parts/` — назначение неясно (возможный старый бас-лейер до `malo-bass.aif`); не участвует в текущем рендере.
- Лирик-клип: `auto-render/14-lyric-review.mp4` помечен «review» — статус вычитки лирики не подтверждён.
