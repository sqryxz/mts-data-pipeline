import os
from typing import Optional, List
from dotenv import load_dotenv
from enum import Enum

# Load environment variables from .env file
load_dotenv()


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class Config:
    """Production-ready configuration class that loads settings from environment variables."""
    
    def __init__(self):
        # Environment Configuration
        self.ENVIRONMENT = Environment(os.getenv('ENVIRONMENT', 'development'))
        self.DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # API Configuration
        self.COINGECKO_BASE_URL = os.getenv('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3')
        self.FRED_API_KEY = os.getenv('FRED_API_KEY', '')
        self.REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '50'))
        
        # Database Configuration
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/crypto_data.db')
        self.DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
        self.DATABASE_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', '30'))
        
        # Signal Generation Configuration
        self.SIGNAL_GENERATION_INTERVAL_MINUTES = int(os.getenv('SIGNAL_GENERATION_INTERVAL_MINUTES', '60'))
        self.DATA_COLLECTION_INTERVAL_MINUTES = int(os.getenv('DATA_COLLECTION_INTERVAL_MINUTES', '30'))
        self.MACRO_DATA_COLLECTION_INTERVAL_HOURS = int(os.getenv('MACRO_DATA_COLLECTION_INTERVAL_HOURS', '6'))
        
        # Strategy Configuration
        self.STRATEGY_CONFIG_DIR = os.getenv('STRATEGY_CONFIG_DIR', 'config/strategies')
        self.ENABLED_STRATEGIES = self._parse_list(os.getenv('ENABLED_STRATEGIES', 'vix_correlation,mean_reversion'))
        self.STRATEGY_WEIGHTS = self._parse_strategy_weights()
        
        # API Server Configuration
        self.API_HOST = os.getenv('API_HOST', '0.0.0.0')
        self.API_PORT = int(os.getenv('API_PORT', '8000'))
        self.API_WORKERS = int(os.getenv('API_WORKERS', '4'))
        self.API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-key-change-in-production')
        self.API_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('API_ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))
        
        # Redis Configuration (for caching and message queue)
        self.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.REDIS_CACHE_TTL = int(os.getenv('REDIS_CACHE_TTL', '3600'))  # 1 hour
        self.REDIS_SIGNAL_TTL = int(os.getenv('REDIS_SIGNAL_TTL', '86400'))  # 24 hours
        
        # Real-Time Data Configuration
        self._setup_realtime_config()
        
        # Monitoring Configuration
        self.ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self.METRICS_PORT = int(os.getenv('METRICS_PORT', '8001'))
        self.HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', '60'))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = os.getenv('LOG_FORMAT', 'json' if self.ENVIRONMENT == Environment.PRODUCTION else 'text')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/mts_pipeline.log')
        
        # Alert Configuration
        self.ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'false').lower() == 'true'
        self.ALERT_EMAIL_SMTP_SERVER = os.getenv('ALERT_EMAIL_SMTP_SERVER', '')
        self.ALERT_EMAIL_SMTP_PORT = int(os.getenv('ALERT_EMAIL_SMTP_PORT', '587'))
        self.ALERT_EMAIL_USERNAME = os.getenv('ALERT_EMAIL_USERNAME', '')
        self.ALERT_EMAIL_PASSWORD = os.getenv('ALERT_EMAIL_PASSWORD', '')
        self.ALERT_EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM', '')
        self.ALERT_EMAIL_TO = self._parse_list(os.getenv('ALERT_EMAIL_TO', ''))
        
        # Discord Webhook Configuration
        self.DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
        self.DISCORD_ALERTS_ENABLED = os.getenv('DISCORD_ALERTS_ENABLED', 'false').lower() == 'true'
        self.DISCORD_MIN_CONFIDENCE = float(os.getenv('DISCORD_MIN_CONFIDENCE', '0.6'))
        self.DISCORD_MIN_STRENGTH = os.getenv('DISCORD_MIN_STRENGTH', 'WEAK')
        self.DISCORD_RATE_LIMIT_SECONDS = int(os.getenv('DISCORD_RATE_LIMIT_SECONDS', '60'))
        
        # Risk Management
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.10'))  # 10%
        self.MAX_DAILY_TRADES = int(os.getenv('MAX_DAILY_TRADES', '50'))
        self.MAX_PORTFOLIO_RISK = float(os.getenv('MAX_PORTFOLIO_RISK', '0.25'))
        
        # Backtest Configuration
        self.BACKTEST_DEFAULT_START_DATE = os.getenv('BACKTEST_DEFAULT_START_DATE', '2023-01-01')
        self.BACKTEST_DEFAULT_PORTFOLIO_SIZE = float(os.getenv('BACKTEST_DEFAULT_PORTFOLIO_SIZE', '100000'))
        
        # Validate required settings
        self._validate_config()

    def _setup_realtime_config(self):
        """Setup comprehensive real-time configuration"""
        # Real-Time Collection Settings
        self.REALTIME_ENABLED = os.getenv('REALTIME_ENABLED', 'true').lower() == 'true'
        self.REALTIME_SYMBOLS = self._parse_list(os.getenv('REALTIME_SYMBOLS', 'BTCUSDT,ETHUSDT,XRPUSDT,TAOUSDT,FETUSDT,AGIXUSDT,RNDRUSDT,OCEANUSDT'))
        self.REALTIME_EXCHANGES = self._parse_list(os.getenv('REALTIME_EXCHANGES', 'binance'))
        
        # Order Book Configuration
        self.ORDERBOOK_DEPTH_LEVELS = int(os.getenv('ORDERBOOK_DEPTH_LEVELS', '10'))
        self.ORDERBOOK_UPDATE_FREQUENCY = int(os.getenv('ORDERBOOK_UPDATE_FREQUENCY', '100'))  # milliseconds
        self.ORDERBOOK_REDIS_TTL = int(os.getenv('ORDERBOOK_REDIS_TTL', '3600'))  # 1 hour
        self.ORDERBOOK_BATCH_SIZE = int(os.getenv('ORDERBOOK_BATCH_SIZE', '100'))
        self.ORDERBOOK_CSV_BACKUP = os.getenv('ORDERBOOK_CSV_BACKUP', 'true').lower() == 'true'
        
        # Funding Rate Configuration
        self.FUNDING_COLLECTION_INTERVAL = int(os.getenv('FUNDING_COLLECTION_INTERVAL', '300'))  # 5 minutes
        self.FUNDING_BATCH_SIZE = int(os.getenv('FUNDING_BATCH_SIZE', '50'))
        self.FUNDING_CSV_BACKUP = os.getenv('FUNDING_CSV_BACKUP', 'true').lower() == 'true'
        
        # Arbitrage Configuration
        self.ARBITRAGE_MIN_RATE_DIFF = float(os.getenv('ARBITRAGE_MIN_RATE_DIFF', '0.0001'))  # 0.01%
        self.ARBITRAGE_MIN_PROFIT_BPS = int(os.getenv('ARBITRAGE_MIN_PROFIT_BPS', '5'))  # 5 basis points
        self.SPREAD_ARBITRAGE_THRESHOLD = float(os.getenv('SPREAD_ARBITRAGE_THRESHOLD', '0.001'))  # 0.1%
        
        # Validation Thresholds
        self.MAX_SPREAD_PERCENTAGE = float(os.getenv('MAX_SPREAD_PERCENTAGE', '5.0'))  # 5%
        self.MIN_ORDER_QUANTITY = float(os.getenv('MIN_ORDER_QUANTITY', '0.001'))
        
        # WebSocket Configuration
        self.WEBSOCKET_RECONNECT_ATTEMPTS = int(os.getenv('WEBSOCKET_RECONNECT_ATTEMPTS', '5'))
        self.WEBSOCKET_RECONNECT_DELAY = float(os.getenv('WEBSOCKET_RECONNECT_DELAY', '1.0'))
        self.WEBSOCKET_MAX_RECONNECT_DELAY = float(os.getenv('WEBSOCKET_MAX_RECONNECT_DELAY', '60.0'))
        self.WEBSOCKET_PING_INTERVAL = int(os.getenv('WEBSOCKET_PING_INTERVAL', '30'))
        self.WEBSOCKET_CONNECTION_TIMEOUT = int(os.getenv('WEBSOCKET_CONNECTION_TIMEOUT', '10'))
        self.WEBSOCKET_MESSAGE_BUFFER_SIZE = int(os.getenv('WEBSOCKET_MESSAGE_BUFFER_SIZE', '1000'))
        
        # Exchange Specific Configuration
        self._setup_exchange_configs()
        
        # Real-Time Storage Configuration
        self.REALTIME_DATA_DIR = os.getenv('REALTIME_DATA_DIR', 'data/realtime')
        self.REALTIME_DB_PATH = os.getenv('REALTIME_DB_PATH', self.DATABASE_PATH)  # Use same DB by default
    
    def _setup_exchange_configs(self):
        """Setup exchange-specific configurations"""
        # Binance Configuration
        self.BINANCE_BASE_URL = os.getenv('BINANCE_BASE_URL', 'https://fapi.binance.com')
        self.BINANCE_WEBSOCKET_URL = os.getenv('BINANCE_WEBSOCKET_URL', 'wss://fstream.binance.com/ws')
        self.BINANCE_RATE_LIMIT_RPM = int(os.getenv('BINANCE_RATE_LIMIT_RPM', '2400'))
        self.BINANCE_MAX_CONNECTIONS = int(os.getenv('BINANCE_MAX_CONNECTIONS', '10'))
        
        # Bybit Configuration (for future implementation)
        self.BYBIT_BASE_URL = os.getenv('BYBIT_BASE_URL', 'https://api.bybit.com')
        self.BYBIT_WEBSOCKET_URL = os.getenv('BYBIT_WEBSOCKET_URL', 'wss://stream.bybit.com/v5/public/linear')
        self.BYBIT_RATE_LIMIT_RPM = int(os.getenv('BYBIT_RATE_LIMIT_RPM', '600'))
        self.BYBIT_MAX_CONNECTIONS = int(os.getenv('BYBIT_MAX_CONNECTIONS', '20'))
    
    def get_orderbook_config(self):
        """Get order book configuration as a dictionary"""
        return {
            'depth_levels': self.ORDERBOOK_DEPTH_LEVELS,
            'update_frequency': self.ORDERBOOK_UPDATE_FREQUENCY,
            'symbols': self.REALTIME_SYMBOLS,
            'exchanges': self.REALTIME_EXCHANGES,
            'storage': {
                'redis_ttl': self.ORDERBOOK_REDIS_TTL,
                'db_batch_size': self.ORDERBOOK_BATCH_SIZE,
                'csv_backup': self.ORDERBOOK_CSV_BACKUP
            },
            'validation': {
                'max_spread_percentage': self.MAX_SPREAD_PERCENTAGE,
                'min_quantity': self.MIN_ORDER_QUANTITY
            }
        }
    
    def get_funding_config(self):
        """Get funding rate configuration as a dictionary"""
        return {
            'collection_interval': self.FUNDING_COLLECTION_INTERVAL,
            'symbols': self.REALTIME_SYMBOLS,
            'exchanges': self.REALTIME_EXCHANGES,
            'arbitrage_thresholds': {
                'min_rate_diff': self.ARBITRAGE_MIN_RATE_DIFF,
                'min_profit_bps': self.ARBITRAGE_MIN_PROFIT_BPS
            },
            'storage': {
                'db_batch_size': self.FUNDING_BATCH_SIZE,
                'csv_backup': self.FUNDING_CSV_BACKUP
            }
        }
    
    def get_binance_config(self):
        """Get Binance configuration as a dictionary"""
        return {
            'base_url': self.BINANCE_BASE_URL,
            'websocket_url': self.BINANCE_WEBSOCKET_URL,
            'rate_limits': {
                'requests_per_minute': self.BINANCE_RATE_LIMIT_RPM,
                'max_connections': self.BINANCE_MAX_CONNECTIONS
            },
            'symbols': self.REALTIME_SYMBOLS,
            'orderbook_depth': self.ORDERBOOK_DEPTH_LEVELS,
            'update_speed': f'{self.ORDERBOOK_UPDATE_FREQUENCY}ms'
        }
    
    def get_bybit_config(self):
        """Get Bybit configuration as a dictionary"""
        return {
            'base_url': self.BYBIT_BASE_URL,
            'websocket_url': self.BYBIT_WEBSOCKET_URL,
            'rate_limits': {
                'requests_per_minute': self.BYBIT_RATE_LIMIT_RPM,
                'max_connections': self.BYBIT_MAX_CONNECTIONS
            },
            'symbols': self.REALTIME_SYMBOLS,
            'orderbook_depth': self.ORDERBOOK_DEPTH_LEVELS,
            'update_speed': f'{self.ORDERBOOK_UPDATE_FREQUENCY}ms'
        }
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string to list"""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _parse_strategy_weights(self) -> dict:
        """Parse strategy weights from environment"""
        weights_str = os.getenv('STRATEGY_WEIGHTS', 'vix_correlation:0.6,mean_reversion:0.4')
        weights = {}
        
        for pair in weights_str.split(','):
            if ':' in pair:
                strategy, weight = pair.split(':')
                weights[strategy.strip()] = float(weight.strip())
        
        return weights
    
    def _validate_config(self):
        """Validate critical configuration settings"""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            # Production-specific validations
            if self.API_SECRET_KEY == 'your-secret-key-change-in-production':
                raise ValueError("API_SECRET_KEY must be changed in production")
            
            if not self.FRED_API_KEY:
                raise ValueError("FRED_API_KEY is required for macro data collection")
            
            if self.DEBUG:
                raise ValueError("DEBUG should be False in production")
        
        # General validations
        if self.REQUEST_TIMEOUT <= 0:
            raise ValueError("REQUEST_TIMEOUT must be positive")
        
        if self.API_PORT < 1024 or self.API_PORT > 65535:
            raise ValueError("API_PORT must be between 1024 and 65535")
        
        # Real-time specific validations
        if self.REALTIME_ENABLED:
            if self.ORDERBOOK_DEPTH_LEVELS <= 0:
                raise ValueError("ORDERBOOK_DEPTH_LEVELS must be positive")
            
            if self.ORDERBOOK_UPDATE_FREQUENCY <= 0:
                raise ValueError("ORDERBOOK_UPDATE_FREQUENCY must be positive")
            
            if not self.REALTIME_SYMBOLS:
                raise ValueError("REALTIME_SYMBOLS must be specified when real-time is enabled")
        
        # Validate Redis configuration
        if not self.REDIS_URL:
            raise ValueError("REDIS_URL is required for real-time data caching") 