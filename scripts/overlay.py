#!/usr/bin/env python3
"""
Overlay OSMOSSAS branding on United24 Shorts.
Keeps original U24 logos intact. Adds our watermark + badge.
Output: 1080x1920 MP4, H.264
"""
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(os.path.expanduser("~/.openclaw/workspace/u24-scraper"))
META_FILE = WORKSPACE / "output" / "videos_meta.json"
RAW_DIR = WORKSPACE / "output" / "raw"
OUTPUT_DIR = WORKSPACE / "output" / "videos"
ASSETS_DIR = WORKSPACE / "assets"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)

def load_meta():
    if META_FILE.exists():
        with open(META_FILE) as f:
            return json.load(f)
    return {}

def save_meta(meta):
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

def get_video_info(path):
    """Get width, height, duration via ffprobe."""
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

def overlay_video(video_id, meta_entry, limit=None):
    """
    Overlay OSMOSSAS branding on a single video.
    Strategy:
    - Keep original video centered (with padding if not 9:16)
    - Add OSMOSSAS watermark at bottom center
    - Add corner badge (top-right)
    - Add subtle top/bottom brand bars if video is not full 9:16
    """
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
    
    # Load assets
    badge = None
    watermark = None
    badge_path = ASSETS_DIR / "badge.png"
    wm_path = ASSETS_DIR / "watermark.png"
    if badge_path.exists():
        badge = Image.open(badge_path).convert("RGBA")
    if wm_path.exists():
        watermark = Image.open(wm_path).convert("RGBA")
    
    vw, vh = info["width"], info["height"]
    duration = info["duration"]
    
    # Target: 1080x1920 (9:16)
    TW, TH = 1080, 1920
    
    # Calculate scaling to fit video into target while preserving aspect
    scale = min(TW / vw, TH / vh)
    new_w = int(vw * scale)
    new_h = int(vh * scale)
    
    # Center position
    off_x = (TW - new_w) // 2
    off_y = (TH - new_h) // 2
    
    # Build ffmpeg filter_complex
    filters = []
    
    # Scale video to fit
    filters.append(f"[0:v]scale={new_w}:{new_h}:force_original_aspect_ratio=decrease[scaled]")
    
    # Pad to target size with black (or dark brand color)
    filters.append(f"[scaled]pad={TW}:{TH}:{off_x}:{off_y}:color=0x111111[padded]")
    
    # Add badge overlay (top-right, with padding)
    if badge:
        bw, bh = badge.size
        badge_x = TW - bw - 20
        badge_y = 20
        badge_path_str = str(badge_path)
        filters.append(
            f"[padded][1:v]overlay={badge_x}:{badge_y}:format=auto[badged]"
        )
        last = "badged"
    else:
        last = "padded"
    
    # Add watermark overlay (bottom-center)
    if watermark:
        ww, wh = watermark.size
        wm_x = (TW - ww) // 2
        wm_y = TH - wh - 25
        wm_path_str = str(wm_path)
        if badge:
            filters.append(
                f"[{last}][2:v]overlay={wm_x}:{wm_y}:format=auto[final]"
            )
        else:
            filters.append(
                f"[{last}][1:v]overlay={wm_x}:{wm_y}:format=auto[final]"
            )
        last = "final"
    
    # Build full command
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
    
    # Add overlay inputs right after the video input
    insert_idx = cmd.index("-i", 0) + 2  # position after "-i <raw_path>"
    if badge:
        cmd.insert(insert_idx, "-i")
        cmd.insert(insert_idx + 1, str(badge_path))
        insert_idx += 2
    if watermark:
        cmd.insert(insert_idx, "-i")
        cmd.insert(insert_idx + 1, str(wm_path))
        insert_idx += 2
    
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
    
    # Update meta
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
        
        success = overlay_video(vid_id, entry, limit)
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
