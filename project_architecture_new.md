# MTS Data Pipeline - Technical Architecture

## Executive Summary

The MTS (Multi-Timeframe Signal) Cryptocurrency Data Pipeline is a sophisticated quantitative trading infrastructure that implements a microservices-oriented architecture with event-driven backtesting capabilities. The system integrates multiple data sources, real-time processing, machine learning-based signal generation, and comprehensive risk management to provide a complete trading strategy development and deployment platform.

**Recent Architecture Enhancements (v2.2.0)**: The system now features an **optimized multi-tier scheduling architecture** that reduces API usage by 86% while improving data quality through intelligent collection frequency adaptation. The enhanced pipeline includes automated signal generation, structured JSON alert systems, and comprehensive operational tooling for production deployment.

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            MTS CRYPTOCURRENCY DATA PIPELINE v2.2.0                     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐                │
│  │  MULTI-TIER DATA │    │ ENHANCED SIGNAL  │    │   BACKTESTING    │                │
│  │    INGESTION     │    │     ENGINE       │    │                  │                │
│  │                  │    │                  │    │                  │                │
│  │ • High-Freq Tier │    │ • VIX Strategy   │    │ • Event-Driven  │                │
│  │   (BTC/ETH-15m)  │    │ • Mean Reversion │    │ • Portfolio Mgmt │                │
│  │ • Hourly Tier    │    │ • Multi-Strategy │    │ • Risk Analytics │                │
│  │   (Others-60m)   │    │ • Auto Generator │    │ • Performance    │                │
│  │ • Macro Tier     │    │ • JSON Alerts   │    │ • Optimization   │                │
│  │   (Daily)        │    │ • Aggregation    │    │                  │                │
│  └──────────────────┘    └──────────────────┘    └──────────────────┘                │
│           │                        │                        │                         │
│           ▼                        ▼                        ▼                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     ENHANCED STORAGE & CACHING LAYER                            │  │
│  │                                                                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │   SQLite     │  │    Redis     │  │  JSON Alerts │  │    Logs      │      │  │
│  │  │   Database   │  │    Cache     │  │ & CSV Backups│  │  & Metrics   │      │  │
│  │  │              │  │              │  │              │  │              │      │  │
│  │  │ • OHLCV Data │  │ • RT Signals │  │ • Vol Alerts │  │ • Structured │      │  │
│  │  │ • Macro Data │  │ • Sessions   │  │ • Signal     │  │ • JSON/Text  │      │  │
│  │  │ • Signals    │  │ • Market     │  │   Alerts     │  │ • Tier Logs  │      │  │
│  │  │ • Backtests  │  │ • Cache      │  │ • State Files│  │ • Metrics    │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  └─────────────────────────────────────────────────────────────────────────────────┐  │
│                                          │                                         │  │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                        ENHANCED SERVICES & ORCHESTRATION                       │  │
│  │                                                                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │  │ Multi-Tier   │  │   Monitor    │  │   FastAPI    │  │ Enhanced CLI │      │  │
│  │  │  Scheduler   │  │ & Health     │  │   Server     │  │  & Scripts   │      │  │
│  │  │              │  │              │  │              │  │              │      │  │
│  │  │ • 86% Less   │  │ • Health     │  │ • REST API   │  │ • main.py    │      │  │
│  │  │   API Calls  │  │ • Metrics    │  │ • WebSocket  │  │ • enhanced.py│      │  │
│  │  │ • Tier-based │  │ • Alerts     │  │ • Auth       │  │ • optimized  │      │  │
│  │  │ • Auto Retry │  │ • Dashboard  │  │ • Signals    │  │ • mgmt.sh    │      │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## Core Architectural Patterns

### 1. Layered Architecture

The system implements a clean layered architecture with clear separation of concerns:

**Presentation Layer**
- CLI Interface (`main.py`)
- REST API (`src/api/signal_api.py`)
- Health Monitoring Endpoints

**Application Layer**
- Service Orchestrators (`src/services/`)
- Signal Aggregation (`src/signals/signal_aggregator.py`)
- Scheduling & Automation (`src/services/scheduler.py`)

**Domain Layer**
- Trading Strategies (`src/signals/strategies/`)
- Risk Management Logic
- Business Rules & Validation

**Infrastructure Layer**
- Data Access (`src/data/`)
- External API Clients (`src/api/`)
- Storage & Caching

### 2. Event-Driven Architecture

The backtesting engine implements a pure event-driven architecture:

```python
# Event Flow
MarketEvent → StrategyEvent → SignalEvent → OrderEvent → FillEvent → PortfolioUpdate
```

**Benefits:**
- Temporal decoupling of components
- Easy strategy testing and validation
- Realistic simulation of market conditions
- Pluggable strategy architecture

### 3. Multi-Tier Scheduling Architecture

The system implements an intelligent multi-tier scheduling pattern that optimizes API usage while maintaining data quality:

```python
class AssetTier(Enum):
    HIGH_FREQUENCY = "high_frequency"    # BTC, ETH - 15 minutes
    HOURLY = "hourly"                    # Other cryptos - 60 minutes  
    MACRO = "macro"                      # Macro indicators - daily

class MultiTierScheduler:
    """
    Tier-based collection strategy:
    - High-frequency: Critical assets requiring real-time analysis
    - Hourly: Portfolio assets with sufficient granularity
    - Macro: Economic indicators with slow-changing nature
    """
    
    def __init__(self):
        self.intervals = {
            AssetTier.HIGH_FREQUENCY: 15 * 60,    # 15 minutes
            AssetTier.HOURLY: 60 * 60,            # 60 minutes
            AssetTier.MACRO: 24 * 60 * 60,        # 24 hours
        }
        
        self.asset_tiers = {
            'bitcoin': AssetTier.HIGH_FREQUENCY,
            'ethereum': AssetTier.HIGH_FREQUENCY,
            'tether': AssetTier.HOURLY,
            'solana': AssetTier.HOURLY,
            # ... other assets
        }
```

**Benefits:**
- **86% API usage reduction**: From 2,880 to 393 daily calls
- **Improved data quality**: Higher frequency for critical assets
- **Resource optimization**: Efficient allocation of API rate limits
- **Scalable design**: Easy to add new tiers and assets

### 4. Strategy Pattern Implementation

Trading strategies implement a common interface:

```python
from abc import ABC, abstractmethod

class SignalStrategy(ABC):
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions"""
        pass
        
    @abstractmethod  
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """Generate trading signals"""
        pass
```

## JSON Alert System Architecture

The system implements a sophisticated alert generation and distribution architecture for real-time trading notifications:

### Alert Generation Pipeline

```python
class JSONAlertSystem:
    """
    Centralized alert generation and distribution system
    """
    
    def __init__(self):
        self.alert_storage = AlertStorage('data/alerts/')
        self.notification_manager = NotificationManager()
        
    def generate_volatility_alert(self, asset: str, volatility_data: Dict) -> Dict:
        """Generate structured volatility spike alerts"""
        alert = {
            "timestamp": int(time.time() * 1000),
            "asset": asset,
            "current_price": volatility_data['price'],
            "volatility_value": volatility_data['volatility'],
            "volatility_threshold": volatility_data['threshold'],
            "volatility_percentile": volatility_data['percentile'],
            "position_direction": self._determine_direction(volatility_data),
            "signal_type": "LONG" if volatility_data['oversold'] else "SHORT",
            "alert_type": "volatility_spike",
            "threshold_exceeded": True
        }
        
        return self._store_and_distribute(alert)
    
    def generate_signal_alert(self, signals: List[TradingSignal]) -> Dict:
        """Generate multi-strategy signal confirmation alerts"""
        aggregated_signal = self._aggregate_signals(signals)
        
        alert = {
            "timestamp": int(time.time() * 1000),
            "asset": aggregated_signal.asset,
            "signal_type": aggregated_signal.signal_type.value,
            "confidence": aggregated_signal.confidence,
            "strategies": [s.strategy_name for s in signals],
            "price": aggregated_signal.price,
            "position_size": aggregated_signal.position_size,
            "risk_metrics": {
                "stop_loss": aggregated_signal.stop_loss,
                "take_profit": aggregated_signal.take_profit
            }
        }
        
        return self._store_and_distribute(alert)
```

### Alert Storage Architecture

```python
class AlertStorage:
    """
    File-based alert storage with structured naming
    """
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    def store_alert(self, alert: Dict) -> str:
        """Store alert with timestamped filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{alert['alert_type']}_{alert['asset']}_{timestamp}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, 'w') as f:
            json.dump(alert, f, indent=2)
            
        return str(filepath)
```

### Alert Distribution Patterns

**Push Notification Architecture:**

```python
class NotificationManager:
    """
    Multi-channel alert distribution system
    """
    
    def __init__(self):
        self.channels = {
            'discord': DiscordNotifier(),
            'webhook': WebhookNotifier(),
            'file': FileNotifier(),
            'redis': RedisNotifier()
        }
    
    async def distribute_alert(self, alert: Dict, channels: List[str] = None):
        """Distribute alert across specified channels"""
        channels = channels or ['file', 'redis']  # Default channels
        
        distribution_tasks = []
        for channel_name in channels:
            if channel_name in self.channels:
                notifier = self.channels[channel_name]
                task = notifier.send_alert(alert)
                distribution_tasks.append(task)
        
        # Parallel distribution for performance
        await asyncio.gather(*distribution_tasks, return_exceptions=True)
```

### Integration Architecture

**Trading Bot Integration:**

```python
class AlertConsumer:
    """
    Alert consumption interface for trading systems
    """
    
    async def consume_alerts(self, alert_filter: Dict = None):
        """Consume alerts matching specified criteria"""
        async for alert in self._get_alert_stream():
            if self._matches_filter(alert, alert_filter):
                yield alert
    
    def parse_signal_alert(self, alert: Dict) -> TradingAction:
        """Parse alert into actionable trading instruction"""
        return TradingAction(
            action=alert['signal_type'],
            asset=alert['asset'],
            price=alert['price'],
            quantity=alert['position_size'],
            stop_loss=alert['risk_metrics']['stop_loss'],
            take_profit=alert['risk_metrics']['take_profit']
        )
```

## Data Architecture

### Database Schema Design

**SQLite Production Schema:**

```sql
-- Core Market Data
CREATE TABLE crypto_ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cryptocurrency TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    date_str TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cryptocurrency, timestamp)
);

-- Macro Economic Indicators
CREATE TABLE macro_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL NOT NULL,
    is_interpolated BOOLEAN DEFAULT 0,
    is_forward_filled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(indicator, date)
);

-- Trading Signals
CREATE TABLE signal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    price REAL NOT NULL,
    strategy_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    position_size REAL,
    stop_loss REAL,
    take_profit REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Backtest Results
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    initial_capital REAL NOT NULL,
    final_value REAL NOT NULL,
    total_return REAL NOT NULL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    trade_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Alert History (Optional - currently file-based)
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    asset TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    alert_data TEXT NOT NULL,  -- JSON blob
    file_path TEXT,
    distributed_channels TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Enhanced Data Flow Patterns

**Multi-Tier Data Collection:**
```
Multi-Tier Scheduler → CoinGecko API → Data Validator → SQLite Storage → Strategy Analysis
     │
     ├─ High-Frequency Tier (BTC/ETH): Every 15 minutes
     ├─ Hourly Tier (Others): Every 60 minutes  
     └─ Macro Tier (Economic): Daily
```

**Signal Generation & Alert Flow:**
```
Data Collection → Multi-Strategy Generator → Signal Aggregation → JSON Alerts → Distribution
                       │                                              │
                       ▼                                              ▼
                   SQLite Storage                              File Storage + Notifications
```

**Real-Time Data Processing:**
```
WebSocket Stream → Redis Cache → Signal Generator → JSON Alert System → Multi-Channel Distribution
```

**State Persistence:**
```
Scheduler State → JSON Files → Restart Recovery
Collection Status → Memory + Disk → Health Monitoring
```

### Enhanced Storage Strategy

**Multi-Tier Storage Architecture:**

```python
# Redis Cache Architecture
# Cache Key Patterns
orderbook:{exchange}:{symbol}:{timestamp}
funding:{exchange}:{symbol}:{timestamp}  
signal:{strategy}:{asset}:{timestamp}
market:{symbol}:{timeframe}:{timestamp}
scheduler_status:{tier}:{asset}

# TTL Settings
orderbook_ttl = 3600     # 1 hour
funding_ttl = 86400      # 24 hours  
signal_ttl = 86400       # 24 hours
market_ttl = 1800        # 30 minutes
scheduler_ttl = 300      # 5 minutes
```

**File-Based Storage Patterns:**

```python
# Alert Storage Structure
data/alerts/
├── volatility_alert_bitcoin_20250729_155543.json
├── signal_alert_ethereum_20250729_160012.json
└── correlation_alert_btc_eth_20250729_161245.json

# State Persistence Structure  
data/
├── multi_tier_scheduler_state.json        # Scheduler state
├── enhanced_multi_tier_scheduler_state.json  # Enhanced scheduler state
└── collection_statistics.json             # Performance metrics

# State File Schema
{
  "last_updated": "2025-01-29T16:30:45.123Z",
  "collection_tasks": {
    "bitcoin": {
      "tier": "high_frequency",
      "last_collection": "2025-01-29T16:15:00.000Z",
      "consecutive_failures": 0,
      "success_rate": 0.98
    }
  },
  "performance_metrics": {
    "total_collections_today": 1247,
    "api_calls_used": 387,
    "average_response_time": 0.245
  }
}
```

## Signal Generation Architecture

### Strategy Framework Design

**Base Strategy Interface:**

```python
class SignalStrategy(ABC):
    def __init__(self, config_path: str):
        self.config = self.load_config(config_path)
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load strategy configuration from JSON"""
        
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Market analysis implementation"""
        
    @abstractmethod
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """Signal generation implementation"""
        
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Strategy parameters for optimization"""
```

### Strategy Implementation

**1. VIX Correlation Strategy**

```python
class VIXCorrelationStrategy(SignalStrategy):
    """
    Signal Generation Logic:
    - Calculate rolling correlations between VIX and crypto prices
    - LONG when correlation < -0.6 (strong negative)
    - SHORT when correlation > 0.6 (strong positive)
    - Position sizing based on correlation strength and VIX levels
    """
    
    def analyze(self, market_data):
        # Multi-timeframe correlation analysis
        correlation_windows = [7, 14, 21, 30]
        correlations = {}
        
        for window in correlation_windows:
            rolling_corr = self._calculate_rolling_correlation(window)
            correlations[f'{window}d_correlation'] = rolling_corr
            
        return {
            'correlations_by_window': correlations,
            'current_correlation': correlations['30d_correlation'],
            'signal_opportunities': self._evaluate_opportunities(correlations)
        }
```

**2. Mean Reversion Strategy**

```python
class MeanReversionStrategy(SignalStrategy):
    """
    Signal Generation Logic:
    - Detect VIX spikes (> 25) combined with crypto drawdowns (> 10%)
    - Calculate RSI for oversold conditions
    - Generate LONG signals for mean reversion opportunities
    - Adaptive position sizing based on VIX percentile
    """
    
    def analyze(self, market_data):
        return {
            'vix_spike_detected': current_vix > self.vix_spike_threshold,
            'drawdown_from_high': self._calculate_drawdown(),
            'rsi': self._calculate_rsi(),
            'vix_percentile': self._calculate_vix_percentile()
        }
```

### Enhanced Multi-Strategy Generation

**Automated Multi-Strategy Generator:**

```python
class MultiStrategyGenerator:
    """
    Automated signal generation orchestrator with integrated alert system
    """
    
    def __init__(self):
        self.strategies = self._load_strategies()
        self.signal_aggregator = SignalAggregator()
        self.alert_system = JSONAlertSystem()
        self.risk_manager = RiskManager()
        
    async def generate_signals_for_all_assets(self) -> Dict[str, List[TradingSignal]]:
        """
        Complete signal generation pipeline:
        1. Run all strategies across all assets
        2. Aggregate and resolve conflicts
        3. Apply risk management
        4. Generate alerts for high-confidence signals
        """
        
        all_signals = {}
        strategy_results = {}
        
        # Run all strategies
        for strategy_name, strategy in self.strategies.items():
            logger.info(f"Running strategy: {strategy_name}")
            try:
                market_data = await self._get_market_data()
                analysis = strategy.analyze(market_data)
                signals = strategy.generate_signals(analysis)
                
                strategy_results[strategy_name] = {
                    'signals': signals,
                    'analysis': analysis,
                    'execution_time': time.time()
                }
                
            except Exception as e:
                logger.error(f"Strategy {strategy_name} failed: {e}")
                continue
        
        # Aggregate signals by asset
        for asset in self._get_monitored_assets():
            asset_signals = []
            for strategy_name, results in strategy_results.items():
                asset_specific_signals = [s for s in results['signals'] if s.asset == asset]
                asset_signals.extend(asset_specific_signals)
            
            if asset_signals:
                # Apply aggregation and risk management
                aggregated_signals = self.signal_aggregator.aggregate_signals(asset_signals)
                risk_managed_signals = self.risk_manager.apply_constraints(aggregated_signals)
                
                all_signals[asset] = risk_managed_signals
                
                # Generate alerts for high-confidence signals
                for signal in risk_managed_signals:
                    if signal.confidence >= 0.8:  # High confidence threshold
                        await self.alert_system.generate_signal_alert([signal])
        
        return all_signals
```

**Enhanced Signal Aggregation Engine:**

```python
class SignalAggregator:
    def aggregate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Enhanced Aggregation Logic:
        1. Group signals by asset
        2. Apply confidence-weighted averaging
        3. Resolve conflicts using advanced voting
        4. Apply correlation-based filtering
        5. Generate final position-sized signals with risk metrics
        """
        
        grouped_signals = self._group_by_asset(signals)
        aggregated_signals = []
        
        for asset, asset_signals in grouped_signals.items():
            if len(asset_signals) == 1:
                # Single signal - apply risk management
                final_signal = self._apply_risk_management(asset_signals[0])
                aggregated_signals.append(final_signal)
            else:
                # Multiple signals - sophisticated aggregation
                confidence_weights = [s.confidence for s in asset_signals]
                
                # Weighted consensus
                if self._has_consensus(asset_signals, threshold=0.6):
                    final_signal = self._weighted_average_signal(asset_signals, confidence_weights)
                    final_signal.confidence = self._calculate_consensus_confidence(asset_signals)
                    aggregated_signals.append(final_signal)
                else:
                    # No consensus - apply conflict resolution
                    resolved_signal = self._advanced_conflict_resolution(asset_signals)
                    if resolved_signal and resolved_signal.confidence >= 0.5:
                        aggregated_signals.append(resolved_signal)
                    
        return aggregated_signals
    
    def _advanced_conflict_resolution(self, signals: List[TradingSignal]) -> Optional[TradingSignal]:
        """
        Advanced conflict resolution using:
        - Strategy historical performance
        - Market regime detection
        - Volatility-based weighting
        """
        
        # Strategy performance weighting
        performance_weights = self._get_strategy_performance_weights(signals)
        
        # Market regime adaptation
        current_regime = self._detect_market_regime()
        regime_weights = self._get_regime_weights(signals, current_regime)
        
        # Combined weighting
        final_weights = [p * r * s.confidence for p, r, s in 
                        zip(performance_weights, regime_weights, signals)]
        
        if max(final_weights) > 0.5:  # Minimum confidence threshold
            best_signal_idx = final_weights.index(max(final_weights))
            return signals[best_signal_idx]
        
        return None
```

## Backtesting Engine Architecture

### Event-Driven Framework

**Core Components:**

```python
# Event System
class BaseEvent(ABC):
    def __init__(self, timestamp: datetime, event_type: str):
        self.timestamp = timestamp
        self.event_type = event_type
        self.event_id = uuid.uuid4()

class EventManager:
    def __init__(self):
        self._event_queue = []  # Priority queue by timestamp
        
    def add_event(self, event):
        heapq.heappush(self._event_queue, (event.timestamp, event))
        
    def get_next_event(self):
        return heapq.heappop(self._event_queue)[1]

# State Management
class StateManager:
    def __init__(self):
        self.current_time = None
        self.portfolio_state = {}
        self.current_prices = {}
        
    def update_state(self, event):
        # Update system state based on event
        pass
```

**Event Types:**

1. **MarketEvent**: OHLCV price updates
2. **SignalEvent**: Strategy-generated trading signals  
3. **OrderEvent**: Order placement instructions
4. **FillEvent**: Order execution confirmations

### Portfolio Management

**Position Tracking:**

```python
class Position:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = 0.0
        self.average_cost = 0.0
        self.unrealized_pnl = 0.0
        
    def update_position(self, quantity_change: float, price: float):
        # Handle position updates with proper averaging
        # Support long/short positions and flips
        pass

class PortfolioManager:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.portfolio_values = []
        
    def process_fill(self, fill_event: FillEvent):
        # Update positions and cash based on fills
        # Calculate commissions and slippage
        # Track portfolio value over time
        pass
```

### Performance Analytics

**Metrics Calculation:**

```python
class PerformanceCalculator:
    def calculate_metrics(self, portfolio_values: List[float]) -> Dict[str, float]:
        returns = self._calculate_returns(portfolio_values)
        
        return {
            'total_return': self._total_return(portfolio_values),
            'annualized_return': self._annualized_return(returns),
            'sharpe_ratio': self._sharpe_ratio(returns),
            'max_drawdown': self._max_drawdown(portfolio_values),
            'volatility': self._volatility(returns),
            'calmar_ratio': self._calmar_ratio(returns),
            'win_rate': self._win_rate(self.trades),
            'profit_factor': self._profit_factor(self.trades)
        }
```

## API & Integration Architecture

### REST API Design

**FastAPI Server Structure:**

```python
from fastapi import FastAPI, HTTPServer, Depends
from pydantic import BaseModel

app = FastAPI(title="MTS Signal API", version="1.0.0")

# Request/Response Models
class SignalRequest(BaseModel):
    strategy_name: str
    symbols: List[str]
    timeframe: str = "1d"

class SignalResponse(BaseModel):
    signals: List[TradingSignal]
    timestamp: int
    metadata: Dict[str, Any]

# Endpoints
@app.post("/signals/generate", response_model=SignalResponse)
async def generate_signals(request: SignalRequest):
    """Generate trading signals for specified strategy and symbols"""
    
@app.post("/backtest", response_model=BacktestResponse)  
async def run_backtest(request: BacktestRequest):
    """Run strategy backtest with specified parameters"""
    
@app.get("/health")
async def health_check():
    """System health and status endpoint"""
```

### WebSocket Architecture

**Real-Time Data Streams:**

```python
class BaseWebSocket:
    async def connect(self):
        """Establish WebSocket connection with reconnection logic"""
        
    async def subscribe(self, channels: List[str]):
        """Subscribe to specific data channels"""
        
    async def handle_message(self, message: dict):
        """Process incoming WebSocket messages"""

class BinanceWebSocket(BaseWebSocket):
    """Binance-specific WebSocket implementation"""
    
class BybitWebSocket(BaseWebSocket):  
    """Bybit-specific WebSocket implementation"""
```

## Configuration Management

### Environment-Based Configuration

**Configuration Hierarchy:**

```python
class Config:
    def __init__(self):
        # Load from environment variables with defaults
        self.ENVIRONMENT = Environment(os.getenv('ENVIRONMENT', 'development'))
        
        # API Configuration
        self.COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
        self.FRED_API_KEY = os.getenv('FRED_API_KEY', '')
        
        # Database Configuration  
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/crypto_data.db')
        
        # Strategy Configuration
        self.ENABLED_STRATEGIES = self._parse_list(
            os.getenv('ENABLED_STRATEGIES', 'vix_correlation,mean_reversion')
        )
        
        # Risk Management
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '0.10'))
        self.MAX_PORTFOLIO_RISK = float(os.getenv('MAX_PORTFOLIO_RISK', '0.25'))
```

### Multi-Tier Collection Configuration

**Optimized Collection Strategy** (`config/optimized_collection.json`):

```json
{
  "collection_strategy": {
    "description": "Multi-tier collection strategy optimized for minimal API usage",
    "total_daily_api_calls_estimate": 393,
    "api_cost_reduction_percent": 86,
    "tiers": {
      "high_frequency": {
        "description": "Critical assets requiring frequent updates",
        "interval_minutes": 15,
        "daily_collections_per_asset": 96,
        "assets": ["bitcoin", "ethereum"],
        "rationale": "BTC and ETH are primary trading pairs requiring real-time analysis"
      },
      "hourly": {
        "description": "Standard crypto assets updated hourly",
        "interval_minutes": 60,
        "daily_collections_per_asset": 24,
        "assets": ["tether", "solana", "ripple", "bittensor", "fetch-ai", 
                  "singularitynet", "render-token", "ocean-protocol"],
        "rationale": "Hourly updates provide good balance for portfolio signals"
      },
      "macro": {
        "description": "Macro economic indicators updated daily",
        "interval_hours": 24,
        "daily_collections_per_indicator": 1,
        "indicators": ["VIXCLS", "DFF", "DGS10", "DTWEXBGS", "DEXUSEU", 
                      "DEXCHUS", "BAMLH0A0HYM2", "RRPONTSYD", "SOFR"],
        "rationale": "Macro indicators change slowly, daily updates sufficient"
      }
    }
  },
  "api_optimization": {
    "rate_limit_compliance": {
      "coingecko": {
        "limit_per_minute": 50,
        "our_usage_peak": 10,
        "utilization_percent": 20,
        "fallback_strategy": "Automatic Pro/Free API switching"
      },
      "fred": {
        "limit_per_hour": 1000,
        "our_usage_per_hour": 1,
        "utilization_percent": 0.1,
        "notes": "Extremely low utilization with daily collection"
      }
    },
    "performance_monitoring": {
      "health_checks": {
        "data_freshness": "Monitor last successful collection per asset",
        "api_response_times": "Track latency and failure rates",
        "storage_health": "Monitor database performance"
      },
      "alerts": {
        "consecutive_failures": 3,
        "stale_data_threshold_hours": 25,
        "api_error_rate_threshold": 10
      }
    }
  }
}
```

### Strategy Configuration

**JSON-Based Strategy Configs:**

```json
// config/strategies/vix_correlation.json
{
  "name": "VIX_Correlation_Strategy",
  "assets": ["bitcoin", "ethereum", "binancecoin"],
  "correlation_thresholds": {
    "strong_negative": -0.6,
    "strong_positive": 0.6
  },
  "lookback_days": 30,
  "position_size": 0.02,
  "risk_management": {
    "max_position_size": 0.05,
    "stop_loss_pct": 0.05,
    "take_profit_pct": 0.10
  }
}
```

## Operational Tools & Automation Architecture

The system includes comprehensive operational tooling for production deployment and maintenance:

### Pipeline Management System

**Shell-Based Service Management** (`scripts/start_optimized_pipeline.sh`):

```bash
#!/bin/bash
# Complete pipeline lifecycle management

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
PID_FILE="$PROJECT_ROOT/data/optimized_pipeline.pid"
LOG_FILE="$PROJECT_ROOT/logs/optimized_pipeline.log"

case "$1" in
    start)
        start_pipeline
        ;;
    stop)
        stop_pipeline
        ;;
    status)
        show_detailed_status
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    test)
        validate_configuration
        ;;
    restart)
        stop_pipeline
        sleep 5
        start_pipeline
        ;;
esac

start_pipeline() {
    # Validate configuration
    if ! python3 main_optimized.py --test; then
        echo "❌ Configuration validation failed"
        exit 1
    fi
    
    # Start background process
    nohup python3 main_enhanced.py --background > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    echo "🚀 Pipeline started with PID $(cat $PID_FILE)"
    echo "📊 Estimated daily API usage: 393 calls (86% reduction)"
    echo "📋 Monitor with: $0 status"
}
```

**Features:**
- **Process Management**: PID tracking and lifecycle control
- **Configuration Validation**: Pre-flight checks before startup
- **Log Management**: Centralized logging with real-time viewing
- **Status Monitoring**: Detailed operational status reporting
- **Safe Restart**: Graceful shutdown and restart procedures

### Alert Generation Utilities

**Volatility Alert Generator** (`generate_real_volatility_alerts.py`):

```python
class AlertGenerator:
    """
    Utility for generating realistic test alerts based on market data
    """
    
    def __init__(self):
        self.alert_system = JSONAlertSystem()
        self.market_data = self._load_recent_market_data()
        
    def generate_realistic_alerts(self, count: int = 5) -> List[str]:
        """Generate alerts with realistic market conditions"""
        
        alert_scenarios = [
            {
                'asset': 'bitcoin',
                'scenario': 'volatility_spike',
                'volatility': 0.042,  # 4.2% - high volatility
                'percentile': 94.2,
                'signal_type': 'LONG'
            },
            {
                'asset': 'ethereum', 
                'scenario': 'correlation_signal',
                'vix_correlation': -0.72,  # Strong negative correlation
                'confidence': 0.89,
                'signal_type': 'LONG'
            }
        ]
        
        generated_files = []
        for scenario in alert_scenarios[:count]:
            alert_file = self._generate_scenario_alert(scenario)
            generated_files.append(alert_file)
            
        return generated_files
    
    def _generate_scenario_alert(self, scenario: Dict) -> str:
        """Generate specific scenario-based alert"""
        
        timestamp = int(time.time() * 1000)
        current_price = self._get_current_price(scenario['asset'])
        
        if scenario['scenario'] == 'volatility_spike':
            alert = self.alert_system.generate_volatility_alert(
                asset=scenario['asset'],
                current_price=current_price,
                volatility_value=scenario['volatility'],
                volatility_percentile=scenario['percentile']
            )
        
        return alert['file_path']
```

### Data Management Utilities

**Data Backfill System:**

```python
class DataBackfillManager:
    """
    Automated data backfill and recovery system
    """
    
    def __init__(self):
        self.collector = DataCollector()
        self.validator = DataValidator()
        
    async def backfill_missing_data(self, 
                                   assets: List[str] = None,
                                   date_range: Tuple[datetime, datetime] = None) -> Dict:
        """
        Comprehensive data backfill with gap detection
        """
        
        assets = assets or self._get_monitored_assets()
        date_range = date_range or self._detect_missing_date_range()
        
        backfill_results = {
            'successful': [],
            'failed': [],
            'gaps_filled': 0,
            'total_data_points': 0
        }
        
        for asset in assets:
            try:
                # Detect data gaps
                gaps = self._detect_data_gaps(asset, date_range)
                
                for gap_start, gap_end in gaps:
                    # Backfill gap
                    data_points = await self.collector.collect_historical_data(
                        asset, gap_start, gap_end
                    )
                    
                    # Validate and store
                    validated_data = self.validator.validate_data_points(data_points)
                    self._store_backfilled_data(asset, validated_data)
                    
                    backfill_results['gaps_filled'] += 1
                    backfill_results['total_data_points'] += len(validated_data)
                
                backfill_results['successful'].append(asset)
                
            except Exception as e:
                logger.error(f"Backfill failed for {asset}: {e}")
                backfill_results['failed'].append({
                    'asset': asset,
                    'error': str(e)
                })
        
        return backfill_results
```

### System Health & Diagnostics

**Enhanced Health Monitoring:**

```python
class SystemDiagnostics:
    """
    Comprehensive system health and performance diagnostics
    """
    
    def __init__(self):
        self.health_checker = HealthChecker()
        self.performance_monitor = PerformanceMonitor()
        
    async def run_comprehensive_diagnostics(self) -> Dict:
        """Complete system health assessment"""
        
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'system_health': await self._system_health_check(),
            'api_performance': await self._api_performance_check(),
            'data_quality': await self._data_quality_check(),
            'scheduler_status': await self._scheduler_status_check(),
            'alert_system': await self._alert_system_check(),
            'recommendations': []
        }
        
        # Generate recommendations based on diagnostics
        diagnostics['recommendations'] = self._generate_recommendations(diagnostics)
        
        return diagnostics
    
    async def _scheduler_status_check(self) -> Dict:
        """Multi-tier scheduler specific health checks"""
        
        scheduler_status = {
            'state_file_health': self._check_state_files(),
            'collection_performance': self._analyze_collection_performance(),
            'tier_balance': self._analyze_tier_balance(),
            'api_usage': self._analyze_api_usage(),
            'failure_rates': self._analyze_failure_rates()
        }
        
        return scheduler_status
```

## Error Handling & Resilience

### Exception Hierarchy

```python
class CryptoDataPipelineError(Exception):
    """Base exception for the pipeline"""
    
class APIError(CryptoDataPipelineError):
    """API-related errors"""
    
class APIRateLimitError(APIError):
    """Rate limiting errors"""
    
class DataValidationError(CryptoDataPipelineError):
    """Data validation errors"""
    
class BacktestingError(CryptoDataPipelineError):
    """Backtesting-specific errors"""
```

### Retry & Circuit Breaker Patterns

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(url: str) -> dict:
    """Fetch data with exponential backoff retry"""
    
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

## Security Architecture

### API Security

**Authentication & Authorization:**

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Rate Limiting:**

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/signals/generate")
@limiter.limit("10/minute")
async def generate_signals(request: Request, signal_request: SignalRequest):
    """Rate-limited signal generation endpoint"""
```

### Data Security

**Input Validation:**

```python
from pydantic import BaseModel, validator

class TradingSignal(BaseModel):
    asset: str
    signal_type: SignalType
    price: float
    confidence: float
    
    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
        
    @validator('confidence')
    def confidence_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v
```

## Monitoring & Observability

### Health Monitoring

**Health Check System:**

```python
class HealthChecker:
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'redis': self._check_redis,
            'external_apis': self._check_external_apis,
            'disk_space': self._check_disk_space
        }
    
    async def run_health_checks(self) -> Dict[str, bool]:
        results = {}
        for check_name, check_func in self.checks.items():
            try:
                results[check_name] = await check_func()
            except Exception:
                results[check_name] = False
        return results
```

### Enhanced Monitoring & Observability

**Multi-Tier Pipeline Monitoring:**

```python
class EnhancedMonitoringSystem:
    """
    Comprehensive monitoring for multi-tier pipeline operations
    """
    
    def __init__(self):
        self.scheduler_metrics = SchedulerMetrics()
        self.alert_metrics = AlertMetrics()
        self.api_metrics = APIMetrics()
        
    def collect_scheduler_metrics(self) -> Dict:
        """Collect multi-tier scheduler performance metrics"""
        
        return {
            'tier_performance': {
                'high_frequency': {
                    'success_rate': self._calculate_tier_success_rate('high_frequency'),
                    'avg_response_time': self._calculate_avg_response_time('high_frequency'),
                    'api_calls_today': self._count_api_calls('high_frequency'),
                    'next_collection_times': self._get_next_collection_times('high_frequency')
                },
                'hourly': {
                    'success_rate': self._calculate_tier_success_rate('hourly'),
                    'avg_response_time': self._calculate_avg_response_time('hourly'),
                    'api_calls_today': self._count_api_calls('hourly'),
                    'collections_completed': self._count_completed_collections('hourly')
                },
                'macro': {
                    'success_rate': self._calculate_tier_success_rate('macro'),
                    'last_successful_collection': self._get_last_successful('macro'),
                    'indicators_updated': self._count_updated_indicators()
                }
            },
            'optimization_metrics': {
                'daily_api_usage': self._calculate_daily_api_usage(),
                'reduction_achieved': self._calculate_reduction_percentage(),
                'rate_limit_utilization': self._calculate_rate_limit_usage(),
                'cost_savings': self._estimate_cost_savings()
            }
        }
    
    def collect_alert_metrics(self) -> Dict:
        """Monitor alert system performance"""
        
        return {
            'alert_generation': {
                'volatility_alerts_today': self._count_alerts('volatility'),
                'signal_alerts_today': self._count_alerts('signal'),
                'high_confidence_alerts': self._count_high_confidence_alerts(),
                'avg_generation_time': self._calculate_avg_alert_time()
            },
            'distribution_metrics': {
                'successful_distributions': self._count_successful_distributions(),
                'failed_distributions': self._count_failed_distributions(),
                'channel_performance': self._analyze_channel_performance()
            },
            'alert_quality': {
                'accuracy_rate': self._calculate_alert_accuracy(),
                'false_positive_rate': self._calculate_false_positive_rate(),
                'response_time': self._calculate_alert_response_time()
            }
        }
```

**Structured Logging with Multi-Tier Context:**

```python
import structlog

# Enhanced structured logging configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage with multi-tier context
logger = structlog.get_logger(__name__)

# Scheduler logging
logger.info("Multi-tier collection completed", 
           tier="high_frequency",
           asset="bitcoin", 
           duration=0.245,
           api_calls_used=2,
           success=True,
           next_collection="2025-01-30T16:30:00Z")

# Alert logging
logger.info("Alert generated and distributed", 
           alert_type="volatility_spike",
           asset="ethereum",
           confidence=0.89,
           channels=["file", "discord"],
           generation_time=0.012)

# Signal logging
logger.info("Multi-strategy signal generated", 
           asset="bitcoin", 
           signal_type="LONG", 
           confidence=0.85,
           strategies=["vix_correlation", "mean_reversion"],
           aggregation_method="weighted_consensus")
```

### Metrics Collection

**Prometheus Metrics:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
signal_generation_counter = Counter('signals_generated_total', 'Total signals generated', ['strategy', 'asset'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')
portfolio_value_gauge = Gauge('portfolio_value_usd', 'Current portfolio value in USD')

# Usage in code
signal_generation_counter.labels(strategy='vix_correlation', asset='bitcoin').inc()
portfolio_value_gauge.set(current_portfolio_value)
```

## Scalability Considerations

### Horizontal Scaling Patterns

**Microservices Decomposition:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Ingestion │    │ Signal Generator│    │ Backtest Engine │
│   Service       │    │    Service      │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Message Queue (Redis/RabbitMQ)              │
└─────────────────────────────────────────────────────────────────┘
```

**Database Scaling:**

- Read replicas for analytical queries
- Partitioning by time/symbol for large datasets  
- Caching layer for frequently accessed data
- Archive old data to reduce active dataset size

**Caching Strategy:**

```python
# Multi-level caching
L1_CACHE = {}  # In-memory cache
L2_CACHE = redis_client  # Redis cache  
L3_CACHE = database  # Persistent storage

async def get_market_data(symbol: str, date: str):
    # Try L1 cache first
    cache_key = f"{symbol}:{date}"
    if cache_key in L1_CACHE:
        return L1_CACHE[cache_key]
    
    # Try L2 cache
    data = await L2_CACHE.get(cache_key)
    if data:
        L1_CACHE[cache_key] = data
        return data
    
    # Fallback to database
    data = await L3_CACHE.get_market_data(symbol, date)
    if data:
        await L2_CACHE.set(cache_key, data, ttl=3600)
        L1_CACHE[cache_key] = data
    
    return data
```

## Deployment Architecture

### Containerization

**Docker Configuration:**

```dockerfile
# Multi-stage build for production
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.api.signal_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Enhanced Docker Compose:**

```yaml
version: '3.8'
services:
  # Main API Service
  mts-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_PATH=/data/crypto_data.db
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - FRED_API_KEY=${FRED_API_KEY}
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    depends_on:
      - redis
      
  # Enhanced Multi-Tier Scheduler with Signal Generation
  mts-enhanced-scheduler:
    build: .
    command: python main_enhanced.py --background
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_PATH=/data/crypto_data.db
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - FRED_API_KEY=${FRED_API_KEY}
      - ENABLE_SIGNALS=true
      - ENABLE_ALERTS=true
    volumes:
      - ./data:/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
      
  # Optimized Data Collection Only
  mts-data-collector:
    build: .
    command: python main_optimized.py --background
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_PATH=/data/crypto_data.db
      - COINGECKO_API_KEY=${COINGECKO_API_KEY}
      - FRED_API_KEY=${FRED_API_KEY}
    volumes:
      - ./data:/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    profiles:
      - data-only
      
  # Health Monitoring Service
  mts-monitor:
    build: .
    command: python -c "
      from src.services.monitor import HealthChecker;
      import asyncio;
      asyncio.run(HealthChecker().start_monitoring_server())
    "
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_PATH=/data/crypto_data.db
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    depends_on:
      - redis
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Service Profiles:**

```bash
# Start full enhanced pipeline (recommended)
docker-compose up -d mts-api mts-enhanced-scheduler mts-monitor redis

# Start data collection only
docker-compose --profile data-only up -d mts-data-collector mts-monitor redis

# Start API server only (external scheduler)
docker-compose up -d mts-api redis
```

### Kubernetes Deployment

**Enhanced Production Deployment:**

```yaml
# Enhanced Multi-Tier Scheduler Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-enhanced-scheduler
  labels:
    app: mts-enhanced-scheduler
    version: v2.2.0
spec:
  replicas: 1  # Single instance for state consistency
  selector:
    matchLabels:
      app: mts-enhanced-scheduler
  template:
    metadata:
      labels:
        app: mts-enhanced-scheduler
    spec:
      containers:
      - name: scheduler
        image: mts-pipeline:v2.2.0
        command: ["python", "main_enhanced.py", "--background"]
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_PATH
          value: "/data/crypto_data.db"
        - name: COINGECKO_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: coingecko-api-key
        - name: FRED_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: fred-api-key
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
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from src.services.monitor import HealthChecker; exit(0 if HealthChecker().check_scheduler_health() else 1)"
          initialDelaySeconds: 60
          periodSeconds: 300
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: mts-data-pvc
      - name: config-volume
        configMap:
          name: mts-config
---
# API Service Deployment  
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-signal-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mts-signal-api
  template:
    metadata:
      labels:
        app: mts-signal-api
    spec:
      containers:
      - name: api
        image: mts-pipeline:v2.2.0
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_PATH
          value: "/data/crypto_data.db"
        volumeMounts:
        - name: data-storage
          mountPath: /data
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: mts-data-pvc
---
# Monitoring Service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mts-monitor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mts-monitor
  template:
    metadata:
      labels:
        app: mts-monitor
    spec:
      containers:
      - name: monitor
        image: mts-pipeline:v2.2.0
        command: ["python", "-c"]
        args: ["from src.services.monitor import HealthChecker; import asyncio; asyncio.run(HealthChecker().start_monitoring_server())"]
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        volumeMounts:
        - name: data-storage
          mountPath: /data
          readOnly: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: mts-data-pvc
---
# Services
apiVersion: v1
kind: Service
metadata:
  name: mts-api-service
spec:
  selector:
    app: mts-signal-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: v1
kind: Service
metadata:
  name: mts-monitor-service
spec:
  selector:
    app: mts-monitor
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## Future Architecture Enhancements

### Planned Improvements

**1. Event Sourcing**
- Implement event sourcing for audit trails
- Replay capabilities for backtesting
- Better error recovery and debugging

**2. Machine Learning Pipeline**
- MLflow for model lifecycle management
- Feature store for consistent feature engineering
- A/B testing framework for strategy comparison

**3. Real-Time Stream Processing**
- Apache Kafka for high-throughput messaging
- Stream processing with Apache Flink
- Complex event processing for multi-asset signals

**4. Advanced Analytics**
- Time-series forecasting models
- Anomaly detection for market regime changes
- Portfolio optimization using modern portfolio theory

## Conclusion

The MTS Data Pipeline architecture (v2.2.0) provides a robust, scalable foundation for cryptocurrency trading strategy development with significant operational optimizations. The enhanced multi-tier scheduling system, automated signal generation, and comprehensive alert infrastructure demonstrate a mature evolution toward production-ready quantitative trading systems.

### Key Architectural Strengths:

**Optimization & Efficiency:**
- **86% API usage reduction** through intelligent multi-tier scheduling
- **Improved data quality** with higher frequency collection for critical assets
- **Resource optimization** with tier-based collection strategies
- **Cost-effective scaling** with configurable collection intervals

**Operational Excellence:**
- **Production-ready tooling** with comprehensive pipeline management scripts
- **Automated monitoring** with multi-tier performance metrics
- **State persistence** for reliable restart and recovery capabilities
- **Health diagnostics** with predictive maintenance capabilities

**Signal Generation & Alerting:**
- **Multi-strategy orchestration** with automated conflict resolution  
- **Structured alert system** with JSON-based notifications
- **Integration-ready architecture** for trading bot connections
- **Real-time distribution** across multiple notification channels

**Architecture Patterns:**
- **Modularity**: Clear separation between collection, signals, and alerts
- **Scalability**: Event-driven patterns with horizontal scaling support
- **Reliability**: Comprehensive error handling and automatic recovery
- **Extensibility**: Plugin architecture for strategies, data sources, and alerts
- **Performance**: Multi-level caching and optimized scheduling algorithms

### Evolution & Future-Proofing:

The architecture demonstrates successful evolution from a basic data collection system to a comprehensive trading infrastructure platform. The multi-tier approach provides a foundation for:

- **Adaptive scaling** based on market conditions and data requirements
- **Strategy diversification** with pluggable signal generation modules
- **Operational automation** reducing manual intervention requirements
- **Cost optimization** through intelligent resource allocation

The enhanced architecture maintains backward compatibility while providing significant operational improvements, positioning the system for continued evolution toward advanced quantitative trading capabilities. 