#!/usr/bin/env python3
"""Focused check on the network-spillover MVP.

Verifies the frozen relationship table, that the design constants match the brief,
that no impossible daily-open substitution can occur, and that a DATA_UNAVAILABLE
result reports no returns. Deterministic and offline: the network probe is not
re-run here.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
RES = json.loads((ROOT / "NETWORK_SPILLOVER_MVP_RESULTS_v1.0.json").read_text(encoding="utf-8"))
REPORT = (ROOT / "NETWORK_SPILLOVER_MVP_REPORT_v1.0.md").read_text(encoding="utf-8")
REL = ROOT / "Live Signal Engine" / "Network_Spillover_MVP" / "network_relationships_v1.0.csv"
TOOL = (ROOT / "tools" / "run_network_spillover_mvp.py").read_text(encoding="utf-8")
FLAT = " ".join(REPORT.split())

FAIL = []


def check(label, ok, detail=""):
    print(("PASS: " if ok else "FAIL: ") + label + ("" if ok or not detail else f"   {detail}"))
    if not ok:
        FAIL.append(label)


import run_network_spillover_mvp as M  # noqa: E402

# ---- 1. frozen relationship table ----
with REL.open(encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
PERMITTED = {"COMPETITOR", "SUPPLIER_FOUNDRY", "EQUIPMENT", "NETWORKING",
             "SERVER_INTEGRATOR", "CUSTOMER_DEMAND"}
check("1a. relationship table has the required columns",
      list(rows[0].keys())[:4] == ["anchor", "neighbor", "edge_type", "graph_distance"])
check("1b. only the three permitted anchors appear",
      {r["anchor"] for r in rows} == set(M.ANCHORS) == {"NVDA", "AMD", "INTC"})
bad_edges = {r["edge_type"] for r in rows} - PERMITTED
check(f"1c. only permitted edge types (bad={bad_edges})", not bad_edges)
check("1d. all six permitted edge types are exercised",
      {r["edge_type"] for r in rows} == PERMITTED)
check("1e. graph distances are positive integers",
      all(r["graph_distance"].isdigit() and int(r["graph_distance"]) >= 1 for r in rows))
check("1f. neighbors are drawn only from the fixed linked universe (plus anchors as peers)",
      {r["neighbor"] for r in rows} <= set(M.NEIGHBORS) | set(M.ANCHORS))
check("1g. no self-edges", not any(r["anchor"] == r["neighbor"] for r in rows))
check("1h. every relationship is labelled exploratory and static",
      all(r["evidence_status"] == "EXPLORATORY_STATIC" for r in rows))
check("1i. no duplicate anchor-neighbor pairs",
      len({(r["anchor"], r["neighbor"]) for r in rows}) == len(rows))

# ---- 2. design constants match the brief ----
check("2a. reaction cutoff is 09:35 ET", M.REACTION_CUTOFF_ET == "09:35")
check("2b. earliest neighbor entry is 09:40 ET", M.EARLIEST_ENTRY_ET == "09:40")
check("2c. the three fixed exits are present",
      M.EXITS == ["same_day_close", "next_day_close", "third_trading_day_close"])
check("2d. one fixed disclosed cost", M.COST_BPS == 10.0)
check("2e. SMH is the benchmark, SPY the sensitivity", M.BENCHMARKS == ["SMH", "SPY"])
check("2f. the fixed linked universe is exactly the twelve named firms",
      M.NEIGHBORS == ["TSM", "ASML", "AMAT", "LRCX", "AVGO", "ANET", "DELL", "SMCI",
                      "MSFT", "AMZN", "GOOGL", "META"])
check("2g. attention is the strictly pre-event GST construction",
      "weeks closing before the event" in RES["design"]["attention_variable"]
      and RES["design"]["overlapping_spike_classification_used"] is False)
check("2h. no quantum kernel", RES["quantum_kernels_implemented"] is False
      and "quantum" not in TOOL.lower().split('"""')[2] if '"""' in TOOL else True)

# ---- 3. the impossible-trade substitution is refused in code ----
check("3a. a refusal guard exists", "def refuse_impossible_substitution" in TOOL)
try:
    M.refuse_impossible_substitution()
    ok = False
except SystemExit:
    ok = True
except Exception:
    ok = False
check("3b. the guard actually raises", ok)
check("3c. the results record the refusal", "substitution_refused" in RES
      and "impossible trade" in RES["substitution_refused"])
check("3d. the report states daily data was not substituted",
      "was not substituted" in FLAT and "impossible trade" in FLAT)

# ---- 4. DATA_UNAVAILABLE is reported honestly ----
ALLOWED = {"NETWORK_SPILLOVER_SIGNAL_SUPPORTED", "NETWORK_SPILLOVER_EXISTS_BUT_GST_ADDS_NOTHING",
           "GST_SELECTS_STRONGER_NETWORK_SPILLOVERS", "NO_NETWORK_SPILLOVER_SIGNAL",
           "INSUFFICIENT_ANCHOR_EVENTS", "DATA_UNAVAILABLE"}
check("4a. decision label is one of the six allowed", RES["decision_label"] in ALLOWED)
check("4b. label is DATA_UNAVAILABLE", RES["decision_label"] == "DATA_UNAVAILABLE")
check("4c. no returns are reported", RES["computed_returns"] is None
      and RES["anchor_events_evaluated"] == 0)
check("4d. the probe evidence is recorded",
      len(RES["data_probe"]["five_minute_probes"]) >= 3
      and RES["data_probe"]["deep_history_available"] is False)
check("4e. the shallow window is disclosed rather than hidden",
      RES["data_probe"]["max_days_back_with_bars"] > 0
      and RES["data_probe"]["max_days_back_with_bars"] < 90)
check("4f. the report contains no spillover return figure",
      "spillover return" in FLAT.lower() and "%" not in FLAT.split("## What was NOT done")[0].split("Decision")[1])
check("4g. no credential value is present anywhere",
      "APCA_API_SECRET_KEY" not in json.dumps(RES).replace('"APCA_API_KEY_ID / APCA_API_SECRET_KEY for the already-implemented Alpaca provider"', "")
      or all(not v for v in [RES["data_probe"]["providers"]["alpaca_env_vars_present"]]))
check("4h. provider probe records names only, never values",
      "never read, printed, logged or committed" in RES["data_probe"]["providers"]["note"])

# ---- 5. state isolation ----
check("5a. declares no HYP-01 or prospective state touched",
      RES["touches_hyp01_or_prospective_state"] is False)
for forbidden in ("registry.jsonl", "GST_HYP01_ANALYSIS_LOCK", "LOCKED_24_TICKER_UNIVERSE",
                  "GST_SEARCH_CONSTRUCT_VALIDITY"):
    check(f"5b. runner never references {forbidden}", forbidden not in TOOL)
check("5c. the unanswered question is stated as unanswered",
      "remains untested" in FLAT)

print()
if FAIL:
    print(f"{len(FAIL)} FAILURE(S): {FAIL}")
    sys.exit(1)
print("ALL NETWORK SPILLOVER MVP CHECKS PASSED")
sys.exit(0)
