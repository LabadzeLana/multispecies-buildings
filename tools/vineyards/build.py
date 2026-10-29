#!/usr/bin/env python3
"""Make the web copies for "A City of Vineyards" from the originals and write media/vineyards/manifest.json.

Run from the repo root (macOS only):
    swiftc -O tools/vineyards/encode.swift -o /tmp/encode
    python3 tools/vineyards/build.py /tmp/encode

Originals are only read, never moved or renamed. Photos: JPEG q0.72, long edge 2400 px and 1200 px
(never upscaled), sRGB, no metadata. Videos: H.264 MP4, faststart, no metadata, poster JPEG.
"""
import json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
plan = json.load(open(os.path.join(os.path.dirname(__file__), "plan.json")))
enc = sys.argv[1] if len(sys.argv) > 1 else "encode"
src_dir = os.path.join(ROOT, plan["source"])
out_dir = os.path.join(ROOT, plan["out"])
os.makedirs(out_dir, exist_ok=True)

def run(*a):
    return subprocess.run([enc, *map(str, a)], check=True, capture_output=True, text=True).stdout.split()

def strip_app1(path):
    # ImageIO still writes a tiny Exif block (pixel size only); drop every APP1 (Exif/XMP) segment
    d = open(path, "rb").read()
    out, i = bytearray(d[:2]), 2
    while i < len(d) and d[i] == 0xFF and d[i + 1] != 0xDA:
        n = int.from_bytes(d[i + 2:i + 4], "big")
        if d[i + 1] != 0xE1:
            out += d[i:i + 2 + n]
        i += 2 + n
    open(path, "wb").write(bytes(out + d[i:]))

def size(name):
    return os.path.getsize(os.path.join(out_dir, name))

def probe(path):
    # original pixel size via sips (reads HEIC too); duration for videos via Spotlight
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path], capture_output=True, text=True).stdout
    vals = dict(l.split(": ") for l in (x.strip() for x in out.splitlines()) if ": " in l)
    return vals.get("pixelWidth", "?"), vals.get("pixelHeight", "?")

def probe_video(path):
    out = subprocess.run(["mdls", "-raw", "-name", "kMDItemDurationSeconds", "-name", "kMDItemPixelHeight",
                          "-name", "kMDItemPixelWidth", path], capture_output=True, text=True).stdout
    d, h, w = [v.strip() for v in out.split("\0")]   # mdls prints the attributes in alphabetical order
    return w, h, round(float(d), 2)

items = []
for im in plan["images"]:
    src = os.path.join(src_dir, im["src"])
    big, small = im["name"] + ".jpg", im["name"] + "-1200.jpg"
    w, h = map(int, run("image", src, os.path.join(out_dir, big), 2400, 0.72))
    w2, h2 = map(int, run("image", src, os.path.join(out_dir, small), 1200, 0.72))
    strip_app1(os.path.join(out_dir, big)); strip_app1(os.path.join(out_dir, small))
    ow, oh = probe(src)
    items.append({"chapter": im["ch"], "type": "photo", "original": im["src"],
                  "original_px": f"{ow}x{oh}", "original_bytes": os.path.getsize(src),
                  "files": [{"file": big, "px": f"{w}x{h}", "bytes": size(big)},
                            {"file": small, "px": f"{w2}x{h2}", "bytes": size(small)}],
                  "credit": im["credit"], "alt": im["alt"], "description": im["desc"]})
    print(big, w, h, size(big))

for v in plan["videos"]:
    src = os.path.join(src_dir, v["src"])
    mp4, poster = v["name"] + ".mp4", v["name"] + "-poster.jpg"
    w, h, dur = run("video", src, os.path.join(out_dir, mp4), v["maxW"], v["maxH"], v["kbps"],
                    1 if v["audio"] else 0, v.get("start", 0), v.get("dur", 0))
    pw, ph = run("poster", src, os.path.join(out_dir, poster), v["poster"], max(int(w), int(h)), 0.72)
    strip_app1(os.path.join(out_dir, poster))
    ow, oh, od = probe_video(src)
    items.append({"chapter": v["ch"], "type": "video", "original": v["src"],
                  "original_px": f"{ow}x{oh}", "original_seconds": od, "original_bytes": os.path.getsize(src),
                  "files": [{"file": mp4, "px": f"{w}x{h}", "seconds": float(dur), "bytes": size(mp4),
                             "audio": "AAC 128 kb/s stereo" if v["audio"] else "none"},
                            {"file": poster, "px": f"{pw}x{ph}", "bytes": size(poster)}],
                  "credit": v["credit"], "alt": v["alt"], "description": v["desc"]})
    print(mp4, w, h, dur, size(mp4))

total = sum(f["bytes"] for i in items for f in i["files"])
json.dump({"note": "Web copies for a-city-of-vineyards/index.html. Credits and captions exactly as in "
                   "'Visual story of grapevine.docx'. Chapter 0 = opening background.",
           "total_bytes": total, "items": items},
          open(os.path.join(out_dir, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("total", total)
