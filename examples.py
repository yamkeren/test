#!/usr/bin/env python3
"""
Example script demonstrating the Interactive Brokers trading framework.
This script shows how to use the enhanced trading features.
"""

import asyncio
import logging
from live_trading import LiveTradingAlgorithm, create_live_trader, run_portfolio_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def example_basic_usage():
    """Basic usage example: Connect, fetch data, and generate signals."""
    print("=== Basic Usage Example ===")
    
    # Create trader instance
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    trader = LiveTradingAlgorithm(
        symbols=symbols,
        initial_capital=10000,
        paper_trading=True,  # Always use paper trading for testing
        max_position_size=1000
    )
    
    try:
        # Connect to IBKR
        connected = await trader.connect_to_ibkr()
        if connected:
            print("✓ Connected to IBKR successfully!")
            
            # Fetch real-time data
            print("Fetching real-time data...")
            await trader.fetch_real_time_data()
            
            if trader.data:
                print(f"✓ Data fetched for {len(trader.data)} symbols")
                
                # Calculate technical indicators
                trader.calculate_indicators()
                print("✓ Technical indicators calculated")
                
                # Generate trading signals
                signals = await trader.generate_trading_signals('combined')
                print(f"✓ Generated {len(signals)} trading signals")
                
                # Display signals
                for signal in signals:
                    action = "BUY" if signal.signal > 0 else "SELL"
                    print(f"  {signal.symbol}: {action} {signal.suggested_quantity} shares "
                          f"(confidence: {signal.confidence:.2f})")
                
                # Show portfolio summary
                if trader.dashboard:
                    await trader.dashboard.display_portfolio_summary()
            else:
                print("⚠ No data received from IBKR")
        else:
            print("❌ Failed to connect to IBKR")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Always disconnect
        await trader.disconnect_from_ibkr()
        print("✓ Disconnected from IBKR")


async def example_portfolio_dashboard():
    """Portfolio dashboard example."""
    print("\n=== Portfolio Dashboard Example ===")
    
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    trader = await create_live_trader(symbols, initial_capital=10000)
    
    if trader.dashboard:
        try:
            # Display portfolio summary
            await trader.dashboard.display_portfolio_summary()
            
            # Display positions table
            await trader.dashboard.display_positions_table()
            
            # Show risk report
            await trader.dashboard.display_risk_report()
            
            # Record a snapshot
            await trader.dashboard.record_portfolio_snapshot()
            print("✓ Portfolio snapshot recorded")
            
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
    else:
        print("❌ Dashboard not available")
    
    await trader.disconnect_from_ibkr()


async def example_trading_signals():
    """Trading signals example for multiple strategies."""
    print("\n=== Trading Signals Example ===")
    
    symbols = ['AAPL', 'TSLA']
    trader = LiveTradingAlgorithm(symbols, initial_capital=10000, paper_trading=True)
    
    try:
        if await trader.connect_to_ibkr():
            # Fetch data
            await trader.fetch_real_time_data()
            trader.calculate_indicators()
            
            # Test different strategies
            strategies = ['combined', 'momentum', 'mean_reversion']
            
            for strategy in strategies:
                print(f"\n--- {strategy.upper()} Strategy ---")
                signals = await trader.generate_trading_signals(strategy)
                
                if signals:
                    for signal in signals:
                        action = "BUY" if signal.signal > 0 else "SELL"
                        print(f"  {signal.symbol}: {action} {signal.suggested_quantity} shares "
                              f"(confidence: {signal.confidence:.2f}, price: ${signal.current_price:.2f})")
                else:
                    print("  No signals generated")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await trader.disconnect_from_ibkr()


async def example_paper_trading():
    """Paper trading example with actual trade execution."""
    print("\n=== Paper Trading Example ===")
    print("⚠ WARNING: This example executes actual trades (paper trading)")
    
    # Ask for confirmation
    response = input("Do you want to proceed with paper trading? (y/N): ")
    if response.lower() != 'y':
        print("Paper trading example skipped")
        return
    
    symbols = ['AAPL']
    trader = LiveTradingAlgorithm(
        symbols=symbols,
        initial_capital=10000,
        paper_trading=True,  # ALWAYS use paper trading for examples
        max_position_size=500,
        max_daily_trades=2
    )
    
    try:
        if await trader.connect_to_ibkr():
            # Fetch data and calculate indicators
            await trader.fetch_real_time_data()
            trader.calculate_indicators()
            
            # Generate signals
            signals = await trader.generate_trading_signals('combined')
            
            if signals:
                # Execute one trade as an example
                signal = signals[0]
                print(f"Executing trade for {signal.symbol}...")
                
                trade_order = await trader.execute_trade(signal)
                
                if trade_order:
                    print(f"✓ Trade executed: {trade_order.action} {trade_order.quantity} "
                          f"{trade_order.symbol} (Order ID: {trade_order.order_id})")
                    
                    # Check order status
                    await asyncio.sleep(2)  # Wait a bit
                    await trader.update_order_status()
                    
                    # Show updated portfolio
                    if trader.dashboard:
                        await trader.dashboard.display_portfolio_summary()
                else:
                    print("❌ Trade execution failed")
            else:
                print("No trading signals generated")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await trader.disconnect_from_ibkr()


async def example_backtest_with_ibkr():
    """Backtesting with real IBKR data."""
    print("\n=== Backtesting with IBKR Data ===")
    
    symbols = ['AAPL', 'GOOGL']
    trader = LiveTradingAlgorithm(symbols, initial_capital=10000)
    
    try:
        if await trader.connect_to_ibkr():
            print("Running backtest with real IBKR data...")
            
            # Run backtest
            results = await trader.backtest_with_ibkr_data(
                strategy='combined',
                duration='5 D'  # 5 days of data
            )
            
            if results:
                print("✓ Backtest completed")
                
                # Show results for each symbol
                for symbol in symbols:
                    if symbol in results:
                        print(f"\n{symbol} Results:")
                        # The results would contain backtest metrics
                        # This is a simplified display
                        print(f"  Data available: Yes")
                    else:
                        print(f"\n{symbol} Results: No data")
                
                # Calculate portfolio metrics
                metrics = trader.calculate_metrics()
                if metrics:
                    print(f"\nPortfolio Metrics:")
                    for key, value in metrics.items():
                        print(f"  {key}: {value}")
            else:
                print("❌ Backtest failed")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await trader.disconnect_from_ibkr()


def create_configuration():
    """Create sample configuration file."""
    print("\n=== Configuration Setup ===")
    
    trader = LiveTradingAlgorithm(['AAPL'], initial_capital=10000)
    trader.create_sample_config()
    
    print("✓ Sample configuration created: ibkr_config_sample.py")
    print("  Copy this file to ibkr_config.py and update with your settings")


def show_menu():
    """Show the example menu."""
    print("\n" + "="*60)
    print("Interactive Brokers Trading Framework Examples")
    print("="*60)
    print("1. Basic Usage (Connect, Fetch Data, Generate Signals)")
    print("2. Portfolio Dashboard")
    print("3. Trading Signals (Multiple Strategies)")
    print("4. Paper Trading (Execute Trades)")
    print("5. Backtesting with IBKR Data")
    print("6. Create Configuration File")
    print("7. Run Interactive Portfolio Dashboard")
    print("8. Exit")
    print("="*60)


async def main():
    """Main function to run examples."""
    print("Interactive Brokers Trading Framework Examples")
    print("Make sure IB Gateway/TWS is running before proceeding!")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        try:
            if choice == '1':
                await example_basic_usage()
            elif choice == '2':
                await example_portfolio_dashboard()
            elif choice == '3':
                await example_trading_signals()
            elif choice == '4':
                await example_paper_trading()
            elif choice == '5':
                await example_backtest_with_ibkr()
            elif choice == '6':
                create_configuration()
            elif choice == '7':
                symbols = ['AAPL', 'GOOGL', 'MSFT']
                await run_portfolio_dashboard(symbols)
            elif choice == '8':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"❌ Fatal error: {e}")