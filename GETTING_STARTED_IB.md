# 🎯 Getting Started with Interactive Brokers - Quick Guide

## Your Strategy at a Glance

**Performance**: 420.83% return over 5 years (43.96% annualized, 1.41 Sharpe)

---

## 5-Minute Setup (Paper Trading)

### Step 1: Install IB Gateway

**Download**: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

**Why Gateway?** Lightweight, designed for APIs, more stable than TWS

### Step 2: Configure IB Gateway

1. Launch IB Gateway
2. Login to **Paper Account**
3. Click: **Configure → Settings → API**
4. Enable: ☑ **ActiveX and Socket Clients**
5. Port: **4002** (paper)
6. Trusted IPs: **127.0.0.1**
7. **Uncheck**: ☐ Read-Only API
8. Click OK, restart Gateway

### Step 3: Test Connection

```bash
cd Macro_Quadrant_Strategy
python test_ib_connection.py
```

**Expected output:**
```
✅ Connected successfully!
Accounts: ['DU12345']
NetLiquidation: $1,000,000.00
✅ Market data working!
✅ ALL TESTS PASSED!
```

### Step 4: Generate Your First Signals

```bash
python signal_generator.py
```

**You'll see:**
- Current quadrant regime (Q1-Q4)
- Top 10 positions with weights
- Notional values

### Step 5: Dry Run (No Real Orders)

```bash
python live_trader.py --mode once --dry-run
```

**This:**
- Generates signals
- Connects to IB
- Shows what it WOULD trade
- **Does NOT place orders**

### Step 6: Paper Trade (Real Orders, Fake Money)

```bash
python live_trader.py --mode once --live --port 4002
```

**This:**
- Places REAL orders in paper account
- Sets stop losses
- Monitors positions

---

## What You Need

### Interactive Brokers Account

- ✅ Paper account (for testing)
- ✅ OR Live account (only after paper trading success)
- ✅ Margin approval (strategy uses 2.0-2.5x leverage)
- ✅ Adequate capital ($50k+ recommended)

### System Requirements

- ✅ Python 3.8+
- ✅ Windows/Mac/Linux
- ✅ Stable internet connection
- ✅ Dependencies installed (`pip install -r requirements.txt`)

---

## Daily Workflow (Once Live)

### Morning (15 min before market open)

```bash
# 1. Generate signals
python signal_generator.py

# 2. Review output (check quadrants, positions)

# 3. Execute trades
python live_trader.py --mode once --live --port 4002
```

### During Market

- Monitor for stop losses
- System handles automatically
- Re-run if stop hit

### After Market

- Review daily P&L
- Compare to backtest expectations
- Update trading log

---

## Key Strategy Features

### What It Does

1. **Analyzes 33 ETFs** daily
2. **Identifies top 2 economic quadrants** (Q1-Q4)
3. **Selects top 10 positions** by weight
4. **Sets ATR 2.0x stop losses** on every position
5. **Rebalances** when signals change

### Risk Management

- **ATR Stops**: Exit at entry - (2.0 × 14-day ATR)
- **EMA Filter**: Only hold uptrends (price > 50-day EMA)
- **Position Limit**: Max 10 positions
- **Leverage**: 2.0-2.5x total
- **Max Drawdown**: -22.62% (historical)

### Expected Performance

**Based on 5-year backtest:**
- Total Return: 420.83%
- Annualized: 43.96%
- Sharpe Ratio: 1.41
- Win Rate: ~54%
- Stops Hit: ~5-6 per month

---

## Important Notes

### ⚠️ Start with Paper Trading

**Do NOT go live immediately!**

1. Paper trade for 30+ days
2. Verify signal accuracy
3. Test execution
4. Monitor stops
5. Build confidence

### 💰 Leverage & Margin

**Strategy uses 2.0-2.5x leverage:**
```
$50k account → $100k-$125k exposure
```

**Requirements:**
- Margin approval from IB
- Sufficient buying power
- Buffer for drawdowns

### 🛑 Stop Losses are CRITICAL

**327 stops hit over 5 years:**
- Protected capital in bear markets
- 2022: +1.07% vs -10.92% without stops
- Must be set on every position
- Use stop-market orders (not stop-limit)

### 📊 CFD vs ETF Trading

**IB doesn't offer CFDs on all ETFs**

**Options:**
1. Trade ETFs directly (if available)
2. Use futures (ES, NQ, RTY)
3. Modify asset list

**Common mappings:**
- SPY → US500 CFD
- QQQ → USTEC CFD
- IWM → US2000 CFD
- GLD → GOLD CFD

### 💵 Trading Costs

**IB actual costs: ~0.01-0.02% per trade**
**Backtest used: 0.10% per trade**

**Real costs are LOWER than backtest!**

---

## Troubleshooting

### Can't Connect to IB

1. IB Gateway running?
2. Logged in?
3. API enabled?
4. Port correct (4002 for paper)?
5. Try restarting Gateway

### Orders Rejected

1. Check margin requirements
2. Reduce position sizes
3. Verify buying power
4. Check account approvals

### Signals Look Wrong

**This is normal!**
- Strategy is dynamic
- Uses latest 50 days
- Market conditions change
- Compare over weeks, not days

---

## Quick Command Reference

```bash
# Test IB connection
python test_ib_connection.py

# Generate signals
python signal_generator.py

# Dry run (no orders)
python live_trader.py --mode once --dry-run

# Paper trading
python live_trader.py --mode once --live --port 4002

# Live trading (when ready)
python live_trader.py --mode once --live --port 4001

# Run backtest
python run_production_backtest.py
```

---

## Next Steps

1. ✅ **Read**: `IB_SETUP_GUIDE.md` (detailed setup)
2. ✅ **Read**: `STRATEGY_EXPLAINED.md` (how it works)
3. ✅ **Install**: IB Gateway
4. ✅ **Test**: Connection (`test_ib_connection.py`)
5. ✅ **Generate**: Signals (`signal_generator.py`)
6. ✅ **Paper trade**: 30+ days
7. ⚠️ **Go live**: Only after success in paper

---

## Support Documents

- `IB_SETUP_GUIDE.md` - Complete IB setup (detailed)
- `STRATEGY_EXPLAINED.md` - Strategy mechanics (entry/exit rules)
- `README.md` - Strategy overview
- `PRODUCTION_SUMMARY.md` - Quick reference

---

## ⚠️ Disclaimer

**NOT FINANCIAL ADVICE**

- You are responsible for your trading
- Past performance ≠ future results
- Leverage amplifies gains AND losses
- Start small, scale gradually
- Paper trade first!
- Consult a financial advisor

---

**Ready to start? Run `python test_ib_connection.py` to verify your setup!** 🚀



