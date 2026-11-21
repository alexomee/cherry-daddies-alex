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
import collections, importlib.util, json, re, time
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
          "bells":   (8, "keys", "колокольчики, такты 8, 10, 23 (во вступлении их в записи нет)"),
          "swell":   (None, "keys", "фраза октавами D# - E - D# - B, такты 3-4 (в MIDI нет; по стему keys)"),
          "strings_hi": (6, "strings", "струнные октавой выше верхней ноты, с такта 24 (верхи записи)"),
          "arp":     (5, "keys", "арпеджио с такта 7"),
          "low":     (4, "keys", "держанные корни аккордов"),
          "strings": (6, "strings", "струнные"),
          "lead":    (7, "lead", "мелодия 44–59: октава + квинта сверху (квинта по записи)"),
          "lead_fig": (7, "lead", "шестнадцатые G#5-C6-F5 той же дорожки (в записи нет, только для сравнения)"),
          "lead_acc": (6, "lead", "аккомпанемент в other 44–59: держанные аккорды = аккорды струнных MIDI"),
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


def write_part(p, about, stems, vs, layer=None):
    """One note a line (a plain json.dump with an indent makes thousands of lines of it); one take a line."""
    j = lambda x: json.dumps(x, ensure_ascii=False)
    body = "{\n" + f' "_about": {j(about)},\n "stems": {j(stems)},\n "voices": {{\n' + ",\n".join(
        f'  {j(vn)}: {{"at": [1], "bars": {END - 1}, "notes": [\n' + ",\n".join(f"   {j(n)}" for n in v["notes"]) + "\n  ]}"
        for vn, v in vs.items()) + "\n }"
    if layer:
        body += f',\n "layer": {{"file": {j(layer["file"])}, "takes": [\n' + ",\n".join(f"  {j(t)}" for t in layer["takes"]) + "\n ]}"
    with open(p, "w", encoding="utf-8") as f:
        f.write(body + "\n}\n")
    print(p)


def spans(notes):
    """Bar ranges [b0, b1) a voice plays in; rests of up to two bars stay inside one range (one take, not many)."""
    out = []
    for n in sorted(notes):
        b0 = int(n[0]); b1 = max(b0 + 1, int(np.ceil(n[0] + (n[1] - 1 + n[2]) / 4 - 1e-6)))
        if out and b0 <= out[-1][1] + 2:
            out[-1][1] = max(out[-1][1], b1)
        else:
            out.append([b0, b1])
    return out


def cmd_notes(src=None):
    os.makedirs(NOTES, exist_ok=True); os.makedirs(os.path.dirname(MID), exist_ok=True)
    if src:
        shutil.copyfile(src, MID)
    T = midi_tracks()
    Q = {vn: quantize(T[tr]) if tr is not None else [] for vn, (tr, _, _) in VOICES.items()}
    # Alex on the first layer: «в начале потеряли колокольчики типа как на 0:33 и 0:42» = bars 8.3 and 10.3: the bells
    # of the MIDI are in the record there (keys stem, B6 D#7 F#7 A#7), not in the intro 1-5 (0 % of their notes heard)
    Q["bells"] = [n for n in Q["bells"] if n[0] >= 6 * 4]
    # «0:13 в оригинале длинная протяжная нота» = bar 3: keys stem, octaves (roll by 16ths) D#5/6 3.1, E5/6 3.1.5 held to
    # 3.4, D#5/6 3.4, B4/5 4.1 ringing ~1.75 beats. Not in the MIDI.
    Q["swell"] = sorted((s0, d, p + o) for s0, d, p in ((8.0, 0.5, 75), (8.5, 2.5, 76), (11.0, 1.0, 75), (12.0, 1.75, 71)) for o in (0, 12))
    # «в припеве не хватает верхов смычковых»: the strings take against the strings stem by octave bands, bars 32-43:
    # +4 dB at 125-500 Hz, -7 / -11.5 / -11 dB at 2 / 4 / 8 kHz (44-55 alike; 12-18 within 3 dB). The record has a
    # voice over the MIDI chords (D#7 -10 dB at the top note D#5 0 in bar 37) -> the top note of each chord an octave up.
    top = collections.defaultdict(int)
    for s0, d, p in Q["strings_hi"]:
        if s0 >= 23 * 4:
            top[(s0, d)] = max(top[(s0, d)], p)
    Q["strings_hi"] = sorted((s0, d, p + 12) for (s0, d), p in top.items())
    # Alex 2026-11-21 on the lead: «две партии пытаешься подобрать одним тоном, там аккомпанемент и мелодия отдельно,
    # возможно в MIDI упростили». Measured in `other` 48-55 (note levels by half bar / eighth): the melody is the
    # loudest, in the rhythm of the MIDI's octave pairs (3+3+2), each pair with the FIFTH above the upper note
    # (C5 0 / C6 0 / G6 -7 dB, A#5 0 / A#6 -2 / F6 -3, D#5 -2 / D#6 0 / A#6 -1); the MIDI has no fifth. Under it, 6-10 dB
    # down, held chords Fm Db Eb Cm by half bars = the chords of the MIDI strings. The MIDI's single 16ths of the same
    # track (G#5 C6 G#5 F5 ...) are not in the record at all (G#5 -50..-58 dB): out of the playback.
    mel = [n for n in Q["lead"] if n[1] >= 0.25]
    dmax = collections.defaultdict(float)                 # one length an onset (the MIDI pairs C#5 0.25 + C#6 0.5)
    for s0, d, p in mel:
        dmax[s0] = max(dmax[s0], d)
    mel = sorted({(s0, dmax[s0], p) for s0, d, p in mel})
    # an octave pair whose other note the MIDI wrote as a zero-length double + a 16th (52.2.5 C6, 52.3 C#5): the pair
    # gets its other octave back, as long as its partner (else the fifth would go on the wrong note)
    on = collections.defaultdict(list)
    for s0, d, p in mel:
        on[(s0, d)].append(p)
    for (s0, d), ps in list(on.items()):
        if len(ps) == 1:
            mate = [p for s1, d1, p in Q["lead"] if s1 == s0 and abs(p - ps[0]) == 12]
            mel += [(s0, d, mate[0])] if mate else []
    top = collections.defaultdict(int)
    for s0, d, p in mel:
        top[(s0, d)] = max(top[(s0, d)], p)
    Q["lead"] = sorted(mel + [(s0, d, p + 7) for (s0, d), p in top.items()])
    Q["lead_fig"] = [n for n in Q["lead_fig"] if n[1] < 0.25]
    Q["lead_acc"] = [n for n in Q["lead_acc"] if n[0] >= 43 * 4]
    # piano: Alex chose «Magical Piano с педалью + реверб 2.5 с, -7 дБ» - the pedal = every note rings to the next bar line
    Q["piano"] = [(s0, max(d, (s0 // 4 + 1) * 4 - s0), p) for s0, d, p in Q["piano"]]
    V = {vn: {"at": [1], "bars": END - 1, "notes": as_notes(q)} for vn, q in Q.items()}
    V["bells"]["notes"] = BELLS_REC                       # the record's bells, not the MIDI's (see BELLS_REC)
    # Alex: «на 0:46 въезд сильно агрессивно звучит ... первое время он как будто там одной нотой» = bar 12, the strings
    # come in. The MIDI chord there is G#2 C#3 G#3 C#4 (an open fifth, low); the record's strings (note levels by quarter /
    # eighth bar) play C#3 0, C#4 -4..0, G#4 -7..-4, C#5 and F5 -12..-16 dB, no G#2 / G#3 (-65..-80), and swell in: C#3
    # rises 16 dB from 12.1 to 12.2.5. -> the record's chord, and STRINGS_IN (gain_curve) on the take that starts at 12.
    V["strings"]["notes"] = [n for n in V["strings"]["notes"] if n[0] != 12] + [[12, 1.0, 4.0, "C#3 C#4 G#4 C#5 F5"]]
    V["strings"]["notes"].sort(key=lambda n: (n[0], n[1]))
    about = ("«Знаешь ли ты», the keys of the playback as notes: the rusmidi MIDI (parts/znaesh-rusmidi.mid) one track "
             "per voice, quantized to 1/8 beat, mix.json bars, original key = band key (pitch_semitones 0). Alex "
             "2026-11-21 on the A/B page: «Да, берём MIDI». Generated by tools/jamzone/prep_znaesh_li_ty.py notes "
             "(edit there, not here).")
    for g, stems in GROUPS.items():
        write_part(os.path.join(NOTES, f"{g}.notes.json"), about + " Sweep file of one stem group.", stems,
                   {vn: v for vn, v in V.items() if VOICES[vn][1] == g})
    P = {vn: v for vn, v in V.items() if vn not in ("lead_fig", "lead")}
    for k, nm in enumerate(("lead_lo", "lead_mid", "lead_hi")):   # the melody stack as three single-note voices: Alex chose
        P[nm] = {"at": [1], "bars": END - 1, "notes": [[n[0], n[1], n[2], n[3].split()[k]] for n in V["lead"]["notes"]]}   # it so
    gains = json.load(open(GAINS, encoding="utf-8")) if os.path.exists(GAINS) else {}
    takes = []
    for vn, spec in LAYER.items():
        for sp in spans(P[vn]["notes"]):
            takes.append(dict({"voice": vn, "zen": spec["zen"], "bars": sp, "gain_db": round(gains.get(vn, 0.0) + EXTRA.get(vn, 0.0), 1)},
                              **{k: spec[k] for k in ("delay", "reverb") if spec.get(k)},
                              **({"gain_curve": STRINGS_IN} if vn == "strings" and sp[0] == 12 else {})))
    write_part(PART, about + " Not in it: the MIDI bells (track 8) and the single 16ths of track 7 - not heard in the "
               "record. Piano notes held to the bar line (pedal). The melody of the lead (`lead_lo` / `lead_mid` / `lead_hi`) "
               "= the MIDI octave pairs + the record's fifth on top, one voice a note. Layer: ZENOLOGY tones chosen by Alex "
               "(`low` = the arp's tone, my proposal; `horn` and `hits` wait for his word); gains from keys.gains.json "
               "(`calibrate`).", ["piano", "keys", "other", "strings"], P, {"file": "pb-keys", "takes": takes})
    print(f"  layer: {len(takes)} takes, {sum(b - a for t in takes for a, b in [t['bars']])} bars")
    for vn, v in V.items():
        bars = sorted({n[0] for n in v["notes"]})
        print(f"  {VOICES[vn][1]:8} {vn:8} {len(v['notes']):4} onsets  bars {bars[0]}-{bars[-1]}")


SRP = 44100
TIMBRE = {"piano": ("pluck", 5000, 0.7, 1.0), "bells": ("bell", 0, 0.6, 0.35), "arp": ("pluck", 3500, 0.35, 0.8),
          "low": ("organ", 900, None, 0.7), "strings": ("pad", 3000, None, 0.35), "lead": ("saw", 4500, 0.4, 0.5),
          "horn": ("saw", 1800, None, 0.5), "hits": ("saw", 3000, 0.25, 0.5), "lead_fig": ("saw", 4500, 0.2, 0.4),
          "lead_acc": ("pad", 2500, None, 0.3)}


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


# Alex 2026-11-21 on the ZENOLOGY page: piano «Magical Piano но не хватает FX», strings Hybrid Strings, arp OrganBell 2.
PICKS = {"piano": "PRST_L Essential 2/6", "strings": "PRST_F Essential/335", "arp": "PRST_D Basic Synth/539",
         "lead_acc": "ZEZ002 Dark Adaptations/20",          # Mode (Alex, lead_acc 44-47); piano: + pedal + reverb 2.5 s -7 dB
         "lead": "PRST_F Essential/383"}                    # Trumpet Echo, the stack as three takes (Alex, after «тон более
                                                            # wind/trumpet» -> the brass / wind sweep 52-55 + `leadwind`)
LAYER = {"piano": {"zen": PICKS["piano"], "reverb": {"rt60": 2.5, "db": -7}},
         "arp": {"zen": PICKS["arp"]}, "low": {"zen": PICKS["arp"]},      # low: the arp's tone - proposal, not Alex's pick
         "strings": {"zen": PICKS["strings"]}, "lead_acc": {"zen": PICKS["lead_acc"]},
         "strings_hi": {"zen": PICKS["strings"]}, "swell": {"zen": "PRST_D Basic Synth/490"}}
# bells: Alex chose «колокольчики из mp3, без фильтра» - bars 8 and 10 cut out of the minus mp3 (BELL_CUT, cut_bells(0)),
# added to the layer by build_layer; bar 23 has no bells now (the strings and backing vocals sound with them there)
# swell = Dreaming 5 (Alex). bells = Into the dreams, the first place of its sweep, only for the candidate: Alex - none of
# the sweep «толком не подходят, звучат сильно плоско тускло по сравнению с оригиналом» (scores 0.48-0.70: the arp is louder there)
# «на соло больше размазать ревербом/делеем»: the melody of the lead with a dotted-eighth echo and a longer room
SOLO_FX = {"delay": {"beats": 0.75, "db": -7, "fb": 0.35}, "reverb": {"rt60": 3.0, "db": -5}}
LAYER.update({v: dict({"zen": PICKS["lead"]}, **SOLO_FX) for v in ("lead_lo", "lead_mid", "lead_hi")})
STRINGS_IN = [[12, -16], [12.375, 0]]                     # the strings swell in at bar 12 like the record (16 dB in 1.5 beats)
EXTRA = {"piano": 3.0}                                      # dB over the stem level: Alex «пианино громче»
GAINS = os.path.join(SONG, "parts", "keys.gains.json")      # voice -> dB of its takes, written by `calibrate`
CAND = os.path.join(OUT, "pb-keys-candidate.wav")           # the layer to listen to before it goes to parts/


def cmd_pianofx():
    """Reverb variants of Magical Piano for «не хватает FX». Measured first (bars 1-6): between the arpeggio notes the
    record and the dry take die away alike (-6 / -7 dB before the next note), stereo alike (L/R corr 0.26 / 0.19);
    the difference is the TAIL - after the last chord of the intro the record holds -11 / -14 / -19 dB at 0.25 /
    0.5 / 0.75 s, the take drops to -21 / -36 / -34 (pedal + reverb). gm800_part.apply_reverb on the dry take
    (zenology/fx/magical-1-8.wav = zr render of bars 1-8), fitted on that tail and on the floor between notes;
    the best fit and a spread around it go to the page as one more voice group (zen-pianofx-*.json). The same with the
    pedal down (analysis/.../notes/piano-pedal.notes.json: every note held to the next bar line, zenology/fx/
    magical-pedal-1-8.wav) - the long tail of the record may be the pedal rather than a room."""
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt, resample_poly
    gp = load_tool("gm800_part"); song = gp.gmm.Song("Знаешь ли ты"); part = json.load(open(PART, encoding="utf-8"))
    zen = os.path.join(OUT, "zenology"); SR = 48000
    dry = sf.read(os.path.join(zen, "fx", "magical-1-8.wav"), always_2d=True)[0]
    x, sr = sf.read(song.stem("piano"), always_2d=True); i0 = int(song.t_stem(1) * sr)
    stem = resample_poly(x[i0:i0 + int(8 * song.bar * sr)], SR, sr, axis=0)
    line = gp.voice_line(song, part, "piano", 1, 7); on = sorted({t for t, _, _ in line}); last = max(t + d for t, _, d in line)
    bp = butter(4, [250, 6000], "bandpass", fs=SR, output="sos")

    def env(y):
        m = sosfiltfilt(bp, y.mean(1)); w = int(0.005 * SR)
        return 10 * np.log10(np.convolve(m ** 2, np.ones(w) / w, "same") + 1e-12)

    def shape(y):          # floor just before each next note (dB to the note's peak), then the tail after the intro
        e = env(y); fl = [e[int(b * SR) - int(0.015 * SR)] - e[int(a * SR):int(a * SR) + int(0.06 * SR)].max()
                          for a, b in zip(on, on[1:]) if b - a >= 0.2]
        ref = e[int((last - 1) * SR):int(last * SR)].max()
        return np.array([np.median(fl)] + [e[int((last + k * 0.25) * SR)] - ref for k in (1, 2, 3)])

    pedal = sf.read(os.path.join(zen, "fx", "magical-pedal-1-8.wav"), always_2d=True)[0]   # notes held to the bar line
    want = shape(stem); res = []
    for src, y0 in (("dry", dry), ("pedal", pedal)):
        for rt in (1.2, 1.8, 2.5, 3.5, 4.5):
            for db in (-18, -14, -10, -7, -4, -1):
                s = shape(gp.apply_reverb(y0, SR, rt60=rt, db=db))
                res.append((float(np.sqrt(((s - want) ** 2).mean())), src, rt, db, s))
    res.sort(key=lambda r: r[0])
    print("record: floor between notes, tail at 0.25/0.5/0.75 s:", " ".join(f"{v:.1f}" for v in want))
    for nm, y0 in (("dry", dry), ("pedal", pedal)):
        print(f"{nm:5} :", " ".join(f"{v:.1f}" for v in shape(y0)), f" off by {np.sqrt(((shape(y0) - want) ** 2).mean()):.1f} dB")
    for d, src, rt, db, s in res[:8]:
        print(f"  {src:5} rt60 {rt:.1f} s  {db:+d} dB  off by {d:.1f} dB:", " ".join(f"{v:.1f}" for v in s))
    bd = next(r for r in res if r[1] == "dry"); bp_ = next(r for r in res if r[1] == "pedal")
    # the fit puts the pedal reverb at -18 dB (just audible): two wetter ones beside it, for «FX» to be heard
    pick = [("dry", None, None), ("pedal", None, None), ("pedal", bp_[2], bp_[3]), ("pedal", bp_[2], bp_[3] + 6),
            ("pedal", bp_[2], bp_[3] + 11), ("dry", bd[2], bd[3]), ("dry", 2.5, -7)]
    tag = "zen-pianofx-piano-1-5"; top = []; srcs = {"dry": dry, "pedal": pedal}
    for k, (src, rt, db) in enumerate(pick):
        y = srcs[src] if rt is None else gp.apply_reverb(srcs[src], SR, rt60=rt, db=db)
        fn = f"{tag}-{k:02d}.wav"; sf.write(os.path.join(zen, fn), y[:int((4 * song.bar + 1.0) * SR)].astype(np.float32), SR, subtype="PCM_16")
        nm = "Magical Piano" + (" с педалью" if src == "pedal" else "") + (" сухой" if rt is None else f" + реверб {rt:.1f} с, {db:+d} дБ")
        if (src, rt, db) in ((bd[1], bd[2], bd[3]), (bp_[1], bp_[2], bp_[3])):
            nm += " (ближе всего к записи)"
        top.append({"bank": "PRST_L Essential 2", "number": 6, "name": nm, "category": "Pop Piano", "score": 0.0, "oct": 0, "file": fn, "tone": True})
    json.dump({"voice": "piano + FX", "bars": [1, 5], "stems": ["piano"], "tried": len(res), "played": len(res), "top": top},
              open(os.path.join(zen, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(os.path.join(zen, tag + ".json"))


# Alex on the melody: «тон более wind/trumpet». The brass/wind sweep (52-55, all 321 tones) kept synth brass on top;
# the solo trumpets / winds sat at 26+ - a solo tone is often MONO and plays one note of the octave + fifth stack.
# Here each of them plays the stack as three single-note takes (gm800-parts rule for mono leads), summed.
WIND = ["PRST_E XV Collection/257", "PRST_L Essential 2/162", "PRST_F Essential/382", "PRST_F Essential/383",
        "PRST_B AX Collection/272", "PRST_E XV Collection/256", "PRST_F Essential/404", "PRST_B AX Collection/270",
        "PRST_E XV Collection/239", "PRST_B AX Collection/334", "PRST_E XV Collection/225"]


def cmd_leadwind():
    """(zr env: needs pedalboard) the WIND tones on the melody, stack split -> appended to zen-lead-lead-52-56.json."""
    import soundfile as sf
    zr = load_tool("zenology_render"); S = os.path.basename(SONG); B0, B1 = 52, 56
    src = json.load(open(os.path.join(NOTES, "lead.notes.json"), encoding="utf-8"))
    split = {f"lead_{k}": {"at": [1], "bars": END - 1, "notes": []} for k in ("lo", "mid", "hi")}
    for n in src["voices"]["lead"]["notes"]:
        for k, p in zip(("lo", "mid", "hi"), n[3].split()):
            split[f"lead_{k}"]["notes"].append([n[0], n[1], n[2], p])
    sp = os.path.join(NOTES, "lead-split.notes.json")
    write_part(sp, "the melody stack (octave + fifth) as three single-note voices, for mono tones", ["other"], split)
    zen = os.path.join(OUT, "zenology"); jf = os.path.join(zen, f"zen-lead-lead-{B0}-{B1}.json"); rk = json.load(open(jf, encoding="utf-8"))
    rk["top"] = [t for t in rk["top"] if not t.get("wind")]
    for tag in WIND:
        x = None
        for vn in split:
            y, gp, sg = zr.render(tag, S, sp, vn, B0, B1)
            x = y if x is None else x[:min(len(x), len(y))] + y[:min(len(x), len(y))]
        dur = (B1 - B0) * sg.bar + 1.0
        ref = sum(sg.read(f"{st}.wav", sg.t_stem(B0), sg.t_stem(B0) + dur) for st in rk["stems"]).mean(1)
        sc, _, _, o = gp.sweep_score(gp.cqt_db(ref), gp.cqt_db(x.mean(1)), sg.semi)
        _, row = zr.tone_state(tag); fn = f"zen-lead-lead-{B0}-{B1}-wind-{row['file'][:-2]}.wav"
        sf.write(os.path.join(zen, fn), x, zr.SR, subtype="PCM_16")
        rk["top"].append({"bank": row["bank"], "number": row["number"], "name": row["name"] + " (стопка тремя дублями)",
                          "category": row["category"], "score": round(sc, 3), "oct": o, "file": fn, "wind": True})
        print(f"  {row['name']:18} {row['category']:15} score {sc:.3f}")
    json.dump(rk, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(jf)


# Alex on the bells of the candidate: none of the sweep «толком не подходят, звучат сильно плоско тускло по сравнению с
# оригиналом». Measured (keys + other, bars 8.3-8.4.5, above 2.5 kHz): our take ~10 dB under the record (the gain was
# taken over 8-10 where the arp is bright too), and 16 dB less at 1-2 kHz - the record's bells have notes an octave
# below the MIDI's F#7 A#7 D#7 (B6, F#6). Attacks of the record by 16ths (CQT, hop 3 ms, rise >= 5 dB within 14 dB of
# the loudest; an attack read on .2.75 and again louder on .3 is one note on .3): dyads in a syncopated figure, not the
# MIDI's single 16ths.
BELLS_REC = [[8, 3.0, 0.5, "B6 F#7"], [8, 3.5, 0.25, "D#7 A#7"], [8, 3.75, 0.5, "B6 F#7"], [8, 4.25, 0.75, "D#7 A#7"],
             [10, 3.0, 0.25, "C#7 G#7"], [10, 3.25, 0.25, "D#7 A#7"], [10, 3.5, 0.25, "F#6 B6 F#7"],
             [10, 3.75, 0.25, "F#6 C#7 G#7"], [10, 4.0, 0.25, "D#7 A#7"], [10, 4.25, 0.75, "F#7"],
             [23, 2.5, 0.25, "A#5"], [23, 2.75, 0.5, "F6"], [23, 3.25, 0.25, "G#6"], [23, 3.5, 0.25, "A#6"],
             [23, 3.75, 0.25, "F6"], [23, 4.0, 1.0, "G#6"]]
BELL_WIN = [(8, 3.0, 9, 1.5), (10, 3.0, 11, 1.5), (23, 2.5, 24, 1.0)]   # where the bells sound: (bar, beat) to (bar, beat)
BELL_CATS = "Bell,Mallet,Synth Bellpad,Synth PolyKey,Synth Pluck,E.Piano1,E.Piano2"


def cmd_bells(top=12):
    """(zr env) Bell tones ranked on the bells only: the record (keys + other) and each take high-passed at 900 Hz and
    cut to BELL_WIN, then the usual CQT score; every tone of BELL_CATS played (dirty, the sweep way), the best `top`
    again clean. Page clips = bars 8-10 of the take + our arp and low takes, the bells levelled to the record in the
    windows above 900 Hz -> zenology/zen-keys-bells2-8-11.json (zr page)."""
    import types, zlib, soundfile as sf
    from mido import Message
    from scipy.signal import butter, sosfiltfilt
    zr = load_tool("zenology_render"); S = os.path.basename(SONG); gp, sg = zr.gp_song(S); SR = zr.SR
    notes = os.path.join(NOTES, "keys.notes.json"); part = json.load(open(notes, encoding="utf-8"))
    segs = [(8, 11), (23, 24)]
    hp = lambda y: sosfiltfilt(butter(4, 900, "highpass", fs=SR, output="sos"), y)

    def cut(sig, b0, b1):                              # the bell windows of the segment [b0, b1)
        out = []
        for wb0, wt0, wb1, wt1 in BELL_WIN:
            if b0 <= wb0 < b1:
                a = (wb0 - b0 + (wt0 - 1) / 4) * sg.bar; b = (wb1 - b0 + (wt1 - 1) / 4) * sg.bar
                if int(b * SR) <= len(sig):
                    out.append(sig[int(a * SR):int(b * SR)])
        return np.concatenate(out)

    def events(b0, b1):
        ev = []
        for t, n, d in gp.voice_line(sg, part, "bells", b0, b1):
            ev += [Message("note_on", note=n, velocity=100, time=t), Message("note_off", note=n, time=t + d)]
        return sorted(ev, key=lambda m: (m.time, m.type == "note_on"))

    EV = {sgm: events(*sgm) for sgm in segs}; DUR = {sgm: (sgm[1] - sgm[0]) * sg.bar + 1.0 for sgm in segs}
    ref = np.concatenate([cut(hp(sum(sg.read(f"{st}.wav", sg.t_stem(b0), sg.t_stem(b0) + DUR[(b0, b1)]) for st in ("keys", "other")).mean(1)), b0, b1)
                          for b0, b1 in segs])
    R = gp.cqt_db(ref)
    rows = zr.select(types.SimpleNamespace(cat=BELL_CATS, name="", bank="", where="")); p = zr.plugin(); res = []; t0 = time.time()
    for i, r in enumerate(rows, 1):
        p.raw_state = zlib.decompress(open(os.path.join(zr.CACHE, r["file"]), "rb").read()); p([], duration=1.5, sample_rate=SR, reset=False)
        x = np.concatenate([cut(hp(p(EV[sgm], duration=DUR[sgm], sample_rate=SR, reset=False).T.mean(1)), *sgm) for sgm in segs])
        if np.sqrt((x ** 2).mean()) < 1e-5:
            continue
        sc, sp, tf, o = gp.sweep_score(R, gp.cqt_db(x), 0); res.append((sc, r))
        if i % 100 == 0:
            print(f"  {i}/{len(rows)}  {(time.time() - t0) / i:.2f} s a tone", flush=True)
    res.sort(key=lambda v: -v[0]); zen = os.path.join(OUT, "zenology"); tag = "zen-keys-bells2-8-11"
    G = json.load(open(GAINS, encoding="utf-8"))
    ctx = sum(_voice_sig(gp, sg, json.load(open(PART, encoding="utf-8")), [v], 8, 11) * 10 ** (G[v] / 20) for v in ("arp", "low"))
    rb = np.concatenate([cut(hp(sum(sg.read(f"{st}.wav", sg.t_stem(8), sg.t_stem(8) + DUR[(8, 11)]) for st in ("keys", "other")).mean(1)), 8, 11)])
    out = []
    for k, (sc0, r) in enumerate(res[:top]):
        tagn = f"{r['bank']}/{r['number']}"
        x, _, _ = zr.render(tagn, S, notes, "bells", 8, 11)
        xb = cut(hp(x.mean(1)), 8, 11); g = np.sqrt((rb ** 2).mean() / ((xb ** 2).mean() + 1e-20))
        n = len(ctx); y = x[:n].mean(1) * g if len(x) >= n else np.pad(x.mean(1), (0, n - len(x))) * g
        clip = np.stack([y + ctx, y + ctx], 1); fn = f"{tag}-{r['file'][:-2]}.wav"; sf.write(os.path.join(zen, fn), clip.astype(np.float32), SR, subtype="PCM_16")
        sc = gp.sweep_score(gp.cqt_db(rb), gp.cqt_db(xb), 0)[0]       # clean take, bars 8-10 windows
        out.append({"bank": r["bank"], "number": r["number"], "name": r["name"] + f" (+арпеджио, {20 * np.log10(g):+.0f} дБ)",
                    "category": r["category"], "score": round(sc, 3), "oct": 0, "file": fn, "gain_db": round(20 * np.log10(g), 1)})
        print(f"  {k + 1:2}. {r['bank']}/{r['number']:>4} {r['name']:18} {r['category']:15} sweep {sc0:.3f}  clean {sc:.3f}  gain {20 * np.log10(g):+.1f} dB", flush=True)
    json.dump({"voice": "bells (ноты по записи; только колокольчики сравниваются выше 900 Гц)", "bars": [8, 11], "stems": ["keys", "other"],
               "tried": len(rows), "played": len(res), "top": out,
               "all": [{"tone": f"{r['bank']}/{r['number']}", "name": r["name"], "score": round(sc, 3)} for sc, r in res]},
              open(os.path.join(zen, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(os.path.join(zen, tag + ".json"))


# Alex after the bell sweeps: «не получается похоже; может взять этот кусок прямо из фул mp3 ... там вроде ничего больше не
# играет в этом куске только колокольчики? проверь». The minus mp3 = the sum of the Moises stems (lag 0, the rest -30 dB).
# In 8.3-9.1 and 10.3-11.1 only piano / keys / other sound (strings, bass, drums, backing vocals silent); the arp holds a
# note there, and above 1.2 kHz the bells are 11-14 dB over the arp alone just before; under 1.2 kHz the tail of the held
# arp note and the piano (-47 / -51 dB). In bar 23 the strings and the backing vocals sound with the bells (-30 / -35 dB
# above 1.2 kHz): not clean, not cut.
MINUS = os.path.join(OUT, "bells-mp3", "minus.wav")      # the mp3 Alex gave (Downloads), decoded; same timeline as the stems
BELL_CUT = [(8, 2.875, 9, 2.0), (10, 2.875, 11, 2.0)]    # from just before the first bell to where its ring is under the arp
BELL_CUT_FILE = os.path.join(OUT, "bells-mp3", "bells-cut.wav")   # stem frame, whole song length


def cut_bells(hp_hz=1200, fade_out=0.45):
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt
    gp = load_tool("gm800_part"); song = gp.gmm.Song("Знаешь ли ты")
    x, sr = sf.read(MINUS, always_2d=True); out = np.zeros_like(x)
    if hp_hz:
        x = sosfiltfilt(butter(2, hp_hz, "highpass", fs=sr, output="sos"), x, axis=0)
    for b0, t0, b1, t1 in BELL_CUT:
        a, b = int(song.t_stem(b0 + (t0 - 1) / 4) * sr), int(song.t_stem(b1 + (t1 - 1) / 4) * sr)
        g = np.ones(b - a); fi, fo = int(0.02 * sr), int(fade_out * sr)
        g[:fi] = np.linspace(0, 1, fi); g[-fo:] = np.linspace(1, 0, fo) ** 2
        out[a:b] += x[a:b] * g[:, None]
    return out, sr, song, gp


def cmd_bellcut():
    """The bells of bars 8 and 10 cut out of the minus mp3 (high-pass 1.2 kHz, and without it), next to our arp + low:
    a page group to compare with the original and with the best plugin tone (Sunrise)."""
    import soundfile as sf
    from scipy.signal import resample_poly
    zen = os.path.join(OUT, "zenology"); tag = "zen-mp3-bells-8-11"; G = json.load(open(GAINS, encoding="utf-8"))
    part = json.load(open(PART, encoding="utf-8")); top = []
    for name, hp in (("колокольчики из mp3, выше 1.2 кГц", 1200), ("колокольчики из mp3, без фильтра", 0), ("колокольчики из mp3, выше 2 кГц", 2000)):
        cut, sr, song, gp = cut_bells(hp)
        if hp == 0:                                   # Alex's pick
            sf.write(BELL_CUT_FILE, cut.astype(np.float32), sr, subtype="FLOAT")
        a = int(song.t_stem(8) * sr); seg = resample_poly(cut[a:a + int((3 * song.bar + 1.0) * sr)].mean(1), gp.SR, sr)
        ctx = sum(_voice_sig(gp, song, part, [v], 8, 11) * 10 ** (G[v] / 20) for v in ("arp", "low"))
        n = len(ctx); y = np.pad(seg, (0, max(0, n - len(seg))))[:n] + ctx
        fn = f"{tag}-hp{hp}.wav"; sf.write(os.path.join(zen, fn), np.stack([y, y], 1).astype(np.float32), gp.SR, subtype="PCM_16")
        top.append({"bank": "mp3", "number": hp, "name": name + " + наше арпеджио", "category": "вырезано из записи", "score": 0.0, "oct": 0, "file": fn})
    jf = next(f for f in (os.path.join(zen, "zen-keys-bells2-8-11.json"), os.path.join(zen, "chosen", "zen-keys-bells2-8-11.json")) if os.path.exists(f))
    sun = json.load(open(jf, encoding="utf-8"))["top"][0]
    top.append(dict(sun, name="для сравнения: " + sun["name"]))
    json.dump({"voice": "колокольчики: вырезать из минуса", "bars": [8, 11], "stems": ["piano", "keys", "other"], "tried": 0, "played": 0, "top": top},
              open(os.path.join(zen, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(BELL_CUT_FILE, os.path.join(zen, tag + ".json"))


# The roots (`low`, MIDI track 4: one low note a bar or half bar, C#3 / A2 / B2) were on the arp's tone, OrganBell 2, my
# proposal. Below 180 Hz (bars 7-11, only keys there) the record holds them at -32..-35 dB through the bar; OrganBell 2
# falls from -33 to -61 dB in 1.5 beats. Alex: «давай послушаем, подбери, с ним без него фрагменты».
LOW_CATS = "Synth Pad/Str,E.Organ,Synth Bellpad,Ensemble Strings,E.Piano1,E.Piano2,Synth PolyKey,Ac.Piano,Pop Piano,Synth Bass,Vox/Choir"
LOW_FRAGS = [(7, 12), (19, 24)]        # the verse (no strings, no bass) and the modulation before the drums (no bass)


def cmd_lowpick(top=8):
    """(zr env) Sustaining tones (traits: sustain_db > -8, attack_ms < 120) for the roots, ranked by how their level
    below 180 Hz follows the record's over bars 7-11 (half-beat envelope, dB, after one offset); the best `top` clean,
    as fragments: original / our layer now (OrganBell 2) / without the roots / with each candidate, arp + roots only,
    the roots levelled to the record below 180 Hz -> zenology/zen-keys-low-<frag>.json (zr page)."""
    import types, zlib, soundfile as sf
    from mido import Message
    from scipy.signal import butter, sosfiltfilt
    zr = load_tool("zenology_render"); S = os.path.basename(SONG); gp, sg = zr.gp_song(S); SR = zr.SR
    part = json.load(open(PART, encoding="utf-8")); G = json.load(open(GAINS, encoding="utf-8"))
    lp = lambda y: sosfiltfilt(butter(4, 180, "lowpass", fs=SR, output="sos"), y)
    h = int(sg.bar / 8 * SR)
    envd = lambda y: np.array([10 * np.log10((y[i:i + h] ** 2).mean() + 1e-12) for i in range(0, len(y) - h + 1, h)])
    b0, b1 = LOW_FRAGS[0]; want = envd(lp(_stem_sig(sg, ["keys", "other"], b0, b1)))
    ev = []
    for t, n, d in gp.voice_line(sg, part, "low", b0, b1):
        ev += [Message("note_on", note=n, velocity=100, time=t), Message("note_off", note=n, time=t + d)]
    ev.sort(key=lambda m: (m.time, m.type == "note_on")); dur = (b1 - b0) * sg.bar
    rows = zr.select(types.SimpleNamespace(cat=LOW_CATS, name="", bank="", where="sustain_db>-8,attack_ms<120"))
    p = zr.plugin(); res = []; t0 = time.time()
    for i, r in enumerate(rows, 1):
        p.raw_state = zlib.decompress(open(os.path.join(zr.CACHE, r["file"]), "rb").read()); p([], duration=1.5, sample_rate=SR, reset=False)
        x = p(ev, duration=dur, sample_rate=SR, reset=False).T.mean(1)
        e = envd(lp(x))[:len(want)]
        if e.max() < -70:
            continue
        off = np.median(want[:len(e)] - e); res.append((float(np.mean(np.abs(want[:len(e)] - e - off))), r))
        if i % 100 == 0:
            print(f"  {i}/{len(rows)}  {(time.time() - t0) / i:.2f} s a tone", flush=True)
    res.sort(key=lambda v: v[0]); zen = os.path.join(OUT, "zenology")
    cur = ("PRST_D Basic Synth/539", "OrganBell 2 (сейчас в плейбеке)")
    picks = [(f"{r['bank']}/{r['number']}", r["name"], d) for d, r in res[:top]]
    print("best by the low envelope (mean |dB| off the record, half beats):")
    for tag, nm, d in picks:
        print(f"  {tag:32} {nm:18} {d:.1f} dB")
    for fb0, fb1 in LOW_FRAGS:
        arp = _voice_sig(gp, sg, part, ["arp"], fb0, fb1) * 10 ** (G["arp"] / 20)
        swell = _voice_sig(gp, sg, part, ["swell"], fb0, fb1) * 10 ** (G.get("swell", 0) / 20)
        ref = lp(_stem_sig(sg, ["keys", "other"], fb0, fb1)); n = len(arp); out = []; tagj = f"zen-keys-low-{fb0}-{fb1}"
        clips = [("none", "без корней", "только наше арпеджио", None)]
        for tag, nm, d in [(cur[0], cur[1], None)] + picks:
            clips.append((re.sub(r"[^A-Za-z0-9]+", "_", tag), nm, (f"{tag} · огибающая низа ±{d:.1f} дБ к записи" if d is not None else tag), tag))
        for cid, nm, note, tag in clips:
            if tag:
                x, _, _ = zr.render(tag, S, PART, "low", fb0, fb1); x = x.mean(1)[:n]; x = np.pad(x, (0, n - len(x)))
                g = np.sqrt((ref[:n] ** 2).mean() / ((lp(x) ** 2).mean() + 1e-20)); y = arp + swell + x * g; note += f" · {20 * np.log10(g):+.0f} дБ"
            else:
                y = arp + swell
            fn = f"{tagj}-{cid}.wav"; sf.write(os.path.join(zen, fn), np.stack([y, y], 1).astype(np.float32), SR, subtype="PCM_16")
            out.append({"bank": "", "number": "", "name": nm, "category": note, "score": 0.0, "oct": 0, "file": fn})
        json.dump({"voice": f"корни (низ под арпеджио), такты {fb0}–{fb1 - 1}: оригинал / без корней / сейчас / варианты", "bars": [fb0, fb1],
                   "stems": ["keys", "other"], "tried": len(rows), "played": len(res), "top": out},
                  open(os.path.join(zen, tagj + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(os.path.join(zen, tagj + ".json"))


# where each voice group is measured against its stems: (voices, stems, bars [b0, b1)); one gain for the voices of a row
CAL = [(["piano"], ["piano"], 1, 7),                       # intro: the piano stem is the piano alone
       (["strings"], ["strings"], 12, 19),
       (["arp", "low"], ["keys", "other"], 7, 12),         # before the strings come in
       (["lead_acc"], ["other"], 44, 48)]                  # the accompaniment alone in `other`
SECTIONS = [(1, 7, "вступление"), (7, 12, "куплет 1"), (12, 19, "куплет 1, струнные"), (19, 24, "модуляция, до барабанов"),
            (24, 44, "барабаны, Ebm"), (44, 48, "Fm, аккомпанемент"), (48, 56, "Fm, мелодия"), (56, 60, "Fm, конец"), (60, 64, "аутро")]


def _voice_sig(gp, song, part, voices, b0, b1):
    """Mono sum of the takes of these voices over bars [b0, b1), as the layer will have them (gains / reverb of the take)."""
    SR = gp.SR; n = int((b1 - b0) * song.bar * SR); y = np.zeros(n)
    for tk in part["layer"]["takes"]:
        if tk["voice"] not in voices or tk["bars"][1] <= b0 or tk["bars"][0] >= b1:
            continue
        x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).astype(np.float64)
        if tk.get("reverb"):
            x = gp.apply_reverb(x, SR, **tk["reverb"])
        a = int(round((b0 - tk["bars"][0]) * song.bar * SR)); i0, j0 = max(a, 0), max(-a, 0)
        m = min(len(x) - i0, n - j0)
        if m > 0:
            y[j0:j0 + m] += x[i0:i0 + m].mean(1)
    return y


def _stem_sig(song, stems, b0, b1, sr_out=48000):
    import soundfile as sf
    from scipy.signal import resample_poly
    y = 0
    for st in stems:
        info = sf.info(song.stem(st)); sr = info.samplerate
        x = sf.read(song.stem(st), start=int(song.t_stem(b0) * sr), stop=int(song.t_stem(b1) * sr), always_2d=True)[0].mean(1)
        y = y + (resample_poly(x, sr_out, sr) if sr != sr_out else x)
    return y


def cmd_calibrate():
    """Voice gains so that each voice group sits at the level of the stems it replaces, where it is alone (CAL); the
    melody of the lead = what `other` has in 48-55 over the accompaniment (powers add) -> parts/keys.gains.json."""
    gp = load_tool("gm800_part"); song = gp.gmm.Song("Знаешь ли ты"); part = json.load(open(PART, encoding="utf-8"))
    ms = lambda y: float(np.mean(y ** 2)) + 1e-20; G = {}
    for voices, stems, b0, b1 in CAL:
        g = 10 * np.log10(ms(_stem_sig(song, stems, b0, b1)) / ms(_voice_sig(gp, song, part, voices, b0, b1)))
        G.update({v: round(g, 1) for v in voices}); print(f"  {'+'.join(voices):12} vs {'+'.join(stems):13} bars {b0}-{b1 - 1}: {g:+.1f} dB")
    mel = ["lead_lo", "lead_mid", "lead_hi"]
    rest = ms(_stem_sig(song, ["other"], 48, 56)) - ms(_voice_sig(gp, song, part, ["lead_acc"], 48, 56)) * 10 ** (G["lead_acc"] / 10)
    g = 10 * np.log10(max(rest, 1e-20) / ms(_voice_sig(gp, song, part, mel, 48, 56)))
    G.update({v: round(g, 1) for v in mel}); print(f"  melody       vs other - accomp. bars 48-55: {g:+.1f} dB")
    from scipy.signal import butter, sosfiltfilt
    bp = lambda y, band: sosfiltfilt(butter(4, band, "bandpass", fs=gp.SR, output="sos"), y)
    # voices added over others: their band of the stem minus what the voices already levelled give there (powers add)
    RES = [(["strings_hi"], ["strings"], 32, 44, (2000, 8000), ["strings"]),
           (["swell"], ["keys", "other"], 3, 5, (500, 3000), ["low"])]
    for voices, stems, b0, b1, band, under in RES:
        u = sum(_voice_sig(gp, song, part, [v], b0, b1) * 10 ** (G[v] / 20) for v in under)
        st, me = ms(bp(_stem_sig(song, stems, b0, b1), band)), ms(bp(_voice_sig(gp, song, part, voices, b0, b1), band))
        rest = st - ms(bp(u, band))
        g = 10 * np.log10(rest / me) if rest > 0.1 * st else 10 * np.log10(0.1 * st / me)
        G.update({v: round(g, 1) for v in voices})
        print(f"  {'+'.join(voices):12} vs {'+'.join(stems):13} bars {b0}-{b1 - 1}, {band[0]}-{band[1]} Hz over "
              f"{'+'.join(under)} ({10 * np.log10(ms(bp(u, band)) / st):+.1f} dB of the stem there): {g:+.1f} dB")
    json.dump(G, open(GAINS, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(GAINS)


def build_layer(gp, song, dst):
    """The plugin takes (gm800_part layer) + the bells cut out of the minus mp3, both in the stem frame."""
    import soundfile as sf
    gp.cmd_layer(song, PART, dst)
    lay, sr = sf.read(dst, always_2d=True); bells, bsr = sf.read(BELL_CUT_FILE, always_2d=True)
    assert bsr == sr; n = min(len(lay), len(bells)); lay[:n] += bells[:n]
    sf.write(dst, lay.astype(np.float32), sr, subtype="FLOAT")
    print(f"  + bells cut from the minus mp3 -> {dst}  peak {20 * np.log10(np.abs(lay).max() + 1e-9):.1f} dBFS")


def cmd_result():
    """The layer candidate (gm800_part layer --out) against the stems it replaces: levels by section, and a whole-song
    page (original keys / layer, with or without drums, bass and backing vocals)."""
    import soundfile as sf
    gp = load_tool("gm800_part"); song = gp.gmm.Song("Знаешь ли ты"); part = json.load(open(PART, encoding="utf-8"))
    build_layer(gp, song, CAND)
    lay, sr = sf.read(CAND, always_2d=True); lay = lay.mean(1)
    orig = sum(sf.read(song.stem(st), always_2d=True)[0].mean(1) for st in part["stems"])
    db = lambda y: 10 * np.log10(float(np.mean(y ** 2)) + 1e-20)
    print("level by section, dB (layer against the stems it replaces: piano + keys + other + strings)")
    for b0, b1, nm in SECTIONS:
        a, b = int(song.t_stem(b0) * sr), int(song.t_stem(b1) * sr)
        print(f"  {b0:2}-{b1 - 1:2} {nm:26} stems {db(orig[a:b]):6.1f}   layer {db(lay[a:b]):6.1f}   {db(lay[a:b]) - db(orig[a:b]):+5.1f}")
    out = os.path.join(OUT, "result"); os.makedirs(out, exist_ok=True); v = time.strftime("%H%M%S")
    for f in os.listdir(out):
        if f.endswith(".mp3"):
            os.remove(os.path.join(out, f))
    n = int(round(song.t_render(END) * sr)) + 2 * sr; a = int(round(song.off * sr))
    def place(y):                                   # stem frame -> render timeline (stems start at the render offset)
        z = np.zeros(n); k = min(len(y), n - a); z[a:a + k] = y[:k]; return z
    ctx = place(sum(sf.read(song.stem(st), always_2d=True)[0].mean(1) for st in ("drums", "bass", "backing_vocals")))
    src = {"orig": place(orig), "layer": place(lay)}
    peak = max(np.abs(x + ctx).max() for x in src.values())
    for k, x in src.items():
        for tag, y in (("", x), ("-ctx", x + ctx)):
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-b:a", "160k",
                            os.path.join(out, f"{k}-{v}{tag}.mp3")], input=(y / peak * 0.9).astype(np.float32).tobytes(), check=True)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / sr, "ctx": "-ctx",
            "title": "Знаешь ли ты — слой клавиш ZENOLOGY",
            "sub": "Кандидат слоя <b>pb-keys</b> против стемов, которые он заменит (piano + keys + other + strings). Тоны — твой "
                   "выбор; колокольчики 8 и 10 — вырезаны из минуса; корни — тоном арпеджио (OrganBell 2, моё предложение); тромбона и хитов нет. Громкость голосов — по "
                   "стемам там, где голос один. В плейбек не поставлен.",
            "tracks": [["1", f"orig-{v}.mp3", "Оригинал: клавиши", "Moises: piano + keys + other + strings", True],
                       ["2", f"layer-{v}.mp3", "Слой ZENOLOGY", "пиано Magical (педаль + реверб), арпеджио и корни OrganBell 2, "
                        "струнные Hybrid, мелодия Trumpet Echo, аккомпанемент Mode"]],
            "marks": [], "html": ""}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(out, "index.html"))


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
    elif cmd == "pianofx":
        cmd_pianofx()
    elif cmd == "leadwind":
        cmd_leadwind()
    elif cmd == "bells":
        cmd_bells()
    elif cmd == "bellcut":
        cmd_bellcut()
    elif cmd == "lowpick":
        cmd_lowpick()
    elif cmd == "calibrate":
        cmd_calibrate()
    elif cmd == "result":
        cmd_result()
    elif cmd == "layer":                  # Alex 2026-11-21 «Да, ставь»: the layer of the playback, parts/pb-keys.wav
        _gp = load_tool("gm800_part"); build_layer(_gp, _gp.gmm.Song("Знаешь ли ты"), os.path.join(SONG, "parts", "pb-keys.wav"))
    else:
        sys.exit(__doc__)
