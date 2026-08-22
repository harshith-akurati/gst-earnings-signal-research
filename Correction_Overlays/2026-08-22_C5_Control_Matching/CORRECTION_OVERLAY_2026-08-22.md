# Correction overlay — C5 matched-control defects in the retrospective market-response decomposition

**Date:** 2026-08-22
**Status:** OVERLAY. **No original artifact byte was changed.** Originals are preserved and
hash-locked in §7.
**No corrected result has been computed.** This overlay records verification only. Recomputation is
Phase 3 and has not been performed.

---

## 1. What was alleged, and what verification found

| # | Allegation | Verdict |
|---|---|---|
| 1 | ~20 treated events matched to themselves | **CONFIRMED — exactly 20** |
| 2 | 133 control rows resolve to ~61 distinct identities, 72 rows reused | **REFUTED AS STATED — 85 distinct identities, 48 redundant rows** (see §3) |
| 3 | Cause is `nearest_earnings_date()` lacking self-match exclusion and cross-row uniqueness | **PARTIALLY CONFIRMED, mechanism mis-stated** (see §4) |
| 4 | `Q1_abs_move_high_vs_control`, `t_stat = 2.138`, is affected | **CONFIRMED, and the lineage is wider than the allegation** (see §5) |
| 5 | Population described inconsistently as 28 vs 24 tickers | **NOT AN INCONSISTENCY — two different universes** (see §6) |

---

## 2. Event identity, defined before counting

Taken from the original schema of `Live Signal Engine/C5_PostEarnings_Population.csv`, whose columns
are `pair_id, role, ticker, anchor, earnings_date, bmo_amc, note, gap, zscore, zscore_note`.

> **Event identity = (`ticker`, `earnings_date`).**

The measured unit is an earnings event at a firm. `anchor` is *not* identity: for a signal row it is
the GST spike week, and for a control row it is the selected control week. Two different anchors can
resolve to the same earnings event, which is precisely the mechanism in §4.

A **self-match** is a `pair_id` whose signal row and control row carry the same identity.

---

## 3. Verified counts

Counted on **the rows actually used by the statistic** (285 of 304 population rows; 19 drop on
`earnings date beyond price coverage`), reproduced by executing the committed tool's own
`build_events()`.

| Quantity | Value |
|---|---|
| Total treated (signal) rows | **152** |
| Total control rows | **133** |
| Distinct treated identities | **152** (no treated reuse) |
| Distinct control identities | **85** |
| **Exact self-match count** | **20** |
| **Reused control identities** | **24** |
| **Redundant (extra) control rows** | **48** |
| Max reuse of one control | **6** |
| Control identities used exactly once | **61** |
| Rows belonging to reused identities | **72** |
| Byte-identical duplicate control rows | **0** |
| Identity-sharing but not byte-identical | **48** |

**Reuse multiplicity distribution** (identities by times used):

| ×1 | ×2 | ×3 | ×4 | ×5 | ×6 |
|---|---|---|---|---|---|
| 61 | 12 | 6 | 2 | 2 | 2 |

### Why allegation 2 is refuted as stated

The figures 61 and 72 both appear in the data, but neither means what the allegation says:

- **61** is the number of control identities used *exactly once*, not the number of distinct
  identities. Distinct identities are **85** (61 used once + 24 reused).
- **72** is the number of *rows belonging to* reused identities. The number of **redundant** rows —
  the pseudoreplication burden — is **48**, because each of the 24 reused identities legitimately
  contributes one row.

Restating the defect at its true size matters: the corrected sample is not ~61 but **85** distinct
controls, and the inflation is **48** rows, not 72.

### Byte-identity

**No duplicate control row is a byte-identical copy.** All 48 redundant rows share
(`ticker`, `earnings_date`) with another row while differing in at least `pair_id`. The duplication
is therefore a matching artefact, not a file-level data-entry duplication.

### Affected tickers and dates

**Self-matched pairs (20)** — `pair_id`, ticker, earnings date:

| | | | |
|---|---|---|---|
| 29 BKR 2022-01-20 | 32 BRK-B 2025-02-22 | 41 GME 2024-03-26 | 48 GPN 2022-10-31 |
| 49 GPN 2024-08-07 | 53 INTC 2024-01-25 | 56 LDOS 2021-08-03 | 58 LDOS 2023-10-31 |
| 59 LDOS 2024-02-13 | 79 NFLX 2022-01-20 | 82 NFLX 2023-01-19 | 101 NKE 2024-03-21 |
| 119 QCOM 2025-02-05 | 126 SBUX 2024-01-30 | 128 SBUX 2025-01-28 | 134 STZ 2025-01-10 |
| 135 SYK 2023-01-31 | 139 SYK 2025-01-28 | 140 SYK 2025-07-31 | 149 TTWO 2025-02-06 |

By ticker: LDOS 3, SYK 3, GPN 2, NFLX 2, SBUX 2, and one each for BKR, BRK-B, GME, INTC, NKE, QCOM,
STZ, TTWO — **13 of 28 tickers**.

**Reused control identities (24)**, times used: NFLX 2022-01-20 ×6 · NKE 2024-12-19 ×6 ·
MSFT 2025-04-30 ×5 · SBUX 2025-01-28 ×5 · ADBE 2023-09-14 ×4 · QCOM 2025-11-05 ×4 ·
ADBE 2023-06-15 ×3 · AMZN 2022-02-03 ×3 · MSFT 2024-04-25 ×3 · NFLX 2023-01-19 ×3 ·
NFLX 2025-04-17 ×3 · QCOM 2025-02-05 ×3 · ADBE 2022-06-16 ×2 · AMZN 2021-04-29 ×2 ·
AMZN 2025-02-06 ×2 · INTC 2022-04-28 ×2 · LDOS 2021-08-03 ×2 · LDOS 2023-10-31 ×2 ·
MSFT 2021-04-27 ×2 · NFLX 2024-04-18 ×2 · NKE 2024-03-21 ×2 · NKE 2025-12-18 ×2 ·
STZ 2025-01-10 ×2 · TTWO 2021-11-03 ×2.

**The two defects overlap.** Eight identities are both self-matched and reused — LDOS 2021-08-03,
LDOS 2023-10-31, NFLX 2022-01-20, NFLX 2023-01-19, NKE 2024-03-21, QCOM 2025-02-05, SBUX 2025-01-28,
STZ 2025-01-10. They must not be counted twice when sizing the correction.

Machine-readable detail: `verified_counts.json` beside this file.

---

## 4. Root cause — corrected mechanism

The allegation places the fault in `nearest_earnings_date()` "lacking a self-match exclusion and a
cross-row uniqueness constraint". Verification shows **two distinct defects with two different
origins**, and only one of them involves that function.

### 4a. Self-matching — created downstream by date collapse

`nearest_earnings_date()` (`GST_C5_PostEarnings_BuildPopulation.py:92`) is **not a matcher**. It maps
an already-selected anchor to the nearest real earnings date within
`EARNINGS_MATCH_WINDOW_DAYS = 10`. Signal/control pairing happens **upstream** and is read from
`Live Signal Engine/MatchedControlGroup_CanonicalRecompute.csv`.

In that upstream file, **zero of 152 pairs have `control_date == spike_week`.** The matcher never
selected a control identical to its treated anchor.

The 20 self-matches are produced *afterwards*: the signal anchor and the control anchor are resolved
**independently**, and when both fall within ±10 days of the same real earnings date they **collapse
onto one identity**. Nothing downstream checks for that collapse.

So the defect is real and does sit in this function's use, but it is a **many-to-one date-resolution
collapse without a post-resolution identity check** — not a missing exclusion inside a matcher. A
self-match exclusion placed inside `nearest_earnings_date()` would be the wrong repair, because that
function sees one row at a time and has no knowledge of the pair.

### 4b. Control reuse — inherited from upstream matching with replacement

Reuse is **not** introduced by `nearest_earnings_date()`. The upstream matched file already contains
**29 reused control anchors over 56 extra rows, max reuse 6**, which after the 19 coverage drops
becomes the 24 / 48 / 6 observed downstream. The upstream matcher performed **matching with
replacement** and recorded no uniqueness constraint.

This is a design property to be decided in Phase 2, not a coding slip: matching with replacement is a
legitimate technique whose consequence is dependence that the inference must then model.

---

## 5. Effects, stated separately, direction not asserted

**No claim is made here about which way the corrected estimate moves.** Direction is a Phase 3 output.

### 5a. Self-match contamination

Twenty events appear **in both arms simultaneously**. The same `|day_return|` value enters the
treated mean and the control mean.

Mechanically this (i) induces positive covariance between the two group means, which the Welch
two-sample statistic used for `Q1` assumes to be zero, and (ii) makes the two samples non-disjoint,
so the difference in means is no longer a contrast between distinct sets of events. The reported
standard error is therefore computed under an assumption the data violate. The magnitude and sign of
the resulting bias in the *point estimate* depend on where those 20 events sit in each distribution
and is not asserted here.

### 5b. Repeated-control dependence (pseudoreplication)

The 133 control rows carry only **85** independent control identities. Treating 133 as the control
sample size overstates the information available by **48 rows**, and the overstatement is
concentrated: two identities appear six times each.

Under naive independent-sample inference this inflates apparent precision and shrinks the standard
error, because repeated appearances of one event contribute no new information about the control
distribution while still counting toward *n*. Effective sample size is bounded above by 85, not 133,
before any further within-ticker dependence is considered.

**The original artifact already recognised this defect in part.** Its `repeated_control_sensitivity`
block reports `unique_control_events: 85`, `duplicated_control_identities: 24`,
`duplicated_control_extra_rows: 48`, `max_reuse_of_one_control: 6` — figures this verification
independently reproduces — together with a deduplicated re-analysis and CR2 inference clustered on
ticker. **The reuse defect was disclosed and partially mitigated; the self-match defect was not
detected anywhere.**

---

## 6. The 28-versus-24 ticker question

**These are two different universes. Neither number is wrong, and neither should replace the other.**

| Count | Universe | Where it applies |
|---|---|---|
| **28** | The **retrospective C5 matched population**: distinct tickers across signal *and* control roles in `C5_PostEarnings_Population.csv`. Also the ticker count of the 175-event `FixedWindow_PerEvent_Canonical.csv`. | `sample.tickers = 28`; every `n_clusters = 28` in `clustered_inference`; this overlay. |
| **24** | The **`LOCKED_24_TICKER_UNIVERSE`**: the *prospective* HYP-01 cohort universe, collection window 2026-09-01 → 2027-05-31, Monday 09:00 America/Chicago cadence. Also the universe of the attention–activity weekly panel. | Prospective cohort protocol, screening sweeps, panel work. |

**A detail neither number exposes:** within the 28, **signal roles span 27 tickers and control roles
span 28.** JBL appears **only as a control** and never as a treated event. Any statement that "the
retrospective study covers 28 tickers" is true of the pooled population but not of the treated arm.

Anywhere the affected population is described, the correct phrasing is *"28 tickers in the
retrospective matched population (27 in the treated arm)"* — not a bare substitution of 24 for 28.

---

## 7. Original artifacts — preserved and hash-locked

Unmodified by this overlay. SHA-256 as of 2026-08-22:

```
3d8fbb85d9388d1ea1391aa31a98484a4ed1c0f81d63eda416c82a490574590d  RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json
544172488e1836f31db529a80c5971ad2c9a1993ee14914975ddab60bfb95306  Live Signal Engine/C5_PostEarnings_Population.csv
ec0fdb11e78ab9fa2bc68da185db50ca7d07ade8e6550fa3136c098134b7c4f3  Live Signal Engine/MatchedControlGroup_CanonicalRecompute.csv
```

`Q1_abs_move_high_vs_control` was **reproduced exactly** from committed artifacts before any analysis
of the defect: `high_mean_abs_pct 7.8871`, `n_high 152`, `control_mean_abs_pct 6.4459`,
`n_control 133`, `difference_pp 1.4411`, `t_stat 2.138` — all six matching to the last reported digit.

---

## 8. Citation status

> ### `Q1_abs_move_high_vs_control`, including `t_stat = 2.138` — **`DO_NOT_CITE_PENDING_CORRECTION`**

The same label applies to every entry marked AFFECTED in §9. These results are **not withdrawn and
not asserted to be wrong.** They are unsafe to cite until recomputed, because their stated inference
rests on assumptions the verified data violate.

**No corrected result has been computed.** Nothing in this overlay estimates what the corrected
values will be.

---

## 9. Artifact lineage

Everything below is in `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` unless stated.

### AFFECTED — depends on the defective control rows

| Result / claim | Path or location | Why |
|---|---|---|
| `Q1_abs_move_high_vs_control` (all fields, `t_stat 2.138`, `answer: YES`) | `/Q1_abs_move_high_vs_control` | Control arm is the comparison group; contains all 20 self-matches and 48 redundant rows |
| Control-arm decomposition, all windows | `/decomposition/control/*` (`n = 133` throughout) | Computed directly on the defective rows |
| `Q6_robustness_of_the_attention_effect` (all fields) | `/Q6_robustness_of_the_attention_effect` | Matched-pair analysis over the same 133 pairs |
| `primary_magnitude_abs_day_return` | `/clustered_inference/...` `n = 285` | Pools 152 treated + 133 control |
| `magnitude_abs_excess_vs_spy` | `/clustered_inference/...` `n = 285` | Same pooled set |
| **`strategy_E_incremental_high_gst`** — **`coef_pp 0.0131`, `p_value 0.98332`** | `/clustered_inference/...` `n = 285` | Same pooled set. **This is the manuscript's headline incremental null** |
| `strategy_B_incremental_high_gst` | `/clustered_inference/...` `n = 285` | Same pooled set |
| `repeated_control_sensitivity` (all fields) | `/repeated_control_sensitivity` | Mitigation analysis of the reuse defect; does not address self-matching |
| Scorecard fields `control_only_mean_net_pct`, `same_ticker_paired_*`, `all_earnings_events_mean_net_pct` | `/scorecard[B, C, E]` | Computed against or pooled with controls |
| `sample.control_events = 133` | `/sample` | Overstates independent controls; 85 distinct |
| **Manuscript §5.1 / §9 / §12: "marginal contribution attributable to attention was +0.0131 pp with p = 0.98332"** | `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.0.md` (branch `phase5-signal-without-strategy-submission-package`) | Traces to `strategy_E_incremental_high_gst`, `n = 285` |
| Manuscript §9 cross-study row "Search attention / Absolute earnings move / **No** — +0.0131 pp, p = 0.98332" | same | same |
| `SIGNAL_WITHOUT_STRATEGY_EXECUTIVE_SUMMARY_v1.0.md`, wherever the +0.0131 pp figure appears | same branch | same |
| Figure 1 evidence ladder, to the extent it renders the incremental-null row | `SIGNAL_WITHOUT_STRATEGY_FIGURE_1_EVIDENCE_LADDER.svg` | Derived from the affected value |

### UNAFFECTED — treated-arm-only or independent of controls

Explicitly **not** invalidated by this defect.

| Result | Path | Why unaffected |
|---|---|---|
| High-GST decomposition, all windows | `/decomposition/high_gst/*` (`n = 152`) | Treated arm only; 152 distinct identities, no reuse, no self-match possible |
| `Q2_Q3_where_the_move_occurs` | `/Q2_Q3_...` | High-GST only |
| `Q4_continuation_vs_reversal` (`t_stat 1.929`) | `/Q4_...` | High-GST only, `n = 152` |
| `Q5_survives_benchmark_subtraction` | `/Q5_...` | High-GST raw vs excess, same 152 |
| Scorecard strategies B, C, E **own** trade statistics — including **`mean_net_pct 0.8543`**, `t_stat_net 3.028`, hit rates, drawdowns | `/scorecard` | One-sample statistics on the 152 treated trades. **The manuscript's "0.8543% per event" is NOT affected** |
| Strategy D quiet-vs-loud contrast | `/scorecard[D]` | Partition within the 152 treated events |
| `sample.events_in_population = 304`, `sample.tickers = 28` | `/sample` | Descriptive counts, verified correct |

### Outside this lineage — untouched

This defect is confined to the C5 matched-control construction. It does **not** reach, and does not
automatically invalidate: the retrospective **magnitude forecast** (`MAE 3.6284 / 3.6299`,
`p = 0.9827`), the retrospective **direction signal** (Brier 0.2711 vs 0.2560, AUC 0.4654, the
leakage-correction figures), the **restaurant search pilot**, the **search-demand nowcast**, the
**semiconductor EPS absorption** work, the **surprise absorption v3** and **temporal replication**
results, or the **attention–activity mismatch** panel. None consumes the C5 control table.

---

## 10. Scope limit

The defect is established for the C5 matched-control construction and the results traced in §9. It
**does not automatically invalidate any result outside that traced lineage**, and no such broader
claim is made. Results listed as UNAFFECTED must not be described as compromised.

---

## 11. What has not been done

- No matcher code has been modified.
- No corrected estimate has been computed.
- No original artifact byte has been changed.
- No replacement hypothesis has been proposed.
- No unrelated outcome has been inspected.

Phase 2 (frozen corrective design) and Phase 3 (one corrective run) follow separately.
