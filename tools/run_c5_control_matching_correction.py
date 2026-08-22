#!/usr/bin/env python3
"""Phase 3 corrective run for the C5 matched-control defects.

Implements CORRECTIVE_DESIGN_v1.0_FROZEN_2026-08-22.md exactly. Two rules are
added to the original matcher and nothing else is re-specified:

    E1  identity distinctness  -- control identity != treated identity
    E2  global uniqueness      -- each control identity used at most once

This is a RESTRICTION of the committed matched set, not a re-match: the control
candidate pool is not committed, so a treated event that loses its control is
dropped rather than re-paired (frozen design section 5).

Reads only committed artifacts. Writes one results JSON. Changes no original.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Correction_Overlays" / "2026-08-22_C5_Control_Matching" / "CORRECTED_RESULTS_v1.0.json"
POP = ROOT / "Live Signal Engine" / "C5_PostEarnings_Population.csv"


def _load_tool():
    p = ROOT / "tools" / "run_retrospective_market_response_decomposition.py"
    spec = importlib.util.spec_from_file_location("dec", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cr2_mean(diff: np.ndarray, clusters: np.ndarray, tool) -> dict:
    """Mean of `diff` with CR2/BRL ticker-clustered SE and Satterthwaite df."""
    X = np.ones((len(diff), 1))
    beta, V, _ = tool.cr_vcov(X, diff.astype(float), clusters, "CR2")
    c = np.array([1.0])
    se = float(math.sqrt(max(c @ V @ c, 0.0)))
    dfree = tool.satterthwaite_df(X, clusters, c)
    b = float(beta[0])
    t = b / se if se > 0 else float("nan")
    try:
        from scipy import stats
        p = float(2 * stats.t.sf(abs(t), dfree))
        crit = float(stats.t.ppf(0.975, dfree))
    except Exception:                                               # noqa: BLE001
        p, crit = float("nan"), 1.96
    return {"coef_pp": round(b, 4), "cr2_se_pp": round(se, 4),
            "satterthwaite_df": round(float(dfree), 3), "t_stat": round(t, 3),
            "p_value": None if math.isnan(p) else round(p, 5),
            "ci95_pp": [round(b - crit * se, 4), round(b + crit * se, 4)],
            "n_clusters": int(len(set(clusters)))}


def welch(a: np.ndarray, b: np.ndarray) -> dict:
    va, vb, na, nb = a.var(ddof=1), b.var(ddof=1), len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    t = (a.mean() - b.mean()) / se
    df = (va / na + vb / nb) ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    try:
        from scipy import stats
        p = float(2 * stats.t.sf(abs(t), df))
    except Exception:                                               # noqa: BLE001
        p = float("nan")
    return {"mean_treated_pp": round(float(a.mean()), 4), "n_treated": int(na),
            "mean_control_pp": round(float(b.mean()), 4), "n_control": int(nb),
            "difference_pp": round(float(a.mean() - b.mean()), 4),
            "t_stat": round(float(t), 3), "welch_df": round(float(df), 2),
            "p_value": None if math.isnan(p) else round(p, 5)}


def main() -> int:
    tool = _load_tool()
    ev, drops = tool.build_events()
    ev["abs_day"] = ev["day_return"].abs() * 100.0

    anchors = pd.read_csv(POP, parse_dates=["anchor"])[["pair_id", "role", "anchor"]]
    ev = ev.merge(anchors, on=["pair_id", "role"], how="left")

    sig = ev[ev.role == "signal"].set_index("pair_id")
    ctl = ev[ev.role == "control"].set_index("pair_id")
    pids = sorted(set(sig.index) & set(ctl.index))

    pairs = []
    for pid in pids:
        s, c = sig.loc[pid], ctl.loc[pid]
        pairs.append({
            "pair_id": int(pid), "ticker": s["ticker"],
            "t_id": (s["ticker"], s["earnings_date"]),
            "c_id": (c["ticker"], c["earnings_date"]),
            "t_abs": float(s["abs_day"]), "c_abs": float(c["abs_day"]),
            "t_pre": abs(float(s["pre_drift"])) * 100.0,
            "c_pre": abs(float(c["pre_drift"])) * 100.0,
            "t_bmo": s["bmo_amc"], "c_bmo": c["bmo_amc"],
            "t_date": s["earnings_date"], "c_date": c["earnings_date"],
            "sep_days": abs((pd.Timestamp(c["anchor"]) - pd.Timestamp(s["anchor"])).days),
        })
    n_start = len(pairs)

    # ---- E1: identity distinctness -------------------------------------
    self_matched = [p for p in pairs if p["t_id"] == p["c_id"]]
    stage1 = [p for p in pairs if p["t_id"] != p["c_id"]]

    # ---- E2: global uniqueness, deterministic award (frozen section 4) --
    by_control: dict[tuple, list] = {}
    for p in stage1:
        by_control.setdefault(p["c_id"], []).append(p)
    kept, dropped_uniq = [], []
    for cid, claimants in by_control.items():
        claimants.sort(key=lambda p: (p["sep_days"], p["t_date"], p["ticker"], p["pair_id"]))
        kept.append(claimants[0])
        dropped_uniq.extend(claimants[1:])
    kept.sort(key=lambda p: (p["ticker"], p["t_date"], p["pair_id"]))

    def arr(rows, k):
        return np.array([r[k] for r in rows], dtype=float)

    def clus(rows):
        return np.array([r["ticker"] for r in rows])

    d_primary = arr(kept, "t_abs") - arr(kept, "c_abs")
    primary = cr2_mean(d_primary, clus(kept), tool)
    naive_t = float(d_primary.mean() / (d_primary.std(ddof=1) / math.sqrt(len(d_primary))))

    # ---- sensitivities --------------------------------------------------
    d_a = arr(stage1, "t_abs") - arr(stage1, "c_abs")
    sens_a = cr2_mean(d_a, clus(stage1), tool)
    sens_b = welch(arr(kept, "t_abs"), arr(kept, "c_abs"))

    loo = {}
    for tk in sorted({p["ticker"] for p in kept}):
        sub = [p for p in kept if p["ticker"] != tk]
        if len({p["ticker"] for p in sub}) < 2:
            continue
        loo[tk] = round(float((arr(sub, "t_abs") - arr(sub, "c_abs")).mean()), 4)

    overlap = {("LDOS", "2021-08-03"), ("LDOS", "2023-10-31"), ("NFLX", "2022-01-20"),
               ("NFLX", "2023-01-19"), ("NKE", "2024-03-21"), ("QCOM", "2025-02-05"),
               ("SBUX", "2025-01-28"), ("STZ", "2025-01-10")}
    sub_d = [p for p in kept if p["t_id"] not in overlap and p["c_id"] not in overlap]
    sens_d = cr2_mean(arr(sub_d, "t_abs") - arr(sub_d, "c_abs"), clus(sub_d), tool)

    balance = {
        "mean_abs_pre_drift_treated_pp": round(float(arr(kept, "t_pre").mean()), 4),
        "mean_abs_pre_drift_control_pp": round(float(arr(kept, "c_pre").mean()), 4),
        "same_ticker_pairs": int(sum(1 for p in kept if p["t_id"][0] == p["c_id"][0])),
        "bmo_amc_concordant_pairs": int(sum(1 for p in kept if p["t_bmo"] == p["c_bmo"])),
        "treated_year_distribution": dict(sorted(
            pd.Series([p["t_date"][:4] for p in kept]).value_counts().items())),
        "control_year_distribution": dict(sorted(
            pd.Series([p["c_date"][:4] for p in kept]).value_counts().items())),
    }

    res = {
        "artifact": "C5_CONTROL_MATCHING_CORRECTED_RESULTS",
        "version": "1.0",
        "status": "RETROSPECTIVE_DEVELOPMENT_ONLY_NOT_HYP01_CONFIRMATION",
        "design": "CORRECTIVE_DESIGN_v1.0_FROZEN_2026-08-22.md",
        "supersedes": "Q1_abs_move_high_vs_control in RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json",
        "method_note": "Restriction of the committed matched set, not a re-match; "
                       "the control candidate pool is not committed.",
        "sample": {
            "pairs_before_correction": n_start,
            "dropped_self_match_E1": len(self_matched),
            "dropped_no_unique_control_E2": len(dropped_uniq),
            "surviving_pairs": len(kept),
            "distinct_control_identities": len({p["c_id"] for p in kept}),
            "distinct_treated_identities": len({p["t_id"] for p in kept}),
            "observations_lost_vs_original_treated_arm": n_start - len(kept),
        },
        "original_for_comparison": {
            "statistic": "unpaired Welch, high vs control",
            "high_mean_abs_pct": 7.8871, "n_high": 152,
            "control_mean_abs_pct": 6.4459, "n_control": 133,
            "difference_pp": 1.4411, "t_stat": 2.138,
            "citation_status": "SUPERSEDED_BY_THIS_ARTIFACT",
        },
        "primary": {
            "estimand": "ATT on |day_return|, percentage points",
            "statistic": "mean paired difference over surviving matched pairs",
            "n_pairs": len(kept),
            "mean_paired_difference_pp": round(float(d_primary.mean()), 4),
            "naive_paired_t_for_reference_only": round(naive_t, 3),
            "inference": {"vcov": "CR2 (BRL)", "cluster_unit": "ticker",
                          "df_method": "coefficient-specific Satterthwaite", **primary},
        },
        "sensitivity": {
            "a_reuse_retained_self_match_excluded": {"n_pairs": len(stage1), **sens_a},
            "b_unpaired_welch_on_corrected_arms": sens_b,
            "c_leave_one_ticker_out_mean_paired_diff_pp": {
                "n_refits": len(loo), "min": min(loo.values()) if loo else None,
                "max": max(loo.values()) if loo else None, "by_excluded_ticker": loo},
            "d_excluding_8_overlap_identities": {"n_pairs": len(sub_d), **sens_d},
            "e_balance": balance,
        },
        "dropped_detail": {
            "self_matched": [{"pair_id": p["pair_id"], "ticker": p["t_id"][0],
                              "earnings_date": p["t_id"][1]} for p in
                             sorted(self_matched, key=lambda x: x["pair_id"])],
            "no_unique_control": [{"pair_id": p["pair_id"], "ticker": p["ticker"],
                                   "treated_date": p["t_date"],
                                   "lost_control": list(p["c_id"])} for p in
                                  sorted(dropped_uniq, key=lambda x: x["pair_id"])],
        },
    }
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("sample", "primary")}, indent=2))
    print(f"\nwritten: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
