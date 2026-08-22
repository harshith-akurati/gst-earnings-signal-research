# Corrective analysis design v1.0 — FROZEN

**Date:** 2026-08-22
**Status:** FROZEN on commit, **before the corrective analysis is run**. No corrected estimate exists
at the time of writing, and no corrected outcome was inspected in choosing any rule below.
**Supersedes nothing.** The original result stays published and citable as *superseded*, per §11.

Prerequisite: Phase 1 overlay `65ef9ab`.

---

## 1. Event identity

> **Identity = (`ticker`, `earnings_date`)**, evaluated **after** `nearest_earnings_date()` resolution.

Resolution-time identity is the binding definition precisely because the defect is a post-resolution
collapse: two distinct anchors can map to one earnings event. Any rule stated on `anchor` would not
have caught it.

---

## 2. Self-match exclusion — mandatory

A pair is **invalid** if its control identity equals its treated identity.

Applied **after** date resolution, as a pair-level check. It is deliberately *not* placed inside
`nearest_earnings_date()`, which sees one row and cannot see the pair.

Verified equivalent upstream guard, recorded for completeness: all 20 observed self-matches have
`|control_date − spike_week| ≤ 10` days against `EARNINGS_MATCH_WINDOW_DAYS = 10`, and no non-self-
matched pair does. Requiring anchor separation strictly greater than the resolution window is
therefore an equivalent prophylactic. **The post-resolution identity check is the binding rule**,
because it holds regardless of any future change to the window.

---

## 3. Matching with or without replacement

> **Primary: WITHOUT replacement.** Each control identity is used **at most once** across the entire
> matched set.

Rationale: the pseudoreplication is the defect under correction. Retaining it and modelling it is
what the original already did, and that path is preserved as a pre-specified sensitivity (§10a), not
as the primary.

---

## 4. Deterministic tie-breaking

When two or more treated events claim the same control identity, assignment is fully deterministic
and independent of any outcome value.

**Processing order** — treated events sorted ascending by:
1. `ticker` (lexicographic, ASCII)
2. `earnings_date` (ascending)
3. `pair_id` (integer, ascending)

**Claim resolution** — the contested control identity is awarded to the claimant with:
1. smallest `|control_anchor − treated_anchor|` in whole days;
2. then earliest treated `earnings_date`;
3. then lexicographically smallest `ticker`;
4. then smallest `pair_id`.

Losing claimants proceed to §6. **No outcome, return, z-score or test statistic may enter any
tie-break.** Every criterion is fixed here before the run.

---

## 5. Caliper and eligibility

Eligibility is **inherited unchanged** from the original matcher
(`GST_MatchedControlGroup_CanonicalRecompute.py`) so that the correction isolates the two defects
rather than silently re-specifying the study:

- same `ticker` and same `bmo_amc` preferred (`match_type = same_ticker`);
- cross-ticker fallback requires same sector and the frozen market-cap band, with the volatility
  band `VOL_BAND_LOW … VOL_BAND_HIGH` and nearest `vol_dist` then `date_dist`;
- control anchors drawn from the archived non-spike ("clean") exclusion pool.

**Two rules are added, and only two:**

- **E1 — identity distinctness.** Control identity ≠ treated identity (§2).
- **E2 — global uniqueness.** Control identity unused by any other surviving pair (§3).

**Rows already excluded upstream stay excluded.** The 19 `MATCH_UNPRICEABLE` pairs remain out; they
are the same 19 that drop on price coverage and are not revisited.

### Scope limitation, stated plainly

The control **candidate pool is not committed to the repository** — `build_candidate_pool()`
reconstructs it at runtime from network sources. This correction therefore operates as a
**restriction of the existing matched set, not a re-match.** A treated event that loses its control
under E1 or E2 is **dropped**, not re-paired against an alternative candidate.

Consequence, acknowledged in advance: the corrected sample is smaller than a true re-match would
yield, and the surviving set is a **non-random subset** of the original treated arm — events whose
control collided are systematically those with a near-in-time or heavily-contested control. This is a
limitation of the corrected estimate and will be reported as one. Re-matching from a rebuilt pool
would require new data retrieval and is out of scope here.

---

## 6. When no eligible unique control remains

The treated event is **dropped from the matched analysis** and counted in
`dropped_no_unique_control`, with its ticker and earnings date recorded.

Explicitly prohibited: falling back to a reused control, relaxing E1 or E2, widening the caliper,
substituting a cross-ticker control where the original was same-ticker, or imputing a control
outcome. **No treated event may be retained without a valid unique control.**

---

## 7. Estimand

> The **average treatment effect on the treated (ATT)**: the difference in **mean absolute
> event-day return**, in percentage points, between high-GST earnings events and their matched
> non-spike control earnings events at the same firm.

Outcome variable: `|day_return| × 100`, where `day_return = close(T)/close(T−1) − 1` and `T` is the
event day under the frozen release convention — **identical to the original**, unchanged.

---

## 8. Primary statistic

> **Mean paired difference in percentage points** across surviving matched pairs:
> `mean( |day_return|_treated − |day_return|_control )`.

Paired, not two-sample, because after §3 the design is 1:1 with distinct identities on both sides.
Reported with the surviving pair count.

Note for comparability: the original headline `Q1_abs_move_high_vs_control` was an **unpaired Welch**
contrast of 152 against 133. The corrected primary is paired. That is a deliberate change of
statistic to match the corrected design, and the unpaired form is retained as sensitivity §10b so the
original and corrected numbers can be compared on like terms.

---

## 9. Inference

> **CR2/BRL cluster-robust variance, clustered on `ticker`, with coefficient-specific Satterthwaite
> degrees of freedom.**

Reused unchanged from `tools/hyp01_inference_feasibility.py`, the implementation already tied out
against an independent R `clubSandwich` reference on 13 of 13 admissible fixtures.

Justification against the corrected dependence structure: without-replacement matching removes the
reused-control dependence entirely, and the self-match exclusion removes cross-arm contamination. The
dependence that remains is **within-firm across separate earnings dates**, since every pair is
same-ticker except at most one. Ticker is therefore the correct and weakly conservative cluster.

Reported: coefficient (pp), CR2 standard error, Satterthwaite df, t, p, 95% CI, cluster count.
A naive paired t is reported **alongside** for comparison and is **not** the inferential basis.

---

## 10. Pre-specified sensitivity analyses

Fixed here; results reported whatever they show.

- **(a) With replacement retained.** Self-match exclusion applied, reuse retained, CR2 on ticker.
  Isolates the reuse defect from the self-match defect.
- **(b) Unpaired Welch on the corrected arms.** Same statistic form as the original Q1, so the
  corrected and original numbers are comparable on like terms.
- **(c) Leave-one-ticker-out** on the primary, reporting the range of the point estimate across the
  28 refits. Guards against a single firm driving the result.
- **(d) Excluding the 8 overlap identities** that are both self-matched and reused (LDOS 2021-08-03,
  LDOS 2023-10-31, NFLX 2022-01-20, NFLX 2023-01-19, NKE 2024-03-21, QCOM 2025-02-05,
  SBUX 2025-01-28, STZ 2025-01-10).
- **(e) Balance diagnostics** on the surviving matched set: pre-event `|pre_drift|`, `bmo_amc`
  composition, same-ticker share, and calendar-year distribution, treated versus control.

---

## 11. Decision language

- The corrective run is **`RETROSPECTIVE_DEVELOPMENT_ONLY`**. It is **not** a HYP-01 confirmation and
  confers no prospective status.
- **No PASS / WEAK / FAIL bucket** is assigned. The output is an estimate with an interval and a
  statement of whether the prior substantive conclusion survives.
- The prior conclusion is reported as **survives / does not survive / indeterminate**, where
  *indeterminate* is the required answer when the corrected interval spans the decision-relevant
  region or the surviving sample is too small to distinguish.
- **The original result is not deleted.** `Q1_abs_move_high_vs_control` with `t = 2.138` remains in
  the repository, relabelled **SUPERSEDED** with a pointer to the corrected value, so prior citations
  remain resolvable.
- The correction is **confined to the traced lineage**. It says nothing about results outside it, and
  no such extension may be drawn from it.
- Direction is not predicted here. Whatever the corrected estimate shows — larger, smaller, or
  reversed — is reported as found.

---

## 12. Freeze attestation

At commit time: no corrective code has been run, no corrected estimate exists, no corrected outcome
has been inspected, and every rule above was chosen from the defect structure and the original
matcher's own specification alone.
