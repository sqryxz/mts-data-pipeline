# MVP Build Plan: Macro Indicators Analytics Module

## Phase 1: Foundation (Database & Models)

### Task 1.1: Create Analytics Database Table
- Create SQL migration file `migrations/001_create_analytics_table.sql`
- Define `macro_analytics_results` table schema
- Add indexes for performance
- **Test**: Execute migration, verify table exists

### Task 1.2: Create Base Data Models
- Create `src/analytics/models/__init__.py`
- Create `src/analytics/models/analytics_models.py`
- Define `MacroIndicatorMetrics` dataclass only
- **Test**: Import and instantiate model

### Task 1.3: Create Analytics Repository Base
- Create `src/analytics/storage/__init__.py`
- Create `src/analytics/storage/analytics_repository.py`
- Implement `__init__` method with db_path
- Add `get_connection()` method
- **Test**: Connect to database

### Task 1.4: Implement Get Indicator Data
- Add `get_indicator_data()` method to repository
- Query macro_indicators table
- Return pandas DataFrame
- **Test**: Fetch VIX data for last 30 days

## Phase 2: Core Calculations

### Task 2.1: Create Rate of Change Calculator
- Create `src/analytics/macro/rate_of_change.py`
- Implement `calculate_roc()` for single calculation
- Handle division by zero
- **Test**: Calculate ROC for sample values

### Task 2.2: Add Period ROC Calculation
- Add `calculate_period_roc()` method
- Accept pandas Series and period
- Return single ROC value
- **Test**: Calculate 24-hour ROC for VIX

### Task 2.3: Create Z-Score Engine Base
- Create `src/analytics/macro/z_score_engine.py`
- Implement `calculate_z_score()` for single value
- Use numpy for mean/std calculation
- **Test**: Calculate z-score for sample data

### Task 2.4: Add Rolling Z-Score
- Add `calculate_rolling_z_scores()` method
- Return pandas Series of z-scores
- Use pandas rolling window
- **Test**: Calculate 30-day rolling z-scores

## Phase 3: Timeframe Analysis

### Task 3.1: Create Timeframe Analyzer
- Create `src/analytics/macro/timeframe_analyzer.py`
- Define `SUPPORTED_TIMEFRAMES` constant
- Implement `__init__` with repository
- **Test**: Import and instantiate

### Task 3.2: Implement Get Timeframe Data
- Add `get_timeframe_data()` method
- Fetch data for specific timeframe
- Resample to appropriate frequency
- **Test**: Get 4-hour resampled data

### Task 3.3: Handle Data Interpolation
- Add interpolation logic to `get_timeframe_data()`
- Use pandas interpolate method
- Fill forward for missing values
- **Test**: Verify no NaN values in output

## Phase 4: Calculator Integration

### Task 4.1: Create Main Calculator Class
- Create `src/analytics/macro/calculator.py`
- Implement `__init__` with dependencies
- Initialize ROC and z-score engines
- **Test**: Instantiate calculator

### Task 4.2: Implement Single Metric Calculation
- Add `_calculate_single_metric()` private method
- Calculate ROC and z-score for one timeframe
- Return dict with both values
- **Test**: Calculate 1h metrics for VIX

### Task 4.3: Implement Multi-Timeframe Calculation
- Add `calculate_metrics()` method
- Loop through timeframes
- Call `_calculate_single_metric()` for each
- **Test**: Calculate 1h, 4h, 24h metrics

### Task 4.4: Add Error Handling
- Wrap calculations in try/except
- Log errors, return None for failed calculations
- Continue with other timeframes
- **Test**: Handle missing data gracefully

## Phase 5: Service Layer

### Task 5.1: Create Analytics Service Base
- Create `src/services/macro_analytics_service.py`
- Implement `__init__` with config path
- Load configuration from JSON
- **Test**: Load test configuration

### Task 5.2: Add Basic Analysis Method
- Add `analyze_indicator()` method
- Accept indicator name and timeframes
- Call calculator and return results
- **Test**: Analyze VIX across timeframes

### Task 5.3: Save Results to Database
- Add `_save_results()` private method
- Convert metrics to database format
- Call repository save method
- **Test**: Verify data in database

## Phase 6: API Integration

### Task 6.1: Create API Router
- Create `src/api/endpoints/macro_analytics.py`
- Define FastAPI router with prefix
- Add basic health check endpoint
- **Test**: Access health endpoint

### Task 6.2: Add Calculate Endpoint
- Add POST `/calculate/{indicator}` endpoint
- Accept timeframes as query parameter
- Return JSON response
- **Test**: Call with curl/httpie

### Task 6.3: Add Error Handling to API
- Add try/except to endpoint
- Return appropriate HTTP status codes
- Include error messages in response
- **Test**: Handle invalid indicator name

## Phase 7: Configuration

### Task 7.1: Create Configuration File
- Create `src/config/analytics/macro_analytics.json`
- Add default timeframes and lookback periods
- Include test database path
- **Test**: Load and parse JSON

### Task 7.2: Update Service Configuration
- Modify service to use config values
- Pass config to calculator
- Use configured lookback periods
- **Test**: Verify config affects calculations

## Phase 8: Testing & Validation

### Task 8.1: Create Integration Test
- Create `tests/test_integration.py`
- Test full flow: API → Service → Calculator → DB
- Use test database
- **Test**: Run pytest

### Task 8.2: Add CLI Command
- Add `--analyze-macro` command to main.py
- Accept indicator as argument
- Print results to console
- **Test**: `python main.py --analyze-macro VIX`

### Task 8.3: Performance Test
- Create script to calculate 10 indicators
- Measure execution time
- Verify under 5 seconds
- **Test**: Run performance script

## MVP Completion Checklist

- [ ] Can fetch macro indicator data from database
- [ ] Calculates ROC for 1h, 4h, 24h timeframes
- [ ] Calculates z-scores with configurable lookback
- [ ] Saves results to database
- [ ] Provides REST API endpoint
- [ ] Handles missing data gracefully
- [ ] Configuration-driven behavior
- [ ] Basic error handling and logging