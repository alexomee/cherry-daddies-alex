---
type: song
updated: 2026-07-10
title: Я устал
artist: Quest Pistols
set: СЕТ 2 #4
---

# Я устал — Quest Pistols

Позиция: **СЕТ 2 #4** (`web/songs.json`, sid `Quest Pistols - Я устал`).
Папка: `/Users/alex/projects/cherry-daddies/music/songs/Quest Pistols - Я устал/`.

## Сводка

- **bpm:** 124.0 (главный темп ровных секций).
- **pitch_semitones:** не задан в `mix.json` (питч не применяется).
- **Особые поля:** `click: "follow"` (переменный темп — есть реальная смена темпа в середине), `tempo_zone` (half-time брейкдаун), `layers` в `pb-other` и `pb-bass`, `players` на 5 человек. `cue_step`/`count_in` не заданы.

## Плейбек и рендер

Стемы (Moises): `bass.mp3`, `drums.mp3`, `guitars.mp3`, `keys.mp3`, `other.mp3`, `vocals.mp3`, `metronome.mp3`.

Layers (см. [layers/Moises-импорт](../pipelines/moises-import.md)):
- `pb-other` ← `backing-vocal` (frame `render`, gain 0 dB). Оригинал: `parts/backing-vocal.aif`.
- `pb-bass` ← `live-bass` (frame `render`, gain −10 dB, **`replaces: ["bass"]`** — живой бас вместо студийного; студийный `bass` выкидывается из `all`/превью). Оригинал: `parts/live-bass.aif`.

Players / practice-миксы (`auto-render/practice-<player>.mp3`, все присутствуют):
- `roma`: other, keys
- `steve`: drums
- `tanya`: vocals
- `alex`: guitars

Рендеры в `auto-render/`: `all.wav`, `click.wav`, `cues.wav`, `pb-bass.wav`, `pb-other.wav`, `cue_preview.mp3` (+ варианты `cue_preview_click+10/_20db/_30db.mp3` — эксперименты громкости клика), `timeline.json`, `15-lyric-review.mp4` (обзор таймд-лирики). См. [jamzone-render](../pipelines/jamzone-render.md).

## Cue

11 cue (см. [cue-система](../pipelines/cue-system.md)):
1. bar 1 — «Я устал bass in» (стартовый, название песни)
2. bar 3 — «drums in»
3. bar 13 — «stop»
4. bar 25 — «verse in»
5. bar 33 — «stop»
6. bar 44 — «keep going»
7. bar 53 — «stop» (вход в брейкдаун)
8. bar 54.1 — «vocal in» (`fast: true`)
9. bar 55.4 — «drums in» (`fast: true`)
10. bar 65.3 — «chorus in» (возврат из брейка)
11. bar 90 — «bass-only in» (`count: true` → «bass only in 3, 3 2 1»)

Особенности:
- **tempo_zone** (bar 53.3 → 63.2, bpm 89.919, `anchor_sec` 102.083742, `return_sec` 131.766742, `accent: 4`, `accent_from: 211`, **`subdiv: 2`** — 8-е в брейке). Half-time брейкдаун лечится переменным `click: "follow"`, а не константной сеткой (иначе накопится дрейф в целые доли). См. правило «Реальная смена темпа в середине» в `CLAUDE.md`.
- 2 брейк-cue помечены `fast: true`, счёт идёт по 2 клика на слово (субдив-тики).
- bar 90 — счётный вход (`count: true`).

## История и гочи

- **2026-06-13** — оцифровка 4 старых cue-треков + черновики новых; введён `click: "follow"` в `jamzone_render.py` для реальной смены темпа. Много итераций по брейкдауну: Moises-метроном ВРЁТ на драм-брейке (держит 124 до 107.1с, реальные слоу-кики с 105.0с) → `tempo_zone` задан ВРУЧНУЮ, anchor на ровную часть брейка. Старый cue-клик из Logic как референс не годится (24% на киках против 90% у Moises-метронома).
- **2026-06-13/14** — выбор разрешения клика в брейке: четверти били 21% киков, 8-е 53%, 16-е 95%; в итоге `subdiv: 2` (8-е) по просьбе (реже). Возврат к константному 89.919 bpm (фит по 9 меткам, ±31мс) — один ровный клик барабанщику. Даунбит возврата привязан к реальному кик-дропу (134.5с рендер), не к метроному.
- **2026-06-15** — убран лишний первый cue «verse in» (bar 5).
- **2026-06-20** — `extend breakdown 2 fast beats`: half-time брейк оставлял пост-брейк музыку ~2 быстрые доли (≈полтакта) не в фазе с непрерывной 124-сеткой, на которой крутится арпеджиатор MainStage → арп дрейфовал на возврате. Вставлено ровно 2 быстрые доли (0.9677с) тишины в интро-паузу брейка (стемы + layers `live-bass`/`backing-vocal`), anchor/return `tempo_zone` сдвинуты +0.9677с.
- **2026-06-22** (память `todo-15-ya-ustal-lyrics`) — таймд-лирика для lyric-launcher (сет #15 в той нумерации) перестроена через mlx-whisper diff-пасс: добавлен 2-й вариант припева «иду на дно», рэп «Обезьяна» сдвинут 1:20→1:51, заполнено ~40с аутро. См. [lyric-launcher](../pipelines/lyric-launcher.md).

## Открытое

- **Аутро-тайминг лирики (2:29–2:52)** ждёт слуха Тани — участок, где whisper зацикливается на галлюцинациях; слова/порядок верны, тайминг может требовать подвижки (память `todo-15-ya-ustal-lyrics`).
- В папке лежат служебные каталоги `aligned/`, `break-fix-backup/`, `old-cue-render/`, `auto-render/untitled folder` — артефакты итераций, не вычищены.
- `bass.mp3` и `metronome.mp3` датированы 13 июня, тогда как остальные стемы — 20 июня (break-fix). Похоже, при вставке 2 долей `bass`/`metronome` не переобрабатывались (bass заменён на live-bass) — проверить, что это осознанно, а не рассинхрон стемов.
