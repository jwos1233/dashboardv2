"""
Hyperliquid Executor for Macro Quadrant Strategy
Handles order execution and position management
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
import aiohttp
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
import logging
from config import (
    HL_API_KEY, HL_SECRET_KEY, HL_BASE_URL, 
    TRADING_UNIVERSE, MAX_POSITION_SIZE, MIN_POSITION_SIZE,
    MAX_LEVERAGE, REGIME_POSITION_SIZES, REGIME_LEVERAGE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HyperliquidExecutor:
    def __init__(self):
        self.api_key = HL_API_KEY
        self.secret_key = HL_SECRET_KEY
        self.base_url = HL_BASE_URL
        self.session = None
        self.positions = {}
        self.orders = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, timestamp: str, data: str) -> str:
        """Generate HMAC signature for authentication"""
        message = timestamp + data
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to Hyperliquid API"""
        if not self.session:
            raise RuntimeError("Session not initialized")
            
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            'Content-Type': 'application/json',
            'X-HL-API-Key': self.api_key,
            'X-HL-Timestamp': timestamp
        }
        
        if data:
            data_str = json.dumps(data)
            headers['X-HL-Signature'] = self._generate_signature(timestamp, data_str)
            payload = data_str
        else:
            payload = None
            
        try:
            async with self.session.request(method, url, headers=headers, data=payload) as response:
                result = await response.json()
                if response.status != 200:
                    logger.error(f"API Error: {response.status} - {result}")
                    return None
                return result
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    async def get_account_info(self) -> Optional[dict]:
        """Get account information including balance and positions"""
        return await self._make_request('GET', '/account')
    
    async def get_positions(self) -> Dict[str, dict]:
        """Get current positions"""
        account_info = await self.get_account_info()
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
        
        self.positions = positions
        return positions
    
    async def get_market_data(self, symbols: List[str] = None) -> Dict[str, dict]:
        """Get market data for specified symbols"""
        if symbols is None:
            symbols = TRADING_UNIVERSE
            
        endpoint = f"/market-data?symbols={','.join(symbols)}"
        return await self._make_request('GET', endpoint)
    
    async def place_order(self, symbol: str, side: str, size: float, 
                         leverage: float = 1.0, order_type: str = 'market') -> Optional[dict]:
        """Place an order on Hyperliquid"""
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
        
        result = await self._make_request('POST', '/order', order_data)
        if result:
            logger.info(f"Order placed: {symbol} {side} {size} @ {leverage}x leverage")
            self.orders[result.get('orderId')] = order_data
        return result
    
    async def close_position(self, symbol: str) -> Optional[dict]:
        """Close a position by placing an opposite order"""
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return None
            
        position = self.positions[symbol]
        if position['size'] == 0:
            return None
            
        # Determine side based on current position
        side = 'sell' if position['size'] > 0 else 'buy'
        size = abs(position['size'])
        
        return await self.place_order(symbol, side, size, position['leverage'])
    
    async def adjust_position(self, symbol: str, target_size: float, 
                            regime: str, current_price: float) -> Optional[dict]:
        """Adjust position size based on regime and current market conditions"""
        if symbol not in TRADING_UNIVERSE:
            return None
            
        current_position = self.positions.get(symbol, {'size': 0, 'leverage': 1.0})
        current_size = current_position['size']
        
        # Get regime-specific parameters
        position_size_pct = REGIME_POSITION_SIZES.get(regime, 0.3)
        leverage = min(REGIME_LEVERAGE.get(regime, 1.0), MAX_LEVERAGE)
        
        # Calculate target position value
        account_info = await self.get_account_info()
        if not account_info:
            return None
            
        account_value = float(account_info.get('accountValue', 100000))
        target_position_value = account_value * position_size_pct
        
        # Calculate target size in contracts
        target_size_contracts = target_position_value / current_price
        
        # Apply leverage
        target_size_contracts *= leverage
        
        # Apply position size limits
        max_size = account_value * MAX_POSITION_SIZE / current_price * leverage
        min_size = account_value * MIN_POSITION_SIZE / current_price * leverage
        
        target_size_contracts = max(min_size, min(max_size, target_size_contracts))
        
        # Calculate size difference
        size_diff = target_size_contracts - current_size
        
        if abs(size_diff) < 0.01:  # Minimum size threshold
            logger.info(f"Position size difference too small for {symbol}")
            return None
            
        # Determine order side
        if size_diff > 0:
            side = 'buy'
        else:
            side = 'sell'
            size_diff = abs(size_diff)
        
        # Place the order
        result = await self.place_order(symbol, side, size_diff, leverage)
        
        if result:
            logger.info(f"Position adjusted for {symbol}: {side} {size_diff:.4f} @ {leverage}x leverage")
            
        return result
    
    async def get_performance_summary(self) -> dict:
        """Get performance summary including P&L and positions"""
        account_info = await self.get_account_info()
        if not account_info:
            return {}
            
        positions = await self.get_positions()
        
        total_pnl = 0
        position_summary = {}
        
        for symbol, position in positions.items():
            total_pnl += position['unrealized_pnl']
            position_summary[symbol] = {
                'size': position['size'],
                'entry_price': position['entry_price'],
                'current_price': position['mark_price'],
                'unrealized_pnl': position['unrealized_pnl'],
                'leverage': position['leverage']
            }
        
        return {
            'account_value': float(account_info.get('accountValue', 0)),
            'total_pnl': total_pnl,
            'positions': position_summary,
            'timestamp': datetime.now().isoformat()
        } 