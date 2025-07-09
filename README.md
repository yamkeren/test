# Enhanced Day Trading Strategies Framework

A comprehensive multi-symbol day trading algorithm framework with advanced backtesting capabilities, multiple trading strategies, and a sophisticated voting mechanism for decision-making.

## 🚀 Features

### Trading Strategies
- **Mean Reversion**: Bollinger Bands + RSI
- **Momentum**: Moving averages + MACD
- **Breakout**: Price breakouts with volume confirmation
- **Range Trading**: Support/resistance based trading
- **VWAP Trading**: Volume-weighted average price strategy
- **News-Based**: Volatility and volume spike analysis
- **Sector Rotation**: Relative strength analysis
- **Pairs Trading**: Statistical arbitrage
- **Multi-Timeframe**: Trend alignment across timeframes
- **Combined Strategy**: Majority voting mechanism

### Advanced Features
- 📊 **Independent Backtesting**: Test each strategy individually
- 🗳️ **Voting Mechanism**: Combined strategy using majority voting
- 🔧 **Parameter Optimization**: Grid search for strategy tuning
- ✅ **Out-of-Sample Validation**: Robust performance testing
- 📈 **Comprehensive Metrics**: Sharpe ratio, drawdown, win rate, etc.
- 🎯 **Multi-Symbol Support**: Trade multiple assets simultaneously

## 📋 Quick Start

```python
from script import MultiSymbolDayTradingAlgo

# Initialize trader
trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT', 'GOOGL'], initial_capital=50000)

# Fetch data and calculate indicators
trader.fetch_data_alternative(period='5d', interval='5m')
trader.calculate_indicators()

# Test strategies
trader.backtest_strategy('breakout')
trader.backtest_strategy('vwap')
trader.backtest_strategy('combined')  # Uses voting mechanism

# Compare all strategies
comparison = trader.run_all_strategies()
print(comparison)
```

## 🔧 Installation

```bash
pip install yfinance pandas numpy matplotlib seaborn
```

## 📊 Performance Metrics

The framework provides comprehensive performance analysis:
- Total Return (%)
- Sharpe Ratio
- Maximum Drawdown (%)
- Win Rate (%)
- Strategy Volatility (%)
- Buy & Hold Comparison

## 🧪 Testing

Run comprehensive tests:
```bash
python test_enhancements.py
```

## 📚 Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed usage instructions, strategy descriptions, and API documentation.

## 🎯 New in This Version

- ✅ 4 new trading strategies (Breakout, Range, VWAP, News-Based)
- ✅ Voting mechanism for combined strategy
- ✅ Parameter optimization framework
- ✅ Out-of-sample validation
- ✅ Enhanced technical indicators (VWAP, ATR, Support/Resistance)
- ✅ Comprehensive test suite

## 📈 Example Results

```
STRATEGY COMPARISON
==================================================
                 Total Return (%)  Sharpe Ratio  Win Rate (%)
momentum                   -45.97          0.56         50.54
vwap                       -46.91          0.97         59.52
mean_reversion             -48.71          0.35         56.25
combined                   -49.98         -1.92         50.00
```

## 🤝 Contributing

1. Fork the repository
2. Add new strategies following the existing pattern
3. Include comprehensive tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.