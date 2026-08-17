#!/usr/bin/env python3
"""Source-to-number checklist for the extended abstract.

Every figure quoted in ATTENTION_WITHOUT_ALPHA_EXTENDED_ABSTRACT_v1.0.md is tied to the
merged artifact it came from. Read-only: no artifact is modified, no model is run, no
data is retrieved.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABS = ROOT / "ATTENTION_WITHOUT_ALPHA_EXTENDED_ABSTRACT_v1.0.md"
TEXT = " ".join(ABS.read_text(encoding="utf-8").split())

FAIL = []


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def tie(claim: str, source: str, value, quoted: str):
    """The number must both match its source and appear verbatim in the abstract."""
    in_text = quoted in TEXT
    print(f"  {'OK ' if in_text else 'MISS'}  {claim:52s} {quoted:>12s}  <- {source}")
    if not in_text:
        FAIL.append(f"{claim}: {quoted} not found in abstract")
    return value


dec = load("RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json")
dirn = load("RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json")
mag = load("RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json")
now = load("SEARCH_DEMAND_NOWCAST_RESULTS_v1.0.json")
pil = load("RESTAURANT_SEARCH_PILOT_RESULTS_v1.0.json")
dir_report = " ".join((ROOT / "RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md")
                      .read_text(encoding="utf-8").split())

print("SOURCE-TO-NUMBER CHECKLIST\n")

E = next(s for s in dec["scorecard"] if s["strategy"].startswith("E."))
inc = dec["clustered_inference"]["strategy_E_incremental_high_gst"]
tie("Strategy E net return", "RETROSPECTIVE_MARKET_RESPONSE_RESULTS", E["mean_net_pct"], "+0.854%")
tie("E incremental GST coefficient", "same, clustered_inference", inc["coef_pp"], "+0.013 pp")
tie("E incremental p-value", "same, clustered_inference", inc["p_value"], "p = 0.9833")
assert E["mean_net_pct"] == 0.8543 and inc["coef_pp"] == 0.0131 and round(inc["p_value"], 4) == 0.9833

tie("Leaked direction accuracy", "RETROSPECTIVE_DIRECTION_SIGNAL_REPORT", "63.6%", "63.6%")
tie("Corrected direction accuracy", "RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS", 0.4792, "47.9%")
tie("Corrected direction AUC", "same, pooled_out_of_sample.logistic_l2", 0.4654, "0.4654")
tie("Intercept-only null Brier", "same, intercept_only_prevalence", 0.256, "0.2560")
tie("Logistic Brier", "same, logistic_l2", 0.2711, "0.2711")
tie("Duplicate rows removed", "same, sample", dirn["sample"]["duplicate_rows_removed"], "68 of 285")
tie("Unique identities after dedup", "same, sample", dirn["sample"]["unique_event_identities"], "217 unique")
assert dirn["pooled_out_of_sample"]["logistic_l2"]["accuracy"] == 0.4792
assert dirn["pooled_out_of_sample"]["logistic_l2"]["auc"] == 0.4654
assert dirn["pooled_out_of_sample"]["intercept_only_prevalence"]["brier"] == 0.256
assert dirn["pooled_out_of_sample"]["logistic_l2"]["brier"] == 0.2711
assert dirn["sample"]["duplicate_rows_removed"] == 68 and dirn["sample"]["rows_in_source"] == 285
assert "63.6% accuracy" in dir_report and "+0.60% net" in dir_report

mb = mag["pooled_out_of_sample"]["B_baseline_no_gst"]["mae_pp"]
mc = mag["pooled_out_of_sample"]["C_baseline_plus_gst"]["mae_pp"]
mp = mag["decisive_paired_loss_difference"]["clustered"]["p_value"]
tie("Magnitude MAE without GST", "RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS", mb, "3.6284 pp")
tie("Magnitude MAE with GST", "same", mc, "3.6299 pp")
tie("Magnitude paired p-value", "same, clustered", mp, "p = 0.9827")
assert (mb, mc, mp) == (3.6284, 3.6299, 0.9827)

nb = now["pooled_out_of_sample"]["B_fundamental"]["mae_pp"]
nc = now["pooled_out_of_sample"]["C_fundamental_plus_search"]["mae_pp"]
npv = now["decisive_paired_comparison"]["clustered"]["p_value"]
tie("Nowcast MAE without search", "SEARCH_DEMAND_NOWCAST_RESULTS", nb, "6.3679 pp")
tie("Nowcast MAE with search", "same", nc, "6.8735 pp")
tie("Nowcast paired p-value", "same, clustered", npv, "p = 0.6253")
tie("Nowcast OOS observations", "same, out_of_sample", now["out_of_sample"]["n"], "38")
tie("Nowcast decision label", "same, decision_label", now["decision_label"], "INSUFFICIENT_DATA")
# Source value is exactly 0.62525. The abstract renders it half-up as 0.6253; Python's
# round() is banker's and would give 0.6252, so compare to the source with a tolerance
# rather than asserting one rounding convention.
assert (nb, nc) == (6.3679, 6.8735) and abs(npv - 0.62525) < 1e-9 and abs(npv - 0.6253) < 1e-3
assert now["out_of_sample"]["n"] == 38 and now["decision_label"] == "INSUFFICIENT_DATA"

M = pil["models"]
tie("Pilot null Brier", "RESTAURANT_SEARCH_PILOT_RESULTS", M["A"]["brier"], "0.18454")
tie("Pilot baseline Brier", "same", M["B"]["brier"], "0.20211")
tie("Pilot + investor search Brier", "same", M["C"]["brier"], "0.23665")
tie("Pilot + product search Brier", "same", M["D"]["brier"], "0.24739")
tie("Product incremental p-value", "same, incremental_C_vs_D.clustered",
    pil["incremental_C_vs_D"]["clustered"]["p_value"], "p = 0.6813")
tie("Non-search baseline AUC", "same, models.B", M["B"]["auc"], "0.6460")
tie("Baseline top-quintile rate", "same, top_quintile_large_move_rate.B",
    pil["top_quintile_large_move_rate"]["B"]["rate"], "35.29%")
tie("Baseline top-quintile lift", "same", pil["top_quintile_large_move_rate"]["B"]["lift_vs_base"],
    "1.447×")
tie("Large-move base rate", "same, out_of_sample.large_move_rate",
    pil["out_of_sample"]["large_move_rate"], "24.39%")
assert (M["A"]["brier"], M["B"]["brier"], M["C"]["brier"], M["D"]["brier"]) == \
       (0.18454, 0.20211, 0.23665, 0.24739)
assert round(pil["incremental_C_vs_D"]["clustered"]["p_value"], 4) == 0.6813
assert M["B"]["auc"] == 0.646
assert pil["top_quintile_large_move_rate"]["B"]["rate"] == 0.3529
assert round(pil["top_quintile_large_move_rate"]["B"]["lift_vs_base"], 3) == 1.447
assert pil["out_of_sample"]["large_move_rate"] == 0.2439
tie("Leakage checks in the final pilot", "same, leakage_assertion",
    pil["leakage_assertion"]["checks"], "353 checks")
assert pil["leakage_assertion"]["checks"] == 353 and pil["leakage_assertion"]["violations"] == 0

# claims the abstract must NOT make
for forbidden in ("proves market efficiency", "Google Trends is useless in general.",
                  "investable model is established"):
    ok = forbidden not in TEXT
    print(f"  {'OK ' if ok else 'MISS'}  abstract avoids overclaim: {forbidden!r}")
    if not ok:
        FAIL.append(f"overclaim present: {forbidden}")

body = re.sub(r"`[^`]*`", " ", ABS.read_text(encoding="utf-8"))
words = len([w for w in re.split(r"\s+", body) if w.strip()])
print(f"\n  word count: {words} (target 900-1200): {'OK' if 900 <= words <= 1200 else 'OUT OF RANGE'}")
if not 900 <= words <= 1200:
    FAIL.append(f"word count {words} outside 900-1200")

print()
if FAIL:
    print(f"{len(FAIL)} PROBLEM(S): {FAIL}")
    sys.exit(1)
print("ALL NUMBERS TIE OUT TO MERGED SOURCE ARTIFACTS")
sys.exit(0)
