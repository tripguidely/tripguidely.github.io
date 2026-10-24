# Global Travel Intelligence V3: USGS phase 2 (local only)

## Scope and integration

Base: `6c963bf03794a0c7a951eb05bcf712d6d7d742c6`, the main merge of PR #60.
Branch: `feat/global-travel-intelligence-v3-usgs`. This phase adds local shadow
processing and offline PR validation only. No live engine collection, public alert,
production workflow activation or deployment is performed.
Canada remains the default profile; its source configuration and Paris V2 are unchanged.

`USGSAdapter` implements the existing `Adapter`/`Batch` contract. It reuses V3's
validated event model, orchestration, compare logic, durable `LocalStateStore` and
escaped local JSON/Markdown reports. The new source profile is opt-in through
`--provider usgs`. It has its own configuration hash. Use a dedicated external state
directory; an existing Canada state directory fails configuration validation instead
of being reset or migrated. Profiles are deliberately separate for offline replay;
combined-provider configuration and production scheduling require another review.

## Selected official feed

[USGS GeoJSON summary documentation](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
provides magnitude-filtered windows. This integration fixes the endpoint to
`https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson`:
M4.5+, past seven days; USGS documents a one-minute feed refresh. This is a source
refresh rate, not a TripGuidely polling schedule. No polling is configured.

Engineering choice: seven days give more overlap for interruptions and corrections
than an hour/day window. M4.5+ limits traffic and state growth compared with all
magnitudes; the significant-only subset could omit events worth reviewing. A month
would cost more volume without providing a complete correction history. A future
collector should use a conservative cadence such as five minutes with shared
caching, approved separately; never issue per-city or per-event detail requests.

[USGS coverage limitations](https://earthquake.usgs.gov/earthquakes/map/?about=true&help=missing)
explicitly warn that lists are incomplete, including M4.5+ worldwide. Small events,
reporting delays, later corrections and events outside the rolling window can be
absent. Threshold selection is not a safety threshold. The parser accepts valid
lower or null magnitudes, including possible downward corrections, without asserting
that this feed normally includes all such events. The minor fixture is deliberately
a stress case, not a claim about feed completeness. Offline gaps cannot reconstruct
all intermediate revisions; the engine reports insufficient coverage.

## Untrusted input and network contract

The collection schema is closed: FeatureCollection, exact metadata keys, bounded
feature count, optional validated 3-D bbox, exact Feature/Point structure, explicit
required/optional property allowlists, primitive types and bounded auxiliary values.
Unknown schema fields or unsupported seismic types reject the whole batch, preserving
last valid observations. This favors review over silently interpreting schema drift.

The shared JSON parser rejects duplicate keys, excessive depth, oversized input and
non-finite numbers. Bounds: 2,000,000 bytes; 1,000 features; longitude [-180,180],
latitude [-90,90], depth [-100,1000] km, magnitude [-2,10] or null. These are defensive
acceptance bounds, not forecasts. Numeric source measurements use normalized decimal
strings in V3's scalar-only source data; units are explicit and null remains unknown.
Epoch milliseconds are interpreted as UTC with millisecond precision, not local time.
Export age is at most one hour; future export/update tolerance is ten minutes.
Event origin must lie in the seven-day window (ten-minute boundary tolerance) and
precede its update. Invalid clocks reject the batch.

Identifiers are bounded alphanumeric/underscore/hyphen tokens; preferred ID must
match network+code. Official event/detail URLs are constructed-contract matches for
that ID on earthquake.usgs.gov, with HTTPS and no query, fragment or foreign host.
No supplied URL is fetched. Configuration endpoints, docs and licence URLs are fixed.
The transport makes one anonymous fixed GET: 15-second socket timeout, 30-second
elapsed read budget checked between chunks, bounded reads, identity encoding, JSON
or GeoJSON media type, no redirect, authentication, cookies or retry. A socket
operation may itself consume its timeout before the next elapsed-budget check;
this is not a hard process-wide 30-second cancellation guarantee.

No live USGS engine collection was performed for this phase. Tests inject bytes or
mock the opener; documentation was read from official websites independently.

## Observations, revisions and technical lifecycle

Each event retains the source ID and preferred USGS event ID, occurrence and update
times, magnitude/type, epicenter longitude/latitude/depth, measurement review status,
aliases, PAGER color and the raw tsunami flag. Provenance contains the adapter
version, exact endpoint, payload SHA256, export time, configuration hash, licence
statement and policy link. Network/code are validated against the preferred ID.
Original full payload bytes are not archived by the engine; fixtures provide
reproducible examples. Production raw-payload retention is a separate decision.

An `automatic` or `reviewed` source status describes USGS measurement processing;
both remain V3 `observed`, never confirmed traveler impact. Magnitude is retained
as a measurement while V3 impact severity remains `unknown`. No hotel, road, airport,
evacuation or tsunami impact is inferred. The `tsunami` flag and PAGER color are
source attributes only; neither is a delegated public warning or evacuation order.

Stable preferred IDs deduplicate across runs. Identical repeated records consolidate;
conflicting versions in one batch reject that batch. A later `updated` time permits
corrections under the same V3 identity and records `source_revised`, requiring human
reverification. Older exports/revisions and conflicting content at the same revision
are refused. Alias lists are normalized and retained as evidence, not used to merge
different preferred IDs automatically. Preferred-ID replacement or cross-source
identity reconciliation requires human review; similarity/proximity is not identity.

Rolling-feed disappearance marks the saved observation `unverifiable` and records a
coverage gap. No end time, withdrawal or all-clear is generated. Outages preserve
last valid content; recovery restores technical observation status without creating
a new earthquake. One-hour freshness/review expiry only describes data quality.
The event's `ends_at` is always null. Source-specific expiry never closes a public alert.

Immutable, integrity-checked generation files form the local audit trail, including
prior revisions and source outcomes. CAS, exclusive writer locks, atomic pointer
replacement, explicit recovery, path/symlink protections and outside-checkout report
writes are reused unchanged. Reports identify coverage gaps and carry no publication
permission. Existing hard caps remain: 1,000 cumulative retained events, 1,000 state
generations and 10 MB per state. No silent eviction or retention reset is implemented;
reaching a cap refuses persistence and requires review. This is not ready for an
unbounded continuous worldwide service.

## Destination association model (design only)

Validated coordinates establish an epicenter point, not a country polygon, city
boundary or affected area. Place strings are not geocoded. Country codes, city,
region, affected locations and destination contexts therefore remain empty/unassigned,
even for a fixture point near Rome. There is no distance-based relevance engine.

A future reviewed association record should contain `event_id`, `source_revision`,
`destination_id`, `relationship=potential_overlap`, `official_geometry_url`,
`geometry_sha256`, `geometry_kind`, `coordinate_reference_system`, geometry validity
interval, destination boundary version/hash, intersection method and uncertainty,
`reviewed_by`, `reviewed_at`, and `impact_confirmed=false`. It must bind the exact
source revision and vetted geometry; a changed revision invalidates the review.
For an epicenter, containment can establish location only. Relevant shaking requires
a qualified intensity footprint; tsunami exposure needs a qualified coastal hazard
product; confirmed traveler impact needs separate authoritative local evidence.
Centroids, nearest cities and a distance radius cannot populate `explicitly_affected`.
This record is a proposed future contract, not accepted configuration or active code.

## Reproduce offline

Python 3.12, Git, IANA timezone data and external temporary directories are required.
On Windows the existing pointer-symlink regression can be skipped if the OS denies
symlink creation; no security setting is changed. The merged Ubuntu validation
workflow discovers `test_*travel_intelligence.py`, including the new suite. Its PR
path filter explicitly includes the USGS test file and its test command requires
the USGS suite to be discovered. Ubuntu 24.04, Python 3.12, read-only permissions,
the Python network guard and the zero-skip rule are preserved. No scheduled or
production collector is added.

```powershell
python -B -m unittest discover -s tests -p 'test_*travel_intelligence.py' -v
python -B scripts/paris-travel-intelligence.py --check-public
python -B scripts/global-travel-intelligence.py --provider usgs `
  --input tests/fixtures/travel-intelligence/usgs-synthetic.geojson `
  --now 2026-10-23T12:00:00Z --state-dir <external-state> --output <external-report>
```

Use new dedicated paths outside every Git checkout; never put reports under docs or
public pages. `--live --provider usgs` exists for an explicit one-shot local fetch,
without an override URL, but is not used in validation or scheduled anywhere.
Local review examples are generated separately from the synthetic fixture: initial
observation, repeat, revised magnitude, rolling omission and outage. No sample is
real earthquake intelligence or public copy.

## Costs, rights and owner decisions

The public summary endpoint needs no API key or paid SDK. This implementation adds
no dependencies or billed service. Storage, human review and any future CI/hosting
costs still belong to the operator. USGS requests attribution; its
[copyright policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits)
places USGS-produced information in the U.S. public domain but excludes some
third-party content. Credit the U.S. Geological Survey and preserve contributor
provenance; do not imply USGS endorsement or reuse logos/media automatically.

Owner-authorized commit/push and a Draft PR permit Linux CI on the actual new code;
they do not authorize merge or production activation. Before production: retention/archival policy,
coverage and thresholds, operational cadence/backoff, source schema monitoring,
geometry licences, human review ownership, and a separately authorized publication
and withdrawal process. No extra GitHub permission is needed for this local phase.
GDACS remains a documented future integration: see `global-travel-intelligence-v3-gdacs-plan.md`.

## Local validation result

Final combined run: 103 discovered cases (49 foundation, 30 Paris V2, 24 USGS).
102 passed; the existing Windows symlink-privilege case was skipped. No other skip,
failure or error. A Python audit hook blocked and logged network requests in the
test process and inherited CLI subprocesses: zero network attempts were detected.
All new USGS cases ran successfully. Paris public guard returned evergreen.
This is Windows/Python 3.12 validation, not a Linux result for the phase 2 code;
Linux CI must follow a separately approved push.
