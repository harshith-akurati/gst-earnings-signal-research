#!/usr/bin/env python3
"""HYP-01 prospective progress reporter — STRICTLY READ-ONLY, REDACTED BY CONSTRUCTION.

Reports how far prospective collection has advanced toward the binding target of
60 eligible events. It answers only "how many, and why not more".

WHAT THIS PRINTS
  - captured dates seen
  - eligible-event count
  - exclusion counts, by the registered reason codes in
    GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md section 1
  - events remaining until 60
  - missing required artifacts

WHAT THIS NEVER PRINTS
  No search value, price, return, gap, z-score, volatility, volume or any other
  measured quantity. Redaction is structural, not a formatting convention: this
  module never reads a measurement field into a printable variable. The only
  values that reach stdout are counts, dates, ticker-free reason codes and
  file paths. `test_hyp01_progress_report.py` asserts this on synthetic data.

WHAT THIS DOES NOT DO
  - It does not enroll events. Enrollment is a human, verified step
    (`HumanVerifiedEventRegistry`); an event absent from the registry is
    reported as NOT_ENROLLED, which is itself a registered disposition.
  - It does not compute, fit, simulate or forecast anything.
  - It does not write. No file is created, modified or deleted.
  - It is deliberately NOT wired to Task Scheduler.
  - It does not freeze the cohort. Reaching 60 licenses a human freeze
    procedure; this tool only reports the count.

STATUS: reporting only. It resolves no open scientific decision. In particular
it does not supply a SESOI, an equivalence procedure, or a power calculation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINDING_TARGET = 60
CANONICAL_STATUS_SCHEMA = "GST_HYP01_ELIGIBILITY_STATUS_v1"  # GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json freeze_and_display.threshold

# Registered dispositions, verbatim from the eligibility ladder, section 1.
REASONS = (
    "NOT_ENROLLED",
    "CLASS_INELIGIBLE",
    "CORE_GATE_FAILED",
    "D1_GATE_FAILED",
    "GST_PROVENANCE_FAILED",
    "OUTCOME_MISSING",
    "MEASUREMENT_INCOMPATIBLE_INTRADAY",
    "EXTENSION_COHORT",
)

# NOTE: the cohort protocol is deliberately ABSENT from this list. Both
# committed versions carry status: DRAFT and are adopted by no authorization
# artifact, so their absence is not a defect and their presence proves nothing.
# A cohort protocol is listed again only once an adopted instrument names the
# authoritative path.
REQUIRED_ARTIFACTS = (
    "Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md",
    "Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json",
    "Live Signal Engine/GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json",
    "Live Signal Engine/Market_Response_Event_Registry/registry.jsonl",
)

# Identity/provenance keys that may be read. Anything not listed is treated as a
# measurement and is never touched. Whitelist, not blacklist, so a new
# measurement column added upstream cannot leak by default.
from gst_market_response.event_registry import (  # noqa: E402
    HumanVerifiedEventRegistry,
)

SAFE_EVENT_KEYS = frozenset({
    "event_id", "ticker", "earnings_date", "expected_response_session",
    "release_market_session", "verification_status", "row_type", "row_id",
})


ROW_REGISTRATION = "REGISTRATION"
ROW_AMENDMENT = "AMENDMENT"


def _safe(record: dict) -> dict:
    """Project a record onto identity/provenance keys only."""
    return {k: v for k, v in record.items() if k in SAFE_EVENT_KEYS}


def load_registry(root: Path) -> tuple[list[dict], str | None, int]:
    """The canonical EFFECTIVE registry view: one row per event, amendments
    folded in.

    The fold is HumanVerifiedEventRegistry.effective_row() -- the canonical
    implementation, called directly -- so this reporter and the eligibility
    driver cannot drift apart. Rows are projected onto SAFE_EVENT_KEYS
    immediately on ingest, so the redaction guarantee is unaffected by reading
    through the registry class.

    Returns (effective_rows, error, amendment_row_count).
    """
    reg_dir = root / "Live Signal Engine/Market_Response_Event_Registry"
    p = reg_dir / "registry.jsonl"
    if not p.exists():
        return [], f"missing: {p.relative_to(root).as_posix()}", 0
    # Constructed only after confirming the log exists, so the constructor's
    # mkdir(exist_ok=True) can never create anything: this tool stays read-only.
    registry = HumanVerifiedEventRegistry(reg_dir)
    try:
        raw = registry.read_all()
    except json.JSONDecodeError:
        return [], "registry.jsonl contains an unparseable line", 0

    amendments = sum(1 for r in raw if r.get("row_type") == ROW_AMENDMENT)
    order: list[str] = []
    for r in raw:
        eid = r.get("event_id")
        if eid and eid not in order:
            order.append(eid)

    rows = []
    for eid in order:
        effective = registry.effective_row(eid)
        if effective is None:
            # Amendment rows with no base REGISTRATION. Surfaced as a structural
            # problem rather than counted as an event.
            rows.append({"event_id": eid, "row_type": None})
            continue
        rows.append(_safe(effective))
    return rows, None, amendments


def captured_dates(root: Path) -> list[str]:
    """Panel capture dates, taken from FILENAMES only. No panel file is opened."""
    d = root / "Live Signal Engine"
    if not d.is_dir():
        return []
    out = set()
    for f in d.glob("GST_Phase2_DailyPanel_TestRun_*_run3_COMPLETION_MARKER.json"):
        parts = f.name.split("_")
        for token in parts:
            if len(token) == 10 and token[4] == "-" and token[7] == "-":
                out.add(token)
    return sorted(out)


def classify(events: list[dict]) -> tuple[int, Counter]:
    """Registry-only enrollment status. **This is not an eligibility evaluation.**

    The eligibility ladder S-2..S-7 needs the pre-event marker, the GST evidence,
    the D1 evidence and the operations plan. This tool opens none of them, so it
    cannot determine any of those gates and does not pretend to.

    What changed and why. This function used to return `eligible = 0` and let the
    caller present that as a real eligible-event count with a
    `remaining_until_target` derived from it. Zero-because-unevaluated is not
    zero-because-assessed, and reporting the two identically overstated what was
    known. It also assigned MEASUREMENT_INCOMPATIBLE_INTRADAY -- a terminal S-7
    disposition -- to an event whose S-2..S-6 gates had never been evaluated,
    inverting the registered gate order.

    Now: registry-derived facts only, labelled descriptively.
    """
    counts = Counter({
        "ENROLLED_AWAITING_EVALUATION": 0,
        "NOT_ENROLLED": 0,
        "STRUCTURAL_REGISTRY_PROBLEM": 0,
    })
    # Descriptive registry-only observations. NOT dispositions, NOT terminal.
    descriptive = Counter({
        "registered_session_bmo_or_amc": 0,
        "registered_session_intraday": 0,
        "registered_session_absent": 0,
    })
    for e in events:
        if e.get("row_type") != ROW_REGISTRATION:
            counts["STRUCTURAL_REGISTRY_PROBLEM"] += 1
            continue
        if str(e.get("verification_status", "")).lower() != "verified":
            counts["NOT_ENROLLED"] += 1
            continue
        counts["ENROLLED_AWAITING_EVALUATION"] += 1
        session = str(e.get("release_market_session") or "").upper()
        if session in ("BMO", "AMC"):
            descriptive["registered_session_bmo_or_amc"] += 1
        elif session:
            # Registry-only observation. S-7 is NOT applied here: an event whose
            # S-2..S-6 gates are unevaluated has no terminal disposition, and an
            # INTRADAY registration is descriptive until the ladder runs.
            descriptive["registered_session_intraday"] += 1
        else:
            descriptive["registered_session_absent"] += 1
    return counts, descriptive


def read_canonical_status(path: Path) -> tuple[dict | None, str]:
    """Load a canonical eligibility-status document, verifying schema and digest.

    This is the ONLY source from which a real eligible-event count may be
    rendered. Anything unverifiable yields (None, reason) and the caller falls
    back to NOT_EVALUATED rather than inventing a count.
    """
    if path is None:
        return None, "no canonical status document supplied"
    p = Path(path)
    if not p.is_file():
        return None, f"canonical status document not found: {p}"
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"canonical status document is not valid JSON: {exc}"
    if not isinstance(doc, dict):
        return None, "canonical status document is not a JSON object"
    if doc.get("schema") != CANONICAL_STATUS_SCHEMA:
        return None, (f"schema is {doc.get('schema')!r}, expected "
                      f"{CANONICAL_STATUS_SCHEMA!r}")
    for field in ("eligible_event_count", "binding_target", "effective_events_seen",
                  "exclusions_by_reason", "registry_snapshot_sha256"):
        if field not in doc:
            return None, f"canonical status document lacks {field!r}"
    # Digest of the document's own bytes, so a reader can tie a rendered count
    # back to the exact artifact it came from.
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    doc["_status_document_sha256"] = digest
    doc["_status_document_path"] = p.as_posix()
    return doc, "ok"


def missing_artifacts(root: Path) -> list[str]:
    return [a for a in REQUIRED_ARTIFACTS if not (root / a).exists()]


def build_report(root: Path, canonical_status: Path | None = None) -> dict:
    events, reg_err, amendment_rows = load_registry(root)
    counts, descriptive = classify(events)
    status_doc, status_note = read_canonical_status(canonical_status)
    dates = captured_dates(root)
    rep = {
        "binding_target": BINDING_TARGET,
        "effective_events_seen": len(events),
        "amendment_rows_folded": amendment_rows,
        "registry_error": reg_err,
        "enrollment_counts": dict(counts),
        "registry_only_observations": dict(descriptive),
        "captured_panel_dates": dates,
        "captured_panel_date_count": len(dates),
        "missing_required_artifacts": missing_artifacts(root),
        "notes": [
            "Read-only. No file was written.",
            "No search, price, return, gap or outcome value was read or printed.",
            "Registry rows are REGISTRATION and AMENDMENT. Amendments are folded "
            "into one effective event by HumanVerifiedEventRegistry.effective_row() "
            "and are never counted as separate events.",
            "enrollment_counts are REGISTRY-DERIVED ONLY. registry_only_observations "
            "are descriptive, not dispositions: S-7 is never applied here, because "
            "S-2..S-6 cannot be evaluated without evidence this tool does not open.",
        ],
    }

    if status_doc is not None:
        # A verified canonical status document is the ONLY source of a real
        # eligible-event count.
        rep["eligibility_evaluated"] = True
        rep["eligible_event_count"] = status_doc["eligible_event_count"]
        rep["remaining_until_target"] = max(
            0, BINDING_TARGET - int(status_doc["eligible_event_count"]))
        rep["exclusions_by_reason"] = status_doc["exclusions_by_reason"]
        rep["canonical_status_document"] = {
            "path": status_doc["_status_document_path"],
            "sha256": status_doc["_status_document_sha256"],
            "schema": status_doc["schema"],
            "registry_snapshot_sha256": status_doc["registry_snapshot_sha256"],
        }
        rep["notes"].append(
            "Eligibility counts were read from the canonical status document named "
            "above, whose schema and SHA-256 were verified.")
    else:
        rep["eligibility_evaluated"] = False
        rep["eligible_event_count"] = "NOT_EVALUATED"
        rep["remaining_until_target"] = "NOT_EVALUATED"
        rep["exclusions_by_reason"] = "NOT_EVALUATED"
        rep["canonical_status_document"] = None
        rep["eligibility_not_evaluated_reason"] = status_note
        rep["notes"].append(
            "NO eligible-event count is reported. Eligibility was NOT evaluated: "
            + status_note + ". A zero here would mean 'unevaluated', not "
            "'assessed and found zero', so no count and no remaining_until_target "
            "is derived.")
    return rep


def render(rep: dict) -> str:
    L = []
    L.append("=" * 66)
    L.append("HYP-01 PROSPECTIVE PROGRESS  (read-only, redacted)")
    L.append("=" * 66)
    L.append(f"  eligible events           : {rep['eligible_event_count']}")
    L.append(f"  binding target            : {rep['binding_target']}")
    L.append(f"  remaining until target    : {rep['remaining_until_target']}")
    L.append(f"  effective events seen     : {rep['effective_events_seen']}")
    L.append(f"  amendment rows folded     : {rep['amendment_rows_folded']}")
    L.append(f"  eligibility evaluated     : {rep['eligibility_evaluated']}")
    for k, v in rep["enrollment_counts"].items():
        L.append(f"    {k:38}: {v}")
    L.append("  registry-only observations (descriptive, not dispositions):")
    for k, v in rep["registry_only_observations"].items():
        L.append(f"    {k:38}: {v}")
    L.append(f"  captured panel dates      : {rep['captured_panel_date_count']}")
    for d in rep["captured_panel_dates"]:
        L.append(f"      {d}")
    if rep["eligibility_evaluated"]:
        L.append(f"  eligible events           : {rep['eligible_event_count']}")
        L.append(f"  remaining until target    : {rep['remaining_until_target']}")
        csd = rep["canonical_status_document"]
        L.append(f"  canonical status doc      : {csd['path']}")
        L.append(f"    sha256                  : {csd['sha256']}")
        L.append("  exclusions by registered reason:")
        for k in sorted(rep["exclusions_by_reason"]):
            L.append(f"      {k:42} {rep['exclusions_by_reason'][k]}")
    else:
        L.append("  eligible events           : NOT_EVALUATED")
        L.append("  remaining until target    : NOT_EVALUATED")
        L.append(f"    reason                  : {rep['eligibility_not_evaluated_reason']}")
    miss = rep["missing_required_artifacts"]
    L.append(f"  missing required artifacts: {len(miss)}")
    for m in miss:
        L.append(f"      MISSING {m}")
    if rep["registry_error"]:
        L.append(f"  registry error            : {rep['registry_error']}")
    L.append("")
    for n in rep["notes"]:
        L.append(f"  note: {n}")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hyp01_progress_report")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    a = ap.parse_args(argv)
    rep = build_report(Path(a.root))
    print(json.dumps(rep, indent=2) if a.json else render(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
