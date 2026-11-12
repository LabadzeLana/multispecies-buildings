"""tools/make_panel_photo.py — generates a Building-page space panel's photo set.

Reads a source photograph (never modified in place) and writes 480/800/1200-wide
WebP + JPEG outputs into media/, named "<base>-<width>.<ext>", matching the
convention mediaSlot() already expects (see index.html, panel-courtyard-* /
panel-grapevines-* files). Crops to the panel frame's own aspect ratio
(1200x645, ~1.86:1) with a chosen vertical focal window, never upscales,
colour-manages from the source's own ICC profile to sRGB, strips all
metadata, and keeps each output under budget.

Run:  python3 tools/make_panel_photo.py                 (all jobs)
      python3 tools/make_panel_photo.py --only <base>    (just one job)
"""
import os
import sys
import io
from PIL import Image, ImageCms, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "media")

FRAME_W, FRAME_H = 1200, 645  # the panel photo frame's own aspect ratio (~1.86:1)
WIDTHS = [480, 800, 1200]
SRGB = ImageCms.createProfile("sRGB")

JOBS = [
    {
        "src": os.path.join(ROOT, "media", "building", "1.jpeg"),
        "base": "panel-grapevines-overhead-vine-01",
        "focal_y0": 607,  # top of the crop window, in source pixels (centered on the vine)
        "webp_quality": {480: 70, 800: 68, 1200: 64},
        "jpg_quality": {480: 66, 800: 64, 1200: 62},
    },
    {
        "src": os.path.join(ROOT, "media", "dogs", "12.jpg"),
        "base": "panel-dogs-street-dog-01",
        "focal_y0": 40,  # top of the crop window, in source pixels (keeps the dog's feet at the frame edge)
        "webp_quality": {480: 70, 800: 68, 1200: 64},
        "jpg_quality": {480: 66, 800: 64, 1200: 62},
    },
]


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    os.makedirs(OUT_DIR, exist_ok=True)
    for job in JOBS:
        if only and job["base"] != only:
            continue
        im = Image.open(job["src"])
        im.load()
        im = ImageOps.exif_transpose(im)
        icc = im.info.get("icc_profile")
        if icc:
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im, src_profile, SRGB, outputMode="RGB")
        else:
            im = im.convert("RGB")
        w, h = im.size
        crop_h = round(w * FRAME_H / FRAME_W)
        y0 = job["focal_y0"]
        y0 = max(0, min(y0, h - crop_h))
        cropped = im.crop((0, y0, w, y0 + crop_h))

        for width in WIDTHS:
            width = min(width, cropped.size[0])  # never upscale
            height = round(width * FRAME_H / FRAME_W)
            resized = cropped.resize((width, height), Image.LANCZOS)
            clean = Image.new("RGB", resized.size)
            clean.paste(resized)  # drop EXIF/GPS/ICC — fresh image, no metadata carried over

            webp_path = os.path.join(OUT_DIR, f"{job['base']}-{width}.webp")
            jpg_path = os.path.join(OUT_DIR, f"{job['base']}-{width}.jpg")
            clean.save(webp_path, "WEBP", quality=job["webp_quality"][width], method=6)
            clean.save(jpg_path, "JPEG", quality=job["jpg_quality"][width], optimize=True, progressive=True)
            print(f"{os.path.basename(webp_path):42s} {width}x{height} {os.path.getsize(webp_path)/1024:7.1f} KB")
            print(f"{os.path.basename(jpg_path):42s} {width}x{height} {os.path.getsize(jpg_path)/1024:7.1f} KB")


if __name__ == "__main__":
    main()
