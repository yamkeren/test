#!/usr/bin/env python3
"""
Test suite for IBKR integration in the enhanced trading framework

This test suite covers:
- IBKR client functionality
- Configuration management
- Enhanced trading framework
- Risk management
- Portfolio management
"""

import unittest
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os
import sys
import tempfile
import shutil

# Import modules to test
from ibkr_client import IBKRClient, IBKRClientSync, IBKRConfig, TradeResult, PortfolioPosition
from config_manager import ConfigManager, TradingConfig, IBKRCredentials
from enhanced_trading import EnhancedTradingFramework, create_enhanced_trader


class TestIBKRConfig(unittest.TestCase):
    """Test IBKR configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = IBKRConfig()
        self.assertEqual(config.host, '127.0.0.1')
        self.assertEqual(config.port, 7497)
        self.assertEqual(config.client_id, 1)
        self.assertTrue(config.paper_trading)
        self.assertEqual(config.timeout, 30)
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = IBKRConfig(
            host='192.168.1.100',
            port=7496,
            client_id=2,
            paper_trading=False,
            timeout=60
        )
        self.assertEqual(config.host, '192.168.1.100')
        self.assertEqual(config.port, 7496)
        self.assertEqual(config.client_id, 2)
        self.assertFalse(config.paper_trading)
        self.assertEqual(config.timeout, 60)


class TestTradeResult(unittest.TestCase):
    """Test TradeResult data structure"""
    
    def test_successful_trade(self):
        """Test successful trade result"""
        result = TradeResult(
            success=True,
            order_id=12345,
            filled_qty=100,
            avg_price=150.50,
            commission=1.0,
            error_message=None,
            timestamp=datetime.now()
        )
        self.assertTrue(result.success)
        self.assertEqual(result.order_id, 12345)
        self.assertEqual(result.filled_qty, 100)
        self.assertEqual(result.avg_price, 150.50)
        self.assertEqual(result.commission, 1.0)
        self.assertIsNone(result.error_message)
    
    def test_failed_trade(self):
        """Test failed trade result"""
        result = TradeResult(
            success=False,
            order_id=None,
            filled_qty=0,
            avg_price=0,
            commission=0,
            error_message="Order rejected",
            timestamp=datetime.now()
        )
        self.assertFalse(result.success)
        self.assertIsNone(result.order_id)
        self.assertEqual(result.filled_qty, 0)
        self.assertEqual(result.error_message, "Order rejected")


class TestPortfolioPosition(unittest.TestCase):
    """Test PortfolioPosition data structure"""
    
    def test_position_creation(self):
        """Test portfolio position creation"""
        position = PortfolioPosition(
            symbol='AAPL',
            position=100,
            market_price=150.0,
            market_value=15000.0,
            avg_cost=145.0,
            unrealized_pnl=500.0,
            realized_pnl=0.0
        )
        self.assertEqual(position.symbol, 'AAPL')
        self.assertEqual(position.position, 100)
        self.assertEqual(position.market_price, 150.0)
        self.assertEqual(position.market_value, 15000.0)
        self.assertEqual(position.avg_cost, 145.0)
        self.assertEqual(position.unrealized_pnl, 500.0)
        self.assertEqual(position.realized_pnl, 0.0)


class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_default_trading_config(self):
        """Test default trading configuration"""
        config = self.config_manager.trading_config
        self.assertEqual(config.data_source, 'yfinance')
        self.assertEqual(config.initial_capital, 50000.0)
        self.assertEqual(config.max_position_size, 0.1)
        self.assertEqual(config.stop_loss_pct, 0.05)
        self.assertEqual(config.take_profit_pct, 0.10)
        self.assertEqual(config.default_strategy, 'combined')
    
    def test_default_ibkr_credentials(self):
        """Test default IBKR credentials"""
        creds = self.config_manager.ibkr_credentials
        self.assertEqual(creds.host, '127.0.0.1')
        self.assertEqual(creds.port, 7497)
        self.assertEqual(creds.client_id, 1)
        self.assertTrue(creds.paper_trading)
        self.assertEqual(creds.timeout, 30)
    
    def test_update_trading_config(self):
        """Test updating trading configuration"""
        self.config_manager.update_trading_config(
            initial_capital=100000.0,
            max_position_size=0.2
        )
        self.assertEqual(self.config_manager.trading_config.initial_capital, 100000.0)
        self.assertEqual(self.config_manager.trading_config.max_position_size, 0.2)
    
    def test_update_ibkr_credentials(self):
        """Test updating IBKR credentials"""
        self.config_manager.update_ibkr_credentials(
            host='192.168.1.100',
            port=7496,
            paper_trading=False
        )
        self.assertEqual(self.config_manager.ibkr_credentials.host, '192.168.1.100')
        self.assertEqual(self.config_manager.ibkr_credentials.port, 7496)
        self.assertFalse(self.config_manager.ibkr_credentials.paper_trading)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid configuration should pass
        self.assertTrue(self.config_manager.validate_config())
        
        # Invalid configuration should fail
        self.config_manager.update_trading_config(max_position_size=1.5)  # > 1
        self.assertFalse(self.config_manager.validate_config())
    
    def test_sample_env_file(self):
        """Test sample environment file creation"""
        sample_file = os.path.join(self.temp_dir, 'test.env')
        self.config_manager.create_sample_env_file(sample_file)
        
        self.assertTrue(os.path.exists(sample_file))
        with open(sample_file, 'r') as f:
            content = f.read()
            self.assertIn('TRADING_INITIAL_CAPITAL', content)
            self.assertIn('IBKR_HOST', content)
            self.assertIn('IBKR_PORT', content)


class TestEnhancedTradingFramework(unittest.TestCase):
    """Test enhanced trading framework"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        self.symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        # Create test data
        dates = pd.date_range('2024-01-01', periods=100, freq='5min')
        self.test_data = {}
        
        for symbol in self.symbols:
            np.random.seed(42)
            prices = 100 + np.random.randn(100).cumsum()
            self.test_data[symbol] = pd.DataFrame({
                'Open': prices,
                'High': prices * 1.01,
                'Low': prices * 0.99,
                'Close': prices,
                'Volume': np.random.randint(1000, 10000, 100)
            }, index=dates)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test framework initialization"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        self.assertEqual(framework.symbols, self.symbols)
        self.assertEqual(framework.initial_capital, 50000)
        self.assertFalse(framework.use_ibkr)
        self.assertEqual(framework.config_manager, self.config_manager)
        self.assertIsNone(framework.ibkr_client)
    
    def test_ibkr_initialization(self):
        """Test IBKR client initialization"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=True,
            config_manager=self.config_manager
        )
        
        self.assertTrue(framework.use_ibkr)
        self.assertIsNotNone(framework.ibkr_client)
    
    def test_data_fetching_fallback(self):
        """Test data fetching with fallback"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Mock the original fetch_data_alternative method
        framework.fetch_data_alternative = Mock(return_value=True)
        framework.data = self.test_data
        
        # Test fallback to yfinance
        result = framework.fetch_data_enhanced(use_ibkr=False)
        self.assertTrue(result)
        framework.fetch_data_alternative.assert_called_once()
    
    def test_period_conversion(self):
        """Test period conversion to IBKR format"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        self.assertEqual(framework._convert_period_to_ibkr('1d'), '1 D')
        self.assertEqual(framework._convert_period_to_ibkr('1mo'), '1 M')
        self.assertEqual(framework._convert_period_to_ibkr('1y'), '1 Y')
    
    def test_interval_conversion(self):
        """Test interval conversion to IBKR format"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        self.assertEqual(framework._convert_interval_to_ibkr('1m'), '1 min')
        self.assertEqual(framework._convert_interval_to_ibkr('5m'), '5 mins')
        self.assertEqual(framework._convert_interval_to_ibkr('1h'), '1 hour')
    
    def test_risk_limits_position_size(self):
        """Test position size risk limits"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Mock get_live_market_data to return a price
        framework.get_live_market_data = Mock(return_value={'price': 100.0})
        
        # Test position size limit
        framework.portfolio_value = 50000
        framework.max_position_size = 0.1  # 10% max position
        
        # Large position should be rejected
        self.assertFalse(framework._check_risk_limits('AAPL', 10000))  # $1M position
        
        # Small position should be accepted
        self.assertTrue(framework._check_risk_limits('AAPL', 50))  # $5K position
    
    def test_risk_limits_daily_loss(self):
        """Test daily loss risk limits"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Mock get_live_market_data to return a price
        framework.get_live_market_data = Mock(return_value={'price': 100.0})
        
        # Set daily loss limit
        framework.max_daily_loss = 0.02  # 2% max daily loss
        framework.daily_pnl = -1500  # $1,500 loss (3% of $50,000)
        
        # Trade should be rejected due to daily loss limit
        self.assertFalse(framework._check_risk_limits('AAPL', 100))
    
    def test_position_update(self):
        """Test position tracking updates"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Test adding position
        framework._update_position('AAPL', 100)
        self.assertEqual(framework.positions['AAPL'], 100)
        
        # Test modifying position
        framework._update_position('AAPL', 50)
        self.assertEqual(framework.positions['AAPL'], 150)
        
        # Test closing position
        framework._update_position('AAPL', -150)
        self.assertNotIn('AAPL', framework.positions)
    
    def test_portfolio_summary_fallback(self):
        """Test portfolio summary fallback"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Add some positions
        framework.positions = {'AAPL': 100, 'MSFT': 200}
        framework.daily_pnl = 500.0
        
        summary = framework.get_portfolio_summary()
        
        self.assertEqual(summary['account_value'], 50000)
        self.assertEqual(summary['realized_pnl'], 500.0)
        self.assertEqual(len(summary['positions']), 2)
    
    def test_create_portfolio_dashboard(self):
        """Test portfolio dashboard creation"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Mock get_portfolio_summary
        framework.get_portfolio_summary = Mock(return_value={
            'account_value': 52000,
            'cash': 10000,
            'unrealized_pnl': 2000,
            'realized_pnl': 0,
            'buying_power': 50000,
            'positions': [{'symbol': 'AAPL', 'quantity': 100}],
            'timestamp': datetime.now()
        })
        
        dashboard = framework.create_portfolio_dashboard()
        
        self.assertIsInstance(dashboard, pd.DataFrame)
        self.assertEqual(len(dashboard), 7)  # 7 metrics
        self.assertIn('Account Value', dashboard['Metric'].values)
        self.assertIn('Total Positions', dashboard['Metric'].values)
    
    def test_trade_history(self):
        """Test trade history tracking"""
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        )
        
        # Add some mock trades
        trade1 = TradeResult(
            success=True,
            order_id=123,
            filled_qty=100,
            avg_price=150.0,
            commission=1.0,
            error_message=None,
            timestamp=datetime.now()
        )
        
        trade2 = TradeResult(
            success=False,
            order_id=124,
            filled_qty=0,
            avg_price=0,
            commission=0,
            error_message="Order rejected",
            timestamp=datetime.now()
        )
        
        framework.trade_history = [trade1, trade2]
        
        history_df = framework.get_trade_history()
        
        self.assertIsInstance(history_df, pd.DataFrame)
        self.assertEqual(len(history_df), 2)
        self.assertEqual(history_df.iloc[0]['Order ID'], 123)
        self.assertEqual(history_df.iloc[1]['Success'], False)
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=False,
            config_manager=self.config_manager
        ) as framework:
            self.assertIsNotNone(framework)
            self.assertFalse(framework.live_trading)
        
        # After exiting context, live trading should be stopped
        self.assertFalse(framework.live_trading)


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions"""
    
    def test_create_enhanced_trader(self):
        """Test create_enhanced_trader function"""
        symbols = ['AAPL', 'MSFT']
        trader = create_enhanced_trader(symbols, use_ibkr=False, initial_capital=100000)
        
        self.assertIsInstance(trader, EnhancedTradingFramework)
        self.assertEqual(trader.symbols, symbols)
        self.assertEqual(trader.initial_capital, 100000)
        self.assertFalse(trader.use_ibkr)


class TestMockIBKRIntegration(unittest.TestCase):
    """Test IBKR integration with mocks"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        self.symbols = ['AAPL', 'MSFT']
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('enhanced_trading.IBKRClientSync')
    def test_ibkr_connection(self, mock_client_class):
        """Test IBKR connection with mocked client"""
        mock_client = Mock()
        mock_client.connect.return_value = True
        mock_client.is_connected.return_value = True
        mock_client_class.return_value = mock_client
        
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=True,
            config_manager=self.config_manager
        )
        
        # Test connection
        result = framework.connect_ibkr()
        self.assertTrue(result)
        mock_client.connect.assert_called_once()
    
    @patch('enhanced_trading.IBKRClientSync')
    def test_market_data_retrieval(self, mock_client_class):
        """Test market data retrieval with mocked client"""
        mock_client = Mock()
        mock_client.is_connected.return_value = True
        mock_client.get_market_data.return_value = {
            'symbol': 'AAPL',
            'price': 150.0,
            'bid': 149.5,
            'ask': 150.5,
            'volume': 1000,
            'timestamp': datetime.now()
        }
        mock_client_class.return_value = mock_client
        
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=True,
            config_manager=self.config_manager
        )
        
        market_data = framework.get_live_market_data('AAPL')
        
        self.assertIsNotNone(market_data)
        self.assertEqual(market_data['symbol'], 'AAPL')
        self.assertEqual(market_data['price'], 150.0)
        mock_client.get_market_data.assert_called_once_with('AAPL')
    
    @patch('enhanced_trading.IBKRClientSync')
    def test_trade_execution(self, mock_client_class):
        """Test trade execution with mocked client"""
        mock_client = Mock()
        mock_client.is_connected.return_value = True
        mock_client.get_market_data.return_value = {'price': 150.0}
        mock_client.place_market_order.return_value = TradeResult(
            success=True,
            order_id=12345,
            filled_qty=100,
            avg_price=150.0,
            commission=1.0,
            error_message=None,
            timestamp=datetime.now()
        )
        mock_client_class.return_value = mock_client
        
        framework = EnhancedTradingFramework(
            symbols=self.symbols,
            initial_capital=50000,
            use_ibkr=True,
            config_manager=self.config_manager
        )
        
        # Mock the risk check to pass
        framework._check_risk_limits = Mock(return_value=True)
        
        result = framework.execute_trade('AAPL', 100, 'market')
        
        self.assertTrue(result.success)
        self.assertEqual(result.filled_qty, 100)
        self.assertEqual(result.avg_price, 150.0)
        mock_client.place_market_order.assert_called_once_with('AAPL', 100, 'BUY')


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestIBKRConfig,
        TestTradeResult,
        TestPortfolioPosition,
        TestConfigManager,
        TestEnhancedTradingFramework,
        TestConvenienceFunctions,
        TestMockIBKRIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    if success:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)