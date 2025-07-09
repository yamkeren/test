#!/usr/bin/env python3
"""
Demo script for the Enhanced Trading Framework with IBKR Integration

This script demonstrates:
1. Setting up the enhanced trading framework
2. Using configuration management
3. Backtesting with historical data
4. Real-time data fetching (simulated)
5. Portfolio management
6. Risk management features
7. IBKR integration (when TWS is available)
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Import the enhanced trading framework
from enhanced_trading import EnhancedTradingFramework, create_enhanced_trader
from config_manager import ConfigManager, get_config
from ibkr_client import IBKRConfig

def demo_basic_setup():
    """Demonstrate basic setup of enhanced trading framework"""
    print("=" * 60)
    print("DEMO 1: Basic Setup and Configuration")
    print("=" * 60)
    
    # Get configuration manager
    config = get_config()
    
    # Show current configuration
    print("\nCurrent Configuration:")
    print(f"Data Source: {config.trading_config.data_source}")
    print(f"Initial Capital: ${config.trading_config.initial_capital:,}")
    print(f"Max Position Size: {config.trading_config.max_position_size:.1%}")
    print(f"Stop Loss: {config.trading_config.stop_loss_pct:.1%}")
    print(f"Take Profit: {config.trading_config.take_profit_pct:.1%}")
    
    # Show IBKR configuration
    print(f"\nIBKR Configuration:")
    print(f"Host: {config.ibkr_credentials.host}")
    print(f"Port: {config.ibkr_credentials.port}")
    print(f"Paper Trading: {config.ibkr_credentials.paper_trading}")
    
    # Create sample environment file
    config.create_sample_env_file()
    print("\n✓ Sample .env file created")
    
    # Validate configuration
    if config.validate_config():
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration validation failed")


def demo_data_fetching():
    """Demonstrate data fetching with fallback"""
    print("\n" + "=" * 60)
    print("DEMO 2: Data Fetching with Fallback")
    print("=" * 60)
    
    # Create enhanced trader
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    trader = create_enhanced_trader(symbols, use_ibkr=False, initial_capital=100000)
    
    print(f"\nFetching data for symbols: {symbols}")
    
    # Try to fetch data (will use yfinance since IBKR is not connected)
    success = trader.fetch_data_enhanced(period='5d', interval='15m')
    
    if success:
        print(f"✓ Successfully fetched data for {len(trader.data)} symbols")
        
        # Show data summary
        for symbol, data in trader.data.items():
            print(f"  {symbol}: {len(data)} data points, "
                  f"from {data.index[0]} to {data.index[-1]}")
    else:
        print("✗ Failed to fetch data")
    
    return trader


def demo_backtesting():
    """Demonstrate backtesting capabilities"""
    print("\n" + "=" * 60)
    print("DEMO 3: Backtesting and Strategy Comparison")
    print("=" * 60)
    
    # Create trader with test data
    symbols = ['AAPL', 'MSFT']
    trader = create_enhanced_trader(symbols, use_ibkr=False, initial_capital=50000)
    
    # Create synthetic test data
    dates = pd.date_range('2024-01-01', periods=500, freq='5min')
    
    for i, symbol in enumerate(symbols):
        np.random.seed(42 + i)
        returns = np.random.normal(0.0002, 0.015, 500)
        prices = 150 * (1 + returns).cumprod()
        
        trader.data[symbol] = pd.DataFrame({
            'Open': prices * 0.999,
            'High': prices * 1.001,
            'Low': prices * 0.998,
            'Close': prices,
            'Volume': np.random.randint(1000, 50000, 500)
        }, index=dates)
    
    print(f"✓ Created synthetic data for {len(trader.data)} symbols")
    
    # Calculate indicators
    trader.calculate_indicators()
    print("✓ Calculated technical indicators")
    
    # Test different strategies
    strategies = ['momentum', 'mean_reversion', 'combined']
    results = {}
    
    for strategy in strategies:
        try:
            trader.backtest_strategy(strategy)
            metrics = trader.calculate_metrics()
            results[strategy] = metrics
            print(f"✓ Backtested {strategy} strategy")
        except Exception as e:
            print(f"✗ Failed to backtest {strategy}: {e}")
    
    # Show strategy comparison
    if results:
        print("\nStrategy Performance Comparison:")
        print("-" * 50)
        for strategy, metrics in results.items():
            print(f"{strategy:15} | Return: {metrics.get('Total Return (%)', 0):6.2f}% | "
                  f"Sharpe: {metrics.get('Sharpe Ratio', 0):5.2f}")
    
    return trader


def demo_portfolio_management():
    """Demonstrate portfolio management features"""
    print("\n" + "=" * 60)
    print("DEMO 4: Portfolio Management")
    print("=" * 60)
    
    # Create trader
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    trader = create_enhanced_trader(symbols, use_ibkr=False, initial_capital=100000)
    
    # Simulate some positions
    trader.positions = {
        'AAPL': 100,
        'MSFT': 200,
        'GOOGL': 50
    }
    trader.daily_pnl = 1250.0
    
    print("✓ Simulated portfolio positions")
    
    # Get portfolio summary
    portfolio_summary = trader.get_portfolio_summary()
    
    print(f"\nPortfolio Summary:")
    print(f"Account Value: ${portfolio_summary['account_value']:,.2f}")
    print(f"Cash: ${portfolio_summary['cash']:,.2f}")
    print(f"Realized P&L: ${portfolio_summary['realized_pnl']:,.2f}")
    print(f"Total Positions: {len(portfolio_summary['positions'])}")
    
    # Create portfolio dashboard
    dashboard = trader.create_portfolio_dashboard()
    print(f"\n✓ Created portfolio dashboard")
    print(dashboard.to_string(index=False))
    
    # Show position details
    if portfolio_summary['positions']:
        print(f"\nPosition Details:")
        for pos in portfolio_summary['positions']:
            print(f"  {pos['symbol']}: {pos['quantity']} shares")
    
    return trader


def demo_risk_management():
    """Demonstrate risk management features"""
    print("\n" + "=" * 60)
    print("DEMO 5: Risk Management")
    print("=" * 60)
    
    # Create trader
    trader = create_enhanced_trader(['AAPL'], use_ibkr=False, initial_capital=50000)
    
    # Mock market data for risk checks
    trader.get_live_market_data = lambda symbol: {'price': 150.0}
    
    print(f"Risk Management Settings:")
    print(f"Max Position Size: {trader.max_position_size:.1%}")
    print(f"Stop Loss: {trader.stop_loss_pct:.1%}")
    print(f"Take Profit: {trader.take_profit_pct:.1%}")
    print(f"Max Daily Loss: {trader.max_daily_loss:.1%}")
    
    # Test position size limits
    print(f"\nTesting Position Size Limits:")
    
    # Small position (should pass)
    small_quantity = 100  # $15,000 position (30% of portfolio)
    result1 = trader._check_risk_limits('AAPL', small_quantity)
    print(f"Small position (100 shares): {'✓ PASS' if result1 else '✗ FAIL'}")
    
    # Large position (should fail)
    large_quantity = 500  # $75,000 position (150% of portfolio)
    result2 = trader._check_risk_limits('AAPL', large_quantity)
    print(f"Large position (500 shares): {'✓ PASS' if result2 else '✗ FAIL'}")
    
    # Test daily loss limits
    print(f"\nTesting Daily Loss Limits:")
    
    # Set daily loss near limit
    trader.daily_pnl = -900  # -1.8% of $50,000
    result3 = trader._check_risk_limits('AAPL', 100)
    print(f"Daily loss -1.8%: {'✓ PASS' if result3 else '✗ FAIL'}")
    
    # Exceed daily loss limit
    trader.daily_pnl = -1200  # -2.4% of $50,000
    result4 = trader._check_risk_limits('AAPL', 100)
    print(f"Daily loss -2.4%: {'✓ PASS' if result4 else '✗ FAIL'}")
    
    return trader


def demo_ibkr_connection():
    """Demonstrate IBKR connection (if available)"""
    print("\n" + "=" * 60)
    print("DEMO 6: IBKR Connection (Optional)")
    print("=" * 60)
    
    # Create trader with IBKR enabled
    trader = create_enhanced_trader(['AAPL'], use_ibkr=True, initial_capital=50000)
    
    print("Attempting to connect to Interactive Brokers...")
    print("Note: This requires TWS or IB Gateway to be running")
    print("Default connection: localhost:7497 (paper trading)")
    
    # Try to connect
    try:
        connected = trader.connect_ibkr()
        if connected:
            print("✓ Successfully connected to IBKR")
            
            # Try to get market data
            print("\nTesting market data retrieval...")
            market_data = trader.get_live_market_data('AAPL')
            
            if market_data:
                print(f"✓ Live market data for AAPL:")
                print(f"  Price: ${market_data.get('price', 'N/A')}")
                print(f"  Bid: ${market_data.get('bid', 'N/A')}")
                print(f"  Ask: ${market_data.get('ask', 'N/A')}")
                print(f"  Volume: {market_data.get('volume', 'N/A')}")
            else:
                print("✗ Could not retrieve market data")
            
            # Try to get account summary
            print("\nTesting account summary...")
            try:
                account_summary = trader.ibkr_client.get_account_summary()
                if account_summary:
                    print("✓ Account summary retrieved:")
                    for key, value in account_summary.items():
                        print(f"  {key}: ${value:,.2f}")
                else:
                    print("✗ Could not retrieve account summary")
            except Exception as e:
                print(f"✗ Error getting account summary: {e}")
            
            # Disconnect
            trader.disconnect_ibkr()
            print("✓ Disconnected from IBKR")
            
        else:
            print("✗ Failed to connect to IBKR")
            print("Make sure TWS or IB Gateway is running")
            print("Check connection settings in configuration")
    
    except Exception as e:
        print(f"✗ Error connecting to IBKR: {e}")
    
    return trader


def demo_configuration_management():
    """Demonstrate configuration management"""
    print("\n" + "=" * 60)
    print("DEMO 7: Configuration Management")
    print("=" * 60)
    
    config = get_config()
    
    # Show current configuration
    print("Current Configuration:")
    current_config = config.get_config()
    
    print(f"\nTrading Settings:")
    for key, value in current_config['trading'].items():
        print(f"  {key}: {value}")
    
    print(f"\nIBKR Settings:")
    for key, value in current_config['ibkr'].items():
        print(f"  {key}: {value}")
    
    # Update configuration
    print(f"\nUpdating configuration...")
    config.update_trading_config(
        initial_capital=75000.0,
        max_position_size=0.15,
        stop_loss_pct=0.03
    )
    
    print(f"✓ Updated trading configuration")
    print(f"New initial capital: ${config.trading_config.initial_capital:,}")
    print(f"New max position size: {config.trading_config.max_position_size:.1%}")
    print(f"New stop loss: {config.trading_config.stop_loss_pct:.1%}")
    
    # Validate updated configuration
    if config.validate_config():
        print("✓ Updated configuration is valid")
    else:
        print("✗ Updated configuration validation failed")


def main():
    """Run all demos"""
    print("Enhanced Trading Framework with IBKR Integration")
    print("Demo Script - Comprehensive Feature Demonstration")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_setup()
        trader1 = demo_data_fetching()
        trader2 = demo_backtesting()
        trader3 = demo_portfolio_management()
        trader4 = demo_risk_management()
        trader5 = demo_ibkr_connection()
        demo_configuration_management()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("All demos completed successfully!")
        print("\nNext Steps:")
        print("1. Configure your IBKR connection settings")
        print("2. Start TWS or IB Gateway for live trading")
        print("3. Create your custom trading strategies")
        print("4. Set up risk management parameters")
        print("5. Start with paper trading before going live")
        
    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()