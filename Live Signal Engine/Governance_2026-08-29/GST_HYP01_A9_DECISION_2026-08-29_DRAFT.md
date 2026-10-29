# A9 — design-sensitivity / power decision

**Status:** `DRAFT_UNSIGNED`. **This is a recommendation, not a decision.** It takes effect only when
two named authors approve it.
**Authored:** 2026-08-29, before any eligible HYP-01 event or outcome exists (eligible count **0**).

## The gap

`PREREGISTRATION_GAP_AUDIT_v1.0.md` row **A9**: *"no power or design-sensitivity analysis exists"* —
class `SCIENTIFIC_DECISION`, deadline `BEFORE_FIRST_OBSERVATION`. The audit's own constraint: any such
analysis *"must use externally justified or clearly hypothetical effect sizes; must never use observed
prospective project results; and must not silently change the locked n = 60."*

## Recommended decision

| # | Recommendation |
|---|---|
| **A9-1** | **Perform no A9 design-sensitivity or power analysis.** |
| **A9-2** | **Register no SESOI.** |
| **A9-3** | **Authorize no equivalence test.** |
| **A9-4** | **`n = 60` remains a governance eligibility floor, not a demonstrated power target** — restating adopted **D16** `NO_PROJECT_DERIVED_POWER_CLAIM`, which this decision does not modify. |
| **A9-5** | **No null result may be described as establishing equivalence, absence of effect, or a negligible effect.** Absent a registered SESOI and an authorized equivalence procedure, the primary test can only *fail to reject*. |
| **A9-6** | **No future power analysis derived from project results may revise the cohort**, the threshold, or the stopping rule — before or after the freeze. |

## Why this is coherent, and what it costs

**The locked primary test needs no SESOI.** It is `abs_overnight_gap ~ gst_zscore`, OLS,
ticker-clustered, **two-sided at α = 0.05** — a test of whether the effect is zero. A
smallest-effect-of-interest is required only for an equivalence procedure or a power calculation,
neither of which is being authorized.

**No external anchor is available.** A bounded literature search closed 2026-08-26 without a
comparable published estimate, and **D16 prohibits** deriving one from this project's own results —
that would make the bar a function of the quantity it is meant to judge.

**The cost, stated plainly.** Declining A9 means the study **cannot claim to be adequately powered**,
and a null result will be **uninformative about small effects**. That is a real limitation and must be
disclosed in any write-up, not presented as a costless design choice. The alternative — inventing a
SESOI to manufacture a power claim — would be worse.

## What signing this does not do

It does not close F5, authorize collection, or permit analysis. It does not alter `n = 60`, α,
sidedness, or any adopted decision.

**A9-2 and A9-3 are independently reversible.** The authors may later register a SESOI and separately
authorize an equivalence test, each in its own dated amendment authored **before any outcome is
seen**. Declining today forecloses nothing except the claim of adequate power.

## Signatures

| Field | Entry |
|---|---|
| Author 1 name · signature · timestamp | `____________` |
| Author 2 name · signature · timestamp | `____________` |
| A9-1 accepted (no power analysis)? **yes / no** | `____________` |
| A9-2 accepted (no SESOI)? **yes / no** | `____________` |
| A9-3 accepted (no equivalence test)? **yes / no** | `____________` |
| Confirm: the limitation in A9-5 will be disclosed in any write-up | `____________` |
| Confirm: no observed project result informed this decision | `____________` |
