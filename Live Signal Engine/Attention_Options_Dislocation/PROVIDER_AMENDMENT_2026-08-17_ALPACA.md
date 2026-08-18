# Provider Amendment 1 — Alpaca Paper Only replaces Tradier as the initial options provider

**Date:** 2026-08-17
**Applies to:** `FROZEN_DESIGN_v1.0.md` (SHA-256
`dc270ef0f2d61c6267204bfc15c2f9e54ca7a2b3264b07f2fb749454c106f1a5`)
**Nature:** **Additive only.** The frozen design is **not rewritten** and remains byte-identical.
This document is committed **before the first Alpaca network request of any kind**.

---

## 1. Why the provider changes

`FROZEN_DESIGN_v1.0.md` §8 and the operations README name **Tradier** as the options provider.
Tradier is **unavailable**: obtaining either a sandbox or a real-time token requires **brokerage
account onboarding** — a real legal identity, a real Social Security Number and brokerage
suitability disclosures.

**No fabricated identity and no third party's SSN will be used to obtain market data.** That is not
a data-quality trade-off; it is identity fraud, and the study will not commit it to acquire a quote.
Tradier therefore stays unavailable until a legitimately-owned account exists.

## 2. What replaces it

**Alpaca Paper Only**, using its **free `indicative` options data feed**, becomes the study's
**initial options-data provider**. Alpaca is reached with **market-data endpoints only** and with a
paper-account credential pair supplied through the environment.

## 3. Mandatory labelling

Every option observation derived from Alpaca is labelled

```
ALPACA_INDICATIVE_NON_EXECUTABLE
```

The label is **mandatory, not decorative**. A record that cannot carry it is refused. Provider and
feed provenance are required fields; a record without both is refused.

## 4. What this feed is, and what it is not

The free `indicative` feed is **not** consolidated OPRA execution-quality data.

- Its **option trades may be delayed**.
- Its **quotes are modified / indicative**, not the consolidated national best bid and offer.
- It is a **paper-trading data tier**, not an execution data tier.

The feed is recorded as exactly what it is. It is never relabelled, upgraded, or described as
real-time consolidated data anywhere in this study's artifacts.

## 5. What these observations may support

They **may** be used to test the study's **primary** question:

> whether pre-announcement search attention improves forecasting of the **realized magnitude** of an
> earnings move beyond an **options-implied benchmark**.

An indicative midpoint is an acceptable *benchmark of market expectation* for a magnitude-forecasting
test, because that test compares a forecast against a realized magnitude — it does not require that
the benchmark be tradeable.

## 6. What these observations may NOT support

They **may not** be used to claim, imply, or report:

- **executable bids or asks**, or that any recorded price was obtainable;
- **realistic spread costs**;
- **attainable straddle P&L** of any kind;
- **tradeable options alpha**, spread-aware or otherwise.

Any such claim is **outside what this data can bear** and is prohibited while this amendment is in
force, regardless of how the numbers come out.

## 7. Execution-economics stage: deferred

The frozen design's **secondary tradability test** (§6 "Secondary tradability test" — long ATM
straddle entered at the combined ask, exited at the first permitted post-event combined bid,
spread-aware net return) is **deferred**, not deleted, with status:

```
OPRA_EXECUTION_DATA_UNAVAILABLE
```

It remains frozen exactly as written and may only be executed against consolidated OPRA
execution-quality data. It is **not** run against the indicative feed, and no partial or
"approximate" version of it is run against the indicative feed.

## 8. What this amendment does NOT change

Nothing else in `FROZEN_DESIGN_v1.0.md` changes. Specifically **unchanged**:

- every **statistical rule** — the 75-event minimum, all four success gates, the ≥2% chronological
  OOS MAE improvement threshold, the block-bootstrap 95% interval requirement, the positive-Spearman
  requirement, and the ≤10% single-ticker concentration cap;
- every **attention feature** — `<TICKER> stock`, `<Issuer name> stock`, one public sample per query
  per day, retained provenance fields;
- every **event rule** — prospective-only, 90-day horizon, AMC/BMO snapshot-day assignment,
  issuer-release or SEC confirmation of timing, `SCHEDULING_INPUT_UNVERIFIED` for vendor dates;
- every **timestamp cutoff** — the 15:45 ET snapshot target, the T−2 search cutoff, and refusal of
  any quote timestamped at or after the announcement;
- the **contract-selection rule** — nearest expiration strictly after the event, strike nearest the
  contemporaneous underlying price;
- the **primary forecast metric** — `midpoint_implied_move = (call_mid + put_mid) / underlying_price`
  and the chronological out-of-sample MAE comparison against the options-only baseline.

The universe hierarchy, the exclusion rules, and every collection-stage prohibition in §8 of the
frozen design continue to apply unchanged.

## 9. No outcome was opened to justify this change

**No retrospective outcome, realized move, post-announcement return, or strategy result was
retrieved, computed, or inspected in deciding to change providers.** The change is forced by
credential availability alone. Opening an outcome to justify a provider choice would make the
provider choice outcome-dependent, and it is therefore prohibited both in making this amendment and
in any future amendment to it.

## 10. If the provider cannot satisfy the frozen calculation

If Alpaca's schema cannot faithfully implement the frozen contract-selection and implied-move
arithmetic, collection **stops** with status `PROVIDER_SCHEMA_INCOMPATIBLE`. The formulas are **not**
altered to accommodate the provider, and **no other provider is silently substituted**.
