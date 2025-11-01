"""
Sync Manually Entered Positions
================================

After manually entering positions in IB, run this to:
1. Query IB for current positions
2. Query IB for existing stop orders
3. Match with expected backtest state
4. Create position_state.json
5. Enable ongoing system to manage them

Run ONCE after manual initialization

Usage:
    python sync_manual_positions.py --port 4002  # Paper trading
    python sync_manual_positions.py --port 4001  # Live trading
"""

from ib_insync import IB, CFD
import json
from datetime import datetime
from typing import Dict, List


class ManualPositionSync:
    """Sync manually entered positions with position tracking system"""
    
    def __init__(self, ib_port=4002):
        self.ib_port = ib_port
        self.ib = None
        self.positions = []
        self.stop_orders = {}
        self.expected_positions = {}
    
    def connect_to_ib(self):
        """Connect to Interactive Brokers"""
        print(f"\nConnecting to IB on port {self.ib_port}...")
        
        self.ib = IB()
        
        try:
            self.ib.connect('127.0.0.1', self.ib_port, clientId=1)
            print("+ Connected to IB")
            return True
        except Exception as e:
            print(f"- Failed to connect: {e}")
            print("\nMake sure:")
            print("  1. IB Gateway or TWS is running")
            print("  2. API connections are enabled")
            print("  3. Port is correct (7497 for TWS paper, 4002 for Gateway paper)")
            return False
    
    def get_ib_positions(self):
        """Get current positions from IB"""
        print("\n" + "="*80)
        print("STEP 1: READING POSITIONS FROM IB")
        print("="*80)
        
        self.positions = self.ib.positions()
        
        if len(self.positions) == 0:
            print("\n! WARNING: No positions found in IB")
            print("  Make sure you've manually entered all positions first!")
            return False
        
        print(f"\nFound {len(self.positions)} positions:")
        for pos in self.positions:
            symbol = pos.contract.symbol if hasattr(pos.contract, 'symbol') else pos.contract.localSymbol
            quantity = pos.position
            avg_cost = pos.avgCost
            market_value = pos.marketValue
            unrealized_pnl = pos.unrealizedPNL
            
            print(f"  {symbol}:")
            print(f"    Quantity: {quantity:.2f}")
            print(f"    Avg Cost: ${avg_cost:.2f}")
            print(f"    Market Value: ${market_value:,.2f}")
            print(f"    Unrealized P&L: ${unrealized_pnl:,.2f}")
        
        return True
    
    def get_stop_orders(self):
        """Get stop orders from IB"""
        print("\n" + "="*80)
        print("STEP 2: READING STOP ORDERS FROM IB")
        print("="*80)
        
        orders = self.ib.openOrders()
        
        print(f"\nFound {len(orders)} open orders")
        
        for order in orders:
            symbol = order.contract.symbol if hasattr(order.contract, 'symbol') else order.contract.localSymbol
            
            if order.orderType == 'STP':  # Stop loss order
                stop_price = order.auxPrice
                order_id = order.orderId
                
                print(f"  {symbol}: Stop @ ${stop_price:.2f} (Order ID: {order_id})")
                
                self.stop_orders[symbol] = {
                    'stop_price': stop_price,
                    'order_id': order_id,
                    'order': order
                }
            else:
                print(f"  {symbol}: {order.orderType} order (not a stop)")
        
        if len(self.stop_orders) == 0:
            print("\n! WARNING: No stop orders found!")
            print("  You should have stop orders for all positions")
            print("  Consider placing them before syncing")
        
        return True
    
    def get_expected_positions(self):
        """Get expected positions from backtest"""
        print("\n" + "="*80)
        print("STEP 3: GETTING EXPECTED POSITIONS FROM BACKTEST")
        print("="*80)
        
        try:
            from initialize_strategy import StrategyInitializer
            
            initializer = StrategyInitializer()
            
            # Run backtest to today
            print("\nRunning backtest to today...")
            initializer.run_backtest_to_today()
            
            # Get current positions with stops
            positions_with_stops = initializer.get_current_positions_with_stops()
            
            # Filter valid positions (not stopped)
            valid_positions, stopped_positions = initializer.check_stops_not_hit(positions_with_stops)
            
            self.expected_positions = valid_positions
            
            print(f"\nExpected positions from backtest: {len(self.expected_positions)}")
            for ticker, info in self.expected_positions.items():
                print(f"  {ticker}:")
                print(f"    Expected stop: ${info['stop_price']:.2f}")
                print(f"    Entry date: {info['entry_date'].date()}")
                print(f"    Entry price: ${info['entry_price']:.2f}")
            
            if len(stopped_positions) > 0:
                print(f"\n! {len(stopped_positions)} positions would have been stopped:")
                for ticker in stopped_positions.keys():
                    print(f"  - {ticker}")
            
            return True
            
        except Exception as e:
            print(f"\n! WARNING: Could not get expected positions: {e}")
            print("  Will sync based on IB data only")
            return False
    
    def match_and_create_state(self):
        """Match IB positions with expected positions and create state"""
        print("\n" + "="*80)
        print("STEP 4: MATCHING & CREATING POSITION STATE")
        print("="*80)
        
        position_state = {
            'positions': {},
            'metadata': {
                'last_updated': datetime.now().isoformat(),
                'initialized_manually': True,
                'sync_date': datetime.now().isoformat(),
                'ib_port': self.ib_port
            }
        }
        
        warnings = []
        
        for pos in self.positions:
            symbol = pos.contract.symbol if hasattr(pos.contract, 'symbol') else pos.contract.localSymbol
            quantity = abs(pos.position)
            avg_cost = pos.avgCost
            
            print(f"\nProcessing {symbol}...")
            
            # Get stop order from IB
            stop_price = None
            stop_order_id = None
            if symbol in self.stop_orders:
                stop_price = self.stop_orders[symbol]['stop_price']
                stop_order_id = self.stop_orders[symbol]['order_id']
                print(f"  + Found stop order: ${stop_price:.2f}")
            else:
                warnings.append(f"{symbol}: No stop order found in IB")
                print(f"  ! No stop order found")
            
            # Get expected info from backtest
            entry_date = None
            atr = None
            expected_stop = None
            
            if symbol in self.expected_positions:
                expected = self.expected_positions[symbol]
                expected_stop = expected['stop_price']
                entry_date = expected['entry_date']
                atr = expected.get('atr', None)
                
                print(f"  + Matched with backtest")
                print(f"    Expected stop: ${expected_stop:.2f}")
                print(f"    Entry date: {entry_date.date()}")
                
                # Check if stops match
                if stop_price and abs(stop_price - expected_stop) > 0.5:
                    warnings.append(f"{symbol}: Stop mismatch (IB: ${stop_price:.2f}, Expected: ${expected_stop:.2f})")
                    print(f"  ! Stop price mismatch")
                
                # Use expected stop if no stop order in IB
                if not stop_price:
                    stop_price = expected_stop
                    print(f"  + Using expected stop: ${stop_price:.2f}")
            else:
                warnings.append(f"{symbol}: Not in expected positions from backtest")
                print(f"  ! Not in expected backtest positions")
            
            # Create position entry
            position_state['positions'][symbol] = {
                'quantity': quantity,
                'entry_price': avg_cost,
                'stop_price': stop_price,
                'stop_order_id': stop_order_id,
                'manually_entered': True
            }
            
            # Add optional fields if available
            if entry_date:
                position_state['positions'][symbol]['entry_date'] = entry_date.isoformat() if hasattr(entry_date, 'isoformat') else str(entry_date)
            if atr:
                position_state['positions'][symbol]['atr'] = float(atr)
        
        # Save position state
        with open('position_state.json', 'w') as f:
            json.dump(position_state, f, indent=2)
        
        print("\n" + "="*80)
        print("SYNC COMPLETE")
        print("="*80)
        print(f"\n+ Synced {len(position_state['positions'])} positions")
        print(f"+ State saved to: position_state.json")
        
        if warnings:
            print(f"\n! {len(warnings)} warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return position_state
    
    def display_summary(self, position_state):
        """Display final summary"""
        print("\n" + "="*80)
        print("POSITION STATE SUMMARY")
        print("="*80)
        
        for ticker, info in position_state['positions'].items():
            print(f"\n{ticker}:")
            print(f"  Quantity: {info['quantity']:.2f}")
            print(f"  Entry: ${info['entry_price']:.2f}")
            if info.get('stop_price'):
                print(f"  Stop: ${info['stop_price']:.2f}")
                risk_pct = (info['entry_price'] - info['stop_price']) / info['entry_price'] * 100
                print(f"  Risk: {risk_pct:.1f}%")
            if info.get('stop_order_id'):
                print(f"  Stop Order ID: {info['stop_order_id']}")
            if info.get('entry_date'):
                print(f"  Entry Date: {info['entry_date']}")
        
        print("\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print("\n1. Verify the position state above is correct")
        print("\n2. You can now run the daily system:")
        print("   Night:   python live_trader.py --step night")
        print("   Morning: python live_trader.py --step morning --live --port", self.ib_port)
        print("\n3. The system will:")
        print("   - Track your manually entered positions")
        print("   - Manage stops automatically")
        print("   - Adjust positions based on signals")
        print("   - Add/remove positions as needed")
        print("="*80)
    
    def disconnect(self):
        """Disconnect from IB"""
        if self.ib and self.ib.isConnected():
            self.ib.disconnect()
            print("\n+ Disconnected from IB")
    
    def run_sync(self):
        """Run complete sync process"""
        print("\n" + "="*80)
        print("SYNC MANUALLY ENTERED POSITIONS")
        print("="*80)
        print("\nThis will:")
        print("  1. Read your positions from IB")
        print("  2. Read your stop orders from IB")
        print("  3. Match with expected backtest state")
        print("  4. Create position_state.json")
        print("  5. Enable daily system to manage them")
        print("="*80)
        
        try:
            # Step 1: Connect to IB
            if not self.connect_to_ib():
                return False
            
            # Step 2: Get IB positions
            if not self.get_ib_positions():
                self.disconnect()
                return False
            
            # Step 3: Get stop orders
            self.get_stop_orders()
            
            # Step 4: Get expected positions (optional)
            self.get_expected_positions()
            
            # Step 5: Match and create state
            position_state = self.match_and_create_state()
            
            # Step 6: Display summary
            self.display_summary(position_state)
            
            # Step 7: Disconnect
            self.disconnect()
            
            return True
            
        except Exception as e:
            print(f"\n- ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.disconnect()
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync manually entered positions with position tracking system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Paper trading account
  python sync_manual_positions.py --port 4002
  
  # Live trading account  
  python sync_manual_positions.py --port 4001

Prerequisites:
  1. IB Gateway or TWS must be running
  2. API connections must be enabled
  3. You must have manually entered all positions
  4. You should have placed stop orders for all positions
        """
    )
    
    parser.add_argument('--port', type=int, default=4002,
                       help='IB port (7497=TWS paper, 4002=Gateway paper, 7496=TWS live, 4001=Gateway live)')
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("IMPORTANT: Run this AFTER manually entering positions in IB")
    print("="*80)
    print("\nBefore running this, make sure you have:")
    print("  [x] Entered all positions in IB")
    print("  [x] Placed stop orders for all positions")
    print("  [x] IB Gateway/TWS is running")
    print("  [x] API connections are enabled")
    print("\nThis script will create 'position_state.json'")
    print("="*80)
    
    confirm = input("\nReady to sync? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        syncer = ManualPositionSync(ib_port=args.port)
        success = syncer.run_sync()
        
        if success:
            print("\n[SUCCESS] Sync complete!")
        else:
            print("\n[FAILED] Sync failed - see errors above")
    else:
        print("\nCancelled - no changes made")

