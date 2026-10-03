param(
  [string]$PublishDir
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir ".."))

$AllowedTarget = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot ".cloudflare\pages\m3-crete"))
if ([string]::IsNullOrWhiteSpace($PublishDir)) { $PublishDir = $AllowedTarget }
$Target = [System.IO.Path]::GetFullPath($PublishDir)
if (-not [string]::Equals($Target, $AllowedTarget, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to write anywhere except the fixed publish directory: $AllowedTarget"
}

if (Test-Path -LiteralPath $Target) {
  # Clear only an explicit read-only bit on files. Rewriting directory
  # attributes is unnecessary and can fail on managed/sandboxed filesystems.
  Get-ChildItem -LiteralPath $Target -Recurse -Force -File |
    Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 } |
    ForEach-Object { $_.IsReadOnly = $false }
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
  "404.html",
  "config.js",
  "favicon.svg",
  "robots.txt",
  "sitemap.xml",
  "llms.txt",
  "DISCLAIMER.md",
  "ELECTRICAL_SCOPE_BOUNDARY.md",
  "SAFETY_NOTICE.md",
  "_headers",
  "_redirects"
)

foreach ($file in $rootFiles) {
  Copy-PublicFile $file
}

# Security contact is a required production surface, not an optional directory extra.
Copy-PublicFile ".well-known\security.txt"

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
Copy-PublicFile "bom\BUYING_GUIDE_PROMPT.md"
if (Test-Path -LiteralPath (Join-Path $RepoRoot "bom\m3-2-final-hardware-pack.json") -PathType Leaf) {
  Copy-PublicFile "bom\m3-2-final-hardware-pack.json"
}

$blockedRoots = @("CAD", "docs", "firmware", "scripts", ".git", "Credential-Quarantine", "_archive")
foreach ($blocked in $blockedRoots) {
  if (Test-Path -LiteralPath (Join-Path $Target $blocked)) {
    throw "Blocked path was copied into Cloudflare publish directory: $blocked"
  }
}

# No CAD, nothing over Cloudflare's 25 MiB cap (the near-miss tripwire).
$tripwireFiles = Get-ChildItem -LiteralPath $Target -Recurse -Force -File
$cadExt = @(".stl",".step",".stp",".3mf",".f3d",".f3z",".sldprt",".sldasm",".ipt",".iam",".iges",".igs",".x_t",".x_b",".dwg",".dxf")
$cad = $tripwireFiles | Where-Object { $cadExt -contains $_.Extension.ToLower() }
if ($cad) { throw "CAD file(s) reached the Cloudflare publish dir: $($cad.FullName -join ', ')" }
$big = $tripwireFiles | Where-Object { $_.Length -gt 25MB }
if ($big) { throw "File(s) over Cloudflare's 25 MiB limit: $(($big | ForEach-Object { $_.Name }) -join ', ')" }

$secretPatterns = @(
  "AKIA[0-9A-Z]{16}",
  "-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
  "ghp_[A-Za-z0-9_]{20,}",
  "xox[baprs]-[A-Za-z0-9-]{20,}",
  "sk-[A-Za-z0-9]{32,}"
)

$matches = @()
foreach ($pattern in $secretPatterns) {
  $matches += Get-ChildItem -LiteralPath $Target -Recurse -Force -File |
    Select-String -Pattern $pattern -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Path -Unique
}

if ($matches.Count -gt 0) {
  $uniqueMatches = $matches | Sort-Object -Unique
  throw "Potential secret-like patterns found in publish directory files: $($uniqueMatches -join ', ')"
}

# Parse every published JSON document. A malformed discovery or BOM resource is
# a release failure, not a browser-only problem.
$jsonFiles = Get-ChildItem -LiteralPath $Target -Recurse -Force -File -Filter "*.json"
foreach ($jsonFile in $jsonFiles) {
  try {
    Get-Content -LiteralPath $jsonFile.FullName -Raw -Encoding UTF8 |
      ConvertFrom-Json | Out-Null
  } catch {
    throw "Invalid published JSON: $($jsonFile.FullName)"
  }
}

# Parse embedded JSON-LD and reject the known Open3DCP identity regression. The
# project is a draft schema, not a supplied Dataset.
function Test-Open3DcpIdentity {
  param(
    [Parameter(Mandatory = $true)]$Node,
    [Parameter(Mandatory = $true)][string]$Source
  )

  if ($null -eq $Node) { return }

  if ($Node -is [System.Array]) {
    foreach ($item in $Node) { Test-Open3DcpIdentity -Node $item -Source $Source }
    return
  }

  if ($Node -is [System.Management.Automation.PSCustomObject]) {
    $nameProperty = $Node.PSObject.Properties['name']
    $typeProperty = $Node.PSObject.Properties['@type']
    if ($nameProperty -and ([string]$nameProperty.Value -match 'Open3DCP')) {
      $types = @($typeProperty.Value)
      if ($types -contains 'Dataset') {
        throw "Open3DCP must not be published as schema.org Dataset: $Source"
      }
    }
    foreach ($property in $Node.PSObject.Properties) {
      Test-Open3DcpIdentity -Node $property.Value -Source $Source
    }
  }
}

$jsonLdCount = 0
$htmlFiles = Get-ChildItem -LiteralPath $Target -Recurse -Force -File -Filter "*.html"
foreach ($htmlFile in $htmlFiles) {
  $html = Get-Content -LiteralPath $htmlFile.FullName -Raw -Encoding UTF8
  $blocks = [regex]::Matches(
    $html,
    '<script[^>]+type=["'']application/ld\+json["''][^>]*>(.*?)</script>',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor
      [System.Text.RegularExpressions.RegexOptions]::Singleline
  )
  foreach ($block in $blocks) {
    try {
      $document = $block.Groups[1].Value | ConvertFrom-Json
    } catch {
      throw "Invalid embedded JSON-LD: $($htmlFile.FullName)"
    }
    $jsonLdCount++
    Test-Open3DcpIdentity -Node $document -Source $htmlFile.FullName
  }
}

if ($jsonLdCount -lt 1) {
  throw "No embedded JSON-LD documents found in publish directory"
}

# Every local hyperlink must resolve inside the fixed output. This guards
# against safety notices, machine resources, and content pages being linked
# from public HTML but silently omitted from the allowlisted build.
# Runs on Windows locally and on Linux pwsh in CI, so never hard-code '\'.
$Sep = [string][System.IO.Path]::DirectorySeparatorChar

function Resolve-PublicHref {
  param(
    [Parameter(Mandatory = $true)][string]$Href,
    [Parameter(Mandatory = $true)][string]$HtmlPath
  )

  $cleanHref = (($Href -split '[?#]', 2)[0]).Trim()
  if ([string]::IsNullOrWhiteSpace($cleanHref) -or $cleanHref.StartsWith('//')) { return $null }
  if ($cleanHref.Contains('${')) { return $null }
  if ($cleanHref -match '^[A-Za-z][A-Za-z0-9+.-]*:') { return $null }

  $decodedHref = [System.Uri]::UnescapeDataString($cleanHref)
  if ($decodedHref.StartsWith('/')) {
    $relative = $decodedHref.TrimStart('/') -replace '/', $Sep
    $candidate = if ([string]::IsNullOrWhiteSpace($relative)) {
      $Target
    } else {
      Join-Path $Target $relative
    }
  } else {
    $candidate = Join-Path (Split-Path -Parent $HtmlPath) ($decodedHref -replace '/', $Sep)
  }

  $candidate = [System.IO.Path]::GetFullPath($candidate)
  $targetPrefix = $Target.TrimEnd('\', '/') + $Sep
  if (
    -not [string]::Equals($candidate, $Target, [System.StringComparison]::OrdinalIgnoreCase) -and
    -not $candidate.StartsWith($targetPrefix, [System.StringComparison]::OrdinalIgnoreCase)
  ) {
    throw "Local hyperlink escapes the fixed publish directory"
  }

  if ($decodedHref.EndsWith('/') -or (Test-Path -LiteralPath $candidate -PathType Container)) {
    $candidate = Join-Path $candidate 'index.html'
  }
  return $candidate
}

$brokenLinks = @()
$localLinkCount = 0
foreach ($htmlFile in $htmlFiles) {
  $html = Get-Content -LiteralPath $htmlFile.FullName -Raw -Encoding UTF8
  $hrefs = [regex]::Matches(
    $html,
    '\bhref\s*=\s*["'']([^"'']+)["'']',
    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
  )
  foreach ($hrefMatch in $hrefs) {
    $href = $hrefMatch.Groups[1].Value
    $resolved = Resolve-PublicHref -Href $href -HtmlPath $htmlFile.FullName
    if ($null -eq $resolved) { continue }
    $localLinkCount++
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
      $brokenLinks += [PSCustomObject]@{
        Source = $htmlFile.FullName.Substring($Target.Length).TrimStart('\', '/')
        Href = $href
      }
    }
  }
}
if ($brokenLinks.Count -gt 0) {
  $summary = @($brokenLinks | ForEach-Object { "$($_.Source) -> $($_.Href)" }) -join '; '
  throw "Broken local hyperlink(s) in public output: $summary"
}

# Require the sitemap to cover each primary indexable page/resource and require
# every listed URL to resolve to the fixed build output.
$sitemapPath = Join-Path $Target 'sitemap.xml'
[xml]$sitemapDocument = Get-Content -LiteralPath $sitemapPath -Raw -Encoding UTF8
$namespace = New-Object System.Xml.XmlNamespaceManager($sitemapDocument.NameTable)
$namespace.AddNamespace('sm', 'http://www.sitemaps.org/schemas/sitemap/0.9')
$sitemapLocs = @(
  $sitemapDocument.SelectNodes('//sm:url/sm:loc', $namespace) |
    ForEach-Object { ([string]$_.InnerText).Trim() }
)
$requiredSitemapPaths = @(
  '/',
  '/bom/',
  '/bom/data.json',
  '/llms.txt',
  '/build-guide/',
  '/build-guide/frame/',
  '/build-guide/software/',
  '/build-guide/validation/',
  '/blog/',
  '/blog/cad-harness-launch/',
  '/blog/m3-2-full-cad-release/',
  '/press/'
)
$sitemapPaths = @()
foreach ($loc in $sitemapLocs) {
  $uri = [System.Uri]$loc
  if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'bom.m3-crete.com') {
    throw "Sitemap URL must use the canonical HTTPS host"
  }
  $path = [System.Uri]::UnescapeDataString($uri.AbsolutePath)
  $sitemapPaths += $path
  $relative = $path.TrimStart('/') -replace '/', $Sep
  $resolved = if ([string]::IsNullOrWhiteSpace($relative)) { $Target } else { Join-Path $Target $relative }
  if ($path.EndsWith('/') -or (Test-Path -LiteralPath $resolved -PathType Container)) {
    $resolved = Join-Path $resolved 'index.html'
  }
  if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
    throw "Sitemap URL does not resolve in public output: $path"
  }
}
if (@($sitemapPaths | Sort-Object -Unique).Count -ne $sitemapPaths.Count) {
  throw "Sitemap contains duplicate URLs"
}
foreach ($requiredPath in $requiredSitemapPaths) {
  if ($sitemapPaths -notcontains $requiredPath) {
    throw "Sitemap is missing required public path: $requiredPath"
  }
}

# Derive BOM facts from the JSON source of truth and require every duplicated
# public summary to match the same snapshot. Counts intentionally include
# excluded/reference-only entries because that is what the JSON array contains.
$bomPath = Join-Path $Target "bom\data.json"
$bomRaw = Get-Content -LiteralPath $bomPath -Raw -Encoding UTF8
$bom = $bomRaw | ConvertFrom-Json
# pwsh 7 (CI) turns ISO strings into DateTime; take the date from the raw text.
$bomGeneratedMatch = [regex]::Match($bomRaw, '"generated"\s*:\s*"(\d{4}-\d{2}-\d{2})')
if (-not $bomGeneratedMatch.Success) { throw "BOM JSON has no ISO generated date" }
$bomGeneratedDate = $bomGeneratedMatch.Groups[1].Value
$parts = @($bom.parts)
$optionCount = @($parts | ForEach-Object { @($_.suppliers) }).Count
$namedSupplierCount = @(
  $parts |
    ForEach-Object { @($_.suppliers) } |
    ForEach-Object { $_.supplier_name } |
    Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
    Sort-Object -Unique
).Count
$categoryCount = @($parts | ForEach-Object { $_.category } | Sort-Object -Unique).Count
$partCount = $parts.Count
$bomVersion = [string]$bom.version

if ($partCount -lt 1 -or $optionCount -lt 1 -or $namedSupplierCount -lt 1 -or $categoryCount -lt 1) {
  throw "BOM fact derivation produced an empty count"
}

$bomPage = Get-Content -LiteralPath (Join-Path $Target "bom\index.html") -Raw -Encoding UTF8
$llms = Get-Content -LiteralPath (Join-Path $Target "llms.txt") -Raw -Encoding UTF8
$manifest = Get-Content -LiteralPath (Join-Path $Target ".well-known\mcp-manifest.json") -Raw -Encoding UTF8

$requiredBomSummaries = @(
  @{
    Name = "BOM metadata"
    Text = $bomPage
    Pattern = "BOM v$([regex]::Escape($bomVersion)) contains $partCount entries across $categoryCount categories and $optionCount supplier options"
  },
  @{
    Name = "BOM no-JS fallback"
    Text = $bomPage
    Pattern = "BOM v$([regex]::Escape($bomVersion)), generated $([regex]::Escape($bomGeneratedDate))"
  },
  @{
    Name = "LLM summary"
    Text = $llms
    Pattern = "$partCount parts, $optionCount options, $namedSupplierCount named suppliers"
  },
  @{
    Name = "Discovery manifest"
    Text = $manifest
    Pattern = "$partCount parts, $optionCount options, and $namedSupplierCount named suppliers"
  }
)

foreach ($summary in $requiredBomSummaries) {
  if ($summary.Text -notmatch $summary.Pattern) {
    throw "$($summary.Name) does not match derived BOM facts: version=$bomVersion parts=$partCount categories=$categoryCount options=$optionCount named_suppliers=$namedSupplierCount"
  }
}

# Exact known-regression markers are safer here than broad word bans: the
# surrounding disclaimers legitimately use words such as "validated" and
# "certified" in negative statements.
$blockedPublicMarkers = @(
  "trained on validated 3D-printed cementitious specimen data",
  "map directly onto Klipper extrusion settings",
  "fits, fully assembled, on a standard US pallet",
  "mechanically and electrically validated",
  "ready for first prints",
  "canonical open-source concrete 3D printer",
  "66 parts across 9 categories",
  "64 Parts",
  "62 parts, v2.5.0",
  "216 supplier options",
  "37 suppliers",
  "99 parts, 13.5 MB",
  "eliminates roughly 25%",
  "more energy-efficient, and more reliable machine",
  "Every part is off-the-shelf",
  "safe for use in training as well as production",
  "two ground-parcel boxes",
  "By using, building, or modifying this project, you agree to these terms"
)

$publicTextFiles = Get-ChildItem -LiteralPath $Target -Recurse -Force -File |
  Where-Object { @('.html', '.json', '.md', '.txt', '.xml', '.js') -contains $_.Extension.ToLowerInvariant() }
foreach ($marker in $blockedPublicMarkers) {
  $found = $publicTextFiles | Select-String -SimpleMatch -Pattern $marker -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Path -Unique
  if ($found) {
    throw "Blocked stale public claim marker '$marker' found in: $($found -join ', ')"
  }
}

$bomFallbackBlocked = @(
  "Adjustable Leveling Feet M16",
  "LED Work Lighting",
  "HEPA Air Filtration"
)
foreach ($marker in $bomFallbackBlocked) {
  if ($bomPage.Contains($marker)) {
    throw "Excluded/stale item remains in the BOM HTML fallback: $marker"
  }
}

$files = Get-ChildItem -LiteralPath $Target -Recurse -Force -File
$bytes = ($files | Measure-Object -Property Length -Sum).Sum
Write-Output "Cloudflare publish directory ready: $Target"
Write-Output "Files: $($files.Count)"
Write-Output "Bytes: $bytes"
Write-Output "JSON documents: $($jsonFiles.Count)"
Write-Output "JSON-LD documents: $jsonLdCount"
Write-Output "Local hyperlinks checked: $localLinkCount"
Write-Output "Sitemap URLs: $($sitemapLocs.Count)"
Write-Output "BOM facts: version=$bomVersion parts=$partCount categories=$categoryCount options=$optionCount named_suppliers=$namedSupplierCount"
