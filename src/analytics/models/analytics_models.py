from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

@dataclass
class MacroIndicatorMetrics:
    """Data model for macro indicator analytics results.
    
    Represents statistical analysis results for economic indicators
    across different timeframes with validation.
    """
    indicator: str                    # Indicator name (e.g., 'GDP', 'CPI')
    timestamp: int                    # Unix timestamp for consistency with DB
    timeframe: str                   # Analysis timeframe ('1d', '1w', '1m', etc.)
    current_value: float             # Latest indicator value
    rate_of_change: float            # Percentage change from previous period
    z_score: float                   # Standard deviations from mean
    percentile_rank: float           # Percentile ranking (0-100)
    mean: float                      # Historical mean value
    std_dev: float                   # Standard deviation
    lookback_period: int = 30        # Analysis period in days (default: 30)

    # Class constants for validation
    MIN_PERCENTILE: ClassVar[float] = 0.0
    MAX_PERCENTILE: ClassVar[float] = 100.0
    MIN_STD_DEV: ClassVar[float] = 0.0
    MIN_LOOKBACK: ClassVar[int] = 1

    def __post_init__(self):
        """Validate field values after initialization."""
        if not (self.MIN_PERCENTILE <= self.percentile_rank <= self.MAX_PERCENTILE):
            raise ValueError(f"percentile_rank must be between {self.MIN_PERCENTILE} and {self.MAX_PERCENTILE}")
        if self.std_dev < self.MIN_STD_DEV:
            raise ValueError(f"std_dev must be >= {self.MIN_STD_DEV}")
        if self.lookback_period < self.MIN_LOOKBACK:
            raise ValueError(f"lookback_period must be >= {self.MIN_LOOKBACK}")
        if not self.indicator.strip():
            raise ValueError("indicator cannot be empty")
        if not self.timeframe.strip():
            raise ValueError("timeframe cannot be empty")

    @classmethod
    def from_datetime(cls, indicator: str, dt: datetime, timeframe: str, 
                     current_value: float, rate_of_change: float, z_score: float,
                     percentile_rank: float, mean: float, std_dev: float,
                     lookback_period: int = 30) -> 'MacroIndicatorMetrics':
        """Create instance from datetime object (converts to Unix timestamp)."""
        return cls(
            indicator=indicator,
            timestamp=int(dt.timestamp()),
            timeframe=timeframe,
            current_value=current_value,
            rate_of_change=rate_of_change,
            z_score=z_score,
            percentile_rank=percentile_rank,
            mean=mean,
            std_dev=std_dev,
            lookback_period=lookback_period
        )

    def to_datetime(self) -> datetime:
        """Convert Unix timestamp back to datetime object."""
        return datetime.fromtimestamp(self.timestamp)

    def is_outlier(self, threshold: float = 2.0) -> bool:
        """Check if current value is statistical outlier based on z-score."""
        return abs(self.z_score) > threshold

    def __str__(self) -> str:
        """Human-readable string representation."""
        dt = self.to_datetime()
        return (f"{self.indicator} ({self.timeframe}) at {dt.strftime('%Y-%m-%d %H:%M')}: "
               f"value={self.current_value:.2f}, change={self.rate_of_change:.1f}%, "
               f"z-score={self.z_score:.2f}") 