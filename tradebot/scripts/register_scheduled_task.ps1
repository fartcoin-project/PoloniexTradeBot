# Register a daily Windows Task Scheduler job for TradeBot (headless run at fixed time).
#
# Usage (from tradebot folder, as Administrator not required for per-user tasks):
#   .\scripts\register_scheduled_task.ps1
#   .\scripts\register_scheduled_task.ps1 -Time "18:00" -TaskName "TradeBot Daily 18:00"
#
# Prerequisites:
#   - tradebot_config.py with API keys
#   - config.json with budget, markets, exclude saved from the GUI (Save settings)
#   - Python on PATH, OR TradeBot.exe in the parent folder

param(
    [string]$Time = "18:00",
    [string]$TaskName = "TradeBot Daily",
    [string]$Action = "start_bot",
    [switch]$StartAfterMissed = $true,
    [ValidateSet("CurrentUser", "LocalSystem")]
    [string]$RunAs = "CurrentUser"
)

$ErrorActionPreference = "Stop"
$TradeBotDir = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Split-Path -Parent $TradeBotDir
$ExePath = Join-Path $ProjectRoot "TradeBot.exe"
$PythonScript = Join-Path $TradeBotDir "run_scheduled.py"

if (Test-Path $ExePath) {
    $Execute = $ExePath
    $Arguments = "--scheduled --action $Action"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Execute = (Get-Command python).Source
    $Arguments = "`"$PythonScript`" --action $Action"
} else {
    throw "Neither TradeBot.exe nor python found. Install Python or build the exe first."
}

$ActionObj = New-ScheduledTaskAction `
    -Execute $Execute `
    -Argument $Arguments `
    -WorkingDirectory $TradeBotDir

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable:$StartAfterMissed `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Principal = New-ScheduledTaskPrincipal -UserId $RunAs -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $ActionObj `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Force | Out-Null

Write-Host "Registered scheduled task '$TaskName' — daily at $Time"
Write-Host "  Command: $Execute $Arguments"
Write-Host "  Working directory: $TradeBotDir"
Write-Host ""
Write-Host "Test now:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "View log:  Get-Content (Join-Path '$TradeBotDir' 'logs\\tradebot.log') -Tail 40"
