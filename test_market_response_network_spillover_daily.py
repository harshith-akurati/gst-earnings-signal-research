#!/usr/bin/env python3
"""Focused check on the daily-delay network spillover study.

Verifies the executable timing (entry strictly after the signal), that neighbor open(T)
is never the entry, event-level (not neighbor-level) primary inference, and that the
reported returns recompute. Deterministic and offline: no network call is made here.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
OUT = ROOT / "Live Signal Engine" / "Network_Spillover_Daily"
RES = json.loads((ROOT / "NETWORK_SPILLOVER_DAILY_RESULTS_v1.0.json").read_text(encoding="utf-8"))
REPORT = (ROOT / "NETWORK_SPILLOVER_DAILY_REPORT_v1.0.md").read_text(encoding="utf-8")
E = pd.read_csv(OUT / "anchor_event_spillovers_v1.0.csv")
PX = pd.read_csv(OUT / "daily_prices_v1.0.csv", parse_dates=["Date"])
REL = OUT / "network_relationships_v1.0.csv"
TOOL = (ROOT / "tools" / "run_network_spillover_daily_delay.py").read_text(encoding="utf-8")
FLAT = " ".join(REPORT.split())

FAIL = []


def check(label, ok, detail=""):
    print(("PASS: " if ok else "FAIL: ") + label + ("" if ok or not detail else f"   {detail}"))
    if not ok:
        FAIL.append(label)


import run_network_spillover_daily_delay as M  # noqa: E402

# ---- 1. executable timing ----
check("1a. entry day is strictly after the event day",
      bool((pd.to_datetime(E.entry_day) > pd.to_datetime(E.event_day)).all()))
check("1b. entry is the next available session, not a later one",
      all(len(PX[(PX.symbol == r.anchor) & (PX.Date > pd.Timestamp(r.event_day))
                 & (PX.Date < pd.Timestamp(r.entry_day))]) == 0
          for r in E.itertuples()))
check("1c. neighbor entry uses open(T+1), never open(T)",
      "ni = align(npx, entry_date)" in TOOL and "entry_date = pd.Timestamp(apx.Date.values[T + 1])" in TOOL)
check("1d. the anchor signal is a close-to-close read through close(T)",
      "apx.Close.values[T] / apx.Close.values[T - 1]" in TOOL)
check("1e. results state why this is executable",
      "known after that close" in RES["executable_because"]
      and "never used as an entry" in RES["executable_because"])

# ---- 2. design constants ----
check("2a. anchors are the three named", M.ANCHORS == ["NVDA", "AMD", "INTC"])
check("2b. twelve frozen neighbors", len(M.NEIGHBORS) == 12 and "META" in M.NEIGHBORS)
check("2c. SMH benchmark, SPY sensitivity", (M.BENCH, M.SENS) == ("SMH", "SPY"))
check("2d. two fixed exits", M.EXITS == {"close_T1": 1, "close_T3": 3})
check("2e. one fixed cost", M.COST_BPS == 10.0)
check("2f. GST threshold frozen and pre-event only",
      M.GST_HIGH_Z == 1.0 and "week_close < pd.Timestamp(event_day)" in TOOL
      and RES["design"]["overlapping_spike_classification_used"] is False)

# ---- 3. relationship table unchanged in character ----
with REL.open(encoding="utf-8") as fh:
    rel = list(csv.DictReader(fh))
check("3a. all relationships remain exploratory and static",
      all(r["evidence_status"] == "EXPLORATORY_STATIC" for r in rel))
check("3b. edge types stay within the permitted set",
      {r["edge_type"] for r in rel} <= {"COMPETITOR", "SUPPLIER_FOUNDRY", "EQUIPMENT",
                                        "NETWORKING", "SERVER_INTEGRATOR", "CUSTOMER_DEMAND"})

# ---- 4. event-level inference, no pseudo-replication ----
check("4a. usable anchor events match the event table",
      RES["sample"]["usable_anchor_events"] == len(E) == 63)
check("4b. events are balanced across the three anchors",
      RES["sample"]["by_anchor"] == {"INTC": 21, "AMD": 21, "NVDA": 21})
check("4c. primary observation is declared to be the anchor event",
      RES["design"]["primary_observation"] == "anchor event, not neighbor row")
check("4d. primary n equals the number of anchor events, not neighbor rows",
      RES["results"]["close_T1"]["gross"]["n"] == len(E)
      and RES["sample"]["neighbor_rows_descriptive"] > 10 * len(E))
check("4e. neighbor tables are labelled descriptive", "descriptive only" in RES["pseudo_replication_note"])

# ---- 5. returns recompute ----
cost = M.COST_BPS / 10000.0
for k in ("close_T1", "close_T3"):
    g = E[f"spillover_{k}"].dropna().values
    check(f"5a. {k} gross mean recomputes",
          abs(100 * g.mean() - RES["results"][k]["gross"]["mean_pct"]) < 1e-3)
    check(f"5b. {k} net == gross - cost",
          abs(RES["results"][k]["net"]["mean_pct"]
              - (RES["results"][k]["gross"]["mean_pct"] - 100 * cost)) < 1e-3)
check("5c. signed spillover equals sign(anchor) x unsigned mean",
      bool(np.allclose(E.anchor_sign.values * E.unsigned_close_T1.values,
                       E.spillover_close_T1.values, atol=1e-12)))
check("5d. anchor sign matches the sign of the anchor abnormal return",
      bool((np.sign(E.anchor_abnormal_close_T_pct.values) == E.anchor_sign.values).all()))

# ---- 6. the honest reading is preserved ----
perm = RES["comparators"]["randomized_anchor_sign_permutation"]
check("6a. a permutation comparator exists at event level", perm["n_permutations"] == 10000)
check("6b. the permutation does not reject", perm["two_sided_p"] > 0.05)
check("6c. the gross CI straddles zero even though the net one does not",
      RES["results"]["close_T1"]["gross"]["ci95_pct"][0] < 0
      < RES["results"]["close_T1"]["gross"]["ci95_pct"][1]
      and RES["results"]["close_T1"]["net"]["ci95_pct"][1] < 0)
check("6d. the report says the permutation is the governing comparator",
      "permutation test" in FLAT and "p = 0.13" in FLAT)
check("6e. the report does not present this as a tradable short",
      "not a tradable short" in FLAT)

# ---- 7. GST honesty ----
check("7a. high-GST cell size is reported", RES["gst"]["high_gst_events"] == 2)
check("7b. the report states n=2 supports no conclusion",
      "n = 2 supports no conclusion" in FLAT)
check("7c. the frozen threshold was not moved after seeing results",
      "z ≥ 1.0" in FLAT and M.GST_HIGH_Z == 1.0)
check("7d. AMD's missing GST coverage is disclosed",
      RES["gst"]["anchors_without_gst_coverage"] == ["AMD"] and "AMD has none" in FLAT)
check("7e. continuous interaction is reported alongside the split",
      RES["gst"]["continuous_interaction"]["n"] == 42)

# ---- 8. decision label ----
ALLOWED = {"DAILY_NETWORK_SPILLOVER_SUPPORTED", "DAILY_SPILLOVER_EXISTS_BUT_GST_ADDS_NOTHING",
           "GST_SELECTS_STRONGER_DAILY_SPILLOVERS", "NO_DAILY_NETWORK_SPILLOVER",
           "INSUFFICIENT_ANCHOR_EVENTS", "DAILY_DATA_UNAVAILABLE"}
check("8a. label is one of the six allowed", RES["decision_label"] in ALLOWED)
check("8b. label is NO_DAILY_NETWORK_SPILLOVER", RES["decision_label"] == "NO_DAILY_NETWORK_SPILLOVER")
check("8c. no model was fitted", RES["models_fitted"] is False)
check("8d. state isolation declared", RES["touches_hyp01_or_prospective_state"] is False)
for forbidden in ("registry.jsonl", "GST_HYP01_ANALYSIS_LOCK", "LOCKED_24_TICKER_UNIVERSE"):
    check(f"8e. runner never references {forbidden}", forbidden not in TOOL)

print()
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL DAILY NETWORK SPILLOVER CHECKS PASSED")
sys.exit(0)
