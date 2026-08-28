#!/usr/bin/env python3
"""Offline synthetic end-to-end tests for the HYP-01 join and counting driver.

Every fixture is synthetic: registries are written into a temporary directory,
legs and markers are built in memory. No project data file is read, no real
prospective record is opened, and a socket guard fails the run on any
connection attempt.

Properties asserted:

  A. JOIN INTEGRITY      exact registered keys only; duplicates, missing legs,
                         key mismatches, unknown columns and undated captures
                         all REFUSE.
  B. LADDER CORRECTNESS  each registered step produces its own disposition.
  C. GATE ARITHMETIC     the 59 -> 60 transition flips freeze_required exactly
                         once; counting REFUSES beyond 60.
  D. NON-DISCLOSURE      no measurement value reaches the status document.
  E. PRECEDENCE          first-failure attribution follows the registered
                         S-1..S-8 order.
  F. PROVENANCE          a provenance failure can never reach the cohort.
  G. CANONICAL REGISTRY  REGISTRATION/AMENDMENT handling and effective rows.
  H. S-2 MECHANIZATION   the locked mechanizer decides S-2, from the persisted
                         pre-event marker, and stays distinct from S-3.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path


class _Blocked(socket.socket):
    def connect(self, *a, **k):
        raise AssertionError("network access attempted; this suite is offline")

    def connect_ex(self, *a, **k):
        raise AssertionError("network access attempted; this suite is offline")


socket.socket = _Blocked
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
    AssertionError("network access attempted; this suite is offline"))

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "hyp01_eligibility", _HERE / "tools" / "hyp01_eligibility.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

FAILURES: list[str] = []
CHECKS = 0
TMP = Path(tempfile.mkdtemp(prefix="hyp01_elig_"))
_counter = itertools.count()


def check(label, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}  {detail}")
        FAILURES.append(label)


class _Drop:
    """Sentinel meaning 'omit this key entirely', so a fixture can express an
    ABSENT field as distinct from a null one."""


_DROP = _Drop()

# Sentinel measurements. If any value or field name appears in a status
# document, non-disclosure has failed.
SENTINELS = {
    "gst_zscore": 7.7777771,
    "wiki_zscore": -8.8888882,
    "panel_implied_volatility": 0.55555555,
    "realized_volatility": 0.44444446,
    "previous_close": 9999.99993,
    "volume": 123456784,
    "overnight_gap": -5.55555558,
    "open_to_30m": 1.11111112,
    "thirty_min_to_close": 2.22222220,
    "open_to_close": 3.33333339,
    "abs_overnight_gap": 6.66666667,
}
HASH_A = "a" * 64
HASH_B = "b" * 64


def _drop_absent(d):
    return {k: v for k, v in d.items() if not isinstance(v, _Drop)}


def _eid(i):
    return f"EVT-TK{i:03d}-FY27Q2-ERN"


def _edate(i):
    return f"2026-09-{(i % 28) + 1:02d}"


def _rdate(i):
    return f"2026-09-{(i % 28) + 2:02d}"


# --- canonical registry fixtures -------------------------------------------

def reg_row(i, *, status="verified", session="AMC", **over):
    """A canonical REGISTRATION row. row_type is REGISTRATION -- never 'event'."""
    r = {
        "row_id": f"{_eid(i)}-REG-001",
        "row_type": "REGISTRATION",
        "event_id": _eid(i),
        "ticker": f"TK{i:03d}",
        "fiscal_period": "FY27Q2",
        "earnings_date": _edate(i),
        "earnings_datetime_utc": None,
        "release_market_session": session,
        "source_url": "https://synthetic.invalid/ir",
        "source_title": "synthetic",
        "source_type": "company_ir_press_release",
        "source_retrieved_at_utc": "2026-08-01T00:00:00+00:00",
        "verified_at_utc": "2026-08-01T00:00:00+00:00",
        "verified_by": "synthetic-operator",
        "verification_status": status,
        "expected_response_session": _rdate(i),
        "exchange_calendar": "XNYS",
        "registry_version": "0.1",
        "notes": "",
        "amends_row_id": None,
        "written_at_utc": "2026-08-01T00:00:00+00:00",
    }
    r.update(over)
    return _drop_absent(r)


def amend_row(i, *, amends=None, seq=1, **corrected):
    """A canonical AMENDMENT row correcting the base registration."""
    base = reg_row(i)
    base.update({
        "row_id": f"{_eid(i)}-AMD-{seq:03d}",
        "row_type": "AMENDMENT",
        "amends_row_id": amends if amends is not None else f"{_eid(i)}-REG-001",
    })
    base.update(corrected)
    return _drop_absent(base)


def build_registry(rows) -> Path:
    root = TMP / f"registry_{next(_counter):04d}"
    root.mkdir(parents=True, exist_ok=True)
    (root / "registry.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return root


# --- pre-event stage marker (the S-2 evidence) ------------------------------

def elig_block(*, core=True, option=False, joint=False,
               tier="core_only_no_option_benchmark",
               status="UNAVAILABLE_NO_VERIFIED_SOURCE", reason="synthetic",
               protocol="0.2"):
    """The module_eligibility dict exactly as ModuleEligibility.as_dict() emits."""
    return {
        "core_pre_event_eligible": core,
        "option_benchmark_eligible": option,
        "joint_full_eligible": joint,
        "pre_event_completeness_tier": tier,
        "option_benchmark_status": status,
        "option_benchmark_unavailable_reason": reason,
        "protocol_version": protocol,
    }


def marker(i, *, block="default", **over):
    """A PRE_EVENT_CAPTURE stage marker, shaped like build_stage_marker()'s
    payload -- including a response_magnitude block full of sentinel outcome
    values, so the projection can be proven to drop it."""
    m = {
        "event_id": _eid(i),
        "stage": "PRE_EVENT_CAPTURE",
        "protocol_version": "0.2",
        "lifecycle_state": "PRE_EVENT_CAPTURED",
        "state_transition_count": 2,
        "state_chronology": ["REGISTERED", "PRE_EVENT_CAPTURED"],
        "written_at_utc": "2026-09-01T13:05:00+00:00",
        "response_magnitude": {"abs_overnight_gap": SENTINELS["abs_overnight_gap"]},
        "module_eligibility": elig_block() if block == "default" else block,
        "is_full_data_complete": False,
        "provenance": {
            "ticker": f"TK{i:03d}",
            "source_csv_sha256": HASH_A,
            "source_marker_sha256": HASH_B,
            "pre_event_snapshot_asof_utc": "2026-09-01T13:00:00Z",
            "methodology_version": "market_response_v0.2",
            "panel_row_count": 24,
        },
    }
    m.update(over)
    return _drop_absent(m)


# --- capture legs -----------------------------------------------------------

def gst(i, **over):
    leg = {"event_id": _eid(i), "ticker": f"TK{i:03d}", "earnings_date": _edate(i),
           "gst_zscore": SENTINELS["gst_zscore"],
           "wiki_zscore": SENTINELS["wiki_zscore"],
           "panel_implied_volatility": SENTINELS["panel_implied_volatility"],
           "realized_volatility": SENTINELS["realized_volatility"],
           "previous_close": SENTINELS["previous_close"],
           "volume": SENTINELS["volume"],
           "source_status_gst": "ok", "source_status_wiki": "ok",
           "source_status_iv": "ok", "source_status_realized_vol": "ok",
           "source_status_price": "ok",
           "pre_event_snapshot_asof_utc": "2026-09-01T13:00:00Z",
           "provenance_path": "synthetic/gst.jsonl", "provenance_sha256": HASH_A,
           "captured_at_utc": "2026-09-01T13:00:00Z"}
    leg.update(over)
    return _drop_absent(leg)


def d1(i, **over):
    leg = {"event_id": _eid(i), "ticker": f"TK{i:03d}", "earnings_date": _edate(i),
           "overnight_gap": SENTINELS["overnight_gap"],
           "open_to_30m": SENTINELS["open_to_30m"],
           "thirty_min_to_close": SENTINELS["thirty_min_to_close"],
           "open_to_close": SENTINELS["open_to_close"],
           "abs_overnight_gap": SENTINELS["abs_overnight_gap"],
           "market_data_provenance_valid": True,
           "provenance_path": "synthetic/d1.jsonl", "provenance_sha256": HASH_B,
           "captured_at_utc": "2026-09-02T21:00:00Z"}
    leg.update(over)
    return _drop_absent(leg)


# --- drivers ----------------------------------------------------------------

def run(rows, markers, gsts, d1s):
    return E.run_driver(build_registry(rows), markers, gsts, d1s)


def one(row, mk, gst_leg, d1_leg):
    """Single-event cohort."""
    return run([row],
               [mk] if mk else [],
               [gst_leg] if gst_leg else [],
               [d1_leg] if d1_leg else [])


def sole_reason(status):
    hits = [k for k, v in status["exclusions_by_reason"].items() if v]
    return hits[0] if len(hits) == 1 else f"<{len(hits)} reasons: {hits}>"


def cohort(n):
    return ([reg_row(i) for i in range(n)], [marker(i) for i in range(n)],
            [gst(i) for i in range(n)], [d1(i) for i in range(n)])


def main() -> int:
    print("=== G. canonical registry handling ===")

    s = one(reg_row(1), marker(1), gst(1), d1(1))
    check("G1. a verified REGISTRATION passes S-1 and counts once",
          s["eligible_event_count"] == 1 and s["eligible_event_ids"] == [_eid(1)],
          json.dumps({k: v for k, v in s["exclusions_by_reason"].items() if v}))

    for st in ("pending", "rejected"):
        s = one(reg_row(1, status=st), marker(1), gst(1), d1(1))
        check(f"G2. verification_status={st!r} does not pass S-1",
              s["eligible_event_count"] == 0 and sole_reason(s) == E.R_NOT_ENROLLED,
              sole_reason(s))

    # A valid amendment corrects the status; it must fold into ONE event.
    s = run([reg_row(1, status="pending"),
             amend_row(1, verification_status="verified")],
            [marker(1)], [gst(1)], [d1(1)])
    check("G3. a valid amendment folds into one effective event and is honoured",
          s["effective_events_seen"] == 1 and s["eligible_event_count"] == 1,
          f"seen={s['effective_events_seen']} eligible={s['eligible_event_count']}")

    check("G4. an amendment is not counted as a second event",
          s["effective_events_seen"] == 1
          and sum(s["exclusions_by_reason"].values()) + s["eligible_event_count"] == 1)

    # An amendment may correct registered timing; the fold must be used.
    s = run([reg_row(1, session="INTRADAY"),
             amend_row(1, release_market_session="AMC")],
            [marker(1)], [gst(1)], [d1(1)])
    check("G5. an amendment correcting registered timing changes the S-7 outcome",
          s["eligible_event_count"] == 1, sole_reason(s))

    try:
        run([amend_row(1, amends="NO-SUCH-ROW")], [marker(1)], [gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_ORPHAN_AMENDMENT
    check("G6. an orphan amendment refuses", ok)

    try:
        run([reg_row(1), reg_row(1, row_id=f"{_eid(1)}-REG-002")],
            [marker(1)], [gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_BASE_REGISTRATION
    check("G7. two base REGISTRATION rows for one event refuse", ok)

    for field, bad in (("ticker", "XXXX"), ("fiscal_period", "FY99Q9")):
        try:
            run([reg_row(1), amend_row(1, **{field: bad})],
                [marker(1)], [gst(1)], [d1(1)])
            ok = False
        except E.JoinRefusal as e:
            ok = e.code == E.J_ILLEGAL_IDENTITY_CHANGE
        check(f"G8. an amendment changing {field} refuses as an identity change", ok)

    try:
        run([reg_row(1, row_type="event")], [marker(1)], [gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_UNKNOWN_ROW_TYPE
    check("G9. the invented row type 'event' is refused, not accepted", ok)

    check("G10. only canonical row types are recognised",
          E.CANONICAL_ROW_TYPES == ("REGISTRATION", "AMENDMENT"))

    src = (_HERE / "tools" / "hyp01_eligibility.py").read_text(encoding="utf-8")
    check("G11. no hypothesis_class read survives in production code",
          "hypothesis_class" not in src)
    check("G12. no row_type == 'event' assumption survives in production code",
          '"event"' not in src and "'event'" not in src)

    try:
        run([reg_row(1, expected_response_session=_DROP)], [marker(1)], [gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_MISSING_REGISTRY_FIELD
    check("G13. a missing registry field refuses rather than defaulting", ok)

    s = run([reg_row(1), amend_row(1, seq=1),
             amend_row(1, seq=2, verification_status="rejected")],
            [marker(1)], [gst(1)], [d1(1)])
    check("G14. multiple amendments fold in order; the last correction wins",
          s["effective_events_seen"] == 1 and sole_reason(s) == E.R_NOT_ENROLLED,
          sole_reason(s))

    print("\n=== H. S-2 mechanization and the S-2/S-3 distinction ===")

    s = one(reg_row(1), marker(1, block=elig_block(core=False)), gst(1), d1(1))
    check("H1. persisted core_pre_event_eligible=False -> CLASS_INELIGIBLE",
          sole_reason(s) == E.R_CLASS_INELIGIBLE, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1, wiki_zscore=_DROP), d1(1))
    check("H2. persisted eligibility true + raw strict-core failure -> CORE_GATE_FAILED",
          sole_reason(s) == E.R_CORE_GATE_FAILED, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1), d1(1))
    check("H3. persisted eligibility true + raw strict-core pass -> continues",
          s["eligible_event_count"] == 1, sole_reason(s))

    s = one(reg_row(1), None, gst(1), d1(1))
    check("H4. a missing pre-event marker refuses structurally",
          sole_reason(s) == E.J_MISSING_PRE_EVENT_MARKER, sole_reason(s))

    s = one(reg_row(1), marker(1, block=None,
                               module_eligibility_note="legacy pre-amendment record"),
            gst(1), d1(1))
    check("H5. a null module-eligibility block refuses structurally",
          sole_reason(s) == E.J_MISSING_MODULE_ELIGIBILITY, sole_reason(s))

    legacy = {"core_pre_event_eligible": True}   # pre-amendment shape
    s = one(reg_row(1), marker(1, block=legacy), gst(1), d1(1))
    check("H6. a legacy module-eligibility block refuses via LegacyRecordError",
          sole_reason(s) == E.J_UNREADABLE_MODULE_ELIGIBILITY, sole_reason(s))

    bad_tier = elig_block()
    bad_tier["pre_event_completeness_tier"] = "not_a_real_tier"
    s = one(reg_row(1), marker(1, block=bad_tier), gst(1), d1(1))
    check("H7. a malformed completeness tier refuses structurally",
          sole_reason(s) == E.J_UNREADABLE_MODULE_ELIGIBILITY, sole_reason(s))

    s = one(reg_row(1), marker(1, block="not-a-dict"), gst(1), d1(1))
    check("H8. a non-object eligibility block refuses structurally",
          sole_reason(s) == E.J_UNREADABLE_MODULE_ELIGIBILITY, sole_reason(s))

    # Markers are indexed by their OWN event_id, so a marker belonging to a
    # different event is simply absent for this one -- which is the accurate
    # answer, not an identity mismatch.
    s = one(reg_row(1), marker(1, event_id=_eid(2)), gst(1), d1(1))
    check("H9a. a marker belonging to another event leaves this one with none",
          sole_reason(s) == E.J_MISSING_PRE_EVENT_MARKER, sole_reason(s))

    # A marker filed under the right key whose internal identity disagrees is a
    # genuine mismatch; reachable through the join, which is where it is caught.
    try:
        E.module_eligibility_for(reg_row(1), marker(1, event_id=_eid(2)))
        ok, code = False, "no refusal"
    except E.JoinRefusal as e:
        ok, code = e.code == E.J_MARKER_IDENTITY_MISMATCH, e.code
    check("H9b. a marker whose internal event_id disagrees refuses on identity",
          ok, code)

    m = marker(1)
    m["provenance"] = {**m["provenance"], "ticker": "WRONG"}
    s = one(reg_row(1), m, gst(1), d1(1))
    check("H10. a marker whose provenance ticker differs refuses",
          sole_reason(s) == E.J_MARKER_IDENTITY_MISMATCH, sole_reason(s))

    s = one(reg_row(1), marker(1, stage="D1_CAPTURE"), gst(1), d1(1))
    check("H11. a marker for the wrong stage refuses",
          sole_reason(s) == E.J_MARKER_IDENTITY_MISMATCH, sole_reason(s))

    s = one(reg_row(1), None, gst(1), d1(1))
    check("H12. a perfectly complete GST leg cannot bypass missing S-2 evidence",
          s["eligible_event_count"] == 0
          and sole_reason(s) not in (E.R_CLASS_INELIGIBLE, E.R_CORE_GATE_FAILED),
          sole_reason(s))

    # S-2 must genuinely call the locked mechanizer, not merely name it.
    calls = []
    real = E.is_eligible_for_hypothesis

    def spy(hypothesis, eligibility):
        calls.append((hypothesis, eligibility.core_pre_event_eligible))
        return real(hypothesis, eligibility)

    E.is_eligible_for_hypothesis = spy
    try:
        one(reg_row(1), marker(1), gst(1), d1(1))
    finally:
        E.is_eligible_for_hypothesis = real
    check("H13. S-2 behaviourally calls is_eligible_for_hypothesis with the "
          "core hypothesis family and the persisted decision",
          calls == [(E.HYPOTHESIS_CORE_ATTENTION_RESPONSE, True)], str(calls))

    check("H14. CLASS_INELIGIBLE and CORE_GATE_FAILED are both reachable",
          sole_reason(one(reg_row(1), marker(1, block=elig_block(core=False)),
                          gst(1), d1(1))) == E.R_CLASS_INELIGIBLE
          and sole_reason(one(reg_row(1), marker(1),
                              gst(1, volume=_DROP), d1(1))) == E.R_CORE_GATE_FAILED)

    print("\n=== A. join integrity ===")

    s = one(reg_row(1), marker(1), None, d1(1))
    check("A1. a missing GST leg refuses, and counts nothing",
          s["eligible_event_count"] == 0 and sole_reason(s) == E.J_MISSING_GST_LEG,
          sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1), None)
    check("A2. a missing D1 leg refuses, and counts nothing",
          sole_reason(s) == E.J_MISSING_D1_LEG, sole_reason(s))

    try:
        run([reg_row(1)], [marker(1)], [gst(1), gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_LEG
    check("A3. two GST legs for one event raise, never pick one", ok)

    s = one(reg_row(1), marker(1), gst(1, ticker="WRONG"), d1(1))
    check("A4. a ticker that differs across legs refuses; no fuzzy match",
          sole_reason(s) == E.J_KEY_MISMATCH, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1, earnings_date="2026-09-09"), d1(1))
    check("A5. a near-miss earnings date refuses; no nearest-date match",
          sole_reason(s) == E.J_KEY_MISMATCH, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1, surprise_column=1), d1(1))
    check("A6. an unknown GST column refuses rather than being ignored",
          sole_reason(s) == E.J_UNEXPECTED_FIELD, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1), d1(1, sneaky_alpha=1))
    check("A7. an unknown D1 column refuses rather than being ignored",
          sole_reason(s) == E.J_UNEXPECTED_FIELD, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1, captured_at_utc=_DROP), d1(1))
    check("A8. an undated capture refuses",
          sole_reason(s) == E.J_NO_CAPTURE_TIME, sole_reason(s))

    print("\n=== B. ladder correctness ===")

    cases = [
        ("B1. S-1 unverified", reg_row(1, status="pending"), marker(1), gst(1), d1(1),
         E.R_NOT_ENROLLED),
        ("B2. S-2 persisted core ineligible", reg_row(1),
         marker(1, block=elig_block(core=False)), gst(1), d1(1), E.R_CLASS_INELIGIBLE),
        ("B3. S-3 missing sixth panel field", reg_row(1), marker(1),
         gst(1, wiki_zscore=_DROP), d1(1), E.R_CORE_GATE_FAILED),
        ("B4. S-3 failed IV leg is not inherited from price", reg_row(1), marker(1),
         gst(1, source_status_iv="error"), d1(1), E.R_CORE_GATE_FAILED),
        ("B5. S-4 incomplete D1", reg_row(1), marker(1), gst(1),
         d1(1, open_to_30m=_DROP), E.R_D1_GATE_FAILED),
        ("B6. S-5 malformed GST digest", reg_row(1), marker(1),
         gst(1, provenance_sha256="short"), d1(1), E.R_GST_PROVENANCE_FAILED),
        ("B7. S-6 absent primary outcome", reg_row(1), marker(1), gst(1),
         d1(1, abs_overnight_gap=_DROP), E.R_OUTCOME_MISSING),
        ("B8. S-6 unverified market-data provenance", reg_row(1), marker(1), gst(1),
         d1(1, market_data_provenance_valid=False), E.R_OUTCOME_MISSING),
        ("B9. S-7 registered INTRADAY release", reg_row(1, session="INTRADAY"),
         marker(1), gst(1), d1(1), E.R_MEASUREMENT_INCOMPATIBLE_INTRADAY),
    ]
    for label, row, mk, g, d, want in cases:
        s = one(row, mk, g, d)
        check(f"{label} -> {want}", sole_reason(s) == want, sole_reason(s))

    s = one(reg_row(1, session="BMO"), marker(1), gst(1), d1(1))
    check("B10. S-7 BMO is an accepted registered session",
          s["eligible_event_count"] == 1, sole_reason(s))

    check("B11. every emitted reason is a registered code",
          all(r in E.REASONS or r in E.JOIN_REFUSALS for r in s["exclusions_by_reason"]),
          str([r for r in s["exclusions_by_reason"]
               if r not in E.REASONS and r not in E.JOIN_REFUSALS]))

    print("\n=== C. gate arithmetic ===")

    s59 = run(*cohort(59))
    check("C1. 59 eligible events do not trigger the freeze",
          s59["eligible_event_count"] == 59 and s59["freeze_required"] is False
          and s59["counting_state"] == "COUNTING",
          json.dumps({k: v for k, v in s59["exclusions_by_reason"].items() if v}))
    check("C2. remaining_until_target is 1 at 59", s59["remaining_until_target"] == 1)

    s60 = run(*cohort(60))
    check("C3. the 60th eligible event triggers the freeze exactly once",
          s60["eligible_event_count"] == 60 and s60["freeze_required"] is True
          and s60["counting_state"] == "REFUSED_AT_GATE")
    check("C4. remaining_until_target is 0 at the gate, never negative",
          s60["remaining_until_target"] == 0)

    s75 = run(*cohort(75))
    check("C5. beyond 60 the frozen set stays at 60",
          s75["eligible_event_count"] == 60 and len(s75["eligible_event_ids"]) == 60,
          str(s75["eligible_event_count"]))
    check("C6. the surplus 15 are EXTENSION_COHORT, not eligible",
          s75["exclusions_by_reason"]["EXTENSION_COHORT"] == 15
          and len(s75["extension_cohort_event_ids"]) == 15)
    check("C7. counting still REFUSES beyond the gate",
          s75["counting_state"] == "REFUSED_AT_GATE"
          and s75["remaining_until_target"] == 0)
    check("C8. the frozen 60 follow the registered expected_response_session order",
          s75["eligible_event_ids"] == sorted(
              s75["eligible_event_ids"],
              key=lambda e: (_rdate(int(e[6:9])), e)))
    check("C9. the driver never authorizes the analysis, even at the gate",
          s60["analysis_authorized"] is False and s75["analysis_authorized"] is False)
    check("C10. eligible + all exclusions == effective events seen",
          sum(s75["exclusions_by_reason"].values()) + s75["eligible_event_count"]
          == s75["effective_events_seen"])

    print("\n=== D. non-disclosure and determinism ===")

    blob = json.dumps(s75)
    leaked = [k for k, v in SENTINELS.items() if str(v) in blob]
    check("D1. no sentinel measurement value reaches the status document",
          not leaked, f"leaked: {leaked}")
    keyed = [k for k in SENTINELS if k in blob]
    check("D2. no measurement field name reaches the status document",
          not keyed, f"present: {keyed}")

    proj = E.project_marker(marker(1))
    check("D3. the marker's response_magnitude block is projected away on ingest",
          "response_magnitude" not in proj
          and str(SENTINELS["abs_overnight_gap"]) not in json.dumps(proj),
          str(sorted(proj)))

    rows, mks, gs, ds = cohort(30)
    a = E.status_digest(run(rows, mks, gs, ds))
    b = E.status_digest(run(rows, mks, gs, ds))
    check("D4. repeated runs are byte-identical", a == b)
    c = E.status_digest(run(rows, list(reversed(mks)), list(reversed(gs)),
                            list(reversed(ds))))
    check("D5. leg ordering does not change the result", a == c)
    check("D6. the status document is self-describing",
          s75["schema"] == "GST_HYP01_ELIGIBILITY_STATUS_v1"
          and s75["binding_target"] == 60)

    print("\n=== E. first-failure precedence under the registered order ===")

    s = one(reg_row(1, session="INTRADAY"), marker(1), None, d1(1))
    check("E1. timing + missing GST leg -> MISSING_GST_LEG",
          sole_reason(s) == E.J_MISSING_GST_LEG, sole_reason(s))

    s = one(reg_row(1, session="INTRADAY"), marker(1), gst(1), None)
    check("E2. timing + missing D1 leg -> MISSING_D1_LEG",
          sole_reason(s) == E.J_MISSING_D1_LEG, sole_reason(s))

    s = one(reg_row(1), marker(1), gst(1, provenance_sha256="short"),
            d1(1, open_to_30m=_DROP))
    check("E3. S-4 completeness + S-5 provenance -> D1_GATE_FAILED",
          sole_reason(s) == E.R_D1_GATE_FAILED, sole_reason(s))

    s = one(reg_row(1), marker(1),
            gst(1, wiki_zscore=_DROP, provenance_sha256="short"), d1(1))
    check("E4. S-3 core + S-5 provenance -> CORE_GATE_FAILED",
          sole_reason(s) == E.R_CORE_GATE_FAILED, sole_reason(s))

    try:
        run([reg_row(1), reg_row(1, row_id=f"{_eid(1)}-REG-002")],
            [marker(1)], [gst(1, wiki_zscore=_DROP)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_BASE_REGISTRATION
    check("E5. duplicate base registration + other failures -> registry refusal", ok)

    # Adjacent ordered pairs.
    pairs = [
        ("E6. S-1 + S-2", reg_row(1, status="pending"),
         marker(1, block=elig_block(core=False)), gst(1), d1(1), E.R_NOT_ENROLLED),
        ("E7. S-2 + S-3", reg_row(1), marker(1, block=elig_block(core=False)),
         gst(1, wiki_zscore=_DROP), d1(1), E.R_CLASS_INELIGIBLE),
        ("E8. S-3 + S-4", reg_row(1), marker(1), gst(1, wiki_zscore=_DROP),
         d1(1, open_to_30m=_DROP), E.R_CORE_GATE_FAILED),
        ("E9. S-4 + S-5", reg_row(1), marker(1), gst(1, provenance_sha256="short"),
         d1(1, thirty_min_to_close=_DROP), E.R_D1_GATE_FAILED),
        ("E10. S-5 + S-6", reg_row(1), marker(1), gst(1, provenance_sha256="short"),
         d1(1, abs_overnight_gap=_DROP), E.R_GST_PROVENANCE_FAILED),
        ("E11. S-6 + S-7", reg_row(1, session="INTRADAY"), marker(1), gst(1),
         d1(1, abs_overnight_gap=_DROP), E.R_OUTCOME_MISSING),
    ]
    for label, row, mk, g, d, want in pairs:
        s = one(row, mk, g, d)
        check(f"{label} -> {want}", sole_reason(s) == want, sole_reason(s))

    # S-7 + S-8: 60 valid events already fill the cohort, so an extra eligible
    # event would rank 61 and be EXTENSION_COHORT. Being INTRADAY it must fail
    # S-7 first instead.
    rows, mks, gs, ds = cohort(60)
    rows.append(reg_row(90, session="INTRADAY"))
    mks.append(marker(90)); gs.append(gst(90)); ds.append(d1(90))
    s = run(rows, mks, gs, ds)
    check("E12. S-7 + S-8 -> MEASUREMENT_INCOMPATIBLE_INTRADAY, not EXTENSION_COHORT",
          s["exclusions_by_reason"]["MEASUREMENT_INCOMPATIBLE_INTRADAY"] == 1
          and s["exclusions_by_reason"]["EXTENSION_COHORT"] == 0
          and s["eligible_event_count"] == 60,
          json.dumps({k: v for k, v in s["exclusions_by_reason"].items() if v}))

    s = one(reg_row(1, status="pending", session="INTRADAY"),
            marker(1, block=elig_block(core=False)),
            gst(1, wiki_zscore=_DROP, provenance_sha256="short"),
            d1(1, open_to_30m=_DROP, abs_overnight_gap=_DROP))
    check("E13. an event failing every gate receives the S-1 code",
          sole_reason(s) == E.R_NOT_ENROLLED, sole_reason(s))

    single = [
        one(reg_row(1, status="pending"), marker(1), gst(1), d1(1)),
        one(reg_row(1), marker(1, block=elig_block(core=False)), gst(1), d1(1)),
        one(reg_row(1), marker(1), gst(1, wiki_zscore=_DROP), d1(1)),
        one(reg_row(1), marker(1), gst(1), d1(1, open_to_30m=_DROP)),
        one(reg_row(1), marker(1), gst(1, provenance_sha256="short"), d1(1)),
        one(reg_row(1), marker(1), gst(1), d1(1, abs_overnight_gap=_DROP)),
        one(reg_row(1, session="INTRADAY"), marker(1), gst(1), d1(1)),
    ]
    observed = tuple(sole_reason(x) for x in single)
    expected = tuple(code for _, code in E.REGISTERED_GATE_ORDER[:7])
    check("E14. observed first-failure codes match the declared S-1..S-7 order",
          observed == expected, f"{observed} != {expected}")

    check("E15. S-8 is the EXTENSION_COHORT gate, applied by the driver",
          E.REGISTERED_GATE_ORDER[7] == ("S-8", E.R_EXTENSION_COHORT)
          and s75["exclusions_by_reason"]["EXTENSION_COHORT"] == 15)

    print("\n=== F. provenance guarantees ===")

    bad_gst = one(reg_row(1), marker(1), gst(1, provenance_sha256="short"), d1(1))
    bad_gst_absent = one(reg_row(1), marker(1), gst(1, provenance_path=_DROP), d1(1))
    bad_d1 = one(reg_row(1), marker(1), gst(1), d1(1, provenance_sha256="nope"))

    check("F1. a GST provenance failure is never marked eligible",
          bad_gst["eligible_event_ids"] == []
          and bad_gst_absent["eligible_event_ids"] == [])
    check("F2. a GST provenance failure does not increment the eligible count",
          bad_gst["eligible_event_count"] == 0
          and bad_gst_absent["eligible_event_count"] == 0)
    check("F3. a D1 provenance failure is never eligible and gets OUTCOME_MISSING",
          bad_d1["eligible_event_count"] == 0
          and sole_reason(bad_d1) == E.R_OUTCOME_MISSING, sole_reason(bad_d1))
    check("F4. a provenance failure receives the registered provenance code",
          sole_reason(bad_gst) == E.R_GST_PROVENANCE_FAILED
          and sole_reason(bad_gst_absent) == E.R_GST_PROVENANCE_FAILED)
    check("F5. GST_PROVENANCE_FAILED is reachable through the full driver",
          bad_gst["exclusions_by_reason"][E.R_GST_PROVENANCE_FAILED] == 1)

    rows, mks, gs, ds = cohort(59)
    rows.append(reg_row(91)); mks.append(marker(91))
    gs.append(gst(91, provenance_sha256="short")); ds.append(d1(91))
    mixed = run(rows, mks, gs, ds)
    check("F6. a provenance failure cannot contribute to the event-60 freeze",
          mixed["eligible_event_count"] == 59 and mixed["freeze_required"] is False
          and mixed["counting_state"] == "COUNTING"
          and mixed["remaining_until_target"] == 1,
          json.dumps({k: v for k, v in mixed["exclusions_by_reason"].items() if v}))
    check("F7. no unregistered failure code is emitted in a mixed cohort",
          all(r in E.REASONS or r in E.JOIN_REFUSALS
              for r in mixed["exclusions_by_reason"]))

    joined = E.join_event(reg_row(1), E.project_marker(marker(1)),
                          gst(1, provenance_sha256="short"), d1(1))
    check("F8. join output carries no eligibility designation to bypass the ladder",
          not any(k in joined for k in
                  ("eligible", "is_eligible", "eligibility", "passed", "status")),
          str(sorted(joined)))
    ok, why = E.classify(reg_row(1), joined, None)
    check("F9. a cleanly-joined but provenance-failed event is refused by the ladder",
          ok is False and why == E.R_GST_PROVENANCE_FAILED, f"{ok} {why}")

    only_gate = one(reg_row(1), marker(1), gst(1),
                    d1(1, market_data_provenance_valid=False))
    check("F10. a joinable event failing a ladder gate never enters the cohort",
          only_gate["eligible_event_ids"] == []
          and sole_reason(only_gate) == E.R_OUTCOME_MISSING)

    print(f"\n{CHECKS} checks run")
    if FAILURES:
        print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL HYP-01 ELIGIBILITY JOIN + DRIVER CHECKS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
