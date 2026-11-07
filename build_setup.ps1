# Build self-contained setup-v0.1.0.exe into the project root.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$projectRoot = $PSScriptRoot
$tradebotDir = Join-Path $projectRoot "tradebot"
$exe = Join-Path $projectRoot "TradeBot.exe"
$setup = Join-Path $projectRoot "setup-v0.1.0.exe"
$iss = Join-Path $projectRoot "installer\TradeBot.iss"
$workDir = Join-Path $tradebotDir "build"
$buildStarted = Get-Date

function Find-Iscc {
    $candidates = New-Object System.Collections.Generic.List[string]
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) {
        [void]$candidates.Add([string]$cmd.Source)
    }
    foreach ($path in @(
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
        )) {
        if ($path) {
            [void]$candidates.Add($path)
        }
    }
    foreach ($path in $candidates) {
        if ($path -and $path -like "*ISCC.exe" -and (Test-Path -LiteralPath $path)) {
            return $path
        }
    }
    return $null
}

function Install-InnoSetup {
    Write-Host "Inno Setup 6 not found — downloading silent installer..."
    $url = "https://jrsoftware.org/download.php/is.exe"
    $installer = Join-Path $env:TEMP "innosetup-silent.exe"
    Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
    $args = "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
    $proc = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Write-Error "Inno Setup silent install failed (exit $($proc.ExitCode))"
    }
    $iscc = Find-Iscc
    if (-not $iscc) {
        Write-Error "Inno Setup installed but ISCC.exe was not found"
    }
    return $iscc
}

$running = @(Get-Process -Name "TradeBot" -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    Write-Host "Stopping $($running.Count) running TradeBot process(es) so the exe can be replaced..."
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
}

Write-Host "Installing build dependencies..."
Push-Location $tradebotDir
try {
    python -m pip install -q -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "pip install failed (exit $LASTEXITCODE)"
    }

    Write-Host "Generating installer assets from icon.png / art.png..."
    python build_assets.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error "build_assets.py failed (exit $LASTEXITCODE)"
    }

    Write-Host "Building single-file TradeBot.exe (this may take a few minutes)..."
    python -m PyInstaller tradebot.spec --noconfirm --distpath $projectRoot --workpath $workDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller failed (exit $LASTEXITCODE). Close TradeBot.exe if it is still running."
    }
}
finally {
    Pop-Location
}

if (-not (Test-Path $exe)) {
    Write-Error "Build failed - TradeBot.exe not found at $exe"
}

$built = Get-Item $exe
if ($built.LastWriteTime -lt $buildStarted) {
    Write-Error "Build did not update $exe (file timestamp is older than this build run)"
}

$iscc = Find-Iscc
if (-not $iscc) {
    $iscc = Install-InnoSetup
}

Write-Host "Compiling setup with Inno Setup ($iscc)..."
& $iscc $iss
if ($LASTEXITCODE -ne 0) {
    Write-Error "ISCC failed (exit $LASTEXITCODE)"
}

if (-not (Test-Path $setup)) {
    Write-Error "Setup build failed - $setup not found"
}

Write-Host ""
Write-Host "Done: $setup" -ForegroundColor Green
Write-Host "Also built: $exe"
Write-Host ""
Write-Host "Installs to: %LOCALAPPDATA%\Programs\TradeBot"
Write-Host "Data folder: %LOCALAPPDATA%\TradeBot"
