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
   The task action pins the runner by content hash, and `check_code_integrity()` hashes the file
   **as it exists on disk**.

   | | |
   |---|---|
   | Currently registered pin | `ff3cd77756846486b5c06c6d9cebab5c1ffcf34ad7da4cb91a85119bb2211802` |
   | **This branch's runner -- committed blob** | **`be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c`** |
   | **This branch's runner -- fresh checkout, on disk** | **`be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c`** |
   | *(pre-fix CRLF form, for reference only -- no longer produced)* | `c27ebf5d2e17c2a65ba1b59e30d4ad919ffb075e4b5ab199b2c548ea4f31e497` |

   **The blob hash and the fresh-checkout on-disk hash are now identical.** That is the whole point
   of the fix below, and it is what makes the pin reproducible.

   Merging **without** re-registering `--runner-sha256` makes the next unattended run refuse with
   `EXIT_INTEGRITY(14)` before any network call. That is the pin working correctly -- but it is a
   silent outage if nobody expects it.

### 6.1 Why the pin was not reproducible, and the exact rule that fixes it

The repository runs with `core.autocrlf=true`, and `.gitattributes` disabled conversion only for
the panel's own **output** files, not for source. The runner was therefore stored with LF and
written to the working tree with CRLF, so its on-disk hash depended on how the file happened to
land rather than on what was committed:

| Form | SHA-256 |
|---|---|
| stored blob (LF) | `be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c` |
| CRLF checkout (what a fresh clone produced) | `c27ebf5d2e17c2a65ba1b59e30d4ad919ffb075e4b5ab199b2c548ea4f31e497` |

The live worktree holds the LF form (`ff3cd777...`, equal to its own blob) **only because that file
has sat there unmodified since it was authored and has never been re-materialised by a checkout.**
This was verified empirically before the fix: a fresh `--local` clone of this branch at commit
`970d2c37` under `core.autocrlf=true` produced `c27ebf5d...`, not the blob hash. A re-clone of the
live branch would therefore have broken its own pin, with nothing but a line ending as the cause.

**The rule, added to `.gitattributes` at the repository root, verbatim:**

```gitattributes
tools/run_phase2_daily_panel_unattended.py    text eol=lf
```

`text eol=lf` normalises the file to LF in the object store and writes it to the working tree with
LF **regardless of `core.autocrlf` or `core.eol`**, so the on-disk SHA-256 equals the committed
blob's SHA-256 on every machine and every clone.

It is scoped to this exact path deliberately. **This is not a repository-wide line-ending change**,
and no other file's stored bytes are affected. In particular the existing `-text` rules that keep
the panel's captured outputs byte-exact are untouched.

### 6.2 Fresh-worktree verification procedure

Run this before re-registering the pin, or after any change to line-ending configuration. It is
also automated as `test_phase2_runner_pin_reproducibility.py`.

```bash
# 1. What is committed?
git cat-file blob HEAD:tools/run_phase2_daily_panel_unattended.py | sha256sum
#    -> be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c

# 2. Is the attribute actually in force?
git check-attr text eol -- tools/run_phase2_daily_panel_unattended.py
#    -> tools/run_phase2_daily_panel_unattended.py: text: set
#    -> tools/run_phase2_daily_panel_unattended.py: eol: lf

# 3. What does a FRESH checkout put on disk, under the hazardous setting?
git -c core.autocrlf=true clone --quiet --local --no-hardlinks \
    --branch <branch> --single-branch . /tmp/pincheck
sha256sum /tmp/pincheck/tools/run_phase2_daily_panel_unattended.py
#    -> be5afc86aa85fe95fec40869d9f0cfbeb36ead1ed582c15df78ddd36ce28f06c

# 4. The two MUST match. If they do not, do not deploy.
```

**Proof that they match.** `test_phase2_runner_pin_reproducibility.py` asserts byte-for-byte
equality between the committed blob and a fresh `core.autocrlf=true` checkout, and re-materialises
the file under all nine combinations of `core.autocrlf` in {`true`, `false`, `input`} x `core.eol`
in {unset, `crlf`, `lf`}, requiring a single hash across every one. It also carries a **control
case**: a synthetic repository holding the identical bytes at the identical path but *without* the
rule, which must produce a *different* hash under `core.autocrlf=true`. That control is what stops
the guard from passing vacuously -- if the rule were deleted, the control would start matching and
the test would fail.

2. **Recompute and verify the live on-disk hash before updating the task pin.**
   Do not copy a hash out of this document into the task registration. After merging, in the live
   worktree:

   ```bash
   git cat-file blob HEAD:tools/run_phase2_daily_panel_unattended.py | sha256sum   # committed
   sha256sum tools/run_phase2_daily_panel_unattended.py                            # on disk
   ```

   **The two must be equal, and that equal value is what gets registered.** If they differ, the
   attribute is not in force in that worktree -- stop and investigate rather than registering the
   on-disk value, because a pin that only matches one machine is the defect this fix exists to
   remove.

   Note that a merge will not necessarily re-materialise the file in an existing worktree. If the
   live worktree still holds pre-merge bytes, force it with
   `rm tools/run_phase2_daily_panel_unattended.py && git checkout -- tools/run_phase2_daily_panel_unattended.py`
   and re-hash. Do this outside the 02:05-02:25 window and on a clean tree.

3. **`--approved-commit 73eb39435c9cb850399517a23dde1c0379b5b7da` does not change.** This branch
   descends from `d49e9834`, which descends from the approved commit, so the lineage gate still
   passes. Verify with `git merge-base --is-ancestor` after the merge, before re-registering.

4. **Deploy between cycles, never during one.** The permitted window is 02:05–02:25 America/Chicago.
   Merge, re-pin and verify outside it.

5. **`GST_Phase2_SafeDiagnostics.py` must be present in the repository root at run time.**
   The runner now imports it, resolving the repository root from its own `__file__`. It is
   committed on this branch, so a normal merge satisfies this — but the runner file must never
   be deployed on its own without the module beside it, or it will fail at import before any
   gate runs.

6. **Deploy on a clean live worktree.** The runner refuses on any dirty path, untracked ones
   included.

7. **First cycle after deployment is a verification cycle.** A clean 24/24 must still produce
   `COMPLETE`, one commit and a push, with **no** `panel diagnostics:` line in the runner log. A
   diagnostics line on a successful run would mean this change altered the success path, and should
   be treated as a regression.

8. **Do not backfill.** 2026-08-29 and 2026-08-31 stay missing. This change improves the record of
   *future* failures; it does not recover past ones.

## 7. What this change does not fix

- It does not make the IV leg more reliable. It makes an IV failure legible.
- It does not make the Trends bootstrap more reliable, and it does not add a retry around it.
- It cannot recover the 2026-08-29 IV exception or the 2026-08-31 Trends exception. Those are gone.
- It does not diagnose the provider behaviour behind either incident. That is separate work, and it
  must not backfill any missed date.
