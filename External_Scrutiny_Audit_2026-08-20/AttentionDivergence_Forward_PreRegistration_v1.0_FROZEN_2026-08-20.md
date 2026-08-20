# Attention-Divergence Regime: Forward Pre-Registration (FROZEN)

**Status: ADOPTED.** Frozen on commit. This commit's timestamp is the data boundary in §2.

**Date:** 2026-08-20
**Queue entry:** item 2, `Live Signal Engine/FUTURE_HYPOTHESES_QUEUE.md`

---

## 1. Question

Among earnings-adjacent attention events, do **GST-high / Wikipedia-low** ("searching without
reading") events differ in market response from **GST-high / Wikipedia-high** ("searching and
reading") events?

The intuition being tested is that the two attention sources proxy different behaviours — transient,
headline-driven search versus deliberate information-seeking — and that only the latter reflects
substantive information acquisition.

**This is a magnitude question. Direction is never predicted.**

---

## 2. Data boundary — binding

**Only Phase 2 panel observations whose event date falls strictly after this document's commit
timestamp are eligible.** No historical event is enrolled, ever.

Specifically excluded and never re-examined: the 152-event canonical population, the semiconductor
outcome populations, and every event in `Wikipedia_Pageviews_ZScore_PerEvent.csv`.

Those data supplied **regime frequencies and clustering structure only** — design inputs, in the same
category as a power calculation. `SATURATED_DATA_DESCRIPTIVE_CENSUS_RULING_2026-08-20.md` prohibits
outcome comparisons on them absolutely, and this pre-registration does not and cannot lift that.

---

## 3. Regime definitions — pre-committed, no re-thresholding

Both z-scores are computed on **weeks closing strictly before the event day**, so neither overlaps
the outcome window. This is the `gst_z_pre` convention, not the `fixed_window_zscore` convention —
the reconciliation of 2026-08-20 established that the latter's numerator is contemporaneous with a
4-day outcome window in 100% of cases.

```
gst_z   = (target - mean(prior 52 complete weekly GST values))  / sd(prior 52),  ddof = 1
wiki_z  = (target - mean(prior 52 complete weekly wiki values)) / sd(prior 52),  ddof = 1
```

Baselines exclude the target week. No winsorisation, clipping, transformation or rounding before
calculation. Zero standard deviation invalidates that series and the event.

**Regime assignment, fixed:**

| Regime | Definition |
|---|---|
| **DIVERGENT** | `gst_z >= GST_FLOOR` **and** `wiki_z < 0` |
| **CONCORDANT** | `gst_z >= GST_FLOOR` **and** `wiki_z >= 0` |
| Not enrolled | `gst_z < GST_FLOOR` |

**`wiki_z < 0` is pre-committed and fixed.** It is the committed baseline definition from the
independence note. **Re-thresholding is prohibited** — no `-0.5`, no `-1`, no percentile cut, no
data-driven boundary, no sensitivity sweep presented as a robustness check. One cut, fixed here.

`GST_FLOOR` is set at **`gst_z >= 2.0`** and fixed here. Rationale in §4.

---

## 4. Handling the GST-magnitude confound

**The problem.** The census found divergent events sit systematically nearer the historical
selection floor: `gst_z` median **6.689** divergent versus **8.391** concordant. Divergence is
therefore **not independent of the selection variable**. A naive two-group comparison would partly
measure GST magnitude rather than a behavioural regime.

**Three options were considered.**

| Approach | Assessment |
|---|---|
| Covariate control (include `gst_z` as a regressor) | Weakest. Assumes a functional form for the confound and leaves the comparison sensitive to it. Rejected. |
| 1:1 matching on `gst_z` | Cleanest bias control, but discards unmatched events. At the accumulation rates this project actually observes, throwing away events is unaffordable. Rejected as primary; retained as a secondary check. |
| **Stratification on `gst_z`** | **Adopted.** Preserves every enrolled event, makes the confound explicit rather than modelled, and yields a per-stratum result that is inspectable rather than absorbed into a coefficient. |

**Adopted design — regimes compared *within* GST-magnitude strata.**

Strata boundaries, fixed here, chosen to bracket the census medians (6.689 / 8.391) rather than to
balance cell counts, which are unknown in advance:

| Stratum | `gst_z` range |
|---|---|
| S1 | 2.0 ≤ `gst_z` < 5.0 |
| S2 | 5.0 ≤ `gst_z` < 8.0 |
| S3 | `gst_z` ≥ 8.0 |

The primary estimate is the **stratum-weighted mean difference** between DIVERGENT and CONCORDANT,
weighted by stratum event count. **Per-stratum estimates are always reported alongside it**, and a
pooled estimate is never reported without them.

The `GST_FLOOR = 2.0` threshold is deliberately below the historical `z >= 5` selection rule: the
historical population's floor is exactly what makes it unable to answer this question, and a lower
floor supplies the S1 stratum that the historical data structurally lacks.

---

## 5. Handling the concentration structure

**The problem.** The census found 13 tickers carried all 45 historical divergent events, with MSFT
alone at 17.8%, and several tickers 0-for-all or all-for-all.

**Pre-committed controls, all binding:**

1. **Firm-clustered inference.** All standard errors clustered by ticker using **CR2 / bias-reduced
   linearisation with Satterthwaite degrees of freedom** — the estimator this project already uses
   where cluster counts are small.
2. **Per-ticker concentration cap: no single ticker may supply more than 10% of the analysed events
   in any regime cell.** Where a ticker exceeds it, its events are **randomly subsampled** to the cap
   using a seed fixed here — **`seed = 20260820`** — and both the capped and uncapped results are
   reported.
3. **Minimum distinct tickers: 12 per regime cell.** Below that the comparison is not run and the
   result is reported as `INSUFFICIENT_TICKER_DIVERSITY` regardless of event count.
4. **No ticker is excluded for any observed outcome.** Exclusions are permitted only for missing
   required data.

---

## 6. Outcome variables

**Primary:** absolute abnormal move over the first full post-announcement regular session,

```
abs_abnormal_move = abs( r_stock(event session) - r_benchmark(event session) )
```

benchmark = SPY, session mapping AMC → next session, BMO → same session, intraday release excluded.

**Secondary, reported always, never promoted over the primary:**

1. Abnormal **volume** ratio: event-session volume / median volume over the prior 20 sessions.
2. `abs_abnormal_move − midpoint_implied_move`, where the implied move is defined exactly as in
   `ProspectiveStudy_PreRegistration_v1.0_FROZEN_2026-08-20.md` §3, **for the subset of events where
   an options snapshot exists**. Absence of an options snapshot never excludes an event from the
   primary test.

**No directional outcome. No trading simulation. No PnL. No strategy.**

---

## 7. Minimum n and decision rule

### 7.1 Minimum before any analysis

> **No analysis of any kind before 30 valid observations in EACH regime cell (60 total), with at
> least 12 distinct tickers per cell.**

Before that: coverage, capture success, regime frequencies and input distributions only — no outcome
opened, no comparison computed, no gate evaluated.

**Per stratum:** a stratum with fewer than 10 events in either regime is reported as
`STRATUM_UNDERPOWERED` and contributes to the weighted estimate but is **not** interpreted
individually.

This threshold is set here, before any data exists, and is **not lowered later**. If accumulation is
slower than hoped, the study waits. The n = 40-as-verdict-gate proposal was declined earlier this
session on exactly this principle.

### 7.2 Binding decision rule

The regime distinction is **supported** only if **all four** hold:

1. Stratum-weighted DIVERGENT−CONCORDANT difference in the primary outcome is **non-zero with a
   block-bootstrap 95% interval excluding zero**, clustered by ticker.
2. The sign of the difference is **consistent across at least 2 of the 3 strata** that are not
   `STRATUM_UNDERPOWERED`.
3. The result **survives the per-ticker concentration cap** (§5.2) — both capped and uncapped
   intervals exclude zero.
4. **At least 12 distinct tickers** contribute to each regime cell.

Failing any one → **not supported**. No partial credit, no promotion of a secondary outcome, no
pooling of strata to manufacture a pass. **These gates are not altered after observations
accumulate.**

### 7.3 Equivalence characterisation for nulls

If §7.2 does not pass, a **TOST equivalence test** is run under the convention established in
`ProspectiveStudy_PreRegistration_Amendment_A_SESOI_TOST_2026-08-20.md`:

- **TOST can never produce a supported verdict**, cannot rescue a failed gate, and is run only after
  all four criteria have been evaluated and not all passed.
- **SESOI for this study is set independently of Amendment A's cost floor**, because the primary
  outcome here is an absolute abnormal move, not an MAE improvement against an options baseline.
  Amendment A's 4.76pp anchor is a *transaction-cost* floor and does not transfer.
- **SESOI is a pre-committed robustness triple: 0.5pp / 1.0pp / 2.0pp** of absolute abnormal move,
  fixed here. Same convention as Amendment A's 3.998 / 4.76 / 4.92 triple.

**Stated plainly: the central value is a design judgment, not a measurement.** No experiment in this
repository measures the smallest regime difference that would matter, because no such regime
comparison has ever been run. The triple exists precisely so that **no single judgment-call number
carries the claim**: conclusions must hold across the plausible range, and **equivalence is reported
at all three bounds, always together**. Selecting among them after seeing results is prohibited.

**Empirical anchor for the central value.** 1.0pp is scaled against the only committed measurement of
the same quantity in this repository — the absolute earnings-move distribution in
`RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json`, whose outcome
`abs(open(T)/close(T-1) - 1)` is the closest available analogue to this study's primary outcome
(n = 136 pooled out-of-sample):

| Reference quantity | Value | 1.0pp as a share |
|---|---|---|
| Overall mean realized absolute move | **6.1135 pp** | 16.4% |
| Pooled out-of-sample baseline MAE | **3.6284 pp** | 27.6% |

So the central bound asks whether the regimes differ by roughly a sixth of a typical absolute
earnings move — large enough to matter behaviourally, small enough not to be a trivially
undetectable target. The 0.5pp bound (8.2% of the mean move) is the demanding end; 2.0pp (32.7%) is
the permissive end.

**Two caveats on that anchor, recorded rather than glossed.** The reference population is the
retrospective earnings-gap panel, not this study's forward panel, and its events were selected under
different rules; and the overnight-gap outcome is not identical to this study's first-full-session
abnormal move. The anchor is therefore a **scale reference, not a transferred measurement**, and it
does not make 1.0pp an empirically derived threshold. This is exactly why the triple, not the point
value, is the protection.

- Reported outcome is exactly one of **equivalence demonstrated** or **inconclusive**, at each of the
  three bounds, using the same block-bootstrap already specified in §7.2.

---

## 8. Registered limitations

Recorded now so they cannot appear later as post-hoc explanations.

1. **Wikipedia coverage is not universal.** Events whose issuer lacks a resolvable article with 52
   complete prior weeks are not enrollable. That exclusion is logged and counted, and — as with the
   issuer-query floor in Method v2 §4 — it likely correlates with firm prominence.
2. **Both series are noisy proxies.** GST is a rescaled, sampled index; Wikipedia pageviews mix
   investor interest with unrelated traffic. Measurement error attenuates differences, so a null may
   understate a true effect. This is a limitation, not a defence.
3. **`wiki_z < 0` is a coarse cut.** It is used because it is pre-committed, not because it is
   optimal. Any finding is a statement about that specific boundary.
4. **Stratification does not eliminate the confound**, it makes it visible. Residual confounding
   within a stratum is possible and is not claimed to be absent.
5. **The GST floor of 2.0 is lower than the historical selection rule**, so results are not
   comparable to any historical GST-spike result in this repository and must never be pooled with
   one.

---

## 9. Scope limits

- Does not touch HYP-01. F5 remains OPEN and HYP-01 collection remains BLOCKED.
- Independent of the attention–options dislocation study; shares no gate, no sample and no verdict.
- No result may be pooled with any retrospective result in this repository.
- No live capital, no order placed or simulated, no investable strategy claimed.

---

## 10. Freeze attestation (on adoption)

At the moment of commit: no event satisfying §2 has been observed, no outcome has been opened, and no
analysis has been run. The regime definitions, strata boundaries, GST floor, wiki cut, concentration
cap, seed, minimum n, four decision criteria and the SESOI triple are all fixed as written above, before any
eligible observation exists.
