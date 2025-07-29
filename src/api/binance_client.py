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

    def get_historical_klines(self, symbol: str, interval: str, start_time: str, end_time: str) -> list:
        """
        Fetch historical klines (candlesticks) from Binance Futures API.
        Args:
            symbol: e.g., 'BTCUSDT'
            interval: e.g., '1m', '5m', '1h'
            start_time: string, e.g., '2024-01-01 00:00:00'
            end_time: string, e.g., '2024-01-07 00:00:00'
        Returns:
            List of klines (each kline is a list)
        """
        try:
            url = f"{self.base_url}/fapi/v1/klines"
            # Convert to milliseconds
            start_ts = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))) * 1000
            end_ts = int(time.mktime(time.strptime(end_time, '%Y-%m-%d %H:%M:%S'))) * 1000
            all_klines = []
            limit = 1500  # Binance max per request
            while start_ts < end_ts:
                params = {
                    'symbol': symbol.upper(),
                    'interval': interval,
                    'startTime': start_ts,
                    'endTime': min(end_ts, start_ts + limit * 60 * 1000),
                    'limit': limit
                }
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                klines = response.json()
                if not klines:
                    break
                all_klines.extend(klines)
                last_open_time = klines[-1][0]
                # Move to next window
                start_ts = last_open_time + 60 * 1000
                if len(klines) < limit:
                    break
                time.sleep(0.2)  # avoid rate limit
            return all_klines
        except Exception as e:
            logger.error(f"Failed to fetch historical klines for {symbol}: {e}")
            return [] 