#!/usr/bin/env python3
"""Phase 1: deterministic parser-development sample + later-XBRL audit validation.

Post-entry returns are NEVER inspected here. The later 10-Q XBRL fact is an AUDIT
REFERENCE only: it cannot influence which Exhibit value is selected, cannot replace an
Exhibit value, and never enters a predictive feature.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from exhibit99_parser import parse_exhibit  # noqa: E402

OUT = ROOT / "Live Signal Engine" / "PIT_Earnings_Surprise_v2"
CACHE = OUT / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)
VALID = OUT / "extraction_validation_v1.0.json"
EXTRACT = OUT / "exhibit_extractions_v1.0.csv"

UA = {"User-Agent": "gst-earnings-signal-research academic research (hakurati11@gmail.com)"}
DEV_PER_TICKER = 2
DEV_SEED = "PIT_EARNINGS_SURPRISE_V2_DEV_SAMPLE"     # fixed, recorded
TOL_REL, TOL_EPS = 0.005, 0.01
GATE = {"tickers": 18, "events": 180, "oos": 120, "oos_per_year": 30, "validation_rate": 0.90}


def get(url, cache_key, timeout=60):
    f = CACHE / cache_key
    if f.exists():
        return f.read_bytes()
    r = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        b = resp.read()
    f.write_bytes(b)
    time.sleep(0.11)
    return b


def dev_rank(ticker, fpe, accession):
    """Deterministic SHA-256 ranking of event identities; no reference to returns."""
    h = hashlib.sha256(f"{DEV_SEED}|{ticker}|{fpe}|{accession}".encode()).hexdigest()
    return h


def build_events():
    sys.path.insert(0, str(ROOT))
    from gst_market_response.constants import LOCKED_24_TICKER_UNIVERSE as U
    ct = json.loads(get("https://www.sec.gov/files/company_tickers.json", "cik.json"))
    cik = {v["ticker"]: int(v["cik_str"]) for v in ct.values()}
    rows = []
    for t in list(U):
        c = cik.get(t)
        if c is None:
            continue
        sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{c:010d}.json", f"sub_{t}.json"))
        rec = sub["filings"]["recent"]
        for form, items, fdate, acc, adt, pdoc in zip(
                rec["form"], rec["items"], rec["filingDate"], rec["accessionNumber"],
                rec["acceptanceDateTime"], rec["primaryDocument"]):
            if form == "8-K" and "2.02" in (items or "") and "2020-01-01" <= fdate < "2026-01-01":
                rows.append({"ticker": t, "cik": c, "accession": acc, "filing_date": fdate,
                             "acceptance": adt, "primary_doc": pdoc})
    return pd.DataFrame(rows), cik


def find_exhibit(cik, accession):
    accn = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accn}"
    idx = json.loads(get(f"{base}/index.json", f"ix_{accession}.json"))
    names = [i["name"] for i in idx["directory"]["item"]]

    def ok(n):
        ln = n.lower()
        if not ln.endswith((".htm", ".html", ".txt")):
            return False
        if "index" in ln or re.match(r"^r\d+\.htm", ln) or re.match(r"^\d{10}-\d\d-\d{6}", ln):
            return False
        return bool(re.search(r"99[-_.]?1", ln) or re.search(r"ex[-_]?99", ln))

    c = sorted([n for n in names if ok(n)],
               key=lambda n: (0 if re.search(r"99[-_.]?1", n.lower()) else 1, len(n), n))
    return (f"{base}/{c[0]}", c[0]) if c else (None, None)


def xbrl_reference(cik, ticker):
    """AUDIT REFERENCE ONLY. Never selects or replaces an Exhibit value."""
    f = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", f"cf_{ticker}.json"))
    g = f.get("facts", {}).get("us-gaap", {})

    def pick(names, unit="USD"):
        best, bn = {}, 0
        for cn in names:
            if cn not in g:
                continue
            for u, arr in g[cn]["units"].items():
                if unit not in u:
                    continue
                q = [x for x in arr if x.get("start") and x.get("end")
                     and 80 <= (pd.Timestamp(x["end"]) - pd.Timestamp(x["start"])).days <= 100]
                if len(q) > bn:
                    d = {}
                    for x in q:
                        k = x["end"]
                        if k not in d or pd.Timestamp(x["filed"]) < pd.Timestamp(d[k]["filed"]):
                            d[k] = x
                    best, bn = d, len(q)
        return best
    return (pick(["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                  "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"]),
            pick(["OperatingIncomeLoss"]),
            pick(["EarningsPerShareDiluted"], "USD/shares"))


def main() -> int:
    ev, cik = build_events()
    ev["rank_hash"] = [dev_rank(r.ticker, r.filing_date, r.accession) for r in ev.itertuples()]
    dev = (ev.sort_values(["ticker", "rank_hash"]).groupby("ticker").head(DEV_PER_TICKER)
             .reset_index(drop=True))
    dev_ids = set(zip(dev.ticker, dev.accession))

    rows = []
    for r in ev.itertuples():
        url, name = None, None
        try:
            url, name = find_exhibit(r.cik, r.accession)
        except Exception:
            pass
        rec = {"ticker": r.ticker, "cik": r.cik, "accession": r.accession,
               "filing_date": r.filing_date, "acceptance": r.acceptance,
               "exhibit_url": url, "exhibit_name": name,
               "in_dev_sample": (r.ticker, r.accession) in dev_ids}
        if url:
            try:
                raw = get(url, f"ex_{r.accession}_{name[:40]}")
                rec["exhibit_sha256"] = hashlib.sha256(raw).hexdigest()
                vals, diag = parse_exhibit(raw.decode("utf-8", "replace"))
                for k in ("revenue", "operating_income", "diluted_eps"):
                    v = vals.get(k)
                    rec[k] = v["value"] if v else None
                    rec[k + "_row"] = v["row_label"] if v else None
                    rec[k + "_col"] = v["column_label"] if v else None
                    rec[k + "_table"] = v["table_index"] if v else None
                rec["n_tables"] = diag["n_tables"]
            except Exception as e:                                # noqa: BLE001
                rec["parse_error"] = f"{type(e).__name__}"
        rows.append(rec)
    X = pd.DataFrame(rows)

    # ---- later-XBRL AUDIT validation (never feeds prediction) ----
    val = {"revenue": [0, 0], "operating_income": [0, 0], "diluted_eps": [0, 0]}
    contradicted, no_reference = {}, {}
    ref_rows = []
    for t, grp in X.groupby("ticker"):
        c = int(grp.cik.iloc[0])
        R, O, E = xbrl_reference(c, t)
        for r in grp.itertuples():
            fd = pd.Timestamp(r.filing_date)
            for comp, ref, tol_rel, tol_abs in (("revenue", R, TOL_REL, None),
                                                ("operating_income", O, TOL_REL, None),
                                                ("diluted_eps", E, None, TOL_EPS)):
                got = getattr(r, comp)
                if got is None or pd.isna(got):
                    continue
                val[comp][1] += 1
                cands = [(k, v) for k, v in ref.items()
                         if 0 <= (fd - pd.Timestamp(k)).days <= 75]
                ok, best = False, None
                for k, v in cands:
                    rv = float(v["val"])
                    if tol_abs is not None:
                        d = abs(got - rv)
                        good = d <= tol_abs
                    else:
                        good = abs(got - rv) <= tol_rel * max(abs(rv), 1e-9)
                    if good:
                        ok, best = True, (k, rv)
                        break
                if ok:
                    val[comp][0] += 1
                elif cands:
                    contradicted.setdefault(comp, 0)
                    contradicted[comp] += 1
                else:
                    no_reference.setdefault(comp, 0)
                    no_reference[comp] += 1
                ref_rows.append({"ticker": t, "accession": r.accession, "component": comp,
                                 "exhibit_value": got,
                                 "later_xbrl_value": best[1] if best else None,
                                 "later_xbrl_period_end": best[0] if best else None,
                                 "validated": bool(ok)})
    V = pd.DataFrame(ref_rows)
    X.to_csv(EXTRACT, index=False, lineterminator="\n")
    rates = {k: (round(v[0] / v[1], 4) if v[1] else 0.0) for k, v in val.items()}
    n2 = int((X[["revenue", "operating_income", "diluted_eps"]].notna().sum(axis=1) >= 2).sum())
    res = {"artifact": "PIT_EARNINGS_SURPRISE_V2_EXTRACTION_VALIDATION", "version": "1.0",
           "status": "EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY",
           "google_trends_used": False, "analyst_estimates_used": False,
           "later_xbrl_used_for_prediction": False,
           "later_xbrl_role": "audit reference only; cannot select, replace or feed a feature",
           "dev_sample": {"rule": f"SHA-256 rank of '{DEV_SEED}|ticker|fiscal_period|accession', "
                                  f"first {DEV_PER_TICKER} per ticker; no reference to returns",
                          "seed": DEV_SEED, "per_ticker": DEV_PER_TICKER, "n": int(len(dev)),
                          "tickers": int(dev.ticker.nunique())},
           "events_seen": int(len(X)), "with_exhibit": int(X.exhibit_url.notna().sum()),
           "extracted_counts": {k: int(X[k].notna().sum()) for k in
                                ("revenue", "operating_income", "diluted_eps")},
           "validation_counts": {k: {"validated": v[0], "compared": v[1]} for k, v in val.items()},
           "validation_rates": rates,
           "contradicted_by_reference": contradicted,
           "no_reference_available": no_reference,
           "validated_among_comparable": {
               k: (round(val[k][0] / (val[k][0] + contradicted.get(k, 0)), 4)
                   if (val[k][0] + contradicted.get(k, 0)) else None) for k in val},
           "rate_definition": ("validation_rates = validated / EXTRACTED, the gate's definition. "
                               "validated_among_comparable = validated / (validated + contradicted), "
                               "excluding extractions with no later-XBRL reference in window."),
           "events_with_2plus_components": n2,
           "tolerances": {"revenue_operating_income_relative": TOL_REL, "eps_absolute": TOL_EPS},
           "gate_thresholds": GATE}
    res["extraction_gate_passed"] = bool(
        X.ticker.nunique() >= GATE["tickers"] and n2 >= GATE["events"]
        and all(rates[k] >= GATE["validation_rate"] for k in rates))
    VALID.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    V.to_csv(OUT / "extraction_audit_rows_v1.0.csv", index=False, lineterminator="\n")
    print(f"events {len(X)} exhibits {int(X.exhibit_url.notna().sum())} 2+components {n2}")
    print("extracted:", res["extracted_counts"])
    print("validation:", res["validation_counts"], rates)
    print("EXTRACTION GATE PASSED:", res["extraction_gate_passed"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
