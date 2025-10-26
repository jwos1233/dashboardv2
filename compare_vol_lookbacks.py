"""
Compare Volatility Lookback Periods for Volatility Chasing Strategy
Tests 20, 30, 50, 60 day lookback periods and plots results
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import the backtest class
import sys
sys.path.append('.')
from quad_portfolio_backtest_volchase import QuadrantPortfolioBacktest

def run_comparison():
    """Run backtest for multiple volatility lookback periods"""
    
    # Configuration
    INITIAL_CAPITAL = 50000
    LOOKBACK_DAYS = 50
    EMA_PERIOD = 50
    BACKTEST_YEARS = 5
    
    # Volatility lookback periods to test
    VOL_LOOKBACKS = [20, 30, 50, 60]
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BACKTEST_YEARS * 365 + 100)
    
    print("=" * 70)
    print("VOLATILITY LOOKBACK COMPARISON - VOLATILITY CHASING STRATEGY")
    print("=" * 70)
    print(f"Testing lookback periods: {VOL_LOOKBACKS}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,}")
    print(f"Backtest Period: {start_date.date()} to {end_date.date()}")
    print("=" * 70)
    print()
    
    # Store results
    results = {}
    equity_curves = {}
    
    for vol_lookback in VOL_LOOKBACKS:
        print(f"\n{'='*70}")
        print(f"Running backtest with {vol_lookback}-day volatility lookback...")
        print(f"{'='*70}")
        
        try:
            # Run backtest
            backtest = QuadrantPortfolioBacktest(
                start_date=start_date,
                end_date=end_date,
                initial_capital=INITIAL_CAPITAL,
                momentum_days=LOOKBACK_DAYS,
                ema_period=EMA_PERIOD,
                vol_lookback=vol_lookback
            )
            
            backtest.run_backtest()
            
            # Store equity curve
            equity_curves[f"{vol_lookback}d"] = backtest.portfolio_value.copy()
            
            # Calculate metrics
            returns = backtest.portfolio_value.pct_change().dropna()
            total_return = (backtest.portfolio_value.iloc[-1] / INITIAL_CAPITAL - 1) * 100
            years = len(returns) / 252
            annual_return = ((backtest.portfolio_value.iloc[-1] / INITIAL_CAPITAL) ** (1 / years) - 1) * 100
            annual_vol = returns.std() * np.sqrt(252) * 100
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            # Drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            results[vol_lookback] = {
                'Total Return': total_return,
                'Annual Return': annual_return,
                'Volatility': annual_vol,
                'Sharpe Ratio': sharpe,
                'Max Drawdown': max_drawdown,
                'Final Value': backtest.portfolio_value.iloc[-1]
            }
            
            print(f"\n✓ {vol_lookback}d: Total Return = {total_return:.2f}%, Sharpe = {sharpe:.2f}, Max DD = {max_drawdown:.2f}%")
            
        except Exception as e:
            print(f"✗ Error with {vol_lookback}d lookback: {str(e)}")
            continue
    
    # Create comparison table
    print("\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)
    df = pd.DataFrame(results).T
    df.index.name = 'Vol Lookback'
    print(df.to_string())
    print("=" * 70)
    
    # Find best strategy for each metric
    print("\n" + "=" * 70)
    print("BEST PERFORMERS BY METRIC")
    print("=" * 70)
    for metric in df.columns:
        if metric in ['Total Return', 'Annual Return', 'Sharpe Ratio', 'Final Value']:
            best_idx = df[metric].idxmax()
        else:  # For drawdown and volatility, lower is better
            best_idx = df[metric].idxmin()
        print(f"{metric:<20} → {best_idx} days ({df.loc[best_idx, metric]:.2f})")
    print("=" * 70)
    
    # Plot results
    plot_comparison(equity_curves, results, INITIAL_CAPITAL)
    
    return results, equity_curves

def plot_comparison(equity_curves, results, initial_capital):
    """Create comprehensive comparison plots"""
    
    fig = plt.figure(figsize=(16, 10))
    
    # 1. Equity Curves (main plot)
    ax1 = plt.subplot(2, 2, 1)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    for (label, curve), color in zip(equity_curves.items(), colors):
        ax1.plot(curve.index, curve.values, label=label, linewidth=2, color=color)
    
    ax1.set_title('Equity Curves by Volatility Lookback Period', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=initial_capital, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Format y-axis
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    # 2. Total Returns Bar Chart
    ax2 = plt.subplot(2, 2, 2)
    lookbacks = [int(k.replace('d', '')) for k in equity_curves.keys()]
    total_returns = [results[lb]['Total Return'] for lb in lookbacks]
    
    bars = ax2.bar(range(len(lookbacks)), total_returns, color=colors, alpha=0.8, edgecolor='black')
    ax2.set_title('Total Return by Lookback Period', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Total Return (%)', fontsize=12)
    ax2.set_xlabel('Volatility Lookback (days)', fontsize=12)
    ax2.set_xticks(range(len(lookbacks)))
    ax2.set_xticklabels([f'{lb}d' for lb in lookbacks])
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, val in zip(bars, total_returns):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 3. Sharpe Ratio Comparison
    ax3 = plt.subplot(2, 2, 3)
    sharpe_ratios = [results[lb]['Sharpe Ratio'] for lb in lookbacks]
    
    bars = ax3.bar(range(len(lookbacks)), sharpe_ratios, color=colors, alpha=0.8, edgecolor='black')
    ax3.set_title('Sharpe Ratio by Lookback Period', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Sharpe Ratio', fontsize=12)
    ax3.set_xlabel('Volatility Lookback (days)', fontsize=12)
    ax3.set_xticks(range(len(lookbacks)))
    ax3.set_xticklabels([f'{lb}d' for lb in lookbacks])
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    # Add value labels
    for bar, val in zip(bars, sharpe_ratios):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 4. Risk Metrics Comparison
    ax4 = plt.subplot(2, 2, 4)
    max_dds = [abs(results[lb]['Max Drawdown']) for lb in lookbacks]
    vols = [results[lb]['Volatility'] for lb in lookbacks]
    
    x = np.arange(len(lookbacks))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, max_dds, width, label='Max Drawdown', 
                    color='#FF6B6B', alpha=0.8, edgecolor='black')
    bars2 = ax4.bar(x + width/2, vols, width, label='Volatility',
                    color='#4ECDC4', alpha=0.8, edgecolor='black')
    
    ax4.set_title('Risk Metrics by Lookback Period', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Percentage (%)', fontsize=12)
    ax4.set_xlabel('Volatility Lookback (days)', fontsize=12)
    ax4.set_xticks(x)
    ax4.set_xticklabels([f'{lb}d' for lb in lookbacks])
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Save figure
    filename = f'vol_lookback_comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n📊 Chart saved as: {filename}")
    
    plt.show()

if __name__ == "__main__":
    results, equity_curves = run_comparison()
    
    print("\n" + "=" * 70)
    print("✅ COMPARISON COMPLETE")
    print("=" * 70)

