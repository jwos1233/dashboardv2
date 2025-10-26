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
    'Q1': 2.00,  # 200% leverage in Goldilocks regime
    'Q2': 0.00,  # Flat in Reflation regime
    'Q3': 1.00,  # 100% leverage in Stagflation regime
    'Q4': 0.00   # Flat in Deflation regime
}

# Risk management
MAX_POSITIONS = 5  # Maximum number of concurrent positions
POSITION_SIZE_PCT = 0.20  # 20% of account value per position
MAX_DRAWDOWN_PCT = 0.15  # 15% maximum drawdown before stopping

# Technical indicators
MOMENTUM_LOOKBACK_DAYS = 50  # 50-day momentum for quadrant calculation
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
MAX_POSITION_SIZE = 0.5  # Maximum 50% of capital per position
MIN_POSITION_SIZE = 0.1  # Minimum 10% of capital per position

# Risk Management
MAX_LEVERAGE = 3.0  # Maximum leverage allowed

# Position Sizing by Regime
REGIME_POSITION_SIZES = {
    'Q1': 2.0,  # 200% of capital per position (Goldilocks)
    'Q2': 0.0,  # 0% of capital per position (Reflation - flat)
    'Q3': 1.0,  # 100% of capital per position (Stagflation)
    'Q4': 0.0   # 0% of capital per position (Deflation - flat)
}

# Leverage by Regime
REGIME_LEVERAGE = {
    'Q1': 2.0,  # 2x leverage (Goldilocks)
    'Q2': 1.0,  # 1x leverage (Reflation - no leverage)
    'Q3': 1.0,  # 1x leverage (Stagflation)
    'Q4': 1.0   # 1x leverage (Deflation - no leverage)
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