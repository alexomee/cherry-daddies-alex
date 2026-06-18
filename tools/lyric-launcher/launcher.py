#!/usr/bin/env python3
"""Lyric video launcher — POC.

One persistent mpv window (fullscreen on the stage monitor), muted, idle.
Listens for MIDI Program Change on a CoreMIDI input port and swaps the
fullscreen video to the matching clip, started from t=0. Audio of the band
stays in MainStage; this only paints lyrics on display 2.

Wiring (real use): MainStage sends a Program Change when a patch activates
-> this listens on the same port -> loads songs/<NN>.mp4 fullscreen on
display 2, frame-accurate because the clip is pre-rendered on the song's
timeline. Sync within a song = none-to-drift (single machine, linear media).

POC test (no MainStage): run this, then `send_pc.py 1` to fire PC #1.

By default the script creates its OWN virtual input port named
"LyricLauncher" (appears as a MIDI *destination* to every other app, incl.
MainStage — no IAC Driver setup required). Use --port NAME to instead open
an existing port (e.g. an IAC bus).
"""
import argparse
import ctypes
import json
import os
import socket
import subprocess
import sys
import time

import mido

SOCK = "/tmp/lyric-mpv.sock"

# Fixed CoreMIDI uniqueID for our virtual "LyricLauncher" port. MainStage's
# saved MIDI binding stores the endpoint's uniqueID, NOT its name — so unless
# this is stable across restarts the binding breaks every launch. python-rtmidi
# assigns a fresh random uniqueID each time it creates the virtual port, so right
# after creation we forcibly stamp this constant on it (see set_port_unique_id).
# 0x4C595243 = ASCII 'LYRC'.
LYRIC_UNIQUE_ID = 0x4C595243  # 1280922179


def set_port_unique_id(port_name, uid):
    """Best-effort: force the CoreMIDI kMIDIPropertyUniqueID of the virtual
    destination named `port_name` to `uid`, so MainStage's saved binding (keyed
    on uniqueID) survives restarts. mido/rtmidi keeps owning the port for actual
    MIDI reading; we only poke its uniqueID property via ctypes against the
    CoreMIDI framework. Any failure is logged and swallowed — the port still
    works, just without a stable ID."""
    try:
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
        coremidi.MIDIObjectSetIntegerProperty.restype = OSStatus
        coremidi.MIDIObjectSetIntegerProperty.argtypes = [
            MIDIObjectRef, CFStringRef, ctypes.c_int32]
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

        # Our virtual *input* port shows up to the system as a *destination*.
        n = coremidi.MIDIGetNumberOfDestinations()
        targets = [coremidi.MIDIGetDestination(i)
                   for i in range(n)
                   if name_of(coremidi.MIDIGetDestination(i)) == port_name]
        if not targets:
            print(f"[midi] warn: no destination named {port_name!r} found; "
                  "uniqueID left as assigned", file=sys.stderr)
            return
        if len(targets) > 1:
            print(f"[midi] warn: {len(targets)} destinations named "
                  f"{port_name!r}; stamping uniqueID on the first only",
                  file=sys.stderr)
        ep = targets[0]
        st = coremidi.MIDIObjectSetIntegerProperty(ep, kUID, uid)
        if st != 0:
            print(f"[midi] warn: could not set uniqueID on {port_name!r} "
                  f"(OSStatus {st}); using rtmidi-assigned ID", file=sys.stderr)
            return
        val = ctypes.c_int32()
        if coremidi.MIDIObjectGetIntegerProperty(
                ep, kUID, ctypes.byref(val)) == 0 and val.value == uid:
            print(f"[midi] LyricLauncher uniqueID={uid} (stable)")
        else:
            print(f"[midi] warn: uniqueID set returned OK but readback differs "
                  f"on {port_name!r}; binding may still drift", file=sys.stderr)
    except Exception as e:  # noqa: BLE001 - best-effort, never crash the launcher
        print(f"[midi] warn: stable uniqueID setup failed ({e}); "
              "port works but ID is rtmidi-random", file=sys.stderr)


def find_clip(clips_dir, program):
    """PC number -> clip path. Convention: <clips_dir>/NN.mp4 (zero-padded
    2 digits) with NN==program. Falls back to a 1-digit name."""
    for name in (f"{program:02d}.mp4", f"{program}.mp4"):
        p = os.path.join(clips_dir, name)
        if os.path.exists(p):
            return p
    return None


def mpv_start(screen, windowed):
    args = [
        "mpv",
        "--idle=yes",
        "--force-window=yes",
        "--keep-open=yes",          # hold last frame instead of going black
        "--mute=yes",               # band audio comes from MainStage
        "--no-osc", "--osd-level=0",
        "--no-input-default-bindings",
        "--no-terminal",
        "--loop-file=no",
        f"--input-ipc-server={SOCK}",
        "--background=color",
        "--background-color=#000000",
    ]
    if windowed:
        args += ["--geometry=960x540", "--title=LyricLauncher (dev)"]
    else:
        args += ["--fullscreen=yes", f"--screen={screen}",
                 f"--fs-screen={screen}", "--ontop=yes", "--cursor-autohide=100"]
    if os.path.exists(SOCK):
        os.remove(SOCK)
    proc = subprocess.Popen(args)
    # wait for the IPC socket to come up
    for _ in range(100):
        if os.path.exists(SOCK):
            return proc
        if proc.poll() is not None:
            sys.exit("mpv exited during startup")
        time.sleep(0.05)
    sys.exit("mpv IPC socket never appeared")


def mpv_cmd(command):
    """Send one JSON command to mpv, return its reply dict (or None)."""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCK)
        s.sendall((json.dumps({"command": command}) + "\n").encode())
        s.settimeout(0.5)
        try:
            data = s.recv(65536).decode()
        except socket.timeout:
            data = ""
        s.close()
        for line in data.splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if "error" in d:
                return d
        return None
    except OSError as e:
        print(f"[mpv] ipc error: {e}", file=sys.stderr)
        return None


def load_clip(path, autoplay):
    """Load a clip + its sibling .ass lyric track. autoplay=False arms it
    paused on frame 0 (the song title shows, 'ready'); True rolls immediately."""
    sub = os.path.splitext(path)[0] + ".ass"
    opts = ("pause=no" if autoplay else "pause=yes")
    if os.path.exists(sub):
        opts += f",sub-files=%{len(sub)}%{sub}"  # %N% = length-prefixed value
    r = mpv_cmd(["loadfile", path, "replace", -1, opts])
    if r and r.get("error") not in (None, "success"):
        # older/stricter mpv: fall back to plain load + sub-add
        mpv_cmd(["loadfile", path, "replace"])
        if os.path.exists(sub):
            mpv_cmd(["sub-add", sub, "select"])
        mpv_cmd(["set_property", "pause", not autoplay])
    mpv_cmd(["seek", 0, "absolute"])


def roll():
    """Play the loaded clip from t=0 (the transport-start trigger)."""
    mpv_cmd(["seek", 0, "absolute"])
    mpv_cmd(["set_property", "pause", False])


def blank():
    mpv_cmd(["playlist-clear"])
    mpv_cmd(["stop"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default=os.path.join(os.path.dirname(__file__), "clips"),
                    help="dir of NN.mp4 clips keyed by program-change number")
    ap.add_argument("--port", default=None,
                    help="existing MIDI input port to open (e.g. an IAC bus). "
                         "Default: create virtual port 'LyricLauncher'.")
    ap.add_argument("--screen", type=int, default=1,
                    help="mpv display index for fullscreen (0=primary, 1=second)")
    ap.add_argument("--windowed", action="store_true",
                    help="dev: small window on primary instead of fullscreen")
    ap.add_argument("--default-clip", type=int, default=None,
                    help="clip NN armed at startup / when transport-start arrives "
                         "with nothing armed (single-song test without patch PC)")
    ap.add_argument("--bpm", type=float, default=120.0,
                    help="transport tempo, for converting MIDI Song-Position (SPP) "
                         "and clock to seconds when chasing MainStage")
    ap.add_argument("--chase-clock", action="store_true",
                    help="continuously re-seek to the clock-tracked position if the "
                         "clip drifts >0.2s (belt-and-suspenders; off by default)")
    ap.add_argument("--play-from-zero", action="store_true",
                    help="MainStage sends `continue` (not `start`) as play and no "
                         "position; with Playback set PLAY FROM: Beginning, treat play "
                         "as roll-from-0 so audio+lyrics always start aligned at 0.")
    ap.add_argument("--go-note", type=int, default=21,
                    help="MIDI note that PLAYS the armed song from 0 (a pad / dead low "
                         "key; MainStage forwards notes easily). Default 21 = A0.")
    ap.add_argument("--stop-note", type=int, default=23,
                    help="MIDI note that FREEZES the lyrics. Default 23 = B0.")
    args = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    clips = os.path.abspath(args.clips)
    print(f"[clips] {clips}")
    mpv_start(args.screen, args.windowed)
    print("[mpv] up")

    if args.port:
        inport = mido.open_input(args.port)
        print(f"[midi] listening on existing port: {args.port}")
    else:
        inport = mido.open_input("LyricLauncher", virtual=True)
        print("[midi] created virtual destination: 'LyricLauncher'")
        # Stamp a fixed CoreMIDI uniqueID so MainStage's saved binding (keyed on
        # uniqueID) resolves across restarts without re-wiring. Best-effort.
        set_port_unique_id("LyricLauncher", LYRIC_UNIQUE_ID)

    # Transport-chase model (MainStage as MIDI clock master):
    #   program_change N -> ARM clip N (load, paused on frame 0, title showing)
    #   start            -> play from 0                       (Playback play from top)
    #   continue         -> resume in place (unpause)         (Playback resume)
    #   stop             -> freeze                            (Playback stop)
    #   songpos (SPP)    -> SEEK to that position             (scrub / locate)  <- scrub-aware
    #   clock (0xF8)     -> 24/quarter; tracks position, optional drift correction
    # Notes/CC are ignored (the keybed is musical spam, not a trigger).
    bpm = args.bpm
    armed = [None]
    state = {"playing": False, "pos": 0.0, "clocks": 0}

    def spp_to_sec(pos16):
        # SPP value counts 16th-notes from song start; lyric clip t=0 = song start.
        return (pos16 / 4.0) * (60.0 / bpm)

    def seek(sec):
        mpv_cmd(["seek", f"{max(0.0, sec):.3f}", "absolute"])

    def set_playing(p):
        state["playing"] = p
        mpv_cmd(["set_property", "pause", not p])

    def arm(program):
        clip = find_clip(clips, program)
        if clip:
            armed[0] = clip
            state["pos"] = 0.0
            print(f"[pc {program}] ARM -> {os.path.basename(clip)} (ready, paused)")
            load_clip(clip, autoplay=False)
            set_playing(False)
        else:
            print(f"[pc {program}] no clip {program:02d}.mp4")

    last_go = [0.0]

    def go_path(clip, tag):
        now = time.time()
        # debounce: a looping/repeating trigger can't machine-gun restarts
        if state["playing"] and armed[0] == clip and now - last_go[0] < 0.7:
            return
        last_go[0] = now
        armed[0] = clip
        state["pos"] = 0.0
        load_clip(clip, autoplay=True)
        set_playing(True)
        mpv_cmd(["show-text", "▶ PLAYING", 1200])   # instant on-screen confirmation
        print(f"[{tag}] GO -> {os.path.basename(clip)} from 0")

    def go(program):
        """Deterministic pad trigger: load clip N and play from 0 in one press."""
        clip = find_clip(clips, program)
        if clip:
            go_path(clip, f"pc {program}")
        else:
            print(f"[pc {program}] no clip {program:02d}.mp4")

    def reset(tag):
        """Rewind to 0 and pause -> shows the song title, ready for the next GO."""
        state["pos"] = 0.0
        seek(0.0)
        set_playing(False)
        mpv_cmd(["show-text", "■ READY", 1200])     # instant on-screen confirmation
        print(f"[{tag}] RESET -> title, ready")

    if args.default_clip is not None:
        arm(args.default_clip)

    CLOCK_TIMEOUT = 0.35   # s without clock while playing -> transport stopped
    DRIFT_CHECK = 1.5      # s between gentle drift corrections
    DRIFT_TOL = 0.35       # s of slip before a resync seek

    last_clock = 0.0
    paused_by_wd = False   # paused because the clock stalled (vs an explicit stop)
    last_drift = 0.0
    last_status = 0.0
    clocks = 0
    clock_seen = False

    print(f"[ready] chasing MainStage transport @ {bpm} bpm  (Ctrl-C to quit)")
    print("[monitor] non-clock MIDI logged · [status] every 2s · clock watchdog on")
    try:
        while True:
            for msg in inport.iter_pending():
                t = msg.type
                if t == "clock":
                    clocks += 1
                    clock_seen = True
                    last_clock = time.time()
                    if state["playing"]:
                        state["pos"] += (60.0 / bpm) / 24.0
                    elif paused_by_wd:
                        # transport resumed (clock came back) -> unpause in place
                        paused_by_wd = False
                        state["playing"] = True
                        mpv_cmd(["set_property", "pause", False])
                        print(f"[resume] clock back -> play @ {state['pos']:.1f}s")
                    continue
                if t in ("active_sensing", "sensing"):
                    continue
                # trigger notes (easiest thing for MainStage to forward)
                if t == "note_on" and msg.velocity > 0 and msg.note == args.go_note:
                    if armed[0]:
                        go_path(armed[0], f"note {msg.note}")
                    continue
                if t == "note_on" and msg.velocity > 0 and msg.note == args.stop_note:
                    reset(f"note {msg.note}")
                    continue
                if t in ("note_on", "note_off"):
                    continue                       # ignore the rest of the keybed
                if t == "control_change":
                    continue                       # ignore expression/CC spam

                print(f"[midi<-] {msg}")
                if t == "program_change":
                    if msg.program == 0:
                        reset("pc 0")              # PC 0 = reset to title
                    else:
                        arm(msg.program)           # SET CHANGE arms the song (title, paused)
                elif t == "start":
                    # transport PLAY (E1 Play/Stop action) -> roll the armed clip from 0
                    state["pos"] = 0.0
                    seek(0.0); set_playing(True)
                    last_clock = time.time(); paused_by_wd = False
                    mpv_cmd(["show-text", "▶ PLAYING", 1200])
                    print("[start] roll from 0")
                elif t == "continue":
                    if args.play_from_zero:
                        state["pos"] = 0.0
                        seek(0.0)
                    set_playing(True)
                    last_clock = time.time(); paused_by_wd = False
                    print(f"[continue] play @ {state['pos']:.1f}s")
                elif t == "stop":
                    set_playing(False); paused_by_wd = False
                    print(f"[stop] freeze @ {state['pos']:.1f}s")
                elif t == "songpos":
                    sec = spp_to_sec(msg.pos)
                    state["pos"] = sec; seek(sec)
                    mpv_cmd(["set_property", "pause", not state["playing"]])
                    print(f"[songpos] pos={msg.pos} (1/16) -> seek {sec:.2f}s")

            nowt = time.time()
            # WATCHDOG: clock stopped streaming while playing => MainStage stopped
            if state["playing"] and clock_seen and (nowt - last_clock) > CLOCK_TIMEOUT:
                state["playing"] = False; paused_by_wd = True
                mpv_cmd(["set_property", "pause", True])
                print(f"[watchdog] clock stopped -> pause @ {state['pos']:.1f}s")
            # gentle drift correction (no per-tick reseek = no lag/stutter)
            if args.chase_clock and state["playing"] and (nowt - last_drift) > DRIFT_CHECK:
                last_drift = nowt
                r = mpv_cmd(["get_property", "time-pos"])
                cur = r.get("data") if isinstance(r, dict) else None
                if isinstance(cur, (int, float)) and abs(cur - state["pos"]) > DRIFT_TOL:
                    seek(state["pos"])
                    print(f"[chase] mpv {cur:.1f}s vs clock {state['pos']:.1f}s -> resync")
            # live debug visibility (only while playing, every 10s)
            if state["playing"] and nowt - last_status > 10.0:
                last_status = nowt
                clk = f"{(nowt-last_clock)*1000:.0f}ms ago" if clock_seen else "NONE"
                print(f"[status] playing={state['playing']} pos={state['pos']:.1f}s "
                      f"clock={clk} clocks={clocks}")
            time.sleep(0.004)
    except KeyboardInterrupt:
        pass
    finally:
        mpv_cmd(["quit"])


if __name__ == "__main__":
    main()
