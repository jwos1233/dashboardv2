# Macro Quadrant Rotation Strategy - PRODUCTION VERSION

## 🎯 Strategy Overview

**Volatility Chasing with Macro Quadrant Rotation**

This is an advanced quantitative trading strategy that combines:
1. **Macro Quadrant Analysis** - Identifies market regimes (Q1-Q4) based on growth and inflation
2. **Volatility Chasing** - Dynamically allocates more capital to higher-volatility assets
3. **Trend Filtering** - 50-day EMA filter ensures alignment with prevailing trends
4. **Event-Driven Rebalancing** - Only trades when signals change (not on a fixed schedule)

## 📊 Performance (5-Year Backtest)

| Metric | **This Strategy** | **S&P 500 (SPY)** | **Difference** |
|--------|-------------------|-------------------|----------------|
| **Total Return** | **169.8%** | 112.9% | **+56.9%** ✅ |
| **Annualized Return** | **14.3%** | 10.7% | **+3.6%** ✅ |
| **Sharpe Ratio** | **0.80** | 0.78 | **+0.02** ✅ |
| **Max Drawdown** | **-22.5%** | -24.5% | **+2.0%** ✅ |
| **Volatility** | 19.1% | 14.4% | +4.7% |

**Outperforms S&P 500 by 56.9% while maintaining similar risk-adjusted returns!**

## 🔧 Strategy Components

### 1. Quadrant Classification

The strategy classifies market regimes into 4 quadrants based on momentum signals:

- **Q1 (Goldilocks)**: Growth ↑, Inflation ↓ → Tech/Growth equities, Long-duration bonds
- **Q2 (Reflation)**: Growth ↑, Inflation ↑ → Commodities, Cyclicals, Energy
- **Q3 (Stagflation)**: Growth ↓, Inflation ↑ → Energy, Gold, TIPS, Defensive
- **Q4 (Deflation)**: Growth ↓, Inflation ↓ → Long bonds, Credit, Utilities, Cash

### 2. Volatility Chasing

**Key Innovation**: Instead of equal weighting or risk parity (inverse vol), this strategy allocates **MORE** to volatile assets.

**Why it works:**
- Volatility = Opportunity in trending markets
- Captures explosive moves in high-momentum assets
- 30-day lookback provides optimal balance between responsiveness and stability

**Formula:**
```
Weight_i = (Vol_i / Σ Vol_j) × Quad_Allocation
```

Where higher Vol_i = higher Weight_i (opposite of traditional risk parity)

### 3. EMA Trend Filter

- Only allocates to assets trading **above** their 50-day EMA
- Assets below EMA held as cash (not redistributed)
- Prevents allocation to assets in downtrends

### 4. Event-Driven Rebalancing

Trades only when:
1. Top 2 quadrants change, **OR**
2. An asset crosses its 50-day EMA (up or down)

**Result**: ~69% of days trigger rebalancing (optimal activity level)

### 5. Leverage

- **2x leverage**: 100% allocation to each of the top 2 quadrants
- Total portfolio allocation: 200% of capital (when fully invested)
- Reduced when assets filter out below EMA (automatic deleveraging in downtrends)

## 📈 Annual Performance Breakdown

| Year | **Strategy** | **S&P 500** | **Outperformance** |
|------|-------------|-------------|-------------------|
| 2020 | +21.4% | +18.4% | +3.0% |
| 2021 | **+42.3%** | +28.7% | **+13.6%** 🚀 |
| 2022 | -13.7% | -18.1% | +4.4% ✅ |
| 2023 | +33.9% | +26.3% | +7.6% |
| 2024 | +9.4% | +24.8% | -15.4% |
| 2025 | +23.4% | +18.2% | +5.2% |

**Key Insights:**
- Massive outperformance in bull markets (2021: +42%)
- Better downside protection in bear markets (2022: -13.7% vs SPY -18.1%)
- Consistent alpha generation across most years

## 🏗️ Asset Universe

**35 ETFs across 4 asset classes:**

### Equities (20)
- **Growth**: QQQ, ARKK, VUG, XLC, XLY
- **Value**: VTV, IWD
- **Small Cap**: IWM
- **Sectors**: XLF, XLI, XLB, XLV, XLU, XLP
- **International**: EFA, EEM, VGK, EWJ, EWG, EWU

### Fixed Income (7)
- **Treasuries**: TLT, IEF, VGLT
- **TIPS**: TIP, VTIP
- **Credit**: LQD, MUB

### Commodities (6)
- **Energy**: XLE, XOP, FCG, USO
- **Broad**: DBC
- **Metals**: REMX

### Alternatives (2)
- **Real Estate**: VNQ, PAVE

## 🚀 Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

Required packages:
- `yfinance` - Historical price data
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib` - Visualization

### Running the Backtest

```bash
python quad_portfolio_backtest.py
```

This will:
1. Download historical data for all 35 tickers
2. Calculate quadrant scores daily
3. Apply volatility weighting and EMA filters
4. Simulate event-driven rebalancing
5. Generate performance metrics
6. Display equity curve and regime chart

### Configuration

Edit the parameters in `quad_portfolio_backtest.py`:

```python
INITIAL_CAPITAL = 50000   # Starting capital
LOOKBACK_DAYS = 50        # Momentum period for quadrant scoring
EMA_PERIOD = 50           # Trend filter period
VOL_LOOKBACK = 30         # Volatility lookback (OPTIMAL)
BACKTEST_YEARS = 5        # Backtest duration
```

## 📁 Project Structure

```
Macro_Quadrant_Strategy/
├── quad_portfolio_backtest.py      # Main production backtest (THIS FILE)
├── quad_portfolio_backtest_volweight.py  # Risk parity version (conservative)
├── quad_portfolio_backtest_volchase.py   # Volatility chasing (same as main)
├── compare_vol_lookbacks.py        # Tool to test different vol periods
├── quadrant_analyzer.py            # Quadrant scoring logic
├── config.py                       # Asset allocations and settings
├── README.md                       # This file
└── requirements.txt                # Python dependencies
```

## 🔬 Optimization History

We tested multiple configurations to find the optimal setup:

### Volatility Lookback Periods

| Period | Total Return | Sharpe | Max DD | Winner? |
|--------|-------------|--------|--------|---------|
| 20-day | 160.8% | 0.77 | -23.6% | |
| **30-day** | **169.8%** | **0.80** | **-22.5%** | ✅ **BEST** |
| 50-day | 165.3% | 0.78 | -23.1% | |
| 60-day | 163.6% | 0.78 | -23.2% | |

**30-day won on all key metrics!**

### Weighting Approaches Compared

| Approach | Total Return | Sharpe | Max DD | Best For |
|----------|-------------|--------|--------|----------|
| **Fixed Allocation** | 129.2% | 0.81 | -20.2% | Simplicity |
| **Risk Parity (60d)** | 85.4% | 0.83 | -17.6% | Low risk |
| **Vol Chasing (30d)** | **169.8%** | 0.80 | -22.5% | **Max returns** ✅ |

**Vol Chasing is the clear winner for absolute returns!**

## ⚙️ Strategy Mechanics

### Daily Process

1. **Morning (T-1)**:
   - Calculate 50-day momentum for quadrant indicators
   - Determine top 2 quadrants
   - Calculate 30-day volatility for all assets
   - Check if rebalancing is needed (quad change or EMA cross)

2. **If Rebalancing Needed**:
   - For each of top 2 quads:
     - Get assets in that quad
     - Calculate volatility weights (higher vol = higher weight)
     - Apply 50-day EMA filter (only allocate if price > EMA)
   - Generate target portfolio (200% leverage when fully invested)

3. **Trade Execution (T)**:
   - Rebalance to target weights
   - Assets below EMA → held as cash

### Example Allocation (Hypothetical Q1 + Q2)

**Q1 (100% allocation):**
- ARKK: 50% vol → **40% weight** (volatile = high allocation)
- QQQ: 30% vol → **24% weight**
- XLC: 20% vol → **16% weight**
- Below EMA: 20% cash

**Q2 (100% allocation):**
- FCG: 60% vol → **35% weight** (highest vol)
- XLE: 45% vol → **26% weight**
- DBC: 40% vol → **23% weight**
- Below EMA: 16% cash

**Total Portfolio: 164% allocated, 36% cash**

## 🎯 Use Cases

### Best For:
✅ Aggressive traders seeking maximum returns  
✅ Those who can stomach 20-25% drawdowns  
✅ Belief that "volatility = opportunity"  
✅ Trend-following mindset  
✅ 5+ year investment horizon  

### Not Ideal For:
❌ Conservative investors  
❌ Those requiring monthly income  
❌ Can't tolerate -20%+ drawdowns  
❌ Need liquidity < 1 year  
❌ Risk-averse portfolios  

## 📊 Risk Metrics

- **Volatility**: 19.1% (similar to leveraged equity exposure)
- **Max Drawdown**: -22.5% (occurred in 2022)
- **Sharpe Ratio**: 0.80 (solid risk-adjusted returns)
- **Win Rate**: ~37% of days positive
- **Rebalance Frequency**: 69% (active but not excessive)

## 🔄 Alternative Configurations

If the production version is too aggressive, consider:

### Conservative (Risk Parity):
```bash
python quad_portfolio_backtest_volweight.py
```
- Uses **inverse** volatility (lower vol = higher weight)
- 85% return, 0.83 Sharpe, -17.6% max DD
- Best for risk-averse investors

### Experiment:
```bash
python compare_vol_lookbacks.py
```
- Tests 20/30/50/60 day periods
- Generates comparison charts
- Helps optimize for your risk tolerance

## 🤝 Contributing

This is a production-ready backtesting framework. To extend:

1. **Add new quadrant definitions** in `config.py`
2. **Test new indicators** in `quadrant_analyzer.py`
3. **Modify weighting schemes** in `calculate_target_weights()`
4. **Adjust filters** (EMA period, momentum lookback, etc.)

## ⚠️ Disclaimer

**THIS IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

- Past performance does not guarantee future results
- Backtests are not representative of live trading
- Slippage, commissions, and market impact are not fully modeled
- This strategy uses leverage (2x) which amplifies both gains and losses
- Consult a financial advisor before implementing any strategy
- You are responsible for your own trading decisions

## 📧 Questions?

For questions about the strategy, methodology, or implementation, please refer to:
- Code comments in `quad_portfolio_backtest.py`
- Quadrant definitions in `config.py`
- Performance comparison charts generated by `compare_vol_lookbacks.py`

---

**Built with ❤️ for systematic traders who believe markets have structure, patterns can be captured, and volatility is opportunity.**

**Last Updated**: October 2025  
**Version**: 1.0 (Production)  
**Performance**: 169.8% return, 0.80 Sharpe, -22.5% max DD (5-year backtest)
