# Amendment A: SESOI and TOST equivalence layer

**Status: ADOPTED.** Append-only dated amendment. It edits nothing.

**Date:** 2026-08-20
**Amends:** `ProspectiveStudy_PreRegistration_v1.0_FROZEN_2026-08-20.md` (additively)
**Does not amend:** `FROZEN_DESIGN_v1.0.md`, which is untouched.

---

## A1. What this adds, and what it cannot do

Adds a **pre-registered smallest effect size of interest (SESOI)** and a **two-one-sided-tests (TOST)
equivalence procedure**, so that a null at the binding 75-event gate can be reported as an
*informative equivalence* result rather than as merely inconclusive.

**Strict limits, binding:**

1. **TOST can never produce a success verdict.** Success remains exactly the four criteria in
   `FROZEN_DESIGN_v1.0.md` §7. TOST is evaluated **only after** those four have been evaluated, and
   **only when they do not all pass**. It characterises a null; it never converts one.
2. **TOST cannot rescue a failed gate**, cannot be substituted for any of the four criteria, and
   cannot be reported in place of them. All four criteria are reported regardless of the TOST result.
3. **Three outcomes are possible and all are reported honestly:** *equivalence demonstrated*
   (effect statistically smaller than the SESOI), *inconclusive* (neither superiority nor
   equivalence — the interval spans the SESOI boundary), or *success* (the four criteria pass, in
   which case TOST is not run).
4. **The 75-event gate is unchanged.** TOST is evaluated at the same n, never earlier.

---

## A2. The SESOI anchor — corrected

The proposal anchored the SESOI to "a ~3–4pp real-vs-modeled option cost gap." **That figure does not
match the repository.** Verified 2026-08-20 directly from the committed calibration samples:

| Sample | File | real cost % of spot | model cost % of spot | **gap (pp)** | ratio |
|---|---|---|---|---|---|
| n = 37 (Pass 1) | `Live Signal Engine/QC_Validation_CleanSample_37Events.csv` | mean 6.9006 / med 6.0200 | mean 2.3104 / med 2.0220 | **mean 4.5902 / med 3.9980** | 2.987× |
| n = 76 (Pass 2) | `Live Signal Engine/QC_Validation_CleanSample_v2_76Events.csv` | mean 7.5442 / med 7.5725 | mean 2.7827 / med 2.6525 | **mean 4.7615 / med 4.9200** | 2.711× |

Two distinct errors are corrected:

- **"3.65" in the record is a dimensionless multiplier, not percentage points.**
  `GST_Recalibrate_IV_Markup.py` records `new_markup = 3.6516` (n = 37), derived as
  `OLD_MARKUP × correction_factor` where `OLD_MARKUP = 1.239816` comes from the "near earnings"
  bucket of `Earnings Clustering Test/iv_calibration_buckets.csv`. It is a **cost multiplier (≈3.65×)**,
  not a 3.65pp gap.
- **Read as percentage points, "3–4pp" matches only the n = 37 median (3.998pp)** — the smaller,
  superseded sample. On the larger n = 76 sample the gap is **4.76pp (mean) / 4.92pp (median)**.

**Adopted SESOI:** `SESOI = 4.76 pp` — the **mean** gap on the **n = 76** sample, the largest and most
recent real-quote calibration in the repository. Fixed here, before any v2 observation exists, and not
re-selected afterwards. Rationale: an improvement smaller than the measured gap between modelled and
actually-quoted option cost cannot be captured by any executable position, so it is not of interest
regardless of statistical significance.

**Sensitivity, pre-committed:** the TOST is additionally reported at `SESOI = 3.998 pp` (n = 37
median) and `SESOI = 4.92 pp` (n = 76 median) as a fixed, pre-specified robustness triple. Choosing
among the three after seeing results is prohibited; all three are always reported.

---

## A3. Provenance disclosure (required)

The SESOI is derived from the **retrospective** 152-event population's real-quote pulls, not from
prospective data. This is a permitted use — a cost parameter fixed in advance is a design constant,
in the same category as a power-calculation input, and no outcome of the prospective study informs it.

It must nonetheless be **disclosed in every report** that the SESOI anchor originates in retrospective
data, so the prospective study is not represented as fully independent of the historical population in
its design constants. The prospective study separately measures its own `executable_straddle_cost`
per `FROZEN_DESIGN_v1.0.md` §4; where those realised costs materially diverge from the 4.76pp anchor,
**that divergence is reported and the SESOI is still not changed.**

---

## A4. Procedure

At n ≥ 75 eligible events, on the paired chronological out-of-sample MAE improvement versus the
options-only baseline (the §7.1 quantity, expressed in the same units as the SESOI):

1. Evaluate the four `FROZEN_DESIGN_v1.0.md` §7 criteria and report all four.
2. If all four pass → **success**; TOST is not run.
3. Otherwise run TOST at α = 0.05, one-sided each side, against bounds `[−SESOI, +SESOI]`, using the
   **same block-bootstrap** resampling already specified for the §7.2 interval — no new resampling
   scheme is introduced.
4. Report exactly one of: **equivalence demonstrated** (both one-sided tests reject) or
   **inconclusive** (at least one fails to reject).
5. Report the TOST result for all three SESOI values in the A2 triple.
6. Report the count of events containing a retried capture (Method v2 §5.5) and confirm the TOST is
   reproducible with them excluded.

---

## A5. Audit note — consistency with prior rulings this session

Same convention as the n = 40 and open-universe rejections recorded on 2026-08-20:

- **n = 40 rejected as a verdict gate** — `FROZEN_DESIGN_v1.0.md` §7 pre-commits 75; 40 was recorded
  only as a descriptive-only checkpoint.
- **Open universe rejected** — §2 prohibits any generated ticker list; the universe was constituted
  from dated, hash-recorded official index snapshots instead.
- **Externally supplied number corrected against the files.** The originating prompt supplied a
  cost floor of "~3-4pp"; verification against the calibration files corrected it to **4.76pp mean**
  (n = 76, `Live Signal Engine/QC_Validation_CleanSample_v2_76Events.csv`), adopted with the
  pre-committed robustness triple **3.998 / 4.76 / 4.92**. This is the session's **third**
  file-check correction of an externally supplied number, logged under the same convention as the
  n = 40 and open-universe rejections.
- **This amendment is permitted on the same principle, from the other direction:** it **adds** a
  characterisation layer without relaxing any in-force commitment. Success criteria, the 75-event
  gate, and the prohibition on altering gates after observations accumulate are all untouched. The one
  correction applied is to the *anchor value*, which was wrong in the proposal and is fixed here
  against the actual calibration files rather than accepted as stated.
