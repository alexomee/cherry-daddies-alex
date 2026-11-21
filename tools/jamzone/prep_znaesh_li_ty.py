#!/usr/bin/env python3
"""One-off stem prep for «МакSим — Знаешь ли ты» (12.12, 2026-11-20). Rebuildable.

  python3 tools/jamzone/prep_znaesh_li_ty.py import <moises.zip>   # zip -> song root *.wav (renamed, unchanged)
                                                                   #   + moises-orig/ (Moises metronome, count-in)
  python3 tools/jamzone/prep_znaesh_li_ty.py metronome             # synthetic metronome.wav on the drum grid
then: python3 tools/jamzone/jamzone_render.py "МакSим - Знаешь ли ты"

Keys as notes (2026-11-21, Alex: «помоги снять песню», with the rusmidi MIDI and the ZENOLOGY guide;
wiki/pipelines/part-transcription-guide.md, wiki/pipelines/zenology.md):
  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  $P tools/jamzone/prep_znaesh_li_ty.py notes [<rusmidi.mid>]   # MIDI (-> parts/znaesh-rusmidi.mid) -> parts/keys.notes.json
                                                                #   + one file per stem group in analysis/.../notes/ (sweeps)
  $P tools/jamzone/prep_znaesh_li_ty.py preview                 # A/B page: stems / the MIDI notes in a plain synth
MIDI (rusmidi «znaesh_li_ty», 128 bpm = our 64 doubled, same key C#m, modulations included): one MIDI beat = an
eighth of ours, our bar 1.1 = MIDI beat 4 (bar 2). Track -> what it is in the record (share of the MIDI notes
heard in the stems, CQT, a note within 18 dB of the loudest of its window):
  T3  piano      piano stem: intro 1-6 100 %, 24-31 93 %, 40-59 65-80 %
  T4  low        held roots under the keys: keys + other 85-100 %
  T5  arp        the arpeggio from bar 7 (the MIDI calls it a jazz guitar; Moises split it over keys + other)
  T6  strings    strings stem, 1-6 and 12-59 (the record has strings in the outro 60-63 too; the MIDI does not)
  T7  lead       16ths in octaves, 44-59: the loud part of `other` in 48-55
  T8  bells      A6-G#8 in 1-23: 0 % in the intro, not in the record (kept for the A/B only)
  T9  horn       a trombone line 39-59: about half of its notes are heard - doubtful
  T10 hits       chord hits 43-46
  T11 drums (live), T2 lyrics: not used.

Source: Moises «Знаешь ли ты _minus_-Db minor-64bpm-441hz.zip» — a MINUS (no lead vocal): its «Vocals» stem is
the backing vocals only -> backing_vocals.wav (back-vox role, ceiling-leveled by the render).

Measured on the raw stems (wiki/songs/maksim-znaesh-li-ty.md):
  * tempo dead-constant 64.000 bpm: drum transients (knock 150-1k / snare 1-5k / hats 6-16k spectral flux,
    beat-synchronous fold per 16 beats, exact-sample hop) sit on one straight line through the whole drum
    part, -1..-2 ms, all bands agree -> no warp.
    (2026-11-20 fix: the first version said 63.855 — my analysis used hop=int(sr*0.0005)=22 samples read
    as 0.5 ms, which stretches every time by 0.23 %; the click drifted ~0.5 beat late by the end.)
  * the Moises metronome is NOT usable: it LAGS the drums by ~38 ms at 84 s growing to ~52 ms at 219 s
    (its own tempo is 63.993, and its intervals are quantized to 20 ms frames: 0.94 / 0.92 s), and
    its first click (raw 1.135 s) is beat 2, not a downbeat: chord changes land on Moises click k%4 == 3
    and the snare on k%4 == 0/2 (= beats 2/4). So bar 1.1 = raw Moises beat k = -1, where the piano
    starts (raw ~0.15 s).
  * no padding/trim: bar 1.1 sits at raw P0 - B = 0.164 s; the stems stay byte-identical to Moises.
  * drums + bass enter ON bar 24.1; the band's last hit is 59.4& (snare 4, kick 4e, hats 4&).
Beat index k = raw Moises click index (k=0 at its first click); bar = (k+1)//4 + 1.
"""
import os, sys, glob, shutil, subprocess, zipfile
import numpy as np

SR = 44100
SONG = os.path.expanduser("~/projects/cherry-daddies/music/songs/МакSим - Знаешь ли ты")
ORIG = os.path.join(SONG, "moises-orig")
BPM = 64.0
B = 60.0 / BPM
P0 = 1.1012                       # raw time of k=0 on the DRUM grid (Moises' own click there: 1.133 s)
K_BAR1 = -1                       # raw beat index of bar 1.1

# Moises file tag -> stem name in the song folder (None = kept out of the stem glob, in moises-orig/)
NAMES = {"Bass": "bass", "Drums": "drums", "Keys": "keys", "Piano": "piano", "Strings": "strings",
         "Other": "other", "Vocals": "backing_vocals", "Metronome": None, "Count-in": None}

S = lambda t: int(round(t * SR))
tk = lambda k: P0 + k * B          # raw beat k -> seconds (stems are not shifted)


def do_import(zp):
    os.makedirs(ORIG, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            tag = next((t for t in NAMES if f"_minus_-{t}-" in base), None)
            if tag is None:
                sys.exit(f"unknown file in zip: {base}")
            dst = os.path.join(SONG, NAMES[tag] + ".wav") if NAMES[tag] else \
                os.path.join(ORIG, tag.lower() + ".wav")
            with z.open(info) as src, open(dst, "wb") as out:
                shutil.copyfileobj(src, out)
            print(f"  ✓ {base} -> {os.path.relpath(dst, SONG)}")


def n_samples(p):
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True).stdout
    return S(float(d))


def do_metronome():
    n = n_samples(os.path.join(SONG, "drums.wav"))
    out = np.zeros((n, 2), np.float32)
    L = S(0.03); t = np.arange(L) / SR
    hit = (np.sin(2 * np.pi * 2000 * t) * np.exp(-t / 0.006)).astype(np.float32) * 0.8
    k = K_BAR1
    while S(tk(k)) + L <= n:
        s = S(tk(k)); out[s:s+L] += hit[:, None]; k += 1
    p = os.path.join(SONG, "metronome.wav")
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_s24le", p], input=out.tobytes(), check=True)
    print(f"  ✓ metronome.wav  synthetic {BPM} bpm, first click (bar 1.1) {tk(K_BAR1):.4f}s, "
          f"{k - K_BAR1} clicks, drums/bass in bar 24.1 = {tk(91):.3f}s")


# ---- keys as notes (2026-11-21) -------------------------------------------------------------------------------
import collections, importlib.util, json, time
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "analysis", "gm800-match", os.path.basename(SONG))
MID = os.path.join(SONG, "parts", "znaesh-rusmidi.mid")   # Alex 2026-11-21 after the A/B page: «Да, берём MIDI»
PART = os.path.join(SONG, "parts", "keys.notes.json")    # every playback voice, stems piano + keys + other + strings
NOTES = os.path.join(OUT, "notes")                       # one file per stem group: what the ZENOLOGY sweeps compare with
PAGE = os.path.join(OUT, "preview-part")
NN = "C C# D D# E F F# G G# A A# B".split()
END = 65                                            # bar after the last one
# voice -> (MIDI track, file = stem group, what)
VOICES = {"piano":   (3, "piano", "пиано: арпеджио вступления, потом аккомпанемент"),
          "bells":   (8, "piano", "колокольчики A6–G#8 (в записи не слышны)"),
          "arp":     (5, "keys", "арпеджио с такта 7"),
          "low":     (4, "keys", "держанные корни аккордов"),
          "strings": (6, "strings", "струнные"),
          "lead":    (7, "lead", "лид шестнадцатыми октавами, 44–59"),
          "horn":    (9, "lead", "тромбоновая линия 39–59 (под вопросом)"),
          "hits":    (10, "lead", "хиты аккордами 43–46")}
GROUPS = {"piano": ["piano"], "keys": ["keys", "other"], "strings": ["strings"], "lead": ["other"]}


def midi_tracks():
    """{track: [(our beats from bar 1.1, our beats long, midi)]}: MIDI beat 4 = our 1.1, two MIDI beats = one of ours."""
    import mido
    m = mido.MidiFile(MID); tpb = m.ticks_per_beat; out = {}
    for i, tr in enumerate(m.tracks):
        t = 0; on = collections.defaultdict(list); ns = []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on[msg.note].append(t)
            elif msg.type in ("note_off", "note_on") and on[msg.note]:
                s = on[msg.note].pop(0); ns.append(((s / tpb - 4) / 2, (t - s) / tpb / 2, msg.note))
        out[i] = sorted(ns)
    return out


def quantize(ns):
    """Onsets and lengths to 1/8 of our beat (the MIDI's own 16ths; its onsets sit a few ticks early), zero-length
    doubles out, a note held into the next attack of the same pitch ends there (its note-off would cut the new one)."""
    q = sorted({(round(s * 8) / 8, max(0.125, round(d * 8) / 8), p) for s, d, p in ns if d >= 0.04})
    nxt, out = {}, []
    for s, d, p in reversed(q):
        if p in nxt and s + d > nxt[p]:
            d = nxt[p] - s
        if d > 0:
            out.append((s, d, p))
        nxt[p] = s
    return sorted(out)


def as_notes(ns):
    grp = collections.OrderedDict()
    for s, d, p in ns:
        grp.setdefault((int(s // 4) + 1, s % 4 + 1, d), []).append(p)
    return [[b, bt, d, " ".join(f"{NN[p % 12]}{p // 12 - 1}" for p in sorted(ps))] for (b, bt, d), ps in grp.items()]


def write_part(p, about, stems, vs):
    """One note a line (a plain json.dump with an indent makes thousands of lines of it)."""
    j = lambda x: json.dumps(x, ensure_ascii=False)
    with open(p, "w", encoding="utf-8") as f:
        f.write("{\n" + f' "_about": {j(about)},\n "stems": {j(stems)},\n "voices": {{\n' + ",\n".join(
            f'  {j(vn)}: {{"at": [1], "bars": {END - 1}, "notes": [\n' + ",\n".join(f"   {j(n)}" for n in v["notes"]) + "\n  ]}"
            for vn, v in vs.items()) + "\n }\n}\n")
    print(p)


def cmd_notes(src=None):
    os.makedirs(NOTES, exist_ok=True); os.makedirs(os.path.dirname(MID), exist_ok=True)
    if src:
        shutil.copyfile(src, MID)
    T = midi_tracks()
    V = {vn: {"at": [1], "bars": END - 1, "notes": as_notes(quantize(T[tr]))} for vn, (tr, _, _) in VOICES.items()}
    about = ("«Знаешь ли ты», the keys of the playback as notes: the rusmidi MIDI (parts/znaesh-rusmidi.mid) one track "
             "per voice, quantized to 1/8 beat, mix.json bars, original key = band key (pitch_semitones 0). Alex "
             "2026-11-21 on the A/B page: «Да, берём MIDI». Generated by tools/jamzone/prep_znaesh_li_ty.py notes "
             "(edit there, not here).")
    for g, stems in GROUPS.items():
        write_part(os.path.join(NOTES, f"{g}.notes.json"), about + " Sweep file of one stem group.", stems,
                   {vn: v for vn, v in V.items() if VOICES[vn][1] == g})
    write_part(PART, about + " Not in it: the MIDI bells (track 8) - not heard in the record.",
               ["piano", "keys", "other", "strings"], {vn: v for vn, v in V.items() if vn != "bells"})
    for vn, v in V.items():
        bars = sorted({n[0] for n in v["notes"]})
        print(f"  {VOICES[vn][1]:8} {vn:8} {len(v['notes']):4} onsets  bars {bars[0]}-{bars[-1]}")


SRP = 44100
TIMBRE = {"piano": ("pluck", 5000, 0.7, 1.0), "bells": ("bell", 0, 0.6, 0.35), "arp": ("pluck", 3500, 0.35, 0.8),
          "low": ("organ", 900, None, 0.7), "strings": ("pad", 3000, None, 0.35), "lead": ("saw", 4500, 0.4, 0.5),
          "horn": ("saw", 1800, None, 0.5), "hits": ("saw", 3000, 0.25, 0.5)}


def synth(kind, fc, dec, f, dur):
    from scipy.signal import butter, sosfilt
    n = int((dur + 0.1) * SRP); t = np.arange(n) / SRP; ph = (f * t) % 1
    if kind == "pluck":
        x = sum(np.sin(2 * np.pi * k * f * t) / k * np.exp(-t * k / (dec * 3)) for k in range(1, 7) if k * f < 0.45 * SRP)
    elif kind == "bell":
        x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * (2.76 * f < 0.45 * SRP)
    elif kind == "organ":
        x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t)
    elif kind == "pad":
        x = sum(2 * ((f * r * t) % 1) - 1 for r in (1.0, 1.006, 0.994))
    else:
        x = 2 * ph - 1
    if fc:
        x = sosfilt(butter(2, min(fc, 0.45 * SRP), "lowpass", fs=SRP, output="sos"), x)
    e = np.minimum(1, t / (0.15 if kind == "pad" else 0.03 if kind == "organ" else 0.003))
    if dec and kind != "pluck":
        e = e * np.exp(-t / dec)
    k = int(0.08 * SRP); e[-k:] *= np.linspace(1, 0, k)
    return x * e * 0.2


def load_tool(name):
    s = importlib.util.spec_from_file_location(name, os.path.join(REPO, "tools", name + ".py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def cmd_preview():
    """Whole-song A/B page: the original keys stems and the MIDI notes in a plain synth (notes and rhythm, not
    sound), every group levelled to its stems; with or without drums / bass / backing vocals of the record."""
    import soundfile as sf
    gp = load_tool("gm800_part"); song = gp.gmm.Song("Знаешь ли ты"); os.makedirs(PAGE, exist_ok=True)
    n = int(round(song.t_render(END) * SRP)) + 2 * SRP
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")[0].mean(1)

    def placed(stems):                     # raw stems on the render timeline (pitch 0: band key = original)
        y = np.zeros(n); a = int(round(song.off * SRP))
        for st in stems:
            x = rd(song.stem(st)); k = min(len(x), n - a); y[a:a + k] += x[:k]
        return y

    def synth_voice(part, vn):
        y = np.zeros(n); kind, fc, dec, g = TIMBRE[vn]
        for t, m, d in gp.voice_line(song, part, vn, 1, END):
            x = synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)) * g
            a = int((song.t_render(1) + t) * SRP); k = min(len(x), n - a); y[a:a + k] += x[:k]
        return y

    def rms_where(x, ref):                 # RMS over the 1/8-bar cells where the reference plays (not silence)
        c = int(song.bar / 8 * SRP); m = len(ref) // c
        R = np.sqrt((ref[:m * c].reshape(m, c) ** 2).mean(1)); X = np.sqrt((x[:m * c].reshape(m, c) ** 2).mean(1))
        sel = X > X.max() * 10 ** (-40 / 20)
        return np.sqrt((R[sel] ** 2).mean()) / (np.sqrt((X[sel] ** 2).mean()) + 1e-12)

    orig = {g: placed(st) for g, st in GROUPS.items() if g != "lead"}
    parts = {g: json.load(open(os.path.join(NOTES, f"{g}.notes.json"), encoding="utf-8")) for g in GROUPS}
    mid = {}
    for g, part in parts.items():
        ref = orig["keys"] if g == "lead" else orig[g]
        for vn in part["voices"]:
            y = synth_voice(part, vn); mid[vn] = y * rms_where(y, ref) * (0.7 if vn in ("low", "horn", "hits") else 1.0)
    src = {"orig": sum(orig.values()), "orig-piano": orig["piano"], "orig-keys": orig["keys"], "orig-strings": orig["strings"],
           "midi": sum(v for k, v in mid.items() if k != "bells"), "midi-piano": mid["piano"], "midi-keys": mid["arp"] + mid["low"],
           "midi-strings": mid["strings"], "midi-lead": mid["lead"] + mid["horn"] + mid["hits"], "midi-bells": mid["piano"] + mid["bells"]}
    ctx = placed(["drums", "bass", "backing_vocals"])
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for k, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            p = os.path.join(PAGE, f"{k}{tag}.mp3")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SRP), "-ac", "1", "-i", "-", "-b:a", "128k", p],
                           input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / SRP, "ctx": "-ctx",
            "title": "Знаешь ли ты — клавиши: запись против MIDI",
            "sub": "Вся песня. Варианты «MIDI» сыграны простым синтом: здесь проверяются <b>ноты и ритм</b>, не звук — звук "
                   "подбираю на ZENOLOGY отдельно. Каждая группа MIDI выровнена по громкости своего стема. Переключение сохраняет место.",
            "tracks": [["1", "orig.mp3", "Оригинал: все клавиши", "стемы piano + keys + other + strings", True],
                       ["2", "orig-piano.mp3", "Оригинал: piano", "стем piano", True],
                       ["3", "orig-keys.mp3", "Оригинал: keys + other", "арпеджио, корни, лид 44–59", True],
                       ["4", "orig-strings.mp3", "Оригинал: strings", "стем strings", True],
                       ["5", "midi.mp3", "MIDI: всё", "пиано, арпеджио, корни, струнные, лид, тромбон, хиты (без колокольчиков)"],
                       ["6", "midi-piano.mp3", "MIDI: пиано", "дорожка 3"],
                       ["7", "midi-keys.mp3", "MIDI: арпеджио + корни", "дорожки 5 и 4"],
                       ["8", "midi-strings.mp3", "MIDI: струнные", "дорожка 6"],
                       ["9", "midi-lead.mp3", "MIDI: лид, тромбон, хиты", "дорожки 7, 9, 10 (такты 39–59)"],
                       ["0", "midi-bells.mp3", "MIDI: пиано + колокольчики", "дорожка 8: в записи их не слышно"]],
            "marks": [[1, "колокольчики MIDI: в записи нет"], [7, "арпеджио: в записи сверху ещё мелодия E5–D♯5–C♯5"],
                      [40, "тромбон MIDI: слышна половина нот"], [48, "лид в стеме other"], [60, "аутро: струнные в MIDI молчат"]],
            "html": HTML_NOTES}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


HTML_NOTES = """
<h2>Голоса MIDI</h2>
<div class="wrap"><table>
<tr><th>Голос</th><th>Дорожка</th><th>Такты</th><th>Что это в записи</th></tr>
<tr><td>пиано</td><td class="n">3</td><td class="n">1–6, 24–31, 39–59</td><td>стем piano; во вступлении все ноты совпали</td></tr>
<tr><td>арпеджио</td><td class="n">5</td><td class="n">7–63</td><td>keys + other (в MIDI — «джазовая гитара»)</td></tr>
<tr><td>корни</td><td class="n">4</td><td class="n">1–63</td><td>держанный низ в keys</td></tr>
<tr><td>струнные</td><td class="n">6</td><td class="n">1–5, 12–59</td><td>стем strings; аутро 60–63 в MIDI пустое</td></tr>
<tr><td>лид</td><td class="n">7</td><td class="n">44–59</td><td>громкая часть other в 48–55</td></tr>
<tr><td>тромбон</td><td class="n">9</td><td class="n">39–59</td><td>под вопросом: слышна около половины нот</td></tr>
<tr><td>хиты</td><td class="n">10</td><td class="n">43–46</td><td>аккорды на модуляции</td></tr>
<tr><td>колокольчики</td><td class="n">8</td><td class="n">1–23</td><td>в записи не найдено ни одной ноты</td></tr>
</table></div>
"""


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "import" and len(sys.argv) > 2:
        do_import(sys.argv[2])
    elif cmd == "metronome":
        do_metronome()
    elif cmd == "notes":
        cmd_notes(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "preview":
        cmd_preview()
    else:
        sys.exit(__doc__)
