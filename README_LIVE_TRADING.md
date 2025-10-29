# Live Trading Setup - Macro Quadrant Strategy (Top 10 Production)

## 🎯 Strategy Overview

**Macro Quadrant Rotation Strategy with Volatility Chasing - Top 10 Positions**
- Identifies top 2 economic quadrants using 50-day momentum
- Allocates capital using volatility chasing (higher vol = higher weight)
- Filters entries with 50-day EMA (only allocate above EMA)
- **Concentrates in top 10 positions by weight**
- Asymmetric leverage: Q1 (Goldilocks) = 1.5x, others = 1.0x
- Rebalances when quadrants change or EMA crossovers occur

**Production Strategy: Top 10 Positions**
- **Analyzes**: All 33 ETFs daily
- **Trades**: Only top 10 positions by weight

**Backtest Performance (2020-2025):**
- Total Return: **192.49%**
- Annualized: **29.38%**
- Sharpe Ratio: **0.91**
- Max Drawdown: **-29.44%**
- Outperformance vs SPY: **+69.69%**

---

## 📁 File Structure

```
Macro_Quadrant_Strategy/
├── signal_generator.py      # Generate Top 10 signals
├── ib_executor.py            # Execute trades via IB API
├── live_trader.py            # Main orchestrator (Top 10 default)
├── config.py                 # Asset allocations & quadrants
├── requirements.txt          # Python dependencies
└── README_LIVE_TRADING.md    # This file
```

---

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Interactive Brokers

**Option A: IB Gateway (Recommended for automated trading)**
1. Download IB Gateway from https://www.interactivebrokers.com
2. Install and launch IB Gateway
3. Log in with your credentials
4. Configure API settings:
   - Enable ActiveX and Socket Clients
   - Socket port: 4002 (paper) or 4001 (live)
   - Trusted IPs: 127.0.0.1
   - Master API client ID: Leave blank
   - Read-Only API: NO (we need write access)

**Option B: Trader Workstation (TWS)**
1. Launch TWS
2. Go to File → Global Configuration → API → Settings
3. Enable ActiveX and Socket Clients
4. Socket port: 7497 (paper) or 7496 (live)
5. Add 127.0.0.1 to Trusted IPs
6. Uncheck "Read-Only API"

### 3. Configure CFD Access

**Important: ETF CFD Availability**

Interactive Brokers offers CFDs on many indices, but not all ETFs. Common mappings:

| ETF  | IB CFD Symbol | Underlying |
|------|---------------|------------|
| SPY  | US500         | S&P 500 |
| QQQ  | USTEC         | NASDAQ-100 |
| IWM  | US2000        | Russell 2000 |
| DIA  | INDU          | Dow Jones |
| EFA  | EUSTX50       | European Stocks |

**Alternatives for unmapped ETFs:**
1. **Trade the ETF directly** (if your IB account supports it)
2. **Use index futures** (e.g., ES for SPY, NQ for QQQ)
3. **Use basket of underlying stocks**
4. **Adjust strategy to only use liquid CFDs**

You'll need to:
- Enable CFD trading in your account
- Sign CFD risk disclosures
- Ensure adequate margin

---

## 🎮 Usage

### Test Signal Generation (No Trading)

```bash
python signal_generator.py
```

This will:
- Fetch market data
- Calculate quadrant scores
- Generate target portfolio weights
- Display results (no trades)

### Test IB Connection

```bash
python ib_executor.py
```

Make sure IB Gateway/TWS is running first!

### Run Live Trading

**Dry Run (Recommended First!)**
```bash
python live_trader.py --mode once
```

**Single Execution with Live Trading**
```bash
python live_trader.py --mode once --live --port 4002
```

**Scheduled Daily Trading (Paper)**
```bash
python live_trader.py --mode scheduled --time 16:00 --port 4002
```

**Scheduled Daily Trading (LIVE - BE CAREFUL!)**
```bash
python live_trader.py --mode scheduled --time 16:00 --port 4001 --live
```

### Command Line Arguments

```
--mode       : 'once' or 'scheduled' (default: once)
--time       : Time to run daily in HH:MM format (default: 16:00)
--port       : IB port number
               - 7497 = TWS paper trading
               - 7496 = TWS live trading  
               - 4002 = Gateway paper trading
               - 4001 = Gateway live trading
--live       : Enable actual trade execution (default: dry run)
```

---

## ⚙️ Configuration

### Modify Strategy Parameters

Edit `signal_generator.py`:

```python
sg = SignalGenerator(
    momentum_days=50,   # Quadrant momentum lookback
    ema_period=50,      # EMA trend filter period
    vol_lookback=30     # Volatility calculation window
)
```

### Modify Asset Universe

Edit `config.py` to change quadrant allocations:

```python
QUAD_ALLOCATIONS = {
    'Q1': {
        'QQQ': 0.30,  # 30% of Q1 allocation to QQQ
        'ARKK': 0.21,  # etc.
        ...
    },
    ...
}
```

### Adjust Leverage

Edit `signal_generator.py`, modify `quad_leverage`:

```python
self.quad_leverage = {
    'Q1': 1.5,  # Goldilocks leverage
    'Q2': 1.0,
    'Q3': 1.0,
    'Q4': 1.0
}
```

---

## 📊 Signal Output

Signals are saved to `signals_YYYYMMDD.json`:

```json
{
  "timestamp": "2025-10-29T16:00:00",
  "regime": "Q1 + Q2",
  "top_quadrants": ["Q1", "Q2"],
  "quadrant_scores": {
    "Q1": 15.43,
    "Q2": 8.21,
    "Q3": -2.34,
    "Q4": -5.67
  },
  "target_weights": {
    "QQQ": 0.45,
    "ARKK": 0.31,
    "XLE": 0.18,
    ...
  },
  "total_leverage": 2.5
}
```

---

## ⚠️ Important Considerations

### CFD Trading Risks

1. **Leverage amplifies gains AND losses**
   - This strategy uses up to 2.5x leverage (Q1 + Q2)
   - Ensure adequate margin and risk management

2. **Overnight financing costs**
   - CFDs incur daily interest charges
   - Factor into your P&L calculations

3. **Currency risk**
   - CFDs may be in different currencies
   - Consider hedging FX exposure

### Position Sizing

- The strategy calculates weights as % of capital
- IB executor converts to notional USD values
- Minimum trade threshold: 5% of target position
- Fractional CFD positions are supported

### Rebalancing

- Strategy checks signals daily at 16:00 EST (after market close)
- Only trades if:
  1. Top 2 quadrants change, OR
  2. Asset crosses 50-day EMA, OR  
  3. Position delta > 5% of target

### Market Data

- Uses Yahoo Finance for signal generation
- Real-time prices from IB for execution
- Ensure market data subscriptions are active in IB

---

## 🐛 Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to IB"

**Solutions**:
- Verify IB Gateway/TWS is running
- Check port number (7497 for TWS paper, 4002 for Gateway paper)
- Ensure API is enabled in IB settings
- Add 127.0.0.1 to Trusted IPs
- Try restarting IB Gateway/TWS

### Contract Issues

**Problem**: "Could not qualify XYZ CFD"

**Solutions**:
- Check if CFD is available for that ticker
- Update `etf_to_cfd` mapping in `ib_executor.py`
- Consider using the underlying ETF if supported
- Use index futures as alternative
- Remove unsupported assets from strategy

### Execution Issues

**Problem**: "Order rejected"

**Solutions**:
- Verify account has sufficient margin
- Check trading permissions for CFDs
- Ensure market is open
- Review order size (may be too small/large)
- Check IB logs for specific error

---

## 📈 Monitoring

### Daily Checklist

- [ ] Check signal file generated (signals_YYYYMMDD.json)
- [ ] Verify positions match targets (allow 5% tolerance)
- [ ] Review IB account for executed trades
- [ ] Monitor margin usage (don't exceed 80% of available)
- [ ] Check for any rejected orders
- [ ] Review performance vs benchmark

### Monthly Review

- [ ] Compare actual returns vs backtest expectations
- [ ] Analyze slippage and execution costs
- [ ] Review quadrant regime accuracy
- [ ] Check if any assets should be added/removed
- [ ] Adjust leverage if drawdowns exceed tolerance

---

## 🔐 Security Best Practices

1. **Use paper trading first** - Test for at least 1 month
2. **Start small** - Use 10-20% of intended capital initially
3. **Set stop losses** - Configure IB account-level risk controls
4. **Monitor daily** - Don't set and forget
5. **Keep IB credentials secure** - Use 2FA
6. **Backup signal files** - Maintain trade history
7. **Test disaster recovery** - Know how to manually close positions

---

## 📞 Support & Resources

- IB API Documentation: https://interactivebrokers.github.io/tws-api/
- ib_insync Documentation: https://ib-insync.readthedocs.io/
- IB Knowledge Base: https://www.interactivebrokers.com/en/support/support.php

---

## ⚖️ Disclaimer

**This is for educational purposes only. Not financial advice.**

- Past performance doesn't guarantee future results
- CFD trading involves substantial risk
- You can lose more than your initial investment
- Backtest results don't account for slippage, costs, and real-world execution
- Always test in paper trading first
- Consult a financial advisor before live trading
- You are responsible for your own trading decisions

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Set up IB Gateway/TWS
3. ✅ Run `python signal_generator.py` to test signals
4. ✅ Run `python ib_executor.py` to test IB connection
5. ✅ Run `python live_trader.py --mode once` (dry run)
6. ✅ Review generated signals
7. ✅ Paper trade for 1 month minimum
8. ✅ Review results vs backtest
9. ⚠️ Consider live trading (start small!)

Good luck! 🚀

