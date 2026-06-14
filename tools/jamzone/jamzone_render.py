#!/usr/bin/env python3
"""Render a song's playback set for Stage Traxx straight from the stems — no Logic.

Per-song manifest mix.json (in the song folder) says which stems go where:

    {
      "pb-other": {"stems": ["05_Synth_Bass", "06_Synth_Lead"], "gain_db": {"06_Synth_Lead": -2}},
      "pb-bass":  null,
      "pitch_semitones": -2          // optional: transpose playback to the band's key
    }

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
"""
import os, sys, glob, json, subprocess
import numpy as np

SR = 44100
SONGS = os.path.expanduser("~/projects/cherry-daddies/music/songs")
CLICK_LVL, MIX_LVL, CUE_LVL = 0.6, 0.85, 1.0   # cue_preview levels (same as jamzone_cues.py)

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
    k = np.round((on-on[0])/np.median(np.diff(on)))
    A = np.vstack([k, np.ones_like(k)]).T
    beat, phase = np.linalg.lstsq(A, on, rcond=None)[0]
    def dom_freq(t):
        s = click_mono[int(t*SR):int(t*SR)+int(0.08*SR)]
        S = np.abs(np.fft.rfft(s*np.hanning(len(s))))
        return np.fft.rfftfreq(len(s), 1/SR)[np.argmax(S)]
    freqs = np.array([dom_freq(t) for t in on[:4]])
    db0 = phase + int(np.argmax(freqs))*beat       # accent (~200Hz) = downbeat
    resid = np.abs(A@[beat, phase]-on)
    return beat, db0, float(resid.max()), len(on)

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

def build_follow_grid(met_mono, mix, beat):
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
        sb = 60.0/float(tz["bpm"])
        anchor = float(tz["anchor_sec"]) if "anchor_sec" in tz else on[0] + z0*beat
        ph_post = phase_at(z1, len(on)) if z1 < len(on)-1 else (on[0] - 0)  # 124 phase = music return
        bt = np.zeros(max(len(on), z1+1))
        for k in range(len(bt)):
            if   k < z0: bt[k] = on[0] + k*beat            # clean pre at true bpm, downbeat anchor
            elif k < z1: bt[k] = anchor + (k-z0)*sb        # clean slow zone, phase = real slow downbeat
            else:        bt[k] = ph_post + k*beat          # clean post at true bpm, phase-locked to music
        bt = np.maximum.accumulate(bt)                     # anchor may sit just before the pre-zone's
        #          last 124-beat (entry transition) -> keep bt non-decreasing so relt() can't go back
        info.update({"manual": True, "z0": z0, "z1": z1, "slowbpm": float(tz["bpm"]), "beatB": beat,
                     "accent": int(tz.get("accent", 4)), "subdiv": int(tz.get("subdiv", 1)),
                     "zone_t": (float(bt[z0]), float(bt[z1-1]))})
        return bt, beat, info
    core = np.where(d > beatA*1.15)[0]                    # auto: clearly-slow intervals (breakdown)
    bt = on.astype(float).copy()
    if len(core):
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

def _metric_clips(metric, beat):
    """clips for the counted block, as (clip, beats_before_event). Word i nominally lands on
    beat -(W-i). Speed-up is capped at `say -r 200` — faster is unintelligible; past that a
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
        if clip is None and len(fast)/SR - budget < 0.15*beat:  # small overflow: squeeze into the
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

def cue_kind(text):
    last = text.split()[-1].lower()
    return "stop" if last == "stop" else "in" if last == "in" else "plain"

def cue_words(text):
    """metered words of a cue + natural-pace intro. The counted block is the LAST 4 words
    ('<x> in ready go'); anything before it (the song title in the start cue) is announcement,
    spoken at natural speed as one phrase, ending just before the block — never squashed."""
    words = (text + " ready go" if cue_kind(text) == "in" else text).split()
    return (" ".join(words[:-4]), words[-4:]) if len(words) > 4 else ("", words)

INTRO_GAP = 0.12                                          # breath between intro and the block
def cue_first_word_time(c, base, relt, bdur):
    """earliest sound of a cue (used to size the front lead so nothing clips off the front)."""
    text = c["text"].strip(); i = cue_beat_index(c)
    if cue_kind(text) == "stop" or c.get("count"):
        return base + relt(i - 5)                         # ~announcement + 3-2-1 count
    intro, metric = cue_words(text)
    nb0 = _metric_clips(metric, bdur(i))[0][1]
    t0 = base + relt(i - nb0)
    if intro:
        clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
        return t0 - INTRO_GAP - len(clip)/SR
    return t0

def _put(buf, clip, t):
    s = int(t*SR); a0 = max(0, -s); s = max(0, s); n = min(len(clip)-a0, len(buf)-s)
    if n > 0: buf[s:s+n, 0] += clip[a0:a0+n]; buf[s:s+n, 1] += clip[a0:a0+n]

def build_cues(cue_list, total, base, relt, bdur):
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
        text = c["text"].strip(); kind = cue_kind(text); counted = bool(c.get("count"))
        i = cue_beat_index(c); t_event = base + relt(i)   # band event here (silent in cue track)
        voice = RU_VOICE if _cyrillic(text) else EN_VOICE
        if kind == "stop" or counted:
            for d, k in (("3", 3), ("2", 2), ("1", 1)):   # count on event-3 / -2 / -1
                clip = _load_clip(COUNT_FILES[d])
                _put(buf, clip, base + relt(i - k) - _vowel_onset(clip))
            ann_text = text.replace("-", " ") + (" in 3" if kind == "stop" else " 3")
            ann = _say(ann_text, voice)                   # announcement finishes before the count
            _put(buf, ann, (base + relt(i - 3)) - 0.35 - len(ann)/SR)
            phrase = ann_text + " · 3 2 1"
        else:
            intro, metric = cue_words(text)
            clips = _metric_clips(metric, bdur(i))        # last word on the beat BEFORE the event
            if intro:                                     # title etc: natural pace, right-aligned
                clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
                _put(buf, clip, base + relt(i - clips[0][1]) - INTRO_GAP - len(clip)/SR)
            for (clip, nb), w in zip(clips, metric):
                _put(buf, clip, base + relt(i - nb) - _vowel_onset(clip))
            ext = clips[0][1] - len(metric)
            phrase = (intro + " · " if intro else "") + " ".join(metric) \
                     + (f"  [{metric[0]} {1+ext} доли]" if ext else "")
        rep.append((int(c["bar"]), int(c.get("beat", 1)), phrase, t_event))
    return buf, rep

def main():
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
        for nm in ((mix.get(grp) or {}).get("stems", [])):
            if nm not in stems: sys.exit(f"mix.json: unknown stem '{nm}' in {grp}")

    click_st = decode(stems[click_name])
    beat, db0, resid, n_on = fit_grid(click_st.mean(1))  # fit_grid uses lstsq = span-average
    if external:
        db0 = float(onsets(click_st.mean(1))[0])  # first click = downbeat (user-specified)
    bpm_set = mix.get("bpm") or bpm_force         # song's locked constant tempo (mix.json > --bpm)
    if bpm_set: beat = 60.0/bpm_set
    bar = 4*beat
    follow = external and mix.get("click") == "follow"   # track a real mid-song tempo change
    if follow:
        bt, beatB, finfo = build_follow_grid(click_st.mean(1), mix, beat)
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
    tag = (f" (tempo-follow: {finfo['n']} onsets, zone {finfo['zone_t'][0]:.1f}-{finfo['zone_t'][1]:.1f}s "
           f"@~{finfo['slowbpm']:.0f}bpm, re-locked after)" if follow and "zone_t" in finfo
           else " (built clean click; Moises tempo ~constant)" if external else "")
    print(f"grid: beat={beat:.6f}s bpm={60/beat:.4f} bar={bar:.6f}s "
          f"downbeat={db0:.4f}s ({n_on} clicks, max resid {resid*1000:.1f}ms){tag}")

    music = [n for n in stems if n != click_name]
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
        min_word = min(cue_first_word_time(c, OFF + db0, relt, bdur) for c in mix["cues"])  # song
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

    def mixdown(names, gains):
        buf = np.zeros((total, 2), np.float32)
        for n in names:
            g = 10**(gains.get(n, 0)/20)
            place(buf, audio[n]*g, off_samp)
        return buf

    if follow:                                     # JZ-sample click ON the metronome's tempo map
        import jamzone_click as JC
        jdb = JC.wav_read(JC.DB); jdb = jdb/(np.max(np.abs(jdb)) or 1)*0.95
        jbt = JC.wav_read(JC.BT); jbt = jbt/(np.max(np.abs(jbt)) or 1)*0.95
        cbuf = np.zeros((total, 2), np.float32)
        zz0, zz1 = finfo.get("z0"), finfo.get("z1")    # zone meter: accent every zacc whole beats
        zacc = int(finfo.get("accent", 4))             # (downbeat), and SUBDIVIDE each beat into zsub
        zsub = int(finfo.get("subdiv", 1))             # ticks (e.g. 2 -> 8ths) so a syncopated half-
        def put(t, h):                                 # time breakdown whose backbone hits on the 'and'
            s = round(t*SR)                            # gets a click on those sub-beats too
            if 0 <= s < total:
                n = min(len(h), total-s); cbuf[s:s+n, 0] += h[:n]; cbuf[s:s+n, 1] += h[:n]
        k = -(int(cue_base/beat) + 4)
        while True:
            t = cue_base + relt(k)
            if t*SR >= total: break
            inzone = zz0 is not None and zz0 <= k < zz1
            accent = (k - zz0) % zacc == 0 if inzone else k % 4 == 0
            put(t, jdb if accent else jbt*0.55)        # whole beat: downbeat loud, others medium
            if inzone and zsub > 1 and k < zz1-1:      # sub-beat ticks inside the zone (quiet)
                for j in range(1, zsub):
                    put(cue_base + relt(k + j/zsub), jbt*0.35)
            k += 1
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
    out["all"] = mixdown(music, {})
    if mix.get("cues"):                            # authored bar/beat cue list (preferred)
        out["cues"], crep = build_cues(mix["cues"], total, cue_base, relt, bdur)
        print(f"cues: {len(crep)} spoken (in -> ready go; stop -> 'in 3' + 3-2-1 count; on grid); "
              f"cue grid bar 1.1 = music downbeat = {cue_base:.3f}s (stem downbeat {db0:.3f}s + OFF {OFF:.3f}s)")
        for b, be, ph, t in crep:
            print(f"  bar {b:>3}.{be}  {t:7.3f}s  {ph}")
    elif cue_st is not None:                        # fallback: prebuilt cue_track.wav (stem timeline)
        cues_buf = np.zeros((total, 2), np.float32); place(cues_buf, cue_st, off_samp)
        out["cues"] = cues_buf
    for grp in ("pb-other", "pb-bass"):
        m = mix.get(grp)
        if m: out[grp] = mixdown(m["stems"], m.get("gain_db", {}))

    semi = mix.get("pitch_semitones", 0)           # band's key vs original (e.g. -2)
    if semi:
        targets = [k for k in out if k not in ("click", "cues")]   # voice/click never pitched
        print(f"pitch: {semi:+g} semitones (rubberband, tempo/grid preserved) on {', '.join(targets)}")
        for n in targets:
            out[n] = pitch_shift(out[n], semi)

    for n, buf in out.items():                     # headroom: only ever attenuate
        pk = float(np.abs(buf).max())
        if pk > 0.99:
            buf *= 0.95/pk
            print(f"  {n}: peak {20*np.log10(pk):+.1f}dBFS -> normalized to -0.4dBFS")

    pre = 1000
    v = onsets(np.concatenate([np.zeros(pre, np.float32), out["click"].mean(1)])) - pre/SR
    ph0 = v[0] if daw else 0.0                      # daw_align: downbeat sits at stem db0, not on a
    err = [((t-ph0) - round((t-ph0)/beat)*beat)*1000 for t in v[:8]]   # bar line — check spacing
    bar_err = ((v[0]-ph0) - round((v[0]-ph0)/bar)*bar)*1000            # relative to the first onset
    print(f"verify click: first onset {v[0]*1000:.1f}ms (bar-line err {bar_err:+.1f}ms), "
          f"beat err {[f'{e:+.1f}' for e in err]} ms")
    if abs(bar_err) > 10 or max(abs(e) for e in err) > 3:
        sys.exit("verification failed — nothing written")
    if "--check" in sys.argv:
        print("✓ --check: all green, nothing written"); return

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
