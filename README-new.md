# MTS Cryptocurrency Data Pipeline

A comprehensive cryptocurrency trading infrastructure system that combines multi-source data collection, real-time market analysis, signal generation, and event-driven backtesting capabilities. The MTS (Multi-Timeframe Signal) pipeline is designed for quantitative cryptocurrency trading strategy development and deployment.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- SQLite 3
- Redis (optional, for caching)
- API Keys (see Environment Variables section)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd MTS-data-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables (see section below)
cp .env.example .env  # Edit with your API keys
```

### Basic Usage

#### 1. Data Collection

```bash
# Collect latest crypto data (1 day)
python3 main.py --collect

# Collect 7 days of historical data
python3 main.py --collect --days 7

# Collect macro-economic indicators
python3 main.py --collect-macro

# Collect specific macro indicators
python3 main.py --collect-macro --macro-indicators VIX DXY

# Collect both crypto and macro data
python3 main.py --collect --collect-macro
```

#### 2. Automated Scheduling

```bash
# Schedule crypto data collection every 60 minutes
python3 main.py --schedule --collect

# Schedule macro data collection every 6 hours
python3 main.py --schedule --collect-macro --interval 360

# Schedule both with custom interval (30 minutes)
python3 main.py --schedule --collect --collect-macro --interval 30
```

#### 3. Health Monitoring

```bash
# Start health monitoring server
python3 main.py --server

# Custom port
python3 main.py --server --port 9090
```

#### 4. Backtesting

```bash
# Run backtest with buy-and-hold strategy
python3 main.py --symbols bitcoin --start 2023-01-01 --end 2023-12-31 --strategy BuyHoldStrategy --capital 100000

# Multiple assets
python3 main.py --symbols bitcoin ethereum --start 2023-01-01 --end 2023-06-30 --strategy BuyHoldStrategy
```

## 📊 System Overview

### Core Components

The MTS pipeline consists of four main components:

1. **Data Sources & Collection**
   - CoinGecko API for historical crypto data (with automatic Pro/Free API fallback)
   - FRED API for macro-economic indicators
   - Binance & Bybit WebSockets for real-time data
   - Order book and funding rate streams
   - Resilient API clients with automatic error recovery

2. **Signal Generation Engine**
   - VIX Correlation Strategy
   - Mean Reversion Strategy
   - Multi-strategy aggregation with conflict resolution
   - Risk management and position sizing

3. **Event-Driven Backtesting**
   - Portfolio management with position tracking
   - Execution simulation with slippage and commissions
   - Performance analytics and metrics
   - Strategy parameter optimization

4. **Storage & Caching**
   - SQLite database for persistent storage
   - Redis for real-time data caching
   - CSV backups for data redundancy
   - Structured logging system

### Data Flow

```
External APIs → Data Collectors → Validators → Database → Signal Strategies → Trading Signals
     ↓                                                                              ↓
WebSocket Streams → Real-time Processors → Redis Cache → Cross-Exchange Analysis → Alerts
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Keys (Required)
COINGECKO_API_KEY=your_coingecko_api_key
FRED_API_KEY=your_fred_api_key

# Environment
ENVIRONMENT=development  # development, staging, production
DEBUG=true

# Database
DATABASE_PATH=data/crypto_data.db

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Real-time Data
REALTIME_ENABLED=true
REALTIME_SYMBOLS=BTCUSDT,ETHUSDT,XRPUSDT,TAOUSDT,FETUSDT,AGIXUSDT,RNDRUSDT,OCEANUSDT
REALTIME_EXCHANGES=binance

# Signal Generation
ENABLED_STRATEGIES=vix_correlation,mean_reversion
SIGNAL_GENERATION_INTERVAL_MINUTES=60

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_SECRET_KEY=your-secret-key-change-in-production

# Risk Management
MAX_POSITION_SIZE=0.10
MAX_DAILY_TRADES=50
MAX_PORTFOLIO_RISK=0.25
```

### Strategy Configuration

Strategies are configured via JSON files in `config/strategies/`:

**VIX Correlation Strategy** (`config/strategies/vix_correlation.json`):
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

**Mean Reversion Strategy** (`config/strategies/mean_reversion.json`):
```json
{
  "name": "Mean_Reversion_Strategy",
  "assets": ["bitcoin", "ethereum", "binancecoin"],
  "vix_spike_threshold": 25,
  "drawdown_threshold": 0.10,
  "lookback_days": 14,
  "position_size": 0.025
}
```

## 📁 Project Structure

```
MTS-data-pipeline/
├── main.py                     # CLI entry point
├── requirements.txt            # Dependencies
├── config/                     # Configuration files
│   ├── settings.py            # Main configuration
│   ├── logging_config.py      # Logging setup
│   ├── exchanges/             # Exchange configs
│   └── strategies/            # Strategy parameters
├── src/                       # Core application code
│   ├── api/                   # External API clients
│   │   ├── coingecko_client.py
│   │   ├── fred_client.py
│   │   ├── binance_client.py
│   │   ├── bybit_client.py
│   │   └── websockets/        # WebSocket implementations
│   ├── data/                  # Data models & storage
│   │   ├── models.py          # Core data structures
│   │   ├── realtime_models.py # Real-time data models
│   │   ├── signal_models.py   # Trading signal models
│   │   ├── sqlite_helper.py   # Database utilities
│   │   └── storage.py         # Data persistence
│   ├── services/              # Business logic services
│   │   ├── collector.py       # Data collection orchestrator
│   │   ├── macro_collector.py # Economic data collection
│   │   ├── scheduler.py       # Automated scheduling
│   │   ├── monitor.py         # Health monitoring
│   │   └── cross_exchange_analyzer.py  # Arbitrage analysis
│   ├── signals/               # Signal generation
│   │   ├── signal_aggregator.py
│   │   ├── backtest_interface.py
│   │   └── strategies/        # Trading strategies
│   │       ├── base_strategy.py
│   │       ├── vix_correlation_strategy.py
│   │       ├── mean_reversion_strategy.py
│   │       └── strategy_registry.py
│   └── utils/                 # Utilities
│       ├── exceptions.py      # Custom exceptions
│       ├── retry.py          # Retry logic
│       └── websocket_utils.py # WebSocket helpers
├── backtesting-engine/        # Event-driven backtesting
│   ├── src/
│   │   ├── core/             # Core engine components
│   │   │   ├── backtest_engine.py
│   │   │   ├── event_manager.py
│   │   │   └── state_manager.py
│   │   ├── events/           # Event system
│   │   │   ├── base_event.py
│   │   │   ├── market_event.py
│   │   │   ├── signal_event.py
│   │   │   ├── order_event.py
│   │   │   └── fill_event.py
│   │   ├── portfolio/        # Portfolio management
│   │   │   ├── portfolio_manager.py
│   │   │   └── position.py
│   │   ├── execution/        # Order execution
│   │   │   └── execution_handler.py
│   │   └── analytics/        # Performance analysis
│   │       └── performance_calculator.py
│   ├── config/               # Backtest configuration
│   │   └── backtest_settings.py
│   └── tests/               # Backtest tests
├── data/                    # Data storage
│   ├── crypto_data.db      # Main SQLite database
│   ├── backup/             # Data backups
│   ├── raw/                # Raw data files
│   └── realtime/           # Real-time data streams
├── scripts/                # Utility scripts
│   ├── fetch_and_import_data.py
│   ├── migrate_csv_to_sqlite.py
│   └── calc_rolling_volatility.py
├── tests/                  # Test suites
├── examples/               # Usage examples
└── logs/                   # Application logs
```

## 🤖 Trading Strategies

### 1. VIX Correlation Strategy

Generates signals based on correlation between VIX and cryptocurrency prices:

- **LONG signals**: When VIX-crypto correlation < -0.6 (strong negative correlation)
- **SHORT signals**: When VIX-crypto correlation > 0.6 (strong positive correlation)
- **Logic**: Exploits changing market dynamics between fear index and crypto markets

### 2. Mean Reversion Strategy

Identifies mean reversion opportunities during market stress:

- **LONG signals**: When VIX > 25 AND crypto drawdown > 10%
- **Logic**: High VIX + oversold crypto conditions create bounce opportunities
- **Risk Management**: Adaptive position sizing based on VIX levels

### 3. Multi-Strategy Aggregation

- Combines signals from multiple strategies
- Weighted signal combination with confidence scoring
- Conflict resolution algorithms
- Risk management and position size optimization

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest backtesting-engine/tests/

# Run with coverage
pytest --cov=src
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Backtest Tests**: Strategy and engine validation
- **API Tests**: External API integration testing

## 📈 Performance Metrics

The system calculates comprehensive performance metrics:

- **Returns**: Total return, annualized return, daily returns
- **Risk Metrics**: Sharpe ratio, maximum drawdown, volatility
- **Trade Analysis**: Win rate, average trade duration, profit factor
- **Portfolio Analytics**: Position sizing, risk exposure, correlation analysis

## 🔌 API Integration

### REST API (Development)

The system includes a FastAPI server for programmatic access:

```python
# Start API server
from src.api.signal_api import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Endpoints**:
- `GET /health` - System health check
- `POST /signals/generate` - Generate trading signals
- `POST /backtest` - Run strategy backtest
- `GET /strategies` - List available strategies

### WebSocket Streams

Real-time data streams for:
- Order book updates (Binance, Bybit)
- Funding rate changes
- Price alerts and signal notifications
- Cross-exchange arbitrage opportunities

## 🚨 Monitoring & Alerts

### Health Monitoring

```bash
# Check system status
curl http://localhost:8080/health

# View metrics
curl http://localhost:8080/metrics
```

### Log Analysis

Structured logging with configurable levels:
- Application logs: `logs/mts_pipeline.log`
- Real-time streams: `logs/streams/`
- Performance metrics: `logs/metrics/`

## 🔒 Security & Risk Management

### API Security

- Rate limiting on all external API calls
- API key rotation and secure storage
- Input validation and sanitization
- SQL injection prevention

### Risk Management

- Position size limits (default: 10% max)
- Daily trade limits (default: 50 trades)
- Portfolio risk exposure limits (default: 25%)
- Stop-loss and take-profit automation

## 🔧 API Resilience & Error Handling

### CoinGecko API Fallback System

The system now includes an intelligent fallback mechanism for CoinGecko API requests:

#### **Automatic Pro/Free API Switching**
```python
# Automatic configuration based on API key
from src.api.coingecko_client import CoinGeckoClient

client = CoinGeckoClient()  # Automatically detects Pro vs Free API
# Pro API key (CG-xxx): Uses pro-api.coingecko.com with fallback to api.coingecko.com
# Free usage: Uses api.coingecko.com only
```

#### **Resilience Features**
- **Connection Failures**: Automatically tries fallback URL
- **DNS Resolution Errors**: Seamless failover to backup endpoint
- **Timeout Handling**: Retries with exponential backoff
- **Rate Limit Respect**: Proper handling without fallback for 429 errors
- **Error Transparency**: Clear error messages for debugging

#### **Fallback Logic**
1. **Primary Attempt**: Uses Pro API with authentication headers
2. **Fallback Attempt**: Uses Free API without authentication if Pro fails
3. **Error Handling**: Returns detailed error information if both fail

#### **Testing API Connectivity**
```bash
# Test CoinGecko connectivity with fallback
python3 -c "
from src.api.coingecko_client import CoinGeckoClient
client = CoinGeckoClient()
try:
    result = client.ping()
    print('✓ CoinGecko API connectivity successful')
    print(f'Base URL: {client.base_url}')
    if hasattr(client, 'fallback_url'):
        print(f'Fallback URL: {client.fallback_url}')
except Exception as e:
    print(f'✗ API connectivity failed: {e}')
"

# Test market data retrieval
python3 -c "
from src.api.coingecko_client import CoinGeckoClient
client = CoinGeckoClient()
data = client.get_market_chart_data('bitcoin', 1)
print(f'✓ Retrieved {len(data[\"prices\"])} price points')
"
```

### Error Recovery Strategies

#### **Automatic Recovery**
- **Exponential Backoff**: Increasing delays between retries
- **Circuit Breaker Pattern**: Temporary failure isolation
- **Graceful Degradation**: Continue with available data sources

#### **Manual Recovery**
```bash
# Force API client reset
python3 -c "
from src.api.coingecko_client import CoinGeckoClient
client = CoinGeckoClient()
print('API Status:', 'OK' if client.ping() else 'Failed')
"

# Check data pipeline health
python3 main.py --health
```

### Common Issues & Troubleshooting

#### **DNS Resolution Errors (CoinGecko API)**

**Problem**: Error messages like:
```
NameResolutionError: Failed to resolve 'pro-api.coingecko.com'
[APICONNECTIONERROR] Failed to connect to API: HTTPSConnectionPool(host='pro-api.coingecko.com', port=443)
```

**Solution**: The enhanced CoinGecko client automatically handles this with fallback:
```bash
# Test connectivity
python3 -c "
from src.api.coingecko_client import CoinGeckoClient
client = CoinGeckoClient()
try:
    result = client.get_market_chart_data('bitcoin', 1)
    print(f'✓ Success: {len(result[\"prices\"])} price points retrieved')
except Exception as e:
    print(f'✗ Still failing: {e}')
"
```

**Manual Workaround** (if needed):
```python
# Force free API usage
import os
os.environ['COINGECKO_API_KEY'] = ''  # Remove Pro API key temporarily
from src.api.coingecko_client import CoinGeckoClient
client = CoinGeckoClient()  # Will use free API only
```

#### **API Rate Limiting**

**Problem**: `429 Too Many Requests` errors

**Solution**:
- Pro API: 500 calls/minute limit
- Free API: 10-50 calls/minute limit
- System automatically respects rate limits and retries

```bash
# Check current rate limit usage
grep "rate limit" logs/*.log | tail -10
```

#### **Data Collection Failures**

**Problem**: Incomplete or failed data collection

**Diagnosis**:
```bash
# Check recent collection status
python3 -c "
from src.services.collector import DataCollector
collector = DataCollector()
status = collector.get_collection_status()
print(f'Success rate: {status[\"success_rate\"]:.1%}')
print(f'Failed assets: {status[\"failed_assets\"]}')
"
```

## 🚀 Production Deployment

### Environment Setup

1. **Database**: PostgreSQL recommended for production
2. **Caching**: Redis cluster for high availability
3. **Monitoring**: Prometheus + Grafana integration
4. **Logging**: ELK stack or centralized logging service

### Scaling Considerations

- Horizontal scaling via microservices decomposition
- Load balancing for API endpoints
- Database read replicas for analytics
- Container orchestration (Docker + Kubernetes)

## 🛠️ Development

### Code Quality

- Type hints throughout codebase
- Comprehensive docstrings
- Error handling best practices
- Structured logging with context

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Tools

```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

## 📚 Examples

### Data Collection Example

```python
from src.services.collector import DataCollector
from config.settings import Config

# Initialize collector
config = Config()
collector = DataCollector()

# Collect 7 days of data
results = collector.collect_all_data(days=7)
print(f"Collected data for {results['successful']} cryptocurrencies")
```

### Signal Generation Example

```python
from src.signals.strategies.strategy_registry import StrategyRegistry
from src.signals.signal_aggregator import SignalAggregator

# Load strategies
registry = StrategyRegistry()
vix_strategy = registry.get_strategy('vix_correlation', 'config/strategies/vix_correlation.json')

# Generate signals
analysis = vix_strategy.analyze({})
signals = vix_strategy.generate_signals(analysis)

for signal in signals:
    print(f"{signal.signal_type.value} {signal.asset} @ {signal.price} (confidence: {signal.confidence:.2f})")
```

### Backtesting Example

```python
from datetime import datetime, timedelta
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig

# Configure backtest
config = BacktestConfig(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=100000.0,
    strategies=["BuyHoldStrategy"],
    symbols=["bitcoin"]
)

# Run backtest
engine = BacktestEngine(config)
result = engine.run_backtest()

print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.3f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
```

## 📋 Recent Updates & Changelog

### Version 2.1.0 - Enhanced API Resilience (Latest)

#### 🔧 **CoinGecko Client Improvements**
- **Added automatic fallback mechanism** for Pro API to Free API switching
- **Enhanced error handling** for DNS resolution and connectivity issues
- **Centralized request logic** with `_make_request_with_fallback()` method
- **Improved reliability** for all CoinGecko API endpoints
- **Backwards compatible** - no code changes required

#### ✨ **Key Features**
- **Seamless Failover**: Automatically switches to Free API when Pro API is unreachable
- **Smart Error Detection**: Distinguishes between network issues and API errors
- **Proper Header Management**: Uses API key only for Pro endpoint requests
- **Comprehensive Testing**: Verified fallback mechanism with connection simulation

#### 🐛 **Bug Fixes**
- **Fixed DNS resolution errors** for `pro-api.coingecko.com`
- **Improved timeout handling** with automatic retries
- **Enhanced connection error recovery** with fallback URLs

#### 🚀 **Performance Improvements**
- **Reduced code duplication** in API client methods
- **Faster error recovery** through intelligent fallback logic
- **Better resource utilization** with centralized request handling

### Previous Updates

#### Version 2.0.0 - Multi-Tier Scheduling System
- **Optimized data collection** with tier-based scheduling
- **Enhanced macro analytics** with correlation analysis
- **Improved signal generation** with confidence scoring
- **Real-time monitoring** and health checks

#### Version 1.5.0 - Backtesting Engine
- **Event-driven backtesting** framework
- **Portfolio management** with position tracking
- **Performance analytics** with comprehensive metrics
- **Strategy optimization** tools

## 📞 Support

- **Documentation**: See `docs/` directory for detailed guides
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss. Past performance is not indicative of future results. Always conduct your own research and consider your financial situation before making trading decisions. 