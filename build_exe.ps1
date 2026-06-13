# Build TradeBot.exe into this folder (project root)
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "tradebot\build_exe.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
