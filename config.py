"""
Configuration for Macro Quadrant Trading Strategy
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === HYPERLIQUID CONFIGURATION ===
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "0x04793e9c32fb5def7a646610fd7a4bbb2c769b3b110b8049ef926e8815082d30")
VAULT_ADDRESS = os.getenv("VAULT_ADDRESS", "0x8bc7d5bf1afe96613e6ff67ade9fcf7d9223165e")

# Multi-Vault Configuration
VAULT_CONFIGS = [
    {
        'name': 'Vault 1',
        'api_key': os.getenv("HL_API_KEY_1", "your_api_key_1"),
        'secret_key': os.getenv("HL_SECRET_KEY_1", "your_secret_key_1"),
        'vault_address': os.getenv("VAULT_ADDRESS_1", "0x1234567890123456789012345678901234567890"),
        'weight': 1.0
    },
    {
        'name': 'Vault 2',
        'api_key': os.getenv("HL_API_KEY_2", "your_api_key_2"),
        'secret_key': os.getenv("HL_SECRET_KEY_2", "your_secret_key_2"),
        'vault_address': os.getenv("VAULT_ADDRESS_2", "0x2345678901234567890123456789012345678901"),
        'weight': 1.0
    },
    {
        'name': 'Vault 3',
        'api_key': os.getenv("HL_API_KEY_3", "your_api_key_3"),
        'secret_key': os.getenv("HL_SECRET_KEY_3", "your_secret_key_3"),
        'vault_address': os.getenv("VAULT_ADDRESS_3", "0x3456789012345678901234567890123456789012"),
        'weight': 1.0
    }
]

# === STRATEGY CONFIGURATION ===
# Position sizing rules
POSITION_RULES = {
    'Q1': 0.333,  # 33.3% of capital (1/3 of previous 100%)
    'Q2': 0.167,  # 16.7% of capital (1/3 of previous 50%)
    'Q3': 0.167,  # 16.7% of capital (1/3 of previous 50%)
    'Q4': 0.00   # Flat in Deflation regime
}

# Risk management
MAX_POSITIONS = 10  # Maximum number of concurrent positions
POSITION_SIZE_PCT = 0.067  # 6.7% of account value per position (1/3 of previous 20%)
MAX_DRAWDOWN_PCT = 0.15  # 15% maximum drawdown before stopping

# Technical indicators
MOMENTUM_LOOKBACK_DAYS = 20  # 20-day momentum for quadrant calculation
EMA_PERIOD = 50  # 50-day EMA filter
MIN_EMA_FILTER = True  # Whether to use EMA filter

# === ASSET CONFIGURATION ===
# Core assets for quadrant analysis
CORE_ASSETS = {
    # Q1 Assets (Growth ↑, Inflation ↓)
    'QQQ': 'NASDAQ 100 (Growth)',
    'VUG': 'Vanguard Growth ETF', 
    'IWM': 'Russell 2000 (Small Caps)',
    'BTC-USD': 'Bitcoin (BTC)',
    
    # Q2 Assets (Growth ↑, Inflation ↑)
    'XLE': 'Energy Sector ETF',
    'DBC': 'Broad Commodities ETF',
    
    # Q3 Assets (Growth ↓, Inflation ↑)
    'GLD': 'Gold ETF',
    'LIT': 'Lithium & Battery Tech ETF',
    
    # Q4 Assets (Growth ↓, Inflation ↓)
    'TLT': '20+ Year Treasury Bonds',
    'XLU': 'Utilities Sector ETF',
    'VIXY': 'Short-Term VIX Futures ETF',
}

# Trading assets on Hyperliquid
TRADING_ASSETS = {
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum', 
    'SOL': 'Solana',
    'BNB': 'Binance Coin',
    'XRP': 'Ripple',
    'ADA': 'Cardano',
    'AVAX': 'Avalanche',
    'DOGE': 'Dogecoin',
    'DOT': 'Polkadot',
    'LINK': 'Chainlink',
    'MATIC': 'Polygon',
    'SHIB': 'Shiba Inu',
    'UNI': 'Uniswap',
    'LTC': 'Litecoin',
    'ATOM': 'Cosmos',
    'XLM': 'Stellar',
    'ALGO': 'Algorand',
    'NEAR': 'NEAR Protocol',
    'AAVE': 'Aave',
    'TRX': 'TRON'
}

# Trading Configuration
TRADING_UNIVERSE = ['BTC', 'ETH']  # Only BTC and ETH
MAX_POSITION_SIZE = 0.167  # Maximum 16.7% of capital per position (1/3 of previous 50%)
MIN_POSITION_SIZE = 0.033  # Minimum 3.3% of capital per position (1/3 of previous 10%)

# Risk Management
MAX_LEVERAGE = 3.0  # Maximum leverage allowed

# Position Sizing by Regime
REGIME_POSITION_SIZES = {
    'Q1': 0.333,  # 33.3% of capital per position (1/3 of previous 100%)
    'Q2': 0.167,  # 16.7% of capital per position (1/3 of previous 50%)
    'Q3': 0.167,  # 16.7% of capital per position (1/3 of previous 50%)
    'Q4': 0.0   # 0% of capital per position (Deflation - flat)
}

# Leverage by Regime
REGIME_LEVERAGE = {
    'Q1': 0.333,  # 33.3% leverage (1/3 of previous 100%)
    'Q2': 0.167,  # 16.7% leverage (1/3 of previous 50%)
    'Q3': 0.167,  # 16.7% leverage (1/3 of previous 50%)
    'Q4': 0.167   # 16.7% leverage (1/3 of previous 50%)
}

# === NOTIFICATION CONFIGURATION ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7206335521:AAGQeuhik1SrN_qMakb9bxkI1iAJmg8A3Wo")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7119645510")

# === QUADRANT DESCRIPTIONS ===
QUADRANT_DESCRIPTIONS = {
    'Q1': 'Growth ↑, Inflation ↓ (Goldilocks)',
    'Q2': 'Growth ↑, Inflation ↑ (Reflation)', 
    'Q3': 'Growth ↓, Inflation ↑ (Stagflation)',
    'Q4': 'Growth ↓, Inflation ↓ (Deflation)'
}

# === EXECUTION SETTINGS ===
EXECUTION_INTERVAL_MINUTES = 60  # Check for signals every hour
RETRY_ATTEMPTS = 3  # Number of retry attempts for failed orders
ORDER_TIMEOUT_SECONDS = 30  # Timeout for order execution

# === LOGGING ===
LOG_LEVEL = "INFO"
LOG_FILE = "macro_quadrant_strategy.log"

# === QUADRANT ALLOCATIONS (FOR DASHBOARD) ===
# Portfolio Allocations per Quadrant - Crypto Asset Deployment Framework
QUAD_ALLOCATIONS = {
    'Q1': {
        # BTC Spot
        'IBIT': 0.20,              # BTC Spot ETF
        
        # ETH Spot
        'ETHA': 0.15,              # ETH Spot ETF
        
        # BTC Treasury Companies (4 assets)
        'MSTR': 0.10,              # BTC Treasury Company
        'CEP': 0.08,               # BTC Treasury Company
        'CEPO': 0.07,              # BTC Treasury Company
        'STRIVE': 0.05,            # BTC Treasury Company
        
        # ETH Treasury Companies (3 assets)
        'SBET': 0.05,              # ETH Treasury Company
        'BMNR': 0.05,              # ETH Treasury Company
        'ETHZ': 0.05,              # ETH Treasury Company
        
        # Pure Play Miners (2 assets)
        'MARA': 0.06,              # Pure Play Miner
        'CIFR': 0.04,              # Pure Play Miner
        
        # Diversified Miners (7 assets)
        'IREN': 0.03,              # Diversified Miner
        'CORZ': 0.03,              # Diversified Miner
        'HUT': 0.02,               # Diversified Miner
        'BTDR': 0.02,              # Diversified Miner
        'BTBT': 0.02,              # Diversified Miner
        'WULF': 0.02,              # Diversified Miner
        'HIVE': 0.02,              # Diversified Miner
        
        # Altcoin Digital Asset Treasuries (4 assets)
        'ASST': 0.015,             # Altcoin Treasury
        'UPXI': 0.015,             # Altcoin Treasury
        'AVX': 0.01,               # Altcoin Treasury
        'DFDV': 0.01,              # Altcoin Treasury
        
        # Infrastructure/Exchanges (6 assets)
        'COIN': 0.03,              # Infrastructure/Exchange
        'GLXY': 0.02,              # Infrastructure/Exchange
        'CRCL': 0.02,              # Infrastructure/Exchange
        'BLSH': 0.015,             # Infrastructure/Exchange
        'CAN': 0.015,              # Infrastructure/Exchange
        'SQ': 0.02,                # Infrastructure/Exchange
    },
    'Q2': {
        # BTC Spot
        'IBIT': 0.30,              # BTC Spot ETF
        
        # BTC Treasury Companies (4 assets)
        'MSTR': 0.15,              # BTC Treasury Company
        'CEP': 0.10,               # BTC Treasury Company
        'CEPO': 0.08,              # BTC Treasury Company
        'STRIVE': 0.07,            # BTC Treasury Company
        
        # Pure Play Miners (2 assets)
        'MARA': 0.10,              # Pure Play Miner
        'CIFR': 0.08,              # Pure Play Miner
        
        # Diversified Miners (7 assets)
        'IREN': 0.04,              # Diversified Miner
        'CORZ': 0.03,               # Diversified Miner
        'HUT': 0.02,               # Diversified Miner
        'BTDR': 0.015,             # Diversified Miner
        'BTBT': 0.015,             # Diversified Miner
        'WULF': 0.01,              # Diversified Miner
        'HIVE': 0.01,              # Diversified Miner
        
        # Infrastructure/Exchanges (6 assets)
        'COIN': 0.03,              # Infrastructure/Exchange
        'GLXY': 0.02,              # Infrastructure/Exchange
        'CRCL': 0.015,             # Infrastructure/Exchange
        'BLSH': 0.01,              # Infrastructure/Exchange
        'CAN': 0.01,               # Infrastructure/Exchange
        'SQ': 0.015,               # Infrastructure/Exchange
    },
    'Q3': {
        # BTC Spot
        'IBIT': 0.50,              # BTC Spot ETF (Core defensive position)
        
        # Diversified Miners (7 assets) - Only low-cost, defensive miners
        'IREN': 0.10,              # Diversified Miner
        'CORZ': 0.08,              # Diversified Miner
        'HUT': 0.07,               # Diversified Miner
        'BTDR': 0.06,              # Diversified Miner
        'BTBT': 0.05,              # Diversified Miner
        'WULF': 0.04,              # Diversified Miner
        'HIVE': 0.10,              # Diversified Miner
        # Note: High cash allocation (remaining ~50%) - no ticker for cash
    },
    'Q4': {
        # FLAT - NO DEPLOYMENT
        # 100% cash (or stablecoins if yield available)
        # No assets allocated in deflationary liquidation regime
    }
}

# Quadrant indicator assets (for scoring)
QUAD_INDICATORS = {
    'Q1': ['QQQ', 'VUG', 'IWM', 'BTC-USD'],
    'Q2': ['XLE', 'DBC', 'GCC', 'LIT'],
    'Q3': ['GLD', 'DBC', 'DBA', 'REMX', 'URA', 'LIT'],
    'Q4': ['TLT', 'XLU', 'VIXY']
} 