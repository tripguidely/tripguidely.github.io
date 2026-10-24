# GDACS: qualification record and remaining production decisions

Phase 3 now provides an explicitly selected local adapter and offline tests; see
[the phase 3 operations document](global-travel-intelligence-v3-gdacs-phase3.md).
This earlier qualification record remains background, not authorization for production.

Reviewed official sources on 2026-10-23. This document does not add a provider,
credential, collector, schedule, public renderer or withdrawal mechanism.

## Interfaces and schemas

[Swagger UI](https://www.gdacs.org/gdacsapi/swagger/index.html) and its
[OpenAPI document](https://www.gdacs.org/gdacsapi/swagger/v1/swagger.json) were read.
The inspected v1 document exposes 71 paths. `/api/Events/geteventlist/search` is a
GET with eventlist, alertlevel, fromDate/toDate, country, severity, pageSize (max 100),
pageNumber and caller parameters; results are ordered by descending end date.
The response declaration for this endpoint gives HTTP 200 without a precise
endpoint-specific payload schema: it is insufficient alone for a strict parser.
Generic FeatureCollection/Feature/Geometry schemas leave Feature properties open.
Eventkey uses eventtype+eventid; Eventdetail includes country, alertlevel,
fromdate, todate and description; seismic and volcano features have separate models.
An adapter must qualify real samples and freeze per-category nullable/type contracts,
units, timezone handling, revision fields, geometries and bounded pagination first.

The [official API quick start](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf)
confirms GeoJSON queries and XML feed alternatives, advises using cached collections
and comparing update timestamps, and describes 100-record pages. A future collector
must finish all pages consistently or mark coverage partial. Empty results and a
missing event are not evidence of resolution. Bulk KML is a limited recent window,
not a complete archive or a guarantee of travel-area accuracy.
The [feed reference](https://www.gdacs.org/feed_reference.aspx) documents a six-minute
feed refresh, not an SLA for detection, scientific review or delivery.

## Hazard coverage and limitations

| Hazard | Future qualification and mapping | Source/update limitations |
| --- | --- | --- |
| Earthquakes (EQ) | Preserve measurement identity, model version, intensity/exposure evidence and source references; associate with USGS for review only. | [EQ methodology](https://www.gdacs.org/Knowledge/models_eq.aspx) uses shaking or seismic parameters with vulnerability/coping capacity. Scores estimate humanitarian needs, not city disruption. |
| Tsunamis | Qualify the tsunami products linked to seismic events separately; do not assume an independently supported TS search family. Require coastal geometry and delegated warning-authority confirmation for any public warning. | [Tsunami model](https://www.gdacs.org/Knowledge/models_ts.aspx) describes scenario calculations, fallback estimates and model delay. Modeling is not an evacuation mandate. |
| Tropical cyclones (TC), including hurricanes/typhoons | Keep storm/episode identity, track forecasts, valid times, wind units, uncertainty and any separate surge/rain products. | [TC methodology](https://www.gdacs.org/Knowledge/models_tc.aspx) combines authoritative bulletins and modeled hazards. Track points or a wind category cannot establish hotel closures. Updates follow source bulletins, not a universal six-minute new forecast. |
| Floods (FL) | Qualify event/episode histories and actual flood footprints separately from representative points; retain authoritative local sources. | [Flood model](https://www.gdacs.org/Knowledge/models_fl.aspx): global event awareness is not exhaustive street-level inundation or guaranteed transport status. Source availability and delineation vary. |
| Volcanoes (VO) | Preserve volcano ID, activity episode, ash advisory validity and national observatory references; route to human review. | [Volcano model](https://www.gdacs.org/Knowledge/models_vo.aspx) uses VAAC reports and weekly Smithsonian reports, with manual escalation. A volcano point does not describe ash extent, airspace closure or all local hazards. |
| Droughts (DR) | A later category needs explicit V3 taxonomy approval, versioned areas and long-duration lifecycle handling. | [Drought model](https://www.gdacs.org/Knowledge/models_dr.aspx) combines ten-day indicators and expert validation; this is not sudden-event timing. |
| Wildfires (WF) | A later category needs explicit taxonomy approval and burn/hazard polygons, source resolution and issue times. | [Wildfire model](https://www.gdacs.org/Knowledge/models_wf.aspx) uses GWIS with selection thresholds and daily updates; it excludes urban/industrial fires and omits many small fires. |

The additional DR/WF families and tsunami hazard are confirmed by GDACS's own
[coverage history](https://data.gdacs.org/anniversary.aspx). No support for arbitrary
extra categories, pandemic alerts, all severe weather or transport monitoring is
inferred. Green/orange/red and numeric scores are source assessments of potential
humanitarian significance. Green never means safe. Event visibility, score thresholds
and timeliness differ by hazard; there is no uniform guaranteed detection delay.

## Identity, geography and lifecycle design

Use `(GDACS, eventtype, eventid)` for base identity and retain episode/revision IDs
and timestamps separately. Distinct episodes must not be discarded as duplicates.
A GDACS earthquake may reuse USGS parameters or ShakeMap products; these are not two
independent confirmations. Prefer an exact shared official ID/reference for a
candidate relationship; time/point/magnitude similarity only creates a review task.
Never merge USGS and GDACS observations or compound EQ/tsunami hazards automatically.

Validate coordinate system, axis order, polygon rings, antimeridian crossing,
geometry validity time, holes, simplification, source resolution and destination
boundary version before any overlap association. A point can be an epicenter,
centroid, volcano or track position; no representative point defines an affected
city. An affected-country label alone does not verify an urban incident.

Preserve last valid content across outage or schema drift, journal revisions, report
partial page coverage and flag stale technical data. An absent record, lower score,
expired forecast or `todate` cannot by itself establish that a hazard ended or that
travel returned to normal. Bind any human-approved association to the exact revision;
corrections invalidate it and require renewed review.

## Terms, attribution and public use

The quick start describes free API access and requests the attribution:
“Global Disaster Alert and Coordination System, GDACS”. It does not establish an
unqualified licence for every upstream product. Recheck upstream rights and current
attribution requirements before republishing maps or derived products; no CC licence
is assumed here and no paid service is introduced.

The [March 2025 terms](https://www.gdacs.org/Documents/2025/GDACS_Terms_of_use_Mar_25.pdf)
require critical validation: some notifications are algorithmic and unreviewed,
coverage/timeliness are not guaranteed, data can change, and authoritative national
or local alerts retain precedence. GDACS is for humanitarian coordination rather
than delegated public warning. Geographic representations also carry uncertainty.

Technically an RSS/API change can create an internal review item. It cannot authorize
public publication or retraction. A future publisher would need a separate approved
policy: authoritative impact evidence, geography and validity review, human approval,
revision binding, audit trail, freshness checks, and explicit withdrawal evidence.
Expiry can trigger review; it must not silently announce an all-clear or remove a
notice as though danger had ended. All such publication/withdrawal capabilities
remain absent from the current V3 engine.

## Decisions before any implementation

1. Authorize a GDACS adapter and select hazard-specific schemas and endpoints.
2. Approve pagination, caching, retention, sampling cadence and outage behavior.
3. Qualify per-product rights, attribution, source independence and geographic data.
4. Define review ownership and verify authoritative local warning sources.
5. Review code and offline fixtures, run Linux CI, then separately authorize any
   operational deployment. Current GitHub read permissions are sufficient for tests;
   no write permission, event-storage branch or automation change is requested.
