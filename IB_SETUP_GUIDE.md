# 🚀 Interactive Brokers Setup Guide - Production v3.0

## Overview

This guide will help you connect your **Top 10 + ATR 2.0x strategy** to Interactive Brokers for live trading.

**Strategy Performance**: 420.83% over 5 years (43.96% annualized)

---

## ⚠️ CRITICAL: Start with Paper Trading!

**DO NOT go live immediately!**

1. Paper trade for **at least 1 month**
2. Verify signal generation accuracy
3. Test order execution
4. Monitor stop losses
5. Confirm costs align with backtest

---

## 📋 Prerequisites

### 1. Interactive Brokers Account

**You need:**
- ✅ Active IB account (Paper or Live)
- ✅ Approved for margin trading (we use 2.0-2.5x leverage)
- ✅ Sufficient capital ($10k minimum, $50k+ recommended)
- ✅ API access enabled

**Account Types:**
- **Paper Account**: For testing (highly recommended first step)
- **Live Account**: For real trading (only after paper trading success)

### 2. Python Environment

```bash
# Check Python version (need 3.8+)
python --version

# Install dependencies
cd Macro_Quadrant_Strategy
pip install -r requirements.txt
```

**Required packages:**
- `ib_insync` - IB API wrapper
- `yfinance` - Market data
- `pandas`, `numpy` - Data processing
- `matplotlib` - Charting

---

## 🔧 Part 1: IB Gateway Setup (Recommended)

**Why IB Gateway?**
- Lightweight (no GUI overhead)
- Designed for automated trading
- More stable for API connections
- Runs in background

### Step 1: Download IB Gateway

1. Go to: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
2. Download for your OS (Windows/Mac/Linux)
3. Install IB Gateway

### Step 2: Launch IB Gateway

```
Windows: Start Menu → IB Gateway
Mac: Applications → IB Gateway
```

### Step 3: Login

**For Paper Trading:**
- Username: Your paper trading username (usually `edemo` or similar)
- Password: Your paper password
- **Mode**: Paper Trading

**For Live Trading:**
- Username: Your live username
- Password: Your live password
- **Mode**: Live Trading

### Step 4: Configure API Settings

After logging in, IB Gateway will show a small window.

**Click: Configure → Settings → API → Settings**

**Required Settings:**
```
☑ Enable ActiveX and Socket Clients
☑ Allow connections from localhost only
Socket port: 4002 (paper) or 4001 (live)
Master API client ID: [leave blank]
☐ Read-Only API [UNCHECK THIS]
Trusted IP addresses: 127.0.0.1
```

**Click "OK" and restart IB Gateway**

---

## 🖥️ Part 2: Alternative - TWS Setup

If you prefer the full Trader Workstation instead of Gateway:

### Step 1: Launch TWS

1. Open Trader Workstation
2. Login (paper or live)

### Step 2: API Settings

```
File → Global Configuration → API → Settings
```

**Configure:**
```
☑ Enable ActiveX and Socket Clients
Socket port: 7497 (paper) or 7496 (live)
Trusted IPs: 127.0.0.1
☐ Read-Only API [UNCHECK]
```

**Restart TWS after saving**

---

## 🧪 Part 3: Test the Connection

### Test 1: Basic Connection

Create a test file: `test_ib_connection.py`

```python
from ib_insync import IB

# Connect to IB
ib = IB()

# Paper trading port
ib.connect('127.0.0.1', 4002, clientId=1)

# Check connection
if ib.isConnected():
    print("✅ Connected to IB successfully!")
    print(f"Account: {ib.managedAccounts()}")
    
    # Get account value
    account_values = ib.accountValues()
    for v in account_values:
        if v.tag == 'NetLiquidation':
            print(f"Account Value: ${float(v.value):,.2f}")
    
    ib.disconnect()
else:
    print("❌ Connection failed!")
```

**Run it:**
```bash
python test_ib_connection.py
```

**Expected output:**
```
✅ Connected to IB successfully!
Account: ['DU12345']
Account Value: $1,000,000.00
```

### Test 2: Market Data

```python
from ib_insync import IB, Stock

ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# Test fetching QQQ price
qqq = Stock('QQQ', 'SMART', 'USD')
ib.qualifyContracts(qqq)

ticker = ib.reqMktData(qqq)
ib.sleep(2)

print(f"QQQ Price: ${ticker.last}")

ib.disconnect()
```

---

## 📊 Part 4: Generate Today's Signals

### Step 1: Run Signal Generator

```bash
python signal_generator.py
```

**Expected Output:**
```
============================================================
GENERATING SIGNALS
============================================================
✓ Loaded 33 tickers, 151 days

Quadrant Scores:
  Q1:  +15.43%
  Q3:  +10.21%
  Q2:   +3.34%
  Q4:   -2.67%

🎯 Top 2 Quadrants: Q1, Q3

📊 Target Portfolio (Top 10 Positions):
  Total leverage: 2.50x
  Number of positions: 10

  ALL POSITIONS (sorted by weight):
  Ticker   Weight     Notional ($10k) Quadrant
  -------- ---------- --------------- ----------
  ARKK        28.50%  $    2,850.00  Q1
  QQQ         22.30%  $    2,230.00  Q1
  REMX        18.40%  $    1,840.00  Q3
  ...
```

**Save the output! You'll use these weights for trading.**

### Step 2: Review Signals

**Check:**
- ✅ Are the quadrants reasonable for current market?
- ✅ Are the assets above their 50-day EMAs?
- ✅ Do the weights sum to ~2.0-2.5x?
- ✅ Are there 10 or fewer positions?

---

## 🎯 Part 5: Test with Dry Run (No Real Orders)

### Run Live Trader in Dry Run Mode

```bash
python live_trader.py --mode once --dry-run
```

**What this does:**
1. Generates signals
2. Connects to IB (to check account)
3. **DOES NOT place orders** (dry run)
4. Shows you what it WOULD trade

**Expected Output:**
```
[DRY RUN MODE]
Account: DU12345
Current Value: $50,000.00

Current Positions: 0
Target Positions: 10

Would execute trades:
  BUY ARKK: 200 shares @ $42.50 = $8,500
  BUY QQQ: 55 shares @ $405.00 = $22,275
  ...

Total notional: $125,000 (2.50x leverage)

[DRY RUN - No orders placed]
```

---

## 🚀 Part 6: Paper Trading (Real Orders, Fake Money)

### Step 1: Verify Settings

**Double-check:**
- ✅ IB Gateway is logged into **PAPER ACCOUNT**
- ✅ Port is **4002** (paper)
- ✅ You have sufficient paper capital ($50k+)

### Step 2: Run Live Trader (Paper)

```bash
python live_trader.py --mode once --live --port 4002
```

**What happens:**
1. Generates signals
2. Connects to IB paper account
3. **Places REAL orders** (in paper account)
4. Monitors positions
5. Sets stop losses

### Step 3: Monitor Execution

**Check in TWS or Gateway:**
- Orders placed?
- Orders filled?
- Positions show up?
- Stop losses set?

### Step 4: Daily Monitoring

**For the next 30 days:**
1. Run signal generator daily
2. Check for regime changes
3. Monitor stop losses
4. Track performance
5. Compare to backtest expectations

---

## ⚠️ Part 7: Important Considerations

### 1. Margin Requirements

**Your strategy uses 2.0-2.5x leverage:**
```
$50k account → $100k-$125k exposure
$100k account → $200k-$250k exposure
```

**IB margin requirements:**
- Reg T margin: 50% (can use 2x leverage)
- Portfolio margin: Higher leverage (need $110k+ account)

**Make sure you have:**
- Margin approval
- Sufficient buying power
- Buffer for drawdowns

### 2. Stop Loss Execution

**ATR 2.0x stops are CRITICAL:**
- Strategy relies on them for risk management
- Must be set immediately after entry
- Use **stop-market orders** (not stop-limit)

**IB Implementation:**
```python
# After buying ARKK at $50
stop_price = 50 - (2.0 * atr)  # e.g., $45
order = Order()
order.action = "SELL"
order.orderType = "STP"
order.auxPrice = stop_price
order.totalQuantity = shares
```

### 3. CFD vs ETF Trading

**Challenge:** IB doesn't offer CFDs on all ETFs

**Options:**
1. **Trade ETFs directly** (if available in your region)
2. **Use futures** (ES, NQ, RTY instead of SPY, QQQ, IWM)
3. **Modify asset list** to only IB-supported instruments

**Common CFD Mappings:**
```
SPY  → US500 CFD (S&P 500)
QQQ  → USTEC CFD (NASDAQ-100)
IWM  → US2000 CFD (Russell 2000)
GLD  → GOLD CFD
TLT  → US30YR CFD (30-year bonds)
```

### 4. Trading Costs

**IB Commission Structure:**
- **US Stocks/ETFs**: $0.005/share (min $1, max 0.5% of trade)
- **CFDs**: Varies by instrument (0.01-0.02% typical)

**Backtest used 0.10% per trade**
- IB actual costs: ~0.01-0.02%
- **Real costs are LOWER than backtest!**
- More profit potential in live trading

### 5. Overnight Financing (CFDs)

**If using CFDs:**
- Charged/paid daily interest
- Long positions: Usually pay interest (~2-5% annually)
- Short positions: Receive interest
- Already factored into strategy (we're usually long)

### 6. Rebalancing Frequency

**Strategy rebalances ~93% of days:**
- This is event-driven (not calendar-based)
- Rebalance when:
  - Quadrants change
  - EMA crossover
  - Stop loss hit
  - Top 10 list changes

**In practice:**
- Some days: No changes (hold positions)
- Some days: 1-2 small adjustments
- Some days: Full rebalance (regime shift)

---

## 📅 Part 8: Daily Workflow

### Morning Routine (Before Market Open)

**1. Generate Signals (15 min before open)**
```bash
python signal_generator.py
```

**2. Review Output**
- Check top quadrants
- Review target positions
- Note any new entries/exits
- Verify stop prices

**3. Check IB Connection**
- Gateway running?
- Logged in?
- API connected?

### At Market Open

**4. Execute Trades**
```bash
python live_trader.py --mode once --live --port 4002
```

**5. Verify Execution**
- Check TWS for fills
- Verify positions match targets
- Confirm stop orders placed

### During Market Hours

**6. Monitor Stops**
- Check if any stops hit
- System should auto-exit, but verify
- Re-run live_trader if stop hit

### After Market Close

**7. Review Performance**
- Daily P&L
- Compare to backtest expectations
- Note any issues

**8. Update Logs**
- Keep track of trades
- Document any manual interventions
- Note market conditions

---

## 🔍 Part 9: Troubleshooting

### Connection Issues

**Problem**: Can't connect to IB
```python
Error: Connection refused
```

**Solutions:**
1. Check IB Gateway is running
2. Verify port number (4002 for paper, 4001 for live)
3. Check API settings enabled
4. Try restarting Gateway
5. Check firewall settings

### Order Rejection

**Problem**: Orders rejected by IB
```
Order rejected: Insufficient funds
```

**Solutions:**
1. Check margin requirements
2. Reduce position sizes
3. Check buying power
4. Verify account approved for margin

### Stop Loss Not Working

**Problem**: Stop loss didn't execute

**Solutions:**
1. Use STP (stop-market), not STP LMT (stop-limit)
2. Check stop price is reasonable
3. Verify order was transmitted
4. Check for gaps (stops might not fill in gaps)

### Signal Discrepancies

**Problem**: Live signals differ from backtest

**Expected!** The strategy is dynamic:
- Uses latest 50 days of data
- Market conditions change
- Normal variation

**Action:**
- Compare overall pattern (not exact positions)
- Track over weeks, not days
- If consistently wrong, review data source

---

## ✅ Part 10: Go-Live Checklist

**Before switching to live account:**

- [ ] Paper traded for 30+ days
- [ ] Understand all strategy mechanics
- [ ] Verified signal generation accuracy
- [ ] Tested order execution
- [ ] Monitored stop losses working
- [ ] Comfortable with leverage (2.0-2.5x)
- [ ] Have adequate capital ($50k+)
- [ ] Understand margin requirements
- [ ] Know how to handle issues
- [ ] Have emergency stop procedure
- [ ] Reviewed all documentation

**When ready for live:**

1. Change port from `4002` to `4001`
2. Login to live account in Gateway
3. **Start with 10-20% of intended capital**
4. Scale up over time as confidence grows
5. Monitor closely for first month

---

## 📚 Additional Resources

**Documentation:**
- `STRATEGY_EXPLAINED.md` - Complete strategy breakdown
- `README.md` - Strategy overview
- `PRODUCTION_SUMMARY.md` - Quick reference

**Support:**
- IB API docs: https://interactivebrokers.github.io/tws-api/
- ib_insync docs: https://ib-insync.readthedocs.io/

---

## ⚠️ Final Warnings

1. **Start small** - Don't deploy full capital immediately
2. **Monitor closely** - Especially first month
3. **Expect deviations** - Live won't match backtest exactly
4. **Have emergency plan** - Know how to manually exit all positions
5. **Use stops** - They're critical to the strategy
6. **Be patient** - Strategy works over months/years, not days
7. **Accept drawdowns** - Max historical: -22.62%
8. **Not financial advice** - You're responsible for your trading

---

## 🎯 Quick Start Commands

**Generate signals:**
```bash
python signal_generator.py
```

**Test connection (dry run):**
```bash
python live_trader.py --mode once --dry-run
```

**Paper trading:**
```bash
python live_trader.py --mode once --live --port 4002
```

**Live trading (when ready):**
```bash
python live_trader.py --mode once --live --port 4001
```

---

**Good luck with your live trading! Start with paper, be patient, and follow the process.** 🚀

