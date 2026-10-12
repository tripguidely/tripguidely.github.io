# Paris family hotel map — local review

UX/CRO base: `c711082c9b0fbb9f145f50f60a6d6a061454a184` (origin/main, PR #32 merged).
Review date: 2026-10-11, America/Toronto.
Branch: `polish/paris-family-hotels-ux-cro` in an isolated temporary worktree.
The owner approved these seven prepared files for commit, push and a PR against
main after final verification. Wait for GitHub Actions and stop for human
validation. No merge or publication is authorized. Earlier results below are
historical.

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
- https://www.pullmanparismontparnasse.com/fr/chambres-suites/chambres-deluxe-famille-amis/
- https://www.hotelregenceetoile.com/en/
- https://www.hotel-bb.com/en/hotel/paris-17-batignolles
- https://data.geopf.fr/geocodage/search?q=24+avenue+Carnot+75017+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=4+rue+des+Innocents+75001+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=4+boulevard+Berthier+75017+Paris&limit=1

## Loading, accessibility and booking

Only this page loads the small bootstrap and scoped stylesheet. The map region,
hotel selector and first card are open automatically. Leaflet JS/CSS and OSM
tiles load when the section approaches within 250px of the viewport, using
IntersectionObserver with a scroll/resize fallback for older browsers.
Four fixed positions: no runtime geocoder, location permission, routing API,
API key, provider account or billing. There is no activation button.

Numbered 44px keyboard-focusable pins select a semantic HTML hotel card outside
Leaflet's event container. A four-button selector provides the same operation
without tiles. Enter/Space select; the region remains open.
The map does not capture wheel scrolling; touch users retain one-finger page
scrolling. Reduced-motion preferences disable map animations.

Card facts and booking anchor are cloned from the corresponding existing hotel
article, avoiding a second affiliate URL/SubID registry. Only the clone's
placement and experiment metadata become `map` / `with_map`. The original list
remains `list` / `baseline`, with byte-identical opening tags. Existing shared
consent-gated affiliate_click handles the card through normal event bubbling;
no second click listener or tracking event is added. `with_map` identifies the
map CTA; this implementation does not assign a randomized A/B cohort.

Native `details`/`summary` now exposes the full description and trade-off inside
the map's hotel card, without a jump to the original list. The hotel name,
neighborhood, trip fit and complete facts are already shown above. Enter/Space
toggles the details; the hotel-specific accessible name identifies the control.
The Klook action precedes the details so expanding long text does not move it
below that text. Leaflet loading preserves the open panel and focused control.
The repeated "Affiliate link" note is removed; the visible disclosure preceding
the map is unchanged. Original list booking buttons remain unchanged.

Tiles failing or timing out display a status message while markers, selectors,
hotel facts and native affiliate links remain functional. Library loading
failure retains the selector/cards. Without JavaScript,
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
The UI informs users of the third-party tile connection before the deferred load.

## Previous three corrections (merged as PR #32)

The four original hotel cards, facts, native Klook anchors, URLs, SubIDs, target,
rel and accessible names are preserved. The four public official-source anchors
become plain source text; the exact URLs and category evidence remain in this
internal document and the original hotel research documents. Visible new-tab
notes are removed from the list and map, while each booking link's aria-label
continues to announce the new tab. No metadata, JSON-LD, heading, itinerary,
shared tracking, consent, coordinates, Leaflet license or attribution is changed.

## Validation

Run the inherited 57 auditor self-tests and full audit against the pinned base.
The correction needs one exact-hash authorization for the existing map script.
No existing exceptions, contracts, shared scripts, original affiliate opening
tags, prior authorizations or other pages are to be changed.

The existing affiliate test still checks all original page content/SEO after
normalizing only the map section/resource tags, the four approved source-anchor
removals and the four removed visible new-tab notes. Map
integration tests cover lazy loading, numbered pins, desktop/mobile, native
booking markup, consent and event counts, tile/library failure, keyboard use,
automatic viewport loading (including without IntersectionObserver), no-JS
fallback and scoped loading. All partner and GA requests are
blocked during QA; live partner attribution and live GA4 delivery are not proven.

Browser artifacts are outside the worktree in the temporary map QA directory.
Real OSM tiles are viewed only for the requested desktop/mobile screenshots;
repeat regression tests use intercepted tile responses rather than OSM traffic.

### Initial map implementation results (before these corrections)

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
The initial implementation was subsequently merged as PR #31. These current
corrections were initially prepared locally for human validation; the owner
subsequently approved a commit, push and PR, with no merge or deployment.

### Previous default-open correction results

- 179 map assertions passed, including automatic open, zero library/tile
  requests before approach, loading within the 250px margin, legacy-browser
  fallback without IntersectionObserver, four pins/cards, mobile/keyboard,
  new-tab accessible names, no visible new-tab notes, and network/no-JS fallbacks.
- 43 affiliate assertions passed; URLs, SubIDs, target, rel, event payloads,
  consent gating and single-event counts remain unchanged.
- Auditor self-tests: 57/57 passed. Full SEO/site audit: PASS, zero regressions;
  all 965 historical findings unchanged. One exact-hash map-script authorization
  was added; previous records and every exception remain unchanged.
- Exact HTML comparison allows only the four official anchor-to-text changes,
  removal of the four visible list notes and removal of the activation button.
  Original metadata, all other article copy and affiliate opening tags match base.
- Shared site.js, the four positions, vendor assets, license, attribution,
  CSS and Disney files/HEAD are unchanged. Nothing was staged or committed at
  completion of the initial correction review.

QA records: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-family-default-qa`.
That phase was subsequently merged as PR #32. Its former publishing approval
does not apply to the current local UX/CRO work.

## Current UX/CRO changes and retained evidence

The four identical source/condition paragraphs are replaced by one shared
category-condition reminder immediately before the original four cards. The
facts and qualifications remain verbatim; their order now places the definition
list before the longer description. Capacity/category labels, neighborhood
badges and distinct trade-off blocks make the existing information easier to
scan on mobile. All four original articles, headings, IDs and booking anchors
remain. No new official-site link is added to the public page.

Category provenance is retained in `docs/paris-hotel-subguides.md` (evidence
reviewed 2026-10-09) and the exact official URLs in this document:

| Property | Retained category evidence and qualification | Source |
| --- | --- | --- |
| Citadines Les Halles Paris | Studios for two, triple apartment, apartments for four; kitchens and bedding depend on category. Verify the exact category and occupancy through the booking channel. | Official Ascott property page above. |
| Pullman Paris Montparnasse | Deluxe Family maximum four with two double beds; connecting arrangements require confirmation. | Official Deluxe Family page above. |
| Hôtel Régence Étoile | Prestige Family maximum three with child-under-12 extra-bed condition; separate connecting category for two adults/two children. Confirm the booked arrangement. | Official hotel page above. |
| B&B HOTEL Paris 17 Batignolles | Family/adjoining descriptions and cot requests; exact occupancy is left for confirmation, not a universal four-person claim. | Official B&B property page above. |

Address and coordinate evidence remains in the first table. Editorial trip fit
and trade-offs are retained in full, not presented as a completed-stay review.
Published formats do not establish current partner availability.

The one new auditor authorization is restricted to the before/after SHA-256 of
the existing page-only map script against this phase's exact base. The initial
audit had no other error. No auditor code, SEO exception, contract, old
authorization, shared script or other public page is changed.

### Current validation

- Map browser QA: 281 assertions passed at 320/390/768/1440px and doubled root
  text, including native details Enter/Space, full text parity, CTA visibility,
  four pins/selectors, automatic viewport loading, consent, and tile/library/
  no-JS fallbacks. Desktop and mobile screenshots were visually reviewed.
- Affiliate browser QA: 43 assertions passed; four exact URL/SubID pairs,
  original target/rel/accessible names, consent gating, single-event counts and
  original SEO/content after only the specified local transformations.
- Auditor self-tests: 57/57 passed. Full site/SEO audit: PASS, zero errors,
  965 historical findings unchanged. Exactly one hash-bound script approval;
  existing exceptions, contracts and earlier approvals are byte-for-byte intact.
- Exact whole-page comparison permits only the four source-paragraph removals,
  shared condition reminder, four fact-list moves and three category labels.
  Head/Schema, map section/disclosure and original affiliate opening tags match
  the base. Coordinates, shared site.js, vendor files, license and attribution
  are unchanged. Disney HEAD, status and all four recorded file hashes match.
- JS syntax and git diff --check passed. Seven scoped implementation/document/
  test files are modified; HEAD remains at the base and the index is empty.
- Partner and GA requests were intercepted: these checks verify local event
  dispatch, not live GA4 receipt, partner availability or commission attribution.
- Physical devices and assistive technology are not directly tested; mobile
  checks use Chrome viewport/touch emulation and native keyboard controls.

Current artifacts: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-family-ux-cro-qa`.
Screenshots: `desktop-hotel-map.png`, `desktop-hotel-cards.png`,
`mobile-hotel-map.png`, `mobile-hotel-cards.png`.
Reports: `map-browser-report.json`, `preservation-report.json`, `self-tests.json`,
`site-audit-initial.json`, `site-audit.json`.
Initial local verdict: GO; no commit, push, PR, merge or publication at that
review. The owner subsequently approved commit, push and a PR, with CI review
and no merge or publication.
