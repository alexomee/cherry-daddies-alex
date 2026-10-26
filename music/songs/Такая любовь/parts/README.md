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
- Содержимое: ритмический аккомпанемент акустической гитары на гитарном соло (165.2 – 179.6 с, такты 92–99 до начала 3-го куплета).
- 2026-10-26: после 2:59 (с такта 100, cue «verse in») слой заглушен через `"mute": {"acoustic-guitar-solo": [[100, 138]]}`, чтобы не звучать в куплете, где Алекс играет вживую.
- Роль: `musical` (`gain_db: -3.5`).
- `mix.json`: включён как второй слой в `pb-other`:
  ```json
  "pb-other": {
    "stems": ["strings"],
    "layers": [
      {"file": "sfx-pb", "frame": "render"},
      {"file": "acoustic-guitar-solo", "frame": "render", "gain_db": -3.5}
    ],
    "roles": {"sfx-pb": "fx", "acoustic-guitar-solo": "musical"},
    "mute": {"acoustic-guitar-solo": [[100, 138]]}
  }
  ```
- Результирующий `auto-render/pb-other.wav` создан с tempo-меткой 135.0 BPM.

## takaia_lubov_keys.wav — 2026-10-26

Аккордовая партия клавиш для плейбека (`pb-other`):
- Источник: `/Users/alex/Downloads/takaia_lubov_keys.wav` (16 bit / 44.1 kHz stereo `pcm_s16le`, 261.333 с от t=0; рендер обрезается на 245.333 с по `cut_after_last_cue: 2`).
- Фрейм **render**: тайминг соответствует линейке рендера от t=0 (вступление на такте 5.1 / 10.667 с по cue «chords in», финальный аккорд на такте 135.1 / 241.778 с по cue «end in»).
- Роль: `musical`, аккордовый подклад (не лид). Исходный уровень: пик −8.89 dBFS, gated RMS −23.62 dBFS (−21.2 LUFS). С учётом коридора громкости `pb-other` для аккордового аккомпанемента применён `"gain_db": -2.5` (уровень слоя −26.12 dBFS gated RMS / −23.7 LUFS; итоговый `pb-other.wav` — −24.78 dBFS gated RMS / −21.6 LUFS, пик −3.40 dBFS).

## takaia_lubov_bass.wav — 2026-10-26

Партия баса для плейбека (`pb-bass`, заменяет студийный Moises-стем `bass`):
- Источник: `/Users/alex/Downloads/takaia_lubov_bass.wav` (16 bit / 44.1 kHz stereo `pcm_s16le`, 261.333 с от t=0; рендер 245.333 с).
- Фрейм **render**: тайминг соответствует линейке рендера от t=0 (подъезд перед тактом 26 «drum fill ready go», паузы на «soft verse» такты 52–57 и на гитарном соло / 3-м куплете такты 94–110, вступление на «chorus in» такт 111.1, финальная нота Си на «end in» такт 135.1).
- Роль: `musical`, `"replaces": ["bass"]`. Исходный уровень: пик −1.43 dBFS, gated RMS −15.03 dBFS (−13.6 LUFS). Для попадания в коридор `pb-bass` программы 28.10 (−18.9..−20.7 dBFS gated RMS / −18.0..−19.9 LUFS) применён `"gain_db": -5.0` (итоговый `pb-bass.wav` — −20.04 dBFS gated RMS / −18.6 LUFS, пик −6.43 dBFS).
