#!/usr/bin/env python3
"""Fast cue-voice bench. Approach: NATURAL speech with real pauses between words, done as ONE
ElevenLabs generation using <break> tags — consistent tone (single gen), genuine inter-word
pauses, nothing sliced. The phrase is anchored so the last word ('go') lands on the beat before
the event. Short click bed (no long intro): ~0.25s pre-roll, click ticks only around the phrase.

Each cue -> web/cue-lab/<slug>_nat.mp3. Usage: CUE_TTS_VOICE=... python3 tools/jamzone/cue_lab.py [bpm] [break_s]
"""
import os, sys, subprocess, re
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jamzone_render as R
import jamzone_click as JC

SR = R.SR
BPM = float(sys.argv[1]) if len(sys.argv) > 1 else 140.0
BREAK_S = float(sys.argv[2]) if len(sys.argv) > 2 else 0.22
BEAT = 60.0/BPM
OUT = os.path.expanduser("~/projects/cherry-daddies/web/cue-lab")
CUES = ["drums in", "synth in", "all in ready go",
        "drums bass break ready go", "vocal-and-synth-only ready go"]

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:32]

def break_text(words, br):
    tag = f' <break time="{br:.2f}s" /> '
    return tag.join(words)

def synth_natural(text):
    """one generation of the whole phrase WITH <break> pauses between words -> mono f32 @SR."""
    kind = R.cue_kind(text)
    full = (text + " ready go") if kind == "in" else text
    words = [R._apply_say_as(w) for w in full.split()]
    tagged = break_text(words, BREAK_S)
    return R._eleven_tts(tagged, R.ELEVEN_SPEED)     # cached; break tags = real pauses, not spoken

def voiced_segments(x, thr_ratio=0.08, min_run=0.04, min_gap=0.06):
    """[(start,end)] sample spans of voiced runs (the <break> silences separate words cleanly)."""
    w = max(1, int(0.01*SR))
    env = np.sqrt(np.convolve(x**2, np.ones(w)/w, mode="same"))
    voiced = env > thr_ratio*env.max()
    segs = []; i = 0; n = len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]: j += 1
            segs.append([i, j]); i = j
        else:
            i += 1
    # merge runs separated by < min_gap; drop runs shorter than min_run
    merged = []
    for s in segs:
        if merged and (s[0]-merged[-1][1]) < int(min_gap*SR): merged[-1][1] = s[1]
        else: merged.append(s)
    return [(a, b) for a, b in merged if (b-a) >= int(min_run*SR)]

def click_aligned(total, event_t):
    """jz click every beat, phase-locked so event_t is an accented downbeat."""
    jdb = JC.wav_read(JC.DB); jdb = jdb/(np.max(np.abs(jdb)) or 1)*0.95
    jbt = JC.wav_read(JC.BT); jbt = jbt/(np.max(np.abs(jbt)) or 1)*0.95
    o = np.zeros((total, 2), np.float32)
    j0 = int(np.floor(event_t/BEAT)) + 4
    for j in range(-j0, j0+8):
        t = event_t + j*BEAT
        s = int(round(t*SR))
        if 0 <= s < total:
            h = jdb if j % 4 == 0 else jbt*0.5
            n = min(len(h), total-s); o[s:s+n, 0] += h[:n]; o[s:s+n, 1] += h[:n]
    return o

def render_nat(text, audio, segs):
    """whole phrase continuous, anchor only 'go' on the beat before the event."""
    pre = 0.25
    go_on = segs[-1][0]/SR if segs else len(audio)/SR
    go_time = pre + go_on; event_t = go_time + BEAT
    total = int((event_t + 0.8)*SR)
    buf = np.zeros((total, 2), np.float32); R._put(buf, audio, pre)
    return buf, event_t, total

def render_grid(text, audio, segs):
    """cut the break-silences into per-word clips (from the SINGLE natural generation) and place
    each word's vowel onset ON its beat — words-on-clicks, but natural single-gen tone/pauses and
    cuts land in the silences (never inside a word)."""
    W = len(segs); pre = 0.30
    clips = [audio[s:e] for s, e in segs]
    event_t = pre + W*BEAT                                  # word0 vowel ~ pre; 'go' at event-1 beat
    total = int((event_t + 0.8)*SR)
    buf = np.zeros((total, 2), np.float32)
    for k, clip in enumerate(clips):
        vo = R._vowel_onset(clip)
        R._put(buf, clip, event_t - (W-k)*BEAT - vo)
    return buf, event_t, total

def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"voice {R.ELEVEN_VOICE}  bpm {BPM}  break {BREAK_S}s  stab {R.ELEVEN_STABILITY} seed {R.ELEVEN_SEED}")
    for text in CUES:
        audio = synth_natural(text)
        if audio is None:
            print(f"  {text!r}: SKIP (synth failed)"); continue
        segs = voiced_segments(audio)
        for mode, fn in (("nat", render_nat), ("grid", render_grid)):
            buf, event_t, total = fn(text, audio, segs)
            m = buf + click_aligned(total, event_t)*0.5
            pk = float(np.abs(m).max())
            if pk > 0.97: m *= 0.97/pk
            p = os.path.join(OUT, f"{slug(text)}_{mode}.mp3")
            subprocess.run(["ffmpeg","-v","quiet","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",
                            "-b:a","192k",p], input=m.astype(np.float32).tobytes())
        print(f"  {slug(text):32} [{len(segs)} words, {len(audio)/SR:.2f}s]  nat+grid  {text!r}")

if __name__ == "__main__":
    main()
