#!/usr/bin/env python3
"""
CoinGecko API Client for Paper Trading Engine
"""

import requests
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime


class APIError(Exception):
    """Base API error"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class APIRateLimitError(APIError):
    """Rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIConnectionError(APIError):
    """Connection error"""
    pass


class APITimeoutError(APIError):
    """Request timeout"""
    def __init__(self, message: str, timeout: float = 30.0):
        super().__init__(message)
        self.timeout = timeout


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying API calls with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except APIRateLimitError as e:
                    if e.retry_after:
                        time.sleep(e.retry_after)
                    else:
                        time.sleep(base_delay * (2 ** attempt))
                    last_exception = e
                except (APIConnectionError, APITimeoutError) as e:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                    last_exception = e
                except APIError as e:
                    # Don't retry client errors (4xx), but retry server errors (5xx)
                    if hasattr(e, 'status_code') and e.status_code and 400 <= e.status_code < 500:
                        raise e
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                    last_exception = e
                except Exception as e:
                    # For unexpected errors, only retry if it's not the last attempt
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                    last_exception = e
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class CoinGeckoClient:
    """CoinGecko API client for real-time cryptocurrency prices"""
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize CoinGecko client
        
        Args:
            api_key: Optional API key for Pro API access
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Use Pro API if we have a Pro API key
        if self.api_key and self.api_key.startswith('CG-'):
            self.base_url = 'https://pro-api.coingecko.com/api/v3'
            self.headers = {'x-cg-pro-api-key': self.api_key}
        else:
            self.base_url = 'https://api.coingecko.com/api/v3'
            self.headers = {}
        
        # Asset ID mapping for common cryptocurrencies
        self.asset_id_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'ADA': 'cardano',
            'SOL': 'solana',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'AVAX': 'avalanche-2',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'XRP': 'ripple',
            'TRX': 'tron',
            'EOS': 'eos',
            'XLM': 'stellar',
            'VET': 'vechain',
            'FIL': 'filecoin',
            'ALGO': 'algorand',
            'USDT': 'tether',
            'USDC': 'usd-coin',
            'BNB': 'binancecoin',
            'XMR': 'monero',
            'SHIB': 'shiba-inu',
            'DAI': 'dai',
            'WBTC': 'wrapped-bitcoin',
            'LEO': 'leo-token'
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request with error handling
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            APIRateLimitError: If rate limit exceeded
            APIConnectionError: If connection fails
            APITimeoutError: If request times out
            APIError: For other API errors
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(
                url, 
                params=params, 
                timeout=self.timeout, 
                headers=self.headers
            )
            
            # Handle rate limiting before raise_for_status
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None
                raise APIRateLimitError("API rate limit exceeded", retry_after=retry_after_int)
            
            response.raise_for_status()
            response_data = response.json()
            
            # Validate response structure
            self._validate_response(response_data)
            
            return response_data
            
        except requests.exceptions.ConnectionError as e:
            raise APIConnectionError(f"Failed to connect to CoinGecko API: {e}")
        except requests.exceptions.Timeout as e:
            raise APITimeoutError(f"CoinGecko API request timed out: {e}", timeout=self.timeout)
        except requests.exceptions.HTTPError as e:
            # Extract status code safely
            status_code = None
            if hasattr(e, 'response') and e.response:
                status_code = e.response.status_code
            raise APIError(f"HTTP error: {e} (Status: {status_code})", status_code=status_code)
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def ping(self) -> Dict:
        """Test connection to CoinGecko API"""
        return self._make_request("/ping")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_current_price(self, asset: str) -> float:
        """
        Get current price for a cryptocurrency
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Current price in USD
            
        Raises:
            APIError: If asset not found or API error
        """
        # Get CoinGecko ID for the asset
        coin_id = self.asset_id_map.get(asset.upper())
        if not coin_id:
            raise APIError(f"Asset '{asset}' not supported. Supported assets: {list(self.asset_id_map.keys())}")
        
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd'
        }
        
        response = self._make_request("/simple/price", params)
        
        # Validate response contains expected coin_id
        if coin_id not in response:
            raise APIError(f"Asset '{asset}' not found in API response")
        
        price_data = response[coin_id]
        if not isinstance(price_data, dict):
            raise APIError(f"Invalid price data format for '{asset}'")
        
        price = price_data.get('usd')
        if price is None:
            raise APIError(f"No USD price found for '{asset}'")
        
        try:
            return float(price)
        except (ValueError, TypeError):
            raise APIError(f"Invalid price value for '{asset}': {price}")
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_current_prices(self, assets: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple cryptocurrencies
        
        Args:
            assets: List of asset symbols
            
        Returns:
            Dictionary mapping asset symbols to current prices
            
        Raises:
            APIError: If any asset not found or API error
        """
        # Get CoinGecko IDs for all assets
        coin_ids = []
        asset_to_coin_id = {}
        
        for asset in assets:
            coin_id = self.asset_id_map.get(asset.upper())
            if not coin_id:
                raise APIError(f"Asset '{asset}' not supported. Supported assets: {list(self.asset_id_map.keys())}")
            coin_ids.append(coin_id)
            asset_to_coin_id[asset.upper()] = coin_id
        
        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd'
        }
        
        response = self._make_request("/simple/price", params)
        
        # Map response back to asset symbols
        prices = {}
        for asset, coin_id in asset_to_coin_id.items():
            if coin_id not in response:
                raise APIError(f"Asset '{asset}' not found in API response")
            
            price_data = response[coin_id]
            if not isinstance(price_data, dict):
                raise APIError(f"Invalid price data format for '{asset}'")
            
            price = price_data.get('usd')
            if price is None:
                raise APIError(f"No USD price found for '{asset}'")
            
            try:
                prices[asset] = float(price)
            except (ValueError, TypeError):
                raise APIError(f"Invalid price value for '{asset}': {price}")
        
        return prices
    
    def get_supported_assets(self) -> List[str]:
        """Get list of supported asset symbols"""
        return list(self.asset_id_map.keys())
    
    def is_asset_supported(self, asset: str) -> bool:
        """Check if an asset is supported"""
        return asset.upper() in self.asset_id_map
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.ping()
            self.logger.info("CoinGecko API connection successful")
            return True
        except Exception as e:
            self.logger.error(f"CoinGecko API connection failed: {e}")
            return False
    
    def _validate_response(self, response: Dict, expected_keys: List[str] = None) -> None:
        """Validate API response structure"""
        if not isinstance(response, dict):
            raise APIError("Invalid response format: expected dictionary")
        
        if not response:
            raise APIError("Empty response received")
        
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in response]
            if missing_keys:
                raise APIError(f"Missing required keys in response: {missing_keys}") 