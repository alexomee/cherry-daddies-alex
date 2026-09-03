---
type: song
updated: 2026-09-03
title: Ту-лу-ла
artist: Чичерина
set: tryout batch 2026-09
---

# Ту-лу-ла (Чичерина)

Tryout 2026-09. **Только click + cues** — плейбека нет, банда играет живьём под клик; в ухо только название + «all in ready go» на старт. См. [youtube-click-only](../pipelines/youtube-click-only.md).

## Сводка

- **bpm:** 130.6 (lstsq по beat-треку librosa, ±5 мс (константа; альбомная версия 2:25, не клип 2:49))
- **pitch_semitones:** 0 · `pb-other: null`, `pb-bass: null`, `players` нет.
- Источник: YouTube `gLe11ZntDCs` → `music/youtube/`, копия `original.mp3` в папке песни (идёт только в `all`/`cue_preview`). `metronome.wav` синтетический: клики от первой сильной доли оригинала (0.468 с) на константной сетке.
- Сильная доля: хрома-флакс mod 4 по сетке, пик на индексе 0 от первого клика.
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/Чичерина - Ту-лу-ла/mix.json`
- Рендер: OFF +3.209 с, такт 1.1 = 3.675 с; lead +1 такт под стартовый cue (2 такта каунт-ина).

## Cue

1 cue: `bar 1`, `"Ту-лу-ла all in"` → «Ту-лу-ла» (естественным темпом в пустом такте 1, выровнено по концу) + «all in ready go» на долях такта 2. Событие (вход) на такте 1.1 = первая сильная доля оригинала.

## Риг (MainStage)

`/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Ту-лу-ла/` — `click.wav` + `cues.wav` (риг-коммиты `eb9b74f6` → `f7b647ec` (cue переделан на стандартный стартовый, 2026-09-03), запушены). Сет в MainStage **не заведён** — новые песни wire'ятся руками (Playback-плагин на два wav). MAP в `sync_to_mainstage.sh` добавлен.
