import requests
import time
import logging
from typing import Dict, Any, Optional, List
from config.exchanges.binance_config import BINANCE_CONFIG

logger = logging.getLogger(__name__)

class BinanceClient:
    def __init__(self):
        self.base_url = BINANCE_CONFIG['base_url']
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MTS-Pipeline/1.0'})
        
    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Get order book for symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/depth"
            params = {
                'symbol': symbol.upper(),
                'limit': limit
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current funding rate for symbol"""
        try:
            url = f"{self.base_url}/fapi/v1/premiumIndex"
            params = {'symbol': symbol.upper()}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get 24hr ticker statistics"""
        try:
            url = f"{self.base_url}/fapi/v1/ticker/24hr"
            params = {'symbol': symbol.upper()}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            return None 