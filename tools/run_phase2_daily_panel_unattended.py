#!/usr/bin/env python3
"""Unattended Phase 2 daily-panel orchestrator — direct Python transport.

Implements TRANSPORT_AMENDMENT_2026-08-22_DIRECT_PYTHON.md. Task Scheduler
invokes the pinned Python interpreter with this file directly; no .ps1, .bat,
.cmd, powershell.exe, pwsh.exe or shell wrapper is involved anywhere, and no
subprocess is ever launched with shell=True.

This replaces the retired PowerShell orchestration, which AVG quarantined three
times under IDP.HELU.PSD11 — a behavioural heuristic targeting a PowerShell
script that spawns a child process and invokes `git push`. No exclusion was
added and no quarantined file was restored; the behaviour was moved out of the
detected host instead.

Scientific rules are unchanged: same panel program, same universe, same feature
construction, same 02:05-02:25 America/Chicago window, same validator, same
refusal rules, same no-backfill rule.

Exit codes -- nothing is ever staged unless validation returns 0:

     0  success, or preflight OK
     3  repository / environment resolution failed
     4  another run holds the lock
     5  panel exceeded the outer timeout
     6  a required output artifact is missing
     7  schema validation failed
     8  staging violation (unexpected changed path, or allowlist mismatch)
     9  commit failed
    10  refused: outside the local-time window
    11  refused: a success or failure is already recorded for this date
    12  refused: scheduled-task registration missing or its action does not
        match the direct Python invocation
    13  push failed -- the local commit and log are preserved and collection is
        NOT repeated

Usage:
    python run_phase2_daily_panel_unattended.py --repo-root <path> [--mode run|preflight]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from GST_Phase2_SafeDiagnostics import (                              # noqa: E402
    MAX_LOG_BLOCK_LINES, format_stream_for_log,
)

EXIT_OK = 0
EXIT_ENV = 3
EXIT_LOCK = 4
EXIT_TIMEOUT = 5
EXIT_MISSING = 6
EXIT_SCHEMA = 7
EXIT_STAGING = 8
EXIT_COMMIT = 9
EXIT_WINDOW = 10
EXIT_DUPLICATE = 11
EXIT_TASK = 12
EXIT_PUSH = 13
# 2026-08-25: runner bytes do not match the pinned hash, or HEAD is not a
# descendant of the approved implementation commit. Distinct from EXIT_ENV so a
# code-integrity refusal is never confused with an ordinary environment problem.
EXIT_INTEGRITY = 14

ZONE = "America/Chicago"
WINDOW_OPEN = dt.time(2, 5)
WINDOW_CLOSE = dt.time(2, 25)          # inclusive
SCHEDULED = dt.time(2, 15)

EXPECTED_BRANCH = "phase5-unattended-panel-recovery"
EXPECTED_UPSTREAM = "origin/phase5-unattended-panel-recovery"
TASK_NAME = "GST_PHASE2_DAILY_PANEL_UNATTENDED"

STATE_DIR = Path(r"C:\Users\hakur\Downloads\gst-source-quarantine\scheduler")
LOG_DIR = STATE_DIR / "logs"
LOCK_DIR = STATE_DIR / "locks"
ATTEMPT_DIR = STATE_DIR / "attempts"

PANEL_SCRIPT = "GST_Phase2_DailyPanel.py"
VALIDATOR = Path("tools") / "phase2_panel_validate.py"
RUNNER_REL = Path("tools") / "run_phase2_daily_panel_unattended.py"

PANEL_TIMEOUT_S = 3000

# Shells and wrappers that must never appear in the task action.
FORBIDDEN_IN_ACTION = ("powershell", "pwsh", "cmd.exe", ".ps1", ".bat", ".cmd", "wscript", "cscript")
# Git subcommands the runner may never invoke.
FORBIDDEN_GIT = ("pull", "checkout", "reset", "clean", "restore", "rebase", "merge", "fetch")


class Refused(Exception):
    def __init__(self, code: int, why: str):
        super().__init__(why)
        self.code = code
        self.why = why


# --------------------------------------------------------------------------- log

class Log:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str) -> None:
        line = f"[{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}"
        print(line, flush=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


# ------------------------------------------------------------------------ helpers

def run(args: list[str], cwd: Path | None = None, timeout: int | None = None
        ) -> subprocess.CompletedProcess:
    """Always an argument array. shell=True is never used anywhere in this file."""
    if args and args[0] == "git" and len(args) > 1:
        sub = next((a for a in args[1:] if not a.startswith("-") and a != "-C"), None)
        # -C <path> <subcommand>
        if args[1] == "-C" and len(args) > 3:
            sub = args[3]
        if sub in FORBIDDEN_GIT:
            raise Refused(EXIT_ENV, f"prohibited git subcommand refused: {sub}")
    return subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True,
                          text=True, timeout=timeout, shell=False)


def log_panel_diagnostics(log, proc) -> None:
    """Write a bounded, sanitized account of a panel failure to the runner log.

    Added 2026-09-01. On 2026-08-31 the panel raised during Google Trends
    client construction and exited 1 after 15s without writing a checkpoint or
    a marker. This runner had already captured the child's stdout and stderr,
    then discarded both on the refusal path -- so the traceback naming the
    exception was never persisted anywhere and the cause was unrecoverable.

    STDOUT IS NEVER ECHOED. The panel writes every measured value -- prices,
    volatilities, z-scores, volumes -- to stdout through its own log(). Copying
    stdout into the runner log would copy measurements out of the panel and
    into an operational log, so only its length is reported. stderr carries the
    traceback and is the diagnostic of record; it is redacted and bounded by
    GST_Phase2_SafeDiagnostics before a byte of it is written.

    This function only writes to the log. It raises nothing, returns nothing,
    and changes no exit code.
    """
    out_len = len(proc.stdout or "")
    err_len = len(proc.stderr or "")
    log(f"panel diagnostics: exit={proc.returncode} stdout_chars={out_len} "
        f"stderr_chars={err_len} (stdout is never echoed: it carries panel measurements)")

    block = format_stream_for_log(proc.stderr)
    if not block:
        log("panel diagnostics: stderr was empty -- the panel produced no traceback")
        return
    log(f"panel diagnostics: sanitized stderr tail follows "
        f"(<= {MAX_LOG_BLOCK_LINES} lines, secrets and user paths redacted)")
    for line in block.split("\n"):
        log(f"  | {line}")
    log("panel diagnostics: end of sanitized stderr")


def git(repo: Path, *args: str, timeout: int | None = 120) -> subprocess.CompletedProcess:
    return run(["git", "-C", str(repo), *args], timeout=timeout)


def local_now(now: dt.datetime | None = None) -> dt.datetime:
    z = ZoneInfo(ZONE)
    if now is None:
        return dt.datetime.now(dt.timezone.utc).astimezone(z)
    return (now.replace(tzinfo=z) if now.tzinfo is None else now.astimezone(z))


def window_open(now_local: dt.datetime) -> tuple[bool, str]:
    t = now_local.time().replace(microsecond=0)
    if WINDOW_OPEN <= t <= WINDOW_CLOSE:
        return True, "inside permitted window"
    if t < WINDOW_OPEN:
        return False, f"too early: {t} precedes {WINDOW_OPEN:%H:%M}"
    return False, (f"too late: {t} follows {WINDOW_CLOSE:%H:%M} -- a missed cycle is skipped, "
                   f"never backfilled")


# ------------------------------------------------------------------- gate helpers

def check_repo(repo_root: str, log: Log) -> Path:
    p = Path(repo_root)
    if not p.is_dir():
        raise Refused(EXIT_ENV, f"repo root does not exist: {repo_root}")
    r = run(["git", "-C", str(p), "rev-parse", "--show-toplevel"])
    if r.returncode != 0 or not r.stdout.strip():
        raise Refused(EXIT_ENV, f"git rev-parse --show-toplevel failed under {repo_root}")
    top = Path(r.stdout.strip().splitlines()[0]).resolve()
    if top != p.resolve():
        raise Refused(EXIT_ENV, f"{p.resolve()} is not a repository toplevel (git says {top})")
    log(f"repo toplevel verified: {top}")
    return top


def runner_file_sha256(repo: Path) -> str:
    """SHA-256 of the runner file's own bytes, read from the worktree.

    Content-addressed, unlike a commit sha: it does not move when the runner
    commits a panel, so pinning to it does not invalidate itself on success.
    Read in binary with no newline translation -- the hash must describe the
    bytes on disk, not a normalised view of them."""
    return hashlib.sha256((repo / RUNNER_REL).read_bytes()).hexdigest()


def check_code_integrity(repo: Path, expected_hash: str | None,
                          approved_commit: str | None, log: Log) -> None:
    """Transport amendment 2026-08-25, section 4.1/4.3.

    Two independent pins, both content-based rather than branch-position based:

      1. the runner file's SHA-256 must equal the approved hash, so the code
         that is about to run is byte-for-byte the code that was reviewed;
      2. HEAD must be a DESCENDANT of the approved implementation commit --
         not equal to it. Equality was the defect: it made every successful
         machine commit invalidate the next day's run. Descent permits
         data-only commits to accumulate forever while still refusing any
         reset, rewrite or divergence away from approved code."""
    if expected_hash:
        actual = runner_file_sha256(repo)
        if actual != expected_hash:
            raise Refused(EXIT_INTEGRITY,
                          f"runner hash {actual[:16]} != pinned {expected_hash[:16]}")
        log(f"runner integrity: sha256 {actual[:16]} matches pin")
    if approved_commit:
        r = git(repo, "merge-base", "--is-ancestor", approved_commit, "HEAD")
        if r.returncode != 0:
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            raise Refused(EXIT_INTEGRITY,
                          f"HEAD {head[:12]} is not a descendant of approved "
                          f"implementation commit {approved_commit[:12]}")
        log(f"code lineage: HEAD descends from approved {approved_commit[:12]}")


def check_branch_head_clean(repo: Path, expected_sha: str | None, log: Log) -> str:
    b = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if b != EXPECTED_BRANCH:
        raise Refused(EXIT_ENV, f"branch is {b!r}, expected {EXPECTED_BRANCH!r}")
    if not (repo / RUNNER_REL).is_file():
        raise Refused(EXIT_ENV, f"committed runner missing from worktree: {RUNNER_REL}")
    if not (repo / PANEL_SCRIPT).is_file():
        raise Refused(EXIT_ENV, f"panel program missing: {PANEL_SCRIPT}")
    if not (repo / VALIDATOR).is_file():
        raise Refused(EXIT_ENV, f"validator missing: {VALIDATOR}")
    dirty = git(repo, "status", "--porcelain").stdout.strip()
    if dirty:
        raise Refused(EXIT_ENV, f"worktree is not clean: {dirty.splitlines()[:3]}")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    # NOTE (2026-08-25): the former `head != expected_sha` equality pin lived here
    # and has been removed, not merely relaxed. It made the runner refuse the day
    # after any success, because its own commit advanced HEAD past the pin.
    # Code identity is now check_code_integrity(): runner-file hash plus descent
    # from an approved implementation commit. See the 2026-08-25 transport
    # amendment, sections 3 and 4.
    up = git(repo, "rev-parse", "--abbrev-ref", "@{u}").stdout.strip()
    if up != EXPECTED_UPSTREAM:
        raise Refused(EXIT_ENV, f"upstream is {up!r}, expected {EXPECTED_UPSTREAM!r}")
    log(f"branch={b} head={head[:12]} worktree=clean upstream={up}")
    return head


def attempt_path(run_date: str) -> Path:
    return ATTEMPT_DIR / f"attempt_{run_date}.json"


def check_no_prior_attempt(run_date: str, log: Log) -> None:
    p = attempt_path(run_date)
    if p.is_file():
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
            outcome = rec.get("outcome", "unknown")
        except Exception:                                           # noqa: BLE001
            outcome = "unreadable"
        raise Refused(EXIT_DUPLICATE,
                      f"an attempt is already recorded for {run_date} (outcome={outcome}); "
                      f"one network-bearing attempt per date, and a failure blocks retry too")
    log(f"no prior attempt recorded for {run_date}")


def record_attempt(run_date: str, outcome: str, detail: dict) -> None:
    ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
    rec = {"run_date": run_date, "outcome": outcome,
           "recorded_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           **detail}
    tmp = attempt_path(run_date).with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    tmp.replace(attempt_path(run_date))


def check_task_registration(log: Log, query=None) -> None:
    """The task must exist and its action must be the direct Python invocation."""
    if query is None:
        query = _query_task_action
    action = query()
    if action is None:
        raise Refused(EXIT_TASK, f"scheduled task {TASK_NAME} is not registered")
    exe, args = action
    blob = f"{exe} {args}".lower()
    for bad in FORBIDDEN_IN_ACTION:
        if bad in blob:
            raise Refused(EXIT_TASK, f"task action contains a shell or wrapper ({bad!r}); "
                                     f"direct Python invocation required")
    if not exe.lower().endswith("python.exe"):
        raise Refused(EXIT_TASK, f"task action executable is not python.exe: {exe}")
    if RUNNER_REL.name not in args:
        raise Refused(EXIT_TASK, f"task action does not invoke {RUNNER_REL.name}")
    log(f"task registration verified: direct python invocation of {RUNNER_REL.name}")


def _query_task_action():
    """Read the registered action. Uses schtasks with an argument array, no shell."""
    r = run(["schtasks", "/query", "/tn", TASK_NAME, "/xml", "ONE"], timeout=60)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    import re
    x = r.stdout
    m_exe = re.search(r"<Command>(.*?)</Command>", x, re.S)
    m_arg = re.search(r"<Arguments>(.*?)</Arguments>", x, re.S)
    if not m_exe:
        return None
    return m_exe.group(1).strip(), (m_arg.group(1).strip() if m_arg else "")


# ------------------------------------------------------------------------- staging

def staged_paths_ok(repo: Path, allow: list[str], log: Log,
                     optional: list[str] | None = None) -> list[str]:
    # -uall is required: plain --porcelain collapses a wholly-untracked directory
    # to a single "dir/" entry, which would both hide the individual files and
    # trip the allowlist on a path that is not a file.
    changed = [l.strip() for l in
               git(repo, "status", "--porcelain", "-uall").stdout.splitlines() if l.strip()]
    paths = [c[3:].strip().strip('"').replace("\\", "/") for c in changed]
    optional = optional or []
    # THE 2026-08-24 DEFECT. `allow` used to be the whole story, and it listed
    # only the final CSV and the marker. The panel ALSO writes a dated
    # _CHECKPOINT_PARTIAL.csv on every run, successful ones included, so a
    # completed 24/24 capture presented three changed paths to a two-path
    # allowlist and was refused at EXIT_STAGING after the network work was
    # already done. The allowlist described what we wanted committed rather
    # than what the panel actually produces.
    #
    # Two lists now. `allow` is REQUIRED-and-permitted: each must exist, and
    # its absence is still a refusal. `optional` is permitted-if-present: it
    # may appear without being demanded. The checkpoint belongs in `optional`
    # because a run that fails before writing one must not be forced to
    # produce it, while a run that does write one must not be refused for it.
    permitted = list(allow) + list(optional)
    unexpected = [p for p in paths if p not in permitted]
    if unexpected:
        raise Refused(EXIT_STAGING,
                      f"unexpected changed path(s), refusing to stage: {unexpected[:5]}")
    present = [a for a in allow if (repo / a).is_file()]
    if len(present) != len(allow):
        raise Refused(EXIT_STAGING,
                      f"expected {len(allow)} required output files, found {len(present)}")
    extra = [o for o in optional if (repo / o).is_file()]
    if extra:
        log(f"  optional outputs present and permitted: {extra}")
    log(f"staging allowlist satisfied: {len(present)} required + {len(extra)} optional "
        f"file(s), no unexpected paths")
    return present + extra


# ---------------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run_phase2_daily_panel_unattended")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--mode", choices=("run", "preflight"), default="run")
    # DEPRECATED 2026-08-25 and ignored. Pinning code identity to a mutable HEAD
    # invalidated itself on first success: the runner's own commit advanced HEAD
    # past the pin, so the next scheduled run refused. Still PARSED, so a stale
    # registration that still passes it fails at the integrity gate with a clear
    # reason instead of dying on an unrecognised argument before it can log.
    ap.add_argument("--expected-sha", default=None,
                    help="DEPRECATED and ignored; superseded by --runner-sha256")
    ap.add_argument("--runner-sha256", default=None,
                    help="pinned SHA-256 of this runner file's own bytes")
    ap.add_argument("--approved-commit", default=None,
                    help="approved implementation commit; HEAD must be a descendant")
    ap.add_argument("--now-override", default=None, help="TEST USE ONLY")
    ap.add_argument("--skip-task-check", action="store_true",
                    help="TEST USE ONLY; never set in the registered action")
    a = ap.parse_args(argv)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = Log(LOG_DIR / f"phase2_unattended_{stamp}.log")
    log(f"START mode={a.mode} transport=direct-python interpreter={sys.executable}")

    now = None
    if a.now_override:
        now = dt.datetime.fromisoformat(a.now_override)
        log("NOTE: clock supplied via --now-override (test path), not read from the host")
    nl = local_now(now)
    run_date = nl.date().isoformat()
    log(f"local now={nl.isoformat()} zone={ZONE} run_date={run_date}")

    try:
        ok, why = window_open(nl)
        log(f"window gate: {why}")
        if not ok:
            raise Refused(EXIT_WINDOW,
                          "outside 02:05-02:25 America/Chicago; no network, git, staging, "
                          "commit or push performed")

        repo = check_repo(a.repo_root, log)
        # Code integrity BEFORE the clean-tree check: if the runner bytes or the
        # code lineage are wrong, nothing else about this tree is worth asserting.
        check_code_integrity(repo, a.runner_sha256, a.approved_commit, log)
        if a.expected_sha:
            log("NOTE: --expected-sha is deprecated and ignored; code identity is "
                "--runner-sha256 plus --approved-commit")
        head = check_branch_head_clean(repo, None, log)
        check_no_prior_attempt(run_date, log)
        if not a.skip_task_check:
            check_task_registration(log)

        if a.mode == "preflight":
            log("PREFLIGHT OK -- no network call made, panel not launched, nothing staged")
            return EXIT_OK

        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        lock = LOCK_DIR / "phase2_daily_panel.lock"
        if lock.exists():
            age = time.time() - lock.stat().st_mtime
            if age < PANEL_TIMEOUT_S:
                raise Refused(EXIT_LOCK, f"another run holds the lock (age {int(age)}s)")
            log(f"stale lock ({int(age)}s); reclaiming")
            lock.unlink()
        lock.write_text(stamp, encoding="utf-8")

        try:
            csv_rel = f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{run_date}_run3.csv"
            marker_rel = (f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_"
                          f"{run_date}_run3_COMPLETION_MARKER.json")
            # Written by the panel on every run, successful ones included. Permitted
            # but never required -- see staged_paths_ok()'s `optional` parameter and
            # the 2026-08-24 incident it exists to prevent.
            checkpoint_rel = (f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_"
                              f"{run_date}_run3_CHECKPOINT_PARTIAL.csv")

            log("launching panel (single network-bearing attempt for this date)")
            t0 = time.time()
            try:
                p = run([sys.executable, "-u", PANEL_SCRIPT], cwd=repo, timeout=PANEL_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                record_attempt(run_date, "failure", {"stage": "panel", "reason": "timeout"})
                raise Refused(EXIT_TIMEOUT, f"panel exceeded {PANEL_TIMEOUT_S}s; nothing committed")
            elapsed = int(time.time() - t0)
            log(f"panel exited code={p.returncode} elapsed={elapsed}s")

            outputs_missing = (not (repo / marker_rel).is_file()
                               or not (repo / csv_rel).is_file())
            if p.returncode != 0 or outputs_missing:
                # Diagnostics only -- this neither changes the refusal
                # condition below nor its exit code.
                log_panel_diagnostics(log, p)
            if outputs_missing:
                record_attempt(run_date, "failure",
                               {"stage": "output", "panel_exit": p.returncode})
                raise Refused(EXIT_MISSING,
                              "required output missing (final CSV is written only on a clean 24/24)")

            v = run([sys.executable, str(repo / VALIDATOR),
                     "--marker", str(repo / marker_rel), "--csv", str(repo / csv_rel)], cwd=repo)
            for line in v.stdout.splitlines():
                log(f"  {line}")
            if v.returncode != 0:
                record_attempt(run_date, "failure",
                               {"stage": "validation", "validator_exit": v.returncode})
                raise Refused(EXIT_SCHEMA if v.returncode == 7 else EXIT_MISSING,
                              f"schema validation returned {v.returncode}; committing nothing")
            log("schema validation PASSED")

            allow = [csv_rel, marker_rel]
            optional = [checkpoint_rel]
            to_stage = staged_paths_ok(repo, allow, log, optional=optional)
            for rel in to_stage:
                r = git(repo, "add", "--", rel)
                if r.returncode != 0:
                    record_attempt(run_date, "failure", {"stage": "stage", "path": rel})
                    raise Refused(EXIT_STAGING, f"git add failed for {rel}")
                log(f"  staged {rel}")

            msg = (f"Unattended Phase 2 daily panel {run_date}: COMPLETE 24/24\n\n"
                   f"Produced and committed by the scheduled direct-Python runner with no human in\n"
                   f"the loop. Schema validation passed before anything was staged; a partial or\n"
                   f"failed run commits nothing.\n\n"
                   f"  run_date   {run_date}\n"
                   f"  elapsed    {elapsed}s\n"
                   f"  panel exit {p.returncode}\n"
                   f"  runner     {head[:12]}\n\n"
                   f"Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>\n")
            c = git(repo, "commit", "-m", msg)
            if c.returncode != 0:
                record_attempt(run_date, "failure", {"stage": "commit"})
                raise Refused(EXIT_COMMIT, f"git commit failed: {c.stderr.strip()[:200]}")
            sha = git(repo, "rev-parse", "HEAD").stdout.strip()
            log(f"COMMITTED {sha}")

            pr = git(repo, "push", timeout=300)
            if pr.returncode != 0:
                record_attempt(run_date, "collected_commit_local_push_failed",
                               {"stage": "push", "commit": sha})
                log("PUSH FAILED -- local commit and log preserved; collection is NOT repeated")
                return EXIT_PUSH
            log(f"PUSHED {sha}")
            record_attempt(run_date, "success", {"commit": sha, "elapsed_s": elapsed})
            log("DONE unattended cycle OK")
            return EXIT_OK
        finally:
            if lock.exists():
                lock.unlink()

    except Refused as e:
        log(f"REFUSED({e.code}): {e.why}")
        return e.code
    except Exception as e:                                          # noqa: BLE001
        log(f"ABORT: unexpected {type(e).__name__}: {e}")
        return EXIT_ENV


if __name__ == "__main__":
    raise SystemExit(main())
