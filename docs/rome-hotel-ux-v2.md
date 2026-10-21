# Rome hotel UX V2 — local review

- Branch: `feat/rome-hotel-ux-v2`; clean starting base/latest fetched main: `d681c019b20aebc6ee60880201edaea2e49191d1` (merged London PR #55).
- Owner authorized only four exact baseline additions and the Rome UX V2 commit/push/Draft PR. No merge or deployment authorized. Functional site files and existing photos are unchanged since validation.
- Verdict: **GO for Draft PR**. Four exact owner-approved authorizations applied; official audit PASS, zero errors, four recognized authorizations. No SEO contract change.

## Targeted changes

- Add one progressive OpenStreetMap/Leaflet map to each existing Luxury, Family and Cheap Rome guide. Three numbered hotel markers, synchronized choices/static cards, selected name/real existing image/location/short fit text and exact cloned Klook CTA.
- Adapt the existing London/New York mechanism without altering those cities or their controllers. Reuse local Leaflet 1.9.4 unchanged; lazy initialization, reset-to-all, keyboard marker controls, live selection/loading status, touch scrolling lock/Escape, panel scroll reset, asset/tile failure handling and static address/detail links.
- Add exactly nine visual hub hotel cards under “Nine hotels to explore in Rome”, in three categories. Each has its original optimized image, exact property name, location, short benefit/trade-off and internal link to the existing `#card-<key>` guide anchor. Existing three top guide routes and all original hub anchors/content are retained.
- Remove exactly nine requested `p.rh-source` provenance UI paragraphs (three per guide). Original source register, verified facts, booking cautions, image captions and affiliate/legal disclosures retained. No replacement provenance paragraph.

## Preservation

- Complete `<head>` markup is identical to the base on all four pages: title, meta description, canonical, hreflang and JSON-LD unchanged. No sitemap or SEO metadata update needed.
- All nine original complete static Klook anchors and both historical hub Klook anchors unchanged. Map CTA is cloned from its original card, with `_map` CTA ID/location; no alternate commercial destination or direct official hotel booking anchor added.
- All 40 existing Rome image variants unchanged; no photo downloaded, converted, removed or replaced. Original `docs/qa/rome-hotels-sources.json`, shared `site.js`, vendor library and auditor unchanged. Baseline changes consist exclusively of the four owner-approved entries; all 37 historical authorizations and all other baseline records are preserved.
- No link/account-side SubID validation was repeated. Existing URL/SubID invariants are checked locally. Actual GA4 receipt, commissions and production Drive behavior are not established by these tests.

## Verified map locations

Published property/feature points are used for planning, not a guarantee of an entrance or step-free route. The original source register remains intact; new coordinate evidence is isolated in `docs/qa/rome-hotel-ux-v2-locations.json`.

| Hotel | Latitude | Longitude | Evidence |
| --- | --- | --- | --- |
| Hotel de Russie | 41.9099087 | 12.4775123 | OpenStreetMap hotel feature De Russie, Vicolo del Borghetto, Campo Marzio, Municipio Roma I, Roma, Roma Capitale, Lazio, 00187, Italia |
| Hotel Eden | 41.906625 | 12.4863071 | OpenStreetMap hotel feature Hotel Eden, 49, Via Ludovisi, Ludovisi, Municipio Roma I, Roma, Roma Capitale, Lazio, 00187, Italia |
| Hotel Manfredi Suite in Rome | 41.9073704 | 12.4809598 | Exact Hotel Manfredi Suite Rome Google property point linked by its official site; Via Margutta 61. Not Palazzo Manfredi by the Colosseum. |
| Hotel Quirinale | 41.9016357 | 12.4948372 | OpenStreetMap hotel feature Hotel Quirinale, 7, Via Nazionale, Castro Pretorio, Municipio Roma I, Roma, Roma Capitale, Lazio, 00184, Italia |
| Starhotels Michelangelo | 41.898842 | 12.454535 | Official View on Google Maps link and new google.maps.LatLng(41.898842, 12.454535) on its property location page. |
| Aparthotel Adagio Rome Vatican | 41.919691 | 12.436872 | Official Hotel GeoCoordinates JSON-LD for Adagio Rome Vatican. Separate OSM hotel/address record confirms Via Damiano Chiesa 8 in Balduina. |
| The Beehive | 41.9031941 | 12.5045889 | Official site businessLocationCoordinates: latitude 41.9031941, longitude 12.5045889; Via Marghera 8. |
| Hotel Sonya | 41.9000334 | 12.4956482 | OpenStreetMap hotel feature Hotel Sonya, 58, Via del Viminale, Castro Pretorio, Municipio Roma I, Roma, Roma Capitale, Lazio, 00184, Italia |
| Generator Rome | 41.895615 | 12.505675 | Official property map element data-google-map-lat="41.8956150" and data-google-map-long="12.5056750". Its old shortened Google link points at nearby street number 257 and is not used. |

Manfredi is the Via Margutta 61 property. Its official Google property link resolves to 41.9073704, 12.4809598, distinct from Palazzo Manfredi by the Colosseum. Generator uses its official map element coordinates; the old shortened Google map link resolves to nearby street number 257 and was not used.

Hotel Sonya retains the existing Opera House surroundings photograph, correctly identified in its alt/caution and selected-map note. It is not presented as the hotel facade. No new photograph was introduced to replace it.

## Validation

- New Rome UX V2 targeted suite: **957 assertions passed** across 12 hub/guide responsive views. Existing multi-thousand-assertion Rome V1 suites not repeated.
- Added explicit direct-hotel-host static check: all four pages pass. Only the static preservation checks were rerun after adding that assertion; no functional code changed.
- Eight axe WCAG A/AA runs on the new hub/map components: zero violations. This is not a full-site accessibility certification.
- All nine hub cards followed in the browser to their exact hotel anchors; existing optimized photos decoded in new hub and selected-map contexts.
- Marker/list/card synchronization, all source-backed coordinate attributes, reset-to-all geometry, keyboard selection, fully visible CTA at 320/641/1440, touch lock/Escape, panel scroll reset, and no-JS/failed asset/failed tile fallbacks checked.
- Unknown/refused consent: no custom GA4 event in the stub. Granted consent: one affiliate_click per legitimate static/map activation, including keyboard Enter. Reinjection of site/map scripts produces no duplicate listeners or choices. Selection/reset does not count as an affiliate click.
- Real OpenStreetMap validation: all three maps reached ready with actual decoded background tiles and three markers, on desktop 1440px and mobile 390px. Partner/analytics traffic was blocked; no live affiliate click made.
- Initial official audit identified four expected map integration gates. After exact owner approval, official audit executed once: PASS, zero errors, four recognized authorizations. 956 known historical findings; 48 resolved fixture findings. No SEO contract change, auditor rule change or historical baseline edit. The 957 assertions and 270 static checks were not repeated; only the test expectation was maintained for the approved baseline, with syntax validation.
- git diff --check passes. Snapshot verification: 825 starting tracked files checked; only the four Rome HTML pages, Rome CSS and the now-approved baseline changed among existing files. All 40 other worktrees retain HEAD, status and dirty-file hashes.

## Exact owner-approved authorizations

Applied only after the owner approved the exact kind/source/base/before/after tuples. Review references record the owner instruction without inventing an identity. Markup hashes identify the new inclusion; the script hash covers LF-normalized content.

```json
[
  {
    "kind": "new_integration_markup",
    "source": "hotels/rome/cheap-hotels/index.html",
    "base_revision": "d681c019b20aebc6ee60880201edaea2e49191d1",
    "before": null,
    "after": "8d70933c656efa63aab7852086e5f3addc6232996956bcee294ca513b1c9ddd3",
    "reason": "Owner explicitly approved this exact Rome UX V2 map inclusion/controller hash. Reuse unchanged local Leaflet and existing consent-aware site.js; add only Rome marker/photo/card selection, reset, keyboard/touch behavior and failure fallbacks. Preserve original SEO/head markup, photo assets, nine Klook URL/SubID pairs, two historical hub links and other cities.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — ROME UX V2 | FINALISATION ET PR DRAFT (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_markup",
    "source": "hotels/rome/family-hotels/index.html",
    "base_revision": "d681c019b20aebc6ee60880201edaea2e49191d1",
    "before": null,
    "after": "8d70933c656efa63aab7852086e5f3addc6232996956bcee294ca513b1c9ddd3",
    "reason": "Owner explicitly approved this exact Rome UX V2 map inclusion/controller hash. Reuse unchanged local Leaflet and existing consent-aware site.js; add only Rome marker/photo/card selection, reset, keyboard/touch behavior and failure fallbacks. Preserve original SEO/head markup, photo assets, nine Klook URL/SubID pairs, two historical hub links and other cities.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — ROME UX V2 | FINALISATION ET PR DRAFT (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_markup",
    "source": "hotels/rome/luxury-hotels/index.html",
    "base_revision": "d681c019b20aebc6ee60880201edaea2e49191d1",
    "before": null,
    "after": "8d70933c656efa63aab7852086e5f3addc6232996956bcee294ca513b1c9ddd3",
    "reason": "Owner explicitly approved this exact Rome UX V2 map inclusion/controller hash. Reuse unchanged local Leaflet and existing consent-aware site.js; add only Rome marker/photo/card selection, reset, keyboard/touch behavior and failure fallbacks. Preserve original SEO/head markup, photo assets, nine Klook URL/SubID pairs, two historical hub links and other cities.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — ROME UX V2 | FINALISATION ET PR DRAFT (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_script",
    "source": "assets/js/rome-hotel-map.js",
    "base_revision": "d681c019b20aebc6ee60880201edaea2e49191d1",
    "before": null,
    "after": "c8a2284baf576ca1bcf021db8caf7fc3b16f6392519ce3cfb382d6506c2abbfe",
    "reason": "Owner explicitly approved this exact Rome UX V2 map inclusion/controller hash. Reuse unchanged local Leaflet and existing consent-aware site.js; add only Rome marker/photo/card selection, reset, keyboard/touch behavior and failure fallbacks. Preserve original SEO/head markup, photo assets, nine Klook URL/SubID pairs, two historical hub links and other cities.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — ROME UX V2 | FINALISATION ET PR DRAFT (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  }
]
```

## Remaining step

Review the owner-authorized Draft PR and GitHub Actions before any merge. The four exact approvals and green local audit are recorded above. No merge/deployment authorized. Existing production Drive behavior and actual GA4 receipt were not rechecked or changed.

## Exact changed-file inventory

11 files: the ten locally validated Rome UX V2 files plus the approved existing baseline update.

- `assets/css/pages/rome-hotels.css`
- `assets/js/rome-hotel-map.js`
- `docs/qa/rome-hotel-ux-v2-locations.json`
- `docs/qa/rome-hotel-ux-v2-pending-authorizations.json`
- `docs/rome-hotel-ux-v2.md`
- `hotels/rome/cheap-hotels/index.html`
- `hotels/rome/family-hotels/index.html`
- `hotels/rome/index.html`
- `hotels/rome/luxury-hotels/index.html`
- `tests/fixtures/site-baseline.json`
- `tests/test_rome_hotel_ux_v2.cjs`
