# MTS Data Pipeline - Enhanced Real-Time Market Data Architecture

## 🎯 Project Overview Enhancement

The **Enhanced MTS Data Pipeline** extends the existing cryptocurrency and macro-economic data collection system to include **real-time market microstructure data** from major exchanges. This enhancement adds bid-ask spreads, order book depth, and perpetual funding rates for comprehensive market analysis and advanced trading signal generation.

### New Capabilities Added
- **Real-Time Order Book Data**: 10+ levels of bid/ask depth from Binance and Bybit
- **Bid-Ask Spread Monitoring**: Real-time spread calculation and historical tracking
- **Perpetual Funding Rates**: Funding rate collection and analysis for BTC/ETH perpetuals
- **Multi-Exchange Integration**: Unified data collection from Binance and Bybit APIs
- **WebSocket Streaming**: Real-time data feeds with automatic reconnection
- **Market Microstructure Analysis**: Advanced market structure indicators
- **Cross-Exchange Arbitrage Signals**: Spread and funding rate arbitrage opportunities

---

## 🏗️ Enhanced Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    Enhanced MTS Data Pipeline + Real-Time Market Data           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Entry Points: main.py | production_main.py | Signal API | Real-Time Streams   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Services Layer                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Collector   │ │MacroCollect.│ │ Real-Time   │ │ Order Book  │ │ Funding     ││
│  │ Service     │ │ Service     │ │ Stream Mgr  │ │ Collector   │ │ Rate Coll.  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Scheduler   │ │ Monitor     │ │ Multi-      │ │ Market      │ │ Arbitrage   ││
│  │ Service     │ │ Service     │ │ Strategy    │ │ Structure   │ │ Signal Gen  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Real-Time Data Layer                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ WebSocket   │ │ Order Book  │ │ Spread      │ │ Funding     │ │ Stream      ││
│  │ Manager     │ │ Processor   │ │ Calculator  │ │ Rate Proc.  │ │ Aggregator  ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Exchange API Layer                                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Binance     │ │ Bybit       │ │ WebSocket   │ │ Rate        │ │ Signal API  ││
│  │ Client      │ │ Client      │ │ Handlers    │ │ Limiter     │ │ (FastAPI)   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Enhanced Data Layer                                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ SQLite      │ │ Redis       │ │ Order Book  │ │ Funding     │ │ Market      ││
│  │ Database    │ │ Cache       │ │ Storage     │ │ Rate Store  │ │ Data Models ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ SQLite DB   │    │ Redis Cache │    │ Real-Time   │    │ Signal JSON │
   │ Enhanced    │    │ Order Books │    │ Streams     │    │ Enhanced    │
   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📁 Enhanced Directory Structure

```
MTS-data-pipeline/
├── 📁 config/                           # Configuration management
│   ├── __init__.py
│   ├── settings.py                      # Core application settings
│   ├── logging_config.py                # Logging configuration
│   ├── macro_settings.py                # Macro data collection settings
│   ├── 📁 exchanges/                    # 🆕 Exchange configurations
│   │   ├── __init__.py
│   │   ├── binance_config.py            # 🆕 Binance API configuration
│   │   ├── bybit_config.py              # 🆕 Bybit API configuration
│   │   └── websocket_config.py          # 🆕 WebSocket connection settings
│   ├── 📁 realtime/                     # 🆕 Real-time data configurations
│   │   ├── __init__.py
│   │   ├── orderbook_config.py          # 🆕 Order book collection settings
│   │   ├── funding_config.py            # 🆕 Funding rate settings
│   │   └── stream_config.py             # 🆕 Stream management settings
│   └── 📁 strategies/                   # Strategy configurations
│       ├── vix_correlation.json         # VIX correlation strategy config
│       ├── mean_reversion.json          # Mean reversion strategy config
│       ├── spread_arbitrage.json        # 🆕 Spread arbitrage strategy
│       └── funding_arbitrage.json       # 🆕 Funding rate arbitrage strategy
├── 📁 src/                              # Source code
│   ├── __init__.py
│   ├── 📁 api/                          # External API clients
│   │   ├── __init__.py
│   │   ├── coingecko_client.py          # CoinGecko API wrapper
│   │   ├── fred_client.py               # FRED API wrapper
│   │   ├── signal_api.py                # FastAPI signal generation endpoint
│   │   ├── binance_client.py            # 🆕 Binance API client
│   │   ├── bybit_client.py              # 🆕 Bybit API client
│   │   └── 📁 websockets/               # 🆕 WebSocket implementations
│   │       ├── __init__.py
│   │       ├── base_websocket.py        # 🆕 Base WebSocket handler
│   │       ├── binance_websocket.py     # 🆕 Binance WebSocket client
│   │       ├── bybit_websocket.py       # 🆕 Bybit WebSocket client
│   │       └── stream_manager.py        # 🆕 Multi-stream management
│   ├── 📁 data/                         # Data management layer
│   │   ├── __init__.py
│   │   ├── db_connection.py             # Database connection handling
│   │   ├── db_init.py                   # Database initialization
│   │   ├── models.py                    # Data models (Cryptocurrency, OHLCVData)
│   │   ├── macro_models.py              # Macro data models
│   │   ├── signal_models.py             # Signal data models
│   │   ├── realtime_models.py           # 🆕 Real-time data models
│   │   ├── orderbook_models.py          # 🆕 Order book data models
│   │   ├── funding_models.py            # 🆕 Funding rate data models
│   │   ├── schema.sql                   # Database schema definition
│   │   ├── enhanced_schema.sql          # 🆕 Enhanced schema with real-time tables
│   │   ├── sqlite_helper.py             # High-level database operations
│   │   ├── redis_helper.py              # 🆕 Redis operations for real-time data
│   │   ├── storage.py                   # CSV storage operations
│   │   └── validator.py                 # Data validation logic
│   ├── 📁 services/                     # Business logic services
│   │   ├── __init__.py
│   │   ├── collector.py                 # Main crypto data collection
│   │   ├── macro_collector.py           # Macro data collection
│   │   ├── monitor.py                   # Health monitoring
│   │   ├── scheduler.py                 # Task scheduling
│   │   ├── multi_strategy_generator.py  # Multi-strategy signal generation
│   │   ├── realtime_collector.py        # 🆕 Real-time data collection orchestrator
│   │   ├── orderbook_collector.py       # 🆕 Order book data collection
│   │   ├── funding_collector.py         # 🆕 Funding rate collection
│   │   ├── spread_calculator.py         # 🆕 Bid-ask spread calculations
│   │   └── stream_coordinator.py        # 🆕 WebSocket stream coordination
│   ├── 📁 signals/                      # Signal generation module
│   │   ├── __init__.py
│   │   ├── backtest_interface.py        # Backtesting interface
│   │   ├── signal_aggregator.py         # Signal aggregation and conflict resolution
│   │   └── 📁 strategies/               # Strategy implementations
│   │       ├── __init__.py
│   │       ├── base_strategy.py         # Abstract base strategy class
│   │       ├── strategy_registry.py     # Strategy registration system
│   │       ├── vix_correlation_strategy.py # VIX correlation strategy
│   │       ├── mean_reversion_strategy.py # Mean reversion strategy
│   │       ├── spread_arbitrage_strategy.py # 🆕 Cross-exchange spread arbitrage
│   │       ├── funding_arbitrage_strategy.py # 🆕 Funding rate arbitrage
│   │       └── market_structure_strategy.py # 🆕 Order book analysis strategy
│   ├── 📁 realtime/                     # 🆕 Real-time data processing
│   │   ├── __init__.py
│   │   ├── orderbook_processor.py       # 🆕 Order book data processing
│   │   ├── funding_processor.py         # 🆕 Funding rate processing
│   │   ├── spread_analyzer.py           # 🆕 Spread analysis and monitoring
│   │   ├── market_structure_analyzer.py # 🆕 Market microstructure analysis
│   │   └── arbitrage_detector.py        # 🆕 Cross-exchange arbitrage detection
│   └── 📁 utils/                        # Utility functions
│       ├── __init__.py
│       ├── exceptions.py                # Custom exception classes
│       ├── retry.py                     # Retry logic with backoff
│       ├── websocket_utils.py           # 🆕 WebSocket utility functions
│       └── exchange_utils.py            # 🆕 Exchange-specific utilities
├── 📁 data/                             # Data storage
│   ├── 📁 backup/                       # CSV backup files
│   ├── 📁 raw/                          # Raw CSV data
│   │   ├── 📁 macro/                    # Macro indicator CSV files
│   │   ├── 📁 orderbooks/               # 🆕 Order book snapshots
│   │   ├── 📁 funding/                  # 🆕 Funding rate history
│   │   └── 📁 spreads/                  # 🆕 Spread analysis data
│   ├── 📁 realtime/                     # 🆕 Real-time data cache
│   │   ├── 📁 binance/                  # 🆕 Binance real-time data
│   │   └── 📁 bybit/                    # 🆕 Bybit real-time data
│   └── crypto_data.db                   # SQLite database (enhanced)
├── 📁 examples/                         # Usage examples
│   ├── sqlite_analysis.py               # Database analysis examples
│   ├── realtime_analysis.py             # 🆕 Real-time data analysis examples
│   ├── orderbook_analysis.py            # 🆕 Order book analysis examples
│   └── arbitrage_analysis.py            # 🆕 Arbitrage opportunity analysis
├── 📁 scripts/                          # Utility scripts
│   ├── migrate_csv_to_sqlite.py         # Migration utilities
│   ├── setup_realtime.py                # 🆕 Real-time system setup
│   └── stream_monitor.py                # 🆕 Stream health monitoring
├── 📁 tests/                            # Test suite
│   ├── test_collector.py                # Existing collector tests
│   ├── test_realtime_collector.py       # 🆕 Real-time collector tests
│   ├── test_websockets.py               # 🆕 WebSocket connection tests
│   ├── test_orderbook_processor.py      # 🆕 Order book processing tests
│   ├── test_funding_collector.py        # 🆕 Funding rate tests
│   └── test_arbitrage_strategies.py     # 🆕 Arbitrage strategy tests
├── 📁 logs/                             # Application logs
│   ├── 📁 streams/                      # 🆕 WebSocket stream logs
│   └── 📁 realtime/                     # 🆕 Real-time processing logs
├── main.py                              # Main application entry point
├── production_main.py                   # Production orchestrator
├── realtime_main.py                     # 🆕 Real-time data collection entry point
├── docker-compose.yml                   # Production deployment configuration (enhanced)
├── docker-compose.realtime.yml          # 🆕 Real-time services deployment
├── Dockerfile                           # Production container image (enhanced)
├── requirements.txt                     # Python dependencies (enhanced)
├── requirements.realtime.txt            # 🆕 Additional real-time dependencies
├── schedule_data.sh                     # Crypto data collection script
├── collect_macro.sh                     # Macro data collection script
├── start_realtime.sh                    # 🆕 Real-time data collection script
├── monitor_streams.sh                   # 🆕 Stream monitoring script
├── PRODUCTION.md                        # Production deployment guide (updated)
├── REALTIME.md                          # 🆕 Real-time system documentation
└── README.md                            # Project documentation (updated)
```

---

## 🧩 Enhanced Core Components

### 1. **New Entry Points**

#### `realtime_main.py` - Real-Time Data Collection Entry Point
```python
# Key functions:
python3 realtime_main.py --start-streams              # Start all WebSocket streams
python3 realtime_main.py --exchanges binance,bybit    # Specific exchanges
python3 realtime_main.py --symbols BTC,ETH            # Specific symbols
python3 realtime_main.py --monitor-only               # Stream monitoring only
python3 realtime_main.py --funding-only               # Funding rates only
```

#### Enhanced `production_main.py`
```python
# New production modes:
python3 production_main.py --mode realtime-full       # Full real-time pipeline
python3 production_main.py --mode streams-only        # WebSocket streams only
python3 production_main.py --mode arbitrage-only      # Arbitrage detection only
```

### 2. **New Service Layer Components**

#### `RealtimeCollector` (`src/services/realtime_collector.py`)
**Real-time data collection orchestrator**
- Coordinates WebSocket streams from multiple exchanges
- Manages connection health and automatic reconnection
- Handles data normalization across exchanges
- Implements backpressure management for high-frequency data

#### `OrderBookCollector` (`src/services/orderbook_collector.py`)
**Order book data collection service**
- Collects 10+ levels of bid/ask data
- Maintains order book snapshots and updates
- Calculates real-time spreads and market depth
- Stores historical order book data for analysis

#### `FundingCollector` (`src/services/funding_collector.py`)
**Perpetual funding rate collection service**
- Collects funding rates for BTC/ETH perpetuals
- Tracks funding rate changes and predictions
- Calculates funding arbitrage opportunities
- Historical funding rate analysis

#### `SpreadCalculator` (`src/services/spread_calculator.py`)
**Bid-ask spread calculation service**
- Real-time spread calculation across exchanges
- Spread trend analysis and alerts
- Cross-exchange spread comparison
- Spread-based trading signal generation

#### `StreamCoordinator` (`src/services/stream_coordinator.py`)
**WebSocket stream coordination service**
- Manages multiple WebSocket connections
- Handles stream failover and redundancy
- Coordinates data flow between streams and processors
- Stream performance monitoring and optimization

### 3. **New API Layer Components**

#### `BinanceClient` (`src/api/binance_client.py`)
**Binance API integration**
- REST API client for account and market data
- WebSocket stream management
- Order book and funding rate endpoints
- Rate limiting and error handling

#### `BybitClient` (`src/api/bybit_client.py`)
**Bybit API integration**
- REST API client for perpetual contracts
- WebSocket stream management
- Order book depth and funding rate data
- Cross-margin and isolated margin support

#### WebSocket Implementations (`src/api/websockets/`)

##### `BaseWebSocket` (`base_websocket.py`)
**Abstract WebSocket handler**
```python
class BaseWebSocket(ABC):
    def connect(self) -> None
    def disconnect(self) -> None
    def subscribe(self, channels: List[str]) -> None
    def handle_message(self, message: dict) -> None
    def reconnect(self) -> None
```

##### `BinanceWebSocket` (`binance_websocket.py`)
**Binance WebSocket client**
- Order book depth streams (`@depth20@100ms`)
- Ticker streams for funding rates
- Automatic reconnection with exponential backoff
- Message validation and error handling

##### `BybitWebSocket` (`bybit_websocket.py`)
**Bybit WebSocket client**
- Order book L2 data streams
- Perpetual contract funding rate streams
- Connection health monitoring
- Data normalization to common format

##### `StreamManager` (`stream_manager.py`)
**Multi-stream management**
- Coordinates multiple WebSocket connections
- Load balancing across connections
- Stream health monitoring and failover
- Data aggregation and routing

### 4. **New Data Layer Components**

#### Enhanced Database Schema (`src/data/enhanced_schema.sql`)
```sql
-- Order book data table
CREATE TABLE order_book (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    side TEXT NOT NULL, -- 'bid' or 'ask'
    level INTEGER NOT NULL, -- 0-based level (0 = best bid/ask)
    price REAL NOT NULL,
    quantity REAL NOT NULL,
    UNIQUE(exchange, symbol, timestamp, side, level)
);

-- Bid-ask spread data table
CREATE TABLE bid_ask_spreads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    bid_price REAL NOT NULL,
    ask_price REAL NOT NULL,
    spread_absolute REAL NOT NULL,
    spread_percentage REAL NOT NULL,
    mid_price REAL NOT NULL,
    UNIQUE(exchange, symbol, timestamp)
);

-- Funding rate data table
CREATE TABLE funding_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    funding_rate REAL NOT NULL,
    predicted_rate REAL,
    funding_time INTEGER NOT NULL,
    UNIQUE(exchange, symbol, timestamp)
);

-- Cross-exchange arbitrage opportunities
CREATE TABLE arbitrage_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL, -- 'spread' or 'funding'
    exchange_a TEXT NOT NULL,
    exchange_b TEXT NOT NULL,
    price_a REAL NOT NULL,
    price_b REAL NOT NULL,
    spread_percentage REAL NOT NULL,
    potential_profit REAL NOT NULL,
    confidence REAL NOT NULL
);
```

#### `RedisHelper` (`src/data/redis_helper.py`)
**Redis operations for real-time data**
- Real-time order book caching
- Stream data buffering
- Cross-exchange data synchronization
- Performance optimization for high-frequency data

#### Real-Time Data Models (`src/data/realtime_models.py`)
```python
@dataclass
class OrderBookLevel:
    price: float
    quantity: float
    level: int

@dataclass
class OrderBookSnapshot:
    exchange: str
    symbol: str
    timestamp: int
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    
@dataclass
class BidAskSpread:
    exchange: str
    symbol: str
    timestamp: int
    bid_price: float
    ask_price: float
    spread_absolute: float
    spread_percentage: float
    mid_price: float

@dataclass
class FundingRate:
    exchange: str
    symbol: str
    timestamp: int
    funding_rate: float
    predicted_rate: Optional[float]
    funding_time: int
```

### 5. **New Real-Time Processing Components**

#### `OrderBookProcessor` (`src/realtime/orderbook_processor.py`)
**Order book data processing**
- Normalizes order book data across exchanges
- Calculates market depth metrics
- Detects order book imbalances
- Generates order flow signals

#### `FundingProcessor` (`src/realtime/funding_processor.py`)
**Funding rate processing**
- Processes funding rate updates
- Calculates funding arbitrage opportunities
- Tracks funding rate trends and predictions
- Generates funding-based trading signals

#### `SpreadAnalyzer` (`src/realtime/spread_analyzer.py`)
**Spread analysis and monitoring**
- Real-time spread calculation and tracking
- Cross-exchange spread comparison
- Spread trend analysis and alerts
- Spread-based market condition assessment

#### `MarketStructureAnalyzer` (`src/realtime/market_structure_analyzer.py`)
**Market microstructure analysis**
- Order book imbalance detection
- Market impact analysis
- Liquidity assessment
- Price discovery efficiency metrics

#### `ArbitrageDetector` (`src/realtime/arbitrage_detector.py`)
**Cross-exchange arbitrage detection**
- Real-time price difference monitoring
- Funding rate arbitrage opportunities
- Risk-adjusted arbitrage scoring
- Execution feasibility analysis

### 6. **New Signal Generation Strategies**

#### `SpreadArbitrageStrategy` (`src/signals/strategies/spread_arbitrage_strategy.py`)
**Cross-exchange spread arbitrage**
- Monitors price differences between exchanges
- Generates arbitrage signals based on spread thresholds
- Accounts for transaction costs and execution risk
- Dynamic position sizing based on opportunity size

#### `FundingArbitrageStrategy` (`src/signals/strategies/funding_arbitrage_strategy.py`)
**Funding rate arbitrage**
- Identifies funding rate discrepancies
- Generates long/short signals for funding arbitrage
- Calculates expected returns from funding payments
- Risk management for funding rate volatility

#### `MarketStructureStrategy` (`src/signals/strategies/market_structure_strategy.py`)
**Order book analysis strategy**
- Analyzes order book imbalances for directional signals
- Detects large order presence and market manipulation
- Generates signals based on liquidity conditions
- Market microstructure-based entry/exit timing

---

## 🔄 Enhanced Data Flow Architecture

### 1. **Real-Time Data Collection Flow**
```
WebSocket Streams → Stream Manager → Data Processors → Redis Cache
                                                            ↓
Database ← Data Validator ← Real-Time Models ← Normalized Data
    ↓
CSV Backup (data/realtime/)
```

### 2. **Order Book Processing Flow**
```
Exchange WebSocket → Order Book Processor → Spread Calculator → Database
                                                    ↓
Redis Cache ← Order Book Snapshot ← Bid/Ask Levels ← Raw Order Data
    ↓
Signal Generation ← Market Structure Analysis ← Order Book Metrics
```

### 3. **Funding Rate Collection Flow**
```
Exchange APIs → Funding Collector → Funding Processor → Database
                                            ↓
Arbitrage Detector ← Funding Analysis ← Rate Comparison ← Multi-Exchange Data
    ↓
Trading Signals ← Opportunity Assessment ← Risk Analysis
```

### 4. **Cross-Exchange Arbitrage Flow**
```
Multi-Exchange Data → Price Comparison → Arbitrage Detector → Opportunity Scoring
                                                                      ↓
Signal Generation ← Risk Assessment ← Execution Feasibility ← Profit Calculation
```

---

## 📊 Enhanced Database Design

### **Storage Strategy Enhancement**
- **Primary**: SQLite database with real-time tables
- **Cache**: Redis for high-frequency real-time data
- **Backup**: CSV files for all data types
- **Archive**: Compressed historical data for long-term storage

### **New Data Models**

#### Real-Time Order Book Data
- **Frequency**: 100ms updates (Binance), 20ms updates (Bybit)
- **Depth**: 10+ levels of bid/ask data
- **Symbols**: BTC/USDT, ETH/USDT perpetuals
- **Exchanges**: Binance, Bybit
- **Metrics**: Spread, depth, imbalance, liquidity

#### Funding Rate Data
- **Frequency**: Every 8 hours (funding payments)
- **Prediction**: Next funding rate predictions
- **Historical**: Full funding rate history
- **Arbitrage**: Cross-exchange funding opportunities

#### Arbitrage Opportunities
- **Types**: Price spread, funding rate arbitrage
- **Scoring**: Risk-adjusted profit potential
- **Execution**: Feasibility and timing analysis
- **Performance**: Historical arbitrage success rates

---

## 🔌 Enhanced API Integration

### **Binance API Integration**
- **REST Endpoints**:
  - `/fapi/v1/depth` - Order book depth
  - `/fapi/v1/premiumIndex` - Funding rates
  - `/fapi/v1/ticker/bookTicker` - Best bid/ask
- **WebSocket Streams**:
  - `btcusdt@depth20@100ms` - Order book updates
  - `btcusdt@ticker` - 24hr ticker statistics
- **Rate Limits**: 2400 requests/minute, 10 connections/IP

### **Bybit API Integration**
- **REST Endpoints**:
  - `/v5/market/orderbook` - Order book L2 data
  - `/v5/market/funding/history` - Funding rate history
  - `/v5/market/tickers` - Real-time ticker data
- **WebSocket Streams**:
  - `orderbook.50.BTCUSDT` - Order book updates
  - `tickers.BTCUSDT` - Real-time ticker
- **Rate Limits**: 600 requests/minute, 20 connections/IP

---

## ⚙️ Enhanced Configuration Management

### **Real-Time Configuration** (`config/realtime/`)

#### Order Book Configuration (`orderbook_config.py`)
```python
ORDERBOOK_CONFIG = {
    'depth_levels': 10,
    'update_frequency': '100ms',
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'exchanges': ['binance', 'bybit'],
    'storage': {
        'redis_ttl': 3600,  # 1 hour
        'db_batch_size': 100,
        'csv_backup': True
    }
}
```

#### Funding Rate Configuration (`funding_config.py`)
```python
FUNDING_CONFIG = {
    'collection_interval': 300,  # 5 minutes
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'exchanges': ['binance', 'bybit'],
    'arbitrage_thresholds': {
        'min_rate_diff': 0.0001,  # 0.01%
        'min_profit_bps': 5       # 5 basis points
    }
}
```

#### Stream Configuration (`stream_config.py`)
```python
STREAM_CONFIG = {
    'reconnect_attempts': 5,
    'reconnect_delay': 1.0,
    'max_reconnect_delay': 60.0,
    'ping_interval': 30,
    'connection_timeout': 10,
    'message_buffer_size': 1000
}
```

### **Exchange Configuration** (`config/exchanges/`)

#### Binance Configuration (`binance_config.py`)
```python
BINANCE_CONFIG = {
    'base_url': 'https://fapi.binance.com',
    'websocket_url': 'wss://fstream.binance.com/ws',
    'rate_limits': {
        'requests_per_minute': 2400,
        'orders_per_second': 100,
        'max_connections': 10
    },
    'streams': {
        'orderbook': '@depth20@100ms',