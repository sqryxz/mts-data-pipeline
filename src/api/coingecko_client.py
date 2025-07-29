import requests
from config.settings import Config
from src.utils.retry import retry_with_backoff
from src.utils.exceptions import APIError, APIRateLimitError, APIConnectionError, APITimeoutError
import os


class CoinGeckoClient:
    """CoinGecko API client for cryptocurrency data."""
    
    def __init__(self, api_key=None):
        self.config = Config()
        self.api_key = api_key or getattr(self.config, 'COINGECKO_API_KEY', None) or os.getenv('COINGECKO_API_KEY')
        
        # Use Pro API endpoint if we have a Pro API key
        if self.api_key and self.api_key.startswith('CG-'):
            self.base_url = 'https://pro-api.coingecko.com/api/v3'
        else:
            self.base_url = self.config.COINGECKO_BASE_URL
            
        self.timeout = self.config.REQUEST_TIMEOUT
        self.headers = {}
        if self.api_key:
            self.headers['x-cg-pro-api-key'] = self.api_key
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def ping(self):
        """Test connection to CoinGecko API."""
        try:
            url = f"{self.base_url}/ping"
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            
            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Already handled above, but just in case
                raise APIRateLimitError(f"API rate limit exceeded: {e}")
            raise APIError(f"HTTP error: {e}", status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_top_cryptos(self, limit):
        """Fetch top cryptocurrencies by market cap."""
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false'
            }
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            
            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Already handled above, but just in case
                raise APIRateLimitError(f"API rate limit exceeded: {e}")
            raise APIError(f"HTTP error: {e}", status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_ohlc_data(self, coin_id, days):
        """Fetch OHLC data for specific cryptocurrency."""
        try:
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            
            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Already handled above, but just in case
                raise APIRateLimitError(f"API rate limit exceeded: {e}")
            raise APIError(f"HTTP error: {e}", status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0) 
    def get_market_chart_data(self, coin_id, days):
        """Fetch market chart data including volume for specific cryptocurrency."""
        try:
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            
            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Already handled above, but just in case
                raise APIRateLimitError(f"API rate limit exceeded: {e}")
            raise APIError(f"HTTP error: {e}", status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_market_chart_range_data(self, coin_id, from_timestamp, to_timestamp):
        """
        Fetch market chart data within a specific date range using Unix timestamps.
        
        This method provides more precise control over data collection periods and
        ensures hourly granularity for ranges between 1-90 days.
        
        Args:
            coin_id: Cryptocurrency ID (e.g., 'bitcoin')
            from_timestamp: Start timestamp in Unix format (seconds)
            to_timestamp: End timestamp in Unix format (seconds)
            
        Returns:
            Dict containing prices and total_volumes arrays
            
        Note:
            - 1 day from anytime (except from current time) = hourly data
            - 2-90 days from anytime = hourly data
            - >90 days from anytime = daily data
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': int(from_timestamp),
                'to': int(to_timestamp)
            }
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            if response.status_code != 200:
                print(f"CoinGecko API error {response.status_code}: {response.text}")
            # Handle specific HTTP status codes
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # Already handled above, but just in case
                raise APIRateLimitError(f"API rate limit exceeded: {e}")
            raise APIError(f"HTTP error: {e}", status_code=response.status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}") 