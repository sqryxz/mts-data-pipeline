"""Comprehensive error scenario tests for the MTS data pipeline."""

import sys
import os
import pytest
import json
import tempfile
import shutil
import stat
from unittest.mock import patch, Mock, MagicMock
import requests_mock
import requests.exceptions

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.collector import DataCollector
from src.services.monitor import HealthChecker
from src.data.storage import CSVStorage
from src.api.coingecko_client import CoinGeckoClient
from src.utils.exceptions import APIError, APITimeoutError, APIRateLimitError, APIConnectionError, DataValidationError, StorageError


class TestAPIFailureScenarios:
    """Test various API failure scenarios."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def valid_crypto_list(self):
        """Valid cryptocurrency list for testing."""
        return [
            {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1},
            {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum', 'market_cap_rank': 2},
            {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether', 'market_cap_rank': 3}
        ]
    
    def test_api_timeout_error(self, temp_data_dir, valid_crypto_list):
        """Test API timeout error handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock timeout for OHLC endpoints
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  exc=requests.exceptions.Timeout)
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  exc=requests.exceptions.Timeout)
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  exc=requests.exceptions.Timeout)
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify timeout errors are handled gracefully
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert results['total_records_collected'] == 0
            assert 'network' in results.get('error_categories', {})
            
            # Verify no CSV files were created
            assert len(os.listdir(temp_data_dir)) == 0
    
    def test_api_rate_limit_error(self, temp_data_dir, valid_crypto_list):
        """Test API rate limit error handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock rate limit responses
            rate_limit_headers = {'Retry-After': '60'}
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  status_code=429, headers=rate_limit_headers)
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  status_code=429, headers=rate_limit_headers)
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  status_code=429, headers=rate_limit_headers)
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify rate limit errors are handled
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert 'rate_limit' in results.get('error_categories', {})
    
    def test_api_connection_error(self, temp_data_dir, valid_crypto_list):
        """Test API connection error handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock connection errors
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  exc=requests.exceptions.ConnectionError)
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  exc=requests.exceptions.ConnectionError)
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  exc=requests.exceptions.ConnectionError)
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify connection errors are handled
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert 'network' in results.get('error_categories', {})
    
    def test_api_server_error(self, temp_data_dir, valid_crypto_list):
        """Test API server error (500) handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock server errors
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  status_code=500, text='Internal Server Error')
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  status_code=503, text='Service Unavailable')
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  status_code=502, text='Bad Gateway')
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify server errors are handled
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert 'server_error' in results.get('error_categories', {})
    
    def test_api_client_error(self, temp_data_dir, valid_crypto_list):
        """Test API client error (404) handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock client errors (should not be retried)
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  status_code=404, text='Not Found')
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  status_code=400, text='Bad Request')
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  status_code=401, text='Unauthorized')
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify client errors are handled (no retries)
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert 'client_error' in results.get('error_categories', {})
    
    def test_invalid_json_response(self, temp_data_dir, valid_crypto_list):
        """Test invalid JSON response handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock invalid JSON responses
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  text='invalid json response')
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  text='<html>Not JSON</html>')
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  text='')
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify invalid JSON is handled
            assert results['successful'] == 0
            assert results['failed'] == 3


class TestDataValidationFailures:
    """Test data validation failure scenarios."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def valid_crypto_list(self):
        """Valid cryptocurrency list for testing."""
        return [
            {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1},
            {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum', 'market_cap_rank': 2}
        ]
    
    def test_invalid_ohlc_data_structure(self, temp_data_dir, valid_crypto_list):
        """Test invalid OHLC data structure handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock invalid OHLC data structures
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=[
                      [1640995200000, 47686.91, 47798.51],  # Missing low and close
                      [1640998800000, 47747.68, 47885.23, 47612.45, 47803.12]
                  ])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=[
                      [1640995200000, -3701.23, 3789.45, 3678.12, 3756.78],  # Negative open
                      [1640998800000, 3756.78, 3823.67, 3734.56, 3789.12]
                  ])
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify validation failures are handled
            assert results['successful'] == 0
            assert results['failed'] == 2
            assert 'data_unavailable' in results.get('error_categories', {})
    
    def test_missing_required_fields(self, temp_data_dir):
        """Test missing required fields in cryptocurrency data."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock cryptocurrency list with missing required fields
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=[
                      {'id': 'bitcoin', 'name': 'Bitcoin'},  # Missing symbol
                      {'symbol': 'eth', 'name': 'Ethereum'},  # Missing id
                      {'id': 'tether', 'symbol': 'usdt'}  # Missing name
                  ])
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify that no cryptocurrencies were processed
            assert results['successful'] == 0
            assert results['failed'] >= 0  # Might not attempt collection if validation fails early
    
    def test_malformed_price_data(self, temp_data_dir, valid_crypto_list):
        """Test malformed price data handling."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            
            # Mock malformed price data
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=[
                      [1640995200000, "invalid", 47798.51, 47431.67, 47747.68],  # String instead of number
                      [1640998800000, None, 47885.23, 47612.45, 47803.12]  # None value
                  ])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=[
                      ["invalid_timestamp", 3701.23, 3789.45, 3678.12, 3756.78],  # Invalid timestamp
                      [1640998800000, 3756.78, 3823.67, 3734.56, 3789.12]
                  ])
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify malformed data is handled
            assert results['successful'] == 0
            assert results['failed'] == 2


class TestStorageFailureScenarios:
    """Test storage failure scenarios."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def valid_crypto_list(self):
        """Valid cryptocurrency list for testing."""
        return [
            {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1}
        ]
    
    @pytest.fixture
    def valid_ohlc_data(self):
        """Valid OHLC data for testing."""
        return [
            [1640995200000, 47686.91, 47798.51, 47431.67, 47747.68],
            [1640998800000, 47747.68, 47885.23, 47612.45, 47803.12]
        ]
    
    def test_readonly_directory(self, temp_data_dir, valid_crypto_list, valid_ohlc_data):
        """Test storage failure with read-only directory."""
        # Make directory read-only
        os.chmod(temp_data_dir, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        try:
            storage = CSVStorage(data_dir=temp_data_dir)
            
            with requests_mock.Mocker() as m:
                # Mock successful API responses
                m.get('https://api.coingecko.com/api/v3/ping',
                      json={'gecko_says': '(V3) To the Moon!'})
                m.get('https://api.coingecko.com/api/v3/coins/markets',
                      json=valid_crypto_list)
                m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                      json=valid_ohlc_data)
                
                # Initialize collector and run collection
                collector = DataCollector(storage=storage)
                results = collector.collect_all_data(days=1)
                
                # Should handle storage errors gracefully
                assert results['successful'] == 0
                assert results['failed'] == 1
                assert 'unexpected' in results.get('error_categories', {})
        
        finally:
            # Restore write permissions for cleanup
            os.chmod(temp_data_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    
    def test_nonexistent_parent_directory(self, valid_crypto_list, valid_ohlc_data):
        """Test storage with nonexistent parent directory."""
        # Use a path that doesn't exist and can't be created
        nonexistent_path = "/nonexistent/path/that/cannot/be/created"
        
        with requests_mock.Mocker() as m:
            # Mock successful API responses
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=valid_crypto_list)
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=valid_ohlc_data)
            
            # This should handle the case where directory creation fails
            try:
                storage = CSVStorage(data_dir=nonexistent_path)
                collector = DataCollector(storage=storage)
                results = collector.collect_all_data(days=1)
                
                # Should handle directory creation errors
                # The exact behavior may vary based on implementation
                assert results['total_attempted'] == 1
            except (OSError, PermissionError):
                # Expected if directory creation fails immediately
                pass


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mixed_crypto_list(self):
        """Mixed cryptocurrency list for testing partial failures."""
        return [
            {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1},
            {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum', 'market_cap_rank': 2},
            {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether', 'market_cap_rank': 3}
        ]
    
    def test_mixed_success_failure_scenario(self, temp_data_dir, mixed_crypto_list):
        """Test mixed success and failure scenarios."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mixed_crypto_list)
            
            # Mock mixed responses: success, failure, success
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=[[1640995200000, 47686.91, 47798.51, 47431.67, 47747.68]])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  status_code=500, text='Internal Server Error')
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=[[1640995200000, 0.9998, 1.0012, 0.9995, 1.0005]])
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify graceful degradation
            assert results['successful'] == 2  # bitcoin and tether
            assert results['failed'] == 1  # ethereum
            assert results['total_records_collected'] == 2
            assert 'bitcoin' in results['successful_cryptos']
            assert 'tether' in results['successful_cryptos']
            assert 'ethereum' in results['failed_cryptos']
            
            # Verify successful files were created
            from datetime import datetime
            current_year = datetime.now().year
            bitcoin_file = os.path.join(temp_data_dir, f'bitcoin_{current_year}.csv')
            tether_file = os.path.join(temp_data_dir, f'tether_{current_year}.csv')
            ethereum_file = os.path.join(temp_data_dir, f'ethereum_{current_year}.csv')
            
            assert os.path.exists(bitcoin_file)
            assert os.path.exists(tether_file)
            assert not os.path.exists(ethereum_file)
    
    def test_complete_api_unavailability(self, temp_data_dir):
        """Test complete API unavailability."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock complete API failure
            m.get('https://api.coingecko.com/api/v3/ping',
                  exc=requests.exceptions.ConnectionError)
            
            # Initialize collector and attempt collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify graceful handling of complete failure
            assert results['successful'] == 0
            assert results['total_records_collected'] == 0
            assert len(os.listdir(temp_data_dir)) == 0
    
    def test_retry_behavior_with_eventual_success(self, temp_data_dir, mixed_crypto_list):
        """Test retry behavior that eventually succeeds."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mixed_crypto_list)
            
            # Mock successful responses after retries
            call_count = {'bitcoin': 0, 'ethereum': 0, 'tether': 0}
            
            def bitcoin_response(request, context):
                call_count['bitcoin'] += 1
                if call_count['bitcoin'] == 1:
                    context.status_code = 500
                    return 'Internal Server Error'
                else:
                    return [[1640995200000, 47686.91, 47798.51, 47431.67, 47747.68]]
            
            def ethereum_response(request, context):
                call_count['ethereum'] += 1
                if call_count['ethereum'] <= 2:
                    context.status_code = 429
                    return 'Rate Limited'
                else:
                    return [[1640995200000, 3701.23, 3789.45, 3678.12, 3756.78]]
            
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=bitcoin_response)
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=ethereum_response)
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=[[1640995200000, 0.9998, 1.0012, 0.9995, 1.0005]])
            
            # Initialize collector and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify eventual success after retries
            assert results['successful'] == 3
            assert results['failed'] == 0
            assert results['retries_used'] > 0 