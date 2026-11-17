---
type: person
updated: 2026-11-17
---

# Roma

> **Ушёл из группы 2026-11-16** (Alex), его MainStage-риг тоже. Ниже — как было; что теперь закрывать плейбеком — раздел «После ухода».

Клавишник и мастер плейбека банды. Его ноут (MainStage) — единственный источник click + playback (pb-other/pb-bass) + cues для всей группы; «готово отдать клавишнику» = полный пакет `auto-render/` на песню (см. [mainstage-rig](../pipelines/mainstage-rig.md)). Живые синты делятся между Roma и [Alex](alex.md) — Alex ведёт отдельные лид-линии, Roma закрывает остальные синты. Основной басист банды; по одной песне играет тенор-сакс, по одной — бас-гитару на бис.

## Живые партии по песням

Источник — ключ `players.roma` в `music/songs/*/mix.json` (стемы, играемые вживую; убираются из `auto-render/practice-roma.mp3`).

### Сет 1
| Песня | Живые стемы |
|---|---|
| Better Off Alone | 07_Synth_Pad, 08_Synth_Strings, 10_Synth_Lead_2, 11_Arpeggiator |
| ATC — Around the World | 06_Digital_Piano, 09_Synth_Strings_(pizzicato), 11_Synth_Lead, 12_Synth_Keys, 13_Vibes |
| Shakira — Whenever, Wherever | 10_Synth_Pad |
| Guru Josh — Infinity 2008 | 05_Synthesizer |
| Alexandra Stan — Mr. Saxobeat | 07/08/09_Synth_Keys (1/2/3) |
| Alex Gaudino — Destination Calabria | 08_Tenor_Saxophone |
| Coldplay — Adventure of a Lifetime | — (в `players` нет; бас, см. ниже) |
| The Weeknd — Blinding Lights | 06_Synthesizer, 07_Synth_Pad_1, 08_Synth_Pad_2 |
| Laurent Wolf — No Stress | 04_Piano, 05_Synthesizer |
| Gala — Freed from Desire | 04_Piano, 05_Organ, 06/07_Synth_Strings, 08_Synth_Lead, 09_Arpeggiator |
| Bruno Mars / Mark Ronson — Uptown Funk | — (в `players` нет; бас, см. ниже) |

### Сет 2
| Песня | Живые стемы |
|---|---|
| Demo — Солнышко | keys, other |
| Band'Eros — Pro krasivuju zhizn' | other, keys |
| SEREBRO — Malo tebya | other, keys |
| Quest Pistols — Я устал | other, keys |
| Basshunter — Now You're Gone | 05_Synthesizer, 06_Synth_Voice |
| Rihanna — S&M | 07_Synth_Lead, 08_Synth_Keys, 09_Arpeggiator |
| Beverly Hills | other, keys |
| Rihanna & Calvin Harris — We Found Love | 06/07/08_Organ (1/2/3), 09/10_Synth_Keys (1/2), 11_Synthesizer |
| Cascada — Everytime We Touch | 10_Synth_Keys_(Bells), 12_Bells |
| Yeah Yeah Yeahs — Heads Will Roll | 09_Synthesizer_(disto), 10_Synth_Pad, 11_Synth_Strings |
| Icona Pop & Charli XCX — I Love It | 06_Synth_Pad, 07_Synth_Strings |

### На бис
| Песня | Живые стемы |
|---|---|
| Пропаганда — Мелом | bass (бас-гитара) |
| t.A.T.u. — Я сошла с ума | — (в `players` нет) |

## Бас

Основной басист. По `web/songs.json` `bass.who`: живая бас-гитара на Coldplay и Uptown Funk; назначен бас на Better Off Alone, Band'Eros, Now You're Gone, Cascada, Мелом (на Мелом бас закреплён и в `players`). ⚠️ На Coldplay/Uptown его бас в `players` не отражён (закрыт плейбеком/pb-bass), поэтому в таблице выше эти песни без стемов.

## Рабочие факты

- Playback master: перерендер песни → стемы в боевом MainStage не обновятся сами, накатывает `tools/sync_to_mainstage.sh` (см. [mainstage-rig](../pipelines/mainstage-rig.md)).
- MainStage-риг также гонит тексты на сценический монитор (lyric-launcher запускается ДО MainStage) — [lyric-launcher](../pipelines/lyric-launcher.md).
- Клавишник вручную правит Lyrics-страйп per-set (No Output + диапазон в `.cst`); авто-проводка это не затирает.
- Moises-песни (Band'Eros, Malo tebya, Я устал, Beverly): его живая партия — смешанные стемы `keys`/`other` (изолировать отдельный синт нельзя — нужен layer).

## После ухода (2026-11-16): что он играл вживую

Рома ушёл из группы вместе с MainStage-ригом. Плейбек теперь локальный Stage Traxx ([stagetraxx-rig](../pipelines/stagetraxx-rig.md)). Всё, что он играл вживую, в плейбеке сейчас **отсутствует**: из 62 песен в сетах `web/songs.json` затронуто 55. Источник списков: `players.roma` в `mix.json` + `bass.who` в `web/songs.json` (снимок 2026-11-16). **Решение Alex (2026-11-16):** бас — везде в плейбек (pb-bass, уровень под медиану остальных pb-bass ≈ −19.2 LUFS); синты/клавиши — многие возьмёт Alex сам, остальное в pb-other, решается по песне. Делаем последовательно, песня за песней.

**Сделано:** 12.12 new songs — pb-bass в Sex on Fire, Ты меня не ищи, Владивосток 2000 (Попрошу тебя уже был), всё в Stage Traxx; прод не обновлялся. Клавиши в «Ты меня не ищи» (такты 41–66, 100–конец) играет Alex (`players.alex`, 2026-11-17). Ту-лу-ла: pb-bass (+2.8 дБ → −19.2 LUFS), в Stage Traxx, 2026-11-17. Everytime We Touch: pb-bass (оба синт-баса −2 дБ → −19.2 LUFS), в Stage Traxx, 2026-11-17; колокольчики (`10_Synth_Keys_(Bells)`, `12_Bells`) — в pb-other (Alex: «в плейбек»), 2026-11-17. Про красивую жизнь: pb-bass (−2.9 дБ → −19.2 LUFS) + клавиши `keys`/`other` в pb-other (Alex: «в плейбек»), в Stage Traxx, 2026-11-17. Pretty Fly (−3.9 дБ), Кукла колдуна (−0.9 дБ), Мелом (+3.1 дБ, −20.8 LUFS — упор в пик): pb-bass из стемов, в Stage Traxx, 2026-11-17. Концертные партии Ромы (мультитрек 28.10, 2026-11-17, решения Alex): бас — Ту-лу-ла (вместо стема); клавиши — Про красивую жизнь, Мало тебя, Беги от меня (бис, деклип), Солнышко (временно, перезаписать), Beverly Hills; Медляк — стем; Такая любовь — слой Ромы + концерт поверх. Затем (тот же день): живой бас — Кукла колдуна, Медведица, Pretty Fly; клавиши — Солнце, Кислотный DJ, Я устал. Слои баса называются «живой бас» (Stage Traxx: «PB Bass · живой бас»). Подробно — `wiki/gigs/2026-10-28-multitrack.md`. Устаревшие `practice-roma.mp3` (Everytime, Ту-лу-ла, Про красивую жизнь, Pretty Fly, Кукла колдуна, Мелом) убраны из `auto-render/` (рендер `--practice` пишет их только при `players.roma`).

### Концертные дорожки 28.10 Music Hall — кандидаты в плейбек (2026-11-17)

Мультитрек с микшера, весь концерт (Set 1 №1–10, Set 2 №1–17 с бисом), 48 кГц, по папке на песню; полностью тихие каналы в экспорт не попали. Папки: `~/Downloads/Cherry Daddies 28.10 raw stems - set1.1-5|set1.6-10|set2.1-6|set2.14-17/Set N/`, Set 2 №7–13 — `~/Downloads/Set 2/`. Скрипт разметки: scratchpad сессии `concert_inventory2.py`. Порядок (Alex): сначала кандидаты, потом анализ «концерт / стем / вместе».

**Каналы `08` и `09` подписаны наоборот** (Alex: выходы весь концерт не менялись; проверено): `08 Guitar LR` = **клавиши Ромы**, `09 Keys LR` = **гитара Alex**, `07 Bass Guitar` = бас Ромы. Проверка — выравнивание по каналу `14 Cues` против `auto-render/cues.wav` (корреляция огибающих 0.85–0.98 у большинства песен; клик не годится — периодичен) и хрома по 0.5-с кадрам против стемов: `09` ↔ гитарный стем 0.91 / 0.88 / 0.76 (Солнце / Такая любовь / Ту-лу-ла), `08` ↔ клавиши/духовые (Кислотный DJ: wind 0.83, guitars 0.58). Живые каналы не совпадают с плейбеком концерта (огибающая ≤ 0.2 против `PB Other`/`PB Bass` и стемов) — это живое исполнение. Тональность концертного баса = тональность группы.

**Правила Alex (2026-11-17):** клавиши в **английских** песнях — **только стемы JamZone**; песня есть в JamZone → и бас из стема (Я сошла с ума). «Беги от меня» — исполнение **с биса**. Beverly Hills — клавиши Ромы с концерта (кандидат). Мелом — играли без метронома, пока не рассматриваем.

**Бас Ромы — кандидаты (`07`):**

| Песня | `07` активен | Стемы | Сейчас pb-bass |
|---|---|---|---|
| Ту-лу-ла | 89% | Moises | из стема (2026-11-17) |
| Медведица | 96% | Moises | **нет** |
| Pretty Fly | 88% | Moises | из стема (2026-11-17) |
| Кукла колдуна | 93% | Moises | из стема (2026-11-17) |
| ~~Я сошла с ума~~ | 75% | JamZone | из стема (2026-11-17) — есть в JamZone → стем (Alex) |
| ~~Ghostbusters~~ | 63% | JamZone | из стема (2026-11-17) — по тому же правилу |
| ~~Мелом~~ | 49% | Moises | из стема — **пока не рассматриваем**: на концерте играли без метронома (Alex) |

**Клавиши Ромы — кандидаты (`08`, русские песни):**

| Песня | `08` активен | Сейчас в pb-other | Заметка |
|---|---|---|---|
| Солнце | 97% | keys Ромы нет | |
| Беги от меня (бис, S2.17) | 85% | keys Ромы нет | в `players` не было — пропуск; брать бис |
| Такая любовь | 86% (S1.04) / 79% (бис, S2.16) | keys/strings/wind нет | **два дубля** |
| Про красивую жизнь | 97% | keys + other из Moises (2026-11-17) | сравнить с концертом |
| Солнышко | 83% | keys/other Ромы нет | |
| Я устал | 74% | keys/other Ромы нет | |
| Медляк | 83% | — | в `players` Ромы нет — **пропуск** |
| Мало тебя | 87% | keys/other Ромы нет | |
| Кислотный DJ | 89% | keys/strings/wind нет | |
| Beverly Hills | 96% | other/keys Ромы нет | английская, но Moises — концерт (Alex) |

**Без концертного кандидата:**
- Английские (JamZone) → клавиши Ромы из стемов JamZone: Around the World (`08` 98%), Blinding Lights (95%), Whenever, Wherever (94%), Everytime We Touch (97%, колокольчики уже в pb-other), Destination Calabria (91%, тенор-сакс Ромы), Freed From Desire (91%), Heads Will Roll (91%), I Love It (`08` молчит).

**Для анализа:** выравнивание по Cues слабое (корреляция < 0.6) у Беги от меня, Heads Will Roll, I Love It, Destination Calabria, Freed From Desire, Медведица, у Мелома канала Cues нет — там выравнивать по `PB Other`/`PB Bass` против рендера или по барабанам.

### Бас вживую, pb-bass нет (34 + Медведица)

| Песня | Стем баса | Сеты |
|---|---|---|
| Ту-лу-ла | bass | СЕТ 1 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Everytime We Touch | — (по bass.who) | СЕТ 1 · 28.10 Music Hall; СЕТ 2 |
| Про красивую жизнь | — (по bass.who) | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Pretty Fly | bass | СЕТ 2 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Кукла колдуна | bass | СЕТ 2 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Медведица | bass | СЕТ 2 · 28.10 Music Hall (добавлена 2026-11-17: найдена по концертному мультитреку — `players`/`bass.who` нет) |
| Мелом | bass | Бис · 28.10 Music Hall; на бис |
| Я сошла с ума | 06_Bass | Бис · 28.10 Music Hall; на бис |
| Ghostbusters (запас) | 03_Bass | Бис · 28.10 Music Hall; SET 2 · 24.10 Lefkara (11 песен) |
| Stayin' Alive | 04_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Sunny | 03_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Venus | 03_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Sarà perché ti amo | 03_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| You're My Heart, You're My Soul | 04_Synth_Bass_1, 05_Synth_Bass_2 | SET 1 · 24.10 Lefkara (10 песен) |
| Mamma Maria | 03_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Gimme! Gimme! Gimme! | 04_Electric_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Hot Stuff | 04_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| It's Raining Men | 05_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| I Will Survive | 04_Bass | SET 1 · 24.10 Lefkara (10 песен) |
| Stumblin' In | 04_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Cheri Cheri Lady | 03_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Felicità | 03_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Brother Louie | 03_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Heart of Glass | 04_Electric_Bass, 05_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| What a Feeling | 04_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Maniac | 04_Synth_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Holding Out for a Hero | 03_Synth_Bass_1, 04_Synth_Bass_2 | SET 2 · 24.10 Lefkara (11 песен) |
| YMCA | 05_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| The Best | 03_Electric_Bass | SET 2 · 24.10 Lefkara (11 песен) |
| Better Off Alone | — (по bass.who) | СЕТ 1 · Мировые танцевальные хиты |
| Adventure of a Lifetime | — (по bass.who) | СЕТ 1 · Мировые танцевальные хиты |
| Uptown Funk | — (по bass.who) | СЕТ 1 · Мировые танцевальные хиты |
| Now You're Gone | — (по bass.who) | СЕТ 2 |
| Rock & Roll Queen | 03_Bass | 28.10 new songs · новые песни |
| Sex on Fire | 03_Bass | 12.12 new songs · новые песни |

### Синты / клавиши / сакс вживую, в pb-other нет (25 + Беги от меня, Медляк)

| Песня | Стемы | Сеты |
|---|---|---|
| Солнце | keys | СЕТ 1 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Around the World | 13_Vibes, 11_Synth_Lead, 06_Digital_Piano, 12_Synth_Keys, 09_Synth_Strings_(pizzicato) | СЕТ 1 · 28.10 Music Hall; СЕТ 1 · Мировые танцевальные хиты |
| Такая любовь | keys, strings, wind | СЕТ 1 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Blinding Lights | 06_Synthesizer, 07_Synth_Pad_1, 08_Synth_Pad_2 | СЕТ 1 · 28.10 Music Hall; СЕТ 1 · Мировые танцевальные хиты |
| Whenever, Wherever | 10_Synth_Pad | СЕТ 1 · 28.10 Music Hall; СЕТ 1 · Мировые танцевальные хиты |
| Everytime We Touch | 10_Synth_Keys_(Bells), 12_Bells | СЕТ 1 · 28.10 Music Hall; СЕТ 2 |
| Destination Calabria | 08_Tenor_Saxophone | СЕТ 1 · 28.10 Music Hall; СЕТ 1 · Мировые танцевальные хиты |
| Freed From Desire | 04_Piano, 05_Organ, 06_Synth_Strings, 07_Synth_Strings_(treble), 08_Synth_Lead, 09_Arpeggiator | СЕТ 1 · 28.10 Music Hall; СЕТ 1 · Мировые танцевальные хиты |
| Beverly Hills | other, keys | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Про красивую жизнь | other, keys | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Солнышко | keys, other | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Я устал | other, keys | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Мало тебя | other, keys | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Heads Will Roll | 09_Synthesizer_(disto), 10_Synth_Pad, 11_Synth_Strings | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| I Love It | 06_Synth_Pad, 07_Synth_Strings | СЕТ 2 · 28.10 Music Hall; СЕТ 2 |
| Мама Люба | keys, strings, wind | СЕТ 2 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Кислотный DJ | keys, strings, wind | СЕТ 2 · 28.10 Music Hall; 28.10 new songs · новые песни |
| Беги от меня | keys (Moises) | СЕТ 1 · 28.10 Music Hall (добавлена 2026-11-17: по концертному мультитреку, в `players` не было) |
| Медляк | keys (Moises) | СЕТ 2 · 28.10 Music Hall (добавлена 2026-11-17: `08` активен 83%, в `players` Ромы не было) |
| Better Off Alone | 07_Synth_Pad, 11_Arpeggiator, 08_Synth_Strings, 10_Synth_Lead_2 | СЕТ 1 · Мировые танцевальные хиты |
| Infinity 2008 | 05_Synthesizer | СЕТ 1 · Мировые танцевальные хиты |
| Mr. Saxobeat | 08_Synth_Keys_2, 07_Synth_Keys_1, 09_Synth_Keys_3 | СЕТ 1 · Мировые танцевальные хиты |
| No Stress | 04_Piano, 05_Synthesizer | СЕТ 1 · Мировые танцевальные хиты |
| Now You're Gone | 05_Synthesizer, 06_Synth_Voice | СЕТ 2 |
| S&M | 07_Synth_Lead, 09_Arpeggiator, 08_Synth_Keys | СЕТ 2 |
| We Found Love | 06_Organ_1, 07_Organ_2, 08_Organ_3, 09_Synth_Keys_1, 10_Synth_Keys_2, 11_Synthesizer | СЕТ 2 |
| Eva 2.0 | keys, strings, wind | Архив · снято с программы |

## Связи

- [Alex](alex.md) — делит живые синты/духовые, играет бас на части песен.
- [Steve](steve.md) · [Tanya](tanya.md)
- Пайплайны: [mainstage-rig](../pipelines/mainstage-rig.md), [lyric-launcher](../pipelines/lyric-launcher.md), [jamzone-render](../pipelines/jamzone-render.md)
