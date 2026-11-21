#!/usr/bin/env python3
"""«Солнышко»: the keys (Moises keys + other) written out as notes for the GM-800
(wiki/pipelines/part-transcription-guide.md; Alex 2026-11-20: «большая задача на снятие партии клавиш»,
notes = the MIDI from the web, sound type = Roma's concert take, original stems = reference, the places
with the cue «alex in» are played live and stay out of the playback).

  P="uv run -q --python 3.12 --with numpy --with scipy --with soundfile --with mido python"
  $P tools/jamzone/prep_solnyshko.py notes     # MIDI + stem corrections -> parts/synths.notes.json
                                               #   (+ the MIDI as it is -> analysis/.../synths-midi.notes.json)
  $P tools/jamzone/prep_solnyshko.py plan      # voices, bars, tone candidates, the sweep commands for the GM-800
  $P tools/jamzone/prep_solnyshko.py preview   # A/B page: original / my notes / MIDI as it is / Roma (no GM-800)
  (the sweeps printed by `plan`, on the GM-800)
  $P tools/jamzone/prep_solnyshko.py tones     # sound choice page: original / Roma / the best takes of each sweep
  gmp record "Solnyshko" "music/songs/Demo - Solnyshko/parts/synths.notes.json"   # the takes, on the GM-800 (16 min)
  $P ... check                                 # every take against its notes: silence, attacks, chroma
  $P ... calibrate                             # voice gains against keys + other -> parts/synths.gains.json
  $P ... notes                                 # again: the gains go into the takes
  gmp layer  "Solnyshko" "music/songs/Demo - Solnyshko/parts/synths.notes.json"   # -> parts/pb-synths.wav
  $P ... fx                                    # the reverse cymbal of `other` -> parts/pb-fx.wav
  (check / calibrate need --with librosa)

Source of the notes: parts/solnyshko-rusmidi.mid (rusmidi.com, C minor, 140 bpm, bar 1 = count-in). All notes
below are in the BAND key (pitch_semitones -2: record Cm, band Bbm), bars = mix.json bars.
MIDI bar -> our bar: + 3 from MIDI bar 6 on (the MIDI intro is 4 bars, ours 8); every section start then
lands on its cue (verse 25, arpegiator 49, more-arpegiator 57, soft-verse 73, ... chorus 129).

Voices (MIDI track -> what it is; checked against the stems with tools/part_notes.py --roll):
  riff     t7  the hook A# A# C# D# C# F, octave 3-4 (the fundamental in the keys stem), 1-25 and 105-128
  riff_hi  t3  the same an octave up (present in the stem, weaker)
  live     t8  off-beat two-note stabs 17-24 and 121-127 = cue «alex in»: Alex plays them, NOT in the layer
  vstab    t8  verse off-beat stab 33-40
  vfill    t10 verse fill, bars 34 36 38 40
  organ    t9  off-beat organ: choruses 41-56, 89-104, 129-144 and the riff part 113-127
  arp      t3  the «arpegiator» gallop 48-72, 96-104, 129-144; arp_lo = an octave below where nothing else
               covers it (48-56, 96-104)
  octs     t12 (= t8) octave-alternating 16ths 57-72, 129-144 («more-arpegiator»)
  stack    t10 octave stabs 57-72, 129-144
  sweep    t5  slow melody 65-72
  pad / strings / brass   t14 / t15 / t16  soft verse and verse 2, 73-88;  roll  t16  the stop bar 128

Where the record disagrees with the MIDI, the pitch follows the record (the MIDI version of these voices is
kept in synths-midi.notes.json for the A/B):
  intro    the record plays the first riff bar eight times with a filter opening (-42 -> -23 dB); the MIDI
           has four bars. Here: bar A x 8, a level ramp on the notes.
  organ    the record plays ONE note, the fifth of the chord (F4 over Bbm, C#4 over F#, D#4 over G#, C4 over F,
           A#3 over D#m; riff part F4 / D#4 / A#4 / G#4); the MIDI has the root. Here: MIDI + 7 semitones.
  vstab    the record has the root an octave below as the loudest note (A#3, F#3, F3) under the MIDI pair.
  vfill    the record plays C -> C# in octaves on 4 and 4& in each of 34 36 38 40; the MIDI has four
           different fills.
Not in the MIDI and not written: the part that enters at 137 («outro-solo», scene 9) - Alex live.
Not notes: the reverse cymbal in `other` (bars 8, 24, 120, 128) and the taiko of the MIDI (percussion: out).
"""
import collections, importlib.util, json, os, subprocess, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SONG = os.path.join(REPO, "music", "songs", "Demo - Solnyshko")
MID = os.path.join(SONG, "parts", "solnyshko-rusmidi.mid")
PART = os.path.join(SONG, "parts", "synths.notes.json")
OUT = os.path.join(REPO, "analysis", "gm800-match", "Demo - Solnyshko")
ALT = os.path.join(OUT, "synths-midi.notes.json")
PAGE = os.path.join(OUT, "preview-part")
NAMES = "C C# D D# E F F# G G# A A# B".split()
SEMI = -2
END = 146                                  # bar after the last one

name = lambda m: f"{NAMES[m % 12]}{m // 12 - 1}"
midi = lambda s: NAMES.index(s[:-1]) + 12 * (int(s[-1]) + 1)

# tone = Alex's picks by ear, 2026-11-20: riff 330 + a layer of 1024 Trance Saws (+3 dB against 330 with both at the
# same RMS - the pair closest to Roma's take), verse stab 317 with the echo of the record (an eighth later, -5 dB),
# organ 537 Mad Organ (second sweep: he asked for a pipe / overdriven sound), 316 arp and octs, 970 stack, 287 sweep
# and pad, 1011 strings, 249 brass. cand = the short list of the first sweep; solo = the bars of the sweep.
# All takes are sent as written ("shift": 0), the way the sweeps were heard: the octave probe misreads 537 (sub-octave
# drawbar) and 970 (a built-in fifth; it is also mono - of the octave pair of `stack` one note sounds, as in the sweep).
# 2026-11-21: the riff moved to a ZENOLOGY tone - Alex: «по солнышку берем Sunrise полусухой» (Sunrise without its bell
# partial, which does not follow the keys, and with a shorter release: at 658 the notes piled up into a chord). `zen`
# wins over tone / layers in the layer; tone and layers stay as the reference `calibrate` and `zen` level it against.
RIFF_ZEN = "PRST_A Factory Presets/32{p1.level=0,p*.release=450}"
CAND = os.path.join(OUT, "pb-synths-candidate.wav")      # `candidate`: the layer to listen to before it goes to parts/
VOICES = {
    "riff":    dict(zen=RIFF_ZEN, tone=330, layers=[(1024, 3.0)], role="lead",  solo=(105, 109), cand=[211, 210, 212, 217, 214, 208, 194, 239, 327, 330, 304],
                    what="рифф, октава 3–4"),
    "riff_hi": dict(tone=330, role="lead",  solo=(105, 109), cand=[], what="рифф октавой выше"),
    "vstab":   dict(tone=317, delay=dict(beats=0.5, db=-5, fb=0.25), role="stab",  solo=(33, 37),  cand=[316, 327, 330, 304, 1092, 317], what="офф-бит стаб куплета"),
    "vfill":   dict(tone=317, delay=dict(beats=0.5, db=-5, fb=0.25), role="stab",  solo=(33, 37),  cand=[], what="филл куплета C → C#"),
    "organ":   dict(tone=537, role="organ", solo=(41, 45),  cand=[527, 530, 27, 33, 34, 518, 522, 38], what="офф-бит орган (квинта)"),
    "arp":     dict(tone=316, role="pluck", solo=(49, 53),  cand=[350, 352, 354, 1087, 1089, 361, 365, 316], what="«арпеджиатор», галоп"),
    "arp_lo":  dict(tone=316, role="pluck", solo=(49, 53),  cand=[], what="галоп октавой ниже"),
    "octs":    dict(tone=316, role="pluck", solo=(57, 61),  cand=[316, 1024, 1092, 322, 199, 350], what="октавы шестнадцатыми"),
    "stack":   dict(tone=970, role="lead",  solo=(57, 61),  cand=[970, 360, 195, 190, 199], what="октавные акценты"),
    "sweep":   dict(tone=287, role="pad",   solo=(65, 73),  cand=[277, 278, 1055, 197, 287], what="медленная мелодия"),
    "pad":     dict(tone=287, role="pad",   solo=(73, 77),  cand=[287, 275, 264, 259, 266, 285], what="пэд тихого куплета"),
    "strings": dict(tone=1011, role="pad",   solo=(73, 77),  cand=[148, 145, 753, 1011, 259], what="струнные, октава"),
    "brass":   dict(tone=249, role="stab",  solo=(73, 77),  cand=[252, 247, 253, 257, 249, 242], what="триольные аккорды"),
    "roll":    dict(tone=249, role="stab",  solo=(128, 129), cand=[], what="дробь в стоп-такте 128"),
}
GAP = {"arp": 0.002, "arp_lo": 0.002, "octs": 0.002, "stack": 0.002, "roll": 0.002}   # staccato lengths are the MIDI's own
GAINS = os.path.join(SONG, "parts", "synths.gains.json")   # "voice@tone" -> dB of its takes: written by `calibrate`
GAIN = ({tuple([k.split("@")[0], int(k.split("@")[1]) if k.split("@")[1].isdigit() else k.split("@")[1]]): v for k, v in json.load(open(GAINS, encoding="utf-8")).items()}
        if os.path.exists(GAINS) else {})
FX_WIN = [(8, 2.5, 9, 1.0), (24, 2.3, 25, 1.0), (120, 2.3, 121, 1.0), (128, 2.3, 129, 1.0)]   # reverse cymbal in `other`
INTRO_DB = [-17, -12, -8, -6, -4, -1, 0, 0]       # keys stem, bars 1-8 against 9-16 (filter opening), on the notes


def tracks():
    import mido
    m = mido.MidiFile(MID); tpb = m.ticks_per_beat; out = {}
    for i, tr in enumerate(m.tracks):
        t = 0; on = collections.defaultdict(list); ns = []
        for msg in tr:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                on[msg.note].append(t)
            elif msg.type in ("note_off", "note_on") and on[msg.note]:
                s = on[msg.note].pop(0); ns.append((s / tpb, (t - s) / tpb, msg.note))
        out[i] = sorted(ns)
    return out


def cut(ns, mb0, mb1, ours, semi=SEMI):
    """Notes of MIDI bars [mb0, mb1) (1-based) -> [[our bar, beat, beats, "pitches"]], our bar of mb0 = ours."""
    grp = collections.OrderedDict()
    for s, d, p in ns:
        mb = int(s // 4) + 1
        if mb0 <= mb < mb1:
            grp.setdefault((ours + mb - mb0, round(s % 4 + 1, 3), round(d, 3)), set()).add(p + semi)
    return [[b, bt, d, " ".join(name(p) for p in sorted(ps))] for (b, bt, d), ps in grp.items()]


def rebar(notes, bar):
    return [[bar, *n[1:]] for n in notes]


def build(as_midi=False):
    T = tracks(); V = {}
    # riff: intro from the record (bar A x 8), then the MIDI
    for vn, tr in (("riff", 7), ("riff_hi", 3)):
        A = cut(T[tr], 6, 7, 1); A[-1][2] = 0.5              # the last F is tied over in bar 9+, not in the intro
        if as_midi:
            intro = cut(T[tr], 2, 6, 1) + cut(T[tr], 2, 6, 5)
        else:
            intro = [n + [{"gain_db": INTRO_DB[b - 1]}] if INTRO_DB[b - 1] else n for b in range(1, 9) for n in rebar(A, b)]
        V[vn] = intro + cut(T[tr], 6, 23, 9) + cut(T[tr], 102, 126, 105)
    V["live"] = cut(T[8], 14, 22, 17) + cut(T[8], 118, 125, 121)
    if as_midi:
        V["vstab"] = cut(T[8], 30, 38, 33)
        V["vfill"] = cut(T[10], 30, 38, 33)
    else:
        chord = {33: "A#3 F4 A#4", 34: "A#3 F4 A#4", 35: "A#3 F4 A#4", 36: "A#3 F4 A#4",
                 37: "F#3 C#4 F#4", 38: "F#3 C#4 F#4", 39: "F3 C4 F4", 40: "F3 C4 F4"}
        V["vstab"] = [[b, bt, 0.25, c] for b, c in chord.items() for bt in (1.5, 2.5, 3.5, 4.5)]
        V["vfill"] = [n for b in (34, 36, 38, 40) for n in ([b, 4.0, 0.5, "C4 C5"], [b, 4.5, 0.5, "C#4 C#5"])]
    fifth = SEMI if as_midi else SEMI + 7
    V["organ"] = (cut(T[9], 38, 54, 41, fifth) + cut(T[9], 86, 102, 89, fifth)
                  + cut(T[9], 110, 125, 113, fifth) + cut(T[9], 126, 142, 129, fifth))
    V["arp"] = cut(T[3], 45, 70, 48) + cut(T[3], 93, 102, 96) + cut(T[3], 126, 142, 129)
    if not as_midi:
        V["arp_lo"] = cut(T[3], 45, 54, 48, SEMI - 12) + cut(T[3], 93, 102, 96, SEMI - 12)
    V["octs"] = cut(T[12], 54, 70, 57) + cut(T[12], 126, 142, 129)
    V["stack"] = cut(T[10], 54, 70, 57) + cut(T[10], 126, 142, 129)
    V["sweep"] = cut(T[5], 62, 70, 65)
    V["pad"] = cut(T[14], 70, 86, 73)
    V["strings"] = cut(T[15], 70, 86, 73)
    V["brass"] = cut(T[16], 70, 86, 73)
    V["roll"] = cut(T[16], 125, 126, 128)
    return {vn: dict({"at": [1], "bars": END - 1, "notes": sorted(ns, key=lambda n: (n[0], n[1]))},
                     **({"gap": GAP[vn]} if vn in GAP else {}),
                     **({"gain_hold": True} if vn in ("riff", "riff_hi") else {})) for vn, ns in V.items()}   # intro: the tails too


def spans(notes):
    """Bar ranges [b0, b1) a voice plays in; a rest of up to two bars stays inside one range (a voice that
    plays every other bar is one take, not eight)."""
    out = []
    for n in notes:
        b0 = int(n[0]); b1 = int(np.ceil(n[0] + (n[1] - 1 + n[2]) / 4 - 1e-6))
        b1 = max(b1, b0 + 1)
        if out and b0 <= out[-1][1] + 2:
            out[-1][1] = max(out[-1][1], b1)
        else:
            out.append([b0, b1])
    return out


def dump(part, path):
    """One note / one take a line (plain json.dump with an indent makes 15 000 lines of it)."""
    j = lambda x: json.dumps(x, ensure_ascii=False)
    out = ["{", f' "_about": {j(part["_about"])},', f' "stems": {j(part["stems"])},', ' "voices": {']
    vs = list(part["voices"].items())
    for i, (vn, v) in enumerate(vs):
        head = ", ".join(f"{j(k)}: {j(x)}" for k, x in v.items() if k != "notes")
        out.append(f'  {j(vn)}: {{{head}, "notes": [')
        out += [f"   {j(n)}" + ("," if k < len(v["notes"]) - 1 else "") for k, n in enumerate(v["notes"])]
        out.append("  ]}" + ("," if i < len(vs) - 1 else ""))
    out.append(" }" + ("," if "layer" in part else ""))
    if "layer" in part:
        tk = part["layer"]["takes"]
        out.append(f' "layer": {{"file": {j(part["layer"]["file"])}, "takes": [')
        out += [f"  {j(t)}" + ("," if k < len(tk) - 1 else "") for k, t in enumerate(tk)]
        out.append(" ]}")
    out.append("}")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")


def cmd_notes():
    V = build()
    takes = []
    for vn, spec in VOICES.items():
        for sp in spans(V[vn]["notes"]):
            if spec.get("zen"):                              # played by the plugin (zenology_render.py record)
                takes.append({"voice": vn, "zen": spec["zen"], "bars": sp, "gain_db": round(GAIN.get((vn, "zen"), 0.0), 1)}); continue
            for tone, rel in [(spec["tone"], 0.0)] + spec.get("layers", []):
                tk = {"voice": vn, "tone": tone, "base": 33, "shift": 0, "bars": sp, "gain_db": round(GAIN.get((vn, tone), rel), 1)}
                if spec.get("delay"):
                    tk["delay"] = spec["delay"]
                takes.append(tk)
    part = {"_about": "Keys of «Солнышко» (Moises keys + other) written out for the GM-800; generated by "
                      "tools/jamzone/prep_solnyshko.py notes (edit there, not here). Notes: the MIDI from rusmidi "
                      "(parts/solnyshko-rusmidi.mid) with the record's pitches where they differ. Band key (Bbm), "
                      "mix.json bars. Voice `live` = cue «alex in», played by Alex, not in the layer. Tones chosen by "
                      "Alex by ear on the sweep takes (2026-11-20).",
            "stems": ["keys", "other"], "voices": V, "layer": {"file": "pb-synths", "takes": takes}}
    dump(part, PART)
    os.makedirs(OUT, exist_ok=True)
    dump({"_about": "The MIDI as it is (only the bar mapping and the key changed): A/B against "
                    "parts/synths.notes.json", "stems": ["keys", "other"], "voices": build(as_midi=True)}, ALT)
    print(PART)
    for vn, v in V.items():
        print(f"  {vn:8} {len(v['notes']):4} notes  bars " + " ".join(f"{a}-{b - 1}" for a, b in spans(v["notes"])))
    print(f"  layer: {len(takes)} takes, {sum(b - a for t in takes for a, b in [t['bars']])} bars to record")
    print(ALT)


def cmd_plan():
    part = json.load(open(PART, encoding="utf-8")); rows = {int(r.split("\t")[0]): r.split("\t")[1] for r in
                                                              open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    rel = os.path.relpath(PART, REPO)
    for vn, spec in VOICES.items():
        sp = " ".join(f"{a}-{b - 1}" for a, b in spans(part["voices"][vn]["notes"]))
        print(f"\n{vn}: {spec['what']}; такты {sp}; пока тон {spec['tone']} {rows[spec['tone']]}")
        if spec["cand"]:
            print("   кандидаты: " + ", ".join(f"{n} {rows[n]}" for n in spec["cand"]))
            print(f"   gmp sweep \"Solnyshko\" \"{rel}\" {vn} --bars {spec['solo'][0]} {spec['solo'][1]} "
                  f"--role {spec['role']} --tones {','.join(map(str, spec['cand']))}")


HTML = """
<h2>Голоса плейбека</h2>
<div class="wrap"><table>
<tr><th>Голос</th><th>Такты</th><th>Что играет</th><th>Откуда</th></tr>
<tr><td>riff + riff_hi</td><td class="n">1–25, 105–128</td><td>рифф A# A# C# D# C# F, две октавы</td><td>MIDI; вступление по записи</td></tr>
<tr><td>vstab</td><td class="n">33–40</td><td>офф-бит: A#3 F4 A#4 → F#3 C#4 F#4 → F3 C4 F4</td><td>MIDI + нижняя нота из записи</td></tr>
<tr><td>vfill</td><td class="n">34, 36, 38, 40</td><td>C → C# октавой на 4 и 4&amp;</td><td>запись (в MIDI четыре разных филла)</td></tr>
<tr><td>organ</td><td class="n">41–56, 89–104, 113–127, 129–144</td><td>офф-бит одной нотой: F4 C#4 D#4 C4 C#4 A#3 D#4 C4</td><td>ритм MIDI, высота по записи</td></tr>
<tr><td>arp + arp_lo</td><td class="n">48–72, 96–104, 129–144</td><td>галоп «арпеджиатор»</td><td>MIDI; нижняя октава по записи</td></tr>
<tr><td>octs, stack</td><td class="n">57–72, 129–144</td><td>октавы шестнадцатыми и октавные акценты</td><td>MIDI</td></tr>
<tr><td>sweep</td><td class="n">65–72</td><td>медленная мелодия октавой</td><td>MIDI</td></tr>
<tr><td>pad, strings, brass</td><td class="n">73–88</td><td>пэд, струнные, триольные аккорды через такт</td><td>MIDI</td></tr>
<tr><td>roll</td><td class="n">128</td><td>дробь на A#3 в стоп-такте</td><td>MIDI</td></tr>
<tr><td><b>live</b> (не в плейбеке)</td><td class="n">17–24, 121–127</td><td>офф-бит стабы F4+A#4 / G#4+C#5 / A#4+D#5</td><td>MIDI; играешь ты</td></tr>
</table></div>
<p class="q">В аутро с такта 137 в записи входит ещё одна партия, которой нет в MIDI. Она не выписана: по сценам GM-800
это твоя живая (сцена 9).</p>
"""


# ---- preview without the GM-800: plain synth, render timeline -------------------------------------------------
SR = 44100
TIMBRE = {"riff": ("square", 2600, None, 0.9), "riff_hi": ("square", 3200, None, 0.45), "live": ("saw", 3500, 0.25, 0.7),
          "vstab": ("saw", 3000, 0.18, 0.6), "vfill": ("saw", 3500, None, 0.6), "organ": ("organ", 0, 0.12, 0.8),
          "arp": ("saw", 4000, 0.12, 0.5), "arp_lo": ("saw", 3000, 0.12, 0.45), "octs": ("saw", 4500, 0.15, 0.45),
          "stack": ("saw", 2500, 0.2, 0.4), "sweep": ("pad", 3000, None, 0.5), "pad": ("pad", 1800, None, 0.35),
          "strings": ("pad", 4000, None, 0.3), "brass": ("saw", 2200, 0.2, 0.45), "roll": ("saw", 2200, 0.08, 0.4)}


def synth(kind, fc, dec, f, dur):
    from scipy.signal import butter, sosfilt
    n = int((dur + 0.08) * SR); t = np.arange(n) / SR; ph = (f * t) % 1
    if kind == "square":
        x = np.where(ph < 0.5, 1.0, -1.0)
    elif kind == "organ":
        x = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.35 * np.sin(6 * np.pi * f * t)
    elif kind == "pad":
        x = (2 * ph - 1) + (2 * ((f * 1.006 * t) % 1) - 1) + (2 * ((f * 0.994 * t) % 1) - 1)
    else:
        x = 2 * ph - 1
    if fc:
        x = sosfilt(butter(2, min(fc, 0.45 * SR), "lowpass", fs=SR, output="sos"), x)
    a = 0.12 if kind == "pad" else 0.004
    e = np.minimum(1, t / a)
    if dec:
        e = e * np.exp(-t / dec)
    r = int(0.06 * SR); e[-r:] *= np.linspace(1, 0, r)
    return x * e * 0.2


def roma_at(song, t_render):
    """Seconds inside parts/roma-keys-2810.wav of a time of TODAY's render: the layer is in the frame of the render
    it was cut for (its rec_off in mix.json), and the render offset has moved since (short intro, 2026-11-20)."""
    lay = next(l for l in song.mix["pb-other"]["layers"] if isinstance(l, dict) and l.get("file") == "roma-keys-2810")
    return t_render - song.off + lay.get("rec_off", song.off)


def render(song, gp, part, voices):
    n = int(round(song.t_render(END) * SR)) + 2 * SR; buf = np.zeros(n)
    for vn in voices:
        if vn not in part["voices"]:
            continue
        kind, fc, dec, g = TIMBRE[vn]
        gains = gp.voice_gains(song, part, vn, 1, END)
        for t, m, d in gp.voice_line(song, part, vn, 1, END):
            db = next((x for t0, dd, x in gains if abs(t0 - t) < 1e-6), 0)
            x = synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)) * g * 10 ** (db / 20)
            a = int((song.t_render(1) + t) * SR); k = min(len(x), n - a)
            buf[a:a + k] += x[:k]
    return buf


def cmd_preview():
    import soundfile as sf
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); song = gp.gmm.Song("Solnyshko"); os.makedirs(PAGE, exist_ok=True)
    n = sf.info(os.path.join(SONG, "auto-render", "all.wav")).frames
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")[0].mean(1)
    fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    rms = lambda x, a, b: np.sqrt((x[int(song.t_render(a) * SR):int(song.t_render(b) * SR)] ** 2).mean()) + 1e-9
    # original keys: raw stems pitched into the band key the way the render does it, placed at the render offset
    tmp = os.path.join(OUT, "tmp-orig"); orig = np.zeros(n)
    for st in ("keys", "other", "guitars"):
        subprocess.run(["rubberband", "-3", "-F", "-p", str(SEMI), song.stem(st), tmp + ".wav"], capture_output=True, check=True)
        x = rd(tmp + ".wav"); a = int(round(song.off * SR)); k = min(len(x), n - a); orig[a:a + k] += x[:k]
    os.remove(tmp + ".wav")
    mine, alt = json.load(open(PART, encoding="utf-8")), json.load(open(ALT, encoding="utf-8"))
    pb = [v for v in VOICES]
    src = {"orig": orig, "mine": fit(render(song, gp, mine, pb)), "midi": fit(render(song, gp, alt, pb)),
           "mine-live": fit(render(song, gp, mine, pb + ["live"])),
           "roma": fit(rd(os.path.join(SONG, "parts", "roma-keys-2810.wav"))[max(0, int(round(roma_at(song, 0) * SR))):])}
    ref = rms(orig, 9, 17)
    for k in ("mine", "midi", "mine-live"):                     # one gain for the three synth renders: same notes, same level
        src[k] = src[k] * ref / rms(src["mine"], 9, 17)
    src["roma"] *= ref / rms(src["roma"], 9, 17)
    ctx = sum(fit(rd(os.path.join(SONG, "auto-render", p))) for p in ("stems/drums.mp3", "stems/vocal.mp3", "pb-bass.mp3"))
    ctx *= 10 ** (3 / 20) * ref / rms(ctx, 9, 17) * 2.0
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for k, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            p = os.path.join(PAGE, f"{k}{tag}.mp3")
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "128k", p],
                           input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
            print(p)
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / SR, "ctx": "-ctx",
            "title": "Солнышко — клавиши нотами для GM-800",
            "sub": "Вся песня, тональность группы. Синтезаторные варианты сыграны простым синтом: здесь проверяются "
                   "<b>ноты и ритм</b>, не звук — звук подберём на GM-800. Переключение сохраняет место.",
            "tracks": [["1", "orig.mp3", "Оригинал", "стемы keys + other + guitars", True],
                       ["2", "mine.mp3", "Мои ноты", "MIDI + правки по записи; без твоих живых мест"],
                       ["3", "midi.mp3", "Как в MIDI", "MIDI без правок; без твоих живых мест"],
                       ["4", "mine-live.mp3", "Мои ноты + твоя партия", "с офф-бит стабами 17–24 и 121–127"],
                       ["5", "roma.mp3", "Рома, концерт 28.10", "сейчас в плейбеке; ориентир по типу звука", True]],
            "marks": [[1, "вступление: 8 тактов одного мотива"], [33, "стаб куплета: добавлен низ"],
                      [34, "филл: C → C#"], [41, "орган: квинта вместо тоники"], [48, "галоп: добавлена нижняя октава"],
                      [113, "орган в риффе: квинта"]],
            "html": HTML}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(PAGE, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(PAGE, "index.html"))


def cmd_tones(top=5):
    """After the sweeps: per voice the original bars, Roma's take and the best takes of the sweep, looped,
    same loudness -> analysis/.../preview-tones/index.html (Alex picks the sound by ear)."""
    import soundfile as sf
    from scipy.signal import resample_poly
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); song = gp.gmm.Song("Solnyshko"); dst = os.path.join(OUT, "preview-tones"); os.makedirs(dst, exist_ok=True)
    hist = json.load(open(gp.HISTORY, encoding="utf-8"))["tones"]
    names = {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0].strip() for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    rms = lambda x: np.sqrt((x ** 2).mean()) + 1e-9
    groups = []
    for vn, spec in VOICES.items():
        b0, b1 = spec["solo"]
        runs = sorted((r["rank"], int(num), r["score"], r["oct"]) for num, t in hist.items() for r in t["runs"]
                      if r["song"] == song.name and r["voices"] == vn and r["bars"] == [b0, b1])
        if not runs:
            continue
        n = int(round((b1 - b0) * song.bar * SR)); tmp = os.path.join(dst, "tmp")
        orig = np.zeros(n)
        for st in ("keys", "other"):                             # the bars of the raw stems, pitched into the band key
            info = sf.info(song.stem(st)); a = int(song.t_stem(b0) * info.samplerate)
            x, sr = sf.read(song.stem(st), start=a, stop=a + int((b1 - b0) * song.bar * info.samplerate) + sr_pad(info), always_2d=True)
            sf.write(tmp + "-in.wav", x, sr)
            subprocess.run(["rubberband", "-3", "-F", "-p", str(SEMI), tmp + "-in.wav", tmp + "-out.wav"], capture_output=True, check=True)
            y = sf.read(tmp + "-out.wav", always_2d=True)[0].mean(1); orig += np.pad(y, (0, max(0, n - len(y))))[:n]
        for f in ("-in.wav", "-out.wav"):
            os.remove(tmp + f)
        a = int(roma_at(song, song.t_render(b0)) * SR)
        roma = sf.read(os.path.join(SONG, "parts", "roma-keys-2810.wav"), start=a, stop=a + n, always_2d=True)[0].mean(1)
        clips = [("orig", orig, "Оригинал", "стемы keys + other", True), ("roma", roma * rms(orig) / rms(roma), "Рома, концерт", "ориентир по типу звука", True)]
        for rank, num, sc, o in runs[:top]:
            x = sf.read(os.path.join(song.out, f"sweep-synths-{vn}-{b0}-{b1}-t{num:04d}.wav"), always_2d=True)[0].mean(1)
            x = resample_poly(x, 147, 160); x = np.pad(x, (0, max(0, n - len(x))))[:n]
            note = f"№{rank} из {len(runs)}, близость {sc:.2f}" + (f"; звучит на {abs(o)} окт. {'ниже' if o < 0 else 'выше'}" if o else "")
            clips.append((f"t{num}", x * rms(orig) / rms(x), f"{num} {names[num]}", note, False))
        peak = max(np.abs(c[1]).max() for c in clips); out = []
        for tag, x, nm, note, ref in clips:
            x = x / peak * 0.8; k = int(0.008 * SR); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
            fn = f"{vn}-{tag}.wav"; sf.write(os.path.join(dst, fn), x.astype(np.float32), SR, subtype="PCM_16"); out.append([fn, nm, note, ref])
        groups.append({"name": f"{vn} — {spec['what']}", "note": f"такты {b0}–{b1 - 1}, по кругу", "clips": out})
        print(vn, [c[1] for c in out[2:]])
    meta = {"title": "Солнышко — выбор звука GM-800",
            "sub": "По каждому голосу: оригинал, Рома и лучшие тоны прибора на тех же тактах, одна громкость, по кругу. "
                   "Внутри голоса переключение сохраняет место; <kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза. "
                   "В оригинале и у Ромы в этих тактах звучат все клавиши сразу, у прибора — один голос.",
            "groups": groups}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(dst, "index.html"))


ORGAN2 = [35, 36, 32, 537, 538, 539, 540, 541, 543, 542, 42, 43, 546, 548, 550, 554, 552, 30]   # overdriven + pipes
STAB_FX = [("сухой", None), ("эхо 1/8, как в записи", dict(beats=0.5, db=-5, fb=0.25)),
           ("эхо 1/8 тише", dict(beats=0.5, db=-9, fb=0.25)), ("эхо 1/8 с длинным хвостом", dict(beats=0.5, db=-5, fb=0.5)),
           ("эхо 1/16", dict(beats=0.25, db=-6, fb=0.4)), ("эхо 1/8 с точкой", dict(beats=0.75, db=-6, fb=0.35))]


def cmd_tones2(top=6):
    """Second round after Alex's answers (2026-11-20): a sustaining layer under the riff's 330 (scored against
    ROMA's take, that is what he asked for), echo variants for the verse stab's 317, the overdriven / pipe organs.
    -> analysis/.../preview-tones2/index.html"""
    import glob, soundfile as sf, librosa
    from scipy.signal import resample_poly
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); song = gp.gmm.Song("Solnyshko"); dst = os.path.join(OUT, "preview-tones2"); os.makedirs(dst, exist_ok=True)
    src = os.path.join(OUT, "preview-tones")
    names = {int(r.split("\t")[0]): r.split("\t")[1].split("  ")[0].strip() for r in open(os.path.join(REPO, "gear", "gm-800", "tones.tsv"), encoding="utf-8")}
    hist = json.load(open(gp.HISTORY, encoding="utf-8"))["tones"]
    rms = lambda x: np.sqrt((x ** 2).mean()) + 1e-9
    rd = lambda p: sf.read(p, always_2d=True)[0].mean(1)

    def take(vn, num):
        b0, b1 = VOICES[vn]["solo"]; n = int(round((b1 - b0) * song.bar * SR))
        x = resample_poly(rd(os.path.join(song.out, f"sweep-synths-{vn}-{b0}-{b1}-t{num:04d}.wav")), 147, 160)
        return np.pad(x, (0, max(0, n - len(x))))[:n]

    def feat(x):
        C = np.abs(librosa.cqt(librosa.resample(x.astype(np.float32), orig_sr=SR, target_sr=22050), sr=22050, hop_length=512,
                               fmin=librosa.note_to_hz("C2"), n_bins=84))
        return np.log1p(30 * C / (C.max() + 1e-9))

    def sim(a, b):                                           # time x frequency cosine, best of small lags (USB latency)
        best = 0
        for l in range(-4, 5):
            p, q = (a[:, l:], b[:, :b.shape[1] - l]) if l >= 0 else (a[:, :l], b[:, -l:])
            k = min(p.shape[1], q.shape[1]); best = max(best, float((p[:, :k] * q[:, :k]).sum() / (np.linalg.norm(p[:, :k]) * np.linalg.norm(q[:, :k]) + 1e-9)))
        return best

    def write(group, clips):                                 # [(tag, x, name, note, ref)] -> same loudness, wav loops
        ref = rms(clips[0][1]); peak = max(np.abs(x * ref / rms(x)).max() for _, x, *_ in clips); out = []
        for tag, x, nm, note, isref in clips:
            x = x * ref / rms(x) / peak * 0.8; k = int(0.008 * SR); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
            sf.write(os.path.join(dst, f"{group}-{tag}.wav"), x.astype(np.float32), SR, subtype="PCM_16"); out.append([f"{group}-{tag}.wav", nm, note, isref])
        return out

    groups = []
    # 1. riff: 330 + a sustaining layer, against Roma
    b0, b1 = VOICES["riff"]["solo"]; roma, orig = rd(os.path.join(src, "riff-roma.wav")), rd(os.path.join(src, "riff-orig.wav"))
    base = take("riff", 330); R = feat(roma); cand = []
    for p in glob.glob(os.path.join(song.out, f"sweep-synths-riff-{b0}-{b1}-t*.wav")):
        num = int(p[-8:-4])
        if num == 330:
            continue
        x = take("riff", num)
        for g in (-9, -6, -3, 0, 3):                          # the layer against 330, dB (both at the same RMS first)
            cand.append((sim(feat(base / rms(base) + x / rms(x) * 10 ** (g / 20)), R), num, g, x))
    alone = sim(feat(base), R); best = {}
    for sc, num, g, x in sorted(cand, key=lambda c: -c[0]):
        best.setdefault(num, (sc, g, x))
    clips = [("roma", roma, "Рома, концерт", "к нему и подбирался слой", True), ("orig", orig, "Оригинал", "стемы keys + other", True),
             ("t330", base, "330 Bright Pulse Key один", f"близость к Роме {alone:.2f}", False)]
    for num, (sc, g, x) in list(best.items())[:top]:
        clips.append((f"t330+{num}", base / rms(base) + x / rms(x) * 10 ** (g / 20), f"330 + {num} {names[num]}",
                      f"слой {g:+d} дБ к 330; близость к Роме {sc:.2f}", False))
        print(f"riff 330 + {num} {names[num]} at {g:+d} dB: {sc:.3f} (330 alone {alone:.3f})")
    top1 = next(iter(best))
    for num, g in ((top1, -3), (194, -3)):                     # the best layer quieter, and a sustaining pulse lead
        sc, x = next((c[0], c[3]) for c in cand if c[1] == num and c[2] == g)
        clips.append((f"t330+{num}q", base / rms(base) + x / rms(x) * 10 ** (g / 20), f"330 + {num} {names[num]}",
                      f"слой {g:+d} дБ к 330; близость к Роме {sc:.2f}", False))
    groups.append({"name": "Рифф: 330 и тянущийся слой, как у Ромы", "note": f"такты {b0}–{b1 - 1}. У Ромы нота держится (через 0.3 с −5 дБ), "
                   "у 330 гаснет (−14 дБ). Слой подобран по близости к записи Ромы из 17 тонов; лучше всего легли пилы.", "clips": write("riff", clips)})
    # 2. verse stab: 317 with an echo
    b0, b1 = VOICES["vstab"]["solo"]; dry = take("vstab", 317); orig = rd(os.path.join(src, "vstab-orig.wav"))
    clips = [("orig", orig, "Оригинал", "стемы keys + other", True)]
    for i, (nm, fx) in enumerate(STAB_FX):
        x = dry if fx is None else gp.apply_delay(dry[:, None], SR, fx["beats"] * song.bar / 4, fx["db"], fx["fb"])[:, 0]
        clips.append((f"t317-fx{i}", x, "317 " + nm, "без обработки" if fx is None else f"{fx['db']} дБ, повтор ×{fx['fb']}", False))
    groups.append({"name": "Стаб куплета: 317 Super Saw Key + FX", "note": f"такты {b0}–{b1 - 1}. В записи после каждого стаба слышен повтор через восьмую, "
                   "около −5 дБ. Эхо добавляется при сборке слоя, не в приборе (голос только в плейбеке).", "clips": write("vstab", clips)})
    # 3. organ: overdriven and pipe tones
    b0, b1 = VOICES["organ"]["solo"]
    runs = sorted((r["rank"], int(num), r["score"], r["oct"]) for num, t in hist.items() for r in t["runs"]
                  if r["song"] == song.name and r["voices"] == "organ" and r["bars"] == [b0, b1] and int(num) in ORGAN2)
    clips = [("orig", rd(os.path.join(src, "organ-orig.wav")), "Оригинал", "стем other", True),
             ("roma", rd(os.path.join(src, "organ-roma.wav")), "Рома, концерт", "ориентир", True)]
    for rank, num, sc, o in runs[:top + 4]:
        clips.append((f"t{num}", take("organ", num), f"{num} {names[num]}", f"близость {sc:.2f}" + (f"; звучит на {abs(o)} окт. {'ниже' if o < 0 else 'выше'}" if o else ""), False))
    groups.append({"name": "Офф-бит орган: с перегрузом и трубные", "note": f"такты {b0}–{b1 - 1}. Второй список: VK Rotary Dist, Rock / Mad / Full OD, "
                   "церковные и Puff.", "clips": write("organ", clips)})
    meta = {"title": "Солнышко — звук, второй круг", "sub": "Три места, где ты попросил другое: слой к риффу, FX на стаб, орган. "
            "Внутри группы переключение сохраняет место; <kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза.",
            "groups": groups}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(dst, "index.html"))


def _gp():
    load = lambda nm: (lambda s: (lambda m: (s.loader.exec_module(m), m)[1])(importlib.util.module_from_spec(s)))(
        importlib.util.spec_from_file_location(nm, os.path.join(REPO, "tools", nm + ".py")))
    gp = load("gm800_part"); return gp, gp.gmm.Song("Solnyshko")


def ref_band(song, stems=("keys", "other")):
    """keys + other in the BAND key, stem timeline, mono 44.1k (cached: rubberband over the whole stems)."""
    import soundfile as sf
    path = os.path.join(OUT, "ref-" + "+".join(stems) + "-band.wav")
    if not os.path.exists(path):
        x = 0
        for st in stems:
            subprocess.run(["rubberband", "-3", "-F", "-p", str(SEMI), song.stem(st), path + ".tmp.wav"], capture_output=True, check=True)
            y = sf.read(path + ".tmp.wav", always_2d=True)[0].mean(1); x = y if isinstance(x, int) else x[:min(len(x), len(y))] + y[:min(len(x), len(y))]
        os.remove(path + ".tmp.wav"); sf.write(path, x.astype(np.float32), SR)
    return sf.read(path)[0]


def voice_audio(gp, song, part, n):
    """{(voice, tone): mono 44.1k in the stem timeline} from the recorded takes, with the note gains and the echo
    of `layer` but WITHOUT the take gains."""
    import soundfile as sf
    from scipy.signal import resample_poly
    out = {}
    for tk in part["layer"]["takes"]:
        x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).astype(np.float64)
        x = gp.apply_gains(x, gp.voice_gains(song, part, tk["voice"], *tk["bars"]), gp.SR)
        if tk.get("delay"):
            d = tk["delay"]; x = gp.apply_delay(x, gp.SR, d["beats"] * song.bar / 4, d.get("db", -6.0), d.get("fb", 0.25))
        k = int(0.3 * gp.SR); x[-k:] *= np.linspace(1, 0, k)[:, None]
        y = resample_poly(x.mean(1), 147, 160); a = int(round(song.t_stem(tk["bars"][0]) * SR))
        buf = out.setdefault((tk["voice"], tk.get("tone") or "zen"), np.zeros(n)); m = min(len(y), n - a); buf[a:a + m] += y[:m]
    return out


def cmd_check():
    """Every recorded take against a plain synth render of the same notes: silent quarters, the time of the attacks,
    the notes (chroma). A take that is off here was disturbed or sent wrong."""
    import librosa
    gp, song = _gp(); part = json.load(open(PART, encoding="utf-8")); bad = 0
    for i, tk in enumerate(part["layer"]["takes"]):
        b0, b1 = tk["bars"]; vn = tk["voice"]; x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).mean(1); sr = gp.SR
        n = int((b1 - b0) * song.bar * sr); x = x[:n]
        kind, fc, dec, g = TIMBRE[vn]; y = np.zeros(int(n * SR / sr) + SR)
        for t, m, d in gp.voice_line(song, part, vn, b0, b1):
            z = synth(kind, fc, dec, 440 * 2 ** ((m - 69) / 12), max(d, 0.03)); a = int(t * SR); k = min(len(z), len(y) - a); y[a:a + k] += z[:k]
        X = librosa.resample(x.astype(np.float32), orig_sr=sr, target_sr=22050); Y = librosa.resample(y.astype(np.float32), orig_sr=SR, target_sr=22050)[:len(X)]
        ch = lambda v: librosa.feature.chroma_cqt(y=v, sr=22050, hop_length=512)
        cx, cy = ch(X), ch(Y); k = min(cx.shape[1], cy.shape[1]); act = cy[:, :k].sum(0) > 1e-6
        csim = float((cx[:, :k] * cy[:, :k]).sum(0)[act].mean() / (np.linalg.norm(cx[:, :k], axis=0) * np.linalg.norm(cy[:, :k], axis=0) + 1e-9)[act].mean())
        on = lambda v: np.maximum(0, np.diff(librosa.feature.rms(y=v, frame_length=256, hop_length=32)[0]))
        ox, oy = on(X), on(Y); m = int(0.08 * 22050 / 32); k = min(len(ox), len(oy))
        cc = [np.dot(ox[m:k - m], oy[m + l:k - m + l]) for l in range(-m, m)]; lag = -(int(np.argmax(cc)) - m) * 32 / 22050 * 1000
        q = len(x) // 8; db = [20 * np.log10(np.sqrt((x[j:j + q] ** 2).mean()) + 1e-9) for j in range(0, len(x) - q + 1, q)]
        notes_q = [any(j * (b1 - b0) / 8 <= nt[0] - b0 + (nt[1] - 1) / 4 < (j + 1) * (b1 - b0) / 8 for nt in part["voices"][vn]["notes"]) for j in range(8)]
        silent = [j for j in range(8) if notes_q[j] and db[j] < -65]
        flag = "  <-- CHECK" if silent or csim < 0.55 or abs(lag) > 45 else ""; bad += bool(flag)
        print(f"take {i:2} {vn:8} t{tk['tone']:<4} bars {b0:3}-{b1 - 1:<3} rms {20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9):6.1f} dB  "
              f"attacks {lag:+4.0f} ms vs the grid  notes {csim:.2f}  silent eighths {silent or '-'}{flag}")
    print("takes to look at:", bad)


def cmd_calibrate():
    """Gains of the voices from the record -> parts/synths.gains.json (read by `notes`). Level of a group = the
    power of keys + other (band key) in the bars where the group is alone, section by section; inside a group that
    never plays alone the split comes from a non-negative fit of the stems' power spectrogram by the voices'.
    The riff's 1024 layer is tied to its 330 (+3 dB at equal RMS - Alex's choice by ear)."""
    import librosa
    from scipy.optimize import lsq_linear
    gp, song = _gp(); part = json.load(open(PART, encoding="utf-8")); ref = ref_band(song); n = len(ref)
    va = voice_audio(gp, song, part, n); rms = lambda x: np.sqrt((x ** 2).mean()) + 1e-12
    seg = lambda x, b0, b1: x[int(song.t_stem(b0) * SR):int(song.t_stem(b1) * SR)]
    tie = {}                                                 # layers of a voice: tied to its main tone
    for vn, spec in VOICES.items():
        for tone, rel in ([] if spec.get("zen") else spec.get("layers", [])):   # a plugin voice has one take, key (voice, "zen")
            b0, b1 = spec["solo"]; tie[(vn, tone)] = rel + 20 * np.log10(rms(seg(va[(vn, spec["tone"])], b0, b1)) / rms(seg(va[(vn, tone)], b0, b1)))
            va[(vn, spec["tone"])] = va[(vn, spec["tone"])] + va.pop((vn, tone)) * 10 ** (tie[(vn, tone)] / 20)
    def feat(x):
        C = np.abs(librosa.cqt(librosa.resample(x.astype(np.float32), orig_sr=SR, target_sr=22050), sr=22050, hop_length=512,
                               fmin=librosa.note_to_hz("C2"), n_bins=84)) ** 2
        six = song.bar / 16; t0 = song.t_stem(1); cols = []
        for k in range((END - 1) * 16):
            a, e = int((t0 + k * six) * 22050 / 512), int((t0 + (k + 1) * six) * 22050 / 512); cols.append(C[:, a:max(e, a + 1)].mean(1))
        return np.array(cols).T.ravel()
    keys = list(va); A = np.array([feat(va[k]) for k in keys], np.float64).T; b = feat(ref).astype(np.float64); lo, hi = [], []
    for k in keys:
        sp = spans(part["voices"][k[0]]["notes"]); r = np.sqrt(np.mean([rms(seg(ref, *s)) ** 2 for s in sp])); v = np.sqrt(np.mean([rms(seg(va[k], *s)) ** 2 for s in sp]))
        hi.append((r / v) ** 2); lo.append((r / v) ** 2 * 10 ** (-15 / 10))
    res = lsq_linear(A, b, bounds=(np.array(lo), np.array(hi))); fit = dict(zip(keys, res.x))      # power gains
    # The fit alone is not the answer: the GM-800 tones are not the record's timbre, and it pushed the main riff to
    # its floor in favour of the octave above (2026-11-20). So the LEVEL of every group comes from the bars where the
    # group is alone in keys + other (power budget, section by section); the fit only splits a group that never
    # plays alone (octs / stack, pad / strings / brass).
    P = lambda x, b0, b1: float((seg(x, b0, b1) ** 2).mean()) + 1e-18
    K = {k[0]: k for k in keys}; g2 = {}
    def group(parts, b0, b1, target):                      # parts = [(voice, power ratio inside the group)]
        mix = sum(va[K[v]] * np.sqrt(r) for v, r in parts); G = max(target, 0.1 * P(ref, b0, b1)) / P(mix, b0, b1)
        for v, r in parts:
            g2[v] = G * r
    rel = lambda v, w, db, b0, b1: P(va[K[w]], b0, b1) / P(va[K[v]], b0, b1) * 10 ** (db / 10)   # v at db under/over w (RMS)
    group([("riff", 1.0), ("riff_hi", rel("riff_hi", "riff", -8, 105, 109))], 105, 109, P(ref, 105, 109))   # keys alone
    group([("vstab", 1.0), ("vfill", 1.0)], 33, 41, P(ref, 33, 41))
    group([("organ", 1.0)], 41, 48, P(ref, 41, 48))                                                      # organ alone
    group([("arp", 1.0), ("arp_lo", rel("arp_lo", "arp", -3, 49, 57))], 49, 57, P(ref, 49, 57) - g2["organ"] * P(va[K["organ"]], 49, 57))
    group([("octs", fit[K["octs"]]), ("stack", fit[K["stack"]])], 57, 65, P(ref, 57, 65) - g2["arp"] * P(va[K["arp"]], 57, 65))
    used = sum(g2[v] * P(va[K[v]], 65, 73) for v in ("arp", "octs", "stack"))
    group([("sweep", 1.0)], 65, 73, max(P(ref, 65, 73) - used, P(ref, 65, 73) * 10 ** -1.2))             # at least -12 dB
    group([("pad", fit[K["pad"]]), ("strings", fit[K["strings"]]), ("brass", fit[K["brass"]])], 73, 81, P(ref, 73, 81))
    g2["roll"] = g2["brass"]
    gains = {}
    for v, x in g2.items():
        k = K[v]; sp = spans(part["voices"][v]["notes"]); own = np.mean([P(va[k], *q) for q in sp]) * x / np.mean([P(ref, *q) for q in sp])
        gains[f"{k[0]}@{k[1]}"] = round(float(10 * np.log10(x)), 1)
        print(f"  {v:8} {k[1]:<5} {10 * np.log10(x):+6.1f} dB   (in its bars {10 * np.log10(own):+5.1f} dB to keys + other; the fit alone said {10 * np.log10(fit[k]):+5.1f})")
    for (vn, tone), r in tie.items():
        gains[f"{vn}@{tone}"] = round(gains[f"{vn}@{VOICES[vn]['tone']}"] + float(r), 1); print(f"  {vn:8} t{tone:<4} {gains[f'{vn}@{tone}']:+6.1f} dB   (tied to {VOICES[vn]['tone']})")
    json.dump(gains, open(GAINS, "w", encoding="utf-8"), indent=1); print(GAINS)


def cmd_fx():
    """The reverse cymbal of the record (in `other`, bars 8 24 120 128) is not notes: cut out of the stem in its
    windows above 3 kHz (below it the same bars carry the riff, which is now played by the GM-800), pitched into
    the band key -> parts/pb-fx.wav, stem frame."""
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt
    gp, song = _gp(); info = sf.info(song.stem("other")); sr = info.samplerate
    x = sf.read(song.stem("other"), always_2d=True)[0]; x = sosfiltfilt(butter(4, 3000, "highpass", fs=sr, output="sos"), x, axis=0)
    w = np.zeros(len(x)); r = int(0.05 * sr)
    for b0, bt0, b1, bt1 in FX_WIN:
        a, e = int((song.t_stem(b0) + (bt0 - 1) * song.bar / 4) * sr), int((song.t_stem(b1) + (bt1 - 1) * song.bar / 4) * sr)
        w[a:e] = 1; w[a - r:a] = np.linspace(0, 1, r); w[e:e + r] = np.linspace(1, 0, r)
    tmp = os.path.join(OUT, "tmp-fx"); sf.write(tmp + "-in.wav", (x * w[:, None]).astype(np.float32), sr)
    subprocess.run(["rubberband", "-3", "-F", "-p", str(SEMI), tmp + "-in.wav", tmp + "-out.wav"], capture_output=True, check=True)
    y = sf.read(tmp + "-out.wav", always_2d=True)[0]; y = np.pad(y, ((0, max(0, len(x) - len(y))), (0, 0)))[:len(x)]
    for f in ("-in.wav", "-out.wav"):
        os.remove(tmp + f)
    dst = os.path.join(SONG, "parts", "pb-fx.wav"); sf.write(dst, y.astype(np.float32), sr, subtype="FLOAT")
    print(dst, f"peak {20 * np.log10(np.abs(y).max() + 1e-9):.1f} dBFS, windows {FX_WIN}")


def cmd_result():
    """The recorded layer against what is in the playback now, whole song, with and without the band
    -> analysis/.../preview-result/index.html. Does not touch mix.json or the render."""
    import soundfile as sf
    gp, song = _gp(); dst = os.path.join(OUT, "preview-result"); os.makedirs(dst, exist_ok=True)
    n = sf.info(os.path.join(SONG, "auto-render", "all.wav")).frames; off = int(round(song.off * SR))
    rd = lambda p: sf.read(p, always_2d=True, dtype="float64")[0].mean(1)
    fit = lambda x: np.pad(x, (0, max(0, n - len(x))))[:n]
    at_off = lambda x: fit(np.concatenate([np.zeros(off), x]))
    seg = lambda x, a, b: x[int(song.t_render(a) * SR):int(song.t_render(b) * SR)]
    rms = lambda x: np.sqrt((x ** 2).mean()) + 1e-9
    cand = os.path.exists(CAND)                                # a candidate layer (`candidate`) against the playback's
    def lay(path):
        x = at_off(rd(path) + rd(os.path.join(SONG, "parts", "pb-fx.wav")))
        a, k = int(song.t_render(145) * SR), int(0.25 * SR)   # the stop on 145: the tones ring on (-29 dB against -43
        x[a:a + k] *= np.linspace(1, 0, k); x[a + k:] = 0; return x   # in the record) - the mix.json layer has this mute too
    src = {"new": lay(CAND if cand else os.path.join(SONG, "parts", "pb-synths.wav")), "roma": lay(os.path.join(SONG, "parts", "pb-synths.wav")),
           "orig": at_off(ref_band(song))}
    ref = rms(seg(src["orig"], 9, 145))
    for k in src:                                             # one loudness over the song for all three
        src[k] = src[k] * ref / rms(seg(src[k], 9, 145))
    ctx = sum(fit(rd(os.path.join(SONG, "auto-render", p))) for p in ("stems/drums.mp3", "stems/vocal.mp3", "pb-bass.mp3"))
    ctx *= 2.8 * ref / rms(seg(ctx, 9, 145))
    peak = max(np.abs(v + ctx).max() for v in src.values())
    for k, v in src.items():
        for tag, x in (("", v), ("-ctx", v + ctx)):
            subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-b:a", "160k",
                            os.path.join(dst, f"{k}{tag}.mp3")], input=(x / peak * 0.9).astype(np.float32).tobytes(), check=True)
    print("section levels, dB to keys + other of the record (both at the same loudness over the song):")
    for b0, b1, nm in [(1, 9, "intro"), (9, 17, "riff"), (17, 25, "alex in"), (33, 41, "verse"), (41, 49, "chorus"), (49, 57, "arp"), (57, 73, "more arp"),
                       (73, 81, "soft verse"), (81, 89, "verse 2"), (89, 105, "chorus 2"), (105, 113, "riff solo"), (113, 129, "riff + organ"), (129, 145, "last chorus")]:
        o = rms(seg(src["orig"], b0, b1)); print(f"  {b0:3}-{b1 - 1:<3} {nm:13} new {20 * np.log10(rms(seg(src['new'], b0, b1)) / o):+5.1f}   in the playback {20 * np.log10(rms(seg(src['roma'], b0, b1)) / o):+5.1f}")
    part = json.load(open(PART, encoding="utf-8"))
    cues = [(c["bar"], c["text"]) for c in song.mix["cues"] if str(c.get("beat", 1)) == "1"]
    rows = "".join(f"<tr><td>{vn}</td><td>{VOICES[vn]['what']}</td><td class=n>{' + '.join(str(t) for t in dict.fromkeys(tk.get('tone') or 'ZENOLOGY ' + tk['zen'] for tk in part['layer']['takes'] if tk['voice'] == vn))}</td></tr>" for vn in VOICES)
    meta = {"bar": song.bar, "bar1": song.t_render(1), "cues": cues, "dur": n / SR, "ctx": "-ctx", "marks": [], "ver": f"?v={int(time.time())}",
            "title": "Солнышко — рифф тоном Sunrise (ZENOLOGY)" if cand else "Солнышко — слой клавиш в плейбеке",
            "sub": ("Кандидат: рифф сыгран плагином ZENOLOGY, тон Sunrise полусухой; остальные голоса — прежние дубли GM-800. "
                    "Все три источника на одной громкости по песне. В плейбек кандидат ещё <b>не поставлен</b>. "
                    "Твоих живых партий (17–24, 121–127, аутро) в слое нет.") if cand else "Слой, который стоит в плейбеке, против оригинала.",
            "tracks": [["1", "new.mp3", "Новый слой" if cand else "Слой в плейбеке", "рифф — Sunrise полусухой (ZENOLOGY)" if cand else "как в parts/pb-synths.wav"],
                       ["2", "roma.mp3", "Сейчас в плейбеке", "рифф — GM-800, 330 + 1024", True],
                       ["3", "orig.mp3", "Оригинал", "стемы keys + other", True]],
            "html": "<h2>Что записано</h2><div class=wrap><table><tr><th>Голос</th><th>Что</th><th>Тон</th></tr>" + rows + "</table></div>"}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-listen-full.html"), encoding="utf-8").read()
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(dst, "index.html"))


SOFT = os.path.join(OUT, "soft.notes.json")              # scratch notes for the sound search of the soft verse


def cmd_softnotes():
    """The soft-verse chords as HELD chords (one a bar, the pitches of `brass`) -> analysis/.../soft.notes.json, for
    `zenology_render.py sweep "Solnyshko" <that file> chords 73 77`. In the record the part hardly breaks: inside a
    triplet slot its level moves by 3 dB (ours, played as stabs: 16), so it is a held dark chord that pulses a little."""
    part = json.load(open(PART, encoding="utf-8")); bars = {}
    for n in part["voices"]["brass"]["notes"]:
        bars.setdefault(n[0], []).append(n[3])
    notes = []
    for b, ch in sorted(bars.items()):
        if len(set(ch)) > 1:
            print(f"  bar {b}: more than one chord {sorted(set(ch))} - the first is held")
        notes.append([b, 1.0, 4.0, ch[0]])
    dump({"_about": "Soft-verse chords of «Солнышко» held (scratch, for sound search; generated by prep_solnyshko.py softnotes)",
          "stems": ["keys", "other"], "voices": {"chords": {"at": [1], "bars": END - 1, "gap": 0.002, "notes": notes}}}, SOFT)
    print(SOFT, len(notes), "chords:", " ".join(f"{n[0]}:{n[3].replace(' ', '+')}" for n in notes))


def cmd_soft():
    """Soft verse (73-88), after Alex 2026-11-21: «прерывную партию должна быть более мокрая… string тише и тембр
    поинтереснее, в оригинале она становится слышна около 2:17, более смычковая». Measures how wet the record is
    (pulsing at the triplet rate, level of the bars after the chords), fits a reverb for the brass take to it and
    builds a page: the chords alone dry / wet, the strings alone on bowed plugin tones (zenology sweep of
    `strings` 77-81, if made), the whole soft verse now and with the changes. Does not touch the layer.
    -> analysis/.../preview-soft/index.html"""
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt, resample_poly
    gp, song = _gp(); part = json.load(open(PART, encoding="utf-8")); dst = os.path.join(OUT, "preview-soft"); os.makedirs(dst, exist_ok=True)
    R = gp.SR; bar = song.bar; rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-12
    def take(voice):                                         # stereo 48k from bar 73 on, with its layer gain
        tk = next(t for t in part["layer"]["takes"] if t["voice"] == voice)
        x = gp.gmm.read_wav(gp.rec_path(song, PART, tk)).astype(np.float64) * 10 ** (tk["gain_db"] / 20)
        return x[int((73 - tk["bars"][0]) * bar * R):]
    seg = lambda v, b0, b1: v[int((b0 - 73) * bar * R):int((b1 - 73) * bar * R)]
    ref = ref_band(song); ref = resample_poly(ref[int(song.t_stem(73) * SR):int(song.t_stem(89) * SR)], 160, 147)
    pad, st, br = take("pad"), take("strings"), take("brass"); n = int(16 * bar * R)
    fit3 = lambda v: np.pad(v, ((0, max(0, n - len(v))), (0, 0)))[:n]; pad, st, br = fit3(pad), fit3(st), fit3(br); ref = np.pad(ref, (0, max(0, n - len(ref))))[:n]
    def swing(v, b):                                         # pulsing of the 600-2000 Hz envelope at the triplet-eighth rate
        y = sosfiltfilt(butter(4, [600, 2000], "bandpass", fs=R, output="sos"), seg(v, b, b + 1)); w = int(0.01 * R)
        e = np.sqrt((y[:len(y) // w * w].reshape(-1, w) ** 2).mean(1)); e = e / e.mean() - 1
        sp = np.abs(np.fft.rfft(e * np.hanning(len(e)))) / len(e) * 4; return float(sp[np.argmin(np.abs(np.fft.rfftfreq(len(e), 0.01) - 6 / bar))])
    odd, even = (73, 75, 77, 79), (74, 76, 78, 80); mono = lambda v: v.mean(1) if v.ndim > 1 else v
    meas = lambda v: (float(np.mean([swing(mono(v), b) for b in odd])),
                      float(np.mean([20 * np.log10(rms(seg(mono(v), b + 1, b + 2)) / rms(seg(mono(v), b, b + 1))) for b in odd])))
    wet = lambda rt, db: (lambda y: y * rms(seg(br, 73, 74)) / rms(seg(y, 73, 74)))(gp.apply_reverb(br, R, rt, db))   # as loud in a played bar as the dry take
    tgt = meas(ref); now = meas(pad + st + br); print(f"record (keys + other): triplet pulsing {tgt[0]:.2f}, the bar after the chords {tgt[1]:+.1f} dB to the bar with them")
    print(f"layer now:             triplet pulsing {now[0]:.2f}, the bar after {now[1]:+.1f} dB")
    res = []
    for rt in (1.5, 2.5, 4.0, 6.0):
        for db in (-6, -3, 0, 3, 6, 9):
            m = meas(pad + st * 10 ** (-6 / 20) + wet(rt, db)); res.append((abs(m[0] - tgt[0]) / 0.1 + abs(m[1] - tgt[1]) / 3, rt, db, m))
    res.sort(); print("reverb on the chords (strings 6 dB down), closest to the record first:")
    for d, rt, db, m in res[:6]:
        print(f"  rt60 {rt} s, wet {db:+d} dB to the dry sound: pulsing {m[0]:.2f}, the bar after {m[1]:+.1f} dB")
    _, rt, db, _ = res[0]; groups = []
    def put(group, clips):                                   # [(id, audio, name, note, is_ref)] -> looped files of one loudness
        k = int(0.01 * R); out = []; lv = rms(mono(clips[0][1])); peak = max(np.abs(c[1] * lv / rms(mono(c[1]))).max() for c in clips)
        for cid, x, nm, note, isref in clips:
            x = x * lv / rms(mono(x)) / peak * 0.8; x = x.copy(); ramp = np.linspace(0, 1, k); x[:k] = (x[:k].T * ramp).T; x[-k:] = (x[-k:].T * ramp[::-1]).T
            fn = f"{group}-{cid}.wav"; sf.write(os.path.join(dst, fn), x.astype(np.float32), R, subtype="PCM_16"); out.append([fn, nm, note, isref])
        return out
    # Alex after the first page (2026-11-21): «дело не в реверберации, а скорее в фильтре или тоне: звук сглаженный,
    # подводный, менее выраженные атаки, менее агрессивный». Measured: inside a triplet slot the record's level moves
    # by 3 dB (ours 16) and it has 7 / 18 dB less above 2.8 / 5.6 kHz - a HELD dark chord that pulses a little. So:
    # held chords (soft.notes.json) on dark sustaining plugin tones, a 3 dB pulse at the triplet rate, light reverb.
    def pulse(x, depth=3.0):                                 # level falls by `depth` dB through every triplet slot
        t = np.arange(len(x)) / R; g = -depth * ((t % (bar / 6)) / (bar / 6)); w = int(0.015 * R); g = np.convolve(g, np.ones(w) / w, "same")
        return x * (10 ** (g / 20))[:, None]
    lp = lambda x, hz: sosfiltfilt(butter(2, hz, "lowpass", fs=R, output="sos"), x, axis=0)
    level = lambda y: y * rms(seg(br, 73, 74)) / rms(seg(y, 73, 74))          # as loud in a chord bar as the take in the playback
    chords = [("orig", ref, "Оригинал", "все клавиши записи (keys + other): партия там не отдельно", True),
              ("dry", br, "Сейчас в плейбеке", "тон 249, отдельные удары", True),
              ("f249", level(gp.apply_reverb(lp(br, 2400), R, rt, db)), "249 с фильтром и ревербом", f"те же удары, срез верхов 2.4 кГц, хвост {rt} с", False)]
    zj = os.path.join(OUT, "zenology", "zen-soft-chords-73-77.json"); held = []
    if os.path.exists(zj):
        for k, t in enumerate(json.load(open(zj, encoding="utf-8"))["top"], 1):
            full = os.path.join(OUT, f"soft-chords-{k:02d}.wav")             # the whole soft verse, if rendered (zenology_render.py render ... chords 73 89)
            x = sf.read(full if os.path.exists(full) else os.path.join(OUT, "zenology", t["file"]), always_2d=True)[0].astype(np.float64)
            y = level(gp.apply_reverb(pulse(fit3(x)), R, 2.5, 0.0)); held.append((k, t, y, os.path.exists(full)))
            chords.append((f"{k:02d}", y, t["name"], f"{t['bank']} {t['number']} · аккорд держится, пульс 3 дБ, лёгкий реверб", False))
    groups.append({"name": "Аккорды тихого куплета одни, такты 73–76", "note": "в записи это тянущийся тёмный аккорд с лёгкой пульсацией, а не отдельные удары",
                   "clips": put("chords", [(c, seg(x, 73, 77), nm, note, r) for c, x, nm, note, r in chords])})
    ws = os.path.join(OUT, "soft-strings-warm.wav")          # Alex: «warm strings» + «струнные выходят к такту 78 — вот это хорошо»
    st2 = fit3(sf.read(ws, always_2d=True)[0].astype(np.float64)) if os.path.exists(ws) else st
    st2 = st2 * rms(seg(st, 73, 89)) / rms(seg(st2, 73, 89))                 # as loud as the 1011 take, then the curve
    sw = lambda v: v * (10 ** ((-12 + 7 * np.clip((np.arange(len(v)) / R / bar - 3.5) / 1.5, 0, 1)) / 20))[:, None]   # -12 dB to bar 76.5, -5 dB from bar 78
    g3 = [("orig", seg(ref, 73, 81), "Оригинал", "все клавиши записи", True),
          ("now", seg(pad + st + br, 73, 81), "Сейчас в плейбеке", "пэд + струнные 1011 + удары 249", True),
          ("f249", seg(pad + sw(st2) + chords[2][1], 73, 81), "249 с фильтром и ревербом", "струнные Warm Strings, выходят к такту 78", False)]
    for k, t, y, whole in held:
        if whole:
            g3.append((f"{k:02d}", seg(pad + sw(st2) + y, 73, 81), t["name"], "аккорд держится; струнные Warm Strings, выходят к такту 78", False))
    groups.append({"name": "Тихий куплет целиком, такты 73–80", "note": "только клавиши слоя, без группы; струнные везде Warm Strings с выходом к такту 78", "clips": put("all", g3)})
    meta = {"title": "Солнышко — тихий куплет", "v": int(time.time()), "groups": groups,
            "sub": "Аккорды тихого куплета: варианты тона. Струнные — Warm Strings, как ты выбрал. Внутри группы переключение сохраняет место; "
                   "<kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза. В плейбеке ничего не менялось."}
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(dst, "index.html"))


def cmd_candidate():
    """The layer of parts/synths.notes.json -> analysis/.../pb-synths-candidate.wav (not parts/: the playback keeps
    its layer until Alex says so); `result` then compares it with the playback's. To put it in: copy it over
    parts/pb-synths.wav (or `gmp layer`), render, sync Stage Traxx, delete the candidate."""
    gp, song = _gp(); gp.cmd_layer(song, PART, CAND)


def sr_pad(info):
    return int(0.2 * info.samplerate)


if __name__ == "__main__":
    {"notes": cmd_notes, "plan": cmd_plan, "preview": cmd_preview, "tones": cmd_tones, "tones2": cmd_tones2, "check": cmd_check,
     "calibrate": cmd_calibrate, "fx": cmd_fx, "result": cmd_result, "candidate": cmd_candidate, "soft": cmd_soft, "softnotes": cmd_softnotes}[sys.argv[1]]()
