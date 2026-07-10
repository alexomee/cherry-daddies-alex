---
type: song
updated: 2026-07-10
title: Beverly Hills
artist: Zivert
set: "СЕТ 2 #7"
---

# Beverly Hills — Zivert

Внешняя песня (стемы + live-bass layer). Сетлист: СЕТ 2, позиция #7 — сверено с `/Users/alex/projects/cherry-daddies/web/songs.json` (`sid: "Beverly Hills"`). Сквозной номер сета для lyric-launcher — **18**.

Пайплайн: см. [moises-import.md](../pipelines/moises-import.md), [jamzone-render.md](../pipelines/jamzone-render.md), [cue-system.md](../pipelines/cue-system.md).

## Сводка

- **bpm:** 115 (`timeline.json`: `bpm 115.0`, `bar_sec 2.086957`, `offset_sec 3.611759`).
- **pitch_semitones:** не задан → **0** (плейбек в родной тональности; стемы помечены `A minor-115bpm-440hz`).
- **Особые поля:** `"click": "follow"` — клик/cue-сетка следует реальному метроному (переменный темп, lstsq-перезахват фазы), **`tempo_zone` НЕ задан**. `pb-other: null` (нет other-группы в плейбеке). `pb-bass` содержит только `layers` (стемов нет). Нет `cue_step`, `count_in`.

## Плейбек и рендер

Файл: `/Users/alex/projects/cherry-daddies/music/songs/Beverly Hills/mix.json`.

- **Стемы** (`music/songs/Beverly Hills/`): `bass.mp3`, `drums.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3` (все 2026-06-15). Оригиналы до варпа — в `moises-orig/` (именование `Beverly Hills-<stem>-A minor-115bpm-440hz.mp3`).
- **Layer (pb-bass):** `parts/zivert-bass.wav` (read-only, 2026-06-20; `file: zivert-bass`), **frame `render`** (кладётся 1:1 с индекса 0), `replaces: ["bass"]` (студийный `bass` выкидывается из `all`/превью, иначе два баса), `gain_db: -7.5`. Layer в ключе группы → без питча. См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **players:** `roma → ["other","keys"]`, `steve → drums`, `tanya → vocals`. **`alex` в `players` НЕ значится** (см. Открытое).
- **Practice-миксы** (`auto-render/`): `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (каждый = весь микс минус стемы игрока + клик + cue). См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **Рендеры** (`auto-render/`, все 2026-06-21): `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `cue_preview.mp3`, `timeline.json`. Также lyric-launcher видео `18-lyric-review.mp4` (2026-06-22).
- **Артефакты JamZone-эры** в корне папки (2026-06-11): `Beverly Hills click.wav`, `Beverly Hills cue_preview.m4a`, `cue_track.wav`, `cues.json` (путь `…/jamzone-stems/…`), `aligned/`. Служебные, в текущем рендере не участвуют.

## Cue

12 cue, позиции как `bar` (beat по умолчанию 1) + кэш `abs_sec` (render-времена). Полный список в `mix.json`:

- Старт: **«Beverly Hills all in ready go»** (bar 1).
- Входы: `vocal in` (5), `all in` (38, 55, 88), `outro in` (96).
- Стопы: `stop` (37, 54), `all stop` (79), `end stop` (104).
- **`ghost beat ready skip`** (bar 13, 46) — нестандартная формулировка (не «in»/«stop»/«count» из правил `CLAUDE.md`), означает пропуск/скип секции; проверить озвучку в `auto-render/cue_preview.mp3`.

## История и гочи

- **2026-06-11:** первичная сборка через JamZone (cue_track/aligned/cues.json).
- **2026-06-15:** стемы (warped) + `moises-orig/` бэкап оригиналов.
- **2026-06-18:** новые рендеры + layers; введены practice-`<player>`.mp3.
- **2026-06-19** (`b826a9b`): коммит «Alex on bass for … Beverly Hills» — бас как живая партия Alex, исключён из его practice-микса. ⚠️ Текущий `mix.json` (2026-06-21) этому противоречит: `alex` отсутствует в `players`, бас = playback-layer `zivert-bass` (`web/songs.json`: `bass.kind = "playback"`). Похоже, решение позже поменяли (бас ушёл в плейбек).
- **2026-06-20:** записан layer `parts/zivert-bass.wav` (frame render, replaces bass, −7.5 dB).
- **2026-06-21:** последний ре-рендер (`mix.json` + все `auto-render/*.wav`).
- **2026-06-22** (`3f7023f`, `91e4796`): вычитка лирики клипа №18 (транскрипция-verified): восстановлена пропущенная пре-чорус секция 2:32–2:48, затем финал переопределён как RU-хук «Его глаза / Её любовь» (3:04–3:22), а не английский чорус; чорусы 1 (1:02) и 2 (2:13) остаются EN.
- **Память:** Beverly Hills — среди dynamic force-aligned RU лирик-клипов lyric-launcher (`lyric-launcher-stage-monitor.md`), клип №18. Синт-стемы `keys`/`other` слитые — общий синт нельзя выделить стемом (`practice-mix-players.md`). См. [lyric-launcher.md](../pipelines/lyric-launcher.md).

## Открытое

- **Кто играет бас — не согласовано в источниках.** `mix.json` держит бас в плейбеке (layer `zivert-bass`, `players` без `alex` → practice-alex не генерится), тогда как коммит 06-19 и agent-память (`practice-mix-players.md`) числят бас живой партией Alex. Уточнить актуальное распределение.
- **Метка источника:** `cues.json` и `moises-orig/` именуют стемы по-JamZone (`A minor-115bpm-440hz`), а память относит Beverly Hills к «4 Moises-песням». Фактически стемы переименованы в Moises-стиль; ярлык неоднозначен.
- **`ghost beat ready skip`** — cue вне стандартных правил разворачивания; корректность озвучки не подтверждена.
