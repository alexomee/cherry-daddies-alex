---
type: song
updated: 2026-09-03
title: Медведица
artist: Мумий Тролль
set: tryout batch 2026-09
---

# Медведица (Мумий Тролль)

Tryout 2026-09. **Только click + cues** — плейбека нет, банда играет живьём под клик; в ухо только название + отсчёт на старт. См. [youtube-click-only](../pipelines/youtube-click-only.md).

## Сводка

- **bpm:** 130.0 (lstsq по beat-треку librosa, ±6 мс по всей песне (константа))
- **pitch_semitones:** 0 · `pb-other: null`, `pb-bass: null`, `players` нет.
- Источник: YouTube `3uDFkM8FH_E` → `music/youtube/`, копия `original.mp3` в папке песни (идёт только в `all`/`cue_preview`). `metronome.wav` синтетический: клики от первой сильной доли оригинала (4.303 с) на константной сетке.
- Сильная доля: хрома-флакс mod 4 по сетке, пик на индексе 0 от первого клика.
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Мумий Тролль - Медведица/mix.json`
- Рендер: OFF −0.608 с (обрезано 0.6 с ведущей тишины ролика), такт 1.1 = 3.692 с; lead +1 такт под стартовый cue (2 такта каунт-ина).

## Cue

1 cue: `bar 1`, `count: true` → «Медведица in 3» + 3 2 1. Событие (вход) на такте 1.1 = первая сильная доля оригинала.

## Риг (MainStage)

`/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Медведица/` — `click.wav` + `cues.wav` (риг-коммит `eb9b74f6`, запушен). Сет в MainStage **не заведён** — новые песни wire'ятся руками (Playback-плагин на два wav). MAP в `sync_to_mainstage.sh` добавлен.
