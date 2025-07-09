"""
Enhanced Multi-Symbol Trading Algorithm with IBKR Integration
This module extends the existing trading framework to support real-time trading
through the Interactive Brokers API.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from ibkr_api import IBKRAPIClient, IBKRConfigManager, TradeOrder
from portfolio_dashboard import PortfolioDashboard
from script import MultiSymbolDayTradingAlgo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Enhanced trading signal with IBKR integration"""
    symbol: str
    signal: int  # 1 for buy, -1 for sell, 0 for hold
    confidence: float  # 0.0 to 1.0
    strategy: str
    timestamp: datetime
    current_price: float
    suggested_quantity: int
    order_type: str = 'MARKET'
    limit_price: Optional[float] = None


class LiveTradingAlgorithm(MultiSymbolDayTradingAlgo):
    """
    Enhanced trading algorithm with Interactive Brokers API integration.
    
    Extends the base MultiSymbolDayTradingAlgo to support:
    - Real-time data from IBKR API
    - Live trade execution
    - Portfolio management
    - Risk controls
    """
    
    def __init__(self, symbols: List[str], initial_capital: float = 10000,
                 use_ibkr: bool = True, paper_trading: bool = True,
                 max_position_size: float = 1000, max_daily_trades: int = 10):
        """
        Initialize the live trading algorithm.
        
        Args:
            symbols: List of stock symbols to trade
            initial_capital: Starting capital
            use_ibkr: Whether to use IBKR API for real-time data and trading
            paper_trading: Whether to use paper trading (recommended for testing)
            max_position_size: Maximum position size in dollars
            max_daily_trades: Maximum number of trades per day
        """
        super().__init__(symbols, initial_capital)
        
        self.use_ibkr = use_ibkr
        self.paper_trading = paper_trading
        self.max_position_size = max_position_size
        self.max_daily_trades = max_daily_trades
        
        # IBKR integration
        self.ibkr_client = None
        self.dashboard = None
        self.config_manager = None
        
        # Live trading state
        self.active_orders = {}  # Track active orders
        self.daily_trades = 0
        self.last_trade_date = None
        self.current_signals = {}  # Current trading signals
        
        # Risk management
        self.daily_pnl = 0.0
        self.max_daily_loss = 500.0  # Maximum daily loss
        self.position_limits = {}  # Position size limits per symbol
        
        # Initialize IBKR if enabled
        if self.use_ibkr:
            self._initialize_ibkr()
    
    def _initialize_ibkr(self):
        """Initialize IBKR API client and configuration."""
        try:
            self.config_manager = IBKRConfigManager()
            host, port, client_id = self.config_manager.get_connection_params()
            
            self.ibkr_client = IBKRAPIClient(host, port, client_id)
            self.dashboard = PortfolioDashboard(self.ibkr_client)
            
            logger.info("IBKR integration initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize IBKR: {e}")
            self.use_ibkr = False
    
    async def connect_to_ibkr(self) -> bool:
        """
        Connect to Interactive Brokers API.
        
        Returns:
            bool: True if connection successful
        """
        if not self.use_ibkr or not self.ibkr_client:
            return False
        
        try:
            success = await self.ibkr_client.connect()
            if success:
                logger.info("Connected to IBKR API")
                return True
            else:
                logger.error("Failed to connect to IBKR API")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to IBKR: {e}")
            return False
    
    async def disconnect_from_ibkr(self):
        """Disconnect from IBKR API."""
        if self.ibkr_client:
            self.ibkr_client.disconnect()
            logger.info("Disconnected from IBKR API")
    
    async def fetch_real_time_data(self, duration: str = '1 D', bar_size: str = '5 mins') -> bool:
        """
        Fetch real-time data from IBKR API.
        
        Args:
            duration: Data duration (e.g., '1 D', '1 W')
            bar_size: Bar size (e.g., '1 min', '5 mins')
            
        Returns:
            bool: True if data fetched successfully
        """
        if not self.use_ibkr or not self.ibkr_client:
            logger.warning("IBKR not available, falling back to yfinance")
            return self.fetch_data_alternative()
        
        try:
            self.data = await self.ibkr_client.get_real_time_data(
                self.symbols, duration, bar_size
            )
            
            if self.data:
                logger.info(f"Fetched real-time data for {len(self.data)} symbols")
                return True
            else:
                logger.warning("No real-time data received, falling back to yfinance")
                return self.fetch_data_alternative()
                
        except Exception as e:
            logger.error(f"Error fetching real-time data: {e}")
            logger.warning("Falling back to yfinance")
            return self.fetch_data_alternative()
    
    async def get_current_market_data(self) -> Dict[str, Dict[str, float]]:
        """
        Get current market data for all symbols.
        
        Returns:
            Dictionary mapping symbols to market data
        """
        if not self.use_ibkr or not self.ibkr_client:
            return {}
        
        try:
            return await self.ibkr_client.get_market_data(self.symbols)
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}
    
    async def generate_trading_signals(self, strategy: str = 'combined') -> List[TradingSignal]:
        """
        Generate trading signals based on current market data.
        
        Args:
            strategy: Trading strategy to use
            
        Returns:
            List of trading signals
        """
        if not self.data:
            logger.warning("No data available for signal generation")
            return []
        
        signals = []
        market_data = await self.get_current_market_data()
        
        for symbol in self.symbols:
            try:
                # Generate signal using the selected strategy
                if strategy == 'combined':
                    signal_df = self.combined_strategy(symbol)
                elif strategy == 'momentum':
                    signal_df = self.momentum_strategy(symbol)
                elif strategy == 'mean_reversion':
                    signal_df = self.mean_reversion_strategy(symbol)
                else:
                    logger.warning(f"Unknown strategy: {strategy}")
                    continue
                
                if signal_df.empty:
                    continue
                
                # Get the latest signal
                latest_signal = signal_df['signal'].iloc[-1]
                
                if latest_signal != 0:  # Only process non-zero signals
                    current_price = market_data.get(symbol, {}).get('price', 0)
                    if current_price == 0:
                        current_price = self.data[symbol]['Close'].iloc[-1]
                    
                    # Calculate suggested quantity based on position size limits
                    suggested_quantity = self._calculate_position_size(symbol, current_price)
                    
                    # Calculate confidence based on signal strength
                    confidence = self._calculate_signal_confidence(signal_df, symbol)
                    
                    trading_signal = TradingSignal(
                        symbol=symbol,
                        signal=latest_signal,
                        confidence=confidence,
                        strategy=strategy,
                        timestamp=datetime.now(),
                        current_price=current_price,
                        suggested_quantity=suggested_quantity
                    )
                    
                    signals.append(trading_signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        
        return signals
    
    def _calculate_position_size(self, symbol: str, current_price: float) -> int:
        """Calculate appropriate position size for a symbol."""
        if current_price <= 0:
            return 0
        
        # Use maximum position size limit
        max_shares = int(self.max_position_size / current_price)
        
        # Check if we have symbol-specific limits
        if symbol in self.position_limits:
            max_shares = min(max_shares, self.position_limits[symbol])
        
        # Ensure we don't exceed available capital
        available_capital = self.initial_capital * 0.8  # Keep 20% cash buffer
        max_shares_by_capital = int(available_capital / current_price)
        
        return min(max_shares, max_shares_by_capital)
    
    def _calculate_signal_confidence(self, signal_df: pd.DataFrame, symbol: str) -> float:
        """Calculate confidence level for a trading signal."""
        try:
            # This is a simplified confidence calculation
            # In practice, you'd want more sophisticated methods
            
            # Look at recent signal consistency
            recent_signals = signal_df['signal'].tail(5)
            consistency = abs(recent_signals.sum()) / len(recent_signals)
            
            # Check volatility (lower volatility = higher confidence)
            if symbol in self.data:
                volatility = self.data[symbol]['Close'].pct_change().std()
                volatility_score = max(0, 1 - volatility * 100)  # Normalize
            else:
                volatility_score = 0.5
            
            # Combine factors
            confidence = (consistency * 0.6 + volatility_score * 0.4)
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence for {symbol}: {e}")
            return 0.5
    
    async def execute_trade(self, signal: TradingSignal) -> Optional[TradeOrder]:
        """
        Execute a trade based on a trading signal.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            TradeOrder object if successful, None otherwise
        """
        if not self.use_ibkr or not self.ibkr_client:
            logger.warning("IBKR not available, cannot execute real trades")
            return None
        
        # Pre-execution checks
        if not self._pre_execution_checks(signal):
            return None
        
        try:
            # Determine action
            action = 'BUY' if signal.signal > 0 else 'SELL'
            
            # Execute trade
            trade_order = await self.ibkr_client.place_order(
                symbol=signal.symbol,
                action=action,
                quantity=signal.suggested_quantity,
                order_type=signal.order_type,
                price=signal.limit_price
            )
            
            if trade_order.status not in ['FAILED']:
                # Track the order
                self.active_orders[trade_order.order_id] = trade_order
                
                # Update daily trade count
                today = datetime.now().date()
                if self.last_trade_date != today:
                    self.daily_trades = 0
                    self.last_trade_date = today
                
                self.daily_trades += 1
                
                logger.info(f"Trade executed: {action} {signal.suggested_quantity} "
                           f"{signal.symbol} at ${signal.current_price:.2f}")
                
                return trade_order
            else:
                logger.error(f"Trade failed: {trade_order.status}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None
    
    def _pre_execution_checks(self, signal: TradingSignal) -> bool:
        """Perform pre-execution risk checks."""
        
        # Check if market is open
        if self.use_ibkr and not self.ibkr_client.is_market_open():
            logger.warning("Market is closed, cannot execute trade")
            return False
        
        # Check daily trade limit
        today = datetime.now().date()
        if self.last_trade_date == today and self.daily_trades >= self.max_daily_trades:
            logger.warning(f"Daily trade limit reached ({self.max_daily_trades})")
            return False
        
        # Check confidence threshold
        if signal.confidence < 0.6:  # Minimum confidence threshold
            logger.warning(f"Signal confidence too low: {signal.confidence:.2f}")
            return False
        
        # Check position size
        if signal.suggested_quantity <= 0:
            logger.warning("Invalid position size")
            return False
        
        # Check if we have enough capital
        required_capital = signal.suggested_quantity * signal.current_price
        if required_capital > self.max_position_size:
            logger.warning(f"Position size exceeds limit: ${required_capital:.2f} > ${self.max_position_size:.2f}")
            return False
        
        return True
    
    async def update_order_status(self):
        """Update status of active orders."""
        if not self.active_orders:
            return
        
        for order_id in list(self.active_orders.keys()):
            try:
                updated_order = await self.ibkr_client.get_order_status(order_id)
                if updated_order:
                    self.active_orders[order_id] = updated_order
                    
                    # Remove completed orders
                    if updated_order.status in ['FILLED', 'CANCELLED']:
                        del self.active_orders[order_id]
                        logger.info(f"Order {order_id} completed with status: {updated_order.status}")
                        
            except Exception as e:
                logger.error(f"Error updating order {order_id}: {e}")
    
    async def run_live_trading(self, strategy: str = 'combined', 
                              check_interval: int = 300):  # 5 minutes
        """
        Run live trading session.
        
        Args:
            strategy: Trading strategy to use
            check_interval: Check interval in seconds
        """
        if not self.use_ibkr:
            logger.error("IBKR not available for live trading")
            return
        
        # Connect to IBKR
        if not await self.connect_to_ibkr():
            return
        
        logger.info("Starting live trading session...")
        logger.info(f"Strategy: {strategy}")
        logger.info(f"Check interval: {check_interval} seconds")
        logger.info(f"Paper trading: {self.paper_trading}")
        
        try:
            while True:
                # Fetch latest data
                await self.fetch_real_time_data()
                
                if self.data:
                    # Calculate indicators
                    self.calculate_indicators()
                    
                    # Generate trading signals
                    signals = await self.generate_trading_signals(strategy)
                    
                    # Execute trades based on signals
                    for signal in signals:
                        await self.execute_trade(signal)
                    
                    # Update order status
                    await self.update_order_status()
                    
                    # Record portfolio snapshot
                    if self.dashboard:
                        await self.dashboard.record_portfolio_snapshot()
                    
                    # Print summary
                    await self._print_trading_summary()
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("Live trading session stopped by user")
        except Exception as e:
            logger.error(f"Error in live trading session: {e}")
        finally:
            await self.disconnect_from_ibkr()
    
    async def _print_trading_summary(self):
        """Print current trading summary."""
        if not self.dashboard:
            return
        
        try:
            metrics = await self.dashboard.get_portfolio_summary()
            
            print(f"\n{'='*50}")
            print(f"LIVE TRADING SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*50}")
            print(f"Portfolio Value: ${metrics.total_value:,.2f}")
            print(f"Cash: ${metrics.cash:,.2f}")
            print(f"Unrealized P&L: ${metrics.unrealized_pnl:,.2f}")
            print(f"Return: {metrics.return_percentage:.2f}%")
            print(f"Positions: {metrics.positions_count}")
            print(f"Active Orders: {len(self.active_orders)}")
            print(f"Daily Trades: {self.daily_trades}")
            print(f"{'='*50}")
            
        except Exception as e:
            logger.error(f"Error printing summary: {e}")
    
    async def backtest_with_ibkr_data(self, strategy: str = 'combined',
                                     duration: str = '1 M') -> Dict:
        """
        Run backtest using real IBKR data.
        
        Args:
            strategy: Trading strategy to use
            duration: Data duration for backtest
            
        Returns:
            Backtest results
        """
        # Fetch historical data
        success = await self.fetch_real_time_data(duration=duration, bar_size='1 hour')
        
        if not success:
            logger.error("Failed to fetch data for backtesting")
            return {}
        
        # Calculate indicators
        self.calculate_indicators()
        
        # Run backtest
        return self.backtest_strategy(strategy)
    
    def create_sample_config(self):
        """Create sample configuration file."""
        if self.config_manager:
            self.config_manager.create_sample_config()
        else:
            logger.warning("Config manager not initialized")


# Utility functions for ease of use
async def create_live_trader(symbols: List[str], 
                           initial_capital: float = 10000,
                           paper_trading: bool = True) -> LiveTradingAlgorithm:
    """
    Create and initialize a live trading algorithm.
    
    Args:
        symbols: List of symbols to trade
        initial_capital: Starting capital
        paper_trading: Whether to use paper trading
        
    Returns:
        Initialized LiveTradingAlgorithm instance
    """
    trader = LiveTradingAlgorithm(
        symbols=symbols,
        initial_capital=initial_capital,
        paper_trading=paper_trading
    )
    
    # Connect to IBKR
    await trader.connect_to_ibkr()
    
    return trader


async def run_portfolio_dashboard(symbols: List[str]):
    """
    Run portfolio dashboard for monitoring.
    
    Args:
        symbols: List of symbols to monitor
    """
    trader = await create_live_trader(symbols)
    
    if trader.dashboard:
        await trader.dashboard.run_dashboard()
    else:
        print("Dashboard not available")


# Example usage
async def main():
    """Example usage of the live trading system."""
    
    # Create trader instance
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    trader = LiveTradingAlgorithm(
        symbols=symbols,
        initial_capital=10000,
        paper_trading=True,  # Always use paper trading for testing
        max_position_size=1000
    )
    
    # Connect to IBKR
    if await trader.connect_to_ibkr():
        print("Connected to IBKR successfully!")
        
        # Run portfolio dashboard
        if trader.dashboard:
            await trader.dashboard.display_portfolio_summary()
        
        # Example: Generate trading signals
        await trader.fetch_real_time_data()
        if trader.data:
            trader.calculate_indicators()
            signals = await trader.generate_trading_signals('combined')
            
            print(f"\nGenerated {len(signals)} trading signals:")
            for signal in signals:
                print(f"  {signal.symbol}: {signal.signal} (confidence: {signal.confidence:.2f})")
    
    # Always disconnect
    await trader.disconnect_from_ibkr()


if __name__ == "__main__":
    asyncio.run(main())