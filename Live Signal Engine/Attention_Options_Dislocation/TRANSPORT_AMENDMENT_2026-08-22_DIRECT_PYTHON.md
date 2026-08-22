# Transport amendment — direct Python execution

**Date:** 2026-08-22
**Status:** FROZEN on commit, **before the replacement runner is implemented**.
**Type:** **TRANSPORT ONLY.** This amendment changes *how* the unattended collection is invoked. It
changes **nothing** about what is collected, when, from where, or how it is validated.

Prerequisite: incident record `ecc8540`.

---

## 1. What is retired, and why

**PowerShell orchestration is retired.** It is not repaired, re-signed, relocated or excluded.

Cause of record: AVG's `IDP.HELU.PSD11` behavioural heuristic quarantined every PowerShell runner
that spawned a child process and invoked `git push`. The detection is behavioural, not
signature-based, so relocation demonstrably did not prevent it — copies inside and outside the
repository were both taken.

**No antivirus exclusion is added and no quarantined file is restored.** The correct response to a
behavioural detection is to stop performing the detected behaviour in the detected host, not to
suppress the detector.

---

## 2. Scientific inputs — UNCHANGED

Restated so the boundary of this amendment is unambiguous. **None of the following is modified:**

- the panel program itself and every one of its six required fields;
- the locked ticker universe;
- feature construction and z-score arithmetic;
- the complete-week rule and data-cutoff convention;
- collection time and the local-time gate: **02:05–02:25 America/Chicago**, scheduled 02:15;
- schema validation thresholds and the 12-plus output checks;
- all refusal rules — a partial or failed run stages nothing and commits nothing;
- **the no-backfill rule**;
- `StartWhenAvailable=False`.

**No outcome or post-event data is read, computed or committed by the runner at any point.**

---

## 3. Transport specification

- **Task Scheduler invokes the pinned Python interpreter directly.**
- **No `.ps1`, `.bat`, `.cmd`, `powershell.exe`, `pwsh.exe`, `cmd.exe` or any shell wrapper may
  appear in the task action.** The action is the Python executable plus argument array.
- All subprocess invocations inside the runner use **argument arrays**; `shell=True` is prohibited.
- The task's working directory is the verified repository root.

---

## 4. One attempt per eligible date

- **Exactly one network-bearing panel attempt per eligible date.**
- **A recorded failure blocks any further attempt that date, exactly as a recorded success does.**
  There is no retry, no second chance and no same-day re-run. A date that fails is a date that
  produced no observation, and it is **not backfilled later**.
- Attempt records are written to the external state directory, outside the repository working tree.

---

## 5. Ordered refusal gate

The runner **writes its external log before performing any collection**, then refuses unless **all**
of the following hold. Each failure exits with its own code and performs no network request, no
staging, no commit and no push.

1. **Repository root resolves exactly** — `git rev-parse --show-toplevel` equals the supplied path.
2. **Expected branch is checked out**, and **the committed runner is present** in the working tree.
3. **Worktree is clean.**
4. **Local `HEAD` equals the pinned expected SHA.**
5. **Upstream configuration is correct** — the branch tracks its expected remote ref.
6. **No same-date success *or* failure record exists.**
7. **The local-time gate is open** — inside 02:05–02:25 America/Chicago.
8. **The scheduled-task registration exists, and its action matches the direct Python invocation** —
   the runner refuses if its own task has been altered to run through a shell, or is missing.

Gate 8 is new and is a direct consequence of the incident: an unattended job that cannot see its own
registration cannot notice that the registration has been tampered with or removed.

---

## 6. Output handling

- **Validation must pass before anything is staged.** The existing schema validator is the gate; a
  non-zero result stages nothing.
- **Only the expected panel and provenance paths may be staged**, enforced by an explicit allowlist.
  **Any unexpected changed path aborts the run** rather than being committed.
- **Commit and push occur only after validation passes.**
- **A push failure preserves the local commit and the log, and must not repeat collection.** The
  observation is already made; re-collecting would produce a second network-bearing attempt for the
  same date, which §4 forbids.

---

## 7. Prohibited Git operations

The runner may run only `rev-parse`, `status`, `diff`, `add` (allowlisted paths), `commit` and
`push`. It must **never** run `git pull`, `checkout`, `reset`, `clean`, `restore`, a force-push, or
any history rewrite. These are asserted by test, not merely documented.

---

## 8. Observability precondition

`Microsoft-Windows-TaskScheduler/Operational` **must be enabled and verified `IsEnabled=True` before
the replacement task is registered.** The incident's central evidentiary gap was that this channel
was off, leaving the task removal unexplainable. Registering a replacement without it would
reproduce the same blindness.

If enabling the channel requires administrator rights that this session does not hold, **the exact
command is handed to the operator and registration stops** until it is confirmed. Permission is not
bypassed.

---

## 9. What this amendment does not do

- It does not change any scientific rule, threshold or definition.
- It does not restore, re-run or reinterpret anything.
- It does not backfill any date, including 2026-08-21 and 2026-08-22.
- It does not weaken, disable or reconfigure any security product.
- It does not resolve the scheduled-task removal, which remains **`CAUSE_UNRESOLVED`**.
- It does not make the system `LIVE`. That term applies only after a scheduled run produces a
  validated panel, a machine-created commit, a successful push, and a matching remote SHA.
