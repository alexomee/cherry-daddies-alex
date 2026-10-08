---
type: song
updated: 2026-10-08
title: Кукла колдуна
artist: Король и Шут
set: tryout batch 2026-09
---

# Кукла колдуна (Король и Шут)

Tryout 2026-09. Moises-стемы (D minor, 148.6 bpm). С 2026-10-01 `pb-other` — пользовательский bounce Alex (бэки, скрипки, гитары); с 2026-10-07 обновлён на более громкую версию v2 (−14.9 LUFS, без трима), т.к. на репетиции −17.9 LUFS оказался слишком тихим. Альтернативная дорожка `pb-other-keys` пока из старых стемов (включает `keys`), `pb-drums` — барабаны для репетиций, бас живой (`pb-bass: null`, Roma).

## Сводка

- **bpm:** 148.6 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 148.6`) с использованием RubberBand (timemap, engine R2). Ранее наивный линейный ресемпл (`np.interp`) вызывал varispeed-колебания высоты тона скрипки до ±60 центов из-за плавающего живого темпа записи 1999 года; после исправления RubberBand сохраняет оригинальную высоту нот без фальши.
- **pitch_semitones:** 0 (D minor).
- **pb-other:** `parts/kukla-pb-other-v2.wav` — полный пользовательский слой (2026-10-07), render-frame; `replaces:["backing_vocals","strings"]`, роль musical, −14.9 LUFS-I / −0.1 dBTP.
- **pb-other-keys:** `backing_vocals` + `strings` + `keys`.
- **pb-drums:** `drums` (установка для репетиций без барабанщика).
- **pb-bass:** null (живой бас, Roma).
- **players:** alex: `guitars`, roma: `bass`, steve: `drums`, tanya: `vocals`.
- **mix.json:** `music/songs/Король и Шут - Кукла колдуна/mix.json`
- **Рендер:** OFF +3.058 с, lead +1 такт под стартовую фразу, длина 205.1 с (127 тактов).

## Cue

4 cue:
1. `bar 1.1` (3.230 с) — `"Кукла колдуна strings in"` → «Кукла колдуна» + «strings in ready go», на 1.1 вступают акустическая гитара и скрипка (`strings`).
2. `bar 8.1` (14.536 с) — `"drums in"` → «drums in ready go», на 8.1 вступают барабаны и полный бэнд.
3. `bar 17.1` (29.071 с) — `"verse in"` → «verse in ready go», на 17.1 вступает куплет («Крик подобен грому...»).
4. `bar 124.1` (201.884 с / 3:21.88) — `"end in"`, `count: true` → объявление «end in 3», отсчёт «3 2 1» (доли 2, 3, 4 такта 123), на 124.1 сильная доля финала / переход в сценический end fill.

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`, `all.wav`
- `pb-other.wav`, `pb-other-keys.wav`, `pb-drums.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`, `pb-other-keys.mp3`
- `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`

## Замена скрипок: MIDI-заготовка (2026-09-29)

Alex хочет записать свои скрипки вместо автовырезанного `strings`. Подтверждён полифонический разбор WAV с двумя редактируемыми MIDI-голосами. Выдача: `music/songs/Король и Шут - Кукла колдуна/transcription/violin-v1/`.

- Основной файл `kukla-violins-2voices.mid`: 148.6 BPM, 4/4, без квантизации/pitch-bend, **render-frame** (сдвиг +3.057926 с уже встроен); импорт от нуля, первая нота ~3.248 с.
- Basic Pitch ONNX + проверка фундаменталов/гармоник, подавление октавных дублей и вибрато-фрагментов: 752 ноты (456/296), 152 помечены для ревью. Разделение голосов автоматическое; это **черновик, не слуховая приёмка**.
- Отдельные MIDI каждого голоса, синтетический аудиогайд, сравнение source-left/MIDI-right, CSV нот и отчёт. Тихую зону/финал и неоднозначные октавы править в Logic.
- Следующий шаг после редактирования/озвучивания — полный WAV с нуля проекта как `parts/violin.wav`, layer `frame:render`, `replaces:["strings"]`. Пока это план замены, не подключённый playback-layer.

## Пользовательский pb-other: аудит громкости (2026-10-01)

Alex сделал полный pb-other (по его описанию: бэк-вокал, скрипки, гитары): `/Users/alex/Documents/kukla_kolduna_pb_other.mp3`, stereo 48 kHz / 320 kbps, 206.784 с. Это полный групповой bounce, не отдельный violin-layer из предыдущего плана.

Сравнение с 26 текущими `*/auto-render/pb-other.wav`: новый файл **−15.4 LUFS-I, −0.1 dBTP**, gated stereo RMS **−18.25 dBFS**, mono **−18.44 dBFS**. Плотные музыкальные референсы: Rock & Roll Queen −17.9 LUFS, Uptown Funk −18.0, Coldplay −18.1, t.A.T.u. −17.6. Прежняя Кукла −18.9 LUFS / −3.1 dBTP / stereo RMS −22.20. FX-only файлы не использованы как целевой уровень.

**Рекомендация — trim −2.5 dB:** измерение через volume+ebur128 без записи файла дало **−17.9 LUFS / −2.6 dBTP**. Активный stereo RMS будет −20.75 dBFS — примерно на 0.7–1.9 dB выше t.A.T.u./Uptown/Subways, то есть соответствует пожеланию «может быть чуть громче». Компрессию ради уровня не предлагали; внутренний баланс стереобонса оценкой громкости не подтверждён. Исходник пока только измерен; коррекция, подключение в mix и sync рига не выполнялись.

Рецепт и полный набор измерений: `analysis/2026-10-01-pb-other-loudness/{measure.py,measurements.json}` в папке песни. LUFS/true peak — ffmpeg EBU R128; gated RMS — 400 мс / hop 100 мс, gate max−20 dB.

По следующей просьбе Alex коррекция выполнена: `/Users/alex/Documents/kukla_kolduna_pb_other_minus2p5dB.wav` — gain −2.5 dB, WAV PCM 24 bit / 48 kHz stereo, 206.784 с. Измерение готового WAV подтвердило **−17.9 LUFS / −2.6 dBTP**. Исходный MP3 сохранён; WAV готов для подключения, mix/риг ещё не обновлены.

### Импорт в проект и риг

2026-10-01 по отдельной просьбе Alex WAV скопирован в `parts/kukla-pb-other-v1.wav`, назначен единственным layer в `mix.json:pb-other`. `auto-render/pb-other.wav` получил идентичный PCM + прежнюю tempo-метку 148.6; прослушка `pb-other.mp3` пересобрана с click/cues. Предыдущий mix и pb-other сохранены в `versions/2026-10-01-before-custom-pb-other/`.

`sync_to_mainstage.sh --apply "Кукла колдуна"`: изменён один `pb-other.wav`; SHA256 factory/риг совпадает (`2f90d49f…33c4536`). Риг-коммит `be489c2a` **запушен в origin/main**. Подробности источника, тайминга и состава будущего all-превью — `parts/README.md`.

## Обновление pb-other после репетиции: v2 без трима (2026-10-07)

На репетиции 2026-10-07 выяснилось, что предыдущая версия с тримом −2.5 dB (−17.9 LUFS) звучит слишком тихо в пачке бэнда. Alex подготовил новый рендер из Logic: `/Users/alex/Downloads/кукла колдуна other.mp3` (48 kHz / 320 kbps stereo, 206.784 с).

Измерения нового файла:
- **−14.9 LUFS-I / −0.1 dBTP** (~+3.0 LUFS громче v1)
- Gated stereo RMS: **−18.22 dBFS**, gated mono RMS: **−19.19 dBFS**
- Loudness Range (LRA): **8.6 LU**
- Тайминг: посемпловое совпадение с v1 (лаг 0 мс, 9 925 632 семплов при 48 kHz).

Файл сконвертирован 1:1 в `parts/kukla-pb-other-v2.wav` (PCM 24 bit / 48 kHz stereo).
В `mix.json` слой обновлён на `kukla-pb-other-v2`. Прежний v1 сохранён в `versions/2026-10-07-before-louder-pb-other/`.
`auto-render/pb-other.wav` получил tempo-метку 148.6 (SHA256: `95220a9f10812855e9a3ff2c672638f8fb60280f1d1d9713761d6416b5c7b7fa`).
Прослушка `auto-render/pb-other.mp3` пересобрана с click/cues.
`sync_to_mainstage.sh --apply "Кукла колдуна"` обновил `pb-other.wav` в риге.
