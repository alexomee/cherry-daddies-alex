---
type: pipeline
updated: 2026-11-16
---

# Stage Traxx-риг (playback без клавишника)

Клавишника в группе больше нет, его MainStage-рига тоже (Alex, 2026-11-16: «делаем всё для локального Stage Traxx») → плейбек переехал с его MainStage на **Stage Traxx 4 на Mac** (4.0.15, карта Behringer FLOW 8, 4 выхода). Клавишник = Рома, он же основной басист — ушёл целиком: в 55 из 62 песен его бас (34) и синты/сакс (25) сейчас ничем не закрыты, списки — [roma](../people/roma.md). Раскладка выходов не меняется: **click / cues / pb-other / pb-bass**. Отдельного выхода под клавиши нет — партии клавишника идут слоем в `pb-other` (`layers`, см. [jamzone-render](jamzone-render.md)), баланс клавиш запекается в рендере.

Статус: **основной плейбек группы** (2026-11-16). Библиотека собрана генератором; вживую (звук по 4 выходам + MIDI в launcher) ещё не проверено. «Синк в риг» = `stagetraxx_sync.py --apply` (правило в `CLAUDE.md`).

## Генератор — `tools/stagetraxx_sync.py`

Аналог `sync_to_mainstage.sh`, но пишет библиотеку целиком (песни, треки, плейлисты, MIDI):

```bash
tools/stagetraxx_sync.py                    # dry-run, весь сетлист
tools/stagetraxx_sync.py --apply --quit     # записать (закрывает Stage Traxx)
tools/stagetraxx_sync.py --apply "S&M"      # только песни по подстроке (плейлисты не трогает)
tools/stagetraxx_sync.py --set "Music Hall" # только сеты по подстроке
```

- **Источник:** сеты и порядок — `web/songs.json`; стемы — `<song>/auto-render/{click,cues,pb-other,pb-bass}.wav`; номер клипа — `tools/lyric-launcher/songs.tsv`.
- **Разводка:** шина = стерео-пара выходов, панорама выбирает канал. bus0: Click L / Cues R; bus1: PB Other L / PB Bass R.
- **Моно-даунмикс:** стемы на входе сводятся в моно (`ffmpeg -ac 1`). `pb-other`/`pb-bass` — настоящее стерео, жёсткая панорама стерео-файла выкинула бы одну сторону.
- **`pb-drums`, `pb-other-keys`, `all`** в Stage Traxx не идут (выходов четыре).
- **Владение:** свои песни скрипт метит `song.notes = cd-sync:<папка>` и обновляет на месте; чужие (ручные) не трогает. Июньский импорт (плейлист «Cherry Daddies», 12 песен) удалён 2026-11-16. Свои плейлисты — `CD · <сет>`.
- **Безопасность:** dry-run по умолчанию; перед записью бэкап базы в `~/.cache/cherry-daddies/stagetraxx-backups/`; Stage Traxx должен быть закрыт.

## MIDI → lyric-launcher

В Stage Traxx 4 исходящий per-song MIDI есть только тегами в поле lyrics (поле «MIDI Trigger» = входящее). Генератор пишет:

```
[midi: PC<clip>@1]      загрузка песни → launcher армит клип NN
[midi@play: START]      play → клип катится с 0
[midi@stop: STOP]       stop → стоп-кадр
```

**BOSS GM-800** получает теги на канале 2 из ключа `"gm800"` в mix.json песни: стартовая сцена плюс смены сцен по таймкоду `[midi@MM:SS.mmm: PC<сцена−1>@2]`. Проверено вживую 2026-11-17, точность ±3 мс. Подробности: [gm-800.md](gm-800.md).

Stage Traxx шлёт во все MIDI-порты, виртуальный `LyricLauncher` получает их без настройки (launcher запускать первым). `wire_concert.py` и `.concert` для этого рига не нужны. Свет/видео — теми же тегами, включая таймкод `[midi@01:34.50: …]`.

Ограничения: play с середины песни тоже шлёт START → текст стартует с 0 (launcher не знает позицию). У песен без клипа (Eva 2.0, Ты меня не ищи, Попрошу тебя, Владивосток 2000, Sex on Fire) PC нет — только START/STOP.

## Формат библиотеки (реверс)

`~/Library/Containers/de.dikant.StageTraxx4/Data/`: `Library/Application Support/StageTraxx4/music_library.sqlite` (GRDB; `song`, `track`, `region`, `playlist`, `playlistSong`) + аудио в `Documents/<папка>/`. id — 16-байтные UUID-блобы; `track.filePath` относителен `Documents`; `track.volume` в dB; `track.bus` 0..15, `pan` −1..+1. iCloud-синк выключен (`syncMetadata` пустая). Ранние скрипты того же формата: `tools/jamzone/stagetraxx_render.py`, `jamzone_stagetraxx.py`.
