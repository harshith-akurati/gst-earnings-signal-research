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
    InvalidStateTransitionError, select_stage_record, validate_transition,
)
from gst_market_response.exchange_calendar import (  # noqa: E402
    compute_expected_next_full_trading_session_xnys,
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
PRE_EVENT_OK_STATES = ("PRE_EVENT_CAPTURED",)
D1_OK_STATES = ("D1_COMPLETE",)


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _parse_utc(raw, event_id: str, what: str) -> datetime:
    """Parse an ISO-8601 timestamp, failing closed.

    A NONBLANK but unparseable, naive or nonsensical timestamp refuses. Merely
    checking presence is insufficient: an unparseable capture time cannot be
    compared against the permitted window at all.
    """
    if raw is None or str(raw).strip() == "":
        raise JoinRefusal(EL.J_MALFORMED_CAPTURE_TIMESTAMP, event_id, f"{what} is blank")
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError) as exc:
        raise JoinRefusal(EL.J_MALFORMED_CAPTURE_TIMESTAMP, event_id,
                          f"{what}={raw!r} is not ISO-8601: {exc}") from exc
    if dt.tzinfo is None:
        raise JoinRefusal(EL.J_MALFORMED_CAPTURE_TIMESTAMP, event_id,
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
    pe = plan.get("event") or {}
    for field, want in (("event_id", eid),
                        ("ticker", effective["ticker"]),
                        ("earnings_date", effective["earnings_date"]),
                        ("release_market_session", effective["release_market_session"])):
        if str(pe.get(field)) != str(want):
            raise JoinRefusal(EL.J_OPERATIONS_PLAN_MISMATCH, eid,
                              f"plan {field}={pe.get(field)!r}, registration says {want!r}")

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

def load_canonical_evidence(snapshot, event_store_root: Path,
                            marker_root: Path, plan_root: Path) -> dict:
    """Assemble the evidence the eligibility driver consumes, from canonical
    roots, for ONE registry snapshot.

    S-1 PREEMPTS ALL EVIDENCE WORK. A registration that is not verified is
    skipped entirely here: its event-store log, stage markers, operations plan,
    GST evidence and D1 evidence are never opened, and it is given NO refusal.
    The driver classifies it as NOT_ENROLLED and nothing else. Inspecting a
    non-enrolled event's artifacts would both violate the gate order and give
    it a second terminal category.

    Returns {"markers": [...], "gst_legs": [...], "d1_legs": [...],
             "refusals": {event_id: JoinRefusal}, "timing": {...},
             "skipped_not_enrolled": [event_id]}.

    A per-event refusal is CARRIED, not raised, and is keyed by event_id so the
    driver can thread it into its single classification flow. It is never added
    to a tally here.
    """
    store = EventStore(Path(event_store_root))
    marker_root = Path(marker_root)
    plan_root = Path(plan_root)

    markers: list[dict] = []
    gst_legs: list[dict] = []
    d1_legs: list[dict] = []
    refusals: dict[str, JoinRefusal] = {}
    timings: dict[str, dict] = {}
    skipped: list[str] = []

    for effective in snapshot.rows:
        eid = effective["event_id"]

        # --- S-1 gate, before any artifact is touched ----------------------
        if not EL.is_enrolled(effective):
            skipped.append(eid)
            continue

        try:
            states = read_state_log(store, eid)

            pre_state = _stage_record(states, FAILURE_STAGE_PRE_EVENT, eid,
                                      PRE_EVENT_OK_STATES, EL.J_MISSING_PRE_EVENT_STATE)
            d1_state = _stage_record(states, FAILURE_STAGE_D1, eid,
                                     D1_OK_STATES, EL.J_MISSING_D1_STATE)

            pre_marker = read_marker(marker_root, eid, STAGE_PRE_EVENT, pre_state,
                                     EL.J_MISSING_PRE_EVENT_MARKER)
            d1_marker = read_marker(marker_root, eid, STAGE_D1, d1_state,
                                    EL.J_MISSING_D1_MARKER)

            plan = read_operations_plan(plan_root, eid)
            timing = validate_d1_response_window(effective, plan, d1_state)

            markers.append(pre_marker)
            gst_legs.append(_gst_leg(effective, pre_state,
                                     marker_path(marker_root, eid, STAGE_PRE_EVENT)))
            d1_legs.append(_d1_leg(effective, d1_state, d1_marker, timing,
                                   marker_path(marker_root, eid, STAGE_D1)))
            timings[eid] = timing
        except JoinRefusal as e:
            refusals[eid] = e

    return {"markers": markers, "gst_legs": gst_legs, "d1_legs": d1_legs,
            "refusals": refusals, "timing": timings,
            "skipped_not_enrolled": skipped}


def run_canonical(registry_root: Path, event_store_root: Path, marker_root: Path,
                  plan_root: Path) -> dict:
    """Canonical roots in, redacted status document out.

    ONE registry snapshot is taken here and threaded through evidence assembly,
    classification and ordering, so a single invocation can never mix two
    registry states.
    """
    snapshot = EL.load_registry_snapshot(Path(registry_root))
    evidence = load_canonical_evidence(snapshot, event_store_root, marker_root,
                                       plan_root)

    # The adapter's per-event refusals go INTO the driver's single
    # classification flow. They are deliberately NOT added to the tally
    # afterwards: doing that was the double-counting defect, because the driver
    # also saw the absent legs and recorded a second generic refusal.
    status = EL.run_driver(snapshot, evidence["markers"], evidence["gst_legs"],
                           evidence["d1_legs"], refusals=evidence["refusals"])

    status["adapter"] = {
        "source": "canonical",
        "registry_root": Path(registry_root).as_posix(),
        "event_store_root": Path(event_store_root).as_posix(),
        "marker_root": Path(marker_root).as_posix(),
        "operations_plan_root": Path(plan_root).as_posix(),
        "events_with_complete_evidence": len(evidence["d1_legs"]),
        "events_refused_structurally": len(evidence["refusals"]),
        "events_stopped_at_s1_not_enrolled": len(evidence["skipped_not_enrolled"]),
        "d1_timing_validated_event_count": len(evidence["timing"]),
    }
    status["notes"] = list(status["notes"]) + [
        "Every leg was derived from canonical artifacts by "
        "tools/hyp01_canonical_adapter.py. No hand-prepared evidence file is "
        "accepted by this command.",
        "S-1 preempts evidence assembly: a registration that is not verified has "
        "no event-store log, marker, plan or capture leg opened, and receives "
        "NOT_ENROLLED and nothing else.",
        "D1 evidence is bound to the REGISTERED response session and to the "
        "operations plan's earliest permitted provider retrieval instant.",
        "SPECIFICATION GAP: no committed artifact states a LATEST permissible D1 "
        "capture instant, so no upper bound is enforced. Inventing a tolerance "
        "was refused; closing this is a human decision.",
    ]
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
