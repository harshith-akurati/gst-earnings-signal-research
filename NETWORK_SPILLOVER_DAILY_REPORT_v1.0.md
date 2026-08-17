# Daily-Delay Network Spillover — Results

`EXPLORATORY_RETROSPECTIVE_NETWORK_DEVELOPMENT_ONLY`. No HYP-01 lock, registry, F5 artifact,
universe constant or prospective observation was read or modified.

## Decision

# `NO_DAILY_NETWORK_SPILLOVER`

**63 usable anchor events** (21 each: NVDA, AMD, INTC), 2021-01-15 → 2025-11-20, from SEC 8-K item
2.02 filings. Zero dropped.

| Exit | Gross | **Net (10 bps)** | 95% CI (net) | t | Hit rate |
|---|---|---|---|---|---|
| close(T+1) | −0.1040% | **−0.2040%** | [−0.338, −0.070] | −2.98 | 34.9% |
| close(T+3) | −0.2547% | **−0.3547%** | [−0.676, −0.034] | −2.17 | 42.9% |

Signed spillover is **negative** at both exits. There is no positive spillover to trade, and the
strategy loses more than costs alone.

### The naive interval and the permutation test disagree — the permutation wins

| Comparator | Result |
|---|---|
| **Randomized anchor-sign permutation** (10,000 draws, event level) | observed −0.1040%, permuted mean −0.0014%, permuted SD 0.0688%, **two-sided p = 0.1327** |
| All anchor events, net | −0.2040% |
| No trade | 0.0000% |
| SMH | neighbor returns are already benchmark-adjusted against it |

The naive t of −2.98 on the net series looks decisive, but nearly all of it is the fixed 10 bps
subtraction. On the **gross** series the naive CI already straddles zero ([−0.238, +0.030], t = −1.52),
and the permutation test — which respects the event-level sign structure — returns **p = 0.13**. The
honest reading is **no reliable directional spillover in either direction**, not a tradable short.

## Is the direction observable before entry?

**Yes, by construction.** The anchor's benchmark-adjusted return through close(T) is fully known after
that close; neighbors are entered at **open(T+1)**, the next session's opening order. Neighbor open(T)
is never used. This is the executable timing that the intraday MVP (PR #25) could not obtain data for.

## Does GST strengthen the spillover?

**Cannot be determined from this sample.** Under the threshold frozen before outcomes (`z ≥ 1.0`) only
**2 of 42** GST-covered events qualify:

| Group | n | Net mean | 95% CI |
|---|---|---|---|
| High GST (z ≥ 1.0) | **2** | −0.6878% | [−1.653, +0.278] |
| Low GST | 40 | −0.0522% | [−0.191, +0.086] |

**n = 2 supports no conclusion**, and I did not move the threshold after seeing that — doing so would
be threshold searching. The continuous view is the more informative one and points the same way as the
split: slope **−0.1444 pp per z**, correlation **−0.2776** over 42 events. Higher pre-event attention
is associated with *more negative* signed spillover, not more positive.

**Coverage limit:** weekly GST exists for **NVDA and INTC only**. **AMD has none**, so its 21 events
enter the spillover analysis but not any GST comparison.

The rarity of high-z events is structural, not a bug: the pre-event GST z uses only weeks **closing
before** the event, which deliberately excludes the attention spike that the earnings release itself
produces.

## By anchor

| Anchor | n | Net mean | 95% CI | t |
|---|---|---|---|---|
| **AMD** | 21 | **−0.4470%** | [−0.707, −0.187] | −3.37 |
| NVDA | 21 | −0.1252% | [−0.378, +0.128] | −0.97 |
| INTC | 21 | −0.0398% | [−0.173, +0.094] | −0.58 |

Only AMD is individually negative beyond its interval; NVDA and INTC straddle zero. One of three
anchors driving the pooled result is not a network effect.

## Descriptive only — neighbor level

These rows are **not independent observations**; primary inference is anchor-event level. 1,512
neighbor rows at the close(T+1) exit.

| Edge type | Rows | Mean signed |
|---|---|---|
| **COMPETITOR** | 21 | **+0.2215%** |
| NETWORKING | 126 | +0.0693% |
| SUPPLIER_FOUNDRY | 42 | −0.0159% |
| EQUIPMENT | 189 | −0.0267% |
| CUSTOMER_DEMAND | 252 | −0.0771% |
| **SERVER_INTEGRATOR** | 126 | **−0.5307%** |

Best `COMPETITOR` (+0.2215%, only 21 rows), worst `SERVER_INTEGRATOR` (−0.5307%). By graph distance:
distance 1 = −0.166% (378 rows), distance 2 = −0.042% (378 rows) — the *closer* relationships are more
negative, the opposite of a decaying-spillover story.

## Older vs newer

Split at 2023-05-03: older 32 events **−0.1477%** net, newer 31 events **−0.2622%** net. No sign of an
effect that existed and decayed; it is absent in both halves.

## SPY sensitivity

Against SPY instead of SMH: gross −0.2044%, CI [−0.473, +0.064]. Same conclusion; the sector benchmark
choice does not rescue a signal.

## What was not done

63 events survived, so machine-learning models were permitted (threshold 30), but this brief's report
is the fixed event-level analysis and none was fitted — no feature search, no hyperparameter tuning,
no alternative entry, exit, cost or threshold. The relationship table is the same frozen, exploratory,
**static** map as PR #25: edge types are labels, **not** evidence of causal supply-chain exposure, and
none was inferred from returns.

## Scope

This tests one delayed daily rule on three semiconductor anchors and twelve linked firms over
2021–2025. It does not test intraday spillover — that remains blocked on data (PR #25) — and a
negative daily result does not establish that no faster spillover exists.

Reproduce: `python tools/run_network_spillover_daily_delay.py`
