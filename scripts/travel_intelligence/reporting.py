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
             "National advice is audience-specific. A disaster observation or modeled hazard does not establish traveler impact.", "",
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
        lines += ["## " + safe_text(event["country_code"] or ("Epicenter point; destination unassigned"
                      if event["source_id"] == "usgs-earthquakes" else "Uncertain geography")), "",
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
        if event["source_id"] == "usgs-earthquakes":
            data = event["source_data"]
            lines += ["- Observed earthquake; measurement review: " + safe_text(data["review-status"]),
                      "- Magnitude / type: " + safe_text(data["magnitude"] if data["magnitude"] is not None else "unknown") + " / " + safe_text(data["magnitude-type"] or "unknown"),
                      "- Epicenter longitude / latitude / depth km: " + safe_text(data["longitude"]) +
                      " / " + safe_text(data["latitude"]) + " / " + safe_text(data["depth-km"]),
                      "- Occurred / revised: " + event["starts_at"] + " / " + event["source_updated_at"],
                      "- USGS tsunami flag: " + str(data["tsunami-flag"]) +
                      "; not an active tsunami warning or evacuation order.",
                      "- Credit: U.S. Geological Survey. Measurement review is not impact verification.", ""]
        if event["source_id"] == "gdacs-multi-hazard":
            data = event["source_data"]
            lines += ["- GDACS potential hazard assessment, not a delegated official public warning.",
                      "- Hazard / episode: " + safe_text(data["event-type"]) + " / " + str(data["episode-id"]),
                      "- Source level / episode level: " + safe_text(data["alert-level"]) + " / " + safe_text(data["episode-alert-level"]),
                      "- Source date basis: " + safe_text(data["time-basis"]),
                      "- Source start / reported end / modified: " + safe_text(data["from-text"]) + " / " +
                      safe_text(data["to-text"]) + " / " + safe_text(data["modified-text"]),
                      "- The reported end or current=false is not a verified end of danger.",
                      "- Country context only: " + safe_text(data["country-contexts"] or "unresolved"),
                      "- Geometry: " + safe_text(data["geometry-summary"]),
                      "- Tsunami assessment not collected; no active tsunami warning or evacuation order inferred.",
                      "- Credit: Global Disaster Awareness and Coordination System, GDACS.", ""]
        for context in report["destination_contexts"][event["event_id"]]:
            lines.append("- Review context only: " + safe_text(context["destination_id"]) +
                         " (" + context["relationship"] + "); no confirmed local incident.")
        lines.append("")
    if "observation_groups" in report:
        lines += ["## Source relationships and review", "", safe_text(report["grouping_statement"]), ""]
        for item in report["observation_groups"] + report["cross_source_relationships"] + report["possible_duplicate_review"]:
            lines.append("- " + safe_text(item))
        lines.append("")
    lines += ["## Changes and coverage gaps", ""]
    for item in report["changes"] + report["diagnostics"]:
        lines.append("- " + safe_text(item))
    if not report["changes"] and not report["diagnostics"]:
        lines.append("No relevant changes in the monitored data; this does not establish normal conditions.")
    lines += ["", "Other unconfigured sources and disaster categories are not monitored.",
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
