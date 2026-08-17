#!/usr/bin/env python3
"""Earnings Information Absorption Engine (MVP).

EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY. Uses NO Google Trends data. Modifies no
GST artifact, HYP-01 lock, F5 state, registry, protocol, production constant or prior
result.

QUESTION. When the economic information in an SEC earnings release implies a larger
price reaction than the market initially produces, does that information-price gap
predict subsequent post-earnings abnormal returns?

CONSTRUCT GUARD. The measured quantity is an INFORMATION-PRICE RESIDUAL PROXY: the
difference between a model-implied reaction fitted on historical data and the observed
reaction. It is NOT intrinsic value, fair value, mispricing, analyst surprise, or proof
of underreaction. The numeric components are mechanical historical-expectation proxies.

================================ FROZEN_DESIGN ================================
Frozen before any post-entry target return was computed. This block was committed
before the outcome analysis was executed.

UNIVERSE      the existing locked 24-ticker universe (no post-hoc firm selection)
PERIOD        2020-2025 subject to coverage
EVENT ID      (ticker, fiscal_period_end, accession_number); duplicates REFUSED
              outright - never silently keep the first

REACTION SESSION, from SEC acceptance timestamp in US/Eastern:
  accepted < 09:30 ET on a trading day -> that day
  accepted during market hours          -> next trading day
  accepted >= 16:00 ET                  -> next trading day
  weekend / holiday                     -> next trading day
  Signal is formed only after the reaction session CLOSES.

TRADE TIMING  entry  = next trading day's OPEN after the reaction session
              exit-1 = 5th trading day's CLOSE after entry   (primary)
              exit-2 = 20th trading day's CLOSE after entry  (secondary)
              benchmark SPY over the identical open-to-close window
              cost 20 bps round trip

FEATURES (exhaustive; nothing else may enter a model)
  numeric_information_score = mean of available standardized components, requiring at
      least 2 of 3. Standardization uses the OUTER TRAINING FOLD ONLY.
      c1 revenue surprise proxy   = YoY revenue growth - median of the company's
                                    previous four observable YoY growth rates
      c2 operating-margin proxy   = operating margin - seasonal (same fiscal quarter)
                                    historical mean from previously filed data
      c3 diluted-EPS proxy        = diluted EPS - seasonal historical mean
      Every reference quarter must have been FILED before this event's acceptance
      timestamp. Missing components are marked missing, never imputed.
  text_novelty = 1 - cosine(current release, that ticker's immediately preceding
      release), HashingVectorizer (fixed, stateless - no corpus fitting)
  MARKET (known after the reaction session closes):
      reaction_abn_ret     reaction-session open->close return minus SPY
      reaction_abn_volume  reaction-session volume / mean volume of prior 20 sessions
      prior20_abn_ret      prior 20-session return minus SPY
      prior20_vol          prior 20-session realized volatility

STAGE 1  target = reaction_abn_ret
  null  : expanding training-fold mean with ticker indicators
  info  : numeric_information_score, text_novelty, their product, ticker indicators
  ridge; alpha from [0.1, 1.0, 10.0, 100.0] by INNER CHRONOLOGICAL validation inside
  the outer training fold only - never in-sample fit, never the outer test fold.
  information_price_gap = stage1_predicted_reaction - observed_reaction_return
  PASSES iff: MAE improvement >= 1% AND bootstrap 95% CI of (null - info) entirely
              above zero AND improvement positive in >= 2 of 3 test years.

STAGE 2  primary target = 5-day abnormal return from entry open; secondary = 20-day
  B : reaction_abn_ret, reaction_abn_volume, prior20_abn_ret, prior20_vol, ticker ind.
  C : B + information_price_gap + information_price_gap x text_novelty
  same ridge and same inner chronological alpha procedure.
  PASSES iff all: MAE improvement >= 1%; bootstrap 95% CI of (B - C) entirely above
  zero; C beats B in >= 2 of 3 years; pooled Spearman IC > 0.03; IC positive in >= 2
  of 3 years.

OUTER FOLDS   train <=2022 -> test 2023; <=2023 -> 2024; <=2024 -> 2025. Never random.
BOOTSTRAP     fixed seed, 2,000 draws, four-week calendar blocks, all events inside a
              sampled block retained together.
TRADING       run ONLY if Stage 1 and Stage 2 both pass. 80th percentile of |C
              predictions| from TRAINING data only; long positive, short negative;
              entry/exit as above; 20 bps round trip.
              PASSES iff >= 30 trades, mean net > 0, 95% CI entirely above zero, and
              net positive in >= 2 of 3 years.
FEASIBILITY   >= 18 tickers, >= 150 unique events, >= 100 OOS events, events in all of
              2023/2024/2025, >= 25 OOS events per test year. Otherwise DATA_UNAVAILABLE.
============================== END FROZEN_DESIGN ==============================
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Live Signal Engine" / "Earnings_Information_Absorption"
OUT.mkdir(parents=True, exist_ok=True)
PANEL = OUT / "event_panel_v1.0.csv"
PROV = OUT / "provenance_v1.0.json"
CACHE = OUT / "_cache"
CACHE.mkdir(exist_ok=True)
RESULTS = ROOT / "EARNINGS_INFORMATION_ABSORPTION_RESULTS_v1.0.json"

UA = {"User-Agent": "gst-earnings-signal-research academic research (hakurati11@gmail.com)"}
UA_MKT = {"User-Agent": "Mozilla/5.0 (gst-earnings-signal-research phase3)"}
ALPHAS = [0.1, 1.0, 10.0, 100.0]
TEST_YEARS = ["2023", "2024", "2025"]
COST = 0.0020
BOOT, BLOCK, SEED = 2000, 4, 20260817
EXIT1, EXIT2 = 5, 20
GATE = {"tickers": 18, "events": 150, "oos": 100, "oos_per_year": 25}

NUM_C = ["c_rev", "c_margin", "c_eps"]
MKT_F = ["reaction_abn_ret", "reaction_abn_volume", "prior20_abn_ret", "prior20_vol"]
S1_F = ["numeric_information_score", "text_novelty", "num_x_novelty"]
S2_C_EXTRA = ["information_price_gap", "gap_x_novelty"]


def get(url, headers=UA, cache_key=None, timeout=60):
    if cache_key:
        f = CACHE / cache_key
        if f.exists():
            return f.read_bytes()
    r = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        b = resp.read()
    if cache_key:
        (CACHE / cache_key).write_bytes(b)
    return b


def strip_html(b: bytes) -> str:
    t = b.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = re.sub(r"&[a-z#0-9]+;", " ", t)
    t = re.sub(r"(?i)edgar|sec\.gov|united states securities and exchange commission", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def daily(sym):
    ck = f"px_{sym}.json"
    p1 = int(pd.Timestamp("2019-06-01").timestamp())
    p2 = int(pd.Timestamp("2026-02-01").timestamp())
    b = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
            f"?period1={p1}&period2={p2}&interval=1d", UA_MKT, ck)
    res = json.loads(b)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    d = pd.DataFrame({"Date": pd.to_datetime(res["timestamp"], unit="s").normalize(),
                      "Open": q["open"], "Close": q["close"], "Volume": q["volume"]})
    return d.dropna(subset=["Open", "Close"]).drop_duplicates("Date").sort_values("Date").reset_index(drop=True)


def build_events():
    sys.path.insert(0, str(ROOT))
    from gst_market_response.constants import LOCKED_24_TICKER_UNIVERSE as U
    tick = list(U)
    ct = json.loads(get("https://www.sec.gov/files/company_tickers.json", UA, "cik.json"))
    cik = {v["ticker"]: int(v["cik_str"]) for v in ct.values()}
    hv = HashingVectorizer(n_features=2 ** 18, alternate_sign=False, norm="l2",
                           stop_words="english")
    rows, prov = [], []
    for t in tick:
        c = cik.get(t)
        if c is None:
            continue
        sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{c:010d}.json", UA, f"sub_{t}.json"))
        rec = sub["filings"]["recent"]
        ev = []
        for form, items, fdate, acc, adt, pdoc in zip(
                rec["form"], rec["items"], rec["filingDate"], rec["accessionNumber"],
                rec["acceptanceDateTime"], rec["primaryDocument"]):
            if form == "8-K" and "2.02" in (items or "") and "2020-01-01" <= fdate < "2026-01-01":
                ev.append({"ticker": t, "cik": c, "accession": acc, "filing_date": fdate,
                           "acceptance": adt, "primary_doc": pdoc})
        # XBRL facts, filed-date aware
        facts = json.loads(get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c:010d}.json",
                               UA, f"cf_{t}.json"))
        g = facts.get("facts", {}).get("us-gaap", {})

        def series(concepts, unit="USD"):
            best, bn = [], 0
            for cn in concepts:
                if cn not in g:
                    continue
                for u, arr in g[cn]["units"].items():
                    if unit not in u:
                        continue
                    q = [x for x in arr if x.get("start") and x.get("end") and x.get("filed")
                         and 80 <= (pd.Timestamp(x["end"]) - pd.Timestamp(x["start"])).days <= 100]
                    if len(q) > bn:
                        best, bn = [(cn, x) for x in q], len(q)
            return best

        rev = series(["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                      "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet"])
        opi = series(["OperatingIncomeLoss"])
        eps = series(["EarningsPerShareDiluted"], unit="USD/shares")
        used_concepts = sorted({cn for cn, _ in rev + opi + eps})

        def hist(sers, cutoff_ts):
            """One value per period end, earliest filed, filed strictly before cutoff."""
            d = {}
            for _, x in sers:
                if pd.Timestamp(x["filed"]) >= cutoff_ts:
                    continue
                k = x["end"]
                if k not in d or pd.Timestamp(x["filed"]) < pd.Timestamp(d[k]["filed"]):
                    d[k] = x
            return dict(sorted(d.items()))

        prior_text = None
        for e in sorted(ev, key=lambda z: z["filing_date"]):
            acc_ts = pd.Timestamp(e["acceptance"])
            if acc_ts.tzinfo is not None:
                acc_ts = acc_ts.tz_convert("America/New_York").tz_localize(None)
            cutoff = pd.Timestamp(e["filing_date"])
            R, O, E = hist(rev, cutoff), hist(opi, cutoff), hist(eps, cutoff)
            if not R:
                continue
            ends = list(R)
            cur_end = ends[-1]
            fpe = cur_end

            def yoy(dd, end):
                tgt = pd.Timestamp(end) - pd.Timedelta(days=365)
                cand = [k for k in dd if abs((pd.Timestamp(k) - tgt).days) <= 20
                        and pd.Timestamp(k) < pd.Timestamp(end)]
                if len(cand) != 1 or not dd[cand[0]]["val"]:
                    return None
                return float(dd[end]["val"]) / float(dd[cand[0]]["val"]) - 1.0

            cur_g = yoy(R, cur_end)
            prevs = [yoy(R, k) for k in ends[:-1][-4:]]
            prevs = [p for p in prevs if p is not None]
            c_rev = (cur_g - float(np.median(prevs))) if (cur_g is not None and len(prevs) >= 2) else np.nan

            def seasonal(dd, end, transform):
                if end not in dd:
                    return np.nan
                cq = pd.Timestamp(end).quarter
                hist_v = [transform(k, dd) for k in dd
                          if k != end and pd.Timestamp(k).quarter == cq and pd.Timestamp(k) < pd.Timestamp(end)]
                hist_v = [v for v in hist_v if v is not None and np.isfinite(v)]
                cur = transform(end, dd)
                if cur is None or not np.isfinite(cur) or len(hist_v) < 2:
                    return np.nan
                return float(cur - np.mean(hist_v))

            def margin(k, dd):
                if k not in R or not R[k]["val"]:
                    return None
                return float(dd[k]["val"]) / float(R[k]["val"])
            c_margin = seasonal(O, cur_end, margin) if O and cur_end in O else np.nan
            c_eps = seasonal(E, cur_end, lambda k, dd: float(dd[k]["val"])) if E and cur_end in E else np.nan

            # earnings-release exhibit text
            accn = e["accession"].replace("-", "")
            base = f"https://www.sec.gov/Archives/edgar/data/{c}/{accn}"
            txt, doc_url, sha = None, None, None
            try:
                idx = json.loads(get(f"{base}/index.json", UA, f"ix_{e['accession']}.json"))
                names = [it["name"] for it in idx["directory"]["item"]]
                # Earnings-release exhibits are named inconsistently across filers
                # (ex99_1.htm, exhibit9919302025.htm, q2fy26exhibit991er.htm,
                # googexhibit991q32025.htm). Match any document carrying a 99-1
                # exhibit marker, excluding EDGAR index and rendered R-files.
                def _is_ex99(n):
                    ln = n.lower()
                    if not ln.endswith((".htm", ".html", ".txt")):
                        return False
                    if "index" in ln or re.match(r"^r\d+\.htm", ln) or re.match(r"^\d{10}-\d\d-\d{6}", ln):
                        return False
                    return bool(re.search(r"99[-_.]?1", ln) or re.search(r"ex[-_]?99", ln))
                cands = [n for n in names if _is_ex99(n)]
                cands.sort(key=lambda n: (0 if re.search(r"99[-_.]?1", n.lower()) else 1, len(n), n))
                if cands:
                    doc_url = f"{base}/{sorted(cands)[0]}"
                    raw = get(doc_url, UA, f"ex_{e['accession']}_{sorted(cands)[0][:40]}")
                    sha = hashlib.sha256(raw).hexdigest()
                    txt = strip_html(raw)
            except Exception:
                pass
            time.sleep(0.11)
            nov = np.nan
            if txt and prior_text and len(txt) > 400 and len(prior_text) > 400:
                m = hv.transform([txt, prior_text])
                nov = float(1.0 - (m[0] @ m[1].T).toarray()[0][0])
            if txt and len(txt) > 400:
                prior_text = txt
            rows.append({"ticker": t, "fiscal_period_end": fpe, "accession": e["accession"],
                         "filing_date": e["filing_date"], "acceptance_et": str(acc_ts),
                         "c_rev": c_rev, "c_margin": c_margin, "c_eps": c_eps,
                         "text_novelty": nov})
            prov.append({"ticker": t, "fiscal_period_end": fpe, "accession": e["accession"],
                         "filing_url": f"{base}/{e['primary_doc']}", "exhibit_url": doc_url,
                         "acceptance_et": str(acc_ts), "exhibit_sha256": sha,
                         "xbrl_concepts_used": used_concepts,
                         "xbrl_filed_cutoff": str(cutoff.date())})
    return pd.DataFrame(rows), prov


def attach_prices(ev):
    px = {}
    spy = daily("SPY")
    spy["oc"] = spy.Close / spy.Open - 1.0
    for t in sorted(ev.ticker.unique()):
        try:
            px[t] = daily(t)
        except Exception:
            pass
        time.sleep(0.12)
    out = []
    for _, r in ev.iterrows():
        d = px.get(r.ticker)
        if d is None:
            continue
        acc = pd.Timestamp(r.acceptance_et)
        day = acc.normalize()
        sess = d.index[d.Date == day]
        before_open = acc.hour < 9 or (acc.hour == 9 and acc.minute < 30)
        if len(sess) == 1 and before_open:
            R = int(sess[0])
        else:
            nx = d.index[d.Date > day]
            if not len(nx):
                continue
            R = int(nx[0])
        if R < 21 or R + 1 + EXIT2 >= len(d):
            continue
        si = spy.index[spy.Date == d.Date.values[R]]
        if not len(si):
            continue
        si = int(si[0])
        if si < 21 or si + 1 + EXIT2 >= len(spy):
            continue
        ent = R + 1
        s_ent = si + 1
        rr = float(d.Close.values[R] / d.Open.values[R] - 1.0)
        sr = float(spy.Close.values[si] / spy.Open.values[si] - 1.0)
        v20 = float(np.mean(d.Volume.values[R - 20:R]))
        p20 = float(d.Close.values[R] / d.Close.values[R - 20] - 1.0)
        sp20 = float(spy.Close.values[si] / spy.Close.values[si - 20] - 1.0)
        dr = d.Close.values[R - 19:R + 1] / d.Close.values[R - 20:R] - 1.0
        row = dict(r)
        row.update({
            "reaction_date": str(pd.Timestamp(d.Date.values[R]).date()),
            "entry_date": str(pd.Timestamp(d.Date.values[ent]).date()),
            "reaction_abn_ret": rr - sr,
            "reaction_abn_volume": float(d.Volume.values[R] / v20) if v20 > 0 else np.nan,
            "prior20_abn_ret": p20 - sp20,
            "prior20_vol": float(np.std(dr, ddof=1)),
            "year": str(pd.Timestamp(d.Date.values[ent]).year)})
        for k, off in (("y5", EXIT1), ("y20", EXIT2)):
            x = float(d.Close.values[ent + off - 1] / d.Open.values[ent] - 1.0)
            b = float(spy.Close.values[s_ent + off - 1] / spy.Open.values[s_ent] - 1.0)
            row[k] = x - b
            row[f"{k}_exit_date"] = str(pd.Timestamp(d.Date.values[ent + off - 1]).date())
        out.append(row)
    return pd.DataFrame(out)


def inner_alpha(tr, feats, target):
    """Alpha by INNER CHRONOLOGICAL split of the outer training fold only."""
    tr = tr.sort_values("entry_date")
    cut = int(len(tr) * 0.7)
    a_tr, a_va = tr.iloc[:cut], tr.iloc[cut:]
    if len(a_va) < 20:
        return 1.0
    best, bs = ALPHAS[0], np.inf
    for a in ALPHAS:
        Z, Zv, _ = design(a_tr, a_va, feats)
        m = Ridge(alpha=a).fit(Z, a_tr[target].values)
        s = float(np.mean(np.abs(a_va[target].values - m.predict(Zv))))
        if s < bs:
            best, bs = a, s
    return best


def design(tr, te, feats):
    tk = pd.get_dummies(tr.ticker, prefix="tk")
    tk_te = pd.get_dummies(te.ticker, prefix="tk").reindex(columns=tk.columns, fill_value=0)
    Xtr = np.column_stack([tr[feats].values.astype(float), tk.values.astype(float)])
    Xte = np.column_stack([te[feats].values.astype(float), tk_te.values.astype(float)])
    mu, sd = np.nanmean(Xtr, 0), np.nanstd(Xtr, 0)
    sd[sd == 0] = 1.0
    Xtr = np.nan_to_num((Xtr - mu) / sd)
    Xte = np.nan_to_num((Xte - mu) / sd)
    return Xtr, Xte, list(feats) + list(tk.columns)


def boot(df, la, lb, seed=SEED):
    rng = np.random.default_rng(seed)
    wk = pd.to_datetime(df.entry_date).dt.to_period("W").astype(str).values
    weeks = np.array(sorted(set(wk)))
    idx = {w: np.where(wk == w)[0] for w in weeks}
    diff = la - lb
    starts = np.arange(0, max(1, len(weeks) - BLOCK + 1))
    n = max(1, len(weeks) // BLOCK)
    out = np.empty(BOOT)
    for i in range(BOOT):
        pick = rng.choice(starts, size=n, replace=True)
        sel = np.concatenate([idx[w] for s in pick for w in weeks[s:s + BLOCK] if w in idx])
        out[i] = diff[sel].mean() if len(sel) else 0.0
    return {"mean": float(diff.mean()),
            "ci95": [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))],
            "draws": BOOT, "block_weeks": BLOCK, "seed": seed,
            "entirely_above_zero": bool(np.percentile(out, 2.5) > 0)}


def main() -> int:
    t0 = time.time()
    ev, prov = build_events()
    ev = attach_prices(ev)
    before = len(ev)
    ev = ev.drop_duplicates(subset=["ticker", "fiscal_period_end", "accession"], keep=False)
    dup_refused = before - len(ev)
    ev = ev.sort_values("entry_date").reset_index(drop=True)
    ev["n_components"] = ev[NUM_C].notna().sum(axis=1)
    ev = ev[ev.n_components >= 2]
    ev = ev.dropna(subset=["text_novelty"] + MKT_F + ["y5", "y20"]).reset_index(drop=True)

    oos = ev[ev.year.isin(TEST_YEARS)]
    per_year = oos.year.value_counts().to_dict()
    gate = {"tickers": int(ev.ticker.nunique()), "events": int(len(ev)),
            "oos_events": int(len(oos)), "oos_by_year": per_year,
            "required": GATE,
            "duplicate_identities_refused": int(dup_refused)}
    gate["passed"] = bool(gate["tickers"] >= GATE["tickers"] and gate["events"] >= GATE["events"]
                          and gate["oos_events"] >= GATE["oos"]
                          and all(per_year.get(y, 0) >= GATE["oos_per_year"] for y in TEST_YEARS))
    res = {"artifact": "EARNINGS_INFORMATION_ABSORPTION_RESULTS", "version": "1.0",
           "status": "EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY",
           "google_trends_used": False,
           "construct": ("information-price RESIDUAL PROXY; not intrinsic value, fair value, "
                         "mispricing, analyst surprise, or proof of underreaction"),
           "feasibility_gate": gate}
    ev.to_csv(PANEL, index=False, lineterminator="\n")
    PROV.write_text(json.dumps(prov[:2000], indent=1), encoding="utf-8", newline="\n")
    if not gate["passed"]:
        res["decision_label"] = "DATA_UNAVAILABLE"
        res["runtime_seconds"] = round(time.time() - t0, 1)
        RESULTS.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
        print("DATA_UNAVAILABLE", gate)
        return 0

    # ---------- Stage 1 ----------
    keep, coefs1 = [], []
    for ty in TEST_YEARS:
        tr, te = ev[ev.year < ty], ev[ev.year == ty]
        if len(tr) < 40 or len(te) == 0:
            continue
        tr = tr.copy(); te = te.copy()
        for c in NUM_C:                       # standardize on TRAINING fold only
            mu, sd = tr[c].mean(), tr[c].std(ddof=1)
            for f in (tr, te):
                f[c + "_z"] = (f[c] - mu) / (sd if sd and np.isfinite(sd) and sd > 0 else 1.0)
        for f in (tr, te):
            f["numeric_information_score"] = f[[c + "_z" for c in NUM_C]].mean(axis=1, skipna=True)
            f["num_x_novelty"] = f.numeric_information_score * f.text_novelty
        a = inner_alpha(tr, S1_F, "reaction_abn_ret")
        Z, Zt, names = design(tr, te, S1_F)
        m = Ridge(alpha=a).fit(Z, tr.reaction_abn_ret.values)
        te["s1_info"] = m.predict(Zt)
        Zn, Ztn, _ = design(tr, te, [])
        mn = Ridge(alpha=inner_alpha(tr, [], "reaction_abn_ret")).fit(Zn, tr.reaction_abn_ret.values)
        te["s1_null"] = mn.predict(Ztn)
        te["information_price_gap"] = te.s1_info - te.reaction_abn_ret
        te["gap_x_novelty"] = te.information_price_gap * te.text_novelty
        coefs1.append(dict(zip(names, m.coef_)))
        keep.append(te)
    d1 = pd.concat(keep, ignore_index=True)
    y = d1.reaction_abn_ret.values
    l_null, l_info = np.abs(y - d1.s1_null.values), np.abs(y - d1.s1_info.values)
    mae_n, mae_i = float(l_null.mean()), float(l_info.mean())
    impr1 = 100 * (mae_n - mae_i) / mae_n
    b1 = boot(d1, l_null, l_info)
    yr1 = {ty: {"null_mae": round(float(np.abs(s.reaction_abn_ret - s.s1_null).mean()), 6),
                "info_mae": round(float(np.abs(s.reaction_abn_ret - s.s1_info).mean()), 6)}
           for ty, s in d1.groupby("year")}
    for v in yr1.values():
        v["info_better"] = bool(v["info_mae"] < v["null_mae"])
    ss = float(np.sum((y - d1.s1_info) ** 2)); ss0 = float(np.sum((y - y.mean()) ** 2))
    g1 = {"improves_1pct": bool(impr1 >= 1.0), "ci_above_zero": b1["entirely_above_zero"],
          "better_in_2of3": sum(v["info_better"] for v in yr1.values()) >= 2}
    res["stage1"] = {"n_oos": int(len(d1)), "null_mae": round(mae_n, 6), "info_mae": round(mae_i, 6),
                     "improvement_pct": round(impr1, 4),
                     "info_rmse": round(float(math.sqrt(np.mean((y - d1.s1_info) ** 2))), 6),
                     "info_r2_oos": round(1 - ss / ss0, 5), "by_year": yr1,
                     "bootstrap_null_minus_info": b1, "gates": g1, "passes": bool(all(g1.values()))}

    # ---------- Stage 2 ----------
    from scipy.stats import spearmanr
    s2 = {}
    for tgt, lbl in (("y5", "five_day"), ("y20", "twenty_day")):
        kp, cf = [], []
        for ty in TEST_YEARS:
            tr, te = d1[d1.year < ty], d1[d1.year == ty]
            if len(tr) < 40 or len(te) == 0:
                continue
            ab = inner_alpha(tr, MKT_F, tgt)
            Zb, Ztb, _ = design(tr, te, MKT_F)
            mb = Ridge(alpha=ab).fit(Zb, tr[tgt].values)
            ac = inner_alpha(tr, MKT_F + S2_C_EXTRA, tgt)
            Zc, Ztc, nc = design(tr, te, MKT_F + S2_C_EXTRA)
            mc = Ridge(alpha=ac).fit(Zc, tr[tgt].values)
            t2 = te.copy(); t2["pb"], t2["pc"] = mb.predict(Ztb), mc.predict(Ztc)
            kp.append(t2); cf.append(dict(zip(nc, mc.coef_)))
        if not kp:
            continue
        dd = pd.concat(kp, ignore_index=True)
        yy = dd[tgt].values
        lb, lc = np.abs(yy - dd.pb.values), np.abs(yy - dd.pc.values)
        mb_, mc_ = float(lb.mean()), float(lc.mean())
        impr = 100 * (mb_ - mc_) / mb_
        bb = boot(dd, lb, lc)
        ic = float(spearmanr(dd.pc.values, yy).statistic)
        yr = {}
        for ty, s in dd.groupby("year"):
            a_ = float(np.abs(s[tgt] - s.pb).mean()); b_ = float(np.abs(s[tgt] - s.pc).mean())
            icy = float(spearmanr(s.pc.values, s[tgt].values).statistic) if len(s) > 5 else float("nan")
            yr[ty] = {"B_mae": round(a_, 6), "C_mae": round(b_, 6), "C_better": bool(b_ < a_),
                      "ic": round(icy, 4), "ic_positive": bool(icy > 0)}
        ssc = float(np.sum((yy - dd.pc) ** 2)); ss0c = float(np.sum((yy - yy.mean()) ** 2))
        g = {"improves_1pct": bool(impr >= 1.0), "ci_above_zero": bb["entirely_above_zero"],
             "beats_in_2of3": sum(v["C_better"] for v in yr.values()) >= 2,
             "ic_above_0_03": bool(ic > 0.03),
             "ic_positive_2of3": sum(v["ic_positive"] for v in yr.values()) >= 2}
        s2[lbl] = {"n_oos": int(len(dd)), "B_mae": round(mb_, 6), "C_mae": round(mc_, 6),
                   "improvement_pct": round(impr, 4),
                   "C_rmse": round(float(math.sqrt(np.mean((yy - dd.pc) ** 2))), 6),
                   "C_r2_oos": round(1 - ssc / ss0c, 5), "spearman_ic": round(ic, 4),
                   "by_year": yr, "bootstrap_B_minus_C": bb, "gates": g,
                   "passes": bool(all(g.values())),
                   "gap_coefficients": {k: {"mean": round(float(np.mean([c[k] for c in cf])), 6),
                                            "sign_stable": bool(len({np.mean([c[k]]) > 0 for c in cf}) == 1
                                                                or len({c[k] > 0 for c in cf}) == 1)}
                                        for k in S2_C_EXTRA}}
        if lbl == "five_day":
            s2["_frame"] = dd
    frame = s2.pop("_frame", None)
    res["stage2"] = s2

    p1 = res["stage1"]["passes"]
    p2 = s2.get("five_day", {}).get("passes", False)
    if p1 and p2 and frame is not None:
        thr_rows = []
        for ty in TEST_YEARS:
            tr, te = frame[frame.year < ty], frame[frame.year == ty]
            if not len(tr) or not len(te):
                continue
            thr = float(np.percentile(np.abs(tr.pc.values), 80))
            sel = te[np.abs(te.pc.values) > thr].copy()
            sel["net"] = np.sign(sel.pc) * sel.y5 - COST
            thr_rows.append(sel)
        tr_all = pd.concat(thr_rows, ignore_index=True) if thr_rows else pd.DataFrame()
        res["trading"] = {"trades": int(len(tr_all))} if len(tr_all) else {"trades": 0}
    else:
        res["trading"] = {"status": "not run: predictive gates did not both pass; "
                                    "no strategy is manufactured from a failed gate"}

    if not gate["passed"]:
        label = "DATA_UNAVAILABLE"
    elif not p1:
        label = "INFORMATION_FEATURES_DO_NOT_EXPLAIN_INITIAL_REACTION"
    elif not p2:
        label = "NO_INFORMATION_PRICE_GAP_EDGE"
    elif not res.get("trading", {}).get("passes", False):
        label = "PREDICTIVE_NOT_TRADABLE"
    else:
        label = "INFORMATION_PRICE_GAP_SIGNAL"
    res["decision_label"] = label
    res["stage1_coefficients"] = {k: round(float(np.mean([c[k] for c in coefs1])), 6) for k in S1_F}
    res["runtime_seconds"] = round(time.time() - t0, 1)
    RESULTS.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(f"events {gate['events']} tickers {gate['tickers']} oos {gate['oos_events']} {gate['oos_by_year']} gate {gate['passed']}")
    print(f"S1 null {mae_n:.6f} info {mae_i:.6f} impr {impr1:.3f}% CI {b1['ci95']} -> {g1}")
    for k, v in s2.items():
        print(f"S2 {k}: B {v['B_mae']:.6f} C {v['C_mae']:.6f} impr {v['improvement_pct']:.3f}% IC {v['spearman_ic']} -> {v['gates']}")
    print(f"DECISION: {label}  ({res['runtime_seconds']}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
