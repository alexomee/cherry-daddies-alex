# log

Append-only хроника вики. Формат: `## [YYYY-MM-DD] <op> | <заголовок>`.

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

## [2026-10-10] cues | It's Raining Men: обновление подсказок по JamZone сетке (15 cues)

По запросу Alex актуализирован набор cue для `The Weather Girls — It's Raining Men`:
- Сохранены стартовые подсказки: `bar 1.1` (3.440s, `It's Raining Men playback in`) и `bar 3.1` (6.880s, `all in`).
- `0:35 cue`: заменён на `bar 19.1` (35.040s) — `pre-verse in` («pre-verse in ready go»).
- `JZ section Verse`: добавлен `bar 27.1` (49.100s) — `verse in` («verse in ready go»).
- `JZ 01:14 (down beat)`: добавлен `bar 43.1` (77.270s, stem 74.49s) — `stop` («stop in 3 · 3 2 1») перед а капелла фразой «It's raining men».
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
- Выполнен рефайн подсказок:
  - Стартовый cue: заменён с «playback in» на `Gimme Gimme Gimme guitar in` (`bar 2.1`, 4.250s);
  - `drums in`: перенесён раньше на такт `10.2` (21.500s) — привязан строго к первому удару барабанного сбива Стива;
  - `verse in`: сдвинут на 1 долю раньше с 19.4 на `19.3` (40.130s) — ровно под вокальный затакт Тани «Half past twelve»;
  - Добавлен cue на секцию Intro 2: `bar 43.1` (87.600s) — `intro in ready go` (точно в сильную долю синтезаторного риффа, на 2 с раньше задержки JamZone);
  - Добавлен cue на секцию Verse 2: `bar 53.3` (108.520s) — `verse in ready go` (ровно под затакт «Movie stars», на 3.16 с раньше задержки JamZone);
  - Добавлен cue на стыке припевов: `bar 77.1` (155.990s, ~02:32 JamZone) — `keep going`;
  - Финальный cue: `bar 99.1` (199.740s) — `end in` (`count: true` $\to$ «end in 3 · 3 2 1»).
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
- В локальной базе веб-дашборда (`web/data/dashboard.db`) закрыты соответствующие задачи по Gimme (`remove solo part`, `end cue is not right`).
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
  - JamZone Instrumental: привязан строго к даунбиту секции `bar 55.1` (96.275s) с текстом `instrumental in ready go` (вместо старого «main in ready go» на 54.4);
  - JamZone Verse 3 (после Instrumental): привязан к даунбиту секции `bar 67.1` (117.669s) с текстом `verse in ready go` (вместо старого 66.4);
  - На стыке Chorus 3 → Chorus 4 (~02:25 JamZone): добавлен cue `bar 83.1` (146.195s) — `keep going`;
  - Финальный cue: исправлен с ложного 02:39 (bar 90.3 перед аутро) на реальный финал трека `bar 107.1` (188.983s, ~03:09 JamZone) — `end in` (`count: true` → «end in 3 · 3 2 1» с ударом на 03:09).
- Добавлены бэк-вокалы в плейбек (`pb-other`):
  - JamZone не экспортирует отдельную дорожку бэк-вокала, но содержит 3 дорожки лид-вокала оригинального состава (`09_Lead_Vocal_Angela_Brambati`, `10_Lead_Vocal_Angelo_Sotgiu`, `11_Lead_Vocal_Franco_Gatti`);
  - Все 3 вокальные дорожки подключены в `pb-other` с ролью `back-vox` (автоуровень по целевому потолку -23 dBFS: Angela -5.6dB, Angelo -5.7dB, Franco 0.0dB) и мьютом вне припевов JamZone: `mute: [[1, 23], [31, 47], [55, 75], [91, 109]]`;
  - В куплетах (Verse 1, Verse 2, Verse 3), интро, инструментале и аутро вокал в плейбеке полностью заглушен (поёт вживую вокалистка Таня), а в припевах (Chorus 1, Chorus 2, Chorus 3, Chorus 4) звучит полноценная 3-голосная вокальная пачка.
- Выполнен рендер через `jamzone_render.py --practice`:
  - Обновлены `mix.json`, `cues.wav`, `click.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `timeline.json`, practice-миксы (steve, roma, tanya, alex) и web-стемы.
- Актуализированы `tools/jamzone/setup_lefkara_27.py`, `web/songs.json`, `wiki/songs/ricchi-e-poveri-mamma-maria.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`.

## [2026-10-10] cues & mix | Maniac: cue main in (0:15), мьют ведущего синта в pre-chorus, chorus in на 1 долю раньше (3:31)

По запросу Alex выполнен второй цикл рефайна `Michael Sembello — Maniac`:
1. **Добавлен cue `main in ready go` на ~0:15:**
   - `bar 11.1` (15.120s, snap 12.101s) — вход основного грува (Rhodes, бас, синт) после драм-интро.
2. **Заглушен ведущий синт (`08_Synth_Keys_1`) во всех секциях pre-chorus:**
   - В `pb-other.mute` добавлено заглушение `08_Synth_Keys_1`: `[[35, 43], [77, 85], [133, 141]]` (Pre-chorus 1, Pre-chorus 2, Pre-chorus 3).
   - Теперь лидирующий синт не звучит в предприпевах и не дублирует партию гитары. В секции Bridge (такты 101–117) синт сохранён.
3. **Сдвинут cue припева Chorus 3 (~3:31) на 1 долю раньше:**
   - Перенесён с `bar 141.1` на `bar 140.4` (210.990s, snap 207.971s) ровно под вокальный затакт Тани («She's a...»);
   - Сам синт `09_Synth_Keys_2` вступает со 141 такта (211.28s, даунбит Chorus 3) и звучит до конца песни.
4. **Ре-рендер и синк:**
   - Выполнен полный рендер через `jamzone_render.py "Flashdance (Michael Sembello) - Maniac"`.
   - Обновлены `mix.json`, `cues.wav`, `click.wav`, `all.wav`, `pb-other.{wav,mp3}`, `pb-drums.{wav,mp3}`, `cue_preview.mp3`, `web/songs.json`.
762:    - Свежие `cues.wav` и `pb-other.wav` скопированы в риг MainStage через `tools/sync_to_mainstage.sh --apply "Maniac"`.
763:    - Обновлены `wiki/songs/maniac.md`, `wiki/index.md`, `wiki/gigs/2026-10-24-lefkara.md`, `tools/jamzone/setup_lefkara_27.py`.
764: 
765: ## [2026-10-10] cues & click | What a Feeling: выравнивание темпа клика интро (92 BPM) и полный рефайн подсказок
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
