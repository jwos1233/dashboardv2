"""
Macro Quadrant Portfolio Backtest - INVERTED/CONTRARIAN VERSION
================================================================

Testing Mean Reversion / Contrarian Strategy:
- Allocates to BOTTOM 2 quadrants (worst momentum) instead of top 2
- Only buys assets BELOW their 50-day EMA (fading strength) instead of above
- Same volatility chasing within quads
- Event-driven rebalancing
- 2x leverage (100% allocation to each of bottom 2 quads)

This tests if the opposite signals would work better!
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
from typing import Dict, List

warnings.filterwarnings('ignore')

# Import allocations from config
import sys
sys.path.append('.')
from config import QUAD_ALLOCATIONS, QUAD_INDICATORS


class QuadrantPortfolioBacktest:
    """Backtest portfolio allocation with INVERTED signals (contrarian approach)"""
    
    def __init__(self, start_date, end_date, initial_capital=10000, momentum_days=50, ema_period=50, vol_lookback=30):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.momentum_days = momentum_days
        self.ema_period = ema_period
        self.vol_lookback = vol_lookback
        
        self.price_data = None
        self.ema_data = None
        self.volatility_data = None
        self.returns_data = None
    
    def fetch_data(self):
        """Fetch historical price data for all tickers"""
        # Get all unique tickers from allocations and indicators
        all_tickers = set()
        for quad_allocs in QUAD_ALLOCATIONS.values():
            all_tickers.update(quad_allocs.keys())
        for quad_inds in QUAD_INDICATORS.values():
            all_tickers.update(quad_inds)
        
        # Add SPY for comparison
        all_tickers.add('SPY')
        all_tickers = sorted(list(all_tickers))
        
        print(f"Fetching data for {len(all_tickers)} tickers...")
        
        # Fetch with buffer for warmup period
        buffer_days = max(self.momentum_days, self.ema_period, self.vol_lookback) + 50
        fetch_start = self.start_date - timedelta(days=buffer_days)
        
        print(f"Period: {fetch_start.date()} to {self.end_date.date()}")
        
        # Fetch data for all tickers
        price_data = {}
        for ticker in all_tickers:
            try:
                data = yf.download(ticker, start=fetch_start, end=self.end_date, progress=False)
                
                if len(data) == 0:
                    continue
                
                # Handle different yfinance output formats
                if isinstance(data.columns, pd.MultiIndex):
                    if 'Adj Close' in data.columns.get_level_values(0):
                        prices = data['Adj Close'].iloc[:, 0] if len(data['Adj Close'].shape) > 1 else data['Adj Close']
                    else:
                        prices = data['Close'].iloc[:, 0] if len(data['Close'].shape) > 1 else data['Close']
                else:
                    if 'Adj Close' in data.columns:
                        prices = data['Adj Close']
                    else:
                        prices = data['Close']
                
                if isinstance(prices, pd.Series) and len(prices) > 0:
                    price_data[ticker] = prices
                    print(f"✓ {ticker}: {len(prices)} days")
                    
            except Exception as e:
                print(f"✗ {ticker}: {e}")
                continue
        
        # Create DataFrame
        self.price_data = pd.DataFrame(price_data)
        self.price_data = self.price_data.ffill().bfill()
        
        print(f"Loaded {len(self.price_data.columns)} tickers, {len(self.price_data)} days")
        
        # Calculate returns
        self.returns_data = self.price_data.pct_change()
        
        # Calculate EMA
        print(f"Calculating {self.ema_period}-day EMA for trend filter...")
        self.ema_data = self.price_data.ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate rolling volatility
        print(f"Calculating {self.vol_lookback}-day rolling volatility for volatility chasing...")
        self.volatility_data = self.returns_data.rolling(window=self.vol_lookback).std() * np.sqrt(252)
        
        return self.price_data
    
    def calculate_quad_scores(self):
        """Calculate momentum scores for each quadrant"""
        quad_scores = {}
        
        print(f"Calculating {self.momentum_days}-day momentum scores...")
        
        for quad, indicators in QUAD_INDICATORS.items():
            scores = []
            for ticker in indicators:
                if ticker in self.price_data.columns:
                    momentum = self.price_data[ticker].pct_change(self.momentum_days) * 100
                    scores.append(momentum)
            
            if scores:
                quad_scores[quad] = pd.concat(scores, axis=1).mean(axis=1)
            else:
                quad_scores[quad] = 0
        
        return pd.DataFrame(quad_scores)
    
    def determine_bottom_quads(self, quad_scores):
        """
        Determine BOTTOM 2 quadrants for each day (INVERTED SIGNAL)
        Instead of buying strength, we buy weakness
        """
        bottom_quads = pd.DataFrame(index=quad_scores.index)
        
        print("Determining BOTTOM 2 quadrants daily (CONTRARIAN)...")
        
        # Get BOTTOM 2 quads by score for each day
        for date in quad_scores.index:
            scores = quad_scores.loc[date].sort_values(ascending=True)  # INVERTED: ascending instead of descending
            bottom_quads.loc[date, 'Bottom1'] = scores.index[0]
            bottom_quads.loc[date, 'Bottom1_Score'] = scores.iloc[0]
            bottom_quads.loc[date, 'Bottom2'] = scores.index[1]
            bottom_quads.loc[date, 'Bottom2_Score'] = scores.iloc[1]
        
        return bottom_quads
    
    def calculate_target_weights(self, bottom_quads):
        """
        Calculate target portfolio weights with VOLATILITY CHASING
        But for BOTTOM 2 quads and assets BELOW EMA (INVERTED)
        """
        weights = pd.DataFrame(0.0, index=bottom_quads.index, columns=self.price_data.columns)
        
        print("Calculating target portfolio weights (INVERTED SIGNALS)...")
        
        for date in bottom_quads.index:
            bottom1 = bottom_quads.loc[date, 'Bottom1']
            bottom2 = bottom_quads.loc[date, 'Bottom2']
            
            final_weights = {}
            
            for quad, quad_weight in [(bottom1, 1.0), (bottom2, 1.0)]:
                quad_tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() 
                              if t in self.price_data.columns]
                
                if not quad_tickers:
                    continue
                
                # Get volatilities
                quad_vols = {}
                for ticker in quad_tickers:
                    if ticker in self.volatility_data.columns and date in self.volatility_data.index:
                        vol = self.volatility_data.loc[date, ticker]
                        if pd.notna(vol) and vol > 0:
                            quad_vols[ticker] = vol
                
                if not quad_vols:
                    continue
                
                # Volatility chasing (same as original)
                total_vol = sum(quad_vols.values())
                vol_weights = {t: (v / total_vol) * quad_weight 
                             for t, v in quad_vols.items()}
                
                # SAME EMA FILTER: only buy assets ABOVE EMA (strong trend)
                # Testing if trend filter alone can salvage weak quad momentum
                for ticker, weight in vol_weights.items():
                    if ticker in self.ema_data.columns and date in self.price_data.index:
                        price = self.price_data.loc[date, ticker]
                        ema = self.ema_data.loc[date, ticker]
                        
                        # KEEP ORIGINAL: price > EMA (strong trend)
                        if pd.notna(price) and pd.notna(ema) and price > ema:
                            if ticker in final_weights:
                                final_weights[ticker] += weight
                            else:
                                final_weights[ticker] = weight
                        # Assets below EMA are held as cash (same as original)
            
            # Set weights for this date
            for ticker, weight in final_weights.items():
                weights.loc[date, ticker] = weight
        
        return weights
    
    def simulate_portfolio(self, target_weights):
        """Simulate portfolio with event-driven rebalancing"""
        dates = target_weights.index
        portfolio_value = pd.Series(index=dates, dtype=float)
        portfolio_value.iloc[0] = self.initial_capital
        
        positions = pd.DataFrame(0.0, index=dates, columns=target_weights.columns)
        cash = pd.Series(index=dates, dtype=float)
        cash.iloc[0] = self.initial_capital
        
        prev_weights = None
        rebalance_count = 0
        
        print("Simulating portfolio with event-driven rebalancing...")
        print("  Trade triggers: (1) Bottom 2 quads change, (2) Asset EMA crossover")
        
        for i in range(len(dates)):
            date = dates[i]
            
            # Check if we need to rebalance (event-driven)
            should_rebalance = False
            if i == 0:
                should_rebalance = True
            else:
                current_weights = target_weights.loc[date]
                prev_weights_series = target_weights.iloc[i-1]
                
                # Check if allocations changed
                if not current_weights.equals(prev_weights_series):
                    should_rebalance = True
            
            if should_rebalance:
                rebalance_count += 1
                current_value = portfolio_value.iloc[i-1] if i > 0 else self.initial_capital
                
                # Calculate new positions
                for ticker in target_weights.columns:
                    weight = target_weights.loc[date, ticker]
                    if weight > 0 and ticker in self.price_data.columns:
                        price = self.price_data.loc[date, ticker]
                        if pd.notna(price) and price > 0:
                            dollar_amount = current_value * weight
                            positions.loc[date, ticker] = dollar_amount / price
                
                # Calculate cash held
                total_invested = sum([
                    positions.loc[date, ticker] * self.price_data.loc[date, ticker]
                    for ticker in target_weights.columns
                    if positions.loc[date, ticker] > 0 and ticker in self.price_data.columns
                    and pd.notna(self.price_data.loc[date, ticker])
                ])
                cash.iloc[i] = current_value - total_invested
            else:
                # Carry forward positions
                if i > 0:
                    positions.iloc[i] = positions.iloc[i-1]
                    cash.iloc[i] = cash.iloc[i-1]
            
            # Calculate portfolio value
            position_value = sum([
                positions.loc[date, ticker] * self.price_data.loc[date, ticker]
                for ticker in target_weights.columns
                if positions.loc[date, ticker] > 0 and ticker in self.price_data.columns
                and pd.notna(self.price_data.loc[date, ticker])
            ])
            portfolio_value.iloc[i] = position_value + cash.iloc[i]
        
        print(f"  Total rebalances: {rebalance_count} (out of {len(dates)} days)")
        print(f"  Rebalance frequency: {rebalance_count/len(dates)*100:.1f}%")
        
        return portfolio_value
    
    def print_performance(self, portfolio_value):
        """Print performance metrics"""
        returns = portfolio_value.pct_change().dropna()
        total_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100
        ann_return = ((portfolio_value.iloc[-1] / portfolio_value.iloc[0]) ** (252 / len(returns)) - 1) * 100
        ann_vol = returns.std() * np.sqrt(252) * 100
        sharpe = (ann_return / ann_vol) if ann_vol > 0 else 0
        
        cummax = portfolio_value.expanding().max()
        drawdown = (portfolio_value - cummax) / cummax * 100
        max_dd = drawdown.min()
        
        print("\n" + "="*70)
        print("PERFORMANCE SUMMARY (INVERTED/CONTRARIAN STRATEGY)")
        print("="*70)
        print(f"Initial Capital...................................  {self.initial_capital:>15,.2f}")
        print(f"Final Capital.....................................  {portfolio_value.iloc[-1]:>15,.2f}")
        print(f"Total Return......................................  {total_return:>14.2f}%")
        print(f"Annualized Return.................................  {ann_return:>14.2f}%")
        print(f"Annualized Volatility.............................  {ann_vol:>14.2f}%")
        print(f"Sharpe Ratio......................................  {sharpe:>14.2f}")
        print(f"Maximum Drawdown..................................  {max_dd:>14.2f}%")
        print(f"Start Date........................................  {portfolio_value.index[0].date():>20}")
        print(f"End Date..........................................  {portfolio_value.index[-1].date():>20}")
        print(f"Trading Days......................................  {len(portfolio_value):>20}")
        print("="*70)
        
        return {
            'total_return': total_return,
            'ann_return': ann_return,
            'ann_vol': ann_vol,
            'sharpe': sharpe,
            'max_dd': max_dd
        }
    
    def run(self):
        """Run the full backtest"""
        self.fetch_data()
        quad_scores = self.calculate_quad_scores()
        bottom_quads = self.determine_bottom_quads(quad_scores)
        target_weights = self.calculate_target_weights(bottom_quads)
        portfolio_value = self.simulate_portfolio(target_weights)
        metrics = self.print_performance(portfolio_value)
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(portfolio_value.index, portfolio_value.values, label='INVERTED Strategy', linewidth=2)
        plt.title('INVERTED/CONTRARIAN Strategy: Bottom 2 Quads + Below EMA', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
        
        return portfolio_value, metrics


if __name__ == "__main__":
    print("Initial Capital: $50,000")
    print("Momentum Lookback: 50 days")
    print("EMA Trend Filter: 50-day (SAME: Buy above EMA)")
    print("Volatility Lookback: 30 days")
    print("Backtest Period: ~5 years")
    print("Leverage: 2x (100% allocation to each of BOTTOM 2 quads)")
    print("Rebalancing: Event-driven (quad change or EMA crossover)")
    print("TESTING: Can trend filter salvage weak quad momentum?")
    print("="*70)
    print("QUADRANT PORTFOLIO BACKTEST - INVERTED/CONTRARIAN VERSION")
    print("="*70)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5 + 200)
    
    backtest = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=50000,
        momentum_days=50,
        ema_period=50,
        vol_lookback=30
    )
    
    portfolio_value, metrics = backtest.run()
    
    print("\n" + "="*70)
    print("✅ BACKTEST COMPLETE - PARTIAL INVERSION TEST")
    print("="*70)
    print("Tested: Bottom 2 quads (WEAK momentum) + Above EMA (STRONG trend)")
    print("  - Quadrant Selection: INVERTED (bottom 2)")
    print("  - Trend Filter: ORIGINAL (above EMA)")
    print("  - Tests if trend filter can salvage weak quad momentum")
    print("="*70)

