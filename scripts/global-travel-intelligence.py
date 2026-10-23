#!/usr/bin/env python3
"""Local V3 shadow monitor. Explicit --input or --live; writes outside Git only."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

from travel_intelligence.engine import Monitor
from travel_intelligence.providers import adapters_for
from travel_intelligence.registry import Registry
from travel_intelligence.reporting import write_report
from travel_intelligence.storage import LocalStateStore, StoreError
from travel_intelligence.validation import (MAX_INPUT_BYTES, UTC, ValidationError, digest,
                                           instant, require, safe_external_directory, stamp)

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input", type=Path, help="Replay one bounded Canada JSON file; no network")
    mode.add_argument("--live", action="store_true", help="One anonymous GET of the already-qualified Canada index")
    mode.add_argument("--recover-state", action="store_true", help="Explicit local recovery only; no collection")
    parser.add_argument("--state-dir", required=True, type=Path, help="Dedicated local directory outside all Git checkouts")
    parser.add_argument("--output", required=True, type=Path, help="Dedicated reports directory outside all Git checkouts")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "travel-intelligence")
    parser.add_argument("--now", help="RFC3339 clock for deterministic offline replay/recovery only")
    args = parser.parse_args(argv)
    if args.live and args.now:
        parser.error("--now cannot be used with --live")
    now = datetime.now(UTC)
    output = None
    try:
        if args.now:
            now = instant(args.now)
        candidate_output = safe_external_directory(args.output, ROOT)
        state_dir = safe_external_directory(args.state_dir, ROOT)
        require(not candidate_output.is_relative_to(state_dir) and not state_dir.is_relative_to(candidate_output),
                "state_and_reports_must_be_separate")
        output = candidate_output
        registry = Registry.from_directory(args.config)
        store = LocalStateStore(state_dir, registry, ROOT)
        adapters = adapters_for(registry)
        if args.recover_state:
            snapshot = store.recover(now)
            # Recovery is never silently followed by a collection/publication.
            report = failure_report(now, "state_recovered_review_gap")
            report["status"] = "state_recovered_review_required"
            report["persistence"].update(committed=True, generation=snapshot.generation, token=snapshot.token)
            write_report(output, report, ROOT)
            print("State recovered locally. Review the coverage gap before the next collection; no publication.")
            return 0
        def replay(_):
            with args.input.open("rb") as stream:
                return stream.read(MAX_INPUT_BYTES + 1)
        report = Monitor(registry, store, adapters).run(now, replay if args.input else None)
        write_report(output, report, ROOT)
        print("V3 local shadow: partial coverage; " + str(len(report["events"])) +
              " national observations; publication disabled; state committed=" +
              str(report["persistence"]["committed"]).lower() + ".")
        return 2 if report["status"] == "verification_required" else 0
    except (StoreError, ValidationError, ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        # Safe diagnostics: never print credentials, response bodies or raw exceptions.
        safe_codes = {"state_invalid_recovery_required", "state_writer_locked", "clock_rollback",
                      "no_valid_recovery_generation", "ambiguous_recovery_generation",
                      "iana_timezone_unavailable", "timestamp_requires_offset", "invalid_timestamp"}
        code = str(exc) if isinstance(exc, (StoreError, ValidationError)) and str(exc) in safe_codes else "local_run_failed"
        try:
            if output is not None:
                write_report(output, failure_report(now, code), ROOT)
        except (OSError, ValueError, TypeError):
            pass
        print("Verification required: configuration, state or output invalid. No publication; inspect local setup.",
              file=sys.stderr)
        return 2


def failure_report(now, code):
    return {"schema_version": 3, "mode": "local_shadow", "generated_at": stamp(now),
            "run_id": digest([stamp(now), code]), "status": "verification_required", "coverage": "partial",
            "safety_conclusion": None, "publication_authorized": False, "automatic_publication": False,
            "initial_observation": False, "no_change": False, "sources": {}, "events": [],
            "changes": [], "diagnostics": [{"kind": "insufficient_coverage", "code": code}],
            "destination_contexts": {}, "pending_review": [], "candidate_duplicate_groups": [],
            "persistence": {"committed": False, "generation": None, "token": None, "error_code": code}}


if __name__ == "__main__":
    raise SystemExit(main())
