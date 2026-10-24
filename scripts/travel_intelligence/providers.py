"""Provider contract. Canada is default; USGS requires its explicit local profile."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import time
from typing import Protocol
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .model import content_hash, event_id
from .validation import (MAX_INPUT_BYTES, UTC, ValidationError, parse_json, plain,
                         require, stamp)

FEED = "https://data.international.gc.ca/travel-voyage/index-alpha-eng.json"
ADAPTER_VERSION = "canada-index-v1"
RISK = {"Exercise normal security precautions", "Exercise a high degree of caution",
        "Avoid non-essential travel", "Avoid all travel"}


@dataclass(frozen=True)
class Batch:
    source_id: str
    generated_at: str | None
    events: list[dict]
    coverage: str = "country_advisories_only"


class Adapter(Protocol):
    """Future providers implement this contract; no imports from remote config."""
    def parse(self, raw: bytes, now: datetime) -> Batch: ...
    def fetch(self) -> bytes: ...


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValidationError("redirect_refused")


def fetch_canada():
    """One fixed GET, no retry, cookie, auth, compression or redirects."""
    request = Request(FEED, headers={
        "User-Agent": "TripGuidelyTravelMonitor/3-local (+https://tripguidely.github.io/contact/)",
        "Accept": "application/json", "Accept-Encoding": "identity",
    })
    started = time.monotonic()
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        require(response.status == 200 and response.geturl() == FEED, "unexpected_http_response")
        require(response.headers.get_content_type() == "application/json", "unexpected_content_type")
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


class CanadaAdapter:
    def __init__(self, registry, source):
        self.registry, self.source = registry, source
        require(source["adapter"] == ADAPTER_VERSION and source["endpoint"] == FEED,
                "adapter_endpoint_not_supported")
        require(source["audience_nationalities"] == ["CA"], "canadian_advisory_audience")
        for code in source["countries"]:
            require("https://travel.gc.ca/destinations/" + source["country_slugs"][code]
                    in source["allowed_urls"], "country_url_not_allowlisted")

    def fetch(self):
        return fetch_canada()

    def parse(self, raw, now):
        payload = parse_json(raw)
        try:
            generated_ts = payload["metadata"]["generated"]["timestamp"]
            require(type(generated_ts) is int, "invalid_generated_timestamp")
            generated = datetime.fromtimestamp(generated_ts, UTC)
            require(now - timedelta(hours=self.source["max_export_age_hours"]) <= generated
                    <= now + timedelta(minutes=10), "stale_or_future_export")
            data = payload["data"]
            require(type(data) is dict, "invalid_country_collection")
            events = []
            for code in self.source["countries"]:
                entry = data[code]
                require(entry["country-iso"] == code, "country_code_mismatch")
                require(entry["eng"]["url-slug"] == self.source["country_slugs"][code],
                        "country_slug_mismatch")
                ts = entry["date-published"]["timestamp"]
                require(type(ts) is int, "invalid_publication_timestamp")
                published = datetime.fromtimestamp(ts, UTC)
                require(published <= generated + timedelta(minutes=10), "publication_after_export")
                for flag in ("has-regional-advisory", "has-advisory-warning", "has-content"):
                    require(type(entry[flag]) is int and entry[flag] in (0, 1), "invalid_advisory_flag")
                require(entry["has-content"] == 1, "country_content_missing")
                risk = plain(entry["eng"]["advisory-text"], 160)
                require(risk in RISK | {x + " (with regional advisories)" for x in RISK},
                        "unknown_advisory_level")
                update = plain(entry["eng"]["recent-updates"])
                update_type = plain(entry["recent-updates-type"], 120)
                url = "https://travel.gc.ca/destinations/" + self.source["country_slugs"][code]
                country_id = self.registry.countries[code]
                e = {
                    "schema_version": 3, "source_id": self.source["source_id"],
                    "source_event_id": "country-advisory:" + code, "record_kind": "advisory",
                    "category": "travel_advisory", "severity": "informational",
                    "country_code": code, "country_codes": [code], "region": None, "city": None,
                    "affected_locations": [{"location_id": country_id, "location_kind": "country",
                        "source_label": self.registry.destinations[country_id]["name_en"],
                        "relationship": "country_context", "evidence_url": url, "geometry_ref": None}],
                    "geographic_scope": "country", "geographic_basis": "source_explicit",
                    "starts_at": None, "ends_at": None, "published_at": stamp(published),
                    "source_published_date": None, "source_updated_at": None,
                    "observed_at": stamp(now), "first_observed_at": stamp(now),
                    "last_verified_at": stamp(now), "verification_method": "provider_record",
                    "review_due_at": stamp(now + timedelta(hours=self.source["review_hours"])),
                    "fresh_until": stamp(min(generated + timedelta(hours=self.source["max_export_age_hours"]),
                                             now + timedelta(hours=self.source["freshness_hours"]))),
                    "source_url": url, "source_status": "observed", "confidence": "high",
                    "confidence_basis": "Structured country bulletin extracted; local impact not established.",
                    "human_review_status": "pending", "publication_status": "withheld", "summary_en": None,
                    "traveler_impact": {"status": "unknown", "text_en": None, "evidence_urls": []},
                    "lifecycle_status": "active", "audience_nationalities": ["CA"],
                    "source_revision": None, "source_severity_raw": risk,
                    "source_data": {"risk": risk, "update-summary": update, "update-type": update_type,
                                    "regional-advisory": entry["has-regional-advisory"],
                                    "advisory-warning": entry["has-advisory-warning"]},
                    "related_event_reference": None, "withdrawal_evidence_url": None,
                    "provenance": {"adapter_version": ADAPTER_VERSION, "endpoint": FEED,
                                   "payload_hash": hashlib.sha256(raw).hexdigest(),
                                   "source_generated_at": stamp(generated),
                                   "config_hash": self.registry.config_hash,
                                   "licence": self.source["licence"], "licence_url": self.source["licence_url"]},
                }
                e["event_id"] = event_id(e["source_id"], e["source_event_id"])
                e["content_hash"] = content_hash(e)
                events.append(e)
            return Batch(self.source["source_id"], stamp(generated), events)
        except (KeyError, TypeError, OverflowError, OSError):
            raise ValidationError("canada_schema_mismatch") from None


def adapters_for(registry):
    result = {}
    for ident, source in registry.sources.items():
        if source["adapter"] == "gdacs-events-v1":
            from .gdacs import GDACSAdapter
            result[ident] = GDACSAdapter(registry, source)
        elif source["adapter"] == "usgs-summary-v1":
            from .usgs import USGSAdapter
            result[ident] = USGSAdapter(registry, source)
        else:
            require(source["adapter"] == ADAPTER_VERSION, "adapter_not_enabled")
            result[ident] = CanadaAdapter(registry, source)
    return result
