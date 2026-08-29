# Gap-closure mapping — C6, C7, E3

**Status:** `DRAFT_UNSIGNED`. Not adopted.
**Authored:** 2026-08-29, before any eligible HYP-01 event or outcome exists.

> **This record makes no new statistical choice.** It maps three gap-audit identifiers onto decisions
> that are **already authoritative** in the adopted lock overlay. If a signatory disagrees that a
> mapping is exact, the gap stays open — the remedy is to reject the row, never to alter the adopted
> decision.

## Why this record exists

The dated amendment of 2026-08-16 selects D1–D16 and is adopted by exact SHA-256
(`11b4df9a…e70b54bd`). **It never mentions the strings "C6", "C7" or "E3".**
`PREREGISTRATION_GAP_AUDIT_v1.0.md` therefore still lists all three as `UNRESOLVED` /
`SCIENTIFIC_DECISION`, and no artifact states whether the adopted decisions discharge them. That
silence — not the decisions themselves — is the remaining gap.

## The mapping

| Gap row | Exact issue text | Adopted decision | Adopted value | Discharges the row? |
|---|---|---|---|---|
| **C6** | *"the exact estimator variant (CR0 / CR1 / CR2 / CR3 or equivalent) is unspecified"* | **D1** — primary covariance estimator | `CR2_BIAS_REDUCED_LINEARIZATION`; authoritative path R 4.6.1 + clubSandwich 0.7.0; `vcovCR(fit, cluster = <ticker factor>, type = "CR2")` | **Yes** — D1 names exactly the variant C6 says is unspecified |
| **C7** | *"which correction, and whether reference-distribution or wild-cluster-bootstrap inference is used, is unspecified"* | **D2** + **D3** (with **D4**) | D2 `BRL_ADJUSTMENT_BUILT_INTO_CLUBSANDWICH_CR2` — BRL only, no CR1 scaling, no second correction; D3 `COEFFICIENT_SPECIFIC_SATTERTHWAITE` with realized df persisted; D4 records the bootstrap as `NOT_USED_IN_HYP01` | **Yes** — D2 fixes the correction, D3 the inference procedure, D4 closes the bootstrap alternative |
| **E3** | *"any adjustment across families is explicitly PENDING_SEPARATE_ANALYSIS_LOCK"* … *"must be decided and written down, not assumed by silence"* | **D15** | `NO_ADJUSTMENT_FOR_THE_SINGLE_LOCKED_PRIMARY_TEST`; family = 1 predictor / 1 outcome / 1 test / α = 0.05 two-sided | **Yes** — the decision is now written down rather than assumed by silence |

## What this record is careful not to claim

- **No new statistical choice is made here.** Every value above is quoted from the adopted amendment.
- **It does not amend the gap audit.** That document is "Audit only"; this is a separate dated record
  a future audit revision may cite.
- **It does not extend to C9, E8, F5, A9, B3, F2, F3 or F4.** Those remain open. E8 has its own
  artifact in this set; F5 and A9 have theirs.
- **Split provenance travels with C6/C7.** The adopted authorization records that CR2 covariance, SE,
  t and p were validated under **PR #17** tolerances, while the continuous Satterthwaite degrees of
  freedom were validated under a **separately prespecified PR #18 tolerance not preregistered in
  PR #17**. That distinction accompanies any citation of D1/D3, including this one.
- **Implementation validation is not scientific proof.** PR #18 established that the study's Python
  code computes what clubSandwich computes on synthetic fixtures. That is implementation agreement —
  not evidence that CR2 is the scientifically correct or optimal estimator for HYP-01.

## Signatures

| Field | Entry |
|---|---|
| Approver 1 name · signature · timestamp | `____________` |
| Approver 2 name · signature · timestamp | `____________` |
| C6 mapping accepted? **yes / no** | `____________` |
| C7 mapping accepted? **yes / no** | `____________` |
| E3 mapping accepted? **yes / no** | `____________` |
| Confirm: no new statistical choice was made by signing | `____________` |
