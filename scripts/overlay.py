#!/usr/bin/env python3
"""
Overlay OSMOSSAS branding on United24 Shorts.
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(".")
META_FILE = WORKSPACE / "output" / "videos_meta.json"
RAW_DIR = WORKSPACE / "output" / "raw"
OUTPUT_DIR = WORKSPACE / "output" / "videos"
ASSETS_DIR = WORKSPACE / "assets"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def load_meta():
    if META_FILE.exists():
        with open(META_FILE) as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

def get_video_info(path):
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    streams = data.get("streams", [{}])[0]
    fmt = data.get("format", {})
    return {
        "width": streams.get("width", 0),
        "height": streams.get("height", 0),
        "duration": float(fmt.get("duration", 0)),
    }

def overlay_video(video_id, meta_entry):
    raw_path = WORKSPACE / meta_entry["raw_path"]
    if not raw_path.exists():
        log(f"[Overlay] Missing raw file for {video_id}")
        return False
    
    info = get_video_info(raw_path)
    if not info:
        log(f"[Overlay] Cannot read {video_id}")
        return False
    
    out_path = OUTPUT_DIR / f"{video_id}.mp4"
    if out_path.exists():
        log(f"[Overlay] Already exists: {out_path.name}")
        return True
    
    badge_path = ASSETS_DIR / "badge.png"
    wm_path = ASSETS_DIR / "watermark.png"
    
    vw, vh = info["width"], info["height"]
    TW, TH = 1080, 1920
    
    scale = min(TW / vw, TH / vh)
    new_w = int(vw * scale)
    new_h = int(vh * scale)
    off_x = (TW - new_w) // 2
    off_y = (TH - new_h) // 2
    
    filters = []
    filters.append(f"[0:v]scale={new_w}:{new_h}:force_original_aspect_ratio=decrease[scaled]")
    filters.append(f"[scaled]pad={TW}:{TH}:{off_x}:{off_y}:color=0x111111[padded]")
    
    badge = Image.open(badge_path).convert("RGBA") if badge_path.exists() else None
    watermark = Image.open(wm_path).convert("RGBA") if wm_path.exists() else None
    
    last = "padded"
    input_idx = 1
    
    if badge:
        bw, bh = badge.size
        badge_x = TW - bw - 20
        badge_y = 20
        filters.append(f"[{last}][{input_idx}:v]overlay={badge_x}:{badge_y}:format=auto[badged]")
        last = "badged"
        input_idx += 1
    
    if watermark:
        ww, wh = watermark.size
        wm_x = (TW - ww) // 2
        wm_y = TH - wh - 25
        filters.append(f"[{last}][{input_idx}:v]overlay={wm_x}:{wm_y}:format=auto[final]")
        last = "final"
        input_idx += 1
    
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw_path),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
    ]
    
    if badge:
        cmd.extend(["-i", str(badge_path)])
    if watermark:
        cmd.extend(["-i", str(wm_path)])
    
    if badge or watermark:
        cmd.extend(["-filter_complex", ";".join(filters), "-map", f"[{last}]"])
    
    cmd.append(str(out_path))
    
    log(f"[Overlay] {video_id}: {meta_entry['title'][:50]}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        log(f"[Overlay] ERROR: {result.stderr[:300]}")
        if out_path.exists():
            out_path.unlink()
        return False
    
    meta_entry["status"] = "branded"
    meta_entry["output_path"] = str(out_path.relative_to(WORKSPACE))
    meta_entry["branded_at"] = datetime.now().isoformat()
    
    log(f"[Overlay] Done: {out_path.name}")
    return True

def run_overlay(limit=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_meta()
    
    processed = skipped = failed = 0
    
    for vid_id, entry in meta.items():
        if entry.get("status") == "branded":
            skipped += 1
            continue
        if entry.get("status") != "downloaded":
            continue
        
        success = overlay_video(vid_id, entry)
        if success:
            processed += 1
        else:
            failed += 1
        
        if limit and processed >= limit:
            break
    
    save_meta(meta)
    log(f"[Overlay] {processed} done | {skipped} skipped | {failed} failed")
    return processed

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_overlay(limit)

if __name__ == "__main__":
    main()
