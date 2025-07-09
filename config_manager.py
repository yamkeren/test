"""
Configuration management for the trading framework

This module handles:
- Environment variable loading
- Secure credential storage
- Configuration validation
- Default settings
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IBKRCredentials:
    """Interactive Brokers credentials and connection settings"""
    host: str = '127.0.0.1'
    port: int = 7497  # Paper trading port (7496 for live)
    client_id: int = 1
    paper_trading: bool = True
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'IBKRCredentials':
        """Create credentials from environment variables"""
        return cls(
            host=os.getenv('IBKR_HOST', '127.0.0.1'),
            port=int(os.getenv('IBKR_PORT', '7497')),
            client_id=int(os.getenv('IBKR_CLIENT_ID', '1')),
            paper_trading=os.getenv('IBKR_PAPER_TRADING', 'True').lower() == 'true',
            timeout=int(os.getenv('IBKR_TIMEOUT', '30'))
        )


@dataclass
class TradingConfig:
    """Main trading configuration"""
    # Data source settings
    data_source: str = 'yfinance'  # 'yfinance' or 'ibkr'
    
    # Trading settings
    initial_capital: float = 50000.0
    max_position_size: float = 0.1  # 10% of portfolio per position
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    
    # Risk management
    max_daily_loss: float = 0.02  # 2% max daily loss
    max_total_positions: int = 10
    
    # Strategy settings
    default_strategy: str = 'combined'
    strategy_voting_threshold: float = 0.5  # 50% agreement needed
    
    # Data settings
    default_period: str = '5d'
    default_interval: str = '5m'
    
    # Backtesting settings
    commission_pct: float = 0.001  # 0.1% commission
    slippage_pct: float = 0.001  # 0.1% slippage
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """Create configuration from environment variables"""
        return cls(
            data_source=os.getenv('TRADING_DATA_SOURCE', 'yfinance'),
            initial_capital=float(os.getenv('TRADING_INITIAL_CAPITAL', '50000.0')),
            max_position_size=float(os.getenv('TRADING_MAX_POSITION_SIZE', '0.1')),
            stop_loss_pct=float(os.getenv('TRADING_STOP_LOSS_PCT', '0.05')),
            take_profit_pct=float(os.getenv('TRADING_TAKE_PROFIT_PCT', '0.10')),
            max_daily_loss=float(os.getenv('TRADING_MAX_DAILY_LOSS', '0.02')),
            max_total_positions=int(os.getenv('TRADING_MAX_TOTAL_POSITIONS', '10')),
            default_strategy=os.getenv('TRADING_DEFAULT_STRATEGY', 'combined'),
            strategy_voting_threshold=float(os.getenv('TRADING_VOTING_THRESHOLD', '0.5')),
            default_period=os.getenv('TRADING_DEFAULT_PERIOD', '5d'),
            default_interval=os.getenv('TRADING_DEFAULT_INTERVAL', '5m'),
            commission_pct=float(os.getenv('TRADING_COMMISSION_PCT', '0.001')),
            slippage_pct=float(os.getenv('TRADING_SLIPPAGE_PCT', '0.001'))
        )


class ConfigManager:
    """Configuration manager for the trading framework"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / '.trading_framework'
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / 'config.json'
        self.credentials_file = self.config_dir / 'credentials.json'
        
        # Load configurations
        self.trading_config = self._load_trading_config()
        self.ibkr_credentials = self._load_ibkr_credentials()
    
    def _load_trading_config(self) -> TradingConfig:
        """Load trading configuration"""
        # Try to load from file first
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    return TradingConfig(**config_data)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
        
        # Fall back to environment variables
        config = TradingConfig.from_env()
        self._save_trading_config(config)
        return config
    
    def _load_ibkr_credentials(self) -> IBKRCredentials:
        """Load IBKR credentials"""
        # Try to load from file first
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                    return IBKRCredentials(**creds_data)
            except Exception as e:
                logger.warning(f"Failed to load credentials file: {e}")
        
        # Fall back to environment variables
        creds = IBKRCredentials.from_env()
        self._save_ibkr_credentials(creds)
        return creds
    
    def _save_trading_config(self, config: TradingConfig):
        """Save trading configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _save_ibkr_credentials(self, credentials: IBKRCredentials):
        """Save IBKR credentials to file"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(asdict(credentials), f, indent=2)
            # Set restrictive permissions
            os.chmod(self.credentials_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def update_trading_config(self, **kwargs):
        """Update trading configuration
        
        Args:
            **kwargs: Configuration parameters to update
        """
        config_dict = asdict(self.trading_config)
        config_dict.update(kwargs)
        self.trading_config = TradingConfig(**config_dict)
        self._save_trading_config(self.trading_config)
    
    def update_ibkr_credentials(self, **kwargs):
        """Update IBKR credentials
        
        Args:
            **kwargs: Credential parameters to update
        """
        creds_dict = asdict(self.ibkr_credentials)
        creds_dict.update(kwargs)
        self.ibkr_credentials = IBKRCredentials(**creds_dict)
        self._save_ibkr_credentials(self.ibkr_credentials)
    
    def get_config(self) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return {
            'trading': asdict(self.trading_config),
            'ibkr': asdict(self.ibkr_credentials)
        }
    
    def validate_config(self) -> bool:
        """Validate configuration settings"""
        try:
            # Validate trading config
            assert 0 < self.trading_config.max_position_size <= 1, "max_position_size must be between 0 and 1"
            assert 0 < self.trading_config.stop_loss_pct <= 1, "stop_loss_pct must be between 0 and 1"
            assert 0 < self.trading_config.take_profit_pct <= 1, "take_profit_pct must be between 0 and 1"
            assert 0 < self.trading_config.max_daily_loss <= 1, "max_daily_loss must be between 0 and 1"
            assert self.trading_config.max_total_positions > 0, "max_total_positions must be positive"
            assert 0 < self.trading_config.strategy_voting_threshold <= 1, "strategy_voting_threshold must be between 0 and 1"
            assert self.trading_config.initial_capital > 0, "initial_capital must be positive"
            
            # Validate IBKR credentials
            assert 1024 <= self.ibkr_credentials.port <= 65535, "Port must be between 1024 and 65535"
            assert self.ibkr_credentials.client_id > 0, "client_id must be positive"
            assert self.ibkr_credentials.timeout > 0, "timeout must be positive"
            
            return True
            
        except AssertionError as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def create_sample_env_file(self, filepath: str = None):
        """Create a sample .env file with all configuration options
        
        Args:
            filepath: Path to save the .env file (default: .env.sample)
        """
        if filepath is None:
            filepath = self.config_dir / '.env.sample'
        
        sample_content = """
# Trading Framework Configuration
# Copy this file to .env and update with your settings

# Data Source Configuration
TRADING_DATA_SOURCE=yfinance  # 'yfinance' or 'ibkr'

# Trading Configuration
TRADING_INITIAL_CAPITAL=50000.0
TRADING_MAX_POSITION_SIZE=0.1  # 10% of portfolio per position
TRADING_STOP_LOSS_PCT=0.05     # 5% stop loss
TRADING_TAKE_PROFIT_PCT=0.10   # 10% take profit

# Risk Management
TRADING_MAX_DAILY_LOSS=0.02    # 2% max daily loss
TRADING_MAX_TOTAL_POSITIONS=10

# Strategy Configuration
TRADING_DEFAULT_STRATEGY=combined
TRADING_VOTING_THRESHOLD=0.5   # 50% agreement needed for voting

# Data Settings
TRADING_DEFAULT_PERIOD=5d
TRADING_DEFAULT_INTERVAL=5m

# Backtesting Settings
TRADING_COMMISSION_PCT=0.001   # 0.1% commission
TRADING_SLIPPAGE_PCT=0.001     # 0.1% slippage

# Interactive Brokers Configuration
IBKR_HOST=127.0.0.1
IBKR_PORT=7497                 # 7497 for paper trading, 7496 for live
IBKR_CLIENT_ID=1
IBKR_PAPER_TRADING=True        # IMPORTANT: Set to False for live trading
IBKR_TIMEOUT=30
"""
        
        try:
            with open(filepath, 'w') as f:
                f.write(sample_content.strip())
            logger.info(f"Sample .env file created at {filepath}")
        except Exception as e:
            logger.error(f"Failed to create sample .env file: {e}")


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager"""
    return config_manager


def load_env_file(filepath: str = '.env'):
    """Load environment variables from file
    
    Args:
        filepath: Path to the .env file
    """
    if not os.path.exists(filepath):
        logger.warning(f"Environment file {filepath} not found")
        return
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        logger.info(f"Environment variables loaded from {filepath}")
    except Exception as e:
        logger.error(f"Failed to load environment file: {e}")


# Auto-load .env file if it exists
if os.path.exists('.env'):
    load_env_file()