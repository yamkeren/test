"""
Interactive Brokers API Client for Trading Framework

This module provides integration with Interactive Brokers API for:
- Real-time market data
- Trade execution
- Portfolio management
- Account information
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ib_insync import IB, Stock, Contract, MarketOrder, LimitOrder, util
from ib_insync.objects import Position, PortfolioItem, AccountValue
import nest_asyncio

# Enable nested event loops for Jupyter/script compatibility
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IBKRConfig:
    """Configuration for IBKR connection"""
    host: str = '127.0.0.1'
    port: int = 7497  # TWS paper trading port (7496 for live)
    client_id: int = 1
    timeout: int = 30
    paper_trading: bool = True  # Safety default


@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    order_id: Optional[int]
    filled_qty: float
    avg_price: float
    commission: float
    error_message: Optional[str]
    timestamp: datetime


@dataclass
class PortfolioPosition:
    """Portfolio position information"""
    symbol: str
    position: float
    market_price: float
    market_value: float
    avg_cost: float
    unrealized_pnl: float
    realized_pnl: float


class IBKRClient:
    """Interactive Brokers API client for trading operations"""
    
    def __init__(self, config: IBKRConfig = None):
        """Initialize IBKR client
        
        Args:
            config: IBKR configuration settings
        """
        self.config = config or IBKRConfig()
        self.ib = IB()
        self.connected = False
        self.contracts = {}  # Cache for contracts
        self.market_data = {}  # Cache for market data
        
    async def connect(self) -> bool:
        """Connect to Interactive Brokers
        
        Returns:
            bool: True if connected successfully
        """
        try:
            await self.ib.connectAsync(
                host=self.config.host,
                port=self.config.port,
                clientId=self.config.client_id,
                timeout=self.config.timeout
            )
            self.connected = True
            logger.info(f"Connected to IBKR at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Interactive Brokers"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.connected and self.ib.isConnected()
    
    async def get_contract(self, symbol: str, exchange: str = 'SMART', 
                          currency: str = 'USD') -> Optional[Contract]:
        """Get contract for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Contract object or None if not found
        """
        contract_key = f"{symbol}_{exchange}_{currency}"
        
        if contract_key in self.contracts:
            return self.contracts[contract_key]
        
        try:
            contract = Stock(symbol, exchange, currency)
            qualified_contracts = await self.ib.qualifyContractsAsync(contract)
            
            if qualified_contracts:
                self.contracts[contract_key] = qualified_contracts[0]
                return qualified_contracts[0]
            else:
                logger.warning(f"No contract found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting contract for {symbol}: {e}")
            return None
    
    async def get_market_data(self, symbol: str, 
                            exchange: str = 'SMART') -> Optional[Dict[str, Any]]:
        """Get real-time market data for a symbol
        
        Args:
            symbol: Stock symbol
            exchange: Exchange
            
        Returns:
            Dictionary with market data or None
        """
        contract = await self.get_contract(symbol, exchange)
        if not contract:
            return None
        
        try:
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            await self.ib.sleep(1)  # Wait for data
            
            if ticker.last != ticker.last:  # Check for NaN
                # If no last price, try to get from bid/ask
                price = (ticker.bid + ticker.ask) / 2 if ticker.bid and ticker.ask else None
            else:
                price = ticker.last
            
            market_data = {
                'symbol': symbol,
                'price': price,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'last': ticker.last,
                'volume': ticker.volume,
                'timestamp': datetime.now()
            }
            
            self.market_data[symbol] = market_data
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    async def get_historical_data(self, symbol: str, duration: str = '1 D',
                                 bar_size: str = '5 mins',
                                 exchange: str = 'SMART') -> Optional[pd.DataFrame]:
        """Get historical data for a symbol
        
        Args:
            symbol: Stock symbol
            duration: Duration (e.g., '1 D', '1 W', '1 M')
            bar_size: Bar size (e.g., '1 min', '5 mins', '1 hour')
            exchange: Exchange
            
        Returns:
            DataFrame with OHLCV data or None
        """
        contract = await self.get_contract(symbol, exchange)
        if not contract:
            return None
        
        try:
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
                df = util.df(bars)
                df.set_index('date', inplace=True)
                df.rename(columns={
                    'open': 'Open',
                    'high': 'High', 
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                }, inplace=True)
                return df
            else:
                logger.warning(f"No historical data received for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    async def place_market_order(self, symbol: str, quantity: int,
                               action: str = 'BUY',
                               exchange: str = 'SMART') -> TradeResult:
        """Place a market order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (positive for buy, negative for sell)
            action: 'BUY' or 'SELL'
            exchange: Exchange
            
        Returns:
            TradeResult object
        """
        contract = await self.get_contract(symbol, exchange)
        if not contract:
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message=f"Could not find contract for {symbol}",
                timestamp=datetime.now()
            )
        
        try:
            order = MarketOrder(action, abs(quantity))
            trade = self.ib.placeOrder(contract, order)
            
            # Wait for order to be filled or timeout
            timeout = 30  # seconds
            start_time = datetime.now()
            
            while not trade.isDone() and (datetime.now() - start_time).seconds < timeout:
                await self.ib.sleep(0.1)
            
            if trade.isDone():
                fill = trade.fills[0] if trade.fills else None
                return TradeResult(
                    success=True,
                    order_id=trade.order.orderId,
                    filled_qty=fill.execution.cumQty if fill else 0,
                    avg_price=fill.execution.avgPrice if fill else 0,
                    commission=fill.commissionReport.commission if fill and fill.commissionReport else 0,
                    error_message=None,
                    timestamp=datetime.now()
                )
            else:
                # Order not filled within timeout
                self.ib.cancelOrder(order)
                return TradeResult(
                    success=False,
                    order_id=trade.order.orderId,
                    filled_qty=0,
                    avg_price=0,
                    commission=0,
                    error_message="Order timeout",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Error placing market order for {symbol}: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def place_limit_order(self, symbol: str, quantity: int, price: float,
                              action: str = 'BUY',
                              exchange: str = 'SMART') -> TradeResult:
        """Place a limit order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Limit price
            action: 'BUY' or 'SELL'
            exchange: Exchange
            
        Returns:
            TradeResult object
        """
        contract = await self.get_contract(symbol, exchange)
        if not contract:
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message=f"Could not find contract for {symbol}",
                timestamp=datetime.now()
            )
        
        try:
            order = LimitOrder(action, abs(quantity), price)
            trade = self.ib.placeOrder(contract, order)
            
            # For limit orders, we return immediately with order info
            return TradeResult(
                success=True,
                order_id=trade.order.orderId,
                filled_qty=0,  # Not filled yet
                avg_price=price,
                commission=0,
                error_message=None,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error placing limit order for {symbol}: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    async def get_portfolio(self) -> List[PortfolioPosition]:
        """Get current portfolio positions
        
        Returns:
            List of PortfolioPosition objects
        """
        if not self.is_connected():
            return []
        
        try:
            portfolio_items = self.ib.portfolio()
            positions = []
            
            for item in portfolio_items:
                position = PortfolioPosition(
                    symbol=item.contract.symbol,
                    position=item.position,
                    market_price=item.marketPrice,
                    market_value=item.marketValue,
                    avg_cost=item.averageCost,
                    unrealized_pnl=item.unrealizedPNL,
                    realized_pnl=item.realizedPNL
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return []
    
    async def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary information
        
        Returns:
            Dictionary with account information
        """
        if not self.is_connected():
            return {}
        
        try:
            account_values = self.ib.accountValues()
            summary = {}
            
            # Key metrics we want to track
            key_metrics = [
                'NetLiquidation',
                'TotalCashValue',
                'AvailableFunds',
                'BuyingPower',
                'UnrealizedPnL',
                'RealizedPnL'
            ]
            
            for av in account_values:
                if av.tag in key_metrics:
                    summary[av.tag] = float(av.value) if av.value else 0.0
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {}
    
    async def get_positions(self) -> List[Position]:
        """Get current positions
        
        Returns:
            List of Position objects
        """
        if not self.is_connected():
            return []
        
        try:
            return self.ib.positions()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Synchronous wrapper functions for easier integration
class IBKRClientSync:
    """Synchronous wrapper for IBKRClient"""
    
    def __init__(self, config: IBKRConfig = None):
        self.client = IBKRClient(config)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def connect(self) -> bool:
        """Connect to IBKR"""
        return self.loop.run_until_complete(self.client.connect())
    
    def disconnect(self):
        """Disconnect from IBKR"""
        self.client.disconnect()
        self.loop.close()
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.client.is_connected()
    
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market data synchronously"""
        return self.loop.run_until_complete(self.client.get_market_data(symbol))
    
    def get_historical_data(self, symbol: str, duration: str = '1 D',
                           bar_size: str = '5 mins') -> Optional[pd.DataFrame]:
        """Get historical data synchronously"""
        return self.loop.run_until_complete(
            self.client.get_historical_data(symbol, duration, bar_size)
        )
    
    def place_market_order(self, symbol: str, quantity: int,
                          action: str = 'BUY') -> TradeResult:
        """Place market order synchronously"""
        return self.loop.run_until_complete(
            self.client.place_market_order(symbol, quantity, action)
        )
    
    def place_limit_order(self, symbol: str, quantity: int, price: float,
                         action: str = 'BUY') -> TradeResult:
        """Place limit order synchronously"""
        return self.loop.run_until_complete(
            self.client.place_limit_order(symbol, quantity, price, action)
        )
    
    def get_portfolio(self) -> List[PortfolioPosition]:
        """Get portfolio synchronously"""
        return self.loop.run_until_complete(self.client.get_portfolio())
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary synchronously"""
        return self.loop.run_until_complete(self.client.get_account_summary())
    
    def get_positions(self) -> List[Position]:
        """Get positions synchronously"""
        return self.loop.run_until_complete(self.client.get_positions())
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()