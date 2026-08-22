# Incident report — removal of the unattended-panel PowerShell runners

**Date:** 2026-08-22
**Type:** Infrastructure incident. **Not a scientific-method change.**
**Scope:** The unattended execution transport only. No frozen scientific design, hypothesis,
estimand, gate, universe or feature definition is touched by this report or by the migration that
follows it.

---

## 1. Summary

Between 2026-08-20 and 2026-08-21, three PowerShell copies of the unattended Phase 2 daily-panel
runner were removed from disk without notice. AVG Antivirus quarantine records name all three, with
detection labels, original paths and timestamps.

Separately, the scheduled task `GST_PHASE2_DAILY_PANEL_UNATTENDED` is absent. **Its removal is not
attributed to AVG and remains unexplained.**

**No data collection ever occurred.** No panel artifact, machine-created commit or push exists.

Classifications:

| Event | Classification |
|---|---|
| PowerShell runner removals | **`SECURITY_PRODUCT_REMOVED_BY_AVG`** |
| Scheduled-task removal | **`CAUSE_UNRESOLVED`** |

---

## 2. Deployed runner hashes and survival status

Four content-addressed deployments were published to the external runners directory. Two survive.

| Deployed (UTC) | SHA-256 (first 12) | Size | Status |
|---|---|---|---|
| 2026-08-21T19:55:13Z | `dd705a5dbe42` | 8,069 B | **REMOVED** |
| 2026-08-21T19:56:06Z | `750c530ff4ea` | 8,574 B | Present |
| 2026-08-21T19:56:57Z | `eb52bc58a61f` | 8,777 B | Present |
| 2026-08-21T20:18:58Z | `426d24a47ae3` | 11,170 B | **REMOVED** |

Full digest of the last deployed copy, recorded for provenance:
`426d24a47ae3f83a9813c759e5a1fa311e240cb83bf0a3c592abb51a1af7e7e8`

A fifth copy — the canonical in-repository runner tracked in Git — **survives untouched** at
11,170 bytes and remains byte-identical to the blob in `b38b826`. An earlier in-repository copy on a
different worktree did **not** survive; see entry 1 below.

**Survival did not correlate with location.** Copies inside and outside the repository were both
taken, and copies inside and outside the repository both survived.

---

## 3. AVG quarantine entries

Source: the AVG quarantine index, last modified **2026-08-21 15:36:29** local. Three entries, all
of them our runner. Paths are given as recorded; the same repository paths already appear in
committed repository content.

| Chest ID | Original file | Original folder | Detection | Quarantined (local) |
|---|---|---|---|---|
| `00000001` | `Invoke-Phase2DailyPanelUnattended.ps1` | `…\Google-Search-Trend-main\Google-Search-Trend-main\tools` | **`IDP.Generic`** | 2026-08-20 01:25:30 |
| `00000002` | `Invoke-Phase2DailyPanelUnattended.dd705a5dbe42.ps1` | `…\gst-source-quarantine\scheduler\runners` | **`IDP.HELU.PSD11`** | 2026-08-21 14:55:42 |
| `00000003` | `Invoke-Phase2DailyPanelUnattended.426d24a47ae3.ps1` | `…\gst-source-quarantine\scheduler\runners` | **`IDP.HELU.PSD11`** | 2026-08-21 15:36:29 |

`IDP.HELU.PSD11` is a PowerShell behavioural heuristic. The runner spawned a child process and
invoked `git push`; that combination is the pattern the heuristic targets. **The detections are
behavioural, not content-signature, which is why relocation did not prevent them.**

---

## 4. Direct evidence supporting `SECURITY_PRODUCT_REMOVED_BY_AVG`

1. **Named quarantine records** for all three removed files, with original filenames and folders
   matching the deployment manifest exactly.
2. **Timestamp agreement to the second across three independent files.** The runners directory
   `LastWriteTime` is `2026-08-21 15:36:24`; the quarantine index mtime is `15:36:29.317`; the AVG
   detection log mtime is `15:36:33.549`. A directory mtime updates when an entry is removed.
3. **The AVG vault database and removal-data file were written in the same 15:30–15:45 window.**
4. **The files are not in the Recycle Bin** — consistent with quarantine, not a user delete.
5. **No PowerShell console session was running at the deletion instant.** The prior session's
   ScheduledTask activity ended 15:23:09; the next console started 15:36:28, four seconds *after*
   the directory changed, so it cannot have performed the removal.
6. **Microsoft Defender is excluded**: Passive Mode, real-time protection disabled, zero detections
   in its history.
7. **Entry 1 independently explains the 2026-08-20 disappearance**, whose directory mtime was
   `01:25`, matching the quarantine time of `01:25:30`.

---

## 5. Evidence gaps requiring `CAUSE_UNRESOLVED` for the task removal

The scheduled task's absence is verified, but **no source capable of explaining it was available**:

- **`Microsoft-Windows-TaskScheduler/Operational` was disabled** for the entire period —
  `IsEnabled=False`, the channel's registry `Enabled` value is `0`, and the `.evtx` file does not
  exist. **This is a configuration state, not evidence that no deletion event occurred.**
- **Security-log task auditing (4698/4699/4702) was unreadable** from a non-elevated session.
- **The `TaskCache` registry keys were unreadable** from a non-elevated session.
- **No AVG artifact references the task name anywhere.** AVG's records name files only.
- **The interactive console history contains no `Unregister-ScheduledTask` and no deletion command
  against the task.** It records inspection and a `Disable-ScheduledTask`, nothing more. That history
  captures interactive console input only; GUI actions, `schtasks.exe`, and other hosts would not
  appear in it.

**The task deletion is therefore not attributed to AVG, or to anything else.** Quarantining a script
file is not the same act as removing a scheduled task, and the AVG evidence does not extend to it.

Verification that the absence is real rather than an access artifact: a task file known to exist is
readable from this session while the panel task's file is not, and the two unrelated ROST tasks
remain registered — so this was a targeted removal, not scheduler-database corruption.

---

## 6. Existence and absence timeline

| Local time | Event | Basis |
|---|---|---|
| 2026-08-20 01:25:30 | First in-repository runner quarantined (`IDP.Generic`) | AVG chest entry 1 |
| 2026-08-21 14:55:42 | `dd705a5dbe42` quarantined (`IDP.HELU.PSD11`) | AVG chest entry 2 |
| 2026-08-21 ~15:17 | `426d24a47ae3` deployed and verified in place | deployment manifest; digest matched its content-addressed name |
| 2026-08-21 ~15:18–15:22 | Task registered; observed `Ready`, NextRun 2026-08-22 02:15 | registration verification |
| 2026-08-21 15:23:09 | Last runner activity (preflight only, no collection) | external log; PowerShell Operational |
| **2026-08-21 15:36:24** | Runners directory modified — **last provable moment the runner existed** | directory mtime |
| **2026-08-21 15:36:29** | `426d24a47ae3` quarantined — **first provable absence** | AVG chest entry 3 |
| 2026-08-21 15:36:28 | A console starts, four seconds *after* the removal | PowerShell Operational |
| after 15:36 | Task still present; disabled interactively | console history; operator report |
| 2026-08-22 01:33 | Task and runner both observed absent | this audit |

**The task and the runner did not disappear together.** The runner was quarantined at 15:36:29 on
2026-08-21. The task survived that event by hours and was still present when it was disabled. These
are two separate events with two separate causes, one of which is unresolved.

---

## 7. Confirmation that no collection occurred

- No panel CSV or completion marker exists for any date after 2026-08-20.
- No machine-created commit exists on any branch; the branch and its remote both stand at `b38b826`.
- The external log directory's newest entry is `20260821T202308Z`, a preflight refusal.
- The lock directory holds only the two unrelated ROST locks from 2026-08-19 and 2026-08-20.
- Every runner invocation in the record was `Preflight` mode or a gate refusal. **No network-bearing
  panel attempt was ever made by the unattended path.**

---

## 8. Correction of a premature statement

A previous status report stated that the 02:15 unattended cycle "did not fire overnight" and treated
that as a failure. **That was wrong and is withdrawn.**

The task was registered on 2026-08-21 with a daily 02:15 trigger, so its first firing would have been
**2026-08-22 02:15**. The observation was made at approximately 01:33 on 2026-08-22 — *before* that
time. With `StartWhenAvailable=False`, nothing was missed, deferred or skipped; **the scheduled window
had simply not yet arrived.**

**No missed-cycle claim is made for that period, and no date is backfilled.**

---

## 9. Scope statements

**The frozen scientific design is unchanged.** This incident concerns execution transport only. The
collection time, local-time gate, universe, feature construction, validation thresholds, refusal
rules and the no-backfill rule are untouched. No hypothesis, estimand, gate or pre-registration is
modified, and no result is affected — none was ever produced by this path.

**No security setting was weakened.** No antivirus exclusion was added, no real-time protection was
disabled, no security product was reconfigured, uninstalled or bypassed, and **no quarantined file
was restored.** The quarantined runners remain in AVG's custody and will not be recovered; the
replacement is a different implementation, not a reinstatement of the detected one.

---

## 10. Disposition

The PowerShell orchestration transport is retired. It is replaced by a direct Python orchestrator
invoked by Task Scheduler without any shell wrapper, specified in the transport amendment committed
alongside this report.

Two follow-ups remain outside this report:

- The Task Scheduler Operational channel must be enabled before the replacement is registered, so a
  future removal is recorded rather than inferred.
- The task-removal cause stays `CAUSE_UNRESOLVED`. It is not closed, and it is not attributed.
