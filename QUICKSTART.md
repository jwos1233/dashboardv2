# Quick Start Guide - Live Trading (Top 10 Production Version)

## 📁 Clean Folder Structure

```
Macro_Quadrant_Strategy/
├── signal_generator.py         # ✅ Generate Top 10 signals
├── ib_executor.py              # ✅ Execute trades via IB API with CFDs
├── live_trader.py              # ✅ Main orchestrator
├── config.py                   # ✅ Asset allocations
├── quad_portfolio_backtest.py  # Reference backtest (not needed for live)
├── requirements.txt            # ✅ Dependencies
├── README.md                   # Top 10 strategy documentation
├── README_LIVE_TRADING.md      # ✅ Full live trading guide
└── QUICKSTART.md               # This file
```

**Production Strategy: TOP 10 POSITIONS**
- Analyzes all 33 ETFs daily
- Trades only the top 10 by weight
- 192.49% backtest return (5 years)
- 29.38% annualized | 0.91 Sharpe

---

## 🚀 3-Step Setup

### Step 1: Install Dependencies

```bash
cd Macro_Quadrant_Strategy
pip install -r requirements.txt
```

### Step 2: Set Up Interactive Brokers

**IB Gateway (Recommended):**
1. Download from https://www.interactivebrokers.com
2. Launch and log in
3. Enable API (Socket Clients)
4. Paper trading port: **4002**
5. Live trading port: **4001**

**Required IB Settings:**
- ✅ Enable ActiveX and Socket Clients
- ✅ Add 127.0.0.1 to Trusted IPs  
- ✅ Uncheck "Read-Only API"
- ✅ Enable CFD trading in account

### Step 3: Test Run

```bash
# Test signal generation (no trading)
python signal_generator.py

# Test IB connection (make sure IB Gateway is running!)
python ib_executor.py

# Run full system (dry run)
python live_trader.py --mode once
```

---

## 💼 Key Commands

### Generate Signals Only
```bash
python signal_generator.py
```
**Output:** Displays quadrant scores and target weights

### Test IB Connection
```bash
python ib_executor.py
```
**Output:** Shows account value and current positions

### Run Once (Dry Run)
```bash
python live_trader.py --mode once
```
**Output:** Generates signals, shows what would be traded

### Run Once (LIVE - Paper Trading)
```bash
python live_trader.py --mode once --live --port 4002
```
**Output:** Executes actual trades on IB paper account

### Run Daily Scheduled (Paper)
```bash
python live_trader.py --mode scheduled --time 16:00 --port 4002 --live
```
**Output:** Runs every day at 4 PM EST

---

## 📊 Understanding the Output

### Signal Generator Output

```
GENERATING SIGNALS
==========================================
✓ Loaded 33 tickers, 150 days

Quadrant Scores:
  Q1:  +15.43%  ← Best performing
  Q2:   +8.21%  ← Second best  
  Q3:   -2.34%
  Q4:   -5.67%

🎯 Top 2 Quadrants: Q1, Q2

📊 Target Portfolio (Top 10 Positions):
  Total leverage: 2.50x      ← 150% Q1 + 100% Q2
  Number of positions: 10    ← Only top 10 by weight

  ALL POSITIONS (sorted by weight):
     QQQ:  23.50%
    ARKK:  18.30%
     IWM:  15.20%
     XLE:  12.40%
     DBC:  10.10%
     ... (10 total)
```

### IB Executor Output

```
EXECUTING REBALANCE
==========================================
Account Value: $50,000.00
Current Positions: 15

📊 Target Portfolio:
  Positions: 18
  Total Notional: $125,000.00   ← 2.5x leverage

🔄 Executing Trades:
  Closing VGLT...
    → SELL 15.0000 VGLT CFD

  Adjusting QQQ...
    → BUY 25.5000 USTEC CFD    ← USTEC is CFD for QQQ
```

---

## ⚠️ Important Notes

### CFD Availability

**Not all ETFs have CFDs!** Common mappings:

| ETF → CFD | Description |
|-----------|-------------|
| SPY → US500 | S&P 500 |
| QQQ → USTEC | NASDAQ-100 |
| IWM → US2000 | Russell 2000 |

**For unmapped ETFs:**
- Trade the ETF directly (if supported)
- Use index futures
- Modify strategy to only use available CFDs

### Leverage Warning

- **Q1 active**: 2.5x total leverage (150% + 100%)
- **No Q1**: 2.0x total leverage (100% + 100%)
- **Top 10 concentration**: Less operational complexity
- **Ensure adequate margin!**

### Top 10 Benefits

- ✅ **Best returns**: +192.49% vs +175% for full portfolio
- ✅ **Simpler execution**: Only 10 positions vs 17-20
- ✅ **Better alpha**: Top 10 captures most gains
- ✅ **Lower complexity**: Easier to manage live

### Costs

CFDs have:
- Overnight financing charges (~2-5% annually)
- Bid-ask spread costs
- Commission (typically $1-2 per trade)

---

## 🎯 Recommended Workflow

1. **Week 1-2: Testing**
   - Run `signal_generator.py` daily
   - Compare signals to backtest logic
   - Verify quadrant detection makes sense

2. **Week 3-4: Paper Trading** 
   - Run `live_trader.py --mode once --live --port 4002` daily
   - Monitor executed trades in IB paper account
   - Check slippage and execution quality

3. **Month 2: Live Trading (Small Size)**
   - Start with 10-20% of intended capital
   - Run scheduled: `--mode scheduled --time 16:00`
   - Monitor daily and compare to backtest

4. **Month 3+: Scale Up**
   - Gradually increase position size
   - Review monthly performance
   - Adjust if needed

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "Failed to connect to IB" | Check IB Gateway running, verify port (4002 for paper) |
| "Could not qualify CFD" | Update CFD mapping in `ib_executor.py` or remove ticker |
| "Order rejected" | Check margin, verify CFD permissions in IB account |
| Signals look wrong | Verify market data, check date range, review config |

---

## 📖 Full Documentation

For complete details, see:
- **`README_LIVE_TRADING.md`** - Comprehensive setup guide
- **`config.py`** - Asset allocations and quadrants
- **IB API Docs**: https://interactivebrokers.github.io/tws-api/

---

## 🎮 Interactive Test Session

Try this now:

```bash
# 1. Generate signals
python signal_generator.py

# Expected: Shows quadrant scores, top 2 quads, target weights

# 2. If IB Gateway is running, test connection
python ib_executor.py

# Expected: Shows account value and positions

# 3. Run full dry run
python live_trader.py --mode once

# Expected: Signals + trade preview (no execution)
```

---

**Ready to trade live? Read `README_LIVE_TRADING.md` first!** ⚠️

