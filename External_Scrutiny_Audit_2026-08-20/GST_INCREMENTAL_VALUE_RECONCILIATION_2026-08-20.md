# Reconciliation: the two GST "incremental value" results

**Date:** 2026-08-20
**Status:** DOCUMENTATION ONLY. Neither original result is edited, retracted or recomputed by this
file. This document describes the *relationship* between two existing results.
**Scope:** does not touch any frozen study rule, locked pre-registration, or the manuscript text.

---

## 1. The apparent contradiction

Two results in this project's record appear to disagree about whether Google Search Trends (GST)
adds incremental predictive value.

| | Result A | Result B |
|---|---|---|
| Short form | GST adds nothing | GST adds a lot |
| Headline | MAE 3.6284 without GST vs 3.6299 with; paired p = 0.9827 | R-squared 0.1538 to 0.2291 (+0.0753); GST coefficient +0.3968, t = 3.337, p = 0.0011 |
| Where it appears | *Signal Without Strategy* section 5.3 and section 9 | commit `4e2ed62`, 2026-07-26 |

Both were re-derived from their committed source files for this document. **Both reproduce exactly.**
Neither is a transcription error and neither is fabricated.

---

## 2. Source files located

### Result A — retrospective magnitude forecast

- Script: `tools/run_retrospective_magnitude_forecast.py`
- Result artifact: `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json`
- Branch: `phase2-retrospective-magnitude-forecast-development`; carried into the submission-package
  branch `phase5-signal-without-strategy-submission-package`.
- Reproduction: values read directly from the committed JSON.

### Result B — H16 exploratory regression

- Pre-registration: `Live Signal Engine/H16_Exploratory_PreRegistration.md` (written before the run)
- Script: `GST_H16_Exploratory_Analysis.py` (added in `4e2ed62`)
- Data: `Live Signal Engine/H16_Exploratory_Analysis_Data.csv` (125 rows, committed with the script)
- Reproduction: the OLS was re-run from the committed CSV on 2026-08-20 and returned
  R-squared base 0.1538, full 0.2291, incremental 0.0753, GST coefficient +0.3968, t = 3.337,
  p = 0.0011, n = 125, 24 tickers, spike weeks 2021-03-21 to 2025-12-07 — matching the commit
  message to every reported digit.

---

## 3. Specification comparison

| | **A — magnitude forecast** | **B — H16** |
|---|---|---|
| **Dependent variable** | `abs(open(T) / close(T-1) - 1)` — absolute *overnight earnings gap*, a single price jump | `realized_move_pct` = abs(cumulative return, entry to exit) x 100 — absolute *4-day realized move* |
| **Outcome window** | close(T-1) to open(T) | entry = spike_week + 2d, exit = spike_week + 6d |
| **GST feature** | `gst_z_pre`: z of the latest weekly GST observation whose week **closes strictly before the event day**, against the prior 52 such weeks (min 20) | `fixed_window_zscore`: (GST of the **anchor week itself** minus mean of prior 12 weeks) / max(sd, 1.0) |
| **Population** | 217 unique earnings-event identities, 189 with complete features, **136 pooled OOS** | **125** GST-spike-selected near-earnings events, deduplicated by (ticker, spike_week) |
| **Selection** | all earnings events for the tickers, regardless of any search spike | events **conditioned on a GST spike** having occurred |
| **Period** | test folds 2023, 2024, 2025 | spike weeks 2021-03-21 to 2025-12-07 |
| **Model** | ridge(alpha = 1.0), fixed; no model/threshold/hyperparameter search | OLS |
| **Covariates** | `prior_mean_abs_gap`, `realized_vol_20d`, `abs_ret_5d`, `spy_vol_20d`, `is_amc` | straddle-cost IV proxy, log(market cap), sector fixed effects |
| **Validation** | **chronological expanding window**, transforms fitted inside the training fold only | **none — fully in-sample** |
| **Metric** | out-of-sample MAE; paired loss difference, CR2 clustered by ticker (26 clusters, Satterthwaite df) | in-sample incremental R-squared and the GST coefficient t-test |
| **Own stated status** | primary reportable result | "EXPLORATORY ONLY ... cannot be treated as confirmatory ... regardless of effect size or significance" |

---

## 4. Why they differ

They differ for **four independent reasons**, each sufficient on its own. They are not two answers to
one question.

### 4.1 Different questions: in-sample variance explained vs. out-of-sample incremental error

A measures whether adding GST **reduces forecast error on data the model never saw**. B measures
whether adding GST **raises R-squared on the same rows used to fit it**. In-sample R-squared is
non-decreasing when any regressor is added, and a t-test on that regressor asks only whether its
coefficient differs from zero within the fitted sample. Neither quantity constrains out-of-sample
MAE. This alone means the two results can both be true.

This is precisely the Level 1 / Level 2 distinction the manuscript sets out in section 3. B sits at
Level 1.

### 4.2 The GST features are not the same variable, and B's is contemporaneous with its own outcome

This is the decisive difference, and it is mechanical rather than interpretive.

`fixed_window_zscore` takes its **numerator from the anchor week's own GST value**
(`GST_FixedWindow_PerEvent_Canonical.py`, `compute_zscore_at_anchor`: the baseline mean and sd are
`.shift(1)`-ed to prior weeks, but the level term is `weekly["gst"]` **at the anchor**).

Google Trends weekly buckets begin on Sunday. **All 125 H16 anchor weeks are Sundays** (verified:
weekday value counts = {6: 125}). So the anchor week spans `[spike_week, spike_week + 6]`.

H16's outcome window is `[spike_week + 2, spike_week + 6]`.

> **The return window lies entirely inside the calendar week whose search volume forms the z-score
> numerator. Containment is 100%, for all 125 events.**

The H16 GST regressor is therefore measured **contemporaneously with** the return it is used to
explain; it aggregates search activity occurring *during* the move. That is a legitimate descriptive
association, and H16 never claims otherwise. It is not a forecast.

Result A's `gst_z_pre` is defined in the opposite way: the latest weekly observation whose week
**closes strictly before the event day**. Nothing in the numerator overlaps the outcome.

Crucially, the magnitude study **considered and explicitly rejected** the H16 family of feature. Its
result artifact records the reason verbatim, in a field named `why_not_population_spike_zscore`:

> "the population's spike z-score spans a 14-day window anchored at the spike week while the maximum
> anchor-to-event lead here is 5 days, so its window always overlaps the announcement; 9 of 217
> anchors fall on or after the event day. **It would be lookahead, so it is kept for reference only
> and never enters a model.**"

So this is not a contradiction discovered now. Study A already classified study B's regressor as
unusable for a forecasting claim, and documented that decision in the committed artifact.

A fair note in H16's favour: the canonical recompute was itself designed to remove a *different*
look-ahead defect (year-chunk rescaling against a future peak), and it succeeds at that. The pull
window never extends past `spike_week + 7`. The contemporaneity described here is a separate
property, and it does not make the canonical recompute wrong for its own purpose.

### 4.3 Different populations, and B conditions on the predictor

A uses every earnings event for its tickers. B uses only events **selected because GST spiked** — the
canonical population is built from (ticker, spike_week) candidates. Estimating the effect of GST on a
sample chosen for having high GST is a conditioned-on-the-regressor design; it restricts range and
changes what the coefficient means. B's own pre-registration states the population is "fully
saturated by every prior test in this project" with "no genuinely held-out data".

### 4.4 Different dependent variables

An overnight gap (A) and a 4-day cumulative move (B) are different quantities. A one-week search
aggregate has far more mechanical opportunity to co-move with a 4-day window sitting inside it than
with a single overnight jump that precedes it.

---

## 5. Verdict

**These two results measure genuinely different things. This is not a case where one number is wrong
and must be withdrawn.**

Stated plainly:

- **B is a valid in-sample, contemporaneous association** on a spike-selected population, using a
  search measure that overlaps its own outcome window. Read as what it is, the result is
  unsurprising: search volume during a week is associated with how much the stock moved that week.
- **A is a valid out-of-sample incremental prediction test** with a strictly pre-event feature, a
  strong price-and-calendar baseline, chronological validation and clustered inference.
- **They are compatible.** Both can hold simultaneously, and the project's own evidence ladder
  predicts exactly this pattern: Level 1 association present, Level 2 incremental prediction absent.

**If forced to rank methodology for the question "does GST add predictive value", A is decisively
stronger**, on five counts: out-of-sample rather than in-sample; a strictly pre-event feature rather
than a contemporaneous one; an unconditioned population rather than one selected on the predictor;
clustered inference rather than OLS t-statistics across repeated tickers; and a pre-specified strong
baseline rather than an unvalidated covariate set.

**B is not evidence against A, because B does not test prediction at all.**

---

## 6. Recommendation (not applied here)

No change is required to either artifact, and none is made. Two observations for external readers:

1. **The manuscript does not cite H16 and does not need to.** H16 is not in the paper's Source
   artifacts list, and no claim in the paper depends on it. There is no published contradiction to
   correct.
2. **The one live risk is quotation out of context.** "+0.0753 R-squared, p = 0.0011" is a
   quotable-looking number sitting in repository history under a commit message that opens
   "GST shows incremental R^2 on RV". A reviewer who finds that commit and not its pre-registration
   could reasonably believe it conflicts with the paper. This document exists so that the pairing is
   already answered in the record.

Both H16 files already carry prominent EXPLORATORY-ONLY language. That labelling is accurate and
should be left as it stands.
