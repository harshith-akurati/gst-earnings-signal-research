# Point-in-Time Earnings Surprise v2 — Extraction Phase Result

`EXPLORATORY_RETROSPECTIVE_DEVELOPMENT_ONLY` · **`google_trends_used: false`** ·
**`analyst_estimates_used: false`** · **`later_xbrl_used_for_prediction: false`**

## Decision

# `EXTRACTION_NOT_RELIABLE`

The Exhibit 99.1 parser did not reach the extraction-quality gate. **No outcome model was fitted, no
post-entry return was computed, and no trading test was run.** Tolerances were not loosened, no
selected value was hand-corrected, and returns were never inspected to choose a parsing rule.

## Why this task existed

PR #31 measured *previously filed* XBRL accounting rather than the figures announced on the day, and
reported that as its most important limitation. This task attempted the correction: parse the actual
release-day values out of Exhibit 99.1. The correction attempt failed at the measurement step, which
is a different and more informative failure than PR #31's.

## Parser-development sample

Deterministic and outcome-blind: events ranked by
`SHA-256("PIT_EARNINGS_SURPRISE_V2_DEV_SAMPLE|ticker|fiscal_period|accession")`, first **2 per
ticker** — **48 events across 24 tickers**. Returns were not consulted in selection or development.

## Extraction coverage

605 Item 2.02 8-K events, **531 with a locatable earnings exhibit**, 382 with two or more extracted
numeric components.

| Component | Extracted | Validated | Contradicted by reference | No reference in window |
|---|---|---|---|---|
| Revenue | 383 | **56** | **114** | 213 |
| Operating income | 375 | **76** | **195** | 104 |
| Diluted EPS | 359 | **237** | **44** | 78 |

**Validation rate (gate definition — validated ÷ extracted): revenue 14.6%, operating income 20.3%,
diluted EPS 66.0%.** The gate requires **≥ 90% each**. All three fail.

Restricting to extractions where a later-XBRL reference actually exists in window
(validated ÷ (validated + contradicted)): revenue **32.9%**, operating income **28.0%**, diluted EPS
**84.3%**. Both readings are reported; **neither reaches the gate**, and the second is not a
substitute for the specified one.

Tolerances used: revenue and operating income within **0.5% relative**, diluted EPS within
**$0.01 absolute**.

## What the parser is getting wrong

Two distinct problems, both visible without touching returns:

1. **Wrong row selection.** The most common revenue label chosen is `Revenues` (107 events), which is
   correct, but `Sales and maturities of marketable securities` was selected **22 times** — a
   cash-flow-statement line, not revenue. Row regexes anchored on `sales` match balance-sheet and
   cash-flow rows in filers whose income statement uses different wording.
2. **Wrong column or scale.** Operating income contradicts the reference most often (195 of 271
   comparable), consistent with selecting a prior-year column or misresolving thousands/millions in
   filers whose unit caption sits outside the table markup.

Diluted EPS is the most reliable component (84.3% among comparable) because EPS rows are lexically
distinctive and carry no unit scaling.

An honest reading: this is a **heterogeneous-format parsing problem across 24 filers**, not something
a regex pass completes inside a one-hour budget. Each filer's income statement uses different row
wording, column ordering and unit conventions.

## What was not done

Because the gate failed, the frozen design was **not** committed and the outcome stage was **not**
run: no surprise construction, no information–reaction gap, no Model B/C comparison, no bootstrap, no
trading simulation. Reporting any of those on 15–20% validated inputs would have been a fabricated
result.

The later-XBRL facts were used **only** as an audit reference. They never selected a value, never
replaced a value, and never entered any feature — `later_xbrl_used_for_prediction: false`, and no
predictive stage exists in this branch to have consumed them.

## Which failure mode this is

Of the three the task distinguishes, this is **inadequate extraction** — not "reliable extraction but
no predictive value", and not "predictive value eliminated by costs". Neither of those was reached.
The question of whether point-in-time earnings surprises predict drift **remains open and untested**.

## Most important limitation

**Correct measurement of release-day figures is the binding constraint, and it is a substantial
engineering problem rather than a modeling one.** A credible v3 would need per-filer income-statement
templates or a table-structure model that identifies the income statement before matching rows, plus
validation on a held-out set of filers. Until extraction validates at the required rate, any
downstream surprise measure is unreliable regardless of how the models are specified.

## Correction to an interim statement

An earlier diagnostic in this session reported "mismatched-against-reference = 0". That was an
artifact of the audit table storing the reference value only on success, so contradictions were
invisible. The corrected counts appear above: revenue 114, operating income 195, EPS 44 contradicted.
The conclusion is unchanged and the fix made the failure *more* clear-cut, not less.

## Interpretation

Nothing here is called an analyst surprise, consensus miss, fair value, intrinsic value, proven
mispricing or causal underreaction. No signal is claimed.

Reproduce: `python tools/validate_exhibit_extraction.py`
