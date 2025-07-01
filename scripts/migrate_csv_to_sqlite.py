#!/usr/bin/env python3
"""
CSV to SQLite Migration Script
Basic migration script that processes a single crypto CSV file for testing.
"""

import os
import sys
import logging
import pandas as pd
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import glob
from typing import List, Dict, Tuple, Any

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.sqlite_helper import CryptoDatabase


def safe_float_conversion(value, field_name: str, default: float = 0.0) -> float:
    """
    Safely convert value to float with error handling.
    
    Args:
        value: Value to convert
        field_name: Name of field for logging
        default: Default value if conversion fails
        
    Returns:
        float: Converted value or default
    """
    try:
        if pd.isna(value):
            logging.warning(f"NaN value found in {field_name}, using default {default}")
            return default
        return float(value)
    except (ValueError, TypeError) as e:
        logging.warning(f"Invalid {field_name} value '{value}': {e}, using default {default}")
        return default


def validate_ohlcv_record(open_val: float, high_val: float, low_val: float, close_val: float, volume_val: float) -> bool:
    """
    Validate OHLCV data for business logic correctness.
    
    Args:
        open_val, high_val, low_val, close_val, volume_val: OHLCV values
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if volume_val < 0:
        raise ValueError(f"Negative volume: {volume_val}")
    
    if not (low_val <= open_val <= high_val and low_val <= close_val <= high_val):
        raise ValueError(f"Invalid OHLCV relationship: O={open_val}, H={high_val}, L={low_val}, C={close_val}")
    
    return True


def convert_timestamp_to_date_str(timestamp: int) -> str:
    """
    Convert timestamp in milliseconds to date string format.
    
    Args:
        timestamp: Timestamp in milliseconds
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.strftime('%Y-%m-%d')


def extract_cryptocurrency_name(filename: str) -> str:
    """
    Extract cryptocurrency name from CSV filename.
    
    Args:
        filename: CSV filename (e.g., 'bitcoin_2025.csv')
        
    Returns:
        str: Cryptocurrency name (e.g., 'bitcoin')
    """
    # Remove file extension and extract name before first underscore
    base_name = Path(filename).stem
    crypto_name = base_name.split('_')[0]
    return crypto_name.lower()


def extract_indicator_name(filename: str) -> str:
    """
    Extract macro indicator name from CSV filename.
    
    Args:
        filename: CSV filename (e.g., 'vixcls_2025.csv', 'dff_2025.csv')
        
    Returns:
        str: Indicator name (e.g., 'VIXCLS', 'DFF')
    """
    # Remove file extension and extract name before first underscore
    base_name = Path(filename).stem
    indicator_name = base_name.split('_')[0]
    return indicator_name.upper()


def process_csv_file(csv_path: str, db: CryptoDatabase) -> int:
    """
    Process a single CSV file and migrate data to SQLite.
    
    Args:
        csv_path: Path to the CSV file
        db: CryptoDatabase instance
        
    Returns:
        int: Number of records inserted
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Extract cryptocurrency name from filename
    filename = os.path.basename(csv_path)
    cryptocurrency = extract_cryptocurrency_name(filename)
    
    logger.info(f"Processing {filename} for cryptocurrency: {cryptocurrency}")
    
    # Read CSV file with error handling
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            logger.warning(f"CSV file {csv_path} is empty, skipping")
            return 0
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty or corrupted")
    except UnicodeDecodeError:
        raise ValueError("CSV file encoding issue")
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")
    
    logger.info(f"Loaded {len(df)} records from CSV")
    
    # Validate required columns
    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Convert to the format expected by database
    crypto_records = []
    skipped_records = 0
    
    for idx, row in df.iterrows():
        try:
            # Safe conversion of OHLCV data
            open_val = safe_float_conversion(row['open'], 'open')
            high_val = safe_float_conversion(row['high'], 'high')
            low_val = safe_float_conversion(row['low'], 'low')
            close_val = safe_float_conversion(row['close'], 'close')
            volume_val = safe_float_conversion(row['volume'], 'volume')
            
            # Validate OHLCV data
            validate_ohlcv_record(open_val, high_val, low_val, close_val, volume_val)
            
            # Handle timestamp conversion
            timestamp = int(row['timestamp']) if pd.notna(row['timestamp']) else 0
            date_str = convert_timestamp_to_date_str(timestamp)
            
            record = {
                'cryptocurrency': cryptocurrency,
                'timestamp': timestamp,
                'date_str': date_str,
                'open': open_val,
                'high': high_val,
                'low': low_val,
                'close': close_val,
                'volume': volume_val
            }
            crypto_records.append(record)
            
        except ValueError as e:
            logger.warning(f"Skipping invalid record at row {idx}: {e}")
            skipped_records += 1
            continue
    
    if skipped_records > 0:
        logger.info(f"Skipped {skipped_records} invalid records out of {len(df)} total")
    
    # Insert into database
    inserted_count = db.insert_crypto_data(crypto_records)
    
    logger.info(f"Migration complete: {inserted_count} records inserted for {cryptocurrency} ({skipped_records} skipped)")
    return inserted_count


def process_macro_csv_file(csv_path: str, db: CryptoDatabase) -> int:
    """
    Process a single macro CSV file and migrate data to SQLite.
    
    Args:
        csv_path: Path to the macro CSV file
        db: CryptoDatabase instance
        
    Returns:
        int: Number of records inserted
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Macro CSV file not found: {csv_path}")
    
    # Extract indicator name from filename
    filename = os.path.basename(csv_path)
    indicator = extract_indicator_name(filename)
    
    logger.info(f"Processing {filename} for indicator: {indicator}")
    
    # Read CSV file with error handling
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            logger.warning(f"Macro CSV file {csv_path} is empty, skipping")
            return 0
    except pd.errors.EmptyDataError:
        raise ValueError("Macro CSV file is empty or corrupted")
    except UnicodeDecodeError:
        raise ValueError("Macro CSV file encoding issue")
    except Exception as e:
        raise ValueError(f"Failed to read macro CSV file: {e}")
    
    logger.info(f"Loaded {len(df)} records from macro CSV")
    
    # Validate required columns for macro data
    required_columns = ['date', 'value']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Convert to the format expected by database
    macro_records = []
    skipped_records = 0
    
    for idx, row in df.iterrows():
        try:
            # Skip records with empty values
            if pd.isna(row['value']) or row['value'] == '':
                logger.debug(f"Skipping record at row {idx}: empty value")
                skipped_records += 1
                continue
            
            # Safe conversion of value
            value = safe_float_conversion(row['value'], 'value')
            
            # Validate value is reasonable (not negative for most indicators)
            if value < 0:
                logger.warning(f"Negative value {value} for {indicator} at row {idx}")
            
            # Handle date (should already be in YYYY-MM-DD format)
            date_str = str(row['date']).strip()
            if not date_str:
                logger.warning(f"Skipping record at row {idx}: empty date")
                skipped_records += 1
                continue
            
            # Handle boolean fields with safe conversion
            is_interpolated = False
            is_forward_filled = False
            
            if 'is_interpolated' in df.columns:
                is_interpolated = str(row['is_interpolated']).lower() in ['true', '1', 'yes']
            
            if 'is_forward_filled' in df.columns:
                is_forward_filled = str(row['is_forward_filled']).lower() in ['true', '1', 'yes']
            
            record = {
                'indicator': indicator,
                'date': date_str,
                'value': value,
                'is_interpolated': is_interpolated,
                'is_forward_filled': is_forward_filled
            }
            macro_records.append(record)
            
        except ValueError as e:
            logger.warning(f"Skipping invalid macro record at row {idx}: {e}")
            skipped_records += 1
            continue
    
    if skipped_records > 0:
        logger.info(f"Skipped {skipped_records} invalid records out of {len(df)} total")
    
    # Insert into database
    inserted_count = db.insert_macro_data(macro_records)
    
    logger.info(f"Macro migration complete: {inserted_count} records inserted for {indicator} ({skipped_records} skipped)")
    return inserted_count


def scan_crypto_csv_files(directory: str = "data/raw") -> List[str]:
    """
    Scan directory for crypto CSV files.
    
    Args:
        directory: Directory to scan for CSV files
        
    Returns:
        List[str]: List of CSV file paths found
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return []
    
    # Look for CSV files in the directory
    csv_pattern = os.path.join(directory, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    # Filter out files that don't look like crypto files (basic heuristic)
    crypto_files = []
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        # Skip files that might be macro data or other non-crypto files
        if not filename.startswith('.') and '_' in filename:
            crypto_files.append(file_path)
    
    crypto_files.sort()  # Process in consistent order
    logger.info(f"Found {len(crypto_files)} crypto CSV files in {directory}")
    
    return crypto_files


def scan_macro_csv_files(directory: str = "data/raw/macro") -> List[str]:
    """
    Scan directory for macro indicator CSV files.
    
    Args:
        directory: Directory to scan for macro CSV files
        
    Returns:
        List[str]: List of macro CSV file paths found
    """
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(directory):
        logger.info(f"Macro directory {directory} does not exist, skipping macro migration")
        return []
    
    # Look for CSV files in the macro directory
    csv_pattern = os.path.join(directory, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    # Filter out hidden files
    macro_files = []
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        if not filename.startswith('.'):
            macro_files.append(file_path)
    
    macro_files.sort()  # Process in consistent order
    logger.info(f"Found {len(macro_files)} macro CSV files in {directory}")
    
    return macro_files


def process_batch_migration(csv_files: List[str], db: CryptoDatabase) -> Dict[str, any]:
    """
    Process multiple CSV files in batch.
    
    Args:
        csv_files: List of CSV file paths to process
        db: CryptoDatabase instance
        
    Returns:
        Dict: Summary of migration results
    """
    logger = logging.getLogger(__name__)
    
    results = {
        'total_files': len(csv_files),
        'successful_files': 0,
        'failed_files': 0,
        'total_records_inserted': 0,
        'file_results': [],
        'errors': []
    }
    
    logger.info(f"Starting batch migration of {len(csv_files)} files")
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        logger.info(f"Processing file: {filename}")
        
        try:
            inserted_count = process_csv_file(file_path, db)
            
            # Record successful migration
            results['successful_files'] += 1
            results['total_records_inserted'] += inserted_count
            results['file_results'].append({
                'filename': filename,
                'status': 'success',
                'records_inserted': inserted_count
            })
            
            logger.info(f"✅ {filename}: {inserted_count} records inserted")
            
        except Exception as e:
            # Record failed migration but continue with other files
            results['failed_files'] += 1
            results['file_results'].append({
                'filename': filename,
                'status': 'failed',
                'error': str(e)
            })
            results['errors'].append(f"{filename}: {str(e)}")
            
            logger.error(f"❌ {filename}: Migration failed - {e}")
            # Continue processing other files
            continue
    
    logger.info(f"Batch migration complete: {results['successful_files']}/{results['total_files']} files successful")
    return results


def process_macro_batch_migration(macro_files: List[str], db: CryptoDatabase) -> Dict[str, any]:
    """
    Process multiple macro CSV files in batch.
    
    Args:
        macro_files: List of macro CSV file paths to process
        db: CryptoDatabase instance
        
    Returns:
        Dict: Summary of macro migration results
    """
    logger = logging.getLogger(__name__)
    
    results = {
        'total_files': len(macro_files),
        'successful_files': 0,
        'failed_files': 0,
        'total_records_inserted': 0,
        'file_results': [],
        'errors': []
    }
    
    if not macro_files:
        logger.info("No macro files to process")
        return results
    
    logger.info(f"Starting macro batch migration of {len(macro_files)} files")
    
    for file_path in macro_files:
        filename = os.path.basename(file_path)
        logger.info(f"Processing macro file: {filename}")
        
        try:
            inserted_count = process_macro_csv_file(file_path, db)
            
            # Record successful migration
            results['successful_files'] += 1
            results['total_records_inserted'] += inserted_count
            results['file_results'].append({
                'filename': filename,
                'status': 'success',
                'records_inserted': inserted_count
            })
            
            logger.info(f"✅ {filename}: {inserted_count} records inserted")
            
        except Exception as e:
            # Record failed migration but continue with other files
            results['failed_files'] += 1
            results['file_results'].append({
                'filename': filename,
                'status': 'failed',
                'error': str(e)
            })
            results['errors'].append(f"{filename}: {str(e)}")
            
            logger.error(f"❌ {filename}: Macro migration failed - {e}")
            # Continue processing other files
            continue
    
    logger.info(f"Macro batch migration complete: {results['successful_files']}/{results['total_files']} files successful")
    return results


def main():
    """Main function to run batch CSV migration."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check for command line argument to run single file mode (for testing)
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Single file mode for testing
        csv_file_path = "data/raw/bitcoin_2025.csv"
        
        try:
            logger.info("Running in single file test mode")
            db = CryptoDatabase()
            
            logger.info(f"Starting migration of {csv_file_path}")
            inserted_count = process_csv_file(csv_file_path, db)
            
            logger.info(f"Migration successful: {inserted_count} records inserted")
            print(f"✅ Migration complete: {inserted_count} records inserted from {csv_file_path}")
            
        except FileNotFoundError as e:
            logger.error(f"File error: {e}")
            print(f"❌ Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"❌ Migration failed: {e}")
            sys.exit(1)
    
    else:
        # Batch mode - process all CSV files in data/raw/ and data/raw/macro/
        try:
            logger.info("Starting batch CSV migration")
            
            # Initialize database
            logger.info("Initializing database...")
            db = CryptoDatabase()
            
            # Scan for crypto CSV files
            crypto_files = scan_crypto_csv_files("data/raw")
            # Scan for macro CSV files  
            macro_files = scan_macro_csv_files("data/raw/macro")
            
            if not crypto_files and not macro_files:
                print("❌ No CSV files found in data/raw/ or data/raw/macro/ directories")
                logger.warning("No CSV files found for migration")
                sys.exit(1)
            
            # Process crypto files
            crypto_results = {'total_files': 0, 'successful_files': 0, 'failed_files': 0, 'total_records_inserted': 0, 'file_results': [], 'errors': []}
            if crypto_files:
                logger.info(f"Found {len(crypto_files)} crypto files to process")
                crypto_results = process_batch_migration(crypto_files, db)
            
            # Process macro files
            macro_results = {'total_files': 0, 'successful_files': 0, 'failed_files': 0, 'total_records_inserted': 0, 'file_results': [], 'errors': []}
            if macro_files:
                logger.info(f"Found {len(macro_files)} macro files to process")
                macro_results = process_macro_batch_migration(macro_files, db)
            
            # Combine results
            total_files = crypto_results['total_files'] + macro_results['total_files']
            total_successful = crypto_results['successful_files'] + macro_results['successful_files']
            total_failed = crypto_results['failed_files'] + macro_results['failed_files']
            total_records = crypto_results['total_records_inserted'] + macro_results['total_records_inserted']
            all_file_results = crypto_results['file_results'] + macro_results['file_results']
            all_errors = crypto_results['errors'] + macro_results['errors']
            
            # Report summary
            print(f"\n🎉 Batch Migration Complete!")
            print(f"📊 Summary:")
            print(f"  • Total files processed: {total_files}")
            print(f"  • Successful migrations: {total_successful}")
            print(f"  • Failed migrations: {total_failed}")
            print(f"  • Total records inserted: {total_records}")
            
            if crypto_files:
                print(f"\n💰 Crypto Results: {crypto_results['successful_files']}/{crypto_results['total_files']} files, {crypto_results['total_records_inserted']} records")
            
            if macro_files:
                print(f"📈 Macro Results: {macro_results['successful_files']}/{macro_results['total_files']} files, {macro_results['total_records_inserted']} records")
            
            if all_file_results:
                print(f"\n📝 Detailed Results:")
                for result in all_file_results:
                    if result['status'] == 'success':
                        print(f"  ✅ {result['filename']}: {result['records_inserted']} records")
                    else:
                        print(f"  ❌ {result['filename']}: {result['error']}")
            
            if all_errors:
                print(f"\n⚠️  Errors encountered:")
                for error in all_errors:
                    print(f"  • {error}")
                sys.exit(1)
            
            # Verification step
            print(f"\n🔍 Migration Verification:")
            verification_results = verify_migration(db)
            display_verification_results(verification_results)
            
            logger.info("Batch migration completed successfully")
            
        except Exception as e:
            logger.error(f"Batch migration failed: {e}")
            print(f"❌ Batch migration failed: {e}")
            sys.exit(1)


def enhanced_data_quality_checks(health_status: Dict[str, Any]) -> List[str]:
    """
    Perform enhanced data quality validation checks.
    
    Args:
        health_status: Database health status dictionary
        
    Returns:
        List[str]: List of data quality issues found
    """
    issues = []
    
    # Check crypto data quality
    for crypto in health_status.get('crypto_data', []):
        symbol = crypto.get('symbol', 'Unknown')
        total_records = crypto.get('total_records', 0)
        
        # Check for reasonable record counts
        if total_records > 100000:  # More than 100k records seems excessive for test data
            issues.append(f"{symbol}: Very high record count ({total_records:,}) - possible data duplication")
        elif total_records > 0 and total_records < 10:  # Very few records
            issues.append(f"{symbol}: Very low record count ({total_records}) - possible incomplete migration")
    
    # Check macro data quality
    for macro in health_status.get('macro_data', []):
        indicator = macro.get('indicator', 'Unknown')
        total_records = macro.get('total_records', 0)
        
        # Macro indicators should have reasonable data points
        if total_records > 10000:  # Too many macro records
            issues.append(f"{indicator}: Excessive macro records ({total_records:,}) - possible data issue")
        elif total_records > 0 and total_records < 5:  # Very few macro records
            issues.append(f"{indicator}: Very few macro records ({total_records}) - possible incomplete data")
    
    return issues


def verify_migration(db: CryptoDatabase) -> Dict[str, Any]:
    """
    Verify migration success by reporting database contents with comprehensive validation.
    
    Args:
        db: CryptoDatabase instance
        
    Returns:
        Dict: Verification results with performance metrics and quality checks
    """
    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    try:
        # Get current database health status
        logger.info("Retrieving database health status...")
        health_status = db.get_health_status()
        
        verification_results = {
            'database_path': health_status['database_path'],
            'database_size_mb': health_status['database_size_mb'],
            'crypto_summary': {
                'total_symbols': len(health_status['crypto_data']),
                'total_records': sum(crypto['total_records'] for crypto in health_status['crypto_data']),
                'symbols': health_status['crypto_data']
            },
            'macro_summary': {
                'total_indicators': len(health_status['macro_data']),
                'total_records': sum(macro['total_records'] for macro in health_status['macro_data']),
                'indicators': health_status['macro_data']
            },
            'verification_passed': True,
            'issues': [],
            'verification_time_seconds': 0.0
        }
        
        # Perform basic data validation checks
        logger.info("Performing data validation checks...")
        
        # Check for expected data completeness
        if verification_results['crypto_summary']['total_records'] == 0:
            verification_results['issues'].append("No crypto data found in database")
        
        if verification_results['macro_summary']['total_records'] == 0:
            verification_results['issues'].append("No macro data found in database")
        
        # Check for reasonable data ranges
        for crypto in health_status['crypto_data']:
            symbol = crypto.get('symbol', 'Unknown')
            if crypto.get('total_records', 0) == 0:
                verification_results['issues'].append(f"No records found for {symbol}")
        
        for macro in health_status['macro_data']:
            indicator = macro.get('indicator', 'Unknown')
            if macro.get('total_records', 0) == 0:
                verification_results['issues'].append(f"No records found for {indicator}")
        
        # Check database file size is reasonable
        if verification_results['database_size_mb'] == 0:
            verification_results['issues'].append("Database file appears to be empty")
        
        # Perform enhanced data quality checks
        logger.info("Performing enhanced data quality checks...")
        quality_issues = enhanced_data_quality_checks(health_status)
        verification_results['issues'].extend(quality_issues)
        
        # Set overall verification status
        if verification_results['issues']:
            verification_results['verification_passed'] = False
            logger.warning(f"Verification found {len(verification_results['issues'])} issues")
        else:
            logger.info("Migration verification passed successfully")
        
        # Add performance metrics
        verification_results['verification_time_seconds'] = round(time.time() - start_time, 2)
        
        return verification_results
        
    except sqlite3.Error as e:
        logger.error(f"Database connection failed during verification: {e}")
        return {
            'verification_passed': False,
            'error': f"Database error: {e}",
            'issues': [f"Database connection error: {e}"],
            'verification_time_seconds': round(time.time() - start_time, 2)
        }
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return {
            'verification_passed': False,
            'error': f"Verification error: {e}",
            'issues': [f"Verification error: {e}"],
            'verification_time_seconds': round(time.time() - start_time, 2)
        }


def display_verification_results(results: Dict[str, Any]) -> None:
    """
    Display verification results in a user-friendly format with robust error handling.
    
    Args:
        results: Verification results dictionary
    """
    # Handle verification errors
    if 'error' in results:
        print(f"❌ Verification Error: {results['error']}")
        print(f"⏱️  Verification Time: {results.get('verification_time_seconds', 0)} seconds")
        return
    
    # Database information with safe access
    db_path = results.get('database_path', 'Unknown')
    db_size = results.get('database_size_mb', 0)
    verification_time = results.get('verification_time_seconds', 0)
    
    print(f"📊 Database: {db_path} ({db_size} MB)")
    
    # Crypto summary with safe access
    crypto_summary = results.get('crypto_summary', {})
    crypto_symbols = crypto_summary.get('total_symbols', 0)
    crypto_records = crypto_summary.get('total_records', 0)
    print(f"💰 Crypto Data: {crypto_symbols} symbols, {crypto_records:,} total records")
    
    # Display crypto details with safety checks
    crypto_symbols_list = crypto_summary.get('symbols', [])
    if crypto_symbols_list and len(crypto_symbols_list) > 0:
        for symbol_info in crypto_symbols_list:
            # Safe field access with defaults
            symbol_name = symbol_info.get('symbol', 'Unknown').upper()
            record_count = symbol_info.get('total_records', 0)
            latest_date = symbol_info.get('latest_date', 'Unknown')
            print(f"  • {symbol_name}: {record_count:,} records (latest: {latest_date})")
    elif crypto_symbols > 0:
        print("  • Symbol details unavailable")
    
    # Macro summary with safe access
    macro_summary = results.get('macro_summary', {})
    macro_indicators = macro_summary.get('total_indicators', 0)
    macro_records = macro_summary.get('total_records', 0)
    print(f"📈 Macro Data: {macro_indicators} indicators, {macro_records:,} total records")
    
    # Display macro details with safety checks
    macro_indicators_list = macro_summary.get('indicators', [])
    if macro_indicators_list and len(macro_indicators_list) > 0:
        for indicator_info in macro_indicators_list:
            # Safe field access with defaults
            indicator_name = indicator_info.get('indicator', 'Unknown')
            record_count = indicator_info.get('total_records', 0)
            latest_date = indicator_info.get('latest_date', 'Unknown')
            print(f"  • {indicator_name}: {record_count:,} records (latest: {latest_date})")
    elif macro_indicators > 0:
        print("  • Indicator details unavailable")
    
    # Overall verification status
    verification_passed = results.get('verification_passed', False)
    if verification_passed:
        print(f"✅ Migration verification: PASSED")
    else:
        print(f"❌ Migration verification: FAILED")
        issues = results.get('issues', [])
        if issues:
            print(f"⚠️  Issues found ({len(issues)}):")
            for issue in issues:
                print(f"  • {issue}")
    
    # Performance and summary metrics
    total_records = crypto_records + macro_records
    print(f"🎯 Grand Total: {total_records:,} records successfully migrated")
    print(f"⏱️  Verification Time: {verification_time} seconds")


if __name__ == "__main__":
    main() 