# Event-Driven Backtesting Engine MVP - Step-by-Step Build Plan

## Phase 1: Foundation & Core Infrastructure

### Task 1: Project Structure Setup
**Objective**: Create basic directory structure and configuration
- Create directory structure as per architecture
- Add `__init__.py` files to all packages
- Create `requirements.txt` with core dependencies: `pandas`, `sqlite3`, `pytest`, `dataclasses`
- **Test**: Directory structure exists, imports work

### Task 2: Base Event System
**Objective**: Implement abstract event base class
- Create `src/events/base_event.py` with `BaseEvent` abstract class
- Include: `timestamp`, `event_type`, `event_id` fields
- Add `__str__` and `__repr__` methods
- **Test**: Can instantiate concrete event subclass, fields populate correctly

### Task 3: Market Event Implementation
**Objective**: Create market data event class
- Create `src/events/market_event.py` inheriting from `BaseEvent`
- Include: `symbol`, `open`, `high`, `low`, `close`, `volume` fields
- Add validation for positive prices and volume
- **Test**: Create market event with OHLCV data, validation works

### Task 4: Basic Configuration
**Objective**: Implement core backtesting configuration
- Create `config/backtest_settings.py` with `BacktestConfig` dataclass
- Include: `start_date`, `end_date`, `initial_capital`, `symbols`
- Add basic validation (end_date > start_date, positive capital)
- **Test**: Create config object, validation catches invalid inputs

### Task 5: MTS Database Connection
**Objective**: Connect to MTS SQLite database
- Create `src/data/data_loader.py` with `DataLoader` class
- Implement `__init__` method to connect to SQLite database
- Add `test_connection()` method to verify database exists
- **Test**: Connect to test database, connection succeeds

## Phase 2: Data Layer

### Task 6: Market Data Loading
**Objective**: Load OHLCV data from MTS database
- Add `load_market_data()` method to `DataLoader`
- Query `crypto_ohlcv` table for single symbol and date range
- Return pandas DataFrame with timestamp index
- **Test**: Load Bitcoin data for 7-day period, verify data structure

### Task 7: Market Data Provider
**Objective**: Convert DataFrame to market events
- Create `src/data/market_data_provider.py` with `MarketDataProvider` class
- Implement `generate_market_events()` method returning iterator
- Convert DataFrame rows to `MarketEvent` objects chronologically
- **Test**: Generate events from test data, verify chronological order

### Task 8: Data Validation
**Objective**: Validate market data quality
- Create `src/data/data_validator.py` with `DataValidator` class
- Implement `validate_ohlcv()` method checking: no nulls, positive values, high >= low
- Add `validate_chronological()` method for timestamp ordering
- **Test**: Validate good and bad data, proper error detection

## Phase 3: Portfolio Management

### Task 9: Position Class
**Objective**: Track individual asset positions
- Create `src/portfolio/position.py` with `Position` class
- Include: `symbol`, `quantity`, `average_cost`, `unrealized_pnl`
- Implement `update_position()` method for quantity/cost changes
- **Test**: Create position, update with trades, verify calculations

### Task 10: Basic Portfolio Manager
**Objective**: Manage portfolio state and cash
- Create `src/portfolio/portfolio_manager.py` with `PortfolioManager` class
- Include: `initial_capital`, `cash_balance`, `positions` dict
- Implement `get_portfolio_value()` method
- **Test**: Create portfolio, verify initial state and value calculation

### Task 11: Portfolio Updates from Fills
**Objective**: Update portfolio when trades execute
- Add `process_fill()` method to `PortfolioManager`
- Update cash balance and position based on fill quantity/price
- Handle new positions and position updates
- **Test**: Process buy/sell fills, verify cash and position updates

## Phase 4: Event Processing

### Task 12: Event Manager
**Objective**: Process events in chronological order
- Create `src/core/event_manager.py` with `EventManager` class
- Use `heapq` for time-ordered event queue
- Implement `add_event()` and `get_next_event()` methods
- **Test**: Add events out of order, retrieve in chronological order

### Task 13: State Manager
**Objective**: Centralized state tracking
- Create `src/core/state_manager.py` with `StateManager` class
- Track: `current_time`, `portfolio_state`, `current_prices`
- Implement `update_state()` method for different event types
- **Test**: Update state with market events, verify state changes

### Task 14: Signal Event Implementation
**Objective**: Create trading signal events
- Create `src/events/signal_event.py` with `SignalEvent` class
- Include: `symbol`, `signal_type` (BUY/SELL/HOLD), `strength`, `strategy`
- Add validation for signal_type and strength (0-1)
- **Test**: Create signal events, validation works correctly

## Phase 5: Order Execution

### Task 15: Order Event Implementation
**Objective**: Create order placement events
- Create `src/events/order_event.py` with `OrderEvent` class
- Include: `symbol`, `order_type` (MARKET), `quantity`, `direction` (BUY/SELL)
- Add validation for positive quantity
- **Test**: Create order events, validation works

### Task 16: Fill Event Implementation
**Objective**: Create order execution events
- Create `src/events/fill_event.py` with `FillEvent` class
- Include: `symbol`, `quantity`, `fill_price`, `commission`
- Add method to calculate total cost including commission
- **Test**: Create fill events, cost calculation correct

### Task 17: Basic Execution Handler
**Objective**: Convert orders to fills with simple execution
- Create `src/execution/execution_handler.py` with `ExecutionHandler` class
- Implement `execute_market_order()` method
- Use current market price, add fixed commission (0.1%)
- **Test**: Execute buy/sell orders, verify fill prices and commissions

## Phase 6: Simple Strategy

### Task 18: Strategy Base Class
**Objective**: Abstract base for backtesting strategies
- Create `src/strategies/backtest_strategy_base.py` with `BacktestStrategy` class
- Define abstract methods: `generate_signals()`, `get_name()`
- Include portfolio reference for position-aware strategies
- **Test**: Create concrete strategy subclass, methods callable

### Task 19: Buy-and-Hold Strategy
**Objective**: Simple strategy for testing
- Create `src/strategies/buy_hold_strategy.py` inheriting from base
- Generate single BUY signal at start, HOLD thereafter
- Implement position sizing (fixed percentage of portfolio)
- **Test**: Generate signals for test period, verify signal sequence

### Task 20: Strategy Signal Generation
**Objective**: Convert strategy logic to signal events
- Add `process_market_data()` method to strategy base class
- Generate `SignalEvent` objects based on strategy logic
- Handle strategy state between market data updates
- **Test**: Process market data, verify signal events generated

## Phase 7: Core Engine

### Task 21: Basic Backtest Engine
**Objective**: Orchestrate backtesting process
- Create `src/core/backtest_engine.py` with `BacktestEngine` class
- Initialize: event_manager, state_manager, portfolio_manager, execution_handler
- Implement basic `run_backtest()` method skeleton
- **Test**: Create engine, initialize components successfully

### Task 22: Market Data Event Loop
**Objective**: Process market data chronologically
- Add market data loading to `run_backtest()`
- Generate market events and add to event queue
- Process events in chronological order, update state
- **Test**: Run backtest with market data, events processed in order

### Task 23: Strategy Integration
**Objective**: Integrate strategy signal generation
- Add strategy initialization to backtest engine
- Process market events through strategies
- Generate signal events and add to queue
- **Test**: Run backtest with buy-hold strategy, signals generated

### Task 24: Order Processing Integration
**Objective**: Convert signals to orders and fills
- Add signal-to-order conversion logic
- Process order events through execution handler
- Generate fill events and update portfolio
- **Test**: Complete backtest run, verify trades executed

## Phase 8: Basic Analytics

### Task 25: Performance Tracking
**Objective**: Track portfolio value over time
- Create `src/analytics/performance_calculator.py` with `PerformanceCalculator` class
- Track daily portfolio values and returns
- Implement `calculate_total_return()` method
- **Test**: Calculate returns for test backtest, verify accuracy

### Task 26: Basic Risk Metrics
**Objective**: Calculate Sharpe ratio and maximum drawdown
- Add `calculate_sharpe_ratio()` method to performance calculator
- Add `calculate_max_drawdown()` method
- Use pandas for efficient calculations
- **Test**: Calculate metrics for test data, verify formulas

### Task 27: Results Data Structure
**Objective**: Structured results output
- Create `src/database/backtest_models.py` with `BacktestResult` dataclass
- Include: total_return, sharpe_ratio, max_drawdown, trade_count
- Add portfolio_values and trade_history lists
- **Test**: Create result object, all fields populate correctly

## Phase 9: Results Storage

### Task 28: Results Database Schema
**Objective**: Create SQLite schema for results
- Create `src/database/schema.sql` with basic tables
- Tables: `backtest_runs`, `performance_metrics`, `trade_executions`
- Include primary keys and foreign key relationships
- **Test**: Create database from schema, tables exist

### Task 29: Results Database Operations
**Objective**: Save backtest results to database
- Create `src/database/results_db.py` with `ResultsDB` class
- Implement `save_backtest_run()` method
- Save run metadata, performance metrics, and trades
- **Test**: Save test backtest results, verify database entries

### Task 30: Results Retrieval
**Objective**: Load saved backtest results
- Add `load_backtest_run()` method to `ResultsDB`
- Add `list_backtest_runs()` method for run history
- Return structured `BacktestResult` objects
- **Test**: Save and load backtest, verify data integrity

## Phase 10: Integration & Testing

### Task 31: End-to-End Integration Test
**Objective**: Complete backtesting workflow
- Create integration test running full backtest
- Use real MTS data for 30-day period
- Verify all components work together
- **Test**: Complete backtest runs without errors, produces results

### Task 32: Main Entry Point
**Objective**: Command-line interface for backtesting
- Create `main.py` with argument parsing
- Support: symbol selection, date range, strategy choice
- Display basic results summary
- **Test**: Run backtest via command line, results displayed

### Task 33: Error Handling
**Objective**: Graceful error handling throughout system
- Add try-catch blocks in critical methods
- Create custom exceptions in `src/utils/exceptions.py`
- Log errors appropriately
- **Test**: Trigger error conditions, verify graceful handling

### Task 34: Documentation & Examples
**Objective**: Usage documentation and examples
- Create `examples/simple_backtest.py` with basic usage
- Add docstrings to all public methods
- Create basic README with setup instructions
- **Test**: Follow README to set up and run example

### Task 35: Performance Validation
**Objective**: Verify backtest accuracy
- Create test with known expected results
- Compare calculated returns with manual calculations
- Verify trade execution prices and timing
- **Test**: Backtest results match expected values within tolerance

---

## MVP Completion Criteria

**The MVP is complete when:**
1. Can load OHLCV data from MTS SQLite database
2. Can run buy-and-hold strategy backtest for any symbol/date range
3. Calculates basic performance metrics (return, Sharpe, drawdown)
4. Saves results to SQLite database
5. Provides command-line interface
6. All tests pass
7. Example runs successfully

**Total Tasks: 35**
**Estimated MVP Completion: 2-3 weeks with 1-2 tasks per day**