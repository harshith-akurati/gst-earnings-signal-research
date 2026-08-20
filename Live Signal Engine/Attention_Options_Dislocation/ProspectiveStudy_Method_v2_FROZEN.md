# Prospective Study — Method v2 (FROZEN)

**Status:** FROZEN on commit. This is a **new frozen file**, not an edit to
`FROZEN_DESIGN_v1.0.md` or to any v1 provenance record. v1 remains byte-identical and in force for
everything v2 does not explicitly supersede.

**Frozen before:** any v2 Trends request, any v2 capture, any v2 observation, and any analysis of any
kind. No outcome has been opened. Nothing in this document was chosen with knowledge of any v2 result.

**Authored:** 2026-08-20, after the ROST T−1 failure of 2026-08-19 and its evidence-only post-mortem
(`External_Scrutiny_Audit_2026-08-20/ROST_T1_COLLECTOR_POSTMORTEM_2026-08-20.md`, branch
`phase5-external-scrutiny-audit`).

---

## 1. Applicability, and the non-retroactivity rule

- **v1 governs ROST (`schedule_event_id` `c547a012b1c7312c1053c5369a3d5d52`).** The ROST T−1 leg was
  invalidated under v1's no-retry rule. **It stays invalidated.** v2 does not repair it, re-run it,
  re-query it, or reinterpret it. The scheduled T0 capture of 2026-08-20 remains under v1.
- **v2 governs every event whose schedule record is written after v2's commit timestamp.** No event
  already scheduled under v1 is migrated to v2.
- **No retroactive application, in either direction.** No v1 observation is re-evaluated under v2, and
  no v2 observation is compared against a v1-era standard.
- Where v2 is silent, **v1 controls**.

---

## 2. Root cause this method fixes

The ROST T−1 issuer query `Ross Stores, Inc. stock` returned `Refused: empty Trends frame` in ~2
seconds. The ticker query `ROST stock` succeeded **1–2 seconds later**, same process, same session,
identical `timeframe`/`geo`/`gprop`/`cat`.

Ruled out by that evidence: **throttling** (a rate limit would strike the later request, not the
earlier), **transport failure** (a response was received and parsed into a DataFrame), and a
**pytrends defect** (an empty frame is pytrends correctly reporting that Google returned no series).

**Punctuation is explicitly ruled out as the mechanism.** This repository has previously issued
successful Trends queries containing punctuation — the restaurant pilot's frozen queries include
`McDonald's` and `Domino's Pizza`, both with apostrophes, and both returned data. An apostrophe is at
least as encoding-hostile as a comma or a period. pytrends passes the keyword through
`build_payload`, which JSON-encodes it; no manual URL construction occurs in the collector.

**The actual cause is the phrasing.** `Ross Stores, Inc. stock` is a *legal registrant name* with a
suffix, not a string people type into Google. It falls below Trends' minimum-volume threshold, and
Trends suppresses the series entirely. This is **deterministic, not transient**: the same string
returns empty on every attempt, so no retry policy can recover it.

The defect therefore originates in v1's `QUERY_IDENTITY_RULE_FROZEN`, whose clause 1 derives the
query from the official issuer display name and whose clause 5 preserves source spelling and
punctuation. Applied faithfully — and it was — that rule converts securities-filing prose into a
search query.

---

## 3. Issuer-query construction rule (supersedes v1 `QUERY_IDENTITY_RULE_FROZEN`)

Applied **uniformly and deterministically to every issuer**. No per-ticker hand-tweaks, no judgment
calls, no exceptions list. The transformation is a pure function of the source string.

**Input.** The issuer display name from the official issuer investor-relations earnings announcement;
failing that, the SEC registrant name associated with the event filing. (v1 clauses 1–4 are retained
unchanged; only the *formatting* of the resulting query changes.)

**Transformation, in this exact order:**

1. Remove any security-description tail: `Common Stock`, `Class A/B/C Common Stock`,
   `Ordinary Shares`, `American Depositary Shares`, `American Depositary Receipts`,
   `New York Registry Shares`, `Subordinate Voting Shares`, and any parenthetical suffix such as
   `(DE)` or `(Ireland)`.
2. Remove trailing legal-entity suffixes, repeatedly, until none remains:
   `Inc`, `Inc.`, `Incorporated`, `Corp`, `Corp.`, `Corporation`, `Co`, `Co.`, `Company`,
   `Ltd`, `Ltd.`, `Limited`, `plc`, `PLC`, `N.V.`, `NV`, `S.A.`, `SA`, `A.G.`, `AG`, `LLC`, `L.P.`,
   `Holdings`, `Holding`, `Group`, `Trust`.
3. Remove any comma that immediately precedes a removed suffix, then strip trailing commas,
   periods and whitespace.
4. Collapse internal runs of whitespace to a single space.
5. **Preserve all remaining internal punctuation** — apostrophes, ampersands, hyphens and periods
   inside the retained name are kept exactly. They are demonstrably safe (see section 2) and removing
   them would corrupt names such as `Lowe's` or `Procter & Gamble`.
6. Append a single space and the literal token `stock`.

**Worked examples (illustrative of the rule, not a lookup table):**

| Source issuer name | v1 query (failed) | v2 query |
|---|---|---|
| `Ross Stores, Inc.` | `Ross Stores, Inc. stock` | `Ross Stores stock` |
| `Advanced Micro Devices, Inc.` | `Advanced Micro Devices, Inc. stock` | `Advanced Micro Devices stock` |
| `Booking Holdings Inc.` | `Booking Holdings Inc. stock` | `Booking stock` |
| `ASML Holding N.V. New York Registry Shares` | (n/a) | `ASML stock` |
| `Lowe's Companies, Inc.` | (n/a) | `Lowe's stock` |

**The ticker query is unchanged from v1:** `<TICKER> stock`.

**Both queries remain separate one-keyword requests. Batching remains prohibited.**

---

## 4. Pre-flight query resolvability gate (new in v2)

Section 3 makes the query *plausible*. It cannot make it *guaranteed* — no rule can, because the
volume threshold is Google's and is not published. v2 therefore verifies rather than assumes.

**At enrolment, before an event is scheduled**, each of the event's two queries is issued once
against the standard window. A query is **resolvable** only if it returns a non-empty frame
containing the query column with at least 52 complete weekly observations plus the target week — the
same data sufficiency the z-score requires.

- If **both** queries resolve, the event is enrolled and its T−1/T0 captures are scheduled.
- If **either** query does not resolve, the event is **not enrolled**, and a record of type
  `EVENT_INELIGIBLE_QUERY_UNRESOLVABLE` is appended to the ledger naming the ticker, both query
  strings, and which slot failed.

**Why this gate exists.** The ROST failure mode is deterministic per issuer: a below-threshold name
query fails at T−1 and at T0, this quarter and every future quarter. Without this gate such issuers
would fail silently and repeatedly, and — because a name query falls below the volume floor precisely
when few people search that company — the cohort would accumulate with **low-attention issuers
systematically deleted from a study about attention**. That is selection on the study's own
predictor, and it is not correctable after the fact.

The gate does not prevent that exclusion. **It makes it visible, counted, and reportable**, so the
realised universe can be compared against the intended one. The count of
`EVENT_INELIGIBLE_QUERY_UNRESOLVABLE` records is a required field in any coverage report.

**The pre-flight request is an enrolment check, not an observation.** Its values are never used as a
predictor, never enter a z-score used in analysis, and are recorded as
`record_type: TRENDS_PREFLIGHT` with `is_observation: false`.

---

## 5. Retry policy (supersedes v1 `retry_policy: NONE`)

**Exactly one retry per query per capture day. No more, under any circumstance.**

1. **At most one retry** per (event, retrieval_date, query_slot). A retry that fails ends that query
   for that day. There is no second retry, no exponential backoff, no escalation.
2. **Minimum 60 seconds** must elapse between the end of the failed attempt and the start of the
   retry. Longer is permitted; shorter is a violation and the retry must be refused.
3. **Same capture day only.** The retry must occur on the same `retrieval_date`, and must still fall
   inside the frozen `15:45 ET ± 10 minutes` window. v1's timing window is **not loosened**. If the
   window would be exceeded, no retry is attempted and the query fails for that day.
4. **The retry is logged as a retry.** Its ledger record carries `attempt: 2` and
   `is_retry: true`, and the originating record carries `retried: true`. The `request_id` includes
   the attempt number, so attempts 1 and 2 are distinct identities and the duplicate-identity guard
   does not block a legitimate retry.
5. **Retried observations are distinguishable in analysis.** Any event whose final value depended on
   a successful attempt 2 is flagged `contains_retried_capture: true` at the event level. Any
   analysis reporting results must also report the count of such events, and must be reproducible
   with them excluded.
6. **A retry is only permitted for a failure that could plausibly be transient** — a transport error,
   a timeout, or an HTTP 429. **An empty frame is NOT retried**, because section 2 establishes it is
   deterministic. An empty frame fails the query immediately and finally for that day.

Clause 6 is the point of the whole section. Retries exist for the failure modes the ROST post-mortem
*ruled out*, not for the one it confirmed.

---

## 6. Carried forward from v1, unchanged

Restated so that v2 is readable standalone. Each item is v1 behaviour and is **not** modified.

- **Two capture days per event: T−1 and T0.** Both required.
- **Both queries required at both captures.** `both_queries_required: true`,
  `both_days_required: true`.
- **No substitution and no fallback.** `one_query_fallback: false`. A missing query is never replaced
  by the other query, by a prior week, by an interpolated value, or by zero.
- **Any missing required capture invalidates the observation**, and the invalidation is logged as
  such. A partially captured event is never partially used.
- **z-score arithmetic unchanged:** `z = (target − mean(previous 52 complete weekly values)) /
  sample sd(previous 52)`, `ddof = 1`, baseline excludes the target week, no winsorisation, no
  clipping, no transformation, no rounding before calculation; zero sd invalidates the query.
- **Complete-week rule unchanged:** weekly resolution required, partial rows rejected, a row retained
  only when `week_start + 6 days <= cutoff`, no interpolation, zero is a valid value and is not
  missing.
- **Aggregation unchanged:** `daily_composite = (z_ticker + z_issuer) / 2`;
  `gst_zscore = (composite_T−1 + composite_T0) / 2`.
- **Stability diagnostic unchanged:** `stability_gap = abs(composite_T−1 − composite_T0)`,
  descriptive only, cannot change any predictor or eligibility decision.
- **Request parameters unchanged:** `geo=US`, `gprop=""`, `cat=0`, weekly granularity expected,
  730-day window ending at the cutoff, no topic IDs, no related-query or spelling substitution.
- **Timing window unchanged:** 15:45 ET ± 10 minutes.
- **Search information must end no later than T−2 calendar days.** Never use a post-release value to
  construct a pre-release feature.
- **All collection-stage prohibitions in `FROZEN_DESIGN_v1.0.md` §8 remain in force**, including: no
  return computed, no post-event price opened, no outcome inspected, no order placed or simulated, no
  credential printed or committed, and no raw provider response committed.

---

## 7. Universe (supersedes `FROZEN_DESIGN_v1.0.md` §2 only as to breadth)

v1 §2's *principles* are retained in full: an objective frame, never hand-picked or generated;
official sources only; deduplicated by issuer; and **no company excluded for any observed return,
search value, implied move or strategy result**.

v2 widens the frame while preserving reproducibility:

- **The universe is the union of dated official index constituent snapshots**, each recorded with its
  source URL, retrieval date and SHA-256.
- Currently constituted from:
  - the **official Nasdaq-100 constituent source** (snapshot retrieved 2026-08-18, response
    sha256 `dbdb857b6bb3202ed8d61a4d66cecc81ef2d964f1c2b69abe771f2f2ddcb5982`, 101 issuers after
    issuer deduplication); and
  - the **iShares S&P 100 (OEF) holdings file** as a **disclosed identity-only proxy** for the S&P
    100 investable universe — explicitly *not* the index provider's canonical constituent list, and
    never described as one (snapshot dated 2026-08-13, 101 equity tickers).
- Union after deduplication: **169 issuers** (33 overlap).
- **A generated ticker list remains prohibited.** "Any US-listed ticker with a confirmed earnings date
  and listed options" is not adopted, because membership would depend on what a vendor happened to
  publish at scan time and could not be reconstructed later from a fixed source.
- Adding a further index snapshot later is permitted **only** by a new dated frozen amendment
  committed before the added issuers' events are enrolled.
- Permitted exclusions are unchanged and exhaustive: not U.S.-listed; not an operating company;
  no listed options; issuer duplication.

---

## 8. Event eligibility and scheduling

- **Prospective events only.** No historical event is enrolled.
- **Session mapping unchanged from v1:** AMC → option snapshot on the announcement trading day;
  BMO → snapshot on the preceding trading day; an intraday release is **excluded**.
- **An event with unknown session timing is not eligible and is not scheduled.** It may become
  eligible if the session is later published or confirmed, provided that occurs before T−1.
- **Vendor calendar dates remain `SCHEDULING_INPUT_UNVERIFIED`.** Timing must ultimately be verified
  against an issuer release or SEC filing before the event's observation is treated as valid.
- **Calendar horizon: next 90 days**, unchanged.

---

## 9. What v2 does not change

v2 is a **collection** method. It sets no hypothesis, no gate, no threshold, no metric and no decision
rule, and it does not alter the minimum sample. Those live in
`FROZEN_DESIGN_v1.0.md` §6–§7 and in the accompanying pre-registration
(`ProspectiveStudy_PreRegistration_v1.0_FROZEN_2026-08-20.md`). In particular, the verdict gate
remains **75 eligible events** and is not modified here.

---

## 10. Implementation status at freeze time

Recorded so that the freeze is not mistaken for a deployment.

- The v1 collector `tools/collect_attention_options_snapshot.py` is **hardcoded to a single event**:
  `TRENDS_QUERIES` holds literal ROST strings, `TRENDS_SCHEDULE` holds literal dates, and
  `trends_request_id()` embeds the literal `"ROST"`. It **cannot** capture any other ticker.
- **No v2 capture has been scheduled or armed**, and no Windows scheduled task points at a v2
  collector, because no v2 collector exists yet.
- Implementing v2 requires, at minimum: event-parameterised queries and schedule; an attempt number
  inside `request_id`; the section 4 pre-flight gate; and the section 5 retry policy with its
  transient-only restriction.
- **This document is frozen first, deliberately.** The implementation is written against it, not the
  other way round.
