#!/usr/bin/env python3
# Offline regression tests for the Phase 2 collector observability correction
# (2026-09-01).
#
# These tests exist because two consecutive unattended failures were diagnosed
# only by inference, both times because the failure detail was captured and
# then dropped:
#
#   2026-08-29  iv_status='error' persisted on 24/24 tickers with iv_error
#               EMPTY, because run_bounded() recorded str(exc) and str() of an
#               argument-less exception is "".
#   2026-08-31  the panel raised inside pytrends' TrendReq() constructor and
#               exited 1 after 15s with no artifacts; the runner had captured
#               the child's stderr and discarded it on the refusal path.
#
# Sockets are blocked before any project import. Every fixture is synthetic and
# lives in a temporary directory. The real panel is never run, no provider is
# contacted, no real panel/registry/market-response/prospective-outcome file is
# opened, and no measurement value appears anywhere in this file -- the only
# numbers used are obvious synthetic sentinels asserted to be ABSENT from logs.
#
# Run directly:  python test_phase2_observability_diagnostics.py

from __future__ import annotations

import ast
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import types
from pathlib import Path

# --- network blocked BEFORE any project import ------------------------------


class NetworkBlocked(RuntimeError):
    pass


def _no_net(*a, **k):
    raise NetworkBlocked("network access attempted")


socket.socket.connect = _no_net
socket.socket.connect_ex = _no_net
socket.create_connection = _no_net
socket.getaddrinfo = _no_net

# --- file-access audit installed BEFORE any project import ------------------

_OPENED: list[str] = []


def _audit(event: str, args) -> None:
    if event == "open" and args and isinstance(args[0], (str, bytes)):
        try:
            _OPENED.append(str(args[0]))
        except Exception:                                          # noqa: BLE001
            pass


sys.addaudithook(_audit)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import GST_Phase2_SafeDiagnostics as D                             # noqa: E402
import run_phase2_daily_panel_unattended as R                      # noqa: E402
import GST_Phase2_DailyPanel as P                                  # noqa: E402

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    if ok:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}" + (f" -- {detail}" if detail else ""))
        _failures.append(label)


def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, shell=False)


# Synthetic sentinels. These are NOT measurements -- they are markers asserted
# to be absent from every runner log, proving panel stdout is never echoed.
SENT_IV = "SENTINEL_IV_VALUE_11111111"
SENT_PRICE = "SENTINEL_PRICE_VALUE_22222222"
SENT_Z = "SENTINEL_ZSCORE_VALUE_33333333"
SENT_VOL = "SENTINEL_VOLUME_VALUE_44444444"
ALL_SENTINELS = (SENT_IV, SENT_PRICE, SENT_Z, SENT_VOL)

# Synthetic secrets, likewise asserted to be absent once redacted.
SECRET_TOKEN = "abcd1234efgh5678ijkl"
SECRET_KEY = "SUPERSECRETAPIKEY99"
FAKE_USER = "victimuser"


# ============================================================ 1. the sanitizer

print("=== 1. centralized exception formatting ===")

# The exact 2026-08-29 defect, documented as an executable fact.
check("1a. str() of an argument-less exception is empty (the original defect)",
      str(ValueError()) == "")
check("1b. format_exception() of the same exception is NOT empty",
      D.format_exception(ValueError()) != "")
check("1c. and it names the exception class",
      "ValueError" in D.format_exception(ValueError()),
      D.format_exception(ValueError()))
check("1d. an absent message is stated explicitly, never left blank",
      D.NO_MESSAGE in D.format_exception(ValueError()))
check("1e. a real message is preserved",
      "chain unavailable" in D.format_exception(RuntimeError("chain unavailable")))
check("1f. format_exception(None) is still non-empty",
      D.format_exception(None) != "")


class _AngryStr(Exception):
    def __str__(self):
        raise RuntimeError("__str__ exploded")


check("1g. an exception whose __str__ raises still yields a non-empty reason",
      D.format_exception(_AngryStr()) != "" and "_AngryStr" in D.format_exception(_AngryStr()))

# --- redaction --------------------------------------------------------------

print("\n=== 2. redaction ===")

hdr = D.sanitize_text(f"401 from provider; Authorization: Bearer {SECRET_TOKEN}")
check("2a. Authorization header value is redacted", SECRET_TOKEN not in hdr, hdr)
check("2b. and the redaction marker is present", D.REDACTED in hdr, hdr)

bearer = D.sanitize_text(f"retrying with Bearer {SECRET_TOKEN} failed")
check("2c. a bare bearer token is redacted", SECRET_TOKEN not in bearer, bearer)

qs = D.sanitize_text(
    f"GET https://provider.invalid/v7/chain?symbol=ZZZ&api_key={SECRET_KEY}&range=1d failed")
check("2d. query-string api_key is redacted", SECRET_KEY not in qs, qs)
check("2e. non-secret query params survive for diagnosis", "symbol=ZZZ" in qs, qs)

js = D.sanitize_text(f'body={{"access_token": "{SECRET_TOKEN}", "status": "denied"}}')
check("2f. a JSON secret field is redacted", SECRET_TOKEN not in js, js)
check("2g. the surrounding JSON context survives", "denied" in js, js)

assign = D.sanitize_text(f"config password='{SECRET_TOKEN}' rejected")
check("2h. a quoted secret assignment is redacted", SECRET_TOKEN not in assign, assign)

winpath = D.sanitize_text(rf"File \"C:\Users\{FAKE_USER}\repo\GST_Phase2_DailyPanel.py\", line 9")
check("2i. a Windows user-profile path is redacted", FAKE_USER not in winpath, winpath)
check("2j. the home placeholder replaces it", D.HOME_PLACEHOLDER in winpath, winpath)
check("2k. the non-identifying remainder of the path survives",
      "GST_Phase2_DailyPanel.py" in winpath, winpath)

for label, raw in (("POSIX /home", f"/home/{FAKE_USER}/proj/x.py"),
                   ("macOS /Users", f"/Users/{FAKE_USER}/proj/x.py"),
                   ("MSYS /c/Users", f"/c/Users/{FAKE_USER}/proj/x.py"),
                   ("%USERPROFILE%", r"%USERPROFILE%\proj\x.py")):
    got = D.sanitize_text(raw)
    check(f"2l. {label} home directory is redacted",
          FAKE_USER not in got and D.HOME_PLACEHOLDER in got, got)

# --- bounds and shape -------------------------------------------------------

print("\n=== 3. bounds and tabular safety ===")

long_msg = D.format_exception(RuntimeError("A" * 5000))
check("3a. a persisted diagnostic is length-bounded",
      len(long_msg) <= D.MAX_ERROR_FIELD_LEN, str(len(long_msg)))
check("3b. truncation is marked, not silent", long_msg.endswith(D.TRUNCATION_MARKER))

multi = D.format_exception(RuntimeError("line one\nline two\r\nline three\tTabbed"))
check("3c. a persisted diagnostic is single-line (no LF)", "\n" not in multi, repr(multi))
check("3d. no CR survives", "\r" not in multi, repr(multi))
check("3e. no TAB survives", "\t" not in multi, repr(multi))
check("3f. the separated content is still readable",
      "line one" in multi and "line three" in multi, multi)

ctrl = D.sanitize_text("before\x00\x07after")
check("3g. control characters are stripped",
      "\x00" not in ctrl and "\x07" not in ctrl, repr(ctrl))

# --- stream formatting ------------------------------------------------------

print("\n=== 4. captured-stream formatting ===")

many = "\n".join(f"line{i}" for i in range(500))
blk = D.format_stream_for_log(many)
check("4a. a long stream is bounded by line count",
      len(blk.split("\n")) <= D.MAX_LOG_BLOCK_LINES + 1, str(len(blk.split("\n"))))
check("4b. the TAIL is kept (the traceback's exception line)", "line499" in blk)
check("4c. omission is disclosed", "omitted" in blk, blk.split("\n")[0])
check("4d. the block is char-bounded", len(blk) <= D.MAX_LOG_BLOCK_CHARS, str(len(blk)))
check("4e. line structure is preserved for a traceback", "\n" in blk)
check("4f. an empty stream yields an empty block", D.format_stream_for_log("") == "")
check("4g. a whitespace-only stream yields an empty block",
      D.format_stream_for_log("  \n\n \t ") == "")
check("4h. secrets inside a stream are redacted",
      SECRET_TOKEN not in D.format_stream_for_log(f"Authorization: Bearer {SECRET_TOKEN}"))


# ================================================ 5. per-source persistence

print("\n=== 5. per-source error persistence in the panel ===")


def _raise_empty():
    raise ValueError()                       # the exact 2026-08-29 shape


res, timed_out, elapsed, err = P.run_bounded(_raise_empty, 10)
check("5a. run_bounded reports the failure", res is None and not timed_out)
check("5b. run_bounded's error string is NOT empty (2026-08-29 regression)",
      bool(err), repr(err))
check("5c. and it names the exception class", "ValueError" in (err or ""), repr(err))

SIX = ("earnings", "price_history", "realized_vol", "iv", "gst", "wiki")
check("5d. every source leg is covered by the post-condition",
      set(SIX) == set(P.SOURCE_LEGS), str(P.SOURCE_LEGS))

# IV -- the 2026-08-29 shape: status set, reason blank.
row = {"iv_status": "error", "iv_error": "", "implied_volatility": None}
P.enforce_error_persistence(row)
check("5e. IV: a blank reason is replaced with a non-empty one",
      bool(row["iv_error"]), repr(row["iv_error"]))
check("5f. IV: status stays 'error'", row["iv_status"] == "error")
check("5g. IV: the reason is single-line (tabular-safe)",
      "\n" not in row["iv_error"] and "\r" not in row["iv_error"])
check("5h. IV: no value is imputed", row["implied_volatility"] is None)

# IV -- the same defect expressed as None rather than "".
row = {"iv_status": "error", "iv_error": None}
P.enforce_error_persistence(row)
check("5i. IV: a None reason is also replaced", bool(row["iv_error"]))

# Google Trends leg.
row = {"gst_status": "error", "gst_error": ""}
P.enforce_error_persistence(row)
check("5j. GST: a blank reason is replaced", bool(row["gst_error"]))

# A leg that never reported at all is a failed leg.
row = {"iv_status": None, "iv_error": None}
P.enforce_error_persistence(row)
check("5k. a leg with no status at all is recorded as error",
      row["iv_status"] == "error" and bool(row["iv_error"]))

# Every leg, all blank at once (the isolation-fallback row).
row = {f"{s}_status": None for s in SIX}
row.update({f"{s}_error": None for s in SIX})
P.enforce_error_persistence(row, fallback=D.format_exception(RuntimeError("ticker aborted")))
check("5l. all six legs receive status=error",
      all(row[f"{s}_status"] == "error" for s in SIX))
check("5m. all six legs receive a non-empty reason",
      all(row[f"{s}_error"] for s in SIX))
check("5n. the supplied fallback reason is used",
      all("ticker aborted" in row[f"{s}_error"] for s in SIX))

# An existing reason carrying a secret is sanitized, not passed through raw.
row = {"iv_status": "error",
       "iv_error": f"HTTP 401 Authorization: Bearer {SECRET_TOKEN} from C:\\Users\\{FAKE_USER}\\x"}
P.enforce_error_persistence(row)
check("5o. an existing reason is redacted, not persisted raw",
      SECRET_TOKEN not in row["iv_error"] and FAKE_USER not in row["iv_error"],
      row["iv_error"])
check("5p. and it stays informative", "401" in row["iv_error"], row["iv_error"])

# A timeout must also carry a reason.
row = {"iv_status": "timeout", "iv_error": ""}
P.enforce_error_persistence(row)
check("5q. a timeout leg also records a non-empty reason", bool(row["iv_error"]))
check("5r. a timeout keeps its own status, not rewritten to error",
      row["iv_status"] == "timeout")

# --- the success path must be untouched -------------------------------------

ok_row = {
    "iv_status": "ok", "iv_error": None, "implied_volatility": 0.5,
    "gst_status": "ok", "gst_error": None, "gst_zscore": 1.5, "gst_note": "n",
    "earnings_status": "ok", "price_history_status": "ok",
    "realized_vol_status": "ok", "wiki_status": "ok",
    "price": 1.0, "volume": 2, "realized_vol": 3.0, "wiki_zscore": 4.0,
    "all_six_fields_clean": True,
}
before = dict(ok_row)
P.enforce_error_persistence(ok_row)
check("5s. a fully successful row is left byte-identical", ok_row == before,
      str({k: (before.get(k), ok_row.get(k)) for k in ok_row if before.get(k) != ok_row.get(k)}))

# A mixed row: the ok legs stay untouched while only the failed one is written.
mixed = {"iv_status": "error", "iv_error": "", "implied_volatility": None,
         "gst_status": "ok", "gst_error": None, "gst_zscore": 1.25}
P.enforce_error_persistence(mixed)
check("5t. a successful leg in a mixed row is untouched",
      mixed["gst_status"] == "ok" and mixed["gst_error"] is None and mixed["gst_zscore"] == 1.25)
check("5u. no measurement field is created by the post-condition",
      "price" not in mixed and "volume" not in mixed and mixed["implied_volatility"] is None)
check("5v. the post-condition returns the same object (no copy semantics)",
      P.enforce_error_persistence(mixed) is mixed)


# ============================== 6. Trends client construction is retained

print("\n=== 6. Google Trends client-construction failure is retained ===")

panel_src = (ROOT / "GST_Phase2_DailyPanel.py").read_text(encoding="utf-8")
tree = ast.parse(panel_src)


def _calls_trendreq(node) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "TrendReq":
            return True
    return False


guard = None
for node in ast.walk(tree):
    if isinstance(node, ast.Try) and _calls_trendreq(ast.Module(body=node.body, type_ignores=[])):
        guard = node
        break

check("6a. the TrendReq() construction is wrapped in a try/except", guard is not None)
if guard is not None:
    handler_src = "\n".join(ast.dump(h) for h in guard.handlers)
    check("6b. the handler formats the exception through the sanitizer",
          "format_exception" in handler_src)
    check("6c. the handler logs it", "log" in handler_src)
    bare_reraise = any(isinstance(n, ast.Raise) and n.exc is None
                       for h in guard.handlers for n in ast.walk(h))
    check("6d. the handler RE-RAISES, so the run still fails closed", bare_reraise)
    swallowed = any(isinstance(n, ast.Return) for h in guard.handlers for n in ast.walk(h))
    check("6e. the handler does not swallow the failure or continue", not swallowed)

check("6f. run_bounded no longer persists a raw str(exc)",
      "result_box[\"error\"] = str(e)" not in panel_src)
check("6g. no source leg persists a raw str(exc)",
      not re.search(r'_error"\]\s*=\s*str\(e\)', panel_src))


# ================================================ 7. runner diagnostics (e2e)

print("\n=== 7. runner diagnostics, end to end ===")

IN_WINDOW = "2026-08-22T02:15:00"
RUN_DATE = "2026-08-22"
CSV_REL = f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{RUN_DATE}_run3.csv"
MARK_REL = f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{RUN_DATE}_run3_COMPLETION_MARKER.json"
GOOD_TASK = ("C:\\Python\\python.exe",
             '"C:\\repo\\tools\\run_phase2_daily_panel_unattended.py" --repo-root "C:\\repo"')

# A stub panel that behaves exactly like 2026-08-31: it prints measurement-like
# sentinels to STDOUT, raises with a secret-bearing traceback on STDERR, writes
# NO output file, and exits 1.
FAILING_PANEL = f'''import sys
print("[AAPL] DONE iv  status=ok  iv={SENT_IV}")
print("[AAPL] DONE price value={SENT_PRICE}")
print("[AAPL] DONE gst  z={SENT_Z}")
print("[AAPL] DONE volume v={SENT_VOL}")
sys.stderr.write("Traceback (most recent call last):\\n")
sys.stderr.write("  File \\"C:\\\\Users\\\\{FAKE_USER}\\\\repo\\\\GST_Phase2_DailyPanel.py\\", line 1361\\n")
sys.stderr.write("    pt = TrendReq(hl='en-US')\\n")
sys.stderr.write("  request headers: Authorization: Bearer {SECRET_TOKEN}\\n")
sys.stderr.write("  url https://trends.invalid/explore?api_key={SECRET_KEY}&geo=US\\n")
sys.stderr.write("requests.exceptions.ConnectionError: bootstrap refused\\n")
sys.exit(1)
'''

OK_PANEL = (f"from pathlib import Path\n"
            f"print('[AAPL] DONE iv value={SENT_IV}')\n"
            f"Path(r'{CSV_REL}').write_text('x', encoding='utf-8')\n"
            f"Path(r'{MARK_REL}').write_text('{{}}', encoding='utf-8')\n")

SILENT_PANEL = "import sys\nsys.exit(1)\n"


class Fixture:
    """Synthetic repo + isolated state. Never touches the real repository."""

    def __init__(self, panel_src: str):
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

        (self.repo / R.PANEL_SCRIPT).write_text(panel_src, encoding="utf-8")
        (self.repo / R.VALIDATOR).write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        (self.repo / R.RUNNER_REL).write_text("# committed runner placeholder\n", encoding="utf-8")

        sh(["git", "-C", str(self.repo), "add", "-A"])
        sh(["git", "-C", str(self.repo), "commit", "--quiet", "-m", "init"])
        sh(["git", "-C", str(self.repo), "remote", "add", "origin", str(self.remote)])
        sh(["git", "-C", str(self.repo), "push", "--quiet", "-u", "origin", R.EXPECTED_BRANCH])
        self.head = sh(["git", "-C", str(self.repo), "rev-parse", "HEAD"]).stdout.strip()

        self._saved = (R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR)
        R.STATE_DIR = self.tmp / "state"
        R.LOG_DIR = R.STATE_DIR / "logs"
        R.LOCK_DIR = R.STATE_DIR / "locks"
        R.ATTEMPT_DIR = R.STATE_DIR / "attempts"

    def call(self):
        argv = ["--repo-root", str(self.repo), "--mode", "run", "--now-override", IN_WINDOW]
        real = R._query_task_action
        R._query_task_action = (lambda: GOOD_TASK)
        try:
            return R.main(argv)
        finally:
            R._query_task_action = real

    def log_text(self) -> str:
        logs = sorted(R.LOG_DIR.glob("phase2_unattended_*.log")) if R.LOG_DIR.is_dir() else []
        return logs[-1].read_text(encoding="utf-8", errors="replace") if logs else ""

    def commit_count(self) -> int:
        out = sh(["git", "-C", str(self.repo), "rev-list", "--count", "HEAD"]).stdout.strip()
        return int(out or 0)

    def close(self):
        R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)


check("7pre. EXIT_MISSING is still 6", R.EXIT_MISSING == 6, str(R.EXIT_MISSING))

f = Fixture(FAILING_PANEL)
try:
    before_commits = f.commit_count()
    rc = f.call()
    log = f.log_text()

    check("7a. a panel that fails before producing output still returns EXIT_MISSING(6)",
          rc == R.EXIT_MISSING == 6, str(rc))
    check("7b. the pre-existing refusal message is unchanged",
          "required output missing (final CSV is written only on a clean 24/24)" in log)

    check("7c. a diagnostics section is written", "panel diagnostics:" in log, log[-400:])
    check("7d. the panel exit code is recorded", "exit=1" in log)
    check("7e. the sanitized stderr tail is present",
          "ConnectionError" in log and "bootstrap refused" in log)
    check("7f. the failing call site survives in the diagnostic", "TrendReq" in log)

    diag_lines = "\n".join(ln for ln in log.splitlines() if "  | " in ln)
    check("7g. diagnostics are emitted as marked, bounded lines", bool(diag_lines))

    # --- the redaction guarantees, on a real runner log ---
    check("7h. a bearer token in stderr never reaches the runner log",
          SECRET_TOKEN not in log)
    check("7i. a query-string api_key in stderr never reaches the runner log",
          SECRET_KEY not in log)
    check("7j. a user-profile path in stderr is redacted",
          FAKE_USER not in log)
    check("7k. the home placeholder appears instead", D.HOME_PLACEHOLDER in log)

    # --- the measurement guarantee ---
    leaked = [s for s in ALL_SENTINELS if s in log]
    check("7l. NO measurement sentinel from panel stdout appears in the runner log",
          not leaked, str(leaked))
    check("7m. stdout is accounted for but not echoed",
          "stdout_chars=" in log and "never echoed" in log)

    # --- fail-closed ---
    check("7n. no final CSV was created", not (f.repo / CSV_REL).exists())
    check("7o. no completion marker was created", not (f.repo / MARK_REL).exists())
    check("7p. nothing was committed after the failure",
          f.commit_count() == before_commits, f"{before_commits} -> {f.commit_count()}")
    check("7q. HEAD is unchanged",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip() == f.head)
    check("7r. the failure was recorded as an attempt (no silent retry)",
          (R.ATTEMPT_DIR / f"attempt_{RUN_DATE}.json").is_file())
    check("7s. no retry or fallback provider was attempted",
          log.count("launching panel") == 1, str(log.count("launching panel")))
finally:
    f.close()

# --- a panel that dies with no stderr at all --------------------------------

f = Fixture(SILENT_PANEL)
try:
    rc = f.call()
    log = f.log_text()
    check("7t. a silent nonzero exit still returns EXIT_MISSING(6)", rc == R.EXIT_MISSING)
    check("7u. an empty stderr is stated explicitly rather than left blank",
          "stderr was empty" in log, log[-300:])
finally:
    f.close()

# --- the success path is behaviorally unchanged -----------------------------

print("\n=== 8. the successful path is unchanged ===")

f = Fixture(OK_PANEL)
try:
    before_commits = f.commit_count()
    rc = f.call()
    log = f.log_text()
    check("8a. a clean run still returns EXIT_OK", rc == R.EXIT_OK, str(rc))
    check("8b. a clean run still commits exactly one new commit",
          f.commit_count() == before_commits + 1,
          f"{before_commits} -> {f.commit_count()}")
    check("8c. a clean run still pushes to the remote",
          sh(["git", "-C", str(f.repo), "rev-parse", "HEAD"]).stdout.strip()
          == sh(["git", "-C", str(f.repo), "rev-parse", "@{u}"]).stdout.strip())
    check("8d. the success log carries no diagnostics section",
          "panel diagnostics:" not in log)
    check("8e. the existing success line is unchanged", "DONE unattended cycle OK" in log)
    check("8f. even on success, panel stdout is not echoed into the runner log",
          SENT_IV not in log)
finally:
    f.close()


# ============================================== 9. file-access audit result

print("\n=== 9. file-access audit ===")

_REAL_ARTIFACT = re.compile(
    r"(GST_Phase2_DailyPanel_TestRun_\d{4}-\d{2}-\d{2}|_COMPLETION_MARKER\.json"
    r"|_CHECKPOINT_PARTIAL\.csv|registry\.jsonl|_OPERATIONS_PLAN\.json"
    r"|MARKET_RESPONSE|locked_universe|EFFECTIVE_LOCK_REPORT)", re.I)

tmp_root = str(Path(tempfile.gettempdir()).resolve()).lower()
suspicious = []
for path in _OPENED:
    if not _REAL_ARTIFACT.search(path):
        continue
    if str(Path(path).resolve()).lower().startswith(tmp_root):
        continue                       # synthetic fixture inside the temp dir
    suspicious.append(path)

check("9a. no real panel/registry/market-response/outcome file was opened",
      not suspicious, str(suspicious[:5]))
check("9b. the audit hook actually observed file activity", len(_OPENED) > 0,
      str(len(_OPENED)))

net_ok = False
try:
    socket.create_connection(("example.invalid", 80))
except NetworkBlocked:
    net_ok = True
except Exception:                                                  # noqa: BLE001
    net_ok = False
check("9c. sockets are still blocked at the end of the run", net_ok)


# --- summary ----------------------------------------------------------------

print()
if _failures:
    print(f"{len(_failures)} CHECK(S) FAILED:")
    for name in _failures:
        print(f"  - {name}")
    sys.exit(1)
print("ALL PHASE 2 OBSERVABILITY DIAGNOSTIC CHECKS PASSED")
