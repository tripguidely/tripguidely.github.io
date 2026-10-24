"""Offline phase-4 acceptance cases; no scheduler or remote backend is implemented."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from travel_intelligence.engine import Monitor
from travel_intelligence.providers import adapters_for
from travel_intelligence.registry import Registry
from travel_intelligence.reporting import write_report
from travel_intelligence.storage import ConflictError, LocalStateStore, Snapshot, StoreError
from travel_intelligence.validation import ValidationError, canonical, instant, load_json, stamp

NOW = instant("2026-10-23T12:00:00Z")
PROFILES = {
    "canada": ("sources.json", "canada-pilot-synthetic.json"),
    "usgs": ("usgs-sources.json", "usgs-synthetic.geojson"),
    "gdacs": ("gdacs-sources.json", "gdacs-synthetic.geojson"),
}


class AutomationFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gti-v3-automation-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registries, self.stores, self.monitors, self.payloads = {}, {}, {}, {}
        for name, (config, fixture) in PROFILES.items():
            registry = Registry.from_directory(ROOT / "config/travel-intelligence", config)
            self.registries[name] = registry
            self.stores[name] = LocalStateStore(self.directory / name / "state", registry, ROOT)
            self.monitors[name] = Monitor(registry, self.stores[name], adapters_for(registry))
            self.payloads[name] = load_json(ROOT / "tests/fixtures/travel-intelligence" / fixture)
        for module, adapter in (("providers", "CanadaAdapter"), ("usgs", "USGSAdapter"),
                                ("gdacs", "GDACSAdapter")):
            guard = patch("travel_intelligence." + module + "." + adapter + ".fetch",
                          side_effect=AssertionError("Live fetch forbidden in phase-4 tests"))
            guard.start()
            self.addCleanup(guard.stop)

    def collect(self, name, now=NOW, reader=None):
        return self.monitors[name].run(
            now, reader if reader is not None else lambda _: canonical(self.payloads[name]))

    def cycle(self, now=NOW, readers=None):
        # Test-only orchestration demonstration: isolate broken state by source.
        # There is no live reader, remote writer, automatic recovery or scheduler.
        results = {}
        for name in PROFILES:
            try:
                results[name] = self.collect(name, now, (readers or {}).get(name))
            except StoreError:
                results[name] = {"state_error": "explicit_recovery_required"}
        return results

    def content(self, report):
        return {event["event_id"]: (event["content_hash"], event["provenance"])
                for event in report["events"]}

    def test_three_profiles_keep_independent_states_reports_and_replay_identity(self):
        first = self.cycle()
        self.assertEqual({name: len(r["events"]) for name, r in first.items()},
                         {"canada": 4, "usgs": 2, "gdacs": 6})
        second = self.cycle(NOW + timedelta(minutes=5))
        for name, report in second.items():
            with self.subTest(source=name):
                self.assertTrue(report["persistence"]["committed"])
                self.assertEqual(report["changes"], [])
                self.assertEqual(self.content(first[name]), self.content(report))
                self.assertFalse(report["automatic_publication"])
                self.assertFalse(report["publication_authorized"])
                self.assertIsNone(report["safety_conclusion"])
                output = self.directory / name / "reports"
                write_report(output, report, ROOT)
                self.assertEqual(load_json(output / "report.json")["run_id"], report["run_id"])
                self.assertIn("Publication disabled", (output / "report.md").read_text(encoding="utf-8"))
                self.assertEqual(self.stores[name].load(NOW + timedelta(minutes=5)).generation, 2)
        self.assertEqual(len({r["config_hash"] for r in first.values()}), 3)

    def test_one_source_outage_keeps_last_verified_content_and_other_sources_running(self):
        first = self.cycle()
        bad = MagicMock(side_effect=TimeoutError("untrusted-private-detail"))
        second = self.cycle(NOW + timedelta(minutes=5), {"gdacs": bad})
        failed = second["gdacs"]
        self.assertEqual(self.content(first["gdacs"]), self.content(failed))
        self.assertTrue(all(e["source_status"] == "unverifiable" for e in failed["events"]))
        self.assertEqual([e["last_verified_at"] for e in first["gdacs"]["events"]],
                         [e["last_verified_at"] for e in failed["events"]])
        self.assertIsNone(failed["safety_conclusion"])
        self.assertNotIn("untrusted-private-detail", canonical(failed).decode())
        for name in ("canada", "usgs"):
            self.assertTrue(all(s["status"] == "checked" for s in second[name]["sources"].values()))
        recovered = self.collect("gdacs", NOW + timedelta(minutes=10))
        self.assertTrue(any(c["kind"] == "source_recovered" for c in recovered["changes"]))
        self.assertFalse(any(c["kind"] in {"initial_observation", "new_information"}
                             for c in recovered["changes"]))

    def test_revision_preserves_the_other_profiles_and_the_original_observation_identity(self):
        first = self.cycle()
        p = self.payloads["usgs"]["features"][0]["properties"]
        p["mag"] += 0.1
        p["updated"] += 1000
        second = self.cycle(NOW + timedelta(minutes=5))
        self.assertEqual(set(self.content(first["usgs"])), set(self.content(second["usgs"])))
        self.assertNotEqual(self.content(first["usgs"]), self.content(second["usgs"]))
        self.assertTrue(any(c["kind"] == "source_revised" for c in second["usgs"]["changes"]))
        for name in ("canada", "gdacs"):
            self.assertEqual(self.content(first[name]), self.content(second[name]))

    def test_omission_and_expiration_keep_observations_without_all_clear(self):
        first = self.collect("gdacs")
        self.payloads["gdacs"] = {"type": "FeatureCollection", "features": [], "bbox": None}
        report = self.collect("gdacs", NOW + timedelta(hours=2))
        self.assertEqual(set(self.content(first)), set(self.content(report)))
        self.assertTrue(all(e["lifecycle_status"] == "expired" and e["ends_at"] is None
                            and e["source_status"] == "unverifiable" for e in report["events"]))
        self.assertIsNone(report["safety_conclusion"])
        self.assertFalse(report["no_change"])
        self.assertTrue(any(d["code"] == "records_missing_not_withdrawn"
                            for d in report["diagnostics"]))

    def test_corrupt_state_blocks_its_reader_but_not_other_profiles(self):
        self.cycle()
        (self.directory / "usgs/state/CURRENT.json").write_bytes(b"{broken")
        reader = MagicMock(return_value=canonical(self.payloads["usgs"]))
        results = self.cycle(NOW + timedelta(minutes=5), {"usgs": reader})
        reader.assert_not_called()
        self.assertEqual(results["usgs"], {"state_error": "explicit_recovery_required"})
        self.assertTrue(results["canada"]["persistence"]["committed"])
        self.assertTrue(results["gdacs"]["persistence"]["committed"])

    def test_cas_rejects_a_stale_writer_without_changing_the_current_pointer(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        old = store.load(NOW)
        self.collect("gdacs", NOW + timedelta(minutes=5))
        pointer = (store.directory / "CURRENT.json").read_bytes()
        data = deepcopy(old.data)
        data["last_run_at"] = stamp(NOW + timedelta(minutes=10))
        with self.assertRaises(ConflictError):
            store.commit(data, old.token, NOW + timedelta(minutes=10))
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)

    def test_writer_lock_never_gets_automatically_removed_or_overwrites_state(self):
        self.cycle()
        store = self.stores["gdacs"]
        pointer = (store.directory / "CURRENT.json").read_bytes()
        lock = store.directory / ".writer.lock"
        lock.write_bytes(b"synthetic existing writer")
        result = self.cycle(NOW + timedelta(minutes=5))
        self.assertFalse(result["gdacs"]["persistence"]["committed"])
        self.assertEqual(result["gdacs"]["persistence"]["error_code"], "persistence_failed")
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)
        self.assertEqual(lock.read_bytes(), b"synthetic existing writer")
        self.assertTrue(result["usgs"]["persistence"]["committed"])
        self.assertTrue(result["canada"]["persistence"]["committed"])

    def test_crash_before_pointer_switch_preserves_old_state_and_explicit_recovery(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        pointer = (store.directory / "CURRENT.json").read_bytes()
        with patch("travel_intelligence.storage.atomic_json", side_effect=OSError("synthetic disk failure")):
            failed = self.collect("gdacs", NOW + timedelta(minutes=5))
        self.assertFalse(failed["persistence"]["committed"])
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)
        self.assertEqual(store.load(NOW + timedelta(minutes=5)).generation, 1)
        self.assertEqual(len(list((store.directory / "generations").glob("*.json"))), 2)
        recovered = store.recover(NOW + timedelta(minutes=5))
        self.assertEqual(recovered.generation, 2)
        replay = self.collect("gdacs", NOW + timedelta(minutes=10))
        self.assertEqual(replay["changes"], [])
        self.assertFalse(replay["initial_observation"])

    def test_two_complete_orphan_heads_require_a_human_recovery_choice(self):
        self.collect("gdacs")
        for score, revision in ((2.1, "2026-10-23T11:55:00"), (2.2, "2026-10-23T11:56:00")):
            self.payloads["gdacs"]["features"][0]["properties"].update(
                alertscore=score, datemodified=revision)
            with patch("travel_intelligence.storage.atomic_json", side_effect=OSError("synthetic crash")):
                self.assertFalse(self.collect("gdacs", NOW + timedelta(minutes=5))["persistence"]["committed"])
        store = self.stores["gdacs"]
        pointer = (store.directory / "CURRENT.json").read_bytes()
        with self.assertRaisesRegex(StoreError, "ambiguous_recovery_generation"):
            store.recover(NOW + timedelta(minutes=5))
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)

    def test_missing_pointer_with_history_never_silently_reinitializes(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        (store.directory / "CURRENT.json").unlink()
        reader = MagicMock(return_value=canonical(self.payloads["gdacs"]))
        with self.assertRaises(StoreError):
            self.collect("gdacs", NOW + timedelta(minutes=5), reader)
        reader.assert_not_called()
        self.assertEqual(len(list((store.directory / "generations").glob("*.json"))), 1)

    def test_profile_migration_cannot_relabel_an_existing_store(self):
        self.collect("gdacs")
        mismatched = LocalStateStore(self.stores["gdacs"].directory, self.registries["usgs"], ROOT)
        reader = MagicMock(return_value=canonical(self.payloads["usgs"]))
        monitor = Monitor(self.registries["usgs"], mismatched, adapters_for(self.registries["usgs"]))
        with self.assertRaises(StoreError):
            monitor.run(NOW + timedelta(minutes=5), reader)
        reader.assert_not_called()

    def test_report_failure_after_commit_is_not_a_state_rollback_or_a_new_observation(self):
        report = self.collect("gdacs")
        output = self.directory / "failed-reports"
        with patch("travel_intelligence.reporting.markdown", side_effect=OSError("synthetic report failure")):
            with self.assertRaises(OSError):
                write_report(output, report, ROOT)
        self.assertTrue((output / "report.json").exists())
        self.assertFalse((output / "report.md").exists())
        self.assertEqual(self.stores["gdacs"].load(NOW).generation, 1)
        replay = self.collect("gdacs", NOW + timedelta(minutes=5))
        self.assertEqual(replay["changes"], [])
        write_report(output, report, ROOT)  # Recover the original change report, not the empty replay.
        self.assertEqual(load_json(output / "report.json")["changes"], report["changes"])

    def test_generation_ceiling_fails_closed_without_resetting_history(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        old = store.load(NOW)
        pointer = (store.directory / "CURRENT.json").read_bytes()
        data = deepcopy(old.data)
        data["last_run_at"] = stamp(NOW + timedelta(minutes=5))
        ceiling = Snapshot(old.token, 1000, old.data)
        with patch.object(store, "load", return_value=ceiling):
            with self.assertRaisesRegex(ValidationError, "generation_limit"):
                store.commit(data, old.token, NOW + timedelta(minutes=5))
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)

    def test_two_concurrent_writers_only_commit_one_successor_generation(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        old = store.load(NOW)
        now = NOW + timedelta(minutes=5)
        data = deepcopy(old.data)
        data["last_run_at"] = stamp(now)
        barrier = Barrier(2)

        def writer():
            independent = LocalStateStore(store.directory, self.registries["gdacs"], ROOT)
            barrier.wait(timeout=10)
            try:
                return independent.commit(deepcopy(data), old.token, now).token
            except ConflictError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: writer(), range(2)))
        self.assertEqual(sum(token is not None for token in results), 1)
        current = store.load(now)
        self.assertEqual(current.generation, 2)
        self.assertIn(current.token, results)
        self.assertEqual(len(list((store.directory / "generations").glob("*.json"))), 2)

    def test_interrupted_generation_write_is_not_current_or_automatically_promoted(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        pointer = (store.directory / "CURRENT.json").read_bytes()
        original_open = Path.open

        class InterruptedFile:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def write(self, raw):
                self.stream.write(raw[:len(raw) // 2])
                self.stream.flush()
                raise OSError("synthetic interruption in generation write")

        def interrupted_open(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            if path.parent == store.directory / "generations" and args == ("xb",):
                return InterruptedFile(stream)
            return stream

        with patch.object(Path, "open", new=interrupted_open):
            failed = self.collect("gdacs", NOW + timedelta(minutes=5))
        self.assertFalse(failed["persistence"]["committed"])
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)
        self.assertEqual(store.load(NOW + timedelta(minutes=5)).generation, 1)
        self.assertEqual(store.recover(NOW + timedelta(minutes=5)).generation, 1)
        self.assertEqual(len(list((store.directory / "generations").glob("*.json"))), 2)

    def test_corrupt_latest_generation_recovers_last_complete_chain_without_duplicates(self):
        first = self.collect("gdacs")
        self.collect("gdacs", NOW + timedelta(minutes=5))
        store = self.stores["gdacs"]
        current = store.load(NOW + timedelta(minutes=5))
        damaged = store.directory / "generations" / f"{current.generation:08d}-{current.token}.json"
        damaged.write_bytes(b"{synthetic truncated generation")
        with self.assertRaises(StoreError):
            store.load(NOW + timedelta(minutes=5))
        self.assertEqual(store.recover(NOW + timedelta(minutes=5)).generation, 1)
        replay = self.collect("gdacs", NOW + timedelta(minutes=10))
        self.assertEqual(self.content(first), self.content(replay))
        self.assertEqual(replay["changes"], [])
        self.assertFalse(replay["initial_observation"])
        self.assertEqual(damaged.read_bytes(), b"{synthetic truncated generation")

    def test_incomplete_history_blocks_collection_and_refuses_empty_recovery(self):
        self.collect("gdacs")
        store = self.stores["gdacs"]
        original = store.load(NOW)
        self.collect("gdacs", NOW + timedelta(minutes=5))
        pointer = (store.directory / "CURRENT.json").read_bytes()
        (store.directory / "generations" / f"00000001-{original.token}.json").unlink()
        reader = MagicMock(return_value=canonical(self.payloads["gdacs"]))
        with self.assertRaises(StoreError):
            self.collect("gdacs", NOW + timedelta(minutes=10), reader)
        reader.assert_not_called()
        with self.assertRaisesRegex(StoreError, "no_valid_recovery_generation"):
            store.recover(NOW + timedelta(minutes=10))
        self.assertEqual((store.directory / "CURRENT.json").read_bytes(), pointer)

    def test_local_backup_restore_survives_absent_actions_cache_without_new_observations(self):
        first = self.cycle()
        missing_cache = self.directory / "absent-actions-cache"
        for name in PROFILES:
            backup = self.directory / "backups" / name
            shutil.copytree(self.stores[name].directory, backup)
            restored = self.directory / "replacement-runner" / name
            shutil.copytree(backup, restored)
            store = LocalStateStore(restored, self.registries[name], ROOT)
            monitor = Monitor(self.registries[name], store, adapters_for(self.registries[name]))
            replay = monitor.run(NOW + timedelta(minutes=5), lambda _: canonical(self.payloads[name]))
            with self.subTest(source=name):
                self.assertEqual(self.content(first[name]), self.content(replay))
                self.assertEqual(replay["changes"], [])
                self.assertFalse(replay["initial_observation"])
                self.assertEqual(replay["persistence"]["generation"], 2)
        self.assertFalse(missing_cache.exists())

    def test_shadow_outages_expiration_and_reports_never_mutate_tracked_site_files(self):
        files = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")

        def snapshot():
            return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files if p}

        before = snapshot()
        initial = self.cycle()
        outage = self.cycle(NOW + timedelta(minutes=5),
                            {"usgs": MagicMock(side_effect=TimeoutError("synthetic outage"))})
        self.payloads["gdacs"] = {"type": "FeatureCollection", "features": [], "bbox": None}
        expired = self.collect("gdacs", NOW + timedelta(hours=2))
        reports = list(initial.values()) + list(outage.values()) + [expired]
        for number, report in enumerate(reports):
            write_report(self.directory / "review-only" / str(number), report, ROOT)
            self.assertFalse(report["publication_authorized"])
            self.assertFalse(report["automatic_publication"])
            self.assertIsNone(report["safety_conclusion"])
            self.assertTrue(all(e["publication_status"] == "withheld" for e in report["events"]))
        self.assertEqual(before, snapshot())


if __name__ == "__main__":
    unittest.main()
