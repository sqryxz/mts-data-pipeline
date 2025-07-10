"""
Integration tests for real-time data collection pipeline.
Tests the complete flow from data collection to storage across multiple components.
"""

import pytest
import asyncio
import tempfile
import time
import os
from unittest.mock import Mock, patch, AsyncMock
from src.services.orderbook_collector import OrderBookCollector
from src.services.funding_collector import FundingCollector
from src.data.realtime_storage import RealtimeStorage
from src.data.realtime_models import OrderBookSnapshot, OrderBookLevel, BidAskSpread, FundingRate
from src.api.binance_client import BinanceClient
from src.realtime.orderbook_processor import OrderBookProcessor
from src.services.spread_calculator import SpreadCalculator
from src.data.redis_helper import RedisHelper


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def realtime_storage(temp_storage_dir):
    """RealtimeStorage instance with temporary database."""
    db_path = os.path.join(temp_storage_dir, "integration_test.db")
    return RealtimeStorage(db_path=db_path, csv_dir=temp_storage_dir)


@pytest.fixture
def mock_binance_client():
    """Mock Binance client with realistic responses."""
    client = Mock(spec=BinanceClient)
    
    # Mock order book response
    client.get_order_book.return_value = {
        'lastUpdateId': 12345,
        'bids': [
            ['50000.00', '1.50'],
            ['49999.00', '2.00'],
            ['49998.00', '1.00']
        ],
        'asks': [
            ['50001.00', '1.20'],
            ['50002.00', '1.80'],
            ['50003.00', '0.80']
        ]
    }
    
    # Mock funding rate response
    client.get_funding_rate.return_value = {
        'symbol': 'BTCUSDT',
        'lastFundingRate': '0.00010000',
        'nextFundingTime': int(time.time() * 1000) + 8 * 3600 * 1000
    }
    
    return client


@pytest.fixture
def mock_redis_helper():
    """Mock Redis helper."""
    redis_helper = Mock(spec=RedisHelper)
    redis_helper.connect.return_value = True
    redis_helper.set_json.return_value = True
    redis_helper.get_json.return_value = None
    return redis_helper


@pytest.fixture
def mock_orderbook_processor():
    """Mock OrderBook processor."""
    processor = Mock(spec=OrderBookProcessor)
    
    def process_side_effect(raw_data, symbol):
        # Create realistic OrderBookSnapshot
        bids = [
            OrderBookLevel(price=50000.0, quantity=1.5, level=0),
            OrderBookLevel(price=49999.0, quantity=2.0, level=1),
            OrderBookLevel(price=49998.0, quantity=1.0, level=2)
        ]
        asks = [
            OrderBookLevel(price=50001.0, quantity=1.2, level=0),
            OrderBookLevel(price=50002.0, quantity=1.8, level=1),
            OrderBookLevel(price=50003.0, quantity=0.8, level=2)
        ]
        return OrderBookSnapshot(
            exchange='binance',
            symbol=symbol,
            timestamp=int(time.time() * 1000),
            bids=bids,
            asks=asks
        )
    
    processor.process_orderbook.side_effect = process_side_effect
    return processor


@pytest.fixture
def mock_spread_calculator():
    """Mock Spread calculator."""
    calculator = Mock(spec=SpreadCalculator)
    
    def calculate_side_effect(orderbook):
        return BidAskSpread(
            exchange=orderbook.exchange,
            symbol=orderbook.symbol,
            timestamp=orderbook.timestamp,
            bid_price=50000.0,
            ask_price=50001.0,
            spread_absolute=1.0,
            spread_percentage=0.002,
            mid_price=50000.5
        )
    
    calculator.calculate_spread.side_effect = calculate_side_effect
    return calculator


class TestRealtimeIntegrationBasics:
    """Test basic integration between components."""
    
    def test_components_initialization(self, realtime_storage):
        """Test that all components can be initialized together."""
        # Initialize all components
        orderbook_collector = OrderBookCollector()
        funding_collector = FundingCollector(storage=realtime_storage)
        
        # Verify initialization
        assert orderbook_collector.binance_client is not None
        assert orderbook_collector.processor is not None
        assert orderbook_collector.spread_calculator is not None
        assert orderbook_collector.redis_helper is not None
        assert funding_collector.storage is realtime_storage
        assert orderbook_collector.is_running is False
        assert funding_collector.is_running is False
    
    def test_shared_storage_health(self, realtime_storage):
        """Test health status with shared storage."""
        health_status = realtime_storage.get_realtime_health_status()
        
        assert health_status['status'] == 'healthy'
        assert 'record_counts' in health_status
        assert 'latest_timestamps' in health_status


class TestOrderBookToStorageIntegration:
    """Test integration between order book collection and storage."""
    
    @pytest.mark.asyncio
    async def test_orderbook_collection_to_redis_flow(self, mock_redis_helper):
        """Test complete flow from order book collection to Redis storage."""
        # Create collector and replace Redis helper
        collector = OrderBookCollector()
        collector.redis_helper = mock_redis_helper
        
        # Test that we can call get_latest_orderbook method
        result = collector.get_latest_orderbook('binance', 'BTCUSDT')
        
        # Since Redis helper is mocked to return None, result should be None
        assert result is None
        
        # Verify Redis helper was called correctly
        mock_redis_helper.get_json.assert_called_once_with('orderbook:binance:BTCUSDT')


class TestFundingToStorageIntegration:
    """Test integration between funding rate collection and storage."""
    
    @pytest.mark.asyncio
    async def test_funding_collection_to_storage_flow(self, realtime_storage, mock_binance_client):
        """Test complete flow from funding rate collection to storage."""
        # Create collector with shared storage
        collector = FundingCollector(storage=realtime_storage)
        collector.binance_client = mock_binance_client
        
        # Collect funding rate data
        result = await collector.collect_single_funding_rate('BTCUSDT')
        
        # Verify collection succeeded
        assert result is not None
        assert result.symbol == 'BTCUSDT'
        assert result.funding_rate == 0.0001
        
        # Verify data was stored
        health_status = realtime_storage.get_realtime_health_status()
        assert health_status['record_counts']['funding_records'] > 0
        
        # Verify we can retrieve the data from cache
        latest_rate = collector.get_latest_funding_rate('binance', 'BTCUSDT')
        assert latest_rate is not None
        assert latest_rate.symbol == 'BTCUSDT'


class TestMultiComponentIntegration:
    """Test integration across multiple components working together."""
    
    @pytest.mark.asyncio
    async def test_funding_collection_integration(self, realtime_storage, mock_binance_client):
        """Test funding rate collection with real storage."""
        # Create funding collector with real storage
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Collect funding rate data
        funding_result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        # Verify collection succeeded
        assert funding_result is not None
        assert funding_result.symbol == 'BTCUSDT'
        assert funding_result.exchange == 'binance'
        
        # Verify data was stored
        health_status = realtime_storage.get_realtime_health_status()
        assert health_status['record_counts']['funding_records'] > 0
    
    @pytest.mark.asyncio
    async def test_multiple_funding_symbols_integration(self, realtime_storage, mock_binance_client):
        """Test funding collection across multiple symbols."""
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        # Create funding collector
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Collect data for multiple symbols
        funding_results = await funding_collector.collect_funding_rates(symbols)
        
        # Verify all collections succeeded
        assert all(funding_results.values())
        
        # Verify data for all symbols was stored
        health_status = realtime_storage.get_realtime_health_status()
        assert health_status['record_counts']['funding_records'] >= 2  # 2 symbols


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    @pytest.mark.asyncio
    async def test_funding_api_failure_handling(self, realtime_storage):
        """Test handling when funding API fails."""
        # Create client that fails for funding
        failing_client = Mock(spec=BinanceClient)
        failing_client.get_funding_rate.return_value = None  # Simulate failure
        
        # Create funding collector
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = failing_client
        
        # Attempt collection
        funding_result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        # Funding should fail gracefully
        assert funding_result is None
        
        # No data should be stored
        health_status = realtime_storage.get_realtime_health_status()
        assert health_status['record_counts']['funding_records'] == 0
    
    @pytest.mark.asyncio
    async def test_storage_failure_handling(self, temp_storage_dir, mock_binance_client):
        """Test handling of storage failures."""
        # Create storage that will fail
        failing_storage = Mock(spec=RealtimeStorage)
        failing_storage.store_funding_rate.side_effect = Exception("Storage failed")
        
        # Create funding collector with failing storage
        funding_collector = FundingCollector(storage=failing_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Attempt collection - should handle storage failures gracefully and return None
        result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        # Should fail gracefully and return None
        assert result is None


class TestDataConsistencyIntegration:
    """Test data consistency across integrated components."""
    
    @pytest.mark.asyncio
    async def test_funding_timestamp_consistency(self, realtime_storage, mock_binance_client):
        """Test that funding rate timestamps are reasonable."""
        # Capture start time
        start_time = int(time.time() * 1000)
        
        # Create funding collector
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Collect funding rate data
        funding_result = await funding_collector.collect_single_funding_rate('BTCUSDT')
        
        end_time = int(time.time() * 1000)
        
        # Verify timestamp is reasonable
        assert start_time <= funding_result.timestamp <= end_time
    
    @pytest.mark.asyncio
    async def test_funding_symbol_consistency(self, realtime_storage, mock_binance_client):
        """Test that symbol handling is consistent in funding collection."""
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        # Create funding collector
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Collect data for all symbols
        for symbol in symbols:
            funding_result = await funding_collector.collect_single_funding_rate(symbol)
            
            # Verify symbol consistency
            assert funding_result.symbol == symbol
            
            # Verify exchange consistency
            assert funding_result.exchange == 'binance'


class TestPerformanceIntegration:
    """Test performance characteristics of integrated system."""
    
    @pytest.mark.asyncio
    async def test_concurrent_funding_collection_performance(self, realtime_storage, mock_binance_client):
        """Test performance of concurrent funding collection operations."""
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        
        # Create funding collector
        funding_collector = FundingCollector(storage=realtime_storage)
        funding_collector.binance_client = mock_binance_client
        
        # Measure collection time
        start_time = time.time()
        
        # Collect all funding data concurrently
        funding_tasks = [funding_collector.collect_single_funding_rate(symbol) for symbol in symbols]
        results = await asyncio.gather(*funding_tasks, return_exceptions=True)
        
        end_time = time.time()
        collection_time = end_time - start_time
        
        # Verify all collections succeeded
        assert all(result is not None and not isinstance(result, Exception) for result in results)
        
        # Performance should be reasonable (less than 5 seconds for all operations)
        assert collection_time < 5.0
        
        # Verify all data was stored
        health_status = realtime_storage.get_realtime_health_status()
        assert health_status['record_counts']['funding_records'] == len(symbols)
    
    @pytest.mark.asyncio
    async def test_storage_batch_performance(self, realtime_storage):
        """Test batch storage performance."""
        # Create large dataset
        orderbooks = []
        spreads = []
        
        for i in range(100):
            # Create order book
            bids = [OrderBookLevel(price=50000.0 - i, quantity=1.0, level=j) for j in range(3)]
            asks = [OrderBookLevel(price=50001.0 + i, quantity=1.0, level=j) for j in range(3)]
            
            orderbook = OrderBookSnapshot(
                exchange='binance',
                symbol='BTCUSDT',
                timestamp=int(time.time() * 1000) + i * 1000,
                bids=bids,
                asks=asks
            )
            orderbooks.append(orderbook)
            
            # Create spread
            spread = BidAskSpread(
                exchange='binance',
                symbol='BTCUSDT',
                timestamp=int(time.time() * 1000) + i * 1000,
                bid_price=50000.0 - i,
                ask_price=50001.0 + i,
                spread_absolute=1.0 + i,
                spread_percentage=0.002,
                mid_price=50000.5
            )
            spreads.append(spread)
        
        # Measure batch storage time
        start_time = time.time()
        
        orderbook_count = realtime_storage.batch_store_orderbooks(orderbooks)
        spread_count = realtime_storage.batch_store_spreads(spreads)
        
        end_time = time.time()
        storage_time = end_time - start_time
        
        # Verify all data was stored
        assert orderbook_count == 600  # 100 orderbooks * 6 levels
        assert spread_count == 100
        
        # Performance should be reasonable (less than 2 seconds for batch operations)
        assert storage_time < 2.0


class TestIntegrationCleanup:
    """Test cleanup and resource management in integrated system."""
    
    @pytest.mark.asyncio
    async def test_component_cleanup(self, realtime_storage):
        """Test that components clean up properly."""
        # Create collectors
        orderbook_collector = OrderBookCollector()
        funding_collector = FundingCollector(storage=realtime_storage)
        
        # Start and stop collection
        orderbook_collector.is_running = True
        funding_collector.is_running = True
        
        await orderbook_collector.stop_collection()
        await funding_collector.stop_collection()
        
        # Verify cleanup
        assert orderbook_collector.is_running is False
        assert funding_collector.is_running is False
        assert orderbook_collector.websocket_clients == {}
        assert funding_collector.collection_task is None 