# Corrective report — C5 matched-control defects

**Date:** 2026-08-22
**Design:** `CORRECTIVE_DESIGN_v1.0_FROZEN_2026-08-22.md`, frozen at `63ed0cb` **before** this run.
**Runs executed:** exactly one. No rule was changed after seeing output.
**Scope:** `RETROSPECTIVE_DEVELOPMENT_ONLY_NOT_HYP01_CONFIRMATION`.

---

## 1. Sample: original versus corrected

| | Original | Corrected |
|---|---|---|
| Treated rows | 152 | — |
| Control rows | 133 | — |
| Matched pairs entering correction | 133 | 133 |
| Dropped — self-match (E1) | — | **20** |
| Dropped — no unique control (E2) | — | **40** |
| **Surviving pairs** | — | **73** |
| Distinct treated identities | 152 | 73 |
| Distinct control identities | **85** (of 133 rows) | **73** (of 73 rows) |
| Ticker clusters | 28 | **26** |

> **Observations lost: 60 of 133 pairs — 45.1%.** Two tickers drop out entirely, taking the cluster
> count from 28 to 26.

---

## 2. Effect estimate: original versus corrected

| | Original | Corrected (primary) |
|---|---|---|
| Statistic | unpaired Welch, 152 vs 133 | mean paired difference, 73 pairs |
| Treated mean \|day return\| | 7.8871 pp | 8.0286 pp |
| Control mean \|day return\| | 6.4459 pp | 5.9489 pp |
| **Effect** | **1.4411 pp** | **2.0797 pp** |
| SE | (Welch, implicit) | 0.6380 pp (CR2/BRL) |
| df | — | 19.742 (Satterthwaite) |
| **t** | **2.138** | **3.260** |
| p | — | **0.00397** |
| 95% CI | — | **[0.748, 3.412] pp** |
| Clusters | — | 26, on ticker |

Naive paired t on the same 73 pairs is 2.492, reported for reference only; **CR2 is the inferential
basis**, and here it is *less* forgiving than the naive statistic on df while still clearing zero.

**The corrected effect is larger, not smaller.** Removing 20 events that sat in both arms removed
observations that were mechanically pulling the two group means together.

---

## 3. Sensitivity analyses (all pre-specified)

| Analysis | n | Effect (pp) | t | p | 95% CI |
|---|---|---|---|---|---|
| **(a) Reuse retained, self-match excluded** | 113 pairs | 1.9591 | 2.117 | **0.0513** | **[−0.012, 3.930]** |
| **(b) Unpaired Welch on corrected arms** | 73 v 73 | 2.0797 | 2.351 | 0.0201 | — |
| **(c) Leave-one-ticker-out** | 26 refits | **1.834 → 2.377** | — | — | — |
| **(d) Excluding 8 overlap identities** | 65 pairs | 2.5682 | 4.046 | 0.00075 | [1.235, 3.901] |

**(a) is the result that most deserves attention, and it cuts against the primary.** When control
reuse is *retained* and only self-matching is fixed, the interval **touches zero** (p = 0.051). The
primary's significance therefore depends materially on removing reuse, not only on removing
self-matches. Both defects had to be corrected for the result to clear zero — fixing either alone
would not have sufficed.

**(c)** shows no single firm drives the point estimate: the full leave-one-out range, 1.83–2.38 pp,
sits inside the primary's confidence interval.

**(b)** confirms the change is not an artefact of switching from an unpaired to a paired statistic —
the unpaired form on the corrected arms gives the same 2.0797 pp.

---

## 4. Balance and matching diagnostics

| Diagnostic | Treated | Control |
|---|---|---|
| Mean \|pre-event drift\| | **3.619 pp** | **2.966 pp** |
| Same-ticker pairs | 72 of 73 | |
| BMO/AMC concordant pairs | **73 of 73** | |
| Year distribution | 2021: 9 · 2022: 13 · 2023: 19 · 2024: 18 · 2025: 14 | 2021: 15 · 2022: 14 · 2023: 12 · 2024: 13 · 2025: 19 |

Two imbalances, neither introduced by this correction:

1. **Pre-event drift is not balanced** — treated events carry 0.65 pp more absolute pre-drift than
   their controls. The original matcher balanced on volatility band, sector and market cap, **not**
   on pre-event drift. Some of the measured effect may reflect that the treated events were already
   moving more before the event. This is a **pre-existing design property** and remains uncorrected.
2. **Calendar composition is tilted** — treated events skew later (2023–2024), controls earlier
   (2021, 2025). Matching had no calendar caliper.

Release-timing balance is perfect (73/73), and matching is essentially within-firm (72/73).

---

## 5. Does the prior substantive conclusion survive?

> **SURVIVES**, on this outcome, with the qualifications below.

The prior substantive claim — that high-GST earnings events show larger absolute event-day moves
than matched control earnings events — holds after correction and is **larger** than reported:
2.08 pp versus 1.44 pp, with a CR2 interval excluding zero.

**Qualifications that must travel with that sentence:**

- It rests on **73 of the original 133 pairs**. Design §5 stated in advance that the survivors are a
  **non-random subset** — events whose control was near-in-time or heavily contested are
  systematically removed — so the corrected estimate is not a clean unbiased re-estimate of the
  original quantity. This is a restriction, not a re-match.
- Sensitivity (a) shows the interval touching zero when reuse is retained. The conclusion is
  **not robust to the reuse correction alone.**
- **Pre-event drift imbalance is unresolved** and offers a live alternative explanation for part of
  the gap.
- Two tickers and 45% of pairs are gone; power is correspondingly reduced and the estimate is less
  precisely located than the interval alone suggests.

---

## 6. What this correction does **not** establish

- **It does not correct the manuscript's headline incremental null.** The `+0.0131 pp,
  p = 0.98332` figure is `strategy_E_incremental_high_gst`, a different outcome (strategy E net
  return) on the pooled 285 rows. The frozen design's estimand was `|day_return|` only. That
  statistic **remains `DO_NOT_CITE_PENDING_CORRECTION` and remains un-recomputed.**
- **It does not extend beyond the traced lineage.** Nothing here bears on the magnitude forecast,
  direction signal, restaurant pilot, nowcast, semiconductor work, or the attention–activity panel.
- **It confers no prospective status.** Not a HYP-01 confirmation. No PASS/WEAK/FAIL bucket is
  assigned, per frozen design §11.
- **It is not a trading result.** No strategy, return or tradability claim follows from it.

---

## 7. Citation status

| Result | Status |
|---|---|
| `Q1_abs_move_high_vs_control`, `t = 2.138` | **SUPERSEDED** by `CORRECTED_RESULTS_v1.0.json` → primary 2.0797 pp, t 3.260 |
| Corrected primary | Citable **only** with §5 qualifications and §6 scope limits |
| `strategy_E_incremental_high_gst` (+0.0131 pp, p = 0.98332) | **`DO_NOT_CITE_PENDING_CORRECTION`** — unchanged, not recomputed |
| All other AFFECTED entries in the overlay lineage | **`DO_NOT_CITE_PENDING_CORRECTION`** — unchanged |

**The original artifact was not modified.** `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` retains
hash `3d8fbb85…`, asserted by test. The SUPERSEDED relabel lives here and in the corrected artifact's
`citation_status` field, so prior citations of `t = 2.138` remain resolvable and the original numbers
stay visible rather than being overwritten.

No history was rewritten, nothing was force-pushed, and no commit was deleted.
