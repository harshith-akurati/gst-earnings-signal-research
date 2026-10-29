# Signal Without Strategy v1.1 — figure and table plan

**Date:** 2026-08-27 · For `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.1_DRAFT.md`

Every display below uses **only committed results**. No confidence interval was computed, no
statistic was created, and no analysis was rerun to complete a display. Fields absent from the
artifacts are marked **"not in artifact"** and left blank rather than filled.

---

## Table 1 — Samples, estimands, and evidence level

Purpose: make it impossible to read four different analyses as one. Placed in §4A.

| Analysis | Sample | n | Estimand | Inference | Evidence level |
|---|---|---|---|---|---|
| Corrected matched association | Matched treated/control earnings-event pairs, post-correction | 73 pairs, 26 clusters | ATT on \|day return\|, pp | CR2 (BRL) on ticker, Satterthwaite df | **1 — Association** |
| Ticker-clustered magnitude model | Full usable event population | 26 clusters, df 16.301 | Coefficient on high-attention indicator, pp | CR2 on ticker, Satterthwaite df | **1 — Association** |
| Out-of-sample magnitude forecast | Pooled out-of-sample events | per artifact | Pooled MAE, pp; paired loss difference | Paired clustered test | **2 — Incremental prediction** |
| Direction forecast | Pooled out-of-sample events | per artifact | Brier score; AUC | Pooled out-of-sample comparison | **2 — Incremental prediction** |
| Strategy E incremental | Event strategy population | 26 clusters | Coefficient attributable to high attention, pp | CR2 on ticker, Satterthwaite df | **3 — Tradability** |

**Rule for this table.** The evidence-level column is the point. Rows 1–2 are association; clearing
them says nothing about rows 3–5.

---

## Table 2 — Matched Level-1 association: primary and all four sensitivities

Placed in §5.1. **Already drafted in the manuscript.** Reproduced here as the display spec.

| Column | Source |
|---|---|
| Specification | label |
| n pairs | `/primary/n_pairs`, `/sensitivity/*/n_pairs` |
| Estimate (pp) | `coef_pp` / `mean_paired_difference_pp` / `min`–`max` for C |
| SE (pp) | `cr2_se_pp` — **not in artifact** for B and C |
| df | `satterthwaite_df`; `welch_df` for B — **not in artifact** for C |
| t | `t_stat` — **not in artifact** for C |
| p | `p_value` — **not in artifact** for C |
| 95% CI (pp) | `ci95_pp` — **not in artifact** for B and C |
| Status | PRIMARY / sensitivity |

**Typographic requirements.**

1. The primary row is **bold**; all four sensitivity rows are plain.
2. **Sensitivity D must carry its exclusion in the row label**, not a footnote: "excluding the 8
   overlap identities". Its 65 pairs must be visible in the same row as its +2.5682 pp.
3. No row may be sorted by p-value. Order is Primary, A, B, C, D — never ascending significance.
4. Empty cells stay empty. Do not interpolate, estimate, or borrow a CI from a neighbouring row.

---

## Table 3 — Incremental forecasting and trading tests

Placed in §5.3–§5.5. This is the table that carries the paper's negative result.

| Test | Comparison | Metric | With attention | Without attention | p | Verdict |
|---|---|---|---|---|---|---|
| Strategy E incremental | Baseline + attention vs baseline | Coefficient, pp | **+0.0131** | — | **0.98332** | **Null** |
| OOS magnitude forecast | Model C vs model B | Pooled MAE, pp | **3.6299** | **3.6284** | **0.9827** | **Null — marginally worse** |
| Direction forecast | Logistic vs intercept-only | Brier (lower better) | **0.2711** | **0.2560** | not in artifact | **Null — worse than baseline** |
| Direction forecast | Logistic | AUC | **0.4654** | 0.5 = chance | not in artifact | **Below chance** |

**Rule.** The "With attention" column must not be typeset as an improvement. Where the attention
model is worse — MAE, Brier, AUC — that direction must be visible without reading the caption.

---

## Figure 1 — Evidence ladder

**Existing asset, retained unchanged:** `SIGNAL_WITHOUT_STRATEGY_FIGURE_1_EVIDENCE_LADDER.svg`,
built by the committed `tools/build_signal_without_strategy_figures.py`. No underlying number
changed in v1.1, so **do not regenerate it.**

Three rungs, ascending: **Association → Incremental prediction → Tradability**. v1.1 requires only a
caption change, marking where attention stops:

> Attention clears rung 1 (matched association, +2.0797 pp, p = 0.00397) and fails rungs 2 and 3
> (incremental contribution +0.0131 pp, p = 0.98332; no out-of-sample forecast improvement). Clearing
> rung 1 does not establish rungs 2 or 3.

---

## Figure 2 — Primary versus sensitivity estimates, estimands visually separated

**`PROPOSED` — presentation only, no new statistics.** Every value already exists in Table 2 and §5.2.

**Design.** Horizontal coefficient plot, points with 95% CI whiskers where a CI exists in the
artifact, grouped into **two visually separated panels** because the estimands differ:

*Panel A — matched-pair ATT (73 pairs unless noted):*

| Row | Estimate | CI | Style |
|---|---|---|---|
| Primary paired difference | +2.0797 | [+0.7479, +3.4116] | filled marker, heavy rule |
| Sensitivity A (113 pairs) | +1.9591 | [−0.0120, +3.9302] | open marker |
| Sensitivity B (unpaired Welch) | +2.0797 | **no CI in artifact — point only, no whisker** | open marker, hollow |
| Sensitivity C (range, 26 refits) | 1.8343–2.3772 | range bar, not a CI — label as range | grey band |
| Sensitivity D (65 pairs) | +2.5682 | [+1.2354, +3.9009] | open marker |

*Panel B — full-population regression coefficient (different estimand, do not compare point-to-point
with Panel A):*

| Row | Estimate | CI | Style |
|---|---|---|---|
| Primary clustered magnitude | +1.509 | [−0.1133, +3.1313] | filled marker, heavy rule |
| Benchmark-adjusted sensitivity | +1.5388 | not in artifact | open marker |

**Binding rules.**

1. **Panels A and B must be visually separated** — separate axes or a labelled rule. They are
   different estimands on different samples; placing them on one continuous axis invites the reader
   to treat +2.0797 and +1.509 as competing estimates of one quantity. They are not.
2. **Sensitivity C's bar is a range across refits, not a confidence interval.** It must be styled
   differently from every CI whisker and labelled in-figure.
3. **Sensitivity B and the benchmark-adjusted row get no whisker.** No CI exists; drawing one would
   fabricate a statistic.
4. **The zero line must be drawn and must remain visible.** The primary clustered estimate's interval
   crosses it, and truncating the axis to hide that crossing would misrepresent the paper's own
   headline caution.
5. **No sorting by significance.** Fixed order as tabulated.

---

## Integrity rules for all displays

1. **No display may present `d = 1.294` alongside matched estimates.** It is an unmatched
   spike-versus-random-week comparison from a different study. Appendix A.3 text only — no figure,
   no shared axis.
2. **No display may promote `p = 0.03707`, `p = 0.00193`, or `p = 0.00075`** to headline position.
   The primary magnitude result is `p = 0.0662`; the primary matched result is `p = 0.00397`.
3. **No display may present the 0.8543% standalone return as attention performance.** The same
   post-earnings drift existed without the attention filter.
4. **No display may contain prospective HYP-01 data.** None exists.
5. **No display may use causal or alpha language** in title, axis label, or caption.

## Build checklist

- [ ] Table 1 typeset in §4A
- [ ] Table 2 typeset in §5.1 with D's exclusion in the row label and empty cells left empty
- [ ] Table 3 typeset with worse-than-baseline direction visible
- [ ] Figure 1 retained unmodified; caption updated
- [ ] Decide Figure 2 (`PROPOSED`) — recommended, presentation-only
- [ ] Confirm no display violates integrity rules 1–5
