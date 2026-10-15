# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Multispecies Buildings is a single-page, self-contained web project (no framework, no build step, no
package.json) documenting the multispecies afterlife of Soviet mass housing in Tbilisi. It is bilingual
(Georgian `ka` / English `en`) and is developed via "vibe coding" directly in `index.html`.

## Commands

There is no build/lint/test tooling. Development is: edit `index.html` directly, then preview it.

- Serve locally: `python3 -m http.server 8743` from the repo root (matches `.claude/launch.json`), then
  open `http://localhost:8743/index.html`.
- There is no bundler/transpiler — HTML, CSS and JS all live inline in `index.html` and must stay valid
  vanilla browser code (no imports, no build-time templating).
- When using the preview tools, prefer serving `index.html` directly rather than opening it as a `file://`
  URL, since media paths are relative.

## Architecture (`index.html`)

Everything — markup, `<style>`, and the single `<script>` — lives in one file. It's large (~2.8MB) mostly
because several photos are inlined as base64 data URIs. Key structure, in order:

1. **`<style>` (head)** — CSS custom properties in `:root` define the palette/fonts (`--paper`, `--ink`,
   `--oil`, `--vine`, etc.). A `[data-theme="dark"]` override exists but is unused by default — paper/light
   theme is the committed default regardless of OS dark-mode preference.
2. **`#cover`** — the fullscreen intro/landing overlay. It implements a scroll-driven "pull back from a
   doorway photo" effect (see `coverScene()` IIFE near the bottom of the script): scrolling `#cover` maps
   scroll position to a CSS `transform: translate+scale` on the `.cv-b` background layer. `PULLBACK_SRC`
   points to an actual file on disk (`2022-07-06 13.29.46-1.jpg`), not a base64 string — don't rename/move
   that file without updating the constant.
3. **`<header class="bar">` + nav** — top nav buttons use `data-nav` attributes (`building`, `inhabitants`,
   `senses`, `index`, `about`) that map to hash routes.
4. **`<main>` → `#stage` (SVG building elevation) + `#panel` (detail aside)** — the building drawing is a
   hand-authored SVG elevation built procedurally by `buildElevation()` (draws walls, windows, balconies,
   level marks, vine/snow/creature decorations as raw SVG path/rect strings). Clickable "hotspots" (circles
   + labels) are generated from `T.spaces` coordinates and injected into `#hotspots`.
5. **`.seasons` bar** — fixed bottom bar toggling `data-season` on `<html>` (`winter|spring|summer|autumn`),
   which drives CSS-only visual changes (vine opacity/color, snow visibility) via `html[data-season="..."]`
   selectors.
6. **`#view`** — the container for non-building "list" pages (Inhabitants, Senses, Index, About), rendered
   by `openView(kind, arg)`.
7. **`<script>` data model, then logic**, in this order:
   - `IMG` — base64 data-URI photos keyed by name (the huge lines in the file).
   - `PLACES` — place metadata used by the standalone `ARCHIVE` taxonomy tree (a planning/content-inventory
     structure for future archive material — not yet wired into the live UI's routing).
   - `T` — the real content model driving the UI:
     - `T.spaces[]` — one entry per building hotspot (`id`, SVG `x/y` + label offset `lx/ly`, bilingual
       title/subtitle/lede/body text as `ka`/`en` pairs, `inh` (inhabitant ids), `sen` (sense ids), `media[]`
       of `{t: photo|audio|video|archive, src?, ka, en}`).
     - `T.inhabitants`, `T.senses` — dictionaries of cross-cutting tags (dog, grapevine, pigeon, rat, mould,
       cat / sound, smell, texture, damp, light), each with bilingual name + description, used both as
       space tags and as their own browsable list pages.
     - `T.seasonNotes` — bilingual caption text per season.
     - `T.about` — project intro + contributor bios.
   - Helpers: `$`, `el`, `L()` (current `<html lang>`), `tr()`.
   - `visited` — a `Set` persisted to `localStorage` (`msb.visited`) tracking which spaces the user opened;
     drives the "visited" hotspot style and Index-page status column.
   - `buildElevation()` — procedurally generates the SVG elevation markup (structure/shaft/openings/ground/
     life layers) and floor-number labels; called once on load.
   - `paintHotspots(activeId)` — refreshes hotspot label text/visited/active classes (language-aware).
   - `openSpace(id)` — renders the right-hand `#panel` for a given `T.spaces` entry (title, media slots via
     `mediaSlot()`, inhabitant/sense tag buttons, metadata fields, "spaces sharing inhabitants" cross-links).
   - `mediaSlot(m)` — renders one media item; if `m.src` is missing it renders a dashed "pending/not yet
     recorded" placeholder instead of a broken image — this is how not-yet-collected material is represented
     deliberately, not a bug.
   - `openView(kind, arg)` — renders the `#view` pages: `inhabitants`/`senses` (card grid), `one` (single
     inhabitant/sense detail with linked spaces — also where the `a-city-of-vineyards/index.html` sub-page is
     linked in, under the `grapevine` inhabitant), `index` (full space list), `about`.
   - `route()` — hash-based router (`#/`, `#/space/<id>`, `#/inhabitant/<id>`, `#/sense/<id>`,
     `#/inhabitants`, `#/senses`, `#/index`, `#/about`); also toggles `aria-current` on nav buttons.
   - `setLang(l)` / `setSeason(s, quiet)` — language is effectively pinned to `"en"` in `setLang` (Georgian
     content exists throughout via `.ka`/`.en` spans and `ka`/`en` data fields, toggled by CSS
     `html[lang="ka"] .en{display:none}` etc., but the language switcher itself currently forces `en`).
   - `init()` IIFE — restores season from `localStorage` (`msb.season`) and calls `route()`.
2. **Bilingual content convention**: every piece of UI copy exists as a `ka`/`en` pair — either as sibling
   `<span class="ka">`/`<span class="en">` in markup, or as `ka`/`en` (and `bka`/`ben`, `dka`/`den`, etc.)
   keys in the `T` data objects. When adding content, always add both language variants and follow the
   existing suffix convention (`b`=body paragraphs array, `d`=description, `sub`=subtitle).

## Related files

- `a-city-of-vineyards/index.html` — a standalone sibling page (own `<style>`, own assets under
  `images/` and `video/`) for one longer-form story; linked to from the main site only via the `grapevine`
  inhabitant's detail page (`openView`, kind `"one"`).
- `cover-pullback-patch.md` — a scoped patch spec describing exactly the `#cover` pull-back feature (markup/
  CSS/JS) in isolation; useful as a reference for how that feature is supposed to work, but the patch has
  already been applied to `index.html`.
- `index.backup.html`, `index-backup-stage2.html` — snapshots of earlier states of `index.html`, kept as
  manual backups. Don't edit these; treat `index.html` as the only live file.
- `Dogs and Buildings/`, and loose top-level photos/`.WAV` files — media assets referenced by relative path
  from `index.html`'s `IMG`/`media` entries (e.g. `PULLBACK_SRC`, `hero-container` background images,
  `ZOOM0254_LR.WAV`). Renaming or moving these breaks the site unless references are updated too.
