"""
Multi-Vault Hyperliquid Executor
Handles multiple vaults and aggregates their portfolio data
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
import aiohttp
import hmac
import hashlib
from datetime import datetime
import logging
from config import (
    TRADING_UNIVERSE, MAX_POSITION_SIZE, MIN_POSITION_SIZE,
    MAX_LEVERAGE, REGIME_POSITION_SIZES, REGIME_LEVERAGE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiVaultExecutor:
    def __init__(self, vault_configs: List[Dict]):
        """
        Initialize with list of vault configurations
        
        vault_configs format:
        [
            {
                'name': 'Vault 1',
                'api_key': 'your_api_key',
                'secret_key': 'your_secret_key', 
                'vault_address': '0x...',
                'weight': 1.0  # Optional weight for position allocation
            },
            ...
        ]
        """
        self.vault_configs = vault_configs
        self.session = None
        self.aggregated_positions = {}
        self.portfolio_summary = {}
        
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
            
        url = f"https://api.hyperliquid.xyz{endpoint}"
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
                    logger.error(f"API Error for {vault_config['name']}: {response.status} - {result}")
                    return None
                return result
        except Exception as e:
            logger.error(f"Request failed for {vault_config['name']}: {e}")
            return None
    
    async def get_vault_account_info(self, vault_config: dict) -> Optional[dict]:
        """Get account information for a specific vault"""
        return await self._make_request('GET', '/account', vault_config)
    
    async def get_vault_positions(self, vault_config: dict) -> Dict:
        """Get positions for a specific vault"""
        account_info = await self.get_vault_account_info(vault_config)
        if not account_info:
            return {}
            
        positions = {}
        for position in account_info.get('positions', []):
            symbol = position.get('symbol')
            if symbol in TRADING_UNIVERSE:
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
        logger.info("📊 Aggregating portfolio across all vaults...")
        
        total_account_value = 0
        total_pnl = 0
        aggregated_positions = {symbol: {'size': 0, 'value': 0} for symbol in TRADING_UNIVERSE}
        vault_summaries = []
        
        for vault_config in self.vault_configs:
            account_info = await self.get_vault_account_info(vault_config)
            
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
                for symbol in TRADING_UNIVERSE:
                    if symbol in positions:
                        pos = positions[symbol]
                        aggregated_positions[symbol]['size'] += pos['size']
                        aggregated_positions[symbol]['value'] += abs(pos['size']) * pos['mark_price']
                
                logger.info(f"   {vault_config['name']}: ${vault_value:.2f} (P&L: ${vault_pnl:.2f})")
            else:
                logger.warning(f"   {vault_config['name']}: ❌ Connection failed")
        
        self.portfolio_summary = {
            'total_account_value': total_account_value,
            'total_unrealized_pnl': total_pnl,
            'aggregated_positions': aggregated_positions,
            'vault_summaries': vault_summaries,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"📈 Total Portfolio: ${total_account_value:.2f} (P&L: ${total_pnl:.2f})")
        
        return self.portfolio_summary
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, dict]:
        """Get market data for specified symbols"""
        if symbols is None:
            symbols = TRADING_UNIVERSE
            
        # Use first vault for market data (should be same across all vaults)
        if self.vault_configs:
            vault_config = self.vault_configs[0]
            endpoint = f"/market-data?symbols={','.join(symbols)}"
            return await self._make_request('GET', endpoint, vault_config)
        else:
            logger.error("No vault configurations available")
            return {}
    
    async def place_order_on_vault(self, vault_config: dict, symbol: str, side: str, 
                                  size: float, leverage: float = 1.0, order_type: str = 'market') -> Optional[dict]:
        """Place an order on a specific vault"""
        if symbol not in TRADING_UNIVERSE:
            logger.warning(f"Symbol {symbol} not in trading universe")
            return None
            
        order_data = {
            'symbol': symbol,
            'side': side,
            'size': str(size),
            'leverage': str(leverage),
            'orderType': order_type
        }
        
        result = await self._make_request('POST', '/order', vault_config, order_data)
        if result:
            logger.info(f"Order placed on {vault_config['name']}: {symbol} {side} {size} @ {leverage}x leverage")
        return result
    
    async def close_position_on_vault(self, vault_config: dict, symbol: str) -> Optional[dict]:
        """Close a position on a specific vault"""
        positions = await self.get_vault_positions(vault_config)
        
        if symbol not in positions:
            logger.warning(f"No position to close for {symbol} on {vault_config['name']}")
            return None
            
        position = positions[symbol]
        if position['size'] == 0:
            return None
            
        # Determine side based on current position
        side = 'sell' if position['size'] > 0 else 'buy'
        size = abs(position['size'])
        
        return await self.place_order_on_vault(vault_config, symbol, side, size, position['leverage'])
    
    async def adjust_positions_for_regime(self, regime: str):
        """Adjust positions across all vaults based on regime"""
        logger.info(f"🎯 Adjusting positions for regime: {regime}")
        
        # Get current market data
        market_data = await self.get_market_data()
        if not market_data:
            logger.error("❌ Failed to get market data")
            return
        
        # Get current aggregated portfolio
        portfolio = await self.get_aggregated_portfolio()
        total_account_value = portfolio['total_account_value']
        
        if total_account_value == 0:
            logger.warning("❌ Total account value is zero")
            return
        
        # Get regime-specific parameters
        position_size_pct = REGIME_POSITION_SIZES.get(regime, 0.0)
        leverage = min(REGIME_LEVERAGE.get(regime, 1.0), MAX_LEVERAGE)
        
        logger.info(f"📊 Regime parameters: {position_size_pct*100:.0f}% position size, {leverage}x leverage")
        
        # Calculate target positions for each symbol
        target_positions = {}
        for symbol in TRADING_UNIVERSE:
            if symbol in market_data:
                current_price = float(market_data[symbol].get('markPrice', 0))
                if current_price > 0:
                    # Calculate target position value
                    target_position_value = total_account_value * position_size_pct
                    
                    # Calculate target size in contracts
                    target_size_contracts = target_position_value / current_price
                    
                    # Apply leverage
                    target_size_contracts *= leverage
                    
                    # Apply position size limits
                    max_size = total_account_value * MAX_POSITION_SIZE / current_price * leverage
                    min_size = total_account_value * MIN_POSITION_SIZE / current_price * leverage
                    
                    target_size_contracts = max(min_size, min(max_size, target_size_contracts))
                    
                    target_positions[symbol] = {
                        'target_size': target_size_contracts,
                        'current_price': current_price,
                        'leverage': leverage
                    }
        
        # Execute position adjustments across vaults
        executed_trades = []
        
        for vault_config in self.vault_configs:
            vault_weight = vault_config.get('weight', 1.0)
            vault_value = 0
            
            # Find vault value
            for vault_summary in portfolio['vault_summaries']:
                if vault_summary['name'] == vault_config['name']:
                    vault_value = vault_summary['account_value']
                    break
            
            if vault_value == 0:
                logger.warning(f"Skipping {vault_config['name']} - no account value")
                continue
            
            # Calculate vault's share of total portfolio
            vault_share = vault_value / total_account_value
            
            for symbol, target_data in target_positions.items():
                # Calculate this vault's target position
                vault_target_size = target_data['target_size'] * vault_share
                
                # Get current position on this vault
                vault_positions = await self.get_vault_positions(vault_config)
                current_size = vault_positions.get(symbol, {}).get('size', 0)
                
                # Calculate size difference
                size_diff = vault_target_size - current_size
                
                if abs(size_diff) < 0.01:  # Minimum size threshold
                    continue
                
                # Determine order side
                if size_diff > 0:
                    side = 'buy'
                else:
                    side = 'sell'
                    size_diff = abs(size_diff)
                
                # Place the order
                result = await self.place_order_on_vault(
                    vault_config, symbol, side, size_diff, target_data['leverage']
                )
                
                if result:
                    executed_trades.append({
                        'vault': vault_config['name'],
                        'symbol': symbol,
                        'side': side,
                        'size': size_diff,
                        'leverage': target_data['leverage'],
                        'price': target_data['current_price']
                    })
        
        if executed_trades:
            logger.info(f"✅ Executed {len(executed_trades)} trades across {len(self.vault_configs)} vaults")
            for trade in executed_trades:
                logger.info(f"   {trade['vault']}: {trade['symbol']} {trade['side']} {trade['size']:.4f}")
        else:
            logger.info("ℹ️ No position adjustments needed")
        
        return executed_trades
    
    async def get_performance_summary(self) -> dict:
        """Get aggregated performance summary"""
        return await self.get_aggregated_portfolio()

# Test function
async def test_multi_vault():
    """Test the multi-vault executor"""
    
    # Example vault configurations
    test_vaults = [
        {
            'name': 'Vault 1',
            'api_key': 'your_api_key_1',
            'secret_key': 'your_secret_key_1',
            'vault_address': '0x1234567890123456789012345678901234567890',
            'weight': 1.0
        },
        {
            'name': 'Vault 2',
            'api_key': 'your_api_key_2', 
            'secret_key': 'your_secret_key_2',
            'vault_address': '0x2345678901234567890123456789012345678901',
            'weight': 1.0
        },
        {
            'name': 'Vault 3',
            'api_key': 'your_api_key_3',
            'secret_key': 'your_secret_key_3', 
            'vault_address': '0x3456789012345678901234567890123456789012',
            'weight': 1.0
        }
    ]
    
    async with MultiVaultExecutor(test_vaults) as executor:
        # Test portfolio aggregation
        portfolio = await executor.get_aggregated_portfolio()
        print(f"Total Portfolio Value: ${portfolio['total_account_value']:.2f}")
        
        # Test market data
        market_data = await executor.get_market_data()
        print(f"Market Data: {market_data}")
        
        # Test regime adjustment (example)
        # await executor.adjust_positions_for_regime('Q1')

if __name__ == "__main__":
    asyncio.run(test_multi_vault()) 