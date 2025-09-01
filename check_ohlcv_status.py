#!/usr/bin/env python3
"""
Script to check the latest OHLCV data status for all cryptocurrencies.
This script will:
1. Connect to the database
2. Get all unique cryptocurrencies
3. Check the latest timestamp for each
4. Report on data freshness
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def get_db_path():
    """Get the database path."""
    # Try to find the database in the expected location
    possible_paths = [
        "data/crypto_data.db",
        "src/data/crypto_data.db",
        "../data/crypto_data.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If not found, ask user
    print("Database not found in expected locations. Please enter the path to crypto_data.db:")
    return input().strip()

def check_ohlcv_status():
    """Check OHLCV data status for all cryptocurrencies."""
    
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return
    
    print(f"Checking OHLCV data status from: {db_path}")
    print("=" * 80)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        
        # Get all unique cryptocurrencies
        crypto_query = """
        SELECT DISTINCT cryptocurrency 
        FROM crypto_ohlcv 
        ORDER BY cryptocurrency
        """
        
        cryptos = pd.read_sql_query(crypto_query, conn)
        
        if cryptos.empty:
            print("No cryptocurrencies found in database.")
            return
        
        print(f"Found {len(cryptos)} cryptocurrencies in database:")
        print()
        
        # Check latest data for each crypto
        results = []
        current_time = datetime.now()
        
        for _, row in cryptos.iterrows():
            crypto = row['cryptocurrency']
            
            # Get latest timestamp for this crypto
            latest_query = """
            SELECT timestamp, date_str, open, high, low, close, volume
            FROM crypto_ohlcv 
            WHERE cryptocurrency = ?
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            latest_data = pd.read_sql_query(latest_query, conn, params=(crypto,))
            
            if not latest_data.empty:
                latest_row = latest_data.iloc[0]
                latest_timestamp = latest_row['timestamp']
                # Convert milliseconds to seconds if needed
                if latest_timestamp > 9999999999:  # If timestamp is in milliseconds
                    latest_timestamp = latest_timestamp / 1000
                latest_datetime = datetime.fromtimestamp(latest_timestamp)
                age = current_time - latest_datetime
                age_hours = age.total_seconds() / 3600
                
                # Determine status
                if age_hours <= 1:
                    status = "🟢 FRESH (< 1 hour)"
                elif age_hours <= 24:
                    status = "🟡 RECENT (< 24 hours)"
                elif age_hours <= 168:  # 7 days
                    status = "🟠 OLD (< 7 days)"
                else:
                    status = "🔴 STALE (> 7 days)"
                
                results.append({
                    'crypto': crypto,
                    'latest_timestamp': latest_timestamp,
                    'latest_datetime': latest_datetime,
                    'age_hours': age_hours,
                    'status': status,
                    'price': latest_row['close'],
                    'volume': latest_row['volume']
                })
            else:
                results.append({
                    'crypto': crypto,
                    'latest_timestamp': None,
                    'latest_datetime': None,
                    'age_hours': None,
                    'status': "❌ NO DATA",
                    'price': None,
                    'volume': None
                })
        
        # Display results in a table format
        print(f"{'Cryptocurrency':<15} {'Latest Data':<20} {'Age':<12} {'Status':<20} {'Price':<12} {'Volume':<15}")
        print("-" * 100)
        
        fresh_count = 0
        total_count = len(results)
        
        for result in results:
            crypto = result['crypto']
            status = result['status']
            
            if result['latest_datetime']:
                latest_str = result['latest_datetime'].strftime('%Y-%m-%d %H:%M')
                age_str = f"{result['age_hours']:.1f}h" if result['age_hours'] else "N/A"
                price_str = f"${result['price']:.2f}" if result['price'] else "N/A"
                volume_str = f"{result['volume']:,.0f}" if result['volume'] else "N/A"
                
                if "FRESH" in status:
                    fresh_count += 1
            else:
                latest_str = "N/A"
                age_str = "N/A"
                price_str = "N/A"
                volume_str = "N/A"
            
            print(f"{crypto:<15} {latest_str:<20} {age_str:<12} {status:<20} {price_str:<12} {volume_str:<15}")
        
        print("-" * 100)
        print(f"Summary: {fresh_count}/{total_count} cryptocurrencies have fresh data (< 1 hour old)")
        
        # Get total record counts
        total_records_query = "SELECT COUNT(*) as total FROM crypto_ohlcv"
        total_records = pd.read_sql_query(total_records_query, conn).iloc[0]['total']
        
        print(f"Total OHLCV records in database: {total_records:,}")
        
        # Check for any cryptos with very old data (> 7 days)
        stale_cryptos = [r['crypto'] for r in results if r['age_hours'] and r['age_hours'] > 168]
        if stale_cryptos:
            print(f"\n⚠️  Cryptocurrencies with stale data (> 7 days): {', '.join(stale_cryptos)}")
        
        # Check for cryptos with no data
        no_data_cryptos = [r['crypto'] for r in results if r['latest_timestamp'] is None]
        if no_data_cryptos:
            print(f"\n❌ Cryptocurrencies with no data: {', '.join(no_data_cryptos)}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ohlcv_status()
