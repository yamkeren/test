import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import seaborn as sns
import time
import random
warnings.filterwarnings('ignore')

class MultiSymbolDayTradingAlgo:
    def __init__(self, symbols, initial_capital=10000, equal_weight=True):
        """
        Initialize multi-symbol day trading algorithm
        
        Args:
            symbols: List of stock symbols or single symbol
            initial_capital: Starting capital
            equal_weight: If True, allocate capital equally across symbols
        """
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.initial_capital = initial_capital
        self.equal_weight = equal_weight
        self.data = {}
        self.signals = {}
        self.results = {}
        self.portfolio_results = None
        self.capital_allocation = {}
        
        # Calculate capital allocation
        if self.equal_weight:
            capital_per_symbol = initial_capital / len(self.symbols)
            self.capital_allocation = {symbol: capital_per_symbol for symbol in self.symbols}
        else:
            # Default equal allocation, can be customized
            self.capital_allocation = {symbol: initial_capital / len(self.symbols) for symbol in self.symbols}
    
    def set_custom_allocation(self, allocation_dict):
        """
        Set custom capital allocation for each symbol
        
        Args:
            allocation_dict: Dictionary with symbol: allocation_percentage
        """
        total_allocation = sum(allocation_dict.values())
        if abs(total_allocation - 1.0) > 0.01:
            print(f"Warning: Total allocation is {total_allocation:.2%}, not 100%")
        
        for symbol in self.symbols:
            if symbol in allocation_dict:
                self.capital_allocation[symbol] = self.initial_capital * allocation_dict[symbol]
            else:
                print(f"Warning: No allocation specified for {symbol}")
    
    def fetch_data_single_symbol(self, symbol, period='1mo', interval='5m', max_retries=3):
        """Fetch data for a single symbol with retry logic"""
        for attempt in range(max_retries):
            try:
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 2.0))
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, interval=interval)
                
                if data.empty:
                    print(f"No data found for {symbol}")
                    return None
                
                data.dropna(inplace=True)
                print(f"Fetched {len(data)} data points for {symbol}")
                return data
                
            except Exception as e:
                if "Too Many Requests" in str(e) or "Rate limited" in str(e):
                    wait_time = (2 ** attempt) + random.uniform(1, 3)  # Exponential backoff
                    print(f"Rate limited for {symbol}, waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"Error fetching data for {symbol}: {e}")
                    break
        
        return None
    
    def fetch_data(self, period='1mo', interval='5m', max_workers=2, sequential=False):
        """
        Fetch data for all symbols with rate limiting protection
        
        Args:
            period: Data period ('1mo', '1d', '5d', '1wk', '1y')
            interval: Data interval ('1m', '2m', '5m', '15m', '30m', '1h', '1d')
            max_workers: Maximum concurrent requests (reduced to avoid rate limits)
            sequential: If True, fetch data sequentially instead of parallel
        """
        print(f"Fetching data for {len(self.symbols)} symbols...")
        
        if sequential:
            # Sequential fetching to avoid rate limits
            print("Using sequential fetching to avoid rate limits...")
            for i, symbol in enumerate(self.symbols):
                print(f"Fetching {symbol} ({i+1}/{len(self.symbols)})")
                data = self.fetch_data_single_symbol(symbol, period, interval)
                if data is not None:
                    self.data[symbol] = data
                
                # Add delay between requests
                if i < len(self.symbols) - 1:
                    time.sleep(random.uniform(1, 3))
        else:
            # Parallel fetching with reduced workers
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.fetch_data_single_symbol, symbol, period, interval): symbol
                    for symbol in self.symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        data = future.result()
                        if data is not None:
                            self.data[symbol] = data
                    except Exception as e:
                        print(f"Error processing {symbol}: {e}")
        
        successful_symbols = list(self.data.keys())
        failed_symbols = [s for s in self.symbols if s not in successful_symbols]
        
        print(f"Successfully fetched data for {len(successful_symbols)} symbols")
        if failed_symbols:
            print(f"Failed to fetch data for: {failed_symbols}")
        
    def fetch_data_alternative(self, period='1mo', interval='5m'):
        """
        Alternative data fetching method using single ticker object
        This method is more rate-limit friendly
        """
        print(f"Fetching data for {len(self.symbols)} symbols using alternative method...")
        
        # Create a single ticker object for all symbols
        try:
            # Join symbols with spaces for bulk download
            symbols_str = ' '.join(self.symbols)
            print(f"Downloading data for: {symbols_str}")
            
            # Download data for all symbols at once
            data = yf.download(symbols_str, period=period, interval=interval, 
                             group_by='ticker', progress=True)
            
            if data.empty:
                print("No data retrieved")
                return False
            
            # Process data for each symbol
            for symbol in self.symbols:
                try:
                    if len(self.symbols) == 1:
                        # Single symbol case
                        symbol_data = data
                    else:
                        # Multiple symbols case
                        symbol_data = data[symbol]
                    
                    if symbol_data.empty:
                        print(f"No data found for {symbol}")
                        continue
                    
                    # Clean the data
                    symbol_data = symbol_data.dropna()
                    
                    if len(symbol_data) > 0:
                        self.data[symbol] = symbol_data
                        print(f"Successfully fetched {len(symbol_data)} data points for {symbol}")
                    else:
                        print(f"No valid data for {symbol} after cleaning")
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    continue
            
            successful_symbols = list(self.data.keys())
            failed_symbols = [s for s in self.symbols if s not in successful_symbols]
            
            print(f"Successfully fetched data for {len(successful_symbols)} symbols")
            if failed_symbols:
                print(f"Failed to fetch data for: {failed_symbols}")
            
            return len(successful_symbols) > 0
            
        except Exception as e:
            print(f"Error in alternative fetch method: {e}")
            return False
    
    def calculate_indicators(self):
        """Calculate technical indicators for all symbols"""
        print("Calculating technical indicators for all symbols...")
        
        for symbol in self.data.keys():
            df = self.data[symbol].copy()
            
            # Moving averages
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['EMA_5'] = df['Close'].ewm(span=5).mean()
            df['EMA_10'] = df['Close'].ewm(span=10).mean()
            
            # RSI
            df['RSI'] = self.calculate_rsi(df['Close'])
            
            # MACD
            df['MACD'], df['MACD_signal'] = self.calculate_macd(df['Close'])
            
            # Bollinger Bands
            df['BB_upper'], df['BB_middle'], df['BB_lower'] = self.calculate_bollinger_bands(df['Close'])
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=10).mean()
            df['Volume_ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price momentum
            df['Price_change'] = df['Close'].pct_change()
            df['Price_momentum'] = df['Close'].pct_change(periods=5)
            
            # Volatility
            df['Volatility'] = df['Close'].rolling(window=10).std()
            
            # Relative strength vs market (using first symbol as proxy)
            if len(self.data) > 1:
                first_symbol = list(self.data.keys())[0]
                if symbol != first_symbol:
                    market_returns = self.data[first_symbol]['Close'].pct_change()
                    symbol_returns = df['Close'].pct_change()
                    df['Relative_strength'] = symbol_returns - market_returns
                else:
                    df['Relative_strength'] = 0
            else:
                df['Relative_strength'] = 0
            
            self.data[symbol] = df
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd, macd_signal
    
    def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def sector_rotation_strategy(self, symbol):
        """Sector rotation strategy using relative strength"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy when showing relative strength and momentum
        buy_condition = (df['Relative_strength'] > 0.001) & (df['RSI'] < 70) & (df['Volume_ratio'] > 1.1)
        
        # Sell when losing relative strength
        sell_condition = (df['Relative_strength'] < -0.001) | (df['RSI'] > 80)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def pairs_trading_strategy(self, symbol):
        """Pairs trading strategy (mean reversion between correlated stocks)"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        if len(self.data) > 1:
            # Calculate correlation with other symbols
            correlations = {}
            for other_symbol in self.data.keys():
                if other_symbol != symbol:
                    try:
                        correlation = df['Close'].corr(self.data[other_symbol]['Close'])
                        correlations[other_symbol] = correlation
                    except:
                        continue
            
            if correlations:
                # Find most correlated pair
                best_pair = max(correlations, key=correlations.get)
                if correlations[best_pair] > 0.7:  # Strong correlation
                    # Calculate spread
                    spread = df['Close'] - self.data[best_pair]['Close']
                    spread_mean = spread.rolling(window=20).mean()
                    spread_std = spread.rolling(window=20).std()
                    
                    # Z-score of spread
                    z_score = (spread - spread_mean) / spread_std
                    
                    # Buy when spread is too low (stocks will converge)
                    buy_condition = z_score < -2
                    
                    # Sell when spread normalizes
                    sell_condition = z_score > 0
                    
                    signals.loc[buy_condition, 'signal'] = 1
                    signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def multi_timeframe_strategy(self, symbol):
        """Multi-timeframe strategy using trend alignment"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Short-term trend (5-period)
        short_trend = df['SMA_5'] > df['SMA_10']
        
        # Medium-term trend (10-period)
        medium_trend = df['SMA_10'] > df['SMA_20']
        
        # Long-term momentum
        long_momentum = df['Price_momentum'] > 0
        
        # Volume confirmation
        volume_confirm = df['Volume_ratio'] > 1.1
        
        # Buy when all timeframes align
        buy_condition = short_trend & medium_trend & long_momentum & volume_confirm & (df['RSI'] < 75)
        
        # Sell when short-term trend breaks
        sell_condition = ~short_trend | (df['RSI'] > 85)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def mean_reversion_strategy(self, symbol):
        """Mean reversion strategy using Bollinger Bands and RSI"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy when price touches lower Bollinger Band and RSI is oversold
        buy_condition = (df['Close'] <= df['BB_lower']) & (df['RSI'] < 30)
        
        # Sell when price touches upper Bollinger Band and RSI is overbought
        sell_condition = (df['Close'] >= df['BB_upper']) & (df['RSI'] > 70)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def momentum_strategy(self, symbol):
        """Momentum strategy using moving averages and MACD"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy when fast MA crosses above slow MA and MACD is bullish
        buy_condition = (df['SMA_5'] > df['SMA_10']) & (df['MACD'] > df['MACD_signal']) & (df['Volume_ratio'] > 1.2)
        
        # Sell when fast MA crosses below slow MA or MACD turns bearish
        sell_condition = (df['SMA_5'] < df['SMA_10']) | (df['MACD'] < df['MACD_signal'])
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def combined_strategy(self, symbol):
        """Combined strategy using multiple indicators"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Score-based approach
        score = pd.Series(0, index=df.index)
        
        # MA trend
        score += (df['SMA_5'] > df['SMA_10']).astype(int)
        score += (df['EMA_5'] > df['EMA_10']).astype(int)
        
        # MACD
        score += (df['MACD'] > df['MACD_signal']).astype(int)
        
        # RSI
        score += (df['RSI'] < 70).astype(int)
        score -= (df['RSI'] > 80).astype(int)
        
        # Volume
        score += (df['Volume_ratio'] > 1.2).astype(int)
        
        # Bollinger Bands
        score += (df['Close'] > df['BB_lower']).astype(int)
        score -= (df['Close'] > df['BB_upper']).astype(int)
        
        # Relative strength (for multi-symbol)
        if len(self.data) > 1:
            score += (df['Relative_strength'] > 0).astype(int)
        
        # Buy when score is high
        buy_condition = score >= 4
        
        # Sell when score is low
        sell_condition = score <= 2
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def breakout_trading_strategy(self, symbol):
        """Breakout trading strategy - Buy when price crosses resistance or sell when it breaks support"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Calculate support and resistance levels using rolling windows
        window = 20
        df['resistance'] = df['High'].rolling(window=window).max()
        df['support'] = df['Low'].rolling(window=window).min()
        
        # Calculate recent high/low for breakout detection
        short_window = 5
        df['recent_high'] = df['High'].rolling(window=short_window).max()
        df['recent_low'] = df['Low'].rolling(window=short_window).min()
        
        # Breakout conditions
        # Buy signal: price breaks above resistance with volume confirmation
        resistance_breakout = (df['Close'] > df['resistance']) & (df['Volume_ratio'] > 1.5)
        
        # Sell signal: price breaks below support
        support_breakdown = (df['Close'] < df['support']) | (df['RSI'] > 80)
        
        # Additional confirmation using momentum
        momentum_confirm = df['Price_momentum'] > 0.01  # 1% momentum
        
        # Buy when breaking resistance with momentum and volume
        buy_condition = resistance_breakout & momentum_confirm
        
        # Sell when breaking support or overbought
        sell_condition = support_breakdown
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def range_trading_strategy(self, symbol):
        """Range trading strategy - Trade within a price range based on support and resistance"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Calculate support and resistance using Bollinger Bands and price levels
        window = 20
        df['price_high'] = df['High'].rolling(window=window).max()
        df['price_low'] = df['Low'].rolling(window=window).min()
        
        # Calculate range boundaries
        df['range_top'] = df['price_high']
        df['range_bottom'] = df['price_low']
        df['range_middle'] = (df['range_top'] + df['range_bottom']) / 2
        
        # Range width for filtering
        df['range_width'] = (df['range_top'] - df['range_bottom']) / df['range_middle']
        
        # Only trade in established ranges (not too narrow or too wide)
        range_condition = (df['range_width'] > 0.02) & (df['range_width'] < 0.15)
        
        # Buy near support (bottom of range) with RSI confirmation
        buy_condition = (df['Close'] <= df['range_bottom'] * 1.02) & (df['RSI'] < 40) & range_condition
        
        # Sell near resistance (top of range) with RSI confirmation
        sell_condition = (df['Close'] >= df['range_top'] * 0.98) & (df['RSI'] > 60) & range_condition
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def vwap_trading_strategy(self, symbol):
        """VWAP trading strategy - Use Volume Weighted Average Price to guide buy/sell decisions"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Calculate VWAP (Volume Weighted Average Price)
        df['typical_price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['vwap_numerator'] = (df['typical_price'] * df['Volume']).cumsum()
        df['vwap_denominator'] = df['Volume'].cumsum()
        df['VWAP'] = df['vwap_numerator'] / df['vwap_denominator']
        
        # Calculate rolling VWAP for shorter periods
        window = 20
        df['rolling_vwap_num'] = (df['typical_price'] * df['Volume']).rolling(window=window).sum()
        df['rolling_vwap_den'] = df['Volume'].rolling(window=window).sum()
        df['rolling_VWAP'] = df['rolling_vwap_num'] / df['rolling_vwap_den']
        
        # VWAP deviation bands
        df['vwap_std'] = df['Close'].rolling(window=window).std()
        df['vwap_upper'] = df['rolling_VWAP'] + (df['vwap_std'] * 1.5)
        df['vwap_lower'] = df['rolling_VWAP'] - (df['vwap_std'] * 1.5)
        
        # Buy when price is below VWAP with volume confirmation
        buy_condition = (df['Close'] < df['rolling_VWAP']) & (df['Close'] > df['vwap_lower']) & \
                       (df['Volume_ratio'] > 1.2) & (df['RSI'] < 50)
        
        # Sell when price is above VWAP and showing weakness
        sell_condition = (df['Close'] > df['rolling_VWAP']) & (df['Close'] < df['vwap_upper']) & \
                        (df['RSI'] > 60) | (df['Close'] > df['vwap_upper'])
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def news_based_trading_strategy(self, symbol):
        """News-based trading strategy - Incorporate trading decisions based on company news
        Note: This is a simplified version using volume and volatility as news proxies"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Since we don't have real news data, we'll use volume and volatility spikes
        # as proxies for news events
        
        # Calculate volume anomalies (potential news events)
        df['volume_ma'] = df['Volume'].rolling(window=20).mean()
        df['volume_std'] = df['Volume'].rolling(window=20).std()
        df['volume_zscore'] = (df['Volume'] - df['volume_ma']) / df['volume_std']
        
        # Calculate volatility anomalies
        df['volatility_ma'] = df['Volatility'].rolling(window=10).mean()
        df['volatility_std'] = df['Volatility'].rolling(window=10).std()
        df['volatility_zscore'] = (df['Volatility'] - df['volatility_ma']) / df['volatility_std']
        
        # News event detection (high volume + high volatility)
        news_event = (df['volume_zscore'] > 2) & (df['volatility_zscore'] > 1.5)
        
        # Direction based on price momentum during news events
        positive_news = news_event & (df['Price_change'] > 0) & (df['RSI'] < 70)
        negative_news = news_event & (df['Price_change'] < 0) & (df['RSI'] > 30)
        
        # Buy on positive news with confirmation
        buy_condition = positive_news & (df['Volume_ratio'] > 1.5)
        
        # Sell on negative news or profit taking after positive news
        sell_condition = negative_news | (df['RSI'] > 80)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def voting_strategy(self, symbol):
        """Combined strategy using majority voting from multiple strategies"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Get signals from all individual strategies
        strategies = {
            'momentum': self.momentum_strategy(symbol),
            'mean_reversion': self.mean_reversion_strategy(symbol),
            'breakout': self.breakout_trading_strategy(symbol),
            'range_trading': self.range_trading_strategy(symbol),
            'vwap': self.vwap_trading_strategy(symbol),
            'news_based': self.news_based_trading_strategy(symbol)
        }
        
        # Create voting DataFrame
        votes = pd.DataFrame(index=df.index)
        for name, strategy_signals in strategies.items():
            votes[name] = strategy_signals['signal']
        
        # Calculate buy and sell votes
        buy_votes = (votes == 1).sum(axis=1)
        sell_votes = (votes == -1).sum(axis=1)
        total_strategies = len(strategies)
        
        # Majority voting with tie-breaking
        # Need more than half for a signal
        majority_threshold = total_strategies // 2 + 1
        
        # Buy when majority vote buy
        buy_condition = buy_votes >= majority_threshold
        
        # Sell when majority vote sell
        sell_condition = sell_votes >= majority_threshold
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        # Store individual votes for analysis
        signals['buy_votes'] = buy_votes
        signals['sell_votes'] = sell_votes
        
        return signals
    
    def backtest_strategy(self, strategy_name='combined'):
        """Backtest a strategy for all symbols"""
        if not self.data:
            print("No data available. Please fetch data first.")
            return None
        
        print(f"Backtesting {strategy_name} strategy for all symbols...")
        
        # Get strategy function
        strategy_functions = {
            'mean_reversion': self.mean_reversion_strategy,
            'momentum': self.momentum_strategy,
            'combined': self.combined_strategy,
            'sector_rotation': self.sector_rotation_strategy,
            'pairs_trading': self.pairs_trading_strategy,
            'multi_timeframe': self.multi_timeframe_strategy,
            'breakout': self.breakout_trading_strategy,
            'range_trading': self.range_trading_strategy,
            'vwap': self.vwap_trading_strategy,
            'news_based': self.news_based_trading_strategy,
            'voting': self.voting_strategy
        }
        
        if strategy_name not in strategy_functions:
            print(f"Unknown strategy: {strategy_name}")
            return None
        
        strategy_func = strategy_functions[strategy_name]
        
        # Backtest each symbol
        for symbol in self.data.keys():
            try:
                signals = strategy_func(symbol)
                positions = signals['signal'].diff()
                
                # Initialize portfolio for this symbol
                portfolio = pd.DataFrame(index=self.data[symbol].index)
                portfolio['price'] = self.data[symbol]['Close']
                portfolio['signal'] = signals['signal']
                portfolio['positions'] = positions
                
                # Calculate returns
                portfolio['returns'] = self.data[symbol]['Close'].pct_change()
                portfolio['strategy_returns'] = portfolio['returns'] * portfolio['signal'].shift(1)
                
                # Calculate cumulative returns
                portfolio['cum_returns'] = (1 + portfolio['returns']).cumprod()
                portfolio['cum_strategy_returns'] = (1 + portfolio['strategy_returns']).cumprod()
                
                # Calculate portfolio value for this symbol
                initial_capital_symbol = self.capital_allocation[symbol]
                portfolio['portfolio_value'] = initial_capital_symbol * portfolio['cum_strategy_returns']
                
                self.results[symbol] = portfolio
                
            except Exception as e:
                print(f"Error backtesting {symbol}: {e}")
                continue
        
        # Calculate combined portfolio results
        self.calculate_portfolio_results()
        
        return self.results
    
    def calculate_portfolio_results(self):
        """Calculate combined portfolio results across all symbols"""
        if not self.results:
            return None
        
        # Find common date range
        all_dates = [df.index for df in self.results.values()]
        common_dates = all_dates[0]
        for dates in all_dates[1:]:
            common_dates = common_dates.intersection(dates)
        
        if len(common_dates) == 0:
            print("No common dates found across symbols")
            return None
        
        # Initialize portfolio results
        portfolio_results = pd.DataFrame(index=common_dates.sort_values())
        
        # Calculate weighted portfolio value
        total_portfolio_value = pd.Series(0, index=common_dates)
        total_initial_capital = 0
        
        for symbol in self.results.keys():
            symbol_data = self.results[symbol].loc[common_dates]
            weight = self.capital_allocation[symbol] / self.initial_capital
            total_portfolio_value += symbol_data['portfolio_value'] * weight
            total_initial_capital += self.capital_allocation[symbol]
        
        portfolio_results['portfolio_value'] = total_portfolio_value
        portfolio_results['portfolio_returns'] = portfolio_results['portfolio_value'].pct_change()
        portfolio_results['cum_portfolio_returns'] = portfolio_results['portfolio_value'] / self.initial_capital
        
        # Calculate buy and hold benchmark (equal weighted)
        buy_hold_value = pd.Series(0, index=common_dates)
        for symbol in self.results.keys():
            symbol_data = self.results[symbol].loc[common_dates]
            weight = self.capital_allocation[symbol] / self.initial_capital
            buy_hold_value += self.capital_allocation[symbol] * symbol_data['cum_returns']
        
        portfolio_results['buy_hold_value'] = buy_hold_value
        portfolio_results['buy_hold_returns'] = buy_hold_value.pct_change()
        
        self.portfolio_results = portfolio_results
        return portfolio_results
    
    def calculate_metrics(self, symbol=None):
        """Calculate performance metrics for a symbol or entire portfolio"""
        if symbol is None:
            # Portfolio metrics
            if self.portfolio_results is None:
                print("No portfolio results available.")
                return None
            
            portfolio = self.portfolio_results
            total_return = (portfolio['portfolio_value'].iloc[-1] / self.initial_capital - 1) * 100
            buy_hold_return = (portfolio['buy_hold_value'].iloc[-1] / self.initial_capital - 1) * 100
            
            strategy_volatility = portfolio['portfolio_returns'].std() * np.sqrt(252) * 100
            
            # Sharpe ratio
            risk_free_rate = 0.02
            excess_returns = portfolio['portfolio_returns'].mean() * 252 - risk_free_rate
            sharpe_ratio = excess_returns / (strategy_volatility / 100) if strategy_volatility > 0 else 0
            
            # Maximum drawdown
            cumulative = portfolio['cum_portfolio_returns']
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            # Win rate
            winning_trades = portfolio['portfolio_returns'][portfolio['portfolio_returns'] > 0]
            losing_trades = portfolio['portfolio_returns'][portfolio['portfolio_returns'] < 0]
            total_trades = len(winning_trades) + len(losing_trades)
            win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
            
            metrics = {
                'Total Return (%)': round(total_return, 2),
                'Buy & Hold Return (%)': round(buy_hold_return, 2),
                'Strategy Volatility (%)': round(strategy_volatility, 2),
                'Sharpe Ratio': round(sharpe_ratio, 2),
                'Maximum Drawdown (%)': round(max_drawdown, 2),
                'Win Rate (%)': round(win_rate, 2),
                'Final Portfolio Value': round(portfolio['portfolio_value'].iloc[-1], 2),
                'Number of Symbols': len(self.data)
            }
            
        else:
            # Individual symbol metrics
            if symbol not in self.results:
                print(f"No results available for {symbol}")
                return None
            
            portfolio = self.results[symbol]
            initial_capital_symbol = self.capital_allocation[symbol]
            
            total_return = (portfolio['portfolio_value'].iloc[-1] / initial_capital_symbol - 1) * 100
            buy_hold_return = (portfolio['cum_returns'].iloc[-1] - 1) * 100
            
            strategy_volatility = portfolio['strategy_returns'].std() * np.sqrt(252) * 100
            
            # Sharpe ratio
            risk_free_rate = 0.02
            excess_returns = portfolio['strategy_returns'].mean() * 252 - risk_free_rate
            sharpe_ratio = excess_returns / (strategy_volatility / 100) if strategy_volatility > 0 else 0
            
            # Maximum drawdown
            cumulative = portfolio['cum_strategy_returns']
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            # Win rate
            winning_trades = portfolio['strategy_returns'][portfolio['strategy_returns'] > 0]
            losing_trades = portfolio['strategy_returns'][portfolio['strategy_returns'] < 0]
            total_trades = len(winning_trades) + len(losing_trades)
            win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
            
            metrics = {
                'Total Return (%)': round(total_return, 2),
                'Buy & Hold Return (%)': round(buy_hold_return, 2),
                'Strategy Volatility (%)': round(strategy_volatility, 2),
                'Sharpe Ratio': round(sharpe_ratio, 2),
                'Maximum Drawdown (%)': round(max_drawdown, 2),
                'Win Rate (%)': round(win_rate, 2),
                'Final Portfolio Value': round(portfolio['portfolio_value'].iloc[-1], 2),
                'Allocated Capital': round(initial_capital_symbol, 2)
            }
        
        return metrics
    
    def calculate_enhanced_metrics(self, symbol=None):
        """Calculate enhanced performance metrics including additional risk metrics"""
        base_metrics = self.calculate_metrics(symbol)
        if base_metrics is None:
            return None
        
        if symbol is None:
            # Portfolio enhanced metrics
            portfolio = self.portfolio_results
            returns = portfolio['portfolio_returns']
        else:
            # Individual symbol enhanced metrics
            portfolio = self.results[symbol]
            returns = portfolio['strategy_returns']
        
        # Additional risk metrics
        enhanced_metrics = base_metrics.copy()
        
        # Calmar Ratio (annualized return / maximum drawdown)
        annual_return = returns.mean() * 252
        max_dd = abs(base_metrics['Maximum Drawdown (%)']) / 100
        calmar_ratio = annual_return / max_dd if max_dd > 0 else 0
        enhanced_metrics['Calmar Ratio'] = round(calmar_ratio, 2)
        
        # Sortino Ratio (downside risk-adjusted return)
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        risk_free_rate = 0.02
        excess_returns = annual_return - risk_free_rate
        sortino_ratio = excess_returns / downside_volatility if downside_volatility > 0 else 0
        enhanced_metrics['Sortino Ratio'] = round(sortino_ratio, 2)
        
        # Information Ratio (active return / tracking error)
        # Using buy-and-hold as benchmark
        if symbol is None:
            benchmark_returns = portfolio['buy_hold_returns']
        else:
            benchmark_returns = portfolio['returns']
        
        active_returns = returns - benchmark_returns
        tracking_error = active_returns.std() * np.sqrt(252)
        information_ratio = active_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
        enhanced_metrics['Information Ratio'] = round(information_ratio, 2)
        
        # Profit Factor (total profits / total losses)
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]
        total_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
        total_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        enhanced_metrics['Profit Factor'] = round(profit_factor, 2)
        
        # Average win/loss ratio
        avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        enhanced_metrics['Win/Loss Ratio'] = round(win_loss_ratio, 2)
        
        # Number of trades
        # Count position changes as trades
        if symbol is None:
            signals = portfolio.get('signal', pd.Series([0] * len(portfolio)))
        else:
            signals = portfolio.get('signal', pd.Series([0] * len(portfolio)))
        
        position_changes = signals.diff()
        num_trades = len(position_changes[position_changes != 0])
        enhanced_metrics['Number of Trades'] = num_trades
        
        # Expectancy (average trade outcome)
        expectancy = returns.mean() if len(returns) > 0 else 0
        enhanced_metrics['Expectancy'] = round(expectancy, 4)
        
        return enhanced_metrics
    
    def backtest_individual_strategies(self):
        """Backtest each strategy individually and return comprehensive results"""
        individual_results = {}
        
        strategies = ['mean_reversion', 'momentum', 'breakout', 'range_trading', 
                     'vwap', 'news_based', 'combined', 'sector_rotation', 
                     'pairs_trading', 'multi_timeframe']
        
        for strategy in strategies:
            print(f"\nBacktesting {strategy} strategy...")
            try:
                self.backtest_strategy(strategy)
                metrics = self.calculate_enhanced_metrics()
                if metrics:
                    individual_results[strategy] = metrics
                    print(f"✓ {strategy} completed successfully")
                else:
                    print(f"✗ {strategy} failed to produce results")
            except Exception as e:
                print(f"✗ {strategy} failed with error: {e}")
        
        return individual_results
    
    def validate_strategy_out_of_sample(self, strategy_name, train_ratio=0.7):
        """Validate strategy performance on out-of-sample data"""
        if not self.data:
            print("No data available for validation")
            return None
        
        results = {}
        
        for symbol in self.data.keys():
            try:
                df = self.data[symbol]
                train_size = int(len(df) * train_ratio)
                
                # Split data
                train_data = df.iloc[:train_size]
                test_data = df.iloc[train_size:]
                
                # Backup original data
                original_data = self.data[symbol]
                
                # Train on training data
                self.data[symbol] = train_data
                train_results = self.backtest_strategy(strategy_name)
                train_metrics = self.calculate_enhanced_metrics(symbol)
                
                # Test on out-of-sample data
                self.data[symbol] = test_data
                test_results = self.backtest_strategy(strategy_name)
                test_metrics = self.calculate_enhanced_metrics(symbol)
                
                # Restore original data
                self.data[symbol] = original_data
                
                results[symbol] = {
                    'train_metrics': train_metrics,
                    'test_metrics': test_metrics,
                    'train_size': len(train_data),
                    'test_size': len(test_data)
                }
                
            except Exception as e:
                print(f"Error validating {symbol}: {e}")
                continue
        
        return results
    
    def optimize_strategy_parameters(self, strategy_name, symbol, param_grid, optimization_metric='Sharpe Ratio'):
        """Optimize strategy parameters using grid search"""
        if symbol not in self.data:
            print(f"No data available for {symbol}")
            return None
        
        print(f"Optimizing {strategy_name} strategy for {symbol}...")
        print(f"Optimization metric: {optimization_metric}")
        
        best_params = None
        best_score = float('-inf')
        best_metrics = None
        results = []
        
        # Generate parameter combinations
        param_combinations = []
        param_names = list(param_grid.keys())
        
        def generate_combinations(params, current_combo):
            if len(current_combo) == len(param_names):
                param_combinations.append(current_combo.copy())
                return
            
            param_name = param_names[len(current_combo)]
            for value in param_grid[param_name]:
                current_combo[param_name] = value
                generate_combinations(params, current_combo)
                current_combo.pop(param_name)
        
        generate_combinations(param_grid, {})
        
        print(f"Testing {len(param_combinations)} parameter combinations...")
        
        for i, params in enumerate(param_combinations):
            try:
                # Create a modified strategy with these parameters
                # This is a simplified version - in practice, you'd modify the strategy
                # to accept parameters
                
                # For demonstration, let's assume we're optimizing the mean reversion strategy
                if strategy_name == 'mean_reversion':
                    # Create a custom strategy function with parameters
                    def custom_strategy(symbol_data):
                        df = symbol_data.copy()
                        signals = pd.DataFrame(index=df.index)
                        signals['signal'] = 0
                        
                        # Use parameters from optimization
                        rsi_oversold = params.get('rsi_oversold', 30)
                        rsi_overbought = params.get('rsi_overbought', 70)
                        bb_std = params.get('bb_std', 2.0)
                        
                        # Recalculate Bollinger Bands with custom std
                        bb_period = 20
                        bb_mean = df['Close'].rolling(window=bb_period).mean()
                        bb_std_dev = df['Close'].rolling(window=bb_period).std()
                        bb_upper = bb_mean + (bb_std_dev * bb_std)
                        bb_lower = bb_mean - (bb_std_dev * bb_std)
                        
                        # Buy when price touches lower BB and RSI is oversold
                        buy_condition = (df['Close'] <= bb_lower) & (df['RSI'] < rsi_oversold)
                        
                        # Sell when price touches upper BB and RSI is overbought
                        sell_condition = (df['Close'] >= bb_upper) & (df['RSI'] > rsi_overbought)
                        
                        signals.loc[buy_condition, 'signal'] = 1
                        signals.loc[sell_condition, 'signal'] = -1
                        
                        return signals
                    
                    # Test this parameter combination
                    signals = custom_strategy(self.data[symbol])
                else:
                    # For other strategies, use the default implementation
                    # In practice, you'd modify each strategy to accept parameters
                    continue
                
                # Calculate performance with these parameters
                positions = signals['signal'].diff()
                
                # Initialize portfolio
                portfolio = pd.DataFrame(index=self.data[symbol].index)
                portfolio['price'] = self.data[symbol]['Close']
                portfolio['signal'] = signals['signal']
                portfolio['positions'] = positions
                
                # Calculate returns
                portfolio['returns'] = self.data[symbol]['Close'].pct_change()
                portfolio['strategy_returns'] = portfolio['returns'] * portfolio['signal'].shift(1)
                
                # Calculate cumulative returns
                portfolio['cum_returns'] = (1 + portfolio['returns']).cumprod()
                portfolio['cum_strategy_returns'] = (1 + portfolio['strategy_returns']).cumprod()
                
                # Calculate metrics
                total_return = (portfolio['cum_strategy_returns'].iloc[-1] - 1) * 100
                strategy_volatility = portfolio['strategy_returns'].std() * np.sqrt(252) * 100
                
                # Sharpe ratio
                risk_free_rate = 0.02
                excess_returns = portfolio['strategy_returns'].mean() * 252 - risk_free_rate
                sharpe_ratio = excess_returns / (strategy_volatility / 100) if strategy_volatility > 0 else 0
                
                # Maximum drawdown
                cumulative = portfolio['cum_strategy_returns']
                rolling_max = cumulative.expanding().max()
                drawdown = (cumulative - rolling_max) / rolling_max
                max_drawdown = drawdown.min() * 100
                
                metrics = {
                    'Total Return (%)': round(total_return, 2),
                    'Strategy Volatility (%)': round(strategy_volatility, 2),
                    'Sharpe Ratio': round(sharpe_ratio, 2),
                    'Maximum Drawdown (%)': round(max_drawdown, 2),
                    'Parameters': params
                }
                
                # Check if this is the best so far
                if optimization_metric in metrics:
                    score = metrics[optimization_metric]
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
                        best_metrics = metrics.copy()
                
                results.append(metrics)
                
                if (i + 1) % 10 == 0:
                    print(f"Completed {i + 1}/{len(param_combinations)} combinations")
                
            except Exception as e:
                print(f"Error with parameters {params}: {e}")
                continue
        
        if best_params:
            print(f"\nBest parameters found:")
            for param, value in best_params.items():
                print(f"  {param}: {value}")
            print(f"Best {optimization_metric}: {best_score}")
        
        return {
            'best_params': best_params,
            'best_metrics': best_metrics,
            'all_results': results
        }
    
    def create_mock_data(self, symbols, days=30, interval_minutes=5):
        """Create mock data for testing when real data is not available"""
        print(f"Creating mock data for {len(symbols)} symbols...")
        
        # Generate time index
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Create time index based on interval
        time_index = pd.date_range(start=start_time, end=end_time, freq=f'{interval_minutes}T')
        
        for symbol in symbols:
            # Generate realistic price data
            np.random.seed(42 + hash(symbol) % 1000)  # Consistent but different for each symbol
            
            # Starting price
            base_price = np.random.uniform(100, 200)
            
            # Generate more realistic returns
            returns = np.random.normal(0, 0.005, len(time_index))  # Lower volatility
            
            # Add some trend and volatility clustering
            trend = np.linspace(0, np.random.normal(0, 0.02), len(time_index))  # Smaller trend
            volatility = np.abs(np.random.normal(0.005, 0.002, len(time_index)))  # Lower volatility
            
            returns = returns * volatility + trend
            
            # Calculate prices
            prices = base_price * np.exp(np.cumsum(returns))
            
            # Generate OHLC data
            noise = np.random.normal(0, 0.002, len(time_index))  # Small noise
            opens = prices * (1 + noise)
            highs = prices * (1 + np.abs(noise) * 0.5)
            lows = prices * (1 - np.abs(noise) * 0.5)
            closes = prices
            
            # Ensure High >= Low and prices are within bounds
            highs = np.maximum(highs, closes)
            highs = np.maximum(highs, opens)
            lows = np.minimum(lows, closes)
            lows = np.minimum(lows, opens)
            
            # Generate volume with more realistic distribution
            base_volume = np.random.uniform(1000000, 5000000)
            volume = base_volume * np.random.lognormal(0, 0.3, len(time_index))
            
            # Create DataFrame
            df = pd.DataFrame({
                'Open': opens,
                'High': highs,
                'Low': lows,
                'Close': closes,
                'Volume': volume.astype(int)
            }, index=time_index)
            
            # Ensure no negative prices
            df = df.abs()
            
            self.data[symbol] = df
        
        print(f"Mock data created for {len(self.data)} symbols")
        return True
    
    def plot_results(self, show_individual=True):
        """Plot backtest results"""
        if self.portfolio_results is None:
            print("No portfolio results available.")
            return
        
        n_symbols = len(self.data)
        n_plots = 2 if not show_individual else 2 + n_symbols
        
        fig, axes = plt.subplots(n_plots, 1, figsize=(15, 6 * n_plots))
        if n_plots == 1:
            axes = [axes]
        
        plot_idx = 0
        
        # Portfolio performance
        axes[plot_idx].plot(self.portfolio_results.index, self.portfolio_results['portfolio_value'], 
                           label='Portfolio Strategy', linewidth=2)
        axes[plot_idx].plot(self.portfolio_results.index, self.portfolio_results['buy_hold_value'], 
                           label='Buy & Hold', linewidth=2, alpha=0.7)
        axes[plot_idx].axhline(y=self.initial_capital, color='black', linestyle='--', 
                              label='Initial Capital', alpha=0.5)
        axes[plot_idx].set_title('Multi-Symbol Portfolio Performance')
        axes[plot_idx].set_ylabel('Portfolio Value ($)')
        axes[plot_idx].legend()
        axes[plot_idx].grid(True, alpha=0.3)
        plot_idx += 1
        
        # Portfolio cumulative returns
        axes[plot_idx].plot(self.portfolio_results.index, self.portfolio_results['cum_portfolio_returns'], 
                           label='Portfolio Strategy', linewidth=2)
        axes[plot_idx].plot(self.portfolio_results.index, 
                           self.portfolio_results['buy_hold_value'] / self.initial_capital, 
                           label='Buy & Hold', linewidth=2, alpha=0.7)
        axes[plot_idx].set_title('Portfolio Cumulative Returns')
        axes[plot_idx].set_ylabel('Cumulative Returns')
        axes[plot_idx].legend()
        axes[plot_idx].grid(True, alpha=0.3)
        plot_idx += 1
        
        # Individual symbol performance
        if show_individual:
            for symbol in self.data.keys():
                if symbol in self.results:
                    portfolio = self.results[symbol]
                    
                    # Price and signals
                    axes[plot_idx].plot(portfolio.index, portfolio['price'], 
                                       label='Price', alpha=0.7)
                    
                    buy_signals = portfolio[portfolio['positions'] == 1]
                    sell_signals = portfolio[portfolio['positions'] == -1]
                    
                    axes[plot_idx].scatter(buy_signals.index, buy_signals['price'], 
                                          color='green', marker='^', s=50, label='Buy', alpha=0.7)
                    axes[plot_idx].scatter(sell_signals.index, sell_signals['price'], 
                                          color='red', marker='v', s=50, label='Sell', alpha=0.7)
                    
                    axes[plot_idx].set_title(f'{symbol} - Price and Trading Signals')
                    axes[plot_idx].set_ylabel('Price')
                    axes[plot_idx].legend()
                    axes[plot_idx].grid(True, alpha=0.3)
                    plot_idx += 1
        
        plt.tight_layout()
        plt.show()
    
    def plot_correlation_matrix(self):
        """Plot correlation matrix of all symbols"""
        if len(self.data) < 2:
            print("Need at least 2 symbols to plot correlation matrix")
            return
        
        # Create correlation matrix
        closes = pd.DataFrame()
        for symbol in self.data.keys():
            closes[symbol] = self.data[symbol]['Close']
        
        correlation_matrix = closes.corr()
        
        # Plot heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, fmt='.2f')
        plt.title('Stock Price Correlation Matrix')
        plt.tight_layout()
        plt.show()
        
        return correlation_matrix
    
    def run_all_strategies(self):
        """Run and compare all strategies"""
        strategies = ['mean_reversion', 'momentum', 'combined', 'sector_rotation', 
                     'pairs_trading', 'multi_timeframe', 'breakout', 'range_trading', 
                     'vwap', 'news_based', 'voting']
        results_summary = {}
        
        for strategy in strategies:
            print(f"\n{'='*50}")
            print(f"Testing {strategy.upper()} Strategy")
            print('='*50)
            
            try:
                self.backtest_strategy(strategy)
                metrics = self.calculate_metrics()
                if metrics:
                    results_summary[strategy] = metrics
                    
                    print(f"Portfolio Results for {strategy}:")
                    for key, value in metrics.items():
                        print(f"{key}: {value}")
                    
                    # Show individual symbol performance
                    print(f"\nIndividual Symbol Performance:")
                    for symbol in self.data.keys():
                        symbol_metrics = self.calculate_metrics(symbol)
                        if symbol_metrics:
                            print(f"{symbol}: {symbol_metrics['Total Return (%)']}% return")
                
            except Exception as e:
                print(f"Error testing {strategy}: {e}")
                continue
        
        # Create comparison DataFrame
        if results_summary:
            comparison_df = pd.DataFrame(results_summary).T
            print(f"\n{'='*50}")
            print("STRATEGY COMPARISON")
            print('='*50)
            print(comparison_df)
            
            return comparison_df
        else:
            print("No successful strategy results to compare")
            return None
    
    def get_symbol_summary(self):
        """Get summary statistics for all symbols"""
        if not self.data:
            print("No data available")
            return None
        
        summary = {}
        for symbol in self.data.keys():
            data = self.data[symbol]
            summary[symbol] = {
                'Current Price': round(data['Close'].iloc[-1], 2),
                'Daily Return (%)': round(data['Price_change'].iloc[-1] * 100, 2),
                'Volatility (%)': round(data['Volatility'].iloc[-1], 2),
                'RSI': round(data['RSI'].iloc[-1], 2),
                'Volume Ratio': round(data['Volume_ratio'].iloc[-1], 2),
                'Allocated Capital': round(self.capital_allocation[symbol], 2)
            }
        
        summary_df = pd.DataFrame(summary).T
        print("Symbol Summary:")
        print(summary_df)
        return summary_df

# Example usage with rate limiting fixes
if __name__ == "__main__":
    # Initialize multi-symbol trading algorithm
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    trader = MultiSymbolDayTradingAlgo(symbols, initial_capital=50000)
    
    # Method 1: Try alternative bulk download (recommended)
    print("Trying alternative bulk download method...")
    if trader.fetch_data_alternative(period='5d', interval='5m'):
        success = True
    else:
        print("Alternative method failed, trying sequential fetching...")
        # Method 2: Sequential fetching with delays
        success = trader.fetch_data(period='5d', interval='5m', sequential=True)
    
    if not success:
        print("Falling back to smaller dataset...")
        # Method 3: Try with fewer symbols and longer intervals
        trader = MultiSymbolDayTradingAlgo(['AAPL', 'MSFT'], initial_capital=50000)
        success = trader.fetch_data(period='5d', interval='15m', sequential=True)
    
    if success:
        # Calculate technical indicators
        trader.calculate_indicators()
        
        # Show symbol summary
        trader.get_symbol_summary()
        
        # Plot correlation matrix (if multiple symbols)
        if len(trader.data) > 1:
            trader.plot_correlation_matrix()
        
        # Run all strategies and compare
        comparison = trader.run_all_strategies()
        
        if comparison is not None:
            # Test the best performing strategy
            best_strategy = comparison['Total Return (%)'].idxmax()
            print(f"\nBest performing strategy: {best_strategy}")
            
            # Run detailed analysis on best strategy
            trader.backtest_strategy(best_strategy)
            trader.plot_results(show_individual=True)
            
            # Print detailed portfolio metrics
            print("\nDetailed Portfolio Metrics:")
            portfolio_metrics = trader.calculate_metrics()
            for key, value in portfolio_metrics.items():
                print(f"{key}: {value}")
    else:
        print("Failed to fetch data. Please try again later or use fewer symbols.")
        print("Tips to avoid rate limiting:")
        print("1. Use longer intervals (15m, 30m, 1h instead of 5m)")
        print("2. Use shorter periods (1d, 5d instead of 1mo)")
        print("3. Use fewer symbols at once")
        print("4. Add delays between requests")
