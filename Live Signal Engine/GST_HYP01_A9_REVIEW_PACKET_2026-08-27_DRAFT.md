# GST HYP-01 / A9 review and decision packet — 2026-08-27 DRAFT

**Status:** DRAFT, committed on a review branch; not approved, registered, or final. **Nothing in this packet is approved or registered.**

> **Date note.** The `2026-08-27` in this filename is the label specified by the co-author for this
> review cycle. The host clock at the time of preparation read **2026-08-26 21:48 America/Chicago**,
> so the work was actually performed on **2026-08-26**. The filename is kept as instructed; the
> preparation date is recorded accurately here rather than silently adjusted. The 2026-08-27 02:15
> scheduled collection cycle had **not yet occurred** at preparation time — see §1 of the operational
> report and the status `AUG27_VERIFICATION_PENDING`.

**Branch:** `hyp01-a9-reconciliation-20260826` · **Base:** `phase6-control-matching-integrity` @
`63e8a13d8fadc4a52b8046df983fb6a8705e9985`

---

## 1. Executive status

| Question | Answer |
|---|---|
| Is any scientific result presented? | **No.** None exists to present |
| Was any prospective outcome inspected? | **No** — see §11 |
| Is a SESOI registered? | **No** |
| Can A9 run? | **No** — `A9_BLOCKED_MISSING_REGISTERED_SESOI` |
| Are C6/C7 closed? | **Substantively yes, administratively no** |
| Is an external effect-size anchor available? | **No** |
| Has any simulation been run for this work? | **No** |
| Is any draft ready to lose DRAFT status? | **No** — all eight require co-author approval |

The work in this branch is **reconciliation and documentation only**. It resolves what the committed
artifacts actually say, records what they do not say, and prepares the decisions a human must make. It
makes no scientific decision of its own.

## 2. Artifact manifest

Draft documents produced on this branch. Hashes are recorded in the companion manifest
`GST_HYP01_A9_DRAFT_MANIFEST_2026-08-27.txt`, which is generated from the files themselves and is
authoritative for byte-level verification.

| # | Document | Role |
|---|---|---|
| 1 | `HYP01_LITERATURE_FRAMING_AMENDMENT_v0.3_DRAFT.md` | Literature framing; makes no design decision |
| 2 | `A9_EFFECT_SIZE_COMPARABILITY_MEMO_v0.3_DRAFT.md` | Why A9 is blocked; rules binding a future A9 |
| 3 | `HYP01_A9_ARTIFACT_RECONCILIATION_TABLE_v1.0_DRAFT.md` | 19-item reconciliation from committed artifacts |
| 4 | `HYP01_A9_LITERATURE_SEARCH_LOG_2026-08-26.md` | Bounded search, closed |
| 5 | `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` | Administrative erratum; no inference decision |
| 6 | `GST_HYP01_A9_REVIEW_PACKET_2026-08-27_DRAFT.md` | This document |
| 7 | `HYP01_SESOI_DECISION_PACKET_v0.1_DRAFT.md` | Decision support; contains **no** numerical SESOI |
| 8 | `HYP01_INFERENCE_SIZE_SIMULATION_PROTOCOL_v0.1_DRAFT.md` | Prospective protocol; **not executed** |

**Source artifacts consulted** — SHA-256 as checked out on the base, full table in document 3:

| Path | SHA-256 |
|---|---|
| `Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_v1.0.json` | `782bd1c361919e2497db5466e2985ac91f19a0fdd2add9eea406984eb80faafa` |
| `Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json` | `e8aa72cabef191ce4136377b33713a34eead9b1e3d891d8a079bfe0cb2ce3895` |
| `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` | `af5a8c963f14d93787477078ca82a90401e79ed678ad82788a01386722b7d892` |
| `Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` | `0cec967f4b208b73f2f7fbd4e220c09d717ea8e3986aa67ce3ce4ec8727d10c9` |
| `Live Signal Engine/GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json` | `04b642ebcf3f9eaf8a1cf85785086b9f9cd21de98c83b68ff6083f6beaff6b74` |
| `Live Signal Engine/GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` | `8836fb3dc01d7b662990daeb837b969133f51a57c929d7f4ffbb5b7bb5873ab3` |
| `Live Signal Engine/GST_HYP01_STATISTICAL_METHOD_REVIEW_PACKET_v1.0_DRAFT.md` | `cacbba900d276d02842733f1d5c060580b23c82a7188b80335f95dbfa9261bc7` |
| `Live Signal Engine/GST_HYP01_AUTHORIZER_DECISION_MATRIX_v1.0_DRAFT.md` | `e27b382fd0f37840815f063a2606f0150b2dc358b72eabd8e5471163f63b466b` |
| `Live Signal Engine/GST_HYP01_METHOD_AUTHORIZATION_2026-08-16.md` | `c5dd83d3e312edf70426ac3bcb120df99ad0c9c3d9302153376dd5ed895a2f9d` |
| `PREREGISTRATION_GAP_AUDIT_v1.0.md` | `82885acda38ff51369b2ad47e38442106ce9f0af46ec2e00c2e366e31a1d3dd8` |

**No source artifact was modified.** All retain their original bytes and hashes.

## 3. Binding design facts

Every row is read from a committed artifact; none is inferred.

| Fact | Value | Source pointer |
|---|---|---|
| Binding sample gate | **60 eligible events** | effective lock `freeze_and_display.threshold` = `60`, `run_count` = `1` |
| `n = 75` | **Unsourced.** Appears in no committed HYP-01, registry, gap-audit or preregistration artifact | whole-tree search; recorded as unsourced, **not** refuted, and **not** adopted |
| Maximum possible clusters | **24** (cluster = ticker; universe locked at 24) | method review request line 27 |
| Eligible HYP-01 events | **0** | registry `/eligible_event_counts/HYP-01` |
| Eligible outcome observed or analysed | **No** | effective lock `/effective_state/analysis_run` = `false`, `/scientific_result` = `null` |
| Primary predictor | **`gst_zscore`** | effective lock `/unamended_base_lock_invariants/"primary_model.coefficient_of_interest"` |
| Primary outcome | **`abs_overnight_gap`** | `"primary_model.formula"` = `abs_overnight_gap ~ gst_zscore` |
| Alpha | **0.05** | `"primary_model.alpha"` |
| Sidedness | **two-sided** | `"primary_model.sidedness"` = `two_sided` |
| Locked inference | **CR2 + BRL + coefficient-specific Satterthwaite** | `/effective_decisions/D1`, `/D2`, `/D3` |
| Wild cluster bootstrap | **No registered HYP-01 role** | `/effective_decisions/D4` = `NOT_USED_IN_HYP01`; D5–D7 `NOT_APPLICABLE` |
| Registered SESOI | **None** | exhaustive artifact search |
| Registered equivalence procedure | **None** | exhaustive artifact search |
| Descriptive checkpoint | **None registered** | exhaustive artifact search |

**Why the three `60`s are not a contradiction.** The governance eligibility floor, the freeze/display
threshold, and the deterministic cohort rank cut (`rank ≤ 60` ELIGIBLE, above it `EXTENSION_COHORT`)
all sit at 60 by design. They are one gate seen from three angles, not competing sample sizes.

## 4. Literature conclusions

> **No compatible external effect-size anchor identified as of 2026-08-26 under the prespecified
> comparability criteria.**

The bounded search is **closed**. Three papers assessed, all excluded.

| Paper | Verdict | Binding reason |
|---|---|---|
| Drake, Roulstone & Thornock (2012) | **EXCLUDED** | Criterion 3 — DV `AR[0, +1]` is a **signed** return, not absolute magnitude. Also criterion 1 (interaction conditional on `UE`) and 4 |
| Da, Engelberg & Gao (2011) | **EXCLUDED** | Criteria 2, 3, 4, 5 — signed subsequent return and reversal, not pre-announcement-window absolute magnitude |
| Ahluwalia (2026) | **EXCLUDED on criterion 3** | Signed/directional outcome. Criteria 4 and 5 are **`NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`** — untested, **not** failed |

The obstacle is structural, not bibliographic: HYP-01's locked outcome is an **absolute** magnitude and
the located literature estimates **signed** quantities. Converting between them is not a units change.

**No external coefficient is used as an anchor anywhere in this package.**

## 5. Drake version-resolution note

**Citation authority: the final published article.** Michael S. Drake, Darren T. Roulstone, and Jacob
R. Thornock (2012), "Investor Information Demand: Evidence from Google Searches Around Earnings
Announcements," *Journal of Accounting Research* 50(4), 1001–1040, DOI
`10.1111/j.1475-679X.2012.00443.x`.

Verified from the author-deposited open-access copy (BYU ScholarsArchive Faculty Publications 8399),
accessed 2026-08-26, PDF SHA-256 `faabe0549cd6853227ce4c28811d63fd8ad46ba1ccb0ea8d73bbb4052e27198a`,
462,447 bytes, 41 PDF pages. **The PDF is not committed** — copyrighted article.

| Verified fact | Value |
|---|---|
| Universe | **S&P 500** |
| Period | **2005–2008** |
| Observations | **N = 4,133** quarterly |
| Location | **Table 8, model (6)**, DV **`AR[0, +1]`**, printed p. 1033 |
| `UE × AbSearch[FQE, −1]` | **−3.289** (2.223) · **−2.477** (1.043) |
| `UE × AbSearch[−5, −1]` | **−3.818** (1.364) · **−2.863** (0.809) |
| Both shorter-window estimates | marked **`***`** (p < 0.01) |
| Tests | **one-tailed where a direction is predicted** (table footnote) |
| Standard errors | clustered by **calendar quarter × Fama-French 17 industry** |
| Outcome type | **Signed** abnormal return |
| Estimand | **Conditional interaction with unexpected earnings** |
| Conversion to HYP-01's marginal absolute-gap coefficient | **None justified** |

**Earlier versions are not called erroneous.** Pre-publication drafts circulated with different table
numbering, and a "Table 6" citation may be correct against one of them. This package takes no position
on any working-paper version; it fixes the **published version of record** as the citation authority,
under which Table 6 (p. 1029) is a *different*, **positive** result on `AR[−5, −1]` and Table 7
(p. 1031) is abnormal volume.

## 6. C6 / C7 status

| Item | Status |
|---|---|
| **C6** — ticker-cluster covariance estimator | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** |
| **C7** — finite-sample correction and inference procedure | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** |

The 2026-08-16 dated amendment specifies CR2, BRL, and coefficient-specific Satterthwaite, and states
the wild cluster bootstrap plays no role — the full subject matter of both register entries. It
**never names C6 or C7**, and `PREREGISTRATION_GAP_AUDIT_v1.0.md` has not been re-issued since
2026-08-09, so both still read UNRESOLVED there. `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` records this and
makes **no new inference decision**; it requires a co-author signature to take effect.

## 7. Simulation reproducibility gap

**`SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP`.**

`GST_HYP01_STATISTICAL_METHOD_REVIEW_PACKET_v1.0_DRAFT.md` §5.1 reports rejection rates from a
synthetic demonstration that was run **outside the repository** under a **true null**, whose
**"script was deleted after use"**. Those figures are **quarantined** in
`A9_EFFECT_SIZE_COMPARABILITY_MEMO_v0.3_DRAFT.md` §6.1 as historical record. They are **not** used to
support any normative claim, are **not** the project's empirical size, and must not be quoted in a
preregistration or used to justify a threshold, a method choice, or a power figure.

Those figures are **not** "the project's empirical size" — no figure in this repository is. They are
an estimated rejection rate under a synthetic DGP that was never recorded.

**A null simulation would not, by itself, produce size-adjusted power.** It estimates rejection rates
under declared synthetic DGPs and nothing more. Size-adjusted power additionally requires a registered
SESOI or labelled hypothetical alternative, a **predeclared calibration rule** deriving a 5% cutoff
from the null results, **separate alternative-DGP simulations** at that cutoff, matched
cluster-count/balance/regressor/error scenarios, and Monte Carlo uncertainty on the power estimate
itself. Until all five exist, only **nominal-reference power with an explicit
anti-conservatism/upper-bound warning** may be reported. An earlier draft implied a null run alone
sufficed; that is corrected in the memo's §6.

A prospective protocol for the **null half only** is drafted at
`HYP01_INFERENCE_SIZE_SIMULATION_PROTOCOL_v0.1_DRAFT.md`, which is **unapproved and unexecuted** and
cannot be approved until every parameter in its §16.1 is filled in.

## 8. SESOI blocker

**`A9_BLOCKED_MISSING_REGISTERED_SESOI`.**

No registered smallest-effect-size-of-interest exists in any dated artifact — no value, no units, no
registration date. The locked `n = 60` cannot substitute: the display-gates document states
affirmatively that the thresholds "are **not** … minimum detectable effect sizes". The registry states
"No power calculation was performed, and none may be performed using observed project results."

**No numerical SESOI is proposed, recommended, inferred, or registered anywhere in this package.**
`HYP01_SESOI_DECISION_PACKET_v0.1_DRAFT.md` prepares the decision for a human; it deliberately leaves
the value blank.

## 9. Co-author approval checklist

Each item requires an explicit decision. None is pre-answered.

- [ ] **A1.** Literature-framing amendment v0.3 — approve as drafted / revise / reject
- [ ] **A2.** A9 comparability memo v0.3 — approve / revise / reject
- [ ] **A3.** Artifact-reconciliation table v1.0 — approve / revise / reject
- [ ] **A4.** Literature-search log — approve / revise / reject; confirm the search may stay closed
- [ ] **A5.** C6/C7 administrative erratum — approve for signature / revise / reject
- [ ] **A6.** Confirm `n = 75` remains **unsourced and unadopted**
- [ ] **A7.** Confirm Drake is cited to the **published version of record** and that earlier working-paper numbering is not disparaged
- [ ] **A8.** Confirm Ahluwalia criteria 4/5 remain `NOT_EVALUATED_AFTER_CRITERION_3_FAILURE`
- [ ] **A9.** Confirm the historical simulation figures stay quarantined under `SIMULATION_EVIDENCE_REPRODUCIBILITY_GAP`
- [ ] **A10.** SESOI — select value, units, symmetry, interpretation, derivation (see decision packet)
- [ ] **A11.** Simulation protocol v0.1 — approve unchanged / revise / reject
- [ ] **A12.** Authorise removal of `DRAFT` status, per document, once A1–A11 are settled
- [ ] **A13.** Authorise merge of the draft PR into `phase6-control-matching-integrity`

## 10. Current repository state

**PR #39 is OPEN as a DRAFT.**
<https://github.com/harshith-akurati/gst-earnings-signal-research/pull/39>

| Field | Value |
|---|---|
| PR | **#39**, state **OPEN**, **isDraft = true** |
| Base | **`phase6-control-matching-integrity`** |
| Head | **`hyp01-a9-reconciliation-20260826`** |
| Auto-merge | **not enabled** |
| Merged | **no** |

The branch carries four documentation commits plus this correction pass. Exact SHAs are recorded in
the commit history and in `GST_HYP01_A9_DRAFT_MANIFEST_2026-08-27.txt`; they are deliberately **not**
restated here, because a document committed inside the branch cannot contain the SHA of the commit
that adds it.

> **The PR must never target `phase5-unattended-panel-recovery`.** That branch is the live
> machine-data-only collection branch. Nothing in this package may reach it, and the base must remain
> `phase6-control-matching-integrity`.

**Do not merge, mark ready for review, approve, enable auto-merge, or change the base** until the §9
checklist is recorded.

## 11. No prospective outcome was inspected

Stated explicitly, as required.

- **No** panel row, financial value, or search value was opened at any point in this work.
- **No** eligible HYP-01 outcome was calculated, inspected, previewed, plotted, or described.
- The eligible-event count (**0**) was read from the registry's `/eligible_event_counts` field and
  from protocol dates — the display-gates document states the count itself is not a result.
- **No** power calculation was performed. **No** SESOI was chosen. **No** simulation was run.
- **No** date was backfilled.
- The live worktree, its branch, and the scheduled task were **not** touched by this work.
