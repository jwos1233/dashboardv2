"""
Macro Quadrant Analyzer
Calculates current market regime based on asset momentum
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from config import CORE_ASSETS, QUADRANT_DESCRIPTIONS, MOMENTUM_LOOKBACK_DAYS

@dataclass
class AssetClassification:
    """Define asset classification for quadrant analysis"""
    symbol: str
    name: str
    primary_quadrant: str
    secondary_quadrant: str = None
    asset_type: str = ""
    weight: float = 1.0

class QuadrantAnalyzer:
    def __init__(self, lookback_days: int = None):
        self.lookback_days = lookback_days or MOMENTUM_LOOKBACK_DAYS
        self.asset_classifications = self._initialize_asset_classifications()
        
    def _initialize_asset_classifications(self) -> Dict[str, AssetClassification]:
        """Initialize asset classifications for quadrant analysis"""
        classifications = {}
        
        # Q1 Assets (Growth ↑, Inflation ↓)
        q1_assets = [
            ('QQQ', 'NASDAQ 100 (Growth)', 'Q1'),
            ('VUG', 'Vanguard Growth ETF', 'Q1'),
            ('IWM', 'Russell 2000 (Small Caps)', 'Q1'),
            ('BTC-USD', 'Bitcoin (BTC)', 'Q1'),
        ]
        
        # Q2 Assets (Growth ↑, Inflation ↑)
        q2_assets = [
            ('XLE', 'Energy Sector ETF', 'Q2'),
            ('DBC', 'Broad Commodities ETF', 'Q2'),
        ]
        
        # Q3 Assets (Growth ↓, Inflation ↑)
        q3_assets = [
            ('GLD', 'Gold ETF', 'Q3'),
            ('LIT', 'Lithium & Battery Tech ETF', 'Q3'),
        ]
        
        # Q4 Assets (Growth ↓, Inflation ↓)
        q4_assets = [
            ('TLT', '20+ Year Treasury Bonds', 'Q4'),
            ('XLU', 'Utilities Sector ETF', 'Q4'),
            ('UUP', 'US Dollar Index ETF', 'Q4'),
            ('VIXY', 'Short-Term VIX Futures ETF', 'Q4'),
        ]
        
        for symbol, name, quad in q1_assets:
            classifications[symbol] = AssetClassification(symbol, name, quad)
        for symbol, name, quad in q2_assets:
            classifications[symbol] = AssetClassification(symbol, name, quad)
        for symbol, name, quad in q3_assets:
            classifications[symbol] = AssetClassification(symbol, name, quad)
        for symbol, name, quad in q4_assets:
            classifications[symbol] = AssetClassification(symbol, name, quad)
            
        return classifications
    
    def fetch_historical_data(self, days: int = 365) -> pd.DataFrame:
        """Fetch historical data for all core assets"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"Fetching historical data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        
        data = {}
        failed_assets = []
        
        for symbol in CORE_ASSETS.keys():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if len(hist) > 0:
                    data[symbol] = hist['Close']
                    print(f"✓ {symbol}: {len(hist)} days")
                else:
                    failed_assets.append(symbol)
                    print(f"✗ {symbol}: No data")
                    
            except Exception as e:
                failed_assets.append(symbol)
                print(f"✗ {symbol}: Error - {str(e)[:50]}")
        
        if failed_assets:
            print(f"\nFailed to fetch: {failed_assets}")
        
        df = pd.DataFrame(data)
        df = df.dropna(how='all')
        
        print(f"\nSuccessfully loaded {len(df.columns)} assets with {len(df)} trading days")
        return df
    
    def calculate_momentum(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling momentum for each asset"""
        momentum_data = pd.DataFrame(index=price_data.index)
        
        for symbol in price_data.columns:
            momentum_data[symbol] = price_data[symbol].pct_change(self.lookback_days) * 100
        
        return momentum_data
    
    def calculate_quadrant_scores(self, momentum_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily quadrant scores"""
        quadrant_scores = pd.DataFrame(index=momentum_data.index)
        
        # Initialize quadrant score columns
        for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
            quadrant_scores[f'{quad}_Score'] = 0.0
            quadrant_scores[f'{quad}_Count'] = 0
        
        # Calculate scores for each day
        for date in momentum_data.index:
            daily_scores = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            daily_counts = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
            
            for symbol in momentum_data.columns:
                if symbol in self.asset_classifications:
                    momentum = momentum_data.loc[date, symbol]
                    
                    if pd.notna(momentum):
                        classification = self.asset_classifications[symbol]
                        quad = classification.primary_quadrant
                        weight = classification.weight
                        
                        weighted_score = momentum * weight
                        daily_scores[quad] += weighted_score
                        daily_counts[quad] += 1
            
            # Store results for this date
            for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
                quadrant_scores.loc[date, f'{quad}_Score'] = daily_scores[quad]
                quadrant_scores.loc[date, f'{quad}_Count'] = daily_counts[quad]
        
        return quadrant_scores
    
    def determine_quadrant(self, quadrant_scores: pd.DataFrame) -> pd.DataFrame:
        """Determine the primary quadrant for each day"""
        results = pd.DataFrame(index=quadrant_scores.index)
        
        # Calculate normalized scores (divide by count to get average)
        for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
            score_col = f'{quad}_Score'
            count_col = f'{quad}_Count'
            
            results[f'{quad}_Normalized'] = np.where(
                quadrant_scores[count_col] > 0,
                quadrant_scores[score_col] / quadrant_scores[count_col],
                0
            )
        
        # Determine primary quadrant (highest normalized score)
        quad_cols = ['Q1_Normalized', 'Q2_Normalized', 'Q3_Normalized', 'Q4_Normalized']
        results['Primary_Quadrant'] = results[quad_cols].idxmax(axis=1).str.replace('_Normalized', '')
        results['Primary_Score'] = results[quad_cols].max(axis=1)
        
        # Determine secondary quadrant (second highest)
        results['Secondary_Quadrant'] = results[quad_cols].apply(
            lambda row: row.nlargest(2).index[1].replace('_Normalized', '') if len(row.nlargest(2)) > 1 else None, 
            axis=1
        )
        results['Secondary_Score'] = results[quad_cols].apply(
            lambda row: row.nlargest(2).iloc[1] if len(row.nlargest(2)) > 1 else 0, 
            axis=1
        )
        
        # Calculate confidence (ratio of primary to secondary)
        results['Confidence'] = np.where(
            results['Secondary_Score'] > 0,
            results['Primary_Score'] / results['Secondary_Score'],
            float('inf')
        )
        
        # Determine regime strength
        results['Regime_Strength'] = pd.cut(
            results['Confidence'],
            bins=[0, 1.2, 1.8, float('inf')],
            labels=['Weak', 'Medium', 'Strong']
        )
        
        return results
    
    def get_current_regime(self) -> Dict:
        """Get the current market regime"""
        # Fetch recent data (365 days for robust calculation)
        price_data = self.fetch_historical_data(days=365)
        
        if price_data.empty:
            return None
        
        # Calculate momentum
        momentum_data = self.calculate_momentum(price_data)
        
        # Calculate quadrant scores
        quadrant_scores = self.calculate_quadrant_scores(momentum_data)
        
        # Determine quadrant
        results = self.determine_quadrant(quadrant_scores)
        
        # Get latest regime
        latest = results.iloc[-1]
        
        current_regime = {
            'date': results.index[-1],
            'primary_quadrant': latest['Primary_Quadrant'],
            'primary_score': latest['Primary_Score'],
            'secondary_quadrant': latest['Secondary_Quadrant'],
            'secondary_score': latest['Secondary_Score'],
            'confidence': latest['Confidence'],
            'regime_strength': latest['Regime_Strength'],
            'description': QUADRANT_DESCRIPTIONS.get(latest['Primary_Quadrant'], 'Unknown'),
            'all_scores': {
                'Q1': latest['Q1_Normalized'],
                'Q2': latest['Q2_Normalized'],
                'Q3': latest['Q3_Normalized'],
                'Q4': latest['Q4_Normalized']
            }
        }
        
        return current_regime
    
    def get_regime_history(self, days: int = 30) -> pd.DataFrame:
        """Get regime history for the specified number of days"""
        # Fetch data with extra days for momentum calculation
        total_days = days + self.lookback_days + 50  # Extra buffer
        price_data = self.fetch_historical_data(days=total_days)
        
        if price_data.empty:
            return pd.DataFrame()
        
        # Calculate momentum
        momentum_data = self.calculate_momentum(price_data)
        
        # Calculate quadrant scores
        quadrant_scores = self.calculate_quadrant_scores(momentum_data)
        
        # Determine quadrant
        results = self.determine_quadrant(quadrant_scores)
        
        # Get last N days
        recent_results = results.tail(days)
        
        # Add date information
        recent_results['Date'] = recent_results.index
        recent_results['Date_Str'] = recent_results.index.strftime('%Y-%m-%d')
        
        return recent_results
    
    def calculate_ema_filter(self, symbol: str = 'BTC-USD', period: int = 50) -> bool:
        """Calculate EMA filter for a given symbol"""
        try:
            # Fetch data for EMA calculation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period + 30)  # Extra buffer
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if len(hist) < period:
                print(f"Warning: Insufficient data for {symbol} EMA calculation")
                return False
            
            # Calculate EMA
            ema = hist['Close'].ewm(span=period).mean()
            current_price = hist['Close'].iloc[-1]
            current_ema = ema.iloc[-1]
            
            # Return True if price > EMA
            return current_price > current_ema
            
        except Exception as e:
            print(f"Error calculating EMA filter for {symbol}: {e}")
            return False

def main():
    """Test the quadrant analyzer"""
    analyzer = QuadrantAnalyzer()
    
    print("=== MACRO QUADRANT ANALYZER TEST ===")
    
    # Get current regime
    current_regime = analyzer.get_current_regime()
    
    if current_regime:
        print(f"\nCurrent Regime: {current_regime['primary_quadrant']}")
        print(f"Description: {current_regime['description']}")
        print(f"Strength: {current_regime['regime_strength']}")
        print(f"Confidence: {current_regime['confidence']:.2f}")
        print(f"Primary Score: {current_regime['primary_score']:.2f}")
        
        print(f"\nAll Quadrant Scores:")
        for quad, score in current_regime['all_scores'].items():
            print(f"  {quad}: {score:.2f}")
    
    # Get regime history
    history = analyzer.get_regime_history(days=30)
    
    if not history.empty:
        print(f"\nRegime History (Last 30 Days):")
        print(f"{'Date':<12} {'Regime':<8} {'Score':<8} {'Strength':<8}")
        print("-" * 40)
        
        for _, row in history.iterrows():
            date_str = row['Date_Str']
            regime = row['Primary_Quadrant']
            score = row['Primary_Score']
            strength = row['Regime_Strength']
            print(f"{date_str:<12} {regime:<8} {score:<8.2f} {strength:<8}")
    
    # Test EMA filter
    ema_filter = analyzer.calculate_ema_filter('BTC-USD', 50)
    print(f"\nBTC 50 EMA Filter: {'ABOVE' if ema_filter else 'BELOW'} EMA")

if __name__ == "__main__":
    main() 