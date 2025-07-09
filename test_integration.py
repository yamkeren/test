#!/usr/bin/env python3
"""
Integration test script to verify all components work together.
This script performs basic functionality tests without requiring IB Gateway.
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import script
        print("✓ script.py imported")
        
        import ibkr_api
        print("✓ ibkr_api.py imported")
        
        import portfolio_dashboard
        print("✓ portfolio_dashboard.py imported")
        
        import live_trading
        print("✓ live_trading.py imported")
        
        import examples
        print("✓ examples.py imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_original_functionality():
    """Test that original functionality still works."""
    print("\nTesting original functionality...")
    try:
        from script import MultiSymbolDayTradingAlgo
        
        # Create original trader
        trader = MultiSymbolDayTradingAlgo(['AAPL'], initial_capital=10000)
        print("✓ Original trader created")
        
        # Test key methods exist
        methods = ['fetch_data', 'calculate_indicators', 'combined_strategy', 'backtest_strategy']
        for method in methods:
            if hasattr(trader, method):
                print(f"✓ Method {method} available")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Original functionality test failed: {e}")
        return False

def test_ibkr_configuration():
    """Test IBKR configuration system."""
    print("\nTesting IBKR configuration...")
    try:
        from ibkr_api import IBKRConfigManager
        
        # Create config manager
        config = IBKRConfigManager()
        print("✓ Config manager created")
        
        # Test configuration loading
        params = config.get_connection_params()
        print(f"✓ Connection params: {params}")
        
        # Test paper trading check
        is_paper = config.is_paper_trading()
        print(f"✓ Paper trading: {is_paper}")
        
        return True
    except Exception as e:
        print(f"❌ IBKR configuration test failed: {e}")
        return False

def test_live_trading_creation():
    """Test live trading algorithm creation."""
    print("\nTesting live trading algorithm...")
    try:
        from live_trading import LiveTradingAlgorithm
        
        # Create live trader
        trader = LiveTradingAlgorithm(
            symbols=['AAPL'],
            initial_capital=10000,
            use_ibkr=False,  # Disable IBKR for testing
            paper_trading=True
        )
        print("✓ Live trader created")
        
        # Test that it has all original methods
        if hasattr(trader, 'fetch_data') and hasattr(trader, 'calculate_indicators'):
            print("✓ Inherits original functionality")
        else:
            print("❌ Missing original functionality")
            return False
        
        # Test new methods
        new_methods = ['generate_trading_signals', 'execute_trade']
        for method in new_methods:
            if hasattr(trader, method):
                print(f"✓ New method {method} available")
            else:
                print(f"❌ New method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Live trading test failed: {e}")
        return False

def test_portfolio_dashboard():
    """Test portfolio dashboard functionality."""
    print("\nTesting portfolio dashboard...")
    try:
        from portfolio_dashboard import PortfolioDashboard
        from ibkr_api import IBKRAPIClient
        
        # Create client (won't connect without IB Gateway)
        client = IBKRAPIClient()
        dashboard = PortfolioDashboard(client)
        print("✓ Portfolio dashboard created")
        
        # Test methods exist
        methods = ['get_portfolio_summary', 'display_portfolio_summary', 'generate_risk_report']
        for method in methods:
            if hasattr(dashboard, method):
                print(f"✓ Method {method} available")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Portfolio dashboard test failed: {e}")
        return False

def test_data_structures():
    """Test data structures and classes."""
    print("\nTesting data structures...")
    try:
        from ibkr_api import TradeOrder, Position, Portfolio
        
        # Test TradeOrder
        order = TradeOrder(
            symbol='AAPL',
            action='BUY',
            quantity=100,
            order_type='MARKET'
        )
        print("✓ TradeOrder created")
        
        # Test Position
        position = Position(
            symbol='AAPL',
            quantity=100,
            avg_cost=150.0,
            market_price=155.0,
            market_value=15500.0,
            unrealized_pnl=500.0
        )
        print("✓ Position created")
        
        # Test Portfolio
        portfolio = Portfolio(
            positions=[position],
            cash=5000.0,
            total_value=20500.0,
            unrealized_pnl=500.0,
            realized_pnl=0.0
        )
        print("✓ Portfolio created")
        
        return True
    except Exception as e:
        print(f"❌ Data structures test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")
    required_files = [
        'script.py',
        'ibkr_api.py',
        'live_trading.py',
        'portfolio_dashboard.py',
        'examples.py',
        'requirements.txt',
        'README.md',
        'IBKR_DOCUMENTATION.md',
        'ibkr_config_sample.py',
        '.gitignore'
    ]
    
    import os
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def main():
    """Run all tests."""
    print("=" * 60)
    print("Interactive Brokers Trading Framework Integration Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Original Functionality", test_original_functionality),
        ("IBKR Configuration", test_ibkr_configuration),
        ("Live Trading Algorithm", test_live_trading_creation),
        ("Portfolio Dashboard", test_portfolio_dashboard),
        ("Data Structures", test_data_structures),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✓ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            print(traceback.format_exc())
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Framework is ready for use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())