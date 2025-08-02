# Paper Trading Engine

A modular paper trading system that processes MTS signals and executes simulated trades.

## Project Structure

```
paper_trading_engine/
├── config/
│   └── settings.py        # Configuration management
├── src/
│   ├── core/
│   │   ├── models.py      # Core data models
│   │   └── enums.py       # Enumerations
│   ├── signal_consumer/
│   │   ├── mts_consumer.py    # MTS alert directory monitoring
│   │   ├── signal_processor.py # Alert to signal conversion
│   │   └── filters.py     # Signal validation & filtering
│   ├── storage/
│   │   └── state_manager.py # JSON persistence
│   └── utils/
│       └── logger.py      # Logging configuration
├── logs/                  # Log files
├── data/                  # Data storage & JSON files
│   └── alerts/            # MTS alert monitoring directory
├── test_task1.py          # Task 1 validation test
├── test_task2.py          # Task 2 validation test
├── test_task3.py          # Task 3 validation test
├── test_task4.py          # Task 4 validation test
├── .env.example           # Environment variables template
└── README.md
```

## Task 1 Complete ✅
## Task 2 Complete ✅ 
## Task 3 Complete ✅
## Task 4 Complete ✅

**Models Implemented:**
- `TradingSignal` - MTS signal data
- `Order` - Trading order  
- `ExecutionResult` - Trade execution result
- `Position` - Portfolio position
- `Trade` - Completed trade record

**Enums Implemented:**
- `SignalType` - LONG/SHORT
- `OrderType` - MARKET/LIMIT/STOP/STOP_LIMIT  
- `OrderSide` - BUY/SELL

**Test Status:** All models can be imported, instantiated, and validated ✅

**Configuration & Logging Implemented:**
- `Config` class with environment variable support
- Structured logging with file and console output
- Configurable log levels and file rotation
- Component-specific loggers

**Test Status:** Config loads from environment, logs appear in files and console ✅

**JSON State Persistence Implemented:**
- `StateManager` class for portfolio and trade history persistence
- Atomic file operations with temporary files
- Proper datetime serialization/deserialization
- Automatic backup functionality  
- Handles both portfolio state and trade history

**Test Status:** Save state, restart, verify data restored correctly ✅

**MTS Signal Consumer Implemented:**
- `MTSSignalConsumer` for real-time directory monitoring
- `SignalProcessor` for converting MTS alerts to TradingSignal objects (production-hardened)
- `SignalFilters` for alert validation and filtering
- File system watcher with automatic processing
- Support for volatility spike alerts with confidence scoring
- Asset mapping (bitcoin→BTCUSDT, ethereum→ETHUSDT)

**Production Improvements Applied:**
- UTC timezone handling for all timestamps
- Division by zero protection in confidence calculations
- Comprehensive input validation for all alert fields
- Constants replacing magic numbers for maintainability
- Enhanced error handling with specific exception types
- Volatility percentile normalization (handles both 0-1 and 0-100 ranges)

**MTS Consumer Production Hardening:**
- Race condition prevention with file lock checking
- Memory leak prevention with signal history limits (1000 max)
- Observer thread cleanup improvements with timeout handling
- Duplicate file processing prevention (thread-safe tracking)
- File handle improvements with UTF-8 encoding
- Exception handling improvements in status methods
- Thread safety for concurrent operations
- File validation (path traversal protection, size limits)
- Comprehensive metrics tracking and health checks

**Test Status:** Drop alert file, verify parsing and validation ✅ (including all production hardening validated)

## Usage

```python
from src.core.models import TradingSignal, Order, Position, Trade
from src.core.enums import SignalType, OrderSide
from config.settings import Config
from src.utils.logger import setup_logging, get_logger
from src.storage.state_manager import StateManager
from src.signal_consumer.mts_consumer import MTSSignalConsumer

# Load configuration
config = Config.from_env()

# Set up logging
logger = setup_logging(config)
portfolio_logger = get_logger('portfolio')

# Set up state management
state_manager = StateManager(config)

# Set up MTS signal consumer
signal_consumer = MTSSignalConsumer(config)

# Start monitoring MTS alerts
signal_consumer.start_monitoring()
logger.info("Started monitoring MTS alerts...")

# The consumer will automatically:
# 1. Monitor data/alerts/ directory for new JSON files
# 2. Parse and validate MTS volatility alerts
# 3. Convert valid alerts to TradingSignal objects
# 4. Filter signals based on volatility percentile (>90th)

# Get processed signals
processed_signals = signal_consumer.get_processed_signals()
for signal in processed_signals:
    logger.info(f"Signal: {signal.asset} {signal.signal_type.value} @ ${signal.price:.2f}")

# Save/load portfolio state
portfolio_state = {
    'initial_capital': 10000.0,
    'cash': 8500.0,
    'positions': {'BTCUSDT': {'quantity': 0.03, 'average_price': 50000.0}},
    'total_value': 10500.0
}

# Save state
state_manager.save_portfolio_state(portfolio_state)

# Load state (e.g., after restart)
restored_state = state_manager.load_portfolio_state()

# Stop monitoring when done
signal_consumer.stop_monitoring()
```