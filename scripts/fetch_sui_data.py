#!/usr/bin/env python3
"""
Fetch SUI Data Script
Dedicated script to fetch comprehensive SUI data to match other cryptocurrencies.
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import time
import json
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from data.sqlite_helper import CryptoDatabase

def get_sui_historical_data():
    """Fetch comprehensive SUI historical data from CoinGecko."""
    print("🪙 Fetching SUI Historical Data")
    print("=" * 50)
    
    # Initialize components
    coingecko_api_key = os.getenv('COINGECKO_API_KEY')
    cg = CoinGeckoClient(api_key=coingecko_api_key)
    db = CryptoDatabase('data/crypto_data.db')
    
    # Define time ranges to fetch
    time_ranges = [
        {
            'name': '2024 Data',
            'start_ts': int(datetime(2024, 1, 1).timestamp()),
            'end_ts': int(datetime(2024, 12, 31, 23, 59, 59).timestamp())
        },
        {
            'name': '2025 Data (Current)',
            'start_ts': int(datetime(2025, 1, 1).timestamp()),
            'end_ts': int(datetime.now().timestamp())
        }
    ]
    
    total_inserted = 0
    
    for time_range in time_ranges:
        print(f"\n📊 Fetching {time_range['name']}...")
        print(f"   From: {datetime.fromtimestamp(time_range['start_ts']).strftime('%Y-%m-%d')}")
        print(f"   To: {datetime.fromtimestamp(time_range['end_ts']).strftime('%Y-%m-%d')}")
        
        try:
            # Fetch market chart data
            ohlcv = cg.get_market_chart_range_data('sui', time_range['start_ts'], time_range['end_ts'])
            prices = ohlcv.get('prices', [])
            volumes = {v[0]: v[1] for v in ohlcv.get('total_volumes', [])}
            
            if not prices:
                print(f"   ⚠️ No price data received for {time_range['name']}")
                continue
            
            # Process and store data
            ohlcv_daily = {}
            for p in prices:
                ts = int(p[0] // 1000)  # ms to s
                dt = datetime.utcfromtimestamp(ts).replace(hour=0, minute=0, second=0, microsecond=0)
                date_str = dt.strftime('%Y-%m-%d')
                
                # Only keep the first price for each day (should be daily already)
                if date_str not in ohlcv_daily:
                    close = float(p[1])
                    ohlcv_daily[date_str] = {
                        'cryptocurrency': 'sui',
                        'timestamp': int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000),
                        'date_str': date_str,
                        'open': close,
                        'high': close,
                        'low': close,
                        'close': close,
                        'volume': float(volumes.get(p[0], 0.0))
                    }
            
            # Insert into database
            if ohlcv_daily:
                inserted = db.insert_crypto_data(list(ohlcv_daily.values()))
                total_inserted += inserted
                print(f"   ✅ Inserted {inserted} records for {time_range['name']}")
                print(f"   📈 Price range: ${min(d['close'] for d in ohlcv_daily.values()):.4f} - ${max(d['close'] for d in ohlcv_daily.values()):.4f}")
            else:
                print(f"   ⚠️ No daily data to insert for {time_range['name']}")
                
        except Exception as e:
            print(f"   ❌ Error fetching {time_range['name']}: {e}")
            continue
        
        # Rate limiting
        time.sleep(2)
    
    return total_inserted

def get_sui_current_data():
    """Fetch current SUI price and market data."""
    print("\n📊 Fetching Current SUI Data")
    print("=" * 50)
    
    try:
        # Get current price
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'sui',
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }
        
        import requests
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        sui_data = data['sui']
        print(f"   💰 Current Price: ${sui_data['usd']:.4f}")
        print(f"   📈 24h Change: {sui_data.get('usd_24h_change', 'N/A'):.2f}%")
        print(f"   💎 Market Cap: ${sui_data.get('usd_market_cap', 'N/A'):,.0f}")
        print(f"   📊 24h Volume: ${sui_data.get('usd_24h_vol', 'N/A'):,.0f}")
        
        return sui_data
        
    except Exception as e:
        print(f"   ❌ Error fetching current data: {e}")
        return None

def verify_sui_data_in_database():
    """Verify SUI data is properly stored in the database."""
    print("\n🔍 Verifying SUI Data in Database")
    print("=" * 50)
    
    try:
        db = CryptoDatabase('data/crypto_data.db')
        
        # Query SUI data
        with db.db_connection.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM crypto_ohlcv WHERE cryptocurrency = 'sui'")
            total_count = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("""
                SELECT MIN(date_str), MAX(date_str), MIN(close), MAX(close)
                FROM crypto_ohlcv 
                WHERE cryptocurrency = 'sui'
            """)
            result = cursor.fetchone()
            
            if result and result[0]:
                min_date, max_date, min_price, max_price = result
                print(f"   📊 Total SUI records: {total_count}")
                print(f"   📅 Date range: {min_date} to {max_date}")
                print(f"   💰 Price range: ${min_price:.4f} - ${max_price:.4f}")
                
                # Get recent data
                cursor.execute("""
                    SELECT date_str, close, volume
                    FROM crypto_ohlcv 
                    WHERE cryptocurrency = 'sui'
                    ORDER BY date_str DESC
                    LIMIT 5
                """)
                recent_data = cursor.fetchall()
                
                print(f"   📈 Recent prices:")
                for date, price, volume in recent_data:
                    print(f"      {date}: ${price:.4f} (Vol: {volume:,.0f})")
                
                return True
            else:
                print("   ❌ No SUI data found in database")
                return False
                
    except Exception as e:
        print(f"   ❌ Error verifying database: {e}")
        return False

def main():
    """Main function to fetch comprehensive SUI data."""
    print("🚀 SUI Data Collection Script")
    print("=" * 60)
    
    # Step 1: Get current market data
    current_data = get_sui_current_data()
    
    # Step 2: Fetch historical data
    total_inserted = get_sui_historical_data()
    
    # Step 3: Verify data in database
    verification_success = verify_sui_data_in_database()
    
    # Summary
    print("\n📋 Collection Summary")
    print("=" * 60)
    print(f"✅ Historical records inserted: {total_inserted}")
    print(f"✅ Database verification: {'PASS' if verification_success else 'FAIL'}")
    
    if current_data:
        print(f"✅ Current price: ${current_data['usd']:.4f}")
    
    if total_inserted > 0 and verification_success:
        print("\n🎉 SUI data collection completed successfully!")
        print("\nNext steps:")
        print("1. Run correlation analysis:")
        print("   python3 -m src.correlation_analysis")
        print("2. Check correlation pairs:")
        print("   python3 scripts/test_sui_integration.py")
    else:
        print("\n⚠️ Some issues occurred during data collection.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
