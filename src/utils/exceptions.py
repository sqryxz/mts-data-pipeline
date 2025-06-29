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


class APIError(CryptoDataPipelineError):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, error_code: str = "API_ERROR", status_code: int = None):
        """
        Initialize API error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code if applicable
        """
        super().__init__(message, error_code)
        self.status_code = status_code


class APIRateLimitError(APIError):
    """Exception for API rate limiting errors."""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None):
        """
        Initialize rate limit error.
        
        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying, if provided by API
        """
        super().__init__(message, "API_RATE_LIMIT", status_code=429)
        self.retry_after = retry_after


class APIConnectionError(APIError):
    """Exception for API connection errors."""
    
    def __init__(self, message: str = "Failed to connect to API"):
        """
        Initialize connection error.
        
        Args:
            message: Human-readable error message
        """
        super().__init__(message, "API_CONNECTION_ERROR")


class APITimeoutError(APIError):
    """Exception for API timeout errors."""
    
    def __init__(self, message: str = "API request timed out", timeout: float = None):
        """
        Initialize timeout error.
        
        Args:
            message: Human-readable error message
            timeout: The timeout value that was exceeded
        """
        super().__init__(message, "API_TIMEOUT")
        self.timeout = timeout


class DataValidationError(CryptoDataPipelineError):
    """Exception for data validation failures."""
    
    def __init__(self, message: str, field: str = None, value = None):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: The field that failed validation
            value: The invalid value
        """
        super().__init__(message, "DATA_VALIDATION_ERROR")
        self.field = field
        self.value = value


class StorageError(CryptoDataPipelineError):
    """Exception for storage operation failures."""
    
    def __init__(self, message: str, operation: str = None, file_path: str = None):
        """
        Initialize storage error.
        
        Args:
            message: Human-readable error message
            operation: The storage operation that failed (e.g., 'read', 'write')
            file_path: The file path involved in the operation
        """
        super().__init__(message, "STORAGE_ERROR")
        self.operation = operation
        self.file_path = file_path


class ConfigurationError(CryptoDataPipelineError):
    """Exception for configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None):
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the error
        """
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key 