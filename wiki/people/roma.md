---
type: person
updated: 2026-07-10
---

# Roma

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

## Связи

- [Alex](alex.md) — делит живые синты/духовые, играет бас на части песен.
- [Steve](steve.md) · [Tanya](tanya.md)
- Пайплайны: [mainstage-rig](../pipelines/mainstage-rig.md), [lyric-launcher](../pipelines/lyric-launcher.md), [jamzone-render](../pipelines/jamzone-render.md)
