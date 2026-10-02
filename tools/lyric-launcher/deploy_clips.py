#!/usr/bin/env python3
"""Selected-song delivery. --apply commits and pushes; default is dry-run."""
import argparse
from pathlib import Path

from lyric_workflow import Workspace


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--rig", type=Path)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--message")
    args = ap.parse_args()
    try:
        Workspace(Path(__file__).resolve().parents[2], args.rig).deliver(
            args.index, apply=args.apply, message=args.message)
    except (ValueError, OSError, KeyError) as e:
        ap.exit(1, f"NOT DELIVERED: {e}\n")


if __name__ == "__main__":
    main()
