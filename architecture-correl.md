# Real-Time Correlation Analysis Module Architecture

## Overview

The Real-Time Correlation Analysis Module is a specialized component within the MTS Data Pipeline that monitors real-time relationships between major cryptocurrency pairs and macro economic indicators. It generates JSON alerts when correlations break down beyond statistical thresholds and produces comprehensive correlation mosaics for market analysis.

## File & Folder Structure

```
src/correlation_analysis/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── correlation_engine.py          # Main correlation calculation engine
│   ├── correlation_monitor.py         # Real-time monitoring service
│   ├── correlation_calculator.py      # Statistical correlation calculations
│   ├── divergence_detector.py         # Divergence signal detection
│   └── mosaic_generator.py           # Daily correlation mosaic creation
├── data/
│   ├── __init__.py
│   ├── data_fetcher.py               # Real-time data retrieval
│   ├── data_validator.py             # Data quality validation
│   └── data_normalizer.py            # Data normalization and alignment
├── alerts/
│   ├── __init__.py
│   ├── correlation_alert_system.py   # Alert generation and distribution
│   ├── alert_templates.py            # JSON alert templates
│   └── alert_filters.py              # Alert filtering and deduplication
├── analysis/
│   ├── __init__.py
│   ├── statistical_analyzer.py       # Statistical analysis utilities
│   ├── trend_analyzer.py             # Trend and regime detection
│   └── breakout_detector.py          # Correlation breakout detection
├── storage/
│   ├── __init__.py
│   ├── correlation_storage.py        # Correlation data persistence
│   ├── state_manager.py              # Module state management
│   └── cache_manager.py              # Redis-based caching
├── visualization/
│   ├── __init__.py
│   ├── mosaic_renderer.py            # Correlation mosaic visualization
│   ├── chart_generator.py            # Chart generation utilities
│   └── report_generator.py           # HTML/PDF report generation
├── config/
│   ├── correlation_config.json       # Module configuration
│   ├── pairs_config.json             # Monitored pairs configuration
│   └── thresholds_config.json        # Alert threshold configuration
└── tests/
    ├── __init__.py
    ├── test_correlation_engine.py
    ├── test_correlation_monitor.py
    ├── test_alert_system.py
    └── test_mosaic_generator.py

# Integration with main project
data/correlation/
├── state/
│   ├── correlation_state.json        # Current correlation state
│   ├── rolling_correlations.json     # Historical rolling correlations
│   └── breakout_history.json         # Correlation breakout history
├── alerts/
│   ├── correlation_breakdown_*.json  # Breakdown alerts
│   ├── divergence_signal_*.json      # Divergence alerts
│   └── mosaic_daily_*.json           # Daily mosaic alerts
├── mosaics/
│   ├── daily/
│   │   ├── correlation_mosaic_20250108.json
│   │   ├── correlation_mosaic_20250108.html
│   │   └── correlation_mosaic_20250108.png
│   └── historical/
│       └── correlation_history.db    # SQLite for historical mosaics
└── cache/
    ├── realtime_data.json            # Real-time price cache
    └── correlation_cache.json        # Calculated correlation cache

# Configuration integration
config/correlation_analysis/
├── monitored_pairs.json             # Crypto-macro pair definitions
├── alert_thresholds.json            # Statistical threshold settings
└── mosaic_settings.json             # Mosaic generation settings
```

## Component Architecture

### 1. Core Engine (`src/correlation_analysis/core/`)

#### `correlation_engine.py`
**Purpose**: Main orchestration engine for correlation analysis
**Responsibilities**:
- Coordinate all correlation analysis components
- Manage real-time data flow
- Trigger alert generation and mosaic creation
- Handle service lifecycle

```python
class CorrelationEngine:
    """
    Main correlation analysis orchestrator
    """
    
    def __init__(self):
        self.monitor = CorrelationMonitor()
        self.calculator = CorrelationCalculator()
        self.divergence_detector = DivergenceDetector()
        self.alert_system = CorrelationAlertSystem()
        self.mosaic_generator = MosaicGenerator()
        self.data_fetcher = DataFetcher()
        self.state_manager = StateManager()
        
    async def start_monitoring(self):
        """Start real-time correlation monitoring"""
        
    async def process_data_update(self, data_update):
        """Process new market data and update correlations"""
        
    async def generate_daily_mosaic(self):
        """Generate daily correlation mosaic"""
```

#### `correlation_monitor.py`
**Purpose**: Real-time monitoring service for correlation changes
**Responsibilities**:
- Monitor real-time price feeds
- Calculate rolling correlations
- Detect correlation breakdowns
- Trigger alerts when thresholds are breached

#### `correlation_calculator.py`
**Purpose**: Statistical correlation calculations
**Responsibilities**:
- Calculate Pearson/Spearman correlations
- Compute rolling correlations with multiple windows
- Statistical significance testing
- Z-score calculations for correlation changes

#### `divergence_detector.py`
**Purpose**: Detect divergence signals between correlated assets
**Responsibilities**:
- Identify price divergences despite high correlation
- Detect momentum divergences
- Signal potential correlation breakdown
- Generate divergence alerts

#### `mosaic_generator.py`
**Purpose**: Generate comprehensive correlation mosaics
**Responsibilities**:
- Create daily correlation matrices
- Generate visual correlation heatmaps
- Produce HTML/JSON reports
- Historical correlation trend analysis

### 2. Data Layer (`src/correlation_analysis/data/`)

#### `data_fetcher.py`
**Purpose**: Real-time data retrieval and integration
**Responsibilities**:
- Interface with existing MTS data pipeline
- Fetch real-time crypto prices
- Retrieve macro indicator updates
- Handle data synchronization

```python
class DataFetcher:
    """
    Real-time data fetcher integrated with MTS pipeline
    """
    
    def __init__(self):
        self.crypto_data_client = CryptoDataClient()
        self.macro_data_client = MacroDataClient()
        self.redis_client = redis.Redis()
        
    async def get_realtime_prices(self, symbols: List[str]) -> Dict:
        """Get real-time crypto prices"""
        
    async def get_macro_indicators(self, indicators: List[str]) -> Dict:
        """Get latest macro indicator values"""
        
    async def sync_data_timestamps(self, data: Dict) -> Dict:
        """Synchronize data timestamps for correlation analysis"""
```

#### `data_validator.py`
**Purpose**: Data quality validation
**Responsibilities**:
- Validate price data completeness
- Check for data anomalies
- Handle missing data points
- Ensure data quality for correlation calculations

#### `data_normalizer.py`
**Purpose**: Data normalization and alignment
**Responsibilities**:
- Normalize different data frequencies
- Align timestamps across data sources
- Handle timezone conversions
- Prepare data for correlation analysis

### 3. Alert System (`src/correlation_analysis/alerts/`)

#### `correlation_alert_system.py`
**Purpose**: Alert generation and distribution
**Responsibilities**:
- Generate JSON alerts for correlation breakdowns
- Create divergence signal alerts
- Distribute alerts through multiple channels
- Integrate with existing MTS alert system

```python
class CorrelationAlertSystem:
    """
    Correlation-specific alert system integrated with MTS alerts
    """
    
    def __init__(self):
        self.alert_storage = AlertStorage('data/correlation/alerts/')
        self.notification_manager = NotificationManager()
        self.template_engine = AlertTemplateEngine()
        
    async def generate_breakdown_alert(self, pair: str, correlation_data: Dict) -> Dict:
        """Generate correlation breakdown alert"""
        
    async def generate_divergence_alert(self, pair: str, divergence_data: Dict) -> Dict:
        """Generate divergence signal alert"""
        
    async def generate_mosaic_alert(self, mosaic_data: Dict) -> Dict:
        """Generate daily mosaic completion alert"""
```

#### `alert_templates.py`
**Purpose**: JSON alert templates
**Responsibilities**:
- Define alert JSON schemas
- Template rendering for different alert types
- Consistent alert formatting

#### `alert_filters.py`
**Purpose**: Alert filtering and deduplication
**Responsibilities**:
- Prevent duplicate alerts
- Filter alerts based on significance
- Rate limiting for alert generation

### 4. Analysis Layer (`src/correlation_analysis/analysis/`)

#### `statistical_analyzer.py`
**Purpose**: Statistical analysis utilities
**Responsibilities**:
- Statistical significance testing
- Confidence interval calculations
- Z-score and standard deviation analysis
- Correlation stability metrics

#### `trend_analyzer.py`
**Purpose**: Trend and regime detection
**Responsibilities**:
- Detect correlation regime changes
- Identify trending vs. ranging correlation periods
- Market regime classification

#### `breakout_detector.py`
**Purpose**: Correlation breakout detection
**Responsibilities**:
- Detect 2-sigma correlation breakouts
- Identify correlation reversals
- Signal correlation regime changes

### 5. Storage Layer (`src/correlation_analysis/storage/`)

#### `correlation_storage.py`
**Purpose**: Correlation data persistence
**Responsibilities**:
- Store correlation calculations
- Persist historical correlation data
- Manage correlation time series

#### `state_manager.py`
**Purpose**: Module state management
**Responsibilities**:
- Persist module state across restarts
- Manage correlation calculation state
- Handle service recovery

#### `cache_manager.py`
**Purpose**: Redis-based caching
**Responsibilities**:
- Cache real-time correlation calculations
- Store frequently accessed data
- Manage cache expiration and cleanup

### 6. Visualization Layer (`src/correlation_analysis/visualization/`)

#### `mosaic_renderer.py`
**Purpose**: Correlation mosaic visualization
**Responsibilities**:
- Generate correlation heatmaps
- Create interactive HTML mosaics
- Produce PNG/SVG visualizations

#### `chart_generator.py`
**Purpose**: Chart generation utilities
**Responsibilities**:
- Generate correlation time series charts
- Create breakout visualization charts
- Produce statistical analysis charts

#### `report_generator.py`
**Purpose**: HTML/PDF report generation
**Responsibilities**:
- Generate daily correlation reports
- Create summary statistics reports
- Produce executive dashboards

## State Management

### State Storage Locations

#### 1. **Real-time State** (Redis)
```python
# Redis Keys Structure
correlation:realtime:{pair}:{window}        # Current correlation values
correlation:zscore:{pair}:{window}          # Z-scores for correlation changes
correlation:breakout:{pair}                 # Active breakout status
correlation:divergence:{pair}               # Divergence signals
correlation:state:engine                    # Engine operational state
correlation:cache:prices                    # Real-time price cache
correlation:cache:indicators                # Macro indicator cache
```

#### 2. **Persistent State** (JSON Files)
```json
// data/correlation/state/correlation_state.json
{
  "last_updated": "2025-01-08T10:30:00Z",
  "active_pairs": {
    "BTC_ETH": {
      "current_correlation": 0.85,
      "30d_average": 0.82,
      "z_score": 1.2,
      "status": "normal",
      "last_breakout": null
    },
    "BTC_DXY": {
      "current_correlation": -0.45,
      "30d_average": -0.38,
      "z_score": -2.3,
      "status": "breakdown",
      "last_breakout": "2025-01-08T09:15:00Z"
    }
  },
  "monitoring_windows": [7, 14, 30, 60],
  "alert_counts": {
    "breakdown_alerts_today": 3,
    "divergence_alerts_today": 1
  }
}
```

#### 3. **Historical Data** (SQLite)
```sql
-- Correlation history database
CREATE TABLE correlation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_name TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    correlation_value REAL NOT NULL,
    window_days INTEGER NOT NULL,
    z_score REAL,
    is_significant BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pair_name, timestamp, window_days)
);

CREATE TABLE breakout_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_name TEXT NOT NULL,
    event_type TEXT NOT NULL, -- 'breakdown', 'reversal', 'divergence'
    timestamp INTEGER NOT NULL,
    correlation_before REAL NOT NULL,
    correlation_after REAL NOT NULL,
    z_score REAL NOT NULL,
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_mosaics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    mosaic_data TEXT NOT NULL, -- JSON blob
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);
```

## Service Connections

### Integration with MTS Pipeline

#### 1. **Data Pipeline Integration**
```python
# Integration with existing MTS data collection
class CorrelationDataIntegration:
    """
    Integration layer with MTS data pipeline
    """
    
    def __init__(self):
        self.mts_database = MTSDatabase()
        self.redis_client = redis.Redis()
        
    async def get_crypto_data(self, symbols: List[str], timeframe: str) -> pd.DataFrame:
        """Get crypto data from MTS database"""
        return await self.mts_database.get_ohlcv_data(symbols, timeframe)
        
    async def get_macro_data(self, indicators: List[str]) -> pd.DataFrame:
        """Get macro data from MTS database"""
        return await self.mts_database.get_macro_indicators(indicators)
        
    async def subscribe_to_realtime_updates(self):
        """Subscribe to real-time data updates from MTS pipeline"""
        # Connect to MTS real-time data streams
```

#### 2. **Alert System Integration**
```python
# Integration with existing MTS alert system
class CorrelationAlertIntegration:
    """
    Integration with MTS JSON alert system
    """
    
    def __init__(self):
        self.mts_alert_system = JSONAlertSystem()
        self.alert_directory = Path("data/alerts/")
        
    async def generate_correlation_alert(self, alert_data: Dict) -> str:
        """Generate correlation alert using MTS alert system"""
        
        # Use existing MTS alert infrastructure
        alert = {
            "timestamp": int(time.time() * 1000),
            "alert_type": "correlation_breakdown",
            "pair": alert_data['pair'],
            "correlation_current": alert_data['current_correlation'],
            "correlation_average": alert_data['average_correlation'],
            "z_score": alert_data['z_score'],
            "significance_level": alert_data['significance'],
            "breakout_direction": alert_data['direction'],
            "recommended_action": alert_data['action']
        }
        
        return await self.mts_alert_system.store_and_distribute(alert)
```

#### 3. **Scheduler Integration**
```python
# Integration with MTS multi-tier scheduler
class CorrelationSchedulerIntegration:
    """
    Integration with MTS enhanced scheduler
    """
    
    def __init__(self):
        self.scheduler = EnhancedMultiTierScheduler()
        
    def register_correlation_tasks(self):
        """Register correlation analysis tasks with MTS scheduler"""
        
        # Real-time correlation monitoring (every 5 minutes)
        self.scheduler.add_task(
            task_id="correlation_realtime_monitor",
            task_func=self.run_realtime_analysis,
            interval=300,  # 5 minutes
            tier="high_frequency"
        )
        
        # Daily mosaic generation (once daily at market close)
        self.scheduler.add_task(
            task_id="correlation_daily_mosaic",
            task_func=self.generate_daily_mosaic,
            interval=86400,  # 24 hours
            tier="macro",
            scheduled_time="16:00"  # 4 PM EST
        )
        
        # Correlation state persistence (every hour)
        self.scheduler.add_task(
            task_id="correlation_state_save",
            task_func=self.save_correlation_state,
            interval=3600,  # 1 hour
            tier="hourly"
        )
```

### Service Communication Architecture

#### 1. **Event-Driven Communication**
```python
# Event system for correlation analysis
class CorrelationEventSystem:
    """
    Event-driven communication for correlation analysis
    """
    
    def __init__(self):
        self.event_bus = EventBus()
        self.subscribers = {}
        
    def publish_correlation_update(self, pair: str, correlation_data: Dict):
        """Publish correlation update event"""
        event = CorrelationUpdateEvent(
            pair=pair,
            correlation=correlation_data['correlation'],
            z_score=correlation_data['z_score'],
            timestamp=datetime.now()
        )
        self.event_bus.publish("correlation.update", event)
        
    def publish_breakdown_detected(self, pair: str, breakdown_data: Dict):
        """Publish correlation breakdown event"""
        event = CorrelationBreakdownEvent(
            pair=pair,
            breakdown_type=breakdown_data['type'],
            severity=breakdown_data['severity'],
            timestamp=datetime.now()
        )
        self.event_bus.publish("correlation.breakdown", event)
```

#### 2. **API Integration**
```python
# REST API endpoints for correlation analysis
@app.get("/correlation/pairs/{pair}/current")
async def get_current_correlation(pair: str):
    """Get current correlation for a specific pair"""
    
@app.get("/correlation/pairs/{pair}/history")
async def get_correlation_history(pair: str, days: int = 30):
    """Get correlation history for a specific pair"""
    
@app.get("/correlation/mosaic/latest")
async def get_latest_mosaic():
    """Get the latest correlation mosaic"""
    
@app.get("/correlation/alerts/active")
async def get_active_alerts():
    """Get currently active correlation alerts"""
    
@app.post("/correlation/pairs/{pair}/threshold")
async def update_correlation_threshold(pair: str, threshold: float):
    """Update correlation alert threshold for a pair"""
```

## Configuration Management

### Main Configuration (`config/correlation_analysis/monitored_pairs.json`)
```json
{
  "crypto_pairs": {
    "BTC_ETH": {
      "primary": "bitcoin",
      "secondary": "ethereum",
      "correlation_windows": [7, 14, 30, 60],
      "alert_threshold": 2.0,
      "significance_level": 0.05,
      "min_data_points": 20
    },
    "BTC_SOL": {
      "primary": "bitcoin",
      "secondary": "solana",
      "correlation_windows": [7, 14, 30],
      "alert_threshold": 2.0,
      "significance_level": 0.05,
      "min_data_points": 20
    }
  },
  "macro_pairs": {
    "BTC_DXY": {
      "crypto": "bitcoin",
      "macro_indicator": "DXY",
      "correlation_windows": [14, 30, 60],
      "alert_threshold": 1.8,
      "significance_level": 0.05,
      "expected_correlation": "negative"
    },
    "ETH_YIELD_SPREAD": {
      "crypto": "ethereum",
      "macro_indicator": "2Y10Y_SPREAD",
      "correlation_windows": [30, 60, 90],
      "alert_threshold": 1.8,
      "significance_level": 0.05,
      "expected_correlation": "positive"
    }
  },
  "monitoring_settings": {
    "update_frequency_seconds": 300,
    "data_retention_days": 365,
    "cache_ttl_seconds": 3600,
    "max_alerts_per_hour": 10
  }
}
```

### Alert Thresholds (`config/correlation_analysis/alert_thresholds.json`)
```json
{
  "breakdown_thresholds": {
    "z_score_threshold": 2.0,
    "significance_level": 0.05,
    "min_duration_minutes": 15,
    "confirmation_windows": 2
  },
  "divergence_thresholds": {
    "price_divergence_threshold": 0.05,
    "momentum_divergence_threshold": 0.03,
    "correlation_stability_threshold": 0.7,
    "min_correlation_for_divergence": 0.5
  },
  "mosaic_settings": {
    "generation_time": "16:00",
    "timezone": "America/New_York",
    "include_significance_test": true,
    "heatmap_color_scheme": "RdYlBu_r",
    "export_formats": ["json", "html", "png"]
  }
}
```

## Alert JSON Schemas

### Correlation Breakdown Alert
```json
{
  "timestamp": 1704722400000,
  "alert_type": "correlation_breakdown",
  "alert_id": "corr_breakdown_btc_dxy_20250108_103000",
  "pair": "BTC_DXY",
  "pair_type": "crypto_macro",
  "breakdown_details": {
    "current_correlation": -0.72,
    "30d_average_correlation": -0.38,
    "z_score": -2.34,
    "significance_level": 0.02,
    "threshold_exceeded": true,
    "breakdown_direction": "stronger_negative",
    "duration_minutes": 45
  },
  "market_context": {
    "btc_price": 42150.50,
    "btc_24h_change": -0.025,
    "dxy_value": 103.45,
    "dxy_24h_change": 0.008,
    "market_volatility": "high"
  },
  "statistical_analysis": {
    "correlation_windows": {
      "7d": -0.68,
      "14d": -0.55,
      "30d": -0.38,
      "60d": -0.42
    },
    "confidence_interval": [-0.85, -0.59],
    "p_value": 0.019
  },
  "recommended_actions": [
    "Monitor for potential trend reversal",
    "Consider macro hedge positions",
    "Watch for correlation normalization"
  ],
  "alert_metadata": {
    "severity": "high",
    "category": "correlation_analysis",
    "expires_at": 1704726000000,
    "related_pairs": ["ETH_DXY", "BTC_YIELD_SPREAD"]
  }
}
```

### Divergence Signal Alert
```json
{
  "timestamp": 1704722400000,
  "alert_type": "divergence_signal",
  "alert_id": "div_signal_btc_eth_20250108_103000",
  "pair": "BTC_ETH",
  "pair_type": "crypto_crypto",
  "divergence_details": {
    "divergence_type": "price_momentum",
    "correlation_strength": 0.82,
    "price_divergence": {
      "btc_momentum": 0.045,
      "eth_momentum": -0.023,
      "divergence_magnitude": 0.068,
      "duration_hours": 6
    },
    "significance": "strong"
  },
  "price_data": {
    "btc_price": 42150.50,
    "eth_price": 2580.25,
    "btc_24h_change": 0.045,
    "eth_24h_change": -0.023,
    "correlation_24h": 0.82
  },
  "technical_indicators": {
    "rsi_divergence": true,
    "macd_divergence": false,
    "volume_confirmation": true
  },
  "recommended_actions": [
    "Monitor for potential correlation breakdown",
    "Consider pair trading opportunity",
    "Watch for momentum convergence"
  ],
  "alert_metadata": {
    "severity": "medium",
    "category": "correlation_analysis",
    "expires_at": 1704729600000
  }
}
```

### Daily Mosaic Alert
```json
{
  "timestamp": 1704657600000,
  "alert_type": "daily_correlation_mosaic",
  "alert_id": "mosaic_daily_20250108",
  "date": "2025-01-08",
  "mosaic_summary": {
    "total_pairs_analyzed": 24,
    "significant_correlations": 18,
    "breakdown_events": 3,
    "divergence_signals": 2,
    "average_correlation_strength": 0.64
  },
  "key_findings": [
    {
      "finding": "BTC-DXY correlation strengthened significantly",
      "correlation": -0.72,
      "z_score": -2.34,
      "significance": "high"
    },
    {
      "finding": "ETH-SOL correlation remains stable",
      "correlation": 0.85,
      "z_score": 0.12,
      "significance": "normal"
    }
  ],
  "file_locations": {
    "json_report": "data/correlation/mosaics/daily/correlation_mosaic_20250108.json",
    "html_report": "data/correlation/mosaics/daily/correlation_mosaic_20250108.html",
    "heatmap_image": "data/correlation/mosaics/daily/correlation_mosaic_20250108.png"
  },
  "alert_metadata": {
    "severity": "info",
    "category": "correlation_analysis",
    "report_type": "daily_summary"
  }
}
```

## Integration Points

### 1. **MTS Data Pipeline Integration**
- **Data Source**: Leverages existing crypto OHLCV data and macro indicators
- **Real-time Updates**: Subscribes to MTS real-time data streams
- **Storage**: Uses existing SQLite database with additional correlation tables

### 2. **Alert System Integration**
- **Alert Distribution**: Uses existing MTS JSON alert system
- **Notification Channels**: Integrates with existing Discord/webhook notifications
- **Alert Storage**: Stores alerts in existing `data/alerts/` directory structure

### 3. **Scheduler Integration**
- **Task Management**: Registers tasks with MTS multi-tier scheduler
- **Resource Optimization**: Follows existing API rate limiting patterns
- **State Persistence**: Uses existing state management patterns

### 4. **API Integration**
- **REST Endpoints**: Extends existing FastAPI server with correlation endpoints
- **Authentication**: Uses existing API authentication mechanisms
- **Rate Limiting**: Follows existing API rate limiting patterns

### 5. **Monitoring Integration**
- **Health Checks**: Integrates with existing health monitoring system
- **Metrics Collection**: Uses existing Prometheus metrics collection
- **Logging**: Follows existing structured logging patterns

## Deployment Considerations

### Docker Integration
```yaml
# Addition to existing docker-compose.yml
services:
  mts-correlation-analyzer:
    build: .
    command: python -c "
      from src.correlation_analysis.core.correlation_engine import CorrelationEngine;
      import asyncio;
      engine = CorrelationEngine();
      asyncio.run(engine.start_monitoring())
    "
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_PATH=/data/crypto_data.db
      - CORRELATION_CONFIG_PATH=/app/config/correlation_analysis
    volumes:
      - ./data:/data
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - redis
      - mts-enhanced-scheduler
    restart: unless-stopped
```

### Kubernetes Integration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-correlation-analyzer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mts-correlation-analyzer
  template:
    metadata:
      labels:
        app: mts-correlation-analyzer
    spec:
      containers:
      - name: correlation-analyzer
        image: mts-pipeline:v2.3.0
        command: ["python", "-c"]
        args: ["from src.correlation_analysis.core.correlation_engine import CorrelationEngine; import asyncio; engine = CorrelationEngine(); asyncio.run(engine.start_monitoring())"]
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_PATH
          value: "/data/crypto_data.db"
        volumeMounts:
        - name: data-storage
          mountPath: /data
        - name: config-volume
          mountPath: /app/config
        resources:
          requests:
            memory: "256Mi"
            cpu: "150m"
          limits:
            memory: "512Mi"
            cpu: "300m"
```

This correlation analysis module seamlessly integrates with the existing MTS Data Pipeline architecture while providing specialized real-time correlation monitoring, breakdown detection, and comprehensive daily correlation analysis capabilities.