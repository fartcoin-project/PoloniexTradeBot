# Build TradeBot onedir into project/dist/TradeBot/ (NEVER distpath=project root:
# on Windows TradeBot/ collides with tradebot/ and wipes sources).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$projectRoot = Split-Path $PSScriptRoot -Parent
$distRoot = Join-Path $projectRoot "dist"
$distDir = Join-Path $distRoot "TradeBot"
$exe = Join-Path $distDir "TradeBot.exe"
$internalDir = Join-Path $distDir "_internal"
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

Write-Host "Generating icon assets..."
python build_assets.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "build_assets.py failed (exit $LASTEXITCODE)"
}

Write-Host "Building onedir TradeBot (this may take a few minutes)..."
if (Test-Path $distDir) {
    Remove-Item -LiteralPath $distDir -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
python -m PyInstaller tradebot.spec --noconfirm --distpath $distRoot --workpath $workDir --clean
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller failed (exit $LASTEXITCODE). Close TradeBot.exe if it is still running."
}

if (-not (Test-Path $exe)) {
    Write-Error "Build failed - TradeBot.exe not found at $exe"
}
if (-not (Test-Path $internalDir)) {
    Write-Error "Build failed - onedir _internal folder missing at $internalDir"
}

$built = Get-Item $exe
if ($built.LastWriteTime -lt $buildStarted) {
    Write-Error "Build did not update $exe (file timestamp is older than this build run)"
}

Write-Host ""
Write-Host "Done: $distDir" -ForegroundColor Green
Write-Host ""
Write-Host "Before running:"
Write-Host "  1. Launch dist\TradeBot\TradeBot.exe (keep _internal beside it)"
Write-Host "  2. Enter API keys in the GUI"
Write-Host "  3. Save settings and run bot actions"
