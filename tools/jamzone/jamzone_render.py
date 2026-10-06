#!/usr/bin/env python3
"""Render a song's playback set for Stage Traxx straight from the stems — no Logic.

Per-song manifest mix.json (in the song folder) says which stems go where:

    {
      "pb-other": {"stems": ["05_Synth_Bass", "06_Synth_Lead"], "gain_db": {"06_Synth_Lead": -2},
                   "layers": ["keys-noise"]},          // contributed parts, parts/<name>.{wav,mp3}
      "pb-bass":  null,
      "pitch_semitones": -2          // optional: transpose playback to the band's key
    }

A "layer" is a part a bandmate recorded for playback (keyboardist synth, live bass...). It is
ALWAYS delivered in the BAND's key -> layers are NEVER pitched. Only the timing FRAME varies,
by what the player monitored while recording:
  - frame "render" (default; entry = "name"): cut against this song's auto-render -> already
    carries the count-in lead + render bpm -> placed 1:1 at render t=0 (no offset).
  - frame "stem" (entry = {"file": "name", "frame": "stem"}): cut against the raw Moises stems
    -> native timeline, no lead -> placed at OFF, exactly where the stems sit.
Determine the frame by MEASURING (don't assume): wide cross-correlate the part's envelope vs
drums; peak near 0 = stem-frame, peak near +OFF = render-frame. Optional "offset_ms" nudges a
residual latency/feel. Source lives in <song>/parts/<name>.{wav,mp3} (outside the stem glob ->
never auto-becomes a stem) and is folded into its group + `all`. A layer is valid only against
the render/stems it was cut to: re-cutting cues (OFF change) invalidates render-frame layers.

click and cues need no manifest: click = the JamZone Click stem, cues = cue_track.wav.
all = every music stem (preview mix). When cues exist, cue_preview.mp3 = the audition
mix to approve them: all*0.85 + click*0.6 + cues*1.0 (levels as in jamzone_cues.py).
Outputs land in <song>/auto-render/ as WAV,
aligned by construction: t=0 = bar line, stem downbeat on a bar line, whole bars
(arp MIDI-clock rule, music/arpeggiator-sync.md). auto-render/timeline.json records
{bpm, bar_sec, offset_sec} — offset to add to stem-timeline times (cues.json /
JamZone structure.json) to hit the rendered audio.

EXTERNAL songs (Moises stems: bass/drums/keys/.../metronome, not NN_*.m4a). We build a
CLEAN constant click from the lifted JamZone samples (jz_downbeat/jz_beat) at the song
bpm (mix.json "bpm" > --bpm > least-squares fit of the metronome), accent on beat 1.
Grid PHASE (first downbeat) = first metronome onset (first click = downbeat).

  Pick bpm = the SPAN-AVERAGE (least-squares over all clicks), NOT the median interval.
  Moises tempo is essentially constant (e.g. Мало тебя: lstsq=130.000, ±20ms over 3.7min),
  but the median is skewed by onset jitter (130.40 here) and a constant grid at the median
  drifts ~700ms end-to-end — which looks like the downbeat sliding off the bar. The
  filename bpm (Moises' own average) is usually the right round number.

User artifacts (stems, cue_track.wav, cues.json, logic-render/) are READ-ONLY.

Usage: jamzone_render.py "<song name or folder>" [--check] [--bpm N]
       --check = analyze + verify, write nothing
       --bpm N = force tempo (external songs; overrides measured)
   position converter (writes nothing; pick where to add a cue without bar-grid guessing):
       --map           list every cue in mix.json bar / render sec / Logic-ruler bar.beat
       --logic B[.bt]  a spot on Logic's ruler (over the loaded render) -> the mix.json "bar" to write
       --bar  N[.bt]   a mix.json bar -> render sec + where it lands on Logic's ruler
       --at   SEC      a render second / Logic SMPTE -> the mix.json "bar" to write
"""
import os, sys, glob, json, re, subprocess
import numpy as np

SR = 44100
SONGS = os.path.expanduser("~/projects/cherry-daddies/music/songs")
MIX_LVL = 0.85                                 # music level in the all-preview / practice mixes
CLICK_LVL, CUE_LVL = 0.6, 1.0                  # base click/cue levels (were matched to jamzone_cues.py)
CUE_DB, CLICK_DB = 5.0, 10.0                   # over band: cues +5dB, click +10dB (5 louder than cues)
CUE_LVL *= 10**(CUE_DB/20); CLICK_LVL *= 10**(CLICK_DB/20)   # cut over the full band in cue_preview & practice-*

# Percussion EXCEPT the main drum kit NEVER goes to playback/preview — the live drummer plays
# it, and in the mix it clashes with him (CLAUDE.md "Перкуссия — ВСЕГДА вон…"). Dropped from
# the stem universe -> absent from music/all/pb-other/pb-bass/cue_preview/practice in one place.
_PERC = re.compile(r"percussion|conga|bongo|shaker|tambour|cowbell|clap|claves|guiro|cabasa|woodblock", re.I)
def is_percussion(name):
    return bool(_PERC.search(name)) and not re.search(r"drum", name, re.I)   # the kit always stays

# ---- pb-other/pb-bass auto-leveling ----------------------------------------------------------
# pb-other plays through ONE MainStage fader, and never carries the lead/melody -- it's all
# support (FX, backing vox, pads, synths) whose Moises internal balance should be preserved.
# So the two recurring SUPPORT roles (noise/sound FX, backing vocals) are bounded by a per-role
# CEILING, ATTENUATE-ONLY: an element LOUDER than its ceiling is pulled down; nothing is ever
# boosted (boosting a quiet support element would push it forward against the musical parts that
# share the same fader -> breaks the balance). MUSICAL parts (synth lead, arpeggiator, charango...)
# are left alone -- some pb-other is meant to be loud. The ceiling both fixes 'too loud' and keeps
# loud FX/back-vox consistent across songs, while a song whose FX already sits below the ceiling is
# untouched. See docs/plans/2026-06-18-pb-other-autolevel-design.md.
FX_CEILING, BACKVOX_CEILING = -30.0, -23.0   # dBFS gated-RMS ceilings (seed; tune once by ear)
ROLE_PATTERNS = [("fx", re.compile(r"noise|sound.?effects?", re.I)),
                 ("back-vox", re.compile(r"back(ing)?.?vocals?|back.?vox", re.I))]
ROLE_CEILING = {"fx": FX_CEILING, "back-vox": BACKVOX_CEILING}   # musical -> not in map -> no level

def classify(name, overrides=None):
    """role of a stem/layer by Moises name; mix.json "roles" map overrides (also opt-out)."""
    if overrides and name in overrides: return overrides[name]
    for role, pat in ROLE_PATTERNS:
        if pat.search(name): return role
    return "musical"

def gated_rms_db(buf):
    """Perceived loudness over ACTIVE regions, in dBFS. 400ms windows / 100ms hop, mono-sum;
    keep windows within 20dB of the loudest (drops the long silences in sparse FX/back-vox so
    the measure reflects the effect's loudness, not diluted by gaps); RMS of the kept power."""
    x = buf.mean(1) if buf.ndim == 2 else buf
    win, hop = int(0.4*SR), int(0.1*SR)
    if len(x) < win:
        return 20*np.log10(float(np.sqrt(np.mean(x**2))) or 1e-9)
    p = np.array([np.mean(x[s:s+win]**2) for s in range(0, len(x)-win, hop)])
    p = p[p > 0]
    if not len(p): return -120.0
    kept = p[p >= p.max()*10**(-20/10)]                # relative gate, -20dB below loudest window
    return 20*np.log10(float(np.sqrt(kept.mean())) or 1e-9)

def auto_gain_db(buf, role):
    """(gain_db<=0, measured_db): pull buf DOWN to its role ceiling if it exceeds it, else 0.
    NEVER boosts -- only attenuates, to keep pb-other's internal balance. musical -> (0, None)."""
    ceil = ROLE_CEILING.get(role)
    if ceil is None: return 0.0, None
    loud = gated_rms_db(buf)
    return min(ceil - loud, 0.0), loud

def _stem_paths(folder):
    """name -> file for a song folder: JamZone NN_*.m4a, else external mp3/wav (legacy excluded)."""
    jz = {os.path.basename(p)[:-4]: p for p in sorted(glob.glob(os.path.join(folder, "[0-9][0-9]_*.m4a")))}
    if jz: return jz
    legacy = lambda n: (n == "cue_track" or "cue_preview" in n.lower() or n.lower().endswith(" click"))
    return {n: p for p in sorted(glob.glob(os.path.join(folder, "*.mp3")) + glob.glob(os.path.join(folder, "*.wav")))
            if not legacy(n := os.path.basename(p)[:-4])}

def pb_group_names(mix):
    """Playback group keys in a mix, json order: pb-other, pb-bass, and any extra pb-* variant
    (e.g. pb-other-keys = pb-other + the keys stem, an alternate MainStage track). Each renders
    to <name>.wav from its own stem/layer subset; stems already live in `all`, so no double-add."""
    return [k for k in mix if k.startswith("pb-")]


def levels_report(query=None):
    """Dry run (writes nothing): for every fx/back-vox stem & layer in every song (or one if
    `query`), print role, measured gated-RMS loudness, the attenuate-only gain that WOULD apply
    (<=0; 0 = below ceiling, untouched), and the post loudness. Cross-song summary shows how many
    exceed the ceiling and the post spread. This is the review gate before applying."""
    folders = ([find_folder(query)] if query else
               sorted(d for d in glob.glob(os.path.join(SONGS, "*")) if os.path.isdir(d)))
    rows = []                                          # (song, grp, name, kind, role, loud, ag, trim)
    for folder in folders:
        mix_p = os.path.join(folder, "mix.json")
        if not os.path.exists(mix_p): continue
        mix = json.load(open(mix_p)); paths = _stem_paths(folder); song = os.path.basename(folder)
        for grp in pb_group_names(mix):
            m = mix.get(grp) or {}
            overrides, trims = m.get("roles", {}), (m.get("gain_db") or {})
            for n in m.get("stems", []):
                role = classify(n, overrides)
                if role == "musical": continue
                if n not in paths: print(f"  !! {song}: stem '{n}' not found"); continue
                ag, loud = auto_gain_db(decode(paths[n]), role)
                rows.append((song, grp, n, "stem", role, loud, ag, trims.get(n, 0)))
            for ent in m.get("layers", []):
                ent = ent if isinstance(ent, dict) else {"file": ent}
                nm = ent["file"]; role = classify(nm, overrides)
                if role == "musical": continue
                lp = sorted(glob.glob(os.path.join(folder, "parts", nm + ".*")))
                if not lp: print(f"  !! {song}: layer '{nm}' not found"); continue
                ag, loud = auto_gain_db(decode(lp[0]), role)
                rows.append((song, grp, nm, "layer", role, loud, ag, ent.get("gain_db", trims.get(nm, 0))))
    if not rows:
        print("no fx/back-vox stems or layers found"); return
    cur = None
    for song, grp, name, kind, role, loud, ag, trim in rows:
        if song != cur: print(f"\n{song}"); cur = song
        mark = "  CUT" if ag < 0 else "  ok "
        tr = f"  trim{trim:+g}" if trim else ""
        print(f"  {grp:8} {role:8} {kind:5} {name:30} {loud:+6.1f}dBFS  gain {ag:+5.1f}{mark}"
              f" -> {loud+ag:+6.1f}dBFS (ceiling {ROLE_CEILING[role]:+.0f}){tr}")
    print("\nsummary (attenuate-only: gain<=0; post = measured + gain, before any per-song trim):")
    for role in ("fx", "back-vox"):
        rr = [r for r in rows if r[4] == role]
        if not rr: continue
        ncut = sum(1 for r in rr if r[6] < 0)
        meas = sorted(r[5] for r in rr); post = sorted(r[5] + r[6] for r in rr)
        print(f"  {role:8} n={len(rr):2}  {ncut} above ceiling -> cut  |  measured "
              f"{meas[0]:+.1f}..{meas[-1]:+.1f}  ->  post {post[0]:+.1f}..{post[-1]:+.1f} "
              f"(ceiling {ROLE_CEILING[role]:+.0f})")
    print(f"\nceilings: fx {FX_CEILING:+.0f}  back-vox {BACKVOX_CEILING:+.0f}  (attenuate-only, never boost)"
          f"   — dry run, nothing written")

def find_folder(q):
    if os.path.isdir(q): return os.path.abspath(q)
    for d in sorted(glob.glob(os.path.join(SONGS, "*"))):
        if os.path.isdir(d) and q.lower() in os.path.basename(d).lower(): return d
    sys.exit(f"no song folder matches '{q}'")

def decode(p, stereo=True):
    ch = "2" if stereo else "1"
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",p,"-ac",ch,"-ar",str(SR),"-f","f32le","-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).copy()
    return a.reshape(-1, 2) if stereo else a

def onsets(mono, thr_ratio=0.3, min_gap=0.3):
    win = int(0.005*SR)
    env = np.sqrt(np.convolve(mono**2, np.ones(win)/win, mode="same"))
    thr = thr_ratio*env.max()
    raw = np.where((env[1:]>thr)&(env[:-1]<=thr))[0]/SR
    out = [raw[0]]
    for t in raw[1:]:
        if t-out[-1] > min_gap: out.append(t)
    return np.array(out)

def fit_grid(click_mono):
    on = onsets(click_mono)
    # Integer beat-index per onset by CUMULATIVE per-gap rounding, not a single global
    # (on-on[0])/median division. A global division accumulates any seed error: a swung
    # click (Heads Will Roll alternates 450/460ms gaps -> bimodal median 0.9% below the true
    # beat) drifts the projected index until it slips a whole beat mid-song, mis-assigning k
    # and corrupting the lstsq slope/phase (and then the robust loop runs away). Rounding each
    # gap to its own beat-count is drift-immune: each ~one-beat gap -> +1 regardless of swing.
    d = np.diff(on)
    k = np.concatenate([[0.0], np.cumsum(np.round(d/np.median(d)))])
    A = np.vstack([k, np.ones_like(k)]).T
    beat, phase = np.linalg.lstsq(A, on, rcond=None)[0]
    # ROBUST: a constant lstsq over ALL onsets is corrupted by a non-constant intro
    # (Whenever Wherever's rubato Andean opening) or a single onset-detection glitch
    # (Destination Calabria, a doubled click mid-song) — both shift the fitted slope/
    # phase so the BODY (which is dead-constant) ends up tens of ms off the grid and the
    # cues drift. Iteratively reject onsets >20% of a beat off and refit, locking to the
    # dominant regular run. For a clean click nothing is rejected -> identical to before.
    keep = np.ones(len(on), bool)
    for _ in range(6):
        b, p = np.linalg.lstsq(np.vstack([k[keep], np.ones(int(keep.sum()))]).T,
                               on[keep], rcond=None)[0]
        nk = np.abs(on - (k*b + p)) < 0.20*b
        if int(nk.sum()) < 8 or np.array_equal(nk, keep):
            beat, phase = b, p; keep = nk if int(nk.sum()) >= 8 else keep; break
        beat, phase, keep = b, p, nk
    def dom_freq(t):
        s = click_mono[int(t*SR):int(t*SR)+int(0.08*SR)]
        S = np.abs(np.fft.rfft(s*np.hanning(len(s))))
        return np.fft.rfftfreq(len(s), 1/SR)[np.argmax(S)]
    freqs = np.array([dom_freq(t) for t in on[:4]])    # downbeat = accent among the first 4 onsets;
    kb0 = int(round((on[0]-phase)/beat))               # anchor db0 at the song's FIRST downbeat (bar 1,
    db0 = phase + (kb0 + int(np.argmax(freqs)))*beat   # so the intro is preserved), using the locked beat
    resid = np.abs((k*beat+phase) - on)[keep]
    return beat, db0, float(resid.max() if len(resid) else 0.0), len(on)

def first_sound(a, thr=1e-3):
    nz = np.where(np.abs(a).max(1) > thr)[0]
    return nz[0]/SR if len(nz) else None


def last_sound(a, thr=10 ** (-55 / 20.0)):
    """Sample count up to the last non-silent peak (> thr). Trims trailing silence:
    Moises stems are zero-padded to a common length, so len(a) would carry dead
    zeros into the playback (+ the click ticking through them). thr = -55 dBFS keeps
    real fades, strips only the silence."""
    amp = np.abs(a).max(1) if a.ndim == 2 else np.abs(a)
    nz = np.nonzero(amp > thr)[0]
    return int(nz[-1]) + 1 if len(nz) else len(a)

def place(buf, audio, at_samp):
    s0 = max(0, at_samp); a0 = max(0, -at_samp)
    n = min(len(audio)-a0, len(buf)-s0)
    if n > 0: buf[s0:s0+n] += audio[a0:a0+n]

def pitch_shift(buf, semitones):
    """Shift pitch by `semitones` (negative = down) preserving tempo, so the
    grid/alignment is untouched. Uses the rubberband CLI R3 engine (`-3`) with
    formant preservation — the ffmpeg rubberband FILTER (R2) mis-shifts pitch
    (asking -2 yields ~-1.4st), the CLI is accurate. Length is pinned to input
    (rubberband may emit ±a few samples) to keep bar lines exact.

    HEADROOM GUARD: the rubberband CLI hard-clips its output at ±1.0 even with
    float wav in and out (verified: a 1.5-peak sine comes back at exactly 1.000).
    The pitch pass runs BEFORE the headroom step and Moises stems routinely peak
    above 0dBFS, so hot material was being clipped here — audible on the kit, and
    it pinned the group's loudness to the crest of the CLIPPED buffer (a trim in
    mix.json then looked like a no-op). Scale down to 0.98 peak before the shift
    and back up after: linear, no clipping, headroom step attenuates as designed."""
    if not semitones: return buf
    import tempfile
    pk = float(np.abs(buf).max())
    guard = 0.98/pk if pk > 0.98 else 1.0
    with tempfile.TemporaryDirectory() as d:
        fin, fout = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        subprocess.run(["ffmpeg","-v","quiet","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-c:a","pcm_f32le",fin], input=(buf*guard).astype(np.float32).tobytes())
        subprocess.run(["rubberband","-3","-F","-p",str(semitones),fin,fout], capture_output=True)
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",fout,"-f","f32le","-ac","2","-ar",str(SR),"-"],
                             capture_output=True).stdout
    y = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    if guard != 1.0: y = y/guard                   # undo the guard: net effect is pure pitch
    if len(y) < len(buf):
        y = np.vstack([y, np.zeros((len(buf)-len(y), 2), np.float32)])
    return y[:len(buf)]

def wav_tempo_write(path, x, bpm):
    """WAV + cue@0 labelled 'Tempo: N' (как пишет GarageBand/Logic) ->
    MainStage Playback видит темп; Stage Traxx играет как обычный wav."""
    import struct
    x = np.clip(x, -1, 1)
    pcm = (x*32767).astype("<i2").tobytes()
    def chunk(cid, body):
        return cid + struct.pack("<L", len(body)) + body + (b"\x00" if len(body) % 2 else b"")
    fmt = struct.pack("<HHLLHH", 1, 2, SR, SR*4, 4, 16)
    cue = struct.pack("<L", 1) + struct.pack("<LL4sLLL", 1, 0, b"data", 0, 0, 0)
    label = b"adtl" + chunk(b"labl", struct.pack("<L", 1) + f"Tempo: {bpm:.1f}".encode() + b"\x00")
    body = chunk(b"fmt ", fmt) + chunk(b"data", pcm) + chunk(b"cue ", cue) + chunk(b"LIST", label)
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<L", 4+len(body)) + b"WAVE" + body)

def build_click(bpm, total, off_samp, bar):
    """Clean constant JZ-sample click for external songs: downbeat (accent) on every
    bar line of the output (which starts on a bar line at sample 0), beat elsewhere."""
    import jamzone_click as JC
    db = JC.wav_read(JC.DB); bt = JC.wav_read(JC.BT)
    beat = 60.0/bpm
    o = np.zeros(total, np.float32)
    n = int(total/(beat*SR)) + 1
    for i in range(n):
        s = round(i*beat*SR)
        hit = db if i % 4 == 0 else bt*0.5
        if s < total: o[s:s+len(hit)] += hit[:total-s]
    o = o/(np.max(np.abs(o)) or 1)*0.95
    return np.column_stack([o, o])

def met_onsets(mono):
    """every metronome onset (peak-pick, ~0.25s min gap) — keeps the real tempo map, unlike
    onsets() which is tuned for a sparse clean click. Returns onset times (s)."""
    win = int(0.004*SR)
    env = np.sqrt(np.convolve(mono**2, np.ones(win)/win, mode="same")); env /= (env.max() or 1)
    thr, mingap, peaks, i = 0.12, int(0.25*SR), [], 1
    while i < len(env)-1:
        if env[i] > thr and env[i] >= env[i-1] and env[i] > env[i+1]:
            if not peaks or i-peaks[-1] >= mingap: peaks.append(i)
            elif env[i] > env[peaks[-1]]: peaks[-1] = i
        i += 1
    return np.array(peaks)/SR

def build_follow_grid(met_mono, mix, beat, external=True):
    """Tempo-FOLLOW beat grid for songs with a real mid-song tempo change (half-time breakdown)
    that must be tracked then re-locked to the music. Steady sections are cleaned to a constant
    tempo (metronomic to play to); the slow zone is a clean slow tempo; the POST-zone grid is
    lstsq-phase-locked to the metronome's real return onsets — so when the tempo comes back the
    bar lines land on the music's downbeats again (arpeggiator/keys stay tight). Returns (bt,
    beatB, info), bt[k] = stem-time of beat k (bt[0] = downbeat).

    The Moises metronome can LAG the music across a drum-break transition (Я устал: real
    half-time kick downbeat ~105.0s, but the metronome stays 124 until ~107.1s and over-counts
    the break). So the zone is set MANUALLY via mix.json "tempo_zone":
        {"from_bar": N, "to_bar": M, "bpm": Z[, "from_beat": b, "to_beat": b, "anchor_sec": T]}
    from_bar..to_bar (beat-index span) at Z bpm; anchor_sec (stem seconds, optional) phase-locks
    the zone's first beat to the real slow downbeat (the drum break hides the phase step). Absent
    "tempo_zone" -> auto-detect the zone from the metronome's own interval deviation."""
    on = met_onsets(met_mono)
    d = np.diff(on); beatA = float(np.median(d[:min(200, len(d))]))
    info = {"n": len(on), "beatA": beatA}
    # STEADY tempo = `beat` (mix.json bpm, e.g. 124.000) — NOT the median interval beatA: the median
    # is skewed by onset jitter (Я устал: median 480.4ms=124.89bpm vs true lstsq 483.9ms=124.000),
    # and a grid at the median drifts off the song's real tempo (the user's DAW is at the true bpm).
    def phase_at(a, b):                                   # best phase for `beat`-tempo over onsets a..b
        kk = np.arange(a, b); return float(np.median(on[a:b] - kk*beat))
    tz = mix.get("tempo_zone")
    if tz:
        z0 = 4*(int(tz["from_bar"])-1) + (int(tz.get("from_beat", 1))-1)
        z1 = 4*(int(tz["to_bar"])-1)   + (int(tz.get("to_beat", 1))-1)
        if tz.get("anchors"):                          # piecewise grid through explicit beat anchors
            # [[beat_offset_from_z0, stem_sec], ...] — the breakdown tempo is NOT constant, so a
            # single bpm drifts (accumulates offset). Pin the grid to the user's real beat marks
            # (stem = his render timecode − count-in OFF); interpolate between, extrapolate the ends.
            an = tz["anchors"]
            idx = np.array([z0 + a[0] for a in an], float); tms = np.array([a[1] for a in an], float)
            slope = (tms[-1]-tms[-2])/(idx[-1]-idx[-2])
            ph_post = phase_at(z1, len(on)) if z1 < len(on)-1 else float(on[0])
            n_bt = max(len(on), z1+1, int(idx[-1])+2)
            bt = np.zeros(n_bt)
            for k in range(n_bt):
                if   k < z0: bt[k] = on[0] + k*beat
                elif k < z1: bt[k] = float(np.interp(k, idx, tms)) if k <= idx[-1] else tms[-1]+(k-idx[-1])*slope
                else:        bt[k] = ph_post + k*beat
            for k in range(1, len(bt)):                # bridge any backward step (entry/exit)
                if bt[k] < bt[k-1]:
                    j = k
                    while j < len(bt) and bt[j] <= bt[k-1]: j += 1
                    if j < len(bt): bt[k-1:j+1] = np.linspace(bt[k-1], bt[j], j-k+2)
            info.update({"manual": True, "z0": z0, "z1": z1, "accent": int(tz.get("accent", 4)),
                         "subdiv": int(tz.get("subdiv", 1)), "beatB": beat,
                         "slowbpm": 60/((tms[-1]-tms[0])/(idx[-1]-idx[0])), "zone_t": (float(bt[z0]), float(bt[z1-1]))})
            return bt, beat, info
        sb = 60.0/float(tz["bpm"])
        anchor = float(tz["anchor_sec"]) if "anchor_sec" in tz else on[0] + z0*beat
        ph_post = phase_at(z1, len(on)) if z1 < len(on)-1 else (on[0] - 0)  # 124 phase = music return
        ret = tz.get("return_sec")                         # the Moises metronome's BAR phase drifts through
        if ret is not None:                                # a half-time break (its beat count != the music's
            n = int(round((float(ret) - ph_post)/beat))    # bar count), so post k%4 no longer lands on the
            kref = int(round(n/4.0))*4                      # real downbeats, and it can lead the kick. Re-
            ph_post = float(ret) - kref*beat               # phase the post 124 grid so a downbeat (k%4==0)
            info["return_t"] = (kref, float(ret))          # sits exactly on the real return (a stem onset
                                                           # the user marks, e.g. the chorus kick-drop).
        bt = np.zeros(max(len(on), z1+1))
        for k in range(len(bt)):
            if   k < z0: bt[k] = on[0] + k*beat            # clean pre at true bpm, downbeat anchor
            elif k < z1: bt[k] = anchor + (k-z0)*sb        # clean slow zone, phase = real slow downbeat
            else:        bt[k] = ph_post + k*beat          # clean post at true bpm, phase-locked to music
        for k in range(1, len(bt)):                        # anchor may sit just before the pre-zone's
            if bt[k] < bt[k-1]:                            # last 124-beat (entry transition). Don't
                j = k                                      # CLAMP (that makes coincident beats ->
                while j < len(bt) and bt[j] <= bt[k-1]: j += 1   # double click); BRIDGE the backward
                if j < len(bt): bt[k-1:j+1] = np.linspace(bt[k-1], bt[j], j-k+2)   # step linearly
        info.update({"manual": True, "z0": z0, "z1": z1, "slowbpm": float(tz["bpm"]), "beatB": beat,
                     "accent": int(tz.get("accent", 4)), "subdiv": int(tz.get("subdiv", 1)),
                     "accent_from": int(tz.get("accent_from", z0)),  # downbeat phase (default z0)
                     "zone_t": (float(bt[z0]), float(bt[z1-1]))})
        return bt, beat, info
    core = np.where(d > beatA*1.15)[0]                    # auto: clearly-slow intervals (breakdown)
    bt = on.astype(float).copy()
    # A Moises METRONOME is ~constant outside a real breakdown, so cleaning pre/post to constant tempo
    # tightens it. A JamZone CLICK instead tracks the recording's tempo continuously (Destination
    # Calabria drifts a few % whole-song, no discrete zone) — constant-izing it makes the cues sit on a
    # straight grid that walks off the real click. For JZ (external=False) keep PURE follow: bt = on.
    if external and len(core):
        lo, hi = int(core[0]), int(core[-1])
        while lo > 0 and abs(d[lo-1]-beatA) > 0.015: lo -= 1
        while hi < len(d)-1 and abs(d[hi+1]-beatA) > 0.015: hi += 1
        za, zb = lo+1, hi+2
        for k in range(za): bt[k] = on[0] + k*beat         # clean pre at true bpm
        ph_post = phase_at(zb, len(on))
        for k in range(zb, len(on)): bt[k] = ph_post + k*beat   # clean post at true bpm
        info.update({"za": za, "zb": zb, "beatB": beat, "zone_t": (float(on[za]), float(on[zb-1])),
                     "slowbpm": 60/float(np.max(d[lo:hi+1]))})
    return bt, beat, info

RU_VOICE, EN_VOICE = "Milena", None              # macOS `say` voices (None = system default)
_SAY_CACHE = {}

# ---- optional ElevenLabs cue voice (OFF by default) -----------------------------------------
# Cue speech is macOS `say`. ElevenLabs was tried as the cue voice but sounded flat/robotic in
# the ear live (rehearsal verdict 2026-07-13) — reverted to `say`, which is now the hard default
# regardless of any key present. The whole EL path below stays dormant and is opt-in per render:
# set CUE_TTS=eleven (needs ELEVENLABS_API_KEY in env or ~/.cherry-secrets, never committed) to
# route cue words/announcements through ElevenLabs multilingual v2. Timing is engine-transparent:
# _metric_clips MEASURES each returned clip to fit words to beats; the 3-2-1 count stays recorded
# aiff clips. Override voice/model with CUE_TTS_VOICE / CUE_TTS_MODEL.
def _load_secrets():
    p = os.path.expanduser("~/.cherry-secrets")
    if os.path.exists(p):
        for ln in open(p):
            ln = ln.strip()
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1); os.environ.setdefault(k, v)
_load_secrets()
# EL only when explicitly requested; a stray key no longer auto-engages it.
ELEVEN_KEY = os.environ.get("ELEVENLABS_API_KEY") if os.environ.get("CUE_TTS", "").lower() in ("eleven", "elevenlabs", "11labs") else None
ELEVEN_VOICE = os.environ.get("CUE_TTS_VOICE", "ZSNL4hPqCnqoMPaI4jGX")   # settled cue voice
ELEVEN_MODEL = os.environ.get("CUE_TTS_MODEL", "eleven_multilingual_v2")
ELEVEN_SPEED = float(os.environ.get("CUE_TTS_SPEED", "1.0"))    # 0.7..1.2; 1.15 felt rushed -> 1.0 natural
# Cue words are rendered SEPARATELY (one synth per word, placed on its beat) — clean boundaries, no
# co-articulation smear. To keep them from sounding choppy/random (each isolated word getting its own
# intonation), tone is flattened: HIGH stability + ZERO style ("creativity" off) -> every word renders
# with the same even delivery, so the sequence reads uniform. Phrase-split (one utterance sliced by
# char timestamps) is opt-in via CUE_TTS_PHRASE=1 — natural prosody but the slices smear word edges.
ELEVEN_STABILITY = float(os.environ.get("CUE_TTS_STABILITY", "1.0"))   # 1.0 = flattest/most consistent
ELEVEN_STYLE     = float(os.environ.get("CUE_TTS_STYLE", "0.0"))       # tone ACROSS separate cue gens
ELEVEN_SEED      = int(os.environ.get("CUE_TTS_SEED", "7"))            # fixed seed -> deterministic gen
CUE_BREAK_S      = float(os.environ.get("CUE_TTS_BREAK", "0.22"))      # <break> pause between cue words
ELEVEN_PHRASE    = os.environ.get("CUE_TTS_PHRASE", "1") != "0"   # phrase-synth+gap-slice by default
                                                                  # (consistent intonation); =0 -> per-word
# cache-key suffix: MUST include every synthesis knob, else changing stability/style/seed silently
# serves a stale cached clip (was a real bug — tone drifted between files mid-tuning).
def _tts_sig(speed):
    return f"{ELEVEN_VOICE}|{ELEVEN_MODEL}|{speed}|st{ELEVEN_STABILITY}|sy{ELEVEN_STYLE}|sd{ELEVEN_SEED}"
def _voice_settings(speed):
    return {"stability": ELEVEN_STABILITY, "similarity_boost": 0.9,
            "style": ELEVEN_STYLE, "use_speaker_boost": True, "speed": speed}
TTS_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tts-cache")

# Spoken respelling: fixes TTS mispronunciation (stress/reading) WITHOUT changing the cue's
# DISPLAY text (mix.json "text" / web songs.json stay verbatim). Applied to both engines just
# before synthesis; whole-word, case-insensitive. Default fixes "DJ" -> Russian «диджей»
# (dee-JAY, stress on 2nd syllable — 11labs/say otherwise say DEE-jay). Extend per song with
# mix.json "say_as": {"word": "respelling"}.
DEFAULT_SAY_AS = {"dj": "ди́джей"}   # combining acute (U+0301) on «и» -> stress FIRST syllable (DEE-jay)
_SAY_AS = {}
def _apply_say_as(text):
    m = {**DEFAULT_SAY_AS, **_SAY_AS}
    if not m: return text
    return re.sub(r"[A-Za-zА-Яа-яЁё]+", lambda mo: m.get(mo.group(0).lower(), mo.group(0)), text)

def _trim_sil(x, thr=0.005, pad=0.02):
    """strip leading+trailing silence (ElevenLabs mp3 carries breath/pad on both ends;
    the length feeds the beat-fit, so untrimmed pad would force needless atempo squeeze)."""
    nz = np.where(np.abs(x) > thr)[0]
    if not len(nz): return x
    return x[max(0, nz[0]-int(pad*SR)): nz[-1]+int(pad*SR)]

# Each ElevenLabs cue is a SEPARATE generation, so their loudness (±10dB) and pitch (nearly an
# octave) drift — one cue sounds fine, the next is quieter/lower. Normalize every synthesized cue
# clip to a common loudness and pitch center so the whole cue track is uniform. Counts ("3 2 1")
# are recorded clips, untouched. Tunable/disable via env.
CUE_LOUDNESS_DB = float(os.environ.get("CUE_TTS_LOUDNESS", "-18"))   # target voiced RMS, dBFS
CUE_F0_HZ       = float(os.environ.get("CUE_TTS_F0", "0"))           # target pitch center (0 = OFF;
                                                                     # rubberband on voice = artifacts,
                                                                     # unacceptable — use API stitching)

def _voiced_rms(x):
    v = x[np.abs(x) > 0.02]
    return float(np.sqrt(np.mean(v**2))) if len(v) > 100 else 0.0

def _median_f0(x, lo=80, hi=350):
    """robust median voiced pitch (autocorrelation per 46ms frame, voiced frames only)."""
    W = 2048; f = []
    for i in range(0, max(0, len(x)-W), W//2):
        s = x[i:i+W]
        if np.sqrt(np.mean(s**2)) < 0.02: continue           # unvoiced/silence
        s = s*np.hanning(W); ac = np.correlate(s, s, "full")[W-1:]
        lo_l, hi_l = int(SR/hi), int(SR/lo)
        if hi_l >= len(ac): continue
        lag = np.argmax(ac[lo_l:hi_l]) + lo_l
        if lag > 0 and ac[lag] > 0.3*ac[0]: f.append(SR/lag)
    return float(np.median(f)) if len(f) >= 3 else 0.0

def _mono_pitch(x, semitones):
    if abs(semitones) < 0.1: return x
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fin, fout = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
        subprocess.run(["ffmpeg","-v","quiet","-f","f32le","-ar",str(SR),"-ac","1","-i","-",
                        "-c:a","pcm_f32le",fin], input=x.astype(np.float32).tobytes())
        subprocess.run(["rubberband","-3","-F","-p",f"{semitones:.3f}",fin,fout], capture_output=True)
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",fout,"-f","f32le","-ac","1","-ar",str(SR),"-"],
                             capture_output=True).stdout
    y = np.frombuffer(raw, np.float32).copy()
    return y if len(y) else x

def _normalize_cue(x):
    """pitch-center to CUE_F0_HZ (formant-preserved, clamped ±5 st), then loudness to
    CUE_LOUDNESS_DB voiced-RMS, peak-limited. Makes separate cue generations sound uniform."""
    if CUE_F0_HZ > 0:
        f0 = _median_f0(x)
        if f0 > 0:
            semi = max(-5.0, min(5.0, 12*np.log2(CUE_F0_HZ/f0)))
            x = _mono_pitch(x, semi)
    rms = _voiced_rms(x)
    if rms > 0:
        x = x * (10**(CUE_LOUDNESS_DB/20) / rms)
    pk = float(np.max(np.abs(x)) or 1)
    if pk > 0.97: x = x*0.97/pk
    return x.astype(np.float32)

_PREGEN = {}   # text -> pre-generated audio (filled by _pregen_blocks: all cue blocks synthesized in
               # ONE request so the voice character is identical across cues; measured f0 spread drops
               # 185Hz (independent) -> 86Hz (single gen). _eleven_tts serves these before hitting the API.

def _eleven_raw(text, speed):
    """one ElevenLabs call -> decoded mono f32 @SR (untrimmed). None on error."""
    import json as _json, urllib.request
    body = _json.dumps({"text": text, "model_id": ELEVEN_MODEL, "seed": ELEVEN_SEED,
                        "voice_settings": _voice_settings(speed)}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print(f"  ElevenLabs failed ({e})"); return None
    raw = subprocess.run(["ffmpeg","-v","quiet","-i","-","-ac","1","-ar",str(SR),"-f","f32le","-"],
                         input=data, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def _pregen_blocks(blocks):
    """Synthesize ALL distinct cue blocks in ONE request (each block = its break-joined words), so
    every cue shares one consistent voice/pitch/loudness — the ElevenLabs-documented way to keep
    separate cues uniform is to generate together, not to pitch-correct after (that wrecks the voice).
    A throwaway warm-up phrase leads so the real cues avoid the sentence-initial high contour. Pieces
    are separated by a long <break>; split back apart at the long silences, loudness-normalized, and
    stashed in _PREGEN keyed by the exact block text _eleven_tts will ask for. On any mismatch we bail
    (per-cue generation still works, just less uniform)."""
    if not (ELEVEN_KEY and blocks): return
    warm = "ready go"
    big = ' <break time="1.4s" /> '
    combined = big.join([warm] + blocks)
    audio = _eleven_raw(combined, ELEVEN_SPEED)
    if audio is None: return
    # split at long (>=0.7s) silences into pieces; the in-block 0.22s gaps stay merged
    segs = _voiced_segments(audio, min_gap=0.7, min_run=0.05)
    if len(segs) != len(blocks) + 1:
        print(f"  pregen: split {len(segs)} != {len(blocks)+1} expected — per-cue fallback"); return
    for k, b in enumerate(blocks):                        # seg 0 = warm-up (discard)
        a, e = segs[k+1]
        pad = int(0.05*SR)
        _PREGEN[b] = _normalize_cue(audio[max(0, a-pad):min(len(audio), e+pad)])
    print(f"  pregen: {len(blocks)} cue blocks in 1 generation (uniform voice), split OK")

def _eleven_tts(text, speed):
    """ElevenLabs multilingual TTS -> mono f32 @SR, silence-trimmed, disk-cached. None on error."""
    import hashlib, json as _json, urllib.request
    if text in _PREGEN: return _PREGEN[text]              # from the single-generation pre-pass
    ck = hashlib.md5(f"{_tts_sig(speed)}|{text}".encode()).hexdigest()
    os.makedirs(TTS_CACHE_DIR, exist_ok=True)
    fp = os.path.join(TTS_CACHE_DIR, ck + ".mp3")
    if not os.path.exists(fp):
        body = _json.dumps({"text": text, "model_id": ELEVEN_MODEL, "seed": ELEVEN_SEED,
                            "voice_settings": _voice_settings(speed)}).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}?output_format=mp3_44100_128",
            data=body, headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"})
        try:
            data = urllib.request.urlopen(req, timeout=30).read()
        except Exception as e:
            print(f"  ElevenLabs TTS failed ({e}) — say fallback for {text!r}"); return None
        with open(fp, "wb") as f: f.write(data)
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",fp,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return _normalize_cue(_trim_sil(x)) if len(x) else None   # uniform loudness+pitch across cues

def _say(text, voice, rate=None):
    import hashlib, tempfile
    text = _apply_say_as(text)                        # spoken respelling (display text unaffected)
    src = "EL" if ELEVEN_KEY else "say"
    key = hashlib.md5(f"{src}|{ELEVEN_VOICE if ELEVEN_KEY else voice}|{rate}|{text}".encode()).hexdigest()
    if key in _SAY_CACHE: return _SAY_CACHE[key]
    x = None
    if ELEVEN_KEY:                                   # ElevenLabs; say's fast rate -> speed 1.2 (max)
        x = _eleven_tts(text, 1.2 if rate else ELEVEN_SPEED)
    if x is None:                                    # macOS say (default, or EL failure fallback)
        with tempfile.TemporaryDirectory() as d:
            aiff = os.path.join(d, "s.aiff")
            cmd = ["say"] + (["-v", voice] if voice else []) + (["-r", str(rate)] if rate else []) \
                  + ["-o", aiff, text]
            subprocess.run(cmd, check=True)
            raw = subprocess.run(["ffmpeg","-v","quiet","-i",aiff,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                                 capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        nz = np.where(np.abs(x) > 0.005)[0]          # drop synth tail silence (it spills into the
        if len(nz): x = x[:nz[-1] + int(0.02*SR)]    # next word's slot check otherwise)
        x = x/(np.max(np.abs(x)) or 1)*0.9           # macOS say: peak-norm (EL path already
                                                     # loudness+pitch normalized in _eleven_tts)
    _SAY_CACHE[key] = x; return x

def _atempo(x, factor):
    """shorten a clip by `factor` keeping pitch (ffmpeg atempo, chained past 2.0)."""
    stages = []
    while factor > 2.0: stages.append("atempo=2.0"); factor /= 2.0
    stages.append(f"atempo={factor:.4f}")
    raw = subprocess.run(["ffmpeg","-v","quiet","-f","f32le","-ar",str(SR),"-ac","1","-i","-",
                          "-af", ",".join(stages), "-f","f32le","-"],
                         input=x.astype(np.float32).tobytes(), capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def _eleven_phrase(text, speed):
    """ElevenLabs with-timestamps: synthesize `text` as ONE utterance -> (mono f32 @SR,
    [(word_start_s, word_end_s), ...]) with word spans from the char alignment (split on
    spaces). Disk-cached (mp3 + alignment json). (None, None) on failure."""
    import hashlib, json as _json, urllib.request, base64
    ck = hashlib.md5(f"ph|{_tts_sig(speed)}|{text}".encode()).hexdigest()
    os.makedirs(TTS_CACHE_DIR, exist_ok=True)
    mp3 = os.path.join(TTS_CACHE_DIR, ck + ".mp3"); jsp = os.path.join(TTS_CACHE_DIR, ck + ".json")
    if not (os.path.exists(mp3) and os.path.exists(jsp)):
        body = _json.dumps({"text": text, "model_id": ELEVEN_MODEL, "seed": ELEVEN_SEED,
                            "voice_settings": _voice_settings(speed)}).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}/with-timestamps?output_format=mp3_44100_128",
            data=body, headers={"xi-api-key": ELEVEN_KEY, "Content-Type": "application/json"})
        try:
            resp = _json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print(f"  ElevenLabs timestamps failed ({e})"); return None, None
        with open(mp3, "wb") as f: f.write(base64.b64decode(resp["audio_base64"]))
        with open(jsp, "w") as f: _json.dump(resp.get("alignment") or {}, f)
    al = _json.load(open(jsp))
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",mp3,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                         capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32).copy()
    chars = al.get("characters") or []; st = al.get("character_start_times_seconds") or []
    en = al.get("character_end_times_seconds") or []
    if not chars or len(chars) != len(st) or len(chars) != len(en): return audio, None
    spans = []; a0 = None; b0 = None                     # group chars into words on whitespace
    for ch, a, b in zip(chars, st, en):
        if ch.strip() == "":
            if a0 is not None: spans.append((a0, b0)); a0 = None
        else:
            if a0 is None: a0 = a
            b0 = b
    if a0 is not None: spans.append((a0, b0))
    return audio, spans

def _voiced_segments(x, thr_ratio=0.08, min_run=0.04, min_gap=0.06):
    """[(start,end)] sample spans of voiced runs. The <break> pauses between cue words leave real
    silence, so a simple energy gate splits the words cleanly (no co-articulation to smear)."""
    w = max(1, int(0.01*SR))
    env = np.sqrt(np.convolve(x**2, np.ones(w)/w, mode="same"))
    voiced = env > thr_ratio*(env.max() or 1)
    segs = []; i = 0; n = len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]: j += 1
            segs.append([i, j]); i = j
        else:
            i += 1
    merged = []
    for s in segs:                                       # bridge micro-gaps inside one word
        if merged and (s[0]-merged[-1][1]) < int(min_gap*SR): merged[-1][1] = s[1]
        else: merged.append(list(s))
    return [(a, b) for a, b in merged if (b-a) >= int(min_run*SR)]

def _phrase_word_clips(metric):
    """Per-word clips for the metric block, cut from ONE natural ElevenLabs generation. The block is
    synthesized WITH <break> pauses between the words ('drums <break/> in <break/> ready <break/>
    go') — one generation so the tone/voice is consistent across the words, and the breaks insert
    REAL silence between them, so segmenting by energy gives clean per-word clips with nothing
    sliced inside a word (co-articulated continuous speech had no gaps to cut — that was the smear).
    _metric_clips then places each clip on its beat (a long word like a hyphenated label overflows
    its beat and is given extra beats there, so words never overlap). Returns clips (len==len(metric))
    or None to fall back to per-word say."""
    try:
        synth = [_apply_say_as(w) for w in metric]
        if any(" " in sw for sw in synth): return None   # a respelling split a word -> can't map 1:1
        tag = f' <break time="{CUE_BREAK_S:.2f}s" /> '
        audio = _eleven_tts(tag.join(synth), ELEVEN_SPEED)   # break tags = pauses, not spoken
        if audio is None: return None
        segs = [list(s) for s in _voiced_segments(audio)]
        if len(segs) < len(metric): return None          # can't split enough -> safe fallback
        while len(segs) > len(metric):                    # too many (a hyphen-word 'drum-bass' split at
            gaps = [segs[k+1][0]-segs[k][1] for k in range(len(segs)-1)]   # its internal seam at slow
            k = int(np.argmin(gaps))                      # speed) -> merge the NARROWEST gap (the seam is
            segs[k] = [segs[k][0], segs[k+1][1]]; segs.pop(k+1)   # tighter than the real <break> pauses)
        # extend each word end through its RELEASE (energy decays below the 8% gate while the word
        # tail is still audible -> a bare [s,e] cut clips 'up'/'build' short = sounds rushed). Follow
        # the release down to 2% of peak, into the <break> silence, capped before the next word.
        w = max(1, int(0.01*SR))
        env = np.sqrt(np.convolve(audio**2, np.ones(w)/w, mode="same")); pk = env.max() or 1
        clips = []
        for k, (s, e) in enumerate(segs):
            lim = segs[k+1][0] if k+1 < len(segs) else len(audio)
            j = e
            while j < lim-1 and env[j] > 0.02*pk: j += 1   # ride the release tail down
            clips.append(audio[max(0, s-int(0.015*SR)):j])
        return clips
    except Exception as e:
        print(f"  phrase-split failed ({e}); per-word fallback"); return None

def _metric_clips(metric, beat, squeeze=False):
    """clips for the counted block, as (clip, beats_before_event). Word i nominally lands on
    beat -(W-i). squeeze=True (fast breakdown cues) ALWAYS atempo-fits each word into its one
    slot — 'rushed' is acceptable when the slot is a fast subdiv tick and there's no room to
    spread. Speed-up is capped at `say -r 200` — faster is unintelligible; past that a
    overflow up to 0.35 beat is squeezed into the slot by atempo (<=~1.4x, still crisp — a short
    word like drums/vocal that runs ~1.1 beat should sit on ONE beat, not sprawl over two). A word
    overflowing MORE STARTS whole beats earlier and spans them at natural pace (first word only —
    the slot before it is free; e.g. instrumental, arpegiator, bass-n-beat): squeezing a genuinely
    long word into one beat sounds rushed, an empty added beat sounds dead, so the 0.35-beat line
    splits the two. Natural pace wins when it needs no more extra beats than the sped-up take."""
    W = len(metric); out = []
    phrase_clips = _phrase_word_clips(metric) if (ELEVEN_KEY and ELEVEN_PHRASE) else None  # opt-in
    for i, w in enumerate(metric):
        v = RU_VOICE if _cyrillic(w) else EN_VOICE
        budget = 0.92*beat
        if phrase_clips is not None:                     # natural-phrase slice (no faster variant;
            nat = fast = phrase_clips[i]                  # atempo handles any beat overflow below)
        else:
            nat, fast = _say(w, v), _say(w, v, 200)
        clip = next((c for c in (nat, fast) if len(c)/SR <= budget), None); extra = 0
        if clip is None and squeeze:                            # fast cue: force into the one tick slot
            clip = _atempo(fast, (len(fast)/SR)/budget)
        elif clip is None and len(fast)/SR - budget < 0.35*beat:  # overflow up to ~1.4 beat: squeeze
            clip = _atempo(fast, (len(fast)/SR)/budget)         # into the slot (<=1.4x, inaudible for a
                                                                # short word like drums/vocal). A whole
                                                                # added beat would
        elif clip is None and i == 0:                           # sit mostly empty (solo/sax ~1.05x)
            ex = lambda c: int(np.ceil((len(c)/SR - budget)/beat))
            clip = nat if ex(nat) <= ex(fast) else fast
            extra = ex(clip)
        elif clip is None:                            # mid-phrase: no room to extend backwards
            clip = _atempo(fast, (len(fast)/SR)/budget)
        out.append((clip, (W-i) + extra))
    return out

def _vowel_onset(x):
    """time of the first 0.02s window whose RMS > 0.4*peak (the spoken vowel) — so the word
    lands its stressed onset, not its leading silence, on the beat."""
    w = int(0.02*SR)
    if len(x) < w: return 0.0
    env = np.array([np.sqrt((x[i:i+w]**2).mean()) for i in range(0, len(x)-w, w//2)])
    if not len(env): return 0.0
    return int(np.argmax(env > 0.4*env.max()))*(w//2)/SR

COUNT_FILES = {"3": "~/3.aiff", "2": "~/2.aiff", "1": "~/1.aiff"}   # recorded count (say-voice era)
COUNT_WORDS = {"3": "three", "2": "two", "1": "one"}                # spoken via the cue TTS voice
def _count_clip(d):
    """the 3-2-1 count segment. With an ElevenLabs cue voice, speak it in the SAME voice as the
    announcement (so 'stop in 3 … 3 2 1' is one voice); else the recorded aiff clips."""
    return _say(COUNT_WORDS[d], EN_VOICE) if ELEVEN_KEY else _load_clip(COUNT_FILES[d])
_CLIP_CACHE = {}
def _load_clip(path):
    path = os.path.expanduser(path)
    if path not in _CLIP_CACHE:
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                             capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        _CLIP_CACHE[path] = x/(np.max(np.abs(x)) or 1)*0.9
    return _CLIP_CACHE[path]

def _cyrillic(s):
    import re
    return bool(re.search("[а-яёА-ЯЁ]", s))

def cue_beat_index(c):
    """beat index from the downbeat (bar 1 beat 1 = 0); beat defaults to 1."""
    return 4*(int(c["bar"])-1) + (int(c.get("beat", 1))-1)

# Cue placement runs on a beat GRID, not a constant beat: relt(i) = seconds of beat index i
# from the downbeat (constant songs: i*beat; tempo-follow songs: the metronome's own map, so a
# mid-song ritardando is tracked and the grid re-locks to the music when the tempo returns).
# base = the downbeat time in the final timeline; bdur(i) = the local beat duration around i.
def cue_event_time(c, base, relt):
    return base + relt(cue_beat_index(c))

def cue_kind(text, raw=False):
    if raw: return "plain"                                # literal cue: words verbatim on beats, no
    last = text.split()[-1].lower()                       # 'ready go'/'3 2 1' expansion — for the slow
    return "stop" if last == "stop" else "in" if last == "in" else "plain"  # breakdown where a word

def cue_words(text, kind):                                # already spans 2 fast clicks and there is no
    """metered words of a cue + natural-pace intro. For an 'in' cue the counted block is the LAST 4
    words ('<x> in ready go') and anything before it is the song TITLE — announcement spoken at
    natural speed as one phrase, ending just before the block. A PLAIN cue (the user typed the whole
    phrase, e.g. 'drum bass break ready go') has no title: EVERY word is metered on its own beat, so
    each is heard clearly (else the leading words get crammed into a fast intro and swallowed)."""
    if "·" in text:
        intro, rest = text.split("·", 1)
        words = (rest.strip() + " ready go" if kind == "in" else rest.strip()).split()
        return (intro.strip(), words)
    words = (text + " ready go" if kind == "in" else text).split()
    if kind == "in" and len(words) > 4:                   # title (natural) + '<x> in ready go' block
        return (" ".join(words[:-4]), words[-4:])
    if len(words) > 3 and words[-2:] == ["ready", "go"] and _cyrillic(words[0]) and not _cyrillic(words[-3]):
        for idx, w in enumerate(words):
            if not _cyrillic(w):
                return (" ".join(words[:idx]), words[idx:])
    return ("", words)                                    # plain: meter every word, one per beat

def _cue_step(c, song_step, subdiv):
    """beats per metered word / count segment. Per-cue "step" > song "cue_step" > 'fast' subdiv
    ticks (1/subdiv, words PACKED into sub-beat ticks of a slow zone) > 1.0 (one word per beat).
    song "cue_step" > 1 SPREADS each word over N beats — for very fast songs (e.g. 171 bpm) where
    one-word-per-beat is too rushed to parse in-ear; the block just spans N× the beats, 'go' still
    one step before the event."""
    if "step" in c:  return float(c["step"])
    if song_step:    return float(song_step)
    return 1.0/subdiv if c.get("fast") and subdiv > 1 else 1.0

_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
def _note_hz(nm):
    """note name (e.g. 'C#4', 'Eb3') -> Hz. A4 = 440, middle C = C4."""
    import re
    m = re.match(r'^([A-Ga-g])([#b]?)(-?\d+)$', nm.strip())
    midi = (int(m.group(3)) + 1)*12 + _PC[m.group(1).upper()] + {'#': 1, 'b': -1, '': 0}[m.group(2)]
    return 440.0*2**((midi - 69)/12)

def _pluck(f, dur_s):
    """One plucked string (Karplus-Strong) at f Hz, ringing for dur_s. A short full-band
    noise burst into a lowpass-feedback delay line -> bright pluck attack with the upper
    harmonics decaying fastest (a guitar/string, not a beep). Excitation is seeded per pitch
    so renders stay reproducible; the per-period gain is set from dur_s so a single pluck is
    still ~-12 dB at clip end -> let-rings the whole bar before the vocal."""
    n = max(1, int(dur_s*SR))
    N = max(2, int(round(SR/f)))                 # delay length = one period of the note
    noise = np.random.default_rng(int(round(f))).uniform(-1.0, 1.0, N)   # pluck color/attack
    sine = np.sin(2*np.pi*np.arange(N)/N)        # exactly one period -> seeds the fundamental
    d = 0.3*noise + 0.7*sine                     # so the fundamental wins (no octave-up at high notes)
    g = 0.25 ** (N/float(n))                      # per-period feedback -> long, controlled ring
    nper = -(-n // N)                             # ceil(n/N) period passes
    out = np.empty(nper*N)
    for p in range(nper):
        out[p*N:(p+1)*N] = d
        d = g*0.5*(d + np.roll(d, -1))            # avg with neighbour = one-pole string damping
    return out[:n]

def _chord_clip(notes, dur_s, level=0.5):
    """Plucked-string in-ear pitch reference (guitar timbre), authored directly in the BAND
    key (cue track is never pitch-shifted). One Karplus-Strong pluck per note, let ringing the
    whole bar; a tiny stagger strums a real multi-note chord (single-note refs unaffected)."""
    n = int(dur_s*SR); y = np.zeros(max(n, 1))
    for k, nm in enumerate(notes):
        p = _pluck(_note_hz(nm), dur_s)
        s = int(0.012*SR)*k                       # strum stagger (0 for the first/only note)
        if s: p = np.concatenate([np.zeros(s), p])[:len(y)]
        y[:len(p)] += p[:len(y)]
    env = np.ones(len(y)); at = int(0.004*SR); rl = int(min(0.08, dur_s*0.2)*SR)
    env[:at] = np.linspace(0, 1, at)              # de-click the pluck attack
    if rl: env[-rl:] = np.cos(np.linspace(0, np.pi/2, rl))   # short fade out (no click into the block)
    return (y*env/(np.max(np.abs(y*env)) or 1)*level).astype(np.float32)

INTRO_GAP = 0.12                                          # breath between intro and the block
def cue_first_word_time(c, base, relt, bdur, subdiv=1, song_step=None):
    """earliest sound of a cue (used to size the front lead so nothing clips off the front)."""
    text = c["text"].strip(); i = cue_beat_index(c); kind = cue_kind(text, c.get("raw"))
    step = _cue_step(c, song_step, subdiv)
    if kind == "stop" or c.get("count"):
        return base + relt(i - 5*step)                    # ~announcement + 3-2-1 count
    intro, metric = cue_words(text, kind)
    blk0 = _metric_clips(metric, bdur(i)*step, (step < 1.0) or c.get("squeeze"))[0][1]
    pre = 4 if c.get("chord") else 0                      # chord reference rings a whole bar before
    t0 = base + relt(i - blk0*step - pre)                 # the block (extra bar for the vocalist)
    if intro:
        clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
        return t0 - INTRO_GAP - len(clip)/SR
    return t0

def _put(buf, clip, t):
    s = int(t*SR); a0 = max(0, -s); s = max(0, s); n = min(len(clip)-a0, len(buf)-s)
    if n > 0: buf[s:s+n, 0] += clip[a0:a0+n]; buf[s:s+n, 1] += clip[a0:a0+n]

def build_cues(cue_list, total, base, relt, bdur, subdiv=1, song_step=None):
    """Spoken cues on the render grid. Event time = base + relt(beat index of the marked bar/beat);
    the band plays/stops ON that beat (no word on it). Words land on grid beats (relt), so a
    tempo-follow song spaces the count/block by the LOCAL tempo. Three styles:
      '<x> in'   -> '<x> in ready go', metered: last word 'go' on the beat BEFORE the event.
      '<x> stop' -> announce '<x> stop in 3', then count 3-2-1 on the three beats before the stop.
      "count": true (any text) -> announce '<text> 3' (stop: '<text> in 3'), then count 3-2-1.
         Use for a counted entry/end ('bass-only in', 'end in') when the band wants a 3-2-1 in
         instead of 'ready go'. Hyphenated words are spoken with the hyphen as a space.
    Russian words use a Russian voice; counts use the lifted count clips (~/3,2,1.aiff)."""
    buf = np.zeros((total, 2), np.float32)
    rep = []
    for c in cue_list:
        text = c["text"].strip(); kind = cue_kind(text, c.get("raw")); counted = bool(c.get("count"))
        i = cue_beat_index(c); t_event = base + relt(i)   # band event here (silent in cue track)
        step = _cue_step(c, song_step, subdiv)            # beats per metered word / count segment
        voice = RU_VOICE if _cyrillic(text) else EN_VOICE
        if kind == "stop" or counted:
            for d, k in (("3", 3), ("2", 2), ("1", 1)):   # count on event-3 / -2 / -1 (× step)
                clip = _count_clip(d)
                _put(buf, clip, base + relt(i - k*step) - _vowel_onset(clip))
            ann_text = text.replace("-", " ") + (" in 3" if kind == "stop" else " 3")
            ann = _say(ann_text, voice)                   # announcement finishes before the count
            _put(buf, ann, (base + relt(i - 3*step)) - 0.35 - len(ann)/SR)
            phrase = ann_text + " · 3 2 1"
        else:
            intro, metric = cue_words(text, kind)
            clips = _metric_clips(metric, bdur(i)*step, (step < 1.0) or c.get("squeeze"))   # ticks (333ms in a half-time
            blk0 = clips[0][1]; chord = c.get("chord")    # word sped up to fit one tick — so '<x> in
            if chord:                                     # ready go' (4 fast words) lands after the
                cs, ce = i - blk0*step - 4, i - blk0*step # band stops. synth triad rings the bar before
                _put(buf, _chord_clip(chord, relt(ce) - relt(cs)), base + relt(cs))  # the block (in-ear
                anchor = cs                               # pitch ref + extra bar). Title ends before it.
            else:
                anchor = i - blk0*step
            if intro:                                     # title etc: natural pace, right-aligned
                clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
                _put(buf, clip, base + relt(anchor) - INTRO_GAP - len(clip)/SR)
            for (clip, nb), w in zip(clips, metric):
                _put(buf, clip, base + relt(i - nb*step) - _vowel_onset(clip))
            ext = clips[0][1] - len(metric)
            phrase = (f"♪{'+'.join(chord)}♪ · " if chord else "") + (intro + " · " if intro else "") \
                     + " ".join(metric) + (f"  [{metric[0]} {1+ext} доли]" if ext else "")
        rep.append((int(c["bar"]), int(c.get("beat", 1)), phrase, t_event))
    return buf, rep

def write_cue_abs_times(mix_path, times, snaps=None):
    """Refresh "abs_sec" (render-timeline event seconds, what you hear in auto-render/cue_preview)
    and "snap_sec" (seek point = 1 bar before the cue's first spoken word, so clicking a cue in the
    web player replays the WHOLE cue, not just its event) on each cue in mix.json, IN PLACE. Edits
    the raw text line-by-line — never re-serializes the whole file — so hand-formatting (column
    alignment, field order, one cue per line) is preserved byte-for-byte. Idempotent: existing
    abs_sec/snap_sec are stripped and rewritten. times[k]/snaps[k] = the k-th cue's render event /
    seek time, in file order. Cue lines are matched by carrying both "bar" and "text" ("from_bar"/
    "to_bar" in tempo_zone never match — no surrounding quotes on `bar`, and no "text").
    Skips writing on a count mismatch (returns the mismatch for the caller to report)."""
    src = open(mix_path, encoding="utf-8").read()
    lines = src.split("\n")
    is_cue = lambda ln: re.search(r'"bar"\s*:', ln) and '"text"' in ln
    n = sum(1 for ln in lines if is_cue(ln))
    if n != len(times):
        return f"abs_sec NOT written ({mix_path}): {n} cue lines vs {len(times)} computed"
    k = 0
    for j, ln in enumerate(lines):
        if not is_cue(ln):
            continue
        body = re.sub(r',\s*"(abs_sec|snap_sec)"\s*:\s*[-0-9.]+', "", ln)   # drop any prior values
        idx = body.rfind("}")                                    # insert before the cue's closing brace
        add = f', "abs_sec": {round(times[k], 3)}'
        if snaps is not None:
            add += f', "snap_sec": {round(snaps[k], 3)}'
        k += 1
        lines[j] = body[:idx].rstrip() + add + body[idx:]
    open(mix_path, "w", encoding="utf-8").write("\n".join(lines))
    return None

def main():
    if "--levels" in sys.argv:                         # dry-run loudness report (all songs, or one
        args = [a for a in sys.argv[1:] if not a.startswith("--")]   # if a song query is given); writes
        return levels_report(args[0] if args else None)             # nothing
    folder = find_folder(sys.argv[1])
    bpm_force = float(sys.argv[sys.argv.index("--bpm")+1]) if "--bpm" in sys.argv else None
    jz_stems = {os.path.basename(p)[:-4]: p
                for p in sorted(glob.glob(os.path.join(folder, "[0-9][0-9]_*.m4a")))}
    external = not jz_stems

    mix_p = os.path.join(folder, "mix.json")
    mix = json.load(open(mix_p)) if os.path.exists(mix_p) else {}
    _SAY_AS.clear(); _SAY_AS.update({k.lower(): v for k, v in (mix.get("say_as") or {}).items()})
    if not external and not mix:
        sys.exit(f"no mix.json in {folder} — define pb-other/pb-bass first")

    if external:
        # old-pipeline artifacts share the folder (cue_track.wav, '<Artist> click.wav',
        # cue_preview) — they are NOT stems and must not leak into the playback mix
        legacy = lambda n: (n == "cue_track" or "cue_preview" in n.lower()
                            or n.lower().endswith(" click"))
        stems = {n: p
                 for p in sorted(glob.glob(os.path.join(folder, "*.mp3")) +
                                 glob.glob(os.path.join(folder, "*.wav")))
                 if not legacy(n := os.path.basename(p)[:-4])}
        click_name = next((n for n in stems if n.lower() in ("metronome", "click")), None) \
                     or sys.exit("external song: no metronome/click stem")
    else:
        stems = jz_stems
        click_name = next((n for n in stems if "click" in n.lower()), None) or sys.exit("no Click stem")
    cue_p = os.path.join(folder, "cue_track.wav")

    for grp in pb_group_names(mix):
        g = mix.get(grp) or {}
        for nm in g.get("stems", []):
            if nm not in stems: sys.exit(f"mix.json: unknown stem '{nm}' in {grp}")
        for ent in g.get("layers", []):                    # contributed parts (str | {file,...})
            nm = ent["file"] if isinstance(ent, dict) else ent
            if not glob.glob(os.path.join(folder, "parts", nm + ".*")):
                sys.exit(f"mix.json: layer '{nm}' not found in {folder}/parts/")
            for r in (ent.get("replaces", []) if isinstance(ent, dict) else []):
                if r not in stems: sys.exit(f"mix.json: layer '{nm}' replaces unknown stem '{r}'")

    players = mix.get("players") or {}                  # member -> stems/layers they play live;
    for who, owned in players.items():                  # practice mix per player = all minus these
        for nm in owned:
            if nm not in stems and not glob.glob(os.path.join(folder, "parts", nm + ".*")):
                sys.exit(f"mix.json: player '{who}' lists unknown stem/layer '{nm}'")

    click_st = decode(stems[click_name])
    beat, db0, resid, n_on = fit_grid(click_st.mean(1))  # fit_grid uses lstsq = span-average
    if external:
        db0 = float(onsets(click_st.mean(1))[0])  # first click = downbeat (user-specified)
    bpm_set = mix.get("bpm") or bpm_force         # song's locked constant tempo (mix.json > --bpm)
    if bpm_set: beat = 60.0/bpm_set
    bar = 4*beat
    follow = mix.get("click") == "follow"   # track a non-constant tempo (Moises drift OR a JZ click
    if follow:
        bt, beatB, finfo = build_follow_grid(click_st.mean(1), mix, beat, external)
        db0 = float(bt[0])                        # downbeat = first metronome onset
        def relt(i):                              # seconds of beat index i from the downbeat
            i = float(i)
            if i <= 0:            return i*beat                          # before downbeat: main tempo
            if i >= len(bt)-1:    return (bt[-1]-bt[0]) + (i-(len(bt)-1))*beatB   # past last onset
            lo = int(np.floor(i)); return (bt[lo]-bt[0]) + (i-lo)*(bt[lo+1]-bt[lo])
        def bdur(i):                              # local beat duration around index i
            i = int(i); return float(bt[i]-bt[i-1]) if 0 < i < len(bt) else beat
    else:
        def relt(i): return i*beat
        def bdur(i): return beat
    cue_subdiv = int(finfo.get("subdiv", 1)) if follow else 1   # 'fast' cues space words by ticks
    cue_step = mix.get("cue_step")                # song-level beats-per-word (>1 spreads on fast songs)
    tag = (f" (tempo-follow: {finfo['n']} onsets, zone {finfo['zone_t'][0]:.1f}-{finfo['zone_t'][1]:.1f}s "
           f"@~{finfo['slowbpm']:.0f}bpm, re-locked after)" if follow and "zone_t" in finfo
           else " (built clean click; Moises tempo ~constant)" if external else "")
    print(f"grid: beat={beat:.6f}s bpm={60/beat:.4f} bar={bar:.6f}s "
          f"downbeat={db0:.4f}s ({n_on} clicks, max resid {resid*1000:.1f}ms){tag}")

    perc = [n for n in stems if n != click_name and is_percussion(n)]
    if perc: print(f"percussion dropped (live drummer plays it, never in playback): {sorted(perc)}")
    music = [n for n in stems if n != click_name and n not in perc]
    audio = {n: decode(stems[n]) for n in music}
    cue_st = decode(cue_p) if os.path.exists(cue_p) else None

    # t=0 = bar line at/before all content, stem downbeat lands on a bar line
    srcs = list(audio.values()) + ([cue_st] if cue_st is not None else [])
    OFF = -db0
    earliest = min(t for a in srcs if (t := first_sound(a)) is not None)
    if earliest + OFF < 0:
        OFF += np.ceil(-(earliest+OFF)/bar)*bar
    # front lead: whole extra bars so the longest cue phrase (e.g. song-title start cue) fits
    # before its event instead of clipping off the front. Shifts music + cues + click together.
    # Counted from the PRE-LEAD cue base (OFF+db0): bars the earliest-sound fix already added
    # give the phrase room too — without this, push songs get a wasted extra count-in bar.
    lead = 0.0
    daw = mix.get("daw_align")                     # DAW-align: WAV time == stem (song) time, no
    if mix.get("cues") and not daw:                # count-in — drop at bar 1 and project SMPTE =
        min_word = min(cue_first_word_time(c, OFF + db0, relt, bdur, cue_subdiv, cue_step) for c in mix["cues"])  # song
        if min_word < 0.05:                        # only when the cue would actually clip the front
            lead = np.ceil((0.05 - min_word)/bar)*bar   # (0.05s onset clearance). A cue that fits
            print(f"lead: +{lead/bar:.0f} bar(s) so the longest cue fits the front")  # gets no
            #                                            wasted count-in bar — the silent intro bars
            #                                            already carry the click before the music.
    # forced count-in: songs whose music's own intro starts under the start cue (no clean
    # count-in space) set "count_in": N to push N whole silent bars in front — the click ticks
    # them (JZ count-in) and the start cue gets room before the first note. Shifts music+cues+
    # click together; cue stays anchored to its music bar.
    ci = int(mix.get("count_in", 0) or 0)
    if ci and not daw:
        lead = max(lead, ci * bar)
        print(f"count_in: forced +{ci} bar(s) of front count-in")
    OFF += lead
    if daw:                                        # render time == stem time (no offset/count-in);
        OFF = 0.0                                  # cue intro words before bar 1.1 get clipped
        print("daw_align: WAV time = stem (song) time, no count-in (drop at bar 1)")
    # cue grid base = the bar line where the stem downbeat (music bar 1.1) lands. NOT `lead`:
    # the earliest-sound fix above may have added whole bars to OFF (e.g. a stem starting
    # before its downbeat), and the cues must shift with the music, not stay on `lead`.
    cue_base = OFF + db0
    off_samp = round(OFF*SR)
    # trailing-silence trim: end on the last REAL sound (not the zero-padded stem length),
    # rounded up to a whole bar, + (tail_bars-1) extra bars. "tail_bars" (mix.json, default 1)
    # tunes the clean tail. The cue tail still holds 2 bars after the last cue so an "end" cue
    # isn't clipped. Strips Moises stem zero-padding so the click doesn't tick into dead air.
    tail_bars = int(mix.get("tail_bars", 1) or 1)
    # "cut_after_last_cue": N -> end the render N bars after the LAST cue event and drop the song's
    # tail past it (e.g. an 'end' cue where the band finishes and the recording's outro is unwanted).
    # N bars let the final hit ring; the output is faded at the cut so the hard stop doesn't click.
    # (true -> 2 bars.) Absent -> normal: extend to the last real sound, +2 bars of cue-tail room.
    cut = mix.get("cut_after_last_cue")
    cut_bars = (2.0 if cut is True else float(cut)) if (cut is not None and mix.get("cues")) else None
    if cut_bars is not None:
        last_ev = max(cue_event_time(c, cue_base, relt) for c in mix["cues"])
        end = int((last_ev + cut_bars*bar)*SR)
        print(f"cut: render ends {cut_bars:g} bar(s) after the last cue event — song tail dropped")
    else:
        end = max(last_sound(a) for a in srcs) + off_samp
        if mix.get("cues"):
            end = max(end, int((max(cue_event_time(c, cue_base, relt) for c in mix["cues"]) + 2*bar)*SR))
    total = int((np.ceil(end/(bar*SR)) + (tail_bars - 1))*bar*SR)
    print(f"timeline = stem {OFF:+.5f}s, length {total/SR:.3f}s = {total/SR/bar:.0f} bars "
          f"(tail {tail_bars}b, trailing silence trimmed)")

    # ---- cue position converter (writes nothing) -------------------------------------------------
    # Three coordinate systems a cue position gets read in — this maps between them:
    #   mix-bar   : mix.json "bar"/"beat". The MUSIC grid (bar 1.1 = stem downbeat). What you AUTHOR.
    #   render-s  : seconds into auto-render/*.wav (== "abs_sec" == Logic SMPTE of the loaded render).
    #   Logic-bar : bar.beat on Logic's OWN ruler when you drop the render in at bar1 = t=0 (constant
    #               song tempo). What the bar counter shows over the rendered click — OFFSET from
    #               mix-bar by the count-in lead (+ tempo-follow drift). DON'T author from this directly.
    # Queries:  --map            whole cue list in all three systems (see the constant lead offset)
    #           --logic B[.beat] a Logic-ruler spot  -> the mix.json "bar" to write
    #           --bar  N[.beat]  a mix.json bar       -> render sec + where it shows on Logic's ruler
    #           --at   SEC       a render/SMPTE second-> mix.json "bar"
    def idx_to_barbeat(i): i = int(round(i)); return i//4 + 1, i % 4 + 1
    def mixbar_to_idx(b, bt_=1): return 4*(int(b)-1) + (int(bt_)-1)
    def render_sec(i): return cue_base + relt(i)
    def sec_to_idx(t):                                  # inverse of render_sec (tempo-follow aware)
        if not follow: return (t - cue_base)/beat
        rel = t - cue_base
        if rel <= 0: return rel/beat
        span = bt - bt[0]
        if rel >= span[-1]: return (len(bt)-1) + (rel-span[-1])/beatB
        j = max(0, min(int(np.searchsorted(span, rel)) - 1, len(span)-2))
        return j + (rel - span[j])/(span[j+1]-span[j])
    def logic_of_sec(t): b = t/bar; return int(b)+1, (b-int(b))*4 + 1   # ruler: bar1=t=0, const tempo
    def sec_of_logic(bn, be=1): return ((bn-1) + (be-1)/4)*bar
    def report(t, src):
        mb, mbe = idx_to_barbeat(sec_to_idx(t)); lb, lbe = logic_of_sec(t)
        write = f'"bar": {mb}' if mbe == 1 else f'"bar": {mb}, "beat": {mbe}'
        print(f'  {src:>18} | render {t:8.3f}s | mix.json {{{write}}} | Logic ruler {lb}.{round(lbe)}')
    def _qval(flag): return sys.argv[sys.argv.index(flag)+1]
    q = False
    if "--map" in sys.argv:
        q = True
        print("cue map — mix.json bar  ->  render sec  ->  Logic ruler bar.beat:")
        for c in mix.get("cues", []):
            i = cue_beat_index(c); t = render_sec(i); lb, lbe = logic_of_sec(t)
            print(f"  bar {int(c['bar']):>3} beat {int(c.get('beat',1))} | {t:8.3f}s "
                  f"| Logic {lb}.{round(lbe)} | {c['text']}")
    for flag, mk in (("--logic", lambda v: sec_of_logic(int(v.split('.')[0]), int((v.split('.')+['1'])[1]))),
                     ("--bar",   lambda v: render_sec(mixbar_to_idx(int(v.split('.')[0]), int((v.split('.')+['1'])[1])))),
                     ("--at",    lambda v: float(v))):
        if flag in sys.argv:
            q = True; v = _qval(flag); report(mk(v), f"{flag[2:]} {v}")
    if q: return

    def mixdown(names, gains, mutes=None):
        mutes = mutes or {}                            # {stem: [[from_bar, to_bar], ...]}: silence the
        buf = np.zeros((total, 2), np.float32)         # stem from from_bar downbeat to to_bar downbeat
        for n in names:                                # (1-indexed bars, to_bar exclusive). Per-stem so
            g = 10**(gains.get(n, 0)/20)               # one stem can drop out of a section (e.g. backing
            if n in mutes:                             # vocals off in the verse) without touching others.
                sb = np.zeros((total, 2), np.float32)
                place(sb, audio[n]*g, off_samp)
                for fr, to in mutes[n]:                # fr/to in bars (fractional ok: 18.2 = bar18 beat1.8)
                    s0 = max(0, round((cue_base + relt((fr-1)*4))*SR))
                    s1 = min(total, round((cue_base + relt((to-1)*4))*SR))
                    if s1 > s0:
                        sb[s0:s1] = 0
                        f = int(0.015*SR)              # 15ms fade-in at the un-mute edge so a hard cut
                        if s1+f <= total:              # landing mid-note doesn't click
                            sb[s1:s1+f] *= np.linspace(0, 1, f)[:, None]
                buf += sb
            else:
                place(buf, audio[n]*g, off_samp)
        return buf

    if follow and external:                        # Moises: JZ-sample click ON the metronome's tempo map
        # (no clean click stem exists). A JamZone song HAS its real click — which already tracks the
        # recording's tempo exactly (Destination Calabria: raw click sits -63ms off the kick, std 3ms,
        # whole song) — so rebuilding it from samples on detected onsets only ADDS drift. JZ songs
        # (follow or not) therefore fall through to the real-click-stem branch below; the follow grid is
        # still used for CUE placement so cues sit on the real clicks.
        import jamzone_click as JC                 # natural JZ samples (full ~70ms decay) — same click
        jdb = JC.wav_read(JC.DB); jdb = jdb/(np.max(np.abs(jdb)) or 1)*0.95   # body as the JamZone-song
        jbt = JC.wav_read(JC.BT); jbt = jbt/(np.max(np.abs(jbt)) or 1)*0.95   # path. (Earlier a 22ms tail-
        # cut was applied to kill a perceived double-click, but that double was the zone-bridge flutter
        # — now skipped above — not the sample tail; clicks are >=333ms apart so tails never overlap.)
        cbuf = np.zeros((total, 2), np.float32)
        zz0, zz1 = finfo.get("z0"), finfo.get("z1")    # zone meter: accent every zacc whole beats
        zaf = finfo.get("accent_from", zz0)            # (downbeat) measured from zaf (= z0 unless the
        zacc = int(finfo.get("accent", 4))             # zone was extended back for a count-in, keeping
        zsub = int(finfo.get("subdiv", 1))             # the downbeats put). SUBDIVIDE each beat into zsub
        def put(t, h):                                 # time breakdown whose backbone hits on the 'and'
            s = round(t*SR)                            # gets a click on those sub-beats too
            if 0 <= s < total:
                n = min(len(h), total-s); cbuf[s:s+n, 0] += h[:n]; cbuf[s:s+n, 1] += h[:n]
        k = -(int(cue_base/beat) + 4)
        while True:
            t = cue_base + relt(k)
            if t*SR >= total: break
            inzone = zz0 is not None and zz0 <= k < zz1
            accent = (k - zaf) % zacc == 0 if inzone else k % 4 == 0
            dur = relt(k) - relt(k-1)                   # local beat length; the zone-exit linspace
            if dur >= 0.55*beat:                        # bridge fills a backward step with compressed
                put(t, jdb if accent else jbt*0.55)     # beats (60-85ms) that read as a fast flutter —
                                                        # skip those in EMISSION only (bt/relt untouched,
                                                        # so cues stay put); the handoff becomes one
                                                        # clean gap then the real 124 downbeat
            if inzone and zsub > 1 and k < zz1-1:      # sub-beat ticks inside the zone (quiet)
                for j in range(1, zsub):
                    put(cue_base + relt(k + j/zsub), jbt*0.35)
            k += 1
        if zz0 is not None:                            # ENTRY gap-fill: the slow anchor can sit a beat+
            t_pre = cue_base + relt(zz0-1)             # past the last 124 beat (the verse still plays
            t_zone = cue_base + relt(zz0)              # 124 into the break). Continue the 124 grid to its
            m = 1                                      # natural downbeats so the normal beat keeps its
            while t_pre + m*beat < t_zone - 0.30*beat: # 'one' instead of the slow grid swallowing it,
                kk = (zz0-1) + m                       # then the slow count-in starts clean after.
                put(t_pre + m*beat, jdb if kk % 4 == 0 else jbt*0.55)
                m += 1
        out = {"click": cbuf}
    elif external:                                 # built clean click, downbeat on every bar line
        out = {"click": build_click(60/beat, total, off_samp, bar)}
    else:                                           # JamZone: the click stem itself, aligned
        cbuf = np.zeros((total, 2), np.float32); place(cbuf, decode(stems[click_name]), off_samp)
        t0c = first_sound(cbuf)                     # added front bars (lead/offset) must tick too:
        if t0c and t0c > beat/2:                    # fill them with JZ samples, accent on bar
            import jamzone_click as JC              # lines, at the stem click's level
            jdb = JC.wav_read(JC.DB); jdb = jdb/(np.max(np.abs(jdb)) or 1)
            jbt = JC.wav_read(JC.BT); jbt = jbt/(np.max(np.abs(jbt)) or 1)
            g = float(np.abs(cbuf).max())
            for k in range(int(round(t0c/beat))):
                hit = (jdb if k % 4 == 0 else jbt*0.5)*g
                s = round(k*beat*SR); n = min(len(hit), total-s)
                cbuf[s:s+n, 0] += hit[:n]; cbuf[s:s+n, 1] += hit[:n]
            print(f"click: front {t0c/bar:.0f} bar(s) filled with JZ count-in")
        out = {"click": cbuf}
    replaced = {r for grp in pb_group_names(mix)              # a layer that RE-RECORDS a Moises stem
                for ent in (mix.get(grp) or {}).get("layers", []) if isinstance(ent, dict)
                for r in ent.get("replaces", [])}             # (live bass for studio bass) -> drop that
    out["all"] = mixdown([n for n in music if n not in replaced], {})   # stem from `all` so it isn't doubled
    if replaced: print(f"all: Moises stems replaced by a layer, excluded: {sorted(replaced)}")
    crep = None
    if mix.get("cues"):                            # authored bar/beat cue list (preferred)
        print(f"cue voice: {'ElevenLabs ' + ELEVEN_VOICE + ' (' + ELEVEN_MODEL + f'), stab {ELEVEN_STABILITY} style {ELEVEN_STYLE} speed {ELEVEN_SPEED}, counts spoken' if ELEVEN_KEY else 'macOS say ' + str(RU_VOICE) + ', counts = recorded clips'}")
        if ELEVEN_KEY and ELEVEN_PHRASE:           # pre-generate every cue block in ONE request so the
            _tag = f' <break time="{CUE_BREAK_S:.2f}s" /> '   # voice is identical across cues (not pitch-DSP'd)
            _blocks = []
            for _c in mix["cues"]:
                _t = _c["text"].strip(); _k = cue_kind(_t, _c.get("raw"))
                if _c.get("count") or _k == "stop": continue      # these use announcement + recorded counts
                _synth = [_apply_say_as(w) for w in cue_words(_t, _k)[1]]
                if any(" " in s for s in _synth): continue
                _b = _tag.join(_synth)
                if _b not in _blocks: _blocks.append(_b)
            _pregen_blocks(_blocks)
        out["cues"], crep = build_cues(mix["cues"], total, cue_base, relt, bdur, cue_subdiv, cue_step)
        print(f"cues: {len(crep)} spoken (in -> ready go; stop -> 'in 3' + 3-2-1 count; on grid); "
              f"cue grid bar 1.1 = music downbeat = {cue_base:.3f}s (stem downbeat {db0:.3f}s + OFF {OFF:.3f}s)")
        for b, be, ph, t in crep:
            print(f"  bar {b:>3}.{be}  {t:7.3f}s  {ph}")
    elif cue_st is not None:                        # fallback: prebuilt cue_track.wav (stem timeline)
        cues_buf = np.zeros((total, 2), np.float32); place(cues_buf, cue_st, off_samp)
        out["cues"] = cues_buf
    autoleveled = set()                                # groups carrying an auto-leveled (fx/back-vox)
    for grp in pb_group_names(mix):                    # stem/layer -> warn if headroom rescales them
        m = mix.get(grp)
        if not m: continue
        overrides, trims = m.get("roles", {}), (m.get("gain_db") or {})
        gstems = [s for s in m.get("stems", []) if s not in perc]   # percussion never in playback
        if len(gstems) != len(m.get("stems", [])):
            print(f"  {grp}: percussion auto-removed from playback: {[s for s in m.get('stems', []) if s in perc]}")
        eff = {}                                       # fx/back-vox auto-leveled to role target;
        for n in gstems:                               # gain_db = TRIM on top for those, ABSOLUTE
            role = classify(n, overrides)              # for musical (unchanged behavior)
            ag, loud = auto_gain_db(audio[n], role)
            trim = trims.get(n, 0)
            eff[n] = ag + trim
            if loud is not None: autoleveled.add(grp)
            if loud is not None:
                note = "" if ag < 0 else "  (under ceiling, unchanged)"
                tr = f" + trim {trim:+g}" if trim else ""
                print(f"  level {grp}/{n}: {role}  measured {loud:+.1f}dBFS vs ceiling "
                      f"{ROLE_CEILING[role]:+.0f}  gain {ag:+.1f}dB{tr} = {eff[n]:+.1f}dB{note}")
        out[grp] = mixdown(gstems, eff, m.get("mute"))

    semi = mix.get("pitch_semitones", 0)
    if semi:
        targets = [k for k in out if k not in ("click", "cues", "pb-drums")]
        print(f"pitch: {semi:+g} semitones (rubberband, tempo/grid preserved) on {', '.join(targets)}")
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as ex:
            futs = {n: ex.submit(pitch_shift, out[n], semi) for n in targets}
            for n, fut in futs.items():
                out[n] = fut.result()

    def load_layer(nm, start):                     # contributed part (parts/), ALWAYS in band key ->
        p = sorted(glob.glob(os.path.join(folder, "parts", nm + ".*")))[0]   # never pitched. `start` =
        a = decode(p); lbuf = np.zeros((total, 2), np.float32)                # render-sample where the
        s0 = max(0, start); a0 = max(0, -start)                               # file's t=0 lands.
        n = min(len(a) - a0, total - s0)
        if n > 0: lbuf[s0:s0+n] = a[a0:a0+n]
        return lbuf
    placed_layers = []                             # (name, placed band-key buffer) for practice minus
    for grp in pb_group_names(mix):                # layers added AFTER pitch (band key -> NEVER pitched),
        m = mix.get(grp)                           # BEFORE headroom (catch peaks); each folded into `all`.
        for ent in (m or {}).get("layers", []):    # entry: "name" (render-frame) | {file, frame, offset_ms}
            ent = ent if isinstance(ent, dict) else {"file": ent}
            nm, frame = ent["file"], ent.get("frame", "render")   # render-frame = cut vs auto-render
            base = off_samp if frame == "stem" else 0             # (placed at render t=0); stem-frame =
            start = base + round(ent.get("offset_ms", 0)/1000*SR) # cut vs Moises stems (native, placed at OFF)
            lbuf = load_layer(nm, start)               # fx/back-vox layers auto-leveled like stems;
            role = classify(nm, (m.get("roles") or {}))   # gain_db = trim for those, absolute for musical
            ag, loud = auto_gain_db(lbuf, role)
            if loud is not None: autoleveled.add(grp)
            trim = ent.get("gain_db", (m.get("gain_db", {}) or {}).get(nm, 0))
            lb = lbuf * 10**((ag + trim)/20)
            placed_layers.append((nm, lb))
            out[grp] = out.get(grp, np.zeros((total, 2), np.float32)) + lb
            out["all"] = out["all"] + lb
            lvl = (f", {role} measured {loud:+.1f}dBFS vs ceiling {ROLE_CEILING[role]:+.0f} gain {ag:+.1f}dB"
                   + (" (unchanged)" if ag == 0 else "")) if loud is not None else ""
            print(f"layer: {nm} -> {grp} + all ({frame}-frame @ {start/SR:+.3f}s, band key, no pitch{lvl})")

    for n, buf in out.items():                     # headroom: only ever attenuate
        pk = float(np.abs(buf).max())
        if pk > 0.99:
            buf *= 0.95/pk
            warn = "  ⚠ auto-leveled group rescaled — fx/back-vox now below ceiling in this song" \
                   if n in autoleveled else ""
            print(f"  {n}: peak {20*np.log10(pk):+.1f}dBFS -> normalized to -0.4dBFS{warn}")

    if cut_bars is not None:                        # soften the hard truncation so the dropped-tail
        fade = min(int(0.08*SR), total)             # cut ends on a clean ramp, not a click
        ramp = np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        for n in out:
            out[n][-fade:] *= ramp

    pre = 1000
    v = onsets(np.concatenate([np.zeros(pre, np.float32), out["click"].mean(1)])) - pre/SR
    ph0 = v[0] if daw else 0.0                      # daw_align: downbeat sits at stem db0, not on a
    eall = np.array([((t-ph0) - round((t-ph0)/beat)*beat)*1000 for t in v])   # each onset's spacing err
    # Grid health = the MEDIAN onset error (robust). A wrong bpm makes the error RAMP across the
    # song (median blows up -> caught); a clean click sits ~1ms; a jittery JZ click (Destination
    # Calabria, ~±15ms quantization noise) or a non-constant intro (Whenever Wherever's rubato
    # opening — a minority of onsets) leaves the median small, so neither false-fails. The first-8
    # spacing + downbeat bar-line are still reported for clean songs as before.
    med = float(np.median(np.abs(eall))); p90 = float(np.percentile(np.abs(eall), 90))
    bar_err = ((v[0]-ph0) - round((v[0]-ph0)/bar)*bar)*1000
    print(f"verify click: median err {med:.1f}ms (p90 {p90:.1f}ms), first onset {v[0]*1000:.1f}ms "
          f"(bar-line err {bar_err:+.1f}ms), beat err {[f'{e:+.1f}' for e in eall[:8]]} ms"
          + ("  [follow: err vs constant beat is the tracked drift, not a fault]" if follow else ""))
    if med > 8 and not follow:                      # gross drift / wrong bpm — cues would walk off.
        sys.exit("verification failed — nothing written")  # follow rebuilds click+cues ON the metronome's
                                                            # own map, so a non-zero constant-beat median IS
                                                            # the tracked tempo curve (correct by construction).
    if crep is not None:                            # write render-timeline abs_sec + snap back per cue.
        # snap = seek point for the web player = 1 bar before the cue's FIRST spoken word, so clicking
        # a cue replays the WHOLE spoken cue (title/announcement/count) and hears the event, not just
        # the event beat with the words already gone. Clamped to >=0 (start cue sits near t=0).
        snaps = [max(0.0, cue_first_word_time(c, cue_base, relt, bdur, cue_subdiv, cue_step) - bar)
                 for c in mix["cues"]]
        warn = write_cue_abs_times(mix_p, [t for *_, t in crep], snaps)
        print(warn if warn else f"✓ abs_sec+snap: {len(crep)} cues updated in {os.path.basename(folder)}/mix.json")
    if "--check" in sys.argv:
        print("✓ --check: grid green, mix.json abs_sec+snap updated, no audio written"); return

    adir = os.path.join(folder, "auto-render")
    os.makedirs(adir, exist_ok=True)
    bpm = 60/beat
    for n, buf in out.items():
        wav_tempo_write(os.path.join(adir, n + ".wav"), buf, bpm)  # ST + MainStage (tempo label)
    json.dump({"offset_sec": round(OFF, 6), "bar_sec": round(bar, 6), "bpm": round(60/beat, 4),
               "note": "add offset_sec to stem-timeline times (cues.json/structure.json); "
                       "t=0 = bar line; downbeat of stem grid on a bar line"},
              open(os.path.join(adir, "timeline.json"), "w"), indent=1)
    extra = ""
    if "cues" in out:                              # audition mix to approve cues (levels as in
        m = out["all"]*MIX_LVL + out["click"]*CLICK_LVL + out["cues"]*CUE_LVL   # jamzone_cues.py)
        pk = float(np.abs(m).max())
        if pk > 0.97: m *= 0.97/pk
        subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-b:a","192k",os.path.join(adir, "cue_preview.mp3")],
                       input=m.astype(np.float32).tobytes())
        extra = " + cue_preview.mp3"

    for grp in pb_group_names(mix):                # clean mp3 per playback group (pb-other, pb-bass, pb-drums)
        if grp not in out: continue                # for the web mixer bus and preview (never bake in click/cues)
        g = out[grp]
        pk = float(np.abs(g).max())
        if pk > 0.97: g = g * (0.97 / pk)
        subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-b:a","192k",os.path.join(adir, grp + ".mp3")],
                       input=g.astype(np.float32).tobytes())
        extra += f" + {grp}.mp3"

    stems_dir = os.path.join(adir, "stems")
    os.makedirs(stems_dir, exist_ok=True)
    cat_rules = [
        ("back_vox", r"back(ing)?.?vocals?|back.?vox"),
        ("vocal",    r"lead.?vocal|^vocals?$"),
        ("drums",    r"drum"),
        ("bass",     r"bass"),
        ("guitars",  r"guitar"),
        ("keys",     r"keys|piano|organ|synth|clav|rhodes|accord|vibe"),
    ]
    cat_map = {}
    for st in music:
        low = st.lower()
        matched = "other"
        for cid, pat in cat_rules:
            if re.search(pat, low):
                matched = cid
                break
        cat_map.setdefault(matched, []).append(st)

    def render_cat_stem(item):
        cid, st_list = item
        buf = mixdown([n for n in st_list if n not in replaced], {})
        if semi and cid != "drums": buf = pitch_shift(buf, semi)
        for lnm, lb in placed_layers:
            matched_l = "other"
            for cid_l, pat in cat_rules:
                if re.search(pat, lnm.lower()):
                    matched_l = cid_l
                    break
            if matched_l == cid:
                buf = buf + lb
        pk = float(np.abs(buf).max())
        if pk > 0.97: buf *= 0.97 / pk
        out_p = os.path.join(stems_dir, f"{cid}.mp3")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-b:a", "192k", out_p], input=buf.astype(np.float32).tobytes())

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as ex:
        list(ex.map(render_cat_stem, cat_map.items()))

    if "click" in out:
        c_pk = float(np.abs(out["click"]).max())
        c_buf = out["click"] * (0.97 / c_pk if c_pk > 0.97 else 1.0)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-b:a", "192k", os.path.join(stems_dir, "click.mp3")], input=c_buf.astype(np.float32).tobytes())
    if "cues" in out:
        cu_pk = float(np.abs(out["cues"]).max())
        cu_buf = out["cues"] * (0.97 / cu_pk if cu_pk > 0.97 else 1.0)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-b:a", "192k", os.path.join(stems_dir, "cues.mp3")], input=cu_buf.astype(np.float32).tobytes())
    extra += " + stems/"

    print(f"✓ auto-render/: {', '.join(n+'.wav' for n in out)} + timeline.json{extra}")

    if "--practice" in sys.argv:
        for who, owned in players.items():             # practice mix: all MINUS this member's stems,
            owned = set(owned)                          # pitched to band key, + click + cues (cue_preview
            minus = mixdown([n for n in music if n not in replaced and n not in owned], {})
            if semi: minus = pitch_shift(minus, semi)   # member plays in band key -> minus is pitched;
            for nm, lb in placed_layers:                # layers are already band-key (never pitched): add
                if nm not in owned: minus = minus + lb  # back the ones this member does NOT play live
            pm = minus*MIX_LVL + out["click"]*CLICK_LVL
            if "cues" in out: pm = pm + out["cues"]*CUE_LVL
            pk = float(np.abs(pm).max())
            if pk > 0.97: pm *= 0.97/pk
            subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                            "-b:a","192k",os.path.join(adir, f"practice-{who}.mp3")],
                           input=pm.astype(np.float32).tobytes())
            print(f"✓ auto-render/practice-{who}.mp3 (all minus {sorted(owned)} + click + cues)")

    # export_stems: individual stems in the SAME aligned/tempo-labelled format (one wav each),
    # e.g. to hand the synths to the keyboardist. Same offset/length/grid/key as the set above.
    exp = mix.get("export_stems") or []
    for nm in exp:
        if nm not in audio: sys.exit(f"export_stems: '{nm}' is not a (non-click) stem")
    if exp:
        sdir = os.path.join(adir, "synths"); os.makedirs(sdir, exist_ok=True)
        for nm in exp:
            buf = mixdown([nm], {})                     # aligned at off_samp, full length
            if semi: buf = pitch_shift(buf, semi)       # follow the band's key if transposed
            pk = float(np.abs(buf).max())
            if pk > 0.99: buf *= 0.95/pk
            wav_tempo_write(os.path.join(sdir, nm + ".wav"), buf, bpm)
        print(f"✓ auto-render/synths/: {', '.join(n+'.wav' for n in exp)}")

    # Keep the web dashboard in sync: web/songs.json is GENERATED from every mix.json by
    # setlist_dashboard.py, and the dashboard reads that file (not mix.json). A cue/stem edit only
    # reaches the page — text, timecodes, and the snap seek-target — once it's rebuilt, so a full
    # render refreshes it automatically. Set JZ_SKIP_SITE=1 in batch loops (rebuild once at the end).
    # Never fatal: a refresh failure must not sink an otherwise-good render.
    if not os.environ.get("JZ_SKIP_SITE"):
        dash = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "setlist_dashboard.py")
        try:
            r = subprocess.run([sys.executable, dash], capture_output=True, text=True)
            tail = next((l for l in reversed(r.stdout.strip().splitlines()) if l.strip()), "")
            print(f"✓ web/songs.json refreshed — {tail}" if r.returncode == 0
                  else f"  web/songs.json refresh skipped (setlist_dashboard exit {r.returncode})")
        except Exception as e:
            print(f"  web/songs.json refresh skipped ({e})")

if __name__ == "__main__":
    main()
