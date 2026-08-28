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
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINDING_TARGET = 60  # GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json freeze_and_display.threshold

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

REQUIRED_ARTIFACTS = (
    "Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md",
    "Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json",
    "Live Signal Engine/GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json",
    "Live Signal Engine/GST_PROSPECTIVE_COHORT_PROTOCOL_v1.0.json",
    "Live Signal Engine/Market_Response_Event_Registry/registry.jsonl",
)

# Identity/provenance keys that may be read. Anything not listed is treated as a
# measurement and is never touched. Whitelist, not blacklist, so a new
# measurement column added upstream cannot leak by default.
SAFE_EVENT_KEYS = frozenset({
    "event_id", "ticker", "earnings_date", "expected_response_session",
    "release_market_session", "verification_status", "row_type", "row_id",
})


def _safe(record: dict) -> dict:
    """Project a record onto identity/provenance keys only."""
    return {k: v for k, v in record.items() if k in SAFE_EVENT_KEYS}


def load_registry(root: Path) -> tuple[list[dict], str | None]:
    p = root / "Live Signal Engine/Market_Response_Event_Registry/registry.jsonl"
    if not p.exists():
        return [], f"missing: {p.relative_to(root).as_posix()}"
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(_safe(json.loads(line)))
        except json.JSONDecodeError:
            return rows, "registry.jsonl contains an unparseable line"
    return rows, None


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
    """Apply only the dispositions decidable from identity/provenance fields.

    Any event whose eligibility cannot be decided without reading a measurement
    is counted as UNDETERMINED_REQUIRES_OUTCOME_CAPTURE rather than guessed. This
    tool will not open an outcome to settle a gate.
    """
    excl = Counter({r: 0 for r in REASONS})
    excl["UNDETERMINED_REQUIRES_OUTCOME_CAPTURE"] = 0
    eligible = 0
    for e in events:
        if e.get("row_type") not in (None, "event", "EVENT"):
            excl["NOT_ENROLLED"] += 1
            continue
        if e.get("verification_status") not in ("verified", "VERIFIED"):
            excl["NOT_ENROLLED"] += 1
            continue
        session = (e.get("release_market_session") or
                   e.get("expected_response_session") or "")
        if session.upper() not in ("BMO", "AMC"):
            excl["MEASUREMENT_INCOMPATIBLE_INTRADAY"] += 1
            continue
        # Steps 3-6 need the market-response capture legs, which are outcome
        # data. Not read here, by design.
        excl["UNDETERMINED_REQUIRES_OUTCOME_CAPTURE"] += 1
    return eligible, excl


def missing_artifacts(root: Path) -> list[str]:
    return [a for a in REQUIRED_ARTIFACTS if not (root / a).exists()]


def build_report(root: Path) -> dict:
    events, reg_err = load_registry(root)
    eligible, excl = classify(events)
    dates = captured_dates(root)
    return {
        "binding_target": BINDING_TARGET,
        "eligible_event_count": eligible,
        "remaining_until_target": max(0, BINDING_TARGET - eligible),
        "registry_rows_seen": len(events),
        "registry_error": reg_err,
        "captured_panel_dates": dates,
        "captured_panel_date_count": len(dates),
        "exclusions_by_reason": dict(excl),
        "missing_required_artifacts": missing_artifacts(root),
        "notes": [
            "Read-only. No file was written.",
            "No search, price, return, gap or outcome value was read or printed.",
            "Eligibility steps requiring market-response capture are reported as "
            "UNDETERMINED_REQUIRES_OUTCOME_CAPTURE, never guessed.",
            "Reaching the target licenses a human freeze procedure; this tool "
            "does not freeze anything.",
        ],
    }


def render(rep: dict) -> str:
    L = []
    L.append("=" * 66)
    L.append("HYP-01 PROSPECTIVE PROGRESS  (read-only, redacted)")
    L.append("=" * 66)
    L.append(f"  eligible events           : {rep['eligible_event_count']}")
    L.append(f"  binding target            : {rep['binding_target']}")
    L.append(f"  remaining until target    : {rep['remaining_until_target']}")
    L.append(f"  registry rows seen        : {rep['registry_rows_seen']}")
    L.append(f"  captured panel dates      : {rep['captured_panel_date_count']}")
    for d in rep["captured_panel_dates"]:
        L.append(f"      {d}")
    L.append("  exclusions by registered reason:")
    for k in sorted(rep["exclusions_by_reason"]):
        L.append(f"      {k:42} {rep['exclusions_by_reason'][k]}")
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
