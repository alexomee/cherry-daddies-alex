# Пользовательский playback

## kukla-pb-other-v2.wav — 2026-10-07

Новый `pb-other` от Alex после репетиции: на репетиции прежний вариант (-17.9 LUFS) оказался слишком тихим.
Источник — `/Users/alex/Downloads/кукла колдуна other.mp3` (Logic Pro 11.2.2 bounce, 48 kHz / 320 kbps stereo, 206.784 с).
WAV сконвертирован 1:1 в 24 bit / 48 kHz stereo (`pcm_s24le`).
Уровни: **−14.9 LUFS-I / −0.1 dBTP**, gated stereo RMS **−18.22 dBFS**, mono **−19.19 dBFS**, LRA **8.6 LU** (~+3.0 LUFS громче v1).
Тайминг: точное посемпловое совпадение с v1 (лаг 0 мс, длительность 9 925 632 семплов).

`mix.json` использует этот файл как единственный layer в `pb-other`:
`{"file": "kukla-pb-other-v2", "frame": "render", "replaces": ["backing_vocals", "strings"]}`, роль `musical`.

`auto-render/pb-other.wav` содержит идентичный PCM плюс cue/LIST-метку `Tempo: 148.6` для MainStage Playback.
SHA256: `95220a9f10812855e9a3ff2c672638f8fb60280f1d1d9713761d6416b5c7b7fa`.
`auto-render/pb-other.mp3` пересобран с click/cues (`pb_other * 0.85 + click * 0.6 + cues * 1.0`, нормализация до 0.97).

Предыдущая версия v1 сохранена в `../versions/2026-10-07-before-louder-pb-other/`.
Синхронизировано в риг: `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кукла колдуна/pb-other.wav`.

## kukla-pb-other-v1.wav — 2026-10-01

Полный `pb-other` от Alex: бэк-вокал, скрипки, гитары. Источник — `/Users/alex/Documents/kukla_kolduna_pb_other.mp3`; согласованное ослабление **−2.5 dB** уже применено в WAV (24 bit / 48 kHz stereo). Уровни: **−17.9 LUFS-I / −2.6 dBTP**.

Фрейм **render**: начальная пауза включена, первый значимый звук около 3.24 с. Дополнительного сдвига/питча нет. Кросс-корреляция с прежним pb-other во вступлении находит общую часть с лагом около +22 мс; огибающая первых 50 с — +10 мс. Это не основание двигать заново сыгранные партии: передан тайминг пользовательского bounce. Конечная тишина длиннее старого рендера; после 205 с WAV нулевой.

`mix.json` использует этот файл как единственный layer в `pb-other`, роль musical (никаких дополнительных автоматических тримов). `replaces` исключает из будущего all-превью старые `backing_vocals` и `strings`; исходная `guitars` остаётся гайд-партией живого гитариста. Нельзя автоматически считать включённые в пользовательский bounce гитары полной заменой исходной гитарной дорожки.

`auto-render/pb-other.wav` содержит **идентичный PCM** этого WAV плюс cue/LIST-метку `Tempo: 148.6`, перенесённую из прежнего файла для MainStage. SHA256 файла с меткой: `2f90d49f1a5db8d76455a0bcfd53cf409d1f036e9927a9ef593f1cd9d33c4536`. `auto-render/pb-other.mp3` обновлён как прослушка группы с существующими click/cues на стандартных уровнях.

Предыдущие mix, pb-other WAV/MP3 и timeline: `../versions/2026-10-01-before-custom-pb-other/`. При этой поставке обновлены именно pb-other и его прослушка; all/practice и альтернативный pb-other-keys не пересобирались.

Риг: `cherry-daddies-2000/cherry-daddies-setlist-2026-06-16/Кукла колдуна/pb-other.wav`, побайтно совпадает с canonical auto-render. Коммит `be489c2a`.
