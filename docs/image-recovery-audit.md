# Priority missing-image recovery review

This document records the bounded image-reference repair prepared for PR #18.
Publication and workflow results are reported in the pull request.

Audit and final local review date: **2026-10-08**, America/Toronto.

Starting main: `e8d2ca3efb4814023e9c43b866a36780e9dd027d`, the merge of PR #17.
Branch: `fix/priority-missing-images`.
Isolation: a separate Git worktree based on the starting main revision.
The original `design/disney-premium-pages` worktree remains separate.

## Inventory and ranking

[image-recovery-inventory.json](image-recovery-inventory.json) records all 293
original missing physical paths and all 807 individual placements, including
source page, line, original URL, locator, occurrence, and historical issue ID.
It also records image roles, template classification, source-declared aspect
ratios, display sizes, component attributes, and recommendations for all 133
HTML files. Ninety-one files originally had a missing image reference.
It is descriptive audit data, not a regression exception fixture or an
instruction to place images automatically.

The schema-version-1 JSON consolidates repeated page recommendation text in
`role_recommendation_defaults` and source measurements in `recovery_sources`.
Pages name their `recommendation_roles`; recovered entries use
`source_metadata_ref`. Omitted `component_optional_fields` mean the attribute
was undeclared, previously represented as null. The `serialization_contract`
documents these lookups. Rehydrating the compact data reproduces the complete
original inventory, including every placement and all page recommendations.
No useful source locations, URLs, dimensions, image roles, or license caveats
were removed. The audit date was added and the personal worktree path removed
during final documentation review; production changes were not expanded.

Coverage includes img/picture/source, src/srcset, preload candidates, CSS
background references, Open Graph, Twitter, JSON-LD, hero components,
destination cards, editorial images, maps, favicons, and shared branding.
The existing auditor found no missing CSS image placements or filename-case
errors. Referenced favicons exist and decode. Four YouTube thumbnail references
in JSON-LD are intentionally external; they are recorded separately, left
unchanged, and were not downloaded or verified over the network.

Classification: 287 paths lack a verified exact repository match; five are
unresolvable publisher-logo path variants whose actual brand artwork already
exists; one is a filename mismatch in an otherwise complete responsive family.
No historical rename was found for the five brand paths. Git history records
the existing Quebec filename as uploaded in commit `95814e2`, the 512px brand
icon in `38cc640`, and the header logo in `887763b`.

Ranking uses repository evidence only. No Search Console, traffic, impressions,
CTR, ranking, engagement, conversion, or revenue measurements were available
or invented. Tiers are: (1) above-the-fold heroes, (2) attraction editorial
imagery, (3) shared assets, (4) commercial editorial imagery, (5) social images,
and (6) other supporting imagery.

The reproducible score is `(7 - tier) * 10000`, plus 1000 for an attraction
template, 500 for exact verified reference recovery, 10 per referring page,
and `min(placements, 9)`. Lexical path order breaks ties. Scores are ordinal
triage, not estimates of commercial impact. Responsive variants are grouped
for the following top 20; individual paths remain separate in the JSON.
Selection additionally requires a verified source and compliance with protected
file scope. Higher-ranked deferred images are not filled with substitutes.

## Top 20 opportunities

| Rank | Image family or existing slot | Missing paths / placements | Score | Source or decision required |
| --- | --- | --- | --- | --- |
| 1 | Universal Orlando ticket hero | 4 / 10 | 61014 | Licensed, verified Orlando park skyline matching the current roller-coaster alt text. |
| 2 | Universal Studios Beijing ticket hero | 4 / 10 | 61014 | Verified Beijing globe entrance and park skyline photo. |
| 3 | Universal Studios Hollywood ticket hero | 4 / 10 | 61014 | Verified Hollywood park, rides, and themed-area view. |
| 4 | Universal Studios Japan ticket hero | 4 / 10 | 61014 | Verified Osaka entrance and park skyline photo. |
| 5 | Universal Studios Singapore ticket hero | 4 / 10 | 61014 | Verified Singapore lagoon and coaster skyline photo. |
| 6 | Quebec City car-rental hero | 1 / 3 | 60513 | Repaired using the exact existing 1600x900 variant. |
| 7 | Best cruises 2026 hero | 1 / 6 | 60016 | Protected cruise page: separate approval plus source/rights review. |
| 8 | Caribbean cruise hero | 1 / 6 | 60016 | Protected; licensed ship/port imagery verified as Caribbean. |
| 9 | Mediterranean cruise hero | 1 / 6 | 60016 | Protected; licensed ship/port imagery verified as Mediterranean. |
| 10 | Canada eSIM hero | 1 / 6 | 60016 | Licensed travel/connectivity scene; verify location if identifiable. |
| 11 | eSIM compatibility hero | 1 / 6 | 60016 | Authentic device photo or explicitly editorial compatibility diagram. |
| 12 | Europe eSIM hero | 1 / 6 | 60016 | Licensed European travel/connectivity scene; no fabricated provider UI. |
| 13 | Italy eSIM hero | 1 / 6 | 60016 | Authentic phone/eSIM setup photo matching existing alt text. |
| 14 | eSIM setup hero | 1 / 6 | 60016 | Authentic device photo or clearly labeled setup illustration. |
| 15 | UK eSIM hero | 1 / 6 | 60016 | Licensed UK travel/connectivity scene. |
| 16 | USA eSIM hero | 1 / 6 | 60016 | Authentic phone/eSIM setup photo matching existing alt text. |
| 17 | London car-rental hero | 1 / 6 | 60016 | Authentic London driving context; no invented rental service. |
| 18 | London transport hero | 4 / 13 | 60015 | Rights-cleared collage matching existing airport/Tube/river/bus alt text. |
| 19 | Bangkok 2-day itinerary hero | 4 / 11 | 60014 | Rights-cleared collage of the actual temples, skyline and river experiences named in alt text. |
| 20 | Bangkok 3-day itinerary hero | 4 / 12 | 60014 | Rights-cleared temple/market/skyline/river collage matching existing alt text. |

The named responsive hero families require the existing 800x450, 1200x675,
1600x900 and 2400x1350 slots: 16:9, without upscaling. Existing individual
Universal section photos are 1200x900; ticket-preview assets are not proof of
a matching photographic hero. They are not stretched, relabeled, or used to
depict another park. Original cruise, legacy eSIM, and London car-rental img
attributes declare 1920x900 (32:15); preserve those actual ratios rather than
blindly applying a universal 16:9 preset. Existing social slots generally
request 1200x630. Actual sizes and any absent sizes attributes are recorded
per page; no new responsive-layout assumptions are introduced here.

## Six-path first batch

All paths below are relative to the repository root. Recovery changes URLs in
existing HTML; it does not create six new bitmap files. Twenty-four placements
now resolve to three existing sources. No aliases or duplicate images were added.

| Missing path | Existing source used | Placements |
| --- | --- | --- |
| `assets/images/hero/quebec-car-rental-1600x900.webp` | `assets/images/hero/quebec-car-rental1600x900.webp` | 3 |
| `assets/images/brand/tripguidely-logo-512.png` | `android-chrome-512x512.png` | 13 |
| `assets/images/branding/logo-512.png` | `android-chrome-512x512.png` | 1 |
| `assets/images/brand/tripguidely-logo.png` | `assets/images/tg-logo.png` | 4 |
| `assets/images/branding/tripguidely-logo.png` | `assets/images/tg-logo.png` | 1 |
| `assets/images/logos/tripguidely-logo.png` | `assets/images/tg-logo.png` | 2 |

The 512px source is the existing TripGuidely webmanifest icon. The 256px source
is the existing header logo. Both were visually inspected and preserve PNG
transparency. Schema fields declaring 512x512 keep those exact dimensions and
reference the existing 512x512 asset. Other publisher-logo objects have no
declared dimensions and reference the existing 256x256 asset. Publisher identity,
article semantics, and all other JSON-LD fields remain unchanged.

The Quebec photo was compared visually across all four variants: the same
winter SUV and frozen-waterfall composition. This does not verify the real
location, rental operator, original capture, or photographic authenticity.
It is the existing variant of the same image already used in that component,
not a newly sourced or generated depiction. The existing decorative empty alt
and aria-hidden wrapper remain appropriate and unchanged. Preload href, img
src and the 1600w srcset candidate now use the filename actually present.
The 1600x900 dimensions, sizes=100vw, eager loading, high fetchpriority, and
the other three candidates remain unchanged.

No explicit image source/license register or credit record was found.
Existing site branding is reused in its existing publisher role; the existing
photo's unrecorded provenance is preserved, not represented as verified licensed
photography. No third-party image was acquired, no attribution was removed,
and no paid service or image-generation tool was used. The remaining factual
heroes, Disney destination-card photos, social crops and missing Beijing map
need authentic sources or verified map rights before further implementation.

| Existing source | Format and intrinsic size | Existing bytes | Treatment |
| --- | --- | --- | --- |
| Quebec 1600 variant | WebP RGB, 1600x900 | 548556 | Unchanged bytes; exact filename repair. |
| Header logo | PNG RGBA, 256x256 | 90671 | Unchanged bytes; no upscaling. |
| Manifest icon | PNG RGBA, 512x512 | 261279 | Unchanged bytes; no upscaling. |

No conversion, crop, recompression, new format, or new image data is necessary
for this batch. Existing file sizes are measurements, not optimization targets
already met. The relatively large Quebec image and brand PNGs can be evaluated
in a separate quality-controlled optimization pass with suitable originals and
measured quality/rendering checks. This repair adds/removes zero image bytes.

## Exact implementation scope

Only the three Quebec references and 21 publisher-logo URL strings change in
production. These are the exact 22 modified HTML paths:

```text
car-rental/quebec-city/index.html
contact/index.html
hotels/new-york/index.html
hotels/paris/index.html
things-to-do/bangkok/index.html
things-to-do/dubai/aquaventure-waterpark/index.html
things-to-do/dubai/burj-khalifa/index.html
things-to-do/dubai/desert-safari/index.html
things-to-do/dubai/dubai-aquarium/index.html
things-to-do/dubai/dubai-fountain/index.html
things-to-do/dubai/index.html
things-to-do/index.html
things-to-do/las-vegas/index.html
things-to-do/london/harry-potter/index.html
things-to-do/london/index.html
things-to-do/new-york/index.html
things-to-do/paris/index.html
things-to-do/quebec-city/index.html
things-to-do/rome/index.html
things-to-do/switzerland/swiss-travel-pass/index.html
things-to-do/tokyo/index.html
transport/paris/index.html
```

Two documentation additions: this report and `docs/image-recovery-inventory.json`.
Production diff: 24 insertions and 24 deletions; normalized Git text byte delta
is -354. Image binary delta is zero. Documentation sizes are recorded in the
pull request; both documentation files use repository-relative file paths.

## Local verification

| Observation | Current main before | Proposed tree after |
| --- | --- | --- |
| Missing physical image paths | 293 | 287 |
| Missing image placements | 807 | 783 |
| Missing WebP paths | 278 | 277 |
| Missing JPG paths | 10 | 10 |
| Missing PNG paths | 5 | 0 |
| Remaining historical findings | 995 | 971 |
| Resolved historical findings, including PR17 | 18 | 42 |
| Newly resolved in this batch | 0 | 24 |
| New regressions | 0 | 0 |

Python 3.12.10: all 57 existing self-tests pass. Six independent in-memory
reintroduction tests pass, one per repaired missing path, covering every one
of the 24 historical placements. Restoring an old reference against the repaired
tree fails despite the unchanged historical fixture.

The full regression auditor passes and validates the historical fixture from
its original Git source. All 343 tracked raster images decode with Pillow
12.3.0 installed only in Temp; the existing SVG also parses. Replacement files
exist, source hashes and intrinsic dimensions are recorded in the inventory,
and all Quebec srcset width descriptors match decoded candidate widths.
Image bytes remain unchanged. JSON-LD parses and the exact HTML diff matches
only the approved URL replacements. Titles, descriptions, canonicals,
OG/Twitter and hreflang metadata, heading structure, layout markup, alt text,
navigation, editorial text, scripts, widgets, and disclosures remain unchanged.

All 1,301 affiliate anchors and tracking contracts, six affiliate forms,
25 widgets, 275 integration-markup units, 346 disclosures, and four shared
JavaScript file hashes match main. All 27 protected cruise file hashes match.
All 12 sitemap files are unchanged and parse; sitemap coverage/duplicates remain
fixed. The 107 historical broken internal-page placements are unchanged.
The auditor, historical fixture, workflow, and all CSS remain unchanged.
No browser visual QA, Lighthouse/CWV measurement, external XSD, image rights
verification, ticket/product verification, or remote workflow run is claimed.

## Future image-agent requirements

Use the page records as source facts, not a request to insert decorations.
They identify template, existing/missing roles, declared aspect ratios and
display sizes, original component attributes, and the existing slots to repair.
Repair missing components before considering new locations. New opportunities
and automated placement must wait for the shared design system and separate
review; image-free sections remain unchanged in this batch.

Before publishing new assets, require a registry with original source/asset,
creator, license and permitted use, attribution, location/subject verification,
native dimensions, source hash, crop/derivative history, and reviewer decision.
Keep licensing/authenticity status distinct from filename similarity. Preserve
attribution and alpha; do not upscale, disguise a screenshot as a photo, reuse
one city's imagery for another, invent factual attraction photography, or
automatically purchase/generate assets.

Choose crops and widths from real containers and their declared sizes, retaining
aspect ratio and intrinsic dimensions to avoid layout shift. Keep the primary
LCP hero eager/high-priority where appropriate; retain lazy loading for existing
below-fold images. The existing 4:3 cards, 16:9 hero families, 32:15 legacy
heroes and 1200:630 social crops need separate treatment. Use transparent PNG
for existing brand marks and WebP for photographic derivatives when justified;
evaluate AVIF only after pipeline/browser support and measured quality checks.

Clearly editorial, non-photographic diagrams may suit eSIM setup/compatibility
or general planning after explicit editorial review. They must not fabricate
provider interfaces or stand in for factual landmark photographs. Maps require
verified geography and rights. No illustration was generated in this batch.

Protected cruise work needs separate authorization. Any future social-image
URL edit must also satisfy the existing metadata contract; this batch does not
alter contracts, admit new baseline exceptions, or weaken the auditor.
The outstanding source/rights decisions, 287 remaining paths, unrecorded
photo provenance, and unmeasured visual/performance behavior remain explicit
review items. Stop here for human review.
