"""tools/make_share_images.py — generates the Open Graph / Twitter share images.

Reads existing site photographs (never modified, renamed or deleted) and writes
1200x630 JPEGs into media/share/, cropped (never stretched) to keep the focal
subject inside the central safe area, with all metadata (EXIF/GPS) stripped.

Sources:
    2022-07-06 13.29.46-1.jpg                              -> share-main-1200x630.jpg
    media/vineyards/vineyards-12-vine-shadows-video-poster.jpg -> share-grapevines-1200x630.jpg

Run:  python3 tools/make_share_images.py
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "media", "share")

W, H = 1200, 630
TARGET_AR = W / H

JOBS = [
    {
        "src": os.path.join(ROOT, "2022-07-06 13.29.46-1.jpg"),
        "out": os.path.join(OUT_DIR, "share-main-1200x630.jpg"),
        "focus_y": 0.40,  # keep more of the ivy-covered facade + trees, less pavement
        "quality": 82,
    },
    {
        "src": os.path.join(ROOT, "media", "vineyards", "vineyards-12-vine-shadows-video-poster.jpg"),
        "out": os.path.join(OUT_DIR, "share-grapevines-1200x630.jpg"),
        "focus_y": 0.50,
        "quality": 85,
    },
]


def cover_crop(im, target_w, target_h, focus_y=0.5):
    """Crop (never stretch/scale up) to target_w x target_h, covering the frame.
    focus_y in [0,1] picks where the kept vertical band is centred (0=top, 1=bottom)."""
    w, h = im.size
    src_ar = w / h
    target_ar = target_w / target_h
    if src_ar > target_ar:
        # source is relatively wider: crop width, keep full height
        new_w = round(h * target_ar)
        new_h = h
        x0 = round((w - new_w) * 0.5)
        y0 = 0
    else:
        # source is relatively taller: crop height, keep full width
        new_w = w
        new_h = round(w / target_ar)
        x0 = 0
        y0 = round((h - new_h) * focus_y)
        y0 = max(0, min(y0, h - new_h))
    box = (x0, y0, x0 + new_w, y0 + new_h)
    cropped = im.crop(box)
    if cropped.size != (target_w, target_h):
        if cropped.size[0] < target_w or cropped.size[1] < target_h:
            raise SystemExit(f"source too small to cover {target_w}x{target_h}: {im.size}")
        cropped = cropped.resize((target_w, target_h), Image.LANCZOS)
    return cropped


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for job in JOBS:
        im = Image.open(job["src"])
        im = im.convert("RGB")  # drop alpha/CMYK, normalise to sRGB-safe mode
        cropped = cover_crop(im, W, H, job.get("focus_y", 0.5))
        # re-save with a fresh Image so no EXIF/ICC/GPS metadata carries over
        clean = Image.new("RGB", cropped.size)
        clean.paste(cropped)
        quality = job["quality"]
        clean.save(job["out"], "JPEG", quality=quality, optimize=True, progressive=True)
        size = os.path.getsize(job["out"])
        # re-encode at lower quality if still over the 300 KB budget
        while size > 300_000 and quality > 55:
            quality -= 5
            clean.save(job["out"], "JPEG", quality=quality, optimize=True, progressive=True)
            size = os.path.getsize(job["out"])
        print(f"{job['out']}  {clean.size[0]}x{clean.size[1]}  q={quality}  {size/1024:.1f} KB")


if __name__ == "__main__":
    main()
