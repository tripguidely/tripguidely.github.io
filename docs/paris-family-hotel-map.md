# Paris family hotel map — local review

Base: `0357558b6fc6a2268a5eaf4c2e95c4ea0d0a6850` (origin/main, PR #30 merged).
Review date: 2026-10-11, America/Toronto. Owner-approved for commit, push and a
pull request against main after final review. Merging remains outside authorization.

## Coordinate evidence

Coordinates are published hotel/location points, not a survey of an accessible
entrance. No directions or accessible-route claim is made. Longitude/latitude
from IGN GeoJSON is reordered to Leaflet's latitude/longitude.

| Property | Latitude | Longitude | Evidence checked |
| --- | --- | --- | --- |
| Citadines Les Halles Paris | 48.86049 | 2.34748 | Official Ascott property's JSON-LD `geo` and `data-google-latitude/longitude`; address 4 rue des Innocents. IGN exact-address point 48.860608, 2.34712 corroborates the same location (about 30 m away). |
| Pullman Paris Montparnasse | 48.8385501 | 2.3203257 | Official property FAQ explicitly publishes these GPS coordinates for 19 rue du Commandant René Mouchotte. |
| Hôtel Régence Étoile | 48.876564 | 2.292922 | Official hotel confirms 24 avenue Carnot, 75017. IGN/BAN exact-address match, score 0.97415. The hotel's embedded-map viewport center is offset and is deliberately not used as its position. |
| B&B HOTEL Paris 17 Batignolles | 48.894501 | 2.312604 | Official property JSON-LD `geo` and map location fields; 4 boulevard Berthier. IGN exact-address point 48.894363, 2.312478 corroborates the location (about 18 m away). |

Sources:
- https://www.discoverasr.com/en/citadines/france/citadines-les-halles-paris
- https://www.pullmanparismontparnasse.com/faq/
- https://www.hotelregenceetoile.com/en/
- https://www.hotel-bb.com/en/hotel/paris-17-batignolles
- https://data.geopf.fr/geocodage/search?q=24+avenue+Carnot+75017+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=4+rue+des+Innocents+75001+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=4+boulevard+Berthier+75017+Paris&limit=1

## Loading, accessibility and booking

Only this page loads the small bootstrap and scoped stylesheet. Leaflet JS/CSS
and OSM tiles load only after the native Show hotel map button is activated.
Four fixed positions: no runtime geocoder, location permission, routing API,
API key, provider account or billing. Hide/reopen reuses the same map.

Numbered 44px keyboard-focusable pins select a semantic HTML hotel card outside
Leaflet's event container. A four-button selector provides the same operation
without tiles. Enter/Space select; Escape hides the map and restores focus.
The map does not capture wheel scrolling; touch users retain one-finger page
scrolling. Reduced-motion preferences disable map animations.

Card facts and booking anchor are cloned from the corresponding existing hotel
article, avoiding a second affiliate URL/SubID registry. Only the clone's
placement and experiment metadata become `map` / `with_map`. The original list
remains `list` / `baseline`, with byte-identical opening tags. Existing shared
consent-gated affiliate_click handles the card through normal event bubbling;
no second click listener or tracking event is added. `with_map` identifies the
map CTA; this implementation does not assign a randomized A/B cohort.

Tiles failing or timing out display a status message while markers, selectors,
hotel facts and native affiliate links remain functional. Library loading
failure retains the selector/cards and offers a retry. Without JavaScript,
the original hotel list and its booking links remain available.

## Leaflet and OpenStreetMap

Leaflet 1.9.4 is vendored, unmodified, from the archive linked by its official
download page:
https://github.com/Leaflet/Leaflet/releases/download/v1.9.4/leaflet.zip

BSD-2-Clause license is retained at assets/vendor/leaflet-1.9.4/LICENSE.
Leaflet JS SHA-256: 85d455b4522415f6badc42a0e7d17c919d100347d6b8958bd0dc738fdecd6d50.

https://operations.osmfoundation.org/policies/tiles/

The standard HTTPS tile endpoint is configured on the section, with visible
linked OpenStreetMap contributor attribution. Browser caching is not bypassed;
the existing strict-origin-when-cross-origin policy supplies a valid Referer.
No prefetch/offline download, caching proxy or tile archive is implemented.
Normal viewport requests only, no retina multiplication, no offscreen tile
buffer, bounded zoom. OSM has no guaranteed quota or SLA and can restrict use;
disable the component or change provider configuration if traffic warrants it.
The UI informs users of the third-party tile connection before activation.

## Validation

Run the inherited 57 auditor self-tests and full audit against the pinned base.
New integration authorizations must be exact-hash, limited to the page bootstrap
script tag and the two new JS files. No existing exceptions, contracts, shared
scripts, original affiliate opening tags or other pages are to be changed.

The existing affiliate test still checks all original page content/SEO after
removing only the additive map section and its two resource tags. New map
integration tests cover lazy loading, numbered pins, desktop/mobile, native
booking markup, consent and event counts, tile/library failure, keyboard use,
hide/reopen, no-JS fallback and scoped loading. All partner and GA requests are
blocked during QA; live partner attribution and live GA4 delivery are not proven.

Browser artifacts are outside the worktree in the temporary map QA directory.
Real OSM tiles are viewed only for the requested desktop/mobile screenshots;
repeat regression tests use intercepted tile responses rather than OSM traffic.

### Results

- Map browser QA: 131 assertions passed, including keyboard Enter/Space,
  Escape/focus return, 320/390/768/1440px and doubled root text, all four map
  CTAs, consent absent/denied/granted/revoked, no event on opening the map,
  hide/reopen without a second library load, tile failure and library failure.
- Inherited affiliate QA: 43 assertions passed; original HTML/SEO preserved
  after removing only the additive map section and its two resource tags.
- Auditor self-tests: 57/57 passed. Full site audit: PASS, zero regressions,
  965 existing findings unchanged, three exact-hash new integration approvals.
  All original exceptions, contracts and previous approvals remain unchanged.
- Shared site.js and four original list affiliate opening tags unchanged.
  Disney HEAD/status and four file hashes unchanged; existing worktree HEADs
  unchanged. At completion of the initial local review, the new map worktree
  was still at the base commit, with nothing staged.
- JS syntax and git diff --check passed. Browser screenshots visually reviewed:
  desktop-hotel-map.png, mobile-hotel-map.png and mobile-tile-fallback.png.
- Bootstrap JS/CSS gzip sizes: 2,977 / 1,109 bytes. Leaflet JS/CSS gzip sizes:
  42,444 / 3,522 bytes, fetched only on activation. These are asset sizes, not
  measured field Core Web Vitals; a browser simulation is not a physical-device
  or assistive-technology review.

QA reports and screenshots:
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-family-map-qa`.
Local verdict: GO. Final source review reconfirmed the four positions, all eight
vendored distribution files against the official archive, the unchanged BSD
license, all four original affiliate anchors and visible linked OSM attribution.
The owner subsequently authorized commit, push and a PR. No merge or deployment
is authorized; stop for human validation after GitHub Actions.
