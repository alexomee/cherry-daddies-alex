#!/usr/bin/env python3
"""Write parts with the ZENOLOGY plugin instead of the GM-800 (wiki/pipelines/zenology.md; Alex 2026-11-20:
«упор на то, чтобы снять ограничение в аппарате, когда ты партии снимаешь», and the tones are for me to choose
and bring him as variants). ZEN-Core is the engine of both; a tone goes ZENOLOGY -> GM-800 as an .svz file
(not back), so a sound found here can also be played live.

    zr() { uv run -q --python 3.12 --with pedalboard --with mido --with numpy --with soundfile --with scipy \
           --with librosa --with pyobjc-framework-Cocoa --with pyobjc-framework-Quartz --with pyobjc-framework-Vision \
           tools/zenology_render.py "$@"; }
    zr catalog [--banks PRST_[AB]]   # walks the plugin's banks by itself (chooses a bank and clicks "next tone" in
                                     #   the plugin window, reads number / category off it, the name out of the
                                     #   state), keeps every tone's state -> gear/zenology/catalog.tsv + state cache
    zr list [--cat "Synth Lead"] [--name pulse] [--bank PRST]            # the catalog, filtered
    zr sweep "<song>" NOTES.json riff 105 109 --cat "Synth Lead,Synth PolyKey" [--name re] [--bank re] [--top 12]
                                     # a voice on every matching tone, no window, faster than real time, ranked
                                     #   against the song's stems like gm800_part.py sweep; the best takes stay
    zr page "<song>" NOTES.json      # listening page of this song's sweeps: original + the best takes per voice
    zr render "PRST_B AX Collection/196" "<song>" NOTES.json riff 105 109 out.wav [--vel 100]
    zr record "<song>" NOTES.json    # the layer takes that name a plugin tone ("zen": "BANK/NUMBER{edits}") -> take
                                     #   files for gm800_part.py layer: a playback voice without the GM-800
    zr index                         # once: a fingerprint of every tone (probe notes) -> sweep plays only the
                                     #   --pre 150 tones the fingerprints promise most of; gear/zenology/traits.tsv
    zr pick NAME                     # by hand: opens the window, the chosen tone -> gear/zenology/states/NAME.bin
    zr variant "<song>" NOTES.json riff 105 109 "PRST_A Factory Presets/32{p1.level=0}" --name "Sunrise без слоя"
                                     # an EDITED tone as one more take of that sweep (next to its tone on the page)

A tone can be edited wherever a tone is named: "BANK/NUMBER{p1.level=0,p*.release=300}" sets parameters of
partials 1..4 (p* = all four) in the state before it is loaded (PARTIAL below: the ones found and measured so far).

How it works. The plugin has no "select tone" parameter and ignores bank / program change without its window
(measured 2026-11-20), but its whole state can be read and set (pedalboard raw_state): a flat list of
address -> value, the tone name at 0x1130. So `catalog` opens the window ONCE, steps through the tones with clicks
sent inside the process (no accessibility permission, the window need not be in front), and saves each state;
after that a tone is loaded from its saved state with no window at all. Sample 0 of a render is the bar line of
b0, as in a GM-800 take; there is no USB latency to take out.
"""
import argparse, importlib.util, json, os, sys, time
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = "/Library/Audio/Plug-Ins/VST3/Roland/ZENOLOGY.vst3"
STATES = os.path.join(REPO, "gear", "zenology", "states")          # states picked by hand (`pick`)
CATALOG = os.path.join(REPO, "gear", "zenology", "catalog.tsv")    # bank, number, name, model, category, file
CACHE = os.path.expanduser("~/.cache/cherry-daddies/zenology/states")   # one zlib'd plugin state a tone, not in git
SR = 48000                                   # same as the GM-800 takes
# Places in the plugin window, in POINTS from the top left of its content. They are the same in every view (compact
# BASIC 464 x 227, with the on-screen keyboard 464 x 337, BROWSE 1009 x 624); shares of the size are not (2026-11-21).
NEXT, PREV = (94, 102), (94, 81)             # the down / up arrows beside the tone name
ALPHA = {c: i for i, c in enumerate(b".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+")}


def state_name(st):
    """Tone name out of a plugin state: <IComponent> is JUCE base64 (6 bits a char, LSB first) of (address u32,
    value u32) records after a 4-byte length; the 16 characters of the name sit at 0x1130, 4 apart."""
    import re, struct
    m = re.search(rb"<IComponent>(\d+)\.([^<]*)</IComponent>", st); n = int(m.group(1)); out = bytearray(n + 2); pos = 0
    for c in m.group(2):
        v = ALPHA.get(c)
        if v is None:
            continue
        byte, bit = divmod(pos, 8); x = v << bit
        if byte >= n:
            break
        out[byte] |= x & 0xFF; out[byte + 1] |= x >> 8; pos += 6
        if byte > 4 + 8 * 4096:              # the name is among the first records: no need to decode 160 kB
            break
    rec = {}
    for i in range(4, min(n, 4 + 8 * 4096) - 7, 8):
        a, v = struct.unpack(">II", out[i:i + 8]); rec[a] = v
    return "".join(chr(rec.get(0x1130 + 4 * k, 32)) if 32 <= rec.get(0x1130 + 4 * k, 32) < 127 else "?" for k in range(16)).rstrip()


# A partial's parameters in the state: records at 80000 + 40000 * (partial - 1) + offset. Found on "Sunrise"
# (PRST_A 32) and measured 2026-11-21: level 0 silences the partial; coarse moves it by semitones; keyfollow 0 = the
# partial sounds at ONE pitch whatever key is played (a bell sample there, heard as "an accompaniment out of tune"),
# 100 = it follows the keys; release = how long a note rings after the key is let go, 0..1023 (Sunrise 658/772: -20 dB
# only after 0.9 s and a tail of seconds, so the notes of a riff pile up into a chord; 500 -> -20 dB in 0.38 s,
# 400 -> 0.22, 300 -> 0.16, 200 -> 0.11). Offset 48 of the block is the PCM wave number, 1024 the filter cutoff
# (read only so far).
PARTIAL = {"level": 900, "coarse": 904, "keyfollow": 1012, "release": 556}


def state_edit(st, edits):
    """The state with some records set: edits = "p1.level=0,p1.coarse=-31" (PARTIAL) or {address: value}."""
    import re, struct
    if isinstance(edits, str):
        ed = {}
        for e in filter(None, (x.strip() for x in edits.split(","))):
            m = re.match(r"^p([1-4*])\.(\w+)=(-?\d+)$", e)                     # p* = every partial
            if not m or m.group(2) not in PARTIAL:
                raise SystemExit(f"tone edit '{e}': expected pN.{{{'|'.join(PARTIAL)}}}=VALUE (N = 1..4 or *)")
            for k in (range(4) if m.group(1) == "*" else [int(m.group(1)) - 1]):
                ed[80000 + 40000 * k + PARTIAL[m.group(2)]] = int(m.group(3))
        edits = ed
    m = re.search(rb"<IComponent>(\d+)\.([^<]*)</IComponent>", st); n = int(m.group(1)); raw = bytearray(n + 2); pos = 0
    for c in m.group(2):
        v = ALPHA.get(c)
        if v is None:
            continue
        byte, bit = divmod(pos, 8)
        if byte >= n:
            break
        x = v << bit; raw[byte] |= x & 0xFF; raw[byte + 1] |= x >> 8; pos += 6
    raw[n:] = b"\0\0"; left = dict(edits)
    for i in range(4, n - 7, 8):
        a = struct.unpack(">I", raw[i:i + 4])[0]
        if a in left:
            raw[i + 4:i + 8] = struct.pack(">i", left.pop(a))
    if left:
        raise SystemExit(f"tone edit: no record at {sorted(left)} in this state")
    inv = {i: c for c, i in ALPHA.items()}
    chars = bytes(inv[((raw[k * 6 // 8] | raw[k * 6 // 8 + 1] << 8) >> (k * 6 % 8)) & 63] for k in range((n * 8 + 5) // 6))
    return st[:m.start(2)] + chars + st[m.end(2):]


def read_catalog():
    if not os.path.exists(CATALOG):
        return []
    return [dict(zip(("bank", "number", "name", "model", "category", "file"), l.rstrip("\n").split("\t")))
            for l in open(CATALOG, encoding="utf-8") if l.strip() and not l.startswith("#")]


def tone_state(tag):
    """Plugin state of a tone: 'BANK/NUMBER' or a unique part of it from the catalog, else a hand-picked state;
    '...{p1.level=0}' edits it (state_edit)."""
    import zlib
    tag, _, ed = tag.partition("{"); tag = tag.strip(); edit = (lambda st: state_edit(st, ed.rstrip("}"))) if ed else (lambda st: st)
    rows = [r for r in read_catalog() if f"{r['bank']}/{r['number']}" == tag] or \
           [r for r in read_catalog() if tag.lower() in f"{r['bank']}/{r['number']} {r['name']}".lower()]
    if len(rows) == 1:
        return edit(zlib.decompress(open(os.path.join(CACHE, rows[0]["file"]), "rb").read())), rows[0]
    if os.path.exists(state_path(tag)):
        return edit(open(state_path(tag), "rb").read()), {"bank": "hand", "number": tag, "name": str(tag), "category": ""}
    raise SystemExit(f"tone '{tag}': {len(rows)} catalog matches {[r['bank'] + '/' + r['number'] + ' ' + r['name'] for r in rows[:8]]}")


def state_path(tag):
    return os.path.join(STATES, f"t{int(tag):04d}.bin" if str(tag).isdigit() else f"{tag}.bin")


def plugin(tag=None):
    from pedalboard import load_plugin
    p = load_plugin(PLUGIN)
    if tag is not None:
        p.raw_state = tone_state(tag)[0]
    return p


def cmd_pick(tag):
    p = plugin(); os.makedirs(STATES, exist_ok=True)
    keep_on_top()
    print(f"ZENOLOGY window is open: choose the tone for '{tag}', then CLOSE the window.", flush=True)
    p.show_editor()                          # blocks until the window is closed
    open(state_path(tag), "wb").write(p.raw_state)
    print("saved", state_path(tag), len(p.raw_state), "bytes")


def keep_on_top():
    """The editor of a plugin hosted by a bare python process has no Dock icon and cannot be brought to the front:
    once another window is clicked it is lost behind it (2026-11-20). So: a regular app (Dock icon, Cmd-Tab) and
    every window of it floating above the others, set by a timer that runs inside the editor's own run loop."""
    from AppKit import NSApplication, NSTimer, NSRunLoop, NSRunLoopCommonModes
    app = NSApplication.sharedApplication(); app.setActivationPolicy_(0)
    state = {"n": 0}
    def tick(_):
        for w in app.windows():
            if w.level() != 3:
                w.setLevel_(3); w.setHidesOnDeactivate_(False)
        if state["n"] < 3:
            app.activateIgnoringOtherApps_(True)
        state["n"] += 1
    t = NSTimer.timerWithTimeInterval_repeats_block_(0.5, True, tick)
    NSRunLoop.mainRunLoop().addTimer_forMode_(t, NSRunLoopCommonModes)


class Window:
    """The plugin's editor driven from a worker thread while show_editor() blocks the main one."""
    def __init__(self, p):
        import queue, threading
        from AppKit import NSApplication
        self.p, self.app, self.q, self.close = p, NSApplication.sharedApplication(), queue.Queue(), threading.Event()
        from AppKit import NSProcessInfo      # no App Nap: a window that is behind others would have its run loop
        self.awake = NSProcessInfo.processInfo().beginActivityWithOptions_reason_(0x00FFFFFF | 0xFF00000000, "walking the tones")
        # throttled, and a walk that takes half a second a tone stalls for minutes (2026-11-21)

    def main(self, fn):                       # run fn on the main thread, wait for its result
        from PyObjCTools import AppHelper
        AppHelper.callAfter(lambda: self.q.put(fn())); return self.q.get(timeout=30)

    def win(self):
        return max((w for w in self.app.windows() if w.isVisible()), key=lambda w: w.frame().size.width * w.frame().size.height)

    def click(self, rel):
        from AppKit import NSEvent, NSProcessInfo
        def f():
            w = self.win(); b = w.contentView().bounds(); pt = (rel[0], b.size.height - rel[1])
            for typ in (1, 2):                # left mouse down, up - sent inside the process
                w.sendEvent_(NSEvent.mouseEventWithType_location_modifierFlags_timestamp_windowNumber_context_eventNumber_clickCount_pressure_(
                    typ, pt, 0, NSProcessInfo.processInfo().systemUptime(), w.windowNumber(), None, 0, 1, 1.0))
        self.main(f)

    def state(self):
        return self.main(lambda: self.p.raw_state)

    def read(self):
        """(bank, number, name, model, category) as the window shows them: the plugin's view drawn into a bitmap
        inside the process and read by Vision OCR. Not a screen capture - that comes back empty as soon as the
        screen locks or the display sleeps (2026-11-21, the first night walk stopped on it)."""
        import re, Vision
        def draw():
            v = self.win().contentView(); b = v.bounds(); rep = v.bitmapImageRepForCachingDisplayInRect_(b)
            v.cacheDisplayInRect_toBitmapImageRep_(b, rep); return rep.CGImage()
        req = Vision.VNRecognizeTextRequest.alloc().init(); req.setRecognitionLevel_(0); req.setUsesLanguageCorrection_(False)
        Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(self.main(draw), None).performRequests_error_([req], None)
        t = [(o.boundingBox().origin.x, o.boundingBox().origin.y, o.topCandidates_(1)[0].string().strip()) for o in req.results()]
        num = next(((x, y, s) for x, y, s in t if re.match(r"^\d+\s*:", s)), None)                 # "196: AX Viola"
        bank = next(((x, y, s) for x, y, s in t if s.endswith(":") and num and 0.03 < y - num[1] < 0.2 and abs(x - num[0]) < 0.05), None)
        if not num or not bank:
            return "", "", "", "", ""
        row = sorted((x, s) for x, y, s in t if abs(y - bank[1]) < 0.03 and x > bank[0] + 0.05)     # model | category
        m = re.match(r"^(\d+)\s*:\s*(.*)$", num[2])
        return bank[2].rstrip(":").strip(), m.group(1), m.group(2).strip(), (row[0][1] if row else ""), (row[1][1] if len(row) > 1 else "")


BANKS = ["PRST_A Factory Presets", "PRST_B AX Collection", "PRST_C Synth Legend", "PRST_D Basic Synth", "PRST_E XV Collection",
         "PRST_F Essential", "PRST_G Essential Drum", "PRST_H Stellar Black", "PRST_I Sun Gate", "PRST_J Nebulous Forms",
         "PRST_K Volatile Memories", "PRST_L Essential 2", "ZEZ001 Hazy Pop", "ZEZ002 Dark Adaptations", "ZEZ003 Liquid"]
# BROWSE view (1009 x 624): the bank list as it opens, unscrolled - the 12 PRST banks, a rule, then the first packs.
# Banks further down (SDZ / EXM / EXZ ...) need the list scrolled: not written yet.
BANK_XY = lambda k: (90, 201.5 + 27.72 * k - (0 if k < 12 else 0.7))
BANK_ALL = (26, 174)
TAB_BROWSE, TAB_BASIC, FIRST_ROW = (139, 21.5), (200, 21.5), (660, 64.5)             # tabs; the first tone of the BROWSE list


def cmd_catalog(a):
    """Bank by bank: BROWSE, click the bank, click its first tone, back to the compact view, then "next tone" until
    the bank ends. Tones already in the catalog are walked over without saving, so a run can be repeated."""
    import difflib, re, threading, zlib
    p = plugin(); os.makedirs(CACHE, exist_ok=True); os.makedirs(os.path.dirname(CATALOG), exist_ok=True)
    seen = {(r["bank"], int(r["number"])) for r in read_catalog()}; W = Window(p)
    want = [k for k, b in enumerate(BANKS) if re.search(a.banks, b, re.I) and "Drum" not in b]
    norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())
    def walk(bank):
        done, last, t0 = 0, None, time.time()
        while done < a.max:
            for k in range(10):                                    # the window settles a moment after the click
                st = W.state(); nm = state_name(st); _, num, shown, model, cat = W.read()
                ok = num.isdigit() and int(num) != last and difflib.SequenceMatcher(None, norm(shown), norm(nm)).ratio() > 0.5
                if ok or (k >= 7 and num.isdigit() and int(num) != last):   # the number moved on; OCR of the name may be off
                    break
                time.sleep(0.12)
            else:
                return done                                        # the arrow no longer moves: end of the bank
            last = int(num)
            if (bank, last) not in seen:
                fn = re.sub(r"[^A-Za-z0-9]+", "_", bank).strip("_") + f"-{last:04d}.z"
                open(os.path.join(CACHE, fn), "wb").write(zlib.compress(st, 6)); seen.add((bank, last)); done += 1
                with open(CATALOG, "a", encoding="utf-8") as f:
                    f.write("\t".join([bank, str(last), nm, model, cat, fn]) + "\n")
                if done % 100 == 0:
                    print(f"    {bank}: {done} new, at {last} {nm} [{cat}], {(time.time() - t0) / done:.2f} s a tone", flush=True)
            W.click(NEXT); time.sleep(a.delay)
        return done
    def work():
        try:
            time.sleep(7)
            finished = {l[7:].strip() for l in open(CATALOG, encoding="utf-8") if l.startswith("# done ")} if os.path.exists(CATALOG) else set()
            for k in want:
                if BANKS[k] in finished:
                    print(f"  {BANKS[k]}: walked to its end before - skipped", flush=True); continue
                W.click(TAB_BROWSE); time.sleep(1.5)
                W.click(BANK_ALL); time.sleep(1.0)                 # the bank list is multi-select: a click ADDS a bank to the
                W.click(BANK_XY(k)); time.sleep(1.2)               # filter, so clear it with "All" first
                for _ in range(4):
                    W.click(FIRST_ROW); time.sleep(1.2); shown_bank = W.read()[0]
                    if norm(shown_bank)[:6] == norm(BANKS[k])[:6]:
                        break
                W.click(TAB_BASIC); time.sleep(1.2)
                if norm(shown_bank)[:6] != norm(BANKS[k])[:6]:
                    print(f"  {BANKS[k]}: the window shows {shown_bank!r} after choosing it - skipped", flush=True); continue
                n = walk(BANKS[k]); print(f"  {BANKS[k]}: +{n} tones ({sum(1 for b, _ in seen if b == BANKS[k])} in the catalog)", flush=True)
                with open(CATALOG, "a", encoding="utf-8") as f:
                    f.write(f"# done {BANKS[k]}\n")
            print(f"catalog: {len(seen)} tones -> {CATALOG}", flush=True)
        except Exception as e:
            print("catalog stopped by an error:", repr(e), flush=True)
        W.close.set()
    threading.Thread(target=work, daemon=True).start()
    p.show_editor(W.close)


def select(a):
    import re
    rows = read_catalog()
    if a.cat:
        cats = [c.strip().lower() for c in a.cat.split(",")]; rows = [r for r in rows if r["category"].lower() in cats]
    if a.name:
        rows = [r for r in rows if re.search(a.name, r["name"], re.I)]
    if a.bank:
        rows = [r for r in rows if re.search(a.bank, r["bank"], re.I)]
    if getattr(a, "where", ""):                              # by the numbers of traits.tsv: "bright<3,attack_ms>15,release_s<0.5"
        tr = {}
        for l in list(open(TRAITS, encoding="utf-8"))[1:]:
            c = l.rstrip("\n").split("\t"); tr[(c[0], c[1])] = dict(zip(TRAIT_COLS, map(float, c[4:])))
        for cl in filter(None, (x.strip() for x in a.where.split(","))):
            m = re.match(r"^(\w+)\s*([<>])\s*(-?[\d.]+)$", cl)
            if not m or m.group(1) not in TRAIT_COLS:
                raise SystemExit(f"--where '{cl}': expected one of {TRAIT_COLS} then < or > and a number")
            k, op, v = m.group(1), m.group(2), float(m.group(3))
            rows = [r for r in rows if (r["bank"], r["number"]) in tr and ((tr[(r["bank"], r["number"])][k] < v) if op == "<" else (tr[(r["bank"], r["number"])][k] > v))]
    return rows


def cmd_list(a):
    import collections
    rows = select(a)
    if not (a.cat or a.name or a.bank or a.where):
        print(len(rows), "tones;", ", ".join(f"{c} {n}" for c, n in collections.Counter(r["category"] for r in rows).most_common()))
        print("banks:", ", ".join(f"{b} {n}" for b, n in collections.Counter(r["bank"] for r in rows).items())); return
    for r in rows:
        print(f"{r['bank']}/{r['number']:>4}  {r['name']:18} {r['category']}")
    print(len(rows), "tones")


def cmd_sweep(a):
    """A voice on every selected tone, offline; ranked against the song's stems the way gm800_part.py sweep does."""
    import zlib, soundfile as sf
    from mido import Message
    gp, sg = gp_song(a.song); part = json.load(open(a.notes, encoding="utf-8")); rows = select(a)[:a.limit]
    if not rows:
        raise SystemExit("no tones selected (zr list shows the categories)")
    line = gp.voice_line(sg, part, a.voice, a.b0, a.b1); dur = (a.b1 - a.b0) * sg.bar + 1.0
    ev = sorted([Message("note_on", note=n, velocity=a.vel, time=t) for t, n, d in line] + [Message("note_off", note=n, time=t + d) for t, n, d in line],
                key=lambda m: (m.time, m.type == "note_on"))
    ref = sum(sg.read(f"{st}.wav", sg.t_stem(a.b0), sg.t_stem(a.b0) + dur) for st in part["stems"]).mean(1); R = gp.cqt_db(ref)
    tried = len(rows)
    if a.pre and len(rows) > a.pre:                          # fingerprints first: only the promising tones are played
        rows, _ = prefilter(gp, sg, rows, line, R, a.pre)
    p = plugin(); out = os.path.join(sg.out, "zenology"); os.makedirs(out, exist_ok=True); res = []; t0 = time.time()
    for i, r in enumerate(rows, 1):
        p.raw_state = zlib.decompress(open(os.path.join(CACHE, r["file"]), "rb").read())
        p([], duration=1.5, sample_rate=SR, reset=False)       # the last tone's tails die away; reset=True would re-initialise
                                                               # the plugin: 9 s a tone against 0.06 s (measured 2026-11-21)
        x = p(ev, duration=dur, sample_rate=SR, reset=False).T.astype(np.float32); m = x.mean(1)
        if np.sqrt((m ** 2).mean()) < 1e-4:
            continue
        sc, sp, tf, o = gp.sweep_score(R, gp.cqt_db(m), sg.semi); res.append((sc, sp, tf, o, r, x))
        res.sort(key=lambda v: -v[0]); res = [(*v[:5], v[5] if k < a.top else None) for k, v in enumerate(res)]   # audio of the best only
        if i % 25 == 0:
            print(f"  {i}/{len(rows)}  {(time.time() - t0) / i:.2f} s a tone", flush=True)
    tag = f"zen-{os.path.basename(a.notes).replace('.notes.json', '')}-{a.voice}-{a.b0}-{a.b1}"
    if not a.dirty:                      # the takes that go to the page are played again, each alone: reset (nothing of the
        best = []                        # tone before in the delay lines - a sweep take carries its tails) and clean_take
        for sc, sp, tf, o, r, x in res[:a.top]:      # (no dropped notes); about 12 s a tone. The score is taken again too.
            p.raw_state = zlib.decompress(open(os.path.join(CACHE, r["file"]), "rb").read()); p([], duration=0.5, sample_rate=SR, reset=True)
            x, dev, n = clean_take(p, ev, dur); sc, sp, tf, o = gp.sweep_score(R, gp.cqt_db(x.mean(1)), sg.semi); best.append((sc, sp, tf, o, r, x))
        res = sorted(best, key=lambda v: -v[0]) + res[a.top:]
    print(f"{tag}: {len(res)} tones of {len(rows)}, best first (spec = mean spectrum, tf = time x frequency, oct = octaves off)")
    top = []
    for k, (sc, sp, tf, o, r, x) in enumerate(res[:a.top]):
        fn = f"{tag}-{r['file'][:-2]}.wav"; sf.write(os.path.join(out, fn), x, SR, subtype="PCM_16")
        top.append({"bank": r["bank"], "number": r["number"], "name": r["name"], "category": r["category"], "score": round(sc, 3), "oct": o, "file": fn})
        print(f"  {r['bank']}/{r['number']:>4}  {r['name']:18} {r['category']:16} score {sc:.3f}  spec {sp:.3f}  tf {tf:.3f}  oct {o:+d}")
    json.dump({"voice": a.voice, "bars": [a.b0, a.b1], "stems": part["stems"], "tried": tried, "played": len(rows), "top": top,
               "all": [{"tone": f"{v[4]['bank']}/{v[4]['number']}", "name": v[4]["name"], "score": round(v[0], 3)} for v in res]},
              open(os.path.join(out, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"takes of the best {len(top)} and the ranking: {out}/{tag}*")


# ---- fingerprints: every tone analysed ONCE, so a sweep does not have to play all of them (Alex 2026-11-21:
# «никакого предварительного анализа нет? зачем каждый раз все 1000 проверять») ----
INDEX = os.path.expanduser("~/.cache/cherry-daddies/zenology/index")   # fingerprints, a few .npz shards; not in git
TRAITS = os.path.join(REPO, "gear", "zenology", "traits.tsv")          # what the fingerprints say in numbers; in git
PROBES = [(36, 0.75), (48, 0.75), (66, 0.75), (72, 0.75), (60, 1.5)]   # (note, seconds held), then as long of release
FPS = 22050 / 512                                                      # frames a second of a fingerprint
TRAIT_COLS = ("level", "attack_ms", "sustain_db", "release_s", "bright", "fixed", "wobble")
SHARD = 300


def probe_plan():
    """[(note, start s, held s)] of the probe phrase and its length."""
    t, plan = 0.0, []
    for n, h in PROBES:
        plan.append((n, t, h)); t += 2 * h + 0.75      # a pause, so a long release does not run into the next probe
    return plan, t


def fingerprint(p, gp, state):
    """The probe notes played by a tone -> (their CQT picture: gm800_part.cqt_db at every 2nd frame, uint8 in
    0.25 dB; traits). None for a tone that stays silent. The picture is what `emulate` builds a voice from."""
    from mido import Message
    plan, dur = probe_plan(); p.raw_state = state; p([], duration=1.5, sample_rate=SR, reset=False)
    ev = sorted([Message("note_on", note=n, velocity=100, time=t) for n, t, h in plan] + [Message("note_off", note=n, time=t + h) for n, t, h in plan],
                key=lambda m: (m.time, m.type == "note_on"))
    m = p(ev, duration=dur, sample_rate=SR, reset=False).mean(0).astype(np.float32); rms = float(np.sqrt((m ** 2).mean()))
    if rms < 1e-4:
        return None
    nf = int(dur * FPS); D = gp.cqt_db(m)[:, ::2]; D = np.pad(D, ((0, 0), (0, max(0, nf - D.shape[1]))))[:, :nf]
    _, t0, h = plan[-1]; w = int(0.01 * SR); env = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, "same")) + 1e-9
    seg, rel = env[int(t0 * SR):int((t0 + h) * SR)], env[int((t0 + h) * SR):int((t0 + 2 * h) * SR)]; pk = seg.max()
    low = np.nonzero(rel < seg[-int(0.05 * SR):].mean() * 0.1)[0]; tail = 20 * np.log10(seg[int(0.5 * SR):] / pk)
    pw = lambda note: (lambda a, hh: np.where(D[:, int(a * FPS):int((a + hh) * FPS)] > 0, 10 ** (D[:, int(a * FPS):int((a + hh) * FPS)] / 10), 0).mean(1))(
        *next((t, hh) for n, t, hh in plan if n == note))
    s60, s66 = pw(60), pw(66)
    traits = [20 * np.log10(rms),                                         # level, dBFS
              float(np.argmax(seg >= 0.8 * pk)) / SR * 1000,              # attack: ms to 80 % of the peak
              20 * np.log10(seg[-int(0.1 * SR):].mean() / pk),            # sustain: the end of a 1.5 s note against its peak, dB
              (low[0] / SR) if len(low) else h,                           # release: s to -20 dB after the key is let go (1.5 = longer)
              float((np.arange(len(s60)) * s60).sum() / (s60.sum() + 1e-12)) / 3 + 24 - 60,   # brightness: centre of the spectrum, semitones above the note
              float(np.minimum(s60 / (s60.sum() + 1e-12), s66 / (s66.sum() + 1e-12)).sum()),  # fixed: share of the sound that does NOT move with the key
              float(np.std(tail - np.polyval(np.polyfit(np.arange(len(tail)), tail, 1), np.arange(len(tail)))))]  # wobble: dB the held note pulses by
    return np.round(D * 4).astype(np.uint8), np.array(traits, np.float32)


def shard_path(bank, start):
    import re
    return os.path.join(INDEX, re.sub(r"[^A-Za-z0-9]+", "_", bank).strip("_") + f"-{start:04d}.npz")


def cmd_index(a):
    """Fingerprints of every tone of the catalog (once; a re-run adds only the tones that have none): shards of 300
    tones in several processes, then gear/zenology/traits.tsv. About 0.3 s a tone a process."""
    import re, subprocess, zlib, collections, concurrent.futures as cf
    os.makedirs(INDEX, exist_ok=True); by = collections.defaultdict(list)
    for r in read_catalog():
        by[r["bank"]].append(r)
    if a.shard:                                                            # a worker: one shard
        bank, start = a.shard.rsplit("|", 1); rows = by[bank][int(start):int(start) + SHARD]; gp = gp_mod()
        p = plugin(); nums, F, T = [], [], []
        for r in rows:
            fp = fingerprint(p, gp, zlib.decompress(open(os.path.join(CACHE, r["file"]), "rb").read()))
            if fp is not None:
                nums.append(int(r["number"])); F.append(fp[0]); T.append(fp[1])
        np.savez_compressed(shard_path(bank, int(start)), numbers=np.array(nums), F=np.stack(F) if F else np.zeros((0, 252, 1), np.uint8),
                            T=np.stack(T) if T else np.zeros((0, len(TRAIT_COLS)), np.float32), tried=len(rows))
        print(f"  {bank} from {start}: {len(nums)} of {len(rows)} tones", flush=True); return
    todo = [(b, s) for b, rows in by.items() if re.search(a.banks, b, re.I) for s in range(0, len(rows), SHARD)
            if a.redo or not os.path.exists(shard_path(b, s))]
    print(f"index: {len(todo)} shards to make, {a.jobs} at a time", flush=True); t0 = time.time()
    run = lambda bs: subprocess.run([sys.executable, os.path.abspath(__file__), "index", "--shard", f"{bs[0]}|{bs[1]}"])
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(run, todo))
    idx = load_index(); cat = {f"{r['bank']}/{r['number']}": r for r in read_catalog()}
    with open(TRAITS, "w", encoding="utf-8") as f:
        f.write("\t".join(("bank", "number", "name", "category") + TRAIT_COLS) + "\n")
        for k, r in cat.items():
            if k in idx:
                f.write("\t".join([r["bank"], r["number"], r["name"], r["category"]] + [f"{v:.3g}" for v in idx[k][1]]) + "\n")
    print(f"index: {len(idx)} of {len(cat)} tones have a fingerprint, {time.time() - t0:.0f} s -> {INDEX}, {TRAITS}")


def gp_mod():
    s = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
    gp = importlib.util.module_from_spec(s); s.loader.exec_module(gp); return gp


def load_index(banks=None):
    """{'BANK/NUMBER': (fingerprint, traits)} of the shards (of some banks only: a shard is 30 MB in memory)."""
    import glob, re, collections
    by = collections.defaultdict(list); out = {}
    for r in read_catalog():
        by[r["bank"]].append(r)
    for bank in by:
        if banks is not None and bank not in banks:
            continue
        for s in range(0, len(by[bank]), SHARD):
            if os.path.exists(shard_path(bank, s)):
                z = np.load(shard_path(bank, s))
                for n, F, T in zip(z["numbers"], z["F"], z["T"]):
                    out[f"{bank}/{n}"] = (F, T)
    return out


def emulate(F, line, nf):
    """The CQT picture (cqt_db scale, every 2nd frame) a tone would give on a voice, put together from its
    fingerprint: every note = the nearest probe note moved to its pitch, cut or held to its length, with the
    probe's release after it. No plugin: a few ms a tone. Good enough to throw out the tones that cannot match;
    the ones that stay are played for real."""
    A = np.where(F > 0, 10.0 ** ((F.astype(np.float32) / 4 - 60) / 10), 0).astype(np.float32)      # power
    P = np.zeros((F.shape[0], nf), np.float32); plan, _ = probe_plan(); lev = A.sum(0) + 1e-12
    for t, n, d in line:
        q, t0, h = min(plan, key=lambda v: abs(v[0] - n)); a, hf = int(round(t0 * FPS)), int(round(h * FPS))
        df = max(1, int(round(d * FPS)))
        if df <= hf:
            note = np.concatenate([A[:, a:a + df], A[:, a + hf:a + 2 * hf] * min(16.0, lev[a + df - 1] / lev[a + hf - 1])], 1)
        else:
            note = np.concatenate([A[:, a:a + hf], np.repeat(A[:, a + hf - 1:a + hf], df - hf, 1), A[:, a + hf:a + 2 * hf]], 1)
        k, f = 3 * (n - q), int(round(t * FPS)); L = min(note.shape[1], nf - f)
        if L <= 0 or abs(k) >= F.shape[0]:
            continue
        if k >= 0:
            P[k:, f:f + L] += note[:F.shape[0] - k, :L]
        else:
            P[:k, f:f + L] += note[-k:, :L]
    D = 10 * np.log10(P + 1e-12); return np.maximum(D - (D.max() - 60), 0)


def prefilter(gp, sg, rows, line, R, keep):
    """The `keep` tones whose fingerprints promise the best match with the stems, plus the tones that have no
    fingerprint yet. -> (rows to play, [(predicted score, row)] of all)"""
    idx = load_index({r["bank"] for r in rows}); R2 = R[:, ::2]; t0 = time.time(); sc, rest = [], []
    for r in rows:
        fp = idx.get(f"{r['bank']}/{r['number']}")
        if fp is None:
            rest.append(r)
        else:
            sc.append((gp.sweep_score(R2, emulate(fp[0], line, R2.shape[1]), sg.semi)[0], r))
    sc.sort(key=lambda v: -v[0])
    print(f"fingerprints: {len(sc)} tones ranked in {time.time() - t0:.0f} s, the best {min(keep, len(sc))} are played"
          + (f"; {len(rest)} tones without a fingerprint are played too (zr index)" if rest else ""), flush=True)
    return [r for _, r in sc[:keep]] + rest, sc


def cmd_record(a):
    """The takes of a part's layer that name a plugin tone ("zen": "BANK/NUMBER{edits}" instead of "tone" / "scene")
    -> the take files gm800_part.py layer reads. Sample 0 = the bar line of the take's first bar, 4 s of tail."""
    import soundfile as sf
    gp, sg = gp_song(a.song); part = json.load(open(a.notes, encoding="utf-8")); n = 0
    for tk in part["layer"]["takes"]:
        if tk.get("zen"):
            x, _, _ = render(tk["zen"], a.song, a.notes, tk["voice"], *tk["bars"], tk.get("vel", 100), tail=4.0)
            dst = gp.rec_path(sg, a.notes, tk); sf.write(dst, x, SR, subtype="FLOAT"); n += 1   # float: the plugin goes over 0 dBFS
            print(f"  {tk['voice']} {tk['bars'][0]}-{tk['bars'][1] - 1}  {tk['zen']}  peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS -> {os.path.basename(dst)}")
    print(f"{n} plugin takes of {len(part['layer']['takes'])} takes of the layer")


def cmd_variant(a):
    """An edited tone as one more take of a sweep already made: rendered, scored the same way, put into the sweep's
    ranking right after the tone it is made of, so `page` shows the two side by side."""
    import soundfile as sf
    x, gp, sg = render(a.tag, a.song, a.notes, a.voice, a.b0, a.b1, a.vel); part = json.load(open(a.notes, encoding="utf-8"))
    out = os.path.join(sg.out, "zenology"); tag = f"zen-{os.path.basename(a.notes).replace('.notes.json', '')}-{a.voice}-{a.b0}-{a.b1}"
    jf = os.path.join(out, tag + ".json")
    if not os.path.exists(jf):
        raise SystemExit(f"no sweep of this voice and bars yet ({jf}): run `sweep` first")
    rk = json.load(open(jf, encoding="utf-8")); _, row = tone_state(a.tag); dur = (a.b1 - a.b0) * sg.bar + 1.0
    ref = sum(sg.read(f"{st}.wav", sg.t_stem(a.b0), sg.t_stem(a.b0) + dur) for st in part["stems"]).mean(1)
    sc, sp, tf, o = gp.sweep_score(gp.cqt_db(ref), gp.cqt_db(x.mean(1)), sg.semi)
    import re
    fn = f"{tag}-{re.sub(r'[^A-Za-z0-9]+', '_', a.tag).strip('_')}.wav"; sf.write(os.path.join(out, fn), x, SR, subtype="PCM_16")
    e = {"bank": row["bank"], "number": row["number"], "name": a.name or f"{row['name']} {a.tag.partition('{')[2].rstrip('}')}",
         "category": row["category"], "score": round(sc, 3), "oct": o, "file": fn, "tone": a.tag}
    top = [t for t in rk["top"] if t.get("tone") != a.tag]
    k = max((i for i, t in enumerate(top) if (t["bank"], str(t["number"])) == (row["bank"], str(row["number"]))), default=len(top) - 1)
    top.insert(k + 1, e); rk["top"] = top
    json.dump(rk, open(jf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{e['name']}: score {sc:.3f} (spec {sp:.3f}, tf {tf:.3f}, oct {o:+d}) -> {os.path.join(out, fn)}; place {k + 2} of {len(top)} in {os.path.basename(jf)}")


def cmd_page(a):
    """Listening page of the sweeps of a song: per voice the original bars (band key) and the best ZENOLOGY takes,
    looped, same loudness -> analysis/gm800-match/<song>/zenology/page/index.html (tools/templates/part-tone-pick.html)."""
    import glob, subprocess, soundfile as sf
    from scipy.signal import resample_poly
    import re
    gp, sg = gp_song(a.song); part = json.load(open(a.notes, encoding="utf-8")); src = os.path.join(sg.out, "zenology"); dst = os.path.join(src, a.dir)
    os.makedirs(dst, exist_ok=True); rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-9; groups = []
    for jf in sorted(glob.glob(os.path.join(src, "zen-*.json")), key=os.path.getmtime):
        if a.only and not re.search(a.only, os.path.basename(jf)):
            continue
        rk = json.load(open(jf, encoding="utf-8")); b0, b1 = rk["bars"]; n = int(round((b1 - b0) * sg.bar * 44100)); orig = np.zeros(n)
        stems = rk.get("stems") or part["stems"]                 # a sweep made on another notes file (a voice heard in
        for st in stems:                                         # another stem) is shown against ITS stems; band key
            info = sf.info(sg.stem(st)); i0 = int(sg.t_stem(b0) * info.samplerate)
            x, sr = sf.read(sg.stem(st), start=i0, stop=i0 + int(((b1 - b0) * sg.bar + 0.2) * info.samplerate), always_2d=True)
            if sg.semi:
                sf.write(os.path.join(dst, "tmp-in.wav"), x, sr)
                subprocess.run(["rubberband", "-3", "-F", "-p", str(sg.semi), os.path.join(dst, "tmp-in.wav"), os.path.join(dst, "tmp-out.wav")], capture_output=True, check=True)
                x = sf.read(os.path.join(dst, "tmp-out.wav"), always_2d=True)[0]
            y = x.mean(1); y = resample_poly(y, 44100, sr) if sr != 44100 else y; orig += np.pad(y, (0, max(0, n - len(y))))[:n]
        clips = [("orig", orig, "Оригинал", "стемы " + " + ".join(stems), True)]
        for k, t in enumerate(rk["top"][:a.top], 1):
            x = resample_poly(sf.read(os.path.join(src, t["file"]), always_2d=True)[0].mean(1), 147, 160); x = np.pad(x, (0, max(0, n - len(x))))[:n]
            if t.get("ref"):                                     # a take to compare with (what the playback has now), not a candidate
                clips.append((f"{k:02d}", x * rms(orig) / rms(x), t["name"], t.get("note", ""), True)); continue
            clips.append((f"{k:02d}", x * rms(orig) / rms(x), f"{t['name']}", f"{t['bank']} {t['number']} · {t['category']} · "
                          + ("правленый тон" if t.get("tone") else f"№{k}") + f", близость {t['score']:.2f}", False))
        peak = max(np.abs(c[1]).max() for c in clips); out = []; tag = os.path.basename(jf)[:-5]
        for cid, x, nm, note, ref in clips:
            x = x / peak * 0.8; k = int(0.008 * 44100); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k)
            sf.write(os.path.join(dst, f"{tag}-{cid}.wav"), x.astype(np.float32), 44100, subtype="PCM_16"); out.append([f"{tag}-{cid}.wav", nm, note, ref])
        groups.append({"name": f"{rk['voice']}, такты {b0}–{b1 - 1}", "note": f"перебрано тонов ZENOLOGY: {rk['tried']}; по кругу, одна громкость", "clips": out})
    for f in ("tmp-in.wav", "tmp-out.wav"):
        if os.path.exists(os.path.join(dst, f)):
            os.remove(os.path.join(dst, f))
    meta = {"title": f"{sg.name} — тоны ZENOLOGY", "sub": "Варианты звука из ZENOLOGY, сыграны плагином без прибора. Внутри голоса переключение "
            "сохраняет место; <kbd>←</kbd> <kbd>→</kbd> соседний вариант, <kbd>пробел</kbd> пауза. Порядок — по близости к стему, это подсказка, не оценка.",
            "groups": groups, "v": int(time.time())}   # the clips are numbered by place: a rebuilt page has other
                                                                  # audio under the same names, the stamp gets round the cache
    tpl = open(os.path.join(REPO, "tools", "templates", "part-tone-pick.html"), encoding="utf-8").read()
    open(os.path.join(dst, "index.html"), "w", encoding="utf-8").write(tpl.replace("/*META*/", json.dumps(meta, ensure_ascii=False)))
    print(os.path.join(dst, "index.html"), f"- {len(groups)} voices")


def gp_song(song):
    s = importlib.util.spec_from_file_location("gp", os.path.join(REPO, "tools", "gm800_part.py"))
    gp = importlib.util.module_from_spec(s); s.loader.exec_module(gp)
    return gp, gp.gmm.Song(song)


def clean_take(p, ev, dur, tries=8, tol=6.0):
    """One take that can be trusted. Rendered faster than real time the plugin now and then drops a few notes
    (they fade by 10-20 dB over seconds) and brings them back with a thump - at random, about once in 90 s of
    audio, with any tone, whatever the pause before the take (measured 2026-11-21: the same tone twice gives two
    different takes; neither a wall-clock wait nor reset=True cures it). So the take is played several times and
    the one whose level curve (200 ms steps) stays within `tol` dB of the median of all of them is kept; random
    phases of a unison make +-3 dB. -> (take, how far it is from the median dB, takes played)"""
    w = int(0.2 * SR); takes, envs = [], []
    env = lambda m: 10 * np.log10((m[:len(m) // w * w].reshape(-1, w) ** 2).mean(1) + 1e-10)
    p(ev, duration=dur, sample_rate=SR, reset=False)      # a warm-up take, thrown away: the FIRST take after a tone is loaded
                                                          # is the one that loses notes most, the more so on a busy machine
                                                          # (measured by the «Беги от меня» session, 2026-11-21)
    for k in range(tries):
        x = p(ev, duration=dur, sample_rate=SR, reset=False).T.astype(np.float32); takes.append(x); envs.append(env(x.mean(1)))
        if k < 2:
            continue
        E = np.array(envs); med = np.median(E, 0); on = med > med.max() - 35          # the steps where the voice sounds
        dev = np.abs(E - med)[:, on].max(1) if on.any() else np.zeros(len(E))
        if dev.min() < tol:
            return takes[int(dev.argmin())], float(dev.min()), k + 1
    return takes[int(dev.argmin())], float(dev.min()), tries


def render(tag, song, notes, voice, b0, b1, vel=100, tail=1.0):
    from mido import Message
    gp, sg = gp_song(song); part = json.load(open(notes, encoding="utf-8")); p = plugin(tag)
    p([], duration=0.5, sample_rate=SR, reset=True)              # a fresh plugin, reset once: nothing of another tone
    ev = []                                                      # in its delay lines (a sweep take is not that clean)
    for t, n, d in gp.voice_line(sg, part, voice, b0, b1):
        ev += [Message("note_on", note=n, velocity=vel, time=t), Message("note_off", note=n, time=t + d)]
    ev.sort(key=lambda m: (m.time, m.type == "note_on"))
    x, dev, n = clean_take(p, ev, (b1 - b0) * sg.bar + tail)
    print(f"  take of {voice} {b0}-{b1 - 1}: {n} played, the kept one within {dev:.1f} dB of their median" + ("  <-- NOT CLEAN, listen to it" if dev >= 6 else ""), flush=True)
    return x, gp, sg

def cmd_render(a):
    import soundfile as sf
    x, _, _ = render(a.tag, a.song, a.notes, a.voice, a.b0, a.b1, a.vel)
    sf.write(a.out, x, SR, subtype="FLOAT"); print(a.out, f"{len(x) / SR:.1f} s, peak {20 * np.log10(np.abs(x).max() + 1e-9):.1f} dBFS")


def cmd_compare(a):
    import soundfile as sf, librosa
    x, gp, sg = render(a.tag, a.song, a.notes, a.voice, a.b0, a.b1, a.vel)
    base = os.path.basename(a.notes).replace(".notes.json", "")
    ref = os.path.join(sg.out, f"sweep-{base}-{a.voice}-{a.b0}-{a.b1}-t{int(a.gm or a.tag):04d}.wav")
    y = sf.read(ref, always_2d=True)[0].astype(np.float32); n = int((a.b1 - a.b0) * sg.bar * SR)
    xm, ym = x[:n].mean(1), y[:n].mean(1); rms = lambda v: np.sqrt((v ** 2).mean()) + 1e-12
    F = lambda v: np.abs(librosa.cqt(librosa.resample(v, orig_sr=SR, target_sr=22050), sr=22050, hop_length=256,
                                     fmin=librosa.note_to_hz("C2"), n_bins=96))
    A, B = F(xm / rms(xm)), F(ym / rms(ym)); cos = lambda u, v: float((u * v).sum() / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12))
    best = max((cos(np.log1p(30 * A[:, max(0, l):A.shape[1] + min(0, l)]), np.log1p(30 * B[:, max(0, -l):B.shape[1] + min(0, -l)])), l) for l in range(-8, 9))
    sa, sb = 20 * np.log10(A.mean(1) + 1e-9), 20 * np.log10(B.mean(1) + 1e-9)
    print(f"ZENOLOGY '{a.tag}' against the GM-800 take {os.path.basename(ref)}")
    print(f"  mean spectrum, cosine      {cos(A.mean(1), B.mean(1)):.3f}   (1 = the same tone)")
    print(f"  time x frequency, cosine   {best[0]:.3f}   at lag {best[1] * 256 / 22050 * 1000:+.0f} ms (the GM-800 take carries its USB latency)")
    print(f"  level                      ZENOLOGY {20 * np.log10(rms(xm)):.1f} dB, GM-800 {20 * np.log10(rms(ym)):.1f} dB")
    print(f"  spectrum difference by octave (ZENOLOGY - GM-800, dB, both at the same RMS): "
          + "  ".join(f"C{2 + k}: {np.mean(sa[12 * k:12 * k + 12]) - np.mean(sb[12 * k:12 * k + 12]):+.1f}" for k in range(8)))
    out = os.path.join(sg.out, "zenology"); os.makedirs(out, exist_ok=True)
    for nm, v in (("zenology", x[:n]), ("gm800", y[:n])):
        v = v / rms(v.mean(1)) * 0.05; k = int(0.008 * SR); v[:k] *= np.linspace(0, 1, k)[:, None]; v[-k:] *= np.linspace(1, 0, k)[:, None]
        sf.write(os.path.join(out, f"{a.voice}-{a.tag}-{nm}.wav"), v, SR, subtype="PCM_16")
    print("  A/B, same loudness:", out)


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick"); p.add_argument("tag")
    p = sub.add_parser("catalog"); p.add_argument("--max", type=int, default=100000); p.add_argument("--delay", type=float, default=0.3)
    p.add_argument("--banks", default=".", help="regular expression on the bank name (default: every bank of BANKS but the drum kits)")
    def filt(p):
        p.add_argument("--cat", default="", help='categories as the window shows them, e.g. "Synth Lead,Synth PolyKey"')
        p.add_argument("--name", default="", help="regular expression on the tone name"); p.add_argument("--bank", default="", help="regular expression on the bank")
        p.add_argument("--where", default="", help='limits on the traits of gear/zenology/traits.tsv, e.g. "bright<3,attack_ms>15,release_s<0.5"')
    p = sub.add_parser("list"); filt(p)
    p = sub.add_parser("sweep"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice"); p.add_argument("b0", type=int); p.add_argument("b1", type=int)
    filt(p); p.add_argument("--top", type=int, default=12); p.add_argument("--limit", type=int, default=100000); p.add_argument("--vel", type=int, default=100)
    p.add_argument("--dirty", action="store_true", help="keep the sweep's own takes of the best tones (faster; they carry tails of other tones)")
    p.add_argument("--pre", type=int, default=150, help="tones kept by the fingerprints and really played (0 = play every selected tone)")
    p = sub.add_parser("index"); p.add_argument("--banks", default="."); p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--redo", action="store_true"); p.add_argument("--shard", default="", help="(worker) 'BANK|START'")
    p = sub.add_parser("page"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("--top", type=int, default=8)
    p.add_argument("--only", default="", help="regular expression on the sweep files (zen-<notes>-<voice>-<bars>.json) to show")
    p.add_argument("--dir", default="page", help="folder of the page inside <song>/zenology/ (another page beside the main one)")
    p = sub.add_parser("record"); p.add_argument("song"); p.add_argument("notes")
    p = sub.add_parser("variant"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice"); p.add_argument("b0", type=int)
    p.add_argument("b1", type=int); p.add_argument("tag"); p.add_argument("--name", default=""); p.add_argument("--vel", type=int, default=100)
    for nm in ("render", "compare"):
        p = sub.add_parser(nm); p.add_argument("tag"); p.add_argument("song"); p.add_argument("notes"); p.add_argument("voice")
        p.add_argument("b0", type=int); p.add_argument("b1", type=int)
        if nm == "render":
            p.add_argument("out")
        else:
            p.add_argument("--gm", default="", help="GM-800 tone number of the sweep take to compare with (default: the tag)")
        p.add_argument("--vel", type=int, default=100)
    a = ap.parse_args()
    return {"pick": lambda: cmd_pick(a.tag), "catalog": lambda: cmd_catalog(a), "list": lambda: cmd_list(a), "sweep": lambda: cmd_sweep(a), "page": lambda: cmd_page(a), "variant": lambda: cmd_variant(a), "index": lambda: cmd_index(a), "record": lambda: cmd_record(a),
            "render": lambda: cmd_render(a), "compare": lambda: cmd_compare(a)}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
