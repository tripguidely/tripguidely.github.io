# V3 phase 3: GDACS multi-hazard local integration

## Scope and reproducibility

Base main: `044b7b464e2cb938c10ba5b550cb5afff8ce75bb`, the merge of PR #61.
Worktree branch: `feat/global-travel-intelligence-v3-gdacs`. The owner authorized
final review, a targeted commit/push and a Draft PR after local validation. The
existing validation-only CI is extended to GDACS; no production collection,
publication, deployment, merge, paid service or extra GitHub permission is authorized.
Canada remains the default profile. Existing Canada and USGS configuration files,
Paris V2, public content, SEO baseline and production workflows remain unchanged.

The adapter reuses Adapter/Batch, event validation, comparison, durable local state,
CAS/locking/recovery and escaped JSON/Markdown reporting. New explicit profiles:
`gdacs` and `gdacs-usgs`. The latter is **offline replay only**; `--live` refuses it
before any path creation or request. Each profile has a different configuration hash;
use a separate external state directory rather than migrating/resetting old state.

## Official interfaces actually studied

The [Swagger UI](https://www.gdacs.org/gdacsapi/swagger/index.html),
[OpenAPI JSON](https://www.gdacs.org/gdacsapi/swagger/v1/swagger.json),
[feed reference](https://www.gdacs.org/feed_reference.aspx),
[quick start v2](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf)
and [March 2025 terms](https://www.gdacs.org/Documents/2025/GDACS_Terms_of_use_Mar_25.pdf)
were inspected. The v2 guide recommends cached collections and identifies bounded
100-record search pages. It requests the attribution used below. Numeric request
quotas per minute/day were not found in these official documents; unlimited access
must not be assumed. The six-minute refresh mentioned by the feed reference is a
source-feed refresh, not a completeness/timeliness SLA or a TripGuidely schedule.

The single adapter endpoint is fixed to:
`https://www.gdacs.org/gdacsapi/api/events/geteventlist/events4app`.
This is an application-selection cache, **not an exhaustive multi-hazard catalog**.
The observed response was JSON FeatureCollection with 100 features, nullable global
bbox, Point/Centroid geometries and EQ/TC/WF records only. No claim is made that FL,
VO or DR are always visible there, or that all events of any category are included.
The 100-record cache must be treated as selection-limited, not a complete page.

To qualify missing category schemas, three bounded documented SEARCH requests were
read (one per FL/VO/DR, pageSize=3, pageNumber=1, fixed study date interval). They
returned HTTP 200 and three records each with the same collection/property schema.
The saved cache's 100 records and all nine search records were accepted in a manual
schema qualification using local files, without running the Monitor or fetching
again. These real samples remain outside the repo; automated tests use only newly
written, clearly marked synthetic records. No access protection was bypassed.

SEARCH remains a **qualification-only** endpoint in this implementation. No
pagination, historic backfill, geometry/detail follow-ups, RSS/XML parser or arbitrary
query URL is enabled. A future comprehensive collector would need approved bounded
pagination, stable snapshot/ordering semantics, explicit date windows, coverage-gap
detection and cache/backoff policy. The API provides no precise per-endpoint response
schema for search; observed keys and semantic contracts are validated explicitly.

## Categories and information meaning

| GDACS type | V3 category | Interpretation |
| --- | --- | --- |
| EQ | earthquake | Source seismic/humanitarian assessment, with upstream identity if supplied. |
| TC | severe_weather | Tropical cyclone, including hurricane/typhoon classifications; no closure inference. |
| FL | flood | Flood assessment; a centroid is not an inundation footprint. |
| VO | volcanic_activity | Volcano assessment; no ash extent, airspace closure or hotel damage inferred. |
| DR | drought | Long-duration drought assessment; explicit V3 drought taxonomy added. |
| WF | wildfire | Selected forest fires; explicit wildfire taxonomy added, not all urban/industrial fires. |

Every normalized GDACS record is a **potential hazard assessment requiring
validation**: source_status=needs_validation (or unverifiable after omission/outage),
confidence=low, traveler impact=unknown, severity=unknown, publication=withheld,
summary=null. The record_kind incident is a V3 container, not a confirmed local
incident. Green/orange/red, score, episode score and quantitative severity/unit are
retained as source attributes rather than TripGuidely impact levels. HTML descriptions,
icons and alleged casualty/damage text are never rendered or used to generate copy.

EQ records explicitly retain `tsunami-context=not_assessed_not_official_warning`.
The qualified summary schema has no independently validated tsunami-warning field.
No TS family, active tsunami alert, evacuation order or secondary-impact assertion is
invented. A synthetic EQ fixture includes tsunami-related HTML to verify that such
text cannot become a warning. Future linked tsunami products require separate detail
schema qualification, authoritative warning evidence and human review; they are not
collected by this adapter.

## Identity, episodes, revision and cancellation

Observation identity is `(GDACS, eventtype, eventid, episodeid)`. Episodes remain
separate observations; the report groups them under their GDACS event family without
counting them as independent proofs. A revision within an episode uses datemodified;
older revisions, conflicting content at the same revision, and changes between
qualified/unqualified time bases reject the entire incoming source batch. Immutable
state generations retain prior versions and source outcomes. No silent repair or
partial source update is performed.

Identical repeated records deduplicate; conflicting versions of one observation in
one batch fail closed. Repeated unchanged observations preserve their original human
review deadline. New episodes receive their own identity and review task.

`iscurrent=false` and a past `todate` are retained as **source episode metadata**.
They do not mean a hazard ended or an alert was cancelled. Such records request
reverification and have ends_at=null. No explicit authoritative cancellation contract
was established in the qualified summary. An invented `iscancelled` property is
rejected as unknown schema. A real cancellation would require qualified explicit
source evidence and renewed review; no automated withdrawal/public retraction exists.

## Honest clocks, freshness and coverage

Actual API samples omit offsets on fromdate/todate/datemodified and omit a collection
export-generation timestamp. The adapter validates calendar dates, precision and
ordering but **does not append Z or guess a timezone**. Offset-free source strings
are normalized as wall-clock strings, flagged offset_unspecified, and V3 starts_at /
source_updated_at remain null. Their revision ordering compares only that source's
consistent wall-clock basis. No claim about exact UTC occurrence, future offset-free
clocks or source scientific freshness follows from successful parsing.

When all three timestamps have explicit offsets, they normalize to UTC; future
revision timestamps beyond ten minutes are rejected. Mixed bases are refused.
Source-generated time is honestly null in Batch, event provenance and source state.
The V3 contracts allow this only for GDACS; Canada/USGS still require their export
timestamps, and old state schemas remain readable unchanged.

Observed_at/last_verified_at describe technical collection, not confirmation of the
hazard. One-hour review/freshness deadlines are technical budgets; continued checks
may refresh technical receipt but not human review or old scientific information.
There is no independently qualified cache-generation clock, so stale-but-successful
cache responses cannot be proven current. Reports always state partial coverage.

Missing rolling-cache records mark prior observations unverifiable with a coverage
gap; outages preserve the last valid content and sanitize error details. Expiry does
not create an end time, safety statement or return-to-normal announcement. Existing
1,000-event, 1,000-generation and 10 MB state caps remain, without silent eviction.
This cannot be activated as an unbounded production monitoring service.

## Geography and traveler relevance

Country references are kept in source_data, not promoted to V3 affected countries
or cities. Pilot cities in a supplied ISO2 country list appear only as
country_context_to_verify, local_incident_confirmed=false. A primary country name or
ISO3 alone is not converted into local impact or a fuzzy country match. No distance,
nearest-city geocoding or country-equals-city inference is implemented.

Point/Centroid coordinates are range-validated and retained as representative points.
Null geometry is unresolved. Bounded Polygon/MultiPolygon coordinates and closed rings
are accepted only as **unqualified areas**: a geometry hash is retained but no impact
intersection is performed. Shape validity, spatial resolution, role, forecast validity,
precise destination boundaries and affected-area suitability are not established by
a syntactically valid polygon. Other geometry types fail closed. GeoJSON bbox may be
null/empty; antimeridian-spanning bounds confer no geographic relevance.

## Conservative USGS reconciliation

The offline combined profile parses each provider independently. When GDACS supplies
source=USGS/NEIC and an exact upstream sourceid matching exactly one USGS preferred
ID or alias, the report links them with basis=shared_official_identifier and
independent_confirmations=false. Both source records, versions and provenance remain
intact. Multiple episodes join the same family. Ambiguous aliases are not matches.

Absent or untrusted IDs produce a bounded review task listing the unresolved GDACS
and USGS earthquake observations; it does not assert a pairwise match. No geographic
radius, magnitude similarity, name parsing or timestamp coincidence establishes
identity. Reports explicitly say observation groups are not a confirmed disaster count.
The adapter never overwrites USGS or treats a model reusing USGS as independent proof.

## Transport, rights and operation

One anonymous GET of the fixed cache URL; no keys, cookies, authentication, retry,
redirect, arbitrary endpoint, remote writes or paid SDK. HTTP 429/5xx fail and preserve
state. JSON/GeoJSON only, identity encoding, 2,000,000-byte input cap, 15-second socket
timeout and a 30-second elapsed budget checked between reads. A socket read can consume
its timeout before the next budget check; this is not a hard total cancellation timer.

Schema allowlists are closed; IDs/flags/levels, country identifiers, dates and geometry
are bounded. Official report/detail/geometry links require the exact HTTPS host/path
and ID-bound query parameter set, with duplicate/extra/encoded query tricks rejected.
Only report links are retained for display; no supplied link is fetched. The shared
JSON parser refuses duplicate keys, non-finite values and excessive nesting.

The public API is documented as free, but hosting/storage/review have operator costs.
No service is purchased or dependency added. Attribution used verbatim:
**Global Disaster Awareness and Coordination System, GDACS**.
Free access is not an unrestricted licence for all upstream maps, media or data;
retain attribution and verify product-specific rights before republication. The terms
warn that automated estimates can be wrong, incomplete or delayed, and cannot replace
delegated local/national warnings. No endorsement is implied. No blanket CC licence
or automated publication permission is inferred.

## Local usage and next steps

Python 3.12, Git, IANA zones and external temporary directories are required.

```powershell
python -B -m unittest discover -s tests -p 'test_*travel_intelligence.py' -v
python -B scripts/paris-travel-intelligence.py --check-public
python -B scripts/global-travel-intelligence.py --provider gdacs `
  --input tests/fixtures/travel-intelligence/gdacs-synthetic.geojson `
  --now 2026-10-23T12:00:00Z --state-dir <external-state> --output <external-reports>
```

Combined replay uses `--provider gdacs-usgs --input <external-envelope.json>`.
The local envelope is `{schema_version:3,payloads:{gdacs-multi-hazard:<GeoJSON>,
usgs-earthquakes:<USGS GeoJSON>}}`, not a GDACS API format. Paths/URLs inside payloads
are never treated as instructions. Recovery is explicit, local, provider-profile-bound
and never followed automatically by collection.

The existing validation workflow now includes GDACS in its PR path filters and
requires exactly 129 discovered tests: 49 foundation/Canada, 24 USGS, 26 GDACS and
30 Paris V2. Ubuntu 24.04/Python 3.12 must pass every case without skips, including
the pointer-symlink regression and three additional path checks. Synthetic fixtures,
an inherited Python network-denial audit hook, the Paris public guard and diff
whitespace validation remain mandatory. Permissions remain `contents: read`;
triggers remain path-filtered Pull Requests to main and manual validation only.
There is no schedule, real collection, publication or deployment. Linux results
must be verified on the actual PR run before declaring the review complete.

For war/security alerts, qualify official national advisories already represented by
Canada before adding authority-specific conflict feeds; national advice is not city
incident evidence. For curfews, qualify competent national/municipal orders with
jurisdiction, original text, timezone, exceptions, effective dates and explicit repeal
rather than expiring an order by guesswork. For health, qualify
[WHO Disease Outbreak News](https://www.who.int/emergencies/disease-outbreak-news)
and competent health ministries, preserving confirmed vs potential events and
non-exhaustive coverage. These are qualification plans only: no new adapter, scraping,
medical/legal inference, source connection or publication is added for these topics.

## Local verification result

Final Windows/Python 3.12 suite: 129 cases discovered; 128 passed, zero failures or
errors. Suites: 49 foundation/Canada, 24 USGS, 26 GDACS, 30 Paris V2. Only the existing
OS-denied pointer-symlink case was skipped. No privilege or Windows security setting
was changed. The Python audit-hook guard was inherited by CLI subprocesses and
reported zero attempted network requests. Paris public guard returned evergreen.
These are local results, not Linux CI results for this new code.

Six separate synthetic JSON/Markdown examples were generated outside every checkout:
initial observation, unchanged replay, revision, omission, outage and combined USGS.
The combined example keeps eight observations in seven groups, with one exact shared
source-identifier relationship and no destructive merge or impact confirmation.
No automatic publication, patch or Git operation is produced by the engine.
