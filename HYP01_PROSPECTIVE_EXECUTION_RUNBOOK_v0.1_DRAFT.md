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
| 6a | Canonical input adapter (production entry point) | `tools/hyp01_canonical_adapter.py` | **Added by this PR** |
| 7 | Human-readable progress report | `tools/hyp01_progress_report.py` | Added earlier on this branch |
| 8 | Cohort freeze at event 60 | Eligibility rules §5 | **Human procedure.** Driver signals; it does not freeze |
| 9 | SESOI registration | `GST_SESOI_DECISION_REQUEST_FOR_COAUTHOR.md` | **Blocked** — `A9_BLOCKED_MISSING_REGISTERED_SESOI` |
| 10 | Primary model, run once | locked in `GST_HYP01_ANALYSIS_LOCK_v1.0.json` | **Blocked** until 8 and 9 complete |

Stages 1, 8, 9 and 10 are deliberately **not** automatable. Everything this PR adds stops at stage 7.

## 2. Running the eligibility count

**The production command takes canonical project roots. It does not accept hand-prepared evidence
files.**

```
python tools/hyp01_canonical_adapter.py \
    --registry-root         <dir containing registry.jsonl> \
    --event-store-root      <dir containing {event_id}.jsonl> \
    --marker-root           <dir containing {event_id}_{stage}_MARKER.json> \
    --operations-plan-root  <dir containing {event_id}_OPERATIONS_PLAN.json> \
    --out                   <redacted status document>
```

Exit codes: `0` a status document was produced; `2` the input set is malformed and the adapter
refused; `3` the reconciliation invariant failed and nothing was written. Re-running over unchanged roots rewrites nothing and prints
`unchanged; nothing rewritten (idempotent)`.

`tools/hyp01_eligibility.py` is **not** an entry point. It previously accepted `--gst-legs`,
`--d1-legs` and `--pre-event-markers` JSONL; running it now prints the canonical command and exits
`2`. Manually fabricated evidence is not canonical evidence — nothing tied those files to the event
store, the immutable markers or the operations plan. `run_driver()`, `join_event()` and `classify()`
remain importable as **internal, testable primitives** for synthetic unit tests; they are not an
input mechanism.

### Exact artifacts read

| Eligibility field | Canonical source |
|---|---|
| S-1 enrollment | effective registry row → `verification_status` |
| identity, registered timing | effective registry row (`HumanVerifiedEventRegistry.effective_row()`) |
| S-2 module eligibility | `PRE_EVENT_CAPTURE` marker → `module_eligibility` |
| S-3 six panel fields + statuses | canonical `PRE_EVENT_CAPTURED` state record → `fields` |
| S-4 D1 decomposition | canonical `D1_COMPLETE` state record → `fields` |
| S-6 `abs_overnight_gap` | canonical `D1_COMPLETE` state record → `fields` |
| GST provenance path/hash | PRE_EVENT record → `source_csv_path` / `source_csv_sha256` |
| D1 provenance path/hash | D1 marker path + SHA-256 of its bytes |
| GST capture timestamp | PRE_EVENT record → `written_at_utc` |
| D1 capture timestamp | D1 record → `written_at_utc` (set by `EventStore.append_state`, never caller-supplied) |
| permitted D1 window (lower bound) | operations plan → `sessions.D1.earliest_provider_retrieval_utc` |
| S-8 ordering key | effective registry row → `expected_response_session` |

**No heuristics.** Every artifact is addressed by an exact deterministic path. There is no
newest-file, nearest-date, glob-and-pick or filename-guessing fallback: if the exact artifact is
absent, that event refuses.

**Redacted output.** The status document carries counts, event identifiers, dates, reason codes and
provenance hashes — no measurement or outcome value. The adapter necessarily *reads* outcome fields
(S-4 and S-6 cannot be evaluated otherwise) but never prints, formats or interprets one, and the
D1 marker's `response_magnitude` block is projected away before the driver sees it.

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

## 3b. D1 response-window validation

Before any gate runs, the adapter proves the D1 evidence belongs to the **registered** response
window. Every comparison reuses a production function or an authoritative persisted field; no session
arithmetic is reimplemented.

| Check | Refusal if it fails |
|---|---|
| D1 `event_id`, ticker and earnings date come from the effective registration | *unconstructible* — the adapter builds identity from the registration |
| registry `expected_response_session` still recomputes from the effective row via `compute_expected_next_full_trading_session_xnys()` | `REGISTRY_TIMING_STALE` |
| operations plan `event.{event_id, ticker, earnings_date, release_market_session}` equal the effective registration | `OPERATIONS_PLAN_MISMATCH` |
| plan `sessions.D1.session_date` equals the registered `expected_response_session` | `D1_RESPONSE_SESSION_MISMATCH` |
| plan recomputes to its own `plan_content_sha256` | `OPERATIONS_PLAN_INTEGRITY` |
| the D1 marker's `response_magnitude` echo equals the D1 state record | `MARKER_STATE_DISAGREEMENT` |
| D1 `written_at_utc` parses as a timezone-aware ISO-8601 instant | `MALFORMED_CAPTURE_TIMESTAMP` |
| D1 `written_at_utc` ≥ plan `sessions.D1.earliest_provider_retrieval_utc` | `CAPTURE_BEFORE_PERMITTED_WINDOW` |

**Superseded timing.** An amendment that moves registered timing causes
`amend_event()` to recompute `expected_response_session`. A capture and plan prepared for the old
session no longer match, and the event refuses — no locked rule exempts such a capture, so it is not
reused. In practice the plan-identity check fires first, because an amendment that moves timing
necessarily changes a field the plan echoes.

**Presence is not validity.** A nonblank but unparseable, malformed or timezone-naive capture
timestamp refuses. An unparseable instant cannot be compared against the window at all, so accepting
it would silently skip the window check.

### SPECIFICATION GAP — no upper bound on D1 capture time

The locked artifacts specify only a **lower** bound on when a D1 capture may occur:
`operations_plan.SessionPlan.earliest_provider_retrieval_utc` (the D1 session's final expected bar
start plus `ALPACA_MIN_END_AGE_MINUTES = 15`).

**No committed artifact states a latest permissible capture instant.** There is no staleness limit,
deadline or recency tolerance for D1 in the SPECs (v0.1 or v0.2), the analysis lock, the eligibility
and freeze rules, the effective lock report, or the code. Searches for `latest`, `deadline`,
`max_age`, `staleness`, `not_after` and `expires` return only option-quote-age and
methodology-version matches, neither of which governs D1 capture recency.

**An upper bound is therefore not enforced**, because enforcing one would mean inventing a tolerance.
This is a specification gap for a human to close, recorded rather than filled.

## 3c. One event, one classification

Every effective event leaves the run with **exactly one** terminal category: eligible (rank 1-60),
`EXTENSION_COHORT`, one registered scientific exclusion, or one structural refusal.

- **S-1 preempts everything.** A registration that is not verified is classified `NOT_ENROLLED` and
  nothing else. Its event-store log, stage markers, operations plan, GST evidence and D1 evidence are
  never opened, and it is given no structural refusal.
- **Precise refusals survive.** A canonical refusal (say `MISSING_PRE_EVENT_STATE`) is threaded into
  the driver's single classification flow, not added to the tally afterwards. It is never replaced by,
  or supplemented with, a generic `MISSING_GST_LEG`.
- **One registry snapshot per invocation.** `registry.jsonl` is read, validated and folded once; the
  same snapshot drives evidence assembly, classification and ordering. The file is hashed before and
  after the fold, so a mutation mid-run refuses instead of blending two states. Only the snapshot
  SHA-256 reaches the status document (`registry_snapshot_sha256`) -- never registry contents.
- **Reconciliation invariant**, enforced before the document is returned or written:

  ```
  eligible + extension + scientific exclusions + structural refusals == effective_events_seen
  ```

  A violation raises `ReconciliationError`; the CLI exits **3** and writes nothing.

**Reachability note.** `CORE_GATE_FAILED`, `CLASS_INELIGIBLE`, `D1_GATE_FAILED` and `OUTCOME_MISSING`
cannot be produced through the canonical writers: a failing strict-core or D1 gate drives the event to
`PARTIAL`, which `validate_transition()` treats as terminal, so no `D1_COMPLETE` record is ever
written and the adapter refuses structurally instead. The canonically reachable scientific exclusions
are S-7 (`MEASUREMENT_INCOMPATIBLE_INTRADAY`) and S-5 (`GST_PROVENANCE_FAILED`). All of them remain
reachable at the primitive level and are exercised in `test_hyp01_eligibility.py`.

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
| `JOIN_REFUSED_MISSING_EVENT_STORE_LOG` | no canonical `{event_id}.jsonl`, or no STATE record | per event |
| `JOIN_REFUSED_MISSING_PRE_EVENT_STATE` | no `PRE_EVENT_CAPTURED` stage record | per event |
| `JOIN_REFUSED_MISSING_D1_STATE` | no `D1_COMPLETE` stage record (a PARTIAL D1 does not qualify) | per event |
| `JOIN_REFUSED_MISSING_D1_MARKER` | no immutable `D1_CAPTURE` marker | per event |
| `JOIN_REFUSED_MARKER_STATE_DISAGREEMENT` | a marker disagrees with its persisted stage record | per event |
| `JOIN_REFUSED_INVALID_STATE_CHRONOLOGY` | the state log replays into an illegal transition | per event |
| `JOIN_REFUSED_DUPLICATE_STATE_RECORD` | duplicate `seq` in the append-only log | per event |
| `JOIN_REFUSED_MISSING_OPERATIONS_PLAN` | no `{event_id}_OPERATIONS_PLAN.json` | per event |
| `JOIN_REFUSED_OPERATIONS_PLAN_MISMATCH` | the plan describes a different event | per event |
| `JOIN_REFUSED_OPERATIONS_PLAN_INTEGRITY` | the plan does not recompute to its own digest | per event |
| `JOIN_REFUSED_D1_RESPONSE_SESSION_MISMATCH` | the plan's D1 session is not the registered response session | per event |
| `JOIN_REFUSED_REGISTRY_TIMING_STALE` | `expected_response_session` no longer recomputes | per event |
| `JOIN_REFUSED_MALFORMED_CAPTURE_TIMESTAMP` | a capture time is unparseable or timezone-naive | per event |
| `JOIN_REFUSED_CAPTURE_BEFORE_PERMITTED_WINDOW` | D1 captured before the plan's earliest permitted retrieval | per event |

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
python tools/hyp01_canonical_adapter.py --help   # the production command
python test_hyp01_canonical_adapter.py  # 47 checks — canonical end-to-end, D1 timing
python test_hyp01_first_failure_classification.py  # 40 checks — one event, one classification
python test_hyp01_eligibility.py        # 91 checks — registry, S-2, join, ladder, gate order, provenance
python test_hyp01_progress_report.py    # 25 checks — redaction, effective registry, deterministic counting
```

All three suites are fully offline: a socket guard fails the run on any connection attempt. Every
fixture is synthetic. The canonical suite builds its fixtures through the project's own writers --
`HumanVerifiedEventRegistry`, `EventStore`, `pipeline.capture_*`, `write_stage_marker`,
`build_operations_plan`/`finalize_plan` -- in a temporary directory, so no raw JSON is substituted
where a production writer exists. No suite reads a project data file.

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
- The canonical adapter has never been executed against a real prospective capture artifact.

### Steps that remain human-only

1. **Enrollment.** A human verifies release timing from a primary source and writes the
   `REGISTRATION` row. No component here enrolls or amends an event.
2. **Freeze at event 60.** Reaching the gate sets `freeze_required` and REFUSES further counting. The
   §5 procedure -- freeze the event set, freeze the environment, re-verify S-1..S-8 for all 60 -- is
   performed by a person. `analysis_authorized` is `false` in every reachable state.
3. **SESOI registration.** Still absent; A9 remains `A9_BLOCKED_MISSING_REGISTERED_SESOI`.
4. **Closing the D1 upper-bound specification gap** (see §3b).

### Recorded deviation

A procedural deviation on 2026-08-28 -- the progress reporter was run once against the real registry
root instead of a synthetic fixture -- is disclosed in
`Live Signal Engine/GST_HYP01_PROCEDURAL_DEVIATION_RECORD_2026-08-28.md`. It read only whitelisted
identity fields, opened no capture or outcome artifact, altered nothing, and did not compromise
outcome blinding.
- No registry row was written or amended; the canonical registry is read-only to this path.
- The corrected eligibility driver has never been executed against a real prospective record.
