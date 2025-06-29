import pytest
from src.utils.exceptions import (
    CryptoDataPipelineError,
    APIError,
    APIRateLimitError,
    APIConnectionError,
    APITimeoutError,
    DataValidationError,
    StorageError,
    ConfigurationError
)


class TestCryptoDataPipelineError:
    """Test the base exception class."""
    
    def test_basic_creation(self):
        """Test basic exception creation."""
        error = CryptoDataPipelineError("Test error")
        assert str(error) == "[CRYPTODATAPIPELINEERROR] Test error"
        assert error.message == "Test error"
        assert error.error_code == "CRYPTODATAPIPELINEERROR"
    
    def test_custom_error_code(self):
        """Test exception with custom error code."""
        error = CryptoDataPipelineError("Test error", "CUSTOM_CODE")
        assert str(error) == "[CUSTOM_CODE] Test error"
        assert error.error_code == "CUSTOM_CODE"
    
    def test_inheritance(self):
        """Test that custom exception inherits from Exception."""
        error = CryptoDataPipelineError("Test error")
        assert isinstance(error, Exception)


class TestAPIError:
    """Test the API error class."""
    
    def test_basic_creation(self):
        """Test basic API error creation."""
        error = APIError("API failed")
        assert str(error) == "[API_ERROR] API failed"
        assert error.message == "API failed"
        assert error.error_code == "API_ERROR"
        assert error.status_code is None
    
    def test_with_status_code(self):
        """Test API error with status code."""
        error = APIError("Not found", status_code=404)
        assert error.status_code == 404
        assert str(error) == "[API_ERROR] Not found"
    
    def test_custom_error_code(self):
        """Test API error with custom error code."""
        error = APIError("Custom error", "CUSTOM_API_ERROR", 500)
        assert error.error_code == "CUSTOM_API_ERROR"
        assert error.status_code == 500
    
    def test_inheritance(self):
        """Test API error inheritance."""
        error = APIError("Test error")
        assert isinstance(error, CryptoDataPipelineError)
        assert isinstance(error, Exception)


class TestAPIRateLimitError:
    """Test the API rate limit error class."""
    
    def test_task_example(self):
        """Test the specific example from Task 6.1."""
        with pytest.raises(APIRateLimitError):
            raise APIRateLimitError("Rate limited")
    
    def test_default_creation(self):
        """Test rate limit error with defaults."""
        error = APIRateLimitError()
        assert str(error) == "[API_RATE_LIMIT] API rate limit exceeded"
        assert error.error_code == "API_RATE_LIMIT"
        assert error.status_code == 429
        assert error.retry_after is None
    
    def test_custom_message(self):
        """Test rate limit error with custom message."""
        error = APIRateLimitError("Too many requests")
        assert str(error) == "[API_RATE_LIMIT] Too many requests"
        assert error.status_code == 429
    
    def test_with_retry_after(self):
        """Test rate limit error with retry after value."""
        error = APIRateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert error.status_code == 429
    
    def test_inheritance(self):
        """Test rate limit error inheritance."""
        error = APIRateLimitError()
        assert isinstance(error, APIError)
        assert isinstance(error, CryptoDataPipelineError)
        assert isinstance(error, Exception)


class TestAPIConnectionError:
    """Test the API connection error class."""
    
    def test_default_creation(self):
        """Test connection error with defaults."""
        error = APIConnectionError()
        assert str(error) == "[API_CONNECTION_ERROR] Failed to connect to API"
        assert error.error_code == "API_CONNECTION_ERROR"
    
    def test_custom_message(self):
        """Test connection error with custom message."""
        error = APIConnectionError("Network unreachable")
        assert str(error) == "[API_CONNECTION_ERROR] Network unreachable"
    
    def test_inheritance(self):
        """Test connection error inheritance."""
        error = APIConnectionError()
        assert isinstance(error, APIError)
        assert isinstance(error, CryptoDataPipelineError)


class TestAPITimeoutError:
    """Test the API timeout error class."""
    
    def test_default_creation(self):
        """Test timeout error with defaults."""
        error = APITimeoutError()
        assert str(error) == "[API_TIMEOUT] API request timed out"
        assert error.error_code == "API_TIMEOUT"
        assert error.timeout is None
    
    def test_custom_message(self):
        """Test timeout error with custom message."""
        error = APITimeoutError("Request took too long")
        assert str(error) == "[API_TIMEOUT] Request took too long"
    
    def test_with_timeout_value(self):
        """Test timeout error with timeout value."""
        error = APITimeoutError("Timed out after 30s", timeout=30.0)
        assert error.timeout == 30.0
    
    def test_inheritance(self):
        """Test timeout error inheritance."""
        error = APITimeoutError()
        assert isinstance(error, APIError)
        assert isinstance(error, CryptoDataPipelineError)


class TestDataValidationError:
    """Test the data validation error class."""
    
    def test_basic_creation(self):
        """Test basic validation error creation."""
        error = DataValidationError("Invalid data")
        assert str(error) == "[DATA_VALIDATION_ERROR] Invalid data"
        assert error.error_code == "DATA_VALIDATION_ERROR"
        assert error.field is None
        assert error.value is None
    
    def test_with_field_and_value(self):
        """Test validation error with field and value."""
        error = DataValidationError("Price cannot be negative", field="price", value=-100)
        assert error.field == "price"
        assert error.value == -100
        assert str(error) == "[DATA_VALIDATION_ERROR] Price cannot be negative"
    
    def test_inheritance(self):
        """Test validation error inheritance."""
        error = DataValidationError("Test error")
        assert isinstance(error, CryptoDataPipelineError)
        assert isinstance(error, Exception)


class TestStorageError:
    """Test the storage error class."""
    
    def test_basic_creation(self):
        """Test basic storage error creation."""
        error = StorageError("Failed to save file")
        assert str(error) == "[STORAGE_ERROR] Failed to save file"
        assert error.error_code == "STORAGE_ERROR"
        assert error.operation is None
        assert error.file_path is None
    
    def test_with_operation_and_path(self):
        """Test storage error with operation and file path."""
        error = StorageError("Permission denied", operation="write", file_path="/data/bitcoin.csv")
        assert error.operation == "write"
        assert error.file_path == "/data/bitcoin.csv"
        assert str(error) == "[STORAGE_ERROR] Permission denied"
    
    def test_inheritance(self):
        """Test storage error inheritance."""
        error = StorageError("Test error")
        assert isinstance(error, CryptoDataPipelineError)
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Test the configuration error class."""
    
    def test_basic_creation(self):
        """Test basic configuration error creation."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "[CONFIGURATION_ERROR] Invalid configuration"
        assert error.error_code == "CONFIGURATION_ERROR"
        assert error.config_key is None
    
    def test_with_config_key(self):
        """Test configuration error with config key."""
        error = ConfigurationError("Missing required setting", config_key="API_KEY")
        assert error.config_key == "API_KEY"
        assert str(error) == "[CONFIGURATION_ERROR] Missing required setting"
    
    def test_inheritance(self):
        """Test configuration error inheritance."""
        error = ConfigurationError("Test error")
        assert isinstance(error, CryptoDataPipelineError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy."""
    
    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from base exception."""
        exceptions = [
            APIError("test"),
            APIRateLimitError(),
            APIConnectionError(),
            APITimeoutError(),
            DataValidationError("test"),
            StorageError("test"),
            ConfigurationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, CryptoDataPipelineError)
            assert isinstance(exc, Exception)
    
    def test_api_exceptions_inherit_from_api_error(self):
        """Test that API-specific exceptions inherit from APIError."""
        api_exceptions = [
            APIRateLimitError(),
            APIConnectionError(),
            APITimeoutError()
        ]
        
        for exc in api_exceptions:
            assert isinstance(exc, APIError)
            assert isinstance(exc, CryptoDataPipelineError)
    
    def test_error_codes_are_unique(self):
        """Test that each exception type has a unique error code."""
        exceptions = [
            CryptoDataPipelineError("test"),
            APIError("test"),
            APIRateLimitError(),
            APIConnectionError(),
            APITimeoutError(),
            DataValidationError("test"),
            StorageError("test"),
            ConfigurationError("test")
        ]
        
        error_codes = [exc.error_code for exc in exceptions]
        # Check for duplicates
        assert len(error_codes) == len(set(error_codes)) 