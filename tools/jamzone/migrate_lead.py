#!/usr/bin/env python3
"""One-off migration for the short render front (2026-11-20, Alex: «слишком долгое вступление»).

jamzone_render.py no longer pads the front to whole bars: the render starts 0.1 s before the
start cue's first word, so every song's OFF (auto-render/timeline.json "offset_sec") shrinks.
Two things are tied to the OLD OFF and are carried over here:

  * render-frame layers (parts/ recorded against auto-render/all.wav) — they get
    "rec_off": <old OFF> in mix.json; the render then shifts them by (new OFF - rec_off).
  * lyric TSVs (tools/lyric-launcher/lyrics-timed/NN.tsv, "<m:ss.xx>\\t<line>" in PLAYBACK time)
    — shifted by the same delta after the re-render (clip NN -> song via songs.tsv).

  python3 tools/jamzone/migrate_lead.py prep  --state S.json [song ...]   # before rendering
  python3 tools/jamzone/migrate_lead.py post  --state S.json [song ...]   # after rendering
  (no songs = every song folder with mix.json + auto-render/timeline.json)

prep records each song's current OFF in the state file (once: a second prep keeps the first value)
and writes rec_off into its render-frame layers (text edit, formatting kept, verified by a
JSON round-trip). post reads the new OFF, shifts the TSVs once (marks the song done in the state)
and prints the per-song deltas. Lyric clips (tools/lyric-launcher/clips) are NOT rebuilt here.
"""
import argparse, csv, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SONGS = os.path.join(REPO, "music", "songs")
LL = os.path.join(REPO, "tools", "lyric-launcher")


def song_dirs(names):
    if names:
        return names
    return sorted(d for d in os.listdir(SONGS)
                  if os.path.isfile(os.path.join(SONGS, d, "mix.json"))
                  and os.path.isfile(os.path.join(SONGS, d, "auto-render", "timeline.json")))


def cur_off(song):
    return json.load(open(os.path.join(SONGS, song, "auto-render", "timeline.json")))["offset_sec"]


def _match_bracket(s, i):
    """index of the bracket closing the one at s[i] ('[' or '{'), skipping strings."""
    open_c = s[i]; close_c = "]" if open_c == "[" else "}"
    depth, j, in_str = 0, i, False
    while j < len(s):
        c = s[j]
        if in_str:
            if c == "\\": j += 1
            elif c == '"': in_str = False
        elif c == '"': in_str = True
        elif c == open_c: depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0: return j
        j += 1
    raise ValueError("unbalanced")


def add_rec_off(text, off):
    """rec_off on every render-frame layer of every "layers" array (string -> object)."""
    out, pos, n = [], 0, 0
    for m in re.finditer(r'"layers"\s*:\s*\[', text):
        a = m.end() - 1; b = _match_bracket(text, a)
        if a < pos: continue
        arr = text[a:b+1]; new = []; k = 1
        while k < len(arr) - 1:
            c = arr[k]
            if c == '"':                                       # "name" = render-frame layer
                e = k + 1
                while arr[e] != '"':
                    e += 2 if arr[e] == "\\" else 1
                new.append(f'{{"file": {arr[k:e+1]}, "rec_off": {off}}}'); n += 1; k = e + 1
            elif c == "{":
                e = _match_bracket(arr, k); obj = arr[k:e+1]; d = json.loads(obj)
                if d.get("frame", "render") == "render" and "rec_off" not in d:
                    fm = re.search(r'"file"\s*:\s*"(?:[^"\\]|\\.)*"', obj)
                    obj = obj[:fm.end()] + f', "rec_off": {off}' + obj[fm.end():]; n += 1
                new.append(obj); k = e + 1
            else:
                new.append(c); k += 1
        out.append(text[pos:a] + "[" + "".join(new) + "]"); pos = b + 1
    out.append(text[pos:])
    return "".join(out), n


def expected(old_obj, off):
    o = json.loads(json.dumps(old_obj))
    for v in o.values():
        if isinstance(v, dict) and isinstance(v.get("layers"), list):
            v["layers"] = [{"file": e, "rec_off": off} if isinstance(e, str) else
                           ({**e, "rec_off": off} if e.get("frame", "render") == "render" and "rec_off" not in e else e)
                           for e in v["layers"]]
    return o


def tsv_for(song):
    rows = list(csv.DictReader(open(os.path.join(LL, "songs.tsv"), encoding="utf-8"), delimiter="\t"))
    return [os.path.join(LL, "lyrics-timed", f"{r['clip']}.tsv") for r in rows
            if r["factory_dir"].rstrip("/").split("/")[-1] == song
            and os.path.isfile(os.path.join(LL, "lyrics-timed", f"{r['clip']}.tsv"))]


def shift_tsv(path, delta):
    def fmt(t):
        t = max(0.0, t); m = int(t // 60); return f"{m}:{t - 60*m:05.2f}"
    lines = open(path, encoding="utf-8").read().split("\n"); n = 0
    for i, l in enumerate(lines):
        mm = re.match(r"^(\d+):(\d+(?:\.\d+)?)\t", l)
        if mm:
            t = int(mm.group(1))*60 + float(mm.group(2)) + delta
            lines[i] = fmt(t) + l[mm.end()-1:]; n += 1
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "post"])
    ap.add_argument("--state", required=True)
    ap.add_argument("songs", nargs="*")
    a = ap.parse_args()
    st = json.load(open(a.state)) if os.path.exists(a.state) else {}
    for song in song_dirs(a.songs):
        rec = st.setdefault(song, {})
        if a.cmd == "prep":
            rec.setdefault("old_off", cur_off(song))
            p = os.path.join(SONGS, song, "mix.json"); txt = open(p, encoding="utf-8").read()
            new, n = add_rec_off(txt, rec["old_off"])
            if n:
                if json.loads(new) != expected(json.loads(txt), rec["old_off"]):
                    sys.exit(f"{song}: rec_off edit does not round-trip — not written")
                open(p, "w", encoding="utf-8").write(new)
            print(f"prep  {song}: old OFF {rec['old_off']:.4f}" + (f", rec_off on {n} layer(s)" if n else ""))
        else:
            if "old_off" not in rec:
                print(f"post  {song}: not prepped — skipped"); continue
            new_off = cur_off(song); d = round(new_off - rec["old_off"], 6); rec["new_off"] = new_off
            msg = f"post  {song}: OFF {rec['old_off']:.4f} -> {new_off:.4f} ({d:+.3f}s)"
            if not rec.get("tsv_done") and abs(d) > 1e-6:      # (a failed render leaves OFF as is:
                for t in tsv_for(song):                         #  nothing shifted, retried next post)
                    msg += f", {os.path.basename(t)} {shift_tsv(t, d)} lines shifted"
                rec["tsv_done"] = True
            print(msg)
        json.dump(st, open(a.state, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
