#!/usr/bin/env python3
"""tools/make_building_facade_photo.py — builds the Building page's shared facade photo.

Reads media/building/main.jpg (never modified) and writes one optimised, colour-managed,
metadata-stripped JPEG: media/building/building-facade-main.jpg. This single file is used
by several BUILDING_ZONES entries (Stairwell, Elevator, Courtyard, Grapevines, Pipes), each
with its own CSS background-position — matching the existing single-file-per-photo
convention the Building zoom already uses (no WebP, no base/detail tier).

main.jpg is already 1600x1200, the same size the other zone photos use, so this is a clean
re-encode (sRGB, metadata stripped) rather than a resize; it is never upscaled.

Run: python3 tools/make_building_facade_photo.py
"""
import os
import io
from PIL import Image, ImageCms, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "media", "building", "main.jpg")
OUT = os.path.join(ROOT, "media", "building", "building-facade-main.jpg")
SRGB = ImageCms.createProfile("sRGB")


def main():
    im = Image.open(SRC)
    im.load()
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src_profile, SRGB, outputMode="RGB")
    else:
        im = im.convert("RGB")
    clean = Image.new("RGB", im.size)
    clean.paste(im)  # drop EXIF/GPS/ICC — fresh image, no metadata carried over
    clean.save(OUT, "JPEG", quality=78, optimize=True, progressive=True)
    print(os.path.basename(OUT), clean.size, f"{os.path.getsize(OUT)/1024:.1f} KB")


if __name__ == "__main__":
    main()
