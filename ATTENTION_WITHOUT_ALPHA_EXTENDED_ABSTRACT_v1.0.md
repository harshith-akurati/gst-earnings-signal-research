# Attention Without Alpha: A Leakage-Controlled Evaluation of Google-Search Signals Around Earnings

**Extended abstract, v1.0.** Exploratory retrospective development: nothing here is confirmatory;
no result is deployed or traded.

## 1. Research question and motivation

Since Da, Engelberg and Gao (2011), Google search volume has been linked to returns, volatility and
investor behavior, and a stronger practical claim has followed: that it yields a tradable edge around
scheduled corporate events.

We ask a narrower question. **Under strict point-in-time discipline, does Google search improve
out-of-sample prediction around earnings announcements — of direction, magnitude, or underlying
fundamentals — relative to honest comparators?** We separate two constructs the literature
often blends: *ticker attention* (the bare ticker, e.g. "AAPL"), intended as a proxy for investor
notice, and *product demand* (e.g. "Starbucks"), intended as a proxy for customer activity. Both
are **candidate** proxies only — a search-construct-validity check remains open, so neither is
validated against the concept it should capture.

Several analyses initially produced encouraging headline results, and each was eliminated by a
specific, nameable control rather than a change of opinion. That pattern — not any single negative
finding — is the subject.

## 2. Data and chronological methodology

The evidence spans five connected retrospective studies on U.S. equities, 2019–2025, using weekly
Google Trends, daily OHLC prices, and SEC filings (8-K item 2.02 acceptance timestamps for timing;
XBRL facts for revenue).

Two kinds of rule must be distinguished. **Rules frozen before each designated run** — universe,
queries, feature definitions, primary metric, decision thresholds — were fixed ahead of that run's
outcomes. **Corrective controls** — event-identity deduplication, the strictly earlier lag, the
rebuilt pre-event attention window, the calibrated prevalence null — were introduced *after* defects
surfaced and are **not** preregistered. **The synthesis here was itself not preregistered.** We
report **both pre-correction and corrected results** wherever a control changed the answer.

Design rules applied across runs: chronological expanding-window validation only, no random split
anywhere; search features drawn only from weeks whose period *closes strictly before* the
announcement timestamp, asserted mechanically per event in the final pilot (353 checks, 0
violations); announcement timing from the filing; unique event identities; CR2/BRL errors clustered
by ticker with Satterthwaite df; and prespecified primary metrics — MAE for continuous targets,
Brier for probabilistic ones — never overturned by secondary metrics.

## 3. Main results

**(a) A profitable-looking strategy whose edge is not attention.** A benchmark-neutral post-earnings
continuation rule conditioned on high search attention returned **+0.854% net per trade** (t ≈ 3.0
standalone). The *incremental* effect of the filter — strategy return on a high-attention indicator,
ticker fixed effects, ticker-clustered CR2 — is **+0.013 pp, p = 0.9833**. The rule is post-earnings
drift; low-attention controls earned marginally *more*.

**(b) A direction model whose skill was leakage.** A logistic model predicting the overnight
earnings-gap sign reached **63.6% out-of-sample accuracy** (AUC 0.6395). But the population reused
matched controls: **68 of 285** rows were duplicate (ticker, date) identities — one appeared
seven times — letting a lagged "prior gap direction" feature read *its own* outcome. After
deduplication to **217 unique** identities and a strictly earlier lag, accuracy fell to **47.9%**
(AUC 0.4654) and the strategy moved from +0.60% to −0.70% net. Against an intercept-only prevalence
null (Brier 0.2560), no learned model won (logistic 0.2711).

**(c) Magnitude forecasting with a strictly pre-event measure.** The population's own attention
z-score was unusable: its 14-day window overlaps the announcement in every event. Rebuilt from weeks
closing strictly before the event, absolute-gap MAE was **3.6284 pp without attention versus
3.6299 pp with it**, paired **p = 0.9827** — a tight interval centered on zero.

**(d) Brand-search revenue nowcasting.** For eight restaurant chains, quarterly year-over-year
revenue growth was forecast with and without two frozen brand-search features: MAE **6.3679 pp
without search versus 6.8735 pp with it**, paired **p = 0.6253**. Only **38** out-of-sample
observations existed against a preregistered minimum of 40, so the study is labeled
**INSUFFICIENT_DATA** on its own rule rather than reported as a finding.

**(e) Large-move prediction: ticker attention versus product demand.** For the same firms we
predicted whether the earnings-session absolute return would exceed the training-fold 75th
percentile. Pooled out-of-sample Brier: **null 0.18454**, baseline **0.20211**, + investor searches
**0.23665**, + product-demand searches **0.24739** — degrading monotonically as search is added.
Product demand *given* investor attention: **p = 0.6813**.

**(f) One genuine but non-search regularity.** The *non-search* baseline showed secondary ranking
evidence: **AUC 0.6460** and a top-quintile realized large-move rate of **35.29%**, a **1.447× lift**
over the **24.39%** base rate. It carries no prespecified decision rule here, establishes no
investable model, and is **not** evidence for search data of either kind.

## 4. Methodological contribution

The intended contribution is a catalog of mechanisms that manufacture convincing alternative-data
results, each demonstrated by a result that survived until its control was applied:

1. **Duplicated events** from reused matched controls, inflating samples and enabling
   self-referential lags.
2. **Contemporaneous-feature leakage**, where a "lagged" feature reads its own outcome.
3. **Overlapping search windows**, where an attention measure's window spans the event it should
   anticipate.
4. **Weak probabilistic comparators** — beating an always-positive classifier is not beating a
   calibrated null.
5. **Probability miscalibration**, where AUC ≈ 0.64 indicates limited ranking ability while
   overconfident probabilities lose to the null on Brier.
6. **Query-construct contamination**, conflating ticker attention with product demand.
7. **Insufficient point-in-time availability** — in this project's retrieval environment, Google
   Trends returned weekly resolution only for windows under roughly five years and rescaled each
   series to the request window, silently coarsening longer requests to monthly.
8. **Failure to test incremental value against controls**, judging a filtered strategy on its
   standalone t-statistic rather than against unfiltered and low-attention comparators.


## 5. Limitations

This is **a set of connected exploratory studies, not one preregistered experiment**; analyses were
designed sequentially and the framing emerged from the failures. **Samples are small and ticker clusters few** — 26 to 28 in the larger studies,
7 to 8 in the restaurant work, with single-digit Satterthwaite degrees of freedom in places.
**Google Trends histories are retrospective reconstructions** that may not match what was observable
contemporaneously. A **search-construct-validity question remains unresolved**. There is **no
historical options-implied-move benchmark** — none was obtainable — so we cannot say whether search
adds anything beyond what options priced. And there is **no prospective confirmation**.

We do not claim Google Trends is useless in general, nor that these nulls demonstrate market
efficiency — only that in these settings, under these controls, the apparent signals did not survive.

## 6. Proposed full-paper contribution

A full manuscript would offer (i) a taxonomy of leakage and comparator failures specific to
search-based event studies, with reproducible demonstrations; (ii) minimum standards — strict
period-close cutoffs, event-identity deduplication, calibrated null comparators, cluster-robust
incremental tests, separation of attention from demand constructs; and (iii) a
negative-replication record pairing pre-correction and corrected numbers.

## 7. Questions for a faculty reviewer

1. Is the false-discovery and negative-replication framing a legitimate finance contribution?
2. Should these experiments be combined into one manuscript or narrowed to the strongest two or three?
3. What additional analysis or prospective evidence would be necessary for a credible submission?
4. Which journal, working-paper series, or conference would be the best fit?
5. Would you be willing to advise on or supervise a full manuscript?
