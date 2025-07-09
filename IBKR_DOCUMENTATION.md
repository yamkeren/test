# Interactive Brokers Trading Framework Documentation

## Overview

This enhanced trading framework integrates with the Interactive Brokers API (IBKR) to provide real-time market data, trade execution, and portfolio management capabilities. The framework extends the existing `MultiSymbolDayTradingAlgo` class to support live trading while maintaining all existing backtesting functionality.

## Features

### 1. API Integration
- **Real-time Data**: Fetch live market data from Interactive Brokers
- **Authentication**: Secure connection to IB Gateway/TWS
- **Error Handling**: Comprehensive error handling and logging

### 2. Trading Operations
- **Order Execution**: Place market and limit orders
- **Order Management**: Track and monitor order status
- **Risk Controls**: Position sizing and daily trade limits

### 3. Portfolio Management
- **Real-time Portfolio**: View current positions and balances
- **Performance Tracking**: Monitor P&L and returns
- **Risk Analysis**: Portfolio risk metrics and analysis

### 4. Dashboard & Visualization
- **Interactive Dashboard**: Real-time portfolio monitoring
- **Charts & Graphs**: Performance and allocation visualization
- **Export Capabilities**: Export portfolio data to CSV

### 5. Security
- **Configuration Management**: Secure API credential storage
- **Paper Trading**: Safe testing environment
- **Environment Variables**: Secure credential management

## Installation

### Prerequisites
- Python 3.8+
- Interactive Brokers Account
- IB Gateway or Trader Workstation (TWS)

### Install Dependencies
```bash
pip install ib-insync pandas numpy matplotlib seaborn yfinance
```

### Required Packages
- `ib-insync`: Interactive Brokers API client
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing
- `matplotlib`: Plotting and visualization
- `seaborn`: Statistical data visualization
- `yfinance`: Fallback data source

## Setup Instructions

### 1. Interactive Brokers Setup

#### Install IB Gateway or TWS
1. Download from [Interactive Brokers](https://www.interactivebrokers.com/en/index.php?f=16040)
2. Install and configure according to IB documentation
3. Enable API connections in the configuration

#### Configure API Settings
1. In TWS/IB Gateway, go to **Global Configuration → API → Settings**
2. Enable "Enable ActiveX and Socket Clients"
3. Set "Socket port" (default: 7497 for paper trading, 7496 for live)
4. Add your client ID to "Trusted IP addresses"

### 2. Framework Configuration

#### Create Configuration File
```python
# Copy ibkr_config_sample.py to ibkr_config.py and update:

# IB Gateway/TWS Connection Settings
IBKR_HOST = '127.0.0.1'  # IB Gateway/TWS host
IBKR_PORT = 7497  # Port (7497 for paper trading, 7496 for live)
IBKR_CLIENT_ID = 1  # Unique client ID

# Trading Settings
PAPER_TRADING = True  # ALWAYS use True for testing!

# Risk Management
MAX_POSITION_SIZE = 1000  # Maximum position size in dollars
MAX_DAILY_LOSS = 500  # Maximum daily loss in dollars
MAX_TRADES_PER_DAY = 10  # Maximum trades per day
```

#### Environment Variables (Alternative)
```bash
export IBKR_HOST=127.0.0.1
export IBKR_PORT=7497
export IBKR_CLIENT_ID=1
export PAPER_TRADING=True
```

## Usage Examples

### Basic Usage

#### 1. Create Configuration
```python
from live_trading import LiveTradingAlgorithm

# Create sample configuration
trader = LiveTradingAlgorithm(['AAPL'], initial_capital=10000)
trader.create_sample_config()
```

#### 2. Initialize Trading Algorithm
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
    connected = await trader.connect_to_ibkr()
    if connected:
        print("Connected successfully!")
        
        # Fetch real-time data
        await trader.fetch_real_time_data()
        
        # Calculate indicators
        trader.calculate_indicators()
        
        # Generate trading signals
        signals = await trader.generate_trading_signals('combined')
        print(f"Generated {len(signals)} signals")
        
        # Execute trades (if signals exist)
        for signal in signals:
            await trader.execute_trade(signal)
    
    # Always disconnect
    await trader.disconnect_from_ibkr()

# Run the trading session
asyncio.run(main())
```

### Live Trading Session

```python
import asyncio
from live_trading import LiveTradingAlgorithm

async def run_live_trading():
    trader = LiveTradingAlgorithm(
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        initial_capital=10000,
        paper_trading=True,
        max_position_size=1000,
        max_daily_trades=5
    )
    
    # Run live trading with 5-minute intervals
    await trader.run_live_trading(
        strategy='combined',
        check_interval=300  # 5 minutes
    )

asyncio.run(run_live_trading())
```

### Portfolio Dashboard

```python
import asyncio
from live_trading import run_portfolio_dashboard

async def main():
    # Run interactive portfolio dashboard
    await run_portfolio_dashboard(['AAPL', 'GOOGL', 'MSFT'])

asyncio.run(main())
```

### Backtesting with Real Data

```python
import asyncio
from live_trading import LiveTradingAlgorithm

async def backtest_with_ibkr():
    trader = LiveTradingAlgorithm(['AAPL', 'GOOGL'], initial_capital=10000)
    
    # Connect and run backtest
    if await trader.connect_to_ibkr():
        results = await trader.backtest_with_ibkr_data(
            strategy='combined',
            duration='1 M'  # 1 month of data
        )
        
        if results:
            print("Backtest Results:")
            for symbol, result in results.items():
                print(f"{symbol}: {result}")
    
    await trader.disconnect_from_ibkr()

asyncio.run(backtest_with_ibkr())
```

## API Reference

### LiveTradingAlgorithm Class

#### Constructor
```python
LiveTradingAlgorithm(
    symbols: List[str],
    initial_capital: float = 10000,
    use_ibkr: bool = True,
    paper_trading: bool = True,
    max_position_size: float = 1000,
    max_daily_trades: int = 10
)
```

#### Key Methods

##### Connection Management
- `connect_to_ibkr()`: Connect to Interactive Brokers API
- `disconnect_from_ibkr()`: Disconnect from API

##### Data Operations
- `fetch_real_time_data()`: Fetch real-time market data
- `get_current_market_data()`: Get current prices and market data

##### Trading Operations
- `generate_trading_signals()`: Generate trading signals
- `execute_trade()`: Execute a trade order
- `update_order_status()`: Update status of active orders

##### Live Trading
- `run_live_trading()`: Run continuous live trading session

##### Analysis
- `backtest_with_ibkr_data()`: Run backtest with real IBKR data

### IBKRAPIClient Class

#### Key Methods
- `connect()`: Connect to IB Gateway/TWS
- `get_real_time_data()`: Fetch historical data
- `get_market_data()`: Get current market data
- `place_order()`: Place a trading order
- `get_portfolio()`: Get portfolio information
- `get_order_status()`: Check order status

### PortfolioDashboard Class

#### Key Methods
- `display_portfolio_summary()`: Show portfolio summary
- `display_positions_table()`: Show detailed positions
- `plot_portfolio_allocation()`: Create allocation pie chart
- `plot_performance_chart()`: Create performance chart
- `generate_risk_report()`: Generate risk analysis
- `export_portfolio_data()`: Export data to CSV
- `run_dashboard()`: Run interactive dashboard

## Trading Strategies

The framework supports all existing strategies from the base class:

### Available Strategies
1. **Combined Strategy**: Multi-indicator approach using MA, MACD, RSI, Bollinger Bands
2. **Momentum Strategy**: Trend-following using moving averages and MACD
3. **Mean Reversion**: Bollinger Bands and RSI-based reversal strategy
4. **Pairs Trading**: Statistical arbitrage between correlated stocks
5. **Sector Rotation**: Relative strength-based sector rotation
6. **Multi-Timeframe**: Multiple timeframe analysis

### Strategy Selection
```python
# Use specific strategy
signals = await trader.generate_trading_signals('momentum')

# Run live trading with specific strategy
await trader.run_live_trading(strategy='mean_reversion')
```

## Risk Management

### Built-in Risk Controls

#### Position Sizing
```python
trader = LiveTradingAlgorithm(
    symbols=['AAPL'],
    max_position_size=1000,  # Maximum $1000 per position
)
```

#### Daily Limits
```python
trader = LiveTradingAlgorithm(
    symbols=['AAPL'],
    max_daily_trades=5,  # Maximum 5 trades per day
)
```

#### Paper Trading
```python
trader = LiveTradingAlgorithm(
    symbols=['AAPL'],
    paper_trading=True,  # Always use for testing
)
```

### Risk Monitoring
```python
# Get risk report
risk_metrics = await trader.dashboard.generate_risk_report()
print(f"Risk Score: {risk_metrics['risk_score']}/100")
```

## Error Handling

### Common Issues and Solutions

#### 1. Connection Issues
```
Error: Failed to connect to IB Gateway
```
**Solution**: 
- Ensure IB Gateway/TWS is running
- Check port configuration (7497 for paper, 7496 for live)
- Verify API settings are enabled

#### 2. Authentication Issues
```
Error: Invalid client ID
```
**Solution**:
- Use unique client ID
- Check if client ID is already in use
- Restart IB Gateway/TWS

#### 3. Data Issues
```
Error: No data received for symbol
```
**Solution**:
- Verify symbol is valid
- Check market hours
- Ensure data subscriptions are active

### Logging Configuration
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

### 1. Configuration Security
- Never commit configuration files with credentials
- Use environment variables for sensitive data
- Keep configuration files in `.gitignore`

### 2. Paper Trading
- Always test with paper trading first
- Verify strategies thoroughly before live trading
- Use small position sizes initially

### 3. API Security
- Use unique client IDs
- Restrict API access to localhost
- Monitor API usage

## Performance Optimization

### 1. Data Fetching
```python
# Use appropriate intervals
await trader.fetch_real_time_data(
    duration='1 D',
    bar_size='5 mins'  # Adjust based on strategy needs
)
```

### 2. Trading Frequency
```python
# Optimize check intervals
await trader.run_live_trading(
    strategy='combined',
    check_interval=300  # 5 minutes - adjust as needed
)
```

### 3. Memory Management
- Portfolio history is automatically limited to 1000 snapshots
- Clear old data periodically
- Monitor memory usage for long-running sessions

## Troubleshooting

### Common Problems

#### 1. Market Data Not Updating
- Check if market is open
- Verify data subscriptions
- Restart IB Gateway/TWS

#### 2. Orders Not Executing
- Check account permissions
- Verify sufficient buying power
- Review order parameters

#### 3. Performance Issues
- Reduce check frequency
- Limit number of symbols
- Use appropriate data intervals

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Support and Resources

### Interactive Brokers Resources
- [IB API Documentation](https://interactivebrokers.github.io/tws-api/)
- [IB Gateway/TWS Setup](https://www.interactivebrokers.com/en/index.php?f=16040)
- [Paper Trading Account](https://www.interactivebrokers.com/en/index.php?f=1286)

### Additional Libraries
- [ib-insync Documentation](https://github.com/erdewit/ib_insync)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [matplotlib Documentation](https://matplotlib.org/stable/contents.html)

## License and Disclaimer

### Important Disclaimer
This software is for educational and research purposes only. Trading financial instruments involves substantial risk of loss. Past performance does not guarantee future results. Always use paper trading for testing and never risk capital you cannot afford to lose.

### Risk Warning
- Always test thoroughly with paper trading
- Never invest more than you can afford to lose
- Past performance does not guarantee future results
- Consult with financial advisors before live trading

## Changelog

### Version 1.0.0
- Initial release with IBKR API integration
- Real-time data fetching
- Live trade execution
- Portfolio management
- Interactive dashboard
- Risk management controls
- Comprehensive documentation