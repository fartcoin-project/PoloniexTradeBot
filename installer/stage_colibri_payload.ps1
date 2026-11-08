# Stage Colibri runtime + portable CPython into installer/payload for Inno Setup.
# Models are NOT staged (downloaded at runtime via HF_TOKEN).
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$payloadRoot = Join-Path $PSScriptRoot "payload"
$colibriOut = Join-Path $payloadRoot "colibri"
$pythonOut = Join-Path $payloadRoot "python"
$cacheDir = Join-Path $payloadRoot ".cache"

$colibriSrcCandidates = @(
    (Join-Path (Split-Path -Parent $projectRoot) "colibri"),
    (Join-Path $projectRoot "colibri"),
    "C:\workspace\projects\colibri"
)
$colibriSrc = $null
foreach ($c in $colibriSrcCandidates) {
    if (Test-Path (Join-Path $c "c\coli")) {
        $colibriSrc = $c
        break
    }
}
if (-not $colibriSrc) {
    Write-Error "Colibri source not found (expected sibling repo with c\coli)."
}

Write-Host "Staging Colibri from $colibriSrc ..."
New-Item -ItemType Directory -Force -Path $payloadRoot | Out-Null
if (Test-Path $colibriOut) {
    Remove-Item -Recurse -Force $colibriOut
}
New-Item -ItemType Directory -Force -Path $colibriOut | Out-Null

# Copy launcher package + START-HERE
Copy-Item -Recurse -Force (Join-Path $colibriSrc "colibri") (Join-Path $colibriOut "colibri")
Copy-Item -Force (Join-Path $colibriSrc "START-HERE.bat") (Join-Path $colibriOut "START-HERE.bat")

# Copy c/ excluding tests and large tiny/fixture trees
$cSrc = Join-Path $colibriSrc "c"
$cDst = Join-Path $colibriOut "c"
New-Item -ItemType Directory -Force -Path $cDst | Out-Null
$excludeDirNames = @(
    "tests", ".git", "__pycache__", "laya_tiny", "qwen36_tiny_bad", "kimi_k3_tiny",
    "node_modules", "web"
)
Get-ChildItem -Path $cSrc -Force | ForEach-Object {
    if ($_.PSIsContainer -and ($excludeDirNames -contains $_.Name)) {
        return
    }
    $dest = Join-Path $cDst $_.Name
    if ($_.PSIsContainer) {
        # Skip nested tests/__pycache__ via robocopy
        & robocopy $_.FullName $dest /E /NFL /NDL /NJH /NJS /nc /ns /np `
            /XD tests __pycache__ .git node_modules | Out-Null
        if ($LASTEXITCODE -ge 8) {
            Write-Error "robocopy failed for $($_.Name) (exit $LASTEXITCODE)"
        }
    } else {
        Copy-Item -Force $_.FullName $dest
    }
}

# Portable embeddable CPython 3.12
$pyVer = "3.12.8"
$pyZipName = "python-$pyVer-embed-amd64.zip"
$pyUrl = "https://www.python.org/ftp/python/$pyVer/$pyZipName"
New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
$pyZip = Join-Path $cacheDir $pyZipName
if (-not (Test-Path $pyZip)) {
    Write-Host "Downloading $pyZipName ..."
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyZip -UseBasicParsing
}
if (Test-Path $pythonOut) {
    Remove-Item -Recurse -Force $pythonOut
}
New-Item -ItemType Directory -Force -Path $pythonOut | Out-Null
Expand-Archive -Path $pyZip -DestinationPath $pythonOut -Force

# Enable site-packages in embeddable distro
$pth = Get-ChildItem -Path $pythonOut -Filter "python*._pth" | Select-Object -First 1
if ($pth) {
    $lines = Get-Content $pth.FullName
    $newLines = @()
    foreach ($line in $lines) {
        if ($line -match '^\s*#\s*import site\s*$') {
            $newLines += "import site"
        } elseif ($line -match '^\s*import site\s*$') {
            $newLines += "import site"
        } else {
            $newLines += $line
        }
    }
    if ($newLines -notcontains "import site") {
        $newLines += "import site"
    }
    if ($newLines -notcontains "Lib\site-packages") {
        $newLines = @("Lib\site-packages") + $newLines
    }
    Set-Content -Path $pth.FullName -Value $newLines -Encoding ASCII
}
$site = Join-Path $pythonOut "Lib\site-packages"
New-Item -ItemType Directory -Force -Path $site | Out-Null

# Bootstrap pip (optional; coli setup is mostly stdlib)
$getPip = Join-Path $cacheDir "get-pip.py"
if (-not (Test-Path $getPip)) {
    Write-Host "Downloading get-pip.py ..."
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
}
$pyExe = Join-Path $pythonOut "python.exe"
& $pyExe $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) {
    Write-Warning "get-pip failed (exit $LASTEXITCODE) — continuing; coli setup uses stdlib"
}

# Marker for installer / manager
@"
colibri_src=$colibriSrc
python=$pyVer
staged=$(Get-Date -Format o)
"@ | Set-Content -Path (Join-Path $payloadRoot "PAYLOAD.txt") -Encoding UTF8

Write-Host "Payload ready:"
Write-Host "  $colibriOut"
Write-Host "  $pythonOut"
