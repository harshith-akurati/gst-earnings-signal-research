# HYP-01 SESOI decision packet — v0.1 DRAFT

**Status:** DRAFT, **decision support only**. Prepared **2026-08-26** (host clock 21:48
America/Chicago); filed under the co-author's 2026-08-27 review-cycle label.

> **This document contains no numerical SESOI, and none is proposed, recommended, implied, or
> inferred anywhere in it.** Selecting the value is a scientific decision reserved to the human
> co-authors. This packet exists to make that decision well-posed, not to pre-empt it. Every numeric
> field below is deliberately blank.

---

## 1. Why a SESOI is required

**A9 (design sensitivity / power) is blocked without one.** Power is not a property of a design alone
— it is the probability of detecting *an effect of a stated size*. With no stated size there is no
quantity to compute, which is why the status is `A9_BLOCKED_MISSING_REGISTERED_SESOI` rather than
"A9 not yet run".

Three committed constraints make this binding rather than a matter of taste:

1. `PREREGISTRATION_GAP_AUDIT_v1.0.md` line 53 — A9 "**must** use externally justified or clearly
   hypothetical effect sizes" and "**must never** use observed prospective project results".
2. `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` `/effective_decisions/D16` =
   `NO_PROJECT_DERIVED_POWER_CLAIM`.
3. `GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` §6 — the locked `n = 60` is a governance eligibility
   floor and is expressly "**not** … [a] minimum detectable effect size", so it cannot be inverted into
   an implied SESOI.

A registered SESOI is additionally the precondition for any **equivalence** claim (§4), because an
equivalence bound *is* a SESOI expressed as an interval.

## 2. The coefficient's exact units

The locked primary model, from `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json`
`/unamended_base_lock_invariants`:

```
abs_overnight_gap ~ gst_zscore        ordinary least squares
coefficient of interest : gst_zscore   (beta_gst)
null hypothesis         : beta_gst = 0
alpha                   : 0.05
sidedness               : two_sided
cluster variable        : ticker
```

**`beta_gst` is therefore in units of `abs_overnight_gap` per one unit of `gst_zscore`.**

- The predictor `gst_zscore` is a **z-score**, so one unit is **one standard deviation** of the
  project's own attention construction, on that construction's own baseline.
- The outcome `abs_overnight_gap` is an **absolute** overnight movement magnitude and is
  **non-negative by construction**. **This says nothing about the sign of `beta_gst`.** A regression
  coefficient on a non-negative outcome can be positive or negative: higher attention may be
  associated with larger *or* smaller absolute movement. The coefficient's range is not bounded by
  the outcome's range.
- `beta_gst` consequently reads as: *the change in expected absolute overnight movement associated
  with a one-standard-deviation increase in pre-announcement attention.*

**Two consequences the co-authors must decide on explicitly.**

- A SESOI must be stated **in these units**, or with an explicit, documented conversion into them. A
  value borrowed from a signed-return study is not in these units.
- **Whether the bound is symmetric is a substantive judgement, not a consequence of the outcome's
  non-negativity.** An earlier draft implied the latter; that inference was wrong and is corrected
  here. The real question is whether a positive association of size Δ and a negative association of
  size Δ are **equally meaningful to this project**. If they are, a symmetric `±Δ` is right. If, say,
  an amplification of size Δ would change conclusions but a dampening of the same size would not,
  an asymmetric bound is right — and that asymmetry must be argued substantively, not derived from
  the outcome's scale. See §7.

## 3. What a SESOI is, and is not

**It is** the smallest value of `beta_gst` that the co-authors would regard as *substantively*
meaningful — the boundary below which an effect, even if statistically detectable, would not change
what anyone concludes or does.

**It is not**: a guess at the true effect; a value chosen to make the design look adequately powered;
a threshold derived from what the data are likely to show; or a restatement of `n = 60`.

## 4. What equivalence would mean

An equivalence test (e.g. TOST) against bounds `[−Δ, +Δ]` asks whether the effect is *small enough to
be uninteresting*, rather than whether it is distinguishable from zero.

**A successful symmetric equivalence result would license this claim:** *at the registered procedure
and alpha, the data are inconsistent with effects at or beyond **both** −Δ and +Δ* — i.e. the
association is smaller in magnitude than the threshold the co-authors declared to matter, **in either
direction**.

It does **not** constrain amplification only. An earlier draft said it did; that was wrong. A
symmetric equivalence test rules out a dampening association of size Δ exactly as much as an
amplifying one. If an asymmetric bound is registered instead, the licensed claim narrows to whatever
that bound actually excludes, and must be stated in those terms.

## 5. What equivalence would NOT prove

Recorded because these are the standard misreadings:

- **Not** that `beta_gst = 0`. Equivalence bounds an effect; it does not establish a null.
- **Not** that attention is unrelated to announcement movement — only that any relationship is smaller
  than Δ *on this outcome, in these units, in this population*.
- **Not** that Drake's preemption mechanism is absent. That is a different estimand on a signed
  outcome conditional on unexpected earnings; HYP-01's marginal absolute-gap coefficient cannot
  identify it in either direction.
- **Not** a result transportable to other universes, periods, or attention constructions.
- **Not** a licence to report anything before the freeze and display gates open.

## 6. Why project-observed effects cannot be used

Prohibited by `D16 = NO_PROJECT_DERIVED_POWER_CLAIM` and by the gap audit's A9 constraints, and
independently unsound: choosing a SESOI from observed data makes the subsequent test circular — the
threshold would be set by the very quantity it is meant to judge. This covers **all** project-derived
sources: the prospective panel, retrospective analyses, exploratory work, pilots, and any earlier
in-project estimate.

It also covers **timing**: the SESOI must be registered **before any eligible HYP-01 outcome is
observed or analysed**. As of 2026-08-26 the eligible count is **0** and
`/effective_state/analysis_run` is `false`, so this window is currently open. It closes at the first
eligible outcome.

## 7. Acceptable non-outcome bases for a human decision

Offered as *categories a co-author may reason within*, with no value attached to any of them and no
recommendation among them.

| Basis | What it would require | Status |
|---|---|---|
| **A. Substantive/economic materiality** | A stated threshold of absolute overnight movement that would matter for the project's purpose, converted into `gst_zscore` units with documented assumptions | Available; requires an explicit judgement |
| **B. Measurement resolution** *(feasibility input, not a basis on its own)* | The smallest effect distinguishable given the construction's own precision | Available, but **cannot alone define a SESOI**. Resolution answers "what could be detected", not "what would matter" — a detectable effect can be substantively trivial and an important effect can be below resolution. It may **inform** a value chosen on basis A, or flag that a substantively chosen Δ is unmeasurable, but a SESOI resting on resolution alone has no substantive justification and is not valid |
| **C. Explicitly hypothetical Cohen-style grid** | A conventional small/medium/large grid, **labelled as convention, not evidence**, used only to show sensitivity across a range | **Permitted only as a hypothetical grid**, never as *the* SESOI, and never presented as a project expectation |
| **D. External literature anchor** | A published estimate satisfying every comparability criterion in the search log | **Currently unavailable** — the 2026-08-26 bounded search found none; Drake, Da–Engelberg–Gao and Ahluwalia are all excluded and **prohibited as direct anchors** |
| **E. Any project-derived value** | — | **PROHIBITED** (§6) |

**Basis D is closed as of 2026-08-26** and may only reopen through a new bounded search with its own
log, which would still have to clear the absolute-vs-signed outcome criterion.

## 8. Required fields for registration

A SESOI registration is valid only if **every** field is completed, in a dated artifact written before
any eligible outcome exists. Left blank deliberately.

| # | Field | Value |
|---|---|---|
| 1 | **Numerical value** | `________` *(to be supplied by co-authors — not proposed here)* |
| 2 | **Units** | `________` *(must resolve to `abs_overnight_gap` per 1 SD of `gst_zscore`, or state the documented conversion)* |
| 3 | **Symmetry or asymmetry** | `________` *(symmetric `±Δ`, or asymmetric — note the outcome is bounded below at zero)* |
| 4 | **Substantive interpretation** | `________` *(what makes this the smallest effect that would matter)* |
| 5 | **Derivation** | `________` *(which basis from §7; the reasoning; explicit statement that no project outcome was used)* |
| 6 | **Approval date** | `________` *(must precede the first eligible HYP-01 outcome)* |
| 7 | **Approving co-authors** | `________` *(named individuals, not a role)* |
| 8 | **Relationship to equivalence testing** | `________` *(does Δ define an equivalence bound? if so, which procedure, and is it registered as primary, secondary, or not at all?)* |

> **Registering an equivalence test is a NEW analysis-design decision requiring its own dated
> authorization.** Selecting Δ does **not** silently add TOST — or any equivalence procedure — to the
> locked model. The locked primary analysis is a two-sided test of `beta_gst = 0` at α = 0.05, and it
> stays that way unless a separate dated instrument, written before any eligible outcome exists, adds
> an equivalence procedure and states its role (primary, secondary, or sensitivity), its bounds, its
> alpha, and its multiplicity treatment. A SESOI registered for A9 design-sensitivity purposes and an
> equivalence bound registered for inference are two decisions, and either may be taken without the
> other.

## 9. Co-author decision table

To be completed by the humans. **No cell is pre-filled.**

| # | Decision | Co-author 1 | Co-author 2 | Agreed value / status | Date |
|---|---|---|---|---|---|
| S1 | Is a SESOI to be registered at all? | | | | |
| S2 | Which basis from §7 is used? | | | | |
| S3 | Numerical value | | | | |
| S4 | Units (and conversion, if any) | | | | |
| S5 | Symmetric or asymmetric bound? | | | | |
| S6 | Substantive interpretation | | | | |
| S7 | Derivation statement | | | | |
| S8 | Is an equivalence procedure registered? | | | | |
| S9 | If yes — procedure, bounds, alpha, primary/secondary | | | | |
| S10 | Confirm no project outcome informed S3–S7 | | | | |
| S11 | Approval date and named approvers | | | | |

## 10. Gate

> **A9 cannot run until this record is completed and approved.** Until fields 1–8 of §8 are filled in
> a dated artifact and the §9 table is signed, the governing status remains
> **`A9_BLOCKED_MISSING_REGISTERED_SESOI`**.

Completing this packet is **necessary but not sufficient**: the A9 memo's §8 also requires the C6/C7
administrative closure and, for size-adjusted power rather than an upper bound, a reproducible
in-repository size study under
`HYP01_INFERENCE_SIZE_SIMULATION_PROTOCOL_v0.1_DRAFT.md` — itself unapproved and unexecuted.
