"""
Compare Different Momentum Lookback Periods
===========================================
Tests momentum lookbacks: 10, 20, 30, 50, 100 days
Shows cumulative P/L on same chart with statistical comparison
"""

from quad_portfolio_backtest import QuadrantPortfolioBacktest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Setup
INITIAL_CAPITAL = 50000
BACKTEST_YEARS = 5
MOMENTUM_LOOKBACKS = [10, 20, 30, 50, 100]

end_date = datetime.now()
start_date = end_date - timedelta(days=BACKTEST_YEARS * 365 + 100)

print("="*70)
print("MOMENTUM LOOKBACK COMPARISON")
print("="*70)
print(f"Initial Capital: ${INITIAL_CAPITAL:,}")
print(f"Max Positions: 10")
print(f"Stop Loss: 2.0x ATR (14-day)")
print(f"Period: ~{BACKTEST_YEARS} years")
print(f"Testing Lookbacks: {MOMENTUM_LOOKBACKS}")
print("="*70)
print()

# Run backtests for each momentum lookback
results_dict = {}
portfolio_values = {}

for momentum_days in MOMENTUM_LOOKBACKS:
    print(f"\n{'='*70}")
    print(f"Running backtest with {momentum_days}-day momentum lookback...")
    print(f"{'='*70}")
    
    backtest = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=INITIAL_CAPITAL,
        momentum_days=momentum_days,
        ema_period=50,
        vol_lookback=30,
        max_positions=10,
        atr_stop_loss=2.0,
        atr_period=14
    )
    
    results = backtest.run_backtest()
    results_dict[momentum_days] = results
    portfolio_values[momentum_days] = backtest.portfolio_value
    
    print(f"\n{momentum_days}-day Lookback Results:")
    print(f"  Total Return:      {results['total_return']:.2f}%")
    print(f"  Annualized Return: {results['annual_return']:.2f}%")
    print(f"  Sharpe Ratio:      {results['sharpe']:.2f}")
    print(f"  Max Drawdown:      {results['max_drawdown']:.2f}%")
    print(f"  Volatility:        {results['annual_vol']:.2f}%")

# Create comparison table
print("\n" + "="*100)
print("STATISTICAL COMPARISON")
print("="*100)

# Prepare data for table
comparison_data = []
for momentum_days in MOMENTUM_LOOKBACKS:
    r = results_dict[momentum_days]
    comparison_data.append({
        'Lookback': f"{momentum_days}d",
        'Total Return': f"{r['total_return']:.2f}%",
        'Annual Return': f"{r['annual_return']:.2f}%",
        'Sharpe': f"{r['sharpe']:.2f}",
        'Max DD': f"{r['max_drawdown']:.2f}%",
        'Volatility': f"{r['annual_vol']:.2f}%",
        'Final Value': f"${r['final_value']:,.2f}"
    })

# Print formatted table
print(f"\n{'Lookback':<12} {'Total Ret':>12} {'Annual Ret':>12} {'Sharpe':>10} {'Max DD':>10} {'Volatility':>12} {'Final Value':>15}")
print("-" * 100)
for row in comparison_data:
    print(f"{row['Lookback']:<12} {row['Total Return']:>12} {row['Annual Return']:>12} {row['Sharpe']:>10} "
          f"{row['Max DD']:>10} {row['Volatility']:>12} {row['Final Value']:>15}")

# Find best performers
best_total_return = max(MOMENTUM_LOOKBACKS, key=lambda x: results_dict[x]['total_return'])
best_sharpe = max(MOMENTUM_LOOKBACKS, key=lambda x: results_dict[x]['sharpe'])
best_annual = max(MOMENTUM_LOOKBACKS, key=lambda x: results_dict[x]['annual_return'])
lowest_dd = max(MOMENTUM_LOOKBACKS, key=lambda x: results_dict[x]['max_drawdown'])  # max because DD is negative

print("\n" + "="*100)
print("BEST PERFORMERS")
print("="*100)
print(f"Best Total Return:     {best_total_return}d lookback ({results_dict[best_total_return]['total_return']:.2f}%)")
print(f"Best Annual Return:    {best_annual}d lookback ({results_dict[best_annual]['annual_return']:.2f}%)")
print(f"Best Sharpe Ratio:     {best_sharpe}d lookback ({results_dict[best_sharpe]['sharpe']:.2f})")
print(f"Lowest Max Drawdown:   {lowest_dd}d lookback ({results_dict[lowest_dd]['max_drawdown']:.2f}%)")
print("="*100)

# Plot cumulative P/L on same chart
print("\nGenerating comparison chart...")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

# Colors for different lookbacks
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
color_map = {lookback: colors[i % len(colors)] for i, lookback in enumerate(MOMENTUM_LOOKBACKS)}

# Plot portfolio values (normalized to start at 1 for easier comparison)
for momentum_days in MOMENTUM_LOOKBACKS:
    pv = portfolio_values[momentum_days]
    normalized = (pv / pv.iloc[0]) * 100  # Normalize to percentage of initial
    ax1.plot(pv.index, normalized.values, 
            linewidth=2, 
            label=f'{momentum_days}d Lookback',
            color=color_map[momentum_days],
            alpha=0.8)

ax1.set_title('Cumulative P/L Comparison - Different Momentum Lookbacks', 
             fontsize=14, fontweight='bold')
ax1.set_ylabel('Portfolio Value (% of Initial)', fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.legend(loc='best')
ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5, linewidth=1)

# Plot drawdowns
for momentum_days in MOMENTUM_LOOKBACKS:
    pv = portfolio_values[momentum_days]
    cummax = pv.expanding().max()
    drawdown = (pv - cummax) / cummax * 100
    ax2.plot(drawdown.index, drawdown.values,
            linewidth=2,
            label=f'{momentum_days}d Lookback',
            color=color_map[momentum_days],
            alpha=0.8)

ax2.set_title('Drawdown Comparison', fontsize=14, fontweight='bold')
ax2.set_ylabel('Drawdown (%)', fontsize=12)
ax2.set_xlabel('Date', fontsize=12)
ax2.grid(True, alpha=0.3)
ax2.legend(loc='best')
ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)

plt.tight_layout()
plt.show()

print("\n" + "="*70)
print("Chart displayed! Close the chart window to continue.")
print("="*70)

