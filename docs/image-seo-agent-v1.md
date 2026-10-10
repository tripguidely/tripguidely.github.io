# Image SEO Agent V1 — local review tooling

This tool audits source files and creates disposable reports/previews outside the site.
It has no asset installation, baseline editing, Git write or publishing commands.
Python auditing is read-only by default. Browser sampling requires explicit opt-in;
its transport guards are not an operating-system network sandbox.
Starting main: `b1eccb19156606e42111a4551a4e460a75f1e2ce` (fetched 2026-10-10).

## Setup and commands

Python 3.12 and Pillow are the only required dependencies. Create a virtual environment
outside the repository and install `scripts/image-seo-requirements.txt` there. Use `-B`
to avoid Python cache writes. Do not install dependencies into production asset paths.

```powershell
python -m venv "$env:TEMP/tripguidely-image-tools"
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -m pip install -r scripts/image-seo-requirements.txt
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B scripts/image-seo-agent.py audit
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B scripts/image-seo-agent.py audit --page hotels/paris/index.html --output "$env:TEMP/paris-image-audit"
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B scripts/image-seo-agent.py brief --page itinerary/index.html --purpose hero --subject "Illustrative travel planning desk" --width 1600 --height 900
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B scripts/image-seo-agent.py optimize --source assets/images/hero/paris-2-day-itinerary-hero-2400x1350.webp --output "$env:TEMP/paris-image-preview-v1" --widths 640 960 --formats WEBP AVIF --quality 80
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B -m unittest discover -s tests -p test_image_seo_agent.py -v
```

An audit without `--output` writes only JSON to stdout. Every output mode requires a
fresh directory outside every Git worktree, reserved by exclusive directory creation.
Even an empty existing directory is rejected. There is no replacement policy: choose
a new output path for every run. Files are created exclusively and written through
their newly opened handles; existing regular files, hardlinks and dangling symlinks
are never truncated. Screenshot/encoder APIs produce buffers rather than writing paths.
Output ancestry rejects symlinks/reparse points and directory identities are checked
before writes. No failure cleanup deletes outputs; incomplete runs must not be reused.
The final audit.md / render.json indicates completion, not a transactional guarantee.
POSIX creation requests 0700 directories and 0600 files; Windows uses inherited ACLs.
Use private, trusted output parents with suitable ACLs. These are not a filesystem
sandbox against a privileged or same-account process concurrently moving ancestors
or changing links after handles are opened. Identity checks fail closed when detected;
exclusive creation prevents the reproduced existing-inode overwrite race.
Establish permitted derivative rights before publishing any optimized images.

Optional layout sampling uses an existing `playwright-core` installation and Chrome.
The verified combination is Python 3.12.10 / Pillow 12.3.0, Node 20.5.0,
playwright-core 1.64.0 and Chrome 154.0.8037.98. No dependency installs itself. The optional
Node/browser dependency is not supplied as a lockfile or vendored browser; use that
version explicitly in an external tooling environment and record browser versions.

```powershell
node scripts/image-seo-render.cjs REPOSITORY_PATH NEW_EXTERNAL_OUTPUT_PATH PLAYWRIGHT_CORE_PATH CHROME_EXE_PATH --allow-browser-sampling
```

The sampler is disabled without `--allow-browser-sampling`, before loading dependencies
or creating outputs. It serves trusted source on an ephemeral loopback port. Context
routing allows HTTP only to that exact origin, separately intercepts/closes all
WebSockets without connecting upstream, and blocks service workers. Local response CSP
restricts connections/frames and prohibits workers, plugins and forms. Page-realm
WebRTC/WebTransport constructors reject use. Missing WebSocket interception support
fails the run. These guards alter integration behavior intentionally during local QA.
They do not prove that every Chromium background/extension/native transport is isolated;
page-realm API guards are not protection from hostile JavaScript or browser exploits.
Do not sample untrusted repositories. Use an OS network sandbox for stronger isolation.
The default remains disabled because no such sandbox is supplied by V1.
It writes `render.json` and representative screenshots outside repositories.
It covers every titled HTML file at 390px/DPR2 and 1440px/DPR1, and seven representative
templates at 320, 768 and 1024px/DPR1. Images are associated with original static markup
by source/alt/order, rather than injected header images. Redirect samples are marked
and excluded from source image plans. Close the sampler before deleting its outputs.

For the complete test run, including the real Chrome loopback transport fixture, set
`IMAGE_SEO_PLAYWRIGHT_MODULE` to the external module path and `IMAGE_SEO_CHROME` to the
Chrome executable, then run the unittest command above. Without these optional tools
the Chrome test is explicitly skipped, not reported as verified.

Manifests record the sampler origin. Legacy manifests may establish that origin from
actualUrl. Only matching site/sampler origins may supply local decoded pixel widths;
other HTTP(S), missing-source or embedded measurements remain explicitly unverified.
Browser naturalWidth is retained as browser evidence, never silently substituted for
verified decoded pixels. Unverified sources produce no measured over/underdelivery
finding. Valid SVGs without intrinsic sizes retain null dimensions and a review finding;
valid explicit dimensions/viewBox values are retained, with no invented fallback size.

```powershell
& "$env:TEMP/tripguidely-image-tools/Scripts/python.exe" -B scripts/image-seo-agent.py audit --render-manifest EXTERNAL_OUTPUT_PATH/render.json --output EXTERNAL_REPORT_PATH
python -B scripts/audit-site.py --base-ref b1eccb19156606e42111a4551a4e460a75f1e2ce --self-test
python -B scripts/audit-site.py --base-ref b1eccb19156606e42111a4551a4e460a75f1e2ce
git diff --check
```

## Workflow and boundaries

| Stage | V1 behavior / required gate |
|---|---|
| SCAN | Inventory HTML, CSS URL image tokens, img/picture/source/srcsets, icons, posters, preloads, OG/Twitter, JSON-LD, interactive previews. |
| AUDIT | Resolve local URLs; decode actual raster files; parse SVG dimensions; inspect format, dimensions, alpha, animation, file hashes, pixel hashes, alt/loading/reservation markup. |
| PRIORITIZE | Deterministic technical severity; group responsive asset families. Visible missing heroes rank above metadata; shallow hub routes get a structural priority bonus. No invented traffic or conversions. |
| BRIEF | Structured JSON with page, purpose, subject, composition, style, ratio, dimensions, formats, filename, alt review, authenticity and rights requirements. |
| SOURCE / GENERATE | Human-owned gate. Record source URL, rights, attribution, derivative permissions and approval. No unattended acquisition or generation in V1. |
| OPTIMIZE | Explicit external-only WebP/AVIF/JPEG/PNG variants. EXIF orientation normalized; ICC retained; alpha checked; animation/CMYK rejected; no upscaling. |
| VALIDATE | Decode output, compare dimensions/format, verify alpha, SHA-256 and PSNR against the resized source. Require >=30 dB or exact pixels; failed quality gates return nonzero. |
| PREVIEW | External HTML contact previews and JSON manifests. Human inspection still required at intended crop and density. |
| HUMAN APPROVAL | Approve rights, authenticity, visual relevance, alt text, crop, quality and exact future file scope. |
| PUBLISH | Deliberately unavailable in V1. A separately authorized PR must preserve integrations and pass the existing auditor without weakening it. |

## Dimension and markup planning

Optional `--traffic-manifest PATH` accepts an exported object with `source`, date range,
account, and `rows` containing `page`, `clicks`, `impressions`, `search_type`. Use actual
connected GSC evidence, never fabricated traffic. Web/image impressions add a bounded
logarithmic tie-break within technical severity; the original metrics remain attached
to findings. Do not combine search types when describing search performance. Missing
rows do not establish zero traffic, and search impressions do not establish conversions.

`dimension_plans` records measured slots and selects the smallest sufficient buckets
from 320, 480, 640, 768, 960, 1200, 1600 and 1920 for DPR1/2, capped at source width.
These are proposals, not commands to create every bucket. If 1920/native width is
insufficient at the intended density, obtain a higher-quality authorized source or
accept a documented density limit; never upscale. Portrait art direction needs its
own reviewed source/crop, not stretched landscape files.

Each plan includes proposed WebP/AVIF srcset names and intrinsic attributes; these
names do not claim corresponding files exist or are published. Final sizes must match
the actual grid/gutter CSS and be validated between measured breakpoints and at zoom.

Browser `naturalWidth` can be density-corrected for srcset. The audit resolves `currentSrc`
to decoded source dimensions before identifying pixel overdelivery. A cover crop that
retains less than half the source area is a review concern, not automatically a defect.

Match image and preload `srcset`/`sizes` to template layout. Paris hotel/guide images
occupy roughly half the container on desktop, so their existing `100vw` claims should
be reviewed. Preserve intrinsic width/height ratio, reserve space with CSS, use
`decoding="async"`, lazy-load only below-fold images, and eagerly load the confirmed
critical LCP image. Use `fetchpriority="high"` sparingly for that critical resource.

For identifiable properties/attractions prefer licensed photography. Contextual alt
describes verified visible content; it must not turn generic imagery into a named hotel
or imply verified facilities. Decorative images use `alt=""`; informative images need
useful descriptions. Avoid repeating adjacent headings or stuffing keywords. Keep
JSON-LD/OG references resolvable and dimensions truthful. A 1200x630 JPEG social card is
a reasonable compatibility fallback, not proof every crawler requires JPEG.

## Quality and interpretation

- 250000 bytes and widths above 1920 are configurable-in-code review thresholds, not
  proof of bad compression or excessive dimensions in every context.
- PSNR compares the re-encoded output to the resized source, not to a higher-resolution
  original. It does not establish perceptual quality, truthful content, or licensing.
- Numeric quality scales differ between encoders. AVIF is not automatically smaller;
  choose using a fair visual-quality/byte benchmark. Retain PNG/lossless WebP for alpha
  or fine text when needed; keep SVG for appropriate existing vector assets.
- Duplicate groups are exact byte and exact decoded-pixel matches. Responsive variants
  and near-identical compositions are not mislabeled as exact duplicates.
- HTMLParser inventories authored markup; it is not a browser HTML conformance validator.
  CSS URL token scanning does not evaluate cascade, image-set descriptors or escaped
  URLs exhaustively. External and embedded references are separately marked, not
  incorrectly reported as missing local files. Single-page mode inventories its markup
  plus all assets; full scan supplies the separate shared CSS inventory.
- Empty alt, visual authenticity/relevance, intentional crops and loading decisions need
  human context. No page quality or ranking improvement is promised.
- Local PerformanceObserver entries are short unthrottled lab samples with HTTP/WebSocket
  guards. They do not establish complete network isolation, field CWV, final LCP, INP, or image-caused
  CLS. Header injection and consent UI can also shift layout. Firefox/Safari unverified.

## Initial local review

The 2026-10-10 review audited 136 HTML files (132 titled documents), 200 img elements,
1975 reference occurrences, 344 image files and 286 referenced local files. It found
287 distinct missing paths / 783 reference occurrences, including 72 img sources;
156 files exceeded 250000 bytes and 55 exceeded 1920px. There were zero missing alt
attributes, zero exact-byte/pixel duplicate groups and 31 large single-source responsive
opportunities. Four external image references remain unverified. Existing historical
findings are reported, not repaired or newly authorized by this tooling.

Confirmed examples: homepage preload declares 1920w for a decoded 1600px source;
Tokyo Drift's 2400x1350 filename actually contains 2400x1600 pixels. A one-pixel filename
height difference also exists in things-to-do-travel-hero-1200x675.webp. Missing cruise
assets and Disney page findings require separate authorized work; those files remain
protected. The New York hotel detail image is correctly below-fold/lazy despite living
in the hero directory; directory names alone must not establish LCP candidacy.

The desktop Paris hotel hero measured 504px but selected a 1600px resource at DPR1;
the Paris two-day guide measured about 554px with the same 1600px selection. Mobile
transport and homepage cover images crop heavily: review subject placement separately
from compression. Existing hotel interiors and attraction composites need owner
authenticity/rights review; contact sheets do not prove their provenance.

Local validation: 29 image-agent tests and all 57 existing regression self-tests pass.
The full site audit passes with zero new regressions (965 historical findings, 48
already resolved relative to the old fixture). Sixteen disposable optimized previews
pass output decoding/dimension/alpha and PSNR gates; human visual approval remains
required. Existing source files, all 27 cruise files and the ten prior worktrees'
5329 recorded file hashes remain preserved. Nothing staged, committed or published.

Built-in image generation is available in the assistant session, but was not invoked.
No local OPENAI_API_KEY is configured. V1 has no automatic API adapter, creates no
fabricated generated files and leaves generation/sourcing at the human gate.

Google Search Console is connected through Windsor.ai for this site. The exported
2026-09-10 through 2026-10-07 evidence (fresh data disabled) reports 1941 web impressions,
1280 image impressions and one click across the returned rows. Harry Potter accounts
for 1276 image impressions; Rome things-to-do has 786 web impressions and Universal's
ticket hub has 719. These are retrieved observations, not a prediction of image changes'
effect on rankings, impressions or conversions. The local tool only reads the exported
file and has no account credentials or connector dependency.

Next phase: review the external audit/report/briefs, resolve rights and protected-file
scope, approve one small pilot, benchmark its selected variants and accurate sizes,
then authorize a separate production PR with mobile/desktop/accessibility and unchanged
affiliate-contract checks. No publication is authorized by this local review.

## Blocking-defect corrections — 2026-10-10

The four reproduced defects are addressed within the tooling files: report/screenshot
hardlink overwrites now fail on fresh-directory reservation or exclusive file creation;
browser WebSockets are explicitly intercepted with service-worker/CSP defenses and
sampling disabled by default; valid SVGs with unknown dimensions continue scanning;
external currentSrc URLs cannot borrow local decoded pixel dimensions. ViewBox values
are identified as vector coordinates, not raster pixels, and excluded from raster-size
recommendations. Legacy layout manifests remain usable via their actualUrl origin.

Validation: 46 tooling tests (29 original + 17 added), including the actual Chrome
loopback fixture, pass with no skips; all 57 site self-tests and the complete site audit
pass. HTTP/WebSocket attempts reached neither test endpoint; source bytes survived both
original hardlink fixtures and late-file insertion. Fresh inventory retains all eight
previous headline counts: 136 HTML, 1975 references, 287 missing paths / 783 occurrences,
344 images, 156 above 250000 bytes, 55 wider than 1920px and 31 responsive opportunities.
The 55 include 54 rasters plus the 2000-unit-wide world-map.svg. Large raster findings
fall from 55 to 54 because this vector no longer receives a raster downsizing warning;
its authored width/viewBox and file remain unchanged. No other finding-category count
changes in the fresh source-only audit.
No production asset, protected contract, baseline, auditor or dependency pin changed.

Remaining limitations include trusted output ancestry/inherited Windows ACLs, no OS
network sandbox, raster decoding/encoding memory budgets, no independent timeout on
font readiness, limited srcset/CSS parsing and first-frame animation inspection. V1 is
conditional tooling-only readiness for trusted local use; these limitations are not
claims of completed production image work, live tracking validation or deployment.
