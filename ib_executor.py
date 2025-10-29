"""
Interactive Brokers Executor for Macro Quadrant Strategy
=========================================================

Executes trades using Interactive Brokers API with CFDs
"""

from ib_insync import *
import pandas as pd
from typing import Dict, List
from datetime import datetime
import time


class IBExecutor:
    """Execute trades via Interactive Brokers API using CFDs"""
    
    def __init__(self, host='127.0.0.1', port=7497, client_id=1):
        """
        Initialize IB connection
        
        Args:
            host: IB Gateway/TWS host (default localhost)
            port: 7497 for paper trading, 7496 for live (TWS)
                  4002 for paper trading, 4001 for live (IB Gateway)
            client_id: Unique client ID
        """
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id
        self.connected = False
        
        # CFD contract mapping (ticker -> IB CFD contract)
        self.cfd_contracts = {}
        
    def connect(self):
        """Connect to Interactive Brokers"""
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            print(f"✓ Connected to IB at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to IB: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IB"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("✓ Disconnected from IB")
    
    def create_cfd_contract(self, ticker: str) -> CFD:
        """
        Create CFD contract for a ticker
        
        Args:
            ticker: ETF ticker (e.g., 'QQQ', 'SPY')
        
        Returns:
            CFD contract object
        
        Note: For ETFs, IB typically offers CFDs on the underlying index
        For example:
        - SPY -> US500 CFD
        - QQQ -> USTEC CFD (NASDAQ-100)
        - IWM -> US2000 CFD (Russell 2000)
        - DIA -> INDU CFD (Dow Jones)
        """
        # ETF to CFD mapping
        etf_to_cfd = {
            'SPY': 'US500',      # S&P 500
            'QQQ': 'USTEC',      # NASDAQ-100
            'IWM': 'US2000',     # Russell 2000
            'DIA': 'INDU',       # Dow Jones
            'EFA': 'EUSTX50',    # European stocks
            'EEM': 'CHINA50',    # Emerging markets
            # Add more mappings as needed
            # For most ETFs without direct CFD, you may need to:
            # 1. Use the ETF directly (if IB offers)
            # 2. Use index futures
            # 3. Use basket of stocks
        }
        
        cfd_symbol = etf_to_cfd.get(ticker, ticker)
        
        # Create CFD contract
        contract = CFD(cfd_symbol, currency='USD')
        
        # Qualify contract with IB
        try:
            qualified = self.ib.qualifyContracts(contract)
            if qualified:
                print(f"  ✓ Qualified {ticker} -> {cfd_symbol} CFD")
                return qualified[0]
            else:
                print(f"  ✗ Could not qualify {ticker} CFD")
                return None
        except Exception as e:
            print(f"  ✗ Error qualifying {ticker}: {e}")
            return None
    
    def get_account_value(self) -> float:
        """Get current account net liquidation value"""
        if not self.connected:
            print("Not connected to IB")
            return 0.0
        
        account_values = self.ib.accountValues()
        for item in account_values:
            if item.tag == 'NetLiquidation' and item.currency == 'USD':
                return float(item.value)
        return 0.0
    
    def get_current_positions(self) -> Dict[str, float]:
        """
        Get current positions
        
        Returns:
            Dict of {ticker: quantity}
        """
        if not self.connected:
            return {}
        
        positions = {}
        for position in self.ib.positions():
            if isinstance(position.contract, CFD):
                symbol = position.contract.symbol
                positions[symbol] = position.position
        
        return positions
    
    def calculate_position_sizes(self, target_weights: Dict[str, float], 
                                 account_value: float) -> Dict[str, float]:
        """
        Calculate CFD position sizes in notional USD
        
        Args:
            target_weights: Dict of {ticker: weight} where weight is % of capital
            account_value: Current account value in USD
        
        Returns:
            Dict of {ticker: notional_usd_value}
        """
        position_sizes = {}
        
        for ticker, weight in target_weights.items():
            notional_value = account_value * weight
            position_sizes[ticker] = notional_value
        
        return position_sizes
    
    def get_market_price(self, contract: CFD) -> float:
        """Get current market price for a contract"""
        try:
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for market data
            
            if ticker.marketPrice():
                price = ticker.marketPrice()
            elif ticker.close:
                price = ticker.close
            else:
                price = None
            
            self.ib.cancelMktData(contract)
            return price
        except Exception as e:
            print(f"Error getting price for {contract.symbol}: {e}")
            return None
    
    def place_order(self, contract: CFD, quantity: float, action: str = 'BUY') -> Order:
        """
        Place a market order
        
        Args:
            contract: CFD contract
            quantity: Number of contracts (can be fractional for CFDs)
            action: 'BUY' or 'SELL'
        
        Returns:
            Order object
        """
        if not self.connected:
            print("Not connected to IB")
            return None
        
        # Create market order
        order = MarketOrder(action, quantity)
        
        # Place order
        trade = self.ib.placeOrder(contract, order)
        
        print(f"  → {action} {quantity:.4f} {contract.symbol} CFD")
        
        return trade
    
    def execute_rebalance(self, target_weights: Dict[str, float]):
        """
        Execute portfolio rebalance
        
        Args:
            target_weights: Dict of {ticker: weight} where weight is % of capital
        """
        if not self.connected:
            print("Not connected to IB")
            return
        
        print("\n" + "="*60)
        print("EXECUTING REBALANCE")
        print("="*60)
        
        # Get account value
        account_value = self.get_account_value()
        print(f"\nAccount Value: ${account_value:,.2f}")
        
        # Get current positions
        current_positions = self.get_current_positions()
        print(f"Current Positions: {len(current_positions)}")
        
        # Calculate target position sizes
        target_sizes = self.calculate_position_sizes(target_weights, account_value)
        
        print(f"\n📊 Target Portfolio:")
        print(f"  Positions: {len(target_sizes)}")
        print(f"  Total Notional: ${sum(target_sizes.values()):,.2f}")
        
        # Execute trades
        print(f"\n🔄 Executing Trades:")
        
        executed_trades = []
        
        # Close positions not in target
        for ticker in current_positions:
            if ticker not in target_sizes:
                print(f"\n  Closing {ticker}...")
                contract = self.create_cfd_contract(ticker)
                if contract:
                    quantity = abs(current_positions[ticker])
                    action = 'SELL' if current_positions[ticker] > 0 else 'BUY'
                    trade = self.place_order(contract, quantity, action)
                    executed_trades.append(trade)
        
        # Open/adjust positions in target
        for ticker, target_notional in target_sizes.items():
            print(f"\n  Adjusting {ticker}...")
            contract = self.create_cfd_contract(ticker)
            
            if not contract:
                print(f"    ✗ Could not create contract for {ticker}")
                continue
            
            # Get current price
            price = self.get_market_price(contract)
            if not price:
                print(f"    ✗ Could not get price for {ticker}")
                continue
            
            # Calculate target quantity
            target_quantity = target_notional / price
            
            # Calculate current quantity
            current_quantity = current_positions.get(ticker, 0)
            
            # Calculate delta
            delta_quantity = target_quantity - current_quantity
            
            # Only trade if delta > threshold (e.g., 5% of target)
            if abs(delta_quantity) > abs(target_quantity) * 0.05:
                action = 'BUY' if delta_quantity > 0 else 'SELL'
                trade = self.place_order(contract, abs(delta_quantity), action)
                executed_trades.append(trade)
            else:
                print(f"    ⊘ Position close to target, no trade")
        
        print(f"\n✓ Executed {len(executed_trades)} trades")
        
        return executed_trades
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


if __name__ == "__main__":
    # Test connection
    print("Testing IB Connection...")
    print("\n⚠️  Make sure IB Gateway or TWS is running!")
    print("    Paper Trading: port 7497 (TWS) or 4002 (Gateway)")
    print("    Live Trading:  port 7496 (TWS) or 4001 (Gateway)")
    
    with IBExecutor(port=7497) as ib_exec:
        if ib_exec.connected:
            print("\n✓ Connection successful!")
            
            # Get account info
            account_value = ib_exec.get_account_value()
            print(f"\nAccount Value: ${account_value:,.2f}")
            
            # Get current positions
            positions = ib_exec.get_current_positions()
            print(f"Current Positions: {positions}")

