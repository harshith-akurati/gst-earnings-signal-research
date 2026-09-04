# AARE submission — fact audit

**Date:** 2026-09-03 · **Branch:** `manuscript-v1.1-revision-20260827`
**Audited against committed primary artifacts only.** No value below was taken from a prior
summary, a previous draft, or memory. Status vocabulary matches
`SIGNAL_WITHOUT_STRATEGY_NUMBER_AUDIT_v1.1.md`: `CURRENT`, `SENSITIVITY`, `SUPERSEDED`,
`HISTORICAL_CONTEXT`.

---

## 1. Sample period and universe

| Fact | Displayed | Full-precision stored | Source | Pointer | Status |
|---|---|---|---|---|---|
| Sample period | March 2021 to December 2025 | `["2021-03-24", "2025-12-19"]` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/sample/date_range` | **CURRENT** |
| Same period, independently stored | 2021-03-24 to 2025-12-19 | `["2021-03-24", "2025-12-19"]` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `/sample/date_range` | **CURRENT** |
| Tickers | 28 | `28` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/sample/tickers` | **CURRENT** |
| Events in population | 304 | `304` | same | `/sample/events_in_population` | **CURRENT** |
| Events usable | 285 | `285` | same | `/sample/events_usable` | **CURRENT** |
| Dropped | 19 | `19`, reason "earnings date beyond price coverage" | same | `/sample/dropped`, `/sample/drop_reasons` | **CURRENT** |
| High-attention events | 152 | `152` | same | `/sample/high_gst_events` | **CURRENT** |
| Control events | 133 | `133` | same | `/sample/control_events` | **CURRENT** |

**Inclusion criteria.** Events enter as role rows of the committed C5 matched population
(`Live Signal Engine/C5_PostEarnings_Population.csv`, 304 rows = 152 `signal` + 152 `control`,
28 distinct tickers, verified by direct read). An event is *usable* when its earnings date falls
inside price coverage; the 19 exclusions are all that single reason. Release-timing rule, fixed
before outcomes: a release accepted before 09:30 ET maps to that session, at or after 16:00 maps
to the next session, weekend or holiday maps to the next session, and a release accepted during
market hours is **excluded** (manuscript §4.2).

**Noted, not reconciled:** `C5_PostEarnings_Population.csv` carries earnings dates up to
`2026-04-08`, beyond the analysis range. Those rows are among the 19 dropped for price coverage.
The analysis period of record is the artifact's `/sample/date_range`.

## 2. Operational definition of high attention

| Component | Value | Source | Pointer |
|---|---|---|---|
| Indicator | `high_gst = 1` iff `role == 'signal'` in the C5 matched population | `tools/run_retrospective_market_response_decomposition.py` | line 463, `ev2["high_gst"] = (ev2.role == "signal").astype(float)` |
| Frozen definition text | "role == 'signal' in the C5 matched population (all z >= 5.0); controls are the matched same-ticker/nearby non-spike events" | same | module docstring, lines 11 to 14 |
| Same text, persisted | `role=signal in C5 matched population (all z>=5.0)` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/frozen_definitions/high_gst` |
| Threshold, verified empirically | min signal z = **5.023**, max = **31.0985**, count below 5.0 = **0** across 152 signal rows | `Live Signal Engine/C5_PostEarnings_Population.csv` | `zscore` where `role == signal` |
| Variable | weekly Google Trends index for the ticker query | `GST_FixedWindow_PerEvent_Canonical.py` | `compute_zscore_at_anchor`, lines 124 to 143 |
| Normalization | `z = (gst_week - rolling_mean) / rolling_std`, rolling stats on `.shift(1)` so the event week never enters its own baseline; std floored at `1.0` | same | lines 127 to 131; `STD_EPSILON_FLOOR = 1.0` line 88 |
| Measurement window | prior **12** weeks, `min_periods = 8` | same | `ROLLING_WINDOW = 12` line 85, `MIN_PERIODS = 8` line 86 |
| Query window | one independent Trends query per event over a fixed-length window ending at that event's own decision date (spike week + 7 days), never extending past it | same | module header |
| Anchor tolerance | nearest pulled week must be within 6 days of the anchor | same | line 139 |

### 2a. Is z >= 5 a selection rule or an observed property? (resolved 2026-09-03)

**It is an explicit deterministic selection rule applied in producer code before matching.**
This was traced through the producers rather than inferred from the observed minimum.

| Step | Evidence |
|---|---|
| Threshold constant | `STRONG_Z = 5.0` — `GST_FixedWindow_PerEvent_Canonical.py` line 87 |
| Rule applied | `qualifies = (z is not None) and (z >= STRONG_Z)` — same file, line 273 |
| Persisted per event | column `qualifies_z5` in `Live Signal Engine/FixedWindow_PerEvent_Canonical.csv` |
| Signal arm filtered on it | `strong = canonical[(canonical["qualifies_z5"] == True) & (canonical["pnl_pct"].notna())]` — `GST_MatchedControlGroup_CanonicalRecompute.py` line 266; that file also sets `Z_THRESHOLD = 5.0` at line 68 |
| Clean partition, verified | 175 canonical events: `qualifies_z5 = True` n = 153, min z = 5.023, max 31.0985; `False` n = 22, min 1.3781, max 4.9568. **No True below 5.0 and no False at or above 5.0** |

The abstract therefore says signal events **"were selected for"** Google Trends spikes at least five
rolling standard deviations above the prior 12-week mean, which is the accurate formulation.

**Controls were not subject to that rule.** Control candidate dates were excluded only when within
+/-10 days of a spike drawn from the archived list (`SPIKE_EXCLUSION_BUFFER_DAYS`,
`GST_MatchedControlGroup_CanonicalRecompute.py` line 209); the control's own canonically recomputed
z-score was never constrained. That is why 20 of the 132 controls carrying a stored z sit at
z >= 5.0. The abstract discloses this explicitly.

**Three thresholds exist in the repository and only one governs these analyses.** `z >= 2.0` is the
base spike tier in `GST_Zscore_Spikes*.py` (`Z_THRESHOLD = 2.0`) used to build the general weekly
spike files. `pooled_z_cut = 4.0` is a reported-alongside repo convention, explicitly described in
the decomposition tool's own docstring as reported "alongside" the governing definition
(`/frozen_definitions/pooled_z_cut`). **Neither defines high attention here.** The operational
definition in force is `role == signal`, whose realized minimum is z = 5.023. This is stated as
"at least 5 rolling standard deviations" in the abstract, which is true of every treated event.

**Controls are not a z-threshold complement.** 20 of the 132 controls with a stored z are
themselves at z >= 5.0, and 36 at z >= 4.0. Controls were selected by matching, not by a cut.

### 2b. How far the control arm is attenuated (measured 2026-09-04)

The abstract states that matched controls were not required to fall below the signal threshold,
and now states how many exceeded it. Re-measured directly by replaying the frozen E1/E2 matching
in `tools/run_c5_control_matching_correction.py` over `retrospective_event_components.csv`:

| Fact | Value | Basis | Status |
|---|---|---|---|
| Surviving matched pairs | 73 | E1 self-match exclusion then E2 unique-control award | **CURRENT** |
| Controls at z >= 5 (STRONG tier) | **6** of 73 | control `zscore` in the surviving pairs | **CURRENT** |
| Controls at z >= 2 | 32 of 73 | same | **CURRENT** |
| Largest control z | 14.60 | same | **CURRENT** |
| Median treated z, among the 73 survivors | 7.28 | treated `zscore` in the surviving pairs | **CURRENT** |
| Median signal z, across all 152 signal events | 7.97 | `retrospective_event_components.csv`, role = signal | **CURRENT** |

**Two different medians, and the distinction matters.** The largest control z (14.60) exceeds both,
so the substantive point holds either way. But `GST_RETROSPECTIVE_CITATION_POLICY_v1.0_2026-09-04.md`
introduces `7.97` inside a clause beginning "among the 73 survivors", which reads as though 7.97 were
the survivors' median. It is not; it is the median over all 152 signal events. The survivors' median
is **7.28**. The policy's figure is real but its attribution is imprecise, and any text derived from
it must say which population it means.

## 3. Analysis-specific sample sizes

These analyses **do not share one estimation sample**. No single headline N is accurate.

| Analysis | N | Clusters | Estimand | Outcome | Source pointer | Status |
|---|---|---|---|---|---|---|
| Matched association (Level 1, primary) | **73 matched pairs** = 73 treated + 73 control = **146 event observations** | 26 tickers | ATT on \|day return\|, percentage points | absolute event-day return | `CORRECTED_RESULTS_v1.0.json` `/primary/n_pairs`, `/primary/estimand`, `/primary/inference/n_clusters`; `/sample/distinct_treated_identities` = 73, `/sample/distinct_control_identities` = 73 | **CURRENT** |
| Ticker-clustered magnitude (primary) | **217 events** (152 signal + 65 control) | **28** tickers | coefficient on the high-attention indicator, percentage points | absolute day return | `Correction_Overlays/2026-09-04_Pooled_Recompute/GST_POOLED_RECOMPUTE_RESULTS_2026-09-04.json` `/results/primary_magnitude_abs_day_return/after_corrected/{n,n_clusters}`, `/sample_audit` | **CURRENT** (supersedes the 285-row fit) |
| Incremental contribution (strategy E) | **217 events** | 28 tickers | marginal coefficient attributable to high attention over a price-and-calendar baseline | strategy E return | same, `/results/strategy_E_incremental_high_gst/after_corrected/{n,n_clusters}` | **CURRENT** (supersedes the 285-row fit) |
| Out-of-sample magnitude forecast | **136 pooled out-of-sample events**; folds 2023, 2024, 2025 | 26 tickers (paired loss test) | pooled MAE and the paired loss difference | `abs(open(T)/close(T-1) - 1)` | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` `/pooled_out_of_sample/*/n`, `/folds`, `/decisive_paired_loss_difference/clustered/{n,n_clusters}`, `/outcome` | **CURRENT** |
| Direction | **144 pooled out-of-sample events**; folds 2023, 2024, 2025 | not clustered | Brier score, AUC secondary | `sign(open(T)/close(T-1) - 1)` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` `/pooled_out_of_sample/*/n`, `/folds`, `/outcome` | **CURRENT** |
| Trading, standalone | **152 treated trades** | not clustered | mean net return per event | net event return | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTION_OVERLAY_2026-08-22.md` line 268, "One-sample statistics on the 152 treated trades" | **CURRENT** |

**Evaluation unit** for both out-of-sample analyses is the **event**. The forecasting build starts
from 285 source rows, deduplicates to 217 unique event identities (68 duplicate rows removed),
retains 189 after feature completeness, and pools 136 test-fold predictions across three
chronological expanding-window folds.

**Matched-analysis wording.** The matched analysis is **73 matched pairs**. Describing it only as
"146 observations" would obscure the pairing that the estimand depends on.

**The two arms now agree on the sample, and did not before.** The clustered regression previously
ran on all **285 source rows**, while the forecasting build above deduplicated the same source to
**217 unique event identities (68 duplicate rows removed)**. The 2026-09-04 recompute's three
frozen membership rules land on **exactly that 217**: verified directly against
`retrospective_event_components.csv`, the 285 rows contain 217 distinct `(ticker, earnings_date)`
identities, of which 152 carry a signal label and 65 are control-only. The rules are therefore
equivalent to *one row per event identity, signal label wins* -- the convention the forecasting arm
already used. This is corroboration the frozen design did not aim at: the pooled regression was the
only analysis in the paper not deduplicated to event identities.

## 4. Headline estimates used in the AARE abstract

| Claim | Abstract precision | Full-precision stored | Source | Pointer | Status |
|---|---|---|---|---|---|
| Matched mean paired difference | 2.08 pp | `2.0797` | `CORRECTED_RESULTS_v1.0.json` | `/primary/mean_paired_difference_pp` | **CURRENT** |
| Matched p | p = .004 | `0.00397` | same | `/primary/inference/p_value` | **CURRENT** |
| Clustered coefficient | 2.72 pp | `2.7199` | `Correction_Overlays/2026-09-04_Pooled_Recompute/GST_POOLED_RECOMPUTE_RESULTS_2026-09-04.json` | `/results/primary_magnitude_abs_day_return/after_corrected/coef_pp` | **CURRENT** (supersedes `1.509`) |
| Clustered p | p = .0003 | `0.00031` | same | `.../p_value` | **CURRENT** (supersedes `0.0662`) |
| Clustered 95% CI | excludes zero | `[1.4294, 4.0104]` | same | `.../ci95_pp` | **CURRENT** (supersedes `[-0.1133, 3.1313]`; the "spanning zero" wording is withdrawn) |
| Incremental coefficient | 0.77 pp | `0.7665` | same | `/results/strategy_E_incremental_high_gst/after_corrected/coef_pp` | **CURRENT** (supersedes `0.0131`) |
| Incremental p | p = .17 | `0.16525` | same | `.../p_value` | **CURRENT** (supersedes `0.98332`; still null, but by a much narrower margin) |
| OOS MAE with attention | 3.630 pp | `3.6299` | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/pooled_out_of_sample/C_baseline_plus_gst/mae_pp` | **CURRENT** |
| OOS MAE without attention | 3.628 pp | `3.6284` | same | `/pooled_out_of_sample/B_baseline_no_gst/mae_pp` | **CURRENT** |
| Paired loss-difference p | p = .98 | `0.9827` | same | `/decisive_paired_loss_difference/clustered/p_value` | **CURRENT** |
| Direction, model Brier | "worse calibrated" | `0.2711` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `/pooled_out_of_sample/logistic_l2/brier` | **CURRENT** |
| Direction, base-rate Brier | "worse calibrated" | `0.256` | same | `/pooled_out_of_sample/intercept_only_prevalence/brier` | **CURRENT** |
| Standalone strategy return | 0.85% per event | `0.8543` | `CORRECTION_OVERLAY_2026-08-22.md` line 268, `/scorecard` | `mean_net_pct` | **CURRENT** |

## 5. Claims deliberately excluded from the AARE abstract

| Excluded | Value | Status | Why excluded |
|---|---|---|---|
| Unmatched mechanism-stability comparison | 7.72% vs 3.72%, Cohen's d = 1.294, permutation p < .0001 | **HISTORICAL_CONTEXT** | Different study, unmatched, compared against random weeks rather than matched earnings events, no stored confidence interval. Appendix A.3 only. Never a headline |
| Original unmatched-control Q1 figure | +1.4411 pp, t = 2.138 | **SUPERSEDED** | Artifact carries `citation_status = SUPERSEDED_BY_THIS_ARTIFACT` |
| Sensitivity D | +2.5682 pp, p = 0.00075 | **SENSITIVITY** | Largest estimate and smallest p in the family; promoting it would be the specification shopping the paper documents |
| Benchmark-adjusted and deduplicated variants | p = 0.03707, p = 0.00193 | **SENSITIVITY** | Not the designated primary estimand |

## 6. Statements the abstract does not make

The abstract does not claim causation, does not average or reconcile the matched and clustered
estimates, does not present the clustered p = .066 as evidence against prediction, and does not
present the standalone 0.85 percent as an attention result. The null-prediction conclusion rests
on the incremental coefficient, the out-of-sample error comparison, and directional calibration.

## 7. Authorship record

No committed manuscript artifact states an author name, affiliation, correspondence address, or
acknowledgments. `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md` contains none of them, and no
acknowledgments section exists. No person other than Harshith Akurati is named as an author
anywhere in the repository, so no mentor or adviser was added to the title page.

`hakurati11@gmail.com` appears in the repository, but only in script `USER_AGENT` and contact
headers (for example `Backtest_Data_Pull.py` line 42), never in a manuscript artifact. It was
therefore **not** promoted to a correspondence address; the title page carries a marked blank
field instead.
