@echo off
REM Live Trading Launcher - Macro Quadrant Strategy
REM ==================================================

cd /d "%~dp0"

echo ========================================
echo Macro Quadrant Strategy - LIVE TRADING
echo ========================================
echo.
echo Port: 7496 (TWS Live)
echo Mode: LIVE EXECUTION
echo.
echo WARNING: This will execute REAL trades!
echo.
pause

echo.
echo Starting live trader...
echo.

python live_trader_simple.py --port 7496 --live

echo.
echo ========================================
echo Execution complete!
echo ========================================
echo.
pause



