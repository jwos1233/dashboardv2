"""
Macro Quadrant Portfolio Backtest - VOLATILITY WEIGHTED VERSION
Allocates to top 2 quadrants based on momentum scoring
Assets within each quad are weighted inversely to their volatility (Risk Parity approach)
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
from typing import Dict, List

warnings.filterwarnings('ignore')

# Portfolio Allocations per Quadrant
QUAD_ALLOCATIONS = {
    'Q1': {
        'QQQ': 0.60 * 0.60,      # 60% of 60% Growth
        'ARKK': 0.60 * 0.40,     # 40% of 60% Growth
        'XLC': 0.15 * 0.50,      # 50% of 15% Consumer Disc
        'XLY': 0.15 * 0.50,      # 50% of 15% Consumer Disc
        'TLT': 0.10 * 0.50,      # 50% of 10% Bonds
        'LQD': 0.10 * 0.50,      # 50% of 10% Bonds
    },
    'Q2': {
        'XLE': 0.35 * 0.25,      # 25% of 35% Commodities
        'DBC': 0.35 * 0.25,      # 25% of 35% Commodities
        'CPER': 0.35 * 0.25,     # 25% of 35% Commodities
        'GCC': 0.35 * 0.25,      # 25% of 35% Commodities
        'XLF': 0.30 * 0.333,     # 33% of 30% Cyclicals
        'XLI': 0.30 * 0.333,     # 33% of 30% Cyclicals
        'XLB': 0.30 * 0.334,     # 34% of 30% Cyclicals
        'XOP': 0.15 * 0.50,      # 50% of 15% Energy
        'FCG': 0.15 * 0.50,      # 50% of 15% Energy
        'VNQ': 0.10 * 0.50,      # 50% of 10% Real Assets
        'PAVE': 0.10 * 0.50,     # 50% of 10% Real Assets
        'VTV': 0.10 * 0.50,      # 50% of 10% Value
        'IWD': 0.10 * 0.50,      # 50% of 10% Value
    },
    'Q3': {
        'FCG': 0.25 * 0.333,     # 33% of 25% Energy
        'XLE': 0.25 * 0.333,     # 33% of 25% Energy
        'XOP': 0.25 * 0.334,     # 34% of 25% Energy
        'GLD': 0.30 * 0.20,      # 20% of 30% Commodities
        'DBC': 0.30 * 0.20,      # 20% of 30% Commodities
        'CPER': 0.30 * 0.20,     # 20% of 30% Commodities
        'DBA': 0.30 * 0.20,      # 20% of 30% Commodities
        'REMX': 0.30 * 0.20,     # 20% of 30% Commodities
        'TIP': 0.20 * 0.50,      # 50% of 20% TIPS
        'VTIP': 0.20 * 0.50,     # 50% of 20% TIPS
        'VNQ': 0.10 * 0.50,      # 50% of 10% Real Assets
        'PAVE': 0.10 * 0.50,     # 50% of 10% Real Assets
        'XLV': 0.15 * 0.333,     # 33% of 15% Equities
        'XLU': 0.15 * 0.333,     # 33% of 15% Equities
    },
    'Q4': {
        'VGLT': 0.50 * 0.50,     # 50% of 50% Long Duration
        'IEF': 0.50 * 0.50,      # 50% of 50% Long Duration
        'LQD': 0.20 * 0.50,      # 50% of 20% IG Credit
        'MUB': 0.20 * 0.50,      # 50% of 20% IG Credit
        'XLU': 0.15 * 0.333,     # 33% of 15% Defensive
        'XLP': 0.15 * 0.333,     # 33% of 15% Defensive
        'XLV': 0.15 * 0.334,     # 34% of 15% Defensive
        # Cash allocation (15%) represented as staying in cash - no ticker
    }
}

# Quadrant indicator assets (for scoring)
QUAD_INDICATORS = {
    'Q1': ['QQQ', 'VUG', 'IWM', 'BTC-USD'],
    'Q2': ['XLE', 'DBC'],
    'Q3': ['GLD', 'LIT'],
    'Q4': ['TLT', 'XLU', 'VIXY']
}


class QuadrantPortfolioBacktest:
    """Backtest portfolio allocation based on quadrant momentum with volatility weighting"""
    
    def __init__(self, start_date, end_date, initial_capital=10000, momentum_days=50, ema_period=50, vol_lookback=60):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.momentum_days = momentum_days
        self.ema_period = ema_period
        self.vol_lookback = vol_lookback  # Volatility lookback period (60 days)
        
        self.price_data = None
        self.ema_data = None
        self.indicator_data = None
        self.volatility_data = None  # Store rolling volatility for each asset
        self.portfolio_value = None
        self.positions = None
        self.quad_history = None
        
    def fetch_data(self):
        """Fetch price data for all assets"""
        # Get all unique tickers from allocations
        all_tickers = set()
        for quad_alloc in QUAD_ALLOCATIONS.values():
            all_tickers.update(quad_alloc.keys())
        
        # Add indicator tickers
        for indicators in QUAD_INDICATORS.values():
            all_tickers.update(indicators)
        
        all_tickers = sorted(list(all_tickers))
        
        print(f"Fetching data for {len(all_tickers)} tickers...")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        price_series = []
        failed = []
        
        for ticker in all_tickers:
            try:
                df = yf.download(ticker, start=self.start_date, end=self.end_date, progress=False)
                if len(df) > 0:
                    # Extract price series - handle different yfinance return formats
                    if 'Adj Close' in df.columns:
                        series = df['Adj Close'].copy()
                    elif 'Close' in df.columns:
                        series = df['Close'].copy()
                    else:
                        # Try first column
                        series = df.iloc[:, 0].copy()
                    
                    # Ensure it's a proper Series
                    if isinstance(series, pd.DataFrame):
                        series = series.squeeze()
                    
                    if isinstance(series, pd.Series):
                        series.name = ticker
                        price_series.append(series)
                        print(f"✓ {ticker}: {len(series)} days")
                    else:
                        # Create Series from array/values
                        series = pd.Series(series.flatten() if hasattr(series, 'flatten') else series, 
                                         index=df.index, name=ticker)
                        price_series.append(series)
                        print(f"✓ {ticker}: {len(series)} days (converted)")
                else:
                    failed.append(ticker)
                    print(f"✗ {ticker}: No data")
            except Exception as e:
                failed.append(ticker)
                print(f"✗ {ticker}: {str(e)[:50]}")
        
        if failed:
            print(f"\nFailed tickers: {failed}")
        
        # Concatenate all series into a DataFrame
        if price_series:
            self.price_data = pd.concat(price_series, axis=1)
            self.price_data = self.price_data.ffill().bfill()
        else:
            raise ValueError("No price data loaded!")
        
        print(f"\nLoaded {len(self.price_data.columns)} tickers, {len(self.price_data)} days")
        
        # Calculate 50-day EMA for all tickers
        print(f"\nCalculating {self.ema_period}-day EMA for trend filter...")
        self.ema_data = pd.DataFrame(index=self.price_data.index, columns=self.price_data.columns)
        for ticker in self.price_data.columns:
            self.ema_data[ticker] = self.price_data[ticker].ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate rolling volatility for all tickers
        print(f"Calculating {self.vol_lookback}-day rolling volatility for risk parity weighting...")
        self.volatility_data = pd.DataFrame(index=self.price_data.index, columns=self.price_data.columns)
        for ticker in self.price_data.columns:
            returns = self.price_data[ticker].pct_change()
            # Annualized volatility (252 trading days)
            self.volatility_data[ticker] = returns.rolling(window=self.vol_lookback).std() * np.sqrt(252)
        
        # Forward fill NaN values in volatility (for early periods)
        self.volatility_data = self.volatility_data.ffill().bfill()
        
        return self.price_data
    
    def calculate_quad_scores(self):
        """Calculate daily quadrant scores based on momentum"""
        print(f"\nCalculating {self.momentum_days}-day momentum scores...")
        
        quad_scores = pd.DataFrame(index=self.price_data.index)
        
        for quad, indicators in QUAD_INDICATORS.items():
            scores = []
            for ticker in indicators:
                if ticker in self.price_data.columns:
                    momentum = self.price_data[ticker].pct_change(self.momentum_days) * 100
                    scores.append(momentum)
            
            if scores:
                # Average momentum across all indicators in this quad
                quad_scores[quad] = pd.concat(scores, axis=1).mean(axis=1)
            else:
                quad_scores[quad] = 0
        
        return quad_scores
    
    def determine_top_quads(self, quad_scores):
        """Determine top 2 quadrants for each day"""
        top_quads = pd.DataFrame(index=quad_scores.index)
        
        # Get top 2 quads by score for each day
        for date in quad_scores.index:
            scores = quad_scores.loc[date].sort_values(ascending=False)
            top_quads.loc[date, 'Top1'] = scores.index[0]
            top_quads.loc[date, 'Top1_Score'] = scores.iloc[0]
            top_quads.loc[date, 'Top2'] = scores.index[1]
            top_quads.loc[date, 'Top2_Score'] = scores.iloc[1]
        
        return top_quads
    
    def calculate_target_weights(self, top_quads):
        """Calculate target portfolio weights with VOLATILITY WEIGHTING and EMA filter"""
        weights = pd.DataFrame(0.0, index=top_quads.index, columns=self.price_data.columns)
        
        for date in top_quads.index:
            top1 = top_quads.loc[date, 'Top1']
            top2 = top_quads.loc[date, 'Top2']
            
            # Process each quad separately with vol weighting
            final_weights = {}
            
            for quad, quad_weight in [(top1, 1.0), (top2, 1.0)]:
                # Get tickers for this quad
                quad_tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() 
                              if t in self.price_data.columns]
                
                if not quad_tickers:
                    continue
                
                # Get volatilities for this date
                quad_vols = {}
                for ticker in quad_tickers:
                    if ticker in self.volatility_data.columns and date in self.volatility_data.index:
                        vol = self.volatility_data.loc[date, ticker]
                        if pd.notna(vol) and vol > 0:
                            quad_vols[ticker] = vol
                
                if not quad_vols:
                    continue
                
                # Calculate inverse volatility weights
                inv_vols = {t: 1.0 / v for t, v in quad_vols.items()}
                total_inv_vol = sum(inv_vols.values())
                
                # Normalize to quad_weight (1.0 for top 2 quads)
                vol_weights = {t: (iv / total_inv_vol) * quad_weight 
                             for t, iv in inv_vols.items()}
                
                # Apply EMA filter - assets below EMA get zero weight (cash)
                for ticker, weight in vol_weights.items():
                    if ticker in self.ema_data.columns and date in self.price_data.index:
                        price = self.price_data.loc[date, ticker]
                        ema = self.ema_data.loc[date, ticker]
                        
                        if pd.notna(price) and pd.notna(ema) and price > ema:
                            # Pass filter: add to final weights
                            if ticker in final_weights:
                                final_weights[ticker] += weight
                            else:
                                final_weights[ticker] = weight
                        # else: Fail filter - weight stays as cash (not redistributed)
            
            # Apply final weights to the weights DataFrame
            for ticker, weight in final_weights.items():
                weights.loc[date, ticker] = weight
        
        return weights
    
    def run_backtest(self):
        """Run the complete backtest"""
        print("=" * 70)
        print("QUADRANT PORTFOLIO BACKTEST - VOLATILITY WEIGHTED")
        print("=" * 70)
        
        # Fetch data
        self.fetch_data()
        
        # Calculate quadrant scores
        quad_scores = self.calculate_quad_scores()
        
        # Warmup period
        warmup = self.momentum_days
        quad_scores.iloc[:warmup] = np.nan
        
        # Determine top 2 quads each day
        print("\nDetermining top 2 quadrants daily...")
        top_quads = self.determine_top_quads(quad_scores.iloc[warmup:])
        self.quad_history = top_quads
        
        # Calculate target weights
        print("Calculating target portfolio weights...")
        target_weights = self.calculate_target_weights(top_quads)
        
        # Simulate portfolio with EVENT-DRIVEN rebalancing
        print("Simulating portfolio with event-driven rebalancing...")
        print("  Trade triggers: (1) Top 2 quads change, (2) Asset EMA crossover")
        
        portfolio_value = pd.Series(self.initial_capital, index=target_weights.index)
        actual_positions = pd.Series(0.0, index=target_weights.columns)  # Current holdings (in % of capital)
        
        prev_top_quads = None
        prev_ema_status = {}
        rebalance_count = 0
        
        for i in range(1, len(target_weights)):
            date = target_weights.index[i]
            prev_date = target_weights.index[i-1]
            
            # Get yesterday's target allocation (T-1 lag)
            if i >= 1:
                target_date = target_weights.index[i-1]
                current_top_quads = (top_quads.loc[target_date, 'Top1'], 
                                   top_quads.loc[target_date, 'Top2'])
                
                # Check EMA status for all tickers
                current_ema_status = {}
                for ticker in target_weights.columns:
                    if ticker in self.ema_data.columns and target_date in self.price_data.index:
                        price = self.price_data.loc[target_date, ticker]
                        ema = self.ema_data.loc[target_date, ticker]
                        if pd.notna(price) and pd.notna(ema):
                            current_ema_status[ticker] = price > ema
                
                # Determine if we need to rebalance
                should_rebalance = False
                
                if prev_top_quads is None:
                    # First day - always rebalance
                    should_rebalance = True
                elif current_top_quads != prev_top_quads:
                    # Top 2 quads changed
                    should_rebalance = True
                else:
                    # Check for EMA crossovers
                    for ticker in current_ema_status:
                        if ticker in prev_ema_status:
                            if current_ema_status[ticker] != prev_ema_status[ticker]:
                                # EMA crossover detected
                                should_rebalance = True
                                break
                
                # Execute rebalancing if triggered
                if should_rebalance:
                    actual_positions = target_weights.loc[target_date].copy()
                    rebalance_count += 1
                
                # Update tracking variables
                prev_top_quads = current_top_quads
                prev_ema_status = current_ema_status
            
            # Calculate daily P&L based on actual positions held
            daily_return = 0
            for ticker in actual_positions.index:
                if ticker in self.price_data.columns:
                    position = actual_positions[ticker]
                    if position > 0 and not pd.isna(self.price_data.loc[date, ticker]):
                        price_return = (self.price_data.loc[date, ticker] / 
                                      self.price_data.loc[prev_date, ticker] - 1)
                        daily_return += position * price_return
            
            portfolio_value.iloc[i] = portfolio_value.iloc[i-1] * (1 + daily_return)
        
        self.portfolio_value = portfolio_value
        
        print(f"  Total rebalances: {rebalance_count} (out of {len(target_weights)-1} days)")
        print(f"  Rebalance frequency: {rebalance_count / (len(target_weights)-1) * 100:.1f}%")
        
        # Generate results
        results = self.generate_results()
        
        print("\n" + "=" * 70)
        print("BACKTEST COMPLETE")
        print("=" * 70)
        
        return results
    
    def generate_results(self):
        """Generate performance statistics"""
        returns = self.portfolio_value.pct_change().dropna()
        
        total_return = (self.portfolio_value.iloc[-1] / self.initial_capital - 1) * 100
        years = len(returns) / 252
        annual_return = ((self.portfolio_value.iloc[-1] / self.initial_capital) ** (1 / years) - 1) * 100
        annual_vol = returns.std() * np.sqrt(252) * 100
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        
        # Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        results = {
            'Initial Capital': f"${self.initial_capital:,.0f}",
            'Final Capital': f"${self.portfolio_value.iloc[-1]:,.2f}",
            'Total Return': f"{total_return:.2f}%",
            'Annualized Return': f"{annual_return:.2f}%",
            'Annualized Volatility': f"{annual_vol:.2f}%",
            'Sharpe Ratio': f"{sharpe:.2f}",
            'Maximum Drawdown': f"{max_drawdown:.2f}%",
            'Start Date': self.portfolio_value.index[0].strftime('%Y-%m-%d'),
            'End Date': self.portfolio_value.index[-1].strftime('%Y-%m-%d'),
            'Trading Days': len(self.portfolio_value)
        }
        
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)
        for key, value in results.items():
            print(f"{key:.<50} {value:>18}")
        print("=" * 70)
        
        # Generate annual breakdown
        self.print_annual_breakdown(returns)
        
        # Compare to S&P 500
        self.print_spy_comparison(returns)
        
        return results
    
    def print_annual_breakdown(self, returns):
        """Print year-by-year performance breakdown"""
        print("\n" + "=" * 70)
        print("ANNUAL PERFORMANCE BREAKDOWN")
        print("=" * 70)
        
        # Group by year
        returns_by_year = returns.groupby(returns.index.year)
        pv_by_year = self.portfolio_value.groupby(self.portfolio_value.index.year)
        
        print(f"{'Year':<8} {'Return':<10} {'Sharpe':<10} {'MaxDD':<10} {'Win%':<10} {'Days':<10}")
        print("-" * 70)
        
        for year in sorted(returns_by_year.groups.keys()):
            year_returns = returns_by_year.get_group(year)
            year_pv = pv_by_year.get_group(year)
            
            # Calculate metrics for the year
            year_return = ((year_pv.iloc[-1] / year_pv.iloc[0]) - 1) * 100
            year_sharpe = (year_returns.mean() / year_returns.std() * np.sqrt(252)) if year_returns.std() > 0 else 0
            
            # Max drawdown for the year
            year_cum = (1 + year_returns).cumprod()
            year_running_max = year_cum.expanding().max()
            year_dd = ((year_cum - year_running_max) / year_running_max).min() * 100
            
            # Win rate
            year_win = (year_returns > 0).sum() / len(year_returns) * 100
            
            # Number of trading days
            year_trades = len(year_returns)
            
            print(f"{year:<8} {year_return:>8.2f}%  {year_sharpe:>8.2f}  {year_dd:>8.2f}%  {year_win:>8.1f}%  {year_trades:>8}")
        
        print("=" * 70)
    
    def print_spy_comparison(self, returns):
        """Compare performance to S&P 500 buy-and-hold"""
        print("\n" + "=" * 70)
        print("COMPARISON VS S&P 500 (SPY Buy-and-Hold)")
        print("=" * 70)
        
        try:
            # Download SPY with some buffer
            start = self.portfolio_value.index[0] - pd.Timedelta(days=10)
            end = self.portfolio_value.index[-1] + pd.Timedelta(days=1)
            spy_data = yf.download('SPY', start=start, end=end, progress=False)
            
            # Handle both single ticker and multi-ticker formats
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_prices = spy_data['Adj Close']['SPY'] if 'Adj Close' in spy_data.columns.get_level_values(0) else spy_data['Close']['SPY']
            else:
                spy_prices = spy_data['Adj Close'] if 'Adj Close' in spy_data.columns else spy_data['Close']
            
            # Forward fill to align with portfolio dates
            spy_prices = spy_prices.reindex(self.portfolio_value.index, method='ffill')
            spy_prices = spy_prices.ffill().bfill()  # Handle any remaining NaNs
            
            # Calculate SPY returns
            spy_returns = spy_prices.pct_change().fillna(0)
            spy_total_return = ((spy_prices.iloc[-1] / spy_prices.iloc[0]) - 1) * 100
            spy_annual_return = ((spy_prices.iloc[-1] / spy_prices.iloc[0]) ** (1 / (len(spy_returns) / 252)) - 1) * 100
            spy_vol = spy_returns.std() * np.sqrt(252) * 100
            spy_sharpe = (spy_returns.mean() / spy_returns.std() * np.sqrt(252)) if spy_returns.std() > 0 else 0
            
            # SPY drawdown
            spy_cum = (1 + spy_returns).cumprod()
            spy_running_max = spy_cum.expanding().max()
            spy_dd = ((spy_cum - spy_running_max) / spy_running_max).min() * 100
            
            # Get strategy metrics
            strat_total = (self.portfolio_value.iloc[-1] / self.initial_capital - 1) * 100
            strat_annual = ((self.portfolio_value.iloc[-1] / self.initial_capital) ** (1 / (len(returns) / 252)) - 1) * 100
            strat_vol = returns.std() * np.sqrt(252) * 100
            strat_sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            strat_cum = (1 + returns).cumprod()
            strat_running_max = strat_cum.expanding().max()
            strat_dd = ((strat_cum - strat_running_max) / strat_running_max).min() * 100
            
            # Print comparison table
            print(f"{'Metric':<25} {'Strategy':<15} {'SPY':<15} {'Diff':<15}")
            print("-" * 70)
            print(f"{'Total Return':<25} {strat_total:>13.2f}%  {spy_total_return:>13.2f}%  {strat_total - spy_total_return:>13.2f}%")
            print(f"{'Annualized Return':<25} {strat_annual:>13.2f}%  {spy_annual_return:>13.2f}%  {strat_annual - spy_annual_return:>13.2f}%")
            print(f"{'Volatility':<25} {strat_vol:>13.2f}%  {spy_vol:>13.2f}%  {strat_vol - spy_vol:>13.2f}%")
            print(f"{'Sharpe Ratio':<25} {strat_sharpe:>14.2f}  {spy_sharpe:>14.2f}  {strat_sharpe - spy_sharpe:>14.2f}")
            print(f"{'Max Drawdown':<25} {strat_dd:>13.2f}%  {spy_dd:>13.2f}%  {strat_dd - spy_dd:>13.2f}%")
            
            # Alpha calculation
            alpha = strat_annual - spy_annual_return
            print(f"\n{'Alpha (vs SPY)':<25} {alpha:>13.2f}%")
            print(f"{'Outperformance':<25} {strat_total - spy_total_return:>13.2f}%")
            
            print("=" * 70)
            
        except Exception as e:
            print(f"Could not compare to SPY: {e}")
            print("=" * 70)
    
    def plot_results(self):
        """Plot backtest results"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Portfolio value
        cumulative_pnl = self.portfolio_value - self.initial_capital
        axes[0].plot(cumulative_pnl.index, cumulative_pnl.values, linewidth=2, color='#2E86AB')
        axes[0].fill_between(cumulative_pnl.index, cumulative_pnl.values, 0, alpha=0.3, color='#2E86AB')
        axes[0].axhline(y=0, color='black', linestyle='-', linewidth=1)
        axes[0].set_title('Quadrant Strategy: Cumulative P/L', fontsize=16, fontweight='bold')
        axes[0].set_ylabel('Profit/Loss ($)', fontsize=12)
        axes[0].grid(True, alpha=0.3)
        
        # Add final P/L
        final_pnl = cumulative_pnl.iloc[-1]
        color = 'green' if final_pnl > 0 else 'red'
        axes[0].text(0.02, 0.98, f'Final P/L: ${final_pnl:,.2f}',
                    transform=axes[0].transAxes, fontsize=14, fontweight='bold',
                    verticalalignment='top', color=color,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Quadrant regime over time
        if self.quad_history is not None:
            quad_colors = {'Q1': '#00AA00', 'Q2': '#FF6600', 'Q3': '#CC0000', 'Q4': '#0066CC'}
            
            for i, (date, row) in enumerate(self.quad_history.iterrows()):
                top1 = row['Top1']
                axes[1].axvspan(date, self.quad_history.index[min(i+1, len(self.quad_history)-1)],
                              alpha=0.3, color=quad_colors.get(top1, 'gray'))
            
            axes[1].set_title('Primary Quadrant Over Time', fontsize=16, fontweight='bold')
            axes[1].set_ylabel('Regime', fontsize=12)
            axes[1].set_xlabel('Date', fontsize=12)
            axes[1].set_ylim(-0.5, 0.5)
            axes[1].set_yticks([])
            
            # Legend
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=quad_colors[q], alpha=0.3, label=q) 
                             for q in ['Q1', 'Q2', 'Q3', 'Q4']]
            axes[1].legend(handles=legend_elements, loc='upper left')
        
        plt.tight_layout()
        plt.show()
        print("\n📊 Chart displayed")


if __name__ == "__main__":
    """
    PRODUCTION CONFIGURATION - VOLATILITY WEIGHTED VERSION
    Risk parity approach: assets weighted inversely to their volatility
    """
    # Strategy parameters
    INITIAL_CAPITAL = 50000  # Starting capital
    LOOKBACK_DAYS = 50       # 50-day momentum for quadrant calculation
    EMA_PERIOD = 50          # 50-day EMA trend filter (OPTIMAL)
    VOL_LOOKBACK = 21        # 21-day volatility lookback for risk parity (SHORT-TERM)
    BACKTEST_YEARS = 5       # Backtest period
    
    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=BACKTEST_YEARS * 365 + 100)
    
    # Display configuration
    print(f"Initial Capital: ${INITIAL_CAPITAL:,}")
    print(f"Momentum Lookback: {LOOKBACK_DAYS} days")
    print(f"EMA Trend Filter: {EMA_PERIOD}-day (OPTIMAL)")
    print(f"Volatility Lookback: {VOL_LOOKBACK} days (Risk Parity Weighting)")
    print(f"Backtest Period: ~{BACKTEST_YEARS} years")
    print(f"Leverage: 2x (100% allocation to each of top 2 quads)")
    print(f"Weighting: Inverse volatility (equal risk contribution)")
    print(f"Rebalancing: Event-driven (quad change or EMA crossover)")
    print()
    
    # Run backtest
    backtest = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=INITIAL_CAPITAL,
        momentum_days=LOOKBACK_DAYS,
        ema_period=EMA_PERIOD,
        vol_lookback=VOL_LOOKBACK
    )
    
    results = backtest.run_backtest()
    backtest.plot_results()
    
    print("\n" + "=" * 70)
    print("✅ BACKTEST COMPLETE - VOLATILITY WEIGHTED")
    print("=" * 70)
    print("\nStrategy: Macro Quadrant Rotation - Risk Parity (Vol Weighted)")
    print("Allocation: 100% to each of top 2 quads (2x leverage)")
    print("Weighting: Inverse volatility within each quad")
    print("Filters: 50-day EMA trend + Event-driven rebalancing")
    print("=" * 70)

