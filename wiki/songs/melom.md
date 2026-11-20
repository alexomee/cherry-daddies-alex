---
type: song
updated: 2026-11-20
title: Мелом
artist: Пропаганда
set: на бис #1; 12.12 new songs #9; 12.12 all
---

# Мелом (Пропаганда)

## Сводка

- **bpm:** 120
- **pitch_semitones:** 0 — тональность Bb minor (из имён Moises-стемов), питч не нужен.
- **Позиция:** блок «на бис» #1; с 2026-11-20 также в сете «12.12 new songs» (#9, плейлист Stage Traxx `CD · 12.12 new songs`) и в «12.12 all» (`web/songs.json`).
- Особых полей в `mix.json` нет: **`cue_step`, `count_in`, `tempo_zone` отсутствуют**; поля `click` тоже нет (по умолчанию рендер строит клик из сетки).
- `mix.json`: `/Users/alex/projects/cherry-daddies/music/songs/Мелом/mix.json`

## Плейбек и рендер

- **Плейбек = click + cues + pb-bass** (`pb-other: null`; `pb-bass` = Moises `bass`, см. ниже). До 2026-11-17 плейбека не было вовсе (живой квартет, рантайм в MainStage = только click + cues, [mainstage-rig](../pipelines/mainstage-rig.md)).
- **Играем с кликом** (Alex, 2026-11-17; на концерте 28.10 играли без метронома — поэтому концертный бас не рассматривался). pb-bass из стема остаётся.
- **С 2026-11-17 pb-bass** (Рома ушёл, бас везде в плейбеке — Alex): Moises `bass`. **С 2026-11-20: `gain_db +4.7` + `"peak": "limit"` → −19.2 LUFS** (медиана баса; лимитер −0.4 dBFS задел 169 сэмплов, остаток против прежнего −41 дБ). До этого `gain_db +3.1` → −20.8 LUFS. До медианы −19.2 не дотянуть: бас тихий с высокими пиками, +4.7 дБ упёрлись бы в нормализацию (пик −0.5 при +3.1). Остаток против стема −76 дБ; all/click прежние, cues.wav прежний. В Stage Traxx: Click, Cues, PB Bass. Есть запись живого баса с концерта 28.10 (`~/Downloads/Set 2/13 Мелом/07 Bass Guitar.wav`) — не сравнивалась.
- **layers нет.**
- **Стемы (Moises)** в `/Users/alex/projects/cherry-daddies/music/songs/Мелом/`: `bass`, `drums`, `guitars`, `keys`, `other`, `vocals`, `backing_vocals`, `metronome`. Оригиналы Moises (`Bb minor / 120bpm / 442hz`, id `OaXj5OMqYtE`) в `moises-orig/`. См. [moises-import](../pipelines/moises-import.md).
- **players:** `alex → guitars`, `steve → drums`, `tanya → vocals` (roma убран 2026-11-17).
- **practice-миксы** в `auto-render/`: `practice-alex.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (`practice-roma.mp3` убран 2026-11-17) (каждый = микс без своих стемов + клик + cue).
- **Рендеры** в `/Users/alex/projects/cherry-daddies/music/songs/Мелом/auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `timeline.json` (с 2026-11-20 offset 2.689 с, такт 1.1 = 2.714 с — короткое вступление без добивки до целых тактов; раньше 3.97 с; bar = 2.0 с, 120 bpm). См. [jamzone-render](../pipelines/jamzone-render.md).

## Cue

- **12 cue** (`ready: true` в `web/songs.json`). Устройство cue — [cue-system](../pipelines/cue-system.md).
- Список: bar 1 «Мелом guitar in» (старт), bar 5 «voice in», bar 21 «chorus in», bar 29 «drums stop», bar 41 «bass-only in», bar 45 «all in», bar 53 «drums stop», bar 61 «drums in», bar 69 «drums stop», bar 73 «drums-n-voice in», bar 81 «keep going», bar 89 «guitar only ready go».
- Много drum stop/in — структура с чередованием «барабаны стоп / вступают».
- **Два `raw: true` cue** (произносятся дословно, без разворота по правилам): bar 81 «keep going» и bar 89 «guitar only ready go».
- **Вокал (замер 2026-11-20).** Moises разложил голос по двум стемам (`vocals` + `backing_vocals`: припев «Фиолетовая пудра» и половина куплета 1 лежат в бэках), паузы мерить по сумме. Вступления: такт 5 (доля 1&, после 4 тактов интро) и такт 73 (припев 3, доля 1&, после паузы 70–72); короткая пауза в такте 44 — вход на 45 под «all in». Остальное поётся подряд (куплет 1 5–20, припев 21–28, куплет 2 29–40, припев 2 45–52, куплет 3 53–69, припевы 73–88).
- Счётных входов (`count: true`) нет; `cue_step` не задан.

## Тексты на сцене

- **static-клип** (весь текст на экране, не караоке) — единственная static-песня в риге. Клип set 23, исходник `lyrics-manual/23.txt`; генерится `make_static_clip.py`. См. [lyric-launcher](../pipelines/lyric-launcher.md).

## История и гочи

- **2026-06-20** — песня добавлена как реальная песня сета 23 (коммит «Мелом (Пропаганда): finish encore song + t.A.T.u. cleanup»): 10 cue, pitch 0 (Bb minor), players на 4 живых участника, плейбек = click+cues, static lyric-клип 23. В том же коммите: сгенерён review-видео `auto-render/23-lyric-review.mp4`.
- **2026-06-20** — все 24 сета разведены в `2000.concert` (`wire_concert.py`), включая Мелом (set 23).

- **2026-11-20** — добавлена в сет «12.12 new songs» (Alex). pb-bass проверен: `auto-render/pb-bass.wav` 188 с, −20.8 LUFS, пик −0.5; в Stage Traxx трек PB Bass на шине 4, 10 регионов.

- **2026-11-20** — pb-bass поднят до −19.2 LUFS (`gain_db 4.7`, `peak: limit`); cue «voice in» на такте 5 и «drums-n-voice in» на 73 вместо «drums in» (Alex: подсказки для голоса в начале и после перерывов). Рендер новой версией скрипта: OFF 3.975 → 2.689 с. Stage Traxx `--apply`, 11 регионов.

- **2026-11-20** — Alex: бас и подсказки «всё норм»; POD Go на всю песню **01A** (`"podgo": "01A"`, было 32D), GM-800 MUTE. В Stage Traxx тег `PC0@3`.

- **2026-11-20** — cue «chorus in» на такте 21 (рендер 0:42.7, припев 1 «Фиолетовая пудра»; Alex: «around 0:43»). click/all/pb-bass побайтно прежние. Stage Traxx `--apply`, 12 регионов.

## Открытое

- Нет открытых TODO в источниках на 2026-07-10.
