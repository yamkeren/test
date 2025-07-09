# Enhanced Day Trading Strategies and Backtesting Framework

## Overview

This repository contains an enhanced multi-symbol day trading algorithm framework with comprehensive backtesting capabilities. The framework includes multiple trading strategies, a voting mechanism for combined decision-making, and tools for strategy optimization and validation.

## New Features

### 1. Additional Trading Strategies

The framework now includes the following new strategies:

#### Breakout Trading Strategy
- **Purpose**: Identify and trade price breakouts above resistance or below support levels
- **Logic**: 
  - Buy when price crosses above resistance with volume confirmation
  - Sell when price breaks below support or RSI becomes overbought
- **Key Indicators**: Support/Resistance levels, Volume ratio, RSI
- **Usage**: `trader.backtest_strategy('breakout')`

#### Range Trading Strategy
- **Purpose**: Trade within established price ranges based on support and resistance
- **Logic**:
  - Buy near support when RSI is oversold
  - Sell near resistance when RSI is overbought
- **Key Indicators**: Dynamic support/resistance, RSI, Volume ratio
- **Usage**: `trader.backtest_strategy('range')`

#### VWAP Trading Strategy
- **Purpose**: Use Volume Weighted Average Price to guide trading decisions
- **Logic**:
  - Buy when price is below VWAP with upward momentum
  - Sell when price is above VWAP with weakening momentum
- **Key Indicators**: VWAP, Moving averages, Volume ratio, RSI
- **Usage**: `trader.backtest_strategy('vwap')`

#### News-Based Trading Strategy
- **Purpose**: Incorporate trading decisions based on market sentiment indicators
- **Logic**:
  - Uses volatility and volume spikes as proxies for news impact
  - Buy on positive momentum with high volume
  - Sell on negative momentum or high volatility
- **Key Indicators**: Volatility spikes, Volume ratio, Price momentum, MACD
- **Usage**: `trader.backtest_strategy('news_based')`

### 2. Enhanced Combined Strategy with Voting Mechanism

The new combined strategy uses a majority voting system instead of the previous score-based approach:

#### How It Works
1. **Individual Strategy Votes**: Each strategy (mean_reversion, momentum, breakout, range, vwap, news_based) votes for buy (1), sell (-1), or hold (0)
2. **Majority Decision**: The final signal is determined by majority vote
3. **Threshold**: More than 50% of strategies must agree for an action to be taken

#### Benefits
- More robust decision-making
- Reduces false signals from individual strategies
- Maintains the legacy approach for comparison

```python
# Use new voting mechanism
trader.backtest_strategy('combined')

# Compare with legacy approach
trader.backtest_strategy('combined_legacy')
```

### 3. New Technical Indicators

#### VWAP (Volume Weighted Average Price)
- Calculates the average price weighted by volume
- Helps identify fair value and potential support/resistance levels

#### Dynamic Support and Resistance
- Automatically calculates support and resistance levels based on recent price action
- Updates continuously as new data becomes available

#### ATR (Average True Range)
- Measures market volatility
- Useful for setting stop-losses and position sizing

### 4. Optimization and Validation Tools

#### Parameter Optimization
```python
# Define parameter grid for testing
param_grid = {
    'rsi_period': [14, 21, 28],
    'bb_period': [20, 30, 40],
    'volume_threshold': [1.2, 1.5, 2.0]
}

# Optimize strategy parameters
results = trader.optimize_strategy_parameters('momentum', param_grid)
```

#### Out-of-Sample Validation
```python
# Validate strategy on unseen data
validation_results = trader.validate_out_of_sample('momentum', train_ratio=0.7)
```

## Usage Examples

### Basic Usage
```python
from script import MultiSymbolDayTradingAlgo

# Initialize with symbols and capital
trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT', 'GOOGL'], initial_capital=50000)

# Fetch real market data
trader.fetch_data_alternative(period='5d', interval='5m')

# Calculate technical indicators
trader.calculate_indicators()

# Test individual strategies
trader.backtest_strategy('breakout')
trader.backtest_strategy('vwap')
trader.backtest_strategy('combined')

# Get performance metrics
metrics = trader.calculate_metrics()
print(f"Total Return: {metrics['Total Return (%)']}%")
print(f"Sharpe Ratio: {metrics['Sharpe Ratio']}")
```

### Strategy Comparison
```python
# Run all strategies and compare performance
comparison_results = trader.run_all_strategies()

# Find best performing strategy
best_strategy = comparison_results['Total Return (%)'].idxmax()
print(f"Best strategy: {best_strategy}")
```

### Validation and Optimization
```python
# Validate strategy robustness
validation_results = trader.validate_out_of_sample('momentum')

# Optimize parameters (framework provided, specific implementation needed)
param_grid = {'param1': [1, 2, 3], 'param2': [0.1, 0.2, 0.3]}
optimization_results = trader.optimize_strategy_parameters('momentum', param_grid)
```

## Strategy Performance Metrics

The framework calculates comprehensive performance metrics for each strategy:

- **Total Return (%)**: Overall return of the strategy
- **Buy & Hold Return (%)**: Benchmark return for comparison
- **Strategy Volatility (%)**: Annualized volatility of returns
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown (%)**: Largest peak-to-trough decline
- **Win Rate (%)**: Percentage of profitable trades
- **Final Portfolio Value**: Ending value of the portfolio

## Testing

Run the comprehensive test suite:
```bash
python test_enhancements.py
```

This will test:
- All new trading strategies
- Voting mechanism functionality
- Strategy comparison
- Out-of-sample validation
- Technical indicator calculations

## Architecture

The framework is built around the `MultiSymbolDayTradingAlgo` class with the following key components:

1. **Data Management**: Handles fetching and storing market data
2. **Technical Indicators**: Calculates various technical indicators
3. **Strategy Methods**: Individual strategy implementations
4. **Backtesting Engine**: Simulates trading and calculates performance
5. **Optimization Tools**: Parameter tuning and validation
6. **Visualization**: Plotting and analysis tools

## Future Enhancements

- Real-time news integration for news-based strategy
- Machine learning-based strategy optimization
- Risk management improvements
- Additional technical indicators
- Performance attribution analysis

## Dependencies

- yfinance: Market data retrieval
- pandas: Data manipulation
- numpy: Numerical computations
- matplotlib: Visualization
- seaborn: Statistical plotting

## Contributing

When adding new strategies:
1. Follow the existing pattern of returning a DataFrame with 'signal' column
2. Use buy (1), sell (-1), hold (0) signals
3. Add strategy to the `strategy_functions` dictionary
4. Update the `run_all_strategies` method
5. Add comprehensive tests