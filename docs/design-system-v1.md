# TripGuidely design system v1: foundation and About pilot

Implementation review date: 2026-10-08, America/Toronto.
Starting main: `510c9c00f9d8c3bc19ace3d0807b365277d38b1a`, the merge of PR #18.
Branch: `design/global-foundation-v1`, in a separate worktree.
This is an implementation for human review, not a published sitewide redesign.

Only `about/index.html` opts in. The two new stylesheets are not loaded by other
pages. Existing stylesheets, partials, scripts, images, metadata, sitemaps,
regression infrastructure, cruise files and unpublished Disney work are preserved.

## Existing design and scope

The review covered `styles.css`, `attractions.css`, `attractionsv2.css`, `home.css`,
`hotels.css`, `itinerary.css`, `transport.css`, and relevant car-rental, contact
and travel-guide styles. The shared header/footer and `site.js` were also reviewed.
Preserve the recognizable TG logo, turquoise family, practical editorial voice,
system-font body, existing navigation and visible affiliate explanations.

| Existing system | Dependency retained |
| --- | --- |
| `styles.css` | Global reset, system font, safe-area padding, skip link, partial navigation, consent UI, legacy components and footer. Uses unprefixed variables such as `--text`, `--max`, `--gutter`, `--radius`. |
| Attractions v1/v2 | `body[data-page^="attractions-"]`, themed palettes and specialized ticket layouts. No Universal or Disney migration. |
| Home | `body[data-page="home"]`, booking forms and home-specific tokens. |
| Hotels | Legacy pill/table components and guide hero dependencies. |
| Itinerary | `body[data-page="itinerary"]`, 74ch reading measure, sticky contents and image heroes. |
| Transport | `body[data-page="transport-hub"]`, search tabs, forms and responsive regional grids. |
| Shared JavaScript | `data-page`, `#site-header`, `#site-footer`, `#lastUpdated`, `.burger`, consent hooks and affiliate attributes. |

Legacy breakpoints vary by page (560, 760, 860, 900, 980, 1100, 1180 and 1200px
among those reviewed). The global navigation changes at 760px. This pilot retains
that behavior and uses intrinsic layout for its content instead of duplicating
all historical breakpoint rules. There are no copied booking widgets or broad
overrides of `.card`, `.wrap`, `.btn`, `.mini`, `.content` or legacy variables.

## A. Brand direction

A quiet travel editorial surface, strong ink typography, ocean actions and warm
sand callouts. The serif display title adds an editorial identity; the familiar
system sans-serif keeps long copy and UI readable. Existing TG artwork and shared
navigation remain recognizable. No new photography, fake credentials, reviews,
partner claims, gradients, glass panels or motion-heavy decoration are introduced.

## B. Palette and contrast

Brand primitives are separate from semantic foreground, surface, action, border
and focus tokens. `tokens.css` declares them only on `.tg-ui`; it does not change
`:root` or map onto legacy names.

| Semantic use | Value |
| --- | --- |
| Ink / text | `#12243A` |
| Ocean / action and focus | `#0B7478` |
| Sand / callout surface | `#F3EEE4` |
| White / cards and secondary controls | `#FFFFFF` |
| Page surface | `#FAF8F3` |
| Muted text | `#475569` |
| Decorative border | `#D9DEDC` |
| Strong control border | `#798A89` |
| Action hover | `#085C60` |
| Action active | `#06484C` |
| Gold primitive, reserved | `#BD9353` |

Calculated sRGB relative-luminance contrast, shown rounded for reporting:

| Foreground / background | Ratio | Implemented use |
| --- | --- | --- |
| Ink / page | 14.77:1 | Heading and body text. |
| Ink / white | 15.68:1 | Step-card titles and disclaimer. |
| Ink / sand | 13.56:1 | Promise and step number. |
| Muted / page | 7.14:1 | Date and breadcrumbs. |
| Muted / white | 7.58:1 | Step descriptions. |
| Ocean / page | 5.23:1 | Underlined inline links and focus outline. |
| Ocean / white (or white / ocean) | 5.55:1 | Secondary label/border and primary label. |
| Ocean / sand | 4.80:1 | Callout accent and focus against sand. |
| White / hover | 7.75:1 | Both button hover states. |
| White / active | 10.30:1 | Both pressed states. |
| Strong border / white | 3.61:1 | Disclaimer control boundary. |
| Gold / white | 2.81:1 | Not used for text, focus, controls or information. |

Text checks use a 4.5:1 minimum without rounding at the pass boundary; control and
focus boundaries use 3:1. Decorative separators do not identify controls and need
not carry the strong-border color. Never assume an arbitrary new background is
covered by this table. Recheck the actual foreground, background and state.
References: [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
and [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
These checks do not establish whole-site WCAG conformance.

## C. Typography

No external font requests. `--tg-font-body` uses local system sans-serif fonts;
`--tg-font-display` uses Georgia with Times New Roman/serif fallback for the H1.
The body token is 1.0625rem, small text 0.9375rem, lead 1.125–1.25rem, section
headings 1.375–1.625rem and title 2.25–3.5rem. Fluid sizes combine rem and viewport
terms; minimums remain relative to the reader's font settings.

Body line height is 1.75; UI is 1.5; headings are 1.15. Heading balance is a
progressive enhancement, with normal wrapping when unsupported. One existing H1
and all six H2 labels are preserved. No headings are selected outside `.tg-prose`.
Bold remains emphasis, not a fabricated qualification. Prose is capped at 68ch.

## D. Spacing

The eight `--tg-space-*` steps are 0.25, 0.5, 0.75, 1, 1.5, 2, 3 and 4rem.
Section padding is fluid from 2 to 3rem. Paragraph spacing, section boundaries,
card padding and focus clearances serve reading and grouping. Do not use fixed
heights for editorial content. Do not add an empty block to compensate for CSS.

## E. Containers and grids

`.tg-container` is full width with a 70rem maximum and fluid 1–2rem gutters.
`.tg-container--reading` caps the About pilot at 52rem including gutters.
`.tg-prose` controls line length and wraps unusually long text/URLs.
`.tg-grid` uses `auto-fit` with an 18rem preferred card minimum, bounded by 100%
of the available width. Its children can shrink without forcing overflow.
The About steps use two columns when they fit and one otherwise. No sidebar,
fixed card width, hard-coded column count or new sitewide breakpoint is required.

## F. Buttons

Implemented `.tg-button`, `.tg-button--primary` and `.tg-button--secondary` style
existing Contact-page and email anchors. Their hrefs and labels are preserved;
the About pilot has no booking CTA. They remain links, without `role="button"`.
Use native buttons for state changes in future components.

The primary is ocean with white text; the secondary is white with ocean text and
border. Both hover to dark ocean and press to a darker ocean. Minimum block size
is 2.75rem (44px at the default root size), text can wrap and maximum width is
100%. There is no scale/translate effect. Transitions cover only background/color
and are disabled under reduced motion. Native disabled/loading controls are not
implemented or implied; a future form pilot must define and test those states.

## G. Cards

`.tg-card` has a white surface, 1px decorative border, 0.75rem radius, fluid 1–1.5rem
padding and a restrained shadow. Only the four existing guide-building steps use
cards here. `.tg-step`, `.tg-step-number` and `.tg-step-copy` are a small adapter
for their existing content. The group is an ordered list with explicit list
semantics; visible number badges are hidden from assistive technology to avoid
duplicating the list numbering. The step row wraps its copy beneath the number
when enlarged text or a narrow container leaves too little reading width; the
copy has an 11rem preferred flex basis and can occupy the full row. No whole-card
link or clickable-card script.

## H. Callouts

`.tg-callout` holds the existing promise on sand with an ocean leading border.
It is ordinary editorial content, not an alert/live region or extra trust claim.
`.tg-disclosure` preserves the existing Quick disclaimer as native details/summary
with a visible browser marker and a strong control border. No accordion library.

## I. Accessibility

Named sections reference their own H2 IDs. The existing skip link, main landmark,
header/footer mounting slots and shared JavaScript remain. The root class is
additive to the existing `data-page="about"` hook. Underlined prose links do not
depend on color alone. Main-content links, summary and skip link receive a 3px
ocean `:focus-visible` outline with a 3px offset; a matching `:focus` fallback also
preserves contrast for pointer focus and older browsers. There is no `outline: none`,
focus clipping, new positive tabindex or invented ARIA widget behavior.

The inherited global reset supplies box sizing and safe-area padding. New content
rules supply wrapping, rem-based dimensions and no fixed text-height assumptions.
Reduced motion disables new transitions; increased-contrast preference strengthens
decorative boundaries. Forced-colors mode retains native color adjustment and
uses system ButtonText/Highlight for control borders/focus. Do not set
`forced-color-adjust: none` on editorial UI.

Inline text links retain their natural inline target sizing; the two actions and
summary get explicit target sizing. See [W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
and [reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).
Shared legacy navigation and consent need their own accessibility review; this
foundation does not certify them or silently restyle them.

## J. Responsive behavior

Responsive rules are intrinsic: clamp-based type/gutters/section spacing,
auto-fitting cards, flexible controls and natural document flow. Tokens cannot
be used as custom properties inside media-query conditions; future fixed
breakpoints must be documented literal values justified by the component.
Respect the existing 760px navigation boundary until a separate shared-nav PR.

Required review widths are 320, 375, 390, 430, 768, 1024 and 1440 CSS pixels.
Also review enlarged text, keyboard reachability, long labels and forced colors.
Do not hide overflow to conceal a new layout defect; the legacy global stylesheet
already has overflow guards, so inspect descendant bounds as well as scrollWidth.

## K. Image specifications (future, not implemented CSS)

No image count requirement and no automatic insertion. First repair existing
slots with verified sources. These are starting specifications for new components;
existing declared ratios and `sizes` take precedence until a reviewed migration.

| Role | Recommended ratio / candidate widths | Display and loading |
| --- | --- | --- |
| Editorial hero | 16:9; 800, 1200, 1600, 2400px where the original supports them. Preserve legacy 1920x900 / 32:15 heroes. | Size to its actual container; eager and high fetchpriority only for the real LCP hero. Preload only a measured useful candidate with matching imagesrcset/imagesizes. |
| Destination card | 4:3; 400, 640, 800px according to rendered card width/DPR. | Grid container width; normally lazy below the fold. No forced lazy loading on an above-fold LCP candidate. |
| Attraction photograph | Preserve original framing; usually 4:3 or 3:2; 640, 960, 1200, 1600px if supported. | Within the reading container; optional reviewed wide figure. Preserve important landmarks and captions. |
| Article section image | Usually native 3:2 or 4:3; 480, 800, 1200px. | Prose measure; lazy below the fold, decoding async. Add only when it explains the adjacent content. |
| Comparison visual | Match information density, not a fixed photo preset; typically 4:3 or 16:9. | Use accessible HTML tables/text when the information is data. For a diagram, provide equivalent text and retain readable labels at mobile size. |
| Social preview | 1200x630 (about 1.91:1), separate reviewed crop. | OG/Twitter metadata, no invented alt description. Metadata changes require separate contract review. No loading-priority attribute applies to a metadata URL. |

Candidate sets are ceilings, not instructions to upscale a small source or ship
every size. Use actual native dimensions and decode-check each derivative. Choose
`sizes` from real container behavior: for this reading container a future full-width
figure would need to account for the 52rem cap and two fluid gutters, not use an
unconditional `100vw` at desktop. Verify the final expression in the browser.
Wider templates need their own measured expression and card breakpoints.

Supply width/height matching the intrinsic ratio and reserve layout space before
load. Photo crops may use object-fit cover only after approving the crop; record
a subject focal point rather than centering every landmark blindly. Maps,
screenshots, brand artwork and informational diagrams generally need contain or
natural sizing. Never cut essential text, invent map geography or relabel a city.

Use a semantic figure/img/figcaption for explanatory imagery. Captions carry
context and credits when required. Alt describes the image's purpose and relevant
subject; decorative images use empty alt. Do not repeat the full caption, stuff
keywords or describe unverified details. Linked images need an accessible link
name. A text equivalent is required for nontrivial visual comparisons.

Photographic derivatives normally favor WebP; preserve alpha for existing PNG
brand marks. AVIF is a future pipeline decision with measured quality/support,
not a new format added by this PR. Record sizes and quality results; there is no
unverified performance score or arbitrary universal byte budget.

## L. Naming conventions

All new custom properties use `--tg-*`. Foundation classes use `tg-` with `--`
modifiers. The opt-in root is `.tg-ui`. Every rule in both files starts with that
scope (the body background uses `body.tg-ui`). Native elements are selected only
inside a component or the opted-in main. No `!important`, framework reset or
generic unscoped heading/link/button selector is introduced.

Implemented: container/reading modifier, prose, section, grid, card, step adapter,
callout, two button variants, disclosure, intro/meta/lead and breadcrumbs.
Planned only: booking forms, image components, comparison component, navigation
migration, theme selector and general stack utility. Do not add unused APIs just
because another framework has them.

## M. CSS layering and load order

The About head loads synchronously in this order:

1. Existing `/assets/css/styles.css`.
2. New `/assets/css/tokens.css`.
3. New `/assets/css/foundation.css`.

The legacy stylesheet is unlayered. Introducing an `@layer` only for the new CSS
would place it below unlayered legacy rules for normal declarations; therefore
this pilot uses explicit load order and scoped specificity, without `!important`.
Do not import these files into global styles. Specialized page styles remain
unchanged and are not loaded on About. Future migration must inspect their
specificity before choosing its load order; the About order is not automatic
permission to override every template.

Only the body page background and opted-in content use the new visual defaults.
Body font/color and legacy custom properties are not overwritten. Shared partials
and consent continue using legacy selectors. The existing translucent header can
show the new page surface behind it; its own styles and markup are unchanged.

## N. Safe page migration

1. Use a separate worktree from reviewed current main; record its SHA and protect
   unpublished work. Select a bounded page and explicit file scope.
2. Run the audit and capture original copy, metadata, schema, links, contracts,
   shared hooks and before screenshots. Inspect specialized CSS dependencies.
3. Add `.tg-ui`, synchronous token/foundation links and only justified component
   classes. Preserve URL, title/description, canonical, robots, schema, hrefs,
   fragments, disclosures, affiliate attributes and scripts.
4. Remove a page's legacy component classes only where replacing their presentation
   is intentional. Never change shared legacy tokens to make one pilot work.
5. Run static and browser checks, compare protected contracts, inspect the entire
   diff, and stop for owner review before publication or further rollout.

The About transformation preserves all editorial text, dates and facts, including
the affiliate paragraphs. Only structural wrappers/classes, H2 IDs, ordered-step
semantics and two stylesheet links change. There are no new links or CTAs.

## O. Component QA and local validation

Check syntax and namespace scope, custom-property completeness, real CSS load
order, no broken references, HTML structure, JSON-LD, exact copy/link preservation,
metadata and integration contracts. Run the existing auditor with `--base-ref
origin/main` and all self-tests; never rewrite the baseline to admit a redesign.

For browser review inspect all seven widths, card column changes, visible focus,
native summary activation, both button variants in default/hover/pressed states,
200% text enlargement, reduced motion, forced colors and descendant overflow.
Check the unchanged header/footer load and consent hooks separately. Test a
non-opted-in control with the new stylesheets loaded to prove namespace isolation.

Final observed results, stylesheet byte counts, screenshot locations and any
remaining limitations are recorded in the implementation report below. Browser
screenshots and temporary validation tools stay outside the repository. No
Lighthouse score, measured Core Web Vitals improvement, Safari/Firefox validation,
screen-reader certification or GitHub workflow result is implied by local checks.

### Observed implementation results

| Check | Local result |
| --- | --- |
| Python / audit self-tests | Python 3.12.10; all 57 existing self-tests passed on the final CSS. |
| Full baseline audit | PASS: 971 historical findings, 42 cumulative resolved, zero new regressions; 287 missing asset paths / 783 placements remain unchanged. |
| HTML and schema | HTML5 parsing has zero parse errors; one H1, six named H2 sections, unique static IDs; JSON-LD parses and is byte-identical. This is not a complete external HTML conformance service. |
| Copy and links | All original main text, dates and facts match after whitespace normalization; all six static anchor targets and labels match, including skip/mailto. Metadata and original head links are unchanged. |
| CSS parsing and scope | CSS Tree 3.2.1: zero parse errors; 49 namespaced tokens, 44 scoped rules, 181 declarations; all referenced tokens defined; no unscoped selectors, legacy token writes or important declarations. |
| Added CSS | `tokens.css`: 1,881 bytes; `foundation.css`: 6,459 bytes; total 8,340 uncompressed bytes, two synchronous local stylesheet requests on About only. |
| Browser | Real headless Chrome 154.0.8037.98 on Windows; local HTTP with shared scripts/partials; external requests blocked, analytics consent declined. |
| Required widths | 320, 375, 390, 430, 768, 1024, 1440px; screenshots captured before/after; zero document-width or main-descendant overflow at default text size. |
| Grid behavior | One column at the four phone widths; two at 768, 1024 and 1440px. Card rows can wrap for enlarged text. |
| Text enlargement | 200% root-font simulation at 320, 390, 768, 1440px: no main-descendant overflow; narrow step copy moves below its number. Native browser-menu zoom was not tested. |
| Keyboard | All seven owned targets reached using Tab: skip, Home, disclosure, privacy, contact, email and summary. Each has a 3px ocean outline / 3px offset. Enter opens and closes native details. |
| Button states | Both default, hover and pressed states measured from computed browser colors: 5.55:1, 7.75:1 and 10.30:1 respectively. Both action targets are at least 44px high at the default font size. |
| Motion / forced colors | Reduced-motion transition duration 0s and inherited CSS scroll behavior auto; forced-colors retains automatic color adaptation and a 2px system control border. |
| Shared UI | Header/footer injected DOM and sampled computed styles match the baseline at all seven widths; consent open/decline and menu open/Escape operate; zero JavaScript errors or failed local requests. |
| Non-opt-in control | Original About markup loaded with both new CSS files, without `.tg-ui`: no new rule matches; sampled styles/geometry identical at all seven widths. Six PNGs are byte-identical; 320px has at most 3/255 channel rasterization variance, without a style/geometry change. |
| Affiliate preservation | All 1,301 anchors, six forms, 25 widgets, 275 integration-markup units and 346 disclosures match, as do all four shared JavaScript hashes and metadata contracts. |
| Cruise / assets | All 27 protected cruise hashes match. Every pre-existing public file except About is unchanged, including CSS, images, scripts and all 12 parseable sitemaps. Auditor, fixture and workflow remain unchanged. |
| Disney | Original unpublished branch, HEAD, four changed paths and all four file hashes remain unchanged. |
| Git boundary | Exactly three untracked additions and one modified HTML file; index empty; HEAD remains starting main. No staging, commit, push, PR creation or merge. |

Screenshot artifacts remain in the temporary `tripguidely-foundation-qa` directory:
`before-{width}.png`, `after-{width}.png`, selected viewport-only `*-top.png`,
`after-contact-{variant}-{state}.png`, keyboard-summary, forced-colors and
`after-text-200-{width}` captures. No screenshot or QA dependency is committed.

Observed inherited limitation: at 320px with 200% root-font enlargement, the
shared header's menu button extends to x=339.19px and is partly clipped. The
original non-opted-in control reproduces the exact same brand/menu geometry.
Its markup and CSS are protected by this PR's scope, so repair it in a separate
shared-navigation change. Do not interpret the pilot's main-content checks as
whole-page certification under every enlarged-text setting. Firefox, Safari,
screen-reader review, native browser zoom and Lighthouse/CWV measurements remain
pending. The 971 historical site findings, including missing social imagery,
remain visible in the unchanged audit.

Recommended next rollout: a bounded editorial foundation migration for Disclosure
and Privacy Policy, preserving copy, metadata, disclosure contracts and shared UI.
Review that pilot before selecting commercial templates or adding image components.
Keep the inherited shared-nav enlarged-text repair separate and explicit.

## P. Future theme support

Semantic aliases separate component intent from primitives. A reviewed future
theme may override the semantic tokens on the opt-in root; do not change a
primitive globally or enable auto-dark mode on legacy pages. Dark/inverse surfaces
need separate text, boundary, focus and action-state contrast checks. No dark
theme, toggle, storage preference or new JavaScript ships here.

## Q. Future Image Agent integration

Use `docs/image-recovery-inventory.json` (schema version 1) as existing-slot facts.
Resolve its shared recommendation/source lookups before planning; distinguish
the six already repaired paths from the 287 still missing. Its ranked suggestions
are not permission to generate, download, purchase or insert imagery.

Require a source registry: original asset/source, creator, license and permitted
uses, attribution, verified location/subject, native dimensions, hash, derivatives,
crop/focal point, reviewer and rights/authenticity decision. Keep review status
distinct from a similar filename. No image source rights or analytics are invented.

Factual travel and attraction photography must accurately depict the actual
location. Do not synthesize a purported documentary photograph of a real park,
hotel, ship or landmark, or replace an unavailable photograph with a convincing
fictional one. Clearly illustrative planning diagrams may be appropriate after
editorial review. Mark synthetic illustrations explicitly in the visible caption
and provenance record; alt describes their illustrative purpose. AI labeling
cannot cure misleading factual depictions. Maps require verified geography and
rights. No AI image generation is implemented or called in this foundation.

Before placement, review purpose, source/rights, crop, responsive slots, alt,
caption, priority, decoding, layout reservation and metadata contracts. Then run
the regression auditor and browser checks. Cruise and unpublished Disney material
remain protected and need their separate approved work. Do not insert decorative
images to meet a quota, remove attribution or silently update historical exceptions.
