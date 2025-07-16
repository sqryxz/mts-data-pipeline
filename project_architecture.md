# MTS Cryptocurrency Data Pipeline - Project Architecture

## Overview

The MTS (Multi-Timeframe Signal) Cryptocurrency Data Pipeline is a comprehensive trading infrastructure system that combines historical data collection, real-time market data processing, signal generation, and backtesting capabilities. The system is designed for cryptocurrency trading strategy development and deployment.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                MTS DATA PIPELINE                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   DATA SOURCES  │  │  REAL-TIME DATA │  │  SIGNAL ENGINE  │  │  BACKTESTING    │  │
│  │                 │  │                 │  │                 │  │                 │  │
│  │ • CoinGecko API │  │ • Binance WS    │  │ • VIX Strategy  │  │ • Event-Driven │  │
│  │ • FRED API      │  │ • Bybit WS      │  │ • Mean Revert.  │  │ • Portfolio Mgr │  │
│  │ • Binance API   │  │ • Order Books   │  │ • Aggregation   │  │ • Execution     │  │
│  │ • Bybit API     │  │ • Funding Rates │  │ • Risk Mgmt     │  │ • Analytics     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│            │                    │                    │                    │           │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                          STORAGE & CACHING LAYER                                │  │
│  │                                                                                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │  SQLite DB  │  │  Redis Cache│  │  CSV Backup │  │  Log Files  │          │  │
│  │  │             │  │             │  │             │  │             │          │  │
│  │  │ • OHLCV     │  │ • RT Data   │  │ • Funding   │  │ • Structured│          │  │
│  │  │ • Macro     │  │ • Signals   │  │ • OrderBook │  │ • Metrics   │          │  │
│  │  │ • Backtest  │  │ • Sessions  │  │ • Spreads   │  │ • Errors    │          │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
│                                          │                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐  │
│  │                           SERVICES & INTERFACES                                 │  │
│  │                                                                                 │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │  Scheduler  │  │  Monitor    │  │  REST API   │  │  CLI Tools  │          │  │
│  │  │  Service    │  │  & Health   │  │  Endpoints  │  │  Interface  │          │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │  │
│  └─────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

### Root Directory Structure

```
MTS-data-pipeline/
├── main.py                     # Main CLI entry point
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── config/                     # Configuration files
├── src/                        # Core application code
├── backtesting-engine/         # Backtesting system
├── data/                       # Data storage
├── logs/                       # Application logs
├── tests/                      # Test suites
├── examples/                   # Usage examples
└── scripts/                    # Utility scripts
```

### Core Components

#### 1. Configuration Layer (`config/`)

**Purpose**: Centralized configuration management for all system components

**Key Files**:
- `settings.py` - Main configuration class with environment-based settings
- `logging_config.py` - Logging configuration
- `exchanges/` - Exchange-specific configurations
- `strategies/` - Strategy parameter configurations

**Key Features**:
- Environment-based configuration (dev/staging/prod)
- Redis and database connection settings
- Real-time data collection parameters
- API rate limiting and timeout configurations
- Risk management parameters

#### 2. Data Layer (`src/data/`)

**Purpose**: Data models, database management, and storage interfaces

**Key Components**:

**Data Models**:
- `models.py` - Core data structures (Cryptocurrency, OHLCVData)
- `realtime_models.py` - Real-time data structures (OrderBookSnapshot, FundingRate)
- `signal_models.py` - Trading signal data structures
- `macro_models.py` - Macro-economic indicator models

**Database Management**:
- `db_connection.py` - Database connection handling
- `db_init.py` - Database initialization
- `schema.sql` - SQLite database schema
- `sqlite_helper.py` - SQLite utilities
- `storage.py` - Data persistence layer

**Data Validation**:
- `validator.py` - Data validation logic
- `data_validator.py` - Market data validation

#### 3. API Layer (`src/api/`)

**Purpose**: External API integrations and WebSocket connections

**Key Components**:

**REST API Clients**:
- `coingecko_client.py` - CoinGecko API integration
- `binance_client.py` - Binance API client
- `bybit_client.py` - Bybit API client
- `fred_client.py` - FRED economic data API

**WebSocket Connections**:
- `websockets/base_websocket.py` - Base WebSocket class
- `websockets/binance_websocket.py` - Binance WebSocket implementation
- `websockets/bybit_websocket.py` - Bybit WebSocket implementation

**Features**:
- Rate limiting and retry logic
- Connection pooling
- Real-time data streaming
- Error handling and reconnection

#### 4. Services Layer (`src/services/`)

**Purpose**: Business logic and data processing services

**Key Services**:

**Data Collection**:
- `collector.py` - Main data collection service
- `macro_collector.py` - Macro-economic data collection
- `funding_collector.py` - Funding rate collection
- `orderbook_collector.py` - Order book data collection

**Data Processing**:
- `cross_exchange_analyzer.py` - Cross-exchange arbitrage analysis
- `spread_calculator.py` - Spread calculation service
- `realtime_signal_aggregator.py` - Real-time signal processing

**System Services**:
- `scheduler.py` - Automated task scheduling
- `monitor.py` - Health monitoring and metrics
- `multi_strategy_generator.py` - Multi-strategy signal generation

#### 5. Signal Generation (`src/signals/`)

**Purpose**: Trading strategy implementation and signal generation

**Key Components**:

**Strategy Framework**:
- `strategies/base_strategy.py` - Abstract base class for strategies
- `strategies/strategy_registry.py` - Strategy management system
- `strategies/mean_reversion_strategy.py` - Mean reversion implementation
- `strategies/vix_correlation_strategy.py` - VIX correlation strategy

**Signal Processing**:
- `signal_aggregator.py` - Multi-strategy signal aggregation
- `backtest_interface.py` - Backtesting integration interface

**Features**:
- Configurable strategy parameters
- Signal confidence scoring
- Risk management integration
- Conflict resolution between strategies

#### 6. Backtesting Engine (`backtesting-engine/`)

**Purpose**: Event-driven backtesting system for strategy validation

**Architecture**:
```
backtesting-engine/
├── src/
│   ├── core/
│   │   ├── backtest_engine.py      # Main backtesting orchestrator
│   │   ├── event_manager.py        # Event handling system
│   │   └── state_manager.py        # State management
│   ├── events/
│   │   ├── base_event.py          # Base event class
│   │   ├── market_event.py        # Market data events
│   │   ├── signal_event.py        # Strategy signal events
│   │   ├── order_event.py         # Order events
│   │   └── fill_event.py          # Trade fill events
│   ├── portfolio/
│   │   ├── portfolio_manager.py   # Portfolio management
│   │   └── position.py            # Position tracking
│   ├── execution/
│   │   └── execution_handler.py   # Order execution simulation
│   ├── strategies/
│   │   ├── backtest_strategy_base.py  # Base backtest strategy
│   │   └── buy_hold_strategy.py       # Buy-and-hold strategy
│   └── analytics/
│       └── performance_calculator.py  # Performance metrics
└── config/
    └── backtest_settings.py       # Backtesting configuration
```

**Key Features**:
- Event-driven architecture
- Portfolio management with position tracking
- Execution simulation with slippage and commissions
- Performance analytics and metrics
- Strategy parameter optimization

#### 7. Utilities (`src/utils/`)

**Purpose**: Common utilities and helper functions

**Key Components**:
- `exceptions.py` - Custom exception classes
- `retry.py` - Retry logic and decorators
- `websocket_utils.py` - WebSocket utility functions

## Data Flow Architecture

### 1. Historical Data Collection Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CoinGecko     │    │   FRED API      │    │   Scheduler     │
│   API Client    │    │   Client        │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data          │    │   Macro Data    │    │   Automated     │
│   Collector     │    │   Collector     │    │   Execution     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data          │    │   Data          │    │   SQLite        │
│   Validator     │    │   Validator     │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite Database                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ crypto_ohlcv│  │ macro_       │  │ signal_     │            │
│  │ table       │  │ indicators  │  │ history     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Real-Time Data Processing Flow

```
┌─────────────────┐    ┌─────────────────┐
│   Binance       │    │   Bybit         │
│   WebSocket     │    │   WebSocket     │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   OrderBook     │    │   Funding Rate  │
│   Processor     │    │   Collector     │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Redis Cache   │    │   CSV Backup    │
│   (Real-time)   │    │   (Persistence) │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Cross-Exchange Analyzer                            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Arbitrage   │  │ Spread      │  │ Opportunity │            │
│  │ Detection   │  │ Analysis    │  │ Alerts      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Signal Generation Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market Data   │    │   Macro Data    │    │   Real-Time     │
│   (Historical)  │    │   (FRED API)    │    │   Data Stream   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VIX           │    │   Mean          │    │   Strategy      │
│   Correlation   │    │   Reversion     │    │   Registry      │
│   Strategy      │    │   Strategy      │    │   Manager       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Signal Aggregator                            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Weighted    │  │ Conflict    │  │ Risk        │            │
│  │ Combination │  │ Resolution  │  │ Management  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Final Trading Signals                       │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Signal Type │  │ Confidence  │  │ Position    │            │
│  │ (LONG/SHORT)│  │ Score       │  │ Size        │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## State Management and Storage

### Database Schema

The system uses SQLite as the primary database with the following key tables:

#### Core Tables

**crypto_ohlcv**: Historical price data
```sql
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
```

**macro_indicators**: Economic indicators
```sql
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
```

### Redis Caching Strategy

**Real-Time Data Cache**:
- Order book snapshots (TTL: 1 hour)
- Funding rates (TTL: 24 hours)
- Signal cache (TTL: 24 hours)
- WebSocket session data

**Cache Keys Pattern**:
```
orderbook:{exchange}:{symbol}:{timestamp}
funding:{exchange}:{symbol}:{timestamp}
signal:{strategy}:{asset}:{timestamp}
```

### File Storage Structure

```
data/
├── crypto_data.db              # Main SQLite database
├── backup/                     # Data backups
│   ├── bitcoin_2025.csv
│   ├── ethereum_2025.csv
│   └── tether_2025.csv
├── raw/                        # Raw data files
│   ├── funding/                # Funding rate data
│   ├── macro/                  # Macro economic data
│   ├── orderbooks/             # Order book snapshots
│   └── spreads/                # Spread data
└── realtime/                   # Real-time data
    ├── binance/                # Binance-specific data
    ├── bybit/                  # Bybit-specific data
    ├── funding/                # Real-time funding rates
    ├── orderbooks/             # Real-time order books
    └── spreads/                # Real-time spreads
```

## Service Integration and Communication

### Service Dependencies

```
┌─────────────────┐
│   Main CLI      │
│   Application   │
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Configuration │    │   Logging       │    │   Health        │
│   Manager       │    │   Service       │    │   Monitor       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data          │    │   Signal        │    │   Backtesting   │
│   Collectors    │    │   Generators    │    │   Engine        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  SQLite DB  │  │  Redis Cache│  │  File System│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Inter-Service Communication

**Service Communication Patterns**:
1. **Direct Method Calls**: For synchronous operations within the same process
2. **Database Queues**: For asynchronous task processing
3. **Redis Pub/Sub**: For real-time event notifications
4. **File System**: For bulk data exchange and persistence

### Error Handling and Recovery

**Custom Exception Hierarchy**:
```python
CryptoDataPipelineError
├── APIError
│   ├── APIRateLimitError
│   ├── APIConnectionError
│   └── APITimeoutError
├── DataValidationError
├── StorageError
└── BacktestingError
    ├── DataError
    ├── StrategyError
    ├── ConfigurationError
    └── ExecutionError
```

**Recovery Strategies**:
- **Exponential Backoff**: For API rate limiting
- **Circuit Breaker**: For failing external services
- **Retry Logic**: For transient failures
- **Graceful Degradation**: For non-critical components

## Deployment and Operations

### Environment Configuration

**Development Environment**:
- Local SQLite database
- File-based logging
- Reduced API rate limits
- Debug mode enabled

**Production Environment**:
- Optimized database configuration
- Structured JSON logging
- Full API rate limits
- Monitoring and alerting enabled

### Monitoring and Health Checks

**Health Check Endpoints**:
```
GET /health - System health status
```

**Monitored Components**:
- Database connectivity
- API client health
- Redis connection status
- WebSocket connection status
- Service response times

### Scalability Considerations

**Current Architecture Limitations**:
- Single-process design
- SQLite database limitations
- No horizontal scaling support

**Future Scalability Improvements**:
- Multi-process architecture
- PostgreSQL migration
- Microservices decomposition
- Container orchestration

## API and Integration Points

### CLI Interface

**Main Commands**:
```bash
# Data Collection
python main.py --collect --days 7
python main.py --collect-macro --macro-indicators VIX DXY

# Scheduled Operations
python main.py --schedule --collect --interval 30
python main.py --schedule --collect-macro --interval 360

# Monitoring
python main.py --server --port 8080

# Backtesting
python main.py --symbols bitcoin --start 2023-01-01 --end 2023-12-31 --strategy BuyHoldStrategy
```

### REST API Endpoints

**Health and Status**:
- `GET /health` - System health check
- `GET /metrics` - Performance metrics

**Data Access** (Future Implementation):
- `GET /api/v1/crypto/{symbol}/ohlcv` - Historical price data
- `GET /api/v1/signals/{strategy}` - Trading signals
- `GET /api/v1/backtest/results` - Backtesting results

### WebSocket Streams

**Real-Time Data Streams**:
- Order book updates
- Funding rate changes
- Price alerts
- Signal notifications

## Security Considerations

### API Security

**Rate Limiting**:
- Per-endpoint rate limiting
- API key rotation
- Request throttling

**Data Protection**:
- Input validation
- SQL injection prevention
- Secure configuration management

### Access Control

**Authentication**:
- API key authentication
- JWT token support (planned)
- Role-based access control (planned)

**Data Privacy**:
- Sensitive data encryption
- Secure credential storage
- Audit logging

## Testing Strategy

### Test Structure

```
tests/
├── unit/                       # Unit tests
│   ├── test_backtest_engine.py
│   ├── test_signal_aggregator.py
│   ├── test_collector.py
│   └── ...
├── integration/                # Integration tests
│   ├── test_end_to_end.py
│   ├── test_realtime_integration.py
│   └── ...
└── fixtures/                   # Test data and fixtures
```

### Test Coverage

**Unit Tests**:
- Data models and validation
- API clients and error handling
- Signal generation algorithms
- Backtesting components

**Integration Tests**:
- End-to-end data flow
- Database operations
- WebSocket connections
- Multi-service interactions

## Development Workflow

### Code Organization

**Module Structure**:
- Clear separation of concerns
- Dependency injection patterns
- Abstract base classes for extensibility
- Configuration-driven behavior

**Code Quality**:
- Type hints throughout
- Comprehensive docstrings
- Error handling best practices
- Structured logging

### Development Tools

**Required Tools**:
- Python 3.9+
- SQLite 3
- Redis (for caching)
- pytest (for testing)

**Development Setup**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py --version
```

## Future Enhancements

### Planned Features

**Short-term (Next 3 months)**:
- Enhanced backtesting metrics
- Additional trading strategies
- Real-time alert system
- Performance optimization

**Medium-term (3-6 months)**:
- Machine learning integration
- Advanced risk management
- Multi-asset portfolio support
- Web-based dashboard

**Long-term (6+ months)**:
- Microservices architecture
- Cloud deployment
- Real-time trading execution
- Advanced analytics platform

### Technical Debt

**Current Issues**:
- Monolithic architecture
- Limited error recovery
- Manual configuration management
- Basic logging and monitoring

**Improvement Priorities**:
1. Implement comprehensive error handling
2. Add automated testing pipeline
3. Improve configuration management
4. Enhance monitoring and alerting
5. Optimize database performance

## Conclusion

The MTS Cryptocurrency Data Pipeline represents a comprehensive solution for cryptocurrency trading strategy development and deployment. The architecture provides a solid foundation for data collection, signal generation, and backtesting while maintaining flexibility for future enhancements.

The modular design allows for easy extension and modification of components, while the event-driven backtesting engine provides robust strategy validation capabilities. The system's emphasis on error handling, monitoring, and data validation ensures reliable operation in production environments.

Key strengths include:
- Comprehensive data collection from multiple sources
- Real-time processing capabilities
- Flexible signal generation framework
- Robust backtesting engine
- Extensive configuration options

Areas for improvement include:
- Scalability limitations
- Monitoring and alerting capabilities
- Documentation and testing coverage
- Performance optimization

The architecture provides a strong foundation for building sophisticated cryptocurrency trading systems and can be extended to support more advanced features as requirements evolve. 