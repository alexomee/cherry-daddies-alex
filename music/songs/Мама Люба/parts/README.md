# Пользовательский playback — Мама Люба

С 2026-11-20 `pb-other` — не вырезанные Moises-стемы `keys` / `strings` / `wind`, а два слоя (фрейм **stem**, `gain_db −10`, `derived`, источник keys + wind + strings). Подробности и цифры: `wiki/songs/serebro-mama-lyuba.md`.

## synths.notes.json

Ноты синтов в тональности группы (G♯m; стемы в B♭m, `pitch_semitones −2`), такты по `mix.json`. **Генерируется**, руками не править: `python3 tools/jamzone/prep_mama_lyuba.py notes` (рисунки, расклады, звуки, усиления — в скрипте). Голоса: `pad` / `padlow` (+ `_intro`, `_end`), `bass`, `bass_intro`, `stab`, `pluck`, `pluck_echo`, хук `lead` / `lead5` (квинта) / `leadsub` (октава ниже) в вариантах `""`, `_chorus`, `_var`, `_build`, `_end`. Раздел `layer` — 48 дублей: тон, такты, усиление, плюс сайдчейн `duck`.

## pb-synths.wav (вне git)

Слой, сыгранный самим GM-800 (ROM-тоны во временной сцене над INIT-слотом 33, сцен в памяти нет). Звуки: пэд 256 Bright Brass Oct + 287 Aurora Pad (−3 дБ); стаб 256; хук 922 Wave Shape Ld тремя дублями; бас интро 129 XMod Rubber Bass; щипок 354 Lo-Fi Comp Pluck. Сайдчейн: проседает 7 дБ на каждую бочку стема `drums`.

Пересобрать:

```bash
gmp() { uv run -q --python 3.12 --with sounddevice --with numpy --with scipy --with python-rtmidi --with soundfile --with pyloudnorm --with librosa tools/gm800_part.py "$@"; }
python3 tools/jamzone/prep_mama_lyuba.py notes
gmp record "Мама Люба" "music/songs/Мама Люба/parts/synths.notes.json"      # ~22 мин, нужен GM-800 по USB
uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with pyloudnorm --with sounddevice --with python-rtmidi python tools/jamzone/prep_mama_lyuba.py calibrate
gmp layer "Мама Люба" "music/songs/Мама Люба/parts/synths.notes.json"
python3 tools/jamzone/jamzone_render.py "Мама Люба" --practice
```

Дубли: `analysis/gm800-match/Мама Люба/rec-synths-*.wav` (вне git). Поменять звук голоса — `SOUND` в скрипте, `notes`, `record --only <номера дублей>`, `layer`. Убрать партию — удалить голос в `build()`, `notes`, `layer`.

## pb-fx.wav (вне git)

То, что в синт-стемах не ноты (удары-кластеры на сильных долях куплетов, шумовые всплески, хвост финального «падения»): сумма keys + wind + strings только в окнах FX, окна выписанных стаба и щипка вырезаны, удары в 102–109 — через фильтр ниже 150 Гц (над ними хук). `python3 tools/jamzone/prep_mama_lyuba.py fx`.
