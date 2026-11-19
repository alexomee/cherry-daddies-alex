#!/usr/bin/env python3
"""Read-only loudness audit of the playback program (see wiki/pipelines/level-anchors.md).

For every song of the program (web/songs.json, archive excluded) measures
  - the rendered groups auto-render/{pb-other,pb-bass,all}.wav
  - every source element (stem / layer) that feeds a pb-* group in mix.json
and writes analysis/level-audit/level_audit.json. Renders and mix.json are never touched.

Metric. Stage Traxx plays a MONO fold of each file (ffmpeg -ac 1 = 0.5L + 0.5R), so the level
that reaches the desk is the level of the fold, not of the stereo render. Every loudness here is
    M = LUFS(mono fold) + 3.01
i.e. centred content reads the same as its stereo LUFS (pb-bass norm stays -19.2), wide content
reads lower by its real fold loss. Fields per measurement:
    I       integrated loudness (gated, so silence between phrases is mostly ignored)
    S50/S90 median / 90th percentile of short-term (3 s) loudness over the active part
    LRA     loudness range, peak = sample peak of the fold (dBFS), active = share of the song
    fold    stereo I - M  (0 = centred, 3 = decorrelated L/R), groups only

Usage:
    tools/level_audit.py              # whole program -> json + summary
    tools/level_audit.py "<song>"     # one song (substring of the folder name), summary only
"""
import collections, concurrent.futures as cf, glob, json, os, re, statistics as st, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools", "jamzone"))
import jamzone_render as jr  # noqa: E402

OUT = os.path.join(REPO, "analysis", "level-audit", "level_audit.json")
FOLD = "pan=mono|c0=0.5*c0+0.5*c1,"

# class of an element by file name: first match wins. Crude on purpose -- the role (riff / pad /
# double) is not in the name; the per-class norm table lives in the wiki, not here.
CLASSES = [
    ("fx", r"noise|sound.?effects?|sfx|\bfx\b"),
    ("back-vox", r"back(ing)?.?vocals?|back.?vox|choir|vocal"),
    ("bass", r"bass|бас"),
    ("guitar", r"guitar|gtr|гитар|wah|charango|banjo|mandolin"),
    ("lead", r"lead|sax|trumpet|brass|horn|flute|violin|accordion|harmonica|whistle|solo"),
    ("pad", r"pad|strings?|organ"),
    ("keys", r"keys|piano|synth|arp|bell|clav|rhodes|marimba|vibra|other|pluck"),
]


def klass(name):
    for k, pat in CLASSES:
        if re.search(pat, name, re.I):
            return k
    return "other"


def _ebur(path, fold):
    cmd = ["ffmpeg", "-nostats", "-hide_banner", "-i", path,
           "-af", (FOLD if fold else "") + "ebur128=peak=sample:framelog=info", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    summ = err[err.rfind("Summary:"):]
    g = lambda pat: (float(m.group(1)) if (m := re.search(pat, summ)) else None)
    return (g(r"I:\s*(-?\d+\.\d+) LUFS"), g(r"LRA:\s*(-?\d+\.\d+) LU"), g(r"Peak:\s*(-?\d+\.\d+) dBFS"),
            [float(x) for x in re.findall(r"\bS:\s*(-?\d+\.\d+)", err)])


def measure(path, with_fold=False):
    """Loudness of the mono fold (+3.01, see module doc). with_fold also measures the stereo file."""
    I, lra, pk, s = _ebur(path, True)
    if I is None or I < -69:
        return {"I": None}
    act = sorted(x for x in s if x > I - 20 and x > -70)
    q = lambda p: round(act[min(len(act) - 1, int(p * len(act)))] + 3.01, 1) if act else None
    r = {"I": round(I + 3.01, 1), "S50": q(0.5), "S90": q(0.9), "LRA": lra, "peak": pk,
         "active": round(len(act) / len(s), 2) if s else None}
    if with_fold:
        Is = _ebur(path, False)[0]
        r["fold"] = round(Is - r["I"], 1) if Is is not None else None
    return r


def program(query=None):
    d = json.load(open(os.path.join(REPO, "web", "songs.json")))
    seen = {}
    for s in d["sets"]:
        for x in s["songs"]:
            seen.setdefault(x["sid"], []).append(s.get("name") or "")
    prog = {sid: sets for sid, sets in seen.items() if not all("рхив" in n for n in sets)}
    if query:
        prog = {sid: v for sid, v in prog.items() if query.lower() in sid.lower()}
    return prog


def collect(query=None):
    jobs, songs = {}, {}
    for sid, sets in program(query).items():
        folder = os.path.join(jr.SONGS, sid)
        mp = os.path.join(folder, "mix.json")
        if not os.path.exists(mp):
            continue
        mix = json.load(open(mp))
        paths = jr._stem_paths(folder)
        rec = {"sets": sets, "pitch": mix.get("pitch_semitones", 0), "gm800": mix.get("gm800"),
               "podgo": mix.get("podgo"), "groups": {}, "render": {}}
        for f in ("pb-other", "pb-bass", "all"):
            p = os.path.join(folder, "auto-render", f + ".wav")
            if os.path.exists(p):
                jobs[(sid, None, f)] = (p, True)
        for grp in jr.pb_group_names(mix):
            m = mix.get(grp) or {}
            trims, overrides = m.get("gain_db") or {}, m.get("roles") or {}
            els = []
            for n in m.get("stems", []):
                if jr.is_percussion(n):
                    continue
                els.append({"name": n, "kind": "stem", "class": klass(n),
                            "role": jr.classify(n, overrides), "gain_db": trims.get(n, 0),
                            "_path": paths.get(n)})
            for ent in m.get("layers", []):
                ent = ent if isinstance(ent, dict) else {"file": ent}
                lp = sorted(glob.glob(os.path.join(folder, "parts", ent["file"] + ".*")))
                els.append({"name": ent["file"], "kind": "layer", "class": klass(ent["file"]),
                            "role": jr.classify(ent["file"], overrides),
                            "gain_db": ent.get("gain_db", trims.get(ent["file"], 0)),
                            "derived": bool(ent.get("derived")), "gain_bars": ent.get("gain_bars"),
                            "_path": lp[0] if lp else None})
            for e in els:
                if e["_path"]:
                    jobs[(sid, grp, e["name"])] = (e["_path"], False)
            rec["groups"][grp] = {"peak_mode": m.get("peak"), "elements": els}
        songs[sid] = rec
    print(f"{len(songs)} songs, {len(jobs)} files", flush=True)
    with cf.ThreadPoolExecutor(8) as ex:
        res = dict(zip(jobs, ex.map(lambda a: measure(*a), jobs.values())))
    for (sid, grp, name), r in res.items():
        if grp is None:
            songs[sid]["render"][name] = r
        else:
            for e in songs[sid]["groups"][grp]["elements"]:
                if e["name"] == name:
                    e["src"] = r   # level of the SOURCE; in the group it is src.I + gain_db, then
    for rec in songs.values():     # the fx/back-vox ceiling and the group's peak step on top
        for g in rec["groups"].values():
            for e in g["elements"]:
                e.pop("_path", None)
    return songs


def _desc(label, v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return
    q = lambda p: v[min(len(v) - 1, int(p * len(v)))]
    print(f"  {label:26} n={len(v):3}  min {v[0]:+6.1f}  p10 {q(.1):+6.1f}  med {st.median(v):+6.1f}"
          f"  p90 {q(.9):+6.1f}  max {v[-1]:+6.1f}  spread {v[-1] - v[0]:4.1f}")


def summary(S):
    print("\ngroups (mono fold + 3.01):")
    for g in ("pb-other", "pb-bass", "all"):
        for k in ("I", "S90", "peak", "fold"):
            _desc(f"{g} {k}", [r["render"].get(g, {}).get(k) for r in S.values()])
    print("\nheadroom of the fold (dB below full scale):")
    for g in ("pb-other", "pb-bass"):
        c = collections.Counter()
        for r in S.values():
            pk = r["render"].get(g, {}).get("peak")
            if pk is None:
                continue
            lim = r["groups"].get(g, {}).get("peak_mode") == "limit"
            c["limiter" if lim else "<1" if pk > -1 else "1-3" if pk > -3 else "3-6" if pk > -6 else ">6"] += 1
        print(f"  {g:9}", dict(c))
    print("\nelements, source I + gain_db (before ceiling / peak step):")
    by = collections.defaultdict(list)
    for r in S.values():
        for g, G in r["groups"].items():
            for e in G["elements"]:
                if (e.get("src") or {}).get("I") is not None:
                    by[(g, e["class"])].append(e["src"]["I"] + e["gain_db"])
    for k in sorted(by):
        _desc(f"{k[0]}/{k[1]}", by[k])
    if len(S) <= 3:
        for sid, r in S.items():
            print(f"\n{sid}")
            for g in ("pb-other", "pb-bass", "all"):
                if g in r["render"]:
                    print(f"  {g:9} {r['render'][g]}")
            for g, G in r["groups"].items():
                for e in G["elements"]:
                    s = e.get("src") or {}
                    if s.get("I") is not None:
                        print(f"  {g:9} {e['class']:8} {e['kind']:5} {e['name'][:32]:32} "
                              f"I {s['I'] + e['gain_db']:+6.1f}  S90 {s['S90'] + e['gain_db']:+6.1f}  "
                              f"gain {e['gain_db']:+g}  active {s['active']}")


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else None
    S = collect(query)
    summary(S)
    if not query:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(S, open(OUT, "w"), ensure_ascii=False, indent=1)
        print("\nwritten", OUT)


if __name__ == "__main__":
    main()
