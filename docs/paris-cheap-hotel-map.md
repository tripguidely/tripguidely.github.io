# Paris cheap hotels — local UX/CRO review

Base: `421e6652744e6793347103a09e9ccbb879abfd01` (latest origin/main, PR #33 merged).
Branch: `feat/paris-cheap-hotels-ux-cro`.
Worktree: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-cheap-hotels-ux-cro`.
Review: 2026-10-11, America/Toronto.
Initial preparation was local only, with no staging, commit, push or PR.
The owner subsequently approved these seven prepared files for commit, push and
a PR against main after final verification. Wait for GitHub Actions, then stop
for human validation. No merge, purchase or publication is authorized.

## Hotel, address and point audit

The existing shortlist contains two hotels and one hostel, not three interchangeable
hotel rooms. Property points are taken from official sources and corroborated
against IGN/BAN addresses. They are not surveyed entrance or accessible-route points.

| Existing property | Address | Leaflet latitude, longitude | Evidence |
| --- | --- | --- | --- |
| ibis Paris Tour Eiffel Cambronne 15ème | 2 rue Cambronne, 75015 Paris | `48.847653, 2.301453` | Accor 1400 publishes these GPS coordinates. IGN exact address `48.847411, 2.301335`, score 0.981449, about 28 m away. |
| B&B HOTEL Paris 17 Batignolles | 4 boulevard Berthier, 75017 Paris | `48.894501, 2.312604` | Official hotel JSON-LD `geo` and location fields agree. IGN exact address `48.894363, 2.312478`, score 0.981752, about 18 m away. |
| Generator Paris | 9–11 place du Colonel Fabien, 75010 Paris | `48.8781526, 2.3698083` | Official page's `data-google-map-lat` / `data-google-map-long`. IGN 9 and 11 address points `48.878115, 2.369571` / `48.878293, 2.369624` corroborate the same property. |

Sources inspected:

- https://all.accor.com/hotel/1400/index.en.shtml
- https://www.hotel-bb.com/en/hotel/paris-17-batignolles
- https://staygenerator.com/hostels/paris
- https://data.geopf.fr/geocodage/search?q=2+rue+Cambronne+75015+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=4+boulevard+Berthier+75017+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=9+place+du+Colonel+Fabien+75010+Paris&limit=1
- https://data.geopf.fr/geocodage/search?q=11+place+du+Colonel+Fabien+75010+Paris&limit=1

## Rooms, transport and costs

- ibis: official single category permits one guest with one single bed; standard
  double and twin categories permit two with one double or two single beds.
  Other categories exist, including a category-specific child sofa rule, but are
  not generalized to the standard rooms. Cambronne is on metro line 6.
- B&B: published double/twin categories allow up to two adults, with one double
  or two singles. Family/adjoining arrangements exist, but no general family
  occupancy is invented. Breakfast and parking are paid services unless included
  in the booked rate. Porte de Clichy serves metro lines 13 and 14.
- Generator: private double/twin categories sleep one or two, with one double
  or two singles. Dorm categories have 4–10 room beds, sold as beds; this is not
  occupancy purchased by one traveler. Bunks include linen; towels can cost
  extra in dorm/private bunk categories, while some private double/twin rooms
  include towels. Current age/access rules and storage costs remain checks to
  perform for the actual party and booking. No unverified minimum-age claim is
  added. Colonel Fabien is on metro line 2.

Transport corroboration:

- https://www.ratp.fr/decouvrir/patrimoine/histoire-metro-ligne-6
- https://www.ratp.fr/decouvrir/patrimoine/histoire-station-barbes-rochechouart
- https://www.hotel-bb.com/en/hotel/paris-17-batignolles (access section)

No nightly price, tax amount, price ranking, transport duration, current timetable
or availability promise is added. Provider teaser prices are deliberately omitted.
Official information supports category facts, not a completed stay or equivalent
partner inventory. Published categories may not be available through Klook.
All original practical descriptions and trade-offs remain intact. Original
total-cost, cancellation, tax, route-planning and hostel cautions remain intact.
Public official-source links in the three commercial cards are removed; their
provenance is preserved here and in `docs/paris-hotel-subguides.md`.

## Exact affiliate inventory

| Property | Existing URL, unchanged | Existing SubID, unchanged | Klook ID |
| --- | --- | --- | --- |
| ibis Cambronne | `https://klook.tpk.ro/jor8wPCP` | `paris_hotel_ibis_cambronne` | `2846` |
| B&B Batignolles | `https://klook.tpk.ro/gX4TDO9u` | `paris_hotel_bb_batignolles` | `412657` |
| Generator Paris | `https://klook.tpk.ro/t3aQhbjX` | `paris_hotel_generator` | `448880` |

HEAD checks on this review date followed two HTTP 302 redirects for each short
URL to the corresponding Klook hotel ID/name. Each final Klook response was
HTTP 403. Identity matches; final room inventory, availability, commission
eligibility and successful server-side SubID attribution are not proven.
No URL is expanded, reparameterized or rewritten in the public page.

The original list anchors retain href, SubID, rel, target, visible label and
hotel-specific accessible name including new-tab behavior. Only the three
opt-in metadata attributes are added: hotel ID, list placement, baseline variant.
Map links clone these original anchors and set map / with_map metadata. The
unmodified shared site.js emits one consent-gated affiliate_click and supplies
page_path. No extra analytics listener, consent mechanism or partner registry
is introduced. with_map identifies the placement, not a randomized A/B cohort.
No repeated "Affiliate link" or visible new-tab note is placed under a button;
the existing disclosure and a clear disclosure near the map remain visible.

## Architecture, accessibility and fallback

Reuse the existing hotel template, design tokens, native anchors, consent/event
handler and unmodified local Leaflet 1.9.4 distribution. Its BSD-2-Clause license
remains in `assets/vendor/leaflet-1.9.4/LICENSE`.
Reference: https://leafletjs.com/download.html

The small bootstrap and stylesheet are page-specific. They follow the audited
Family implementation but do not import or modify Family's page-specific files;
Family and all other pages remain unchanged. The CSS requires tg-cheap-hotels
and the script requires data-map-page=paris-cheap, avoiding accidental cross-page
behavior. No build system, plugin, runtime geocoder, API key or provider account.

The map selector and initial hotel card open automatically. Leaflet JS/CSS and
tiles are deferred until within 250 px of the viewport, with a passive
scroll/resize fallback when IntersectionObserver is absent. Three 44 px numbered
pins and three native buttons select the same semantic card outside Leaflet's
event container. Keyboard selection focuses its heading. Native details/summary
exposes the complete information in place; loading Leaflet preserves the open
panel/focused control.

Capacity and transport remain visible above Klook. Bedding, budget checks,
address, description and trade-off are available in the expandable panel, cloned
from the original HTML. Stable data-fact keys determine the compact summary;
no text parsing or positional category assumption is used. Original cards show
all five fact groups, with capacity first, clear neighborhood badges and distinct
trade-off blocks. The comparison retains native column/row headers, caption,
named keyboard-scrollable region and all five columns on mobile. The pricing
reminder sits outside the horizontally scrolling table so it remains readable.

Tiles/library errors leave selectors, facts, details and Klook links functional.
Without JavaScript, the original three HTML cards and booking links work; an
explicit fallback link and noscript explanation remain. Reduced motion disables
map animations; one-finger page scrolling remains available. No hotel photo is
added, downloaded or generated.

## OpenStreetMap usage

Policy checked: https://operations.osmfoundation.org/policies/tiles/
Use HTTPS standard tiles and visible linked OpenStreetMap contributors attribution.
Browser referrer policy remains strict-origin-when-cross-origin; caching headers
are honored, with no cache bypass, proxy, offline archive or bulk tile requests.
Zoom is bounded; retina multiplication and offscreen tile buffer are disabled.
Endpoint configuration remains in the section's data attribute. No billing,
subscription or API key. OSM has no guaranteed quota/SLA and may block excessive
traffic; the booking fallback is independent of tile availability.

## Validation scope

Run the new Cheap browser and preservation suites, the inherited 57 auditor
self-tests and full SEO/site audit against the exact base. Preserve all SEO
metadata, JSON-LD, existing images, other public HTML and shared scripts/vendor
assets. Verify Disney branch/HEAD/status/file hashes and existing worktrees.

Initial audit: only three owner-review gates, with 965 historical findings and
zero new SEO/link findings. Narrow hash-bound approvals are needed for the new
bootstrap, its script tag and the three anchors' added metadata. Do not change
auditor code, old approvals, exceptions, inventory or protected contracts.

Browser analytics and partner requests are blocked; repeated tests use fake
tiles. Only the desktop/mobile screenshots view real OSM viewport tiles, without
automated panning/zooming or tile collection. Local gtag interception verifies
events/consent but not live GA4 delivery or commission attribution. Chrome mobile
emulation and keyboard checks are not physical-device or screen-reader testing.

QA artifacts: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-cheap-hotels-qa`.

## Observed final results

- Browser suite: 285 assertions passed. Viewports 320/390/768/1440 px, mobile
  touch emulation, doubled root text, native details Enter/Space, CTA visibility,
  complete fact/paragraph parity, three numbered markers/selectors, all three
  original list and map URLs/metadata, consent absent/denied/granted/revoked,
  grant after initialization and no duplicates after shared-script reinit.
- Map assets/tiles make zero requests before viewport approach; IntersectionObserver
  and its passive fallback pass. Tile/library failure retains booking behavior;
  no-JS retains the original cards. Table keyboard scrolling reaches all columns.
- Preservation suite: 57 checks passed. Exact original affiliate opening tags
  after stripping only added opt-in metadata; head/Schema unchanged except the
  scoped stylesheet; other sections, all original practical descriptions and
  trade-offs, Family/shared assets and all eight vendor/license files preserved.
- Auditor self-tests: 57/57 passed. Full SEO/site audit PASS, zero regressions,
  965 historical findings unchanged. Exactly three narrowly scoped review
  records; no auditor, old authorization, contract or exception changes.
- JS syntax and git diff --check passed. Bootstrap JS/CSS: 9,964 / 5,577 bytes
  uncompressed, 3,331 / 1,525 gzip bytes. Leaflet is reused locally and remains
  viewport-deferred. These asset sizes are not measured field Core Web Vitals.
- All six final desktop/mobile captures visually reviewed: hotel-map,
  hotel-cards and comparison for both screen sizes. Mobile hotel-cards capture
  shows the first original card; desktop shows all three. Expanded map details
  show full information, with Klook preceding the expansion control.
- Isolation verified: seven scoped implementation/document/test files changed,
  twenty existing worktrees retained plus this new worktree; Disney branch,
  HEAD, exact status and four recorded SHA-256 file hashes unchanged. Nothing
  staged or committed; the new worktree HEAD still equals the pinned main base.

Reports: `map-browser-report.json`, `preservation-report.json`, `self-tests.json`,
`site-audit-initial.json`, `site-audit.json`, `isolation-report.json`,
`asset-sizes.json` in the external QA directory.

Initial local verdict: GO for human review. The final Klook HTTP 403 / live
inventory and commission limitations remain as recorded above.
Before the approved PR, 283 browser assertions were rechecked without real tile
or partner traffic; 57 preservation checks passed again. The exact seven-file
scope and unchanged Family, Luxury, shared consent and Disney were reconfirmed.
The owner approved commit, push and a PR; wait for CI and stop for human
validation. Do not merge or publish.
