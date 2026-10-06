"""Local, reproducible violin transcription analysis (Python 3.11).

Dependencies: basic-pitch[onnx]==0.4.0 numpy<2 setuptools<81 matplotlib soundfile.
Run from any directory; generated model data stays in .cache/.
"""

import json
import csv
import hashlib
import sys
from pathlib import Path

import librosa
import matplotlib
import numpy as np
import soundfile as sf
import pretty_midi
from scipy.ndimage import gaussian_filter1d, median_filter, binary_closing, binary_dilation

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SONG = HERE.parent.parent
CACHE = HERE / ".cache"
CACHE.mkdir(exist_ok=True)
SOURCE = SONG / "strings.wav"
BPM = json.loads((SONG / "mix.json").read_text())["bpm"]
OFFSET = json.loads((SONG / "auto-render/timeline.json").read_text())["offset_sec"]


def infer():
    from basic_pitch.inference import predict
    import basic_pitch

    cache_path = CACHE / "model.npz"
    if not cache_path.exists():
        model = Path(basic_pitch.__file__).parent / "saved_models/icassp_2022/nmp.onnx"
        output, midi, events = predict(
            SOURCE, model, onset_threshold=0.3, frame_threshold=0.18,
            minimum_note_length=85, minimum_frequency=190, maximum_frequency=2100,
            midi_tempo=BPM,
        )
        np.savez_compressed(cache_path, **output)
        midi.write(str(CACHE / "raw.mid"))
        (CACHE / "raw-notes.json").write_text(json.dumps([
            [float(s), float(e), int(p), float(a)] for s, e, p, a, _ in events
        ], indent=2))
    return dict(np.load(cache_path))


def inspect_source(output):
    y, sr = librosa.load(SOURCE, sr=22050)
    hop = 256
    cqt_path = CACHE / "cqt.npz"
    if cqt_path.exists():
        spec = np.load(cqt_path)["spec"]
    else:
        spec = abs(librosa.cqt(y, sr=sr, hop_length=hop, fmin=librosa.midi_to_hz(48),
                               n_bins=156, bins_per_octave=36))
        np.savez_compressed(cqt_path, spec=spec)
    fig, axes = plt.subplots(3, 1, figsize=(20, 12))
    axes[0].plot(np.arange(len(y))[::220] / sr, y[::220])
    axes[0].set(title="Strings stem waveform (source seconds)", xlim=(0, len(y)/sr))
    axes[1].imshow(librosa.amplitude_to_db(spec, ref=np.max), origin="lower", aspect="auto",
                   extent=(0, spec.shape[1]*hop/sr, 48, 100), vmin=-65, vmax=0)
    axes[1].set(title="CQT, MIDI pitch", yticks=range(48, 101, 4))
    axes[2].imshow(output["note"].T, origin="lower", aspect="auto",
                   extent=(0, len(y)/sr, 21, 109), vmin=0, vmax=0.8)
    axes[2].set(title="Basic Pitch note activation", ylim=(48, 100), yticks=range(48, 101, 4))
    fig.tight_layout()
    fig.savefig(HERE / "analysis-overview.png", dpi=130)
    plt.close(fig)
    for start, end in [(0, 6.5), (26, 32.5), (60, 66.5), (160, 173)]:
        fig, ax = plt.subplots(figsize=(20, 9))
        lo, hi = int(start*sr/hop), int(end*sr/hop)
        image = spec[:, lo:hi]
        ax.imshow(librosa.amplitude_to_db(image, ref=np.max), origin="lower", aspect="auto",
                  extent=(start, end, 48-1/6, 100-1/6), vmin=-45, vmax=0)
        ax.set(yticks=range(55, 100), ylim=(55, 98), xticks=np.arange(start, end, .2),
               title=f"{start}-{end}s source: CQT, MIDI pitch")
        ax.grid(alpha=.3)
        fig.tight_layout()
        fig.savefig(CACHE / f"detail-{start}.png", dpi=120)
        plt.close(fig)
    notes = json.loads((CACHE / "raw-notes.json").read_text())
    for start in range(0, 210, 10):
        found = [n for n in notes if start <= n[0] < start+10]
        rms = np.sqrt(np.mean(y[start*sr:min((start+10)*sr, len(y))]**2))
        print(f"{start:3d}s rms={rms:.5f}: " + " ".join(
            f"{s:.2f}:{librosa.midi_to_note(p)}({e-s:.2f},{a:.2f})" for s,e,p,a in sorted(found)))


def runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))


def refine(output):
    """Combine neural activation with fundamental support; reject harmonic duplicates.

    No key/scale snapping: chromatic source notes are allowed. A short median
    filter and spectral gap checks remove vibrato-driven onset fragmentation.
    """
    from basic_pitch.note_creation import model_frames_to_time

    dt = .01
    times = np.arange(0, sf.info(SOURCE).duration, dt)
    pitches = np.arange(60, 87)
    model_times = model_frames_to_time(len(output["note"]))
    prob = np.array([np.interp(times, model_times, output["note"][:, p-21]) for p in pitches])
    prob = median_filter(prob, size=(1, 5))
    cqt = np.load(CACHE / "cqt.npz")["spec"]
    cqt_times = np.arange(cqt.shape[1])*256/22050
    fundamental = np.array([
        np.interp(times, cqt_times, cqt[(p-48)*3-1:(p-48)*3+2].max(axis=0))
        for p in pitches
    ])
    strongest = np.interp(times, cqt_times, cqt[36:135].max(axis=0))
    relative = fundamental / np.maximum(strongest, 1e-8)
    # Require a harmonic family, not just a single strong overtone. This also
    # recovers source-supported notes whose neural activation is weak.
    harmonic = []
    for k,p in enumerate(pitches):
        partials=[fundamental[k]]
        for h in (2,3):
            center=round((p+12*np.log2(h)-48)*3)
            if center+2<cqt.shape[0]:
                partials.append(np.interp(times,cqt_times,cqt[center-1:center+2].max(axis=0)))
        harmonic.append(np.exp(np.mean(np.log(np.maximum(partials,1e-9)),axis=0)))
    harmonic=np.array(harmonic)
    harmonic/=np.maximum(harmonic.max(axis=0),1e-8)
    score=(.55*prob+.45*harmonic)*np.minimum(1.,relative/.22)
    # At least some neural evidence is required to avoid transcribing spill.
    score*=np.minimum(1.,prob/.22)
    # Absolute gate derived from the active stem, not normalized silence/noise.
    gate = strongest > np.percentile(strongest, 90)*.025
    score *= gate
    original_score = score.copy()
    # A supported lower fundamental explains octave/third-harmonic detections.
    # This is conservative about octave doubling; candidates remain in raw.mid.
    for k in reversed(range(len(pitches))):
        p=pitches[k]
        for interval in (12, 19, 24):
            low = k-interval
            if low >= 0:
                supported = (original_score[low] > .38) & (relative[low] > .13)
                supported = binary_closing(supported,structure=np.ones(12))
                supported = median_filter(supported, size=9)
                # Bridge short octave jumps at attacks: a lower fundamental is
                # present but the model briefly reports its second harmonic.
                if interval==12:
                    nearby=binary_dilation(supported,structure=np.ones(31))
                    nearby &= (relative[low]>.11) & (prob[low]>.15)
                    score[low,nearby]=np.maximum(score[low,nearby],.85*score[k,nearby])
                    supported |= nearby
                score[k, supported] *= .10
    # Weak neighbouring-semitone duplicates usually represent vibrato/slides,
    # not a second violin playing a sustained minor second.
    for k in range(len(pitches)):
        for j in (k-1,k+1):
            if 0<=j<len(pitches):
                smear=(score[j]>.55)&(score[k]<.65*score[j])&(prob[k]<.45)
                score[k,smear]*=.1

    candidates = []
    for k, p in enumerate(pitches):
        active = binary_closing(score[k] > .26, structure=np.ones(6))
        for s, e in runs(active):
            if (e-s)*dt < .105 or np.max(score[k, s:e]) < .40:
                continue
            if np.mean(score[k, s:e]) < .31:
                continue
            # Natural repeated bows are retained when their fundamental has
            # a real energy valley. Neural onset peaks alone often follow vibrato.
            amp = gaussian_filter1d(fundamental[k, s:e], 1.2)
            from scipy.signal import find_peaks
            valleys, props = find_peaks(-amp, distance=16, prominence=max(amp)*.42)
            cuts = [s] + [s+int(v) for v in valleys if v >= 11 and e-s-v >= 11] + [e]
            for a, b in zip(cuts, cuts[1:]):
                candidates.append({
                    "start": round(a*dt, 4), "end": round(b*dt, 4), "pitch": int(p),
                    "confidence": float(np.mean(prob[k,a:b])),
                    "support": float(np.median(relative[k,a:b])),
                    "score": float(np.mean(score[k,a:b])),
                })

    # Resolve genuine overlaps using continuity. Weak third candidates cannot
    # create a third violin; keep a review log of dropped/conflicting material.
    # Occupancy selection favours sustained notes over short noisy intrusions.
    eligible = np.zeros((len(pitches), len(times)), dtype=bool)
    for n in candidates:
        a, b = round(n["start"]/dt), round(n["end"]/dt)
        k = n["pitch"]-pitches[0]
        eligible[k,a:b]=True
    rank_score=median_filter(score,size=(1,9))*eligible
    best=np.argsort(rank_score,axis=0)[-2:]
    selected=np.zeros_like(eligible)
    for row in best:
        selected[row,np.arange(len(times))]=True
    selected &= eligible
    notes = []
    for k,p in enumerate(pitches):
        # Keep observed retriggers from candidate segmentation.
        cuts = {round(n["start"]/dt) for n in candidates if n["pitch"] == p}
        for a,b in runs(selected[k]):
            boundaries = [a] + sorted(c for c in cuts if a+10 <= c <= b-10) + [b]
            for s,e in zip(boundaries, boundaries[1:]):
                if e-s < 10:
                    continue
                conf = float(np.mean(prob[k,s:e]))
                supp = float(np.median(relative[k,s:e]))
                notes.append(dict(start=s*dt, end=e*dt, pitch=int(p), confidence=conf,
                                  support=supp, score=float(np.mean(score[k,s:e]))))
    notes.sort(key=lambda n: (n["start"], -n["pitch"]))
    # Remove very short octave-tail fragments adjacent to a supported lower
    # note. They otherwise turn a single violin release into a register jump.
    notes=[n for n in notes if not (
        n["end"]-n["start"]<.20 and n["score"]<.65 and any(
            m["pitch"]==n["pitch"]-12 and m["score"]>.50 and
            (abs(m["end"]-n["start"])<.08 or abs(m["start"]-n["end"])<.08)
            for m in notes))]
    # Neural release tails at stepwise transitions should not force artificial
    # swaps of the two voices (e.g. E4 overlaps the following D4 by 30 ms).
    for i,a in enumerate(notes):
        for b in notes[i+1:]:
            if b["start"]>=a["end"]:
                break
            overlap=a["end"]-b["start"]
            if 0<abs(a["pitch"]-b["pitch"])<=5 and overlap<=.08 and b["start"]-a["start"]>.09:
                a["end"]=b["start"]
    np.savez_compressed(CACHE / "refined-activation.npz", times=times, pitches=pitches,
                        score=score, original_score=original_score, selected=selected)
    return notes, candidates


def split_voices(notes):
    """Colour the interval graph, then orient each phrase upper/lower.

    Connected overlap components have at most two active notes. The notes remain
    whole: a sustained note is not chopped every time its companion changes.
    An isolated phrase belongs to Violin 1.
    """
    adjacency = [[] for _ in notes]
    for i,a in enumerate(notes):
        for j in range(i+1,len(notes)):
            b=notes[j]
            if b["start"] >= a["end"]-1e-7:
                break
            adjacency[i].append(j)
            adjacency[j].append(i)
    visited=set()
    for root in range(len(notes)):
        if root in visited:
            continue
        labels={root:0}
        stack=[root]
        while stack:
            i=stack.pop()
            visited.add(i)
            for j in adjacency[i]:
                if j in labels:
                    assert labels[j] != labels[i], "More than two voices"
                else:
                    labels[j]=1-labels[i]
                    stack.append(j)
        # Choose orientation by actual overlapping pitch order, weighted by time.
        vote=0.
        for i in labels:
            for j in adjacency[i]:
                if j <= i:
                    continue
                overlap=min(notes[i]["end"],notes[j]["end"])-max(notes[i]["start"],notes[j]["start"])
                vote += overlap*np.sign(notes[i]["pitch"]-notes[j]["pitch"])*(1 if labels[i]==0 else -1)
        flip=int(vote<0)
        for i,label in labels.items():
            notes[i]["voice"]=(label^flip)+1
    return notes


def write_midi(notes, path, voice=None):
    midi=pretty_midi.PrettyMIDI(initial_tempo=BPM, resolution=960)
    midi.time_signature_changes.append(pretty_midi.TimeSignature(4,4,0))
    midi.key_signature_changes.append(pretty_midi.KeySignature(14,0))  # D minor
    for v in ([voice] if voice else [1,2]):
        instrument=pretty_midi.Instrument(40,name=f"Violin {v} - draft voice")
        for n in notes:
            if n["voice"] != v:
                continue
            velocity=int(np.clip(55+45*n["confidence"],60,105))
            instrument.notes.append(pretty_midi.Note(velocity,n["pitch"],n["start"]+OFFSET,n["end"]+OFFSET))
        midi.instruments.append(instrument)
    midi.write(str(path))
    return midi


def previews(notes):
    """Plain harmonic guide, deliberately not sold as a sampled violin sound."""
    sr=44100
    source,_=sf.read(SOURCE,always_2d=True)
    total=max(len(source)+round(OFFSET*sr), round(max(n["end"] for n in notes)*sr)+round(OFFSET*sr)+sr)
    voices=np.zeros((2,total),dtype=np.float32)
    for n in notes:
        start=round((n["start"]+OFFSET)*sr)
        duration=n["end"]-n["start"]
        t=np.arange(round((duration+.05)*sr))/sr
        freq=librosa.midi_to_hz(n["pitch"])
        wave=sum(np.sin(2*np.pi*freq*h*t)/(h**1.7) for h in range(1,7))
        env=np.minimum(t/.014,1)*np.clip((duration+.05-t)/.05,0,1)
        wave=wave*env*(.6+.4*n["confidence"])
        voices[n["voice"]-1,start:start+len(wave)]+=wave
    scale=.65/max(1,np.max(abs(voices.sum(axis=0))))
    voices*=scale
    midi_stereo=np.stack([voices[0]+.65*voices[1],.65*voices[0]+voices[1]],axis=1)
    sf.write(HERE/"violin-midi-guide.wav",midi_stereo,sr,subtype="PCM_24")
    aligned=np.zeros(total,dtype=np.float32)
    aligned[round(OFFSET*sr):round(OFFSET*sr)+len(source)]=source.mean(axis=1)
    synthesized=voices.sum(axis=0)
    # Equalize active RMS for an easy headphones comparison; shared peak limiter.
    active=abs(aligned)>.008
    synthesized*=np.sqrt(np.mean(aligned[active]**2))/max(np.sqrt(np.mean(synthesized[active]**2)),1e-8)
    comparison=np.stack([aligned,synthesized],axis=1)
    comparison*=.90/max(np.max(abs(comparison)),1e-8)
    sf.write(HERE/"compare-source-left-midi-right.wav",comparison,sr,subtype="PCM_24")


def export(notes, candidates, output):
    import mido

    midi=write_midi(notes,HERE/"kukla-violins-2voices.mid")
    for voice in (1,2):
        write_midi(notes,HERE/f"kukla-violin-{voice}.mid",voice)
    rows=[]
    for n in notes:
        start=n["start"]+OFFSET
        rows.append({"voice":n["voice"],"midi_note":n["pitch"],
                     "note_C4_60":librosa.midi_to_note(n["pitch"],unicode=False),
                     "render_start_s":round(start,4),"duration_s":round(n["end"]-n["start"],4),
                     "source_start_s":round(n["start"],4),
                     "confidence":round(n["confidence"],3),"fundamental_support":round(n["support"],3),
                     "review":n["confidence"]<.48 or n["support"]<.20})
    with (HERE/"notes.csv").open("w") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    # Fresh readback, independent MIDI parser, and comparison to source-frame data.
    check=pretty_midi.PrettyMIDI(str(HERE/"kukla-violins-2voices.mid"))
    assert len(check.instruments)==2
    assert abs(check.get_tempo_changes()[1][0]-BPM)<.001
    assert all(not inst.pitch_bends for inst in check.instruments)
    max_error=0.
    for v,inst in enumerate(check.instruments,1):
        expected=[n for n in notes if n["voice"]==v]
        assert len(inst.notes)==len(expected)
        for a,b in zip(inst.notes,expected):
            assert a.pitch==b["pitch"] and a.end>a.start and 1<=a.velocity<=127
            max_error=max(max_error,abs(a.start-(b["start"]+OFFSET)),abs(a.end-(b["end"]+OFFSET)))
        assert all(a.end<=b.start+.001 for a,b in zip(inst.notes,inst.notes[1:]))
    assert max_error<.001
    parsed=mido.MidiFile(HERE/"kukla-violins-2voices.mid")
    assert sum(msg.type=="note_on" and msg.velocity>0 for track in parsed.tracks for msg in track)==len(notes)
    previews(notes)
    report={"source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "source_duration_s":sf.info(SOURCE).duration,"bpm":BPM,"render_offset_s":OFFSET,
            "raw_notes":len(json.loads((CACHE/"raw-notes.json").read_text())),
            "spectrally_filtered_candidates":len(candidates),"final_notes":len(notes),
            "voice_notes":{str(v):sum(n["voice"]==v for n in notes) for v in (1,2)},
            "review_notes":sum(r["review"] for r in rows),
            "pitch_range_midi":[min(n["pitch"] for n in notes),max(n["pitch"] for n in notes)],
            "first_note_render_s":min(n["start"] for n in notes)+OFFSET,
            "last_note_render_s":max(n["end"] for n in notes)+OFFSET,
            "midi_roundtrip_max_error_s":max_error,
            "pitch_bends":0,"quantization":"none","verification":"spectral and MIDI structural; not a listening sign-off"}
    (HERE/"verification.json").write_text(json.dumps(report,indent=2)+"\n")
    (CACHE/"final-notes.json").write_text(json.dumps(notes,indent=2))
    print(json.dumps(report,indent=2))
    # Focused source-vs-notes visual check, not just a plot of model outputs.
    spec=np.load(CACHE/"cqt.npz")["spec"]
    for start,end in [(0,6.5),(26,32.5),(60,66.5),(160,173),(190,200)]:
        lo,hi=int(start*22050/256),int(end*22050/256)
        fig,ax=plt.subplots(figsize=(19,7))
        ax.imshow(librosa.amplitude_to_db(spec[:,lo:hi],ref=np.max),origin="lower",aspect="auto",
                  extent=(start,end,48-1/6,100-1/6),vmin=-45,vmax=0,cmap="Greys")
        for n in notes:
            if n["start"]<end and n["end"]>start:
                ax.plot([n["start"],n["end"]],[n["pitch"]+.2]*2,lw=3,
                        color="tab:blue" if n["voice"]==1 else "tab:orange")
        ax.set(xlim=(start,end),ylim=(59,87),yticks=range(60,87),
               title="Source spectrum + MIDI (source seconds; blue=1, orange=2)")
        ax.grid(alpha=.2); fig.tight_layout()
        fig.savefig(HERE/f"check-{start:03d}s.png",dpi=120); plt.close(fig)


if __name__ == "__main__":
    output=infer()
    if "--inspect" in sys.argv or not (CACHE/"cqt.npz").exists():
        inspect_source(output)
    if "--inspect" not in sys.argv:
        notes,candidates=refine(output)
        export(split_voices(notes),candidates,output)
