"""
Enhanced Trading Framework with Interactive Brokers Integration

This module extends the original trading framework to support:
- Interactive Brokers API integration
- Real-time data and trading
- Portfolio management
- Risk management
- Live trading capabilities
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings

# Import original trading framework
from script import MultiSymbolDayTradingAlgo

# Import new IBKR integration
from ibkr_client import IBKRClientSync, IBKRConfig, TradeResult, PortfolioPosition
from config_manager import ConfigManager, get_config

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedTradingFramework(MultiSymbolDayTradingAlgo):
    """Enhanced trading framework with IBKR integration"""
    
    def __init__(self, symbols, initial_capital=50000, equal_weight=True, 
                 use_ibkr=False, config_manager=None):
        """
        Initialize enhanced trading framework
        
        Args:
            symbols: List of stock symbols or single symbol
            initial_capital: Starting capital
            equal_weight: If True, allocate capital equally across symbols
            use_ibkr: If True, use Interactive Brokers for data and trading
            config_manager: Configuration manager instance
        """
        super().__init__(symbols, initial_capital, equal_weight)
        
        # Configuration
        self.config_manager = config_manager or get_config()
        self.use_ibkr = use_ibkr
        
        # IBKR client
        self.ibkr_client = None
        if use_ibkr:
            self._initialize_ibkr()
        
        # Trading state
        self.live_trading = False
        self.positions = {}
        self.open_orders = {}
        self.trade_history = []
        self.portfolio_value = initial_capital
        
        # Risk management
        self.daily_pnl = 0.0
        self.max_daily_loss = self.config_manager.trading_config.max_daily_loss
        self.max_position_size = self.config_manager.trading_config.max_position_size
        self.stop_loss_pct = self.config_manager.trading_config.stop_loss_pct
        self.take_profit_pct = self.config_manager.trading_config.take_profit_pct
    
    def _initialize_ibkr(self):
        """Initialize Interactive Brokers client"""
        try:
            ibkr_config = IBKRConfig(
                host=self.config_manager.ibkr_credentials.host,
                port=self.config_manager.ibkr_credentials.port,
                client_id=self.config_manager.ibkr_credentials.client_id,
                timeout=self.config_manager.ibkr_credentials.timeout,
                paper_trading=self.config_manager.ibkr_credentials.paper_trading
            )
            self.ibkr_client = IBKRClientSync(ibkr_config)
            logger.info("IBKR client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize IBKR client: {e}")
            self.ibkr_client = None
    
    def connect_ibkr(self) -> bool:
        """Connect to Interactive Brokers
        
        Returns:
            bool: True if connected successfully
        """
        if not self.ibkr_client:
            self._initialize_ibkr()
        
        if self.ibkr_client:
            try:
                success = self.ibkr_client.connect()
                if success:
                    logger.info("Connected to Interactive Brokers")
                    return True
                else:
                    logger.error("Failed to connect to Interactive Brokers")
                    return False
            except Exception as e:
                logger.error(f"Error connecting to IBKR: {e}")
                return False
        return False
    
    def disconnect_ibkr(self):
        """Disconnect from Interactive Brokers"""
        if self.ibkr_client:
            self.ibkr_client.disconnect()
            logger.info("Disconnected from Interactive Brokers")
    
    def fetch_data_ibkr(self, period='1D', interval='5 mins') -> bool:
        """Fetch data using Interactive Brokers API
        
        Args:
            period: Data period (e.g., '1 D', '1 W', '1 M')
            interval: Data interval (e.g., '1 min', '5 mins', '1 hour')
            
        Returns:
            bool: True if data was fetched successfully
        """
        if not self.ibkr_client or not self.ibkr_client.is_connected():
            logger.error("IBKR client not connected")
            return False
        
        successful_symbols = []
        
        for symbol in self.symbols:
            try:
                data = self.ibkr_client.get_historical_data(symbol, period, interval)
                if data is not None and not data.empty:
                    self.data[symbol] = data
                    successful_symbols.append(symbol)
                    logger.info(f"Fetched {len(data)} data points for {symbol}")
                else:
                    logger.warning(f"No data retrieved for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
        
        if successful_symbols:
            logger.info(f"Successfully fetched data for {len(successful_symbols)} symbols")
            return True
        else:
            logger.error("Failed to fetch data for any symbols")
            return False
    
    def fetch_data_enhanced(self, period='5d', interval='5m', use_ibkr=None) -> bool:
        """Enhanced data fetching with automatic fallback
        
        Args:
            period: Data period
            interval: Data interval
            use_ibkr: Override use_ibkr setting
            
        Returns:
            bool: True if data was fetched successfully
        """
        use_ibkr = use_ibkr if use_ibkr is not None else self.use_ibkr
        
        if use_ibkr:
            # Try IBKR first
            if self.connect_ibkr():
                # Convert yfinance format to IBKR format
                ibkr_period = self._convert_period_to_ibkr(period)
                ibkr_interval = self._convert_interval_to_ibkr(interval)
                
                success = self.fetch_data_ibkr(ibkr_period, ibkr_interval)
                if success:
                    return True
                else:
                    logger.warning("IBKR data fetch failed, falling back to yfinance")
            else:
                logger.warning("IBKR connection failed, falling back to yfinance")
        
        # Fall back to yfinance
        try:
            return self.fetch_data_alternative(period, interval)
        except:
            return self.fetch_data(period, interval, sequential=True)
    
    def _convert_period_to_ibkr(self, period: str) -> str:
        """Convert yfinance period to IBKR format"""
        mapping = {
            '1d': '1 D',
            '5d': '5 D',
            '1mo': '1 M',
            '3mo': '3 M',
            '6mo': '6 M',
            '1y': '1 Y',
            '2y': '2 Y',
            '5y': '5 Y',
            '10y': '10 Y',
            'ytd': '1 Y',
            'max': '10 Y'
        }
        return mapping.get(period, period)
    
    def _convert_interval_to_ibkr(self, interval: str) -> str:
        """Convert yfinance interval to IBKR format"""
        mapping = {
            '1m': '1 min',
            '2m': '2 mins',
            '5m': '5 mins',
            '15m': '15 mins',
            '30m': '30 mins',
            '1h': '1 hour',
            '1d': '1 day'
        }
        return mapping.get(interval, interval)
    
    def get_live_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get live market data for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with market data or None
        """
        if not self.ibkr_client or not self.ibkr_client.is_connected():
            logger.error("IBKR client not connected")
            return None
        
        return self.ibkr_client.get_market_data(symbol)
    
    def execute_trade(self, symbol: str, quantity: int, order_type: str = 'market',
                     price: float = None) -> TradeResult:
        """Execute a trade
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares (positive for buy, negative for sell)
            order_type: 'market' or 'limit'
            price: Limit price (required for limit orders)
            
        Returns:
            TradeResult object
        """
        if not self.ibkr_client or not self.ibkr_client.is_connected():
            logger.error("IBKR client not connected")
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message="IBKR not connected",
                timestamp=datetime.now()
            )
        
        # Risk management checks
        if not self._check_risk_limits(symbol, quantity):
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message="Risk limits exceeded",
                timestamp=datetime.now()
            )
        
        action = 'BUY' if quantity > 0 else 'SELL'
        
        try:
            if order_type.lower() == 'market':
                result = self.ibkr_client.place_market_order(symbol, abs(quantity), action)
            elif order_type.lower() == 'limit':
                if price is None:
                    raise ValueError("Price required for limit orders")
                result = self.ibkr_client.place_limit_order(symbol, abs(quantity), price, action)
            else:
                raise ValueError(f"Unknown order type: {order_type}")
            
            # Update local positions if trade was successful
            if result.success:
                self._update_position(symbol, result.filled_qty if action == 'BUY' else -result.filled_qty)
                self.trade_history.append(result)
                logger.info(f"Trade executed: {action} {result.filled_qty} {symbol} at {result.avg_price}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return TradeResult(
                success=False,
                order_id=None,
                filled_qty=0,
                avg_price=0,
                commission=0,
                error_message=str(e),
                timestamp=datetime.now()
            )
    
    def _check_risk_limits(self, symbol: str, quantity: int) -> bool:
        """Check if trade complies with risk limits
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            
        Returns:
            bool: True if trade is within risk limits
        """
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss * self.initial_capital:
            logger.warning(f"Daily loss limit exceeded: {self.daily_pnl}")
            return False
        
        # Check position size limit
        current_position = self.positions.get(symbol, 0)
        new_position = current_position + quantity
        
        # Get current price for position value calculation
        market_data = self.get_live_market_data(symbol)
        if not market_data or not market_data.get('price'):
            logger.warning(f"Cannot get price for {symbol}")
            return False
        
        position_value = abs(new_position) * market_data['price']
        position_pct = position_value / self.portfolio_value
        
        if position_pct > self.max_position_size:
            logger.warning(f"Position size limit exceeded for {symbol}: {position_pct:.2%}")
            return False
        
        # Check maximum number of positions
        if len(self.positions) >= self.config_manager.trading_config.max_total_positions:
            logger.warning("Maximum number of positions reached")
            return False
        
        return True
    
    def _update_position(self, symbol: str, quantity: int):
        """Update position tracking
        
        Args:
            symbol: Stock symbol
            quantity: Change in position
        """
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        self.positions[symbol] += quantity
        
        # Remove position if it's zero
        if self.positions[symbol] == 0:
            del self.positions[symbol]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary
        
        Returns:
            Dictionary with portfolio information
        """
        if self.ibkr_client and self.ibkr_client.is_connected():
            try:
                # Get live portfolio data from IBKR
                portfolio_positions = self.ibkr_client.get_portfolio()
                account_summary = self.ibkr_client.get_account_summary()
                
                summary = {
                    'timestamp': datetime.now(),
                    'account_value': account_summary.get('NetLiquidation', 0),
                    'cash': account_summary.get('TotalCashValue', 0),
                    'unrealized_pnl': account_summary.get('UnrealizedPnL', 0),
                    'realized_pnl': account_summary.get('RealizedPnL', 0),
                    'buying_power': account_summary.get('BuyingPower', 0),
                    'positions': []
                }
                
                for pos in portfolio_positions:
                    summary['positions'].append({
                        'symbol': pos.symbol,
                        'quantity': pos.position,
                        'price': pos.market_price,
                        'value': pos.market_value,
                        'pnl': pos.unrealized_pnl
                    })
                
                return summary
                
            except Exception as e:
                logger.error(f"Error getting portfolio summary: {e}")
        
        # Fallback to local tracking
        return {
            'timestamp': datetime.now(),
            'account_value': self.portfolio_value,
            'cash': self.portfolio_value,
            'unrealized_pnl': 0,
            'realized_pnl': self.daily_pnl,
            'buying_power': self.portfolio_value,
            'positions': [
                {
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': 0,
                    'value': 0,
                    'pnl': 0
                }
                for symbol, quantity in self.positions.items()
            ]
        }
    
    def start_live_trading(self, strategy_name: str = 'combined'):
        """Start live trading with the specified strategy
        
        Args:
            strategy_name: Name of the strategy to use
        """
        if not self.ibkr_client or not self.ibkr_client.is_connected():
            logger.error("IBKR client not connected")
            return
        
        if not self.data:
            logger.error("No data available for trading")
            return
        
        self.live_trading = True
        logger.info(f"Starting live trading with {strategy_name} strategy")
        
        # This is a basic implementation - in practice you'd want a more sophisticated
        # event-driven system with proper scheduling
        try:
            while self.live_trading:
                # Get current market data
                for symbol in self.symbols:
                    market_data = self.get_live_market_data(symbol)
                    if market_data:
                        # Update data with latest price
                        self._update_live_data(symbol, market_data)
                
                # Calculate indicators
                self.calculate_indicators()
                
                # Generate signals
                signals = self.get_strategy_signals(strategy_name)
                
                # Execute trades based on signals
                for symbol, signal in signals.items():
                    if signal != 0:  # 0 = hold, 1 = buy, -1 = sell
                        self._execute_signal(symbol, signal)
                
                # Check stop losses and take profits
                self._check_stop_losses()
                self._check_take_profits()
                
                # Sleep between iterations
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Live trading stopped by user")
        except Exception as e:
            logger.error(f"Error in live trading: {e}")
        finally:
            self.live_trading = False
    
    def stop_live_trading(self):
        """Stop live trading"""
        self.live_trading = False
        logger.info("Live trading stopped")
    
    def _update_live_data(self, symbol: str, market_data: Dict[str, Any]):
        """Update live data with current market information
        
        Args:
            symbol: Stock symbol
            market_data: Current market data
        """
        if symbol not in self.data:
            return
        
        # Create new row with current data
        new_row = pd.DataFrame({
            'Open': [market_data.get('price', 0)],
            'High': [market_data.get('price', 0)],
            'Low': [market_data.get('price', 0)],
            'Close': [market_data.get('price', 0)],
            'Volume': [market_data.get('volume', 0)]
        }, index=[datetime.now()])
        
        # Append to existing data
        self.data[symbol] = pd.concat([self.data[symbol], new_row])
        
        # Keep only recent data to prevent memory issues
        if len(self.data[symbol]) > 1000:
            self.data[symbol] = self.data[symbol].tail(1000)
    
    def get_strategy_signals(self, strategy_name: str) -> Dict[str, int]:
        """Get trading signals for all symbols
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary mapping symbol to signal (-1, 0, 1)
        """
        signals = {}
        
        for symbol in self.symbols:
            if symbol in self.data:
                try:
                    strategy_signals = getattr(self, f"{strategy_name}_strategy")(symbol)
                    if not strategy_signals.empty:
                        signals[symbol] = strategy_signals['signal'].iloc[-1]
                    else:
                        signals[symbol] = 0
                except Exception as e:
                    logger.error(f"Error getting signal for {symbol}: {e}")
                    signals[symbol] = 0
        
        return signals
    
    def _execute_signal(self, symbol: str, signal: int):
        """Execute a trading signal
        
        Args:
            symbol: Stock symbol
            signal: Trading signal (-1, 0, 1)
        """
        if signal == 0:
            return
        
        # Calculate position size based on available capital
        market_data = self.get_live_market_data(symbol)
        if not market_data or not market_data.get('price'):
            return
        
        price = market_data['price']
        max_position_value = self.portfolio_value * self.max_position_size
        quantity = int(max_position_value / price)
        
        if signal == 1:  # Buy signal
            if quantity > 0:
                self.execute_trade(symbol, quantity, 'market')
        elif signal == -1:  # Sell signal
            current_position = self.positions.get(symbol, 0)
            if current_position > 0:
                self.execute_trade(symbol, -current_position, 'market')
    
    def _check_stop_losses(self):
        """Check and execute stop losses"""
        for symbol, position in self.positions.items():
            if position <= 0:
                continue
            
            market_data = self.get_live_market_data(symbol)
            if not market_data or not market_data.get('price'):
                continue
            
            current_price = market_data['price']
            
            # Calculate stop loss based on entry price (simplified)
            # In practice, you'd track actual entry prices
            stop_loss_price = current_price * (1 - self.stop_loss_pct)
            
            if current_price <= stop_loss_price:
                logger.info(f"Stop loss triggered for {symbol}")
                self.execute_trade(symbol, -position, 'market')
    
    def _check_take_profits(self):
        """Check and execute take profits"""
        for symbol, position in self.positions.items():
            if position <= 0:
                continue
            
            market_data = self.get_live_market_data(symbol)
            if not market_data or not market_data.get('price'):
                continue
            
            current_price = market_data['price']
            
            # Calculate take profit based on entry price (simplified)
            # In practice, you'd track actual entry prices
            take_profit_price = current_price * (1 + self.take_profit_pct)
            
            if current_price >= take_profit_price:
                logger.info(f"Take profit triggered for {symbol}")
                self.execute_trade(symbol, -position, 'market')
    
    def create_portfolio_dashboard(self) -> pd.DataFrame:
        """Create a portfolio dashboard
        
        Returns:
            DataFrame with portfolio metrics
        """
        portfolio_summary = self.get_portfolio_summary()
        
        # Create dashboard data
        dashboard_data = {
            'Account Value': f"${portfolio_summary['account_value']:,.2f}",
            'Cash': f"${portfolio_summary['cash']:,.2f}",
            'Unrealized P&L': f"${portfolio_summary['unrealized_pnl']:,.2f}",
            'Realized P&L': f"${portfolio_summary['realized_pnl']:,.2f}",
            'Buying Power': f"${portfolio_summary['buying_power']:,.2f}",
            'Total Positions': len(portfolio_summary['positions']),
            'Last Updated': portfolio_summary['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        }
        
        dashboard_df = pd.DataFrame(list(dashboard_data.items()), 
                                  columns=['Metric', 'Value'])
        
        return dashboard_df
    
    def get_trade_history(self) -> pd.DataFrame:
        """Get trade history as DataFrame
        
        Returns:
            DataFrame with trade history
        """
        if not self.trade_history:
            return pd.DataFrame()
        
        trades_data = []
        for trade in self.trade_history:
            trades_data.append({
                'Timestamp': trade.timestamp,
                'Order ID': trade.order_id,
                'Filled Qty': trade.filled_qty,
                'Avg Price': trade.avg_price,
                'Commission': trade.commission,
                'Success': trade.success,
                'Error': trade.error_message
            })
        
        return pd.DataFrame(trades_data)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_live_trading()
        self.disconnect_ibkr()


# Convenience function for quick setup
def create_enhanced_trader(symbols: List[str], use_ibkr: bool = False, 
                          initial_capital: float = 50000) -> EnhancedTradingFramework:
    """Create an enhanced trading framework instance
    
    Args:
        symbols: List of stock symbols
        use_ibkr: Whether to use Interactive Brokers
        initial_capital: Starting capital
        
    Returns:
        EnhancedTradingFramework instance
    """
    return EnhancedTradingFramework(
        symbols=symbols,
        initial_capital=initial_capital,
        use_ibkr=use_ibkr
    )