#!/usr/bin/env python3
"""Builds the web copies of media/dogs/Lastdog.JPG for the Dogs page's closing
photo (stZoomFigure in index.html). Same conventions as tools/make_vineyards_photo.py:
colour-managed conversion to sRGB, EXIF orientation applied then all metadata
stripped, long edge resized by width (never upscaled), progressive JPEG plus a
WebP sibling at each width.

Usage:
    python3 tools/make_lastdog_photo.py <source> <out-dir> <name>
Writes <out-dir>/<name>-<w>.jpg and <out-dir>/<name>-<w>.webp for each width in
WIDTHS that does not exceed the source's own width.
"""
import sys, os, io
from PIL import Image, ImageCms, ImageOps

SRGB = ImageCms.createProfile("sRGB")
WIDTHS = (1200, 2400, 3200)


def make(src, out_dir, name):
    im = Image.open(src)
    im.load()
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src_profile, SRGB, outputMode="RGB")
    else:
        im = im.convert("RGB")
    w0, h0 = im.size
    for w in WIDTHS:
        tw = min(w, w0)  # never upscale
        th = round(h0 * tw / w0)
        resized = im.resize((tw, th), Image.LANCZOS) if tw != w0 else im
        jpg = os.path.join(out_dir, f"{name}-{w}.jpg")
        webp = os.path.join(out_dir, f"{name}-{w}.webp")
        resized.save(jpg, "JPEG", quality=72, optimize=True, progressive=True)
        resized.save(webp, "WEBP", quality=72, method=6)
        print(jpg, resized.size, os.path.getsize(jpg))
        print(webp, resized.size, os.path.getsize(webp))


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
