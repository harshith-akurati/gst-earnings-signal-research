# Signal Without Strategy v1.1 — number-to-source audit

**Date:** 2026-08-27 · **Audits:** `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md`
**Branch:** `manuscript-v1.1-revision-20260827` · **Base:** `phase6-control-matching-integrity` @ `63e8a13d8fadc4a52b8046df983fb6a8705e9985`

Every numerical claim in v1.1 with its exact source location, full-precision stored value,
rounding rule, and status. No value was typed from memory or from a prior draft.

**Status vocabulary.** `CURRENT` — the estimate v1.1 relies on. `SENSITIVITY` — reported
alongside a primary, never promoted. `SUPERSEDED` — replaced by a newer artifact, retained
for provenance only. `HISTORICAL_CONTEXT` — a different study, appendix only, not a
manuscript result.

## Source artifacts

| Artifact | SHA-256 |
|---|---|
| `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `0e2fb1694deb3c4f6d9be7f6505537e72350cade7167f981a2f77447252f066e` |
| `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `3d8fbb85d9388d1ea1391aa31a98484a4ed1c0f81d63eda416c82a490574590d` |
| `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `6c61ef4489c239b54452d30553ac4e13e29c61d38de623d50e68207bf7d76b69` |
| `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `3e94185c75060dca0ab7a5b03578183faf311ac30a701b92c8347b6c22517511` |
| `Live Signal Engine/MechanismStability_Results.csv` | `37b3768e06f75fd0219f65f098c879ff67c4ef11fac96acc4d4295d4486e509a` |

## Claim table

| # | Manuscript § | Displayed | Source file | JSON pointer / CSV field | Full-precision source | Rounding | Status |
|---|---|---|---|---|---|---|---|
| 1 | 1 Abstract / 5.1 / Table 2 | `+2.0797 pp` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/mean_paired_difference_pp` | `2.0797` | none (exact) | **CURRENT** |
| 2 | 5.1 / Table 2 | `0.00397` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/p_value` | `0.00397` | none (exact) | **CURRENT** |
| 3 | 5.1 / Table 2 | `0.638` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/cr2_se_pp` | `0.638` | none (exact) | **CURRENT** |
| 4 | 5.1 / Table 2 | `19.742` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/satterthwaite_df` | `19.742` | none (exact) | **CURRENT** |
| 5 | 5.1 / Table 2 | `3.260` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/t_stat` | `3.26` | trailing zero added | **CURRENT** |
| 6 | 5.1 / Table 2 | `+0.7479` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/ci95_pp/0` | `0.7479` | none (exact) | **CURRENT** |
| 7 | 5.1 / Table 2 | `+3.4116` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/ci95_pp/1` | `3.4116` | none (exact) | **CURRENT** |
| 8 | 5.1 / Table 2 | `73` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/n_pairs` | `73` | none (exact) | **CURRENT** |
| 9 | 5.1 / Table 2 | `+1.9591 pp` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/coef_pp` | `1.9591` | none (exact) | **SENSITIVITY** |
| 10 | 5.1 / Table 2 | `0.05125` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/p_value` | `0.05125` | none (exact) | **SENSITIVITY** |
| 11 | 5.1 / Table 2 | `0.9254` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/cr2_se_pp` | `0.9254` | none (exact) | **SENSITIVITY** |
| 12 | 5.1 / Table 2 | `15.118` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/satterthwaite_df` | `15.118` | none (exact) | **SENSITIVITY** |
| 13 | 5.1 / Table 2 | `113` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/n_pairs` | `113` | none (exact) | **SENSITIVITY** |
| 14 | 5.1 / Table 2 | `8.0286%` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/mean_treated_pp` | `8.0286` | none (exact) | **SENSITIVITY** |
| 15 | 5.1 / Table 2 | `5.9489%` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/mean_control_pp` | `5.9489` | none (exact) | **SENSITIVITY** |
| 16 | 5.1 / Table 2 | `0.02014` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/p_value` | `0.02014` | none (exact) | **SENSITIVITY** |
| 17 | 5.1 / Table 2 | `138.58` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/welch_df` | `138.58` | none (exact) | **SENSITIVITY** |
| 18 | 5.1 / Table 2 | `+1.8343` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/min` | `1.8343` | none (exact) | **SENSITIVITY** |
| 19 | 5.1 / Table 2 | `+2.3772` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/max` | `2.3772` | none (exact) | **SENSITIVITY** |
| 20 | 5.1 / Table 2 | `26 refits` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/n_refits` | `26` | none (exact) | **SENSITIVITY** |
| 21 | 5.1 / Table 2 | `+2.5682 pp` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/coef_pp` | `2.5682` | none (exact) | **SENSITIVITY** |
| 22 | 5.1 / Table 2 | `0.00075` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/p_value` | `0.00075` | none (exact) | **SENSITIVITY** |
| 23 | 5.1 / Table 2 | `0.6347` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/cr2_se_pp` | `0.6347` | none (exact) | **SENSITIVITY** |
| 24 | 5.1 / Table 2 | `18.128` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/satterthwaite_df` | `18.128` | none (exact) | **SENSITIVITY** |
| 25 | 5.1 / Table 2 | `4.046` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/t_stat` | `4.046` | none (exact) | **SENSITIVITY** |
| 26 | 5.1 / Table 2 | `+1.2354` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/ci95_pp/0` | `1.2354` | none (exact) | **SENSITIVITY** |
| 27 | 5.1 / Table 2 | `+3.9009` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/ci95_pp/1` | `3.9009` | none (exact) | **SENSITIVITY** |
| 28 | 5.1 / Table 2 | `65` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/d_excluding_8_overlap_identities/n_pairs` | `65` | none (exact) | **SENSITIVITY** |
| 29 | 5.1 balance | `3.619` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/e_balance/mean_abs_pre_drift_treated_pp` | `3.619` | none (exact) | **SENSITIVITY** |
| 30 | 5.1 balance | `2.9662` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/e_balance/mean_abs_pre_drift_control_pp` | `2.9662` | none (exact) | **SENSITIVITY** |
| 31 | 5.1 attrition | `133` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sample/pairs_before_correction` | `133` | none (exact) | **CURRENT** |
| 32 | 5.1 attrition | `20` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sample/dropped_self_match_E1` | `20` | none (exact) | **CURRENT** |
| 33 | 5.1 attrition | `40` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sample/dropped_no_unique_control_E2` | `40` | none (exact) | **CURRENT** |
| 34 | 5.1 attrition | `73` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sample/surviving_pairs` | `73` | none (exact) | **CURRENT** |
| 35 | 5.1 attrition | `60` | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sample/observations_lost_vs_original_treated_arm` | `60` | none (exact) | **CURRENT** |
| 36 | 5.2 / Table 2 | `+1.509 pp` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/coef_pp` | `1.509` | none (exact) | **CURRENT** |
| 37 | 5.2 | `0.7664` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/cr2_se_pp` | `0.7664` | none (exact) | **CURRENT** |
| 38 | 5.2 | `16.301` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/satterthwaite_df` | `16.301` | none (exact) | **CURRENT** |
| 39 | 5.2 | `0.0662` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/p_value` | `0.0662` | none (exact) | **CURRENT** |
| 40 | 5.2 | `-0.1133` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/ci95_pp/0` | `-0.1133` | none (exact) | **CURRENT** |
| 41 | 5.2 | `+3.1313` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/ci95_pp/1` | `3.1313` | none (exact) | **CURRENT** |
| 42 | 5.2 sensitivity | `+1.5388 pp` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/magnitude_abs_excess_vs_spy/coef_pp` | `1.5388` | none (exact) | **SENSITIVITY** |
| 43 | 5.2 sensitivity | `0.03707` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/magnitude_abs_excess_vs_spy/p_value` | `0.03707` | none (exact) | **SENSITIVITY** |
| 44 | 5.2 sensitivity | `0.00193` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/repeated_control_sensitivity/deduplicated_cr2/p_value` | `0.00193` | none (exact) | **SENSITIVITY** |
| 45 | 5.3 / Table 3 | `+0.0131 pp` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/strategy_E_incremental_high_gst/coef_pp` | `0.0131` | none (exact) | **CURRENT** |
| 46 | 5.3 / Table 3 | `0.98332` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/strategy_E_incremental_high_gst/p_value` | `0.98332` | none (exact) | **CURRENT** |
| 47 | 5.5 / Table 3 | `3.6299` | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/pooled_out_of_sample/C_baseline_plus_gst/mae_pp` | `3.6299` | none (exact) | **CURRENT** |
| 48 | 5.5 / Table 3 | `3.6284` | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/pooled_out_of_sample/B_baseline_no_gst/mae_pp` | `3.6284` | none (exact) | **CURRENT** |
| 49 | 5.5 / Table 3 | `0.9827` | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/decisive_paired_loss_difference/clustered/p_value` | `0.9827` | none (exact) | **CURRENT** |
| 50 | 5.4 / Table 3 | `0.2560` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `/pooled_out_of_sample/intercept_only_prevalence/brier` | `0.256` | 4 dp as stored | **CURRENT** |
| 51 | 5.4 / Table 3 | `0.2711` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `/pooled_out_of_sample/logistic_l2/brier` | `0.2711` | 4 dp as stored | **CURRENT** |
| 52 | 5.4 / Table 3 | `0.4654` | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | `/pooled_out_of_sample/logistic_l2/auc` | `0.4654` | 4 dp as stored | **CURRENT** |
| 53 | App A.2 | `7.8871%` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/high_mean_abs_pct` | `7.8871` | none (exact) | **SUPERSEDED** |
| 54 | App A.2 | `6.4459%` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/control_mean_abs_pct` | `6.4459` | none (exact) | **SUPERSEDED** |
| 55 | App A.2 | `+1.4411 pp` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/difference_pp` | `1.4411` | none (exact) | **SUPERSEDED** |
| 56 | App A.2 | `2.138` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/t_stat` | `2.138` | none (exact) | **SUPERSEDED** |
| 57 | App A.2 | `152` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/n_high` | `152` | none (exact) | **SUPERSEDED** |
| 58 | App A.2 | `133` | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/n_control` | `133` | none (exact) | **SUPERSEDED** |
| 59 | App A.3 | `7.72%` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.spike_mean_move_pct` | `7.72` | none (exact) | **HISTORICAL_CONTEXT** |
| 60 | App A.3 | `3.72%` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.baseline_mean_move_pct` | `3.72` | none (exact) | **HISTORICAL_CONTEXT** |
| 61 | App A.3 | `1.294` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.cohens_d` | `1.294` | none (exact) | **HISTORICAL_CONTEXT** |
| 62 | App A.3 | `147` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.n_spike` | `147` | none (exact) | **HISTORICAL_CONTEXT** |
| 63 | App A.3 | `1,275` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.n_baseline` | `1275` | thousands separator added | **HISTORICAL_CONTEXT** |
| 64 | App A.3 | `6.63%` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.spike_median_move_pct` | `6.63` | none (exact) | **HISTORICAL_CONTEXT** |
| 65 | App A.3 | `3.03%` | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.baseline_median_move_pct` | `3.03` | none (exact) | **HISTORICAL_CONTEXT** |

**Total claims audited: 65. Resolution failures: 0.**

## Required distinctions, stated explicitly

| Quantity | Status | Why |
|---|---|---|
| Corrected matched association, **+2.0797 pp, p = 0.00397** | `CURRENT` | Newest explicitly superseding artifact; the manuscript's Level-1 estimate |
| Original Q1, **+1.4411 pp, t = 2.138** | `SUPERSEDED` | Artifact carries `citation_status = SUPERSEDED_BY_THIS_ARTIFACT`. Appendix A.2 only |
| Unmatched mechanism-stability, **7.72% / 3.72%, d = 1.294** | `HISTORICAL_CONTEXT` | Different study, different comparison group (random weeks), unmatched, no stored CI. Appendix A.3 only. **Never a headline, never matched, never predictive** |
| Primary clustered magnitude, **+1.509 pp, p = 0.0662** | `CURRENT` | Designated primary in advance; CI spans zero |
| Sensitivities **p = 0.03707**, **p = 0.00193**, **p = 0.00075** | `SENSITIVITY` | All significant; none promoted over the primary; none is incremental prediction |
| Strategy E incremental, **+0.0131 pp, p = 0.98332** | `CURRENT` | Null. Level 2 |
| OOS magnitude, **3.6299 vs 3.6284, p = 0.9827** | `CURRENT` | Null. Level 2 |
| Direction, Brier **0.2711** vs **0.2560**, AUC **0.4654** | `CURRENT` | Null; worse than baseline. Level 2 |

## Sensitivity D — full disclosure

`/sensitivity/d_excluding_8_overlap_identities` yields **+2.5682 pp, p = 0.00075**, the largest
estimate and smallest p-value of any matched specification. It excludes the eight identities that are
both self-matched and reused, named in the frozen design: LDOS 2021-08-03, LDOS 2023-10-31,
NFLX 2022-01-20, NFLX 2023-01-19, NKE 2024-03-21, QCOM 2025-02-05, SBUX 2025-01-28, STZ 2025-01-10.

It is reported in Table 2 and audited above with status `SENSITIVITY`. It does **not** appear in the
title, the abstract headline, or the conclusion, and it does not replace the primary paired estimate.
It is a Level-1 association on a restricted subset — not incremental prediction, not causal, not alpha.

## Fields deliberately not computed

| Missing | Where | Why not supplied |
|---|---|---|
| 95% CI for sensitivity B | Table 2 | Not present in the artifact. Computing one would create a new statistic |
| SE / df / CI for sensitivity C | Table 2 | The artifact stores only the range of point estimates across refits |
| CI for Cohen's d = 1.294 | Appendix A.3 | Source script stores point estimates and a permutation p-value only |

## Discrepancy recorded, not reconciled

The frozen corrective design specifies leave-one-ticker-out over **28** refits
(`CORRECTIVE_DESIGN_v1.0_FROZEN_2026-08-22.md`). The committed results report **26** refits and 26
entries in `by_excluded_ticker`. v1.1 reports the realised **26** and flags the difference. Nothing
was recomputed to reconcile it.

