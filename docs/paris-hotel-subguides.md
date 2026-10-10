# Paris hotel subguides: local implementation and review record

Reviewed: 2026-10-09, America/Toronto. Starting main: `66d813f83809ce227f99b7334016a40d30d2aa4d` (PR #24 merged).
Branch: `feat/paris-hotel-subguides`.
Worktree: `C:/Users/1995/AppData/Local/Temp/tripguidely-paris-hotel-subguides`.
The owner authorized finalization of these six files: commit, push the isolated feature branch and open a PR against main. Publication and merging remain outside this authorization.

## Scope and search intent

Create the cheap, family and luxury Paris hotel `index.html` files and this document; modify only `sitemap-paris.xml` and the Paris child entry date in `sitemap.xml`.
No CSS, JavaScript, parent-page, image, baseline, auditor or authorization changes.
Cheap focuses on accommodation format, travel friction and total cost; family on occupancy, bedding and room arrangements; luxury on documented facilities, category-specific views and booking inclusions.
The parent remains the broad neighborhood guide. New prose, FAQs, titles and descriptions are original; do not copy the parent shortlist or its neighborhood paragraphs.
Each guide links back to the parent and includes contextually useful sibling/transport/itinerary links.

## Selection and source evidence

- Cheap: ibis Cambronne (official economy positioning), B&B Batignolles (brand affordable positioning, outer-area transport trade-off), Generator (hostel; shared-bed versus private-room distinction). None is claimed always cheapest; no live rates or numerical tax claims. Campanile omitted because no comparable-date cost evidence supports adding another budget recommendation.
- Family: Citadines Les Halles (official studio/apartment category capacities and kitchens); Pullman Montparnasse (Deluxe Family maximum four, two double beds); Régence Étoile (Prestige Family child-under-12 extra-bed rule versus separate connecting category); B&B Batignolles (family/adjoining descriptions, precise occupancy left for confirmation).
- Luxury: Le Meurice, Mandarin Oriental Lutetia and Shangri-La Paris have official category/location/facility evidence. Pullman Eiffel is a separately labeled premium alternative, not an equivalent luxury classification. No awards, ratings, prices, availability guarantees or property photographs.

Evidence reviewed on 2026-10-09; sources support editorial facts, not a completed stay or a partner booking:

| Source | Limited facts used |
| --- | --- |
| https://all.accor.com/hotel/1400/index.en.shtml | ibis economy positioning and property identity |
| https://www.hotel-bb.com/en/city/hotels-paris/bar | B&B affordable positioning, not a particular cheap rate |
| https://www.hotel-bb.com/en/hotel/paris-17-batignolles | Address, family/adjoining descriptions and cot requests; no universal four-person capacity |
| https://staygenerator.com/hostels/paris | Hostel identity and shared/private accommodation formats; current minor age policies remain unverified |
| https://www.discoverasr.com/en/citadines/france/citadines-les-halles-paris | Studios for two, triple apartment, apartments for four, category-specific bedding and kitchens |
| https://www.pullmanparismontparnasse.com/fr/chambres-suites/chambres-deluxe-famille-amis/ | Deluxe Family maximum four, two double beds; connecting arrangements require confirmation |
| https://www.hotelregenceetoile.com/en/ | Prestige Family max three with extra-bed child age condition; connecting category for two adults/two children |
| https://www.dorchestercollection.com/paris/le-meurice | Rue de Rivoli/Tuileries location, room/suite categories and Valmont spa |
| https://www.mandarinoriental.com/en/paris/lutetia | Current property identity and address |
| https://www.mandarinoriental.com/en/paris/lutetia/wellness | Spa, pool and fitness facilities; no guarantee of included services |
| https://www.shangri-la.com/paris/shangrila/ | Property identity, location, distinct Eiffel-view categories and wellness offerings |
| https://www.shangri-la.com/paris/shangrila/about/local-guide/explore-paris/transportation/ | Official address at 10 avenue d'Iéna |
| https://pullman.accor.com/en/hotels/paris/7229.html | Premium alternative; room/category/view distinctions |

## Exact inherited owner inventory

All thirteen mappings from the pilot are retained here unchanged. Placement selection in these new guides does not change their historical status on the parent.

| Property | Exact URL | Exact SubID | Klook ID in pilot inventory | New-guide use |
| --- | --- | --- | --- | --- |
| Citadines Les Halles Paris | `https://klook.tpk.ro/7c3IV7YH` | `paris_hotel_citadines_halles` | 247912 | Family |
| Pullman Paris Tour Eiffel / Pullman Paris Eiffel Tower | `https://klook.tpk.ro/QlEUdy0e` | `paris_hotel_pullman_eiffel` | 118674 | Luxury page, separate premium alternative |
| ibis Paris Tour Eiffel Cambronne 15ème | `https://klook.tpk.ro/jor8wPCP` | `paris_hotel_ibis_cambronne` | 2846 | Cheap |
| Hôtel Régence Étoile | `https://klook.tpk.ro/LsvOTPx3` | `paris_hotel_regence_etoile` | 248416 | Family |
| Hôtel Madrigal | `https://klook.tpk.ro/L8RoCWCT` | `paris_hotel_madrigal` | 30459 | Deferred; no new placement |
| Hôtel de France Gare de Lyon Bastille | `https://klook.tpk.ro/T0Ke9K8B` | `paris_hotel_france_gare_lyon` | 96375 | Deferred; no new placement |
| Campanile Paris 12 – Bercy Village | `https://klook.tpk.ro/vU2HH3fF` | `paris_hotel_campanile_bercy` | 268911 | Deferred; no new placement |
| Pullman Paris Montparnasse | `https://klook.tpk.ro/w9gvKJbA` | `paris_hotel_pullman_montparnasse` | 732134 | Family |
| Hôtel Beauregard | `https://klook.tpk.ro/ieahj3xg` | `paris_hotel_beauregard` | 488816 | Deferred; no new placement |
| OKKO HOTELS Paris Porte de Versailles | `https://klook.tpk.ro/ub8eEqdy` | `paris_hotel_okko_versailles` | 112980 | Deferred; no new placement |
| B&B HOTEL Paris 17 Batignolles | `https://klook.tpk.ro/gX4TDO9u` | `paris_hotel_bb_batignolles` | 412657 | Cheap and family |
| The Originals Boutique, Hôtel Maison Montmartre Paris Les Puces | `https://klook.tpk.ro/kRWzniR1` | `paris_hotel_maison_montmartre` | 417845 | Deferred; no new placement |
| Generator Paris | `https://klook.tpk.ro/t3aQhbjX` | `paris_hotel_generator` | 448880 | Cheap, clearly labeled hostel |

## Newly supplied luxury mappings and redirect checks

| Hotel | Exact short URL | Exact SubID | Expected / observed Klook ID | Result / placement |
| --- | --- | --- | --- | --- |
| Le Meurice | `https://klook.tpk.ro/GOOv5HfU` | `paris_luxury_le_meurice` | 166198 / 166198 | Two HTTP 302 redirects to `/hotels/detail/166198-le-meurice--dorchester-collection/`; final HTTP 403. CTA locally integrated with owner approval; pending publication. |
| Mandarin Oriental Lutetia, Paris | `https://klook.tpk.ro/C2ZHDWrY` | `paris_luxury_lutetia` | 110940 / 110940 | Two HTTP 302 redirects to `/hotels/detail/110940-hotel-lutetia-paris/`; final HTTP 403. CTA locally integrated with owner approval; pending publication. |
| Shangri-La Paris | `https://klook.tpk.ro/D8WBtyB5` | `paris_luxury_shangrila` | 340754 / 340754 | Two HTTP 302 redirects to `/hotels/detail/340754-shangrila-hotel-paris/`; final HTTP 403. CTA locally integrated with owner approval; pending publication. |

Direct urllib checks followed the actual short links. Destination paths, hotel-name slugs and IDs match the owner’s expected properties; final listing contents, room inventory and current operator/listing consistency could not be inspected due to HTTP 403. The web tool also could not open these short links. Do not interpret a blocked response as proof of a dead link.
The owner authorized local integration after reviewing the matching redirect IDs and the final-listing retrieval limitation. Exactly one booking CTA per luxury property is now locally integrated, pending publication; this authorization does not establish live room availability, finalized commission attribution or completed bookings. No short URL is rewritten, expanded in markup or parameterized. Official editorial source links are not affiliate booking replacements.

## Commercial uncertainty and attribution

No owner dashboard, contract or commercial eligibility evidence was supplied with this implementation instruction. PR #24 is merged, but its inventory still records eligibility, live availability and actual SubID attribution as unverified. Merging does not itself establish those checks.
Before publication, the owner must confirm that the connected Travelpayouts Klook program permits commissioned hotel bookings and provide attribution evidence. Live booking availability, commission rates and actual SubID attribution remain UNVERIFIED for every inherited or new mapping.
Shared `trackAffiliateClicks` records program/destination after consent, not the anchor’s `data-subid`. Do not claim that the attribute itself sends attribution to Klook. No consent, GA4, booking or affiliate JavaScript is changed. Existing anchors and contracts everywhere else remain intact.
New placed anchors use native links, exact URL/SubID, `js-aff`, `data-aff="klook"`, `rel="nofollow sponsored noopener"`, `_blank`, hotel-specific accessible names and a preceding disclosure. There are eleven new placements (three cheap, four family, three luxury and one premium alternative): seven distinct inherited property mappings and three owner-generated luxury mappings.

## SEO, design and dates

One unique H1/title/description per page; self-canonical, matching en/x-default, OG URL and page-specific JSON-LD IDs. Breadcrumbs are Home → Hotels → Paris → guide. Graphs use Organization, WebSite, ImageObject, WebPage, Article and BreadcrumbList; no ratings, offers or review schema. Native visible FAQs are original; no copied FAQPage graph.
Visible review dates and schema dateModified reflect preparation on 2026-10-09. datePublished is deliberately omitted while unpublished; set it truthfully during a separately authorized publication review. New sitemap lastmod dates reflect content preparation, not a claim of deployment.
Reuse the established six CSS files in their existing order and `body.tg-ui` / `main.tg-main.tg-hotels`. No new CSS or JS. Cards use articles and H3s; comparisons retain native captions/headers and named focusable scrolling regions. The existing Paris city imagery is decorative and explicitly identified as illustrative city imagery, never a property photo.
Only three canonical entries are added to the Paris sitemap. Existing entries remain; only its child lastmod changes in the sitemap index.

## Broken-link and preservation checks

The six parent anchors at original lines 499, 509, 526, 1035, 1041 and 1047 now resolve to the three new routes without changing the parent HTML. Only their six corresponding historical `missing_internal_page` findings resolved in this implementation; the baseline and auditor remain unchanged.
All 27 protected cruise files and all integration files must match starting main. Preserve original Disney branch `design/disney-premium-pages`, HEAD `bce66a7f4aae7ae94a0fee5bfee369cbb85bd8e7`, unchanged status and hashes:

- Paris: `2DF604E7F1EA47C0964DC8D2C984A7AC76A52B66E3B134F7EE237F72CAE8EC44`
- Disneyland: `1D9060F3C70746E2C9CF0426DE9E86979096FDE382C9F91E8438ACEE7B6C56FD`
- Tokyo: `908051F1A38F1E7EC98C34BA5C67C6F98A2EABB7D27C8E5D6B977455D4530D43`
- Disney CSS: `DB4D20AEB6C5B40DF2CD6A797B24BCDB72415D1AA3FE19A23F33795E7AE44D5D`

## Validation record

Local validation, including the owner-approved three-CTA amendment, completed on 2026-10-09. All checks below were rerun after integration. Reports, executable helpers and 33 screenshots remain outside the repository in `C:/Users/1995/AppData/Local/Temp/tripguidely-subguides-qa`.

Exact workflow commands run against the recorded main:

```text
python -B scripts/audit-site.py --base-ref 66d813f83809ce227f99b7334016a40d30d2aa4d --self-test
python -B scripts/audit-site.py --base-ref 66d813f83809ce227f99b7334016a40d30d2aa4d
```

| Check | Actual result |
| --- | --- |
| Regression self-tests | 57/57 passed; exit 0 |
| Full site audit | Passed; exit 0; zero new regressions |
| Audit inventory | 136 HTML files, 1,319 affiliate anchors, 12 sitemap XML files |
| Historical findings | 971 on starting main to 965 now; six new resolutions, 48 cumulative resolutions including 42 prior resolutions |
| Remaining categories | 783 missing_asset, 101 missing_internal_page, 78 robots_syntax, one each canonical_route_review, empty_html_page and runtime_fragment_review |
| Missing asset inventory | 287 distinct paths, unchanged |
| Contracts and protection | All pre-existing affiliate and integration contracts preserved; all 27 protected cruise files unchanged; no baseline/auditor/authorization changes |
| Static structure | HTML parsed without errors; JSON-LD and both sitemap XML files valid; unique H1/title/description/IDs; correct canonical/hreflang/OG URLs, breadcrumb graph and dates |
| Routes and assets | All six parent destinations resolve; new internal routes/fragments and referenced image/srcset/preload paths exist |
| Affiliate markup | Eleven exact URL/SubID placements across seven inherited and three new luxury mappings; exactly one CTA per luxury property; required attributes and hotel-specific accessible names checked |
| CSS and scope | Established six-file CSS order; no CSS/JS changes; 176 other tracked text files preserved; exactly six approved changed paths, empty index |
| Diff hygiene | `git diff --check` passed |

The six resolved finding IDs are `missing_internal_page:15bb1b6d8cf36dbe435b`, `missing_internal_page:2f9be5f01c4a2a728277`, `missing_internal_page:5b34efe1b78644271bba`, `missing_internal_page:e741fb73088c7c48d1f2`, `missing_internal_page:e7da13bb2bc8a066e8d6` and `missing_internal_page:f7ed3f301c8a89f16aa1`. No other historical finding changed.

Headless Chrome 154.0.8037.98 loaded the actual shared scripts and partials. Each page passed at 320, 375, 390, 430, 768, 1024 and 1440 CSS pixels, then at those same seven widths with 200% root text. Native Chrome 200% and 400% zoom also passed on all three pages (effective CSS widths 631 and 315 pixels). No document/main/header overflow, JavaScript errors or failed local requests occurred. Tables intentionally scroll within bounded regions.

Keyboard checks passed for table scrolling, all 18 native FAQs, internal fragment activation, menu dismissal/focus restoration and consent accept/decline. All eleven affiliate buttons retained at least 44-by-44-pixel targets and visible keyboard outlines. Their native links opened exact short URLs in new tabs in intercepted local activation tests; external partner requests were intercepted, so this is clickability evidence, not live attribution. Reduced-motion scrolling, forced-colors focus and emulated touch table scrolling passed. Visual review covered desktop/mobile hero, cards and tables plus enlarged text and zoom screenshots; city imagery remained intact and captions explicit.

The shared header reflows onto two rows at 320px with 200% text; no clipping or document overflow was observed with the inherited PR #23 repairs. Browser tests do not establish screen-reader usability or physical-device behavior.

Evidence files: `static-report.json`, `self-tests.json`, `site-audit.json`, `site-audit.txt`, `preservation-report.json` and `browser-report.json`. The three page sets include desktop/mobile top, cards and table screenshots, 320px enlarged-text captures and native-zoom captures.

## Known limitations

Three new luxury CTAs locally integrated with owner approval, pending publication; final partner listings returned HTTP 403. Commission eligibility, availability, attribution and live GA4 delivery unverified. Firefox/Safari, assistive-technology review and physical-device testing pending. No Lighthouse/CWV claims. Reconfirm all current room rules at booking. The owner authorized commit, push and PR creation; do not publish or merge. Stop for human review after verifying GitHub Actions.
