# MVP Development Plan: Crypto Data Collection Pipeline

## Phase 1: Foundation & Basic Structure

### Task 1.1: Project Setup
**Goal**: Initialize project structure and dependencies
**Start**: Empty directory
**End**: Working Python environment with basic structure
```bash
# Test: Run `python -c "import requests; print('OK')"` successfully
```
**Steps**:
- Create directory structure (only `src/`, `config/`, `tests/`)
- Initialize `requirements.txt` with: `requests`, `pytest`, `python-dotenv`
- Create `.env.example` file
- Add `__init__.py` files to packages

### Task 1.2: Basic Configuration
**Goal**: Load configuration from environment
**Start**: Empty `config/settings.py`
**End**: Configuration class that loads from `.env`
```python
# Test: config = Config(); assert config.COINGECKO_BASE_URL is not None
```
**Steps**:
- Create `Config` class in `config/settings.py`
- Add COINGECKO_BASE_URL, REQUEST_TIMEOUT constants
- Load from environment with defaults
- Write basic test

### Task 1.3: Basic Logging
**Goal**: Set up simple file logging
**Start**: No logging configuration
**End**: Logger writes to `logs/app.log`
```python
# Test: logger.info("test"); assert "test" in open("logs/app.log").read()
```
**Steps**:
- Create `logs/` directory
- Configure basic file logger in `config/logging_config.py`
- Test log file creation and writing

## Phase 2: API Client Foundation

### Task 2.1: Basic HTTP Client
**Goal**: Make successful HTTP requests to CoinGecko
**Start**: Empty `src/api/coingecko_client.py`
**End**: Client that can fetch `/ping` endpoint
```python
# Test: client = CoinGeckoClient(); response = client.ping(); assert response["gecko_says"]
```
**Steps**:
- Create `CoinGeckoClient` class
- Implement `ping()` method
- Add basic error handling for network issues
- Write test with mock response

### Task 2.2: Market Data Endpoint
**Goal**: Fetch cryptocurrency market data
**Start**: Client with only ping method
**End**: Client fetches top cryptocurrencies by market cap
```python
# Test: data = client.get_top_cryptos(3); assert len(data) == 3; assert "bitcoin" in [c["id"] for c in data]
```
**Steps**:
- Implement `get_top_cryptos(limit)` method
- Parse JSON response into list of dicts
- Handle API errors (rate limit, network)
- Test with live API call

### Task 2.3: Price History Endpoint
**Goal**: Fetch OHLC data for specific cryptocurrency
**Start**: Client with market data method
**End**: Client fetches hourly OHLC data
```python
# Test: data = client.get_ohlc_data("bitcoin", days=1); assert len(data) > 0; assert len(data[0]) == 5
```
**Steps**:
- Implement `get_ohlc_data(coin_id, days)` method
- Parse OHLC response format
- Handle missing data scenarios
- Test with known cryptocurrency

## Phase 3: Data Models & Validation

### Task 3.1: Cryptocurrency Model
**Goal**: Define cryptocurrency data structure
**Start**: Empty `src/data/models.py`
**End**: Cryptocurrency dataclass with validation
```python
# Test: crypto = Cryptocurrency(id="bitcoin", symbol="btc", name="Bitcoin"); assert crypto.symbol == "btc"
```
**Steps**:
- Create `Cryptocurrency` dataclass
- Add fields: id, symbol, name, market_cap_rank
- Add basic validation (non-empty strings)
- Write validation tests

### Task 3.2: OHLCV Model
**Goal**: Define OHLCV data structure
**Start**: Cryptocurrency model only
**End**: OHLCV dataclass with timestamp handling
```python
# Test: ohlcv = OHLCVData(timestamp=1234567890, open=50000, high=51000, low=49000, close=50500, volume=1000000)
```
**Steps**:
- Create `OHLCVData` dataclass
- Add timestamp conversion utilities
- Validate numeric fields (positive values)
- Test edge cases (zero volume, equal OHLC)

### Task 3.3: Data Validator
**Goal**: Validate API responses before storage
**Start**: Models without validation logic
**End**: Validator class that checks data quality
```python
# Test: validator = DataValidator(); assert validator.validate_ohlcv_data(valid_data) == True
```
**Steps**:
- Create `DataValidator` class in `src/data/validator.py`
- Implement OHLCV data validation (logical price relationships)
- Check for missing or null values
- Test with valid and invalid data samples

## Phase 4: Storage Layer

### Task 4.1: CSV Storage Setup
**Goal**: Save data to CSV files
**Start**: Empty `src/data/storage.py`
**End**: CSVStorage class writes OHLCV data to files
```python
# Test: storage.save_ohlcv_data("bitcoin", [ohlcv_data]); assert os.path.exists("data/raw/bitcoin_2024.csv")
```
**Steps**:
- Create `CSVStorage` class
- Implement file naming convention (crypto_YYYY.csv)
- Handle file creation and appending
- Test file writing and reading

### Task 4.2: Data Deduplication
**Goal**: Prevent duplicate entries in storage
**Start**: Basic CSV storage
**End**: Storage checks for existing timestamps
```python
# Test: storage.save_ohlcv_data("bitcoin", [duplicate_data]); assert row_count_unchanged()
```
**Steps**:
- Add timestamp checking before writing
- Implement `_record_exists()` method
- Handle partial duplicates (same timestamp, different data)
- Test duplicate detection

### Task 4.3: Data Retrieval ✅
**Goal**: Read stored data back from CSV
**Start**: Write-only storage
**End**: Storage can load historical data
```python
# Test: data = storage.load_ohlcv_data("bitcoin", start_date, end_date); assert len(data) > 0
```
**Steps**:
- Implement `load_ohlcv_data()` method
- Add date range filtering
- Handle missing files gracefully
- Test data loading and filtering

## Phase 5: Collection Service

### Task 5.1: Market Cap Tracker ✅
**Goal**: Identify top 3 cryptocurrencies by market cap
**Start**: Empty `src/services/collector.py`
**End**: Service identifies current top 3 cryptos
```python
# Test: collector = DataCollector(); top3 = collector.get_top_cryptocurrencies(); assert len(top3) == 3
```
**Steps**:
- Create `DataCollector` class
- Implement `get_top_cryptocurrencies()` method
- Handle API failures gracefully
- Test with live API data

### Task 5.2: Single Crypto Collection ✅
**Goal**: Collect OHLCV data for one cryptocurrency
**Start**: Market cap tracker only
**End**: Collect and store data for one crypto
```python
# Test: collector.collect_crypto_data("bitcoin"); assert new_data_in_storage()
```
**Steps**:
- Implement `collect_crypto_data(crypto_id)` method
- Integrate API client and storage
- Add error handling for API failures
- Test end-to-end data flow

### Task 5.3: Batch Collection ✅
**Goal**: Collect data for all top 3 cryptocurrencies
**Start**: Single crypto collection
**End**: Collect data for multiple cryptos in sequence
```python
# Test: collector.collect_all_data(); assert data_exists_for_all_top3()
```
**Steps**:
- Implement `collect_all_data()` method
- Handle individual crypto failures
- Log collection results
- Test with mock API responses

## Phase 6: Error Handling & Reliability

### Task 6.1: Custom Exceptions ✅
**Goal**: Define specific error types
**Start**: Generic exception handling
**End**: Custom exceptions for different failure modes
```python
# Test: with pytest.raises(APIRateLimitError): raise APIRateLimitError("Rate limited")
```
**Steps**:
- Create exception classes in `src/utils/exceptions.py`
- Define: `APIError`, `APIRateLimitError`, `DataValidationError`, `StorageError`
- Add error codes and messages
- Test exception inheritance

### Task 6.2: API Retry Logic ✅
**Goal**: Retry failed API requests with backoff
**Start**: No retry mechanism
**End**: API client retries with exponential backoff
```python
# Test: Mock API to fail twice then succeed; assert client eventually succeeds
```
**Steps**:
- Add retry decorator to API methods
- Implement exponential backoff
- Set maximum retry attempts
- Test retry behavior with mocked failures

**Completed**: Created `src/utils/retry.py` with `retry_with_backoff` decorator
- Exponential backoff with configurable parameters (base_delay, max_delay, backoff_factor)
- Jitter support to prevent thundering herd
- Special handling for rate limit errors with retry-after headers
- Comprehensive test coverage with mocked failures and edge cases
- Applied to all API client methods (ping, get_top_cryptos, get_ohlc_data)
- Retries connection and timeout errors, but not client errors (404, etc.)
- Live API testing confirmed working correctly

### Task 6.3: Collection Error Recovery ✅
**Goal**: Continue collection even if individual cryptos fail
**Start**: Collection stops on first error
**End**: Collection logs errors but continues
```python
# Test: Mock one crypto to fail; assert other cryptos still collected
```
**Steps**:
- Wrap individual crypto collection in try/catch
- Log errors without stopping batch
- Return success/failure summary
- Test partial failure scenarios

**Completed**: Enhanced data collection service with comprehensive error recovery
- **Error Categorization**: Automatically categorizes errors into types (rate_limit, network, client_error, server_error, validation, storage, unexpected)
- **Collection-Level Retries**: Configurable retry attempts per crypto with intelligent retry logic
- **Enhanced Metrics**: Detailed timing, attempt counts, and error analytics for monitoring
- **Smart Retry Logic**: Only retries recoverable errors, respects non-retryable errors
- **Comprehensive Logging**: Enhanced logging with attempt numbers, timing, and error categories
- **Backward Compatibility**: All existing functionality preserved with enhanced capabilities
- **Full Test Coverage**: 16 new tests covering error categorization, retry logic, and integration scenarios
- **Live Testing**: Confirmed working with mocked failure scenarios and real API integration

## Phase 7: Scheduling & Automation

### Task 7.1: Manual Trigger ✅
**Goal**: Run collection on command
**Start**: Collection service only
**End**: Command-line script triggers collection
```bash
# Test: python main.py --collect; assert exit_code == 0
```
**Steps**:
- Create `main.py` with argument parsing
- Add `--collect` flag for manual runs
- Initialize all services
- Test command execution

**Completed**: Created comprehensive command-line interface with professional features
- **Main Entry Point**: `main.py` with full argument parsing using argparse
- **Collection Command**: `--collect` flag triggers data collection with exit code 0 on success
- **Flexible Parameters**: `--days` parameter for collecting 1-365 days of data
- **User Experience**: `--help`, `--version`, and `--verbose` flags for better usability
- **Error Handling**: Comprehensive validation, graceful error handling, and proper exit codes
- **Service Integration**: Seamless initialization of all services (config, logging, collector)
- **Professional Logging**: Beautiful formatted logs with collection summaries and progress tracking
- **Live Testing**: Confirmed working with real API, including rate limit handling and retry logic
- **Full Test Coverage**: 21 comprehensive tests covering all functionality and edge cases
- **Production Ready**: Robust error handling, keyboard interrupt support, and operational excellence

### Task 7.2: Basic Scheduler
**Goal**: Run collection every hour
**Start**: Manual trigger only
**End**: Scheduler runs collection automatically
```python
# Test: Start scheduler; wait 2 minutes; assert collection_ran()
```
**Steps**:
- Create `SimpleScheduler` class in `src/services/scheduler.py`
- Use `time.sleep()` for basic timing
- Add graceful shutdown handling
- Test with short intervals

### Task 7.3: Scheduler Persistence
**Goal**: Track last collection time across restarts
**Start**: In-memory scheduling only
**End**: Scheduler resumes after restart
```python
# Test: Stop scheduler; restart; assert no duplicate collections
```
**Steps**:
- Save last run timestamp to file
- Check timestamp on startup
- Skip collection if recently completed
- Test restart behavior

## Phase 8: Monitoring & Health Checks

### Task 8.1: Collection Status Logging
**Goal**: Log detailed collection results
**Start**: Basic error logging
**End**: Structured logs with metrics
```python
# Test: Run collection; assert logs contain success counts and timing
```
**Steps**:
- Add structured logging to collector
- Log: start time, end time, records collected, errors
- Use consistent log format
- Test log parsing

### Task 8.2: Data Freshness Check
**Goal**: Detect stale data
**Start**: No data monitoring
**End**: Health check detects missing recent data
```python
# Test: health_check = HealthChecker(); assert health_check.is_data_fresh("bitcoin") == True
```
**Steps**:
- Create `HealthChecker` class in `src/services/monitor.py`
- Check if latest data is within expected timeframe
- Return status and details
- Test with old and fresh data

### Task 8.3: System Health Endpoint ✅
**Goal**: HTTP endpoint for health monitoring
**Start**: File-based health checks
**End**: Simple HTTP server returns health status
```bash
# Test: curl localhost:8080/health; assert response contains "status": "healthy"
```
**Steps**:
- Add simple HTTP server to main.py
- Create `/health` endpoint
- Return JSON with system status
- Test endpoint accessibility

**Completed**: Created comprehensive HTTP health monitoring server
- **HTTP Server**: Built-in Python HTTP server with `--server` command-line flag
- **Health Endpoint**: `/health` endpoint returns detailed JSON system status
- **HealthChecker Integration**: Leverages existing HealthChecker for data freshness monitoring
- **Response Format**: JSON with status, healthy boolean, message, timestamp, and component details
- **Error Handling**: Graceful error responses with appropriate HTTP status codes (500 for errors, 404 for unknown endpoints)
- **Port Configuration**: Configurable port via `--port` parameter (default: 8080)
- **Signal Handling**: Graceful shutdown with SIGINT/SIGTERM support
- **CORS Support**: Cross-origin support for web dashboard integration
- **Comprehensive Testing**: 7 test cases covering request handling, error scenarios, and server integration
- **Production Ready**: Validates the exact test requirement - returns `"status": "healthy"` when data is fresh
- **Live Testing**: Confirmed working with `curl localhost:8080/health` showing healthy system status

## Phase 9: Testing & Documentation

### Task 9.1: Integration Tests ✅
**Goal**: Test complete data flow
**Start**: Unit tests only
**End**: End-to-end test with mocked API
```python
# Test: Mock CoinGecko API; run full collection; assert data in CSV files
```
**Steps**:
- Create integration test suite
- Mock all external API calls
- Test complete collection workflow
- Verify data persistence

**Completed**: Created comprehensive end-to-end integration test suite
- **Complete Workflow Test**: `test_complete_data_collection_workflow` fully mocks CoinGecko API and verifies complete data flow
- **API Mocking**: Uses `requests_mock` to mock all external API calls (ping, markets, OHLC endpoints)
- **Data Verification**: Tests successful collection of 3 cryptos with 4 records each (12 total)
- **File Persistence**: Verifies CSV files are created with correct year-based naming (`bitcoin_2025.csv`, etc.)
- **Data Validation**: Checks CSV structure, columns, and specific price values from mocked data
- **Partial Failure Testing**: `test_partial_failure_collection_workflow` tests graceful handling when some APIs fail
- **Storage Integration**: Direct CSVStorage integration with temporary directories for isolated testing
- **Requirements Met**: Successfully implements the exact test requirement: "Mock CoinGecko API; run full collection; assert data in CSV files"

**Key Features Implemented**:
- Mock API responses with realistic cryptocurrency data (Bitcoin, Ethereum, Tether)
- Temporary directory isolation for test data
- Complete data flow from API → Collection → Validation → Storage → File verification
- Realistic error scenarios (API failures, partial success)
- Verification of specific data values and CSV file structure
- Integration with existing DataCollector, CSVStorage, and validation components

### Task 9.2: Error Scenario Tests ✅
**Goal**: Test failure handling
**Start**: Happy path tests only
**End**: Tests for all major failure modes
```python
# Test: API timeout, invalid data, disk full, network error scenarios
```
**Steps**:
- Test API failures (timeout, rate limit, invalid response)
- Test storage failures (disk full, permission denied)
- Test data validation failures
- Verify graceful degradation

**Completed**: Created comprehensive error scenario test suite covering all major failure modes
- **API Failure Tests**: Complete coverage of API error scenarios
  - `test_api_timeout_error`: Verifies timeout handling with proper retries
  - `test_api_rate_limit_error`: Tests rate limit detection and handling (HTTP 429)
  - `test_api_connection_error`: Validates network connection failure recovery
  - `test_api_server_error`: Tests server errors (500, 503, 502) with retry logic
  - `test_api_client_error`: Verifies client errors (404, 400, 401) are not retried
  - `test_invalid_json_response`: Handles malformed API responses gracefully

- **Data Validation Failure Tests**: Comprehensive data quality checks
  - `test_invalid_ohlc_data_structure`: Tests malformed OHLC data (missing fields, negative values)
  - `test_missing_required_fields`: Validates cryptocurrency data field requirements
  - `test_malformed_price_data`: Handles invalid data types and null values

- **Storage Failure Tests**: Filesystem and permission error handling
  - `test_readonly_directory`: Tests behavior with read-only storage locations
  - `test_nonexistent_parent_directory`: Validates directory creation failure handling

- **Graceful Degradation Tests**: System resilience verification
  - `test_mixed_success_failure_scenario`: Verifies partial success with some failures
  - `test_complete_api_unavailability`: Tests complete API failure scenarios
  - `test_retry_behavior_with_eventual_success`: Validates retry logic with eventual recovery

**Key Features Validated**:
- **Error Categorization**: Automatic categorization into rate_limit, network, client_error, server_error, validation, storage, unexpected
- **Retry Logic**: Smart retry behavior for recoverable errors, immediate failure for non-recoverable errors
- **Graceful Degradation**: System continues operating with partial failures
- **Data Integrity**: No corrupted data written during error scenarios
- **Comprehensive Logging**: All error scenarios properly logged with structured metrics
- **Recovery Mechanisms**: System recovers gracefully from transient failures

**Test Coverage**: 14 comprehensive error scenario tests covering:
- 6 API failure scenarios
- 3 data validation failure scenarios  
- 2 storage failure scenarios
- 3 graceful degradation scenarios

**Requirements Met**: Successfully implements all specified test scenarios including API timeout, invalid data, storage failures, and network errors with verified graceful degradation behavior.

### Task 9.3: MVP Documentation ✅
**Goal**: Document MVP usage
**Start**: Code comments only
**End**: README with setup and usage instructions
```markdown
# Test: Follow README instructions; successfully run collection
```
**Steps**:
- Document installation steps
- Explain configuration options
- Provide usage examples
- Add troubleshooting section

**Completed**: Created comprehensive MVP documentation with complete user guide
- **Installation Guide**: Step-by-step setup with prerequisites, dependencies, and verification
- **Configuration Documentation**: Complete coverage of data storage, logging, and API settings
- **Usage Examples**: Detailed command-line interface documentation with practical examples
- **Troubleshooting Section**: Comprehensive guide covering common issues and solutions
- **Production Deployment**: Systemd and Docker deployment examples
- **Performance Metrics**: Resource usage and scalability information
- **Testing Instructions**: Complete verification steps and test suite guidance
- **Architecture Overview**: Clear explanation of components and data flow
- **Health Monitoring**: Full documentation of HTTP endpoint and health checks
- **Requirements Verified**: Successfully tested all README instructions:
  - ✅ Version check: `python3 main.py --version` works
  - ✅ API connectivity: CoinGecko API connection verified
  - ✅ Data collection: `python3 main.py --collect --days 1 --verbose` successfully collected 144 records
  - ✅ File creation: CSV files created with proper structure (bitcoin_2025.csv, ethereum_2025.csv, tether_2025.csv)
  - ✅ Health monitoring: HTTP server and `/health` endpoint working correctly
  - ✅ Data format: CSV files contain correct columns (timestamp, open, high, low, close, volume)
  - ✅ Complete workflow: End-to-end verification confirms all documentation is accurate

## MVP Completion Criteria

✅ **Functional Requirements**:
- Collects hourly OHLCV data for Bitcoin, Ethereum, and #3 crypto by market cap
- Stores data in CSV format with timestamps
- Runs automatically every hour
- Handles API failures gracefully

✅ **Technical Requirements**:
- Modular architecture following the design
- Comprehensive error handling
- Basic monitoring and health checks
- Test coverage for critical paths

✅ **Operational Requirements**:
- Can be started/stopped via command line
- Logs important events and errors
- Recovers from common failure scenarios
- Simple deployment (single machine)

**Total Estimated Tasks**: 27 tasks
**Estimated Timeline**: 2-3 weeks for solo developer
**Key Deliverable**: Working MVP that collects crypto data reliably