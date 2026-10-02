---
type: pipeline
updated: 2026-10-02
---

# MainStage-риг (боевой playback клавишника)

Клавишник — **мастер плейбека**: его ноут (MainStage) на концерте гонит **click + playback (pb-other/pb-bass) + cues** для всей банды. Stage Traxx как источник плейбека для этих песен больше не используется.

Из этого следует: **«готово отдать клавишнику»** = не синт-стемы, а **полный auto-render пакет по каждой песне** — `click.wav` + `cues.wav` + `pb-other.wav` (+ `pb-bass.wav`), выровненный, с темпо-метками, в тональности группы, который он грузит в MainStage Playback. Готовность песни = auto-render собран (click+cues+pb) + cue утверждены + состав pb решён + правильная тональность (`pitch_semitones`) + (для Moises) стемы финализированы, не черновик.

Пакет собирает [jamzone-render](jamzone-render.md) (`tools/jamzone/jamzone_render.py`), cue — по [cue-system](cue-system.md), тексты на монитор — по [lyric-launcher](lyric-launcher.md).

## Два репо

GitHub основного полного репо — `alexomee/cherry-daddies-alex`, рига —
`basbit/cherry-daddies-2000`. Самостоятельный lyrics-флоу Тани:
[памятка](../../docs/vocalist-workflow.md). Доставка одной проверенной песни:
`lyric_workflow.py deliver NN --apply` (перед этим `save NN`). Записывает source
commit в `lyrics/deliveries/NN.json`; обновления аудио этой песни после ревью
обнаруживаются по хешам. Push в GitHub рига ещё требует Pull на ноуте клавишника.

- **Фабрика** — этот репо `/Users/alex/projects/cherry-daddies` (рендер в `music/songs/<Song>/auto-render/`).
- **Риг** — отдельный репо `/Users/alex/projects/cherry-daddies-2000`, боевой MainStage-проект на ноуте клавишника. Сетлист-папка: `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/<NN Song>/`.

Перерендер песни в фабрике **сам риг не обновляет** — стемы в боевом проекте надо накатить.

## `tools/sync_to_mainstage.sh` — накат стемов в риг

Копирует из `<song>/auto-render/` в сетлист-папку рига **только те стемы, что УЖЕ лежат в целевой папке** (`click.wav`/`cues.wav`/`pb-other.wav`/`pb-bass.wav`), перезаписывая на месте. MainStage ссылается на аудио **по пути** → перезапись 1:1 = плагин видит новый звук без правок патча. `all.wav`/`cue_preview.mp3`/`timeline.json` — пайплайн-внутренние, не копируются.

- **Дефолт — dry-run** (показывает, что бы изменилось, с размерами). `--apply` реально пишет.
- Фильтр по подстроке: `tools/sync_to_mainstage.sh --apply "S&M"` (матчит и имя сет-папки, и имя песни-источника).
- Коммит в риге (без push): `tools/sync_to_mainstage.sh --apply --commit "S&M: re-render cues"`.
- Идентичные стемы пропускаются (`cmp -s`), выводит `changed / identical / missing-in-render`.
- Маппинг **сет-папка ↔ song-папка** — табличка `MAP` в самом скрипте (не из `web/songs.json`), `|||`-разделитель. На 2026-07-10 в `MAP` 23 записи.

### `MISSING in render`

В целевой папке стем есть, а в `auto-render/` — нет. Значит песню не дорендерили или стем переименован в `mix.json`. **Чинить рендер, не скрипт.**

### Новый / переименованный стем = только руками в MainStage

Скрипт **никогда не заводит и не удаляет** файлы стемов — только перезаписывает существующие. Добавление стема (напр. впервые подмешать `pb-bass` к песне, где его не было) или переименование делается **вручную**: открыть сет в MainStage → Playback-плагин → добавить дорожку на новый wav.

Причина: путь к wav лежит **только в бинарном `.cst`-блобе** Playback-плагина (не в чистом `data.plist`), имя сет-папки переменной длины → бинарная хирургия хрупкая, рискует побить патч. (В отличие от `wire_concert.py` из [lyric-launcher](lyric-launcher.md), который правит чистый plist-`channels` — там автоматизация безопасна.)

## Cue-only scope: только `cues.wav`

Правка **только cue-трека** (тембр/нота интро-тона и т.п.) должна уезжать в риг как **`cues.wav` и только он**. Но перерендер песни регенерит ВСЕ стемы, и `sync_to_mainstage.sh` тогда покажет `click`/`pb-other`/`pb-bass` тоже как «changed». Эти диффы — **дрейф пайплайна, а не правка**: обрезка хвостовой тишины, недетерминизм rubberband на питченных песнях (S&M `pitch_semitones:-2`), потолок громкости.

**Клик-сетка при этом идентична** (проверено: тот же счётчик кликов, 0.0мс дельта онсета, тот же downbeat) — меняется только длина хвоста. Значит новый `cues.wav` идеально ложится на СТАРЫЙ клик, остальное трогать не надо.

Как оформить (после `--apply <song>` для cue-only правки, перед коммитом в риге):

1. `git -C <RIG> checkout HEAD~1 -- "<SL>/<NN Song>/click.wav" .../pb-other.wav .../pb-bass.wav`
2. оставить только `cues.wav`, `git commit --amend`
3. проверить `git show --stat HEAD` = только файлы `cues.wav`

**БЕЗОПАСНО только пока клик-сетка не сдвинулась** — сперва подтвердить идентичность сетки (декод старого vs нового клика, сравнить онсеты). Если сетка реально сдвинулась — весь пакет едет вместе.

Прецедент 2026-06-22: гитарный интро-тон, коммит рига `29a0b33`, 3× `cues.wav` only.

## Границы

- `sync_to_mainstage.sh` и `deploy_clips.sh` (клипы lyric-launcher) `.concert` **не трогают** — там реверта нет.
- Правки MainStage-концерта (`.concert` = бинарные plist), lyric-проводка, `wire_concert.py` и регрессия-гард ручного фикса клавишника — в [lyric-launcher](lyric-launcher.md).

## Источники

- `CLAUDE.md` → «Обновление playback/cue в риге», «Practice-микс», «Тексты на сцене».
- `tools/sync_to_mainstage.sh` (маппинг `MAP`, механика).
- Память агента: `keyboardist-playback-master`, `sync-cue-only-scope`, `never-touch-logic-render`, `version-every-render`.
