#!/usr/bin/env python3
# Offline tests for the direct-Python unattended panel orchestrator.
#
# Sockets are blocked before any project import. The real panel is NEVER run:
# every scenario uses a synthetic temporary git repository with a stub panel
# program, a stub validator and an injected task-registration query. No network,
# no provider, no financial data, no outcome access, no backfill.
#
# Run directly:  python test_phase2_direct_python_runner.py

from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path


class NetworkBlocked(RuntimeError):
    pass


def _no_net(*a, **k):
    raise NetworkBlocked("network access attempted")


socket.socket.connect = _no_net
socket.socket.connect_ex = _no_net
socket.create_connection = _no_net
socket.getaddrinfo = _no_net

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import run_phase2_daily_panel_unattended as R                       # noqa: E402

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, shell=False)


IN_WINDOW = "2026-08-22T02:15:00"
TOO_EARLY = "2026-08-22T02:04:00"
TOO_LATE = "2026-08-22T02:26:00"
BACKFILL = "2026-08-22T09:30:00"
RUN_DATE = "2026-08-22"

GOOD_TASK = ("C:\\Python\\python.exe",
             '"C:\\repo\\tools\\run_phase2_daily_panel_unattended.py" --repo-root "C:\\repo"')
PS_TASK = ("C:\\windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
           '-File "C:\\x\\Invoke-Phase2DailyPanelUnattended.ps1"')

CSV_REL = f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{RUN_DATE}_run3.csv"
MARK_REL = f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{RUN_DATE}_run3_COMPLETION_MARKER.json"


class Fixture:
    """A synthetic repo + isolated state dirs. Never touches the real repository."""

    def __init__(self, panel="ok", validator="ok"):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.remote = self.tmp / "remote.git"
        (self.repo / "tools").mkdir(parents=True)
        (self.repo / "Live Signal Engine").mkdir(parents=True)

        sh(["git", "init", "--quiet", "--bare", str(self.remote)])
        sh(["git", "init", "--quiet", "-b", R.EXPECTED_BRANCH, str(self.repo)])
        for k, v in (("user.email", "t@example.invalid"), ("user.name", "T"),
                     ("commit.gpgsign", "false")):
            sh(["git", "-C", str(self.repo), "config", k, v])

        # stub panel: writes the two outputs (or not), per mode
        panel_src = {
            "ok": (f"from pathlib import Path\n"
                   f"Path(r'{CSV_REL}').write_text('x', encoding='utf-8')\n"
                   f"Path(r'{MARK_REL}').write_text('{{}}', encoding='utf-8')\n"),
            "fail": "import sys; sys.exit(1)\n",
            "noout": "pass\n",
            "extra": (f"from pathlib import Path\n"
                      f"Path(r'{CSV_REL}').write_text('x', encoding='utf-8')\n"
                      f"Path(r'{MARK_REL}').write_text('{{}}', encoding='utf-8')\n"
                      f"Path('STRAY_ARTIFACT.txt').write_text('nope', encoding='utf-8')\n"),
        }[panel]
        (self.repo / R.PANEL_SCRIPT).write_text(panel_src, encoding="utf-8")
        (self.repo / R.VALIDATOR).write_text(
            "import sys\nsys.exit(%d)\n" % (0 if validator == "ok" else 7), encoding="utf-8")
        (self.repo / R.RUNNER_REL).write_text("# committed runner placeholder\n", encoding="utf-8")

        sh(["git", "-C", str(self.repo), "add", "-A"])
        sh(["git", "-C", str(self.repo), "commit", "--quiet", "-m", "init"])
        sh(["git", "-C", str(self.repo), "remote", "add", "origin", str(self.remote)])
        sh(["git", "-C", str(self.repo), "push", "--quiet", "-u", "origin", R.EXPECTED_BRANCH])
        self.head = sh(["git", "-C", str(self.repo), "rev-parse", "HEAD"]).stdout.strip()

        # isolate all external state into the temp dir
        self._saved = (R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR)
        R.STATE_DIR = self.tmp / "state"
        R.LOG_DIR = R.STATE_DIR / "logs"
        R.LOCK_DIR = R.STATE_DIR / "locks"
        R.ATTEMPT_DIR = R.STATE_DIR / "attempts"

    def call(self, now=IN_WINDOW, mode="run", sha=None, task=GOOD_TASK, skip_task=False):
        argv = ["--repo-root", str(self.repo), "--mode", mode, "--now-override", now]
        if sha:
            argv += ["--expected-sha", sha]
        if skip_task:
            argv += ["--skip-task-check"]
        real = R._query_task_action
        R._query_task_action = (lambda: task)
        try:
            return R.main(argv)
        finally:
            R._query_task_action = real

    def log_text(self) -> str:
        logs = sorted(R.LOG_DIR.glob("phase2_unattended_*.log")) if R.LOG_DIR.is_dir() else []
        return logs[-1].read_text(encoding="utf-8", errors="replace") if logs else ""

    def close(self):
        R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)


# --- 1. isolation -----------------------------------------------------------

print("\n=== 1. network isolation ===")
for lbl, fn in (("connect", lambda: socket.create_connection(("example.org", 443), timeout=1)),
                ("DNS", lambda: socket.getaddrinfo("example.org", 443))):
    try:
        fn(); check(f"1. outbound {lbl} refused", False, "not blocked")
    except NetworkBlocked:
        check(f"1. outbound {lbl} refused", True)
    except Exception as e:                                          # noqa: BLE001
        check(f"1. outbound {lbl} refused", False, type(e).__name__)

# --- 2. successful preflight ------------------------------------------------

print("\n=== 2. successful preflight ===")
f = Fixture()
try:
    rc = f.call(mode="preflight", sha=f.head)
    check("2a. preflight in-window returns 0", rc == R.EXIT_OK, str(rc))
    t = f.log_text()
    check("2b. external log written before collection", "START mode=preflight" in t)
    check("2c. log records direct-python transport", "transport=direct-python" in t)
    check("2d. preflight states nothing was launched or staged",
          "panel not launched, nothing staged" in t)
    check("2e. no commit was created",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
finally:
    f.close()

# --- 3. window gate ---------------------------------------------------------

print("\n=== 3. local-time window ===")
for lbl, when in (("too early 02:04", TOO_EARLY), ("too late 02:26", TOO_LATE),
                  ("backfill 09:30", BACKFILL)):
    f = Fixture()
    try:
        rc = f.call(now=when, mode="preflight", sha=f.head)
        check(f"3. {lbl} refuses with EXIT_WINDOW", rc == R.EXIT_WINDOW, str(rc))
    finally:
        f.close()
f = Fixture()
try:
    f.call(now=BACKFILL, mode="preflight", sha=f.head)
    check("3d. late refusal says a missed cycle is never backfilled",
          "never backfilled" in f.log_text())
finally:
    f.close()

# --- 4. scheduled-task registration self-check ------------------------------

print("\n=== 4. task registration self-check ===")
f = Fixture()
try:
    check("4a. absent registration refuses with EXIT_TASK",
          f.call(mode="preflight", sha=f.head, task=None) == R.EXIT_TASK)
finally:
    f.close()
f = Fixture()
try:
    rc = f.call(mode="preflight", sha=f.head, task=PS_TASK)
    check("4b. PowerShell action refuses with EXIT_TASK", rc == R.EXIT_TASK, str(rc))
    check("4c. refusal names the shell wrapper", "shell or wrapper" in f.log_text())
finally:
    f.close()
f = Fixture()
try:
    bad = ("C:\\Python\\python.exe", '"C:\\repo\\tools\\something_else.py"')
    check("4d. action not invoking this runner refuses",
          f.call(mode="preflight", sha=f.head, task=bad) == R.EXIT_TASK)
finally:
    f.close()

# --- 5. repo / branch / HEAD / worktree -------------------------------------

print("\n=== 5. repository state gates ===")
f = Fixture()
try:
    (f.repo / "dirty.txt").write_text("x", encoding="utf-8")
    check("5a. dirty worktree refuses", f.call(mode="preflight", sha=f.head) == R.EXIT_ENV)
    check("5b. refusal names the unclean worktree", "not clean" in f.log_text())
finally:
    f.close()
f = Fixture()
try:
    sh(["git", "-C", str(f.repo), "checkout", "--quiet", "-b", "wrong-branch"])
    check("5c. wrong branch refuses", f.call(mode="preflight", sha=f.head) == R.EXIT_ENV)
finally:
    f.close()
f = Fixture()
try:
    rc = f.call(mode="preflight", sha="0" * 40)
    check("5d. HEAD != pinned expected SHA refuses", rc == R.EXIT_ENV, str(rc))
    check("5e. refusal names the pin mismatch", "pinned expected" in f.log_text())
finally:
    f.close()
f = Fixture()
try:
    nested = f.repo / "tools"
    argv = ["--repo-root", str(nested), "--mode", "preflight", "--now-override", IN_WINDOW,
            "--skip-task-check"]
    check("5f. nested subdirectory is not accepted as toplevel", R.main(argv) == R.EXIT_ENV)
finally:
    f.close()

# --- 6. one attempt per date ------------------------------------------------

print("\n=== 6. one attempt per eligible date ===")
f = Fixture()
try:
    R.ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
    R.attempt_path(RUN_DATE).write_text(json.dumps({"outcome": "success"}), encoding="utf-8")
    check("6a. a recorded SUCCESS blocks another attempt",
          f.call(mode="preflight", sha=f.head) == R.EXIT_DUPLICATE)
finally:
    f.close()
f = Fixture()
try:
    R.ATTEMPT_DIR.mkdir(parents=True, exist_ok=True)
    R.attempt_path(RUN_DATE).write_text(json.dumps({"outcome": "failure"}), encoding="utf-8")
    rc = f.call(mode="preflight", sha=f.head)
    check("6b. a recorded FAILURE also blocks another attempt", rc == R.EXIT_DUPLICATE, str(rc))
    check("6c. refusal states a failure blocks retry too", "a failure blocks retry too" in f.log_text())
finally:
    f.close()

# --- 7. lock contention -----------------------------------------------------

print("\n=== 7. lock contention ===")
f = Fixture()
try:
    R.LOCK_DIR.mkdir(parents=True, exist_ok=True)
    (R.LOCK_DIR / "phase2_daily_panel.lock").write_text("held", encoding="utf-8")
    rc = f.call(sha=f.head)
    check("7a. held lock refuses with EXIT_LOCK", rc == R.EXIT_LOCK, str(rc))
    check("7b. no commit was created while locked",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
finally:
    f.close()

# --- 8. panel and validator failures ---------------------------------------

print("\n=== 8. panel / validator failures ===")
f = Fixture(panel="noout")
try:
    rc = f.call(sha=f.head)
    check("8a. missing output refuses with EXIT_MISSING", rc == R.EXIT_MISSING, str(rc))
    check("8b. a failure is recorded for the date", R.attempt_path(RUN_DATE).is_file())
    check("8c. nothing was committed",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
finally:
    f.close()
f = Fixture(panel="fail")
try:
    check("8d. panel non-zero exit with no output refuses",
          f.call(sha=f.head) in (R.EXIT_MISSING, R.EXIT_TIMEOUT))
finally:
    f.close()
f = Fixture(validator="fail")
try:
    rc = f.call(sha=f.head)
    check("8e. validator failure refuses with EXIT_SCHEMA", rc == R.EXIT_SCHEMA, str(rc))
    check("8f. nothing was committed after validator failure",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
finally:
    f.close()

# --- 9. staging allowlist ---------------------------------------------------

print("\n=== 9. staging allowlist ===")
f = Fixture(panel="extra")
try:
    rc = f.call(sha=f.head)
    check("9a. an unexpected changed path refuses with EXIT_STAGING", rc == R.EXIT_STAGING, str(rc))
    check("9b. refusal names the stray path", "STRAY_ARTIFACT.txt" in f.log_text())
    check("9c. nothing was committed",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
finally:
    f.close()

# --- 10. success path, then push failure preserving the local commit --------

print("\n=== 10. success and push failure ===")
f = Fixture()
try:
    rc = f.call(sha=f.head)
    new = sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip()
    check("10a. clean run returns 0", rc == R.EXIT_OK, str(rc))
    check("10b. a machine commit was created", new != f.head)
    files = [x for x in sh(["git", "-C", str(f.repo), "show", "--name-only",
                            "--pretty=format:", new]).stdout.splitlines() if x.strip()]
    check("10c. exactly the two allowlisted files are in the commit",
          sorted(files) == sorted([CSV_REL, MARK_REL]), str(files))
    check("10d. success is recorded for the date",
          json.loads(R.attempt_path(RUN_DATE).read_text())["outcome"] == "success")
finally:
    f.close()

f = Fixture()
try:
    # Break the remote by URL rather than deleting it: git object files are
    # read-only on Windows and rmtree cannot remove them.
    sh(["git", "-C", str(f.repo), "remote", "set-url", "origin",
        str(f.tmp / "no_such_remote.git")])
    rc = f.call(sha=f.head)
    new = sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip()
    check("10e. push failure returns EXIT_PUSH", rc == R.EXIT_PUSH, str(rc))
    check("10f. the local commit is PRESERVED", new != f.head)
    check("10g. log says collection is not repeated", "NOT repeated" in f.log_text())
    rec = json.loads(R.attempt_path(RUN_DATE).read_text())
    check("10h. the date is recorded so no second attempt can occur",
          rec["outcome"] == "collected_commit_local_push_failed")
finally:
    f.close()

# --- 11. commit failure -----------------------------------------------------

print("\n=== 11. commit failure ===")
f = Fixture()
try:
    for k in ("user.email", "user.name"):
        sh(["git", "-C", str(f.repo), "config", "--unset", k])
    sh(["git", "-C", str(f.repo), "config", "--local", "user.useConfigOnly", "true"])
    env_backup = {k: os.environ.pop(k, None) for k in
                  ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME",
                   "GIT_COMMITTER_EMAIL", "EMAIL")}
    try:
        rc = f.call(sha=f.head)
        check("11a. commit failure returns EXIT_COMMIT (or is otherwise refused)",
              rc in (R.EXIT_COMMIT, R.EXIT_STAGING), str(rc))
        check("11b. a failure is recorded for the date", R.attempt_path(RUN_DATE).is_file())
    finally:
        for k, v in env_backup.items():
            if v is not None:
                os.environ[k] = v
finally:
    f.close()

# --- 12. prohibited PowerShell and destructive git ------------------------
# Moved to test_phase2_runner_static_guards.py, which inspects the runner's
# AST rather than its text: the runner legitimately contains the strings it
# forbids, in its docstring and in FORBIDDEN_IN_ACTION.

# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for x in _failures:
        print(f"  - {x}")
    sys.exit(1)
print("ALL DIRECT-PYTHON RUNNER CHECKS PASSED")
