# MTS Data Pipeline - Project Architecture

## 🎯 Project Overview

The **MTS (Market Time Series) Data Pipeline** is a comprehensive cryptocurrency data collection and trading signal system that combines historical data collection, real-time market monitoring, and advanced signal generation across multiple exchanges. The system is designed for production trading environments with robust error handling, cross-exchange arbitrage detection, and sophisticated signal aggregation.

### Key Capabilities

#### Core Data Infrastructure
- **Historical Data Collection**: Automated OHLCV data collection for top cryptocurrencies via CoinGecko API
- **Real-Time Market Data**: Live WebSocket streams from Binance and Bybit exchanges
- **Cross-Exchange Integration**: Seamless data normalization across multiple exchange formats
- **Macro Economic Data**: Integration with FRED API for VIX, Treasury rates, and economic indicators

#### Advanced Analytics & Trading
- **Cross-Exchange Arbitrage Detection**: Real-time identification of profitable arbitrage opportunities
- **Multi-Strategy Signal Generation**: VIX correlation, mean reversion, volume spikes, and momentum strategies
- **Real-Time Signal Aggregation**: Live signal processing with confidence scoring and strength classification
- **Funding Rate Analysis**: Cross-exchange funding rate divergence monitoring
- **Volume Anomaly Detection**: Automated detection of unusual trading patterns

#### Production Features
- **Multi-Tier Storage**: Redis caching + SQLite analysis + CSV backup architecture
- **WebSocket Infrastructure**: Robust real-time connections with auto-reconnection and error recovery
- **Comprehensive Testing**: 96+ tests covering all components including real-time edge cases
- **Production Deployment**: Docker-based deployment with orchestration and monitoring
- **Health Monitoring**: Advanced health checks for real-time components and data freshness
- **Performance Optimization**: Efficient data processing and memory management for high-frequency data

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     MTS Real-Time Trading Signal Pipeline                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Entry Points: main.py | production_main.py | WebSocket Streams | API Endpoints │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Real-Time Services Layer                                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ OrderBook   │ │ Funding     │ │Cross-Exchang│ │ Real-Time   │ │ Arbitrage   ││
│  │ Collector   │ │ Collector   │ │ Analyzer    │ │ Signal Agg. │ │ Monitor     ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Historical Services Layer                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Crypto      │ │ Macro       │ │ Scheduler   │ │ Monitor     │ │ Multi-      ││
│  │ Collector   │ │ Collector   │ │ Service     │ │ Service     │ │ Strategy    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Signal Generation & Processing Layer                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ VIX         │ │ Mean        │ │ Volume      │ │ Strategy    │ │ Signal      ││
│  │ Correlation │ │ Reversion   │ │ Spike       │ │ Registry    │ │ Aggregator  ││
│  │ Strategy    │ │ Strategy    │ │ Detection   │ │             │ │             ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  API & WebSocket Layer                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Binance     │ │ Bybit       │ │ CoinGecko   │ │ FRED API    │ │ Signal API  ││
│  │ WS + REST   │ │ WS + REST   │ │ Client      │ │ Client      │ │ (FastAPI)   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
├─────────────────────────────────────────────────────────────────────────────────┤
│  Multi-Tier Data Layer                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Redis Cache │ │ SQLite      │ │ CSV         │ │ Real-Time   │ │ OrderBook   ││
│  │ (Real-Time) │ │ Database    │ │ Storage     │ │ Storage     │ │ Processor   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
         │                    │                    │                    │
         ▼                    ▼                    ▼                    ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Redis       │    │ SQLite DB   │    │ CSV Files   │    │ Real-Time   │
   │ (Live Data) │    │ crypto_data │    │ data/raw/   │    │ Signals     │
   └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📁 Directory Structure

```
MTS-data-pipeline/
├── 📁 config/                    # Configuration management
│   ├── __init__.py
│   ├── settings.py               # Core application settings
│   ├── logging_config.py         # Logging configuration
│   ├── macro_settings.py         # Macro data collection settings
│   └── 📁 strategies/            # 🆕 Strategy configurations
│       ├── vix_correlation.json  # VIX correlation strategy config
│       └── mean_reversion.json   # Mean reversion strategy config
├── 📁 src/                       # Source code
│   ├── __init__.py
│   ├── 📁 api/                   # External API clients
│   │   ├── __init__.py
│   │   ├── coingecko_client.py   # CoinGecko API wrapper
│   │   ├── binance_client.py     # 🆕 Binance REST API client
│   │   ├── bybit_client.py       # 🆕 Bybit REST API client
│   │   ├── fred_client.py        # FRED API wrapper
│   │   ├── signal_api.py         # FastAPI signal generation endpoint
│   │   └── 📁 websockets/        # 🆕 Real-time WebSocket clients
│   │       ├── __init__.py
│   │       ├── base_websocket.py # Abstract WebSocket base class
│   │       ├── binance_websocket.py # Binance WebSocket streams
│   │       └── bybit_websocket.py   # Bybit WebSocket streams
│   ├── 📁 data/                  # Data management layer
│   │   ├── __init__.py
│   │   ├── db_connection.py      # Database connection handling
│   │   ├── db_init.py           # Database initialization
│   │   ├── models.py            # Historical data models (Cryptocurrency, OHLCVData)
│   │   ├── realtime_models.py   # 🆕 Real-time data structures (OrderBook, FundingRate)
│   │   ├── macro_models.py      # Macro data models
│   │   ├── signal_models.py     # Signal data models
│   │   ├── schema.sql           # Database schema definition
│   │   ├── enhanced_schema.sql  # 🆕 Real-time tables schema
│   │   ├── sqlite_helper.py     # High-level database operations
│   │   ├── storage.py           # CSV storage operations
│   │   ├── realtime_storage.py  # 🆕 Real-time data persistence
│   │   ├── redis_helper.py      # 🆕 Redis caching operations
│   │   └── validator.py         # Data validation logic
│   ├── 📁 realtime/             # 🆕 Real-time processing
│   │   ├── __init__.py
│   │   └── orderbook_processor.py # Order book data processing and normalization
│   ├── 📁 services/             # Business logic services
│   │   ├── __init__.py
│   │   ├── collector.py         # Historical crypto data collection
│   │   ├── orderbook_collector.py # 🆕 Real-time order book collection
│   │   ├── funding_collector.py   # 🆕 Funding rate collection service
│   │   ├── cross_exchange_analyzer.py # 🆕 Arbitrage detection and analysis
│   │   ├── realtime_signal_aggregator.py # 🆕 Real-time signal generation
│   │   ├── spread_calculator.py   # 🆕 Bid-ask spread analysis
│   │   ├── macro_collector.py   # Macro data collection
│   │   ├── monitor.py           # Health monitoring
│   │   ├── scheduler.py         # Task scheduling
│   │   └── multi_strategy_generator.py # Multi-strategy signal generation
│   ├── 📁 signals/              # 🆕 Signal generation module
│   │   ├── __init__.py
│   │   ├── backtest_interface.py # Backtesting interface
│   │   ├── signal_aggregator.py  # Signal aggregation and conflict resolution
│   │   └── 📁 strategies/        # Strategy implementations
│   │       ├── __init__.py
│   │       ├── base_strategy.py  # Abstract base strategy class
│   │       ├── strategy_registry.py # Strategy registration system
│   │       ├── vix_correlation_strategy.py # VIX correlation strategy
│   │       └── mean_reversion_strategy.py # Mean reversion strategy
│   └── 📁 utils/                # Utility functions
│       ├── __init__.py
│       ├── exceptions.py        # Custom exception classes
│       └── retry.py             # Retry logic with backoff
├── 📁 data/                     # Data storage
│   ├── 📁 backup/               # CSV backup files
│   ├── 📁 raw/                  # Raw CSV data
│   │   ├── 📁 macro/            # Macro indicator CSV files
│   │   ├── 📁 orderbooks/       # 🆕 Order book snapshots
│   │   ├── 📁 funding/          # 🆕 Funding rate data
│   │   └── 📁 spreads/          # 🆕 Bid-ask spread data
│   ├── 📁 realtime/             # 🆕 Real-time data storage
│   │   ├── 📁 binance/          # Binance real-time data
│   │   │   ├── 📁 orderbooks/
│   │   │   ├── 📁 funding/
│   │   │   └── 📁 spreads/
│   │   ├── 📁 bybit/            # Bybit real-time data
│   │   │   ├── 📁 orderbooks/
│   │   │   ├── 📁 funding/
│   │   │   └── 📁 spreads/
│   │   └── 📁 signals/          # Real-time signal outputs
│   │       ├── 📁 arbitrage/
│   │       ├── 📁 volume_spikes/
│   │       └── 📁 spread_anomalies/
│   └── crypto_data.db           # SQLite database
├── 📁 examples/                 # Usage examples
│   └── sqlite_analysis.py       # Database analysis examples
├── 📁 scripts/                  # Utility scripts
│   └── migrate_csv_to_sqlite.py # Migration utilities
├── 📁 tests/                    # Test suite
│   └── [comprehensive test files including signal generation tests]
├── 📁 logs/                     # Application logs
├── main.py                      # Main application entry point
├── production_main.py           # 🆕 Production orchestrator
├── docker-compose.yml           # 🆕 Production deployment configuration
├── Dockerfile                   # 🆕 Production container image
├── deploy.sh                    # 🆕 Production deployment script
├── PRODUCTION.md                # 🆕 Production deployment guide
├── requirements.txt             # Python dependencies
├── schedule_data.sh             # Crypto data collection script
├── collect_macro.sh             # Macro data collection script
└── README.md                    # Project documentation
```

---

## 🧩 Core Components

### 1. **Entry Points**

#### `main.py` - Development Interface
```python
# Key functions:
python3 main.py --collect                    # Collect crypto data
python3 main.py --collect --days 7          # Collect 7 days of data
python3 main.py --server                    # Start health monitoring server
python3 main.py --server --port 9090       # Custom port
```

#### `production_main.py` - Production Orchestrator
```python
# Production deployment modes:
python3 production_main.py --mode full                 # Full production pipeline
python3 production_main.py --mode api-only            # API server only
python3 production_main.py --mode collector-only      # Data collection only
python3 production_main.py --mode signals-only        # Signal generation only
```

#### Docker Deployment
```bash
# Production deployment with Docker
./deploy.sh setup              # Interactive setup
./deploy.sh start              # Start all services
./deploy.sh start --with-monitoring  # Include monitoring
./deploy.sh health             # Check service health
```

### 2. **Real-Time Components**

#### `BinanceClient` & `BybitClient` (`src/api/binance_client.py`, `src/api/bybit_client.py`)
**Exchange REST API clients**
- Order book data retrieval with configurable depth
- Funding rate collection for perpetual futures
- Ticker and instrument information
- Rate limiting and error handling
- Exchange-specific response format handling

#### `BinanceWebSocket` & `BybitWebSocket` (`src/api/websockets/`)
**Real-time WebSocket streaming clients**
- Live order book updates and ticker streams
- Automatic subscription management
- Exponential backoff reconnection strategy
- Message parsing and validation
- Exchange-specific protocol handling

#### `OrderBookProcessor` (`src/realtime/orderbook_processor.py`)
**Multi-exchange order book data processor**
- Unified processing for Binance and Bybit order book formats
- Data normalization and validation
- Order book snapshot creation
- Cross-market data comparison
- Real-time data quality assurance

#### `CrossExchangeAnalyzer` (`src/services/cross_exchange_analyzer.py`)
**Arbitrage detection and analysis service**
- Real-time arbitrage opportunity identification
- Profit calculation with volume analysis
- Cross-exchange spread monitoring
- Opportunity tracking and expiration management
- Performance metrics and statistics

#### `RealtimeSignalAggregator` (`src/services/realtime_signal_aggregator.py`)
**Live signal generation and aggregation**
- Multi-signal type generation (arbitrage, volume spikes, spread anomalies)
- Signal strength classification (WEAK, MODERATE, STRONG)
- Confidence scoring and thresholding
- Real-time signal callbacks and notifications
- Signal expiration and cleanup management

### 3. **Historical Service Layer**

#### `DataCollector` (`src/services/collector.py`)
**Primary crypto data collection service**
- Fetches top 3 cryptocurrencies by market cap
- Collects OHLCV data via CoinGecko API
- Handles market_chart endpoint (price + volume data)
- Comprehensive error categorization and retry logic
- Structured metrics logging

#### `MacroDataCollector` (`src/services/macro_collector.py`)
**Macro economic data collection service**
- Collects VIX, Dollar Index, Treasury rates, Fed Funds rate
- Integrates with FRED API
- Handles missing data and interpolation
- Automatic data quality checks

#### `MultiStrategyGenerator` (`src/services/multi_strategy_generator.py`)
**Signal generation orchestration service**
- Coordinates multiple trading strategies
- Manages strategy lifecycle and execution
- Handles signal aggregation and conflict resolution
- Provides backtesting capabilities
- Generates timestamped signal outputs

#### `HealthChecker` (`src/services/monitor.py`)
**System health monitoring**
- Database health checks
- Data freshness validation
- Component status monitoring
- HTTP endpoint for external monitoring

#### `SimpleScheduler` (`src/services/scheduler.py`)
**Task scheduling and automation**
- Configurable collection intervals
- Graceful shutdown handling
- Persistent scheduling state

### 3. **Signal Generation Layer**

#### `SignalStrategy` (`src/signals/strategies/base_strategy.py`)
**Abstract base strategy class**
```python
# Strategy interface:
class SignalStrategy(ABC):
    def analyze(self, market_data: dict) -> dict
    def generate_signals(self, analysis_results: dict) -> List[TradingSignal]
    def get_parameters(self) -> dict
    def backtest(self, historical_data: pd.DataFrame) -> dict
```

#### `VIXCorrelationStrategy` (`src/signals/strategies/vix_correlation_strategy.py`)
**VIX correlation-based signal generation**
- Analyzes VIX vs cryptocurrency correlations
- Generates long/short signals based on correlation thresholds
- Configurable lookback periods and correlation bands
- Risk-adjusted position sizing

#### `MeanReversionStrategy` (`src/signals/strategies/mean_reversion_strategy.py`)
**Mean reversion signal generation**
- Detects VIX spikes and crypto price drawdowns
- Generates contrarian signals during market stress
- Configurable volatility thresholds
- Risk management integration

#### `StrategyRegistry` (`src/signals/strategies/strategy_registry.py`)
**Dynamic strategy loading and management**
- Automatic strategy discovery and registration
- Configuration-based strategy activation
- Strategy parameter validation
- Performance tracking

#### `SignalAggregator` (`src/signals/signal_aggregator.py`)
**Signal aggregation and conflict resolution**
- Combines signals from multiple strategies
- Handles conflicting signals with weighted scoring
- Portfolio-level risk management
- Signal quality assessment

#### `BacktestInterface` (`src/signals/backtest_interface.py`)
**Backtesting framework**
- Historical signal validation
- Performance metrics calculation
- Risk-adjusted return analysis
- Strategy comparison utilities

### 4. **API Layer**

#### `CoinGeckoClient` (`src/api/coingecko_client.py`)
**CoinGecko API integration**
- Rate limiting and retry logic
- Market cap ranking endpoints
- OHLCV data via market_chart endpoint
- Comprehensive error handling

#### `FredClient` (`src/api/fred_client.py`)
**Federal Reserve Economic Data API**
- Economic indicator collection
- API key management
- Data series retrieval

#### `SignalAPI` (`src/api/signal_api.py`)
**FastAPI signal generation endpoint**
- RESTful API for signal generation
- Authentication and rate limiting
- Real-time signal streaming
- Historical signal retrieval
- Strategy configuration endpoints

### 5. **Data Layer**

#### `CryptoDatabase` (`src/data/sqlite_helper.py`)
**High-level database operations**
```python
# Key methods:
db = CryptoDatabase()
db.insert_crypto_data(crypto_data)
db.insert_macro_data(macro_data)
health_status = db.get_health_status()
df = db.get_crypto_data('bitcoin', days=30)
combined_df = db.get_combined_analysis_data('bitcoin', days=30)
```

#### Signal Data Models (`src/data/signal_models.py`)
**Signal-specific data structures**
- `TradingSignal`: Individual signal representation
- `StrategyResult`: Strategy execution results
- `BacktestResult`: Backtesting output structure
- `SignalMetrics`: Performance tracking data

#### Database Schema (`src/data/schema.sql`)
```sql
-- Crypto OHLCV data table
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
    UNIQUE(cryptocurrency, timestamp)
);

-- Macro economic data table
CREATE TABLE macro_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL NOT NULL,
    UNIQUE(indicator, date)
);
```

---

## 🔄 Data Flow Architecture

### 1. **Real-Time Data Flow**
```
┌─────────────────────────────────────────────────────────────────┐
│                     WebSocket Streams                           │
│  Binance WS ←→ BinanceWebSocket ←→ OrderBookProcessor           │
│  Bybit WS   ←→ BybitWebSocket   ←→ OrderBookProcessor           │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Real-Time Analysis                             │
│  CrossExchangeAnalyzer → ArbitrageOpportunity                  │
│  RealtimeSignalAggregator → TradingSignal                      │
└─────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Tier Storage                           │
│  Redis (Live) → SQLite (Analysis) → CSV (Backup)               │
└─────────────────────────────────────────────────────────────────┘
```

### 2. **Cross-Exchange Arbitrage Flow**
```
Order Books → Price Comparison → Arbitrage Detection → Signal Generation
   ↓              ↓                    ↓                    ↓
Binance        Best Bid/Ask        Profit Calc         Trading Signal
Bybit          Spread Analysis     Volume Check        Confidence Score
               Market Validation   Opportunity Track.  Action (BUY/SELL)
```

### 3. **Historical Data Collection Flow**
```
Scheduler/Manual → DataCollector → CoinGeckoClient → API Response
                                                           ↓
Database ← DataValidator ← OHLCVData Models ← Raw Data Processing
    ↓
CSV Backup (data/backup/)
```

### 4. **Macro Data Collection Flow**
```
Scheduler/Manual → MacroDataCollector → FredClient → FRED API
                                                         ↓
Database ← Data Processing ← Interpolation ← Raw Economic Data
    ↓
CSV Storage (data/raw/macro/)
```

### 5. **Signal Generation Flow**
```
Market Data → MultiStrategyGenerator → Strategy Registry → Individual Strategies
                                                                    ↓
Signal Aggregator ← Strategy Results ← VIX Correlation + Mean Reversion
      ↓
Conflict Resolution → Final Signals → JSON Output → API Responses
```

### 6. **Health Monitoring Flow**
```
HTTP Request → HealthChecker → Database Queries → Component Checks
                                    ↓
JSON Response ← Status Compilation ← Health Metrics + Real-Time Status
```

### 7. **Production Deployment Flow**
```
Docker Compose → MTS Container + Redis + Nginx → Signal API Server
                                                       ↓
External Requests → Authentication → Strategy Execution → Signal Response
                                         ↓
                     Real-Time WebSocket → Live Data → Signal Updates
```

---

## 📊 Database Design

### **Storage Strategy**
- **Primary**: SQLite database (`data/crypto_data.db`)
- **Backup**: CSV files (`data/backup/`, `data/raw/`)
- **Analysis**: Built-in Pandas integration for data science workflows

### **Data Models**

#### Cryptocurrency Data
- **Frequency**: 5-minute intervals (CoinGecko limitation)
- **Cryptocurrencies**: Bitcoin, Ethereum, #3 by market cap (typically Tether)
- **Data Points**: Open, High, Low, Close, Volume, Timestamp
- **Deduplication**: Automatic via UNIQUE constraints

#### Macro Economic Data
- **Frequency**: Daily
- **Indicators**: VIX, DXY (Dollar Index), 10Y Treasury, Fed Funds Rate
- **Data Quality**: Interpolation for missing values, forward-fill for weekends
- **Source**: Federal Reserve Economic Data (FRED)

---

## 🔌 API Integration

### **CoinGecko API**
- **Base URL**: `https://api.coingecko.com/api/v3/`

### **Real-Time API Integration**

#### **Binance API**
- **REST Base URL**: `https://fapi.binance.com`
- **WebSocket URL**: `wss://fstream.binance.com/ws`
- **Key Endpoints**: `/fapi/v1/depth`, `/fapi/v1/premiumIndex`, `/fapi/v1/ticker/24hr`
- **WebSocket Streams**: `{symbol}@depth20@100ms`, `{symbol}@ticker`
- **Rate Limits**: 2400 requests/minute, 10 connections max
- **Update Speed**: 100ms order book updates

#### **Bybit API**
- **REST Base URL**: `https://api.bybit.com`
- **WebSocket URL**: `wss://stream.bybit.com/v5/public/linear`
- **Key Endpoints**: `/v5/market/orderbook`, `/v5/market/funding/history`, `/v5/market/tickers`
- **WebSocket Channels**: `orderbook.50.{symbol}`, `tickers.{symbol}`
- **Rate Limits**: 600 requests/minute, 20 connections max
- **Update Speed**: 20ms order book updates

---

## 🧪 Testing Architecture

### **Comprehensive Test Coverage (96+ Tests)**

#### **Real-Time Component Tests**
- **Bybit REST Client**: 14 tests covering all API endpoints and error scenarios
- **Bybit WebSocket Client**: 24 tests including connection management and message handling
- **Cross-Exchange Analyzer**: 15 tests for arbitrage detection and profit calculations
- **Real-Time Signal Aggregator**: 14 tests covering all signal types and edge cases
- **Order Book Processor**: Tests for multi-exchange data normalization

#### **Integration Tests**
- **Real-Time Integration**: End-to-end testing of live data flows
- **WebSocket Connection Tests**: Connection reliability and reconnection scenarios
- **Cross-Exchange Data Sync**: Verification of data consistency across exchanges
- **Signal Generation Pipeline**: Complete signal workflow testing

#### **Error Scenario Testing**
- **Network Failures**: WebSocket disconnections and API timeouts
- **Data Quality Issues**: Invalid order book data and market anomalies
- **Rate Limiting**: API throttling and backoff behavior
- **Exchange Outages**: Graceful degradation when exchanges are unavailable

#### **Performance Tests**
- **High-Frequency Data**: Order book update processing performance
- **Memory Management**: Real-time data caching and cleanup
- **Signal Latency**: End-to-end signal generation timing
- **Concurrent Processing**: Multi-exchange data handling

### **Test Execution**
```bash
# Run all tests
python3 -m pytest

# Run specific test categories  
python3 -m pytest tests/test_bybit_client.py      # Bybit REST tests
python3 -m pytest tests/test_bybit_websocket.py   # Bybit WebSocket tests
python3 -m pytest tests/test_cross_exchange_analyzer.py  # Arbitrage tests
python3 -m pytest tests/test_realtime_signal_aggregator.py  # Signal tests

# Run with coverage
python3 -m pytest --cov=src --cov-report=html
```
- **Key Endpoints**:
  - `/coins/markets` - Market cap rankings
  - `/coins/{id}/market_chart` - OHLCV data
- **Rate Limits**: Built-in exponential backoff
- **Authentication**: None required (public API)

### **FRED API**
- **Base URL**: `https://api.stlouisfed.org/fred`
- **Authentication**: API key required (environment variable)
- **Rate Limits**: 120,000 requests/day, 1,000 requests/hour
- **Key Series**:
  - `VIXCLS` - VIX Volatility Index
  - `DTWEXBGS` - US Dollar Index
  - `DGS10` - 10-Year Treasury Rate
  - `DFF` - Federal Funds Rate

---

## ⚙️ Configuration Management

### **Environment Variables**
```bash
# .env file
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
REQUEST_TIMEOUT=30
FRED_API_KEY=your_fred_api_key_here
```

### **Configuration Classes**
- `Config` (`config/settings.py`) - Core application settings
- `MACRO_INDICATORS` (`config/macro_settings.py`) - Macro data configuration
- `FRED_API_CONFIG` - FRED API settings and limits

---

## 🛡️ Error Handling & Recovery

### **Error Categories**
- **Network Errors**: Connection timeouts, DNS failures
- **API Errors**: Rate limits, server errors, authentication
- **Data Validation**: Invalid formats, missing fields
- **Storage Errors**: Database locks, disk space issues

### **Recovery Strategies**
```python
# Retry logic with exponential backoff
@retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=60.0)
def collect_data():
    # Collection logic with automatic retry
```

### **Error Monitoring**
- Structured logging with JSON metrics
- Error categorization and recovery recommendations
- Health check integration

---

## 📈 Monitoring & Health Checks

### **Health Check Endpoint**
```bash
curl http://localhost:8080/health
```

### **Health Metrics**
- Data freshness (age of latest data)
- Component availability
- Database health
- API connectivity
- Error rates and categories

### **Monitoring Output**
```json
{
  "status": "healthy",
  "healthy": true,
  "components": {
    "data_freshness": {
      "overall_status": "healthy",
      "fresh_count": 3,
      "cryptos": {
        "bitcoin": {
          "status": "fresh",
          "age_hours": 0.5,
          "records_count": 24
        }
      }
    }
  }
}
```

---

## 🚀 Usage Examples

### **Basic Data Collection**
```python
from src.services.collector import DataCollector

# Initialize collector
collector = DataCollector()

# Collect current data
results = collector.collect_all_data(days=1)

# Check results
print(f"Successfully collected: {results['successful_cryptos']}")
```

### **Database Analysis**
```python
from src.data.sqlite_helper import CryptoDatabase

# Initialize database
db = CryptoDatabase()

# Get Bitcoin data
bitcoin_df = db.get_crypto_data('bitcoin', days=30)

# Get combined crypto-macro analysis
combined_df = db.get_combined_analysis_data('bitcoin', days=30)

# Health status
health = db.get_health_status()
```

### **Automated Collection**
```bash
# Run collection script
./schedule_data.sh

# Run macro collection
./collect_macro.sh

# Start monitoring server
python3 main.py --server --port 8080
```

---

## 📦 Dependencies

### **Core Dependencies**
```txt
requests          # HTTP client for API calls
pytest           # Testing framework  
python-dotenv    # Environment variable management
pandas           # Data analysis and manipulation
matplotlib       # Plotting and visualization
seaborn          # Statistical data visualization
```

### **Python Version**
- **Minimum**: Python 3.8+
- **Recommended**: Python 3.10+
- **Tested**: Python 3.12

---

## 🔧 Development & Extension Notes

### **Adding New Cryptocurrencies**
The system automatically tracks the top 3 cryptocurrencies by market cap. No manual configuration needed.

### **Adding New Macro Indicators**
Add to `config/macro_settings.py`:
```python
MACRO_INDICATORS['NEW_INDICATOR'] = {
    'fred_series_id': 'SERIES_ID',
    'name': 'Indicator Name',
    'frequency': 'daily',
    'units': 'Units',
    'file_prefix': 'filename'
}
```

### **Custom Analysis**
See `examples/sqlite_analysis.py` for analysis patterns:
- Basic queries and statistics
- Price trend analysis
- Combined crypto-macro analysis
- Health monitoring

### **Testing**
```bash
# Run full test suite
pytest tests/

# Run specific test categories
pytest tests/test_collector.py
pytest tests/test_integration.py
```

### **Database Extensions**
The SQLite schema supports easy extension. Add new tables following the existing pattern with proper indexing.

---

## 🎯 Key Design Principles

1. **Reliability**: Comprehensive error handling and recovery
2. **Observability**: Structured logging and health monitoring
3. **Flexibility**: Easy configuration and extension
4. **Performance**: Efficient database operations and API usage
5. **Maintainability**: Clean architecture and comprehensive testing

---

This architecture supports both manual data collection and automated pipeline operations, with built-in monitoring and analysis capabilities for production use. 

---

## 🎯 Signal Generation Architecture

### **Signal Strategy Framework**
The MTS pipeline includes an extensible signal generation framework that analyzes market data and generates trading signals based on multiple strategies.

#### **Strategy Interface**
```python
class SignalStrategy(ABC):
    def analyze(self, market_data: dict) -> dict
    def generate_signals(self, analysis_results: dict) -> List[TradingSignal]
    def get_parameters(self) -> dict
    def backtest(self, historical_data: pd.DataFrame) -> dict
```

#### **Strategy Configuration**
Each strategy has a JSON configuration file in `config/strategies/`:
```json
{
    "name": "VIX_Correlation_Strategy",
    "assets": ["bitcoin", "ethereum", "binancecoin"],
    "correlation_thresholds": {
        "strong_negative": -0.6,
        "strong_positive": 0.6
    },
    "lookback_days": 30,
    "position_size": 0.02
}
```

### **Signal Generation Process**
1. **Data Collection**: Gather crypto and macro data
2. **Strategy Execution**: Run each enabled strategy
3. **Signal Generation**: Generate individual trading signals
4. **Aggregation**: Combine signals from multiple strategies
5. **Conflict Resolution**: Handle contradictory signals
6. **Output**: Generate JSON signal files with timestamps

### **Signal Output Format**
```json
{
    "timestamp": "2025-01-07T10:30:00Z",
    "signals": [
        {
            "strategy": "VIX_Correlation_Strategy",
            "asset": "bitcoin",
            "signal": "long",
            "confidence": 0.75,
            "position_size": 0.02,
            "risk_level": "medium"
        }
    ],
    "market_context": {
        "vix_level": 18.5,
        "correlation_btc_vix": -0.65
    }
}
```

---

## 🐳 Production Deployment Architecture

### **Container Architecture**
The production deployment uses Docker Compose to orchestrate multiple services:

#### **MTS Pipeline Container**
- **Base Image**: Python 3.11 slim
- **Services**: Data collection, signal generation, API server
- **Ports**: 8000 (API), 8001 (metrics)
- **Volumes**: Data, logs, configuration

#### **Redis Container**
- **Purpose**: Caching and message queue
- **Configuration**: Persistent storage, memory optimization
- **Usage**: Signal caching, API response caching

#### **Nginx Container** (Optional)
- **Purpose**: Reverse proxy and load balancing
- **SSL**: Certificate management
- **Rate Limiting**: API protection

#### **Monitoring Stack** (Optional)
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Alerting**: Real-time notifications

### **Production Entry Points**
```bash
# Full production pipeline
python3 production_main.py --mode full

# API server only
python3 production_main.py --mode api-only

# Data collection only
python3 production_main.py --mode collector-only

# Signal generation only
python3 production_main.py --mode signals-only
```

### **Deployment Configuration**
```yaml
# docker-compose.yml
services:
  mts-pipeline:
    build: .
    environment:
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379/0
      - API_SECRET_KEY=${API_SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
```

### **Health Monitoring**
```json
{
  "status": "healthy",
  "healthy": true,
  "services": {
    "data_collector": "running",
    "signal_generator": "running",
    "api_server": "running",
    "redis": "connected"
  },
  "performance": {
    "signals_generated_last_hour": 12,
    "api_requests_last_hour": 45,
    "database_health": "good"
  }
}
```

---

## 📊 Signal Generation Configuration

### **Strategy Configuration Files**
Located in `config/strategies/`:

#### **VIX Correlation Strategy**
```json
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
        "max_portfolio_risk": 0.10,
        "volatility_adjustment": true
    }
}
```

#### **Mean Reversion Strategy**
```json
{
    "name": "Mean_Reversion_Strategy",
    "assets": ["bitcoin", "ethereum", "binancecoin"],
    "vix_spike_threshold": 25,
    "drawdown_threshold": 0.10,
    "lookback_days": 14,
    "position_size": 0.025,
    "risk_management": {
        "max_drawdown": 0.15,
        "stop_loss": 0.05
    }
}
```

### **Signal API Endpoints**
```python
# FastAPI endpoints
GET  /signals/current          # Get current signals
POST /signals/generate         # Generate new signals
GET  /signals/history          # Historical signals
GET  /strategies/list          # Available strategies
POST /strategies/config        # Update strategy config
GET  /health                   # API health check
```

---

## 🔄 Extended Data Flow

### **Complete Pipeline Flow**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Production Pipeline                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Data Collection (Crypto + Macro)                                        │
│    ├─ CoinGecko API → OHLCV Data → Database                               │
│    └─ FRED API → VIX/Economic Data → Database                             │
│                                                                             │
│ 2. Signal Generation                                                        │
│    ├─ Strategy Registry → Load Strategies                                  │
│    ├─ Multi-Strategy Generator → Execute Strategies                        │
│    ├─ Signal Aggregator → Combine & Resolve Conflicts                      │
│    └─ JSON Output → Timestamped Signal Files                               │
│                                                                             │
│ 3. API Services                                                             │
│    ├─ FastAPI Server → RESTful Endpoints                                   │
│    ├─ Authentication → JWT Token Validation                                │
│    ├─ Rate Limiting → Request Throttling                                   │
│    └─ Real-time Signals → WebSocket Streaming                              │
│                                                                             │
│ 4. Monitoring & Health                                                      │
│    ├─ Health Checks → Component Status                                     │
│    ├─ Performance Metrics → System Monitoring                              │
│    ├─ Error Tracking → Structured Logging                                  │
│    └─ Alerting → Production Notifications                                  │
└─────────────────────────────────────────────────────────────────────────────┘
``` 