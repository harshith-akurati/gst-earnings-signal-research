# D1 latest-permissible-capture rule — recommendation

**Status:** `DRAFT_UNSIGNED`. **This is a scientific/operational recommendation requiring two human
approvals. It is not adopted and is not in force.**
**Authored:** 2026-08-29, before any eligible HYP-01 event or outcome exists.

---

## The gap

Only a **lower** bound on D1 capture time exists:

```
operations_plan.SessionPlan.earliest_provider_retrieval_utc
  = D1 session final expected bar start + ALPACA_MIN_END_AGE_MINUTES (15)
```

It is enforced in code (`JOIN_REFUSED_CAPTURE_BEFORE_PERMITTED_WINDOW`).

**No committed artifact states a latest permissible capture instant.** Searches for `latest`,
`deadline`, `max_age`, `staleness`, `not_after` and `expires` across the SPECs, the analysis lock, the
eligibility rules, the effective-lock report and the code return only option-quote-age and
methodology-version matches — neither governs D1 capture recency.

**Nothing was invented.** The adapter declares the gap and enforces no upper bound.

## Why an upper bound matters

Without one, a D1 capture performed arbitrarily late is indistinguishable from a timely one. Two
concrete risks:

1. **Silent repair.** A failed capture could be retried days later and recorded as if it had been
   collected on schedule.
2. **Revision exposure.** Market data vendors restate bars. The later the pull, the more the recorded
   value may reflect a restatement rather than what was observable at the response session.

## Recommended rule — R-D1

| # | Recommendation |
|---|---|
| **R-D1.1** | A successful D1 capture **must occur after** `sessions.D1.earliest_provider_retrieval_utc` (unchanged) **and before the open of the next full XNYS trading session after the D1 response session**. |
| **R-D1.2** | The upper bound is computed with the **production exchange calendar** — `next_session()` and `session_open_utc()`. Holidays, weekends and shortened sessions are handled by the calendar, never by arithmetic in the rule. |
| **R-D1.3** | A capture outside that window is **recorded as a failed capture** with its reason and timestamp. It is **never silently back-filled**, retried into the window, or relabelled as timely. |
| **R-D1.4** | If the provider is unavailable for the whole window, the event is recorded `D1_CAPTURE_FAILED_PROVIDER_UNAVAILABLE` — a **documented missing observation**, consistent with adopted **D4** (*a provider or schema failure is a documented missing observation; retrieval failure is never recorded as issuer-confirmed absence*). The event then fails S-4 or S-6 on the merits and is **not** eligible. It is not excluded from the cohort by fiat, and it is not re-attempted after the window. |
| **R-D1.5** | The rule is **prospective only**. It creates no deadline before its approval timestamp and reclassifies no earlier capture. |

### Worked illustration (calendar-derived, not a new rule)

For an AMC release on a Thursday with D1 on the Friday, the window opens ~10 minutes after the Friday
close and shuts at the **Monday** open — or the **Tuesday** open if the Monday is an exchange holiday.
The calendar decides; the rule never counts days.

## What R-D1 deliberately does not do

- It sets **no tolerance in hours or minutes.** The bound is a session boundary the calendar already
  defines, not an invented duration.
- It changes **no** outcome definition, gate, estimator or threshold.
- It does not license retrying a failed capture. R-D1.3 and R-D1.4 exist to prevent exactly that.

## Alternatives the signatories should weigh

| Option | Consequence |
|---|---|
| **Adopt R-D1** | Bounded, calendar-derived, no invented tolerance. Some legitimate captures may fail if operations slip past the next open. |
| **A longer bound** (e.g. D1+2 sessions) | More operational slack; more exposure to vendor restatement. |
| **No upper bound** (status quo) | No capture is ever late — and the two risks above stay unmitigated. |

**No option is preselected.**

## Signatures

| Field | Entry |
|---|---|
| Approver 1 name · signature · timestamp | `____________` |
| Approver 2 name · signature · timestamp | `____________` |
| Rule adopted: **R-D1 / longer bound / none / other** | `____________` |
| If other or longer — the exact bound and the instant it is measured from | `____________` |
| Artifact to be amended (a timing rule requires a dated SPEC amendment) | `____________` |
| Effective from | `____________` |
| Confirm: prospective only; reclassifies no earlier capture | `____________` |
