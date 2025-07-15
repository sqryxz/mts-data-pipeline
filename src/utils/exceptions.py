"""Custom exceptions for the crypto data pipeline."""


class CryptoDataPipelineError(Exception):
    """Base exception for all crypto data pipeline errors."""
    
    def __init__(self, message: str, error_code: str = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for categorization
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# Real-Time Data Collection Exceptions
class RealTimeDataError(CryptoDataPipelineError):
    """Base exception for real-time data collection errors."""
    pass


class WebSocketConnectionError(RealTimeDataError):
    """WebSocket connection failed or lost."""
    
    def __init__(self, message: str, exchange: str = None, retry_after: int = None):
        super().__init__(message)
        self.exchange = exchange
        self.retry_after = retry_after


class OrderBookError(RealTimeDataError):
    """Order book data processing error."""
    
    def __init__(self, message: str, symbol: str = None, exchange: str = None):
        super().__init__(message)
        self.symbol = symbol
        self.exchange = exchange


class FundingRateError(RealTimeDataError):
    """Funding rate collection error."""
    
    def __init__(self, message: str, symbol: str = None, exchange: str = None):
        super().__init__(message)
        self.symbol = symbol
        self.exchange = exchange


class StreamError(RealTimeDataError):
    """Stream processing error."""
    
    def __init__(self, message: str, stream_name: str = None, error_type: str = None):
        super().__init__(message)
        self.stream_name = stream_name
        self.error_type = error_type


class ArbitrageError(RealTimeDataError):
    """Arbitrage detection and calculation error."""
    
    def __init__(self, message: str, symbol: str = None, exchanges: list = None):
        super().__init__(message)
        self.symbol = symbol
        self.exchanges = exchanges or []


class RealTimeStorageError(RealTimeDataError):
    """Real-time data storage error."""
    
    def __init__(self, message: str, storage_type: str = None):
        super().__init__(message)
        self.storage_type = storage_type  # 'redis', 'sqlite', 'csv'


# API and Connection Exceptions
class APIError(CryptoDataPipelineError):
    """Base exception for API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class APIRateLimitError(APIError):
    """API rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None, status_code: int = 429):
        super().__init__(message, status_code)
        self.retry_after = retry_after


class APIConnectionError(APIError):
    """API connection error."""
    pass


class APITimeoutError(APIError):
    """API request timeout."""
    pass


# Data Processing Exceptions
class DataValidationError(CryptoDataPipelineError):
    """Data validation failed."""
    
    def __init__(self, message: str, field_name: str = None, field_value: str = None):
        super().__init__(message)
        self.field_name = field_name
        self.field_value = field_value


class DataStorageError(CryptoDataPipelineError):
    """Data storage operation failed."""
    pass


class DataProcessingError(CryptoDataPipelineError):
    """Data processing operation failed."""
    pass


# Storage Exceptions
class StorageError(CryptoDataPipelineError):
    """Storage operation failed."""
    pass


class DatabaseError(StorageError):
    """Database operation failed."""
    pass


# FRED API Exceptions  
class FREDAPIError(APIError):
    """FRED API specific error."""
    pass


class MacroDataError(CryptoDataPipelineError):
    """Macro data collection error."""
    
    def __init__(self, message: str, indicator: str = None):
        super().__init__(message)
        self.indicator = indicator


# Strategy and Signal Exceptions
class StrategyError(CryptoDataPipelineError):
    """Strategy execution error."""
    
    def __init__(self, message: str, strategy_name: str = None):
        super().__init__(message)
        self.strategy_name = strategy_name


class SignalGenerationError(CryptoDataPipelineError):
    """Signal generation error."""
    pass


class BacktestError(CryptoDataPipelineError):
    """Backtesting error."""
    pass


# Configuration Exceptions
class ConfigurationError(CryptoDataPipelineError):
    """Configuration error."""
    pass


class ValidationError(CryptoDataPipelineError):
    """General validation error."""
    pass 

"""
Custom exceptions for the backtesting engine.
"""

class BacktestingError(Exception):
    """Base exception for all backtesting-related errors."""
    pass

class DataError(BacktestingError):
    """Raised when there are issues with market data."""
    pass

class StrategyError(BacktestingError):
    """Raised when there are issues with strategy execution."""
    pass

class ConfigurationError(BacktestingError):
    """Raised when there are issues with backtest configuration."""
    pass

class ExecutionError(BacktestingError):
    """Raised when there are issues with order execution."""
    pass

class PortfolioError(BacktestingError):
    """Raised when there are issues with portfolio management."""
    pass

class ValidationError(BacktestingError):
    """Raised when input validation fails."""
    pass

class DatabaseError(BacktestingError):
    """Raised when there are database-related issues."""
    pass 