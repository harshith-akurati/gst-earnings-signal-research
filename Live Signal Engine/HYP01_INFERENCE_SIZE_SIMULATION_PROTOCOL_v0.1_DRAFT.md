# HYP-01 inference-size simulation protocol — v0.1 DRAFT

**Status:** DRAFT, **UNAPPROVED AND UNEXECUTED**. Prepared **2026-08-26** (host clock 21:48
America/Chicago); filed under the co-author's 2026-08-27 review-cycle label.

> **No simulation has been run under this protocol, and none may be run until the approval gate in
> §16 is signed.** This document contains **no empirical results**. Every table below is a *schema*
> for results that do not yet exist.

---

## 1. Purpose

To establish, by synthetic simulation under a **true null**, the **empirical size** of the locked
HYP-01 inference procedure at the cluster counts and balance patterns the realised design may present.

This is needed because a power figure computed against a nominal reference distribution is only an
**upper bound** on true power when empirical size is inflated. Without a reproducible size estimate,
`A9_EFFECT_SIZE_COMPARABILITY_MEMO_v0.3_DRAFT.md` §6 permits only option (b) — a qualitative
upper-bound label. This protocol is the route to option (a), size-adjusted power.

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
- **Unbalanced** — a declared skew. The exact allocation rule must be fixed in the script before
  execution and recorded in the output schema. The gap audit notes the cohort is expected to be
  unbalanced, so this arm is the one of primary interest.

### 7.2 DGP assumptions — declared in advance

| Component | Specification |
|---|---|
| Regressor | One continuous covariate, drawn i.i.d. standard normal, standing in structurally for `gst_zscore`. **Not** calibrated to any observed distribution |
| True coefficient | **β = 0 exactly** — this is a **true-null** study. Size only |
| Cluster effect | Additive cluster-level random intercept, variance declared in the script |
| Idiosyncratic error | Declared in the script |
| Outcome transform | The protocol must state explicitly whether the simulated outcome is left on the raw scale or transformed to respect the non-negativity of `abs_overnight_gap`. **This choice must be made and justified before execution**, and both arms may be run only if both are declared in advance |

> **Open item for co-author decision.** The outcome-transform question in the last row is a
> substantive modelling choice with a bearing on realism. It is **deliberately not decided here**, and
> approving this protocol requires deciding it.

### 7.3 Error structures

Declared in advance, each a separate labelled arm; results reported per arm, never pooled:

- **E1 — homoskedastic** normal errors (baseline).
- **E2 — cluster-heteroskedastic**: error variance varying by cluster.
- **E3 — heavy-tailed**: a declared heavier-tailed family, to probe robustness of the Satterthwaite
  approximation.

## 8. Replications and justification

**R = 10,000 replications per cell** (scenario × balance × error structure).

Justification, stated as Monte Carlo precision rather than convention: for a true rejection rate near
α = 0.05, the Monte Carlo standard error is `sqrt(0.05 × 0.95 / R)`. At R = 10,000 that is ≈ 0.00218,
giving a 95% Monte Carlo interval of roughly ±0.0043 — narrow enough to distinguish a materially
inflated size (say 0.07) from nominal, which is the decision this study must support. R may be
**increased** by amendment before execution; it may **not** be reduced, and it may **not** be changed
after any result is seen.

## 9. Deterministic seeds

- A single **master seed**, declared in the committed script.
- Per-cell seeds derived deterministically from the master seed and the cell's identifying tuple
  (scenario, balance, error structure, replication index), so any single replication can be
  regenerated in isolation.
- The master seed, the derivation rule, and the RNG algorithm are recorded in the output schema.
- **Seeds are fixed before execution and never re-drawn.** A re-run with a new seed is a *new study*
  requiring its own record, not a replacement of the first.

## 10. Methods compared

| Label | Method | Role |
|---|---|---|
| **M1** | CR2 + coefficient-specific Satterthwaite | **The locked procedure — the object of the study** |
| M2 | CR2 + t(G−1) | Comparator: isolates the reference-distribution choice |
| M3 | CR1 + t(G−1) | Comparator: the "reported reference number" method |
| M4 | CV0 + normal | Comparator: known-bad lower bound |
| M5 | Wild cluster bootstrap | **Optional, non-binding.** Only if `fwildclusterboot` (or equivalent) is installed and pinned. Currently deliberately not installed, and D4 gives it no HYP-01 role |

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

Every reported rate must carry a **95% Monte Carlo interval** (Wilson or Clopper–Pearson; the choice
declared in the script before execution). A rate reported without its interval is not a valid output
of this protocol. Differences between methods must be assessed against these intervals and not by
point-estimate ordering.

## 13. No tuning after results

**Binding.** After any result is observed, the following may **not** change: scenario grid, balance
rule, DGP parameters, error structures, R, seeds, method set, estimands, interval method, or output
schema. Any change after results exist makes the study **exploratory**, which must be stated in the
output, and it may not be used to support a size adjustment.

## 14. Software, environment, and script requirements

- **Language and packages pinned** to the environment already locked for HYP-01 in
  `/authoritative_calculation`: R 4.6.1, `clubSandwich` 0.7.0, `sandwich` 3.1-3, and the remaining
  pinned versions recorded there.
- The **script is committed to the repository before execution** — path, content hash, and commit SHA
  recorded in the output.
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
master_seed, cell_seed, rng_algorithm,
script_commit_sha, script_sha256, environment_manifest_sha256,
run_started_utc, run_ended_utc, protocol_version
```

Plus a run-level record: protocol version, approval reference, and an explicit
`no_project_data_used: true` attestation.

### 15.2 Failure handling

- A replication that fails to converge, produces a non-finite statistic, or trips a refusal threshold
  from `/refusal_thresholds` is **recorded as a failure**, counted in `replications_failed`, and
  **excluded from the rate** — never silently retried and never replaced by a fresh draw.
- If `replications_failed / R` exceeds **1%** in any cell, that cell's empirical size is reported as
  **`UNRELIABLE`** with the failure fraction, and is not used for size adjustment.
- Any deviation from this protocol during execution must be recorded in the output as a deviation.
  Undocumented deviation voids the run.

## 16. Approval gate

> **This protocol must be approved, in writing, by the co-authors before any execution.**

Approval requires, at minimum:

- [ ] **P1.** Scenario grid (§6) approved, or amended before execution
- [ ] **P2.** DGP assumptions (§7.2) approved, **including the outcome-transform decision left open in §7.2**
- [ ] **P3.** Error structures (§7.3) approved
- [ ] **P4.** R = 10,000 approved or increased
- [ ] **P5.** Method set (§10) approved; decision on whether M5 is included at all
- [ ] **P6.** Monte Carlo interval method (§12) selected
- [ ] **P7.** Confirmation that the historical §2 figures are **not** treated as evidence
- [ ] **P8.** Confirmation that execution touches **no** project outcome
- [ ] **P9.** Script committed and environment pinned **before** the first run
- [ ] **P10.** Explicit authorisation to execute

**Until P1–P10 are signed, this document is a plan and nothing more. No results exist. No size
adjustment may be claimed. A9 remains `A9_BLOCKED_MISSING_REGISTERED_SESOI` independently of this
protocol's status.**
