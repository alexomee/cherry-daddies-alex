---
type: song
updated: 2026-09-03
title: Кукла колдуна
artist: Король и Шут
set: tryout batch 2026-09
---

# Кукла колдуна (Король и Шут)

Tryout 2026-09. **Только click + cues** — плейбека нет, банда играет живьём под клик; в ухо только название + отсчёт на старт. См. [youtube-click-only](../pipelines/youtube-click-only.md).

## Сводка

- **bpm:** 148.6 (lstsq по beat-треку librosa, живая запись: ±47 мс (0–60 с +10…−11, 90–120 с −25…−30, 150 с +47) — константный клик к оригиналу в превью плывёт на пол-доли, для рига неважно)
- **pitch_semitones:** 0 · `pb-other: null`, `pb-bass: null`, `players` нет.
- Источник: YouTube `yUp01GbQxTw` → `music/youtube/`, копия `original.mp3` в папке песни (идёт только в `all`/`cue_preview`). `metronome.wav` синтетический: клики от первой сильной доли оригинала (0.286 с) на константной сетке.
- Сильная доля: хрома-флакс mod 4 по сетке, пик на индексе 0 от первого клика.
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Король и Шут - Кукла колдуна/mix.json`
- Рендер: OFF +2.946 с, такт 1.1 = 3.230 с; lead +1 такт под стартовый cue (2 такта каунт-ина).

## Cue

1 cue: `bar 1`, `count: true` → «Кукла колдуна in 3» + 3 2 1. Событие (вход) на такте 1.1 = первая сильная доля оригинала.

## Риг (MainStage)

`/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кукла колдуна/` — `click.wav` + `cues.wav` (риг-коммит `eb9b74f6`, запушен). Сет в MainStage **не заведён** — новые песни wire'ятся руками (Playback-плагин на два wav). MAP в `sync_to_mainstage.sh` добавлен.
