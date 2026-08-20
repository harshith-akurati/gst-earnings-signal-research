# Prospective cohort yield: what the no-retry two-query design actually accumulates

**Date:** 2026-08-20
**Status:** ARITHMETIC ONLY. No design change proposed or made. No new data request of any kind.
**Purpose:** make the data-accumulation rate a known number rather than an assumption.

---

## 1. Design parameters (from the frozen records, not assumed)

| Parameter | Value | Source |
|---|---|---|
| Universe | **101 issuers** (raw 102, deduplicated by issuer) | `collection_provenance.jsonl` record 3, `universe_snapshot`, Nasdaq-100 official constituents, retrieved 2026-08-18 |
| Queries per retrieval | **2** (`<TICKER> stock`, `<Issuer name> stock`), separate one-keyword requests, never batched | `TRENDS_METHOD_FROZEN`, `queries.batching` |
| Retrieval days per event | **2** (T−1, T0) | `scheduled_retrieval_dates` |
| Both queries required | **yes** (`both_queries_required: true`, `one_query_fallback: false`) | `TRENDS_METHOD_FROZEN.aggregation` |
| Both days required | **yes** (`both_days_required: true`) | same |
| Retry policy | **NONE** — no retry, no second same-day request after success or failure | `request_parameters.retry_policy` |
| Verdict gate | **75 eligible events** before any scientific or trading verdict | `FROZEN_DESIGN_v1.0.md` section 7 |
| Composition gate | no ticker supplies more than **10%** of eligible events | same |

**Therefore an event requires 4 consecutive successful Trends retrievals, with no second chance at
any of them.** That is the structural fact driving everything below.

Baseline calendar: 101 quarterly reporters = **404 events/year = 33.67 events/month** (flat average).

---

## 2. Model A — i.i.d. per-query failure

This is the model as literally requested: each of the 4 retrievals fails independently with
probability *p*. P(event valid) = (1 − p)^4.

| p per query | P(all 4 succeed) | Valid events/month | Valid events/quarter | Months to reach 75 |
|---|---|---|---|---|
| **10%** | 0.6561 | **22.1** | 66.3 | **3.4** |
| **25%** | 0.3164 | **10.6** | 32.0 | **7.0** |
| **40%** | 0.1296 | **4.4** | 13.1 | **17.2** |

**Cost of the "both days required" rule.** If only one retrieval day were required (2 requests
instead of 4), holding everything else fixed:

| p per query | Valid events/month | Months to 75 |
|---|---|---|
| 10% | 27.3 | 2.8 |
| 25% | 18.9 | 4.0 |
| 40% | 12.1 | 6.2 |

At p = 40%, requiring both days nearly **triples** time-to-gate (6.2 → 17.2 months). The second
retrieval day is a stability diagnostic (`stability_gap`, explicitly `descriptive_only`,
`can_change_predictor_or_eligibility: false`) — so the design is currently paying its largest
throughput cost for a field that, by its own definition, cannot change any predictor or eligibility
decision.

**Anchoring on what was actually observed:** across the 2 T−1 retrievals executed so far, 1 failed.
A naive 50% per-query rate gives P(event) = 0.0625, **2.1 valid events/month, 35.6 months to 75.**
This figure should not be taken seriously as an estimate — n = 2 — but it marks the pessimistic end.

---

## 3. Model B — the model the evidence actually supports

**Model A is the wrong model**, and this matters more than any number in it.

The ROST post-mortem establishes that the failure was **deterministic, not stochastic**: the string
`Ross Stores, Inc. stock` sits below Google Trends' volume floor and returns an empty series *every
time*. It is a property of the query string, which is a property of the issuer's legal name.

Consequences that Model A cannot express:

1. **Failures are perfectly correlated within an issuer.** If an issuer's name query is dead, it is
   dead at T−1 *and* T0, so no retrieval-day redundancy helps.
2. **Failures are perfectly correlated across time.** It is dead this quarter, next quarter, and
   every quarter. That issuer contributes **zero events, permanently**.
3. **Retries are worthless.** The request does not fail transiently; it returns a correct empty
   answer. No retry policy recovers it.

Let *q* = the share of the 101 issuers whose `<Issuer name> stock` query falls below the threshold.
Surviving issuers contribute at approximately full rate; dead issuers contribute nothing, ever.

| q (dead issuers) | Live issuers | Valid events/month | Months to 75 |
|---|---|---|---|
| **10%** | 90.9 | **30.3** | **2.5** |
| **25%** | 75.8 | **25.3** | **3.0** |
| **40%** | 60.6 | **20.2** | **3.7** |

*q is not currently known.* Estimating it requires querying issuer names, which this document does
not do. One issuer has been sampled and it failed (1/1) — that is not an estimate of q, only proof
that q > 0.

---

## 4. The finding that matters is not the throughput

Model B looks *better* than Model A on months-to-gate. **That comparison is misleading, and reading it
as good news would be the serious error here.**

Under Model A, failures are random noise: the cohort accumulates more slowly but remains a
**representative** sample of the universe.

Under Model B, failures are a **systematic filter on issuer identity**. And the filter is not
arbitrary — a company's name query falls below the Trends volume floor precisely when **few people
search for that company by name**. That is, when public attention to it is low.

> **This study measures whether attention dislocation predicts realized moves. Its collection
> mechanism silently deletes low-attention issuers from the sample.**

The predictor and the missingness mechanism are the same construct. This is selection on the
independent variable, and it is not fixable after the fact by weighting, because the deleted issuers
have no data at all. A cohort of 75 events assembled this way would satisfy the frozen sample gate
while being systematically unrepresentative in the one dimension the study is about.

Two secondary effects:

- **The 10%-per-ticker composition gate becomes easier to pass for the wrong reason.** With fewer
  live issuers the cohort concentrates, but the gate counts share of *eligible* events, so a
  shrunken, biased pool can still satisfy it.
- **The bias is invisible in the ledger.** A dead issuer produces a `FAILURE` record and then simply
  never appears again. Nothing in the current artifacts distinguishes "this issuer is permanently
  excluded" from "this event happened to fail", so the ledger will not surface the pattern on its own.

---

## 5. Additional attrition not modelled above

Both models cover only the Trends leg. The frozen design imposes further refusals that reduce yield
independently, and they compound multiplicatively:

- Options records missing a bid or ask are **refused, not repaired**; crossed markets are refused.
- Option quotes timestamped after the announcement are refused.
- Event timing must be verified against an issuer release or SEC filing; vendor calendar dates are
  `SCHEDULING_INPUT_UNVERIFIED` until confirmed.
- Only prospective events inside a 90-day horizon are enrollable.
- Announcements are **seasonally clustered**. Nasdaq-100 reporting concentrates into roughly four
  earnings seasons, so the flat 33.67/month is a smoothed average, not a monthly reality — some
  months deliver far more, others near zero. Time-to-gate in *calendar* months will therefore be
  lumpy, and the figures above should be read as "months of average calendar", not as a schedule.

**Every figure in sections 2 and 3 is an upper bound on the true rate.**

---

## 6. Summary

| Question | Answer |
|---|---|
| Retrievals required per event | **4**, all must succeed, no retry |
| Yield at 10% / 25% / 40% i.i.d. per-query failure | **22.1 / 10.6 / 4.4** valid events per month |
| Months to the 75-event gate | **3.4 / 7.0 / 17.2** |
| Is the i.i.d. model right? | **No** — the observed failure is deterministic per issuer |
| Yield if 10% / 25% / 40% of issuer names are below threshold | **30.3 / 25.3 / 20.2** per month; **2.5 / 3.0 / 3.7** months to gate |
| Principal risk | **Not throughput. Selection bias correlated with the study's own predictor.** |

The honest one-line statement of the accumulation rate: **at any plausible failure rate the cohort
reaches 75 events within roughly 3 to 17 months of average calendar, but under the failure mode
actually observed it reaches 75 events on a sample from which low-search-attention issuers have been
systematically removed.**

The corrected method — which is to be frozen separately — should be evaluated primarily on whether it
makes the issuer query resolvable for *all* issuers, not on whether it raises the success rate.
