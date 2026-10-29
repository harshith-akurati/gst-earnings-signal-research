# OSF preregistration — HYP-01 — DRAFT, NOT SUBMITTED

**Status:** `DRAFT_UNSIGNED_NOT_SUBMITTED`. **This has not been submitted to OSF or any registry.**
**Prepared:** 2026-08-29, while eligible events = **0**, collection = **BLOCKED**, results = **none**.

> Completing an internal lock does **not** make a study preregistered. Preregistration requires actual
> submission to an external timestamped registry. **That has not happened.**
> **Do not submit while F5 is open** — see §12.

---

## 1. Title

Prospective test of whether abnormal pre-earnings Google-search attention is associated with a larger
absolute overnight earnings response.

## 2. Authors and contributions

| Field | Entry |
|---|---|
| Author 1 (name, affiliation, ORCID) | `____________` |
| Author 2 (name, affiliation, ORCID) | `____________` |
| Named analysis authorizer (gap-audit E9) | `____________` |
| Qualified F5 construct-validity reviewer | `____________` |

## 3. Hypothesis

**HYP-01.** Does higher abnormal pre-earnings Google-search attention associate with a greater
absolute overnight earnings response?

This is an **association** hypothesis. It is not a causal claim, not a forecasting claim, and not a
tradability claim.

## 4. Design

Prospective observational cohort. Each event contributes one pre-event attention observation and one
post-event market-response observation. No treatment is assigned; nothing is traded.

## 5. Sample

| | |
|---|---|
| Universe | 24 tickers, `Event_Dossier_Protocol/locked_universe_v0.1.json` (`date_locked: 2026-08-02`) |
| Events | regular quarterly/annual earnings announcements of those issuers |
| Target n | **60 eligible events** |
| Nature of n | **A governance eligibility floor, explicitly NOT a demonstrated power target** (adopted D16) |
| Collection window | pre-event anchor within 2026-09-01 → 2027-05-31 (pending cohort-protocol adoption) |

**Tickers:** AAPL, ABBV, ADBE, AMZN, BKR, BRK-B, CTSH, DELL, DVN, GME, GOOGL, GPN, INTC, LDOS, MSFT,
NCLH, NKE, QCOM, SBUX, STZ, SYK, TSLA, TTWO, UAL.

## 6. Variables

| Role | Variable | Definition |
|---|---|---|
| **Predictor** | `gst_zscore` | Abnormal Google-search attention at the mechanically derived pre-event anchor session. **Continuous, natural scale, unthresholded.** No data-driven cutoff, winsorization or outcome-informed transform. |
| **Outcome** | `abs_overnight_gap` | `abs(next_session_open / previous_close − 1)` for the registered response session. |

**The exact query string per ticker is pending F5 resolution (§12) and must be fixed before the first
observation.**

## 7. Eligibility — S-1…S-8, applied in order

1. enrolled under the adopted cohort protocol · 2. eligible for `core_attention_vs_equity_response` ·
3. strict v0.2 six-field core passed · 4. D1 capture passed · 5. `gst_zscore` non-null with successful
GST provenance · 6. `abs_overnight_gap` non-null with valid market-data provenance · 7. release
session ∈ {BMO, AMC} · 8. among the first 60 in the deterministic order.

**Ordering:** `(response_session_date ASC, event_id ASC)` — fixed before any event exists, reading no
observed value.

## 8. Analysis plan — already locked and adopted

```
abs_overnight_gap ~ gst_zscore        OLS, single RHS term, no covariates
```

| Element | Value | Source |
|---|---|---|
| Covariance | cluster-robust on `ticker`, **CR2 bias-reduced linearization** | adopted **D1** |
| Correction | **BRL only** — no CR1 scaling, no second correction | adopted **D2** |
| Inference | **coefficient-specific Satterthwaite** df, realized df reported | adopted **D3** |
| Bootstrap | **not used** | adopted **D4** |
| α, sidedness | **0.05, two-sided** | adopted lock |
| Multiplicity | **no adjustment** — family = 1 predictor / 1 outcome / 1 test | adopted **D15** |
| Singletons | retained; counts and realized df reported | adopted **D8** |
| Official path | R 4.6.1 + clubSandwich 0.7.0; Python is a validated cross-check, **not authoritative** | adopted **D1**, **D11** |

**Implementation validation is not scientific proof.** PR #18 showed the study's code agrees with
clubSandwich on synthetic fixtures — implementation agreement, not evidence that CR2 is the correct
estimator for this question.

## 9. Missing data

No imputation, no zero-fill, no winsorization, no outlier deletion. A provider or schema failure is a
**documented missing observation**; a retrieval failure is never recorded as issuer-confirmed absence
(adopted D4 / gap-audit D4).

## 10. Stopping, freezing and display

- **No optional stopping.** Collection is neither stopped early nor extended because of results.
- **Freeze at 60:** freeze the 60 event IDs → freeze the environment (D11) → re-verify all gates →
  run the model **once**.
- **Extension cohort:** events becoming eligible after the freeze are separately labelled, never
  enlarge the frozen 60, and never re-open the primary analysis.
- **Before the freeze**, only the eligible-event count, per-event disposition and unique-ticker count
  may be displayed. Effect estimate, direction, plot, interim p-value and confidence interval are
  **prohibited**.

## 11. Power and equivalence

**No power or design-sensitivity analysis has been performed. No SESOI is registered. No equivalence
test is authorized** (recommended A9 decision, unsigned).

**Consequences, disclosed rather than minimised:** the study cannot claim to be adequately powered,
and **a null result will be uninformative about small effects and must never be described as
establishing equivalence or absence of effect.**

## 12. Known open items at drafting

| Item | State |
|---|---|
| **F5 search-construct validity** | **OPEN.** The exact query per ticker is unresolved; the offline lexical screen explicitly cannot close it. **Submission should wait**, since the predictor's operational definition is not yet fixed. |
| E8 development/confirmatory boundary | drafted, unsigned |
| Cohort protocol adoption + S-1 reference | drafted, unsigned |
| Collection-gate circularity correction | drafted, unsigned |
| D1 latest-capture rule | recommended, unsigned |
| E9 named analysis authorizer | unassigned |
| C6 / C7 / E3 | substantively discharged by D1/D2/D3/D15; mapping record unsigned |

## 13. Development / confirmatory boundary

Permitted development material: synthetic fixtures; external literature; repository code and
retrospective artifacts dated before activation; a declared F5 study using **search data only**.

Prohibited: any HYP-01 prospective outcome; any effect estimate, direction, plot or interim pattern
from the cohort; **selecting a query because it better predicts an earnings response**; tuning
measurement on a cohort event's outcome.

## 14. Prior work and its status

Retrospective analyses exist and are **development material only**. Their point-in-time check
**failed**, and no policy yet governs external citation of reconstructed retrospective figures
(gap-audit B3). **No retrospective result is offered as evidence for HYP-01.**

## 15. Timeline

| Milestone | Date |
|---|---|
| Analysis rules authorized | 2026-08-16 |
| Eligible events at drafting | **0** |
| F5 resolution | `____________` |
| External preregistration submitted | `____________` (**not submitted**) |
| First pre-event observation | `____________` |

## 16. Submission sign-off

| Field | Entry |
|---|---|
| Author 1 · signature · timestamp | `____________` |
| Author 2 · signature · timestamp | `____________` |
| Confirm: F5 resolved and the query mapping fixed | `____________` |
| Confirm: zero prospective observations collected at submission | `____________` |
| Confirm: no outcome, estimate or direction has been inspected | `____________` |
| Registry and submission timestamp | `____________` |
