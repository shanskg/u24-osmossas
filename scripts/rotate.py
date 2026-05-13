#!/usr/bin/env python3
"""Rotate videos to keep within caps."""
import json
from pathlib import Path

OUTPUT_DIR = Path("../output/videos")
TOP_DIR = OUTPUT_DIR / "top"
MAX_TOTAL = 150
MAX_TOP = 10

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    TOP_DIR.mkdir(exist_ok=True)

    all_videos = sorted([f for f in OUTPUT_DIR.glob("*.mp4") if f.is_file()], key=lambda f: f.stat().st_mtime, reverse=True)
    top_videos = sorted([f for f in TOP_DIR.glob("*.mp4") if f.is_file()], key=lambda f: f.stat().st_mtime, reverse=True)

    if len(top_videos) > MAX_TOP:
        for old in top_videos[MAX_TOP:]:
            old.unlink()

    main_cap = MAX_TOTAL - len(list(TOP_DIR.glob("*.mp4")))
    if len(all_videos) > main_cap:
        for old in all_videos[main_cap:]:
            old.unlink()

    print(f"Rotated: {min(len(all_videos), main_cap)} main + {len(list(TOP_DIR.glob('*.mp4')))} top")

if __name__ == "__main__":
    main()
