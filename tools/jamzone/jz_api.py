import hmac, hashlib, re, urllib.request, urllib.error
KEY=b"2MyMGVlN!IxZjFiNGRiN"
def _sig(msg): return hmac.new(KEY, msg.encode(), hashlib.sha256).hexdigest()
def _creds():
    log=open("/tmp/jz_http.log").read()
    tok=re.findall(r"x-authorization:\s*Bearer\s*(\S+)", log)[-1]
    ck =re.findall(r"x-client-key:\s*(\S+)", log)[-1]
    ver=re.findall(r"x-client-version:\s*(\S+)", log)[-1]
    return tok,ck,ver
def call(method, path, query="", body=None, sign_body=False):
    tok,ck,ver=_creds()
    url="https://api.jamzone.com"+path+(("?"+query) if query else "")
    msg = (body or "") if sign_body else query
    req=urllib.request.Request(url, method=method, data=body.encode() if body else None,
        headers={"x-authorization":"Bearer "+tok,"x-client-key":ck,"x-client-version":ver,
                 "x-request-signature":_sig(msg),"accept":"application/json","content-type":"application/json"})
    try:
        r=urllib.request.urlopen(req,timeout=20); return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
