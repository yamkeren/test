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
            
            # VWAP (Volume Weighted Average Price)
            df['VWAP'] = self.calculate_vwap(df)
            
            # Support and Resistance levels
            df['Support'], df['Resistance'] = self.calculate_support_resistance(df['Close'])
            
            # Average True Range (ATR) for volatility-based strategies
            df['ATR'] = self.calculate_atr(df)
            
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
    
    def calculate_vwap(self, df, period=20):
        """Calculate Volume Weighted Average Price"""
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        vwap = (typical_price * df['Volume']).rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()
        return vwap
    
    def calculate_support_resistance(self, prices, window=20):
        """Calculate dynamic support and resistance levels"""
        support = prices.rolling(window=window).min()
        resistance = prices.rolling(window=window).max()
        return support, resistance
    
    def calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def breakout_trading_strategy(self, symbol):
        """Breakout trading strategy - buy when price crosses resistance, sell when it breaks support"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy when price breaks above resistance with volume confirmation
        breakout_up = (df['Close'] > df['Resistance'].shift(1)) & (df['Volume_ratio'] > 1.3) & (df['RSI'] < 80)
        
        # Sell when price breaks below support
        breakout_down = (df['Close'] < df['Support'].shift(1)) | (df['RSI'] > 85)
        
        signals.loc[breakout_up, 'signal'] = 1
        signals.loc[breakout_down, 'signal'] = -1
        
        return signals
    
    def range_trading_strategy(self, symbol):
        """Range trading strategy - trade within a price range based on support and resistance"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Calculate range boundaries
        range_top = df['Resistance'] - 0.01 * df['Close']  # Slightly below resistance
        range_bottom = df['Support'] + 0.01 * df['Close']  # Slightly above support
        
        # Buy near support when RSI is oversold
        buy_condition = (df['Close'] <= range_bottom) & (df['RSI'] < 40) & (df['Volume_ratio'] > 1.1)
        
        # Sell near resistance when RSI is overbought
        sell_condition = (df['Close'] >= range_top) & (df['RSI'] > 60)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def vwap_trading_strategy(self, symbol):
        """VWAP trading strategy - use Volume Weighted Average Price to guide buy/sell decisions"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Buy when price is below VWAP and showing upward momentum
        buy_condition = (df['Close'] < df['VWAP']) & (df['SMA_5'] > df['SMA_10']) & (df['Volume_ratio'] > 1.2) & (df['RSI'] < 70)
        
        # Sell when price is above VWAP and momentum is weakening
        sell_condition = (df['Close'] > df['VWAP']) & (df['SMA_5'] < df['SMA_10']) | (df['RSI'] > 80)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def news_based_trading_strategy(self, symbol):
        """News-based trading strategy - incorporate trading decisions based on market sentiment indicators"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Since we don't have real news data, we'll use volatility and volume spikes as proxies
        # High volume + high volatility = potential news impact
        
        # Calculate volatility spike
        volatility_spike = df['Volatility'] > df['Volatility'].rolling(window=20).mean() * 1.5
        
        # High volume + positive momentum = potential good news
        good_news_proxy = volatility_spike & (df['Volume_ratio'] > 2.0) & (df['Price_momentum'] > 0.02)
        
        # High volume + negative momentum = potential bad news
        bad_news_proxy = volatility_spike & (df['Volume_ratio'] > 2.0) & (df['Price_momentum'] < -0.02)
        
        # Buy on good news proxy with confirmation
        buy_condition = good_news_proxy & (df['RSI'] < 75) & (df['MACD'] > df['MACD_signal'])
        
        # Sell on bad news proxy or when momentum fades
        sell_condition = bad_news_proxy | (df['RSI'] > 85)
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
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
        """Combined strategy using voting mechanism from all individual strategies"""
        df = self.data[symbol].copy()
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0
        
        # Get signals from all individual strategies
        strategy_methods = [
            self.mean_reversion_strategy,
            self.momentum_strategy,
            self.breakout_trading_strategy,
            self.range_trading_strategy,
            self.vwap_trading_strategy,
            self.news_based_trading_strategy
        ]
        
        # Collect votes from each strategy
        votes = pd.DataFrame(index=df.index)
        
        for i, strategy_method in enumerate(strategy_methods):
            try:
                strategy_signals = strategy_method(symbol)
                votes[f'strategy_{i}'] = strategy_signals['signal']
            except Exception as e:
                # If a strategy fails, fill with neutral votes (0)
                votes[f'strategy_{i}'] = 0
                print(f"Strategy {i} failed for {symbol}: {e}")
        
        # Implement majority voting
        # Count buy votes (1), sell votes (-1), and hold votes (0)
        buy_votes = (votes == 1).sum(axis=1)
        sell_votes = (votes == -1).sum(axis=1)
        hold_votes = (votes == 0).sum(axis=1)
        
        # Determine final signal based on majority vote
        # Need more than 50% agreement for action
        total_strategies = len(strategy_methods)
        majority_threshold = total_strategies // 2
        
        # Buy when majority of strategies vote buy
        buy_condition = buy_votes > majority_threshold
        
        # Sell when majority of strategies vote sell
        sell_condition = sell_votes > majority_threshold
        
        signals.loc[buy_condition, 'signal'] = 1
        signals.loc[sell_condition, 'signal'] = -1
        
        return signals
    
    def combined_strategy_legacy(self, symbol):
        """Legacy combined strategy using score-based approach (kept for comparison)"""
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
            'combined_legacy': self.combined_strategy_legacy,
            'sector_rotation': self.sector_rotation_strategy,
            'pairs_trading': self.pairs_trading_strategy,
            'multi_timeframe': self.multi_timeframe_strategy,
            'breakout': self.breakout_trading_strategy,
            'range': self.range_trading_strategy,
            'vwap': self.vwap_trading_strategy,
            'news_based': self.news_based_trading_strategy
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
                     'pairs_trading', 'multi_timeframe', 'breakout', 'range', 'vwap', 'news_based']
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
    
    def optimize_strategy_parameters(self, strategy_name, param_grid, metric='Total Return (%)'):
        """
        Optimize strategy parameters using grid search
        
        Args:
            strategy_name: Name of the strategy to optimize
            param_grid: Dictionary of parameter ranges to test
            metric: Metric to optimize for
        """
        print(f"Optimizing {strategy_name} strategy parameters...")
        
        if not self.data:
            print("No data available for optimization")
            return None
        
        from itertools import product
        
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))
        
        best_params = None
        best_score = float('-inf')
        results = []
        
        for params in param_combinations:
            param_dict = dict(zip(param_names, params))
            
            try:
                # Temporarily modify strategy parameters
                original_params = self._get_strategy_params(strategy_name)
                self._set_strategy_params(strategy_name, param_dict)
                
                # Run backtest
                self.backtest_strategy(strategy_name)
                metrics = self.calculate_metrics()
                
                if metrics and metric in metrics:
                    score = metrics[metric]
                    results.append({
                        'params': param_dict,
                        'score': score,
                        'metrics': metrics
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_params = param_dict
                
                # Restore original parameters
                self._set_strategy_params(strategy_name, original_params)
                
            except Exception as e:
                print(f"Error testing parameters {param_dict}: {e}")
                continue
        
        if best_params:
            print(f"Best parameters for {strategy_name}: {best_params}")
            print(f"Best {metric}: {best_score}")
            
            # Set best parameters
            self._set_strategy_params(strategy_name, best_params)
            
            return {
                'best_params': best_params,
                'best_score': best_score,
                'all_results': results
            }
        else:
            print("No valid parameter combinations found")
            return None
    
    def _get_strategy_params(self, strategy_name):
        """Get current parameters for a strategy (placeholder for now)"""
        # This would need to be implemented based on the specific strategy
        # For now, return empty dict
        return {}
    
    def _set_strategy_params(self, strategy_name, params):
        """Set parameters for a strategy (placeholder for now)"""
        # This would need to be implemented based on the specific strategy
        # For now, do nothing
        pass
    
    def validate_out_of_sample(self, strategy_name, train_ratio=0.7):
        """
        Validate strategy on out-of-sample data
        
        Args:
            strategy_name: Name of the strategy to validate
            train_ratio: Proportion of data to use for training
        """
        print(f"Validating {strategy_name} strategy with out-of-sample data...")
        
        if not self.data:
            print("No data available for validation")
            return None
        
        # Store original results
        original_results = self.results.copy()
        original_portfolio = self.portfolio_results
        
        validation_results = {}
        
        for symbol in self.data.keys():
            df = self.data[symbol].copy()
            
            # Split data
            split_idx = int(len(df) * train_ratio)
            train_data = df.iloc[:split_idx]
            test_data = df.iloc[split_idx:]
            
            # Train on in-sample data
            self.data[symbol] = train_data
            self.backtest_strategy(strategy_name)
            train_metrics = self.calculate_metrics()
            
            # Test on out-of-sample data
            self.data[symbol] = test_data
            self.backtest_strategy(strategy_name)
            test_metrics = self.calculate_metrics()
            
            # Restore original data
            self.data[symbol] = df
            
            validation_results[symbol] = {
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'train_period': f"{train_data.index[0]} to {train_data.index[-1]}",
                'test_period': f"{test_data.index[0]} to {test_data.index[-1]}"
            }
        
        # Restore original results
        self.results = original_results
        self.portfolio_results = original_portfolio
        
        # Print validation summary
        print("\nOut-of-Sample Validation Results:")
        print("=" * 50)
        
        for symbol, results in validation_results.items():
            print(f"\n{symbol}:")
            if results['train_metrics'] and results['test_metrics']:
                train_return = results['train_metrics']['Total Return (%)']
                test_return = results['test_metrics']['Total Return (%)']
                print(f"  Train Return: {train_return}%")
                print(f"  Test Return: {test_return}%")
                print(f"  Performance Consistency: {'Good' if abs(train_return - test_return) < 10 else 'Poor'}")
        
        return validation_results

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
