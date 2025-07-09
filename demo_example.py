#!/usr/bin/env python3
"""
Example usage of the enhanced day trading strategies framework

This script demonstrates how to use the new features including:
- New trading strategies
- Voting mechanism
- Strategy comparison
- Out-of-sample validation
"""

from script import MultiSymbolDayTradingAlgo
import pandas as pd
import numpy as np

def create_demo_data():
    """Create demo data for the example"""
    print("Creating demo data...")
    
    # Create a trader with demo data
    trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT'], initial_capital=50000)
    
    # Generate synthetic data for demonstration
    dates = pd.date_range('2024-01-01', periods=500, freq='5min')
    
    for i, symbol in enumerate(['AAPL', 'MSFT']):
        np.random.seed(42 + i)
        
        # Generate realistic price movements
        returns = np.random.normal(0.0002, 0.015, 500)
        close_prices = 150 * (1 + returns).cumprod()
        
        # Generate high/low prices
        high_prices = close_prices * (1 + np.random.uniform(0, 0.01, 500))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.01, 500))
        
        # Generate volumes
        volumes = np.random.randint(1000, 50000, 500)
        
        trader.data[symbol] = pd.DataFrame({
            'Close': close_prices,
            'High': high_prices,
            'Low': low_prices,
            'Volume': volumes
        }, index=dates)
    
    return trader

def demo_new_strategies():
    """Demonstrate the new trading strategies"""
    print("\n" + "="*60)
    print("DEMO: New Trading Strategies")
    print("="*60)
    
    trader = create_demo_data()
    trader.calculate_indicators()
    
    # Test each new strategy
    new_strategies = {
        'breakout': 'Breakout Trading',
        'range': 'Range Trading',
        'vwap': 'VWAP Trading',
        'news_based': 'News-Based Trading'
    }
    
    for strategy_key, strategy_name in new_strategies.items():
        print(f"\nTesting {strategy_name}...")
        
        try:
            trader.backtest_strategy(strategy_key)
            metrics = trader.calculate_metrics()
            
            print(f"✓ {strategy_name} Results:")
            print(f"  Total Return: {metrics['Total Return (%)']}%")
            print(f"  Sharpe Ratio: {metrics['Sharpe Ratio']:.2f}")
            print(f"  Win Rate: {metrics['Win Rate (%)']}%")
            print(f"  Max Drawdown: {metrics['Maximum Drawdown (%)']}%")
            
        except Exception as e:
            print(f"✗ {strategy_name} failed: {e}")

def demo_voting_mechanism():
    """Demonstrate the voting mechanism"""
    print("\n" + "="*60)
    print("DEMO: Voting Mechanism vs Legacy Combined Strategy")
    print("="*60)
    
    trader = create_demo_data()
    trader.calculate_indicators()
    
    # Test voting mechanism
    print("\nTesting Voting Mechanism...")
    trader.backtest_strategy('combined')
    voting_metrics = trader.calculate_metrics()
    
    # Test legacy combined strategy
    print("Testing Legacy Combined Strategy...")
    trader.backtest_strategy('combined_legacy')
    legacy_metrics = trader.calculate_metrics()
    
    # Compare results
    print("\nComparison Results:")
    print(f"Voting Mechanism:")
    print(f"  Return: {voting_metrics['Total Return (%)']}%")
    print(f"  Sharpe: {voting_metrics['Sharpe Ratio']:.2f}")
    print(f"  Win Rate: {voting_metrics['Win Rate (%)']}%")
    
    print(f"\nLegacy Approach:")
    print(f"  Return: {legacy_metrics['Total Return (%)']}%")
    print(f"  Sharpe: {legacy_metrics['Sharpe Ratio']:.2f}")
    print(f"  Win Rate: {legacy_metrics['Win Rate (%)']}%")
    
    # Determine winner
    if voting_metrics['Total Return (%)'] > legacy_metrics['Total Return (%)']:
        print("\n🎉 Voting mechanism performed better!")
    else:
        print("\n📊 Legacy approach performed better this time.")

def demo_strategy_comparison():
    """Demonstrate strategy comparison"""
    print("\n" + "="*60)
    print("DEMO: Strategy Comparison")
    print("="*60)
    
    trader = create_demo_data()
    trader.calculate_indicators()
    
    # Run all strategies
    print("Running all strategies...")
    comparison_results = trader.run_all_strategies()
    
    if comparison_results is not None:
        print("\nTop 5 Strategies by Total Return:")
        sorted_strategies = comparison_results.sort_values('Total Return (%)', ascending=False)
        
        for i, (strategy, metrics) in enumerate(sorted_strategies.head(5).iterrows()):
            print(f"{i+1}. {strategy.upper()}")
            print(f"   Return: {metrics['Total Return (%)']}%")
            print(f"   Sharpe: {metrics['Sharpe Ratio']:.2f}")
            print(f"   Win Rate: {metrics['Win Rate (%)']}%")
            print()

def demo_validation():
    """Demonstrate out-of-sample validation"""
    print("\n" + "="*60)
    print("DEMO: Out-of-Sample Validation")
    print("="*60)
    
    trader = create_demo_data()
    trader.calculate_indicators()
    
    # Test validation for a few strategies
    strategies_to_test = ['momentum', 'vwap', 'combined']
    
    for strategy in strategies_to_test:
        print(f"\nValidating {strategy.upper()} strategy...")
        
        try:
            validation_results = trader.validate_out_of_sample(strategy, train_ratio=0.7)
            
            if validation_results:
                print(f"✓ Validation completed for {strategy}")
                
                for symbol, results in validation_results.items():
                    if results['train_metrics'] and results['test_metrics']:
                        train_return = results['train_metrics']['Total Return (%)']
                        test_return = results['test_metrics']['Total Return (%)']
                        consistency = "Good" if abs(train_return - test_return) < 15 else "Poor"
                        
                        print(f"  {symbol}: Train {train_return:.2f}%, Test {test_return:.2f}% ({consistency})")
                        
        except Exception as e:
            print(f"✗ Validation failed for {strategy}: {e}")

def demo_technical_indicators():
    """Demonstrate new technical indicators"""
    print("\n" + "="*60)
    print("DEMO: New Technical Indicators")
    print("="*60)
    
    trader = create_demo_data()
    trader.calculate_indicators()
    
    # Show sample of new indicators
    symbol = 'AAPL'
    df = trader.data[symbol]
    
    print(f"Sample of new indicators for {symbol}:")
    print(f"VWAP: {df['VWAP'].dropna().tail(3).tolist()}")
    print(f"Support: {df['Support'].dropna().tail(3).tolist()}")
    print(f"Resistance: {df['Resistance'].dropna().tail(3).tolist()}")
    print(f"ATR: {df['ATR'].dropna().tail(3).tolist()}")
    
    # Show how indicators are used
    print(f"\nIndicator Usage Example:")
    print(f"Current Price: ${df['Close'].iloc[-1]:.2f}")
    print(f"Current VWAP: ${df['VWAP'].iloc[-1]:.2f}")
    print(f"Support Level: ${df['Support'].iloc[-1]:.2f}")
    print(f"Resistance Level: ${df['Resistance'].iloc[-1]:.2f}")
    
    if df['Close'].iloc[-1] > df['VWAP'].iloc[-1]:
        print("📈 Price is above VWAP (potentially bullish)")
    else:
        print("📉 Price is below VWAP (potentially bearish)")

def main():
    """Main demonstration function"""
    print("Enhanced Day Trading Strategies Framework - Demo")
    print("="*60)
    print("This demo showcases the new features and capabilities")
    print("using synthetic data for demonstration purposes.")
    
    # Run all demonstrations
    demo_new_strategies()
    demo_voting_mechanism()
    demo_strategy_comparison()
    demo_validation()
    demo_technical_indicators()
    
    print("\n" + "="*60)
    print("Demo completed! 🎉")
    print("="*60)
    print("\nTo use with real data, replace the demo data creation with:")
    print("  trader.fetch_data_alternative(period='5d', interval='5m')")
    print("\nFor more information, see DOCUMENTATION.md")

if __name__ == "__main__":
    main()