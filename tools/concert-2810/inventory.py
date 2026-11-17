#!/usr/bin/env python3
"""28.10 concert multitrack inventory (all songs). Ch08 "Guitar LR" = Roma keys, ch09 "Keys LR" = Alex guitar."""
import glob, json, os, subprocess, unicodedata, re
import numpy as np

REPO = "/Users/alex/projects/cherry-daddies"
DL = "/Users/alex/Downloads"
ROOTS = [f"{DL}/Cherry Daddies 28.10 raw stems - set1.1-5/Set 1", f"{DL}/Cherry Daddies 28.10 raw stems - set1.6-10/Set 1",
         f"{DL}/Cherry Daddies 28.10 raw stems - set2.1-6/Set 2", f"{DL}/Set 2", f"{DL}/Cherry Daddies 28.10 raw stems - set2.14-17/Set 2"]
MAP = {"Солнце": "Елена Терлеева - Солнце", "Around the World": "A Touch of Class - Around the World (La La La La La)",
       "Беги от меня": "Беги от меня", "Такая любовь": "Такая любовь", "Ту-лу-ла": "Чичерина - Ту-лу-ла",
       "Blinding Lights": "The Weeknd - Blinding Lights", "Whenever, Wherever": "Shakira - Whenever, Wherever",
       "Everytime We Touch": "Cascada - Everytime We Touch", "Destination Calabria": "Alex Gaudino - Destination Calabria",
       "Freed From Desire": "Gala - Freed from Desire", "Beverly Hills": "Beverly Hills",
       "Про красивую жизнь": "Band'Eros - Pro krasivuju zhizn'", "Солнышко": "Demo - Solnyshko", "Я устал": "Quest Pistols - Я устал",
       "Медляк": "Mr. Credo - Медляк", "Мало тебя": "SEREBRO - Malo tebya", "Медведица": "Мумий Тролль - Медведица",
       "Pretty Fly": "The Offspring - Pretty Fly (For A White Guy)", "Кукла колдуна": "Король и Шут - Кукла колдуна",
       "Heads Will Roll": "Yeah Yeah Yeahs - Heads Will Roll", "I Love It": "Icona Pop & Charli XCX - I Love It",
       "Кислотный DJ": "Кислотный DJ", "Мелом": "Мелом", "Я сошла с ума": "t.A.T.u. - Ya Soshla S Uma (Я сошла с ума)",
       "Ghostbusters": "Ray Parker Jr. - Ghostbusters", "Такая любовь (бис)": "Такая любовь", "Беги от меня (бис)": "Беги от меня"}
SNAP = "4e67c9a"   # 2026-11-16: Roma left, before any pb-bass/players edits
SR = 8000; HOP = 40
nfc = lambda s: unicodedata.normalize("NFC", s)

def dec(p):
    r = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()
def active(x):
    n = len(x)//SR
    if n == 0: return 0.0
    r = np.sqrt((x[:n*SR].reshape(n, SR)**2).mean(1)); return float((r > 10**(-45/20)).mean())
def envl(x):
    n = len(x)//HOP; e = np.log(np.sqrt((x[:n*HOP].reshape(n, HOP)**2).mean(1) + 1e-12) + 1e-4); return e - e.mean()
def align(a, b):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b)))); c = np.fft.irfft(np.fft.rfft(a, n)*np.conj(np.fft.rfft(b, n)), n)
    i = int(np.argmax(c)); return (i if i < n//2 else i - n)*HOP/SR, float(c[i]/np.sqrt((a**2).sum()*(b**2).sum()))
def snap_mix(folder):
    r = subprocess.run(["git", "-C", REPO, "show", f"{SNAP}:music/songs/{folder}/mix.json"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {}

bass_assign = {}
src = subprocess.run(["git", "-C", REPO, "show", f"{SNAP}:tools/setlist_dashboard.py"], capture_output=True, text=True).stdout
for m in re.finditer(r'^\s*"([^"]+)":\s*"([^"]+)",', src[src.index("BASS_ASSIGN"):src.index("}", src.index("BASS_ASSIGN"))], re.M):
    bass_assign[m.group(1)] = m.group(2)

rows = []
for root in ROOTS:
    for d in sorted(glob.glob(root + "/*/")):
        base = nfc(os.path.basename(d.rstrip("/"))); num, title = base[:2], base[3:]
        setn = "1" if "/Set 1" in root else "2"
        repo = MAP.get(title); F = f"{REPO}/music/songs/{repo}"
        ch = {nfc(os.path.basename(f))[:2]: f for f in glob.glob(d + "*.wav")}
        act = {k: active(dec(ch[k])) if k in ch else None for k in ("07", "08", "09", "10", "11", "12")}
        cur = json.load(open(F + "/mix.json")); old = snap_mix(repo)
        jz = bool(glob.glob(glob.escape(F) + "/[0-9][0-9]_*.m4a"))
        al = None
        if "14" in ch and os.path.exists(F + "/auto-render/cues.wav"):
            al = align(envl(dec(ch["14"])), envl(dec(F + "/auto-render/cues.wav")))
        rows.append({"set": setn, "num": num, "title": title, "repo": repo, "dir": d, "jamzone": jz, "act": act, "cues_align": al,
                     "roma_old": (old.get("players") or {}).get("roma"), "bass_who": bass_assign.get(repo, ""),
                     "pb_bass_now": cur.get("pb-bass"), "pb_bass_old": old.get("pb-bass"),
                     "pb_other_now": cur.get("pb-other")})
        r = rows[-1]
        f = lambda v: "  —" if v is None else f"{v*100:3.0f}%"
        print(f"S{setn}.{num} {title[:24]:24s} {'JZ' if jz else 'MO'} | bass07 {f(act['07'])} keys08 {f(act['08'])} gtr09 {f(act['09'])} gsyn10 {f(act['10'])} pbB {f(act['11'])} pbO {f(act['12'])}"
              f" | cues {('%+.2fs r%.2f' % al) if al else '—'} | roma {r['roma_old']} | bass.who {r['bass_who'] or '—'} | pb-bass {'yes' if r['pb_bass_old'] else 'no'}->{'yes' if r['pb_bass_now'] else 'no'}")
json.dump(rows, open("/Users/alex/projects/cherry-daddies/analysis/concert-2810/inventory.json", "w"), ensure_ascii=False, indent=1, default=str)
