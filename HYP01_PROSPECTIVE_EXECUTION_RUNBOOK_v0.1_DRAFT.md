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
| 5 | Exact GST ↔ D1 join | `tools/hyp01_eligibility.py` → `join_event()` | **Added by this PR** |
| 6 | Eligibility ladder + count to 60 | `tools/hyp01_eligibility.py` → `run_driver()` | **Added by this PR** |
| 7 | Human-readable progress report | `tools/hyp01_progress_report.py` | Added earlier on this branch |
| 8 | Cohort freeze at event 60 | Eligibility rules §5 | **Human procedure.** Driver signals; it does not freeze |
| 9 | SESOI registration | `GST_SESOI_DECISION_REQUEST_FOR_COAUTHOR.md` | **Blocked** — `A9_BLOCKED_MISSING_REGISTERED_SESOI` |
| 10 | Primary model, run once | locked in `GST_HYP01_ANALYSIS_LOCK_v1.0.json` | **Blocked** until 8 and 9 complete |

Stages 1, 8, 9 and 10 are deliberately **not** automatable. Everything this PR adds stops at stage 7.

## 2. Running the eligibility count

```
python tools/hyp01_eligibility.py \
    --registry  <path>/registry.jsonl \
    --gst-legs  <path>/gst_legs.jsonl \
    --d1-legs   <path>/d1_legs.jsonl \
    --out       <path>/GST_HYP01_ELIGIBILITY_STATUS.json
```

Exit codes: `0` a status document was produced; `2` the record set is malformed and the driver
refused (see §4). Re-running with unchanged inputs rewrites nothing and prints
`unchanged; nothing rewritten (idempotent)`.

The status document carries counts, event identifiers, dates, reason codes and provenance hashes.
**It carries no measurement or outcome value**, and this is enforced by test D1/D2, which stuff
sentinel values into every fixture field and assert none of them reaches the output.

## 3. The eligibility ladder

Steps are applied in the order fixed by `GST_HYP01_ELIGIBILITY_AND_FREEZE_RULES_v1.0.md` §1. The
first step an event fails determines its disposition; each disposition is a registered code.

| Step | Question | Disposition if failed |
|---|---|---|
| 1 | Is the event human-verified and enrolled? | `NOT_ENROLLED` |
| 2 | Is it in the core attention/response family? | `CLASS_INELIGIBLE` |
| 7 | Is the release BMO or AMC? | `MEASUREMENT_INCOMPATIBLE_INTRADAY` |
| 3 | Do all six panel fields pass the strict v0.2 core gate? | `CORE_GATE_FAILED` |
| 4 | Is the D1 decomposition complete? | `D1_GATE_FAILED` |
| 5 | Is `gst_zscore` present with a successful status and valid provenance? | `GST_PROVENANCE_FAILED` |
| 6 | Is `abs_overnight_gap` present with valid market-data provenance? | `OUTCOME_MISSING` |
| 8 | Is it within rank 60 of the frozen order? | `EXTENSION_COHORT` |

**Step 7 is evaluated ahead of steps 3–6** even though it is numbered later. An intraday release is
measurement-incompatible whatever its data completeness, so reporting it as a data-quality failure
would misattribute the reason. The set of eligible events is identical either way; only the exclusion
label differs. Ordering within the exclusion codes is a reporting choice, not a scientific one.

**Ordering for step 8** is `(response_session_date ASC, event_id ASC)`, per §2 — deterministic and
independent of arrival order, which test D4 confirms by reversing every input list.

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

**No artifact was edited to reconcile this.** Correcting the eligibility-rules text is a documentation
amendment to a governing artifact and needs its own authorization. Until then, an operator reading
that document alone would wrongly conclude the path is blocked. It is not.

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
python test_hyp01_eligibility.py        # 37 checks — join, ladder, gate, non-disclosure
python test_hyp01_progress_report.py    # 22 checks — redaction, deterministic counting
```

Both suites are fully offline: a socket guard fails the run on any connection attempt. Every fixture
is synthetic and built in memory or in a temporary directory. Neither suite reads a project data file.

The gate arithmetic is tested at the boundary specifically: 59 events do not trigger the freeze, the
60th does, and 75 still yields exactly 60 with 15 in the extension cohort.

## 9. Standing constraints observed in this work

- No real prospective search, quote, price, return, gap or outcome value was opened, printed or
  interpreted.
- No code was executed against real prospective data; no live API was queried.
- No event was enrolled and no backfill was performed.
- No locked scientific definition was changed; no SESOI was selected or recommended.
- The live collector, the scheduled task and AVG were not touched.
- PR #40 remains a draft and is not marked ready.
