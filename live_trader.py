"""
Live Trading Orchestrator for Macro Quadrant Strategy
======================================================

Main script to generate signals and execute trades via Interactive Brokers
"""

import schedule
import time
from datetime import datetime
from signal_generator import SignalGenerator
from ib_executor import IBExecutor
import json


class LiveTrader:
    """Orchestrate signal generation and trade execution"""
    
    def __init__(self, ib_port=7497, dry_run=True):
        """
        Initialize live trader
        
        Args:
            ib_port: IB port (7497 for paper, 7496 for live with TWS)
            dry_run: If True, generate signals but don't execute trades
        """
        self.signal_gen = SignalGenerator(momentum_days=50, ema_period=50, vol_lookback=30, max_positions=10)
        self.ib_port = ib_port
        self.dry_run = dry_run
        
        self.current_positions = {}
        self.last_signal_time = None
        self.last_trades = []
        
    def check_and_trade(self):
        """Generate signals and execute trades if needed"""
        print("\n" + "="*70)
        print(f"CHECKING SIGNALS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # Generate signals
            signals = self.signal_gen.generate_signals()
            
            self.last_signal_time = signals['timestamp']
            
            # Save signals to file
            self.save_signals(signals)
            
            if self.dry_run:
                print("\n🔒 DRY RUN MODE - No trades executed")
                return
            
            # Execute trades via IB
            print("\n💼 Executing trades via Interactive Brokers...")
            
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    trades = ib_exec.execute_rebalance(signals['target_weights'])
                    self.last_trades = trades
                    
                    # Update current positions
                    self.current_positions = ib_exec.get_current_positions()
                else:
                    print("❌ Failed to connect to IB - no trades executed")
        
        except Exception as e:
            print(f"\n❌ Error in check_and_trade: {e}")
            import traceback
            traceback.print_exc()
    
    def save_signals(self, signals: dict):
        """Save signals to JSON file for record keeping"""
        filename = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
        
        # Convert to serializable format
        signal_data = {
            'timestamp': signals['timestamp'].isoformat(),
            'regime': signals['current_regime'],
            'top_quadrants': signals['top_quadrants'],
            'quadrant_scores': signals['quadrant_scores'].to_dict(),
            'target_weights': signals['target_weights'],
            'total_leverage': signals['total_leverage']
        }
        
        with open(filename, 'w') as f:
            json.dump(signal_data, f, indent=2)
        
        print(f"\n💾 Signals saved to {filename}")
    
    def run_once(self):
        """Run signal generation and trade execution once"""
        self.check_and_trade()
    
    def run_scheduled(self, check_time="16:00"):
        """
        Run on a schedule (daily after market close)
        
        Args:
            check_time: Time to check signals (HH:MM format)
                       Default 16:00 = 4 PM EST (after US market close)
        """
        print("\n" + "="*70)
        print("LIVE TRADER - SCHEDULED MODE")
        print("="*70)
        print(f"Schedule: Daily at {check_time} EST")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        print(f"IB Port: {self.ib_port}")
        print("="*70)
        
        # Schedule the job
        schedule.every().day.at(check_time).do(self.check_and_trade)
        
        # Run immediately on start
        print("\nRunning initial signal check...")
        self.check_and_trade()
        
        # Keep running
        print(f"\nWaiting for next scheduled run at {check_time}...")
        print("Press Ctrl+C to stop")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Macro Quadrant Live Trader')
    parser.add_argument('--mode', choices=['once', 'scheduled'], default='once',
                       help='Run once or on schedule')
    parser.add_argument('--time', default='16:00',
                       help='Scheduled run time (HH:MM format, default 16:00)')
    parser.add_argument('--port', type=int, default=7497,
                       help='IB port (7497=paper/TWS, 7496=live/TWS, 4002=paper/Gateway, 4001=live/Gateway)')
    parser.add_argument('--live', action='store_true',
                       help='Enable live trading (default is dry run)')
    
    args = parser.parse_args()
    
    # Initialize trader
    trader = LiveTrader(
        ib_port=args.port,
        dry_run=not args.live
    )
    
    # Run
    if args.mode == 'once':
        print("Running signal generation once...")
        trader.run_once()
    else:
        print(f"Starting scheduled trading at {args.time}...")
        trader.run_scheduled(check_time=args.time)

