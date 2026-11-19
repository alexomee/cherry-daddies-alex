#!/usr/bin/env python3
"""Build the level-calibration song from real pieces of the program (wiki/pipelines/level-anchors.md).

Not an artificial sound: each block is a place of a real song, played alone, at exactly the level
it has in that song's playback.

  guitar  «Мало тебя» bars 21-37 — the recorded distortion rhythm guitar (layer malo-guitars),
          alone in PB Other. Live guitar there = POD Go 32D.
  bass    «Солнышко» bars 9-25 — bars 9-17 the bass is played live (GM-800 scene 7, pb-bass
          silent, as in the song), bars 17-25 the recorded synth-bass takes over in PB Bass.

Each block alternates "recording" and "you": 8 bars the recording plays, 8 bars only the click.
Click and cues are cut from the same songs' renders, so tempo and the spoken cues are the real ones.

Writes music/songs/_Калибровка/{mix.json, auto-render/{click,cues,pb-other,pb-bass}.wav}.
Then: tools/stagetraxx_sync.py --apply "Калибровка".

    uv run -q --python 3.12 --with numpy --with soundfile tools/calibration_track.py
"""
import io, json, os, subprocess, sys
import numpy as np, soundfile as sf

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS = os.path.join(REPO, "music", "songs")
SID = "_Калибровка"
SR = 44100
GUITAR = {"song": "SEREBRO - Malo tebya", "layer": "malo-guitars", "group": "pb-other"}
BASS = {"song": "Demo - Solnyshko", "group": "pb-bass"}
ROUNDS = 2          # guitar: (rec 21-29, you, rec 29-37, you) x ROUNDS
BASS_ROUNDS = 3     # bass:   (you 9-17, rec 17-25) x BASS_ROUNDS
FADE = 0.012
# What the live rig plays in each block: guitar on 32D with the synth muted (scene 1 = MUTE),
# synth bass on scene 7 with the guitar on the mute patch 31D.
PATCH = {"guitar": {"podgo": "32D", "gm800": 1}, "bass": {"podgo": "31D", "gm800": 7}}
TAG_IN = 0.030      # a region's patch tag goes out this long after the region starts


def tag(i, region_start):
    return 0.0 if i == 0 else round(region_start + TAG_IN, 3)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR),
                          "-f", "wav", "-"], capture_output=True, check=True).stdout
    x, _ = sf.read(io.BytesIO(raw), dtype="float64")
    return x


def song(name):
    d = os.path.join(SONGS, name)
    mix = json.load(open(os.path.join(d, "mix.json"), encoding="utf-8"))
    bar1 = next(c["abs_sec"] for c in mix["cues"] if c["bar"] == 1 and c.get("beat", 1) == 1)
    tl = json.load(open(os.path.join(d, "auto-render", "timeline.json")))
    r = {f: load(os.path.join(d, "auto-render", f + ".wav")) for f in ("click", "cues")}
    return d, mix, bar1, tl["bar_sec"], r


def cut(x, bar1, bar_sec, a, b):
    """Bars [a, b) of a render-frame signal, faded at both ends."""
    i, j = int(round((bar1 + (a - 1) * bar_sec) * SR)), int(round((bar1 + (b - 1) * bar_sec) * SR))
    y = x[i:j].copy()
    n = int(FADE * SR)
    ramp = np.linspace(0, 1, n)[:, None]
    y[:n] *= ramp
    y[-n:] *= ramp[::-1]
    return y


def lufs_mono(x):
    """Playback metric of the project: LUFS of the mono fold + 3.01 (level_audit.py)."""
    buf = io.BytesIO()
    sf.write(buf, x, SR, format="WAV", subtype="PCM_24")
    out = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", "-", "-af",
                          "pan=mono|c0=0.5*c0+0.5*c1,ebur128=framelog=quiet", "-f", "null", "-"],
                         input=buf.getvalue(), capture_output=True).stderr.decode()
    return float(out.split("Integrated loudness:")[-1].split("I:")[1].split("LUFS")[0]) + 3.01


def main():
    # ---- guitar: the layer alone, at the gain it has inside the rendered pb-other
    gd, gmix, g1, gbar, gr = song(GUITAR["song"])
    layer = next(l for l in gmix["pb-other"]["layers"] if l["file"] == GUITAR["layer"])
    part = load(os.path.join(gd, "parts", GUITAR["layer"] + ".wav"))        # render frame, 1:1
    rendered = load(os.path.join(gd, "auto-render", "pb-other.wav"))
    n = min(len(part), len(rendered))
    i, j = int((g1 + 20 * gbar) * SR), int((g1 + 36 * gbar) * SR)
    p, r = part[i:j].ravel(), rendered[i:j].ravel()
    k = float(p @ r / (p @ p))                       # least squares: other layers are uncorrelated
    k_db = 20 * np.log10(k)
    print(f"guitar: layer gain in the render {k_db:+.2f} dB (mix.json gain_db {layer['gain_db']})")
    guitar = part[:n] * k

    # ---- bass: pb-bass of «Солнышко» is the synth-bass layer alone
    bd, bmix, b1, bbar, br = song(BASS["song"])
    bass = load(os.path.join(bd, "auto-render", "pb-bass.wav"))

    Z = lambda a: np.zeros_like(a)
    tracks = {"click": [], "cues": [], "pb-other": [], "pb-bass": []}
    marks, t = [], 0.0

    def add(label, click, cues, other=None, pbass=None, dev="guitar", early=0.0, lead_in=0.0):
        """One region. It starts `early` seconds before this chunk (a "you" region opens on the
        last bar of the recording: a count-in, and the patch is up before you play); `lead_in` =
        count bars at the head of the chunk itself."""
        nonlocal t
        marks.append((label, t + lead_in, t - early, dev))
        tracks["click"].append(click)
        tracks["cues"].append(cues)
        tracks["pb-other"].append(other if other is not None else Z(click))
        tracks["pb-bass"].append(pbass if pbass is not None else Z(click))
        t += len(click) / SR

    gc = lambda a, b: cut(gr["click"], g1, gbar, a, b)
    add("гитара: счёт", gc(19, 21), cut(gr["cues"], g1, gbar, 19, 21))
    for rnd in range(ROUNDS):
        for a in (21, 29):
            add(f"гитара запись {a}–{a + 8}", gc(a, a + 8), cut(gr["cues"], g1, gbar, a, a + 8),
                other=cut(guitar, g1, gbar, a, a + 8))
            add("гитара ты", gc(a, a + 8), Z(gc(a, a + 8)), early=gbar)
    bc = lambda a, b: cut(br["click"], b1, bbar, a, b)
    for rnd in range(BASS_ROUNDS):
        a = 9 - (rnd == 0)                 # the first round carries its own count bar (bar 8)
        add("бас ты 9–17", bc(a, 17), cut(br["cues"], b1, bbar, a, 17), dev="bass",
            early=bbar * (rnd > 0), lead_in=bbar * (rnd == 0))
        add("бас запись 17–25", bc(17, 25), cut(br["cues"], b1, bbar, 17, 25),
            pbass=cut(bass, b1, bbar, 17, 25), dev="bass")

    out = os.path.join(SONGS, SID, "auto-render")
    os.makedirs(out, exist_ok=True)
    for name, chunks in tracks.items():
        sf.write(os.path.join(out, name + ".wav"), np.concatenate(chunks), SR, subtype="PCM_16")

    g_rec = np.concatenate([c for c, m in zip(tracks["pb-other"], marks) if "гитара запись" in m[0]])
    b_rec = np.concatenate([c for c, m in zip(tracks["pb-bass"], marks) if "бас запись" in m[0]])
    print(f"guitar block: {lufs_mono(g_rec):.1f}   bass block: {lufs_mono(b_rec):.1f}   "
          f"(norms: F -17, bass -19)   length {t:.1f} s")

    mix = {
        "_generated_by": "tools/calibration_track.py — do not render with jamzone_render.py",
        "bpm": gmix["bpm"],
        "cues": [{"bar": i + 1, "text": lb, "abs_sec": round(s, 3), "snap_sec": round(r, 3)}
                 for i, (lb, s, r, _d) in enumerate(marks)],
        # Every region sets its own patch, so a jump to any region leaves both units right:
        # the tag sits just inside the region ("lead": 0 = sent exactly at abs_sec), and
        # "resend" makes the sync write it even when the program does not change.
        "resend": True,
        "podgo": [{"bar": i + 1, "preset": PATCH[d]["podgo"], "abs_sec": tag(i, r), "lead": 0}
                  for i, (_lb, _s, r, d) in enumerate(marks)],
        "gm800": [{"bar": i + 1, "scene": PATCH[d]["gm800"], "abs_sec": tag(i, r), "lead": 0}
                  for i, (_lb, _s, r, d) in enumerate(marks)],
        "sources": {"guitar": {**GUITAR, "bars": [21, 37], "gain_in_render_db": round(k_db, 2)},
                    "bass": {**BASS, "bars": [9, 25]}},
    }
    with open(os.path.join(SONGS, SID, "mix.json"), "w", encoding="utf-8") as f:
        json.dump(mix, f, ensure_ascii=False, indent=1)
    for lb, s, r, d in marks:
        print(f"  region {int(r // 60)}:{r % 60:04.1f}  music {int(s // 60)}:{s % 60:04.1f}  {lb:22} "
              f"POD Go {PATCH[d]['podgo']}  GM-800 {PATCH[d]['gm800']}")


if __name__ == "__main__":
    sys.exit(main())
