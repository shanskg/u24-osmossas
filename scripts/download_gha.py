#!/usr/bin/env python3
"""
United24 Shorts Scraper for GitHub Actions
GitHub Actions runners have IPs that YouTube doesn't block.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("./output/raw")
META_FILE = Path("./output/videos_meta.json")
LIMIT = int(os.environ.get("LIMIT", "12"))

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def load_meta():
    if META_FILE.exists():
        with open(META_FILE) as f:
            return json.load(f)
    return {}

def save_meta(meta):
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

def download_shorts():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_meta()
    
    log(f"Downloading up to {LIMIT} Shorts from United24...")
    
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--ignore-errors",
        "--match-filter", "duration <= 60",
        "-f", "best[height<=1280]",
        "--write-info-json",
        "--output", str(OUTPUT_DIR / "%(id)s.%(ext)s"),
        "--playlist-end", str(LIMIT * 2),
        "https://youtube.com/@united24media/shorts",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        log(f"yt-dlp stderr: {result.stderr[:500]}")
    
    new_videos = []
    for video_file in sorted(OUTPUT_DIR.glob("*.mp4")):
        video_id = video_file.stem
        if video_id in meta:
            continue
        
        info = {}
        json_file = OUTPUT_DIR / f"{video_id}.info.json"
        if json_file.exists():
            try:
                with open(json_file) as f:
                    info = json.load(f)
            except:
                pass
        
        meta[video_id] = {
            "id": video_id,
            "title": info.get("title", video_id),
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "uploader": info.get("uploader", "United24"),
            "thumbnail": info.get("thumbnail", ""),
            "raw_path": str(Path("output/raw") / f"{video_id}.mp4"),
            "status": "downloaded",
            "downloaded_at": datetime.now().isoformat(),
        }
        new_videos.append(meta[video_id])
        log(f"New: {info.get('title', video_id)[:60]} ({info.get('duration', 0)}s)")
    
    save_meta(meta)
    log(f"Downloaded {len(new_videos)} new Shorts")
    return new_videos

def main():
    download_shorts()

if __name__ == "__main__":
    main()
