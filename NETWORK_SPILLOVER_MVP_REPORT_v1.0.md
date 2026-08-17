# Network-Spillover MVP — Result

`EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY`. No HYP-01 lock, registry, F5 artifact,
universe constant or prospective observation was read or modified. No quantum kernel is implemented.

## Decision

# `DATA_UNAVAILABLE`

**Zero anchor events were evaluated. No spillover return is reported, because none could be computed
honestly.**

## Why

The design requires reading the anchor's reaction **through 09:35 ET** and entering neighbors **no
earlier than the 09:40 ET bar**. That is not derivable from daily data. Every source available in
this environment was probed:

| Source | Result |
|---|---|
| Public chart endpoint, 5-minute | **~59 days only** — 30d → 1,561 bars, 59d → 3,043 bars, **90d → HTTP 422**, 400d → HTTP 422 |
| This repository | daily **`Date, Open, Close`** only — no intraday bars anywhere |
| Alpaca (provider already implemented) | `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` **not present** in the environment; no credential file |
| Polygon | HTTP 401 Unauthorized — key not configured |
| Alpha Vantage | demo key rejected — real key not configured |
| Stooq | daily / weekly / monthly only, no intraday |
| `yfinance` | returns 0 bars at every interval here, including daily — its own parsing is broken in this environment, independent of the 60-day cap |

The anchor earnings history this study needs runs back to **2021**. Roughly 59 days of 5-minute data
cannot support it. Even inside that window only about one earnings event per anchor could fall, which
would be `INSUFFICIENT_ANCHOR_EVENTS` in its own right — but the binding constraint is the data, so
the label is `DATA_UNAVAILABLE`.

## What was NOT done

**Daily open/close was not substituted for intraday bars.** Doing so would mean reading the anchor's
direction from the opening gap and then entering neighbors at that same open — the price that formed
the signal would also be the assumed fill. That is an impossible trade, and it would have produced a
confident-looking spillover number that no one could have earned. The prohibition is enforced in code
(`refuse_impossible_substitution()`), not only in prose.

No entry time, exit window, cost or threshold was searched. No model was fitted. No neighbor return
was computed at all.

## What was delivered

The frozen, pre-retrieval pieces stand, so that a later run with intraday access changes only the
data layer:

- **`Live Signal Engine/Network_Spillover_MVP/network_relationships_v1.0.csv`** — 42 rows,
  3 anchors × 14 neighbor relationships, columns `anchor, neighbor, edge_type, graph_distance,
  evidence_status`. All six permitted edge types are used: `COMPETITOR`, `SUPPLIER_FOUNDRY`,
  `EQUIPMENT`, `NETWORKING`, `SERVER_INTEGRATOR`, `CUSTOMER_DEMAND`. Every row is marked
  **`EXPLORATORY_STATIC`**: these are labels, **not** evidence of causal supply-chain exposure, and
  **none was inferred from returns**.
- **`tools/run_network_spillover_mvp.py`** — the executable design: 09:35 reaction cutoff, 09:40
  earliest entry, three fixed exits, 10 bps round-trip cost, SMH benchmark with SPY as a documented
  sensitivity, and the strictly pre-event GST z-score from PR #24. The overlapping historical spike
  classification is never used as pre-event evidence.

## The unanswered question

Whether an anchor's observable post-earnings reaction predicts delayed abnormal returns in linked
firms **remains untested**. This report is not evidence for or against it.

## What would unblock it

1. `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` for the Alpaca provider already implemented in
   `gst_market_response/alpaca_provider.py`.
2. Any keyed intraday vendor (Polygon, Tiingo, Alpha Vantage, Finnhub).
3. A committed historical 5-minute bar archive for the anchors, neighbors, SMH and SPY.

No credential value was read, printed, logged or committed at any point.

Reproduce the probe: `python tools/run_network_spillover_mvp.py`
