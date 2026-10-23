"""Local review artifacts only; no patch, public renderer or Git integration."""
from __future__ import annotations

import html
import os
from pathlib import Path
import tempfile

from .storage import atomic_json
from .validation import safe_external_directory


def safe_text(value):
    return "".join("&#" + str(ord(char)) + ";" if char in "\\`[]()*_!#|" else
                   html.escape(char, quote=False) for char in str(value))


def markdown(report):
    lines = ["# Global Travel Intelligence V3 — local human review", "",
             "Run: " + report["generated_at"], "Run ID: " + report["run_id"], "",
             "**Partial monitoring. No safety conclusion. Publication disabled.**", "",
             "Canadian national advice is for Canadian travellers. A country bulletin is not a confirmed city incident.", "",
             "- Status: " + safe_text(report["status"]),
             "- No change detected in comparable data: " + str(report["no_change"]).lower(),
             "- Initial observation: " + str(report["initial_observation"]).lower(),
             "- Durable local state committed: " + str(report["persistence"]["committed"]).lower(),
             "- Changed review items: " + str(len(report["changes"])), ""]
    for ident, source in sorted(report["sources"].items()):
        lines += ["## " + safe_text(ident), "", "- Status: " + safe_text(source["status"]),
                  "- Attempted: " + source["last_attempt_at"],
                  "- Last successful observation: " + (source["last_success_at"] or "none"),
                  "- Source export generated: " + (source["source_generated_at"] or "unknown"),
                  "- Diagnostic: " + (source["error_code"] or "none"), ""]
    for event in report["events"]:
        lines += ["## " + safe_text(event["country_code"] or "Uncertain geography"), "",
                  "- Type/scope: " + event["record_kind"] + " / " + event["geographic_scope"],
                  "- Source: [Official bulletin](" + event["source_url"] + ")",
                  "- Source published: " + (event["published_at"] or event["source_published_date"] or "unknown"),
                  "- Last observed: " + event["observed_at"],
                  "- Last technical verification: " + (event["last_verified_at"] or "unknown"),
                  "- Review due: " + event["review_due_at"],
                  "- Technical freshness ends: " + event["fresh_until"],
                  "- Review / lifecycle: " + event["human_review_status"] + " / " + event["lifecycle_status"],
                  "- Source level (not a city impact): " + safe_text(event["source_severity_raw"]),
                  "- Source change text (unreviewed): " + safe_text(event["source_data"].get("update-summary", "not provided")),
                  "- Publication: withheld. Traveler impact: not established.", ""]
        for context in report["destination_contexts"][event["event_id"]]:
            lines.append("- Review context only: " + safe_text(context["destination_id"]) +
                         " (" + context["relationship"] + "); no confirmed local incident.")
        lines.append("")
    lines += ["## Changes and coverage gaps", ""]
    for item in report["changes"] + report["diagnostics"]:
        lines.append("- " + safe_text(item))
    if not report["changes"] and not report["diagnostics"]:
        lines.append("No relevant changes in the monitored data; this does not establish normal conditions.")
    lines += ["", "Other health, disaster and local transport sources are not enabled.",
              "Expiry, missing data or source unavailability never establish that a danger has ended.",
              "No public copy, patch, approval, PR or deployment is produced.", ""]
    return "\n".join(lines)


def write_report(directory, report, checkout):
    out = safe_external_directory(directory, checkout)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("report.json", "report.md"):
        path = out / name
        if path.is_symlink() or path.is_junction():
            raise ValueError("linked_report_path")
    atomic_json(out / "report.json", report)
    descriptor, temporary = tempfile.mkstemp(prefix=".pending-report-", dir=out)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(markdown(report).encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, out / "report.md")
    finally:
        Path(temporary).unlink(missing_ok=True)
