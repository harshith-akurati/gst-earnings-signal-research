#!/usr/bin/env python3
"""HYP-01 exact GST/D1 join and deterministic eligibility-counting driver.

Implements the two components the locked artifacts specify but no code provided:
an exact-key join between the GST measurement leg and the D1 market-response
leg, and a driver that counts eligible events against the locked 60-event gate.

GOVERNING ARTIFACTS
  Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md
      section 1  the eight-step ladder and its registered dispositions
      section 2  ordering: sort key = (response_session_date ASC, event_id ASC)
      section 5  freeze procedure, triggered exactly once at the 60th event
      section 6  extension cohort; no optional stopping; no model change
  Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_v1.0.json
      /sample/inclusion_conditions   the step rules
      /primary_outcome/field         abs_overnight_gap
      freeze_and_display.threshold   60
  gst_market_response/completeness.py   the three implemented gate functions

WHAT THIS DOES NOT DO
  - It does not enroll events. Enrollment is a human verified decision recorded
    in the registry; this module only reads `verification_status`.
  - It does not freeze the cohort, record the environment freeze, or authorize
    or run the primary model. Reaching 60 REFUSES further counting and emits a
    freeze-required signal for a human to act on (section 5 steps 1-4).
  - It does not print any measurement value. Statuses, counts, identifiers,
    dates, reason codes and provenance hashes only.
  - It performs no network access and opens no real prospective record when
    driven at a synthetic root.

INACTIVE BY DESIGN. Nothing here is wired to Task Scheduler, and this module
was never executed against real prospective data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gst_market_response.completeness import (  # noqa: E402
    D1_REQUIRED_FIELDS, STRICT_CORE_REQUIRED_PROVENANCE, STRICT_CORE_SIX_FIELDS,
    STRICT_CORE_STATUS_KEY, STRICT_CORE_SUCCESS_STATUSES,
    evaluate_strict_core_v0_2, is_valid_d1_decomposition,
)

# freeze_and_display.threshold in GST_HYP01_ANALYSIS_LOCK_v1.0.json
BINDING_TARGET = 60

# Registered dispositions, verbatim from the ladder, section 1.
R_NOT_ENROLLED = "NOT_ENROLLED"
R_CLASS_INELIGIBLE = "CLASS_INELIGIBLE"
R_CORE_GATE_FAILED = "CORE_GATE_FAILED"
R_D1_GATE_FAILED = "D1_GATE_FAILED"
R_GST_PROVENANCE_FAILED = "GST_PROVENANCE_FAILED"
R_OUTCOME_MISSING = "OUTCOME_MISSING"
R_MEASUREMENT_INCOMPATIBLE_INTRADAY = "MEASUREMENT_INCOMPATIBLE_INTRADAY"
R_EXTENSION_COHORT = "EXTENSION_COHORT"

REASONS = (
    R_NOT_ENROLLED, R_CLASS_INELIGIBLE, R_CORE_GATE_FAILED, R_D1_GATE_FAILED,
    R_GST_PROVENANCE_FAILED, R_OUTCOME_MISSING,
    R_MEASUREMENT_INCOMPATIBLE_INTRADAY, R_EXTENSION_COHORT,
)

# Join-integrity refusals. These are not eligibility dispositions -- they mean
# the record set is malformed and no disposition may be assigned at all.
J_DUPLICATE_EVENT = "JOIN_REFUSED_DUPLICATE_EVENT"
J_DUPLICATE_LEG = "JOIN_REFUSED_DUPLICATE_LEG"
J_MISSING_GST_LEG = "JOIN_REFUSED_MISSING_GST_LEG"
J_MISSING_D1_LEG = "JOIN_REFUSED_MISSING_D1_LEG"
J_KEY_MISMATCH = "JOIN_REFUSED_KEY_MISMATCH"
J_UNEXPECTED_FIELD = "JOIN_REFUSED_UNEXPECTED_SCHEMA_FIELD"
J_NO_CAPTURE_TIME = "JOIN_REFUSED_NO_CAPTURE_TIME"

JOIN_REFUSALS = (
    J_DUPLICATE_EVENT, J_DUPLICATE_LEG, J_MISSING_GST_LEG, J_MISSING_D1_LEG,
    J_KEY_MISMATCH, J_UNEXPECTED_FIELD, J_NO_CAPTURE_TIME,
)

# NOTE ON THE DIVISION OF LABOUR between refusals and dispositions.
# The join establishes IDENTITY only: does exactly one GST leg and one D1 leg
# exist for this registered event, under exactly the registered keys, carrying
# only known columns. Those are structural questions with no registered
# scientific disposition, so they REFUSE -- no event is counted or excluded on
# a malformed record set, and the operator must fix the input.
#
# Provenance QUALITY is a different question and the ladder already has
# registered codes for it: step 5 (GST_PROVENANCE_FAILED) and step 6
# (OUTCOME_MISSING). Checking provenance content in the join would emit an
# unregistered code where a registered one exists, and would make
# GST_PROVENANCE_FAILED unreachable. So it is checked in classify(), not here.

# Step 5 of the ladder: gst_zscore non-null AND source_status_gst successful.
# Bound to the locked constant so it cannot diverge from the core gate.
GST_OK_STATUSES = frozenset(STRICT_CORE_SUCCESS_STATUSES)

# Step 7: release session must be one of these. Anything else is intraday and
# measurement-incompatible.
VALID_SESSIONS = frozenset({"BMO", "AMC"})

# The only identifier keys a join may use. Registered identifiers only -- no
# company name, no fuzzy ticker, no nearest date.
JOIN_KEYS = ("event_id", "ticker", "earnings_date")

# Keys permitted on a joined leg. Anything else is an unexpected schema field
# and refuses, so an upstream column cannot silently enter the pipeline.
# The strict v0.2 core gate reads all six panel fields and their five per-leg
# source statuses, so the whitelist must admit exactly those and nothing more.
# Sourced from completeness.STRICT_CORE_SIX_FIELDS / STRICT_CORE_STATUS_KEY /
# STRICT_CORE_REQUIRED_PROVENANCE rather than restated, so the two cannot drift.
GST_LEG_ALLOWED = frozenset({
    *JOIN_KEYS, *STRICT_CORE_SIX_FIELDS, *STRICT_CORE_STATUS_KEY.values(),
    *STRICT_CORE_REQUIRED_PROVENANCE, "provenance_path", "provenance_sha256",
    "captured_at_utc",
})
D1_LEG_ALLOWED = frozenset({
    *JOIN_KEYS, "release_market_session", "response_session_date",
    "abs_overnight_gap", *D1_REQUIRED_FIELDS, "provenance_path",
    "provenance_sha256", "captured_at_utc", "market_data_provenance_valid",
})


class JoinRefusal(Exception):
    """Raised when the record set is malformed. Carries a registered code."""

    def __init__(self, code: str, event_id: str, detail: str = ""):
        super().__init__(f"{code}: {event_id} {detail}".strip())
        self.code = code
        self.event_id = event_id
        self.detail = detail


def _sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def _present(fields: dict, key: str) -> bool:
    return fields.get(key) is not None


def _check_schema(leg: dict, allowed: frozenset, event_id: str, which: str) -> None:
    extra = sorted(set(leg) - allowed)
    if extra:
        raise JoinRefusal(J_UNEXPECTED_FIELD, event_id, f"{which} leg: {extra}")


def provenance_ok(leg: dict) -> bool:
    """A leg carries usable provenance: a non-empty path and a well-formed
    lowercase SHA-256. Absent or malformed provenance is a FAILED gate, not a
    silently-accepted one."""
    path = leg.get("provenance_path")
    digest = leg.get("provenance_sha256")
    if not path or not isinstance(digest, str):
        return False
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def _index_unique(legs: Iterable[dict], which: str) -> dict:
    """Index legs by event_id, refusing duplicates.

    Duplication and a missing event_id are WHOLE-SET ambiguities: there is no
    correct per-event answer, so they raise and stop the run. Schema validation
    is deliberately NOT done here -- an unexpected column affects one event, and
    a per-event problem should refuse that event, not the other 59.
    """
    out: dict[str, dict] = {}
    for leg in legs:
        eid = leg.get("event_id")
        if not eid:
            raise JoinRefusal(J_KEY_MISMATCH, "<none>", f"{which} leg has no event_id")
        if eid in out:
            raise JoinRefusal(J_DUPLICATE_LEG, eid, f"{which} leg appears twice")
        out[eid] = leg
    return out


def join_event(registration: dict, gst_leg: dict | None, d1_leg: dict | None) -> dict:
    """Exact-key join for one event. Refuses rather than guessing.

    Returns the joined record. Raises JoinRefusal on any integrity problem.
    """
    eid = registration.get("event_id")
    if not eid:
        raise JoinRefusal(J_KEY_MISMATCH, "<none>", "registration has no event_id")
    if gst_leg is None:
        raise JoinRefusal(J_MISSING_GST_LEG, eid)
    if d1_leg is None:
        raise JoinRefusal(J_MISSING_D1_LEG, eid)

    _check_schema(gst_leg, GST_LEG_ALLOWED, eid, "gst")
    _check_schema(d1_leg, D1_LEG_ALLOWED, eid, "d1")

    # Every join key must match EXACTLY across all three sources.
    for k in JOIN_KEYS:
        vals = {str(registration.get(k)), str(gst_leg.get(k)), str(d1_leg.get(k))}
        if len(vals) != 1 or "None" in vals:
            raise JoinRefusal(J_KEY_MISMATCH, eid, f"key {k!r} differs across legs")

    # An undated capture cannot be ordered or audited, so it is refused rather
    # than reinterpreted. The VALUE of the timestamp is never compared against
    # anything here -- that would require reading the measurement schedule.
    for leg, which in ((gst_leg, "gst"), (d1_leg, "d1")):
        if not leg.get("captured_at_utc"):
            raise JoinRefusal(J_NO_CAPTURE_TIME, eid, f"{which} leg has no capture time")

    return {
        "event_id": eid,
        "ticker": registration["ticker"],
        "earnings_date": registration["earnings_date"],
        "release_market_session": d1_leg.get("release_market_session"),
        "response_session_date": d1_leg.get("response_session_date"),
        "gst": gst_leg,
        "d1": d1_leg,
        "provenance": {
            "gst_path": gst_leg.get("provenance_path"),
            "gst_sha256": gst_leg.get("provenance_sha256"),
            "d1_path": d1_leg.get("provenance_path"),
            "d1_sha256": d1_leg.get("provenance_sha256"),
        },
    }


def classify(registration: dict, joined: dict | None,
             refusal: JoinRefusal | None) -> tuple[bool, str | None]:
    """Apply the ladder to one event. Returns (eligible, reason_or_None).

    Steps 1-7 only. Step 8 (rank <= 60) is a property of the ordered set and is
    applied by the driver, not per event.
    """
    # Step 1 -- enrolled under cohort protocol v1.0, human verified.
    if str(registration.get("verification_status", "")).lower() != "verified":
        return False, R_NOT_ENROLLED
    if str(registration.get("row_type", "event")).lower() != "event":
        return False, R_NOT_ENROLLED

    if refusal is not None:
        # A malformed record set is not a scientific disposition. Surface the
        # join code; the driver tallies it separately and counts nothing.
        return False, refusal.code
    assert joined is not None

    # Step 2 -- hypothesis-family gate.
    if str(registration.get("hypothesis_class", "core_attention_vs_equity_response")) \
            != "core_attention_vs_equity_response":
        return False, R_CLASS_INELIGIBLE

    # Step 7 -- release session. Checked before the outcome gates because an
    # intraday release is measurement-incompatible regardless of completeness.
    session = str(joined.get("release_market_session") or "").upper()
    if session not in VALID_SESSIONS:
        return False, R_MEASUREMENT_INCOMPATIBLE_INTRADAY

    # Step 3 -- strict core v0.2 over the six panel fields.
    core = evaluate_strict_core_v0_2(joined["gst"])
    if not getattr(core, "passed", False):
        return False, R_CORE_GATE_FAILED

    # Step 4 -- valid D1 decomposition.
    if not is_valid_d1_decomposition(joined["d1"]):
        return False, R_D1_GATE_FAILED

    # Step 5 -- GST provenance.
    if not _present(joined["gst"], "gst_zscore"):
        return False, R_GST_PROVENANCE_FAILED
    if str(joined["gst"].get("source_status_gst", "")) not in GST_OK_STATUSES:
        return False, R_GST_PROVENANCE_FAILED
    if not provenance_ok(joined["gst"]):
        return False, R_GST_PROVENANCE_FAILED

    # Step 6 -- abs_overnight_gap non-null with valid market-data provenance.
    if not _present(joined["d1"], "abs_overnight_gap"):
        return False, R_OUTCOME_MISSING
    if joined["d1"].get("market_data_provenance_valid") is not True:
        return False, R_OUTCOME_MISSING
    if not provenance_ok(joined["d1"]):
        return False, R_OUTCOME_MISSING

    return True, None


def _sort_key(rec: dict) -> tuple:
    """Section 2: (response_session_date ASC, event_id ASC)."""
    return (str(rec.get("response_session_date") or ""), str(rec.get("event_id") or ""))


def run_driver(registrations: list[dict], gst_legs: list[dict],
               d1_legs: list[dict]) -> dict:
    """Deterministic eligibility count. Pure: reads inputs, returns a status
    document. Writes nothing; the caller persists it."""
    tally = {r: 0 for r in REASONS}
    tally.update({j: 0 for j in JOIN_REFUSALS})

    seen: set[str] = set()
    for reg in registrations:
        eid = reg.get("event_id")
        if eid in seen:
            raise JoinRefusal(J_DUPLICATE_EVENT, str(eid), "registry lists it twice")
        seen.add(str(eid))

    gst_ix = _index_unique(gst_legs, "gst")
    d1_ix = _index_unique(d1_legs, "d1")

    candidates: list[dict] = []
    for reg in registrations:
        eid = str(reg.get("event_id"))
        joined = None
        refusal = None
        try:
            joined = join_event(reg, gst_ix.get(eid), d1_ix.get(eid))
        except JoinRefusal as e:
            refusal = e
        ok, reason = classify(reg, joined, refusal)
        if ok:
            candidates.append(joined)
        else:
            if reason in tally:
                tally[reason] += 1
            else:
                tally[reason] = tally.get(reason, 0) + 1

    # Step 8 -- deterministic order, rank <= 60 eligible, the rest extension.
    candidates.sort(key=_sort_key)
    eligible = candidates[:BINDING_TARGET]
    extension = candidates[BINDING_TARGET:]
    tally[R_EXTENSION_COHORT] += len(extension)

    count = len(eligible)
    at_gate = count >= BINDING_TARGET

    return {
        "schema": "GST_HYP01_ELIGIBILITY_STATUS_v1",
        "binding_target": BINDING_TARGET,
        "eligible_event_count": count,
        "remaining_until_target": max(0, BINDING_TARGET - count),
        "eligible_event_ids": [c["event_id"] for c in eligible],
        "extension_cohort_event_ids": [c["event_id"] for c in extension],
        "exclusions_by_reason": {k: v for k, v in sorted(tally.items()) if v or k in REASONS},
        "registry_rows_seen": len(registrations),
        "freeze_required": at_gate,
        "counting_state": "REFUSED_AT_GATE" if at_gate else "COUNTING",
        "freeze_note": (
            "The 60-event gate is reached. Further counting is REFUSED. Section 5 "
            "of the eligibility rules requires a human to freeze the event set, "
            "freeze the environment, re-verify all gates, and only then run the "
            "primary model once. This driver performs none of those steps and "
            "does not authorize the analysis."
            if at_gate else
            "Below the gate. Counting continues. No freeze is triggered."
        ),
        "analysis_authorized": False,
        "notes": [
            "No measurement or outcome value is included in this document.",
            "Enrollment is a human verified decision; this driver never enrolls.",
            "Events beyond rank 60 in the section-2 order are EXTENSION_COHORT and "
            "never enlarge the frozen set.",
        ],
    }


def status_digest(status: dict) -> str:
    """Stable digest for idempotence checks."""
    return _sha256_text(json.dumps(status, sort_keys=True, separators=(",", ":")))


def _load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hyp01_eligibility")
    ap.add_argument("--registry", required=True)
    ap.add_argument("--gst-legs", required=True)
    ap.add_argument("--d1-legs", required=True)
    ap.add_argument("--out", help="write the status document here (append-only)")
    a = ap.parse_args(argv)
    try:
        status = run_driver(_load_jsonl(Path(a.registry)),
                            _load_jsonl(Path(a.gst_legs)),
                            _load_jsonl(Path(a.d1_legs)))
    except JoinRefusal as e:
        print(f"REFUSED {e.code}: {e.event_id} {e.detail}".rstrip())
        return 2
    body = json.dumps(status, indent=2)
    if a.out:
        out = Path(a.out)
        if out.exists() and out.read_text(encoding="utf-8") == body:
            print("unchanged; nothing rewritten (idempotent)")
        else:
            out.write_text(body, encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
