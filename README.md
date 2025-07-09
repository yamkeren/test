# Enhanced Day Trading Strategies Framework with IBKR Integration

A comprehensive multi-symbol day trading algorithm framework with advanced backtesting capabilities, multiple trading strategies, Interactive Brokers integration, and real-time trading capabilities.

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

### 🆕 Interactive Brokers Integration
- **Real-Time Data**: Live market data streaming
- **Trade Execution**: Market and limit orders
- **Portfolio Management**: Real-time position tracking
- **Account Management**: Account summary and balances
- **Risk Management**: Position sizing and loss limits
- **Paper Trading**: Safe testing environment
- **Secure Configuration**: Encrypted credential storage

## 📋 Quick Start

### Basic Usage (Backtesting)
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

### Enhanced Usage with IBKR Integration
```python
from enhanced_trading import create_enhanced_trader

# Create enhanced trader with IBKR support
trader = create_enhanced_trader(['AAPL', 'MSFT'], use_ibkr=True, initial_capital=50000)

# Connect to Interactive Brokers (requires TWS/IB Gateway)
if trader.connect_ibkr():
    # Get real-time market data
    market_data = trader.get_live_market_data('AAPL')
    print(f"AAPL Price: ${market_data['price']}")
    
    # Execute a trade
    result = trader.execute_trade('AAPL', 100, 'market')  # Buy 100 shares
    if result.success:
        print(f"Trade executed: {result.filled_qty} shares at ${result.avg_price}")
    
    # Get portfolio summary
    portfolio = trader.get_portfolio_summary()
    print(f"Account Value: ${portfolio['account_value']:,.2f}")
    
    # Start live trading (optional)
    # trader.start_live_trading('combined')
```

## 🔧 Installation

### Basic Installation
```bash
pip install yfinance pandas numpy matplotlib seaborn
```

### With Interactive Brokers Support
```bash
pip install yfinance pandas numpy matplotlib seaborn ib_insync
```

### IBKR Setup
1. **Install TWS or IB Gateway**: Download from Interactive Brokers
2. **Configure API**: Enable API access in TWS/IB Gateway settings
3. **Paper Trading**: Use port 7497 for paper trading, 7496 for live
4. **Configure Framework**: Set up credentials using environment variables

```bash
# Copy sample configuration
cp .env.sample .env

# Edit configuration
nano .env
```

### Environment Variables
```bash
# IBKR Configuration
IBKR_HOST=127.0.0.1
IBKR_PORT=7497                 # 7497 for paper trading, 7496 for live
IBKR_CLIENT_ID=1
IBKR_PAPER_TRADING=True        # IMPORTANT: Set to False for live trading
IBKR_TIMEOUT=30

# Trading Configuration
TRADING_INITIAL_CAPITAL=50000.0
TRADING_MAX_POSITION_SIZE=0.1  # 10% of portfolio per position
TRADING_STOP_LOSS_PCT=0.05     # 5% stop loss
TRADING_TAKE_PROFIT_PCT=0.10   # 10% take profit
TRADING_MAX_DAILY_LOSS=0.02    # 2% max daily loss
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

### Run Basic Tests
```bash
python test_enhancements.py
```

### Run IBKR Integration Tests
```bash
python test_ibkr_integration.py
```

### Run Demo
```bash
python demo_ibkr_integration.py
```

## 📚 Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for detailed usage instructions, strategy descriptions, and API documentation.

## 🎯 New in This Version

### IBKR Integration Features
- ✅ **Real-Time Data**: Live market data streaming from Interactive Brokers
- ✅ **Trade Execution**: Market and limit order execution
- ✅ **Portfolio Management**: Real-time position and account tracking
- ✅ **Risk Management**: Position sizing and daily loss limits
- ✅ **Configuration Management**: Secure credential storage
- ✅ **Paper Trading**: Safe testing environment

### Enhanced Trading Features
- ✅ 4 new trading strategies (Breakout, Range, VWAP, News-Based)
- ✅ Voting mechanism for combined strategy
- ✅ Parameter optimization framework
- ✅ Out-of-sample validation
- ✅ Enhanced technical indicators (VWAP, ATR, Support/Resistance)
- ✅ Comprehensive test suite
- ✅ Real-time trading capabilities
- ✅ Portfolio dashboard and reporting

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