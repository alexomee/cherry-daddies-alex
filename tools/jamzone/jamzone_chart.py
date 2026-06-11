#!/usr/bin/env python3
"""
Generate a compact chord/structure chart from a JamZone song's decrypted
tiles.json + structure.json. Key = md5("cat_<id>"); no key capture needed.

Chord decode (validated against the app + diatonic calibration over the library):
  root:  (root mod 100) -> pitch class 1=C..12=B ; root>=100 => flat spelling.
  type_id -> quality (anchored: 1=maj 2=m 8=5(power) 9/39=maj7 10=m7
             11/16/17=dom7 ; remaining ids classed maj/min/dim by diatonic vote).

Usage: jamzone_chart.py <cat_id|query> [more...]
"""
import os, sys, hashlib, subprocess, json, re

JAMS = os.path.expanduser(
    "~/Library/Containers/com.recisio.jamzone.ios/Data/Library/"
    "Application Support/com.recisio.jamzone.ios/jams")
OUT = os.path.expanduser("~/projects/cherry-daddies/music/songs")

SHARP = {1:'C',2:'C#',3:'D',4:'D#',5:'E',6:'F',7:'F#',8:'G',9:'G#',10:'A',11:'A#',12:'B'}
FLAT  = {1:'C',2:'Db',3:'D',4:'Eb',5:'E',6:'F',7:'Gb',8:'G',9:'Ab',10:'A',11:'Bb',12:'Cb'}

# type_id -> chord-quality suffix. Anchored ids are explicit; the rest were
# classed maj('')/min('m')/dim by diatonic voting across the whole library.
QUAL = {1:'',2:'m',6:'m',7:'',8:'5',9:'maj7',10:'m7',11:'7',12:'m',13:'dim',
        14:'m',15:'m',16:'7',17:'7',18:'m',19:'',22:'',23:'m',24:'m',25:'m',
        28:'',34:'m',37:'m',39:'maj7',41:'m',42:'m',48:'m',49:'m',54:'',56:'',
        57:'',58:'',63:'',64:'m',65:'m',70:'m',73:'dim',76:'dim',77:'m',90:'',
        97:'m',98:'m'}
# richness for collapsing two glyphs on the same root (keep the more specific)
RICH = {'maj7':4,'m7':4,'7':4,'dim':3,'m':2,'5':1,'':1}

def keyhex(cat): return hashlib.md5(cat.encode()).hexdigest().encode().hex()

def dec(cat, name):
    d = open(os.path.join(JAMS, cat, name), "rb").read()
    return subprocess.run(["openssl","enc","-aes-256-cbc","-d","-K",keyhex(cat),
                           "-iv",d[:16].hex()], input=d[16:], capture_output=True).stdout

def note(root):
    flat = root >= 100
    b = root - 100 if flat else root
    return (FLAT if flat else SHARP).get(b, '?')

def chord(root, tid):
    return note(root) + QUAL.get(tid, '')

def norm(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '')
    return re.sub(r'[^a-z0-9]', '', s.encode('ascii','ignore').decode().lower())

SECMAP = {
    'intro':'I', 'verse':'V', 'prechorus':'PC', 'chorus':'Ch', 'break':'Br',
    'bridge':'Bri', 'instrumental':'Ins', 'interlude':'Intl', 'outro':'O',
    'solo':'Solo', 'hook':'Hk', 'refrain':'Ref', 'precount':'',
}

def abbrev(cap):
    cap = (cap or '').strip()
    m = re.search(r'(\d+)\s*$', cap)
    num = m.group(1) if m else ''
    base = re.sub(r'\d+\s*$', '', cap).strip().lower()
    ab = SECMAP.get(base.replace(' ', ''))
    if ab is None:
        words = base.split()
        ab = ''.join(w[0] for w in words).upper() if len(words) > 1 else base[:3].capitalize()
    return ab + num

def compress(seq):
    """Express a chord list as (cell) xN when it's a clean repeat."""
    n = len(seq)
    for p in range(1, n//2 + 1):
        if n % p == 0 and all(seq[i] == seq[i % p] for i in range(n)):
            if n // p > 1:
                return f"({' '.join(seq[:p])}) x{n//p}"
            break
    return ' '.join(seq)

def build_chart(cat):
    song = json.loads(dec(cat, "song.json"))
    artist = song.get("artist"); artist = artist.get("en") if isinstance(artist, dict) else artist
    title = song.get("title")
    key = song.get("key") or "?"
    bpm = song.get("bpm") or "?"
    tiles = json.loads(dec(cat, "tiles.json"))

    # collapse consecutive same-root glyphs, keep richest quality, group by section
    sections = []  # (caption, [chords])
    for it in tiles:
        cap = it.get("sectionCaption")
        for sb in it.get("subBeats", []):
            c = sb.get("chords")
            if not c or c.get("chord_is_repetition"):
                continue
            r, tid = c["chord_root"], c["chord_type_id"]
            ch = chord(r, tid)
            if sections and sections[-1][0] == cap and sections[-1][2] == r:
                if RICH.get(QUAL.get(tid,''),0) > RICH.get(sections[-1][3],0):
                    sections[-1][1][-1] = ch; sections[-1][3] = QUAL.get(tid,'')
            else:
                sections.append([cap, [ch], r, QUAL.get(tid,'')])

    # merge into ordered sections (skip Precount / chordless)
    ordered = []
    for cap, chords, *_ in sections:
        if not cap or cap.lower().startswith("precount"):
            continue
        if ordered and ordered[-1][0] == cap:
            ordered[-1][1].extend(chords)
        else:
            ordered.append([cap, list(chords)])

    lines = [f"{artist} - {title}    {key} / {bpm} bpm"]
    chain = "-".join(abbrev(cap) for cap, _ in ordered)
    lines.append(chain)
    lines.append("")
    width = max((len(abbrev(c)) for c, _ in ordered), default=3)
    for cap, chords in ordered:
        lines.append(f"{abbrev(cap):<{width}} : {compress(chords)}")
    return artist, title, "\n".join(lines)

def resolve(q):
    if re.fullmatch(r'cat_\d+', q): return [q]
    nq = norm(q)
    hits = []
    for cat in sorted(os.listdir(JAMS)):
        sj = os.path.join(JAMS, cat, "song.json")
        if not os.path.isfile(sj): continue
        try: s = json.loads(dec(cat, "song.json"))
        except Exception: continue
        a = s.get("artist"); a = a.get("en") if isinstance(a, dict) else a
        if nq in norm(s.get("title")) or nq in norm(f"{a}{s.get('title')}"):
            hits.append(cat)
    return hits

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    for q in sys.argv[1:]:
        for cat in resolve(q):
            artist, title, text = build_chart(cat)
            label = f"{artist} - {title}".replace("/","-").replace(":","-")
            dest = os.path.join(OUT, label)
            os.makedirs(dest, exist_ok=True)
            open(os.path.join(dest, "chart.txt"), "w").write(text + "\n")
            print(text); print(f"  -> {dest}/chart.txt\n")

if __name__ == "__main__":
    main()
