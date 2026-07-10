---
type: person
updated: 2026-07-10
---

# Alex

Гитарист, владелец репозитория `cherry-daddies` (git-автор `alexandr-bbm`). Основной инструмент — электро/акустическая гитара; по ряду песен играет бас, а также ведёт живые синт-лид-линии (живые синты делятся между Alex и [Roma](roma.md)) и духовые (сакс) партии по назначению в `mix.json`.

## Живые партии по песням

Источник — ключ `players.alex` в `music/songs/*/mix.json` (стемы, которые убираются из practice-микса, т.е. играются вживую). Рендерятся в `auto-render/practice-alex.mp3` через [jamzone-render](../pipelines/jamzone-render.md).

### Сет 1
| Песня | Живые стемы |
|---|---|
| Better Off Alone | 09_Synth_Lead_1 |
| ATC — Around the World | 07_Synth_Pad_1, 08_Synth_Pad_2, 10_Synth_Strings |
| Shakira — Whenever, Wherever | 05_Rhythm_Electric_Guitar, 06/07_Distorted_Electric_Guitar (L/R) |
| Guru Josh — Infinity 2008 | 06_Synth_Pad |
| Alexandra Stan — Mr. Saxobeat | 06_Synth_Lead, 11_Saxophone |
| Alex Gaudino — Destination Calabria | 07_Baritone_Saxophone |
| Coldplay — Adventure of a Lifetime | 06_Acoustic_Guitar, 07_Electric_Guitar, 08_Electric_Guitar_(right) |
| The Weeknd — Blinding Lights | — (не играет) |
| Laurent Wolf — No Stress | 03_Synth_Bass (бас) |
| Gala — Freed from Desire | — (не играет) |
| Bruno Mars / Mark Ronson — Uptown Funk | 05_Electric_Guitar |

### Сет 2
| Песня | Живые стемы |
|---|---|
| Demo — Солнышко | bass, synth-bass (бас) |
| Band'Eros — Pro krasivuju zhizn' | guitars |
| SEREBRO — Malo tebya | guitars |
| Quest Pistols — Я устал | guitars |
| Basshunter — Now You're Gone | 07_Synth_Lead |
| Rihanna — S&M | 04_Electric_Bass, 05_Synth_Bass (бас) |
| Beverly Hills | — (в `players` нет; ⚠️ см. ниже) |
| Rihanna & Calvin Harris — We Found Love | — (не играет) |
| Cascada — Everytime We Touch | 09_Synth_Lead |
| Yeah Yeah Yeahs — Heads Will Roll | 06_Electric_Guitar, 07_Distorted_Electric_Guitar, 08_Electric_Guitar_(delay) |
| Icona Pop & Charli XCX — I Love It | 05_Synthesizer, 08_Synth_Lead, 09/10_Guitar_Synth (1/2) |

### На бис
| Песня | Живые стемы |
|---|---|
| Пропаганда — Мелом | guitars |
| t.A.T.u. — Я сошла с ума | — (не играет) |

Не играет вообще (нет партии): Blinding Lights, Gala, We Found Love, t.A.T.u.

## Бас

Играет бас на: No Stress (`web/songs.json` `bass.who = Alex`), а также — по `players` — Солнышко и S&M. ⚠️ Расхождение источников: `web/songs.json` помечает бас как назначенный Alex только на No Stress, тогда как `mix.json players` даёт Alex басовые стемы ещё на Солнышко и S&M. Остальной бас — у [Roma](roma.md).

## Рабочие факты

- Владелец репо и основной драйвер музыкального пайплайна (рендер, cue, Moises-импорт).
- Moises-песни (Band'Eros, Malo tebya, Я устал, Мелом): его живая партия — стем `guitars`.
- По контенту (рилсы): фидбек собирается со всей банды, не только с Alex — на реле-подарке (2026-06-11) банда выбрала более плотный по гэгам монтаж против «чистого» варианта, сделанного по сольным заметкам Alex.

## Связи

- [Roma](roma.md) — делит живые синты и духовые с Alex, основной басист.
- [Steve](steve.md) · [Tanya](tanya.md)
- Пайплайны: [jamzone-render](../pipelines/jamzone-render.md), [moises-import](../pipelines/moises-import.md), [cue-system](../pipelines/cue-system.md)
