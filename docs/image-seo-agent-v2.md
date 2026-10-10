# Image SEO Agent V2 — offline candidate tooling

Recorded base: `aa38d2eb649555ed7b32515d88bb84a362e1fe1c`, fetched 2026-10-10.
This phase permits local implementation and synthetic fixtures only. No paid API,
production asset generation, website edits, staging, publication or deployment is
authorized. V1 auditing, optimization, output guards and browser opt-in are retained.

## Dependencies and offline commands

Use Python 3.12 and the existing external virtual environment with
`Pillow==12.3.0` from `scripts/image-seo-requirements.txt`. V2 adds only Python
standard-library modules; no OpenAI SDK, package installation, downloading or
network discovery happens at import or execution of offline commands. Existing
optional browser tests use an externally installed Playwright-core and Chrome;
the browser sampler still exits before dependency loading without explicit opt-in.

From the worktree, using that environment's Python:

```powershell
python -B scripts/image-seo-agent.py generate-preview --brief docs/image-briefs/paris-v2-pilot.json --brief-id paris-family-logistics-illustration --base-revision aa38d2eb649555ed7b32515d88bb84a362e1fe1c --output "$env:TEMP/paris-v2-unused-dry-run"
python -B scripts/image-seo-agent.py generate-preview --brief docs/image-briefs/paris-v2-pilot.json --brief-id paris-family-logistics-illustration --base-revision aa38d2eb649555ed7b32515d88bb84a362e1fe1c --output "$env:TEMP/paris-v2-fresh-mock-preview" --mock
python -B -m unittest discover -s tests -p test_image_seo_agent.py -v
python -B -m unittest discover -s tests -p test_image_seo_generation.py -v
python -B scripts/audit-site.py --base-ref aa38d2eb649555ed7b32515d88bb84a362e1fe1c --self-test
python -B scripts/audit-site.py --base-ref aa38d2eb649555ed7b32515d88bb84a362e1fe1c
```

The default command returns a plan to stdout without creating any directory or
reading credentials. `--mock` creates deterministic colored test shapes, not an
AI-generated illustration of the brief. Every report identifies this distinction.
Neither command has a live-provider, credential or paid-use option. Use `-B` to
avoid cache writes. Choose a fresh external output path for each mock run.

## Provider boundary and verified API schema

`GenerationRequest` binds brief identifier, local page, placement, prompt, dimensions,
format, quality, count, recorded base and a hash of the selected brief plus page bytes.
`Provider` exposes `capabilities()`, `estimate()` and `generate()`; `GenerationResult`
contains in-memory bytes and provenance, never an arbitrary download URL. The mock
implements this boundary without a network client. `prepare_generation_candidate()`
connects a provider result to V1 optimization without making a provider request.

The optional adapter pins `gpt-image-2.5-flare-2026-09-08`, documented in the
[official model catalog](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare).
Its fixed TLS POST uses `/v1/images/generations`, bearer authentication, `model`,
`prompt`, `n=1`, `size`, `quality`, `output_format` and opaque background. It accepts
one `data[].b64_json` result; redirects and URL outputs are rejected. Schema and
authentication were checked on 2026-10-10 against the
[Images API reference](https://developers.openai.com/api/reference/resources/images/methods/generate).

Custom dimensions require multiples of 16, aspect ratios from 1:3 to 3:1, and
documented pixel/edge limits. The adapter applies stricter local limits and avoids
experimental resolutions; 1536x864 is accepted. PNG, JPEG and WebP are provider
outputs; AVIF is a local derivative. See the
[image generation guide](https://developers.openai.com/api/docs/guides/image-generation).
These are documentation checks, not an account probe, live generation test, service
availability guarantee or validation of billed costs. No fallback model is selected.

## Paid-call approval: implemented but not authorized for this phase

An explicit library call to `OpenAIProvider.generate()` would require all of:

- An exact matching paid-use approval dictionary and the separate runtime phrase
  `I AUTHORIZE ONE PAID IMAGE REQUEST`.
- `operation: PAID_IMAGE_GENERATION`, `provider: openai`, `status: APPROVED`,
  the exact `request_sha256` and `base_revision`, `max_requests: 1`, `max_images: 1`.
- A unique 32-character lowercase hexadecimal `approval_id`, an owner
  `review_reference`, timezone-aware `approved_at` and `expires_at` with a validity
  window no longer than 24 hours, and current time within that window.
- A positive finite `advisory_budget_usd` and `budget_is_advisory: true`.
- The source repository root and one persistent private external approval ledger.

The ledger exclusively reserves `paid-<approval_id>/attempt.json` before reading
`OPENAI_API_KEY`. A consumed ID cannot be replayed in that ledger. Missing
credentials, HTTP errors, bad responses, decoding failures and timeouts consume
the attempt too. The ledger records request/review references and unknown billing,
never the key or provider body. Transport errors are sanitized. There are no retries,
redirect following, proxy discovery or user-configurable endpoints.

Approval dictionaries/receipts are human workflow inputs, not signed attestations.
Use a single trusted ledger; someone with the ability to change code, forge approvals,
delete ledger records or select a different ledger can bypass that workflow. This
is not account-level spend enforcement. `estimate()` returns unknown live dollar
cost and explicitly advisory status. A timeout does not cancel a remote job or
prove that it was unbilled. Future live operation requires a separate owner decision.

## Resource and output limits

| Resource | Bound |
| --- | --- |
| Initial images/requests per approved run | 1 / 1; framework ceiling 3 images, not enabled |
| Concurrent live requests | 1 per process; each approved run has one request |
| Prompt | 8000 UTF-8 bytes |
| Brief/page/layout inputs | 2 MiB each |
| Provider JSON response | 24 MiB, including streaming reads |
| Decoded source file | 16 MiB |
| Decoded image | 4,194,304 pixels; maximum edge 2560; one frame |
| Live resolution | At least 655,360 pixels; at most 2560x1440 pixels in area; local edge bound also applies |
| Connection / total transport deadline | 10 / 180 seconds; parent worker deadline includes DNS and headers |
| Response parsing / image codec worker | 45 seconds per operation |
| Worker result frame | Fixed shared mapping: 24 MiB transport, 16 MiB image bytes, 2 MiB JSON; 41-byte header |
| Worker input frame | At most one 24 MiB binary input plus 2 MiB JSON metadata, four-byte metadata length and 41-byte header |
| Variant plan | At most 3 widths and 4 formats; no upscaling |
| Encoded derivative bytes | At most 64 MiB total; source and small reports are additional |

Before Pillow/native opening, a bounded still-image preflight validates PNG chunk
lengths/CRCs and IHDR, JPEG baseline/progressive frame/scan markers, and WebP RIFF
lengths, padding, VP8/VP8L bitstream dimensions and matching VP8X canvas. Animated,
multiframe, ambiguous, unsupported or suspicious containers fail closed. The edge
and pixel limits apply before known native canvas allocation, and native dimensions
and actual format are checked again before the full decode. Preflight establishes
structural/canvas limits, not pixel validity; full decode, alpha and quality checks
are still required. In particular the 706-byte 4096-square WebP review fixture is
rejected before `Image.open`, rather than after allocation of its large canvas.

Bulk inputs also use a bounded shared frame with JSON metadata and opaque binary
bytes. Spawn bootstrap carries only small mapping names, a trusted function and
limits; large image/response bodies and credentials are not sent through its
bootstrap pipe. Neither input nor result frames use pickle. Shared mappings contain
transient request data during execution and inherit OS access controls; they are
not a secret vault or protection against a privileged/same-account local reader.

Workers return a fixed shared-memory frame with kind, bounded length and SHA-256,
committed after payload writing. The parent waits on process exit with a monotonic
deadline; it never calls blocking `recv()` or unpickles result messages. Partial
frames, oversized lengths, crashed workers and responses arriving after the deadline
are rejected. A complete frame from a producer that has not exited is not accepted.
Startup, transfer, bounded result copies/parsing and acceptance share the elapsed
deadline. Timed-out workers are terminated, joined, killed if necessary and reaped;
process/sentinel and mapping handles are closed, with unlink where applicable.
Cleanup has up to two seconds of additional termination/reaping grace. OS process
creation/scheduling is not a hard real-time guarantee; late results never succeed.

Workers are sequential. Inputs, canvas dimensions, variant counts and encoded
output bytes are bounded; there is no hard process-RSS limit or OS-level
network/filesystem sandbox. Native codecs remain a dependency security boundary.
Large JSON or codec inputs can still consume substantial memory within these bounds.
Use private trusted parents and appropriate Windows ACLs. Exclusive creation and
alias/identity checks cannot defend against every same-account or privileged race.
Incomplete outputs are retained and never reused or automatically deleted.

Fresh output directories must be outside every Git worktree, not an ancestor of the
source root. V1 rejects symlink/reparse ancestry and existing output directories.
Files are exclusively created without truncating existing regular files, hardlinks
or symlinks. Nothing writes into production assets or invokes Git/deployment tools.

## Validation, layout evidence and review

Actual bytes are fully decoded, not trusted by extension. PNG/JPEG/WebP, frame count,
color mode, requested/decoded dimensions, pixel and file limits, EXIF orientation,
SHA-256 and decoded-pixel hashes are checked. Duplicate byte/pixel candidates can
be rejected against up to two previously inspected candidates; this is not perceptual
near-duplicate detection or a historical inventory of every generated image.

The external validated source is placed in its own input directory. V1 optimizes
from that directory into a sibling external directory, preserving source containment
without relaxing repository output guards. It decodes each derivative, verifies
dimensions and alpha, and checks PSNR against the resized source (minimum 30 dB,
or exact pixels). Failed encodings remain explicitly rejected in the disposable
preview and cannot be selected. At least one passing encoding is needed per width.
The manifest identifies the smallest passing file for each width from actual bytes;
this is a review aid, not automatic approval or proof of equivalent perceptual quality.
PNG or lossless alpha-preserving formats may be preferable to a smaller lossy output.

Without an external `--layout-manifest`, mock output is master-size only and marked
`MASTER_ONLY_LAYOUT_UNVERIFIED`. No proposed brief size becomes a measured variant.
A layout manifest needs exactly `page`, `placement`, `context_sha256`, a nonempty
string `evidence_reference` (at most 2000 UTF-8 bytes) and 1..20 `samples` with
exactly measured CSS `width` and `dpr` (1..3). Duplicate JSON keys, nonfinite
numbers, unknown fields and malformed samples are rejected.
Widths are rounded up from width times DPR and capped to native width. More than
three unique targets requires human review of a smaller bounded plan. Owner-supplied
evidence is not independently measured by this command. Recheck after layout changes.

Version 3 `review-manifest.json` records target, placement, brief, base/context/request hashes,
source/provider/model, requested and actual sizes, actual format/bytes/file and pixel
hashes, optimization results, layout status, authenticity/rights and every artifact
hash (including plan and preview). `layout_evidence` retains the exact supplied
document and its SHA-256 over UTF-8 JSON with sorted keys and compact separators;
key order and whitespace do not change the fingerprint. With no supplied evidence,
it explicitly records `state: ABSENT`, `sha256: null`, `document: null`; supplied
evidence records `state: SUPPLIED`. The plan also binds the state/fingerprint and
cannot be reused if evidence changes before candidate preparation.
It always starts `PENDING`. Mock provenance never
claims a photographer, license, AI service execution, real property or generation
history. Other provider candidates remain unverified illustrative material.

`verify_generation_review()` checks a separately supplied receipt with
`schema_version: 3`, `status: APPROVED`, exact manifest SHA-256, request SHA-256,
explicit `layout_evidence_state` and `layout_evidence_sha256` (including null for
ABSENT), the complete artifact hash map,
`rights_reviewed`, `visual_reviewed`, `layout_reviewed` all true and an owner
`review_reference`. It recomputes current brief/page and artifact hashes, rejects
traversal/aliases and stale approvals after source, manifest or file changes. For
SUPPLIED evidence the caller must provide the current file using the keyword
`layout_file`; it is canonicalized, validated and compared with the recorded
document/fingerprint and receipt. Changed measurements or references, missing
current evidence, evidence added after an ABSENT review, or changed artifact hashes
invalidate approval. Older schema/receipts that omit evidence fields fail closed;
they require fresh human review. It
returns receipt validity only, leaves the manifest pending, and authorizes no
publication. Visual quality, truthful subject matter, licensing and accessibility
require real human evidence, not merely a boolean someone can fabricate.

## Paris briefs and next phase

`docs/image-briefs/paris-v2-pilot.json` contains three disabled, pending briefs:
existing itinerary collage delivery only; existing shared hotel hero delivery only;
optional family logistics illustration (stroller, luggage, planning sheet, clock).
Existing composition is retained; photographic authenticity/rights are not assumed.
The optional master is 1536x864; 640x360, 800x450 and 1280x720 are proposals awaiting
actual slot measurement. No branded property, invented facility, accessibility claim
or fake landmark is permitted. The current text needs no replacement image.

Next: human tooling review; owner rights review for existing heroes; separately
approve and measure any illustration placement. Only then consider a separately
authorized one-image external preview with exact provider/prompt/budget review.
Publication would require another reviewed asset/page PR and the unchanged full
regression audit. This implementation contains no publication mechanism.

## Local validation on 2026-10-10

All 46 original V1 tests remain unchanged and pass; the V1 suite passes 49/49
including three new integration checks and the real local Chrome transport fixture.
The initial implementation passed 61/61 V2 offline tests; the independent review
then reproduced three gaps that those tests did not cover. Targeted corrections
add pre-allocation container checks, complete worker-result supervision and a
versioned layout-evidence receipt contract. V2 now passes 90/90 tests (29 added
regressions); 18/18 external reproduction/safety checks also pass without real API
calls. All 57 site self-tests and the full recorded-base
site audit pass with zero new regressions. Python syntax, JSON, dry-run containment,
four-format mock conversion, stale receipt rejection and diff checks pass.
All 532 public files, 27 cruise files and 6423 recorded hashes across the 12 prior
worktrees are preserved. No real provider calls, production assets or Git publication.

External Windows measurements of the original 706-byte WebP now show zero Pillow
opens and zero private committed-byte increase during rejection; the earlier open
allocated 134,488,064 bytes before rejection. This measures that fixture, not a hard
RSS ceiling or a universal native-code memory guarantee. Real spawned partial-frame
codec/transport fixtures timed out at approximately 1.015/1.016 seconds on one-second
deadlines, with children reaped and both mappings closed. A 0.05-second late-producer
deadline raised TimeoutError after approximately 0.062 seconds including cleanup.
These are offline process measurements, not observed remote-provider behavior.
Unchanged layout evidence and reordered JSON keys validate; changed measurements,
references, missing current evidence and stale receipts are rejected. Publication
remains unauthorized. Independent re-review and a separate owner decision are still
required before any paid generation.
