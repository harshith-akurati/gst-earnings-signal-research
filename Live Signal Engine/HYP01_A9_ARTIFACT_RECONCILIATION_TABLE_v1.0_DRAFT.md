# HYP-01 / A9 artifact reconciliation — v1.0 DRAFT

**Prepared:** 2026-08-26 · **Status:** DRAFT, committed on a review branch; not approved, registered, or final. · **Method:** committed artifacts only.

Every row below was read from a committed file in the repository. No panel row, financial value,
search value, or HYP-01 outcome was opened. Nothing was inferred from memory, from repetition across
documents, or from conversation history.

**Base for this reconciliation:** branch `phase6-control-matching-integrity` @
`63e8a13d8fadc4a52b8046df983fb6a8705e9985`. Every HYP-01, registry, gap-audit and preregistration
artifact on this base is **blob-identical** to the same path on the live branch
`phase5-unattended-panel-recovery` @ `031885f113df0e98dad1cf744488877157239c06` (verified by
`git ls-tree` comparison of mode+blob+path across the full artifact set). The live branch was
therefore not used as the document base, and nothing on it was touched.

## Artifact hashes (SHA-256, as checked out on this base)

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

Two hashes are recorded *inside* the effective-lock report as its declared inputs, and are LF-normalised
rather than as-checked-out: base lock `85264e9786e42180547a22f320da7384b4a54d1e45c777e40b2f596a982b3805`,
amendment `11b4df9a6e3321584a617fb2134afae431ac2c84ced193f85279b5bee70b54bd`. These differ from the
table above because the working tree is CRLF; that is expected and is not a discrepancy in content.

---

## Reconciliation

| # | Item | Authoritative value / status | Exact repository path | Exact field / pointer / heading | Artifact date / version | File SHA-256 (abbrev.) | Authority rationale | Conflicting artifacts or values | Resolution |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Binding primary-analysis sample-size gate | **60 eligible events** | `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` | `/unamended_base_lock_invariants/"freeze_and_display.threshold"` = `60`; `"freeze_and_display.run_count"` = `1` | Effective lock v1.0, resolved from base lock v1.0 + 2026-08-16 amendment | `af5a8c96…` | The effective-lock report is the only artifact that resolves base lock against the dated amendment; it declares `inputs_note: "Resolved solely from the base lock and the dated amendment. No other artifact contributes a rule."` | None. `n = 75` does not occur in any HYP-01, registry, gap-audit or preregistration artifact (see §"n=60 vs n=75") | **RESOLVED** |
| 2 | Descriptive checkpoint | **DOES NOT EXIST** | — | — | — | — | An exhaustive search for `descriptive checkpoint`, `checkpoint`, `interim`, `preliminary`, `midpoint`, `halfway`, `partial look` across all HYP-01 artifacts, the registry and the gap audit returns no registered checkpoint. The only `interim` hit is `GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` line 43, which lists "interim p-value" among things that may **not** be displayed | None | **RESOLVED — no such gate is registered.** Any future descriptive checkpoint would be a new scientific decision requiring a dated lock written before any outcome exists |
| 3 | Event-60 environment freeze | **Required at the event-60 freeze; not yet performed** | `Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json`; `PREREGISTRATION_GAP_AUDIT_v1.0.md` | `/decisions/D11/freeze_at_event_60/*` (analysis-script Git SHA, OS/architecture, fixture-validation artifact hash, …); gap audit line 169 enumerates: language version · statistics package · package version · cluster-covariance option string · finite-sample-correction option · random seed · analysis-code commit SHA | Amendment 2026-08-16; gap audit v1.0 (2026-08-09) | `e8aa72ca…` / `82885acd…` | The amendment is the dated authorising instrument; the gap audit enumerates the same field set as item **B4** with deadline `AT_EVENT_60_FREEZE` | None on content. The gap audit (line 132) recommends **splitting** the bundle so the statistical *rule* (C6/C7) resolves earlier than the *option string* (B4); it states explicitly that it does not make that split | **RESOLVED as to content; the recommended bundle split is NOT recorded as made in any later artifact** |
| 4 | Maximum possible clusters | **24** | `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` (authority); `GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json` (locked universe) | `/unamended_base_lock_invariants/"primary_model.covariance.cluster_variable"` = `ticker`, combined with the **locked 24-ticker universe** | Effective lock v1.0 | `af5a8c96…` | **Derived, not quoted.** A cluster *is* a ticker (locked cluster variable) and the universe *is* 24 tickers (locked), so the number of clusters cannot exceed 24. Both inputs are locked artifacts. `GST_HYP01_METHOD_REVIEW_REQUEST_v1.0_DRAFT.md` line 27 states the same thing ("At most 24 clusters … Fewer if some tickers contribute no eligible event") and is listed **as corroboration only** — it is a DRAFT request and is not authoritative for a binding design fact | None | **RESOLVED — 24 is a ceiling, not an expectation** |
| 5 | SESOI value | **NONE REGISTERED** | — | — | — | — | No artifact contains a registered smallest-effect-size-of-interest. The only adjacent text is a *proposed exercise* in a DRAFT review packet (§11 / line 211: "report what effect size would be detectable at conventional power"), which is a request, not a registration | `GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` line 71 states affirmatively that the thresholds "are **not** … minimum detectable effect sizes" | **UNRESOLVED — `A9_BLOCKED_MISSING_REGISTERED_SESOI`** |
| 6 | SESOI units and interpretation | **NOT APPLICABLE — no SESOI exists to carry units** | — | — | — | — | Follows from item 5 | None | **UNRESOLVED (blocked by item 5)** |
| 7 | SESOI source artifact and registration date | **NONE** | — | — | — | — | Follows from item 5 | None | **UNRESOLVED (blocked by item 5)** |
| 8 | Equivalence procedure | **NONE REGISTERED** | — | — | — | — | No TOST, equivalence bound, or non-inferiority procedure appears in any HYP-01 artifact. All `equivalence` hits are Wikipedia-transport fixtures and a Phase-2 chunk-reconstruction proposal, unrelated to HYP-01 inference | None | **RESOLVED — none registered.** An equivalence procedure would additionally require a SESOI (item 5) |
| 9 | Primary predictor | **`gst_zscore`** | `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` | `/unamended_base_lock_invariants/"primary_model.coefficient_of_interest"` | Effective lock v1.0 | `af5a8c96…` | Unamended base-lock invariant; the 2026-08-16 amendment does not list it in `amended_fields` | None | **RESOLVED** |
| 10 | Primary outcome | **`abs_overnight_gap`** | same | `/unamended_base_lock_invariants/"primary_model.formula"` = `abs_overnight_gap ~ gst_zscore` | Effective lock v1.0 | `af5a8c96…` | Same | None | **RESOLVED.** Note this is an **absolute** magnitude outcome — material to Phase 4 comparability |
| 11 | Primary model | **OLS**, `abs_overnight_gap ~ gst_zscore`, clustered on `ticker` | same | `/unamended_base_lock_invariants/"primary_model.estimator"` = `ordinary_least_squares`; `"primary_model.covariance.cluster_variable"` = `ticker`; `"primary_model.null_hypothesis"` = `beta_gst = 0` | Effective lock v1.0 | `af5a8c96…` | Same | None | **RESOLVED** |
| 12 | Alpha | **0.05** | same | `/unamended_base_lock_invariants/"primary_model.alpha"` | Effective lock v1.0 | `af5a8c96…` | Same; corroborated by registry `/statistical_governance/primary_alpha` = `0.05` | None | **RESOLVED** |
| 13 | Sidedness | **two-sided** | same | `/unamended_base_lock_invariants/"primary_model.sidedness"` = `two_sided` | Effective lock v1.0 | `af5a8c96…` | Same; corroborated by registry `/statistical_governance/inference_sidedness` = `two_sided` | None | **RESOLVED — already locked, and not reopened by this pass** |
| 14 | Locked covariance specification | **CR2 (bias-reduced linearisation) on `ticker`, with coefficient-specific Satterthwaite df** | `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` | `/effective_decisions/D1` = `CR2_BIAS_REDUCED_LINEARIZATION`; `/D2` = `BRL_ADJUSTMENT_BUILT_INTO_CLUBSANDWICH_CR2`; `/D3` = `COEFFICIENT_SPECIFIC_SATTERTHWAITE`; `/authoritative_calculation/covariance_call` = `vcovCR(fit, cluster = <ticker factor>, type = "CR2")`; `/authoritative_calculation/inference_call` = `coef_test(fit, vcov = <CR2>, test = "Satterthwaite")` | Amendment dated 2026-08-16, authorised 2026-08-16T03:57:18Z | `af5a8c96…` | Dated authorising amendment, post-dating the gap audit by 7 days | **Direct conflict with items 16 below** — the gap audit still carries C6/C7 as `UNRESOLVED` | **`SUBSTANTIVELY_RESOLVED`** — see item 16 and `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` |
| 15 | CR1 / CR2 / wild-cluster-bootstrap status | **CR2 = locked primary. CR1 = reported reference number only. Wild cluster bootstrap = plays no role in HYP-01; independently unvalidated** | `Live Signal Engine/GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json`; `…AUTHORIZER_DECISION_MATRIX_v1.0_DRAFT.md` | `/decisions/D4` note: "The wild cluster bootstrap-t plays no role in HYP-01."; `/effective_decisions/D4` = `NOT_USED_IN_HYP01`; D5–D7 = `NOT_APPLICABLE`; decision matrix line 37: "**CR3 and the wild cluster bootstrap-t remain independently unvalidated.** … **PR #18 did not validate CR3**, and `fwildclusterboot` was deliberately not installed. CR2 agreement is not evidence about either." | Amendment 2026-08-16 | `e8aa72ca…` / `e27b382f…` | Dated amendment plus the validation-scope statement | The **proposed** v1.1 lock (`GST_HYP01_ANALYSIS_LOCK_v1.1_PROPOSED.json` `/sensitivity_analyses.wild_cluster_bootstrap`, variant `PLACEHOLDER_PENDING_METHODOLOGIST`) contemplates a wild-bootstrap sensitivity role. The effective-lock report records `proposed_v1_1_excluded: true` | **RESOLVED — v1.1 is excluded from the effective lock and confers nothing** |
| 16 | Gap-audit items C6 and C7 | **UNRESOLVED of record** | `PREREGISTRATION_GAP_AUDIT_v1.0.md` | line 75 (**C6** — "Ticker-cluster covariance estimator … **UNRESOLVED** … the exact estimator variant (CR0 / CR1 / CR2 / CR3 or equivalent) is unspecified … `BEFORE_PREREG_AND_FIRST_OBSERVATION`"); line 76 (**C7** — "Finite-sample correction and inference procedure … **UNRESOLVED** … *which* correction, and whether reference-distribution or wild-cluster-bootstrap inference is used, is unspecified; the small-cluster problem is real at ~24 clusters") | Gap audit v1.0, last modified `6aefdd2` 2026-08-09 | `82885acd…` | The gap audit is the authoritative register of preregistration gaps and has **not** been re-issued since 2026-08-09 | The 2026-08-16 amendment selects CR2 (C6's subject) and BRL + Satterthwaite (C7's subject), but **never references C6 or C7 by identifier** — verified by grep across the amendment JSON, its MD, and the method-authorisation note | **`SUBSTANTIVELY_RESOLVED`** · **`ADMINISTRATIVELY_OPEN`** — recorded, not settled. See §"C6 / C7" and `C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md` |
| 17 | Eligible HYP-01 observation count | **0** | `Live Signal Engine/GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json` | `/eligible_event_counts/HYP-01` = `0` | Registry v1.0, last modified `0245e04` 2026-08-08 | `04b642eb…` | Canonical registry JSON; corroborated by `GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` §2 ("HYP-01 · Threshold 60 · Eligible now 0 · `ACTIVE_COLLECTING` · **CLOSED**") and §"Current status" ("**Every gate below is currently CLOSED.** No hypothesis has any eligible events.") | None | **RESOLVED — 0, and structurally so.** The cohort window `begins 2026-09-01` (`GST_PROSPECTIVE_COHORT_PROTOCOL_v1.0.json` `/…/begins`), the first DELL anchor is 2026-09-02 with release 2026-09-03, and today is 2026-08-26. No eligible event can yet exist |
| 18 | Any eligible HYP-01 outcome observed or analysed? | **NO** | `Live Signal Engine/GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` | `/effective_state/analysis_run` = `false`; `/effective_state/scientific_result` = `null`; `/effective_state/prospective_collection` = `BLOCKED`; `/effective_state/external_preregistration` = `NOT_PERFORMED` | Effective lock v1.0 | `af5a8c96…` | Effective-state block of the resolved lock, corroborated by item 17 and by the CLOSED display gate | None | **RESOLVED — no outcome has been observed or analysed.** Determined from registry, eligibility metadata, protocol dates and operational records only; no panel row or financial value was opened |
| 19 | A9 status and prerequisites | **UNRESOLVED / BLOCKED** | `PREREGISTRATION_GAP_AUDIT_v1.0.md`; `Live Signal Engine/GST_PROSPECTIVE_HYPOTHESIS_REGISTRY_v1.0.json` | Gap audit line 51 ("A9 · Design sensitivity / power · registry `statistical_governance.power_statement` · **UNRESOLVED** · `SCIENTIFIC_DECISION` · no power or design-sensitivity analysis exists · Medium · **yes**, if it were used to revise n · `BEFORE_FIRST_OBSERVATION`"); line 53 (A9 constraints); registry `/statistical_governance/power_statement` | Gap audit v1.0 2026-08-09; registry v1.0 2026-08-08 | `82885acd…` / `04b642eb…` | Both artifacts agree and neither has been superseded | The effective lock adds `/effective_decisions/D16` = `NO_PROJECT_DERIVED_POWER_CLAIM`, which constrains A9 but does not resolve it | **UNRESOLVED.** Prerequisites, verbatim from gap audit line 53: A9 "**must** occur before prospective outcomes exist; **must** use externally justified or clearly hypothetical effect sizes; **must never** use observed prospective project results; and **must not** silently change the locked `n = 60` threshold". Registry adds: "No power calculation was performed, and none may be performed using observed project results." |

---

## The `n = 60` versus `n = 75` question

**Observed fact.** The string `75`, in any sample-size or event-count sense, **does not appear in any
committed HYP-01, registry, gap-audit or preregistration artifact.** A whole-tree search across
`Live Signal Engine/` and `PREREGISTRATION_GAP_AUDIT_v1.0.md` for `75` bounded by non-digits returns
exactly one hit, and it is a source-code line-number range — `STRATEGY_SPEC_v1.0_FROZEN_2026-07-18.md`
line 160, "`lines 62, 75–86`" — which has nothing to do with sample size.

**Every `60` in the artifact set is one of three distinct things**, and they are not competing sample
sizes:

| Sense of 60 | Where | What it governs |
|---|---|---|
| **Governance eligibility floor** | registry `/eligible_event_counts` context; `GST_PROSPECTIVE_RESULT_DISPLAY_GATES_v1.0.md` §2 | The minimum eligible-event count before anyone is **permitted to look**. Explicitly *not* a power claim (§6) |
| **Freeze / display threshold** | effective lock `freeze_and_display.threshold` = `60`, `run_count` = `1` | The point at which the eligible event-ID set is frozen and the single analysis run is permitted |
| **Deterministic cohort rank cut** | `GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` §1 step 8 | `rank ≤ 60` in the `(response_session_date ASC, event_id ASC)` order is `ELIGIBLE`; rank > 60 is `EXTENSION_COHORT` |

These three coincide numerically at 60 by design — they are the same gate viewed from governance,
from analysis-freeze, and from cohort-construction. They are **not** a contradiction, and none of
them is a power-derived sample size.

**Resolution.** There is no `n = 60` versus `n = 75` contradiction *in the artifacts*. `n = 75` has no
artifact basis at all. **This does not establish that the number was never used** — it establishes
only that it is not committed anywhere in this repository. If `75` originated in conversation, in an
uncommitted note, or in a recollection, it carries **no authority**, because authority in this project
is a dated committed artifact. Per the standing instruction not to infer authority from repetition or
memory, `75` is recorded here as **UNSOURCED** rather than as refuted.

## C6 / C7

**Observed facts, in date order.**

1. `PREREGISTRATION_GAP_AUDIT_v1.0.md` (last modified 2026-08-09) records C6 and C7 as **UNRESOLVED**,
   `SCIENTIFIC_DECISION`, **Critical**, could change whether HYP-01 is reported as significant
   ("**Three of these — C6, C7 and E3 — could each change whether HYP-01 is reported as
   significant**", line 165), deadline `BEFORE_PREREG_AND_FIRST_OBSERVATION`.
2. `GST_HYP01_ANALYSIS_LOCK_AMENDMENT_2026-08-16.json` (dated 2026-08-16, authorised
   2026-08-16T03:57:18Z) selects **CR2** as the primary covariance estimator (D1), **BRL built into
   clubSandwich CR2** as the finite-sample correction (D2), and **coefficient-specific Satterthwaite**
   as the reference distribution (D3), and states the wild cluster bootstrap plays no role (D4).
3. The amendment, its markdown companion, and `GST_HYP01_METHOD_AUTHORIZATION_2026-08-16.md`
   **never mention `C6` or `C7`**. Verified by identifier-bounded grep across all three.
4. The gap audit has **not been re-issued** since 2026-08-09.

**Interpretation, marked as such.** The 2026-08-16 amendment appears to settle the *substance* of both
C6 (estimator variant) and C7 (finite-sample correction and inference procedure). But no committed
artifact *closes the register entries*, and the gap audit's own rule for such closure is a dated
instrument. Treating C6/C7 as closed would therefore require inferring closure from topical overlap —
which is precisely the inference this reconciliation is instructed not to make.

**Recorded status: C6 and C7 are `SUBSTANTIVELY_RESOLVED` and `ADMINISTRATIVELY_OPEN`.** The
scientific content is specified by the dated 2026-08-16 instrument; the register entries are not
closed by any artifact that names them. Closing them requires a dated erratum or gap-audit v1.1
naming C6 and C7 and citing the 2026-08-16 decisions. A draft is prepared at
`C6_C7_GAP_AUDIT_ERRATUM_DRAFT.md`; signing it is a human authoring action and is **not performed
here**, and that draft makes no new inference decision.
