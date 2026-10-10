# Paris hotel affiliate and editorial pilot

Review date: 2026-10-09 (America/Toronto).
Starting main: `ae421ffee27c6332c33173395c391add37da2f1c` (PR #23 merged).
Branch: `feat/paris-hotel-affiliate-pilot`.
Worktree: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-affiliate-pilot`.
Local implementation and validation only. Do not stage, commit, push, create a
PR, publish or merge without the next owner instruction.

## Scope and preservation

Only these files belong to this pilot:

- Modified: `hotels/paris/index.html`.
- Added: `assets/css/templates/hotels.css`.
- Added: this document.

The page remains a neighborhood-first "Where to Stay in Paris" guide. Preserve
all original article wording, heading text, section IDs, internal links, FAQs,
dates, metadata, canonical/hreflang, social metadata, JSON-LD, images, scripts,
disclosures and the three original affiliate opening tags. There are seven new
hotel booking anchors; six deferred properties have no commercial placements.
No shared CSS, JavaScript, partial, hub, sitemap, audit, baseline or authorization
changes. No protected cruise or unpublished Disney changes.

## Owner source-of-truth inventory

Copy URL and SubID cells exactly, including case. Official display names may
include accents or a fuller brand name; IDs and addresses identify the intended
property. No redirects or URL parameters may be invented or appended.

For **every row**, commission eligibility, live booking availability and actual
SubID attribution are **UNVERIFIED**. These are three independent outstanding
checks, including for the listing that returned HTTP 200. Public hotel pages and
room-selection controls are not proof of commissionable inventory or attribution.

| Official display name | Exact affiliate URL | Exact SubID | Klook hotel ID | Verified area | Research source | Status | Remaining gaps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Citadines Les Halles Paris | `https://klook.tpk.ro/7c3IV7YH` | `paris_hotel_citadines_halles` | 247912 | 4 rue des Innocents, 75001; Les Halles, 1st | [Ascott](https://www.discoverasr.com/en/citadines/france/citadines-les-halles-paris) | Selected | Eligibility, availability, attribution UNVERIFIED; booked apartment occupancy |
| Pullman Paris Tour Eiffel / Pullman Paris Eiffel Tower | `https://klook.tpk.ro/QlEUdy0e` | `paris_hotel_pullman_eiffel` | 118674 | 18 avenue de Suffren, entrance 22 rue Jean Rey, 75015; Eiffel area, 15th | [Accor](https://pullman.accor.com/en/hotels/paris/7229.html) | Selected | Eligibility, availability, attribution UNVERIFIED; room-specific views |
| ibis Paris Tour Eiffel Cambronne 15ème | `https://klook.tpk.ro/jor8wPCP` | `paris_hotel_ibis_cambronne` | 2846 | 2 rue Cambronne, 75015; Cambronne, 15th | [Accor](https://all.accor.com/hotel/1400/index.en.shtml) | Selected | Eligibility, availability, attribution UNVERIFIED; room size and rate inclusions |
| Hôtel Régence Étoile | `https://klook.tpk.ro/LsvOTPx3` | `paris_hotel_regence_etoile` | 248416 | 24 avenue Carnot, 75017; Étoile/Ternes, 17th | [Official hotel](https://www.hotelregenceetoile.com/en/) | Selected | Eligibility, availability, attribution UNVERIFIED; distinguish Hyatt Regency Paris Étoile |
| Hôtel Madrigal | `https://klook.tpk.ro/L8RoCWCT` | `paris_hotel_madrigal` | 30459 | 32 boulevard Pasteur, 75015; Pasteur/Montparnasse edge, 15th | [Official contact](https://www.hotel-madrigal.com/?page_id=60), [RATP Pasteur](https://www.ratp.fr/en/vos-lignes/vos-stations/pasteur) | Selected | Eligibility, availability, attribution UNVERIFIED; official contact corroborated through search indexing, direct retrieval failed |
| Hôtel de France Gare de Lyon Bastille | `https://klook.tpk.ro/T0Ke9K8B` | `paris_hotel_france_gare_lyon` | 96375 | 12 rue de Lyon, 75012; Gare de Lyon/Bastille edge, 12th | [Official location](https://www.hoteldefrance-paris.fr/en/location) | Selected | Eligibility, availability, attribution UNVERIFIED; current room/noise feedback |
| Campanile Paris 12 – Bercy Village | `https://klook.tpk.ro/vU2HH3fF` | `paris_hotel_campanile_bercy` | 268911 | 17 rue Baron Le Roy, 75012; Bercy, 12th | [Campanile](https://paris-12-bercy-village.campanile.com/en-us/) | Selected | Eligibility, availability, attribution UNVERIFIED; date-specific total price |
| Pullman Paris Montparnasse | `https://klook.tpk.ro/w9gvKJbA` | `paris_hotel_pullman_montparnasse` | 732134 | 19 rue du Commandant René Mouchotte, 75014; Montparnasse, 14th | [Official FAQ](https://www.pullmanparismontparnasse.com/fr/faq/) | Deferred | Eligibility, availability, attribution UNVERIFIED; family-room occupancy |
| Hôtel Beauregard | `https://klook.tpk.ro/ieahj3xg` | `paris_hotel_beauregard` | 488816 | 14 rue Pétel, 75015; Vaugirard, 15th | [Official location](https://www.hotelbeauregard.fr/fr/plan.html) | Deferred | Eligibility, availability, attribution UNVERIFIED; room-specific views and listing-description freshness |
| OKKO HOTELS Paris Porte de Versailles | `https://klook.tpk.ro/ub8eEqdy` | `paris_hotel_okko_versailles` | 112980 | 2 rue du Colonel Pierre Avia, 75015; outer southwestern 15th, Paris, not Versailles town | [OKKO](https://www.okkohotels.com/en/page/paris-porte-de-versailles/.24897.html) | Deferred | Eligibility, availability, attribution UNVERIFIED; actual exhibition itinerary fit |
| B&B HOTEL Paris 17 Batignolles | `https://klook.tpk.ro/gX4TDO9u` | `paris_hotel_bb_batignolles` | 412657 | 4 boulevard Berthier, 75017; Porte de Clichy, outer 17th | [B&B Hotels](https://www.hotel-bb.com/en/hotel/paris-17-batignolles) | Deferred | Eligibility, availability, attribution UNVERIFIED; actual price comparison, not "cheapest" |
| The Originals Boutique, Hôtel Maison Montmartre Paris Les Puces | `https://klook.tpk.ro/kRWzniR1` | `paris_hotel_maison_montmartre` | 417845 | 32 avenue de la Porte de Montmartre, 75018; northern edge/Les Puces, not Montmartre hill | [Official access](https://hotelmaisonmontmartre.com/en/page/contact-acces.17564.html) | Deferred | Eligibility, availability, attribution UNVERIFIED; exact walking route to transport |
| Generator Paris | `https://klook.tpk.ro/t3aQhbjX` | `paris_hotel_generator` | 448880 | 9–11 place du Colonel Fabien, 75010; Colonel Fabien, 10th | [Generator](https://staygenerator.com/hostels/paris) | Deferred | Eligibility, availability, attribution UNVERIFIED; hostel dorm/private room, age/group rules |

### Research evidence and limits

During Phase 1 on the review date, all thirteen supplied short links followed
two redirects to their matching Klook hotel IDs. Citadines returned HTTP 200;
the other twelve final requests returned HTTP 403. Indexed Klook listing names
and addresses matched the intended properties. A blocked request is not proof
of a dead link; none of these checks establishes a completed booking.

The seven selected cards cover distinct central-apartment, Eiffel-area,
western-Paris, Pasteur, rail-arrival and Bercy needs. Suitability is an editorial
inference from documented geography and accommodation format, not a tested-stay
review or a quality ranking. There are no ratings, prices, discounts, availability
promises or guaranteed views. General searches continue to serve neighborhoods
not represented by the owner inventory, including Le Marais and Saint-Germain.

## Components and cascade

Load order: legacy `styles.css`, legacy `hotels.css`, `tokens.css`, `foundation.css`,
`components/editorial.css`, then new `templates/hotels.css`. Add `tg-ui` to body
without changing `data-page="guide"` or `data-section="hotels"`; content is scoped
by `tg-hotels` on main. Every new selector starts with `.tg-ui .tg-hotels`.
No imports, external libraries, new JavaScript, cascade layers or `!important`.

Reuse the existing ink/ocean/sand semantic tokens, display/body typography,
spacing, 68ch measure, wide container, card radius, grid, 44px controls and focus
tokens. The hero keeps its original image markup and sources; its owned layout
shows the full image without text overlay, beside copy when space permits.
The legacy hero classes are replaced locally to avoid their high-specificity
overlay rules. Existing wording, summary items and hero CTA destinations remain.

Hotel cards are semantic articles with H3 names, location, trip fit, practical
copy, address/transport definition lists, a trade-off and one native booking
anchor. All seven cards are image-free. No city image is labeled as a property
photo. Seven comparison rows use row headers, a caption and five column headers;
their details links go to card headings and do not duplicate affiliate buttons.

The two inherited area tables retain their markup/content and focusable named
regions. Scoped CSS restores native table/head/row/cell display, removes mobile
generated labels, and replaces the conflicting 980px/clipped presentation with
bounded horizontal overflow. No data or columns are hidden. Native FAQs and
the existing shared menu/consent code stay functional without custom scripts.

## Affiliate invariants and tracking

There are three historical general-search opening tags, preserved byte-for-byte:

```html
<a class="btn js-aff" data-aff="klook" href="https://klook.tpk.ro/cNYZdcZk" rel="sponsored noopener" target="_blank">
<a class="pill-link js-aff" data-aff="klook" href="https://klook.tpk.ro/cNYZdcZk" rel="sponsored noopener" target="_blank">
<a class="pill-link js-aff" data-aff="klook" href="https://klook.tpk.ro/kdtCrBKA" rel="sponsored noopener" target="_blank">
```

New anchors use the exact owner URL/SubID, `js-aff`, `data-aff="klook"`,
`rel="nofollow sponsored noopener"`, and `target="_blank"`. Their visible label
is "Check availability on Klook"; accessible names identify the property,
destination and new-tab behavior. The disclosure precedes the first hotel card.
Existing article and global disclosures remain unchanged.

Shared affiliate-click code is consent-gated. It records the destination and
program but does not read an anchor's `data-subid` or append it to the URL.
Redirect fields did not visibly expose the owner labels; opaque server-side
mapping may exist. Owner Travelpayouts records and attribution evidence are
required. Do not infer eligibility, commission rates, GA4 delivery or SubID
delivery from markup or a successful local click. No tracking code is changed.

Valid additive anchors must pass the existing audit without fixture changes.
The audit, historical exceptions/contracts and previous authorizations remain
intact; never regenerate the baseline or add exceptions to suppress a failure.

## Existing debt and remaining verification

Preserve all six existing references to absent `/hotels/paris/cheap-hotels/`,
`/hotels/paris/family-hotels/` and `/hotels/paris/luxury-hotels/` routes. A separate
owner decision is required to repair them; this pilot must introduce no new
broken links. Nine visible FAQs and seven FAQ-schema questions remain as found.
Publication/modification dates stay unchanged by owner instruction.

No verified rights registry for property photography was found. Any future
property photos require provenance and reuse permission, truthful captions,
dimensions and responsive derivatives. No imagery is generated or downloaded.

Firefox/Safari, screen-reader review and physical-device testing remain
unverified unless separately performed. Headless Chrome touch emulation is not
a physical touchscreen test. Live GA4 and affiliate attribution are unverified.

## Validation record

QA artifacts and executable checks must remain outside this repository at
`C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-qa`.
Run static preservation checks, CSS Tree/HTML parsing, exact owner mappings,
fragment/image checks, protected files and `git diff --check`.

Run the unchanged workflow commands against the recorded base:

```text
python -B scripts/audit-site.py --base-ref ae421ffee27c6332c33173395c391add37da2f1c --self-test
python -B scripts/audit-site.py --base-ref ae421ffee27c6332c33173395c391add37da2f1c
```

Browser QA must cover seven widths (320, 375, 390, 430, 768, 1024, 1440),
200% root text, actual Chrome zoom where feasible, descendant overflow,
keyboard/wheel/emulated-touch table scrolling, native FAQs, menu/consent,
reduced motion, visible focus and seven intercepted booking clicks. Keep
before/after 390px and 1440px screenshots outside the repo. Local intercepts
prove clickability and href selection, not live partner attribution.

### Observed local results

| Check | Result |
| --- | --- |
| Regression self-tests | 57/57 PASS, exit 0, unchanged test implementation. |
| Full site audit | PASS, exit 0; 133 HTML files, 1,308 affiliate anchors, 12 sitemap XML files. Zero regressions; 971 historical findings, 42 cumulative resolutions and 287 distinct missing asset paths. |
| Historical findings | Exact finding identity set matches starting main; no unexpected additions or resolutions. |
| Protected files/contracts | All 27 cruise hashes and integration scripts match main; all existing contracts remain. No baseline or authorization edits. |
| Affiliate invariants | Three original opening tags byte-identical; seven new exact URL/SubID pairs; all thirteen owner mappings documented; zero deferred hotel placements. |
| Article preservation | Original text, heading wording, old link order/destinations and all old IDs preserved. Original head is byte-identical after removing only the four new stylesheet lines. JSON-LD, scripts, image markup and nine FAQ disclosures unchanged. |
| HTML/CSS | Parse5: zero HTML5 errors; one H1, fourteen H2s and seventeen H3s, without heading-level skips; thirty unique IDs. CSS Tree: zero syntax/property errors, 62 scoped rules, 173 declarations, 33 existing tokens resolved, no new important rules or token overrides. |
| CSS size | New template: 8,735 uncompressed bytes. Four additional stylesheet requests use the established foundation/component files and this template. |
| Responsive layout | Headless Chrome 154.0.8037.98: all seven specified widths and all seven with 200% root text; zero document or non-table descendant overflow; seven booking targets at least 44px high. Original hero image retains its 16:9 ratio. |
| Native Chrome zoom | Persistent Chrome zoom preferences: 200% gives DPR 2 / 631 CSS px; 400% gives DPR 4 / 315 CSS px. No document overflow; keyboard table scrolling passes. These are native zoom settings, not CSS transforms or root-font simulation. |
| Table viewing | All three tables retain visible native headers/cells and bounded overflow. Arrow keys, horizontal wheel and emulated touch scroll each table at normal and 200% root text; last columns remain reachable. No columns/data hidden. |
| Clickability | Seven real local activations open their exact short URLs in new tabs. Requests were intercepted locally; live booking, commission and attribution were not tested. |
| Accessibility interactions | All seven CTAs reached through Tab with visible 3px focus; nine FAQs toggle with Enter/Space; new navigation/detail fragments resolve; mobile menu opens with keyboard, closes with Escape and restores focus; consent accept/decline works. Reduced-motion fragment scrolling uses auto; button transition is 0s; forced-colors focus remains visible. |
| Button text contrast | Measured default 5.55:1, hover 7.75:1, pressed 10.30:1. |
| Isolation/shared UI | Non-opt-in control with added CSS matches original styles/geometry at all seven widths. Shared header/footer styles match main at all seven widths. No JavaScript errors or failed local requests. |
| Existing debt | Exactly six original missing-subguide placements remain; zero new broken links. Nine visible FAQs/seven schema questions and article dates preserved. |
| Whitespace/index | git diff --check PASS; only the three approved paths are changed/new; index remains empty. |

Artifacts: `static-report.json`, `preservation-report.json`, `self-tests.json`,
`site-audit.txt`, `site-audit.json`, `browser-report.json` and
`extra-browser-report.json` in the external QA directory. Required visual pairs:
`before-390.png` / `after-390.png`, `before-1440.png` / `after-1440.png`, plus
the corresponding `-top.png` views. Detail views include `after-390-hotel-picks.png`,
`after-1440-hotel-picks.png` and both comparison views. Enlarged-text,
forced-colors and zoom artifacts remain outside the repository. For native zoom
visual review, use `after-zoom-2-cdp-dip.png` and `after-zoom-4-cdp-dip.png`.
CSS-coordinate capture variants are retained as QA diagnostics, not visual
evidence of the page's zoomed viewport.

The original Disney branch, HEAD and four previously recorded SHA-256 hashes
were rechecked and preserved. Nothing is staged, committed, pushed, deployed
or merged; no PR has been created for this local pilot. Owner review is next.
