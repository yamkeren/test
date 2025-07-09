"""
Interactive Brokers API Integration Module
This module provides functionality to connect to Interactive Brokers API,
fetch real-time market data, execute trades, and manage portfolios.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from datetime import datetime, timedelta
from ib_insync import IB, Stock, MarketOrder, LimitOrder, util
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeOrder:
    """Represents a trade order"""
    symbol: str
    action: str  # 'BUY' or 'SELL'
    quantity: int
    order_type: str  # 'MARKET' or 'LIMIT'
    price: Optional[float] = None
    order_id: Optional[str] = None
    status: str = 'PENDING'
    filled_quantity: int = 0
    avg_fill_price: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class Position:
    """Represents a portfolio position"""
    symbol: str
    quantity: int
    avg_cost: float
    market_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float = 0.0


@dataclass
class Portfolio:
    """Represents the complete portfolio"""
    positions: List[Position]
    cash: float
    total_value: float
    unrealized_pnl: float
    realized_pnl: float
    

class IBKRAPIClient:
    """
    Interactive Brokers API client for real-time data and trading operations.
    
    This class provides methods to:
    - Connect to Interactive Brokers API
    - Fetch real-time market data
    - Execute trades
    - Manage portfolio
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 1):
        """
        Initialize the IBKR API client.
        
        Args:
            host: IB Gateway/TWS host address
            port: IB Gateway/TWS port (7497 for TWS paper trading, 7496 for TWS live)
            client_id: Unique client identifier
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        self.contracts = {}  # Cache for contract objects
        self.market_data = {}  # Cache for market data
        self.orders = {}  # Track orders
        
    async def connect(self) -> bool:
        """
        Connect to Interactive Brokers API.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            await self.ib.connectAsync(self.host, self.port, self.client_id)
            self.connected = True
            logger.info(f"Connected to IB Gateway at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IB Gateway: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers API."""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IB Gateway")
    
    async def get_contract(self, symbol: str, exchange: str = 'SMART', currency: str = 'USD') -> Optional[Stock]:
        """
        Get contract object for a stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            exchange: Exchange (default: 'SMART')
            currency: Currency (default: 'USD')
            
        Returns:
            Stock contract object or None if not found
        """
        if not self.connected:
            logger.error("Not connected to IB Gateway")
            return None
            
        # Check cache first
        cache_key = f"{symbol}_{exchange}_{currency}"
        if cache_key in self.contracts:
            return self.contracts[cache_key]
        
        try:
            contract = Stock(symbol, exchange, currency)
            qualified_contracts = await self.ib.qualifyContractsAsync(contract)
            
            if qualified_contracts:
                self.contracts[cache_key] = qualified_contracts[0]
                return qualified_contracts[0]
            else:
                logger.warning(f"Contract not found for symbol: {symbol}")
                return None
        except Exception as e:
            logger.error(f"Error getting contract for {symbol}: {e}")
            return None
    
    async def get_real_time_data(self, symbols: List[str], duration: str = '1 D', 
                                bar_size: str = '5 mins') -> Dict[str, pd.DataFrame]:
        """
        Fetch real-time historical data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            duration: Duration (e.g., '1 D', '1 W', '1 M')
            bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour')
            
        Returns:
            Dictionary mapping symbols to DataFrames with OHLCV data
        """
        if not self.connected:
            logger.error("Not connected to IB Gateway")
            return {}
        
        data = {}
        
        for symbol in symbols:
            try:
                contract = await self.get_contract(symbol)
                if contract:
                    # Get historical data
                    bars = await self.ib.reqHistoricalDataAsync(
                        contract,
                        endDateTime='',
                        durationStr=duration,
                        barSizeSetting=bar_size,
                        whatToShow='TRADES',
                        useRTH=True,
                        formatDate=1
                    )
                    
                    if bars:
                        # Convert to DataFrame
                        df = util.df(bars)
                        df.set_index('date', inplace=True)
                        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount']
                        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # Keep only OHLCV
                        data[symbol] = df
                        logger.info(f"Fetched {len(df)} bars for {symbol}")
                    else:
                        logger.warning(f"No data received for {symbol}")
                        
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                continue
        
        return data
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get real-time market data (current prices) for symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to market data (price, bid, ask, volume)
        """
        if not self.connected:
            logger.error("Not connected to IB Gateway")
            return {}
        
        market_data = {}
        
        for symbol in symbols:
            try:
                contract = await self.get_contract(symbol)
                if contract:
                    # Request market data
                    self.ib.reqMktData(contract, '', False, False)
                    
                    # Wait for data
                    await asyncio.sleep(1)
                    
                    # Get ticker data
                    ticker = self.ib.ticker(contract)
                    
                    market_data[symbol] = {
                        'price': ticker.marketPrice() if ticker.marketPrice() else ticker.close,
                        'bid': ticker.bid,
                        'ask': ticker.ask,
                        'bid_size': ticker.bidSize,
                        'ask_size': ticker.askSize,
                        'volume': ticker.volume,
                        'high': ticker.high,
                        'low': ticker.low,
                        'close': ticker.close,
                        'timestamp': datetime.now()
                    }
                    
            except Exception as e:
                logger.error(f"Error getting market data for {symbol}: {e}")
                continue
        
        return market_data
    
    async def place_order(self, symbol: str, action: str, quantity: int, 
                         order_type: str = 'MARKET', price: Optional[float] = None) -> TradeOrder:
        """
        Place a trade order.
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MARKET' or 'LIMIT'
            price: Limit price (required for LIMIT orders)
            
        Returns:
            TradeOrder object with order details
        """
        if not self.connected:
            logger.error("Not connected to IB Gateway")
            return TradeOrder(symbol, action, quantity, order_type, price, status='FAILED')
        
        try:
            contract = await self.get_contract(symbol)
            if not contract:
                return TradeOrder(symbol, action, quantity, order_type, price, status='FAILED')
            
            # Create order
            if order_type.upper() == 'MARKET':
                order = MarketOrder(action, quantity)
            elif order_type.upper() == 'LIMIT':
                if price is None:
                    logger.error("Price required for LIMIT order")
                    return TradeOrder(symbol, action, quantity, order_type, price, status='FAILED')
                order = LimitOrder(action, quantity, price)
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return TradeOrder(symbol, action, quantity, order_type, price, status='FAILED')
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            # Create trade order object
            trade_order = TradeOrder(
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=order_type,
                price=price,
                order_id=str(trade.order.orderId),
                status='SUBMITTED',
                timestamp=datetime.now()
            )
            
            # Store order for tracking
            self.orders[trade_order.order_id] = trade_order
            
            logger.info(f"Order placed: {action} {quantity} {symbol} at {order_type}")
            return trade_order
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return TradeOrder(symbol, action, quantity, order_type, price, status='FAILED')
    
    async def get_portfolio(self) -> Portfolio:
        """
        Get current portfolio information.
        
        Returns:
            Portfolio object with positions and account information
        """
        if not self.connected:
            logger.error("Not connected to IB Gateway")
            return Portfolio([], 0.0, 0.0, 0.0, 0.0)
        
        try:
            # Get account values
            account_values = self.ib.accountValues()
            cash = 0.0
            total_value = 0.0
            unrealized_pnl = 0.0
            realized_pnl = 0.0
            
            for value in account_values:
                if value.tag == 'CashBalance' and value.currency == 'USD':
                    cash = float(value.value)
                elif value.tag == 'NetLiquidation' and value.currency == 'USD':
                    total_value = float(value.value)
                elif value.tag == 'UnrealizedPnL' and value.currency == 'USD':
                    unrealized_pnl = float(value.value)
                elif value.tag == 'RealizedPnL' and value.currency == 'USD':
                    realized_pnl = float(value.value)
            
            # Get positions
            positions = []
            portfolio_items = self.ib.portfolio()
            
            for item in portfolio_items:
                if hasattr(item.contract, 'symbol'):
                    position = Position(
                        symbol=item.contract.symbol,
                        quantity=int(item.position),
                        avg_cost=float(item.averageCost),
                        market_price=float(item.marketPrice),
                        market_value=float(item.marketValue),
                        unrealized_pnl=float(item.unrealizedPNL),
                        realized_pnl=float(item.realizedPNL)
                    )
                    positions.append(position)
            
            return Portfolio(
                positions=positions,
                cash=cash,
                total_value=total_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl
            )
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return Portfolio([], 0.0, 0.0, 0.0, 0.0)
    
    async def get_order_status(self, order_id: str) -> Optional[TradeOrder]:
        """
        Get the status of a placed order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Updated TradeOrder object or None if not found
        """
        if not self.connected or order_id not in self.orders:
            return None
        
        try:
            # Get all trades and find the matching one
            trades = self.ib.trades()
            for trade in trades:
                if str(trade.order.orderId) == order_id:
                    order = self.orders[order_id]
                    order.status = trade.orderStatus.status
                    order.filled_quantity = trade.orderStatus.filled
                    if trade.orderStatus.avgFillPrice:
                        order.avg_fill_price = trade.orderStatus.avgFillPrice
                    return order
            
            return self.orders[order_id]
            
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        
        Returns:
            bool: True if market is open, False otherwise
        """
        # This is a simplified check - in practice, you'd want to check
        # market holidays and trading hours for specific exchanges
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Check if it's a weekday (Monday-Friday)
        if weekday >= 5:  # Saturday or Sunday
            return False
        
        # Check if it's within trading hours (9:30 AM - 4:00 PM ET)
        # This is a simplified check - real implementation should handle timezones
        current_time = now.time()
        market_open = datetime.strptime('09:30', '%H:%M').time()
        market_close = datetime.strptime('16:00', '%H:%M').time()
        
        return market_open <= current_time <= market_close


class IBKRConfigManager:
    """
    Configuration manager for IBKR API credentials and settings.
    Handles secure storage and retrieval of API configuration.
    """
    
    def __init__(self, config_file: str = 'ibkr_config.py'):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables."""
        config = {}
        
        # Try to load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_content = f.read()
                exec(config_content, config)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        # Load from environment variables (override file config)
        config.update({
            'IBKR_HOST': os.getenv('IBKR_HOST', config.get('IBKR_HOST', '127.0.0.1')),
            'IBKR_PORT': int(os.getenv('IBKR_PORT', config.get('IBKR_PORT', 7497))),
            'IBKR_CLIENT_ID': int(os.getenv('IBKR_CLIENT_ID', config.get('IBKR_CLIENT_ID', 1))),
            'PAPER_TRADING': os.getenv('PAPER_TRADING', config.get('PAPER_TRADING', True)),
        })
        
        return config
    
    def get_connection_params(self) -> Tuple[str, int, int]:
        """
        Get connection parameters for IBKR API.
        
        Returns:
            Tuple of (host, port, client_id)
        """
        return (
            self.config['IBKR_HOST'],
            self.config['IBKR_PORT'],
            self.config['IBKR_CLIENT_ID']
        )
    
    def is_paper_trading(self) -> bool:
        """Check if paper trading is enabled."""
        return bool(self.config.get('PAPER_TRADING', True))
    
    def create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = '''# Interactive Brokers API Configuration
# Copy this file and update with your settings

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
'''
        
        with open('ibkr_config_sample.py', 'w') as f:
            f.write(sample_config)
        
        logger.info("Sample configuration file created: ibkr_config_sample.py")
        logger.info("Copy this file to ibkr_config.py and update with your settings")