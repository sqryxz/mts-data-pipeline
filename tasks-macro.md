# Macro Indicators Add-on MVP Development Plan (Simplified)

## Critical Path: 18 Essential Tasks Only

### Phase 1: Foundation (Tasks 1-4)

### Task 1: Create Macro Configuration
**Start**: Empty `config/macro_settings.py` file  
**End**: Complete config with FRED_API_CONFIG and all 4 MACRO_INDICATORS  
**Test**: Import config, verify all indicators have required fields  
**Deliverable**: Complete configuration for VIX, DXY, Treasury 10Y, Fed Funds Rate

### Task 2: Create Macro Data Model
**Start**: Empty `src/data/macro_models.py`  
**End**: `MacroIndicatorRecord` dataclass with all core fields  
**Test**: Create record, serialize to dict, verify all fields present  
**Deliverable**: Data structure for macro records

### Task 3: Add Custom Macro Exceptions
**Start**: Basic exceptions exist  
**End**: Add `FREDAPIError` and `MacroDataError` to existing exceptions.py  
**Test**: Raise each exception, verify proper inheritance  
**Deliverable**: Specific error handling for macro operations

### Task 4: Create Macro Directory Structure
**Start**: Existing `data/raw/` directory  
**End**: `data/raw/macro/` directory created programmatically  
**Test**: Run creation code, verify directory exists  
**Deliverable**: File system organization for macro data

### Phase 2: API & Storage (Tasks 5-10)

### Task 5: Create Basic FRED API Client
**Start**: Empty `src/api/fred_client.py`  
**End**: `FREDClient` class with API key handling and basic request method  
**Test**: Mock API response, verify request formatting  
**Deliverable**: Core FRED API communication

### Task 6: Implement Series Data Fetching
**Start**: Basic FRED client exists  
**End**: `get_series_data()` method fetches time series with date filtering  
**Test**: Mock FRED response, verify data extraction and parsing  
**Deliverable**: Data retrieval from FRED API

### Task 7: Add Basic Retry Logic
**Start**: Series data fetching works  
**End**: Failed API requests retry 3 times with exponential backoff  
**Test**: Mock network failures, verify retry behavior  
**Deliverable**: Resilient API communication

### Task 8: Create CSV Storage for Single Indicator
**Start**: Macro directory exists  
**End**: Write MacroIndicatorRecord to CSV with proper headers  
**Test**: Create record, write to CSV, verify format and content  
**Deliverable**: Basic data persistence

### Task 9: Add Data Deduplication
**Start**: CSV writing works  
**End**: Skip records that already exist (by date) when writing  
**Test**: Write same data twice, verify no duplicates  
**Deliverable**: Data integrity protection

### Task 10: Implement Batch CSV Operations
**Start**: Single record storage works  
**End**: Write multiple records efficiently, read existing data for deduplication  
**Test**: Write batch of records, verify all present and no duplicates  
**Deliverable**: Efficient batch storage and retrieval

### Phase 3: Collection Service (Tasks 11-14)

### Task 11: Create Macro Collector Service
**Start**: API client and storage exist  
**End**: `MacroDataCollector` class that fetches one indicator and saves to CSV  
**Test**: Mock API, collect VIX data, verify CSV file created correctly  
**Deliverable**: Core collection functionality

### Task 12: Add All Indicators Collection
**Start**: Single indicator collection works  
**End**: `collect_all_indicators()` processes all 4 configured indicators  
**Test**: Mock API for all indicators, verify 4 CSV files created  
**Deliverable**: Complete macro data collection

### Task 13: Add Basic Missing Data Handling
**Start**: Collection works with complete data  
**End**: Handle missing values by marking as None, don't crash on gaps  
**Test**: Mock API with missing data points, verify graceful handling  
**Deliverable**: Robust data processing

### Task 14: Add Collection Error Handling
**Start**: Collection works in happy path  
**End**: Continue with other indicators if one fails, log errors clearly  
**Test**: Mock API failure for one indicator, verify others still collect  
**Deliverable**: Partial failure resilience

### Phase 4: CLI Integration (Tasks 15-16)

### Task 15: Add Macro CLI Arguments
**Start**: Existing main.py CLI  
**End**: Add `--collect-macro` and `--macro-indicators` arguments  
**Test**: Parse various argument combinations, verify correct handling  
**Deliverable**: CLI interface for macro collection

### Task 16: Implement Macro Collection Execution
**Start**: CLI arguments exist  
**End**: Execute macro collection when `--collect-macro` used  
**Test**: Run CLI command, verify macro data collected and saved  
**Deliverable**: End-to-end working macro collection via CLI

### Phase 5: Basic Monitoring (Tasks 17-18)

### Task 17: Add Basic Health Check
**Start**: Existing health monitoring  
**End**: Include macro data freshness in `/health` endpoint  
**Test**: Create fresh/stale macro data, verify health status reflects reality  
**Deliverable**: Basic macro health monitoring

### Task 18: Add Structured Logging
**Start**: Basic collection works  
**End**: Log collection metrics in structured format (records collected, errors, timing)  
**Test**: Run collection, verify metrics appear in logs  
**Deliverable**: Operational visibility

## MVP Validation Criteria

✅ **Core Functionality**
- Collect all 4 macro indicators (VIX, DXY, Treasury 10Y, Fed Funds Rate) from FRED API
- Save data to properly formatted CSV files in `data/raw/macro/`
- Handle API failures gracefully without crashing
- Deduplicate data to prevent duplicate records

✅ **CLI Integration**  
- `python3 main.py --collect-macro` collects all indicators
- `python3 main.py --collect-macro --macro-indicators VIX DXY` collects specific indicators
- Clear error messages for configuration issues

✅ **Basic Monitoring**
- Health endpoint shows macro data status
- Structured logging shows collection results and any errors

✅ **Data Quality**
- CSV files have proper headers and consistent formatting
- Missing data doesn't crash the system
- Date-based deduplication works correctly

**Estimated Development Time**: 12-16 hours across 18 focused tasks

**What's NOT included in MVP** (can be added later):
- Historical backfill functionality
- Data interpolation/forward-fill
- Combined dataset exports  
- Advanced health monitoring
- Performance metrics
- Configuration validation
- Comprehensive test coverage
- Data archival features

This simplified plan delivers a working macro indicators add-on with the absolute minimum viable features.