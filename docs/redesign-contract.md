# TripGuidely regression and redesign contract

This infrastructure change leaves the published site untouched. Existing errors
remain visible, identified exceptions and must be repaired through future bounded
PRs. Inventory totals are observations, never passing thresholds.

## Run locally

Use Python 3.12 or later and Git. There are no third-party runtime dependencies.
Run from a clean checkout or isolated worktree based on current main:

```text
git fetch origin main
python -B scripts/audit-site.py --base-ref origin/main
python -B scripts/audit-site.py --base-ref origin/main --verbose
python -B scripts/audit-site.py --base-ref origin/main --json
python -B scripts/audit-site.py --base-ref origin/main --self-test
```

The audit reads tracked public files and relevant untracked additions, respecting
Git ignore rules. It excludes infrastructure directories, Git metadata, build
outputs and dependencies. Tracked `.gitkeep` files remain in cruise protection.
It never stages, edits, opens affiliate destinations or makes network requests.
Self-tests use a tiny independent site held entirely in memory. They do not alter
the website, even temporarily. Repairs to production baseline defects do not make
these tests obsolete.

Exit 0 means no new regressions, 1 means findings or self-test failures, and 2
means invalid configuration, inaccessible Git history or an invalid fixture.
Plain output separates historical findings, resolved issues, authorizations and
errors. `--verbose` lists individual historical findings; JSON includes all of
them. JSON omits elapsed time so equivalent runs are byte-for-byte deterministic.

## Pull request checks

`.github/workflows/site-audit.yml` runs on PRs targeting main and on manual dispatch.
PR checkout uses GitHub's proposed merge tree and compares against the event's
exact base SHA, supplied through an environment variable rather than interpolated
shell code. Manual dispatch checks the selected ref against `origin/main`.
Full history is fetched for reproducing the original fixture. The workflow uses
`contents: read`, disables persisted checkout credentials, runs mutation tests
and the audit, propagates the auditor's exit status, and writes a readable job
summary even when the audit fails. It has no deploy, merge, secrets, baseline
generation or `pull_request_target` steps.

The maintained major pins are `actions/checkout@v7` and
`actions/setup-python@v7`; CI uses Python 3.12, aligned with the locally tested
Python 3.12.10. Python 3.14 compatibility has not been tested. Review action upgrades against the
[checkout documentation](https://github.com/actions/checkout),
[setup-python documentation](https://github.com/actions/setup-python) and
[Python support schedule](https://devguide.python.org/versions/).
Local validation does not prove a remote workflow run. Configure this job as a
required branch-protection check after it has run successfully on GitHub. Owner
review of the auditor, workflow and fixture is necessary: code in a PR cannot
authenticate its own reviewer or prevent edits to its own enforcement policy.

## What is checked and protected

- Internal anchors, fragments (including mounted header/footer IDs), image and
  social-image references, JSON-LD assets, multiline `srcset`, local stylesheets,
  scripts, CSS imports/URLs and statically identifiable JavaScript imports/assets.
  Resolution handles relative and root paths, directory routes, `index.html`,
  percent encoding and query strings. Filenames remain case-sensitive on Windows.
  Missing pages, media, fragments, case errors, external URLs, mailto and tel are
  classified separately. Missing assets are also deduplicated by physical path.
- Indexable content has one nonempty title, description and canonical. Canonical
  shape, local destination and route agreement, robots directives and JSON-LD
  parsing are checked. H1 rules apply to pages declaring Article schema, not
  arbitrary utilities, redirects, partials or verification files. Existing SEO
  metadata, OG/Twitter values, canonical and hreflang markup are protected against
  unreviewed edits by a comparison with the PR base.
- Sitemap XML namespace/parseability, location shape, local destination,
  duplicate URLs, child index membership, canonical agreement and self-canonical
  publication coverage. Redirect, empty, partial and verification destinations
  are distinguished from content. A syntax-valid sitemap can still fail these
  checks.
- Existing affiliate opening tags retain exact URL, Sub ID, attributes and their
  multiplicity on each page. Affiliate forms, widget markup, disclosure markup,
  all non-JSON-LD script elements, redirect settings and local JavaScript file
  hashes are protected. CRLF/LF differences are normalized; actual markup and
  URL edits are not. Historical tracking patterns are retained without automatic
  normalization. Additions are allowed without requiring an exact anchor total.
- All published HTML deletions and all cruise-related file changes are reported.
  Cruise protection uses individual paths and SHA-256 hashes, including images,
  HTML, its sitemap and its tracked placeholder. Yacht Charter paths/references
  and SeaRadar references cannot be introduced into public site content.

The existing Paris `hotels/paris/where-to-stay/` refresh redirect is preserved
and excluded from independent article coverage. The French Montreal cruise
canonical is flagged for localization review rather than rewritten. Existing
hreflang decisions are preserved as metadata; reciprocal hreflang correctness
still needs a separate localization audit.

## Baseline exceptions and repairs

`tests/fixtures/site-baseline.json` records source revision, origin, recording
date, informational inventories, contract fingerprints and explicit exceptions.
Each exception has a stable ID, category, source, destination/issue, locator,
occurrence, reason and date. Identity excludes line numbers so formatting does
not create different defects. Repeated placements in one source are distinct
occurrences; physical missing asset paths are counted separately from placements.

The recorded source is main commit
`bce66a7f4aae7ae94a0fee5bfee369cbb85bd8e7`, dated 2026-10-08. The auditor
reconstructs that Git revision and verifies the fixture inventory, fingerprints
and exception identities. It requires the source to be an ancestor of the base.
When the base already contains a fixture, a PR cannot add exception IDs beyond
that trusted fixture. An ordinary audit never regenerates or writes the fixture.

Fix a specific finding in a bounded repair PR, run the audit, and inspect its
`RESOLVED` report. Remove only those resolved exception entries from the fixture;
keep the source revision, original inventory and contracts as historical evidence.
Do not refresh totals or hashes to the changed site. A defect that is absent from
the PR base fails if reintroduced, even if its old exception has not yet been
retired. Once retired, its ID cannot be added back in a normal PR.

Initial bootstrapping only used this explicit command before the fixture existed:

```text
python -B scripts/audit-site.py --base-ref origin/main --record-baseline --recorded-on 2026-10-08
```

It refuses to overwrite a fixture. Do not delete and recreate the baseline to
make a repair/redesign pass. A genuine policy migration requires a separate owner
review of the policy code, fixture and reasons; it is not an ordinary exception
update. Reason/date corrections and retirement are reviewable manual fixture edits.

## Approving intentional contract changes

Prefer adding valid content while preserving existing contracts. If an owner
intentionally changes protected material, add an exact entry in the fixture's
`authorizations` array. Inspect the audit's before/after hashes and the underlying
diff. Record the owner's review; this field documents approval and does not
authenticate the owner. Do not preauthorize changes without human review.

```json
{
  "kind": "integration_script",
  "source": "assets/js/site.js",
  "base_revision": "exact-current-base-commit-sha",
  "before": "64-character-sha256-reported-by-the-audit",
  "after": "64-character-sha256-reported-by-the-audit",
  "reason": "Concrete approved purpose and review reference",
  "reviewed_by": "owner-review-reference",
  "recorded_on": "2026-10-08"
}
```

Replace placeholders with actual values. Matching is exact: no wildcard paths,
count thresholds or partner-wide bypasses. Each entry is bound to the base commit,
source, kind and exact before/after hashes, preventing reuse against another base.
Use null for a missing before/after value. Remove consumed entries in a later
cleanup PR. Authorization never suppresses broken links, invalid XML/JSON-LD,
missing coverage, malformed new affiliate anchors or prohibited integrations.

Kinds for changed existing contracts are `affiliate_anchor`, `affiliate_form`,
`widget`, `disclosure`, `integration_markup`, `seo_metadata`, `redirect_behavior`,
`integration_script`, `cruise_file` and `published_file` (HTML deletion).
Markup contract before/after values hash the complete per-source, per-kind
fingerprint/count mapping, not a single opening tag. File kinds use file hashes.
A deliberate cruise deletion can require several independent authorizations
because HTML deletion and embedded protected contracts are also checked; repair
links and sitemaps instead of authorizing those new errors away.

New script markup not already used in the base requires `new_integration_markup`
with before null and after its markup hash. New local JavaScript files require
`new_integration_script`, and new widgets require `new_widget`. Exact reusable
script markup from the base can be added on a new page without a new authorization.
Review widget settings, partner identifiers, destinations, Sub IDs and consent
behavior separately; authorization records that review rather than validating
the partner product. A script update can need both removal/change authorization
and authorization for its newly introduced markup.

## New SEO pages and affiliate additions

Add a complete HTML document with a single title, description and self-canonical
HTTPS URL on the site origin, valid robots syntax, valid JSON-LD and an H1 when
declaring Article schema. Use existing assets and verified fragments, and add
the canonical to the appropriate child sitemap already listed in the index.
Untracked new pages are included locally, so the checks work before staging.

New affiliate anchors must use HTTPS on a recognized partner host, a matching
`data-aff`, a nonempty `data-subid`, the `js-aff` class, `target="_blank"` and
`nofollow sponsored noopener` rel tokens. Partners currently recognized are
Klook, Airalo, Tiqets, Kiwi and Travelpayouts; the host sets are explicit in the
auditor. Use owner-generated URLs and the page's reviewed disclosure. Newly added
affiliate forms receive separate HTTPS/partner/Sub ID configuration validation.
Other forms of integration use the explicit review mechanism above. Expanding
the host/program policy requires owner review. No test clicks destinations,
books tickets or performs transactions. Product validity and affiliate destination
verification remain human checks.

## CSS redesign review

Run the audit before and after each bounded redesign. Preserve editorial content,
SEO metadata, navigation/fragments, affiliate attributes, forms/widgets, scripts
and disclosures. Confirm all added local CSS/JS/media references resolve. Review
the exact protected contract diff before introducing an authorization; a broad
baseline refresh cannot substitute for review. Existing CSS can change when its
references remain valid and it does not affect cruise-protected assets.

Perform desktop/mobile browser review of layout, navigation, keyboard focus,
contrast, consent controls, responsive images and affiliate interactions. Measure
Lighthouse/Core Web Vitals separately when needed. This static auditor does not
claim visual, accessibility, performance or live partner verification.

## Interpreting failures and limits

`KNOWN` means an unchanged recorded defect, not a claim that the site is error-free.
`RESOLVED` means a historical issue is absent now. `ERROR` identifies a new or
reintroduced defect or a changed protected contract. Fix the specific source and
target; inspect base and current markup for hash failures. Configuration errors
require fixing missing history or the fixture rather than adding exceptions.

HTML extraction uses the standard-library parser, not full HTML5 conformance or
JavaScript execution. Static imports/literal asset references are checked;
computed URLs, minifier-dependent constructs and arbitrary dynamic references
need code/browser review. Article detection currently uses Article JSON-LD;
editorial pages without that declaration need manual heading review. XML checks
cover parsing and sitemap semantics, not an external XSD validator. Network
redirects, deployment routing, partner destinations, ticket availability and
reciprocal hreflang are not verified. Symlinked public files fail for review.

## Verified initial observations

The unchanged main audit passes with 1,013 explicit historical placement/findings
and zero new regressions. Inventory: 133 HTML files (128 content, two partials,
one redirect, one verification file and one empty page); 107 missing-page anchor
placements, zero static broken-fragment/case findings, and one runtime consent
fragment review. Missing assets: 807 reference placements across 293 distinct
paths (278 WebP, 10 JPG, five PNG). Broader reference coverage includes social
metadata, JSON-LD, responsive sources and JavaScript image configuration.

Twelve sitemap XML files parse; 11 child sitemaps contain 116 URL entries and
114 unique URLs. Fourteen self-canonical routes lack coverage, two entries are
duplicates, and one points to empty New York transport content. Remaining known
findings are 78 invalid robots directives on 39 pages, one missing Article H1,
one French cross-route canonical and the empty page itself.

Affiliate inventory: 1,301 anchors (1,142 Klook, including 118 historical
host-only patterns; 37 Airalo; 58 Tiqets; 64 Travelpayouts); six forms, 25 widgets,
275 script elements, 346 disclosure markup units and four local JavaScript files.
Cruise inventory: 27 individually hashed files, including six HTML pages,
19 images, its sitemap and a tracked `.gitkeep`. No protected website content
changes are included in this implementation.

Recommended next repair PR: the 14 missing canonical sitemap entries and two
duplicate entries, after checking publication intent. Keep the empty New York
transport page and French canonical decision as explicit separate editorial
decisions, and use exact approval for any protected cruise sitemap change.
Follow with bounded link and media repairs rather than one broad baseline rewrite.

## Local implementation validation, 2026-10-08

| Requested check | Result |
| --- | --- |
| 1. Worktree and branch | `C:/Users/1995/AppData/Local/Temp/tripguidely-site-regression-guards`; `infrastructure/site-regression-guards`. Clean before implementation. |
| 2. Starting main | `bce66a7f4aae7ae94a0fee5bfee369cbb85bd8e7`; origin fetched; PR 15 confirmed merged. |
| 3. Disney preservation | Original `design/disney-premium-pages` branch, HEAD and dirty file list retained; all four initial SHA-256 file hashes match. |
| 4. Files created | Exactly auditor, JSON fixture, this contract and site-audit workflow; no extra test fixture files. |
| 5. HTML inventory | 133 HTML files; role breakdown recorded above. |
| 6. Broken links | 107 missing-page anchor placements, 70 distinct hrefs; no static fragment/case errors; one runtime consent review. |
| 7. Missing assets | 293 distinct paths: 278 WebP, 10 JPG, five PNG; 807 placements (691 HTML/social and 116 JSON-LD). |
| 8. Sitemaps | 12 parseable XML files; 116 child URL entries, 114 unique; 14 coverage gaps, two duplicates, one empty-page destination. |
| 9. Affiliate inventory | 1,301 anchors; six forms, 25 widgets, 275 script elements, 346 disclosure units, four local JavaScript files. |
| 10. Cruise inventory | 27 paths individually hashed; no removals or modifications; no Yacht Charter or SeaRadar introduced. |
| 11. Historical exceptions | 1,013 explicit records with identities, sources, targets, categories, reasons and dates; zero new regressions. |
| 12. Runtime | Full local JSON audit measured 3.855 seconds including Python/Git startup; runtime varies by machine. |
| 13. Determinism | Two complete JSON outputs match byte-for-byte; SHA-256 `093e3781c8a035bae0c2271e0294a1097c1bba2c22e4cde2848710004bfbd035`. |
| 14. Mutation proof | All 41 in-memory self-tests pass. All seven requested failures are detected, plus case, fragment, imports, srcset, canonical, heading, tracking, widget, authorization and reintroduction checks. |
| 15. New valid page | Passes with canonical, valid schema/assets and sitemap addition. |
| 16. Historical repair | Missing-image repair passes and reports resolved; removing it against the repaired base fails despite the stale exception. |
| 17. Affiliate addition | New legitimate CTA passes; malformed CTA and modified existing URL fail. No destination opened or transaction made. |
| 18. Workflow review | PR-main/manual triggers, exact PR base SHA, merge-tree checkout, maintained major pins, supported Python, read-only permissions, failure propagation and summary reviewed. Remote execution pending. |
| 19. Python | Python 3.12.10 syntax compilation and 41 self-tests pass; real baseline audit exits 0. CI aligned to Python 3.12; remote execution pending. Python 3.14 not tested. |
| 20. YAML | Structure and shell steps manually reviewed; no PyYAML, yaml or js-yaml parser installed locally. Formal YAML/actionlint validation not performed. |
| 21. Diff whitespace | `git diff --check` passes; because files are untracked, new-file trailing whitespace was checked separately. |
| 22. Final newlines | Every new file has exactly one final LF, no CR and no trailing whitespace. |
| 23. File scope | Four additions only. All 524 public files in the starting Git tree remain unchanged (text CRLF/LF normalized). |
| 24. Git status | Exactly four untracked implementation files; index empty; no existing tracked diff. Original worktree keeps its three modified HTML files and untracked Disney CSS. No staging, commit, push, PR or merge performed. |
| 25. Limits | Static extraction only; no browser QA, Lighthouse/CWV, external XSD, live destinations/products, reciprocal hreflang audit or remote CI pass claimed. |
| 26. Next repair | Bounded sitemap coverage/duplicate repair after editorial review; separate empty-page and French canonical decisions. |
