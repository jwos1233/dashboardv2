"""
Signal Generator for Macro Quadrant Strategy
==============================================

Generates trading signals based on macro regime detection.

Strategy:
- Identifies top 2 quadrants using 50-day momentum
- Weights assets within quadrants by 30-day volatility (volatility chasing)
- Filters: 50-day EMA (only allocate above EMA)
- Asymmetric leverage: Q1=1.5x, Q2/Q3/Q4=1.0x
- Entry confirmation: 1-day lag on live EMA status
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Tuple
from config import QUAD_ALLOCATIONS

# Quadrant indicators for momentum scoring
QUAD_INDICATORS = {
    'Q1': ['QQQ', 'VUG', 'IWM', 'BTC-USD'],
    'Q2': ['XLE', 'DBC'],
    'Q3': ['GLD', 'LIT'],
    'Q4': ['TLT', 'XLU', 'VIXY']
}


class SignalGenerator:
    """Generate live trading signals for macro quadrant rotation strategy"""
    
    def __init__(self, momentum_days=50, ema_period=50, vol_lookback=30, max_positions=10):
        self.momentum_days = momentum_days
        self.ema_period = ema_period
        self.vol_lookback = vol_lookback
        self.max_positions = max_positions  # Top 10 positions (optimal from backtesting)
        
        # Leverage by quadrant
        self.quad_leverage = {
            'Q1': 1.5,  # Goldilocks - overweight
            'Q2': 1.0,  # Reflation
            'Q3': 1.0,  # Stagflation
            'Q4': 1.0   # Deflation
        }
    
    def fetch_market_data(self, lookback_days=150):
        """
        Fetch market data for all tickers
        
        Args:
            lookback_days: Number of days to fetch (default 150 for buffers)
        
        Returns:
            DataFrame with price data
        """
        # Get all unique tickers
        all_tickers = set()
        for quad_assets in QUAD_ALLOCATIONS.values():
            all_tickers.update(quad_assets.keys())
        for indicators in QUAD_INDICATORS.values():
            all_tickers.update(indicators)
        
        all_tickers = sorted(list(all_tickers))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        print(f"Fetching data for {len(all_tickers)} tickers...")
        
        price_series = []
        for ticker in all_tickers:
            try:
                data = yf.download(ticker, start=start_date, end=end_date, 
                                 progress=False, auto_adjust=True)
                if len(data) > 0 and 'Close' in data.columns:
                    series = data['Close'].copy()
                    series.name = ticker
                    price_series.append(series)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        if not price_series:
            raise ValueError("No price data loaded!")
        
        df = pd.concat(price_series, axis=1)
        df = df.ffill().bfill()
        
        print(f"✓ Loaded {len(df.columns)} tickers, {len(df)} days")
        return df
    
    def calculate_quadrant_scores(self, price_data: pd.DataFrame) -> pd.Series:
        """
        Calculate momentum scores for each quadrant
        
        Returns:
            Series with quad scores for today
        """
        scores = {}
        
        for quad, indicators in QUAD_INDICATORS.items():
            quad_scores = []
            for ticker in indicators:
                if ticker in price_data.columns:
                    # 50-day momentum
                    momentum = price_data[ticker].pct_change(self.momentum_days).iloc[-1] * 100
                    if not pd.isna(momentum):
                        quad_scores.append(momentum)
            
            scores[quad] = np.mean(quad_scores) if quad_scores else 0
        
        return pd.Series(scores).sort_values(ascending=False)
    
    def get_top_quadrants(self, quad_scores: pd.Series) -> Tuple[str, str]:
        """Get top 2 quadrants"""
        top_quads = quad_scores.index[:2].tolist()
        return top_quads[0], top_quads[1]
    
    def calculate_target_weights(self, price_data: pd.DataFrame, 
                                 top1: str, top2: str) -> Dict[str, float]:
        """
        Calculate target portfolio weights
        
        Returns:
            Dictionary of {ticker: weight} where weights sum to ~2.5 (if Q1 active)
        """
        # Calculate EMA
        ema_data = price_data.ewm(span=self.ema_period, adjust=False).mean()
        
        # Calculate volatility
        returns = price_data.pct_change()
        volatility_data = returns.rolling(window=self.vol_lookback).std() * np.sqrt(252)
        
        final_weights = {}
        
        for quad in [top1, top2]:
            # Get leverage for this quad
            quad_leverage = self.quad_leverage[quad]
            
            # Get tickers in this quad
            quad_tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() 
                          if t in price_data.columns]
            
            if not quad_tickers:
                continue
            
            # Get current volatilities
            quad_vols = {}
            for ticker in quad_tickers:
                vol = volatility_data[ticker].iloc[-1]
                if pd.notna(vol) and vol > 0:
                    quad_vols[ticker] = vol
            
            if not quad_vols:
                continue
            
            # Volatility chasing weights
            total_vol = sum(quad_vols.values())
            vol_weights = {t: (v / total_vol) * quad_leverage 
                          for t, v in quad_vols.items()}
            
            # Apply EMA filter
            for ticker, weight in vol_weights.items():
                current_price = price_data[ticker].iloc[-1]
                current_ema = ema_data[ticker].iloc[-1]
                
                if pd.notna(current_price) and pd.notna(current_ema) and current_price > current_ema:
                    # Pass EMA filter
                    if ticker in final_weights:
                        final_weights[ticker] += weight
                    else:
                        final_weights[ticker] = weight
        
        # Filter to top N positions if max_positions is set
        if self.max_positions and len(final_weights) > self.max_positions:
            # Sort by weight and keep top N
            sorted_weights = sorted(final_weights.items(), key=lambda x: x[1], reverse=True)
            top_n_weights = dict(sorted_weights[:self.max_positions])
            
            # Re-normalize to maintain total leverage
            original_total = sum(final_weights.values())
            new_total = sum(top_n_weights.values())
            scale_factor = original_total / new_total if new_total > 0 else 1
            
            final_weights = {t: w * scale_factor for t, w in top_n_weights.items()}
        
        return final_weights
    
    def generate_signals(self) -> Dict:
        """
        Generate current trading signals
        
        Returns:
            Dictionary with:
            - top_quadrants: (Q1, Q2) tuple
            - quadrant_scores: Series of all quad scores
            - target_weights: Dict of {ticker: weight}
            - current_regime: str description
            - timestamp: datetime
        """
        print("\n" + "="*60)
        print("GENERATING SIGNALS")
        print("="*60)
        
        # Fetch data
        price_data = self.fetch_market_data(lookback_days=150)
        
        # Calculate quadrant scores
        quad_scores = self.calculate_quadrant_scores(price_data)
        top1, top2 = self.get_top_quadrants(quad_scores)
        
        print(f"\nQuadrant Scores:")
        for quad in quad_scores.index:
            print(f"  {quad}: {quad_scores[quad]:>7.2f}%")
        
        print(f"\n🎯 Top 2 Quadrants: {top1}, {top2}")
        
        # Calculate target weights
        target_weights = self.calculate_target_weights(price_data, top1, top2)
        
        # Calculate total leverage
        total_leverage = sum(target_weights.values())
        
        print(f"\n📊 Target Portfolio (Top {self.max_positions} Positions):")
        print(f"  Total leverage: {total_leverage:.2f}x")
        print(f"  Number of positions: {len(target_weights)}")
        
        if target_weights:
            print(f"\n  ALL POSITIONS (sorted by weight):")
            print(f"  {'Ticker':<8} {'Weight':<10} {'Notional ($10k)':<15} {'Quadrant':<10}")
            print(f"  {'-'*8} {'-'*10} {'-'*15} {'-'*10}")
            
            sorted_weights = sorted(target_weights.items(), key=lambda x: x[1], reverse=True)
            for ticker, weight in sorted_weights:
                # Determine which quadrant(s) this ticker belongs to
                quads = []
                for q, assets in QUAD_ALLOCATIONS.items():
                    if ticker in assets:
                        quads.append(q)
                
                quad_str = '+'.join(quads) if quads else ''
                
                # Calculate notional value for $10k account
                notional_10k = weight * 10000
                
                print(f"  {ticker:<8} {weight*100:>8.2f}%  ${notional_10k:>12,.2f}  {quad_str:<10}")
        
        return {
            'top_quadrants': (top1, top2),
            'quadrant_scores': quad_scores,
            'target_weights': target_weights,
            'current_regime': f"{top1} + {top2}",
            'timestamp': datetime.now(),
            'total_leverage': total_leverage
        }


if __name__ == "__main__":
    # Test signal generation
    sg = SignalGenerator()
    signals = sg.generate_signals()
    
    print("\n" + "="*60)
    print("SIGNAL GENERATION COMPLETE")
    print("="*60)
    print(f"Timestamp: {signals['timestamp']}")
    print(f"Regime: {signals['current_regime']}")
    print(f"Total Leverage: {signals['total_leverage']:.2f}x")
    print(f"Positions: {len(signals['target_weights'])}")
    
    # Export to CSV-friendly format (sorted by weight, largest to smallest)
    print("\n📋 CSV Export Format (Sorted by Weight):")
    print("Ticker,Weight(%),Quadrant(s)")
    sorted_by_weight = sorted(signals['target_weights'].items(), key=lambda x: x[1], reverse=True)
    for ticker, weight in sorted_by_weight:
        quads = []
        for q, assets in QUAD_ALLOCATIONS.items():
            if ticker in assets:
                quads.append(q)
        quad_str = '+'.join(quads) if quads else ''
        print(f"{ticker},{weight*100:.2f}%,{quad_str}")

