---
type: person
updated: 2026-07-10
---

# Steve

Барабанщик. Играет живую барабанную установку во ВСЕХ песнях сетлиста.

## Живые партии

Источник — ключ `players.steve` в `music/songs/*/mix.json`. В каждой песне назначен основной drum kit:

- JamZone-песни: `02_Drum_Kit` или `02_Electronic_Drum_Kit`.
- Moises-песни (Band'Eros, Malo tebya, Я устал, Beverly, Солнышко, Мелом): `drums`.

Установка убирается из practice-миксов (Steve играет её сам); барабаны остаются в общем плейбеке/превью как единственная перкуссия.

## Перкуссия — только основной кит

КРИТИЧНО для рендера: вся перкуссия КРОМЕ основной установки (конги, шейкеры, тамбурин, каубелл, клэпы, `Percussion`/`Electronic_Percussion`) НИКОГДА не идёт в плейбек/превью — её играет живой барабанщик, и перкуссия в плейбеке с ним конфликтует. В миксе оставляют только `drums` / `Drum_Kit` / `Electronic_Drum_Kit`, остальную перкуссию выкидывают из `pb-other`/`pb-bass`/`all`/превью. Подробности и прецедент-чистка (t.A.T.u. `03_Percussion`) — см. [jamzone-render](../pipelines/jamzone-render.md).

## Связи

- [Alex](alex.md) · [Roma](roma.md) · [Tanya](tanya.md)
- Пайплайн: [jamzone-render](../pipelines/jamzone-render.md)
