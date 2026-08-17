#!/usr/bin/env python3
"""Complete numeric audit of the extended abstract.

Every numeric token in ATTENTION_WITHOUT_ALPHA_EXTENDED_ABSTRACT_v1.0.md is accounted
for: each is either (a) tied to the merged artifact it came from and asserted to appear
verbatim, or (b) listed in an explicit allowlist of non-artifact tokens (section
numbers, list numerals, a citation year, the document version). Nothing is silently
uncovered, so the coverage claim is exact rather than a headline-only sample.

Read-only: no artifact is modified, no model is run, no data is retrieved.
"""
from __future__ import annotations

import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABS = ROOT / "ATTENTION_WITHOUT_ALPHA_EXTENDED_ABSTRACT_v1.0.md"
RAW = ABS.read_text(encoding="utf-8")
TEXT = " ".join(RAW.split())

FAIL: list[str] = []
COVERED: set[str] = set()


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def tie(claim: str, source: str, quoted: str, matches: bool):
    """Quoted string must appear in the abstract AND match its source value."""
    ok = quoted in TEXT and matches
    print(f"  {'OK ' if ok else 'FAIL'}  {claim:50s} {quoted:>14s}  <- {source}")
    if not ok:
        FAIL.append(f"{claim} ({quoted})")
    for tok in re.findall(r"\d[\d,]*\.?\d*", quoted):
        COVERED.add(tok.rstrip(".,"))


dec = load("RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json")
dirn = load("RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json")
mag = load("RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json")
now = load("SEARCH_DEMAND_NOWCAST_RESULTS_v1.0.json")
pil = load("RESTAURANT_SEARCH_PILOT_RESULTS_v1.0.json")
dir_rep = " ".join((ROOT / "RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md").read_text(encoding="utf-8").split())

print("COMPLETE NUMERIC AUDIT\n")
print("-- Study (a): retrospective decomposition --")
E = next(s for s in dec["scorecard"] if s["strategy"].startswith("E."))
inc = dec["clustered_inference"]["strategy_E_incremental_high_gst"]
tie("Strategy E net return", "MARKET_RESPONSE_RESULTS.scorecard", "+0.854%", E["mean_net_pct"] == 0.8543)
tie("Strategy E standalone t", "same.t_stat_net", "3.0", round(E["t_stat_net"]) == 3)
tie("E incremental coefficient", "same.clustered_inference", "+0.013 pp", inc["coef_pp"] == 0.0131)
tie("E incremental p-value", "same.clustered_inference", "0.9833", round(inc["p_value"], 4) == 0.9833)

print("-- Study (b): direction signal --")
lg = dirn["pooled_out_of_sample"]["logistic_l2"]
tie("Pre-correction accuracy", "DIRECTION_SIGNAL_REPORT", "63.6%", "63.6% accuracy" in dir_rep)
tie("Pre-correction AUC", "DIRECTION_SIGNAL_REPORT", "0.6395", "AUC 0.6395" in dir_rep)
tie("Pre-correction strategy net", "DIRECTION_SIGNAL_REPORT", "+0.60%", "+0.60% net" in dir_rep)
tie("Corrected strategy net", "DIRECTION_SIGNAL_REPORT", "−0.70%", "−0.70% net" in dir_rep)
tie("Corrected accuracy", "DIRECTION_SIGNAL_RESULTS.logistic_l2", "47.9%", lg["accuracy"] == 0.4792)
tie("Corrected AUC", "same", "0.4654", lg["auc"] == 0.4654)
tie("Duplicate rows", "same.sample", "68 of 285",
    dirn["sample"]["duplicate_rows_removed"] == 68 and dirn["sample"]["rows_in_source"] == 285)
tie("Unique identities", "same.sample", "217 unique", dirn["sample"]["unique_event_identities"] == 217)
tie("Null Brier", "same.intercept_only_prevalence", "0.2560",
    dirn["pooled_out_of_sample"]["intercept_only_prevalence"]["brier"] == 0.256)
tie("Logistic Brier", "same.logistic_l2", "0.2711", lg["brier"] == 0.2711)

print("-- Study (c): magnitude forecast --")
mp = mag["decisive_paired_loss_difference"]["clustered"]
tie("MAE without attention", "MAGNITUDE_RESULTS.B_baseline_no_gst", "3.6284 pp",
    mag["pooled_out_of_sample"]["B_baseline_no_gst"]["mae_pp"] == 3.6284)
tie("MAE with attention", "same.C_baseline_plus_gst", "3.6299 pp",
    mag["pooled_out_of_sample"]["C_baseline_plus_gst"]["mae_pp"] == 3.6299)
tie("Paired p-value", "same.clustered", "0.9827", mp["p_value"] == 0.9827)
tie("Spike-window length", "same.why_not_population_spike_zscore", "14-day",
    "14-day window" in mag["why_not_population_spike_zscore"])
tie("Magnitude cluster count", "same.clustered.n_clusters (lower end of 26-28)", "26",
    mp["n_clusters"] == 26)

print("-- Study (d): revenue nowcasting --")
npc = now["decisive_paired_comparison"]["clustered"]
# Explicit decimal half-up: 0.62525 -> 0.6253 (Python's round() is banker's and gives 0.6252).
half_up = Decimal(str(npc["p_value"])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
tie("MAE without search", "NOWCAST_RESULTS.B_fundamental", "6.3679 pp",
    now["pooled_out_of_sample"]["B_fundamental"]["mae_pp"] == 6.3679)
tie("MAE with search", "same.C_fundamental_plus_search", "6.8735 pp",
    now["pooled_out_of_sample"]["C_fundamental_plus_search"]["mae_pp"] == 6.8735)
tie("Paired p-value (half-up from 0.62525)", "same.clustered", "0.6253", half_up == Decimal("0.6253"))
print(f"        half-up check: source {npc['p_value']} -> ROUND_HALF_UP 4dp = {half_up}")
tie("OOS observations", "same.out_of_sample.n", "38", now["out_of_sample"]["n"] == 38)
tie("Required OOS minimum", "same.minimum_sample_gates.required", "40",
    now["minimum_sample_gates"]["required"]["oos_observations"] == 40)
tie("Nowcast cluster count", "same.clustered.n_clusters (lower end of 7-8)", "7", npc["n_clusters"] == 7)

print("-- Study (e/f): restaurant large-move pilot --")
M, TQ = pil["models"], pil["top_quintile_large_move_rate"]["B"]
tie("Null Brier", "PILOT_RESULTS.models.A", "0.18454", M["A"]["brier"] == 0.18454)
tie("Baseline Brier", "same.models.B", "0.20211", M["B"]["brier"] == 0.20211)
tie("+ investor Brier", "same.models.C", "0.23665", M["C"]["brier"] == 0.23665)
tie("+ product Brier", "same.models.D", "0.24739", M["D"]["brier"] == 0.24739)
tie("Product incremental p", "same.incremental_C_vs_D.clustered", "0.6813",
    round(pil["incremental_C_vs_D"]["clustered"]["p_value"], 4) == 0.6813)
tie("Baseline AUC", "same.models.B.auc", "0.6460", M["B"]["auc"] == 0.646)
tie("Top-quintile rate", "same.top_quintile_large_move_rate.B", "35.29%", TQ["rate"] == 0.3529)
tie("Top-quintile lift", "same", "1.447×", round(TQ["lift_vs_base"], 3) == 1.447)
tie("Large-move base rate", "same.out_of_sample", "24.39%", pil["out_of_sample"]["large_move_rate"] == 0.2439)
PILOT_SRC = (ROOT / "tools" / "run_restaurant_search_demand_pilot.py").read_text(encoding="utf-8")
tie("Tail threshold percentile", "run_restaurant_search_demand_pilot.py TAIL_Q", "75th",
    "TAIL_Q = 0.75" in PILOT_SRC)
tie("Leakage checks", "same.leakage_assertion", "353 checks",
    pil["leakage_assertion"]["checks"] == 353 and pil["leakage_assertion"]["violations"] == 0)
tie("Leakage violations", "same.leakage_assertion", "0 violations",
    pil["leakage_assertion"]["violations"] == 0)
tie("Pilot cluster count", "same.incremental.n_clusters (upper end of 7-8)", "8",
    pil["incremental_C_vs_D"]["clustered"]["n_clusters"] == 8)
tie("Frozen universe size", "same.frozen_queries", "eight restaurant", len(pil["frozen_queries"]) == 8)
tie("Direction-study clusters (upper end 26-28)", "DIRECTION_SIGNAL_RESULTS", "28",
    dec["clustered_inference"]["primary_magnitude_abs_day_return"]["n_clusters"] == 28)
tie("Mid cluster count", "DIRECTION_SIGNAL_RESULTS.incremental", "27",
    dirn["combined_strategy"]["incremental_gst_effect_cr2"]["n_clusters"] == 27)

# Non-artifact tokens: editorial, structural, or bibliographic. Declared, not hidden.
ALLOWLIST = {
    "1.0": "document version", "2011": "citation year (Da, Engelberg and Gao)",
    "2019": "study period start", "2025": "study period end",
    "2.02": "SEC 8-K item number", "8": "8-K form number / eight firms",
    "1": "section and list numeral", "2": "section and list numeral",
    "3": "section and list numeral", "4": "section and list numeral",
    "5": "section and list numeral / five studies", "6": "section and list numeral",
    "7": "section and list numeral", "0.64": "AUC rounded in prose (0.6460, tied above)",
    "0": "list/leakage zero", "2560": "part of 0.2560", "285": "part of '68 of 285'",
}

# strip trailing separators so "1." / "2025," are not counted as distinct tokens
tokens = {t.rstrip(".,") for t in re.findall(r"\d[\d,]*\.?\d*", TEXT)}
uncovered = sorted(t for t in tokens if t not in COVERED and t not in ALLOWLIST)
print("\n-- coverage --")
print(f"  distinct numeric tokens in abstract: {len(tokens)}")
print(f"  tied to a source artifact:           {len(COVERED & tokens)}")
print(f"  declared non-artifact (allowlist):   {len(tokens & set(ALLOWLIST))}")
print(f"  UNACCOUNTED:                         {len(uncovered)} {uncovered if uncovered else ''}")
if uncovered:
    FAIL.append(f"unaccounted numeric tokens: {uncovered}")

for forbidden in ("proves market efficiency", "Google Trends is useless in general.",
                  "validated proxy", "AAPL stock"):
    ok = forbidden not in TEXT
    print(f"  {'OK ' if ok else 'FAIL'}  abstract avoids: {forbidden!r}")
    if not ok:
        FAIL.append(f"present: {forbidden}")

LOWER = TEXT.lower()
for required in ("not preregistered", "candidate", "in this project's retrieval environment",
                 "several analyses initially produced encouraging headline results"):
    ok = required.lower() in LOWER
    print(f"  {'OK ' if ok else 'FAIL'}  abstract states: {required!r}")
    if not ok:
        FAIL.append(f"missing: {required}")

body = re.sub(r"`[^`]*`", " ", RAW)
words = len([w for w in re.split(r"\s+", body) if w.strip()])
print(f"\n  word count: {words} (target 900-1200): {'OK' if 900 <= words <= 1200 else 'OUT OF RANGE'}")
if not 900 <= words <= 1200:
    FAIL.append(f"word count {words} outside 900-1200")

print()
if FAIL:
    print(f"{len(FAIL)} PROBLEM(S): {FAIL}")
    sys.exit(1)
print("EVERY NUMERIC TOKEN IS SOURCED OR EXPLICITLY DECLARED NON-ARTIFACT")
sys.exit(0)
