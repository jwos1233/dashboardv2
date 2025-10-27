# Macro Quadrant Rotation Strategy - PRODUCTION VERSION

## 🎯 Strategy Overview

**Volatility Chasing with Asymmetric Leverage**

This is an advanced quantitative trading strategy that combines:
1. **Macro Quadrant Analysis** - Identifies market regimes (Q1-Q4) based on growth and inflation
2. **Volatility Chasing** - Dynamically allocates more capital to higher-volatility assets
3. **Asymmetric Leverage** - Overweights the best-performing quadrant (Q1 Goldilocks)
4. **Trend Filtering** - 50-day EMA filter ensures alignment with prevailing trends
5. **Event-Driven Rebalancing** - Only trades when signals change (not on a fixed schedule)

## 📊 Performance (5-Year Backtest)

| Metric | **This Strategy** | **S&P 500 (SPY)** | **Difference** |
|--------|-------------------|-------------------|----------------|
| **Total Return** | **279.50%** | 121.47% | **+158.03%** 🚀 |
| **Annualized Return** | **19.63%** | 11.27% | **+8.36%** ✅ |
| **Sharpe Ratio** | **0.78** | 0.82 | -0.04 |
| **Max Drawdown** | **-35.41%** | -24.50% | -10.91% ⚠️ |
| **Volatility** | 27.81% | 14.32% | +13.49% |

**Outperforms S&P 500 by 158% over 5 years!**

## 🔧 Strategy Components

### 1. Quadrant Classification

The strategy classifies market regimes into 4 quadrants based on momentum signals:

- **Q1 (Goldilocks)**: Growth ↑, Inflation ↓ → Tech/Growth equities, Long-duration bonds
- **Q2 (Reflation)**: Growth ↑, Inflation ↑ → Commodities, Cyclicals, Energy
- **Q3 (Stagflation)**: Growth ↓, Inflation ↑ → Energy, Gold, TIPS, Defensive
- **Q4 (Deflation)**: Growth ↓, Inflation ↓ → Long bonds, Credit, Utilities, Cash

**Quadrant Performance (Historical):**
- **Q1**: +98.82% cumulative (631 days active) 🏆
- **Q3**: +48.91% cumulative (520 days active)
- **Q2**: +36.87% cumulative (467 days active)
- **Q4**: -22.45% cumulative (256 days active)

### 2. Asymmetric Leverage (KEY INNOVATION)

**The Game-Changer**: Not all quadrants are equal. We overweight the winner!

- **Q1 (Goldilocks)**: 200% allocation
- **Q2/Q3/Q4**: 100% allocation each

**Why it works:**
- Q1 has historically been the best-performing quad (+98.82% vs +36-48% for others)
- When Q1 is active, we double down to capture explosive tech/growth rallies
- When Q1 is not active, we reduce to standard 2x leverage (100% + 100%)

**Example Scenarios:**
- **Q1 + Q2 Active**: 200% (Q1) + 100% (Q2) = **300% total leverage** 🚀
- **Q1 + Q3 Active**: 200% (Q1) + 100% (Q3) = **300% total leverage**
- **Q2 + Q3 Active**: 100% (Q2) + 100% (Q3) = **200% total leverage** (standard)

**Result**: Massive outperformance when Goldilocks regime is active!

### 3. Volatility Chasing

**Second Innovation**: Allocates **MORE** to volatile assets (opposite of risk parity).

**Why it works:**
- Volatility = Opportunity in trending markets
- Captures explosive moves in high-momentum assets
- 30-day lookback provides optimal balance between responsiveness and stability

**Formula:**
```
Weight_i = (Vol_i / Σ Vol_j) × Quad_Allocation
```

Where higher Vol_i = higher Weight_i (amplifies winning positions)

### 4. EMA Trend Filter

- Only allocates to assets trading **above** their 50-day EMA
- Assets below EMA held as cash (not redistributed)
- Prevents allocation to assets in downtrends
- Automatic deleveraging during market stress

### 5. Event-Driven Rebalancing

Trades only when:
1. Top 2 quadrants change, **OR**
2. An asset crosses its 50-day EMA (up or down)

**Result**: ~69% of days trigger rebalancing (optimal activity level)

## 📈 Annual Performance Breakdown

| Year | **Strategy** | **S&P 500** | **Outperformance** | Sharpe | Max DD |
|------|-------------|-------------|-------------------|--------|--------|
| 2020 | **+29.02%** | +18.4% | **+10.62%** 🚀 | 1.89 | -17.80% |
| 2021 | **+40.41%** | +28.7% | **+11.71%** ✅ | 0.99 | -19.31% |
| 2022 | **-23.94%** | -18.1% | -5.84% ⚠️ | -0.59 | **-32.64%** |
| 2023 | **+69.93%** | +26.3% | **+43.63%** 🔥 | 1.32 | **-32.84%** |
| 2024 | **+5.10%** | +24.8% | -19.70% | 0.26 | -15.18% |
| 2025 | **+54.21%** | +18.2% | **+36.01%** 🚀 | 1.50 | -15.04% |

**Key Insights:**
- **Explosive Q1 years**: 2023 (+69.93%) and 2025 (+54.21%) = asymmetric leverage pays off massively
- **Bear market risk**: 2022 saw -23.94% loss (Q1 crashed hard with 2x leverage)
- **Annual volatility**: High variance between years (risk = opportunity)
- **Best use case**: Long-term holders who can stomach short-term volatility

## 🏗️ Asset Universe

**35 ETFs across 4 asset classes:**

### Q1 Assets (Growth + Low Inflation)
- **Growth**: QQQ, ARKK, XLC, XLY
- **Bonds**: TLT, LQD

### Q2 Assets (Growth + High Inflation)
- **Commodities**: XLE, DBC, CPER, GCC
- **Cyclicals**: XLF, XLI, XLB
- **Energy**: XOP, FCG
- **Real Assets**: VNQ, PAVE
- **Value**: VTV, IWD

### Q3 Assets (Recession + High Inflation)
- **Energy**: FCG, XLE, XOP
- **Commodities**: GLD, DBC, CPER, DBA, REMX
- **TIPS**: TIP, VTIP
- **Real Assets**: VNQ, PAVE
- **Defensive**: XLV, XLU

### Q4 Assets (Recession + Low Inflation)
- **Long Duration**: VGLT, IEF
- **Credit**: LQD, MUB
- **Defensive**: XLU, XLP, XLV

**35 carefully selected, liquid ETFs = optimal diversification without dilution**

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
2. Calculate quadrant scores daily (50-day momentum)
3. Apply asymmetric leverage (Q1=2x, others=1x)
4. Apply volatility weighting (30-day lookback)
5. Apply EMA filters (50-day)
6. Simulate event-driven rebalancing
7. Generate performance metrics
8. Display equity curve and annual breakdown

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
├── quad_portfolio_backtest.py      # Main production backtest with ASYMMETRIC leverage
├── quad_portfolio_backtest_volweight.py  # Risk parity version (conservative)
├── quad_portfolio_backtest_volchase.py   # Symmetric 2x leverage (previous version)
├── quad_portfolio_backtest_INVERSE.py    # Contrarian version (testing)
├── quad_portfolio_TIME_DIVERSIFIED.py    # Time diversification tests
├── compare_vol_lookbacks.py        # Tool to test different vol periods
├── quadrant_analyzer.py            # Quadrant scoring logic
├── config.py                       # Asset allocations and settings
├── streamlit_dashboard.py          # Live dashboard UI
├── README.md                       # This file
└── requirements.txt                # Python dependencies
```

## 🔬 Strategy Evolution

We tested multiple configurations to arrive at the optimal setup:

### Leverage Schemes Tested

| Approach | Total Return | Sharpe | Max DD | Winner? |
|----------|-------------|--------|--------|---------|
| Symmetric (2x all) | 173.68% | 0.81 | -22.46% | Good |
| **Asymmetric (Q1=2x)** | **279.50%** | 0.78 | -35.41% | ✅ **BEST** |

**Asymmetric adds +106% total return!** The extra drawdown risk is worth it for long-term holders.

### Volatility Lookback Periods

| Period | Total Return | Sharpe | Max DD | Winner? |
|--------|-------------|--------|--------|---------|
| 20-day | 160.8% | 0.77 | -23.6% | |
| **30-day** | **169.8%** | **0.80** | **-22.5%** | ✅ **OPTIMAL** |
| 50-day | 165.3% | 0.78 | -23.1% | |
| 60-day | 163.6% | 0.78 | -23.2% | |

**30-day won on all key metrics (before asymmetric leverage).**

### Asset Universe Tests

| Universe | Tickers | Return | Sharpe | Max DD | Winner? |
|----------|---------|--------|--------|--------|---------|
| Lite | 16 | 66.0% | 0.64 | -28.31% | |
| **Original** | **35** | **279.5%** | **0.78** | **-35.41%** | ✅ **BEST** |
| Expanded | 56 | 95.8% | 0.53 | -40.63% | Worse |

**35 tickers = optimal sweet spot (quality over quantity).**

## ⚙️ Strategy Mechanics

### Daily Process

1. **Morning (T-1)**:
   - Calculate 50-day momentum for quadrant indicators (Q1-Q4)
   - Determine top 2 quadrants by momentum score
   - Calculate 30-day volatility for all 35 assets
   - Check if rebalancing is needed (quad change or EMA cross)

2. **If Rebalancing Needed**:
   - For each of top 2 quads:
     - Determine base allocation: **Q1 = 200%**, **Q2/Q3/Q4 = 100%**
     - Get assets in that quad
     - Calculate volatility weights (higher vol = higher weight)
     - Apply 50-day EMA filter (only allocate if price > EMA)
   - Generate target portfolio (200-300% leverage when fully invested)

3. **Trade Execution (T)**:
   - Rebalance to target weights
   - Assets below EMA → held as cash (automatic deleveraging)

### Example Allocation (Q1 + Q3 Active)

**Q1 (200% allocation - DOUBLE!):**
- ARKK: 50% vol → **80% weight** (volatile = high allocation × Q1 multiplier)
- QQQ: 30% vol → **48% weight**
- XLC: 20% vol → **32% weight**
- Below EMA: 40% cash

**Q3 (100% allocation - STANDARD):**
- FCG: 60% vol → **35% weight** (highest vol)
- XLE: 45% vol → **26% weight**
- GLD: 40% vol → **23% weight**
- Below EMA: 16% cash

**Total Portfolio: 244% allocated, 56% cash**

## 🎯 Use Cases

### Best For:
✅ Aggressive traders seeking **maximum absolute returns**  
✅ Those who can stomach **30-35% drawdowns**  
✅ Belief that "volatility = opportunity"  
✅ Trend-following / momentum mindset  
✅ **5+ year investment horizon** (to ride through volatility)  
✅ High conviction in Q1 (Goldilocks) regime outperformance  

### Not Ideal For:
❌ Conservative investors  
❌ Those requiring stable monthly returns  
❌ Can't tolerate -30%+ drawdowns  
❌ Need liquidity < 3 years  
❌ Risk-averse portfolios  
❌ Margin-called portfolios (3x leverage in Q1 periods!)  

## 📊 Risk Metrics

- **Volatility**: 27.81% (high, but expected with 2-3x leverage)
- **Max Drawdown**: -35.41% (occurred in 2022 and 2023 when Q1 crashed)
- **Sharpe Ratio**: 0.78 (solid given the aggression)
- **Win Rate**: ~37% of days positive (momentum = streaky)
- **Rebalance Frequency**: 68.7% (active but controlled)
- **Leverage**: 200-300% gross (2-3x depending on quad mix)

**Risk Management Built-In:**
- EMA filter automatically deleverages in downtrends
- Cash held when assets below EMA (reduces leverage in bear markets)
- Event-driven rebalancing prevents whipsaw losses

## 🔄 Alternative Configurations

If the production version is too aggressive, consider:

### Moderate (Symmetric 2x Leverage):
```bash
python quad_portfolio_backtest_volchase.py
```
- Q1/Q2/Q3/Q4 all get 100% allocation (2x total)
- 173.68% return, 0.81 Sharpe, -22.46% max DD
- Best for those who want leverage without Q1 concentration

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

## 🖥️ Live Dashboard

Run the Streamlit dashboard to see live signals:

```bash
streamlit run streamlit_dashboard.py
```

Features:
- Current active quadrants
- Recommended asset allocations
- Strategy performance chart
- Dominant assets in each quad
- Live EMA filter status

## 🤝 Contributing

This is a production-ready backtesting framework. To extend:

1. **Add new quadrant definitions** in `config.py`
2. **Test new indicators** in `quadrant_analyzer.py`
3. **Modify leverage schemes** in `calculate_target_weights()`
4. **Adjust filters** (EMA period, momentum lookback, etc.)

## ⚠️ Disclaimer

**THIS IS FOR EDUCATIONAL AND RESEARCH PURPOSES ONLY.**

- Past performance does not guarantee future results
- Backtests are not representative of live trading
- Slippage, commissions, and market impact are not fully modeled
- **This strategy uses 2-3x leverage which amplifies both gains and losses**
- **Max drawdown of -35% means you must have risk tolerance for large swings**
- The asymmetric Q1 allocation assumes future Q1 dominance (regime change risk)
- Consult a financial advisor before implementing any strategy
- You are responsible for your own trading decisions

**Specific Risks:**
- **Leverage risk**: 3x leverage in Q1+Q1 scenarios can lead to rapid losses
- **Concentration risk**: Overweight to tech/growth in Q1 periods
- **Regime change risk**: If Q1 stops outperforming, strategy underperforms
- **Volatility risk**: Chasing volatility works in trends but fails in chop

## 📧 Questions?

For questions about the strategy, methodology, or implementation, please refer to:
- Code comments in `quad_portfolio_backtest.py`
- Quadrant definitions in `config.py`
- Performance comparison charts generated by `compare_vol_lookbacks.py`
- Live dashboard: `streamlit_dashboard.py`

---

**Built with ❤️ for systematic traders who believe markets have structure, patterns can be captured, and volatility is opportunity.**

**Last Updated**: October 2025  
**Version**: 2.0 (Asymmetric Leverage Production)  
**Performance**: 279.50% return, 0.78 Sharpe, -35.41% max DD (5-year backtest)  
**Key Innovation**: Asymmetric leverage (Q1=2x) captures +158% alpha vs S&P 500
