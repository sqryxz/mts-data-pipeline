"""
Tests for health monitoring service.

This module tests the HealthChecker class functionality including
data freshness checks, system health monitoring, and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.services.monitor import HealthChecker
from src.data.models import OHLCVData
from src.data.storage import CSVStorage


class TestHealthChecker:
    """Test the HealthChecker class functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_storage = Mock(spec=CSVStorage)
        self.health_checker = HealthChecker(
            storage=self.mock_storage,
            freshness_threshold_hours=2
        )
    
    def test_health_checker_initialization(self):
        """Test HealthChecker initialization."""
        # Test with default storage
        checker = HealthChecker()
        assert isinstance(checker.storage, CSVStorage)
        assert checker.freshness_threshold_hours == 2
        
        # Test with custom parameters
        custom_storage = Mock(spec=CSVStorage)
        custom_checker = HealthChecker(
            storage=custom_storage,
            freshness_threshold_hours=4
        )
        assert custom_checker.storage == custom_storage
        assert custom_checker.freshness_threshold_hours == 4
    
    def test_is_data_fresh_with_recent_data(self):
        """Test data freshness check with recent data."""
        # Create fresh data (1 hour old)
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(hours=1)).timestamp() * 1000)
        
        fresh_data = [
            OHLCVData(
                timestamp=fresh_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        # Test that data is considered fresh
        assert self.health_checker.is_data_fresh("bitcoin") is True
        
        # Verify storage was called correctly
        self.mock_storage.load_ohlcv_data.assert_called_once_with("bitcoin")
    
    def test_is_data_fresh_with_stale_data(self):
        """Test data freshness check with stale data."""
        # Create stale data (3 hours old, threshold is 2 hours)
        current_time = datetime.now()
        stale_timestamp = int((current_time - timedelta(hours=3)).timestamp() * 1000)
        
        stale_data = [
            OHLCVData(
                timestamp=stale_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = stale_data
        
        # Test that data is considered stale
        assert self.health_checker.is_data_fresh("bitcoin") is False
    
    def test_is_data_fresh_with_no_data(self):
        """Test data freshness check when no data exists."""
        self.mock_storage.load_ohlcv_data.return_value = []
        
        # Test that missing data is considered not fresh
        assert self.health_checker.is_data_fresh("bitcoin") is False
    
    def test_get_data_freshness_status_fresh_data(self):
        """Test detailed freshness status with fresh data."""
        # Create fresh data (30 minutes old)
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(minutes=30)).timestamp() * 1000)
        
        fresh_data = [
            OHLCVData(
                timestamp=fresh_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        status = self.health_checker.get_data_freshness_status("bitcoin")
        
        # Verify status fields
        assert status['crypto_id'] == "bitcoin"
        assert status['is_fresh'] is True
        assert status['status'] == 'fresh'
        assert 'message' in status
        assert status['latest_timestamp'] == fresh_timestamp
        assert status['age_hours'] < 1.0  # Should be 0.5 hours
        assert status['threshold_hours'] == 2
        assert status['record_count'] == 1
        assert 'checked_at' in status
    
    def test_get_data_freshness_status_stale_data(self):
        """Test detailed freshness status with stale data."""
        # Create stale data (4 hours old)
        current_time = datetime.now()
        stale_timestamp = int((current_time - timedelta(hours=4)).timestamp() * 1000)
        
        stale_data = [
            OHLCVData(
                timestamp=stale_timestamp,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = stale_data
        
        status = self.health_checker.get_data_freshness_status("bitcoin")
        
        # Verify status fields
        assert status['crypto_id'] == "bitcoin"
        assert status['is_fresh'] is False
        assert status['status'] == 'stale'
        assert status['age_hours'] >= 3.9  # Should be around 4 hours
        assert status['threshold_hours'] == 2
    
    def test_get_data_freshness_status_no_data(self):
        """Test detailed freshness status with no data."""
        self.mock_storage.load_ohlcv_data.return_value = []
        
        status = self.health_checker.get_data_freshness_status("bitcoin")
        
        # Verify no data status
        assert status['crypto_id'] == "bitcoin"
        assert status['is_fresh'] is False
        assert status['status'] == 'no_data'
        assert 'No data found' in status['message']
        assert status['latest_timestamp'] is None
        assert status['latest_datetime'] is None
        assert status['age_hours'] is None
    
    def test_get_data_freshness_status_with_multiple_records(self):
        """Test freshness status selection of most recent data."""
        current_time = datetime.now()
        
        # Create multiple data points with different ages
        data = [
            OHLCVData(  # 3 hours old (stale)
                timestamp=int((current_time - timedelta(hours=3)).timestamp() * 1000),
                open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0
            ),
            OHLCVData(  # 1 hour old (fresh) - this should be selected
                timestamp=int((current_time - timedelta(hours=1)).timestamp() * 1000),
                open=51000.0, high=52000.0, low=50000.0, close=51500.0, volume=150.0
            ),
            OHLCVData(  # 2.5 hours old (stale)
                timestamp=int((current_time - timedelta(hours=2, minutes=30)).timestamp() * 1000),
                open=49000.0, high=50000.0, low=48000.0, close=49500.0, volume=120.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = data
        
        status = self.health_checker.get_data_freshness_status("bitcoin")
        
        # Should use the most recent (1 hour old) data
        assert status['is_fresh'] is True
        assert status['age_hours'] < 1.1  # Should be around 1 hour
        assert status['record_count'] == 3
    
    def test_get_data_freshness_status_error_handling(self):
        """Test error handling in freshness status check."""
        # Mock storage to raise an exception
        self.mock_storage.load_ohlcv_data.side_effect = Exception("Storage error")
        
        status = self.health_checker.get_data_freshness_status("bitcoin")
        
        # Verify error status
        assert status['crypto_id'] == "bitcoin"
        assert status['is_fresh'] is False
        assert status['status'] == 'error'
        assert 'Storage error' in status['message']
        assert 'error' in status
    
    def test_check_all_cryptos_freshness_all_fresh(self):
        """Test batch freshness check with all fresh data."""
        # Create fresh data for all cryptos
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(hours=1)).timestamp() * 1000)
        
        fresh_data = [
            OHLCVData(
                timestamp=fresh_timestamp,
                open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        result = self.health_checker.check_all_cryptos_freshness(['bitcoin', 'ethereum'])
        
        # Verify overall status
        assert result['overall_status'] == 'healthy'
        assert result['is_healthy'] is True
        assert result['fresh_count'] == 2
        assert result['total_count'] == 2
        assert result['freshness_percentage'] == 100.0
        
        # Verify individual crypto results
        assert 'bitcoin' in result['cryptos']
        assert 'ethereum' in result['cryptos']
        assert result['cryptos']['bitcoin']['is_fresh'] is True
        assert result['cryptos']['ethereum']['is_fresh'] is True
    
    def test_check_all_cryptos_freshness_partial_fresh(self):
        """Test batch freshness check with some stale data."""
        current_time = datetime.now()
        
        def mock_load_data(crypto_id):
            if crypto_id == 'bitcoin':
                # Fresh data
                fresh_timestamp = int((current_time - timedelta(hours=1)).timestamp() * 1000)
                return [OHLCVData(timestamp=fresh_timestamp, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0)]
            elif crypto_id == 'ethereum':
                # Stale data
                stale_timestamp = int((current_time - timedelta(hours=3)).timestamp() * 1000)
                return [OHLCVData(timestamp=stale_timestamp, open=3000.0, high=3100.0, low=2900.0, close=3050.0, volume=200.0)]
            else:
                return []
        
        self.mock_storage.load_ohlcv_data.side_effect = mock_load_data
        
        result = self.health_checker.check_all_cryptos_freshness(['bitcoin', 'ethereum'])
        
        # Verify partial freshness
        assert result['overall_status'] == 'degraded'
        assert result['is_healthy'] is False
        assert result['fresh_count'] == 1
        assert result['total_count'] == 2
        assert result['freshness_percentage'] == 50.0
        
        # Verify individual results
        assert result['cryptos']['bitcoin']['is_fresh'] is True
        assert result['cryptos']['ethereum']['is_fresh'] is False
    
    def test_check_all_cryptos_freshness_all_stale(self):
        """Test batch freshness check with all stale data."""
        # Create stale data
        current_time = datetime.now()
        stale_timestamp = int((current_time - timedelta(hours=5)).timestamp() * 1000)
        
        stale_data = [
            OHLCVData(
                timestamp=stale_timestamp,
                open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = stale_data
        
        result = self.health_checker.check_all_cryptos_freshness(['bitcoin', 'ethereum'])
        
        # Verify unhealthy status
        assert result['overall_status'] == 'unhealthy'
        assert result['is_healthy'] is False
        assert result['fresh_count'] == 0
        assert result['total_count'] == 2
        assert result['freshness_percentage'] == 0.0
    
    def test_check_all_cryptos_freshness_default_cryptos(self):
        """Test batch freshness check with default crypto list."""
        # Mock fresh data
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(hours=1)).timestamp() * 1000)
        fresh_data = [OHLCVData(timestamp=fresh_timestamp, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0)]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        result = self.health_checker.check_all_cryptos_freshness()  # No crypto_ids provided
        
        # Should check default cryptos: bitcoin, ethereum, tether
        assert result['total_count'] == 3
        assert 'bitcoin' in result['cryptos']
        assert 'ethereum' in result['cryptos']
        assert 'tether' in result['cryptos']
    
    def test_get_system_health_status_healthy(self):
        """Test system health status when all components are healthy."""
        # Mock fresh data for all cryptos
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(hours=1)).timestamp() * 1000)
        fresh_data = [OHLCVData(timestamp=fresh_timestamp, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0)]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        health_status = self.health_checker.get_system_health_status()
        
        # Verify overall system health
        assert health_status['status'] == 'healthy'
        assert health_status['healthy'] is True
        assert 'All components healthy' in health_status['message']
        assert 'data_freshness' in health_status['components']
        assert health_status['components']['data_freshness']['is_healthy'] is True
    
    def test_get_system_health_status_unhealthy(self):
        """Test system health status when components are unhealthy."""
        # Mock stale data
        current_time = datetime.now()
        stale_timestamp = int((current_time - timedelta(hours=5)).timestamp() * 1000)
        stale_data = [OHLCVData(timestamp=stale_timestamp, open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0)]
        
        self.mock_storage.load_ohlcv_data.return_value = stale_data
        
        health_status = self.health_checker.get_system_health_status()
        
        # Verify unhealthy system
        assert health_status['status'] == 'unhealthy'
        assert health_status['healthy'] is False
        assert 'Some components unhealthy' in health_status['message']
        assert health_status['components']['data_freshness']['is_healthy'] is False
    
    def test_custom_freshness_threshold(self):
        """Test HealthChecker with custom freshness threshold."""
        # Create checker with 4-hour threshold
        custom_checker = HealthChecker(
            storage=self.mock_storage,
            freshness_threshold_hours=4
        )
        
        # Create data that's 3 hours old (would be stale with 2-hour threshold)
        current_time = datetime.now()
        timestamp_3h = int((current_time - timedelta(hours=3)).timestamp() * 1000)
        
        data_3h_old = [
            OHLCVData(
                timestamp=timestamp_3h,
                open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = data_3h_old
        
        # With 4-hour threshold, 3-hour-old data should be fresh
        assert custom_checker.is_data_fresh("bitcoin") is True
        
        status = custom_checker.get_data_freshness_status("bitcoin")
        assert status['is_fresh'] is True
        assert status['threshold_hours'] == 4
    
    def test_task_8_2_example(self):
        """Test the specific example from Task 8.2."""
        # Create fresh data
        current_time = datetime.now()
        fresh_timestamp = int((current_time - timedelta(minutes=30)).timestamp() * 1000)
        
        fresh_data = [
            OHLCVData(
                timestamp=fresh_timestamp,
                open=50000.0, high=51000.0, low=49000.0, close=50500.0, volume=100.0
            )
        ]
        
        self.mock_storage.load_ohlcv_data.return_value = fresh_data
        
        # Test the exact format from the task
        health_check = HealthChecker()
        health_check.storage = self.mock_storage
        
        assert health_check.is_data_fresh("bitcoin") == True 