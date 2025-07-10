import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from src.services.funding_collector import FundingCollector
from src.api.binance_client import BinanceClient
from src.data.realtime_storage import RealtimeStorage
from src.data.realtime_models import FundingRate
import tempfile
import shutil


@pytest.fixture
def mock_binance_client():
    """Mock Binance client for testing."""
    client = Mock(spec=BinanceClient)
    client.get_funding_rate.return_value = {
        'symbol': 'BTCUSDT',
        'lastFundingRate': '0.00010000',
        'nextFundingTime': int(time.time() * 1000) + 8 * 3600 * 1000  # 8 hours from now
    }
    return client


@pytest.fixture
def mock_storage():
    """Mock RealtimeStorage for testing."""
    storage = Mock(spec=RealtimeStorage)
    storage.store_funding_rate.return_value = True
    return storage


@pytest.fixture
def funding_collector(mock_storage):
    """FundingCollector instance with mocked dependencies."""
    collector = FundingCollector(storage=mock_storage)
    return collector


@pytest.fixture
def sample_funding_rate():
    """Create a sample funding rate for testing."""
    return FundingRate(
        exchange='binance',
        symbol='BTCUSDT',
        timestamp=int(time.time() * 1000),
        funding_rate=0.0001,
        predicted_rate=0.0001,
        funding_time=int(time.time() * 1000) + 8 * 3600 * 1000
    )


class TestFundingCollectorInitialization:
    """Test FundingCollector initialization."""

    def test_initialization_with_default_storage(self):
        """Test initialization with default storage."""
        collector = FundingCollector()
        
        assert collector.binance_client is not None
        assert collector.storage is not None
        assert collector.is_running is False
        assert collector.collection_task is None
        assert collector.last_rates == {}

    def test_initialization_with_custom_storage(self, mock_storage):
        """Test initialization with custom storage."""
        collector = FundingCollector(storage=mock_storage)
        
        assert collector.storage is mock_storage
        assert collector.binance_client is not None
        assert collector.is_running is False


class TestFundingRateCollection:
    """Test funding rate collection functionality."""

    @pytest.mark.asyncio
    async def test_collect_single_funding_rate_success(self, funding_collector, mock_binance_client):
        """Test successful single funding rate collection."""
        funding_collector.binance_client = mock_binance_client
        
        result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        assert result is not None
        assert result.exchange == 'binance'
        assert result.symbol == 'BTCUSDT'
        assert result.funding_rate == 0.0001
        
        # Verify storage was called
        funding_collector.storage.store_funding_rate.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_single_funding_rate_api_failure(self, funding_collector, mock_binance_client):
        """Test handling of API failure during single collection."""
        mock_binance_client.get_funding_rate.return_value = None
        funding_collector.binance_client = mock_binance_client
        
        result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        assert result is None
        # Storage should not be called
        funding_collector.storage.store_funding_rate.assert_not_called()

    @pytest.mark.asyncio
    async def test_collect_funding_rates_multiple_symbols(self, funding_collector, mock_binance_client):
        """Test collecting funding rates for multiple symbols."""
        funding_collector.binance_client = mock_binance_client
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        results = await funding_collector.collect_funding_rates(symbols)
        
        assert len(results) == 2
        assert results['BTCUSDT'] is True
        assert results['ETHUSDT'] is True
        
        # Binance client should be called for each symbol
        assert mock_binance_client.get_funding_rate.call_count == 2

    @pytest.mark.asyncio
    async def test_collect_funding_rates_partial_failure(self, funding_collector, mock_binance_client):
        """Test handling partial failure when collecting multiple symbols."""
        def side_effect(symbol):
            if symbol == 'BTCUSDT':
                return {
                    'symbol': 'BTCUSDT',
                    'lastFundingRate': '0.00010000',
                    'nextFundingTime': int(time.time() * 1000) + 8 * 3600 * 1000
                }
            else:
                return None  # Simulate failure for ETHUSDT
        
        mock_binance_client.get_funding_rate.side_effect = side_effect
        funding_collector.binance_client = mock_binance_client
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        results = await funding_collector.collect_funding_rates(symbols)
        
        assert results['BTCUSDT'] is True
        assert results['ETHUSDT'] is False

    @pytest.mark.asyncio
    async def test_collect_symbol_funding_rate_success(self, funding_collector, mock_binance_client):
        """Test successful collection for a specific symbol."""
        funding_collector.binance_client = mock_binance_client
        
        result = await funding_collector._collect_symbol_funding_rate('BTCUSDT')
        
        assert result is not None
        assert result.symbol == 'BTCUSDT'
        assert result.funding_rate == 0.0001
        mock_binance_client.get_funding_rate.assert_called_once_with('BTCUSDT')

    @pytest.mark.asyncio
    async def test_collect_symbol_funding_rate_no_data(self, funding_collector, mock_binance_client):
        """Test handling when no data is returned."""
        mock_binance_client.get_funding_rate.return_value = None
        funding_collector.binance_client = mock_binance_client
        
        result = await funding_collector._collect_symbol_funding_rate('BTCUSDT')
        
        assert result is None

    @pytest.mark.asyncio
    async def test_collect_symbol_funding_rate_exception(self, funding_collector, mock_binance_client):
        """Test handling when client raises exception."""
        mock_binance_client.get_funding_rate.side_effect = Exception("API Error")
        funding_collector.binance_client = mock_binance_client
        
        result = await funding_collector._collect_symbol_funding_rate('BTCUSDT')
        
        assert result is None


class TestDataProcessing:
    """Test data processing functionality."""

    def test_process_binance_funding_data_success(self, funding_collector):
        """Test successful processing of Binance funding data."""
        raw_data = {
            'symbol': 'BTCUSDT',
            'lastFundingRate': '0.00010000',
            'nextFundingTime': 1640995200000
        }
        
        result = funding_collector._process_binance_funding_data(raw_data, 'BTCUSDT')
        
        assert result is not None
        assert result.exchange == 'binance'
        assert result.symbol == 'BTCUSDT'
        assert result.funding_rate == 0.0001
        assert result.funding_time == 1640995200000

    def test_process_binance_funding_data_missing_fields(self, funding_collector):
        """Test processing with missing required fields."""
        raw_data = {
            'symbol': 'BTCUSDT'
            # Missing lastFundingRate and nextFundingTime
        }
        
        result = funding_collector._process_binance_funding_data(raw_data, 'BTCUSDT')
        
        # Should handle missing fields gracefully
        assert result is not None
        assert result.funding_rate == 0.0  # Default value

    def test_process_binance_funding_data_invalid_data(self, funding_collector):
        """Test processing with invalid data types."""
        raw_data = {
            'symbol': 'BTCUSDT',
            'lastFundingRate': 'invalid_float',
            'nextFundingTime': 'invalid_int'
        }
        
        result = funding_collector._process_binance_funding_data(raw_data, 'BTCUSDT')
        
        assert result is None


class TestCacheManagement:
    """Test rate cache management."""

    def test_update_rate_cache_new_rate(self, funding_collector, sample_funding_rate):
        """Test updating cache with new rate."""
        funding_collector._update_rate_cache('BTCUSDT', sample_funding_rate)
        
        cache_key = f"{sample_funding_rate.exchange}_BTCUSDT"
        assert cache_key in funding_collector.last_rates
        assert funding_collector.last_rates[cache_key] == sample_funding_rate

    def test_update_rate_cache_significant_change(self, funding_collector, sample_funding_rate):
        """Test logging of significant rate changes."""
        # Add initial rate
        funding_collector._update_rate_cache('BTCUSDT', sample_funding_rate)
        
        # Create rate with significant change
        new_rate = FundingRate(
            exchange='binance',
            symbol='BTCUSDT',
            timestamp=sample_funding_rate.timestamp + 1000,
            funding_rate=0.0002,  # 100% increase
            predicted_rate=0.0002,
            funding_time=sample_funding_rate.funding_time
        )
        
        with patch('src.services.funding_collector.logger') as mock_logger:
            funding_collector._update_rate_cache('BTCUSDT', new_rate)
            
            # Should log the significant change
            mock_logger.info.assert_called_once()

    def test_update_rate_cache_small_change(self, funding_collector, sample_funding_rate):
        """Test that small changes don't trigger logging."""
        # Add initial rate
        funding_collector._update_rate_cache('BTCUSDT', sample_funding_rate)
        
        # Create rate with small change
        new_rate = FundingRate(
            exchange='binance',
            symbol='BTCUSDT',
            timestamp=sample_funding_rate.timestamp + 1000,
            funding_rate=0.00011,  # Small increase
            predicted_rate=0.00011,
            funding_time=sample_funding_rate.funding_time
        )
        
        with patch('src.services.funding_collector.logger') as mock_logger:
            funding_collector._update_rate_cache('BTCUSDT', new_rate)
            
            # Should not log small changes
            mock_logger.info.assert_not_called()


class TestStorageOperations:
    """Test storage operations."""

    @pytest.mark.asyncio
    async def test_store_funding_rates_single(self, funding_collector, sample_funding_rate):
        """Test storing a single funding rate."""
        await funding_collector._store_funding_rates([sample_funding_rate])
        
        funding_collector.storage.store_funding_rate.assert_called_once_with(
            sample_funding_rate, csv_backup=True
        )

    @pytest.mark.asyncio
    async def test_store_funding_rates_multiple(self, funding_collector, sample_funding_rate):
        """Test storing multiple funding rates."""
        rates = [sample_funding_rate, sample_funding_rate]
        
        await funding_collector._store_funding_rates(rates)
        
        # Should be called twice (once for each rate)
        assert funding_collector.storage.store_funding_rate.call_count == 2

    @pytest.mark.asyncio
    async def test_store_funding_rates_storage_failure(self, funding_collector, sample_funding_rate):
        """Test handling storage failure."""
        funding_collector.storage.store_funding_rate.side_effect = Exception("Storage error")
        
        with pytest.raises(Exception, match="Storage error"):
            await funding_collector._store_funding_rates([sample_funding_rate])


class TestCollectionControl:
    """Test collection start/stop control."""

    @pytest.mark.asyncio
    async def test_start_collection_already_running(self, funding_collector):
        """Test starting collection when already running."""
        funding_collector.is_running = True
        
        with patch('src.services.funding_collector.logger') as mock_logger:
            await funding_collector.start_collection(['BTCUSDT'])
            
            mock_logger.warning.assert_called_with("Funding collection is already running")

    @pytest.mark.asyncio
    async def test_stop_collection_not_running(self, funding_collector):
        """Test stopping collection when not running."""
        funding_collector.is_running = False
        
        await funding_collector.stop_collection()
        
        # Should handle gracefully
        assert funding_collector.is_running is False

    @pytest.mark.asyncio
    async def test_stop_collection_with_task(self, funding_collector):
        """Test stopping collection with active task."""
        # Create a real asyncio task that we can control
        async def dummy_task():
            try:
                await asyncio.sleep(10)  # Long sleep that will be cancelled
            except asyncio.CancelledError:
                raise
        
        # Create actual task
        task = asyncio.create_task(dummy_task())
        funding_collector.collection_task = task
        funding_collector.is_running = True
        
        await funding_collector.stop_collection()
        
        # Task should be cancelled
        assert task.cancelled() or task.done()
        assert funding_collector.is_running is False

    @pytest.mark.asyncio 
    async def test_collection_loop_error_handling(self, funding_collector):
        """Test error handling in collection loop."""
        symbols = ['BTCUSDT']
        interval = 1
        
        # Mock collect_funding_rates to raise exception first time, then work
        call_count = 0
        async def mock_collect_funding_rates(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Collection error")
            else:
                funding_collector.is_running = False  # Stop after successful call
                return {}
        
        funding_collector.collect_funding_rates = mock_collect_funding_rates
        funding_collector.is_running = True
        
        # Should handle the error and continue
        await funding_collector._collection_loop(symbols, interval)
        
        # Should have been called twice (error + success)
        assert call_count == 2


class TestStatusAndAnalysis:
    """Test status reporting and analysis functions."""

    def test_get_collection_status_empty(self, funding_collector):
        """Test status when no data cached."""
        status = funding_collector.get_collection_status()
        
        assert status['is_running'] is False
        assert status['cached_rates_count'] == 0
        assert status['cached_symbols'] == []
        assert isinstance(status['configured_symbols'], list)
        assert isinstance(status['collection_interval'], int)

    def test_get_collection_status_with_data(self, funding_collector, sample_funding_rate):
        """Test status with cached data."""
        funding_collector._update_rate_cache('BTCUSDT', sample_funding_rate)
        
        status = funding_collector.get_collection_status()
        
        assert status['cached_rates_count'] == 1
        assert 'BTCUSDT' in status['cached_symbols']
        assert 'BTCUSDT' in status['last_collection_times']

    def test_get_latest_funding_rate(self, funding_collector, sample_funding_rate):
        """Test retrieving latest funding rate from cache."""
        funding_collector._update_rate_cache('BTCUSDT', sample_funding_rate)
        
        result = funding_collector.get_latest_funding_rate('binance', 'BTCUSDT')
        
        assert result == sample_funding_rate

    def test_get_latest_funding_rate_not_found(self, funding_collector):
        """Test retrieving non-existent funding rate."""
        result = funding_collector.get_latest_funding_rate('binance', 'NONEXISTENT')
        
        assert result is None

    def test_get_funding_rate_history_placeholder(self, funding_collector):
        """Test funding rate history (placeholder implementation)."""
        result = funding_collector.get_funding_rate_history('binance', 'BTCUSDT')
        
        assert result == []

    def test_detect_arbitrage_opportunities_placeholder(self, funding_collector):
        """Test arbitrage detection (placeholder implementation)."""
        result = funding_collector.detect_arbitrage_opportunities(['BTCUSDT'])
        
        assert result == []

    def test_calculate_funding_cost(self, funding_collector):
        """Test funding cost calculation."""
        funding_rate = 0.0001  # 0.01%
        position_size = 10000  # $10,000
        
        cost = funding_collector.calculate_funding_cost(funding_rate, position_size)
        
        # Cost should be position_size * funding_rate
        assert cost == 1.0  # $1

    def test_calculate_funding_cost_custom_hours(self, funding_collector):
        """Test funding cost calculation with custom funding interval."""
        funding_rate = 0.0001
        position_size = 10000
        hours = 4  # 4-hour funding
        
        cost = funding_collector.calculate_funding_cost(funding_rate, position_size, hours)
        
        assert cost == 1.0  # Same calculation regardless of hours

    def test_calculate_funding_cost_error_handling(self, funding_collector):
        """Test funding cost calculation error handling."""
        with patch('src.services.funding_collector.logger') as mock_logger:
            # Pass invalid data to trigger exception
            cost = funding_collector.calculate_funding_cost(None, 10000)
            
            assert cost == 0.0
            mock_logger.error.assert_called_once()


class TestIntegration:
    """Integration tests with real components."""

    @pytest.mark.asyncio
    async def test_collect_and_store_integration(self):
        """Test integration between collection and storage."""
        # Use temporary storage with fresh database
        with tempfile.TemporaryDirectory() as temp_dir:
            import os
            from src.data.realtime_storage import RealtimeStorage
            
            # Use a unique database file for this test
            db_path = os.path.join(temp_dir, "test_integration.db")
            storage = RealtimeStorage(db_path=db_path, csv_dir=temp_dir)
            collector = FundingCollector(storage=storage)
            
            # Mock the API call
            mock_data = {
                'symbol': 'BTCUSDT',
                'lastFundingRate': '0.00010000',
                'nextFundingTime': int(time.time() * 1000) + 8 * 3600 * 1000
            }
            
            with patch.object(collector.binance_client, 'get_funding_rate', return_value=mock_data):
                result = await collector.collect_single_funding_rate('BTCUSDT')
                
                assert result is not None
                assert result.funding_rate == 0.0001
                
                # Verify data was actually stored
                health_status = storage.get_realtime_health_status()
                assert health_status['record_counts']['funding_records'] == 1 