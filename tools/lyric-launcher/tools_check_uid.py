#!/usr/bin/env python3
"""Standalone checker: print the CoreMIDI uniqueID of the 'LyricLauncher'
virtual destination, using the same ctypes calls the launcher uses.

Run while the launcher is up:

    .venv/bin/python tools_check_uid.py

Exit 0 if found, 1 if not. Used to verify the uniqueID is STABLE across
launcher restarts (it must equal launcher.LYRIC_UNIQUE_ID = 0x4C595243)."""
import ctypes
import sys

PORT_NAME = "LyricLauncher"
EXPECTED = 0x4C595243  # launcher.LYRIC_UNIQUE_ID


def main():
    coremidi = ctypes.CDLL(
        "/System/Library/Frameworks/CoreMIDI.framework/CoreMIDI")
    cf = ctypes.CDLL(
        "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")

    CFStringRef = ctypes.c_void_p
    OSStatus = ctypes.c_int32
    ItemCount = ctypes.c_ulong
    MIDIObjectRef = ctypes.c_uint32
    kCFStringEncodingUTF8 = 0x08000100

    cf.CFStringGetCString.restype = ctypes.c_bool
    cf.CFStringGetCString.argtypes = [
        CFStringRef, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    cf.CFRelease.argtypes = [ctypes.c_void_p]

    coremidi.MIDIGetNumberOfDestinations.restype = ItemCount
    coremidi.MIDIGetDestination.restype = MIDIObjectRef
    coremidi.MIDIGetDestination.argtypes = [ItemCount]
    coremidi.MIDIObjectGetStringProperty.restype = OSStatus
    coremidi.MIDIObjectGetStringProperty.argtypes = [
        MIDIObjectRef, CFStringRef, ctypes.POINTER(CFStringRef)]
    coremidi.MIDIObjectGetIntegerProperty.restype = OSStatus
    coremidi.MIDIObjectGetIntegerProperty.argtypes = [
        MIDIObjectRef, CFStringRef, ctypes.POINTER(ctypes.c_int32)]

    kName = CFStringRef.in_dll(coremidi, "kMIDIPropertyName")
    kUID = CFStringRef.in_dll(coremidi, "kMIDIPropertyUniqueID")

    def name_of(obj):
        out = CFStringRef()
        if coremidi.MIDIObjectGetStringProperty(
                obj, kName, ctypes.byref(out)) != 0 or not out.value:
            return None
        buf = ctypes.create_string_buffer(512)
        s = (buf.value.decode("utf-8")
             if cf.CFStringGetCString(out, buf, 512, kCFStringEncodingUTF8)
             else None)
        cf.CFRelease(out)
        return s

    n = coremidi.MIDIGetNumberOfDestinations()
    found = False
    for i in range(n):
        ep = coremidi.MIDIGetDestination(i)
        if name_of(ep) != PORT_NAME:
            continue
        found = True
        val = ctypes.c_int32()
        coremidi.MIDIObjectGetIntegerProperty(ep, kUID, ctypes.byref(val))
        uid = val.value & 0xFFFFFFFF
        match = "MATCH" if val.value == EXPECTED else "MISMATCH"
        print(f"{PORT_NAME}: uniqueID={val.value} ({hex(uid)})  "
              f"expected={EXPECTED} ({hex(EXPECTED)})  [{match}]")
    if not found:
        print(f"{PORT_NAME}: destination NOT FOUND (is the launcher running?)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
