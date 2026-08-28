# Signal Without Strategy v1.1 — reviewer cover memo

**Date:** 2026-08-27 · **Status:** draft for co-author review. Not submitted.

---

## What the paper claims

**Search attention is associated with unusually active earnings events in retrospective matched
comparisons, but it does not provide reliable incremental forecasting or trading value.**

Every qualifier carries weight. *Retrospective*: nothing was preregistered. *Matched*: the comparison
is against comparable earnings events, not ordinary weeks. *Association*: every incremental test was
null.

## The five things a reviewer should check first

**1. Retrospective matched association — the one positive result.**
Corrected matched-pair analysis: **+2.0797 pp**, **p = 0.00397**, 73 pairs, CR2 clustered on ticker.
Stable across leave-one-ticker-out refits (**+1.8343 to +2.3772 pp**). This is a **Level-1
association only** — not prediction, not causation, not tradability. It was estimated on data already
observed.

A **separate** ticker-clustered regression over the full event population gives **+1.509 pp**,
**p = 0.0662**, 95% CI **[−0.113, +3.131]** — suggestive, spanning zero, not supported at 5%. These
are different specifications on different samples with different estimands, **not competing versions
of one number**.

**2. Null incremental prediction.**
Against a strong price-and-calendar baseline the marginal contribution of attention was **+0.0131
pp**, **p = 0.98332**. Out-of-sample magnitude error was **3.6299** with attention versus **3.6284**
without (paired **p = 0.9827**) — marginally *worse*. A logistic direction model was worse calibrated
than assuming the base rate (Brier **0.2711** vs **0.2560**; AUC **0.4654**, below chance).

**3. Null GST-specific tradability.**
A standalone event strategy returned a mean net **0.8543%** per event. **The same post-earnings drift
was present without the attention filter.** That return is a property of the earnings-event
population the filter selected into, not an attention result, and it must not be cited as one.

**4. A design-versus-result discrepancy we did not smooth over.**
The frozen corrective design specifies leave-one-ticker-out over **28** refits. The committed results
report **26** refits and 26 per-ticker entries. We report the realised **26** and flag the
difference. Nothing was recomputed to reconcile it.

**5. Imperfect match balance.**
Treated events carry mean |pre-drift| of **3.619 pp** against **2.9662 pp** for controls. Some of the
measured difference may reflect pre-event activity the match did not remove. Disclosed in §5.1 and
§11 as a limitation of the match, not a result.

## The prospective study

A separate preregistered protocol (internally "HYP-01") is designed to test whether the Level-1
association survives prospectively. **It has produced no results of any kind**: zero of the required
60 eligible events collected, no outcome analysed, and open methodological decisions in its own
governing record — including no registered smallest-effect-size-of-interest. It contributes **no
evidence** to this manuscript, and nothing here anticipates its outcome.

## What we did not do

No analysis was rerun. No specification was searched. No confidence interval was computed to fill a
gap — fields absent from the committed artifacts are marked "not in artifact" and left blank. No
external coefficient is used as an effect-size anchor; a bounded literature search closed on
2026-08-26 without finding a comparable published estimate.

## Verification available to a reviewer

Every numerical claim resolves to a committed artifact with an exact JSON pointer or CSV field,
full-precision source value, rounding rule, and status (`CURRENT` / `SENSITIVITY` / `SUPERSEDED` /
`HISTORICAL_CONTEXT`). The number-audit supplement in this package lists all 65. Two automated
checkers run against the manuscript: the original v1.0 checker (82 claims) and an extended v1.1
checker (154 claims, 213 distinct numeric tokens accounted for) that additionally refuses causal,
alpha and confirmatory language, refuses promotion of a secondary result over a designated primary,
and verifies that superseded and non-comparable historical results stay labelled as such.

## Package contents

| File | What it is |
|---|---|
| `Signal_Without_Strategy_v1.1_MANUSCRIPT.pdf` | The manuscript |
| `Signal_Without_Strategy_v1.1_FIGURES.pdf` | Figures 1–3 with captions |
| `Signal_Without_Strategy_v1.1_NUMBER_AUDIT.pdf` | 65 claims, each traced to source |
| `Signal_Without_Strategy_v1.1_FIGURE_TABLE_PLAN.pdf` | Display specification |
| `Signal_Without_Strategy_v1.1_COVER_MEMO.pdf` | This memo |
| `tables/*.csv` | Every manuscript table, cell text verbatim |

**No prospective panel data, no financial or search values, and no HYP-01 outcome are included in
this package.**
