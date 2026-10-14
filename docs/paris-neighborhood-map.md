# Paris neighborhood map — PR #41 mobile UX

Branch: feat/paris-neighborhood-mobile-ux.
Worktree: C:/Users/1995/AppData/Local/Temp/tripguidely-paris-neighborhood-mobile-ux.
Base: 5f3c1d0db4ee88689352607e6adf4bc6b83407a5, origin/main after PR #40, fetched on 2026-10-13.
Owner GO on 2026-10-13 authorizes commit, push and a PR toward main after rerunning all checks. Wait for GitHub Actions, then stop for human review. No merge or worktree deletion.

## Structure before / after

Before, small screens placed the street map, then the selected card, then the ten-button numbered list. Users reached the chooser only after crossing the canvas and the current decision card.
After, profiles precede a labeled native select, selection status, the complete selected card, then the same canvas. The select contains all ten numbered choices in All areas; each profile shows only its original-number matches. No second map or extra affiliate CTA.
At 64rem and above, the ten numbered buttons form two rows above the existing map on the left and selected card on the right. The DOM keeps the decision card before the map; CSS gives desktop its two-column arrangement. At increased text size the layout returns to the single-column chooser when the rem breakpoint requires it. Tablet uses the compact chooser and single column.
Without JavaScript (or malformed source data), all ten original native area links remain visible and the original editorial cards and seven hotel cards remain available.

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

Profiles are suggestions from the existing editorial guide, not exclusive suitability claims, availability or price guarantees:
- All areas: original numbers 1–10.
- Budget: 3. Latin Quarter; 10. Opéra / 9th.
- Family: 3. Latin Quarter; 5. 7th.
- Couple: 1. Le Marais; 2. Saint-Germain; 6. Montmartre; 9. Canal.
- Attractions: 1. Le Marais; 2. Saint-Germain; 3. Latin Quarter; 4. 1st; 5. 7th.
- Nightlife: **only 1. Le Marais, 7. Bastille / Oberkampf, 8. South Pigalle**.

All previous profile memberships and all reference coordinates are unchanged. Source cards still require exactly three editorial li elements. The selected card reads those facts and clones only existing internal routes.
PR #40's eleven source links are unchanged: Citadines in the 1st; Pullman and ibis explicitly in the 15th outside the 7th; Hôtel de France on the Gare de Lyon side in the 12th, not Oberkampf; seven explicit shortlist gaps with general-search fallback. Régence, Madrigal and Campanile remain in the general shortlist.

## Accessibility and failure contracts

Six native profile buttons retain aria-pressed; aria-controls references the list, native select, card and canvas. The select has an explicit label and aria-describedby pointing to a polite atomic selection status. Announcements include profile, result count and original selected number. The selection status stays visible; redundant map loading/ready instructions use a visually hidden live status, restored visibly on map or tile failure. The All areas button restores the full ten choices.
Select changes preserve select focus, allowing native arrow-key navigation. Original desktop buttons and pins retain focus transfer to the selected heading. All visible controls and internal card links have at least 44px targets; focus outlines support forced colors.
The enhanced numbered list is hidden below 64rem because the native chooser supplies the same choices. It remains in the DOM and is the fallback without JS. Desktop hides only the native chooser.
Leaflet 1.9.4 and local CSS still load within 250px of the canvas, with the existing scroll/resize fallback. Map height: 320px small phone, 440px tablet, 520px desktop. Scroll-wheel zoom, reference geometry, reduced-motion behavior, coarse-pointer scrolling and tile policy remain unchanged.
Leaflet JS/CSS failure hides the canvas and restores a one-column desktop decision panel; profiles, chooser and internal links remain functional. OSM tile failure retains pins and the chooser, with a visible status message.
No geolocation, geocoder, extra external API, image, library, analytics handler or affiliate clone.

## Free libraries, attribution and tile policy
Local Leaflet 1.9.4 and its existing BSD-2-Clause LICENSE are reused without modification. No new dependency, key, account, billing or paid service.
[OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) checked on the research date: visible linked attribution, browser Referer (existing strict-origin-when-cross-origin), ordinary HTTP cache behavior; no bulk download, offline archive or cache bypass.
Tile endpoint in the HTML data attribute: https://tile.openstreetmap.org/{z}/{x}/{y}.png. keepBuffer 0, no retina multiplication. Automated repeated tests use fake tiles; screenshot review may request only the normal current viewport without automated pan/zoom.
OSM has no guaranteed traffic quota or SLA and can withdraw access; the native fallback is required. No automatic invoicing.
[Leaflet 1.9.4 documentation](https://leafletjs.com/reference-1.9.4.html).

## Scope and audit integrity

Seven paths only: parent HTML, dedicated controller and CSS, this document, browser tests, preservation tests and site-baseline fixture. All other tracked files are compared against the reviewed base, including shared GA4/consent, three child guides, Disney, images and local Leaflet.
All ten complete affiliate anchors must be identical, including label, URL, SubID, rel, target and tracking. All HTML outside the map section, source cards, SEO metadata and Schema must be identical.
The auditor and old fixture facts, exceptions and authorizations stay unchanged. One new integration_script authorization records the owner-requested controller change from the main hash to the exact new hash; it authorizes no other script or defect.

## Validation

Run from this worktree with external QA output:
- node tests/test_paris_neighborhood_map.cjs PLAYWRIGHT_MODULE CHROME OUTPUT_DIR
- python -B tests/test_paris_neighborhood_map_preservation.py
- python -B scripts/audit-site.py --base-ref 5f3c1d0db4ee88689352607e6adf4bc6b83407a5 --self-test
- python -B scripts/audit-site.py --base-ref 5f3c1d0db4ee88689352607e6adf4bc6b83407a5
- git diff --check

Browser matrix: 320, 390, 430, 768 and 1440px; 100%/200% text; keyboard and accessible names/status; reduced motion; forced colors; JS disabled; Leaflet JS/CSS and tile failures; every profile and every area; eleven internal routes; ten affiliates under absent, denied, granted and revoked consent.
Measured reports, captures and before/after layout evidence are retained outside the site at C:/Users/1995/AppData/Local/Temp/tripguidely-paris-neighborhood-mobile-ux-qa. Final validation results are recorded there and summarized for human review.
Local results (2026-10-13):
- 1055 browser assertions passed, including all five widths at 200% text, native chooser, ARIA accessibility tree, focus, touch targets, all filters, consent and map failures.
- Independent geographic/navigation QA: 1055 assertions passed; all ten areas and eleven PR #40 routes, with and without JavaScript at each of the five widths.
- 19 preservation assertions passed; 582 other tracked files match the reviewed main base.
- Auditor: 57/57 self-tests passed; full audit PASS with zero regressions (965 known historical findings remain).
- At 390px, selecting the 1st arrondissement: filters-to-card-title 576px before / 248px after; filters-to-Citadines-link 1167px before / 838px after. This is layout evidence, not a conversion result.
- Local gzip (LF-normalized): HTML +96 bytes; controller +353; CSS +307, total +756 bytes. No additional library or image. Initial Leaflet/tile requests remain absent.
- Mobile and desktop captures with ordinary OSM viewport tiles inspected; no horizontal overflow.
- Initial local review completed without commit/push/PR/merge; the authorized PR phase reruns all checks. git diff --check and worktree comparison are recorded in the external QA report.

Actual screen-reader/device review, production Core Web Vitals and conversion impact remain to test. Automated ARIA and keyboard checks do not claim an NVDA/VoiceOver session or conversion uplift.

Historical implementation: PR #38 established the original map and local Leaflet integration; PR #39 corrected generic Klook labels; PR #40 added verified internal area-to-hotel routes and Chrome's existing 0.5px visibility tolerance. Those commercial and test contracts are preserved.
