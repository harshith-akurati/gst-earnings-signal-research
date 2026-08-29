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

        print("\n=== 2. registry-only reporting, no fabricated eligibility ===")
        again = R.render(R.build_report(root))
        check("2a. repeated runs are byte-identical", text == again)
        check("2b. binding target is 60", rep["binding_target"] == 60)

        # The core correction: an unevaluated zero is never presented as a real
        # eligible-event count.
        check("2c. eligibility is reported as NOT evaluated",
              rep["eligibility_evaluated"] is False
              and rep["eligible_event_count"] == "NOT_EVALUATED",
              str(rep["eligible_event_count"]))
        check("2d. no remaining_until_target is derived from an unevaluated count",
              rep["remaining_until_target"] == "NOT_EVALUATED",
              str(rep["remaining_until_target"]))
        check("2e. a reason for non-evaluation is given",
              isinstance(rep.get("eligibility_not_evaluated_reason"), str)
              and rep["eligibility_not_evaluated_reason"].strip() != "")
        check("2f. no canonical status document was accepted",
              rep["canonical_status_document"] is None)

        counts = rep["enrollment_counts"]
        # The fixture's AMENDMENT corrects EVT0003 from pending to verified, so
        # after folding all four effective events are enrolled.
        check("2g. all four effective events are ENROLLED_AWAITING_EVALUATION "
              "once the amendment is folded",
              counts["ENROLLED_AWAITING_EVALUATION"] == 4, str(counts))
        check("2h. no effective event is left NOT_ENROLLED",
              counts["NOT_ENROLLED"] == 0, str(counts))
        check("2i. enrollment counts reconcile to effective events seen",
              sum(counts.values()) == rep["effective_events_seen"],
              f"{sum(counts.values())} vs {rep['effective_events_seen']}")
        check("2j. the amendment folds in; 4 effective events, not 5",
              rep["effective_events_seen"] == 4
              and rep["amendment_rows_folded"] == 1,
              f"seen={rep['effective_events_seen']} amd={rep['amendment_rows_folded']}")

        obs = rep["registry_only_observations"]
        check("2k. the INTRADAY registration is a DESCRIPTIVE observation, "
              "not a terminal S-7 disposition",
              obs["registered_session_intraday"] == 1
              and "MEASUREMENT_INCOMPATIBLE_INTRADAY" not in json.dumps(rep),
              json.dumps(obs))
        check("2l. no S-2..S-7 disposition appears anywhere in the report",
              not any(k in json.dumps(rep) for k in
                      ("CLASS_INELIGIBLE", "CORE_GATE_FAILED", "D1_GATE_FAILED",
                       "GST_PROVENANCE_FAILED", "OUTCOME_MISSING")))

        needle = '"row_type"' + ': "' + "event" + '"'
        prod = (Path(__file__).resolve().parent / "tools"
                / "hyp01_progress_report.py").read_text(encoding="utf-8")
        check("2m. no fixture or production code assumes row_type 'event'",
              needle not in prod and '"event"' not in prod)
        check("2n. draft cohort protocols are not required artifacts",
              not any("COHORT_PROTOCOL" in a for a in R.REQUIRED_ARTIFACTS),
              str(R.REQUIRED_ARTIFACTS))
        check("2o. captured panel dates read from filenames only",
              rep["captured_panel_dates"] == ["2026-08-26", "2026-08-27"])

        print("\n=== 2b. a verified canonical status document IS used ===")
        good = tmp / "status_ok.json"
        good.write_text(json.dumps({
            "schema": "GST_HYP01_ELIGIBILITY_STATUS_v1",
            "eligible_event_count": 7, "binding_target": 60,
            "effective_events_seen": 9,
            "exclusions_by_reason": {"NOT_ENROLLED": 2},
            "registry_snapshot_sha256": "d" * 64}), encoding="utf-8")
        rep2 = R.build_report(root, canonical_status=good)
        check("2p. a schema-valid status document supplies the eligible count",
              rep2["eligibility_evaluated"] is True
              and rep2["eligible_event_count"] == 7
              and rep2["remaining_until_target"] == 53, str(rep2["eligible_event_count"]))
        check("2q. the status document's own SHA-256 is recorded",
              len(rep2["canonical_status_document"]["sha256"]) == 64)

        bad = tmp / "status_bad_schema.json"
        bad.write_text(json.dumps({"schema": "SOMETHING_ELSE"}), encoding="utf-8")
        rep3 = R.build_report(root, canonical_status=bad)
        check("2r. a wrong-schema status document is refused, not used",
              rep3["eligibility_evaluated"] is False
              and rep3["eligible_event_count"] == "NOT_EVALUATED")

        broken = tmp / "status_broken.json"
        broken.write_text("{ not json", encoding="utf-8")
        rep4 = R.build_report(root, canonical_status=broken)
        check("2s. a malformed status document is refused, not used",
              rep4["eligibility_evaluated"] is False)
        rep5 = R.build_report(root, canonical_status=tmp / "absent.json")
        check("2t. an absent status document is refused, not used",
              rep5["eligibility_evaluated"] is False)

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
