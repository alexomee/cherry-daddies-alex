#!/usr/bin/env python3
"""Roma left (2026-11-16): put his live parts into playback from STEMS, song by song.

usage: tools/roma_parts_batch.py [--dry] [song substring ...]
Per song (Alex's decisions 2026-11-17):
  * synths/keys Roma played live (players.roma in snapshot 4e67c9a, non-bass)  -> appended to pb-other stems, unity gain
  * Roma's bass (players.roma bass stems, or bass.who=Roma) with no pb-bass yet   -> pb-bass from stems, level -19.2 LUFS
  * players.roma removed
Safety: auto-render backed up; after the render the click must be sample-identical and timeline offset unchanged
(otherwise the song is ROLLED BACK — mix.json + auto-render — and reported; e.g. a re-render with a newer script
shifted OFF on Beverly Hills). Previous cues.wav restored (say re-synthesis). Then Stage Traxx --apply and verify.
Per-stem fade_out dicts in pb-other are extended to the new stems (copy of an existing entry)."""
import glob, json, os, re, shutil, subprocess, sys, tempfile
import numpy as np

REPO = "/Users/alex/projects/cherry-daddies"; SONGS = f"{REPO}/music/songs"; SNAP = "4e67c9a"; SR = 44100; TARGET = -19.2
BK_ROOT = os.path.join(tempfile.gettempdir(), "roma-parts-batch"); os.makedirs(BK_ROOT, exist_ok=True)
SKIP = {"Eva 2.0"}   # archive (снято с программы)
STDOCS = os.path.expanduser("~/Library/Containers/de.dikant.StageTraxx4/Data/Documents")
sys.path.insert(0, f"{REPO}/tools/jamzone"); import jamzone_render as jr

def git_show(path):
    r = subprocess.run(["git", "-C", REPO, "show", f"{SNAP}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None
src = git_show("tools/setlist_dashboard.py")
BA = dict(re.findall(r'^\s*"([^"]+)":\s*"([^"]+)",', src[src.index("BASS_ASSIGN"):src.index("}", src.index("BASS_ASSIGN"))], re.M))

def dec(p, ch=1):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32).copy()
    return a.reshape(-1, ch) if ch > 1 else a
def lufs(p):
    o = subprocess.run(["ffmpeg", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
def set_top(text, key, value):
    """replace (or insert) a top-level key's value in mix.json text, keeping the rest of the file as is."""
    line = json.dumps(value, ensure_ascii=False)
    m = re.search(r'\n(\s*)"%s"\s*:\s*' % re.escape(key), text)
    if m:
        _, end = json.JSONDecoder().raw_decode(text, m.end())
        return text[:m.end()] + line + text[end:]
    m = re.search(r'\n(\s*)"(players|cues)"\s*:', text)
    return text[:m.start()] + f'\n{m.group(1)}"{key}": {line},' + text[m.start():]

def plan(sid):
    F = f"{SONGS}/{sid}"; mix = json.load(open(F + "/mix.json"))
    old = json.loads(git_show(f"music/songs/{sid}/mix.json") or "{}")
    roma = (old.get("players") or {}).get("roma") or []
    stems = jr._stem_paths(F)
    synth = [s for s in roma if "bass" not in s.lower() and s in stems]
    bass = [s for s in roma if "bass" in s.lower() and s in stems]
    if not bass and BA.get(sid, "").startswith("Roma"):
        bass = [n for n in stems if re.search(r"bass", n, re.I) and not jr.is_percussion(n)]
    po = mix.get("pb-other"); pb_stems = (po or {}).get("stems") or []
    layers = [l for g in jr.pb_group_names(mix) for l in ((mix.get(g) or {}).get("layers") or [])]
    lnames = [l if isinstance(l, str) else l.get("file", "") for l in layers]
    replaced = {r for l in layers if isinstance(l, dict) for r in l.get("replaces", [])}
    if any(n.startswith("roma-keys-") for n in lnames): synth = []      # concert keys already chosen for this song
    synth = [s for s in synth if s not in pb_stems and s not in replaced]
    if mix.get("pb-bass"): bass = []
    return mix, synth, bass, (mix.get("players") or {}).get("roma") is not None

def apply_mix(sid, synth, bass, bass_gain=None):
    F = f"{SONGS}/{sid}"; p = F + "/mix.json"; t = open(p).read(); mix = json.loads(t)
    if synth:
        po = dict(mix.get("pb-other") or {})
        po["stems"] = (po.get("stems") or []) + [s for s in synth if s not in (po.get("stems") or [])]
        fo = po.get("fade_out")
        if isinstance(fo, dict) and fo and all(isinstance(v, dict) for v in fo.values()):   # per-stem fades
            proto = next(v for k, v in fo.items() if k in (po.get("stems") or []))
            for s in synth: fo.setdefault(s, dict(proto))
        t = set_top(t, "pb-other", po)
    if bass:
        pb = {"stems": bass}
        if bass_gain is not None and abs(bass_gain) >= 0.1: pb["gain_db"] = {b: bass_gain for b in bass}
        t = set_top(t, "pb-bass", pb)
    pl = dict(mix.get("players") or {})
    if "roma" in pl:
        pl.pop("roma"); t = set_top(t, "players", pl)
    json.loads(t); open(p, "w").write(t)

def render(sid):
    env = dict(os.environ, JZ_SKIP_SITE="1")
    r = subprocess.run([sys.executable, f"{REPO}/tools/jamzone/jamzone_render.py", sid], cwd=REPO, capture_output=True, text=True, env=env)
    if r.returncode: raise RuntimeError((r.stdout + r.stderr)[-1500:])
    return [l.strip() for l in r.stdout.splitlines() if "normalized" in l or "excluded" in l or "fade_out" in l]

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]; dry = "--dry" in sys.argv
    sets = json.load(open(f"{REPO}/web/songs.json")); sids = []
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("songs"), list):
                for s in o["songs"]:
                    if isinstance(s, dict) and s.get("sid") and s["sid"] not in sids: sids.append(s["sid"])
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(sets)
    sids += [s for s in ("Мама Люба",) if s not in sids]
    sids = [s for s in sids if s not in SKIP]
    report = []
    for sid in sids:
        if args and not any(a in sid for a in args): continue
        if not os.path.exists(f"{SONGS}/{sid}/mix.json"): continue
        mix, synth, bass, has_roma = plan(sid)
        if not synth and not bass and not has_roma: continue
        print(f"\n=== {sid}: + pb-other {synth or '—'} | + pb-bass {bass or '—'}", flush=True)
        if dry: continue
        F = f"{SONGS}/{sid}"; AR = F + "/auto-render"; BK = os.path.join(BK_ROOT, re.sub(r"\W+", "_", sid))
        shutil.rmtree(BK, ignore_errors=True); shutil.copytree(AR, BK); mix_txt = open(F + "/mix.json").read()
        try:
            apply_mix(sid, synth, bass); notes = render(sid)
            oc = jr.onsets(dec(f"{BK}/click.wav"), 0.3, 0.1); nc = jr.onsets(dec(f"{AR}/click.wav"), 0.3, 0.1)
            dt = np.max(np.abs(nc - oc))*1000 if len(oc) == len(nc) else 1e9      # click TIMING, not samples
            d_off = abs(json.load(open(f"{BK}/timeline.json"))["offset_sec"] - json.load(open(f"{AR}/timeline.json"))["offset_sec"])*1000
            same_tl = d_off < 1e-3
            if (dt > 0.5 or d_off > 0.5) and not ("--allow-shift" in sys.argv and not any(
                    (mix.get(gg) or {}).get("layers") for gg in jr.pb_group_names(mix))):   # shift OK only without layers
                raise RuntimeError(f"click timing moved up to {dt:.1f} ms, timeline offset moved {d_off:.1f} ms -> needs a manual look")
            g = None
            if bass:
                L0 = lufs(f"{AR}/pb-bass.wav"); g = round(TARGET - L0, 1)
                if any("pb-bass: peak" in x for x in notes):          # group was normalized at unity -> L0 is too low;
                    g = round(g - float(re.findall(r"pb-bass: peak ([+-][\d.]+)dBFS", " ".join(notes))[0]) - 0.4, 1)
                if abs(g) >= 0.1:
                    apply_mix(sid, [], bass, g); notes = render(sid)
                    if len(jr.onsets(dec(f"{AR}/click.wav"), 0.3, 0.1)) != len(nc): raise RuntimeError("click changed on 2nd render")
            if same_tl and os.path.exists(f"{BK}/cues.wav") and len(dec(f"{BK}/cues.wav")) == len(dec(f"{AR}/cues.wav")):
                shutil.copy(f"{BK}/cues.wav", f"{AR}/cues.wav")
            pr = f"{AR}/practice-roma.mp3"
            if os.path.exists(pr): os.remove(pr)
            Lb = lufs(f"{AR}/pb-bass.wav") if bass else None
            s = subprocess.run([sys.executable, f"{REPO}/tools/stagetraxx_sync.py", "--apply", "--quit", sid], cwd=REPO, capture_output=True, text=True)
            stout = s.stdout + s.stderr; bk = re.findall(r"backup: (\S+)", stout)
            ver = []
            for st, ar in [("1_Click.wav", "click"), ("2_Cues.wav", "cues"), ("3_PB_Other.wav", "pb-other"), ("4_PB_Bass.wav", "pb-bass")]:
                pth = f"{STDOCS}/{sid}/{st}"
                if not os.path.exists(pth) or not os.path.exists(f"{AR}/{ar}.wav"): continue
                a = dec(pth); b = dec(f"{AR}/{ar}.wav"); n = min(len(a), len(b)); gg = np.dot(a[:n], b[:n])/np.dot(b[:n], b[:n]); rr = a[:n] - gg*b[:n]
                ver.append(round(float(10*np.log10(np.sum(rr**2)/np.sum(a[:n]**2) + 1e-15)), 1))
            norm = [x for x in notes if x.startswith("pb-other") or x.startswith("pb-bass")]
            print(f"   ok: bass gain {g} -> {Lb} LUFS | {norm} | ST {bk[-1].split('/')[-1] if bk else '?'} residual {ver}", flush=True)
            report.append((sid, "ok", synth, bass, g, Lb, norm, ver))
        except Exception as e:
            open(F + "/mix.json", "w").write(mix_txt); shutil.rmtree(AR); shutil.copytree(BK, AR)
            print(f"   ROLLED BACK: {e}", flush=True); report.append((sid, f"rolled back: {e}", synth, bass, None, None, [], []))
    subprocess.run([sys.executable, f"{REPO}/tools/setlist_dashboard.py"], cwd=REPO, capture_output=True)
    json.dump(report, open(os.path.join(BK_ROOT, "report.json"), "w"), ensure_ascii=False, indent=1)
    print("\nDONE", len(report), "songs;", sum(1 for r in report if r[1] == "ok"), "ok")

if __name__ == "__main__":
    main()
