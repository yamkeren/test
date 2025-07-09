# Interactive Brokers API Configuration Sample
# Copy this file to ibkr_config.py and update with your settings

# IB Gateway/TWS Connection Settings
IBKR_HOST = '127.0.0.1'  # IB Gateway/TWS host
IBKR_PORT = 7497  # 7497 for TWS paper trading, 7496 for TWS live, 4002 for IB Gateway paper, 4001 for IB Gateway live
IBKR_CLIENT_ID = 1  # Unique client ID

# Trading Settings
PAPER_TRADING = True  # Set to False for live trading (be careful!)

# Risk Management
MAX_POSITION_SIZE = 1000  # Maximum position size in dollars
MAX_DAILY_LOSS = 500  # Maximum daily loss in dollars
MAX_TRADES_PER_DAY = 10  # Maximum number of trades per day

# Logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'ibkr_trading.log'  # Log file path