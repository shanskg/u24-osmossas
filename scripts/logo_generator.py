#!/usr/bin/env python3
"""Generate OSMOSSAS logo/badge assets for video overlay."""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path("./assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def create_watermark():
    text = "@osmossas"
    font = get_font(28)
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    img = Image.new("RGBA", (w + 20, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w + 20, h + 16], radius=8, fill=(0, 0, 0, 120))
    d.text((10, 6), text, font=font, fill=(255, 255, 255, 220))
    
    path = ASSETS_DIR / "watermark.png"
    img.save(path)
    return path

def create_corner_badge():
    text = "OSMOSSAS"
    font = get_font(18)
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    img = Image.new("RGBA", (w + 24, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w + 24, h + 14], radius=6, fill=(200, 50, 80, 180))
    d.text((12, 5), text, font=font, fill=(255, 255, 255, 240))
    
    path = ASSETS_DIR / "badge.png"
    img.save(path)
    return path

def create_logo_full():
    text = "OSMOSSAS"
    font = get_font(48)
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    img = Image.new("RGBA", (w + 40, h + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w + 40, h + 30], radius=12, fill=(200, 50, 80, 200))
    d.text((20, 12), text, font=font, fill=(255, 255, 255, 255))
    
    path = ASSETS_DIR / "logo_full.png"
    img.save(path)
    return path

if __name__ == "__main__":
    print("[Assets] Generating OSMOSSAS branding...")
    create_watermark()
    create_corner_badge()
    create_logo_full()
    print(f"[Assets] Saved to {ASSETS_DIR}")
