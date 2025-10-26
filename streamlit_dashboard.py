#!/usr/bin/env python3
"""
Macro Quadrant Rotation Strategy Dashboard
Real-time monitoring of quadrant signals, asset allocations, and performance
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Handle imports with proper error checking
PLOTLY_AVAILABLE = True
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    PLOTLY_AVAILABLE = False

import yfinance as yf

# Import strategy modules
from config import QUAD_ALLOCATIONS, QUADRANT_DESCRIPTIONS, QUAD_INDICATORS
from quad_portfolio_backtest import QuadrantPortfolioBacktest

warnings.filterwarnings('ignore')

class MacroQuadrantDashboard:
    """Main dashboard for Macro Quadrant Rotation Strategy"""
    
    def __init__(self):
        self.setup_page()
        self.initialize_session_state()
        
    def setup_page(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Macro Quadrant Strategy Dashboard",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS matching the macro dashboard style
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00ff88;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 0.5rem;
            border: 1px solid #333;
        }
        .quad-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            border: 2px solid;
            margin: 0.5rem;
        }
        .q1-box { border-color: #00ff88; background-color: rgba(0, 255, 136, 0.1); }
        .q2-box { border-color: #0088ff; background-color: rgba(0, 136, 255, 0.1); }
        .q3-box { border-color: #ff8800; background-color: rgba(255, 136, 0, 0.1); }
        .q4-box { border-color: #8800ff; background-color: rgba(136, 0, 255, 0.1); }
        </style>
        """, unsafe_allow_html=True)
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'backtest_results' not in st.session_state:
            st.session_state['backtest_results'] = None
        if 'current_quadrant' not in st.session_state:
            st.session_state['current_quadrant'] = None
        if 'last_refresh' not in st.session_state:
            st.session_state['last_refresh'] = datetime.now()
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">Macro Quadrant Rotation Strategy Dashboard</h1>', unsafe_allow_html=True)
        
        # Status bar
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(f"Last update: {st.session_state['last_refresh'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    def render_sidebar(self):
        """Render the sidebar with controls"""
        st.sidebar.title("Strategy Controls")
        
        # Strategy parameters
        st.sidebar.subheader("Strategy Parameters")
        initial_capital = st.sidebar.number_input("Initial Capital ($)", value=50000, step=10000)
        lookback_days = st.sidebar.slider("Momentum Lookback", 20, 100, 50, help="Days for quadrant scoring")
        ema_period = st.sidebar.slider("EMA Filter Period", 20, 100, 50, help="Trend filter period")
        vol_lookback = st.sidebar.slider("Vol Lookback", 10, 90, 30, help="Volatility weighting period")
        
        # Refresh button
        if st.sidebar.button("Refresh All Data", type="primary"):
            st.session_state['last_refresh'] = datetime.now()
            st.session_state['backtest_results'] = None
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Strategy info
        st.sidebar.markdown("### Strategy Info")
        st.sidebar.markdown("**Type**: Volatility Chasing")
        st.sidebar.markdown("**Leverage**: 2x (top 2 quads)")
        st.sidebar.markdown("**Rebalancing**: Event-driven")
        st.sidebar.markdown("**Assets**: 35 ETFs")
        
        # Performance targets
        st.sidebar.markdown("### Expected Performance")
        st.sidebar.markdown("**Total Return**: ~170%")
        st.sidebar.markdown("**Sharpe Ratio**: 0.80")
        st.sidebar.markdown("**Max Drawdown**: -22.5%")
        st.sidebar.markdown("**vs SPY**: +56.9%")
        
        # Instructions
        with st.sidebar.expander("📖 How It Works"):
            st.markdown("""
            **Quadrant Classification:**
            - Q1 (Goldilocks): Growth ↑, Inflation ↓
            - Q2 (Reflation): Growth ↑, Inflation ↑
            - Q3 (Stagflation): Growth ↓, Inflation ↑
            - Q4 (Deflation): Growth ↓, Inflation ↓
            
            **Strategy Logic:**
            1. Score all 4 quadrants daily
            2. Allocate 100% to each of top 2
            3. Weight assets by volatility (higher = more)
            4. Filter: only allocate if above 50-day EMA
            5. Rebalance when quads change or EMA cross
            """)
        
        return {
            'initial_capital': initial_capital,
            'lookback_days': lookback_days,
            'ema_period': ema_period,
            'vol_lookback': vol_lookback
        }
    
    def fetch_current_quadrant_scores(self):
        """Fetch current quadrant scores and determine top 2"""
        try:
            # Download recent data for quadrant indicators
            tickers = []
            for quad_tickers in QUAD_INDICATORS.values():
                tickers.extend(quad_tickers)
            tickers = list(set(tickers))
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            with st.spinner("Fetching current market data..."):
                data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                return None, None, None
            
            # Get adjusted close prices - handle both single and multiple ticker formats
            if len(tickers) == 1:
                # Single ticker case
                if isinstance(data, pd.DataFrame) and 'Adj Close' in data.columns:
                    prices = data['Adj Close'].to_frame()
                    prices.columns = tickers
                elif isinstance(data, pd.DataFrame):
                    prices = data[['Close']].copy()
                    prices.columns = tickers
                else:
                    prices = pd.DataFrame(data, columns=tickers)
            else:
                # Multiple tickers case
                if isinstance(data.columns, pd.MultiIndex):
                    if 'Adj Close' in data.columns.get_level_values(0):
                        prices = data['Adj Close']
                    else:
                        prices = data['Close']
                else:
                    # Fallback for unexpected format
                    if 'Adj Close' in data.columns:
                        prices = data[['Adj Close']].copy()
                        prices.columns = tickers
                    else:
                        prices = data[['Close']].copy()
                        prices.columns = tickers
            
            # Forward fill any missing data
            prices = prices.ffill().bfill()
            
            # Calculate 50-day momentum for each quadrant
            quad_scores = {}
            for quad, quad_tickers in QUAD_INDICATORS.items():
                valid_scores = []
                for ticker in quad_tickers:
                    if ticker in prices.columns:
                        price_series = prices[ticker].dropna()
                        if len(price_series) >= 50:
                            momentum = (price_series.iloc[-1] / price_series.iloc[-50] - 1) * 100
                            valid_scores.append(momentum)
                
                quad_scores[quad] = np.mean(valid_scores) if valid_scores else 0
            
            # Sort to get top 2
            sorted_quads = sorted(quad_scores.items(), key=lambda x: x[1], reverse=True)
            top1_quad, top1_score = sorted_quads[0]
            top2_quad, top2_score = sorted_quads[1]
            
            return top1_quad, top2_quad, quad_scores
            
        except Exception as e:
            st.error(f"Error fetching quadrant scores: {e}")
            import traceback
            st.error(f"Full traceback: {traceback.format_exc()}")
            return None, None, None
    
    def get_asset_momentum_in_quad(self, quad):
        """Get momentum scores for all assets in a quadrant"""
        try:
            # Get all tickers from this quad's allocation
            tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() if t != 'CASH']
            
            if not tickers:
                return pd.DataFrame()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=70)  # Extra buffer for data
            
            # Download data - add retry logic
            data = None
            for attempt in range(2):
                try:
                    data = yf.download(tickers, start=start_date, end=end_date, progress=False, threads=False)
                    if not data.empty:
                        break
                except Exception as e:
                    if attempt == 1:
                        st.warning(f"Failed to download data for {quad} assets after 2 attempts")
                        return pd.DataFrame()
                    continue
            
            if data is None or data.empty:
                st.warning(f"No data returned for {quad} assets")
                return pd.DataFrame()
            
            # Get prices - handle both single and multiple ticker formats
            if len(tickers) == 1:
                # Single ticker case
                if isinstance(data, pd.DataFrame) and 'Adj Close' in data.columns:
                    prices = data['Adj Close'].to_frame()
                    prices.columns = tickers
                elif isinstance(data, pd.DataFrame):
                    prices = data[['Close']].copy()
                    prices.columns = tickers
                else:
                    prices = pd.DataFrame(data, columns=tickers)
            else:
                # Multiple tickers case
                if isinstance(data.columns, pd.MultiIndex):
                    if 'Adj Close' in data.columns.get_level_values(0):
                        prices = data['Adj Close']
                    else:
                        prices = data['Close']
                else:
                    prices = data
            
            # Forward fill any missing data
            prices = prices.ffill().bfill()
            
            # Calculate metrics for each asset
            asset_data = []
            for ticker in tickers:
                try:
                    if ticker in prices.columns:
                        price_series = prices[ticker].dropna()
                        
                        # Check minimum data requirements
                        if len(price_series) < 30:
                            continue
                        
                        # Calculate momentum (with fallbacks for shorter periods)
                        mom_50d = (price_series.iloc[-1] / price_series.iloc[-50] - 1) * 100 if len(price_series) >= 50 else np.nan
                        mom_20d = (price_series.iloc[-1] / price_series.iloc[-20] - 1) * 100 if len(price_series) >= 20 else np.nan
                        mom_5d = (price_series.iloc[-1] / price_series.iloc[-5] - 1) * 100 if len(price_series) >= 5 else np.nan
                        
                        # Calculate volatility
                        returns = price_series.pct_change().dropna()
                        if len(returns) >= 20:
                            vol_30d = returns.tail(min(30, len(returns))).std() * np.sqrt(252) * 100
                        else:
                            vol_30d = np.nan
                        
                        # Get current price and EMA
                        current_price = price_series.iloc[-1]
                        if len(price_series) >= 50:
                            ema_50 = price_series.ewm(span=50, adjust=False).mean().iloc[-1]
                        else:
                            ema_50 = price_series.mean()
                        above_ema = current_price > ema_50
                        
                        # Only add if we have at least some valid data
                        if not np.isnan(mom_50d) or not np.isnan(mom_20d):
                            asset_data.append({
                                'Ticker': ticker,
                                '50d Momentum': mom_50d if not np.isnan(mom_50d) else mom_20d,
                                '20d Momentum': mom_20d if not np.isnan(mom_20d) else 0,
                                '5d Momentum': mom_5d if not np.isnan(mom_5d) else 0,
                                '30d Volatility': vol_30d if not np.isnan(vol_30d) else 0,
                                'Price': current_price,
                                'EMA(50)': ema_50,
                                'Above EMA': 'Yes' if above_ema else 'No',
                                'Quad Allocation': QUAD_ALLOCATIONS[quad].get(ticker, 0) * 100
                            })
                except Exception as e:
                    # Skip this ticker if there's an error
                    continue
            
            if asset_data:
                df = pd.DataFrame(asset_data)
                df = df.sort_values('50d Momentum', ascending=False)
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            st.warning(f"Could not load asset data for {quad}: {str(e)[:100]}")
            # Don't show full traceback to keep UI clean
            return pd.DataFrame()
    
    def render_current_quadrants(self):
        """Render current and backup quadrant analysis"""
        st.header("Current Market Regime")
        
        # Fetch current quadrant scores
        top1_quad, top2_quad, all_scores = self.fetch_current_quadrant_scores()
        
        if top1_quad is None:
            st.error("Failed to fetch current quadrant data")
            return
        
        # Display top 2 quadrants
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f'<div class="quad-box {top1_quad.lower()}-box">', unsafe_allow_html=True)
            st.subheader(f"🥇 PRIMARY: {top1_quad}")
            st.markdown(f"**Score**: {all_scores[top1_quad]:.2f}%")
            st.markdown(f"**Description**: {QUADRANT_DESCRIPTIONS.get(top1_quad, 'N/A')}")
            st.markdown(f"**Allocation**: 100% (1.0x)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="quad-box {top2_quad.lower()}-box">', unsafe_allow_html=True)
            st.subheader(f"🥈 BACKUP: {top2_quad}")
            st.markdown(f"**Score**: {all_scores[top2_quad]:.2f}%")
            st.markdown(f"**Description**: {QUADRANT_DESCRIPTIONS.get(top2_quad, 'N/A')}")
            st.markdown(f"**Allocation**: 100% (1.0x)")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Show all quadrant scores
        st.subheader("All Quadrant Scores")
        score_df = pd.DataFrame([
            {'Quadrant': quad, 'Score (%)': f"{score:.2f}", 'Status': 'ACTIVE' if quad in [top1_quad, top2_quad] else 'Inactive'}
            for quad, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(score_df, use_container_width=True, hide_index=True)
        
        return top1_quad, top2_quad
    
    def render_dominant_assets(self, quad, quad_label):
        """Render dominant assets in a quadrant"""
        st.subheader(f"Dominant Assets in {quad_label} ({quad})")
        
        with st.spinner(f"Loading {quad} asset data..."):
            asset_df = self.get_asset_momentum_in_quad(quad)
        
        if asset_df.empty:
            # Show which tickers we tried to fetch
            tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() if t != 'CASH']
            st.info(f"Could not fetch data for {quad} assets: {', '.join(tickers[:5])}{'...' if len(tickers) > 5 else ''}")
            return
        
        # Display metrics for top assets
        top_assets = asset_df.head(3)
        cols = st.columns(3)
        
        for idx, (_, row) in enumerate(top_assets.iterrows()):
            with cols[idx]:
                st.metric(
                    label=row['Ticker'],
                    value=f"{row['50d Momentum']:.1f}%",
                    delta=f"{row['5d Momentum']:.1f}% (5d)"
                )
        
        # Detailed table
        st.dataframe(
            asset_df.style.format({
                '50d Momentum': '{:.2f}%',
                '20d Momentum': '{:.2f}%',
                '5d Momentum': '{:.2f}%',
                '30d Volatility': '{:.2f}%',
                'Price': '${:.2f}',
                'EMA(50)': '${:.2f}',
                'Quad Allocation': '{:.1f}%'
            }),
            use_container_width=True,
            height=300
        )
    
    def calculate_live_vol_weighted_allocations(self, top1_quad, top2_quad, vol_lookback=30, ema_period=50):
        """Calculate ACTUAL vol-weighted allocations with EMA filter (matches backtest logic)"""
        try:
            # Get all unique tickers from both quads
            all_tickers = set()
            for ticker in QUAD_ALLOCATIONS[top1_quad].keys():
                if ticker != 'CASH':
                    all_tickers.add(ticker)
            for ticker in QUAD_ALLOCATIONS[top2_quad].keys():
                if ticker != 'CASH':
                    all_tickers.add(ticker)
            
            all_tickers = list(all_tickers)
            
            # Fetch recent data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=max(vol_lookback, ema_period) + 30)
            data = yf.download(all_tickers, start=start_date, end=end_date, progress=False, threads=False)
            
            # Extract prices
            if len(all_tickers) == 1:
                if isinstance(data, pd.DataFrame) and 'Adj Close' in data.columns:
                    prices = data['Adj Close'].to_frame()
                    prices.columns = all_tickers
                else:
                    prices = data[['Close']].copy()
                    prices.columns = all_tickers
            else:
                if isinstance(data.columns, pd.MultiIndex):
                    prices = data['Adj Close'] if 'Adj Close' in data.columns.get_level_values(0) else data['Close']
                else:
                    prices = data[['Adj Close']].copy() if 'Adj Close' in data.columns else data[['Close']].copy()
            
            prices = prices.ffill().bfill()
            
            # Calculate volatility and EMA for each asset
            volatilities = {}
            ema_status = {}
            
            for ticker in all_tickers:
                if ticker in prices.columns:
                    price_series = prices[ticker].dropna()
                    if len(price_series) >= vol_lookback:
                        returns = price_series.pct_change().dropna()
                        vol = returns.tail(vol_lookback).std() * np.sqrt(252)
                        volatilities[ticker] = vol
                        
                        # Check EMA
                        if len(price_series) >= ema_period:
                            ema = price_series.ewm(span=ema_period, adjust=False).mean().iloc[-1]
                            current_price = price_series.iloc[-1]
                            ema_status[ticker] = current_price > ema
                        else:
                            ema_status[ticker] = True
            
            # Calculate vol-weighted allocations for each quad
            final_allocs = {}
            
            for quad, quad_weight in [(top1_quad, 1.0), (top2_quad, 1.0)]:
                quad_tickers = [t for t in QUAD_ALLOCATIONS[quad].keys() if t != 'CASH']
                quad_vols = {t: volatilities.get(t, 0) for t in quad_tickers if t in volatilities}
                
                if not quad_vols:
                    continue
                
                # Volatility chasing: higher vol = higher weight
                total_vol = sum(quad_vols.values())
                vol_weights = {t: (v / total_vol) * quad_weight for t, v in quad_vols.items()}
                
                # Apply EMA filter
                for ticker, weight in vol_weights.items():
                    if ema_status.get(ticker, False):
                        final_allocs[ticker] = final_allocs.get(ticker, 0) + weight
            
            return final_allocs, ema_status
            
        except Exception as e:
            st.warning(f"Could not calculate live vol-weighted allocations: {str(e)[:100]}")
            # Fallback to static allocations
            return self.get_static_allocations(top1_quad, top2_quad), {}
    
    def get_static_allocations(self, top1_quad, top2_quad):
        """Get static base allocations (fallback)"""
        combined_allocs = {}
        for ticker, alloc in QUAD_ALLOCATIONS[top1_quad].items():
            if ticker != 'CASH':
                combined_allocs[ticker] = combined_allocs.get(ticker, 0) + alloc
        for ticker, alloc in QUAD_ALLOCATIONS[top2_quad].items():
            if ticker != 'CASH':
                combined_allocs[ticker] = combined_allocs.get(ticker, 0) + alloc
        return combined_allocs
    
    def render_recommended_allocations(self, top1_quad, top2_quad):
        """Render recommended asset allocations"""
        st.header("Recommended Portfolio Allocations")
        
        st.markdown("""
        **Allocation Method:** Volatility Chasing (30-day lookback)  
        - Higher volatility assets get higher allocations within each quad
        - 50-day EMA filter: Only allocate to assets above their EMA
        - Target: 100% in each of top 2 quads (200% leverage)
        - Any EMA-filtered portion remains in cash
        """)
        
        # Get ACTUAL vol-weighted allocations
        with st.spinner("Calculating live allocations..."):
            combined_allocs, ema_status = self.calculate_live_vol_weighted_allocations(top1_quad, top2_quad)
        
        # Calculate cash (unallocated portion due to EMA filter)
        total_allocated = sum(combined_allocs.values())
        cash_pct = max(0, 2.0 - total_allocated)  # 2.0 = 200% leverage target
        
        # Sort by allocation
        sorted_allocs = sorted(combined_allocs.items(), key=lambda x: x[1], reverse=True)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leverage", f"{total_allocated:.1%}")
        with col2:
            st.metric("Cash Held", f"{cash_pct:.1%}")
        with col3:
            st.metric("Active Assets", f"{len(combined_allocs)}")
        with col4:
            assets_filtered = sum(1 for t in ema_status.values() if not t)
            st.metric("Assets Filtered (Below EMA)", f"{assets_filtered}")
        
        # Allocation table
        st.subheader("Detailed Allocations (Vol-Weighted)")
        alloc_df = pd.DataFrame([
            {
                'Asset': ticker,
                'Allocation (%)': alloc * 100,
                'Above EMA': 'Yes' if ema_status.get(ticker, True) else 'No',
                f'In {top1_quad}': 'Yes' if ticker in QUAD_ALLOCATIONS[top1_quad] else 'No',
                f'In {top2_quad}': 'Yes' if ticker in QUAD_ALLOCATIONS[top2_quad] else 'No',
                'Asset Class': self.get_asset_class(ticker)
            }
            for ticker, alloc in sorted_allocs
        ])
        
        st.dataframe(
            alloc_df.style.format({'Allocation (%)': '{:.2f}%'}),
            use_container_width=True,
            height=400
        )
        
        # Pie chart of allocations
        if PLOTLY_AVAILABLE:
            fig = px.pie(
                alloc_df.head(10),
                values='Allocation (%)',
                names='Asset',
                title='Top 10 Asset Allocations'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def get_asset_class(self, ticker):
        """Determine asset class from ticker"""
        if ticker in ['QQQ', 'SPY', 'IWM', 'ARKK', 'VUG', 'VTV', 'IWD', 'EFA', 'EEM', 'VGK', 'EWJ', 'EWG', 'EWU']:
            return 'Equities'
        elif ticker in ['TLT', 'IEF', 'VGLT', 'LQD', 'MUB', 'TIP', 'VTIP']:
            return 'Bonds'
        elif ticker in ['GLD', 'USO', 'DBC', 'CPER', 'DBA', 'GCC', 'REMX']:
            return 'Commodities'
        elif ticker in ['XLE', 'XLF', 'XLI', 'XLB', 'XLC', 'XLY', 'XLV', 'XLU', 'XLP']:
            return 'Sectors'
        elif ticker in ['VNQ', 'PAVE', 'FCG', 'XOP']:
            return 'Real Estate/Energy'
        else:
            return 'Other'
    
    def render_strategy_performance(self, params):
        """Render backtest performance"""
        st.header("Strategy Performance (Backtest)")
        
        # Run backtest button
        if st.button("Run Backtest", type="primary") or st.session_state['backtest_results'] is None:
            with st.spinner("Running backtest... This may take 1-2 minutes"):
                try:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=5 * 365 + 100)
                    
                    backtest = QuadrantPortfolioBacktest(
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=params['initial_capital'],
                        momentum_days=params['lookback_days'],
                        ema_period=params['ema_period'],
                        vol_lookback=params['vol_lookback']
                    )
                    
                    results = backtest.run_backtest()
                    st.session_state['backtest_results'] = {
                        'backtest': backtest,
                        'results': results
                    }
                    
                    st.success("Backtest complete!")
                    
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                    return
        
        # Display results if available
        if st.session_state['backtest_results'] is not None:
            backtest_data = st.session_state['backtest_results']
            backtest = backtest_data['backtest']
            
            # Calculate metrics
            portfolio_value = backtest.portfolio_value
            returns = portfolio_value.pct_change().dropna()
            
            total_return = (portfolio_value.iloc[-1] / params['initial_capital'] - 1) * 100
            years = len(returns) / 252
            annual_return = ((portfolio_value.iloc[-1] / params['initial_capital']) ** (1 / years) - 1) * 100
            annual_vol = returns.std() * np.sqrt(252) * 100
            sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_dd = drawdown.min() * 100
            
            # Display metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Return", f"{total_return:.1f}%")
            with col2:
                st.metric("Annual Return", f"{annual_return:.1f}%")
            with col3:
                st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            with col4:
                st.metric("Max Drawdown", f"{max_dd:.1f}%")
            with col5:
                st.metric("Volatility", f"{annual_vol:.1f}%")
            
            # Performance chart
            if PLOTLY_AVAILABLE:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    mode='lines',
                    name='Strategy',
                    line=dict(color='#00ff88', width=2)
                ))
                
                fig.update_layout(
                    title='Portfolio Value Over Time',
                    xaxis_title='Date',
                    yaxis_title='Portfolio Value ($)',
                    height=400,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Drawdown chart
            if PLOTLY_AVAILABLE:
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,
                    mode='lines',
                    name='Drawdown',
                    fill='tozeroy',
                    line=dict(color='#ff4444', width=2)
                ))
                
                fig.update_layout(
                    title='Drawdown Over Time',
                    xaxis_title='Date',
                    yaxis_title='Drawdown (%)',
                    height=300,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def run(self):
        """Main method to run the dashboard"""
        try:
            # Render components
            self.render_header()
            params = self.render_sidebar()
            
            # Main content
            top1_quad, top2_quad = self.render_current_quadrants()
            
            if top1_quad and top2_quad:
                st.markdown("---")
                
                # Dominant assets in both quads
                col1, col2 = st.columns(2)
                with col1:
                    self.render_dominant_assets(top1_quad, "PRIMARY")
                with col2:
                    self.render_dominant_assets(top2_quad, "BACKUP")
                
                st.markdown("---")
                
                # Recommended allocations
                self.render_recommended_allocations(top1_quad, top2_quad)
            
            st.markdown("---")
            
            # Strategy performance
            self.render_strategy_performance(params)
            
            # Footer
            st.markdown("---")
            st.markdown("**Macro Quadrant Rotation Strategy** | Volatility Chasing with EMA Filter | Production v1.0")
            
        except Exception as e:
            st.error(f"Dashboard error: {str(e)}")
            st.exception(e)

def main():
    """Main entry point"""
    try:
        dashboard = MacroQuadrantDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Failed to initialize dashboard: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()

