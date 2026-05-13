#!/usr/bin/env python3
"""
United24 YouTube Shorts Scraper — Direct fetch method
Extracts ytInitialPlayerResponse from page HTML and downloads via direct URLs.
"""
import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.path.expanduser("~/.openclaw/workspace/u24-scraper"))
OUTPUT_DIR = WORKSPACE / "output" / "raw"
META_FILE = WORKSPACE / "output" / "videos_meta.json"
SHORTS_URL = "https://www.youtube.com/@united24media/shorts"

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
    META_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(META_FILE, "w") as f:
        json.dump(meta, f, indent=2)

def curl_fetch(url, max_time=30):
    """Fetch URL with browser-like headers."""
    cmd = [
        "curl", "-s", "-L", "--max-time", str(max_time),
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.5",
        "-H", "Cookie: CONSENT=YES+cb",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout

def extract_player_response(html):
    """Extract ytInitialPlayerResponse JSON from page HTML."""
    # Match ytInitialPlayerResponse = {"..."};
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});\s*</script>', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Fallback: match with different ending
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None

def extract_video_urls(player_response):
    """Extract video download URLs from player response."""
    urls = []
    streaming_data = player_response.get("streamingData", {})
    
    # Regular formats (muxed video+audio)
    for fmt in streaming_data.get("formats", []):
        url = fmt.get("url") or fmt.get("signatureCipher")
        if url and "googlevideo.com" in url:
            urls.append({
                "url": url,
                "quality": fmt.get("qualityLabel", ""),
                "itag": fmt.get("itag", 0),
                "mime": fmt.get("mimeType", ""),
                "width": fmt.get("width", 0),
                "height": fmt.get("height", 0),
            })
    
    # Adaptive formats (video only or audio only)
    for fmt in streaming_data.get("adaptiveFormats", []):
        url = fmt.get("url") or fmt.get("signatureCipher")
        if url and "googlevideo.com" in url:
            urls.append({
                "url": url,
                "quality": fmt.get("qualityLabel", fmt.get("quality", "")),
                "itag": fmt.get("itag", 0),
                "mime": fmt.get("mimeType", ""),
                "width": fmt.get("width", 0),
                "height": fmt.get("height", 0),
            })
    
    # Sort by height descending, prefer mp4
    urls.sort(key=lambda x: (x["height"], "mp4" in x["mime"]), reverse=True)
    return urls

def extract_video_info(player_response):
    """Extract metadata from player response."""
    video_details = player_response.get("videoDetails", {})
    microformat = player_response.get("playerMicroformatRenderer", {})
    
    return {
        "title": video_details.get("title", ""),
        "duration": int(video_details.get("lengthSeconds", 0)),
        "author": video_details.get("author", ""),
        "video_id": video_details.get("videoId", ""),
        "thumbnail": f"https://i.ytimg.com/vi/{video_details.get('videoId', '')}/maxresdefault.jpg",
        "upload_date": microformat.get("uploadDate", "").replace("-", ""),
    }

def extract_shorts_ids_from_channel():
    """Extract Shorts video IDs from the channel page."""
    html = curl_fetch(SHORTS_URL, max_time=30)
    if not html:
        return []
    
    ids = set()
    # Pattern 1: /shorts/VIDEO_ID
    ids.update(re.findall(r'/shorts/([a-zA-Z0-9_-]{11})', html))
    # Pattern 2: videoId":"VIDEO_ID
    ids.update(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html))
    return list(ids)

def download_video(video_id):
    """Download a single video using direct URL extraction."""
    url = f"https://www.youtube.com/shorts/{video_id}"
    out_path = OUTPUT_DIR / f"{video_id}.mp4"
    
    if out_path.exists():
        return True, {"file": out_path}
    
    log(f"[Download] Fetching page for {video_id}...")
    html = curl_fetch(url, max_time=20)
    if not html:
        return False, None
    
    player_response = extract_player_response(html)
    if not player_response:
        log(f"[Download] Could not extract player response for {video_id}")
        return False, None
    
    # Check playability
    playability = player_response.get("playabilityStatus", {})
    if playability.get("status") != "OK":
        reason = playability.get("reason", "Unknown")
        log(f"[Download] Video not playable: {reason}")
        return False, None
    
    video_urls = extract_video_urls(player_response)
    if not video_urls:
        log(f"[Download] No URLs found for {video_id}")
        return False, None
    
    info = extract_video_info(player_response)
    
    # Pick best URL (highest resolution, prefer muxed)
    best = video_urls[0]
    for u in video_urls:
        if u["height"] > best["height"] and "mp4" in u["mime"]:
            best = u
        elif u["height"] == best["height"] and "mp4" in u["mime"] and "mp4" not in best["mime"]:
            best = u
    
    log(f"[Download] Best URL: {best['quality']} ({best['height']}p)")
    
    # Download with curl
    cmd = [
        "curl", "-s", "-L", "--max-time", "120",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H", "Referer: https://www.youtube.com/",
        "-o", str(out_path),
        best["url"],
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
    
    if result.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 1000:
        log(f"[Download] Curl failed or file too small for {video_id}")
        if out_path.exists():
            out_path.unlink()
        return False, None
    
    log(f"[Download] Saved: {out_path.name} ({out_path.stat().st_size // 1024}KB)")
    return True, info

def download_with_ytdlp_cookies(video_id, out_path):
    """Try downloading with cookies file if available."""
    cookies_path = WORKSPACE / "cookies.txt"
    if not cookies_path.exists():
        return False
    
    url = f"https://youtube.com/shorts/{video_id}"
    cmd = [
        "yt-dlp", "--no-warnings", "--ignore-errors",
        "--cookies", str(cookies_path),
        "-f", "best[height<=1280]",
        "--output", str(out_path),
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return out_path.exists() and out_path.stat().st_size > 1000

def download_with_ytdlp(video_id, out_path):
    """Try multiple yt-dlp methods."""
    url = f"https://youtube.com/shorts/{video_id}"
    methods = [
        ["yt-dlp", "--no-warnings", "--ignore-errors", "--extractor-args", "youtube:player_client=android",
         "-f", "best[height<=1280]", "--output", str(out_path), url],
        ["yt-dlp", "--no-warnings", "--ignore-errors", "--extractor-args", "youtube:player_client=tv_embedded",
         "-f", "best[height<=1280]", "--output", str(out_path), url],
        ["yt-dlp", "--no-warnings", "--ignore-errors", "--extractor-args", "youtube:player_client=ios",
         "--geo-bypass", "-f", "best[height<=1280]", "--output", str(out_path), url],
        ["yt-dlp", "--no-warnings", "--ignore-errors", "--extractor-args", "youtube:player_client=mweb",
         "-f", "best[height<=1280]", "--output", str(out_path), url],
        ["yt-dlp", "--no-warnings", "--ignore-errors", "--extractor-args", "youtube:player_client=web;player_skip=webpage,configs,js",
         "-f", "best[height<=1280]", "--output", str(out_path), url],
    ]
    
    cookies_path = WORKSPACE / "cookies.txt"
    if cookies_path.exists():
        methods.insert(0, [
            "yt-dlp", "--no-warnings", "--ignore-errors", "--cookies", str(cookies_path),
            "-f", "best[height<=1280]", "--output", str(out_path), url,
        ])
    
    for i, cmd in enumerate(methods):
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if out_path.exists() and out_path.stat().st_size > 1000:
            log(f"[Download] Method {i+1} worked for {video_id}")
            return True
    return False

def process_manual_uploads():
    """Process any MP4 files dropped into input/ folder."""
    input_dir = WORKSPACE / "input"
    if not input_dir.exists():
        return []
    
    meta = load_meta()
    new_videos = []
    
    for video_file in sorted(input_dir.glob("*.mp4")):
        video_id = video_file.stem
        out_path = OUTPUT_DIR / f"{video_id}.mp4"
        
        if video_id in meta:
            log(f"[Manual] Skip (already have): {video_id}")
            continue
        
        # Move to raw dir
        video_file.rename(out_path)
        
        meta[video_id] = {
            "id": video_id,
            "title": video_id,
            "duration": 0,
            "upload_date": "",
            "uploader": "United24",
            "thumbnail": "",
            "raw_path": str(out_path.relative_to(WORKSPACE)),
            "status": "downloaded",
            "downloaded_at": datetime.now().isoformat(),
            "source": "manual_upload",
        }
        new_videos.append(meta[video_id])
        log(f"[Manual] Processed: {video_id}")
    
    save_meta(meta)
    return new_videos

def download_shorts(limit=10):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_meta()
    
    # First, process any manual uploads
    manual = process_manual_uploads()
    
    log(f"[Download] Fetching up to {limit} Shorts from United24...")
    
    video_ids = extract_shorts_ids_from_channel()
    log(f"[Download] Found {len(video_ids)} video IDs")
    
    if not video_ids:
        log("[Download] No IDs found from channel page")
        # Still try yt-dlp direct playlist as last resort
        cmd = [
            "yt-dlp", "--no-warnings", "--ignore-errors",
            "--extractor-args", "youtube:player_client=android",
            "--match-filter", "duration <= 60",
            "-f", "best[height<=1280]",
            "--write-info-json",
            "--output", str(OUTPUT_DIR / "%(id)s.%(ext)s"),
            "--playlist-end", str(limit * 2),
            SHORTS_URL,
        ]
        cookies_path = WORKSPACE / "cookies.txt"
        if cookies_path.exists():
            cmd.insert(3, "--cookies")
            cmd.insert(4, str(cookies_path))
        
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    new_videos = list(manual)
    
    for vid in video_ids:
        if vid in meta:
            log(f"[Download] Skip (already have): {vid}")
            continue
        
        out_path = OUTPUT_DIR / f"{vid}.mp4"
        
        # Try yt-dlp methods first
        ok = download_with_ytdlp(vid, out_path)
        
        if ok:
            # Get info
            info = {}
            json_file = OUTPUT_DIR / f"{vid}.info.json"
            if json_file.exists():
                try:
                    with open(json_file) as f:
                        info = json.load(f)
                except:
                    pass
            
            meta[vid] = {
                "id": vid,
                "title": info.get("title", vid),
                "duration": info.get("duration", 0),
                "upload_date": info.get("upload_date", ""),
                "uploader": info.get("uploader", "United24"),
                "thumbnail": info.get("thumbnail", ""),
                "raw_path": str(out_path.relative_to(WORKSPACE)),
                "status": "downloaded",
                "downloaded_at": datetime.now().isoformat(),
            }
            new_videos.append(meta[vid])
            log(f"[Download] ✓ {info.get('title', vid)[:55]} ({info.get('duration', 0)}s)")
        else:
            log(f"[Download] ✗ Failed: {vid}")
        
        if len(new_videos) >= limit:
            break
    
    save_meta(meta)
    log(f"[Download] {len(new_videos)} new Shorts (manual: {len(manual)}, auto: {len(new_videos) - len(manual)})")
    return new_videos

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    download_shorts(limit)

if __name__ == "__main__":
    main()
