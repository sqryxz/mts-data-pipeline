import requests
import time
import logging
from typing import Dict, Any, Optional, List
from config.exchanges.bybit_config import BYBIT_CONFIG

logger = logging.getLogger(__name__)

class BybitClient:
    def __init__(self):
        self.base_url = BYBIT_CONFIG['base_url']
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MTS-Pipeline/1.0'})
        
    def get_order_book(self, symbol: str, limit: int = 25) -> Optional[Dict[str, Any]]:
        """Get order book for symbol using Bybit API v5"""
        try:
            url = f"{self.base_url}/v5/market/orderbook"
            params = {
                'category': 'linear',  # USDT perpetual
                'symbol': symbol.upper(),
                'limit': min(limit, 50)  # Bybit max is 50
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract order book from Bybit response format
            if data.get('retCode') == 0 and 'result' in data:
                return data['result']
            else:
                logger.error(f"Bybit API error for {symbol}: {data.get('retMsg', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current funding rate for symbol using Bybit API v5"""
        try:
            url = f"{self.base_url}/v5/market/funding/history"
            params = {
                'category': 'linear',
                'symbol': symbol.upper(),
                'limit': 1  # Get only the latest
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract funding rate from Bybit response format
            if (data.get('retCode') == 0 and 'result' in data and 
                'list' in data['result'] and len(data['result']['list']) > 0):
                return data['result']['list'][0]
            else:
                logger.error(f"Bybit funding rate API error for {symbol}: {data.get('retMsg', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get funding rate for {symbol}: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get 24hr ticker statistics using Bybit API v5"""
        try:
            url = f"{self.base_url}/v5/market/tickers"
            params = {
                'category': 'linear',
                'symbol': symbol.upper()
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract ticker from Bybit response format
            if (data.get('retCode') == 0 and 'result' in data and 
                'list' in data['result'] and len(data['result']['list']) > 0):
                return data['result']['list'][0]
            else:
                logger.error(f"Bybit ticker API error for {symbol}: {data.get('retMsg', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            return None
    
    def get_instruments_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """Get instruments information for symbol or all linear instruments"""
        try:
            url = f"{self.base_url}/v5/market/instruments-info"
            params = {'category': 'linear'}
            
            if symbol:
                params['symbol'] = symbol.upper()
                
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') == 0 and 'result' in data:
                return data['result']
            else:
                logger.error(f"Bybit instruments info API error: {data.get('retMsg', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get instruments info: {e}")
            return None
    
    def get_current_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current funding rate (not historical) using funding info endpoint"""
        try:
            url = f"{self.base_url}/v5/market/funding/history"
            params = {
                'category': 'linear',
                'symbol': symbol.upper(),
                'limit': 1
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if (data.get('retCode') == 0 and 'result' in data and 
                'list' in data['result'] and len(data['result']['list']) > 0):
                # Get the most recent funding rate
                latest = data['result']['list'][0]
                return {
                    'symbol': latest.get('symbol'),
                    'fundingRate': latest.get('fundingRate'),
                    'fundingRateTimestamp': latest.get('fundingRateTimestamp')
                }
            else:
                logger.error(f"Bybit current funding rate error for {symbol}: {data.get('retMsg', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get current funding rate for {symbol}: {e}")
            return None 