<#
.SYNOPSIS
  Unattended Phase 2 daily-panel cycle: run, validate, commit, push.

.DESCRIPTION
  CANONICAL COPY. This file is tracked in Git and is the source of truth.
  It is NOT the copy the scheduled task executes. Deploy-Phase2Runner.ps1
  publishes a content-addressed copy outside the repository working tree, and
  the scheduled task points at that copy.

  Why the deployed copy lives outside the repo:
  UNRESOLVED_POSSIBLE_THIRD_PARTY_SECURITY_REMOVAL.

  On 2026-08-20 the previous in-repo runner was removed from the working tree
  within ~60 s of its first scheduled execution while remaining intact in Git,
  leaving the scheduled task pointing at a path that no longer existed.

  What the evidence establishes: it was not Git (clean reflog, no checkout,
  reset or clean) and not Microsoft Defender (Passive Mode, real-time
  protection disabled, empty detection history). The file was absent from a
  recursive -Force search of the user profile, so it was removed rather than
  moved.

  What the evidence does NOT establish: the actual agent. AVG Antivirus and
  McAfee are both registered on this host, but neither has been shown to have
  removed the file -- no quarantine record was produced for either, and no
  vendor log was read. Naming either as the cause would be an inference beyond
  the evidence, and is not made here.

  Relocating outside the working tree is therefore mitigation against a real
  but unattributed removal, not a fix for a diagnosed one. The ROST capture
  runner, which has lived outside the repo since 2026-08-19 and executes
  normally, is the working precedent this follows.

  Repository location is resolved with `git -C <RepoRoot> rev-parse --show-toplevel`
  and compared against the supplied path. A mismatch aborts; the runner never
  assumes its own directory or the current directory is the repository.

.PARAMETER Mode
  Run       full cycle: lock, panel, validate, stage, commit, push.
  Preflight environment checks only. Makes no network calls, does not launch
            the panel, stages nothing and commits nothing.

.NOTES
  Exit codes -- the runner never stages anything unless validation returns 0.
     0 success (or preflight OK)   3 repo/environment resolution failed
     4 another run holds the lock  5 panel exceeded the outer timeout
     6 a required artifact is missing (marker or final CSV)
     7 schema validation failed    8 staging mismatch
     9 commit succeeded but push failed (commit is local only)
    10 refused: outside the 02:05-02:25 America/Chicago window. Nothing was
       done -- no network, no git, no staging, no commit, no push.
#>
[CmdletBinding()]
param(
    [ValidateSet('Run', 'Preflight')]
    [string]$Mode = 'Run',

    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,

    [string]$ExpectedBranch = 'phase5-unattended-panel-recovery',
    [int]   $TimeoutSec     = 3000,
    [switch]$NoPush,

    # TEST USE ONLY. Supplies the instant the local-time gate evaluates instead
    # of the host clock. Its use is logged, so an injected clock can never be
    # mistaken for a real firing.
    [string]$NowOverride
)

$ErrorActionPreference = 'Stop'

$deployRoot = 'C:\Users\hakur\Downloads\gst-source-quarantine\scheduler'
$logDir     = Join-Path $deployRoot 'logs'
$lockDir    = Join-Path $deployRoot 'locks'
foreach ($d in @($logDir, $lockDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

$stamp  = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$runLog = Join-Path $logDir "phase2_unattended_${stamp}.log"

function Log([string]$m) {
    $line = '[{0}] {1}' -f (Get-Date).ToUniversalTime().ToString('s'), $m
    Write-Output $line
    Add-Content -LiteralPath $runLog -Value $line -Encoding utf8
}

function Fail([int]$code, [string]$why) {
    Log "ABORT($code): $why"
    exit $code
}

Log "START mode=$Mode stamp=$stamp"

# ---- local-time execution gate --------------------------------------------
# FIRST action of substance, deliberately ahead of repository resolution. A
# refusal here performs no network call, no git command, no staging, no commit
# and no push -- it writes this log line and exits 10. StartWhenAvailable is
# False on the task, so a missed cycle is skipped rather than deferred; this
# gate is the second half of that guarantee, refusing a firing that arrives
# outside 02:05-02:25 America/Chicago however it got there.
$gate = Join-Path $PSScriptRoot 'phase2_window_gate.py'
if (-not (Test-Path -LiteralPath $gate)) {
    # The deployed runner lives outside the repository, so the gate is resolved
    # from the repository when it is not beside the runner.
    $gate = Join-Path $RepoRoot 'tools\phase2_window_gate.py'
}
if (-not (Test-Path -LiteralPath $gate)) { Fail 3 "window gate module missing: $gate" }

$pythonForGate = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonForGate) { Fail 3 'python not found on PATH (needed by the window gate)' }

$gateArgs = @($gate)
if ($NowOverride) { $gateArgs += @('--now', $NowOverride) }
$gateOut = & $pythonForGate.Source @gateArgs 2>&1
$gateCode = $LASTEXITCODE
foreach ($l in $gateOut) { Log "  $l" }
if ($gateCode -ne 0) {
    Log 'REFUSED by local-time gate: no network, git, staging, commit or push was performed'
    exit 10
}
Log 'window gate OPEN'

# ---- repository resolution -------------------------------------------------
if (-not (Test-Path -LiteralPath $RepoRoot)) { Fail 3 "RepoRoot does not exist: $RepoRoot" }

# git writes to stderr on failure, and under $ErrorActionPreference='Stop' a
# native command's stderr is promoted to a terminating error before the exit
# code can be inspected. Probe with error action relaxed so the abort path
# below owns the outcome and the documented exit code is what callers see.
$top = $null
try {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    # Capture fully before selecting: piping a native command into
    # Select-Object -First closes the pipeline early, terminates git and leaves
    # a misleading $LASTEXITCODE.
    $out = @(& git -C $RepoRoot rev-parse --show-toplevel 2>$null)
    $rc  = $LASTEXITCODE
    if ($out.Count -gt 0) { $top = $out[0] }
} finally {
    $ErrorActionPreference = $prev
}
if ($rc -ne 0 -or -not $top) { Fail 3 "git rev-parse --show-toplevel failed under $RepoRoot (git exit $rc)" }
$topNorm  = (Resolve-Path -LiteralPath $top).Path.TrimEnd('\')
$rootNorm = (Resolve-Path -LiteralPath $RepoRoot).Path.TrimEnd('\')
if ($topNorm -ne $rootNorm) { Fail 3 "RepoRoot '$rootNorm' is not a repository toplevel (git says '$topNorm')" }
Log "repo toplevel verified: $topNorm"

$branch = (& git -C $topNorm rev-parse --abbrev-ref HEAD 2>$null)
if ($branch -ne $ExpectedBranch) { Fail 3 "branch is '$branch', expected '$ExpectedBranch'" }
$head = (& git -C $topNorm rev-parse --short HEAD)
Log "branch=$branch head=$head"

$panel     = Join-Path $topNorm 'GST_Phase2_DailyPanel.py'
$validator = Join-Path $topNorm 'tools\phase2_panel_validate.py'
foreach ($f in @($panel, $validator)) {
    if (-not (Test-Path -LiteralPath $f)) { Fail 3 "required file missing: $f" }
}
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { Fail 3 'python not found on PATH' }
Log "panel, validator and python all present"

$runDate = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
$csvRel    = "Live Signal Engine/GST_Phase2_DailyPanel_TestRun_${runDate}_run3.csv"
$markerRel = "Live Signal Engine/GST_Phase2_DailyPanel_TestRun_${runDate}_run3_COMPLETION_MARKER.json"
$csvAbs    = Join-Path $topNorm $csvRel
$markerAbs = Join-Path $topNorm $markerRel

# ---- preflight stops here --------------------------------------------------
if ($Mode -eq 'Preflight') {
    $upstream = (& git -C $topNorm rev-parse --abbrev-ref '@{u}' 2>$null)
    Log ("upstream: " + $(if ($upstream) { $upstream } else { '<none>' }))
    Log ("git user.name : " + (& git -C $topNorm config user.name))
    Log ("git user.email: " + (& git -C $topNorm config user.email))
    Log "log dir writable : $logDir"
    Log "lock dir writable: $lockDir"
    Log "would write CSV  : $csvRel"
    Log "PREFLIGHT OK -- no network call made, panel not launched, nothing staged"
    exit 0
}

# ---- concurrency guard -----------------------------------------------------
$lock = Join-Path $lockDir 'phase2_daily_panel.lock'
if (Test-Path $lock) {
    $age = (Get-Date) - (Get-Item $lock).LastWriteTime
    if ($age.TotalSeconds -lt $TimeoutSec) { Fail 4 "another run holds the lock (age $([int]$age.TotalSeconds)s)" }
    Log "stale lock ($([int]$age.TotalSeconds)s >= timeout); reclaiming"
    Remove-Item -LiteralPath $lock -Force
}
Set-Content -LiteralPath $lock -Value $stamp -Encoding utf8

try {
    # ---- run the panel under an explicit outer timeout ---------------------
    $t0 = Get-Date
    $p = Start-Process -FilePath $python.Source -ArgumentList '-u', 'GST_Phase2_DailyPanel.py' `
            -WorkingDirectory $topNorm -NoNewWindow -PassThru `
            -RedirectStandardOutput "$runLog.panel.out" -RedirectStandardError "$runLog.panel.err"
    if (-not $p.WaitForExit($TimeoutSec * 1000)) {
        Log "TIMEOUT after ${TimeoutSec}s -- killing PID $($p.Id); nothing will be committed"
        try { $p.Kill() } catch { }
        exit 5
    }
    $elapsed = [int]((Get-Date) - $t0).TotalSeconds
    Log "panel exited code=$($p.ExitCode) elapsed=${elapsed}s"

    # ---- schema validation BEFORE any staging ------------------------------
    $vout = & $python.Source $validator --marker $markerAbs --csv $csvAbs 2>&1
    $vcode = $LASTEXITCODE
    foreach ($l in $vout) { Log "  $l" }
    if ($vcode -ne 0) { Fail $vcode "schema validation returned $vcode; committing nothing" }
    Log 'schema validation PASSED'

    # ---- existence-checked staging ----------------------------------------
    $stage = @($csvRel, $markerRel) | Where-Object { Test-Path -LiteralPath (Join-Path $topNorm $_) }
    if ($stage.Count -ne 2) { Fail 8 "expected 2 stageable files, found $($stage.Count)" }
    foreach ($f in $stage) { & git -C $topNorm add -- $f; Log "  staged $f" }

    $staged = (& git -C $topNorm diff --cached --name-only)
    if (-not $staged) { Log 'nothing staged (already committed); exiting 0'; exit 0 }

    $msg = @"
Unattended Phase 2 daily panel ${runDate}: COMPLETE 24/24

Produced and committed by the scheduled unattended runner with no human in the
loop. tools/phase2_panel_validate.py passed before anything was staged; a
partial or failed run commits nothing.

  run_date   $runDate
  elapsed    ${elapsed}s
  panel exit $($p.ExitCode)
  runner     $head

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
"@
    & git -C $topNorm commit -m $msg | Out-Null
    $sha = (& git -C $topNorm rev-parse HEAD)
    Log "COMMITTED $sha"

    if ($NoPush) { Log 'NoPush set; not pushing'; exit 0 }
    & git -C $topNorm push | Out-Null
    if ($LASTEXITCODE -ne 0) { Log 'push failed; commit is local only'; exit 9 }
    Log "PUSHED $sha"
    Log 'DONE unattended cycle OK'
    exit 0
}
finally {
    if (Test-Path $lock) { Remove-Item -LiteralPath $lock -Force }
}
