#!/usr/bin/env python3
"""
United24 Shorts Scraper — Works on GitHub Actions runners
(YouTube blocks cloud IPs, but GitHub Actions runners usually work)
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./output/raw"))
META_FILE = Path(os.environ.get("META_FILE", "./output/videos_meta.json"))
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
    log(f"Output dir: {OUTPUT_DIR.absolute()}")
    log(f"Meta file: {META_FILE.absolute()}")
    log(f"Existing entries: {len(meta)}")
    
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
    
    log(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    log(f"yt-dlp return code: {result.returncode}")
    if result.stdout:
        log(f"yt-dlp stdout:\n{result.stdout[:2000]}")
    if result.stderr:
        log(f"yt-dlp stderr:\n{result.stderr[:2000]}")
    
    # List files in output dir
    all_files = list(OUTPUT_DIR.iterdir())
    log(f"Files in {OUTPUT_DIR}: {len(all_files)}")
    for f in all_files[:10]:
        log(f"  {f.name}")
    
    new_videos = []
    for video_file in sorted(OUTPUT_DIR.glob("*.mp4")):
        video_id = video_file.stem
        if video_id in meta:
            log(f"Skip (already in meta): {video_id}")
            continue
        
        info = {}
        json_file = OUTPUT_DIR / f"{video_id}.info.json"
        if json_file.exists():
            try:
                with open(json_file) as f:
                    info = json.load(f)
            except Exception as e:
                log(f"Error reading info for {video_id}: {e}")
        
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
    log(f"Total meta entries: {len(meta)}")
    return new_videos

def main():
    download_shorts()

if __name__ == "__main__":
    main()
