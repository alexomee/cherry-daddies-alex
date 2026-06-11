#include <CommonCrypto/CommonCrypto.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>

// DYLD_INTERPOSE macro
#define DYLD_INTERPOSE(_replacement, _replacee) \
    __attribute__((used)) static struct { \
        const void* replacement; \
        const void* replacee; \
    } _interpose_##_replacee \
    __attribute__((section("__DATA,__interpose"))) = { \
        (const void*)(unsigned long)&_replacement, \
        (const void*)(unsigned long)&_replacee \
    };

static int g_call_count = 0;

CCCryptorStatus hooked_CCCrypt(
    CCOperation op, CCAlgorithm alg, CCOptions options,
    const void *key, size_t keyLength,
    const void *iv,
    const void *dataIn, size_t dataInLength,
    void *dataOut, size_t dataOutAvailable,
    size_t *dataOutMoved)
{
    // Call the real CCCrypt first
    CCCryptorStatus result = CCCrypt(op, alg, options, key, keyLength, iv,
                                     dataIn, dataInLength, dataOut,
                                     dataOutAvailable, dataOutMoved);

    // Only log decryption calls
    if (op == kCCDecrypt) {
        int call_id = __sync_fetch_and_add(&g_call_count, 1);

        fprintf(stderr, "\n[HOOK] === CCCrypt DECRYPT call #%d ===\n", call_id);
        fprintf(stderr, "[HOOK] Algorithm: %d (0=AES), Options: %d, KeyLen: %zu, Status: %d\n",
                alg, options, keyLength, result);

        // Print key as hex
        fprintf(stderr, "[HOOK] Key: ");
        const unsigned char *k = (const unsigned char *)key;
        for (size_t i = 0; i < keyLength; i++)
            fprintf(stderr, "%02x", k[i]);
        fprintf(stderr, "\n");

        // Print IV as hex
        if (iv) {
            fprintf(stderr, "[HOOK] IV:  ");
            const unsigned char *v = (const unsigned char *)iv;
            for (size_t i = 0; i < 16; i++)
                fprintf(stderr, "%02x", v[i]);
            fprintf(stderr, "\n");
        } else {
            fprintf(stderr, "[HOOK] IV:  (null)\n");
        }

        fprintf(stderr, "[HOOK] DataIn: %zu bytes, DataOut: %zu bytes\n",
                dataInLength, dataOutMoved ? *dataOutMoved : 0);

        // Save decrypted output to file
        if (result == kCCSuccess && dataOutMoved && *dataOutMoved > 0) {
            const char *outdir = getenv("JAMZONE_EXTRACT_DIR");
            if (!outdir) outdir = "/tmp/jamzone-extract";
            char path[512];
            snprintf(path, sizeof(path), "%s/decrypted_%04d.bin", outdir, call_id);
            FILE *f = fopen(path, "wb");
            if (f) {
                fwrite(dataOut, 1, *dataOutMoved, f);
                fclose(f);
                fprintf(stderr, "[HOOK] Saved %zu bytes to %s\n", *dataOutMoved, path);
            }
        }
    }

    return result;
}

DYLD_INTERPOSE(hooked_CCCrypt, CCCrypt)
