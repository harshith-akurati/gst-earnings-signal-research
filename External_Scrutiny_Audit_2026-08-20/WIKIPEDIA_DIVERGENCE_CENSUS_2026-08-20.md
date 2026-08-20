# Wikipedia-divergence descriptive census — CENSUS, NOT ANALYSIS

**Date:** 2026-08-20
**Authorised by:** `SATURATED_DATA_DESCRIPTIVE_CENSUS_RULING_2026-08-20.md` (same directory).

> **This is a census, not an analysis.** No outcome variable appears anywhere in this document. No
> return, abnormal return, volatility, win rate, PnL, option price, implied move or any function of a
> price was computed, retrieved or inspected. No test statistic, p-value, confidence interval or model
> fit appears.
>
> **Outcome comparisons between the divergent and concordant sets are PROHIBITED** — now and later —
> pending a pre-registration on forward data that does not yet exist. Nothing here may be cited as
> evidence for or against any claim about market behaviour.

---

## 1. Verification of the "~30%" claim

**Source file:** `Live Signal Engine/Wikipedia_Pageviews_ZScore_PerEvent.csv` — 152 rows, columns
`ticker, spike_week, wikipedia_article, gst_zscore, wiki_aligned_week, wiki_value, wiki_zscore, note`.
Recomputed directly from that file on 2026-08-20.

| Quantity | Value |
|---|---|
| Total events | **152** |
| `wiki_zscore < 0` | **45** |
| Share | **29.6%** |
| `wiki_zscore >= 0` | 107 |
| `wiki_zscore >= 2` | 36 (23.7%) |
| `wiki_zscore >= 5` | 13 (8.6%) |
| `gst_zscore` range | 5.023 → 31.099, **0 nulls** |
| `wiki_zscore` range | −5.326 → 23.756, **0 nulls** |

**"Below baseline" is defined as `wiki_zscore < 0`** — Wikipedia pageviews below the article's own
trailing baseline at the aligned week. The claim verifies exactly: **45/152 = 29.6%**.

These figures were already committed in `Live Signal Engine/Wikipedia_Pageviews_IndependenceCheck_Note.md`,
which records the same 45/152 (29.6%) alongside Pearson r = 0.2442 (p = 0.0024) and Spearman
rho = 0.1646 (p = 0.0428).

### Correction to the framing

The proposal described these as events with "BELOW-baseline Wikipedia attention despite **extreme**
Google attention," implying a contrast against events with ordinary Google attention.

**No such contrast exists in this population.** All 152 events qualify on `qualifies_z5`, so
`gst_zscore >= 5` holds **by construction** — the observed floor is 5.023. There is no low-GST
comparison group here. The split is on Wikipedia only.

The committed independence note already warns about the consequence: because `gst_zscore` has a hard
floor at 5 while `wiki_zscore` centres near zero, 131/152 events trivially satisfy
`|gst_zscore| > 2 × |wiki_zscore|` **for scale reasons alone**, and that count is not evidence of
divergence.

---

## 2. Composition — divergent set (`wiki_zscore < 0`, n = 45)

**Tickers:** 13 distinct.

| Ticker | Divergent events |
|---|---|
| MSFT | 8 |
| ADBE | 6 |
| NKE | 6 |
| AMZN | 5 |
| NFLX | 5 |
| SBUX | 5 |
| AAPL | 3 |
| CTSH | 2 |
| ABBV, GME, GPN, LDOS, QCOM | 1 each |

**Concentration:** MSFT alone supplies 8/45 (17.8%); the top three tickers supply 20/45 (44.4%).

**Sectors:** Technology 21, Consumer Cyclical 17, Communication Services 5, Healthcare 1,
Industrials 1.

**By year:** 2021: 4 · 2022: 8 · 2023: 10 · 2024: 11 · 2025: 12 — monotonically increasing.

**Input z-score distribution:** `gst_zscore` median 6.689, mean 8.104. `wiki_zscore` median −0.573,
minimum −5.326.

---

## 3. Composition — concordant set (`wiki_zscore >= 0`, n = 107)

**Tickers:** 25 distinct. Largest: NFLX 11, QCOM 9, ADBE 8, NKE 7, TTWO 7, INTC 6, MSFT 6, NVDA 6,
SYK 6, SBUX 5.

**Sectors:** Technology 45, Communication Services 22, Consumer Cyclical 21, Healthcare 6, Energy 4,
Industrials 4, Consumer Defensive 4, Financial Services 1.

**By year:** 2021: 17 · 2022: 17 · 2023: 28 · 2024: 25 · 2025: 20.

**Input z-score distribution:** `gst_zscore` median 8.391, mean 9.930.

---

## 4. Per-ticker divergence rate

Ordered by total events. This is composition, not a test.

| Ticker | Divergent / total | Rate |
|---|---|---|
| NFLX | 5/16 | 31.2% |
| ADBE | 6/14 | 42.9% |
| MSFT | 8/14 | 57.1% |
| NKE | 6/13 | 46.2% |
| QCOM | 1/10 | 10.0% |
| SBUX | 5/10 | 50.0% |
| AMZN | 5/9 | 55.6% |
| TTWO | 0/7 | 0.0% |
| INTC | 0/6 | 0.0% |
| NVDA | 0/6 | 0.0% |
| SYK | 0/6 | 0.0% |
| AAPL | 3/5 | 60.0% |
| LDOS | 1/5 | 20.0% |
| GOOGL, STZ | 0/4 | 0.0% |
| BKR | 0/3 | 0.0% |
| GME, GPN | 1/3 | 33.3% |
| CTSH | 2/2 | 100.0% |
| ABBV | 1/1 | 100.0% |
| COHR, DELL, TSLA, UAL | 0/2 | 0.0% |
| BRK-B, DVN, NCLH | 0/1 | 0.0% |

---

## 5. Two composition facts a forward design must account for

Stated as census observations. Neither is a hypothesis, and neither may be tested on this population.

**(a) The divergent set has systematically lower GST magnitude.** Median `gst_zscore` is **6.689** in
the divergent set versus **8.391** in the concordant set. Divergence is therefore **not independent of
the selection variable**: events nearer the z ≥ 5 floor are more likely to fall in the divergent
group. A forward design that treats "GST-high / Wiki-low" as a distinct regime must control for GST
magnitude, or it will partly be measuring proximity to the selection threshold rather than a
behavioural regime.

**(b) Divergence is heavily ticker-concentrated, and several tickers are all-or-nothing.** CTSH is
2/2 and ABBV 1/1 divergent; TTWO, INTC, NVDA, SYK, GOOGL, TSLA and others are 0-for-everything. With
13 tickers carrying all 45 divergent events and one ticker supplying 17.8%, any forward test needs
firm-level clustering and a per-ticker concentration cap, or a handful of firms will drive the
result.

---

## 6. Explicit non-conclusions

- Nothing here indicates that divergent events behave differently in any market sense. **That was not
  examined and must not be examined on this data.**
- The year-on-year increase in divergent counts (4 → 12) is reported as composition only. It is not
  attributed to any cause, and the denominator changes by year.
- No sector, ticker or period is characterised as favourable, unfavourable, interesting or
  promising.
- The census supplies **regime frequencies and clustering structure** for sizing a forward
  pre-registration. That is its only authorised downstream use.
