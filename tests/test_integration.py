"""Integration tests for the complete MTS data pipeline workflow."""

import sys
import os
import pytest
import json
import tempfile
import shutil
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
import requests_mock

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.collector import DataCollector
from src.services.monitor import HealthChecker
from src.data.storage import CSVStorage
from src.api.coingecko_client import CoinGeckoClient
from src.utils.exceptions import APIError, DataValidationError


class TestIntegrationWorkflow:
    """Test complete end-to-end data collection workflow."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses for CoinGecko endpoints."""
        return {
            'top_cryptos': [
                {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1},
                {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum', 'market_cap_rank': 2},
                {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether', 'market_cap_rank': 3}
            ],
            'bitcoin_ohlc': [
                [1640995200000, 47686.91, 47798.51, 47431.67, 47747.68],  # 2022-01-01
                [1640998800000, 47747.68, 47885.23, 47612.45, 47803.12],
                [1641002400000, 47803.12, 47950.78, 47723.89, 47876.34],
                [1641006000000, 47876.34, 48012.56, 47834.12, 47923.45]
            ],
            'ethereum_ohlc': [
                [1640995200000, 3701.23, 3789.45, 3678.12, 3756.78],
                [1640998800000, 3756.78, 3823.67, 3734.56, 3789.12],
                [1641002400000, 3789.12, 3845.23, 3756.89, 3812.45],
                [1641006000000, 3812.45, 3887.34, 3798.67, 3845.12]
            ],
            'tether_ohlc': [
                [1640995200000, 0.9998, 1.0012, 0.9995, 1.0005],
                [1640998800000, 1.0005, 1.0018, 1.0001, 1.0009],
                [1641002400000, 1.0009, 1.0015, 0.9998, 1.0003],
                [1641006000000, 1.0003, 1.0021, 0.9997, 1.0012]
            ]
        }
    
    def test_complete_data_collection_workflow(self, temp_data_dir, mock_api_responses):
        """Test complete end-to-end data collection workflow with mocked API."""
        # Setup temporary data directory for CSV storage
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping', 
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets', 
                  json=mock_api_responses['top_cryptos'])
            
            # Mock OHLC endpoints for each crypto
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=mock_api_responses['bitcoin_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=mock_api_responses['tether_ohlc'])
            
            # Initialize collector with custom storage and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify collection results
            assert results['successful'] == 3
            assert results['failed'] == 0
            assert set(results['successful_cryptos']) == {'bitcoin', 'ethereum', 'tether'}
            assert results['total_records_collected'] == 12  # 4 records per crypto
            
            # Verify CSV files were created
            current_year = datetime.now().year
            expected_files = [
                os.path.join(temp_data_dir, f'bitcoin_{current_year}.csv'),
                os.path.join(temp_data_dir, f'ethereum_{current_year}.csv'),
                os.path.join(temp_data_dir, f'tether_{current_year}.csv')
            ]
            
            for file_path in expected_files:
                assert os.path.exists(file_path), f"CSV file not found: {file_path}"
                
                # Verify CSV content
                df = pd.read_csv(file_path)
                assert len(df) == 4, f"Expected 4 records in {file_path}"
                assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                
                # Verify data types and values
                assert df['timestamp'].notna().all()
                assert df['open'].notna().all()
                assert (df['open'] > 0).all()
                assert (df['high'] >= df['open']).all()
                assert (df['low'] <= df['close']).all()
            
            # Verify Bitcoin specific data
            bitcoin_df = pd.read_csv(os.path.join(temp_data_dir, f'bitcoin_{current_year}.csv'))
            assert bitcoin_df.iloc[0]['open'] == 47686.91
            assert bitcoin_df.iloc[0]['close'] == 47747.68
            
            # Verify Ethereum specific data
            ethereum_df = pd.read_csv(os.path.join(temp_data_dir, f'ethereum_{current_year}.csv'))
            assert ethereum_df.iloc[0]['open'] == 3701.23
            assert ethereum_df.iloc[0]['close'] == 3756.78
    
    def test_partial_failure_collection_workflow(self, temp_data_dir, mock_api_responses):
        """Test workflow when some cryptos fail but others succeed."""
        storage = CSVStorage(data_dir=temp_data_dir)
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mock_api_responses['top_cryptos'])
            
            # Mock successful OHLC endpoints
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=mock_api_responses['bitcoin_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            
            # Mock failed OHLC endpoint for tether
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  status_code=500, text='Internal Server Error')
            
            # Initialize collector with custom storage and run collection
            collector = DataCollector(storage=storage)
            results = collector.collect_all_data(days=1)
            
            # Verify partial success results
            assert results['successful'] == 2
            assert results['failed'] == 1
            assert set(results['successful_cryptos']) == {'bitcoin', 'ethereum'}
            assert results['failed_cryptos'] == ['tether']
            assert results['total_records_collected'] == 8  # 4 records each for bitcoin, ethereum
            
            # Verify successful CSV files were created
            current_year = datetime.now().year
            successful_files = [
                os.path.join(temp_data_dir, f'bitcoin_{current_year}.csv'),
                os.path.join(temp_data_dir, f'ethereum_{current_year}.csv')
            ]
            
            for file_path in successful_files:
                assert os.path.exists(file_path)
                df = pd.read_csv(file_path)
                assert len(df) == 4
            
            # Verify failed CSV file was not created
            tether_file = os.path.join(temp_data_dir, f'tether_{current_year}.csv')
            assert not os.path.exists(tether_file)
    
    @patch('src.data.storage.CSVStorage')
    def test_health_monitoring_integration(self, mock_csv_storage, temp_data_dir, mock_api_responses):
        """Test health monitoring integration after data collection."""
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Setup API mocks
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mock_api_responses['top_cryptos'])
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=mock_api_responses['bitcoin_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=mock_api_responses['tether_ohlc'])
            
            # Run data collection
            collector = DataCollector()
            collector.collect_all_data(days=1)
            
            # Test health monitoring
            health_checker = HealthChecker(data_dir=temp_data_dir)
            
            # Check individual crypto freshness
            assert health_checker.is_data_fresh('bitcoin') is True
            assert health_checker.is_data_fresh('ethereum') is True
            assert health_checker.is_data_fresh('tether') is True
            
            # Check system health status
            system_health = health_checker.get_system_health_status()
            assert system_health['healthy'] is True
            assert system_health['status'] == 'healthy'
            assert system_health['components']['data_freshness']['fresh_count'] == 3
            assert system_health['components']['data_freshness']['total_count'] == 3
    
    @patch('src.data.storage.CSVStorage')
    def test_api_connection_failure(self, mock_csv_storage, temp_data_dir):
        """Test workflow when API connection fails completely."""
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Mock complete API failure
            m.get('https://api.coingecko.com/api/v3/ping', 
                  exc=requests_mock.exceptions.ConnectTimeout)
            
            # Initialize collector and attempt collection
            collector = DataCollector()
            results = collector.collect_all_data(days=1)
            
            # Verify complete failure
            assert results['successful'] == 0
            assert results['failed'] == 3
            assert results['total_records_collected'] == 0
            assert len(results['error_categories']) > 0
            
            # Verify no CSV files were created
            current_year = datetime.now().year
            csv_files = [f'bitcoin_{current_year}.csv', f'ethereum_{current_year}.csv', f'tether_{current_year}.csv']
            for filename in csv_files:
                file_path = os.path.join(temp_data_dir, filename)
                assert not os.path.exists(file_path)
    
    @patch('src.data.storage.CSVStorage')
    def test_invalid_api_response(self, mock_csv_storage, temp_data_dir):
        """Test workflow with invalid API response data."""
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Mock ping endpoint
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            
            # Mock top cryptocurrencies endpoint with invalid data
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=[{'invalid': 'data'}])  # Missing required fields
            
            # Initialize collector and attempt collection
            collector = DataCollector()
            results = collector.collect_all_data(days=1)
            
            # Verify graceful handling of invalid data
            assert results['successful'] == 0
            assert results['failed'] >= 1  # Could fail at crypto list or individual collections
            assert results['total_records_collected'] == 0
    
    @patch('src.data.storage.CSVStorage')
    def test_storage_directory_creation(self, mock_csv_storage, temp_data_dir, mock_api_responses):
        """Test that storage directory is created if it doesn't exist."""
        # Create a nested path that doesn't exist
        nested_dir = os.path.join(temp_data_dir, 'nested', 'data', 'directory')
        mock_storage_instance = CSVStorage(data_dir=nested_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Setup API mocks
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mock_api_responses['top_cryptos'])
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=mock_api_responses['bitcoin_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=mock_api_responses['tether_ohlc'])
            
            # Verify directory doesn't exist initially
            assert not os.path.exists(nested_dir)
            
            # Run collection
            collector = DataCollector()
            results = collector.collect_all_data(days=1)
            
            # Verify directory was created and data was stored
            assert os.path.exists(nested_dir)
            assert results['successful'] == 3
            
            # Verify CSV files exist in the nested directory
            current_year = datetime.now().year
            for crypto in ['bitcoin', 'ethereum', 'tether']:
                csv_path = os.path.join(nested_dir, f'{crypto}_{current_year}.csv')
                assert os.path.exists(csv_path)
    
    @patch('src.data.storage.CSVStorage')
    def test_data_validation_integration(self, mock_csv_storage, temp_data_dir, mock_api_responses):
        """Test data validation during the complete workflow."""
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Setup API mocks
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mock_api_responses['top_cryptos'])
            
            # Mock OHLC with some invalid data
            invalid_ohlc = [
                [1640995200000, -100, 47798.51, 47431.67, 47747.68],  # Negative open price
                [1640998800000, 47747.68, 47885.23, 47612.45, 47803.12],
                [1641002400000, 47803.12, 47950.78, 47723.89, 47876.34],
            ]
            
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc', json=invalid_ohlc)
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=mock_api_responses['tether_ohlc'])
            
            # Run collection
            collector = DataCollector()
            results = collector.collect_all_data(days=1)
            
            # Should have failed validation for bitcoin but succeeded for others
            assert results['successful'] == 2  # ethereum and tether
            assert results['failed'] == 1  # bitcoin
            assert 'bitcoin' in results['failed_cryptos']
            assert 'validation' in results.get('error_categories', {})


class TestIntegrationCommandLine:
    """Test integration through command-line interface."""
    
    @patch('src.data.storage.CSVStorage')
    def test_main_collect_integration(self, mock_csv_storage, temp_data_dir):
        """Test complete workflow through main.py command-line interface."""
        import main
        
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        # Mock successful API responses
        with requests_mock.Mocker() as m:
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets', json=[
                {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin', 'market_cap_rank': 1},
                {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum', 'market_cap_rank': 2},
                {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether', 'market_cap_rank': 3}
            ])
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc', json=[
                [1640995200000, 47686.91, 47798.51, 47431.67, 47747.68]
            ])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc', json=[
                [1640995200000, 3701.23, 3789.45, 3678.12, 3756.78]
            ])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc', json=[
                [1640995200000, 0.9998, 1.0012, 0.9995, 1.0005]
            ])
            
            # Mock command-line arguments
            with patch('sys.argv', ['main.py', '--collect', '--days', '1']):
                exit_code = main.main()
                
                # Verify successful execution
                assert exit_code == 0
                
                # Verify CSV files were created
                current_year = datetime.now().year
                for crypto in ['bitcoin', 'ethereum', 'tether']:
                    csv_path = os.path.join(temp_data_dir, f'{crypto}_{current_year}.csv')
                    assert os.path.exists(csv_path)
                    df = pd.read_csv(csv_path)
                    assert len(df) == 1  # One record for 1 day


class TestIntegrationHealthMonitoring:
    """Test integration of health monitoring with data collection."""
    
    @patch('src.data.storage.CSVStorage')
    def test_health_endpoint_integration(self, mock_csv_storage, temp_data_dir, mock_api_responses):
        """Test health endpoint after data collection."""
        import main
        
        mock_storage_instance = CSVStorage(data_dir=temp_data_dir)
        mock_csv_storage.return_value = mock_storage_instance
        
        with requests_mock.Mocker() as m:
            # Setup API mocks
            m.get('https://api.coingecko.com/api/v3/ping',
                  json={'gecko_says': '(V3) To the Moon!'})
            m.get('https://api.coingecko.com/api/v3/coins/markets',
                  json=mock_api_responses['top_cryptos'])
            m.get('https://api.coingecko.com/api/v3/coins/bitcoin/ohlc',
                  json=mock_api_responses['bitcoin_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/ethereum/ohlc',
                  json=mock_api_responses['ethereum_ohlc'])
            m.get('https://api.coingecko.com/api/v3/coins/tether/ohlc',
                  json=mock_api_responses['tether_ohlc'])
            
            # First run data collection
            collector = DataCollector()
            collector.collect_all_data(days=1)
            
            # Then test health endpoint
            health_checker = HealthChecker(data_dir=temp_data_dir)
            
            # Create handler and test health check
            handler = object.__new__(main.HealthRequestHandler)
            handler.health_checker = health_checker
            handler.path = '/health'
            
            # Mock response methods
            handler.send_response = Mock()
            handler.send_header = Mock()
            handler.end_headers = Mock()
            handler.wfile = Mock()
            
            # Execute health check
            handler._handle_health_check()
            
            # Verify healthy response
            handler.send_response.assert_called_once_with(200)
            
            # Parse response JSON
            write_calls = handler.wfile.write.call_args_list
            assert len(write_calls) == 1
            response_data = write_calls[0][0][0].decode('utf-8')
            response_json = json.loads(response_data)
            
            # Verify health status
            assert response_json['status'] == 'healthy'
            assert response_json['healthy'] is True
            assert response_json['components']['data_freshness']['fresh_count'] == 3 