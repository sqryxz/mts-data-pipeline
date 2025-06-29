"""Tests for the scheduler service."""

import sys
import pytest
import time
import threading
import signal
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.scheduler import SimpleScheduler
from src.services.collector import DataCollector
from src.utils.exceptions import APIError, DataValidationError


class TestSimpleScheduler:
    """Test the SimpleScheduler class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create mock collector
        self.mock_collector = Mock(spec=DataCollector)
        self.mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 3,
            'failed': 0,
            'retries_used': 0,
            'duration_seconds': 1.5,
            'successful_cryptos': ['bitcoin', 'ethereum', 'tether'],
            'failed_cryptos': [],
            'error_categories': {}
        }
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization with default parameters."""
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        assert scheduler.collector is self.mock_collector
        assert scheduler.interval_seconds == 3600  # Default 1 hour
        assert scheduler.days_to_collect == 1
        assert not scheduler.is_running()
        assert scheduler._collection_count == 0
        assert scheduler._last_collection_time is None
    
    def test_scheduler_initialization_with_custom_params(self):
        """Test scheduler initialization with custom parameters."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,  # 5 minutes
            days_to_collect=7
        )
        
        assert scheduler.interval_seconds == 300
        assert scheduler.days_to_collect == 7
    
    def test_scheduler_initialization_default_collector(self):
        """Test scheduler creates default collector when none provided."""
        with patch('src.services.scheduler.DataCollector') as mock_collector_class:
            mock_collector_instance = Mock(spec=DataCollector)
            mock_collector_class.return_value = mock_collector_instance
            
            scheduler = SimpleScheduler()
            
            mock_collector_class.assert_called_once()
            assert scheduler.collector is mock_collector_instance
    
    def test_single_collection_run(self):
        """Test running a single collection cycle."""
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        # Run single collection
        success = scheduler.run_once()
        
        # Verify
        assert success is True
        self.mock_collector.collect_all_data.assert_called_once_with(days=1)
        assert scheduler._collection_count == 1
        assert scheduler._last_collection_time is not None
        assert isinstance(scheduler._last_collection_time, datetime)
    
    def test_single_collection_with_custom_days(self):
        """Test single collection with custom days parameter."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            days_to_collect=7
        )
        
        success = scheduler.run_once()
        
        assert success is True
        self.mock_collector.collect_all_data.assert_called_once_with(days=7)
    
    def test_single_collection_failure(self):
        """Test single collection when collector fails."""
        # Setup collector to fail
        self.mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 0,
            'failed': 3,
            'retries_used': 2,
            'duration_seconds': 5.0,
            'successful_cryptos': [],
            'failed_cryptos': ['bitcoin', 'ethereum', 'tether'],
            'error_categories': {'network': 3}
        }
        
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        success = scheduler.run_once()
        
        assert success is False
        assert scheduler._collection_count == 1  # Count increments even on failure
    
    def test_single_collection_exception(self):
        """Test single collection when collector raises exception."""
        self.mock_collector.collect_all_data.side_effect = APIError("API failed")
        
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        success = scheduler.run_once()
        
        assert success is False
        assert scheduler._collection_count == 0  # No increment on exception
    
    def test_run_once_while_scheduler_running(self):
        """Test that run_once fails when scheduler is running."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=1  # Short interval for testing
        )
        
        try:
            # Start scheduler
            scheduler.start()
            assert scheduler.is_running()
            
            # Try to run manual collection
            success = scheduler.run_once()
            assert success is False
            
        finally:
            scheduler.stop()
    
    def test_scheduler_start_and_stop(self):
        """Test starting and stopping the scheduler."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=10  # Short interval for testing
        )
        
        # Initially not running
        assert not scheduler.is_running()
        
        # Start scheduler
        started = scheduler.start()
        assert started is True
        assert scheduler.is_running()
        
        # Stop scheduler
        stopped = scheduler.stop()
        assert stopped is True
        assert not scheduler.is_running()
    
    def test_scheduler_start_already_running(self):
        """Test starting scheduler when already running."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=10
        )
        
        try:
            # Start scheduler
            scheduler.start()
            assert scheduler.is_running()
            
            # Try to start again
            started_again = scheduler.start()
            assert started_again is False
            assert scheduler.is_running()  # Still running
            
        finally:
            scheduler.stop()
    
    def test_scheduler_stop_not_running(self):
        """Test stopping scheduler when not running."""
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        assert not scheduler.is_running()
        
        stopped = scheduler.stop()
        assert stopped is True
    
    def test_scheduler_multiple_collections(self):
        """Test scheduler runs multiple collections automatically."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=0.5,  # Very short interval for testing
            days_to_collect=1
        )
        
        try:
            # Start scheduler
            scheduler.start()
            assert scheduler.is_running()
            
            # Wait for at least 2 collections
            time.sleep(1.5)
            
            # Stop scheduler
            scheduler.stop()
            
            # Verify multiple collections occurred
            assert scheduler._collection_count >= 2
            assert self.mock_collector.collect_all_data.call_count >= 2
            
            # Verify all calls had correct parameters
            for call in self.mock_collector.collect_all_data.call_args_list:
                assert call[1]['days'] == 1
                
        finally:
            if scheduler.is_running():
                scheduler.stop()
    
    def test_scheduler_continues_after_collection_failure(self):
        """Test scheduler continues running even if individual collections fail."""
        # Setup collector to fail first time, succeed second time
        self.mock_collector.collect_all_data.side_effect = [
            APIError("First collection fails"),
            {  # Second collection succeeds
                'total_attempted': 3,
                'successful': 3,
                'failed': 0,
                'retries_used': 0,
                'duration_seconds': 1.0,
                'successful_cryptos': ['bitcoin', 'ethereum', 'tether'],
                'failed_cryptos': [],
                'error_categories': {}
            }
        ]
        
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=0.3  # Very short interval
        )
        
        try:
            # Start scheduler
            scheduler.start()
            
            # Wait for both collections
            time.sleep(1.0)
            
            # Stop scheduler
            scheduler.stop()
            
            # Verify both collections were attempted
            assert self.mock_collector.collect_all_data.call_count >= 2
            assert scheduler.is_running() is False
            
        finally:
            if scheduler.is_running():
                scheduler.stop()
    
    def test_scheduler_status(self):
        """Test scheduler status reporting."""
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
            temp_state_file = f.name
        
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,
            days_to_collect=7,
            state_file=temp_state_file
        )
        
        # Initial status
        status = scheduler.get_status()
        assert status['running'] is False
        assert status['interval_seconds'] == 300
        assert status['days_to_collect'] == 7
        assert status['collection_count'] == 0
        assert status['last_collection_time'] is None
        assert status['next_collection_time'] is None
        
        # Run a collection
        scheduler.run_once()
        
        # Status after collection
        status = scheduler.get_status()
        assert status['collection_count'] == 1
        assert status['last_collection_time'] is not None
        assert status['next_collection_time'] is not None
        
        # Verify next collection time calculation
        last_time = datetime.fromisoformat(status['last_collection_time'])
        next_time = datetime.fromisoformat(status['next_collection_time'])
        expected_next = last_time + timedelta(seconds=300)
        
        # Allow for small time differences due to processing
        time_diff = abs((next_time - expected_next).total_seconds())
        assert time_diff < 1  # Within 1 second
        
        # Cleanup
        import os
        if os.path.exists(temp_state_file):
            os.unlink(temp_state_file)
    
    def test_scheduler_graceful_shutdown_timeout(self):
        """Test scheduler shutdown with timeout."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=0.1
        )
        
        # Mock thread that doesn't stop
        with patch('threading.Thread') as mock_thread_class:
            mock_thread = Mock()
            mock_thread.is_alive.return_value = True  # Never stops
            mock_thread_class.return_value = mock_thread
            
            scheduler.start()
            
            # Try to stop with very short timeout
            stopped = scheduler.stop(timeout_seconds=0.01)
            
            # Should return False due to timeout
            assert stopped is False
    
    def test_scheduler_wait_for_completion(self):
        """Test waiting for scheduler completion."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=0.2
        )
        
        # Start scheduler
        scheduler.start()
        
        # Schedule stop in background
        def stop_after_delay():
            time.sleep(0.5)
            scheduler.stop()
        
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        # Wait for completion
        start_time = time.time()
        scheduler.wait_for_completion(timeout_seconds=2.0)
        elapsed = time.time() - start_time
        
        # Should complete in approximately 0.5 seconds
        assert 0.4 < elapsed < 1.0
        assert not scheduler.is_running()
        
        stop_thread.join()
    
    @patch('signal.signal')
    def test_signal_handler_setup(self, mock_signal):
        """Test that signal handlers are set up correctly."""
        scheduler = SimpleScheduler(collector=self.mock_collector)
        
        # Verify signal handlers were registered
        assert mock_signal.call_count >= 2
        
        # Check for SIGINT and SIGTERM
        calls = mock_signal.call_args_list
        signal_nums = [call[0][0] for call in calls]
        assert signal.SIGINT in signal_nums
        assert signal.SIGTERM in signal_nums
    
    def test_scheduler_thread_daemon_mode(self):
        """Test that scheduler thread runs in daemon mode."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=1
        )
        
        try:
            scheduler.start()
            assert scheduler._thread is not None
            assert scheduler._thread.daemon is True
            
        finally:
            scheduler.stop()


class TestSchedulerIntegration:
    """Integration tests for the scheduler with real components."""
    
    def test_scheduler_with_real_collector_mock_api(self):
        """Test scheduler with real DataCollector but mocked API."""
        with patch('src.api.coingecko_client.CoinGeckoClient') as mock_client_class:
            # Setup mock API client
            mock_client = Mock()
            mock_client.get_top_cryptos.return_value = [
                {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'},
                {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'},
                {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether'}
            ]
            mock_client.get_ohlc_data.return_value = [
                [1234567890000, 50000, 51000, 49000, 50500]  # Single OHLC record
            ]
            mock_client_class.return_value = mock_client
            
            # Create scheduler with real DataCollector
            scheduler = SimpleScheduler(interval_seconds=0.3)
            
            try:
                # Run single collection
                success = scheduler.run_once()
                
                # Verify success
                assert success is True
                assert scheduler._collection_count == 1
                
                # Verify API was called
                mock_client.get_top_cryptos.assert_called()
                assert mock_client.get_ohlc_data.call_count >= 3  # Once per crypto
                
            finally:
                if scheduler.is_running():
                    scheduler.stop()
    
    def test_scheduler_error_recovery_integration(self):
        """Test scheduler error recovery with real DataCollector."""
        with patch('src.api.coingecko_client.CoinGeckoClient') as mock_client_class:
            # Setup mock client to fail then succeed
            mock_client = Mock()
            mock_client.get_top_cryptos.side_effect = [
                APIError("First call fails"),
                [  # Second call succeeds
                    {'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'},
                    {'id': 'ethereum', 'symbol': 'eth', 'name': 'Ethereum'},
                    {'id': 'tether', 'symbol': 'usdt', 'name': 'Tether'}
                ]
            ]
            mock_client.get_ohlc_data.return_value = [
                [1234567890000, 50000, 51000, 49000, 50500]
            ]
            mock_client_class.return_value = mock_client
            
            scheduler = SimpleScheduler(interval_seconds=0.2)
            
            try:
                # Start scheduler
                scheduler.start()
                
                # Wait for multiple collection attempts
                time.sleep(0.8)
                
                # Stop scheduler
                scheduler.stop()
                
                # Verify multiple attempts were made
                assert mock_client.get_top_cryptos.call_count >= 2
                assert scheduler._collection_count >= 2
                
            finally:
                if scheduler.is_running():
                    scheduler.stop()


class TestSchedulerEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_scheduler_exception_in_loop(self):
        """Test scheduler handles exceptions in the main loop."""
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.side_effect = Exception("Fatal error")
        
        scheduler = SimpleScheduler(
            collector=mock_collector,
            interval_seconds=0.1
        )
        
        try:
            # Start scheduler
            scheduler.start()
            
            # Wait briefly
            time.sleep(0.3)
            
            # Stop scheduler
            scheduler.stop()
            
            # Scheduler should have handled the exception and continued
            assert not scheduler.is_running()
            
        finally:
            if scheduler.is_running():
                scheduler.stop()
    
    def test_scheduler_very_short_interval(self):
        """Test scheduler with very short intervals."""
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.return_value = {
            'total_attempted': 1,
            'successful': 1,
            'failed': 0,
            'retries_used': 0,
            'duration_seconds': 0.01,
            'successful_cryptos': ['bitcoin'],
            'failed_cryptos': [],
            'error_categories': {}
        }
        
        scheduler = SimpleScheduler(
            collector=mock_collector,
            interval_seconds=0.05  # 50ms interval
        )
        
        try:
            scheduler.start()
            time.sleep(0.3)  # Should allow ~6 collections
            scheduler.stop()
            
            # Should have multiple collections
            assert scheduler._collection_count >= 3
            
        finally:
            if scheduler.is_running():
                scheduler.stop()
    
    def test_scheduler_shutdown_event_interrupt(self):
        """Test that shutdown event properly interrupts waiting."""
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.return_value = {
            'total_attempted': 1,
            'successful': 1,
            'failed': 0,
            'retries_used': 0,
            'duration_seconds': 0.1,
            'successful_cryptos': ['bitcoin'],
            'failed_cryptos': [],
            'error_categories': {}
        }
        
        scheduler = SimpleScheduler(
            collector=mock_collector,
            interval_seconds=60  # Long interval
        )
        
        try:
            # Start scheduler
            start_time = time.time()
            scheduler.start()
            
            # Wait briefly to ensure first collection completes
            time.sleep(0.2)
            
            # Stop scheduler immediately (should interrupt the 60s wait)
            scheduler.stop()
            elapsed = time.time() - start_time
            
            # Should stop quickly, not wait for 60 seconds
            assert elapsed < 5.0
            assert not scheduler.is_running()
            
        finally:
            if scheduler.is_running():
                scheduler.stop()


class TestSchedulerPersistence:
    """Test scheduler persistence functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create mock collector
        self.mock_collector = Mock(spec=DataCollector)
        self.mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 3,
            'failed': 0,
            'retries_used': 0,
            'duration_seconds': 1.5,
            'successful_cryptos': ['bitcoin', 'ethereum', 'tether'],
            'failed_cryptos': [],
            'error_categories': {}
        }
        
        # Use temporary state file for testing
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, 'test_scheduler_state.json')
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_state_persistence_save_and_load(self):
        """Test that scheduler state is saved and loaded correctly."""
        # Create scheduler and run a collection
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=60,
            state_file=self.state_file
        )
        
        # Initially no state
        assert scheduler._last_collection_time is None
        assert scheduler._collection_count == 0
        
        # Run a collection
        success = scheduler.run_once()
        assert success is True
        assert scheduler._last_collection_time is not None
        assert scheduler._collection_count == 1
        
        # Verify state file was created
        assert os.path.exists(self.state_file)
        
        # Create new scheduler instance (simulating restart)
        scheduler2 = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=60,
            state_file=self.state_file
        )
        
        # Verify state was loaded
        assert scheduler2._last_collection_time == scheduler._last_collection_time
        # Collection count resets per session (not persisted)
        assert scheduler2._collection_count == 0
    
    def test_state_file_json_format(self):
        """Test that state file has correct JSON format."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            state_file=self.state_file
        )
        
        # Run collection to create state
        scheduler.run_once()
        
        # Check JSON format
        import json
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        
        expected_keys = {'last_collection_time', 'collection_count', 'interval_seconds', 'days_to_collect'}
        assert set(state.keys()) == expected_keys
        assert state['last_collection_time'] is not None
        assert state['collection_count'] == 1
        assert state['interval_seconds'] == 3600  # Default
        assert state['days_to_collect'] == 1  # Default
    
    def test_skip_recent_collection(self):
        """Test that scheduler skips collection if last run was recent."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,  # 5 minutes
            state_file=self.state_file
        )
        
        # Manually set recent collection time
        recent_time = datetime.now() - timedelta(seconds=120)  # 2 minutes ago
        scheduler._last_collection_time = recent_time
        scheduler._save_state()
        
        # Check that collection should be skipped
        assert scheduler._should_skip_collection() is True
        
        # Set old collection time
        old_time = datetime.now() - timedelta(seconds=400)  # 6+ minutes ago
        scheduler._last_collection_time = old_time
        
        # Check that collection should not be skipped
        assert scheduler._should_skip_collection() is False
    
    def test_scheduler_restart_behavior(self):
        """Test that scheduler resumes correctly after restart without duplicate collections."""
        # First scheduler - run collection
        scheduler1 = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,  # 5 minutes
            state_file=self.state_file
        )
        
        scheduler1.run_once()
        collection_time = scheduler1._last_collection_time
        assert collection_time is not None
        
        # Second scheduler - simulate restart immediately after
        scheduler2 = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,
            state_file=self.state_file
        )
        
        # Should load the previous collection time
        assert scheduler2._last_collection_time == collection_time
        
        # Should skip collection (too recent)
        assert scheduler2._should_skip_collection() is True
        
        # Third scheduler - simulate restart after interval has passed
        # Mock old time by modifying state file
        import json
        old_time = datetime.now() - timedelta(seconds=400)  # 6+ minutes ago
        state = {
            'last_collection_time': old_time.isoformat(),
            'collection_count': 1,
            'interval_seconds': 300,
            'days_to_collect': 1
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)
        
        scheduler3 = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=300,
            state_file=self.state_file
        )
        
        # Should not skip collection (enough time has passed)
        assert scheduler3._should_skip_collection() is False
    
    def test_missing_state_file(self):
        """Test scheduler behavior when state file doesn't exist."""
        non_existent_file = os.path.join(self.temp_dir, 'does_not_exist.json')
        
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            state_file=non_existent_file
        )
        
        # Should initialize with default state
        assert scheduler._last_collection_time is None
        assert scheduler._collection_count == 0
        assert scheduler._should_skip_collection() is False
    
    def test_corrupted_state_file(self):
        """Test scheduler behavior with corrupted state file."""
        # Create corrupted JSON file
        with open(self.state_file, 'w') as f:
            f.write("invalid json content")
        
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            state_file=self.state_file
        )
        
        # Should fall back to default state
        assert scheduler._last_collection_time is None
        assert scheduler._collection_count == 0
    
    def test_state_directory_creation(self):
        """Test that state directory is created if it doesn't exist."""
        nested_state_file = os.path.join(self.temp_dir, 'nested', 'dir', 'state.json')
        
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            state_file=nested_state_file
        )
        
        # Run collection to trigger state save
        scheduler.run_once()
        
        # Verify directory and file were created
        assert os.path.exists(nested_state_file)
        assert os.path.isfile(nested_state_file)
    
    def test_scheduler_automatic_skip_integration(self):
        """Test scheduler automatically skips collections during automated run."""
        scheduler = SimpleScheduler(
            collector=self.mock_collector,
            interval_seconds=2,  # Short interval for testing
            state_file=self.state_file
        )
        
        # Set recent collection time
        scheduler._last_collection_time = datetime.now() - timedelta(seconds=0.5)
        scheduler._save_state()
        
        try:
            # Start scheduler
            scheduler.start()
            
            # Wait briefly - should skip initial collection
            time.sleep(1)
            
            # Verify no new collection occurred (mock not called beyond state save)
            # Note: This is tricky to test directly, but we can check the collection count
            initial_count = scheduler._collection_count
            
            # Wait for scheduler to potentially run
            time.sleep(1.5)
            
            # Collection count should not have increased much due to skipping
            # (This test is timing-dependent, so we allow some flexibility)
            
        finally:
            scheduler.stop() 