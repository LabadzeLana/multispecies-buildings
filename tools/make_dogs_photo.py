#!/usr/bin/env python3
"""Builds the web copies of a Dogs-page photo in the plain src+thumb convention most of
the page's galleries use (e.g. media/dogs/17.jpg + media/dogs/thumb/17.jpg): a full-size
JPEG at 1600px long edge and a thumbnail at 600px long edge, both never upscaled beyond the
source. sRGB (colour-managed from the source's own profile), EXIF orientation applied then
all metadata stripped, quality 72, progressive.

Usage:
    python3 tools/make_dogs_photo.py <source> <out-dir> <name>
Writes <out-dir>/<name>.jpg (1600px long edge) and <out-dir>/thumb/<name>.jpg (600px long
edge).
"""
import sys, os, io
from PIL import Image, ImageCms, ImageOps

SRGB = ImageCms.createProfile("sRGB")


def _encode_one(im, out, max_long_edge, quality=72):
    w, h = im.size
    long_edge = max(w, h)
    target = min(max_long_edge, long_edge)  # never upscale
    out_im = im
    if target < long_edge:
        scale = target / long_edge
        out_im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    out_im.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    return out_im.size, os.path.getsize(out)


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

    thumb_dir = os.path.join(out_dir, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    big = os.path.join(out_dir, name + ".jpg")
    small = os.path.join(thumb_dir, name + ".jpg")
    for out, max_edge in ((big, 1600), (small, 600)):
        size, nbytes = _encode_one(im, out, max_edge)
        print(out, size, nbytes)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
