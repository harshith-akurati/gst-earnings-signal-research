# Earnings Information Absorption Engine — MVP Result

`EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY` · **`google_trends_used: false`** · no GST artifact,
HYP-01 lock, F5 state, registry, protocol, production constant or prior result was touched.

> **Construct guard.** The measured quantity is an **information–price residual proxy**: a
> model-implied reaction fitted on historical data minus the observed reaction. It is **not**
> intrinsic value, fair value, mispricing, analyst surprise, or proof of underreaction. The numeric
> components are mechanical historical-expectation proxies, not analyst estimates.

## Decision

# `INFORMATION_FEATURES_DO_NOT_EXPLAIN_INITIAL_REACTION`

**Stage 1 failed.** The release-information features do not explain the market's first full-session
reaction, so the residual they generate has no established meaning — and Stage 2 was evaluated and
reported for completeness, not treated as a live test.

## Sample

| | |
|---|---|
| Tickers | **22** of the locked 24 (gate ≥ 18) |
| Unique events | **472** (gate ≥ 150) |
| Out-of-sample events | **261** (gate ≥ 100) |
| OOS by year | **2023: 86 · 2024: 88 · 2025: 87** (gate ≥ 25 each) |
| Duplicate identities refused | **0** |

Event identity `(ticker, fiscal_period_end, accession_number)`; duplicates are dropped outright, never
first-kept. Folds: train ≤2022 → test 2023; ≤2023 → 2024; ≤2024 → 2025.

## Stage 1 — do release features explain the initial reaction?

Target: reaction-session abnormal return (stock open→close minus SPY).

| Model | MAE | RMSE | OOS R² |
|---|---|---|---|
| Null (training mean + ticker indicators) | **0.025983** | — | — |
| Information model | 0.025970 | 0.038579 | **−0.06033** |

**Improvement: +0.050%** against a required **1.0%**. Block bootstrap (2,000 draws, 4-week calendar
blocks, fixed seed) on `null_loss − info_loss`: mean +1.30e-05, **95% CI [−9.04e-05, +1.13e-04]** —
straddles zero.

| Year | Null MAE | Info MAE | Info better |
|---|---|---|---|
| 2023 | 0.027064 | 0.027100 | no |
| 2024 | 0.027388 | 0.027338 | yes |
| 2025 | 0.023494 | 0.023470 | yes |

**Gates: ≥1% improvement FAIL (0.05%) · CI above zero FAIL · better in ≥2 of 3 years PASS.** One of
three. **Stage 1 does not pass.** Negative OOS R² means the information model predicts the reaction
worse than the sample mean.

Stage-1 coefficients (standardized, descriptive): `numeric_information_score` +0.000304,
`text_novelty` −0.000335, interaction +0.000993 — all near zero relative to a reaction whose typical
magnitude is ~2.6%.

## Stage 2 — reported for completeness, gated off

Because Stage 1 failed, the `information_price_gap` is a residual from a model with no demonstrated
explanatory power. These numbers are reported as required and must not be read as a live test.

**Primary, 5-day abnormal return (175 OOS events):**

| Model | MAE | RMSE | OOS R² | Spearman IC |
|---|---|---|---|---|
| B (market only) | 0.035650 | — | — | — |
| C (+ gap, + gap×novelty) | 0.035609 | 0.048865 | −0.26887 | **−0.0898** |

Improvement +0.115% (need 1%); bootstrap CI **[−1.07e-04, +1.68e-04]** straddles zero; C better in
1 of 2 evaluable years; **IC is negative**. All five gates fail.

**Secondary, 20-day (175 OOS events):** B 0.063420 vs C 0.064179 — **−1.196%, worse**; CI
[−0.001748, −1.92e-05] entirely *below* zero; IC **−0.0802**. All gates fail.

Gap coefficients: 5-day `information_price_gap` −0.002227 (sign-stable across folds),
`gap × novelty` +0.000250 (sign-stable); at 20 days neither is sign-stable. The negative sign and
negative IC point the opposite way from the drift hypothesis, but on a residual with no validated
first stage this is not interpretable as evidence of reversal.

**No trading test was run**, and no strategy is manufactured from a failed gate.

## Which link broke

**The information model failed, not the drift test.** The chain is: release information → explains
initial reaction → residual → predicts drift. It broke at the first link. Costs were never reached,
and the residual's failure to predict drift is uninformative because the residual itself is
ill-defined without Stage 1.

Concretely, the numeric components are the weak point. XBRL facts for the quarter being announced are
generally filed later with the 10-Q, not with the 8-K, so a strictly point-in-time construction can
only use **previously filed** quarters. The proxies therefore encode stale accounting rather than the
news actually released that day — which sits in the exhibit text. That is a design limitation of this
MVP, disclosed rather than patched mid-run.

## Most important limitation

**The numeric "information" available point-in-time at the 8-K is not the information the market is
reacting to.** The quarter's own revenue, operating income and EPS enter XBRL with the subsequent
10-Q. Any honest point-in-time build using XBRL alone measures prior-quarter accounting plus text
novelty, not the released figures. A credible version would parse the reported figures from the
Exhibit 99.1 text itself. This MVP does not do that, and the Stage-1 failure is consistent with it.

## Data integrity

Provenance retained per event: ticker, fiscal period, accession, filing and exhibit URLs, acceptance
timestamp (US/Eastern), exhibit SHA-256, XBRL concepts used, and the filed-before cutoff, plus
reaction/entry/exit dates in the panel. Every accounting reference is filed strictly before the event;
text novelty compares each release only with that ticker's immediately preceding release, via a
stateless `HashingVectorizer` (no corpus fitting). Standardization, regularization selection and any
threshold use training-fold data only, with alpha chosen by inner chronological validation.

One extraction defect was found and fixed **before** any outcome was inspected: the exhibit selector
matched only `ex99`-style filenames and missed conventions like `exhibit9919302025.htm`,
`q2fy26exhibit991er.htm` and `googexhibit991q32025.htm`, dropping seven tickers. Broadening it raised
coverage from 17 to 22 tickers and cleared the feasibility gate. The gate itself was never lowered.

## Interpretation

No claim is made of analyst-expectation surprise, intrinsic value, causal underreaction, market
inefficiency, investability, or generalization outside this sample. This is one MVP specification on
one locked 24-ticker universe, 2020–2025.

Reproduce: `python tools/run_earnings_information_absorption.py`
