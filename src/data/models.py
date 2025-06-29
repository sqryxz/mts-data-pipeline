from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class Cryptocurrency:
    """Data model for cryptocurrency information."""
    
    id: str
    symbol: str
    name: str
    market_cap_rank: Optional[int] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Cryptocurrency id cannot be empty")
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Cryptocurrency symbol cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Cryptocurrency name cannot be empty")


@dataclass
class OHLCVData:
    """Data model for OHLCV (Open, High, Low, Close, Volume) data."""
    
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def __post_init__(self):
        """Validate fields after initialization."""
        if self.open < 0:
            raise ValueError("Open price cannot be negative")
        if self.high < 0:
            raise ValueError("High price cannot be negative")
        if self.low < 0:
            raise ValueError("Low price cannot be negative")
        if self.close < 0:
            raise ValueError("Close price cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        
        # Logical price validation
        if self.high < self.low:
            raise ValueError("High price cannot be lower than low price")
        if self.open > self.high or self.open < self.low:
            raise ValueError("Open price must be between low and high prices")
        if self.close > self.high or self.close < self.low:
            raise ValueError("Close price must be between low and high prices")
    
    def to_datetime(self) -> datetime.datetime:
        """Convert timestamp to datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp / 1000)
    
    @classmethod
    def from_datetime(cls, dt: datetime.datetime, open_price: float, high: float, low: float, close: float, volume: float):
        """Create OHLCVData from datetime object."""
        timestamp = int(dt.timestamp() * 1000)
        return cls(timestamp=timestamp, open=open_price, high=high, low=low, close=close, volume=volume) 