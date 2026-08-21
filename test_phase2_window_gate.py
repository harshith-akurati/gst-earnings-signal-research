#!/usr/bin/env python3
# Deterministic tests for the unattended panel's local-time execution gate.
#
# No network, no provider, no financial data retrieval, no outcome access and
# no panel run. Sockets are blocked BEFORE any project module is imported, the
# same discipline the rest of this repository's test files use. Every clock is
# injected; the host clock is never consulted for a pass/fail assertion.
#
# Run directly:  python test_phase2_window_gate.py

from __future__ import annotations

import datetime as dt
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

# --- blockers installed BEFORE importing any project module ----------------


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
from phase2_window_gate import (                                    # noqa: E402
    EXIT_OK, EXIT_OUTSIDE_WINDOW, ZONE, evaluate,
)

CT = ZoneInfo(ZONE)
_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


def at(h: int, m: int, s: int = 0, day: int = 22, month: int = 8, year: int = 2026):
    """An instant on a CDT day, expressed in America/Chicago."""
    return dt.datetime(year, month, day, h, m, s, tzinfo=CT)


def code(h: int, m: int, s: int = 0, **kw) -> int:
    return evaluate(at(h, m, s, **kw))["exit_code"]


# --- 1. network isolation ---------------------------------------------------

print("\n=== 1. network isolation ===")
for label, fn in (("outbound connection", lambda: socket.create_connection(("example.org", 443), timeout=1)),
                  ("DNS resolution", lambda: socket.getaddrinfo("example.org", 443))):
    try:
        fn()
        check(f"1. {label} is refused", False, "was NOT blocked")
    except NetworkBlocked:
        check(f"1. {label} is refused", True)
    except Exception as e:                                          # noqa: BLE001
        check(f"1. {label} is refused", False, f"unexpected {type(e).__name__}")

# --- 2. the four required clock cases ---------------------------------------

print("\n=== 2. required clock cases ===")
check("2a. 02:15 (scheduled) passes", code(2, 15) == EXIT_OK, str(code(2, 15)))
check("2b. 02:04 refuses", code(2, 4) == EXIT_OUTSIDE_WINDOW, str(code(2, 4)))
check("2c. 02:26 refuses", code(2, 26) == EXIT_OUTSIDE_WINDOW, str(code(2, 26)))

r_early, r_late = evaluate(at(2, 4)), evaluate(at(2, 26))
check("2d. the 02:04 refusal is attributed to being early", "too early" in r_early["reason"])
check("2e. the 02:26 refusal is attributed to being late", "too late" in r_late["reason"])

# --- 3. window boundaries are inclusive as specified ------------------------

print("\n=== 3. boundaries ===")
check("3a. 02:05:00 open boundary is permitted", code(2, 5) == EXIT_OK)
check("3b. 02:25:00 close boundary is permitted", code(2, 25) == EXIT_OK)
check("3c. 02:04:59 is refused", code(2, 4, 59) == EXIT_OUTSIDE_WINDOW)
check("3d. 02:25:01 is refused", code(2, 25, 1) == EXIT_OUTSIDE_WINDOW)

# --- 4. a missed task cannot backfill later ---------------------------------

print("\n=== 4. a missed cycle cannot backfill ===")
backfill = [(3, 15, "one hour late"), (6, 0, "morning"), (9, 30, "mid-morning"),
            (14, 45, "afternoon"), (23, 59, "end of the same day")]
for h, m, why in backfill:
    check(f"4. a firing at {h:02d}:{m:02d} ({why}) is refused",
          code(h, m) == EXIT_OUTSIDE_WINDOW, str(code(h, m)))
check("4f. a next-day firing still only passes inside its own window",
      code(2, 15, day=23) == EXIT_OK and code(9, 0, day=23) == EXIT_OUTSIDE_WINDOW)
check("4g. the late refusal states that a missed cycle is skipped, not backfilled",
      "never backfilled" in evaluate(at(9, 30))["reason"])

# --- 5. zone correctness, not host-clock coincidence ------------------------

print("\n=== 5. zone handling ===")
# 07:15 UTC is 02:15 CDT in August. The gate must convert, not compare naively.
utc_in = dt.datetime(2026, 8, 22, 7, 15, tzinfo=dt.timezone.utc)
check("5a. 07:15Z in August resolves to 02:15 CDT and passes",
      evaluate(utc_in)["exit_code"] == EXIT_OK, evaluate(utc_in)["now_local"])
utc_out = dt.datetime(2026, 8, 22, 14, 15, tzinfo=dt.timezone.utc)
check("5b. 14:15Z (09:15 CDT) refuses", evaluate(utc_out)["exit_code"] == EXIT_OUTSIDE_WINDOW)
# A January instant is CST (-06:00): 08:15Z is 02:15 CST.
cst = dt.datetime(2027, 1, 15, 8, 15, tzinfo=dt.timezone.utc)
e = evaluate(cst)
check("5c. DST is handled: 08:15Z in January is 02:15 CST and passes",
      e["exit_code"] == EXIT_OK and e["tzname"] == "CST", f"{e['now_local']} {e['tzname']}")
check("5d. an injected clock is reported as overridden", evaluate(at(2, 15))["clock_overridden"])

# --- 6. fails closed on an unreadable clock ---------------------------------

print("\n=== 6. fail-closed behaviour ===")
p = subprocess.run([sys.executable, str(ROOT / "tools" / "phase2_window_gate.py"),
                    "--now", "not-a-timestamp"], capture_output=True, text=True)
check("6a. an unparseable --now refuses rather than defaulting open",
      p.returncode == EXIT_OUTSIDE_WINDOW, f"rc={p.returncode}")

# --- 7. a refusal produces an external log ----------------------------------

print("\n=== 7. refusal is recorded in an external log ===")
runner = ROOT / "tools" / "Invoke-Phase2DailyPanelUnattended.ps1"
logdir = Path(r"C:\Users\hakur\Downloads\gst-source-quarantine\scheduler\logs")
if not runner.is_file():
    check("7. runner present", False, str(runner))
else:
    before = set(logdir.glob("phase2_unattended_*.log")) if logdir.is_dir() else set()
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(runner), "-Mode", "Preflight", "-RepoRoot", str(ROOT),
         "-NowOverride", "2026-08-22T09:30:00"],
        capture_output=True, text=True)
    after = set(logdir.glob("phase2_unattended_*.log")) if logdir.is_dir() else set()
    new = sorted(after - before)

    check("7a. an out-of-window run exits 10", proc.returncode == EXIT_OUTSIDE_WINDOW,
          f"rc={proc.returncode}")
    check("7b. a new log file was written outside the repository", len(new) == 1,
          f"{len(new)} new files")
    if new:
        body = new[0].read_text(encoding="utf-8", errors="replace")
        check("7c. the log records the refusal", "GATE REFUSED" in body)
        check("7d. the log states nothing else was performed",
              "no network, git, staging, commit or push was performed" in body)
        check("7e. the log lies outside the repository working tree",
              ROOT not in new[0].parents, str(new[0]))
        check("7f. the refusal happened before repository resolution",
              "repo toplevel verified" not in body)
    # Nothing may have been staged in the repository by a refused run.
    st = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--name-only"],
                        capture_output=True, text=True)
    check("7g. a refused run staged nothing", st.stdout.strip() == "", st.stdout.strip()[:120])

# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL WINDOW GATE CHECKS PASSED")
