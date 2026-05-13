#!/usr/bin/env python3
"""Rotate videos to keep within caps."""
from pathlib import Path

OUTPUT_DIR = Path("../output/videos")
TOP_DIR = OUTPUT_DIR / "top"
MAX_TOTAL = 150
MAX_TOP = 10

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TOP_DIR.mkdir(parents=True, exist_ok=True)

    all_videos = sorted([f for f in OUTPUT_DIR.glob("*.mp4") if f.is_file()], key=lambda f: f.stat().st_mtime, reverse=True)
    top_videos = sorted([f for f in TOP_DIR.glob("*.mp4") if f.is_file()], key=lambda f: f.stat().st_mtime, reverse=True)

    if len(top_videos) > MAX_TOP:
        for old in top_videos[MAX_TOP:]:
            try:
                old.unlink()
            except Exception as e:
                print(f"Warning: could not remove {old}: {e}")

    top_count = len(list(TOP_DIR.glob("*.mp4")))
    main_cap = max(0, MAX_TOTAL - top_count)
    
    if len(all_videos) > main_cap:
        for old in all_videos[main_cap:]:
            try:
                old.unlink()
            except Exception as e:
                print(f"Warning: could not remove {old}: {e}")

    final_main = len(list(OUTPUT_DIR.glob("*.mp4")))
    final_top = len(list(TOP_DIR.glob("*.mp4")))
    print(f"Rotated: {final_main} main + {final_top} top = {final_main + final_top} total")

if __name__ == "__main__":
    main()
