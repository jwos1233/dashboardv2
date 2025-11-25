# Setup Task Scheduler for Live Trader
# Run this script as Administrator

param(
    [string]$Time = "14:35",  # Default: 2:35 PM (before market close)
    [int]$Port = 4001,        # IB Gateway port
    [switch]$DryRun = $false  # Set to $true for testing
)

$ScriptPath = "$PSScriptRoot\live_trader_simple.py"
$PythonPath = (Get-Command python).Source
$WorkingDir = $PSScriptRoot

# Build the command
if ($DryRun) {
    $Arguments = "$ScriptPath --port $Port"
    $TaskName = "LiveTrader_DryRun"
} else {
    $Arguments = "$ScriptPath --port $Port --live"
    $TaskName = "LiveTrader_Live"
}

Write-Host "Creating scheduled task: $TaskName" -ForegroundColor Green
Write-Host "  Time: $Time (Mon-Fri)" -ForegroundColor Cyan
Write-Host "  Command: python $Arguments" -ForegroundColor Cyan
Write-Host "  Working Directory: $WorkingDir" -ForegroundColor Cyan

# Create the scheduled task
$Action = New-ScheduledTaskAction -Execute $PythonPath `
    -Argument $Arguments `
    -WorkingDirectory $WorkingDir

$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At $Time

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Force
    
    Write-Host "`n✅ Task created successfully!" -ForegroundColor Green
    Write-Host "`nTask will run:" -ForegroundColor Yellow
    Write-Host "  - Every weekday (Mon-Fri) at $Time" -ForegroundColor White
    Write-Host "  - Even if computer was off at scheduled time" -ForegroundColor White
    Write-Host "`nTo view: Open Task Scheduler and look for '$TaskName'" -ForegroundColor Cyan
    Write-Host "To test: schtasks /run /tn `"$TaskName`"" -ForegroundColor Cyan
    Write-Host "To delete: schtasks /delete /tn `"$TaskName`" /f" -ForegroundColor Cyan
    
} catch {
    Write-Host "`n❌ Error creating task: $_" -ForegroundColor Red
    Write-Host "`nTry running PowerShell as Administrator" -ForegroundColor Yellow
}




