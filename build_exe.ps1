# Build TradeBot onedir into this folder (project root\TradeBot\)
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "tradebot\build_exe.ps1")
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
