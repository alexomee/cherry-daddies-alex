---
type: song
updated: 2026-09-29
title: Pretty Fly (For A White Guy)
artist: The Offspring
set: tryout batch 2026-09
---

# Pretty Fly (For A White Guy) (The Offspring)

Tryout 2026-09. Moises стемы (B minor, 143 bpm, тональность группы A minor, pitch_semitones: -2). В плейбеке: backing vocals (`pb-other`) + drums (`pb-drums` для репетиций без барабанщика). Бас живой (`pb-bass: null`), гитары живые, лид-вокал живой.

## Сводка

- **bpm:** 143.0 — Moises стемы выровнены через `jamzone_warp_ext.py` (`--bpm 143 --downbeat 1`), клик 0 заглушен. Спереди отрезано 3 такта (12 долей = 5.035 с; немецкий сэмпл-интро пропущен), оригиналы до трима в `pre-trim/`. Downbeat стема на 0.783 с совпадает со входом барабанов.
- **pitch_semitones:** -2 (A minor, -1 тон от оригинала B minor)
- **pb-other:** `backing_vocals` (Moises background vocals: "Give it to me baby", "Uh huh uh huh", "Uno, dos, tres..."), авто-гейн -3.0 dBFS под ceiling -23 dBFS.
- **pb-drums:** `drums` (основная установка для репетиций без барабанщика).
- **pb-bass:** null (живой бас, Roma).
- **players:** alex: `guitars`, roma: `bass`, steve: `drums`, tanya: `vocals`.
- **mix.json:** `music/songs/The Offspring - Pretty Fly (For A White Guy)/mix.json`
- **Рендер:** OFF +2.574 с, lead +1 такт под стартовую фразу, длина 188.0 с (112 тактов).

## Cue

| Такт.доля музыки | Вход в рендере | Подсказка перед входом |
|---|---:|---|
| 1.1 | 0:03.357 | Pretty Fly … drums in ready go |
| 2.1 | 0:05.035 | vocal in ready go |
| 10.1 | 0:18.462 | all in ready go |
| 73.4 | 2:05.455 | bass verse ready go |

Разметка 2026-09-29 по отдельным стемам и сетке 143 BPM:

- Alex явно выбрал для первого `vocal in` **самый первый бэк «Give it to me baby»**, который уже находится в pb-other (~5.05 с), а не отдельный lead-вокал около 15 с.
- Общий вход около 19 с — 10.1; бас активно входит ~18.434 с (пересечение 20% RMS ~18.446 с), гитара подхватывает немного раньше.
- `bass verse ready go` привязан **к вокальному затакту на 73.4**, на долю раньше басового входа 74.1 / 125.874 с. Первый слог lead-вокала начинается ~125.354 с, ближайшая доля 125.455 с. Текст хранится целиком с `raw:true`, чтобы не добавлять `in` и не удваивать `ready go`.
- Последнее `go` на долю перед входом; название песни естественным темпом перед стартовым четырёхсловным блоком.

Предыдущая версия (1 cue) сохранена в `music/songs/The Offspring - Pretty Fly (For A White Guy)/versions/2026-09-29-before-cues-v1/`.

Версия с 4 cue сохранена в `versions/2026-09-29-cues-v2/`. Пересобраны плюс, прослушки pb-other/pb-drums, четыре practice и web-стем cues; актуальные preview/practice проверены HTTP-хешами через localhost:5173. Музыкальный `all.wav`, клик и playback WAV побайтно совпали с предыдущей версией. Измерения вокальных якорей сохранены в `analysis/cue-anchors-2026-09-29.json`. `sync_to_mainstage.sh --apply "Pretty Fly"` обновил `cues.wav` в риге.

## Файлы рендера (`auto-render/`)

- `click.wav`, `cues.wav`
- `pb-other.wav` (backing vocals)
- `pb-drums.wav` (drums)
- `all.wav`
- `cue_preview.mp3`, `pb-drums.mp3`, `pb-other.mp3`
- `practice-alex.mp3`, `practice-roma.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`
