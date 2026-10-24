"""Closed observation model. Collection can never authorize publication."""
from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import re

from .validation import (canonical, country, digest, instant, keys, official_url,
                         plain, require, slug, stamp)

CATEGORIES = {"drought", "wildfire", "public_health", "earthquake", "volcanic_activity", "tsunami", "flood",
              "severe_weather", "civil_unrest", "security_restriction", "transport_strike",
              "transport_disruption", "planned_works", "travel_advisory", "entry_restriction",
              "destination_access", "other_exceptional"}
SCOPES = {"global", "multi_country", "country", "region", "city", "neighborhood",
          "transport", "point", "uncertain"}
LOCATION_FIELDS = {"location_id", "location_kind", "source_label", "relationship",
                   "evidence_url", "geometry_ref"}
FIELDS = {
    "schema_version", "event_id", "source_id", "source_event_id", "record_kind", "category",
    "severity", "country_code", "country_codes", "region", "city", "affected_locations",
    "geographic_scope", "geographic_basis", "starts_at", "ends_at", "published_at",
    "source_published_date", "first_observed_at", "observed_at", "last_verified_at",
    "verification_method", "review_due_at", "fresh_until", "source_url", "source_status",
    "confidence", "confidence_basis", "human_review_status", "publication_status", "summary_en",
    "traveler_impact", "lifecycle_status", "audience_nationalities", "source_revision",
    "source_updated_at", "source_severity_raw", "source_data", "content_hash", "provenance",
    "related_event_reference", "withdrawal_evidence_url",
}
SEMANTIC_FIELDS = {
    "source_id", "source_event_id", "record_kind", "category", "severity", "country_code",
    "country_codes", "region", "city", "affected_locations", "geographic_scope",
    "geographic_basis", "starts_at", "ends_at", "published_at", "source_published_date",
    "source_url", "source_severity_raw", "source_data", "audience_nationalities",
    "source_revision", "source_updated_at", "related_event_reference", "withdrawal_evidence_url",
}


def event_id(source_id, source_event_id):
    return "gti-" + digest([source_id, source_event_id])


def content_hash(event):
    return digest({k: event[k] for k in sorted(SEMANTIC_FIELDS)})


def lifecycle(event, now):
    if event["source_status"] == "withdrawn":
        return "withdrawn"
    if event["ends_at"] and instant(event["ends_at"]) <= now:
        return "expired"
    if instant(event["fresh_until"]) <= now:
        return "expired"
    if instant(event["review_due_at"]) <= now:
        return "review_overdue"
    if event["source_status"] == "unverifiable":
        return "unverifiable"
    return "active"


def validate_event(event, registry, now):
    keys(event, FIELDS)
    require(type(event["schema_version"]) is int and event["schema_version"] == 3, "event_schema")
    source = registry.sources.get(slug(event["source_id"]))
    require(source is not None, "unknown_event_source")
    plain(event["source_event_id"], 256)
    require(event["event_id"] == event_id(event["source_id"], event["source_event_id"]), "event_identity")
    require(event["record_kind"] in {"advisory", "incident", "publication_notice"}, "record_kind")
    require(event["category"] in CATEGORIES, "category")
    require(event["severity"] in {"unknown", "informational", "minor", "moderate", "major", "critical"},
            "severity")
    codes = event["country_codes"]
    require(type(codes) is list and len(codes) == len(set(codes)) <= 64, "event_countries")
    for code in codes:
        country(code)
        require(code in registry.countries and code in source["countries"], "unconfigured_country")
    require(event["country_code"] == (codes[0] if len(codes) == 1 else None), "primary_country")
    require(event["geographic_scope"] in SCOPES, "geographic_scope")
    require(event["geographic_basis"] in {"source_explicit", "source_geometry", "reviewed_mapping", "unresolved"},
            "geographic_basis")
    if event["geographic_scope"] == "country":
        require(len(codes) == 1 and event["city"] is None and event["region"] is None,
                "national_is_not_local")
    if event["geographic_scope"] == "multi_country":
        require(len(codes) > 1, "multi_country_scope")
    for field, kind in (("region", "region"), ("city", "city")):
        ident = event[field]
        if ident is not None:
            d = registry.destinations.get(ident)
            require(d is not None and d["kind"] == kind and d["country_code"] in codes,
                    "event_location_mismatch")
    if event["geographic_scope"] == "city":
        require(event["city"] is not None, "city_scope_requires_id")
    if event["geographic_scope"] == "region":
        require(event["region"] is not None, "region_scope_requires_id")
    if event["city"] is not None:
        require(event["geographic_scope"] in {"city", "neighborhood", "transport", "point"}
                and event["geographic_basis"] != "unresolved", "city_requires_evidence")
        if event["region"] is not None:
            ancestor = registry.destinations[event["city"]]
            parents = set()
            while ancestor["parent_id"] is not None:
                parents.add(ancestor["parent_id"])
                ancestor = registry.destinations[ancestor["parent_id"]]
            require(event["region"] in parents, "city_region_mismatch")
    if event["geographic_scope"] in {"uncertain", "global", "multi_country"}:
        require(event["city"] is None and event["region"] is None, "uncertain_locality")
    locations = event["affected_locations"]
    require(type(locations) is list and len(locations) <= 200, "affected_locations")
    for loc in locations:
        keys(loc, LOCATION_FIELDS)
        require(loc["location_kind"] in {"country", "region", "city", "neighborhood", "airport",
                "transport_zone", "station", "route", "poi", "unknown"}, "location_kind")
        require(loc["relationship"] in {"explicitly_affected", "country_context", "potential_overlap", "unknown"},
                "location_relationship")
        plain(loc["source_label"], 120)
        official_url(loc["evidence_url"], source["allowed_urls"])
        # No geometry engine is enabled in Phase 1; explicit registry IDs only.
        require(loc["geometry_ref"] is None, "geometry_not_enabled")
        if loc["location_id"] is not None:
            d = registry.destinations.get(loc["location_id"])
            require(d is not None and d["kind"] == loc["location_kind"]
                    and d["country_code"] in codes, "affected_location_mismatch")
        if event["geographic_scope"] == "country":
            require(loc["location_kind"] == "country" and loc["relationship"] == "country_context",
                    "national_is_not_local")
        if event["city"] is not None and loc["location_kind"] == "city":
            require(loc["location_id"] == event["city"], "conflicting_city_evidence")
    for field in ("first_observed_at", "observed_at", "review_due_at", "fresh_until"):
        instant(event[field])
    for field in ("starts_at", "ends_at", "published_at", "last_verified_at", "source_updated_at"):
        if event[field] is not None:
            instant(event[field])
    require(instant(event["first_observed_at"]) <= instant(event["observed_at"]) <= now + timedelta(minutes=5),
            "observation_clock")
    if event["last_verified_at"]:
        require(instant(event["last_verified_at"]) <= instant(event["observed_at"]), "verification_clock")
    if event["published_at"]:
        require(instant(event["published_at"]) <= now + timedelta(minutes=10), "future_publication")
    if event["starts_at"] and event["ends_at"]:
        require(instant(event["starts_at"]) < instant(event["ends_at"]), "event_interval")
    require(event["ends_at"] is None or event["starts_at"] is not None, "end_without_start")
    require(instant(event["review_due_at"]) > instant(event["first_observed_at"])
            and instant(event["review_due_at"]) <= instant(event["observed_at"]) + timedelta(hours=48),
            "review_deadline")
    require(instant(event["fresh_until"]) <= instant(event["observed_at"]) + timedelta(hours=48),
            "freshness_deadline")
    if event["source_published_date"] is not None:
        from datetime import date
        value = event["source_published_date"]
        require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "publication_date")
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError("publication_date") from None
        require(event["published_at"] is None, "date_precision_conflict")
    if source["adapter"] == "gdacs-events-v1":
        from .gdacs import validate_gdacs_event
        validate_gdacs_event(event, source, now)
    elif source["adapter"] == "usgs-summary-v1":
        from .usgs import validate_usgs_event
        validate_usgs_event(event, source, now)
    else:
        official_url(event["source_url"], source["allowed_urls"])
    require(event["source_status"] in {"observed", "officially_confirmed", "needs_validation",
                                      "withdrawn", "unverifiable"}, "source_status")
    if event["withdrawal_evidence_url"] is not None:
        official_url(event["withdrawal_evidence_url"], source["allowed_urls"])
    if event["source_status"] == "withdrawn":
        require(event["withdrawal_evidence_url"] is not None, "withdrawal_requires_evidence")
    require(event["verification_method"] in {None, "provider_record", "human"}, "verification_method")
    require(event["confidence"] in {"unassessed", "low", "medium", "high"}, "confidence")
    plain(event["confidence_basis"], 500)
    require(event["human_review_status"] in {"not_requested", "pending", "rejected", "needs_reverification"},
            "approval_not_implemented")
    require(event["publication_status"] == "withheld" and event["summary_en"] is None,
            "publication_disabled_in_phase1")
    keys(event["traveler_impact"], {"status", "text_en", "evidence_urls"})
    require(event["traveler_impact"] == {"status": "unknown", "text_en": None, "evidence_urls": []},
            "impact_review_not_implemented")
    require(event["severity"] in {"unknown", "informational"}, "impact_review_not_implemented")
    require(event["lifecycle_status"] in {"active", "review_overdue", "expired", "withdrawn", "unverifiable"},
            "lifecycle_status")
    require(event["audience_nationalities"] == source["audience_nationalities"], "advisory_audience")
    for field in ("source_revision", "source_severity_raw"):
        if event[field] is not None:
            plain(event[field], 256)
    require(type(event["source_data"]) is dict and len(event["source_data"]) <= 20
            and len(canonical(event["source_data"])) <= 4000, "source_data_size")
    for key, value in event["source_data"].items():
        slug(key)
        if type(value) is str:
            require(plain(value) == value, "source_data_not_normalized")
        else:
            require(type(value) in (int, bool) or value is None, "source_data_scalar_required")
    keys(event["provenance"], {"adapter_version", "endpoint", "payload_hash", "source_generated_at",
                              "config_hash", "licence", "licence_url"})
    p = event["provenance"]
    require(p["endpoint"] == source["endpoint"] and p["licence"] == source["licence"]
            and p["licence_url"] == source["licence_url"], "provenance_mismatch")
    plain(p["adapter_version"], 64)
    for field in ("payload_hash", "config_hash"):
        require(type(p[field]) is str and re.fullmatch(r"[a-f0-9]{64}", p[field]), "provenance_hash")
    if p["source_generated_at"] is None:
        require(source["adapter"] == "gdacs-events-v1", "unknown_export_time_not_supported")
    else:
        require(instant(p["source_generated_at"]) <= instant(event["observed_at"]) + timedelta(minutes=10),
                "future_generation")
    if event["related_event_reference"] is not None:
        official_url(event["related_event_reference"], source["allowed_urls"])
    require(event["content_hash"] == content_hash(event), "content_hash_mismatch")
    return event


def normalize_event(original, registry, now):
    """Validate before normalizing so corrupt hashes cannot be silently repaired."""
    validate_event(original, registry, now)
    event = deepcopy(original)
    for field in ("starts_at", "ends_at", "published_at", "first_observed_at", "observed_at",
                  "last_verified_at", "review_due_at", "fresh_until", "source_updated_at"):
        if event[field] is not None:
            event[field] = stamp(instant(event[field]))
    if event["provenance"]["source_generated_at"] is not None:
        event["provenance"]["source_generated_at"] = stamp(instant(event["provenance"]["source_generated_at"]))
    event["country_codes"] = sorted(event["country_codes"])
    event["affected_locations"] = sorted(event["affected_locations"], key=canonical)
    event["content_hash"] = content_hash(event)
    return validate_event(event, registry, now)


def compare(previous_events, incoming, registry, now):
    """Keep each source's identity; never auto-merge cross-authority claims."""
    previous = {e["event_id"]: e for e in previous_events}
    seen, changes, duplicates = {}, [], 0
    for original in incoming:
        event = normalize_event(original, registry, now)
        ident = event["event_id"]
        if ident in seen:
            require(seen[ident]["content_hash"] == event["content_hash"], "conflicting_duplicate")
            duplicates += 1
            continue
        old = previous.get(ident)
        kind = "initial_observation" if not previous_events else "new_information"
        if old:
            require(instant(event["observed_at"]) >= instant(old["observed_at"]), "clock_rollback")
            if registry.sources[event["source_id"]]["adapter"] == "usgs-summary-v1":
                require(instant(event["source_updated_at"]) >= instant(old["source_updated_at"]),
                        "usgs_revision_rollback")
                require(event["source_updated_at"] != old["source_updated_at"] or
                        event["content_hash"] == old["content_hash"], "usgs_revision_conflict")
            if registry.sources[event["source_id"]]["adapter"] == "gdacs-events-v1":
                from .gdacs import validate_revision
                validate_revision(old, event)
            event["first_observed_at"] = old["first_observed_at"]
            if old["content_hash"] == event["content_hash"]:
                kind = "no_change"
                event["review_due_at"] = old["review_due_at"]
                event["human_review_status"] = old["human_review_status"]
            else:
                kind = ("source_revised" if registry.sources[event["source_id"]]["adapter"] in
                        {"usgs-summary-v1", "gdacs-events-v1"}
                        else "severity_changed" if old["source_severity_raw"] != event["source_severity_raw"]
                        else "new_information")
                event["human_review_status"] = "needs_reverification"
        event["lifecycle_status"] = lifecycle(event, now)
        validate_event(event, registry, now)
        seen[ident] = event
        if kind != "no_change":
            changes.append({"event_id": ident, "kind": kind})
    return seen, changes, duplicates


def candidate_groups(events):
    """Exact shared official reference + precise identical scope/time; review only."""
    groups = {}
    for e in events:
        if (e["record_kind"] != "incident" or e["geographic_scope"] in {"uncertain", "global", "multi_country"}
                or not e["related_event_reference"] or not e["starts_at"]):
            continue
        key = digest([e["related_event_reference"], e["category"], e["country_codes"],
                      e["region"], e["city"], e["geographic_scope"], e["starts_at"], e["ends_at"]])
        groups.setdefault(key, []).append(e)
    return [{"candidate_group_id": key, "event_ids": sorted(e["event_id"] for e in values),
             "needs_human_review": True, "merged": False}
            for key, values in sorted(groups.items()) if len({e["source_id"] for e in values}) > 1]
