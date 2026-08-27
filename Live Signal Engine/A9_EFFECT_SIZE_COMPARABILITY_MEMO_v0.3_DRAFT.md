# A9 Effect-Size Comparability Memo — v0.3 DRAFT

**Date drafted:** 2026-08-26 · **Status:** DRAFT, **uncommitted**, for co-author review.
**Type:** **FEASIBILITY ASSESSMENT ONLY.** No power calculation is performed, licensed, or implied by
this memo. No SESOI is proposed.

## 1. Verdict

> **`A9_BLOCKED_MISSING_REGISTERED_SESOI`**

A9 (design sensitivity / power) **cannot proceed**. The blocking condition is not difficulty or
missing tooling — it is that the quantity A9 would be computed *about* does not exist.

## 2. Why A9 is blocked

**Observed.** An exhaustive search of every committed HYP-01, registry, gap-audit and preregistration
artifact located **no registered SESOI** — no smallest effect size of interest, in any units, with any
registration date, in any dated artifact. The only adjacent text is a *request* in a draft review
packet (`GST_HYP01_STATISTICAL_METHOD_REVIEW_PACKET_v1.0_DRAFT.md` §11, line 211) that someone
*should* report a minimum-detectable-effect curve. A request is not a registration.

**Observed.** `GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` §6 states affirmatively:
"**60 / 60 / 40 are governance eligibility floors, not power calculations.** … They are not claims of
statistical power, not minimum detectable effect sizes, and not guarantees that a result at that n
will be meaningful." The locked `n = 60` therefore cannot be reverse-engineered into an implied SESOI.

**Observed.** `GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json`
`/statistical_governance/power_statement`: "No power calculation was performed, and none may be
performed using observed project results."

**Observed.** `PREREGISTRATION_GAP_AUDIT_v1.0.md` line 51 carries A9 as **UNRESOLVED**,
`SCIENTIFIC_DECISION`, deadline `BEFORE_FIRST_OBSERVATION`, with the note "no power or
design-sensitivity analysis exists".

**Per the co-author's standing instruction, this memo does not propose a numerical SESOI.** Selecting
one is a scientific decision requiring a dated lock authored by a qualified human before any eligible
outcome exists.

## 3. Rules that bind any future A9 pass

Carried forward verbatim in substance from `PREREGISTRATION_GAP_AUDIT_v1.0.md` line 53 and
`GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` `/effective_decisions/D16`:

1. A9 **must** occur before prospective outcomes exist.
2. A9 **must** use externally justified or clearly hypothetical effect sizes.
3. A9 **must never** use observed prospective project results. `D16 = NO_PROJECT_DERIVED_POWER_CLAIM`.
4. A9 **must not** silently change the locked `n = 60` threshold; a revision requires a new dated lock
   written before any outcome is seen.

### 3.1 Permitted and prohibited effect-size sources

| Source | Status |
|---|---|
| A **registered SESOI**, once one exists in a dated artifact | **PRIMARY — required.** A9 uses it as the primary effect or A9 does not run |
| Cohen-style conventional values (small / medium / large) | **PERMITTED ONLY as an explicitly hypothetical grid**, labelled as convention rather than evidence, never as "the" effect size, and never presented as a project expectation |
| Any project-derived effect size — pilot, retrospective, exploratory, panel-derived, or from any observed prospective result | **PROHIBITED** |
| Drake, Roulstone & Thornock (2012) coefficients — **verified**: Table 8, model (6), DV `AR[0, +1]`, `UE × AbSearch[FQE, −1]` = −3.289\* (2.223) / −2.477\*\*\* (1.043); `UE × AbSearch[−5, −1]` = −3.818\*\*\* (1.364) / −2.863\*\*\* (0.809); N = 4,133; S&P 500 2005–2008; one-tailed where a direction is predicted | **PROHIBITED as a direct anchor** unless a fully justified conversion satisfies **every** inclusion criterion. Verification did not change this: it fails criteria 1, 3, 4 and 5. The estimand is an interaction conditional on `UE` on a **signed** return — HYP-01 has neither the `UE` conditioning nor a signed outcome |
| Da, Engelberg & Gao (2011) coefficients | **PROHIBITED as a direct anchor**, same condition. Currently fails criteria 2, 3, 4, 5 |
| Ahluwalia (2026) coefficients | **PROHIBITED as a direct anchor**, same condition. Currently fails criterion 3; criteria 4 and 5 are `NOT_EVALUATED_AFTER_CRITERION_3_FAILURE` and must not be described as failures |

## 4. External anchor availability

One bounded search was conducted on 2026-08-26 and **closed**; see
`HYP01_A9_LITERATURE_SEARCH_LOG_2026-08-26.md`.

> **No compatible external effect-size anchor identified as of 2026-08-26 under the prespecified
> comparability criteria.**

The binding obstacle is structural rather than bibliographic. HYP-01's locked outcome
`abs_overnight_gap` is an **absolute** movement magnitude. The located literature estimates **signed**
quantities — response coefficients, drift, buying pressure, subsequent return and reversal. Converting
a signed-response coefficient into an absolute-magnitude coefficient is not a units change; it
requires assumptions about the conditional distribution of the signed quantity, and those assumptions
would themselves determine the answer.

## 5. Three transports, which must not be conflated

This section exists because the project's inference constraints are frequently — and incorrectly —
described as though they prevented borrowing an effect magnitude. They do not.

**5.1 Transporting an underlying effect magnitude.** Whether a coefficient estimated elsewhere is a
reasonable stand-in for the coefficient here. This is limited by **construct and estimand
comparability**: predictor construction, outcome definition, population, period, and functional form.
It is *not* limited by this project's clustering choice or its sidedness. **Clustering and sidedness
are not independently fatal to transferring an underlying coefficient.**

**5.2 Transporting its standard error or precision.** Whether an external standard error says anything
about the uncertainty attaching to `beta_gst` here. It does not. Precision depends on this design's
own cluster structure, cluster count, balance, and effective degrees of freedom. **Clustering is a
direct barrier here.**

**5.3 Transporting statistical power.** Whether an external power figure describes this design's
ability to detect an effect. It does not, for the same reasons as 5.2, plus α and sidedness. **Both
clustering and sidedness are direct barriers here.**

**The correct statement.** An external paper may in principle supply a candidate *magnitude* (5.1),
subject to construct comparability. It may **never** supply the *uncertainty* or the *power* (5.2,
5.3) — those must be computed from this design's own realised cluster structure. Nothing found in the
2026-08-26 search clears even 5.1.

## 6. Size-adjustment requirement

**This requirement stands on its own and does not depend on any project simulation.** It follows from
the general fact that when a test's empirical size exceeds its nominal size, power computed against
the nominal reference distribution overstates true power.

**Normative rule.** Any future A9 output **must** either:

- **(a)** report **size-adjusted power**, computed against the test's empirical size at the realised
  cluster count and balance, using a reproducible in-repository simulation; **or**
- **(b)** carry an **explicit upper-bound label** stating the nominal reference distribution used and
  stating that the figure is an **upper bound on true power**, not an estimate of it.

An unlabelled nominal-reference power number is not acceptable output. **No empirical-size value is
adopted here**, because no reproducible one exists (see §6.1). Which of (a) or (b) applies, and any
numbers entering either, must come from evidence produced after the gap in §6.1 is closed.

### 6.1 `SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP` — historical discrepancy note

**Status: `SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP`. The figures in this subsection are recorded for
historical continuity only. They are NOT used to support any normative claim in this memo, and they
must not be cited as the project's empirical size, quoted in a preregistration, or used to justify a
threshold, a method choice, or a power calculation.**

`GST_HYP01_STATISTICAL_METHOD_REVIEW_PACKET_v1.0_DRAFT.md` §5.1 reports a synthetic demonstration with
these characteristics, quoted from the packet:

- run **outside the repository**, on pseudo-random data with a fixed seed;
- matching only the *shape* of the design — n = 60, G ∈ {10, 16, 24}, one continuous regressor, a
  cluster random effect;
- under a **true null**, so it measures **size, not power**;
- **"The script was deleted after use."**

The figures as recorded in that packet:

| Clusters | Cluster sizes | CV0 + normal | CV1 + t(G−1) | CV2 + t(G−1) | CV2 + Satterthwaite | mean ν | ν 5th pct | mean G* |
|---|---|---|---|---|---|---|---|---|
| 10 | balanced | 0.128 | 0.069 | 0.056 | 0.043 | 5.8 | 4.0 | 6.8 |
| 10 | unbalanced | 0.208 | 0.135 | 0.102 | 0.057 | 4.2 | 1.9 | 5.0 |
| 16 | balanced | 0.114 | 0.079 | 0.065 | 0.049 | 8.5 | 5.7 | 9.6 |
| 16 | unbalanced | 0.186 | 0.140 | 0.100 | 0.052 | 5.5 | 2.6 | 6.4 |
| 24 | balanced | 0.101 | 0.077 | 0.072 | 0.057 | 11.4 | 7.6 | 12.5 |
| 24 | unbalanced | 0.154 | 0.127 | 0.094 | 0.054 | 7.3 | 3.7 | 8.2 |

**Why these numbers cannot carry normative weight.**

1. **Not reproducible.** The generating script was deleted and never existed in the repository. No
   commit, seed record, or environment manifest allows regeneration. The numbers cannot be checked,
   re-derived, or audited.
2. **Not a power study.** Run under a true null. It speaks to size only.
3. **Not the project's design.** It matched the *shape* only — no ticker, no `gst_zscore`, no
   `abs_overnight_gap`, nothing calibrated to the project.
4. **Incomplete method coverage.** It tested CV0 + normal, CV1 + t(G−1), CV2 + t(G−1), and
   CV2 + Satterthwaite. It did **not** test the wild cluster bootstrap and did **not** test CR3.
5. **Cluster grid may not match realisation.** G ∈ {10, 16, 24}; HYP-01's realised cluster count is
   bounded above by 24 and may be lower.

**No simulation was rerun for this memo, and none may be run on prospective project data.**

**Closing this gap** requires a reproducible in-repository size study — committed script, recorded
seed, pinned environment, at the realised cluster count and balance — before any size-adjusted power
figure may be reported under §6(a). Until then only §6(b), the explicit upper-bound label, is
available, and it must be stated qualitatively rather than with a numeric size correction drawn from
the table above.

## 7. Inference status carried forward

| Item | Status | Source |
|---|---|---|
| Primary covariance estimator | **CR2 (bias-reduced linearisation)**, `vcovCR(fit, cluster = <ticker factor>, type = "CR2")` | effective lock `/effective_decisions/D1`, `/authoritative_calculation/covariance_call` |
| Finite-sample correction | **BRL built into clubSandwich CR2** | `/effective_decisions/D2` |
| Reference distribution | **Coefficient-specific Satterthwaite**, `coef_test(fit, vcov = <CR2>, test = "Satterthwaite")` | `/effective_decisions/D3`, `/authoritative_calculation/inference_call` |
| CR1 | Reported reference number only, not the inferential rule | review packet §4 "Suitability here" |
| Wild cluster bootstrap | **Plays no role in HYP-01**; independently unvalidated; `fwildclusterboot` deliberately not installed | amendment `/decisions/D4` note; decision matrix line 37 |
| CR3 | Not validated by PR #18 | decision matrix line 37 |
| Cluster-count / effective-df threshold | **No threshold set.** `PLACEHOLDER_PENDING_METHODOLOGIST`; any future threshold requires a new dated amendment authored without outcome inspection | decision matrix D10; amendment `/decisions/D10/future_threshold_rule` |
| **C6 — estimator variant** | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** | gap audit line 75; `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` |
| **C7 — finite-sample correction and inference procedure** | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** | gap audit line 76; `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` |

**C6/C7 are not treated as closed.** The 2026-08-16 amendment settles their subject matter
(`SUBSTANTIVELY_RESOLVED`) but never names them by identifier, and the gap audit has not been
re-issued, so the register entries stay open (`ADMINISTRATIVELY_OPEN`). This memo settles nothing.
See `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` for the chronology, the exact JSON pointers, and the closure
action a co-author would need to take.

## 8. Prerequisites for unblocking A9

In order. Each is a human authoring action; none is performed here.

1. A **dated SESOI registration** in an artifact written before any eligible HYP-01 outcome exists,
   stating value, units, interpretation, and derivation.
2. A **dated closure of C6 and C7** by identifier — a gap-audit v1.1 or signed erratum naming them
   and pointing at the 2026-08-16 decisions — so the inference procedure the power calculation
   assumes is formally the registered one. A draft is prepared at
   `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md`; it is unsigned and makes no inference decision.
3. A decision on whether A9 runs on the registered SESOI alone or additionally on an explicitly
   hypothetical Cohen-style grid.
4. A **reproducible in-repository size study** at the realised cluster count and balance, if
   size-adjusted power is to be reported rather than an upper bound. The §6.1 figures cannot serve:
   they carry `SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP` and are historical record only. A prospective
   protocol for that study is drafted at
   `HYP01_INFERENCE_SIZE_SIMULATION_PROTOCOL_v0.1_DRAFT.md`; it is **unapproved and unexecuted**, and
   it produces no empirical results.

Until item 1 exists, A9 remains **`A9_BLOCKED_MISSING_REGISTERED_SESOI`**.
