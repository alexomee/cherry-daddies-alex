# Музыкальный пайплайн — JamZone / стемы / cue

Канонический дом музыкальной подготовки. Скрипты: `../tools/jamzone/` (перенесены из скила `jamzone-stems`; скил теперь ссылается сюда). Симлинк совместимости: `~/Desktop/jamzone-stems` → `music/songs/`.

```
music/
├── songs/<Artist - Title>/   ← по папке на песню (стемы + производные)
│   ├── NN_<Stem>.m4a         ← сырые стемы из JamZone (нативные песни)
│   ├── structure.txt          ← секции песни
│   ├── chart.txt              ← аккорды+структура (jamzone_chart)
│   ├── cues.json              ← редактируемые подсказки
│   ├── cue_track.wav          ← рендер cue-трека
│   ├── <click>.wav            ← клик
│   └── aligned/ + *-{stem}-…  ← внешние (Moises) песни: выровненные стемы
├── songs/jz_beat.wav, jz_downbeat.wav   ← сэмплы клика (используют click/cues_ext)
├── songs/.loudness_cache.json, .realm-*.bak ← артефакты normalize/setlist (не трогать)
├── setlists/                  ← сет-листы и лирика (booklet из jamzone-lyrics)
├── SONGS.md                   ← СТАТУС-БОРД: что готово, что делать
└── README.md                  ← этот файл
```

## Пайплайн на песню (порядок)

| # | Этап | Команда (из `tools/jamzone/`) | Результат |
|---|---|---|---|
| 1 | Извлечь стемы | `python3 jamzone_extract.py "<запрос>"` (или `--cat cat_N`) | `NN_*.m4a` + `structure.txt` |
| 2 | Чарт | `python3 jamzone_chart.py "<запрос>"` | `chart.txt` (потом руками докурировать) |
| 3 | Громкость | `python3 jamzone_normalize.py …` | per-song master (НЕ per-stem); сначала выставить мьюты, применять по требованию |
| 4 | Cue-трек (нативная) | `python3 jamzone_cues.py "<песня>"` | `cues.json` + `cue_track.wav` (+ `--audition` прослушка) |
| 4' | Cue-трек (внешняя/Moises) | `python3 jamzone_cues_ext.py …` | detect + matched click (см. скил-док) |
| 5 | Экспорт в StageTraxx | `python3 jamzone_stagetraxx.py …` | плейлист для сцены |
| 6 | Сет-лист в облаке | `python3 jamzone_setlist.py …` | reorder/rename (cloud-only, нужен token capture) |

Песня «готова к репетиции» = стемы + структура + cue-трек **отслушан** + громкость выровнена.

## Известные грабли (из боевого опыта)

1. **Clickgrid-баг (исправлен 10.06.2026):** старый `jamzone_cues.py` масштабировал время кликов на +0.227% → счёт «3-2-1» уезжал до полудоли к ~1:46. **Все нативные cue-треки, отрендеренные ДО фикса, требуют ре-рендера**: `jamzone_cues.py "<песня>"` без `--regen` (cues.json сохраняется, пересобирается только рендер). Список — в SONGS.md. Внешний `jamzone_cues_ext.py` не был подвержен.
2. **Тайм-привязка:** нативные треки — song-time = Logic-time − 1ч, без lead-офсета; внешние (Moises) несут lead. `click_grid` декодировать на 44.1k.
3. **Нормализация** — мастер на песню, не на стем; mute-конфиг до применения.
4. **Сет-листы JamZone — только в облаке**; правки через `jamzone_setlist.py` + перехват токена.
5. Пути в скриптах захардкожены на `~/projects/cherry-daddies/music/songs` (обновлены при переезде 11.06.2026).

## Подготовка к репетиции (рабочий цикл)

1. Открыть `SONGS.md`, выбрать 2–4 песни на репетицию (колонка «Действие»).
2. Догнать пайплайн по каждой (см. таблицу этапов).
3. **Отслушать cue** (`--audition`) — не пропускать, см. список неотслушанных.
4. Отметить статус в SONGS.md, собрать сет в StageTraxx.
