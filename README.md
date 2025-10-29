# Macro Quadrant Rotation Strategy - PRODUCTION v3.0

## 🎯 Strategy Overview

**Macro Quadrant Rotation with Volatility Chasing + ATR Stop Loss**

This quantitative strategy combines macro regime detection with volatility-weighted allocation and dynamic stop losses to generate exceptional risk-adjusted returns.

### Key Features

- **Top 10 Positions**: Concentrates allocation in highest-conviction positions
- **ATR 2.0x Stop Loss**: Dynamic risk management (2.0 × 14-day ATR)
- **Quadrant Detection**: Identifies top 2 economic regimes using 50-day momentum
- **Volatility Chasing**: Allocates MORE to volatile assets (opportunity seeking)
- **50-day EMA Filter**: Only allocates to assets in confirmed uptrends
- **Asymmetric Leverage**: Q1 (Goldilocks) gets 1.5x, others 1.0x
- **Event-Driven Rebalancing**: Trades when signals change, not on fixed schedule

---

## 📊 Performance (5-Year Backtest)

### Production Strategy: Top 10 + ATR 2.0x

| Metric | **Top 10 + ATR 2.0x** | **S&P 500 (SPY)** | **Difference** |
|--------|----------------------|-------------------|----------------|
| **Total Return** | **420.86%** | 122.90% | **+297.95%** ✅ |
| **Annualized Return** | **43.96%** | 18.35% | **+25.62%** ✅ |
| **Sharpe Ratio** | **1.41** | 1.06 | **+0.35** ✅ |
| **Max Drawdown** | **-22.62%** | -24.50% | **+1.88%** ✅ |
| **Volatility** | **31.07%** | 17.26% | +13.81% |

**Outperforms S&P 500 by 297.95% over 5 years!** 🚀

**$50,000 → $260,428 (net of all costs)**

### Annual Returns

| Year | Return | Sharpe | Max DD | Win% |
|------|--------|--------|--------|------|
| 2020 | +16.66% | 1.11 | -17.62% | 56.7% |
| 2021 | **+80.40%** | 1.74 | -17.22% | 56.0% |
| 2022 | **+1.07%** 🛡️ | 0.19 | -22.62% | 51.4% |
| 2023 | +54.15% | 1.75 | -18.33% | 55.2% |
| 2024 | -1.07% | 0.07 | -11.23% | 53.2% |
| 2025 | **+60.56%** | 2.21 | -10.76% | 54.1% |

**2022 Bear Market: +1.07% vs SPY -18.1%** (ATR stops protected capital!)

---

## 🏆 Evolution of the Strategy

| Version | Key Feature | Total Return | Sharpe | Max DD | Verdict |
|---------|-------------|--------------|--------|--------|---------|
| v1.0 | Full Portfolio (17-20 positions) | 175.06% | 0.91 | -27.81% | Good |
| v2.0 | **Top 10 Positions** | 192.49% | 0.91 | -29.44% | Better |
| **v3.0** | **Top 10 + ATR 2.0x** | **420.86%** | **1.41** | **-22.62%** | **BEST** ✅ |

**Why ATR stops changed everything:**
- +228% better returns than v2.0
- +55% better Sharpe ratio
- -7% lower max drawdown
- Protected in 2022 bear market (+1.07% vs -10.92%)

---

## 🎮 Asset Universe

**33 ETFs Analyzed Daily → Trade Top 10 with ATR Stops**

### Quadrant 1 - Goldilocks (Growth ↑, Inflation ↓)
- QQQ, ARKK, IWM (Growth/Tech)
- XLC, XLY (Consumer)
- TLT, LQD (Bonds)

### Quadrant 2 - Reflation (Growth ↑, Inflation ↑)
- XLE, DBC, CPER, GCC (Commodities)
- XLF, XLI, XLB (Cyclicals)
- XOP, FCG, USO (Energy)
- VNQ, PAVE (Real Assets)
- VTV, IWD (Value)

### Quadrant 3 - Stagflation (Growth ↓, Inflation ↑)
- FCG, XLE, XOP (Energy)
- GLD, DBC, CPER, DBA, REMX, URA (Commodities)
- TIP, VTIP (TIPS)
- VNQ, PAVE (Real Assets)
- XLV, XLU (Defensive)

### Quadrant 4 - Deflation (Growth ↓, Inflation ↓)
- VGLT, IEF (Long Treasuries)
- LQD, MUB (Credit)
- XLU, XLP, XLV (Defensive)
- Cash (15% allocation)

---

## 🚀 Live Trading

### Two-Step Entry Process

The system uses a **two-step confirmation** to match the backtest's 420% returns:

```bash
# STEP 1: Night run (after market close)
python live_trader.py --step night

# STEP 2: Morning run (before market open)
python live_trader.py --step morning --live --port 4002
```

**Why two steps?**
- Day 1: Generate signals from close prices
- Day 2: Confirm EMA still valid before executing at open
- **Result:** 28.1% rejection rate (as in backtest)
- Avoids bad entries, improves returns by +228%

See `TWO_STEP_ENTRY.md` for full details.

### Automated Mode

```bash
# Runs both steps automatically (16:00 and 09:29)
python live_trader.py --mode scheduled --live --port 4002
```

### Quick Start (Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Generate signals (Top 10 + ATR 2.0x automatically)
python signal_generator.py

# Dry run test
python live_trader.py --step night
python live_trader.py --step morning  # Without --live
```

See `STRATEGY_EXPLAINED.md` for complete entry/exit rules.

---

## ⚙️ Strategy Mechanics

### Daily Process

1. **Fetch Data**: Download prices for all 33 ETFs
2. **Calculate Quadrant Scores**: 50-day momentum for Q1/Q2/Q3/Q4
3. **Identify Top 2 Quads**: Highest momentum quadrants
4. **Calculate Volatility**: 30-day rolling volatility for all assets
5. **Apply EMA Filter**: Only consider assets above 50-day EMA
6. **Weight by Volatility**: Higher vol = higher allocation (chasing)
7. **Select Top 10**: Keep 10 largest positions, scale to maintain leverage
8. **Apply ATR Stops**: Exit if price < entry - (2.0 × 14-day ATR)
9. **Execute**: Trade at next day's open

### Entry Rules

**ALL required:**
1. ✅ Asset in top 2 quadrants
2. ✅ Price > 50-day EMA
3. ✅ In Top 10 by weight
4. ✅ **Confirmed**: Still above EMA next day

**Execute at next day's open**

### Exit Rules

**Exit on ANY (priority order):**
1. 🛑 **Stop Loss**: Price ≤ Entry - (2.0 × ATR)
2. 📉 **EMA Cross**: Price < 50-day EMA
3. 🔄 **Quadrant Change**: Asset's quad no longer in top 2
4. 📊 **Dropped from Top 10**: Asset no longer in top 10 by weight

**No lag on exits - immediate!**

### Leverage Structure

- **Q1 Active**: 1.5x allocation (Goldilocks gets overweight)
- **Q2/Q3/Q4 Active**: 1.0x allocation
- **Total Leverage**: 2.0x to 2.5x (depending on quadrants)

### Risk Management

- **ATR Stop Loss**: Dynamic stops adapt to volatility
- **EMA Filter**: Prevents allocation to downtrending assets
- **Entry Confirmation**: 1-day lag using live EMA data
- **5% Minimum Trade**: Avoids excessive churning
- **Top 10 Concentration**: Reduces operational complexity

---

## 💰 Costs & Execution

### Trading Costs (Included in Results)

- **Cost per trade**: 10 basis points (0.10%)
- **Total costs**: ~79% of initial capital over 5 years
- **Net returns**: 420.86% after all costs

Despite high trading frequency and stop losses, alpha generation more than covers costs!

### Stop Loss Statistics

- **Stops hit**: 327 over 5 years (~5.4 per month)
- **Rejection rate**: 28.1% (entry confirmation working)
- **Rebalancing**: 93.8% of days (highly responsive)

---

## 📁 File Structure

```
Macro_Quadrant_Strategy/
├── signal_generator.py          # Generate Top 10 + ATR signals
├── ib_executor.py                # Execute via Interactive Brokers
├── live_trader.py                # Main orchestrator
├── config.py                     # Asset allocations
├── quad_portfolio_backtest.py    # Backtesting engine (supports ATR)
├── requirements.txt              # Dependencies
├── README.md                     # This file
├── STRATEGY_EXPLAINED.md         # Complete strategy breakdown
├── README_LIVE_TRADING.md        # Full live trading guide
├── QUICKSTART.md                 # Quick reference
└── PRODUCTION_SUMMARY.md         # Production overview
```

---

## 🎯 Use Cases

**Best For:**
- ✅ Traders seeking maximum returns with managed risk
- ✅ Those comfortable with 20-25% drawdowns
- ✅ "Volatility = opportunity" mindset
- ✅ 5+ year investment horizon
- ✅ Systematic/algorithmic trading

**Not Ideal For:**
- ❌ Very conservative investors
- ❌ Cannot tolerate >20% drawdowns
- ❌ Need monthly income
- ❌ Short-term trading (<1 year)

---

## 📚 Documentation

- **`STRATEGY_EXPLAINED.md`**: Complete strategy breakdown with examples
- **`README_LIVE_TRADING.md`**: Interactive Brokers setup
- **`QUICKSTART.md`**: Quick reference guide
- **`PRODUCTION_SUMMARY.md`**: Production overview
- **`config.py`**: Modify asset allocations

---

## ⚠️ Disclaimer

**THIS IS FOR EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.**

- Past performance doesn't guarantee future results
- Backtests don't fully represent live trading
- Strategy uses leverage (amplifies gains AND losses)
- Stop losses don't guarantee fills (gaps, liquidity)
- You can lose more than your initial investment
- Always paper trade first
- Consult a financial advisor
- You are responsible for your own trading decisions

---

## 📈 Next Steps

1. ✅ Review backtest results (420.86% return)
2. ✅ Read `STRATEGY_EXPLAINED.md` for complete breakdown
3. ✅ Understand ATR stop loss mechanics
4. ✅ Set up Interactive Brokers account
5. ✅ Run `python signal_generator.py` to see current signals
6. ✅ Paper trade for 1+ month
7. ⚠️ Consider live trading (start small!)

---

**Built for systematic traders who believe markets have structure, patterns can be captured, and risk can be managed dynamically.**

**Version**: 3.0 (Top 10 + ATR 2.0x Production)  
**Last Updated**: October 2025  
**Performance**: 420.86% return, 1.41 Sharpe, -22.62% max DD (5-year backtest)
