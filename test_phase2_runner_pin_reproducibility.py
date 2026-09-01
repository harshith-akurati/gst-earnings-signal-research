#!/usr/bin/env python3
# Offline static/regression guard: the unattended runner's SHA-256 pin must be
# reproducible from what is committed, on every machine and every clone.
#
# WHY
# ---
# The scheduled task pins the runner by content hash (--runner-sha256), and
# check_code_integrity() hashes the file AS IT EXISTS ON DISK. This repository
# runs with core.autocrlf=true. Without an attribute for this path, git stores
# the runner with LF and writes it to the working tree with CRLF, so the on-disk
# hash depends on how the file happened to land rather than on what is
# committed:
#
#   stored blob (LF)   be5afc86...
#   CRLF checkout      c27ebf5d...
#
# The live worktree currently holds the LF form only because that file has never
# been re-materialised by a checkout. A fresh clone would produce the CRLF form
# and the registered pin would stop matching, refusing the next cycle with
# EXIT_INTEGRITY(14) -- a silent outage caused by nothing but a line ending.
#
# .gitattributes now carries an exact-path rule:
#
#   tools/run_phase2_daily_panel_unattended.py    text eol=lf
#
# These tests prove that rule actually does the job, and -- via a deliberate
# control case -- that the test would fail if the rule were removed.
#
# No network (sockets blocked before any import), no provider, no financial
# data, no panel run, no real panel/registry/outcome file opened. Git is
# invoked only against a local clone in a temporary directory; every clone is a
# --local file copy, never a fetch.
#
# Run directly:  python test_phase2_runner_pin_reproducibility.py

from __future__ import annotations

import hashlib
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

# --- network blocked BEFORE anything else -----------------------------------


class NetworkBlocked(RuntimeError):
    pass


def _no_net(*a, **k):
    raise NetworkBlocked("network access attempted")


socket.socket.connect = _no_net
socket.socket.connect_ex = _no_net
socket.create_connection = _no_net
socket.getaddrinfo = _no_net

# --- file-access audit ------------------------------------------------------

_OPENED: list[str] = []


def _audit(event: str, args) -> None:
    if event == "open" and args and isinstance(args[0], (str, bytes)):
        try:
            _OPENED.append(str(args[0]))
        except Exception:                                          # noqa: BLE001
            pass


sys.addaudithook(_audit)

ROOT = Path(__file__).resolve().parent
RUNNER_REL = "tools/run_phase2_daily_panel_unattended.py"

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


def git_text(*args: str, cwd: Path | None = None) -> str:
    r = subprocess.run(["git", *args], cwd=str(cwd or ROOT), capture_output=True,
                       text=True, shell=False)
    return r.stdout


def git_bytes(*args: str, cwd: Path | None = None) -> bytes:
    """Binary git output -- never text mode, so nothing is translated."""
    r = subprocess.run(["git", *args], cwd=str(cwd or ROOT), capture_output=True,
                       shell=False)
    return r.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def force_rmtree(path: Path) -> None:
    """Windows leaves git object files read-only, so a plain rmtree cannot
    remove a clone. Chmod each offender and retry."""
    def _fix(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:                                          # noqa: BLE001
            pass

    for _ in range(3):
        if not path.exists():
            return
        try:
            shutil.rmtree(path, onexc=_fix)
        except TypeError:                       # Python < 3.12 has no onexc
            shutil.rmtree(path, onerror=_fix)
        except Exception:                                          # noqa: BLE001
            pass


# --- 1. the attribute rule is declared for the exact path -------------------

print("=== 1. .gitattributes declares the rule for the exact runner path ===")

attrs = git_text("check-attr", "text", "eol", "--", RUNNER_REL)
check("1a. git check-attr reports text: set", f"{RUNNER_REL}: text: set" in attrs, attrs.strip())
check("1b. git check-attr reports eol: lf", f"{RUNNER_REL}: eol: lf" in attrs, attrs.strip())

ga = (ROOT / ".gitattributes").read_text(encoding="utf-8")
rule_lines = [ln for ln in ga.splitlines()
              if ln.strip() and not ln.lstrip().startswith("#") and RUNNER_REL in ln]
check("1c. the rule is written as an exact path, not a broad glob",
      len(rule_lines) == 1, str(rule_lines))
if rule_lines:
    rule = rule_lines[0]
    check("1d. the rule declares 'text'", re.search(r"(^|\s)text(\s|$)", rule) is not None, rule)
    check("1e. the rule declares 'eol=lf'", "eol=lf" in rule, rule)

# The change must stay narrow: no repository-wide line-ending rule.
broad = [ln for ln in ga.splitlines()
         if ln.strip() and not ln.lstrip().startswith("#")
         and ln.split()[0] in ("*", "**", "*.py", "**/*.py")]
check("1f. no repository-wide line-ending rule was introduced", not broad, str(broad))

# --- 2. in THIS worktree, on-disk bytes already equal the committed blob ----

print("\n=== 2. this worktree: on-disk == committed blob ===")

blob = git_bytes("cat-file", "blob", f"HEAD:{RUNNER_REL}")
blob_sha = sha256_bytes(blob)
disk_sha = sha256_file(ROOT / RUNNER_REL)

check("2a. the committed blob is non-empty", len(blob) > 0, str(len(blob)))
check("2b. on-disk SHA-256 equals the committed blob's SHA-256",
      disk_sha == blob_sha, f"disk={disk_sha[:16]} blob={blob_sha[:16]}")
check("2c. the working copy contains no CR bytes", b"\r" not in (ROOT / RUNNER_REL).read_bytes())
print(f"      committed blob SHA-256 : {blob_sha}")
print(f"      on-disk       SHA-256 : {disk_sha}")

# --- 3. a fresh clone with core.autocrlf=true reproduces the same bytes -----

print("\n=== 3. fresh clone under core.autocrlf=true ===")

head = git_text("rev-parse", "HEAD").strip()
branch = git_text("rev-parse", "--abbrev-ref", "HEAD").strip()
tmp = Path(tempfile.mkdtemp())
try:
    # A --local clone is a file copy, never a fetch. core.autocrlf=true is set
    # for the clone itself, so the checkout runs under the hazardous setting.
    clone = tmp / "fresh"
    subprocess.run(["git", "-c", "core.autocrlf=true", "clone", "--quiet", "--local",
                    "--no-hardlinks", "--branch", branch, "--single-branch",
                    str(ROOT), str(clone)],
                   capture_output=True, shell=False)
    check("3a. a fresh local clone was created", (clone / ".git").exists())
    check("3a2. the clone really has core.autocrlf=true",
          git_text("config", "core.autocrlf", cwd=clone).strip() == "true")
    check("3a3. the clone is at the same commit",
          git_text("rev-parse", "HEAD", cwd=clone).strip() == head)

    fresh = clone / RUNNER_REL
    check("3b. the runner exists in the fresh checkout", fresh.is_file())

    if fresh.is_file():
        fresh_bytes = fresh.read_bytes()
        check("3c. fresh-checkout bytes are byte-identical to the committed blob",
              fresh_bytes == blob,
              f"len {len(fresh_bytes)} vs {len(blob)}")
        check("3d. fresh-checkout SHA-256 equals the committed blob's SHA-256",
              sha256_bytes(fresh_bytes) == blob_sha,
              f"fresh={sha256_bytes(fresh_bytes)[:16]} blob={blob_sha[:16]}")
        check("3e. no CR byte survived the autocrlf=true checkout",
              b"\r" not in fresh_bytes)
        print(f"      fresh-checkout SHA-256 : {sha256_bytes(fresh_bytes)}")

        # The clone must also carry the attribute, i.e. the rule is committed.
        cattrs = git_text("check-attr", "text", "eol", "--", RUNNER_REL, cwd=clone)
        check("3f. the committed .gitattributes carries the rule into the clone",
              "text: set" in cattrs and "eol: lf" in cattrs, cattrs.strip())

    # --- 4. no line-ending configuration can change the pin -----------------

    print("\n=== 4. line-ending configuration cannot silently change the pin ===")

    matrix = [("true", None), ("false", None), ("input", None),
              ("true", "crlf"), ("false", "crlf"), ("input", "crlf"),
              ("true", "lf"), ("false", "lf"), ("input", "lf")]
    seen: dict[str, str] = {}
    for autocrlf, eol in matrix:
        target = clone / RUNNER_REL
        try:
            os.remove(target)
        except OSError:
            pass
        cfg = ["-c", f"core.autocrlf={autocrlf}"]
        if eol:
            cfg += ["-c", f"core.eol={eol}"]
        subprocess.run(["git", "-C", str(clone), *cfg, "checkout", "--", RUNNER_REL],
                       capture_output=True, shell=False)
        label = f"autocrlf={autocrlf} eol={eol or 'unset'}"
        if not target.is_file():
            check(f"4. {label}: file re-materialised", False, "missing after checkout")
            continue
        got = sha256_file(target)
        seen[label] = got
        check(f"4. {label} -> pin unchanged", got == blob_sha,
              f"{got[:16]} != {blob_sha[:16]}")

    check("4z. every configuration produced exactly one hash",
          len(set(seen.values())) == 1, str(sorted(set(seen.values()))))

    # --- 5. control: without the rule, the hash WOULD change ---------------
    #
    # This proves the guard is not vacuous. A synthetic repo holding the same
    # committed bytes at the same path, but WITHOUT the attribute rule, must
    # produce a different on-disk hash under core.autocrlf=true.

    print("\n=== 5. control -- the rule is doing real work ===")

    ctl = tmp / "control"
    (ctl / "tools").mkdir(parents=True)
    (ctl / RUNNER_REL).write_bytes(blob)
    (ctl / ".gitattributes").write_bytes(b"# deliberately no rule for the runner\n")
    for args in (["init", "--quiet", "-b", "ctl"],
                 ["config", "user.email", "t@example.invalid"],
                 ["config", "user.name", "T"],
                 ["config", "commit.gpgsign", "false"],
                 ["config", "core.autocrlf", "true"],
                 ["add", "-A"],
                 ["commit", "--quiet", "-m", "control"]):
        subprocess.run(["git", "-C", str(ctl), *args], capture_output=True, shell=False)

    ctl_blob = git_bytes("cat-file", "blob", "HEAD:" + RUNNER_REL, cwd=ctl)
    check("5a. the control repo stores the same normalised blob",
          sha256_bytes(ctl_blob) == blob_sha,
          f"{sha256_bytes(ctl_blob)[:16]} vs {blob_sha[:16]}")

    ctl_out = tmp / "control_fresh"
    subprocess.run(["git", "-c", "core.autocrlf=true", "clone", "--quiet", "--local",
                    "--no-hardlinks", str(ctl), str(ctl_out)],
                   capture_output=True, shell=False)
    ctl_file = ctl_out / RUNNER_REL
    if ctl_file.is_file():
        ctl_sha = sha256_file(ctl_file)
        check("5b. WITHOUT the rule, a fresh autocrlf=true checkout differs from the blob",
              ctl_sha != blob_sha,
              "hashes matched, so this platform does not reproduce the hazard")
        check("5c. and the difference is exactly CRLF translation",
              ctl_file.read_bytes().replace(b"\r\n", b"\n") == blob)
        print(f"      unguarded checkout SHA-256 : {ctl_sha}")
    else:
        check("5b. control checkout produced the runner file", False, "missing")
finally:
    force_rmtree(tmp)

# --- 6. isolation -----------------------------------------------------------

print("\n=== 6. isolation ===")

_REAL_ARTIFACT = re.compile(
    r"(GST_Phase2_DailyPanel_TestRun_\d{4}-\d{2}-\d{2}|_COMPLETION_MARKER\.json"
    r"|_CHECKPOINT_PARTIAL\.csv|registry\.jsonl|_OPERATIONS_PLAN\.json"
    r"|MARKET_RESPONSE|locked_universe|EFFECTIVE_LOCK_REPORT)", re.I)

tmp_root = str(Path(tempfile.gettempdir()).resolve()).lower()
suspicious = [p for p in _OPENED
              if _REAL_ARTIFACT.search(p)
              and not str(Path(p).resolve()).lower().startswith(tmp_root)]
check("6a. no real panel/registry/market-response/outcome file was opened",
      not suspicious, str(suspicious[:5]))

net_ok = False
try:
    socket.create_connection(("example.invalid", 80))
except NetworkBlocked:
    net_ok = True
except Exception:                                                  # noqa: BLE001
    net_ok = False
check("6b. sockets are still blocked at the end of the run", net_ok)
check("6c. the temporary clone directory was removed", not Path(tmp).exists(),
      f"left behind: {tmp}")

# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for name in _failures:
        print(f"  - {name}")
    sys.exit(1)
print("ALL RUNNER PIN REPRODUCIBILITY CHECKS PASSED")
