"""
Macro Quadrant Portfolio Backtest - TRUE 1-DAY ENTRY CONFIRMATION
===========================================================

Volatility Chasing Strategy with Asymmetric Leverage + TRUE 1-DAY LAG
- Allocates to top 2 quadrants based on 50-day momentum scoring (T-1 lag)
- Within-quad weighting: DIRECT volatility (higher vol = higher weight)
- 30-day volatility lookback (optimal for responsiveness vs stability)
- 50-day EMA trend filter (only allocate to assets above EMA)
- Event-driven rebalancing (quad change or EMA crossover)
- ASYMMETRIC leverage: Q1=150%, Q2/Q3/Q4=100% (moderate overweight to best quad)
- **TRUE 1-DAY LAG: Check CURRENT/TODAY's EMA for confirmation (not lagged)**

This checks live/current EMA status for entry confirmation, giving true 1-day lag
on top of the T-1 macro signal lag.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from config import QUAD_ALLOCATIONS, QUADRANT_DESCRIPTIONS

class QuadrantPortfolioBacktest:
    def __init__(self, start_date, end_date, initial_capital=50000, 
                 momentum_days=50, ema_period=50, vol_lookback=30):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.momentum_days = momentum_days
        self.ema_period = ema_period
        self.vol_lookback = vol_lookback
        
        self.price_data = None
        self.ema_data = None
        self.volatility_data = None
        self.portfolio_value = None
        self.quad_history = None
    
    def fetch_data(self):
        """Download price data for all tickers"""
        all_tickers = []
        for quad_assets in QUAD_ALLOCATIONS.values():
            all_tickers.extend(quad_assets.keys())
        all_tickers = sorted(set(all_tickers))
        
        print(f"Fetching data for {len(all_tickers)} tickers...")
        
        # Add buffer for momentum calculation
        buffer_days = max(self.momentum_days, self.ema_period, self.vol_lookback) + 10
        fetch_start = pd.to_datetime(self.start_date) - timedelta(days=buffer_days)
        
        print(f"Period: {fetch_start.date()} to {self.end_date}")
        
        price_data = {}
        for ticker in all_tickers:
            try:
                data = yf.download(ticker, start=fetch_start, end=self.end_date, 
                                 progress=False, auto_adjust=True)
                
                if isinstance(data.columns, pd.MultiIndex):
                    if 'Close' in data.columns.get_level_values(0):
                        prices = data['Close']
                else:
                    if 'Close' in data.columns:
                        prices = data['Close']
                    else:
                        continue
                
                if isinstance(prices, pd.DataFrame):
                    prices = prices.iloc[:, 0]
                
                if len(prices) > 100:
                    price_data[ticker] = prices
                    print(f"✓ {ticker}: {len(prices)} days")
                    
            except Exception as e:
                print(f"✗ {ticker}: {e}")
                continue
        
        self.price_data = pd.DataFrame(price_data)
        self.price_data = self.price_data.ffill().bfill()
        
        print(f"\nLoaded {len(self.price_data.columns)} tickers, {len(self.price_data)} days")
        
        # Calculate 50-day EMA
        print(f"Calculating {self.ema_period}-day EMA for trend filter...")
        self.ema_data = self.price_data.ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate volatility (rolling std of returns)
        print(f"Calculating {self.vol_lookback}-day rolling volatility for volatility chasing...")
        returns = self.price_data.pct_change()
        self.volatility_data = returns.rolling(window=self.vol_lookback).std() * np.sqrt(252)
    
    def calculate_quad_scores(self):
        """Calculate momentum scores for each quadrant"""
        print(f"\nCalculating {self.momentum_days}-day momentum scores...")
        
        # Calculate momentum for all assets
        momentum = self.price_data.pct_change(self.momentum_days)
        
        # Score each quadrant by average momentum of its assets
        quad_scores = pd.DataFrame(index=momentum.index)
        
        for quad, assets in QUAD_ALLOCATIONS.items():
            quad_tickers = [t for t in assets.keys() if t in momentum.columns]
            if quad_tickers:
                quad_scores[quad] = momentum[quad_tickers].mean(axis=1)
        
        return quad_scores
    
    def determine_top_quads(self, quad_scores):
        """Determine top 2 quadrants for each day"""
        top_quads = pd.DataFrame(index=quad_scores.index)
        
        for date in quad_scores.index:
            scores = quad_scores.loc[date].sort_values(ascending=False)
            top_quads.loc[date, 'Top1'] = scores.index[0]
            top_quads.loc[date, 'Top2'] = scores.index[1]
            top_quads.loc[date, 'Score1'] = scores.iloc[0]
            top_quads.loc[date, 'Score2'] = scores.iloc[1]
        
        return top_quads
    
    def calculate_target_weights(self, top_quads):
        """Calculate target portfolio weights with volatility chasing"""
        weights = pd.DataFrame(0.0, index=top_quads.index, 
                              columns=self.price_data.columns)
        
        for date in top_quads.index:
            top1 = top_quads.loc[date, 'Top1']
            top2 = top_quads.loc[date, 'Top2']
            
            # Process each quad separately with volatility weighting
            final_weights = {}
            
            # ASYMMETRIC LEVERAGE: Q1 gets 1.5x allocation, all others get 1x
            quad1_weight = 1.5 if top1 == 'Q1' else 1.0
            quad2_weight = 1.5 if top2 == 'Q1' else 1.0
            
            for quad, quad_weight in [(top1, quad1_weight), (top2, quad2_weight)]:
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
                
                # Calculate DIRECT volatility weights (higher vol = higher weight)
                direct_vols = {t: v for t, v in quad_vols.items()}
                total_vol = sum(direct_vols.values())
                
                # Normalize to quad_weight (Q1=1.5, others=1.0)
                vol_weights = {t: (v / total_vol) * quad_weight 
                             for t, v in direct_vols.items()}
                
                # Apply EMA filter - assets below EMA get zero weight (held as cash)
                for ticker, weight in vol_weights.items():
                    if ticker in self.ema_data.columns and date in self.price_data.index:
                        price = self.price_data.loc[date, ticker]
                        ema = self.ema_data.loc[date, ticker]
                        
                        if pd.notna(price) and pd.notna(ema) and price > ema:
                            # Pass EMA filter: add to final weights
                            if ticker in final_weights:
                                final_weights[ticker] += weight
                            else:
                                final_weights[ticker] = weight
            
            # Apply final weights to the weights DataFrame
            for ticker, weight in final_weights.items():
                weights.loc[date, ticker] = weight
        
        return weights
    
    def run_backtest(self):
        """Run the complete backtest with TRUE 1-day entry confirmation"""
        print("=" * 70)
        print("QUADRANT PORTFOLIO BACKTEST - TRUE 1-DAY ENTRY CONFIRMATION")
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
        
        # Simulate portfolio with EVENT-DRIVEN rebalancing + TRUE 1-DAY ENTRY LAG
        print("Simulating portfolio with TRUE 1-day entry confirmation...")
        print("  Macro signals: T-1 lag (trade yesterday's regime)")
        print("  Entry confirmation: Check TODAY's EMA (live/current)")
        print("  Exit rule: Immediate (no lag)")
        
        portfolio_value = pd.Series(self.initial_capital, index=target_weights.index)
        actual_positions = pd.Series(0.0, index=target_weights.columns)  # Current holdings
        pending_entries = {}  # {ticker: target_weight} - waiting for confirmation
        
        prev_top_quads = None
        prev_ema_status = {}
        rebalance_count = 0
        entries_confirmed = 0
        entries_rejected = 0
        
        for i in range(1, len(target_weights)):
            date = target_weights.index[i]
            prev_date = target_weights.index[i-1]
            
            # ===== CRITICAL: LAG STRUCTURE TO PREVENT FORWARD-LOOKING BIAS =====
            # MACRO SIGNALS (Quad Rankings): T-1 lag
            #   - On Day T, we trade based on Day T-1's quad rankings
            #   - This prevents forward-looking bias in regime detection
            # 
            # ENTRY CONFIRMATION (EMA Filter): T+0 (current/live)
            #   - We check TODAY's EMA to confirm entry (not yesterday's)
            #   - This is the key difference: responsive to current market
            # ===================================================================
            
            if i >= 1:
                target_date = target_weights.index[i-1]  # YESTERDAY (T-1 for quad signals)
                current_top_quads = (top_quads.loc[target_date, 'Top1'], 
                                   top_quads.loc[target_date, 'Top2'])
                
                # Check EMA status for YESTERDAY (for change detection)
                yesterday_ema_status = {}
                for ticker in target_weights.columns:
                    if ticker in self.ema_data.columns and target_date in self.price_data.index:
                        price = self.price_data.loc[target_date, ticker]
                        ema = self.ema_data.loc[target_date, ticker]
                        if pd.notna(price) and pd.notna(ema):
                            yesterday_ema_status[ticker] = price > ema
                
                # Check EMA status for TODAY (for entry confirmation) - THIS IS THE KEY DIFFERENCE!
                today_ema_status = {}
                for ticker in target_weights.columns:
                    if ticker in self.ema_data.columns and date in self.price_data.index:
                        price = self.price_data.loc[date, ticker]
                        ema = self.ema_data.loc[date, ticker]
                        if pd.notna(price) and pd.notna(ema):
                            today_ema_status[ticker] = price > ema
                
                # Get current target weights (based on yesterday's signals)
                current_targets = target_weights.loc[target_date]
                
                # Process pending entries - confirm if still above EMA TODAY
                confirmed_entries = {}
                for ticker, weight in list(pending_entries.items()):
                    # Check if STILL above EMA using TODAY's data
                    if ticker in today_ema_status and today_ema_status[ticker]:
                        # Confirmed! Enter the position
                        confirmed_entries[ticker] = weight
                        entries_confirmed += 1
                    else:
                        # Rejected - dropped below EMA
                        entries_rejected += 1
                    # Remove from pending regardless
                    del pending_entries[ticker]
                
                # Determine if we need to rebalance
                should_rebalance = False
                
                if prev_top_quads is None:
                    should_rebalance = True
                elif current_top_quads != prev_top_quads:
                    should_rebalance = True
                else:
                    # Check for EMA crossovers (using yesterday's data for consistency)
                    for ticker in yesterday_ema_status:
                        if ticker in prev_ema_status:
                            if yesterday_ema_status[ticker] != prev_ema_status[ticker]:
                                should_rebalance = True
                                break
                
                # Execute rebalancing if triggered
                if should_rebalance or len(confirmed_entries) > 0:
                    rebalance_count += 1
                    
                    # First, apply confirmed entries
                    for ticker, weight in confirmed_entries.items():
                        actual_positions[ticker] = weight
                    
                    # Now handle the rest of the rebalancing
                    for ticker in target_weights.columns:
                        target_weight = current_targets[ticker]
                        current_position = actual_positions[ticker]
                        
                        if target_weight == 0 and current_position > 0:
                            # Exit immediately (no lag)
                            actual_positions[ticker] = 0
                        elif target_weight > 0 and current_position == 0:
                            # New entry - add to pending (wait for confirmation using TOMORROW's EMA)
                            if ticker not in confirmed_entries:  # Don't re-add if just confirmed
                                pending_entries[ticker] = target_weight
                        elif target_weight > 0 and current_position > 0:
                            # Already holding - adjust position immediately
                            actual_positions[ticker] = target_weight
                
                # Update tracking variables (use yesterday's for consistency in change detection)
                prev_top_quads = current_top_quads
                prev_ema_status = yesterday_ema_status
            
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
        print(f"  Entries confirmed: {entries_confirmed}")
        print(f"  Entries rejected: {entries_rejected}")
        print(f"  Rejection rate: {entries_rejected / (entries_confirmed + entries_rejected) * 100:.1f}%")
        
        # Generate results
        results = self.generate_results()
        
        print("\n" + "=" * 70)
        print("BACKTEST COMPLETE")
        print("=" * 70)
        
        return results
    
    def generate_results(self):
        """Calculate performance metrics"""
        total_return = (self.portfolio_value.iloc[-1] / self.initial_capital - 1) * 100
        
        daily_returns = self.portfolio_value.pct_change().dropna()
        annual_return = ((1 + daily_returns.mean()) ** 252 - 1) * 100
        annual_vol = daily_returns.std() * np.sqrt(252) * 100
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0
        
        cummax = self.portfolio_value.expanding().max()
        drawdown = (self.portfolio_value - cummax) / cummax * 100
        max_drawdown = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_vol': annual_vol,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'final_value': self.portfolio_value.iloc[-1]
        }
    
    def print_annual_breakdown(self):
        """Print annual performance breakdown"""
        returns = self.portfolio_value.pct_change()
        
        print("\n" + "=" * 70)
        print("ANNUAL PERFORMANCE BREAKDOWN")
        print("=" * 70)
        print(f"{'Year':<8}{'Return':<12}{'Sharpe':<12}{'MaxDD':<12}{'Win%':<12}{'Days':<8}")
        print("-" * 70)
        
        for year in returns.index.year.unique():
            year_returns = returns[returns.index.year == year]
            
            if len(year_returns) < 10:
                continue
            
            year_return = (1 + year_returns).prod() - 1
            year_sharpe = year_returns.mean() / year_returns.std() * np.sqrt(252) if year_returns.std() > 0 else 0
            
            year_values = self.portfolio_value[self.portfolio_value.index.year == year]
            year_cummax = year_values.expanding().max()
            year_dd = ((year_values - year_cummax) / year_cummax).min()
            
            win_rate = (year_returns > 0).sum() / len(year_returns)
            
            print(f"{year:<8}{year_return*100:>10.2f}%  {year_sharpe:>10.2f}  "
                  f"{year_dd*100:>10.2f}%  {win_rate*100:>10.1f}%  {len(year_returns):>6}")
        
        print("=" * 70)
    
    def print_spy_comparison(self):
        """Compare strategy to SPY buy-and-hold"""
        # Download SPY data with a buffer
        spy_start = self.portfolio_value.index[0] - timedelta(days=5)
        spy_end = self.portfolio_value.index[-1] + timedelta(days=1)
        
        try:
            spy_data = yf.download('SPY', start=spy_start, end=spy_end, progress=False)
            
            if isinstance(spy_data.columns, pd.MultiIndex):
                spy_prices = spy_data['Close'].iloc[:, 0] if isinstance(spy_data['Close'], pd.DataFrame) else spy_data['Close']
            else:
                spy_prices = spy_data['Close']
            
            # Align SPY with portfolio dates
            spy_prices = spy_prices.reindex(self.portfolio_value.index, method='ffill').fillna(method='bfill')
            
            # Calculate SPY returns
            spy_returns = spy_prices.pct_change().dropna()
            spy_total_return = (spy_prices.iloc[-1] / spy_prices.iloc[0] - 1) * 100
            spy_annual_return = ((1 + spy_returns.mean()) ** 252 - 1) * 100
            spy_vol = spy_returns.std() * np.sqrt(252) * 100
            spy_sharpe = spy_annual_return / spy_vol if spy_vol > 0 else 0
            
            spy_cummax = spy_prices.expanding().max()
            spy_dd = ((spy_prices - spy_cummax) / spy_cummax * 100).min()
            
            # Strategy metrics
            strat_returns = self.portfolio_value.pct_change().dropna()
            strat_total = (self.portfolio_value.iloc[-1] / self.portfolio_value.iloc[0] - 1) * 100
            strat_annual = ((1 + strat_returns.mean()) ** 252 - 1) * 100
            strat_vol = strat_returns.std() * np.sqrt(252) * 100
            strat_sharpe = strat_annual / strat_vol if strat_vol > 0 else 0
            
            strat_cummax = self.portfolio_value.expanding().max()
            strat_dd = ((self.portfolio_value - strat_cummax) / strat_cummax * 100).min()
            
            print("\n" + "=" * 70)
            print("COMPARISON VS S&P 500 (SPY Buy-and-Hold)")
            print("=" * 70)
            print(f"{'Metric':<30}{'Strategy':>15}{'SPY':>15}{'Diff':>15}")
            print("-" * 70)
            print(f"{'Total Return':<30}{strat_total:>14.2f}%{spy_total_return:>14.2f}%{strat_total-spy_total_return:>14.2f}%")
            print(f"{'Annualized Return':<30}{strat_annual:>14.2f}%{spy_annual_return:>14.2f}%{strat_annual-spy_annual_return:>14.2f}%")
            print(f"{'Volatility':<30}{strat_vol:>14.2f}%{spy_vol:>14.2f}%{strat_vol-spy_vol:>14.2f}%")
            print(f"{'Sharpe Ratio':<30}{strat_sharpe:>15.2f}{spy_sharpe:>15.2f}{strat_sharpe-spy_sharpe:>15.2f}")
            print(f"{'Max Drawdown':<30}{strat_dd:>14.2f}%{spy_dd:>14.2f}%{strat_dd-spy_dd:>14.2f}%")
            print()
            print(f"{'Alpha (vs SPY)':<30}{strat_annual-spy_annual_return:>14.2f}%")
            print(f"{'Outperformance':<30}{strat_total-spy_total_return:>14.2f}%")
            print("=" * 70)
            
        except Exception as e:
            print(f"\nCould not compare to SPY: {e}")
    
    def plot_results(self):
        """Plot portfolio performance"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Portfolio value
        ax1.plot(self.portfolio_value.index, self.portfolio_value.values, 
                linewidth=2, color='purple', label='Portfolio Value')
        ax1.set_title('Portfolio Performance - TRUE 1-Day Entry Confirmation', 
                     fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Drawdown
        cummax = self.portfolio_value.expanding().max()
        drawdown = (self.portfolio_value - cummax) / cummax * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                        alpha=0.3, color='red', label='Drawdown')
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.show()
        
        print("\n" + "=" * 70)
        print("📊 Chart displayed")
        print("=" * 70)


if __name__ == "__main__":
    # Configuration
    INITIAL_CAPITAL = 50000
    LOOKBACK_DAYS = 50
    EMA_PERIOD = 50
    VOL_LOOKBACK = 30
    BACKTEST_YEARS = 5
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * BACKTEST_YEARS + 200)
    
    print("\n" + "=" * 70)
    print("TRUE 1-DAY ENTRY CONFIRMATION TEST")
    print("=" * 70)
    print(f"Initial Capital: ${INITIAL_CAPITAL:,}")
    print(f"Momentum Lookback: {LOOKBACK_DAYS} days")
    print(f"EMA Trend Filter: {EMA_PERIOD}-day")
    print(f"Volatility Lookback: {VOL_LOOKBACK} days")
    print(f"Backtest Period: ~{BACKTEST_YEARS} years")
    print(f"Leverage: ASYMMETRIC (Q1=150%, Q2/Q3/Q4=100% each)")
    print(f"Entry Rule: Check CURRENT/TODAY's EMA (live data)")
    print("=" * 70)
    print()
    
    # Run backtest
    backtest = QuadrantPortfolioBacktest(start_date, end_date, INITIAL_CAPITAL, 
                                         LOOKBACK_DAYS, EMA_PERIOD, VOL_LOOKBACK)
    results = backtest.run_backtest()
    
    # Print results
    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    print(f"Initial Capital...................................  ${INITIAL_CAPITAL:>12,}")
    print(f"Final Capital.....................................  ${results['final_value']:>12,.2f}")
    print(f"Total Return......................................  {results['total_return']:>12.2f}%")
    print(f"Annualized Return.................................  {results['annual_return']:>12.2f}%")
    print(f"Annualized Volatility.............................  {results['annual_vol']:>12.2f}%")
    print(f"Sharpe Ratio......................................  {results['sharpe']:>12.2f}")
    print(f"Maximum Drawdown..................................  {results['max_drawdown']:>12.2f}%")
    print(f"Start Date........................................  {backtest.portfolio_value.index[0].strftime('%Y-%m-%d'):>15}")
    print(f"End Date..........................................  {backtest.portfolio_value.index[-1].strftime('%Y-%m-%d'):>15}")
    print(f"Trading Days......................................  {len(backtest.portfolio_value):>15,}")
    print("=" * 70)
    
    # Annual breakdown
    backtest.print_annual_breakdown()
    
    # SPY comparison
    backtest.print_spy_comparison()
    
    backtest.plot_results()
    
    print("\n" + "=" * 70)
    print("✅ TRUE 1-DAY ENTRY CONFIRMATION TEST COMPLETE")
    print("=" * 70)
    print("\nStrategy: Check CURRENT EMA for entry confirmation (not lagged)")
    print("Key Feature: Quad signals use T-1 lag (prevent forward-looking)")
    print("             Entry confirmation uses T+0 (current/live EMA)")
    print("=" * 70)

