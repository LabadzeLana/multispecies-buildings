#!/usr/bin/env python3
"""Make the embossed-relief overlay images for chapter 2 ("Grapevines as Trees of Life") of
a-city-of-vineyards/index.html, from the existing web copies in media/vineyards/ (never upscaled;
these two photographs have no larger source — see media/vineyards/manifest.json).

Method (no live-in-the-browser effect; this is a static, repeatable pre-render):
  1. Denoise the luminance a little, then isolate a "detail" layer = luminance minus a heavily
     blurred copy of itself. This keeps the fine engraved/embossed structure (the tree-of-life
     ornament) and discards the broad photographic lighting of the original photo.
  2. Treat that detail layer as a height field, take its gradient (simple numpy Sobel, no scipy
     needed), and light it with a fixed top-left Lambertian light. The result is signed: positive
     where a surface would catch top-left light (highlight), negative where it would fall into
     shadow (shadow) — flat, detail-less areas end up ~0 either way.
  3. Turn that signed shading into a soft RGBA image: white where positive, an ink-tinted paper
     colour where negative, alpha = |shading|, gamma-shaped and blurred for softness, nothing
     else drawn — so on the page it sits directly on the paper colour with no background of its
     own, matching the pressed-out, same-colour-as-the-surface look of the reference image.

Usage (run from the repo root):
    python3 tools/vineyards/make_relief.py

Requires: numpy, Pillow (both already installed; no scipy, no network, no upscaling).
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MEDIA = os.path.join(ROOT, "media", "vineyards")

# Colours read from a-city-of-vineyards/index.html's own :root custom properties, so the relief
# sits on exactly this page's paper and uses its ink for the shadow side (never a new colour).
PAPER = (0xE8, 0xE9, 0xE5)
INK = (0x1B, 0x21, 0x1F)

# ---- tunable per image ------------------------------------------------------------------
# strength: overall relief depth (gradient multiplier). Raise it if the relief looks too faint,
# lower it if it looks noisy/harsh. Tuned separately per photo since the two panels (one
# brighter/more even metal, one more tarnished/uneven copper) picked up relief at different rates
# from the same settings.
IMAGES = [
    {"src": "vineyards-2-metalwork-01.jpg", "out": "vineyards-02-relief-01", "strength": 2.4},
    {"src": "vineyards-2-metalwork-02.jpg", "out": "vineyards-02-relief-02", "strength": 2.2},
]

DENOISE_SIGMA = 6.0      # pre-blur before anything else; this is what keeps the result calm —
                         # too small and the metal's own fine hammered texture reads as noise
                         # across the whole surface instead of staying quiet between the forms
DETAIL_SIGMA = 16.0      # radius of the broad blur subtracted out; sets the scale of ornament
                         # that "rises" (bigger = coarser forms stand out, fine texture flattens)
SOFT_SIGMA = 4.0         # final blur on the shaded result; this is what makes the edges soft
                         # (reference image) instead of a crisp bevel, and it also makes the
                         # alpha channel compress a good deal smaller as WebP
GAMMA = 1.6              # >1 suppresses weak, widespread shading (texture) relative to the
                         # strongest edges (the real contours), for a calmer result
HIGHLIGHT_ALPHA_MAX = 0.80
SHADOW_ALPHA_MAX = 0.62  # kept a bit lower than the highlight so the shadow reads as soft tone,
                         # not a dirty smear, per the brief
SHADOW_TINT = 0.68       # 0 = pure ink, 1 = pure paper; blends toward paper so the "shadow" is a
                         # warm soft shade of the page colour rather than flat black

# light from the top-left, in image space (x right, y down, z toward the viewer)
LIGHT = np.array([-1.0, -1.0, 1.0])
LIGHT /= np.linalg.norm(LIGHT)
FLAT_BASELINE = LIGHT[2]  # dot(N,L) for a perfectly flat surface (N = [0,0,1]); subtracted off
                          # so flat, detail-less regions shade to ~0 instead of a uniform grey


def gblur(arr, sigma):
    """Separable Gaussian blur on a float32 array, no scipy, no PIL float-mode filter (not
    supported by this Pillow build) — a plain numpy 1D-pass convolution instead."""
    if sigma <= 0:
        return arr
    radius = max(1, int(round(sigma * 3)))
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-(x * x) / (2 * sigma * sigma))
    kernel /= kernel.sum()

    def conv1d(a, axis):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (radius, radius)
        p = np.pad(a, pad, mode="edge")
        out = np.zeros_like(a)
        for i, k in enumerate(kernel):
            if axis == 0:
                out += k * p[i:i + a.shape[0], :]
            else:
                out += k * p[:, i:i + a.shape[1]]
        return out

    return conv1d(conv1d(arr, 0), 1)


def sobel(h):
    """Simple 3x3 Sobel gradient via array shifts (no scipy)."""
    p = np.pad(h, 1, mode="edge")
    gx = (
        (p[0:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2 * p[1:-1, 0:-2] + p[2:, 0:-2])
    ) / 8.0
    gy = (
        (p[2:, 0:-2] + 2 * p[2:, 1:-1] + p[2:, 2:])
        - (p[0:-2, 0:-2] + 2 * p[0:-2, 1:-1] + p[0:-2, 2:])
    ) / 8.0
    return gx, gy


def make_relief(src_path, strength):
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    gray = np.asarray(img.convert("L"), dtype=np.float32) / 255.0

    base = gblur(gray, DENOISE_SIGMA)
    broad = gblur(base, DETAIL_SIGMA)
    detail = base - broad  # signed, ~0-centred local contrast: the "height" of the relief

    gx, gy = sobel(detail * strength * 255.0)  # scale so the gradient magnitude is in sane units
    nx, ny, nz = -gx, -gy, np.ones_like(gx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / norm, ny / norm, nz / norm

    shade = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2] - FLAT_BASELINE

    shade = gblur(shade, SOFT_SIGMA)

    pos = np.clip(shade, 0, None)
    neg = np.clip(-shade, 0, None)
    pos = pos ** GAMMA if pos.max() > 0 else pos
    neg = neg ** GAMMA if neg.max() > 0 else neg
    pos = np.clip(pos / (np.percentile(pos, 99.5) + 1e-6), 0, 1) * HIGHLIGHT_ALPHA_MAX
    neg = np.clip(neg / (np.percentile(neg, 99.5) + 1e-6), 0, 1) * SHADOW_ALPHA_MAX

    shadow_color = tuple(INK[c] + (PAPER[c] - INK[c]) * SHADOW_TINT for c in range(3))

    alpha = np.clip(pos + neg, 0, 1)
    # colour: white where positive dominates, soft ink-paper tint where negative dominates,
    # blended by their relative share so the thin transition band doesn't hard-switch colour
    total = pos + neg + 1e-6
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for c in range(3):
        col = (pos * 255.0 + neg * shadow_color[c]) / total
        out[..., c] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

    return Image.fromarray(out, mode="RGBA")


def export(im, out_base, widths):
    paths = []
    for wtarget in widths:
        w, h = im.size
        if wtarget >= w:
            resized = im  # never upscale; the native size is the ceiling
            wtarget = w
        else:
            htarget = round(h * wtarget / w)
            resized = im.resize((wtarget, htarget), Image.LANCZOS)
        name = f"{out_base}-{wtarget}.webp"
        path = os.path.join(MEDIA, name)
        resized.save(path, "WEBP", quality=82, method=6)  # no exif/icc passed -> none written
        paths.append((name, resized.size, os.path.getsize(path)))
    return paths


def main():
    manifest_path = os.path.join(MEDIA, "manifest.json")
    manifest = json.load(open(manifest_path))

    for spec in IMAGES:
        src = os.path.join(MEDIA, spec["src"])
        relief = make_relief(src, spec["strength"])
        print(spec["src"], "->", spec["out"], "native", relief.size)
        files = export(relief, spec["out"], widths=[1150, 900])  # 1150 = native ceiling (no
        # upscale) stands in for the "desktop" 1600px target asked for; 900 for mobile
        for name, (w, h), nbytes in files:
            print("  ", name, f"{w}x{h}", nbytes, "bytes")

        for item in manifest["items"]:
            if item.get("files") and item["files"][0]["file"] == spec["src"]:
                item["relief"] = {
                    "strength": spec["strength"],
                    "files": [{"file": n, "px": f"{w}x{h}", "bytes": nb} for n, (w, h), nb in files],
                }

    json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=1)
    print("manifest updated:", manifest_path)


if __name__ == "__main__":
    main()
