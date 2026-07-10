---
type: song
updated: 2026-07-10
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
- `pb-bass: null` — своей группы баса в плейбеке нет.

## Плейбек и рендер

Стемы (Moises, переименованы): `bass.mp3`, `drums.mp3`, `guitars.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3`. См. [moises-import](../pipelines/moises-import.md).

- **layers** (`pb-other`): `keys-noise` — записанный синт-шум клавишника.
  - Источник: `/Users/alex/projects/cherry-daddies/music/songs/Band'Eros - Pro krasivuju zhizn'/parts/keys-noise.wav`.
  - **frame: render** (запись слушала мой `auto-render`/`all.wav`) → кладётся 1:1 с индекса 0, lag **+0мс** (измерено, прецедент из `CLAUDE.md`).
  - Уже в тональности группы → без питча. `replaces` не задан (не переписывает студийный стем).
- **players** (кто играет живьём): `roma` = other, keys; `steve` = drums; `tanya` = vocals; `alex` = guitars.
- **practice-миксы:** `auto-render/practice-{alex,roma,steve,tanya}.mp3` — весь микс без стемов игрока + клик + cue. См. [jamzone-render](../pipelines/jamzone-render.md).
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

- Нет открытых TODO по этой песне.
