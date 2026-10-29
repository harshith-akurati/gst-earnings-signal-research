# DELL registry amendment — CONTINGENCY DRAFT, NOT WARRANTED ON CURRENT EVIDENCE

**Status:** `DRAFT_UNSIGNED_UNAPPLIED`. **The registry was not altered.**
**Authored:** 2026-08-29.

---

## 1. Why this amendment is drafted but NOT recommended

The review finding asked me to classify DELL `REGISTRY_VERIFICATION_PROVENANCE_CONFLICT` **if** it is
marked verified *without directly observed primary-source evidence*, and to draft the amendment moving
it to `pending`.

**Read-only inspection of the registry shows that condition is FALSE.** The classification is
therefore **not** applied, and this amendment is **not** warranted on current evidence. It is drafted
only so that a reviewer who disputes the human observation has an exact instrument ready.

## 2. What the registry actually records

| Field | Value |
|---|---|
| `row_id` · `row_type` | `EVT-DELL-FY27Q2-ERN-REG-001` · `REGISTRATION` |
| `verification_status` | `verified` |
| **`verified_by`** | **Harshith Akurati — a named human** |
| `source_type` | `company_ir_events_calendar` — on the permitted list |
| `source_url` | `https://investors.delltechnologies.com/news-events/upcoming-events` |
| `source_title` | *Upcoming Events \| Dell Technologies* |
| **Observed text** | event title *"Dell Technologies Fiscal Year 2027 Second Quarter Results"*, displayed as **"Sep 3, 2026 at 3:30 PM CDT"** |
| `source_retrieved_at_utc` | `2026-08-07T06:10:27+00:00` |
| `verified_at_utc` | `2026-08-07T06:14:40+00:00` |
| `earnings_date` · session | **2026-09-03** · **AMC** |
| `expected_response_session` | 2026-09-04 |
| Amendments | **none** — the effective row is the base row |

The notes record that the source was **manually observed in a browser by the named verifier**, that a
screenshot is held as supplementary evidence, and — explicitly — that *"no search snippet, third-party
calendar, historical precedent or cached assumption was used as the source of record."*

## 3. The automated-retrieval failure is not contrary evidence

The registry records that **eight** direct fetch attempts against
`investors.delltechnologies.com` and `delltechnologies.gcs-web.com` failed from the automation host
(`ConnectionResetError WinError 10054`, read timeouts). My own two `WebFetch` attempts on 2026-08-28
and 2026-08-29 also timed out.

**That is an environmental limitation of the automation host, not evidence about the issuer page.**
The cohort protocol requires a source *"directly fetched **or directly observed by a named human**"*.
It was directly observed by a named human. An assistant's inability to reach a host does not
invalidate a person having read it.

## 4. Independent verification of the mechanical claims

Reproduced with the production calendar, from enrollment metadata only:

| Claim | Verification |
|---|---|
| 3:30 PM CDT → `2026-09-03T20:30:00Z` | consistent (CDT = UTC−5) |
| XNYS close 2026-09-03 | `2026-09-03T20:00:00Z` |
| Release after close → **AMC** | `20:30Z > 20:00Z` — **AMC correct** |
| Derived anchor | `previous_session(2026-09-03)` = **2026-09-02** |
| Derived D1 | `compute_expected_next_full_trading_session_xnys` = **2026-09-04** |
| Registry `expected_response_session` | `2026-09-04` — **matches** |

The AMC classification is mechanical, not behavioural, and Dell's historical cadence was explicitly
not used.

## 5. Correction to my own earlier packets

Packets v0.1–v0.3 stated DELL's candidate date was **2026-09-01**, taken from a search-engine result
title, and treated the issuer page as unretrieved.

**Both were wrong.** The registered, human-observed date is **2026-09-03** (a Thursday; 2026-09-01 was
a Tuesday). A search snippet was never a source of record, and I never cross-read the registry row's
enrollment metadata before asserting a universe-wide "no primary-source-confirmed event" conclusion.
**Those packet statements are withdrawn.** Nothing in the registry was changed to reconcile them.

## 6. How the progress reporter produced `UNDETERMINED_REQUIRES_OUTCOME_CAPTURE`

Under the code as it stood, `classify()` required, in order: `row_type == REGISTRATION` →
`verification_status == verified` → registered session ∈ {BMO, AMC}. Only a row passing **all three**
fell through to `UNDETERMINED_REQUIRES_OUTCOME_CAPTURE`, which meant *"enrolled, but S-3…S-6 need
capture evidence this tool will not open."*

**So that output was itself evidence that DELL is a verified AMC registration** — the reporter could
not have emitted it otherwise. I read it at the time as an opaque placeholder rather than as the
positive signal it was.

*(The reporter has since been corrected on branch `hyp01-prospective-readiness-20260828`: it no longer
presents unevaluated state as an eligibility count, and reports registered session values
descriptively rather than as terminal dispositions.)*

## 7. The contingency amendment — unsigned, unapplied

Apply **only** if a reviewer determines the human observation is unreliable. It is append-only: the
base row's bytes are never rewritten.

```json
{
  "row_type": "AMENDMENT",
  "amends_row_id": "EVT-DELL-FY27Q2-ERN-REG-001",
  "event_id": "EVT-DELL-FY27Q2-ERN",
  "ticker": "DELL",
  "fiscal_period": "FY27Q2",
  "earnings_date": "2026-09-03",
  "earnings_datetime_utc": "2026-09-03T20:30:00+00:00",
  "release_market_session": "AMC",
  "source_url": "https://investors.delltechnologies.com/news-events/upcoming-events",
  "source_title": "Upcoming Events | Dell Technologies",
  "source_type": "company_ir_events_calendar",
  "source_retrieved_at_utc": "2026-08-07T06:10:27+00:00",
  "verification_status": "pending",
  "verified_at_utc": "<TO BE SET AT SIGNATURE>",
  "verified_by": "<NAMED HUMAN — TO BE SET AT SIGNATURE>",
  "notes": "CONTINGENCY AMENDMENT. Moves verification_status from verified to pending pending re-observation of the issuer Upcoming Events page. This does NOT assert that the 2026-08-07 observation was wrong; it records that a reviewer elected to re-verify before the event enters collection. Identity fields are unchanged: event_id, ticker and fiscal_period are identical to the base registration, so this is a status amendment and not an identity change. expected_response_session is recomputed mechanically by amend_event() from the unchanged corrected values; it is never supplied by the caller. No pre-event, market, attention or outcome data was inspected."
}
```

**It must be written through `HumanVerifiedEventRegistry.amend_event()`**, never by editing
`registry.jsonl` — that function recomputes `expected_response_session` and appends without rewriting
prior bytes.

## 8. Recommended action

| Option | When |
|---|---|
| **Take no registry action** *(recommended on current evidence)* | The row is verified by a named human against a permitted source, with observed text, timestamp and screenshot held. |
| Re-verify and, if it fails, apply §7 | A reviewer disputes the observation or wants a second observation before collection opens. |
| Apply §7 unconditionally | **Not recommended** — it would downgrade a properly evidenced registration on the strength of an automation-host network failure. |

| Field | Entry |
|---|---|
| Reviewer decision | `____________` |
| If re-verifying: verifier name · timestamp · observed text | `____________` |
| Approver 1 · signature · timestamp | `____________` |
| Approver 2 · signature · timestamp | `____________` |
