#!/usr/bin/env python3
"""Network-spillover MVP: anchor earnings reaction -> delayed linked-firm returns.

EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY. Touches no HYP-01 lock,
registry, F5 artifact, universe constant or prospective observation.

DESIGN (frozen before any return was computed)
  Anchors            NVDA, AMD, INTC
  Linked universe    TSM ASML AMAT LRCX AVGO ANET DELL SMCI MSFT AMZN GOOGL META
  Relationships      Live Signal Engine/Network_Spillover_MVP/network_relationships_v1.0.csv
                     exploratory and STATIC; edge types are labels, not evidence of
                     causal supply-chain exposure, and none was inferred from returns.
  Anchor reaction    computed from information available THROUGH 09:35 ET
  Neighbor entry     earliest permitted bar is 09:40 ET
  Exits              same-day close, next-day close, third-trading-day close
  Cost               10 bps round trip, fixed and disclosed
  Benchmark          SMH; SPY only as a documented sensitivity
  Attention          strictly pre-event GST z (weeks CLOSING before the event), the
                     construction from PR #24. The overlapping historical spike
                     classification is never used as pre-event evidence.

WHY THIS DESIGN NEEDS INTRADAY BARS
  A 09:35 reaction read and a 09:40 entry are not derivable from daily open/close.
  Substituting the daily open would mean entering at the SAME price whose gap was
  used to read the anchor's direction - an impossible trade. This runner refuses to
  do that; see refuse_impossible_substitution().

DATA PROBE
  This runner probes for 5-minute history before computing anything. If it cannot be
  obtained it emits DATA_UNAVAILABLE and writes no returns.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Live Signal Engine" / "Network_Spillover_MVP"
RELATIONSHIPS = OUT_DIR / "network_relationships_v1.0.csv"
RESULTS = ROOT / "NETWORK_SPILLOVER_MVP_RESULTS_v1.0.json"

ANCHORS = ["NVDA", "AMD", "INTC"]
NEIGHBORS = ["TSM", "ASML", "AMAT", "LRCX", "AVGO", "ANET", "DELL", "SMCI",
             "MSFT", "AMZN", "GOOGL", "META"]
BENCHMARKS = ["SMH", "SPY"]

REACTION_CUTOFF_ET = "09:35"
EARLIEST_ENTRY_ET = "09:40"
EXITS = ["same_day_close", "next_day_close", "third_trading_day_close"]
COST_BPS = 10.0

# The event study needs intraday bars back to the start of the anchor earnings
# history in this repository's population, not merely the recent past.
REQUIRED_HISTORY_START = "2021-01-01"
UA = {"User-Agent": "Mozilla/5.0 (gst-earnings-signal-research exploratory network MVP)"}


def refuse_impossible_substitution() -> None:
    """Guard. Daily open/close CANNOT stand in for a 09:35 read and a 09:40 entry.

    Reading the anchor's direction from the opening gap and then entering neighbors
    at that same open is not executable: the price used to form the signal is the
    price assumed for the fill. This function exists so the prohibition is in the
    code path, not only in prose.
    """
    raise SystemExit(
        "REFUSED: daily open/close cannot substitute for 5-minute bars. Reading the "
        "anchor reaction from the opening gap and entering neighbors at the same open "
        "is an impossible trade, and this MVP will not report it as a result.")


def probe_5m(symbol: str, days_back: int, timeout: int = 45) -> dict:
    """One probe of a public chart endpoint for 5-minute bars."""
    now = int(time.time())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={now - days_back * 86400}&period2={now}&interval=5m&includePrePost=false")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            body = json.loads(r.read())
        res = (body.get("chart") or {}).get("result")
        if not res or not res[0].get("timestamp"):
            return {"days_back": days_back, "bars": 0,
                    "error": str((body.get("chart") or {}).get("error"))[:120]}
        ts = res[0]["timestamp"]
        return {"days_back": days_back, "bars": len(ts),
                "first_epoch": int(ts[0]), "last_epoch": int(ts[-1])}
    except Exception as e:                                   # noqa: BLE001
        return {"days_back": days_back, "bars": -1,
                "error": f"{type(e).__name__}: {str(e)[:110]}"}


def credentials_present() -> dict:
    """Names only. No value is read, printed, logged or committed."""
    return {
        "alpaca_env_vars_present": bool(os.environ.get("APCA_API_KEY_ID")
                                        and os.environ.get("APCA_API_SECRET_KEY")),
        "other_provider_key_names_present": sorted(
            k for k in os.environ
            if any(t in k.upper() for t in ("POLYGON", "TIINGO", "FINNHUB", "ALPHAVANTAGE", "IEX"))),
        "note": "credential VALUES are never read, printed, logged or committed",
    }


def main() -> int:
    probes = [probe_5m("NVDA", d) for d in (30, 59, 90, 400)]
    deep = [p for p in probes if p["days_back"] >= 90 and p["bars"] > 0]
    shallow = [p for p in probes if p["days_back"] <= 59 and p["bars"] > 0]
    max_days = max((p["days_back"] for p in probes if p["bars"] > 0), default=0)

    intraday_ok = bool(deep)
    res = {
        "artifact": "NETWORK_SPILLOVER_MVP_RESULTS", "version": "1.0",
        "status": "EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY",
        "touches_hyp01_or_prospective_state": False,
        "quantum_kernels_implemented": False,
        "design": {
            "anchors": ANCHORS, "neighbors": NEIGHBORS, "benchmarks": BENCHMARKS,
            "relationship_table": str(RELATIONSHIPS.relative_to(ROOT)).replace("\\", "/"),
            "relationship_status": "EXPLORATORY_STATIC; edge types are labels, not "
                                   "evidence of causal supply-chain exposure; none inferred from returns",
            "anchor_reaction_cutoff_et": REACTION_CUTOFF_ET,
            "earliest_neighbor_entry_et": EARLIEST_ENTRY_ET,
            "exits": EXITS, "cost_bps_round_trip": COST_BPS,
            "attention_variable": "strictly pre-event GST z (weeks closing before the event), "
                                  "the PR #24 construction",
            "overlapping_spike_classification_used": False,
            "required_history_start": REQUIRED_HISTORY_START,
        },
        "data_probe": {
            "five_minute_probes": probes,
            "max_days_back_with_bars": max_days,
            "deep_history_available": intraday_ok,
            "recent_window_available": bool(shallow),
            "providers": credentials_present(),
            "repository_intraday_bars_present": False,
            "repository_daily_columns": ["Date", "Open", "Close"],
        },
    }

    if not intraday_ok:
        res["decision_label"] = "DATA_UNAVAILABLE"
        res["reason"] = (
            "Historical 5-minute bars could not be obtained for the required period. The public "
            f"chart endpoint serves 5-minute data only for roughly the last {max_days} days "
            "(90-day and longer requests return HTTP 422); the repository contains daily "
            "Open/Close only; no Alpaca credentials are present in the environment; and the "
            "other providers probed require an API key that is not configured. The 09:35 "
            "reaction read and 09:40 entry this design requires cannot be constructed.")
        res["substitution_refused"] = (
            "Daily open/close was NOT substituted. Reading the anchor's direction from the "
            "opening gap and entering neighbors at that same open is an impossible trade.")
        res["what_would_unblock_this"] = [
            "APCA_API_KEY_ID / APCA_API_SECRET_KEY for the already-implemented Alpaca provider",
            "any keyed intraday vendor (Polygon, Tiingo, Alpha Vantage, Finnhub)",
            "a committed historical 5-minute bar archive for the anchors, neighbors, SMH and SPY",
        ]
        res["computed_returns"] = None
        res["anchor_events_evaluated"] = 0
        RESULTS.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
        print("DECISION: DATA_UNAVAILABLE")
        print(f"  max 5-minute history available: ~{max_days} days "
              f"(need back to {REQUIRED_HISTORY_START})")
        for p in probes:
            print(f"    probe {p['days_back']:>4}d -> bars={p['bars']}"
                  + (f"  {p.get('error','')}" if p.get("error") else ""))
        print("  daily open/close substitution REFUSED (impossible trade)")
        return 0

    # Intraday history exists: the study proceeds. Not reached in this environment.
    res["decision_label"] = "PENDING_COMPUTATION"
    RESULTS.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("5-minute history available; event computation would proceed here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
