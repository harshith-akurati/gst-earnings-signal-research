# HYP-01 inference-size simulation protocol — v0.1 DRAFT

**Status:** DRAFT, **UNAPPROVED AND UNEXECUTED**. Prepared **2026-08-26** (host clock 21:48
America/Chicago); filed under the co-author's 2026-08-27 review-cycle label.

> **No simulation has been run under this protocol, and none may be run until the approval gate in
> §16 is signed.** This document contains **no empirical results**. Every table below is a *schema*
> for results that do not yet exist.

---

## 1. Purpose

To estimate, by synthetic simulation under a **true null**, the **rejection rate of the locked
HYP-01 inference procedure under specifically declared synthetic data-generating processes**, across
the cluster counts and balance patterns the realised design may present.

**What this study is not.** It is **not** a measurement of "the project's empirical size" — no such
quantity is established by a synthetic DGP, and no figure produced here may be described that way.
Every number it yields is a *rejection rate under a named synthetic DGP*, and its transportability to
the realised design is exactly as good as the DGP's realism, which is an assumption and not a result.

**It does not by itself produce size-adjusted power.** Per
`A9_EFFECT_SIZE_COMPARABILITY_MEMO_v0.3_DRAFT.md` §6, size-adjusted power additionally requires a
registered SESOI or labelled hypothetical alternative, a predeclared calibration rule deriving a 5%
cutoff from these null results, **separate alternative-DGP simulations** run at that cutoff, matched
scenarios, and Monte Carlo uncertainty on the power estimate itself. This protocol covers the **null
half only** — one input among five. Alternative-DGP runs are **out of scope** and would need their
own protocol and their own authorization.

**This protocol does not perform A9 and does not require a SESOI.** Size is a property of the test
under the null; it is independent of any effect size. A9 remains separately blocked
(`A9_BLOCKED_MISSING_REGISTERED_SESOI`).

## 2. The historical evidence this replaces

> **`SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP`**

`GST_HYP01_STATISTICAL_METHOD_REVIEW_PACKET_v1.0_DRAFT.md` §5.1 reports rejection rates from an
earlier synthetic demonstration. **Those figures are not reproducible evidence and this protocol does
not build on them.** Per the packet's own description, that run was performed **outside the
repository**, and **"The script was deleted after use."** There is no committed script, no recorded
seed, no environment manifest, and no way to regenerate, audit, or check the numbers. It also tested a
narrower method set and was a size study only.

Accordingly:

- the historical rejection rates are **not** used as inputs, priors, calibration targets, or expected
  values anywhere in this protocol;
- results produced under this protocol **supersede** them for every purpose;
- any discrepancy between the two is to be **reported as a discrepancy**, not reconciled in favour of
  either. The historical numbers carry no evidentiary weight against which a new result could be
  judged wrong.

## 3. Locked model and inference procedure under test

Read from `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json`. **This protocol tests the locked procedure; it
does not propose changing it.**

```
model      : abs_overnight_gap ~ gst_zscore        (OLS)
cluster    : ticker
covariance : CR2 bias-reduced linearisation   [D1]
correction : BRL, built into clubSandwich CR2  [D2]
reference  : coefficient-specific Satterthwaite [D3]
alpha      : 0.05
sidedness  : two_sided
calls      : vcovCR(fit, cluster = <ticker factor>, type = "CR2")
             coef_test(fit, vcov = <CR2>, test = "Satterthwaite")
```

Wild cluster bootstrap has **no registered HYP-01 role** (`D4 = NOT_USED_IN_HYP01`); it appears below
only as a non-binding comparator, and no result concerning it may be used to alter the locked
procedure.

## 4. Synthetic-only data restriction

**Absolute.** The simulation uses **pseudo-random synthetic data only**.

- **No** project data of any kind: no ticker identity, no `gst_zscore` value, no `abs_overnight_gap`
  value, no panel row, no prospective observation, no retrospective dataset.
- **No** calibration of any DGP parameter to observed project data. Parameters are declared in §7
  before execution and are not tuned to resemble project data.
- **No** eligible HYP-01 outcome is read, at any stage, by anyone running this protocol.
- The only project-derived inputs are **design facts from committed artifacts** — the cluster ceiling
  of 24 and the event gate of 60 — which are governance constants, not observations.

## 5. No project outcomes

Restated as a standalone requirement because it is the one that would invalidate everything:
**running this protocol must not involve inspecting, loading, querying, or deriving any prospective
project outcome.** A run that touches outcome data is void and its results must be discarded, not
corrected.

## 6. Cluster-count scenarios, derived from committed artifacts

Justification for each, from artifacts rather than from convenience:

| Scenario | G (clusters) | n (observations) | Derivation |
|---|---|---|---|
| **S1 — ceiling** | 24 | 60 | `GST_HYP01_METHOD_REVIEW_REQUEST_v1.0_DRAFT.md` line 27: "At most 24 clusters, because a cluster is a ticker and the universe is locked at 24" |
| **S2 — partial participation** | 18 | 60 | Same source: "Fewer if some tickers contribute no eligible event" |
| **S3 — moderate participation** | 12 | 60 | As S2, a lower realisation of the same mechanism |
| **S4 — sparse participation** | 8 | 60 | As S2; also probes the small-G regime the gap audit calls "real at ~24 clusters" |
| **S5 — floor probe** | 4 | 60 | Stress scenario. Above the refusal floor `min_clusters_for_any_output = 2` in the effective lock's `/refusal_thresholds` |

`n = 60` is fixed across scenarios by the locked `freeze_and_display.threshold`. **No scenario may be
added, dropped, or reweighted after results are seen** (§13).

## 7. Balance scenarios and data-generating process

### 7.1 Balance

Each cluster-count scenario is run under **two** cluster-size patterns:

- **Balanced** — cluster sizes as equal as `n = 60` permits.
- **Unbalanced** — a skew that must be written out **as an explicit integer allocation for every G**
  before approval.

> **LOOPHOLE CLOSED.** An earlier draft said the allocation "must be fixed in the script before
> execution". That let the *script* decide the study after the *protocol* was approved. **The exact
> allocation vectors for every G, balanced and unbalanced, must appear in this document and be
> approved as written** (see §16.1). "Declared in the script" is no longer sufficient anywhere in
> this protocol.

The gap audit notes the cohort is expected to be unbalanced, so that arm is of primary interest.

### 7.2 DGP assumptions — declared in advance

| Component | What must be fixed **in this document** before approval |
|---|---|
| Regressor construction | Exact distribution and whether the regressor is i.i.d. across observations or **clustered** (correlated within cluster). These behave differently under CR2, so the choice is substantive, not cosmetic |
| Clustered-regressor / high-leverage stress arm | Explicit **yes or no**, and if yes, the exact construction. Small-G CR2 behaviour is sensitive to leverage, so omitting this arm is a decision that must be taken deliberately rather than by silence |
| True coefficient | **β = 0 exactly** — true-null study |
| Cluster-intercept variance | Exact numeric value |
| Idiosyncratic-error variance | Exact numeric value |
| Heteroskedasticity rule (E2) | The exact generating rule mapping cluster index to error variance |
| Heavy-tail family and df (E3) | Named distribution **and** its degrees-of-freedom parameter |
| Outcome construction / transformation | Exact statement of whether the simulated outcome is left on the raw scale or transformed to respect the non-negativity of `abs_overnight_gap`, with the transformation written out if used |

> **Every cell above is currently UNSPECIFIED and must be filled in before §16 can be signed.** None
> of them may be deferred to the script. A protocol whose parameters are chosen after approval is not
> a preregistration.

### 7.3 Error structures

Declared in advance, each a separate labelled arm; results reported per arm, never pooled:

- **E1 — homoskedastic** normal errors (baseline). Variance to be specified per §7.2.
- **E2 — cluster-heteroskedastic**: error variance varying by cluster, by the **exact rule** required
  in §7.2 — not "some skew".
- **E3 — heavy-tailed**: a **named** family with a **stated df**, per §7.2, to probe robustness of
  the Satterthwaite approximation.

## 8. Replications and justification

**R = 10,000 replications per cell** (scenario × balance × error structure).

Justification, stated as Monte Carlo precision rather than convention: for a true rejection rate near
α = 0.05, the Monte Carlo standard error is `sqrt(0.05 × 0.95 / R)`. At R = 10,000 that is ≈ 0.00218,
giving a 95% Monte Carlo interval of roughly ±0.0043 — narrow enough to distinguish a materially
inflated size (say 0.07) from nominal, which is the decision this study must support. R may be
**increased** by amendment before execution; it may **not** be reduced, and it may **not** be changed
after any result is seen.

## 9. Deterministic seeds

- A single **master seed**, an exact integer, fixed **in this document** before approval.
- A **named RNG algorithm** (e.g. PCG64), fixed in this document — not left to a library default,
  which can change between versions.
- A **deterministic seed-derivation rule** from `(master_seed, scenario, balance, error_structure,
  replication_index)`, written out explicitly enough that a third party can regenerate the seed of any
  single replication from the document alone.

> **SCHEMA CONSISTENCY.** The seed tuple includes `replication_index`, so seeds exist **per
> replication**, but the §15.1 output schema is one row **per cell**. A per-cell row cannot carry a
> per-replication seed. The protocol therefore requires **one** of the following, chosen before
> approval:
>
> - **(i)** record the derivation rule in full at cell level, sufficient to regenerate every
>   replication seed deterministically — the rule, not the seeds; **or**
> - **(ii)** emit a separate **replication-level seed record** alongside the cell-level results.
>
> Recording a single `cell_seed` while seeding per replication is internally inconsistent and would
> not permit regeneration. That inconsistency existed in the previous draft and is corrected here.

- **Seeds are fixed before execution and never re-drawn.** A re-run with a new seed is a *new study*
  requiring its own record, not a replacement of the first.

## 10. Methods compared

| Label | Method | Role |
|---|---|---|
| **M1** | CR2 + coefficient-specific Satterthwaite | **The locked procedure — the object of the study** |
| M2 | CR2 + t(G−1) | Comparator: isolates the reference-distribution choice |
| M3 | CR1 + t(G−1) | Comparator: the "reported reference number" method |
| M4 | CV0 + normal | Comparator: an uncorrected **benchmark**. Expected to reject most often, but **no ordering among methods is guaranteed** — M4 is not a floor, a bound, or a guaranteed worst case, and any such claim must be read off the results rather than assumed |
| M5 | Wild cluster bootstrap | **Non-binding.** Inclusion or exclusion must be decided **explicitly before approval** (§16.1) rather than left to whether a package happens to be installed. Currently `fwildclusterboot` is deliberately not installed, and D4 gives the bootstrap no HYP-01 role |

**No comparator result may be used to change the locked procedure.** Changing it requires a new dated
amendment authored without outcome inspection, per `D10/future_threshold_rule`.

## 11. Estimands

Per cell, for each method:

- **Empirical rejection rate** at nominal two-sided α = 0.05 under the true null — i.e. **empirical
  size**.
- Secondary, descriptive: realised Satterthwaite ν (mean, SD, 5th percentile) and effective cluster
  count G\* where the method defines them.
- **Size distortion** = empirical size − 0.05.

**No power estimand is defined**, because β = 0 throughout. Power requires a SESOI, which does not
exist.

## 12. Monte Carlo uncertainty

Every reported rate must carry a **95% Monte Carlo interval**. The interval method — Wilson or
Clopper–Pearson — must be **named in this document before approval**, not chosen in the script. A rate
reported without its interval is not a valid output of this protocol.

> **PAIRED, NOT MARGINAL.** All methods are evaluated on the **same synthetic replications**, so their
> rejection indicators are **paired**. Comparing two methods by checking whether their marginal
> confidence intervals overlap is **invalid** — it ignores the pairing and is systematically
> conservative. Any method-difference inference must use **paired rejection indicators** (e.g.
> McNemar-style discordant-pair analysis on the per-replication indicator vectors) or a **paired
> Monte Carlo standard error** for the difference. Overlapping marginal intervals are not evidence of
> no difference, and non-overlapping ones are not the test. The previous draft's instruction to assess
> differences "against these intervals" was wrong and is corrected here.

## 13. No tuning after results

**Binding.** After any result is observed, the following may **not** change: scenario grid, balance
rule, DGP parameters, error structures, R, seeds, method set, estimands, interval method, or output
schema. Any change after results exist makes the study **exploratory**, which must be stated in the
output, and it may not be used to support a size adjustment.

## 14. Software, environment, and script requirements

- **Every package version stated exactly in this document before approval** — not "as locked
  elsewhere". The starting point is the HYP-01 environment in `/authoritative_calculation` (R 4.6.1,
  `clubSandwich` 0.7.0, `sandwich` 3.1-3, and the remaining pinned versions recorded there), but the
  full list, including anything the simulation harness itself pulls in, must be enumerated here.
- **The executable script must be committed and reviewed BEFORE execution is authorized**, and its
  **repository path and SHA-256 recorded in this document**. Approving a protocol whose script does
  not yet exist authorizes an unreviewed program; §16 cannot be signed until the script is in hand.
- A **machine-readable environment manifest** (package versions, OS, architecture, RNG) is emitted
  with the results.
- **Nothing is deleted after use.** The failure mode this protocol exists to prevent is precisely the
  disappearance of the generating script.

## 15. Output schema and failure handling

### 15.1 Output schema

One row per (scenario, balance, error structure, method), with columns:

```
scenario_id, G, n, balance_pattern, error_structure, method_label,
replications_completed, replications_failed,
empirical_size, mc_ci_lower, mc_ci_upper, size_distortion,
nu_mean, nu_sd, nu_p05, g_star_mean,
master_seed, seed_derivation_rule, rng_algorithm,
(plus a replication-level seed record if §9 option (ii) was chosen),
script_commit_sha, script_sha256, environment_manifest_sha256,
run_started_utc, run_ended_utc, protocol_version
```

Plus a run-level record: protocol version, approval reference, and an explicit
`no_project_data_used: true` attestation.

### 15.2 Failure handling

A replication that fails to converge, produces a non-finite statistic, or trips a refusal threshold
from `/refusal_thresholds` is **recorded as a failure** — never silently retried, never replaced by a
fresh draw.

> **FAILURES ARE NOT SIMPLY DROPPED.** Excluding failures from the denominator silently assumes they
> would have behaved like the successes, which is exactly what cannot be assumed when the failure is
> a degenerate fit at small G. The previous draft did this and is corrected here.

Every cell must report **all four** of the following, and the bounds are the primary figures:

| Quantity | Definition |
|---|---|
| `failure_fraction` | `failures / R` |
| `rejection_lower_bound` | `rejections / R` — every failure counted as a non-rejection |
| `rejection_upper_bound` | `(rejections + failures) / R` — every failure counted as a rejection |
| `rejection_conditional` | `rejections / (R − failures)` — **clearly labelled as conditional on the replication succeeding**, and never reported alone |

**A cell whose bounds are wide enough to change the substantive classification cannot support
calibration.** Concretely: if `rejection_lower_bound` and `rejection_upper_bound` fall on opposite
sides of a threshold that would change the conclusion — nominal 0.05, or whatever cutoff a future
calibration rule uses — that cell is `INDETERMINATE` and must not be used to derive a critical value,
justify a method choice, or support a power claim. It is reported with its bounds and left there.
- Any deviation from this protocol during execution must be recorded in the output as a deviation.
  Undocumented deviation voids the run.

## 16. Approval gate

> **This protocol must be approved, in writing, by the co-authors before any execution.**

### 16.1 Exact specifications that must be filled in FIRST

**The protocol cannot be approved while any row below is unspecified.** Each is currently blank by
design; none may be deferred to the script.

| # | Item | Value |
|---|---|---|
| 1 | Balanced cluster allocation, per G (all five scenarios) | `________` |
| 2 | Unbalanced cluster allocation, per G (all five scenarios) | `________` |
| 3 | Cluster-intercept variance | `________` |
| 4 | Idiosyncratic-error variance | `________` |
| 5 | Heteroskedasticity-generating rule (E2) | `________` |
| 6 | Heavy-tail distribution and degrees of freedom (E3) | `________` |
| 7 | Regressor construction (i.i.d. or clustered; exact distribution) | `________` |
| 8 | Clustered-regressor / high-leverage stress arm: included? | `________` |
| 9 | Outcome construction / transformation | `________` |
| 10 | Master seed (exact integer) | `________` |
| 11 | Deterministic seed-derivation rule | `________` |
| 12 | RNG algorithm (named) | `________` |
| 13 | Monte Carlo interval method (Wilson / Clopper–Pearson) | `________` |
| 14 | M5 wild bootstrap: included or excluded | `________` |
| 15 | All package versions (full enumeration) | `________` |
| 16 | Executable script repository path | `________` |
| 17 | Executable script SHA-256 | `________` |

### 16.2 Approval checklist

- [ ] **P1.** Every row of §16.1 filled in, in this document, and reviewed
- [ ] **P2.** Scenario grid (§6) approved, or amended before execution
- [ ] **P3.** DGP assumptions (§7.2) approved as written, with no cell left to the script
- [ ] **P4.** Error structures (§7.3) approved with exact rules and parameters
- [ ] **P5.** R = 10,000 approved or increased
- [ ] **P6.** Method set (§10) approved, including the explicit M5 include/exclude decision
- [ ] **P7.** Paired-inference requirement (§12) understood and accepted
- [ ] **P8.** Failure-bound reporting and the `INDETERMINATE` rule (§15.2) accepted
- [ ] **P9.** Confirmation that the historical §2 figures are **not** treated as evidence
- [ ] **P10.** Confirmation that execution touches **no** project outcome
- [ ] **P11.** **Executable script committed and reviewed**, path and SHA-256 recorded in §16.1
- [ ] **P12.** Explicit authorisation to execute

> **No run is authorized by this document, and none was authorized in the correction pass that
> produced this revision.**

**Until P1–P10 are signed, this document is a plan and nothing more. No results exist. No size
adjustment may be claimed. A9 remains `A9_BLOCKED_MISSING_REGISTERED_SESOI` independently of this
protocol's status.**
