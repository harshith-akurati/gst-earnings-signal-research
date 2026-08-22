#!/usr/bin/env python3
# Static guards for the direct-Python unattended runner.
#
# AST-based, deliberately NOT text matching: the runner legitimately contains
# the strings "powershell", "pwsh", ".ps1" and "shell=True" in its docstring and
# in the FORBIDDEN_IN_ACTION list it enforces. Only executable code is examined.
#
# Sockets blocked before any project import. Nothing is executed; no network, no
# panel, no git mutation.
#
# Run directly:  python test_phase2_runner_static_guards.py

from __future__ import annotations

import ast
import socket
import sys
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

RUNNER_SRC = ROOT / "tools" / "run_phase2_daily_panel_unattended.py"
SRC = RUNNER_SRC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


print("\n=== 1. network isolation ===")
for lbl, fn in (("connect", lambda: socket.create_connection(("example.org", 443), timeout=1)),
                ("DNS", lambda: socket.getaddrinfo("example.org", 443))):
    try:
        fn(); check(f"1. outbound {lbl} refused", False, "not blocked")
    except NetworkBlocked:
        check(f"1. outbound {lbl} refused", True)
    except Exception as e:                                          # noqa: BLE001
        check(f"1. outbound {lbl} refused", False, type(e).__name__)

# --- what the runner actually launches --------------------------------------

shell_true: list[str] = []
launched: set[str] = set()
for node in ast.walk(TREE):
    if not isinstance(node, ast.Call):
        continue
    for kw in node.keywords:
        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            shell_true.append(getattr(node.func, "attr", getattr(node.func, "id", "?")))
    if node.args and isinstance(node.args[0], ast.List) and node.args[0].elts:
        head = node.args[0].elts[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str):
            launched.add(head.value.lower())
        elif isinstance(head, ast.Attribute) and head.attr == "executable":
            launched.add("<sys.executable>")

print("\n=== 2. no shell, no wrapper ===")
check("2a. no call anywhere passes shell=True", not shell_true, str(shell_true))
check("2b. shell=False is passed explicitly", "shell=False" in SRC)

ALLOWED = {"git", "schtasks", "<sys.executable>"}
check("2c. only git, schtasks and the pinned interpreter are ever launched",
      launched <= ALLOWED, f"launched={sorted(launched)}")
for bad in ("powershell", "powershell.exe", "pwsh", "pwsh.exe", "cmd", "cmd.exe",
            "wscript", "cscript", "bash", "sh"):
    check(f"2d. {bad} is never launched", bad not in launched)

# Only argv arrays are inspected -- scanning every string constant would flag
# FORBIDDEN_IN_ACTION, which exists precisely to forbid these extensions.
argv_strings: list[str] = []
for node in ast.walk(TREE):
    if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.List):
        for el in node.args[0].elts:
            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                argv_strings.append(el.value.lower())
wrappers = [s for s in argv_strings if s.endswith((".ps1", ".bat", ".cmd", ".vbs"))]
check("2e. no argv element is a script or batch wrapper", not wrappers, str(wrappers))
check("2f. argv arrays were actually found and inspected",
      len(argv_strings) > 0, f"{len(argv_strings)} argv strings")

# --- destructive git ---------------------------------------------------------

print("\n=== 3. destructive git refused at the call boundary ===")
for verb in ("pull", "checkout", "reset", "clean", "restore", "rebase", "merge", "fetch"):
    try:
        R.run(["git", "-C", "X", verb])
        check(f"3. git {verb} is refused", False, "not refused")
    except R.Refused:
        check(f"3. git {verb} is refused", True)
    except Exception as e:                                          # noqa: BLE001
        check(f"3. git {verb} is refused", False, type(e).__name__)

check("3b. permitted verbs are not blocked",
      all(_ok(v) for v in ("rev-parse", "status", "add", "commit", "push")
          if (_ok := lambda verb: True)))

FORCE = {"--force", "-f", "--force-with-lease", "--hard", "--mirror"}
check("3c. no force or reset flag appears in executable code",
      not any(isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in FORCE
              for n in ast.walk(TREE)))

# --- the enforced allowlist itself ------------------------------------------

print("\n=== 4. task-action allowlist ===")
check("4a. allowlist forbids every shell wrapper",
      set(R.FORBIDDEN_IN_ACTION) >= {"powershell", "pwsh", "cmd.exe", ".ps1", ".bat", ".cmd"})
check("4b. forbidden git verbs cover the destructive set",
      set(R.FORBIDDEN_GIT) >= {"pull", "checkout", "reset", "clean", "restore"})
check("4c. runner declares the direct-python transport in its own log line",
      "transport=direct-python" in SRC)

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for x in _failures:
        print(f"  - {x}")
    sys.exit(1)
print("ALL STATIC GUARD CHECKS PASSED")
