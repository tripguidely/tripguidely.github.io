"""Deterministic V3 tests. Synthetic data; network access is mocked throughout."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import Message
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from travel_intelligence.engine import Monitor
from travel_intelligence.model import candidate_groups, compare, content_hash, event_id, lifecycle, validate_event
from travel_intelligence.providers import Batch, CanadaAdapter, FEED, NoRedirect, adapters_for, fetch_canada
from travel_intelligence.registry import Registry
from travel_intelligence.reporting import markdown, write_report
from travel_intelligence.storage import ConflictError, LocalStateStore, StoreError
from travel_intelligence.validation import (MAX_INPUT_BYTES, ValidationError, canonical, digest,
                                           instant, load_json, local_time, parse_json,
                                           safe_external_directory, stamp)

FIXTURE = ROOT / "tests/fixtures/travel-intelligence/canada-pilot-synthetic.json"
NOW = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)


def configuration():
    return (load_json(ROOT / "config/travel-intelligence/destinations.json"),
            load_json(ROOT / "config/travel-intelligence/sources.json"))


def fixture(**changes):
    data = load_json(FIXTURE)
    for key, value in changes.items():
        data["data"]["FR"]["eng"][key] = value
    return canonical(data)


def incident(event, city="fr-paris", reference=True):
    e = deepcopy(event)
    e.update(record_kind="incident", category="earthquake", geographic_scope="city" if city else "uncertain",
             geographic_basis="source_explicit" if city else "unresolved", city=city,
             starts_at=stamp(NOW - timedelta(hours=1)), ends_at=None,
             related_event_reference=e["source_url"] if reference else None)
    if city:
        e["affected_locations"] = [{"location_id": city, "location_kind": "city", "source_label": "Synthetic city",
            "relationship": "explicitly_affected", "evidence_url": e["source_url"], "geometry_ref": None}]
    else:
        e.update(country_code=None, country_codes=[], affected_locations=[], confidence="low")
    e["content_hash"] = content_hash(e)
    return e


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gti-v3-tests-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = Registry(*configuration())
        self.store = LocalStateStore(self.directory / "state", self.registry, ROOT)
        self.adapters = adapters_for(self.registry)
        self.ident = "ca-travel-advisories"

    def run_monitor(self, raw=None, now=NOW, reader=None, store=None):
        return Monitor(self.registry, store or self.store, self.adapters).run(
            now, reader or (lambda _: raw if raw is not None else fixture()))

    def events(self):
        return self.adapters[self.ident].parse(fixture(), NOW).events

    def test_four_countries_one_collection_never_local_incidents(self):
        read = MagicMock(return_value=fixture())
        report = self.run_monitor(reader=read)
        self.assertEqual(read.call_count, 1)
        self.assertEqual({e["country_code"] for e in report["events"]}, {"FR", "GB", "IT", "US"})
        for event in report["events"]:
            self.assertEqual(event["record_kind"], "advisory")
            self.assertEqual(event["geographic_scope"], "country")
            self.assertIsNone(event["city"])
            self.assertEqual(event["audience_nationalities"], ["CA"])
            self.assertEqual(event["publication_status"], "withheld")
            self.assertIsNone(event["summary_en"])
        self.assertIsNone(report["safety_conclusion"])
        self.assertFalse(report["publication_authorized"])

    def test_multiple_cities_per_country_share_country_context_only(self):
        destinations, sources = configuration()
        destinations["destinations"].append({"destination_id": "fr-lyon", "name_en": "Lyon",
            "kind": "city", "country_code": "FR", "parent_id": "fr", "timezone": "Europe/Paris", "pages": []})
        registry = Registry(destinations, sources)
        event = CanadaAdapter(registry, registry.sources[self.ident]).parse(fixture(), NOW).events[0]
        contexts = registry.contexts(event)
        self.assertEqual({c["destination_id"] for c in contexts}, {"fr-paris", "fr-lyon"})
        self.assertTrue(all(c["relationship"] == "country_context" and not c["local_incident_confirmed"]
                            for c in contexts))

    def test_registry_rejects_cross_country_parent_cycles_unknown_fields_and_publication(self):
        for mutation in ("cross", "cycle", "field", "publish", "timezone"):
            destinations, sources = configuration()
            if mutation == "cross": destinations["destinations"][-1]["parent_id"] = "fr"
            if mutation == "cycle": destinations["destinations"][-1]["parent_id"] = "us-new-york-city"
            if mutation == "field": destinations["destinations"][0]["remote_code"] = "untrusted"
            if mutation == "publish": sources["publication_enabled"] = True
            if mutation == "timezone": destinations["destinations"][-1]["timezone"] = "Invalid/Zone"
            with self.subTest(mutation=mutation), self.assertRaises((ValidationError, ValueError)):
                Registry(destinations, sources)

    def test_city_country_mismatch_and_national_local_promotion_rejected(self):
        for change in ({"city": "fr-paris"}, {"country_code": "IT"}, {"publication_status": "published"},
                       {"human_review_status": "approved"}, {"summary_en": "Unapproved public claim"}):
            event = self.events()[0]
            event.update(change)
            event["content_hash"] = content_hash(event)
            with self.subTest(change=change), self.assertRaises(ValidationError):
                validate_event(event, self.registry, NOW)

    def test_unknown_geography_is_not_associated_with_any_city(self):
        event = incident(self.events()[0], city=None)
        validate_event(event, self.registry, NOW)
        self.assertEqual(self.registry.contexts(event), [])
        self.assertEqual(candidate_groups([event, deepcopy(event)]), [])

    def test_wrong_region_cannot_be_attached_to_rome(self):
        destinations, sources = configuration()
        destinations["destinations"].append({"destination_id": "it-sicily", "name_en": "Sicily",
            "kind": "region", "country_code": "IT", "parent_id": "it", "timezone": "Europe/Rome", "pages": []})
        registry = Registry(destinations, sources)
        event = incident(CanadaAdapter(registry, registry.sources[self.ident]).parse(fixture(), NOW).events[2],
                         city="it-rome")
        event["region"] = "it-sicily"
        event["content_hash"] = content_hash(event)
        with self.assertRaisesRegex(ValidationError, "city_region_mismatch"):
            validate_event(event, registry, NOW)

    def test_expiration_evaluation_requires_no_workflow_or_network(self):
        event = self.events()[0]
        self.assertEqual(lifecycle(event, NOW), "active")
        self.assertEqual(lifecycle(event, NOW + timedelta(days=7)), "expired")
        self.assertEqual(event["publication_status"], "withheld")

    def test_withdrawal_requires_explicit_official_evidence(self):
        event = self.events()[0]
        event["source_status"] = "withdrawn"
        with self.assertRaisesRegex(ValidationError, "withdrawal_requires_evidence"):
            validate_event(event, self.registry, NOW)

    def test_region_event_not_associated_with_rome_without_city_evidence(self):
        event = self.events()[2]
        event.update(record_kind="incident", category="earthquake", geographic_scope="region", region="it-lazio")
        event["content_hash"] = content_hash(event)
        validate_event(event, self.registry, NOW)
        self.assertEqual(self.registry.contexts(event), [])

    def test_identical_second_run_restores_durable_state_without_new_findings(self):
        first = self.run_monitor()
        # New process-like store object, without a cache.
        reloaded = LocalStateStore(self.directory / "state", self.registry, ROOT)
        second = self.run_monitor(now=NOW + timedelta(minutes=10), store=reloaded)
        self.assertTrue(first["initial_observation"])
        self.assertFalse(second["initial_observation"])
        self.assertTrue(second["no_change"])
        self.assertEqual(second["changes"], [])
        self.assertEqual(second["persistence"]["generation"], 2)
        self.assertEqual({e["event_id"] for e in first["events"]}, {e["event_id"] for e in second["events"]})
        self.assertEqual(len(list((self.directory / "state/generations").glob("*.json"))), 2)

    def test_whitespace_export_clock_and_unrelated_country_do_not_trigger_changes(self):
        self.run_monitor()
        data = load_json(FIXTURE)
        data["metadata"]["generated"]["timestamp"] += 30
        data["data"]["XX"] = {"unrelated": "ignored"}
        data["data"]["FR"]["eng"]["recent-updates"] = "  " + data["data"]["FR"]["eng"]["recent-updates"].replace(" ", " \n ")
        report = self.run_monitor(canonical(data), NOW + timedelta(minutes=1))
        self.assertEqual(report["changes"], [])
        self.assertTrue(report["no_change"])

    def test_revision_and_level_changes_have_separate_classifications(self):
        self.run_monitor()
        changed = self.run_monitor(fixture(**{"recent-updates": "Synthetic revision requiring interpretation."}),
                                   NOW + timedelta(minutes=1))
        self.assertEqual([c["kind"] for c in changed["changes"]], ["new_information"])
        level = self.run_monitor(fixture(**{"advisory-text": "Avoid non-essential travel"}), NOW + timedelta(minutes=2))
        self.assertIn("severity_changed", [c["kind"] for c in level["changes"]])
        self.assertTrue(all(e["city"] is None and e["publication_status"] == "withheld" for e in level["events"]))

    def test_source_publication_time_change_is_a_revision_not_a_new_identity(self):
        first = self.run_monitor()
        payload = load_json(FIXTURE)
        payload["data"]["FR"]["date-published"]["timestamp"] += 60
        second = self.run_monitor(canonical(payload), NOW + timedelta(minutes=1))
        self.assertEqual({e["event_id"] for e in first["events"]}, {e["event_id"] for e in second["events"]})
        self.assertEqual(len(second["changes"]), 1)

    def test_equivalent_timestamp_offsets_normalize_without_false_revision(self):
        event = self.events()[0]
        seen, _, _ = compare([], [event], self.registry, NOW)
        changed = deepcopy(event)
        changed["published_at"] = "2026-10-22T13:00:00+02:00"
        changed["content_hash"] = content_hash(changed)
        _, changes, _ = compare(list(seen.values()), [changed], self.registry, NOW)
        self.assertEqual(changes, [])

    def test_same_source_duplicates_consolidate_but_conflicts_fail(self):
        event = self.events()[0]
        seen, changes, duplicates = compare([], [event, deepcopy(event)], self.registry, NOW)
        self.assertEqual((len(seen), len(changes), duplicates), (1, 1, 1))
        other = deepcopy(event)
        other["source_data"]["update-summary"] = "Synthetic conflicting revision."
        other["content_hash"] = content_hash(other)
        with self.assertRaisesRegex(ValidationError, "conflicting_duplicate"):
            compare([], [event, other], self.registry, NOW)

    def test_cross_source_duplicates_are_review_candidates_never_merged(self):
        destinations, sources = configuration()
        mirror = deepcopy(sources["sources"][0])
        mirror["source_id"] = "synthetic-second-source"
        sources["sources"].append(mirror)
        registry = Registry(destinations, sources)
        events = []
        for source in registry.sources.values():
            event = incident(CanadaAdapter(registry, source).parse(fixture(), NOW).events[0])
            validate_event(event, registry, NOW)
            events.append(event)
        groups = candidate_groups(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(len(groups), 1)
        self.assertFalse(groups[0]["merged"])
        self.assertTrue(groups[0]["needs_human_review"])
        events[1]["related_event_reference"] = None
        self.assertEqual(candidate_groups(events), [])

    def test_different_national_authority_observations_never_auto_merge(self):
        event = self.events()[0]
        event["related_event_reference"] = event["source_url"]
        second = deepcopy(event)
        second["source_id"] = "synthetic-other-authority"
        self.assertEqual(candidate_groups([event, second]), [])

    def test_unchanged_poll_does_not_extend_human_review_deadline(self):
        first = self.run_monitor()
        later = self.run_monitor(now=NOW + timedelta(hours=25))
        self.assertEqual({e["event_id"]: e["review_due_at"] for e in first["events"]},
                         {e["event_id"]: e["review_due_at"] for e in later["events"]})
        self.assertTrue(all(e["lifecycle_status"] == "review_overdue" for e in later["events"]))
        self.assertFalse(later["automatic_publication"])

    def test_known_end_expires_without_claim_of_reopening(self):
        event = incident(self.events()[0])
        event["ends_at"] = stamp(NOW - timedelta(minutes=1))
        event["content_hash"] = content_hash(event)
        seen, _, _ = compare([], [event], self.registry, NOW)
        self.assertEqual(next(iter(seen.values()))["lifecycle_status"], "expired")
        self.assertEqual(next(iter(seen.values()))["traveler_impact"]["status"], "unknown")

    def test_failure_retains_last_good_content_and_expires_absolute_freshness(self):
        first = self.run_monitor()
        def unavailable(_): raise URLError("secret must not be logged")
        failed = self.run_monitor(now=NOW + timedelta(hours=13), reader=unavailable)
        self.assertFalse(failed["no_change"])
        self.assertTrue(failed["persistence"]["committed"])
        self.assertTrue(all(e["lifecycle_status"] == "expired" for e in failed["events"]))
        for old in first["events"]:
            event = next(e for e in failed["events"] if e["event_id"] == old["event_id"])
            for field in ("content_hash", "observed_at", "last_verified_at", "fresh_until"):
                self.assertEqual(event[field], old[field])
        self.assertNotIn("secret", json.dumps(failed))
        self.assertIsNone(failed["safety_conclusion"])

    def test_repeated_outage_not_new_and_recovery_keeps_ids(self):
        self.run_monitor()
        def unavailable(_): raise TimeoutError("do not log")
        first = self.run_monitor(now=NOW + timedelta(minutes=1), reader=unavailable)
        second = self.run_monitor(now=NOW + timedelta(minutes=2), reader=unavailable)
        self.assertTrue(first["changes"])
        self.assertEqual(second["changes"], [])
        self.assertFalse(second["no_change"])
        recovered = self.run_monitor(now=NOW + timedelta(minutes=3))
        self.assertIn("source_recovered", [c["kind"] for c in recovered["changes"]])
        self.assertFalse(recovered["initial_observation"])

    def test_malformed_json_no_last_good_loss_no_exception_content_leak(self):
        self.run_monitor()
        for raw in (b'{"token":"secret",', b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'\xff'):
            with self.subTest(raw=raw):
                report = self.run_monitor(raw, NOW + timedelta(minutes=1))
                self.assertEqual(len(report["events"]), 4)
                self.assertEqual(report["sources"][self.ident]["status"], "unavailable")
                self.assertNotIn("secret", markdown(report))

    def test_invalid_country_rejects_whole_collection_without_partial_mutation(self):
        first = self.run_monitor()
        for change in ("missing", "code", "slug", "flag", "level", "future", "markup", "booltime"):
            data = load_json(FIXTURE)
            if change == "missing": del data["data"]["US"]
            if change == "code": data["data"]["US"]["country-iso"] = "GB"
            if change == "slug": data["data"]["US"]["eng"]["url-slug"] = "elsewhere"
            if change == "flag": data["data"]["US"]["has-content"] = True
            if change == "level": data["data"]["US"]["eng"]["advisory-text"] = "Safe everywhere"
            if change == "future": data["data"]["US"]["date-published"]["timestamp"] += 100000
            if change == "markup": data["data"]["US"]["eng"]["recent-updates"] = "<script>bad()</script>"
            if change == "booltime": data["data"]["US"]["date-published"]["timestamp"] = True
            data["data"]["FR"]["eng"]["recent-updates"] = "Synthetic change must not partly commit."
            report = self.run_monitor(canonical(data), NOW + timedelta(minutes=1))
            with self.subTest(change=change):
                self.assertEqual({e["content_hash"] for e in report["events"]},
                                 {e["content_hash"] for e in first["events"]})
                self.assertEqual(report["sources"][self.ident]["status"], "unavailable")

    def test_stale_and_future_exports_rejected(self):
        for delta in (-49 * 3600, 11 * 60):
            payload = load_json(FIXTURE)
            payload["metadata"]["generated"]["timestamp"] += delta
            report = self.run_monitor(canonical(payload))
            self.assertEqual(report["events"], [])
            self.assertEqual(report["sources"][self.ident]["error_code"], "stale_or_future_export")

    def test_oversize_and_deep_json_are_bounded(self):
        for raw in (b" " * (MAX_INPUT_BYTES + 1), b"[" * 40 + b"0" + b"]" * 40):
            with self.assertRaises(ValidationError): parse_json(raw)

    def test_missing_state_is_explicit_initial_observation_not_all_new_today(self):
        report = self.run_monitor()
        self.assertTrue(report["initial_observation"])
        self.assertEqual({c["kind"] for c in report["changes"]}, {"initial_observation"})

    def test_corrupt_state_stops_before_collection_and_does_not_reset(self):
        self.run_monitor()
        pointer = self.directory / "state/CURRENT.json"
        pointer.write_bytes(b"{broken")
        reader = MagicMock(return_value=fixture())
        with self.assertRaises(StoreError): self.run_monitor(reader=reader)
        reader.assert_not_called()
        self.assertEqual(pointer.read_bytes(), b"{broken")

    def test_snapshot_tamper_and_config_changes_require_recovery_or_migration(self):
        self.run_monitor()
        target = next((self.directory / "state/generations").glob("*.json"))
        original = target.read_bytes()
        target.write_bytes(original.replace(b'"severity":"informational"', b'"severity":"critical"', 1))
        with self.assertRaises(StoreError): self.store.load(NOW)
        target.write_bytes(original)
        destinations, sources = configuration()
        destinations["destinations"][-1]["name_en"] = "Synthetic configuration change"
        new_registry = Registry(destinations, sources)
        with self.assertRaises(StoreError):
            LocalStateStore(self.directory / "state", new_registry, ROOT).load(NOW)

    def test_pointer_recovery_preserves_history_and_recovers_latest(self):
        self.run_monitor()
        self.run_monitor(now=NOW + timedelta(minutes=1))
        pointer = self.directory / "state/CURRENT.json"
        pointer.write_bytes(b"bad pointer")
        recovered = self.store.recover(NOW + timedelta(minutes=2))
        self.assertEqual(recovered.generation, 2)
        self.assertEqual(self.store.load(NOW + timedelta(minutes=2)).token, recovered.token)
        self.assertTrue(list((self.directory / "state").glob("recovery-pointer-*.bin")))

    def test_corrupt_latest_generation_rolls_back_explicitly_not_silently(self):
        self.run_monitor()
        self.run_monitor(now=NOW + timedelta(minutes=1))
        pointer = load_json(self.directory / "state/CURRENT.json")
        target = self.directory / "state/generations" / f'00000002-{pointer["token"]}.json'
        target.write_bytes(b"truncated generation")
        with self.assertRaises(StoreError): self.store.load(NOW + timedelta(minutes=2))
        recovered = self.store.recover(NOW + timedelta(minutes=2))
        self.assertEqual(recovered.generation, 1)
        self.assertEqual(len(list((self.directory / "state/generations").glob("*.json"))), 2)

    def test_empty_or_forked_recovery_refuses_to_guess(self):
        with self.assertRaises(StoreError): self.store.recover(NOW)
        self.run_monitor()
        p = load_json(self.directory / "state/CURRENT.json")
        path = self.directory / "state/generations" / f'00000001-{p["token"]}.json'
        envelope = load_json(path)
        envelope["data"]["events"][0]["human_review_status"] = "rejected"
        new_token = digest(envelope)
        (path.parent / f"00000001-{new_token}.json").write_bytes(canonical(envelope))
        with self.assertRaisesRegex(StoreError, "ambiguous"):
            self.store.recover(NOW)

    def test_conflicting_writer_cannot_overwrite_new_generation(self):
        self.run_monitor()
        old = self.store.load(NOW)
        self.run_monitor(now=NOW + timedelta(minutes=1))
        data = deepcopy(old.data)
        data["last_run_at"] = stamp(NOW + timedelta(minutes=2))
        with self.assertRaises(ConflictError): self.store.commit(data, old.token, NOW + timedelta(minutes=2))
        self.assertEqual(self.store.load(NOW + timedelta(minutes=2)).generation, 2)

    def test_writer_lock_never_auto_broken(self):
        self.run_monitor()
        lock = self.directory / "state/.writer.lock"
        lock.write_text("synthetic interrupted writer")
        report = self.run_monitor(now=NOW + timedelta(minutes=1))
        self.assertFalse(report["persistence"]["committed"])
        self.assertEqual(lock.read_text(), "synthetic interrupted writer")
        self.assertEqual(self.store.load(NOW + timedelta(minutes=1)).generation, 1)

    def test_crash_before_pointer_swap_keeps_valid_old_state_then_replays_idempotently(self):
        self.run_monitor()
        with patch("travel_intelligence.storage.atomic_json", side_effect=OSError("synthetic disk failure")):
            failed = self.run_monitor(now=NOW + timedelta(minutes=1))
        self.assertFalse(failed["persistence"]["committed"])
        self.assertEqual(self.store.load(NOW + timedelta(minutes=1)).generation, 1)
        recovered = self.run_monitor(now=NOW + timedelta(minutes=1))
        self.assertTrue(recovered["persistence"]["committed"])
        self.assertEqual(recovered["persistence"]["generation"], 2)
        self.assertEqual(len(recovered["events"]), 4)
        self.assertEqual(recovered["changes"], [])

    def test_missing_pointer_with_orphan_generation_requires_explicit_recovery(self):
        with patch("travel_intelligence.storage.atomic_json", side_effect=OSError("synthetic crash")):
            report = self.run_monitor()
        self.assertFalse(report["persistence"]["committed"])
        with self.assertRaises(StoreError): self.store.load(NOW)
        self.assertEqual(self.store.recover(NOW).generation, 1)

    def test_clock_rollback_rejected_before_fetch(self):
        self.run_monitor()
        reader = MagicMock(return_value=fixture())
        with self.assertRaises(StoreError): self.run_monitor(now=NOW - timedelta(minutes=1), reader=reader)
        reader.assert_not_called()

    def test_gap_is_reported_without_fabricating_intermediate_history(self):
        self.run_monitor()
        report = self.run_monitor(now=NOW + timedelta(hours=13))
        self.assertIn("monitoring_gap_history_not_recoverable", [d["code"] for d in report["diagnostics"]])

    def test_missing_feed_record_is_unverifiable_not_withdrawn(self):
        self.run_monitor()
        original = self.adapters[self.ident]
        class Missing:
            def parse(_, raw, now):
                batch = original.parse(raw, now)
                return Batch(batch.source_id, batch.generated_at, batch.events[1:])
        self.adapters[self.ident] = Missing()
        report = self.run_monitor(now=NOW + timedelta(minutes=1))
        self.assertEqual(len(report["events"]), 4)
        self.assertEqual(sum(e["source_status"] == "unverifiable" for e in report["events"]), 1)
        self.assertFalse(any(e["source_status"] == "withdrawn" for e in report["events"]))

    def test_timezones_offsets_dst_and_ambiguous_dates(self):
        self.assertEqual(local_time("2026-10-25T00:30:00Z", "Europe/Paris"), "2026-10-25T02:30:00+02:00")
        self.assertEqual(local_time("2026-10-25T01:30:00Z", "Europe/Rome"), "2026-10-25T02:30:00+01:00")
        self.assertEqual(local_time("2026-10-25T01:30:00Z", "Europe/London"), "2026-10-25T01:30:00+00:00")
        self.assertEqual(local_time("2026-11-01T06:30:00Z", "America/New_York"), "2026-11-01T01:30:00-05:00")
        self.assertEqual(instant("2026-10-22T14:00:00+02:00"), NOW)
        for value in ("2026-10-22", "2026-10-22T12:00:00", "22/10/2026", "2026-02-30T12:00:00Z"):
            with self.assertRaises(ValidationError): instant(value)

    def test_date_only_never_invents_midnight_and_event_interval_is_validated(self):
        event = self.events()[0]
        event.update(published_at=None, source_published_date="2026-10-22")
        event["content_hash"] = content_hash(event)
        validate_event(event, self.registry, NOW)
        event.update(starts_at=stamp(NOW), ends_at=stamp(NOW - timedelta(hours=1)))
        event["content_hash"] = content_hash(event)
        with self.assertRaises(ValidationError): validate_event(event, self.registry, NOW)

    def test_model_urls_and_markup_fail_closed(self):
        for url in ("https://travel.gc.ca.evil.test/destinations/france", "file:///tmp/state",
                    "https://travel.gc.ca/destinations/france?next=https://evil.test", "http://127.0.0.1/"):
            event = self.events()[0]
            event["source_url"] = url
            event["content_hash"] = content_hash(event)
            with self.assertRaises(ValidationError): validate_event(event, self.registry, NOW)

    def test_network_contract_refuses_redirect_challenge_encoding_and_size(self):
        with self.assertRaises(ValidationError): NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test")
        for kind in ("html", "gzip", "large", "redirect"):
            headers = Message()
            headers["Content-Type"] = "text/html" if kind == "html" else "application/json"
            if kind == "gzip": headers["Content-Encoding"] = "gzip"
            response = SimpleNamespace(status=200, headers=headers,
                geturl=lambda: FEED + ("/redirect" if kind == "redirect" else ""),
                read1=lambda _: b"x" * (MAX_INPUT_BYTES + 1))
            opener = MagicMock()
            opener.open.return_value.__enter__.return_value = response
            with self.subTest(kind=kind), patch("travel_intelligence.providers.build_opener", return_value=opener), self.assertRaises(ValidationError):
                fetch_canada()
            self.assertEqual(opener.open.call_count, 1)

    def test_network_fetch_is_one_fixed_request_with_no_retry(self):
        headers = Message(); headers["Content-Type"] = "application/json"
        chunks = iter([fixture(), b""])
        response = SimpleNamespace(status=200, headers=headers, geturl=lambda: FEED, read1=lambda _: next(chunks))
        opener = MagicMock(); opener.open.return_value.__enter__.return_value = response
        with patch("travel_intelligence.providers.build_opener", return_value=opener):
            self.assertEqual(fetch_canada(), fixture())
        self.assertEqual(opener.open.call_count, 1)
        self.assertEqual(opener.open.call_args[0][0].full_url, FEED)
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)

    def test_timeout_and_http_errors_are_sanitized_and_not_retried(self):
        for exc in (HTTPError(FEED, 429, "secret", {}, None), TimeoutError("token=secret")):
            reader = MagicMock(side_effect=exc)
            report = self.run_monitor(reader=reader)
            self.assertEqual(reader.call_count, 1)
            self.assertNotIn("secret", json.dumps(report))
            self.assertFalse(report["no_change"])

    def test_only_qualified_canada_endpoint_can_be_enabled(self):
        destinations, sources = configuration()
        sources["sources"][0]["endpoint"] = "https://travel.gc.ca/destinations/france"
        registry = Registry(destinations, sources)
        with self.assertRaises(ValidationError): adapters_for(registry)

    def test_report_is_escaped_and_produces_no_public_proposal(self):
        report = self.run_monitor(fixture(**{"recent-updates": "Synthetic [click](https://evil.test) # heading"}))
        out = self.directory / "reports"
        write_report(out, report, ROOT)
        value = (out / "report.md").read_text(encoding="utf-8")
        self.assertNotIn("[click](https://evil.test)", value)
        self.assertIn("Publication disabled", value)
        self.assertEqual({p.name for p in out.iterdir()}, {"report.json", "report.md"})
        self.assertEqual(load_json(out / "report.json")["safety_conclusion"], None)

    def test_output_paths_cannot_mutate_checkout_or_git_metadata(self):
        for target in (ROOT / "hotels/paris", ROOT / "docs/qa/new-v3", ROOT / ".git", ROOT):
            with self.assertRaises(ValidationError): safe_external_directory(target, ROOT)
        fake = self.directory / "other-checkout"
        fake.mkdir(); (fake / ".git").write_text("gitdir: elsewhere")
        with self.assertRaises(ValidationError): safe_external_directory(fake / "state", ROOT)

    def test_linked_state_pointer_is_refused(self):
        self.run_monitor()
        pointer = self.directory / "state/CURRENT.json"
        original = pointer.read_bytes()
        target = self.directory / "target.json"; target.write_bytes(original)
        pointer.unlink()
        try:
            pointer.symlink_to(target)
        except OSError:
            pointer.write_bytes(original)
            self.skipTest("OS does not grant symlink creation")
        with self.assertRaises(StoreError): self.store.load(NOW)

    def test_cli_offline_end_to_end_preserves_main_v2_and_public_files(self):
        refs_before = subprocess.check_output(["git", "show-ref", "--heads"], cwd=ROOT)
        protected = [ROOT / p for p in ("scripts/paris-travel-intelligence.py",
            ".github/workflows/paris-travel-intelligence.yml", "docs/travel-intelligence/paris-events.json",
            "tests/fixtures/site-baseline.json", "hotels/paris/index.html", "assets/js/site.js")]
        before = {p: p.read_bytes() for p in protected}
        cmd = [sys.executable, "-B", str(ROOT / "scripts/global-travel-intelligence.py"),
               "--input", str(FIXTURE), "--now", stamp(NOW), "--state-dir", str(self.directory / "cli-state"),
               "--output", str(self.directory / "cli-report")]
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = load_json(self.directory / "cli-report/report.json")
        self.assertEqual(len(report["events"]), 4)
        self.assertFalse(report["automatic_publication"])
        self.assertEqual(refs_before, subprocess.check_output(["git", "show-ref", "--heads"], cwd=ROOT))
        self.assertTrue(all(p.read_bytes() == value for p, value in before.items()))


if __name__ == "__main__":
    unittest.main()
