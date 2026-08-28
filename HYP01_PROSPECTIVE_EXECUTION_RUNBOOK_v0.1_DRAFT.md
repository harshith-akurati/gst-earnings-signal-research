# HYP-01 prospective execution runbook — v0.1 DRAFT

**Status:** draft, on branch `hyp01-prospective-readiness-20260828` (draft PR #40). Not merged, not
authorized, not scheduled. **Nothing described here has been run against real prospective data.**

**Scope:** how the prospective HYP-01 path is executed once collection is under way, who decides what,
and where the path is still blocked. This is an operations document. It changes no scientific
definition and proposes no threshold.

---

## 1. The path, end to end

| # | Stage | Component | State |
|---|---|---|---|
| 1 | Human enrollment of an earnings event | `Live Signal Engine/Market_Response_Event_Registry/registry.jsonl` | **Human decision.** Not automated, by design |
| 2 | Pre-event attention/market snapshot | `gst_market_response/pipeline.py` (pre-event capture) | Implemented |
| 3 | D1 market-response decomposition | `pipeline.capture_d1()` | Implemented |
| 4 | Primary outcome `abs_overnight_gap` | `response_magnitude.apply_absolute_fields()` → `derivations.abs_or_none()` | Implemented — see §6 |
| 4a | Pre-event module eligibility (S-2 evidence) | `stage_markers.build_stage_marker()` → `module_eligibility` | Implemented |
| 5 | Exact registry ↔ marker ↔ GST ↔ D1 join | `tools/hyp01_eligibility.py` → `join_event()` | **Added by this PR** |
| 6 | Eligibility ladder + count to 60 | `tools/hyp01_eligibility.py` → `run_driver()` | **Added by this PR** |
| 7 | Human-readable progress report | `tools/hyp01_progress_report.py` | Added earlier on this branch |
| 8 | Cohort freeze at event 60 | Eligibility rules §5 | **Human procedure.** Driver signals; it does not freeze |
| 9 | SESOI registration | `GST_SESOI_DECISION_REQUEST_FOR_COAUTHOR.md` | **Blocked** — `A9_BLOCKED_MISSING_REGISTERED_SESOI` |
| 10 | Primary model, run once | locked in `GST_HYP01_ANALYSIS_LOCK_v1.0.json` | **Blocked** until 8 and 9 complete |

Stages 1, 8, 9 and 10 are deliberately **not** automatable. Everything this PR adds stops at stage 7.

## 2. Running the eligibility count

```
python tools/hyp01_eligibility.py \
    --registry-root      <dir containing the canonical registry.jsonl> \
    --pre-event-markers  <path>/pre_event_markers.jsonl \
    --gst-legs           <path>/gst_legs.jsonl \
    --d1-legs            <path>/d1_legs.jsonl \
    --out                <path>/GST_HYP01_ELIGIBILITY_STATUS.json
```

Exit codes: `0` a status document was produced; `2` the record set is malformed and the driver
refused (see §4). Re-running with unchanged inputs rewrites nothing and prints
`unchanged; nothing rewritten (idempotent)`.

The status document carries counts, event identifiers, dates, reason codes and provenance hashes.
**It carries no measurement or outcome value**, and this is enforced by test D1/D2, which stuff
sentinel values into every fixture field and assert none of them reaches the output.

## 3. The eligibility ladder

Gates are evaluated in the **registered order, S-1 → S-8**, exactly as fixed by
`GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` §1 and, identically, by
`GST_HYP01_ANALYSIS_LOCK_v1.0.json` `/sample/inclusion_conditions[0..7]`. **This order may not be
rearranged.**

| Step | Question | Disposition if failed |
|---|---|---|
| S-1 | Is the **effective** registration human-verified? | `NOT_ENROLLED` |
| S-2 | Does the **persisted pre-event module eligibility** admit the core family? | `CLASS_INELIGIBLE` |
| S-3 | Do all six panel fields pass the strict v0.2 core gate? | `CORE_GATE_FAILED` |
| S-4 | Is the D1 decomposition complete? | `D1_GATE_FAILED` |
| S-5 | Is `gst_zscore` present with a successful status and valid provenance? | `GST_PROVENANCE_FAILED` |
| S-6 | Is `abs_overnight_gap` present with valid market-data provenance? | `OUTCOME_MISSING` |
| S-7 | Is the **registered** release session BMO or AMC? | `MEASUREMENT_INCOMPATIBLE_INTRADAY` |
| S-8 | Is it within rank 60 of the frozen order? | `EXTENSION_COHORT` |

**First-failure attribution is part of the audit record.** An event failing several gates receives the
code of the **first** gate it fails, so the order determines the exclusion reason. Reordering the
gates would leave the eligible *set* unchanged — an event must pass every gate to be eligible — but it
would change the recorded reason, and §1 requires that *"every disposition is recorded"*. The
registered sequence is therefore implemented literally, and `REGISTERED_GATE_ORDER` in
`tools/hyp01_eligibility.py` is asserted against actual behaviour by test E15.

**Where structural refusals sit.** Only **S-1** reads the registration alone. It evaluates the
*effective* enrollment decision — the base `REGISTRATION` row with every `AMENDMENT` folded in — so it
is decidable even when no capture artifact exists, and when it fails it gives the most informative
answer: the event is not in the study at all.

**S-2 is not a registration check.** Its evidence is the module-eligibility block persisted on the
pre-event stage marker, so it needs a joined artifact exactly like S-3–S-7 do. The correct order is
therefore:

1. **S-1** — effective human enrollment, from the folded registry row.
2. **Structural availability** — the exact join plus the required pre-event marker, GST leg and D1
   leg must all be present and readable.
3. **S-2** — persisted module eligibility, via the locked mechanizer.
4. **S-3–S-7** — the joined evidence.
5. **S-8** — deterministic rank.

A structural refusal surfaces at step 2: after enrollment, before S-2. Duplicate detection and
registry-shape validation precede everything and raise for the whole run.

**A structural failure is not a scientific exclusion.** A refusal means an input artifact is absent or
unreadable, so no gate could be evaluated and no disposition may be assigned; the event is neither
eligible nor scientifically excluded until an operator fixes the input.

**Ordering for step 8** is `(response_session_date ASC, event_id ASC)`, per §2. The date is the
registry's `expected_response_session`, which `register_verified_event()` computes mechanically via
`exchange_calendar.compute_expected_next_full_trading_session_xnys()` — never hand-entered and never
taken from a capture leg. Ordering is independent of arrival order, which test D5 confirms by
reversing every input list.

## 3a. Canonical registry handling

Registry rows are **`REGISTRATION`** and **`AMENDMENT`** — the row types `EventRegistryRow` validates.
There is no `event` row type and never was; a row carrying one is refused, not accepted.

- Exactly **one** base `REGISTRATION` per `event_id`. A second refuses.
- Amendments are folded by **`HumanVerifiedEventRegistry.effective_row()`** — the canonical
  implementation, called directly. No second folding algorithm exists in this tool.
- An amendment is a **correction to its event**, never another event. Counts are per effective event.
- Every `amends_row_id` must resolve to a row of the same event. An orphan refuses.
- An amendment may correct timing, sourcing and status. It may **never** change `event_id`, `ticker`
  or `fiscal_period`; `effective_row()` would fold such a change silently, so it is refused first.
- The base row's bytes are never rewritten — the registry is append-only.
- **Nothing is defaulted.** A required registry field that is absent or blank refuses.

Enrollment status and release timing both come from the **effective** row, so a correction recorded by
amendment is honoured.

## 4. Refusals

A refusal is not a scientific disposition. It means the record set is malformed, no disposition can
be assigned, and an operator must fix the input.

| Code | Meaning | Scope |
|---|---|---|
| `JOIN_REFUSED_DUPLICATE_EVENT` | the registry lists one event twice | whole run raises |
| `JOIN_REFUSED_DUPLICATE_LEG` | two GST or two D1 legs for one event | whole run raises |
| `JOIN_REFUSED_KEY_MISMATCH` | a join key differs across legs, or is absent | per event |
| `JOIN_REFUSED_MISSING_GST_LEG` / `..._D1_LEG` | one leg of the pair is absent | per event |
| `JOIN_REFUSED_UNEXPECTED_SCHEMA_FIELD` | a leg carries a column not on the whitelist | per event |
| `JOIN_REFUSED_NO_CAPTURE_TIME` | a leg has no `captured_at_utc` | per event |
| `JOIN_REFUSED_UNKNOWN_ROW_TYPE` | a registry row is neither REGISTRATION nor AMENDMENT | whole run raises |
| `JOIN_REFUSED_DUPLICATE_BASE_REGISTRATION` | two REGISTRATION rows for one event | whole run raises |
| `JOIN_REFUSED_NO_BASE_REGISTRATION` | an AMENDMENT with no base registration | whole run raises |
| `JOIN_REFUSED_ORPHAN_AMENDMENT` | `amends_row_id` resolves to nothing, or to another event | whole run raises |
| `JOIN_REFUSED_ILLEGAL_IDENTITY_CHANGE` | an amendment rewrites event_id, ticker or fiscal_period | whole run raises |
| `JOIN_REFUSED_MISSING_REGISTRY_FIELD` | a required registry field is absent or blank | whole run raises |
| `JOIN_REFUSED_MISSING_PRE_EVENT_MARKER` | no pre-event marker carries the S-2 decision | per event |
| `JOIN_REFUSED_MISSING_MODULE_ELIGIBILITY` | the marker's `module_eligibility` block is null | per event |
| `JOIN_REFUSED_UNREADABLE_MODULE_ELIGIBILITY` | legacy or malformed block (`LegacyRecordError`) | per event |
| `JOIN_REFUSED_MARKER_IDENTITY_MISMATCH` | the marker's event, stage or ticker disagrees | per event |

Duplication raises for the whole run because there is no correct per-event answer — choosing one of
two legs would be a guess. A stray column or a missing leg affects one event, so it refuses that
event and the rest of the cohort still counts.

**The join uses exact registered keys only** (`event_id`, `ticker`, `earnings_date`). There is no
fuzzy ticker matching, no company-name matching, and no nearest-date matching. Tests A6 and A7 assert
that a wrong ticker and a one-day-off earnings date both refuse rather than resolve.

## 5. The 60-event gate

`BINDING_TARGET = 60`, from `GST_HYP01_EFFECTIVE_LOCK_REPORT_v1.0.json`
`freeze_and_display.threshold`.

- Below 60: `counting_state = COUNTING`, `freeze_required = false`.
- At 60: `counting_state = REFUSED_AT_GATE`, `freeze_required = true`. **The driver stops counting.**
- Beyond 60: the eligible set stays at exactly 60. Surplus events become `EXTENSION_COHORT` and never
  enlarge the frozen set.

`analysis_authorized` is `false` in every state the driver can produce. Reaching the gate is a
**signal to a human**, not an authorization. The freeze itself — freezing the event set, freezing the
environment, re-verifying all gates, then running the primary model exactly once — is the §5 human
procedure and no part of it is implemented here.

## 6. Recorded discrepancy — `abs_overnight_gap` emission

Two governing artifacts disagree, and the disagreement is recorded rather than silently resolved.

- `GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` states that `abs_overnight_gap` is *"specified in
  SPEC v0.1 but **not yet emitted** by the D1 capture path"* and that *"Event 60 cannot be frozen
  until this exists."*
- `GST_HYP01_ANALYSIS_LOCK_v1.0.json` `/primary_outcome/persistence_note` states that the D1 capture
  path **does** emit it, via `pipeline.capture_d1()` → `response_magnitude.apply_absolute_fields()` →
  `derivations.abs_or_none()`.

**The lock is correct and the eligibility-rules text is stale.** Verified directly in this worktree:
`pipeline.py:169` calls `apply_absolute_fields(d1_fields, D1_ABS_FIELD_MAP)`, and
`response_magnitude.py:41` maps `"overnight_gap" → "abs_overnight_gap"`. All three named functions
exist, and `test_market_response_absolute_persistence.py` passes.

**Chronology (from Git history, not inferred):** the eligibility rules and the analysis lock were
authored together in `d059c0b` at 2026-08-08 23:28:32 −0500, and **both** correctly said the field was
not yet emitted. `5fd82ad` implemented emission 27 minutes 16 seconds later, at 23:55:48, and updated
the lock's `persistence_note` but not the eligibility rules. **The statement was correct when authored
and became stale 27 minutes later** — an update omission in `5fd82ad`, not an authoring error.

**The original artifact is not edited.** Per its own §7 (*"a dated amendment alongside the frozen
artifact — never as an edit to it"*), the correction is recorded in an append-only erratum beside it:

```
Live Signal Engine/GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0_IMPLEMENTATION_STATUS_ERRATUM_2026-08-27.md
```

The erratum corrects implementation status only. It changes no outcome definition, timing rule,
eligibility gate, sample-size gate, SESOI status or analysis authorization, and it records that Event
60 remains procedurally dependent on human enrollment and human freeze authorization. An operator
reading the governing artifact alone would wrongly conclude the path is technically blocked; it is
not, but it remains procedurally blocked.

`D1_REQUIRED_FIELDS` is a locked completeness gate and was **not** modified — `abs_overnight_gap` is a
derived output, not a new completeness requirement, exactly as the lock states.

## 7. What is still blocked

| Blocker | Nature | Who resolves it |
|---|---|---|
| Zero events enrolled | operational — collection has not produced eligible events | accrues over time |
| No registered SESOI | **scientific** — `A9_BLOCKED_MISSING_REGISTERED_SESOI` | named co-authors, via the decision request |
| No FROZEN decomposition SPEC | governance — SPEC v0.1 and v0.2 are both `_DRAFT` | project governance |
| Stale eligibility-rules text (§6) | documentation | authorized amendment |

The SESOI blocker is the binding one for A9. It cannot be resolved by anyone on the analysis side:
choosing the threshold from observed estimates would make the test circular, which the project's own
rule `D16 = NO_PROJECT_DERIVED_POWER_CLAIM` prohibits.

## 8. Verification

```
python test_hyp01_eligibility.py        # 91 checks — registry, S-2, join, ladder, gate order, provenance
python test_hyp01_progress_report.py    # 25 checks — redaction, effective registry, deterministic counting
```

Both suites are fully offline: a socket guard fails the run on any connection attempt. Every fixture
is synthetic and built in memory or in a temporary directory. Neither suite reads a project data file.

The gate arithmetic is tested at the boundary specifically: 59 events do not trigger the freeze, the
60th does, and 75 still yields exactly 60 with 15 in the extension cohort.

First-failure precedence is tested for every adjacent pair of ordered gates where simultaneous failure
is possible (S-1/S-2 through S-7/S-8), for timing combined with each missing leg, for provenance
combined with completeness, for duplicates combined with other failures, and for an event that fails
every gate at once. Provenance failures are separately proven unable to be marked eligible, to
increment the count, or to contribute to the event-60 freeze.

## 9. Standing constraints observed in this work

- No real prospective search, quote, price, return, gap or outcome value was opened, printed or
  interpreted.
- No code was executed against real prospective data; no live API was queried.
- No event was enrolled and no backfill was performed.
- No locked scientific definition was changed; no SESOI was selected or recommended.
- The live collector, the scheduled task and AVG were not touched.
- PR #40 remains a draft and is not marked ready.
- No registry row was written or amended; the canonical registry is read-only to this path.
- The corrected eligibility driver has never been executed against a real prospective record.
