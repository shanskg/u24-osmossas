# U24 × OSMOSSAS — Branded Shorts Pipeline

Automatically download United24 YouTube Shorts, apply OSMOSSAS branding, and publish a gallery.

**Gallery**: https://shanskg.github.io/u24-osmossas/

---

## How It Works

This repo runs on **GitHub Actions** every 2 hours. The pipeline:

1. **Downloads** United24 Shorts (or processes manual uploads)
2. **Overlays** OSMOSSAS branding (watermark + badge)
3. **Rotates** archive (150 main + 10 top videos max)
4. **Generates** an HTML gallery
5. **Deploys** to GitHub Pages

---

## Two Ways to Add Videos

### Option 1: Auto-Download (May Not Work)

The pipeline tries to auto-download from `youtube.com/@united24media/shorts`.

⚠️ **YouTube blocks most cloud/datacenter IPs** (including GitHub Actions). If auto-download fails, use Option 2.

### Option 2: Manual Upload (Recommended)

Drop MP4 files into the **`input/` folder** in this repo, then push. The next pipeline run will:
- Copy them to `output/raw/`
- Apply branding
- Add them to the gallery

```bash
# Clone the repo
git clone https://github.com/shanskg/u24-osmossas.git
cd u24-osmossas

# Copy your MP4s
cp ~/Downloads/*.mp4 input/

# Push
git add input/
git commit -m "manual upload"
git push
```

The pipeline runs automatically after every push.

---

## Local Download Helper

If you want to download Shorts on your **local machine** (which YouTube doesn't block) and then upload:

```bash
# Run this on your home computer
python3 scripts/local_download.py

# Then upload the downloaded files
cp output/raw/*.mp4 input/
git add input/
git commit -m "local downloads"
git push
```

---

## Pipeline Status

Check runs: https://github.com/shanskg/u24-osmossas/actions

---

## Branding

- **Badge**: `OSMOSSAS` (top-right corner)
- **Watermark**: `@osmossas` (bottom-center)
- **Original U24 content**: Fully preserved, never obscured

---

## Limits

| Limit | Value |
|-------|-------|
| Max total videos | 150 |
| Max "top" videos | 10 |
| Video format | 1080×1920 MP4 |
| Schedule | Every 2 hours |

---

## File Structure

```
u24-osmossas/
├── .github/workflows/pipeline.yml  # GitHub Actions workflow
├── scripts/
│   ├── download_gha.py             # Auto-download (GitHub Actions)
│   ├── local_download.py           # Download helper for local machines
│   ├── manual_upload.py            # Process input/ folder
│   ├── overlay.py                  # Apply branding
│   ├── rotate.py                   # Keep video count within caps
│   ├── gallery.py                  # Generate index.html
│   └── logo_generator.py           # Create badge/watermark assets
├── assets/                         # Branding images
├── input/                          # Drop MP4s here for manual upload
└── output/
    ├── videos/                     # Branded videos (git-tracked)
    ├── raw/                        # Pre-branding downloads (.gitignored)
    └── index.html                  # Gallery page
```
