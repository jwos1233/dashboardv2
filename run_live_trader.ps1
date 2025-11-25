# Live Trading Launcher - Macro Quadrant Strategy
# ==================================================

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Macro Quadrant Strategy - LIVE TRADING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Port: 7496 (TWS Live)" -ForegroundColor Yellow
Write-Host "Mode: LIVE EXECUTION" -ForegroundColor Yellow
Write-Host ""
Write-Host "WARNING: This will execute REAL trades!" -ForegroundColor Red
Write-Host ""
Read-Host "Press Enter to continue or Ctrl+C to cancel"

Write-Host ""
Write-Host "Starting live trader..." -ForegroundColor Green
Write-Host ""

python live_trader_simple.py --port 7496 --live

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Execution complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"



