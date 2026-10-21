# London hotel hub + three guides V1 — local review

- Branch: `feat/london-hotel-guides-v1`; clean starting base/latest fetched main: `47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb` (includes merged Rome PR #54).
- Owner explicitly authorized the five exact baseline entries, a London-only commit/push and Draft PR. No merge or deployment authorized. Auditor and functional site code unchanged after local validation.
- Verdict: **GO for Draft PR**: five exact owner-approved authorizations applied. Official audit PASS, zero errors, five recognized authorizations. All 32 historic entries and all other baseline records preserved.

## Pages

| Page | Improvements |
| --- | --- |
| `/hotels/london/` | All original paragraphs, anchors, images, H1, canonical/hreflang, JSON-LD, scripts and CSP retained. Three guide routes near the top; three photo previews introduce all nine hotels. Title, description and matching social text updated for first-visit area/Tube intent. |
| `/hotels/london/luxury-hotels/` | Savoy/Strand, Shard/London Bridge and Langham/Oxford Circus differentiated by location, view category and inclusions. Three quick choices, mobile comparison, map and three photo galleries. |
| `/hotels/london/family-hotels/` | Suite kitchens versus exact sleeping arrangement, apartment category and occupancy distinguished; Vauxhall, Warwick Road and Trafalgar Square compared. |
| `/hotels/london/cheap-hotels/` | Liverpool Street, Holborn and Blackfriars Road compared by compact room, window category, luggage and full total. |

All new guides use scoped London navy/teal styling and existing header/footer/site.js. Each hotel has one early static Klook CTA and a map selection can clone that same link with a distinct placement identifier. No competing tracking system, direct official hotel booking anchor, new affiliate URL, fabricated rate/rating/availability or personal hotel-test claim.

Three maps adapt the already implemented New York controller, loading unchanged local Leaflet 1.9.4 lazily. Exact source-backed property points, selection/card synchronization, numbered keyboard markers, touch movement lock, panel scroll reset and failure fallbacks are retained. The London map CTA was moved before address/room facts so it remains fully visible on small screens. No other city/controller/vendor assets changed.

New guide canonicals added to `sitemap-london.xml`; existing entries and dates retained. Practical TfL maps/accessibility and internal London area/itinerary/transport/sightseeing links included.

## Nine exact Klook/SubID mappings

| Hotel | Supplied short link | Supplied HTML SubID | First HEAD target |
| --- | --- | --- | --- |
| The Savoy | https://klook.tpk.ro/3MIczRWd | `london_luxury_savoy` | https://www.klook.com/hotels/detail/253441-the-savoy/ |
| Shangri-La The Shard, London | https://klook.tpk.ro/8hv8Ydc3 | `london_luxury_shard` | https://www.klook.com/hotels/detail/276467-shangrila-the-shard-london/ |
| The Langham, London | https://klook.tpk.ro/IZoWBLQU | `london_luxury_langham` | https://www.klook.com/hotels/detail/397831-the-langham-london/ |
| Staybridge Suites London – Vauxhall | https://klook.tpk.ro/O9FymwTV | `london_family_staybridge` | https://www.klook.com/hotels/detail/280436-staybridge-suites-london--vauxhall-by-ihg/ |
| Residence Inn by Marriott London Kensington | https://klook.tpk.ro/BY4TrnYK | `london_family_residence` | https://www.klook.com/hotels/detail/269874-residence-inn-by-marriott-london-kensington/ |
| Citadines Trafalgar Square London | https://klook.tpk.ro/JTNTiOoK | `london_family_citadines` | https://www.klook.com/hotels/detail/450124-citadines-trafalgar-square-london/ |
| Point A London Liverpool Street | https://klook.tpk.ro/2jwtcX4r | `london_cheap_pointa` | https://www.klook.com/hotels/detail/426970-point-a-london-liverpool-street/ |
| The Z Hotel Holborn | https://klook.tpk.ro/96ZF10xT | `london_cheap_zholborn` | https://www.klook.com/hotels/detail/573167-the-z-hotel-holborn/ |
| ibis London Blackfriars | https://klook.tpk.ro/zeO1g3Av | `london_cheap_ibis` | https://www.klook.com/hotels/detail/257814-ibis-london-blackfriars/ |

One HEAD request was made to each supplied short URL, stopping at its initial response without following the Klook affiliate redirect or opening a booking journey. All nine returned 302 to `affiliate.klook.com` with the corresponding named hotel in `k_site` and Partner ID `699178` visible in `aid`. These diagnostic requests may be counted by a provider; no account click-count claim is made.

**Not confirmed:** the account-side SubID/project configuration is not exposed by that response. Exact HTML `data-subid` values are not proof of how Travelpayouts stores the short link. No commission, booking, conversion or attribution guarantee. Final rendered Klook product pages and actual GA4 receipt were not verified.

Static CTA IDs: `<SubID>_hotel_card`; map clone IDs: `<SubID>_map`; `data-offer-id` is the exact SubID. Both use unchanged delegated consent-aware `site.js`. All original hub anchors remain exact; it contains no historical `js-aff` Klook CTA. Existing Drive and CSP on the hub remain unchanged; new guides do not add Drive.

## Photos

All 27 supplied URLs downloaded and decoded successfully; three per hotel in the original order. Originals remain intact outside Git. 108 variants: 480w/960w, WebP q84/method6 and AVIF q63/speed6. Full-frame proportional LANCZOS resizing with rounded integer height; no new crop, retouch or upscale.

Gallery main images and thumbnails use `object-fit: contain`, including tall Shard/Staybridge/ibis exteriors; each can open its local 960w full composition. AVIF with WebP fallback, responsive srcset/sizes, explicit intrinsic dimensions and below-fold lazy/async/low-priority loading. Three existing variants reused for hub previews.

| Hotel | Originals (in supplied order) | Generated assets | Total optimized KiB |
| --- | --- | --- | --- |
| The Savoy | WEBP 1680×1364; WEBP 1680×1090; JPEG 1920×1440 | 12 | 660.7 |
| Shangri-La The Shard, London | WEBP 1680×2340; WEBP 1680×1132; WEBP 1680×1013 | 12 | 535.1 |
| The Langham, London | WEBP 1680×1258; WEBP 1680×1099; JPEG 1920×1536 | 12 | 747.5 |
| Staybridge Suites London – Vauxhall | JPEG 1470×2000; WEBP 1680×1105; JPEG 1920×1278 | 12 | 769.6 |
| Residence Inn by Marriott London Kensington | JPEG 1920×1280; JPEG 1920×1280; JPEG 1920×1287 | 12 | 678.0 |
| Citadines Trafalgar Square London | WEBP 1680×1060; JPEG 1920×1127; JPEG 1920×1146 | 12 | 420.8 |
| Point A London Liverpool Street | JPEG 1920×1280; JPEG 1920×1280; WEBP 1680×1121 | 12 | 690.4 |
| The Z Hotel Holborn | JPEG 1920×1181; JPEG 1920×1281; JPEG 1920×1281 | 12 | 591.4 |
| ibis London Blackfriars | WEBP 1680×2327; JPEG 1920×1280; WEBP 1680×1121 | 12 | 554.5 |

Total optimized storage: 5,783,448 bytes (5.52 MiB); visitors request selected responsive sources rather than all variants. Exact original paths, source/final URLs, hashes, individual variant dimensions/bytes/hashes, captions and processing are in `docs/qa/london-hotels-sources.json`.

Photos retain the owner-selected hotel association and visually consistent facades/brands/shared areas. Interior photographs do not independently prove a room category or that a pictured service is included. No additional license or independent live-gallery match is invented; local integration follows the owner request.

## Fact checks and limits

- Staybridge: suite kitchens documented; exact occupancy and sleeping configuration not independently established. No claim that an arbitrary suite sleeps four.
- Residence Inn: kitchens and one-/two-bedroom formats documented. Selected double/twin plus sofa-bed descriptions are category-specific. The generic reservation widget maximum of eight is not used as room capacity.
- Citadines: published studio maximum two, one-bedroom four, two-bedroom six. Actual sleeping places and cot/extra-bed arrangements still require the named offer.
- Point A Liverpool Street is the Folgate Street property; windowless categories and the distinct Shoreditch property are not conflated.
- Z Holborn: Kingsway address and windowless category disclosed; compact bed/room wording kept distinct.
- ibis: named double-plus-sofa-bed category distinguished from a standard double.
- Luxury: room view, club access, pool conditions and dining must match the actual rate; no blanket view/inclusion guarantee.

Primary official URLs and check dates plus coordinate provenance are retained in the register. Four property coordinate sources are official page data; Savoy uses its official map link; four other points use exact-property/address OpenStreetMap results. Markers aid location, not entrance or step-free navigation.

## Validation

- Full targeted suite: **3881 assertions passed**, 24 page/width views (320,390,641,760,900,1440). Eight main-content axe WCAG A/AA checks: zero violations.
- Initial test adaptation stopped at a leftover Rome/TfL source URL assertion before browser journeys; corrected in the new test. No site failure was hidden.
- After visual review, map CTA ordering was improved. Only targeted map validation repeated: **1,095 assertions passed across 15 category/width views** (320,390,641,900,1440), including full CTA visibility without panel scrolling and six map-specific axe checks. Photos, hub and other cities were not retested unnecessarily.
- Tests include exact URLs/SubIDs and responsive image hashes, canonical/schema/sitemap/internal fragments, keyboard skip/details/marker/CTA, no horizontal overflow, 641px map controls, panel scroll reset, touch lock/Escape, no-JS booking links, and failed Leaflet/tile fallbacks.
- Unknown/refused consent produces no custom GA4 event in the stub. Granted consent produces exactly one affiliate_click per activation, including Enter. Site/map reinitialization creates no duplicate listeners. Empty/same-page hrefs do not count as outbound affiliate activations. All partner/analytics network traffic blocked in the browser tests.
- Real-map review separately allowed only OpenStreetMap tiles and local site assets: three desktop maps plus Family mobile reached ready, decoded real background tiles and displayed all three markers. No GA4/partner traffic allowed.
- Initial official audit identified five expected protected-review gates only. After explicit owner approval, official audit run once: **PASS, zero errors, five recognized authorizations**, 956 known historical findings and 48 resolved fixture findings. No auditor rule or historic baseline record changed. Browser suites were not rerun because functional files and images are unchanged; only static baseline/preservation checks repeated.
- All 27 original hashes preserved and all 108 optimized images independently decoded at their recorded dimensions/formats.
- Field Core Web Vitals, actual GA4 receipt, account-side Travelpayouts SubIDs/project association and production partner/Drive behavior remain unverified. Offline event generation is not GA4 receipt or commission evidence.

## Exact owner-approved authorizations

The five entries below were applied only after explicit owner approval and exact current hash verification. The review reference names the owner instruction without inventing an identity. Markup/metadata hashes are per-source auditor contract fingerprints; the script hash is the exact LF-normalized file hash.

```json
[
  {
    "kind": "seo_metadata",
    "source": "hotels/london/index.html",
    "base_revision": "47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb",
    "before": "0632ce500b0b0c0ace6334d5c12cb05d60b2a553ac08f1305778d16e9fe743b4",
    "after": "eef06c27f00ef7841b9fabd7018e7fd27898d059a6983f466fae89db22c3ee0b",
    "reason": "Intentional London hub title/description and corresponding social metadata update for first-visit, neighborhood and Tube-access intent. Original H1, canonical, hreflang, JSON-LD, content, anchors, Drive, consent/shared script and CSP preserved. Exact hashes explicitly approved by the owner in LONDON : APPROBATION FINALE ET PR.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — LONDON : APPROBATION FINALE ET PR (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_markup",
    "source": "hotels/london/cheap-hotels/index.html",
    "base_revision": "47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb",
    "before": null,
    "after": "33f17e7d893665c5eaa231023b23dffcec10ef17d31981070fba28e869654d08",
    "reason": "London-only progressive Leaflet map adapter/inclusion derived from the existing New York mechanism, using unchanged local Leaflet assets. Nine source-backed property points, accessible synchronized choices, touch-safe movement, panel scroll reset, early map CTA and asset/tile fallback. Existing site.js alone tracks consent-aware affiliate clicks; exact supplied links/SubIDs preserved. No changes to shared scripts or other cities. Exact hashes explicitly approved by the owner in LONDON : APPROBATION FINALE ET PR.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — LONDON : APPROBATION FINALE ET PR (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_markup",
    "source": "hotels/london/family-hotels/index.html",
    "base_revision": "47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb",
    "before": null,
    "after": "33f17e7d893665c5eaa231023b23dffcec10ef17d31981070fba28e869654d08",
    "reason": "London-only progressive Leaflet map adapter/inclusion derived from the existing New York mechanism, using unchanged local Leaflet assets. Nine source-backed property points, accessible synchronized choices, touch-safe movement, panel scroll reset, early map CTA and asset/tile fallback. Existing site.js alone tracks consent-aware affiliate clicks; exact supplied links/SubIDs preserved. No changes to shared scripts or other cities. Exact hashes explicitly approved by the owner in LONDON : APPROBATION FINALE ET PR.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — LONDON : APPROBATION FINALE ET PR (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_markup",
    "source": "hotels/london/luxury-hotels/index.html",
    "base_revision": "47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb",
    "before": null,
    "after": "33f17e7d893665c5eaa231023b23dffcec10ef17d31981070fba28e869654d08",
    "reason": "London-only progressive Leaflet map adapter/inclusion derived from the existing New York mechanism, using unchanged local Leaflet assets. Nine source-backed property points, accessible synchronized choices, touch-safe movement, panel scroll reset, early map CTA and asset/tile fallback. Existing site.js alone tracks consent-aware affiliate clicks; exact supplied links/SubIDs preserved. No changes to shared scripts or other cities. Exact hashes explicitly approved by the owner in LONDON : APPROBATION FINALE ET PR.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — LONDON : APPROBATION FINALE ET PR (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  },
  {
    "kind": "new_integration_script",
    "source": "assets/js/london-hotel-map.js",
    "base_revision": "47d11b6d8cd811fe9fd526d3a785dcdc4ba989cb",
    "before": null,
    "after": "a14f66c56ac4e07aa7f92a04385371410d77035d838e2be4336be0bfacb1a901",
    "reason": "London-only progressive Leaflet map adapter/inclusion derived from the existing New York mechanism, using unchanged local Leaflet assets. Nine source-backed property points, accessible synchronized choices, touch-safe movement, panel scroll reset, early map CTA and asset/tile fallback. Existing site.js alone tracks consent-aware affiliate clicks; exact supplied links/SubIDs preserved. No changes to shared scripts or other cities. Exact hashes explicitly approved by the owner in LONDON : APPROBATION FINALE ET PR.",
    "reviewed_by": "owner instruction: TRIPGUIDELY — LONDON : APPROBATION FINALE ET PR (Codex conversation, 2026-10-20)",
    "recorded_on": "2026-10-20"
  }
]
```

## Remaining steps

1. Prepare the owner-authorized London-only commit and Draft PR, then review GitHub Actions.
2. Review the Draft PR before any merge; the exact baseline approval and successful local audit are recorded above.
3. Confirm account-side Travelpayouts SubID/project configuration before making attribution claims. This is distinct from the observed nine hotel destinations and Partner ID.
4. Commit/push/Draft PR are now explicitly authorized; no merge/deployment authorized. The existing hub Drive integration and CSP were preserved and their production behavior is outside these local checks.

## Exact changed-file inventory

120 files total: the 119 locally validated London files plus the explicitly approved existing baseline update. No file was removed merely to keep the earlier pre-authorization count.

- `assets/css/pages/london-hotels.css`
- `assets/images/hotels/london/citadines-trafalgar-square-london-exterior-480x303.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-exterior-480x303.webp`
- `assets/images/hotels/london/citadines-trafalgar-square-london-exterior-960x606.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-exterior-960x606.webp`
- `assets/images/hotels/london/citadines-trafalgar-square-london-living-kitchen-480x282.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-living-kitchen-480x282.webp`
- `assets/images/hotels/london/citadines-trafalgar-square-london-living-kitchen-960x564.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-living-kitchen-960x564.webp`
- `assets/images/hotels/london/citadines-trafalgar-square-london-studio-480x286.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-studio-480x286.webp`
- `assets/images/hotels/london/citadines-trafalgar-square-london-studio-960x573.avif`
- `assets/images/hotels/london/citadines-trafalgar-square-london-studio-960x573.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-exterior-480x665.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-exterior-480x665.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-exterior-960x1330.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-exterior-960x1330.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-lounge-480x320.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-lounge-480x320.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-lounge-960x641.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-lounge-960x641.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-twin-room-480x320.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-twin-room-480x320.webp`
- `assets/images/hotels/london/ibis-london-blackfriars-twin-room-960x640.avif`
- `assets/images/hotels/london/ibis-london-blackfriars-twin-room-960x640.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-corridor-480x320.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-corridor-480x320.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-corridor-960x641.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-corridor-960x641.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-exterior-480x320.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-exterior-480x320.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-exterior-960x640.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-exterior-960x640.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-lounge-480x320.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-lounge-480x320.webp`
- `assets/images/hotels/london/point-a-liverpool-street-london-lounge-960x640.avif`
- `assets/images/hotels/london/point-a-liverpool-street-london-lounge-960x640.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-exterior-480x320.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-exterior-480x320.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-exterior-960x640.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-exterior-960x640.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-lounge-480x322.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-lounge-480x322.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-lounge-960x644.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-lounge-960x644.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-reception-480x320.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-reception-480x320.webp`
- `assets/images/hotels/london/residence-inn-kensington-london-reception-960x640.avif`
- `assets/images/hotels/london/residence-inn-kensington-london-reception-960x640.webp`
- `assets/images/hotels/london/shangri-la-shard-london-exterior-480x669.avif`
- `assets/images/hotels/london/shangri-la-shard-london-exterior-480x669.webp`
- `assets/images/hotels/london/shangri-la-shard-london-exterior-960x1337.avif`
- `assets/images/hotels/london/shangri-la-shard-london-exterior-960x1337.webp`
- `assets/images/hotels/london/shangri-la-shard-london-lobby-480x323.avif`
- `assets/images/hotels/london/shangri-la-shard-london-lobby-480x323.webp`
- `assets/images/hotels/london/shangri-la-shard-london-lobby-960x647.avif`
- `assets/images/hotels/london/shangri-la-shard-london-lobby-960x647.webp`
- `assets/images/hotels/london/shangri-la-shard-london-pool-480x289.avif`
- `assets/images/hotels/london/shangri-la-shard-london-pool-480x289.webp`
- `assets/images/hotels/london/shangri-la-shard-london-pool-960x579.avif`
- `assets/images/hotels/london/shangri-la-shard-london-pool-960x579.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-bedroom-480x316.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-bedroom-480x316.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-bedroom-960x631.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-bedroom-960x631.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-breakfast-room-480x320.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-breakfast-room-480x320.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-breakfast-room-960x639.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-breakfast-room-960x639.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-exterior-480x653.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-exterior-480x653.webp`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-exterior-960x1306.avif`
- `assets/images/hotels/london/staybridge-suites-vauxhall-london-exterior-960x1306.webp`
- `assets/images/hotels/london/the-langham-london-dining-room-480x384.avif`
- `assets/images/hotels/london/the-langham-london-dining-room-480x384.webp`
- `assets/images/hotels/london/the-langham-london-dining-room-960x768.avif`
- `assets/images/hotels/london/the-langham-london-dining-room-960x768.webp`
- `assets/images/hotels/london/the-langham-london-exterior-480x359.avif`
- `assets/images/hotels/london/the-langham-london-exterior-480x359.webp`
- `assets/images/hotels/london/the-langham-london-exterior-960x719.avif`
- `assets/images/hotels/london/the-langham-london-exterior-960x719.webp`
- `assets/images/hotels/london/the-langham-london-pool-480x314.avif`
- `assets/images/hotels/london/the-langham-london-pool-480x314.webp`
- `assets/images/hotels/london/the-langham-london-pool-960x628.avif`
- `assets/images/hotels/london/the-langham-london-pool-960x628.webp`
- `assets/images/hotels/london/the-savoy-london-indoor-pool-480x360.avif`
- `assets/images/hotels/london/the-savoy-london-indoor-pool-480x360.webp`
- `assets/images/hotels/london/the-savoy-london-indoor-pool-960x720.avif`
- `assets/images/hotels/london/the-savoy-london-indoor-pool-960x720.webp`
- `assets/images/hotels/london/the-savoy-london-lobby-480x311.avif`
- `assets/images/hotels/london/the-savoy-london-lobby-480x311.webp`
- `assets/images/hotels/london/the-savoy-london-lobby-960x623.avif`
- `assets/images/hotels/london/the-savoy-london-lobby-960x623.webp`
- `assets/images/hotels/london/the-savoy-london-riverside-480x390.avif`
- `assets/images/hotels/london/the-savoy-london-riverside-480x390.webp`
- `assets/images/hotels/london/the-savoy-london-riverside-960x779.avif`
- `assets/images/hotels/london/the-savoy-london-riverside-960x779.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-bedroom-480x320.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-bedroom-480x320.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-bedroom-960x640.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-bedroom-960x640.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-exterior-480x295.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-exterior-480x295.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-exterior-960x590.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-exterior-960x590.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-lounge-480x320.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-lounge-480x320.webp`
- `assets/images/hotels/london/z-hotel-holborn-london-lounge-960x640.avif`
- `assets/images/hotels/london/z-hotel-holborn-london-lounge-960x640.webp`
- `assets/js/london-hotel-map.js`
- `docs/london-hotel-guides-v1.md`
- `docs/qa/london-hotels-pending-authorizations.json`
- `docs/qa/london-hotels-sources.json`
- `hotels/london/cheap-hotels/index.html`
- `hotels/london/family-hotels/index.html`
- `hotels/london/index.html`
- `hotels/london/luxury-hotels/index.html`
- `sitemap-london.xml`
- `tests/fixtures/site-baseline.json`
- `tests/test_london_hotels.cjs`
