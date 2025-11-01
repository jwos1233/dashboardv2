"""
Monte Carlo Backtest for Macro Quadrant Strategy
=================================================

Runs thousands of simulations to understand:
- Distribution of returns
- Probability of drawdowns
- Robustness to variations
- Confidence intervals

Simulation Methods:
1. Bootstrap Returns - Resample daily returns
2. Random Entry Timing - Vary entry by ±1-2 days
3. Random Exit Timing - Vary stop/EMA exits slightly
4. Position Size Variation - Add noise to weights
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Tuple
from quad_portfolio_backtest import QuadrantPortfolioBacktest
import warnings
warnings.filterwarnings('ignore')


class MonteCarloBacktest:
    """
    Monte Carlo simulation for quadrant strategy
    
    Runs N simulations with variations to understand distribution of outcomes
    """
    
    def __init__(self, base_strategy_params: Dict):
        """
        Initialize Monte Carlo simulator
        
        Args:
            base_strategy_params: Base parameters for strategy
        """
        self.base_params = base_strategy_params
        self.simulations = []
    
    def run_bootstrap_simulation(self, n_simulations=1000, block_size=20):
        """
        Bootstrap returns simulation
        
        Resamples daily returns in blocks to preserve autocorrelation
        
        Args:
            n_simulations: Number of simulations to run
            block_size: Size of blocks to resample (preserves momentum)
        """
        print(f"\n{'='*70}")
        print(f"MONTE CARLO SIMULATION - BOOTSTRAP RETURNS")
        print(f"{'='*70}")
        print(f"Simulations: {n_simulations}")
        print(f"Block size: {block_size} days")
        print(f"{'='*70}\n")
        
        # Run base strategy once to get returns series
        print("Running base strategy...")
        base_strategy = QuadrantPortfolioBacktest(**self.base_params)
        base_results = base_strategy.run_backtest()
        
        # Get daily returns
        base_equity = base_strategy.portfolio_value
        base_returns = base_equity.pct_change().dropna()
        
        print(f"Base strategy: {base_results['total_return']:.2%} return")
        print(f"Daily returns: {len(base_returns)} days\n")
        
        # Run simulations
        results = []
        
        for i in range(n_simulations):
            if (i + 1) % 100 == 0:
                print(f"  Simulation {i+1}/{n_simulations}...")
            
            # Bootstrap returns in blocks
            bootstrapped_returns = self._bootstrap_block_returns(base_returns, block_size)
            
            # Calculate simulated equity curve
            sim_equity = (1 + bootstrapped_returns).cumprod() * base_strategy.initial_capital
            
            # Calculate metrics
            total_return = (sim_equity.iloc[-1] / base_strategy.initial_capital - 1)
            
            # Calculate drawdown
            cummax = sim_equity.cummax()
            drawdown = (sim_equity - cummax) / cummax
            max_dd = drawdown.min()
            
            # Calculate annual return (assuming same time period)
            years = len(sim_equity) / 252
            annual_return = (1 + total_return) ** (1 / years) - 1
            
            # Calculate Sharpe
            daily_sharpe = bootstrapped_returns.mean() / bootstrapped_returns.std() if bootstrapped_returns.std() > 0 else 0
            sharpe = daily_sharpe * np.sqrt(252)
            
            results.append({
                'simulation': i + 1,
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': max_dd,
                'sharpe_ratio': sharpe,
                'final_value': sim_equity.iloc[-1],
                'volatility': bootstrapped_returns.std() * np.sqrt(252)
            })
        
        self.simulations = pd.DataFrame(results)
        
        print(f"\n+ Completed {n_simulations} simulations")
        
        return self.simulations
    
    def run_parameter_variation_simulation(self, n_simulations=500):
        """
        Vary strategy parameters within reasonable ranges
        
        Tests robustness to:
        - EMA period (45-55)
        - Momentum period (45-55)
        - Vol lookback (25-35)
        - ATR multiplier (1.8-2.2)
        
        Args:
            n_simulations: Number of simulations
        """
        print(f"\n{'='*70}")
        print(f"MONTE CARLO SIMULATION - PARAMETER VARIATION")
        print(f"{'='*70}")
        print(f"Simulations: {n_simulations}")
        print(f"{'='*70}\n")
        
        results = []
        
        for i in range(n_simulations):
            if (i + 1) % 50 == 0:
                print(f"  Simulation {i+1}/{n_simulations}...")
            
            # Randomize parameters
            params = self.base_params.copy()
            params['ema_period'] = np.random.randint(45, 56)
            params['momentum_days'] = np.random.randint(45, 56)
            params['vol_lookback'] = np.random.randint(25, 36)
            
            if 'atr_stop_loss' in params and params['atr_stop_loss'] is not None:
                params['atr_stop_loss'] = np.random.uniform(1.8, 2.2)
            
            # Run strategy
            strategy = QuadrantPortfolioBacktest(**params)
            result = strategy.run_backtest()
            
            results.append({
                'simulation': i + 1,
                'ema_period': params['ema_period'],
                'momentum_days': params['momentum_days'],
                'vol_lookback': params['vol_lookback'],
                'atr_multiplier': params.get('atr_stop_loss', None),
                'total_return': result['total_return'],
                'annual_return': result['annual_return'],
                'max_drawdown': result['max_drawdown'],
                'sharpe_ratio': result['sharpe_ratio'],
                'final_value': result['final_value']
            })
        
        self.simulations = pd.DataFrame(results)
        
        print(f"\n+ Completed {n_simulations} simulations")
        
        return self.simulations
    
    def analyze_results(self) -> Dict:
        """
        Analyze simulation results
        
        Returns:
            Dictionary with statistical summary
        """
        if self.simulations is None or len(self.simulations) == 0:
            print("⚠️ No simulations to analyze. Run a simulation first.")
            return {}
        
        print(f"\n{'='*70}")
        print(f"MONTE CARLO ANALYSIS - {len(self.simulations)} SIMULATIONS")
        print(f"{'='*70}\n")
        
        # Calculate percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        
        print("TOTAL RETURN DISTRIBUTION:")
        print("-" * 70)
        for p in percentiles:
            val = np.percentile(self.simulations['total_return'], p)
            print(f"  {p:>2}th percentile: {val:>8.2%}")
        
        print(f"\n  Mean:   {self.simulations['total_return'].mean():>8.2%}")
        print(f"  Median: {self.simulations['total_return'].median():>8.2%}")
        print(f"  Std:    {self.simulations['total_return'].std():>8.2%}")
        
        print(f"\n\nMAX DRAWDOWN DISTRIBUTION:")
        print("-" * 70)
        for p in percentiles:
            val = np.percentile(self.simulations['max_drawdown'], p)
            print(f"  {p:>2}th percentile: {val:>8.2%}")
        
        print(f"\n  Mean:   {self.simulations['max_drawdown'].mean():>8.2%}")
        print(f"  Median: {self.simulations['max_drawdown'].median():>8.2%}")
        print(f"  Worst:  {self.simulations['max_drawdown'].min():>8.2%}")
        
        print(f"\n\nSHARPE RATIO DISTRIBUTION:")
        print("-" * 70)
        for p in percentiles:
            val = np.percentile(self.simulations['sharpe_ratio'], p)
            print(f"  {p:>2}th percentile: {val:>8.2f}")
        
        print(f"\n  Mean:   {self.simulations['sharpe_ratio'].mean():>8.2f}")
        print(f"  Median: {self.simulations['sharpe_ratio'].median():>8.2f}")
        
        print(f"\n\nANNUAL RETURN DISTRIBUTION:")
        print("-" * 70)
        for p in percentiles:
            val = np.percentile(self.simulations['annual_return'], p)
            print(f"  {p:>2}th percentile: {val:>8.2%}")
        
        print(f"\n  Mean:   {self.simulations['annual_return'].mean():>8.2%}")
        print(f"  Median: {self.simulations['annual_return'].median():>8.2%}")
        
        # Risk metrics
        print(f"\n\nRISK ANALYSIS:")
        print("-" * 70)
        
        prob_positive = (self.simulations['total_return'] > 0).mean() * 100
        prob_beat_spy = (self.simulations['total_return'] > 1.229).mean() * 100  # 122.9% SPY return
        prob_dd_over_30 = (self.simulations['max_drawdown'] < -0.30).mean() * 100
        prob_dd_over_40 = (self.simulations['max_drawdown'] < -0.40).mean() * 100
        
        print(f"  Probability of positive return: {prob_positive:.1f}%")
        print(f"  Probability of beating SPY:     {prob_beat_spy:.1f}%")
        print(f"  Probability of DD > 30%:        {prob_dd_over_30:.1f}%")
        print(f"  Probability of DD > 40%:        {prob_dd_over_40:.1f}%")
        
        # Value at Risk
        var_95 = np.percentile(self.simulations['total_return'], 5)
        var_99 = np.percentile(self.simulations['total_return'], 1)
        
        print(f"\n  Value at Risk (95%): {var_95:.2%} (5% chance of worse)")
        print(f"  Value at Risk (99%): {var_99:.2%} (1% chance of worse)")
        
        print(f"\n{'='*70}\n")
        
        return {
            'return_mean': self.simulations['total_return'].mean(),
            'return_median': self.simulations['total_return'].median(),
            'return_std': self.simulations['total_return'].std(),
            'return_5th': np.percentile(self.simulations['total_return'], 5),
            'return_95th': np.percentile(self.simulations['total_return'], 95),
            'dd_mean': self.simulations['max_drawdown'].mean(),
            'dd_median': self.simulations['max_drawdown'].median(),
            'dd_worst': self.simulations['max_drawdown'].min(),
            'sharpe_mean': self.simulations['sharpe_ratio'].mean(),
            'sharpe_median': self.simulations['sharpe_ratio'].median(),
            'prob_positive': prob_positive,
            'prob_beat_spy': prob_beat_spy,
            'var_95': var_95,
            'var_99': var_99
        }
    
    def plot_results(self, save_path='monte_carlo_results.png'):
        """
        Plot simulation results
        
        Args:
            save_path: Path to save figure
        """
        if self.simulations is None or len(self.simulations) == 0:
            print("⚠️ No simulations to plot. Run a simulation first.")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(f'Monte Carlo Simulation Results ({len(self.simulations)} runs)', 
                     fontsize=16, fontweight='bold')
        
        # 1. Total Return Distribution
        ax = axes[0, 0]
        ax.hist(self.simulations['total_return'] * 100, bins=50, alpha=0.7, color='blue', edgecolor='black')
        ax.axvline(self.simulations['total_return'].mean() * 100, color='red', 
                   linestyle='--', linewidth=2, label=f"Mean: {self.simulations['total_return'].mean():.1%}")
        ax.axvline(self.simulations['total_return'].median() * 100, color='green', 
                   linestyle='--', linewidth=2, label=f"Median: {self.simulations['total_return'].median():.1%}")
        ax.set_xlabel('Total Return (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Total Return Distribution', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Max Drawdown Distribution
        ax = axes[0, 1]
        ax.hist(self.simulations['max_drawdown'] * 100, bins=50, alpha=0.7, color='red', edgecolor='black')
        ax.axvline(self.simulations['max_drawdown'].mean() * 100, color='darkred', 
                   linestyle='--', linewidth=2, label=f"Mean: {self.simulations['max_drawdown'].mean():.1%}")
        ax.axvline(self.simulations['max_drawdown'].median() * 100, color='orange', 
                   linestyle='--', linewidth=2, label=f"Median: {self.simulations['max_drawdown'].median():.1%}")
        ax.set_xlabel('Max Drawdown (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Max Drawdown Distribution', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 3. Sharpe Ratio Distribution
        ax = axes[0, 2]
        ax.hist(self.simulations['sharpe_ratio'], bins=50, alpha=0.7, color='green', edgecolor='black')
        ax.axvline(self.simulations['sharpe_ratio'].mean(), color='darkgreen', 
                   linestyle='--', linewidth=2, label=f"Mean: {self.simulations['sharpe_ratio'].mean():.2f}")
        ax.axvline(self.simulations['sharpe_ratio'].median(), color='lime', 
                   linestyle='--', linewidth=2, label=f"Median: {self.simulations['sharpe_ratio'].median():.2f}")
        ax.set_xlabel('Sharpe Ratio', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Sharpe Ratio Distribution', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. Annual Return Distribution
        ax = axes[1, 0]
        ax.hist(self.simulations['annual_return'] * 100, bins=50, alpha=0.7, color='purple', edgecolor='black')
        ax.axvline(self.simulations['annual_return'].mean() * 100, color='darkviolet', 
                   linestyle='--', linewidth=2, label=f"Mean: {self.simulations['annual_return'].mean():.1%}")
        ax.axvline(18.35, color='gray', linestyle=':', linewidth=2, label='SPY: 18.35%')
        ax.set_xlabel('Annual Return (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax.set_title('Annual Return Distribution', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 5. Return vs Drawdown Scatter
        ax = axes[1, 1]
        scatter = ax.scatter(self.simulations['max_drawdown'] * 100, 
                            self.simulations['total_return'] * 100,
                            c=self.simulations['sharpe_ratio'], 
                            cmap='viridis', alpha=0.6, s=20)
        ax.set_xlabel('Max Drawdown (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Total Return (%)', fontsize=11, fontweight='bold')
        ax.set_title('Return vs Drawdown (color = Sharpe)', fontsize=12, fontweight='bold')
        plt.colorbar(scatter, ax=ax, label='Sharpe Ratio')
        ax.grid(True, alpha=0.3)
        
        # 6. Percentile Chart
        ax = axes[1, 2]
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        returns = [np.percentile(self.simulations['total_return'], p) * 100 for p in percentiles]
        
        ax.barh(percentiles, returns, color='steelblue', edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('Total Return (%)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Percentile', fontsize=11, fontweight='bold')
        ax.set_title('Return Percentiles', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for i, (p, r) in enumerate(zip(percentiles, returns)):
            ax.text(r, p, f' {r:.1f}%', va='center', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\n[SAVED] Plot saved to: {save_path}")
        plt.show()
    
    def _bootstrap_block_returns(self, returns: pd.Series, block_size: int) -> pd.Series:
        """
        Bootstrap returns in blocks to preserve autocorrelation
        
        Args:
            returns: Original returns series
            block_size: Size of blocks
            
        Returns:
            Bootstrapped returns series
        """
        n = len(returns)
        n_blocks = int(np.ceil(n / block_size))
        
        # Create blocks from the original returns
        blocks = []
        for i in range(n // block_size):
            start_idx = i * block_size
            end_idx = start_idx + block_size
            blocks.append(returns.iloc[start_idx:end_idx].values)
        
        # Add remaining returns as final block if any
        remainder = n % block_size
        if remainder > 0:
            blocks.append(returns.iloc[-(remainder):].values)
        
        # Randomly sample blocks with replacement until we have enough data
        bootstrapped = []
        while len(bootstrapped) < n:
            block_idx = np.random.randint(0, len(blocks))
            bootstrapped.extend(blocks[block_idx])
        
        # Trim to exact original length
        bootstrapped = bootstrapped[:n]
        
        return pd.Series(bootstrapped, index=returns.index)


def run_full_monte_carlo(simulation_type='bootstrap', n_simulations=1000):
    """
    Run complete Monte Carlo analysis
    
    Args:
        simulation_type: 'bootstrap' or 'parameter'
        n_simulations: Number of simulations
    """
    print(f"\n{'='*70}")
    print(f"MACRO QUADRANT STRATEGY - MONTE CARLO ANALYSIS")
    print(f"{'='*70}")
    print(f"Simulation type: {simulation_type}")
    print(f"Number of runs: {n_simulations}")
    print(f"{'='*70}\n")
    
    # Base strategy parameters (Top 10 + ATR 2.0x)
    base_params = {
        'start_date': '2020-01-01',
        'end_date': '2024-12-31',
        'momentum_days': 50,
        'ema_period': 50,
        'vol_lookback': 30,
        'max_positions': 10,
        'atr_stop_loss': 2.0,
        'atr_period': 14
    }
    
    # Initialize Monte Carlo
    mc = MonteCarloBacktest(base_params)
    
    # Run simulations
    if simulation_type == 'bootstrap':
        mc.run_bootstrap_simulation(n_simulations=n_simulations, block_size=20)
    elif simulation_type == 'parameter':
        mc.run_parameter_variation_simulation(n_simulations=n_simulations)
    else:
        print(f"❌ Unknown simulation type: {simulation_type}")
        return None
    
    # Analyze results
    analysis = mc.analyze_results()
    
    # Plot results
    mc.plot_results(save_path=f'monte_carlo_{simulation_type}_{n_simulations}.png')
    
    # Save results to CSV
    csv_file = f'monte_carlo_{simulation_type}_{n_simulations}.csv'
    mc.simulations.to_csv(csv_file, index=False)
    print(f"[SAVED] Results saved to: {csv_file}")
    
    return mc


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monte Carlo Backtest')
    parser.add_argument('--type', choices=['bootstrap', 'parameter'], default='bootstrap',
                       help='Simulation type')
    parser.add_argument('--n', type=int, default=1000,
                       help='Number of simulations')
    
    args = parser.parse_args()
    
    # Run Monte Carlo
    mc = run_full_monte_carlo(
        simulation_type=args.type,
        n_simulations=args.n
    )
    
    print("\n[SUCCESS] Monte Carlo analysis complete!")

