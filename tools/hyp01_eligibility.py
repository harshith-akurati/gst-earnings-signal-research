#!/usr/bin/env python3
"""HYP-01 exact join and deterministic eligibility-counting driver.

Implements the two components the locked artifacts specify but no code
provided: an exact-key join across the canonical registry, the pre-event
module-eligibility marker, the GST leg and the D1 leg; and a driver that counts
eligible events against the locked 60-event gate.

GOVERNING ARTIFACTS
  Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md
      section 1  the S-1..S-8 ladder and its registered dispositions
      section 2  ordering: (response_session_date ASC, event_id ASC)
      section 5  freeze procedure, triggered exactly once at the 60th event
      section 6  extension cohort; no optional stopping; no model change
  Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_v1.0.json
      /sample/inclusion_conditions[0..7]   S-1..S-8, naming the mechanizer for
                                           S-2, S-3 and S-4
      /primary_outcome/field               abs_overnight_gap
  Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json
      freeze_and_display.threshold         60

CANONICAL SCHEMA FIDELITY
  Registry rows are `REGISTRATION` and `AMENDMENT` -- the row types
  EventRegistryRow actually validates. Amendment folding is delegated to
  HumanVerifiedEventRegistry.effective_row(); this module adds a validation
  pass in front of it and implements no second folding algorithm.

  S-2 is mechanised by completeness.is_eligible_for_hypothesis(), reading the
  module-eligibility block persisted on the pre-event stage marker. It is NOT
  read from the event registry, which carries no hypothesis-family field.

WHAT THIS DOES NOT DO
  - It does not enroll or amend events. Enrollment is a human verified decision
    recorded in the registry; this module only reads it.
  - It does not freeze the cohort, record the environment freeze, or authorize
    or run the primary model. Reaching 60 REFUSES further counting and emits a
    freeze-required signal for a human to act on (section 5 steps 1-4).
  - It does not read, derive or print any measurement value. Statuses, counts,
    identifiers, dates, reason codes and provenance hashes only. The marker's
    `response_magnitude` block carries real abs_* outcome values and is
    projected away on ingest rather than merely left unread.
  - It performs no network access.

INACTIVE BY DESIGN. Nothing here is wired to Task Scheduler, and this module
has never been executed against a real prospective record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gst_market_response.completeness import (  # noqa: E402
    D1_REQUIRED_FIELDS, HYPOTHESIS_CORE_ATTENTION_RESPONSE,
    STRICT_CORE_REQUIRED_PROVENANCE, STRICT_CORE_SIX_FIELDS,
    STRICT_CORE_STATUS_KEY, STRICT_CORE_SUCCESS_STATUSES, LegacyRecordError,
    evaluate_strict_core_v0_2, is_eligible_for_hypothesis,
    is_valid_d1_decomposition, read_module_eligibility,
)
from gst_market_response.event_registry import (  # noqa: E402
    HumanVerifiedEventRegistry,
)
from gst_market_response.stage_markers import STAGE_PRE_EVENT  # noqa: E402

# freeze_and_display.threshold in GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json
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

# --- Structural refusals ----------------------------------------------------
# A refusal is NOT a scientific disposition. It means an input artifact is
# absent or malformed, so no gate can be evaluated and no disposition may be
# assigned. An operator fixes the input; the event is neither eligible nor
# scientifically excluded in the meantime.
J_DUPLICATE_EVENT = "JOIN_REFUSED_DUPLICATE_EVENT"
J_DUPLICATE_LEG = "JOIN_REFUSED_DUPLICATE_LEG"
J_MISSING_GST_LEG = "JOIN_REFUSED_MISSING_GST_LEG"
J_MISSING_D1_LEG = "JOIN_REFUSED_MISSING_D1_LEG"
J_KEY_MISMATCH = "JOIN_REFUSED_KEY_MISMATCH"
J_UNEXPECTED_FIELD = "JOIN_REFUSED_UNEXPECTED_SCHEMA_FIELD"
J_NO_CAPTURE_TIME = "JOIN_REFUSED_NO_CAPTURE_TIME"

# Registry-shape refusals.
J_NO_BASE_REGISTRATION = "JOIN_REFUSED_NO_BASE_REGISTRATION"
J_DUPLICATE_BASE_REGISTRATION = "JOIN_REFUSED_DUPLICATE_BASE_REGISTRATION"
J_ORPHAN_AMENDMENT = "JOIN_REFUSED_ORPHAN_AMENDMENT"
J_ILLEGAL_IDENTITY_CHANGE = "JOIN_REFUSED_ILLEGAL_IDENTITY_CHANGE"
J_UNKNOWN_ROW_TYPE = "JOIN_REFUSED_UNKNOWN_ROW_TYPE"
J_MISSING_REGISTRY_FIELD = "JOIN_REFUSED_MISSING_REGISTRY_FIELD"

# Module-eligibility (S-2 evidence) refusals.
#
# WHY THESE HAD TO BE ADDED. Every registered disposition in section 1 is a
# SCIENTIFIC outcome; none of them describes "the artifact carrying the S-2
# decision is absent or unreadable". Mapping that to CLASS_INELIGIBLE would
# record a scientific exclusion that was never evaluated, and mapping it to
# eligible would be worse. completeness.LegacyRecordError is the canonical
# fail-closed mechanism for an unreadable eligibility block and is used
# directly; these codes only carry it out to the caller. They are the narrowest
# clearly-structural additions that keep the distinction intact, and they add
# no scientific disposition.
J_MISSING_PRE_EVENT_MARKER = "JOIN_REFUSED_MISSING_PRE_EVENT_MARKER"
J_MISSING_MODULE_ELIGIBILITY = "JOIN_REFUSED_MISSING_MODULE_ELIGIBILITY"
J_UNREADABLE_MODULE_ELIGIBILITY = "JOIN_REFUSED_UNREADABLE_MODULE_ELIGIBILITY"
J_MARKER_IDENTITY_MISMATCH = "JOIN_REFUSED_MARKER_IDENTITY_MISMATCH"

JOIN_REFUSALS = (
    J_DUPLICATE_EVENT, J_DUPLICATE_LEG, J_MISSING_GST_LEG, J_MISSING_D1_LEG,
    J_KEY_MISMATCH, J_UNEXPECTED_FIELD, J_NO_CAPTURE_TIME,
    J_NO_BASE_REGISTRATION, J_DUPLICATE_BASE_REGISTRATION, J_ORPHAN_AMENDMENT,
    J_ILLEGAL_IDENTITY_CHANGE, J_UNKNOWN_ROW_TYPE, J_MISSING_REGISTRY_FIELD,
    J_MISSING_PRE_EVENT_MARKER, J_MISSING_MODULE_ELIGIBILITY,
    J_UNREADABLE_MODULE_ELIGIBILITY, J_MARKER_IDENTITY_MISMATCH,
)

# Canonical registry row types. `event` is NOT one of them and never was.
ROW_REGISTRATION = "REGISTRATION"
ROW_AMENDMENT = "AMENDMENT"
CANONICAL_ROW_TYPES = (ROW_REGISTRATION, ROW_AMENDMENT)

# S-5: gst_zscore non-null AND source_status_gst successful. Bound to the
# locked constant so it cannot diverge from the core gate.
GST_OK_STATUSES = frozenset(STRICT_CORE_SUCCESS_STATUSES)

# S-7: eligible release sessions, per /sample/eligible_release_sessions.
VALID_SESSIONS = frozenset({"BMO", "AMC"})

# Registry fields this path depends on. Never defaulted when absent -- a
# missing one refuses (J_MISSING_REGISTRY_FIELD) rather than being invented.
REQUIRED_REGISTRY_FIELDS = (
    "event_id", "ticker", "fiscal_period", "earnings_date",
    "release_market_session", "expected_response_session",
    "verification_status", "row_type", "row_id",
)

# An AMENDMENT may correct timing, sourcing and status. It may NEVER change who
# the event is. effective_row() would fold such a change silently, so it is
# refused before the fold.
IDENTITY_FIELDS = ("event_id", "ticker", "fiscal_period")

# Join keys. Registered identifiers only -- no company name, no fuzzy ticker,
# no nearest date.
JOIN_KEYS = ("event_id", "ticker", "earnings_date")

# Whitelisted leg columns. Anything else refuses, so an upstream column cannot
# silently enter the pipeline.
GST_LEG_ALLOWED = frozenset({
    *JOIN_KEYS, *STRICT_CORE_SIX_FIELDS, *STRICT_CORE_STATUS_KEY.values(),
    *STRICT_CORE_REQUIRED_PROVENANCE, "provenance_path", "provenance_sha256",
    "captured_at_utc",
})
# The D1 leg no longer carries session or response-session date: both are
# registered human-verified timing and come from the effective registry row.
D1_LEG_ALLOWED = frozenset({
    *JOIN_KEYS, "abs_overnight_gap", *D1_REQUIRED_FIELDS, "provenance_path",
    "provenance_sha256", "captured_at_utc", "market_data_provenance_valid",
})

# Marker keys retained on ingest. `response_magnitude` is deliberately absent:
# it carries real abs_* outcome values, so it is projected away.
MARKER_KEEP = ("event_id", "stage", "module_eligibility",
               "module_eligibility_note", "lifecycle_state", "protocol_version")
MARKER_PROVENANCE_KEEP = ("ticker", "source_csv_sha256", "source_marker_sha256",
                          "pre_event_snapshot_asof_utc", "methodology_version")


class JoinRefusal(Exception):
    """Raised when an input artifact is absent or malformed. Carries a
    registered structural code."""

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
    lowercase SHA-256. Absent or malformed provenance is a FAILED gate."""
    path = leg.get("provenance_path")
    digest = leg.get("provenance_sha256")
    if not path or not isinstance(digest, str):
        return False
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


# ---------------------------------------------------------------------------
# Canonical registry handling
# ---------------------------------------------------------------------------

def validate_registry_rows(rows: list[dict]) -> None:
    """Structural validation of the raw append-only registry log.

    Runs BEFORE any fold and implements no folding of its own. Its purpose is
    to refuse the shapes effective_row() would otherwise absorb silently: a
    second base registration (it takes the first), an amendment pointing at
    nothing (it folds anyway), and an amendment that rewrites identity (it
    folds that too).
    """
    by_id: dict[str, str] = {}
    registrations: dict[str, int] = {}
    for r in rows:
        rt = r.get("row_type")
        eid = r.get("event_id") or "<none>"
        if rt not in CANONICAL_ROW_TYPES:
            raise JoinRefusal(J_UNKNOWN_ROW_TYPE, eid,
                              f"row_type={rt!r}; canonical types are {CANONICAL_ROW_TYPES}")
        rid = r.get("row_id")
        if not rid:
            raise JoinRefusal(J_MISSING_REGISTRY_FIELD, eid, "row_id absent")
        if rid in by_id:
            raise JoinRefusal(J_DUPLICATE_LEG, eid, f"row_id {rid!r} appears twice")
        by_id[rid] = eid
        if rt == ROW_REGISTRATION:
            registrations[eid] = registrations.get(eid, 0) + 1

    for eid, n in sorted(registrations.items()):
        if n > 1:
            raise JoinRefusal(J_DUPLICATE_BASE_REGISTRATION, eid,
                              f"{n} REGISTRATION rows; exactly one is required")

    base = {r["event_id"]: r for r in rows if r.get("row_type") == ROW_REGISTRATION}
    for r in rows:
        if r.get("row_type") != ROW_AMENDMENT:
            continue
        eid = r.get("event_id") or "<none>"
        amends = r.get("amends_row_id")
        if not amends:
            raise JoinRefusal(J_ORPHAN_AMENDMENT, eid, "amends_row_id absent")
        if amends not in by_id:
            raise JoinRefusal(J_ORPHAN_AMENDMENT, eid,
                              f"amends_row_id {amends!r} matches no row")
        if by_id[amends] != eid:
            raise JoinRefusal(J_ORPHAN_AMENDMENT, eid,
                              f"amends_row_id {amends!r} belongs to {by_id[amends]!r}")
        if eid not in registrations:
            raise JoinRefusal(J_NO_BASE_REGISTRATION, eid,
                              "AMENDMENT with no base REGISTRATION")
        # An amendment may correct timing, sourcing and status -- never identity.
        original = base.get(eid)
        for f in IDENTITY_FIELDS:
            if f in r and original is not None and r[f] != original.get(f):
                raise JoinRefusal(
                    J_ILLEGAL_IDENTITY_CHANGE, eid,
                    f"amendment changes {f}: {original.get(f)!r} -> {r[f]!r}")


def load_effective_registrations(registry_root: Path) -> list[dict]:
    """Validate the log, then return one effective row per event.

    The fold itself is HumanVerifiedEventRegistry.effective_row() -- the
    canonical implementation, called directly -- so no amendment-folding logic
    is reimplemented here and the two cannot drift.
    """
    registry = HumanVerifiedEventRegistry(Path(registry_root))
    rows = registry.read_all()
    validate_registry_rows(rows)

    # One entry per event_id, in first-appearance order. An amendment
    # contributes corrections to its event, never a new event.
    order: list[str] = []
    for r in rows:
        if r["event_id"] not in order:
            order.append(r["event_id"])

    effective = []
    for eid in order:
        row = registry.effective_row(eid)
        if row is None:
            raise JoinRefusal(J_NO_BASE_REGISTRATION, eid,
                              "no REGISTRATION row for this event_id")
        missing = sorted(f for f in REQUIRED_REGISTRY_FIELDS
                         if row.get(f) in (None, ""))
        if missing:
            raise JoinRefusal(J_MISSING_REGISTRY_FIELD, eid,
                              f"absent or blank: {missing}")
        effective.append(row)
    return effective


# ---------------------------------------------------------------------------
# S-2 evidence: the persisted pre-event module-eligibility marker
# ---------------------------------------------------------------------------

def project_marker(marker: dict) -> dict:
    """Keep only identity, provenance and the module-eligibility decision.

    Structural redaction: the marker's `response_magnitude` block carries real
    abs_* outcome values, so it is dropped here rather than carried around
    unread.
    """
    out = {k: marker[k] for k in MARKER_KEEP if k in marker}
    prov = marker.get("provenance") or {}
    out["provenance"] = {k: prov.get(k) for k in MARKER_PROVENANCE_KEEP if k in prov}
    return out


def module_eligibility_for(effective: dict, marker: dict | None):
    """Return the parsed ModuleEligibility for an event, or refuse.

    Fails closed on every unreadable path. A missing, null, legacy or malformed
    block is a STRUCTURAL input problem -- never silently CLASS_INELIGIBLE and
    never silently eligible.
    """
    eid = effective["event_id"]
    if marker is None:
        raise JoinRefusal(J_MISSING_PRE_EVENT_MARKER, eid,
                          "no pre-event stage marker supplied")
    if marker.get("stage") != STAGE_PRE_EVENT:
        raise JoinRefusal(J_MARKER_IDENTITY_MISMATCH, eid,
                          f"marker stage={marker.get('stage')!r}, expected {STAGE_PRE_EVENT!r}")
    if marker.get("event_id") != eid:
        raise JoinRefusal(J_MARKER_IDENTITY_MISMATCH, eid,
                          f"marker event_id={marker.get('event_id')!r}")
    prov_ticker = (marker.get("provenance") or {}).get("ticker")
    if prov_ticker is not None and prov_ticker != effective["ticker"]:
        raise JoinRefusal(J_MARKER_IDENTITY_MISMATCH, eid,
                          "marker provenance ticker differs from the registered ticker")

    block = marker.get("module_eligibility")
    if block is None:
        # build_stage_marker() sets this to None both when no pre-event record
        # exists and when the record is legacy; module_eligibility_note says
        # which. Either way there is no persisted decision to read.
        raise JoinRefusal(J_MISSING_MODULE_ELIGIBILITY, eid,
                          str(marker.get("module_eligibility_note") or "block is null"))
    if not isinstance(block, dict):
        raise JoinRefusal(J_UNREADABLE_MODULE_ELIGIBILITY, eid,
                          f"block is {type(block).__name__}, not an object")
    try:
        # completeness.read_module_eligibility is the canonical reader AND the
        # canonical fail-closed mechanism: it raises LegacyRecordError rather
        # than defaulting a pre-amendment or malformed record.
        return read_module_eligibility(block)
    except LegacyRecordError as exc:
        raise JoinRefusal(J_UNREADABLE_MODULE_ELIGIBILITY, eid, str(exc)) from exc


# ---------------------------------------------------------------------------
# Join
# ---------------------------------------------------------------------------

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


def join_event(effective: dict, marker: dict | None, gst_leg: dict | None,
               d1_leg: dict | None) -> dict:
    """Exact-key join for one event. Refuses rather than guessing.

    Identity comes from the effective registration; timing comes from the
    registered human-verified fields, not from a capture leg.
    """
    eid = effective["event_id"]
    if gst_leg is None:
        raise JoinRefusal(J_MISSING_GST_LEG, eid)
    if d1_leg is None:
        raise JoinRefusal(J_MISSING_D1_LEG, eid)

    _check_schema(gst_leg, GST_LEG_ALLOWED, eid, "gst")
    _check_schema(d1_leg, D1_LEG_ALLOWED, eid, "d1")

    # Every join key must match EXACTLY across all three sources.
    for k in JOIN_KEYS:
        vals = {str(effective.get(k)), str(gst_leg.get(k)), str(d1_leg.get(k))}
        if len(vals) != 1 or "None" in vals:
            raise JoinRefusal(J_KEY_MISMATCH, eid, f"key {k!r} differs across legs")

    # An undated capture cannot be ordered or audited. The VALUE of the
    # timestamp is never compared against anything here.
    for leg, which in ((gst_leg, "gst"), (d1_leg, "d1")):
        if not leg.get("captured_at_utc"):
            raise JoinRefusal(J_NO_CAPTURE_TIME, eid, f"{which} leg has no capture time")

    eligibility = module_eligibility_for(effective, marker)

    return {
        "event_id": eid,
        "ticker": effective["ticker"],
        "fiscal_period": effective["fiscal_period"],
        "earnings_date": effective["earnings_date"],
        # Registered human-verified timing -- the registry is authoritative.
        "release_market_session": effective["release_market_session"],
        "response_session_date": effective["expected_response_session"],
        "module_eligibility": eligibility,
        "gst": gst_leg,
        "d1": d1_leg,
        "provenance": {
            "registry_row_id": effective.get("row_id"),
            "gst_path": gst_leg.get("provenance_path"),
            "gst_sha256": gst_leg.get("provenance_sha256"),
            "d1_path": d1_leg.get("provenance_path"),
            "d1_sha256": d1_leg.get("provenance_sha256"),
        },
    }


# ---------------------------------------------------------------------------
# The ladder
# ---------------------------------------------------------------------------

def classify(effective: dict, joined: dict | None,
             refusal: JoinRefusal | None) -> tuple[bool, str | None]:
    """Apply the registered ladder to one event. Returns (eligible, reason).

    THE ORDER HERE IS THE REGISTERED ORDER AND MAY NOT BE REARRANGED.
    S-1..S-8 are fixed by GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md
    section 1 and, identically, by GST_HYP01_ANALYSIS_LOCK_v1.0.json
    /sample/inclusion_conditions[0..7].

    Reordering would leave the eligible SET unchanged, because an event must
    pass every gate. It would NOT leave the audit record unchanged: the
    disposition assigned to a multi-failure event is the code of the FIRST gate
    it fails, so the order determines the exclusion reason. Section 1 requires
    that "every disposition is recorded", so the sequence is literal.

    S-8 (rank <= 60) is a property of the ordered set and is applied by the
    driver.
    """
    # --- S-1: enrolled under cohort protocol v1.0 (human verified) ----------
    # Reads the EFFECTIVE registration -- the base REGISTRATION row with every
    # amendment folded in -- so a corrected status is honoured. This is the
    # only gate evaluable without the capture artifacts.
    if str(effective.get("verification_status", "")).lower() != "verified":
        return False, R_NOT_ENROLLED

    # --- structural availability --------------------------------------------
    # Every remaining gate reads a joined artifact, INCLUDING S-2, whose
    # evidence is the persisted pre-event marker. If any required artifact is
    # absent or unreadable, no later gate can be evaluated, so the refusal
    # surfaces here: after enrollment, before S-2. A refusal is not a
    # scientific disposition.
    if refusal is not None:
        return False, refusal.code
    assert joined is not None

    # --- S-2: hypothesis-family gate, via the locked mechanizer -------------
    # The lock names completeness.is_eligible_for_hypothesis as the mechanizer.
    # Its input is the module-eligibility decision PERSISTED on the pre-event
    # stage marker -- not any registry field, and not a reconstruction.
    if not is_eligible_for_hypothesis(HYPOTHESIS_CORE_ATTENTION_RESPONSE,
                                      joined["module_eligibility"]):
        return False, R_CLASS_INELIGIBLE

    # --- S-3: strict v0.2 core gate over the six panel fields ---------------
    # Independent of S-2. S-2 asks whether the PERSISTED decision admits this
    # hypothesis family; S-3 re-verifies the underlying six-field evidence from
    # the raw leg. A persisted decision never substitutes for the raw check.
    if not evaluate_strict_core_v0_2(joined["gst"]).passed:
        return False, R_CORE_GATE_FAILED

    # --- S-4: valid D1 decomposition ----------------------------------------
    if not is_valid_d1_decomposition(joined["d1"]):
        return False, R_D1_GATE_FAILED

    # --- S-5: gst_zscore non-null with a successful GST source status -------
    if not _present(joined["gst"], "gst_zscore"):
        return False, R_GST_PROVENANCE_FAILED
    if str(joined["gst"].get("source_status_gst", "")) not in GST_OK_STATUSES:
        return False, R_GST_PROVENANCE_FAILED
    if not provenance_ok(joined["gst"]):
        return False, R_GST_PROVENANCE_FAILED

    # --- S-6: abs_overnight_gap non-null with valid market-data provenance ---
    if not _present(joined["d1"], "abs_overnight_gap"):
        return False, R_OUTCOME_MISSING
    if joined["d1"].get("market_data_provenance_valid") is not True:
        return False, R_OUTCOME_MISSING
    if not provenance_ok(joined["d1"]):
        return False, R_OUTCOME_MISSING

    # --- S-7: registered release session in {BMO, AMC} ----------------------
    session = str(joined.get("release_market_session") or "").upper()
    if session not in VALID_SESSIONS:
        return False, R_MEASUREMENT_INCOMPATIBLE_INTRADAY

    # S-8 is applied by the driver over the ordered candidate set.
    return True, None


# The registered sequence, exposed so a test can assert the implementation
# matches the artifacts rather than trusting the comments above.
REGISTERED_GATE_ORDER = (
    ("S-1", R_NOT_ENROLLED),
    ("S-2", R_CLASS_INELIGIBLE),
    ("S-3", R_CORE_GATE_FAILED),
    ("S-4", R_D1_GATE_FAILED),
    ("S-5", R_GST_PROVENANCE_FAILED),
    ("S-6", R_OUTCOME_MISSING),
    ("S-7", R_MEASUREMENT_INCOMPATIBLE_INTRADAY),
    ("S-8", R_EXTENSION_COHORT),
)


def _sort_key(rec: dict) -> tuple:
    """Section 2: (response_session_date ASC, event_id ASC)."""
    return (str(rec.get("response_session_date") or ""), str(rec.get("event_id") or ""))


def run_driver(registry_root: Path, markers: list[dict], gst_legs: list[dict],
               d1_legs: list[dict]) -> dict:
    """Deterministic eligibility count over the canonical effective registry.

    Reads inputs and returns a status document; writes nothing. The caller
    persists it.
    """
    tally = {r: 0 for r in REASONS}
    tally.update({j: 0 for j in JOIN_REFUSALS})

    effective_rows = load_effective_registrations(Path(registry_root))

    seen: set[str] = set()
    for row in effective_rows:
        eid = row["event_id"]
        if eid in seen:
            raise JoinRefusal(J_DUPLICATE_EVENT, eid, "effective registry lists it twice")
        seen.add(eid)

    marker_ix = {k: project_marker(v)
                 for k, v in _index_unique(markers, "pre-event marker").items()}
    gst_ix = _index_unique(gst_legs, "gst")
    d1_ix = _index_unique(d1_legs, "d1")

    candidates: list[dict] = []
    for row in effective_rows:
        eid = row["event_id"]
        joined = None
        refusal = None
        try:
            joined = join_event(row, marker_ix.get(eid), gst_ix.get(eid), d1_ix.get(eid))
        except JoinRefusal as e:
            refusal = e
        ok, reason = classify(row, joined, refusal)
        if ok:
            candidates.append(joined)
        else:
            tally[reason] = tally.get(reason, 0) + 1

    # S-8 -- deterministic order, rank <= 60 eligible, the rest extension.
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
        "exclusions_by_reason": {k: v for k, v in sorted(tally.items())
                                 if v or k in REASONS},
        "effective_events_seen": len(effective_rows),
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
            "Enrollment is a human verified decision; this driver never enrolls "
            "and never amends the registry.",
            "Registry rows are REGISTRATION and AMENDMENT; amendments are folded "
            "by HumanVerifiedEventRegistry.effective_row() and are never counted "
            "as separate events.",
            "S-2 is decided by completeness.is_eligible_for_hypothesis() over the "
            "module eligibility persisted on the pre-event stage marker.",
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
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hyp01_eligibility")
    ap.add_argument("--registry-root", required=True,
                    help="directory containing the canonical registry.jsonl")
    ap.add_argument("--pre-event-markers", required=True,
                    help="JSONL of PRE_EVENT_CAPTURE stage markers")
    ap.add_argument("--gst-legs", required=True)
    ap.add_argument("--d1-legs", required=True)
    ap.add_argument("--out", help="write the status document here")
    a = ap.parse_args(argv)
    try:
        status = run_driver(Path(a.registry_root),
                            _load_jsonl(Path(a.pre_event_markers)),
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
