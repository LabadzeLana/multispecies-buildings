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
