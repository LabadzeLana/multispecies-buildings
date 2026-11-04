"""tools/make_cartoon.py — generates the Dogs-page "cartoon reveal" layers
(ink lines -> flat painted colour -> real photograph) for the Dogs story's
final photograph ("Last Image": three puppies in a dark courtyard).

Adapted from the reference spec media/dogs/Last Image/cartoon-sample.py —
the SOFT style (hand-drawn ink lines + flat colour), never a halftone/
comic-book look. That reference script has no COMIC switch at all; this
script likewise has only the one, soft style.

Input (gitignored, never committed):
    media/dogs/Last Image/Last Image.jpg

Output (committed, in media/dogs/):
    dogs-final-cartoon-color-{1100,700}.webp   (quality ~78)
    dogs-final-cartoon-color-{1100,700}.jpg    (JPEG fallback)
    dogs-final-cartoon-lines-0{1,2,3}-{1100,700}.webp   (transparent, quality ~80)

All metadata (EXIF/GPS/time) is stripped from every output. Widths are
never upscaled past the source's own resolution.

Run:  python3 tools/make_cartoon.py
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import gaussian_filter, map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "media", "dogs", "Last Image", "Last Image.jpg")
OUT_DIR = os.path.join(ROOT, "media", "dogs")

# ---- output widths: desktop / mobile (never upscaled past the source) ----
WIDTHS = {"1100": 1100, "700": 700}
W_REF = 1100  # the width the pixel-space constants below were tuned at

# ---- look ----
BRIGHT = 1.55     # the photo is dark: lift it so the drawing reads (kept for reference;
SAT = 1.35        # the actual lift/saturation work is done via GAMMA/SAT2 below)
LINE_COLOR = (0x1B, 0x16, 0x12)   # ink colour, RGB
LINE_W = 3         # outline thickness, px at W_REF
BOIL = 3           # number of "boiling" line frames
BOIL_AMP = 2.2     # how much the lines wobble, px at W_REF

GAMMA = 0.58       # lift curve for the dark photo
SAT2 = 1.55        # saturation boost for the flat-colour layer
LEVELS = 7         # number of flat shading steps
CLAHE_CLIP = 2.4
CLAHE_TILE = (6, 6)

# puppy ellipses, as fractions of the frame: (centre x, centre y, half-width, half-height).
# Tuned for this exact photograph (confirmed pixel-identical to the sample's own source
# photo via a pixel-difference check against cartoon-reveal-sample.html's embedded layers).
DOGS = [(0.32, 0.53, 0.10, 0.075), (0.545, 0.47, 0.06, 0.12), (0.555, 0.81, 0.095, 0.115)]
DOG_MASK_BLUR = 22    # px at W_REF
DOG_MASK_GAIN = 2.0

# Canny edge thresholds are intensity-based, not spatial — they do NOT scale with width.
CANNY_SIGMA = 2.0     # px at W_REF (scales)
CANNY_LO, CANNY_HI = 14, 38
CANNY_MIN_AREA = 140  # px^2 at W_REF (scales by s^2)

COLOR_QUALITY = 78
COLOR_JPEG_QUALITY = 82
LINES_QUALITY = 80


def odd(n):
    n = max(1, round(n))
    return n if n % 2 == 1 else n + 1


def load_source(path):
    """Load + auto-rotate by EXIF orientation (PIL), hand off to OpenCV as BGR."""
    pil = Image.open(path)
    pil = ImageOps.exif_transpose(pil).convert("RGB")
    rgb = np.array(pil)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def render(src_bgr, width):
    s = width / W_REF  # spatial scale factor for this output size
    h0, w0 = src_bgr.shape[:2]
    width = min(width, w0)  # never upscale
    h = round(h0 * width / w0)
    img = cv2.resize(src_bgr, (width, h), interpolation=cv2.INTER_AREA)
    W = width

    # lift the dark photo, then make an illustrated, flat-shaded version that keeps the real colours
    f = img.astype(np.float32) / 255
    lab0 = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_TILE)
    lab0[..., 0] = clahe.apply(lab0[..., 0].astype(np.uint8)).astype(np.float32)
    lab0[..., 0] = 255 * np.clip(lab0[..., 0] / 255, 0, 1) ** GAMMA
    lift = cv2.cvtColor(np.clip(lab0, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

    dm = np.zeros((h, W), np.float32)
    for cx, cy, rx, ry in DOGS:
        cv2.ellipse(dm, (int(cx * W), int(cy * h)), (int(rx * W), int(ry * h)), 0, 0, 360, 1, -1)
    dm = np.clip(gaussian_filter(dm, DOG_MASK_BLUR * s) * DOG_MASK_GAIN, 0, 1)[..., None]

    # simplify at half resolution (big, calm shapes), then bring back
    small = cv2.resize(lift, (W // 2, h // 2), interpolation=cv2.INTER_AREA)
    for _ in range(3):
        small = cv2.bilateralFilter(small, odd(9 * s), 55, odd(9 * s))
    small = cv2.edgePreservingFilter(small, flags=1, sigma_s=70 * s, sigma_r=0.32)
    small = cv2.medianBlur(small, odd(5 * s))
    sm_bg = cv2.resize(small, (W, h), interpolation=cv2.INTER_CUBIC)
    sm_dog = lift
    for _ in range(2):
        sm_dog = cv2.bilateralFilter(sm_dog, odd(9 * s), 40, odd(7 * s))
    sm = (sm_bg * (1 - dm) + sm_dog * dm).astype(np.uint8)

    hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * SAT2, 0, 255)
    v = hsv[..., 2] / 255
    vq = np.round(v * (LEVELS - 1)) / (LEVELS - 1)
    hsv[..., 2] = (0.45 * v + 0.55 * vq) * 255
    flat = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    flat = cv2.medianBlur(flat, odd(7 * s))
    flat = cv2.GaussianBlur(flat, (0, 0), 0.8 * s)

    # outlines: Canny on the simplified picture (bold, calm); skip over the puppy areas
    # (the real, lightly simplified colours stay there instead, so the puppies read clearly)
    gray = cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY)
    gg = cv2.GaussianBlur(gray, (0, 0), CANNY_SIGMA * s)
    e = cv2.Canny(gg, CANNY_LO, CANNY_HI)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    n, cc, stats, _ = cv2.connectedComponentsWithStats(e, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= CANNY_MIN_AREA * s * s
    coarse = keep[cc].astype(np.uint8)
    coarse = coarse * (dm[..., 0] < 0.3).astype(np.uint8)
    line_w = odd(LINE_W * s) if LINE_W * s >= 1 else 1
    lines = cv2.dilate(coarse, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (line_w, line_w)))
    soft = np.clip(cv2.GaussianBlur(lines.astype(np.float32), (0, 0), 0.6 * s) * 1.3, 0, 1)

    sd = lift
    for _ in range(4):
        sd = cv2.bilateralFilter(sd, odd(9 * s), 45, odd(9 * s))
    sd = cv2.GaussianBlur(sd, (0, 0), 1.5 * s)
    flat = (flat * (1 - dm) + sd * dm).astype(np.uint8)

    def boil(alpha, seed):
        rs = np.random.RandomState(seed)
        dx = gaussian_filter(rs.randn(h, W), 14 * s)
        dy = gaussian_filter(rs.randn(h, W), 14 * s)
        amp = BOIL_AMP * s
        dx = dx / np.abs(dx).max() * amp
        dy = dy / np.abs(dy).max() * amp
        yy, xx = np.mgrid[0:h, 0:W].astype(np.float32)
        return map_coordinates(alpha, [yy + dy, xx + dx], order=1, mode="nearest")

    lines_rgba = []
    for i in range(BOIL):
        a = boil(soft, 10 + i)
        rgba = np.zeros((h, W, 4), np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = LINE_COLOR
        rgba[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
        lines_rgba.append(rgba)

    color_rgb = cv2.cvtColor(flat, cv2.COLOR_BGR2RGB)
    return color_rgb, lines_rgba, (W, h)


def save_webp(arr_rgba_or_rgb, path, quality):
    mode = "RGBA" if arr_rgba_or_rgb.shape[2] == 4 else "RGB"
    im = Image.fromarray(arr_rgba_or_rgb, mode)
    im.save(path, "WEBP", quality=quality, method=6)


def save_jpg(arr_rgb, path, quality):
    im = Image.fromarray(arr_rgb, "RGB")
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)


def main():
    if not os.path.isfile(SRC):
        raise SystemExit(f"source not found: {SRC}")
    src_bgr = load_source(SRC)
    os.makedirs(OUT_DIR, exist_ok=True)
    report = []
    for suffix, width in WIDTHS.items():
        color_rgb, lines_rgba, (w, h) = render(src_bgr, width)

        color_webp = os.path.join(OUT_DIR, f"dogs-final-cartoon-color-{suffix}.webp")
        color_jpg = os.path.join(OUT_DIR, f"dogs-final-cartoon-color-{suffix}.jpg")
        save_webp(color_rgb, color_webp, COLOR_QUALITY)
        save_jpg(color_rgb, color_jpg, COLOR_JPEG_QUALITY)
        report.append((color_webp, w, h, os.path.getsize(color_webp)))
        report.append((color_jpg, w, h, os.path.getsize(color_jpg)))

        for i, rgba in enumerate(lines_rgba, start=1):
            path = os.path.join(OUT_DIR, f"dogs-final-cartoon-lines-{i:02d}-{suffix}.webp")
            save_webp(rgba, path, LINES_QUALITY)
            report.append((path, w, h, os.path.getsize(path)))

    print(f"source: {SRC}  {src_bgr.shape[1]}x{src_bgr.shape[0]}")
    for path, w, h, size in report:
        print(f"{os.path.basename(path):42s} {w:5d}x{h:<5d} {size/1024:7.1f} KB")


if __name__ == "__main__":
    main()
