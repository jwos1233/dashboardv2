# Windows Task Scheduler Setup for Live Trader

## 🎯 Quick Setup

### Step 1: Run Setup Script

**Open PowerShell as Administrator:**
```powershell
cd C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy

# For dry run (testing)
.\setup_scheduler.ps1 -Time "14:35" -DryRun

# For live trading
.\setup_scheduler.ps1 -Time "14:35" -Port 4001
```

**Parameters:**
- `-Time` - When to run (24-hour format, e.g., "14:35" = 2:35 PM)
- `-Port` - IB Gateway port (4001=live, 4002=paper)
- `-DryRun` - If specified, runs in dry run mode (no actual trading)

---

## 📋 Manual Setup (Alternative)

### Option A: Task Scheduler GUI

1. **Open Task Scheduler:**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create Basic Task:**
   - Click "Create Basic Task" on right panel
   - Name: `LiveTrader_Live`
   - Description: `Automated trading execution`

3. **Trigger:**
   - When: `Daily`
   - Start: `Today at 14:35` (2:35 PM)
   - Recur every: `1 days`
   - Advanced → Check: `Monday, Tuesday, Wednesday, Thursday, Friday`

4. **Action:**
   - Action: `Start a program`
   - Program: `python` (or full path: `C:\Users\jake\AppData\Local\Programs\Python\Python313\python.exe`)
   - Arguments: `live_trader_simple.py --port 4001 --live`
   - Start in: `C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy`

5. **Settings:**
   - ✅ Allow task to be run on demand
   - ✅ Run task as soon as possible after scheduled start is missed
   - ✅ If task fails, restart every 1 minute
   - ❌ Stop task if it runs longer than 3 days

---

### Option B: Command Line (schtasks)

```powershell
# Navigate to directory
cd C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy

# Create scheduled task for live trading
schtasks /create /tn "LiveTrader_Live" /tr "python live_trader_simple.py --port 4001 --live" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:35 /sd 01/15/2024 /rl HIGHEST /f

# Create scheduled task for dry run (testing)
schtasks /create /tn "LiveTrader_DryRun" /tr "python live_trader_simple.py --port 4001" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:30 /sd 01/15/2024 /rl HIGHEST /f
```

**Parameters explained:**
- `/tn` - Task name
- `/tr` - Command to run
- `/sc` - Schedule type (weekly)
- `/d` - Days (Mon-Fri)
- `/st` - Start time (14:35 = 2:35 PM)
- `/sd` - Start date
- `/rl` - Run level (HIGHEST = administrator)
- `/f` - Force (overwrites existing task)

---

## 🔍 Manage Your Scheduled Tasks

### List all tasks:
```powershell
schtasks /query /fo LIST /tn "LiveTrader*"
```

### Test run immediately:
```powershell
schtasks /run /tn "LiveTrader_Live"
```

### View task details:
```powershell
Get-ScheduledTask -TaskName "LiveTrader_Live" | Get-ScheduledTaskInfo
```

### Disable task (without deleting):
```powershell
schtasks /change /tn "LiveTrader_Live" /disable
```

### Enable task:
```powershell
schtasks /change /tn "LiveTrader_Live" /enable
```

### Delete task:
```powershell
schtasks /delete /tn "LiveTrader_Live" /f
```

### View task history:
```powershell
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" | 
    Where-Object {$_.Message -like "*LiveTrader*"} | 
    Select-Object TimeCreated, Message -First 10
```

---

## ⏰ Recommended Schedule

### For US Stock Market:

**Market Hours:** 9:30 AM - 4:00 PM ET

**Recommended run times:**

1. **2:35 PM ET (14:35)** - Main execution ⭐
   - 1 hour 25 min before market close
   - Time to react to afternoon moves
   - Catches rebalancing signals
   
2. **9:00 AM ET (09:00)** - Morning check (optional)
   - Review overnight changes
   - Adjust positions if needed
   - Run with `--dry-run` to see what changed

3. **3:45 PM ET (15:45)** - Late day check (optional)
   - Final rebalancing opportunity
   - Close to market close

### Example: Multiple Daily Checks

```powershell
# Morning check (dry run)
schtasks /create /tn "LiveTrader_Morning" /tr "python live_trader_simple.py --port 4001" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:00 /rl HIGHEST /f

# Afternoon execution (live)
schtasks /create /tn "LiveTrader_Afternoon" /tr "python live_trader_simple.py --port 4001 --live" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:35 /rl HIGHEST /f
```

---

## 🛡️ Important Considerations

### Before Running Automatically:

1. **Test Manually First:**
   ```powershell
   python live_trader_simple.py --port 4001
   ```

2. **Verify IB Connection:**
   - IB Gateway must be running
   - Auto-login must be configured
   - API settings must be correct

3. **Check Logs Directory:**
   - Make sure script can write to working directory
   - Monitor `execution_log_*.txt` files

4. **Set Up Monitoring:**
   - Check Telegram notifications
   - Review `trade_history.csv` daily
   - Monitor `position_state.json`

---

## 🔧 Troubleshooting

### Task doesn't run?

1. **Check task history:**
   ```powershell
   Get-ScheduledTask -TaskName "LiveTrader_Live" | Get-ScheduledTaskInfo
   ```

2. **Verify task is enabled:**
   ```powershell
   Get-ScheduledTask -TaskName "LiveTrader_Live" | Select-Object State
   ```

3. **Check last run result:**
   ```powershell
   (Get-ScheduledTaskInfo -TaskName "LiveTrader_Live").LastTaskResult
   ```
   - `0` = Success
   - Non-zero = Error code

4. **Test manually:**
   ```powershell
   schtasks /run /tn "LiveTrader_Live"
   ```

### Computer was off/asleep at scheduled time?

✅ The script is configured with "Run task as soon as possible after scheduled start is missed"
- Task will run when computer wakes up
- Up to you if you want this behavior

### Python not found?

Use full Python path:
```powershell
# Find Python path
(Get-Command python).Source

# Example output: C:\Users\jake\AppData\Local\Programs\Python\Python313\python.exe
```

Then update task with full path:
```powershell
schtasks /create /tn "LiveTrader_Live" /tr "C:\Users\jake\AppData\Local\Programs\Python\Python313\python.exe C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy\live_trader_simple.py --port 4001 --live" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:35 /rl HIGHEST /f
```

---

## 📊 Monitor Your Automation

### Daily Checklist:

- [ ] Check execution logs: `execution_log_*.txt`
- [ ] Review trades: `trade_history.csv`
- [ ] Verify positions: `position_state.json`
- [ ] Check IB Gateway is running
- [ ] Confirm Telegram alerts received
- [ ] Review P&L in IB TWS

### Weekly Checklist:

- [ ] Archive old execution logs
- [ ] Review overall performance
- [ ] Check for any failed runs in Task Scheduler
- [ ] Verify stop losses are still active in IB

---

## 🎯 Example: Full Setup Command

```powershell
# Run as Administrator
cd C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy

# Create scheduled task for 2:35 PM Mon-Fri
schtasks /create `
    /tn "LiveTrader_Afternoon" `
    /tr "python live_trader_simple.py --port 4001 --live" `
    /sc weekly `
    /d MON,TUE,WED,THU,FRI `
    /st 14:35 `
    /rl HIGHEST `
    /f

# Verify it was created
schtasks /query /tn "LiveTrader_Afternoon" /fo LIST
```

---

## ⚠️ Safety Tips

1. **Always test with dry run first**
2. **Monitor for first few days**
3. **Keep IB Gateway running** (or set it to auto-start)
4. **Check logs daily**
5. **Set up Telegram for instant alerts**
6. **Review stop losses weekly**

---

## 🚀 Quick Start (Copy-Paste)

```powershell
# 1. Open PowerShell as Administrator
# 2. Navigate to your strategy folder
cd C:\Users\jake\Desktop\Coding\Macro_Quadrant_Strategy

# 3. Create the task (replace time as needed)
schtasks /create /tn "LiveTrader_Live" /tr "python live_trader_simple.py --port 4001 --live" /sc weekly /d MON,TUE,WED,THU,FRI /st 14:35 /rl HIGHEST /f

# 4. Test it works
schtasks /run /tn "LiveTrader_Live"

# 5. Check the logs
Get-Content execution_log_*.txt -Tail 50
```

**Done!** Your trader will now run automatically Mon-Fri at 2:35 PM. 🎉


