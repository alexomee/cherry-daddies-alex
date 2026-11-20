---
type: song
updated: 2026-11-20
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
- **Особые поля:** `pb-other: {"layers": [{"file": "malo-guitars", "frame": "render", "gain_db": -7.0}, {"file": "malo-sfx", "frame": "render", "gain_db": -4.0}], "roles": {"malo-guitars": "musical", "malo-sfx": "musical"}}`. `pb-bass` содержит только `layers` (стемов нет). Нет `cue_step`, `count_in`, `tempo_zone`, `click` (константная сетка).

## Плейбек и рендер

Файл: `/Users/alex/projects/cherry-daddies/music/songs/SEREBRO - Malo tebya/mix.json`.

- **Стемы Moises** (`music/songs/SEREBRO - Malo tebya/`): `bass.mp3`, `drums.mp3`, `guitars.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3`.
- **Layers (pb-other):**
  - `parts/malo-guitars.wav` (`file: malo-guitars`), **frame `render`**, `gain_db: -7.0`. Ритм-гитара от Alex на припевах и соло (такты 21–45, 61–85, 95–119). Уровень согласован с ритм-гитарой в «Ту-лу-ле» (пик −7.1 dBFS, gated RMS −19.8 dBFS).
  - `parts/malo-sfx.wav` (`file: malo-sfx`), **frame `render`**, `gain_db: -4.0`. Шумовые свипы/эффекты на структурных переходах (такты 20–22, 45–47, 60–62, 85–87) с RMS −30.1 dBFS (аналогично «Солнцу»); кульминационный разгон/сбивка со снейром на тактах 91–96 звучит громче (RMS −20.1 dBFS, пик −4.1 dBFS).
- **Layer (pb-bass):** `parts/malo-bass.aif` (`file: malo-bass`), **frame `stem`** (записан под сырые Moises-стемы → кладётся на OFF), `replaces: ["bass"]` (живой бас вместо студийного — студийный `bass` выкидывается из `all`/превью), `gain_db: -5`. Хрома −2 = уже в ключе группы → **без питча**. Прецедент задокументирован в `CLAUDE.md` (раздел layers). См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **players:** `alex → guitars`, `roma → ["other","keys"]`, `steve → drums`, `tanya → vocals`.
- **Practice-миксы** (`auto-render/`): `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3` (каждый = весь микс минус стемы игрока + клик + cue). См. [jamzone-render.md](../pipelines/jamzone-render.md).
- **Рендеры** (`auto-render/`): `all.wav`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-other.mp3`, `pb-bass.wav`, `pb-bass.mp3`, `cue_preview.mp3`, `timeline.json` (обновлено 2026-10-28). Также lyric-launcher видео `14-TIMED-prototype.mp4`, `14-lyric-review.mp4`.

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

## Концертный слой Ромы (2026-11-17)

- **pb-other** ← `parts/roma-keys-2810.wav` (render-frame): клавиши Ромы (`08`, Set 2 №6), заменяют Moises `keys`+`other`, `gain_db +4.9` (громкость стемов); сдвиг +12.1 мс. Пики слоя прижаты лимитером до −8.5 dBFS в файле (388 мс за песню), чтобы pb-other не уходил в нормализацию и malo-guitars/malo-sfx остались на своих уровнях. В тактах 5–12 Рома не играл.
- Источник: мультитрек 28.10, разбор и A/B — [мультитрек 28.10](../gigs/2026-10-28-multitrack.md). Пересборка: `python3 tools/concert-2810/make_layer.py "<take>" roma-keys-2810` (wav не в git). В Stage Traxx 2026-11-17.

## Клавиши нотами для GM-800 (2026-11-20, подготовка без прибора)

Запрос Alex: снять партию клавиш; запись Ромы — ориентир по яркости и типу звука, стемы — ориентир, MIDI Nepke «вроде похож», сцена 11 MALO TEBYA CH «требует серьёзных доработок»; «не понимаю, как запись так круто звучит, обволакивающе в припевах». Гайд: [снятие партий](../pipelines/part-transcription-guide.md). Скрипт: `tools/jamzone/prep_malo_tebya.py notes | plan | preview`.

**Тональность:** запись D minor, группа C minor (−2). На этой странице и в `parts/README.md` раньше стояло C#/D# minor — ошибка.

**Что в записи (стемы `keys` + `other`):** один широкий суперсо-пэд через всю песню, 13–118, с обрывом в 94.

| Что | Цифры |
|---|---|
| Аккорды припева | Cm (G3 C4 D#4 G4 C5) · Ebmaj9 (A#3 D4 F4 G4 A#4 D5 на D#2) · Abmaj7 (G#3 C4 D#4 G4 C5) · Fm add9 (F3 G#3 C4 F4 G4 C5). G4 и C5 звучат все четыре такта |
| Сайдчейн | −7 дБ на 145 мс от каждой бочки, к «и» (230 мс) обратно; выше 2 кГц провал 10–18 дБ, в низу 10–11. Начинает падать за ~30 мс до бочки |
| Стерео | L и R не коррелированы (−0.1…+0.1, side ≥ mid), низ 40–120 Гц в противофазе (−0.5). У Ромы +0.6 |
| Фильтр по секциям | центр спектра: куплет 230 Гц, припев 1050, куплет 2 — 560, бридж 240 (и узкий), третье соло 1660 |
| Яркость против Ромы | в припеве у записи 4–8 кГц −13 дБ от суммы, 8–16 кГц −18; у Ромы −32 и −38 |
| Реверб | умеренный: после стопа 119 −25 дБ за четверть; стоп 94 — обрыв |

**Ноты против MIDI.** В MIDI трезвучия октавой выше на тактовой черте (Cm Eb Ab Fm; куплет Cm Eb Ab G · Cm Eb Fm G), аккорды и бас на «и» — так его автор записал сайдчейн, отдельного стаба в записи нет. Хрома по секциям против оригинала: мои ноты 0.90–0.97, MIDI 0.72–0.90; по высоте с учётом октав 0.58–0.89 против 0.15–0.62.

**Лид соло 37–44, 77–84** (pyin по шестнадцатым, двухтактная фраза): · · · C5(3&) D5(4) D#5(4&) | G5(1&) F5(2&) D#5(3&) D5(4); каждый второй раз G5 C5 F5 C5 D#5 C5 D#5 восьмыми с 1&. В MIDI другая мелодия. Alex играет соло вживую (сцена 12), в слой лид не пишется. В третьем «соло» 95–102 лида в записи нет: это открытый пэд с октавой сверху. Самое слабое место разбора (0.58): C5 на долях задавлены сайдчейном, читаются не везде.

**Не ноты:** удары стема `other` в соло (слайд C4 → D#4 с верхом на A5, доли 2–3 нечётных тактов 37 39 41 43; кластер в конце 38) и райзер 91–93. Из стемов не вырезаны: переходы закрывает `malo-sfx` Alex.

**Файлы:** `parts/synths.notes.json` (6 голосов, 13 дублей к записи, `duck` 7.5 дБ), `parts/malo-nepke.mid`, страница `analysis/gm800-match/SEREBRO - Malo tebya/preview-part/index.html` (оригинал / мои ноты / MIDI / Рома; простой синт, моно).

**Сцены Alex (по бэкапу лайвсета 17.11, прибор не читался):** 11 MALO TEBYA CH — включена одна партия 2: 281 Angels Saw Pad, level 74, cutoff −10, хорус и реверб включены; партии 1 (580 Reso Guitar w), 3 (44 Harpsichord 1), 4 (994 Stacc Heaven w) выключены. 12 MALO TEBYA SOLO — 205 Simple Soft Lead + 228 Sync Lead 1 + 197 Edge Boost Sweep + 226 Sync Saw Lead.

**Кандидаты тона** (перебор не делался, прибор занят): пэд припева — 1021 S-Saw Pad, 1022 S-Saw Pad w, 1018 Super Saws, 1024/1025 Trance Saws, 314/315/322 Super Saw Poly, 316 Trance Syn Poly, 317 Super Saw Key, 281, 284, 1020, 974, 1017, 913; тёмный пэд куплета — 259 JP Soft Strings, 270 JP-6 Pad, 276, 998, 1000, 1007, 1031. Команды: `prep_malo_tebya.py plan`.

**Что мешает «как в записи» на сцене:** `pb-other` в Stage Traxx — моно-шина. Ширина там пропадает, а противофазный низ пэда при сведении в моно гасится. Плотность надо брать расстройкой и хорусом самого тона, качание — `duck`, открытие фильтра — отдельными дублями по секциям.

**Попутно:** `abs_sec` у cue этой песни в `mix.json` устарели на +0.836 с (cue записаны в несколько строк, рендер такие строки не обновляет). Инструменты нот из-за этого читали стемы со сдвигом почти на две доли; `tools/gm800_match.py` теперь берёт `downbeat_sec` из `timeline.json` и предупреждает. Сами `abs_sec` не исправлены.

**Не сделано:** ничего не сыграно на GM-800, тоны и уровни условные; `mix.json`, рендер и Stage Traxx не трогались; Alex страницу не слушал.
