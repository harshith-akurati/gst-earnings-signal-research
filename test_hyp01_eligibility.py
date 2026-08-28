#!/usr/bin/env python3
"""Offline synthetic end-to-end tests for the HYP-01 join and counting driver.

Every fixture is built in memory from sentinel values. No project file is read,
no real prospective record is opened, and a socket guard fails the run on any
connection attempt.

The suite asserts four properties:

  A. JOIN INTEGRITY -- exact registered keys only; duplicates, missing legs,
     key mismatches, unknown columns and undated captures all REFUSE.
  B. LADDER CORRECTNESS -- each of the eight steps produces its own registered
     disposition, and enrollment is never inferred.
  C. GATE ARITHMETIC -- the 59 -> 60 transition flips freeze_required exactly
     once, and counting REFUSES beyond 60 rather than growing the cohort.
  D. NON-DISCLOSURE -- no measurement value reaches the status document.
"""
from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path


class _Blocked(socket.socket):
    def connect(self, *a, **k):
        raise AssertionError("network access attempted; this suite is offline")

    def connect_ex(self, *a, **k):
        raise AssertionError("network access attempted; this suite is offline")


socket.socket = _Blocked
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
    AssertionError("network access attempted; this suite is offline"))

_spec = importlib.util.spec_from_file_location(
    "hyp01_eligibility",
    Path(__file__).resolve().parent / "tools" / "hyp01_eligibility.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)

FAILURES: list[str] = []
CHECKS = 0


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

# Sentinel measurements. If any of these values or field names appears in a
# status document, non-disclosure has failed.
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


def _edate(i):
    return f"2026-09-{(i % 28) + 1:02d}"


def _rdate(i):
    return f"2026-09-{(i % 28) + 2:02d}"


def reg(i, *, status="verified", row_type="event", hclass=None, **over):
    r = {"event_id": f"EVT{i:04d}", "ticker": f"TK{i:03d}",
         "earnings_date": _edate(i),
         "verification_status": status, "row_type": row_type}
    if hclass is not None:
        r["hypothesis_class"] = hclass
    r.update(over)
    return _drop_absent(r)


def gst(i, **over):
    leg = {"event_id": f"EVT{i:04d}", "ticker": f"TK{i:03d}",
           "earnings_date": _edate(i),
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


def d1(i, *, session="AMC", **over):
    leg = {"event_id": f"EVT{i:04d}", "ticker": f"TK{i:03d}",
           "earnings_date": _edate(i),
           "release_market_session": session,
           "response_session_date": _rdate(i),
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


def one(registration, gst_leg, d1_leg):
    """Run the driver on a single-event cohort and return its status doc."""
    return E.run_driver([registration],
                        [gst_leg] if gst_leg else [],
                        [d1_leg] if d1_leg else [])


def sole_reason(status):
    hits = [k for k, v in status["exclusions_by_reason"].items() if v]
    return hits[0] if len(hits) == 1 else f"<{len(hits)} reasons: {hits}>"


def cohort(n):
    return ([reg(i) for i in range(n)],
            [gst(i) for i in range(n)],
            [d1(i) for i in range(n)])


def main() -> int:
    print("=== A. join integrity ===")

    s = one(reg(1), gst(1), d1(1))
    check("A1. a complete, enrolled, gate-passing event counts once",
          s["eligible_event_count"] == 1 and s["eligible_event_ids"] == ["EVT0001"],
          json.dumps(s["exclusions_by_reason"]))

    s = one(reg(1), None, d1(1))
    check("A2. a missing GST leg refuses, and counts nothing",
          s["eligible_event_count"] == 0
          and sole_reason(s) == E.J_MISSING_GST_LEG, sole_reason(s))

    s = one(reg(1), gst(1), None)
    check("A3. a missing D1 leg refuses, and counts nothing",
          s["eligible_event_count"] == 0
          and sole_reason(s) == E.J_MISSING_D1_LEG, sole_reason(s))

    try:
        E.run_driver([reg(1), reg(1)], [gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_EVENT
    check("A4. a duplicated registry event raises, never silently dedupes", ok)

    try:
        E.run_driver([reg(1)], [gst(1), gst(1)], [d1(1)])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_LEG
    check("A5. two GST legs for one event raises, never picks one", ok)

    s = one(reg(1), gst(1, ticker="WRONG"), d1(1))
    check("A6. a ticker that differs across legs refuses; no fuzzy match",
          sole_reason(s) == E.J_KEY_MISMATCH, sole_reason(s))

    s = one(reg(1), gst(1, earnings_date="2026-09-03"), d1(1))
    check("A7. a near-miss earnings date refuses; no nearest-date match",
          sole_reason(s) == E.J_KEY_MISMATCH, sole_reason(s))

    s = one(reg(1), gst(1, surprise_column=1), d1(1))
    check("A8. an unknown GST column refuses rather than being ignored",
          sole_reason(s) == E.J_UNEXPECTED_FIELD, sole_reason(s))

    s = one(reg(1), gst(1), d1(1, sneaky_alpha=1))
    check("A9. an unknown D1 column refuses rather than being ignored",
          sole_reason(s) == E.J_UNEXPECTED_FIELD, sole_reason(s))

    s = one(reg(1), gst(1, captured_at_utc=_DROP), d1(1))
    check("A10. an undated capture refuses",
          sole_reason(s) == E.J_NO_CAPTURE_TIME, sole_reason(s))

    print("\n=== B. ladder correctness ===")

    s = one(reg(1, status="pending"), gst(1), d1(1))
    check("B1. step 1 -- an unverified event is NOT_ENROLLED even with full data",
          sole_reason(s) == E.R_NOT_ENROLLED and s["eligible_event_count"] == 0,
          sole_reason(s))

    s = one(reg(1, row_type="amendment"), gst(1), d1(1))
    check("B2. step 1 -- a non-event registry row is NOT_ENROLLED",
          sole_reason(s) == E.R_NOT_ENROLLED, sole_reason(s))

    s = one(reg(1, hclass="options_implied_move"), gst(1), d1(1))
    check("B3. step 2 -- another hypothesis family is CLASS_INELIGIBLE",
          sole_reason(s) == E.R_CLASS_INELIGIBLE, sole_reason(s))

    s = one(reg(1), gst(1, wiki_zscore=_DROP), d1(1))
    check("B4. step 3 -- a missing sixth panel field is CORE_GATE_FAILED",
          sole_reason(s) == E.R_CORE_GATE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1, source_status_iv="error"), d1(1))
    check("B5. step 3 -- a failed IV leg is CORE_GATE_FAILED, not inherited from price",
          sole_reason(s) == E.R_CORE_GATE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1), d1(1, open_to_30m=_DROP))
    check("B6. step 4 -- an incomplete D1 decomposition is D1_GATE_FAILED",
          sole_reason(s) == E.R_D1_GATE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1, provenance_sha256="short"), d1(1))
    check("B7. step 5 -- a malformed GST digest is GST_PROVENANCE_FAILED",
          sole_reason(s) == E.R_GST_PROVENANCE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1), d1(1, abs_overnight_gap=_DROP))
    check("B8. step 6 -- an absent primary outcome is OUTCOME_MISSING",
          sole_reason(s) == E.R_OUTCOME_MISSING, sole_reason(s))

    s = one(reg(1), gst(1), d1(1, market_data_provenance_valid=False))
    check("B9. step 6 -- an unverified market-data provenance is OUTCOME_MISSING",
          sole_reason(s) == E.R_OUTCOME_MISSING, sole_reason(s))

    s_intraday = one(reg(1), gst(1), d1(1, session="INTRADAY"))
    check("B10. step 7 -- an intraday release is MEASUREMENT_INCOMPATIBLE_INTRADAY",
          sole_reason(s_intraday) == E.R_MEASUREMENT_INCOMPATIBLE_INTRADAY,
          sole_reason(s_intraday))

    check("B11. every emitted reason is a registered code",
          all(r in E.REASONS or r in E.JOIN_REFUSALS
              for r in s_intraday["exclusions_by_reason"]),
          str([r for r in s_intraday["exclusions_by_reason"]
               if r not in E.REASONS and r not in E.JOIN_REFUSALS]))

    s = one(reg(1), gst(1), d1(1, session="BMO"))
    check("B12. step 7 -- BMO is an accepted session",
          s["eligible_event_count"] == 1, sole_reason(s))

    print("\n=== C. gate arithmetic ===")

    s59 = E.run_driver(*cohort(59))
    check("C1. 59 eligible events do not trigger the freeze",
          s59["eligible_event_count"] == 59
          and s59["freeze_required"] is False
          and s59["counting_state"] == "COUNTING",
          json.dumps(s59["exclusions_by_reason"]))
    check("C2. remaining_until_target is 1 at 59",
          s59["remaining_until_target"] == 1, str(s59["remaining_until_target"]))

    s60 = E.run_driver(*cohort(60))
    check("C3. the 60th eligible event triggers the freeze exactly once",
          s60["eligible_event_count"] == 60
          and s60["freeze_required"] is True
          and s60["counting_state"] == "REFUSED_AT_GATE")
    check("C4. remaining_until_target is 0 at the gate, never negative",
          s60["remaining_until_target"] == 0)

    s75 = E.run_driver(*cohort(75))
    check("C5. beyond 60 the frozen set stays at 60, it does not grow",
          s75["eligible_event_count"] == 60
          and len(s75["eligible_event_ids"]) == 60,
          str(s75["eligible_event_count"]))
    check("C6. the surplus 15 are EXTENSION_COHORT, not eligible",
          s75["exclusions_by_reason"]["EXTENSION_COHORT"] == 15
          and len(s75["extension_cohort_event_ids"]) == 15,
          str(s75["exclusions_by_reason"]["EXTENSION_COHORT"]))
    check("C7. counting still REFUSES beyond the gate",
          s75["counting_state"] == "REFUSED_AT_GATE"
          and s75["remaining_until_target"] == 0)

    ids = s75["eligible_event_ids"]
    check("C8. the frozen 60 are the section-2 order, not arrival order",
          ids == sorted(ids, key=lambda e: (_rdate(int(e[3:])), e)))
    check("C9. the driver never authorizes the analysis, even at the gate",
          s60["analysis_authorized"] is False and s75["analysis_authorized"] is False)
    check("C10. eligible + all exclusions == registry rows seen",
          sum(s75["exclusions_by_reason"].values()) + s75["eligible_event_count"]
          == s75["registry_rows_seen"])

    print("\n=== D. non-disclosure and determinism ===")

    blob = json.dumps(s75)
    leaked = [k for k, v in SENTINELS.items() if str(v) in blob]
    check("D1. no sentinel measurement value reaches the status document",
          not leaked, f"leaked: {leaked}")
    keyed = [k for k in SENTINELS if k in blob]
    check("D2. no measurement field name reaches the status document",
          not keyed, f"present: {keyed}")

    check("D3. repeated runs are byte-identical",
          E.status_digest(E.run_driver(*cohort(75))) == E.status_digest(s75))

    regs, gs, ds = cohort(30)
    shuffled = E.run_driver(list(reversed(regs)), list(reversed(gs)), list(reversed(ds)))
    check("D4. input ordering does not change the result",
          E.status_digest(shuffled) == E.status_digest(E.run_driver(regs, gs, ds)))

    check("D5. the status document is self-describing",
          s75["schema"] == "GST_HYP01_ELIGIBILITY_STATUS_v1"
          and s75["binding_target"] == 60)

    print("\n=== E. first-failure precedence under the registered order ===")

    # The registered sequence is S-1..S-8 (eligibility rules section 1 table, and
    # identically the analysis lock /sample/inclusion_conditions[0..7]). An event
    # failing several gates must receive the code of the FIRST one it fails.
    # These fixtures each break two or more gates at once and assert the earlier
    # code wins -- which is exactly what a reordered implementation would break.

    # -- the two leg-absence cases named in the correction request -------------
    s = one(reg(1), None, d1(1, session="INTRADAY"))
    check("E1. timing + missing GST leg -> MISSING_GST_LEG, not the timing code",
          sole_reason(s) == E.J_MISSING_GST_LEG, sole_reason(s))

    s = one(reg(1), gst(1), None)
    check("E2. timing + missing D1 leg -> MISSING_D1_LEG (session is unknowable "
          "without the D1 leg that carries it)",
          sole_reason(s) == E.J_MISSING_D1_LEG, sole_reason(s))

    # -- provenance vs completeness ------------------------------------------
    s = one(reg(1), gst(1, provenance_sha256="short"), d1(1, open_to_30m=_DROP))
    check("E3. S-4 completeness + S-5 provenance -> D1_GATE_FAILED",
          sole_reason(s) == E.R_D1_GATE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1, wiki_zscore=_DROP, provenance_sha256="short"), d1(1))
    check("E4. S-3 core completeness + S-5 provenance -> CORE_GATE_FAILED",
          sole_reason(s) == E.R_CORE_GATE_FAILED, sole_reason(s))

    # -- duplicates outrank everything ---------------------------------------
    try:
        E.run_driver([reg(1, status="pending"), reg(1)],
                     [gst(1, wiki_zscore=_DROP)], [d1(1, session="INTRADAY")])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_EVENT
    check("E5. duplicate event + three other failures -> DUPLICATE_EVENT raises", ok)

    try:
        E.run_driver([reg(1)], [gst(1), gst(1, wiki_zscore=_DROP)],
                     [d1(1, session="INTRADAY")])
        ok = False
    except E.JoinRefusal as e:
        ok = e.code == E.J_DUPLICATE_LEG
    check("E6. duplicate leg + other failures -> DUPLICATE_LEG raises", ok)

    # -- every adjacent pair of ordered gates where simultaneous failure is
    #    possible. Each fixture breaks gate N and gate N+1; gate N must win.
    s = one(reg(1, status="pending", hclass="options_implied_move"), gst(1), d1(1))
    check("E7. S-1 + S-2 -> NOT_ENROLLED", sole_reason(s) == E.R_NOT_ENROLLED,
          sole_reason(s))

    s = one(reg(1, hclass="options_implied_move"), gst(1, wiki_zscore=_DROP), d1(1))
    check("E8. S-2 + S-3 -> CLASS_INELIGIBLE", sole_reason(s) == E.R_CLASS_INELIGIBLE,
          sole_reason(s))

    s = one(reg(1), gst(1, wiki_zscore=_DROP), d1(1, open_to_30m=_DROP))
    check("E9. S-3 + S-4 -> CORE_GATE_FAILED", sole_reason(s) == E.R_CORE_GATE_FAILED,
          sole_reason(s))

    # S-5 broken via the provenance digest, which S-3 does not read -- so this
    # isolates the S-4/S-5 boundary instead of also tripping S-3.
    s = one(reg(1), gst(1, provenance_sha256="short"), d1(1, thirty_min_to_close=_DROP))
    check("E10. S-4 + S-5 -> D1_GATE_FAILED", sole_reason(s) == E.R_D1_GATE_FAILED,
          sole_reason(s))

    s = one(reg(1), gst(1, provenance_sha256="short"), d1(1, abs_overnight_gap=_DROP))
    check("E11. S-5 + S-6 -> GST_PROVENANCE_FAILED",
          sole_reason(s) == E.R_GST_PROVENANCE_FAILED, sole_reason(s))

    s = one(reg(1), gst(1), d1(1, abs_overnight_gap=_DROP, session="INTRADAY"))
    check("E12. S-6 + S-7 -> OUTCOME_MISSING (the case the previous "
          "implementation mislabelled)",
          sole_reason(s) == E.R_OUTCOME_MISSING, sole_reason(s))

    # S-7 + S-8: 60 valid events already fill the cohort, so an additional
    # eligible event would rank 61 and be EXTENSION_COHORT. Being INTRADAY, it
    # must fail S-7 first instead.
    regs, gs, ds = cohort(60)
    regs.append(reg(90))
    gs.append(gst(90))
    ds.append(d1(90, session="INTRADAY"))
    s = E.run_driver(regs, gs, ds)
    check("E13. S-7 + S-8 -> MEASUREMENT_INCOMPATIBLE_INTRADAY, not EXTENSION_COHORT",
          s["exclusions_by_reason"]["MEASUREMENT_INCOMPATIBLE_INTRADAY"] == 1
          and s["exclusions_by_reason"]["EXTENSION_COHORT"] == 0
          and s["eligible_event_count"] == 60,
          json.dumps({k: v for k, v in s["exclusions_by_reason"].items() if v}))

    # -- an event failing every gate at once gets the first code ---------------
    s = one(reg(1, status="pending", hclass="options_implied_move"),
            gst(1, wiki_zscore=_DROP, provenance_sha256="short"),
            d1(1, open_to_30m=_DROP, abs_overnight_gap=_DROP, session="INTRADAY"))
    check("E14. an event failing every gate receives the S-1 code",
          sole_reason(s) == E.R_NOT_ENROLLED, sole_reason(s))

    # -- the declared order matches actual behaviour, gate by gate ------------
    # Each fixture breaks exactly one gate; the observed sequence of codes must
    # equal REGISTERED_GATE_ORDER. This proves the constant describes the code
    # rather than merely sitting beside it.
    single = [
        one(reg(1, status="pending"), gst(1), d1(1)),
        one(reg(1, hclass="options_implied_move"), gst(1), d1(1)),
        one(reg(1), gst(1, wiki_zscore=_DROP), d1(1)),
        one(reg(1), gst(1), d1(1, open_to_30m=_DROP)),
        one(reg(1), gst(1, provenance_sha256="short"), d1(1)),
        one(reg(1), gst(1), d1(1, abs_overnight_gap=_DROP)),
        one(reg(1), gst(1), d1(1, session="INTRADAY")),
    ]
    observed = tuple(sole_reason(x) for x in single)
    expected = tuple(code for _, code in E.REGISTERED_GATE_ORDER[:7])
    check("E15. observed first-failure codes match the declared S-1..S-7 order",
          observed == expected, f"{observed} != {expected}")

    s75x = E.run_driver(*cohort(75))
    check("E16. S-8 is the EXTENSION_COHORT gate, applied by the driver",
          E.REGISTERED_GATE_ORDER[7] == ("S-8", E.R_EXTENSION_COHORT)
          and s75x["exclusions_by_reason"]["EXTENSION_COHORT"] == 15)

    print("\n=== F. provenance guarantees ===")

    # The design evaluates provenance on the ladder (S-5/S-6) rather than inside
    # the join. That is permissible only if a provenance failure can never reach
    # the cohort by any route. Each property is asserted separately.

    bad_gst = one(reg(1), gst(1, provenance_sha256="short"), d1(1))
    bad_gst_absent = one(reg(1), gst(1, provenance_path=_DROP), d1(1))
    bad_d1 = one(reg(1), gst(1), d1(1, provenance_sha256="not-a-digest"))

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
          and sole_reason(bad_gst_absent) == E.R_GST_PROVENANCE_FAILED,
          f"{sole_reason(bad_gst)} / {sole_reason(bad_gst_absent)}")
    check("F5. GST_PROVENANCE_FAILED is reachable through the full driver",
          bad_gst["exclusions_by_reason"][E.R_GST_PROVENANCE_FAILED] == 1)

    # 59 valid events plus one whose provenance fails must NOT trigger the freeze.
    regs, gs, ds = cohort(59)
    regs.append(reg(91))
    gs.append(gst(91, provenance_sha256="short"))
    ds.append(d1(91))
    mixed = E.run_driver(regs, gs, ds)
    check("F6. a provenance failure cannot contribute to the event-60 freeze",
          mixed["eligible_event_count"] == 59
          and mixed["freeze_required"] is False
          and mixed["counting_state"] == "COUNTING"
          and mixed["remaining_until_target"] == 1,
          json.dumps({k: v for k, v in mixed["exclusions_by_reason"].items() if v}))
    check("F7. no unregistered failure code is emitted anywhere in a mixed cohort",
          all(r in E.REASONS or r in E.JOIN_REFUSALS
              for r in mixed["exclusions_by_reason"]),
          str([r for r in mixed["exclusions_by_reason"]
               if r not in E.REASONS and r not in E.JOIN_REFUSALS]))

    # The join must not be able to bless an event on its own. Its output carries
    # identity and provenance only -- no eligibility designation of any kind.
    joined = E.join_event(reg(1), gst(1, provenance_sha256="short"), d1(1))
    check("F8. join output carries no eligibility designation to bypass the ladder",
          not any(k in joined for k in
                  ("eligible", "is_eligible", "eligibility", "passed", "status")),
          str(sorted(joined)))
    ok, why = E.classify(reg(1), joined, None)
    check("F9. a cleanly-joined but provenance-failed event is refused by the ladder",
          ok is False and why == E.R_GST_PROVENANCE_FAILED, f"{ok} {why}")

    # Only classify() may admit an event: an event that joins perfectly but fails
    # a later gate must never appear in the cohort.
    joinable_but_failing = E.run_driver(
        [reg(1)], [gst(1)], [d1(1, market_data_provenance_valid=False)])
    check("F10. a perfectly joinable event failing a ladder gate never enters the cohort",
          joinable_but_failing["eligible_event_ids"] == []
          and sole_reason(joinable_but_failing) == E.R_OUTCOME_MISSING,
          sole_reason(joinable_but_failing))

    print(f"\n{CHECKS} checks run")
    if FAILURES:
        print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nALL HYP-01 ELIGIBILITY JOIN + DRIVER CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
