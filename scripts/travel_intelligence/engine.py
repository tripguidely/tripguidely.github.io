"""Shadow-only orchestration with independent source and persistence outcomes."""
from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
from urllib.error import HTTPError, URLError

from .model import candidate_groups, compare, lifecycle, validate_event
from .storage import StoreError
from .validation import ValidationError, digest, instant, require, stamp

SAFE_SOURCE_CODES = {"malformed_json", "duplicate_json_key", "nonfinite_json_number",
                     "json_size_limit", "json_too_deep", "stale_or_future_export",
                     "country_code_mismatch", "country_slug_mismatch", "country_content_missing",
                     "canada_schema_mismatch", "unknown_advisory_level", "redirect_refused",
                     "unexpected_http_response", "unexpected_content_type", "unexpected_encoding",
                     "response_time_limit", "response_size_limit", "conflicting_duplicate"}


def source_error(exc):
    if isinstance(exc, HTTPError):
        return "http_" + str(exc.code) if exc.code in (400, 401, 403, 404, 429, 500, 502, 503) else "http_error"
    if isinstance(exc, ValidationError) and str(exc) in SAFE_SOURCE_CODES:
        return str(exc)
    return "source_unavailable" if isinstance(exc, (OSError, URLError, TimeoutError)) else "invalid_source_data"


class Monitor:
    def __init__(self, registry, store, adapters):
        require(set(adapters) == set(registry.sources), "adapter_registry_mismatch")
        self.registry, self.store, self.adapters = registry, store, adapters

    def run(self, now, reader=None):
        stamp(now)  # Reject naive clock before touching state or network.
        snapshot = self.store.load(now)
        before = snapshot.data
        if before["last_run_at"] is not None and instant(before["last_run_at"]) > now:
            raise StoreError("clock_rollback")
        events = {e["event_id"]: deepcopy(e) for e in before["events"]}
        source_states, changes, diagnostics = {}, [], []
        duplicate_count = 0
        for ident, source in self.registry.sources.items():
            old_source = before["sources"].get(ident, {})
            old_events = [e for e in before["events"] if e["source_id"] == ident]
            if old_source.get("last_success_at") and now - instant(old_source["last_success_at"]) > timedelta(
                    hours=source["freshness_hours"]):
                diagnostics.append({"kind": "insufficient_coverage", "source_id": ident,
                                    "code": "monitoring_gap_history_not_recoverable"})
            try:
                adapter = self.adapters[ident]
                raw = reader(ident) if reader is not None else adapter.fetch()
                batch = adapter.parse(raw, now)
                require(batch.source_id == ident and batch.coverage == "country_advisories_only",
                        "batch_identity_or_coverage")
                require(type(batch.events) is list and len(batch.events) <= 1000, "batch_limit")
                require(instant(batch.generated_at) <= now + timedelta(minutes=10), "future_batch")
                for event in batch.events:
                    require(event["source_id"] == ident and
                            event["provenance"]["config_hash"] == self.registry.config_hash,
                            "batch_event_source")
                    validate_event(event, self.registry, now)
                seen, source_changes, duplicates = compare(old_events, batch.events, self.registry, now)
                missing = [e for e in old_events if e["event_id"] not in seen]
                for event in missing:
                    # A rolling feed omission is not a withdrawal or an all-clear.
                    if events[event["event_id"]]["source_status"] != "unverifiable":
                        changes.append({"event_id": event["event_id"], "kind": "insufficient_coverage"})
                    events[event["event_id"]]["source_status"] = "unverifiable"
                if missing:
                    diagnostics.append({"kind": "insufficient_coverage", "source_id": ident,
                                        "code": "records_missing_not_withdrawn"})
                events.update(seen)
                changes.extend(source_changes)
                duplicate_count += duplicates
                source_states[ident] = {"status": "checked", "last_attempt_at": stamp(now),
                    "last_success_at": stamp(now), "source_generated_at": batch.generated_at, "error_code": None}
                if old_source.get("status") == "unavailable":
                    changes.append({"source_id": ident, "kind": "source_recovered"})
            except (ValueError, TypeError, KeyError, OSError, URLError, RecursionError) as exc:
                code = source_error(exc)
                source_states[ident] = {"status": "unavailable", "last_attempt_at": stamp(now),
                    "last_success_at": old_source.get("last_success_at"),
                    "source_generated_at": old_source.get("source_generated_at"), "error_code": code}
                if old_source.get("status") != "unavailable" or old_source.get("error_code") != code:
                    changes.append({"source_id": ident, "kind": "source_unavailable", "code": code})
                diagnostics.append({"kind": "source_unavailable", "source_id": ident, "code": code})
                for old in old_events:
                    events[old["event_id"]]["source_status"] = "unverifiable"
        previous_by_id = {e["event_id"]: e for e in before["events"]}
        for event in events.values():
            state = lifecycle(event, now)
            old = previous_by_id.get(event["event_id"])
            if old and old["lifecycle_status"] != state:
                changes.append({"event_id": event["event_id"], "kind": state})
            event["lifecycle_status"] = state
        ordered = sorted(events.values(), key=lambda e: e["event_id"])
        next_state = {"schema_version": 3, "config_hash": self.registry.config_hash,
                      "last_run_at": stamp(now), "events": ordered, "sources": source_states}
        report = {"schema_version": 3, "mode": "local_shadow", "generated_at": stamp(now),
                  "run_id": digest([self.registry.config_hash, stamp(now), snapshot.token]),
                  "config_hash": self.registry.config_hash, "coverage": "partial",
                  "coverage_statement": "Canadian national advisory changes only; local conditions not verified.",
                  "status": "verification_required" if any(s["status"] == "unavailable" for s in source_states.values())
                            else "monitoring_partial",
                  "initial_observation": snapshot.token is None, "safety_conclusion": None,
                  "publication_authorized": False, "automatic_publication": False,
                  "sources": source_states, "events": ordered, "changes": changes,
                  "diagnostics": diagnostics, "duplicates_in_batch": duplicate_count,
                  "candidate_duplicate_groups": candidate_groups(ordered),
                  "destination_contexts": {e["event_id"]: self.registry.contexts(e) for e in ordered},
                  "pending_review": [e["event_id"] for e in ordered],
                  "no_change": bool(snapshot.token) and not changes and not diagnostics
                               and all(s["status"] == "checked" for s in source_states.values()),
                  "persistence": {"committed": False, "previous_generation": snapshot.generation,
                                  "generation": None, "token": None, "error_code": None}}
        try:
            committed = self.store.commit(next_state, snapshot.token, now)
            report["persistence"].update(committed=True, generation=committed.generation, token=committed.token)
        except (StoreError, OSError, ValidationError, TypeError, KeyError):
            report["status"] = "verification_required"
            report["persistence"]["error_code"] = "persistence_failed"
            report["no_change"] = False
            report["diagnostics"].append({"kind": "insufficient_coverage", "code": "persistence_failed"})
        return report
