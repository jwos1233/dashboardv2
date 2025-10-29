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
from position_manager import PositionManager
from pending_orders import PendingOrdersManager
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
        self.signal_gen = SignalGenerator(momentum_days=50, ema_period=50, vol_lookback=30, 
                                          max_positions=10, atr_stop_loss=2.0, atr_period=14)
        self.pending_manager = PendingOrdersManager()
        self.ib_port = ib_port
        self.dry_run = dry_run
        
        self.current_positions = {}
        self.last_signal_time = None
        self.last_trades = []
        
    def generate_signals_night(self):
        """
        STEP 1: Generate signals and save pending entries (Night run)
        
        Run this after market close (16:00 EST)
        - Generates signals based on today's close
        - Saves pending entries for tomorrow
        - Does NOT execute trades yet
        """
        print("\n" + "="*70)
        print(f"STEP 1: SIGNAL GENERATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # Generate signals
            signals = self.signal_gen.generate_signals()
            
            self.last_signal_time = signals['timestamp']
            
            # Save signals to file
            self.save_signals(signals)
            
            # Get current EMA data for confirmation tomorrow
            ema_data = {}
            if hasattr(self.signal_gen, 'ema_data') and self.signal_gen.ema_data is not None:
                # Get latest EMA for each ticker
                for ticker in signals['target_weights'].keys():
                    if ticker in self.signal_gen.ema_data.columns:
                        ema_data[ticker] = float(self.signal_gen.ema_data[ticker].iloc[-1])
            
            # Save pending entries
            self.pending_manager.add_pending_entries(signals, ema_data)
            
            print("\n✅ Step 1 Complete - Signals generated and saved")
            print("⏰ Run confirm_and_execute_morning() before market open tomorrow")
        
        except Exception as e:
            print(f"\n❌ Error in generate_signals_night: {e}")
            import traceback
            traceback.print_exc()
    
    def confirm_and_execute_morning(self):
        """
        STEP 2: Confirm entries and execute (Morning run)
        
        Run this before market open (09:29 EST)
        - Loads pending entries from last night
        - Re-checks EMA for each position
        - Executes only confirmed entries
        - Matches backtest's 28.1% rejection rate
        """
        print("\n" + "="*70)
        print(f"STEP 2: CONFIRMATION & EXECUTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # Check if we have pending orders
            if not self.pending_manager.has_pending_orders():
                print("ℹ️ No pending orders to confirm")
                print("💡 Run generate_signals_night() first (after market close)")
                return
            
            # Get pending summary
            summary = self.pending_manager.get_pending_summary()
            print(f"Signal date: {summary['signal_date']}")
            print(f"Pending positions: {summary['count']}")
            print(f"Regime: {summary['regime']}")
            
            # Get tickers to check
            pending_tickers = list(self.pending_manager.pending_orders['entries'].keys())
            
            # Fetch current market data
            price_data, ema_data = self.pending_manager.get_current_market_data(pending_tickers)
            
            # Confirm entries (checks EMA)
            confirmed_entries = self.pending_manager.confirm_and_get_entries(price_data, ema_data)
            
            if not confirmed_entries:
                print("\n⚠️ No entries confirmed - all rejected!")
                return
            
            # Build target weights from confirmed entries
            target_weights = {
                ticker: entry['weight'] 
                for ticker, entry in confirmed_entries.items()
            }
            
            # Build ATR data for stops
            atr_data = {
                ticker: entry.get('atr')
                for ticker, entry in confirmed_entries.items()
                if entry.get('atr') is not None
            }
            
            if self.dry_run:
                print("\n🔒 DRY RUN MODE - No trades executed")
                print("\nConfirmed positions to trade:")
                for ticker, weight in sorted(target_weights.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {ticker}: {weight*100:.2f}%")
                return
            
            # Execute trades via IB
            print("\n💼 Executing confirmed entries via Interactive Brokers...")
            
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    # Initialize position manager
                    position_manager = PositionManager(ib_exec.ib)
                    
                    # Execute rebalance with confirmed entries
                    trades = ib_exec.execute_rebalance(
                        target_weights, 
                        position_manager=position_manager,
                        atr_data=atr_data
                    )
                    self.last_trades = trades
                    
                    # Update current positions
                    self.current_positions = ib_exec.get_current_positions()
                    
                    print("\n✅ Step 2 Complete - Trades executed")
                else:
                    print("❌ Failed to connect to IB - no trades executed")
        
        except Exception as e:
            print(f"\n❌ Error in confirm_and_execute_morning: {e}")
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
    
    def run_once_night(self):
        """Run Step 1: Generate signals (night run)"""
        self.generate_signals_night()
    
    def run_once_morning(self):
        """Run Step 2: Confirm and execute (morning run)"""
        self.confirm_and_execute_morning()
    
    def run_scheduled(self, night_time="16:00", morning_time="09:29"):
        """
        Run on a schedule (two-step process)
        
        Args:
            night_time: Time to generate signals (HH:MM format)
                       Default 16:00 = 4 PM EST (after market close)
            morning_time: Time to confirm and execute (HH:MM format)
                         Default 09:29 = 9:29 AM EST (before market open)
        """
        print("\n" + "="*70)
        print("LIVE TRADER - SCHEDULED MODE (TWO-STEP)")
        print("="*70)
        print(f"Night Schedule:   {night_time} EST (Generate signals)")
        print(f"Morning Schedule: {morning_time} EST (Confirm & execute)")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        print(f"IB Port: {self.ib_port}")
        print("="*70)
        
        # Schedule both jobs
        schedule.every().day.at(night_time).do(self.generate_signals_night)
        schedule.every().day.at(morning_time).do(self.confirm_and_execute_morning)
        
        print("\n⏰ Waiting for scheduled runs...")
        print(f"   Next night run:   {night_time}")
        print(f"   Next morning run: {morning_time}")
        print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Macro Quadrant Live Trader - Two-Step Entry Confirmation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Night run (after close) - Generate signals
  python live_trader.py --step night
  
  # Morning run (before open) - Confirm and execute
  python live_trader.py --step morning --live --port 4002
  
  # Scheduled mode (runs both automatically)
  python live_trader.py --mode scheduled --live --port 4002
        """
    )
    
    parser.add_argument('--step', choices=['night', 'morning'], 
                       help='Run specific step: night (generate signals) or morning (confirm & execute)')
    parser.add_argument('--mode', choices=['scheduled'], 
                       help='Run in scheduled mode (auto runs both night and morning)')
    parser.add_argument('--night-time', default='16:00',
                       help='Night run time for scheduled mode (HH:MM, default 16:00)')
    parser.add_argument('--morning-time', default='09:29',
                       help='Morning run time for scheduled mode (HH:MM, default 09:29)')
    parser.add_argument('--port', type=int, default=7497,
                       help='IB port (7497=paper/TWS, 7496=live/TWS, 4002=paper/Gateway, 4001=live/Gateway)')
    parser.add_argument('--live', action='store_true',
                       help='Enable live trading (default is dry run)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.step and not args.mode:
        parser.error("Must specify either --step or --mode")
    
    if args.step and args.mode:
        parser.error("Cannot use both --step and --mode")
    
    # Initialize trader
    trader = LiveTrader(
        ib_port=args.port,
        dry_run=not args.live
    )
    
    # Run
    if args.step == 'night':
        print("\n🌙 Running STEP 1: Signal Generation (Night Run)")
        trader.run_once_night()
    elif args.step == 'morning':
        print("\n☀️ Running STEP 2: Confirmation & Execution (Morning Run)")
        trader.run_once_morning()
    elif args.mode == 'scheduled':
        print(f"\n⏰ Starting scheduled mode...")
        trader.run_scheduled(
            night_time=args.night_time, 
            morning_time=args.morning_time
        )

