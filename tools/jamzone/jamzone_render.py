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
CLICK_LVL, MIX_LVL, CUE_LVL = 0.6, 0.85, 1.0   # cue_preview levels (same as jamzone_cues.py)

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
        for grp in ("pb-other", "pb-bass"):
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

def place(buf, audio, at_samp):
    s0 = max(0, at_samp); a0 = max(0, -at_samp)
    n = min(len(audio)-a0, len(buf)-s0)
    if n > 0: buf[s0:s0+n] += audio[a0:a0+n]

def pitch_shift(buf, semitones):
    """Shift pitch by `semitones` (negative = down) preserving tempo, so the
    grid/alignment is untouched. Uses the rubberband CLI R3 engine (`-3`) with
    formant preservation — the ffmpeg rubberband FILTER (R2) mis-shifts pitch
    (asking -2 yields ~-1.4st), the CLI is accurate. float-wav temps avoid
    clipping (mix may exceed 0dBFS before the later headroom step). Length is
    pinned to input (rubberband may emit ±a few samples) to keep bar lines exact."""
    if not semitones: return buf
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fin, fout = os.path.join(d, "in.wav"), os.path.join(d, "out.wav")
        subprocess.run(["ffmpeg","-v","quiet","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                        "-c:a","pcm_f32le",fin], input=buf.astype(np.float32).tobytes())
        subprocess.run(["rubberband","-3","-F","-p",str(semitones),fin,fout], capture_output=True)
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",fout,"-f","f32le","-ac","2","-ar",str(SR),"-"],
                             capture_output=True).stdout
    y = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
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
def _say(text, voice, rate=None):
    import hashlib, tempfile
    key = hashlib.md5(f"{voice}|{rate}|{text}".encode()).hexdigest()
    if key in _SAY_CACHE: return _SAY_CACHE[key]
    with tempfile.TemporaryDirectory() as d:
        aiff = os.path.join(d, "s.aiff")
        cmd = ["say"] + (["-v", voice] if voice else []) + (["-r", str(rate)] if rate else []) \
              + ["-o", aiff, text]
        subprocess.run(cmd, check=True)
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",aiff,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                             capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    nz = np.where(np.abs(x) > 0.005)[0]              # drop synth tail silence (it spills into the
    if len(nz): x = x[:nz[-1] + int(0.02*SR)]        # next word's slot check otherwise)
    x = x/(np.max(np.abs(x)) or 1)*0.9
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

def _metric_clips(metric, beat, squeeze=False):
    """clips for the counted block, as (clip, beats_before_event). Word i nominally lands on
    beat -(W-i). squeeze=True (fast breakdown cues) ALWAYS atempo-fits each word into its one
    slot — 'rushed' is acceptable when the slot is a fast subdiv tick and there's no room to
    spread. Speed-up is capped at `say -r 200` — faster is unintelligible; past that a
    small overflow (<0.15 beat) is squeezed into the slot by atempo (inaudible at such factors,
    e.g. solo/sax ~1.05x). A word overflowing MORE STARTS whole beats earlier and spans them at
    natural pace (first word only — the slot before it is free; e.g. instrumental, arpegiator,
    bass-n-beat): squeezing a long word into one beat sounds rushed, an empty added beat sounds
    dead, so the 0.15-beat line splits the two. Natural pace wins when it needs no more extra
    beats than the sped-up take."""
    W = len(metric); out = []
    for i, w in enumerate(metric):
        v = RU_VOICE if _cyrillic(w) else EN_VOICE
        budget = 0.92*beat
        nat, fast = _say(w, v), _say(w, v, 200)
        clip = next((c for c in (nat, fast) if len(c)/SR <= budget), None); extra = 0
        if clip is None and squeeze:                            # fast cue: force into the one tick slot
            clip = _atempo(fast, (len(fast)/SR)/budget)
        elif clip is None and len(fast)/SR - budget < 0.15*beat:  # small overflow: squeeze into the
            clip = _atempo(fast, (len(fast)/SR)/budget)         # slot — a whole added beat would
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

COUNT_FILES = {"3": "~/3.aiff", "2": "~/2.aiff", "1": "~/1.aiff"}
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
    """metered words of a cue + natural-pace intro. The counted block is the LAST 4 words
    ('<x> in ready go'); anything before it (the song title in the start cue) is announcement,
    spoken at natural speed as one phrase, ending just before the block — never squashed."""
    words = (text + " ready go" if kind == "in" else text).split()
    return (" ".join(words[:-4]), words[-4:]) if len(words) > 4 else ("", words)

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

def _chord_clip(notes, dur_s, level=0.5):
    """Soft synth triad for an in-ear pitch reference (authored directly in the BAND key — the
    cue track is never pitch-shifted). Sine + two quiet harmonics, gentle attack and a long
    cosine release so it rings like a pad, not a beep."""
    n = int(dur_s*SR); t = np.arange(n)/SR; y = np.zeros(n)
    for nm in notes:
        f = _note_hz(nm)
        for h, a in ((1, 1.0), (2, 0.35), (3, 0.15)):
            y += a*np.sin(2*np.pi*f*h*t)
    env = np.ones(n); at = int(0.015*SR); rl = int(min(0.55, dur_s*0.55)*SR)
    env[:at] = np.linspace(0, 1, at)
    env[-rl:] = np.cos(np.linspace(0, np.pi/2, rl))       # smooth fade to 0 (no click into the block)
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
                clip = _load_clip(COUNT_FILES[d])
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

def write_cue_abs_times(mix_path, times):
    """Refresh "abs_sec" (render-timeline event seconds, what you hear in auto-render/cue_preview)
    on each cue in mix.json, IN PLACE. Edits the raw text line-by-line — never re-serializes the
    whole file — so hand-formatting (column alignment, field order, one cue per line) is preserved
    byte-for-byte. Idempotent: an existing abs_sec is stripped and rewritten. times[k] = the k-th
    cue's render event time, in file order. Cue lines are matched by carrying both "bar" and "text"
    ("from_bar"/"to_bar" in tempo_zone never match — no surrounding quotes on `bar`, and no "text").
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
        body = re.sub(r',\s*"abs_sec"\s*:\s*[-0-9.]+', "", ln)   # drop any prior abs_sec
        idx = body.rfind("}")                                    # insert before the cue's closing brace
        t = round(times[k], 3); k += 1
        lines[j] = body[:idx].rstrip() + f', "abs_sec": {t}' + body[idx:]
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

    for grp in ("pb-other", "pb-bass"):
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
    OFF += lead
    if daw:                                        # render time == stem time (no offset/count-in);
        OFF = 0.0                                  # cue intro words before bar 1.1 get clipped
        print("daw_align: WAV time = stem (song) time, no count-in (drop at bar 1)")
    # cue grid base = the bar line where the stem downbeat (music bar 1.1) lands. NOT `lead`:
    # the earliest-sound fix above may have added whole bars to OFF (e.g. a stem starting
    # before its downbeat), and the cues must shift with the music, not stay on `lead`.
    cue_base = OFF + db0
    off_samp = round(OFF*SR)
    end = max(len(a) for a in srcs) + off_samp
    if mix.get("cues"):
        end = max(end, int((max(cue_event_time(c, cue_base, relt) for c in mix["cues"]) + 2*bar)*SR))
    total = int(np.ceil(end/(bar*SR))*bar*SR)
    print(f"timeline = stem {OFF:+.5f}s, length {total/SR:.3f}s = {total/SR/bar:.0f} bars")

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
    replaced = {r for grp in ("pb-other", "pb-bass")          # a layer that RE-RECORDS a Moises stem
                for ent in (mix.get(grp) or {}).get("layers", []) if isinstance(ent, dict)
                for r in ent.get("replaces", [])}             # (live bass for studio bass) -> drop that
    out["all"] = mixdown([n for n in music if n not in replaced], {})   # stem from `all` so it isn't doubled
    if replaced: print(f"all: Moises stems replaced by a layer, excluded: {sorted(replaced)}")
    crep = None
    if mix.get("cues"):                            # authored bar/beat cue list (preferred)
        out["cues"], crep = build_cues(mix["cues"], total, cue_base, relt, bdur, cue_subdiv, cue_step)
        print(f"cues: {len(crep)} spoken (in -> ready go; stop -> 'in 3' + 3-2-1 count; on grid); "
              f"cue grid bar 1.1 = music downbeat = {cue_base:.3f}s (stem downbeat {db0:.3f}s + OFF {OFF:.3f}s)")
        for b, be, ph, t in crep:
            print(f"  bar {b:>3}.{be}  {t:7.3f}s  {ph}")
    elif cue_st is not None:                        # fallback: prebuilt cue_track.wav (stem timeline)
        cues_buf = np.zeros((total, 2), np.float32); place(cues_buf, cue_st, off_samp)
        out["cues"] = cues_buf
    autoleveled = set()                                # groups carrying an auto-leveled (fx/back-vox)
    for grp in ("pb-other", "pb-bass"):                # stem/layer -> warn if headroom rescales them
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

    semi = mix.get("pitch_semitones", 0)           # band's key vs original (e.g. -2)
    if semi:
        targets = [k for k in out if k not in ("click", "cues")]   # voice/click never pitched
        print(f"pitch: {semi:+g} semitones (rubberband, tempo/grid preserved) on {', '.join(targets)}")
        for n in targets:
            out[n] = pitch_shift(out[n], semi)

    def load_layer(nm, start):                     # contributed part (parts/), ALWAYS in band key ->
        p = sorted(glob.glob(os.path.join(folder, "parts", nm + ".*")))[0]   # never pitched. `start` =
        a = decode(p); lbuf = np.zeros((total, 2), np.float32)                # render-sample where the
        s0 = max(0, start); a0 = max(0, -start)                               # file's t=0 lands.
        n = min(len(a) - a0, total - s0)
        if n > 0: lbuf[s0:s0+n] = a[a0:a0+n]
        return lbuf
    placed_layers = []                             # (name, placed band-key buffer) for practice minus
    for grp in ("pb-other", "pb-bass"):            # layers added AFTER pitch (band key -> NEVER pitched),
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
    if crep is not None:                            # write render-timeline abs_sec back onto each cue
        warn = write_cue_abs_times(mix_p, [t for *_, t in crep])
        print(warn if warn else f"✓ abs_sec: {len(crep)} cues updated in {os.path.basename(folder)}/mix.json")
    if "--check" in sys.argv:
        print("✓ --check: grid green, mix.json abs_sec updated, no audio written"); return

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
    print(f"✓ auto-render/: {', '.join(n+'.wav' for n in out)} + timeline.json{extra}")

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

if __name__ == "__main__":
    main()
