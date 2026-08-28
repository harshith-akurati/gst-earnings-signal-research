#!/usr/bin/env python3
"""Synthetic canonical end-to-end tests for the HYP-01 production path.

Every fixture is built through the PROJECT'S OWN WRITERS -- no raw JSON is
substituted where a production writer exists:

    HumanVerifiedEventRegistry.register_verified_event / amend_event
    pipeline.register_event
    pipeline.capture_pre_event_and_option_benchmark_v0_2
    pipeline.capture_d1                        (EventStore.append_state)
    stage_markers.write_stage_marker
    operations_plan.build_operations_plan / finalize_plan

Everything lives in a temporary directory. No project data file is read, no
real prospective record is opened, and a socket guard fails the run on any
connection attempt.
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

from gst_market_response import pipeline                                  # noqa: E402
from gst_market_response.event_record import EventStore                   # noqa: E402
from gst_market_response.event_registry import HumanVerifiedEventRegistry  # noqa: E402
from gst_market_response.exchange_calendar import (                       # noqa: E402
    is_trading_day, next_session, session_close_utc,
)
from gst_market_response.operations_plan import (                         # noqa: E402
    build_operations_plan, finalize_plan,
)
from gst_market_response.stage_markers import (                           # noqa: E402
    STAGE_D1, STAGE_PRE_EVENT, marker_path, write_stage_marker,
)

_spec = importlib.util.spec_from_file_location(
    "hyp01_canonical_adapter", _HERE / "tools" / "hyp01_canonical_adapter.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
EL = A.EL

FAILURES: list[str] = []
CHECKS = 0
TMP = Path(tempfile.mkdtemp(prefix="hyp01_canon_"))


def check(label, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}  {detail}")
        FAILURES.append(label)


# Sentinel measurements. If any reaches a status document, redaction failed.
SENT = {
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
}
HASH_A = "a" * 64
HASH_B = "b" * 64

TICKERS = ["AAPL", "ABBV", "ADBE", "AMZN", "BKR", "CTSH", "DELL", "DVN", "GME",
           "GOOGL", "GPN", "INTC", "LDOS", "MSFT", "NCLH", "NKE", "QCOM",
           "SBUX", "STZ", "SYK", "TSLA", "TTWO", "UAL"]


class Roots:
    """One isolated set of canonical roots."""

    _n = 0

    def __init__(self):
        Roots._n += 1
        base = TMP / f"proj{Roots._n:04d}"
        self.registry = base / "registry_root"
        self.store = base / "event_store"
        self.markers = base / "markers"
        self.plans = base / "plans"
        for d in (self.registry, self.store, self.markers, self.plans):
            d.mkdir(parents=True, exist_ok=True)
        self.reg = HumanVerifiedEventRegistry(self.registry)
        self.es = EventStore(self.store)

    def status(self):
        return A.run_canonical(self.registry, self.store, self.markers, self.plans)

    def snapshot(self):
        return EL.load_registry_snapshot(self.registry)

    def evidence(self, snapshot=None):
        return A.load_canonical_evidence(snapshot or self.snapshot(), self.store,
                                         self.markers, self.plans)


def core_fields(**over):
    f = {
        "gst_zscore": SENT["gst_zscore"],
        "wiki_zscore": SENT["wiki_zscore"],
        "panel_implied_volatility": SENT["panel_implied_volatility"],
        "realized_volatility": SENT["realized_volatility"],
        "previous_close": SENT["previous_close"],
        "volume": SENT["volume"],
        "source_status_gst": "ok", "source_status_wiki": "ok",
        "source_status_iv": "ok", "source_status_realized_vol": "ok",
        "source_status_price": "ok",
        "pre_event_snapshot_asof_utc": "2026-08-03T13:00:00+00:00",
        "source_csv_path": "synthetic/panel.csv",
        "source_csv_sha256": HASH_A,
        "source_marker_path": "synthetic/panel_marker.json",
        "source_marker_sha256": HASH_B,
        "methodology_version": "market_response_v0.2",
        "research_commit_sha": "0" * 40,
    }
    f.update(over)
    return f


OPTION_UNAVAILABLE = {
    "option_benchmark_status": "UNAVAILABLE_NO_VERIFIED_SOURCE",
    "option_benchmark_unavailable_reason": "synthetic fixture: no option feed",
}


def d1_fields(**over):
    f = {"overnight_gap": SENT["overnight_gap"],
         "open_to_30m": SENT["open_to_30m"],
         "thirty_min_to_close": SENT["thirty_min_to_close"],
         "open_to_close": SENT["open_to_close"]}
    f.update(over)
    return f


def _amc_datetime(d: date) -> datetime:
    """A release instant after that session's close, so the AMC label is
    mechanically consistent with the calendar cross-check in the planner."""
    if is_trading_day(d):
        return session_close_utc(d) + timedelta(minutes=30)
    return datetime(d.year, d.month, d.day, 21, 0, tzinfo=timezone.utc)


def register(r: Roots, ticker: str, fy: str, earnings: date, *,
             session="AMC", status="verified"):
    return r.reg.register_verified_event(
        ticker=ticker, fiscal_period=fy, earnings_date=earnings,
        earnings_datetime_utc=_amc_datetime(earnings),
        release_market_session=session,
        source_url="https://synthetic.invalid/ir",
        source_title="synthetic press release",
        source_type="company_ir_press_release",
        source_retrieved_at_utc=datetime(2026, 7, 1, tzinfo=timezone.utc),
        verified_at_utc=datetime(2026, 7, 1, tzinfo=timezone.utc),
        verified_by="synthetic-operator", verification_status=status)


def write_plan(r: Roots, event_id: str, *, company="Synthetic Co"):
    plan = finalize_plan(build_operations_plan(
        registry_path=r.registry / "registry.jsonl", event_id=event_id,
        company_name=company,
        generated_at_utc=datetime(2026, 7, 2, tzinfo=timezone.utc),
        planning_commit="0" * 40, methodology_version="market_response_v0.2"))
    (r.plans / A.PLAN_FILENAME.format(event_id=event_id)).write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan


def build_event(r: Roots, ticker: str, fy: str, earnings: date, *,
                session="AMC", status="verified", with_pre=True,
                with_pre_marker=True, with_d1=True, with_d1_marker=True,
                with_plan=True, core=None, d1=None):
    """One event, written entirely through the production writers."""
    row = register(r, ticker, fy, earnings, session=session, status=status)
    eid = row.event_id
    pipeline.register_event(r.es, eid, {"ticker": ticker, "fiscal_period": fy})
    # The mainline order forbids D1 without a captured pre-event stage, so an
    # event missing PRE_EVENT necessarily has no D1 either.
    if not with_pre:
        with_d1 = False
    if with_pre:
        pipeline.capture_pre_event_and_option_benchmark_v0_2(
            r.es, eid, core if core is not None else core_fields(),
            dict(OPTION_UNAVAILABLE))
        if with_pre_marker:
            write_stage_marker(r.markers, eid, STAGE_PRE_EVENT, r.es)
    if with_d1:
        pipeline.capture_d1(r.es, eid, d1 if d1 is not None else d1_fields())
        if with_d1_marker:
            write_stage_marker(r.markers, eid, STAGE_D1, r.es)
    if with_plan:
        write_plan(r, eid)
    return eid


def refusal_codes(r: Roots) -> list[str]:
    """Refusals are now a dict event_id -> JoinRefusal, keyed so the driver can
    thread each one into its single classification flow."""
    return sorted({e.code for e in r.evidence()["refusals"].values()})


def main() -> int:
    print("=== A. canonical happy path ===")

    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    ev = r.evidence()
    check("A1. the adapter derives all three legs from canonical artifacts",
          len(ev["markers"]) == 1 and len(ev["gst_legs"]) == 1
          and len(ev["d1_legs"]) == 1 and not ev["refusals"],
          str(ev["refusals"]))

    st = r.status()
    check("A2. a fully captured enrolled event is eligible end to end",
          st["eligible_event_count"] == 1 and st["eligible_event_ids"] == [eid],
          json.dumps({k: v for k, v in st["exclusions_by_reason"].items() if v}))
    check("A3. the status document records the canonical adapter provenance",
          st["adapter"]["source"] == "canonical"
          and st["adapter"]["d1_timing_validated_event_count"] == 1)
    check("A4. S-2 came from the persisted PRE_EVENT marker",
          ev["markers"][0]["stage"] == STAGE_PRE_EVENT
          and ev["markers"][0]["module_eligibility"]["core_pre_event_eligible"] is True)
    check("A5. the GST leg carries the six strict-core fields from the state record",
          all(k in ev["gst_legs"][0] for k in EL.STRICT_CORE_SIX_FIELDS))
    check("A6. the D1 leg carries the four intervals and abs_overnight_gap",
          all(k in ev["d1_legs"][0] for k in EL.D1_REQUIRED_FIELDS)
          and "abs_overnight_gap" in ev["d1_legs"][0])
    check("A7. market-data provenance is derived from D1_COMPLETE + marker echo",
          ev["d1_legs"][0]["market_data_provenance_valid"] is True)
    check("A8. provenance hashes come from canonical artifacts",
          ev["gst_legs"][0]["provenance_sha256"] == HASH_A
          and len(ev["d1_legs"][0]["provenance_sha256"]) == 64)

    # Amended registration.
    r = Roots()
    row = register(r, "MSFT", "FY27Q2", date(2026, 8, 3), status="pending")
    r.reg.amend_event(amends_row_id=row.row_id,
                      corrected_fields={"verification_status": "verified"},
                      verified_at_utc=datetime(2026, 7, 3, tzinfo=timezone.utc),
                      verified_by="synthetic-operator", notes="synthetic amendment")
    eid = row.event_id
    pipeline.register_event(r.es, eid, {"ticker": "MSFT"})
    pipeline.capture_pre_event_and_option_benchmark_v0_2(
        r.es, eid, core_fields(), dict(OPTION_UNAVAILABLE))
    write_stage_marker(r.markers, eid, STAGE_PRE_EVENT, r.es)
    pipeline.capture_d1(r.es, eid, d1_fields())
    write_stage_marker(r.markers, eid, STAGE_D1, r.es)
    write_plan(r, eid)
    st = r.status()
    check("A9. an effective amended registration is enrolled and counted once",
          st["eligible_event_count"] == 1 and st["effective_events_seen"] == 1,
          json.dumps({k: v for k, v in st["exclusions_by_reason"].items() if v}))

    print("\n=== B. missing / disagreeing canonical artifacts ===")

    cases = [
        ("B1. missing PRE_EVENT state", dict(with_pre=False),
         EL.J_MISSING_PRE_EVENT_STATE),
        ("B2. missing PRE_EVENT marker", dict(with_pre_marker=False),
         EL.J_MISSING_PRE_EVENT_MARKER),
        ("B3. missing D1 state", dict(with_d1=False), EL.J_MISSING_D1_STATE),
        ("B4. missing D1 marker", dict(with_d1_marker=False), EL.J_MISSING_D1_MARKER),
        ("B5. missing operations plan", dict(with_plan=False),
         EL.J_MISSING_OPERATIONS_PLAN),
    ]
    for label, kw, want in cases:
        r = Roots()
        build_event(r, "DELL", "FY27Q2", date(2026, 8, 3), **kw)
        got = refusal_codes(r)
        check(f"{label} -> {want}", got == [want], str(got))
        st = r.status()
        nz = {k: v for k, v in st["exclusions_by_reason"].items() if v}
        # The COMPLETE nonzero tally, not merely "the expected code appears":
        # a second generic refusal alongside it is exactly the defect this
        # guards against.
        check(f"{label} yields exactly one terminal classification",
              st["eligible_event_count"] == 0 and nz == {want: 1}
              and sum(st["exclusions_by_reason"].values()) == st["effective_events_seen"],
              json.dumps(nz))

    # Marker / state disagreement: tamper with the marker AFTER it is written.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    mp = marker_path(r.markers, eid, STAGE_D1)
    tampered = json.loads(mp.read_text(encoding="utf-8"))
    tampered["response_magnitude"]["abs_overnight_gap"] = 1.23456789
    mp.write_text(json.dumps(tampered), encoding="utf-8")
    check("B6. a D1 marker whose outcome echo disagrees with the record refuses",
          refusal_codes(r) == [EL.J_MARKER_STATE_DISAGREEMENT]
          and {k: v for k, v in r.status()["exclusions_by_reason"].items() if v}
              == {EL.J_MARKER_STATE_DISAGREEMENT: 1}, str(refusal_codes(r)))

    # The same, on the PRE_EVENT marker's persisted S-2 decision.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    mp = marker_path(r.markers, eid, STAGE_PRE_EVENT)
    tampered = json.loads(mp.read_text(encoding="utf-8"))
    tampered["module_eligibility"]["core_pre_event_eligible"] = False
    mp.write_text(json.dumps(tampered), encoding="utf-8")
    check("B6b. a PRE_EVENT marker whose eligibility block was edited refuses",
          refusal_codes(r) == [EL.J_MARKER_STATE_DISAGREEMENT]
          and {k: v for k, v in r.status()["exclusions_by_reason"].items() if v}
              == {EL.J_MARKER_STATE_DISAGREEMENT: 1}, str(refusal_codes(r)))

    # And on the provenance echo.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    mp = marker_path(r.markers, eid, STAGE_PRE_EVENT)
    tampered = json.loads(mp.read_text(encoding="utf-8"))
    tampered["provenance"]["source_csv_sha256"] = "c" * 64
    mp.write_text(json.dumps(tampered), encoding="utf-8")
    check("B6c. a PRE_EVENT marker whose provenance echo was edited refuses",
          refusal_codes(r) == [EL.J_MARKER_STATE_DISAGREEMENT]
          and {k: v for k, v in r.status()["exclusions_by_reason"].items() if v}
              == {EL.J_MARKER_STATE_DISAGREEMENT: 1}, str(refusal_codes(r)))

    # PARTIAL D1 (incomplete decomposition) is not D1_COMPLETE.
    r = Roots()
    build_event(r, "DELL", "FY27Q2", date(2026, 8, 3),
                d1=d1_fields(open_to_30m=None))
    check("B7. a PARTIAL D1 stage is not accepted as D1 evidence",
          refusal_codes(r) == [EL.J_MISSING_D1_STATE], str(refusal_codes(r)))

    # No event-store log at all.
    r = Roots()
    register(r, "DELL", "FY27Q2", date(2026, 8, 3))
    check("B8. an enrolled event with no event-store log refuses",
          refusal_codes(r) == [EL.J_MISSING_EVENT_STORE_LOG], str(refusal_codes(r)))

    print("\n=== C. D1 response-window identity ===")

    # Wrong plan: a plan built for a DIFFERENT event, filed under this event's
    # deterministic name.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3), with_plan=False)
    other = build_event(r, "MSFT", "FY27Q3", date(2026, 8, 10), with_plan=False)
    other_plan = finalize_plan(build_operations_plan(
        registry_path=r.registry / "registry.jsonl", event_id=other,
        company_name="Other Co",
        generated_at_utc=datetime(2026, 7, 2, tzinfo=timezone.utc),
        planning_commit="0" * 40, methodology_version="market_response_v0.2"))
    (r.plans / A.PLAN_FILENAME.format(event_id=eid)).write_text(
        json.dumps(other_plan), encoding="utf-8")
    write_plan(r, other)
    check("C1. an operations plan describing another event refuses",
          EL.J_OPERATIONS_PLAN_MISMATCH in refusal_codes(r), str(refusal_codes(r)))

    # Plan integrity: edit a plan after finalize_plan().
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    pp = r.plans / A.PLAN_FILENAME.format(event_id=eid)
    plan = json.loads(pp.read_text(encoding="utf-8"))
    plan["sessions"]["D1"]["session_date"] = "2026-08-05"
    pp.write_text(json.dumps(plan), encoding="utf-8")
    check("C2. a plan edited after finalisation fails its own digest",
          refusal_codes(r) == [EL.J_OPERATIONS_PLAN_INTEGRITY], str(refusal_codes(r)))

    # Wrong response-session date, with the digest recomputed so ONLY the
    # session date is wrong -- the case Defect 2 named.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    pp = r.plans / A.PLAN_FILENAME.format(event_id=eid)
    plan = json.loads(pp.read_text(encoding="utf-8"))
    plan["sessions"]["D1"]["session_date"] = "2026-08-05"
    plan.pop("integrity", None)
    pp.write_text(json.dumps(finalize_plan(plan)), encoding="utf-8")
    check("C3. a D1 plan session that is not the registered response session refuses",
          refusal_codes(r) == [EL.J_D1_SESSION_MISMATCH], str(refusal_codes(r)))

    # Superseded timing: amend the earnings date AFTER the capture and plan
    # were made for the original one.
    r = Roots()
    row = register(r, "DELL", "FY27Q2", date(2026, 8, 3))
    eid = row.event_id
    pipeline.register_event(r.es, eid, {"ticker": "DELL"})
    pipeline.capture_pre_event_and_option_benchmark_v0_2(
        r.es, eid, core_fields(), dict(OPTION_UNAVAILABLE))
    write_stage_marker(r.markers, eid, STAGE_PRE_EVENT, r.es)
    pipeline.capture_d1(r.es, eid, d1_fields())
    write_stage_marker(r.markers, eid, STAGE_D1, r.es)
    write_plan(r, eid)                      # plan for the ORIGINAL timing
    r.reg.amend_event(amends_row_id=row.row_id,
                      corrected_fields={"earnings_date": "2026-08-10",
                                        "earnings_datetime_utc":
                                            _amc_datetime(date(2026, 8, 10)).isoformat()},
                      verified_at_utc=datetime(2026, 8, 5, tzinfo=timezone.utc),
                      verified_by="synthetic-operator", notes="corrected date")
    # An amendment that moves registered timing necessarily changes a field the
    # plan echoes (earnings_date), so OPERATIONS_PLAN_MISMATCH fires before the
    # session-date comparison. Both codes are structural superseded-timing
    # refusals; C3 exercises the session-date code in isolation.
    got = refusal_codes(r)
    check("C4. an amendment moving registered timing invalidates the superseded capture",
          len(got) == 1 and got[0] in (EL.J_OPERATIONS_PLAN_MISMATCH,
                                       EL.J_D1_SESSION_MISMATCH), str(got))
    check("C4b. the superseded capture is refused structurally, never counted",
          r.status()["eligible_event_count"] == 0
          and r.status()["exclusions_by_reason"].get(got[0]) == 1)

    # Capture BEFORE the permitted window: a far-future response session means
    # earliest_provider_retrieval_utc has not yet arrived.
    r = Roots()
    future = date(2027, 6, 2)
    build_event(r, "DELL", "FY28Q2", future)
    check("C5. a D1 capture before the plan's earliest permitted retrieval refuses",
          refusal_codes(r) == [EL.J_CAPTURE_BEFORE_PERMITTED_WINDOW],
          str(refusal_codes(r)))

    # A nonblank but invalid capture timestamp must refuse -- presence alone is
    # not enough. Exercised on the production parser and the window validator.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    plan = json.loads((r.plans / A.PLAN_FILENAME.format(event_id=eid))
                      .read_text(encoding="utf-8"))
    effective = r.reg.effective_row(eid)
    for bad in ("not-a-timestamp", "2026-13-45T99:99:99Z", "  ", "20260803"):
        try:
            A.validate_d1_response_window(effective, plan,
                                          {"written_at_utc": bad, "state": "D1_COMPLETE"})
            ok, code = False, "accepted"
        except EL.JoinRefusal as e:
            ok, code = e.code == EL.J_MALFORMED_CAPTURE_TIMESTAMP, e.code
        check(f"C6. nonblank but invalid capture timestamp {bad!r} refuses", ok, code)

    try:
        A._parse_utc("2026-08-04T21:00:00", "E", "naive")
        ok, code = False, "accepted"
    except EL.JoinRefusal as e:
        ok, code = e.code == EL.J_MALFORMED_CAPTURE_TIMESTAMP, e.code
    check("C7. a timezone-naive capture timestamp refuses rather than assuming UTC",
          ok, code)

    # Stale registry timing: expected_response_session that no longer recomputes.
    r = Roots()
    eid = build_event(r, "DELL", "FY27Q2", date(2026, 8, 3))
    effective = dict(r.reg.effective_row(eid))
    effective["expected_response_session"] = "2026-08-06"
    plan = json.loads((r.plans / A.PLAN_FILENAME.format(event_id=eid))
                      .read_text(encoding="utf-8"))
    try:
        A.validate_d1_response_window(effective, plan,
                                      {"written_at_utc": "2026-08-05T00:00:00+00:00",
                                       "state": "D1_COMPLETE"})
        ok, code = False, "accepted"
    except EL.JoinRefusal as e:
        ok, code = e.code == EL.J_REGISTRY_TIMING_STALE, e.code
    check("C8. a registry response session that no longer recomputes refuses", ok, code)

    check("C9. the missing upper bound is declared, not invented",
          "SPECIFICATION GAP" in A.validate_d1_response_window.__doc__
          and "upper bound" in A.validate_d1_response_window.__doc__)

    print("\n=== D. cohort arithmetic through the canonical adapter ===")

    def cohort(n):
        r = Roots()
        base = date(2026, 3, 2)
        for i in range(n):
            t = TICKERS[i % len(TICKERS)]
            fy = f"FY27Q{(i // len(TICKERS)) + 1}"
            d = base + timedelta(days=i)
            while not is_trading_day(d):
                d = d + timedelta(days=1)
            build_event(r, t, fy, d)
        return r

    r59 = cohort(59)
    s59 = r59.status()
    check("D1. 59 canonical events do not trigger the freeze",
          s59["eligible_event_count"] == 59 and s59["freeze_required"] is False
          and s59["counting_state"] == "COUNTING",
          json.dumps({k: v for k, v in s59["exclusions_by_reason"].items() if v}))

    r60 = cohort(60)
    s60 = r60.status()
    check("D2. the 60th canonical event triggers the freeze exactly once",
          s60["eligible_event_count"] == 60 and s60["freeze_required"] is True
          and s60["counting_state"] == "REFUSED_AT_GATE",
          json.dumps({k: v for k, v in s60["exclusions_by_reason"].items() if v}))
    check("D3. the driver never authorizes analysis at the gate",
          s60["analysis_authorized"] is False)

    r63 = cohort(63)
    s63 = r63.status()
    check("D4. beyond 60 the frozen set stays at 60 and the surplus is EXTENSION_COHORT",
          s63["eligible_event_count"] == 60
          and s63["exclusions_by_reason"]["EXTENSION_COHORT"] == 3,
          json.dumps({k: v for k, v in s63["exclusions_by_reason"].items() if v}))
    check("D5. each event is counted exactly once",
          len(set(s63["eligible_event_ids"])) == 60
          and sum(s63["exclusions_by_reason"].values())
          + s63["eligible_event_count"] == s63["effective_events_seen"])

    again = r63.status()
    check("D6. reruns over unchanged canonical roots are byte-identical",
          EL.status_digest(again) == EL.status_digest(s63))

    print("\n=== E. non-disclosure ===")

    blob = json.dumps(s63)
    leaked = [k for k, v in SENT.items() if str(v) in blob]
    check("E1. no sentinel measurement value reaches the status document",
          not leaked, f"leaked: {leaked}")
    keyed = [k for k in SENT if k in blob]
    check("E2. no measurement field name reaches the status document",
          not keyed, f"present: {keyed}")
    check("E3. abs_overnight_gap never appears in the status document",
          "abs_overnight_gap" not in blob)
    check("E4. the specification gap is disclosed in the status document",
          any("SPECIFICATION GAP" in n for n in s63["notes"]))

    print(f"\n{CHECKS} checks run")
    if FAILURES:
        print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL HYP-01 CANONICAL ADAPTER CHECKS PASSED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
