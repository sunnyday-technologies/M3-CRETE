param(
    [switch]$PrePush
)

$ErrorActionPreference = "Continue"

function GitLines {
    param([string[]]$GitArgs)
    $out = & git @GitArgs 2>$null
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
        throw "git $($GitArgs -join ' ') failed"
    }
    return @($out | Where-Object { $_ -and $_.Trim() -ne "" })
}

function Fail {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

$repoRoot = GitLines @("rev-parse", "--show-toplevel")
if (-not $repoRoot) {
    Fail "Not inside a git repository."
}
Set-Location ([string]$repoRoot)

$failed = $false

Write-Host "Privacy audit: checking local-only BOM/order artifacts..."
$localOnlyTracked = GitLines @(
    "ls-files",
    "bom/build_bom_*.py",
    "bom/M3-CRETE_*_build_bom.xlsx",
    "bom/orders/**",
    "_archive/**",
    "*.env",
    ".env*"
)

if ($localOnlyTracked.Count -gt 0) {
    $failed = $true
    Write-Host "FAIL: local-only or secret-style paths are tracked:"
    $localOnlyTracked | ForEach-Object { Write-Host "  $_" }
}

Write-Host "Privacy audit: checking staged files..."
$staged = GitLines @("diff", "--cached", "--name-only")
if ($staged.Count -eq 0) {
    Write-Host "  No staged files."
} else {
    $riskyStaged = $staged | Where-Object {
        $_ -match '(^|/)\.env($|[./_-])' -or
        $_ -match '(?i)(secret|credential|token|private[-_]?key|orders?/|build_bom_|_archive/)'
    }
    if ($riskyStaged.Count -gt 0) {
        $failed = $true
        Write-Host "FAIL: staged risky paths:"
        $riskyStaged | ForEach-Object { Write-Host "  $_" }
    }
}

Write-Host "Privacy audit: scanning tracked text for sensitive markers..."
$patterns = @(
    'api[_-]?key',
    'client[_-]?secret',
    'private[_-]?key',
    'authorization:',
    'bearer[[:space:]]+',
    'password[[:space:]]*[:=]',
    'passwd[[:space:]]*[:=]',
    'secret[[:space:]]*[:=]',
    'token[[:space:]]*[:=]',
    'BEGIN (RSA|OPENSSH|PRIVATE) KEY',
    'order_id',
    'shipping address',
    'credit card',
    'thread_id'
)

$matchedFiles = New-Object System.Collections.Generic.HashSet[string]
foreach ($pattern in $patterns) {
    $matches = GitLines @(
        "grep",
        "-Il",
        "-E",
        $pattern,
        "--",
        ":(exclude)bom/build_bom_*.py",
        ":(exclude)bom/M3-CRETE_*_build_bom.xlsx",
        ":(exclude)bom/orders/**",
        ":(exclude)_archive/**",
        ":(exclude).gitignore",
        ":(exclude)scripts/privacy_audit.ps1",
        # cadclaw.yaml's redact_patterns block contains regex DEFINITIONS for
        # finding credentials in scanned content — by design it looks like
        # what the audit hunts for. Excluded to avoid self-tripping.
        ":(exclude)cadclaw.yaml"
    )
    foreach ($file in $matches) {
        [void]$matchedFiles.Add($file)
    }
}

if ($matchedFiles.Count -gt 0) {
    $failed = $true
    Write-Host "FAIL: sensitive markers found in tracked files. Review these files; values are intentionally not printed:"
    $matchedFiles | Sort-Object | ForEach-Object { Write-Host "  $_" }
}

Write-Host "Privacy audit: checking untracked publish candidates..."
$untracked = GitLines @("ls-files", "--others", "--exclude-standard")
$riskyUntracked = $untracked | Where-Object {
    $_ -match '(^|/)\.env($|[./_-])' -or
    $_ -match '(?i)(secret|credential|token|private[-_]?key|orders?/|build_bom_|_archive/)' -or
    $_ -match '(?i)\.(xlsx|xls|csv|tsv|docx|pdf)$'
}
if ($riskyUntracked.Count -gt 0) {
    $failed = $true
    Write-Host "FAIL: untracked risky publish candidates exist:"
    $riskyUntracked | ForEach-Object { Write-Host "  $_" }
}

if ($failed) {
    Write-Host "Privacy audit failed. Fix, ignore, or explicitly review the listed paths before pushing."
    exit 1
}

Write-Host "Privacy audit passed."
