---
type: song
updated: 2026-09-03
title: Rock & Roll Queen
artist: The Subways
set: tryout batch 2026-09
---

# Rock & Roll Queen (The Subways)

Tryout 2026-09. **Только click + cues** — плейбека нет, банда играет живьём под клик; в ухо только название + «all in ready go» на старт. См. [youtube-click-only](../pipelines/youtube-click-only.md).

## Сводка

- **bpm:** 141.0 — живая запись, локальный темп гуляет 138–145 по 10-с окнам (интро-рифф ~143.6, тело ~140–141, кусок 75–90 с ~136); lstsq по всей песне 141.0. Константный клик к оригиналу в превью плывёт до ±60 мс, для рига неважно.
- **pitch_semitones:** 0 · `pb-other: null`, `pb-bass: null`, `players` нет.
- Источник: YouTube `wAQUsdw01IA` (THE SUBWAYS, «Official Upload», 2:50) → `music/youtube/`, копия `original.mp3` в папке песни (только в `all`/`cue_preview`). `metronome.wav` синтетический от первого удара риффа (0.410 с) на константной сетке.
- Сильная доля: кик/низ и хрома-флакс mod 4 по трекнутым долям — пик на индексе 0 (бэкбит-снейр на 1/3 подтверждает 2-4), первый удар риффа = такт 1.1.
- mix.json: `/Users/alex/projects/cherry-daddies/music/songs/The Subways - Rock & Roll Queen/mix.json`
- Рендер: OFF +2.997 с, такт 1.1 = 3.404 с; lead +1 такт под стартовый cue (2 такта каунт-ина), 102 такта.

## Cue

1 cue: `bar 1`, `"Rock & Roll Queen all in"` → «Rock & Roll Queen» (естественным темпом в такте 1) + «all in ready go» по долям такта 2, вход на 1.1. Английский текст читает EN-голос `say`, «&» = «and».

## Риг (MainStage)

`/Users/alex/projects/cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Rock & Roll Queen/` — `click.wav` + `cues.wav` (риг-коммит `55091574`, запушен). Сет в MainStage **не заведён** — wire руками. MAP в `sync_to_mainstage.sh` добавлен.
