import pytest
from src.data.validator import DataValidator


def test_data_validator_creation():
    """Test that DataValidator can be created."""
    validator = DataValidator()
    assert validator is not None


def test_validate_ohlcv_data_valid():
    """Test validation with valid OHLCV data."""
    validator = DataValidator()
    valid_data = [
        [1234567890, 50000, 51000, 49000, 50500],
        [1234567950, 50500, 51500, 50000, 51000]
    ]
    assert validator.validate_ohlcv_data(valid_data) == True


def test_validate_ohlcv_data_task_example():
    """Test the specific example from Task 3.3."""
    validator = DataValidator()
    valid_data = [[1234567890, 50000, 51000, 49000, 50500]]
    assert validator.validate_ohlcv_data(valid_data) == True


def test_validate_ohlcv_data_empty():
    """Test validation with empty data."""
    validator = DataValidator()
    assert validator.validate_ohlcv_data([]) == False


def test_validate_ohlcv_data_wrong_length():
    """Test validation with wrong array length."""
    validator = DataValidator()
    invalid_data = [[1234567890, 50000, 51000, 49000]]  # Missing close price
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_null_values():
    """Test validation with null values."""
    validator = DataValidator()
    invalid_data = [[1234567890, None, 51000, 49000, 50500]]
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_negative_prices():
    """Test validation with negative prices."""
    validator = DataValidator()
    invalid_data = [[1234567890, -50000, 51000, 49000, 50500]]
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_high_lower_than_low():
    """Test validation with high < low."""
    validator = DataValidator()
    invalid_data = [[1234567890, 50000, 48000, 49000, 50500]]  # high < low
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_open_above_high():
    """Test validation with open > high."""
    validator = DataValidator()
    invalid_data = [[1234567890, 52000, 51000, 49000, 50500]]  # open > high
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_close_below_low():
    """Test validation with close < low."""
    validator = DataValidator()
    invalid_data = [[1234567890, 50000, 51000, 49000, 48000]]  # close < low
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_non_numeric():
    """Test validation with non-numeric values."""
    validator = DataValidator()
    invalid_data = [[1234567890, "50000", 51000, 49000, 50500]]
    assert validator.validate_ohlcv_data(invalid_data) == False


def test_validate_ohlcv_data_equal_prices():
    """Test validation with equal OHLC prices (edge case)."""
    validator = DataValidator()
    valid_data = [[1234567890, 50000, 50000, 50000, 50000]]
    assert validator.validate_ohlcv_data(valid_data) == True


def test_validate_ohlcv_data_mixed_valid_invalid():
    """Test validation with mix of valid and invalid entries."""
    validator = DataValidator()
    mixed_data = [
        [1234567890, 50000, 51000, 49000, 50500],  # Valid
        [1234567950, 50000, 48000, 49000, 50500]   # Invalid: high < low
    ]
    assert validator.validate_ohlcv_data(mixed_data) == False


def test_validate_cryptocurrency_data_valid():
    """Test validation with valid cryptocurrency data."""
    validator = DataValidator()
    valid_data = {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "Bitcoin",
        "market_cap_rank": 1
    }
    assert validator.validate_cryptocurrency_data(valid_data) == True


def test_validate_cryptocurrency_data_missing_id():
    """Test validation with missing id field."""
    validator = DataValidator()
    invalid_data = {
        "symbol": "btc",
        "name": "Bitcoin"
    }
    assert validator.validate_cryptocurrency_data(invalid_data) == False


def test_validate_cryptocurrency_data_empty_symbol():
    """Test validation with empty symbol."""
    validator = DataValidator()
    invalid_data = {
        "id": "bitcoin",
        "symbol": "",
        "name": "Bitcoin"
    }
    assert validator.validate_cryptocurrency_data(invalid_data) == False


def test_validate_cryptocurrency_data_whitespace_name():
    """Test validation with whitespace-only name."""
    validator = DataValidator()
    invalid_data = {
        "id": "bitcoin",
        "symbol": "btc",
        "name": "   "
    }
    assert validator.validate_cryptocurrency_data(invalid_data) == False 