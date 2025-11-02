import schedule
import time
from datetime import datetime
from signal_generator import SignalGenerator
from ib_executor import IBExecutor
from position_manager import PositionManager
from pending_orders import PendingOrdersManager
from telegram_notifier import get_notifier
import json


class LiveTrader:
    """Orchestrate signal generation and trade execution"""
    
    def __init__(self, ib_port=7497, dry_run=True, enable_telegram=True):
        """
        Initialize live trader
        
        Args:
            ib_port: IB port (7497 for paper, 7496 for live with TWS)
            dry_run: If True, generate signals but don't execute trades
            enable_telegram: If True, send Telegram notifications
        """
        self.signal_gen = SignalGenerator(momentum_days=50, ema_period=50, vol_lookback=30, 
                                          max_positions=10, atr_stop_loss=2.0, atr_period=14)
        self.pending_manager = PendingOrdersManager()
        self.ib_port = ib_port
        self.dry_run = dry_run
        self.enable_telegram = enable_telegram
        
        # Initialize Telegram notifier
        self.telegram = get_notifier() if enable_telegram else None
        
        self.current_positions = {}
        self.last_signal_time = None
        self.last_trades = []
    
    def _get_account_value(self):
        """Helper to get real account value from IB Gateway"""
        try:
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    account_summary = ib_exec.ib.accountSummary()
                    for item in account_summary:
                        if item.tag == 'NetLiquidation':
                            value = float(item.value)
                            print(f"✓ Fetched account value: ${value:,.2f}")
                            return value
        except Exception as e:
            print(f"! Warning: Could not fetch account value: {e}")
        print("! Using fallback account value: $50,000")
        return 50000  # Fallback only if connection fails
        
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
            
            # Display detailed plan
            self.display_night_plan(signals, ema_data)
            
            # Save plan to file
            self.save_night_plan(signals, ema_data)
            
            # Send Telegram notification
            if self.telegram:
                try:
                    # Get account value and current positions for TG alert
                    account_value = self._get_account_value()
                    current_positions = {}
                    try:
                        with IBExecutor(port=self.ib_port) as ib_exec:
                            if ib_exec.connected:
                                current_positions = ib_exec.get_current_positions()
                    except:
                        pass
                    
                    self.telegram.send_night_alert(
                        signals, 
                        len(signals['target_weights']),
                        account_value=account_value,
                        current_positions=current_positions
                    )
                    print("+ Telegram notification sent")
                except Exception as e:
                    print(f"! Telegram notification failed: {e}")
            
            print("\n" + "="*70)
            print("NIGHT RUN COMPLETE")
            print("="*70)
            print(f"+ Signals generated and saved")
            print(f"+ Pending entries: {len(signals['target_weights'])}")
            print(f"+ Plan saved to: night_plan_{datetime.now().strftime('%Y%m%d')}.txt")
            if self.telegram:
                print(f"+ Telegram alert sent")
            print(f"\nNext step:")
            print(f"  Run tomorrow morning (9:29 AM):")
            print(f"  python live_trader.py --step morning --live --port {self.ib_port}")
            print("="*70)
        
        except Exception as e:
            print(f"\n" + "="*70)
            print("ERROR IN NIGHT RUN")
            print("="*70)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print("="*70)
            
            # Send error alert
            if self.telegram:
                try:
                    self.telegram.send_error_alert(str(e), "Night Run - Signal Generation")
                except:
                    pass
    
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
            confirmed_entries, rejected_entries = self.pending_manager.confirm_and_get_entries(price_data, ema_data)
            
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
            print("\n" + "="*70)
            print("EXECUTING VIA INTERACTIVE BROKERS")
            print("="*70)
            
            execution_log = {
                'timestamp': datetime.now().isoformat(),
                'confirmed_entries': list(confirmed_entries.keys()),
                'rejected_entries': list(rejected_entries.keys()),
                'trades_executed': [],
                'errors': []
            }
            
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    # Get account value before
                    account_value_before = ib_exec.get_account_value()
                    
                    # Initialize position manager
                    position_manager = PositionManager(ib_exec.ib)
                    
                    # Get positions before
                    positions_before = ib_exec.get_current_positions()
                    
                    # Execute rebalance with confirmed entries
                    trades = ib_exec.execute_rebalance(
                        target_weights, 
                        position_manager=position_manager,
                        atr_data=atr_data
                    )
                    self.last_trades = trades
                    
                    # Get positions after
                    positions_after = ib_exec.get_current_positions()
                    
                    # Update current positions
                    self.current_positions = positions_after
                    
                    # Log execution details
                    execution_log['trades_executed'] = trades if trades else []
                    execution_log['account_value_before'] = account_value_before
                    execution_log['positions_before'] = positions_before
                    execution_log['positions_after'] = positions_after
                    
                    # Display execution summary
                    self.display_execution_summary(
                        confirmed_entries, 
                        rejected_entries,
                        positions_before, 
                        positions_after, 
                        trades
                    )
                    
                    # Save execution report
                    self.save_execution_report(execution_log)
                    
                    # Send Telegram notification
                    if self.telegram:
                        try:
                            # Build positions summary for telegram
                            positions_summary = self._build_positions_summary(
                                positions_before, positions_after
                            )
                            
                            self.telegram.send_morning_alert(
                                confirmed_entries,
                                rejected_entries,
                                trades,
                                positions_summary
                            )
                            print("+ Telegram notification sent")
                        except Exception as e:
                            print(f"! Telegram notification failed: {e}")
                    
                    print("\n" + "="*70)
                    print("MORNING RUN COMPLETE")
                    print("="*70)
                    print(f"+ Confirmed entries: {len(confirmed_entries)}")
                    print(f"+ Rejected entries: {len(rejected_entries)}")
                    print(f"+ Trades executed: {len(trades) if trades else 0}")
                    print(f"+ Report saved to: morning_report_{datetime.now().strftime('%Y%m%d')}.txt")
                    if self.telegram:
                        print(f"+ Telegram alert sent")
                    print("="*70)
                else:
                    print("\n" + "="*70)
                    print("CONNECTION FAILED")
                    print("="*70)
                    print("- Failed to connect to IB")
                    print("- No trades were executed")
                    print("- Check IB Gateway/TWS is running")
                    print("="*70)
                    execution_log['errors'].append("Failed to connect to IB")
        
        except Exception as e:
            print(f"\n" + "="*70)
            print("ERROR IN MORNING RUN")
            print("="*70)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print("="*70)
            if 'execution_log' in locals():
                execution_log['errors'].append(str(e))
            
            # Send error alert
            if self.telegram:
                try:
                    self.telegram.send_error_alert(str(e), "Morning Run - Trade Execution")
                except:
                    pass
    
    def _build_positions_summary(self, positions_before: dict, positions_after: dict) -> dict:
        """Build positions summary for Telegram"""
        all_tickers = set(list(positions_before.keys()) + list(positions_after.keys()))
        
        added = []
        removed = []
        adjusted = []
        
        for ticker in sorted(all_tickers):
            before = positions_before.get(ticker, 0)
            after = positions_after.get(ticker, 0)
            
            if before == 0 and after > 0:
                added.append(f"{ticker} (+{after:.2f})")
            elif before > 0 and after == 0:
                removed.append(f"{ticker} (-{before:.2f})")
            elif before != after:
                change = after - before
                adjusted.append(f"{ticker} ({change:+.2f})")
        
        return {
            'added': added,
            'removed': removed,
            'adjusted': adjusted
        }
    
    def display_night_plan(self, signals: dict, ema_data: dict):
        """Display detailed plan for tomorrow's execution"""
        print("\n" + "="*70)
        print("TOMORROW'S EXECUTION PLAN")
        print("="*70)
        
        print(f"\nMarket Regime: {signals['current_regime']}")
        print(f"Top Quadrants: {signals['top_quadrants'][0]}, {signals['top_quadrants'][1]}")
        print(f"Total Leverage: {signals['total_leverage']:.2f}x")
        
        # Get real account value from IB
        account_value = self._get_account_value()
        
        # Get current positions
        current_positions = {}
        try:
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    current_positions = ib_exec.get_current_positions()
        except:
            pass
        
        # Show current positions
        if current_positions:
            print(f"\n{'='*70}")
            print("CURRENT POSITIONS")
            print(f"{'='*70}")
            print(f"{'Ticker':<8} {'Quantity':<12} {'Est. Value':<15}")
            print("-"*70)
            
            total_current_value = 0
            for ticker, qty in sorted(current_positions.items()):
                # Rough estimate (would need prices for exact)
                est_value = qty * 100  # Placeholder
                print(f"{ticker:<8} {qty:>10.2f}  ${est_value:>12,.2f}")
                total_current_value += est_value
            
            print("-"*70)
            print(f"{'TOTAL':<8} {'':>10}  ${total_current_value:>12,.2f}")
        else:
            print(f"\n{'='*70}")
            print("CURRENT POSITIONS: None (or unable to fetch)")
            print(f"{'='*70}")
        
        # Show target positions
        print(f"\n{'='*70}")
        print("TARGET POSITIONS (ALL)")
        print(f"{'='*70}")
        print(f"{'Ticker':<8} {'Weight %':<10} {'Target $':<15} {'Current EMA':<15}")
        print("-"*70)
        
        sorted_weights = sorted(signals['target_weights'].items(), 
                               key=lambda x: x[1], reverse=True)
        
        total_target_value = 0
        for ticker, weight in sorted_weights:
            target_usd = account_value * weight
            total_target_value += target_usd
            ema = ema_data.get(ticker, 'N/A')
            ema_str = f"${ema:.2f}" if ema != 'N/A' else 'N/A'
            
            print(f"{ticker:<8} {weight*100:>8.2f}%  ${target_usd:>12,.2f}  {ema_str:<15}")
        
        print("-"*70)
        print(f"{'TOTAL':<8} {signals['total_leverage']*100:>8.2f}%  ${total_target_value:>12,.2f}")
        
        # Show pending entries with USD values
        print(f"\n{'='*70}")
        print("PENDING ENTRIES FOR TOMORROW (Subject to EMA confirmation)")
        print(f"{'='*70}")
        print(f"{'Ticker':<8} {'Target $':<15} {'Weight %':<10} {'Status':<20}")
        print("-"*70)
        
        for ticker, weight in sorted_weights:
            target_usd = account_value * weight
            print(f"{ticker:<8} ${target_usd:>12,.2f}  {weight*100:>8.2f}%  Pending confirmation")
        
        print(f"\n{'='*70}")
        print("TOMORROW MORNING PROCESS:")
        print(f"{'='*70}")
        print(f"1. Re-fetch current prices and EMAs")
        print(f"2. For each position above:")
        print(f"   - Check: Is price still > EMA?")
        print(f"   - YES -> Execute entry at market open")
        print(f"   - NO  -> Reject entry (trend broken)")
        print(f"3. Expected: ~{len(sorted_weights) * 0.28:.0f} positions rejected (~28%)")
        print(f"4. Confirmed entries: Place ATR 2.0x stop orders")
        print(f"5. Existing positions: Adjust if delta > 5%")
        print("="*70)
    
    def save_night_plan(self, signals: dict, ema_data: dict):
        """Save detailed plan to file"""
        filename = f"night_plan_{datetime.now().strftime('%Y%m%d')}.txt"
        
        # Get real account value from IB
        account_value = self._get_account_value()
        
        # Get current positions
        current_positions = {}
        try:
            with IBExecutor(port=self.ib_port) as ib_exec:
                if ib_exec.connected:
                    current_positions = ib_exec.get_current_positions()
        except:
            pass
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write(f"NIGHT SIGNAL GENERATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Market Regime: {signals['current_regime']}\n")
            f.write(f"Top Quadrants: {signals['top_quadrants'][0]}, {signals['top_quadrants'][1]}\n")
            f.write(f"Total Target Leverage: {signals['total_leverage']:.2f}x\n")
            f.write(f"Account Value: ${account_value:,.2f}\n\n")
            
            f.write("QUADRANT SCORES:\n")
            f.write("-"*80 + "\n")
            for quad, score in signals['quadrant_scores'].items():
                f.write(f"  {quad}: {score:>7.2f}%\n")
            
            # Current positions
            f.write("\n" + "="*80 + "\n")
            f.write("CURRENT POSITIONS\n")
            f.write("="*80 + "\n")
            if current_positions:
                f.write(f"{'Ticker':<8} {'Quantity':<12}\n")
                f.write("-"*80 + "\n")
                for ticker, qty in sorted(current_positions.items()):
                    f.write(f"{ticker:<8} {qty:>10.2f}\n")
            else:
                f.write("None (or unable to fetch)\n")
            
            # Target positions
            f.write("\n" + "="*80 + "\n")
            f.write("TARGET POSITIONS (ALL)\n")
            f.write("="*80 + "\n")
            f.write(f"{'Ticker':<8} {'Weight %':<10} {'Target $':<15} {'Current EMA':<15}\n")
            f.write("-"*80 + "\n")
            
            sorted_weights = sorted(signals['target_weights'].items(), 
                                   key=lambda x: x[1], reverse=True)
            
            total_target_value = 0
            for ticker, weight in sorted_weights:
                target_usd = account_value * weight
                total_target_value += target_usd
                ema = ema_data.get(ticker, 'N/A')
                ema_str = f"${ema:.2f}" if ema != 'N/A' else 'N/A'
                f.write(f"{ticker:<8} {weight*100:>8.2f}%  ${target_usd:>12,.2f}  {ema_str:<15}\n")
            
            f.write("-"*80 + "\n")
            f.write(f"{'TOTAL':<8} {signals['total_leverage']*100:>8.2f}%  ${total_target_value:>12,.2f}\n")
            
            # Pending entries
            f.write("\n" + "="*80 + "\n")
            f.write("PENDING ENTRIES FOR TOMORROW (Subject to EMA confirmation)\n")
            f.write("="*80 + "\n")
            f.write(f"{'Ticker':<8} {'Target $':<15} {'Weight %':<10}\n")
            f.write("-"*80 + "\n")
            
            for ticker, weight in sorted_weights:
                target_usd = account_value * weight
                f.write(f"{ticker:<8} ${target_usd:>12,.2f}  {weight*100:>8.2f}%\n")
            
            f.write("-"*80 + "\n")
            f.write(f"TOTAL:    ${total_target_value:>12,.2f}  {signals['total_leverage']*100:>8.2f}%\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("TOMORROW'S PROCESS:\n")
            f.write("="*80 + "\n")
            f.write("1. Morning Run (9:29 AM):\n")
            f.write(f"   python live_trader.py --step morning --live --port {self.ib_port}\n\n")
            f.write("2. Entry Confirmation:\n")
            f.write("   - Re-check EMA for each pending position\n")
            f.write("   - Only enter if price > EMA (trend confirmed)\n")
            f.write(f"   - Expected rejections: ~{len(sorted_weights) * 0.28:.0f} positions (~28%)\n\n")
            f.write("3. Execution:\n")
            f.write("   - Enter confirmed positions at market open\n")
            f.write("   - Place ATR 2.0x stop orders\n")
            f.write("   - Adjust existing positions (delta-only if >5%)\n\n")
            f.write("4. Result:\n")
            f.write("   - Execution report saved to morning_report_YYYYMMDD.txt\n")
            f.write("   - Trade history updated in trade_history.csv\n")
            f.write("   - Position state updated in position_state.json\n")
            f.write("   - Telegram notification sent\n")
            f.write("="*80 + "\n")
        
        print(f"+ Plan saved to {filename}")
    
    def display_execution_summary(self, confirmed, rejected, positions_before, positions_after, trades):
        """Display detailed execution summary"""
        print("\n" + "="*70)
        print("EXECUTION SUMMARY")
        print("="*70)
        
        print(f"\nCONFIRMATION RESULTS:")
        print(f"  Confirmed entries: {len(confirmed)}")
        print(f"  Rejected entries: {len(rejected)}")
        if len(confirmed) + len(rejected) > 0:
            rejection_rate = len(rejected) / (len(confirmed) + len(rejected)) * 100
            print(f"  Rejection rate: {rejection_rate:.1f}%")
        
        if confirmed:
            print(f"\n  Confirmed positions:")
            for ticker in sorted(confirmed.keys()):
                print(f"    + {ticker}")
        
        if rejected:
            print(f"\n  Rejected positions:")
            for ticker in sorted(rejected.keys()):
                print(f"    - {ticker}")
        
        print(f"\nPOSITION CHANGES:")
        all_tickers = set(list(positions_before.keys()) + list(positions_after.keys()))
        
        added = []
        removed = []
        adjusted = []
        unchanged = []
        
        for ticker in sorted(all_tickers):
            before = positions_before.get(ticker, 0)
            after = positions_after.get(ticker, 0)
            
            if before == 0 and after > 0:
                added.append(f"{ticker} (+{after:.2f})")
            elif before > 0 and after == 0:
                removed.append(f"{ticker} (-{before:.2f})")
            elif before != after:
                change = after - before
                adjusted.append(f"{ticker} ({before:.2f} -> {after:.2f}, {change:+.2f})")
            else:
                unchanged.append(ticker)
        
        if added:
            print(f"  New positions: {len(added)}")
            for item in added:
                print(f"    + {item}")
        
        if removed:
            print(f"  Closed positions: {len(removed)}")
            for item in removed:
                print(f"    - {item}")
        
        if adjusted:
            print(f"  Adjusted positions: {len(adjusted)}")
            for item in adjusted:
                print(f"    ~ {item}")
        
        if unchanged:
            print(f"  Unchanged positions: {len(unchanged)}")
        
        if trades:
            print(f"\nTRADES EXECUTED: {len(trades)}")
            for i, trade in enumerate(trades, 1):
                print(f"  {i}. {trade}")
        else:
            print(f"\nTRADES EXECUTED: 0 (no changes needed)")
        
        print("="*70)
    
    def save_execution_report(self, execution_log: dict):
        """Save detailed execution report to file"""
        filename = f"morning_report_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(filename, 'w') as f:
            f.write("="*70 + "\n")
            f.write(f"MORNING EXECUTION REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write("CONFIRMATION RESULTS:\n")
            f.write("-"*70 + "\n")
            f.write(f"Confirmed entries: {len(execution_log.get('confirmed_entries', []))}\n")
            f.write(f"Rejected entries: {len(execution_log.get('rejected_entries', []))}\n")
            
            total = len(execution_log.get('confirmed_entries', [])) + len(execution_log.get('rejected_entries', []))
            if total > 0:
                rejection_rate = len(execution_log.get('rejected_entries', [])) / total * 100
                f.write(f"Rejection rate: {rejection_rate:.1f}%\n")
            
            if execution_log.get('confirmed_entries'):
                f.write("\nConfirmed:\n")
                for ticker in execution_log['confirmed_entries']:
                    f.write(f"  + {ticker}\n")
            
            if execution_log.get('rejected_entries'):
                f.write("\nRejected:\n")
                for ticker in execution_log['rejected_entries']:
                    f.write(f"  - {ticker}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("POSITION CHANGES:\n")
            f.write("="*70 + "\n")
            
            positions_before = execution_log.get('positions_before', {})
            positions_after = execution_log.get('positions_after', {})
            
            all_tickers = set(list(positions_before.keys()) + list(positions_after.keys()))
            
            f.write("\nBefore:\n")
            for ticker in sorted(positions_before.keys()):
                f.write(f"  {ticker}: {positions_before[ticker]:.2f}\n")
            
            f.write("\nAfter:\n")
            for ticker in sorted(positions_after.keys()):
                f.write(f"  {ticker}: {positions_after[ticker]:.2f}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("TRADES EXECUTED:\n")
            f.write("="*70 + "\n")
            
            trades = execution_log.get('trades_executed', [])
            if trades:
                for i, trade in enumerate(trades, 1):
                    f.write(f"{i}. {trade}\n")
            else:
                f.write("No trades executed (no changes needed)\n")
            
            if execution_log.get('errors'):
                f.write("\n" + "="*70 + "\n")
                f.write("ERRORS:\n")
                f.write("="*70 + "\n")
                for error in execution_log['errors']:
                    f.write(f"  ! {error}\n")
            
            f.write("\n" + "="*70 + "\n")
            f.write("FILES UPDATED:\n")
            f.write("="*70 + "\n")
            f.write("  position_state.json - Current position tracking\n")
            f.write("  trade_history.csv - Trade log\n")
            f.write("  entry_rejections.csv - Rejected entries log\n")
            f.write("="*70 + "\n")
        
        print(f"+ Execution report saved to {filename}")
    
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
        
        print(f"+ Signals saved to {filename}")
    
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
  python live_trader.py --step night --port 4001
  
  # Morning run (before open) - Confirm and execute
  python live_trader.py --step morning --live --port 4001
  
  # Scheduled mode (runs both automatically)
  python live_trader.py --mode scheduled --live --port 4001
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
    parser.add_argument('--no-telegram', action='store_true',
                       help='Disable Telegram notifications')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.step and not args.mode:
        parser.error("Must specify either --step or --mode")
    
    if args.step and args.mode:
        parser.error("Cannot use both --step and --mode")
    
    # Initialize trader
    trader = LiveTrader(
        ib_port=args.port,
        dry_run=not args.live,
        enable_telegram=not args.no_telegram
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
