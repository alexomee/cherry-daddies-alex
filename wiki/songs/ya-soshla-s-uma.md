---
type: song
updated: 2026-07-10
title: Я сошла с ума
artist: t.A.T.u.
set: на бис #2
---

# t.A.T.u. — Я сошла с ума

Позиция: **на бис #2** (сверено с `/Users/alex/projects/cherry-daddies/web/songs.json`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)/`.

## Сводка

- **bpm:** 90.0
- **pitch_semitones:** нет (JamZone-стемы уже в ключе группы — не питчатся).
- **Источник:** JamZone (не Moises), `cat_54835`. См. [moises-import.md](../pipelines/moises-import.md) для общего пайплайна стемов.
- Особых полей mix.json нет: `cue_step`, `count_in`, `tempo_zone`, `"click": "follow"` — отсутствуют. Клик берётся из стема `01_Click.m4a`.
- timeline.json (`auto-render/`): `offset_sec` 2.369571, `bar_sec` 2.666667.

## Плейбек и рендер

`mix.json`:
- **pb-other:** `04_Noise_effects`, `05_Noise_effects_(Wind)`, `07_Acoustic_Guitar`, `09_Synth_Pad`, `10_Synth_Voice`, `11_Synth_Lead`, `12_String_Section`, `13_Backing_Vocals`.
- **pb-bass:** `06_Bass`.
- **layers:** нет.
- **players:** `steve` → `02_Drum_Kit`; `tanya` → `15_Lead_Vocal_Lena`, `14_Lead_Vocal_Julia`.

Стемы в папке (`.m4a`, 15 шт): `01_Click`, `02_Drum_Kit`, `03_Percussion`, `04_Noise_effects`, `05_Noise_effects_(Wind)`, `06_Bass`, `07_Acoustic_Guitar`, `08_Distorted_Electric_Guitar`, `09_Synth_Pad`, `10_Synth_Voice`, `11_Synth_Lead`, `12_String_Section`, `13_Backing_Vocals`, `14_Lead_Vocal_Julia`, `15_Lead_Vocal_Lena`.

`auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-bass.wav`, `cue_preview.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`, `timeline.json`, `24-lyric-review.mp4`.

**Practice-миксы:** `practice-steve.mp3` (барабанщик — минус `02_Drum_Kit`), `practice-tanya.mp3` (вокалистка — минус обоих lead-вокалов). См. [jamzone-render.md](../pipelines/jamzone-render.md).

## Cue

12 cue, все секции входят на **долю 3** (полутактовый анакрузис — контрольный признак песни, см. ниже). Список (bar.beat → текст):

- 2 — «Я сошла с ума pad in» (стартовый cue: название + pad in ready go)
- 6.3 — chorus in
- 14.3 — verse in
- 23.3 — chorus in
- 31.3 — **drums stop** (объявление «drums stop in 3» + 3-2-1; драм-брейк перед instrumental)
- 33.3 — **instrumental in** (длинное слово — начинается на долю раньше, занимает 2 доли)
- 41.3 — all stop
- 49.3 — chorus in
- 61.3 — all stop
- 65.3 — drums in
- 69.3 — chorus in
- 77.3 — all stop

Правила разворачивания cue (in / stop / счётный вход) — [cue-system.md](../pipelines/cue-system.md).

## История и гочи

- **2026-06-18** — заведение песни (новые рендеры/timeline, mix.json).
- **2026-06-19** — `jamzone_render` стал выкидывать перкуссию (кроме drum kit) из music/all/pb/preview/practice.
- **2026-06-20** — cleanup t.A.T.u. + финализация Мелом (на бис).
- **2026-06-21** — cue `drums stop` поставлен на долю 31.3 (драм-брейк перед instrumental).

Гочи:
- **Все секции входят на долю 3, не на барлайн** (chorus/verse/instrumental/pre/bridge/end). Per-bar RMS округляет границу к соседнему такту и промахивается в обе стороны (громкий фил впереди → cue на 2 доли рано; тихий переход → на 2 доли поздно). Мерить надо онсеты на уровне доли, а не по тактам. (память: cue-sections-beat-resolution)
- **Перкуссия:** `03_Percussion` присутствует стемом, но НЕ в pb-other/pb-bass — правило «перкуссия вон из плейбека» соблюдено (было прецедент-нарушением до чистки; играет живой барабанщик). См. CLAUDE.md и память percussion-out-of-playback.
- **Lyric-launcher (дуэт-гоча):** тексты на сцену — клип `cat_54835`, два голоса: оранжевый `#F5800A` + зелёный `#02A80B`. Куплеты разведены по цветам, припевы в унисон. Старый одно-цветный `lead_color()` ронял целый куплет → фикс `lead_words()` (мержит цвета с ≥50% слогов, дедупит унисон). Set 24 в риге, заведён 2026-06-20. См. [lyric-launcher.md](../pipelines/lyric-launcher.md).
- **MainStage-риг:** сохранения клавишника молча ревертят Lyrics-страйп (страйп tatu был убит save'ами «bass») — при апдейте риг перепроводить. См. [mainstage-rig.md](../pipelines/mainstage-rig.md).
- Alex в этой песне **сидит без партии** (память practice-mix-players) — practice-микс для него не пишется.

## Открытое

- **`08_Distorted_Electric_Guitar` нигде не задействован** — ни в pb-other/pb-bass, ни в `players`. `07_Acoustic_Guitar` в pb-other, а дисторшн-гитара выпала. Непонятно, намеренно (играет живой гитарист без записи в players) или пропуск в mix.json. Проверить.
