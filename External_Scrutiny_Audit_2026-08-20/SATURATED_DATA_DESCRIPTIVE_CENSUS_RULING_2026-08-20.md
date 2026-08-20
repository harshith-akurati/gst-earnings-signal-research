# Compliance ruling: descriptive census on the saturated 152-event population

**Date:** 2026-08-20
**Question:** Does purely descriptive characterization of a subgroup inside the exhausted 152-event
historical population fall under the no-new-hypotheses-on-saturated-data rule?
**Ruling:** **PERMITTED, NARROWLY** — subject to the hard boundary in §3, which is binding.

---

## 1. What is being ruled on

A candidate observation: a subset of the 152 validated GST-spike events shows Wikipedia pageview
attention *below* its own trailing baseline at the same anchor week, despite the event qualifying on
a GST z-score ≥ 5. The proposal is to describe **who those events are** — ticker, sector, market cap,
date clustering, z-score magnitude — without touching any outcome.

---

## 2. Ruling and reasoning

The saturation rule exists to prevent significance-hunting on data that every prior hypothesis has
already touched. Its target is **inference against outcomes**, because that is the only thing that
can manufacture a false positive about market behaviour.

**Permitted, because:**

1. **No outcome variable is involved.** A census over ticker, sector, market cap, date and z-score
   magnitude cannot produce a claim about returns, volatility, option pricing or tradability. There
   is no test statistic to hunt.
2. **The subgroup is not discovered by searching.** The split `wiki_zscore < 0` is the natural
   baseline boundary, and the divergence counts are **already committed** in
   `Live Signal Engine/Wikipedia_Pageviews_IndependenceCheck_Note.md` (July 2026). Describing an
   already-recorded split is not a new search over the data.
3. **The legitimate use is design sizing.** Knowing how common each regime is, is a
   *power/feasibility* input for a forward pre-registration on data that does not yet exist. That is
   the same category as a power calculation, not the same category as a result.

**The objection is real and is handled by §3, not dismissed.** Examining subgroup structure can
absolutely seed post-hoc hypotheses, and "describing" drifts into "noticing patterns that become
claims" precisely at the boundary between composition and outcome. The mitigation is that the
boundary is written down here, before the census is produced, and is enforceable by inspection of
the census output.

---

## 3. The boundary (binding)

### PERMITTED on the 152-event population

- Counts and proportions of the divergent and concordant sets.
- Composition: ticker, sector, market capitalisation, event date, year.
- Temporal clustering of event dates.
- Distribution of `gst_zscore` and `wiki_zscore` **as inputs** — these are selection and attention
  variables, not outcomes.
- Plain statements of the form "regime X occurs in N of 152 events."

### PROHIBITED on the 152-event population — absolutely

- **ANY comparison of the divergent group's market outcomes against the concordant group's.**
  Returns, abnormal returns, realized volatility, win rate, PnL, straddle cost, option pricing,
  implied move, drift, or any function of a price. **That comparison would be hypothesis #15 on dead
  data and it is not authorised now or later.**
- Any p-value, confidence interval, hypothesis test or model fit **of any kind**, including on
  composition. A census reports counts, not inference.
- Re-thresholding: trying `wiki_zscore < -0.5`, `< -1`, or any alternative cut to obtain a more
  interesting split. The threshold is `< 0` because that is the committed baseline definition, and it
  is fixed.
- Ranking, scoring, or aggregating the census into an index.
- Citing the census as evidence **for or against** any market-behaviour claim. Its only permitted
  downstream use is sizing a forward pre-registration.

### Required labelling

Any census output must state on its face that it is a census and not an analysis, and must state
that outcome comparisons are prohibited pending a forward-data pre-registration.

---

## 4. What this ruling does not do

- It does not authorise any test of the Wikipedia-divergence question on historical data, in any
  form, at any future date.
- It does not modify the saturation rule, any frozen design, any locked pre-registration, or
  `FROZEN_DESIGN_v1.0.md`.
- It does not create a hypothesis. The forward version of this question requires its own
  pre-registration, on data that does not exist at the time that pre-registration is frozen.

---

## 5. Audit note — consistency with prior rulings this session

This ruling continues the convention applied earlier on 2026-08-20:

- **n = 40 rejected as a verdict gate.** A proposal to pre-register `n >= 40` was declined as the
  binding threshold because `FROZEN_DESIGN_v1.0.md` §7 already pre-commits **75** eligible events;
  40 was recorded instead as an explicitly descriptive-only interim checkpoint at which no gate may
  be evaluated. A pre-committed minimum is not lowered after learning that accumulation is slow.
- **Open universe rejected.** A proposal to define the prospective universe as "any US-listed ticker
  with a confirmed earnings date and listed options" was declined under `FROZEN_DESIGN_v1.0.md` §2,
  which prohibits any generated ticker list. The universe was instead constituted from dated,
  hash-recorded official index constituent snapshots.

The common principle in all three: **a rule may be added, and a study may be widened prospectively,
but an in-force commitment is never relaxed after seeing what it costs.** The present ruling permits
a census precisely because it adds nothing to, and relaxes nothing in, the outcome-facing rules.
