# Build TradeBot.exe - output lands in project root (../TradeBot.exe)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$projectRoot = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $projectRoot "TradeBot.exe"
$workDir = Join-Path $PSScriptRoot "build"
$buildStarted = Get-Date

$running = @(Get-Process -Name "TradeBot" -ErrorAction SilentlyContinue)
if ($running.Count -gt 0) {
    Write-Host "Stopping $($running.Count) running TradeBot process(es) so the exe can be replaced..."
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
}

Write-Host "Installing build dependencies..."
python -m pip install -q -r requirements-build.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "pip install failed (exit $LASTEXITCODE)"
}

Write-Host "Building single-file exe (this may take a few minutes)..."
python -m PyInstaller tradebot.spec --noconfirm --distpath $projectRoot --workpath $workDir
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller failed (exit $LASTEXITCODE). Close TradeBot.exe if it is still running."
}

if (-not (Test-Path $exe)) {
    Write-Error "Build failed - TradeBot.exe not found at $exe"
}

$built = Get-Item $exe
if ($built.LastWriteTime -lt $buildStarted) {
    Write-Error "Build did not update $exe (file timestamp is older than this build run)"
}

Write-Host ""
Write-Host "Done: $exe" -ForegroundColor Green
Write-Host ""
Write-Host "Before running:"
Write-Host "  1. Launch the exe from the project root (or copy it anywhere)"
Write-Host "  2. Enter API keys in the GUI, or edit tradebot_config.py beside the exe"
Write-Host "  3. Save settings and run bot actions"
