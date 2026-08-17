# Attention–Options Dislocation — operations

Collection stage for the study frozen in `FROZEN_DESIGN_v1.0.md`. **Read the frozen design first;
this file only says how to run the collector.**

Nothing here computes a return, opens a post-event price, or calls a trading endpoint. There is no
order code path.

## Commands

```
python tools/collect_attention_options_snapshot.py doctor
python tools/collect_attention_options_snapshot.py calendar
python tools/collect_attention_options_snapshot.py snapshot --ticker ZZZ --issuer "Zeta Systems" \
       --event-date 2026-08-19 --session AMC
python tools/collect_attention_options_snapshot.py validate
```

| Mode | Does |
|---|---|
| `doctor` | Reports provider readiness. Presence only — never a credential value, length or prefix. |
| `calendar` | Next-90-day candidate earnings dates from Alpha Vantage. **Dates only.** |
| `snapshot` | Timestamped pre-event input snapshot. Refuses to run outside the prescribed window or without a Tradier credential. |
| `validate` | Re-checks stored records: schema, timestamps, hashes, uniqueness, pre-event eligibility. |

## Credentials

Recognised: `ALPHAVANTAGE_API_KEY`, `TRADIER_TOKEN`, `TRADIER_SANDBOX_TOKEN`,
`GOOGLE_TRENDS_ALPHA_KEY`.

`TRADIER_TOKEN` is preferred. Falling back to `TRADIER_SANDBOX_TOKEN` labels **every** record
`DELAYED_15_MINUTES`. **If neither exists the collector stops** — it does not scrape Cboe, Yahoo,
MarketChameleon or any other site as a substitute.

Credential values are never printed, serialized, hashed, partially revealed or committed.

## Current status

| Provider | State |
|---|---|
| Alpha Vantage (calendar dates) | **Available** |
| Tradier real-time | **Absent** |
| Tradier sandbox | **Absent** |
| Google Trends alpha | **Absent** — public sampling only |

**Options snapshots cannot begin until a Tradier token exists.** That is the one blocker.

### To enable collection

1. Create a Tradier developer account at <https://developer.tradier.com/>.
2. Set `TRADIER_SANDBOX_TOKEN` for delayed data, or obtain market-data entitlement and set
   `TRADIER_TOKEN` for real-time.
3. Re-run `doctor` and confirm a provider is selected.
4. Resolve the universe file (see below).
5. Schedule the snapshot job for **15:45 ET** on each event's snapshot day.

## Universe

Official sources only, in order: the Nasdaq-100 official constituent source, then the official
Invesco QQQ holdings file as a **disclosed index proxy**. Wikipedia, scraped aggregator lists and
generated ticker lists are prohibited. Retain U.S.-listed operating companies with listed options,
deduplicated by issuer. **No company is ever excluded for an observed return, search value, implied
move or strategy result.**

## Data handling

- Raw provider responses stay **repository-external** (default `../gst-aod-cache`, override with
  `AOD_CACHE_DIR`). They are never committed.
- The committed manifest is **sanitized and append-only**: permitted fields plus raw-response
  SHA-256 hashes.
- Refused outright: duplicate `(ticker, event_date, provider, quote_timestamp)`; quotes timestamped
  at or after the announcement; missing or crossed bid/ask markets.
- A missing bid or ask is **never** replaced with the last price.

## Cadence, once unblocked

One public Google Trends sample **per query per day** — no repeated in-day loop, because Google may
cache and repeated sampling would measure the cache rather than stability. Repeated-sample stability
accumulates across distinct retrieval dates.

Vendor calendar dates are `SCHEDULING_INPUT_UNVERIFIED`. Event timing must ultimately be confirmed
against an issuer release or SEC filing before an event counts as eligible.

## Reporting limits

**No scientific or trading verdict before 75 eligible events.** Until then, report only coverage,
data quality, timing integrity and descriptive input distributions.
