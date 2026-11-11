#!/usr/bin/env python3
"""Fallback for tools/vineyards/build.py's single-image step, for when
`swiftc -O tools/vineyards/encode.swift -o /tmp/encode` cannot be built on this
machine (local Swift/SDK toolchain mismatch). Same effective spec as build.py:
colour-managed conversion to sRGB, JPEG quality ~0.72 (72/100), progressive,
long edge 2400px and 1200px (never upscaled), EXIF orientation applied, no
metadata written.

Usage:
    python3 tools/make_vineyards_photo.py <source> <out-dir> <name>
Writes <out-dir>/<name>.jpg (2400px long edge) and <out-dir>/<name>-1200.jpg
(1200px long edge).
"""
import sys, os, io
from PIL import Image, ImageCms, ImageOps

SRGB = ImageCms.createProfile("sRGB")


def _encode_one(src, out, max_long_edge, quality=72):
    im = Image.open(src)
    im.load()
    im = ImageOps.exif_transpose(im)  # apply EXIF orientation, like encode.swift
    icc = im.info.get("icc_profile")
    if icc:
        src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        im = ImageCms.profileToProfile(im, src_profile, SRGB, outputMode="RGB")
    else:
        im = im.convert("RGB")
    w, h = im.size
    long_edge = max(w, h)
    target = min(max_long_edge, long_edge)  # never upscale
    if target < long_edge:
        scale = target / long_edge
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    im.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size, os.path.getsize(out)


def make(src, out_dir, name):
    big = os.path.join(out_dir, name + ".jpg")
    small = os.path.join(out_dir, name + "-1200.jpg")
    for out, max_edge in ((big, 2400), (small, 1200)):
        size, nbytes = _encode_one(src, out, max_edge)
        print(out, size, nbytes)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
