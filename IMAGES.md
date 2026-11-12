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
- `panel-dogs-street-dog-01-{480,800,1200}.{webp,jpg}` — the Dogs panel's photograph,
  cropped (full width, trimmed from the top only so the dog's feet stay at the frame's
  edge) from `media/dogs/12.jpg` (kept in the repo; not a hidden/original-only source).
  Colour-managed from the source's embedded Display P3 profile to sRGB, all EXIF/GPS
  metadata stripped, each size under budget (480 ≈ 14 KB, 800 ≈ 37 KB, 1200 ≈ 80 KB).

Regenerate with:

```
python3 tools/make_panel_photo.py                 # all jobs
python3 tools/make_panel_photo.py --only panel-dogs-street-dog-01   # just this one
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

# Grapevines story page: chapter 11 still photograph, resized

- `vineyards-11-leaf-collage-01-1400.jpg` — added so the chapter 11 photograph (the pressed
  vine leaf and leaf collage above the "While some of the vine's cuttings..." paragraph) is
  sharp at its new, much smaller rendered width (matching the "Grapevines as Trees of Life"
  photographs' own width, up to 680px, instead of filling the whole page column at up to
  1152px). Built from the already-committed `vineyards-11-leaf-collage-01.jpg` (2400x1800,
  the best available source — no separate uncommitted original exists for this one), sRGB,
  all metadata stripped, long edge 1400px (covers 680px at 2x pixel density), JPEG quality
  72, never upscaled. The existing `-1200.jpg` and un-suffixed 2400px files are unchanged
  and still in the `srcset`.

Regenerate with:

```
python3 -c "
import io
from PIL import Image, ImageCms, ImageOps
SRGB = ImageCms.createProfile('sRGB')
im = Image.open('media/vineyards/vineyards-11-leaf-collage-01.jpg')
im.load(); im = ImageOps.exif_transpose(im)
icc = im.info.get('icc_profile')
im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), SRGB, outputMode='RGB') if icc else im.convert('RGB')
w, h = im.size
im = im.resize((1400, round(h * 1400 / w)), Image.LANCZOS)
im.save('media/vineyards/vineyards-11-leaf-collage-01-1400.jpg', 'JPEG', quality=72, optimize=True, progressive=True)
"
```

# Dogs story page: two added frames at the end of the first (street) gallery

- `dogs-gallery-1-111.jpg` / `-111-1200.jpg` and `dogs-gallery-1-222.jpg` / `-222-1200.jpg`
  — two new frames appended to the end of the Dogs page's first gallery (`streetCarousel`,
  the filmstrip right after the intro text, shared/filmstrip-carousel.js). Built from
  `media/dogs/111..jpg` (note the literal double dot in that filename) and
  `media/dogs/222.jpg`. Both source photos are kept on disk only and never committed (see
  `.gitignore`). sRGB, all metadata stripped, full size capped at the source's own
  resolution (2048px long edge, never upscaled) plus a 1200px-long-edge sibling — the same
  two-tier convention (no 480/800 tier, no WebP) the gallery's other six frames already use;
  `shared/filmstrip-carousel.js` only ever requests those same two URLs per photo, so adding
  a third size or a WebP source would need a change to that shared component, which this
  task didn't call for.
- No manifest.json exists for `media/dogs/` (only `media/vineyards/` has one); this section
  of IMAGES.md is the only record of these two files, same as the closing photograph above.

Regenerate with:

```
python3 tools/make_dogs_gallery_photo.py "media/dogs/111..jpg" media/dogs dogs-gallery-1-111
python3 tools/make_dogs_gallery_photo.py media/dogs/222.jpg media/dogs dogs-gallery-1-222
```

# Dogs story page: "Dog Gardens" section, two added photographs, one removed

- `dogs-garden-333.jpg` and `dogs-garden-444.jpg` (plus `thumb/dogs-garden-333.jpg` and
  `thumb/dogs-garden-444.jpg`) — two new photographs appended to the end of the "Dog
  Gardens" section (`storyOfPuppies` in `index.html`), in the section's own plain src+thumb
  convention (1600px long edge / 600px long edge, no WebP, matching sibling entries like
  `17.jpg`/`thumb/17.jpg`). Built from `media/dogs/333.jpeg` and `media/dogs/444.jpeg`. Both
  source photos are kept on disk only and never committed (see `.gitignore`). sRGB, all
  metadata stripped, never upscaled.
- `16.jpg` was removed from this section (replaced by the two new photographs). Its
  generated thumbnail, `media/dogs/thumb/16.jpg`, has been deleted (it was used nowhere
  else on the page). The original, `media/dogs/16.jpg`, is untouched and still in the repo,
  just no longer referenced from any page.
- No manifest.json exists for `media/dogs/` (only `media/vineyards/` has one); this section
  of IMAGES.md is the only record of these files, same as the other Dogs-page additions
  above.

Regenerate with:

```
python3 tools/make_dogs_photo.py media/dogs/333.jpeg media/dogs dogs-garden-333
python3 tools/make_dogs_photo.py media/dogs/444.jpeg media/dogs dogs-garden-444
```

# Dogs story page: "notAllowed" section, one added photograph

- `dogs-entrance-notices.jpg` (plus `thumb/dogs-entrance-notices.jpg`) — one new photograph
  added to the end of the section whose heading begins "Bonds of care and affection for
  dogs..." (`notAllowed` in `index.html`), in the section's own plain src+thumb convention
  (1600px long edge / 600px long edge, no WebP, matching sibling entries `5.jpg`/`13.jpg`).
  Built from `media/dogs/666.jpg`, kept on disk only and never committed (see `.gitignore`).
  sRGB, EXIF orientation applied (the source was stored landscape with a rotate-to-portrait
  EXIF tag), all metadata stripped — notably including embedded GPS coordinates the source
  carried — never upscaled.
- No manifest.json exists for `media/dogs/`; this section of IMAGES.md is the only record of
  this file, same as the other Dogs-page additions above.

Regenerate with:

```
python3 tools/make_dogs_photo.py media/dogs/666.jpg media/dogs dogs-entrance-notices
```

# Dogs story page: "Homes" section, one added photograph, two removed, new layout

- `dogs-home-doghouse-lot.jpg` (plus `thumb/dogs-home-doghouse-lot.jpg`) — one new photograph
  appended to the end of the "Homes" section (`homes` in `index.html`), in the section's own
  plain src+thumb convention (1600px long edge / 600px long edge, no WebP, matching sibling
  entries like `3.jpg`/`19.jpg`). Built from `media/dogs/555.jpeg`, kept on disk only and
  never committed (see `.gitignore`). sRGB, all metadata stripped, never upscaled.
- `8.jpg` and `9.jpg` were removed from this section. Their generated thumbnails,
  `media/dogs/thumb/8.jpg` and `media/dogs/thumb/9.jpg`, have been deleted (used nowhere
  else on the page). The originals, `media/dogs/8.jpg` and `media/dogs/9.jpg`, are untouched
  and still in the repo, just no longer referenced from any page.
- The "Homes" gallery's layout was also replaced: the decorative "building drawing" system
  (`INK`, `stRuler`, `stInk`, `stInkBleed` and all `.ink*` CSS — small line fragments cloned
  from the Building page's elevation drawing, used as section dividers, a left-margin section
  ruler, and a hover/scroll "develop" effect specifically over the Homes photographs) has been
  removed from the Dogs page entirely, per request. In its place, "Homes" now uses its own
  `.st-homes` grid — a 4-role cycle of column spans (7/5/5/7, alternating which side is wider
  each row, with a small vertical stagger) instead of the generic `.st-gallery` pattern the
  other sections use.
- No manifest.json exists for `media/dogs/`; this section of IMAGES.md is the only record of
  this file, same as the other Dogs-page additions above.

Regenerate with:

```
python3 tools/make_dogs_photo.py media/dogs/555.jpeg media/dogs dogs-home-doghouse-lot
```
