#!/usr/bin/env python3
"""Canonical read-only adapter: project roots -> HYP-01 eligibility evidence.

This is the production input path. It derives every eligibility leg directly
from the committed canonical artifacts, so no operator ever hand-prepares an
evidence file:

    registry root      HumanVerifiedEventRegistry             registry.jsonl
    event-store root   EventStore                             {event_id}.jsonl
    marker root        stage_markers                          {event_id}_{stage}_MARKER.json
    plan root          operations_plan / operations_cli       {event_id}_OPERATIONS_PLAN.json

FIELD -> CANONICAL SOURCE

    S-1 enrollment              effective registry row, verification_status
    identity + registered
      timing                    effective registry row
    S-2 module eligibility      PRE_EVENT_CAPTURE marker, module_eligibility
                                (written by build_stage_marker from
                                 read_module_eligibility(pre_event_state.fields))
    S-3 six panel fields        canonical PRE_EVENT state record, fields
    S-4 D1 decomposition        canonical D1 state record, fields
    S-6 abs_overnight_gap       canonical D1 state record, fields
                                (emitted by pipeline.capture_d1 via
                                 response_magnitude.apply_absolute_fields)
    provenance paths/hashes     PRE_EVENT state record, stage_markers.PROVENANCE_KEYS
    GST capture timestamp       PRE_EVENT state record, written_at_utc
    D1 capture timestamp        D1 state record, written_at_utc  (set by
                                EventStore.append_state -- never caller-supplied)
    permitted D1 window (lower) operations plan, sessions.D1.
                                earliest_provider_retrieval_utc

NO HEURISTICS. Every artifact is addressed by an exact deterministic path. There
is no newest-file, nearest-date, glob-and-pick or filename-guessing fallback
anywhere in this module: if the exact artifact is absent, the event refuses.

NO MEASUREMENT IS PRINTED. The adapter necessarily READS outcome fields -- S-4
and S-6 cannot be evaluated otherwise -- but it never prints, formats, compares
or interprets one, and nothing it returns reaches the status document except
counts, identifiers, dates, reason codes and provenance hashes.

INACTIVE BY DESIGN. Never wired to Task Scheduler, and never executed against a
real prospective capture artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from gst_market_response.event_record import (  # noqa: E402
    FAILURE_STAGE_D1, FAILURE_STAGE_PRE_EVENT, EventStore,
    InvalidStateTransitionError, partial_failure_stage, select_stage_record,
    validate_transition,
)
from gst_market_response.exchange_calendar import (  # noqa: E402
    compute_expected_next_full_trading_session_xnys, previous_session,
)
from gst_market_response.completeness import (  # noqa: E402
    LegacyRecordError, read_module_eligibility,
)
from gst_market_response.operations_plan import plan_content_sha256  # noqa: E402
from gst_market_response.response_magnitude import (  # noqa: E402
    D1_ABS_FIELD_MAP, response_magnitude_block,
)
from gst_market_response.stage_markers import (  # noqa: E402
    PROVENANCE_KEYS, STAGE_D1, STAGE_PRE_EVENT, marker_path,
)

import hyp01_eligibility as EL  # noqa: E402

JoinRefusal = EL.JoinRefusal

# Deterministic operations-plan filename. operations_cli writes wherever the
# operator points --out, so no locked filename convention exists; this adapter
# fixes ONE exact name rather than searching a directory. Naming it explicitly
# is not guessing -- a plan filed under any other name simply refuses.
PLAN_FILENAME = "{event_id}_OPERATIONS_PLAN.json"

# The lifecycle states each stage's evidence may legitimately come from.
#
# A stage-specific PARTIAL IS evidence, not a missing state. The production
# writers put the stage's own fields on it, and the production readers hand it
# back deliberately:
#
#   pipeline.capture_pre_event_and_option_benchmark_v0_2() appends PARTIAL with
#       the module-eligibility block and the strict-core fields when the core
#       gate fails, tagged failure_stage="pre_event";
#   pipeline.capture_d1() appends PARTIAL with the incomplete D1 fields when the
#       decomposition gate fails, tagged failure_stage="d1";
#   event_record.select_stage_record() returns the stage's OWN PARTIAL, and
#       never one belonging to another stage;
#   stage_markers._stage_state_is_allowed() permits a marker for exactly that
#       PARTIAL.
#
# Rejecting them turned scientific first failures into structural missing-state
# refusals, which is the defect this module previously had. The stage guard is
# now enforced by partial_failure_stage(), so a PARTIAL belonging to a DIFFERENT
# stage is still refused.
PRE_EVENT_OK_STATES = ("PRE_EVENT_CAPTURED", "PARTIAL")
D1_OK_STATES = ("D1_COMPLETE", "PARTIAL")


def require_canonical_roots(registry_root: Path, event_store_root: Path,
                            marker_root: Path, plan_root: Path) -> None:
    """Fail closed on any absent canonical root, BEFORE any constructor runs.

    This must precede EventStore() and HumanVerifiedEventRegistry(): the latter
    mkdirs its root, so constructing it against a missing path both creates a
    directory during a nominally read-only invocation and converts a broken
    input set into a clean "zero eligible events" answer.

    A missing root is never an empty cohort.
    """
    for label, root, code in (
        ("registry root", registry_root, EL.J_MISSING_REGISTRY_ROOT),
        ("event-store root", event_store_root, EL.J_MISSING_EVENT_STORE_ROOT),
        ("marker root", marker_root, EL.J_MISSING_MARKER_ROOT),
        ("operations-plan root", plan_root, EL.J_MISSING_PLAN_ROOT),
    ):
        if not Path(root).is_dir():
            raise JoinRefusal(code, "<roots>", f"{label} does not exist: {root}")
    reg = Path(registry_root) / "registry.jsonl"
    if not reg.is_file():
        raise JoinRefusal(EL.J_MISSING_REGISTRY_FILE, "<roots>",
                          f"no registry.jsonl in {registry_root}")


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _parse_utc(raw, event_id: str, what: str,
               code: str = None) -> datetime:
    """Parse an ISO-8601 timestamp, failing closed.

    `code` lets the caller emit a stage-specific refusal so a bad PRE_EVENT
    snapshot instant is not reported as a D1 capture-time problem.

    A NONBLANK but unparseable, naive or nonsensical timestamp refuses. Merely
    checking presence is insufficient: an unparseable capture time cannot be
    compared against the permitted window at all.
    """
    code = code or EL.J_MALFORMED_CAPTURE_TIMESTAMP
    if raw is None or str(raw).strip() == "":
        raise JoinRefusal(code, event_id, f"{what} is blank")
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise JoinRefusal(code, event_id,
                          f"{what}={raw!r} is not ISO-8601: {exc}") from exc
    if dt.tzinfo is None:
        raise JoinRefusal(code, event_id,
                          f"{what}={raw!r} has no timezone; refusing to assume one")
    return dt


# ---------------------------------------------------------------------------
# Canonical state log
# ---------------------------------------------------------------------------

def read_state_log(store: EventStore, event_id: str) -> list[dict]:
    """Every STATE record for one event, with chronology validated.

    validate_transition() is the production rule and is replayed pairwise over
    the persisted chronology, so a log that could never have been written by
    the pipeline refuses instead of being read as evidence.
    """
    try:
        records = store.read_all(event_id)
    except json.JSONDecodeError as exc:
        raise JoinRefusal(EL.J_MALFORMED_CANONICAL_JSON, event_id,
                          f"event-store log is not valid JSONL: {exc}") from exc
    if not records:
        raise JoinRefusal(EL.J_MISSING_EVENT_STORE_LOG, event_id,
                          "no canonical event-store log")
    states = [r for r in records if r.get("record_type") == "STATE"]
    if not states:
        raise JoinRefusal(EL.J_MISSING_EVENT_STORE_LOG, event_id,
                          "log carries no STATE record")

    seqs = [r.get("seq") for r in records]
    if len(set(seqs)) != len(seqs):
        raise JoinRefusal(EL.J_DUPLICATE_STATE_RECORD, event_id,
                          "duplicate seq in the append-only log")

    previous = None
    for r in states:
        try:
            validate_transition(previous, r["state"])
        except InvalidStateTransitionError as exc:
            raise JoinRefusal(EL.J_INVALID_STATE_CHRONOLOGY, event_id, str(exc)) from exc
        previous = r["state"]
    return states


def _stage_record(states: list[dict], stage_key: str, event_id: str,
                  allowed_states: tuple[str, ...], missing_code: str) -> dict:
    """The canonical record for one stage.

    select_stage_record() is the production selector: it prefers the stage's own
    success state and accepts only a PARTIAL belonging to THIS stage. No
    heuristic ranking happens here.
    """
    record = select_stage_record(states, stage_key)
    if record is None:
        raise JoinRefusal(missing_code, event_id, f"no {stage_key} stage record")
    if record.get("state") not in allowed_states:
        raise JoinRefusal(missing_code, event_id,
                          f"{stage_key} stage is {record.get('state')!r}, "
                          f"not one of {allowed_states}")
    if record.get("state") == "PARTIAL":
        # select_stage_record() already refuses another stage's PARTIAL, but the
        # attribution is re-derived here so a wrong-stage record can never be
        # reassigned to this stage by a future caller.
        idx = states.index(record)
        owner = partial_failure_stage(states, idx)
        if owner != stage_key:
            raise JoinRefusal(missing_code, event_id,
                              f"PARTIAL belongs to stage {owner!r}, not {stage_key!r}")
    if not record.get("fields"):
        raise JoinRefusal(missing_code, event_id, f"{stage_key} record carries no fields")
    return record


# ---------------------------------------------------------------------------
# Immutable stage markers
# ---------------------------------------------------------------------------

def read_marker(marker_root: Path, event_id: str, stage: str,
                stage_record: dict, missing_code: str) -> dict:
    """Read one immutable marker and prove it ties out to its stage record.

    WHY NOT verify_marker_ties_out(). That production helper rebuilds the marker
    with build_stage_marker(), which refuses unless the event's CURRENT state
    still matches the stage -- so it cannot check a PRE_EVENT marker once the
    event has advanced to D1_COMPLETE, which is exactly the situation every
    eligible event is in. It remains the right tool at capture time; it is not
    usable for after-the-fact verification.

    So the tie-out is done directly against the PERSISTED stage record, using
    the same production functions build_stage_marker() itself used:
    read_module_eligibility() for the eligibility block, PROVENANCE_KEYS for the
    provenance echo, and response_magnitude_block() for the abs_* echo. Fields
    that are only knowable at write time (lifecycle_state, chronology) are not
    recomputed and not compared -- they are not evidence for any gate.

    A marker that disagrees fails closed. It is never regenerated, replaced, or
    preferred over the record.
    """
    path = marker_path(marker_root, event_id, stage)
    if not path.exists():
        raise JoinRefusal(missing_code, event_id, f"no {stage} marker at {path.name}")
    try:
        marker = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise JoinRefusal(EL.J_MALFORMED_CANONICAL_JSON, event_id,
                          f"{stage} marker is not valid JSON: {exc}") from exc

    diffs = []
    if marker.get("event_id") != event_id:
        diffs.append("event_id")
    if marker.get("stage") != stage:
        diffs.append("stage")

    fields = stage_record.get("fields") or {}
    if stage == STAGE_PRE_EVENT:
        try:
            expected_elig = read_module_eligibility(fields).as_dict()
        except LegacyRecordError as exc:
            raise JoinRefusal(EL.J_UNREADABLE_MODULE_ELIGIBILITY, event_id,
                              str(exc)) from exc
        if marker.get("module_eligibility") != expected_elig:
            diffs.append("module_eligibility")
        if marker.get("provenance") != {k: fields.get(k) for k in PROVENANCE_KEYS}:
            diffs.append("provenance")
    elif stage == STAGE_D1:
        expected_rm = response_magnitude_block(fields, D1_ABS_FIELD_MAP)
        on_disk = marker.get("response_magnitude") or {}
        if {k: on_disk.get(k) for k in expected_rm} != expected_rm:
            diffs.append("response_magnitude")

    if diffs:
        raise JoinRefusal(EL.J_MARKER_STATE_DISAGREEMENT, event_id,
                          f"{stage} marker disagrees with the event record on {diffs}")
    return marker


# ---------------------------------------------------------------------------
# Operations plan and D1 response-window identity
# ---------------------------------------------------------------------------

def read_operations_plan(plan_root: Path, event_id: str) -> dict:
    path = Path(plan_root) / PLAN_FILENAME.format(event_id=event_id)
    if not path.exists():
        raise JoinRefusal(EL.J_MISSING_OPERATIONS_PLAN, event_id,
                          f"no operations plan at {path.name}")
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise JoinRefusal(EL.J_MALFORMED_CANONICAL_JSON, event_id,
                          f"operations plan is not valid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise JoinRefusal(EL.J_MALFORMED_CANONICAL_JSON, event_id,
                          "operations plan is not a JSON object")
    integrity = plan.get("integrity") or {}
    stored = integrity.get("plan_content_sha256")
    if not stored:
        raise JoinRefusal(EL.J_OPERATIONS_PLAN_INTEGRITY, event_id,
                          "plan carries no integrity digest")
    # plan_content_sha256 is the production canonicalisation; recomputing with
    # it proves the plan bytes were not edited after finalize_plan().
    if plan_content_sha256(plan) != stored:
        raise JoinRefusal(EL.J_OPERATIONS_PLAN_INTEGRITY, event_id,
                          "plan does not recompute to its own stored digest")
    return plan


def _plan_describes_event(effective: dict, plan: dict) -> None:
    """The operations plan must describe THIS event. Shared by the PRE_EVENT and
    D1 validators so the two cannot drift."""
    eid = effective["event_id"]
    pe = plan.get("event") or {}
    for field, want in (("event_id", eid),
                        ("ticker", effective["ticker"]),
                        ("earnings_date", effective["earnings_date"]),
                        ("release_market_session", effective["release_market_session"])):
        if str(pe.get(field)) != str(want):
            raise JoinRefusal(EL.J_OPERATIONS_PLAN_MISMATCH, eid,
                              f"plan {field}={pe.get(field)!r}, registration says {want!r}")


def validate_pre_event_anchor(effective: dict, plan: dict, pre_state: dict) -> dict:
    """Prove the PRE_EVENT evidence belongs to the registered pre-event anchor.

    Runs BEFORE S-2 and S-3. Without it, a snapshot captured for a superseded
    anchor -- or for an unrelated session -- could satisfy the attention gates,
    because S-2 and S-3 read the persisted fields without asking which session
    produced them.

    Every comparison reuses a production function or an authoritative persisted
    field. No session arithmetic is reimplemented, and no nearest-date or
    historical fallback is accepted: every comparison is exact equality.

    SPECIFICATION GAP -- deliberately not filled. No committed artifact states an
    intra-session PRE_EVENT capture window (an earliest or latest instant within
    the anchor session). Only the anchor SESSION is derivable, so this function
    binds the snapshot to that session date and refuses to invent a
    within-session bound. Recorded for human closure alongside the D1
    upper-bound gap.
    """
    eid = effective["event_id"]
    _plan_describes_event(effective, plan)

    # -- the plan's anchor must BE the mechanically derived registered anchor --
    # previous_session() is the production calendar function; operations_plan
    # derives the anchor the same way (operations_plan.py:343-350).
    derived = previous_session(date.fromisoformat(effective["earnings_date"]))
    planned = ((plan.get("sessions") or {}).get("pre_event_anchor") or {}).get("session_date")
    if planned != derived.isoformat():
        raise JoinRefusal(
            EL.J_PRE_EVENT_ANCHOR_MISMATCH, eid,
            f"plan pre_event_anchor.session_date={planned!r} but the calendar derives "
            f"{derived.isoformat()} from the effective earnings date; evidence prepared "
            f"for a superseded anchor is not evidence for the current one")

    f = pre_state.get("fields") or {}

    # -- the snapshot instant must be parseable and timezone-aware ------------
    asof = _parse_utc(f.get("pre_event_snapshot_asof_utc"), eid,
                      "pre_event_snapshot_asof_utc",
                      EL.J_MALFORMED_SNAPSHOT_TIMESTAMP)

    # -- the panel/snapshot date must BE the anchor session -------------------
    # run_date is the Phase 2 panel's own session date, persisted in
    # stage_markers.PROVENANCE_KEYS. Exact equality only.
    for field in ("run_date", "price_asof_date"):
        got = f.get(field)
        if got is None:
            continue          # absent provenance is judged by S-5, not here
        if str(got)[:10] != derived.isoformat():
            raise JoinRefusal(
                EL.J_PRE_EVENT_PANEL_DATE_MISMATCH, eid,
                f"{field}={got!r} is not the derived pre-event anchor "
                f"{derived.isoformat()}")

    if asof.date().isoformat() != derived.isoformat():
        raise JoinRefusal(
            EL.J_PRE_EVENT_PANEL_DATE_MISMATCH, eid,
            f"pre_event_snapshot_asof_utc falls on {asof.date().isoformat()}, "
            f"not the derived anchor session {derived.isoformat()}")

    return {"pre_event_anchor": derived.isoformat(),
            "snapshot_asof_utc": asof.isoformat(),
            "intra_session_window_enforced": False,
            "intra_session_window_note":
                "No committed artifact states an intra-session PRE_EVENT capture "
                "window; none was invented. Specification gap recorded."}


def validate_d1_response_window(effective: dict, plan: dict, d1_state: dict) -> dict:
    """Prove the D1 evidence belongs to the REGISTERED response window.

    Every comparison reuses a production function or an authoritative persisted
    field; no session arithmetic is reimplemented here.

    SPECIFICATION GAP -- deliberately not filled. The locked artifacts specify
    only a LOWER bound on when a D1 capture may occur:
    operations_plan.SessionPlan.earliest_provider_retrieval_utc, which is the
    D1 session's final expected bar start plus ALPACA_MIN_END_AGE_MINUTES. No
    committed artifact states a LATEST permissible capture instant -- there is
    no staleness limit, deadline or recency tolerance for D1 anywhere in the
    SPECs, the analysis lock, the eligibility rules or the code. An upper bound
    is therefore NOT enforced, because enforcing one would mean inventing a
    tolerance. This is reported as a specification gap for a human to close.
    """
    eid = effective["event_id"]

    # -- the registry's own derived timing must still be self-consistent -----
    # compute_expected_next_full_trading_session_xnys is the production rule.
    # After an amendment, amend_event() recomputes expected_response_session
    # from the corrected values; a row where it no longer recomputes is stale.
    expected = compute_expected_next_full_trading_session_xnys(
        date.fromisoformat(effective["earnings_date"]),
        effective["release_market_session"])
    registered = effective["expected_response_session"]
    if registered != expected.isoformat():
        raise JoinRefusal(
            EL.J_REGISTRY_TIMING_STALE, eid,
            f"registered expected_response_session={registered} but the calendar "
            f"derives {expected.isoformat()} from the effective earnings date and session")

    # -- the plan must describe THIS event ----------------------------------
    _plan_describes_event(effective, plan)

    # -- the plan's D1 session must BE the registered response session -------
    # This is what invalidates a capture prepared under superseded timing: an
    # amendment moves expected_response_session, and a plan built for the old
    # date no longer matches. No locked rule exempts such a capture, so it
    # refuses rather than being reused.
    d1_session = ((plan.get("sessions") or {}).get("D1") or {})
    planned_date = d1_session.get("session_date")
    if planned_date != registered:
        raise JoinRefusal(
            EL.J_D1_SESSION_MISMATCH, eid,
            f"operations plan D1 session_date={planned_date!r} but the registered "
            f"response session is {registered!r}; a capture prepared for superseded "
            f"timing is not evidence for the current one")

    # -- the capture must fall inside the permitted locked window -----------
    captured = _parse_utc(d1_state.get("written_at_utc"), eid, "D1 written_at_utc")
    earliest = _parse_utc(d1_session.get("earliest_provider_retrieval_utc"), eid,
                          "plan earliest_provider_retrieval_utc")
    if captured < earliest:
        raise JoinRefusal(
            EL.J_CAPTURE_BEFORE_PERMITTED_WINDOW, eid,
            "D1 capture precedes the plan's earliest permitted provider retrieval "
            "for the registered response session")

    return {
        "response_session_date": registered,
        "captured_at_utc": captured.isoformat(),
        "earliest_permitted_utc": earliest.isoformat(),
        "plan_content_sha256": plan["integrity"]["plan_content_sha256"],
    }


# ---------------------------------------------------------------------------
# Leg construction
# ---------------------------------------------------------------------------

def _gst_leg(effective: dict, pre_state: dict, marker_file: Path) -> dict:
    f = pre_state["fields"]
    leg = {
        "event_id": effective["event_id"],
        "ticker": effective["ticker"],
        "earnings_date": effective["earnings_date"],
        "captured_at_utc": pre_state.get("written_at_utc"),
        "provenance_path": f.get("source_csv_path"),
        "provenance_sha256": f.get("source_csv_sha256"),
    }
    # The six strict-core fields and their five per-leg statuses, copied
    # verbatim from the canonical record. Never recomputed, never defaulted.
    for k in EL.STRICT_CORE_SIX_FIELDS:
        if k in f:
            leg[k] = f[k]
    for k in set(EL.STRICT_CORE_STATUS_KEY.values()):
        if k in f:
            leg[k] = f[k]
    for k in EL.STRICT_CORE_REQUIRED_PROVENANCE:
        if k in f:
            leg[k] = f[k]
    return leg


def _d1_leg(effective: dict, d1_state: dict, d1_marker: dict, timing: dict,
            marker_file: Path) -> dict:
    f = d1_state["fields"]
    leg = {
        "event_id": effective["event_id"],
        "ticker": effective["ticker"],
        "earnings_date": effective["earnings_date"],
        "captured_at_utc": timing["captured_at_utc"],
        "provenance_path": marker_file.as_posix(),
        "provenance_sha256": _sha256_file(marker_file),
    }
    # A stage-specific D1 PARTIAL carries whichever interval fields the capture
    # did produce. They are copied verbatim; S-4 then decides. Absent fields
    # stay absent -- nothing is defaulted to make the gate pass.
    for k in EL.D1_REQUIRED_FIELDS:
        if k in f:
            leg[k] = f[k]
    if "abs_overnight_gap" in f:
        leg["abs_overnight_gap"] = f["abs_overnight_gap"]

    # S-6's "valid market-data provenance", derived from committed behaviour
    # rather than asserted: the D1 stage reached D1_COMPLETE, its immutable
    # marker ties out to the record (already proven by read_marker), and the
    # marker's response_magnitude block -- which stage_markers reads back from
    # the STORED record rather than recomputing -- carries the same primary
    # outcome the state record does.
    echoed = (d1_marker.get("response_magnitude") or {}).get("abs_overnight_gap")
    leg["market_data_provenance_valid"] = (
        d1_state.get("state") == "D1_COMPLETE"
        and "abs_overnight_gap" in f
        and echoed is not None
        and echoed == f["abs_overnight_gap"]
    )
    return leg


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_event(effective: dict, store: EventStore, marker_root: Path,
                   plan_root: Path) -> tuple:
    """Walk ONE event down the registered ladder, opening evidence only as far
    as the ladder actually reaches.

    Returns (eligible, reason_or_None, sort_record_or_None) -- exactly one
    terminal outcome.

    The ladder is progressive on purpose. Requiring every downstream artifact
    before classifying meant an event that fails S-2 or S-3 was reported as a
    structural missing-D1 refusal, and a stage-specific PARTIAL -- which the
    production writers create precisely to preserve the failing stage's fields
    -- was reported as a missing state. Both hid the earlier, registered
    scientific disposition behind a later structural one.

    Short-circuiting is therefore a correctness property, not an optimisation:
    once a gate fails, no later artifact is opened, so no later artifact's
    absence can overwrite the answer.
    """
    eid = effective["event_id"]

    # ---- S-1 -------------------------------------------------------------
    # Preempts everything. No capture artifact is opened for a non-enrolled
    # registration, and it never receives a structural refusal.
    if not EL.is_enrolled(effective):
        return (False, EL.R_NOT_ENROLLED, None)

    # ---- PRE_EVENT evidence, for S-2 and S-3 -----------------------------
    try:
        states = read_state_log(store, eid)
        pre_state = _stage_record(states, FAILURE_STAGE_PRE_EVENT, eid,
                                  PRE_EVENT_OK_STATES, EL.J_MISSING_PRE_EVENT_STATE)
        pre_marker = read_marker(marker_root, eid, STAGE_PRE_EVENT, pre_state,
                                 EL.J_MISSING_PRE_EVENT_MARKER)
        # The operations plan is opened here -- earlier than the D1 stage -- so
        # the PRE_EVENT evidence can be bound to the registered anchor BEFORE
        # S-2 and S-3 read it.
        plan = read_operations_plan(plan_root, eid)
        pre_timing = validate_pre_event_anchor(effective, plan, pre_state)
        eligibility = EL.module_eligibility_for(effective, EL.project_marker(pre_marker))
    except JoinRefusal as e:
        return (False, e.code, None)

    gst_leg = _gst_leg(effective, pre_state,
                       marker_path(marker_root, eid, STAGE_PRE_EVENT))

    # ---- S-2, then S-3 ---------------------------------------------------
    if not EL.gate_s2(eligibility):
        return (False, EL.R_CLASS_INELIGIBLE, None)
    if not EL.gate_s3(gst_leg):
        return (False, EL.R_CORE_GATE_FAILED, None)

    # ---- D1 evidence, only now -------------------------------------------
    try:
        d1_state = _stage_record(states, FAILURE_STAGE_D1, eid,
                                 D1_OK_STATES, EL.J_MISSING_D1_STATE)
        d1_marker = read_marker(marker_root, eid, STAGE_D1, d1_state,
                                EL.J_MISSING_D1_MARKER)
        timing = validate_d1_response_window(effective, plan, d1_state)
    except JoinRefusal as e:
        return (False, e.code, None)

    d1_leg = _d1_leg(effective, d1_state, d1_marker, timing,
                     marker_path(marker_root, eid, STAGE_D1))

    # ---- S-4 .. S-7 ------------------------------------------------------
    if not EL.gate_s4(d1_leg):
        return (False, EL.R_D1_GATE_FAILED, None)
    if not EL.gate_s5(gst_leg):
        return (False, EL.R_GST_PROVENANCE_FAILED, None)
    if not EL.gate_s6(d1_leg):
        return (False, EL.R_OUTCOME_MISSING, None)
    if not EL.gate_s7(effective.get("release_market_session")):
        return (False, EL.R_MEASUREMENT_INCOMPATIBLE_INTRADAY, None)

    # S-8 is applied by tally_outcomes() over the ordered candidate set.
    return (True, None, {"event_id": eid,
                         "response_session_date": timing["response_session_date"]})


def load_canonical_evidence(snapshot, event_store_root: Path,
                            marker_root: Path, plan_root: Path) -> dict:
    """Walk every event in ONE registry snapshot down the progressive ladder.

    Returns {"outcomes": {event_id: (eligible, reason, sort_record)},
             "eligible": [event_id], "scientific": {event_id: code},
             "structural": {event_id: code},
             "skipped_not_enrolled": [event_id]}.

    Exactly one terminal outcome per event; nothing is tallied here.
    """
    store = EventStore(Path(event_store_root))
    marker_root = Path(marker_root)
    plan_root = Path(plan_root)

    outcomes: dict[str, tuple] = {}
    eligible: list[str] = []
    scientific: dict[str, str] = {}
    structural: dict[str, str] = {}
    skipped: list[str] = []

    for effective in snapshot.rows:
        eid = effective["event_id"]
        outcome = evaluate_event(effective, store, marker_root, plan_root)
        outcomes[eid] = outcome
        ok, reason, _rec = outcome
        if ok:
            eligible.append(eid)
        elif reason == EL.R_NOT_ENROLLED:
            skipped.append(eid)
        elif reason in EL.REASONS:
            scientific[eid] = reason
        else:
            structural[eid] = reason

    return {"outcomes": outcomes, "eligible": eligible, "scientific": scientific,
            "structural": structural, "skipped_not_enrolled": skipped}


def run_canonical(registry_root: Path, event_store_root: Path, marker_root: Path,
                  plan_root: Path) -> dict:
    """Canonical roots in, redacted status document out.

    ONE registry snapshot is taken here and threaded through the progressive
    ladder and the tally, so a single invocation can never mix two registry
    states.
    """
    require_canonical_roots(Path(registry_root), Path(event_store_root),
                            Path(marker_root), Path(plan_root))
    snapshot = EL.load_registry_snapshot(Path(registry_root))
    ev = load_canonical_evidence(snapshot, event_store_root, marker_root, plan_root)

    status = EL.tally_outcomes(snapshot, ev["outcomes"], extra_notes=(
        "Every leg was derived from canonical artifacts by "
        "tools/hyp01_canonical_adapter.py. No hand-prepared evidence file is "
        "accepted by this command.",
        "The ladder is walked progressively: evidence is opened only as far as "
        "the ladder reaches, so a later missing artifact can never replace an "
        "earlier scientific disposition.",
        "A stage-specific PARTIAL record is scientific evidence, not a missing "
        "state; a PARTIAL belonging to another stage is still refused.",
        "S-1 preempts evidence assembly: a registration that is not verified has "
        "no event-store log, marker, plan or capture leg opened, and receives "
        "NOT_ENROLLED and nothing else.",
        "D1 evidence is bound to the REGISTERED response session and to the "
        "operations plan's earliest permitted provider retrieval instant.",
        "SPECIFICATION GAP: no committed artifact states a LATEST permissible D1 "
        "capture instant, so no upper bound is enforced. Inventing a tolerance "
        "was refused; closing this is a human decision.",
    ))

    status["adapter"] = {
        "source": "canonical",
        "registry_root": Path(registry_root).as_posix(),
        "event_store_root": Path(event_store_root).as_posix(),
        "marker_root": Path(marker_root).as_posix(),
        "operations_plan_root": Path(plan_root).as_posix(),
        "events_eligible": len(ev["eligible"]),
        "events_excluded_scientifically": len(ev["scientific"]),
        "events_refused_structurally": len(ev["structural"]),
        "events_stopped_at_s1_not_enrolled": len(ev["skipped_not_enrolled"]),
    }
    return status


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="hyp01_canonical_adapter",
        description="Canonical HYP-01 eligibility status from project roots.")
    ap.add_argument("--registry-root", required=True,
                    help="directory containing the canonical registry.jsonl")
    ap.add_argument("--event-store-root", required=True,
                    help="directory containing the canonical {event_id}.jsonl logs")
    ap.add_argument("--marker-root", required=True,
                    help="directory containing the immutable stage markers")
    ap.add_argument("--operations-plan-root", required=True,
                    help="directory containing {event_id}_OPERATIONS_PLAN.json")
    ap.add_argument("--out", help="write the redacted status document here")
    a = ap.parse_args(argv)
    try:
        status = run_canonical(Path(a.registry_root), Path(a.event_store_root),
                               Path(a.marker_root), Path(a.operations_plan_root))
    except JoinRefusal as e:
        print(f"REFUSED {e.code}: {e.event_id} {e.detail}".rstrip())
        return 2
    except EL.ReconciliationError as e:
        # A status document that does not account for every event exactly once
        # would misrepresent the cohort. Nothing is written.
        print(f"RECONCILIATION FAILED: {e}", file=sys.stderr)
        return 3
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
