#!/usr/bin/env python3
"""
jamzone_setlist.py — read & modify JamZone setlists via the cloud API.

Setlists live in JamZone's account/cloud (not the local Realm — local edits get
reconciled away on sync), reachable only through the signed API at
https://api.jamzone.com. Reverse-engineered request auth (every call needs all four):
    x-authorization: Bearer <access token>      # rotates at runtime; captured live
    x-client-key:    <client key>               # static per app build
    x-client-version: <app version>
    x-request-signature: HMAC_SHA256(SECRET, message)   hex
where SECRET = b"2MyMGVlN!IxZjFiNGRiN" and message = the query string for GET, or the
exact request BODY for writes. Setlist model: GET /setlist/ -> [{id,name,songs:[ids]}].
Update = POST /setlist/<id>/ (trailing slash) with pretty JSON {name, songs:[...]}.

The access token can't be minted offline (no captured refresh flow) and the plist token
is NOT the bearer — so `auth` briefly launches the DYLD-hooked app copy
(~/.cache/jamzone-inject), which auto-authenticates from its stored session and logs a
fresh token via hook_http.dylib; we read it and quit the app. The HMAC secret / client
key only change if JamZone ships a new build — recapture with the hook (see SKILL.md).

Usage:
    jamzone_setlist.py auth                       # refresh cached creds (launch hook app)
    jamzone_setlist.py list                       # all setlists (id, name, #songs)
    jamzone_setlist.py show <id|name>             # a setlist's songs as titles
    jamzone_setlist.py reorder <id|name> <file>   # file = .json [ids] OR .txt (1 title/line)
    jamzone_setlist.py rename <id|name> <new name>
    jamzone_setlist.py create <name> <file>       # new setlist from a .json/.txt order
<id|name> matches a setlist id or a unique case-insensitive substring of its name.
"""
import os, sys, json, re, time, hmac, hashlib, subprocess, unicodedata
import urllib.request, urllib.error

HOME = os.path.expanduser("~")
API = "https://api.jamzone.com"
SECRET = b"2MyMGVlN!IxZjFiNGRiN"
HOOK_APP = f"{HOME}/.cache/jamzone-inject/Jamzone.app"
DYLIB = f"{HOOK_APP}/Contents/MacOS/hook_http.dylib"
HTTP_LOG = "/tmp/jz_http.log"
CREDS = f"{HOME}/.cache/jamzone-inject/creds.json"
HOOK_PROC = "jamzone-inject/Jamzone.app/Contents/MacOS/Jamzone"


# ---- auth / signed transport ----
def _sig(msg): return hmac.new(SECRET, msg.encode(), hashlib.sha256).hexdigest()

def _creds_from_log():
    try: log = open(HTTP_LOG).read()
    except OSError: return None
    t = re.findall(r"x-authorization:\s*Bearer\s*(\S+)", log)
    k = re.findall(r"x-client-key:\s*(\S+)", log)
    v = re.findall(r"x-client-version:\s*(\S+)", log)
    return {"token": t[-1], "client_key": k[-1], "version": v[-1]} if (t and k and v) else None

def auth():
    """Launch the hooked app, capture a fresh bearer token, save creds, quit."""
    if not os.path.isdir(HOOK_APP):
        sys.exit(f"hooked app missing at {HOOK_APP}\nRebuild it (see SKILL.md 'Setlist API').")
    subprocess.run(["pkill", "-9", "-f", HOOK_PROC], capture_output=True)
    try: os.remove(HTTP_LOG)
    except OSError: pass
    env = dict(os.environ, DYLD_INSERT_LIBRARIES=DYLIB)
    subprocess.Popen([f"{HOOK_APP}/Contents/MacOS/Jamzone"], env=env,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    creds = None
    for _ in range(25):
        time.sleep(1)
        creds = _creds_from_log()
        if creds: break
    subprocess.run(["pkill", "-9", "-f", HOOK_PROC], capture_output=True)
    if not creds:
        sys.exit("auth failed — no token captured (is the hooked app still logged in?)")
    os.makedirs(os.path.dirname(CREDS), exist_ok=True)
    json.dump(creds, open(CREDS, "w"))
    return creds

def _creds():
    try: return json.load(open(CREDS))
    except OSError: return auth()

def call(method, path, query="", body=None, sign_body=False, _retry=True):
    c = _creds()
    url = API + path + (("?" + query) if query else "")
    msg = (body or "") if sign_body else query
    req = urllib.request.Request(url, method=method, data=body.encode() if body else None,
        headers={"x-authorization": "Bearer " + c["token"], "x-client-key": c["client_key"],
                 "x-client-version": c["version"], "x-request-signature": _sig(msg),
                 "accept": "application/json", "content-type": "application/json; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=25); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 401 and _retry:
            auth(); return call(method, path, query, body, sign_body, _retry=False)
        return e.code, e.read().decode()


# ---- setlist ops ----
def setlists():
    st, b = call("GET", "/setlist/")
    if st != 200: sys.exit(f"GET /setlist/ -> {st}: {b[:120]}")
    return json.loads(b)

def pick(key):
    sls = setlists()
    if str(key).isdigit():
        for s in sls:
            if s["id"] == int(key): return s
        sys.exit(f"no setlist id {key}")
    k = str(key).lower()
    hits = [s for s in sls if k in s["name"].lower()]
    if not hits: sys.exit(f"no setlist matches {key!r}")
    if len(hits) > 1: sys.exit("ambiguous: " + ", ".join(f'{s["name"]}#{s["id"]}' for s in hits))
    return hits[0]

def swift_pretty(name, songs):
    out = ["{", f'  "name" : {json.dumps(name, ensure_ascii=False)},', '  "songs" : [']
    out += [f"    {s}" + ("," if i < len(songs) - 1 else "") for i, s in enumerate(songs)]
    out += ["  ]", "}"]
    return "\n".join(out)

def write_setlist(sid, name, songs):
    st, b = call("POST", f"/setlist/{sid}/", body=swift_pretty(name, songs), sign_body=True)
    return st, b


# ---- title <-> id mapping (via the local library) ----
def _titles():
    try:
        import jamzone_normalize as J
        return {int(c.split("_")[1]): J.label_of(s) for c, _, s in J.iter_songs()}
    except Exception:
        return {}

def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def _order_from_file(path, current_ids):
    """Resolve a desired order file (.json ids OR .txt titles) to a permutation."""
    raw = open(path).read()
    if path.endswith(".json"):
        ids = json.loads(raw)
    else:
        titles = _titles()
        pool = [(sid, titles.get(sid, "")) for sid in current_ids]
        ids = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if re.match(r"(?i)^(set|reserve|encore|break|interval)\b", line): continue
            nl = _norm(line)
            if not nl: continue            # non-Latin section header (e.g. РЕЗЕРВ) -> empty
            hits = [sid for sid, t in pool if nl and nl in _norm(t) and sid not in ids]
            if len(hits) != 1:
                # fall back: any word-overlap unique match
                hits = [sid for sid, t in pool if sid not in ids and nl and
                        set(nl.split()) <= set(_norm(t).split())]
            if len(hits) == 1:
                ids.append(hits[0])
            else:
                sys.exit(f"can't uniquely match line {line!r} ({len(hits)} candidates)")
    if sorted(ids) != sorted(current_ids):
        miss = [i for i in current_ids if i not in ids]
        extra = [i for i in ids if i not in current_ids]
        sys.exit(f"order is not a permutation of the setlist.\n  missing {miss}\n  extra {extra}")
    return ids


# ---- commands ----
def c_auth(a): print("creds:", {k: (v[:10] + "…" if k == "token" else v) for k, v in auth().items()})

def c_list(a):
    for s in setlists(): print(f"  {s['id']:>8}  {len(s['songs']):>2} songs  {s['name']}")

def c_show(a):
    s = pick(a[0]); t = _titles()
    print(f"{s['name']} (#{s['id']}, {len(s['songs'])} songs)")
    for i, sid in enumerate(s["songs"], 1): print(f"  {i:>2}. {t.get(sid, sid)}")

def c_reorder(a):
    s = pick(a[0]); order = _order_from_file(a[1], s["songs"]); t = _titles()
    print(f"reordering {s['name']} (#{s['id']}):")
    for i, sid in enumerate(order, 1): print(f"  {i:>2}. {t.get(sid, sid)}")
    st, b = write_setlist(s["id"], s["name"], order)
    print("POST ->", st, ("OK" if st == 200 else b[:150]))

def c_rename(a):
    s = pick(a[0]); new = " ".join(a[1:])
    st, b = write_setlist(s["id"], new, s["songs"])
    print(f"renamed #{s['id']} -> {new!r}: {st}")

def c_create(a):
    name = a[0]; order = _order_from_file(a[1], json.loads(open(a[1]).read())) if a[1].endswith(".json") else None
    ids = json.loads(open(a[1]).read()) if a[1].endswith(".json") else sys.exit("create needs a .json id list")
    st, b = call("POST", "/setlist/", body=swift_pretty(name, ids), sign_body=True)
    print(f"create {name!r}: {st} {b[:200]}")


def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    cmd, rest = a[0], a[1:]
    {"auth": c_auth, "list": c_list, "show": c_show, "reorder": c_reorder,
     "rename": c_rename, "create": c_create}.get(cmd, lambda _: sys.exit(__doc__))(rest)


if __name__ == "__main__":
    main()
