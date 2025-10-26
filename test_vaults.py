"""
Test script for Hyperliquid multi-vault functionality
"""

import asyncio
import json
import time
import aiohttp
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Test configuration
TEST_VAULTS = [
    {
        'name': 'Vault 1',
        'api_key': 'your_api_key_1',
        'secret_key': 'your_secret_key_1',
        'vault_address': '0x1234567890123456789012345678901234567890'
    },
    {
        'name': 'Vault 2', 
        'api_key': 'your_api_key_2',
        'secret_key': 'your_secret_key_2',
        'vault_address': '0x2345678901234567890123456789012345678901'
    },
    {
        'name': 'Vault 3',
        'api_key': 'your_api_key_3', 
        'secret_key': 'your_secret_key_3',
        'vault_address': '0x3456789012345678901234567890123456789012'
    }
]

BASE_URL = "https://api.hyperliquid.xyz"

class HyperliquidVaultTester:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, timestamp: str, data: str, secret_key: str) -> str:
        """Generate HMAC signature for authentication"""
        message = timestamp + data
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _make_request(self, method: str, endpoint: str, vault_config: dict, data: dict = None) -> dict:
        """Make authenticated request to Hyperliquid API for a specific vault"""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        url = f"{BASE_URL}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            'Content-Type': 'application/json',
            'X-HL-API-Key': vault_config['api_key'],
            'X-HL-Timestamp': timestamp,
            'X-HL-Vault-Address': vault_config['vault_address']
        }
        
        if data:
            data_str = json.dumps(data)
            headers['X-HL-Signature'] = self._generate_signature(timestamp, data_str, vault_config['secret_key'])
            payload = data_str
        else:
            payload = None
            
        try:
            async with self.session.request(method, url, headers=headers, data=payload) as response:
                result = await response.json()
                if response.status != 200:
                    print(f"❌ API Error for {vault_config['name']}: {response.status} - {result}")
                    return None
                return result
        except Exception as e:
            print(f"❌ Request failed for {vault_config['name']}: {e}")
            return None
    
    async def test_vault_connection(self, vault_config: dict) -> Optional[dict]:
        """Test connection to a specific vault"""
        print(f"\n🔍 Testing connection to {vault_config['name']}...")
        
        # Test account info endpoint
        account_info = await self._make_request('GET', '/account', vault_config)
        
        if account_info:
            print(f"✅ {vault_config['name']} connected successfully")
            print(f"   Account Value: ${account_info.get('accountValue', 0):.2f}")
            print(f"   Vault Address: {vault_config['vault_address']}")
            return account_info
        else:
            print(f"❌ Failed to connect to {vault_config['name']}")
            return None
    
    async def get_vault_positions(self, vault_config: dict) -> Dict:
        """Get positions for a specific vault"""
        account_info = await self._make_request('GET', '/account', vault_config)
        if not account_info:
            return {}
            
        positions = {}
        for position in account_info.get('positions', []):
            symbol = position.get('symbol')
            if symbol in ['BTC', 'ETH']:  # Only track BTC/ETH
                positions[symbol] = {
                    'size': float(position.get('size', 0)),
                    'entry_price': float(position.get('entryPrice', 0)),
                    'mark_price': float(position.get('markPrice', 0)),
                    'unrealized_pnl': float(position.get('unrealizedPnl', 0)),
                    'leverage': float(position.get('leverage', 1.0))
                }
        
        return positions
    
    async def get_aggregated_portfolio(self) -> Dict:
        """Get aggregated portfolio across all vaults"""
        print("\n📊 Aggregating portfolio across all vaults...")
        
        total_account_value = 0
        total_pnl = 0
        aggregated_positions = {'BTC': {'size': 0, 'value': 0}, 'ETH': {'size': 0, 'value': 0}}
        vault_summaries = []
        
        for vault_config in TEST_VAULTS:
            account_info = await self.test_vault_connection(vault_config)
            
            if account_info:
                vault_value = float(account_info.get('accountValue', 0))
                vault_pnl = float(account_info.get('unrealizedPnl', 0))
                
                total_account_value += vault_value
                total_pnl += vault_pnl
                
                # Get positions for this vault
                positions = await self.get_vault_positions(vault_config)
                
                vault_summary = {
                    'name': vault_config['name'],
                    'account_value': vault_value,
                    'unrealized_pnl': vault_pnl,
                    'positions': positions
                }
                vault_summaries.append(vault_summary)
                
                # Aggregate positions
                for symbol in ['BTC', 'ETH']:
                    if symbol in positions:
                        pos = positions[symbol]
                        aggregated_positions[symbol]['size'] += pos['size']
                        aggregated_positions[symbol]['value'] += abs(pos['size']) * pos['mark_price']
                
                print(f"   {vault_config['name']}: ${vault_value:.2f} (P&L: ${vault_pnl:.2f})")
            else:
                print(f"   {vault_config['name']}: ❌ Connection failed")
        
        portfolio_summary = {
            'total_account_value': total_account_value,
            'total_unrealized_pnl': total_pnl,
            'aggregated_positions': aggregated_positions,
            'vault_summaries': vault_summaries,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n📈 Portfolio Summary:")
        print(f"   Total Account Value: ${total_account_value:.2f}")
        print(f"   Total Unrealized P&L: ${total_pnl:.2f}")
        print(f"   BTC Position: {aggregated_positions['BTC']['size']:.4f} (${aggregated_positions['BTC']['value']:.2f})")
        print(f"   ETH Position: {aggregated_positions['ETH']['size']:.4f} (${aggregated_positions['ETH']['value']:.2f})")
        
        return portfolio_summary
    
    async def test_market_data(self):
        """Test market data fetching"""
        print("\n📊 Testing market data...")
        
        # Test with first vault's credentials
        if TEST_VAULTS:
            vault_config = TEST_VAULTS[0]
            market_data = await self._make_request('GET', '/market-data?symbols=BTC,ETH', vault_config)
            
            if market_data:
                print("✅ Market data fetched successfully")
                for symbol, data in market_data.items():
                    if symbol in ['BTC', 'ETH']:
                        price = data.get('markPrice', 0)
                        print(f"   {symbol}: ${price:.2f}")
            else:
                print("❌ Failed to fetch market data")

async def main():
    """Test multi-vault functionality"""
    print("🚀 Hyperliquid Multi-Vault Tester")
    print("=" * 50)
    
    async with HyperliquidVaultTester() as tester:
        # Test individual vault connections
        print("\n1. Testing individual vault connections...")
        for vault_config in TEST_VAULTS:
            await tester.test_vault_connection(vault_config)
        
        # Test aggregated portfolio
        print("\n2. Testing aggregated portfolio...")
        portfolio = await tester.get_aggregated_portfolio()
        
        # Test market data
        print("\n3. Testing market data...")
        await tester.test_market_data()
        
        # Save results to file
        with open('vault_test_results.json', 'w') as f:
            json.dump(portfolio, f, indent=2, default=str)
        print(f"\n💾 Results saved to vault_test_results.json")

if __name__ == "__main__":
    asyncio.run(main()) 