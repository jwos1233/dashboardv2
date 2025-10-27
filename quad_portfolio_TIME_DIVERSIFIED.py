"""
TIME DIVERSIFIED MACRO QUADRANT STRATEGY
==========================================

Runs TWO momentum strategies in parallel:
- 50% capital to 50-day momentum (intermediate trend)
- 50% capital to 21-day momentum (short-term trend)

Both use same logic: volatility chasing, EMA filter, event-driven rebalancing
Tests if time diversification improves risk-adjusted returns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# Import the main backtest class
from quad_portfolio_backtest import QuadrantPortfolioBacktest

if __name__ == "__main__":
    # Strategy parameters
    INITIAL_CAPITAL = 50000
    CAPITAL_SPLIT = 0.5  # 50% to each strategy
    VOL_LOOKBACK = 30
    BACKTEST_YEARS = 5
    
    # Aligned timeframes (momentum period = EMA period)
    MOMENTUM_50D = 50
    EMA_50D = 50
    MOMENTUM_21D = 21
    EMA_21D = 21
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BACKTEST_YEARS * 365 + 100)
    
    print("=" * 70)
    print("TIME DIVERSIFIED MACRO QUADRANT STRATEGY - ALIGNED TIMEFRAMES")
    print("=" * 70)
    print(f"Total Capital: ${INITIAL_CAPITAL:,}")
    print(f"Strategy 1: 50-day momentum + 50-day EMA ({CAPITAL_SPLIT*100:.0f}% capital)")
    print(f"Strategy 2: 21-day momentum + 21-day EMA ({CAPITAL_SPLIT*100:.0f}% capital)")
    print(f"Shared: 30-day vol chasing, 2x leverage each")
    print(f"Backtest Period: ~{BACKTEST_YEARS} years")
    print(f"Improvement: Each strategy uses internally consistent timeframes")
    print("=" * 70)
    print()
    
    # Run Strategy 1: 50-day momentum + 50-day EMA
    print("Running Strategy 1 (50-day momentum + 50-day EMA)...")
    print("-" * 70)
    backtest_50d = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=INITIAL_CAPITAL * CAPITAL_SPLIT,
        momentum_days=MOMENTUM_50D,
        ema_period=EMA_50D,
        vol_lookback=VOL_LOOKBACK
    )
    results_50d = backtest_50d.run_backtest()
    pv_50d = backtest_50d.portfolio_value
    
    print("\n" + "=" * 70)
    print()
    
    # Run Strategy 2: 21-day momentum + 21-day EMA
    print("Running Strategy 2 (21-day momentum + 21-day EMA)...")
    print("-" * 70)
    backtest_21d = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=INITIAL_CAPITAL * CAPITAL_SPLIT,
        momentum_days=MOMENTUM_21D,
        ema_period=EMA_21D,
        vol_lookback=VOL_LOOKBACK
    )
    results_21d = backtest_21d.run_backtest()
    pv_21d = backtest_21d.portfolio_value
    
    print("\n" + "=" * 70)
    print()
    
    # Combine portfolios
    print("Calculating combined portfolio performance...")
    
    # Align dates (both should have same dates but just in case)
    common_dates = pv_50d.index.intersection(pv_21d.index)
    pv_50d_aligned = pv_50d.loc[common_dates]
    pv_21d_aligned = pv_21d.loc[common_dates]
    
    # Combined portfolio value
    pv_combined = pv_50d_aligned + pv_21d_aligned
    
    # Calculate combined returns
    returns_combined = pv_combined.pct_change().dropna()
    
    # Performance metrics
    total_return = (pv_combined.iloc[-1] / INITIAL_CAPITAL - 1) * 100
    years = len(returns_combined) / 252
    annual_return = ((pv_combined.iloc[-1] / INITIAL_CAPITAL) ** (1 / years) - 1) * 100
    annual_vol = returns_combined.std() * np.sqrt(252) * 100
    sharpe = (returns_combined.mean() / returns_combined.std() * np.sqrt(252)) if returns_combined.std() > 0 else 0
    
    # Drawdown
    cumulative = (1 + returns_combined).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    
    # Display combined results
    print("\n" + "=" * 70)
    print("COMBINED PORTFOLIO PERFORMANCE")
    print("=" * 70)
    print(f"Initial Capital...................................            ${INITIAL_CAPITAL:,.0f}")
    print(f"Final Capital.....................................        ${pv_combined.iloc[-1]:,.2f}")
    print(f"Total Return......................................            {total_return:.2f}%")
    print(f"Annualized Return.................................             {annual_return:.2f}%")
    print(f"Annualized Volatility.............................             {annual_vol:.2f}%")
    print(f"Sharpe Ratio......................................               {sharpe:.2f}")
    print(f"Maximum Drawdown..................................            {max_drawdown:.2f}%")
    print("=" * 70)
    
    # Individual strategy comparison
    print("\n" + "=" * 70)
    print("STRATEGY COMPARISON (ALIGNED TIMEFRAMES)")
    print("=" * 70)
    print(f"{'Metric':<25} {'50d/50d':<15} {'21d/21d':<15} {'Combined':<15}")
    print("-" * 70)
    
    # Extract metrics for each
    returns_50d = pv_50d.pct_change().dropna()
    total_50d = (pv_50d.iloc[-1] / (INITIAL_CAPITAL * CAPITAL_SPLIT) - 1) * 100
    ann_ret_50d = ((pv_50d.iloc[-1] / (INITIAL_CAPITAL * CAPITAL_SPLIT)) ** (1 / years) - 1) * 100
    vol_50d = returns_50d.std() * np.sqrt(252) * 100
    sharpe_50d = (returns_50d.mean() / returns_50d.std() * np.sqrt(252)) if returns_50d.std() > 0 else 0
    
    cum_50d = (1 + returns_50d).cumprod()
    dd_50d = ((cum_50d - cum_50d.expanding().max()) / cum_50d.expanding().max()).min() * 100
    
    returns_21d = pv_21d.pct_change().dropna()
    total_21d = (pv_21d.iloc[-1] / (INITIAL_CAPITAL * CAPITAL_SPLIT) - 1) * 100
    ann_ret_21d = ((pv_21d.iloc[-1] / (INITIAL_CAPITAL * CAPITAL_SPLIT)) ** (1 / years) - 1) * 100
    vol_21d = returns_21d.std() * np.sqrt(252) * 100
    sharpe_21d = (returns_21d.mean() / returns_21d.std() * np.sqrt(252)) if returns_21d.std() > 0 else 0
    
    cum_21d = (1 + returns_21d).cumprod()
    dd_21d = ((cum_21d - cum_21d.expanding().max()) / cum_21d.expanding().max()).min() * 100
    
    print(f"{'Total Return':<25} {total_50d:>13.2f}%  {total_21d:>13.2f}%  {total_return:>13.2f}%")
    print(f"{'Annualized Return':<25} {ann_ret_50d:>13.2f}%  {ann_ret_21d:>13.2f}%  {annual_return:>13.2f}%")
    print(f"{'Volatility':<25} {vol_50d:>13.2f}%  {vol_21d:>13.2f}%  {annual_vol:>13.2f}%")
    print(f"{'Sharpe Ratio':<25} {sharpe_50d:>13.2f}   {sharpe_21d:>13.2f}   {sharpe:>13.2f}")
    print(f"{'Max Drawdown':<25} {dd_50d:>13.2f}%  {dd_21d:>13.2f}%  {max_drawdown:>13.2f}%")
    print("=" * 70)
    
    # Correlation between strategies
    corr = returns_50d.loc[returns_50d.index.isin(returns_21d.index)].corr(
        returns_21d.loc[returns_21d.index.isin(returns_50d.index)]
    )
    print(f"\nCorrelation between strategies: {corr:.3f}")
    print("(Lower correlation = better diversification benefit)")
    
    # Plot comparison
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Portfolio values
    axes[0].plot(pv_50d.index, pv_50d.values, label='50d/50d (momentum/EMA)', linewidth=2, alpha=0.7)
    axes[0].plot(pv_21d.index, pv_21d.values, label='21d/21d (momentum/EMA)', linewidth=2, alpha=0.7)
    axes[0].plot(pv_combined.index, pv_combined.values, label='Combined (50/50)', 
                linewidth=2.5, color='black', linestyle='--')
    axes[0].set_title('Time Diversified Strategy: Aligned Timeframes Comparison', 
                     fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Portfolio Value ($)', fontsize=12)
    axes[0].legend(loc='upper left', fontsize=10)
    axes[0].grid(True, alpha=0.3)
    
    # Add performance text
    axes[0].text(0.02, 0.98, 
                f'Combined: {total_return:.1f}% return, {sharpe:.2f} Sharpe',
                transform=axes[0].transAxes, fontsize=11, fontweight='bold',
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Cumulative returns comparison
    cum_ret_50d = (pv_50d / (INITIAL_CAPITAL * CAPITAL_SPLIT) - 1) * 100
    cum_ret_21d = (pv_21d / (INITIAL_CAPITAL * CAPITAL_SPLIT) - 1) * 100
    cum_ret_combined = (pv_combined / INITIAL_CAPITAL - 1) * 100
    
    axes[1].plot(cum_ret_50d.index, cum_ret_50d.values, label='50d/50d', linewidth=2, alpha=0.7)
    axes[1].plot(cum_ret_21d.index, cum_ret_21d.values, label='21d/21d', linewidth=2, alpha=0.7)
    axes[1].plot(cum_ret_combined.index, cum_ret_combined.values, label='Combined', 
                linewidth=2.5, color='black', linestyle='--')
    axes[1].axhline(y=0, color='gray', linestyle='-', linewidth=1)
    axes[1].set_title('Cumulative Returns Comparison', fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Cumulative Return (%)', fontsize=12)
    axes[1].set_xlabel('Date', fontsize=12)
    axes[1].legend(loc='upper left', fontsize=10)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    print("\n" + "=" * 70)
    print("✅ TIME DIVERSIFICATION TEST COMPLETE - ALIGNED TIMEFRAMES")
    print("=" * 70)
    print("\nConclusion:")
    if sharpe > max(sharpe_50d, sharpe_21d):
        print("  ✓ Combined strategy IMPROVES Sharpe ratio")
        print("  ✓ Aligned timeframes (momentum = EMA) add value!")
        print(f"  ✓ Sharpe improved from {max(sharpe_50d, sharpe_21d):.2f} to {sharpe:.2f}")
    else:
        print("  ✗ Combined strategy does NOT improve Sharpe")
        print("  ✗ Better to stick with single timeframe")
    print("=" * 70)

