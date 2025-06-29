import pytest
import os
import tempfile
import shutil
import csv
from datetime import datetime
from src.data.storage import CSVStorage
from src.data.models import OHLCVData


@pytest.fixture
def temp_storage():
    """Create a temporary CSVStorage instance for testing."""
    temp_dir = tempfile.mkdtemp()
    storage = CSVStorage(data_dir=temp_dir)
    yield storage
    # Cleanup
    shutil.rmtree(temp_dir)


def test_csv_storage_creation():
    """Test that CSVStorage can be created."""
    storage = CSVStorage()
    assert storage is not None
    assert storage.data_dir == "data/raw"


def test_csv_storage_directory_creation(temp_storage):
    """Test that data directory is created if it doesn't exist."""
    assert os.path.exists(temp_storage.data_dir)
    assert os.path.isdir(temp_storage.data_dir)


def test_save_ohlcv_data_creates_file(temp_storage):
    """Test that save_ohlcv_data creates a CSV file."""
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    current_year = datetime.now().year
    expected_file = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    assert os.path.exists(expected_file)


def test_save_ohlcv_data_file_content(temp_storage):
    """Test that CSV file contains correct data."""
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check header
    assert "timestamp,open,high,low,close,volume" in content
    # Check data
    assert "1234567890,50000,51000,49000,50500,1000000" in content


def test_save_ohlcv_data_append_mode(temp_storage):
    """Test that subsequent saves append to existing file."""
    # Save first data
    ohlcv_data1 = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data1)
    
    # Save second data
    ohlcv_data2 = [OHLCVData(timestamp=1234567950, open=50500, high=51500, low=50000, close=51000, volume=2000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data2)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Should have header + 2 data lines
    assert len(lines) == 3
    assert "1234567890,50000,51000,49000,50500,1000000" in lines[1]
    assert "1234567950,50500,51500,50000,51000,2000000" in lines[2]


def test_save_ohlcv_data_empty_list(temp_storage):
    """Test that saving empty data doesn't create a file."""
    temp_storage.save_ohlcv_data("bitcoin", [])
    
    current_year = datetime.now().year
    expected_file = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    assert not os.path.exists(expected_file)


def test_save_ohlcv_data_multiple_cryptos(temp_storage):
    """Test that different cryptocurrencies create separate files."""
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    temp_storage.save_ohlcv_data("ethereum", ohlcv_data)
    
    current_year = datetime.now().year
    bitcoin_file = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    ethereum_file = os.path.join(temp_storage.data_dir, f"ethereum_{current_year}.csv")
    
    assert os.path.exists(bitcoin_file)
    assert os.path.exists(ethereum_file)


def test_task_example():
    """Test the specific example from Task 4.1."""
    # Clean up any existing file first
    current_year = datetime.now().year
    test_file = f"data/raw/bitcoin_{current_year}.csv"
    if os.path.exists(test_file):
        os.remove(test_file)
    
    storage = CSVStorage()
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    storage.save_ohlcv_data("bitcoin", ohlcv_data)
    assert os.path.exists(test_file)


# Deduplication Tests (Task 4.2)

def test_duplicate_prevention(temp_storage):
    """Test that duplicate timestamps are not saved."""
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    
    # Save data first time
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    # Save same data again (duplicate)
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Should have header + 1 data line (no duplicate)
    assert len(lines) == 2


def test_row_count_unchanged_with_duplicates(temp_storage):
    """Test the specific example from Task 4.2."""
    ohlcv_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    
    # Save data first time
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    # Count rows before duplicate attempt
    with open(filepath, 'r') as f:
        initial_row_count = len(f.readlines())
    
    # Try to save duplicate data
    duplicate_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", duplicate_data)
    
    # Count rows after duplicate attempt
    with open(filepath, 'r') as f:
        final_row_count = len(f.readlines())
    
    # Row count should be unchanged
    assert initial_row_count == final_row_count


def test_partial_duplicates_same_timestamp_different_data(temp_storage):
    """Test handling of same timestamp with different OHLCV data."""
    # First data entry
    ohlcv_data1 = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data1)
    
    # Second data entry with same timestamp but different prices
    ohlcv_data2 = [OHLCVData(timestamp=1234567890, open=51000, high=52000, low=50000, close=51500, volume=2000000)]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data2)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Should have header + 1 data line (duplicate timestamp rejected)
    assert len(lines) == 2
    # Should contain original data
    assert "50000,51000,49000,50500,1000000" in lines[1]


def test_record_exists_method(temp_storage):
    """Test the _record_exists method."""
    existing_timestamps = {1234567890, 1234567950}
    
    assert temp_storage._record_exists(1234567890, existing_timestamps) == True
    assert temp_storage._record_exists(1234567950, existing_timestamps) == True
    assert temp_storage._record_exists(1234568000, existing_timestamps) == False


def test_get_existing_timestamps_empty_file(temp_storage):
    """Test _get_existing_timestamps with non-existent file."""
    filepath = os.path.join(temp_storage.data_dir, "nonexistent.csv")
    timestamps = temp_storage._get_existing_timestamps(filepath)
    assert timestamps == set()


def test_get_existing_timestamps_with_data(temp_storage):
    """Test _get_existing_timestamps with existing data."""
    ohlcv_data = [
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000),
        OHLCVData(timestamp=1234567950, open=50500, high=51500, low=50000, close=51000, volume=2000000)
    ]
    temp_storage.save_ohlcv_data("bitcoin", ohlcv_data)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    timestamps = temp_storage._get_existing_timestamps(filepath)
    
    assert timestamps == {1234567890, 1234567950}


def test_mixed_new_and_duplicate_data(temp_storage):
    """Test saving a mix of new and duplicate data."""
    # Save initial data
    initial_data = [OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", initial_data)
    
    # Save mix of new and duplicate data
    mixed_data = [
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000),  # Duplicate
        OHLCVData(timestamp=1234567950, open=50500, high=51500, low=50000, close=51000, volume=2000000)   # New
    ]
    temp_storage.save_ohlcv_data("bitcoin", mixed_data)
    
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Should have header + 2 data lines (1 original + 1 new)
    assert len(lines) == 3


# Data Retrieval Tests (Task 4.3)

def test_load_ohlcv_data_basic(temp_storage):
    """Test basic data loading functionality."""
    # Save test data
    test_data = [
        OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000),
        OHLCVData(timestamp=1641081600000, open=50500, high=51500, low=50000, close=51000, volume=2000000)
    ]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load data back
    loaded_data = temp_storage.load_ohlcv_data("bitcoin")
    
    assert len(loaded_data) == 2
    assert loaded_data[0].timestamp == 1640995200000
    assert loaded_data[0].open == 50000
    assert loaded_data[1].timestamp == 1641081600000


def test_load_ohlcv_data_task_example(temp_storage):
    """Test the specific example from Task 4.3."""
    # Save test data
    test_data = [OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000)]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load data with date range
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 12, 31)
    data = temp_storage.load_ohlcv_data("bitcoin", start_date, end_date)
    assert len(data) > 0


def test_load_ohlcv_data_missing_file(temp_storage):
    """Test loading data from non-existent file."""
    # Try to load from non-existent file
    data = temp_storage.load_ohlcv_data("nonexistent")
    assert data == []


def test_load_ohlcv_data_with_date_range(temp_storage):
    """Test loading data with date range filtering."""
    # Save test data with different timestamps
    test_data = [
        OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000),  # 2022-01-01
        OHLCVData(timestamp=1672531200000, open=51000, high=52000, low=50000, close=51500, volume=1500000),  # 2023-01-01
        OHLCVData(timestamp=1704067200000, open=52000, high=53000, low=51000, close=52500, volume=2000000)   # 2024-01-01
    ]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load with date range (2022 only)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 12, 31)
    filtered_data = temp_storage.load_ohlcv_data("bitcoin", start_date, end_date)
    
    assert len(filtered_data) == 1
    assert filtered_data[0].timestamp == 1640995200000


def test_load_ohlcv_data_start_date_only(temp_storage):
    """Test loading data with only start date specified."""
    # Save test data
    test_data = [
        OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000),  # 2022-01-01
        OHLCVData(timestamp=1672531200000, open=51000, high=52000, low=50000, close=51500, volume=1500000)   # 2023-01-01
    ]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load with only start date
    start_date = datetime(2023, 1, 1)
    filtered_data = temp_storage.load_ohlcv_data("bitcoin", start_date=start_date)
    
    assert len(filtered_data) == 1
    assert filtered_data[0].timestamp == 1672531200000


def test_load_ohlcv_data_end_date_only(temp_storage):
    """Test loading data with only end date specified."""
    # Save test data
    test_data = [
        OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000),  # 2022-01-01
        OHLCVData(timestamp=1672531200000, open=51000, high=52000, low=50000, close=51500, volume=1500000)   # 2023-01-01
    ]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load with only end date
    end_date = datetime(2022, 12, 31)
    filtered_data = temp_storage.load_ohlcv_data("bitcoin", end_date=end_date)
    
    assert len(filtered_data) == 1
    assert filtered_data[0].timestamp == 1640995200000


def test_load_ohlcv_data_no_date_filter(temp_storage):
    """Test loading data without date filtering."""
    # Save test data
    test_data = [
        OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000),
        OHLCVData(timestamp=1672531200000, open=51000, high=52000, low=50000, close=51500, volume=1500000)
    ]
    temp_storage.save_ohlcv_data("bitcoin", test_data)
    
    # Load all data
    all_data = temp_storage.load_ohlcv_data("bitcoin")
    
    assert len(all_data) == 2


def test_load_ohlcv_data_malformed_rows(temp_storage):
    """Test loading data with malformed CSV rows."""
    # Manually create a CSV with some malformed rows
    current_year = datetime.now().year
    filepath = os.path.join(temp_storage.data_dir, f"bitcoin_{current_year}.csv")
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        writer.writerow([1640995200000, 50000, 51000, 49000, 50500, 1000000])  # Valid
        writer.writerow(['invalid', 'data', 'row'])  # Malformed
        writer.writerow([1641081600000, 50500, 51500, 50000, 51000, 2000000])  # Valid
        writer.writerow([])  # Empty row
    
    # Load data - should skip malformed rows
    data = temp_storage.load_ohlcv_data("bitcoin")
    
    assert len(data) == 2
    assert data[0].timestamp == 1640995200000
    assert data[1].timestamp == 1641081600000


def test_is_in_date_range_helper(temp_storage):
    """Test the _is_in_date_range helper method."""
    test_data = OHLCVData(timestamp=1640995200000, open=50000, high=51000, low=49000, close=50500, volume=1000000)  # 2022-01-01
    
    # No date range
    assert temp_storage._is_in_date_range(test_data, None, None) == True
    
    # In range
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2023, 1, 1)
    assert temp_storage._is_in_date_range(test_data, start_date, end_date) == True
    
    # Before start date
    start_date = datetime(2023, 1, 1)
    assert temp_storage._is_in_date_range(test_data, start_date, None) == False
    
    # After end date
    end_date = datetime(2021, 1, 1)
    assert temp_storage._is_in_date_range(test_data, None, end_date) == False 