---
type: song
updated: 2026-11-19
title: Supermassive Black Hole
artist: Muse
set: 12.12 new songs
status: draft (GM-800 MUTE, POD Go 32D; 12 базовых cue, pb-other бэки+синт+нойз+синт-бас, pb-bass; в Stage Traxx, прод не публиковался)
---

# Supermassive Black Hole (Muse)

Добавлена 2026-11-19 в секцию **12.12 new songs** вместо Sex on Fire (та ушла в «Архив»). Источник: JamZone `cat_12553`, 12 стемов HQ (~124 kb/s), перкуссии нет.

## Сводка

- **Сетка:** ровные 120.00 bpm из `01_Click.m4a` (419 кликов, отклонение до 0.4 мс), 4/4, первый клик = сильная доля. Тональность родная (`pitch_semitones: 0`).
- **Каунт-ин:** +1 такт спереди, чтобы название песни в стартовом cue не обрезалось. OFF = +1.703 с: такт 1.1 = 2.000 с рендера.
- **Секции JamZone:** Precount 1 · Intro 2 · Verse 18 · Chorus 26 · Verse 2 42 · Chorus 2 50 · Break 66 · Instrumental 74 · Chorus 3 82 · Outro 98 · конец 106.

## Плейбек

- **pb-other:** `11_Backing_Vocals` (back-vox, авто −5.4 дБ), `09_Synthesizer`, `10_Noise_effects` (fx, авто −11.7 дБ), `04_Synth_Bass` (−6.5 дБ) + `"peak": "limit"`. `09_Synthesizer` играет только переходы (такты 41, 65, 81, 97) с пиком 0 dBFS. Без лимитера группа ужималась бы целиком, а так лимитер трогает 225 сэмплов. −15.7 LUFS.
- **pb-bass:** `03_Electric_Bass` −6.5 дБ → −19.2 LUFS (норма программы), пик −9.4 dBFS. Синт-бас дублирует бас в припевах и стоит в pb-other с тем же −6.5 дБ, чтобы их баланс остался оригинальным (правило Alex с Now You're Gone: синт → pb-other).
- pb-other + pb-bass = −15.2 LUFS (середина программы).
- **Не в плейбеке:** барабаны (Steve), лид-вокал (Tanya), все 4 гитары: `05` theme (рифф), `06` fuzz (интро 9–17, припевы), `07` lead (соло 74–81, припев 3), `08` arr. `players` не заданы.
- **Риг Alex:** GM-800 = 1 MUTE (`PC0@2`), POD Go = 32D (`PC127@3`) на всю песню (Alex, 2026-11-19), в Stage Traxx.

## Cue (12)

Входы гитар и барабанов — на сильную долю: атака приходится на последнюю шестнадцатую перед долей, затакта на 4& нет. Вокал — по словам из `tiles.json` и онсетам стема.

| такт.доля | cue | что |
|---|---|---|
| 2.1 | Supermassive Black Hole · all in | рифф + барабаны + бас |
| 18.2 | verse in | «Ooh baby…» на 2-ю долю |
| 26.1 | chorus in | fuzz + бас + синт-бас |
| 42.2 | verse in | «I thought…»; гитары молчат 42–45 |
| 46.1 | guitar in | рифф возвращается |
| 50.1 | chorus in | |
| 66.1 | break in | рифф; «Supermassive black hole» с 67 |
| 74.1 | solo in | lead guitar 74–81 |
| 82.1 | chorus in | «Glaciers melting…» 82–89 поёт бэк (в плейбеке) |
| 90.1 | vocal in | вход лид-вокала «Ooh» (подъезд с 89.4&) |
| 98.1 | outro in | рифф как в интро |
| 105.1 | end in 3 · 3 2 1 (`count`) | последний такт: удары 1&, 2&, обрыв на 3&; вокал тянет «hole» |

## Открытое

- Не проверено на слух: послушать `auto-render/cue_preview.mp3`. Формулировки cue черновые.
- `players` / practice-миксы не заданы.
