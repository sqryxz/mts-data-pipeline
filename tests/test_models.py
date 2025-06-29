import pytest
import datetime
from src.data.models import Cryptocurrency, OHLCVData


def test_cryptocurrency_creation():
    """Test that Cryptocurrency can be created with valid data."""
    crypto = Cryptocurrency(id="bitcoin", symbol="btc", name="Bitcoin")
    assert crypto.id == "bitcoin"
    assert crypto.symbol == "btc"
    assert crypto.name == "Bitcoin"
    assert crypto.market_cap_rank is None


def test_cryptocurrency_with_market_cap_rank():
    """Test that Cryptocurrency can be created with market cap rank."""
    crypto = Cryptocurrency(
        id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        market_cap_rank=1
    )
    assert crypto.market_cap_rank == 1


def test_cryptocurrency_empty_id():
    """Test that empty id raises ValueError."""
    with pytest.raises(ValueError, match="Cryptocurrency id cannot be empty"):
        Cryptocurrency(id="", symbol="btc", name="Bitcoin")


def test_cryptocurrency_whitespace_id():
    """Test that whitespace-only id raises ValueError."""
    with pytest.raises(ValueError, match="Cryptocurrency id cannot be empty"):
        Cryptocurrency(id="   ", symbol="btc", name="Bitcoin")


def test_cryptocurrency_empty_symbol():
    """Test that empty symbol raises ValueError."""
    with pytest.raises(ValueError, match="Cryptocurrency symbol cannot be empty"):
        Cryptocurrency(id="bitcoin", symbol="", name="Bitcoin")


def test_cryptocurrency_empty_name():
    """Test that empty name raises ValueError."""
    with pytest.raises(ValueError, match="Cryptocurrency name cannot be empty"):
        Cryptocurrency(id="bitcoin", symbol="btc", name="")


def test_cryptocurrency_validation_basics():
    """Test the specific validation example from the task."""
    crypto = Cryptocurrency(id="bitcoin", symbol="btc", name="Bitcoin")
    assert crypto.symbol == "btc"


# OHLCV Data Tests

def test_ohlcv_creation():
    """Test that OHLCVData can be created with valid data."""
    ohlcv = OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)
    assert ohlcv.timestamp == 1234567890
    assert ohlcv.open == 50000
    assert ohlcv.high == 51000
    assert ohlcv.low == 49000
    assert ohlcv.close == 50500
    assert ohlcv.volume == 1000000


def test_ohlcv_task_example():
    """Test the specific example from Task 3.2."""
    ohlcv = OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)
    assert ohlcv is not None


def test_ohlcv_zero_volume():
    """Test edge case with zero volume."""
    ohlcv = OHLCVData(timestamp=1234567890, open=50000, high=50000, low=50000, close=50000, volume=0)
    assert ohlcv.volume == 0


def test_ohlcv_equal_ohlc():
    """Test edge case with equal OHLC values."""
    ohlcv = OHLCVData(timestamp=1234567890, open=50000, high=50000, low=50000, close=50000, volume=1000000)
    assert ohlcv.open == ohlcv.high == ohlcv.low == ohlcv.close


def test_ohlcv_negative_open():
    """Test that negative open price raises ValueError."""
    with pytest.raises(ValueError, match="Open price cannot be negative"):
        OHLCVData(timestamp=1234567890, open=-1, high=51000, low=49000, close=50500, volume=1000000)


def test_ohlcv_negative_high():
    """Test that negative high price raises ValueError."""
    with pytest.raises(ValueError, match="High price cannot be negative"):
        OHLCVData(timestamp=1234567890, open=50000, high=-1, low=49000, close=50500, volume=1000000)


def test_ohlcv_negative_low():
    """Test that negative low price raises ValueError."""
    with pytest.raises(ValueError, match="Low price cannot be negative"):
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=-1, close=50500, volume=1000000)


def test_ohlcv_negative_close():
    """Test that negative close price raises ValueError."""
    with pytest.raises(ValueError, match="Close price cannot be negative"):
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=-1, volume=1000000)


def test_ohlcv_negative_volume():
    """Test that negative volume raises ValueError."""
    with pytest.raises(ValueError, match="Volume cannot be negative"):
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=-1)


def test_ohlcv_high_lower_than_low():
    """Test that high < low raises ValueError."""
    with pytest.raises(ValueError, match="High price cannot be lower than low price"):
        OHLCVData(timestamp=1234567890, open=50000, high=48000, low=49000, close=50500, volume=1000000)


def test_ohlcv_open_above_high():
    """Test that open > high raises ValueError."""
    with pytest.raises(ValueError, match="Open price must be between low and high prices"):
        OHLCVData(timestamp=1234567890, open=52000, high=51000, low=49000, close=50500, volume=1000000)


def test_ohlcv_close_below_low():
    """Test that close < low raises ValueError."""
    with pytest.raises(ValueError, match="Close price must be between low and high prices"):
        OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=48000, volume=1000000)


def test_ohlcv_timestamp_conversion():
    """Test timestamp conversion utilities."""
    ohlcv = OHLCVData(timestamp=1234567890000, open=50000, high=51000, low=49000, close=50500, volume=1000000)
    dt = ohlcv.to_datetime()
    assert isinstance(dt, datetime.datetime)
    
    # Test round-trip conversion
    dt_test = datetime.datetime(2023, 1, 1, 12, 0, 0)
    ohlcv_from_dt = OHLCVData.from_datetime(dt_test, 50000, 51000, 49000, 50500, 1000000)
    assert ohlcv_from_dt.to_datetime().replace(microsecond=0) == dt_test.replace(microsecond=0) 