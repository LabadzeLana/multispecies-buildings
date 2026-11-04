"""Render favicon.svg's exact design (building elevation + climbing vine) to PNGs
via PIL, at a chosen set of pixel sizes, by reproducing the same vector shapes
(not rasterizing the SVG file itself -- avoids needing a system SVG renderer).
Draws at high supersample resolution then downsamples with LANCZOS for clean
anti-aliased edges at small sizes."""
from PIL import Image, ImageDraw
import os

PAPER = (0xE8, 0xE9, 0xE5, 255)
INK = (0x1B, 0x21, 0x1F, 255)
VINE = (0x4E, 0x6B, 0x3B, 255)

SS = 16  # supersample factor relative to the 64x64 viewBox -> 1024px working canvas


def cubic_bezier_points(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = (mt**3) * p0[0] + 3 * (mt**2) * t * p1[0] + 3 * mt * (t**2) * p2[0] + (t**3) * p3[0]
        y = (mt**3) * p0[1] + 3 * (mt**2) * t * p1[1] + 3 * mt * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x * SS, y * SS))
    return pts


def thick_polyline(draw, pts, width, fill):
    r = width * SS / 2
    for (x, y) in pts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)
    draw.line(pts, fill=fill, width=round(width * SS), joint="curve")


def leaf(draw, p0, c1, c2, p3, c4, c5, p6, fill):
    # two cubic bezier curves sharing endpoints p0 and p6 (p0==p3 start/end of stem attach),
    # forming a closed lens/leaf shape
    pts = cubic_bezier_points(p0, c1, c2, p3, 24) + cubic_bezier_points(p3, c4, c5, p6, 24)
    draw.polygon(pts, fill=fill)


def render(size):
    W = 64 * SS
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # background: rounded square, paper
    d.rounded_rectangle([2 * SS, 2 * SS, 62 * SS, 62 * SS], radius=9 * SS, fill=PAPER)

    # building outline
    d.rectangle([14 * SS, 15 * SS, 42 * SS, 52 * SS], outline=INK, width=round(2.2 * SS))
    # grid lines
    d.line([(14 * SS, 26 * SS), (42 * SS, 26 * SS)], fill=INK, width=round(1.4 * SS))
    d.line([(14 * SS, 37 * SS), (42 * SS, 37 * SS)], fill=INK, width=round(1.4 * SS))
    d.line([(28 * SS, 15 * SS), (28 * SS, 52 * SS)], fill=INK, width=round(1.4 * SS))
    # door
    d.rectangle([24 * SS, 44 * SS, 32 * SS, 52 * SS], outline=INK, width=round(1.4 * SS))

    # vine stem: M46 54 C44 46 50 40 47 33 C44 26 50 20 47 13
    stem = cubic_bezier_points((46, 54), (44, 46), (50, 40), (47, 33), 40)
    stem += cubic_bezier_points((47, 33), (44, 26), (50, 20), (47, 13), 40)
    thick_polyline(d, stem, 2.1, VINE)

    # three leaves
    leaf(d, (47, 33), (50, 31), (54, 31), (55, 28), (52, 29), (49, 30), (47, 33), VINE)
    leaf(d, (46, 44), (49, 43), (52, 44), (54, 41), (51, 41), (48, 42), (46, 44), VINE)
    leaf(d, (47, 15), (44, 11), (40, 11), (39, 8), (42, 10), (45, 12), (47, 15), VINE)

    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__)) + "/.."
    targets = {
        "favicon-16.png": 16,
        "favicon-32.png": 32,
        "apple-touch-icon.png": 180,
    }
    for name, size in targets.items():
        img = render(size)
        path = os.path.join(out_dir, name)
        img.save(path, "PNG", optimize=True)
        print(name, size, os.path.getsize(path), "bytes")
