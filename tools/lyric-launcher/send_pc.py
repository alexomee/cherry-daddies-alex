#!/usr/bin/env python3
"""POC test sender — plays MainStage's role.

Send a Program Change (or a blank-note) to the launcher's MIDI port so you
can prove the chain without MainStage wired up.

  send_pc.py 1            # fire Program Change #1  -> launcher plays 01.mp4
  send_pc.py 3            # PC #3 -> 03.mp4
  send_pc.py --blank      # note_on 60 -> blank screen

Targets the 'LyricLauncher' virtual port by default; --port to override.
"""
import argparse
import sys

import mido


def pick_port(name):
    outs = mido.get_output_names()
    for o in outs:
        if name == o or name in o:
            return o
    sys.exit(f"port '{name}' not found. available outputs: {outs}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("program", nargs="?", type=int, help="program change number")
    ap.add_argument("--port", default="LyricLauncher")
    ap.add_argument("--blank", action="store_true", help="send blank note (60) instead")
    ap.add_argument("--channel", type=int, default=0)
    args = ap.parse_args()

    port = pick_port(args.port)
    with mido.open_output(port) as out:
        if args.blank:
            out.send(mido.Message("note_on", note=60, velocity=100, channel=args.channel))
            print(f"sent blank note -> {port}")
        elif args.program is not None:
            out.send(mido.Message("program_change", program=args.program, channel=args.channel))
            print(f"sent PC {args.program} -> {port}")
        else:
            sys.exit("give a program number or --blank")


if __name__ == "__main__":
    main()
