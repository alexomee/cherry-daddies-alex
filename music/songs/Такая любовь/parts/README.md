# Пользовательский playback

## sfx-pb.wav — 2026-10-12 (апдейт)

Дорожка sound fx от Alex:
- Источник: `/Users/alex/Downloads/sfx pb.mp3` (Logic Pro 11.2.2 bounce, 48 kHz / 320 kbps stereo, 135.168 с от такта 35).
- Сконвертирован в 24 bit / 44.1 kHz stereo (`pcm_s24le`) с выравниванием по сетке рендера (lead 64.0 с до такта 35).
- Фрейм **render**: тайминг соответствует линейке рендера от t=0.
- Содержимое: шумовые свипы, эффекты, райзеры, доработанные эффекты вокруг гитарного соло (такты 93–97 перед solo leak):
  - 63.9 – 94.4 с (такты ~35 – 52)
  - 122.5 – 185.4 с (такты ~68 – 103, включая переход на solo leak на такте 97)
  - 198.1 – 199.3 с: райзер перед припевом (вход на такте 111 / 199.111 с)
- Роль: `fx` (автоматическое выравнивание до потолка `FX_CEILING = -30.0 dBFS` gated RMS, gain −8.9 dB).
- `mix.json`: включён как слой в `pb-other`:
  ```json
  "pb-other": {
    "stems": ["strings"],
    "layers": [
      {"file": "sfx-pb", "frame": "render"}
    ],
    "roles": {"sfx-pb": "fx"}
  }
  ```
## acoustic-guitar-solo.wav — 2026-10-12

Партия акустической гитары на соло от Alex:
- Источник: `/Users/alex/Downloads/acoustic guitar on solo pb.mp3` (Logic Pro 11.2.2 bounce, 48 kHz / 320 kbps stereo, 245.4 с от t=0).
- Сконвертирован в 24 bit / 48 kHz stereo (`pcm_s24le`).
- Фрейм **render**: тайминг соответствует линейке рендера от t=0.
- Содержимое: ритмический аккомпанемент акустической гитары на гитарном соло (165.2 – 194.8 с, такты ~92 – 108).
- Роль: `musical` (уровень сохраняется как в баунсе из Logic, пик −0.2 dBFS).
- `mix.json`: включён как второй слой в `pb-other`:
  ```json
  "pb-other": {
    "stems": ["strings"],
    "layers": [
      {"file": "sfx-pb", "frame": "render"},
      {"file": "acoustic-guitar-solo", "frame": "render"}
    ],
    "roles": {"sfx-pb": "fx", "acoustic-guitar-solo": "musical"}
  }
  ```
- Результирующий `auto-render/pb-other.wav` создан с tempo-меткой 135.0 BPM.
