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
    beat -(W-i). Speed-up is capped at `say -r 250` — faster is unintelligible; past that a
    small overflow (<0.3 beat) is squeezed into the slot by atempo (inaudible at such factors).
    A word still longer STARTS whole beats earlier and spans them (first word only — the
    slot before it is free; e.g. arpegiator, more-arpegiator, bass-n-beat). Natural pace wins
    when it needs no more extra beats than the sped-up take."""
    W = len(metric); out = []
    for i, w in enumerate(metric):
        v = RU_VOICE if _cyrillic(w) else EN_VOICE
        budget = 0.92*beat
        nat, fast = _say(w, v), _say(w, v, 250)
        clip = next((c for c in (nat, fast) if len(c)/SR <= budget), None); extra = 0
        if clip is None and len(fast)/SR - budget < 0.3*beat:   # small overflow: squeeze into the
            clip = _atempo(fast, (len(fast)/SR)/budget)         # slot — a whole added beat would
        elif clip is None and i == 0:                           # sit mostly empty (solo: +19ms)
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

def cue_event_time(c, bar, beat, lead):
    return lead + (int(c["bar"])-1)*bar + (int(c.get("beat", 1))-1)*beat

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
def cue_first_word_time(c, bar, beat, lead):
    """earliest sound of a cue (used to size the front lead so nothing clips off the front)."""
    text = c["text"].strip(); te = cue_event_time(c, bar, beat, lead)
    if cue_kind(text) == "stop":
        return te - 5*beat                                # ~announcement + 3-2-1 count
    intro, metric = cue_words(text)
    t0 = te - _metric_clips(metric, beat)[0][1]*beat
    if intro:
        clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
        return t0 - INTRO_GAP - len(clip)/SR
    return t0

def _put(buf, clip, t):
    s = int(t*SR); a0 = max(0, -s); s = max(0, s); n = min(len(clip)-a0, len(buf)-s)
    if n > 0: buf[s:s+n, 0] += clip[a0:a0+n]; buf[s:s+n, 1] += clip[a0:a0+n]

def build_cues(cue_list, total, bar, beat, lead):
    """Spoken cues on the render grid. Event time = the marked Logic bar/beat (+lead); the band
    plays/stops ON that beat (no word on it). Two styles by trailing keyword:
      '<x> in'   -> '<x> in ready go', metered: last word 'go' on the beat BEFORE the event.
      '<x> stop' -> announce '<x> stop in 3', then count 3-2-1 on the three beats before the stop.
    Russian words use a Russian voice; counts use the lifted count clips (~/3,2,1.aiff)."""
    buf = np.zeros((total, 2), np.float32)
    rep = []
    for c in cue_list:
        text = c["text"].strip(); kind = cue_kind(text)
        t_event = cue_event_time(c, bar, beat, lead)      # band event here (silent in cue track)
        voice = RU_VOICE if _cyrillic(text) else EN_VOICE
        if kind == "stop":
            for d, k in (("3", 3), ("2", 2), ("1", 1)):   # count on event-3 / -2 / -1
                clip = _load_clip(COUNT_FILES[d])
                _put(buf, clip, t_event - k*beat - _vowel_onset(clip))
            ann = _say(text + " in 3", voice)             # announcement finishes before the count
            _put(buf, ann, (t_event - 3*beat) - 0.35 - len(ann)/SR)
            phrase = text + " in 3 · 3 2 1"
        else:
            intro, metric = cue_words(text)
            clips = _metric_clips(metric, beat)           # last word on the beat BEFORE the event
            if intro:                                     # title etc: natural pace, right-aligned
                clip = _say(intro, RU_VOICE if _cyrillic(intro) else EN_VOICE)
                _put(buf, clip, t_event - clips[0][1]*beat - INTRO_GAP - len(clip)/SR)
            for (clip, nb), w in zip(clips, metric):
                _put(buf, clip, t_event - nb*beat - _vowel_onset(clip))
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
        stems = {os.path.basename(p)[:-4]: p
                 for p in sorted(glob.glob(os.path.join(folder, "*.mp3")) +
                                 glob.glob(os.path.join(folder, "*.wav")))}
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
    tag = " (built clean click; Moises tempo ~constant)" if external else ""
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
    lead = 0.0
    if mix.get("cues"):
        min_word = min(cue_first_word_time(c, bar, beat, 0.0) for c in mix["cues"])
        if min_word < 0.30:                        # 0.30s room for the first word's onset
            lead = np.ceil((0.30 - min_word)/bar)*bar
            print(f"lead: +{lead/bar:.0f} bar(s) so the longest cue fits the front")
    OFF += lead
    off_samp = round(OFF*SR)
    end = max(len(a) for a in srcs) + off_samp
    if mix.get("cues"):
        end = max(end, int((max(cue_event_time(c, bar, beat, lead) for c in mix["cues"]) + 2*bar)*SR))
    total = int(np.ceil(end/(bar*SR))*bar*SR)
    print(f"timeline = stem {OFF:+.5f}s, length {total/SR:.3f}s = {total/SR/bar:.0f} bars")

    def mixdown(names, gains):
        buf = np.zeros((total, 2), np.float32)
        for n in names:
            g = 10**(gains.get(n, 0)/20)
            place(buf, audio[n]*g, off_samp)
        return buf

    if external:                                   # built clean click, downbeat on every bar line
        out = {"click": build_click(60/beat, total, off_samp, bar)}
    else:                                           # JamZone: the click stem itself, aligned
        cbuf = np.zeros((total, 2), np.float32); place(cbuf, decode(stems[click_name]), off_samp)
        out = {"click": cbuf}
    out["all"] = mixdown(music, {})
    if mix.get("cues"):                            # authored bar/beat cue list (preferred)
        out["cues"], crep = build_cues(mix["cues"], total, bar, beat, lead)
        print(f"cues: {len(crep)} spoken (in -> ready go; stop -> 'in 3' + 3-2-1 count; on grid)")
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
    err = [(t - round(t/beat)*beat)*1000 for t in v[:8]]
    bar_err = (v[0] - round(v[0]/bar)*bar)*1000
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
