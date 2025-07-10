import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from src.data.realtime_storage import RealtimeStorage
from src.data.realtime_models import OrderBookSnapshot, OrderBookLevel, BidAskSpread, FundingRate
import sqlite3
import csv
from datetime import datetime
import time


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_db_dir = tempfile.mkdtemp()
    temp_csv_dir = tempfile.mkdtemp()
    
    yield temp_db_dir, temp_csv_dir
    
    # Cleanup
    shutil.rmtree(temp_db_dir, ignore_errors=True)
    shutil.rmtree(temp_csv_dir, ignore_errors=True)


@pytest.fixture
def realtime_storage(temp_dirs):
    """RealtimeStorage instance with temporary directories."""
    temp_db_dir, temp_csv_dir = temp_dirs
    db_path = os.path.join(temp_db_dir, "test_realtime.db")
    return RealtimeStorage(db_path=db_path, csv_dir=temp_csv_dir)


@pytest.fixture
def sample_orderbook():
    """Create a sample order book for testing."""
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
        symbol='BTCUSDT',
        timestamp=int(time.time() * 1000),
        bids=bids,
        asks=asks
    )


@pytest.fixture
def sample_spread():
    """Create a sample spread for testing."""
    return BidAskSpread(
        exchange='binance',
        symbol='BTCUSDT',
        timestamp=int(time.time() * 1000),
        bid_price=50000.0,
        ask_price=50001.0,
        spread_absolute=1.0,
        spread_percentage=0.002,
        mid_price=50000.5
    )


@pytest.fixture
def sample_funding_rate():
    """Create a sample funding rate for testing."""
    return FundingRate(
        exchange='binance',
        symbol='BTCUSDT',
        timestamp=int(time.time() * 1000),
        funding_rate=0.0001,
        predicted_rate=0.00012,
        funding_time=int(time.time() * 1000) + 8 * 3600 * 1000  # 8 hours later
    )


class TestRealtimeStorageInitialization:
    """Test RealtimeStorage initialization."""

    def test_initialization_default_paths(self):
        """Test initialization with default paths."""
        # Test with temporary directory to avoid affecting real database
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_dir = os.path.join(temp_dir, "realtime")
            storage = RealtimeStorage(csv_dir=csv_dir)
            
            assert storage.csv_dir == csv_dir
            assert storage.db_connection is not None
            assert os.path.exists(csv_dir)
            assert os.path.exists(os.path.join(csv_dir, "orderbooks"))
            assert os.path.exists(os.path.join(csv_dir, "spreads"))
            assert os.path.exists(os.path.join(csv_dir, "funding"))

    def test_initialization_custom_paths(self, temp_dirs):
        """Test initialization with custom paths."""
        temp_db_dir, temp_csv_dir = temp_dirs
        db_path = os.path.join(temp_db_dir, "custom.db")
        
        storage = RealtimeStorage(db_path=db_path, csv_dir=temp_csv_dir)
        
        assert storage.db_path == db_path
        assert storage.csv_dir == temp_csv_dir
        assert os.path.exists(temp_csv_dir)

    def test_database_tables_creation(self, realtime_storage):
        """Test that database tables are created properly."""
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check that all tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('order_book', 'bid_ask_spreads', 'funding_rates')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'order_book' in tables
            assert 'bid_ask_spreads' in tables
            assert 'funding_rates' in tables


class TestOrderBookStorage:
    """Test order book storage functionality."""

    def test_store_orderbook_snapshot_success(self, realtime_storage, sample_orderbook):
        """Test successful order book snapshot storage."""
        result = realtime_storage.store_orderbook_snapshot(sample_orderbook)
        
        # Should store 6 levels (3 bids + 3 asks)
        assert result == 6
        
        # Verify data in database
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM order_book")
            count = cursor.fetchone()[0]
            assert count == 6

    def test_store_orderbook_snapshot_empty(self, realtime_storage):
        """Test storing empty order book snapshot."""
        empty_orderbook = OrderBookSnapshot(
            exchange='binance',
            symbol='BTCUSDT',
            timestamp=int(time.time() * 1000),
            bids=[],
            asks=[]
        )
        
        result = realtime_storage.store_orderbook_snapshot(empty_orderbook)
        assert result == 0

    def test_store_orderbook_snapshot_with_csv_backup(self, realtime_storage, sample_orderbook):
        """Test order book storage with CSV backup."""
        realtime_storage.store_orderbook_snapshot(sample_orderbook, csv_backup=True)
        
        # Check CSV file was created
        date_str = datetime.fromtimestamp(sample_orderbook.timestamp / 1000).strftime('%Y%m%d')
        expected_filename = f"binance_BTCUSDT_orderbook_{date_str}.csv"
        csv_path = os.path.join(realtime_storage.csv_dir, "orderbooks", expected_filename)
        
        assert os.path.exists(csv_path)
        
        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should have header + 6 data rows
            assert len(rows) == 7
            assert rows[0] == ['timestamp', 'side', 'level', 'price', 'quantity']

    def test_store_orderbook_snapshot_without_csv_backup(self, realtime_storage, sample_orderbook):
        """Test order book storage without CSV backup."""
        realtime_storage.store_orderbook_snapshot(sample_orderbook, csv_backup=False)
        
        # Check CSV file was not created
        orderbooks_dir = os.path.join(realtime_storage.csv_dir, "orderbooks")
        csv_files = os.listdir(orderbooks_dir)
        assert len(csv_files) == 0

    def test_batch_store_orderbooks(self, realtime_storage, sample_orderbook):
        """Test batch order book storage."""
        # Create multiple orderbooks with different timestamps
        orderbooks = []
        for i in range(3):
            orderbook = OrderBookSnapshot(
                exchange=sample_orderbook.exchange,
                symbol=sample_orderbook.symbol,
                timestamp=sample_orderbook.timestamp + i * 1000,
                bids=sample_orderbook.bids,
                asks=sample_orderbook.asks
            )
            orderbooks.append(orderbook)
        
        result = realtime_storage.batch_store_orderbooks(orderbooks)
        
        # Should store 18 levels (3 orderbooks * 6 levels each)
        assert result == 18
        
        # Verify data in database
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM order_book")
            count = cursor.fetchone()[0]
            assert count == 18

    def test_get_latest_orderbook(self, realtime_storage, sample_orderbook):
        """Test retrieving latest order book."""
        # Store an order book
        realtime_storage.store_orderbook_snapshot(sample_orderbook)
        
        # Retrieve it
        retrieved = realtime_storage.get_latest_orderbook('binance', 'BTCUSDT')
        
        assert retrieved is not None
        assert retrieved.exchange == sample_orderbook.exchange
        assert retrieved.symbol == sample_orderbook.symbol
        assert retrieved.timestamp == sample_orderbook.timestamp
        assert len(retrieved.bids) == len(sample_orderbook.bids)
        assert len(retrieved.asks) == len(sample_orderbook.asks)

    def test_get_latest_orderbook_not_found(self, realtime_storage):
        """Test retrieving order book when none exists."""
        retrieved = realtime_storage.get_latest_orderbook('binance', 'NONEXISTENT')
        assert retrieved is None


class TestSpreadStorage:
    """Test spread storage functionality."""

    def test_store_bid_ask_spread_success(self, realtime_storage, sample_spread):
        """Test successful spread storage."""
        result = realtime_storage.store_bid_ask_spread(sample_spread)
        
        assert result is True
        
        # Verify data in database
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bid_ask_spreads")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_store_bid_ask_spread_with_csv_backup(self, realtime_storage, sample_spread):
        """Test spread storage with CSV backup."""
        realtime_storage.store_bid_ask_spread(sample_spread, csv_backup=True)
        
        # Check CSV file was created
        date_str = datetime.fromtimestamp(sample_spread.timestamp / 1000).strftime('%Y%m%d')
        expected_filename = f"binance_BTCUSDT_spreads_{date_str}.csv"
        csv_path = os.path.join(realtime_storage.csv_dir, "spreads", expected_filename)
        
        assert os.path.exists(csv_path)

    def test_batch_store_spreads(self, realtime_storage, sample_spread):
        """Test batch spread storage."""
        # Create multiple spreads with different timestamps
        spreads = []
        for i in range(3):
            spread = BidAskSpread(
                exchange=sample_spread.exchange,
                symbol=sample_spread.symbol,
                timestamp=sample_spread.timestamp + i * 1000,
                bid_price=sample_spread.bid_price,
                ask_price=sample_spread.ask_price,
                spread_absolute=sample_spread.spread_absolute,
                spread_percentage=sample_spread.spread_percentage,
                mid_price=sample_spread.mid_price
            )
            spreads.append(spread)
        
        result = realtime_storage.batch_store_spreads(spreads)
        
        assert result == 3
        
        # Verify data in database
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bid_ask_spreads")
            count = cursor.fetchone()[0]
            assert count == 3

    def test_get_latest_spread(self, realtime_storage, sample_spread):
        """Test retrieving latest spread."""
        # Store a spread
        realtime_storage.store_bid_ask_spread(sample_spread)
        
        # Retrieve it
        retrieved = realtime_storage.get_latest_spread('binance', 'BTCUSDT')
        
        assert retrieved is not None
        assert retrieved.exchange == sample_spread.exchange
        assert retrieved.symbol == sample_spread.symbol
        assert retrieved.timestamp == sample_spread.timestamp
        assert retrieved.spread_percentage == sample_spread.spread_percentage

    def test_get_latest_spread_not_found(self, realtime_storage):
        """Test retrieving spread when none exists."""
        retrieved = realtime_storage.get_latest_spread('binance', 'NONEXISTENT')
        assert retrieved is None


class TestFundingRateStorage:
    """Test funding rate storage functionality."""

    def test_store_funding_rate_success(self, realtime_storage, sample_funding_rate):
        """Test successful funding rate storage."""
        result = realtime_storage.store_funding_rate(sample_funding_rate)
        
        assert result is True
        
        # Verify data in database
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM funding_rates")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_store_funding_rate_with_csv_backup(self, realtime_storage, sample_funding_rate):
        """Test funding rate storage with CSV backup."""
        realtime_storage.store_funding_rate(sample_funding_rate, csv_backup=True)
        
        # Check CSV file was created
        date_str = datetime.fromtimestamp(sample_funding_rate.timestamp / 1000).strftime('%Y%m%d')
        expected_filename = f"binance_BTCUSDT_funding_{date_str}.csv"
        csv_path = os.path.join(realtime_storage.csv_dir, "funding", expected_filename)
        
        assert os.path.exists(csv_path)


class TestHealthStatus:
    """Test health status functionality."""

    def test_get_realtime_health_status_empty(self, realtime_storage):
        """Test health status with empty database."""
        status = realtime_storage.get_realtime_health_status()
        
        assert status['status'] == 'healthy'
        assert status['record_counts']['order_book_levels'] == 0
        assert status['record_counts']['spread_records'] == 0
        assert status['record_counts']['funding_records'] == 0

    def test_get_realtime_health_status_with_data(self, realtime_storage, sample_orderbook, sample_spread, sample_funding_rate):
        """Test health status with data."""
        # Store some data
        realtime_storage.store_orderbook_snapshot(sample_orderbook)
        realtime_storage.store_bid_ask_spread(sample_spread)
        realtime_storage.store_funding_rate(sample_funding_rate)
        
        status = realtime_storage.get_realtime_health_status()
        
        assert status['status'] == 'healthy'
        assert status['record_counts']['order_book_levels'] == 6
        assert status['record_counts']['spread_records'] == 1
        assert status['record_counts']['funding_records'] == 1
        assert status['latest_timestamps']['order_book'] == sample_orderbook.timestamp
        assert status['latest_timestamps']['spreads'] == sample_spread.timestamp
        assert status['latest_timestamps']['funding'] == sample_funding_rate.timestamp


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_database_connection_failure(self, temp_dirs):
        """Test handling of database connection failure."""
        temp_db_dir, temp_csv_dir = temp_dirs
        
        # Try to create storage with invalid database path
        invalid_db_path = "/invalid/path/that/does/not/exist/db.sqlite"
        
        with pytest.raises(Exception):
            RealtimeStorage(db_path=invalid_db_path, csv_dir=temp_csv_dir)

    def test_csv_directory_creation_failure(self, temp_dirs):
        """Test handling of CSV directory creation failure."""
        temp_db_dir, _ = temp_dirs
        db_path = os.path.join(temp_db_dir, "test.db")
        
        # Try to create CSV directory in read-only location
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                RealtimeStorage(db_path=db_path, csv_dir="/read/only/path")

    def test_storage_with_malformed_data(self, realtime_storage):
        """Test storage with malformed data."""
        # Create order book with invalid data (negative prices)
        malformed_orderbook = OrderBookSnapshot(
            exchange='binance',
            symbol='BTCUSDT',
            timestamp=int(time.time() * 1000),
            bids=[OrderBookLevel(price=-100.0, quantity=1.0, level=0)],
            asks=[OrderBookLevel(price=-99.0, quantity=1.0, level=0)]
        )
        
        # Should still store the data (validation is done elsewhere)
        result = realtime_storage.store_orderbook_snapshot(malformed_orderbook)
        assert result == 2


class TestDataIntegrity:
    """Test data integrity and consistency."""

    def test_orderbook_replace_functionality(self, realtime_storage, sample_orderbook):
        """Test that storing the same timestamp and level replaces existing data."""
        # Store initial order book
        realtime_storage.store_orderbook_snapshot(sample_orderbook)
        
        # Create modified order book with same timestamp but different prices for same levels
        modified_orderbook = OrderBookSnapshot(
            exchange=sample_orderbook.exchange,
            symbol=sample_orderbook.symbol,
            timestamp=sample_orderbook.timestamp,  # Same timestamp
            bids=[
                OrderBookLevel(price=60000.0, quantity=10.0, level=0),  # Same level 0, different price
                OrderBookLevel(price=59999.0, quantity=20.0, level=1),  # Same level 1, different price
                OrderBookLevel(price=59998.0, quantity=30.0, level=2)   # Same level 2, different price
            ],
            asks=[
                OrderBookLevel(price=60001.0, quantity=10.0, level=0),  # Same level 0, different price
                OrderBookLevel(price=60002.0, quantity=20.0, level=1),  # Same level 1, different price
                OrderBookLevel(price=60003.0, quantity=30.0, level=2)   # Same level 2, different price
            ]
        )
        
        # Store modified order book
        realtime_storage.store_orderbook_snapshot(modified_orderbook)
        
        # Should still have 6 levels (same number, but replaced data)
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM order_book WHERE timestamp = ?", (sample_orderbook.timestamp,))
            count = cursor.fetchone()[0]
            assert count == 6
            
            # Verify the data was actually replaced by checking a specific level
            cursor.execute("""
                SELECT price FROM order_book 
                WHERE timestamp = ? AND side = 'bid' AND level = 0
            """, (sample_orderbook.timestamp,))
            bid_price = cursor.fetchone()[0]
            assert bid_price == 60000.0  # Should be the new price, not the original 50000.0

    def test_spread_replace_functionality(self, realtime_storage, sample_spread):
        """Test that storing the same spread timestamp replaces existing data."""
        # Store initial spread
        realtime_storage.store_bid_ask_spread(sample_spread)
        
        # Create modified spread with same timestamp
        modified_spread = BidAskSpread(
            exchange=sample_spread.exchange,
            symbol=sample_spread.symbol,
            timestamp=sample_spread.timestamp,  # Same timestamp
            bid_price=60000.0,  # Different data
            ask_price=60001.0,
            spread_absolute=1.0,
            spread_percentage=0.0016,
            mid_price=60000.5
        )
        
        # Store modified spread
        realtime_storage.store_bid_ask_spread(modified_spread)
        
        # Should still have only 1 record
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bid_ask_spreads WHERE timestamp = ?", (sample_spread.timestamp,))
            count = cursor.fetchone()[0]
            assert count == 1


class TestPerformance:
    """Test performance-related functionality."""

    def test_large_batch_storage(self, realtime_storage):
        """Test storage of large batches."""
        # Create 100 order book snapshots
        orderbooks = []
        base_timestamp = int(time.time() * 1000)
        
        for i in range(100):
            orderbook = OrderBookSnapshot(
                exchange='binance',
                symbol='BTCUSDT',
                timestamp=base_timestamp + i * 1000,
                bids=[OrderBookLevel(price=50000.0 + i, quantity=1.0, level=0)],
                asks=[OrderBookLevel(price=50001.0 + i, quantity=1.0, level=0)]
            )
            orderbooks.append(orderbook)
        
        # Store batch
        result = realtime_storage.batch_store_orderbooks(orderbooks, csv_backup=False)
        
        assert result == 200  # 100 orderbooks * 2 levels each
        
        # Verify all data was stored
        with realtime_storage.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM order_book")
            count = cursor.fetchone()[0]
            assert count == 200 