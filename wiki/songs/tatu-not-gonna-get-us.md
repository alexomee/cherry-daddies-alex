---
type: song
updated: 2026-11-19
title: Нас не догонят (playback из Not Gonna Get Us)
artist: t.A.T.u.
set: не в сетлисте (новая)
---

# t.A.T.u. — Not Gonna Get Us (Нас не догонят)

Стемы английской версии из JamZone, **исполняем русскую «Нас не догонят»** (Alex, 2026-11-19). Папка: `/Users/alex/projects/cherry-daddies/music/songs/t.A.T.u. - Not Gonna Get Us (Нас не догонят)/`.

## Сводка

- **Источник:** JamZone `cat_25870`, 15 HQ-стемов (`.m4a`), заведена 2026-11-19.
- **bpm:** 130 (клик JamZone, ресид 0.4 мс). Оригинал C#m (JamZone пишет «A»).
- **pitch_semitones: −4** (C#m → Am, ключ группы, Alex 2026-11-19). Питчатся pb-other, pb-bass, all, practice-миксы.
- **Sound effects НЕ питчатся:** это шумовой райзер (спектральная плоскостность 0.04–0.15 против 0.001 у пэда, хрома D/A/C/G# вне C#m, один и тот же сэмпл во всех 7 местах). Сделано слоем: `parts/sound-effects.wav` = декод `12_Sound_effects.m4a` 1:1, `frame: stem`, `replaces: [12_Sound_effects]` (оригинал вон из all). Слой авто-уровнится как fx (−7.7 дБ). Проверено: в pb-other совпадает с исходником по форме волны (corr 0.98), лаг 0; бас −4 полутона, лаг 0.
- `timeline.json`: `offset_sec` −0.297 (рендер начинается с первой сильной доли клика), каунт-ин не нужен: название влезает в такт 1.
- **Плейбек = всё, кроме гитары и английских бэков** (Alex): pb-other = `06_Electric_Piano`, `07_Synth_Pad`, `08_Synth_Voice`, `09_Synth_Lead`, `10_Arpeggiator_1`, `11_Arpeggiator_2` + слой `sound-effects`; pb-bass = `04_Synth_Bass`. `13/14_Backing_Vocals` (английские) убраны из pb-other, но остаются в `all` и practice-миксах как референс. Барабаны (steve) и лид-вокал (tanya) живьём, `03_Claves-Woodblock` выкинут как перкуссия.
- **players:** steve → `02_Electronic_Drum_Kit`, tanya → `15_Lead_Vocal`, alex → `05_Electric_Guitar`; practice-миксы для всех троих.
- GM-800 / POD Go не заданы.

## Структура (такты mix.json, 1 аккорд на такт)

| такты | секция | кто играет | гармония |
|---|---|---|---|
| 1–2 | Precount | только Synth Voice (плейбек) | — |
| 3–6 | Intro | + барабаны, fx | C5 (педаль) |
| 6.4&–13 | Intro | вокал «They're…» с затакта, всё вступает 7.1 | A C#m C#m E Amaj7 C#m C#m |
| 14 | — | барабаны молчат, стаб гитары+баса на 1 | E |
| 15–22 | Verse | только E-piano + вокал | A C#m ×3, F#m B7 |
| 23–30 | Verse (вторая половина) | барабаны + бас; бас уходит с 27, такт 30 без барабанов | A G#m C#m E A G# C#m E |
| 31–46 | Chorus | всё; 38 — брейк барабанов внутри припева; 46 — брейк, стаб на 1 | A G# C#m E |
| 47–61 | Instrumental | всё, лид-синт | A G# C#m E |
| 62 | — | только барабаны; стаб остальных на 1 | N.C. |
| 63–77 | Verse 2 | всё; 70 — стаб на 1, барабаны молчат до 3& | A G#5 C#m E |
| 78 | — | общий стаб на 1 (крэш с эхом) | N.C. |
| 79–94 | Break | E-piano + бэки, барабанов и гитары нет | (A C#m ×3, F#m7 B7) ×2 |
| 95–110 | Chorus 2 | всё; **110.1 — финальный общий удар (наша концовка)** | A G# C#m E |
| 111–115 | Outro оригинала | барабаны + бэки, **вырезано** | — |

Барабанный грув заканчивается на **4&** такта: последний удар перед каждым стопом = доля «4&», стаб гитары/баса — на следующую 1.

## Аккорды для гитары (Am, −4)

Файл: `/Users/alex/projects/cherry-daddies/music/songs/t.A.T.u. - Not Gonna Get Us (Нас не догонят)/chart.txt`. Из `tiles.json`, транспонировано −4 (A→F, G#→E, C#m→Am, E→C, F#m→Dm, B7→G7). Стабы на тактах без аккорда в JamZone (14, 46, 62, 70, 78, 110) определены по гитарному стему.

```

INTRO   [1-6]   барабаны + synth voice                       [гитара молчит]
INTRO   [7-14]  F Am Am C | Fmaj7 Am Am C!
V1      [15-22] F Am F Am | F Am Dm G7                        [гитара молчит, пиано]
V1b     [23-30] F Em Am C | F E Am C                          [гитара молчит, барабаны+бас; 30 без барабанов]
CH      [31-46] F E Am C | F E Am C5 | F E Am C | F E Am C!   (38 брейк барабанов)
INSTR   [47-62] F E Am C | F E Am C | F E Am C | F E Am C!    (62 стаб, дальше барабаны соло)
V2      [63-78] F E5 Am C | F E5 Am Am! | F E5 Am C | F Em Am Am!
BREAK   [79-94] (F Am F Am | F Am Dm7 G7) x2                  [гитара молчит]
CH2     [95-110] F E Am C | F E Am C5 | F E Am C | F E Am C!  (110.1 финальный удар — конец)
```

## Cue (14, правки Alex 2026-11-19)

| такт.доля | render | текст | звучит | зачем |
|---|---|---|---|---|
| 3.1 | 0:03.7 | Нас не догонят drums in | название + drums in ready go | плейбек с 1.1, барабаны с 3.1 |
| 7.1 | 0:11.1 | all in | all in ready go | вся банда; на сильную долю (Alex), «go» на 6.4 под затакт вокала |
| 13.4& | 0:23.8 | drums stop | stop in 3, 3 2 1 | такт 14 без барабанов |
| 23.1 | 0:40.6 | drums in | ready go | барабаны+бас, смена гармонии |
| 29.4& | 0:53.3 | drums stop | stop in 3, 3 2 1 | такт 30 без барабанов |
| 31.1 | 0:55.4 | drums in | ready go | припев |
| 45.4& | 1:22.8 | drums stop | stop in 3, 3 2 1 | такт 46 |
| 47.1 | 1:24.9 | solo in | ready go | Instrumental (лид-синт) |
| 62.1 | 1:52.6 | drums-only in (count) | drums only in 3, 3 2 1 | все бьют стаб на 1, дальше такт барабанов |
| 69.4& | 2:07.2 | drums stop | stop in 3, 3 2 1 | стоп в Verse 2 |
| 70.3& | 2:08.5 | drums in (step 0.5) | drums in ready go по полдоли на 70.1&…70.3 | барабаны возвращаются на 70.3& |
| 78.1 | 2:22.2 | all stop | stop in 3, 3 2 1 | общий стаб, дальше Break |
| 95.1 | 2:53.5 | chorus in | ready go | второй припев |
| 110.1 | 3:21.2 | end in (count) | end in 3, 3 2 1 | **концовка для всех** |

**Концовка (Alex 2026-11-19):** песня кончается общим ударом на 110.1. `fade_out` всех стемов 110.1.25 → 110.3 (0.8 с после удара), `cut_after_last_cue: 1` — рендер 110 тактов = 203.08 с, аутро 111–115 (барабаны + «not gonna get us») выброшено. Гармония в 110 — C (стаб).

Без cue: стоп 37.4& (внутри припева), возврат на Verse 2 (63).

## История

- **2026-11-19** — заведена: стемы JamZone, mix.json, рендер `--practice`, 12 черновых cue. В Stage Traxx не синкалась.
- **2026-11-19** — русская версия: pitch −4, бэки вон из pb-other, Sound effects слоем без питча, стартовый cue «Нас не догонят drums in» (Milena). OFF не изменился (−0.297). Дашборд: строка сетлиста привязана к папке (`setlist_dashboard.py`).
- **2026-11-19** — правки cue (Alex): all in на 7.1, drums in 31 и 70.3&, solo in 47, drums-only in 62 (счётный), end in 110.1 + обрезка после (fade + cut_after_last_cue 1); 203.08 с. Stage Traxx обновлён.
- **2026-11-19** — в Stage Traxx (`stagetraxx_sync.py --apply`, новая песня): Click/Cues/PB Other/PB Bass включены, Drums/Vocals/All замьючены, все треки 216.00 с = рендер. Текстового клипа нет (только START/STOP).
