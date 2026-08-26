# Transport amendment — code-integrity pinning and persistence recovery

**Date:** 2026-08-25
**Status:** FROZEN on commit, **before the corrected runner is implemented**.
**Type:** **TRANSPORT AND PERSISTENCE ONLY.** This amendment changes *how* a completed collection is
proved authentic and written down. It changes **nothing** about what is collected, when, from where,
or how it is validated.

Prerequisites: transport amendment `2c5e006`, incident record `aa4e297`, implementation `3d6ab8a`.

---

## 1. What happened, stated precisely

On 2026-08-24 the scheduled task fired at 02:15:02 and the panel ran to completion, exiting 0 after
884s. Schema validation passed 23 of 23 checks. The runner then **refused to stage** and exited
`EXIT_STAGING(8)`:

```
REFUSED(8): unexpected changed path(s), refusing to stage:
['Live Signal Engine/GST_Phase2_DailyPanel_TestRun_2026-08-24_run3_CHECKPOINT_PARTIAL.csv']
```

`staged_paths_ok()` allows exactly `[final CSV, completion marker]`. The panel also writes a dated
`_CHECKPOINT_PARTIAL.csv` on every run, including successful ones. The allowlist did not describe
the panel's actual output set, so a valid capture could not be persisted.

The three resulting artifacts were left untracked. On 2026-08-25 the task fired normally and
`check_branch_head_clean()` refused with `EXIT_ENV(3)` — `worktree is not clean` — because those
artifacts were still sitting there.

**Classification of record: `VALID_SCHEDULED_CAPTURE_WITH_PERSISTENCE_FAILURE`.** The collection
succeeded. The persistence of that collection failed. These are different failures and are not to be
conflated: no scientific rule, threshold, or captured value is implicated.

---

## 2. Scientific inputs — UNCHANGED

Restated so the boundary of this amendment is unambiguous. **None of the following is modified:**

- the panel program's six required fields and their construction;
- the locked 24-ticker universe;
- feature construction and z-score arithmetic;
- the complete-week rule and data-cutoff convention;
- collection time and the local-time gate: **02:05–02:25 America/Chicago**, scheduled 02:15;
- schema validation thresholds and the full output check set;
- all refusal rules — a partial or failed run stages nothing and commits nothing;
- **the no-backfill rule**;
- `StartWhenAvailable=False`.

**The 2026-08-24 captured values are and remain byte-identical.** They are recovered, not
regenerated. No value is recomputed, corrected, re-requested, or interpreted by this amendment or by
the recovery commit that follows it. The 2026-08-24 and 2026-08-25 dates are **not** re-run and
**not** backfilled.

---

## 3. What is retired: pinning to mutable repository HEAD

The runner currently pins code identity to `--expected-sha <commit>` compared against
`git rev-parse HEAD`. That is **wrong in kind**, not merely inconvenient.

`HEAD` is mutable and, by design, advances every time the runner itself commits a panel. A pin to
`HEAD` therefore invalidates itself on first success: the very act of persisting a capture makes the
next scheduled run refuse. That is the coupling that forced a scheduled task to be re-registered by
hand after each successful day, which is not an unattended system.

**Code integrity must be pinned to content, not to branch position.**

---

## 4. The replacement rule

### 4.1 Code integrity — content-pinned

The runner is authenticated by the **SHA-256 of the runner file's own bytes**, and separately by the
**approved implementation commit** that the running tree must descend from:

| Pin | Value at this amendment |
| --- | --- |
| Runner file SHA-256 | `919c0d3d9e6292001758ac4049cb2d080fa63f8a9dc212cb71ab740a8f17bb44` |
| Runner git blob | `6cd5d5ca06eacb5759be9a3f4fcdc5765401e9e0` |
| Approved implementation commit | `3d6ab8ad3bf07e23409b04970e11fd0e5b5aae76` |

These values describe the runner **as it stands before the Phase 5 correction** and are superseded by
the implementation commit that applies that correction. Superseding them requires a new dated
amendment; it is not a silent edit.

### 4.2 Data-only commits may advance HEAD

A commit that touches **only** paths on the run's output allowlist is a **data-only commit**. A
data-only commit may advance `HEAD` freely and **must not** require the scheduled task to be
re-registered, re-armed, or edited in any way.

### 4.3 HEAD must remain a descendant of the approved implementation commit

`HEAD` is not required to equal anything. It is required to be a **descendant of the approved
implementation commit** (`git merge-base --is-ancestor <approved> HEAD`). This permits the runner's
own data-only commits to accumulate indefinitely while making any rewrite, reset, or divergence away
from approved code a refusal.

### 4.4 Mandatory conditions, unchanged in force

Every one of the following remains **required** before anything is committed or pushed:

1. runner file hash matches the pinned SHA-256;
2. branch is the expected branch;
3. upstream is the expected upstream;
4. `HEAD` descends from the approved implementation commit;
5. the starting worktree is clean;
6. the local-time window gate passes;
7. exactly one network-bearing attempt per date;
8. the panel's own completion marker reports a clean full-universe run;
9. schema validation passes in full;
10. **every changed path** is on the exact allowlist for that run — no extras, no absences;
11. the commit succeeds;
12. the push succeeds **fast-forward only**;
13. the remote ref equals the local commit after the push.

### 4.5 The task must not disable or rewrite itself

The runner **must not** call `Disable-ScheduledTask`, `Set-ScheduledTask`, `Register-ScheduledTask`,
`schtasks /change`, `/create` or `/delete`, or otherwise mutate its own registration, under any
outcome. It may **read** its registration to verify it. Task registration changes are a human
maintenance action, performed once, deliberately, and recorded.

### 4.6 A failed persistence step retains evidence and blocks later collection

If collection succeeds but persistence fails, the runner **retains every artifact**, records the
failure for that date, and **refuses all subsequent collection until a human has reviewed it**. It
must not retry, overwrite, clean, or discard. Silent self-cleanup of a failed persistence is
forbidden — the artifacts are the evidence that the capture was real.

### 4.7 No missed date is ever backfilled

A date that was not collected inside its own window is skipped permanently. Recovery of an
*already-captured* date's artifacts, as performed alongside this amendment, is **not** backfill: no
network request is made and no value is produced.

---

## 5. What this amendment does not decide

The cause of the approximately twenty `Disable`/`Update` task-registration events recorded between
2026-08-24 21:27 and 2026-08-25 14:45 is **not** established. Interactive console history proves at
least one manual `Disable-ScheduledTask` was typed, but the events cannot be attributed to a
specific process or command, and no script, scheduled task, or running process on this machine
performs such mutation. Recorded as **`TASK_MUTATION_CAUSE_UNRESOLVED`**. Section 4.5 constrains the
runner regardless of that finding.
