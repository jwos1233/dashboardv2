"""
Strategy Initialization Script
===============================

Initialize the strategy mid-stream by:
1. Running backtest to today to get current positions
2. Filtering out positions that would have been stopped
3. Entering valid positions at current price with HISTORICAL stops
4. Matching the backtest's current state exactly
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from quad_portfolio_backtest import QuadrantPortfolioBacktest
import yfinance as yf
from typing import Dict, Tuple


class StrategyInitializer:
    """Initialize strategy matching backtest's current state"""
    
    def __init__(self):
        self.backtest = None
        self.valid_positions = {}
        self.stopped_positions = {}
    
    def run_backtest_to_today(self):
        """Run backtest from start to today"""
        print("\n" + "="*80)
        print("STEP 1: RUNNING BACKTEST TO TODAY")
        print("="*80)
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Period: 2020-01-01 to {end_date}")
        print("Running backtest...")
        
        self.backtest = QuadrantPortfolioBacktest(
            start_date='2020-01-01',
            end_date=end_date,
            momentum_days=50,
            ema_period=50,
            vol_lookback=30,
            max_positions=10,
            atr_stop_loss=2.0,
            atr_period=14
        )
        
        results = self.backtest.run_backtest()
        
        print(f"\nBacktest complete:")
        print(f"  Total return: {results['total_return']:.2%}")
        print(f"  Final value: ${results['final_value']:,.2f}")
        
        return results
    
    def get_current_positions_with_stops(self) -> Dict:
        """
        Extract current positions from backtest with their historical stops
        
        Uses the stored entry_prices, entry_dates, and entry_atrs from backtest
        
        Returns dict with:
        - weight: current target weight
        - entry_price: historical entry price
        - entry_date: when position was entered
        - stop_price: historical stop level
        - atr: ATR at entry
        """
        print("\n" + "="*80)
        print("STEP 2: EXTRACTING CURRENT POSITIONS")
        print("="*80)
        
        # Get latest target weights
        latest_weights = self.backtest.target_weights.iloc[-1]
        
        # Get positions with weight > 0
        current_positions = latest_weights[latest_weights > 0]
        
        print(f"\nCurrent theoretical positions: {len(current_positions)}")
        
        # Get entry tracking from backtest
        entry_prices = self.backtest.entry_prices
        entry_dates = self.backtest.entry_dates
        entry_atrs = self.backtest.entry_atrs
        
        positions_with_stops = {}
        
        for ticker in current_positions.index:
            weight = current_positions[ticker]
            
            # Check if we have entry tracking for this position
            if ticker not in entry_prices or ticker not in entry_dates or ticker not in entry_atrs:
                print(f"  {ticker}: No entry tracking (possibly new today)")
                continue
            
            entry_price = entry_prices[ticker]
            entry_date = entry_dates[ticker]
            entry_atr = entry_atrs[ticker]
            stop_price = entry_price - (entry_atr * 2.0)
            
            print(f"  {ticker}:")
            print(f"    Weight: {weight*100:.1f}%")
            print(f"    Entry: ${entry_price:.2f} on {entry_date.date()}")
            print(f"    Stop: ${stop_price:.2f}")
            
            positions_with_stops[ticker] = {
                'weight': weight,
                'entry_price': entry_price,
                'entry_date': entry_date,
                'stop_price': stop_price,
                'atr': entry_atr
            }
        
        return positions_with_stops
    
    def _find_entry_info(self, ticker: str) -> Dict:
        """Find the most recent entry for a ticker"""
        # Get weight history for this ticker
        weight_history = self.backtest.target_weights[ticker]
        
        # Find transitions from 0 to positive (entries)
        was_zero = weight_history.shift(1).fillna(0) == 0
        became_positive = weight_history > 0
        entry_signals = was_zero & became_positive
        
        if not entry_signals.any():
            return None
        
        # Get most recent entry
        entry_dates = weight_history.index[entry_signals]
        last_entry_signal = entry_dates[-1]
        
        # Entry happens at next day's open (backtest logic)
        # But we need the entry date in our data
        entry_idx = self.backtest.target_weights.index.get_loc(last_entry_signal)
        
        # Check if there's a next day
        if entry_idx + 1 >= len(self.backtest.target_weights):
            return None
        
        entry_date = self.backtest.target_weights.index[entry_idx + 1]
        
        # Get entry price (open of next day)
        if ticker not in self.backtest.open_data.columns:
            return None
        
        entry_price = self.backtest.open_data.loc[entry_date, ticker]
        
        # Get ATR at signal date (used for stop calculation)
        if ticker not in self.backtest.atr_data.columns:
            return None
        
        atr_at_signal = self.backtest.atr_data.loc[last_entry_signal, ticker]
        
        # Calculate stop
        stop_price = entry_price - (atr_at_signal * 2.0)
        
        return {
            'entry_date': entry_date,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'atr': atr_at_signal
        }
    
    def check_stops_not_hit(self, positions_with_stops: Dict) -> Tuple[Dict, Dict]:
        """
        Filter out positions where stop was hit
        
        Returns:
        - valid_positions: positions where stop was never hit
        - stopped_positions: positions where stop was hit
        """
        print("\n" + "="*80)
        print("STEP 3: CHECKING IF STOPS WERE HIT")
        print("="*80)
        
        valid = {}
        stopped = {}
        
        for ticker, info in positions_with_stops.items():
            print(f"\nChecking {ticker}...")
            print(f"  Entry: ${info['entry_price']:.2f} on {info['entry_date'].date()}")
            print(f"  Stop: ${info['stop_price']:.2f}")
            
            # Get price history since entry
            try:
                end_date = datetime.now()
                prices = yf.download(
                    ticker,
                    start=info['entry_date'],
                    end=end_date,
                    progress=False
                )['Close']
                
                if len(prices) == 0:
                    print(f"  + No price data - assuming valid")
                    valid[ticker] = info
                    continue
                
                # Check if stop was hit
                min_price = prices.min()
                
                if min_price <= info['stop_price']:
                    print(f"  - STOPPED OUT (low: ${min_price:.2f})")
                    stopped[ticker] = info
                else:
                    print(f"  + VALID (low: ${min_price:.2f})")
                    valid[ticker] = info
                    
            except Exception as e:
                print(f"  + Error fetching data ({e}) - assuming valid")
                valid[ticker] = info
        
        print(f"\n" + "="*80)
        print(f"RESULTS:")
        print(f"  Valid positions: {len(valid)}")
        print(f"  Stopped positions: {len(stopped)}")
        print("="*80)
        
        return valid, stopped
    
    def calculate_entry_orders(self, valid_positions: Dict) -> Dict:
        """
        Calculate entry orders using:
        - Current price for entry
        - Historical stop levels (from backtest)
        """
        print("\n" + "="*80)
        print("STEP 4: CALCULATING ENTRY ORDERS")
        print("="*80)
        
        if len(valid_positions) == 0:
            print("\nNo valid positions to enter!")
            return {}
        
        # Get current prices
        tickers = list(valid_positions.keys())
        print(f"\nFetching current prices for {len(tickers)} tickers...")
        
        try:
            current_data = yf.download(tickers, period='1d', progress=False)
            
            if len(tickers) == 1:
                current_prices = {tickers[0]: current_data['Close'].iloc[-1]}
            else:
                current_prices = current_data['Close'].iloc[-1].to_dict()
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return {}
        
        print("\n" + "="*80)
        print("ENTRY ORDERS (Matching Backtest State)")
        print("="*80)
        print(f"{'Ticker':<8} {'Weight':<8} {'Entry$':<12} {'Current$':<12} {'Stop$':<12} {'Risk$':<12} {'Risk%':<10}")
        print("-"*80)
        
        entry_orders = {}
        total_risk_dollars = 0
        
        for ticker in sorted(valid_positions.keys(), 
                            key=lambda t: valid_positions[t]['weight'], 
                            reverse=True):
            info = valid_positions[ticker]
            
            if ticker not in current_prices:
                print(f"{ticker:<8} - No current price available")
                continue
            
            current_price = current_prices[ticker]
            historical_stop = info['stop_price']
            
            # Calculate risk from CURRENT price to HISTORICAL stop
            risk_dollars = current_price - historical_stop
            risk_pct = (risk_dollars / current_price) * 100
            
            print(f"{ticker:<8} {info['weight']*100:>6.1f}%  "
                  f"${info['entry_price']:>10.2f}  "
                  f"${current_price:>10.2f}  "
                  f"${historical_stop:>10.2f}  "
                  f"${risk_dollars:>10.2f}  "
                  f"{risk_pct:>8.1f}%")
            
            entry_orders[ticker] = {
                'weight': info['weight'],
                'current_price': current_price,
                'stop_price': historical_stop,
                'risk_dollars': risk_dollars,
                'risk_pct': risk_pct,
                'historical_entry': info['entry_price'],
                'entry_date_in_backtest': info['entry_date']
            }
            
            total_risk_dollars += risk_dollars * info['weight']
        
        if len(entry_orders) > 0:
            risks = [order['risk_pct'] for order in entry_orders.values()]
            print("\n" + "="*80)
            print(f"RISK ANALYSIS:")
            print(f"  Positions: {len(entry_orders)}")
            print(f"  Min risk per position: {min(risks):.1f}%")
            print(f"  Max risk per position: {max(risks):.1f}%")
            print(f"  Avg risk per position: {sum(risks)/len(risks):.1f}%")
            print(f"  Weighted portfolio risk: {total_risk_dollars:.1f}%")
            print(f"\n  Note: This matches the backtest's CURRENT risk profile")
            print(f"        (stops are static, so risk grows as positions win)")
            print("="*80)
        
        return entry_orders
    
    def run_initialization(self):
        """
        Run full initialization in dry-run mode
        
        Shows what positions to enter and where stops should be
        """
        print("\n" + "="*80)
        print("STRATEGY INITIALIZATION - DRY RUN")
        print("="*80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Mode: Analysis only (no trades)")
        print("="*80)
        
        try:
            # Step 1: Run backtest to today
            self.run_backtest_to_today()
            
            # Step 2: Get current positions with stops
            positions_with_stops = self.get_current_positions_with_stops()
            
            if len(positions_with_stops) == 0:
                print("\n+ No positions with historical entries")
                print("  This means all current positions are NEW today")
                print("  Run normal signal generation instead!")
                return None
            
            # Step 3: Check if stops were hit
            valid_positions, stopped_positions = self.check_stops_not_hit(positions_with_stops)
            
            self.valid_positions = valid_positions
            self.stopped_positions = stopped_positions
            
            # Step 4: Calculate entry orders
            entry_orders = self.calculate_entry_orders(valid_positions)
            
            # Summary
            print("\n" + "="*80)
            print("INITIALIZATION SUMMARY")
            print("="*80)
            print(f"Total theoretical positions: {len(positions_with_stops)}")
            print(f"Valid positions (enter these): {len(valid_positions)}")
            print(f"Stopped positions (skip these): {len(stopped_positions)}")
            print("="*80)
            
            if len(stopped_positions) > 0:
                print("\nPositions to SKIP (were stopped out):")
                for ticker in stopped_positions.keys():
                    print(f"  - {ticker}")
            
            if len(valid_positions) > 0:
                print("\nPositions to ENTER:")
                for ticker, order in entry_orders.items():
                    print(f"  + {ticker}: BUY at ${order['current_price']:.2f}, "
                          f"Stop at ${order['stop_price']:.2f} "
                          f"({order['risk_pct']:.1f}% risk)")
            
            print("\n" + "="*80)
            print("NEXT STEPS:")
            print("="*80)
            print("1. Review the positions above")
            print("2. If correct, use these entry orders for your live system:")
            print("   - Enter each position at current market price")
            print("   - Place stop orders at the historical stop levels shown")
            print("   - This will match your backtest's current state exactly")
            print("="*80)
            
            return entry_orders
            
        except Exception as e:
            print(f"\n+ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MACRO QUADRANT STRATEGY - INITIALIZATION ANALYZER")
    print("="*80)
    print("\nThis script will:")
    print("  1. Run backtest to today")
    print("  2. Show current theoretical positions")
    print("  3. Filter out stopped positions")
    print("  4. Calculate entry orders with historical stops")
    print("\nNo trades will be executed (dry run only)")
    print("="*80)
    
    initializer = StrategyInitializer()
    entry_orders = initializer.run_initialization()
    
    if entry_orders:
        print("\n[SUCCESS] Initialization analysis complete!")
    else:
        print("\n[DONE] Analysis complete")

