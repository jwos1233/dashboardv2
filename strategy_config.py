"""
Strategy Configuration
======================

Configuration for discretionary positions and strategy behavior
"""

# Tickers to IGNORE (discretionary positions - not managed by strategy)
# These positions will not be tracked, adjusted, or closed by the automated system
IGNORE_TICKERS = [
    'PLTR',  # Discretionary options position - managed manually
    # Add any other discretionary tickers here
]

# Contract types the strategy manages
# Only these types will be tracked and traded
MANAGED_CONTRACT_TYPES = ['STK', 'CFD']

# Contract types to ignore (options, futures, etc.)
IGNORED_CONTRACT_TYPES = ['OPT', 'FUT', 'FOP', 'WAR', 'IOPT']



