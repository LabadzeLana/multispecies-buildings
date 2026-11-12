#!/usr/bin/env python3
"""Builds the web copies of a Dogs-page gallery photo for shared/filmstrip-carousel.js
(the same two-tier convention the existing carousel frames already use: a full-size JPEG
capped at the source's own resolution, never upscaled, plus a 1200px-long-edge sibling).
sRGB (colour-managed from the source's own profile), EXIF orientation applied then all
metadata stripped, quality 72, progressive.

Usage:
    python3 tools/make_dogs_gallery_photo.py <source> <out-dir> <name>
Writes <out-dir>/<name>.jpg (full size) and <out-dir>/<name>-1200.jpg (1200px long edge).
"""
import sys, os, io
from PIL import Image, ImageCms, ImageOps

SRGB = ImageCms.createProfile("sRGB")


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
    w, h = im.size
    full = os.path.join(out_dir, name + ".jpg")
    im.save(full, "JPEG", quality=72, optimize=True, progressive=True)
    print(full, im.size, os.path.getsize(full))

    small_path = os.path.join(out_dir, name + "-1200.jpg")
    long_edge = max(w, h)
    target = min(1200, long_edge)  # never upscale
    scale = target / long_edge
    small = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS) if scale < 1 else im
    small.save(small_path, "JPEG", quality=72, optimize=True, progressive=True)
    print(small_path, small.size, os.path.getsize(small_path))


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
