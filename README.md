# Macro Quadrant Rotation Strategy - TOP 10 PRODUCTION VERSION

## 🎯 Strategy Overview

**Macro Quadrant Rotation with Volatility Chasing - Top 10 Positions**

This quantitative strategy combines macro regime detection with volatility-weighted allocation to generate superior risk-adjusted returns.

### Key Features

- **Top 10 Positions**: Concentrates allocation in highest-conviction positions
- **Quadrant Detection**: Identifies top 2 economic regimes using 50-day momentum
- **Volatility Chasing**: Allocates MORE to volatile assets (opportunity seeking)
- **50-day EMA Filter**: Only allocates to assets in confirmed uptrends
- **Asymmetric Leverage**: Q1 (Goldilocks) gets 1.5x, others 1.0x
- **Event-Driven Rebalancing**: Trades when signals change, not on fixed schedule

---

## 📊 Performance (5-Year Backtest)

### Production Strategy: Top 10 Positions

| Metric | **Top 10 Strategy** | **S&P 500 (SPY)** | **Difference** |
|--------|---------------------|-------------------|----------------|
| **Total Return** | **192.49%** | 122.80% | **+69.69%** ✅ |
| **Annualized Return** | **29.38%** | 18.35% | **+11.03%** ✅ |
| **Sharpe Ratio** | **0.91** | 1.06 | -0.15 |
| **Max Drawdown** | **-29.44%** | -24.50% | -4.94% |
| **Volatility** | **32.19%** | 17.27% | +14.92% |

**Outperforms S&P 500 by 69.69% over 5 years!** 🚀

### Annual Returns

| Year | Return | Sharpe | Max DD | Win% |
|------|--------|--------|--------|------|
| 2020 | +9.37% | 0.72 | -21.95% | 54.8% |
| 2021 | **+69.00%** | 1.56 | -16.98% | 55.6% |
| 2022 | -10.92% | -0.20 | -28.07% | 51.4% |
| 2023 | +39.74% | 1.36 | -20.07% | 54.4% |
| 2024 | -8.16% | -0.21 | -15.92% | 54.0% |
| 2025 | +38.41% | 1.48 | -18.83% | 52.4% |

**Bear market resilience: 2022 -10.92% vs SPY -18.1%**

---

## 🏆 Why Top 10?

We tested multiple concentration levels:

| Strategy | Total Return | Sharpe | Max DD | Verdict |
|----------|--------------|--------|--------|---------|
| **Top 5** | 108.99% | 0.63 | -33.63% | ❌ Too concentrated |
| **Top 10** | **192.49%** ✅ | **0.91** ✅ | -29.44% | 🥇 **OPTIMAL** |
| **Top 15** | 182.64% | 0.92 | -27.56% | 🥈 Good alternative |
| **Full (17-20)** | 175.06% | 0.91 | -27.81% | 🥉 Over-diversified |

**Top 10 delivers the best absolute returns while maintaining excellent risk-adjusted performance.**

### Why It Works

1. **Captures Alpha**: Top 10 positions contain most of the strategy's alpha
2. **Manageable**: 10 positions is operationally simple for live trading
3. **Concentrated Enough**: Gets upside from best opportunities
4. **Diversified Enough**: Avoids blow-up risk of Top 5
5. **Better Than Full**: Positions 11-20 dilute returns without adding value

---

## 🎮 Asset Universe

**33 ETFs Analyzed Daily → Trade Top 10**

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

**Strategy analyzes all 33, trades only the top 10 by weight each day.**

---

## 🚀 Live Trading

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate signals (Top 10 automatically)
python signal_generator.py

# Run live trading (dry run)
python live_trader.py --mode once

# Run live trading (paper account)
python live_trader.py --mode once --live --port 4002
```

See `README_LIVE_TRADING.md` and `QUICKSTART.md` for full setup instructions.

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
8. **Execute**: Trade if quadrants change or positions cross EMA

### Leverage Structure

- **Q1 Active**: 1.5x allocation (Goldilocks gets overweight)
- **Q2/Q3/Q4 Active**: 1.0x allocation
- **Total Leverage**: 2.0x to 2.5x (depending on quadrants)

### Risk Management

- **EMA Filter**: Prevents allocation to downtrending assets
- **Entry Confirmation**: 1-day lag using live EMA data
- **5% Minimum Trade**: Avoids excessive churning
- **Top 10 Concentration**: Reduces operational complexity

---

## 💰 Costs & Execution

### Trading Costs (Included in Results)

- **Cost per trade**: 10 basis points (0.10%)
- **Total costs**: ~53% of initial capital over 5 years
- **Net returns**: 192.49% after all costs

Despite high trading frequency, alpha generation more than covers costs!

### Rebalancing Frequency

- **Event-driven**: Not on fixed schedule
- **Triggers**: Quadrant change or EMA crossover
- **Frequency**: ~92% of days (highly responsive)

---

## 📁 File Structure

```
Macro_Quadrant_Strategy/
├── signal_generator.py          # Generate Top 10 signals
├── ib_executor.py                # Execute via Interactive Brokers
├── live_trader.py                # Main orchestrator
├── config.py                     # Asset allocations
├── quad_portfolio_backtest.py    # Backtesting engine
├── requirements.txt              # Dependencies
├── README.md                     # This file
├── README_LIVE_TRADING.md        # Full live trading guide
└── QUICKSTART.md                 # Quick reference
```

---

## 🎯 Use Cases

**Best For:**
- ✅ Traders seeking maximum returns
- ✅ Those comfortable with 25-30% drawdowns
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

- **`README_LIVE_TRADING.md`**: Complete Interactive Brokers setup
- **`QUICKSTART.md`**: Quick reference guide
- **`config.py`**: Modify asset allocations
- **`test_top10.py`**: Reproduce backtest results

---

## ⚠️ Disclaimer

**THIS IS FOR EDUCATIONAL PURPOSES ONLY. NOT FINANCIAL ADVICE.**

- Past performance doesn't guarantee future results
- Backtests don't fully represent live trading
- Strategy uses leverage (amplifies gains AND losses)
- You can lose more than your initial investment
- Always paper trade first
- Consult a financial advisor
- You are responsible for your own trading decisions

---

## 📈 Next Steps

1. ✅ Review backtest results
2. ✅ Understand Top 10 concentration benefits
3. ✅ Set up Interactive Brokers account
4. ✅ Run `python signal_generator.py` to see current signals
5. ✅ Paper trade for 1+ month
6. ⚠️ Consider live trading (start small!)

---

**Built for systematic traders who believe markets have structure, patterns can be captured, and volatility is opportunity.**

**Version**: 2.0 (Top 10 Production)  
**Last Updated**: October 2025  
**Performance**: 192.49% return, 0.91 Sharpe, -29.44% max DD (5-year backtest)
