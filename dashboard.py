"""
Macro Quadrant Strategy Dashboard
Streamlit dashboard for visualizing quadrant analysis and portfolio allocations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from functools import lru_cache
import warnings
import yfinance as yf
import uuid

warnings.filterwarnings('ignore')

from signal_generator import SignalGenerator
from config import QUAD_ALLOCATIONS, QUADRANT_DESCRIPTIONS, QUAD_INDICATORS
from quad_portfolio_backtest import QuadrantPortfolioBacktest

# Known asset names (fallback to Yahoo Finance lookup otherwise)
ASSET_NAME_OVERRIDES = {
    'QQQ': 'Invesco QQQ Trust',
    'ARKK': 'ARK Innovation ETF',
    'IWM': 'iShares Russell 2000 ETF',
    'XLC': 'Communication Services Select Sector SPDR',
    'XLY': 'Consumer Discretionary Select Sector SPDR',
    'TLT': 'iShares 20+ Year Treasury Bond ETF',
    'LQD': 'iShares iBoxx $ Investment Grade Corporate',
    'XLE': 'Energy Select Sector SPDR',
    'DBC': 'Invesco DB Commodity Index Tracking',
    'GCC': 'WisdomTree Enhanced Commodity Strategy',
    'LIT': 'Global X Lithium & Battery Tech ETF',
    'AA': 'Alcoa Corporation',
    'PALL': 'Aberdeen Physical Palladium Shares',
    'VALT': 'ETF Managers Group Short-Term Treasury',
    'XLF': 'Financial Select Sector SPDR',
    'XLI': 'Industrial Select Sector SPDR',
    'XLB': 'Materials Select Sector SPDR',
    'XOP': 'SPDR S&P Oil & Gas Exploration & Production',
    'FCG': 'First Trust Natural Gas ETF',
    'USO': 'United States Oil Fund',
    'VNQ': 'Vanguard Real Estate ETF',
    'PAVE': 'Global X U.S. Infrastructure Development',
    'VTV': 'Vanguard Value ETF',
    'IWD': 'iShares Russell 1000 Value ETF',
    'GLD': 'SPDR Gold Shares',
    'DBA': 'Invesco DB Agriculture Fund',
    'REMX': 'VanEck Rare Earth/Strategic Metals ETF',
    'URA': 'Global X Uranium ETF',
    'TIP': 'iShares TIPS Bond ETF',
    'VTIP': 'Vanguard Short-Term Inflation-Protected Sec',
    'XLV': 'Health Care Select Sector SPDR',
    'XLU': 'Utilities Select Sector SPDR',
    'VGLT': 'Vanguard Long-Term Treasury ETF',
    'IEF': 'iShares 7-10 Year Treasury Bond ETF',
    'MUB': 'iShares National Muni Bond ETF',
    'XLP': 'Consumer Staples Select Sector SPDR',
    'QID': 'ProShares UltraShort QQQ'
}

# Page config
st.set_page_config(
    page_title="Macro Quadrant Strategy Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .quadrant-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid;
        margin: 0.5rem 0;
    }
    .quad-q1 { border-color: #2ecc71; }
    .quad-q2 { border-color: #e74c3c; }
    .quad-q3 { border-color: #f39c12; }
    .quad-q4 { border-color: #3498db; }
    .risk-box {
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: #fff;
        text-align: center;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .risk-on { background-color: #27ae60; }
    .risk-off { background-color: #c0392b; }
    .risk-neutral { background-color: #7f8c8d; }
</style>
""", unsafe_allow_html=True)


@lru_cache(maxsize=256)
def get_asset_name(ticker: str) -> str:
    """Return a human-readable asset name for a ticker."""
    ticker = ticker.upper()
    if ticker in ASSET_NAME_OVERRIDES:
        return ASSET_NAME_OVERRIDES[ticker]
    
    try:
        info = yf.Ticker(ticker).info
        for field in ('longName', 'shortName', 'name'):
            value = info.get(field)
            if value:
                return value
    except Exception:
        pass
    
    return ticker

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_quadrant_history(days=180):
    """Get quadrant scores history for the last N days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 100)  # Extra buffer for momentum calc
    
    # Create a minimal backtest to get quadrant scores
    backtest = QuadrantPortfolioBacktest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=50000,
        momentum_days=20,
        ema_period=50,
        vol_lookback=30
    )
    
    # Fetch data and calculate quadrant scores
    backtest.fetch_data()
    quad_scores = backtest.calculate_quad_scores()
    
    # Convert to percentages (backtest returns decimals, signal_generator returns percentages)
    quad_scores = quad_scores * 100
    
    # Determine top quads
    warmup = 50
    if len(quad_scores) > warmup:
        top_quads = backtest.determine_top_quads(quad_scores.iloc[warmup:])
        
        # Combine scores with top quads
        result = pd.DataFrame(index=quad_scores.index[warmup:])
        result['Q1_Score'] = quad_scores.loc[result.index, 'Q1']
        result['Q2_Score'] = quad_scores.loc[result.index, 'Q2']
        result['Q3_Score'] = quad_scores.loc[result.index, 'Q3']
        result['Q4_Score'] = quad_scores.loc[result.index, 'Q4']
        result['Top1'] = top_quads['Top1']
        result['Top2'] = top_quads['Top2']
        result['Score1'] = top_quads['Score1']
        result['Score2'] = top_quads['Score2']
        
        # Get last 180 days
        if len(result) > days:
            result = result.tail(days)
        
        return result
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_current_signals():
    """Get current trading signals"""
    sg = SignalGenerator()
    signals = sg.generate_signals()
    return signals

def main():
    st.markdown('<h1 class="main-header">📊 Macro Quadrant Strategy Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        refresh_button = st.button("🔄 Refresh Data", type="primary")
        if refresh_button:
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📖 About")
        st.markdown("""
        This dashboard shows:
        - **Active Quadrants**: Current Top1 and Top2 quadrants
        - **Quadrant Scores**: Historical scores over last 180 days
        - **Portfolio Breakdown**: Current target allocations
        """)
    
    # Get current signals
    with st.spinner("Loading current signals..."):
        try:
            signals = get_current_signals()
        except Exception as e:
            st.error(f"Error loading signals: {e}")
            return
    
    # Section 1: Current Active Quadrants
    st.header("🎯 Current Active Quadrants")
    
    top1, top2 = signals['top_quadrants']
    quad_scores_raw = signals['quadrant_scores']
    
    # Convert Series to dict if needed
    if isinstance(quad_scores_raw, pd.Series):
        quad_scores = quad_scores_raw.to_dict()
    else:
        quad_scores = quad_scores_raw
    
    col1, col2, col3, col4 = st.columns(4)
    
    quad_colors = {
        'Q1': '#2ecc71',  # Green
        'Q2': '#e74c3c',  # Red
        'Q3': '#f39c12',  # Orange
        'Q4': '#3498db'   # Blue
    }
    
    for i, quad in enumerate(['Q1', 'Q2', 'Q3', 'Q4']):
        with [col1, col2, col3, col4][i]:
            score = quad_scores.get(quad, 0)
            is_active = quad in [top1, top2]
            
            # Determine if it's Top1 or Top2
            if quad == top1:
                label = f"🥇 {quad} (Top 1)"
            elif quad == top2:
                label = f"🥈 {quad} (Top 2)"
            else:
                label = f"{quad}"
            
            st.metric(
                label=label,
                value=f"{score:.2f}%",
                delta=f"{'ACTIVE' if is_active else 'Inactive'}"
            )
    
    # Show active quadrants + risk regime
    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        <div class="quadrant-box">
            <p><strong>Primary ({top1})</strong> — {QUADRANT_DESCRIPTIONS[top1]}</p>
            <hr style="margin: 0.75rem 0;">
            <p><strong>Secondary ({top2})</strong> — {QUADRANT_DESCRIPTIONS[top2]}</p>
        </div>
        """, unsafe_allow_html=True)
    
    risk_status = "Neutral"
    risk_reason = "No clear risk-on/off signal"
    risk_class = "risk-neutral"
    top_quads_set = {top1, top2}
    if 'Q1' in top_quads_set:
        risk_status = "Risk On"
        risk_reason = "Q1 present in top regimes → favor growth assets"
        risk_class = "risk-on"
    elif 'Q4' in top_quads_set:
        risk_status = "Risk Off"
        risk_reason = "Q4 present in top regimes → defensive posture"
        risk_class = "risk-off"
    
    with col2:
        st.markdown(f"""
        <div class="risk-box {risk_class}">
            <h3>{risk_status}</h3>
            <p>{risk_reason}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Section 2: Daily Line Chart of Quadrant Scores
    st.header("📈 Daily Quadrant Scores (Last 180 Days)")
    
    with st.spinner("Loading quadrant history..."):
        try:
            history = get_quadrant_history(days=180)
            
            if not history.empty:
                # Plot daily scores (already in percentage format)
                fig = go.Figure()
                
                for quad in ['Q1', 'Q2', 'Q3', 'Q4']:
                    score_col = f'{quad}_Score'
                    if score_col in history.columns:
                        # Use raw daily scores (already in percentage)
                        daily_scores = history[score_col]
                        
                        # Determine if this quad is currently active
                        is_active = quad in [top1, top2]
                        line_width = 3 if is_active else 2
                        opacity = 1.0 if is_active else 0.6
                        
                        fig.add_trace(go.Scatter(
                            x=history.index,
                            y=daily_scores,
                            mode='lines',
                            name=quad,
                            line=dict(
                                color=quad_colors[quad],
                                width=line_width
                            ),
                            opacity=opacity,
                            hovertemplate=f'{quad}<br>Date: %{{x}}<br>Score: %{{y:.2f}}%<extra></extra>'
                        ))
                
                # Add zero line
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Zero")
                
                fig.update_layout(
                    title="Daily Quadrant Scores Over Time",
                    xaxis_title="Date",
                    yaxis_title="Daily Score (%)",
                    height=500,
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # New: Strategy backtest section
                @st.cache_data(ttl=600)
                def run_dashboard_backtest():
                    years = 3
                    end = datetime.now()
                    start = end - timedelta(days=365 * years + 100)
                    bt = QuadrantPortfolioBacktest(
                        start_date=start,
                        end_date=end,
                        initial_capital=50000,
                        momentum_days=20,
                        ema_period=50,
                        vol_lookback=30,
                        max_positions=10,
                        atr_stop_loss=2.0,
                        atr_period=14
                    )
                    res = bt.run_backtest()
                    return bt, res
                
                st.subheader("📈 Strategy Backtest (3-Year)")
                try:
                    backtest, results = run_dashboard_backtest()
                    
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Total Return", f"{results['total_return']:.2f}%")
                    col_b.metric("Annualized Return", f"{results['annual_return']:.2f}%")
                    col_c.metric("Sharpe Ratio", f"{results['sharpe']:.2f}")
                    col_d.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
                    
                    equity_fig = go.Figure(
                        data=[go.Scatter(
                            x=backtest.portfolio_value.index,
                            y=backtest.portfolio_value,
                            mode='lines',
                            line=dict(color='#8e44ad', width=2),
                            name='Portfolio Value'
                        )]
                    )
                    equity_fig.update_layout(
                        title="Backtest Portfolio Value",
                        yaxis_title="Equity ($)",
                        xaxis_title="Date",
                        height=450,
                        hovermode='x unified'
                    )
                    st.plotly_chart(equity_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Backtest failed: {e}")
                
                # Show recent scores table
                with st.expander("📊 Recent Scores Table (Last 30 Days)"):
                    display_cols = ['Q1_Score', 'Q2_Score', 'Q3_Score', 'Q4_Score', 'Top1', 'Top2']
                    available_cols = [col for col in display_cols if col in history.columns]
                    if available_cols:
                        recent = history[available_cols].tail(30)
                        st.dataframe(
                            recent.style.format({
                                'Q1_Score': '{:.2f}',
                                'Q2_Score': '{:.2f}',
                                'Q3_Score': '{:.2f}',
                                'Q4_Score': '{:.2f}'
                            }),
                            use_container_width=True
                        )
            else:
                st.warning("No historical data available")
                
        except Exception as e:
            st.error(f"Error loading history: {e}")
            st.exception(e)
    
    # Section 3: Current Portfolio Breakdown
    st.header("💼 Current Portfolio Breakdown")
    
    target_weights = signals.get('target_weights', {})
    total_leverage = signals.get('total_leverage', 0)
    
    if target_weights:
        # Create portfolio dataframe
        portfolio_data = []
        for ticker, weight in target_weights.items():
            # Determine which quadrant(s) this ticker belongs to
            quads = []
            for q, assets in QUAD_ALLOCATIONS.items():
                if ticker in assets:
                    quads.append(q)
            
            quad_str = '+'.join(quads) if quads else 'N/A'
            is_in_active = any(q in [top1, top2] for q in quads)
            
            portfolio_data.append({
                'Asset': get_asset_name(ticker),
                'Quadrant(s)': quad_str,
                'Weight (%)': weight * 100
            })
        
        portfolio_df = pd.DataFrame(portfolio_data)
        portfolio_df = portfolio_df.sort_values('Weight (%)', ascending=False)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Leverage", f"{total_leverage:.2f}x")
        with col2:
            st.metric("Number of Positions", len(target_weights))
        with col3:
            st.metric("Active Quadrants", f"{top1} + {top2}")
        
        # Display portfolio table
        st.subheader("Position Details")
        st.dataframe(
            portfolio_df[['Asset', 'Quadrant(s)', 'Weight (%)']].style.format({'Weight (%)': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Portfolio allocation chart
        st.subheader("Portfolio Allocation Chart")
        fig_pie = go.Figure(data=[go.Pie(
            labels=portfolio_df['Asset'],
            values=portfolio_df['Weight (%)'],
            hole=0.3,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Weight: %{percent}<br>Quadrant: %{customdata}<extra></extra>',
            customdata=portfolio_df['Quadrant(s)']
        )])
        
        fig_pie.update_layout(
            title="Portfolio Weight Distribution",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
        
    else:
        st.warning("No portfolio data available")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    st.markdown("*Data refreshes every 5 minutes. Click 'Refresh Data' to update manually.*")

if __name__ == "__main__":
    main()

