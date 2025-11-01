"""
Backtest Analysis Tool
======================

Analyze the backtest to understand:
1. Rolling allocations over time
2. Return attribution by asset
3. Which products contributed most to returns
4. Position frequency and duration
5. Win rates by asset
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from quad_portfolio_backtest import QuadrantPortfolioBacktest
import warnings
warnings.filterwarnings('ignore')


class BacktestAnalyzer:
    """Analyze backtest performance and attribution"""
    
    def __init__(self):
        self.backtest = None
        self.results = None
    
    def run_backtest(self):
        """Run the backtest"""
        print("\n" + "="*80)
        print("RUNNING BACKTEST FOR ANALYSIS")
        print("="*80)
        
        self.backtest = QuadrantPortfolioBacktest(
            start_date='2020-01-01',
            end_date='2024-12-31',
            momentum_days=50,
            ema_period=50,
            vol_lookback=30,
            max_positions=10,
            atr_stop_loss=2.0,
            atr_period=14
        )
        
        self.results = self.backtest.run_backtest()
        
        print(f"\n+ Backtest complete: {self.results['total_return']:.2%} return")
        
        return self.results
    
    def analyze_position_frequency(self):
        """Analyze how often each asset was held"""
        print("\n" + "="*80)
        print("POSITION FREQUENCY ANALYSIS")
        print("="*80)
        
        target_weights = self.backtest.target_weights
        
        # Count days held for each asset
        days_held = {}
        total_weight = {}
        max_weight = {}
        
        for ticker in target_weights.columns:
            weights = target_weights[ticker]
            days_held[ticker] = (weights > 0).sum()
            total_weight[ticker] = weights.sum()
            max_weight[ticker] = weights.max()
        
        # Create summary DataFrame
        freq_data = []
        for ticker in days_held.keys():
            avg_weight = total_weight[ticker] / days_held[ticker] if days_held[ticker] > 0 else 0
            freq_pct = days_held[ticker] / len(target_weights) * 100
            
            freq_data.append({
                'Ticker': ticker,
                'Days Held': days_held[ticker],
                'Total Weight': total_weight[ticker],
                'Avg Weight When Held': avg_weight,
                'Max Weight': max_weight[ticker],
                'Frequency %': freq_pct
            })
        
        freq_df = pd.DataFrame(freq_data)
        freq_df = freq_df.set_index('Ticker')
        
        # Sort by days held
        freq_df = freq_df.sort_values('Days Held', ascending=False)
        
        print(f"\n{'Ticker':<8} {'Days':<8} {'Freq %':<10} {'Avg Wt':<10} {'Max Wt':<10}")
        print("-"*80)
        
        for ticker, row in freq_df.head(15).iterrows():
            if row['Days Held'] > 0:
                print(f"{ticker:<8} {row['Days Held']:>6.0f}  "
                      f"{row['Frequency %']:>7.1f}%  "
                      f"{row['Avg Weight When Held']:>7.1%}  "
                      f"{row['Max Weight']:>7.1%}")
        
        return freq_df
    
    def calculate_return_attribution(self):
        """Calculate which assets contributed most to returns"""
        print("\n" + "="*80)
        print("RETURN ATTRIBUTION ANALYSIS")
        print("="*80)
        
        target_weights = self.backtest.target_weights
        price_data = self.backtest.price_data
        
        # Calculate daily returns for each asset
        asset_returns = price_data.pct_change()
        
        # Calculate contribution: weight × return
        contributions = pd.DataFrame(index=target_weights.index)
        
        for ticker in target_weights.columns:
            # Use yesterday's weight (what you held) × today's return
            weights_shifted = target_weights[ticker].shift(1).fillna(0)
            contributions[ticker] = weights_shifted * asset_returns[ticker]
        
        # Sum contributions over time
        total_contribution = contributions.sum()
        
        # Calculate cumulative returns per asset
        cumulative_contribution = contributions.cumsum()
        
        # Sort by total contribution
        attribution_df = pd.DataFrame({
            'Total Contribution': total_contribution,
            'Total Contribution %': total_contribution * 100,
            'Days Held': (target_weights > 0).sum(),
            'Avg Daily Contrib': total_contribution / ((target_weights > 0).sum()).replace(0, np.nan)
        })
        
        attribution_df = attribution_df.sort_values('Total Contribution', ascending=False)
        
        print(f"\n{'Ticker':<8} {'Total Return':<15} {'Return %':<12} {'Days':<8} {'Avg Daily':<12}")
        print("-"*80)
        
        for ticker, row in attribution_df.head(20).iterrows():
            if row['Total Contribution'] != 0:
                print(f"{ticker:<8} {row['Total Contribution']:>13.4f}  "
                      f"{row['Total Contribution %']:>9.2f}%  "
                      f"{row['Days Held']:>6.0f}  "
                      f"{row['Avg Daily Contrib']:>10.4f}")
        
        # Show winners vs losers
        winners = attribution_df[attribution_df['Total Contribution'] > 0]
        losers = attribution_df[attribution_df['Total Contribution'] < 0]
        
        print(f"\n{'='*80}")
        print(f"SUMMARY:")
        print(f"  Winners: {len(winners)} assets")
        print(f"  Total positive contribution: {winners['Total Contribution'].sum():.2%}")
        print(f"\n  Losers: {len(losers)} assets")
        print(f"  Total negative contribution: {losers['Total Contribution'].sum():.2%}")
        print(f"\n  Net contribution: {attribution_df['Total Contribution'].sum():.2%}")
        print(f"{'='*80}")
        
        return attribution_df, contributions
    
    def analyze_position_timeline(self):
        """Show position history over time"""
        print("\n" + "="*80)
        print("POSITION TIMELINE (Last 60 Days)")
        print("="*80)
        
        target_weights = self.backtest.target_weights
        
        # Get last 60 days
        recent_weights = target_weights.iloc[-60:]
        
        print(f"\nDate range: {recent_weights.index[0].date()} to {recent_weights.index[-1].date()}")
        
        # Find which assets were held
        held_assets = recent_weights.columns[(recent_weights > 0).any()]
        
        print(f"Assets held in last 60 days: {len(held_assets)}\n")
        
        # Show each asset's weight over time
        for ticker in held_assets:
            weights = recent_weights[ticker]
            nonzero_weights = weights[weights > 0]
            
            if len(nonzero_weights) > 0:
                print(f"{ticker}:")
                print(f"  Days held: {len(nonzero_weights)}")
                print(f"  Avg weight: {nonzero_weights.mean():.1%}")
                print(f"  Max weight: {nonzero_weights.max():.1%}")
                print(f"  Date range: {nonzero_weights.index[0].date()} to {nonzero_weights.index[-1].date()}")
        
        return recent_weights
    
    def plot_allocation_over_time(self, save_path='allocation_history.png'):
        """Plot stacked area chart of allocations over time"""
        print("\n" + "="*80)
        print("CREATING ALLOCATION CHART")
        print("="*80)
        
        target_weights = self.backtest.target_weights
        
        # Get top 15 most frequently held assets
        freq = (target_weights > 0).sum().sort_values(ascending=False)
        top_assets = freq.head(15).index
        
        # Create DataFrame with just top assets
        plot_data = target_weights[top_assets].copy()
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        
        # Plot 1: Stacked area chart
        plot_data.plot.area(ax=ax1, alpha=0.7, linewidth=0)
        ax1.set_title('Position Allocation Over Time (Top 15 Assets)', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Allocation (fraction of portfolio)', fontsize=11, fontweight='bold')
        ax1.legend(loc='upper left', bbox_to_anchor=(1, 1), ncol=1)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, None)
        
        # Plot 2: Total leverage over time
        total_leverage = target_weights.sum(axis=1)
        ax2.plot(total_leverage.index, total_leverage.values, 
                linewidth=2, color='darkblue')
        ax2.axhline(y=1.0, color='gray', linestyle='--', linewidth=1, label='1.0x Leverage')
        ax2.axhline(y=1.5, color='red', linestyle='--', linewidth=1, label='1.5x Leverage')
        ax2.fill_between(total_leverage.index, 0, total_leverage.values, 
                        alpha=0.3, color='blue')
        ax2.set_title('Total Portfolio Leverage Over Time', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Leverage', fontsize=11, fontweight='bold')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, None)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"+ Chart saved to: {save_path}")
        plt.show()
    
    def plot_return_attribution(self, contributions, save_path='return_attribution.png'):
        """Plot return attribution chart"""
        print("\n" + "="*80)
        print("CREATING RETURN ATTRIBUTION CHART")
        print("="*80)
        
        # Calculate cumulative contribution
        cumulative = contributions.cumsum()
        
        # Get top 10 contributors
        total_contrib = contributions.sum().sort_values(ascending=False)
        top_contributors = total_contrib.head(10).index
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Cumulative contribution over time
        for ticker in top_contributors:
            ax1.plot(cumulative.index, cumulative[ticker] * 100, 
                    label=ticker, linewidth=2)
        
        ax1.set_title('Cumulative Return Contribution by Asset (Top 10)', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Cumulative Return (%)', fontsize=11, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Total contribution bar chart
        total_contrib_top = total_contrib.head(15)
        colors = ['green' if x > 0 else 'red' for x in total_contrib_top]
        
        ax2.barh(range(len(total_contrib_top)), total_contrib_top * 100, color=colors, alpha=0.7)
        ax2.set_yticks(range(len(total_contrib_top)))
        ax2.set_yticklabels(total_contrib_top.index)
        ax2.set_xlabel('Total Return Contribution (%)', fontsize=11, fontweight='bold')
        ax2.set_title('Top 15 Assets by Return Contribution', 
                     fontsize=14, fontweight='bold')
        ax2.axvline(x=0, color='black', linewidth=1)
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, val in enumerate(total_contrib_top * 100):
            ax2.text(val, i, f' {val:.1f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"+ Chart saved to: {save_path}")
        plt.show()
    
    def analyze_winners_vs_losers(self, contributions):
        """Analyze winning vs losing trades"""
        print("\n" + "="*80)
        print("WINNING vs LOSING TRADES ANALYSIS")
        print("="*80)
        
        # For each asset, count winning vs losing days
        results = {}
        
        for ticker in contributions.columns:
            daily_contrib = contributions[ticker]
            
            # Only count days when position was held (non-zero contribution)
            held_days = daily_contrib[daily_contrib != 0]
            
            if len(held_days) > 0:
                wins = (held_days > 0).sum()
                losses = (held_days < 0).sum()
                win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
                
                avg_win = held_days[held_days > 0].mean() if wins > 0 else 0
                avg_loss = held_days[held_days < 0].mean() if losses > 0 else 0
                
                total_return = held_days.sum()
                
                results[ticker] = {
                    'Days Held': len(held_days),
                    'Winning Days': wins,
                    'Losing Days': losses,
                    'Win Rate %': win_rate,
                    'Avg Win': avg_win,
                    'Avg Loss': avg_loss,
                    'Total Return': total_return
                }
        
        results_df = pd.DataFrame(results).T
        results_df = results_df.sort_values('Total Return', ascending=False)
        
        print(f"\n{'Ticker':<8} {'Days':<8} {'Win%':<8} {'Wins':<8} {'Losses':<8} {'Total Return':<15}")
        print("-"*80)
        
        for ticker, row in results_df.head(20).iterrows():
            print(f"{ticker:<8} {row['Days Held']:>6.0f}  "
                  f"{row['Win Rate %']:>6.1f}%  "
                  f"{row['Winning Days']:>6.0f}  "
                  f"{row['Losing Days']:>6.0f}  "
                  f"{row['Total Return']:>13.2%}")
        
        # Overall stats
        print(f"\n{'='*80}")
        print("PORTFOLIO-LEVEL STATS:")
        print(f"  Avg win rate across assets: {results_df['Win Rate %'].mean():.1f}%")
        print(f"  Best performer: {results_df.index[0]} ({results_df['Total Return'].iloc[0]:.2%})")
        print(f"  Worst performer: {results_df.index[-1]} ({results_df['Total Return'].iloc[-1]:.2%})")
        print(f"{'='*80}")
        
        return results_df
    
    def analyze_quadrant_performance(self):
        """Analyze performance by quadrant"""
        print("\n" + "="*80)
        print("QUADRANT PERFORMANCE ANALYSIS")
        print("="*80)
        
        from config import QUAD_ALLOCATIONS
        
        target_weights = self.backtest.target_weights
        price_data = self.backtest.price_data
        
        # Calculate returns
        asset_returns = price_data.pct_change()
        
        # Calculate weighted contributions
        contributions = pd.DataFrame(index=target_weights.index)
        for ticker in target_weights.columns:
            weights_shifted = target_weights[ticker].shift(1).fillna(0)
            contributions[ticker] = weights_shifted * asset_returns[ticker]
        
        # Aggregate by quadrant
        quad_contrib = {}
        
        for quad, assets in QUAD_ALLOCATIONS.items():
            quad_tickers = [t for t in assets.keys() if t in contributions.columns]
            if quad_tickers:
                quad_contrib[quad] = contributions[quad_tickers].sum(axis=1)
        
        quad_df = pd.DataFrame(quad_contrib)
        total_quad_contrib = quad_df.sum()
        
        print(f"\n{'Quadrant':<12} {'Total Contribution':<20} {'Days Active':<15}")
        print("-"*80)
        
        for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
            if quad in total_quad_contrib:
                days_active = (quad_df[quad] != 0).sum()
                print(f"{quad:<12} {total_quad_contrib[quad]:>18.2%}  {days_active:>13.0f}")
        
        return quad_df, total_quad_contrib
    
    def create_comprehensive_report(self):
        """Create comprehensive analysis report"""
        print("\n" + "="*80)
        print("GENERATING COMPREHENSIVE BACKTEST ANALYSIS")
        print("="*80)
        
        # Run all analyses
        freq_df = self.analyze_position_frequency()
        attribution_df, contributions = self.calculate_return_attribution()
        win_loss_df = self.analyze_winners_vs_losers(contributions)
        quad_df, quad_contrib = self.analyze_quadrant_performance()
        recent_weights = self.analyze_position_timeline()
        
        # Create plots
        self.plot_allocation_over_time()
        self.plot_return_attribution(contributions)
        
        # Save detailed report to file
        self.save_detailed_report(freq_df, attribution_df, win_loss_df, quad_contrib)
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print("Files created:")
        print("  - backtest_analysis_report.txt")
        print("  - allocation_history.png")
        print("  - return_attribution.png")
        print("="*80)
    
    def save_detailed_report(self, freq_df, attribution_df, win_loss_df, quad_contrib):
        """Save detailed analysis to text file"""
        filename = 'backtest_analysis_report.txt'
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MACRO QUADRANT STRATEGY - BACKTEST ANALYSIS REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Period: 2020-01-01 to 2024-12-31\n")
            f.write(f"Total Return: {self.results['total_return']:.2%}\n")
            f.write(f"Annual Return: {self.results['annual_return']:.2%}\n")
            f.write(f"Sharpe Ratio: {self.results['sharpe']:.2f}\n")
            f.write(f"Max Drawdown: {self.results['max_drawdown']:.2%}\n")
            f.write("="*80 + "\n\n")
            
            # Position frequency
            f.write("POSITION FREQUENCY (Top 20):\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Ticker':<8} {'Days':<8} {'Freq %':<10} {'Avg Wt':<10} {'Max Wt':<10}\n")
            f.write("-"*80 + "\n")
            
            for ticker, row in freq_df.head(20).iterrows():
                if row['Days Held'] > 0:
                    f.write(f"{ticker:<8} {row['Days Held']:>6.0f}  "
                           f"{row['Frequency %']:>7.1f}%  "
                           f"{row['Avg Weight When Held']:>7.1%}  "
                           f"{row['Max Weight']:>7.1%}\n")
            
            # Return attribution
            f.write("\n" + "="*80 + "\n")
            f.write("RETURN ATTRIBUTION (Top 20):\n")
            f.write("="*80 + "\n")
            f.write(f"{'Ticker':<8} {'Total Return':<15} {'Return %':<12} {'Days':<8}\n")
            f.write("-"*80 + "\n")
            
            for ticker, row in attribution_df.head(20).iterrows():
                if row['Total Contribution'] != 0:
                    f.write(f"{ticker:<8} {row['Total Contribution']:>13.4f}  "
                           f"{row['Total Contribution %']:>9.2f}%  "
                           f"{row['Days Held']:>6.0f}\n")
            
            # Winners vs losers
            winners = attribution_df[attribution_df['Total Contribution'] > 0]
            losers = attribution_df[attribution_df['Total Contribution'] < 0]
            
            f.write("\n" + "="*80 + "\n")
            f.write("WINNERS vs LOSERS:\n")
            f.write("="*80 + "\n")
            f.write(f"Winners: {len(winners)} assets\n")
            f.write(f"Total positive: {winners['Total Contribution'].sum():.2%}\n")
            f.write(f"\nLosers: {len(losers)} assets\n")
            f.write(f"Total negative: {losers['Total Contribution'].sum():.2%}\n")
            f.write(f"\nNet: {attribution_df['Total Contribution'].sum():.2%}\n")
            
            # Quadrant performance
            f.write("\n" + "="*80 + "\n")
            f.write("QUADRANT PERFORMANCE:\n")
            f.write("="*80 + "\n")
            for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
                if quad in quad_contrib:
                    f.write(f"{quad}: {quad_contrib[quad]:>8.2%}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("KEY INSIGHTS:\n")
            f.write("="*80 + "\n")
            f.write(f"1. Most held asset: {freq_df.index[0]} ({freq_df['Days Held'].iloc[0]:.0f} days)\n")
            f.write(f"2. Best performer: {attribution_df.index[0]} ({attribution_df['Total Contribution'].iloc[0]:.2%})\n")
            f.write(f"3. Avg position win rate: {win_loss_df['Win Rate %'].mean():.1f}%\n")
            f.write(f"4. Top quadrant: {quad_contrib.idxmax()} ({quad_contrib.max():.2%})\n")
            f.write("="*80 + "\n")
        
        print(f"+ Report saved to: {filename}")


def run_full_analysis():
    """Run complete backtest analysis"""
    analyzer = BacktestAnalyzer()
    
    # Run backtest
    analyzer.run_backtest()
    
    # Run all analyses
    analyzer.create_comprehensive_report()
    
    print("\n[SUCCESS] Complete backtest analysis finished!")


if __name__ == "__main__":
    run_full_analysis()

