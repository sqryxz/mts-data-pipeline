"""Tests for retry functionality with exponential backoff."""

import time
import pytest
import requests
from unittest.mock import Mock, patch
from src.utils.retry import retry_with_backoff, calculate_backoff_delay
from src.utils.exceptions import (
    APIError, APIRateLimitError, APIConnectionError, 
    APITimeoutError, DataValidationError
)


class TestRetryDecorator:
    """Test the retry_with_backoff decorator."""
    
    def test_successful_first_attempt(self):
        """Test function succeeds on first attempt."""
        @retry_with_backoff(max_retries=3)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_success_after_retries(self):
        """Test function succeeds after retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)  # Short delay for test
        def eventually_success_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIConnectionError("Connection failed")
            return "success"
        
        result = eventually_success_func()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test function fails after max retries exceeded."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fail_func():
            nonlocal call_count
            call_count += 1
            raise APIConnectionError("Always fails")
        
        with pytest.raises(APIConnectionError):
            always_fail_func()
        
        assert call_count == 3  # Original attempt + 2 retries
    
    def test_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3)
        def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise DataValidationError("Data is invalid")
        
        with pytest.raises(DataValidationError):
            non_retryable_func()
        
        assert call_count == 1  # Should not retry
    
    def test_rate_limit_handling(self):
        """Test special handling for rate limit errors."""
        call_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def rate_limited_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIRateLimitError("Rate limited", retry_after=5)
            return "success"
        
        with patch('time.sleep') as mock_sleep:
            result = rate_limited_func()
            assert result == "success"
            assert call_count == 2
            # Should use retry_after value (5) instead of base_delay
            mock_sleep.assert_called_once()
            assert mock_sleep.call_args[0][0] >= 5  # Should be at least retry_after
    
    def test_exponential_backoff(self):
        """Test exponential backoff timing."""
        call_count = 0
        delays = []
        
        @retry_with_backoff(max_retries=3, base_delay=1.0, jitter=False)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise APIConnectionError("Connection failed")
            return "success"
        
        with patch('time.sleep') as mock_sleep:
            result = failing_func()
            assert result == "success"
            
            # Check exponential backoff: 1.0, 2.0, 4.0
            expected_delays = [1.0, 2.0, 4.0]
            actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays
    
    def test_custom_retry_parameters(self):
        """Test custom retry parameters."""
        call_count = 0
        
        @retry_with_backoff(
            max_retries=1,
            base_delay=0.5,
            backoff_factor=3.0,
            jitter=False,
            retryable_exceptions=(APIError,)
        )
        def custom_retry_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise APIError("API error")
            return "success"
        
        with patch('time.sleep') as mock_sleep:
            result = custom_retry_func()
            assert result == "success"
            assert call_count == 2
            mock_sleep.assert_called_once_with(0.5)
    
    def test_jitter_enabled(self):
        """Test that jitter adds randomness to delays."""
        @retry_with_backoff(max_retries=1, base_delay=1.0, jitter=True)
        def jitter_func():
            raise APIConnectionError("Always fails")
        
        with patch('time.sleep') as mock_sleep, \
             patch('random.uniform', return_value=0.05):  # Mock 5% jitter
            
            with pytest.raises(APIConnectionError):
                jitter_func()
            
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert delay > 1.0  # Should be base_delay + jitter
    
    def test_max_delay_cap(self):
        """Test maximum delay cap is enforced."""
        call_count = 0
        
        @retry_with_backoff(max_retries=5, base_delay=10.0, max_delay=20.0, jitter=False)
        def capped_delay_func():
            nonlocal call_count
            call_count += 1
            raise APIConnectionError("Always fails")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(APIConnectionError):
                capped_delay_func()
            
            # Check that no delay exceeds max_delay
            for call in mock_sleep.call_args_list:
                delay = call.args[0]
                assert delay <= 20.0


class TestCalculateBackoffDelay:
    """Test the calculate_backoff_delay function."""
    
    def test_exponential_growth(self):
        """Test exponential growth of delays."""
        delays = [
            calculate_backoff_delay(attempt, base_delay=1.0, backoff_factor=2.0, jitter=False)
            for attempt in range(5)
        ]
        
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]
        assert delays == expected
    
    def test_max_delay_cap(self):
        """Test maximum delay is capped."""
        delay = calculate_backoff_delay(
            attempt=10, 
            base_delay=1.0, 
            backoff_factor=2.0, 
            max_delay=30.0, 
            jitter=False
        )
        assert delay == 30.0
    
    def test_custom_backoff_factor(self):
        """Test custom backoff factor."""
        delay = calculate_backoff_delay(
            attempt=2, 
            base_delay=2.0, 
            backoff_factor=3.0, 
            jitter=False
        )
        assert delay == 18.0  # 2.0 * (3.0 ** 2)
    
    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness."""
        with patch('random.uniform', return_value=0.1):
            delay = calculate_backoff_delay(
                attempt=1, 
                base_delay=1.0, 
                backoff_factor=2.0, 
                jitter=True
            )
            assert delay == 2.1  # 2.0 + 0.1 (10% of 2.0)


class TestAPIClientRetryIntegration:
    """Test retry integration with API client methods."""
    
    @patch('src.api.coingecko_client.requests.get')
    def test_ping_retry_on_connection_error(self, mock_get):
        """Test ping method retries on connection error."""
        from src.api.coingecko_client import CoinGeckoClient
        
        # First call fails, second succeeds
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            Mock(status_code=200, json=lambda: {"gecko_says": "Success!"})
        ]
        
        client = CoinGeckoClient()
        
        with patch('time.sleep'):  # Speed up test
            result = client.ping()
            assert result == {"gecko_says": "Success!"}
            assert mock_get.call_count == 2
    
    @patch('src.api.coingecko_client.requests.get')
    def test_get_top_cryptos_retry_on_timeout(self, mock_get):
        """Test get_top_cryptos retries on timeout."""
        from src.api.coingecko_client import CoinGeckoClient
        
        # First call times out, second succeeds
        mock_get.side_effect = [
            requests.exceptions.Timeout("Request timed out"),
            Mock(status_code=200, json=lambda: [{"id": "bitcoin"}])
        ]
        
        client = CoinGeckoClient()
        
        with patch('time.sleep'):  # Speed up test
            result = client.get_top_cryptos(1)
            assert result == [{"id": "bitcoin"}]
            assert mock_get.call_count == 2
    
    @patch('src.api.coingecko_client.requests.get')
    def test_rate_limit_retry_after(self, mock_get):
        """Test API respects retry-after header for rate limits."""
        from src.api.coingecko_client import CoinGeckoClient
        
        # First call rate limited with retry-after, second succeeds
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '10'}
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"data": "success"}
        
        mock_get.side_effect = [rate_limit_response, success_response]
        
        client = CoinGeckoClient()
        
        with patch('time.sleep') as mock_sleep:
            result = client.ping()
            assert result == {"data": "success"}
            assert mock_get.call_count == 2
            # Should wait at least the retry-after duration
            mock_sleep.assert_called_once()
            assert mock_sleep.call_args[0][0] >= 10
    
    @patch('src.api.coingecko_client.requests.get')
    def test_non_retryable_http_error(self, mock_get):
        """Test non-retryable HTTP errors are not retried."""
        from src.api.coingecko_client import CoinGeckoClient
        
        # Return 404 error
        error_response = Mock()
        error_response.status_code = 404
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        mock_get.return_value = error_response
        
        client = CoinGeckoClient()
        
        with pytest.raises(APIError):
            client.get_ohlc_data("nonexistent", 1)
        
        assert mock_get.call_count == 1  # Should not retry 404 errors 