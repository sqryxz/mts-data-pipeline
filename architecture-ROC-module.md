# Macro Indicators Analytics Module Architecture

## Module Overview

The Macro Indicators Analytics Module extends the MTS Pipeline to provide real-time and historical analysis of macroeconomic indicators through rate-of-change calculations and z-score normalization across multiple timeframes.

## File & Folder Structure

```
src/
├── analytics/
│   ├── __init__.py
│   ├── macro/
│   │   ├── __init__.py
│   │   ├── calculator.py          # Core calculation engine
│   │   ├── timeframe_analyzer.py  # Multi-timeframe analysis
│   │   ├── z_score_engine.py      # Z-score calculations
│   │   └── rate_of_change.py      # ROC calculations
│   ├── models/
│   │   ├── __init__.py
│   │   └── analytics_models.py    # Data models for analytics
│   └── storage/
│       ├── __init__.py
│       ├── analytics_repository.py # Database operations
│       └── cache_manager.py        # Redis caching layer
├── services/
│   └── macro_analytics_service.py  # Service orchestration
├── api/
│   └── endpoints/
│       └── macro_analytics.py      # REST API endpoints
└── config/
    └── analytics/
        └── macro_analytics.json    # Configuration file
```

## Component Architecture

### 1. Core Calculation Engine (`calculator.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class MacroIndicatorCalculator:
    """
    Central calculation engine for macro indicator analytics.
    Coordinates ROC and z-score calculations across timeframes.
    """
    
    def __init__(self, db_path: str, redis_client=None):
        self.db_path = db_path
        self.redis_client = redis_client
        self.roc_calculator = RateOfChangeCalculator()
        self.zscore_engine = ZScoreEngine()
        self.repository = AnalyticsRepository(db_path)
        
    def calculate_metrics(
        self, 
        indicator: str, 
        timeframes: List[str] = ['1h', '4h', '24h'],
        lookback_periods: Dict[str, int] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate ROC and z-scores for specified indicator across timeframes.
        
        Returns:
        {
            '1h': {'roc': 0.025, 'z_score': 1.2},
            '4h': {'roc': 0.045, 'z_score': 0.8},
            '24h': {'roc': 0.082, 'z_score': 2.1}
        }
        """
        
    def batch_calculate(
        self,
        indicators: List[str],
        timeframes: List[str] = ['1h', '4h', '24h']
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Batch calculation for multiple indicators.
        """
```

### 2. Timeframe Analyzer (`timeframe_analyzer.py`)

```python
class TimeframeAnalyzer:
    """
    Handles multi-timeframe data aggregation and alignment.
    Manages data resampling and interpolation for different timeframes.
    """
    
    SUPPORTED_TIMEFRAMES = {
        '1h': timedelta(hours=1),
        '4h': timedelta(hours=4),
        '24h': timedelta(hours=24),
        '1d': timedelta(days=1),
        '1w': timedelta(weeks=1)
    }
    
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository
        
    def get_timeframe_data(
        self,
        indicator: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        Retrieve and resample data for specific timeframe.
        Handles missing data interpolation.
        """
        
    def align_multi_timeframe_data(
        self,
        indicator: str,
        timeframes: List[str],
        reference_time: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Align data across multiple timeframes to reference time.
        """
```

### 3. Z-Score Engine (`z_score_engine.py`)

```python
class ZScoreEngine:
    """
    Calculates z-scores with configurable lookback windows.
    Supports rolling and expanding window calculations.
    """
    
    def __init__(self, default_lookback: int = 30):
        self.default_lookback = default_lookback
        
    def calculate_z_score(
        self,
        values: pd.Series,
        lookback_period: Optional[int] = None,
        method: str = 'rolling'  # 'rolling' or 'expanding'
    ) -> float:
        """
        Calculate z-score for the most recent value.
        
        Z-score = (value - mean) / std_dev
        """
        
    def calculate_rolling_z_scores(
        self,
        values: pd.Series,
        lookback_period: int
    ) -> pd.Series:
        """
        Calculate z-scores for entire series using rolling window.
        """
        
    def get_z_score_percentile(
        self,
        z_score: float
    ) -> float:
        """
        Convert z-score to percentile rank.
        """
```

### 4. Rate of Change Calculator (`rate_of_change.py`)

```python
class RateOfChangeCalculator:
    """
    Calculates percentage rate of change across different periods.
    Handles edge cases and data quality issues.
    """
    
    def calculate_roc(
        self,
        current_value: float,
        previous_value: float,
        handle_zero: bool = True
    ) -> float:
        """
        Calculate percentage rate of change.
        
        ROC = ((current - previous) / previous) * 100
        """
        
    def calculate_period_roc(
        self,
        values: pd.Series,
        period: int
    ) -> float:
        """
        Calculate ROC over specified period.
        """
        
    def calculate_multi_period_roc(
        self,
        values: pd.Series,
        periods: List[int]
    ) -> Dict[int, float]:
        """
        Calculate ROC for multiple periods simultaneously.
        """
```

### 5. Analytics Models (`analytics_models.py`)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class MacroIndicatorMetrics:
    """Data model for macro indicator analytics results."""
    indicator: str
    timestamp: datetime
    timeframe: str
    current_value: float
    rate_of_change: float
    z_score: float
    percentile_rank: float
    mean: float
    std_dev: float
    lookback_period: int
    
@dataclass
class AnalyticsRequest:
    """Request model for analytics calculations."""
    indicators: List[str]
    timeframes: List[str] = None
    lookback_periods: Dict[str, int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
@dataclass
class AnalyticsResponse:
    """Response model for analytics API."""
    request_id: str
    timestamp: datetime
    results: Dict[str, Dict[str, MacroIndicatorMetrics]]
    execution_time_ms: float
    cache_hit: bool
```

### 6. Analytics Repository (`analytics_repository.py`)

```python
class AnalyticsRepository:
    """
    Database operations for analytics module.
    Extends base repository with analytics-specific queries.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_indicator_data(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
        interpolate: bool = True
    ) -> pd.DataFrame:
        """
        Retrieve indicator data with optional interpolation.
        """
        
    def save_analytics_results(
        self,
        results: List[MacroIndicatorMetrics]
    ) -> None:
        """
        Persist calculated analytics to database.
        """
        
    def get_latest_analytics(
        self,
        indicator: str,
        timeframe: str
    ) -> Optional[MacroIndicatorMetrics]:
        """
        Retrieve most recent analytics for indicator/timeframe.
        """
```

### 7. Cache Manager (`cache_manager.py`)

```python
class AnalyticsCacheManager:
    """
    Redis caching layer for analytics results.
    Implements TTL-based cache invalidation.
    """
    
    CACHE_KEY_PATTERNS = {
        'metrics': 'analytics:metrics:{indicator}:{timeframe}:{timestamp}',
        'roc': 'analytics:roc:{indicator}:{period}:{timestamp}',
        'zscore': 'analytics:zscore:{indicator}:{lookback}:{timestamp}'
    }
    
    DEFAULT_TTL = {
        '1h': 3600,      # 1 hour
        '4h': 14400,     # 4 hours
        '24h': 86400     # 24 hours
    }
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def get_cached_metrics(
        self,
        indicator: str,
        timeframe: str,
        timestamp: datetime
    ) -> Optional[MacroIndicatorMetrics]:
        """
        Retrieve cached metrics if available.
        """
        
    def cache_metrics(
        self,
        metrics: MacroIndicatorMetrics,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache analytics results with appropriate TTL.
        """
```

### 8. Macro Analytics Service (`macro_analytics_service.py`)

```python
class MacroAnalyticsService:
    """
    Service orchestration layer for macro analytics.
    Coordinates calculations, caching, and persistence.
    """
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.calculator = MacroIndicatorCalculator(
            db_path=self.config['database_path'],
            redis_client=self._init_redis()
        )
        self.cache_manager = AnalyticsCacheManager(self.redis_client)
        self.scheduler = None
        
    def analyze_indicators(
        self,
        request: AnalyticsRequest
    ) -> AnalyticsResponse:
        """
        Main entry point for indicator analysis.
        Handles caching, calculation, and response formatting.
        """
        
    def schedule_periodic_updates(
        self,
        indicators: List[str],
        interval_minutes: int = 15
    ) -> None:
        """
        Schedule periodic recalculation of analytics.
        """
        
    async def real_time_analysis(
        self,
        indicator: str,
        callback: Callable
    ) -> None:
        """
        Real-time analysis with WebSocket updates.
        """
```

### 9. API Endpoints (`macro_analytics.py`)

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

router = APIRouter(prefix="/analytics/macro", tags=["macro_analytics"])

@router.post("/calculate", response_model=AnalyticsResponse)
async def calculate_analytics(
    request: AnalyticsRequest,
    service: MacroAnalyticsService = Depends(get_analytics_service)
) -> AnalyticsResponse:
    """
    Calculate ROC and z-scores for specified indicators.
    
    Example request:
    {
        "indicators": ["VIX", "DXY", "US10Y"],
        "timeframes": ["1h", "4h", "24h"],
        "lookback_periods": {
            "1h": 24,
            "4h": 30,
            "24h": 90
        }
    }
    """
    
@router.get("/indicators/{indicator}/latest")
async def get_latest_analytics(
    indicator: str,
    timeframe: Optional[str] = "24h",
    service: MacroAnalyticsService = Depends(get_analytics_service)
) -> MacroIndicatorMetrics:
    """
    Get latest analytics for specific indicator.
    """
    
@router.ws("/indicators/{indicator}/stream")
async def stream_analytics(
    websocket: WebSocket,
    indicator: str,
    timeframes: List[str] = Query(["1h", "4h", "24h"])
):
    """
    WebSocket endpoint for real-time analytics streaming.
    """
```

## State Management

### 1. Database State

**Analytics Results Table:**
```sql
CREATE TABLE macro_analytics_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    current_value REAL NOT NULL,
    rate_of_change REAL NOT NULL,
    z_score REAL NOT NULL,
    percentile_rank REAL NOT NULL,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    lookback_period INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator, timeframe, timestamp)
);

CREATE INDEX idx_analytics_indicator_timeframe 
ON macro_analytics_results(indicator, timeframe, timestamp DESC);
```

### 2. Cache State

**Redis Cache Structure:**
```
# Current metrics cache
analytics:metrics:VIX:1h:1234567890 → {serialized MacroIndicatorMetrics}

# ROC calculation cache
analytics:roc:VIX:24:1234567890 → 0.045

# Z-score cache
analytics:zscore:VIX:30:1234567890 → 1.85

# Calculation lock (prevent duplicate calculations)
analytics:lock:VIX:1h → 1 (with TTL)
```

### 3. In-Memory State

```python
class AnalyticsState:
    """In-memory state management for performance optimization."""
    
    def __init__(self):
        # LRU cache for frequent calculations
        self._calculation_cache = LRUCache(maxsize=1000)
        
        # Running statistics for real-time updates
        self._running_stats = {
            # indicator: {timeframe: RunningStatistics}
        }
        
        # Active calculation tracking
        self._active_calculations = set()
```

## Service Connections

### 1. Integration with Existing Services

```python
# Integration points with existing MTS pipeline

# Data Collection Service Integration
from src.services.data_collection_service import DataCollectionService

class MacroAnalyticsIntegration:
    def __init__(self, analytics_service: MacroAnalyticsService):
        self.analytics_service = analytics_service
        
    def on_macro_data_update(self, indicator: str, new_value: float):
        """
        Callback triggered when new macro data is collected.
        Initiates analytics recalculation.
        """
        
# Signal Generator Integration  
from src.signals.signal_aggregator import SignalAggregator

class AnalyticsSignalIntegration:
    def get_macro_analytics_context(
        self,
        indicators: List[str]
    ) -> Dict[str, MacroIndicatorMetrics]:
        """
        Provide analytics context to signal generation strategies.
        """
```

### 2. Service Communication Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Data Collection │────▶│ Macro Analytics  │────▶│ Signal Generator│
│    Service      │     │     Service      │     │    Service      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                          │
         │                       ▼                          │
         │              ┌──────────────────┐               │
         └─────────────▶│   SQLite DB      │◀──────────────┘
                        │ & Redis Cache    │
                        └──────────────────┘
```

### 3. Event-Driven Updates

```python
# Event definitions
class MacroAnalyticsEvent:
    CALCULATION_COMPLETED = "macro.analytics.calculation.completed"
    THRESHOLD_EXCEEDED = "macro.analytics.threshold.exceeded"
    ANOMALY_DETECTED = "macro.analytics.anomaly.detected"

# Event publisher
class AnalyticsEventPublisher:
    def publish_calculation_completed(
        self,
        indicator: str,
        metrics: MacroIndicatorMetrics
    ):
        """Publish event when calculation completes."""
        
    def publish_threshold_alert(
        self,
        indicator: str,
        threshold_type: str,
        value: float
    ):
        """Publish alert when thresholds are exceeded."""
```

## Configuration

### Configuration File (`macro_analytics.json`)

```json
{
  "analytics": {
    "default_timeframes": ["1h", "4h", "24h"],
    "default_lookback_periods": {
      "1h": 24,
      "4h": 30,
      "24h": 90
    },
    "z_score_thresholds": {
      "extreme_high": 3.0,
      "high": 2.0,
      "normal": 1.0,
      "low": -2.0,
      "extreme_low": -3.0
    },
    "roc_thresholds": {
      "1h": {
        "significant_increase": 0.05,
        "significant_decrease": -0.05
      },
      "4h": {
        "significant_increase": 0.10,
        "significant_decrease": -0.10
      },
      "24h": {
        "significant_increase": 0.20,
        "significant_decrease": -0.20
      }
    },
    "indicators": {
      "VIX": {
        "interpolation_method": "linear",
        "outlier_detection": true,
        "custom_thresholds": {
          "spike_level": 25.0
        }
      },
      "DXY": {
        "interpolation_method": "ffill",
        "smoothing_window": 3
      },
      "US10Y": {
        "interpolation_method": "linear",
        "decimal_places": 3
      }
    },
    "performance": {
      "batch_size": 100,
      "parallel_workers": 4,
      "cache_enabled": true,
      "cache_ttl_multiplier": 1.0
    },
    "monitoring": {
      "metrics_enabled": true,
      "alert_channels": ["email", "webhook"],
      "health_check_interval": 60
    }
  }
}
```

## Performance Optimizations

### 1. Batch Processing

```python
class BatchProcessor:
    """Efficient batch processing for multiple indicators."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        
    async def process_batch(
        self,
        indicators: List[str],
        calculator: MacroIndicatorCalculator
    ) -> Dict[str, Dict[str, MacroIndicatorMetrics]]:
        """
        Process indicators in optimized batches.
        Uses asyncio for concurrent processing.
        """
```

### 2. Parallel Calculation

```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

class ParallelCalculator:
    """Parallel calculation engine for performance."""
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def calculate_parallel(
        self,
        tasks: List[Callable]
    ) -> List[Any]:
        """Execute calculations in parallel."""
```

### 3. Incremental Updates

```python
class IncrementalUpdater:
    """
    Incremental update strategy to avoid full recalculation.
    Maintains running statistics for efficiency.
    """
    
    def update_statistics(
        self,
        indicator: str,
        new_value: float,
        timestamp: datetime
    ) -> MacroIndicatorMetrics:
        """
        Update statistics incrementally with new data point.
        """
```

## Error Handling

```python
class MacroAnalyticsError(Exception):
    """Base exception for analytics module."""

class DataQualityError(MacroAnalyticsError):
    """Raised when data quality issues detected."""

class CalculationError(MacroAnalyticsError):
    """Raised when calculation fails."""

class TimeframeError(MacroAnalyticsError):
    """Raised for invalid timeframe operations."""

# Error recovery
class ErrorRecovery:
    @staticmethod
    def handle_missing_data(
        indicator: str,
        timeframe: str,
        method: str = "interpolate"
    ) -> pd.Series:
        """Handle missing data points gracefully."""
        
    @staticmethod
    def handle_calculation_failure(
        error: Exception,
        fallback_strategy: str = "use_cached"
    ) -> Optional[MacroIndicatorMetrics]:
        """Recover from calculation failures."""
```

## Testing Strategy

```python
# Test structure
tests/
├── analytics/
│   ├── test_calculator.py
│   ├── test_timeframe_analyzer.py
│   ├── test_z_score_engine.py
│   ├── test_rate_of_change.py
│   └── integration/
│       ├── test_service_integration.py
│       └── test_api_endpoints.py
```

## Deployment Considerations

### 1. Resource Requirements

```yaml
# Kubernetes resource allocation
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### 2. Monitoring Metrics

```python
# Prometheus metrics
analytics_calculation_duration = Histogram(
    'macro_analytics_calculation_seconds',
    'Time spent calculating analytics',
    ['indicator', 'timeframe']
)

analytics_cache_hit_rate = Counter(
    'macro_analytics_cache_hits_total',
    'Cache hit rate for analytics',
    ['indicator', 'timeframe']
)
```

This architecture provides a comprehensive, scalable solution for calculating rate-of-change and z-scores across multiple timeframes while integrating seamlessly with the existing MTS Pipeline infrastructure.