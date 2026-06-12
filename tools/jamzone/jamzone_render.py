#!/usr/bin/env python3
"""Render a song's playback set for Stage Traxx straight from the stems — no Logic.

Per-song manifest mix.json (in the song folder) says which stems go where:

    {
      "pb-other": {"stems": ["05_Synth_Bass", "06_Synth_Lead"], "gain_db": {"06_Synth_Lead": -2}},
      "pb-bass":  null,
      "pitch_semitones": -2          // optional: transpose playback to the band's key
    }

click and cues need no manifest: click = the JamZone Click stem, cues = cue_track.wav.
all = every music stem (preview mix). Outputs land in <song>/auto-render/ as WAV,
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
def _say(text, voice):
    import hashlib, tempfile
    key = hashlib.md5(f"{voice}|{text}".encode()).hexdigest()
    if key in _SAY_CACHE: return _SAY_CACHE[key]
    with tempfile.TemporaryDirectory() as d:
        aiff = os.path.join(d, "s.aiff")
        cmd = ["say"] + (["-v", voice] if voice else []) + ["-o", aiff, text]
        subprocess.run(cmd, check=True)
        raw = subprocess.run(["ffmpeg","-v","quiet","-i",aiff,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                             capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    x = x/(np.max(np.abs(x)) or 1)*0.9
    _SAY_CACHE[key] = x; return x

def _vowel_onset(x):
    """time of the first 0.02s window whose RMS > 0.4*peak (the spoken vowel) — so the word
    lands its stressed onset, not its leading silence, on the beat."""
    w = int(0.02*SR)
    if len(x) < w: return 0.0
    env = np.array([np.sqrt((x[i:i+w]**2).mean()) for i in range(0, len(x)-w, w//2)])
    if not len(env): return 0.0
    return int(np.argmax(env > 0.4*env.max()))*(w//2)/SR

def expand_cue(text):
    """'<x> in' -> '<x> in ready go', '<x> stop' -> '<x> stop ready stop', else unchanged."""
    last = text.split()[-1].lower()
    return text + (" ready go" if last == "in" else " ready stop" if last == "stop" else "")

def cue_event_time(c, bar, beat, lead):
    return lead + (int(c["bar"])-1)*bar + (int(c.get("beat", 1))-1)*beat

def cue_first_word_time(c, bar, beat, lead):
    """earliest spoken-word beat of a cue (used to size the front lead so nothing clips)."""
    W = len(expand_cue(c["text"].strip()).split())
    return cue_event_time(c, bar, beat, lead) - W*beat

def build_cues(cue_list, total, bar, beat, lead):
    """Spoken cues on the render grid. Event time = the marked Logic bar/beat (+lead); the
    instrument enters ON that beat, so the phrase's LAST word ('go'/'stop') lands the beat
    BEFORE it and earlier words on the beats before that (metered count). Russian words use a
    Russian voice, others the default."""
    import re
    buf = np.zeros((total, 2), np.float32)
    rep = []
    for c in cue_list:
        words = expand_cue(c["text"].strip()).split(); W = len(words)
        t_event = cue_event_time(c, bar, beat, lead)      # instrument enters here (no word on it)
        for i, w in enumerate(words):
            clip = _say(w, RU_VOICE if re.search("[а-яёА-ЯЁ]", w) else EN_VOICE)
            s = int((t_event - (W-i)*beat - _vowel_onset(clip))*SR)   # last word on t_event-beat
            a0 = max(0, -s); s = max(0, s); n = min(len(clip)-a0, total-s)
            if n > 0: buf[s:s+n, 0] += clip[a0:a0+n]; buf[s:s+n, 1] += clip[a0:a0+n]
        rep.append((int(c["bar"]), int(c.get("beat", 1)), " ".join(words), t_event))
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
        print(f"cues: {len(crep)} spoken (ready-go/ready-stop, metered to grid)")
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
    print(f"✓ auto-render/: {', '.join(n+'.wav' for n in out)} + timeline.json")

if __name__ == "__main__":
    main()
