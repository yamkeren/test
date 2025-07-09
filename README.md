# Interactive Brokers Trading Framework

A comprehensive Python trading framework that integrates with Interactive Brokers API for real-time market data, automated trading, and portfolio management.

## 🚀 Features

### 📊 Real-Time Data & Trading
- **Real-time market data** from Interactive Brokers API
- **Live trade execution** with market and limit orders
- **Order management** and tracking
- **Portfolio monitoring** with real-time P&L

### 🎯 Trading Strategies
- **Multiple strategies**: Combined, Momentum, Mean Reversion, Pairs Trading
- **Technical indicators**: Moving Averages, MACD, RSI, Bollinger Bands
- **Multi-symbol support** with portfolio allocation
- **Backtesting** with both historical and real-time data

### 🛡️ Risk Management
- **Position sizing** controls
- **Daily trade limits**
- **Maximum loss protection**
- **Paper trading** for safe testing

### 📈 Portfolio Dashboard
- **Interactive dashboard** for portfolio monitoring
- **Performance charts** and allocation visualizations
- **Risk analysis** and reporting
- **Data export** capabilities

### 🔒 Security
- **Secure credential management**
- **Environment variable support**
- **API key protection**
- **Paper trading mode**

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Interactive Brokers account
- IB Gateway or Trader Workstation (TWS)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Key Dependencies
- `ib-insync`: Interactive Brokers API client
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `matplotlib`: Data visualization
- `yfinance`: Fallback data source

## 🚀 Quick Start

### 1. Setup Interactive Brokers
1. Install [IB Gateway or TWS](https://www.interactivebrokers.com/en/index.php?f=16040)
2. Enable API connections in settings
3. Configure ports (7497 for paper trading, 7496 for live)

### 2. Configure the Framework
```python
# Create configuration file
python examples.py
# Choose option 6 to create configuration file
```

### 3. Run Examples
```python
# Run interactive examples
python examples.py
```

### 4. Basic Usage
```python
import asyncio
from live_trading import LiveTradingAlgorithm

async def main():
    # Create trader instance
    trader = LiveTradingAlgorithm(
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        initial_capital=10000,
        paper_trading=True,  # Always use paper trading for testing
        max_position_size=1000
    )
    
    # Connect to IBKR
    if await trader.connect_to_ibkr():
        # Fetch real-time data
        await trader.fetch_real_time_data()
        
        # Calculate indicators
        trader.calculate_indicators()
        
        # Generate trading signals
        signals = await trader.generate_trading_signals('combined')
        
        # Show portfolio summary
        if trader.dashboard:
            await trader.dashboard.display_portfolio_summary()
    
    # Disconnect
    await trader.disconnect_from_ibkr()

asyncio.run(main())
```

## 📋 Usage Examples

### Live Trading Session
```python
async def live_trading():
    trader = LiveTradingAlgorithm(
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        initial_capital=10000,
        paper_trading=True,
        max_position_size=1000
    )
    
    # Run live trading with 5-minute intervals
    await trader.run_live_trading(
        strategy='combined',
        check_interval=300
    )

asyncio.run(live_trading())
```

### Portfolio Dashboard
```python
from live_trading import run_portfolio_dashboard

async def dashboard():
    await run_portfolio_dashboard(['AAPL', 'GOOGL', 'MSFT'])

asyncio.run(dashboard())
```

### Backtesting with Real Data
```python
async def backtest():
    trader = LiveTradingAlgorithm(['AAPL', 'GOOGL'], initial_capital=10000)
    
    if await trader.connect_to_ibkr():
        results = await trader.backtest_with_ibkr_data(
            strategy='combined',
            duration='1 M'
        )
        print(f"Backtest completed: {results}")
    
    await trader.disconnect_from_ibkr()

asyncio.run(backtest())
```

## 🎯 Trading Strategies

### Available Strategies
1. **Combined Strategy**: Multi-indicator approach
2. **Momentum Strategy**: Trend-following
3. **Mean Reversion**: Reversal-based
4. **Pairs Trading**: Statistical arbitrage
5. **Sector Rotation**: Relative strength
6. **Multi-Timeframe**: Multiple timeframe analysis

### Strategy Configuration
```python
# Use specific strategy
signals = await trader.generate_trading_signals('momentum')

# Run live trading with strategy
await trader.run_live_trading(strategy='mean_reversion')
```

## 🛡️ Risk Management

### Built-in Controls
```python
trader = LiveTradingAlgorithm(
    symbols=['AAPL'],
    max_position_size=1000,      # Max $1000 per position
    max_daily_trades=5,          # Max 5 trades per day
    paper_trading=True,          # Always use for testing
)
```

### Risk Monitoring
```python
# Generate risk report
risk_metrics = await trader.dashboard.generate_risk_report()
print(f"Risk Score: {risk_metrics['risk_score']}/100")
```

## 📊 Dashboard Features

### Portfolio Summary
- Real-time portfolio value
- Cash and invested amounts
- Unrealized and realized P&L
- Position details

### Visualization
- Portfolio allocation pie chart
- Performance over time
- Risk analysis charts
- Export capabilities

### Interactive Features
```python
# Run interactive dashboard
await trader.dashboard.run_dashboard()

# Available options:
# 1. Portfolio Summary
# 2. Positions Detail
# 3. Allocation Chart
# 4. Performance Chart
# 5. Risk Report
# 6. Export Data
```

## 📁 Project Structure

```
├── script.py                    # Original trading algorithm
├── ibkr_api.py                 # Interactive Brokers API integration
├── live_trading.py             # Enhanced live trading algorithm
├── portfolio_dashboard.py      # Portfolio dashboard and visualization
├── examples.py                 # Usage examples and demos
├── requirements.txt            # Python dependencies
├── ibkr_config_sample.py       # Sample configuration file
├── IBKR_DOCUMENTATION.md       # Comprehensive documentation
└── README.md                   # This file
```

## 🔧 Configuration

### Configuration File
```python
# ibkr_config.py
IBKR_HOST = '127.0.0.1'
IBKR_PORT = 7497  # Paper trading port
IBKR_CLIENT_ID = 1
PAPER_TRADING = True
MAX_POSITION_SIZE = 1000
MAX_DAILY_LOSS = 500
MAX_TRADES_PER_DAY = 10
```

### Environment Variables
```bash
export IBKR_HOST=127.0.0.1
export IBKR_PORT=7497
export IBKR_CLIENT_ID=1
export PAPER_TRADING=True
```

## 🚨 Important Notes

### ⚠️ Risk Warning
- **Always use paper trading** for testing
- **Never risk capital** you cannot afford to lose
- **Past performance** does not guarantee future results
- **Test thoroughly** before live trading

### 📝 Prerequisites
- Interactive Brokers account
- IB Gateway or TWS running
- API connections enabled
- Paper trading account for testing

### 🔐 Security
- Keep API credentials secure
- Use environment variables
- Never commit credentials to version control
- Monitor API usage

## 🐛 Troubleshooting

### Common Issues
1. **Connection Issues**: Check IB Gateway/TWS is running
2. **Data Issues**: Verify symbol validity and market hours
3. **Order Issues**: Check account permissions and buying power

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Documentation

- **[Complete Documentation](IBKR_DOCUMENTATION.md)**: Detailed API reference and examples
- **[Interactive Brokers API](https://interactivebrokers.github.io/tws-api/)**: Official IB API documentation
- **[ib-insync Documentation](https://github.com/erdewit/ib_insync)**: Python IB API wrapper

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes only. Use at your own risk.

## ⚖️ Disclaimer

**Trading involves substantial risk of loss. This software is provided for educational purposes only. Past performance does not guarantee future results. Always consult with qualified financial advisors before making investment decisions.**

---

**Happy Trading! 📈**