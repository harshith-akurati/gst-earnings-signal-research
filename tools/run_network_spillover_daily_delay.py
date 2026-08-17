#!/usr/bin/env python3
"""Daily-delay network spillover: anchor reaction through close(T) -> neighbors from open(T+1).

EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY. Touches no HYP-01 lock, registry,
F5 artifact, universe constant or prospective observation.

WHY THIS IS EXECUTABLE
  The anchor's benchmark-adjusted return through close(T) is fully known AFTER the
  close of session T. Neighbors are entered at open(T+1) - the next session's opening
  order, placed after the signal exists. Neighbor open(T) is NEVER used as an entry.

FROZEN DESIGN
  Anchors        NVDA, AMD, INTC
  Neighbors      TSM ASML AMAT LRCX AVGO ANET DELL SMCI MSFT AMZN GOOGL META
  Event day T    from SEC 8-K item 2.02 acceptance time: accepted after 16:00 ET -> next
                 session; accepted before 09:30 ET -> that session; otherwise next session
  Anchor signal  sign( [close(T)/close(T-1) - 1] - [SMH close(T)/close(T-1) - 1] )
  Neighbor entry open(T+1)
  Exits          close(T+1) and close(T+3)
  Neighbor R     [neighbor exit/open(T+1) - 1] - [SMH exit/open(T+1) - 1]   (SPY = sensitivity)
  Cost           10 bps round trip, fixed
  Attention      strictly pre-event GST z, the PR #24 construction: weeks CLOSING before
                 the event day only. The overlapping spike classification is never used.
  Primary        anchor-event level: sign(anchor) x mean(neighbor abnormal). Neighbor rows
                 are descriptive only - they are not independent observations.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Live Signal Engine" / "Network_Spillover_Daily"
OUT.mkdir(parents=True, exist_ok=True)
PRICES = OUT / "daily_prices_v1.0.csv"
EVENTS_CSV = OUT / "anchor_earnings_events_v1.0.csv"
REL = OUT / "network_relationships_v1.0.csv"
RESULTS = ROOT / "NETWORK_SPILLOVER_DAILY_RESULTS_v1.0.json"

ANCHORS = ["NVDA", "AMD", "INTC"]
NEIGHBORS = ["TSM", "ASML", "AMAT", "LRCX", "AVGO", "ANET", "DELL", "SMCI",
             "MSFT", "AMZN", "GOOGL", "META"]
BENCH, SENS = "SMH", "SPY"
ALL_SYMS = ANCHORS + NEIGHBORS + [BENCH, SENS]

COST_BPS = 10.0
EXITS = {"close_T1": 1, "close_T3": 3}
START, END = "2021-01-01", "2026-01-01"
GST_BASELINE_WEEKS, GST_MIN_WEEKS = 52, 20
GST_HIGH_Z = 1.0                      # frozen before any outcome was computed
UA_SEC = {"User-Agent": "gst-earnings-signal-research academic research (hakurati11@gmail.com)"}
UA_MKT = {"User-Agent": "Mozilla/5.0 (gst-earnings-signal-research exploratory network study)"}


def fetch_daily(sym: str) -> pd.DataFrame:
    p1 = int(pd.Timestamp(START).timestamp())
    p2 = int(pd.Timestamp(END).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA_MKT), timeout=60) as r:
        b = json.loads(r.read())
    res = b["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    d = pd.DataFrame({"Date": pd.to_datetime(res["timestamp"], unit="s").normalize(),
                      "Open": q["open"], "Close": q["close"]})
    d["symbol"] = sym
    return d.dropna().drop_duplicates("Date").sort_values("Date")


def load_prices() -> pd.DataFrame:
    if PRICES.exists():
        d = pd.read_csv(PRICES, parse_dates=["Date"])
        if set(d.symbol.unique()) >= set(ALL_SYMS):
            return d
    frames = []
    for s in ALL_SYMS:
        frames.append(fetch_daily(s))
        time.sleep(0.3)
    d = pd.concat(frames, ignore_index=True)
    d.to_csv(PRICES, index=False, lineterminator="\n")
    return d


def fetch_anchor_events() -> pd.DataFrame:
    if EVENTS_CSV.exists():
        return pd.read_csv(EVENTS_CSV, parse_dates=["filing_date"])
    ct = json.loads(urllib.request.urlopen(
        urllib.request.Request("https://www.sec.gov/files/company_tickers.json", headers=UA_SEC),
        timeout=90).read())
    cik = {v["ticker"]: int(v["cik_str"]) for v in ct.values()}
    rows = []
    for s in ANCHORS:
        d = json.loads(urllib.request.urlopen(
            urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik[s]:010d}.json",
                                   headers=UA_SEC), timeout=90).read())
        rec = d["filings"]["recent"]
        for form, items, fdate, acc in zip(rec["form"], rec["items"], rec["filingDate"],
                                           rec["acceptanceDateTime"]):
            if form == "8-K" and "2.02" in (items or "") and START <= fdate < END:
                rows.append({"anchor": s, "cik": cik[s], "filing_date": fdate,
                             "acceptance_utc": acc, "items": items})
        time.sleep(0.2)
    e = pd.DataFrame(rows).drop_duplicates(subset=["anchor", "filing_date"])
    e.to_csv(EVENTS_CSV, index=False, lineterminator="\n")
    return e


def session_T(px: pd.DataFrame, filing_date, acceptance_utc) -> int | None:
    """SEC acceptance time -> the session that first prices the release."""
    ts = pd.Timestamp(acceptance_utc)
    if ts.tzinfo is None:                       # SEC acceptance stamps are ET
        et = ts
    else:
        et = ts.tz_convert("America/New_York").tz_localize(None)
    d = pd.Timestamp(filing_date).normalize()
    idx = px.index[px.Date == d]
    after_close = et.hour >= 16
    before_open = et.hour < 9 or (et.hour == 9 and et.minute < 30)
    if len(idx) == 1 and before_open:
        return int(idx[0])                       # BMO: prices on the filing session
    nxt = px.index[px.Date > d]                  # AMC or non-session: next session
    return int(nxt[0]) if len(nxt) else None


def gst_z_pre(weekly: dict[str, pd.DataFrame], sym: str, event_day) -> float:
    g = weekly.get(sym)
    if g is None:
        return float("nan")
    closed = g[g.week_close < pd.Timestamp(event_day)]
    if len(closed) < GST_MIN_WEEKS + 1:
        return float("nan")
    latest = float(closed.value.values[-1])
    base = closed.value.values[-(GST_BASELINE_WEEKS + 1):-1]
    if len(base) < GST_MIN_WEEKS or np.std(base, ddof=1) == 0:
        return float("nan")
    return float((latest - np.mean(base)) / np.std(base, ddof=1))


def load_weekly_gst() -> dict[str, pd.DataFrame]:
    out: dict[str, list] = {}
    for f in glob.glob(str(ROOT / "GST Data" / "Weekly Data*" / "*.csv")):
        t = os.path.basename(f).rsplit("_", 1)[0]
        if t not in ANCHORS:
            continue
        try:
            d = pd.read_csv(f)
        except Exception:
            continue
        if "Week" in d.columns and t in d.columns:
            out.setdefault(t, []).append(d[["Week", t]].rename(columns={t: "value"}))
    res = {}
    for t, fr in out.items():
        d = pd.concat(fr, ignore_index=True)
        d["Week"] = pd.to_datetime(d["Week"])
        d = d.dropna().drop_duplicates("Week").sort_values("Week").reset_index(drop=True)
        d["week_close"] = d["Week"] + pd.Timedelta(days=6)
        res[t] = d
    return res


def ci95(x: np.ndarray) -> dict:
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    n = len(x)
    if n < 2:
        return {"n": n, "mean_pct": None, "ci95_pct": None, "t_stat": None}
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(n)
    return {"n": n, "mean_pct": round(100 * m, 4),
            "median_pct": round(100 * float(np.median(x)), 4),
            "ci95_pct": [round(100 * (m - 1.96 * se), 4), round(100 * (m + 1.96 * se), 4)],
            "t_stat": round(m / se, 3) if se > 0 else None,
            "hit_rate_pct": round(100 * float((x > 0).mean()), 2)}


def main() -> int:
    px_all = load_prices()
    rel = pd.read_csv(REL)
    ev = fetch_anchor_events()
    weekly = load_weekly_gst()
    P = {s: g.reset_index(drop=True) for s, g in px_all.groupby("symbol")}
    bench, sens = P[BENCH], P[SENS]

    def win_ret(d: pd.DataFrame, i0: int, i1: int, from_open: bool) -> float | None:
        if i0 < 0 or i1 >= len(d):
            return None
        a = d.Open.values[i0] if from_open else d.Close.values[i0]
        return float(d.Close.values[i1] / a - 1.0)

    def align(d: pd.DataFrame, date) -> int | None:
        i = d.index[d.Date == pd.Timestamp(date)]
        return int(i[0]) if len(i) else None

    events, neigh_rows, dropped = [], [], []
    for _, r in ev.iterrows():
        apx = P.get(r.anchor)
        if apx is None:
            dropped.append((r.anchor, r.filing_date, "no anchor prices"))
            continue
        T = session_T(apx, r.filing_date, r.acceptance_utc)
        if T is None or T < 1 or T + max(EXITS.values()) >= len(apx):
            dropped.append((r.anchor, str(r.filing_date)[:10], "session window incomplete"))
            continue
        edate = pd.Timestamp(apx.Date.values[T])
        bi = align(bench, edate)
        if bi is None or bi < 1:
            dropped.append((r.anchor, str(edate.date()), "benchmark not aligned on T"))
            continue
        a_ret = apx.Close.values[T] / apx.Close.values[T - 1] - 1.0
        b_ret = bench.Close.values[bi] / bench.Close.values[bi - 1] - 1.0
        a_abn = float(a_ret - b_ret)
        sgn = 1.0 if a_abn > 0 else (-1.0 if a_abn < 0 else 0.0)
        if sgn == 0.0:
            dropped.append((r.anchor, str(edate.date()), "zero anchor abnormal return"))
            continue

        entry_date = pd.Timestamp(apx.Date.values[T + 1])
        per_exit: dict[str, list] = {k: [] for k in EXITS}
        per_exit_sens: dict[str, list] = {k: [] for k in EXITS}
        for _, e in rel[rel.anchor == r.anchor].iterrows():
            npx = P.get(e.neighbor)
            if npx is None or e.neighbor in ANCHORS:
                continue
            ni = align(npx, entry_date)
            bj = align(bench, entry_date)
            sj = align(sens, entry_date)
            if ni is None or bj is None or sj is None:
                continue
            for k, off in EXITS.items():
                nr = win_ret(npx, ni, ni + off - 1, True)
                br = win_ret(bench, bj, bj + off - 1, True)
                sr = win_ret(sens, sj, sj + off - 1, True)
                if nr is None or br is None:
                    continue
                per_exit[k].append(nr - br)
                if sr is not None:
                    per_exit_sens[k].append(nr - sr)
                neigh_rows.append({"anchor": r.anchor, "event_day": str(edate.date()),
                                   "neighbor": e.neighbor, "edge_type": e.edge_type,
                                   "graph_distance": int(e.graph_distance), "exit": k,
                                   "neighbor_abnormal": nr - br,
                                   "signed_abnormal": sgn * (nr - br)})
        if not per_exit["close_T1"]:
            dropped.append((r.anchor, str(edate.date()), "no eligible neighbors"))
            continue
        rec = {"anchor": r.anchor, "filing_date": str(r.filing_date)[:10],
               "acceptance_utc": str(r.acceptance_utc), "event_day": str(edate.date()),
               "entry_day": str(entry_date.date()), "year": str(edate.year),
               "anchor_abnormal_close_T_pct": round(100 * a_abn, 4), "anchor_sign": sgn,
               "n_neighbors": len(per_exit["close_T1"]),
               "gst_z_pre": gst_z_pre(weekly, r.anchor, edate)}
        for k in EXITS:
            rec[f"spillover_{k}"] = sgn * float(np.mean(per_exit[k])) if per_exit[k] else None
            rec[f"spillover_{k}_spy"] = (sgn * float(np.mean(per_exit_sens[k]))
                                         if per_exit_sens[k] else None)
            rec[f"unsigned_{k}"] = float(np.mean(per_exit[k])) if per_exit[k] else None
        events.append(rec)

    E = pd.DataFrame(events).sort_values("event_day").reset_index(drop=True)
    N = pd.DataFrame(neigh_rows)
    E.to_csv(OUT / "anchor_event_spillovers_v1.0.csv", index=False, lineterminator="\n")

    cost = COST_BPS / 10000.0
    res: dict = {
        "artifact": "NETWORK_SPILLOVER_DAILY_RESULTS", "version": "1.0",
        "status": "EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY",
        "touches_hyp01_or_prospective_state": False,
        "executable_because": ("the anchor's benchmark-adjusted return through close(T) is known "
                               "after that close; neighbors are entered at open(T+1). Neighbor "
                               "open(T) is never used as an entry."),
        "design": {"anchors": ANCHORS, "neighbors": NEIGHBORS, "benchmark": BENCH,
                   "sensitivity_benchmark": SENS, "exits": list(EXITS),
                   "cost_bps_round_trip": COST_BPS,
                   "event_session_rule": "SEC 8-K item 2.02 acceptance time; after 16:00 ET -> next "
                                         "session, before 09:30 ET -> that session",
                   "gst_feature": "strictly pre-event z from weeks closing before the event day",
                   "gst_high_threshold_z": GST_HIGH_Z,
                   "overlapping_spike_classification_used": False,
                   "primary_observation": "anchor event, not neighbor row"},
        "sample": {"sec_earnings_filings": int(len(ev)), "usable_anchor_events": int(len(E)),
                   "dropped": len(dropped),
                   "drop_reasons": pd.Series([d[2] for d in dropped]).value_counts().to_dict() if dropped else {},
                   "neighbor_rows_descriptive": int(len(N)),
                   "date_range": [E.event_day.min(), E.event_day.max()] if len(E) else None,
                   "by_anchor": E.anchor.value_counts().to_dict() if len(E) else {}},
    }

    if len(E) < 5:
        res["decision_label"] = "INSUFFICIENT_ANCHOR_EVENTS"
        RESULTS.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
        print("INSUFFICIENT_ANCHOR_EVENTS", len(E))
        return 0

    prim = "close_T1"
    res["primary_exit"] = prim
    res["results"] = {}
    for k in EXITS:
        g = E[f"spillover_{k}"].dropna().values
        res["results"][k] = {"gross": ci95(g), "net": ci95(g - cost),
                             "spy_sensitivity_gross": ci95(E[f"spillover_{k}_spy"].dropna().values)}

    # GST split (anchors with weekly GST coverage only)
    hasg = E[E.gst_z_pre.notna()]
    hi = hasg[hasg.gst_z_pre >= GST_HIGH_Z]
    lo = hasg[hasg.gst_z_pre < GST_HIGH_Z]
    res["gst"] = {
        "events_with_gst": int(len(hasg)),
        "anchors_with_gst_coverage": sorted(hasg.anchor.unique().tolist()),
        "anchors_without_gst_coverage": sorted(set(E.anchor) - set(hasg.anchor)),
        "high_gst_events": int(len(hi)), "low_gst_events": int(len(lo)),
        "high_net": ci95(hi[f"spillover_{prim}"].dropna().values - cost),
        "low_net": ci95(lo[f"spillover_{prim}"].dropna().values - cost),
    }
    if len(hasg) > 3 and hasg.gst_z_pre.nunique() > 2:
        x = hasg.gst_z_pre.values.astype(float)
        y = hasg[f"spillover_{prim}"].values.astype(float)
        b1, b0 = np.polyfit(x, y, 1)
        r = float(np.corrcoef(x, y)[0, 1])
        res["gst"]["continuous_interaction"] = {
            "slope_pct_per_z": round(100 * float(b1), 4), "intercept_pct": round(100 * float(b0), 4),
            "correlation": round(r, 4), "n": int(len(x))}

    res["by_anchor"] = {a: ci95(E[E.anchor == a][f"spillover_{prim}"].dropna().values - cost)
                        for a in sorted(E.anchor.unique())}
    if len(N):
        Np = N[N.exit == prim]
        res["descriptive_by_edge_type"] = {
            k: {"n_rows": int(len(v)), "mean_signed_pct": round(100 * float(v.signed_abnormal.mean()), 4)}
            for k, v in Np.groupby("edge_type")}
        res["descriptive_by_graph_distance"] = {
            str(k): {"n_rows": int(len(v)), "mean_signed_pct": round(100 * float(v.signed_abnormal.mean()), 4)}
            for k, v in Np.groupby("graph_distance")}
        res["pseudo_replication_note"] = ("edge-type and distance tables are neighbor-level and "
                                          "descriptive only; primary inference is anchor-event level")

    med = sorted(E.event_day)[len(E) // 2]
    res["older_vs_newer"] = {
        "split_at": med,
        "older_net": ci95(E[E.event_day <= med][f"spillover_{prim}"].dropna().values - cost),
        "newer_net": ci95(E[E.event_day > med][f"spillover_{prim}"].dropna().values - cost)}

    # event-level permutation of the anchor sign
    uns = E[f"unsigned_{prim}"].dropna().values
    obs = float((E[f"spillover_{prim}"].dropna().values).mean())
    rng = np.random.default_rng(12345)
    draws = np.array([float((rng.choice([-1.0, 1.0], size=len(uns)) * uns).mean())
                      for _ in range(10000)])
    res["comparators"] = {
        "randomized_anchor_sign_permutation": {
            "n_permutations": 10000, "observed_mean_pct": round(100 * obs, 4),
            "permuted_mean_pct": round(100 * float(draws.mean()), 4),
            "permuted_sd_pct": round(100 * float(draws.std(ddof=1)), 4),
            "two_sided_p": round(float((np.abs(draws) >= abs(obs)).mean()), 4)},
        "all_anchor_events_net": ci95(E[f"spillover_{prim}"].dropna().values - cost),
        "no_trade": {"mean_pct": 0.0, "n": 0},
        "smh_benchmark": "neighbor returns are already benchmark-adjusted against SMH",
    }

    net = res["results"][prim]["net"]
    perm_p = res["comparators"]["randomized_anchor_sign_permutation"]["two_sided_p"]
    spill = bool(net["ci95_pct"] and net["ci95_pct"][0] > 0 and perm_p < 0.05)
    hn, ln = res["gst"]["high_net"], res["gst"]["low_net"]
    gst_better = bool(hn.get("mean_pct") is not None and ln.get("mean_pct") is not None
                      and hn["ci95_pct"] and hn["ci95_pct"][0] > 0
                      and hn["mean_pct"] > ln["mean_pct"])
    if len(E) < 5:
        label = "INSUFFICIENT_ANCHOR_EVENTS"
    elif spill and gst_better:
        label = "GST_SELECTS_STRONGER_DAILY_SPILLOVERS"
    elif spill:
        label = "DAILY_SPILLOVER_EXISTS_BUT_GST_ADDS_NOTHING"
    elif gst_better:
        label = "GST_SELECTS_STRONGER_DAILY_SPILLOVERS"
    else:
        label = "NO_DAILY_NETWORK_SPILLOVER"
    res["decision_label"] = label
    res["models_fitted"] = False
    res["models_note"] = (f"{len(E)} anchor events survived; machine-learning models were permitted "
                          "at >=30 but this brief's report is the fixed event-level analysis, so "
                          "none was fitted and no feature or hyperparameter search was run.")
    RESULTS.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    if len(N):
        N.to_csv(OUT / "neighbor_rows_descriptive_v1.0.csv", index=False, lineterminator="\n")

    print(f"usable anchor events: {len(E)}  (by anchor: {res['sample']['by_anchor']})")
    for k in EXITS:
        print(f"  {k}: gross {res['results'][k]['gross']['mean_pct']}%  "
              f"net {res['results'][k]['net']['mean_pct']}%  "
              f"CI {res['results'][k]['net']['ci95_pct']}  t={res['results'][k]['net']['t_stat']}")
    print(f"  high-GST net {hn.get('mean_pct')}% (n={hn.get('n')})  "
          f"low-GST net {ln.get('mean_pct')}% (n={ln.get('n')})")
    print(f"  permutation two-sided p: {perm_p}")
    print(f"  DECISION: {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
