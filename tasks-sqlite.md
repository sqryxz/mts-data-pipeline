# CSV to SQLite Migration: Granular MVP Plan

## **Phase 1: Database Foundation (Tasks 1-6)**

### Task 1: Create SQLite Schema File
**Start**: Empty repository  
**End**: Complete `src/data/schema.sql` file with all table definitions  
**Test**: File exists and contains valid SQL syntax  
**Deliverable**: SQL schema file for crypto_ohlcv and macro_indicators tables

**Specific Requirements:**
- Create `src/data/schema.sql`
- Include crypto_ohlcv table with exact columns: id, cryptocurrency, timestamp, date_str, open, high, low, close, volume, created_at
- Include macro_indicators table with: id, indicator, date, value, is_interpolated, is_forward_filled, created_at
- Add UNIQUE constraints to prevent duplicates
- Include basic indexes

### Task 2: Create Database Connection Manager
**Start**: Schema file exists  
**End**: `src/data/db_connection.py` with working connection context manager  
**Test**: Can create database file and establish connection without errors  
**Deliverable**: Database connection utility class

**Specific Requirements:**
- Create `DatabaseConnection` class with `get_connection()` context manager
- Set default database path to `data/crypto_data.db`
- Enable row factory for column access by name
- Include proper connection cleanup

### Task 3: Create Database Initializer
**Start**: Connection manager exists  
**End**: `src/data/db_init.py` that creates tables from schema  
**Test**: Run initializer, verify tables exist with correct structure  
**Deliverable**: Database initialization function

**Specific Requirements:**
- Read schema.sql file and execute it
- Create `initialize_database()` function
- Handle "table already exists" gracefully
- Log successful initialization

### Task 4: Create Basic Database Helper Class
**Start**: Database initializer works  
**End**: `src/data/sqlite_helper.py` with CryptoDatabase class stub  
**Test**: Can instantiate CryptoDatabase class and it creates database file  
**Deliverable**: Empty database helper class that initializes database

**Specific Requirements:**
- Create `CryptoDatabase` class with `__init__` method
- Auto-initialize database on instantiation
- Include database path configuration
- Add basic logging

### Task 5: Add Crypto Data Insert Method
**Start**: Basic CryptoDatabase class exists  
**End**: `insert_crypto_data()` method that accepts list of dictionaries  
**Test**: Insert single crypto record, verify it appears in database  
**Deliverable**: Working crypto data insertion with duplicate handling

**Specific Requirements:**
- Method signature: `insert_crypto_data(self, crypto_data: List[Dict]) -> int`
- Use INSERT OR IGNORE for duplicate handling
- Return count of inserted records
- Handle all crypto_ohlcv columns

### Task 6: Add Macro Data Insert Method
**Start**: Crypto insert method works  
**End**: `insert_macro_data()` method for macro indicators  
**Test**: Insert single macro record, verify it appears in database  
**Deliverable**: Working macro data insertion with duplicate handling

**Specific Requirements:**
- Method signature: `insert_macro_data(self, macro_data: List[Dict]) -> int`
- Use INSERT OR IGNORE for duplicate handling
- Return count of inserted records
- Handle all macro_indicators columns

## **Phase 2: Data Query Methods (Tasks 7-10)**

### Task 7: Add Latest Data Query Methods
**Start**: Insert methods work  
**End**: Methods to get latest timestamp/date for incremental collection  
**Test**: Insert data, query latest values, verify correct results  
**Deliverable**: `get_latest_crypto_timestamp()` and `get_latest_macro_date()` methods

**Specific Requirements:**
- `get_latest_crypto_timestamp(cryptocurrency: str) -> Optional[int]`
- `get_latest_macro_date(indicator: str) -> Optional[str]`
- Return None if no data exists
- Handle empty database gracefully

### Task 8: Add DataFrame Query Method
**Start**: Latest data queries work  
**End**: Generic SQL-to-DataFrame conversion method  
**Test**: Execute simple SELECT query, verify DataFrame output  
**Deliverable**: `query_to_dataframe()` method for analysis

**Specific Requirements:**
- Method signature: `query_to_dataframe(self, sql: str, params: tuple = ()) -> pd.DataFrame`
- Use pandas.read_sql_query()
- Support parameterized queries
- Return empty DataFrame if no results

### Task 9: Add Crypto Data Retrieval Method
**Start**: DataFrame query method works  
**End**: `get_crypto_data()` method for recent crypto data  
**Test**: Insert crypto data, retrieve last 7 days, verify correct filtering  
**Deliverable**: Convenient crypto data retrieval for analysis

**Specific Requirements:**
- Method signature: `get_crypto_data(cryptocurrency: str, days: int = 30) -> pd.DataFrame`
- Filter by cryptocurrency and date range
- Order by timestamp ascending
- Return all OHLCV columns

### Task 10: Add Health Status Method
**Start**: Crypto data retrieval works  
**End**: `get_health_status()` method returning database metrics  
**Test**: Insert test data, call health status, verify correct counts and dates  
**Deliverable**: Database health monitoring for operational visibility

**Specific Requirements:**
- Return dict with crypto_data and macro_data arrays
- Include latest_date and total_records for each symbol/indicator
- Add database_path and database_size_mb
- Handle empty database gracefully

## **Phase 3: CSV Migration Scripts (Tasks 11-14)**

### Task 11: Create Basic CSV Migration Script
**Start**: Database helper is complete  
**End**: `scripts/migrate_csv_to_sqlite.py` that processes one CSV file  
**Test**: Run with single crypto CSV file, verify data migrated correctly  
**Deliverable**: Working migration for single crypto CSV file

**Specific Requirements:**
- Hard-code single CSV file path for testing
- Extract cryptocurrency name from filename
- Convert timestamp to date_str format
- Insert all records and report count

### Task 12: Add Batch CSV Processing
**Start**: Single file migration works  
**End**: Process all crypto CSV files in data/raw/ directory  
**Test**: Run with multiple CSV files, verify all data migrated  
**Deliverable**: Complete crypto CSV migration capability

**Specific Requirements:**
- Scan data/raw/ for *.csv files
- Process each file automatically
- Log progress and results for each file
- Continue processing if one file fails

### Task 13: Add Macro CSV Migration
**Start**: Crypto CSV migration works  
**End**: Process macro CSV files from data/raw/macro/  
**Test**: Create test macro CSV, run migration, verify data appears in database  
**Deliverable**: Complete macro data migration capability

**Specific Requirements:**
- Look for CSV files in data/raw/macro/ directory
- Extract indicator name from filename
- Handle missing macro directory gracefully
- Use same logging pattern as crypto migration

### Task 14: Add Migration Verification
**Start**: All CSV migration works  
**End**: Verification function that reports migration success  
**Test**: Run full migration, verify reports match actual database contents  
**Deliverable**: Migration verification and reporting

**Specific Requirements:**
- Call database health_status() after migration
- Display summary of migrated data
- Show before/after record counts
- Report any missing or failed migrations

## **Phase 4: Update Collection Services (Tasks 15-18)**

### Task 15: Update Crypto Collector to Use SQLite
**Start**: Current crypto collector saves to CSV  
**End**: `CryptoDataCollector` saves to SQLite database  
**Test**: Run crypto collection, verify new data appears in database  
**Deliverable**: SQLite-enabled crypto data collection

**Specific Requirements:**
- Replace CSV file operations with database calls
- Use `get_latest_crypto_timestamp()` for incremental collection
- Use `insert_crypto_data()` for saving new records
- Remove CSV-related imports and methods

### Task 16: Update Macro Collector to Use SQLite
**Start**: Macro collector works (if implemented)  
**End**: Macro data collector saves to SQLite database  
**Test**: Run macro collection, verify new data appears in database  
**Deliverable**: SQLite-enabled macro data collection

**Specific Requirements:**
- Replace CSV operations with database calls
- Use `get_latest_macro_date()` for incremental collection
- Use `insert_macro_data()` for saving new records
- Handle all 4 macro indicators (VIX, DXY, Treasury, Fed Funds)

### Task 17: Update CLI to Support Database Operations
**Start**: CLI currently handles CSV operations  
**End**: CLI commands work with SQLite database  
**Test**: Run CLI commands, verify database operations work correctly  
**Deliverable**: Updated CLI interface for database operations

**Specific Requirements:**
- Update main.py to use database instead of CSV
- Ensure --collect-crypto uses database
- Ensure --collect-macro uses database (if implemented)
- Add database path configuration option

### Task 18: Update Health Monitoring
**Start**: Health endpoint checks CSV files  
**End**: Health endpoint queries SQLite database  
**Test**: Check health endpoint, verify database metrics displayed  
**Deliverable**: Database-aware health monitoring

**Specific Requirements:**
- Replace CSV file checking with database health_status()
- Show latest data timestamps from database
- Include database size and record counts
- Handle database connection failures gracefully

## **Phase 5: Analysis Capabilities (Tasks 19-20)**

### Task 19: Add Combined Analysis Query
**Start**: Basic database queries work  
**End**: Method to get crypto data with macro indicators joined  
**Test**: Insert crypto and macro data, run combined query, verify join works  
**Deliverable**: Combined dataset query for analysis

**Specific Requirements:**
- Method signature: `get_combined_analysis_data(cryptocurrency: str, days: int = 30) -> pd.DataFrame`
- LEFT JOIN crypto data with all 4 macro indicators by date
- Return single DataFrame with price, volume, and all macro values
- Handle missing macro data gracefully

### Task 20: Create Basic Analysis Examples
**Start**: Combined query method works  
**End**: `examples/sqlite_analysis.py` with sample queries  
**Test**: Run example script, verify queries execute and produce results  
**Deliverable**: Example usage of SQLite database for analysis

**Specific Requirements:**
- Show crypto price trends query
- Show macro correlation analysis query
- Demonstrate filtering and aggregation
- Include basic visualization using pandas/matplotlib

## **Validation Criteria**

### **Critical Success Metrics:**
✅ **Data Integrity**: All CSV data successfully migrated without loss  
✅ **Duplicate Handling**: No duplicate records created during migration or collection  
✅ **Incremental Collection**: New data collection only fetches missing records  
✅ **Query Performance**: Basic queries execute in <1 second  
✅ **CLI Compatibility**: All existing CLI commands work with database  
✅ **Health Monitoring**: Database status visible in health endpoint  

### **Test Database Creation:**
After each phase, create test database with sample data to verify functionality independently.

**Total Estimated Time**: 8-12 hours across 20 atomic tasks  
**Each Task**: 20-40 minutes of focused work  
**Testing Time**: 5-10 minutes per task  

This plan ensures each task is completely independent and testable, allowing you to verify progress incrementally and catch issues early.

db = CryptoDatabase()
# Test insertions, queries, health status, etc.
status = db.get_health_status()
print(status)