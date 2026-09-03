---
type: pipeline
updated: 2026-09-03
title: YouTube-оригинал → только click + cues
---

# YouTube-оригинал → только click + cues (без плейбека)

Для песен, которые банда играет целиком живьём и хочет только клик и стартовый отсчёт в ухо (2026-09: Медведица, Кукла колдуна, Ту-лу-ла). Moises-стемов нет — сетку строим по оригиналу.

1. **Скачать оригинал:** `tools/yt-download.sh <url> audio` → `music/youtube/<title> [<id>].mp3`. Если yt-dlp отдаёт 403/age-gate — `yt-dlp --cookies-from-browser chrome …` с тем же шаблоном имени (yt-dlp из brew отстаёт от YouTube).
2. **bpm + сильная доля:** `uv run --with librosa --with numpy --python 3.12 python tools/jamzone/yt_bpm.py <mp3>` (скрипт: beat_track → кумулятивная индексация → lstsq bpm + фаза, остаток по 30-с окнам = дрейф; хрома-флакс mod 4 по сетке → индекс сильной доли; первая сильная доля ≥ первого звука). НЕ брать `tempo` из librosa напрямую — он квантован (две разные песни дали одинаковые 129.20).
3. **Папка песни:** `original.mp3` (копия), `metronome.wav` — синтетические клики (1 кГц, 20 мс) на константной сетке от первой сильной доли до конца файла, `mix.json`: `{"bpm": X, "pitch_semitones": 0, "pb-other": null, "pb-bass": null, "cues": [{"bar": 1, "text": "<Название> all in"}]}`.
4. `jamzone_render.py "<song>"` → `auto-render/click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3` (оригинал ложится на OFF; рендер сам добавляет lead-такт под фразу). Проверка: xcorr `all.wav` ↔ `original.mp3` = OFF; спаны cue: название в такте 1 (естественный темп, по концу), «all in ready go» по долям такта 2, вход на 1.1. Стартовый cue — стандартный (не `count: true`): пользователь явно попросил «название — пауза — all in ready go».
5. Дашборд: строка в `SETS` (`tools/setlist_dashboard.py`) → `songs.json`. Риг: папка `<Название>/` с `click.wav`+`cues.wav` руками (скрипт синка только перезаписывает существующие) + строка в `MAP` `sync_to_mainstage.sh`. Сет в MainStage заводит клавишник руками.

Дрейф живых записей (Кукла колдуна ±47 мс) в превью виден, для рига не важен — банда играет под константный клик.
