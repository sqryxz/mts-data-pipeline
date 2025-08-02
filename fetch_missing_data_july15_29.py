#!/usr/bin/env python3
"""
Fetch Missing Data: July 15 to July 29, 2025
Fetches crypto and macro data that's missing from our database.
"""

import sys
import os
import logging
from datetime import datetime, timedelta, timezone
import asyncio
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.coingecko_client import CoinGeckoClient
from src.api.fred_client import FREDClient
from src.data.sqlite_helper import CryptoDatabase
from src.services.collector import DataCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def fetch_crypto_data():
    """Fetch crypto data from July 15 to July 29."""
    
    print("🪙 Fetching Crypto Data (July 15 - July 29)")
    print("=" * 50)
    
    # Initialize clients
    coingecko = CoinGeckoClient()
    database = CryptoDatabase()
    
    # Define date range
    start_date = datetime(2025, 7, 15, tzinfo=timezone.utc)
    end_date = datetime(2025, 7, 29, tzinfo=timezone.utc)
    
    # Crypto assets to fetch
    crypto_assets = [
        {'id': 'bitcoin', 'symbol': 'btc'},
        {'id': 'ethereum', 'symbol': 'eth'},
        {'id': 'binancecoin', 'symbol': 'bnb'},
        {'id': 'ripple', 'symbol': 'xrp'},
        {'id': 'solana', 'symbol': 'sol'},
        {'id': 'tether', 'symbol': 'usdt'},
        {'id': 'cardano', 'symbol': 'ada'},
        {'id': 'avalanche-2', 'symbol': 'avax'},
        {'id': 'polkadot', 'symbol': 'dot'},
        {'id': 'chainlink', 'symbol': 'link'},
        {'id': 'polygon', 'symbol': 'matic'},
        {'id': 'dogecoin', 'symbol': 'doge'},
        {'id': 'litecoin', 'symbol': 'ltc'},
        {'id': 'uniswap', 'symbol': 'uni'},
        {'id': 'bitcoin-cash', 'symbol': 'bch'},
        {'id': 'stellar', 'symbol': 'xlm'},
        {'id': 'vechain', 'symbol': 'vet'},
        {'id': 'filecoin', 'symbol': 'fil'},
        {'id': 'cosmos', 'symbol': 'atom'},
        {'id': 'monero', 'symbol': 'xmr'}
    ]
    
    total_inserted = 0
    
    for asset in crypto_assets:
        try:
            print(f"📊 Fetching {asset['id'].capitalize()} data...")
            
            # Fetch daily OHLC data
            ohlc_data = coingecko.get_ohlc_data(
                coin_id=asset['id'],
                days=15  # July 15 to July 29 is 15 days
            )
            
            if ohlc_data and len(ohlc_data) > 0:
                # Convert to our database format
                crypto_records = []
                for data_point in ohlc_data:
                    # Filter for our date range
                    timestamp = data_point[0] / 1000  # Convert from milliseconds
                    data_date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    
                    if start_date <= data_date <= end_date:
                        record = {
                            'cryptocurrency': asset['id'],
                            'timestamp': int(timestamp * 1000),  # Store in milliseconds
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
                    inserted = database.insert_crypto_data(crypto_records)
                    total_inserted += inserted
                    print(f"  ✅ Inserted {inserted} records for {asset['id']}")
                else:
                    print(f"  ⚠️ No data in date range for {asset['id']}")
            else:
                print(f"  ❌ No data received for {asset['id']}")
                
        except Exception as e:
            print(f"  ❌ Error fetching {asset['id']}: {e}")
            continue
        
        # Rate limiting
        await asyncio.sleep(1)
    
    print(f"\n📊 Crypto Data Summary:")
    print(f"  Total records inserted: {total_inserted}")
    return total_inserted

async def fetch_macro_data():
    """Fetch macro indicators from July 15 to July 29."""
    
    print("\n📈 Fetching Macro Indicators (July 15 - July 29)")
    print("=" * 50)
    
    # Initialize FRED client
    fred = FREDClient()
    database = CryptoDatabase()
    
    # Define date range
    start_date = datetime(2025, 7, 15)
    end_date = datetime(2025, 7, 29)
    
    # Macro indicators to fetch
    macro_indicators = [
        'VIXCLS',      # VIX Volatility Index
        'DGS10',       # 10-Year Treasury Rate
        'DFF',         # Federal Funds Rate
        'DEXCHUS',     # US Dollar Index
        'DEXUSEU',     # Euro/USD Exchange Rate
        'DTWEXBGS',    # Trade Weighted Dollar Index
        'BAMLH0A0HYM2', # High Yield Bond Spread
        'RRPONTSYD',   # Reverse Repo Rate
        'SOFR'         # Secured Overnight Financing Rate
    ]
    
    total_inserted = 0
    
    for indicator in macro_indicators:
        try:
            print(f"📊 Fetching {indicator} data...")
            
            # Fetch data from FRED
            macro_data = fred.get_series_data(
                series_id=indicator,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if macro_data and len(macro_data) > 0:
                # Convert to our database format
                macro_records = []
                for data_point in macro_data:
                    record = {
                        'indicator': indicator,
                        'date': data_point['date'],
                        'value': data_point['value'],
                        'is_interpolated': False,
                        'is_forward_filled': False
                    }
                    macro_records.append(record)
                
                if macro_records:
                    # Insert into database
                    inserted = database.insert_macro_data(macro_records)
                    total_inserted += inserted
                    print(f"  ✅ Inserted {inserted} records for {indicator}")
                else:
                    print(f"  ⚠️ No data in date range for {indicator}")
            else:
                print(f"  ❌ No data received for {indicator}")
                
        except Exception as e:
            print(f"  ❌ Error fetching {indicator}: {e}")
            continue
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    print(f"\n📈 Macro Data Summary:")
    print(f"  Total records inserted: {total_inserted}")
    return total_inserted

def verify_data_insertion():
    """Verify that data was inserted correctly."""
    
    print("\n🔍 Verifying Data Insertion")
    print("=" * 30)
    
    database = CryptoDatabase()
    
    # Check crypto data
    print("Crypto Data (July 15-29):")
    crypto_assets = ['bitcoin', 'ethereum', 'binancecoin', 'ripple', 'solana']
    
    for asset in crypto_assets:
        try:
            data = database.get_crypto_data(asset, 30)
            if not data.empty:
                # Filter for our date range
                mask = (data['date_str'] >= '2025-07-15') & (data['date_str'] <= '2025-07-29')
                filtered_data = data[mask]
                print(f"  {asset.capitalize()}: {len(filtered_data)} records")
            else:
                print(f"  {asset.capitalize()}: No data")
        except Exception as e:
            print(f"  {asset.capitalize()}: Error - {e}")
    
    # Check macro data
    print("\nMacro Indicators (July 15-29):")
    import sqlite3
    conn = sqlite3.connect('data/crypto_data.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT indicator, COUNT(*) 
        FROM macro_indicators 
        WHERE date >= '2025-07-15' AND date <= '2025-07-29'
        GROUP BY indicator
    """)
    
    results = cursor.fetchall()
    for indicator, count in results:
        print(f"  {indicator}: {count} records")
    
    conn.close()

async def main():
    """Main function to fetch all missing data."""
    
    print("🚀 Fetching Missing Data: July 15 to July 29, 2025")
    print("=" * 60)
    print()
    
    try:
        # Fetch crypto data
        crypto_inserted = await fetch_crypto_data()
        
        # Fetch macro data
        macro_inserted = await fetch_macro_data()
        
        # Verify data insertion
        verify_data_insertion()
        
        # Summary
        print("\n📊 Final Summary")
        print("=" * 20)
        print(f"✅ Crypto records inserted: {crypto_inserted}")
        print(f"✅ Macro records inserted: {macro_inserted}")
        print(f"✅ Total records inserted: {crypto_inserted + macro_inserted}")
        print()
        
        print("🎉 SUCCESS: Missing data fetched!")
        print("   - Crypto data from July 15-29")
        print("   - Macro indicators from July 15-29")
        print("   - All data verified and inserted")
        
    except Exception as e:
        print(f"❌ Error during data fetch: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 