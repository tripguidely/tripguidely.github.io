"""GDACS application-selection adapter; potential hazards require human validation."""
from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import json
import re
import time
from urllib.parse import parse_qsl, urlsplit
from urllib.request import Request, build_opener

from .model import content_hash, event_id
from .providers import Batch, NoRedirect
from .usgs import number
from .validation import (MAX_INPUT_BYTES, canonical, digest, instant, keys, parse_json,
                         plain, require, stamp)

ADAPTER_VERSION = "gdacs-events-v1"
SOURCE_ID = "gdacs-multi-hazard"
FEED = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/events4app"
DOCUMENTATION = "https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf"
TERMS = "https://www.gdacs.org/Documents/2025/GDACS_Terms_of_use_Mar_25.pdf"
CATEGORIES = {"EQ": "earthquake", "TC": "severe_weather", "FL": "flood",
              "VO": "volcanic_activity", "DR": "drought", "WF": "wildfire"}
PROPERTIES = {"eventtype", "eventid", "episodeid", "eventname", "glide", "name", "description",
              "htmldescription", "icon", "iconoverall", "url", "alertlevel", "alertscore",
              "episodealertlevel", "episodealertscore", "istemporary", "iscurrent", "country",
              "fromdate", "todate", "datemodified", "iso3", "source", "sourceid", "polygonlabel",
              "Class", "countryonland", "affectedcountries", "severitydata"}
REQUIRED = PROPERTIES - {"countryonland", "icon", "iconoverall", "htmldescription", "glide", "eventname"}
DATA_FIELDS = {"event-type", "gdacs-id", "episode-id", "alert-level", "alert-score",
               "episode-alert-level", "episode-alert-score", "source-current", "source-temporary",
               "from-text", "to-text", "modified-text", "time-basis", "country-contexts", "country-label",
               "geometry-summary", "upstream-source", "upstream-id", "severity-measurement", "tsunami-context"}


def validate_source(source):
    require(source["adapter"] == ADAPTER_VERSION and source["source_id"] == SOURCE_ID and
            source["endpoint"] == FEED and source["documentation_url"] == DOCUMENTATION and
            source["licence_url"] == TERMS, "gdacs_source_contract")
    require(type(source["allowed_urls"]) is list and set(source["allowed_urls"]) == {FEED, DOCUMENTATION, TERMS}
            and source["countries"] == [] and source["country_slugs"] == {}
            and source["audience_nationalities"] == [], "gdacs_worldwide_contract")
    require(all(type(source[k]) is int and source[k] == 1 for k in
                ("max_export_age_hours", "freshness_hours", "review_hours")), "gdacs_time_policy")


def positive_id(value):
    require(type(value) is int and 1 <= value <= 2147483647, "gdacs_identifier")
    return value


def source_date(value):
    """Never turn the API's offset-free clock into an invented UTC instant."""
    require(type(value) is str and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})?", value),
        "gdacs_timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("gdacs_timestamp") from None
    require(1970 <= dt.year <= 2100, "gdacs_timestamp")
    if dt.utcoffset() is None:
        return dt.isoformat(timespec="microseconds"), None
    return stamp(dt), instant(stamp(dt))


def event_url(kind, typ, ident, episode):
    require(type(typ) is str and typ in CATEGORIES, "gdacs_category")
    positive_id(ident); positive_id(episode)
    if kind == "report":
        return f"https://www.gdacs.org/report.aspx?eventid={ident}&episodeid={episode}&eventtype={typ}"
    path = "polygons/getgeometry" if kind == "geometry" else "events/geteventdata"
    suffix = f"&episodeid={episode}" if kind == "geometry" else ""
    return f"https://www.gdacs.org/gdacsapi/api/{path}?eventtype={typ}&eventid={ident}" + suffix


def checked_url(value, kind, typ, ident, episode):
    expected = event_url(kind, typ, ident, episode)
    require(type(value) is str and len(value) <= 2048 and "%" not in value, "gdacs_url")
    try:
        supplied, target = urlsplit(value), urlsplit(expected)
        pairs = parse_qsl(supplied.query, keep_blank_values=True, strict_parsing=True)
        valid = (supplied.scheme == "https" and supplied.netloc == "www.gdacs.org" and
                 supplied.path == target.path and not supplied.fragment and
                 len(pairs) == len(dict(pairs)) and dict(pairs) == dict(parse_qsl(target.query)))
    except ValueError:
        valid = False
    require(valid, "gdacs_url")
    return expected


def bbox(value):
    if value is None: return
    require(type(value) is list and len(value) in (0, 4), "gdacs_bbox")
    if value:
        for i, limit in enumerate((180, 90, 180, 90)):
            number(value[i], -limit, limit)
        # An antimeridian-spanning box is allowed; it is never an impact proof.
        require(value[1] <= value[3], "gdacs_bbox")


def geometry_summary(value):
    if value is None:
        return {"kind": "missing", "sha256": digest(None), "point": None}
    keys(value, {"type", "coordinates"})
    count = 0
    def position(pos):
        nonlocal count
        require(type(pos) is list and len(pos) == 2, "gdacs_coordinates")
        count += 1; require(count <= 1000, "gdacs_geometry_limit")
        return [number(pos[0], -180, 180), number(pos[1], -90, 90)]
    def polygon(rings):
        require(type(rings) is list and 1 <= len(rings) <= 100, "gdacs_polygon")
        for ring in rings:
            require(type(ring) is list and 4 <= len(ring) <= 1000, "gdacs_polygon")
            points = [position(pos) for pos in ring]
            require(points[0] == points[-1], "gdacs_polygon_open")
    typ, coordinates = value["type"], value["coordinates"]
    if typ == "Point":
        point = position(coordinates); kind = "representative_point"
    elif typ == "Polygon":
        polygon(coordinates); point = None; kind = "unqualified_area"
    elif typ == "MultiPolygon":
        require(type(coordinates) is list and 1 <= len(coordinates) <= 100, "gdacs_polygon")
        for poly in coordinates: polygon(poly)
        point = None; kind = "unqualified_area"
    else:
        raise ValueError("gdacs_geometry_not_qualified")
    return {"kind": kind, "sha256": digest(value), "point": point}


def country_contexts(items):
    require(type(items) is list and len(items) <= 64, "gdacs_countries")
    codes = []
    for item in items:
        keys(item, {"iso2", "iso3", "countryname"})
        require(type(item["iso2"]) is str and re.fullmatch(r"[A-Z]{2}", item["iso2"]), "gdacs_country")
        require(type(item["iso3"]) is str and re.fullmatch(r"[A-Z]{3}", item["iso3"]), "gdacs_country")
        plain(item["countryname"], 120); codes.append(item["iso2"])
    require(len(codes) == len(set(codes)), "gdacs_country_duplicate")
    return ",".join(sorted(codes)) or None


def validate_gdacs_event(event, source, now):
    validate_source(source)
    data = event["source_data"]; keys(data, DATA_FIELDS)
    typ, ident, episode = data["event-type"], positive_id(data["gdacs-id"]), positive_id(data["episode-id"])
    require(type(typ) is str and typ in CATEGORIES and event["category"] == CATEGORIES[typ], "gdacs_category")
    require(event["source_event_id"] == f"{typ}:{ident}:{episode}" and
            event["source_url"] == event_url("report", typ, ident, episode), "gdacs_identity")
    require(event["record_kind"] == "incident" and event["severity"] == "unknown" and
            event["country_codes"] == [] and event["country_code"] is None and event["region"] is None
            and event["city"] is None and event["affected_locations"] == [], "gdacs_no_impact_inference")
    require(event["source_status"] in {"needs_validation", "unverifiable"} and
            event["ends_at"] is None and event["published_at"] is None and event["source_published_date"] is None
            and event["withdrawal_evidence_url"] is None and event["related_event_reference"] is None,
            "gdacs_no_inferred_resolution")
    for key in ("alert-level", "episode-alert-level"):
        require(type(data[key]) is str and data[key] in {"Green", "Orange", "Red"}, "gdacs_alert_level")
    for key in ("alert-score", "episode-alert-score"):
        require(type(data[key]) is str and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", data[key]) and
                0 <= float(data[key]) <= 100, "gdacs_score")
    require(type(data["source-current"]) is bool and type(data["source-temporary"]) is bool, "gdacs_flags")
    for key in ("country-label", "upstream-source", "upstream-id"):
        if data[key] is not None: require(plain(data[key], 256) == data[key], "gdacs_text")
    codes = data["country-contexts"]
    require(codes is None or (type(codes) is str and len(codes) <= 255 and
            re.fullmatch(r"[A-Z]{2}(?:,[A-Z]{2})*", codes) and codes == ",".join(sorted(set(codes.split(","))))),
            "gdacs_country_context")
    require(type(data["geometry-summary"]) is str and len(data["geometry-summary"]) <= 800, "gdacs_geometry")
    geo = parse_json(data["geometry-summary"].encode(), 800)
    keys(geo, {"kind", "sha256", "point"})
    require(type(geo["sha256"]) is str and re.fullmatch(r"[a-f0-9]{64}", geo["sha256"]), "gdacs_geometry_hash")
    require(geo["kind"] in {"missing", "representative_point", "unqualified_area"}, "gdacs_geometry")
    if geo["kind"] == "representative_point":
        require(type(geo["point"]) is list and len(geo["point"]) == 2, "gdacs_coordinates")
        for value, limit in zip(geo["point"], (180, 90)):
            require(type(value) is str and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) and
                    -limit <= float(value) <= limit, "gdacs_coordinates")
    else: require(geo["point"] is None, "gdacs_coordinates")
    require(event["geographic_scope"] == ("point" if geo["kind"] == "representative_point" else "uncertain") and
            event["geographic_basis"] == ("source_geometry" if geo["kind"] != "missing" else "unresolved"),
            "gdacs_geographic_basis")
    dates = [source_date(data[key]) for key in ("from-text", "to-text", "modified-text")]
    require(all(text == data[key] for (text, _), key in zip(dates, ("from-text", "to-text", "modified-text"))), "gdacs_date_format")
    aware = [dt is not None for _, dt in dates]
    require(all(aware) or not any(aware), "gdacs_mixed_time_basis")
    require(dates[0][0] <= dates[1][0] and dates[0][0] <= dates[2][0], "gdacs_date_order")
    basis = "explicit_offset" if all(aware) else "offset_unspecified"
    require(data["time-basis"] == basis and event["starts_at"] == (dates[0][0] if all(aware) else None)
            and event["source_updated_at"] == (dates[2][0] if all(aware) else None), "gdacs_no_invented_utc")
    if all(aware): require(dates[2][1] <= now + timedelta(minutes=10), "gdacs_future_revision")
    require(event["source_revision"] == data["modified-text"] and
            event["source_severity_raw"] == data["alert-level"], "gdacs_revision")
    require(type(data["severity-measurement"]) is str and len(data["severity-measurement"]) <= 800, "gdacs_measurement")
    measure = parse_json(data["severity-measurement"].encode(), 800)
    keys(measure, {"value", "unit"})
    require(type(measure["value"]) is str and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", measure["value"]) and
            -2 <= float(measure["value"]) <= 1000000000000, "gdacs_measurement")
    require(measure["unit"] is None or plain(measure["unit"], 40) == measure["unit"], "gdacs_unit")
    require(data["tsunami-context"] == ("not_assessed_not_official_warning" if typ == "EQ" else None), "gdacs_tsunami")
    require(event["provenance"]["source_generated_at"] is None and
            event["provenance"]["adapter_version"] == ADAPTER_VERSION, "gdacs_unknown_export_time")
    require(instant(event["fresh_until"]) <= instant(event["observed_at"]) + timedelta(hours=1), "gdacs_freshness")


def validate_revision(previous, incoming):
    old, new = previous["source_data"], incoming["source_data"]
    require(old["time-basis"] == new["time-basis"], "gdacs_time_basis_changed")
    require(new["modified-text"] >= old["modified-text"], "gdacs_revision_rollback")
    require(new["modified-text"] != old["modified-text"] or
            incoming["content_hash"] == previous["content_hash"], "gdacs_revision_conflict")


def fetch_gdacs():
    request = Request(FEED, headers={"Accept": "application/json, application/geo+json",
        "Accept-Encoding": "identity", "User-Agent": "TripGuidelyTravelMonitor/3-local (+https://tripguidely.github.io/contact/)"})
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        require(response.status == 200 and response.geturl() == FEED, "unexpected_http_response")
        require(response.headers.get_content_type() in {"application/json", "application/geo+json"}, "unexpected_content_type")
        require(response.headers.get("Content-Encoding", "identity") == "identity", "unexpected_encoding")
        chunks, size = [], 0
        while True:
            require(time.monotonic() - started <= 30, "response_time_limit")
            chunk = response.read1(16384)
            if not chunk: break
            size += len(chunk); require(size <= MAX_INPUT_BYTES, "response_size_limit"); chunks.append(chunk)
        require(time.monotonic() - started <= 30, "response_time_limit")
    return b"".join(chunks)


class GDACSAdapter:
    def __init__(self, registry, source):
        validate_source(source); self.registry, self.source = registry, source

    def fetch(self):
        return fetch_gdacs()

    def parse(self, raw, now):
        stamp(now); payload = parse_json(raw)
        require(type(payload) is dict and {"type", "features"} <= set(payload) <= {"type", "features", "bbox"}, "gdacs_collection")
        require(payload["type"] == "FeatureCollection" and type(payload["features"]) is list and
                len(payload["features"]) <= 1000, "gdacs_collection_limit")
        if "bbox" in payload: bbox(payload["bbox"])
        events = []
        for feature in payload["features"]:
            require(type(feature) is dict and {"type", "geometry", "properties"} <= set(feature)
                    <= {"type", "geometry", "properties", "bbox"}, "gdacs_feature")
            require(feature["type"] == "Feature", "gdacs_feature")
            if "bbox" in feature: bbox(feature["bbox"])
            p = feature["properties"]
            require(type(p) is dict and REQUIRED <= set(p) <= PROPERTIES, "gdacs_property_fields")
            typ, ident, episode = p["eventtype"], positive_id(p["eventid"]), positive_id(p["episodeid"])
            require(type(typ) is str and typ in CATEGORIES, "gdacs_category")
            keys(p["url"], {"geometry", "report", "details"})
            for kind in p["url"]: checked_url(p["url"][kind], kind, typ, ident, episode)
            for field in ("name", "description", "eventname", "glide", "country", "source", "sourceid", "polygonlabel", "Class", "countryonland"):
                value = p.get(field)
                require(value is None or type(value) is str, "gdacs_text")
                if value: plain(value, 800)
            require(type(p["iso3"]) is str and (p["iso3"] == "" or re.fullmatch(r"[A-Z]{3}", p["iso3"])), "gdacs_country")
            # HTML and icons are never rendered or followed, even when apparently official.
            for field in ("htmldescription", "icon", "iconoverall"):
                require(p.get(field) is None or (type(p[field]) is str and len(p[field]) <= 20000), "gdacs_unused_text")
            for flag in ("iscurrent", "istemporary"):
                require(type(p[flag]) is str and p[flag] in {"true", "false"}, "gdacs_flags")
            severity = p["severitydata"]; keys(severity, {"severity", "severitytext", "severityunit"})
            require(type(severity["severitytext"]) is str and len(severity["severitytext"]) <= 800, "gdacs_severity_text")
            require(type(severity["severityunit"]) is str, "gdacs_unit")
            unit = plain(severity["severityunit"], 40) if severity["severityunit"] else None
            geo = geometry_summary(feature["geometry"])
            date_values = [source_date(p[k]) for k in ("fromdate", "todate", "datemodified")]
            aware = all(dt is not None for _, dt in date_values)
            data = {"event-type": typ, "gdacs-id": ident, "episode-id": episode,
                "alert-level": p["alertlevel"], "alert-score": number(p["alertscore"], 0, 100),
                "episode-alert-level": p["episodealertlevel"], "episode-alert-score": number(p["episodealertscore"], 0, 100),
                "source-current": p["iscurrent"] == "true", "source-temporary": p["istemporary"] == "true",
                "from-text": date_values[0][0], "to-text": date_values[1][0], "modified-text": date_values[2][0],
                "time-basis": "explicit_offset" if aware else "offset_unspecified",
                "country-contexts": country_contexts(p["affectedcountries"]),
                "country-label": plain(p["country"], 256) if p["country"] else None,
                "geometry-summary": canonical(geo).decode(), "upstream-source": plain(p["source"],256) if p["source"] else None,
                "upstream-id": plain(p["sourceid"],256) if p["sourceid"] else None,
                "severity-measurement": canonical({"value":number(severity["severity"], -2, 1000000000000), "unit":unit}).decode(),
                "tsunami-context": "not_assessed_not_official_warning" if typ == "EQ" else None}
            event = {"schema_version":3,"source_id":SOURCE_ID,"source_event_id":f"{typ}:{ident}:{episode}",
                "record_kind":"incident","category":CATEGORIES[typ],"severity":"unknown","country_code":None,
                "country_codes":[],"region":None,"city":None,"affected_locations":[],
                "geographic_scope":"point" if geo["kind"]=="representative_point" else "uncertain",
                "geographic_basis":"unresolved" if geo["kind"]=="missing" else "source_geometry",
                "starts_at":date_values[0][0] if aware else None,"ends_at":None,"published_at":None,
                "source_published_date":None,"source_updated_at":date_values[2][0] if aware else None,
                "observed_at":stamp(now),"first_observed_at":stamp(now),"last_verified_at":stamp(now),
                "verification_method":"provider_record","review_due_at":stamp(now+timedelta(hours=1)),
                "fresh_until":stamp(now+timedelta(hours=1)),"source_url":event_url("report",typ,ident,episode),
                "source_status":"needs_validation","confidence":"low",
                "confidence_basis":"GDACS potential hazard assessment; source geometry and local traveler impact unverified.",
                "human_review_status":"pending" if data["source-current"] else "needs_reverification",
                "publication_status":"withheld","summary_en":None,
                "traveler_impact":{"status":"unknown","text_en":None,"evidence_urls":[]},"lifecycle_status":"active",
                "audience_nationalities":[],"source_revision":data["modified-text"],"source_severity_raw":data["alert-level"],
                "source_data":data,"related_event_reference":None,"withdrawal_evidence_url":None,
                "provenance":{"adapter_version":ADAPTER_VERSION,"endpoint":FEED,"payload_hash":hashlib.sha256(raw).hexdigest(),
                    "source_generated_at":None,"config_hash":self.registry.config_hash,
                    "licence":self.source["licence"],"licence_url":self.source["licence_url"]}}
            event["event_id"]=event_id(SOURCE_ID,event["source_event_id"]); event["content_hash"]=content_hash(event)
            from .model import validate_event
            validate_event(event,self.registry,now);events.append(event)
        return Batch(SOURCE_ID,None,events,"gdacs_app_selection_partial")
