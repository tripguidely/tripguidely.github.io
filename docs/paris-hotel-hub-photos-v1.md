# Paris hotel hub photography

The seven hotel shortlist cards now display photographs with consistent rounded frames and the full original composition. Seven visible new-tab notes beneath the booking buttons are removed; their unchanged accessible link names still announce the new tab.

## Scope and image provenance

- Only `hotels/paris/index.html` changes among existing tracked files. No shared CSS, JavaScript, other page, consent, map data, SEO metadata or routing file changes.
- Four existing assets are reused byte-for-byte: Citadines Les Halles Paris (the square/fountain photo), Pullman Paris Tour Eiffel, ibis Paris Tour Eiffel Cambronne and Hotel Regence Etoile.
- Three owner-supplied TravelAPI JPEGs are reduced proportionally, without crop or upscale, to AVIF quality 55 / speed 6. Original JPEGs and unused WebP variants remain local and unversioned.
- Source URLs, source/selected SHA-256 values and encoder settings are recorded in [the image manifest](qa/paris-hotel-hub-photos-v1-images.json). HTTP 200, image/jpeg and full JPEG integrity were verified during acquisition.

| Hotel ID | Exact image path | Dimensions | Selected bytes | Origin |
|---|---|---|---:|---|
| `hotel-citadines-halles` | `assets/images/hotels/paris/citadines-les-halles-paris-square-fontaine-1200x800.avif` | 1200 x 800 | 175981 | Existing repository asset, unchanged |
| `hotel-pullman-eiffel` | `assets/images/hotels/paris/pullman-paris-tour-eiffel-facade.avif` | 960 x 640 | 94735 | Existing repository asset, unchanged |
| `hotel-ibis-cambronne` | `assets/images/hotels/paris/ibis-paris-tour-eiffel-cambronne-15eme-entree.webp` | 960 x 720 | 155676 | Existing repository asset, unchanged |
| `hotel-regence-etoile` | `assets/images/hotels/paris/hotel-regence-etoile-paris-entree-facade.avif` | 1120 x 746 | 103624 | Existing repository asset, unchanged |
| `hotel-france-gare-lyon` | `assets/images/hotels/paris/hotel-de-france-gare-de-lyon-bastille.avif` | 1200 x 801 | 59639 | Exact owner-supplied URL in manifest |
| `hotel-campanile-bercy` | `assets/images/hotels/paris/campanile-paris-12-bercy-village.avif` | 1200 x 800 | 122424 | Exact owner-supplied URL in manifest |
| `hotel-madrigal` | `assets/images/hotels/paris/hotel-madrigal-paris.avif` | 1200 x 799 | 47519 | Exact owner-supplied URL in manifest |

Total of seven unique images: **759598 bytes**. Three new AVIF files: **229582 bytes**.

| New photo | Source JPEG bytes | WebP comparison bytes | Selected AVIF bytes |
|---|---:|---:|---:|
| `hotel-de-france-gare-de-lyon-bastille` | 495023 | 97814 | 59639 |
| `campanile-paris-12-bercy-village` | 1018008 | 242640 | 122424 |
| `hotel-madrigal-paris` | 416491 | 86582 | 47519 |

AVIF reduces the three original JPEGs by 88.1% in total and the tested WebP variants by 46.2%. Both variants were visually compared. The original ratios are retained within integer-pixel rounding: 1200x801, 1200x800 and 1200x799.

## Preservation and accessibility

- All **97 complete anchor elements**, including **10 Klook links**, their URL/rel/target/aria-label attributes, visible CTA text and **7 SubID** values, are exact relative to base `2549de3c4aae381e4117e3e659639962bc6429a4`.
- All data/tracking attributes and scripts are unchanged. Leaflet retains ten neighborhood controls/pins, six travel profiles and the original consent-sensitive affiliate event behavior.
- Each hotel photograph has a reviewed English ALT, its intrinsic width/height, lazy loading and async decoding. CSS uses `object-fit: contain` in reserved 3:2 frames; no photo caption is added.
- Removing the seven sibling spans leaves each accessible CTA name and `(opens in a new tab)` announcement intact. `target="_blank"` and `rel="nofollow sponsored noopener"` are unchanged.
- Removing the seven photos and the one stylesheet link from current HTML exactly restores the base HTML minus only the seven approved visual note lines.

## Validation

- `python -B tests/test_paris_hotel_hub_photos.py`: PASS, **120** preservation checks.
- `python -B scripts/audit-site.py --base-ref 2549de3 --self-test`: PASS, **57** existing audit self-tests.
- `python -B scripts/audit-site.py --base-ref 2549de3 --json`: PASS, zero new errors. Historical baseline findings are unchanged.
- `python -B tests/test_paris_hotel_hub_photos_browser.py --chrome <installed-chrome> --output .qa-paris-hub/pr-browser --report .qa-paris-hub/pr-browser-report.json`: PASS, **1123** checks across **14 scenarios** at 320/375/390/430/768/1024/1440 px, with and without JavaScript. Seven photos decode, no horizontal overflow, seven CTA names announce new tabs, and no visible note remains.
- Existing `tests/test_paris_neighborhood_map.cjs`, invoked by the local QA wrapper: PASS, **1055** checks covering neighborhoods, profiles, keyboard, reduced motion, fallbacks, affiliate events and consent. Wrapper changes only AVIF MIME and permits ignored local output; the existing test file is unchanged.
- `git diff --check` and staged diff whitespace review: PASS.
- Visual inspection: final desktop/mobile screenshots and the owner-approved photographic layout. Separate blocked-image tests at 390/1440 px previously measured zero movement of photo frames and titles.

## Re-running the new checks

The preservation test uses only Python standard-library modules and the approved Git base. It supports committed or staged checkouts. The browser test retrieves baseline HTML from Git rather than a temporary snapshot. Install Playwright and its Chromium runtime in a development environment, then run:

```sh
python -B tests/test_paris_hotel_hub_photos.py
python -B tests/test_paris_hotel_hub_photos_browser.py
```

Pass `--chrome /path/to/chrome` to use an installed Chromium-compatible browser. The test creates `.qa-paris-hub/.gitignore` when needed and writes runtime output into that ignored directory. No dependency package, original JPEG, screenshot or temporary runner is part of this change.

## Screenshots and limitations

Large screenshots remain local, outside the commit. Before the note removal (already with photographs): `.qa-paris-hub/browser/hotels-1440-js.png` and `hotels-390-js.png`. Final state: `.qa-paris-hub/pr-browser/hotels-1440-js.png` and `hotels-390-js.png`. Corresponding no-JavaScript screenshots and all seven widths are available locally. They are not attached to the public PR.

The owner approved the seven photographs visually. The Hotel de France sign corroborates its identity; Campanile branding is visible. Exact property identification for the Campanile facade and Madrigal room relies on the owner-selected sources rather than independent visual proof. No rights audit beyond owner-provided provenance is claimed.

Chrome headless uses local route fulfillment, blocked third-party scripts and mocked OSM tiles. Twelve initial-load samples requested no hotel photos before scroll; captured LCP entries remain the existing hero. These measurements do not establish production Core Web Vitals. Safari, Firefox, real devices, live tiles and real network performance remain outside this validation.

## Commit contents

- `hotels/paris/index.html`
- `assets/css/pages/paris-hotel-hub-photos.css`
- `assets/images/hotels/paris/hotel-de-france-gare-de-lyon-bastille.avif`
- `assets/images/hotels/paris/campanile-paris-12-bercy-village.avif`
- `assets/images/hotels/paris/hotel-madrigal-paris.avif`
- `docs/qa/paris-hotel-hub-photos-v1-images.json`
- `tests/test_paris_hotel_hub_photos.py`
- `tests/test_paris_hotel_hub_photos_browser.py`
- `docs/paris-hotel-hub-photos-v1.md`
