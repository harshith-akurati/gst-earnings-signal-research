# Attention–Options Dislocation — operations

Collection stage for the study frozen in `FROZEN_DESIGN_v1.0.md`, as amended by
`PROVIDER_AMENDMENT_2026-08-17_ALPACA.md`. **Read the frozen design first, then the amendment;
this file only says how to run the collector.**

Nothing here computes a return, opens a post-event price, or calls a trading endpoint. There is no
order code path.

## Commands

```
python tools/collect_attention_options_snapshot.py doctor
python tools/collect_attention_options_snapshot.py alpaca-check
python tools/collect_attention_options_snapshot.py universe
python tools/collect_attention_options_snapshot.py readiness
python tools/collect_attention_options_snapshot.py calendar
python tools/collect_attention_options_snapshot.py snapshot --ticker ZZZ --issuer "Zeta Systems" \
       --event-date 2026-08-19 --session AMC --timing-confirmed <issuer-release-or-SEC-url>
python tools/collect_attention_options_snapshot.py validate
```

| Mode | Does |
|---|---|
| `doctor` | Reports provider readiness. Presence only — never a credential value, length or prefix. |
| `alpaca-check` | **One** minimal Alpaca connectivity + schema-validation request, labelled `NON_EVENT_SYSTEM_VALIDATION_ONLY`. Writes to the provenance ledger, never to the research panel. |
| `universe` | Retrieves the universe from the official source hierarchy, hashes and timestamps it, keeps identity fields only. |
| `readiness` | Intersects the universe with the unverified Alpha Vantage calendar and reports the next required collection time. Collects nothing. |
| `calendar` | Next-90-day candidate earnings dates from Alpha Vantage. **Dates only.** |
| `snapshot` | Timestamped pre-event input snapshot. Refuses outside the 15:45 ET window, on the wrong snapshot day, without a provider credential, or without issuer/SEC-confirmed event timing. |
| `validate` | Re-checks stored records: schema, provenance, labels, timestamps, hashes, uniqueness, pre-event eligibility. |

## Provider (amended 2026-08-18) — MANUAL Cboe capture

Per `PROVIDER_AMENDMENT_2026-08-18_CBOE_MANUAL.md`, Alpaca is abandoned (HTTP 401, credentials
rejected) and **no further account, identity, credential or API-provider work will be attempted**.
The source is now the **official Cboe Delayed Quotes dashboard**.

> ## ⚠ BROWSER AUTOMATION, HTTP REQUESTS, SCRAPING AND PROGRAMMATIC CSV DOWNLOADING ARE PROHIBITED.
>
> Cboe permits a **person** to type a ticker and click **Download CSV**. Cboe's terms **explicitly
> prohibit automated extraction**. There is **no Cboe URL, HTTP client, browser driver, headless
> browser, scheduled fetch or retry loop anywhere in this repository, and none may be added.**
> The software only ever reads a file a human already saved to local disk.

Every accepted record is labelled **`CBOE_MANUAL_DELAYED_NON_EXECUTABLE`**. The **page-displayed
market-data timestamp — not the download time — is the information cutoff**; both are recorded
separately. Delayed quotes may test forecast improvement against an options-implied benchmark; they
**cannot** establish executable bids/asks, spread-adjusted P&L or tradeable options alpha, and the
importer refuses to emit any of them.

### Human runbook

1. **Confirm the earnings date and AMC/BMO timing** from the issuer's official investor-relations
   page or an SEC filing. A vendor calendar is `SCHEDULING_INPUT_UNVERIFIED` and is never sufficient.
2. At the frozen collection time (**15:45 ET** on the snapshot day), **manually open** Cboe's
   delayed-quotes page in a browser: <https://www.cboe.com/delayed_quotes/>
3. **Manually type the ticker** into the page.
4. **Select the required expiration** (the first expiration strictly after the event) and a
   **near-the-money strike range** around the current underlying price.
5. Click **"Download CSV."**
6. **Immediately record two things**: the **displayed quote timestamp** shown on the page, and the
   **UTC download timestamp**.
7. Run the local importer (below).
8. **Preserve the downloaded file outside Git.** The importer copies it to the repository-external
   cache; never commit a raw file.
9. **Verify the result**: the importer either appends exactly one valid observation or refuses with
   an explicit reason. A refusal is a real answer — do not retry with looser inputs.

### Importer

```
python tools/collect_attention_options_snapshot.py cboe-import        --ticker TICKER --event-date YYYY-MM-DD --event-session AMC        --retrieved-at 2026-08-20T19:45:00Z --csv /path/to/manual_download.csv        --quote-timestamp "2026-08-20 19:40:00" --underlying-price 186.00        --timing-confirmed https://issuer.example/ir/press-release
```

It performs **no network access**. It records the filename, byte count and SHA-256 in the
append-only provenance ledger, applies the **already-frozen** expiration and nearest-strike rules and
the **unmodified** implied-move arithmetic, records the option and underlying timestamps separately,
and refuses on: wrong ticker, wrong event, missing calls or puts, duplicate contracts, crossed or
negative quotes, missing timestamps, stale data, wrong expiration, ambiguous ATM selection, retrieval
outside the frozen window, a displayed timestamp that does not precede its download, or unconfirmed
event timing.

## Provider history (amended 2026-08-17) — Alpaca, failed


Per `PROVIDER_AMENDMENT_2026-08-17_ALPACA.md`, the options provider is **Alpaca Paper Only** on its
free **`indicative`** feed. Tradier stays unavailable because its tokens require brokerage
onboarding with a real legal identity and a real SSN, and **no fabricated identity or third party's
SSN will be used to obtain market data**.

Every Alpaca option record carries **`ALPACA_INDICATIVE_NON_EXECUTABLE`**. The feed is **not**
consolidated OPRA execution-quality data: its option trades may be delayed and its quotes are
modified/indicative rather than the NBBO. These records may test whether attention improves
realized-move forecasting beyond an options-implied benchmark. They may **not** support any claim
about executable bids or asks, realistic spread costs, attainable straddle P&L, or tradeable
options alpha. The execution-economics stage is deferred with status
**`OPRA_EXECUTION_DATA_UNAVAILABLE`**, and the collector refuses to emit an executable price on an
indicative record.

Alpaca is reached through **market-data endpoints only**. The endpoint guard fails **closed**: a URL
must be on the market-data allowlist to be requested at all. Order, position, account and trading
endpoints are refused before any socket opens, and there is no order code path to disable.

## Credentials

Recognised: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`, `ALPHAVANTAGE_API_KEY`, `TRADIER_TOKEN`,
`TRADIER_SANDBOX_TOKEN`, `GOOGLE_TRENDS_ALPHA_KEY`.

Alpaca credentials are read **only** from `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`. Half a pair
is a configuration error, not an invitation to use a different provider. **A provider that is
selected and then fails is never retried against another provider** — the collector stops. No
website is scraped as a substitute.

Credential values are never printed, logged, serialized, hashed, partially revealed or committed,
and no fingerprint derived from one is either.

## Current status — 2026-08-17

| Provider | State |
|---|---|
| Alpaca Paper Only (`indicative` options) | **BLOCKED — HTTP 401, credentials rejected** |
| Alpha Vantage (calendar dates) | Key absent this session; the previously retrieved calendar is reused as an **unverified scheduling input** |
| Tradier real-time / sandbox | **Unavailable** — brokerage onboarding required; see the amendment |
| Google Trends alpha | **Absent** — public sampling only |

**`APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are both PRESENT but are rejected by the provider.**
`data.alpaca.markets` returns **HTTP 401** for the options snapshot endpoint, for the equity
market-data endpoint, and for the repository's own previously-proven bars path in
`gst_market_response/alpaca_provider.py` — which that module records as `LIVE_DIAGNOSTIC_PASSED` on
2026-08-04 with identical auth headers. An implementation defect in this study is therefore ruled
out: the credential pair itself is rejected, and this is not an options-entitlement problem.

**Options snapshots cannot begin until a working Alpaca credential pair exists.** That is the one
blocker. Because authentication failed, the live Alpaca response schema has **never been observed**;
the adapter is written to Alpaca's documented options-snapshot shape and is exercised only against
fixtures. It must be re-validated with `alpaca-check` the moment credentials work, and it will stop
with `PROVIDER_SCHEMA_INCOMPATIBLE` rather than bend the frozen formulas if the real schema differs.

### To enable collection

1. Issue a working Alpaca Paper key pair and set `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`.
2. Run `alpaca-check` and confirm HTTP 200 **and** that the frozen arithmetic is implementable.
3. Run `universe`, then `readiness`.
4. Confirm the event date **and** the AMC/BMO session against an issuer release or SEC filing.
5. Schedule the snapshot job for **15:45 ET** on that event's snapshot day.

## Universe

Official sources only, in order: the Nasdaq-100 official constituent source, then the official
Invesco QQQ holdings file as a **disclosed index proxy**. Scraped aggregator lists, generated ticker
lists and remembered lists are prohibited and have no code path. Retain U.S.-listed operating
companies with listed options, deduplicated by issuer. **No company is ever excluded for an observed
return, search value, implied move or strategy result.**

Only identity fields (`ticker`, `issuer_name`) are retained. **Weights and market values are never
retained.**

### Snapshot retrieved 2026-08-18T01:18:53Z

| Field | Value |
|---|---|
| Source | Nasdaq-100 official constituent source (**rank 1, primary — not the proxy**) |
| Kind | `OFFICIAL_INDEX_CONSTITUENTS` |
| URL | `https://api.nasdaq.com/api/quote/list-type/nasdaq100` |
| HTTP status | 200 |
| Bytes | 21,775 |
| SHA-256 | `dbdb857b6bb3202ed8d61a4d66cecc81ef2d964f1c2b69abe771f2f2ddcb5982` |
| Constituents (raw) | 102 |
| Constituents (deduplicated by issuer) | **101** |

The source host was corrected from `www.nasdaq.com` to `api.nasdaq.com` **before any universe
request was issued**. It is the same official Nasdaq constituent source; only the API host differs.
The Invesco QQQ proxy was **not** used and **not** requested, because the primary source succeeded.

### Calendar readiness — 2026-08-17 21:19 ET

Universe x the previously retrieved Alpha Vantage calendar (sha256
`cfd85d86c15d9d90df7f7c7f63a204298a4a316913154429869e5b1dfa52c1f2`) gives **35 candidate events**
inside the frozen 90-day horizon. Every one is `SCHEDULING_INPUT_UNVERIFIED`: the vendor supplies a
date but **not** the AMC/BMO session, so no snapshot day can be fixed yet. The earliest candidate is
**2026-08-19 (ADI)**.

**Next required collection time:** 2026-08-18 15:45 ET *if* that event is confirmed BMO, otherwise
2026-08-19 15:45 ET if confirmed AMC — and only once an issuer release or SEC filing fixes both the
date and the session.

## Data handling

- Raw provider responses stay **repository-external** (default `../gst-aod-cache`, override with
  `AOD_CACHE_DIR`). They are never committed.
- Two committed files, and they are not interchangeable:
  - `snapshot_manifest.jsonl` — the **research panel**. Sanitized, append-only, `RESEARCH` class
    only. It does not exist yet, because no legitimate observation has been collected.
  - `collection_provenance.jsonl` — **provenance only**, append-only. System-validation and
    universe records live here. The collector refuses to write a research record into it and
    refuses to point it at the manifest.
- **System-validation data can never enter the research panel.** The connectivity check is labelled
  `NON_EVENT_SYSTEM_VALIDATION_ONLY`, and both the class check and a label scan reject it.
- Provider **and** feed provenance are mandatory on every record; a record missing either is refused.
- Refused outright: duplicate `(ticker, event_date, provider, quote_timestamp)`; quotes timestamped
  at or after the announcement; captures outside the 15:45 ET window or on the wrong snapshot day;
  missing, crossed, stale, future-dated or empty (0/0) markets; call and put quotes that are not
  contemporaneous; records that fail cross-field consistency.
- A missing bid or ask is **never** replaced with the last price, and an empty two-sided quote is
  treated as a **missing market**, not as a price of zero.
- Alpaca's options snapshot does not supply **open interest**. Its absence is disclosed per record in
  `design_fields_absent` rather than imputed. It is not an input to the frozen arithmetic.

## Cadence, once unblocked

One public Google Trends sample **per query per day** — no repeated in-day loop, because Google may
cache and repeated sampling would measure the cache rather than stability. Repeated-sample stability
accumulates across distinct retrieval dates.

Vendor calendar dates are `SCHEDULING_INPUT_UNVERIFIED`. Event timing must ultimately be confirmed
against an issuer release or SEC filing before an event counts as eligible.

## Reporting limits

**No scientific or trading verdict before 75 eligible events.** Until then, report only coverage,
data quality, timing integrity and descriptive input distributions.
