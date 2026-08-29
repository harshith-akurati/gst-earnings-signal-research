# E8 — development / confirmatory-cohort boundary

**Status:** `DRAFT_UNSIGNED`. Not adopted, not in force.
**Authored:** 2026-08-29, before any eligible HYP-01 event or outcome exists (eligible count **0**).
**Closes:** gap-audit row **E8** — *"no dated document states which retrospective artifacts may inform
development without contaminating the confirmatory cohort. Currently implicit."*

> The audit flagged that writing this down *"may reveal that a past choice was informed by data now
> inside the cohort."* That risk is why the boundary is stated before collection, not after.

---

## 1. What the boundary is for

The confirmatory claim rests on the primary model being fixed **before** anyone sees the data it will
be run on. Development work — building code, choosing queries, screening candidates — is legitimate
and necessary. It becomes contamination the moment it is informed by an outcome that later sits inside
the confirmatory cohort.

This document draws the line explicitly so it stops being implicit.

## 2. Permitted development material

| # | Material | Condition |
|---|---|---|
| P-1 | **Synthetic fixtures** | Any quantity, any time. Every PR #40 test uses these exclusively. |
| P-2 | **External literature** | Published work not derived from this project's prospective data. |
| P-3 | **Repository code** | Any commit; code is an implementation of a decision, never where a decision is made. |
| P-4 | **Retrospective artifacts dated before activation** | Only those already committed and dated **before** the pipeline is activated. Their use must be cited when it informs a choice. |
| P-5 | **A separately declared F5 construct-validation study** | **Search data only.** No market outcome, return, price or earnings-response comparison of any kind. Must be declared development-only in advance (§4). |

## 3. Prohibited development material

| # | Material | Why |
|---|---|---|
| X-1 | **Any HYP-01 prospective outcome** | It is the thing being tested. |
| X-2 | **Any effect estimate, direction, plot, interim pattern or p-value from the prospective cohort** | Seeing the answer before fixing the question is the failure the whole design prevents. |
| X-3 | **Selecting a query because it better predicts an earnings response** | This is the sharpest prohibition. It would make the predictor a function of the outcome, and no amount of later blinding repairs it. |
| X-4 | **Using an event later included in the confirmatory cohort to tune measurement based on its outcome** | Contaminates that event and, through the shared query mapping, every other event. |

**X-3 restated, because it is the one most likely to happen by accident:** a query may be chosen for
issuer specificity, coverage, stability or lexical clarity. It may **never** be chosen, ranked,
shortlisted or defended on the grounds that it correlates better with any market response.

## 4. Labelling rule for F5 validation series

Any Google Trends series pulled for F5 construct validation:

1. **must be labelled `DEVELOPMENT_ONLY` at the moment of retrieval**, in the artifact that stores it;
2. **must be excluded from confirmatory observations** — it is never reused as, or merged into, a
   cohort event's pre-event snapshot;
3. must be drawn from a **fixed historical interval declared before any pull** (see the F5 protocol);
4. must be retained, including every rejected candidate, so the selection is auditable.

A development-only series and a confirmatory observation are different artifacts even when the query
string and ticker are identical. **They must never be interchanged.**

## 5. What this does not do

- It does not close F5. It states what an F5 study may and may not use.
- It changes no statistical rule, gate, threshold or timing window.
- It authorizes no collection, enrollment, analysis or activation.
- It makes no claim that past choices were or were not contaminated. **Auditing that is a separate
  exercise**, and this document's adoption is the natural moment for a reviewer to perform it.

## 6. Signatures

| Field | Entry |
|---|---|
| Approver 1 name · signature · timestamp | `____________` |
| Approver 2 name · signature · timestamp | `____________` |
| Effective from | `____________` |
| Confirm: adoption is prospective and reclassifies no earlier work | `____________` |
| Confirm: a retrospective review of past choices against §3 has been performed, or is scheduled | `____________` |
