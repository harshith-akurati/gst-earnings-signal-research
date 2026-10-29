# F5 — outcome-blind construct-validation protocol

**Status:** `DRAFT_UNSIGNED`. **F5 is OPEN and this document does not close it.**
**Authored:** 2026-08-29, while eligible events = **0** and collection = **BLOCKED**.

> This is a bounded work plan for a **qualified human reviewer**. It prescribes what must be done,
> what may never be done, and what must be recorded. It selects no query and ranks no candidate.

---

## 1. What F5 asks

`PREREGISTRATION_GAP_AUDIT_v1.0.md` row **F5**, `SCIENTIFIC_DECISION`, deadline
`BEFORE_FIRST_OBSERVATION`:

> *"no documented ticker→query mapping justification; homonym/ambiguity risk unreviewed (e.g. `GME`,
> `STZ`, `BKR`); Trends' own revision behaviour undocumented"* — and *"a query-term change changes the
> signal."*

Production currently uses the **bare ticker as the query** for all 24 issuers: no mapping layer
exists (`GST_SEARCH_CONSTRUCT_INVENTORY_v1.0.csv`, `constant_or_mapping_entry` = *"TICKERS (no
mapping; the ticker IS the query)"*).

## 2. Why the existing audit cannot close it

`GST_SEARCH_CONSTRUCT_VALIDITY_AUDIT_v1.0.json` records `gap_audit_status_after_this_work:
STILL_OPEN`, describes itself as *"an offline lexical screen, not a construct-validity finding"*, and
lists **"closing gap-audit item F5"** among its `prohibited_uses_of_this_document`. It made **zero**
live Trends calls. It is a starting inventory, not a validation.

## 3. Scope — all 24, with 11 mandatory empirical comparisons

**Every one of the 24 locked tickers must be assessed.** The inventory already marks all 24
`human_review_required: YES`.

**Empirical comparison is MANDATORY for the 11 marked `REQUIRED`:**

> **BKR · BRK-B · DELL · DVN · GME · GOOGL · GPN · NKE · STZ · SYK · UAL**

Empirical comparison is **RECOMMENDED** for the remaining 13: AAPL, ABBV, ADBE, AMZN, CTSH, INTC,
LDOS, MSFT, NCLH, QCOM, SBUX, TSLA, TTWO. A reviewer who skips any of the 13 must record why.

Ambiguity as screened: 3 `HIGH`, 8 `MODERATE`, 13 `LOW`. **A `LOW_LEXICAL_AMBIGUITY` label is not
evidence of construct validity** — the audit prohibits reading it that way.

## 4. Candidate-query families — identical set for every ticker

The inventory already carries six columns. The same six families are evaluated for each ticker, so
the comparison is symmetric:

| # | Family | Example form |
|---|---|---|
| 1 | Current production | bare ticker |
| 2 | Official company name | *Apple Inc.* |
| 3 | Ticker + stock | *AAPL stock* |
| 4 | Company + earnings | *Apple Inc. earnings* |
| 5 | Google topic / entity | the Freebase-style topic where one exists |
| 6 | Issuer-specific alternative | reviewer-proposed, justified in writing |

## 5. Fixed development-only interval — declared before any pull

| Field | Entry (declare **before** the first call) |
|---|---|
| Interval start | `____________` |
| Interval end | `____________` |
| Geography | `____________` |
| Category | `____________` |
| Search property | `____________` |

**Constraints.** The interval must end **before** the collection window opens (2026-09-01), must be
identical for every ticker and every candidate, and must be **declared before any comparison call**.
It may not be adjusted after seeing any result.

**Every series pulled is labelled `DEVELOPMENT_ONLY` at retrieval** and is excluded from confirmatory
observations, per the E8 boundary artifact.

## 6. Prohibitions — absolute

| # | Prohibited |
|---|---|
| **F5-X1** | Any market price, return, volatility or volume comparison |
| **F5-X2** | Any earnings-response or event-study comparison |
| **F5-X3** | Any HYP-01 prospective outcome, or any event inside the confirmatory cohort |
| **F5-X4** | **Selecting or ranking a query because it correlates better with any market response** |
| **F5-X5** | Any effect estimate, direction or plot derived from cohort data |

**F5-X4 is the one most likely to happen by accident.** A query may be chosen for issuer specificity,
coverage, stability or lexical clarity. It may **never** be chosen, shortlisted or defended on
predictive grounds. Doing so makes the predictor a function of the outcome, and no later blinding
repairs it.

## 7. Dimensions to evaluate — all six, every ticker

| # | Dimension | Question |
|---|---|---|
| D-1 | **Issuer specificity** | Does the query retrieve interest in *this issuer*, or something else? |
| D-2 | **Lexical collision** | Does it collide with an ordinary word, brand or unrelated entity? (`DELL` is a dictionary word and consumer brand; `GME`, `STZ`, `BKR` were flagged.) |
| D-3 | **Coverage / sparsity** | Does the series return usable data, or sparse/zero values the z-score cannot handle? |
| D-4 | **Punctuation behaviour** | How are `BRK-B`, `BRK.B`, spaces and casing handled by the endpoint? |
| D-5 | **Google topic availability** | Does a topic/entity exist, and does it behave differently from the free-text query? |
| D-6 | **Repeat-pull revision behaviour** | Pull the same query and interval on **at least two separate days**. Record whether values change. Trends revision behaviour is undocumented and is itself part of F5. |

## 8. Selection criteria — predeclared, before any comparison call

**Fill this in and date it BEFORE the first pull. Criteria fixed afterwards are not predeclared.**

| Field | Entry |
|---|---|
| Criteria, in priority order | `____________` |
| How D-1…D-6 are weighed against each other | `____________` |
| Tie-breaking rule | `____________` |
| Threshold for "unusable" (e.g. sparsity) | `____________` |
| Predeclaration date · reviewer signature | `____________` |

## 9. Historical series if the query changes

If any query changes, the reviewer must state which applies:

| Option | Consequence |
|---|---|
| **H-1** Re-pull all historical series under the new query | Consistent construct; historical values change |
| **H-2** Keep bare-ticker history, use the new query prospectively | **Predictor is not comparable across the boundary** — must be disclosed and justified |
| **H-3** Restrict all analysis to the prospective window | Cleanest; discards historical comparability |

The inventory records `same_query_historical_and_prospective: YES` today. **A change breaks that, and
the break must be recorded, not absorbed silently.**

| Field | Entry |
|---|---|
| Option chosen | `____________` |
| Justification | `____________` |

## 10. One systematic rule, or documented per-ticker justification

Preferred: **one systematic rule** applied to all 24 (e.g. "official company name for every issuer").

If any ticker deviates, that ticker needs its **own written justification** naming the dimension that
forced it. **Ad-hoc per-ticker choices without a stated reason are not acceptable** — they are how a
mapping becomes unfalsifiable.

| Field | Entry |
|---|---|
| Systematic rule adopted | `____________` |
| Tickers deviating, with per-ticker justification | `____________` |

## 11. Preservation

Every candidate, including **rejected** ones, and every pulled series must be retained with: ticker ·
query string · family · interval · pull timestamp · raw result · `DEVELOPMENT_ONLY` label · the
decision and its reason. **Nothing is discarded because it lost.**

## 12. Who may serve as reviewer

**Required expertise:** search behaviour, information retrieval, marketing analytics, or a related
methodological field — someone who can judge whether a query measures the intended construct.

| | |
|---|---|
| Reviewer name | `____________` |
| Affiliation | `____________` |
| Relevant expertise | `____________` |
| Declaration of independence | `____________` |

**Explicitly disqualified, individually or together:**

- **Claude** (Anthropic) — the existing audit records its own author as *"Not a search-methodology
  authority"*
- **Codex** or any other automated assistant
- **The project author alone** — the analysis side cannot validate its own construct

At least one qualified **independent human** must sign. An assistant may prepare materials; it may not
be the reviewer.

## 13. Deliverable

A dated artifact recording: the predeclared criteria; every candidate and result; the systematic rule
or per-ticker justifications; the historical-series decision; the revision-behaviour finding; and an
explicit statement of whether F5 is closed.

**Only that artifact, signed by a qualified reviewer, can move F5 from OPEN.** This protocol cannot,
and the offline lexical screen cannot.

| Field | Entry |
|---|---|
| Reviewer signature · date | `____________` |
| F5 status after this work: **CLOSED / STILL_OPEN** | `____________` |
| Second approver (project side) · date | `____________` |
