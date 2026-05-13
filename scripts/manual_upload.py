#!/usr/bin/env python3
"""
Process manually uploaded MP4s from input/ folder.
Copies them to output/raw/ and adds meta entries.
"""
import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(".")
INPUT_DIR = WORKSPACE / "input"
RAW_DIR = WORKSPACE / "output" / "raw"
META_FILE = WORKSPACE / "output" / "videos_meta.json"

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

def get_video_duration(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            return float(result.stdout.strip())
        except:
            pass
    return 0

def process_manual_uploads():
    if not INPUT_DIR.exists():
        log("No input/ folder found")
        return []
    
    meta = load_meta()
    new_videos = []
    
    for mp4_file in sorted(INPUT_DIR.glob("*.mp4")):
        video_id = mp4_file.stem
        
        if video_id in meta:
            log(f"Skip (already in meta): {video_id}")
            continue
        
        duration = get_video_duration(mp4_file)
        
        # Copy to raw/
        raw_path = RAW_DIR / f"{video_id}.mp4"
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp4_file, raw_path)
        
        meta[video_id] = {
            "id": video_id,
            "title": video_id.replace("_", " ").replace("-", " ").title(),
            "duration": duration,
            "upload_date": datetime.now().strftime("%Y%m%d"),
            "uploader": "United24",
            "thumbnail": "",
            "raw_path": str(Path("output/raw") / f"{video_id}.mp4"),
            "status": "downloaded",
            "source": "manual_upload",
            "downloaded_at": datetime.now().isoformat(),
        }
        new_videos.append(meta[video_id])
        log(f"Manual upload: {video_id} ({duration:.1f}s)")
    
    save_meta(meta)
    log(f"Processed {len(new_videos)} manual uploads")
    return new_videos

def main():
    process_manual_uploads()

if __name__ == "__main__":
    main()
