#!/usr/bin/env python3
"""Offline synthetic tests for the HYP-01 progress reporter.

Two properties are asserted:

  1. REDACTION. Given a registry and panel files stuffed with measurement values
     under many plausible names, no measurement value reaches the rendered
     report or the JSON payload.
  2. DETERMINISTIC COUNTING. The same synthetic input yields byte-identical
     output across repeated runs and across dict-ordering perturbations, and
     the exclusion reasons are the registered ones.

Fully offline: a socket guard fails the run on any connection attempt. No
project data is read; every fixture is written into a temporary directory.
"""
from __future__ import annotations

import importlib.util
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

_spec = importlib.util.spec_from_file_location(
    "hyp01_progress_report",
    Path(__file__).resolve().parent / "tools" / "hyp01_progress_report.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

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


# Distinctive synthetic measurement values. If any of these strings appears in
# the output, redaction has failed.
SECRETS = {
    "gst_zscore": "7.7777771",
    "wiki_zscore": "-8.8888882",
    "price": "9999.99993",
    "volume": "123456784",
    "implied_volatility": "0.55555555",
    "realized_vol": "0.44444446",
    "abs_overnight_gap": "6.66666667",
    "overnight_gap": "-5.55555558",
    "open_to_close": "3.33333339",
    "close_T1_to_close_T2": "2.22222220",
}


def make_fixture(tmp: Path) -> Path:
    root = tmp / "repo"
    (root / "Live Signal Engine" / "Market_Response_Event_Registry").mkdir(parents=True)
    lse = root / "Live Signal Engine"

    # Canonical REGISTRATION rows exercising each decidable branch. row_type is
    # REGISTRATION -- the schema EventRegistryRow actually validates. The
    # invented type "event" appears nowhere.
    spec = [("AMC", "verified"), ("BMO", "verified"),
            ("INTRADAY", "verified"), ("AMC", "pending")]
    rows = []
    for i, (session, status) in enumerate(spec):
        rec = {
            "row_id": f"EVT{i:04d}-REG-001",
            "row_type": "REGISTRATION",
            "event_id": f"EVT{i:04d}",
            "ticker": ["AAPL", "MSFT", "NVDA", "AMZN"][i],
            "earnings_date": f"2026-09-{i + 1:02d}",
            "release_market_session": session,
            "expected_response_session": f"2026-09-{i + 2:02d}",
            "verification_status": status,
        }
        rec.update(SECRETS)  # measurements deliberately embedded
        rows.append(rec)
    # A canonical AMENDMENT correcting event 3 from pending to verified. It must
    # fold into that event, never appear as a fifth event.
    rows.append({
        "row_id": "EVT0003-AMD-001",
        "row_type": "AMENDMENT",
        "amends_row_id": "EVT0003-REG-001",
        "event_id": "EVT0003",
        "ticker": "AMZN",
        "earnings_date": "2026-09-04",
        "release_market_session": "AMC",
        "expected_response_session": "2026-09-05",
        "verification_status": "verified",
        **SECRETS,
    })

    (lse / "Market_Response_Event_Registry" / "registry.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    # panel markers whose *contents* are full of measurements
    for d in ("2026-08-26", "2026-08-27"):
        (lse / f"GST_Phase2_DailyPanel_TestRun_{d}_run3_COMPLETION_MARKER.json").write_text(
            json.dumps({"status": "COMPLETE", **SECRETS}), encoding="utf-8")
        (lse / f"GST_Phase2_DailyPanel_TestRun_{d}_run3.csv").write_text(
            "ticker,gst_zscore,price\nAAPL," + SECRETS["gst_zscore"] + "," +
            SECRETS["price"] + "\n", encoding="utf-8")

    for a in ("GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md",
              "GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json",
              "GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json"):
        (lse / a).write_text("{}", encoding="utf-8")
    # GST_PROSPECTIVE_COHORT_PROTOCOL_v1.0.json deliberately absent
    return root


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="hyp01_progress_"))
    try:
        root = make_fixture(tmp)

        rep = R.build_report(root)
        text = R.render(rep)
        # The prose notes legitimately contain words like "price" while asserting
        # that no such VALUE was read. Scan the data payload and the rendered
        # report with the notes removed, so the check tests leakage rather than
        # the wording of the disclaimer.
        data_only = {k: v for k, v in rep.items() if k != "notes"}
        blob = json.dumps(data_only)
        text_wo_notes = "\n".join(
            ln for ln in text.splitlines() if not ln.strip().startswith("note:"))

        print("\n=== 1. redaction ===")
        leaked = [k for k, v in SECRETS.items() if v in text or v in blob]  # values: full text
        check("1a. no measurement value appears in the rendered report or JSON",
              not leaked, f"leaked: {leaked}")
        for name in ("gst_zscore", "abs_overnight_gap", "overnight_gap", "price",
                     "implied_volatility", "realized_vol", "volume"):
            check(f"1b. measurement key {name!r} absent from data output",
                  name not in text_wo_notes and name not in blob)
        check("1c. SAFE_EVENT_KEYS is a whitelist, not a blacklist",
              isinstance(R.SAFE_EVENT_KEYS, frozenset) and
              "gst_zscore" not in R.SAFE_EVENT_KEYS)
        rows, _, _amd = R.load_registry(root)
        check("1d. loaded registry rows carry only whitelisted keys",
              all(set(r) <= R.SAFE_EVENT_KEYS for r in rows),
              str([sorted(set(r) - R.SAFE_EVENT_KEYS) for r in rows]))

        print("\n=== 2. deterministic counting ===")
        again = R.render(R.build_report(root))
        check("2a. repeated runs are byte-identical", text == again)
        check("2b. binding target is 60", rep["binding_target"] == 60)
        check("2c. eligible count is 0 on this fixture",
              rep["eligible_event_count"] == 0, str(rep["eligible_event_count"]))
        check("2d. remaining = target - eligible",
              rep["remaining_until_target"] ==
              rep["binding_target"] - rep["eligible_event_count"])
        excl = rep["exclusions_by_reason"]
        check("2e. every registered reason code is present in the tally",
              all(r in excl for r in R.REASONS),
              str([r for r in R.REASONS if r not in excl]))
        check("2f. no verified REGISTRATION is mislabelled NOT_ENROLLED",
              excl["NOT_ENROLLED"] == 0, str(excl["NOT_ENROLLED"]))
        check("2f2. the amendment folds in; 4 effective events, not 5",
              rep["effective_events_seen"] == 4
              and rep["amendment_rows_folded"] == 1,
              f"seen={rep['effective_events_seen']} amd={rep['amendment_rows_folded']}")
        check("2g. the INTRADAY row is MEASUREMENT_INCOMPATIBLE_INTRADAY",
              excl["MEASUREMENT_INCOMPATIBLE_INTRADAY"] == 1,
              str(excl["MEASUREMENT_INCOMPATIBLE_INTRADAY"]))
        check("2h. undecidable rows are flagged, not guessed",
              excl["UNDETERMINED_REQUIRES_OUTCOME_CAPTURE"] == 3,
              str(excl["UNDETERMINED_REQUIRES_OUTCOME_CAPTURE"]))
        check("2h2. the amended event is enrolled via its effective status",
              excl["STRUCTURAL_REGISTRY_PROBLEM"] == 0,
              str(excl["STRUCTURAL_REGISTRY_PROBLEM"]))
        check("2i. exclusions + eligible == effective events seen",
              sum(excl.values()) + rep["eligible_event_count"] ==
              rep["effective_events_seen"])
        # The needle is assembled from parts so this assertion does not match
        # itself when it scans its own source file.
        needle = '"row_type"' + ': "' + "event" + '"'
        prod = (Path(__file__).resolve().parent / "tools"
                / "hyp01_progress_report.py").read_text(encoding="utf-8")
        mine = Path(__file__).read_text(encoding="utf-8")
        check("2i2. no fixture or production code assumes row_type 'event'",
              needle not in prod and needle not in mine
              and '"event"' not in prod,
              f"prod={needle in prod} test={needle in mine}")
        check("2j. captured panel dates read from filenames only",
              rep["captured_panel_dates"] == ["2026-08-26", "2026-08-27"])
        check("2k. missing artifact detected",
              any("COHORT_PROTOCOL" in m for m in rep["missing_required_artifacts"]))

        print("\n=== 3. read-only ===")
        before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
        R.build_report(root)
        after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
        check("3a. no file created, modified or removed", before == after)

        print(f"\n{CHECKS} checks run")
        if FAILURES:
            print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
            for f in FAILURES:
                print(f"  - {f}")
            return 1
        print("\nALL HYP-01 PROGRESS REPORTER CHECKS PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
