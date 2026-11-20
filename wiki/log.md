# log

Append-only хроника вики. Формат: `## [YYYY-MM-DD] <op> | <заголовок>`.

## [2026-10-28] cues & lyrics | Медведица (Мумий Тролль): добавлен cue stop на 3:03.69 (bar 98.3) и обновлён фонетический текст рэп-секции (клип 27)

1. В `music/songs/Мумий Тролль - Медведица/mix.json` добавлен 6-й cue:
   - `{"bar": 98, "beat": 3, "text": "stop", "abs_sec": 183.692, "snap_sec": 179.538}` (`03:03.692`) — «stop in 3 · 3 2 1» перед сольным вокальным затактом «Мерещится».
2. В `tools/lyric-launcher/lyrics-timed/27.tsv` (и `clips/27.ass`) обновлён пофразовый фонетический текст рэп-брейкдауна (`2:36.81–3:03.38`, такты 84–97).
3. Выполнен полный рендер (`jamzone_render.py "Мумий Тролль - Медведица"`), синхронизация с R2/Vercel (`tools/sync_site.py`), синк аудио в риг MainStage (`tools/sync_to_mainstage.sh --apply "Медведица"`, коммит `a0e657ce`) и доставка клипа `27` в риг (`lyric_workflow.py deliver 27 --apply`).

## [2026-10-28] mix | Мало тебя (SEREBRO): добавлены malo-guitars и malo-sfx в pb-other

1. Сконвертированы пользовательские дорожки из `/Users/alex/Downloads/`:
   - `/Users/alex/Downloads/malo-tebya-rhytm-guitars.mp3` → `music/songs/SEREBRO - Malo tebya/parts/malo-guitars.wav` (24 bit / 48 kHz stereo `pcm_s24le`, 227.136 с).
   - `/Users/alex/Downloads/malo-tebya-rhytm-sfx.mp3` → `music/songs/SEREBRO - Malo tebya/parts/malo-sfx.wav` (24 bit / 48 kHz stereo `pcm_s24le`, 227.136 с).
2. Настроены слои в `music/songs/SEREBRO - Malo tebya/mix.json`:
   - Фрейм: **`render`** (оба файла согласованы с линейкой рендера от t=0).
   - `malo-guitars`: тональность C# minor (уже в ключе группы, без питча); применен `"gain_db": -7.0` (роль `musical`), уровень полностью согласован с ритм-гитарой в «Ту-лу-ле» (пик −7.13 dBFS, RMS −19.79 dBFS).
   - `malo-sfx`: применен `"gain_db": -4.0` (роль `musical`), 4 регулярных свипа звучат с RMS −30.03 dBFS (аналогично «Солнцу» −30.3 dBFS); кульминационный разгон/сбивка со снейром на тактах 91–96 звучит на уровне микса с RMS −18.91 dBFS (пик −4.11 dBFS).
   - Итоговый `pb-other.wav`: пик −4.11 dBFS (запас по хедруму >4 dB, без клиппинга).
3. Выполнен полный рендер (`jamzone_render.py "SEREBRO - Malo tebya"`):
   - Пересобраны `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, стемы в `auto-render/stems/`.
   - Автоматически обновлен `web/songs.json` (`pb_other.available: true`, хэш `pb-other`: `f6f4ba4068`). Доступно для прослушивания через веб-дашборд (`http://localhost:5173`).

1. В `music/songs/Mr. Credo - Медляк/mix.json` уровень `pb-other` поднят на +4 dB:
   - `"gain_db": {"backing_vocals": 0.5, "keys": 0.5, "strings": 2.5}` (было `{"backing_vocals": -3.5, "keys": -3.5, "strings": -1.5}`).
   - Сырой пик микса `pb-other` (+2.17 dBFS) приведен хэдрум-нормализацией к −0.4 dBFS (`buf *= 0.95/pk`), итоговый уровень `auto-render/pb-other.wav` — **`−20.69 dBFS` gated RMS** (было `−22.07 dBFS`, пик `−0.4 dBFS`), в верхней зоне коридора `pb-other` программы 28.10 (рядом с `Кукла колдуна` `−20.70 dBFS`).
2. Выполнен полный рендер (`jamzone_render.py "Mr. Credo - Медляк" --practice`):
   - Пересобраны `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`.
   - Обновлен `web/songs.json` (хэш `pb-other`: `061cfbd97c`).
3. Синхронизировано в риг MainStage (`cherry-daddies-2000`):
   - Запущен `tools/sync_to_mainstage.sh --apply "Медляк"`: обновлены `cherry-daddies-setlist-2026-06-16/Медляк/pb-other.wav`, `28_10_2.concert/Playback/pb-other_2.wav` и резервные концерты.
   - Закоммичено и запушено в `origin/main` рига.

## [2026-10-27] cues | Кислотный DJ: обновлены подсказки на 1:37 (bar 56 drums-bass fill), 2:05 (bar 72 drum fill) и 2:20 (bar 81 drums-bass break)

1. В `music/songs/Кислотный DJ/mix.json` изменены 3 подсказки:
   - `bar 56.1` (`01:37.714`): `drums-bass break ready go` → `drums-bass fill ready go`
   - `bar 72.1` (`02:05.143`): `drum break ready go` → `drum fill ready go`
   - `bar 81.1` (`02:20.571`): `long break ready go` → `drums-bass break ready go`
2. Выполнен полный рендер (`jamzone_render.py "Кислотный DJ" --practice`): пересобраны `cues.wav`, `cue_preview.mp3`, `all.wav`, practice-миксы и обновлён `web/songs.json`.
3. Обновления синхронизированы в риг MainStage (`cherry-daddies-2000`: `cherry-daddies-setlist-2026-06-16/Кислотный DJ/` и бандлы `28_10_2.concert/Playback/`, `2000_1.concert/Playback/`).

## [2026-10-27] stage-video | Dark Cinema + Club 1920×640 Smart Hybrid (v6/v7): анти-засвет сцены и адаптивный формат 1920×640 для всех 27 клипов 28.10 Music Hall

1. Разработан пайплайн сценической стилизации задника (`tools/stage_dark_cinema.py`, PoC 5 стилей — `tools/stage_video_poc.py`) и метрики засвета сцены (средний линейный свет $\text{APL}_{\text{lin}}$, пиковый свет кадра, доля ярких пятен $Y>0.65$, паразитный белый свет).
2. Выбран и применён профиль **Dark Cinema (Natural Colors)** ко всем 27 синхронизированным с плейбеком клипам из `music/youtube/28.10-setlist/` → `music/youtube/28.10-setlist-dark-cinema/`:
   - локальный контраст (`CLAHE`) + пространственное подавление плоских белых фонов (небо, циклорама, белые стены);
   - отсечка глубоких теней в чистый `#000000`, плавный roll-off светов, овальная сценическая виньетка и экспо-лимитер анти-строб вспышек (потолок ~3.2–4.6% линейного света при исходных 30–100%);
   - сохранение родной цветовой палитры каждого клипа и 1:1 копирование синхронизированного аудио (`-c:a copy`).
3. Разработан конвейер под разрешение клубного экрана **`1920×640` (`3:1`) в режиме Smart Hybrid** (`tools/stage_club_1920x640.py`, выходная папка `music/youtube/28.10-setlist-1920x640/`):
   - автоматическая обрезка запечённых рамок (`ACTIVE_CROPS`) и адаптивный зум по категории исходника (`1860×640` для Cinema `2:1`, `1580×640` для `16:9 HD`, `1360×640` для `4:3 HD`, `1200×640` для `480p SD`, `1120×640` для квадратных обложек) со смещением вертикального кропа в верхнюю треть (`y_bias = 0.28..0.38`) и мягкой косинусной растушёвкой боковых границ в `#000000` (без логотипа).
4. Все 27 клипов `1920×640` выгружены в R2 под префиксом `cherry-daddies/videos/club-1920x640-v6/<id>.mp4` (а `16:9` Dark-версии — в `cherry-daddies/videos/dark-v6/<id>.mp4`); опубликованы витрины `https://releases.agentiqa.com/cherry-daddies/videos/index-v7.html` и `https://releases.agentiqa.com/cherry-daddies/videos/index-v6.html`.

## [2026-10-27] cues & playback | Медведица (Мумий Тролль): добавлены подсказки break in (2:35.08) и voice in (2:36.92), слой guitars_on_rap в pb-other (−5.5 dB, medium коридор)

1. В `music/songs/Мумий Тролль - Медведица/mix.json` добавлены 2 подсказки на рэп-брейкдаун (всего стало 5 cue):
   - `{"bar": 83, "text": "break in", "abs_sec": 155.077, "snap_sec": 151.385}` (`02:35.077`) — «break in ready go» по долям такта 82 перед началом брейкдауна (снятие лид-гитары и баса).
   - `{"bar": 84, "text": "voice in", "abs_sec": 156.923, "snap_sec": 153.231}` (`02:36.923`) — «voice in ready go» по долям такта 83 перед вступлением вокала («О, диги-диги...») на сильную долю `bar 84.1`.
2. В `pb-other` добавлен пользовательский гитарный слой `parts/guitars_on_rap.wav` из `/Users/alex/Downloads/медведица guitars on rap.mp3` (24-bit / 44.1 kHz stereo PCM, `frame: "render"` от $t=0$, оригинальная тональность `pitch_semitones: 0`, роль `musical`):
   - **Активный участок:** такты `90.4–98.4` (`169.47–184.40 с`, `02:49.5–03:04.4`) — фанковый ритм во второй половине рэп-секции (`bars 90.4–94.4`) и перегруженный разгон на распеве «О-о-о...» (`bars 95.1–98.4`) до входа финального припева на `bar 99.1`.
   - **Уровень громкости (`"gain_db": -5.5`):** исходный уровень файла (`0.0 dB`) — `−16.69 dBFS` gated RMS (`−16.02 dBFS` stereo gated RMS, `−12.0 LUFS`, пик `−0.13 dBFS`). С поправкой `"gain_db": -5.5` итоговый `auto-render/pb-other.wav` выведен в зону **medium** коридора `pb-other` программы 28.10 (рядом с `Медляк` `−22.07 dBFS`, `Ghostbusters` `−22.17 dBFS`, `Я буду` `−22.27 dBFS` и `Я устал` `−23.08 dBFS`): **`−22.19 dBFS` gated RMS** (`−21.52 dBFS` stereo gated RMS, **`−17.5 LUFS`**, пик `−5.63 dBFS`; ритм на рэпе `−26.48 dBFS`, разгон `−19.84 dBFS`).
3. Выполнен полный рендер (`jamzone_render.py "Мумий Тролль - Медведица"`): пересобраны `all.wav`, `click.wav`, `cues.wav`, `pb-other.{wav,mp3}`, `cue_preview.mp3`, `stems/*.mp3` и обновлён `web/songs.json`. Скопированы `cues.wav` и `pb-other.wav` в локальный риг MainStage (`tools/sync_to_mainstage.sh --apply --create-missing "Медведица"`).

## [2026-10-27] playback | Кислотный DJ: добавлен слой wind_part в pb-other (−8.0 dB, на 4 дБ тише прежнего)

1. Из `/Users/alex/Downloads/кислотный dj wind part.mp3` (48 kHz / 320 kbps stereo, 236.64 с) сконвертирован слой `music/songs/Кислотный DJ/parts/wind_part.wav` (24-bit / 44.1 kHz stereo PCM, `frame: "render"` от $t=0$, оригинальная тональность `pitch_semitones: 0`, роль `musical`):
   - **Активные участки:** такты `33–57` (`58.31–99.95 с`, разгон перед Chorus 1 + Chorus 1), такты `86–103` (`149.16–179.27 с`, разгон + Chorus 2) и такты `127–135` (`219.46–233.77 с`, финальный блок `all in` до `end in`).
   - **Баланс громкости (`"gain_db": -8.0`):** по запросу Alex ветер понижен ещё на 4 дБ (с `−4.0` до `"gain_db": -8.0` → **`−27.05 dBFS` gated RMS / `−23.0 LUFS`**, пик `−8.12 dBFS`), чтобы на крещендо не спорить с `DJ_arp` (`−21.52 dBFS` gated RMS / `−18.99 dBFS` stereo gated RMS / `−16.1 LUFS`, пик `−3.21 dBFS`). Суммарный `pb-other.wav` — **`−21.19 dBFS` gated RMS** (`−18.96 dBFS` stereo gated RMS, пик `−2.36 dBFS`).
2. Выполнен полный рендер (`jamzone_render.py "Кислотный DJ" --practice`, 22 cue), обновлены `pb-other.{wav,mp3}`, `all.wav`, `cues.wav`, `cue_preview.mp3`, `stems/*.mp3`, practice-миксы и `web/songs.json`.
3. Обновлённые файлы выгружены в R2 и задеплоены на сайт (`tools/sync_site.py`), синхронизированы в риг MainStage (`cherry-daddies-2000`) и запушены в оба репозитория.

## [2026-10-27] cues | Кислотный DJ: добавлены подсказки all in на 2:29.14 (bar 86.1) и stop in 3 3 2 1 на 3:37.71 (bar 126.1)

1. В `music/songs/Кислотный DJ/mix.json` добавлены 2 подсказки (всего стало 22 cue):
   - `{"bar": 86, "text": "all in ready go", "abs_sec": 149.143, "snap_sec": 145.714}` (`02:29.14`) — вступление полного бэнда (бас, клавиши, синт-арпеджиатор) на начало 2-го припева сразу после такта разгона `bar 85` (`build up ready go`).
   - `{"bar": 126, "text": "stop", "abs_sec": 217.714, "snap_sec": 213.857}` (`03:37.71`) — `stop in 3 · 3 2 1` на последний удар барабанов в конце разгона (`bar 124–125`) перед тактом паузы и финальным припевом `bar 127` (`all in ready go`, `03:39.43`).
2. Выполнен полный рендер (`jamzone_render.py "Кислотный DJ" --practice`): пересобраны `cues.wav`, `cue_preview.mp3`, `all.wav`, `pb-other.wav`, `pb-drums.wav`, practice-миксы (`alex`, `roma`, `steve`, `tanya`, `trio`) и обновлён `web/songs.json`.

## [2026-10-27] cues | Freed from Desire: убраны подсказки 1:47 piano in (bar 59) и 3:17 bass stop (bar 107)

1. В `music/songs/Gala - Freed from Desire/mix.json` удалены 2 подсказки:
   - `{"bar": 59, "text": "piano in"}` (107.907 с / 01:47.9)
   - `{"bar": 107, "text": "bass stop"}` (197.209 с / 03:17.2)
   Осталось 14 подсказок (включая секционные входы и финальный `end stop` на bar 114).
2. Выполнен полный рендер (`jamzone_render.py "Gala - Freed from Desire" --practice`): пересобраны `cues.wav`, `cue_preview.mp3`, `all.wav`, `pb-bass.wav`, `stems/*.mp3` и practice-миксы (`roma`, `steve`, `tanya`). Обновлён `web/songs.json`.
3. Обновления синхронизированы в риг MainStage (`cherry-daddies-2000`):
   - папка сетлиста `cherry-daddies-setlist-2026-06-16/10 Freed From Desire/cues.wav`
   - Playback-бандлы концертов `28_10_1.concert/Playback/`, `2000_1.concert/Playback/`, `2000_all.concert/Playback/` (`cues_9.wav`, `click_9.wav`, `pb-bass_6.wav`).

## [2026-10-26] playback | Кислотный DJ: добавлен синт-арпеджиатор DJ_arp в pb-other (+3.5 dB, medium-to-high коридор)

1. В `music/songs/Кислотный DJ/parts/DJ_arp.wav` добавлен пользовательский слой из `/Users/alex/Downloads/DJ_arp.wav` (16-bit / 44.1 kHz stereo PCM, 236.571 с = 138 тактов при 140 BPM):
   - **Фрейм и ключ:** фрейм `render` (от $t=0$, `OFF = +2.79846 с` уже внутри файла; лаг огибающей к `wind.wav` на `OFF` равен `0 мс`), оригинальная тональность (`pitch_semitones: 0`, корреляция хромы со сдвигом `0 st`: `0.828` по `wind`, `0.799` по `other`, `0.752` по `bass`).
   - **Активные секции:** такты 41–72 (`72.54–127.20 с`, Chorus 1 + Solo 1), такты 86–117 (`149.69–203.88 с`, Build-up / Chorus 2 + Solo 2) и такты 127–135 (`219.97–233.55 с`, финальный блок `all in` до `end in`).
   - **Уровень громкости:** исходный уровень файла (`0 dB`) — `−25.02 dBFS` gated RMS (`−22.49 dBFS` stereo gated RMS, `−19.6 LUFS`, пик `−6.71 dBFS`), что попадало в нижнюю (мягкую) зону коридора `pb-other`. С поправкой `"gain_db": 3.5` (роль `musical`) итоговый `auto-render/pb-other.wav` выведен в зону **medium-to-high** актуального коридора `pb-other` программы 28.10 (между средними `Медляк` `−22.07 dBFS` / `Ghostbusters` `−22.17 dBFS` и верхними `Кукла колдуна` `−20.70 dBFS` / `Ту-лу-ла` `−19.76 dBFS`): **`−21.52 dBFS` gated RMS** (`−18.99 dBFS` stereo gated RMS, **`−16.1 LUFS`**, пик `−3.21 dBFS`).
2. Выполнен полный рендер (`jamzone_render.py "Кислотный DJ" --practice`): собраны `pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `stems/*.mp3`, practice-миксы (`alex`, `roma`, `steve`, `tanya`, `trio`) и обновлён `web/songs.json`; удалён устаревший `auto-render/pb-bass.wav`.
3. Новый `pb-other.wav` скопирован в локальный риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кислотный DJ/pb-other.wav`).

## [2026-10-26] playback | Такая любовь: добавлен takaia_lubov_keys в pb-other (−2.5 dB) и takaia_lubov_bass в pb-bass (−5.0 dB)

1. Добавлены два пользовательских слоя в `music/songs/Такая любовь/parts/` (render-фрейм от $t=0$, 44.1 kHz / 16-bit stereo):
   - `takaia_lubov_keys.wav` — аккордовый клавишный подклад в `pb-other` (вступает на `bar 5.1` «chords in», завершается на финальном ударе `bar 135.1` «end in»). Исходный уровень: −23.62 dBFS gated RMS / −21.2 LUFS (пик −8.89 dBFS). Так как партия аккордовая (не ведущая), применён `"gain_db": -2.5` (уровень слоя −26.12 dBFS gated RMS / −23.7 LUFS; общий `pb-other.wav` — −24.78 dBFS gated RMS / −21.6 LUFS, пик −3.40 dBFS).
   - `takaia_lubov_bass.wav` — басовая дорожка в `pb-bass` (`"replaces": ["bass"]`). Исходный уровень: −15.03 dBFS gated RMS / −13.6 LUFS (пик −1.43 dBFS). Под коридор громкости `pb-bass` программы 28.10 (−18.9..−20.7 dBFS gated RMS / −18.0..−19.9 LUFS) применён `"gain_db": -5.0` (итоговый `pb-bass.wav` — −20.04 dBFS gated RMS / −18.6 LUFS, пик −6.43 dBFS).
2. Выполнен полный рендер (`jamzone_render.py "Такая любовь" --practice`), обновлены `pb-other.{wav,mp3}`, `pb-bass.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `stems/*.mp3`, practice-миксы и `web/songs.json`.
3. Обновлённые `pb-other.wav` и `pb-bass.wav` синхронизированы в риг MainStage (`cherry-daddies-2000`: папка сетлиста + бандлы `28_10_1.concert/Playback/` и `2000_1.concert/Playback/`), закоммичены и запушены в `origin/main`.

## [2026-10-26] playback | Ту-лу-ла: обновлён гитарный плейбек pb-guitars из `/Users/alex/Downloads/тулула guitars.mp3`

1. По запросу Alex обновлён пользовательский слой `parts/pb-guitars.wav` в `music/songs/Чичерина - Ту-лу-ла/` из `/Users/alex/Downloads/тулула guitars.mp3` (24-bit / 48 kHz PCM, render-фрейм, тональность −1 полутон C#/Db major; прежняя версия сохранена в `versions/2026-10-14-pb-guitars-v1/pb-guitars.wav`).
2. В новой версии финальное 3-е соло (такты 69–77, 128.6–143.8 с) сдвинуто на −62.5 мс раньше, чтобы вступление ложилось точно на сильную долю `bar 69.1` (128.649 с против 128.637 с сетки, +12.1 мс вместо прежних +74.6 мс); 1-е и 2-е соло без изменений.
3. Выполнен полный рендер (`jamzone_render.py "Чичерина - Ту-лу-ла" --practice`): пересобраны `pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `stems/*.mp3`, practice-миксы (`alex`, `roma`, `steve`, `tanya`) и `web/songs.json`.
4. В `tools/sync_to_mainstage.sh` исправлен выбор пути `.concert/Playback/` из `.cst` при наличии нескольких `file://` URL (теперь выбирается URL внутри `.concert/Playback/`, благодаря чему подхватываются `28_10_1.concert/Playback/pb-other_25.wav` и `cues_16.wav`). Обновлённый плейбек синхронизирован в риг MainStage (`cherry-daddies-2000`), закоммичен и запушен в `origin/main`.

## [2026-10-26] fix | Такая любовь: акустическая гитара убрана из pb-other после 2:59 (начало 3-го куплета)

1. Проблема: слой `acoustic-guitar-solo` в `pb-other` продолжал звучать после гитарного соло в начале 3-го куплета (такты 100–108, 179.6–194.8 с), где Алекс играет чистую гитару вживую.
2. Реализация:
   - В `tools/jamzone/jamzone_render.py` добавлена поддержка секции `mute` для пользовательских слоёв (`layers`) в плейбек-группах с 15 мс сглаживающим кроссфейдом.
   - В `music/songs/Такая любовь/mix.json` для `pb-other` настроен мьют: `"mute": {"acoustic-guitar-solo": [[100, 138]]}` (с такта 100 / 179.556 с / 02:59.556 до конца песни). Акустическая гитара звучит только на соло (такты 92–99).
3. Выполнен рендер (`jamzone_render.py "Такая любовь"`), обновлены `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, `web/songs.json`.
4. Свежие рендеры синхронизированы в риг MainStage (`cherry-daddies-2000`): обновлены `cherry-daddies-setlist-2026-06-16/Такая любовь/pb-other.wav` и бандлы `28_10_1.concert/Playback/pb-other_24.wav` / `2000_1.concert/Playback/pb-other_17.wav`, изменения закоммичены и запушены в `origin/main`.

## [2026-10-25] fix | Destination Calabria: выравнивание клика и стемов в ровный 4/4 на и после сакс-соло (cut_bars -0.710 с)

1. Причина сдвига клика: в оригинале (и в стемах JamZone) между тремя 2-тактовыми фразами сакс-соло (`Bars 65–70`) вставлены три лишние паузы по `1/8` (`0.235 с`), в сумме дававшие сдвиг `+1.5 доли` (`0.710 с`) к началу 2-тактового разгона (`132.256 с`), из-за чего в `01_Click.m4a` такт 71 обрывался через `1.5 доли` (`131.546 → 132.256 с`), а все последующие сильные доли съезжали относительно начальной сетки.
2. Решение (Вариант 1Б):
   - В `tools/jamzone/jamzone_render.py` расширен `cut_bars` для поддержки полудолевых точек (`"1&"`, `"2&"`) и раздельных срезов `click` / `stems`.
   - В `mix.json` вырезан полуторадольный сбой клика `[[71, 1], [71, "2&"]]` (`0.710 с`) и три восьмые паузы в музыкальных стемах (`[[67, 1], [67, "1&"]]`, `[[69, "1&"], [69, 2]]`, `[[71, 2], [71, "2&"]]`).
   - Сакс-соло от `sax solo in` (`Bar 65.1`) до `crash in` (`Bar 73.1`) стало ровным 8-тактовым квадратом в 4/4 (`128.01 BPM`, `max_resid = 8.4 мс`), все cue хвоста (`73 crash in`, `74 vocal in`, `75 all in`, `87 outro in`, `96 end stop`) стоят строго на Beat 1.
3. Полный ре-рендер выполнен (`--practice`), пересобраны титры `clips/06.ass` + `06.mp4` (`make_song_clip.py` учитывает `cuts` из `timeline.json`), обновлены веб и риг MainStage (`cherry-daddies-2000`).

## [2026-10-13] cues | Gimme! Gimme! Gimme!: добавлен cue «intro in ready go» на 02:56.3 (такт 87.1, вступление Outro)

1. По запросу Alex добавлен cue на сильную долю 87 такта: `{"bar": 87, "text": "intro in ready go", "abs_sec": 176.262, "snap_sec": 172.247}`.
2. 4-дольный отсчёт «intro in ready go» звучит на такте 86 (174.29s – 176.26s) поверх окончания припева и затакта клавиш, выводя группу точно на сильную долю Outro (аккорд Dm, крэш, синт-рифф). Всего в сетке 8 cues.
3. Выполнен рендер через `jamzone_render.py`, обновлённый `cues.wav` синхронизирован в риг MainStage (`cherry-daddies-2000`).

## [2026-10-13] fix | Gimme! Gimme! Gimme!: cue chorus in на 69.3 (+2 доли), продление Outro до такта 99 (финальный хит)

1. Сдвиг cue припева: `chorus in ready go` перенесён с сильной доли 69.1 на 3-ю долю такта (`bar 69, beat 3`, 141.142s, ровно на 2 доли позже). Теперь отсчёт «chorus in ready go» завершается ровно перед вокальным вступлением Тани «Gimme! Gimme! Gimme!», которое начинается на 3-й доле такта 69.
2. Продление Outro и адаптация финала:
   - Ранее плейбек гасился через `fade_out` на такте 97, обрывая главную клавишную тему Outro на середине квадрата.
   - Главная тема Outro теперь звучит полностью до конца — до сильной доли 99 такта (199.942s / ~03:20 в рендере, что соответствует финальному крэшу и аккорду Dm на даунбите оригинального такта 145).
   - Финальный cue `end in 3 · 3 2 1` перенесён на `bar 99.1` (199.942s).
   - Затухание плейбека `fade_out` адаптировано под такт 99: с 99.1 до 99.3 (1.01 с рампа после финального удара банды).
3. Полный рендер выполнен, обновлены `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav`, синхронизированы в риг MainStage (`cherry-daddies-2000`).

## [2026-10-13] fix | Gimme! Gimme! Gimme!: долевой срез [[86, 3], [132, 3]] для сохранения затакта темы Outro

1. Проблема: при `cut_bars: [87, 133]` главная клавишная тема Outro (`11_Synth_Lead`, D-F-A-D) начиналась с обрезанным затактом, так как в оригинале её 2-дольный разбег звучит на 3-й и 4-й долях такта 132 (`265.42s`), которые срезались даунбитом 133.
2. Реализация:
   - В `tools/jamzone/jamzone_render.py` добавлена поддержка долевых срезов (`cut_bars: [[from_bar, from_beat], [to_bar, to_beat]]` и через dict).
   - В `mix.json` срез настроен как `cut_bars: [[86, 3], [132, 3]]`: склейка перенесена ровно на 3-ю долю такта.
   - Длина среза — ровно 184 доли = 46.0 целых тактов 4/4 (сетка клика осталась строго 4/4 без фазовых сдвигов).
   - Затакт главной клавишной темы Outro теперь звучит полностью (доли 3 и 4 такта 86/132), плавно выходя на сильную долю 133 и запуск полного синт-риффа.
3. Рендеры пересобраны и скопированы в риг MainStage (`cherry-daddies-2000`). Субтитры и видео (`clips/47.{ass,mp4}`) пересобраны.

## [2026-10-13] fix | Tina Turner — The Best: возврат всех 5 гитар в плейбек (pb-other) во всей песне

1. Все 5 гитар (`04_Acoustic_Guitar_(clean)`, `05_Rhythm_Electric_Guitar_(muted)`, `06_Rhythm_Electric_Guitar`, `07_Arr._Electric_Guitar`, `08_Distorted_Electric_Guitar`) возвращены в `pb-other.stems` на протяжении всей песни (без мьютов).
2. Выполнен полный рендер (`jamzone_render.py "Tina Turner - The Best" --practice`): обновлены `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, practice-миксы, web-стемы, обновлён `web/songs.json`.
3. Синхронизированы свежие `pb-other.wav` и `cues.wav` в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/The Best/`).

## [2026-10-13] fix | Gimme! Gimme! Gimme!: Вариант А — срез перенесён на [87, 133] (полное устранение вокальных срезов)

1. Проблема на 02:19: при `cut_bars: [69, 117]` на сильной доле припева происходил срез между Pre-chorus 2 и Chorus 4. Слово *«prayer»* обрывалось на полуноте (оно звучит до 1-й доли такта 69), а припев из такта 117 врывался сразу на первой доле без 2-дольной паузы, из-за чего припев казался начавшимся на 2 доли раньше времени.
2. Реализация Варианта А (`cut_bars: [87, 133]`):
   - Блок Verse 2 $\to$ Pre-chorus 2 $\to$ Chorus 2 (такты 53–76) звучит **100% непрерывным студийным дублем** без единого среза.
   - За ним звучит Chorus 3 (бэк-вокалы, такты 77–86), где вокал полностью завершается.
   - Срез перенесён на такт 87 (`174.341s` $\to$ `266.401s`, такт 133 Outro), в зону **полной тишины вокала**: вырезано инструментальное соло (флейта/синт, 24 такта), повтор предприпева 3 и припева 4/5.
   - Трек с такта 87 бесшовно переходит в нативное Outro (такт 133, синт-рифф) и финальный хит.
   - Длина трека: 205.47 с (102 такта, 3:25). Внутри вокальных секций больше нет ни одной склейки.
3. Подсказки и тайминги:
   - Все 7 cues в `mix.json` сохранили свои номера тактов: `chorus in ready go` на 69.1 (140.132s), `end in 3 · 3 2 1` на 97.1 (196.002s, fade out 2 доли).
   - В `tools/lyric-launcher/lyrics-timed/47.tsv` актуализированы тайминги строк предприпева и припевов, пересобраны `clips/47.ass` и `clips/47.mp4`.
   - Рендеры обновлены и скопированы в риг MainStage (`cherry-daddies-2000`).


## [2026-10-12] fix | Gimme! Gimme! Gimme!: перенос cut_bars на [69, 117] (исправление обрыва вокала куплета 2)

1. Проблема: `cut_bars: [63, 111]` вырезал `Pre-chorus 2` и прыгал в `Pre-chorus 3`. Срез на сильную долю такта 63 (`126.101s` в стэмах, `02:08.04` в рендере) обрывал последнее слово Verse 2 (*«sight»*), которое звучит на 1-й доле такта 63, и срезал 2-дольную паузу/вдох перед предприпевом.
2. Решение: срез перенесён на 6 тактов — `cut_bars: [69, 117]`:
   - Verse 2 (такты 53–62) теперь непрерывно и без срезов переходит в нативный Pre-chorus 2 (такты 63–68): слово *«sight»* звучит полностью, сохраняется естественный вдох на доле 2, предприпев звучит с оригинальным балансом и фразировкой.
   - Склейка перенесена на сильную долю припева (такт 69 $\to$ такт 117, `Chorus 2` $\to$ `Chorus 4`), оба с крэшем и вступлением *«Gimme!»*.
   - Длина вырезки сохранена: ровно 48 тактов (96.31 с), длина трека прежняя (201.18 с, 3:21).
   - Подсказки сохранили свои такты: `chorus in ready go` на 69.1 (140.132s), `end in` на 97.1 (195.712s).
3. Синхронизация:
   - Выполнен перерендер через `jamzone_render.py`, обновлены файлы в `auto-render/` и скопированы в риг MainStage (`cherry-daddies-2000`).
   - В `tools/lyric-launcher/lyrics-timed/47.tsv` скорректирован тайминг строки предприпева (`2:08.92`), пересобраны `clips/47.ass` и `clips/47.mp4` и скопированы в риг (`lyrics/clips/`).
   - Обновлены `wiki/songs/abba-gimme-gimme-gimme.md` и `wiki/index.md`.


## [2026-10-12] feat | Felicità: добавлен cue «chorus in» на второй припев (~2:22)

1. В `music/songs/Al Bano & Romina Power - Felicità/mix.json` добавлен cue для второго припева:
   - `bar 63.4` (142.188 с, `snap_sec: 137.727`) — `chorus in ready go` на 4-ю долю такта под затакт вокала «Sen-ti» (согласно правилу CLAUDE.md для вокала из-за такта и аналогично 1-му припеву `bar 29.4`).
2. Выполнен локальный рендер через `tools/jamzone/jamzone_render.py "Felicità" --practice`, обновлены рендеры в `auto-render/` (`cues.wav`, `cue_preview.mp3`, `all.wav`, `practice-*.mp3`), обновлён `web/songs.json`.
3. Обновлены страницы `wiki/songs/al-bano-romina-power-felicita.md`, `wiki/index.md` и `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-12] feat | Gimme! Gimme! Gimme!: затухание плейбека (fade_out) после финального удара

1. В `music/songs/ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)/mix.json` добавлено затухание на 2 доли после финального удара:
   ```json
   "fade_out": {
     "from_bar": 97,
     "from_beat": 1,
     "to_bar": 97,
     "to_beat": 3
   }
   ```
2. Финальный удар банды приходится на такт 97.1 (195.642 с, cue `end in 3 · 3 2 1`). Рампа затухания длится ровно 2 доли (1.01 с, 195.642 с → 196.647 с), после чего плейбек (`pb-other`, `pb-drums`, `all`) полностью замолкает.
3. Выполнен локальный рендер (`jamzone_render.py "ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)"`), обновлены файлы в `auto-render/` и скопированы в MainStage (`cherry-daddies-setlist-2026-06-16/Gimme! Gimme! Gimme!/`).


## [2026-10-12] feat | Такая любовь: добавлен слой acoustic-guitar-solo в pb-other

1. Добавлен пользовательский слой акустической гитары:
   - Исходник `/Users/alex/Downloads/acoustic guitar on solo pb.mp3` сконвертирован в `music/songs/Такая любовь/parts/acoustic-guitar-solo.wav` (frame `render` от t=0, длительность 245.4 с).
   - Звучит во время гитарного соло: 165.2 – 194.8 с (такты ~92 – 108).
   - Роль `musical` (пик −0.2 dBFS, уровень сохранён из Logic Pro).
2. Включён в `pb-other`:
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
3. Выполнен полный рендер (`jamzone_render.py "Такая любовь"`), обновлены `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, `web/songs.json`.
4. Свежий `pb-other.wav` синхронизирован в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/pb-other.wav`).

## [2026-10-12] fix | Такая любовь: обновление слоя sfx-pb в pb-other

1. Обновлён файл слоя `sfx-pb` из `/Users/alex/Downloads/sfx pb.mp3` (баунс из Logic Pro, 135.168 с от такта 35 / 64.0 с).
2. Сконвертирован в `music/songs/Такая любовь/parts/sfx-pb.wav` с точным выравниванием на сетку рендера (lead 64.0 с до такта 35, frame `render`). Доработаны эффекты вокруг гитарного соло перед переходом в solo leak (такты 93–97).
3. Выполнен полный рендер (`jamzone_render.py "Такая любовь"`), авто-уровень роли `fx` (−21.1 dBFS, gain −8.9 dB до потолка −30 dBFS).
4. Обновлены `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, `web/songs.json`.
5. Свежий `pb-other.wav` синхронизирован в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/pb-other.wav`).

## [2026-10-12] cues | Такая любовь: добавлен cue «solo leak ready go» на 00:02:54.222 (такт 97)

1. Добавлен cue: `{"bar": 97, "text": "solo leak ready go", "abs_sec": 174.222, "snap_sec": 170.667}`.
   - Позиция: 00:02:54.222 (174.222 с) = даунбит такта 97 (tempo 135 bpm, beat 0.4444 с).
   - 4-дольный отсчёт «solo leak ready go» звучит на долях такта 96 (слова на долях 1, 2, 3, 4 перед событием такта 97.1).
2. Выполнен полный рендер (`jamzone_render.py "Такая любовь"`), обновлены `cues.wav`, `cue_preview.mp3`, `web/songs.json`. Всего 14 cue.
3. Обновлённый `cues.wav` синхронизирован в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/cues.wav`).

## [2026-10-11] fix | Такая любовь: бэк-вокал убран из pb-other/pb-other-keys, добавлен слой sfx-pb в pb-other

1. Из `pb-other` убран стем `backing_vocals` (остался `strings`).
2. Из альтернативного `pb-other-keys` (вариант без клавишника) также убран `backing_vocals` (остались `strings` и `keys`).
3. Добавлен пользовательский слой sound fx:
   - Исходник `/Users/alex/Downloads/sfx pb.mp3` сконвертирован в `music/songs/Такая любовь/parts/sfx-pb.wav` (frame `render`, длительность 245.4 с).
   - Включён в `pb-other`: `layers: [{"file": "sfx-pb", "frame": "render"}]`, `roles: {"sfx-pb": "fx"}` (gated RMS −21.5 dBFS с авто-выравниванием до потолка −30 dBFS, gain −8.5 dB).
4. Выполнен полный рендер (`jamzone_render.py "Такая любовь"`): обновлены `pb-other.wav`, `pb-other.mp3`, `pb-other-keys.wav`, `pb-other-keys.mp3`, `web/songs.json`.
5. Свежие плейбеки (`pb-other.wav`, `pb-other-keys.wav`, а также актуализированные `cues.wav` и `pb-bass.wav`) скопированы в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Такая любовь/`).


## [2026-10-11] fix | Tina Turner — The Best: полное удаление всех гитар из плейбека (pb-other)

1. Все 5 гитар (`04_Acoustic_Guitar_(clean)`, `05_Rhythm_Electric_Guitar_(muted)`, `06_Rhythm_Electric_Guitar`, `07_Arr._Electric_Guitar`, `08_Distorted_Electric_Guitar`) полностью удалены из `pb-other` (включая секцию Instrumental; Алекс играет все гитары вживую).
2. Секция `mute` в `pb-other` удалена.
3. Выполнен полный рендер (`jamzone_render.py "Tina Turner - The Best"`): обновлены `pb-other.wav`, `pb-other.mp3`, `all.wav`, `cue_preview.mp3`, `stems/`, `web/songs.json`.
4. Синхронизирован `pb-other.wav` в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/The Best/pb-other.wav`).

## [2026-10-11] fix | Stumblin' In: intro guitar tone guidance + сдвиг вокального cue на bar 1 beat 3

1. Поддержка гитарного/аудио-тон гайданса в `tools/jamzone/jamzone_render.py` через `tone_clip` (файл) и `tone_beats` (6 долей).
2. Стартовый cue `Stumblin In vocal in`:
   - Добавлен intro guitar riff `stumbling cue tone.mp3` на 6 долей (`bar -1.1`..`bar 0.3`).
   - Порядок воспроизведения: сначала войсовер «Stumblin In», затем звучит гитарный тон, затем отсчет «vocal in ready go».
   - Событие «vocal in» сдвинуто на полдоли вправо: с `bar 1.2&` на `bar 1.3` (слово «go» звучит на `bar 1.2`, аккуратно перед вокальным затактом).
3. Рендер автоматически добавил +1 count-in такт для чистого размещения войсовера и тона (`lead: +1 bar(s)`).
4. Выполнен полный рендер (`jamzone_render.py "Suzi Quatro & Chris Norman - Stumblin' In" --practice`), обновлены `auto-render/*`, `mix.json`, `web/songs.json`.

## [2026-10-10] fix | Tina Turner — The Best: правки cue, мьют гитар вне Instrumental, саксофон убран из pb-other

1. Саксофон `12_Tenor_Saxophone` удалён из `pb-other` (партия играется вживую).
2. Все 5 гитар в `pb-other` (`04`..`08`) заглушены вне секции Instrumental (`mute: [[1, 82], [90, 115]]`). В секции Instrumental (такты 82–89) гитары в плейбеке звучат.
3. Cue саксофонного соло передвинут с `bar 82.1` на `bar 81 beat 3&` (188.51с) под точную первую ноту саксофона (188.54с).
4. Cue припева передвинут на 1 долю раньше: `bar 90.1` → `bar 89 beat 4` (207.24с) под вокальный затакт.
5. Финальный cue `end in` передвинут с ошибочного `bar 98.1` на `bar 106.1` (244.79с, ~4:05), где звучит финальный аккорд/хит банды.
6. Выполнен полный рендер (`jamzone_render.py "Tina Turner - The Best"`).

## [2026-07-10] init | Схема и каркас вики

Заведена вики по Karpathy LLM-wiki паттерну. Решения: скоуп — весь бэнд-опс (песни+гиги+контент+риг), живёт в репо `wiki/`, линки — стандартный markdown (GitHub-читаемо). Схема: `wiki/SCHEMA.md`.

## [2026-07-10] ingest | Первичное наполнение (seed): 24 песни + 7 пайплайнов + 4 людей + 1 гиг + 3 контента

Параллельный сид 32 агентами из источников репо (mix.json, git-история, docs/plans, память агента). Заведён index.md. Открытые противоречия зафиксированы в секциях «Открытое» страниц (см. в т.ч. Beverly Hills бас, Infinity players, No Stress A4/A#4, Mr. Saxobeat «alex vocal in»).

## [2026-07-22] ingest | Беги от меня: полный cue-сет + синк в риг

Новая страница [begi-ot-menya](songs/begi-ot-menya.md) (+ index tryout-секция). 16 cue: старт передвинут на пикап-долю синт-риффа (bar 1 beat 0), остальные позиции — таймстемпы пользователя из Logic. Ключевая находка: его фрейм = нетримленные оригиналы Moises (−8.8с фронт-трима), а сырой индекс клика метронома завышает долю на 2 (варп-даунбит на клике #2) — mapping «клик k = доля k−2» сверен по кик-входу и всем 12 точкам (±50мс на кликах). Риг: только cues.wav (click/pb побайтно те же), коммит в риге не запушен.

## [2026-09-02] fix | Беги от меня: баг фазы варпа → пере-варп, cue перенумерованы, риг обновлён

Пользователь заметил обрезанное начало и сдвиг `moises-orig/keys` относительно `all.wav`. Причина — `jamzone_warp_ext.py`: фаза константной сетки = медиана по всем кликам; при дрейфе +700 → −520 мс варп выбросил первые 700 мс всех стемов, рендер взял клик 2 за такт 1.1 (акцент клика на 3-й доле, все cue на «beat 3»). Фикс инструмента: фаза от старта (dev(0)=0), хвост удлиняется. Пере-варп из `moises-orig/`, cue → на «1» (`bar N.3` → `N+1.1`), рендер = старый +0.96с, синк в риг (cues/pb-other/pb-bass/pb-drums; click тот же), риг-коммит `0cc4f838` не запушен. Страница [begi-ot-menya](songs/begi-ot-menya.md) переписана (правило «k−2» отменено), [moises-import](pipelines/moises-import.md) — примечание про фазу. Побочно: Eva 2.0 тем же багом потеряла 50 мс тишины до первого клика (музыка цела), Солнышко не задето.

## [2026-09-02] fix | Такая любовь: студийный бас после финального удара убран из pb-bass

Бас в pb-bass продолжал фразу с 136.1 в 2-тактовом хвосте `cut_after_last_cue` — после того, как банда остановилась на «end in» 135.1. Штатный `mute` группы: `"pb-bass": {"mute": {"bass": [[135.5, 138]]}}`; удар на 135.1 цел, файл побайтно тот же до 242.6с. В риг ушёл только `pb-bass.wav` (коммит `75b7a5fc`, запушен). Заведена страница [takaya-lyubov](songs/takaya-lyubov.md) (её не было). Попутно: пуш рига с Беги (`0cc4f838`) прошёл после освобождения портов (17 тыс. TIME_WAIT в системе); у основного репо remote не настроен — коммиты локальные.

## [2026-09-03] ingest | Tryout: Медведица, Кукла колдуна, Ту-лу-ла — click + стартовый cue

Три новые песни без плейбека: оригиналы с YouTube (yt-dlp с куками Chrome — brew-версия отдаёт 403/age-gate), bpm по lstsq на beat-треке librosa (130.0 / 148.6 / 130.6), синтетический `metronome.wav` от первой сильной доли (хрома-флакс mod 4), один cue `bar 1` + `count: true` («<Название> in 3» + 3 2 1). Рендер click/cues/all/cue_preview, дашборд «НА ПРОБУ», в риге папки с click+cues (`eb9b74f6`), MAP синка дополнен; сеты в MainStage заводятся руками. Новый пайплайн-page [youtube-click-only](pipelines/youtube-click-only.md).

## [2026-09-03] fix | Tryout-тройка: стартовый cue → стандартный «<Название> … all in ready go»

По правке пользователя: не `count: true` («in 3» + 3 2 1), а обычный стартовый cue — название естественным темпом в такте 1, «all in ready go» по долям такта 2, вход на 1.1. Геометрия рендера та же (click побайтно тот же), в риг ушли только `cues.wav` (`f7b647ec`). Страницы песен, index и [youtube-click-only](pipelines/youtube-click-only.md) поправлены.

## [2026-09-03] ingest | Tryout: Rock & Roll Queen (The Subways) — click + стартовый cue

Тем же пайплайном [youtube-click-only](pipelines/youtube-click-only.md). Гоча: `beat_track` без приора трекал половину долей (197 на 170 с), с `start_bpm` и hop 128 — 400 долей, но темп живой (138–145 по окнам), lstsq по всей песне 141.0 → взято 141. Сильная доля по кик/хрома mod 4 на трекнутых долях (не на константной сетке — она теряет фазу на плывущем темпе). Риг `55091574`, дашборд «НА ПРОБУ» (34 песни).

## [2026-09-11] ingest | Tryout: Pretty Fly (For A White Guy) (The Offspring) — Moises stems + click + cues + pb-drums + backing vocals

Импорт из архива Moises (143 bpm, B minor): выравнивание через `jamzone_warp_ext.py` (`--bpm 143 --downbeat 1`), интро 3 такта отрезано под вход барабанов.
Настроен `mix.json`: стартовый cue (`Pretty Fly drums in`), `pb-other` (backing vocals, auto-leveled до -23 dBFS), `pb-drums` (drums для репетиций), бас живой (Roma).
Сгенерирован полный авто-рендер (click, cues, pb-other, pb-drums, all, cue_preview, pb-drums.mp3, practice-миксы). Песня добавлена в дашборд («НА ПРОБУ», 35 песен).

## [2026-09-11] ingest | Tryout: Медляк (Mr. Credo) — Moises stems + click + cues + pb-drums + pb-other + pb-bass

Импорт из архива Moises (105 bpm, G minor): выравнивание через `jamzone_warp_ext.py` (`--bpm 105.0`), дрейф минимальный (0–36 мс).
Настроен `mix.json`: `pb-other` (backing_vocals + strings), `pb-other-keys` (+keys), `pb-drums`, `pb-bass`.
3 cue: `Медляк synth in` на 1.1, `drums in` на 9.1 (вход барабанов и баса), `verse in` на 17.1 (куплет).
Сгенерирован полный авто-рендер, песня добавлена в дашборд («НА ПРОБУ», 36 песен).

## [2026-09-11] ingest | Tryout: Кукла колдуна (Король и Шут) — Moises stems + click + cues + pb-drums + pb-other (strings скрипка)

Импорт из архива Moises (148.6 bpm, D minor): замена старого youtube-click-only на полный набор стемов.
Выравнивание через `jamzone_warp_ext.py` (`--bpm 148.6`), сетка сведена с плавающей живой записью 1999 года.
Настроен `mix.json`: `pb-other` (backing_vocals + strings со скрипичной темой), `pb-other-keys` (+keys), `pb-drums` (барабаны для репетиций), бас живой (Roma).
3 cue: `Кукла колдуна all in` на 1.1, `drums in` на 8.1 (вход ударных и полного бэнда), `verse in` на 17.1.
Сгенерирован полный авто-рендер со всеми practice-миксами, дашборд обновлён.

## [2026-09-12] tune | Pretty Fly (For A White Guy): транспонирование на 1 тон вниз (B minor → A minor, pitch_semitones: -2)

По запросу группы песня переведена на 1 тон ниже оригинала (B minor → A minor, `"pitch_semitones": -2` в `mix.json`).
Выполнен полный перерендер (`jamzone_render.py` с флагом `--practice`):
- `all.wav`, `pb-other.wav` (бэк-вокал), а также мультитрековые стемы (`auto-render/stems/`) и practice-миксы для участников (`alex`, `roma`, `steve`, `tanya`) спитчены на -2 полутона через Rubberband R3 `-3 -F` с сохранением формант;
- `pb-drums.wav` и барабанный стем оставлены без питча;
- Сетка, клик и стартовый cue («Pretty Fly drums in») не изменились;
- Риг MainStage синхронизирован через `sync_to_mainstage.sh --apply "Pretty Fly"`.

## [2026-09-12] fix | Кукла колдуна: исправление плавающего строя скрипки (варпинг через RubberBand timemap вместо varispeed-интерполяции)

- Обнаружено, что наивный линейный ресемплинг (`np.interp`) в `jamzone_warp_ext.py` при выравнивании живой записи 1999 года (дрейф сетки до 270 мс) работал как ленточный вариспид: локальная скорость менялась на ±3.5–4%, вызывая девиацию питча скрипки от -60 до +62 центов (больше полутона размаха!).
- `tools/jamzone/jamzone_warp_ext.py` модернизирован: для всех аудиостемов теперь используется `rubberband` (CLI R2 с посекундным `--timemap`), сохраняющий исходную высоту тона независимо от локальных сжатий и растяжений темпа. Метроном остаётся на линейной интерполяции для сохранения импульсных атак клика.
- Скрипт теперь автоматически поддерживает повторный варп из папки `moises-orig/` без необходимости ручного переноса файлов.
- Все стемы переварплены из `moises-orig/` и заново отрендерены через `jamzone_render.py --practice` (включая `pb-other.wav`, `pb-other-keys.wav`, мультитрековые стемы и practice-миксы).
- Риг MainStage синхронизирован через `sync_to_mainstage.sh --apply "Кукла колдуна"`.

## [2026-09-12] feat | Интерактивный мультитрековый микшер на дашборде (100% песен репертуара)

- В `jamzone_render.py` добавлен параллельный экспорт выровненных mp3-стемов (vocal, back_vox, drums, keys, bass, guitars, other, click, cues) в `auto-render/stems/`.
- Выполнен экспорт стемов для всех 37 песен всех сетов (СЕТ 1, СЕТ 2, НА БИС, НА ПРОБУ, АРХИВ).
- В `web/index.html` реализован Web Audio мультитрековый плеер со строгим каноническим порядком дорожек и независимым мгновенным мьютом/анмьютом на лету (с сохранением состояния в `localStorage`).

## [2026-09-24] cues | Медведица: 3 cue на интро + ренейм вкладки «28.10 new songs»

- По запросу группы в `Мумий Тролль - Медведица/mix.json` настроены 3 подсказки:
  1. `bar 1.1` (3.692 с): `Медведица drums in` («Медведица» в lead-такте + «drums in ready go»);
  2. `bar 3.1` (7.385 с): `all in` («all in ready go» на 4 долях такта 2, вступает гитара и банда);
  3. `bar 19.1` (36.923 с): `verse in` («verse in ready go» на 4 долях такта 18, сильная доля перед входом вокала «В слезах парнишка...»).
- Исправлен баг отсутствия `abs_sec` для Медведицы (многострочный JSON мешал регулярке `is_cue` в `jamzone_render.py`).
- Полный перерендер: обновлены `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3` и стемы.
- Секция «НА ПРОБУ» / «New» в дашборде и сетлисте переименована в «28.10 new songs». `web/songs.json` обновлён.
- Настроен `tools/sync_site.py` и `tools/r2_upload_mixes.cjs`: 410 файлов мультитреков залиты в Cloudflare R2 (`cherry-dash/<slug>/stems/`), деплой на Vercel Production.

## [2026-09-29] analysis | Rock & Roll Queen: JamZone-клик тоже переменный

По запросу Alex извлечены 7 HQ-стемов cat_67531 в `music/songs/The Subways - Rock and Roll Queen/`. Измерены 377 импульсов исходного `01_Click.m4a`: precount ~155.28 BPM, вступление/первый куплет ~144, припевы ~139.4–139.6, финальные 10 с ~146.05; 141 в метаданных — номинальный темп. Переменность подтверждена несколькими RMS-порогами и независимым измерением максимумов волн (расхождение интервалов <0.046 мс). Сохранена CSV импульсов, дополнена [страница песни](songs/rock-and-roll-queen.md). Текущий YouTube-рендер и риг ещё не переключены: сырой JZ требует follow-сетки, строго ровные 141 — общего варпа стемов. Исправлено прежнее предположение в разговоре, что JamZone автоматически даст ровную версию.

## [2026-09-29] render | Rock & Roll Queen: ровный JamZone-плюс + клик 141 для репетиций

По подтверждению Alex применён метод «Куклы колдуна»: шесть музыкальных стемов через общую сглаженную карту RubberBand R2, pitch сохранён. Быстрый JZ-precount удалён; новый ровный клик и стандартный стартовый cue, музыка на 3.404 с. Версия `The Subways - Rock and Roll Queen/warped-141-v1/`, рецепт `analysis/warp_141_v1.py`; канонический рендер в папке с `&` обновлён, прежний целиком сохранён в `youtube-before-jamzone-2026-09-29/`. Клик 140.999997 BPM (остаток <0.303 мс), барабанный выход следует карте с лагом 2–6 мс в 11 окнах по песне. Плюс `all.wav`, плюс+клик+cue `cue_preview.mp3`, раздельные stems. Локальный дашборд обновлён, аплоада нет. Sync рига dry-run: click/cues уже побайтно идентичны, копирование не требуется.

## [2026-09-29] cues | Rock & Roll Queen: pb-other, живой бас Ромы, 4 cue

По указаниям Alex: pb-other = `06_Backing_Vocals` + `05_Lead_Electric_Guitar`, бас живой (Рома на гитаре), `players.roma = [03_Bass]`. Cue: 1 guitar in, 13 all in (первый припев), 69 solo in (Break), 77 chorus in (выход из Break). Точки сверены через исходную структуру/клики и warp-map, активность lead guitar подтверждает такты 69–76. Полный рендер + practice Ромы без баса; pb-other проверен как точная сумма двух назначенных стемов. Версия сохранена в `The Subways - Rock and Roll Queen/arrangement-v2/`; локальный web отдаёт новый плюс, cue и practice. В риг синхронизирован cues.wav; нового pb-other там пока нет, подключение в MainStage вручную.

## [2026-09-29] cues | Rock & Roll Queen: Verse 2/3 и guitar only после Chorus 2

Добавлены 3 cue по структуре JamZone/warp-map: bar 33 Verse 2 (57.872 с) «verse in ready go»; bar 57 Intro 3 после Chorus 2 (98.723 с) «guitar only ready go» (полный текст + raw:true); bar 61 Verse 3 (105.532 с) «verse in ready go». Всего 7 cue. Пересобраны плюс/прослушка pb-other/practice Ромы/стем cues, проверены актуальные HTTP-файлы локального web; cues.wav синхронизирован в риг. Версия сохранена как `The Subways - Rock and Roll Queen/arrangement-v3/`.

## [2026-09-29] cues | Ту-лу-ла: 10 cue и укороченный финал

По заданию Alex измерены события по уже имевшимся Moises-WAV: drums 1.1, guitar 4.4, verse 13.1, solo 32.4, verse 41.1, drums only 51.1, all 53.1, keep going (фраза около 2:00, точка 65.1), solo 68.4, end 77.1 / 2:23.338. Alex отдельно выбрал обрезать оригинальный хвост после финального удара: fade +80…260 мс, последующие музыкальные WAV обнулены, один такт хвоста клика. Старые источники/рендер в `versions/2026-09-29-before-cues-v1/`, новый в `versions/2026-09-29-cues-v2/`, рецепт `analysis/ending_v2.py`. Проверены сохранность PCM до fade, тишина после, все 10 cue и текущие HTTP-файлы web. Пересобраны все четыре practice; в риг синхронизированы click/cues/pb-drums. Восстановлены отсутствовавшие ~/1,2,3.aiff из идентичных по PCM копий Logic-проектов. Страница песни обновлена: прежнее описание YouTube-click-only уже не соответствовало имевшимся стемам.

## [2026-09-29] cues | Rock & Roll Queen: отсчёт к последнему удару

По стему барабанов найден финальный удар около 2:40 (пик атаки ~160.08 с), cue привязан к ближайшей доле 93.1 / 160.000 с. Добавлен `end in` + count:true → «end in 3 … 3 2 1», всего 8 cue. Пересобраны preview/pb-other-прослушка/practice Ромы/стем cues; локальные HTTP-файлы проверены хешами, cues.wav синхронизирован в риг. Версия сохранена в `The Subways - Rock and Roll Queen/arrangement-v4/`.

## [2026-09-29] cues | Pretty Fly: первый бэк, общий вход, вокальный затакт басового куплета

По измеренным стемам добавлены cue: vocal in на 2.1 / 5.035 с (Alex отдельно подтвердил первый бэк «Give it to me baby», а не lead около 15 с); all in на 10.1 / 18.462 с; bass verse ready go на 73.4 / 125.455 с — вокальный затакт на долю раньше баса 74.1 / 125.874 с. Последняя фраза целиком с raw:true. Всего 4 cue с прежним drums in на старте. Предыдущая версия сохранена в `Pretty Fly/versions/2026-09-29-before-cues-v1/` (в канонической папке The Offspring).

Полный рендер с pitch −2 завершён, плюс/прослушки плейбека/4 practice/web-стемы обновлены; текущие локальные HTTP-файлы проверены хешами. Музыка/клик/pb-other/pb-drums WAV побайтно совпали с предыдущей версией. Снимок `versions/2026-09-29-cues-v2/`, измерения `analysis/cue-anchors-2026-09-29.json`; cues.wav синхронизирован в риг.

## [2026-09-29] import | Медведица: Moises ZIP → стемы в локальном web

По запросу Alex импортирован архив `Мумии_ Тролль _ Медведица _3uDFkM8FH_E_-E minor-130bpm-443hz.zip`: 8 музыкальных стемов + метроном + служебный count-in. Сглаженный дрейф −19.7…+3.2 мс выровнен общей картой RubberBand R2 на 130 BPM без pitch shift. Male/female vocals сохранены отдельно (оба нужны), в web объединены как Вокал; lead/rhythm guitars — Гитары. Ещё Барабаны/Бас/Клавиши/Остальное + Click/Cues. Новый плюс собран только из стемов, старый цельный источник и рендер перенесены в `versions/2026-09-29-before-stems-v1/`; сырьё/рецепт/манифест в `imports/moises-2026-09-29/`. Прежние три cue на 3.692 / 7.385 / 36.923 с. Локальные 8 дорожек + preview проверены HTTP-хешами, seeking 206; cues.wav синхронизирован в риг. Аплоада нет.

## [2026-09-29] transcription | Кукла колдуна: два MIDI-голоса скрипок для Logic

По подтверждению Alex разобран корневой `strings.wav` через Basic Pitch ONNX, затем фундаментальные частоты/гармоники: убраны многие октавные дубли, вибрато-фрагменты и короткие хвостовые перекрытия. `transcription/violin-v1/kukla-violins-2voices.mid` — 752 ноты (456/296), 148.6 BPM, render-frame +3.057926 с, без квантизации и pitch-bend. MIDI перечитан двумя библиотеками (ошибка сериализации <0.46 мс), просмотрены спектральные наложения, выполнен обратный синтез. Аудиогайд и source-left/MIDI-right для слуховой правки; 152 ноты отмечены менее уверенными, особенно тихая зона/финал. Статус — черновая транскрипция, не выверенная партитура и не готовый playback-layer. Сохранены рецепт, CSV, отчёт и инструкция импорта; обновлены страница песни и index.

## [2026-10-01] analysis | Кукла колдуна: громкость пользовательского pb-other

Найден `/Users/alex/Documents/kukla_kolduna_pb_other.mp3` (бэки/скрипки/гитары по описанию Alex). Измерены он и 26 текущих pb-other: новый −15.4 LUFS, −0.1 dBTP, активный stereo RMS −18.25; плотные музыкальные референсы около −17.6…−18.1 LUFS, старая Кукла −18.9. Рекомендован общий trim **−2.5 dB**: отдельный измерительный проход без сохранения аудио подтвердил −17.9 LUFS / −2.6 dBTP. Активные фрагменты остаются немного громче большинства выбранных музыкальных референсов. Результаты и рецепт в `Король и Шут - Кукла колдуна/analysis/2026-10-01-pb-other-loudness/`; исходник не правили и в playback пока не подключали.

## [2026-10-01] level | Кукла колдуна: пользовательский pb-other −2.5 dB

По просьбе Alex сохранён `/Users/alex/Documents/kukla_kolduna_pb_other_minus2p5dB.wav`: простой gain −2.5 dB, PCM 24 bit / 48 kHz stereo. Проверка готового файла: −17.9 LUFS, true peak −2.6 dBTP, длительность 206.784 с. Исходный MP3 сохранён, mix/риг ещё не обновлены.

## [2026-10-01] deploy | Кукла колдуна: пользовательский pb-other в проекте и риге

По просьбе Alex WAV −2.5 dB импортирован в `parts/kukla-pb-other-v1.wav`, закреплён как единственный render-layer pb-other в mix.json. В canonical WAV перенесена tempo-метка 148.6 при побайтно идентичном PCM; обновлена pb-other MP3-прослушка. Старая версия сохранена в `versions/2026-10-01-before-custom-pb-other/`. Sync изменил только `Кукла колдуна/pb-other.wav` в риге, SHA256 factory/риг совпал. Коммит `be489c2a` успешно запушен в `basbit/cherry-daddies-2000`, `origin/main`.

## [2026-10-01] import | Медведица: обновление файлов, две отдельные гитары

По просьбе Alex импортирован новый Moises ZIP с суффиксом `(1)` (MP3 48 kHz); после уточнения «только файлы» обновлены 8 музыкальных WAV и метроном в корне песни. `lead_guitars.wav` и `rhythm_guitars.wav` — отдельные проверенные партии. Подготовка прежним рецептом: 44.1 kHz stereo float, общий warp 130 BPM без питча; карта совпадает с прежней, все файлы по 235.721519 с, онсеты метронома отличаются максимум на один сэмпл. Сырьё/хеши/рецепт/проверка — `imports/moises-2026-10-01/`, прежние файлы — `versions/2026-10-01-before-stems-update/`. Web, auto-render и риг остаются на предыдущем импорте согласно выбранному объёму задачи.

## [2026-10-02] workflow | Самостоятельные lyrics, сохранение и доставка в риг

Полный репозиторий группы подключён к `alexomee/cherry-daddies-alex`, `tkozinets` приглашена с write-доступом. Добавлены AGENTS.md, русская памятка `docs/vocalist-workflow.md`, setup.command, локальная MLX/faster-whisper транскрипция, build/review/approve/check/save/deliver. Превью использует сценический ASS и реальные click/cues рига; хеши связывают подтверждение с исходниками и версией плейбека. «Сохрани» = проверенный commit/push сюда; «сохрани и отправь клавишнику» = также выбранная пара клипов и строка манифеста в риг. Доставка сохраняет чужие песни, проверяет удалённый source commit, обнаруживает устаревшее ревью и поддерживает повтор после отказа push. 44 теста, реальный mpv-рендер и транскрипция русского фрагмента прошли; доступ в приватный риг Тане должен выдать basbit. Новая песня требует проверки подключения MainStage; Push не равен Pull на ноуте клавишника. Основная реализация: `ab4fddd`.

## [2026-10-02] skill | tanya-texts: запуск Тани с нуля

По просьбе Alex добавлен repo-scoped скилл `.agents/skills/tanya-texts/SKILL.md` с UI-метаданными ChatGPT/Codex: настройка, два репо, JamZone/ASR, preview, человеческая проверка, save и deliver. `docs/tanya-start.md` обращается к Тане и содержит ссылки на оба приглашения и готовые сообщения агенту для клонирования и запуска скилла. Alex сообщил, что basbit уже отправил приглашение в риг; принятие и реальные write-права агент проверяет на её машине. Нативный вызов: `@` в ChatGPT, `$`/`/skills` в Codex; запрос `/tanya-texts` также описан в AGENTS.md, доступен прямой запуск по пути SKILL.md. YAML и локальные ссылки проверены.

## [2026-10-03] render | Я буду: бэк-вокал убран из всех шин плейбека

По запросу Alex `backing_vocals` исключён из всех шин в `music/songs/5sta Family & 23:45 - Я буду/mix.json`:
- `pb-other`: остался только `piano`;
- `pb-other-keys`: остались `piano`, `keys`, `other`.
Выполнен полный перерендер через `jamzone_render.py`: обновлены `pb-other.{wav,mp3}`, `pb-other-keys.{wav,mp3}`, `all.wav`, `cue_preview.mp3` и `web/songs.json`. Скорректированы страницы вики `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-03] workflow | Общая библиотека all.wav и превью Тани по одной песне

По согласованию Alex опубликованы 37 чистых WAV (1.406 ГБ) в существующем R2,
вне Git; проверены полным HTTP-скачиванием и SHA-256. Каталог версий/таймлайнов
в `music/guide-catalog.json`, публикация включена в `tools/sync_site.py` и
`--guides-only`. Workflow получает один guide и только выбранные sparse-файлы
рига, собирает полное вокальное review командой `preview NN`. Проверены
отпечатки 24/24 песен lyric-сетлиста; для clip 13 измерен реальный синхрон по
восстановленному сигналу (0 мс в начале/середине/конце). Обновлены скилл и
инструкции Intel Mac без Homebrew. Подтверждение текста остаётся за Таней,
сценический риг и доставка клипов не менялись. [Процесс и измерения](pipelines/lyric-guide-library.md).

## [2026-10-05] cues | Такая любовь: правка cue-сета (13 cue)

По запросу Alex обновлены подсказки в `music/songs/Такая любовь/mix.json`:
1. Стартовый cue bar 1.1 переведён в `Такая любовь synth fade-in ready go` (3.556 с, название в естественном темпе + блок из 4 слов «synth fade-in ready go» по долям такта 0);
2. Убран cue `strings in` (бывший bar 21);
3. Оба `drums in` переведены в `drum fill ready go` и сдвинуты на 1 такт раньше (bar 27 → 26 / 48.0 с и bar 68 → 67 / 120.9 с) под реальные барабанные сбивки перед входом грува;
4. Оба `solo in` заменены на `synth solo ready go` (bar 43 / 78.2 с и bar 84 / 151.1 с);
5. Убран cue `light drums` (бывший bar 59);
6. Стоп 2:45 (bar 92 / 165.3 с) заменён на `drum stop` («drum stop in 3 · 3 2 1») — останавливаются только барабаны, гитара и другие партии продолжают звучать;
7. `guitar in` заменён на `guitar solo ready go` на затакте соло (bar 93.4 / 168.4 с).
Всего 13 cue. Выполнен полный рендер (`jamzone_render.py`): обновлены `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-*.wav`, practice-миксы и `web/songs.json`.

## [2026-10-05] render | Я буду: pb-other объединён с pb-other-keys, pb-other-keys удалён

По запросу Alex состав `pb-other` в `music/songs/5sta Family & 23:45 - Я буду/mix.json` изменён на `["piano", "keys", "other"]` (включены все клавиши и вступительный синт-хук), отдельная шина `pb-other-keys` удалена. Выполнен полный перерендер через `jamzone_render.py`: обновлены `pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `web/songs.json`. Файлы `pb-other-keys.*` удалены из `auto-render/` и из рига (`cherry-daddies-setlist-2026-06-16/Я буду/pb-other-keys.wav`), `pb-other.wav` скопирован в риг. Скорректированы страницы вики `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-05] import | Я буду: сборка pb-other из оригинальных стемов + караоке бэк-вокал (redacted)

По указанию Alex состав `pb-other` скомпонован заново:
- `backing_vocals`: взят `redacted`-вариант из караоке-минусовки, точно сфазирован с таймлайном оригинала (компенсированы задержка энкодера и смещение);
- `guitars`, `piano`, `keys`: возвращены из оригинального импорта (лучшее разделение);
- `other`: взят из оригинала и заглушен с 0:13 (13.0 сек);
- `bass`: взят из караоке-минусовки (скомпенсирован на 20 мс и отварплен под 90.0 BPM, глубокий суб-бас 30–80 Гц);
- `drums`, `metronome`, `vocals`: из оригинального импорта.

В `tools/jamzone/jamzone_render.py` убран баг подмешивания click/cues в `pb-*.mp3`. Выполнен переварп (`jamzone_warp_ext.py`) и полный рендер (`jamzone_render.py --practice`): `pb-other.{wav,mp3}`, `pb-bass.{wav,mp3}`, `all.wav`, practice-миксы и `web/songs.json` обновлены. В риг синхронизированы `pb-other.wav`, `pb-bass.wav`, `pb-drums.wav`. Скорректированы `wiki/songs/ya-budu.md` и `wiki/index.md`.

## [2026-10-06] web | Раздел «24.10 lefkara» для сборки нового плейлиста

По запросу Alex добавлен новый раздел/таб «24.10 lefkara» в веб-дашборд (`web/index.html` и `tools/setlist_dashboard.py`):
- Вкладка «24.10 lefkara» выведена первой в навигации с фиолетовым акцентом (`--lefkara:#9d5bf0`) и выставлена активной по умолчанию.
- Поддерживает отображение как единого списка (`cls: "lefkara"`), так и разбивки по сетам (`cls: "lefkara1"`, `"lefkara2"`).
- При пустом списке корректно выводится плейсхолдер «Плейлист пока пуст — собираем треки».
- Перегенерирован `web/songs.json`. Сетлист готов к наполнению треками.

## [2026-10-06] render | 24.10 Lefkara: импорт 5 JamZone-треков, pb-other, живой бас Ромы, стартовые cues

По предоставленному Alex списку из 10 песен проверена локальная библиотека JamZone:
- 5 песен скачаны в JamZone и полностью собраны:
  1. `Shocking Blue — Venus` (cat_12674, 128 BPM, `click: follow`): pb-other = Wurlitzer + Backing Vocals, стартовый cue `Venus guitar in ready go`.
  2. `Modern Talking — Cheri, Cheri Lady` (cat_37357, 114 BPM): pb-other = все синты, Orchestra Hit, Synth Brass, Synth Flute, Backing Vocals; стартовый cue `Cheri Cheri Lady all in ready go`.
  3. `Ricchi e Poveri — Sarà perché ti amo` (cat_18179, 120.6 BPM): pb-other = Piano, Synthesizer, Synth Pad, String Section; стартовый cue `Sarà perché ti amo all in ready go`.
  4. `Modern Talking — Brother Louie` (cat_38978, 109 BPM): pb-other = Piano, Synthesizer 1/2, Synth Pad, Synth Strings, Orchestra Hit, Synth Brass, Backing Vocals; стартовый cue `Brother Louie all in ready go`.
  5. `Donna Summer — Hot Stuff (12" Version)` (cat_5408, 120.3 BPM, `click: follow`): `03_Percussion` исключена (играет барабанщик), pb-other = Piano, Synthesizer, Synth Keys, Backing Vocals; стартовый cue `Hot Stuff all in ready go`.
- Для всех 5 песен: бас живой (`pb-bass: null`, Рома на бас-гитаре), сгенерированы `all.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, practice-миксы на четверых и поканальные stems.
- 5 остальных песен добавлены в список сетлиста `24.10 Lefkara` (Heart of Glass, Ghostbusters, Stumblin' In, Sweet Dreams, Personal Jesus) в статусе ожидания загрузки/источников.
- `web/songs.json`, страницы `wiki/songs/`, `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md` обновлены.

## [2026-10-06] render | 24.10 Lefkara: остальные 5 треков скачаны в JamZone и собраны на 100%

После докачки Alex недостающих треков в JamZone:
- Извлечены HQ-стемы, настроен `mix.json`, собраны starter cues и practice-миксы для оставшихся 5 песен:
  1. `Blondie — Heart of Glass` (cat_12447, ~114.7 BPM, `click: follow`): `03_Percussion` исключена, pb-other = Organ, Pad, Strings, Backing Vocals; стартовый cue `Heart of Glass all in ready go`.
  2. `Ray Parker Jr. — Ghostbusters` (cat_11300, 115 BPM): pb-other = Piano, Clavinet, синты (Strings, Keys 1/2, Lead, Brass), Brass section, Backing Vocals; стартовый cue `Ghostbusters all in ready go`.
  3. `Suzi Quatro & Chris Norman — Stumblin' In` (cat_22836, ~129.3 BPM, `click: follow`): `01_Intro_Count` отделен от основного `02_Click`, pb-other = Rhodes, String Section; стартовый cue `Stumblin In all in ready go`.
  4. `Eurythmics — Sweet Dreams (Are Made of This)` (cat_69124, ~125.2 BPM): `03_Percussion` исключена, pb-other = Noise effects, Piano, синты, Strings, Lead, Backing Vocals; стартовый cue `Sweet Dreams all in ready go`.
  5. `Depeche Mode — Personal Jesus` (cat_12804, 130 BPM): `03_Percussion` исключена, pb-other = Breath FX, Guitar Synth, Piano, Organ, Pad, Lead, Arp 1/2, Backing Vocals; стартовый cue `Personal Jesus all in ready go`.
- Для всех 10 песен сета: бас играет Рома (`pb-bass: null`), сформированы `auto-render` (all, cue_preview, pb-other, pb-drums, practice, stems).
- Все 10 песен в разделе `24.10 lefkara` на дашборде получили 10/10 готовность данных и полный интерактивный плеер.
- Созданы страницы в `wiki/songs/` для всех 10 песен, обновлены `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md`.

## [2026-10-06] lyrics | 24.10 Lefkara: сценические тексты (клипы 34–43) для всех 10 песен

По запросу Alex созданы сценические тексты и видеоклипы для сценического вокального монитора:
- Сгенерированы сценические субтитры ASS с двухстрочным page-flip отображением (`clips/34.ass` .. `clips/43.ass`) и фоновые видео MP4 (`clips/34.mp4` .. `clips/43.mp4`).
- Экспортированы тайм-кодированные TSV-таблицы в `tools/lyric-launcher/lyrics-timed/34.tsv` .. `43.tsv` с точным смещением `offset_sec` под финальный таймлайн плейбека.
- В дуэтах (`Stumblin' In`, `Sarà perché ti amo`) учтены оба ведущих голоса.
- В `tools/lyric-launcher/songs.tsv` зарегистрированы 10 новых строк: клипы 34–43, Program Change 35–44.

## [2026-10-06] cues | Heart of Glass: фикс стартового кью + полный набор из 14 подсказок

По замечаниям и таймкодам Alex:
- **Причина раннего стартового кью:** в JamZone клике первый такт — прекаунт клика в тишине; барабаны и музыка на самом деле вступают на такте 2 (`bar 2.1`, 4.254 с). Стартовый cue переведён на `bar 2`: теперь «Heart of Glass all in ready go» идеально выровнен по входу барабанов.
- Настроены все запрошенные подсказки (всего 14 cue):
  - `bar 2.1` — `Heart of Glass all in ready go`
  - `bar 6.1` — `verse in ready go` (вход куплета 1)
  - `bar 14.1` — `keep going` (окончание куплета 1, сквозной ход к куплету 2)
  - `bar 17.1` — `verse in ready go` (куплет 2)
  - `bar 26.1` — `chorus in ready go` (припев 1)
  - `bar 38.1` — `verse in ready go` (куплет 3, ~1:21)
  - `bar 47.1` — `chorus in ready go` (припев 2, ~1:41)
  - `bar 55.1` — `instrumental with-beat-offset ready go` (инструментал с 2-долевым оффсетом)
  - `bar 70.2` — `voice in ready go` (вокал в бридже, ~2:29)
  - `bar 78.2` — `break in ready go` (брейк, ~2:46)
  - `bar 82.2` — `guitar in ready go` (гитара после брейка, ~2:54)
  - `bar 86.1` — `verse in ready go` (куплет 4, ~3:02)
  - `bar 95.1` — `chorus in ready go` (припев 3, ~3:21)
  - `bar 119.2` — `end in` (`count: true` → «end in 3 · 3 2 1», финал ~4:12).
- Выполнен перерендер: обновлены `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.mp3`, practice-миксы и `web/songs.json`.
- Пересобран сценический lyric-клип 34 (`clips/34.ass`, `clips/34.mp4`, `lyrics-timed/34.tsv`) под новый таймлайн.

## [2026-10-06] cues | Heart of Glass: 5-дольный instrumental, точное выравнивание куплета 3:00 и припева 3:18

По замечаниям Alex:
1. `instrumental with-beat-offset ready go` развёрнут на 5 долей:
   - `instrumental`: 1 доля (доля -5)
   - `with-beat-offset`: 2 доли натуральным темпом без сжатия (доли -4 и -3)
   - `ready`: 1 доля (доля -2)
   - `go`: 1 доля (доля -1)
   В `jamzone_render.py` (`_metric_clips`) добавлена поддержка натурального многодолевого растяжения для длинных слов внутри фразы без агрессивного `_atempo` сжатия.
2. Куплет 4 (`verse in` около 3:00) сдвинут с доли 1 на долю 2 (`bar 86.2` = 180.564 с): точно под вход фразы «Once I had a love».
3. Припев 3 (`chorus in` около 3:18) сдвинут с доли 1 на долю 2 (`bar 95.2` = 199.394 с): точно под вход фразы «In between...».
4. Перерендер `all.wav`, `cue_preview.mp3`, `click.wav`, `cues.wav`, stems и `web/songs.json`.

## [2026-10-06] cues | Ghostbusters: добавлены 11 cue по сетке песни

По запросу Alex сформирован и добавлен полный набор cue для `Ray Parker Jr. — Ghostbusters`:
- `bar 1.1` (4.174s) — `Ghostbuster playback in` («Ghostbuster · playback in ready go»)
- `bar 2.1` (6.261s) — `guitar bass ready go` (вступление живой гитары и баса, 0:06)
- `bar 6.1` (14.609s) — `drums in` («drums in ready go», барабанный грув, 0:14)
- `bar 7.1` (16.696s) — `main in` («main in ready go», главная тема, 0:17)
- `bar 59.1` (125.217s) — `break-one in` («break-one in ready go», первый брейк, 2:05)
- `bar 75.1` (158.609s) — `break-two in` («break-two in ready go», второй брейк, 2:38)
- `bar 83.1` (175.304s) — `chorus in` («chorus in ready go», припев / главная тема, 2:55)
- `bar 103.1` (217.043s) — `keep going` (звучит на 3:36 перед новым 4-тактовым циклом)
- `bar 115.1` (242.087s) — `keep going` (звучит на 4:02 перед новым 4-тактовым циклом)
- `bar 123.1` (258.783s) — `keep going` (звучит на 4:18 перед новым 4-тактовым циклом)
- `bar 128.1` (269.217s) — `end in` («end in 3 · 3 2 1», финальный удар барабанов на 4:29)

Выполнен локальный рендер через `jamzone_render.py "Ghostbusters"`: обновлены `mix.json`, `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`, `timeline.json` и `web/songs.json`.

## [2026-10-06] cues | Venus, Cheri Cheri Lady, Stumblin' In: обновление подсказок и обрезка интро Cheri

По запросу Alex обновлены cue и таймлайны трёх песен:
1. **Venus (Shocking Blue):**
   - Ранний стартовый cue на 1-м такте удалён.
   - `bar 9.1` (19.066s) — `Venus all in` («Venus · all in ready go», вступление банды).
   - `bar 13.1` (26.656s) — `verse in` («verse in ready go», вступление вокала на даунбит).
   - `bar 103.1` (195.666s = 3:15.7) — `end in` (`count: true` → «end in 3 · 3 2 1» на последний барабанный удар).
   - Зафиксирован `count_in: 2` для сохранения стабильного таймлайна (+3.450с).

2. **Cheri, Cheri Lady (Modern Talking):**
   - В `jamzone_render.py` добавлена поддержка `cut_bars`: физическая вырезка диапазона тактов из стемов и клика с de-click фейдами.
   - Вырезаны 4 вступительных такта флейты (`cut_bars: [2, 6]`), трек начинается сразу с главной темы клавиш:
     - `bar 2.1` (4.211s) — `Cheri Cheri Lady all in` («Cheri Cheri Lady · all in ready go» на вступление клавишной темы).
     - `bar 105.1` (221.053s = 3:41.1) — `end fill in` (`count: true` → «end fill in 3 · 3 2 1» под финальную сбивку барабанов).
   - Таймлайн сценических lyrics пересчитан под новый трек: `37.tsv` сдвинут на 5 тактов (-10.53с), перегенерированы `clips/37.ass` и `clips/37.mp4`.

3. **Stumblin' In (Suzi Quatro & Chris Norman):**
   - Добавлены 13 cue строго под вокал, соло и стопы барабанов:
     - `bar 1.3` (4.654s) — `Stumblin In vocal in` («Stumblin In · vocal in ready go» под вступление голосов на 3-й доле).
     - `bar 17.3` (34.414s) — `alex sing ready go` (вход Alex «Wherever you go»).
     - `bar 25.3` (49.214s) — `tanya sing ready go` (вход Tanya «I'm fallin' for you»).
     - `bar 37.2` (70.994s = 1:11.0) — `stop` («stop in 3 · 3 2 1» на стоп барабанов).
     - `bar 54.1` (102.094s = 1:42.1) — `guitar solo ready go` (гитарное соло).
     - `bar 61.3` (116.014s = 1:56.0) — `alex sing ready go` (Alex «You were so young»).
     - `bar 65.2` (123.034s = 2:03.0) — `tanya sing ready go` (Tanya «I may have been young»).
     - `bar 69.3` (130.914s = 2:10.9) — `alex sing ready go` (Alex «Well you were the one»).
     - `bar 81.2` (152.734s = 2:32.7) — `stop` («stop in 3 · 3 2 1» на стоп барабанов).
     - `bar 105.2` (197.314s = 3:17.3) — `alex sing ready go` (Alex «Oh stumblin' in»).
     - `bar 113.2` (212.154s = 3:32.2) — `tanya sing ready go` (Tanya «Oh stumblin' in»).
     - `bar 121.1` (226.494s = 3:46.5) — `tanya sasha sing go` (дуэт Tanya & Sasha).
     - `bar 128.1` (239.414s = 3:59.4) — `end in` (`count: true` → «end in 3 · 3 2 1» на финальный удар).

Выполнены рендеры всех трёх песен в `auto-render/` (`all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`), обновлён `web/songs.json`.

## [2026-10-06] cues | Sarà perché ti amo, Sweet Dreams, Personal Jesus, Brother Louie, Hot Stuff: фикс ранних стартовых cue и добавление "end in 3 2 1"

По замечаниям Alex обновлены стартовые и финальные кью для 5 песен сетлиста Lefkara:

1. **Ricchi e Poveri — Sarà perché ti amo:**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.978s): `Sarà perché ti amo all in` («Sarà perché ti amo · all in ready go»); 2 такта precount теперь корректно содержат объявление и отсчёт перед вступлением всей банды на такте 3.
   - Добавлен финальный cue на последний барабанный удар: `bar 91.2` (179.520s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

2. **Eurythmics — Sweet Dreams (Are Made of This):**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.834s): `Sweet Dreams all in` («Sweet Dreams · all in ready go»); музыка вступает на такте 3 после 2 тактов precount.
   - Добавлен финальный cue на последний барабанный удар: `bar 113.1` (214.709s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

3. **Depeche Mode — Personal Jesus:**
   - Стартовый cue перенесён с `bar 1` на `bar 3.1` (3.692s) и заменён на гитару: `Personal Jesus guitar in` («Personal Jesus · guitar in ready go») — вступление гитары на такте 3 после 2 тактов precount.
   - Добавлен финальный cue на последний барабанный удар перед клавишным хвостом: `bar 117.4` (215.538s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

4. **Modern Talking — Brother Louie:**
   - Стартовый cue перенесён с `bar 1.1` на первую ноту клавиш `bar 1.3` (3.303s): `Brother Louie playback in` («Brother Louie · playback in ready go»); автоматически добавлен 1 такт count-in lead, чтобы фраза чисто отзвучала перед нотой.
   - Добавлен финальный cue на orchestra hit и финальный удар барабанов: `bar 105.4` (232.844s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

5. **Donna Summer — Hot Stuff (12" Version):**
   - Стартовый cue перенесён с `bar 1` на `bar 2.1` (4.114s): `Hot Stuff all in` («Hot Stuff · all in ready go»); вся банда вступает на такте 2 (lead +1 такт count-in для чистого звучания).
   - Добавлен финальный cue на последний барабанный удар: `bar 160.1` (319.254s) — `end in` (`count: true` → «end in 3 · 3 2 1»).

Для всех 5 песен выполнен локальный рендер через `jamzone_render.py` (`mix.json`, `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `pb-*.wav`, `pb-*.mp3`, `timeline.json`), актуализирован `web/songs.json`.

## [2026-10-07] fix | Stumblin' In: стартовый cue сдвинут на «&» (bar 1 beat 2&, 4.419s)

- В `jamzone_render.py` добавлена поддержка дробных долей `beat: 2.5` и `"2&"` (парсинг `_parse_beat`, формат отображения `_disp_beat`).
- **Синкопированный вход:** вокальная фраза «Our love is alive» начинается со слова «Our» на синкопе 2& (4.419s). Чтобы подсказка звучала в том же синкопированном ритме и приходила точно в долю:
  - `vocal` на 2& прекаунта (2.55s)
  - `in` на 3& прекаунта (3.02s)
  - `ready` на 4& прекаунта (3.48s)
  - `go` на 1& такта 1 (3.95s)
  - ровно через 1 долю (на 2&, 4.419s) чисто и в ритме вступает голос: «Our» (2&) → «love» (доля 3, 4.65s).
- **Стопы барабанов (bar 37 и 81):** оба cue были сдвинуты на 1 долю позже (`beat 2`). Исправлено на `bar 37 beat 1` (70.514s) и `bar 81 beat 1` (152.254s) — отсчёт «3 2 1» теперь звучит на долях 2, 3, 4 предыдущего такта, и стоп приходится точно на сильную долю 1.
- **Гитарное соло (bar 53):** соло начиналось на `bar 53 beat 3` (во время прежнего «ready»), а cue целился в `bar 54 beat 1`. Cue перенесён на `bar 53 beat 3` (101.174s) — теперь «ready» на 53.1, «go» на 53.2, и соло начинается ровно на следующей доле после «go».
- Выполнен перерендер `jamzone_render.py`, обновлены `auto-render/*`, `mix.json`, `web/songs.json`, `wiki/songs/stumblin-in.md`.

## [2026-10-07] web | Добавлен сет «07.10 rehearsal» (10 песен) в веб-дашборд

- По запросу Alex сформирован репетиционный список на 7 октября 2026:
  1. `Smells Like Teen Spirit — Nirvana` (черновой слот без папки / hasData: false)
  2. `Кукла колдуна — Король и Шут`
  3. `Pretty Fly (For A White Guy) — The Offspring`
  4. `Rock & Roll Queen — The Subways`
  5. `Heads Will Roll — Yeah Yeah Yeahs`
  6. `I Love It — Icona Pop`
  7. `Медведица — Мумий Тролль`
  8. `Мелом — Пропаганда`
  9. `Я сошла с ума — ТАТУ`
  10. `Мама Люба — SEREBRO`
- Создана выделенная вкладка «07.10 rehearsal» в `web/index.html` с акцентным цветом `--rehearsal:#38bdf8`.
- В `tools/setlist_dashboard.py` добавлен блок сета `07.10 rehearsal`, перегенерирован `web/songs.json`.
- Существующие заметки и todo для всех 9 готовых треков сохранены и подтянуты по `sid` без дублирования.
- Создана страница `wiki/gigs/2026-10-07-rehearsal.md`, обновлён `wiki/index.md`.

## [2026-10-07] cues | Sarà perché ti amo: финальный cue перенесён на такт 91.1 ("end fill in 3 · 3 2 1")

- Финальный cue перенесён с `bar 91.2` (179.520s, последний удар) на 1 долю раньше: `bar 91.1` (179.023s = 2:59.02).
- Текст изменён на `end fill in` (`count: true` → «end fill in 3 · 3 2 1»):
  - Анонс «end fill in 3» звучит в конце такта 89 / начале такта 90 (~2:56.2 – 2:57.1s).
  - Отсчёт «3» (2:57.5s, такт 90.2), «2» (2:58.0s, такт 90.3), «1» (2:58.5s, такт 90.4) звучит во время барабанной сбивки.
  - На 2:59.02s (такт 91.1) отсчёт завершён, и точно в долю звучат три финальных акцента keys: «pa pa pa» (такт 91 доли 1, 1-и, 2 с финальным крэшем).
- Выполнен перерендер `jamzone_render.py` (`mix.json`, `cues.wav`, `cue_preview.mp3`, `all.wav`, стемы), обновлены `web/songs.json`, `wiki/index.md`, `wiki/songs/sara-perche-ti-amo.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-07] cues | Brother Louie: финальный cue перенесён на такт 105.3 ("end fill in 3 · 3 2 1")

- Финальный cue перенесён с `bar 105.4` (232.844s) на 1 долю раньше: `bar 105.3` (232.294s = 3:52.29).
- Текст изменён на `end fill in` (`count: true` → «end fill in 3 · 3 2 1»):
  - Анонс «end fill in 3» звучит в конце такта 104 (~3:49.3 – 3:50.2s).
  - Отсчёт «3» (3:50.6s, такт 104.4), «2» (3:51.2s, такт 105.1), «1» (3:51.7s, такт 105.2).
  - На 232.294s (такт 105.3) отсчёт завершён, и точно в долю звучат финальные удары orchestra hit / барабанов (такт 105 доли 3 и 4).
- Выполнен перерендер `jamzone_render.py` (`mix.json`, `cues.wav`, `cue_preview.mp3`, `all.wav`, стемы), обновлены `web/songs.json`, `wiki/index.md`, `wiki/songs/brother-louie.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-07] level | Кукла колдуна: замена pb-other на более громкий рендер v2 без трима

На репетиции выяснилось, что предыдущая версия с тримом −2.5 dB (−17.9 LUFS) звучала слишком тихо.
По запросу Alex получен новый файл `/Users/alex/Downloads/кукла колдуна other.mp3` (Logic Pro bounce, 48 kHz / 320 kbps stereo, 206.784 с).
- **Уровни:** −14.9 LUFS-I, −0.1 dBTP, активный stereo RMS −18.22 dBFS, mono −19.19 dBFS, LRA 8.6 LU (на ~3 dB громче прежнего v1).
- **Тайминг:** точное посемпловое совпадение с v1 (лаг 0 мс, 9 925 632 семплов при 48 kHz).
- **Пайплайн:** файл импортирован в `parts/kukla-pb-other-v2.wav` (PCM 24 bit / 48 kHz stereo); в `mix.json` обновлена привязка на `kukla-pb-other-v2`. В canonical `auto-render/pb-other.wav` добавлена tempo-метка 148.6 (SHA256: `95220a9f10812855e9a3ff2c672638f8fb60280f1d1d9713761d6416b5c7b7fa`). Обновлена прослушка `auto-render/pb-other.mp3` (pb-other + click + cues) и `web/songs.json`.
- Предыдущая версия сохранена в `versions/2026-10-07-before-louder-pb-other/`.
- Выполнен `sync_to_mainstage.sh --apply "Кукла колдуна"`: обновлён `pb-other.wav` в риге `cherry-daddies-2000`.

## [2026-10-07] ingest | Smells Like Teen Spirit: базовый плейбек (intro cue + click) из JamZone

- По запросу Alex подготовлен базовый плейбек для репетиции (`07.10 rehearsal`).
- Исходник: JamZone **cat_11775**, 13 HQ M4A-стемов распакованы через `jamzone_extract.py`.
- **Сетка и темп:** в оригинальной дорожке темп интро ~110–111 BPM, с такта 5 (вход барабанов) ускоряется до ~117.6 BPM. Использован `"click": "follow"` (BPM 118.0) — рендер следует реальной сетке клика с максимальной ошибкой <4.2 мс.
- **Плейбек:** базовый живой состав (`pb-other: null`, `pb-bass: null`). Стволы распределены по игрокам в `players`: Alex (все электрогитары), Roma (бас), Steve (барабаны), Tanya (вокал).
- **Cue:** 1 стартовая подсказка `bar 2.1` (4.221s) — `"Smells Like Teen Spirit guitar in"`:
  - Lead-такт 0 (0.00–2.03s, JZ count-in сэмплы клика): название песни **«Smells Like Teen Spirit»** в естественном темпе.
  - Такт 1 (2.03–4.22s, прекаунт JamZone): слова **«guitar in ready go»** точно на долях клика.
  - Такт 2.1 (4.221s): вступает гитарный рифф Курта Кобейна (`05_Electric_Guitar_(intro)`).
- Выполнен рендер через `jamzone_render.py` с флагом `--practice`: сгенерированы `all.wav`, `click.wav`, `cues.wav`, `cue_preview.mp3`, `timeline.json`, раздельные mp3 в `stems/`, а также practice-миксы для всех 4 участников.
- Обновлён `tools/setlist_dashboard.py` (привязка к папке `Nirvana - Smells Like Teen Spirit`), перегенерирован `web/songs.json` (57/57 песен с данными, hasData: true).
- Создана страница `wiki/songs/nirvana-smells-like-teen-spirit.md`, обновлены `wiki/gigs/2026-10-07-rehearsal.md` и `wiki/index.md`.

## [2026-10-08] cue | Кукла колдуна: добавлен финальный cue «end in 3 3 2 1»

- По запросу Alex добавлен финальный cue на такт 124.1 (201.884 с / 3:21.88): `{"bar": 124, "text": "end in", "count": true}`.
- Голосовой движок объявляет «end in 3», затем отсчитывает «3 2 1» на долях 2, 3, 4 такта 123 (200.67s, 201.08s, 201.48s), после чего на 124.1 звучит сильная доля финального аккорда, переходящая в сценический end fill.
- Выполнен перерендер через `jamzone_render.py` (`cues.wav`, `cue_preview.mp3`, practice-миксы, `web/songs.json`), сохранён оригинальный 24-bit/48kHz `auto-render/pb-other.wav` v2 (`95220a9f...`). Обновлены `wiki/songs/korol-i-shut-kukla-kolduna.md` и `wiki/index.md`.

## [2026-10-08] cue | Pretty Fly: добавлен финальный cue «end fill in 3 3 2 1» на 108.1 (3:02.94s / ~3:03 даунбит)

- По запросу Alex добавлен финальный cue на такт 108.1 (182.937 с / 3:02.937 ≈ 3:03): `{"bar": 108, "text": "end fill in", "count": true}`.
- Голосовой движок объявляет «end fill in 3» в конце такта 106 (~3:00.0s), затем отсчитывает «3 2 1» на долях 107.2, 107.3, 107.4 (3:01.68s, 3:02.10s, 3:02.52s).
- На 108.1 (даунбит ~3:03) в cue-треке тишина — начинается сбивка барабанщика, завершающаяся финальным хитом на 109.1 (3:04.62s).
- Выполнен перерендер `jamzone_render.py` с `--practice` (`cues.wav`, `cue_preview.mp3`, practice-миксы для Alex/Roma/Steve/Tanya, web-стемы). Музыкальный `all.wav`, `click.wav`, `pb-other.wav`, `pb-drums.wav`, `timeline.json` побайтно идентичны предыдущей версии.
- Версия с 4 cue сохранена в `versions/2026-09-29-cues-v2/`, актуальная версия с 5 cue сохранена в `versions/2026-10-08-cues-v3/`.
- Риг MainStage синхронизирован через `sync_to_mainstage.sh --apply "Pretty Fly"` (`cues.wav`). Обновлены `wiki/songs/pretty-fly.md`, `wiki/index.md` и `web/songs.json`.

## [2026-10-08] render | Я сошла с ума: fade-out pb-other в 0 за 2 доли до финального удара (3:24.3)

- По запросу Alex `pb-other` в «Я сошла с ума» (ТАТУ) зафейжен в ноль к финальной доле около 3:24 (bar 77.3, 204.297 с, cue «all stop»).
- В `tools/jamzone/jamzone_render.py` добавлена поддержка параметра `fade_out` для групп плейбека (`mixdown`, `placed_layers`, `render_cat_stem`, `--practice`): плавный линейный спад `fs0..fs1`, после чего строго тишина (0.0) до конца трека.
- В `music/songs/t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)/mix.json` в `pb-other` добавлен `"fade_out": {"from_bar": 77, "from_beat": 1, "to_bar": 77, "to_beat": 3}` (2 доли = 1.333 с, с 202.964 с до 204.297 с).
- До 202.964 с трек звучит без изменений; за 2 доли плавно спадает (-21.9 dBFS → 0.0); с 204.297 с до конца трека (14.37 с) в `pb-other.wav`, `pb-other.mp3` и соответствующих stems (`keys.mp3`, `other.mp3`, `back_vox.mp3`) абсолютный ноль (вычищены остаточные шумы дождя `04_Noise_effects` и шепчущие синты `10_Synth_Voice`).
- Выполнен перерендер с `--practice`: обновлены `auto-render/` (`pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `practice-steve.mp3`, `practice-tanya.mp3`, `stems/*.mp3`), обновлены `web/songs.json`, `wiki/songs/ya-soshla-s-uma.md` и `wiki/index.md`.

## [2026-10-08] cues & render | Venus: фикс стартового интро-кью на бар 3.1 («Venus guitar in»), сохранение «all in» на бар 9.1, подсказки «guitar solo ready go» на оба соло (такты 33.1 и 95.1), удаление лишних пустых тактов (count_in: 2), акустическая гитара в pb-other на обоих соло

- **Интро-кью и удаление лишних пустых тактов:**
  - Реальный вход гитары в треке Shocking Blue — Venus находится на сильной доле 3-го такта (`bar 3.1`, 3.876s без искусственного каунт-ина).
  - Удалена директива `"count_in": 2`, которая принудительно добавляла 2 пустых такта клика в тишине перед началом трека.
  - Трек теперь начинается сразу с 2 встроенных тактов прекаунта JamZone:
    - `bar 1.1` (0.000s) — клик 1, 2, 3 → анонс «Venus» на естественной скорости (1.32s) → клик 4;
    - `bar 2.1` (1.938s) — размеренный отсчёт «guitar in ready go» на 4 долях;
    - `bar 3.1` (3.876s) — точно в долю вступает акустическая гитара интро.
  - Cue на такте 9 сохранён как `"all in"` (`bar 9.1`, 15.316s = «all in ready go») на вступление всей банды (барабаны, бас, электропиано).
  - Cue на такте 13 (`verse in`, 22.906s) и на такте 103 (`end in`, 191.917s = «end in 3 · 3 2 1») сохранены.
  - Добавлены cue на старт обоих гитарных соло:
    - `bar 33.1` (60.356s) — `"guitar solo ready go"`: отсчёт «guitar solo ready go» на 4 долях такта 32 (58.52s – 59.91s), на 60.36s начинается соло 1;
    - `bar 95.1` (176.816s) — `"guitar solo ready go"`: отсчёт «guitar solo ready go» на 4 долях такта 94 (174.93s – 176.35s), на 176.82s начинается аутро-соло 2.
  - Сценические субтитры пересинхронизированы под новый таймлайн (-3.75с): обновлены `tools/lyric-launcher/lyrics-timed/36.tsv` (первая строка «A goddess on a mountain top...» теперь на 0:22.67), пересобраны `clips/36.ass` и `clips/36.mp4`.
- **Акустическая гитара в pb-other во время обоих гитарных соло:**
  - Семы Venus получены из JamZone (cat_12674) — они изначально являются изолированными студийными дорожками (в отличие от смешанных Moises-стэмов). Дорожка `04_Acoustic_Guitar.m4a` полностью отделена от `07_Lead_Electric_Guitar.m4a` (соло) и `05_Rhythm_Electric_Guitar.m4a`.
  - В `pb-other` добавлена `04_Acoustic_Guitar` с секцией `"mute": {"04_Acoustic_Guitar": [[1, 33], [41, 95], [103, 109]]}`.
  - Акустическая гитара звучит в плейбеке строго во время обоих гитарных соло (такты 33–40, 60.36s – 75.15s и такты 95–102, 176.82s – 191.92s), когда живой гитарист Alex занят соло-партией, и абсолютно бесшумна во всех остальных частях песни (куплеты, припевы, интро, аутро).
  - В `tools/jamzone/jamzone_render.py` добавлен 15мс fade-out перед началом mute-диапазонов, исключающий щелчки при мьютировании.
- **Рендер:**
  - Выполнен перерендер с `--practice`: обновлены `auto-render/*` (`click.wav`, `all.wav`, `cues.wav`, `pb-other.wav`, `pb-drums.wav`, `cue_preview.mp3`, `pb-other.mp3`, practice-миксы для Ромы, Стива и Тани, стемы), обновлены `web/songs.json`, `wiki/songs/venus.md`, `wiki/index.md`.

## [2026-10-08] arrangement & cues | Heart of Glass: 4-тактовое барабанное интро перед стартом трека, стартовый cue «drums in», «all in» на бар 6.1

- По запросу Alex добавлено пространство для вступительного соло живого барабанщика Стива перед стартом песни Heart of Glass (Blondie):
  - Стартовый cue изменён на `"Heart of Glass drums in"` на такте 2 (`bar 2.1`, 4.239s): «Heart of Glass» звучит в lead-такте, «drums in ready go» — на такте 1, и на 4.239s вступает живой барабанщик.
  - Затем следуют 4 пустых такта (такты 2, 3, 4, 5) без плейбека, в течение которых звучит только клик и играет барабанщик.
  - В такте 5 звучит cue `"all in"` («all in ready go» на долях 1, 2, 3, 4), и на `bar 6.1` (12.626s) вступает вся группа и оригинальный плейбек трека.
- В `tools/jamzone/jamzone_render.py` добавлена поддержка `"insert_bars": {"at_bar": 2, "bars": 4}` (также в формате списка `[at_bar, count]`):
  - Точный сплит в точке межтактовой тишины (между долей 4 такта 1 и долей 1 такта 2).
  - Генерация 16 кликов JamZone (`jdb` на сильных долях каждого такта, `jbt` на долях 2, 3, 4) в темпе трека (114.66 BPM).
  - Вставка эквивалентного времени тишины (8.372 с) во все музыкальные стемы плейбека и превью.
  - Исправлен `jamzone_render.py` для использования модифицированного `click_st` вместо повторного декодирования файла с диска.
  - Добавлен автоматический тест `tools/jamzone/tests/test_insert_bars.py` (20/20 тестов зелёные).
- Все 13 последующих cue сдвинуты на +4 такта (всего 15 cue, финал `end in 3 · 3 2 1` на такте 123.2, 258.016s).
- Сценические lyrics: `lyrics-timed/34.tsv` сдвинут на +8.372s (первая строка «Once I had a love» теперь на 0:20.96 под новый вход вокала на такте 10), пересобраны `clips/34.ass` и `clips/34.mp4` через `lyric_workflow.py build 34`.
- Выполнен перерендер с `--practice`: обновлены `auto-render/*` (`click.wav`, `all.wav`, `cues.wav`, `pb-other.wav`, `pb-drums.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, `timeline.json`, practice-миксы для Roma, Steve, Tanya).
- Выполнен синк в риг: `sync_to_mainstage.sh --apply "Heart of Glass"` обновил `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav` в `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Heart of Glass/`.
- Обновлены `web/songs.json`, `music/guide-catalog.json`, `wiki/songs/heart-of-glass.md`, `wiki/index.md`.

## [2026-10-08] cues & render | Лефкара Сет 2: извлечение 7 песен, базовые стартовые/финальные cue, полный рендер и practice-миксы

- Извлечены и подготовлены все 7 новых треков 2 сета Лефкары из JamZone:
  1. `Village People - Y.M.C.A.` (cat_6926, ~127 BPM): стартовый cue `YMCA all in` (bar 3.1, 3.920s), финальный cue `end in` (bar 155.1, 291.400s).
  2. `Gloria Gaynor - I Will Survive` (cat_5921, ~116.3 BPM): стартовый cue `I Will Survive piano in` (bar 2.1, 4.113s), финальный cue `end in` (bar 103.1, 212.583s).
  3. `Bee Gees - Stayin' Alive` (cat_5447, 105 BPM): стартовый cue `Stayin Alive all in` (bar 2.1, 4.571s), финальный cue `end in` (bar 125.1, 285.714s).
  4. `Flashdance (Michael Sembello) - Maniac` (cat_7662, ~159 BPM, `cue_step: 2`): стартовый cue `Maniac all in` (bar 3.1, 4.549s), финальный cue `end in` (bar 171.1, 258.129s).
  5. `Modern Talking - You're My Heart, You're My Soul (Mix '98)` (cat_14066, ~117.5 BPM): стартовый cue `You're My Heart all in` (bar 2.1, 4.085s), финальный cue `end in` (bar 111.1, 226.703s).
  6. `Ricky Martin - Livin' La Vida Loca` (cat_8526, ~177.7 BPM, `cue_step: 2`): стартовый cue `Livin La Vida Loca all in` (bar 3.1, 4.052s), финальный cue `end in` (bar 180.1, 243.102s).
  7. `Weather Girls - It's Raining Men` (cat_13536, ~137 BPM): стартовый cue `It's Raining Men all in` (bar 3.1, 5.192s), финальный cue `end in` (bar 185.1, 324.332s).
  (8-й трек сета, `Gala - Freed from Desire`, был подготовлен ранее с 16 cue).
- Во всех треках исключена перкуссия под живого барабанщика (Стива), назначен живой бас Ромы (`pb-bass: null`), собраны `pb-other`, `pb-drums` и practice-миксы для Roma, Steve, Tanya и Alex.
- Выполнен полный рендер через `jamzone_render.py` с флагом `--practice` для всех треков (сгенерированы `click.wav`, `all.wav`, `cues.wav`, `pb-other.wav`, `pb-drums.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, practice-миксы и web-стемы).
- Созданы 7 wiki-страниц в `wiki/songs/`: `ymca.md`, `i-will-survive.md`, `stayin-alive.md`, `maniac.md`, `youre-my-heart-youre-my-soul.md`, `livin-la-vida-loca.md`, `its-raining-men.md`.
- Обновлены `wiki/gigs/2026-10-24-lefkara.md`, `wiki/index.md` и `web/songs.json` (65/65 песен с полными данными, 65 cues, 63 с practice-миксами).

## [2026-10-08] cues | Cheri, Cheri Lady: добавлен cue "verse in ready go" на первый куплет

- По запросу добавлен cue на первый куплет песни `Modern Talking — Cheri, Cheri Lady`:
  - `bar 5.4` (12.105s, snap 7.895s) — `verse in` («verse in ready go» под вокальный затакт «Oh I» на 4-й доле 5-го такта, вступающий ровно после слова «go»).
  - Сетка cues теперь содержит 3 подсказки:
    1. `bar 2.1` (4.211s) — `Cheri Cheri Lady all in` («Cheri Cheri Lady · all in ready go»)
    2. `bar 5.4` (12.105s) — `verse in` («verse in ready go»)
    3. `bar 105.1` (221.053s) — `end fill in` (`count: true` → «end fill in 3 · 3 2 1»)
- Выполнен рендер через `jamzone_render.py --practice`:
  - Обновлены `cues.wav`, `cue_preview.mp3`, `timeline.json`, practice-миксы для Roma, Steve, Tanya.
  - Музыкальные стемы (`all.wav`, `pb-other.wav`, `pb-drums.wav`) не затронуты.
- Актуализирован `web/songs.json`.
- Синхронизированы обновлённые `click.wav` и `cues.wav` в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Cheri, Cheri Lady/`).
- Обновлены `wiki/songs/cheri-cheri-lady.md`, `wiki/gigs/2026-10-24-lefkara.md`, `wiki/index.md`.

## [2026-10-08] cues & tooling | Brother Louie: cues "verse in" на куплет 2 и "short chorus ready go" на Chorus 3 + инструмент расчёта секций JamZone

1. **Brother Louie — Cues на Verse 2 и Chorus 3:**
   - По запросу Alex рассчитаны и добавлены две подсказки:
     1. `{"bar": 50, "text": "verse in"}` (render 110.092s, snap 105.688s) — вступление куплета 2 («Stay, 'cause this boy wants to gamble…»).
     2. `{"bar": 89, "beat": 4, "text": "short chorus ready go"}` (render 197.615s, snap 193.211s) — вступление перед затактом укороченного припева Chorus 3: сдвинуто на 1 долю раньше (такт 89 доля 4 вместо 90.1), так что слова «short» (88.4), «chorus» (89.1), «ready» (89.2), «go» (89.3) звучат ДО затакта «Bro-ther» (89.4), а на 90.1 вступает даунбит припева «Louie, Louie…».
   - Выполнен перерендер через `jamzone_render.py "Brother Louie"`: обновлены `mix.json`, `cues.wav`, `cue_preview.mp3`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, practice-миксы, web-стемы и `web/songs.json`.
   - Обновлены `wiki/songs/brother-louie.md` и `wiki/index.md`.

2. **Инструмент мгновенного расчёта секций JamZone (`jamzone_sections.py` / `--sections`):**
   - Чтобы не тратить время на написание разовых скриптов расшифровки метаданных JamZone, в `tools/jamzone/jamzone_render.py` добавлен флаг `--sections`, а также создан CLI-хелпер `tools/jamzone/jamzone_sections.py "<song>"`.
   - Мгновенно (<0.2с) расшифровывает `structure.json` и `tiles.json`, сопоставляет с сеткой песни и выводит единую таблицу:
     - `stem_t` — секунды исходных стемов JamZone;
     - `render_t` (`abs_sec`) — **точное время в отрендеренном аудио** с автоматическим учётом оффсета клика (`OFF` / count-in lead из `timeline.json`);
     - `Logic ruler` — позиция такт.доля на линейке Logic Pro;
     - `mix.json` — точные `bar` и `beat` от сильной доли ($t=0$ стемов);
     - готовый сниппет cue для вставки в `mix.json` (`{"bar": N, "text": "..."}`);
     - превью первой вокальной фразы секции из `tiles.json`.
   - Правила зафиксированы в `CLAUDE.md` и `AGENTS.md`.

## [2026-10-09] setlist & render | 24.10 Lefkara: расширение программы до 27 песен, распаковка 12 новых треков из JamZone, секционные cues и полный рендер

- **Обновление сетлиста Лефкары:** список утверждён в едином порядке из 27 песен:
  1. Stayin’ Alive (Bee Gees, 1977)
  2. Heart of Glass (Blondie, 1978)
  3. I Will Survive (Gloria Gaynor, 1978)
  4. YMCA (Village People, 1978)
  5. Hot Stuff (Donna Summer, 1979)
  6. Gimme! Gimme! Gimme! (ABBA, 1979)
  7. Sarà perché ti amo (Ricchi e Poveri, 1981)
  8. I Love Rock ‘n’ Roll (Joan Jett, 1981)
  9. Felicità (Al Bano & Romina Power, 1982)
  10. Mamma Maria (Ricchi e Poveri, 1982)
  11. It’s Raining Men (The Weather Girls, 1982)
  12. Maniac (Michael Sembello, 1983)
  13. Sweet Dreams (Eurythmics, 1983)
  14. Girls Just Want to Have Fun (Cyndi Lauper, 1983)
  15. What a Feeling (Irene Cara, 1983)
  16. Ghostbusters (Ray Parker Jr., 1984)
  17. You’re My Heart, You’re My Soul (Modern Talking, 1984)
  18. Holding Out for a Hero (Bonnie Tyler, 1984)
  19. Cheri Cheri Lady (Modern Talking, 1985)
  20. Brother Louie (Modern Talking, 1986)
  21. Venus (Shocking Blue, 1986 — подтверждена готовая версия)
  22. I Wanna Dance with Somebody (Whitney Houston, 1987)
  23. The Best (Tina Turner, 1989)
  24. Sunny (Boney M., 1976)
  25. Money, Money, Money (ABBA, 1976)
  26. Stumblin’ In (Chris Norman & Suzi Quatro, 1978)
  27. What Is Love (Haddaway, 1993)

- **12 новых треков извлечены из JamZone HQ:**
  `Gimme! Gimme! Gimme!`, `I Love Rock 'n' Roll`, `Felicità`, `Mamma María`, `Girls Just Want to Have Fun`, `What a Feeling`, `Holding Out for a Hero`, `I Wanna Dance with Somebody`, `The Best`, `Sunny`, `Money, Money, Money`, `What Is Love`.
  Для каждого трека:
  - Исключена перкуссия (Claps, Tambourines, Congas, Timpani, Marimba и т.д.) — играет барабанщик Стив.
  - Бас живой (`pb-bass: null`) — играет Рома.
  - Собраны `pb-other` (клавиши, синты, FX, духовые, струнные, бэк-вокал), назначены `players`.
  - При дрейфе сетки >8мс автоматически включён `"click": "follow"`.

- **Секционные подсказки (Cues) расставлены по правилам группы:**
  - Интро: `playback in` при игре плейбека без бэнда (*What a Feeling, Gimme Gimme Gimme, Money Money Money, What Is Love, It's Raining Men, You're My Heart, Maniac, Sweet Dreams, Sara perche*).
  - Первые куплеты: `verse in` выставлен строго на долю затакта (pickup) там, где фраза идёт из-за такта (*Stayin' Alive bar 7.4, Gimme Gimme Gimme bar 19.4, Felicità bar 13.4, Mamma Maria bar 6.4, Sunny bar 13.4, The Best bar 5.4, Money Money Money bar 7.4, What a Feeling bar 7.4, Maniac bar 18.4, Hot Stuff bar 17.4*).
  - Инструменталы и брейки: `{section} in ready go` и обязательный cue на следующую секцию при выходе из них.
  - Финалы: `end in` / `end fill in` (`count: true` $\to$ «end in 3 · 3 2 1»).
  - Существующие песни с >2 подсказками (*Heart of Glass, Ghostbusters, Venus, Stumblin' In, Cheri Cheri Lady, Brother Louie*) сохранены без изменений.

- **Рендер и синхронизация:**
  - Все 27 песен полностью отрендерены через `jamzone_render.py` (`click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, practice-миксы, web-стемы).
  - Обновлён `tools/setlist_dashboard.py` (единый сет Лефкары из 27 треков в точном порядке), перегенерирован `web/songs.json` (74 трека с полными данными и плеером).
  - Созданы 12 wiki-страниц в `wiki/songs/`, обновлены `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md`.

## [2026-10-09] lyrics | 24.10 Lefkara: сценические тексты (клипы 44–61) для остальных 18 песен программы

По запросу Alex созданы сценические тексты и видеоклипы для вокального монитора на все остальные 18 песен программы Лефкары:
- Сгенерированы сценические субтитры ASS (`clips/44.ass` .. `clips/61.ass`) и фоновые видео MP4 (`clips/44.mp4` .. `clips/61.mp4`).
- Экспортированы тайм-кодированные TSV-таблицы в `tools/lyric-launcher/lyrics-timed/44.tsv` .. `61.tsv` с точным смещением `offset_sec` под финальный таймлайн плейбека.
- Для `Bee Gees — Stayin' Alive` (clip 44) выполнена транскрипция через `mlx-whisper` с привязкой слов к вокальному стему.
- Для остальных 17 песен (clips 45–61) тексты и тайминги извлечены напрямую из JamZone `tiles.json`.
- В `tools/lyric-launcher/songs.tsv` зарегистрированы 18 новых строк (клипы 44–61, Program Change 45–62).
- Все клипы (ASS, MP4) и обновлённый манифест доставлены в репозиторий рига (`cherry-daddies-2000`).

## [2026-10-09] sync & rules | 24.10 Lefkara: синхронизация аудио-плейбеков (18 песен) в риг и фиксация правила синка

По запросу Alex:
- **Все 18 недостающих песен программы Лефкары скопированы и запушены в репо рига (`cherry-daddies-2000`):**
  - Папки в `cherry-daddies-setlist-2026-06-16/` (`Stayin' Alive`, `I Will Survive`, `YMCA`, `Gimme! Gimme! Gimme!`, `I Love Rock 'n' Roll`, `Felicità`, `Mamma María`, `It's Raining Men`, `Maniac`, `Girls Just Want to Have Fun`, `What a Feeling`, `You're My Heart, You're My Soul`, `Holding Out for a Hero`, `I Wanna Dance with Somebody`, `The Best`, `Sunny`, `Money, Money, Money`, `What Is Love`).
  - Для каждой песни скопированы боевые стемы: `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav`.
  - Все изменения закоммичены и отправлены в remote `origin/main` рига. Теперь **все 27 песен Лефкары имеют полные плейбеки в риге**.
  - Дополнительно через `tools/sync_to_mainstage.sh --apply` синхронизированы свежие рендеры для ранее загруженных песен (*Ghostbusters, Cheri Cheri Lady, Stumblin' In, Sarà perché ti amo, Brother Louie, Rock & Roll Queen*).
- **Обновлён `tools/sync_to_mainstage.sh`:**
  - В таблицу `MAP` добавлены все 18 новых песен Лефкары (всего 65 песен в маппинге).
  - Добавлен флаг `--create-missing` для инициализации папок новых песен при необходимости.
- **Зафиксировано железное правило группы в `CLAUDE.md` и `AGENTS.md`:**
  - **«Синк песен в риг» ВСЕГДА означает, что аудио-рендеры (плейбеки/стемы) скопированы, закоммичены и ЗАПУШЕНЫ в origin/main рига.**
  - Отправка одних только lyrics без аудио-плейбеков никогда не считается синком песни в риг.

## [2026-10-10] setlist | 24.10 Lefkara: исключение Joan Jett, Cyndi Lauper, What Is Love и Sweet Dreams из программы (23 песни)

По результатам ревью репертуара и задач из локального дашборда:
- Из сетлиста Лефкары исключены 4 песни:
  1. `Joan Jett — I Love Rock 'n' Roll` (задача `убрать`)
  2. `Cyndi Lauper — Girls Just Want to Have Fun` (задача `remove song`)
  3. `Haddaway — What Is Love`
  4. `Eurythmics — Sweet Dreams (Are Made of This)`
- В локальной базе веб-дашборда (`web/data/dashboard.db` через `/api/state`) задачи отмечены как выполненные (`done: true`).
- Обновлён `tools/setlist_dashboard.py` (программа уменьшена до 23 треков), перегенерирован `web/songs.json`.
- Обновлены `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md`.

## [2026-10-10] cues & mix | Maniac: уточнение cues и мьют synth keys 2 до Chorus 3

По запросу Alex выполнен рефайн аранжировки и подсказок в `Michael Sembello — Maniac`:
1. **Мьют `09_Synth_Keys_2` в `pb-other` до Chorus 3:**
   - В `mix.json` добавлена секция `"mute": {"09_Synth_Keys_2": [[1, 141]]}`.
   - Лид-партию синта до такта 141 играет гитара (Alex); на Chorus 3 (такт 141) гитара продолжает играть соло, и `09_Synth_Keys_2` вступает в плейбеке с такта 141 до конца песни.
2. **Первый cue изменён на барабаны:**
   - `"Maniac drums in"` на `bar 3.1` (3.040s) вместо `playback in`, точно совпадает с первым ударом кика барабанов (3.044s в `pb-drums`).
3. **Нормализация темпа cue («verse in goes too slow»):**
   - Убран глобальный `"cue_step": 2`, возвращён дефолтный темп 1 слово на долю (`step: 1`).
   - Блок «verse in ready go» звучит в ровном темпе (по слову на четверть), событие строго на 4-й доле 18 такта (`bar 18 beat 4`, 26.860s), куда попадает вокальный вход Тани («Just a...»).
4. **Добавлен cue для секции Bridge JamZone:**
   - `"bridge in"` на `bar 101.1` (150.970s).
5. **Добавлен cue для секции Pre chorus 3 JamZone:**
   - `"prechorus in"` на `bar 133.1` (199.270s, ~3:15–3:20 JZ time).
6. **Полный ре-рендер трека:**
   - `python3 tools/jamzone/jamzone_render.py "Flashdance (Michael Sembello) - Maniac"` перегенерировал `click.wav`, `cues.wav`, `pb-other.wav`, `pb-drums.wav`, `all.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, practice-миксы.
   - Обновлены `web/songs.json`, `wiki/songs/maniac.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`, `tools/jamzone/setup_lefkara_27.py`.
- Суммарная длительность чистых плейбеков программы Лефкары теперь составляет **1ч 37м 11с** (5,830.85 с).

## [2026-10-10] cues | It's Raining Men: обновление подсказок по JamZone сетке (16 cues)

По запросу Alex актуализирован набор cue для `The Weather Girls — It's Raining Men`:
- Сохранены стартовые подсказки: `bar 1.1` (3.440s, `It's Raining Men playback in`) и `bar 3.1` (6.880s, `all in`).
- `0:35 cue`: заменён на `bar 19.1` (35.040s) — `pre-verse in` («pre-verse in ready go»).
- `JZ section Verse`: добавлен `bar 27.1` (49.100s) — `verse in` («verse in ready go»).
- `JZ 01:14 (down beat)`: добавлен `bar 43.1` (77.270s, stem 74.49s) — `stop` («stop in 3 · 3 2 1») перед а капелла фразой «It's raining men».
- `~1:33 our time`: добавлен `bar 52.1` (93.040s, snap 89.108s) — `stop` («stop in 3 · 3 2 1») на последний удар барабанов перед стопом на аккорде C в Chorus 1.
- `JZ section Bridge`: добавлен `bar 62.1` (110.580s) — `bridge in` («bridge in ready go»).
- `JZ 02:18 (C chord)`: добавлен `bar 79.1` (140.400s, stem 137.62s) — `stop` («stop in 3 · 3 2 1») на аккорд C.
- `JZ Break section`: добавлен `bar 91.1` (161.430s) — `break in ready go`.
- `JZ section Bridge 2`: добавлен `bar 109.1` (192.970s) — `bridge-2 in` («bridge-2 in ready go»).
- `JZ ~03:40 (C chord)`: добавлен `bar 126.1` (222.730s, stem 219.95s) — `stop` («stop in 3 · 3 2 1») на аккорд C.
- `JZ section Verse 2`: добавлен `bar 129.1` (227.990s) — `verse in` («verse in ready go»).
- `JZ ~04:25 (C chord)`: добавлен `bar 152.1` (268.270s, stem 265.49s) — `stop` («stop in 3 · 3 2 1») на аккорд C.
- `JZ 04:51`: добавлен `bar 167.1` (294.520s, stem 291.74s) — `keep going` (raw).
- `JZ section Outro`: добавлен `bar 177.1` (312.000s) — `outro in` («outro in ready go»).
- `JZ 05:23 down beat`: добавлен `bar 185.1` (326.020s, stem 323.24s) — `end in` (`count: true` → «end in 3 · 3 2 1») на финальный удар.
Выполнен локальный рендер через `jamzone_render.py "It's Raining Men"`: обновлены `mix.json`, `click.wav`, `cues.wav`, `pb-other.wav`, `pb-drums.wav`, `all.wav`, `cue_preview.mp3`, `pb-other.mp3`, `pb-drums.mp3`, practice-миксы, стемы и `web/songs.json`.

## [2026-10-10] cues | Stayin' Alive: добавлены секционные подсказки (Verse 3, Instrumental 3, Bridge-2..5) и исправлен финал (на 2 доли раньше)

По запросу Alex обновлены cues для `Bee Gees — Stayin' Alive` (cat_5447):
- Добавлены недостающие подсказки по секциям JamZone и аутро-циклам:
  - `bar 60.1` (137.143s, snap 132.571s) — `verse in ready go` (куплет 3, JamZone секция Verse 3, ~02:16);
  - `bar 79.1` (180.571s, snap 176.000s) — `main in ready go` (главная гитарная тема 3, JamZone секция Instrumental 3, ~02:56);
  - `bar 81.1` (185.143s, snap 180.571s) — `bridge-2 in ready go` (JamZone секция Outro, вход бриджа 2 «Life goin' nowhere...», ~03:02);
  - `bar 92.1` (210.286s, snap 205.714s) — `bridge-3 in ready go` (бридж 3, +11 тактов от bridge-2, ~03:28);
  - `bar 103.1` (235.429s, snap 230.857s) — `bridge-4 in ready go` (бридж 4, +11 тактов от bridge-3, ~03:53);
  - `bar 114.1` (260.571s, snap 256.000s) — `bridge-5 in ready go` (бридж 5, +11 тактов от bridge-4, ~04:18);
- Исправлен финальный cue: сдвинут строго на 2 доли раньше с такта 125.1 на сильный хит такта 124.3:
  - `bar 124.2` (284.000s, snap 278.857s) — `end in` (`count: true` $\to$ «end in 3 · 3 2 1»); отсчёт звучит на 123.3 (3), 123.4 (2), 124.1 (1), на 124.2 отсчёт завершён на финальный крэш/аккорд.
- Всего 13 cue. Выполнен полный локальный рендер через `jamzone_render.py "Stayin' Alive"`:
  - Обновлены `mix.json`, `click.wav`, `cues.wav`, `all.wav`, `cue_preview.mp3`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, practice-миксы, web-стемы.
  - Актуализирован `web/songs.json`, обновлены `wiki/songs/stayin-alive.md`, `wiki/index.md`.

## [2026-10-10] edit | YMCA: вырезано всё ритмическое интро до вступления духовых (cut_bars [3, 11]), трек начинается сразу с темы духовых

По запросу Alex для `Village People — YMCA` (cat_6926):
- В `music/songs/Village People - Y.M.C.A./mix.json` установлен параметр `"cut_bars": [3, 11]`:
  - Физически вырезаны 8 вступительных тактов ритм-секции (такты 3–10, 15.34 с) до вступления духовых;
  - Теперь после 2 тактов прекаунта банда на 3 такте (`YMCA all in`) вступает сразу с культовой темы духовых (`09_Brass_section`), без предварительного гитарного грува.
- Актуализирован список подсказок в `mix.json`:
  - `bar 3.1` (3.920s) — `YMCA all in` («YMCA all in ready go», вступление банды сразу с духовыми);
  - `bar 9.1` (15.370s) — `verse in` («verse in ready go», куплет 1, сдвинут на 1 долю раньше под затакт вокала);
  - подсказки на 0:49 (припев 1) удалена по запросу;
  - `bar 111.1` (208.180s = 03:28) — `instrumental in ready go` (секция Instrumental JamZone, с учётом вырезки 8 тактов интро, на 1 долю раньше на даунбит такта 111);
  - `bar 119.1` (223.310s = 03:43) — `chorus in ready go` (секция Chorus 4 JamZone, с учётом вырезки 8 тактов интро, на 1 долю раньше на даунбит такта 119);
  - `bar 147.1` (276.060s) — `end in` (`count: true` → «end in 3 · 3 2 1», финал).
- Выполнен полный рендер через `jamzone_render.py --practice`:
  - Обновлены `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `timeline.json`, practice-миксы для Roma, Steve, Tanya, Alex и web-стемы.
  - Длина рендера сократилась с 296.75 с до 281.63 с (149 тактов).
- Синхронизированы сценические lyrics:
  - `tools/lyric-launcher/lyrics-timed/46.tsv` сдвинут на -15.34 с под новый таймлайн;
  - Пересобраны `clips/46.ass` и `clips/46.mp4`.
- Рендеры синхронизированы в риг MainStage (`cherry-daddies-2000`):
  - `cherry-daddies-setlist-2026-06-16/YMCA/`: `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav`;
  - `lyrics/clips/`: `46.ass`, `46.mp4`.
- Актуализирован `web/songs.json`, обновлены страницы вики `wiki/songs/ymca.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-10] cues & edit | Gimme! Gimme! Gimme!: рефайн подсказок, вырезка соло (такты 87–132, переход из Chorus 3 сразу в Outro)

По запросу Alex для `ABBA — Gimme! Gimme! Gimme! (A Man After Midnight)` (cat_9159):
- Из плейбека исключены все гитары (`06_Electric_Guitar_(clean)` и `07_Electric_Guitar`) — Alex играет гитарные партии живьём.
- Выполнен рефайн подсказок:
  - Стартовый cue: заменён с «playback in» на `Gimme Gimme Gimme guitar in` (`bar 2.1`, 4.472s);
  - `drums in`: перенесён раньше на такт `10.2` (21.722s) — привязан строго к первому удару барабанного сбива Стива;
  - `verse in`: сдвинут на 1 долю раньше с 19.4 на `19.3` (40.352s) — ровно под вокальный затакт Тани «Half past twelve»;
  - Добавлен cue на секцию Intro 2: `bar 43.1` (87.822s) — `intro in ready go` (вступление риффа, 1:27.8);
  - Добавлен cue на секцию Verse 2: `bar 53.3` (108.742s) — `verse in ready go` (ровно под затакт «Movie stars», 1:48.7);
  - Добавлен cue на финальные припевы: `bar 69.1` (140.062s) — `chorus in ready go` (вход в Chorus 4 после Pre-chorus 3);
  - Финальный cue: `bar 97.1` (195.642s) — `end in` (`count: true` $\to$ «end in 3 · 3 2 1»).
- Вырезка середины песни (`cut_bars: [63, 111]`):
  - По скриншоту из JamZone из трека вырезан весь выделенный блок (48 тактов, 96.38 с): Pre-chorus 2, Chorus 2, Chorus 3 и Instrumental;
  - После Verse 2 («...no one in sight») трек сразу переходит в Pre-chorus 3 («There's not a soul out there...»), далее звучат финальные Chorus 4 и Chorus 5 и нативное Outro;
  - В результате нет затянутости (устранены 4 припева подряд), идеальная песенная форма (2 куплета, 2 припевных блока) и естественный финальный fade/рифф;
  - Длина рендера составляет 201.08 с (3:21, 100 тактов).
- Синхронизированы сценические lyrics:
  - В `tools/lyric-launcher/lyrics-timed/47.tsv` удалены вырезанные Pre-chorus 2 и Choruses 2-3, финальные секции сдвинуты на -96.38 с;
  - Пересобраны `clips/47.ass` и `clips/47.mp4`.
- Выполнен полный рендер через `jamzone_render.py --practice`:
  - Обновлены `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `timeline.json`, practice-миксы для Roma, Steve, Tanya, Alex и web-стемы.
  - Рендеры синхронизированы в риг MainStage (`cherry-daddies-2000`).
- В локальной базе веб-дашборда (`web/data/dashboard.db`) закрыты соответствующие задачи по Gimme (`learn guitar intro and remove guitar part`, `remove solo part`, `end cue is not right`).
- Актуализирован `web/songs.json`, обновлены `wiki/songs/abba-gimme-gimme-gimme.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-10] cues | Cheri, Cheri Lady: добавлены 5 подсказок ("verse in", "melody in" ×3, "chorus in")

По запросу Alex для `Modern Talking — Cheri, Cheri Lady` (cat_37357, 114 BPM) добавлены 5 подсказок:
- `bar 35.1` (73.684s, snap 69.474s, Logic 36.1) — `melody in` («melody in ready go» на клавишную тему `10_Synth_Brass` на 01:20 в JamZone);
- `bar 42.4` (90.000s, snap 85.789s, Logic 43.4) — `verse in` («verse in ready go» под вокальный затакт «I get up» на 4-й доле перед Verse 2 на 01:37 в JamZone);
- `bar 74.1` (155.790s, snap 151.579s, Logic 74.5) — `melody in` («melody in ready go» на клавишную тему `10_Synth_Brass` / `08_Synth_Keys_3` на 02:42 в JamZone);
- `bar 81.3` (171.579s, snap 167.368s, Logic 82.3) — `chorus in` («chorus in ready go» под вокальный затакт «Che-ri» на 3-й доле перед Chorus 3 на ~2:58 в JamZone);
- `bar 98.1` (206.316s, snap 202.105s, Logic 99.1) — `melody in` («melody in ready go» на клавишную тему на Outro на 03:32 в JamZone).

Итого в сетке 8 cues:
1. `bar 2.1` (4.211s) — `Cheri Cheri Lady all in`
2. `bar 5.4` (12.105s) — `verse in`
3. `bar 35.1` (73.684s) — `melody in`
4. `bar 42.4` (90.000s) — `verse in`
5. `bar 74.1` (155.790s) — `melody in`
6. `bar 81.3` (171.579s) — `chorus in`
7. `bar 98.1` (206.316s) — `melody in`
8. `bar 105.1` (221.053s) — `end fill in` (`count: true`)

В `tools/jamzone/jamzone_render.py` исправлен расчёт секций JamZone (`_dump_jamzone_sections` / `--sections`): теперь смещение `cut_bars` корректно учитывается при сопоставлении секций с таймлайном рендера и нумерацией тактов.
Выполнен полный рендер через `jamzone_render.py --practice`, обновлены `cues.wav`, `cue_preview.mp3`, `timeline.json`, practice-миксы и `web/songs.json`.
Обновлённые `click.wav` и `cues.wav` синхронизированы в риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Cheri, Cheri Lady/`).

## [2026-10-10] cues | Sarà perché ti amo: рефайн подсказок

По запросу Alex для `Ricchi e Poveri — Sarà perché ti amo` (cat_18179):
- Обновлены голосовые подсказки (cues):
  - Интро: заменён с «Sara perche playback in» на `Ti amo all in ready go` (`bar 3.1`, 3.978s) — вступление группы после 2 тактов precount;
  - Куплет: заменён с «verse in» на `voice-only verse ready go` (`bar 11.1`, 19.891s) — вход в куплет без ударных и баса;
  - Добавлен cue на первый drum kick: `kick in ready go` (`bar 17.1`, 31.826s, ~00:32) — привязан строго к первому удару бочки на такте 17;
  - Добавлен cue на вступление ритм-секции: `all in ready go` (`bar 19.1`, 35.805s, ~00:36) — вход в Verse 2 («Lo canto al ritmo...»);
  - JamZone Intro 2: заменён с «main in ready go» на `instrumental in ready go` (`bar 59.1`, 115.370s);
  - Сохранены `chorus in ready go` (`bar 67.1`, 131.283s) и финальный `end fill in` (`bar 91.1`, 179.023s, «end fill in 3 · 3 2 1»).
- Выполнен рендер через `jamzone_render.py --practice`:
  - Обновлены `mix.json`, `cues.wav`, `click.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, practice-миксы (roma, steve, tanya) и web-стемы.
- Актуализированы `tools/jamzone/setup_lefkara_27.py`, `web/songs.json`, `wiki/songs/sara-perche-ti-amo.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-10] cues & playback | Mamma María: рефайн подсказок и бэк-вокалы в припевах

По запросу Alex для `Ricchi e Poveri — Mamma María` (cat_82836):
- Обновлены голосовые подсказки (cues):
  - Verse 1: сдвинут на 1 долю позже — с `bar 6.4` (10.251s) на `bar 7.1` (10.697s, `verse in ready go`);
  - Припев 0:39: удалён cue припева (`bar 23.1`, 39.223s, `chorus in`);
  - Модуляция в D (~01:08 JamZone): добавлен cue на даунбит аккорда D `bar 39.1` (67.749s, `modulation in ready go`);
  - JamZone Instrumental: привязан строго к даунбиту секции `bar 55.1` (96.275s) с текстом `instrumental in ready go` (вместо старого «main in ready go» на 54.4);
  - JamZone Verse 3 (после Instrumental): привязан к даунбиту секции `bar 67.1` (117.669s) с текстом `verse in ready go` (вместо старого 66.4);
  - На стыке Chorus 3 → Chorus 4 (~02:25 JamZone): добавлен cue `bar 83.1` (146.195s) — `keep going`;
  - Финальный cue: исправлен с ложного 02:39 (bar 90.3 перед аутро) на реальный финал трека `bar 107.1` (188.983s, ~03:09 JamZone) — `end in` (`count: true` → «end in 3 · 3 2 1» с ударом на 03:09).
- Добавлены бэк-вокалы в плейбек (`pb-other`):
  - JamZone не экспортирует отдельную дорожку бэк-вокала, но содержит 3 дорожки лид-вокала оригинального состава (`09_Lead_Vocal_Angela_Brambati`, `10_Lead_Vocal_Angelo_Sotgiu`, `11_Lead_Vocal_Franco_Gatti`);
  - Все 3 вокальные дорожки подключены в `pb-other` с ролью `back-vox` (автоуровень по целевому потолку -23 dBFS: Angela -5.6dB, Angelo -5.7dB, Franco 0.0dB) и мьютом вне припевов JamZone: `mute: [[1, 23], [31, 47], [55, 75], [91, 109]]`;
  - В куплетах (Verse 1, Verse 2, Verse 3), интро, инструментале и аутро вокал в плейбеке полностью заглушен (поёт вживую вокалистка Таня), а в припевах (Chorus 1, Chorus 2, Chorus 3, Chorus 4) звучит полноценная 3-голосная вокальная пачка;
  - Электрогитары (`04_Electric_Guitar_(left)`, `05_Electric_Guitar_(right)`) убраны из плейбека `pb-other` (играет Алекс вживую).
- Выполнен рендер через `jamzone_render.py --practice`:
  - Обновлены `mix.json`, `cues.wav`, `click.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `timeline.json`, practice-миксы (steve, roma, tanya, alex) и web-стемы.
- Актуализированы `tools/jamzone/setup_lefkara_27.py`, `web/songs.json`, `wiki/songs/ricchi-e-poveri-mamma-maria.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.
- Свежие рендеры синхронизированы и запушены в риг MainStage (`cherry-daddies-2000`): `Mamma María` (`cues.wav`, `pb-other.wav`), `Maniac` и `Holding Out for a Hero`.
- Выполнен деплой дашборда на Vercel (`https://web-ten-psi-12.vercel.app`) и R2-синк обновлённых аудио.

## [2026-10-10] cues & mix | Maniac: cue main in (0:15), мьют ведущего синта в pre-chorus, chorus in на 1 долю раньше (3:31)

По запросу Alex выполнен второй цикл рефайна `Michael Sembello — Maniac`:
1. **Cue на ~0:15 обновлён на `guitar in`:**
   - `bar 11.1` (15.120s, snap 12.101s) — `guitar in ready go` (вход соло/темы гитары Alex вместо общего «main in»).
2. **Synth Keys 1 (`08_Synth_Keys_1`) оставлен в плейбеке:**
   - По указанию Alex синт `08_Synth_Keys_1` звучит во всех предприпевах (Pre-chorus 1, 2, 3) и бридже, создавая необходимую гармоническую основу. Заглушен только `09_Synth_Keys_2` до Chorus 3 (`[1, 141]`).
3. **Сдвинут cue припева Chorus 3 (~3:31) на 1 долю раньше:**
   - Перенесён с `bar 141.1` на `bar 140.4` (210.990s, snap 207.971s) ровно под вокальный затакт Тани («She's a...»);
   - Сам синт `09_Synth_Keys_2` вступает со 141 такта (211.28s, даунбит Chorus 3) и звучит до конца песни.
4. **Добавлен cue `longer here` на ~1:27:**
   - `bar 59.1` (87.590s, snap 84.571s) — 2-тактовый инструментальный тернараунд после Chorus 1 перед Verse 2.
5. **Fade out плейбека за 4 доли после финального удара:**
   - В `mix.json` настроен `"fade_out": {"from_bar": 171, "from_beat": 1, "to_bar": 172, "to_beat": 1}` — плавное линейное затухание за 4 доли (1.51 с) с 256.620s до 258.129s.
   - Задействован `"cut_after_last_cue": 2`, убирающий лишний хвост тишины после завершения фейда.
6. **Ре-рендер и синк:**
   - Выполнен полный рендер через `jamzone_render.py "Flashdance (Michael Sembello) - Maniac"`.
   - Обновлены `mix.json`, `cues.wav`, `click.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `web/songs.json`.
   - Свежие `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav` скопированы в риг MainStage через `tools/sync_to_mainstage.sh --apply "Maniac"`.
   - Обновлены `wiki/songs/maniac.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`, `tools/jamzone/setup_lefkara_27.py`.

## [2026-10-10] cues & click | What a Feeling: выравнивание темпа клика интро (92 BPM) и полный рефайн подсказок
766: 
767: По запросу Alex для `Irene Cara — What a Feeling` (cat_10091):
768: 1. **Выравнивание темпа клика интро:**
769:    - Ранее synthetic count-in клики спереди генерировались по глобальному усреднённому темпу `beat = 120.7 BPM`, тогда как реальное интро песни идёт в медленном темпе 92.0 BPM (`bt[1] - bt[0] = 0.652s`), из-за чего клик интро казался неестественно быстрым до вступления стемов.
770:    - В `tools/jamzone/jamzone_render.py` для `follow` режима введено отсчитывание `b_intro` (темп вступительных тактов) для шага pre-lead кликов, расчета `lead` и `sec_to_idx`: клики спереди теперь тикают строго назад от даунбита на тех же 92.0 BPM с акцентом на сильную долю.
771:    - Также в `_dump_jamzone_sections` добавлена поддержка `sec_to_idx` для точного маппинга секций переменного темпа на реальные такты.
772: 2. **Обновление подсказок (cues):**
773:    - Первый cue: заменён с «playback in» на `"What a Feeling guitars in"` (`bar 2.1`, 5.218s);
774:    - Verse 1: сдвинут с 0:19 (`bar 7.4`) на точный даунбит секции Verse в JamZone `bar 6.1` (15.652s, ~0:13 JZ time, «First when there's nothing...»);
775:    - Вход барабанов / разгон темпа: добавлен `"all in"` на `bar 20.1` (52.098s, ~0:51 render time, первый кик на click #76);
776:    - Удалены старые ошибочные cues: `1:03 all in` (старый bar 26.1), `1:57 main` (старый bar 54.2), `2:13 verse in` (старый bar 62.2), `3:29 end in` (старый bar 101.4);
777:    - Первая секция Instrumental JamZone: добавлен `"solo in ready go"` на `bar 48.1` (106.379s, соло гитары Alex);
778:    - Вокал под затакт «Now» (~1:58 JZ time): добавлен `"vocal in"` на 4-ю долю такта 55 (`bar 55.4`, 121.403s), «ready go» звучит до слова «Now»;
779:    - Вторая секция Instrumental JamZone: добавлен `"bridge in"` на `bar 80.1` (168.414s);
780:    - Последний припев Chorus 3 (~03:02 JZ time): добавлен `"chorus variation ready go"` на `bar 88.1` (183.923s);
781:    - Секция Outro JamZone: добавлен `"outro in ready go"` на `bar 96.1` (199.432s);
782:    - Аутро ~3:33 JZ time: добавлен cue продолжения `"keep going"` на `bar 104.1` (214.941s);
783:    - Финал трека ~03:52 JZ time: добавлен `"end in"` (`count: true` $\to$ «end in 3 · 3 2 1») на финальный аккорд Gm на `bar 114.1` (234.327s).
784: 3. **Ре-рендер трека:**
785:    - Выполнен полный рендер через `jamzone_render.py "Flashdance (Irene Cara) - What a Feeling"`.
786:    - Обновлены `mix.json`, `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `web/songs.json`.
787:    - Обновлены `wiki/songs/what-a-feeling.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`, `tools/jamzone/setup_lefkara_27.py`.

## [2026-10-10] setlist | 24.10 Lefkara: исключение Whitney Houston и Money, Money, Money из программы (21 песня)

По запросу Alex из сетлиста Лефкары исключены 2 песни:
1. `Whitney Houston — I Wanna Dance with Somebody (Who Loves Me)`
2. `ABBA — Money, Money, Money`

- Обновлён `tools/setlist_dashboard.py` (программа сокращена до 21 трека).
- Перегенерирован `web/songs.json` (`python3 tools/setlist_dashboard.py`).
- Обновлены страницы `wiki/gigs/2026-10-24-lefkara.md`, `wiki/index.md`, а также `wiki/songs/whitney-houston-i-wanna-dance-with-somebody.md`, `wiki/songs/abba-money-money-money.md`, `wiki/songs/tina-turner-the-best.md`, `wiki/songs/boney-m-sunny.md`, `wiki/songs/stumblin-in.md`.

## [2026-10-10] cues & playback | Holding Out for a Hero: убраны гитары из pb-other, полный рефайн cues (12 подсказок)

По запросу Alex для `Bonnie Tyler — Holding Out for a Hero` (cat_13868):
1. **Гитары убраны из плейбека (`pb-other`):**
   - Дорожки `05_Electric_Guitar_(left)` и `06_Electric_Guitar_(right)` удалены из `pb-other.stems` — Alex играет их вживую на гитаре.
   - В `pb-other` оставлены: `07_Electric_Guitar`, `08_Piano`, `09_Synth_Strings`, `10_Arpeggiator`, `11_Brass_section`, `12_Backing_Vocals`.
2. **Обновлены голосовые подсказки (cues):**
   - Стартовый cue (`bar 3.1`, 3.208s): заменён на `"Holding Out for a Hero drum-base in"` («Holding Out for a Hero drum-base in ready go»). Слово «drum-base» ровно укладывается в 1 долю (в отличие от «drum-n-bass», растягивавшегося на 3 доли), что убрало лишний пустой pre-lead такт и вернуло чистый таймлайн;
   - Секция Intro 2 (JamZone): добавлен cue `"intro in"` на `bar 55.1` (88.206s);
   - Секция Verse 2 (~1:40 JZ time): добавлен cue `"verse in"` на `bar 63.1` (101.036s);
   - Старый ошибочный cue `2:40 main in ready go` на такте 101.2 удалён;
   - Секция Instrumental (JamZone): добавлен cue `"bridge in"` на `bar 101.1` (161.978s);
   - Секция Bridge (JamZone): добавлен cue `"voice in"` на `bar 117.1` (187.551s) ровно на вход вокала Тани («Up where the mountains...»);
   - Секция Chorus 1 (1:00): сдвинут на 2 доли раньше с такта 39 на `bar 38 beat 3` (`bar 38.3`, 60.140s), чтобы отсчёт завершался точно перед затактом «I need a hero» (60.5s);
   - Секция Chorus 4 (~03:39 JZ time): сдвинут на 2 доли позже с такта 137.2 на `bar 137 beat 4` (`bar 137.4`, 219.128s), слово «go» звучит на 03:39.04 точно на слове «I» лид-вокала во фразе «I need a hero»;
   - Переход в Chorus 5 (~4:04 JZ time): добавлен cue `"keep going"` на `bar 153.1` (243.568s, сдвинут на 1.5 с раньше с такта 154 ровно на 153 такт);
   - Секция Outro (JamZone): заменён старый countdown на `"outro in ready go"` на `bar 170.1` (272.451s);
   - Четвёртый цикл аутро (~05:08 JZ time): добавлен cue `"keep going"` на `bar 194.1` (310.951s, фраза звучит на такте 193 в 05:08 JZ time);
   - Финальный аккорд (~05:29 JZ time): добавлен счётный финал `"end in"` (`count: true` $\to$ «end in 3 · 3 2 1») на `bar 206.1` (330.201s, финальный удар на 05:29 JZ time).
3. **Ре-рендер трека:**
   - Выполнен полный рендер через `jamzone_render.py --practice`:
     - Сгенерированы `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, practice-миксы (roma, steve, tanya, alex) и web-стемы.
     - Актуализированы `mix.json`, `web/songs.json`, `tools/jamzone/setup_lefkara_27.py`, `wiki/songs/holding-out-for-a-hero.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-10] cues & playback | You're My Heart, You're My Soul: cues all in / melody in / end fill in, lead guitar и lead vocal на припевах в плейбек

По запросу Alex для `Modern Talking — You're My Heart, You're My Soul (Mix '98)` (cat_14066):
1. **Обновлены cues:**
   - Стартовый cue (`bar 2.1`, 4.085s): заменено слово «playback» на «all» $\to$ `You're My Heart · all in ready go` («You're My Heart all in ready go»);
   - На такте `44.3` (90.882s) подсказка изменена с «main in» на `melody in ready go` («melody in ready go», вход мелодической темы синта/инструментала);
   - Финальный cue (`bar 111.1`, 226.703s): изменён с «end in» на `end fill in` (`count: true` $\to$ «end fill in 3 · 3 2 1»).
2. **Лид-электрогитара добавлена в плейбек (`pb-other`):**
   - Дорожка `08_Lead_Electric_Guitar` добавлена в `pb-other.stems` (звучит в Verse 2 и переходе в припев 2);
   - Убрана из партий `players.alex` (`alex` теперь играет живьём `06_Electric_Guitar` и `07_Rhythm_Electric_Guitar`, а в `practice-alex.mp3` слышит лид-гитару плейбека).
3. **Лид-вокал добавлен в плейбек только на припевах:**
   - Дорожка `14_Lead_Vocal` подключена в `pb-other.stems`;
   - Назначена роль `"roles": {"14_Lead_Vocal": "back-vox"}` с автоуровнем по целевому потолку -23 dBFS (-5.1 dB) для идеального баланса с `13_Backing_Vocals`;
   - Настроен мьют вне припевов: `"mute": {"14_Lead_Vocal": [[1, 26], [44, 76], [103, 115]]}`;
   - В куплетах (Verse 1, Verse 2), интро, инструментале и аутро вокал в плейбеке полностью заглушен (поёт живьём Таня), а на припевах (Chorus 1, Chorus 2, Chorus 3) звучит оригинальный мужской голос в пачке с бэками.
4. **Ре-рендер трека:**
   - Выполнен полный рендер через `jamzone_render.py --practice`:
     - Сгенерированы `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, practice-миксы (roma, steve, tanya, alex) и web-стемы.
     - Актуализированы `mix.json`, `web/songs.json`, `tools/jamzone/setup_lefkara_27.py`, `wiki/songs/youre-my-heart-youre-my-soul.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.
   - Свежие `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav` скопированы в риг MainStage через `tools/sync_to_mainstage.sh --apply "You're My Heart"`.

## [2026-10-10] cues & playback | Sunny: вырезано интро плейбека (cut_bars [2, 6]), refine cues, сдвиг lyrics (-8.14s)

По запросу Alex для `Boney M. — Sunny` (cat_5568):
1. **Вырезано плейбек-интро (первые 10 секунд):**
   - Добавлен `"cut_bars": [2, 6]` — вырезаны 4 пустых такта плейбека (8.136s).
   - Трек начинается прямо с отсчёта и стартовой голосовой подсказки `"Sunny, all in ready go"` на `bar 2.1` (4.068s), после чего сразу вступает вся группа.
2. **Обновлены голосовые подсказки (cues) с учётом сдвига тактов (-4 такта):**
   - Стартовый cue: `"Sunny, all in ready go"` на `bar 2.1` (4.068s);
   - Куплет 1 (`verse in`): сильная доля куплета на `bar 10.1` (20.339s);
   - Старые cues удалены: `2:06` (`main in ready go`), `2:38` (`verse in ready go`), `3:07` (`end in`);
   - Секция Verse 3 (01:31 JZ time): добавлен даунбит-cue `"modulation in ready go"` на `bar 42.1` (85.424s);
   - Секция Instrumental (02:04 JZ time): добавлен cue `"instrumental in ready go"` на `bar 58.1` (117.966s);
   - Секция Verse 4 (02:37 JZ time): добавлен cue `"modulation in ready go"` на `bar 74.1` (150.508s);
   - Секция Outro (JamZone): добавлен cue `"outro in ready go"` на `bar 88.1` (178.983s);
   - Финал трека (03:21 JZ time): добавлен счётный финал `"end in"` (`count: true` $\to$ «end in 3 · 3 2 1») на `bar 96.1` (195.254s).
3. **Обновлены тайминги lyrics и видео-клип:**
   - Все строки в `tools/lyric-launcher/lyrics-timed/59.tsv` сдвинуты на -8.14s (4 такта).
   - Пересобран титровый клип: `clips/59.ass` и `clips/59.mp4`.
4. **Ре-рендер трека:**
   - Выполнен полный рендер через `jamzone_render.py "Boney M. - Sunny" --practice`.
   - Обновлены `mix.json`, `click.wav`, `cues.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, practice-миксы (steve, roma, tanya, alex) и `web/songs.json`.
   - Актуализированы `wiki/songs/boney-m-sunny.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`, `tools/jamzone/setup_lefkara_27.py`.
   - Новые плейбеки скопированы в риг MainStage через `tools/sync_to_mainstage.sh --apply "Sunny"`.

## [2026-10-10] cues & playback | Holding Out for a Hero: cue "guitar in", обрезка до 5:30, cue "chorus variation" на 02:32

По запросу Alex для `Bonnie Tyler — Holding Out for a Hero` (cat_13868):
1. **Добавлен голосовой cue для входа гитары:**
   - На сильную долю 7 такта (`bar 7.1`, 9.622s render time) добавлен cue `"guitar in"` («guitar in ready go»), предваряющий вступление гитарных дорожек (отсчёт на 6 такте, вход на даунбит bar 7).
2. **Обрезка всех дорожек до 5:30:**
   - Лишний аутро-хвост после финального удара на такте 206.1 сброшен через `"cut_after_last_cue": 0.85` (длина трека сокращена с 5:51 до ровно 5:30 / 330.1s, 206 тактов).
   - Настроен `"fade_out": {"from_bar": 206, "to_bar": 207}` (1.60s ramp) под финальный удар.
3. **Добавлен cue "chorus variation" на 02:32:**
   - На сильную долю 96 такта (`bar 96.1`, 152.356s render time, ~02:32) добавлен cue `"chorus variation ready go"`, предваряющий переходную вариацию припева (Chorus 2 tag / Chorus 3) перед Instrumental.
4. **Ре-рендер трека:**
   - Выполнен полный рендер через `jamzone_render.py "Holding Out for a Hero" --practice`.
   - Обновлены `click.wav`, `cues.wav`, `all.wav`, `pb-drums.wav`, `pb-other.wav`, `cue_preview.mp3`, practice-миксы (steve, roma, tanya, alex) и `web/songs.json`.
   - Актуализированы `mix.json`, `tools/jamzone/setup_lefkara_27.py`, `wiki/songs/holding-out-for-a-hero.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.
   - Свежие `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav` скопированы в риг MainStage через `tools/sync_to_mainstage.sh --apply "Holding Out for a Hero"`.

## [2026-10-13] cues & playback | Holding Out for a Hero: финал сдвинут на bar 210 (полный 8-тактовый квадрат аутро)

По запросу Alex для `Bonnie Tyler — Holding Out for a Hero` (cat_13868):
1. **Завершение гармонического квадрата аутро (+4 такта):**
   - Ранее трек обрезался на такте 206 (`bar 206.1`), из-за чего последний гармонический цикл Outro (Am-Em-F-C-G) обрывался на середине (после 4 тактов Am-Em на bar 202..205).
   - Счётный финал `"end in"` (`count: true` $\to$ «end in 3 · 3 2 1») перенесён на сильную долю 210 такта (`bar 210.1`, 335.028s render time). Отсчёт идёт на 209 такте (аккорд G), разрешение и финальный стоп группы — на даунбите bar 210 (аккорд Am / тоника).
   - Теперь все циклы аутро имеют ровные 8-тактовые квадраты: bar 170..177 (8 тактов), 178..185 (8 тактов), 186..193 (8 тактов), 194..201 (8 тактов, cue «keep going»), 202..209 (8 тактов, завершение на 210.1).
2. **Обрезка и fade out:**
   - `"fade_out": {"from_bar": 210, "to_bar": 211}` (1.61s ramp) под финальный удар.
   - `"cut_after_last_cue": 0.85` — общая длительность плейбека стала 5:36 (336.5s, 210 тактов).
3. **Ре-рендер трека:**
   - Выполнен полный рендер через `jamzone_render.py "Footloose (1984 film) - Holding Out for a Hero" --practice`.
   - Обновлены `click.wav`, `cues.wav`, `all.wav`, `pb-drums.wav`, `pb-other.wav`, `cue_preview.mp3`, practice-миксы (steve, roma, tanya, alex) и `web/songs.json`.
   - Пересобран титровый клип: `clips/56.ass` и `clips/56.mp4` под новую длину 5:36.53.
   - Актуализированы `mix.json`, `tools/jamzone/setup_lefkara_27.py`, `wiki/songs/holding-out-for-a-hero.md`.

## [2026-10-13] setlist & web | 24.10 Lefkara: разбивка на SET 1 (10 песен) и SET 2 (11 песен) и утверждённый порядок треков

По запросу Alex обновлён порядок песен для концерта 24.10 в Лефкаре в веб-дашборде (`tools/setlist_dashboard.py` и `web/songs.json`):
- **SET 1 (`cls: "lefkara1"`, 10 песен):**
  1. Stayin' Alive — Bee Gees
  2. Felicità — Al Bano & Romina Power
  3. Cheri Cheri Lady — Modern Talking
  4. Sunny — Boney M.
  5. Stumblin' In — Suzi Quatro & Chris Norman
  6. Sarà perché ti amo — Ricchi e Poveri
  7. You're My Heart, You're My Soul — Modern Talking
  8. Mamma Maria — Ricchi e Poveri
  9. Gimme! Gimme! Gimme! — ABBA
  10. YMCA — Village People
- **SET 2 (`cls: "lefkara2"`, 11 песен):**
  1. Heart of Glass — Blondie
  2. Ghostbusters — Ray Parker Jr.
  3. I Will Survive — Gloria Gaynor
  4. Brother Louie — Modern Talking
  5. Venus — Bananarama
  6. What a Feeling — Irene Cara
  7. Maniac — Michael Sembello
  8. Hot Stuff — Donna Summer
  9. Holding Out for a Hero — Bonnie Tyler
  10. It's Raining Men — The Weather Girls
  11. The Best — Tina Turner
- Перегенерирован `web/songs.json` (`python3 tools/setlist_dashboard.py`), обновлены `wiki/gigs/2026-10-24-lefkara.md` и `wiki/index.md`.

## [2026-10-13] setlist & web | 28.10 Music Hall: замена вкладки «07.10 rehearsal» на сетлист концерта 28.10 (26 песен)

По запросу Alex из веб-дашборда (`web/index.html`, `tools/setlist_dashboard.py`) удалён список `07.10 rehearsal` и добавлена новая вкладка **«28.10 Music Hall»** (26 песен: СЕТ 1 — 11 песен, СЕТ 2 — 13 песен, Бис — 2 песни):
- **СЕТ 1 (`cls: "musichall1"`, 11 песен):** Солнце, Around the World (La La La La La), Беги от меня, Everytime We Touch, Я буду, Whenever Wherever, Mr. Saxobeat, Такая любовь, Ту-лу-ла, Destination Calabria, Freed From Desire (prod. Molella).
- **СЕТ 2 (`cls: "musichall2"`, 13 песен):** Кислотный DJ, Я устал, Про красивую жизнь, Солнышко, Медляк, Кукла колдуна, Мало тебя, Pretty Fly, Rock & Roll Queen, Heads Will Roll, I Love It, Мама Люба, Медведица.
- **Бис (`cls: "musichall_bis"`, 2 песни):** Мелом, Я сошла с ума.
- Перегенерирован `web/songs.json` (84/84 записей с данными), добавлена страница `wiki/gigs/2026-10-28-music-hall.md`, обновлён `wiki/index.md`.

## [2026-10-13] tune | Ту-лу-ла: транспонирование на полтона ниже (D major → C# / Db major, pitch_semitones: -1)

По запросу Alex песня «Ту-лу-ла» (Чичерина) переведена на полтона ниже оригинала (`"pitch_semitones": -1` в `music/songs/Чичерина - Ту-лу-ла/mix.json`, D major → C# / Db major):
- Выполнен полный перерендер через `jamzone_render.py "Чичерина - Ту-лу-ла" --practice`.
- `all.wav`, `cue_preview.mp3`, мультитрековые стемы (`auto-render/stems/vocal.mp3`, `bass.mp3`, `guitars.mp3`) и все 4 practice-микса (`alex`, `roma`, `steve`, `tanya`) транспонированы на −1 полутон через RubberBand R3 (`-3 -F`, с сохранением формант и темпа).
- `click.wav`, `cues.wav`, `pb-drums.wav` и `stems/drums.mp3` остались без питча; проверка `sync_to_mainstage.sh "Ту-лу-ла"` подтвердила побайтную идентичность файлов рига (`click.wav`, `cues.wav`, `pb-drums.wav`).
- Обновлены `web/songs.json`, `wiki/songs/chicherina-tu-lu-la.md` и `wiki/index.md`.

## [2026-10-14] feat | Ту-лу-ла: добавлен слой pb-guitars в pb-other, обновление сайта и рига

По запросу Alex добавлен пользовательский гитарный плейбек `/Users/alex/Downloads/тулула-pb-guitars.mp3` в `pb-other`:
1. **Измерение фрейма и тональности:**
   - Фрейм **render** (от $t=0$, длительность 146.064 с): входы ритм-гитары точно ложатся на сильные доли трёх соло-секций (`bar 5.1` = 11.026 с, `bar 33.1` = 62.480 с, `bar 69.1` = 128.637 с до `bar 77.1`).
   - Тональность: уже в ключе группы (**−1 полутон**, C# / Db major; корреляция хрома-профиля со сдвигом −1: 0.911 по басу, 0.960 по гитаре) → подключён как `layer` (без повторного питча).
   - Роль: `musical` (пик −0.1 dBFS, gated RMS −12.8 dBFS).
2. **Конфигурация и рендер:**
   - Сконвертирован в `music/songs/Чичерина - Ту-лу-ла/parts/pb-guitars.wav` (24-bit / 48 kHz PCM), описан в `parts/README.md`.
   - В `mix.json` задан `"pb-other": {"layers": [{"file": "pb-guitars", "frame": "render"}], "roles": {"pb-guitars": "musical"}}`.
   - Выполнен полный рендер (`jamzone_render.py "Чичерина - Ту-лу-ла" --practice`): собраны `pb-other.{wav,mp3}`, `all.wav`, `cue_preview.mp3`, `stems/*.mp3`, practice-миксы (`alex`, `roma`, `steve`, `tanya`).
3. **Синхронизация сайта и рига:**
   - Сайт обновлён через `tools/sync_site.py`: выгружены 10 обновлённых миксов/стемов и новый guide `all.wav` в R2 (`music/guide-catalog.json`), задеплоен прод Vercel (`web`).
   - В риг (`basbit/cherry-daddies-2000`) скопирован `cherry-daddies-setlist-2026-06-16/Ту-лу-ла/pb-other.wav` (`sync_to_mainstage.sh --apply --create-missing "Ту-лу-ла"`), закоммичен и запушен в `origin/main` (`47214db9`). `click.wav`, `cues.wav` и `pb-drums.wav` остались побайтно без изменений.

## [2026-10-14] playback | Sunny: убрана электрогитара из pb-other

По запросу Alex для `Boney M. — Sunny` (`cat_5568`):
- Из `pb-other.stems` в `music/songs/Boney M. - Sunny/mix.json` удалён стем `04_Electric_Guitar` (Alex играет его живьём, остаётся в `players.alex`).
- В `pb-other` остались: `05_Piano`, `06_Synth_Pad`, `07_Brass_section`, `08_String_Section`, `09_Backing_Vocals`.
- Выполнен полный ре-рендер (`jamzone_render.py "Boney M. - Sunny" --practice`), обновлены `pb-other.{wav,mp3}`, `web/songs.json` и `wiki/songs/boney-m-sunny.md`.

## [2026-10-14] cues | Gimme! Gimme! Gimme!: сдвиг cue «intro in ready go» (Outro) на 1 долю раньше (bar 86.4, 02:55.8)

По запросу Alex в `ABBA — Gimme! Gimme! Gimme! (A Man After Midnight)` подсказка `intro in ready go` на входе в Outro перенесена на 1 долю раньше — с `bar 87.1` (176.262s / 02:56.3) на `bar 86.4` (175.772s / 02:55.8, `snap_sec: 171.757`):
- Обновлён `music/songs/ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)/mix.json`.
- Выполнен полный ре-рендер (`jamzone_render.py "ABBA - Gimme! Gimme! Gimme! (A Man After Midnight)" --practice`), обновлены `cues.wav`, `cue_preview.mp3`, practice-миксы и `web/songs.json`.
- Обновлённый `cues.wav` скопирован в локальный риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Gimme! Gimme! Gimme!/cues.wav`).

## [2026-10-14] cues & click | What a Feeling: отсчёт «all in» (0:52) и клик в такте 19 переведены на 2-й темп (123.8 BPM)

По запросу Alex проверен и исправлен темп подсказки `all in` (`bar 20.1`, 52.098s) и клика перед входом барабанов в `Irene Cara — What a Feeling`:
- **Причина:** в исходном `01_Click.m4a` JamZone переключение темпа с 92.0 BPM на 123.8 BPM происходило только в момент `bar 20.1` (`52.098s`), поэтому 4 доли такта 19 (где звучит отсчёт «all — in — ready — go» и клик перед вступлением барабанов) шли в старом медленном темпе **92.0 BPM** (`49.565s, 50.218s, 50.870s, 51.522s`).
- **Исправление (`"lead_tempo": "post"` в `mix.json` и `jamzone_render.py`):**
  - Даунбит `49.565s` (аккорд F на слове «steel» после 18.4) сохранён, а 4 доли отсчёта такта 19 перед `bar 20.1` (`50.159s, 50.644s, 51.128s, 51.613s` → `52.098s`) теперь как в `cues.wav` («all — in — ready — go»), так и в `click.wav` идут ровно во **2-м (быстром) темпе 123.8 BPM** (шаг `0.4846s`).
- Выполнен полный ре-рендер (`jamzone_render.py "What a Feeling"`): обновлены `click.wav`, `cues.wav`, `cue_preview.mp3`, `stems/click.mp3`, `stems/cues.mp3`, `mix.json`, `web/songs.json`.
- Обновлённые `click.wav` и `cues.wav` скопированы в локальный риг MainStage (`cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/What a Feeling/`).

## [2026-10-14] playback | What a Feeling: добавлен лид-вокал в припевы в плейбек (pb-other)

По запросу Alex для `Irene Cara — What a Feeling` (cat_10091):
- Дорожка `11_Lead_Vocal` подключена в `pb-other.stems` с ролью `"roles": {"11_Lead_Vocal": "back-vox"}` (автоуровень по целевому потолку -23 dBFS: -5.4 dB, выровнено с `10_Backing_Vocals`).
- Настроен мьют вне припевов с сохранением затактов «What a feeling»: `"mute": {"11_Lead_Vocal": [[1, 31.58], [48.5, 63.59], [82.5, 87.55]]}`:
  - Заглушены интро + Verse 1 + Verse 2 (`[1, 31.58]`, до затакта «What a feeling» перед Chorus 1), Instrumental 1 + Verse 3 (`[48.5, 63.59]`, после хвоста «life» и до затакта «What a feeling» перед Chorus 2), Instrumental 2 / бридж (`[82.5, 87.55]`, после протяжного «What a feeling» и до затакта перед Chorus 3).
  - В Chorus 1 (`31.58..48.5`), Chorus 2 (`63.59..82.5`), Chorus 3 и финальном припевном аутро (`87.55..114`) лид-вокал звучит в плейбеке вместе с `10_Backing_Vocals`.
- Выполнен полный ре-рендер (`jamzone_render.py "What a Feeling" --practice`), обновлены `pb-other.{wav,mp3}`, `cue_preview.mp3`, practice-миксы и `web/songs.json`; обновлённый `pb-other.wav` скопирован в локальный риг MainStage (`tools/sync_to_mainstage.sh --apply "What a Feeling"`).

## [2026-10-17] cues & playback | Holding Out for a Hero: обрезка концовки на 4:43 (bar 178.1) и отключение бэк-вокала после последнего лида (~4:36)

По запросу Alex для `Bonnie Tyler — Holding Out for a Hero` (`cat_13868`):
1. **Сокращение аутро до одного 8-тактового квадрата (`bar 170..177`):**
   - После входа в Outro (`bar 170.1`, 270.848s / 4:30.85) и последней фразы лид-вокала Тани («I need a hero / I'm holding out for a hero 'till the end of the night», заканчивается на `bar 173.2` = 276.07s / 4:36.07) оставлены ровно 4 такта инструментального доигрыша квадрата (`bar 174..177` с барабанным брейком в 177 такте и арпеджиатором).
   - Счётный финал `"end in"` (`count: true` → «end in 3 · 3 2 1») перенесён с `bar 210.1` на даунбит **`bar 178.1` (`283.688s` / `4:43.69`, `snap_sec: 280.068`)**, удалён промежуточный cue `keep going` на `bar 194`.
   - Анализ `10_Arpeggiator` в `bar 177..178` показал, что каждый такт арпеджиатор играет 16-ми вверх (доли 1–2) и вниз (доли 3–4): в 177 такте на доле 3 («2») он берёт вершину `G6` и спускается `B5 → G5 → D5`, а на доле 4 («1», `bar 177.4` = `283.288s`) завершает нисходящий ход `B4 → G4 → D4 → B3`; затем на `bar 178.1` (`283.688s`) он прыгал вверх и начинал новую восходящую фразу `A4 → C5 → E5 → A5`, обрывавшуюся на полуслове.
   - В `pb-other.fade_out` для `10_Arpeggiator` задано `{"from_bar": 177, "from_beat": 4, "to_bar": 178, "to_beat": 1}` (`283.288s → 283.688s`): на счёте «1» синт доигрывает нисходящий ход и к даунбиту `bar 178.1` (доля после «1») уже полностью в нуле (`0.0`), новая фраза не начинается.
   - Общий `"fade_out"` задан `{"from_bar": 178, "from_beat": 1.15, "to_bar": 178, "to_beat": 1.45}` (`283.748s → 283.868s`): на `bar 178.1` звучит только финальный даунбит-удар барабанов и тоника баса `A2` (до слабой восьмой `178.1.5`), после чего с `283.87s` (`4:43.87`) трек полностью в тишине.
2. **Отключение бэк-вокала после последнего лида (~4:36):**
   - В `pb-other.fade_out` для `12_Backing_Vocals` задано `{"from_bar": 171, "from_beat": 1, "to_bar": 172, "to_beat": 1}` (в тактах 171..173.2 стем бэк-вокала уже в паузе, поэтому с `bar 172.1` / 4:34.05 до конца песни `12_Backing_Vocals` полностью в нуле и хор на `bar 173.25` / 4:36.3 не вступает).
3. **Ре-рендер и обновление артефактов:**
   - Выполнен полный рендер `jamzone_render.py "Holding Out for a Hero" --practice` (обновлены `all.wav`, `click.wav`, `cues.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `stems/*.mp3`, `practice-{steve,roma,tanya,alex}.mp3` и `web/songs.json`).
   - Пересобран титровый клип `tools/lyric-launcher/clips/56.{ass,mp4}` под новую длительность 4:45.25.
   - Обновлённые `click.wav`, `cues.wav`, `pb-drums.wav`, `pb-other.wav` скопированы в локальный риг MainStage (`tools/sync_to_mainstage.sh --apply "Holding Out for a Hero"`).

## [2026-10-18] cues & playback | Ghostbusters (4:02) и It's Raining Men (3:46): обрезка концовок, сдвиг end in и чистое завершение pb-other

По запросу Alex аналогично `Holding Out for a Hero` обрезаны концовки и настроены раздельные `fade_out` для `pb-other` и ритм-секции в двух песнях:
1. **`Ray Parker Jr. — Ghostbusters` (финал на `bar 115.1` = `242.087s` / `4:02.09`):**
   - Подсказка `"end in"` (`count: true` → «end in 3 · 3 2 1») перенесена с `bar 128` на `bar 115.1` (`242.087s` / `4:02.09`, конец 8-тактового квадрата `107..114` с барабанным брейком в 114 такте), удалены последующие подсказки на `bar 123` и `128`.
   - В `pb-other.fade_out` духовые и синты (`06_Digital_Piano`, `07_Electric_Piano_(Clavinet)`, `08_Synth_Strings`, `09_Synth_Keys_1`, `10_Synth_Keys_2`, `11_Synth_Lead`, `12_Synth_Brass`, `13_Brass_section`) доигрывают финальный аккорд риффа на счёте «1» (`bar 114.4`) и уходят в ноль на `bar 114 beat 4.5 → bar 115 beat 1` (`241.826s → 242.087s`), так что на даунбите `115.1` (`4:02.09`) `pb-other` уже полностью в нуле (`0.0`); `15_Lead_Vocal` заглушается после `114.1` (до затакта следующей фразы «Who you gonna call?»).
   - Общий `fade_out` (`bar 115 beat 1.15 → 1.4`, `242.165s → 242.296s`): на `115.1` звучит только финальный даунбит-удар барабанов, баса и гитар.
2. **`The Weather Girls — It's Raining Men` (финал на `bar 127.1` = `224.480s` / `3:44.48`, ровно на слове «Yeah!»; общая длина `3:46.0`):**
   - В такте 126 (`222.730s..224.480s`) вокалистка поёт «Oh, it's raining men» (`126.1..126.4`), а слово **«Yeah!»** падает ровно на даунбит **`bar 127.1` (`224.480s` / `3:44.48`)**.
   - Финальная подсказка `"end in"` (`count: true` → «end in 3 · 3 2 1») поставлена на даунбит **`bar 127.1` (`224.480s` / `3:44.48`)**: отсчёт «3 – 2 – 1» звучит на долях `126.2, 126.3, 126.4` под «it's raining men», а на «Yeah!» (`127.1`) вся группа ставит финальный удар и останавливается.
   - В `pb-other.fade_out`: все дорожки `pb-other` (`04_Sound_effects`, `07_Piano`, `08_Synth_Keys`, `09_Arpeggiator`, `10_Backing_Vocals`) уводятся в ноль на `bar 126 beat 4 → bar 127 beat 1` (`224.040s → 224.480s`), так что на слове «Yeah!» (`bar 127.1`) `pb-other` уже полностью в нуле (`0.0`); `11_Lead_Vocal_Izora_Armstead` допевает «Yeah!» и уводится в ноль на `127.3 → 127.3.5` (`225.360s → 225.575s`).
   - Общий `fade_out` (`bar 127 beat 1.15 → 1.4`, `224.546s → 224.656s`): финальный даунбит-удар ритм-секции ровно на «Yeah!» (`127.1` / `3:44.48`) и тишина до слабой восьмой `127.1.5`.
3. **Ре-рендер, деплой и синк в риг:**
   - Выполнены полные рендеры обеих песен (`--practice`), пересобраны титры `35.{ass,mp4}` и `51.{ass,mp4}`, обновлён сайт и R2 (`tools/sync_site.py`), синхронизированы WAV-файлы и титры в риг `basbit/cherry-daddies-2000`.

## [2026-10-20] cues | Медляк (Mr. Credo): добавлены подсказки stop (bar 81.1 / 3:07.43), drum in (bar 96.1 / 3:41.71) и end in (bar 113.1 / 4:20.57)

В `music/songs/Mr. Credo - Медляк/mix.json` добавлены 3 подсказки:
- `bar 81.1` (`abs_sec: 187.429` / `3:07.43`, `snap_sec: 182.286`) — `"stop"` → «stop in 3 · 3 2 1» на последнем ударе бочки перед брейкдауном (отсчёт «3 2 1» на долях `80.2–80.4`).
- `bar 96.1` (`abs_sec: 221.714` / `3:41.71`, `snap_sec: 217.143`) — `"drum in"` → «drum in ready go» на возвращении барабанов после брейкдауна (блок на долях `95.1–95.4`).
- `bar 113.1` (`abs_sec: 260.571` / `4:20.57`, `snap_sec: 256.0`) — `"end in"` (`count: true`) → «end in 3 · 3 2 1» на последнем ударе барабанов в финале (отсчёт «3 2 1» на долях `112.2–112.4`).
Выполнен полный рендер с `--practice` и обновлён `web/songs.json`.

## [2026-10-22] setlist & web | 24.10 Lefkara: обновлён порядок песен в SET 1 и SET 2 по списку Тани

В `tools/setlist_dashboard.py` и `web/songs.json` обновлён порядок треков для концерта 24.10 в Лефкаре (21 песня):
- **SET 1 (`cls: "lefkara1"`, 10 песен):** Stayin' Alive, Sunny, Venus, Sarà perché ti amo, You're My Heart, You're My Soul, Mamma Maria, Gimme! Gimme! Gimme!, Hot Stuff, It's Raining Men, I Will Survive.
- **SET 2 (`cls: "lefkara2"`, 11 песен):** Stumblin' In, Cheri Cheri Lady, Felicità, Brother Louie, Heart of Glass, Ghostbusters, What a Feeling, Maniac, Holding Out for a Hero, YMCA, The Best.
- Обновлена страница `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-22] lyrics, setlist & rig | 28.10 Music Hall: добавлены клипы 62–65 (Солнце, Кислотный DJ, Мама Люба, Smells Like Teen Spirit), обновлён сетлист 28.10 (27 песен) и проводка 28_10_1/2.concert

1. **Тексты и клипы (`tools/lyric-launcher/`):**
   - Подготовлены, проверены с guide и доставлены в риг (`basbit/cherry-daddies-2000`) клипы `62` (*Солнце — Елена Терлеева*), `63` (*Кислотный DJ — Акула*), `64` (*Мама Люба — SEREBRO*) и `65` (*Smells Like Teen Spirit — Nirvana*).
   - В `28_10_1.concert`, `28_10_2.concert`, `2000_1.concert`, `2000_2.concert` исправлены `Lyrics.cst` / `programChangeNumber` для `Сольнце.patch` (`prog=62`), `Akula.patch` (`prog=63`), `Serebro.patch` (`prog=64`) и `я буду.patch` (`prog=33`).
2. **Сетлист `28.10 Music Hall` (27 песен) и `28_10_2.concert`:**
   - **SET 1 — Dance Nostalgia (12 песен):** Солнце, Around the World, Беги от меня, Я буду, Такая любовь, Ту-лу-ла, Blinding Lights, Whenever, Wherever, Everytime We Touch, Mr. Saxobeat, Destination Calabria, Freed From Desire.
   - **SET 2 — Party & Rock (13 песен):** Кислотный DJ, Солнышко, Про красивую жизнь, Я устал, Медляк, Beverly Hills (добавлен `beverly hills.patch` в `28_10_2.concert`, убран `Rock & roll Queen.patch`), Мало тебя, Медведица, Pretty Fly, Кукла колдуна, Heads Will Roll, I Love It, Мама Люба.
   - **БИС — Все поют! (2 песни):** Мелом, Я сошла с ума.
   - Обновлены `tools/setlist_dashboard.py`, `web/songs.json`, `wiki/gigs/2026-10-28-music-hall.md`, `wiki/index.md`.

## [2026-10-25] setlist & web | 28.10 Music Hall: убран Mr. Saxobeat из SET 1, добавлен Ghostbusters в конец как запас

В `tools/setlist_dashboard.py` и `web/songs.json` обновлён сетлист `28.10 Music Hall`:
- **SET 1 — Dance Nostalgia (11 песен):** убран `Mr. Saxobeat — Alexandra Stan`.
- **SET 2 — Party & Rock (13 песен):** без изменений.
- **БИС — Все поют! + запас (3 песни):** после `Мелом` и `Я сошла с ума` добавлен `Ghostbusters (запас) — Ray Parker Jr.`.
- Обновлены `wiki/gigs/2026-10-28-music-hall.md` и `wiki/index.md`.

## [2026-11-11] ingest | Ты меня не ищи (Вирус): импорт Moises, клик, 27 cue, FX-плейбек, веб-секция 12.12 new songs

- Новая песня `music/songs/Вирус - Ты меня не ищи/`: исходники → `moises-orig/`, обработанные WAV в корне (`tools/jamzone/prep_ty_menya_ne_ishchi.py`, воспроизводимо).
- Сетка: ровные 137.59 bpm (не 138, без варпа); метроном Moises на 34 мс позже барабанов → синтетический `metronome.wav` по барабанам; лишняя восьмая на брейке 66.1→67.1 сжата rubberband до 4 долей; интро вырезано с Logic 01:00:15.652.
- `mix.json`: 27 cue по таймкодам Alex, сверены со стемами (⚠️ строки в таблице страницы песни); pb-other = layer `fx-pb` (stem-frame).
- Рендер `auto-render/`: OFF +3.441 с, 127 тактов; клик против барабанов −1…−6 мс.
- Веб: новая вкладка/секция «12.12 new songs» (`cls new1212`, добавлена ПОСЛЕДНЕЙ в `SETS` — нумерация lyric-launcher не сдвигается); `web/songs.json` перегенерирован. Сайт не публиковался, в риг не синкалось.
- Страница: [virus-ty-menya-ne-ishchi](songs/virus-ty-menya-ne-ishchi.md).

## [2026-11-12] cues | Ты меня не ищи: cue 0:17 сокращён до «verse go»

- Было: `verse in` на 8.4& со `step 0.5` (слова по полдоли сразу после «3 2 1»). Стало: `verse go` с событием на 9.1 — «verse» звучит на 8.3, «go» на 8.4, вокальный затакт 8.4&, банда 9.1; между «1» и «verse» пауза ~100 мс. Рендер обновлён, OFF без изменений (+3.441 с).

## [2026-11-12] cues | Ты меня не ищи: cue 1:13 → «synth only ready go»

- Такт 41.1: `synth-solo only ready go` (`squeeze`) → `synth only ready go` без squeeze, все слова в естественном темпе на 40.1–40.4. Рендер обновлён, OFF без изменений; локальный дашборд обновлён рендером.

## [2026-11-12] playback | Ты меня не ищи: FX на стопе такта 57 → оригинальные барабаны

- В `parts/fx-pb.wav` на 57.1–58.1 вместо филла такта 8 ×2 теперь собственные барабаны записи этого такта (сырые Moises 01:01:53.339–01:01:55.070, на своём месте). Скрипт `tools/jamzone/prep_ty_menya_ne_ishchi.py fx` обновлён; рендер и локальный дашборд обновлены. Стопы 66 и 107 пока с филлом такта 8 ×2.

## [2026-11-12] playback | Ты меня не ищи: FX на стопе такта 107 → оригинальные барабаны

- В `parts/fx-pb.wav` на 107.1–108.1 вместо филла такта 8 ×2 — собственные барабаны записи (сырые Moises 01:03:20.761–01:03:22.500, на своём месте). Филл такта 8 остался только на 8.3 и на брейке 66 (+keys).

## [2026-11-12] playback | Ты меня не ищи: брейк 66 → 4 выстрела вместо филла из начала

- Alex на localhost услышал на брейке филл из начала («на 01:01:55.070 должно быть 4 звука выстрела»). На сайте брейк звучит около 1:56. После правок 57 и 107 филл такта 8 ×2 оставался только на брейке 66 (сырые 01:02:09.040).
- В `parts/fx-pb.wav` на 66.1–67.1 теперь те же 4 выстрела, что в такте 57 (сырые барабаны 01:01:53.339–55.070), с тем же смещением к доле. Keys 66.1–66.4& остались. Филл такта 8 теперь только на своём месте, 8.3.
- «4 выстрела» = на каждой доле такта 57 гулкий удар (низ <150 Гц ~38–45 дБ) с хвостом. Филл такта 8 — тонкая дробь без низа (~2–26 дБ). По этому признаку их легко различить.

## [2026-11-12] cue+playback | Ты меня не ищи: брейк 66 без «Take it out!», 3 cue

- FX, брейк 66: keys 66.1–66.4& убраны из `parts/fx-pb.wav`. В Moises-стеме keys там сидит вокальный выкрик «Take it out!» (whisper: сырые 129.1–130.5), синта нет. На брейке остались только 4 выстрела из такта 57; pb-other 66 бит-в-бит = 57.
- Cue: старт «Ты меня не ищи drums bass ready go» (было «drum-bass in»); `verse in` 66.4& → **67.1** (на сильную долю, Alex: «not on down beat»); 100.1 «solo drums-half ready go» (было «solo-with-little-drums in»). Lead/OFF не изменились (+3.441 с).

## [2026-11-12] playback+cue | Ты меня не ищи: keys+strings в pb-other, «double kick ready go»

- `pb-other` = стемы `keys` + `strings` + layer `fx-pb`. Keys замьючены через `mix.json` `mute` (такты 40.8494–66.9457 и 99.7679–конец = сырые Moises 01:01:25.175–01:02:10.909 и 01:03:08.164–конец). Strings без мьютов. В `all` стемы не задваиваются. Сайт в режиме pb-other мьютит `keys` и `other`. Проверено: pb-other = strings + keys(с мьютами) + fx, остаток −94 дБ.
- `fx-pb`: на брейк вернул keys, сырые 01:02:09.073–10.931, по второму ТЗ Alex. В стеме keys там выкрик «Take it out!». Стем keys на брейке замьючен, так что двойного нет.
- Cue 53.1: «double kick ready go» вместо «kick in».

## [2026-11-12] playback | Ты меня не ищи: pb-other = две дорожки pb-fx + pb-keys

- По уточнению Alex: на выходе один `pb-other.wav`, внутри две дорожки. Каждая — отдельный layer в `mix.json`, на сайте видны обе: `layer: pb-fx, pb-keys`. Выключить дорожку — убрать её строку и перерендерить.
- `pb-keys` = keys + strings из записи, keys замьючены на 01:01:25.175–01:02:10.909 и 01:03:08.164–конец. Собирается `prep_ty_menya_ne_ishchi.py keys`, мьюты лежат в скрипте в сырых секундах Moises. Прежний вариант со `stems` + `mute` прямо в `pb-other` убран: на сайте он был не виден.
- `fx-pb` переименован в `pb-fx` по словам Alex. Файл побайтно тот же.
- `jamzone_render.py`: новый флаг layer'а `"derived": true`. Такая дорожка вырезана из собственных стемов песни и идёт ТОЛЬКО в свою pb-группу, а в `all`, стемы сайта и practice-минус не добавляется, чтобы не было задвоения. Описано в CLAUDE.md.
- Сверка с вариантом stems+mute: `pb-other` совпадает (разница −94 дБ: 24-бит и округление краёв мьюта). `all` и все стемы сайта побайтно те же.

## [2026-11-12] playback | Ты меня не ищи: pb-wah + Other 3:03 в pb-keys

- Третья дорожка `pb-other` — `pb-wah`: весь Moises Background Vocals (`derived`, role back-vox: −29 dBFS при потолке −23, поэтому громкость не менялась).
- `pb-keys` раньше был только keys + strings. Синт-пульс на 01:03:02.937 сидит в стеме Moises **Other**, поэтому в pb-keys его не было. Добавлен Other 01:03:02.937–01:03:08.164 (такт 96.4 → стоп 98.3, хвост до начала мьюта keys). Конец взят по затуханию: в сообщении Alex время конца не дошло.
- У derived-layer'ов новое поле `"source": [...]`. `setlist_dashboard.group_categories` его читает, и сайт в режиме pb-other мьютит нужные категории. Для pb-wah это `back_vox`, иначе бэки звучали бы дважды.

## [2026-11-12] playback | Ты меня не ищи: Other 2:52.867–3:06.294 → pb-wah

- В `pb-wah` добавлен Moises Other 01:02:52.867–01:03:06.294 (такт 91.1, стоп drum-bass → пульс до 98.3).
- Из `pb-keys` убран Other 01:03:02.937–08.164. Тот кусок я добавил по обрезанному сообщению, и он лежит внутри нового диапазона, так что иначе Other звучал бы дважды. `source`: pb-keys = keys + strings, pb-wah = backing_vocals + other.
- pb-wah −27.8 dBFS при потолке back-vox −23, поэтому громкость не менялась.

## [2026-11-12] playback | Ты меня не ищи: тишина в pb-other 58.1–66.1 и 108.1–123.4&

- Alex: «between cues 1:42 and 1:56 and 3:10 till 3:37 — no playback». Там звучали только тихие хвосты strings/keys из pb-keys (пики −43…−56 дБ) и следы бэков из pb-wah. Через PA на концерте это было бы слышно.
- На `pb-keys` и `pb-wah` добавлен layer-`mute` `[[58, 66], [108, 123.875]]`. pb-fx не трогал: там и так цифровая тишина, а мьют до 66.1 срезал бы атаку выстрела.

## [2026-11-14] ingest | Попрошу тебя (Вирус): новая песня 12.12 — клик + intro cue + pb-keys

- Moises-стемы → `music/songs/Вирус - Попрошу тебя/` (`moises-orig/` канон-имена + count-in). Сетка: 140.09 bpm, константно, метроном на кике (−1.2 мс). Первый клик Moises не на сильной доле: песня начинается с заезда клавиш (сырые 0.415 с), сильная доля 2.985 с.
- `tools/jamzone/prep_poproshu_tebya.py`: стемы сдвинуты на +0.4918 с, такт 1.1 = такт заезда (заезд 1.3, банда 3.1), синтетический `metronome.wav`. Стемы float WAV, чтобы пики выше 0 dBFS не срезались.
- Cue «Попрошу тебя playback in ready go», событие 1.3 (старт заезда), lead +2 такта. pb-other = layer `pb-keys` (весь Keys, `derived`). Добавлена в 12.12 new songs на дашборде, последней, так что клипы текстов не перенумеровываются.

## [2026-11-14] cue | Попрошу тебя: 15 cue + обрезка после end

- 14 cue Alex добавлены к стартовому: all in 3.1, stop 19.1, all in 20.1, verse no-keys ready go 28.1, pause in 3 на 35.4 (count), stop 43.1, all in 44.1, stop 52.1, all in 53.1, pause and verse in 3 на 60.4 (count), bass stop 69.1, stop 76.1, all in 77.1, end in 3 на 93.1 (count).
- ⚠️ Первая пауза: отметка 0:58.607 ложится на 35.3. По стемам пауза (бас и кик выкл) на 35.4, как и вторая на 60.4, поэтому поставлено 35.4. Ждёт подтверждения Alex.
- `cut_after_last_cue: 1`: рендер кончается через такт после финального крэша, длина 162.75 с вместо 229.6.

## [2026-11-14] playback | Попрошу тебя: pb-bass

- `pb-bass` = стем `bass` целиком (стандартный `{"stems": ["bass"]}`, как у других Moises-песен). pb-bass.wav = bass.wav на OFF, громкость без изменений (−3.4 dBFS пик), остаток −96 дБ.
- Первая пауза на 35.4 подтверждена Alex.

## [2026-11-14] gear | Попрошу тебя: рифф Keys → BOSS GM-800

- Сэмпл Alex = Moises Keys «Попрошу тебя» (сырые 3.41 с). Разбор: суперсо-стаб на каждую долю, 0.41 доли после доли, ~130 мс; Cm (C5+Eb5+C6) → Ab (Ab5+C6); сухой влево, эхо 1/8 вправо −10 дБ.
- Рецепт для GM-800 записан на странице песни: тоны 1019/1024/314/317, TONE MODIFY, MFX 53 Delay с sync 1/8, Oct Shift +1, аппликатура. Источники — GM-800 Parameter Guide и Sound List (Roland).

## [2026-11-14] cue | Попрошу тебя: lead synth 11.1, synth solo ×2, без bass stop

- Добавлен «lead synth ready go» на 11.1 (Logic 16.714). В стеме other перед ним возможен 16-й затакт с 10.4e, cue стоит на 11.1, как отметил Alex.
- «all in» 20.1 и 53.1 → «synth solo ready go». «bass stop» 69.1 (1:59.9) удалён. По-прежнему 15 cue.

## [2026-11-14] cue | Попрошу тебя: all no-rhythm 77.1 → rhythm in 85.1

- 77.1 «all in» → «all no-rhythm ready go». В записи барабаны и бас здесь играют, так что это аранжировка банды. Пишется «rhythm»: у Alex было «rhytm», с такой опечаткой say прочёл бы слово неправильно.
- Добавлен «rhythm in ready go» на 85.1. ⚠️ Отметка 01:02:23.143 приходится на ≈84.4e, на 0.75 доли раньше. Поставлено на 85.1: 8 тактов после 77.1, начало фразы. Ждёт подтверждения. «no-rhythm» уместилось в одну долю, слова не наезжают.
- 85.1 для «rhythm in» подтверждено Alex. Опубликовано на прод.

## [2026-11-14] cue | Попрошу тебя: 60.4 → «pause and synth-verse in 3»

- Подсказка на 1:45.8 (60.4, count) теперь «pause and synth-verse in 3 · 3 2 1». Анонс занимает ~3 доли (58.4& → 59.4) и кончается до «3» на 60.1, ни на что не наезжает. Опубликовано на прод.

## [2026-11-15] fix | Попрошу тебя: клик отставал от барабанов на 34 мс

- Alex на телефоне услышал, что клик сдвинут относительно барабанов. Замер на отданных сайтом mp3: атаки барабанов (удар / снейр / хэты, spectral flux) на −33…−35 мс от клика во всех полосах, по всей песне. В других песнях тем же методом 0…+7 мс. Сайт сдвиг не вносит: Web Audio стартует все буферы одновременно.
- Причина: на импорте фазу сетки взяли по 50%-атаке кика в низкой полосе. Саб у кика нарастает медленно, эта точка на ~34 мс позже удара и совпала с отстающим метрономом Moises (та же история, что в «Ты меня не ищи»).
- Фикс: `P0` в `tools/jamzone/prep_poproshu_tebya.py` сдвинут на −34.5 мс (PAD 0.4918 → 0.5263 с), пересобраны stems и pb-keys, рендер. Проверка: удар +0.1 / снейр −1.0 / хэты 0.0 / кик +1.3 мс. Cue, OFF и рендер-таймкоды не изменились. Опубликовано на прод (R2-файлы сверены по md5), в риг не синкалось.

## [2026-11-15] import | Владивосток 2000 (Мумий Тролль): клик + стартовый cue

- Moises-стемы из `~/Downloads/Владивосток 2000 _TAbS41KKNko_-A minor-130bpm-441hz (1)`: 7 стемов, пустых нет (удалять было нечего). Lead и Rhythm Guitars раздельно, count-in не импортирован.
- Темп ровный, 129.95 (lstsq 129.947, в имени 130), без варпа. Первый клик = сильная доля, банда с 1.1.
- Метроном Moises отстаёт от атак барабанов на ~27 мс → `tools/jamzone/prep_vladivostok_2000.py click` строит синтетический клик на сетке атак. После рендера удар −1.2 / снейр −0.2 / хэты +1.0 мс.
- Один cue: 1.1 «Владивосток 2000 all in ready go». Песня добавлена в веб, секция «12.12 new songs». Локально; на прод не публиковалось.

## [2026-11-15] cue + pb | Владивосток 2000: +6 cue, pb-other guitars-pb, аудит громкости гитарных pb

- Таймкоды Alex легли на линейку рендера: pre-verse break 29.1, keep going 53.3, solo in 62.1, chorus in **69.4&** (вокал входит затактом на 69.4&, по правилу затакта вместо отмеченного 70.1), outro in 78.1, double hit ending 85.4 (count; удары на 85.4 и 85.4&). ⚠️ На 53.3 в стемах ничего не меняется, поставлено по отметке; граница фразы на 54.1.
- pb-other = `parts/guitars-pb.mp3` (записанная гитара Alex, render-frame, тональность оригинальная, без `replaces`).
- Аудит: в pb-other «Ту-лу-ла» −19.8 gRMS / −16.6 LUFS, «Мало тебя» −20.0 / −16.7, «Медведица» −22.2 / −17.5, «Такая любовь» −23.2 / −18.6. Новый файл −15.2 / −12.1 → `gain_db −4.5` → готовый pb-other.wav −19.7 / −16.6, как в «Ту-лу-ла». Локально; прод и риг не трогал.

## [2026-11-15] stems | Владивосток 2000: убран Moises rhythm guitars, keep going 53.3 подтверждён

- Moises `rhythm_guitars.mp3` → `moises-orig/` (Alex): его заменяет записанная `guitars-pb`. Нет в `all`, превью и категориях сайта; «Гитары» на сайте = lead + guitars-pb. Перерендерено, cue и сетка те же.
- «keep going» остаётся на 53.3 (Alex). Опубликовано на прод (R2: стемы, pb-other, all.mp3 сверены побайтно; guide all.wav в каталоге).

## [2026-11-15] import | Sex on Fire (Kings of Leon): стемы JamZone, клик, cue интро

- JamZone `cat_20791` → `music/songs/Kings of Leon - Sex on Fire/` (9 стемов HQ). Клик JZ плавает (146–158 bpm, до ±340 мс от константы) → `click: follow`. `04_Percussion` выкидывается автоматически.
- Cue: «Sex on Fire guitar in ready go» на **2.4** (рифф правой гитары входит затактом в последнюю долю прекаунта), «all in ready go» на 7.1 (бас, левая гитара, барабаны; затакт барабанов 6.4&). Слова сверены по cues.wav.
- pb-other (черновик) = Arr. Electric Guitar + Synthesizer; pb-bass нет; players: steve, roma, alex (ритм L+R), tanya. Добавлена в веб, секция «12.12 new songs». Клик против барабанов в пределах ±7 мс. Локально; прод и риг не трогал.

## [2026-11-15] pb | Sex on Fire: pb-rhythm-guitar (L везде, R в припевах и бридже)

- `tools/jamzone/prep_sex_on_fire.py rhythm` → `parts/pb-rhythm-guitar.wav`: JZ Rhythm Guitar left везде, right в тактах 35–42, 59–74, 91–конец (Chorus 1–4 + Bridge). Equal-power кроссфейд 20 мс до тактовой линии, щелчков нет.
- mix.json: layer stem-frame, `derived: true`, source = обе ритм-гитары, `gain_db +5.0` → −16.6 LUFS в pb-other (как «Ту-лу-ла» / «Мало тебя» / «Владивосток 2000»). Arr. guitar + синт в pb-other оставлены (Alex). pb-other.wav проверен посекционно (остаток −68…−77 дБ). Локально.

## [2026-11-15] pb | Sex on Fire: Arr. guitar и синт в pb-other +5 дБ

- `"gain_db": {"07_Arr._Electric_Guitar": 5, "08_Synthesizer": 5}` в pb-other (Alex): баланс оригинала с ритм-гитарой (+5) сохранён. Arr −21.2, синт −22.2, весь pb-other −16.1 LUFS, пик 0.79. `all` без изменений. Локально.

## [2026-11-15] cue | Sex on Fire: 10 cue (минимальный набор + keep going)

- Разбор: припевы 8/16/8/16 тактов, вокал везде затактом, куплеты 2–3 начинаются за такт до секции JZ, финальный удар 131.1. Alex выбрал минимальный набор + «keep going» в середине длинных припевов.
- Добавлены: verse in 18.3, 42.2&, 74.3; keep going 66.3, 122.3 (слова в паузе вокала); bridge in 98.4; chorus in 114.4; end in (count) 131.1. Слова сверены по cues.wav, вокал под ними не звучит. Локально.

## [2026-11-15] publish | Sex on Fire на проде

- `tools/sync_site.py`: R2 (стемы, pb-other, all.mp3 — md5 совпадают с локальным рендером) + guide `all.wav` в каталоге + Vercel prod READY (web-ten-psi-12.vercel.app). Риг не трогал.

## [2026-11-15] rig | Sex on Fire → риг

- `tools/sync_to_mainstage.sh --apply --create-missing "Sex on Fire"` (новая строка MAP, секция «12.12 new songs»): `click.wav`, `cues.wav`, `pb-other.wav` в `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Sex on Fire/`, побайтно = auto-render. Подтянуты 2 коммита клавишника (ff), закоммичено и запушено в origin/main рига (14f64951).
- MainStage-сет не заведён (Playback-дорожки — вручную у клавишника). Клип текста не делался.

## [2026-11-16] pb + publish + rig | Попрошу тебя без keys; все песни 12.12 в риге

- «Попрошу тебя»: keys убраны из плейбека (Alex) → `pb-other: null` (был только derived-слой `pb-keys`). Перерендер: сетка и cue те же, плейбек = pb-bass. Устаревшие `auto-render/pb-other.{wav,mp3}` удалены (иначе синк рига подхватил бы). ⚠️ Стартовый cue «playback in» на 1.3 стоял на заезде клавиш — теперь он живьём.
- Публикация `sync_site.py`: mp3 не изменились (0 changed), обновлены songs.json (pb-other у песни выключен) и guide-каталог; Vercel prod READY; R2 сверен md5.
- Риг: в MAP `sync_to_mainstage.sh` добавлены Ты меня не ищи, Попрошу тебя, Владивосток 2000 (секция 12.12, вместе с Sex on Fire). `--apply --create-missing` по фильтру: Ты меня не ищи (click, cues, pb-other), Попрошу тебя (click, cues, pb-bass), Владивосток 2000 (click, cues, pb-other); всё побайтно = auto-render, запушено в origin/main рига (c6af41a7). Проверка по SETS: других песен из программы без рига нет. MainStage-сеты — руками у клавишника.

## [2026-11-16] pb | Попрошу тебя: заезд остаётся → pb-fx

- Поправка Alex: синт-заезд до основной темы должен остаться в плейбеке. `prep_poproshu_tebya.py fx` → `parts/pb-fx.wav` = keys + other с начала до 3.1 (затухание 20 мс до тактовой линии), дальше тишина. pb-other = derived-слой `pb-fx` (source keys, other; role musical). `pb-keys.wav` и шаг `keys` удалены.
- Проверка: pb-other звучит 4.26–6.855 с рендера (1.3 → 3.1), против keys+other −77 дБ; click/cues/pb-bass побайтно прежние. Стартовый cue «playback in» снова верен.
- Прод: 1 изменённый микс, R2 pb-other сверен md5 (ориджин и edge). Риг: + `pb-other.wav` в «Попрошу тебя», запушено (209836fb).

## [2026-11-16] rig | Инструкция клавишнику по 4 новым песням 12.12

- Страница-инструкция (artifact, приватная, шарит Alex): https://claude.ai/artifact/DyzZTaqiFHcJRkDbd3sPQs — Pull → патч дублированием донора («тулула» для 3 дорожек, «Quest pistols» для 4 с pb-bass) → имя патча = имя песни → заменить wav в каждом Playback → удалить канал Lyrics из копии → проверить с E1 → сохранить, commit, push. Плюс по песням: что в плейбеке, что живьём, плавающий темп Sex on Fire (без tempo-synced арпов).
- Устройство патчей в риге (по `data.plist` + `.cst`): каждая дорожка = отдельный канал с Playback (click/cues/pb-other/pb-bass, mono-выходы), wav копируются MainStage в `<concert>/Playback/*_N.wav`.
- `sync_to_mainstage.sh` PATCH_TO_SONG: заранее добавлены `Ты меня не ищи.patch`, `Попрошу тебя.patch`, `Владивосток 2000.patch`, `Sex on Fire.patch` — после того как клавишник заведёт патчи с этими именами, перерендеры будут обновлять и копии в концерте.

## [2026-11-16] rig | Инструкция v2: темп патча и Sync в Playback

- Sex on Fire: Рома играет бас живьём (pb-bass нет) → в карточке «Ты живьём: бас», плашка про арпы убрана.
- Клавишник всегда спрашивает bpm для патча. Проверено по риге: **Sync в Playback выключен** в рабочих патчах. MainStage пишет в свои копии wav чанк `LGBM` со своей оценкой темпа (big-endian float, байты 12–16), и она у файлов одной песни разная: «Беги от меня» click 125.0 / cues 128.0 / pb-other 91.0 / pb-bass 125.0 при темпе патча 123, «тулула» pb-other 110.6 при 130.6. С включённым Sync файлы растянулись бы по-разному; на концерте 28.10 всё играло ровно, значит Sync Off. Темп патча влияет только на арпы/дилеи.
- В инструкцию добавлен шаг «Темп патча + Sync = Off» и строка «Темп патча» в каждой карточке: 137.6 / 140.1 / 130 / 153 (Sex on Fire плавает 146–158, дилей по темпу на басу будет плавать).
- Попутно: патч «Беги от меня» стоит на 123, песня 125 (после варпа) — темповые эффекты/арпы в нём уходят на 1.6 %.

## [2026-11-16] rig | Stage Traxx вместо MainStage (PoC)

- Клавишник уходит из группы → плейбек с компа через Stage Traxx 4 (Mac, FLOW 8, 4 выхода: click/cues/pb-other/pb-bass). Клавиши пойдут слоем в pb-other, отдельного выхода нет.
- Новый `tools/stagetraxx_sync.py`: из `web/songs.json` + `auto-render` собирает библиотеку (62 песни, 202 моно-стема, 11 плейлистов `CD · <сет>`), MIDI-теги PC/START/STOP для lyric-launcher в поле lyrics. Применён к живой библиотеке, бэкап в `~/.cache/cherry-daddies/stagetraxx-backups/`.
- Не проверено вживую: звук по 4 выходам и приём MIDI launcher'ом. Страница: `wiki/pipelines/stagetraxx-rig.md`.

## [2026-11-16] song | Попрошу тебя: pb-other = весь Keys

- Alex: Moises «Keys-C minor-140bpm» в плейбек целиком. `mix.json` `"pb-other": {"stems": ["keys"]}`, слой pb-fx убран, `parts/pb-fx.wav` удалён (восстанавливается `prep_poproshu_tebya.py fx`).
- Рендер: pb-other = keys 1:1 (остаток −68 дБ), −25.5 dBFS RMS, пик −1.6. click и pb-bass байт в байт как в риге. В cues.wav перерендер дал другое по сэмплам «no-rhythm» (77.1) при той же разметке — возвращён прежний cues.wav (= риг); stems/cues.mp3 сайта из нового рендера.
- Локальный сайт обновлён. Прод и риг пока с pb-fx.

## [2026-11-16] rig | Клавишника и MainStage-рига нет → всё для локального Stage Traxx

- Alex: «клавишника больше нет, его рига тоже нет, делаем всё для локального Stage Traxx». MainStage, `basbit/cherry-daddies-2000`, `sync_to_mainstage.sh`, `wire_concert.py`, инструкция клавишнику (artifact DyzZTaqiFHcJRkDbd3sPQs) — история. Риг для «Попрошу тебя» не обновлялся (там остался pb-fx).
- «Синк в риг» теперь = `tools/stagetraxx_sync.py --apply "<song>"` (железное правило переписано в `CLAUDE.md`). Пометки «история» — `wiki/pipelines/mainstage-rig.md`, `lyric-launcher.md`, `index.md`, `AGENTS.md`, `docs/vocalist-workflow.md`, скилл `tanya-texts` (там «отправь клавишнику» больше не выполнять; путь клипов на сцену решает Alex).
- Попрошу тебя: прод опубликован (pb-other = весь Keys; R2 md5 pb-other/all сверены, Vercel READY); в Stage Traxx обновлён (`stagetraxx_sync.py --apply`, бэкап `music_library-20261116-230028.sqlite`), PB Other = моно полного Keys (остаток −72 дБ).

## [2026-11-16] people | Рома ушёл из группы

- Alex: клавишник, ушедший вместе с MainStage-ригом, — это Рома, он же основной басист. Ушёл целиком.
- Сводка по `players.roma` + `bass.who` (снимок `web/songs.json`): из 62 песен в сетах затронуто 55. Бас вживую без pb-bass — 34, синты/клавиши/сакс вне pb-other — 25 (4 песни в обоих списках). Таблицы — `wiki/people/roma.md`, раздел «После ухода». Плейбек ещё не менялся: кто закрывает партии, Alex решает по песне.
- Обновлены `wiki/people/roma.md`, `index.md`, `pipelines/stagetraxx-rig.md`, память.

## [2026-11-16] song | 12.12 new songs: pb-bass везде (Рома ушёл)

- Решение Alex: бас везде в плейбек; многие синт-партии Ромы Alex возьмёт сам (по песне); делаем последовательно.
- Уровень: существующие 22 pb-bass −18.2…−20.3 LUFS, медиана ≈ −19.2 → новые подогнаны к ней.
- Sex on Fire: `pb-bass` = `03_Bass` −1.5 дБ (−19.2 LUFS, остаток −76 дБ), `players.roma` убран. Ты меня не ищи: `bass` −0.5 дБ (−19.2, −71 дБ). Владивосток 2000: `bass` −3.0 дБ (−19.4, −78 дБ при сдвиге 1 сэмпл). click/pb-other не изменились (сверено с прежними копиями Stage Traxx); cues.wav у Sex on Fire перерендерился (речь `say` в другой реализации, тайминг 42 слов тот же ±20 мс).
- Все три в локальном Stage Traxx (4 дорожки, бэкапы `music_library-20261116-2309..2311`). Прод не публиковался.

## [2026-11-17] song | Ты меня не ищи: живые клавиши — Alex

- Alex: бывшую живую партию клавиш Ромы играет сам. `players.alex = [keys, strings]`. Плейбек не менялся (keys в `pb-keys` уже вырезаны в тактах 41–66 и 100–конец), Stage Traxx не трогался.
- Уточнение: живые места шире, чем 58–66 и 108+ (это `mute` всего слоя); keys вырезаны ещё раньше, prep-скриптом (`KEYS_MUTES`): с 40.4 и с 99.4. Alex подтвердил: все участки (41–66, 100–конец) играет он.
- `jamzone_render.py --practice`: `derived`-layer, все стемы `source` которого у игрока, возвращается в минус (иначе practice без keys/strings во всей песне). `practice-alex.mp3` проверен регрессией по стемам. Остальной `auto-render/` возвращён к прежнему (cues.wav = Stage Traxx).
- `CLAUDE.md`/`jamzone-render.md`: practice пишется только с `--practice` (было «на каждый рендер» — расходилось с кодом).

## [2026-11-17] song | Ту-лу-ла: pb-bass

- Бас Ромы → плейбек: `pb-bass: {stems: [bass], gain_db: {bass: 2.8}}` (было `null`), `players.roma` убран. Уровень −22.0 → −19.2 LUFS (медиана pb-bass), пик −6.9 dBFS.
- click/all/pb-other/pb-drums байт в байт прежние; cues.wav возвращён прежний (перерендер `say`). pb-bass против баса сайта: спектр совпадает, расхождение формы волны — фаза отдельных проходов rubberband (pitch −1).
- Stage Traxx: `--apply`, бэкап `music_library-20261117-062709.sqlite`, 4 дорожки по 145.176 с, остаток против рендера ≤ −79 дБ. Прод не публиковался.

## [2026-11-17] song | Everytime We Touch: pb-bass

- Бас Ромы → плейбек: `pb-bass` = `05_Synth_Bass` + `06_Synth_Bass_(crunch)`, оба −2.0 дБ → −19.2 LUFS (без правки −17.2). Остаток против суммы стемов −79 дБ.
- click/all/pb-other байт в байт прежние; cues.wav возвращён прежний. Stage Traxx `--apply`, бэкап `music_library-20261117-070140.sqlite`, 4 дорожки по 199.437 с.
- Колокольчики Ромы (`10_Synth_Keys_(Bells)`, `12_Bells`) пока не закрыты — вопрос Alex. Прод не публиковался.

## [2026-11-17] gear | GM-800: раскладка сцен, gm800_tsl.py, целевой лайвсет

- Решение Alex: сцены переключает MIDI из Stage Traxx внутри песни. Раскладка: 1 MUTE, 2–50 банда (только обычный PC), 51–150 все 100 заводских. Схема «PC# = сцена» в `web/stage.html` устарела.
- `tools/gm800_tsl.py` (ls/diff/build). Бэкапы и план лежат в `gear/gm-800/`. Собран `livesets/2026-11-17-target.tsl`: заводские 51–150 совпали байт в байт, у MUTE уровни партий 0. 26 старых сцен остались только в бэкапе прибора. На прибор пока не записан.
- Страница: [pipelines/gm-800.md](pipelines/gm-800.md).
- v2: сцены `<ПЕСНЯ>-` оказались заглушками (SCENE LEVEL 0). 18 песен ушли в слот 1 MUTE. Солнышко LEAD = один вариант (level 110). Банда теперь 2–28, свободно 29–50 (`livesets/2026-11-17-v2.tsl`).
- v3: тихий LEAD Солнышка (level 81) стал отдельной сценой «SOLNbISHKO QUIET» (слот 9). Новые песни 12.12 перенесены после июньской программы (27–29). Свободно 30–50 (`livesets/2026-11-17-v3.tsl`).

## [2026-11-17] song | Everytime We Touch: колокольчики Ромы → pb-other

- Alex: «в плейбек». pb-other += `10_Synth_Keys_(Bells)` (такты 19–34, 68–91) и `12_Bells` (11–12, 68–69), без правок громкости. Добавка в pb-other = стемы 1:1 (остаток −68 дБ); пик −2.3, без нормализации. `players.roma` убран.
- click/all/pb-bass байт в байт прежние, cues.wav прежний. Stage Traxx `--apply`, бэкап `music_library-20261117-073248.sqlite`, остаток против рендера ≤ −73 дБ.
- Устаревшие `practice-roma.mp3` (Everytime, Ту-лу-ла) убраны из `auto-render/` — сайт строит список practice по файлам и показывал Рому. `web/songs.json` пересобран. Прод не публиковался.

## [2026-11-17] song | Про красивую жизнь: pb-bass + клавиши Ромы в pb-other

- Alex: клавиши Ромы «в плейбек». pb-other = стемы `keys` + `other` + layer `keys-noise`; pb-bass = `bass` −2.9 дБ (−16.3 → −19.2 LUFS). `players.roma` убран, `practice-roma.mp3` убран.
- pb-other упирается в пик +0.3 → вся группа −0.7 дБ (keys-noise на 0.7 дБ тише прежнего). Регрессия: keys/other/keys-noise поровну −0.72 дБ, остаток −79 дБ; pb-bass остаток −73 дБ. click/all прежние, cues.wav прежний.
- `other` на перкуссию: верх >6 кГц на 15–19 дБ ниже хэтов, коррелирует с барабанами (протечка Moises); отдельной ручной перкуссии не видно, на слух не проверено.
- Stage Traxx `--apply`, бэкап `music_library-20261117-073757.sqlite`, 4 дорожки по 222.72 с. Прод не публиковался.
- Тест MIDI Stage Traxx → GM-800 (Солнышко, Scene Rx Ch2): GM-800 показал 7 → 8 → 9 → 10 → 1. Формат тега: `PC<сцена−1>@2`. Таймкод-теги срабатывают с точностью ±3 мс. `[midi: …]` срабатывает только при загрузке песни, поэтому стартовая сцена нужна ещё и на `@00:00.00`. `.N` в синтаксисе = Bank LSB. Тестовые теги остались в Солнышке до следующего `stagetraxx_sync`.

## [2026-11-17] song | pb-bass из стемов: Pretty Fly, Кукла колдуна, Мелом

- Бас Ромы → плейбек (Moises `bass`), `players.roma` и `practice-roma.mp3` убраны. Pretty Fly −3.9 дБ (pitch −2, −19.2 LUFS), Кукла колдуна −0.9 дБ (−19.2), Мелом +3.1 дБ (−20.8: упор в пик, +4.7 дало бы нормализацию).
- В каждой all/click/прочие группы байт в байт прежние, cues.wav прежний; остаток против стема −76…−79 дБ (Pretty Fly — по спектру, −39 дБ против баса сайта). Stage Traxx `--apply`, бэкапы `music_library-20261117-0743..0747`.
- Конвейер одной песни вынесен в скрипт scratchpad `add_pb_bass.py` (рендер → уровень −19.2 → проверки → Stage Traxx).
- Alex: есть мультитрек с микшера с концерта 28.10 (`~/Downloads/Set 2/`, 7 песен: живые бас и клавиши Ромы). Выбор «концерт / стемы / вместе» — отдельный разбор.
- Генератор тегов GM-800. В mix.json песни ключ `"gm800"` (`1` = MUTE на всю песню, либо список такт → сцена). `jamzone_render.py` (рендер или `--check`) вписывает `abs_sec` через `cue_event_time`, `stagetraxx_sync.py` пишет `[midi: …]` + `@00:00.000` + смены по таймкоду на канале 2. Проверено на копии Солнышка: такт 17 = 31.304 с, как у cue. Тесты `tools/jamzone/tests/test_gm800.py` (16), все jamzone-тесты зелёные (36). Ни одна песня пока не размечена.
- Разметка GM-800. 28 песен получили `"gm800"`: 18 MUTE (1) и 10 на одной сцене (2/3/5/6/13/13/14/15/26/27). `stagetraxx_sync --apply` для 29 песен (с Солнышком — убраны тестовые теги), бэкап `music_library-20261117-075553.sqlite`, стемы не перекодировались. Остались 9 песен с несколькими сценами, по ним нужны такты от Alex.

## [2026-11-17] gig | Мультитрек 28.10: кандидаты в плейбек

- Alex прислал мультитрек с микшера 28.10 (Set 1 №1–5 zip → `~/Downloads/Cherry Daddies 28.10 raw stems - set1.1-5/`, Set 2 №7–13 уже в `~/Downloads/Set 2/`); остальные песни будут. Порядок: сначала кандидаты, потом анализ.
- Кандидаты — бас: Ту-лу-ла, Медведица, Pretty Fly, Кукла колдуна, Мелом (49% песни); клавиши: Солнце, Такая любовь, Heads Will Roll, I Love It. Без концертного источника: синты Ромы в Around the World, Кислотный DJ. Таблица — `wiki/people/roma.md`.
- Найден пропуск: в Медведице бас играл Рома, а pb-bass нет и в списке «бас вживую» её не было (нет ни `players`, ни `bass.who`).
- ⚠ В 5 песнях с басом Ромы `Guitar LR` молчит, а `Keys LR` играет гитарную партию — вероятно, гитара Alex в канале клавиш; ждёт подтверждения.

## [2026-11-17] gig | Мультитрек 28.10: каналы 08/09 перепутаны, правила Alex

- `08 Guitar LR` = клавиши Ромы, `09 Keys LR` = гитара Alex (выходы весь концерт не менялись — Alex; проверено хромой после выравнивания по каналу Cues, корреляция 0.96–0.98).
- Alex: клавиши английских песен — только стемы JamZone; «Беги от меня» брать с биса. В «Беги от меня» Рома играл клавиши — в списках не было, добавлена.
- Кандидаты с концерта: бас — Ту-лу-ла, Медведица, Pretty Fly, Кукла колдуна, Мелом; клавиши — Солнце, Такая любовь, Кислотный DJ, Беги от меня (бис). Таблица — `wiki/people/roma.md`.

## [2026-11-17] gig | Мультитрек 28.10 целиком: кандидаты

- Распакованы оставшиеся архивы (set1.6-10, set2.1-6, set2.14-17) — весь концерт, 27 папок, включая бис (Я сошла с ума, Ghostbusters, Такая любовь, Беги от меня).
- Кандидаты: бас `07` — Ту-лу-ла, Медведица, Pretty Fly, Кукла колдуна, Мелом, Я сошла с ума, Ghostbusters; клавиши `08` (русские) — Солнце, Беги от меня (бис), Такая любовь (2 дубля), Про красивую жизнь, Солнышко, Я устал, Медляк, Мало тебя, Кислотный DJ. Английские JamZone — стемы. Beverly Hills (английская, Moises) — вопрос.
- Ещё пропуск в списках: в Медляке Рома играл клавиши (`players` без Ромы). Таблицы — `wiki/people/roma.md`.

## [2026-11-17] song | pb-bass из JamZone: Я сошла с ума, Ghostbusters; правила Alex

- Alex: Я сошла с ума — бас из стемов (есть в JamZone); по тому же правилу Ghostbusters. pb-bass: `06_Bass` −2.2 дБ, `03_Bass` −2.5 дБ → −19.2 LUFS; остаток против стема −79 дБ; all/pb-other прежние, cues.wav прежние. Stage Traxx, бэкапы `music_library-20261117-0826..0829`.
- Grabля: `stagetraxx_sync.py` пропускает файл, если копия в Stage Traxx новее исходника (mtime). Возврат прежнего cues.wav через `cp -p` (старый mtime) после синка оставлял в Stage Traxx новый cues (Ghostbusters) — исправлено `touch` + повторный синк; в прежних песнях этого дня копия в Stage Traxx совпадала с возвращённой (сверено, остаток ≤ −114 дБ).
- Beverly Hills — клавиши Ромы с концерта в кандидаты. Мелом — на концерте без метронома, пока не рассматриваем.
- Солнышко размечено по тактам Alex: 7 (1) → 8 (17) → 7 (25) → 10 (73) → 7 (81) → 8 (121) → 7 (129) → 9 (137). Стартовая сцена BASS взята из прежнего порядка сцен на приборе. `--check` посчитал `abs_sec`: все совпадают с cue на тех же тактах. Сдвиг `snap_sec` у cue 57 откатил, он к делу не относится. Засинкано, бэкап `music_library-20261117-085012.sqlite`.

## [2026-11-17] gig | Мультитрек 28.10: анализ «концерт или стем»

- Синхронизация всех 15 кандидатов по онсетам клика (p90 ≤ 3.5 мс); уход часов пульта −75.5 ppm. На концерте Беги от меня шла в 123 bpm (рендер 125), Медведица в 130.7 (рендер 129.9) — MainStage тянул плейбек.
- A/B-страница `analysis/concert-2810/index.html` (стем/концерт в миксе и соло, громкость и задержка выровнены). Инструменты `tools/concert-2810/`, итоги `wiki/gigs/2026-10-28-multitrack.md`.
- По цифрам: концерт сильнее — Кукла колдуна (бас), Солнце, Кислотный DJ (Рома играл больше, чем есть в стемах); кандидаты — Медведица (бас), Я устал, Beverly Hills; слушать — Pretty Fly, Про красивую жизнь, Мало тебя; стем лучше — Ту-лу-ла, Солнышко; не нужны — Медляк, Такая любовь (уже слой Ромы); Беги (бис) — клиппинг входа.
- Я сошла с ума и Ghostbusters: pb-bass из JamZone-стемов (Alex). Мелом — без метронома, отложен.
- Регионы Stage Traxx из cue. `stagetraxx_sync` пишет таблицу `region`: регион на каждый cue (`<такт> · <текст>`), начало в `snap_sec`, режим next. Солнышко засинкано (19 регионов), бэкап `music_library-20261117-091036.sqlite`. Тесты `test_stagetraxx_regions.py`, всего 39 зелёных.
- Цвета регионов по типу секции: stop красный, solo жёлтый, chorus зелёный, verse синий, остальное серый (`region_color`). Палитра Stage Traxx выведена из бинарника и подтверждена скриншотом. Солнышко пересинкано.
- Разводка Stage Traxx переделана: трек = своя шина (1 Click, 2 Cues, 3 PB Other, 4 PB Bass), панорама по центру. Разводка по картам: Rubix24 → моновыходы 1–4, FLOW 8 → пары 1/2 и 3/4 (дома всё в обоих ушах, проверено Alex). Треки 62 песен переложены прямо в базе (215), стемы не тронуты. `stagetraxx_sync` пишет так же. Бэкапы `music_library-20261117-094921.sqlite`, `prefs-20261117-094921.plist`. На FLOW 8 канал 7/8 = USB 3/4. Rubix24 на репе не проверен. `monoToStereo` не работает.

## [2026-11-17] song | Концертные партии Ромы в плейбеке (решения Alex)

- Alex: Ту-лу-ла — живой бас; Про красивую жизнь, Мало тебя, Беги от меня (бис + обработка), Солнышко (временно, перезаписать), Beverly Hills — клавиши с концерта; Медляк — стем; Такая любовь — слой Ромы `takaia_lubov_keys` не все клавиши (у меня ошибочно был «не нужен» и подпись «Стем» для слоя — исправлено).
- Слои `parts/roma-{bass,keys}-2810.wav` (render-frame, `tools/concert-2810/make_layer.py`, wav не в git), `replaces` заменённых стемов, громкость как в A/B, бас Ту-лу-лы −19.2 LUFS. Беги: `adeclip` (207 срезанных вершин) + `alimiter` −1 dBFS, растяжка 123→125. Мало тебя: пики слоя лимитером до −8.5 dBFS в файле (388 мс), иначе pb-other уходил в нормализацию и тянул вниз malo-guitars/malo-sfx.
- Ошибка подгонки: у Солнышка привязка по периодичному клику встала на такт раньше (A/B был сдвинут) — подгонка теперь держится у грубой оценки по cues/PB; A/B Солнышка пересобран.
- Beverly Hills: перерендер новой версией скрипта сдвинул OFF на −23.9 мс (клик и стемы вместе) — `zivert-bass` `offset_ms −23.9`, слой Ромы под новый клик, cues.wav новый. Правило в CLAUDE.md (layers).
- Все 6 в Stage Traxx (бэкапы `music_library-20261117-0935..0956`), дорожки сверены с рендером (≤ −74 дБ). Прод не публиковался.
- Регионы из cue залиты во все 62 песни Stage Traxx: 679 штук. Писались только регионы, треки, стемы, lyrics и плейлисты не тронуты. Перед этим сверено: у всех песен есть cue с `abs_sec`, копии в Stage Traxx совпадают с рендером по длине (±0.05 с). Бэкап `music_library-20261117-100532.sqlite`.

## [2026-11-17] song | Ещё 7 концертных партий Ромы + пометка «живой бас»

- Alex: Такая любовь — и слой Ромы, и концерт поверх (он играл под этот плейбек); Кукла колдуна, Медведица, Pretty Fly (бас), Солнце, Кислотный DJ, Я устал (клавиши) — с концерта. Обязательная пометка «живой бас».
- Бас-слои `parts/живой бас.wav` (Ту-лу-ла переименован), −19.2 LUFS; Stage Traxx: «PB Bass · живой бас» (`stagetraxx_sync.py`), рендер: категория bass ловит «бас». Клавиши — `roma-keys-2810` с громкостью как в A/B. Медведица: растяжка 130.7→129.9.
- Найдено и исправлено: `alimiter` без `latency=1` сдвигал слой на 3 мс (Беги, Мало тебя, Я устал, Кислотный DJ) — пересобраны, сдвиг 0 сэмплов. Потолки пиков слоёв (Мало −9.3, Беги −2.0, Кислотный −4.7 dBFS), чтобы pb-other не нормализовался и не тянул вниз соседние слои.
- Новая страница `wiki/songs/elena-terleeva-solntse.md`. Все в Stage Traxx (бэкапы `music_library-20261117-1005..10xx`), дорожки сверены (≤ −67 дБ). Прод не публиковался.

## [2026-11-17] song | Партии Ромы из стемов: 38 песен (`tools/roma_parts_batch.py`)

- Решения Alex: синты Ромы в английских (JamZone) песнях — пока все в плейбек из стемов; Мама Люба — из стемов; Мелом — теперь с кликом (бас из стема); Destination Calabria — сетка должна остаться ровной (проверено: клик сэмпл в сэмпл прежний); записанные бас-слои (MIDI) — без пометки «живой бас».
- Пакет: синты → pb-other (единица), бас → pb-bass −19.2 LUFS, `players.roma` убран; после рендера сверка клика (тайминг онсетов ≤ 0.5 мс) и OFF, иначе откат; прежний cues.wav возвращается только при неизменном таймлайне; Stage Traxx `--apply` + сверка дорожек (≤ −70 дБ).
- Откаты и разбор: 5 песен (Stayin' Alive, Sunny, Gimme, Cheri Cheri Lady, YMCA) — ложная тревога (сэмплы клика другие, тайминг тот же; Stayin' Alive сдвиг 0.18 мс). 4 песни с `click: follow` (Whenever Wherever +278 мс, Hot Stuff +126, Heart of Glass +68, I Will Survive −14) — в старых рендерах каунт-ин шёл не в темпе песни (Whenever 0.551 с против 0.620), новый скрипт ставит его в темп → начало сдвинулось; слоёв нет — приняты (`--allow-shift`), cues новые.
- You're My Heart: первый замер баса был после нормализации группы → −17.9 LUFS; исправлено (−5.2 дБ → −19.2), логика пакета учитывает нормализацию.
- pb-other упирался в пик и опускался целиком (attenuate-only) в Мама Люба (−7.5 дБ), Felicità, Brother Louie, You're My Heart, Maniac, Freed From Desire — громкость групп всё равно в норме (Мама Люба −15.4, Felicità −15.0 при медиане −17.9 LUFS). S&M: последний рендер 12.09, новый применил потолок бэков (pb-other −0.9 дБ) — это правило рендера, не правка.
- Прод не публиковался.

## [2026-11-17] site | Прод: все изменения дня (партии Ромы)

- `tools/sync_site.py`: 253 изменённых микса в R2 (58 песен: pb-other 32, pb-bass 45, all 53, стемы сайта 113, pb-drums 9, practice 1) + гайды (`music/guide-catalog.json`), Vercel prod READY (`dpl_FGS7GWGdbJ2xhChYYwyeNKaTP37X`).
- Сверка с R2 по md5 (с `?v=`): pb-other 59/59 и pb-bass 59/59 совпадают с локальными. Сайт за паролем (401 без входа) — как и должно.

## [2026-11-17] site | Кнопка «pb audition» (прослушивание с iPhone)

- Сайт играет миксы через Web Audio, а iPhone глушит его при блокировке экрана. Новая кнопка «▶ pb audition» в строке плеера играет один mp3 через обычный `<audio>` (нижняя панель, Media Session: кнопки на экране блокировки, ±10 с; `navigator.audioSession = playback`). Обычный ▶ ставит её на паузу и наоборот.
- Микс `auto-render/pb-audition.mp3` (`tools/pb_audition.py`): pb-other + pb-bass в 0 дБ, клик −3, кью −3, ведущий вокал (`stems/vocal.mp3`) −3. Если сумма клипует, весь микс опускается целиком. Только песни сетов 28.10 Music Hall и «new songs» (32 песни); у остальных файл удаляется. `jamzone_render.py` пересобирает его после каждого рендера; `setlist_dashboard.py` → `audition` + `versions["pb-audition"]`; `sync_site.py` льёт в R2; `web/dev.mjs` отдаёт локально.

## [2026-11-17] rig | Stage Traxx: очередь и клавиши

1. Тап по песне ставил её в очередь: был выключен Automatic Queue Handling. Alex включил.
2. Разобран формат `remote_triggerMappings` (prefs, JSON, HID-коды) по образцу, который Alex назначил через Learn. Дописаны → `nextSong`, ↑/↓ выбор, Return загрузить. Пробел = `startStop`. Бэкап prefs: `de.dikant.StageTraxx4.plist.bak-20261117-211815`. Детали: `wiki/pipelines/stagetraxx-rig.md` → «Очередь и клавиши».

## [2026-11-17] gear | POD Go по MIDI из Stage Traxx

1. POD Go подключён по USB, в macOS виден как MIDI-порт `POD Go`.
2. Тест: PC4 на канале 1 → POD Go переключился на 02A. Нумерация PC n = банк n//4+1, буква n%4.
3. Найден конфликт: теги launcher `PC<клип>@1` в 57 песнях будут дёргать POD Go на канале 1. Решение — MIDI Base Channel = 3 на приборе. Страница: `wiki/pipelines/pod-go.md`.

## [2026-11-17] gear | POD Go: ключ `podgo` → теги Stage Traxx

1. `jamzone_render.py`: запись `abs_sec` обобщена на оба прибора (`MIDI_DEVICES`: `gm800`/scene, `podgo`/preset).
2. `stagetraxx_sync.py`: таблица `DEVICES`; POD Go — `PC…@3`, смены за 200 мс до такта (`PODGO_LEAD`), `--podgo-channel`. Сверка до/после: теги всех 62 песен совпали побайтно. `--check` на Солнышке — mix.json без изменений.
3. Тесты: `test_podgo.py` + обновлён `test_gm800.py` (40 passed). Раскладки пресетов по песням ещё нет.

## [2026-11-17] rig | FLOW 8: весь плейбек в USB 1/2

1. Гитара (POD Go) и синт (GM-800), оба стерео, снова в стереоканалах 5/6 и 7/8 FLOW 8. Чтобы освободить 7/8, в Stage Traxx (prefs `audio_busDeviceSettings`) шины 2–4 для FLOW 8 переведены с USB 3/4 на USB 1/2. Rubix24 не тронут. Бэкап prefs: `de.dikant.StageTraxx4.plist.bak-20261117-222937`.
2. На приборе: канал 7/8 вернуть с USB 3/4 на аналоговый вход (делает Alex).

## [2026-11-17] rig | FLOW 8: поправка — плейбек в USB 3/4

Предыдущая запись ошибочна: USB 1/2 на FLOW 8 приходит не в BT-канал, а в стереоканал 5/6 (вместо аналога), и гитара в 5/6 молчала. Теперь все 4 шины Stage Traxx → USB 3/4 (канал 7/8), 5/6 — аналог под гитару. Синт — в моно 3+4 или 1+2. Бэкап prefs рядом с plist (`.bak-20261117-…`).

## [2026-11-17] rig | Заметки с дашборда в Stage Traxx

`stagetraxx_sync.py` пишет заметки песен (локальный `web/data/dashboard.db`) под MIDI-тегами в поле lyrics → видны в центральной области. Полный синк: 62 песни, у 55 есть заметки. Тесты `test_stagetraxx_notes.py` (45 passed вместе с gm800/podgo).

## [2026-11-17] rig | Мьют-патчи: POD Go 31D, GM-800 MUTE

1. POD Go mute = 31D (PC123@3) на 7 песнях без живой гитары: Around the World, Destination Calabria, Солнышко, Infinity 2008, No Stress, Ты меня не ищи, Попрошу тебя.
2. GM-800 MUTE (`"gm800": 1`): Владивосток 2000, Sex on Fire.
3. Засинкано в Stage Traxx (9 песен). Спорные 7 песен (только синт на доске) ждут решения Alex.

## [2026-11-17] rig | POD Go 31D ещё на 7 песнях

Alex подтвердил мьют гитары и в песнях «только синт»: Беги от меня, Beverly Hills, Кислотный DJ, Better Off Alone, Mr. Saxobeat, Now You're Gone, S&M. Итого 31D на 14 песнях, засинкано. Первый `--apply` молча не записал (вывод без `written`), повтор прошёл — проверять строку `written:`.

## [2026-11-17] rig | Drums и Vocals в Stage Traxx (замьючены)

`stagetraxx_sync.py`: треки 5 Drums (`stems/drums.mp3`) и 6 Vocals (`stems/vocal.mp3`) на шине PB Other, `mute = 1`. Полный синк: 62 песни, 122 стема сконвертировано, длины совпали с кликом.

## [2026-11-17] rig | Трек All и мьют-группы в Stage Traxx

`stagetraxx_sync.py`: 7-й трек All (all.wav, замьючен), `MUTE_GROUPS`: 1 = всё кроме All, 2 = плейбек-части без клика/cues. Полный синк 62 песен. Номера групп на экране Alex проверит сам (скриншот Stage Traxx без разрешения на запись экрана не снять).

## [2026-11-17] gear | GM-800: CTL1 по MIDI через ASSIGN (Ты меня не ищи)

CTL по MIDI не нажать, поэтому новый ключ `gm800_cc` (рендер пишет `abs_sec`, синк — `CC<n>.<v>@2`). «Ты меня не ищи»: CC80 0 → 127 на такте 17 (0:31.198), засинкано. На приборе в сцене 27 Alex настраивает ASSIGN 1/2 (Part 1 вкл / Part 2 выкл по CC80) и сохраняет. Тесты: 55 passed.

## [2026-11-17] gear | GM-800 слот 027: ASSIGN по CC80 записан и проверен

Правки ASSIGN из BTS до прибора не дошли (тестовый PC перезагружал сцену без WRITE). Записал ASSIGN 1/2 прямо в память слота 027 по SysEx DT1, проверил чтением и переключением после перезагрузки сцены; Alex подтвердил на слух. Адреса, коды TARGET/SOURCE и грабли — в `wiki/pipelines/gm-800.md`, инструмент `tools/midiq.swift`.

## [2026-11-17] song | Ты меня не ищи: pb-bass только в соло, Hammer обратно на 25

`pb-bass` замьючен вне соло (такты 1–58 и 66–108, там Alex играет бас вживую); CC80 = 0 на такте 25 «chorus in» (Hammer Bass обратно). Полный перерендер: OFF и клик не изменились, pb-bass в соло тот же по уровню. Засинкано в Stage Traxx.

## [2026-11-18] song | Ты меня не ищи: GM-800 сцена 30 на соло

`gm800`: 27 → 30 (57.4&) → 27 (66.4&) → 30 (107.4&), смены на «4&» стоп-тактов, ~218 мс до события. Засинкано в Stage Traxx. Имя слота 30 не прочитано: GM-800 в этот момент не был подключён к Mac.

## [2026-11-18] song | Партии Ромы: громкость по песням, а не +4 дБ везде

Alex: «плейбеки после переноса партий Ромы тише, может +4 дБ везде?» Анализ (LUFS каждого элемента pb-other): системной разницы нет, партии Ромы против остального pb-other — медиана 0 LU, разброс −7…+18 (в Мама Люба / Freed / ATC они громче pb-bass). Ещё и 46 из 59 pb-other в пределах 4.4 дБ от пика. Тихие места адресные, правки:
- **Солнце:** концертные клавиши −8.1 → −3.6 (были −27.7 LUFS против fx −23.3, стали −23.2). Рома на концерте не сделал паузу «keys stop» (такты 81–88, в стеме Moises там тишина) → слой замьючен `[[81, 89]]` с фейдом 200 мс на выходе / 5 мс на входе (атака 89.1 на сетке); cue «keys stop / keys in» остались.
- **Такая любовь:** синт-соло Ромы записано на ~7 дБ тише его аккордов (в тактах соло в слое только соло) → `gain_bars` +7 на 43.2–50 и 84.2–91: соло −17.8 LUFS ≈ акустика в pb −18.1.
- **Я устал:** концертные клавиши −8.1 → −4.1 (−20.9 LUFS, бэк-вокал −19.2).
- **Around the World:** в pb-other добавлены пэды 07/08, струнные 10 (Alex их больше не играет) и `04_Noise_effects` (не перкуссия); `players.alex` убран, `practice-alex.mp3` удалён.
Рендер: новые поля слоя `gain_bars`, `mute_fade_ms` (CLAUDE.md, раздел layers). OFF у всех четырёх не изменился, pb-other нигде не ужимался по пику. В Stage Traxx засинкано (4 песни), PB Other Солнца сверен: 81–88 тишина. Прод не обновлялся. Не тронуты, но тихие по записи: Synth Lead в S&M (−28.6 LUFS), тенор-сакс в Destination Calabria (−24.0).

## [2026-11-18] song | S&M Synth Lead +6, Destination Calabria тенор-сакс +3.5

Продолжение правок громкости партий Ромы (Alex: «да, поднять»). Ориентир — лид-партии других песен сидят на −3…−5 LU от полного микса записи в местах, где играют (ATC Synth Lead −4.6, BOA Arpeggiator −2.7). Было: S&M `07_Synth_Lead` −10.5 LU, Calabria `08_Tenor_Saxophone` −8.1 → `gain_db` +6 / +3.5 → обе −4.5 LU. Клик Calabria побайтно прежний (сетка cut_bars цела), OFF обеих не изменился, pb-other без нормализации (пики −2.8 / −1.3). Засинкано в Stage Traxx. В S&M тоже тихие по записи, не тронуты: `09_Arpeggiator` −12.8 LU, `08_Synth_Keys` −11.5.

## [2026-11-18] publish | Прод: правки громкости партий Ромы

`tools/sync_site.py`: 28 миксов в R2 (Солнце, Такая любовь, Я устал, Around the World, S&M, Destination Calabria + неопубликованный pb-bass «Ты меня не ищи» от 17.11), 3 новых guide WAV (Солнце, Такая любовь, Я устал), `vercel deploy --prod` READY. pb-other всех 7 песен на R2 совпадает с локальными по md5. Грабля: у `sync_site.py` нет `--help` — любой аргумент кроме своих флагов запускает полную публикацию; а пайп в `head` обрывает её на середине (guide и деплой убиты SIGPIPE) — повторный запуск догоняет (миксы уже в `.r2-uploaded.json`).

## [2026-11-18] song | Клавиши Ромы до −7 LU от записи (6 песен)

Полный замер: 61 клавишная партия, добавленная после ухода Ромы (27 песен), — громкость партии против `all.wav` в местах, где она звучит. Лиды/клавиши ниже −8 LU подняты `gain_db` до −7 LU: Mr. Saxobeat Synth Keys 1/2/3 +4.5/+5/+5.5; S&M Arpeggiator +6, Synth Keys +4.5; Попрошу тебя keys +3.5; We Found Love Synth Keys 2 +3, Synthesizer +2.5; Better Off Alone Synth Lead 2 +4; Cascada Synth Keys (Bells) +1.5, 12_Bells +6 (потолок подъёма; −11.9 LU, до −7 было бы +11). Heads Will Roll `09_Synthesizer_(disto)` (−10.9) не тронут: это не главный риф, а дист-слой в припевах (Alex). Пэды/струнные ниже −9 — фон, как в записи, не тронуты. Saxobeat и Попрошу тебя упёрлись в пик (головной нормалайзер ужимал весь pb-other на 2.3–2.4 дБ) → новый ключ группы `"peak": "limit"` (alimiter −0.4 dBFS, 22–42 выброса на песню). Клик и OFF у всех шести прежние. Засинкано в Stage Traxx; прод не обновлялся.

## [2026-11-18] publish | Прод: клавиши Ромы до −7 LU (6 песен)

`tools/sync_site.py`: 20 миксов в R2 (Mr. Saxobeat, S&M, Попрошу тебя, We Found Love, Better Off Alone, Everytime We Touch), новых guide нет (all.wav не менялись), `vercel deploy --prod` READY. pb-other всех шести на R2 совпадает с локальными по md5.

## [2026-11-18] rig | Мьют-группа 1 = All + клик + cues

Alex: с группой 1 не размьютить Click/Cues, а с All они нужны всегда. `MUTE_GROUPS`: группа 1 = PB Other/PB Bass/Drums/Vocals; Click и Cues ни в одной группе; группа 2 (дубль) убрана. Бит 0 = группа 1 подтверждён скриншотом. Полный синк 62 песен.

## [2026-11-18] song | Ты меня не ищи: GM-800 сцена 30 с «synth only», бас в соло из плейбека

GM-800: 27 → 30 на 40.4& (1:13.043, «synth only») → 27 на 66.4& (1:58.395, «verse in») → 30 на 99.4& (2:55.958, соло) до конца; смена на 57.4& убрана. Бас в соло-кусках (Alex: «где соло я играю, там должен быть бас — пока из плейбека»): Moises `bass` там пустой (−73…−100 дБ) — прежний «pb-bass только в соло» фактически молчал; синт-бас соло-кусков сидит в Moises `other` (тональная линия A/G#/A#). Новый derived-слой `pb-solo-bass` = `other` через ФНЧ 400 Гц 24 дБ/окт (`prep_ty_menya_ne_ishchi.py solobass`), в pb-bass звучит 58–66 и 100–116 (−18 LUFS, середина −20 дБ от низа); `source` не указан намеренно — иначе сайт в режиме pb-bass глушил бы весь `other`. В «synth only» 41–57 баса нет и в записи. Клик/OFF прежние; засинкано в Stage Traxx; прод не обновлялся. Запись нормального баса — в [todo.md](todo.md). Заведён TODO-журнал `wiki/todo.md`.

## [2026-11-18] rig | Все переключения за 0.5 с до такта

Alex: «переключение на соло патч 30 должно быть раньше, стандартно пол секунды вместо 200 мс». `stagetraxx_sync.py`: `SWITCH_LEAD = 0.5` для сцен GM-800 (было 0 — точки ставились на «4&»), CC GM-800 и POD Go (было 200 мс). В mix.json теперь отмечается само событие: «Ты меня не ищи» сцены на 41 / 67 / 100 → 1:12.761 / 1:58.113 / 2:55.676. Затронуты также Солнышко (GM-800) и Солнце (POD Go) — засинкано, проверить на слух (todo). Тесты: 75 passed.

## [2026-11-18] rig | Посторонний дист-синт на «Ты меня не ищи» — это Logic Pro

Звук шёл при опущенных фейдерах Stage Traxx. Найден открытый Logic Pro с `~/Downloads/ты меня не ищи.logicx`: принимает START, клок и PC от Stage Traxx и играет проект. GM-800 по SysEx: слот 27 NE ISHI BASS, 30 NE ISHI SOLO, 13 I LOVE IT HEADS — сцены верные. Правило записано в `wiki/pipelines/stagetraxx-rig.md`.

## [2026-11-18] rig | Попрошу тебя и Владивосток 2000: GM-800 / POD Go

Попрошу тебя: GM-800 28 (POPROSHU TEBYA) → 29 (POPROSHU TEBYA *) на «lead synth» такт 11 (0:20.058), имена слотов прочитаны с прибора. Владивосток 2000: GM-800 MUTE (было); POD Go 32A → 32B на куплетах (такты 5, 30) → 32D на припевах (21, 46) до конца. Границы частей взяты по тексту (whisper по стему vocals) и затактам голоса на 4-й доле: со стандартным отступом 0.5 с смена приходится на вход голоса (0.04–0.2 с раньше). Засинкано в Stage Traxx.

## [2026-11-18] rig | Владивосток 2000: соло на 32A

POD Go: 32A на соло (такт 62), обратно 32D на припев (такт 70), смены за 0.5 с до такта. Засинкано в Stage Traxx.

## [2026-11-18] rig | Rubix24 в другом USB-порту: разводка Stage Traxx не подхватилась

1. Rubix24 подключён в другой порт → новый UID `AppleUSBAudioEngine:Roland:Rubix24:1100000:1,2` (в prefs был только `…:100000:1,2`); выход по умолчанию стоял на динамиках MacBook, Stage Traxx играл туда.
2. Stage Traxx закрыт, prefs забэкаплены (`de.dikant.StageTraxx4.plist.bak-rubix-20261118-185041`), раскладка шин 1–4 → моновыходы 1–4 скопирована на новый UID (обе записи остаются). Rubix24 выбран системным выходом, Stage Traxx запущен: устройство активно, разводка после запуска на месте.
3. Голосовой тест «Выход один… четыре» прогнан по выходам 1–4 Rubix (AUHAL, по каналу на фразу, −12 dBFS, два круга). Подтверждение на пульте — за Alex. Грабля описана в [stagetraxx-rig](pipelines/stagetraxx-rig.md).

## [2026-11-18] rig | Раскладка Rubix24 в Stage Traxx на все USB-порты

1. Новый `tools/stagetraxx_ports.py`: берёт известную раскладку Rubix24 (шины 1–4 → моновыходы 1–4) и прописывает её на UID каждого пути — 3 корневых порта Mac (из ioreg) напрямую и через хаб, гнёзда 1–7. Итого 24 UID (было 2). Stage Traxx закрыт/запущен скриптом, бэкап `de.dikant.StageTraxx4.plist.bak-ports-20261118-190104`, остальные устройства не тронуты, после запуска все 24 на месте.
2. Без флагов скрипт проверяет подключение: UID из CoreAudio (ctypes) → routed / NOT ROUTED, плюс выход по умолчанию. Если реальный UID не входит в вычисленные — предупреждает (формат хаб-гнёзд `%x` от location сверен с корневыми портами и с UID GM-800 на хабе, Rubix в хабе вживую ещё не был).

## [2026-11-18] query | Самая громкая песня плейбека

pb-other + pb-bass, integrated LUFS по 61 песне программы: «Мало тебя» −12.3 (+1.7 LU к следующей группе −14.0), самые тихие Мелом −20.8 и Ты меня не ищи −20.3. Рейтинг и вывод — в [stagetraxx-rig](pipelines/stagetraxx-rig.md#громкость-плейбека-по-песням-2026-11-18).

## [2026-11-18] rig | Now You're Gone: сцены GM-800 в Stage Traxx

`gm800`: 22 SOLO (такт 1) → 23 BR (58) → 22 (75). Теги `PC21@2` / `PC22@2` @01:31.300 / `PC21@2` @01:58.679, синк `--apply` прошёл, в базе проверено. Сначала BR был поставлен на брейк 42 (cue «break in»), потом перенесён на бридж по заметке Alex «br aft 2nd solo». Открытый вопрос: если в бридже Alex играет партию 05_Synthesizer, то она задваивается с pb-other. См. [gm-800](pipelines/gm-800.md).

## [2026-11-18] song | Now You're Gone: 04_Synth_Bass_2 → pb-other

По словам Alex, `04_Synth_Bass_2` — синт, а `03_Synth_Bass_1` — настоящий бас. pb-bass теперь только `03` (−1.4 дБ → −18.7 LUFS, в коридоре pb-bass), `04` с тем же −1.4 дБ в pb-other. Сумма pb-other+pb-bass совпадает с прежней (остаток −73.5 дБ), click/all/OFF байт в байт прежние, cues.wav возвращён прежний. Stage Traxx `--apply`, бэкап `music_library-20261118-211920.sqlite`, 7 дорожек по 149.779 с, остаток против рендера ≤ −73 дБ. Прод не публиковался.

## [2026-11-18] song | Now You're Gone: синт-бас +6 дБ

`04_Synth_Bass_2` в pb-other: −1.4 → +4.6 дБ. Причина (Alex): на репетиции синт в басу звучал очень тихо, pb-bass поднимали на +6 дБ, пока в нём не было отдельной партии настоящего баса. pb-other: пик −3.55 dBFS, RMS −24.7 → −21.9 dB, нормализации группы нет. click/all/pb-bass байт в байт прежние, cues.wav прежний, practice-миксы перерендерены. Stage Traxx `--apply`, бэкап `music_library-20261118-230045.sqlite`, остаток ≤ −76 дБ.

## [2026-11-19] song | Supermassive Black Hole вместо Sex on Fire в 12.12

- Sex on Fire снята с 12.12 и перенесена в «Архив» (`tools/setlist_dashboard.py`).
- Supermassive Black Hole (Muse) из JamZone `cat_12553`: 12 стемов, 120 bpm, 12 базовых cue по структуре и словам `tiles.json`. pb-other = бэки + синт + нойз + синт-бас −6.5 дБ, `peak: limit` (переходы синта 0 dBFS). pb-bass = электробас −6.5 дБ → −19.2 LUFS. Вместе −15.2 LUFS.
- Stage Traxx: полный синк `--apply` (63 песни, 1 новая, 11 плейлистов), бэкап `music_library-20261119-053819.sqlite`. Плейлист 12.12 = Ты меня не ищи, Попрошу тебя, Владивосток 2000, Supermassive. Дорожки 214.000 с, остаток против рендера ≤ −75 дБ. Прод не публиковался.
- Открыто: players, GM-800, POD Go не заданы. Страница: [muse-supermassive-black-hole](songs/muse-supermassive-black-hole.md).

## [2026-11-19] rig | Supermassive Black Hole: GM-800 MUTE, POD Go 32D

`gm800: 1`, `podgo: "32D"` на всю песню (Alex). В Stage Traxx теги `PC0@2` и `PC127@3` (при загрузке и в 00:00), проверено в базе; бэкап `music_library-20261119-054304.sqlite`.

## [2026-11-19] song | Supermassive Black Hole: стопы барабанов в cue

9 стопов барабанов на 4-й доле (такты 9, 17, 25, 33, 49, 57, 73, 81, 89), найдены по атакам в стеме барабанов. Порог −40 дБ пропустил 17/81/89, там звенит тарелка. Разметка: «drums stop» (на 49 и 73 «all stop», там молчат и гитара, и бас) + `raw`/`step: 0.5` «chorus go» / «verse go» / «solo go» / «vocal go» / «go» в долю стопа. Они заменили «in ready go» на 18.2, 26, 50, 74, 90. Всего 24 cue. click/all/pb байт в байт прежние, Stage Traxx `--apply` (бэкап `music_library-20261119-060013.sqlite`, Cues остаток −120 дБ). Приём описан в [cue-system](pipelines/cue-system.md).

## [2026-11-19] song | Supermassive Black Hole: стопы барабанов исправлены

Alex: последний удар должен быть на долю после «1», стопы внутри припевов и все «go» убрать. По атакам последний удар в такте стопа — на 2& (обычный грув 1, 2, 2&, 4; в стопе 1, 1&, 2&, тишина, подхват на 4a). Стопы перенесены на `"beat": "2&"`: 9, 17, 25, 49 (all), 73 (all), 81. Убраны стопы на 33/57/89 и все go; на 90 возвращён «vocal in». Итого 13 cue. click/all/pb байт в байт прежние, Stage Traxx `--apply` (бэкап `music_library-20261119-061111.sqlite`, Cues остаток −127 дБ). Правило «точка стопа = последний удар» записано в CLAUDE.md и [cue-system](pipelines/cue-system.md).

## [2026-11-19] rig | POD Go: смены пресетов за 1 с

`PODGO_LEAD` 0.5 → 1.0 с в `tools/stagetraxx_sync.py` (Alex: «переключение патчей гитары миди за 1 секунду»). GM-800 сцены/CC остаются на `SWITCH_LEAD` 0.5 с. Полный синк Stage Traxx `--apply` (63 песни, 11 плейлистов, бэкап `music_library-20261119-061108.sqlite`). Проверено в базе: Владивосток 2000, такт 5 (32B) — `00:10.081` вместо `00:11.081`. Сейчас тайм-смены POD Go только у Владивостока, у остальных пресет на всю песню, у них меняется только время смен. Без `podgo` (кроме программы 80-х и архива) 24 песни: Такая любовь, Ту-лу-ла, Blinding Lights, Whenever Wherever, Everytime We Touch, Freed from Desire, Про красивую жизнь, Я устал, Мало тебя, Медляк, Медведица, Pretty Fly, Кукла колдуна, Heads Will Roll, I Love It, Мама Люба, Мелом, Я сошла с ума, Ghostbusters, Adventure of a Lifetime, Uptown Funk, We Found Love, Rock & Roll Queen, Я буду.

## [2026-11-19] rig | Опорные точки громкости: постановка и аудит

Alex: выстроить «теорию опорных точек» для баланса живой гитары/синта против плейбека. Постановка, инварианты и якоря согласованы: «Владивосток 2000» (слой `guitars-pb` против живой POD Go) и «Солнышко» (бас GM-800 → `synth-bass` в pb-bass). Новый `tools/level_audit.py` (только чтение, меряет моно-свёртку, как играет Stage Traxx): pb-bass ровный (−21.0…−18.2, медиана −19.2), pb-other нет (−24.6…−13.9), у музыкальных партий абсолютной нормы нет, норма «−7 LU от `all.wav`» относительная (all гуляет на 8.6 LU), пик-шаг по песне съедает подъёмы в 34 из 59 pb-other, свёртка в моно отнимает у pb-other 0–3 дБ по песням. Рендеры и `mix.json` не менялись. Страница: [level-anchors](pipelines/level-anchors.md); нормы, запас и запись пресетов — в [todo.md](todo.md).

## [2026-11-19] song | Supermassive Black Hole: solo in 74, без vocal in 90

По таймкодам Alex из рендера: 2:28 = такт 74.1, добавлен «solo in» с `step: 0.5`. «solo in ready go» уложено по полдоли в тихие доли стопа 73 (73.3–73.4&), после последнего удара 73.2& — иначе наложилось бы на «3 2 1». 3:00 = такт 90.1: «vocal in» убран. click/all/pb байт в байт прежние, Stage Traxx `--apply` (бэкап `music_library-20261119-061908.sqlite`, Cues остаток −121 дБ).

## [2026-11-19] rig | Опорные точки громкости: черновик норм v0

Нормы по ролям от якорей (integrated, моно-свёртка, на сумму роли в песне): F передний план −17, A аккомпанемент −21, P фон −26, бас −19. Медианы программы уже лежат в 0.5–0.8 LU от них; в ±2 LU — 47 из 115 пар песня + роль. Запас: опора на 6 дБ ниже → выше −1 dBFS остаются 4 из 59 pb-other. Не утверждено, к `mix.json` не применено. [level-anchors](pipelines/level-anchors.md#черновик-норм-v0-2026-11-19-не-утверждён-к-mixjson-не-применён).


## [2026-11-19] setlist | Сет «12.12 all» и отклонения от норм по нему

Alex: программа концерта 12.12 — 29 старых песен + 5 новых; песни 80-х и Uptown Funk в работе по громкости пока не учитывать. В `tools/setlist_dashboard.py` добавлен сет «12.12 all» (последним, `cls: all1212`), на сайте вкладка «12.12 all», `web/songs.json` пересобран (32 из 34 с данными; нет в базе: МакSим «Знаешь ли ты», t.A.T.u. «Нас не догонят»). `tools/level_audit.py --set`. Отклонения от норм v0 по сету — в [level-anchors](pipelines/level-anchors.md#фокус-программа-1212-alex-2026-11-19). Прод и Stage Traxx не обновлялись (плейлист «CD · 12.12 all» появится при полном синке).

## [2026-11-19] rig | Роли: клавиши Ромы в трёх песнях — передний план

Alex: `roma-keys-2810` в «Мало тебя», «Про красивую жизнь», «Беги от меня» — передний план (F). С гитарными слоями это шесть партий F в −16.0…−16.8. Остальные роли по программе 12.12 ждут ответа. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | Роли 12 партий от Alex; плейбек голосу не уступает

Alex расставил роли по 12 спорным партиям программы 12.12 (9 — F, 3 — A) и спросил про «важную партию, которая не должна быть громче голоса» (Солнышко, Такая любовь, Ты меня не ищи). Замер: вокал занимает 75–85% песни, `pb-other` в паузах вокала громче всего на 1.0 дБ в медиане. Предложен признак «уступает голосу» (авто-`gain_bars` от стема вокала, −4 LU под голосом), не утверждён. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | Ступень V = −19 вместо признака «уступает голосу»

Alex: плейбек всегда должен уступать голосу, отдельный признак не нужен, автоматику по тактам не делаем. Для важных партий под голосом — ступень V −19 на всю песню (между F −17 и A −21). Солнышко, Такая любовь, Ты меня не ищи → V. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | Ступень V снята: важные партии — F

Alex: «упростим до F, потом посмотрим на практике». Ступеней три: F −17, A −21, P −26, бас −19. Солнышко, Такая любовь, Ты меня не ищи → F. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] song | Нормы громкости: первые правки в шести песнях

По ролям от Alex (F −17, A −21): Солнышко клавиши +4.8, Солнце +4.3, Такая любовь клавиши +4.0 (и `gain_bars` соло 7 → 3), Beverly Hills +2.2, Supermassive `09_Synthesizer` −2.5, Mr. Saxobeat реверс-сакс −6.5 (+8.9 → +2.4, был как в исходном баунсе). Клик, OFF, pb-bass прежние; cues.wav возвращены прежние. В Stage Traxx засинкано, бэкап `music_library-20261119-073952.sqlite`, PB Other сверен. «Ты меня не ищи» (`pb-keys` +8.3) упёрлась в пик, группа ужалась на 2 дБ — не синкалась, ждёт решения. Прод не обновлялся. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] song | Ты меня не ищи: клавиши +8.3 через лимитер

Alex: «да, лимитер». `pb-other` получил `"peak": "limit"`: `pb-keys` −25.3 → −17.0 (F), fx и вау прежние, группа −16.9. Клик, OFF, pb-bass прежние, cues.wav возвращён прежний. Засинкано в Stage Traxx, PB Other сверен. Прод не обновлялся.

## [2026-11-19] rig | POD Go: черновик пресетов основной программы (24 песни)

По словам Alex и заметкам доски `podgo` вписан в 24 `mix.json`, таблица в [pod-go](pipelines/pod-go.md). На всю песню: 32D — 16 песен (в т.ч. Ghostbusters и все, где пресета в заметках не было), 32B — Whenever Wherever, Медляк; Everytime We Touch — 31D (MUTE) + GM-800 сцена 4 CASCADA SOLO. По тактам: Такая любовь 32C → 32D (43) → 32C (100) → 32D (110.3, «ready», под заезд); Мало тебя 32B → 32D (21) → 32B (45) → 32D (61); Мама Люба 01A → 01B (12) → 01A (36) → 01B (52) → 01A (68); Кукла колдуна 01A → 01B (34); Ту-лу-ла 32A → 32B (13) → 32D (25) → 32A (32.4) → 32B (41) → 32D (53) → 32A (68.4). Такты припевов — из `lyrics-timed/NN.tsv` и cue (`jamzone_sections.py` на Moises-песнях выдаёт чужой каталог). `--check` вписал `abs_sec`, cue не сдвинулись. Stage Traxx `--apply` (64 песни, бэкап `music_library-20261119-081936.sqlite`), теги проверены в базе: Такая любовь `PC126@3` → `PC127@3` 01:17.222, Кукла `PC1@3` 00:55.528, Everytime `PC3@2` + `PC123@3`. Предположения (Ту-лу-ла, вступление и такты 12/68 Мамы Любы) — в [todo](todo.md).

## [2026-11-19] rig | POD Go: правки Такая любовь и Мама Люба

Alex: в «Такая любовь» заезд в последний припев делается уже на «ready», пресет нужен на две доли раньше → 32D с 110.3 на 110.1 (тег 03:16.333). «Мама Люба» была расставлена наоборот: начало на 01B, куплеты (с «verse-instrumental» 12) на 01A, припевы и проигрыши на 01B → 01B (1) → 01A (12) → 01B (36) → 01A (52) → 01B (68, до конца). Stage Traxx `--apply` по обеим, теги проверены в базе.

## [2026-11-19] rig | GM-800: Saxobeat, Мало тебя, MUTE трём гитарным песням

Mr. Saxobeat: 18 SAX (1) → 19 SYNTH (16) → 18 (74) → 19 (87) → 18 (95); такты по активности стемов сакса и синт-лида, в 95–102 звучат оба — Alex играет сакс. Мало тебя (черновик, «пока ок»): MUTE в куплетах и бридже, 11 CH на припевах (21, 61, 103), 12 SOLO на соло (37, 77, 95). `gm800: 1` — Rock & Roll Queen, Я буду, Smells Like Teen Spirit. Infinity, No Stress, S&M отложены (нет в листе 12.12), черновик тактов в [gm-800](pipelines/gm-800.md). Stage Traxx `--apply` по пяти песням, теги проверены в базе.

## [2026-11-19] publish | Прод: правки по нормам громкости, сет «12.12 all», pb-audition для всей программы 12.12

Alex: «чтобы на проде был актуальный pb-audition». `tools/pb_audition.py`: цель теперь ещё и сет «12.12 all» (добавились Mr. Saxobeat и Now You're Gone; у Smells Like Teen Spirit плейбека нет). `sync_site.py`: 49 файлов по 8 песням (семь с правками уровней + Now You're Gone + впервые Supermassive Black Hole), деплой READY. pb-audition всех восьми на R2 побайтно равны локальным. Страница прода за паролем, вкладку «12.12 all» снаружи не проверить.

## [2026-11-19] rig | Живая сторона: громкость 23 сцен GM-800 замерена автоматом

Alex подключил POD Go и GM-800 и скачал мануалы в `docs/manuals/`. GM-800 играет от MIDI-нот по USB при NOTE SOURCE = USB; `tools/live_levels.py gm800` переключает это по SysEx, играет одну фразу на каждой сцене из `mix.json`, пишет USB-аудио 1/2 и возвращает настройку (проверено чтением: GK IN). Разброс сцен 24 LU; басовые сцены расходятся на 6 дБ (якорная «Солнышко» тише «Кислотного DJ» и «Ты меня не ищи»). POD Go: re-amp требует Input block = USB 3/4 в каждом пресете руками, не замерен. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | Живая сторона: пресеты POD Go замерены re-amp'ом

15 с сухой игры Alex прогнаны через 6 пресетов (вход `USB 3/4` Alex переключал руками по голосовым подсказкам): 32A −21.9, 32B −24.3, 01B −25.0, 32D −25.0, 01A −26.8, 32C −28.3; 31D — мьют. Разброс 6.4 дБ; 01B = 32D. `tools/live_levels.py podgo`. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | Опорные звуки живой стороны: 32D и сцена 7; черновик калибровки

Alex: опорный пресет гитары — 32D. Синт — сцена 7 (бас «Солнышка»). В [level-anchors](pipelines/level-anchors.md) добавлены цели для сцен GM-800 по тем же шагам между ролями, что у плейбека, и черновик процедуры калибровки на площадке (два фейдера по двум песням). На приборах ничего не менялось.

## [2026-11-19] rig | GM-800: бас сцены 27 выровнен с якорной сценой 7

Alex: «выровнять». По SysEx в память слота 27: PART LEVEL партии 2 (Hammer) 127 → 90, партии 1 (Reso, по CC80) 98 → 88; обе −17.0 на нижних нотах, как сцена 7 (повторные замеры в обоих состояниях). Сцена 14 не тронута: её замер гуляет до 7 дБ, «+5.2» было выбросом. NOTE SOURCE возвращён на GK IN. Лайвсет v3 в репо правку не содержит. `tools/live_levels.py`: частичный прогон не стирает остальные сцены, `EXTRA_CC`. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | GM-800: способ замера исправлен (струны), таблица сцен перемерена

Alex: в сцене 14 играется только бас. Причина ложных «+5 дБ»: один тон разложен на партии 3 и 4 по струнам 6 и 5, а MIDI-ноты шли во все партии сразу и складывались со случайной фазой. `tools/live_levels.py` теперь читает `STRING MUTE` партий загруженной сцены и шлёт ноту как датчик. Все 23 сцены перемерены дважды (расхождение ≤ 0.8 дБ), метрика — K-взвешенная громкость ноты по открытым струнам. Бас трёх сцен в пределах 1.5 дБ; соло-сцены (кроме «Солнышка») на 4–12 дБ ниже цели F; сцены 2, 3, 6, 11 на 19 дБ тише якорной. Сцена 14 не менялась. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | GM-800: запас по уровню, тихие сцены на длинных нотах

Копия `SCENE LEVEL` и `PART LEVEL` всех 23 сцен: `gear/gm-800/backups/2026-11-19-levels.json`. Соло-сцены 4 и 22 уже на максимуме общего уровня (127) и всё равно на 4–6 дБ ниже цели F — подъёмом всё не выровнять, нужно опускать опору. Сцены 2, 3, 6, 11 на 6-секундных нотах и аккордах не раскрываются (−30…−36 против −14 у сцены 8). На приборе ничего не менялось. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] song | Not Gonna Get Us (t.A.T.u.) заведена из JamZone

Alex: плейбек из английской версии в JamZone, в плейбеке всё кроме гитары, базовые cue с упором на стопы барабанов и смены гармонии. `cat_25870` → 15 стемов, 130 bpm. pb-other = клавиши/синты/арпы/fx/бэки, pb-bass = Synth Bass, claves выкинуты. 12 черновых cue (стопы на последний удар 4&). Рендер с practice-миксами для steve/tanya/alex. В Stage Traxx не синкалась. [Страница](songs/tatu-not-gonna-get-us.md).

## [2026-11-19] song | Нас не догонят: русская версия, pitch −4

Alex: поём русскую версию, питч всего −4, английские бэки из pb-other убрать. Sound effects — шумовой райзер вне тональности, оставлен без питча слоем `parts/sound-effects.wav` (stem-frame, replaces оригинал). Стартовый cue — «Нас не догонят drums in». OFF не изменился. Строка дашборда привязана к папке. [Страница](songs/tatu-not-gonna-get-us.md).

## [2026-11-19] rig | Нас не догонят в Stage Traxx; синк теперь автоматом

`stagetraxx_sync.py --apply "Нас не догонят"`: новая песня, 7 треков, длины = рендер. Alex: после рендера синкать в Stage Traxx автоматически, не спрашивая. [Страница](songs/tatu-not-gonna-get-us.md).

## [2026-11-19] rig | GM-800: сцены подогнаны к целям (опора −5 дБ)

Alex: «опускаем опору», роли 14 сцен от него. Цели по громкости ноты: бас −22.1, F −20.1, A −24.1. По SysEx в память слотов: подгонка `SCENE LEVEL` / `PART LEVEL` с перемером. На цели 14 из 22 сцен, ещё 3 в пределах 2 дБ; 7 сцен упёрлись в максимум и ниже цели на 3.6–7.9 дБ (30, 29, 3, 6, 23, 2, 28). «Мало тебя»: сцена 11 → MUTE (соло-сцена 12 осталась), засинкано в Stage Traxx. Копии уровней до и после — `gear/gm-800/backups/2026-11-19-levels*.json`. Синт стал тише на 5 дБ — вернуть на пульте. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] song | Нас не догонят: правки cue и концовка на 110.1

Alex: all in на сильную долю (7.1), после стопов — drums in 31, solo in 47, drums in 70.3& (по полдоли), 62 — «drums only in 3», концовка для всех на 3:21 (end in → 110.1), всё дальше обрезано (fade 0.8 с + `cut_after_last_cue: 1`, 203.08 с). Stage Traxx обновлён. [Страница](songs/tatu-not-gonna-get-us.md).

## [2026-11-19] rig | GM-800, сцена 28: панорама и возврат уровня

Alex: патч «Попрошу тебя» играет то вправо, то влево. Подтверждено по записи; моно-свёртка занижает его на 3 дБ (и широкие сцены 2, 3, 6 на 2–3 дБ). `SCENE LEVEL` сцены 28 возвращён с 127 на 86: подъём не давал прибавки громкости. Открытый вопрос: синт идёт на пульт в моно или стерео — от этого зависит, чем мерить. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] rig | GM-800: итог подгонки в стерео

Alex: синт идёт на пульт в стерео; сцена 2 в исходном виде должна быть тихой, цель — аккомпанемент с CTL1. Замер переведён на стерео-сумму L+R, сцены подогнаны заново: 17 на цели (±0.8 дБ), 3 / 6 / 2-с-CTL1 в пределах 2 дБ, не дотянулись на максимуме 23 (−2.5), 30 (−3.5), 29 (−3.8); сцена 28 (панорама) возвращена к исходному и не тронута. Сцена 2 возвращена к исходным уровням, CTL1 = партии 3 и R. Проверочный проход повторён после обрыва USB-кабеля; NOTE SOURCE = GK IN. [level-anchors](pipelines/level-anchors.md).

## [2026-11-19] song | Нас не догонят: chorus in 31, voice in 63, концовка без обрыва

Alex: 0:55 → chorus in, ~1:54 voice in (вход вокала 63.1), концовка обрывалась слишком резко. Теперь после удара 110.1 плейбек доигрывает такт 110 и гаснет за такт 111 (fade 111→112, cut 2 такта, 204.92 с); барабаны в all глушатся сразу после удара. Stage Traxx обновлён. [Страница](songs/tatu-not-gonna-get-us.md).

## [2026-11-19] rig | GM-800: правки уровней пережили выключение питания

Alex выключил и включил прибор. Уровни всех 23 сцен, прочитанные по SysEx, совпали с `gear/gm-800/backups/2026-11-19-levels-after.json` (изменено 16 сцен). NOTE SOURCE = GK IN.

## [2026-11-19] rig | Калибровка дома на FLOW 8: три ручки, не четыре

Все шины Stage Traxx на FLOW 8 идут в USB 3/4 → канал 7/8 (prefs, шины на 0 дБ). Домашний порядок: гитара 5/6 → плейбек 7/8 по «Владивостоку» → синт 3+4 по «Солнышку». Отношение pb-bass/pb-other дома = шины Stage Traxx. Записано в `wiki/pipelines/level-anchors.md`.

## [2026-11-19] rig | Исключения опережения переключений: поле `lead` в записи

Стандарт остаётся (POD Go за 1 с, GM-800 сцены/CC за 0.5 с до такта). Для одной смены его заменяет `"lead": сек` в записи `podgo` / `gm800` / `gm800_cc`; отрицательное = позже такта. `tools/stagetraxx_sync.py` (`entry_lead`, `send_sec`, проверка порядка отправки), тесты в `tools/jamzone/tests/test_podgo.py` (54 passed). Dry-run по всей программе до и после правки совпал: в данных исключений пока нет. Медведица в итоге не размечалась (Alex передумал, см. следующую запись).

## [2026-11-19] rig | Владивосток 2000: пресеты POD Go за 300 мс до такта (`switch_lead`)

Alex: вся песня — смены за 0.3 с вместо стандартной 1 с. Новый ключ уровня песни `"switch_lead": сек` в mix.json (`song_lead` в `tools/stagetraxx_sync.py`; число = все приборы, `{"podgo": 0.3}` = один; `lead` в записи главнее). В `music/songs/Мумий Тролль - Владивосток 2000/mix.json` стоит `"switch_lead": 0.3`. Синк `--apply --quit "Владивосток"` выполнен, теги в базе Stage Traxx проверены: 00:10.781 / 00:40.331 / 00:56.953 / 01:26.503 / 01:56.052 / 02:10.827 (= `abs_sec` − 0.3). Перерендера не было. На приборе не проверено.

## [2026-11-19] rig | Калибровочная песня из настоящих кусков

Alex: гитара во «Владивостоке» мягче живой, а искусственный звук не нужен. Собрана песня `music/songs/_Калибровка/` (`tools/calibration_track.py`): гитара `malo-guitars` из «Мало тебя» 21–37 (ближе всех к 32D по спектру, −16.6) и бас из «Солнышка» 9–25 (−19.1), чередование 8 тактов запись / 8 тактов клик. В Stage Traxx — «Калибровка уровней», служебная (`SERVICE_SONGS` в `tools/stagetraxx_sync.py`). Описание: `wiki/pipelines/level-anchors.md`.

## [2026-11-19] rig | Владивосток 2000: 2-й куплет остаётся на 32D

Alex: на 2-м куплете (такт 30) пресет не меняется. Из `podgo` убраны записи такта 30 (32B) и такта 46 (32D, стала повтором). Теперь 32A (1) → 32B (5) → 32D (21) → 32A (62) → 32D (70), смены за 0.3 с. Засинкано в Stage Traxx.

## [2026-11-19] rig | Калибровочная песня: каждый регион ставит свой пресет и сцену

Alex: регион должен сам ставить патч на синт и POD Go. В `music/songs/_Калибровка/mix.json` переключения стоят в начале каждого из 15 регионов (`"resend": true`, новый ключ в `tools/stagetraxx_sync.py`). Регион «ты» начинается за такт до вступления.

## [2026-11-19] song | Ты меня не ищи: финал = повтор припева

Alex: «после 3:10 нужно повторить припев и закончить». Такты 1–107 как были (стоп 107, 4 выстрела). С 108.1 копия припева 2 (83–98) во всех стемах и pb-слоях, сдвиг 25 тактов; конец на его стопе 123.3, cue `end in` (count). Синт-аутро записи и «Take it out!» убраны, длина та же (127 тактов). Монтаж — `arrange()` в `tools/jamzone/prep_ty_menya_ne_ishchi.py` (шаг `all`), стыки по стемам: барабаны/pb-fx 108.1, вокал 107.1& (затакт «ты меня не ищи»), остальное 107.4&. GM-800 сцена 27 на 108 (бас вживую), pb-bass мьют с 108, мьют pb-keys/pb-wah 108–123 снят. Проверено: до стыка стемы побайтно прежние, такты 108–124 рендера = 83–99 (pb-other/pb-bass/all ±0.1 дБ), клик ±1.7 мс. Stage Traxx: `--apply`, бэкап `music_library-20261119-224558.sqlite`, 7 треков сверены с рендером. Прод не публиковался. [virus-ty-menya-ne-ishchi](songs/virus-ty-menya-ne-ishchi.md).

## [2026-11-19] song | Ты меня не ищи: последний припев = первый, без остановок

Alex: «последний припев должен быть без остановок как первый, по длительности как 0:45–1:33… никаких сбивок» (1:33 прочитано как 1:13: 0:45–1:13 = ровно припев 1, такты 25–40; на 1:33 середина синт-брейка с остановками барабанов). Вместо копии припева 2 (drum-bass stop, single drum) с 108.1 теперь копия припева 1, сдвиг 83 такта; затакт вокала с 106.4&; финальный удар 124.1 = крэш записи 41.1, синт-рифф «synth only» вырезан, такт затухания. Cue с 108: «chorus in», «end in» (count) на 124.1. До стыка стемы побайтно прежние, после = запись со сдвигом. Stage Traxx `--apply`, бэкап `music_library-20261119-225646.sqlite`, 7 треков сверены. Прод не публиковался. [virus-ty-menya-ne-ishchi](songs/virus-ty-menya-ne-ishchi.md).

## [2026-11-19] song | Ты меня не ищи: последний припев без плейбека, FX-концовка обратно

Alex: «в конце нужно убрать плейбек, сейчас слышу синт и wah; сделать как было — в конце был fx». `pb-keys`/`pb-wah` `mute [107.75, 130]` (с 107.4: вход пэдов припева на последней восьмой тоже глушится), pb-bass уже с 108. `pb-fx` больше не монтируется (в записи пуст 108.1–124.1) — снова прежний файл, FX «Take it out!» на 124.1 поверх финального удара; `FX_GAIN` убран. В pb-other с 107.4 до 124.1 тишина. Stage Traxx `--apply`, бэкап `music_library-20261119-231023.sqlite`, 7 треков сверены. [virus-ty-menya-ne-ishchi](songs/virus-ty-menya-ne-ishchi.md).

## [2026-11-19] song | Ты меня не ищи: FX-концовка на 2 доли позже

Alex: «на 2 счёта позже должна быть fx фраза». «Take it out!» в `pb-fx` перенесена со 124.1 на 124.3 (`F3_AT = 529` в `prep_ty_menya_ne_ishchi.py`); остальной pb-fx без изменений. Stage Traxx `--apply`, 7 треков сверены. [virus-ty-menya-ne-ishchi](songs/virus-ty-menya-ne-ishchi.md).

## [2026-11-19] song | Попрошу тебя: концовка возвращена до конца голоса

Alex: «была срезана (отрубили концовку), вернуть, но только до 3:20, где голос заканчивает». Рендер резался после крэша 93.1 (2:41). Голос в записи кончается на крэше 119.1 (оригинал 3:21.7, рендер 3:25.6), дальше инструментальное аутро. Конец теперь 119.1: `prep_poproshu_tebya.py stems` фейдит все стемы 119.2& → 119.3e − 20 мс (на 119.3e барабанный подход в аутро, `cut_after_last_cue` режет только по тактам). Cue черновиком по записи: 93 `stop` (было `end in`), 94 `synth solo ready go`, 102 `pause in` (count), 111 `all in`, 119 `end in` (count). Рендер 207.3 с; клик ±1.7 мс; до 119.2& стемы побайтно прежние. Stage Traxx `--apply`, бэкап `music_library-20261119-232146.sqlite`, 7 треков сверены. Прод не публиковался. [virus-poproshu-tebya](songs/virus-poproshu-tebya.md).

## [2026-11-19] analysis | Попрошу тебя: свип фильтра в синт-соло 94–101 и как повторить на GM-800

Замер по барабанам против тактов 86–91: резонансный ФНЧ на весь микс. Проход 1: 94.2–95.3 ~300 Гц, к 97.4 до 4.9 кГц. Сброс на 98.1 (~140 Гц). Проход 2: к 100.4 до 8.9 кГц, 101.1 открыт. Горб резонанса +6…+10 дБ. В соло 20–27 и 53–60 свипа нет. GM-800: вариант А — SuperFilter в FX сцены 29 + ASSIGN CC→`FX1 SPR FILTR CUTOFF`; вариант Б — CC74/CC71 на канале сцены (относительный сдвиг TONE MODIFY). Для обоих нужна рампа CC в `stagetraxx_sync.py` (пока только одиночные значения). Не сделано, ждёт решения. [virus-poproshu-tebya](songs/virus-poproshu-tebya.md#свип-фильтра-в-последнем-синт-соло-такты-94101--разбор-2026-11-19).

## [2026-11-19] tool | GM-800: подбор звука под партию стема (`tools/gm800_match.py`), «Попрошу тебя» куплет 1

Alex: «первый куплет играть бас на гитарном синте… какой из басов подходит больше и будет ли вровень». Новый инструмент: синт сам играет партию из стема по USB-MIDI (сцены банды или ROM-тоны во временной сцене, в память ничего), гармоники + огибающая против стема, уровень на пульте через басовый якорь «Солнышко», mp3 в контексте; список тонов прибора `gear/gm-800/tones.tsv` (официальный Sound List). Итог: стем — квадрат; лучший тон 645 Juno Sqr Bass (сцены банды все пила); сцена 7 по громкости вровень с `pb-bass` (0…+0.6 дБ), 645 в шаблоне сцены 7 на 6.6 дБ тише. В mix.json и на приборе ничего не менялось — ждёт выбора. [gm-800-match](pipelines/gm-800-match.md), [virus-poproshu-tebya](songs/virus-poproshu-tebya.md).

## [2026-11-20] song | Попрошу тебя: бас куплета 1 на GM-800 (сцена 31 POPROSHU BASS)

Alex выбрал 645 Juno Sqr Bass. Сцена 31 (была INIT) = сцена 7 + тон 645 в партии 1, партии 2–4/R выкл., собрана во временном буфере и записана по SysEx целиком (88 блоков, сверено чтением), PART LEVEL 78 → 127: на пульте −19.5 против `pb-bass` −19.3. `mix.json`: `gm800` 28 → 29 (11) → 31 (28, `"lead": 0` — соло в 27 до барлайна; сцена встаёт за ≤100 мс, до первой ноты баса 190 мс) → 29 (44), `pb-bass` mute 28–44. Рендер: изменился только `pb-bass`, OFF прежний. Stage Traxx `--apply`, бэкап `music_library-20261120-001533.sqlite`, 7 треков по 207.295 с, PB Bass = рендер (−79 дБ остаток), теги `PC30@2` 0:49.682 / `PC28@2` 1:16.593. Инструмент: `gm800_match.py build` / `level`. Дампы слота: `gear/gm-800/backups/sysex/`. ⚠️ Сцены 30–31 есть только на приборе, в лайвсете `.tsl` их нет. [virus-poproshu-tebya](songs/virus-poproshu-tebya.md), [gm-800-match](pipelines/gm-800-match.md).

## [2026-11-20] publish | Прод: Попрошу тебя, Ты меня не ищи, Нас не догонят

Alex: «обнови рендеры на проде». `tools/sync_site.py`: 42 из 953 миксов изменились, 42/42 залиты в R2 (Попрошу тебя — бас куплета 1 на GM-800 и концовка до 119; Ты меня не ищи — правки концовки 19.11; t.A.T.u. «Нас не догонят» — плейбек и cue). Guide: 3 новые версии `all.wav`, каталог `music/guide-catalog.json` (MISSING `_Калибровка` — служебная, без all.wav, норма). Vercel prod READY (`web-ten-psi-12.vercel.app`, `dpl_7EfzZvbosrGRicifNB4x4bE3inEc`). Сверка md5 R2 (`?v=`) против локальных mp3 — 4 из 4 совпали. Перед публикацией проверено: незакоммиченная правка сетов 28.10 в `tools/setlist_dashboard.py` уже была на проде (в `web/songs.json` публикации 3590421).

## [2026-11-20] gear | Попрошу тебя: свип фильтра GM-800 из Stage Traxx (рампы CC + SuperFilter)

Alex: «да, делай» на разбор свипа 94–101. `stagetraxx_sync.py`: `"ramp": true` в `gm800_cc` = плавный CC от предыдущей записи к этой, тег каждые ≥30 мс при смене значения, без опережения 0.5 с; тесты (106 passed). GM-800 слот 29 по SysEx (`tools/gm800_superfilter.py apply`, бэкап `gear/gm-800/backups/slot29-superfilter-20261120-002002.json`): FX1 = SuperFilter LPF −24 дБ Res 50 Gain +3 (хранится выключенным), партии 1–2 → FX1, PARALLEL, ASSIGN 1 CC#81 → cutoff (цель 407), ASSIGN 2 CC#81 = 127 → FX1 выкл (цель 361). Калибровка CC → Гц и проверка на приборе: при CC 127 звук как до правки (±0.1 дБ), горб +6…+10 дБ как в записи, ступенек нет. mix.json: 94.1 CC40 → 95.3 46 → 97.4& 113, 98.1 24 → 101.1 127. Stage Traxx `--apply`, 179 тегов CC81. Параллельная сессия в это время добавила сцену 31 (бас) на 28–43 — не пересекается. [gm-800](pipelines/gm-800.md), [virus-poproshu-tebya](songs/virus-poproshu-tebya.md).

## [2026-11-20] song | Попрошу тебя: GM-800 сцена 28 на «pause in» 102

Alex: «после 102 на pause in должно быть переключение на 028». `gm800` + `{"bar": 102, "scene": 28}` (стандартные 0.5 с → 2:55.958). Сцены: 28 → 29 (11) → 31 (28) → 29 (44) → 28 (102). Stage Traxx `--apply`, PC27@2 на 2:55.958 в базе, CC81 без изменений. [virus-poproshu-tebya](songs/virus-poproshu-tebya.md).

## [2026-11-20] pipeline | Практис-дорожки Drums / Vocals / All: уровень рядом с плейбеком

Alex: «эти стемы надо по громкости убавить, сейчас после калибровки бас тихо на фоне их». Замер 65 песен: стемы сайта на громкости оригинального мастера, барабаны −23.8…−10.5 при pb-bass около −19. `tools/stagetraxx_sync.py`: `PRACTICE_LEVEL` (Drums −17, Vocals −21, All −16), громкость дорожки = цель − замер, не выше 0 дБ, кэш замеров `~/.cache/cherry-daddies/stagetraxx-levels.json`. Применено ко всей программе (66 песен). Ручные фейдеры Alex на «Ты меня не ищи» (Drums −6.3, Vocals −7.0) заменены расчётом (−6.2, −5.4). Страницы: [level-anchors](pipelines/level-anchors.md), [stagetraxx-rig](pipelines/stagetraxx-rig.md). На слух не проверено.

## [2026-11-20] song | Ты меня не ищи: клавиши плейбека из переднего плана в аккомпанемент

Alex после калибровки баса: «плейбек громче звучит, чем нужно», на вопрос о роли — «да, в аккомпанемент». `pb-other` → `pb-keys` `gain_db` 8.3 → 4.3: клавиши −17.0 → −21.1, `pb-other` −16.9 → −20.2, `pb-bass` −18.2 как был, оффсет рендера 3.441 без изменений. В Stage Traxx. Страницы: [песня](songs/virus-ty-menya-ne-ishchi.md), [level-anchors](pipelines/level-anchors.md). На слух не проверено.

## [2026-11-20] pipeline | Клавиши плейбека F → A ещё в четырёх песнях

Alex: «давай все их тоже в А». Солнышко `roma-keys-2810` +0.6 → −3.4 (−20.9); Такая любовь `takaia_lubov_keys` +1.5 → −2.5, `roma-keys-2810` +2.2 → −1.8, `gain_bars` соло 3 → 7 (аккорды −21.0, соло −17.8); Beverly Hills `roma-keys-2810` +3.0 → −1.0 (−21.0); Попрошу тебя стем `keys` +3.5 → +1.6 (−21.0). Клик, `pb-bass`, OFF прежние. В Stage Traxx, PB Other сверен с рендером. Таблица: [level-anchors](pipelines/level-anchors.md). На слух не проверено.

## [2026-11-20] pipeline | Клавиши плейбека звуками GM-800: подход и первая партия

Alex: вырезанные стемы клавиш плохо звучат на большом звуке, партии надо прописать звуками GM-800, чтобы он мог играть их вживую, а потом они шли из плейбека тем же звуком. Начали с куплета «Ты меня не ищи». Новая страница [gm-800-parts](pipelines/gm-800-parts.md), инструмент `tools/gm800_part.py` (`probe` / `take` / `preview`), файл партии `music/songs/Вирус - Ты меня не ищи/parts/verse-keys.notes.json` (черновик). Найдено по стему: Am – F – C – G, низкий голос A1+A3 / G1+G3, верхний E4 A4 C5 / F4 A4 C5 / C5 E5 G5 / B4 D5 G5; MIDI из сети в двух аккордах расходится. Сцены 57 и 51 разобраны по партиям, записаны дубли тактов 9–12, mp3 для слуха готовы. Ждёт Alex: ноты и выбор партий.

## [2026-11-20] pipeline | Клавиши куплета «Ты меня не ищи»: страница прослушивания, верхняя До в такте 3

Alex: «собери страничку, чтобы проще было слушать», затем «не хватает какой-то верхней ноты в 3 такте». Страница `analysis/gm800-match/Вирус - Ты меня не ищи/preview-part/index.html` (локальная, синхронное A/B). По стему в такте 11 найдены C6 (+7.9 дБ против дубля без неё) и E4; в `verse-keys.notes.json` добавлены варианты `high-c6` и `high-c6-e4`, записаны с прибора, смеси на странице. Ждёт выбора Alex. [gm-800-parts](pipelines/gm-800-parts.md).

## [2026-11-20] song | Ты меня не ищи: клавиши куплета утверждены, сцена 32 NE ISHI PAD, табы

Alex: «отлично, берём 3, и мне табы что играть». Вариант 3 = смесь B (JP Soft Strings + Aurora Pad + OB Bright Str) с E4 и C6 в такте 3; `parts/verse-keys.notes.json` зафиксирован (`low`, `high`, `live`). Слот 32 прибора: NE ISHI PAD из заводской 51 (Aurora 127, OB Bright Str 64, октава партий +1), записан и сверен. `mix.json`: `gm800` + такт 9 → 32, такт 17 → 27 (`lead` 0.3), CC80 на 17 `lead` 0.1; в Stage Traxx. `tools/gm800_part.py`: + `balance`, `scene`; `gm800_match.py` `Sx.dump` отбрасывает блоки, которые прибор шлёт сам. Табы и остаток работ: [gm-800-parts](pipelines/gm-800-parts.md). Слой плейбека не записан.

## [2026-11-20] song | Ты меня не ищи: клавиши куплетов в плейбеке звуками GM-800

Alex: «да, записывай». `tools/gm800_part.py` + `record` (дубль с меткой времени: нота на сцене 7 даёт задержку записи, 7–9 мс) и `layer` (дубли → `parts/pb-keys-verse.wav`, stem-фрейм). Шесть дублей: низкий голос 9–24 (сцена 57, JP Soft Strings + Hybrid Strings), верхний 17–24 и 67–82 со сцены 32, во втором куплете низкий только A3/G3. `mix.json`: слой `pb-keys-verse` (`derived`, +6.5), `pb-keys` mute `[9, 25]`, `[67, 83]`. `pb-other` в куплетах −21.0, в 9–16 −28.1. Живая сцена 32 по якорю (G +4.66) −22.5 против −22.1 у того же голоса в слое — SCENE LEVEL не менялся. OFF прежний, в Stage Traxx. Прод не обновлён, на слух не проверено. [gm-800-parts](pipelines/gm-800-parts.md).

## [2026-11-20] pipeline | Табы в Stage Traxx

Alex: «табы можешь сделать, чтобы показывались в Stage Traxx». `stagetraxx_sync.py` `song_tabs`: строки `"tab"` из `parts/*.notes.json` идут под заметкой с доски. «Ты меня не ищи»: четыре аккорда куплета (лады от 6-й струны к 1-й), в Stage Traxx. Там же в [gm-800-parts](pipelines/gm-800-parts.md) таблица, где в песне ещё остались вырезанные клавиши (припевы 25–40 и 83–98, подложка strings 41–56).

## [2026-11-20] pipeline | Табы в Stage Traxx: табулатура по струнам, моноширинный шрифт

Alex прислал скриншот Stage Traxx со строками «аккорд — лады» и рядом ASCII-табулатуру: нужен второй вид. `"tab"` в `verse-keys.notes.json` переписан табулатурой; в Stage Traxx включён `lyrics_fixedWidthFont` (моноширинный шрифт текста, на все песни). В базе текст проверен, на экране не проверено.

## [2026-11-20] song | Ты меня не ищи: припевы и высокая нота на GM-800, Moises-клавиш в плейбеке больше нет

Alex: «припевы переведи на gm 800… ещё заменить на соло подкладку, длинный писклявый звук… в любой такой песне задача убрать полностью moises звук клавиш; исключения только эффекты, которые нельзя воспроизвести». Припевы по стему = тот же пэд (низкий голос без нижней октавы, в 91–98 с ней). Файл партии → `parts/keys-pad.notes.json`, слой `pb-keys-pad` (9–40, 67–98, длинные дубли, мьют к 41 и к стопу 98.3). Высокая нота = A6 в 41–56, тон 272 Soft Glass Pad из 16 кандидатов (`gmp tones`), `parts/keys-solo-pad.notes.json`, слой `pb-keys-solo-pad`. `pb-keys` из `mix.json` убран. `tools/gm800_part.py`: + `tones`, дубль ROM-тоном (`"tone"`), `"fade"`. Уровни секций прежние (−21 в куплетах и припевах), OFF прежний, в Stage Traxx. Правило записано в `CLAUDE.md` и [gm-800-parts](pipelines/gm-800-parts.md). Прод не обновлён, на слух не проверено.

## [2026-11-20] song | Ты меня не ищи: с «drum-bass stop» клавиши играет Alex

Alex: «drum bass stop — после этого я буду играть, нужно убрать из плейбека клавиши и добавить переключение эффекта на gm 800». В 91–98 из `pb-keys-pad` убран верхний голос (`"fade": [91, 91.75]` у дубля 67–99), низкий оставлен как в 9–16. `gm800` + `{"bar": 91, "scene": 32, "lead": 0.1}` (бас доигрывает 90.4&). Таб подписан «9-16 и 91-98». `pb-other` 91–98: −22.7. В Stage Traxx. [gm-800-parts](pipelines/gm-800-parts.md).

## [2026-11-20] song | Ты меня не ищи: соло на сцене 34 NE ISHI SOLO 2 (копия 147); банк 1 GM-800

Alex: «там, где я играю соло, хочу разнообразить: переключить эффект на 147 на solo in», затем «не надо ctl1, я сам буду крутить ctl 2». Сцену 147 по обычному PC не вызвать, поэтому она скопирована в слот 34 (`gm800_part.py copy`), scene level 55 → 73 (вровень со сценой 30: −18.1 против −17.8 LUFS по USB). `mix.json` `gm800` + `{"bar": 58, "scene": 34}`, в Stage Traxx (PC33@2 на 1:42.4). Попутно найдено и записано в [gm-800](pipelines/gm-800.md): банк 1 (`CC0=0 + CC32=1`, или сцена ≥ 129, выбранная руками) заставляет прибор игнорировать обычные PC; инструменты теперь шлют банк 0 перед PC, теги Stage Traxx — нет (в todo).

## [2026-11-20] pipeline | Stage Traxx: сброс банка перед каждой сменой сцены GM-800

Alex: «да, добавь». `stagetraxx_sync.py`: теги сцен GM-800 = `CC0.0@2, CC32.0@2, PC<n>@2` (`bank0` в `DEVICES`), POD Go без изменений. Вся программа пересинкана (41 песня со сценами), тесты `test_podgo.py` обновлены (44 прошли). Проверка на приборе: банк 1, сцена 147 → запуск Stage Traxx → стартовая сцена песни встала. [gm-800](pipelines/gm-800.md).

## [2026-11-20] rig | GM-800: сцена 30 звучала на струнах баса — разбор, не воспроизведено

Alex: после переключения на 30 из Stage Traxx звук только на струнах 5–6 («как для баса»), настройки на экране верные, руками сцена работает. Данные сцены и слот 30 по SysEx верные и не менялись. Четыре прогона с записью звука прибора (простой PC, с банком 0, цепочка песни с CC80 и сценой 32, настоящий прогон из Stage Traxx, после банка 1) — везде сцена 30 звучит на 3–4 струнах. Причина не найдена; описание и таблица проверок в [gm-800](pipelines/gm-800.md), пункт в todo.

## [2026-11-20] song | Ты меня не ищи: бас раньше перед 108; сцена 30 −4 дБ не доделана

Alex: «108 chorus in — нужно раньше переключить на бас; пресет 030 сделай потише на 4 дБ». `gm800` такт 108: `"lead": 1.3` (тег 3:08.830), в Stage Traxx. Сцена 30: команда SCENE LEVEL 80 отправлена, но GM-800 перестал отвечать на запросы по USB — не проверено (todo). Наблюдение: прибор отдавал ответы с отставанием на 28 сообщений (по одному на каждый входящий запрос), потом замолчал совсем; безвредные CC очередь не двигают.

## [2026-11-20] rig | GM-800: сцена 30 NE ISHI SOLO тише на 4 дБ

После перезапуска прибора он снова отвечает. Слот 30: SCENE LEVEL 127 → 80, замер фразы A3–A4 по USB −20.4 → −24.4 LUFS (−4.0 дБ). Сцена 34 не тронута (−18.6 на той же фразе), вопрос о ней в todo. Записано в [level-anchors](pipelines/level-anchors.md) и [gm-800](pipelines/gm-800.md) (сбой ответов на SysEx, закон SCENE LEVEL 20·lg).

## [2026-11-20] rig | GM-800: в сцену 34 добавлен плак сцены 30

Alex: 34 не убавлять; «посмотри, можно ли в сцену 34 добавить что-то из 30, чтобы 34 была ультра-навороченной версией 30», затем «сразу запиши плак в свободную, я проверю сам». Разбор сцен по дампам: 30 = два Lo-Fi Comp Pluck в октаву, сухие, струны 3–4, CTL1 октава, CTL2 модуляция; 34 = три лида через FX1, партия 4 выключена, CTL1 = вкл/выкл партии 4, CTL2 = подтяжка +12 у всех четырёх партий. `tools/gm800_part.py` + `part` (перенос партии между сценами: 9 блоков, блок струн остаётся от целевой сцены). Партия 1 сцены 30 → партия 4 сцены 34, уровень 127, сверено чтением. Замер: плак −26.3, лиды −18.6, сцена −19.2 LUFS. [gm-800](pipelines/gm-800.md).

## [2026-11-20] song | Ты меня не ищи: сцена 30 на 41 раньше, Reso Bass во всех басовых местах

Alex: «переключение на 41 synth only тоже надо раньше, на секунду где-то; бас сделай везде, чтобы был как в куплете первом». `gm800` такт 41: `"lead": 1.5` (1:11.761). `gm800_cc` CC80: 0 → 127 (17) → 0 (41) → 127 (67) → 0 (100) → 127 (108), возврат на Hammer в припеве убран; Hammer только в интро 1–8 (не уточнено, нужен ли Reso и там). Проверено на приборе: PC27 + CC80=127 через 0.2–0.3 с → Reso Bass вкл., Hammer выкл.; перезагрузка 27 при CC80=127 без сброса даёт обе партии сразу. В Stage Traxx.

## [2026-11-20] song | Ты меня не ищи: высокая нота на соло перезаписана на сцене 32

Alex: интро оставить на Hammer; «перезапиши длинную высокую ноту в плейбеке клавиш, это должна быть длинная нота на 032». `keys-solo-pad.notes.json`: дубль со сцены 32 вместо тона 272, `pb-keys-solo-pad` `gain_db` 0.4 → 11.1, `pb-other` 41–53 −26.6 как было. OFF прежний, в Stage Traxx, PB Other сверен.

## [2026-11-20] song | Ты меня не ищи: сцена 34 во второй половине второго соло, пэд в последнем припеве

Alex: «во втором соло на второй его части надо также переключить на соло 2 пресет; в последнем хорусе нужно вставить плейбек клавишный». `gm800` + `{"bar": 104, "scene": 34, "lead": 0.1}` (середина соло 100–107, по стемам явной границы нет). `keys-pad.notes.json`: голоса `high` и `low2` + такты 108–123, три новых дубля; `pb-keys-pad` mute `[[41, 67], [98.5, 108], [124.25, 130]]`. `pb-other` 108–123 −21.1, OFF прежний, в Stage Traxx.

## [2026-11-20] pipeline | Гайд «Снятие партий»; Ты меня не ищи: убраны смена на 104 и FX-концовка

Alex: «убери переключение на втором соло и убери fx концовку; по результатам сессии составь гайд, как работать с подобными запросами («снятие партий»)». `mix.json`: запись `gm800` такта 104 удалена, `pb-fx` `mute [[124, 130]]`; после 124.25 в `pb-other` тишина; в Stage Traxx. Новая страница [part-transcription-guide](pipelines/part-transcription-guide.md): вопросы, порядок из 9 шагов, грабли, чек-лист. В репозиторий перенесены рабочие инструменты сессии: `tools/part_notes.py` (ноты стема по тактам, `--track`, `--take`), `gm800_part.py loudness`, пример страницы прослушивания `tools/templates/part-listen-page.example.html`. Замечено: SCENE LEVEL сцены 30 на приборе сейчас 105 (Alex менял сам).

## [2026-11-20] song | Мама Люба: синты keys + wind + strings переведены в ноты и записаны с GM-800
- Запрос Alex: «сними и запиши партию клавиш»; объём — все три синт-стема, всё в плейбек, звуки «выбери сам по патчам». Moises раскидал один синт по трём стемам — партии сняты по сумме: пэд (G♯m–B–C♯, = брасс MIDI), бас интро, стаб куплета, щипок, хук (pyin по `wind`, четыре такта H1 H2 H1 H4 + варианты). Генератор `tools/jamzone/prep_mama_lyuba.py`, ноты `parts/synths.notes.json`.
- Звуки перебором `gm800_part.py sweep` (новая команда; ~530 тонов): пэд 256 Bright Brass Oct + 287 Aurora Pad, хук 922 Wave Shape Ld (моно-тон → основной, квинта, октава ниже отдельными дублями), бас 129, щипок 354. Сайдчейн записи повторён `duck`. FX (удары, шумы) — слой `pb-fx` из стемов.
- 48 дублей, слой `pb-synths`, `mix.json` `pb-other` = layers, рендер, Stage Traxx (PB Other = рендер). Уровень `pb-other` −18.1 (был −18.2). На слух не проверено.
- Инструменты: `part_notes.py` — mp3-стемы, ноты в тональности группы, `--roll`/`--period`; `gm800_part.py` — `sweep` (+ журнал `gear/gm-800/tone-sweeps.json`, `--from-history`), `duck`, `transpose`; `gm800_match.Song` — `gm800: 1`. Гайд дополнен. Атлас тонов — в todo, ждёт решения Alex.

## [2026-11-20] song | Мама Люба v2: хук по ритму MIDI, аккорды пэда встык
- Alex по v1: «после длинной ноты обрыв — третья нота в основном риффе, должно быть легато» → пауза 30 мс перед аккордом давала у Bright Brass Oct провал 15–19 дБ; голосам пэда/баса `"gap": 0.002` (новое поле голоса в `gm800_part.py`). «Соло звучит косячно» → A/B простого рендера MIDI и моих нот (`tools/midi_preview.py`), решение «по миди»: хук переписан ритмом брасс-дорожки MIDI (соло, kick stop, вариация, билд; в последнем припеве — ритм соло, в MIDI там хука нет). Перезаписано 50 дублей, уровни по стему, рендер, Stage Traxx, ссылки v2.

## [2026-11-20] song | Мама Люба v3: бенд на длинных нотах хука (kick stop, вариация)
- Alex: «во втором проходе в соло длинные остановки на нотах — в оригинале что-то типа бенда». pyin 6 мс: A♯/F поднимается на ~65 центов к соседнему полутону и резко возвращается. GM-800 MIDI pitch bend не принимает → кривая бенда в ноте `notes.json`, `gm800_part.py layer` гнёт дубль rubberband `--pitchmap` (поправка опережения карты 64 мс). Без перезаписи на приборе. Рендер, Stage Traxx, ссылки v3. В первом проходе соло оригинал гнёт так же, но там оставлены ноты MIDI — по слову Alex.

## [2026-11-20] song | Мама Люба v4: бенд во всех проходах хука
- Alex: «да, давай» — бент-оборот (A♯↗B↘A♯ G♯ / F↗F♯↘F D♯) и в первом соло; оригинал гнёт так же в 110–117 и 118–125 → H1/H2 = K1/K2 везде (4-й такт без бенда). 9 дублей хука перезаписаны, уровни в пределах ±0.8 дБ, рендер, Stage Traxx, ссылки v4.

## [2026-11-20] song | Мама Люба v5: FX в тональности группы, аккорды пэда внахлёст
- Alex по v4: соло хорошо; во вступительном риффе мини-перерыв на 3-м аккорде; интро и куплет в разных тональностях. `pb-fx` (из стемов в B♭m) не транспонировался — теперь сдвигается на −2 при сборке. Провал ~60 мс на входе C♯ (4.3, без бочки) — аккорды пэда внахлёст 40 мс, сайдчейн подогнан по огибающей записи (6 дБ / 35 мс / −30 мс), B и C♯ −2 дБ. 24 дубля пэда перезаписаны, рендер, Stage Traxx, ссылка v5.

## [2026-11-20] song | Попрошу тебя: ритм в соло-блоках — сцена 28 вместо стема keys
- Alex: «вместо стемовых ритмов записать с моими пресетами там, где я поверх играю соло». MIDI (MIDIfind, такт MIDI +2 = наш): стабы на «и», Cm–A♭–E♭–B♭; расклад по стему. Шесть блоков, где Alex на сцене 29 играет лид/соло: 11–18, 20–27, 44–51, 53–60, 85–92, 94–101. Сцена 28 «как играешь» (`as_played` в `gm800_part.py`: всем партиям одна нота). Стем keys там замьючен, слой `pb-rhythm`; `pb-other` в блоках −23 LUFS (= стабы в 3–10). Stage Traxx обновлён.
- (тот же день) Alex: «убрать» стем keys и в 61–84 (его «Клавиши 2» и лид на сцене 29): мьют keys 53–92 целиком. Рендер, Stage Traxx, ссылка `temp/poproshu-gm800-rhythm-pb-vox-drums-cues-v1.mp3`.

## [2026-11-20] song | Попрошу тебя: слот 28 насыщен (316 + эхо 1/8), ритм в плейбеке переписан; стем keys только на заезде
- Alex: первая запись ритма «звучит по-другому» и не проверялась — причины: velocity 100 (на 1.7 кГц ярче оригинала; подобрано 63 по центру спектра) и бедный пресет. По перебору 32 суперсо-тонов и решению Alex: в слот 28 партия 4 = 316 Trance Syn Poly (oct 0, level 100), Chorus/Delay сцены = DELAY 1/8 (`tools/gm800_poproshu28.py`). Шесть блоков перезаписаны «как играешь», сила 63; стем keys выключен и в интро/конце (Alex играет ритм сам), остался заезд 1–2. Рендер, Stage Traxx. Правило: клип A/B для Alex до плейбека (память агента).

## [2026-11-20] rig | Футсвич Ampero Control управляет Stage Traxx
- Alex купил Hotone Ampero Control. По Bluetooth macOS видит его только после Connect в Audio MIDI Setup; на сцену — USB-кабель (порт `Ampero Control`).
- Банк 00 был пустой — педали молчали. Запрограммирован из приложения (CC 20–23, ch 16, Single, Output USB). Save в приложении падал с «Connection failed», лог Mac-версии показал: банк уходит целиком, пульт рвёт связь после записи — банк сохранился.
- Раскладка Alex: FS1 стоп и в начало, FS2 предыдущая песня, FS3 пауза/старт, FS4 следующая песня. Формат MIDI-триггера снят с Learn, назначения пишет `tools/stagetraxx_remote.py --apply --quit --launch`. AirTurn Support в Stage Traxx выключен.
- Детали и грабли: [stagetraxx-rig](pipelines/stagetraxx-rig.md#футсвич-ampero-control-2026-11-20).
- (тот же день) Слот 29 (лид/соло Alex): к клавесину слоем 198 Fat Mask Dist Ld в партию 3 (выход FX1, +3 дБ к клавесину), выбор Alex по клипу из короткого списка (полный перебор остановлен по его слову). На приборе 0.909 против оригинала (клавесин один 0.870). Сцена ~4 дБ громче. `tools/gm800_poproshu29.py`.
- (тот же день) Слот 29: 198 и клавесин «не вместе» (Alex). По MIDI вступают одновременно (< 1 мс). Причина в настройках игры партии 3: у 198 MONO + LEGATO + PORTAMENTO + CHROMATIC OFF, у клавесина POLY, TYPE2, без легато. Партии 3 поставлены настройки клавесина, записано в слот (`gm800_poproshu29.py match-store`). С гитары не проверено.
- (тот же день) Попрошу тебя: SCENE LEVEL слота 29 127 → 77 (со слоем 198 сцена была на 4.2 дБ громче одного клавесина, теперь +0.1). Бас 28–43 снова из плейбека (`pb-bass` без mute), GM-800 там 1 MUTE (Alex). Рендер и Stage Traxx `--apply`, PB Bass сверен с рендером.
- (тот же день) Попрошу тебя: соло без голоса (21/22–27, 53–60, 94–101) на уровне F. Слот 29 ASSIGN 3: CC#82 → SCENE LEVEL 77…127 (−24.8 → −20.5, F −20.1); `gm800_cc` CC82 с рампой на входе в соло 1, сбросы в 0 перед возвратами на сцену 29. Stage Traxx `--apply`, теги сверены. На слух не проверено.

## [2026-11-20] song | Знаешь ли ты (МакSим) заведена: Moises-минус, всё в плейбек, cue на старт/барабаны/модуляции/финиш
- Песня была в сетах «12.12 new songs» и «12.12 all» без папки (`NOFOLDER`). Стемы — Moises-минус без лид-вокала: «Vocals» = бэки → `backing_vocals.wav`. Папка `music/songs/МакSим - Знаешь ли ты/`, prep `tools/jamzone/prep_znaesh_li_ty.py`.
- Замеры: темп ровный 63.855 (барабаны на прямой ±1 мс), метроном Moises отстаёт на 37–52 мс и стартует со 2-й доли (аккорды на k%4 = 3, снейр на 2/4) → синтетический клик, барабаны на нём 0.0 ±1 мс. 1.1 = 0.165 с сырых стемов. Модуляции по аккордам на долях: C#m → Ebm 19.1 → Fm 44.1 → Gm 60.1 (аутро плейбеком).
- Плейбек: pb-other = piano/keys/strings/other/бэки, pb-bass = bass, барабаны живьём (practice-steve). 5 cue: «Знаешь ли ты playback in» 1.1, modulation in 19 и 44, drums in 24 (затакт барабанов 23.4a после «go»), end in 3 → 59.4 (последний удар). Модуляция 60 без cue: встала бы на отсчёт концовки, играет только плейбек.
- Рендер (каунт-ин +1 такт, 248.06 с), сайт localhost, Stage Traxx `--apply` (без плейлистов), треки сверены. Прод не обновлялся. Открыто: тональность группы, концовка 59.4 или 64.1 ([страница](songs/maksim-znaesh-li-ty.md)).
- (тот же день) Alex: аккорды в Stage Traxx по частям, без повторов последовательностей. Аккорды по долям из стемов (корень по басу), схема из 8 частей с ×N записана заметкой песни на доске через `/api/state`, Stage Traxx `--apply`, текст в базе сверен. Вид в самом Stage Traxx не смотрел; аккорды на слух не сверены.
- (тот же день) Alex: концовка остаётся на 59.4; POD Go 32C на всю песню, GM-800 MUTE (`"podgo": "32C"`, `"gm800": 1`). Stage Traxx `--apply`, теги `PC126@3` и `CC0.0@2, CC32.0@2, PC0@2` в базе сверены.
- (тот же день) Alex по скриншоту: схема аккордов некомпактна (вертикальные разделители, ×2 отдельной строкой). Причина: `[…]` Stage Traxx рисует как ChordPro-аккорды над строкой текста, а текст вне скобок уходит строкой ниже. Переписано обычным текстом, одна строка на часть, ×N в строке; Stage Traxx `--apply`. Находка про скобки записана в [stagetraxx-rig](pipelines/stagetraxx-rig.md).

## 2026-11-20 — Teen Spirit: синт-бас, черновики линий
- Идея Alex: синти-поп бас вместо бас-гитары, по типу интро «Я устал». Замер интро «Я устал» (Moises `bass.mp3`): октавные восьмые D♯2-D♯2-D♯3-D♯3 с шестнадцатыми в конце фразы, фильтр ходит (центроид 500–1000 Гц), энергия 60–250 Гц.
- Бас Teen Spirit снят со стема `03_Bass` на сетке клика (песня `click: follow`, `part_notes.py` не работает): петля F–B♭ | A♭–D♭ по полтакта, рифф после припева F–G♭ | C–B♭–A–A♭ (такты 46–49, 82–85).
- `tools/synth_bass_audition.py`: три линии (A/B/C) софт-синтом, такты 1–53, с группой и отдельно, громкость по LUFS бас-гитары. Страница `analysis/teen-spirit-synth-bass/index.html`. Ждёт выбора Alex ([todo](todo.md)); `music/` не тронут.
- (тот же день) Alex: название части всегда отдельной строкой, длинных строк не надо. Схема переписана: часть с тактами, под ней по строке на последовательность (самая длинная 23 знака). Stage Traxx `--apply`.
- (тот же день) Alex: экономить место — строки по 4–6 аккордов, последовательности через ` | `, без строк из 2–3 аккордов. Схема 17 строк (было 23), заголовок «Аккорды» убран. Stage Traxx `--apply`.
- (тот же день) Alex: различать цветом `×N` и `|`. В бинарнике Stage Traxx нашлась демо-песня с разметкой: `{c:<цвет>}…{c}`, `*жирный*`, `_курсив_`, `+подчёркнутый+`, `#`-заголовки. В `stagetraxx_sync.py` добавлена раскраска схем аккордов (`color_chart_note`): в заметке с `×N`/`|` аккорды зелёные, `×N` оранжевые, `|` серые. Доска остаётся чистым текстом (стейдж-лист). Stage Traxx `--apply` для «Знаешь ли ты»; вид на экране не проверен.
- (тот же день) Alex: «занесено в гайд?» Было частично (абзац в stagetraxx-rig + память агента). Добавлен раздел-гайд «Схема аккордов» в [stagetraxx-rig](pipelines/stagetraxx-rig.md#схема-аккордов-гайд-2026-11-20): как снимать аккорды со стемов, формат, запись заметкой через `/api/state`, синк, цвета, разметка Stage Traxx. Указатель в `CLAUDE.md` и index.
- (тот же день) Alex: «в районе 0:30 на сильную долю voice in». Рендер-таймкод → такт 7.1 (30.068 с, начало части 1 после интро). Cue `{"bar": 7, "text": "voice in"}`, рендер (OFF тот же 7.355 с; click/pb-other/pb-bass/all побайтно те же), слова на 6.1–6.4, Stage Traxx `--apply`, 6 регионов.
- (тот же день) Alex выбрал B: убрать шестнадцатые, ярче, в припеве те же ровные восьмые. Вариант B2 в `tools/synth_bass_audition.py`: без фигуры шестнадцатыми, фильтр открыт шире (центр спектра куплета 407 → 795 Гц), без плавания фильтра, звук один на куплет и припев, громкость нот выровнена (разброс восьмых 5.3 → 0.1 дБ). Страница обновлена, старый B оставлен для сравнения.
- (тот же день) Alex: «Мелом» добавить в лист 12.12 new, сделать pb bass. Добавлена в сет «12.12 new songs» (`tools/setlist_dashboard.py`, `web/songs.json`: 9 песен), Stage Traxx `--set "12.12 new" --apply` (плейлист `CD · 12.12 new songs`, 9 песен, сверено в базе). pb-bass у песни уже есть с 2026-11-17 (Moises `bass`, +3.1 дБ, −20.8 LUFS, пик −0.5; трек PB Bass на шине 4) — заново не собирался, рендер не запускался. Вопрос Alex: устраивает ли стем или нужен другой бас ([Мелом](songs/melom.md)).
- (тот же день) Alex: «клавиши как будто не попадают в клик, смотрел по сетке?» Ошибка в моём анализе: кадр `int(sr·0.0005)` = 22 сэмпла читался как 0.5 мс → времена растянуты на 0.23 %, темп вышел 63.855 вместо 64.000, и проверка тем же кодом её не видела (клик отставал на 2.1 мс/долю, к концу ~полдоли). Перемерено с точным кадром: барабаны ровно 64.000, вход барабанов 24.1 (затакта нет), модуляции 19/44/60 на месте, последний удар 59.4&. Prep 64.0 / P0 1.1012, `mix.json` bpm 64, `end in` на 59.4&; рендер (OFF 7.339, voice in = 0:30.000), проверено по рендеру: барабаны против `click.wav` −1.4 мс во всех окнах. Stage Traxx `--apply`. Остальные песни с синтетическим кликом проверены тем же точным методом — дрейфа нет. Урок в памяти агента.
- (тот же день) Alex: тон софт-синта «пердящий», «возьми тон 025». ROM-тон 25 = EP + Strings, слот 25 = M&S BASS ONLY, взята сцена. `tools/synth_bass_gm800.py` (новый: ноты с собственными временами, потому что `gm800_part.py` требует ровный темп; привязка по синк-ноте как в `record`): 375 нот, партии 3 (98 MG Saw Bass, окт. −1) и 4 (100 Acid Bass), задержка записи 8.8 мс, −20.8 LUFS. Замер: первая нота 43.6 Гц (F1), атаки на 17 мс позже софт-синта, в полосе 0–60 Гц −5 дБ от всей энергии (у бас-гитары −22). На странице кнопки 5 / Y.
- (тот же день) Alex: сцена 25 «хорошо», «давай на 10 bpm быстрее её сделаем». `tools/jamzone/prep_teen_spirit_tempo.py`: все стемы ×128/118 (rubberband R3), клик пересобран по ударам, оригиналы в `jamzone-orig/`; кик−клик +7 мс до и после. `mix.json`: `bpm 128`, `stem_speed`, `pb-bass` = слой `synth-bass` (`replaces 03_Bass`, `gain_db 1.7`). Бас B2 на всю песню (1074 ноты; рифф, затакт и концовка руками) записан с GM-800 на сцене 25, `tools/jamzone/prep_teen_spirit_bass.py` (атаки −7 мс на сетку). Рендер: 279.375 с, pb-bass −19.2 LUFS, бас−клик в пределах ±1.2 мс; Stage Traxx `--apply`, 6 треков по 279.37 с. В `jamzone_render.py` добавлен `stem_speed` для `--sections`. Рендер шёл на рабочей копии с чужими незакоммиченными правками рендера (другая сессия): лид стал +1.505 с вместо целого такта.

## [2026-11-20] parts | Солнышко: клавиши выписаны нотами из MIDI для GM-800 (подготовка к записи, прибор занят)

- Alex дал MIDI с rusmidi.com: «по нотам хорошо подобрано»; стемы — ориентир, запись Ромы — ориентир по типу звука; места «alex in» живые, в плейбек не нужны.
- `tools/jamzone/prep_solnyshko.py` (`notes` / `plan` / `preview`): MIDI → `parts/synths.notes.json`, 14 голосов плейбека + `live`, 23 дубля. Наш такт = такт MIDI + 3 с такта 6.
- По стему исправлено: вступление (8 тактов одного мотива), офф-бит орган (квинта, не тоника), стаб и филл куплета. Версия «как в MIDI» — отдельным файлом для A/B.
- Страница сравнения на всю песню: `analysis/gm800-match/Demo - Solnyshko/preview-part/index.html`; новый шаблон `tools/templates/part-listen-full.html`.
- Не сделано: звук (тоны предварительные, по названиям), запись, слой, `mix.json`, рендер. На слух не проверено. Подробности: [страница песни](songs/solnyshko.md), [todo](todo.md).
- (тот же день) Alex: «подними громкость и добавь подсказки для голоса voice in в начале и после перерывов» (Мелом). pb-bass: `gain_db` 3.1 → 4.7 + `"peak": "limit"`, −20.8 → −19.2 LUFS (169 сэмплов у потолка, остаток −41 дБ). Вокал замерен по сумме `vocals` + `backing_vocals` (Moises разнёс голос по двум стемам): вступления на 5 (после интро) и 73 (после паузы 70–72); такт 44 — короткая пауза, вход на 45 уже под «all in». Cue: + `{"bar": 5, "text": "voice in"}`, 73 «drums in» → «drums-n-voice in» (слово занимает 71.4–72.1). Рендер прошёл новой версией скрипта (короткое вступление): OFF 3.975 → 2.689 с, слоёв и timed-текста у песни нет. Stage Traxx `--apply`: 11 регионов, PB Bass моно −22.3 LUFS ([Мелом](songs/melom.md)).
- (тот же день) Alex: «всё норм, сделай на эту песню 1A на POD Go». Мелом: `"podgo"` 32D → 01A, без рендера, Stage Traxx `--apply`, тег `PC0@3` в базе сверен ([Мелом](songs/melom.md)).
- (тот же день) Alex про ровную линию в 128: «нормально», просит ненавязчиво разнообразить; пока писались демо — «звучит классно, скомпонуй всю песню по своему усмотрению». Демо четырёх вариаций на сцене 25 (такты 14–53): `analysis/teen-spirit-synth-bass/variations/`. В плейбек пошла аранжировка ARR (`SECT` в `tools/synth_bass_audition.py`): куплеты реже и все три разные, пре-припев и припев полные с проходящей C в конце петли, синкопа на B♭ в каждой второй петле припева, под соло почти ровно. 971 нота, записано с прибора, слой пересобран (`prep_teen_spirit_bass.py ARR`), рендер (OFF тот же 1.229), pb-bass −19.4 LUFS, Stage Traxx `--apply`.
- (тот же день) Alex: «around 0:43 need cue chorus in» (Мелом). Рендер-таймкод → такт 21.1 (42.714 с, припев 1). Cue `{"bar": 21, "text": "chorus in"}`, рендер (OFF тот же 2.689 с; click/all/pb-bass побайтно те же), Stage Traxx `--apply`, 12 регионов ([Мелом](songs/melom.md)).
- (тот же день) POD Go для Teen Spirit по словам Alex (старт 04D, дисторшн и припевы 32D, куплеты 04A, соло 32A): 9 записей `podgo`, точки по стемам гитар; смены на чистый звук и на соло идут сразу после сильной доли (`lead` −0.15 / −0.1 / −0.15), после соло — через 2 с. `--check`, Stage Traxx `--apply`, теги `PC15/127/12/124@3` сверены в базе. Замечено: другая сессия в 22:21 перерендерила Teen Spirit в своём батче (тот же mix.json).
- (тот же день) Alex: «большая задача на снятие партии клавиш в песне беги от меня… по нотам и самой партии хорошо тут подобрано в миди файле… пока gm 800 занят делай все что требуется для записи». MIDI (midifind, 124 bpm, 139 тактов) разложен на наши такты (вступление +8, второе соло +4), 7 голосов в `parts/synths.notes.json` (`tools/jamzone/prep_begi_ot_menya.py`). По записи исправлено: удары припева (квинты октавой выше, ритм 1 · 2 · 2.75 · 3.5 · 4.25), арп (одна фигура C#4 D#4 E4 G#3), такты пэда и G#sus4 в бридже, нижняя октава лида; версия «как в MIDI» оставлена для A/B. Свеллы перед припевами — `parts/pb-fx.wav` из стемов. Страница сравнения `analysis/gm800-match/Беги от меня/preview-part/` (порт 8767). `mix.json`, рендер и Stage Traxx не тронуты; на слух не проверено ([Беги от меня](songs/begi-ot-menya.md)).
- (тот же день) Alex про ARR: первый куплет «под одиночные не катит», одиночные нигде не нужны; основной рисунок — прямые частые, раз в 4 такта небольшая вариация типа синкопы; правки хочет без прибора. ARR2: прямые везде, в каждом 4-м такте последняя ячейка — синкопа или проходящая C по очереди (32 места). Дубль склеен из B2 и ARR (`prep_teen_spirit_bass.py splice`, перенос по восьмым: у 9 ячеек длина донора отличалась на 9–37 мс), все 32 вставки проверены по уровню и высоте. Рендер: pb-bass −19.2 LUFS, секции −19.1…−19.3; Stage Traxx `--apply`.
- (тот же день) Alex про «Такая любовь»: «перед 2:48 за 1 сек переключить на 32A, перед 2:59 32C, на 3:17 на 32D». Новая запись `podgo` `{"bar": 93, "beat": 4, "preset": "32A"}` (гитарное соло, рендер 168.444 с), остальные точки уже стояли. Теги: 32C → 32D@01:17.2 → 32A@02:47.4 → 32C@02:58.6 → 32D@03:16.3, Stage Traxx `--apply` без запуска. Песня ещё на старом вступлении (OFF 2.995 с): `--check` новой версией рендера пишет `abs_sec` под OFF 2.314, чего в `auto-render/` нет — значения возвращены под текущий рендер; у слоёв нет `rec_off`, перевод на короткое вступление — отдельно ([POD Go](pipelines/pod-go.md)).
- (тот же день, вечер) Alex: «да, запускай». Перебор тонов на GM-800: 66 дублей, 10 голосов; первые места — рифф 330 Bright Pulse Key, стаб и октавы 316 Trance Syn Poly, орган 33 Perc Jazz Org 2, галоп 352 Super Saw Mild, акценты 970 5th Saw Lead Dly, пэд 285 VoiceFormant Pad, брасс 249 JP-8 Brass (у `sweep` и `strings` рейтинг ненадёжен). Первый прогон сорвала чужая смена сцены (Stage Traxx, перезапущенный параллельной сессией): в `sweep` добавлена проверка сцены с повтором дубля. Страница выбора звука `analysis/gm800-match/Demo - Solnyshko/preview-tones/index.html`, шаблон `tools/templates/part-tone-pick.html`. Запись Ромы на страницах поправлена на смену OFF рендера. Запись слоя не начата: ждёт выбора Alex.
- (тот же день) Alex про ARR2: «вот это кач». Просьбы: проигрыш после припева перед 2-м куплетом поинтереснее, потом ровно; cue verse in на вступление голоса, «guitar solo ready go» на соло, ending cue; Stage Traxx не перезапускать. ARR3: такты 50–53 чередованием октав + C (склейка обобщена до отдельных восьмых, 48 замен, высоты 50–53 проверены). Cue: verse in 18.2, guitar solo ready go 86.2, end in (count) 142.1 — слова сверены с кликом по `cues.wav`. Рендер: OFF 1.2268 (−2.3 мс от прежнего), pb-bass −19.2 LUFS. **Stage Traxx не синкнут** — ждёт разрешения на перезапуск.
- (тот же день) Alex про «Такая любовь»: первый припев тоже на 32D, «причём он раньше должен начаться, когда вокал начинает тянуть последнюю ноту куплета». По `vocals.wav`: слог «-жно» начинается в 45.48 с рендера (согласная с 45.34), тянется на ре (294 Гц) до 49.5 с → событие такт 24 доля 3 (45.333 с). `podgo`: запись такта 43 заменена на `{"bar": 24, "beat": 3, "preset": "32D"}`, тег `PC127@3` в 00:44.333; Stage Traxx `--apply` без запуска ([POD Go](pipelines/pod-go.md)).
- (тот же день) Alex про «Беги от меня»: «Всё в плейбек» — все семь голосов клавиш идут в слой, живых нет ([Беги от меня](songs/begi-ot-menya.md)).
- (тот же день, вечер) Alex выбрал звук на слух: рифф 330 + «слой, как у Ромы», стаб 317 + FX, галоп и октавы 316, акценты 970, мелодия и пэд 287, струнные 1011, брасс 249; орган не подошёл («нет трубного / перегруз звука»). Второй перебор: 18 органов (впереди 35 VK Rotary Dist 1, 543 Full Organ OD) и 7 слоёв для риффа; пары «330 + слой» ранжированы по близости к Роме (впереди 1024 Trance Saws). `gm800_part.py layer`: эхо на дубль (`"delay"`). Страница второго круга `analysis/gm800-match/Demo - Solnyshko/preview-tones2/index.html`. Ждёт Alex.
- (тот же день) Alex: «а ты по одному тону собрался перебирать? кандидатов из пресетов нет?» (Беги от меня). В плане были только ROM-тоны. Добавлены сцены-кандидаты по составу всех 150 сцен лайвсета (43 дубля, пэд — сцена 3 BEGI OT MENYA), `prep_begi_ot_menya.py plan` печатает `gmp take` по сценам и `gmp sweep` по тонам, `rank` сводит их в один рейтинг ([Беги от меня](songs/begi-ot-menya.md), [гайд](pipelines/part-transcription-guide.md)).

## [2026-11-20] render | Короткое вступление: без целых тактов, все песни перерендерены
- Alex: «слишком долгое вступление; удали правило, что вступление — ровное количество тактов; главное разборчиво название, потом первая кью и поехали как можно быстрее; паузы между песнями сократить». `jamzone_render.py`: рендер начинается за 0.1 с до первого слова стартового cue (`LEAD_CLEAR`), музыка с затактом — за 0.05 с до первого звука (`MUSIC_CLEAR`); клик внешних песен якорится на такт 1.1 (`build_click(downbeat=)`), проверка клика сверяет фазу с тактом 1.1; `timeline.json` + `downbeat_sec`, `lead_sec`; линейка Logic от тактовой черты перед t=0. Время первого звука стартового cue считается точно (согласная до доли, длина объявления у стоп/count).
- Render-фрейм слои получили `rec_off` (OFF рендера, под который писали): рендер сам сдвигает их на (OFF − rec_off). TSV текстов (`tools/lyric-launcher/lyrics-timed`) сдвинуты на разницу OFF. Миграция: `tools/jamzone/migrate_lead.py prep|post`.
- Прогон (сабагент + вручную): 73 песни, все rc 0; плейбек против старого рендера — сдвиг 0.00 мс, corr 1.000 (у питчёванных S&M и «Нас не догонят» rubberband даёт другую форму волны, огибающая на месте); клик ≤ 2 мс (кроме follow и Sweet Dreams — как было). OFF короче у 46 песен, всего ≈ 45 с, больше всего «Знаешь ли ты» 2.7 с, «Я буду» 1.8, Shakira, What a Feeling, Felicità, Медляк, The Best, Coldplay ≈ 1.5; у JamZone-песен, где название и так влезало в начало стемов, без изменений. 34 TSV сдвинуты; клипы lyric-launcher не пересобирались (отстают на разницу OFF до пересборки).
- Stage Traxx: полный синк (67 песен, 13 плейлистов), Sunny/Shakira/Felicità досинкнуты после фикса первого слова. «Мама Люба» не перерендерена (чужие незакоммиченные правки пресетов POD Go в mix.json) — в Stage Traxx со старым длинным вступлением. Eva 2.0: в Stage Traxx играет старый июльский `auto-render/pb-bass.wav` при `"pb-bass": null`, после смены OFF он опаздывает на 1.15 с — ждёт решения Alex.
- (тот же день) Alex: Eva 2.0 — «убрать бас». Старый `auto-render/pb-bass.wav` (2026-07-11, при `"pb-bass": null`; с 16.11 играл в Stage Traxx, после короткого вступления опаздывал на 1.15 с) перенесён в Корзину, синк Eva `--apply`: треки Click / Cues / Drums / Vocals / All, PB Bass нет. Других песен с таким устаревшим pb-файлом нет (у «_Калибровка» pb-файлы пишет `calibration_track.py`, это задумано).

## [2026-11-20] analysis | Мало тебя: клавиши нотами для GM-800, подготовка без прибора
- Alex: «большая задача на снятие партии клавиш… пока gm 800 занят делай все что требуется для записи… особое внимание эффектам… вообще не понимаю как запись так круто звучит обволакивающе в припевах… malo tebya ch требует серьёзных доработок».
- Найдено: один широкий суперсо-пэд 13–118; «обволакивание» = аккорды maj7/9 с общими G4 и C5 + сайдчейн −7 дБ от бочки + некоррелированное стерео (низ в противофазе) + фильтр, открытый только в припевах; реверб умеренный. Запись ярче Ромы на 15–20 дБ выше 4 кГц. MIDI Nepke: трезвучия октавой выше, сайдчейн записан аккордами на «и», лид другой; хрома против оригинала 0.72–0.90, у нот по записи 0.90–0.97.
- Сделано: `tools/jamzone/prep_malo_tebya.py`, `parts/synths.notes.json` (6 голосов, 13 дублей, `duck`), `parts/malo-nepke.mid`, страница сравнения. `mix.json`, рендер, Stage Traxx, прибор не трогались ([страница песни](songs/malo-tebya.md)).
- Попутно: у песни устарели `abs_sec` cue (+0.836 с), из-за этого `part_notes.py` читал стемы со сдвигом; `gm800_match.Song` теперь берёт `downbeat_sec` из `timeline.json`. Тональность группы у песни — C minor (в доках стояло C# minor). Гайд дополнен четырьмя граблями.
- (тот же день, 23:05–23:40) Alex: «330+1024 нравится, 317 эхо как в записи, давай 537»; «да, занимай». Слой записан с GM-800: 25 дублей, две чужие смены сцены пойманы и переиграны, `check` чистый. `calibrate` (уровень групп по секциям, где группа одна; подгонка спектрограммы только для долей внутри группы) → `parts/synths.gains.json`; `gmp layer` → `parts/pb-synths.wav`; `fx` → `parts/pb-fx.wav`. Слой против оригинала: атаки −6…+1 мс, уровень секций −1.2…+0.5 дБ (последний припев +2.2). Страница результата `analysis/gm800-match/Demo - Solnyshko/preview-result/index.html`. **В плейбек не поставлено** — ждёт слуха Alex. По его просьбе сессии «Клавишная партия "Беги от меня"» отправлено, что GM-800 свободен.
- (тот же день) Alex: «Да, исправь» — cue в `mix.json` сведены в одну строку, `--check` обновил `abs_sec`/`snap_sec` 16 cue (аудио не писалось), `web/songs.json` пересобран.
- (тот же день, 23:37) Alex: «да, ставь». Слой клавиш GM-800 поставлен в плейбек «Солнышка» вместо записи Ромы: `mix.json` (`pb-synths` + `pb-fx`, derived, +0.4 дБ, mute со 145.15), рендер, `pb-other` I −21.0 (было −20.9), Stage Traxx `--apply`, файлы сверены. Замечание Alex: вводный рифф посуше, перезаписать — в todo. Вопрос Alex про рендер через ZENOLOGY вместо прибора: плагин установлен (AU + VST3), см. ответ в сессии; не внедрено.
- (тот же день) GM-800 освободился (сообщение сессии «Солнышко»), Alex: «когда освободишь прибор напиши в чат „мало тебя“». Беги от меня: 37 дублей на сценах + 47 тонов (два прогона, 23 + 5 минут), в память ничего не писалось. Слоты выше 128 `take` загрузил как N−128 (130 → 2 и т. д.) — пять дублей выброшены. Рейтинг: лид — сцена 84 SYNTH PLEDGE 0.88, свист — тон 886 Sine Lead 0.74, удары — сцена 101 0.65, арп — сцена 84 0.82, пэд — сцена 91 0.87 (сцена 3 Alex 0.81). Страница выбора `analysis/gm800-match/Беги от меня/preview-part/sound.html`. Прибор оставлен на сцене 1 MUTE, сессии «Мало тебя» сообщено. Звук не выбран, слой не записан ([Беги от меня](songs/begi-ot-menya.md)).
