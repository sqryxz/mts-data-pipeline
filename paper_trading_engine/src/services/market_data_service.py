"""
Centralized market data service for the Paper Trading Engine
"""

import random
import logging
from datetime import datetime
from typing import Optional, Dict, List
from .coingecko_client import CoinGeckoClient, APIError, APIRateLimitError, APIConnectionError


class MarketDataService:
    """Centralized market data provider with real-time CoinGecko integration"""
    
    def __init__(self, use_real_time: bool = True, api_key: Optional[str] = None):
        """
        Initialize market data service
        
        Args:
            use_real_time: Whether to use real-time CoinGecko API or fallback to mock data
            api_key: Optional CoinGecko API key for Pro access
        """
        self.use_real_time = use_real_time
        self.logger = logging.getLogger(__name__)
        
        # Initialize CoinGecko client if using real-time data
        if self.use_real_time:
            self.coingecko_client = CoinGeckoClient(api_key=api_key)
            # Test connection
            if not self.coingecko_client.test_connection():
                self.logger.warning("CoinGecko API connection failed, falling back to mock data")
                self.use_real_time = False
        
        # Configuration constants for mock data
        self.PRICE_VARIATION_RANGE = 0.001  # ±0.1% (realistic for real-time feeds)
        
        # Base prices for different assets (fallback)
        self.BASE_PRICES = {
            'BTC': 50000.0,
            'ETH': 3000.0,
            'DOGE': 0.1,
            'ADA': 0.5,
            'SOL': 100.0,
            'DOT': 7.0,
            'MATIC': 0.8,
            'LINK': 15.0,
            'UNI': 8.0,
            'AVAX': 25.0,
            'ATOM': 10.0,
            'LTC': 80.0,
            'BCH': 250.0,
            'XRP': 0.5,
            'TRX': 0.08,
            'EOS': 0.7,
            'XLM': 0.1,
            'VET': 0.02,
            'FIL': 5.0,
            'ALGO': 0.2
        }
    
    def get_current_price(self, asset: str, timestamp: Optional[datetime] = None) -> float:
        """Get current market price with real-time CoinGecko integration"""
        
        # Try real-time API if enabled
        if self.use_real_time:
            try:
                return self.coingecko_client.get_current_price(asset)
            except (APIError, APIRateLimitError, APIConnectionError) as e:
                self.logger.warning(f"Failed to get real-time price for {asset}: {e}")
                # Fall back to mock data
                pass
        
        # Fallback to mock data
        base_price = self.BASE_PRICES.get(asset.upper(), 100.0)
        
        # Use deterministic variation if timestamp provided (for backtesting)
        if timestamp:
            seed = int(timestamp.timestamp()) % 1000
            random.seed(seed)
        
        # Add realistic price variation (±0.1%)
        variation = random.uniform(-self.PRICE_VARIATION_RANGE, self.PRICE_VARIATION_RANGE)
        return base_price * (1 + variation)
    
    def get_current_prices(self, assets: List[str]) -> Dict[str, float]:
        """Get current prices for multiple assets with real-time integration"""
        
        # Try real-time API if enabled
        if self.use_real_time:
            try:
                return self.coingecko_client.get_current_prices(assets)
            except (APIError, APIRateLimitError, APIConnectionError) as e:
                self.logger.warning(f"Failed to get real-time prices: {e}")
                # Fall back to mock data
                pass
        
        # Fallback to mock data
        prices = {}
        for asset in assets:
            prices[asset] = self.get_current_price(asset)
        
        return prices
    
    def get_market_conditions(self, asset: str) -> dict:
        """Get asset-specific market conditions"""
        
        # Asset-specific conditions
        conditions_map = {
            'BTC': {
                'volatility': 0.02,    # 2% volatility
                'spread': 0.0005,      # 0.05% spread
                'volume': 10000000,    # $10M daily volume
                'liquidity': 'high'
            },
            'ETH': {
                'volatility': 0.025,   # 2.5% volatility
                'spread': 0.0008,      # 0.08% spread
                'volume': 5000000,     # $5M daily volume
                'liquidity': 'high'
            },
            'DOGE': {
                'volatility': 0.05,    # 5% volatility
                'spread': 0.002,       # 0.2% spread
                'volume': 1000000,     # $1M daily volume
                'liquidity': 'medium'
            },
            'ADA': {
                'volatility': 0.04,    # 4% volatility
                'spread': 0.0015,      # 0.15% spread
                'volume': 2000000,     # $2M daily volume
                'liquidity': 'medium'
            },
            'SOL': {
                'volatility': 0.035,   # 3.5% volatility
                'spread': 0.001,       # 0.1% spread
                'volume': 3000000,     # $3M daily volume
                'liquidity': 'high'
            }
        }
        
        return conditions_map.get(asset.upper(), {
            'volatility': 0.04,        # Default for unknown assets
            'spread': 0.002,
            'volume': 100000,
            'liquidity': 'low'
        })
    
    def validate_asset(self, asset: str) -> bool:
        """Validate if asset is supported"""
        if self.use_real_time:
            return self.coingecko_client.is_asset_supported(asset)
        return asset.upper() in self.BASE_PRICES or len(asset) >= 2
    
    def get_supported_assets(self) -> List[str]:
        """Get list of supported assets"""
        if self.use_real_time:
            return self.coingecko_client.get_supported_assets()
        return list(self.BASE_PRICES.keys())
    
    def is_using_real_time(self) -> bool:
        """Check if service is using real-time data"""
        return self.use_real_time 