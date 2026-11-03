#!/usr/bin/env python3
"""Make the embossed-relief overlay and the real-photo web copies for chapter 2
("Grapevines as Trees of Life") of a-city-of-vineyards/index.html.

Adapted from the reference a-city-of-vineyards/relief-sample.py (not committed, see .gitignore),
which is kept as the algorithm's starting point. Source images: media/vineyards/
vineyards-2-metalwork-01.jpg and -02.jpg. The brief asked for the true originals (the numbered
chapter-2 folder under "ვაზის მულტიმოდალური ისტორია"), but that folder is not present on this
machine (checked the project and a whole-disk Spotlight search) -- confirmed with the user to use
these instead. Per media/vineyards/manifest.json they are the same 1150x862 pixels as the
(missing) originals, so this loses no detail; everything below is "never upscale" accordingly:
1150px is the ceiling for both the relief and the real photo, even though the brief's 1200/2400 and
1000/700 targets assume a bigger source.

Usage (run from the repo root):
    python3 tools/make_relief.py

Requires: numpy, scipy, Pillow. scipy was not installed on this machine; installed with
`pip3 install --user scipy` (numpy and Pillow were already present).
"""
import json
import os

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, shift

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "media", "vineyards")
OUT_DIR = os.path.join(ROOT, "media", "vineyards")

# Paper/ink read from a-city-of-vineyards/index.html's own :root custom properties (not the
# sample's placeholder ink) -- this is what makes the relief sit on exactly this page's colours.
PAPER = (0xE8, 0xE9, 0xE5)
INK = (0x1B, 0x21, 0x1F)

RELIEF_WIDTHS = (1000, 700)   # desktop, mobile -- capped to the 1150px source, see module docstring
# the brief asks for 1200px and 2400px photo copies; both are wider than this 1150px source, so
# both collapse to the same single, native-resolution, never-upscaled file -- see export_photo()
RELIEF_QUALITY = 68
PHOTO_QUALITY_WEBP = 78
PHOTO_QUALITY_JPEG = 78

# ---- per-image parameters, starting from relief-sample.py's own values -------------------
# gain: how strongly local (fine) detail is pushed toward fully raised/sunk.
# ds, blur_s: the double-shadow offset and its blur, in source-resolution px (at W below).
# big: radius of the broad blur that fine detail is measured against.
# edge: strength of the edge-lighting term from the height gradient.
# mid: weight of the broad-forms term (whole bodies/leaves rising as a shape, not just their edges).
# box: (x0,y0,x1,y1) as fractions of the frame -- the metal panel itself, checked against the real
#   photographs (both match the sample's own box closely: the panel fills almost the whole frame
#   with a thin margin).
IMAGES = [
    {
        "src": "vineyards-2-metalwork-01.jpg",
        "relief_out": "vineyards-02-relief-01",
        "photo_out": "vineyards-02-photo-01",
        "alt": "Metal relief: a figure holding a bunch of grapes among vine leaves",
        "W": 1000, "gain": 3.6, "ds": 5.0, "blur_s": 1.2, "big": 20.0, "edge": 0.9, "mid": 0.7,
        "box": (0.15, 0.02, 0.92, 0.86), "outside": 0.4, "feather": 14,
        "highlight_factor": 0.62, "shadow_max": 0.8,
    },
    {
        "src": "vineyards-2-metalwork-02.jpg",
        "relief_out": "vineyards-02-relief-02",
        "photo_out": "vineyards-02-photo-02",
        "alt": "Copper relief: a kneeling figure tending a young vine with grape clusters",
        "W": 1000, "gain": 3.6, "ds": 5.0, "blur_s": 1.2, "big": 20.0, "edge": 0.9, "mid": 0.9,
        "box": (0.13, 0.13, 0.85, 0.92), "outside": 0.4, "feather": 14,
        "highlight_factor": 0.62, "shadow_max": 0.8,
    },
]


def make_relief(src_path, W, gain, ds, blur_s, big, edge, mid, box, outside, feather,
                 highlight_factor, shadow_max):
    im = Image.open(src_path).convert("RGB")
    native_w = im.width
    W = min(W, native_w)  # never upscale
    h = round(im.height * W / im.width)
    im_w = im.resize((W, h), Image.LANCZOS)
    a = np.asarray(im_w).astype(np.float32) / 255
    L = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]

    # local relief: what stands out from its immediate surroundings
    d = gaussian_filter(L, blur_s) - gaussian_filter(L, big)
    hgt = np.tanh(d * gain)  # -1..1 (dark detail sinks, light detail rises)
    if mid:  # broad forms (bodies, leaves) rise as a whole, not just their edges
        dm = gaussian_filter(L, 5) - gaussian_filter(L, 48)
        hgt = np.clip(hgt * 0.8 + mid * np.tanh(dm * 2.6), -1, 1)
    hgt = gaussian_filter(hgt, 0.7)

    if box:
        x0, y0, x1, y1 = box
        mk = np.zeros((h, W), np.float32)
        mk[int(y0 * h):int(y1 * h), int(x0 * W):int(x1 * W)] = 1
        mk = gaussian_filter(mk, feather)
        mk = outside + (1 - outside) * mk
        hgt = hgt * mk

    m = np.clip(hgt * 0.5 + 0.5, 0, 1)  # 0..1 height

    # soft double shadow, like a neumorphic emboss: a shifted, blurred copy of the raised mask
    # offset down-right (shadow) and up-left (highlight)
    raised = np.clip(hgt * 1.6, 0, 1)
    sh = gaussian_filter(shift(raised, (ds, ds), order=1, mode="nearest"), ds * 0.7) * (1 - raised * 0.6)
    li = gaussian_filter(shift(raised, (-ds * 0.8, -ds * 0.8), order=1, mode="nearest"), ds * 0.6) * (1 - raised * 0.6)

    # edge lighting from the height gradient (light from the top-left)
    gy, gx = np.gradient(gaussian_filter(m, 0.9))
    s = (gx + gy) * edge * 14
    hi = np.clip(s, 0, 1)
    lo = np.clip(-s, 0, 1)

    A_shadow = np.clip(sh * 0.9 + lo * 0.6, 0, shadow_max)
    A_light = np.clip((li * 1.0 + hi * 0.75) * highlight_factor, 0, shadow_max)

    tot = A_shadow + A_light * (1 - A_shadow)
    col = np.zeros((h, W, 3), np.float32)
    for c in range(3):
        col[..., c] = (
            INK[c] / 255 * A_shadow * (1 - A_light) + 1.0 * A_light
        ) / np.maximum(A_shadow * (1 - A_light) + A_light, 1e-4)

    rgba = np.zeros((h, W, 4), np.float32)
    rgba[..., :3] = col
    rgba[..., 3] = np.clip(tot, 0, 1)
    return Image.fromarray((rgba * 255).astype(np.uint8), "RGBA"), native_w, im.height


def strip_app1(path):
    """Drop every APP1 (Exif/XMP) JPEG segment, same technique as tools/vineyards/build.py."""
    d = open(path, "rb").read()
    out, i = bytearray(d[:2]), 2
    while i < len(d) and d[i] == 0xFF and d[i + 1] != 0xDA:
        n = int.from_bytes(d[i + 2:i + 4], "big")
        if d[i + 1] != 0xE1:
            out += d[i:i + 2 + n]
        i += 2 + n
    open(path, "wb").write(bytes(out + d[i:]))


def export_relief(rgba, out_base, widths):
    files = []
    nat_w = rgba.width
    for w in widths:
        w = min(w, nat_w)
        h = round(rgba.height * w / rgba.width)
        resized = rgba if w == nat_w else rgba.resize((w, h), Image.LANCZOS)
        name = f"{out_base}-{w}.webp"
        path = os.path.join(OUT_DIR, name)
        resized.save(path, "WEBP", quality=RELIEF_QUALITY, method=6)  # no exif/icc -> none written
        files.append({"file": name, "px": f"{w}x{h}", "bytes": os.path.getsize(path)})
    return files


def export_photo(src_path, out_base):
    """Both the 1200px and 2400px targets the brief asks for are wider than this 1150px source,
    so -- never upscaling -- they collapse to the same single, native-resolution file; producing
    two identically-sized "1200" and "2400" copies would just be the same bytes under two names
    (exactly the duplication already sitting in media/vineyards/ from the original chapter-2
    build), so this makes one WebP + one JPEG fallback at native size instead."""
    im = Image.open(src_path).convert("RGB")
    im.info.pop("exif", None)
    w, h = im.size
    webp_name, jpg_name = f"{out_base}.webp", f"{out_base}.jpg"
    webp_path, jpg_path = os.path.join(OUT_DIR, webp_name), os.path.join(OUT_DIR, jpg_name)
    im.save(webp_path, "WEBP", quality=PHOTO_QUALITY_WEBP, method=6)
    im.save(jpg_path, "JPEG", quality=PHOTO_QUALITY_JPEG, optimize=True, progressive=True)
    strip_app1(jpg_path)
    files = [
        {"file": webp_name, "px": f"{w}x{h}", "bytes": os.path.getsize(webp_path)},
        {"file": jpg_name, "px": f"{w}x{h}", "bytes": os.path.getsize(jpg_path)},
    ]
    return files, w


def main():
    manifest_path = os.path.join(SRC_DIR, "manifest.json")
    manifest = json.load(open(manifest_path))

    for spec in IMAGES:
        src = os.path.join(SRC_DIR, spec["src"])
        rgba, native_w, native_h = make_relief(
            src, spec["W"], spec["gain"], spec["ds"], spec["blur_s"], spec["big"], spec["edge"],
            spec["mid"], spec["box"], spec["outside"], spec["feather"],
            spec["highlight_factor"], spec["shadow_max"],
        )
        print(spec["src"], "-> native", f"{native_w}x{native_h}", "(never upscaled beyond this)")
        relief_files = export_relief(rgba, spec["relief_out"], RELIEF_WIDTHS)
        for f in relief_files:
            print("  relief", f["file"], f["px"], f["bytes"], "bytes")
        photo_files, _ = export_photo(src, spec["photo_out"])
        for f in photo_files:
            print("  photo ", f["file"], f["px"], f["bytes"], "bytes")

        for item in manifest["items"]:
            if item.get("files") and item["files"][0]["file"] == spec["src"]:
                item.pop("relief", None)  # drop the previous task's relief sub-object
                item["relief"] = {
                    "params": {k: spec[k] for k in
                               ("gain", "ds", "blur_s", "big", "edge", "mid", "box",
                                "outside", "feather", "highlight_factor", "shadow_max")},
                    "files": relief_files,
                }
                item["chapter2_photo_copies"] = photo_files

    json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=1)
    print("manifest updated:", manifest_path)


if __name__ == "__main__":
    main()
