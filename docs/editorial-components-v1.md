# TripGuidely editorial components v1: Paris two-day pilot

Review date: 2026-10-09, America/Toronto.
Starting main: `e00299954b4395c6fcdad4ac12ca306eae963636` (PR #21 merged).
Branch: `design/editorial-components-v1`.
Isolated worktree: `C:/Users/1995/AppData/Local/Temp/tripguidely-editorial-components-v1`.
Implementation and local validation only; stop for human review before staging,
commit, push, or PR creation. No production deployment is part of this work.

## Scope and dependency map

Only `itinerary/paris/2-days/index.html` opts in. Added CSS is not imported by the
global stylesheets. No existing CSS, JavaScript, partial, image, audit, baseline,
workflow, sitemap, or other guide is modified.

| Existing dependency | Preserved behavior / adapter |
| --- | --- |
| `styles.css` | Reset, box sizing, safe areas, skip link, shared header/footer, menu, consent, and legacy component definitions remain. Its overflow guards are not evidence of successful reflow; QA checks descendant bounds too. |
| `itinerary.css` | Preserves `data-page="itinerary"`. Legacy hero classes are replaced on this page to avoid their high-specificity image overlays, glass buttons, and fixed minimum heights. Existing image containers remain. |
| `tokens.css`, `foundation.css` | Reuse semantic ink/ocean/sand/white, type, spacing, focus, grid, and size tokens; `.tg-main`, `.tg-container`, `.tg-card`, `.tg-callout`, `.tg-button`, and `.tg-breadcrumbs`. No parallel palette or legacy variable writes. |
| Hero image | Existing decorative `picture` with four WebP candidates, `sizes="100vw"`, 1600x900 fallback, eager/high priority and async decoding. Render the full 16:9 collage, without cropping or text over it. No preload is added. |
| Contents / fragments | `#main`, `#breadcrumbs`, `#toc`, `#summary`, `#quick-book`, `#plan`, `#day1`, `#day2`, `#tickets`, `#soldout`, `#rules`, `#sources`, `#faq`, and mounting IDs stay unchanged. |
| Day structure | Original Day 1 then Day 2, each with four stops and its existing booking group. New named section wrappers reference the existing H3 IDs. The optional upgrade remains after Day 2. |
| Booking | Eleven existing affiliate anchors, including repeated placements. Opening tags, labels, hrefs, rel/target and all tracking attributes are untouched. No new provider, widget, or integration. |
| FAQs | Three existing native details/summary pairs; wording and markup untouched. Restore native disclosure markers through scoped CSS. |
| Related guides | Five existing links, descriptions and tags; use a flexible card grid without new links or recommendations. |
| `site.js` | Keep header/footer mounts, page classification, outbound consent/tracking hooks, mobile burger/drawer, footer privacy controls, and fragment handler. Its explicit header-offset smooth scroll is unchanged. |
| Head metadata | Entire original title, meta, canonical/hreflang, OG/Twitter, verification script and both JSON-LD scripts remain. Four stylesheet links are the only head additions. |

There are no comparison tables, attraction photographs, booking widgets, or
separate attraction-card sections on this pilot. Do not manufacture them to
complete a component checklist. Comparison/table components remain future work.

## Implemented components and conventions

| Component | Classes / purpose |
| --- | --- |
| Guide shell / hero | `.tg-guide`, `.tg-guide-hero`, `.tg-guide-layout`: type defaults, content width, introductory text and intact collage. `.tg-guide-intro` identifies the existing copy wrapper. |
| Section heading | `.tg-guide-heading`: serif H2 plus existing subtitle, vertically grouped rather than squeezed into a horizontal title row. |
| Contents | `.tg-guide-toc`: compact, non-sticky fragment-link grid. |
| Overview | `.tg-guide-summary`: warm sand route summary, two columns when the actual container fits. |
| Editorial section | `.tg-guide-section`: open reading sections with restrained rules and consistent vertical rhythm. |
| Lists / links | `.tg-guide-checklist`, `.tg-guide-links`: readable bullet lists and contextual link groups, including existing booking anchors. |
| Day / stop | `.tg-guide-day`, `.tg-guide-stops`, `.tg-guide-stop`: named day panels and chronological timelines using original stage labels. |
| Tip / optional offer | `.tg-guide-tip` extends foundation callouts; `.tg-guide-offer` frames only the existing dinner-cruise upgrade. |
| FAQ | `.tg-guide-faq`: native disclosures, visible markers, minimum summary target size. |
| Related guides | `.tg-guide-related`, `.tg-guide-related-grid`, `.tg-guide-related-link`: existing guide cards with underlined titles and flexible columns. |

All new design selectors start with `.tg-ui` or `body.tg-ui`. Native elements
are targeted inside owned components, never as new global rules. The one scoped
ID adapter, `.tg-ui .tg-guide #toc`, defeats the legacy itinerary sticky ID rule
while preserving its public fragment. No new `!important`, reset, cascade layer,
global import, third-party font, JavaScript, or animation.

## CSS load order and legacy boundaries

1. `/assets/css/styles.css`
2. `/assets/css/itinerary.css`
3. `/assets/css/tokens.css`
4. `/assets/css/foundation.css`
5. `/assets/css/components/editorial.css`
6. `/assets/css/templates/guide.css`

Legacy styles are unlayered; this bounded pilot uses explicit order and component
specificity. `editorial.css` holds reusable content components; `guide.css` owns
the guide shell, image/intro arrangement and scoped legacy adapters. No changes
to shared navigation, footer, consent, or the About pilot are necessary.

Retain `.checklist` for its decorative positioned bullets and `.pill-link` on
existing anchors. New list/group classes replace their presentation locally.
Preserve inline margins already present in the page. The final affiliate
disclosure section is styled through its existing aria-label; its protected
HTML and disclosure paragraph are not edited.

## Responsive and semantic requirements

The reading container reuses the foundation's 52rem cap, including gutters;
paragraphs have a 68ch maximum. Heading sizes and spacing are fluid. Grids use
`auto-fit` and minima bounded by 100% of the available container. At 64rem viewport
width the hero can place the text and complete landscape image side by side;
below that it stacks the existing image before the copy. The literal breakpoint
is justified by those two columns and leaves the shared 760px menu boundary alone.
No fixed-height text boxes, viewport-height empty heroes, or horizontal clipping
are introduced. No sticky guide component obscures anchor destinations.

Preserve main, heading levels, breadcrumb/section names and document reading
order. List-style-free checklists/timelines retain explicit `role="list"`.
Day sections reference their own H3s. Bookings remain anchors, state changes
remain native buttons, and FAQs remain native details/summary. Never add
clickable-card scripts, positive tabindex, faux accordion roles, or duplicate
accessible labels.

Guide links and summaries reuse a 3px ocean focus outline with 3px offset and a
`:focus` fallback. Booking groups and summaries have at least a 2.75rem target
height; inline source links keep natural sizing. Informational links are
underlined, including related-card titles. New transitions are color-only and
disabled under reduced motion. Forced colors keep automatic color adaptation,
system control borders and Highlight focus outlines.

## Image Agent requirements

This migration preserves every image attribute and source. No images are
generated, downloaded, renamed or replaced. This pilot has one decorative hero
picture and no article-stop photographs; do not add slots merely to satisfy a
photo count. Preserve the existing collage's location/subject description and
do not infer provenance or documentary authenticity from its filename.

Keep the entire native 16:9 collage visible with intrinsic width/height, normal
flow and a reserved aspect ratio. Existing source candidates, `sizes`, alt,
loading, decoding and fetch priority take precedence over proposed new defaults.
The existing `100vw` sizes expression intentionally remains even when the image
column is narrower; a measured image-delivery optimization needs separate review.
Do not stretch, crop important landmarks, or place illegible text over the image.

For future article imagery require verified subject/location, source, creator,
license, credit, native dimensions, hash and reviewed derivatives/focal point.
Use figure/img/figcaption where imagery explains prose, retain meaningful alt and
attribution, reserve the actual ratio, and lazy-load only appropriate below-fold
assets. No factual-location synthetic photography or unverified substitutions.
Consult `docs/design-system-v1.md` for the wider source and Image Agent contract.

## Safe migration procedure

1. Isolate from reviewed main; record the base and preserve unpublished work.
2. Inventory text, IDs, metadata/schema, images, links, affiliate/disclosure
   contracts, scripts and specialized CSS. Capture the original rendered page.
3. Add `tg-ui` without replacing `data-page`; load all six styles in the order
   above. Migrate only markup with a demonstrated component use case.
4. Keep affiliate opening tags and disclosures untouched. Style through wrappers
   so a design migration does not require new baseline authorizations.
5. Preserve complete original text, FAQ markup, all URLs, source sets and anchors;
   inspect link targets and keyboard behavior after restructuring.
6. Check syntax, token scope, browser reflow/isolation, all protected contracts,
   full audit, self-tests and exact file scope. Leave the index empty for review.

## Local QA results

The full audit passes against the recorded starting main: 971 known historical
findings, 42 cumulative resolved, zero new regressions; 287 distinct missing
asset paths / 783 missing placements remain visible. No fixture regeneration or
exception edits. Both audit commands use the exact recorded main SHA:

```text
python -B scripts/audit-site.py --base-ref e00299954b4395c6fcdad4ac12ca306eae963636
python -B scripts/audit-site.py --base-ref e00299954b4395c6fcdad4ac12ca306eae963636 --self-test
```

| Check | Observed result |
| --- | --- |
| Audit | PASS, exit 0, zero regressions. Historical findings unchanged from main. |
| Self-tests | All 57 existing self-tests pass, exit 0. No test/auditor changes. |
| CSS | CSS Tree 3.2.1: zero syntax/property errors; every new selector scoped; all referenced design tokens resolve; no new important declarations or legacy variable writes. |
| HTML / schema | Parse5: zero HTML5 parse errors. Both JSON-LD scripts parse and remain byte-identical. One H1, ten H2s, three H3s; no skipped heading levels. All 15 static IDs unchanged and unique. |
| Content / links | Exact main text after whitespace normalization; all 42 anchor destinations, attributes other than non-affiliate visual classes, labels, and sequence preserved. All existing local/fragment targets resolve. Metadata, dates, all three FAQ disclosures, and disclosure contracts unchanged. |
| Affiliates | All 11 pilot opening tags byte-identical. All site contracts identical, including 1,301 affiliate anchors, integration markup, disclosures and shared JavaScript. No baseline authorization needed. |
| Images | Original picture, source and img markup byte-identical: alt, dimensions, srcset, sizes, loading, decoding and priority. Loaded image stays 16:9 at every tested width. All existing image files unchanged. |
| Browser | Isolated headless Chrome 154.0.8037.98 on Windows; local HTTP server, real shared JS/partials. External requests blocked, analytics consent declined. Zero JS errors or failed local requests. |
| Widths | 320, 375, 390, 430, 768, 1024, 1440 CSS px. Zero document/main-descendant/internal overflow at default text size. Full-page screenshots at every width. |
| Enlarged text | 200% root-font simulation at all seven widths: zero main or internal overflow. Native browser-menu zoom is not claimed. |
| Non-opt-in control | Original Paris markup with all four added stylesheet links but without tg-ui: no new matching selectors; rendered style/geometry identical at all seven widths. Responsive-image naturalWidth is excluded from geometry equality because browsers update its density correction asynchronously; original responsive inputs are independently byte-checked. |
| Shared UI | Injected header/footer DOM and sampled descendant computed styles/dimensions match main at all seven widths. Mobile menu opens and closes with Escape; footer consent opens and decline operates. |
| Keyboard | All 45 guide/skip targets reached with Tab, with visible 3px ocean focus and 3px offset. All three native FAQs open with Enter and close with Space. |
| Fragment navigation | 18 rendered checks: seven contents links and both direct day fragments at 390/1440px. Destinations remain visible; contents block is static. |
| Actions / contrast | Primary/secondary hero and booking-link samples, default/hover/pressed: minimum 5.55:1 measured text contrast and at least 44px height. No translation/scale motion on new links. |
| Reduced motion / forced colors | Sampled new link transition 0s; inherited CSS scroll behavior auto under reduced motion. Forced-colors retains automatic adaptation and 3px system focus. Shared JS still explicitly requests smooth fragment scrolling; it is preserved, not certified as preference-aware. |
| Cruise / protected files | All 27 cruise hashes and all protected site contracts identical. All existing public files except the pilot are unchanged. |
| Disney | Original branch design/disney-premium-pages and HEAD bce66a7 preserved. All four original edited-file SHA-256 hashes match the starting snapshot. |
| Whitespace / scope | git diff --check passes. Exactly three new files plus one modified pilot. Index empty; HEAD still starting main. No staging, commit, push, PR or merge. |

New authored CSS: `components/editorial.css` 6,374 bytes;
`templates/guide.css` 5,175 bytes; total 11,549 uncompressed bytes. The pilot adds
four synchronous stylesheet requests (two established foundation files plus two
new files) after its two existing stylesheets. No new tooling is added to the repo.

QA scripts, reports and screenshots live outside the repository in the temporary
`C:/Users/1995/AppData/Local/Temp/tripguidely-editorial-qa` directory. Review:

- `before-390-top.png`, `after-390-top.png`, `before-1440-top.png`,
  `after-1440-top.png` for the required visual comparison.
- `before-{width}.png` and `after-{width}.png` for all seven complete pages.
- `after-{390|1440}-{summary|day1|faq|related|footer}.png` for detail captures.
- `after-text-200-{320|390|1440}.png`, `before-text-200-320-top.png`,
  `after-text-200-320-top.png`, `after-keyboard-faq.png`,
  `after-forced-colors-faq.png`, `after-consent.png`, and `after-mobile-menu.png`.
- `browser-report.json`, `static-report.json`, `preservation-report.json` for
  measured outputs. No Lighthouse score or deployment result is fabricated.

## Known issues and next rollout

No table scrolling result is claimed because no table exists on this pilot.
The inherited shared-header issue is reproduced at 320px with 200% root text:
the menu button spans x=307.19 to x=339.19px and is partly clipped. Before/after
brand and button geometry is identical. It requires a separate shared-navigation
review; do not widen this pilot to fix it. Shared JS's explicit smooth scroll
also remains a separate reduced-motion follow-up.

Preserve historical content inconsistencies, including the existing shorthand
"one anchor per day" alongside the Day 1 Louvre/Eiffel sequence, for a separately
authorized editorial review. No facts or recommendations are added here.

Cross-browser review, actual assistive-technology review, native browser-menu
zoom and Lighthouse/Core Web Vitals measurement are not implied by headless
Chrome and root-font enlargement checks. External affiliate destinations and
third-party tracking are not exercised during local QA.

After this pilot is reviewed, migrate the Paris three-day guide in a separate,
equally bounded change with its own image, affiliate and specialized CSS audit.
Reuse heading/day/tip/link/FAQ components; implement tables or photo-stop cards
only on a page with real content needing them. Keep shared navigation repairs
separate from this component rollout.
