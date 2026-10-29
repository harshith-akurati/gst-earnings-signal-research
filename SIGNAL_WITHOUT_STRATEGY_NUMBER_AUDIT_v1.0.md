# Signal Without Strategy — number-to-source audit v1.0

**Date:** 2026-08-27 · **Manuscript audited:** `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md`
**Branch:** `manuscript-v1.1-revision-20260827` · **Base:** `phase6-control-matching-integrity` @ `63e8a13d8fadc4a52b8046df983fb6a8705e9985`

Every headline statistic in v1.1 is listed with the exact committed artifact path and field it
was read from. No value was typed from memory, from a prior draft, or from conversation.

**Result: 35 of 35 claims verified. 0 discrepancies.**

## Source artifact hashes

| Artifact | SHA-256 |
|---|---|
| `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `0e2fb1694deb3c4f6d9be7f6505537e72350cade7167f981a2f77447252f066e` |
| `Live Signal Engine/MechanismStability_Results.csv` | `37b3768e06f75fd0219f65f098c879ff67c4ef11fac96acc4d4295d4486e509a` |
| `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `6c61ef4489c239b54452d30553ac4e13e29c61d38de623d50e68207bf7d76b69` |
| `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `3d8fbb85d9388d1ea1391aa31a98484a4ed1c0f81d63eda416c82a490574590d` |

## Claim-to-source table

| # | Claim | Manuscript §| Source artifact | Field / JSON pointer | Value | Match |
|---|---|---|---|---|---|---|
| 1 | `2.0797` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/mean_paired_difference_pp` | `2.0797` | ✅ |
| 2 | `0.00397` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/primary/inference/p_value` | `0.00397` | ✅ |
| 3 | `1.9591` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/coef_pp` | `1.9591` | ✅ |
| 4 | `0.05125` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/a_reuse_retained_self_match_excluded/p_value` | `0.05125` | ✅ |
| 5 | `8.0286` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/mean_treated_pp` | `8.0286` | ✅ |
| 6 | `5.9489` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/mean_control_pp` | `5.9489` | ✅ |
| 7 | `0.02014` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/b_unpaired_welch_on_corrected_arms/p_value` | `0.02014` | ✅ |
| 8 | `1.8343` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/min` | `1.8343` | ✅ |
| 9 | `2.3772` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/max` | `2.3772` | ✅ |
| 10 | `26` | 5.1 | `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json` | `/sensitivity/c_leave_one_ticker_out_mean_paired_diff_pp/n_refits` | `26` | ✅ |
| 11 | `1.509` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/coef_pp` | `1.509` | ✅ |
| 12 | `0.7664` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/cr2_se_pp` | `0.7664` | ✅ |
| 13 | `16.301` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/satterthwaite_df` | `16.301` | ✅ |
| 14 | `0.0662` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/p_value` | `0.0662` | ✅ |
| 15 | `-0.1133` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/ci95_pp/0` | `-0.1133` | ✅ |
| 16 | `3.1313` | 5.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/primary_magnitude_abs_day_return/ci95_pp/1` | `3.1313` | ✅ |
| 17 | `1.5388` | 5.2 (not promoted) | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/magnitude_abs_excess_vs_spy/coef_pp` | `1.5388` | ✅ |
| 18 | `0.03707` | 5.2 (not promoted) | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/magnitude_abs_excess_vs_spy/p_value` | `0.03707` | ✅ |
| 19 | `0.0131` | 5.3 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/strategy_E_incremental_high_gst/coef_pp` | `0.0131` | ✅ |
| 20 | `0.98332` | 5.3 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/clustered_inference/strategy_E_incremental_high_gst/p_value` | `0.98332` | ✅ |
| 21 | `7.8871` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/high_mean_abs_pct` | `7.8871` | ✅ |
| 22 | `6.4459` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/control_mean_abs_pct` | `6.4459` | ✅ |
| 23 | `1.4411` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/difference_pp` | `1.4411` | ✅ |
| 24 | `2.138` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/t_stat` | `2.138` | ✅ |
| 25 | `152` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/n_high` | `152` | ✅ |
| 26 | `133` | App A.2 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | `/Q1_abs_move_high_vs_control/n_control` | `133` | ✅ |
| 27 | `3.6299` | 5.5 | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/pooled_out_of_sample/C_baseline_plus_gst/mae_pp` | `3.6299` | ✅ |
| 28 | `3.6284` | 5.5 | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/pooled_out_of_sample/B_baseline_no_gst/mae_pp` | `3.6284` | ✅ |
| 29 | `0.9827` | 5.5 | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | `/decisive_paired_loss_difference/clustered/p_value` | `0.9827` | ✅ |
| 30 | `7.72` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.spike_mean_move_pct` | `7.72` | ✅ |
| 31 | `3.72` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.baseline_mean_move_pct` | `3.72` | ✅ |
| 32 | `1.294` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.cohens_d` | `1.294` | ✅ |
| 33 | `147` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.n_spike` | `147` | ✅ |
| 34 | `1275` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.n_baseline` | `1275` | ✅ |
| 35 | `4.0` | App A.3 | `Live Signal Engine/MechanismStability_Results.csv` | `full_sample.diff_mean_pt` | `4.0` | ✅ |

## Supersession record

| Quantity | Status |
|---|---|
| `Q1_abs_move_high_vs_control` (+1.4411 pp) | **SUPERSEDED** by the 2026-08-22 control-matching overlay. Artifact carries `citation_status = SUPERSEDED_BY_THIS_ARTIFACT`. Retained in Appendix A.2 as history; **not** the current estimate |
| Corrected matched paired difference (+2.0797 pp) | **CURRENT** Level-1 estimate, §5.1 |
| Mechanism-stability spike-vs-random-week (7.72 / 3.72 / d = 1.294) | **NOT A HEADLINE RESULT.** Different study, unmatched design, different comparison group. Appendix A.3 only |

## Values deliberately reported but not promoted

| Value | Where | Why not promoted |
|---|---|---|
| `+1.5388 pp`, `p = 0.03707` (abs excess vs SPY) | §5.2 | Secondary metric. The primary gate was designated in advance at `primary_magnitude_abs_day_return` (p = 0.0662). Promoting the significant variant would be specification shopping |
| `0.8543%` standalone strategy return | §5.3 | Post-earnings drift present without the attention filter. Not an attention result |
| `d = 1.294` | Appendix A.3 | Large *unmatched descriptive* effect; no stored confidence interval; not comparable to the matched estimate |

## Method

Each claim was resolved by direct JSON-pointer or CSV-field lookup against the committed artifact,
compared to the manuscript string, and required to match exactly or within 1e-9. Failures would have
blocked the commit. No analysis was rerun and no new result was generated.

