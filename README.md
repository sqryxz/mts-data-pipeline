# MTS Data Pipeline

A robust cryptocurrency data collection pipeline that automatically gathers OHLCV (Open, High, Low, Close, Volume) data for the top 3 cryptocurrencies by market cap using the CoinGecko API.

## Features

- **Automated Data Collection**: Collects hourly OHLCV data for Bitcoin, Ethereum, and the #3 cryptocurrency by market cap
- **Reliable Storage**: Stores data in CSV format with automatic deduplication and year-based file organization
- **Comprehensive Error Handling**: Smart retry logic with exponential backoff for API failures
- **Health Monitoring**: Built-in health checks and HTTP monitoring endpoint
- **Scheduled Operations**: Persistent scheduler with graceful shutdown and restart handling
- **Structured Logging**: Detailed metrics and logging for monitoring and debugging
- **Production Ready**: Comprehensive test coverage and robust error recovery

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Internet connection for CoinGecko API access

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MTS-data-pipeline
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**:
   ```bash
   python3 main.py --version
   ```

### Basic Usage

**Run a one-time data collection**:
```bash
python3 main.py --collect
```

**Collect multiple days of historical data**:
```bash
python3 main.py --collect --days 7
```

**Start health monitoring server**:
```bash
python3 main.py --server --port 8080
```

## Detailed Usage

### Command-Line Interface

The main entry point is `main.py` with the following options:

```bash
usage: main.py [-h] [--collect] [--server] [--days DAYS] [--port PORT] [--version] [--verbose]

MTS Cryptocurrency Data Pipeline

options:
  -h, --help     show this help message and exit
  --collect      Trigger data collection for top 3 cryptocurrencies
  --server       Start HTTP health monitoring server
  --days DAYS    Number of days of data to collect (default: 1, max: 365)
  --port PORT    Port for health monitoring server (default: 8080)
  --version      Show version information
  --verbose, -v  Enable verbose logging output

Examples:
  python3 main.py --collect                    # Collect latest data (1 day)
  python3 main.py --collect --days 7          # Collect 7 days of data
  python3 main.py --server                    # Start health monitoring server
  python3 main.py --server --port 9090       # Start server on custom port
  python3 main.py --version                   # Show version info
```

### Data Collection

#### Manual Collection
```bash
# Collect current day's data
python3 main.py --collect

# Collect last 30 days of data
python3 main.py --collect --days 30

# Enable verbose logging for debugging
python3 main.py --collect --verbose
```

#### Automated Collection
For production use, set up automated collection using your system's scheduler:

**Using cron (Linux/macOS)**:
```bash
# Add to crontab to run every hour
0 * * * * /usr/bin/python3 /path/to/MTS-data-pipeline/main.py --collect
```

**Using Task Scheduler (Windows)**:
- Create a new task that runs `python3 main.py --collect` every hour

### Health Monitoring

Start the health monitoring server to check system status:

```bash
# Start server on default port 8080
python3 main.py --server

# Start server on custom port
python3 main.py --server --port 9090
```

#### Health Check Endpoint

Access the health status via HTTP:

```bash
curl http://localhost:8080/health
```

**Healthy Response**:
```json
{
  "status": "healthy",
  "healthy": true,
  "message": "All components healthy",
  "checked_at": "2025-01-15T10:30:00.000000",
  "components": {
    "data_freshness": {
      "overall_status": "healthy",
      "is_healthy": true,
      "fresh_count": 3,
      "total_count": 3,
      "cryptos": {
        "bitcoin": {
          "status": "fresh",
          "is_fresh": true,
          "age_hours": 0.5,
          "last_update": "2025-01-15T10:00:00.000000",
          "records_count": 24
        }
      }
    }
  }
}
```

## Configuration

### Data Storage

Data is stored in CSV files under the `data/raw/` directory:

```
data/raw/
├── bitcoin_2025.csv
├── ethereum_2025.csv
└── tether_2025.csv
```

Each CSV file contains the following columns:
- `timestamp`: Unix timestamp in milliseconds
- `open`: Opening price
- `high`: Highest price
- `low`: Lowest price  
- `close`: Closing price
- `volume`: Trading volume (set to 0 as CoinGecko OHLC doesn't provide volume)

### Logging Configuration

Logs are written to:
- Console (INFO level and above)
- `logs/app.log` (DEBUG level and above)

Configure logging levels in `config/logging_config.py` or use the `--verbose` flag.

### API Configuration

The pipeline uses the CoinGecko public API with built-in rate limiting and retry logic:

- **Base URL**: https://api.coingecko.com/api/v3/
- **Rate Limits**: Automatically handled with exponential backoff
- **Timeout**: 30 seconds per request
- **Retries**: Up to 3 attempts for recoverable errors

## Architecture

### Core Components

```
src/
├── api/                 # External API integration
│   └── coingecko_client.py
├── data/                # Data models, validation, and storage
│   ├── models.py
│   ├── validator.py
│   └── storage.py
├── services/            # Core business logic
│   ├── collector.py     # Data collection orchestration
│   ├── monitor.py       # Health monitoring
│   └── scheduler.py     # Automated scheduling
└── utils/               # Utilities and exceptions
    ├── exceptions.py
    └── retry.py
```

### High-Level Data Flow

1. **Discovery**: Get top 3 cryptocurrencies by market cap
2. **Collection**: Fetch OHLCV data for each cryptocurrency
3. **Validation**: Validate data structure and values
4. **Storage**: Save to CSV files with deduplication
5. **Monitoring**: Track collection status and data freshness

## How the Data Pipeline Works

### 1. System Architecture Overview

The MTS Data Pipeline follows a modular, layered architecture designed for reliability, maintainability, and scalability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Line Interface                    │
│                        (main.py)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
      ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│Collection│    │Health    │    │Scheduler │
│Service   │    │Monitor   │    │Service   │
└─────┬────┘    └─────┬────┘    └─────┬────┘
      │               │               │
      ▼               ▼               ▼
┌─────────────────────────────────────────┐
│         Core Data Layer                 │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐  │
│  │API      │ │Validation│ │Storage  │  │
│  │Client   │ │Engine    │ │Engine   │  │
│  └─────────┘ └──────────┘ └─────────┘  │
└─────────────────────────────────────────┘
      │               │               │
      ▼               ▼               ▼
┌─────────────────────────────────────────┐
│         External Dependencies           │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐  │
│  │CoinGecko│ │File      │ │Logging  │  │
│  │API      │ │System    │ │System   │  │
│  └─────────┘ └──────────┘ └─────────┘  │
└─────────────────────────────────────────┘
```

### 2. Data Collection Process (Step-by-Step)

#### Phase 1: Cryptocurrency Discovery
```python
# 1. API call to get top cryptocurrencies by market cap
GET /api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=3&page=1

# 2. Response processing
{
  "id": "bitcoin",
  "symbol": "btc", 
  "name": "Bitcoin",
  "market_cap": 2000000000000,
  ...
}

# 3. Extract cryptocurrency IDs for data collection
crypto_ids = ["bitcoin", "ethereum", "tether"]
```

#### Phase 2: OHLCV Data Collection
For each cryptocurrency:
```python
# 1. API call for OHLCV data
GET /api/v3/coins/{crypto_id}/ohlc?vs_currency=usd&days={days}

# 2. Raw API response (array of arrays)
[
  [1751049000000, 106842.0, 106943.0, 106809.0, 106811.0],  # [timestamp, open, high, low, close]
  [1751050800000, 106797.0, 106797.0, 106598.0, 106623.0],
  ...
]

# 3. Data transformation to structured format
OHLCVRecord(
    timestamp=1751049000000,
    open=106842.0,
    high=106943.0, 
    low=106809.0,
    close=106811.0,
    volume=0.0  # Set to 0 as CoinGecko OHLC doesn't provide volume
)
```

#### Phase 3: Data Validation & Quality Assurance
```python
# 1. Structure validation
- Verify all required fields present (timestamp, open, high, low, close)
- Check data types (timestamp: int, prices: float)
- Validate logical constraints (high >= low, open/close within range)

# 2. Business logic validation  
- Ensure timestamps are chronological
- Check for reasonable price ranges
- Detect obvious data anomalies

# 3. Deduplication
- Compare with existing CSV data
- Skip records that already exist (by timestamp)
- Preserve data integrity
```

#### Phase 4: Data Storage & Persistence
```python
# 1. CSV file organization
data/raw/
├── bitcoin_2025.csv     # Year-based file naming
├── ethereum_2025.csv
└── tether_2025.csv

# 2. CSV structure
timestamp,open,high,low,close,volume
1751049000000,106842.0,106943.0,106809.0,106811.0,0.0

# 3. Atomic write operations
- Write to temporary file first
- Validate written data  
- Atomic rename to final location
- Ensures no partial/corrupted files
```

### 3. Error Handling & Recovery System

#### Multi-Layer Error Handling
```python
# Layer 1: Network-level retry logic
@retry_with_exponential_backoff(max_attempts=3)
def api_call():
    # Automatic retry for:
    # - Network timeouts
    # - Rate limiting (HTTP 429)
    # - Server errors (5xx)
    pass

# Layer 2: Application-level error categorization
try:
    collect_data()
except APIError as e:
    if e.is_rate_limit():
        wait_and_retry()
    elif e.is_client_error():
        skip_retry()  # Don't retry 4xx errors
    else:
        retry_with_backoff()

# Layer 3: System-level graceful degradation
if bitcoin_collection_fails():
    continue_with_ethereum_and_tether()
    log_partial_success()
```

#### Error Categories & Handling Strategy
```python
ERROR_CATEGORIES = {
    'rate_limit': 'wait_and_retry',      # HTTP 429
    'network': 'exponential_backoff',    # Timeouts, connection errors
    'server_error': 'retry_limited',     # 5xx errors  
    'client_error': 'fail_fast',         # 4xx errors (don't retry)
    'validation': 'skip_record',         # Invalid data
    'storage': 'retry_with_cleanup',     # Disk/permission issues
    'unexpected': 'log_and_continue'     # Unknown errors
}
```

### 4. Scheduling & Persistence System

#### Scheduler Architecture
```python
class SimpleScheduler:
    def __init__(self):
        self.running = False
        self.state_file = "data/scheduler_state.json"
        self.collection_interval = 3600  # 1 hour
        
    def start(self):
        # 1. Load previous state from disk
        last_run = self.load_state()
        
        # 2. Calculate next run time
        next_run = last_run + self.collection_interval
        
        # 3. Wait smartly (only remaining time, not full interval)
        if next_run > current_time():
            sleep(next_run - current_time())
            
        # 4. Run collection loop
        while self.running:
            self.collect_and_save_state()
            sleep(self.collection_interval)
```

#### State Persistence Format
```json
{
    "last_collection_time": "2025-06-29T12:00:00.000000",
    "last_collection_timestamp": 1751169600.0,
    "last_collection_success": true,
    "version": "1.0"
}
```

### 5. Health Monitoring & Observability

#### Data Freshness Detection
```python
def is_data_fresh(crypto_id: str, threshold_hours: int = 2) -> bool:
    # 1. Read latest timestamp from CSV file
    latest_timestamp = get_latest_timestamp(f"{crypto_id}_2025.csv")
    
    # 2. Calculate age
    age_hours = (current_time() - latest_timestamp) / 3600
    
    # 3. Compare against threshold
    return age_hours <= threshold_hours

# Health status levels
HEALTH_STATES = {
    'healthy': 'all_data_fresh',      # All cryptos within threshold
    'degraded': 'some_data_stale',    # Some cryptos stale
    'unhealthy': 'all_data_stale'     # All cryptos stale
}
```

#### HTTP Health Endpoint
```python
# GET /health response structure
{
    "status": "healthy|degraded|unhealthy",
    "healthy": true|false,
    "message": "Human-readable status",
    "timestamp": "2025-06-29T12:00:00.000000",
    "components": {
        "data_freshness": {
            "overall_status": "healthy",
            "fresh_count": 3,
            "total_count": 3,
            "cryptos": {
                "bitcoin": {
                    "status": "fresh",
                    "age_hours": 0.5,
                    "record_count": 72
                }
            }
        }
    }
}
```

### 6. Structured Logging & Metrics

#### Event-Based Logging System
```python
# Collection events with structured data
METRICS: {
    "event_type": "batch_collection_complete",
    "timestamp": "2025-06-29T12:24:15.618570", 
    "total_attempted": 3,
    "successful": 3,
    "failed": 0,
    "total_records_collected": 144,
    "duration_seconds": 1.138,
    "successful_cryptos": ["bitcoin", "ethereum", "tether"],
    "error_categories": {}
}
```

#### Log Analysis & Monitoring
```bash
# Parse structured logs
grep "METRICS:" logs/app.log | jq '.total_records_collected'

# Monitor success rates
grep "batch_collection_complete" logs/app.log | jq '.successful/.total_attempted'

# Track performance metrics
grep "duration_seconds" logs/app.log | jq '.duration_seconds'
```

### 7. Data Integrity & Quality Assurance

#### Multi-Level Validation
```python
# Level 1: Schema validation
def validate_structure(record):
    required_fields = ['timestamp', 'open', 'high', 'low', 'close']
    return all(field in record for field in required_fields)

# Level 2: Business logic validation  
def validate_ohlc_logic(record):
    return (
        record.high >= record.low and
        record.high >= record.open and
        record.high >= record.close and
        record.low <= record.open and
        record.low <= record.close
    )

# Level 3: Data consistency validation
def validate_consistency(records):
    # Check chronological order
    timestamps = [r.timestamp for r in records]
    return timestamps == sorted(timestamps)
```

#### Deduplication Strategy
```python
# 1. Read existing data
existing_timestamps = set(get_existing_timestamps("bitcoin_2025.csv"))

# 2. Filter new records
new_records = [r for r in records if r.timestamp not in existing_timestamps]

# 3. Append only new data
append_to_csv(new_records, "bitcoin_2025.csv")
```

### 8. System Resilience & Fault Tolerance

#### Graceful Degradation Patterns
```python
# Pattern 1: Partial success handling
def collect_all_cryptos():
    results = []
    for crypto in ['bitcoin', 'ethereum', 'tether']:
        try:
            result = collect_crypto_data(crypto)
            results.append(result)
        except Exception as e:
            log_error(f"Failed to collect {crypto}: {e}")
            continue  # Continue with other cryptos
    return results

# Pattern 2: Circuit breaker for API failures
if consecutive_failures >= 3:
    enter_circuit_breaker_mode()
    wait_before_retry(exponential_backoff_delay)

# Pattern 3: Data quality fallback
if data_quality_score < threshold:
    skip_storage()
    alert_monitoring_system()
```

#### Recovery Mechanisms
```python
# Automatic recovery strategies
RECOVERY_STRATEGIES = {
    'api_timeout': 'retry_with_longer_timeout',
    'rate_limit': 'exponential_backoff_with_jitter', 
    'storage_full': 'cleanup_old_logs_and_retry',
    'permission_denied': 'create_directory_and_retry',
    'network_partition': 'wait_for_connectivity_and_retry'
}
```

### 9. Performance & Scalability

#### Resource Management
```python
# Memory-efficient CSV reading (streaming)
def read_large_csv(filename):
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield process_row(row)  # Process one row at a time

# Connection pooling for API calls
session = requests.Session()
session.mount('https://', HTTPAdapter(pool_connections=1, pool_maxsize=10))
```

#### Scalability Considerations
- **Horizontal Scaling**: Each crypto can be collected independently
- **Vertical Scaling**: Memory usage stays constant (~50MB) regardless of data volume
- **Storage Growth**: Linear growth (~1GB/year for 3 cryptos)
- **API Rate Limits**: Built-in exponential backoff handles CoinGecko limits

### 10. Production Deployment Patterns

#### Process Management
```bash
# Systemd service for automatic startup/recovery
[Unit]
Description=MTS Data Pipeline
After=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=300
ExecStart=/usr/bin/python3 /opt/mts-pipeline/main.py --collect
```

#### Monitoring Integration
```bash
# Health check integration with monitoring systems
curl -f http://localhost:8080/health || alert_ops_team()

# Log aggregation for centralized monitoring
tail -f logs/app.log | grep "METRICS:" | forward_to_log_aggregator()
```

This comprehensive architecture ensures reliable, scalable, and maintainable cryptocurrency data collection with robust error handling, monitoring, and recovery capabilities.

## Troubleshooting

### Common Issues

#### "No data collected" or "API errors"

**Symptoms**: Collection returns 0 records or shows API errors
**Causes**: Network issues, API rate limiting, or service outages

**Solutions**:
1. Check internet connectivity:
   ```bash
   curl https://api.coingecko.com/api/v3/ping
   ```
2. Try running with verbose logging:
   ```bash
   python3 main.py --collect --verbose
   ```
3. Wait a few minutes and retry (may be rate limited)

#### "Permission denied" errors

**Symptoms**: Cannot write to data directory
**Causes**: Insufficient file system permissions

**Solutions**:
1. Check directory permissions:
   ```bash
   ls -la data/raw/
   ```
2. Fix permissions:
   ```bash
   chmod 755 data/raw/
   ```
3. Ensure the directory exists:
   ```bash
   mkdir -p data/raw
   ```

#### "Health check shows stale data"

**Symptoms**: Health endpoint returns `"status": "degraded"` or `"status": "unhealthy"`
**Causes**: Data collection hasn't run recently or failed

**Solutions**:
1. Run manual collection:
   ```bash
   python3 main.py --collect
   ```
2. Check logs for errors:
   ```bash
   tail -f logs/app.log
   ```
3. Verify CSV files exist and have recent data:
   ```bash
   ls -la data/raw/
   ```

#### "Module not found" errors

**Symptoms**: Python import errors when running
**Causes**: Missing dependencies or incorrect Python path

**Solutions**:
1. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Verify Python version:
   ```bash
   python3 --version  # Should be 3.8+
   ```
3. Run from project root directory

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
python3 main.py --collect --verbose
```

This will show:
- API request/response details
- Data validation steps
- Storage operations
- Error categorization and retry logic

### Log Analysis

Check application logs for detailed information:

```bash
# View recent logs
tail -f logs/app.log

# Search for errors
grep ERROR logs/app.log

# View structured metrics
grep "METRICS:" logs/app.log | jq .
```

### Health Check Validation

Verify system health programmatically:

```bash
# Check if health endpoint is responding
curl -f http://localhost:8080/health > /dev/null && echo "Healthy" || echo "Unhealthy"

# Parse health status
curl -s http://localhost:8080/health | jq .status
```

## Testing

### Run All Tests

```bash
# Run complete test suite
python3 -m pytest

# Run with coverage
python3 -m pytest --cov=src

# Run specific test categories
python3 -m pytest tests/test_integration.py     # Integration tests
python3 -m pytest tests/test_error_scenarios.py # Error scenarios
```

### Verify Installation

Follow these steps to verify your installation:

1. **Run version check**:
   ```bash
   python3 main.py --version
   ```

2. **Test API connectivity**:
   ```bash
   python3 -c "from src.api.coingecko_client import CoinGeckoClient; client = CoinGeckoClient(); print('API Status:', client.ping())"
   ```

3. **Run data collection test**:
   ```bash
   python3 main.py --collect --days 1 --verbose
   ```

4. **Verify data files created**:
   ```bash
   ls -la data/raw/
   ```

5. **Test health monitoring**:
   ```bash
   # Start server in background
   python3 main.py --server &
   
   # Test health endpoint
   sleep 2 && curl http://localhost:8080/health
   
   # Stop server
   pkill -f "python3 main.py --server"
   ```

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/mts-pipeline.service`:

```ini
[Unit]
Description=MTS Data Pipeline
After=network.target

[Service]
Type=simple
User=mts
WorkingDirectory=/opt/mts-data-pipeline
ExecStart=/usr/bin/python3 main.py --collect
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mts-pipeline.service
sudo systemctl start mts-pipeline.service
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "main.py", "--collect"]
```

Build and run:
```bash
docker build -t mts-pipeline .
docker run -v $(pwd)/data:/app/data mts-pipeline
```

## Performance

### Resource Usage

- **Memory**: ~50MB typical usage
- **CPU**: Minimal (data collection is I/O bound)
- **Storage**: ~1MB per day per cryptocurrency
- **Network**: ~100KB per collection cycle

### Scalability

- **Data Retention**: CSV files are organized by year (e.g., `bitcoin_2025.csv`)
- **Collection Frequency**: Designed for hourly collection, can be adjusted
- **API Limits**: Built-in rate limiting handles CoinGecko's limits gracefully
- **Storage Growth**: Approximately 1GB per year for 3 cryptocurrencies

## Support

### Getting Help

1. **Check logs**: Review `logs/app.log` for error details
2. **Run tests**: Execute test suite to verify system integrity
3. **Health check**: Use monitoring endpoint to check system status
4. **Verbose mode**: Run with `--verbose` for detailed debugging information

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: 256MB minimum, 512MB recommended
- **Storage**: 10GB for data and logs (grows ~1GB/year)
- **Network**: Stable internet connection for API access

This documentation covers the complete MVP functionality. The system is designed to be robust, maintainable, and production-ready for reliable cryptocurrency data collection. 