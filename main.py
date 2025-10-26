"""
Macro Quadrant Trading Strategy - Main Execution Script
Combines quadrant analysis with Hyperliquid execution
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

from config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, UPDATE_INTERVAL_MINUTES,
    ENABLE_TELEGRAM_NOTIFICATIONS, ENABLE_EMA_FILTER
)
from quadrant_analyzer import QuadrantAnalyzer
from hyperliquid_executor import HyperliquidExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MacroQuadrantStrategy:
    def __init__(self):
        self.analyzer = QuadrantAnalyzer()
        self.executor = None
        self.last_regime = None
        self.last_update = None
        
    async def initialize(self):
        """Initialize the strategy components"""
        logger.info("🚀 Initializing Macro Quadrant Strategy")
        
        # Initialize executor
        self.executor = HyperliquidExecutor()
        await self.executor.__aenter__()
        
        # Test connection
        account_info = await self.executor.get_account_info()
        if account_info:
            logger.info(f"✅ Connected to Hyperliquid")
            logger.info(f"💰 Account Value: ${account_info.get('accountValue', 0):.2f}")
        else:
            logger.error("❌ Failed to connect to Hyperliquid")
            return False
            
        return True
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            await self.executor.__aexit__(None, None, None)
    
    async def send_telegram_notification(self, message: str):
        """Send notification via Telegram"""
        if not ENABLE_TELEGRAM_NOTIFICATIONS:
            return
            
        try:
            import requests
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Telegram notification sent")
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}")
    
    async def get_current_regime(self) -> Optional[Dict]:
        """Get current market regime"""
        try:
            regime_data = self.analyzer.get_current_regime()
            if regime_data:
                # Map the quadrant analyzer output to the expected format
                mapped_regime = {
                    'regime': regime_data['primary_quadrant'],
                    'strength': regime_data['regime_strength'],
                    'confidence': regime_data['confidence'],
                    'description': regime_data['description'],
                    'all_scores': regime_data['all_scores']
                }
                logger.info(f"📊 Current Regime: {mapped_regime['regime']}")
                logger.info(f"🎯 Regime Strength: {mapped_regime['strength']}")
                return mapped_regime
            else:
                logger.error("❌ Failed to get current regime")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting regime: {e}")
            return None
    
    async def execute_regime_strategy(self, regime_data: Dict):
        """Execute trading strategy based on regime"""
        regime = regime_data['regime']
        strength = regime_data['strength']
        
        logger.info(f"🎯 Executing strategy for {regime} regime (strength: {strength:.2f})")
        
        # Get current positions
        positions = await self.executor.get_positions()
        logger.info(f"📊 Current positions: {positions}")
        
        # Get market data for BTC and ETH
        market_data = await self.executor.get_market_data(['BTC', 'ETH'])
        if not market_data:
            logger.error("❌ Failed to get market data")
            return
        
        # Execute trades for each asset
        executed_trades = []
        
        for symbol in ['BTC', 'ETH']:
            if symbol not in market_data:
                logger.warning(f"⚠️ No market data for {symbol}")
                continue
                
            current_price = float(market_data[symbol].get('markPrice', 0))
            if current_price == 0:
                logger.warning(f"⚠️ Invalid price for {symbol}")
                continue
            
            # Adjust position based on regime
            result = await self.executor.adjust_position(
                symbol=symbol,
                target_size=0,  # Let the executor calculate based on regime
                regime=regime,
                current_price=current_price
            )
            
            if result:
                executed_trades.append({
                    'symbol': symbol,
                    'regime': regime,
                    'price': current_price,
                    'order': result
                })
                logger.info(f"✅ Position adjusted for {symbol}")
        
        # Send notification if trades were executed
        if executed_trades:
            message = f"🔄 <b>Strategy Update</b>\n"
            message += f"📊 Regime: {regime}\n"
            message += f"💪 Strength: {strength:.2f}\n"
            message += f"📈 Trades: {len(executed_trades)}\n"
            for trade in executed_trades:
                message += f"  • {trade['symbol']}: ${trade['price']:.2f}\n"
            
            await self.send_telegram_notification(message)
        
        return executed_trades
    
    async def get_performance_summary(self) -> Dict:
        """Get current performance summary"""
        return await self.executor.get_performance_summary()
    
    async def run_strategy_cycle(self):
        """Run one complete strategy cycle"""
        try:
            # Get current regime
            regime_data = await self.get_current_regime()
            if not regime_data:
                logger.error("❌ Could not get regime data")
                return
            
            current_regime = regime_data['regime']
            
            # Check if regime has changed
            if self.last_regime != current_regime:
                logger.info(f"🔄 Regime changed from {self.last_regime} to {current_regime}")
                self.last_regime = current_regime
                
                # Execute strategy for new regime
                await self.execute_regime_strategy(regime_data)
            
            # Update timestamp
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Error in strategy cycle: {e}")
    
    async def run_continuous(self):
        """Run the strategy continuously"""
        logger.info("🚀 Starting continuous strategy execution")
        
        if not await self.initialize():
            logger.error("❌ Failed to initialize strategy")
            return
        
        try:
            while True:
                await self.run_strategy_cycle()
                
                # Wait for next update
                logger.info(f"⏰ Waiting {UPDATE_INTERVAL_MINUTES} minutes until next update")
                await asyncio.sleep(UPDATE_INTERVAL_MINUTES * 60)
                
        except KeyboardInterrupt:
            logger.info("🛑 Strategy stopped by user")
        except Exception as e:
            logger.error(f"❌ Strategy error: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    strategy = MacroQuadrantStrategy()
    
    # Check if running in continuous mode or single execution
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        await strategy.run_continuous()
    else:
        # Single execution mode
        if not await strategy.initialize():
            return
        
        try:
            await strategy.run_strategy_cycle()
            
            # Print performance summary
            summary = await strategy.get_performance_summary()
            if summary:
                print(f"\n📊 Performance Summary:")
                print(f"💰 Account Value: ${summary['account_value']:.2f}")
                print(f"📈 Total P&L: ${summary['total_pnl']:.2f}")
                print(f"📊 Positions: {len(summary['positions'])}")
                
        finally:
            await strategy.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 