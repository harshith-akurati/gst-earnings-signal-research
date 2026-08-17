# Attention–Implied Volatility Dislocation — FROZEN DESIGN v1.0

**Status:** Frozen. Committed **before any Alpha Vantage, Tradier, Google Trends, price or
earnings-calendar request was made** for this study.
**Type:** Prospective observational study. Collection-first; no verdict until the minimum sample.
**This is not a GST-to-stock-return regression.** Search attention supplies magnitude/attention
information, the options market supplies the benchmark, and **direction is never predicted**.

---

## 0. Relationship to the existing HYP-01 collection block

The repository records that prospective collection is **BLOCKED**. That block is examined here and
**not modified, reinterpreted or relaxed**. The controlling language is HYP-01-specific:

> "**Why collection is still blocked.** Authorizing the statistical package removes one gate. It
> does not remove the others. Collection may begin only when F5 construct validity is resolved and
> recorded, every other pre-observation gate in the cohort protocol and eligibility rules is
> satisfied, and the event-60 environment freeze required by D11 is recorded."
> — `Live Signal Engine/GST_HYP01_METHOD_AUTHORIZATION_2026-08-16.md`, §"Why collection is still
> blocked"

Every condition named is a HYP-01 construct: **F5** is HYP-01's GST construct-validity gate, the
**cohort protocol** governs HYP-01's locked 24-ticker universe and its ≥60-event enrolment, and the
**event-60 environment freeze** is HYP-01's D11 requirement. The cohort protocol describes itself as
carrying forward "the locked 24-ticker universe, the collection window (2026-09-01 … 2027-05-31),
the target of ≥ 60 registered events" — a specific cohort, not a repository-wide prohibition.

**Determination.** The block governs the HYP-01 prospective cohort. It does not, on its own terms,
prohibit this independent follow-on study, which uses a different universe, a different construct,
a different benchmark and its own frozen design. This study therefore proceeds **without touching
HYP-01**: no HYP-01 artifact is read for a decision, modified, or relied upon, and **F5 remains
OPEN and HYP-01 collection remains BLOCKED**.

If the project owner reads the block as global, stop this study — the determination above is a
reading of scope, not an authorization to override anything.

---

## 1. Research question

Does pre-announcement search attention improve prediction of the **realized magnitude** of an
earnings move beyond the **options-implied move**, and does an attention/options dislocation
identify positive net long-straddle returns **after the bid–ask spread**?

---

## 2. Universe

Objective, attention-heavy, optionable frame — never a hand-picked or generated ticker list.

1. **Primary source:** the official Nasdaq-100 constituent source.
2. **Permitted fallback:** the official Invesco QQQ holdings file, used as a **disclosed index
   proxy** and labelled as such in every artifact.
3. **Prohibited:** Wikipedia, scraped aggregator lists, and any generated ticker list.
4. Retain **U.S.-listed operating-company equities with listed options**.
5. **Deduplicate by security/issuer** (multi-class issuers contribute one issuer).
6. **No company may be excluded** because of any observed return, search value, implied move, or
   strategy result. Exclusions are permitted only for: not U.S.-listed, not an operating company
   (fund/trust/SPAC shell), no listed options, or issuer duplication.

The universe snapshot used for any analysis is recorded with its source URL and retrieval date.

---

## 3. Event timing

- **Prospective events only.** No historical event is enrolled.
- **Calendar horizon:** next **90 days**.
- **AMC** (after market close) announcement → option snapshot on the **announcement trading day**.
- **BMO** (before market open) announcement → option snapshot on the **preceding trading day**.
- **Target snapshot time: 15:45 ET.**
- A **Tradier sandbox** snapshot is **15 minutes delayed** and every such record is labelled
  `DELAYED_15_MINUTES`.
- **Search information must end no later than T−2 calendar days.**
- **Never use a post-release value to construct a pre-release feature.**
- **Future outcome, once available:** the absolute underlying return from the pre-event reference
  price to the **first post-announcement regular-session close**. It is *defined* here and
  **not computed, retrieved or inspected** by this study's collection stage.
- **Event timing must ultimately be verified against an issuer release or SEC filing.** Vendor
  calendar dates are **scheduling inputs, not final timing proof**, and are labelled
  `SCHEDULING_INPUT_UNVERIFIED` until confirmed.

---

## 4. Options benchmark

For the **nearest expiration strictly after** the earnings event:

- Select the **strike nearest the contemporaneous underlying price**.
- Record, for both the call and the put: **bid, ask, midpoint, last, volume, open interest, IV if
  supplied, quote timestamp, expiration, strike, provider**.

Definitions:

```
midpoint_implied_move   = (call_mid + put_mid) / underlying_price
executable_straddle_cost = (call_ask + put_ask) / underlying_price
```

- **A missing bid or ask is never silently replaced with the last price.** A record missing either
  side is **refused**, not repaired.
- A **crossed market** (bid > ask) is **refused**.

---

## 5. Search features

**Investor-attention queries, not product demand:**

- `<TICKER> stock`
- `<Issuer name> stock`

Existing repository query-normalisation code is reused where available.

Retained for every retrieval: **exact query, geography, category, time window, retrieval timestamp,
raw-response SHA-256, normalized weekly values.**

- **One public Trends sample per query per day.** No fake repeated-sampling loop — Google may cache
  requests, so repeated in-day sampling measures the cache, not stability. Repeated-sample stability
  accumulates **across distinct retrieval dates**.
- If **authorized Google Trends API alpha credentials** are present they are supported separately and
  the source is labelled. **Alpha access is not assumed to exist.**

---

## 6. Core hypothesis

```
attention_dislocation = percentile(pre_event_attention_z) - percentile(options_implied_move)
```

**Primary tests — run only after the minimum sample is reached:**

1. Whether attention features improve **chronological out-of-sample MAE** over an **options-only
   baseline**.
2. Whether attention dislocation has **positive rank correlation** with
   `realized_absolute_move - options_implied_move`.

**Secondary tradability test:**

- Long ATM straddle entered at the **combined ask**.
- Exited at the **first permitted post-event combined bid** snapshot.
- Report **spread-aware net return**.
- **No direction signal.**

---

## 7. Minimum sample and decision rule

- **No scientific or trading verdict before 75 eligible events.**
- Before 75 events, report **only** coverage, data quality, timing integrity, and descriptive input
  distributions.

**Primary success requires all four:**

1. At least **2%** chronological OOS MAE improvement versus the options-only baseline.
2. **Block-bootstrap 95% interval** for the paired improvement **entirely above zero**.
3. **Positive Spearman** association between attention dislocation and excess realized move.
4. **No individual ticker supplies more than 10%** of eligible events.

**These gates are not altered after observations accumulate.**

---

## 8. Collection-stage prohibitions

While collecting, the system must not:

- compute any return, or open any post-event price;
- inspect any post-announcement outcome;
- call any trading, account or order endpoint;
- place or simulate an order;
- treat Alpha Vantage EPS fields as an outcome or as point-in-time analyst data (Alpha Vantage
  supplies **calendar dates only**);
- substitute a scraped website for a missing options provider;
- print, serialize, hash, partially reveal or commit a credential value;
- commit a raw provider response (raw bodies stay repository-external or gitignored).

**Refusal rules:** duplicate `(ticker, event_date, provider, quote_timestamp)` identities; option
quotes timestamped **after** the known announcement time; missing or crossed bid/ask markets.

The committed manifest is **sanitized and append-only**: permitted fields plus raw-response hashes.
