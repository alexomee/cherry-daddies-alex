---
type: content
updated: 2026-07-10
status: pilot
title: Промо DANCE2000 (замена саундтрека)
---

# Промо DANCE2000 — пилот промо-видео пайплайна

Пилот (2026-06-14) переиспользуемого дома для промо/рекламных видео (зеркалит музыкальный пайплайн:
per-project папка + committed EDL + версионированные рендеры). Дизайн —
`/Users/alex/projects/cherry-daddies/docs/plans/2026-06-14-video-create-iteration-pipeline-design.md`.

## Статус

**Pilot, отрендерен.** Папка `/Users/alex/projects/cherry-daddies/assets/video/projects/dance2000-promo/`
(`src/` симлинки, `edl.json` коммитится, `auto-render/dance2000-promo_vN.mp4` gitignored).

## Задача

Пересобрать аудио промо события 26 июня `~/Downloads/DANCE2000 рус1.mp4` — заменить запечённый
Shakira-mix саундтрек новым песенным бедом, сохранив ElevenLabs-войсовер на исходной позиции.

- **bed** = SEREBRO «Мало тебя» (`music/youtube/Мало тебя [VsLGqtzAdic].webm`), seek `0:30`, на полную
  длину видео 22.04с, фейд-аут 0.8с хвост. См. песню [../songs/malo-tebya.md](../songs/malo-tebya.md).
- **vo** = ElevenLabs-дорожка (Дмитрий, 20.19с), задержана на **1.771с** — исходный онсет, измерен
  кросс-кором отдельного VO против сорс-микса. Верифицировано: VO в рендере на 1.771с ровно.
- **duck** = бед sidechain-компрессится войсовером (threshold 0.03, ratio 8, attack 20, release 300) →
  музыка проседает ~−12дБ под речью, восстанавливается в паузах.
- **mux** = заменено только аудио, `-c:v copy` (HEVC 1080×1920 не трогается).

## Гочи (из пилота)

- VO декодится дважды (два `-i` одного файла → sidechain-ключ + слышимая копия); `asplit` форк одного
  декода молча дропнул слышимую ветку (бед дакался, VO не было).
- Каждый стрим `apad,atrim=duration=<video>` до точной длины видео — иначе микс дрейфует (первый заход
  дал 21.68с аудио под 22.04с видео).
- Версия авто-инкрементится (`_v1`, `_v2`…) — рендер не перезаписывается.
- Knobs итерации (`edl.json`): `song_seek`, `vo_offset`, `bed_gain_db`, `vo_gain_db`, `bed_fadeout`,
  `duck.{threshold,ratio,attack,release}`. Рендерер `tools/video/render_audio.py`.
