#!/usr/bin/env python3
"""
Simple script to fetch historical data for new strategy tokens back to 2024.
Uses the working approach from fetch_and_import_data.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import time
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from data.sqlite_helper import CryptoDatabase

# New tokens to fetch
NEW_TOKENS = [
    'hype',
    'dogecoin', 
    'chainlink',
    'sui',
    'uniswap'
]

# Date range: January 1, 2024 to now
START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime.now(timezone.utc)

def main():
    print(f"🚀 Fetching historical data for new strategy tokens")
    print(f"📅 Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"🎯 Tokens: {', '.join(NEW_TOKENS)}")
    
    # Initialize clients
    db = CryptoDatabase()
    cg = CoinGeckoClient()
    
    # Convert dates to Unix timestamps
    start_ts = int(START_DATE.timestamp())
    end_ts = int(END_DATE.timestamp())
    
    print(f"⏰ Timestamps: {start_ts} to {end_ts}")
    
    # Fetch data for each token
    for token in NEW_TOKENS:
        print(f"\n{'='*50}")
        print(f"Processing {token.upper()}")
        print(f"{'='*50}")
        
        try:
            print(f"📊 Fetching CoinGecko data for {token}...")
            
            # Fetch OHLCV data
            ohlcv = cg.get_market_chart_range_data(token, start_ts, end_ts)
            
            if not ohlcv or 'prices' not in ohlcv:
                print(f"⚠️ No data returned for {token}")
                continue
            
            prices = ohlcv.get('prices', [])
            volumes = {v[0]: v[1] for v in ohlcv.get('total_volumes', [])}
            
            print(f"✅ Fetched {len(prices)} price points for {token}")
            
            # Process data into daily OHLCV format
            ohlcv_daily = {}
            for p in prices:
                ts = int(p[0] // 1000)  # ms to s
                dt = datetime.utcfromtimestamp(ts).replace(hour=0, minute=0, second=0, microsecond=0)
                date_str = dt.strftime('%Y-%m-%d')
                
                # Only keep the first price for each day (should be daily already)
                if date_str not in ohlcv_daily:
                    close = float(p[1])
                    ohlcv_daily[date_str] = {
                        'cryptocurrency': token,
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
                print(f"💾 Inserted {inserted} OHLCV records for {token}")
            else:
                print(f"⚠️ No daily data to insert for {token}")
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to process {token}: {e}")
            continue
    
    print(f"\n🎉 Historical data fetch completed!")
    print(f"📊 Processed {len(NEW_TOKENS)} tokens")

if __name__ == "__main__":
    main()
