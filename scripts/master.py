#!/usr/bin/env python3
"""
United24 Branded Shorts — Master Pipeline
Orchestrates: download U24 Shorts → overlay OSMOSSAS branding → rotate → push
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(".")
LOG_FILE = WORKSPACE / "logs" / "pipeline.log"
OUTPUT_DIR = WORKSPACE / "output" / "videos"
TOP_DIR = OUTPUT_DIR / "top"

# Caps
MAX_TOTAL = 150
MAX_TOP = 10

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run(cmd, cwd=None):
    log(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        log(f"  ERROR (code {result.returncode}): {result.stderr[:500]}")
        return False
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            log(f"  {line}")
    return True

def rotate_videos():
    """Keep only MAX_TOTAL videos + MAX_TOP in top folder."""
    if not OUTPUT_DIR.exists():
        return

    all_videos = sorted(
        [f for f in OUTPUT_DIR.glob("*.mp4") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    TOP_DIR.mkdir(exist_ok=True)
    top_videos = sorted(
        [f for f in TOP_DIR.glob("*.mp4") if f.is_file()],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if len(top_videos) > MAX_TOP:
        for old in top_videos[MAX_TOP:]:
            old.unlink()
            log(f"[ROTATE] Removed from top/: {old.name}")

    main_cap = MAX_TOTAL - len(top_videos)
    if len(all_videos) > main_cap:
        for old in all_videos[main_cap:]:
            old.unlink()
            log(f"[ROTATE] Removed: {old.name}")

    log(f"[ROTATE] Kept {min(len(all_videos), main_cap)} main + {len(top_videos)} top videos")

def generate_gallery():
    """Generate index.html gallery page."""
    meta_file = WORKSPACE / "output" / "videos_meta.json"
    if not meta_file.exists():
        return

    import json
    with open(meta_file) as f:
        meta = json.load(f)

    # Build video list
    videos = []
    for vid_id, entry in meta.items():
        if entry.get("status") != "branded":
            continue
        out_path = WORKSPACE / entry.get("output_path", "")
        if not out_path.exists():
            continue
        videos.append({
            "id": vid_id,
            "title": entry.get("title", vid_id),
            "file": f"videos/{vid_id}.mp4",
            "thumbnail": entry.get("thumbnail", ""),
            "date": entry.get("upload_date", ""),
        })

    videos.sort(key=lambda x: x["date"], reverse=True)

    cards = []
    for v in videos:
        title = v["title"].replace('"', '&quot;')
        cards.append(f'''<div class="card">
  <video controls preload="metadata" poster="{v['thumbnail']}" playsinline>
    <source src="{v['file']}" type="video/mp4">
  </video>
  <div class="info">
    <h3>{title}</h3>
    <div class="meta">📅 {v['date'][:4]}-{v['date'][4:6]}-{v['date'][6:]} | United24 × OSMOSSAS</div>
    <a href="{v['file']}" download class="dl">⬇ Download</a>
  </div>
</div>''')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OSMOSSAS × United24 — Branded Shorts</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0a; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
.header {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #1a1a2e 0%, #0f0f1a 100%); border-bottom: 2px solid #c83250; }}
.header h1 {{ font-size: 2.2rem; margin-bottom: 8px; }}
.header span {{ color: #c83250; }}
.header p {{ color: #888; font-size: 0.95rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; padding: 30px; max-width: 1400px; margin: 0 auto; }}
.card {{ background: #151515; border-radius: 12px; overflow: hidden; border: 1px solid #222; transition: transform 0.2s, border-color 0.2s; }}
.card:hover {{ transform: translateY(-4px); border-color: #c83250; }}
.card video {{ width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; background: #000; }}
.card .info {{ padding: 16px; }}
.card h3 {{ font-size: 1rem; margin-bottom: 8px; line-height: 1.4; }}
.card .meta {{ font-size: 0.8rem; color: #888; margin-bottom: 12px; }}
.card .dl {{ display: inline-block; background: #c83250; color: #fff; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; }}
.card .dl:hover {{ background: #e04060; }}
.footer {{ text-align: center; padding: 30px; color: #555; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="header">
  <h1><span>OSMOSSAS</span> × United24</h1>
  <p>Branded Shorts | Credit to @united24media | Auto-generated gallery</p>
</div>
<div class="grid">
{chr(10).join(cards)}
</div>
<div class="footer">
  <p>Content from <a href="https://youtube.com/@united24media" style="color:#c83250;text-decoration:none;">@united24media</a> — Branded by OSMOSSAS</p>
</div>
</body>
</html>'''

    index_path = WORKSPACE / "output" / "index.html"
    with open(index_path, "w") as f:
        f.write(html)
    log(f"[Gallery] Generated {len(cards)} cards")

def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12

    log("=" * 50)
    log("U24 × OSMOSSAS Master Pipeline Starting")
    log(f"Limit: {limit} videos | Cap: {MAX_TOTAL} total")
    log("=" * 50)

    # Step 1: Download
    log("[STEP 1] Downloading United24 Shorts...")
    ok = run([sys.executable, str(WORKSPACE / "download.py"), str(limit * 2)], cwd=WORKSPACE)
    if not ok:
        log("[WARN] Download had issues, continuing...")

    # Step 2: Overlay branding
    log("[STEP 2] Applying OSMOSSAS branding...")
    ok = run([sys.executable, str(WORKSPACE / "overlay.py"), str(limit)], cwd=WORKSPACE)
    if not ok:
        log("[FATAL] Overlay failed")
        sys.exit(1)

    # Step 3: Rotate
    log("[STEP 3] Rotating videos...")
    rotate_videos()

    # Step 4: Gallery
    log("[STEP 4] Regenerating gallery...")
    generate_gallery()

    # Step 5: Git push
    GIT_DIR = OUTPUT_DIR / ".git"
    if GIT_DIR.exists():
        log("[STEP 5] Pushing to repo...")
        run(["git", "add", "videos/", "index.html"], cwd=OUTPUT_DIR)
        run(["git", "commit", "-m", f"auto: U24 shorts {datetime.now().strftime('%Y%m%d-%H%M')}"], cwd=OUTPUT_DIR)
        run(["git", "push"], cwd=OUTPUT_DIR)

    log("[DONE] Pipeline complete")
    log("=" * 50)

if __name__ == "__main__":
    main()
