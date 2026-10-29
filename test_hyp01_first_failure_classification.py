#!/usr/bin/env python3
"""Regression suite: one effective event == exactly one terminal classification.

THE DEFECT THIS PINS DOWN. The canonical path used to classify some events
twice. load_canonical_evidence() caught a precise per-event JoinRefusal and
omitted that event's legs; run_driver() then saw the absent legs and recorded a
second, generic refusal (JOIN_REFUSED_MISSING_GST_LEG); run_canonical() finally
added the original refusal to the tally as well. Two registry rows could
produce four exclusion counts.

It also inspected every registry row's event store, markers and plan BEFORE
S-1 had a chance to classify a non-verified row as NOT_ENROLLED, so a
non-enrolled event both leaked downstream reads and picked up a structural
refusal it should never have had.

Fixtures are built through the project's own writers in a temporary directory.
A socket guard fails the run on any connection attempt, and an audit hook
records every file open so "these artifacts were never opened" is proven by
evidence rather than asserted.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import socket
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
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
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / "tools"))

from gst_market_response import pipeline                                   # noqa: E402
from gst_market_response.event_record import EventStore                    # noqa: E402
from gst_market_response.event_registry import HumanVerifiedEventRegistry  # noqa: E402
from gst_market_response.exchange_calendar import (                        # noqa: E402
    is_trading_day, previous_session, session_close_utc, session_open_utc,
)
from gst_market_response.operations_plan import (                          # noqa: E402
    build_operations_plan, finalize_plan,
)
from gst_market_response.stage_markers import (                            # noqa: E402
    STAGE_D1, STAGE_PRE_EVENT, marker_path, write_stage_marker,
)

_spec = importlib.util.spec_from_file_location(
    "hyp01_canonical_adapter", _HERE / "tools" / "hyp01_canonical_adapter.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
EL = A.EL

FAILURES: list[str] = []
CHECKS = 0
TMP = Path(tempfile.mkdtemp(prefix="hyp01_ffc_"))

SENT = {"gst_zscore": 7.7777771, "wiki_zscore": -8.8888882,
        "panel_implied_volatility": 0.55555555, "realized_volatility": 0.44444446,
        "previous_close": 9999.99993, "volume": 123456784,
        "overnight_gap": -5.55555558, "open_to_30m": 1.11111112,
        "thirty_min_to_close": 2.22222220, "open_to_close": 3.33333339}
HASH_A = "a" * 64
HASH_B = "b" * 64
TICKERS = ["AAPL", "ABBV", "ADBE", "AMZN", "BKR", "CTSH", "DELL", "DVN", "GME",
           "GOOGL", "GPN", "INTC", "LDOS", "MSFT", "NCLH", "NKE", "QCOM",
           "SBUX", "STZ", "SYK", "TSLA", "TTWO", "UAL"]


def check(label, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}  {detail}")
        FAILURES.append(label)


class Roots:
    _n = 0

    def __init__(self):
        Roots._n += 1
        base = TMP / f"proj{Roots._n:04d}"
        self.registry, self.store = base / "reg", base / "store"
        self.markers, self.plans = base / "mk", base / "plans"
        for d in (self.registry, self.store, self.markers, self.plans):
            d.mkdir(parents=True, exist_ok=True)
        self.reg = HumanVerifiedEventRegistry(self.registry)
        self.es = EventStore(self.store)

    def status(self):
        return A.run_canonical(self.registry, self.store, self.markers, self.plans)


def core_fields(anchor=None, **over):
    """`anchor` is the event's mechanically derived pre-event anchor. The
    snapshot and panel dates must equal it, or the adapter refuses -- that
    binding is the point of the PRE_EVENT anchor check."""
    a = (anchor.isoformat() if hasattr(anchor, "isoformat") else anchor) or "2026-08-03"
    f = {**{k: SENT[k] for k in ("gst_zscore", "wiki_zscore",
                                 "panel_implied_volatility", "realized_volatility",
                                 "previous_close", "volume")},
         "source_status_gst": "ok", "source_status_wiki": "ok",
         "source_status_iv": "ok", "source_status_realized_vol": "ok",
         "source_status_price": "ok",
         "pre_event_snapshot_asof_utc": f"{a}T13:00:00+00:00",
         "run_date": a,
         "price_asof_date": a,
         "source_csv_path": "synthetic/panel.csv", "source_csv_sha256": HASH_A,
         "source_marker_path": "synthetic/pm.json", "source_marker_sha256": HASH_B,
         "methodology_version": "market_response_v0.2",
         "research_commit_sha": "0" * 40}
    f.update(over)
    return {k: v for k, v in f.items() if v is not None}


OPT = {"option_benchmark_status": "UNAVAILABLE_NO_VERIFIED_SOURCE",
       "option_benchmark_unavailable_reason": "synthetic"}


def d1_fields(**over):
    f = {k: SENT[k] for k in ("overnight_gap", "open_to_30m",
                              "thirty_min_to_close", "open_to_close")}
    f.update(over)
    return f


def _release_dt(d: date, session: str) -> datetime:
    """A release instant consistent with the declared session, so the planner's
    mechanical calendar cross-check accepts it."""
    if not is_trading_day(d):
        return datetime(d.year, d.month, d.day, 21, tzinfo=timezone.utc)
    if session == "INTRADAY":
        return session_close_utc(d) - timedelta(hours=2)
    if session == "BMO":
        return session_open_utc(d) - timedelta(hours=1)
    return session_close_utc(d) + timedelta(minutes=30)


def register(r, ticker, fy, earnings, *, status="verified", session="AMC"):
    return r.reg.register_verified_event(
        ticker=ticker, fiscal_period=fy, earnings_date=earnings,
        earnings_datetime_utc=_release_dt(earnings, session),
        release_market_session=session,
        source_url="https://synthetic.invalid/ir", source_title="synthetic",
        source_type="company_ir_press_release",
        source_retrieved_at_utc=datetime(2026, 7, 1, tzinfo=timezone.utc),
        verified_at_utc=datetime(2026, 7, 1, tzinfo=timezone.utc),
        verified_by="synthetic-operator", verification_status=status)


def write_plan(r, eid):
    plan = finalize_plan(build_operations_plan(
        registry_path=r.registry / "registry.jsonl", event_id=eid,
        company_name="Synthetic Co",
        generated_at_utc=datetime(2026, 7, 2, tzinfo=timezone.utc),
        planning_commit="0" * 40, methodology_version="market_response_v0.2"))
    (r.plans / A.PLAN_FILENAME.format(event_id=eid)).write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8")


def build_event(r, ticker, fy, earnings, *, status="verified", session="AMC",
                with_pre=True, with_pre_marker=True, with_d1=True,
                with_d1_marker=True, with_plan=True, core=None, d1=None):
    row = register(r, ticker, fy, earnings, status=status, session=session)
    eid = row.event_id
    anchor = previous_session(earnings)
    pipeline.register_event(r.es, eid, {"ticker": ticker})
    if not with_pre:
        with_d1 = False
    if with_pre:
        pipeline.capture_pre_event_and_option_benchmark_v0_2(
            r.es, eid, core if core is not None else core_fields(anchor), dict(OPT))
        if with_pre_marker:
            write_stage_marker(r.markers, eid, STAGE_PRE_EVENT, r.es)
    if with_d1:
        pipeline.capture_d1(r.es, eid, d1 if d1 is not None else d1_fields())
        if with_d1_marker:
            write_stage_marker(r.markers, eid, STAGE_D1, r.es)
    if with_plan:
        write_plan(r, eid)
    return eid


def nonzero(status):
    return {k: v for k, v in status["exclusions_by_reason"].items() if v}


def terminal_total(status):
    return sum(status["exclusions_by_reason"].values()) + status["eligible_event_count"]


def status_with_open_audit(r):
    """Run the canonical path while recording every file the interpreter opens.

    sys.addaudithook cannot be bypassed by pathlib or os.open, so the resulting
    path list is evidence, not inspection.
    """
    opened: list[str] = []
    armed = [False]

    def hook(event, args):
        if armed[0] and event == "open":
            try:
                opened.append(str(args[0]))
            except Exception:
                pass

    sys.addaudithook(hook)
    armed[0] = True
    try:
        st = r.status()
    finally:
        armed[0] = False
    return st, opened


def main() -> int:
    print("=== 1. non-verified registration, no downstream artifacts ===")

    r = Roots()
    row = register(r, "DELL", "FY27Q2", date(2026, 8, 3), status="pending")
    st, opened = status_with_open_audit(r)
    check("1a. only NOT_ENROLLED is recorded",
          nonzero(st) == {"NOT_ENROLLED": 1}, json.dumps(nonzero(st)))
    check("1b. no structural refusal is attached",
          not any(k.startswith("JOIN_REFUSED_") for k in nonzero(st)),
          json.dumps(nonzero(st)))
    check("1c. exactly one terminal classification for one event",
          terminal_total(st) == 1 and st["effective_events_seen"] == 1,
          f"total={terminal_total(st)} seen={st['effective_events_seen']}")
    check("1d. the adapter reports it stopped at S-1",
          st["adapter"]["events_stopped_at_s1_not_enrolled"] == 1
          and st["adapter"]["events_refused_structurally"] == 0,
          json.dumps(st["adapter"]))
    store_opens = [o for o in opened if row.event_id in o and o.endswith(".jsonl")]
    check("1e. the event-store log was never opened",
          not store_opens, str(store_opens))

    print("\n=== 2. non-verified registration with poisoned downstream files ===")

    r = Roots()
    row = register(r, "MSFT", "FY27Q2", date(2026, 8, 4), status="rejected")
    eid = row.event_id
    poisoned = {
        "event_store": r.store / f"{eid}.jsonl",
        "pre_marker": marker_path(r.markers, eid, STAGE_PRE_EVENT),
        "d1_marker": marker_path(r.markers, eid, STAGE_D1),
        "plan": r.plans / A.PLAN_FILENAME.format(event_id=eid),
    }
    for p in poisoned.values():
        p.write_text("{ this is not valid JSON at all ][", encoding="utf-8")

    st, opened = status_with_open_audit(r)
    check("2a. a poisoned non-enrolled event is still only NOT_ENROLLED",
          nonzero(st) == {"NOT_ENROLLED": 1}, json.dumps(nonzero(st)))
    check("2b. exactly one terminal classification",
          terminal_total(st) == 1 == st["effective_events_seen"])
    opened_norm = [str(Path(o)).lower() for o in opened]
    touched = {name: str(p).lower() in opened_norm for name, p in poisoned.items()}
    check("2c. none of the poisoned artifacts was opened",
          not any(touched.values()), str(touched))
    check("2d. malformed JSON was not converted into a scientific exclusion",
          "CLASS_INELIGIBLE" not in nonzero(st)
          and "CORE_GATE_FAILED" not in nonzero(st))

    print("\n=== 3. verified event missing PRE_EVENT state ===")

    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3), with_pre=False)
    st = r.status()
    check("3a. exactly MISSING_PRE_EVENT_STATE = 1, and nothing else",
          nonzero(st) == {EL.J_MISSING_PRE_EVENT_STATE: 1}, json.dumps(nonzero(st)))
    check("3b. the generic MISSING_GST_LEG refusal is 0",
          st["exclusions_by_reason"].get(EL.J_MISSING_GST_LEG, 0) == 0)
    check("3c. total terminal classifications == 1",
          terminal_total(st) == 1 == st["effective_events_seen"],
          f"total={terminal_total(st)} seen={st['effective_events_seen']}")

    print("\n=== 4. verified event missing the D1 marker ===")

    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3), with_d1_marker=False)
    st = r.status()
    check("4a. exactly the precise D1-marker refusal, and nothing else",
          nonzero(st) == {EL.J_MISSING_D1_MARKER: 1}, json.dumps(nonzero(st)))
    check("4b. no generic missing-leg refusal appears",
          st["exclusions_by_reason"].get(EL.J_MISSING_GST_LEG, 0) == 0
          and st["exclusions_by_reason"].get(EL.J_MISSING_D1_LEG, 0) == 0)
    check("4c. total terminal classifications == 1", terminal_total(st) == 1)

    # The same, for every other missing canonical artifact -- complete tally,
    # not merely "the expected code appears somewhere".
    for label, kw, want in (
            ("PRE_EVENT marker", dict(with_pre_marker=False), EL.J_MISSING_PRE_EVENT_MARKER),
            ("D1 state", dict(with_d1=False), EL.J_MISSING_D1_STATE),
            ("operations plan", dict(with_plan=False), EL.J_MISSING_OPERATIONS_PLAN)):
        r = Roots()
        build_event(r, "DELL", "FY27Q2", date(2026, 8, 3), **kw)
        st = r.status()
        check(f"4d. missing {label} -> complete tally is exactly {{{want}: 1}}",
              nonzero(st) == {want: 1}, json.dumps(nonzero(st)))

    print("\n=== 5. mixed cohort: one of each category ===")

    r = Roots()
    eligible_id = build_event(r, "AAPL", "FY27Q2", date(2026, 8, 3))
    register(r, "MSFT", "FY27Q2", date(2026, 8, 4), status="pending")
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 5), with_d1_marker=False)
    # A REACHABILITY FINDING, not a shortcut. CORE_GATE_FAILED, CLASS_INELIGIBLE,
    # D1_GATE_FAILED and OUTCOME_MISSING cannot be produced through the canonical
    # writers at all: a failing strict-core or D1 gate drives the event to
    # PARTIAL, which validate_transition() treats as terminal, so no D1_COMPLETE
    # record is ever written and the adapter refuses structurally instead. The
    # scientific exclusion that IS canonically reachable is S-7: an INTRADAY
    # release is registered normally and captured normally, and fails only at the
    # session gate. Those codes remain reachable at the primitive level and are
    # exercised in test_hyp01_eligibility.py.
    build_event(r, "TSLA", "FY27Q2", date(2026, 8, 6), session="INTRADAY")
    st = r.status()
    expected = {EL.J_MISSING_D1_MARKER: 1, "NOT_ENROLLED": 1,
                "MEASUREMENT_INCOMPATIBLE_INTRADAY": 1}
    check("5a. effective_events_seen == 4", st["effective_events_seen"] == 4,
          str(st["effective_events_seen"]))
    check("5b. exactly one eligible event", st["eligible_event_count"] == 1
          and st["eligible_event_ids"] == [eligible_id], str(st["eligible_event_ids"]))
    check("5c. the complete nonzero tally is one of each remaining category",
          nonzero(st) == expected, json.dumps(nonzero(st)))
    check("5d. reconciliation invariant holds: 1 eligible + 3 exclusions == 4",
          terminal_total(st) == 4, str(terminal_total(st)))
    check("5e. the scientific failure was NOT replaced by a structural refusal",
          st["exclusions_by_reason"]["MEASUREMENT_INCOMPATIBLE_INTRADAY"] == 1)
    check("5f. the structural refusal was NOT replaced by a scientific exclusion",
          st["exclusions_by_reason"][EL.J_MISSING_D1_MARKER] == 1)
    check("5g. a registry snapshot digest is recorded, not registry contents",
          len(st["registry_snapshot_sha256"]) == 64
          and "verified_by" not in json.dumps(st)
          and "source_url" not in json.dumps(st))

    print("\n=== 6. gate arithmetic is unchanged ===")

    def cohort(n):
        rr = Roots()
        d = date(2026, 3, 2)
        for i in range(n):
            while not is_trading_day(d):
                d += timedelta(days=1)
            build_event(rr, TICKERS[i % len(TICKERS)],
                        f"FY27Q{(i // len(TICKERS)) + 1}", d)
            d += timedelta(days=1)
        return rr

    s59 = cohort(59).status()
    check("6a. 59 eligible: no freeze, 1 remaining, invariant holds",
          s59["eligible_event_count"] == 59 and s59["freeze_required"] is False
          and s59["remaining_until_target"] == 1
          and terminal_total(s59) == 59, json.dumps(nonzero(s59)))

    r61 = cohort(61)
    s61 = r61.status()
    check("6b. 61 eligible: frozen at 60, 1 in the extension cohort",
          s61["eligible_event_count"] == 60
          and s61["exclusions_by_reason"]["EXTENSION_COHORT"] == 1
          and s61["freeze_required"] is True
          and s61["counting_state"] == "REFUSED_AT_GATE", json.dumps(nonzero(s61)))
    check("6c. invariant holds at the gate: 60 + 1 extension == 61",
          terminal_total(s61) == 61 == s61["effective_events_seen"],
          str(terminal_total(s61)))
    check("6d. reruns are byte-identical (idempotent)",
          EL.status_digest(r61.status()) == EL.status_digest(s61))

    print("\n=== 7. no measurement value or field name leaks ===")

    blob = json.dumps(s61)
    leaked = [k for k, v in SENT.items() if str(v) in blob]
    check("7a. no sentinel measurement value reaches the status document",
          not leaked, str(leaked))
    named = [k for k in SENT if k in blob]
    check("7b. no measurement field name reaches the status document",
          not named, str(named))
    check("7c. abs_overnight_gap never appears", "abs_overnight_gap" not in blob)

    print("\n=== 8. malformed canonical JSON fails closed ===")

    for label, target in (("PRE_EVENT marker", STAGE_PRE_EVENT),
                          ("D1 marker", STAGE_D1)):
        r = Roots()
        eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
        marker_path(r.markers, eid, target).write_text("{ broken ][", encoding="utf-8")
        st = r.status()
        check(f"8a. a malformed {label} refuses structurally, exactly once",
              nonzero(st) == {EL.J_MALFORMED_CANONICAL_JSON: 1}, json.dumps(nonzero(st)))

    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    (r.plans / A.PLAN_FILENAME.format(event_id=eid)).write_text("[[[", encoding="utf-8")
    st = r.status()
    check("8b. a malformed operations plan refuses structurally, exactly once",
          nonzero(st) == {EL.J_MALFORMED_CANONICAL_JSON: 1}, json.dumps(nonzero(st)))

    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    (r.store / f"{eid}.jsonl").write_text("not json\n", encoding="utf-8")
    st = r.status()
    check("8c. a malformed event-store log refuses structurally, exactly once",
          nonzero(st) == {EL.J_MALFORMED_CANONICAL_JSON: 1}, json.dumps(nonzero(st)))

    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    (r.registry / "registry.jsonl").write_text("{ not jsonl\n", encoding="utf-8")
    try:
        r.status()
        ok, code = False, "no refusal"
    except EL.JoinRefusal as e:
        ok, code = e.code == EL.J_MALFORMED_CANONICAL_JSON, e.code
    check("8d. a malformed registry refuses at run level, not per event", ok, code)

    check("8e. no malformed artifact became a scientific disposition",
          all(k in EL.JOIN_REFUSALS or k == "NOT_ENROLLED"
              for k in nonzero(st)) if nonzero(st) else True)

    print("\n=== 9. reconciliation invariant is enforced, not merely computed ===")

    bad = {"exclusions_by_reason": {"NOT_ENROLLED": 2}, "eligible_event_count": 1,
           "effective_events_seen": 2}
    try:
        EL.reconcile(bad)
        ok = False
    except EL.ReconciliationError:
        ok = True
    check("9a. reconcile() raises when an event is counted twice", ok)

    good = {"exclusions_by_reason": {"NOT_ENROLLED": 1}, "eligible_event_count": 1,
            "effective_events_seen": 2}
    try:
        EL.reconcile(good)
        ok = True
    except EL.ReconciliationError:
        ok = False
    check("9b. reconcile() accepts a correct tally", ok)

    print("\n=== 10. progressive ladder: stage-specific PARTIAL is evidence ===")

    # -- PRE_EVENT strict-core failure, written by the production writer -----
    # capture_pre_event_and_option_benchmark_v0_2() appends PARTIAL tagged
    # failure_stage="pre_event", carrying the module-eligibility block and the
    # strict-core fields. write_stage_marker() is permitted for exactly that
    # PARTIAL. The ladder must reach the registered SCIENTIFIC disposition.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                      core=core_fields(previous_session(date(2026, 8, 3)), wiki_zscore=None), with_d1=False)
    states = [x for x in r.es.read_all(eid) if x["record_type"] == "STATE"]
    from gst_market_response.event_record import (                      # noqa: E402
        FAILURE_STAGE_D1, FAILURE_STAGE_PRE_EVENT, partial_failure_stage,
    )
    check("10a. the production writer created a stage-specific PRE_EVENT PARTIAL",
          states[-1]["state"] == "PARTIAL"
          and partial_failure_stage(states, len(states) - 1) == FAILURE_STAGE_PRE_EVENT,
          str([x["state"] for x in states]))
    check("10b. the production marker writer created the PRE_EVENT marker",
          marker_path(r.markers, eid, STAGE_PRE_EVENT).exists())

    st, opened = status_with_open_audit(r)
    check("10c. a PRE_EVENT PARTIAL yields the S-2 scientific disposition, "
          "not a missing-state refusal",
          nonzero(st) == {"CLASS_INELIGIBLE": 1}, json.dumps(nonzero(st)))
    check("10d. exactly one terminal classification",
          terminal_total(st) == 1 == st["effective_events_seen"])
    # NOTE: since the PRE_EVENT anchor binding was added, the operations plan is
    # opened BEFORE S-2 -- it carries the anchor the PRE_EVENT evidence must be
    # bound to, so it is no longer "later" work. The D1 short-circuit guarantee
    # is unchanged and is what this check now asserts.
    later = [o for o in opened if o.endswith("_D1_CAPTURE_MARKER.json")]
    check("10e. no D1 marker was opened after S-2 failed", not later, str(later))

    # -- D1 decomposition failure, written by the production writer ----------
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                      d1=d1_fields(open_to_30m=None))
    states = [x for x in r.es.read_all(eid) if x["record_type"] == "STATE"]
    check("10f. the production writer created a stage-specific D1 PARTIAL",
          states[-1]["state"] == "PARTIAL"
          and partial_failure_stage(states, len(states) - 1) == FAILURE_STAGE_D1,
          str([x["state"] for x in states]))
    check("10g. the production marker writer created the D1 marker",
          marker_path(r.markers, eid, STAGE_D1).exists())

    st = r.status()
    check("10h. a D1 PARTIAL with an invalid decomposition yields D1_GATE_FAILED",
          nonzero(st) == {"D1_GATE_FAILED": 1}, json.dumps(nonzero(st)))
    check("10i. no later disposition is added after S-4 fails",
          "GST_PROVENANCE_FAILED" not in nonzero(st)
          and "OUTCOME_MISSING" not in nonzero(st)
          and terminal_total(st) == 1)

    # -- a PARTIAL belonging to the wrong stage is never reassigned ----------
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                      core=core_fields(previous_session(date(2026, 8, 3)), wiki_zscore=None), with_d1=False)
    states = A.read_state_log(EventStore(r.store), eid)
    try:
        A._stage_record(states, FAILURE_STAGE_D1, eid, A.D1_OK_STATES,
                        EL.J_MISSING_D1_STATE)
        ok, code = False, "accepted"
    except EL.JoinRefusal as e:
        ok, code = e.code == EL.J_MISSING_D1_STATE, e.code
    check("10j. a PRE_EVENT PARTIAL is never accepted as D1 evidence", ok, code)

    # -- a valid PARTIAL whose marker is absent stays STRUCTURAL -------------
    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                core=core_fields(previous_session(date(2026, 8, 3)), wiki_zscore=None), with_pre_marker=False,
                with_d1=False)
    st = r.status()
    check("10k. a PRE_EVENT PARTIAL with no marker is a precise structural "
          "refusal, never a scientific exclusion",
          nonzero(st) == {EL.J_MISSING_PRE_EVENT_MARKER: 1}, json.dumps(nonzero(st)))

    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                d1=d1_fields(open_to_30m=None), with_d1_marker=False)
    st = r.status()
    check("10l. a D1 PARTIAL with no marker is a precise structural refusal",
          nonzero(st) == {EL.J_MISSING_D1_MARKER: 1}, json.dumps(nonzero(st)))

    print("\n=== 11. six-category mixed cohort ===")

    r = Roots()
    ok_id = build_event(r, "AAPL", "FY27Q2", date(2026, 8, 3))          # eligible
    register(r, "MSFT", "FY27Q2", date(2026, 8, 4), status="pending")   # S-1
    build_event(r, "ADBE", "FY27Q2", date(2026, 8, 5),                  # S-2
                core=core_fields(previous_session(date(2026, 8, 5)), wiki_zscore=None), with_d1=False)
    build_event(r, "AMZN", "FY27Q2", date(2026, 8, 6),                  # S-4
                d1=d1_fields(open_to_30m=None))
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 7), with_d1_marker=False)  # structural
    build_event(r, "TSLA", "FY27Q2", date(2026, 8, 10), session="INTRADAY")   # S-7
    st, opened = status_with_open_audit(r)
    expected = {"NOT_ENROLLED": 1, "CLASS_INELIGIBLE": 1, "D1_GATE_FAILED": 1,
                EL.J_MISSING_D1_MARKER: 1, "MEASUREMENT_INCOMPATIBLE_INTRADAY": 1}
    check("11a. effective_events_seen == 6", st["effective_events_seen"] == 6,
          str(st["effective_events_seen"]))
    check("11b. exactly one eligible event",
          st["eligible_event_count"] == 1 and st["eligible_event_ids"] == [ok_id])
    check("11c. the complete nonzero tally is one of each remaining category",
          nonzero(st) == expected, json.dumps(nonzero(st)))
    check("11d. reconciliation: 1 eligible + 5 exclusions == 6",
          terminal_total(st) == 6, str(terminal_total(st)))
    check("11e. every category is represented exactly once",
          all(v == 1 for v in expected.values()) and len(expected) == 5)

    print("\n=== 12. missing canonical roots fail closed and create nothing ===")

    # HumanVerifiedEventRegistry.__init__ calls mkdir(parents=True, exist_ok=True),
    # so merely CONSTRUCTING it against a missing path creates that path and then
    # reads zero rows -- silently turning a broken invocation into a clean
    # "0 eligible events" report. The guard must fire before any constructor.
    base = TMP / "rootcheck"
    base.mkdir(parents=True, exist_ok=True)
    good = Roots()
    build_event(good, "DELL", "FY27Q2", date(2026, 8, 3))
    absent = base / "does_not_exist"

    cases = [
        ("registry root",     (absent, good.store, good.markers, good.plans), EL.J_MISSING_REGISTRY_ROOT),
        ("event-store root",  (good.registry, absent, good.markers, good.plans), EL.J_MISSING_EVENT_STORE_ROOT),
        ("marker root",       (good.registry, good.store, absent, good.plans), EL.J_MISSING_MARKER_ROOT),
        ("operations-plan root", (good.registry, good.store, good.markers, absent), EL.J_MISSING_PLAN_ROOT),
    ]
    for label, args, want in cases:
        before = sorted(x.name for x in base.iterdir())
        try:
            A.run_canonical(*args)
            ok, got = False, "NO REFUSAL"
        except EL.JoinRefusal as e:
            ok, got = e.code == want, e.code
        after = sorted(x.name for x in base.iterdir())
        check(f"12. missing {label} -> {want}", ok, got)
        check(f"12. missing {label} created nothing on disk",
              before == after and not absent.exists(),
              f"created {set(after) - set(before)}")

    # An empty directory with no registry.jsonl is NOT an empty cohort.
    empty = base / "empty_registry_root"
    empty.mkdir(exist_ok=True)
    try:
        A.run_canonical(empty, good.store, good.markers, good.plans)
        ok, got = False, "NO REFUSAL"
    except EL.JoinRefusal as e:
        ok, got = e.code == EL.J_MISSING_REGISTRY_FILE, e.code
    check("12. a registry root with no registry.jsonl refuses; it is never read "
          "as a valid zero-event cohort", ok, got)

    # And the guard is reachable through the primitive too.
    try:
        EL.load_registry_snapshot(absent)
        ok, got = False, "NO REFUSAL"
    except EL.JoinRefusal as e:
        ok, got = e.code == EL.J_MISSING_REGISTRY_ROOT, e.code
    check("12. load_registry_snapshot refuses a missing root before constructing", ok, got)
    check("12. the missing path was still not created", not absent.exists())

    print("\n=== 13. PRE_EVENT evidence is bound to the registered anchor ===")

    # Baseline: a correctly anchored event reaches the end of the ladder.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    check("13a. correctly anchored PRE_EVENT evidence passes the binding",
          r.status()["eligible_event_count"] == 1,
          json.dumps(nonzero(r.status())))

    # The snapshot must fall on the derived anchor session, not another session.
    r = Roots()
    wrong = previous_session(previous_session(date(2026, 8, 3)))
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                core=core_fields(wrong))
    st = r.status()
    check("13b. a snapshot taken on the wrong session refuses before S-2",
          nonzero(st) == {EL.J_PRE_EVENT_PANEL_DATE_MISMATCH: 1}, json.dumps(nonzero(st)))

    # A panel run_date that disagrees with the anchor refuses.
    r = Roots()
    a = previous_session(date(2026, 8, 3))
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                core=core_fields(a, run_date=previous_session(a).isoformat()))
    st = r.status()
    check("13c. a panel run_date that is not the anchor refuses",
          nonzero(st) == {EL.J_PRE_EVENT_PANEL_DATE_MISMATCH: 1}, json.dumps(nonzero(st)))

    # A nonblank but unparseable / naive snapshot instant refuses.
    for bad in ("not-a-timestamp", "2026-08-31T13:00:00"):
        r = Roots()
        build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                    core=core_fields(a, pre_event_snapshot_asof_utc=bad))
        st = r.status()
        check(f"13d. snapshot instant {bad!r} refuses (presence is not validity)",
              nonzero(st) == {EL.J_MALFORMED_SNAPSHOT_TIMESTAMP: 1}, json.dumps(nonzero(st)))

    # An amendment that moves registered timing invalidates evidence prepared
    # for the superseded anchor.
    r = Roots()
    row = register(r, "DELL", "FY27Q2", date(2026, 8, 3))
    eid = row.event_id
    pipeline.register_event(r.es, eid, {"ticker": "DELL"})
    pipeline.capture_pre_event_and_option_benchmark_v0_2(
        r.es, eid, core_fields(previous_session(date(2026, 8, 3))), dict(OPT))
    write_stage_marker(r.markers, eid, STAGE_PRE_EVENT, r.es)
    pipeline.capture_d1(r.es, eid, d1_fields())
    write_stage_marker(r.markers, eid, STAGE_D1, r.es)
    write_plan(r, eid)
    r.reg.amend_event(amends_row_id=row.row_id,
                      corrected_fields={"earnings_date": "2026-08-10",
                                        "earnings_datetime_utc":
                                            _release_dt(date(2026, 8, 10), "AMC").isoformat()},
                      verified_at_utc=datetime(2026, 8, 5, tzinfo=timezone.utc),
                      verified_by="synthetic-operator", notes="corrected date")
    st = r.status()
    got = nonzero(st)
    check("13e. an amendment moving registered timing invalidates the superseded "
          "PRE_EVENT evidence, before S-2",
          len(got) == 1 and next(iter(got)) in (
              EL.J_PRE_EVENT_ANCHOR_MISMATCH, EL.J_PRE_EVENT_PANEL_DATE_MISMATCH,
              EL.J_OPERATIONS_PLAN_MISMATCH), json.dumps(got))

    check("13f. the missing intra-session PRE_EVENT window is declared, not invented",
          "SPECIFICATION GAP" in A.validate_pre_event_anchor.__doc__
          and "intra-session" in A.validate_pre_event_anchor.__doc__)

    print(f"\n{CHECKS} checks run")
    if FAILURES:
        print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL HYP-01 FIRST-FAILURE CLASSIFICATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
