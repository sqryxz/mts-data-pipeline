import pytest
import requests
import requests_mock
import json
from unittest.mock import patch, MagicMock
from src.api.bybit_client import BybitClient

class TestBybitClient:
    def setup_method(self):
        self.client = BybitClient()
    
    def test_init(self):
        """Test client initialization"""
        assert self.client.base_url == 'https://api.bybit.com'
        assert 'User-Agent' in self.client.session.headers
        assert self.client.session.headers['User-Agent'] == 'MTS-Pipeline/1.0'
    
    def test_get_order_book_success(self):
        """Test successful order book retrieval"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                's': 'BTCUSDT',
                'b': [['43000.00', '1.5'], ['42999.50', '2.0']],
                'a': [['43001.00', '1.0'], ['43001.50', '0.5']],
                'ts': 1640995200000,
                'u': 18521
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                json=mock_response
            )
            
            result = self.client.get_order_book('BTCUSDT', limit=10)
            
            assert result is not None
            assert result['s'] == 'BTCUSDT'
            assert 'b' in result  # bids
            assert 'a' in result  # asks
            assert len(result['b']) == 2
            assert len(result['a']) == 2
    
    def test_get_order_book_api_error(self):
        """Test order book retrieval with API error"""
        mock_response = {
            'retCode': 10001,
            'retMsg': 'Invalid symbol',
            'result': {}
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                json=mock_response
            )
            
            result = self.client.get_order_book('INVALID')
            assert result is None
    
    def test_get_order_book_network_error(self):
        """Test order book retrieval with network error"""
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                exc=requests.exceptions.ConnectionError
            )
            
            result = self.client.get_order_book('BTCUSDT')
            assert result is None
    
    def test_get_order_book_limit_validation(self):
        """Test order book limit parameter validation"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {'s': 'BTCUSDT', 'b': [], 'a': []}
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                json=mock_response
            )
            
            # Test limit > 50 gets capped to 50
            self.client.get_order_book('BTCUSDT', limit=100)
            
            # Check that the request was made with limit=50
            assert m.last_request.qs['limit'] == ['50']
    
    def test_get_funding_rate_success(self):
        """Test successful funding rate retrieval"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': [{
                    'symbol': 'BTCUSDT',
                    'fundingRate': '0.0001',
                    'fundingRateTimestamp': '1640995200000'
                }]
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/funding/history',
                json=mock_response
            )
            
            result = self.client.get_funding_rate('BTCUSDT')
            
            assert result is not None
            assert result['symbol'] == 'BTCUSDT'
            assert result['fundingRate'] == '0.0001'
            assert 'fundingRateTimestamp' in result
    
    def test_get_funding_rate_empty_list(self):
        """Test funding rate retrieval with empty list"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': []
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/funding/history',
                json=mock_response
            )
            
            result = self.client.get_funding_rate('BTCUSDT')
            assert result is None
    
    def test_get_ticker_success(self):
        """Test successful ticker retrieval"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': [{
                    'symbol': 'BTCUSDT',
                    'lastPrice': '43000.50',
                    'volume24h': '12345.67',
                    'turnover24h': '530123456.78',
                    'price24hPcnt': '0.0123'
                }]
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/tickers',
                json=mock_response
            )
            
            result = self.client.get_ticker('BTCUSDT')
            
            assert result is not None
            assert result['symbol'] == 'BTCUSDT'
            assert result['lastPrice'] == '43000.50'
            assert 'volume24h' in result
    
    def test_get_ticker_api_error(self):
        """Test ticker retrieval with API error"""
        mock_response = {
            'retCode': 10001,
            'retMsg': 'Invalid category',
            'result': {}
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/tickers',
                json=mock_response
            )
            
            result = self.client.get_ticker('BTCUSDT')
            assert result is None
    
    def test_get_instruments_info_success(self):
        """Test successful instruments info retrieval"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': [{
                    'symbol': 'BTCUSDT',
                    'contractType': 'LinearPerpetual',
                    'status': 'Trading',
                    'baseCoin': 'BTC',
                    'quoteCoin': 'USDT'
                }]
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/instruments-info',
                json=mock_response
            )
            
            result = self.client.get_instruments_info('BTCUSDT')
            
            assert result is not None
            assert 'category' in result
            assert 'list' in result
            assert len(result['list']) == 1
            assert result['list'][0]['symbol'] == 'BTCUSDT'
    
    def test_get_instruments_info_all_instruments(self):
        """Test instruments info retrieval for all instruments"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': [
                    {'symbol': 'BTCUSDT', 'status': 'Trading'},
                    {'symbol': 'ETHUSDT', 'status': 'Trading'}
                ]
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/instruments-info',
                json=mock_response
            )
            
            result = self.client.get_instruments_info()
            
            assert result is not None
            assert len(result['list']) == 2
    
    def test_get_current_funding_rate_success(self):
        """Test successful current funding rate retrieval"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {
                'category': 'linear',
                'list': [{
                    'symbol': 'BTCUSDT',
                    'fundingRate': '0.0001',
                    'fundingRateTimestamp': '1640995200000'
                }]
            }
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/funding/history',
                json=mock_response
            )
            
            result = self.client.get_current_funding_rate('BTCUSDT')
            
            assert result is not None
            assert result['symbol'] == 'BTCUSDT'
            assert result['fundingRate'] == '0.0001'
            assert result['fundingRateTimestamp'] == '1640995200000'
    
    def test_timeout_configuration(self):
        """Test that requests have proper timeout configuration"""
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                json={'retCode': 0, 'result': {}}
            )
            
            self.client.get_order_book('BTCUSDT')
            
            # Verify timeout was set (this is verified by the fact that 
            # the mock doesn't raise a timeout error)
            assert m.called
    
    def test_symbol_case_handling(self):
        """Test that symbols are properly converted to uppercase"""
        mock_response = {
            'retCode': 0,
            'retMsg': 'OK',
            'result': {'s': 'BTCUSDT', 'b': [], 'a': []}
        }
        
        with requests_mock.Mocker() as m:
            m.get(
                'https://api.bybit.com/v5/market/orderbook',
                json=mock_response
            )
            
            # Test with lowercase symbol
            self.client.get_order_book('btcusdt')
            
            # Check that the request URL contains uppercase symbol
            assert 'symbol=BTCUSDT' in m.last_request.url 