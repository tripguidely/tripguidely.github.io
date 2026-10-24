"""Bounded USGS summary adapter. Measurements never authorize public alerts."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import re
import time
from urllib.request import Request, build_opener

from .model import content_hash, event_id
from .providers import Batch, NoRedirect
from .validation import (MAX_INPUT_BYTES, UTC, keys, parse_json, plain, require, stamp, instant)

ADAPTER_VERSION = "usgs-summary-v1"
FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
DOCUMENTATION = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php"
LICENCE = "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits"
EVENT_BASE = "https://earthquake.usgs.gov/earthquakes/eventpage/"
DETAIL_BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/"
ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
PROPERTIES = {"mag", "place", "time", "updated", "tz", "url", "detail", "felt", "cdi", "mmi",
              "alert", "status", "tsunami", "sig", "net", "code", "ids", "sources", "types",
              "nst", "dmin", "rms", "gap", "magType", "type", "title"}
REQUIRED = {"mag", "place", "time", "updated", "url", "detail", "status", "tsunami",
            "net", "code", "ids", "magType", "type"}
DATA_FIELDS = {"magnitude", "magnitude-type", "longitude", "latitude", "depth-km", "place",
               "review-status", "tsunami-flag", "pager-alert", "aliases", "detail-url"}


def validate_source(source):
    require(source["adapter"] == ADAPTER_VERSION and source["source_id"] == "usgs-earthquakes" and
            source["endpoint"] == FEED and
            source["documentation_url"] == DOCUMENTATION and source["licence_url"] == LICENCE,
            "usgs_source_contract")
    require(set(source["allowed_urls"]) == {FEED, DOCUMENTATION, LICENCE} and
            source["countries"] == [] and source["country_slugs"] == {} and
            source["audience_nationalities"] == [], "usgs_worldwide_contract")
    require(all(source[k] == 1 and type(source[k]) is int for k in
                ("max_export_age_hours", "freshness_hours", "review_hours")), "usgs_time_policy")


def number(value, minimum, maximum):
    require(type(value) in (int, float) and minimum <= value <= maximum, "usgs_number")
    # Decimal text retains source precision without relaxing the V3 scalar model.
    text = format(Decimal(str(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def milliseconds(value):
    require(type(value) is int and 0 <= value <= 4102444800000, "usgs_timestamp")
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=value)


def identifier(value):
    require(type(value) is str and ID.fullmatch(value), "usgs_identifier")
    return value


def aliases(value, ident):
    require(type(value) is str and len(value) <= 800 and value.startswith(",") and value.endswith(","),
            "usgs_aliases")
    values = value[1:-1].split(",")
    require(1 <= len(values) <= 100 and len(set(values)) == len(values) and ident in values, "usgs_aliases")
    for item in values:
        identifier(item)
    return "," + ",".join(sorted(values)) + ","


def validate_usgs_event(event, source, now):
    """Also validate persisted observations; recomputing a hash cannot forge impact."""
    validate_source(source)
    ident = identifier(event["source_event_id"])
    require(event["source_url"] == EVENT_BASE + ident, "usgs_event_url")
    require(event["record_kind"] == "incident" and event["category"] == "earthquake" and
            event["severity"] == "unknown" and event["geographic_scope"] == "point" and
            event["geographic_basis"] == "source_geometry" and event["country_codes"] == [] and
            event["country_code"] is None and event["city"] is None and event["region"] is None and
            event["affected_locations"] == [], "usgs_no_inferred_impact")
    require(event["source_status"] in {"observed", "unverifiable"} and event["ends_at"] is None and
            event["published_at"] is None and event["source_published_date"] is None and
            event["withdrawal_evidence_url"] is None and event["related_event_reference"] is None,
            "usgs_no_inferred_resolution")
    data = event["source_data"]
    keys(data, DATA_FIELDS)
    for key, lo, hi in (("longitude", -180, 180), ("latitude", -90, 90), ("depth-km", -100, 1000),
                        ("magnitude", -2, 10)):
        value = data[key]
        if key == "magnitude" and value is None:
            continue
        require(type(value) is str and len(value) <= 64 and
                re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value), "usgs_measurement_text")
        numeric = Decimal(value)
        require(lo <= numeric <= hi, "usgs_measurement_range")
    require(type(data["review-status"]) is str and data["review-status"] in {"automatic", "reviewed"}, "usgs_review_status")
    require(type(data["tsunami-flag"]) is int and data["tsunami-flag"] in (0, 1), "usgs_tsunami_flag")
    require(data["pager-alert"] is None or (type(data["pager-alert"]) is str and
            data["pager-alert"] in {"green", "yellow", "orange", "red"}), "usgs_pager")
    require(data["detail-url"] == DETAIL_BASE + ident + ".geojson", "usgs_detail_url")
    require(aliases(data["aliases"], ident) == data["aliases"], "usgs_alias_order")
    require(data["magnitude-type"] is None or (type(data["magnitude-type"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,16}", data["magnitude-type"])),
            "usgs_magnitude_type")
    if data["place"] is not None:
        require(plain(data["place"], 256) == data["place"], "usgs_place")
    occurred, updated = instant(event["starts_at"]), instant(event["source_updated_at"])
    generated = instant(event["provenance"]["source_generated_at"])
    require(occurred <= updated <= generated + timedelta(minutes=10) and
            occurred <= generated + timedelta(minutes=10), "usgs_event_clock")
    require(updated <= now + timedelta(minutes=10), "usgs_event_clock")
    require(event["source_revision"] == stamp(updated), "usgs_revision")
    require(event["provenance"]["adapter_version"] == ADAPTER_VERSION and
            event["source_severity_raw"] == "M " + (data["magnitude"] or "unknown"), "usgs_provenance")
    require(instant(event["fresh_until"]) <= generated + timedelta(hours=1), "usgs_freshness")


def fetch_usgs():
    """One fixed anonymous GET; no retry, redirects, detail fetches or credentials."""
    request = Request(FEED, headers={"Accept": "application/geo+json, application/json",
        "Accept-Encoding": "identity",
        "User-Agent": "TripGuidelyTravelMonitor/3-local (+https://tripguidely.github.io/contact/)"})
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        require(response.status == 200 and response.geturl() == FEED, "unexpected_http_response")
        require(response.headers.get_content_type() in {"application/json", "application/geo+json"},
                "unexpected_content_type")
        require(response.headers.get("Content-Encoding", "identity") == "identity", "unexpected_encoding")
        chunks, size = [], 0
        while True:
            require(time.monotonic() - started <= 30, "response_time_limit")
            chunk = response.read1(16384)
            if not chunk:
                break
            size += len(chunk)
            require(size <= MAX_INPUT_BYTES, "response_size_limit")
            chunks.append(chunk)
        require(time.monotonic() - started <= 30, "response_time_limit")
    return b"".join(chunks)


class USGSAdapter:
    def __init__(self, registry, source):
        validate_source(source)
        self.registry, self.source = registry, source

    def fetch(self):
        return fetch_usgs()

    def parse(self, raw, now):
        stamp(now)
        payload = parse_json(raw)
        require(type(payload) is dict and {"type", "metadata", "features"} <= set(payload) and
                set(payload) <= {"type", "metadata", "features", "bbox"}, "usgs_collection_fields")
        require(payload["type"] == "FeatureCollection", "usgs_collection_type")
        meta = payload["metadata"]
        keys(meta, {"generated", "url", "title", "status", "api", "count"})
        generated = milliseconds(meta["generated"])
        require(now - timedelta(hours=1) <= generated <= now + timedelta(minutes=10), "stale_or_future_export")
        require(meta["url"] == FEED and type(meta["status"]) is int and meta["status"] == 200,
                "usgs_metadata_endpoint")
        plain(meta["title"], 200); plain(meta["api"], 32)
        features = payload["features"]
        require(type(features) is list and type(meta["count"]) is int and
                meta["count"] == len(features) <= 1000, "usgs_collection_count")
        if "bbox" in payload:
            box = payload["bbox"]
            require(type(box) is list and len(box) == 6, "usgs_bbox")
            for offset, lo, hi in ((0, -180, 180), (1, -90, 90), (2, -100, 1000)):
                number(box[offset], lo, hi); number(box[offset+3], lo, hi)
                require(box[offset] <= box[offset+3], "usgs_bbox_order")
        events = []
        for feature in features:
            keys(feature, {"type", "properties", "geometry", "id"})
            require(feature["type"] == "Feature", "usgs_feature_type")
            ident = identifier(feature["id"])
            props = feature["properties"]
            require(type(props) is dict and REQUIRED <= set(props) <= PROPERTIES, "usgs_property_fields")
            require(props["type"] == "earthquake", "usgs_not_earthquake")
            occurred, updated = milliseconds(props["time"]), milliseconds(props["updated"])
            require(generated - timedelta(days=7, minutes=10) <= occurred <= updated
                    <= generated + timedelta(minutes=10), "usgs_event_clock")
            require(props["url"] == EVENT_BASE + ident and
                    props["detail"] == DETAIL_BASE + ident + ".geojson", "usgs_event_url")
            require(type(props["net"]) is str and re.fullmatch(r"[a-z0-9]{1,8}", props["net"]), "usgs_network")
            identifier(props["code"])
            require(ident == props["net"] + props["code"], "usgs_preferred_id")
            geometry = feature["geometry"]
            keys(geometry, {"type", "coordinates"})
            require(geometry["type"] == "Point" and type(geometry["coordinates"]) is list and
                    len(geometry["coordinates"]) == 3, "usgs_geometry")
            lon, lat, depth = geometry["coordinates"]
            data = {"longitude": number(lon, -180, 180), "latitude": number(lat, -90, 90),
                    "depth-km": number(depth, -100, 1000),
                    "magnitude": None if props["mag"] is None else number(props["mag"], -2, 10),
                    "magnitude-type": props["magType"], "place": None if props["place"] is None else plain(props["place"], 256),
                    "review-status": props["status"], "tsunami-flag": props["tsunami"],
                    "pager-alert": props.get("alert"), "aliases": aliases(props["ids"], ident),
                    "detail-url": props["detail"]}
            for field, lo, hi in (("felt", 0, 1000000000), ("nst", 0, 1000000), ("sig", 0, 100000),
                                  ("tz", -1440, 1440)):
                value = props.get(field)
                if value is not None:
                    require(type(value) is int, "usgs_integer")
                    number(value, lo, hi)
            for field, lo, hi in (("cdi", 0, 12), ("mmi", 0, 12), ("gap", 0, 360),
                                  ("dmin", 0, 180), ("rms", 0, 1000)):
                if props.get(field) is not None:
                    number(props[field], lo, hi)
            for field in ("sources", "types", "title"):
                if props.get(field) is not None:
                    plain(props[field], 800)
            event = {"schema_version": 3, "source_id": self.source["source_id"], "source_event_id": ident,
                "record_kind": "incident", "category": "earthquake", "severity": "unknown",
                "country_code": None, "country_codes": [], "region": None, "city": None,
                "affected_locations": [], "geographic_scope": "point", "geographic_basis": "source_geometry",
                "starts_at": stamp(occurred), "ends_at": None, "published_at": None,
                "source_published_date": None, "source_updated_at": stamp(updated),
                "observed_at": stamp(now), "first_observed_at": stamp(now), "last_verified_at": stamp(now),
                "verification_method": "provider_record", "review_due_at": stamp(now + timedelta(hours=1)),
                "fresh_until": stamp(min(generated, now) + timedelta(hours=1)),
                "source_url": props["url"], "source_status": "observed", "confidence": "medium",
                "confidence_basis": "USGS point measurement only; country, destination and traveler impact unverified.",
                "human_review_status": "pending", "publication_status": "withheld", "summary_en": None,
                "traveler_impact": {"status": "unknown", "text_en": None, "evidence_urls": []},
                "lifecycle_status": "active", "audience_nationalities": [], "source_revision": stamp(updated),
                "source_severity_raw": "M " + (data["magnitude"] or "unknown"), "source_data": data,
                "related_event_reference": None, "withdrawal_evidence_url": None,
                "provenance": {"adapter_version": ADAPTER_VERSION, "endpoint": FEED,
                    "payload_hash": hashlib.sha256(raw).hexdigest(), "source_generated_at": stamp(generated),
                    "config_hash": self.registry.config_hash, "licence": self.source["licence"],
                    "licence_url": self.source["licence_url"]}}
            event["event_id"] = event_id(event["source_id"], ident)
            event["content_hash"] = content_hash(event)
            from .model import validate_event
            validate_event(event, self.registry, now)
            events.append(event)
        return Batch(self.source["source_id"], stamp(generated), events, "worldwide_earthquakes_rolling_7_days")
