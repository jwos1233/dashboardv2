"""
Pending Orders Manager
======================

Handles entry confirmation with 1-day lag to match backtest.

Flow:
1. Night run: Generate signals, save pending entries
2. Morning run: Confirm entries (check EMA), execute at open

This matches the backtest's 28.1% rejection rate.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf


class PendingOrdersManager:
    """
    Manages pending orders with 1-day entry confirmation
    
    Matches backtest logic:
    - Day T: Signal generated, pending entry created
    - Day T+1: Confirm EMA still valid, execute at open
    - Result: 28.1% rejection rate (as in backtest)
    """
    
    def __init__(self, pending_file='pending_entries.json'):
        """
        Initialize pending orders manager
        
        Args:
            pending_file: Path to pending orders JSON file
        """
        self.pending_file = pending_file
        self.pending_orders = self.load_pending()
    
    def load_pending(self) -> Dict:
        """Load pending orders from file"""
        if os.path.exists(self.pending_file):
            try:
                with open(self.pending_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading pending orders: {e}")
                return {'entries': {}, 'metadata': {}}
        else:
            return {'entries': {}, 'metadata': {}}
    
    def save_pending(self):
        """Save pending orders to file"""
        try:
            self.pending_orders['metadata']['last_updated'] = datetime.now().isoformat()
            with open(self.pending_file, 'w') as f:
                json.dump(self.pending_orders, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving pending orders: {e}")
    
    def add_pending_entries(self, signals: Dict, current_ema_data: Dict[str, float]):
        """
        Add new pending entries from signal generation
        
        Called during night run (after market close)
        
        Args:
            signals: Signal data with target_weights, quadrants, etc.
            current_ema_data: Dict of {ticker: current_ema_value}
        """
        today = date.today().isoformat()
        
        # Create new pending entries
        new_entries = {}
        
        for ticker, weight in signals['target_weights'].items():
            if weight > 0:
                new_entries[ticker] = {
                    'weight': weight,
                    'target_weight_pct': weight * 100,
                    'ema_at_signal': current_ema_data.get(ticker, None),
                    'signal_date': today,
                    'quadrants': self._get_ticker_quadrants(ticker, signals),
                    'atr': signals.get('atr_data', {}).get(ticker, None)
                }
        
        # Update pending orders
        self.pending_orders['entries'] = new_entries
        self.pending_orders['metadata'] = {
            'signal_date': today,
            'regime': signals.get('current_regime', ''),
            'top_quadrants': signals.get('top_quadrants', []),
            'total_positions': len(new_entries),
            'total_leverage': signals.get('total_leverage', 0)
        }
        
        self.save_pending()
        
        print(f"\n💾 Saved {len(new_entries)} pending entries for tomorrow")
        print(f"   Signal date: {today}")
        print(f"   Regime: {self.pending_orders['metadata']['regime']}")
        print(f"   Top quadrants: {self.pending_orders['metadata']['top_quadrants']}")
        
        return new_entries
    
    def confirm_and_get_entries(self, price_data: pd.DataFrame, 
                                ema_data: pd.DataFrame) -> Dict:
        """
        Confirm pending entries using current EMA data
        
        Called during morning run (before market open)
        
        Args:
            price_data: Current price data (from yfinance)
            ema_data: Current 50-day EMA data
            
        Returns:
            Dict of confirmed entries ready to execute
        """
        if not self.pending_orders['entries']:
            print("ℹ️ No pending entries to confirm")
            return {}
        
        print(f"\n{'='*70}")
        print(f"ENTRY CONFIRMATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        signal_date = self.pending_orders['metadata'].get('signal_date', 'unknown')
        print(f"Signal date: {signal_date}")
        print(f"Pending entries: {len(self.pending_orders['entries'])}")
        print()
        
        confirmed = {}
        rejected = {}
        
        for ticker, entry_data in self.pending_orders['entries'].items():
            try:
                # Get current price and EMA
                current_price = price_data[ticker].iloc[-1] if ticker in price_data else None
                current_ema = ema_data[ticker].iloc[-1] if ticker in ema_data else None
                
                if current_price is None or current_ema is None:
                    print(f"  ⚠️ {ticker}: No data available - SKIP")
                    rejected[ticker] = {**entry_data, 'reason': 'NO_DATA'}
                    continue
                
                # Check confirmation: price > EMA
                if current_price > current_ema:
                    # CONFIRMED!
                    confirmed[ticker] = {
                        **entry_data,
                        'confirmed_price': float(current_price),
                        'confirmed_ema': float(current_ema),
                        'confirmation_date': date.today().isoformat()
                    }
                    print(f"  ✅ {ticker}: ${current_price:.2f} > ${current_ema:.2f} EMA - CONFIRMED")
                else:
                    # REJECTED (dropped below EMA)
                    rejected[ticker] = {
                        **entry_data,
                        'rejected_price': float(current_price),
                        'rejected_ema': float(current_ema),
                        'reason': 'BELOW_EMA'
                    }
                    print(f"  ❌ {ticker}: ${current_price:.2f} < ${current_ema:.2f} EMA - REJECTED")
                    
            except Exception as e:
                print(f"  ⚠️ {ticker}: Error confirming - {e}")
                rejected[ticker] = {**entry_data, 'reason': f'ERROR: {e}'}
        
        # Print summary
        total = len(confirmed) + len(rejected)
        rejection_rate = (len(rejected) / total * 100) if total > 0 else 0
        
        print()
        print(f"{'='*70}")
        print(f"CONFIRMATION SUMMARY")
        print(f"{'='*70}")
        print(f"Confirmed: {len(confirmed)}")
        print(f"Rejected:  {len(rejected)}")
        print(f"Rejection rate: {rejection_rate:.1f}%")
        print(f"{'='*70}")
        
        # Log rejections
        if rejected:
            self._log_rejections(rejected)
        
        # Clear pending orders after confirmation
        self.pending_orders['entries'] = {}
        self.save_pending()
        
        return confirmed
    
    def get_current_market_data(self, tickers: List[str]) -> tuple:
        """
        Fetch current price and EMA data for confirmation
        
        Args:
            tickers: List of tickers to fetch
            
        Returns:
            (price_data, ema_data) as DataFrames
        """
        print(f"\n📊 Fetching current market data for {len(tickers)} tickers...")
        
        # Fetch last 60 days to calculate 50-day EMA
        price_data = yf.download(
            tickers,
            period='60d',
            interval='1d',
            progress=False,
            group_by='ticker'
        )
        
        # Extract close prices
        if len(tickers) == 1:
            prices = pd.DataFrame({tickers[0]: price_data['Close']})
        else:
            prices = pd.DataFrame({
                ticker: price_data[ticker]['Close'] 
                for ticker in tickers 
                if ticker in price_data
            })
        
        # Calculate 50-day EMA
        ema_data = prices.ewm(span=50, adjust=False).mean()
        
        print(f"✓ Loaded data for {len(prices.columns)} tickers")
        
        return prices, ema_data
    
    def has_pending_orders(self) -> bool:
        """Check if there are pending orders"""
        return len(self.pending_orders.get('entries', {})) > 0
    
    def get_pending_summary(self) -> Dict:
        """Get summary of pending orders"""
        return {
            'count': len(self.pending_orders.get('entries', {})),
            'signal_date': self.pending_orders.get('metadata', {}).get('signal_date', 'N/A'),
            'regime': self.pending_orders.get('metadata', {}).get('regime', 'N/A')
        }
    
    def _get_ticker_quadrants(self, ticker: str, signals: Dict) -> List[str]:
        """Get which quadrants a ticker belongs to"""
        quadrants = []
        
        # This would need to reference the config
        # For now, just return empty or use signals data if available
        return quadrants
    
    def _log_rejections(self, rejected: Dict):
        """Log rejected entries to CSV for analysis"""
        try:
            log_file = 'entry_rejections.csv'
            
            rows = []
            for ticker, data in rejected.items():
                rows.append({
                    'date': date.today().isoformat(),
                    'ticker': ticker,
                    'weight': data.get('weight', 0),
                    'reason': data.get('reason', 'UNKNOWN'),
                    'rejected_price': data.get('rejected_price', None),
                    'rejected_ema': data.get('rejected_ema', None)
                })
            
            df = pd.DataFrame(rows)
            
            # Append to CSV
            if os.path.exists(log_file):
                df.to_csv(log_file, mode='a', header=False, index=False)
            else:
                df.to_csv(log_file, mode='w', header=True, index=False)
                
        except Exception as e:
            print(f"⚠️ Error logging rejections: {e}")
    
    def clear_pending(self):
        """Clear all pending orders (use with caution!)"""
        self.pending_orders = {'entries': {}, 'metadata': {}}
        self.save_pending()
        print("✓ Cleared all pending orders")


if __name__ == "__main__":
    # Test
    manager = PendingOrdersManager()
    
    if manager.has_pending_orders():
        print("Pending orders exist!")
        print(manager.get_pending_summary())
    else:
        print("No pending orders")

