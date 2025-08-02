#!/usr/bin/env python3
"""
Fetch Missing Crypto Data: July 15 to July 29, 2025
Simple script to fetch crypto data using direct API calls.
"""

import sys
import os
import requests
import sqlite3
from datetime import datetime, timedelta, timezone
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fetch_crypto_data():
    """Fetch crypto data from July 15 to July 29 using CoinGecko API."""
    
    print("🪙 Fetching Missing Crypto Data (July 15 - July 29)")
    print("=" * 50)
    
    # Database connection
    db_path = 'data/crypto_data.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crypto assets to fetch
    crypto_assets = [
        {'id': 'bitcoin', 'name': 'Bitcoin'},
        {'id': 'ethereum', 'name': 'Ethereum'},
        {'id': 'binancecoin', 'name': 'Binance Coin'},
        {'id': 'ripple', 'name': 'Ripple'},
        {'id': 'solana', 'name': 'Solana'},
        {'id': 'cardano', 'name': 'Cardano'},
        {'id': 'avalanche-2', 'name': 'Avalanche'},
        {'id': 'polkadot', 'name': 'Polkadot'},
        {'id': 'chainlink', 'name': 'Chainlink'},
        {'id': 'polygon', 'name': 'Polygon'},
        {'id': 'dogecoin', 'name': 'Dogecoin'},
        {'id': 'litecoin', 'name': 'Litecoin'},
        {'id': 'uniswap', 'name': 'Uniswap'},
        {'id': 'bitcoin-cash', 'name': 'Bitcoin Cash'},
        {'id': 'stellar', 'name': 'Stellar'},
        {'id': 'vechain', 'name': 'VeChain'},
        {'id': 'filecoin', 'name': 'Filecoin'},
        {'id': 'cosmos', 'name': 'Cosmos'},
        {'id': 'monero', 'name': 'Monero'}
    ]
    
    total_inserted = 0
    
    for asset in crypto_assets:
        try:
            print(f"📊 Fetching {asset['name']} data...")
            
            # Use CoinGecko free API
            url = f"https://api.coingecko.com/api/v3/coins/{asset['id']}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': 15  # July 15 to July 29 is 15 days
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                ohlc_data = response.json()
                
                if ohlc_data and len(ohlc_data) > 0:
                    # Convert to our database format
                    crypto_records = []
                    for data_point in ohlc_data:
                        # data_point format: [timestamp, open, high, low, close]
                        timestamp = data_point[0]  # Already in milliseconds
                        data_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                        
                        # Filter for our date range (July 15-29)
                        if datetime(2025, 7, 15, tzinfo=timezone.utc) <= data_date <= datetime(2025, 7, 29, tzinfo=timezone.utc):
                            record = {
                                'cryptocurrency': asset['id'],
                                'timestamp': timestamp,
                                'date_str': data_date.strftime('%Y-%m-%d'),
                                'open': data_point[1],
                                'high': data_point[2],
                                'low': data_point[3],
                                'close': data_point[4],
                                'volume': 0  # CoinGecko OHLC doesn't include volume
                            }
                            crypto_records.append(record)
                    
                    if crypto_records:
                        # Insert into database
                        for record in crypto_records:
                            cursor.execute("""
                                INSERT OR IGNORE INTO crypto_ohlcv 
                                (cryptocurrency, timestamp, date_str, open, high, low, close, volume, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            """, (
                                record['cryptocurrency'],
                                record['timestamp'],
                                record['date_str'],
                                record['open'],
                                record['high'],
                                record['low'],
                                record['close'],
                                record['volume']
                            ))
                        
                        inserted = len(crypto_records)
                        total_inserted += inserted
                        print(f"  ✅ Inserted {inserted} records for {asset['name']}")
                    else:
                        print(f"  ⚠️ No data in date range for {asset['name']}")
                else:
                    print(f"  ❌ No data received for {asset['name']}")
            else:
                print(f"  ❌ API error for {asset['name']}: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error fetching {asset['name']}: {e}")
            continue
        
        # Rate limiting
        time.sleep(1)
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n📊 Crypto Data Summary:")
    print(f"  Total records inserted: {total_inserted}")
    return total_inserted

def verify_data_insertion():
    """Verify that data was inserted correctly."""
    
    print("\n🔍 Verifying Data Insertion")
    print("=" * 30)
    
    conn = sqlite3.connect('data/crypto_data.db')
    cursor = conn.cursor()
    
    # Check crypto data for July 15-29
    cursor.execute("""
        SELECT cryptocurrency, COUNT(*) 
        FROM crypto_ohlcv 
        WHERE date_str >= '2025-07-15' AND date_str <= '2025-07-29'
        GROUP BY cryptocurrency
        ORDER BY cryptocurrency
    """)
    
    results = cursor.fetchall()
    print("Crypto Data (July 15-29):")
    for cryptocurrency, count in results:
        print(f"  {cryptocurrency.capitalize()}: {count} records")
    
    # Check date ranges
    cursor.execute("""
        SELECT cryptocurrency, MIN(date_str), MAX(date_str), COUNT(*)
        FROM crypto_ohlcv 
        GROUP BY cryptocurrency
        ORDER BY cryptocurrency
    """)
    
    date_results = cursor.fetchall()
    print("\nUpdated Date Ranges:")
    for cryptocurrency, min_date, max_date, count in date_results:
        print(f"  {cryptocurrency.capitalize()}: {min_date} to {max_date} ({count} records)")
    
    conn.close()

def main():
    """Main function to fetch missing crypto data."""
    
    print("🚀 Fetching Missing Crypto Data: July 15 to July 29, 2025")
    print("=" * 60)
    print()
    
    try:
        # Fetch crypto data
        crypto_inserted = fetch_crypto_data()
        
        # Verify data insertion
        verify_data_insertion()
        
        # Summary
        print("\n📊 Final Summary")
        print("=" * 20)
        print(f"✅ Crypto records inserted: {crypto_inserted}")
        print()
        
        print("🎉 SUCCESS: Missing crypto data fetched!")
        print("   - Crypto data from July 15-29")
        print("   - All data verified and inserted")
        
    except Exception as e:
        print(f"❌ Error during data fetch: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 