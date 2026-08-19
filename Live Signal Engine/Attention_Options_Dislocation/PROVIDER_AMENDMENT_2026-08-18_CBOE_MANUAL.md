# Provider Amendment 2 — manual, official Cboe delayed-quotes capture replaces Alpaca

**Date:** 2026-08-18
**Applies to:** `FROZEN_DESIGN_v1.0.md` (SHA-256
`dc270ef0f2d61c6267204bfc15c2f9e54ca7a2b3264b07f2fb749454c106f1a5`) as already amended by
`PROVIDER_AMENDMENT_2026-08-17_ALPACA.md` (SHA-256
`0417380b3115255ed65956a54b2120f789334a8f5a9afcde61e8ae184547df0f`).
**Nature:** **Additive only.** Neither the original frozen design nor Amendment 1 is rewritten; both
remain byte-identical. This document is committed **before any real Cboe file is ingested**.

---

## 1. Alpaca remains unavailable, and provider-acquisition work stops here

Amendment 1 made Alpaca Paper Only's free `indicative` feed the study's options provider. That
attempt **failed at authentication**: the credential pair `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`
was PRESENT but returned **HTTP 401** from `data.alpaca.markets` on the options snapshot endpoint,
on the equity market-data endpoint, and on this repository's own previously-proven bars path. That
evidence stands and is **not** deleted, rewritten or reinterpreted; it remains in
`collection_provenance.jsonl` as `provider_connectivity_check` and `auth_failure_cross_check`.

**No further account, identity, credential or API-provider work will be attempted.** The study stops
trying to acquire programmatic market-data access. Each such attempt has cost more than it returned,
and the alternative below needs no account at all.

## 2. The replacement source

The **official Cboe Delayed Quotes dashboard**, operated by the exchange itself.

Cboe permits a person to enter a ticker by hand and download the resulting quotes as CSV. Cboe's
terms **explicitly prohibit automated extraction** of that data.

**Therefore, no code in this repository may request, scrape, click, download, or otherwise access
Cboe.** There is no HTTP client, no browser driver, no headless browser, no scheduled fetch and no
retry loop pointed at Cboe, and none may be added. The prohibition is on the *access*, not merely on
the intent.

**A human must manually open the page, manually enter the ticker, and manually click
"Download CSV."** The repository's software may only read a file that a person has already
downloaded and placed on local disk. This is a **local-file importer**, not a provider client.

## 3. Mandatory labelling

Every observation accepted from a manually downloaded Cboe file is labelled

```
CBOE_MANUAL_DELAYED_NON_EXECUTABLE
```

The label is mandatory. A record that cannot carry it is refused, as is a record missing provider or
feed provenance.

## 4. The information cutoff is the displayed timestamp, not the download time

Cboe's dashboard displays the **market-data timestamp** for the quotes it is showing. That displayed
timestamp — **not** the time the file happened to be saved — is the study's information cutoff, and
it is what every timing rule is evaluated against.

The two are recorded **separately** on every record:

* `quote_timestamp_utc` — the page-displayed market-data timestamp.
* `retrieved_at_utc` — when the human downloaded the file.

**Delayed-data timing rule.** The feed is delayed, so the displayed timestamp necessarily precedes
the download. A record is **refused** unless the displayed timestamp is *earlier* than the retrieval
timestamp, and refused if the two are further apart than the permitted staleness bound. A file whose
displayed timestamp is missing, unparseable, equal to, or later than its retrieval timestamp is
refused rather than repaired.

## 5. What these observations are, and are not

Delayed exchange quotes are **not** consolidated real-time OPRA execution-quality data, and are not
treated as such.

They **may** be used to test the study's primary question: whether pre-announcement search attention
improves forecasting of the **realized magnitude** of an earnings move beyond an **options-implied
benchmark**.

They **may not** establish, imply or report:

* **executable bids or asks**, or that any recorded price was obtainable;
* **spread-adjusted P&L** of any kind;
* **tradeable options alpha**.

The execution-economics stage stays deferred under Amendment 1's status
`OPRA_EXECUTION_DATA_UNAVAILABLE`. No executable straddle cost, simulated P&L or trade instruction is
emitted from a delayed record, and the importer refuses to construct one.

## 6. What this amendment does NOT change

Unchanged: the **model**, every **attention feature**, the **contract-selection rule** (nearest
expiration strictly after the event; strike nearest the contemporaneous underlying price) and the
**primary prediction metric**
(`midpoint_implied_move = (call_mid + put_mid) / underlying_price`, compared by chronological
out-of-sample MAE against the options-only baseline).

Also unchanged: the 75-event minimum and all four success gates, the 15:45 ET snapshot target, the
T−2 search cutoff, the AMC/BMO snapshot-day rules, the requirement that event timing be confirmed
against an issuer release or SEC filing, the official-source universe hierarchy, and every
collection-stage prohibition in §8 of the frozen design.

## 7. No outcomes have been viewed

**No outcome, realized move, post-announcement return or strategy result has been retrieved,
computed or inspected** — not in reaching this amendment, and not at any point in this study. The
provider change is forced by access constraints alone. Opening an outcome to justify a provider
choice would make the choice outcome-dependent, and it is prohibited here and in any future
amendment.
