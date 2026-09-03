# Signal Without Strategy: Search Attention, Earnings Surprise, and the Difference Between Association and Tradable Prediction

*Version 1.1 — 2026-08-27.*

*Exploratory retrospective research synthesis. **Not preregistered.** Every result below was
**known after analysis**, not specified before it, except where a frozen design is explicitly
named in §4.7. No investable strategy is claimed. The separate prospective protocol has produced
no results and contributes no evidence here (§4.7).*

---

## 1. Abstract

Public information can be associated with market activity without supplying incremental forecasts or tradable returns. This study examines weekly Google search attention around 285 usable U.S. earnings announcements from 28 companies between March 2021 and December 2025. Before outcomes were observed, signal events were selected for Google Trends spikes at least five rolling standard deviations above the prior 12-week mean, excluding the event week from its own baseline; matched controls were not required to fall below that threshold.

Among 73 signal events and 73 individually matched controls, signal events had absolute event-day returns 2.08 percentage points larger (p = .004). This retrospective association does not establish incremental predictive value. A separate ticker-clustered regression across all 285 usable events produced a 1.51-percentage-point coefficient (p = .066) with a confidence interval spanning zero. The first result is a matched difference among selected signal events; the second is a conditional association across the full usable sample.

Incremental prediction tests were null. Against a price-and-calendar baseline, attention contributed 0.013 percentage points (p = .98). Out-of-sample magnitude error was 3.630 percentage points with attention versus 3.628 without (paired p = .98), and a directional model was less well calibrated than an intercept-only baseline. An attention-filtered event strategy returned 0.85% per event, but comparable post-earnings drift occurred without the filter, so the return cannot be attributed to attention.

Association, prediction, and tradability must be evaluated as separate empirical claims.

*(Abstract: 233 words.)*

---

## 2. Introduction

Two ideas motivate much of the modern "alternative data" literature. The first is that public
attention is informative: if unusually many people search for a company's name, something is
happening to that company, and prices may respond. The second is that earnings surprise is
informative: if reported profit differs from what was expected, the price should move to reflect the
news. Both ideas are intuitive, both have serious academic support, and both are widely marketed as
foundations for trading strategies.

This paper is about the gap between those two facts and a third claim that does not follow from
them. A variable can be reliably *associated* with market outcomes without *predicting* them
incrementally, and it can predict them incrementally without being *tradable* once one accounts for
when information actually becomes observable and what execution costs. These are three different
assertions requiring three different kinds of evidence. Conflating them is, in our reading, the most
common way that plausible research becomes an unreliable strategy.

**The research question.** Across a connected program of retrospective studies, do search attention
or vendor-defined earnings surprise supply *incremental, out-of-sample* forecasting power over
strong baselines — and if so, does that power survive realistic timing and costs?

**Main findings.** Search attention repeatedly failed the incremental test. Strategies built around
attention-selected earnings events were profitable in raw terms, but the profitability was
attributable to the underlying earnings event, not to attention: once a baseline containing price
and calendar information was in place, the marginal contribution of attention was economically and
statistically indistinguishable from zero. Earnings surprise told a more interesting story. Its
association with the first full-session price reaction was real, replicated in direction across two
non-overlapping time periods, and became statistically clear in the larger, earlier sample. But the
association did not translate into stable forecast-error reduction, so the downstream drift and
trading stages were never authorised.

Along the way, an internal defect produced a result that looked like a discovery. Correcting it
changed a directional model from apparently skilful to demonstrably unskilful. We report that
episode as a finding in its own right.

**Contribution.** We do not claim markets are efficient, that Google Trends is useless, that
earnings surprises do not matter, or that alternative data cannot work. We claim something narrower
and, we think, more useful: we locate precisely where two intuitively attractive signals stop being
predictive, and we document the methodological controls whose presence or absence changed the
answer.

**Roadmap.** Section 3 defines the three-level framework. Section 4 explains the data and study
architecture from first principles. Section 5 reports the search-attention results and Section 6 the
leakage episode. Sections 7 and 8 cover the earnings-surprise measurement work and its outcome
results including the temporal replication. Section 9 gives a cross-study evidence matrix, Section
10 discusses interpretation, Section 11 states limitations, and Section 12 concludes.

---

## 3. Conceptual framework: three levels of evidence

**Level 1 — Association.** A variable moves together with an outcome. Formally, some measure of
dependence between the variable and the outcome differs from zero in-sample. Association is cheap to
establish and is often contemporaneous: it can hold even when the variable is measured *at the same
time as* or *after* the outcome begins to form.

**Level 2 — Incremental prediction.** The variable improves a genuine out-of-sample forecast
*relative to a strong baseline*. Three words carry the weight. *Out-of-sample* means the model
never saw the evaluated observation during fitting or tuning. *Incremental* means the comparison is
against a baseline already containing everything cheaply available — not against an empty model.
*Strong* matters because a weak baseline makes almost anything look useful; an intercept-only
probabilistic forecast, for example, is a surprisingly hard benchmark to beat on calibration.

**Level 3 — Tradability.** The incremental forecast survives contact with implementation: the
signal must be observable strictly before the position is taken, the holding period must be
executable, and returns must survive transaction costs and realistic slippage.

Each level is strictly stronger than the last. Association does not imply prediction, because a
contemporaneous relationship carries no guarantee that the variable leads the outcome, and because
improvement against a *particular* baseline is not implied by correlation. Prediction does not imply
tradability, because a statistically real reduction in forecast error can be far smaller than the
cost of acting on it.

| Level | Claim | Minimum evidence required | Typical failure mode |
|---|---|---|---|
| 1. Association | The variable moves with the outcome | A dependence measure with an honest interval; no look-ahead in construction | Contemporaneous or post-hoc measurement |
| 2. Incremental prediction | It improves a proper OOS forecast | Chronological validation, a strong baseline, a prespecified loss, an uncertainty interval, stability across periods | Weak baseline; in-sample tuning; leakage |
| 3. Tradability | The forecast is implementable | Signal observable before entry; explicit entry/exit; costs deducted; clustered inference | Ignoring timing; ignoring costs; overfitting the backtest |

This ladder is the organising device for everything that follows. Each study is placed at the
highest level its evidence actually supports — not the highest level it was designed to reach.

---

## 4. Data and study architecture

### 4.1 Google Trends and search-query ambiguity

Google Trends does not report search counts. It reports a **relative** index: for a requested query,
region, and time window, Google scales the series so the maximum observed value equals 100 and
everything else is expressed as a proportion of that peak. Two consequences matter. First, the index
is not comparable across windows: extending the window can rescale every earlier point. Second, the
series is sampled, so repeated retrievals of the identical request can differ.

A subtler problem is **query ambiguity**. A ticker such as "AMD" is also an acronym in other
domains, and a company name such as "Apple" is also a fruit. Any attention series therefore measures
a mixture of the intended construct and unrelated interest. We treat search attention as a *noisy
proxy* for investor attention, not as a measurement of it.

Because Trends series retrieved today are a retrospective reconstruction, they cannot by themselves
establish that the identical series was available at the time a decision would have been made. This
limitation is recorded explicitly in the committed nowcast artifact and is not resolved anywhere in
this program.

### 4.2 Earnings announcements and event timing

United States issuers report quarterly results via a press release, filed with the Securities and
Exchange Commission (SEC) as an 8-K under **Item 2.02**, "Results of Operations and Financial
Condition". The SEC records an **acceptance timestamp** — when the filing was actually received —
which is the closest available proxy for when the information became public.

Timing determines which trading session can first reflect the news. We use a rule fixed before
outcomes were examined, in United States Eastern Time: a release accepted before 09:30 maps to that
same trading session; a release accepted at or after 16:00 maps to the next session; a release on a
weekend or market holiday maps to the next session; and a release accepted *during* market hours is
**excluded**, because a daily closing price cannot separate the pre-release from the post-release
part of that day. Getting this wrong is not a minor issue: mapping an after-close release to the
session that has already closed would import the outcome into the predictor.

### 4.3 Abnormal returns and benchmarks

A raw stock return mixes firm news with whatever the market did that day. We therefore work with
**abnormal returns**: the stock's return minus a benchmark's return over the identical window. For
the semiconductor studies the benchmark is SMH, a semiconductor sector exchange-traded fund, which
removes both market-wide and sector-wide movement and isolates the firm-specific component.

Two windows recur. The **initial abnormal reaction** spans the close before the event session to the
close of the event session — the first full session in which the news can be absorbed. The
**subsequent abnormal return** spans the event-session close to the close five sessions later, the
window in which post-announcement drift, if present, would appear.

### 4.4 Vendor-defined earnings surprise, and what it is not

Earnings surprise is conventionally *reported minus expected* earnings per share (EPS). Obtaining
this historically is harder than it appears, and the distinction drove a substantial part of this
program.

We initially attempted to parse EPS directly from SEC earnings-release exhibits. That work is
described in Section 7. When it proved infeasible at the required coverage, we moved to a commercial
vendor feed. The resulting variable is labelled **`VENDOR_DEFINED_REPORTED_EPS_SURPRISE`** throughout,
and the label is load-bearing. The vendor's `reportedEPS` is **not** SEC-validated GAAP diluted EPS:
on 139 events where a vendor value overlapped an SEC-validated parsed value, only 8 matched within
$0.01 — a match rate of 0.0576 — with a median absolute difference of $0.26. The differences were
not random. They decomposed into retroactive share-split restatement and a GAAP-versus-adjusted
definitional gap.

**The estimate-vintage limitation is unresolved.** The vendor publishes no guarantee that a
historical `estimatedEPS` is the consensus that existed *at the announcement* rather than a value
revised later. This program records that as
`POINT_IN_TIME_ESTIMATE_PROVENANCE_NOT_GUARANTEED` and does not resolve it by assumption. If those
estimates were revised after the fact, the surprise variable is contaminated in an unknown
direction. This is the single largest threat to interpreting even our statistically clear
association, and we do not claim to have eliminated it.

Because share splits scale reported EPS, estimated EPS, and their difference proportionally, we use
**`surprisePercentage`** — a ratio — as the primary field, and verified mechanically on all 320
in-window vendor records that the ratio is invariant to proportional restatement. That neutralises
*split* restatement. It does **not** neutralise *estimate-vintage* revision.

### 4.5 Validation, metrics, and inference

All model evaluation uses **chronological expanding-window validation**: train on all data up to a
year, test on the following year, then expand. This mirrors how a forecaster would actually have
operated and prevents future observations from informing past predictions. Every transformation —
winsorisation limits, standardisation means and standard deviations, and hyperparameter selection —
is fitted **inside the training fold only** and then applied frozen to the test fold. A single
full-sample standardisation would leak distributional information from the test period backwards.

Metrics are chosen to match the target. **Mean absolute error (MAE)** measures average forecast
error for continuous outcomes. The **Brier score** is the mean squared error of probability
forecasts, where lower is better and calibration matters as much as discrimination [Brier 1950].
**AUC** (area under the receiver operating characteristic curve) measures ranking ability for binary
outcomes; 0.5 is chance. **Spearman correlation** measures monotonic association without assuming
linearity.

For uncertainty we use a **moving-block bootstrap**: resampling calendar blocks rather than
individual events preserves the fact that events cluster in earnings season and that firms within a
period share shocks. Where coefficient inference is reported, standard errors are clustered by firm
using a CR2/bias-reduced-linearisation estimator with Satterthwaite degrees of freedom, which is
appropriate when the number of clusters is small [Cameron et al. 2008].

### 4.6 Leakage

**Leakage** is the accidental presence, in a model's inputs, of information not available at
prediction time [Kaufman et al. 2012]. Two forms bit us directly. **Duplicated events** inflate
apparent sample size and can place copies of the same observation in both training and test folds.
**Same-event lag features** occur when a variable intended to carry the *previous* event's value
actually carries the current event's own outcome. Section 6 documents both.

### 4.7 Status of the components

Interpretation requires knowing what was fixed in advance and what was not.

- **Frozen before designated runs.** The semiconductor extraction quality gate; the feasibility
  design for the vendor data; the outcome design for the initial-reaction study; and the temporal
  replication design. Each was committed before the corresponding outcomes were opened.
- **Corrective controls introduced after defects were found.** Deduplication and the lag-feature fix
  in the direction study (Section 6); throttle-aware retrieval in the vendor audit. These improved
  validity but were reactive, and we label them as such.
- **Retrospective exploratory work.** Everything in this synthesis. No result here is a
  prospectively registered confirmation.
- **Separate prospective protocol, no results.** A distinct preregistered protocol (internally
  "HYP-01") exists as a *future confirmatory validation* of the Level-1 association reported here. As
  of this version it has produced **no results of any kind**: no eligible observation has been
  collected, no outcome has been analysed, and its own governing status records outstanding
  methodological decisions. It contributes **no evidence** to this manuscript, appears nowhere in our
  results, and nothing in this synthesis should be read as anticipating its outcome. Confirmation, if
  it comes, will come from that protocol and not from anything reported here.

---

---

## 4A. Methods: four distinct analyses, four distinct estimands

The results in Section 5 come from four analyses that answer different questions on different
samples with different estimands. Conflating them is the specific error this paper is about, so we
state each separately before reporting any of them. **All four are retrospective and exploratory.**

### 4A.1 Corrected matched association (Level 1)

**Question.** Do high-attention earnings events move more than *comparable earnings events*?

**Design.** Treated high-attention earnings events matched one-to-one against control earnings
events. The August 2022 correction restricted the committed matched set after two defects were
found: self-matching (an event matched to itself) and control reuse (one control serving several
treated events). Correction dropped 20 self-matched pairs and 40 pairs lacking a unique control,
leaving 73 pairs.

**Estimand.** ATT on |day return|, percentage points.
**Statistic.** Mean paired difference over surviving matched pairs.
**Inference.** CR2 (BRL) covariance clustered on ticker, coefficient-specific Satterthwaite df,
26 clusters.
**Scope limit, quoted from the artifact.** *"Restriction of the committed matched set, not a
re-match; the control candidate pool is not committed."*

**What it cannot answer.** Whether attention *predicts* anything out of sample, and whether any of
it is tradable. Matching controls for what was matched on; it does not make the comparison causal,
and it is estimated on data already observed.

### 4A.2 Ticker-clustered regression (primary magnitude model)

**Question.** In the wider event population, is the high-attention indicator associated with a larger
absolute move once inference accounts for repeated tickers?

**Design.** Regression of absolute day return on the high-attention indicator over the full usable
event population, not the matched subset.
**Estimand.** Coefficient on the high-attention indicator, percentage points.
**Inference.** CR2 clustered on ticker with Satterthwaite df — the same inference family as 4A.1 but
a different sample and estimand, which is why the two estimates are not expected to coincide and
must not be averaged or presented as replications of each other.

**Designated primary.** `primary_magnitude_abs_day_return` was designated the primary specification
in advance. Two other specifications exist in the same artifact and are reported in Section 5.2 as
labelled sensitivities only.

### 4A.3 Out-of-sample forecasting (Level 2)

**Question.** Does adding attention features to a strong baseline reduce forecast error on data the
model has not seen?

**Design.** Nested comparison of a price-and-calendar baseline (B) against the same baseline plus
attention features (C), evaluated out of sample.
**Estimand.** Pooled mean absolute error in percentage points, and the paired loss difference
between C and B.
**Inference.** Paired test on the loss difference, clustered.
**Decision rule, prespecified.** The comparison is decided on the paired loss difference, not on
whichever model happens to look better on a secondary metric.

**Why this is the decisive level.** A variable can be associated with an outcome and still fail here,
because association is measured in-sample against no competitor while forecasting is measured out of
sample against a baseline that already contains the easy information.

### 4A.4 Trading evaluation (Level 3)

**Question.** Does an implementable strategy using attention earn a return that attention itself
explains?

**Design.** An event strategy selecting earnings events with an attention filter, evaluated net, and
then the decisive test: the incremental contribution attributable to high attention once a baseline
containing price and calendar information is already present.
**Estimand.** Mean net return per event for the standalone figure; coefficient attributable to high
attention, in percentage points, for the incremental figure.
**Inference.** CR2 clustered on ticker with Satterthwaite df.

**Why the standalone figure is not the answer.** Selecting earnings events selects post-earnings
drift, which exists whether or not anyone is searching. Only the incremental coefficient isolates
attention's contribution.

---

## 5. Search-attention results

We report the load-bearing evidence rather than every exploratory branch, and we do not claim that
all possible attention specifications have been tested. The subsections are ordered by the evidence
hierarchy of Section 3: association first, then incremental prediction, then tradability. Each level
is a strictly stronger claim than the one before it, and attention clears only the first.

### 5.1 Matched-event association (Level 1)

High-attention earnings events are more active than comparable earnings events. In the corrected
matched-population analysis, the **mean paired difference in absolute move was +2.0797 percentage
points**, with **p = 0.00397**. The result is not fragile:

**Table 2. Matched Level-1 association: primary estimate and all four sensitivities.** Estimand is
the ATT on |day return| in percentage points. Inference is CR2 (BRL) clustered on ticker with
coefficient-specific Satterthwaite degrees of freedom, except sensitivity B which is an unpaired
Welch test by construction.

| Specification | n pairs | Estimate (pp) | SE (pp) | df | t | p | 95% CI (pp) | Status |
|---|---|---|---|---|---|---|---|---|
| **Primary — mean paired difference** | **73** | **+2.0797** | **0.638** | **19.742** | **3.260** | **0.00397** | **[+0.7479, +3.4116]** | **PRIMARY** |
| Sensitivity A — reuse retained, self-match excluded | 113 | +1.9591 | 0.9254 | 15.118 | 2.117 | 0.05125 | [−0.0120, +3.9302] | sensitivity |
| Sensitivity B — unpaired Welch on corrected arms (treated 8.0286%, n = 73; control 5.9489%, n = 73) | 73 v 73 | +2.0797 | — | 138.58 | 2.351 | 0.02014 | not reported in artifact | sensitivity |
| Sensitivity C — leave-one-ticker-out | 73 | +1.8343 to +2.3772 (range over 26 refits) | — | — | — | — | — | sensitivity |
| Sensitivity D — excluding the 8 overlap identities | 65 | +2.5682 | 0.6347 | 18.128 | 4.046 | 0.00075 | [+1.2354, +3.9009] | sensitivity |

Source: `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json`. Fields
marked "—" or "not reported" are genuinely absent from the artifact and were **not** computed for
this manuscript.

**Sensitivity D, stated explicitly because it is the most favourable number in the family.**
Sensitivity D is a **sensitivity analysis, not the primary estimate.** It excludes the eight
identities that are *both* self-matched and reused — LDOS 2021-08-03, LDOS 2023-10-31,
NFLX 2022-01-20, NFLX 2023-01-19, NKE 2024-03-21, QCOM 2025-02-05, SBUX 2025-01-28, STZ 2025-01-10
— which the frozen corrective design names individually because "the two defects overlap … They must
not be counted twice when sizing the correction." Removing them leaves 65 pairs and produces the
largest point estimate (+2.5682 pp) and the smallest p-value (0.00075) of any specification here.

**That is exactly why it is not promoted.** Reporting the tightest of five specifications as the
headline would be the specification shopping this paper exists to document. The primary estimate
remains **+2.0797 pp at p = 0.00397**, and D is disclosed so a reader can see the full range rather
than discover it later. D is a **Level-1 association on a restricted matched subset**; it is not
incremental prediction, not causal evidence, and not alpha.

**A restriction, not a re-match.** The overlay records its own scope limit verbatim: *"Restriction of
the committed matched set, not a re-match; the control candidate pool is not committed."* Every
sensitivity above, D included, re-uses the committed matched set rather than re-running the matching
procedure, so none of them can repair a matching decision — only test the surviving set's
sensitivity to it.

**One design-versus-result discrepancy, recorded rather than smoothed.** The frozen corrective design
specifies leave-one-ticker-out over **28** refits; the committed results report **26** refits and 26
entries in `by_excluded_ticker`. We report the realised 26 and flag the difference; we did not
recompute anything to reconcile it.

**Balance.** The overlay also reports balance diagnostics on the surviving set (sensitivity E):
mean |pre-drift| 3.619 pp treated versus 2.9662 pp control, 72 same-ticker pairs, 73 BMO/AMC
concordant pairs, and the treated/control calendar-year distributions. Treated events carry
noticeably more pre-event drift than controls, which is a limitation of the match rather than a
result, and we treat it as such in Section 11.

**What this is.** A retrospective, matched, **Level-1 association** between search attention and how
much a stock moves around its earnings announcement. The comparison is against *matched earnings
events*, not against ordinary weeks, which is what makes it a statement about attention rather than
a restatement of the fact that earnings announcements move prices.

**What this is not.** It is not a forecast, not an incremental contribution over a baseline, and not
a tradable edge. It was estimated on data already observed, and it is reported here as association
only. Sections 5.2 through 5.4 test whether anything survives the stronger claims. Nothing does.

**Provenance.** This estimate **supersedes** the earlier unmatched-control figure of **+1.4411 pp**
(high 7.8871%, n = 152; control 6.4459%, n = 133; t = 2.138) reported as
`Q1_abs_move_high_vs_control` in `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json`. That artifact now
carries `citation_status = SUPERSEDED_BY_THIS_ARTIFACT`. The superseded value is retained in this
manuscript for history only (Appendix A) and is not the current estimate. The correction overlay
itself is labelled `RETROSPECTIVE_DEVELOPMENT_ONLY_NOT_HYP01_CONFIRMATION`.

**Sample attrition under the correction.** The original matched set held 133 pairs. Correction
dropped 20 self-matched pairs (defect E1) and 40 pairs with no unique control (defect E2), leaving
**73 surviving pairs** with 73 distinct treated and 73 distinct control identities — a loss of 60
observations from the original treated arm. The corrected estimate is therefore both larger and
built on less than half the original pairs, and both facts belong together whenever it is cited.

### 5.2 Primary clustered magnitude model

The primary inferential specification regresses the absolute day return on the high-attention
indicator with ticker-clustered CR2 standard errors and Satterthwaite degrees of freedom:

> **+1.509 percentage points**, CR2 SE **0.766**, **df 16.3**, **p = 0.0662**,
> 95% CI **[−0.113, +3.131]**.

**The interval spans zero and the result is not statistically supported at the 5% level.** We
describe it as *suggestive but unsupported*, and we do not describe it as significant, marginal,
trending, or approaching significance.

Two other specifications in the same artifact reach significance. **Neither is promoted, and both
are recorded here only as labelled sensitivities:**

| Specification | Estimate | p | Status |
|---|---|---|---|
| **`primary_magnitude_abs_day_return`** | **+1.509 pp** | **0.0662** | **PRIMARY — designated in advance** |
| `magnitude_abs_excess_vs_spy` (benchmark-adjusted) | +1.5388 pp | 0.03707 | sensitivity |
| `repeated_control_sensitivity.deduplicated_cr2` (deduplicated) | — | 0.00193 | sensitivity |

The primary gate was designated before these were compared. Reporting whichever variant clears 5% as
the headline would be exactly the specification shopping this paper argues against, and the
significance of a benchmark-adjusted or deduplicated variant does not transfer to the primary
estimand. All three are Level-1 association measures; **none of them is incremental prediction**, and
no combination of them changes the null results in Sections 5.4 and 5.5.

### 5.3 Standalone profitability is not attention alpha

An event strategy selecting earnings events using an attention filter produced a mean net return of
**0.8543%** per event. Taken alone this looks like a working signal. The decisive test is
incremental: with a baseline already containing price and calendar information, the marginal
contribution attributable to attention was **+0.0131 percentage points** with **p = 0.98332**. The
point estimate is near zero and the p-value is close to 1.

**The same post-earnings drift was present without the attention filter.** The strategy captured the
well-documented tendency of prices to drift after earnings announcements [Ball and Brown 1968; Foster
et al. 1984; Bernard and Thomas 1989], not anything contributed by search attention. Attention acted
as an event-selection device that picked earnings events, and earnings events carry drift regardless
of who is searching.

**The 0.8543% is therefore not a GST result and must not be cited as one.** It is a property of the
underlying earnings-drift population that the attention filter happened to select into. Reporting it
as attention performance would be the central error this paper documents.

### 5.4 Direction

A logistic model predicting the sign of the initial price move was compared to an intercept-only
baseline that simply assigns the training-fold base rate to every observation. On pooled
out-of-sample data the baseline achieved a Brier score of **0.2560**; the logistic model achieved
**0.2711**. Lower is better, so the model was *worse calibrated than assuming the base rate*. Its
AUC was **0.4654**, below the 0.5 chance level.

### 5.5 Magnitude

A model forecasting the absolute size of the earnings move produced a pooled out-of-sample MAE of
**3.6299** percentage points with attention features versus **3.6284** without them. The
attention-augmented model was very slightly worse, and a paired test of the loss difference gave
**p = 0.9827**.

### 5.6 Weekly volatility

The final weekly volatility model showed a MAE change of **−0.0309%** (baseline MAE **0.420367**
versus augmented **0.420497**), with a paired block-bootstrap interval of
**[−0.0011023, +0.0010839]** spanning zero.

### 5.7 Product search and restaurant demand

A pilot testing whether product-level search improves prediction of restaurant-sector earnings moves
found that adding search blocks **worsened** both metrics: pooled Brier rose from **0.20211** to
**0.23665** to **0.24739** as search blocks were added, and continuous MAE for the absolute move
rose from **5.4534** to **5.6790** to **5.8543** percentage points. The committed decision label is
`NO_INCREMENTAL_SEARCH_VALUE`.

### 5.8 Fundamental nowcasting

An attempt to nowcast company fundamentals from search demand terminated at
`INSUFFICIENT_DATA`. It is reported for completeness and supports no conclusion in either
direction.

**Summary.** Search attention reached Level 1 in places — it does track when something is happening
— but did not reach Level 2 in any test we ran with a strong baseline.

---

## 6. Leakage as an empirical result

The directional study initially looked successful. With duplicates present, the logistic model
scored **63.6%** accuracy, AUC **0.6395**, and Brier **0.23824**. Those numbers would ordinarily
justify further development.

Two defects were then found. First, the event table contained **68** duplicated rows among **285**,
leaving **217** unique event identities after deduplication. Duplicates inflate the sample and can
put copies of one event on both sides of a train/test split. Second, a feature intended to carry the
*prior* event's gap direction was in fact reading the **same event's own** gap direction — the
model was being shown a transformation of the answer.

After deduplicating to unique identities and correcting the lag feature, the same model family
scored:

- accuracy **47.9%** (below the 53.5% achieved by always predicting positive),
- AUC **0.4654**,
- direction-only strategy net return **−0.7027%**.

The pre-correction figures are **invalidated** and are reported here only to document the size of
the distortion. This was an internal defect, discovered and corrected internally; we neither
sensationalise it nor conceal it.

The methodological point generalises. Nothing about the pre-correction output looked anomalous:
63.6% accuracy on a binary financial target is plausible enough to be believed and modest enough not
to invite suspicion. Realistic-looking alpha can be manufactured accidentally by two ordinary
data-handling mistakes, which is precisely why leakage audits belong in the standard protocol rather
than in the appendix [Kaufman et al. 2012].

---

## 7. Earnings-surprise measurement engineering

Measurement work and outcome evidence must be kept separate, because effort spent on the former is
not evidence for the latter.

A general attempt to parse EPS from earnings-release exhibits across a broad universe was abandoned
as infeasible. A semiconductor-specific parser performed substantially better, reaching a held-out
conditional precision of **0.9860** (combined **0.9868**) — that is, where a value could be
independently checked, it was almost always right.

But precision conditional on checkability is not coverage. Verified reference coverage reached only
**0.7037** against a required 0.80, and usable-event coverage **0.2742** against 0.60. The binding
constraint was structural rather than a parser deficiency: the audit design validated an extracted
quarterly EPS against the same quarter restated in a later quarterly filing, and a **fiscal-year-end
quarter is never restated that way**, because the next periodic report is the annual filing. Of
**216** extractions, **47** were fiscal-year-end quarters, capping attainable coverage at
**0.7824** — below the gate, independent of parser quality.

The extraction phase was therefore classified with two separate fields rather than one: a
`FAILED_EXTRACTION_QUALITY_GATE` decision alongside a characterisation of
`HIGH_CONDITIONAL_PRECISION_BUT_INSUFFICIENT_VERIFIED_COVERAGE`. The original single label was
corrected because it implied the parser was inaccurate, which the evidence contradicts.

A subsequent audit of the vendor feed found uniform coverage (**320** complete records, 10 firms)
and perfect internal arithmetic consistency, but its crosswalk gate failed at **0.6719** against
0.90 — again for a structural reason, since only **267** of **306** SEC events carried a parsed
fiscal period, capping that gate at **0.8344**. That gate failed and **remains failed**; the outcome
studies that follow used a successor exact-date crosswalk and are labelled accordingly.

---

## 8. Initial-reaction results and temporal replication

### 8.1 The 2023–2025 study

Using vendor `surprisePercentage` on **298** uniquely matched semiconductor events, with **116**
out-of-sample events across 2023–2025:

| | Baseline (firm effects) | + Surprise |
|---|---|---|
| MAE of initial abnormal reaction | 0.052506 | **0.051203** |
| Improvement | | **+2.482%** |

Spearman correlation between transformed surprise and the initial reaction was **+0.13515**
(**p = 0.148026**). The block-bootstrap 95% interval for the MAE difference was
**[−0.0007272, +0.0031700]**, which includes zero. The model improved MAE in **all three**
out-of-sample years.

Three of four prespecified gates passed; the uncertainty gate failed. Under the frozen rule the
study stopped.

### 8.2 The 2010–2017 temporal replication

The terminal replication applied the identical frozen model, grid, transformation, bootstrap, and
gates to an earlier, non-overlapping window, on **462** uniquely matched events with **283**
out-of-sample events across 2010–2017:

| | Baseline (firm effects) | + Surprise |
|---|---|---|
| MAE of initial abnormal reaction | 0.044226 | **0.043246** |
| Improvement | | **+2.216%** |

Spearman was **+0.2169** with **p = 0.000236** — larger in magnitude and now clearly significant, on
a sample roughly 2.4 times larger. The bootstrap interval was
**[−0.0000561, +0.0021342]**, again including zero, though only marginally at the lower bound. The
augmented model beat the baseline in **five of eight** years and helped **four of nine** firms —
while **all nine** firms showed a positive firm-level Spearman correlation. The replication failed
its prespecified gate.

### 8.3 Interpretation

The correct reading has four parts, and the order matters.

1. **Earnings surprise contains information about the contemporaneous reaction.** A Spearman of
   +0.2169 at p = 0.000236 across 283 events, positive for every one of nine firms, is not a null
   result and we do not describe it as one.
2. **The association replicated in direction and strengthened.** Both windows produced positive
   point estimates for both the MAE improvement and the correlation. The two samples do not overlap
   in time.
3. **The fixed model did not deliver stable forecast-error improvement.** Five of eight years, four
   of nine firms, and a bootstrap interval containing zero. The annual pattern was notably unstable —
   strong early, absent in the middle years, strong again at the end.
4. **Therefore the downstream stages were never authorised.** The information–price gap was never
   constructed, the drift model never fitted, and no trading was simulated. A gate that exists to
   prevent building on unstable foundations only works if it is honoured when it fails.

The two windows were never pooled. Combining two independent failures of the same gate to
manufacture a pass would invert the purpose of the gate, and no such combination was performed.

---

## 9. Cross-study synthesis

| Construct | Target | Sample | Association | Incremental prediction | Trading | Principal limitation | Final interpretation |
|---|---|---|---|---|---|---|---|
| Search attention | Absolute earnings move | Retrospective US equities | Present in places | **No** — +0.0131 pp, p = 0.98332 | Standalone 0.8543% net, not incremental | Drift confound | Event selector, not alpha |
| Search attention | Move direction | 217 unique events | None detected | **No** — Brier 0.2711 vs 0.2560; AUC 0.4654 | −0.7027% net | Leakage before correction | No directional skill |
| Search attention | Move magnitude | Retrospective panel | Weak | **No** — MAE 3.6299 vs 3.6284, p = 0.9827 | Not run | Noisy normalisation | No incremental value |
| Search attention | Weekly volatility | Weekly panel | Weak | **No** — −0.0309%, interval spans zero | Not run | Small effect size | No incremental value |
| Product search | Restaurant earnings moves | Sector pilot | Not established | **No** — Brier and MAE both worsened | Not run | Small sample | `NO_INCREMENTAL_SEARCH_VALUE` |
| Vendor earnings surprise | Initial reaction 2023–2025 | 116 OOS events | Positive, not significant (+0.13515, p = 0.148026) | **Gate failed** — +2.482%, interval spans zero | Not authorised | Estimate vintage | Suggestive, not established |
| Vendor earnings surprise | Initial reaction 2010–2017 | 283 OOS events | **Positive and significant** (+0.2169, p = 0.000236) | **Gate failed** — +2.216%, 5 of 8 years | Not authorised | Estimate vintage | Real association, unstable prediction |

No new score, ranking, or aggregate is computed from this table.

---

## 10. Discussion

### 10.0 Why a detectable association coexists with null incremental prediction

The central result of this paper looks paradoxical only until the three levels are held apart. A
matched association of +2.0797 pp at p = 0.00397 is a real, statistically detectable difference. An
incremental contribution of +0.0131 pp at p = 0.98332 is an unambiguous null. Both come from the
same variable on overlapping data. Four reasons they are consistent:

**1. The comparison groups differ.** The association contrasts high-attention earnings events with
*matched earnings events*. The incremental test contrasts a baseline *already containing price and
calendar information* with that same baseline plus attention. If the information attention carries is
also carried by the baseline, attention can differ across groups and still add nothing on top.

**2. In-sample association faces no competitor; out-of-sample prediction faces a strong one.**
Association asks whether a difference exists. Incremental prediction asks whether a variable earns
its place beside features that already work. The second is strictly harder, and most variables that
clear the first fail the second.

**3. Selection is not forecasting.** Attention identifies *which* periods are unusually active. That
is genuinely useful for describing when information arrives — and it is orthogonal to predicting the
*size* of a move before it happens. Our out-of-sample magnitude errors (3.6299 with attention versus
3.6284 without) say the second thing directly.

**4. Magnitude without direction is not tradable.** Even a perfect absolute-move forecast does not
determine position sign, and our direction model was worse calibrated than assuming the base rate.

**What follows, and what does not.** The corrected matched association does **not** overturn the null
incremental findings, and the nulls do **not** invalidate the association. They are answers to
different questions, and this paper's contribution is largely the discipline of keeping them apart.
Nothing here licenses a causal reading: the matched design controls for what it matched on and no
more, the data are observational, and the analysis is retrospective.


**Why a variable can explain a reaction yet fail to forecast it.** The initial-reaction studies
regress a same-session outcome on a variable released just before that session. That is close to a
*contemporaneous* relationship: surprise and reaction are two views of one event. Forecasting is a
harder task requiring the variable to carry information the baseline lacks *and* to do so
consistently enough that average error falls. A modest, unstable edge can be genuinely present and
still fail to reduce mean absolute error reliably.

**Rapid incorporation.** If prices absorb earnings news within the first session, then by the time a
daily-close-based strategy can act, the informative content is largely priced. Our design measures
the reaction over the first full session and would enter only at that session's close — after the
absorption we measure.

**Regime and firm heterogeneity.** The replication's annual pattern was strong in the early years,
absent in the middle, and strong again at the end, and the model helped only four of nine firms. One
natural hypothesis is that the relationship is regime-dependent. We record this as a hypothesis
*generated by* the observed instability. We did not test it, it is not established, and testing it
retrospectively on the same data would be exactly the multiple-testing error this program is trying
to avoid [Harvey et al. 2016].

**Measurement error.** Both constructs are proxies. Search attention mixes investor interest with
unrelated queries and is delivered on a rescaled, sampled index. Vendor EPS is restated for splits
and follows an adjusted rather than GAAP definition. Classical measurement error attenuates
estimated relationships, so our nulls may understate any true effect — a limitation, not a defence.

**Sample size and power.** With 116 and 283 out-of-sample events and firm-level clustering, our
power to detect a small MAE improvement is limited. Failing an interval-based gate is at least as
consistent with low power as with no effect, and we prefer that honest ambiguity to a claim in
either direction.

**Strong baselines.** The single most consequential design choice was comparing against strong
baselines. An intercept-only probability forecast beat a fitted logistic model; a firm-effects
baseline absorbed most of what surprise appeared to offer. Against an empty baseline, several of
these signals would have looked successful.

**Why null incremental results are useful.** Published financial signals are filtered by
positive results, so the aggregate literature overstates how many work [Harvey et al. 2016; Bailey
and López de Prado 2014]. Documented nulls with prespecified gates and honest intervals are a
partial corrective — particularly when, as here, the nulls are *incremental* nulls that leave the
underlying association intact.

---

## 11. Limitations

**Retrospective selection.** Every result in this paper was produced after the data existed. Analyses
were chosen, refined, and in one case corrected with the outcomes visible. Nothing here was
preregistered, and no result should be read with the confidence a prespecified test would earn.

**Multiple development analyses.** Many specifications were run over the life of this program. We
report the load-bearing ones and label sensitivities as sensitivities, but we cannot compute an
honest multiplicity correction across an exploratory development process, and we do not pretend to.
The five matched-association specifications in Table 2 span +1.8343 to +2.5682 pp with p-values from
0.00075 to 0.05125; that spread is itself the relevant caution.

**Matching assumptions.** The matched analysis is a *restriction of a committed matched set, not a
re-match* — the control candidate pool is not committed, so the matching cannot be reproduced or
improved from the artifacts. Correction cost 60 of the original treated observations, leaving 73
pairs. Balance is imperfect: treated events carry mean |pre-drift| of 3.619 pp against 2.9662 pp for
controls, so some of the measured difference may reflect pre-event activity the match did not remove.

**Ticker clustering and small effective samples.** Inference clusters on ticker with 25–26 clusters
and Satterthwaite degrees of freedom between 15.1 and 19.7 — well below the nominal cluster count.
Small-cluster inference is fragile, and the reported intervals should be read as approximate.

**Google Trends normalisation.** The attention measure is a normalised, sampled index rather than a
raw count. It is rescaled per query and window, may be redrawn differently on re-request, and its
query strings are ambiguous between a firm and its products. Section 4.1 covers this; it bounds how
precisely any attention coefficient can be interpreted.

**Estimate vintage.** Results were produced at different times under different code. The matched
association carries an August 2022 correction; the clustered models and forecasting results predate
it. We have not re-run earlier analyses under later code, so vintage differences remain.

**Generalisability.** A locked universe of large-capitalisation United States equities over a limited
window, with attention measured by one vendor's index. Nothing here establishes that the association
holds for other universes, periods, attention measures, or market regimes.

## 12. Conclusion

**Search attention is associated with unusually active earnings events in retrospective matched
comparisons, but it does not provide reliable incremental forecasting or trading value.** That
sentence is the whole finding, and every qualifier in it is load-bearing: *retrospective*, because
nothing here was preregistered; *matched*, because the comparison is against comparable earnings
events rather than ordinary weeks; *association*, because the incremental tests were null.

The evidence separates cleanly by level. At Level 1, high-attention events moved +2.0797 pp more than
matched controls (p = 0.00397), stable from +1.8343 to +2.3772 pp across 26 leave-one-ticker-out
refits. At the primary inferential specification the estimate was +1.509 pp with a 95% interval of
[−0.113, +3.131] that spans zero (p = 0.0662) — suggestive, not supported at 5%. At Level 2 nothing
survived: incremental contribution +0.0131 pp (p = 0.98332); out-of-sample magnitude MAE 3.6299 with
attention versus 3.6284 without (p = 0.9827); a direction model worse calibrated than assuming the
base rate. At Level 3 the standalone 0.8543% per event was post-earnings drift that existed without
the attention filter.

Attention and earnings surprise both carry descriptive information about how prices react to public
news. In the strongest case we measured, vendor-defined earnings surprise showed a positive,
statistically clear association with the first full-session reaction across 283 out-of-sample
semiconductor events, positive for every firm examined.

Descriptive information alone is not alpha. The same variable, in the same frozen model, improved
forecast error in only five of eight years and for four of nine firms, with a bootstrap interval
including zero — and search attention, tested against strong baselines, failed to add incremental
value in every specification we ran.

Method changed conclusions materially. Correcting duplicated events and one mis-specified lag
feature turned an apparent 63.6% directional accuracy into 47.9%. Requiring a strong baseline turned
a 0.8543% standalone strategy into an incremental contribution of 0.0131 percentage points at
p = 0.98332. Requiring temporal replication turned a suggestive 2023–2025 result into a
better-identified but still unstable 2010–2017 one.

**None of the tested strategies qualifies as investable, and none is offered as such.** The
contribution of this work is not a signal. It is a reasonably careful map of where explanatory
signal stops becoming predictive strategy — and a demonstration that the boundary sits earlier, and
is easier to cross accidentally, than intuition suggests.

---

## 13. Future work

**A prospective confirmatory study exists and has produced no results.** A separate preregistered
protocol (internally "HYP-01") is designed to test, prospectively, whether the Level-1 association
reported here survives as a confirmatory finding. As of this version it has produced **no results of
any kind**: no eligible observation has been collected, no outcome has been analysed, and outstanding
methodological decisions remain open in its own governing record.

It contributes **no evidence** to this manuscript. Nothing in this paper should be read as
anticipating, previewing, or partially reporting its outcome, and no number in this paper comes from
it. Whether the association replicates prospectively is precisely the open question, and this paper
does not answer it.

**What would strengthen the retrospective record**, independent of that protocol: a committed control
candidate pool so the matching can be reproduced rather than only restricted; a reproducible
in-repository size study for the clustered inference; and replication of the attention measure under
an independently sourced attention proxy.

---

## References

1. Ball, R., and Brown, P. (1968). An empirical evaluation of accounting income numbers.
   *Journal of Accounting Research*, 6(2), 159–178. https://doi.org/10.2307/2490232
2. Bailey, D. H., and López de Prado, M. (2014). The deflated Sharpe ratio: correcting for selection
   bias, backtest overfitting, and non-normality. *The Journal of Portfolio Management*, 40(5),
   94–107. https://doi.org/10.3905/jpm.2014.40.5.094
3. Bernard, V. L., and Thomas, J. K. (1989). Post-earnings-announcement drift: delayed price response
   or risk premium? *Journal of Accounting Research*, 27 (Supplement), 1–36.
   https://doi.org/10.2307/2491062
4. Brier, G. W. (1950). Verification of forecasts expressed in terms of probability.
   *Monthly Weather Review*, 78(1), 1–3. DOI (plain text, contains angle brackets):
   `10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2`. Publisher page:
   https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml
5. Cameron, A. C., Gelbach, J. B., and Miller, D. L. (2008). Bootstrap-based improvements for
   inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427.
   https://doi.org/10.1162/rest.90.3.414
6. Da, Z., Engelberg, J., and Gao, P. (2011). In search of attention. *Journal of Finance*, 66(5),
   1461–1499. https://doi.org/10.1111/j.1540-6261.2011.01679.x
7. Diebold, F. X., and Mariano, R. S. (1995). Comparing predictive accuracy.
   *Journal of Business and Economic Statistics*, 13(3), 253–263.
   https://doi.org/10.1080/07350015.1995.10524599
8. Foster, G., Olsen, C., and Shevlin, T. (1984). Earnings releases, anomalies, and the behavior of
   security returns. *The Accounting Review*, 59(4), 574–603. https://www.jstor.org/stable/247321
9. Harvey, C. R., Liu, Y., and Zhu, H. (2016). ... and the cross-section of expected returns.
   *Review of Financial Studies*, 29(1), 5–68. https://doi.org/10.1093/rfs/hhv059
10. Kaufman, S., Rosset, S., Perlich, C., and Stitelman, O. (2012). Leakage in data mining:
    formulation, detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data*,
    6(4), Article 15. https://doi.org/10.1145/2382577.2382579

---

## Appendix A — Methodological history: two comparisons that are not interchangeable

This appendix exists to prevent a specific confusion. Two different "high attention moves more"
comparisons exist in this project's history. Only one is the manuscript's Level-1 estimate.

**A.1 The matched earnings-event comparison — the current estimate (§5.1).**
Treated high-attention earnings events against *matched control earnings events*. Corrected primary:
**+2.0797 pp, p = 0.00397**. This is what §5.1 reports.

**A.2 The superseded unmatched-control figure.**
`Q1_abs_move_high_vs_control` in `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json`: high 7.8871%
(n = 152) versus control 6.4459% (n = 133), difference **+1.4411 pp**, t = 2.138. The control matching
in this version was defective; the artifact now carries
`citation_status = SUPERSEDED_BY_THIS_ARTIFACT`. **Retained for history only. Not the current
estimate. Not to be cited.**

**A.3 The mechanism-stability comparison — a different study, not comparable.**
An earlier, separate analysis compared STRONG_EARNINGS attention-spike weeks against **random
baseline weeks**:

| Quantity | Value | Source |
|---|---|---|
| Spike mean absolute move | 7.72% (n = 147) | `MechanismStability_Results.csv`, `full_sample` row |
| Random-baseline mean absolute move | 3.72% (n = 1,275) | same row |
| Difference | 4.0 points | same row |
| Cohen's d | 1.294 | same row |
| Permutation p | < 0.0001 (0 of 10,000 permutations) | `STRATEGY_SPEC_v1.0_TERMINOLOGY.md` §3 |

**This is not the manuscript's Level-1 result and is not comparable to it.** Three reasons, each
sufficient on its own:

1. **The comparison group is different.** Spike weeks are compared against *random weeks*, not
   against matched earnings events. Most of the 4.0-point gap is the ordinary fact that earnings
   weeks move more than non-earnings weeks. It largely measures the presence of an earnings
   announcement, not the presence of attention.
2. **It is unmatched.** No control matching was performed, so firm, period, and event-type
   composition are uncontrolled.
3. **It is not incremental evidence.** Like every association in this paper, it says nothing about
   forecasting or tradability, and the incremental tests in §5.3–§5.5 are null regardless.

The large Cohen's d of 1.294 should be read in that light: it is a large *unmatched descriptive*
effect, and it is precisely the kind of number that looks like a trading signal and is not one. No
confidence interval is stored for it — the source script reports point estimates and a permutation
p-value only — so it cannot be compared inferentially with the matched estimate in §5.1 even if the
designs were alike, which they are not.

---

## Source artifacts

Every figure in this manuscript is drawn from a committed artifact in this repository:

- `Correction_Overlays/2026-08-22_C5_Control_Matching/CORRECTED_RESULTS_v1.0.json`
  — **authoritative for the Level-1 matched association (§5.1)**; supersedes
  `Q1_abs_move_high_vs_control`
- `RETROSPECTIVE_MARKET_RESPONSE_RESULTS_v1.0.json`
  — clustered inference (§5.2, §5.3); its `Q1_abs_move_high_vs_control` block is **superseded**
- `Live Signal Engine/MechanismStability_Results.csv` and
  `Live Signal Engine/STRATEGY_SPEC_v1.0_TERMINOLOGY.md` §3 — **Appendix A only**, not a headline
  result
- `RETROSPECTIVE_DIRECTION_SIGNAL_RESULTS_v1.0.json` and
  `RETROSPECTIVE_DIRECTION_SIGNAL_REPORT_v1.0.md`
- `RETROSPECTIVE_MAGNITUDE_FORECAST_RESULTS_v1.0.json`
- `RESTAURANT_SEARCH_PILOT_RESULTS_v1.0.json`
- `SEARCH_DEMAND_NOWCAST_RESULTS_v1.0.json`
- `ATTENTION_ACTIVITY_MISMATCH_RESULTS_v1.0.json` (branch `phase2-attention-activity-mismatch`)
- `SEMICONDUCTOR_EPS_ABSORPTION_RESULTS_v1.0.json`
- `Live Signal Engine/Semiconductor_EPS_Absorption/structured_earnings_feasibility_v1.0.json`
- `SEMICONDUCTOR_SURPRISE_ABSORPTION_V3_RESULTS_v1.0.json`
- `SEMICONDUCTOR_SURPRISE_TEMPORAL_REPLICATION_RESULTS_v1.0.json`
