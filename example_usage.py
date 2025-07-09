#!/usr/bin/env python3
"""
Example usage of the Enhanced Day Trading Strategies Framework
This script demonstrates the key features and capabilities
"""

import sys
import os
sys.path.append('/home/runner/work/test/test')

from script import MultiSymbolDayTradingAlgo
import pandas as pd
import numpy as np

def main():
    """Main example demonstrating the trading framework"""
    
    print("🚀 Enhanced Day Trading Strategies Framework - Example Usage")
    print("=" * 60)
    
    # Initialize the trading algorithm with multiple symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    initial_capital = 50000
    
    print(f"Initializing trader with symbols: {symbols}")
    print(f"Initial capital: ${initial_capital:,}")
    
    trader = MultiSymbolDayTradingAlgo(symbols, initial_capital=initial_capital)
    
    # For demonstration, we'll use mock data since network access might be limited
    print("\n📊 Creating mock market data...")
    success = trader.create_mock_data(symbols, days=60, interval_minutes=5)
    
    if not success:
        print("❌ Failed to create mock data")
        return
    
    # Calculate technical indicators
    print("📈 Calculating technical indicators...")
    trader.calculate_indicators()
    
    # Show data summary
    print("\n📋 Market Data Summary:")
    summary = trader.get_symbol_summary()
    
    # Example 1: Test individual strategies
    print("\n" + "="*60)
    print("EXAMPLE 1: Testing Individual Strategies")
    print("="*60)
    
    individual_strategies = ['momentum', 'mean_reversion', 'breakout', 'vwap']
    
    for strategy in individual_strategies:
        print(f"\n🔍 Testing {strategy.upper()} Strategy")
        try:
            trader.backtest_strategy(strategy)
            metrics = trader.calculate_enhanced_metrics()
            
            print(f"  📊 Performance Metrics:")
            print(f"    • Total Return: {metrics['Total Return (%)']}%")
            print(f"    • Sharpe Ratio: {metrics['Sharpe Ratio']}")
            print(f"    • Win Rate: {metrics['Win Rate (%)']}%")
            print(f"    • Max Drawdown: {metrics['Maximum Drawdown (%)']}%")
            print(f"    • Profit Factor: {metrics['Profit Factor']}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Example 2: Comprehensive strategy comparison
    print("\n" + "="*60)
    print("EXAMPLE 2: Comprehensive Strategy Comparison")
    print("="*60)
    
    print("🏆 Running all strategies and comparing performance...")
    comparison = trader.run_all_strategies()
    
    if comparison is not None:
        print("\n📊 Strategy Ranking by Total Return:")
        top_strategies = comparison.nlargest(5, 'Total Return (%)')
        
        for i, (strategy, row) in enumerate(top_strategies.iterrows(), 1):
            print(f"  {i}. {strategy.upper()}")
            print(f"     Return: {row['Total Return (%)']}%")
            print(f"     Sharpe: {row['Sharpe Ratio']}")
            print(f"     Drawdown: {row['Maximum Drawdown (%)']}%")
    
    # Example 3: Voting mechanism
    print("\n" + "="*60)
    print("EXAMPLE 3: Voting Mechanism")
    print("="*60)
    
    print("🗳️  Testing voting strategy (majority voting across all strategies)...")
    try:
        trader.backtest_strategy('voting')
        voting_metrics = trader.calculate_enhanced_metrics()
        
        print(f"📊 Voting Strategy Results:")
        print(f"  • Total Return: {voting_metrics['Total Return (%)']}%")
        print(f"  • Sharpe Ratio: {voting_metrics['Sharpe Ratio']}")
        print(f"  • Win Rate: {voting_metrics['Win Rate (%)']}%")
        print(f"  • Information Ratio: {voting_metrics['Information Ratio']}")
        
    except Exception as e:
        print(f"❌ Voting strategy error: {e}")
    
    # Example 4: Parameter optimization
    print("\n" + "="*60)
    print("EXAMPLE 4: Parameter Optimization")
    print("="*60)
    
    print("🔧 Optimizing mean reversion strategy parameters...")
    
    # Define parameter grid for optimization
    param_grid = {
        'rsi_oversold': [20, 25, 30],
        'rsi_overbought': [70, 75, 80],
        'bb_std': [1.5, 2.0, 2.5]
    }
    
    try:
        optimization_results = trader.optimize_strategy_parameters(
            'mean_reversion', 'AAPL', param_grid, 'Sharpe Ratio'
        )
        
        if optimization_results and optimization_results['best_params']:
            print(f"🎯 Best parameters found:")
            for param, value in optimization_results['best_params'].items():
                print(f"  • {param}: {value}")
            
            best_metrics = optimization_results['best_metrics']
            print(f"📊 Best performance:")
            print(f"  • Sharpe Ratio: {best_metrics['Sharpe Ratio']}")
            print(f"  • Total Return: {best_metrics['Total Return (%)']}%")
            
    except Exception as e:
        print(f"❌ Parameter optimization error: {e}")
    
    # Example 5: Out-of-sample validation
    print("\n" + "="*60)
    print("EXAMPLE 5: Out-of-Sample Validation")
    print("="*60)
    
    print("📊 Validating momentum strategy on out-of-sample data...")
    try:
        validation_results = trader.validate_strategy_out_of_sample(
            'momentum', train_ratio=0.7
        )
        
        if validation_results:
            print("📈 Validation Results:")
            for symbol, results in validation_results.items():
                train_return = results['train_metrics']['Total Return (%)']
                test_return = results['test_metrics']['Total Return (%)']
                
                print(f"  {symbol}:")
                print(f"    • Training Return: {train_return}%")
                print(f"    • Test Return: {test_return}%")
                print(f"    • Generalization: {'✓' if test_return > -20 else '⚠️'}")
                
    except Exception as e:
        print(f"❌ Validation error: {e}")
    
    # Example 6: Individual strategy backtesting
    print("\n" + "="*60)
    print("EXAMPLE 6: Batch Individual Strategy Testing")
    print("="*60)
    
    print("🔄 Running individual backtests for all strategies...")
    try:
        individual_results = trader.backtest_individual_strategies()
        
        if individual_results:
            print("📊 Individual Strategy Summary:")
            
            # Sort by Sharpe ratio
            sorted_strategies = sorted(
                individual_results.items(),
                key=lambda x: x[1]['Sharpe Ratio'],
                reverse=True
            )
            
            for strategy, metrics in sorted_strategies:
                print(f"  {strategy.upper()}:")
                print(f"    Return: {metrics['Total Return (%)']}%")
                print(f"    Sharpe: {metrics['Sharpe Ratio']}")
                print(f"    Trades: {metrics['Number of Trades']}")
                
    except Exception as e:
        print(f"❌ Individual backtesting error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("🎉 EXAMPLE COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    print("✅ Framework Features Demonstrated:")
    print("   • Multiple trading strategies (momentum, mean reversion, breakout, etc.)")
    print("   • Comprehensive performance metrics")
    print("   • Voting mechanism for strategy combination")
    print("   • Parameter optimization")
    print("   • Out-of-sample validation")
    print("   • Individual strategy backtesting")
    
    print("\n📝 Next Steps:")
    print("   • Try with real market data using fetch_data_alternative()")
    print("   • Experiment with different parameter combinations")
    print("   • Add custom strategies following the existing pattern")
    print("   • Use the framework for live trading analysis")
    
    print("\n⚠️  Remember: This is for educational purposes only.")
    print("   Always backtest thoroughly before using real capital!")

if __name__ == "__main__":
    main()