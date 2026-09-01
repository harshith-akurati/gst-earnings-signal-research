# Phase 2 collector — observability maintenance

**Dated:** 2026-09-01
**Branch:** `phase2-observability-maintenance-20260901`
**Base:** `d49e9834b6687259c782f24b1a3863aaabf76ea1` (live `phase5-unattended-panel-recovery` HEAD)
**Status:** `DRAFT — NOT DEPLOYED.` The scheduled task, its runner hash pin and the live branch are untouched.

---

## 1. Why this exists

Two consecutive unattended cycles failed, and both were diagnosed only by inference — not because
the evidence was ambiguous at the time, but because **the collector captured the reason and then
threw it away.**

### 1.1 — 2026-08-29: the implied-volatility leg failed 24/24 and recorded no reason

Every one of the 24 tickers failed the IV leg. The checkpoint persisted `iv_status = error` on all
24 rows and `iv_error = nan` on all 24 rows. `failed_source_counts.iv = 24`;
`implied_volatility` completeness `0.0 %`; every other leg `ok` on 24/24.

**Root cause, now identified rather than hypothesised.** `run_bounded()` recorded a failed call as:

```python
except Exception as e:
    result_box["error"] = str(e)
```

`str()` of an exception constructed with no arguments is **the empty string**. The empty string was
written to the `iv_error` column, the CSV round-tripped it as an empty cell, and it read back as
`nan`. The status said the leg failed; the reason said nothing.

The operational cost was concrete: a transient provider outage and a permanent entitlement change
produce *the same retained evidence*, so the 2026-08-29 incident could not be closed on its own
evidence. It was only closed the following day, by the 2026-08-30 cycle succeeding on unchanged code.

### 1.2 — 2026-08-31: the Google Trends bootstrap failure was captured and discarded

The panel exited 1 after 15 s having written **no** checkpoint and **no** completion marker. The
panel's only `sys.exit(1)` runs *after* both are written, so the process died earlier, on an
unhandled exception. Its own run log stops immediately after the scope-disclosure banner — the very
next statement is the `TrendReq(...)` constructor.

pytrends' `TrendReq.__init__` calls `GetGoogleCookie()`, a live request, and that helper catches
only `requests.exceptions.ProxyError`; every other exception escapes the constructor uncaught.

The runner launches the panel with `capture_output=True`, so **it held the traceback in memory** —
and then raised `Refused(EXIT_MISSING, ...)` without writing either stream anywhere. The exception
class that killed the run is unrecoverable from retained evidence.

### 1.3 — The common defect

Neither incident was an IV problem or a Trends problem. Both were the same failure of the collector
to write down what it already knew. That is what this change fixes, and it is the whole of what this
change fixes.

## 2. Why this is an observability correction, not a data-method change

**Nothing about what is measured, how it is measured, or what qualifies as a valid observation is
touched by this branch.**

| Untouched | Confirmed by |
|---|---|
| The six locked research fields and their definitions | no change to `COLUMN_ORDER` semantics or any value assignment |
| The clean-24/24 completeness requirement | `is_run_complete()` unmodified |
| `all_six_fields_clean` | computation unmodified |
| The eligibility ladder, the registry, HYP-01, F5, the SESOI | not opened, not referenced |
| Every measurement, provenance and note field on a **successful** leg | the post-condition skips any leg whose status is exactly `"ok"`, and a test asserts a fully successful row is left byte-identical |
| Panel schema, column count, validator contract | unchanged; the committed validator is not modified |
| Every runner exit-code meaning | unchanged, `EXIT_MISSING` is still `6` |

A change is a *data-method* change if it can alter which observations exist or what their values
are. This one cannot: it only writes text into `<source>_error` cells that were **empty on failed
legs**, and text into a runner log. A failed leg stays failed, and a missing value stays missing.

## 3. What changed

### 3.1 `GST_Phase2_SafeDiagnostics.py` — new, the single formatting authority

One module, imported by both the panel and the runner. No project imports, no I/O, no network — it
is pure string handling, so it is safe to import under a socket block.

- `format_exception(exc)` — bounded, redacted, and **never empty**. The class name always survives.
- `sanitize_text(value)` — redact, normalise newlines, strip control characters, bound length.
- `format_stream_for_log(stream)` — prepare a captured stderr stream: redacted, tail-preserving
  (the exception line is at the end of a traceback), line- and character-bounded.

### 3.2 `GST_Phase2_DailyPanel.py`

| Change | Effect |
|---|---|
| `run_bounded()` records `format_exception(e)`, not `str(e)` | **the direct 2026-08-29 fix**; fixes every bounded leg at one point, IV included |
| `realized_vol` and `gst` legs use `format_exception(e)` | no leg persists a raw `str(exc)` |
| New `enforce_error_persistence(row, fallback=None)` | post-condition: a leg that did not succeed carries a non-empty sanitized reason |
| Applied at `process_ticker()` return, after the Wikipedia second pass, and on the per-ticker isolation fallback row | every row that reaches a checkpoint or marker has passed the post-condition |
| `TrendReq(...)` wrapped in `try/except` that logs `format_exception(e)` and **re-raises** | the 2026-08-31 failure would now name itself in the panel's own run log |

The re-raise is deliberate: the run must still fail closed with no artifacts. The handler adds a log
line and changes nothing else.

### 3.3 `tools/run_phase2_daily_panel_unattended.py`

New `log_panel_diagnostics(log, proc)`, called when the panel exits non-zero **or** required output
is missing, *before* the existing refusal.

The refusal condition itself is unchanged. The old test was inlined into `outputs_missing` and that
variable alone still gates `raise Refused(EXIT_MISSING, ...)`, so the refusal fires on exactly the
same states, with exactly the same code and message, as before.

## 4. Redaction guarantees

Every string this branch persists — into a CSV cell or a runner log — passes through
`sanitize_text()` first. Nothing is written as a raw `str(exc)` or `repr(exc)`.

| Guarantee | Rule |
|---|---|
| Authorization material | `Authorization`, `Proxy-Authorization`, `WWW-Authenticate`, `X-Api-Key`, `X-Auth-Token`, `X-Access-Token`, `Cookie`, `Set-Cookie` values replaced with `<redacted>` |
| Bearer/basic tokens | `Bearer <token>` / `Basic <token>` redacted even with no header name present |
| Query-string secrets | `api_key`, `apikey`, `access_token`, `refresh_token`, `id_token`, `token`, `secret`, `client_secret`, `password`, `passwd`, `pwd`, `signature`, `sig`, `session_id`, `credential(s)`, `auth`, `key` redacted; **non-secret parameters are kept**, so the failing endpoint is still identifiable |
| JSON and quoted assignments | `"token": "…"` and `password='…'` forms redacted |
| User-specific absolute paths | `C:\Users\<name>`, `/c/Users/<name>`, `/home/<name>`, `/Users/<name>`, `%USERPROFILE%`, `$HOME` → `<HOME>`; the non-identifying remainder of the path survives |
| Control characters | stripped |
| Length | `<source>_error` ≤ **500** chars; runner log block ≤ **4000** chars and ≤ **40** lines; truncation always marked with `...[truncated]`, never silent |
| Tabular safety | anything persisted to a CSV cell is collapsed to a single line, so it cannot break a row |

### 4.1 The measurement guarantee — and its exact limit

**Panel stdout is never echoed into the runner log.** The panel writes every measured value —
prices, volatilities, z-scores, volumes — to stdout through its own `log()`. The runner reports only
`stdout_chars=<n>` and states in the log line that stdout is deliberately not echoed. A regression
test drives the real runner against a stub panel that prints measurement-shaped sentinels to stdout
and asserts that **not one** of them reaches the runner log.

Only **stderr** is included, because the traceback is the entire point. Stated plainly rather than
glossed: a Python traceback contains file paths, line numbers, source text and the exception
message, and an exception message *could in principle* embed a numeric argument from the failing
call. Two things bound that residual — measurement logging goes exclusively to stdout, which is
never included; and every stderr line is redacted and bounded before it is written. This residual is
disclosed, not claimed to be zero.

## 5. Fail-closed and no-backfill rules — unchanged

| Rule | Status |
|---|---|
| The final CSV is written **only** on a clean 24/24 | unchanged |
| A failed partial is never committed | unchanged; a test asserts no commit and no HEAD movement after a panel failure |
| `EXIT_MISSING` = **6** | unchanged, asserted by test |
| One network-bearing attempt per date | unchanged; a test asserts `launching panel` appears exactly once |
| No automatic retry | none added |
| No backfill of a missed date | none added; 2026-08-29 and 2026-08-31 remain missing observations |
| No fallback provider | none added |
| No imputation, substitution, carry-forward or default of a failed value | none added; a test asserts the post-condition creates no measurement field and leaves `implied_volatility` `None` |
| Success-path staging, commit, push and remote equality | unchanged; a test asserts `EXIT_OK`, exactly one new commit, and local == upstream |

**A better error message is not a reason to relax a gate.** Nothing here lowers a threshold.

## 6. Deployment requirements

**This branch is not deployed and must not be deployed silently.** The next scheduled cycle
(2026-09-01 02:15 CT) will run the **unchanged** live code.

1. **The runner's SHA-256 pin must be updated in the same maintenance window as the merge.**
   The task action pins the runner by content hash:

   | | |
   |---|---|
   | Currently registered pin | `ff3cd77756846486b5c06c6d9cebab5c1ffcf34ad7da4cb91a85119bb2211802` |
   | This branch's runner, as a fresh checkout lands it on disk | `c27ebf5d2e17c2a65ba1b59e30d4ad919ffb075e4b5ab199b2c548ea4f31e497` |
   | This branch's runner, stored-blob (LF) form | `be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c` |

   **The pin is line-ending dependent, and this is a pre-existing hazard that predates this
   branch.** The repository runs with `core.autocrlf=true`, and `.gitattributes` disables
   conversion only for the panel's own output files -- not for source. So the runner is stored
   with LF and checked out with CRLF, and the two forms hash differently. The runner hashes the
   file *as it exists on disk*, so the value to register is the on-disk form.

   The currently live worktree happens to hold the LF form on disk (`ff3cd777...`, equal to its
   stored blob) because that file has sat there unmodified since it was authored and has never
   been re-materialised by a checkout. A fresh checkout of the same commit would produce the CRLF
   form and a different hash. Nothing is wrong with the live pin today, but it is luck rather than
   design, and it will not survive a re-clone.

   **Therefore: after merging, recompute the hash of the runner file as it actually exists on disk
   in the live worktree and register THAT value.** Do not copy a hash out of this document. On this
   machine a merge that rewrites the file is expected to produce `c27ebf5d...`, but verify it rather
   than assume it.

   Making the pin line-ending independent -- e.g. by adding a `-text` or `eol=lf` attribute for
   `tools/*.py` -- is a real improvement and is deliberately **not** done here. It changes stored
   bytes for files outside this fix's scope and is a separate reviewed decision.

   Merging this branch **without** re-registering the task with the new `--runner-sha256` makes the
   next unattended run refuse with `EXIT_INTEGRITY(14)` before any network call. That is the pin
   working correctly — but it is a silent outage if nobody expects it.

2. **`--approved-commit 73eb39435c9cb850399517a23dde1c0379b5b7da` does not change.** This branch
   descends from `d49e9834`, which descends from the approved commit, so the lineage gate still
   passes. Verify with `git merge-base --is-ancestor` after the merge, before re-registering.

3. **Deploy between cycles, never during one.** The permitted window is 02:05–02:25 America/Chicago.
   Merge, re-pin and verify outside it.

4. **`GST_Phase2_SafeDiagnostics.py` must be present in the repository root at run time.**
   The runner now imports it, resolving the repository root from its own `__file__`. It is
   committed on this branch, so a normal merge satisfies this — but the runner file must never
   be deployed on its own without the module beside it, or it will fail at import before any
   gate runs.

5. **Deploy on a clean live worktree.** The runner refuses on any dirty path, untracked ones
   included.

6. **First cycle after deployment is a verification cycle.** A clean 24/24 must still produce
   `COMPLETE`, one commit and a push, with **no** `panel diagnostics:` line in the runner log. A
   diagnostics line on a successful run would mean this change altered the success path, and should
   be treated as a regression.

7. **Do not backfill.** 2026-08-29 and 2026-08-31 stay missing. This change improves the record of
   *future* failures; it does not recover past ones.

## 7. What this change does not fix

- It does not make the IV leg more reliable. It makes an IV failure legible.
- It does not make the Trends bootstrap more reliable, and it does not add a retry around it.
- It cannot recover the 2026-08-29 IV exception or the 2026-08-31 Trends exception. Those are gone.
- It does not diagnose the provider behaviour behind either incident. That is separate work, and it
  must not backfill any missed date.
