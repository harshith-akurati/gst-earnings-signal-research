<#
.SYNOPSIS
  Publish a content-addressed copy of the canonical unattended runner outside
  the repository working tree.

.DESCRIPTION
  The canonical runner is tracked in Git. The scheduled task must NOT execute
  the in-repo copy: on 2026-08-20 an in-repo runner was removed from the working
  tree within ~60 s of its first scheduled execution while remaining intact in
  Git, which left the scheduled task pointing at a path that no longer existed
  (powershell.exe returned 0xFFFD0000, file not found, and the runner never
  reached its first log write).

  This publishes to:

      <deployRoot>\runners\Invoke-Phase2DailyPanelUnattended.<sha256-12>.ps1

  The filename carries the first 12 hex characters of the file's SHA-256, so the
  deployed path IS the integrity check: if the content ever differs from what
  was deployed, the hash no longer matches the name it is stored under, and a
  re-deploy produces a different path rather than silently replacing a good copy.
  A deployment manifest records the full digest, source blob and timestamp.

  Deploying does NOT register or modify any scheduled task. Arming is a separate,
  deliberate step.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$RepoRoot,
    [string]$DeployRoot = 'C:\Users\hakur\Downloads\gst-source-quarantine\scheduler\runners'
)

$ErrorActionPreference = 'Stop'

$top = (& git -C $RepoRoot rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $top) { throw "not a git repository: $RepoRoot" }
$top = (Resolve-Path -LiteralPath $top).Path.TrimEnd('\')

$src = Join-Path $top 'tools\Invoke-Phase2DailyPanelUnattended.ps1'
if (-not (Test-Path -LiteralPath $src)) { throw "canonical runner missing: $src" }

# Refuse to deploy a runner that differs from what is committed -- the deployed
# copy must be reproducible from the repository, not from a dirty working tree.
$dirty = (& git -C $top status --porcelain -- 'tools/Invoke-Phase2DailyPanelUnattended.ps1')
if ($dirty) { throw "canonical runner has uncommitted changes; commit it before deploying:`n$dirty" }

if (-not (Test-Path $DeployRoot)) { New-Item -ItemType Directory -Force -Path $DeployRoot | Out-Null }

$digest = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower()
$short  = $digest.Substring(0, 12)
$dest   = Join-Path $DeployRoot "Invoke-Phase2DailyPanelUnattended.$short.ps1"

if (Test-Path -LiteralPath $dest) {
    $existing = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()
    if ($existing -ne $digest) { throw "hash collision at $dest -- refusing to overwrite" }
    Write-Output "already deployed (content identical): $dest"
} else {
    Copy-Item -LiteralPath $src -Destination $dest -Force
    Write-Output "deployed: $dest"
}

$verify = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToLower()
if ($verify -ne $digest) { throw "post-copy verification failed at $dest" }

$blob = (& git -C $top rev-parse "HEAD:tools/Invoke-Phase2DailyPanelUnattended.ps1")
$manifest = [ordered]@{
    deployed_utc     = (Get-Date).ToUniversalTime().ToString('s') + 'Z'
    source_repo      = $top
    source_branch    = (& git -C $top rev-parse --abbrev-ref HEAD)
    source_commit    = (& git -C $top rev-parse HEAD)
    source_blob      = $blob
    sha256           = $digest
    sha256_short     = $short
    deployed_path    = $dest
    size_bytes       = (Get-Item -LiteralPath $dest).Length
}
$mf = Join-Path $DeployRoot 'deployment_manifest.jsonl'
Add-Content -LiteralPath $mf -Value ($manifest | ConvertTo-Json -Compress) -Encoding utf8

Write-Output "sha256      : $digest"
Write-Output "source blob : $blob"
Write-Output "manifest    : $mf"
Write-Output ''
Write-Output 'Deployment complete. No scheduled task was created or modified.'
