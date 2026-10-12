# Paris neighborhood map — internal audit and human review

Branch: feat/paris-where-to-stay-map.
Worktree: C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map.
Base: 06922e955141eecf391f99356f38ea4baa4b40bc (main after PR #36 and PR #37; local base advanced with --keep, without creating a commit or merge).
Research: 2026-10-12. The owner authorized commit, push and a PR toward main on 2026-10-12 after final checks. Wait for GitHub Actions, then stop for human validation. No merge or worktree deletion authorized.

## Existing guide and choice of geometry
The parent guide contains ten area cards, four decision journeys, seven hotel cards and ten original Klook anchors. Existing area facts and useful internal routes remain the source of the map panels.
Tourist areas such as South Pigalle and Le Marais are not interchangeable with administrative boundaries. Use ten reference pins and explicitly label them as orientation points rather than hotel positions, complete area extents or precise centers. No unverified polygons.
IGN/BAN provides address/street reference points. These are not surveyed entrances. GeoJSON longitude/latitude is converted to Leaflet latitude/longitude without rounding beyond the source values.
Combined Bastille / Oberkampf uses a Bastille reference; Opéra / 9th uses an Opéra reference. The visible note makes this choice explicit.
The numbered list remains available without JavaScript and routes to complete original area cards.

## Verified references
| Number / existing zone | Reference | Latitude | Longitude | IGN type / score | Coordinate source | Area context source |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Le Marais | Square du Temple / Paris Centre town hall | 48.863992 | 2.361532 | housenumber / 0.959420 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=2+Rue+Eugene+Spuller+75003+Paris&limit=1) | [City of Paris square](https://www.paris.fr/lieux/square-du-temple-elie-wiesel-2425), [Tourism office](https://parisjetaime.com/culture/square-du-temple-elie-wiesel-p1027) |
| 2. Saint-Germain-des-Prés | Place Saint-Germain-des-Prés | 48.854148 | 2.333399 | street / 0.961760 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+Saint+Germain+des+Pres+75006+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/article/saint-germain-des-pres-l-indemodable-a587) |
| 3. Latin Quarter | Place de la Sorbonne | 48.848614 | 2.342377 | street / 0.964198 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+de+la+Sorbonne+75005+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/article/le-quartier-latin-et-saint-germain-crevent-l-ecran-a479) |
| 4. 1st Arrondissement | Place Colette | 48.863356 | 2.336069 | street / 0.950992 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+Colette+75001+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/article/balade-du-palais-royal-a-la-place-vendome-a789) |
| 5. 7th Arrondissement | Place Joffre | 48.85288 | 2.303337 | street / 0.967145 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+Joffre+75007+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/article/visites-autour-de-la-tour-eiffel-paris-a895) |
| 6. Montmartre | Place du Tertre | 48.886518 | 2.340671 | street / 0.972057 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+du+Tertre+75018+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/transport/place-du-tertre-p1989) |
| 7. Bastille / Oberkampf | Place de la Bastille | 48.853711 | 2.370213 | street / 0.965214 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+de+la+Bastille+75011+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/eng/article/explore-paris-s-11th-arrondissement-a829) |
| 8. South Pigalle | Place Gustave Toudouze | 48.879563 | 2.337431 | street / 0.960196 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+Gustave+Toudouze+75009+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/eng/article/south-pigalle-naughty-but-nice-a582) |
| 9. Canal Saint-Martin | Quai de Jemmapes | 48.873548 | 2.364072 | housenumber / 0.977236 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=102+Quai+de+Jemmapes+75010+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/transports/82784/Canal-Saint-Martin) |
| 10. Opéra / 9th Arrondissement | Place de l’Opéra | 48.871044 | 2.332135 | street / 0.962040 | [IGN/BAN](https://data.geopf.fr/geocodage/search?q=Place+de+l+Opera+75009+Paris&limit=1) | [Paris je t’aime](https://parisjetaime.com/article/balade-du-palais-royal-a-la-place-vendome-a789) |

The Marais pin uses 2 Rue Eugène Spuller, the town hall alongside Square du Temple, corroborated by the [Paris Centre municipality](https://mairiepariscentre.paris.fr/pages/coordonnees-et-horaires-de-la-mairie-9749). The square’s 64 Rue de Bretagne query returned only a street centroid and was rejected. The canal pin uses 102 Quai de Jemmapes. Representative-point choices are editorial; postcode and source labels were checked. Raw responses are retained outside the site in C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/geocoding.json and marais-reference-alternatives.json.
No hotel official-site URL is added to public HTML or JavaScript. These internal sources concern geography, not booking.

## Travel profiles
Filters are suggestions taken from the guide, not exclusive suitability claims or price guarantees:
- Budget: Latin Quarter, Opéra / 9th.
- Family: Latin Quarter, 7th.
- Couple: Le Marais, Saint-Germain, Montmartre, Canal Saint-Martin.
- Attractions: Le Marais, Saint-Germain, Latin Quarter, 1st, 7th.
All areas also includes Bastille / Oberkampf and South Pigalle, retaining their nightlife purpose.
Labels, advantages and compromises are read from the original cards. The ten short summaries paraphrase that existing editorial content; no partner copy or new room/price claims.
The panel reuses original internal routes, including relevant child guides and the existing Paris-wide shortlist. It does not claim that the seven hotels cover all areas and does not invent an area-specific Klook destination.

## Runtime, accessibility and failures
One page-owned controller initializes selections; Leaflet 1.9.4 and its CSS load only when the canvas approaches within 250 px of the viewport. Fallback scroll/resize detection also defers loading when IntersectionObserver is unavailable.
Five profile buttons and ten numbered area choices use native buttons with aria-pressed and aria-controls. Selecting a pin or area moves focus to the panel heading. Re-adding a filtered marker restores its accessible name. Selected pins are raised above nearby pins; zoom controls and the always-available area list resolve close reference points at wide zoom.
Scroll-wheel zoom is disabled. Coarse-pointer users retain one-finger page scrolling, pinch zoom and buttons. Reduced-motion and forced-color modes are supported.
No JavaScript: native area links and all original content work. Leaflet/CSS failure: chooser and panels remain, canvas hides. Tile failure/timeout: pins, chooser, profiles and internal links remain functional.
No geolocation, runtime geocoder, search API, new analytics handler or affiliate clone. All ten original Klook anchors stay byte-identical.

## Free libraries, attribution and tile policy
Local Leaflet 1.9.4 and its existing BSD-2-Clause LICENSE are reused without modification. No new dependency, key, account, billing or paid service.
[OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) checked on the research date: visible linked attribution, browser Referer (existing strict-origin-when-cross-origin), ordinary HTTP cache behavior; no bulk download, offline archive or cache bypass.
Tile endpoint in the HTML data attribute: https://tile.openstreetmap.org/{z}/{x}/{y}.png. keepBuffer 0, no retina multiplication. Automated repeated tests use fake tiles; screenshot review may request only the normal current viewport without automated pan/zoom.
OSM has no guaranteed traffic quota or SLA and can withdraw access; the native fallback is required. No automatic invoicing.
[Leaflet 1.9.4 documentation](https://leafletjs.com/reference-1.9.4.html).

## Scope and audit integrity
Only the parent HTML plus its dedicated CSS/JS, this internal document, map tests and two exact-hash authorization records in tests/fixtures/site-baseline.json are in scope. Shared scripts, CSS, other Paris pages, Disney, vendor libraries, images, titles, metadata, canonical and Schema stay unchanged.
The existing auditor code, historical findings, exception inventory and previous authorizations are untouched. The two records authorize only the explicitly requested new script tag and script bytes, against this base:
- new_integration_markup: 2fcb1651cad4b02e4f097a3b3fe4bedfca8ff2fd84c14624eab9036a63c3cb80
- new_integration_script: 92b777255a8217dd96764f71aaeee6f40aac375ece6b2e29417f6c0e15ee99ea
These records authorize only the two explicitly requested integration hashes. The owner’s subsequent GO for the PR supplies commit/push/PR authorization; no SEO or affiliation defect is suppressed.

## Final local validation

- 413 Chrome browser checks passed: ten pins/panels, five profile views, exact panel facts and reused internal links, keyboard/focus, 320/390/768/1440 px, text at 200%, forced colors, no JavaScript, no IntersectionObserver, tile/Leaflet JS/Leaflet CSS failure.
- Consent absent/denied/revoked: no affiliate_click. Granted: one event per original CTA, exact inherited payload, no duplicate binding. Area exploration creates no affiliate event.
- 57/57 auditor self-tests passed.
- 15 preservation checks passed; 582 other tracked files match the final base, with only checkout line endings normalized for text.
- Full site audit against 06922e955141eecf391f99356f38ea4baa4b40bc: PASS, zero new errors, 965 known historical findings unchanged. Exactly two new integration declarations; no new exception or audit-code change.
- Initial implementation validation: git diff --check passed, index empty and HEAD at the reviewed main base. Existing worktrees untouched. The final PR phase reruns all checks before the authorized commit/push; no merge is authorized.
- Mobile and desktop screenshots inspected after replacing the overlapping Marais/Bastille references. Both use real viewport tiles and visible OSM attribution. Repeated automated scenarios use simulated tiles.
- Gzip measurements: HTML +751 bytes; page controller 4127 bytes; dedicated CSS 1107 bytes. Existing hero markup and load priorities unchanged. Leaflet requests are absent before viewport approach.
- Field Core Web Vitals, live device/screen-reader review and conversion uplift remain to test; browser QA is not a guarantee of production metrics.

Captures and machine reports (outside the site worktree):
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/browser/desktop-neighborhood-map.png
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/browser/mobile-neighborhood-map.png
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/browser/browser-report.json
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/preservation.json
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/self-tests.json
- C:/Users/1995/AppData/Local/Temp/tripguidely-paris-where-to-stay-map-qa/site-audit.json

Verdict after implementation review: **GO for the authorized PR**. Wait for GitHub Actions and STOP for human validation. Do not merge.
