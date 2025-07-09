#!/usr/bin/env python3
"""
Test script for the enhanced day trading strategies and backtesting framework
"""

import sys
import pandas as pd
import numpy as np
from script import MultiSymbolDayTradingAlgo

def create_test_data():
    """Create synthetic test data for validation"""
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    dates = pd.date_range('2024-01-01', periods=200, freq='5min')
    
    test_data = {}
    
    for i, symbol in enumerate(symbols):
        np.random.seed(42 + i)  # Different seed for each symbol
        
        # Generate realistic price movements
        returns = np.random.normal(0.0001, 0.02, 200)
        close_prices = 100 * (1 + returns).cumprod()
        
        # Generate high/low prices
        high_prices = close_prices * (1 + np.random.uniform(0, 0.02, 200))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.02, 200))
        
        # Generate volumes with some pattern
        volumes = np.random.randint(1000, 10000, 200)
        
        test_data[symbol] = pd.DataFrame({
            'Close': close_prices,
            'High': high_prices,
            'Low': low_prices,
            'Volume': volumes
        }, index=dates)
    
    return test_data

def test_new_strategies():
    """Test all new strategies"""
    print("Testing New Strategies...")
    print("=" * 50)
    
    # Initialize trader with test data
    trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT', 'GOOGL'], initial_capital=50000)
    trader.data = create_test_data()
    
    # Calculate indicators
    trader.calculate_indicators()
    
    # Test each new strategy
    new_strategies = ['breakout', 'range', 'vwap', 'news_based']
    
    for strategy in new_strategies:
        print(f"\nTesting {strategy} strategy...")
        try:
            trader.backtest_strategy(strategy)
            metrics = trader.calculate_metrics()
            
            if metrics:
                print(f"✓ {strategy} strategy successful")
                print(f"  Total Return: {metrics['Total Return (%)']}%")
                print(f"  Sharpe Ratio: {metrics['Sharpe Ratio']}")
                print(f"  Win Rate: {metrics['Win Rate (%)']}%")
                print(f"  Max Drawdown: {metrics['Maximum Drawdown (%)']}%")
            else:
                print(f"✗ {strategy} strategy failed - no metrics")
        except Exception as e:
            print(f"✗ {strategy} strategy failed: {e}")
    
    return trader

def test_voting_mechanism():
    """Test the voting mechanism in combined strategy"""
    print("\n\nTesting Voting Mechanism...")
    print("=" * 50)
    
    trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT'], initial_capital=30000)
    trader.data = create_test_data()
    trader.calculate_indicators()
    
    try:
        # Test voting-based combined strategy
        trader.backtest_strategy('combined')
        voting_metrics = trader.calculate_metrics()
        
        # Test legacy combined strategy
        trader.backtest_strategy('combined_legacy')
        legacy_metrics = trader.calculate_metrics()
        
        print("✓ Voting mechanism successful")
        print(f"  Voting Strategy Return: {voting_metrics['Total Return (%)']}%")
        print(f"  Legacy Strategy Return: {legacy_metrics['Total Return (%)']}%")
        
        # Compare performance
        if voting_metrics['Total Return (%)'] > legacy_metrics['Total Return (%)']:
            print("  🎉 Voting mechanism outperformed legacy approach")
        else:
            print("  📊 Legacy approach performed better this time")
            
    except Exception as e:
        print(f"✗ Voting mechanism failed: {e}")

def test_strategy_comparison():
    """Test running all strategies and comparing results"""
    print("\n\nTesting Strategy Comparison...")
    print("=" * 50)
    
    trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT'], initial_capital=30000)
    trader.data = create_test_data()
    trader.calculate_indicators()
    
    try:
        # Run all strategies
        comparison_results = trader.run_all_strategies()
        
        if comparison_results is not None:
            print("✓ Strategy comparison successful")
            print("\nTop 3 strategies by total return:")
            
            # Sort by total return
            sorted_strategies = comparison_results.sort_values('Total Return (%)', ascending=False)
            for i, (strategy, metrics) in enumerate(sorted_strategies.head(3).iterrows()):
                print(f"  {i+1}. {strategy}: {metrics['Total Return (%)']}%")
        else:
            print("✗ Strategy comparison failed")
            
    except Exception as e:
        print(f"✗ Strategy comparison failed: {e}")

def test_validation():
    """Test out-of-sample validation"""
    print("\n\nTesting Out-of-Sample Validation...")
    print("=" * 50)
    
    trader = MultiSymbolDayTradingAlgo(['AAPL'], initial_capital=20000)
    trader.data = create_test_data()
    trader.calculate_indicators()
    
    try:
        # Test validation for momentum strategy
        validation_results = trader.validate_out_of_sample('momentum', train_ratio=0.6)
        
        if validation_results:
            print("✓ Out-of-sample validation successful")
            
            for symbol, results in validation_results.items():
                if results['train_metrics'] and results['test_metrics']:
                    train_return = results['train_metrics']['Total Return (%)']
                    test_return = results['test_metrics']['Total Return (%)']
                    print(f"  {symbol}: Train {train_return}%, Test {test_return}%")
        else:
            print("✗ Out-of-sample validation failed")
            
    except Exception as e:
        print(f"✗ Out-of-sample validation failed: {e}")

def test_indicators():
    """Test new technical indicators"""
    print("\n\nTesting New Technical Indicators...")
    print("=" * 50)
    
    trader = MultiSymbolDayTradingAlgo(['AAPL'], initial_capital=10000)
    trader.data = create_test_data()
    trader.calculate_indicators()
    
    # Check if new indicators are calculated
    df = trader.data['AAPL']
    new_indicators = ['VWAP', 'Support', 'Resistance', 'ATR']
    
    for indicator in new_indicators:
        if indicator in df.columns:
            print(f"✓ {indicator} indicator calculated successfully")
            print(f"  Sample values: {df[indicator].dropna().head(3).tolist()}")
        else:
            print(f"✗ {indicator} indicator missing")

def main():
    """Main test function"""
    print("Enhanced Day Trading Strategies - Comprehensive Test")
    print("=" * 60)
    
    # Run all tests
    test_new_strategies()
    test_voting_mechanism()
    test_strategy_comparison()
    test_validation()
    test_indicators()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()