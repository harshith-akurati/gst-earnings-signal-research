#!/usr/bin/env python3
"""Two consecutive scheduled dates must both succeed without human intervention.

This is the test the system did not have, and its absence is why the 2026-08-24
failure reached production. What existed tested each guard in isolation against a
stub panel whose output set had been modelled on the ALLOWLIST rather than on what
the real panel writes -- so the allowlist and the stub agreed with each other and
both disagreed with reality. Nothing exercised two runs in sequence, so nothing
could observe that a successful run made the next one refuse.

Two independent defects had to be fixed for this to pass, and this file asserts
both from the outside, by running the runner twice:

  1. STAGING. The panel writes a dated _CHECKPOINT_PARTIAL.csv on every run,
     successful ones included. The old allowlist was exactly [final CSV, marker],
     so a completed capture presented three changed paths to a two-path allowlist
     and was refused at EXIT_STAGING after all the network work was done. The
     stub panel here writes the checkpoint too -- that is the whole point.

  2. CODE IDENTITY. The old pin compared git rev-parse HEAD to a fixed commit
     passed on the command line. The runner's own successful commit advances HEAD
     past that pin, so day two refused with EXIT_ENV. Replaced by the runner
     file's SHA-256 plus descent from an approved implementation commit.

Fully offline. No socket is created: the panel and validator are local stubs and
the remote is a bare repository on disk. See the socket guard below, which fails
the run if anything attempts a connection.
"""
import io
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# --- socket guard: any outbound connection attempt is a test failure ----------
class _BlockedSocket(socket.socket):
    def connect(self, *a, **k):
        raise AssertionError("network access attempted; this suite must stay offline")

    def connect_ex(self, *a, **k):
        raise AssertionError("network access attempted; this suite must stay offline")


socket.socket = _BlockedSocket
socket.create_connection = lambda *a, **k: (_ for _ in ()).throw(
    AssertionError("network access attempted; this suite must stay offline"))

sys.path.insert(0, str(Path(__file__).parent / "tools"))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "runner", Path(__file__).parent / "tools" / "run_phase2_daily_panel_unattended.py")
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

FAILURES = []
CHECKS = 0


def check(label, cond, detail=""):
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}  {detail}")
        FAILURES.append(label)


def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


DAY1 = "2026-09-01T02:15:00-05:00"
DAY2 = "2026-09-02T02:15:00-05:00"
D1 = "2026-09-01"
D2 = "2026-09-02"
GOOD_TASK = (r"C:\python.exe", '"run_phase2_daily_panel_unattended.py" --mode run')


def rel(date, suffix):
    return f"Live Signal Engine/GST_Phase2_DailyPanel_TestRun_{date}_run3{suffix}"


class Rig:
    """A repo whose stub panel writes the SAME THREE FILES the real panel writes."""

    def __init__(self, panel="ok"):
        self.tmp = Path(tempfile.mkdtemp(prefix="phase2_recur_"))
        self.repo = self.tmp / "repo"
        self.remote = self.tmp / "remote.git"
        self.repo.mkdir()
        (self.repo / "Live Signal Engine").mkdir(parents=True)
        (self.repo / "tools").mkdir(parents=True)
        sh(["git", "init", "--quiet", "--initial-branch", R.EXPECTED_BRANCH, str(self.repo)])
        sh(["git", "-C", str(self.repo), "config", "user.email", "runner@test.local"])
        sh(["git", "-C", str(self.repo), "config", "user.name", "Runner Test"])
        sh(["git", "init", "--quiet", "--bare", str(self.remote)])

        # The stub panel writes final CSV + marker + CHECKPOINT, exactly like the
        # real one. A stub that wrote only the first two would re-create the blind
        # spot this file exists to close.
        body = (
            "import sys, datetime as dt\n"
            "from pathlib import Path\n"
            "d = dt.date.today().isoformat()\n"
            "import os\n"
            "d = os.environ.get('STUB_RUN_DATE', d)\n"
            "base = Path('Live Signal Engine') / f'GST_Phase2_DailyPanel_TestRun_{d}_run3'\n"
            "base.parent.mkdir(parents=True, exist_ok=True)\n"
            "rows = 'run_date,ticker,value\\n' + ''.join(f'{d},T{i},1\\n' for i in range(24))\n"
            "Path(str(base) + '_CHECKPOINT_PARTIAL.csv').write_text(rows, encoding='utf-8')\n"
        )
        if panel == "ok":
            body += (
                "Path(str(base) + '.csv').write_text(rows, encoding='utf-8')\n"
                "Path(str(base) + '_COMPLETION_MARKER.json').write_text('{\"status\":\"COMPLETE\"}', encoding='utf-8')\n"
            )
        elif panel == "partial":
            # writes ONLY the checkpoint, as a real PARTIAL run does
            body += "sys.exit(1)\n"
        elif panel == "stray":
            body += (
                "Path(str(base) + '.csv').write_text(rows, encoding='utf-8')\n"
                "Path(str(base) + '_COMPLETION_MARKER.json').write_text('{}', encoding='utf-8')\n"
                "Path('STRAY.txt').write_text('nope', encoding='utf-8')\n"
            )
        (self.repo / R.PANEL_SCRIPT).write_text(body, encoding="utf-8")
        (self.repo / R.VALIDATOR).write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        (self.repo / R.RUNNER_REL).write_text("# committed runner placeholder\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text("state/\n", encoding="utf-8")

        sh(["git", "-C", str(self.repo), "add", "-A"])
        sh(["git", "-C", str(self.repo), "commit", "--quiet", "-m", "approved implementation"])
        sh(["git", "-C", str(self.repo), "remote", "add", "origin", str(self.remote)])
        sh(["git", "-C", str(self.repo), "push", "--quiet", "-u", "origin", R.EXPECTED_BRANCH])
        self.approved = sh(["git", "-C", str(self.repo), "rev-parse", "HEAD"]).stdout.strip()
        self.runner_hash = R.runner_file_sha256(self.repo)

        self._saved = (R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR)
        R.STATE_DIR = self.tmp / "state"
        R.LOG_DIR = R.STATE_DIR / "logs"
        R.LOCK_DIR = R.STATE_DIR / "locks"
        R.ATTEMPT_DIR = R.STATE_DIR / "attempts"

    def call(self, now, run_date, approved=None, runner_hash=None, task=GOOD_TASK):
        os.environ["STUB_RUN_DATE"] = run_date
        argv = ["--repo-root", str(self.repo), "--mode", "run", "--now-override", now,
                "--approved-commit", approved or self.approved,
                "--runner-sha256", runner_hash or self.runner_hash]
        real = R._query_task_action
        R._query_task_action = (lambda: task)
        try:
            return R.main(argv)
        finally:
            R._query_task_action = real
            os.environ.pop("STUB_RUN_DATE", None)

    def head(self):
        return sh(["git", "-C", str(self.repo), "rev-parse", "HEAD"]).stdout.strip()

    def remote_head(self):
        out = sh(["git", "-C", str(self.repo), "ls-remote", "origin",
                  f"refs/heads/{R.EXPECTED_BRANCH}"]).stdout.strip()
        return out.split("\t")[0] if out else ""

    def committed_files(self, sha):
        return [x for x in sh(["git", "-C", str(self.repo), "show", "--name-only",
                               "--pretty=format:", sha]).stdout.splitlines() if x.strip()]

    def log_text(self):
        logs = sorted(R.LOG_DIR.glob("phase2_unattended_*.log")) if R.LOG_DIR.is_dir() else []
        return logs[-1].read_text(encoding="utf-8") if logs else ""

    def close(self):
        (R.STATE_DIR, R.LOG_DIR, R.LOCK_DIR, R.ATTEMPT_DIR) = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)


# === 1. two consecutive dates, no intervention between them ==================
print("\n=== 1. two consecutive scheduled dates ===")
g = Rig()
try:
    approved = g.approved
    code_before = sh(["git", "-C", str(g.repo), "rev-parse", f"HEAD:{R.PANEL_SCRIPT}"]).stdout.strip()

    rc1 = g.call(DAY1, D1)
    head1 = g.head()
    check("1a. day one returns EXIT_OK", rc1 == R.EXIT_OK, str(rc1))
    check("1b. day one created a commit", head1 != approved)
    check("1c. day one pushed; remote equals local", g.remote_head() == head1)
    files1 = g.committed_files(head1)
    check("1d. day one committed all three panel outputs", len(files1) == 3, str(files1))
    check("1e. day one committed the checkpoint (the 8/24 defect)",
          any("CHECKPOINT_PARTIAL" in f for f in files1), str(files1))

    # NOTHING happens here. No re-registration, no argument change, no human.
    rc2 = g.call(DAY2, D2)
    head2 = g.head()
    check("1f. day two returns EXIT_OK with the SAME arguments", rc2 == R.EXIT_OK, str(rc2))
    check("1g. day two created a further commit", head2 != head1)
    check("1h. HEAD advanced across both days", head2 != approved and head1 != approved)
    check("1i. day two pushed; remote equals local", g.remote_head() == head2)
    files2 = g.committed_files(head2)
    check("1j. day two committed its own dated outputs",
          all(D2 in f for f in files2) and len(files2) == 3, str(files2))

    # the pin still holds after two data-only commits
    ok = sh(["git", "-C", str(g.repo), "merge-base", "--is-ancestor", approved, head2])
    check("1k. HEAD still descends from the approved implementation commit",
          ok.returncode == 0)
    code_after = sh(["git", "-C", str(g.repo), "rev-parse", f"HEAD:{R.PANEL_SCRIPT}"]).stdout.strip()
    check("1l. neither run altered the panel program", code_after == code_before)
    check("1m. neither run altered the runner file",
          R.runner_file_sha256(g.repo) == g.runner_hash)
    check("1n. worktree is clean after both runs",
          sh(["git", "-C", str(g.repo), "status", "--porcelain"]).stdout.strip() == "")
finally:
    g.close()

# === 2. refusal surfaces that must still hold ================================
print("\n=== 2. refusals ===")

g = Rig()
try:
    (g.repo / "dirt.txt").write_text("x", encoding="utf-8")
    check("2a. dirty tree refuses with EXIT_ENV", g.call(DAY1, D1) == R.EXIT_ENV)
finally:
    g.close()

g = Rig(panel="stray")
try:
    rc = g.call(DAY1, D1)
    check("2b. unexpected path refuses with EXIT_STAGING", rc == R.EXIT_STAGING, str(rc))
    check("2c. refusal names the stray path", "STRAY.txt" in g.log_text())
finally:
    g.close()

g = Rig()
try:
    g.call(DAY1, D1)
    rc = g.call(DAY1, D1)
    check("2d. duplicate date refuses with EXIT_DUPLICATE", rc == R.EXIT_DUPLICATE, str(rc))
finally:
    g.close()

g = Rig()
try:
    rc = g.call(DAY1, D1, runner_hash="0" * 64)
    check("2e. runner-hash mismatch refuses with EXIT_INTEGRITY", rc == R.EXIT_INTEGRITY, str(rc))
    check("2f. nothing was committed on a hash mismatch", g.head() == g.approved)
finally:
    g.close()

g = Rig()
try:
    rc = g.call(DAY1, D1, approved="0" * 40)
    check("2g. non-descendant HEAD refuses with EXIT_INTEGRITY", rc == R.EXIT_INTEGRITY, str(rc))
finally:
    g.close()

g = Rig()
try:
    # break commits by removing the identity the commit needs
    sh(["git", "-C", str(g.repo), "config", "--unset", "user.email"])
    sh(["git", "-C", str(g.repo), "config", "--unset", "user.name"])
    sh(["git", "-C", str(g.repo), "config", "--local", "user.useConfigOnly", "true"])
    rc = g.call(DAY1, D1)
    check("2h. commit failure refuses without pushing",
          rc in (R.EXIT_COMMIT, R.EXIT_STAGING), str(rc))
    check("2i. remote unchanged after commit failure", g.remote_head() == g.approved)
finally:
    g.close()

g = Rig()
try:
    # destroy the remote so the push cannot succeed
    shutil.rmtree(g.remote, ignore_errors=True)
    rc = g.call(DAY1, D1)
    check("2j. push failure returns EXIT_PUSH and keeps the local commit",
          rc == R.EXIT_PUSH, str(rc))
    check("2k. the local commit is preserved after push failure", g.head() != g.approved)
    check("2l. push failure is recorded for the date",
          R.attempt_path(D1).is_file())
finally:
    g.close()

g = Rig()
try:
    # remote moved ahead: a fast-forward push must fail rather than force
    g.call(DAY1, D1)
    side = g.tmp / "side"
    sh(["git", "clone", "--quiet", str(g.remote), str(side)])
    # The bare remote's symbolic HEAD points at a branch it does not have, so a
    # plain clone lands DETACHED and `push origin <branch>` fails with "src
    # refspec does not match any" -- which silently makes the remote never
    # diverge and the whole scenario vacuous. Materialise the branch explicitly.
    sh(["git", "-C", str(side), "checkout", "-B", R.EXPECTED_BRANCH,
        f"origin/{R.EXPECTED_BRANCH}", "--quiet"])
    sh(["git", "-C", str(side), "config", "user.email", "o@t.local"])
    sh(["git", "-C", str(side), "config", "user.name", "Other"])
    (side / "other.txt").write_text("divergent", encoding="utf-8")
    sh(["git", "-C", str(side), "add", "-A"])
    sh(["git", "-C", str(side), "commit", "--quiet", "-m", "divergent remote commit"])
    pushed = sh(["git", "-C", str(side), "push", "origin", R.EXPECTED_BRANCH])
    check("2m. the divergence was actually established", pushed.returncode == 0,
          pushed.stderr.strip()[:160])
    remote_ahead = g.remote_head()
    rc = g.call(DAY2, D2)
    check("2n. a diverged remote does not produce a silent success",
          rc != R.EXIT_OK, str(rc))
    check("2o. the refusal is the push step", rc == R.EXIT_PUSH, str(rc))
    # the real anti-force assertion: the other commit must still be the remote
    # tip, or reachable from it -- checked against the REMOTE, not the clone
    # that authored it (which would hold the object either way).
    still = g.remote_head()
    check("2p. the runner did not force-push over the other commit",
          still == remote_ahead, f"remote moved {remote_ahead[:12]} -> {still[:12]}")
finally:
    g.close()

print(f"\n{CHECKS} checks run")
if FAILURES:
    print(f"\n{len(FAILURES)} CHECK(S) FAILED:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("\nALL TWO-DATE RECURRENCE CHECKS PASSED")
