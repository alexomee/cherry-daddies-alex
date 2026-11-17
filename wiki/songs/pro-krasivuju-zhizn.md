---
type: song
updated: 2026-11-17
title: Про красивую жизнь
artist: Банд'Эрос
set: "СЕТ 2 #2"
---

# Про красивую жизнь (Банд'Эрос)

Внешняя (Moises) песня. Позиция: **СЕТ 2, #2** (`web/songs.json`, sid `Band'Eros - Pro krasivuju zhizn'`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Band'Eros - Pro krasivuju zhizn'/`.

## Сводка

- **bpm:** 125 (число из имени Moises-файла).
- **pitch_semitones:** не задан → **0**, оригинальная тональность (минус не питчится).
- Особых полей mix.json нет: `cue_step`, `count_in`, `tempo_zone`, `click` — отсутствуют (константная сетка, без ретемпо/каунт-ина).
- **pb-bass** (2026-11-17, Рома ушёл, бас везде в плейбеке — Alex): стем `bass`, `gain_db −2.9` → −19.2 LUFS (без правки −16.3), остаток −73 дБ. До этого `null`: бас играл Рома.

## Плейбек и рендер

Стемы (Moises, переименованы): `bass.mp3`, `drums.mp3`, `guitars.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3`. См. [moises-import](../pipelines/moises-import.md).

- **layers** (`pb-other`): `keys-noise` — записанный синт-шум клавишника.
  - Источник: `/Users/alex/projects/cherry-daddies/music/songs/Band'Eros - Pro krasivuju zhizn'/parts/keys-noise.wav`.
  - **frame: render** (запись слушала мой `auto-render`/`all.wav`) → кладётся 1:1 с индекса 0, lag **+0мс** (измерено, прецедент из `CLAUDE.md`).
  - Уже в тональности группы → без питча. `replaces` не задан (не переписывает студийный стем).
- **pb-other = стемы `keys` + `other` + layer `keys-noise`** (2026-11-17, Alex: клавиши Ромы «в плейбек»). Группа упирается в пик +0.3 dBFS и целиком опускается на −0.7 дБ (нормализация «только вниз»), поэтому keys-noise в pb-other на 0.7 дБ тише прежнего; баланс внутри группы как в `all`. Остаток регрессии на keys/other/keys-noise −79 дБ. Ручной перкуссии в `other` не видно: верх выше 6 кГц на 15–19 дБ тише хэтов барабанов и идёт за ними (протечка Moises, не отдельный шейкер); на слух не проверено. click/all не изменились, cues.wav прежний. В Stage Traxx 2026-11-17 (4 дорожки по 222.72 с, остаток против рендера ≤ −75 дБ).
- **players** (кто играет живьём): `steve` = drums; `tanya` = vocals; `alex` = guitars (`roma` = other, keys убран 2026-11-17: ушёл, партия в плейбеке).
- **practice-миксы:** `auto-render/practice-{alex,steve,tanya}.mp3` (`practice-roma.mp3` убран 2026-11-17) — весь микс без стемов игрока + клик + cue. См. [jamzone-render](../pipelines/jamzone-render.md).
- Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `cue_preview.mp3` (20.06.2026).
- Примечание: `keys`/`other` — слитные Moises-стемы, отдельный синт не выделяется стемом, поэтому вклад клавишника заведён как layer.

## Cue

10 cue (совпадает с `web/songs.json`). См. [cue-system](../pipelines/cue-system.md).

- Стартовый: bar 1.4 «Про красивую жизнь all in» (= муз. даунбит на bar 1.1).
- bar 9.4 `vocal in`; `all stop` на bar 21.2 / 41.2 / 80; `keep going` bar 57 / 106; `rap in` bar 66; `instrumental outro` bar 98; `end stop` bar 113.4.
- Особых режимов нет (`cue_step`/`count_in`/`tempo_zone` не заданы).

## История и гочи

- **2026-06-13** — cue оцифрованы со старого mp3 (Moises 125), 10 cue. В этот же проход введена семантика `bar 1.1 = муз. даунбит`, cue-сетка считается от OFF+db0 (раньше внешние песни с push-тактами клали cue на такт раньше музыки).
- **2026-06-13** — стартовый cue изменён на «all in» вместо «drums in».
- **2026-06-15** — записан layer `parts/keys-noise.wav` (render-фрейм).
- **2026-06-19** — players SET 2: alex играет гитару на этой песне (финальный проход раскладки).
- **2026-06-20** — свежий рендер (timeline).
- `pb-other`: микс уже ниже потолка громкости, правки от attenuate-only ceiling не получает (память `pb-other-loudness-ceiling`).

## Открытое

- **2026-10-03:** чистый guide опубликован в общей библиотеке. Реальное
  выравнивание проверено восстановлением из стемов и кросс-корреляцией в начале,
  середине и конце: 0 мс. Click/cues/pb-other совпадают с ригом побайтно.
  [Измерения и процесс](../pipelines/lyric-guide-library.md).
- Вокалистская проверка текста под этим guide ещё требует просмотра и явного
  подтверждения Тани. Команда агента: `lyric_workflow.py preview 13`.
