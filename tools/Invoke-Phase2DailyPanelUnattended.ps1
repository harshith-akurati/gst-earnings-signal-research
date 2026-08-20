<#
.SYNOPSIS
  Unattended Phase 2 daily-panel collection cycle: run, validate, commit, push.

.DESCRIPTION
  Runs GST_Phase2_DailyPanel.py unattended and commits its output ONLY if the
  output passes schema validation. A failed or partial run commits nothing and
  exits non-zero.

  Why Windows Scheduler rather than GitHub Actions:
  the panel's Wikipedia leg is paced by a shared 3.5 s limiter that the repo
  documents as "the smallest rate this project has direct evidence for" -- that
  calibration was measured from this host's residential IP. GitHub-hosted
  runners egress from datacenter ranges that Google Trends (pytrends) and
  Wikimedia rate-limit far more aggressively, so the measured pacing would not
  transfer and the GST leg would likely fail outright. Moving the collector to
  an uncalibrated network is a change to collection conditions, not just to
  infrastructure. Recorded here so the choice is inspectable.

.NOTES
  Timeout is sized from measured runtimes: 272 s (2026-08-20) and 959 s
  (2026-07-30). The script's own internal budget is TOTAL_RUN_BUDGET_S = 2700 s.
  The outer backstop below is 3000 s, matching the repository's existing
  `timeout -k 30 3000` convention.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot   = 'C:\Users\hakur\Downloads\Google-Search-Trend-main\Google-Search-Trend-main',
    [int]   $TimeoutSec = 3000,
    [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $RepoRoot

$stamp   = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$logDir  = 'C:\Users\hakur\Downloads\gst-source-quarantine\scheduler\logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }
$runLog  = Join-Path $logDir "phase2_unattended_$stamp.log"

function Log([string]$m) {
    $line = "[{0}] {1}" -f (Get-Date).ToUniversalTime().ToString('s'), $m
    Write-Output $line
    Add-Content -LiteralPath $runLog -Value $line -Encoding utf8
}

# ---- concurrency guard -----------------------------------------------------
$lockDir = 'C:\Users\hakur\Downloads\gst-source-quarantine\scheduler\locks'
if (-not (Test-Path $lockDir)) { New-Item -ItemType Directory -Force -Path $lockDir | Out-Null }
$lock = Join-Path $lockDir 'phase2_daily_panel.lock'
if (Test-Path $lock) {
    $age = (Get-Date) - (Get-Item $lock).LastWriteTime
    if ($age.TotalSeconds -lt $TimeoutSec) {
        Log "REFUSED: another run holds the lock (age $([int]$age.TotalSeconds)s). Exiting without running."
        exit 4
    }
    Log "Stale lock ($([int]$age.TotalSeconds)s > timeout); reclaiming."
    Remove-Item -LiteralPath $lock -Force
}
Set-Content -LiteralPath $lock -Value $stamp -Encoding utf8

try {
    $runDate  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
    $csv      = "Live Signal Engine\GST_Phase2_DailyPanel_TestRun_${runDate}_run3.csv"
    $marker   = "Live Signal Engine\GST_Phase2_DailyPanel_TestRun_${runDate}_run3_COMPLETION_MARKER.json"

    Log "START unattended cycle. run_date=$runDate timeout=${TimeoutSec}s"
    Log "HEAD=$(git rev-parse --short HEAD) branch=$(git rev-parse --abbrev-ref HEAD)"

    # ---- run the panel under an explicit timeout ---------------------------
    $t0 = Get-Date
    $p  = Start-Process -FilePath 'python' -ArgumentList '-u','GST_Phase2_DailyPanel.py' `
              -WorkingDirectory $RepoRoot -NoNewWindow -PassThru `
              -RedirectStandardOutput "$runLog.panel.out" -RedirectStandardError "$runLog.panel.err"
    if (-not $p.WaitForExit($TimeoutSec * 1000)) {
        Log "TIMEOUT after ${TimeoutSec}s -- killing PID $($p.Id). Nothing will be committed."
        try { $p.Kill() } catch {}
        exit 5
    }
    $elapsed = [int]((Get-Date) - $t0).TotalSeconds
    Log "panel exited code=$($p.ExitCode) elapsed=${elapsed}s"

    # ---- schema validation BEFORE any staging ------------------------------
    if (-not (Test-Path -LiteralPath $marker)) { Log "FAIL: no completion marker at $marker"; exit 6 }
    if (-not (Test-Path -LiteralPath $csv))    { Log "FAIL: no final CSV at $csv (written only on clean 24/24)"; exit 6 }

    $m = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
    $rows = @(Import-Csv -LiteralPath $csv)
    $cols = ($rows[0].PSObject.Properties | Measure-Object).Count
    $tick = ($rows | Select-Object -ExpandProperty ticker -Unique | Measure-Object).Count

    $checks = [ordered]@{
        'status is COMPLETE'        = ($m.status -eq 'COMPLETE')
        'marker row_count = 24'     = ($m.row_count -eq 24)
        'all_six_fields_clean = 24' = ($m.all_six_fields_clean_count -eq 24)
        'csv data rows = 24'        = ($rows.Count -eq 24)
        'csv unique tickers = 24'   = ($tick -eq 24)
        'csv column count = 92'     = ($cols -eq 92)
        'gst_zscore 100%'           = ($m.field_completeness_pct.gst_zscore -eq 100)
        'wiki_zscore 100%'          = ($m.field_completeness_pct.wiki_zscore -eq 100)
        'implied_volatility 100%'   = ($m.field_completeness_pct.implied_volatility -eq 100)
        'realized_vol 100%'         = ($m.field_completeness_pct.realized_vol -eq 100)
        'price 100%'                = ($m.field_completeness_pct.price -eq 100)
        'volume 100%'               = ($m.field_completeness_pct.volume -eq 100)
    }
    $failed = @()
    foreach ($k in $checks.Keys) {
        if ($checks[$k]) { Log "  PASS  $k" } else { Log "  FAIL  $k"; $failed += $k }
    }
    if ($failed.Count -gt 0) {
        Log "SCHEMA VALIDATION FAILED ($($failed.Count) check(s)). Committing nothing."
        exit 7
    }
    Log "SCHEMA VALIDATION PASSED (12/12)."

    # ---- existence-checked staging ----------------------------------------
    $stage = @($csv, $marker) | Where-Object { Test-Path -LiteralPath $_ }
    if ($stage.Count -ne 2) { Log "FAIL: expected 2 stageable files, found $($stage.Count)"; exit 8 }
    foreach ($f in $stage) { git add -- $f; Log "  staged $f" }

    if (-not (git diff --cached --name-only)) { Log "Nothing staged (already committed). Exiting 0."; exit 0 }

    $msg = @"
Unattended Phase 2 daily panel $runDate : COMPLETE 24/24

Produced and committed by tools/Invoke-Phase2DailyPanelUnattended.ps1 with no
human in the loop. Schema validation passed 12/12 before anything was staged;
a failed or partial run commits nothing.

  status               $($m.status)
  row_count            $($m.row_count)
  all_six_fields_clean $($m.all_six_fields_clean_count)
  elapsed_s            $($m.elapsed_s)
  csv rows / cols      $($rows.Count) / $cols
  wall clock           ${elapsed}s

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
"@
    git commit -m $msg | Out-Null
    $sha = git rev-parse HEAD
    Log "COMMITTED $sha"

    if ($NoPush) { Log "NoPush set; not pushing."; exit 0 }
    git push | Out-Null
    Log "PUSHED $sha to $(git rev-parse --abbrev-ref '@{u}')"
    Log "DONE unattended cycle OK"
    exit 0
}
finally {
    if (Test-Path $lock) { Remove-Item -LiteralPath $lock -Force }
}
