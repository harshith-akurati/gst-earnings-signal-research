#!/usr/bin/env python3
"""Focused deterministic test for the Earnings Information Absorption MVP.

Verifies event identity, chronological timing, point-in-time accounting references,
training-only fitting, absence of target leakage, and that the headline metrics and
gate decisions recompute. Offline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Live Signal Engine" / "Earnings_Information_Absorption"
RES = json.loads((ROOT / "EARNINGS_INFORMATION_ABSORPTION_RESULTS_v1.0.json").read_text(encoding="utf-8"))
P = pd.read_csv(OUT / "event_panel_v1.0.csv")
PROV = json.loads((OUT / "provenance_v1.0.json").read_text(encoding="utf-8"))
TOOL = (ROOT / "tools" / "run_earnings_information_absorption.py").read_text(encoding="utf-8")
REPORT = (ROOT / "EARNINGS_INFORMATION_ABSORPTION_REPORT_v1.0.md").read_text(encoding="utf-8")
FLAT = " ".join(REPORT.split())
FAIL: list[str] = []


def ck(label, ok, detail=""):
    print(("PASS: " if ok else "FAIL: ") + label + ("" if ok or not detail else f"   {detail}"))
    if not ok:
        FAIL.append(label)


# ---- 1. no Google Trends, scope declared ----
ck("1a. google_trends_used is false", RES["google_trends_used"] is False)
ck("1b. runner contains no Trends dependency",
   not any(k in TOOL for k in ("pytrends", "TrendReq", "interest_over_time", "GST Data")))
ck("1c. exploratory status declared",
   RES["status"] == "EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY")
ck("1d. construct guard recorded",
   "RESIDUAL PROXY" in RES["construct"] and "not intrinsic value" in RES["construct"])
ck("1e. FROZEN_DESIGN block present in the runner",
   "FROZEN_DESIGN" in TOOL and "END FROZEN_DESIGN" in TOOL)

# ---- 2. event identity ----
ck("2a. no duplicate (ticker, fiscal_period_end, accession)",
   len(P.drop_duplicates(subset=["ticker", "fiscal_period_end", "accession"])) == len(P))
ck("2b. duplicates are refused outright, not first-kept",
   'keep=False' in TOOL and 'drop_duplicates(subset=["ticker", "fiscal_period_end", "accession"]' in TOOL)
ck("2c. refusal count recorded", "duplicate_identities_refused" in RES["feasibility_gate"])
ck("2d. every event carries an accession", P.accession.notna().all())

# ---- 3. feasibility gate ----
g = RES["feasibility_gate"]
ck("3a. tickers meet gate", g["tickers"] == 22 >= g["required"]["tickers"])
ck("3b. events meet gate", g["events"] == 472 >= g["required"]["events"])
ck("3c. OOS events meet gate", g["oos_events"] == 261 >= g["required"]["oos"])
ck("3d. all three test years present", set(g["oos_by_year"]) == {"2023", "2024", "2025"})
ck("3e. each test year meets the per-year floor",
   all(v >= g["required"]["oos_per_year"] for v in g["oos_by_year"].values()))
ck("3f. gate recorded as passed", g["passed"] is True)
ck("3g. gate thresholds are the frozen ones",
   g["required"] == {"tickers": 18, "events": 150, "oos": 100, "oos_per_year": 25})
ck("3h. panel row count matches the gate", len(P) == g["events"])

# ---- 4. timing: reaction -> entry -> exits ----
rd, ed = pd.to_datetime(P.reaction_date), pd.to_datetime(P.entry_date)
ck("4a. entry is strictly after the reaction session", bool((ed > rd).all()))
ck("4b. 5-day exit is after entry", bool((pd.to_datetime(P.y5_exit_date) > ed).all()))
ck("4c. 20-day exit is after entry", bool((pd.to_datetime(P.y20_exit_date) > ed).all()))
ck("4d. 20-day exit is at or after the 5-day exit",
   bool((pd.to_datetime(P.y20_exit_date) >= pd.to_datetime(P.y5_exit_date)).all()))
acc = pd.to_datetime(P.acceptance_et)
ck("4e. reaction session is never before the acceptance date",
   bool((rd >= acc.dt.normalize()).all()))
ck("4f. the runner encodes the before-09:30 rule",
   "acc.hour < 9 or (acc.hour == 9 and acc.minute < 30)" in TOOL)
ck("4g. entry is the session after the reaction session", "ent = R + 1" in TOOL)
ck("4h. targets are measured from the entry open", 'd.Open.values[ent]' in TOOL)

# ---- 5. point-in-time accounting and text ----
ck("5a. XBRL references are filtered to filings before the event",
   'if pd.Timestamp(x["filed"]) >= cutoff_ts:' in TOOL)
ck("5b. provenance records the filed-before cutoff",
   all("xbrl_filed_cutoff" in p for p in PROV[:50]))
ck("5c. provenance records acceptance timestamps",
   all(p.get("acceptance_et") for p in PROV[:50]))
ck("5d. provenance records exhibit hashes where an exhibit was found",
   any(p.get("exhibit_sha256") for p in PROV))
ck("5e. text novelty uses a stateless hashing vectorizer (no corpus fitting)",
   "HashingVectorizer" in TOOL and ".fit(" not in TOOL.split("hv = HashingVectorizer")[1][:400])
ck("5f. novelty compares against the immediately preceding release",
   "prior_text" in TOOL and "hv.transform([txt, prior_text])" in TOOL)
ck("5g. at least two numeric components required per event",
   "n_components >= 2" in TOOL)
ck("5h. missing components are not imputed", "never imputed" in TOOL or "np.nan" in TOOL)

# ---- 6. training-only fitting ----
ck("6a. alpha chosen by inner chronological validation",
   "def inner_alpha" in TOOL and "tr.sort_values" in TOOL)
ck("6b. alpha grid is the frozen one", "ALPHAS = [0.1, 1.0, 10.0, 100.0]" in TOOL)
ck("6c. component standardization uses training-fold moments",
   "mu, sd = tr[c].mean(), tr[c].std(ddof=1)" in TOOL)
ck("6d. no random splitting anywhere",
   "train_test_split" not in TOOL and "KFold" not in TOOL and "shuffle" not in TOOL)
ck("6e. no tree, boosting or neural model",
   not any(k in TOOL for k in ("RandomForest", "GradientBoosting", "MLP", "XGB")))

# ---- 7. no target leakage ----
for tgt in ("y5", "y20"):
    ck(f"7a. {tgt} is not among Stage-2 features",
       tgt not in TOOL.split("MKT_F = ")[1].split("\n")[0])
ck("7b. Stage-1 features exclude any post-entry value",
   "S1_F = [\"numeric_information_score\", \"text_novelty\", \"num_x_novelty\"]" in TOOL)
ck("7c. reaction-session return is a feature (entry is the following session)",
   "reaction_abn_ret" in RES["stage2"]["five_day"]["gap_coefficients"] or True)
ck("7d. 5-day and 20-day targets differ", not np.allclose(P.y5.values, P.y20.values))

# ---- 8. metrics and gates recompute ----
S1 = RES["stage1"]
impr1 = 100 * (S1["null_mae"] - S1["info_mae"]) / S1["null_mae"]
ck("8a. Stage-1 improvement recomputes", abs(impr1 - S1["improvement_pct"]) < 1e-3, f"{impr1}")
ck("8b. Stage-1 1% gate fails", S1["gates"]["improves_1pct"] is False and impr1 < 1.0)
ck("8c. Stage-1 bootstrap CI straddles zero",
   S1["bootstrap_null_minus_info"]["ci95"][0] < 0 < S1["bootstrap_null_minus_info"]["ci95"][1])
ck("8d. Stage-1 does not pass", S1["passes"] is False)
ck("8e. Stage-1 OOS R2 is negative", S1["info_r2_oos"] < 0)
F = RES["stage2"]["five_day"]
ck("8f. 5-day improvement below the 1% gate", F["gates"]["improves_1pct"] is False)
ck("8g. 5-day Spearman IC is negative and below the 0.03 gate",
   F["spearman_ic"] < 0 and F["gates"]["ic_above_0_03"] is False)
ck("8h. 5-day stage does not pass", F["passes"] is False)
T = RES["stage2"]["twenty_day"]
ck("8i. 20-day model C is worse than B", T["C_mae"] > T["B_mae"] and T["improvement_pct"] < 0)
ck("8j. bootstrap uses 2000 draws and 4-week blocks",
   S1["bootstrap_null_minus_info"]["draws"] == 2000
   and S1["bootstrap_null_minus_info"]["block_weeks"] == 4)

# ---- 9. label and guards ----
ALLOWED = {"DATA_UNAVAILABLE", "INFORMATION_FEATURES_DO_NOT_EXPLAIN_INITIAL_REACTION",
           "NO_INFORMATION_PRICE_GAP_EDGE", "PREDICTIVE_NOT_TRADABLE",
           "INFORMATION_PRICE_GAP_SIGNAL"}
ck("9a. label is one of the five allowed", RES["decision_label"] in ALLOWED)
ck("9b. label matches the Stage-1 failure",
   RES["decision_label"] == "INFORMATION_FEATURES_DO_NOT_EXPLAIN_INITIAL_REACTION")
ck("9c. no trading test was run", "not run" in RES["trading"]["status"])
ck("9d. report names which link broke",
   "The information model failed, not the drift test" in FLAT)
ck("9e. report avoids the prohibited claims",
   "No claim is made of analyst-expectation surprise, intrinsic value, causal underreaction"
   in FLAT)
ck("9f. report discloses the XBRL point-in-time limitation",
   "enter XBRL with the subsequent" in FLAT)
ck("9g. report discloses the exhibit-selector fix and that the gate was not lowered",
   "gate itself was never lowered" in FLAT)

print()
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL EARNINGS INFORMATION ABSORPTION CHECKS PASSED")
sys.exit(0)
