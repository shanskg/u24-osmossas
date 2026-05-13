#!/usr/bin/env python3
"""Generate index.html gallery."""
import json
from pathlib import Path

OUTPUT_DIR = Path("../output")
META_FILE = OUTPUT_DIR / "videos_meta.json"

def main():
    if not META_FILE.exists():
        print("No meta file")
        return

    with open(META_FILE) as f:
        meta = json.load(f)

    videos = []
    for vid_id, entry in meta.items():
        if entry.get("status") != "branded":
            continue
        out_path = OUTPUT_DIR / entry.get("output_path", "")
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
        date_str = f"{v['date'][:4]}-{v['date'][4:6]}-{v['date'][6:]}" if len(v["date"]) == 8 else "Unknown"
        cards.append(f'''<div class="card">
  <video controls preload="metadata" poster="{v['thumbnail']}" playsinline>
    <source src="{v['file']}" type="video/mp4">
  </video>
  <div class="info">
    <h3>{title}</h3>
    <div class="meta">📅 {date_str} | United24 × OSMOSSAS</div>
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
.empty {{ text-align: center; padding: 80px 20px; color: #555; }}
.empty h2 {{ color: #c83250; margin-bottom: 12px; }}
.footer {{ text-align: center; padding: 30px; color: #555; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="header">
  <h1><span>OSMOSSAS</span> × United24</h1>
  <p>Branded Shorts | Credit to @united24media | Auto-generated gallery</p>
</div>
<div class="grid">
{chr(10).join(cards) if cards else '<div class="empty"><h2>🎬 No videos yet</h2><p>Pipeline is running — check back soon!</p></div>'}
</div>
<div class="footer">
  <p>Content from <a href="https://youtube.com/@united24media" style="color:#c83250;text-decoration:none;">@united24media</a> — Branded by OSMOSSAS</p>
</div>
</body>
</html>'''

    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(html)

    print(f"Gallery: {len(cards)} cards")

if __name__ == "__main__":
    main()
