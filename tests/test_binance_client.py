import pytest
from src.api.binance_client import BinanceClient

class TestBinanceClient:
    def setup_method(self):
        self.client = BinanceClient()
    
    def test_get_order_book(self):
        """Test order book retrieval"""
        result = self.client.get_order_book('BTCUSDT', limit=10)
        assert result is not None
        assert 'bids' in result
        assert 'asks' in result
        assert len(result['bids']) <= 10
        assert len(result['asks']) <= 10
    
    def test_get_funding_rate(self):
        """Test funding rate retrieval"""
        result = self.client.get_funding_rate('BTCUSDT')
        assert result is not None
        assert 'symbol' in result
        assert 'lastFundingRate' in result
        assert result['symbol'] == 'BTCUSDT'
    
    def test_get_ticker(self):
        """Test ticker retrieval"""
        result = self.client.get_ticker('BTCUSDT')
        assert result is not None
        assert 'symbol' in result
        assert 'lastPrice' in result
        assert result['symbol'] == 'BTCUSDT' 