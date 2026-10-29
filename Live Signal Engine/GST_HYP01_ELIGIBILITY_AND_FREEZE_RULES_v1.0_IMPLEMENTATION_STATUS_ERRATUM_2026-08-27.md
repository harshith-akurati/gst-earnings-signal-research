# Implementation-status erratum — HYP-01 Eligibility and Freeze Rules v1.0

**Date:** 2026-08-27
**Applies to:** `GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` (this directory)
**Type:** append-only implementation-status erratum
**Scope:** implementation status only

---

## 0. What this is, and what it is not

The governing artifact is **not modified**. Per its own §7 — *"recorded as a dated amendment alongside
the frozen artifact — never as an edit to it"* — this file sits beside it and is appended, never
merged into it.

**This erratum corrects a statement of implementation status and nothing else.** It does not change:

| Unchanged | Confirmation |
|---|---|
| the outcome definition | `abs_overnight_gap` as specified in SPEC v0.1 — formula untouched |
| timing rules | `response_session_date` derivation untouched |
| eligibility gates S-1…S-8 | unchanged in content and in order |
| `D1_REQUIRED_FIELDS` | unchanged — still the four signed intervals |
| the 60-event sample-size gate | unchanged |
| SESOI status | still absent; `A9_BLOCKED_MISSING_REGISTERED_SESOI` stands |
| analysis authorization | still not granted |

**No prospective result exists.** Zero eligible events have been collected. Nothing in this erratum
reports, implies, or anticipates any outcome.

## 1. The stale sections

Two adjacent paragraphs in **§4 "Blocking prerequisite"**, lines 51 and 53 of the governing artifact:

> **(line 51)** `abs_overnight_gap` is specified in SPEC v0.1 but **not yet emitted** by the D1 capture
> path — `D1_REQUIRED_FIELDS` holds only the four signed intervals. Step 6 therefore cannot pass for
> any event until that field is persisted with valid provenance.

> **(line 53)** **Event 60 cannot be frozen until this exists.** Building it is a separate, authorised
> task. Until then HYP-01 accrues 0 eligible events, and that is the honest state — not a failure to
> report.

The clause *"`D1_REQUIRED_FIELDS` holds only the four signed intervals"* remains **correct and
current** — that list was deliberately not extended. Only the emission claim is stale.

## 2. Current implementation status

**`abs_overnight_gap` is emitted by the committed D1 capture pipeline.**

| Element | Location |
|---|---|
| derivation call site | `gst_market_response/pipeline.py:169` — `fields = apply_absolute_fields(d1_fields, D1_ABS_FIELD_MAP)` |
| import | `gst_market_response/pipeline.py:32` |
| field mapping | `gst_market_response/response_magnitude.py:41` — `"overnight_gap": "abs_overnight_gap"` |
| absolute-value helper | `gst_market_response/derivations.py` — `abs_or_none()` |
| completeness list (unchanged) | `gst_market_response/completeness.py:23` — `D1_REQUIRED_FIELDS` |
| test coverage | `test_market_response_absolute_persistence.py` |

The field is a **canonical derived output, not a new completeness requirement** — which is precisely
why `D1_REQUIRED_FIELDS` was correctly left alone.

## 3. Chronology — the statement was correct when authored

Established from Git history, not inferred.

| Time (−0500) | Commit | Event |
|---|---|---|
| 2026-08-08 23:28:32 | `d059c0b3b626c0dc13f4a0f25f0ce8102636669c` | `HYP-01 primary analysis lock v1.0 (draft)` — authored **both** the eligibility rules and the analysis lock. Both stated the field was **not yet emitted**. |
| 2026-08-08 23:55:48 | `5fd82ad2e719232d2c67066e3cb0ddae1c266a2c` | `Implement canonical absolute response persistence` — implemented emission, added `test_market_response_absolute_persistence.py`, **and updated the lock's `persistence_note`**. Did **not** update the eligibility rules. |

**Elapsed: 27 minutes 16 seconds.**

**The statement was correct when authored and became stale 27 minutes later.** It was *not* erroneous
at the time of writing. At `d059c0b` the two artifacts agreed with each other and with the code; the
lock's `persistence_note` then read:

> abs_overnight_gap is an authoritative SPEC v0.1 field and its formula is fixed, but the D1 capture
> path does not yet emit it … Emitting it is a separate build task, NOT performed here.

The divergence is an **update omission in `5fd82ad`**: that commit revised one of the two artifacts
describing the same fact and left the other behind. The eligibility-rules artifact has been touched by
exactly **one** commit in its entire history (`d059c0b`) and has never been amended.

The lock's `persistence_note` now reads, correctly:

> as of the canonical absolute-response persistence commit the D1 capture path EMITS it:
> `pipeline.capture_d1()` derives it via `response_magnitude.apply_absolute_fields()` using
> `derivations.abs_or_none()` … `D1_REQUIRED_FIELDS` is unchanged — the field is a canonical derived
> output, not a new completeness requirement. The analytical definition in this lock did not change;
> only its implementation status did.

Where the two artifacts disagree, **the lock is current and the eligibility rules are stale.**

## 4. What Event 60 still depends on

Correcting the emission claim removes a *technical* blocker. It removes **no procedural one.** Event
60 remains dependent on, in order:

1. **Human enrollment.** Events enter the cohort only by a human-verified registration. No automated
   component enrolls an event, and none may.
2. **Accrual to 60 eligible events.** Currently **0**.
3. **Human freeze authorization.** The §5 procedure — freeze the event set, freeze the environment,
   re-verify S-1…S-8 for all 60 — is performed by a person. Automated counting signals that the
   threshold is reached; it does not freeze anything and does not authorize analysis.
4. **A registered SESOI**, for A9. Still absent.

The second sentence of line 53 — *"HYP-01 accrues 0 eligible events, and that is the honest state"* —
therefore **remains true today**, though now for procedural rather than technical reasons.

## 5. Effect on the eligibility ladder

**None.** S-6 (*`abs_overnight_gap` non-null with valid market-data provenance*) is unchanged in
wording, position and meaning. The correction is that S-6 is now **capable of passing** for an event
whose D1 capture succeeded, where line 51 asserted it could not pass for any event.

Records written **before** `5fd82ad` carry no `abs_*` fields and are transparently ineligible under
S-6. **Nothing was backfilled**, and this erratum authorizes no backfill.

## 6. Verification performed

Read-only inspection of committed code and Git history in worktree
`gst-hyp01-readiness-worktree`, branch `hyp01-prospective-readiness-20260828`. No prospective
measurement or outcome value was opened, executed against, displayed or interpreted. No API was
queried. No event was enrolled. `test_market_response_absolute_persistence.py` was executed and
passes.

## 7. Integrity of the original artifact

`GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` is preserved **byte-for-byte**.

```
git blob    957557d191243669e521a94bc8e1cb18cc079a4c   (identical in d059c0b and at HEAD)
sha256 (LF) 6c6266deba732932cd9d85db9e89cfec13f8723ac6d8849eed4ced63ccc1b58c
```

Frozen bytes are never rewritten. This erratum is append-only and does not supersede the artifact; it
records that one implementation-status statement within it has been overtaken by a later commit.
