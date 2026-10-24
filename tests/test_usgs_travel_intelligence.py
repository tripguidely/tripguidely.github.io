"""Offline USGS contract and durable lifecycle tests; synthetic measurements only."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import Message
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from travel_intelligence.engine import Monitor
from travel_intelligence.model import content_hash, validate_event
from travel_intelligence.providers import adapters_for, NoRedirect
from travel_intelligence.registry import Registry
from travel_intelligence.reporting import markdown, write_report
from travel_intelligence.storage import LocalStateStore, StoreError
from travel_intelligence.usgs import FEED, USGSAdapter, fetch_usgs
from travel_intelligence.validation import MAX_INPUT_BYTES, ValidationError, canonical, load_json, stamp

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)
FIXTURE = ROOT / "tests/fixtures/travel-intelligence/usgs-synthetic.geojson"


def fixture():
    return load_json(FIXTURE)


class USGSTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gti-usgs-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = Registry.from_directory(ROOT / "config/travel-intelligence", "usgs-sources.json")
        self.adapters = adapters_for(self.registry)
        self.adapter = self.adapters["usgs-earthquakes"]
        self.store = LocalStateStore(self.directory / "state", self.registry, ROOT)

    def run_monitor(self, data=None, now=NOW, reader=None):
        return Monitor(self.registry, self.store, self.adapters).run(
            now, reader or (lambda _: canonical(fixture() if data is None else data)))

    def test_important_and_minor_observations_never_establish_traveler_impact(self):
        report = self.run_monitor()
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual({e["source_data"]["magnitude"] for e in report["events"]}, {"6.8", "3.2"})
        for event in report["events"]:
            self.assertEqual(event["severity"], "unknown")
            self.assertEqual(event["source_status"], "observed")
            self.assertEqual(event["category"], "earthquake")
            self.assertEqual(event["traveler_impact"], {"status": "unknown", "text_en": None, "evidence_urls": []})
            self.assertEqual(event["publication_status"], "withheld")
            self.assertIsNone(event["summary_en"])
        self.assertTrue(report["persistence"]["committed"])
        self.assertFalse(report["publication_authorized"])
        self.assertFalse(report["automatic_publication"])
        self.assertIsNone(report["safety_conclusion"])

    def test_point_near_rome_and_label_are_not_city_or_country_evidence(self):
        data = fixture(); data["features"][0]["properties"]["place"] = "1 km from Rome, Italy"
        report = self.run_monitor(data)
        for event in report["events"]:
            self.assertEqual(event["geographic_scope"], "point")
            self.assertEqual(event["geographic_basis"], "source_geometry")
            self.assertEqual(event["country_codes"], [])
            self.assertIsNone(event["city"])
            self.assertEqual(event["affected_locations"], [])
            self.assertEqual(report["destination_contexts"][event["event_id"]], [])

    def test_unchanged_poll_deduplicates_across_runs_and_keeps_review_deadline(self):
        first = self.run_monitor()
        second = self.run_monitor(now=NOW + timedelta(minutes=1))
        self.assertEqual([e["event_id"] for e in first["events"]], [e["event_id"] for e in second["events"]])
        self.assertEqual([e["review_due_at"] for e in first["events"]], [e["review_due_at"] for e in second["events"]])
        self.assertTrue(second["no_change"])
        self.assertEqual(second["changes"], [])
        self.assertEqual(self.store.load(NOW + timedelta(minutes=1)).generation, 2)

    def test_revision_updates_same_identity_and_requires_reverification(self):
        first = self.run_monitor()
        data = fixture(); props = data["features"][0]["properties"]
        props["mag"] = 6.6; props["status"] = "automatic"; props["updated"] += 60000
        data["features"][0]["geometry"]["coordinates"][0] = 12.5
        report = self.run_monitor(data, NOW + timedelta(minutes=1))
        ident = next(e["event_id"] for e in first["events"] if e["source_event_id"] == "ussynthetic001")
        event = next(e for e in report["events"] if e["event_id"] == ident)
        self.assertEqual(event["source_data"]["magnitude"], "6.6")
        self.assertEqual(event["source_data"]["longitude"], "12.5")
        self.assertEqual(event["human_review_status"], "needs_reverification")
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual(report["changes"], [{"event_id": ident, "kind": "source_revised"}])

    def test_reviewed_status_is_measurement_review_only_and_revision_is_audited(self):
        self.run_monitor()
        data = fixture(); data["features"][1]["properties"].update(status="reviewed", updated=data["metadata"]["generated"])
        report = self.run_monitor(data, NOW + timedelta(minutes=1))
        event = next(e for e in report["events"] if e["source_event_id"] == "ussynthetic002")
        self.assertEqual(event["source_status"], "observed")
        self.assertEqual(event["traveler_impact"]["status"], "unknown")
        self.assertEqual(report["changes"][0]["kind"], "source_revised")
        generations = list((self.directory / "state/generations").glob("*.json"))
        self.assertEqual(len(generations), 2)

    def test_revision_and_export_rollback_preserve_last_valid_content(self):
        self.run_monitor()
        for change in ("revision", "export", "same-revision"):
            with self.subTest(change=change):
                data = fixture()
                if change == "revision": data["features"][0]["properties"]["updated"] -= 1000
                elif change == "export": data["metadata"]["generated"] -= 1000
                else: data["features"][0]["properties"]["mag"] = 7
                report = self.run_monitor(data, NOW + timedelta(minutes=1))
                self.assertEqual(report["sources"]["usgs-earthquakes"]["status"], "unavailable")
                self.assertTrue(report["persistence"]["committed"])
                event = next(e for e in report["events"] if e["source_event_id"] == "ussynthetic001")
                self.assertEqual(event["source_data"]["magnitude"], "6.8")

    def test_rolling_omission_and_empty_feed_never_withdraw_or_end_danger(self):
        self.run_monitor()
        data = fixture(); data["features"] = []; data["metadata"]["count"] = 0
        report = self.run_monitor(data, NOW + timedelta(minutes=1))
        self.assertEqual(len(report["events"]), 2)
        self.assertTrue(any(d["code"] == "records_missing_not_withdrawn" for d in report["diagnostics"]))
        for event in report["events"]:
            self.assertEqual(event["source_status"], "unverifiable")
            self.assertIsNone(event["ends_at"])
        self.assertIsNone(report["safety_conclusion"])

    def test_source_outage_preserves_observations_and_recovery_is_deduplicated(self):
        self.run_monitor()
        reader = MagicMock(side_effect=URLError("secret response detail"))
        outage = self.run_monitor(now=NOW + timedelta(minutes=1), reader=reader)
        self.assertNotIn("secret response detail", json.dumps(outage))
        self.assertEqual(len(outage["events"]), 2)
        self.assertEqual(outage["sources"]["usgs-earthquakes"]["error_code"], "source_unavailable")
        recovered = self.run_monitor(now=NOW + timedelta(minutes=2))
        self.assertEqual(sum(c["kind"] == "source_recovered" for c in recovered["changes"]), 1)
        self.assertEqual({c["kind"] for c in recovered["changes"]}, {"source_recovered", "active"})
        self.assertEqual(len(recovered["events"]), 2)

    def test_expiry_is_technical_freshness_not_resolution(self):
        self.run_monitor()
        report = self.run_monitor(now=NOW + timedelta(hours=2), reader=MagicMock(side_effect=TimeoutError()))
        self.assertTrue(all(e["lifecycle_status"] == "expired" for e in report["events"]))
        self.assertTrue(all(e["ends_at"] is None for e in report["events"]))
        self.assertIsNone(report["safety_conclusion"])
        self.assertFalse(report["automatic_publication"])

    def test_tsunami_and_pager_fields_never_become_warnings_or_evacuations(self):
        data = fixture(); data["features"][0]["properties"].update(tsunami=1, alert="red")
        report = self.run_monitor(data)
        event = next(e for e in report["events"] if e["source_event_id"] == "ussynthetic001")
        self.assertEqual(event["category"], "earthquake")
        self.assertEqual(event["severity"], "unknown")
        self.assertEqual(event["source_data"]["tsunami-flag"], 1)
        self.assertIn("not an active tsunami warning or evacuation order", markdown(report))

    def test_identical_duplicates_consolidate_and_conflicting_duplicates_fail_whole_batch(self):
        data = fixture(); data["features"].append(deepcopy(data["features"][0])); data["metadata"]["count"] = 3
        report = self.run_monitor(data)
        self.assertEqual(len(report["events"]), 2)
        self.assertEqual(report["duplicates_in_batch"], 1)
        data["features"][-1]["properties"]["mag"] = 7.1
        report = self.run_monitor(data, NOW + timedelta(minutes=1))
        self.assertEqual(report["sources"]["usgs-earthquakes"]["error_code"], "conflicting_duplicate")
        self.assertTrue(all(e["source_data"]["magnitude"] != "7.1" for e in report["events"]))

    def test_invalid_coordinates_magnitude_and_types_reject_entire_collection(self):
        for coordinates in ([181, 0, 10], [0, 91, 10], [0, 0, -101], [0, 0], [True, 0, 1], [0, "0", 1]):
            with self.subTest(coordinates=coordinates):
                data = fixture(); data["features"][1]["geometry"]["coordinates"] = coordinates
                with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)
        for field, value in (("mag", 11), ("mag", True), ("time", "yesterday"), ("updated", -1),
                             ("status", "confirmed"), ("tsunami", True), ("alert", "evacuate"),
                             ("magType", 123), ("nst", 1.5), ("rms", -1)):
            with self.subTest(field=field):
                data = fixture(); data["features"][0]["properties"][field] = value
                with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)

    def test_null_measurements_and_zero_magnitude_are_not_invented(self):
        data = fixture(); data["features"][0]["properties"].update(mag=None, magType=None, place=None)
        data["features"][1]["properties"]["mag"] = 0
        events = self.adapter.parse(canonical(data), NOW).events
        self.assertIsNone(events[0]["source_data"]["magnitude"])
        self.assertIsNone(events[0]["source_data"]["magnitude-type"])
        self.assertEqual(events[1]["source_data"]["magnitude"], "0")

    def test_schema_malformed_json_limits_and_unknown_fields_fail_closed(self):
        for raw in (b"{broken", b'{"type":1,"type":2}', b'{"x":NaN}', b"x"*(MAX_INPUT_BYTES+1)):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(ValidationError): self.adapter.parse(raw, NOW)
        for part in ("root", "metadata", "feature", "properties", "geometry"):
            data = fixture()
            target = {"root":data, "metadata":data["metadata"], "feature":data["features"][0],
                      "properties":data["features"][0]["properties"], "geometry":data["features"][0]["geometry"]}[part]
            target["unknown"] = "not supported"
            with self.subTest(part=part):
                with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)
        data = fixture(); data["metadata"]["count"] = 3
        with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)
        data = fixture(); data["features"][0]["properties"]["type"] = "explosion"
        with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)

    def test_dates_export_window_and_future_updates_fail_closed(self):
        for field in ("generated-old", "generated-future", "occurred-future", "occurred-old", "update-before-origin"):
            data = fixture(); props = data["features"][0]["properties"]
            if field == "generated-old": data["metadata"]["generated"] -= 7200000
            elif field == "generated-future": data["metadata"]["generated"] += 7200000
            elif field == "occurred-future": props["time"] += 7200000
            elif field == "occurred-old": props["time"] -= 8*86400000
            else: props["updated"] = props["time"] - 1
            with self.subTest(field=field):
                with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)

    def test_urls_and_ids_cannot_escape_fixed_official_domains(self):
        for field, value in (("id", "../escape"), ("url", "https://earthquake.usgs.gov.evil.test/event"),
                             ("url", "https://earthquake.usgs.gov/earthquakes/eventpage/ussynthetic001?x=1"),
                             ("detail", "http://127.0.0.1/"), ("ids", ",other,")):
            data = fixture()
            if field == "id": data["features"][0][field] = value
            else: data["features"][0]["properties"][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValidationError): self.adapter.parse(canonical(data), NOW)

    def test_persisted_usgs_event_cannot_forge_destination_or_publication(self):
        original = self.adapter.parse(canonical(fixture()), NOW).events[0]
        for field, value in (("city", "it-rome"), ("country_codes", ["IT"]), ("source_url", FEED),
                             ("severity", "critical"), ("publication_status", "approved"),
                             ("ends_at", stamp(NOW)), ("source_status", "officially_confirmed")):
            event = deepcopy(original); event[field] = value; event["content_hash"] = content_hash(event)
            with self.subTest(field=field):
                with self.assertRaises(ValidationError): validate_event(event, self.registry, NOW)

    def test_provenance_retains_official_link_payload_hash_and_ms_precision(self):
        raw = canonical(fixture()); event = self.adapter.parse(raw, NOW).events[0]
        self.assertEqual(event["provenance"]["payload_hash"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(event["provenance"]["endpoint"], FEED)
        self.assertIn("ussynthetic001", event["source_url"])
        data = fixture(); data["features"][0]["properties"]["time"] += 123
        event = self.adapter.parse(canonical(data), NOW).events[0]
        self.assertTrue(event["starts_at"].endswith(".123000Z"))

    def test_corrupt_state_stops_before_fetch_and_config_profiles_are_isolated(self):
        self.run_monitor()
        (self.directory / "state/CURRENT.json").write_bytes(b"{broken")
        reader = MagicMock(return_value=canonical(fixture()))
        with self.assertRaises(StoreError): self.run_monitor(reader=reader)
        reader.assert_not_called()
        default = Registry.from_directory(ROOT / "config/travel-intelligence")
        self.assertEqual(set(adapters_for(default)), {"ca-travel-advisories"})
        self.assertNotEqual(default.config_hash, self.registry.config_hash)

    def test_registry_refuses_other_feeds_audiences_and_publication(self):
        destinations = load_json(ROOT / "config/travel-intelligence/destinations.json")
        original = load_json(ROOT / "config/travel-intelligence/usgs-sources.json")
        for field, value in (("endpoint", FEED.replace("4.5_week", "all_day")),
                             ("countries", ["IT"]), ("audience_nationalities", ["CA"]),
                             ("publication_enabled", True), ("freshness_hours", 48)):
            data = deepcopy(original); data["sources"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaises(ValidationError): Registry(destinations, data)
        with self.assertRaises(ValidationError):
            Registry.from_directory(ROOT / "config/travel-intelligence", "../../outside.json")

    def test_old_generations_record_revisions_and_recovery_does_not_fetch(self):
        self.run_monitor()
        data = fixture(); data["features"][0]["properties"].update(mag=6.7, updated=data["metadata"]["generated"])
        self.run_monitor(data, NOW + timedelta(minutes=1))
        pointer = self.directory / "state/CURRENT.json"
        pointer.unlink()
        with patch("travel_intelligence.usgs.fetch_usgs", side_effect=AssertionError("network forbidden")):
            recovered = self.store.recover(NOW + timedelta(minutes=1))
        self.assertEqual(recovered.generation, 2)
        magnitudes = {e["source_data"]["magnitude"] for e in recovered.data["events"]}
        self.assertEqual(magnitudes, {"6.7", "3.2"})
        self.assertEqual(len(list((self.directory / "state/generations").glob("*.json"))), 2)

    def test_one_fixed_fetch_bounded_mock_no_redirect_no_auth(self):
        headers = Message(); headers["Content-Type"] = "application/geo+json"
        response = SimpleNamespace(status=200, headers=headers, geturl=lambda:FEED,
                                   read1=MagicMock(side_effect=[b"{}", b""]))
        context = MagicMock(); context.__enter__.return_value = response
        opener = MagicMock(); opener.open.return_value = context
        with patch("travel_intelligence.usgs.build_opener", return_value=opener):
            self.assertEqual(fetch_usgs(), b"{}")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, FEED)
        self.assertEqual(opener.open.call_args.kwargs, {"timeout":15})
        self.assertEqual(opener.open.call_count, 1)
        self.assertNotIn("Authorization", request.headers)
        self.assertNotIn("Cookie", request.headers)
        with self.assertRaises(ValidationError): NoRedirect().redirect_request(None,None,302,"",{},"https://evil.test")

    def test_fetch_rejects_http_content_encoding_size_timeout_and_failure_without_retry(self):
        for kind in ("status", "url", "html", "gzip", "size", "timeout", "unavailable"):
            headers = Message(); headers["Content-Type"] = "text/html" if kind=="html" else "application/json"
            if kind=="gzip": headers["Content-Encoding"] = "gzip"
            response = SimpleNamespace(status=500 if kind=="status" else 200, headers=headers,
                geturl=lambda:FEED+('/redirect' if kind=="url" else ''),
                read1=MagicMock(side_effect=[b"x"*(MAX_INPUT_BYTES+1),b""] if kind=="size" else [b"{}",b""]))
            context=MagicMock(); context.__enter__.return_value=response
            opener=MagicMock(); opener.open.return_value=context
            if kind=="unavailable": opener.open.side_effect=TimeoutError()
            clock=iter([0,31,31,31]) if kind=="timeout" else iter([0]*10)
            with self.subTest(kind=kind), patch("travel_intelligence.usgs.build_opener",return_value=opener), patch(
                    "travel_intelligence.usgs.time.monotonic",side_effect=lambda:next(clock)):
                with self.assertRaises((ValidationError,TimeoutError)): fetch_usgs()
                self.assertEqual(opener.open.call_count,1)

    def test_cli_offline_replay_writes_only_local_reports_and_keeps_checkout_unchanged(self):
        tracked = subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0")
        before = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked if name}
        with patch("travel_intelligence.usgs.fetch_usgs",side_effect=AssertionError("network forbidden")):
            report=self.run_monitor()
        write_report(self.directory/"report",report,ROOT)
        self.assertEqual({p.name for p in (self.directory/"report").iterdir()},{"report.json","report.md"})
        result=subprocess.run([sys.executable,"-B",str(ROOT/"scripts/global-travel-intelligence.py"),
            "--provider","usgs","--input",str(FIXTURE),"--now",stamp(NOW),
            "--state-dir",str(self.directory/"cli-state"),"--output",str(self.directory/"cli-report")],
            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(load_json(self.directory/"cli-report/report.json")["automatic_publication"])
        self.assertEqual(before,{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in before})


if __name__ == "__main__":
    unittest.main()
