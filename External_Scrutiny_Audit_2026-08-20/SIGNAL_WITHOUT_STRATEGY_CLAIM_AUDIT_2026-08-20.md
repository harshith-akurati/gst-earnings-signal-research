# Claim-by-claim audit: *Signal Without Strategy* v1.0

**Date:** 2026-08-20
**Audited file:** `SIGNAL_WITHOUT_STRATEGY_MANUSCRIPT_v1.0.md` (579 lines), branch
`phase5-signal-without-strategy-submission-package`
**Standard applied:** this project's own — a result referenced in text must trace to an actual
committed results file.
**Status:** FLAGGING ONLY. No manuscript text was edited.

---

## 1. Headline outcome

**The paper passes its own standard.** Every numeric research claim in the manuscript traces to a
committed file. Four issues are flagged below, none of which is a fabricated or unsupported number;
they concern *provenance tier* and *repository self-containment*, not truth.

Two independent checks were run:

1. **The repository's own auditor**, `tools/check_signal_without_strategy_numbers.py` (545 lines),
   executed 2026-08-20. Result: `NUMERICAL AUDIT PASSED` — 82 claimed values resolved against
   committed artifacts; all 139 distinct numeric tokens in the manuscript accounted for (82 claims,
   71 allowlisted); no claim shadowed by the allowlist; required disclaimers present; the significant
   association explicitly not described as a null; the replication correctly described as having
   failed its gate.
2. **An independent re-verification for this audit**, reading each headline number directly out of
   the JSON artifacts rather than trusting the auditor. Results in section 3.

The paper also declares its own provenance in a **Source artifacts** section listing 11 files.
**All 11 exist.**

---

## 2. Existence check of declared source artifacts

| # | Declared artifact | Present |
|---|---|---|
| 1 | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | YES |
| 2 | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | YES |
| 3 | `RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md` | YES |
| 4 | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | YES |
| 5 | `RESTAURANT_SEARCH_PILOT_RESULTS_v1.0.json` | YES |
| 6 | `SEARCH_DEMAND_NOWCAST_RESULTS_v1.0.json` | YES |
| 7 | `ATTENTION_ACTIVITY_MISMATCH_RESULTS_v1.0.json` | YES (see Finding B) |
| 8 | `SEMICONDUCTOR_EPS_ABSORPTION_RESULTS_v1.0.json` | YES |
| 9 | `Live Signal Engine/Semiconductor_EPS_Absorption/structured_earnings_feasibility_v1.0.json` | YES |
| 10 | `SEMICONDUCTOR_SURPRISE_ABSORPTION_V3_RESULTS_v1.0.json` | YES |
| 11 | `SEMICONDUCTOR_SURPRISE_TEMPORAL_REPLICATION_RESULTS_v1.0.json` | YES |

---

## 3. Claim-by-claim table

`ARTIFACT` = resolves to a machine-generated results JSON. `REPORT` = resolves to committed prose in
a markdown report, not to a results JSON. `DERIVED` = arithmetic on artifact values.

| # | Section | Claim | Source file | Verified |
|---|---|---|---|---|
| 1 | 1, 5.1, 9, 12 | Standalone event strategy mean net return **0.8543%** per event | `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 2 | 1, 5.1, 9, 12 | Incremental attention contribution **+0.0131 pp** | same | VERIFIED (ARTIFACT) |
| 3 | 1, 5.1, 9, 12 | **p = 0.98332** on that contribution | same | VERIFIED (ARTIFACT) |
| 4 | 1, 5.2, 9 | Intercept-only baseline Brier **0.2560** | `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 5 | 1, 5.2, 9 | Logistic model Brier **0.2711** | same | VERIFIED (ARTIFACT) |
| 6 | 5.2, 6, 9 | Post-correction AUC **0.4654** | same | VERIFIED (ARTIFACT) |
| 7 | 6, 12 | Post-correction accuracy **47.9%** | same | VERIFIED (ARTIFACT) |
| 8 | 6 | Always-positive benchmark **53.5%** | same | VERIFIED (ARTIFACT) |
| 9 | 6, 9 | Direction-only strategy net **−0.7027%** | same | VERIFIED (ARTIFACT) |
| 10 | 6 | **68** duplicated rows among **285**, leaving **217** unique | same | VERIFIED (ARTIFACT) |
| 11 | 1, 6, 12 | Pre-correction accuracy **63.6%** | `RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md` line 144 | VERIFIED (REPORT) — **Finding A** |
| 12 | 6 | Pre-correction AUC **0.6395** | same, line 144 | VERIFIED (REPORT) — **Finding A** |
| 13 | 6 | Pre-correction Brier **0.23824** | same, line 144 | VERIFIED (REPORT) — **Finding A** |
| 14 | 1, 5.3, 9 | Magnitude MAE **3.6299** with vs **3.6284** without | `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 15 | 1, 5.3, 9 | Paired **p = 0.9827** | same | VERIFIED (ARTIFACT) |
| 16 | 5.4, 9 | Weekly volatility MAE change **−0.0309%**; baseline **0.420367** vs **0.420497**; interval **[−0.0011023, +0.0010839]** | `ATTENTION_ACTIVITY_MISMATCH_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) — **Finding B** |
| 17 | 5.5, 9 | Restaurant pooled Brier **0.20211 → 0.23665 → 0.24739** | `RESTAURANT_SEARCH_PILOT_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 18 | 5.5 | Restaurant MAE **5.4534 → 5.6790 → 5.8543** pp | same | VERIFIED (ARTIFACT) |
| 19 | 5.5, 9 | Decision label `NO_INCREMENTAL_SEARCH_VALUE` | same | VERIFIED (ARTIFACT) |
| 20 | 5.6 | Nowcast terminated at `INSUFFICIENT_DATA` | `SEARCH_DEMAND_NOWCAST_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 21 | 4.4 | **139** overlapping events, only **8** matched within $0.01, match rate **0.0576**, median abs diff **$0.26** | `structured_earnings_feasibility_v1.0.json` | VERIFIED (ARTIFACT) |
| 22 | 4.4 | **320** in-window vendor records, ratio invariant to proportional restatement | same | VERIFIED (ARTIFACT) |
| 23 | 7 | Held-out conditional precision **0.9860**, combined **0.9868** | `SEMICONDUCTOR_EPS_ABSORPTION_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 24 | 7 | Verified reference coverage **0.7037** vs required 0.80; usable-event coverage **0.2742** vs 0.60 | same | VERIFIED (ARTIFACT) |
| 25 | 7 | **216** extractions, **47** fiscal-year-end quarters, cap **0.7824** | same | VERIFIED (ARTIFACT) |
| 26 | 7 | Crosswalk gate failed at **0.6719** vs 0.90; **267** of **306** SEC events carried a parsed fiscal period; cap **0.8344** | `structured_earnings_feasibility_v1.0.json` | VERIFIED (ARTIFACT) |
| 27 | 8.1, 9 | 2023–2025: **298** matched events, **116** OOS | `SEMICONDUCTOR_SURPRISE_ABSORPTION_V3_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 28 | 8.1 | MAE **0.052506** baseline vs **0.051203** augmented; improvement **+2.482%** | same | VERIFIED (ARTIFACT) |
| 29 | 8.1, 9 | Spearman **+0.13515**, **p = 0.148026** | same | VERIFIED (ARTIFACT) |
| 30 | 8.1 | Bootstrap interval **[−0.0007272, +0.0031700]** | same | VERIFIED (ARTIFACT) |
| 31 | 8.2, 9 | 2010–2017: **462** matched, **283** OOS | `SEMICONDUCTOR_SURPRISE_TEMPORAL_REPLICATION_RESULTS_v1.0.json` | VERIFIED (ARTIFACT) |
| 32 | 8.2 | MAE **0.044226** vs **0.043246**; improvement **+2.216%** | same | VERIFIED (ARTIFACT) |
| 33 | 1, 8.2, 8.3, 9, 12 | Spearman **+0.2169**, **p = 0.000236** | same | VERIFIED (ARTIFACT) |
| 34 | 8.2 | Interval **[−0.0000561, +0.0021342]** | same | VERIFIED (ARTIFACT) |
| 35 | 8.2, 8.3, 12 | **5 of 8** years, **4 of 9** firms, **all 9** firms positive Spearman | same | VERIFIED (ARTIFACT) |
| 36 | 4.7, 11 | HYP-01 "specified but never ran, contributes no evidence" | `Live Signal Engine/GST_HYP01_*` lock and authorization files | VERIFIED (REPORT) |
| 37 | 1 | "Abstract: 231 words" | self-referential; countable from the text | DERIVED |

**No claim in the manuscript was found to be unsupported by a committed file.**

---

## 4. Findings

### Finding A — three numbers rest on committed prose, not on a results artifact (LOW)

The pre-correction leakage figures — accuracy **63.6%**, AUC **0.6395**, Brier **0.23824** — appear in
the abstract, section 6 and the conclusion. They resolve to line 144 of
`RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md` and to `CHANGELOG.md` line 666. They do **not** appear
in `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` or any other results JSON.

This is defensible and probably unavoidable: the run that produced them was invalidated by the very
defect the section documents, so there is no valid results artifact to point at, and re-generating one
would mean re-running a knowingly leaky pipeline. The repository's auditor knows this and labels them
"pre-correction ... (invalidated)".

It is still a weaker provenance tier than every other number in the paper, and these three numbers
carry real rhetorical weight — they are the "before" half of the paper's most quotable comparison.

*Suggested (not applied):* one sentence in section 6 noting that the pre-correction figures are
preserved as a committed record of the invalidated run rather than as a reproducible artifact.

### Finding B — one source artifact lives on an unmerged branch (MEDIUM, repository hygiene)

Section 5.4's weekly-volatility numbers resolve to `ATTENTION_ACTIVITY_MISMATCH_RESULTS_v1.0.json`.
The manuscript's own Source artifacts list flags this, annotating it
"(branch `phase2-attention-activity-mismatch`)".

The auditor confirms the artifact's content hash but emits a standing note:

> "PR #30 (phase2-attention-activity-mismatch) must merge before PR #36 for main to be
> self-contained. PR #36 alone does not contain this source artifact."

**Consequence for external scrutiny:** if the paper is submitted and a reviewer clones `main`, section
5.4 is unverifiable until PR #30 merges. This is the single most likely way an outside reader hits a
dead reference. It is a merge-ordering task, not a research defect.

### Finding C — "hundreds of automated tests" does not appear in the paper (NO ACTION)

The phrase was searched for in the manuscript, the executive summary, and every markdown file across
the submission, synthesis and main trees. **It appears nowhere.** If it is being used in an external
description of the project, it is not sourced from the paper.

**Had the claim been made, it would be true.** Counted on the submission branch:

| Measure | Count |
|---|---|
| Test files (`test_*.py`) | **55** |
| Test functions (`def test_*`) | **537** |
| `check(...)` assertions | **2,849** |
| CI workflows | **3** |

The suite is standalone-runnable (`python test_x.py`; no pytest dependency — pytest is in fact not
installed in this environment). Two files were executed as a spot check on 2026-08-20:
`test_market_response_absolute_persistence.py` and `test_market_response_search_demand_nowcast.py`.
Both printed `ALL ... PASSED`. The tests install socket-level network blockers before importing
project modules, so they are deterministic and offline.

"Hundreds of automated tests" is therefore an accurate and conservative description of 537.

### Finding D — "numerous classical ML models" does not appear in the paper, and would overclaim (NO ACTION IN PAPER)

Also searched for across all three trees. **It appears nowhere in the paper or the repository.**

**Had the claim been made, it would be an overstatement.** The complete inventory of learned models
actually fitted and reported anywhere in the program:

| Model | Where | Role |
|---|---|---|
| `Ridge(alpha=1.0)` | magnitude forecast, volatility | fixed, no hyperparameter search |
| `LogisticRegression` (L2) — `logistic_l2` | direction study | candidate |
| `GradientBoostingClassifier(max_depth=2)` — `gbt_shallow` | direction study | candidate |
| OLS | H16 exploratory | in-sample only |

Plus three non-learned benchmarks in the direction study: `always_positive`,
`intercept_only_prevalence`, `momentum_sign`.

That is **three learned model families plus OLS** — deliberately minimal. The manuscript is explicit
that this is a design choice (section 4.5: "ridge(alpha=1.0), fixed; no model, threshold or
hyperparameter search"), and section 10 makes the restraint a *finding*: "An intercept-only
probability forecast beat a fitted logistic model."

Scanning for `RandomForest`, `XGBoost`, `LGBM`, `SVR`, `MLPRegressor` and `CatBoost` returns hits in
exactly two places — **tests that assert these models are NOT used**:

- `test_market_response_search_demand_nowcast.py:81`
- `test_market_response_semiconductor_surprise_temporal_replication.py:111`

So the repository actively enforces model minimalism. Describing the program as using "numerous
classical ML models" would contradict both the code and the paper's own argument, and would invite a
reviewer to ask which models and find only three. **Recommend this phrasing be dropped from any
external description.** The stronger and true claim is the opposite: *a deliberately minimal, frozen
model set, because the baselines were the point.*

---

## 5. Bottom line

| Item | Status |
|---|---|
| Numeric claims traceable to committed files | **37 of 37** |
| Declared source artifacts present | **11 of 11** |
| Repository's own numerical audit | **PASSED** |
| Claims resting on prose rather than a results JSON | 3 (Finding A) |
| Claims dependent on an unmerged branch | 1 group (Finding B) |
| "hundreds of automated tests" | not in the paper; **would be true** (537) |
| "numerous classical ML models" | not in the paper; **would be an overclaim** (3 + OLS) |

The only action genuinely worth taking before external submission is **Finding B**: merge PR #30
before PR #36 so that `main` is self-contained.
