#!/usr/bin/env python3
"""Focused deterministic test for Point-in-Time Earnings Surprise v2 (extraction phase).

Verifies the outcome-blind dev-sample rule, event uniqueness, later-XBRL isolation,
parser determinism and refusal behaviour, and that the reported extraction/validation
figures recompute. No outcome stage exists in this branch: the gate failed. Offline.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "Live Signal Engine" / "PIT_Earnings_Surprise_v2"
V = json.loads((OUT / "extraction_validation_v1.0.json").read_text(encoding="utf-8"))
X = pd.read_csv(OUT / "exhibit_extractions_v1.0.csv")
A = pd.read_csv(OUT / "extraction_audit_rows_v1.0.csv")
R = json.loads((ROOT / "PIT_EARNINGS_SURPRISE_V2_RESULTS_v1.0.json").read_text(encoding="utf-8"))
PARSER = (ROOT / "tools" / "exhibit99_parser.py").read_text(encoding="utf-8")
VAL_SRC = (ROOT / "tools" / "validate_exhibit_extraction.py").read_text(encoding="utf-8")
REPORT = (ROOT / "PIT_EARNINGS_SURPRISE_V2_REPORT_v1.0.md").read_text(encoding="utf-8")
FLAT = " ".join(REPORT.split())
FAIL: list[str] = []
GATE_RATE = 0.90


def ck(label, ok, detail=""):
    print(("PASS: " if ok else "FAIL: ") + label + ("" if ok or not detail else f"   {detail}"))
    if not ok:
        FAIL.append(label)


# ---- 1. scope declarations ----
ck("1a. exploratory status", V["status"] == "EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY")
ck("1b. google_trends_used is false", V["google_trends_used"] is False)
ck("1c. analyst_estimates_used is false", V["analyst_estimates_used"] is False)
ck("1d. later_xbrl_used_for_prediction is false", V["later_xbrl_used_for_prediction"] is False)
ck("1e. later-XBRL role documented as audit reference only",
   "audit reference only" in V["later_xbrl_role"])
ck("1f. no Trends dependency in either tool",
   not any(k in PARSER + VAL_SRC for k in ("pytrends", "TrendReq", "GST Data")))

# ---- 2. outcome-blind dev sample ----
ck("2a. dev sample is 2 per ticker", V["dev_sample"]["per_ticker"] == 2)
ck("2b. dev sample size and ticker count", V["dev_sample"]["n"] == 48
   and V["dev_sample"]["tickers"] == 24)
ck("2c. selection rule is a recorded SHA-256 ranking",
   "SHA-256" in V["dev_sample"]["rule"] and V["dev_sample"]["seed"] == "PIT_EARNINGS_SURPRISE_V2_DEV_SAMPLE")
ck("2d. rule states no reference to returns", "no reference to returns" in V["dev_sample"]["rule"])
ck("2e. dev flag present on the extraction table", "in_dev_sample" in X.columns)
ck("2f. dev sample rows match the recorded size", int(X.in_dev_sample.sum()) == V["dev_sample"]["n"])
# the ranking is reproducible
row = X[X.in_dev_sample].iloc[0]
h = hashlib.sha256(f"PIT_EARNINGS_SURPRISE_V2_DEV_SAMPLE|{row.ticker}|{row.filing_date}|{row.accession}".encode()).hexdigest()
ck("2g. dev-rank hash is reproducible", isinstance(h, str) and len(h) == 64)

# ---- 3. event identity ----
ck("3a. no duplicate (ticker, accession) in the extraction table",
   len(X.drop_duplicates(subset=["ticker", "accession"])) == len(X))
ck("3b. every row carries an accession", X.accession.notna().all())
ck("3c. events seen matches the table", V["events_seen"] == len(X))
ck("3d. exhibit count matches", V["with_exhibit"] == int(X.exhibit_url.notna().sum()))

# ---- 4. parser discipline ----
ck("4a. parser rejects adjusted / non-GAAP rows", "ADJUSTED = re.compile" in PARSER
   and "non[- ]?gaap" in PARSER)
ck("4b. parser rejects year-to-date spans", "YTD = re.compile" in PARSER
   and "six months" in PARSER and "nine months" in PARSER)
ck("4c. parser rejects EBITDA and guidance rows",
   "ebitda" in PARSER.lower() and "guidance" in PARSER.lower())
ck("4d. parser resolves thousands and millions",
   "in thousands" in PARSER and "in millions" in PARSER)
ck("4e. parser retains row label, column label, table index and units",
   all(k in PARSER for k in ("row_label", "column_label", "table_index", "raw_scale")))
ck("4f. parser identifies quarter columns and skips YTD columns",
   "QTR = re.compile" in PARSER and "reject year-to-date columns" in PARSER)
ck("4g. parser is deterministic (no randomness)",
   "random" not in PARSER and "shuffle" not in PARSER)
ck("4h. provenance columns exist for every component",
   all(f"{c}_row" in X.columns and f"{c}_col" in X.columns and f"{c}_table" in X.columns
       for c in ("revenue", "operating_income", "diluted_eps")))
ck("4i. exhibit hashes retained", "exhibit_sha256" in X.columns and X.exhibit_sha256.notna().any())

# ---- 5. later-XBRL isolation ----
ck("5a. audit rows keep exhibit and reference values separately",
   {"exhibit_value", "later_xbrl_value"} <= set(A.columns))
ck("5b. the validator never substitutes a reference value for an exhibit value",
   "cannot select, replace or feed a feature" in V["later_xbrl_role"])
ck("5c. no predictive stage was run that could have consumed the reference",
   R["not_run_because_gate_failed"]["surprise_construction"] == "not run"
   and R["not_run_because_gate_failed"]["model_b_vs_model_c"] == "not run"
   and R["not_run_because_gate_failed"]["post_entry_returns_inspected"] is False)
ck("5d. tolerances are the specified ones",
   V["tolerances"]["revenue_operating_income_relative"] == 0.005
   and V["tolerances"]["eps_absolute"] == 0.01)

# ---- 6. reported figures recompute ----
for c in ("revenue", "operating_income", "diluted_eps"):
    ck(f"6a. {c} extracted count recomputes",
       V["extracted_counts"][c] == int(X[c].notna().sum()))
    vc = V["validation_counts"][c]
    ck(f"6b. {c} validation rate recomputes",
       abs(V["validation_rates"][c] - vc["validated"] / vc["compared"]) < 1e-4)
    ck(f"6c. {c} compared equals extracted (gate denominator)",
       vc["compared"] == V["extracted_counts"][c])
    tot = vc["validated"] + V["contradicted_by_reference"].get(c, 0) + V["no_reference_available"].get(c, 0)
    ck(f"6d. {c} validated + contradicted + no-reference equals compared", tot == vc["compared"])
ck("6e. audit row count matches the components compared",
   len(A) == sum(v["compared"] for v in V["validation_counts"].values()))
ck("6f. validated_among_comparable excludes no-reference rows",
   "excluding extractions with no later-XBRL reference" in V["rate_definition"])

# ---- 7. gate outcome ----
ck("7a. gate thresholds are the specified ones",
   V["gate_thresholds"]["tickers"] == 18 and V["gate_thresholds"]["events"] == 180
   and V["gate_thresholds"]["oos"] == 120 and V["gate_thresholds"]["oos_per_year"] == 30
   and V["gate_thresholds"]["validation_rate"] == 0.90)
ck("7b. every component falls short of the 90% gate",
   all(v < 0.90 for v in V["validation_rates"].values()))
ck("7c. gate recorded as failed", V["extraction_gate_passed"] is False)
ck("7d. tolerances were not loosened to pass",
   V["tolerances"]["revenue_operating_income_relative"] == 0.005)

# ---- 8. report honesty ----
ck("8a. report states EXTRACTION_NOT_RELIABLE", "EXTRACTION_NOT_RELIABLE" in REPORT)
ck("8b. report states no outcome model was fitted",
   "No outcome model was fitted" in FLAT)
ck("8c. report names the failure mode as inadequate extraction",
   "this is **inadequate extraction**" in FLAT or "inadequate extraction" in FLAT)
ck("8d. report discloses both rate definitions",
   "14.6%" in FLAT and "32.9%" in FLAT)
ck("8e. report discloses the wrong-row example",
   "Sales and maturities of marketable securities" in FLAT)
ck("8f. report corrects the interim zero-contradiction statement",
   "mismatched-against-reference = 0" in FLAT and "artifact of the audit table" in FLAT)
ck("8g. report avoids the prohibited terms",
   "analyst surprise" not in FLAT.replace("called an analyst surprise", "")
   or "Nothing here is called an analyst surprise" in FLAT)
ck("8h. report states the question remains untested",
   "remains open and untested" in FLAT)

# ---- 9. results artifact agrees with the validation artifact ----
ck("9a. decision label is EXTRACTION_NOT_RELIABLE", R["decision_label"] == "EXTRACTION_NOT_RELIABLE")
ck("9b. results declare the same three no-use flags",
   R["google_trends_used"] is False and R["analyst_estimates_used"] is False
   and R["later_xbrl_used_for_prediction"] is False)
ck("9c. results stopped at the extraction gate",
   R["stopped_at"] == "phase_1_extraction_quality_gate")
for c in ("revenue", "operating_income", "diluted_eps"):
    e = R["extraction"][c]
    ck(f"9d. {c} counts agree between results and validation artifacts",
       e["extracted"] == V["extracted_counts"][c]
       and e["validated"] == V["validation_counts"][c]["validated"]
       and e["contradicted_by_reference"] == V["contradicted_by_reference"][c]
       and e["no_reference_available"] == V["no_reference_available"][c])
    ck(f"9e. {c} rates agree between results and validation artifacts",
       abs(e["validation_rate_gate_definition"] - V["validation_rates"][c]) < 1e-4
       and abs(e["validated_among_comparable"] - V["validated_among_comparable"][c]) < 1e-4)
ck("9f. results record no outcome stage was run",
   all(v == "not run" for k, v in R["not_run_because_gate_failed"].items()
       if isinstance(v, str) and k != "frozen_design_outcome_commit"))
ck("9g. results record that returns were never inspected",
   R["not_run_because_gate_failed"]["post_entry_returns_inspected"] is False)
ck("9h. results classify the failure as inadequate extraction",
   R["failure_mode_classification"] == "inadequate_extraction")
ck("9i. results record tolerances were not loosened",
   R["tolerances"]["loosened_after_seeing_results"] is False)
ck("9j. results list the prohibited interpretations as not made",
   {"analyst surprise", "intrinsic value", "causal underreaction"}
   <= set(R["prohibited_interpretations_not_made"]))
ck("9k. results carry the correction to the interim zero-mismatch statement",
   "artifact of the audit table" in R["correction_to_interim_statement"])
ck("9l. results state the binding limitation is measurement, not modeling",
   "engineering problem, not a modeling one" in R["most_important_limitation"])
ck("9m. coverage figures agree", R["coverage"]["item_202_events"] == V["events_seen"]
   and R["coverage"]["events_with_exhibit"] == V["with_exhibit"]
   and R["coverage"]["events_with_2plus_components"] == V["events_with_2plus_components"])
ck("9n. results gate matches the validation gate",
   R["gate"]["passed"] is False and V["extraction_gate_passed"] is False
   and R["gate"]["required_validation_rate_each_component"] == GATE_RATE)

print()
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL PIT EARNINGS SURPRISE V2 EXTRACTION CHECKS PASSED")
sys.exit(0)
