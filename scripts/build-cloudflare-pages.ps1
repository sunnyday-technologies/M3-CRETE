param(
  [string]$PublishDir
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir ".."))

if ([string]::IsNullOrWhiteSpace($PublishDir)) {
  $PublishDir = Join-Path $RepoRoot ".cloudflare\pages\m3-crete"
}

$Target = [System.IO.Path]::GetFullPath($PublishDir)
if (-not $Target.StartsWith($RepoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to write outside repository root: $Target"
}

if (Test-Path -LiteralPath $Target) {
  Remove-Item -LiteralPath $Target -Recurse -Force
}
New-Item -ItemType Directory -Path $Target -Force | Out-Null

function Copy-PublicFile {
  param([string]$RelativePath)

  $Source = Join-Path $RepoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw "Missing public file: $RelativePath"
  }

  $Dest = Join-Path $Target $RelativePath
  $DestDir = Split-Path -Parent $Dest
  New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
  Copy-Item -LiteralPath $Source -Destination $Dest -Force
}

function Copy-PublicDirectory {
  param([string]$RelativePath)

  $Source = Join-Path $RepoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Missing public directory: $RelativePath"
  }

  $Dest = Join-Path $Target $RelativePath
  New-Item -ItemType Directory -Path $Dest -Force | Out-Null
  Copy-Item -Path (Join-Path $Source "*") -Destination $Dest -Recurse -Force
}

$rootFiles = @(
  "index.html",
  "config.js",
  "favicon.svg",
  "robots.txt",
  "sitemap.xml",
  "llms.txt",
  "DISCLAIMER.md",
  "_headers",
  "_redirects"
)

foreach ($file in $rootFiles) {
  Copy-PublicFile $file
}

$publicDirs = @(
  ".well-known",
  "blog",
  "build-guide",
  "images",
  "press"
)

foreach ($dir in $publicDirs) {
  Copy-PublicDirectory $dir
}

New-Item -ItemType Directory -Path (Join-Path $Target "bom") -Force | Out-Null
Copy-PublicFile "bom\index.html"
Copy-PublicFile "bom\data.json"
if (Test-Path -LiteralPath (Join-Path $RepoRoot "bom\m3-2-final-hardware-pack.json") -PathType Leaf) {
  Copy-PublicFile "bom\m3-2-final-hardware-pack.json"
}

$blockedRoots = @("CAD", "docs", "firmware", "scripts", ".git", "Credential-Quarantine", "_archive")
foreach ($blocked in $blockedRoots) {
  if (Test-Path -LiteralPath (Join-Path $Target $blocked)) {
    throw "Blocked path was copied into Cloudflare publish directory: $blocked"
  }
}

$secretPatterns = @(
  "AKIA[0-9A-Z]{16}",
  "-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
  "ghp_[A-Za-z0-9_]{20,}",
  "xox[baprs]-[A-Za-z0-9-]{20,}",
  "sk-[A-Za-z0-9]{32,}"
)

$matches = @()
foreach ($pattern in $secretPatterns) {
  $matches += Get-ChildItem -LiteralPath $Target -Recurse -File |
    Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Path -Unique
}

if ($matches.Count -gt 0) {
  $uniqueMatches = $matches | Sort-Object -Unique
  throw "Potential secret-like patterns found in publish directory files: $($uniqueMatches -join ', ')"
}

$files = Get-ChildItem -LiteralPath $Target -Recurse -File
$bytes = ($files | Measure-Object -Property Length -Sum).Sum
Write-Output "Cloudflare publish directory ready: $Target"
Write-Output "Files: $($files.Count)"
Write-Output "Bytes: $bytes"
