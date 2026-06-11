// hook_http.m — DYLD-injected capture of JamZone's authenticated API requests.
// Swizzles NSMutableURLRequest's header/body/method setters (and NSURLSessionTask
// -resume) to log every request to api.jamzone.com — URL, HTTP method, all headers
// (incl. Authorization + any public-key/signature header) and body — to /tmp/jz_http.log.
// Goal: capture a fresh Bearer token + the exact auth scheme so the setlist reorder
// can be replayed via the real API. Read-only logging; it always calls through to the
// original implementation.
#import <Foundation/Foundation.h>
#import <objc/runtime.h>

static void jzlog(NSString *s) {
    static NSFileHandle *fh; static dispatch_once_t once;
    dispatch_once(&once, ^{
        NSString *p = @"/tmp/jz_http.log";
        [[NSFileManager defaultManager] createFileAtPath:p
            contents:[@"== jz http hook start ==\n" dataUsingEncoding:NSUTF8StringEncoding]
            attributes:nil];
        fh = [NSFileHandle fileHandleForWritingAtPath:p];
        [fh seekToEndOfFile];
    });
    @synchronized(fh) {
        @try { [fh writeData:[[s stringByAppendingString:@"\n"] dataUsingEncoding:NSUTF8StringEncoding]]; }
        @catch (__unused id e) {}
    }
}
static BOOL jzAPI(NSURL *u) { return u && u.host && [u.host containsString:@"jamzone.com"]; }

static IMP o_setValue, o_setAllH, o_setBody, o_setMethod, o_resume;

static void jz_install(void) {
    Class mreq = NSClassFromString(@"NSMutableURLRequest");
    Class task = NSClassFromString(@"NSURLSessionTask");

    SEL sv = @selector(setValue:forHTTPHeaderField:);
    Method m_sv = class_getInstanceMethod(mreq, sv); o_setValue = method_getImplementation(m_sv);
    method_setImplementation(m_sv, imp_implementationWithBlock(^(NSMutableURLRequest *r, NSString *v, NSString *f){
        ((void(*)(id,SEL,id,id))o_setValue)(r, sv, v, f);
        if (jzAPI(r.URL)) jzlog([NSString stringWithFormat:@"HDR  %@ | %@: %@", r.URL.absoluteString, f, v]);
    }));

    SEL sah = @selector(setAllHTTPHeaderFields:);
    Method m_sah = class_getInstanceMethod(mreq, sah); o_setAllH = method_getImplementation(m_sah);
    method_setImplementation(m_sah, imp_implementationWithBlock(^(NSMutableURLRequest *r, NSDictionary *d){
        ((void(*)(id,SEL,id))o_setAllH)(r, sah, d);
        if (jzAPI(r.URL)) jzlog([NSString stringWithFormat:@"HDRS %@ | %@", r.URL.absoluteString, d]);
    }));

    SEL sb = @selector(setHTTPBody:);
    Method m_sb = class_getInstanceMethod(mreq, sb); o_setBody = method_getImplementation(m_sb);
    method_setImplementation(m_sb, imp_implementationWithBlock(^(NSMutableURLRequest *r, NSData *b){
        ((void(*)(id,SEL,id))o_setBody)(r, sb, b);
        if (jzAPI(r.URL)) jzlog([NSString stringWithFormat:@"BODY %@ | %@", r.URL.absoluteString,
            b ? [[NSString alloc] initWithData:b encoding:NSUTF8StringEncoding] : @""]);
    }));

    SEL sm = @selector(setHTTPMethod:);
    Method m_sm = class_getInstanceMethod(mreq, sm); o_setMethod = method_getImplementation(m_sm);
    method_setImplementation(m_sm, imp_implementationWithBlock(^(NSMutableURLRequest *r, NSString *meth){
        ((void(*)(id,SEL,id))o_setMethod)(r, sm, meth);
        if (jzAPI(r.URL)) jzlog([NSString stringWithFormat:@"METH %@ | %@", r.URL.absoluteString, meth]);
    }));

    // belt & suspenders: dump the final request at -resume
    SEL sr = @selector(resume);
    Method m_sr = class_getInstanceMethod(task, sr); o_resume = method_getImplementation(m_sr);
    method_setImplementation(m_sr, imp_implementationWithBlock(^(NSURLSessionTask *t){
        @try {
            NSURLRequest *r = t.originalRequest ?: t.currentRequest;
            if (jzAPI(r.URL)) {
                NSMutableString *ms = [NSMutableString stringWithFormat:@"REQ  %@ %@\n", r.HTTPMethod, r.URL.absoluteString];
                [r.allHTTPHeaderFields enumerateKeysAndObjectsUsingBlock:^(id k, id v, BOOL *s){ [ms appendFormat:@"   %@: %@\n", k, v]; }];
                if (r.HTTPBody) [ms appendFormat:@"   BODY %@\n", [[NSString alloc] initWithData:r.HTTPBody encoding:NSUTF8StringEncoding]];
                jzlog(ms);
            }
        } @catch (__unused id e) {}
        ((void(*)(id,SEL))o_resume)(t, sr);
    }));

    jzlog(@"hooks installed");
}

__attribute__((constructor))
static void jz_init(void) { jzlog(@"dylib loaded"); jz_install(); }
