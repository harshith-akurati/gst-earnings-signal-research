# Prospective cohort protocol — v1.2 DRAFT

**Status:** `DRAFT_UNSIGNED`. **Not adopted. Not in force.**
**Authored:** 2026-08-29, before any eligible HYP-01 event or outcome exists (eligible count **0**).
**Supersedes:** nothing yet. v1.1 remains as written; **being pushed to a branch supersedes nothing.**

> A protocol becomes operative only when an independently authoritative instrument adopts its exact
> bytes and two named humans sign. Until then this document governs nothing.

---

## 0. What v1.2 corrects in v1.1

| # | v1.1 defect | v1.2 |
|---|---|---|
| 1 | Presents its rules as though in force while carrying `status: DRAFT` | Draft-versus-effective semantics stated explicitly in §1 |
| 2 | Implies supersession by existence | §1: supersession requires adoption, never a push |
| 3 | Implies events may already be eligible | §2: **zero** eligible events exist; nothing is grandfathered |
| 4 | Silent on DELL's actual state | §3 states it from the registry |
| 5 | The 60-event threshold is restated loosely | §4 cites the adopted lock as the only source |
| 6 | S-1 references a protocol version that the adopted lock does not name | §5 + the accompanying S-1 reference amendment |

## 1. Draft versus effective

| Term | Meaning |
|---|---|
| **DRAFT** | Committed, readable, and **binding on nothing**. |
| **ADOPTED** | An authoritative instrument records this document's exact SHA-256 and two named humans have signed. |
| **EFFECTIVE FROM** | The approval timestamp. **Never retroactive.** |

**No rule in this document may be cited as binding, may create a deadline, or may reclassify any past
event, unless and until it is adopted.** A prior draft is not superseded by a newer draft being
committed or pushed; it is superseded only when an adoption instrument says so.

## 2. Current cohort state — factual, not aspirational

| | |
|---|---|
| Eligible HYP-01 events | **0** |
| Enrolled registrations | **1** (DELL, see §3) |
| Observations collected | **0** |
| Events grandfathered into eligibility | **0 — none, ever** |

**v1.1's framing that events may already be eligible is false.** Eligibility is determined by the
S-1…S-8 ladder over collected evidence. No evidence has been collected, so no event is eligible.

## 3. DELL — actual registry state

From `Live Signal Engine/Market_Response_Event_Registry/registry.jsonl`, read as enrollment metadata
only:

| Field | Value |
|---|---|
| `row_id` / `row_type` | `EVT-DELL-FY27Q2-ERN-REG-001` · `REGISTRATION` |
| `verification_status` | `verified` |
| `verified_by` | **Harshith Akurati** (a named human) |
| `source_type` | `company_ir_events_calendar` (on the permitted list) |
| `source_url` | `https://investors.delltechnologies.com/news-events/upcoming-events` |
| Observed text | event title *"Dell Technologies Fiscal Year 2027 Second Quarter Results"*, displayed as **"Sep 3, 2026 at 3:30 PM CDT"** |
| `source_retrieved_at_utc` | `2026-08-07T06:10:27+00:00` (observed in a browser by the verifier) |
| `earnings_date` · session | **2026-09-03** · **AMC** |
| Derived anchor · D1 | **2026-09-02** · **2026-09-04** |
| Amendments | none |

**DELL is enrolled, and its enrollment is supported by directly observed primary-source evidence.**
The AMC classification is mechanical, not behavioural: 3:30 PM CDT = `2026-09-03T20:30:00Z`, strictly
after the XNYS close `2026-09-03T20:00:00Z`. Both were independently reproduced with the production
calendar.

**DELL is nonetheless NOT eligible and NOT grandfathered.** Enrollment is stage 1; eligibility
requires collected evidence through S-1…S-8, and no observation exists. If PRE_EVENT collection has
not opened by its anchor, the event is simply missed — never back-filled (§7).

**Correction to earlier external packets.** Packets v0.1–v0.3 described a DELL candidate dated
**2026-09-01** taken from a search-engine result title, and treated the issuer page as unretrieved.
Both were wrong: the registered, human-observed date is **2026-09-03**, and a search snippet was never
a source of record. Those packet statements are withdrawn here.

## 4. Sample-size threshold

**n = 60**, cited from the **adopted** lock — `sample.target_n` and `freeze_and_display.threshold`,
inside the bytes adopted by `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json` at SHA-256
`85264e97…82b3805`. Adopted decision **D16** fixes it as a **governance eligibility floor, explicitly
not a power claim**. This protocol does not restate, reinterpret or modify it.

## 5. S-1 and the protocol version it names

The adopted base lock's `cohort_protocol` field names
`Live Signal Engine/GST_PROSPECTIVE_COHORT_PROTOCOL_v1.0_DRAFT.md`. **S-1 therefore currently
references v1.0**, not v1.1 and not this document.

Adopting v1.2 without amending that reference would leave S-1 pointing at a superseded draft. The
required prospective amendment is drafted alongside this file as
`GST_HYP01_S1_COHORT_PROTOCOL_REFERENCE_AMENDMENT_2026-08-29_DRAFT.json`. **Both must be signed
together or neither takes effect.**

---

## 6. Rules carried forward from v1.1 (defensible, unchanged in substance)

- **Locked universe:** the 24 tickers of `Event_Dossier_Protocol/locked_universe_v0.1.json`
  (`date_locked: 2026-08-02`), mechanised by `constants.is_locked_universe_member`.
- **Collection window:** pre-event anchor inside **2026-09-01 → 2027-05-31**, inclusive, applied to
  the mechanically derived anchor.
- **Screening cadence:** Mondays 09:00 America/Chicago, full 24-ticker scope.
- **Anchor and response-session derivation:** production calendar only; never recomputed by hand.
- **Blinding:** inspecting any prohibited input before an enrollment decision voids that decision
  (`COMPROMISED_ENROLLMENT_BLINDING`); the event is never silently re-enrolled.

## 7. Recommended rules — DRAFT, pending two signatures

**None of these is in force. They are the author's recommendation for the signatories to accept,
amend or reject.**

| # | Recommended rule |
|---|---|
| R-1 | **Registration lead: five XNYS trading sessions** before the mechanically derived pre-event anchor. Session arithmetic by the production calendar only. |
| R-2 | **No retrospective enrollment and no pre-event backfill.** An event whose anchor has passed without a registration is missed. A missed event is never registered afterwards and its pre-event snapshot is never reconstructed. |
| R-3 | **Enrollment uses only directly observed issuer or SEC date-and-timing evidence**, observed by a named human. A search snippet, aggregator, third-party calendar, broker estimate or historical cadence is never a source of record. Permitted types: `company_ir_events_calendar`, `company_ir_press_release`, `company_earnings_advisory_pr`, `sec_filing_8k_earnings_date`. |
| R-4 | **Enrollment may precede F5 closure. PRE_EVENT capture may not.** Enrollment consumes only official date/timing inputs; the pre-event snapshot is the first observation and is exactly what F5 governs. |
| R-5 | **DELL is not grandfathered.** It is enrolled on directly observed evidence, and it is subject to every rule here on the same terms as any other event — including R-2 if its anchor passes before collection opens. |

**R-1 and R-2 create no deadline before adoption.** If signed, they apply prospectively from the
approval timestamp and reclassify nothing.

## 8. Signatures

| Field | Entry |
|---|---|
| Approver 1 name · signature · timestamp | `____________` |
| Approver 2 name · signature · timestamp | `____________` |
| Effective from | `____________` |
| Adopting instrument recording this file's SHA-256 | `____________` |
| Confirm: adoption is prospective and reclassifies no earlier event | `____________` |
| Confirm: the S-1 reference amendment is signed together with this | `____________` |
