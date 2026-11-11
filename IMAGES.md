# Share images (Open Graph / Twitter)

`media/share/` holds the social-preview images referenced by the `og:image` /
`twitter:image` tags in `index.html` and `a-city-of-vineyards/index.html`.

- `share-main-1200x630.jpg` — cropped from the cover photograph
  `2022-07-06 13.29.46-1.jpg` (repo root).
- `share-grapevines-1200x630.jpg` — cropped from
  `media/vineyards/vineyards-12-vine-shadows-video-poster.jpg`, the same
  vine-shadow image used as the Grapevines page's own hero/background, at its
  higher-resolution (1920x1080) source so the crop needs no upscaling.

Both are 1200x630 JPEGs, sRGB, with all EXIF/GPS metadata stripped, kept under
300 KB. Source photographs are never modified — only read and cropped into
new output files.

Regenerate with:

```
python3 tools/make_share_images.py
```

# Building page: space panel photographs

Each space's photograph card (`mediaSlot()` in `index.html`, `media:[{t:"photo",base:...}]`
in `T.spaces`) loads `media/<base>-{480,800,1200}.{webp,jpg}` — flat filenames directly
under `media/`, not a subfolder, matching the panel frame's own ~1.86:1 aspect ratio
(1200x645 at full size).

- `panel-grapevines-overhead-vine-01-{480,800,1200}.{webp,jpg}` — the Grapevines panel's
  photograph, cropped (vertically centered, no upscaling) from `media/building/1.jpeg`,
  a source photo kept on disk only and never committed (see `.gitignore`). sRGB, all
  EXIF/GPS metadata stripped, each size under budget (480 ≈ 36 KB, 800 ≈ 90 KB,
  1200 ≈ 183 KB).

Regenerate with:

```
python3 tools/make_panel_photo.py
```

# Grapevines story page: Creeping Agency strip photographs

`media/vineyards/` holds the web copies for `a-city-of-vineyards/index.html`; the batch
pipeline and its full file list live in `tools/vineyards/` (`plan.json` + `build.py` +
`encode.swift`, run as `swiftc -O tools/vineyards/encode.swift -o /tmp/encode && python3
tools/vineyards/build.py /tmp/encode`) and in `media/vineyards/manifest.json`.

- `vineyards-5-facade-vine-06.jpg` / `-06-1200.jpg` and `vineyards-5-facade-vine-07.jpg` /
  `-07-1200.jpg` — two added frames at the end of chapter 5's "Creeping Agency of
  Grapevines" filmstrip, cropped from `media/vineyards/2.jpeg` and `3.jpeg`. Those two
  source photos are kept on disk only and never committed (see `.gitignore`) — unlike the
  rest of this chapter's originals, they live directly in `media/vineyards/` rather than
  the gitignored per-chapter originals folder, because that is where they were supplied.
  sRGB (colour-managed from the source's Display P3 profile, not just stripped), all
  EXIF/GPS metadata removed, long edge 2400px/1200px, never upscaled.
  **Captions for these two frames are still empty** — no credit, place or date was
  supplied; search the page for "caption to be added" before publishing.

Regenerate with (`swiftc` toolchain working):

```
swiftc -O tools/vineyards/encode.swift -o /tmp/encode
python3 tools/vineyards/build.py /tmp/encode
```

If `swiftc` fails to build on this machine (SDK/toolchain mismatch), use the Pillow
fallback instead, which produces byte-identical output to the spec above:

```
python3 tools/make_vineyards_photo.py media/vineyards/2.jpeg media/vineyards vineyards-5-facade-vine-06
python3 tools/make_vineyards_photo.py media/vineyards/3.jpeg media/vineyards vineyards-5-facade-vine-07
```

# Grapevines story page: Labyrinths of Unintended Resistance (ch8) figures

- `vineyards-8-garages-vine-03.jpg` / `-03-1200.jpg` and `vineyards-8-garages-vine-04.jpg` /
  `-04-1200.jpg` — two added figures appended to chapter 8's "Labyrinths of Unintended
  Resistance" `.pair` layout, cropped from `media/vineyards/4.jpeg` and `5.jpg` (note the
  different extensions). Those two source photos are kept on disk only and never committed
  (see `.gitignore`), same arrangement as `2.jpeg`/`3.jpeg` above. sRGB (colour-managed from
  the source's Display P3 profile), all EXIF/GPS metadata removed, long edge 2400px/1200px,
  never upscaled.
  **Captions for these two figures are still empty** — no credit, place or date was
  supplied; search the page for "caption to be added" before publishing.
- The chapter's second original figure (`vineyards-8-garages-vine-02`, credited to Irakli
  Kochlashvili) was enlarged to the same displayed width as the first figure
  (`vineyards-8-garages-vine-01`) by giving it the `big` modifier class (see `.pair .big` in
  the page CSS), which places it in the grid's first, wider column on its own row, and
  widening its `sizes` attribute to match. No new image variant was needed: the existing
  2400px-wide file already covers the larger rendered width at 2x pixel density.

Regenerate the same way as the Creeping Agency frames above, substituting the source file
and output name:

```
python3 tools/make_vineyards_photo.py media/vineyards/4.jpeg media/vineyards vineyards-8-garages-vine-03
python3 tools/make_vineyards_photo.py media/vineyards/5.jpg media/vineyards vineyards-8-garages-vine-04
```

# Dogs story page: closing photograph (stZoomFigure)

- `dogs-last-photo-{1200,2400,3200}.jpg` / `.webp` — the Dogs page's closing photograph (a
  scroll-driven zoom-in/zoom-out, `stZoomFigure` in `index.html`), built from
  `media/dogs/Lastdog.JPG`. That source photo is kept on disk only and never committed (see
  `.gitignore`). sRGB (colour-managed from the source's own profile), EXIF orientation
  applied then all metadata stripped, width-resized (1200/2400/3200px, never upscaled beyond
  the original's 3360px), JPEG quality 72 alongside a WebP sibling at each width, loaded via
  a dedicated `<picture>` built by `stZoomImg()` (the rest of the Dogs page's photos keep
  using the simpler thumb+src `stImg()` srcset, left untouched).
- This replaces the former "cartoon-to-photo" closing element (`stCartoonFigure`, its
  `.st-cartoon` CSS and its 10 generated `dogs-final-cartoon-*` layer files, all removed).
  `tools/make_cartoon.py`, the script that generated those layers, is no longer used by
  anything but is kept in `tools/` in case it's wanted again. `media/dogs/24.jpg` and
  `media/dogs/thumb/24.jpg` (the plain photograph the cartoon used to resolve into) are
  originals, not generated files, and are likewise kept in place though now unused.

Regenerate with:

```
python3 tools/make_lastdog_photo.py media/dogs/Lastdog.JPG media/dogs dogs-last-photo
```
