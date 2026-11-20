#!/usr/bin/env python3
"""Find a GM-800 sound for a part of a song's stem and check it sits level with the playback
(wiki/pipelines/gm-800-match.md). The GM-800 plays the part itself from MIDI over USB.

    gmm() { uv run -q --python 3.12 --with sounddevice --with numpy --with scipy --with python-rtmidi \
            --with librosa --with soundfile --with pyloudnorm tools/gm800_match.py "$@"; }
    gmm line    "<song>" FROM TO [--stem bass]   # notes of the stem part -> line.json
    gmm sweep   "<song>" FROM TO [--cat 21]      # every ROM tone of a category, ranked
    gmm scenes  "<song>" FROM TO 7 14 27:80=127  # band scenes play the whole part
    gmm tones   "<song>" FROM TO 645 119         # ROM tones play the whole part
    gmm tones   "<song>" FROM TO 645 --template 7  # ...inside band scene 7 (part 1, others off)
    gmm preview "<song>" FROM TO [--norm]        # in-context mp3 of every take (--norm: at pb level)
    gmm anchor                                   # re-measure the USB -> desk offset
    gmm build 31 7 645 "POPROSHU BASS"           # new scene in INIT slot 31 = scene 7 + tone 645 in part 1
    gmm level 31 part1 127                       # PART LEVEL (part 1) / SCENE LEVEL in slot memory
    gmm scenes "<song>" FROM TO 31 7             # ...re-measure; repeat level until desk ~ pb

FROM..TO = bars of the part (TO exclusive, as "mute"). Constant-tempo songs only.
Tones are set in the TEMP scene by SysEx on top of an INIT scene (--base 31): nothing is written
to the GM-800's memory - except `build` / `level`, which write one user slot (SysEx dumps before/after
in gear/gm-800/backups/sysex/). NOTE SOURCE goes to USB for the run and is ALWAYS put back; scene 1 (MUTE)
is loaded at the end. Output: analysis/gm800-match/<song>/ (audio not in git).

Level: a take is predicted at the desk through the bass anchor (Солнышко bars 9-17 on scene 7 is
matched to its synth-bass layer in PB Bass, bars 17-25): desk = LUFS(take, USB) + G, where
G = LUFS(pb anchor) - LUFS(anchor line on scene 7). Compared with the song's pb group over FROM..TO.
"""
import glob, importlib.util, json, os, subprocess, sys, time, wave
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs")
OUTROOT = os.path.join(REPO, "analysis", "gm800-match")
TONES = os.path.join(REPO, "gear", "gm-800", "tones.tsv")       # parsed official Sound List
SR = 48000
VEL = 100
OPEN = [64, 59, 55, 50, 45, 40]                                  # open strings, index 0 = high E
ANCHOR = {"song": "Demo - Solnyshko", "line": (9, 17), "scene": 7, "pb": (17, 25)}
BAND = ("drums", "keys", "other", "vocals", "backing_vocals", "guitars", "piano", "strings")


# ---- song geometry ----------------------------------------------------------------------------
def song_dir(q):
    hits = [d for d in sorted(glob.glob(os.path.join(SONGS, "*"))) if q.lower() in os.path.basename(d).lower()]
    if len(hits) != 1:
        raise SystemExit(f"song '{q}': {len(hits)} matches {[os.path.basename(h) for h in hits]}")
    return hits[0]


class Song:
    def __init__(self, q):
        self.dir = song_dir(q); self.name = os.path.basename(self.dir)
        self.mix = json.load(open(os.path.join(self.dir, "mix.json")))
        tl = json.load(open(os.path.join(self.dir, "auto-render", "timeline.json")))
        self.off, self.bar = tl["offset_sec"], tl["bar_sec"]
        if self.mix.get("click") == "follow" or self.mix.get("tempo_zone"):
            raise SystemExit("variable tempo (click: follow / tempo_zone) is not supported")
        g8 = self.mix.get("gm800", [])
        ref = [c for c in self.mix.get("cues", []) + (g8 if isinstance(g8, list) else [])
               if isinstance(c, dict) and "abs_sec" in c and str(c.get("beat", 1)).isdigit()]
        if not ref:
            raise SystemExit("no cue with abs_sec: run jamzone_render.py --check first")
        c = ref[0]
        self.bar1_render = c["abs_sec"] - (c["bar"] - 1 + (int(c.get("beat", 1)) - 1) / 4) * self.bar
        self.semi = self.mix.get("pitch_semitones", 0)
        self.out = os.path.join(OUTROOT, self.name); os.makedirs(self.out, exist_ok=True)

    def t_stem(self, bar):            # stem-file seconds of a bar line
        return self.bar1_render + (bar - 1) * self.bar - self.off

    def t_render(self, bar):
        return self.bar1_render + (bar - 1) * self.bar

    def stem(self, name):             # path of a stem: wav, else the Moises mp3 (the render reads the same file)
        for ext in (".wav", ".mp3"):
            p = os.path.join(self.dir, name + ext)
            if os.path.exists(p):
                return p
        raise SystemExit(f"no stem '{name}' (.wav/.mp3) in {self.dir}")

    def read(self, rel, t0, t1):
        import soundfile as sf
        from scipy.signal import resample_poly
        p = os.path.join(self.dir, rel)
        if not os.path.exists(p) and p.endswith(".wav"):
            p = p[:-4] + ".mp3"
        x, sr = sf.read(p, always_2d=True, dtype="float32")
        x = x[max(0, int(t0 * sr)):int(t1 * sr)]
        return resample_poly(x, SR, sr, axis=0).astype(np.float32) if sr != SR else x


# ---- stem part -> notes ------------------------------------------------------------------------
def transcribe(song, b0, b1, stem="bass"):
    import librosa
    t0, t1 = song.t_stem(b0) - 0.05, song.t_stem(b1) + 0.05
    y = song.read(f"{stem}.wav", t0, t1).mean(1)
    y = librosa.resample(y, orig_sr=SR, target_sr=22050); sr, hop = 22050, 128
    f0, _, _ = librosa.pyin(y, fmin=28, fmax=500, sr=sr, frame_length=4096, hop_length=hop)
    rdb = 20 * np.log10(librosa.feature.rms(y=y, frame_length=1024, hop_length=hop)[0] + 1e-9)
    on = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, backtrack=True, delta=0.08)
    notes = []
    for i, o in enumerate(on):
        nxt = on[i + 1] if i + 1 < len(on) else len(rdb)
        pk = rdb[o:nxt].max()
        if pk < rdb.max() - 30:
            continue
        ip = o + int(np.argmax(rdb[o:nxt])); below = np.where(rdb[ip:nxt] < pk - 15)[0]
        off = ip + (below[0] if len(below) else nxt - ip)
        fs = f0[o + int(0.03 * sr / hop):nxt]; fs = fs[~np.isnan(fs)]
        if len(fs) < 3:
            continue
        midi = float(np.median(librosa.hz_to_midi(fs)))
        notes.append({"t": round(t0 + o * hop / sr, 4), "dur": round((off - o) * hop / sr, 4),
                      "midi": int(round(midi + song.semi)), "cents": round((midi - round(midi)) * 100)})
    path = os.path.join(song.out, f"line-{b0}-{b1}.json")
    json.dump({"bars": [b0, b1], "stem": stem, "semitones": song.semi, "notes": notes}, open(path, "w"), indent=0)
    nm = "C C# D Eb E F F# G Ab A Bb B".split()
    for n in notes:
        k = (n["t"] - song.t_stem(1)) / song.bar
        print(f"  {int(k) + 1:3}.{(k % 1) * 4 + 1:4.2f}  {nm[n['midi'] % 12]}{n['midi'] // 12 - 1:<2} dur {n['dur']:.2f}")
    print(f"{len(notes)} notes -> {path}")
    return path


def load_line(song, b0, b1, stem="bass"):
    p = os.path.join(song.out, f"line-{b0}-{b1}.json")
    if not os.path.exists(p):
        transcribe(song, b0, b1, stem)
    d = json.load(open(p))
    return d["notes"]


# ---- GM-800 -------------------------------------------------------------------------------------
def gm():
    spec = importlib.util.spec_from_file_location("ll", os.path.join(REPO, "tools", "live_levels.py"))
    ll = importlib.util.module_from_spec(spec); spec.loader.exec_module(ll)
    return ll


class Rig:
    """GM-800 on USB: NOTE SOURCE = USB inside the with-block, restored + MUTE scene after."""
    def __enter__(self):
        import sounddevice as sd
        self.sd, self.ll = sd, gm()
        self.g = self.ll.GM800(); b = self.g.rq(self.ll.SYS_MIDI, 0x10)
        if not b:
            raise SystemExit("GM-800 does not answer SysEx (BOSS Tone Studio holding the port?)")
        self.scene_ch, self.part_ch, self.src0 = b[0] + 1, list(b[1:6]), (b[8] if b[8] != self.ll.NOTE_SRC_USB else 0)
        self.dev = self.ll.audio_in("GM-800")
        self.g.dt(self.ll.SYS_MIDI[:3] + [0x08], [self.ll.NOTE_SRC_USB])
        return self

    def __exit__(self, *a):
        self.g.dt(self.ll.SYS_MIDI[:3] + [0x08], [self.src0]); back = self.g.rq(self.ll.SYS_MIDI, 0x10)
        self.g.scene(1, self.scene_ch); self.g.close()
        print(f"NOTE SOURCE restored to {back[8] if back else '?'} (was {self.src0}); scene 1 MUTE loaded")

    def load(self, scene, ccs=()):
        self.g.scene(scene, self.scene_ch)
        for cc, v in ccs:
            self.g.out.send_message([0xB0 | (self.scene_ch - 1), cc, v])
        time.sleep(0.3)
        routes, _ = self.ll.part_routes(self.g, self.part_ch)
        return self.g.name(), routes

    def tone(self, msb, lsb, pc):             # part 1 of the TEMP scene only
        self.g.dt([0x10, 0x02, 0x00, 0x00], [msb, lsb, pc - 1]); time.sleep(0.35)

    def play(self, line, chans, tail=1.2):
        """line = [(t, midi, dur)]; chans(midi) -> MIDI channels. Returns stereo USB take."""
        dur = max(t + d for t, _, d in line) + tail
        rec = self.sd.rec(int((dur + 0.4) * SR), SR, channels=2, device=self.dev)
        t0 = time.perf_counter() + 0.4
        ev = sorted([(t, 0x90, n) for t, n, d in line] + [(t + d, 0x80, n) for t, n, d in line],
                    key=lambda e: (e[0], e[1] == 0x90))
        for t, st, n in ev:
            while time.perf_counter() < t0 + t:
                time.sleep(0.0005)
            for ch in chans(n):
                self.g.out.send_message([st | ch, n, VEL if st == 0x90 else 0])
        self.sd.wait()
        return rec[int(0.4 * SR):]


def route(note, routes):
    """Parts Alex would trigger: the highest open string at or below the note that a part listens to."""
    for st in range(6):
        if OPEN[st] <= note and routes[st]:
            return routes[st]
    return next((routes[st] for st in (5, 4, 3, 2, 1, 0) if routes[st]), [])


def f0_of(x):
    x = x - x.mean(); n = len(x); ac = np.fft.irfft(np.abs(np.fft.rfft(x, 2 * n)) ** 2)[:n]
    lo, hi = int(SR / 500), int(SR / 20)
    return SR / (lo + int(np.argmax(ac[lo:hi])))


def guitar_line(rig, notes, chans):
    """Probe A2 for the scene's octave shift; map the part to the notes Alex plays (>= E2)."""
    p = rig.play([(0.0, 45, 0.7)], chans, tail=0.3)[int(0.15 * SR):int(0.6 * SR)].mean(1)
    if np.sqrt((p ** 2).mean()) < 1e-4:
        return None, None
    shift = int(round((12 * np.log2(f0_of(p) / 440) + 69 - 45) / 12)) * 12
    g = [n - shift for n in notes]
    while min(g) < 40:
        g = [n + 12 for n in g]           # below the low E: the scene sounds an octave higher here
    return g, shift


def save(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def read_wav(path):
    import soundfile as sf
    return sf.read(path, always_2d=True, dtype="float32")[0]


# ---- comparison ---------------------------------------------------------------------------------
def lufs(x):
    import pyloudnorm as pyln
    v = pyln.Meter(SR).integrated_loudness(x.astype(np.float64))
    return float(v) if np.isfinite(v) else -99.0


def lag(x, ref, maxms=120):
    def e(y):
        m = np.abs(y.mean(1)); r = np.convolve(m, np.ones(96) / 96, "same")[::48]
        return np.maximum(np.diff(r), 0)
    a, b = e(ref)[:8000], e(x)[:8000]; k = min(len(a), len(b)); a, b = a[:k], b[:k]
    c = np.correlate(b - b.mean(), a - a.mean(), "full"); mid = k - 1
    return (int(np.argmax(c[mid - 10:mid + maxms])) - 10) / 1000


def feats(x, rel):
    """rel = [(t, midi, dur)] relative to x start. Median harmonic profile h1..h10 (dB re h1) of
    notes >= 0.2 s, mean note envelope at 20/50/100/150/200/250 ms (dB re its peak)."""
    prof, envs = [], []
    for t, m, d in rel:
        i0 = int(t * SR)
        if d >= 0.2:
            s = x[i0 + int(0.04 * SR):i0 + int(0.2 * SR)].mean(1)
            if len(s) < int(0.16 * SR):
                continue
            f0 = 440 * 2 ** ((m - 69) / 12)
            nf = 1 << 15; F = np.abs(np.fft.rfft(s * np.hanning(len(s)), nf)); f = np.fft.rfftfreq(nf, 1 / SR)
            h = [F[(f > j * f0 * 0.97) & (f < j * f0 * 1.03)].max() for j in range(1, 11)]
            prof.append(20 * np.log10(np.array(h) / max(h[0], 1e-9) + 1e-9))
        s = x[i0:i0 + int(0.3 * SR)].mean(1)
        if len(s) == int(0.3 * SR):
            envs.append(np.sqrt(np.convolve(s ** 2, np.ones(240) / 240, "same")))
    r = np.mean(envs, 0); dbv = 20 * np.log10(r / r.max() + 1e-9)
    return np.median(prof, 0), np.array([dbv[int(ms / 1000 * SR)] for ms in (20, 50, 100, 150, 200, 250)])


def take_feats(x, rel_band):
    """feats of a GM-800 take; finds the octave the tone really sounds in (some ROM basses and
    scenes sit an octave off the note sent) from the longest note first."""
    t, m, d = max(rel_band, key=lambda r: r[2])
    s = x[int((t + 0.04) * SR):int((t + 0.2) * SR)].mean(1)
    k = int(round(np.log2(f0_of(s) / (440 * 2 ** ((m - 69) / 12)))))
    return (*feats(x, [(t, m + 12 * k, d) for t, m, d in rel_band]), k)


def score(hx, ex, hs, es):
    hd = float(np.sqrt(np.mean((hx[1:9] - hs[1:9]) ** 2)))                       # h2..h9
    ed = float(np.sqrt(np.mean((np.maximum(ex, -30) - np.maximum(es, -30)) ** 2)))
    return hd + 0.5 * ed, hd, ed


def stem_ref(song, b0, b1, notes, stem="bass"):
    t0 = notes[0]["t"]
    x = song.read(f"{stem}.wav", t0, song.t_stem(b1) + 1.0)
    rel = [(n["t"] - t0, n["midi"] - song.semi, n["dur"]) for n in notes]   # stem is in the original key
    return x, rel


def anchor_g():
    p = os.path.join(OUTROOT, "anchor.json")
    if not os.path.exists(p):
        raise SystemExit("no anchor yet: run `gm800_match.py anchor` once")
    return json.load(open(p))["G"]


def pb_level(song, b0, b1, grp="pb-bass"):
    x = song.read(os.path.join("auto-render", f"{grp}.wav"), song.t_render(b0), song.t_render(b1))
    m = x.mean(1, keepdims=True)
    return lufs(np.repeat(m, 2, 1)) if np.abs(m).max() > 0 else -99.0   # Stage Traxx mono fold (+3.01)


def report(song, b0, b1, takes, notes, stem="bass", grp="pb-bass"):
    """takes = {label: wav path}. Timbre vs the stem + level at the desk vs the pb group."""
    xs, rel = stem_ref(song, b0, b1, notes, stem)
    hs, es = feats(xs, rel)
    G = anchor_g(); pb_in = pb_level(song, b0, b1, grp)
    pb_after = pb_level(song, b1, b1 + 8, grp)
    print(f"stem harmonics h1..h10: {' '.join(f'{v:4.0f}' for v in hs)}   env {' '.join(f'{v:5.1f}' for v in es)}")
    print(f"{grp}: bars {b0}-{b1} {pb_in:.1f}, bars {b1}-{b1 + 8} {pb_after:.1f}  (G = {G:+.1f} dB USB -> desk)")
    rows = []
    for lab, p in takes.items():
        x = read_wav(p); lg = max(lag(x, xs), 0); x = x[int(lg * SR):]
        hx, ex, _ = take_feats(x, [(t, m + song.semi, d) for t, m, d in rel])   # takes are in the band key
        sc, hd, ed = score(hx, ex, hs, es)
        desk = lufs(x[:len(xs)]) + G
        rows.append((sc, lab, hd, ed, desk, hx))
    rows.sort()
    for sc, lab, hd, ed, desk, hx in rows:
        print(f"  {lab:28} score {sc:5.1f} (harm {hd:4.1f} env {ed:4.1f})  desk {desk:6.1f} ({desk - pb_after:+.1f} vs pb after)"
              f"  h {' '.join(f'{v:4.0f}' for v in hx)}")
    json.dump([{"label": r[1], "score": r[0], "harm": r[2], "env": r[3], "desk": r[4], "vs_pb_after": r[4] - pb_after}
               for r in rows], open(os.path.join(song.out, f"report-{b0}-{b1}.json"), "w"), ensure_ascii=False, indent=1)


# ---- commands -----------------------------------------------------------------------------------
def tone_table(cat=None):
    rows = []
    for l in open(TONES):
        no, nm, msb, lsb, pc, c = l.rstrip("\n").split("\t")
        if cat is None or c.split(":")[0] == str(cat):
            rows.append((int(no), nm, int(msb), int(lsb), int(pc), c))
    return rows


def cmd_scenes(song, b0, b1, specs):
    notes = load_line(song, b0, b1); t0 = notes[0]["t"]
    takes = {}
    with Rig() as rig:
        for spec in specs:
            sc, _, cc = spec.partition(":")
            ccs = [tuple(int(v) for v in cc.split("="))] if cc else []
            nm, routes = rig.load(int(sc), ccs)
            ch = lambda n, r=routes: route(n, r)
            g, shift = guitar_line(rig, [n["midi"] for n in notes], ch)
            if g is None:
                print(f"scene {spec} {nm}: silent"); continue
            line = [(n["t"] - t0, gn, n["dur"]) for n, gn in zip(notes, g)]
            lab = f"scene-{int(sc):03d}" + (f"-cc{cc.replace('=', '_')}" if cc else "")
            p = os.path.join(song.out, f"{lab}.wav"); save(p, rig.play(line, ch)); takes[f"{lab} {nm}"] = p
            print(f"scene {spec} '{nm}': octave {shift:+d}, guitar notes {min(g)}..{max(g)}", flush=True)
    report(song, b0, b1, takes, notes)


def cmd_tones(song, b0, b1, nums, base, bars=None):
    """Whole part (or the first `bars` bars) on ROM tones over the INIT scene."""
    notes = load_line(song, b0, b1); t0 = notes[0]["t"]
    if bars:
        notes = [n for n in notes if n["t"] < song.t_stem(b0 + bars)]
    tab = {r[0]: r for r in tone_table()}
    takes = {}
    with Rig() as rig:
        nm, routes = rig.load(base)
        if "INIT" not in nm.upper():
            raise SystemExit(f"base scene {base} is '{nm}', not an INIT scene: pick a free INIT slot (--base)")
        part1 = rig.part_ch[0]
        for no in nums:
            _, tn, msb, lsb, pc, _ = tab[no]; rig.tone(msb, lsb, pc)
            line = [(n["t"] - t0, n["midi"], n["dur"]) for n in notes]   # real pitch: INIT has no octave shift
            p = os.path.join(song.out, f"tone-{no:04d}{'-probe' if bars else ''}.wav")
            save(p, rig.play(line, lambda n: [part1], tail=0.8)); takes[f"{no} {tn}"] = p
            print(f"  {no:4} {tn}", flush=True)
    return takes, notes


def cmd_template(song, b0, b1, nums, tpl):
    """ROM tones inside a band scene (its octave shift, strings, effects): TEMP scene part 1 = tone,
    parts 2-4/R off. What the new scene will sound like before anything is written."""
    notes = load_line(song, b0, b1); t0 = notes[0]["t"]
    tab = {r[0]: r for r in tone_table()}
    takes = {}
    with Rig() as rig:
        for no in nums:
            nm, routes = rig.load(tpl)
            _, tn, msb, lsb, pc, _ = tab[no]; rig.tone(msb, lsb, pc)
            for p in (1, 2, 3, 4):
                rig.g.dt([0x10, 0x02, p, 0x04], [0])                 # PART SW off
            lvl = rig.g.rq([0x10, 0x02, 0x00, 0x00], 12)
            ch = lambda n: [rig.part_ch[0]] if any(rig.part_ch[0] in r for r in routes.values()) else []
            g, shift = guitar_line(rig, [n["midi"] for n in notes], ch)
            line = [(n["t"] - t0, gn, n["dur"]) for n, gn in zip(notes, g)]
            p = os.path.join(song.out, f"tone-{no:04d}-tpl{tpl:03d}.wav")
            save(p, rig.play(line, ch)); takes[f"{no} {tn} in {tpl} {nm}"] = p
            print(f"  {no:4} {tn} in scene {tpl} '{nm}': octave {shift:+d}, part-1 level {lvl[6] if lvl else '?'}", flush=True)
    report(song, b0, b1, takes, notes)


def cmd_sweep(song, b0, b1, cat, base, bars):
    nums = [r[0] for r in tone_table(cat)]
    print(f"{len(nums)} tones of category {cat}, {bars} bars each")
    takes, notes = cmd_tones(song, b0, b1, nums, base, bars)
    b1p = b0 + bars
    xs, rel = stem_ref(song, b0, b1p, notes)
    hs, es = feats(xs, rel)
    rows = []
    for lab, p in takes.items():
        x = read_wav(p)
        if np.sqrt((x ** 2).mean()) < 1e-4:
            continue
        lg = max(lag(x, xs), 0); x = x[int(lg * SR):]
        hx, ex, k = take_feats(x, [(t, m + song.semi, d) for t, m, d in rel])   # takes are in the band key
        sc, hd, ed = score(hx, ex, hs, es)
        rows.append((sc, lab, hd, ed, k, hx))
    rows.sort()
    for sc, lab, hd, ed, k, hx in rows[:25]:
        print(f"  {lab:24} score {sc:5.1f} (harm {hd:4.1f} env {ed:4.1f}) oct {k:+d}  h {' '.join(f'{v:4.0f}' for v in hx)}")
    json.dump([{"tone": r[1], "score": r[0], "harm": r[2], "env": r[3], "oct": r[4]} for r in rows],
              open(os.path.join(song.out, f"sweep-cat{cat}-{b0}.json"), "w"), ensure_ascii=False, indent=1)


def cmd_preview(song, b0, b1, stem="bass", lead=2, tail=4, norm=False):
    """band (all stems but `stem`) from b0-lead to b1+tail; the stem outside b0..b1, each take inside,
    at its desk level (G) - or, with --norm, at the level of the pb group after the part (timbre A/B
    for sounds whose scene level is still to be set). Plus the original for A/B."""
    import pyloudnorm  # noqa: F401  (fail early)
    notes = load_line(song, b0, b1); G = anchor_g()
    a0, a1 = song.t_stem(b0 - lead), song.t_stem(b1 + tail)
    band = sum(song.read(f"{n}.wav", a0, a1) for n in BAND if n != stem and os.path.exists(os.path.join(song.dir, f"{n}.wav")))
    st = song.read(f"{stem}.wav", a0, a1); n = len(band)
    i0, i1 = int((song.t_stem(b0) - a0) * SR), int((song.t_stem(b1) - a0) * SR); f = int(0.015 * SR)
    pdir = os.path.join(song.out, "preview"); os.makedirs(pdir, exist_ok=True)

    def mp3(name, mix):
        pk = np.abs(mix).max(); mix = mix / pk * 0.89 if pk > 0.89 else mix
        out = os.path.join(pdir, f"{name}.mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "libmp3lame", "-q:a", "2", out], input=(mix * 0.85).astype("<f4").tobytes(), check=True)
        return out
    print(mp3("00-original", band + st))
    xs, _ = stem_ref(song, b0, b1, notes, stem)
    pb_after = pb_level(song, b1, b1 + 8)
    s2 = st.copy(); s2[i0 - f:i0] *= np.linspace(1, 0, f)[:, None]; s2[i0:i1] = 0; s2[i1:i1 + f] *= np.linspace(0, 1, f)[:, None]
    for p in sorted(glob.glob(os.path.join(song.out, "scene-*.wav")) + glob.glob(os.path.join(song.out, "tone-[0-9][0-9][0-9][0-9].wav"))
                    + glob.glob(os.path.join(song.out, "tone-*-tpl*.wav"))):
        x = read_wav(p); lg = max(lag(x, xs), 0); x = x[int(lg * SR):]
        y = np.zeros_like(band); s = int((notes[0]["t"] - a0) * SR); k = min(len(x), n - s)
        desk = lufs(x[:len(xs)]) + G; gain = (pb_after - desk + G) if norm else G
        y[s:s + k] = x[:k] * 10 ** (gain / 20); y[i1:] = 0
        name = os.path.basename(p)[:-4] + ("-norm" if norm else "")
        print(mp3(name, band + s2 + y), f"(desk {desk:.1f}, pb after {pb_after:.1f}{', placed at pb' if norm else ''})")


# ---- scene memory (SysEx) -----------------------------------------------------------------------
HDR = [0xF0, 0x41, 0x10, 0x00, 0x00, 0x00, 0x00, 0x26]
BACKUPS = os.path.join(REPO, "gear", "gm-800", "backups", "sysex")


def csum(b):
    return (128 - sum(b) % 128) % 128


def slot_base(n):                      # user scene n: 40 00 00 00 + (n-1) * 00 10 00 00 (7-bit)
    v = (n - 1) * 0x10
    return [0x40 + v // 128, v % 128]


class Sx:
    """Whole-scene SysEx I/O. Input by callback: a polled queue loses the first ~17 of 88 blocks."""
    def __init__(self):
        import rtmidi
        self.o, self.i = rtmidi.MidiOut(), rtmidi.MidiIn()
        self.o.open_port(self.o.get_ports().index("GM-800")); self.i.open_port(self.i.get_ports().index("GM-800"))
        self.i.ignore_types(sysex=False, timing=True, active_sense=True)
        self.buf, self.t = [], time.time(); self.i.set_callback(self._cb)

    def _cb(self, ev, _):
        m = ev[0]
        if m and m[0] == 0xF0 and len(m) > 13 and m[8] == 0x12:
            self.buf.append(m); self.t = time.time()

    def dt(self, addr, data, wait=0.05):
        body = list(addr) + list(data); self.o.send_message(HDR + [0x12] + body + [csum(body), 0xF7]); time.sleep(wait)

    def dump(self, base):
        """{"gg bb cc": data} of all 88 blocks of the scene at base ([0x10, 0] = temp)."""
        out = {}
        for g in range(6):                                   # scene groups +00..+05
            b1 = base[1] + g; b0 = base[0] + b1 // 128; b1 %= 128
            self.buf = []; body = [b0, b1, 0, 0, 0, 1, 0, 0]
            self.o.send_message(HDR + [0x11] + body + [csum(body), 0xF7]); self.t = t0 = time.time()
            while time.time() - self.t < 0.6 and time.time() - t0 < 6:
                time.sleep(0.01)
            for m in self.buf:                               # the GM-800 also sends blocks on its own
                if m[9] == b0 and m[10] == b1:               # after a scene load: keep this group only
                    out[f"{g:02X} {m[11]:02X} {m[12]:02X}"] = list(m[13:-2])
        return out

    def write(self, base, blocks):
        for k, data in sorted(blocks.items()):
            g, b2, b3 = (int(x, 16) for x in k.split())
            b1 = base[1] + g
            self.dt([base[0] + b1 // 128, b1 % 128, b2, b3], data)

    def close(self):
        self.i.cancel_callback(); self.o.close_port(); self.i.close_port()


def scene_name(blocks):
    return bytes(blocks["00 00 00"][3:19]).decode("ascii", "replace").strip()


def backup(sx, slot, tag):
    os.makedirs(BACKUPS, exist_ok=True)
    d = sx.dump(slot_base(slot))
    p = os.path.join(BACKUPS, f"{time.strftime('%Y-%m-%d')}-slot{slot:03d}-{tag}.json")
    json.dump(d, open(p, "w"), indent=0, sort_keys=True)
    return d, p


def cmd_build(slot, tpl, tone, name, force=False):
    """New scene = band scene `tpl` with ROM `tone` in part 1 and parts 2-4/R off, built in TEMP (the
    GM-800 itself resets part 1's TONE MODIFY for the new tone, as in `tones --template`), read back
    whole and written to user slot `slot` (must be an INIT scene unless --force). Backups before/after."""
    tab = {r[0]: r for r in tone_table()}
    _, tn, msb, lsb, pc, _ = tab[tone]
    sx = Sx()
    try:
        before, pb = backup(sx, slot, "before")
        if len(before) != 88:
            raise SystemExit(f"slot {slot}: read {len(before)} of 88 blocks, not writing")
        if "INIT" not in scene_name(before).upper() and not force:
            raise SystemExit(f"slot {slot} is '{scene_name(before)}', not INIT: refusing (--force to overwrite)")
        ch = 2                                               # Scene Rx channel (gm-800.md)
        sx.o.send_message([0xC0 | (ch - 1), tpl - 1]); time.sleep(1.0)
        sx.dt([0x10, 0x02, 0x00, 0x00], [msb, lsb, pc - 1], 0.5)
        for p in (1, 2, 3, 4):
            sx.dt([0x10, 0x02, p, 0x04], [0])
        time.sleep(0.3)
        new = sx.dump([0x10, 0x00])
        if len(new) != 88:
            raise SystemExit(f"temp scene: read {len(new)} of 88 blocks, not writing")
        new["00 00 00"][3:19] = list(name.ljust(16)[:16].encode("ascii"))
        sx.write(slot_base(slot), new); time.sleep(0.5)
        after, pa = backup(sx, slot, "after")
        bad = [k for k in new if after.get(k) != new[k]]
        print(f"slot {slot}: '{scene_name(before)}' -> '{scene_name(after)}' = scene {tpl} + {tone} {tn}; "
              f"88 blocks written, mismatches {bad or 'none'}\n  backups: {pb}\n           {pa}")
        sx.o.send_message([0xC0 | (ch - 1), 0])              # leave the synth on MUTE
    finally:
        sx.close()


def cmd_level(slot, what, val):
    """PART LEVEL of part 1 (ToneSelect 1, +06) or SCENE LEVEL (Common, +13) in a slot's memory."""
    b = slot_base(slot)
    addr = {"part1": [b[0], b[1] + 2, 0x00, 0x06], "scene": [b[0], b[1], 0x00, 0x13]}[what]
    sx = Sx()
    try:
        sx.dt(addr, [val], 0.3); d = sx.dump(b)
        print(f"slot {slot} '{scene_name(d)}': part-1 level {d['02 00 00'][6]}, scene level {d['00 00 00'][0x13]}")
    finally:
        sx.close()


def cmd_anchor():
    a = Song(ANCHOR["song"]); b0, b1 = ANCHOR["line"]
    notes = load_line(a, b0, b1); t0 = notes[0]["t"]
    with Rig() as rig:
        nm, routes = rig.load(ANCHOR["scene"]); ch = lambda n: route(n, routes)
        g, shift = guitar_line(rig, [n["midi"] for n in notes], ch)
        x = rig.play([(n["t"] - t0, gn, n["dur"]) for n, gn in zip(notes, g)], ch)
    save(os.path.join(OUTROOT, "anchor-scene07.wav"), x)
    lu = lufs(x); pb = pb_level(a, *ANCHOR["pb"])
    d = {"date": time.strftime("%Y-%m-%d %H:%M"), "scene": ANCHOR["scene"], "scene_name": nm, "vel": VEL,
         "usb_lufs": round(lu, 2), "pb_lufs": round(pb, 2), "G": round(pb - lu, 2)}
    json.dump(d, open(os.path.join(OUTROOT, "anchor.json"), "w"), ensure_ascii=False, indent=1)
    print(d)


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, dflt: type(dflt)(a[a.index(k) + 1]) if k in a else dflt
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    if not pos:
        raise SystemExit(__doc__)
    cmd = pos[0]
    if cmd == "anchor":
        cmd_anchor(); sys.exit()
    if cmd == "build":                                    # build SLOT TEMPLATE TONE "NAME" [--force]
        cmd_build(int(pos[1]), int(pos[2]), int(pos[3]), pos[4], "--force" in a); sys.exit()
    if cmd == "level":                                    # level SLOT part1|scene VALUE
        cmd_level(int(pos[1]), pos[2], int(pos[3])); sys.exit()
    song, b0, b1 = Song(pos[1]), int(pos[2]), int(pos[3])
    if cmd == "line":
        transcribe(song, b0, b1, opt("--stem", "bass"))
    elif cmd == "scenes":
        cmd_scenes(song, b0, b1, pos[4:])
    elif cmd == "tones" and "--template" in a:
        cmd_template(song, b0, b1, [int(x) for x in pos[4:]], opt("--template", 7))
    elif cmd == "tones":
        takes, notes = cmd_tones(song, b0, b1, [int(x) for x in pos[4:]], opt("--base", 31))
        report(song, b0, b1, takes, notes)
    elif cmd == "sweep":
        cmd_sweep(song, b0, b1, opt("--cat", 21), opt("--base", 31), opt("--bars", 3))
    elif cmd == "preview":
        cmd_preview(song, b0, b1, opt("--stem", "bass"), norm="--norm" in a)
    else:
        raise SystemExit(__doc__)
