# Пользовательский playback

## DJ_arp.wav — 2026-10-26

Партия синт-арпеджиатора от Alex:
- Источник: `/Users/alex/Downloads/DJ_arp.wav` (16 bit / 44.1 kHz stereo PCM, 236.571 с = 138 тактов при 140 BPM).
- Фрейм **render**: тайминг соответствует линейке рендера от `t=0` (`OFF = +2.798458 с` уже внутри файла; задержка огибающей относительно `wind.wav` на `OFF` равна `0 мс`).
- Тональность: оригинальная тональность трека (`pitch_semitones: 0`; корреляция хромы со сдвигом `0 st`: `0.828` по `wind`, `0.799` по `other`, `0.752` по `bass`).
- Содержимое: пульсирующий 16-ми синт-арпеджиатор в припевах и инструментальных/соло-секциях:
  - `72.54 – 127.20 с` (такты 41 – 72, Chorus 1 + Solo 1)
  - `149.69 – 203.88 с` (такты 86 – 117, Build-up / Chorus 2 + Solo 2)
  - `219.97 – 233.55 с` (такты 127 – 135, финальный блок `all in` до `end in`)
- Роль: `musical`. Исходный уровень: gated RMS `−25.02 dBFS` (stereo gated RMS `−22.49 dBFS`, `−19.6 LUFS`, пик `−6.71 dBFS`). С поправкой `"gain_db": 3.5` выходит на **medium-to-high** уровень актуального коридора `pb-other` программы 28.10: gated RMS **`−21.52 dBFS`** (stereo gated RMS `−18.99 dBFS`, `−16.1 LUFS`, пик `−3.21 dBFS`).
- `mix.json`:
  ```json
  "pb-other": {
    "layers": [
      {"file": "DJ_arp", "frame": "render", "gain_db": 3.5},
      {"file": "wind_part", "frame": "render", "gain_db": -8.0}
    ],
    "roles": {"DJ_arp": "musical", "wind_part": "musical"}
  }
  ```

## wind_part.wav — 2026-10-27

Партия духовых/свелл-пэда (`wind`) от Alex:
- Источник: `/Users/alex/Downloads/кислотный dj wind part.mp3` (48 kHz / 320 kbps stereo, 236.640 с; сконвертирован в 24 bit / 44.1 kHz stereo PCM `parts/wind_part.wav`).
- Фрейм **render**: тайминг соответствует линейке рендера от `t=0` (`OFF = +2.798458 с` внутри файла).
- Тональность: оригинальная тональность трека (`pitch_semitones: 0`).
- Содержимое: нарастающие духовые/синт-пэды на разгонах и в припевах:
  - `58.31 – 99.95 с` (такты `33 – 57`, разгон перед Chorus 1 + Chorus 1)
  - `149.16 – 179.27 с` (такты `86 – 103`, разгон + Chorus 2)
  - `219.46 – 233.77 с` (такты `127 – 135`, финальный блок `all in` до `end in`)
- Роль: `musical`. Исходный уровень (`0.0 dB`): gated RMS `−19.05 dBFS` (`−15.0 LUFS`, пик `−0.12 dBFS`). Понижен ещё на 4 дБ (с `−4.0` до `"gain_db": -8.0` → `−27.05 dBFS` gated RMS / `−23.0 LUFS`, пик `−8.12 dBFS`), чтобы на крещендо не спорить с `DJ_arp` (`−21.52 dBFS` gated RMS / `−18.99 dBFS` stereo gated RMS / `−16.1 LUFS`, пик `−3.21 dBFS`). Итоговый суммарный `pb-other.wav` — `−21.19 dBFS` gated RMS (`−18.96 dBFS` stereo gated RMS, пик `−2.36 dBFS`).
