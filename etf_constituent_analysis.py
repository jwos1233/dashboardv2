"""
ETF Constituent Relative Strength Analysis
===========================================

Analyzes constituents of your long ETF positions to identify 
the strongest individual stocks within trending sectors.

For each ETF you're long, this script:
1. Gets the top holdings
2. Calculates relative strength vs the ETF
3. Identifies outperformers you could trade directly

Usage:
    python etf_constituent_analysis.py
    python etf_constituent_analysis.py --lookback 30  # Custom lookback period
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple


class ETFConstituentAnalyzer:
    """Analyze constituents of ETFs for relative strength"""
    
    def __init__(self, lookback_days=30):
        """
        Initialize analyzer
        
        Args:
            lookback_days: Number of days for relative strength calculation
        """
        self.lookback_days = lookback_days
        self.current_positions = {}
        
        # Top holdings for major ETFs (update periodically)
        # These are the top 10-15 holdings for each ETF
        self.etf_holdings = {
            'ARKK': ['COIN', 'ROKU', 'SHOP', 'HOOD', 'RBLX', 'PATH', 'DKNG', 
                     'TWLO', 'ZM', 'CRSP', 'U', 'EXAS', 'TXG', 'NTLA', 'IONS'],
            
            'QQQ': ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'GOOG', 
                    'TSLA', 'AVGO', 'COST', 'NFLX', 'AMD', 'ASML', 'PEP', 'ADBE'],
            
            'IWM': ['HIMS', 'FTAI', 'RKLB', 'DOCS', 'FTNT', 'SAIA', 'CVNA',
                    'UFPI', 'INSM', 'MOD', 'FN', 'PIPR', 'KNSL', 'DY', 'ANF'],
            
            'XLC': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'VZ', 
                    'TMUS', 'T', 'CHTR', 'EA', 'TTWO', 'MTCH', 'OMC', 'NWSA'],
            
            'XLY': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'SBUX', 
                    'TJX', 'BKNG', 'CMG', 'MAR', 'ORLY', 'YUM', 'GM', 'F'],
            
            'XLE': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 
                    'VLO', 'OXY', 'HES', 'HAL', 'DVN', 'FANG', 'BKR', 'MRO'],
            
            'GLD': [],  # GLD tracks gold directly, no individual stocks
            'TLT': [],  # TLT is treasuries, no individual stocks
            'URA': ['CCJ', 'UUUU', 'DNN', 'NXE', 'UEC', 'URNM', 'PALAF', 
                    'LEU', 'BNNLF', 'EFR', 'UROY', 'Boss', 'URG', 'GLATF'],
            'REMX': ['ALB', 'SQM', 'LTHM', 'LAC', 'PLL', 'SGML', 'LIT', 
                     'LIFT', 'AVZ', 'CXO', 'ORE', 'MIN', 'NMG'],
            'COPX': ['FCX', 'SCCO', 'TECK', 'VALE', 'RIO', 'BHP', 'GLNCY',
                     'CPRUY', 'CMCL', 'TRQ', 'HBM', 'LBRMF', 'KGHM'],
            'CPER': [],  # CPER is copper futures, no individual stocks
            'PAVE': ['CAT', 'URI', 'VMC', 'MLM', 'DE', 'EME', 'FAST', 
                     'STRL', 'SUM', 'BLDR', 'FLS', 'IESC', 'MWA', 'ACM'],
        }
    
    def load_current_positions(self) -> List[str]:
        """Load current ETF positions from position_state.json"""
        if not os.path.exists('position_state.json'):
            print("WARNING: No position_state.json found")
            print("   Run sync_manual_positions.py first")
            return []
        
        try:
            with open('position_state.json', 'r') as f:
                state = json.load(f)
            
            positions = state.get('positions', {})
            etf_tickers = list(positions.keys())
            
            print(f"Found {len(etf_tickers)} current positions:")
            for ticker in etf_tickers:
                shares = positions[ticker].get('shares', 0)
                print(f"   {ticker}: {shares} shares")
            
            return etf_tickers
            
        except Exception as e:
            print(f"ERROR: Error loading positions: {e}")
            return []
    
    def get_price_data(self, tickers: List[str], days: int = None) -> pd.DataFrame:
        """
        Fetch price data for tickers
        
        Args:
            tickers: List of ticker symbols
            days: Number of days of history (defaults to lookback_days + 50)
        
        Returns:
            DataFrame with adjusted close prices
        """
        if days is None:
            days = self.lookback_days + 50
        
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\nDownloading {len(tickers)} tickers ({days} days)...")
        
        try:
            data = yf.download(tickers, start=start_date, end=end_date, 
                             progress=False, auto_adjust=True)['Close']
            
            if isinstance(data, pd.Series):
                data = data.to_frame(name=tickers[0])
            
            print(f"+ Downloaded data: {len(data)} days")
            return data
            
        except Exception as e:
            print(f"- Error downloading data: {e}")
            return pd.DataFrame()
    
    def calculate_relative_strength(self, stock_prices: pd.Series, 
                                    etf_prices: pd.Series) -> Tuple[float, pd.Series]:
        """
        Calculate relative strength of stock vs ETF
        
        Args:
            stock_prices: Price series for individual stock
            etf_prices: Price series for ETF
        
        Returns:
            (momentum, ratio_series) tuple
            - momentum: % change in ratio over lookback period
            - ratio_series: Stock/ETF ratio time series
        """
        # Calculate ratio
        ratio = stock_prices / etf_prices
        
        # Remove NaN values
        ratio = ratio.dropna()
        
        if len(ratio) < 2:
            return 0.0, ratio
        
        # Use available data (or full lookback if we have it)
        actual_lookback = min(self.lookback_days, len(ratio) - 1)
        
        # Calculate momentum (% change over lookback period)
        start_ratio = ratio.iloc[-actual_lookback - 1]
        end_ratio = ratio.iloc[-1]
        
        momentum = (end_ratio / start_ratio - 1) * 100
        
        return momentum, ratio
    
    def analyze_etf(self, etf_ticker: str) -> List[Dict]:
        """
        Analyze constituents of a single ETF
        
        Args:
            etf_ticker: ETF symbol (e.g., 'ARKK')
        
        Returns:
            List of dicts with stock analysis results
        """
        print(f"\n{'='*80}")
        print(f"Analyzing: {etf_ticker}")
        print(f"{'='*80}")
        
        # Get holdings
        holdings = self.etf_holdings.get(etf_ticker, [])
        
        if not holdings:
            print(f"INFO: No constituent data available for {etf_ticker}")
            print(f"   (Either not tracked or commodity ETF without stocks)")
            return []
        
        print(f"Holdings to analyze: {len(holdings)}")
        
        # Download data for ETF and all constituents
        all_tickers = [etf_ticker] + holdings
        price_data = self.get_price_data(all_tickers, self.lookback_days + 10)
        
        if price_data.empty or etf_ticker not in price_data.columns:
            print(f"ERROR: Could not get price data for {etf_ticker}")
            return []
        
        etf_prices = price_data[etf_ticker]
        
        # Analyze each constituent
        results = []
        
        for stock in holdings:
            if stock not in price_data.columns:
                continue
            
            stock_prices = price_data[stock]
            
            # Calculate relative strength
            rs_momentum, ratio_series = self.calculate_relative_strength(
                stock_prices, etf_prices
            )
            
            # Get current values
            current_stock_price = stock_prices.iloc[-1]
            current_etf_price = etf_prices.iloc[-1]
            current_ratio = current_stock_price / current_etf_price
            
            # Calculate stock's own momentum (if enough data)
            if len(stock_prices) >= self.lookback_days:
                stock_momentum = (stock_prices.iloc[-1] / stock_prices.iloc[-self.lookback_days] - 1) * 100
            else:
                # Use whatever data we have
                stock_momentum = (stock_prices.iloc[-1] / stock_prices.iloc[0] - 1) * 100
            
            results.append({
                'ticker': stock,
                'rs_momentum': rs_momentum,
                'stock_momentum': stock_momentum,
                'current_price': current_stock_price,
                'current_ratio': current_ratio,
                'etf': etf_ticker
            })
        
        # Sort by relative strength momentum
        results.sort(key=lambda x: x['rs_momentum'], reverse=True)
        
        return results
    
    def display_results(self, etf_ticker: str, results: List[Dict], top_n: int = 5):
        """Display analysis results for an ETF"""
        if not results:
            return
        
        print(f"\nTop {top_n} Performers in {etf_ticker} (by Relative Strength):")
        print(f"{'Rank':<6} {'Ticker':<8} {'RS Mom':<12} {'Stock Mom':<12} {'Price':<12}")
        print("-" * 80)
        
        for i, result in enumerate(results[:top_n], 1):
            ticker = result['ticker']
            rs_mom = result['rs_momentum']
            stock_mom = result['stock_momentum']
            price = result['current_price']
            
            print(f"{i:<6} {ticker:<8} {rs_mom:>+10.2f}%  {stock_mom:>+10.2f}%  ${price:>10.2f}")
        
        print()
    
    def generate_summary_report(self, all_results: Dict[str, List[Dict]]):
        """Generate summary report across all ETFs"""
        print("\n" + "="*80)
        print("OVERALL TOP PERFORMERS ACROSS ALL YOUR ETFS")
        print("="*80)
        
        # Flatten all results
        all_stocks = []
        for etf, results in all_results.items():
            all_stocks.extend(results)
        
        # Remove duplicates (same stock in multiple ETFs - keep best RS)
        unique_stocks = {}
        for stock in all_stocks:
            ticker = stock['ticker']
            if ticker not in unique_stocks or stock['rs_momentum'] > unique_stocks[ticker]['rs_momentum']:
                unique_stocks[ticker] = stock
        
        # Sort by RS momentum
        sorted_stocks = sorted(unique_stocks.values(), 
                              key=lambda x: x['rs_momentum'], 
                              reverse=True)
        
        print(f"\n*** Top 15 Stocks Across All Your ETFs ***")
        print(f"{'Rank':<6} {'Ticker':<8} {'In ETF':<8} {'RS Mom':<12} {'Stock Mom':<12} {'Price':<12}")
        print("-" * 80)
        
        for i, result in enumerate(sorted_stocks[:15], 1):
            ticker = result['ticker']
            etf = result['etf']
            rs_mom = result['rs_momentum']
            stock_mom = result['stock_momentum']
            price = result['current_price']
            
            print(f"{i:<6} {ticker:<8} {etf:<8} {rs_mom:>+10.2f}%  {stock_mom:>+10.2f}%  ${price:>10.2f}")
        
        print()
    
    def save_report(self, all_results: Dict[str, List[Dict]], filename: str = None):
        """Save detailed report to file"""
        if filename is None:
            filename = f"etf_constituent_analysis_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"ETF CONSTITUENT RELATIVE STRENGTH ANALYSIS\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Lookback Period: {self.lookback_days} days\n")
            f.write("="*80 + "\n\n")
            
            # By ETF
            for etf_ticker, results in all_results.items():
                if not results:
                    continue
                
                f.write(f"\n{'='*80}\n")
                f.write(f"ETF: {etf_ticker}\n")
                f.write(f"{'='*80}\n")
                f.write(f"{'Rank':<6} {'Ticker':<8} {'RS Momentum':<15} {'Stock Momentum':<15} {'Price':<12}\n")
                f.write("-"*80 + "\n")
                
                for i, result in enumerate(results[:10], 1):
                    ticker = result['ticker']
                    rs_mom = result['rs_momentum']
                    stock_mom = result['stock_momentum']
                    price = result['current_price']
                    
                    f.write(f"{i:<6} {ticker:<8} {rs_mom:>+13.2f}%  {stock_mom:>+13.2f}%  ${price:>10.2f}\n")
            
            # Overall top performers
            all_stocks = []
            for etf, results in all_results.items():
                all_stocks.extend(results)
            
            unique_stocks = {}
            for stock in all_stocks:
                ticker = stock['ticker']
                if ticker not in unique_stocks or stock['rs_momentum'] > unique_stocks[ticker]['rs_momentum']:
                    unique_stocks[ticker] = stock
            
            sorted_stocks = sorted(unique_stocks.values(), 
                                  key=lambda x: x['rs_momentum'], 
                                  reverse=True)
            
            f.write(f"\n{'='*80}\n")
            f.write(f"OVERALL TOP 20 PERFORMERS\n")
            f.write(f"{'='*80}\n")
            f.write(f"{'Rank':<6} {'Ticker':<8} {'In ETF':<8} {'RS Momentum':<15} {'Stock Momentum':<15} {'Price':<12}\n")
            f.write("-"*80 + "\n")
            
            for i, result in enumerate(sorted_stocks[:20], 1):
                ticker = result['ticker']
                etf = result['etf']
                rs_mom = result['rs_momentum']
                stock_mom = result['stock_momentum']
                price = result['current_price']
                
                f.write(f"{i:<6} {ticker:<8} {etf:<8} {rs_mom:>+13.2f}%  {stock_mom:>+13.2f}%  ${price:>10.2f}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("INTERPRETATION:\n")
            f.write("="*80 + "\n")
            f.write("RS Momentum = Relative Strength Momentum\n")
            f.write("  - Positive: Stock outperforming its ETF\n")
            f.write("  - Negative: Stock underperforming its ETF\n\n")
            f.write("Stock Momentum = Absolute price momentum\n")
            f.write("  - The stock's own price trend\n\n")
            f.write("Use this to:\n")
            f.write("  1. Identify leaders within your trending sectors\n")
            f.write("  2. Consider trading individual stocks instead of ETFs\n")
            f.write("  3. Spot sector rotation opportunities\n")
            f.write("  4. Find high-conviction ideas for discretionary trades\n")
            f.write("="*80 + "\n")
        
        print(f"\n+ Full report saved to: {filename}")
    
    def run_analysis(self) -> Dict[str, List[Dict]]:
        """Run complete analysis"""
        print("\n" + "="*80)
        print("ETF CONSTITUENT RELATIVE STRENGTH ANALYSIS")
        print("="*80)
        print(f"Lookback Period: {self.lookback_days} days")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("="*80)
        
        # Load current positions
        current_etfs = self.load_current_positions()
        
        if not current_etfs:
            print("\nERROR: No positions found - run sync_manual_positions.py first")
            return {}
        
        # Analyze each ETF
        all_results = {}
        
        for etf_ticker in current_etfs:
            results = self.analyze_etf(etf_ticker)
            
            if results:
                all_results[etf_ticker] = results
                self.display_results(etf_ticker, results, top_n=5)
        
        # Generate overall summary
        if all_results:
            self.generate_summary_report(all_results)
            self.save_report(all_results)
        
        return all_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Analyze ETF constituents for relative strength',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default 30-day analysis
  python etf_constituent_analysis.py
  
  # Custom lookback period
  python etf_constituent_analysis.py --lookback 60
  
  # Specific ETFs only
  python etf_constituent_analysis.py --etfs ARKK QQQ

Output:
  - Top performers within each ETF you're long
  - Overall top performers across all ETFs
  - Relative strength momentum (stock vs ETF)
  - Absolute stock momentum
  
Use this to:
  - Identify leaders in your trending sectors
  - Find discretionary trade ideas
  - Understand what's driving your ETF returns
        """
    )
    
    parser.add_argument('--lookback', type=int, default=30,
                       help='Lookback period in days (default: 30)')
    parser.add_argument('--etfs', nargs='+', 
                       help='Specific ETFs to analyze (default: all current positions)')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ETFConstituentAnalyzer(lookback_days=args.lookback)
    
    # Override with specific ETFs if provided
    if args.etfs:
        print(f"\nAnalyzing specific ETFs: {', '.join(args.etfs)}")
        all_results = {}
        for etf in args.etfs:
            results = analyzer.analyze_etf(etf)
            if results:
                all_results[etf] = results
                analyzer.display_results(etf, results, top_n=5)
        
        if all_results:
            analyzer.generate_summary_report(all_results)
            analyzer.save_report(all_results)
    else:
        # Analyze all current positions
        analyzer.run_analysis()


if __name__ == "__main__":
    main()

