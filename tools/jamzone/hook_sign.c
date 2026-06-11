// hook_sign.c — capture the inputs to JamZone's x-request-signature.
// Interposes CommonCrypto HMAC (one-shot + streaming) and CC_SHA256 to log the
// key (the baked-in secret) and message (method/path/body/nonce format) used to
// compute the request signature, so signatures can be reproduced for our own calls.
#include <CommonCrypto/CommonCrypto.h>
#include <CommonCrypto/CommonHMAC.h>
#include <stdio.h>
#include <string.h>

#define DYLD_INTERPOSE(_replacement, _replacee) \
    __attribute__((used)) static struct { \
        const void* replacement; const void* replacee; \
    } _interpose_##_replacee __attribute__((section("__DATA,__interpose"))) = { \
        (const void*)(unsigned long)&_replacement, (const void*)(unsigned long)&_replacee };

static FILE *slog(void) { static FILE *f; if (!f) f = fopen("/tmp/jz_sign.log", "a"); return f; }
static void hx(FILE *f, const char *l, const void *d, size_t n) {
    fprintf(f, "%s[%zu] hex: ", l, n);
    const unsigned char *p = d; for (size_t i = 0; i < n && i < 512; i++) fprintf(f, "%02x", p[i]);
    fprintf(f, "\n");
}
static void st(FILE *f, const char *l, const void *d, size_t n) {
    fprintf(f, "%s str: ", l);
    const char *p = d; for (size_t i = 0; i < n && i < 1024; i++) { char c = p[i]; fputc((c >= 32 && c < 127) ? c : '.', f); }
    fprintf(f, "\n");
}

void hooked_CCHmac(CCHmacAlgorithm alg, const void *key, size_t kl, const void *data, size_t dl, void *out) {
    CCHmac(alg, key, kl, data, dl, out);
    if (alg == kCCHmacAlgSHA256) {
        FILE *f = slog(); if (f) {
            fprintf(f, "=== CCHmac-SHA256 ===\n");
            hx(f, "KEY", key, kl); st(f, "KEY", key, kl);
            st(f, "MSG", data, dl); hx(f, "MSG", data, dl);
            const unsigned char *o = out; fprintf(f, "OUT: "); for (int i = 0; i < 32; i++) fprintf(f, "%02x", o[i]); fprintf(f, "\n\n");
            fflush(f);
        }
    }
}
DYLD_INTERPOSE(hooked_CCHmac, CCHmac)

// streaming HMAC (in case it's built incrementally)
void hooked_CCHmacUpdate(CCHmacContext *ctx, const void *data, size_t dl) {
    FILE *f = slog(); if (f) { st(f, "HmacUpdate", data, dl); fflush(f); }
    CCHmacUpdate(ctx, data, dl);
}
DYLD_INTERPOSE(hooked_CCHmacUpdate, CCHmacUpdate)

// plain SHA256 one-shot (in case signature = SHA256(msg+secret))
unsigned char *hooked_CC_SHA256(const void *data, CC_LONG len, unsigned char *md) {
    unsigned char *r = CC_SHA256(data, len, md);
    FILE *f = slog(); if (f && len < 4096) { fprintf(f, "--- CC_SHA256 ---\n"); st(f, "DATA", data, len);
        fprintf(f, "DIG: "); for (int i = 0; i < 32; i++) fprintf(f, "%02x", md[i]); fprintf(f, "\n\n"); fflush(f); }
    return r;
}
DYLD_INTERPOSE(hooked_CC_SHA256, CC_SHA256)
