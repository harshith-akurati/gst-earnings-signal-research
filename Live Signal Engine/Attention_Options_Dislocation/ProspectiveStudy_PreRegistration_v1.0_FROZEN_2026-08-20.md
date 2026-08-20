# Prospective Study — Pre-Registration v1.0 (FROZEN)

**Status:** FROZEN on commit, **before any v2 data accumulates**. No v2 capture has been taken, no
outcome has been opened, and no analysis of any kind has been run.

**Date:** 2026-08-20

---

## 0. Honest statement of what already existed

**A formal pre-registration for this study already exists.** It is
`FROZEN_DESIGN_v1.0.md`, frozen before any Alpha Vantage, Tradier, Google Trends, price or
earnings-calendar request was made. It already specifies the research question (§1), universe (§2),
event timing (§3), options benchmark (§4), search features (§5), core hypothesis and primary tests
(§6), minimum sample and decision gates (§7), and collection prohibitions (§8). The GST score
arithmetic is separately frozen in the `TRENDS_METHOD_FROZEN` ledger record of 2026-08-19T05:32:17Z.

**This document does not replace it and does not restate it as new.** It does three things and
nothing more:

1. **Consolidates** the definitions currently spread across `FROZEN_DESIGN_v1.0.md`, the
   `TRENDS_METHOD_FROZEN` ledger record, and `ProspectiveStudy_Method_v2_FROZEN.md` into one
   readable specification.
2. **Closes two genuine ambiguities** that would otherwise be resolved after seeing data — §3 below
   (which implied-move measure binds) and §5 (the interim checkpoint).
3. **Re-affirms the pre-committed minimum sample**, unchanged.

Where this document and `FROZEN_DESIGN_v1.0.md` could be read as differing, **`FROZEN_DESIGN_v1.0.md`
controls**, except for the single ambiguity resolved in §3, which it left open.

---

## 1. Hypothesis

Pre-announcement search attention improves prediction of the **realized magnitude** of an earnings
move beyond the **options-implied move**; and an attention/options dislocation identifies positive
net long-straddle returns after the bid–ask spread.

**Direction is never predicted.** No directional signal is constructed, tested or reported.

---

## 2. GST attention score — exact definition

Per query, per retrieval day, on weekly US Google Trends data (`geo=US`, `gprop=""`, `cat=0`), over a
730-day window ending at the data cutoff, where the cutoff is **no later than T−2 calendar days**:

```
z_query = (target_value - mean(previous 52 complete weekly values))
          / sample_standard_deviation(previous 52 complete weekly values)
```

- `ddof = 1`; the baseline **excludes** the target week.
- No winsorisation, no clipping, no transformation, no rounding before calculation.
- A week is retained only if it is weekly resolution, not marked partial, and
  `week_start + 6 days <= cutoff`. No interpolation. Zero is a valid value, not missing.
- The target week is the most recent retained complete week.
- Zero standard deviation invalidates that query.

Two queries per event — `<TICKER> stock` and the issuer query constructed by
`ProspectiveStudy_Method_v2_FROZEN.md` §3 — issued as **separate one-keyword requests**, never
batched, each standardised within its own history before combination:

```
daily_composite = (z_ticker_query + z_issuer_query) / 2
gst_zscore      = (daily_composite_Tminus1 + daily_composite_T0) / 2
```

Both queries and both days are required. No substitution, no fallback, no one-query variant.

---

## 3. Options-implied move benchmark — exact definition

Measured at the **15:45 ET ± 10 minutes** snapshot, on the announcement trading day for an AMC
release and on the preceding trading day for a BMO release, for the **nearest expiration strictly
after** the event, at the **strike nearest the contemporaneous underlying price**:

```
midpoint_implied_move    = (call_mid + put_mid) / underlying_price
executable_straddle_cost = (call_ask + put_ask) / underlying_price
```

**Ambiguity closed here.** `FROZEN_DESIGN_v1.0.md` §4 defines both measures; §6 refers to "the
options-implied move" without naming which one binds. Resolved now, before any v2 data exists:

- **`midpoint_implied_move` is the binding benchmark for the primary tests** (§6.1 and §6.2 of the
  frozen design). It is the standard mid-market measure and is not inflated by the spread.
- **`executable_straddle_cost` binds only the secondary tradability test**, where the position is
  entered at the combined ask.
- Both are recorded for every event regardless. Reporting one without the other is not permitted.

**Refusals, unchanged:** a missing bid or ask is never replaced by the last price; a crossed market
(bid > ask) is refused; a quote timestamped at or after the announcement is refused; call and put
quotes that diverge beyond the frozen tolerance are refused. A refused leg refuses the event.

---

## 4. Realized move — exact definition

```
realized_absolute_move = abs( close(first post-announcement regular session)
                              / pre_event_reference_price - 1 )
```

- The **pre-event reference price** is the underlying price recorded at the same 15:45 ET snapshot
  that produced the implied-move benchmark. The two are taken from one snapshot, so they are
  contemporaneous by construction.
- The **first post-announcement regular session** is the first full regular session that can reflect
  the release, under the frozen session mapping: AMC → the next session; BMO → that same session;
  an intraday release is excluded entirely.
- No abnormal-return adjustment and no benchmark subtraction is applied to this quantity. It is an
  absolute underlying move.

**This outcome is defined here and is not computed, retrieved or inspected during collection.**
Opening it before the minimum sample is a protocol violation.

---

## 5. Binding decision rule and pre-committed minimum sample

### 5.1 Minimum sample — unchanged

> **No scientific or trading verdict before 75 eligible events.**

This is inherited verbatim from `FROZEN_DESIGN_v1.0.md` §7 and is **not modified, relaxed or
reinterpreted** by this document. It was pre-committed before any data existed and it remains the
binding gate.

### 5.2 Interim checkpoint at 40 — descriptive only

A checkpoint is registered at **40 eligible events**, for operational visibility only.

**Permitted at 40:** coverage, capture success and failure counts, retry counts, counts of
`EVENT_INELIGIBLE_QUERY_UNRESOLVABLE`, timing integrity, provider refusal counts, and descriptive
distributions of the *inputs*.

**Forbidden at 40:** any evaluation of any gate; any verdict; any statement that the hypothesis is
supported, unsupported, promising or unpromising; any directional or favourable/unfavourable
characterisation; any correlation, MAE, or return computed against an outcome; and any decision to
continue, stop or modify the study that is informed by an outcome.

**The 40-event checkpoint is explicitly not a reduction of the 75-event gate.** It is recorded here
so that a milestone exists without creating an opportunity to peek. Nothing observed at 40 may change
anything specified in this document or in the frozen design.

### 5.3 Primary success criteria — unchanged

All four required, evaluated only at ≥75 eligible events:

1. At least **2%** chronological out-of-sample MAE improvement versus the options-only baseline.
2. **Block-bootstrap 95% interval** for the paired improvement **entirely above zero**.
3. **Positive Spearman** association between attention dislocation and
   `realized_absolute_move − midpoint_implied_move`.
4. **No individual ticker supplies more than 10%** of eligible events.

**These gates are not altered after observations accumulate.** Failing any one of them stops the
study at that stage; a failed gate is never combined with another sample to manufacture a pass.

### 5.4 Attention dislocation

```
attention_dislocation = percentile(pre_event_attention_z) - percentile(midpoint_implied_move)
```

Percentiles are computed within the analysis sample at evaluation time, not rolling and not
look-ahead-adjusted, and this is disclosed as an in-sample ranking.

---

## 6. Validity conditions registered in advance

Registered now so they cannot be introduced later as post-hoc explanations:

1. **Google Trends is a rescaled, sampled index**, not a search count. Repeated retrievals of an
   identical request can differ. The series retrieved at T−1 and T0 cannot establish that the same
   series was available at any earlier decision time.
2. **Query ambiguity is unresolved.** A ticker or company name is a mixture of the intended construct
   and unrelated interest. Attention here is a **noisy proxy**, not a measurement.
3. **Issuer-query resolvability is not universal.** Issuers whose name query falls below Google's
   volume floor are excluded by the §4 pre-flight gate of Method v2. Because that floor correlates
   with how much attention a company receives, **the realised cohort is expected to be biased toward
   higher-attention issuers**. The count of such exclusions is a required field in every coverage
   report, and any result must be read against it. This limitation is registered before data
   collection and is not offered later as a defence.
4. **Vendor calendar dates are scheduling inputs, not timing proof**, until confirmed against an
   issuer release or SEC filing.
5. **Delayed or manual option quotes are non-executable** and are labelled as such. No latency
   guarantee is claimed.
6. **Retried captures are flagged.** Any analysis must report the count of events containing a
   retried capture and must be reproducible with them excluded (Method v2 §5.5).

---

## 7. Scope limits

- This study does not touch HYP-01. F5 remains OPEN and HYP-01 collection remains BLOCKED.
- No live capital is deployed. No order is placed or simulated during collection.
- No result from this study may be pooled with any retrospective result in this repository.
- Nothing here is an investment recommendation, and no investable strategy is claimed.

---

## 8. Freeze attestation

At the moment of this commit: no v2 Trends request has been issued, no v2 capture exists, no outcome
has been opened or computed, and no analysis has been run. The 75-event gate, the four success
criteria, the GST score arithmetic, the implied-move benchmark, and the realized-move definition are
all fixed as written above, before any v2 observation exists.
