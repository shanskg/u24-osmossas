#!/usr/bin/env python3
"""
Local Download Script — Run this on your HOME computer (not the cloud server)
YouTube blocks cloud IPs, so run this locally and upload the files.
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def download_shorts(output_dir, limit=10):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://youtube.com/@united24media/shorts"
    
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--ignore-errors",
        "--match-filter", "duration <= 60",
        "-f", "best[height<=1280]",
        "--write-info-json",
        "--output", str(output_dir / "%(id)s.%(ext)s"),
        "--playlist-end", str(limit),
        url,
    ]
    
    log(f"Downloading up to {limit} Shorts to {output_dir}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log(f"yt-dlp stderr: {result.stderr[:500]}")
    
    # List results
    mp4s = list(output_dir.glob("*.mp4"))
    log(f"Downloaded {len(mp4s)} videos")
    
    for f in sorted(mp4s):
        info_file = f.with_suffix(".info.json")
        title = f.stem
        if info_file.exists():
            try:
                with open(info_file) as fh:
                    info = json.load(fh)
                title = info.get("title", title)
            except:
                pass
        log(f"  ✓ {f.name} — {title[:50]}")
    
    log(f"\nNext steps:")
    log(f"  1. Upload these MP4 files to the server: ~/.openclaw/workspace/u24-scraper/input/")
    log(f"  2. Run: python3 master.py")

def main():
    parser = argparse.ArgumentParser(description="Download United24 Shorts locally")
    parser.add_argument("--limit", type=int, default=10, help="Number of Shorts to download")
    parser.add_argument("--output", default="./u24_shorts", help="Output directory")
    args = parser.parse_args()
    
    download_shorts(args.output, args.limit)

if __name__ == "__main__":
    main()
