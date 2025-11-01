"""
Test Interactive Brokers Connection
Simple script to verify IB Gateway/TWS is set up correctly
"""

from ib_insync import IB, Stock
import sys

def test_connection(port=4002):
    """
    Test connection to IB
    
    Args:
        port: 4002 for paper trading, 4001 for live
    """
    print("="*60)
    print("TESTING INTERACTIVE BROKERS CONNECTION")
    print("="*60)
    print(f"Port: {port} ({'Paper' if port == 4002 else 'Live'})")
    print()
    
    try:
        # Create IB instance
        ib = IB()
        
        # Connect
        print("Connecting to IB...")
        ib.connect('127.0.0.1', port, clientId=1)
        
        if ib.isConnected():
            print("✅ Connected successfully!")
            print()
            
            # Get account info
            accounts = ib.managedAccounts()
            print(f"Accounts: {accounts}")
            print()
            
            # Get account value
            print("Account Values:")
            print("-" * 60)
            account_values = ib.accountValues()
            
            key_metrics = ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 
                          'GrossPositionValue', 'AvailableFunds']
            
            for v in account_values:
                if v.tag in key_metrics:
                    print(f"  {v.tag:20s}: ${float(v.value):,.2f}")
            
            print()
            
            # Test market data with QQQ
            print("Testing Market Data (QQQ):")
            print("-" * 60)
            
            qqq = Stock('QQQ', 'SMART', 'USD')
            ib.qualifyContracts(qqq)
            
            ticker = ib.reqMktData(qqq)
            ib.sleep(2)  # Wait for data
            
            if ticker.last:
                print(f"  QQQ Last Price: ${ticker.last:.2f}")
                print(f"  Bid: ${ticker.bid:.2f}")
                print(f"  Ask: ${ticker.ask:.2f}")
                print(f"  Volume: {ticker.volume:,}")
                print("✅ Market data working!")
            else:
                print("⚠️ No market data received (might be outside market hours)")
            
            print()
            
            # Disconnect
            ib.disconnect()
            
            print("="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
            print()
            print("Next steps:")
            print("1. Run: python signal_generator.py")
            print("2. Run: python live_trader.py --mode once --dry-run")
            print("3. Review output before live trading")
            print()
            
            return True
            
        else:
            print("❌ Connection failed!")
            return False
            
    except ConnectionRefusedError:
        print("="*60)
        print("❌ CONNECTION REFUSED")
        print("="*60)
        print()
        print("Possible issues:")
        print("1. IB Gateway/TWS is not running")
        print("2. Wrong port (paper=4002, live=4001)")
        print("3. API not enabled in IB settings")
        print("4. Firewall blocking connection")
        print()
        print("Solutions:")
        print("1. Launch IB Gateway")
        print("2. Go to Configure → Settings → API")
        print("3. Enable 'ActiveX and Socket Clients'")
        print("4. Set port to 4002 (paper) or 4001 (live)")
        print("5. Add 127.0.0.1 to trusted IPs")
        print("6. Restart IB Gateway")
        print()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print(f"Error type: {type(e).__name__}")
        print()
        return False

if __name__ == "__main__":
    # Check command line args
    port = 4002  # Default to paper
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--live':
            port = 4001
            print("⚠️ WARNING: Testing LIVE account connection!")
            print()
    
    success = test_connection(port)
    
    if not success:
        sys.exit(1)



