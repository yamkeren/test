# Enhanced Day Trading Strategies and Backtesting Framework

This repository contains a comprehensive day trading strategies and backtesting framework with multiple trading strategies, performance metrics, and optimization capabilities.

## Features

### Day Trading Strategies

1. **Momentum Trading**: Identifies upward or downward trends using moving averages and MACD
2. **Mean Reversion**: Trades based on overbought/oversold conditions using Bollinger Bands and RSI
3. **Breakout Trading**: Buys when price crosses resistance or sells when it breaks support
4. **Range Trading**: Trades within price ranges based on support and resistance levels
5. **News-Based Trading**: Incorporates volume and volatility spikes as news event proxies
6. **VWAP Trading**: Uses Volume Weighted Average Price to guide buy/sell decisions
7. **Voting Strategy**: Combines multiple strategies using majority voting mechanism

### Backtesting Framework

- **Individual Strategy Backtesting**: Test each strategy independently
- **Enhanced Performance Metrics**: 
  - Win rate, profitability, Sharpe ratio, maximum drawdown
  - Calmar ratio, Sortino ratio, Information ratio
  - Profit factor, Win/Loss ratio, Expectancy
- **Multi-Symbol Support**: Trade multiple symbols simultaneously
- **Portfolio-Level Analysis**: Aggregate performance across symbols

### Advanced Features

- **Parameter Optimization**: Grid search for optimal strategy parameters
- **Out-of-Sample Validation**: Test strategies on unseen data
- **Voting Mechanism**: Majority voting across multiple strategies
- **Risk Management**: Comprehensive risk metrics and drawdown analysis
- **Mock Data Generation**: Testing functionality when market data is unavailable

## Installation

```bash
pip install yfinance pandas numpy matplotlib seaborn
```

## Quick Start

```python
from script import MultiSymbolDayTradingAlgo

# Initialize with symbols and capital
trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT'], initial_capital=10000)

# Fetch market data
trader.fetch_data_alternative(period='5d', interval='5m')

# Calculate technical indicators
trader.calculate_indicators()

# Run all strategies and compare
comparison = trader.run_all_strategies()

# Test individual strategies
trader.backtest_strategy('momentum')
metrics = trader.calculate_enhanced_metrics()
```

## Strategy Details

### 1. Momentum Trading Strategy
- **Indicators**: Moving averages (SMA_5, SMA_10), MACD, Volume ratio
- **Buy Signal**: Fast MA > Slow MA AND MACD > Signal AND Volume > 1.2x average
- **Sell Signal**: Fast MA < Slow MA OR MACD < Signal

### 2. Mean Reversion Strategy
- **Indicators**: Bollinger Bands, RSI
- **Buy Signal**: Price ≤ Lower BB AND RSI < 30 (oversold)
- **Sell Signal**: Price ≥ Upper BB AND RSI > 70 (overbought)

### 3. Breakout Trading Strategy
- **Indicators**: Rolling resistance/support levels, Volume, Momentum
- **Buy Signal**: Price > Resistance AND Volume > 1.5x average AND Momentum > 1%
- **Sell Signal**: Price < Support OR RSI > 80

### 4. Range Trading Strategy
- **Indicators**: Dynamic support/resistance levels, RSI
- **Buy Signal**: Price near support (within 2%) AND RSI < 40
- **Sell Signal**: Price near resistance (within 2%) AND RSI > 60

### 5. VWAP Trading Strategy
- **Indicators**: Volume Weighted Average Price, VWAP bands
- **Buy Signal**: Price < VWAP AND above lower band AND Volume > 1.2x average
- **Sell Signal**: Price > VWAP OR price > upper band

### 6. News-Based Trading Strategy
- **Indicators**: Volume anomalies, Volatility spikes
- **Buy Signal**: Volume Z-score > 2 AND Volatility Z-score > 1.5 AND positive price change
- **Sell Signal**: Volume Z-score > 2 AND Volatility Z-score > 1.5 AND negative price change

### 7. Voting Strategy
- **Mechanism**: Collects signals from all individual strategies
- **Buy Signal**: Majority of strategies vote buy (>50%)
- **Sell Signal**: Majority of strategies vote sell (>50%)

## Performance Metrics

### Basic Metrics
- **Total Return (%)**: Overall strategy performance
- **Buy & Hold Return (%)**: Benchmark comparison
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown (%)**: Largest peak-to-trough decline
- **Win Rate (%)**: Percentage of profitable trades

### Enhanced Metrics
- **Calmar Ratio**: Annualized return / Maximum drawdown
- **Sortino Ratio**: Downside risk-adjusted returns
- **Information Ratio**: Active return / Tracking error
- **Profit Factor**: Total profits / Total losses
- **Win/Loss Ratio**: Average win / Average loss

## Usage Examples

### Individual Strategy Testing
```python
# Test momentum strategy
trader.backtest_strategy('momentum')
metrics = trader.calculate_enhanced_metrics()
print(f"Sharpe Ratio: {metrics['Sharpe Ratio']}")
```

### Parameter Optimization
```python
# Optimize mean reversion parameters
param_grid = {
    'rsi_oversold': [20, 25, 30],
    'rsi_overbought': [70, 75, 80],
    'bb_std': [1.5, 2.0, 2.5]
}
results = trader.optimize_strategy_parameters('mean_reversion', 'AAPL', param_grid)
```

### Out-of-Sample Validation
```python
# Validate strategy on unseen data
validation_results = trader.validate_strategy_out_of_sample('momentum', train_ratio=0.7)
```

### Comprehensive Comparison
```python
# Compare all strategies
comparison = trader.run_all_strategies()
best_strategy = comparison['Total Return (%)'].idxmax()
```

## Testing

Run the comprehensive test suite:

```bash
python /tmp/comprehensive_test.py
```

This will test all strategies, metrics, and optimization features using mock data.

## Architecture

The framework is built around the `MultiSymbolDayTradingAlgo` class with the following key components:

- **Data Management**: Handles fetching, storing, and processing market data
- **Strategy Engine**: Implements individual trading strategies
- **Backtesting Engine**: Simulates trading and calculates performance
- **Metrics Calculator**: Computes comprehensive performance metrics
- **Optimization Engine**: Parameter tuning and validation
- **Visualization**: Plotting and analysis tools

## Contributing

When adding new strategies:

1. Implement the strategy method following the existing pattern
2. Add the strategy to the `strategy_functions` dictionary
3. Update the `run_all_strategies` method
4. Add comprehensive documentation
5. Include unit tests

## Risk Disclaimer

This is for educational and research purposes only. Past performance does not guarantee future results. Always test strategies thoroughly before using real capital.

## License

This project is open source and available under the MIT License.