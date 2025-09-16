#!/usr/bin/env python3
"""
Simplified script to fetch missing crypto data since 1-1-2024 using CoinGecko Pro API.
This script will:
1. Check which cryptos don't have data since 1-1-2024
2. Fetch the missing data from CoinGecko
3. Store it in the database
"""

import os
import sys
import time
import json
import sqlite3
import requests
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Load environment variables
load_env()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fetch_missing_2024_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
START_DATE = datetime(2024, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime.now(timezone.utc)
DB_PATH = 'data/crypto_data.db'

class SimpleCoinGeckoClient:
    """Simple CoinGecko API client for cryptocurrency data."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://pro-api.coingecko.com/api/v3'
        self.headers = {'x-cg-pro-api-key': api_key}
        self.timeout = 30
    
    def get_market_chart_range_data(self, coin_id: str, from_timestamp: int, to_timestamp: int) -> Optional[Dict]:
        """Fetch market chart data for a specific range."""
        try:
            endpoint = f"/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': from_timestamp,
                'to': to_timestamp
            }
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning(f"Rate limit hit for {coin_id}, waiting 60 seconds...")
                time.sleep(60)
                return self.get_market_chart_range_data(coin_id, from_timestamp, to_timestamp)
            else:
                logger.error(f"API error for {coin_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch data for {coin_id}: {e}")
            return None

class SimpleCryptoDatabase:
    """Simple database helper for crypto data operations."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the crypto_ohlcv table exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS crypto_ohlcv (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cryptocurrency TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        date_str TEXT NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(cryptocurrency, timestamp)
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_cryptocurrency ON crypto_ohlcv(cryptocurrency)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_timestamp ON crypto_ohlcv(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_crypto_ohlcv_date_str ON crypto_ohlcv(date_str)")
                
                conn.commit()
                logger.debug("Database table and indexes created/verified")
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
    
    def insert_crypto_data(self, crypto_data: List[Dict]) -> int:
        """Insert crypto data into the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                inserted = 0
                for record in crypto_data:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO crypto_ohlcv 
                            (cryptocurrency, timestamp, date_str, open, high, low, close, volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
                        if cursor.rowcount > 0:
                            inserted += 1
                    except sqlite3.IntegrityError:
                        # Duplicate entry, skip
                        continue
                
                conn.commit()
                return inserted
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return 0
    
    def check_missing_data_since_2024(self, cryptos: List[Dict]) -> List[Dict]:
        """Check which cryptos don't have data since 1-1-2024."""
        logger.info("Checking which cryptos need data since 1-1-2024...")
        
        missing_cryptos = []
        start_timestamp = int(START_DATE.timestamp()) * 1000  # Convert to milliseconds
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for crypto in cryptos:
                    coingecko_id = crypto['coingecko_id']
                    
                    try:
                        # Check if we have any data since 1-1-2024
                        query = """
                            SELECT COUNT(*) as count, 
                                   MIN(timestamp) as earliest_ts,
                                   MAX(timestamp) as latest_ts
                            FROM crypto_ohlcv 
                            WHERE cryptocurrency = ? AND timestamp >= ?
                        """
                        
                        cursor = conn.execute(query, (coingecko_id, start_timestamp))
                        result = cursor.fetchone()
                        
                        if result:
                            count, earliest_ts, latest_ts = result
                            
                            if count == 0:
                                logger.info(f"❌ {coingecko_id}: No data since 1-1-2024")
                                missing_cryptos.append(crypto)
                            else:
                                earliest_date = datetime.fromtimestamp(earliest_ts / 1000).strftime('%Y-%m-%d')
                                latest_date = datetime.fromtimestamp(latest_ts / 1000).strftime('%Y-%m-%d')
                                logger.info(f"✅ {coingecko_id}: {count} records from {earliest_date} to {latest_date}")
                                
                                # Check if we have continuous data from 1-1-2024
                                if earliest_ts > start_timestamp:
                                    logger.info(f"⚠️ {coingecko_id}: Missing data from 1-1-2024 to {earliest_date}")
                                    missing_cryptos.append(crypto)
                                    
                    except Exception as e:
                        logger.error(f"Error checking data for {coingecko_id}: {e}")
                        missing_cryptos.append(crypto)
                        
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return cryptos  # Return all cryptos if we can't check
        
        logger.info(f"Found {len(missing_cryptos)} cryptos that need data fetching")
        return missing_cryptos

def process_and_store_data(
    db: SimpleCryptoDatabase, 
    crypto: Dict, 
    market_data: Dict
) -> int:
    """Process market data and store in database."""
    coingecko_id = crypto['coingecko_id']
    
    try:
        prices = market_data.get('prices', [])
        volumes = {v[0]: v[1] for v in market_data.get('total_volumes', [])}
        
        # Convert to daily OHLCV format
        ohlcv_daily = {}
        
        for price_point in prices:
            timestamp_ms, price = price_point
            
            # Convert to date string (UTC)
            ts_seconds = int(timestamp_ms // 1000)
            dt = datetime.fromtimestamp(ts_seconds, tz=timezone.utc)
            date_str = dt.strftime('%Y-%m-%d')
            
            # Only keep one record per day (use close price)
            if date_str not in ohlcv_daily:
                volume = float(volumes.get(timestamp_ms, 0.0))
                
                ohlcv_daily[date_str] = {
                    'cryptocurrency': coingecko_id,
                    'timestamp': int(dt.timestamp() * 1000),  # Convert to milliseconds
                    'date_str': date_str,
                    'open': float(price),
                    'high': float(price),
                    'low': float(price),
                    'close': float(price),
                    'volume': volume
                }
        
        if ohlcv_daily:
            # Insert into database
            records = list(ohlcv_daily.values())
            inserted = db.insert_crypto_data(records)
            logger.info(f"✅ Inserted {inserted} records for {coingecko_id}")
            return inserted
        else:
            logger.warning(f"⚠️ No valid data to insert for {coingecko_id}")
            return 0
            
    except Exception as e:
        logger.error(f"❌ Failed to process/store data for {coingecko_id}: {e}")
        return 0

def main():
    """Main execution function."""
    logger.info("🚀 Starting missing data fetch for 2024")
    logger.info(f"📅 Date range: {START_DATE.date()} to {END_DATE.date()}")
    
    try:
        # Load environment variables
        coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        if not coingecko_api_key:
            logger.error("❌ COINGECKO_API_KEY not set in environment")
            return
        
        # Initialize clients
        logger.info("Initializing clients...")
        coingecko = SimpleCoinGeckoClient(api_key=coingecko_api_key)
        db = SimpleCryptoDatabase(DB_PATH)
        
        # Load monitored cryptos
        with open('config/monitored_cryptos.json', 'r') as f:
            config = json.load(f)
            cryptos = config['cryptocurrencies']
        logger.info(f"Loaded {len(cryptos)} monitored cryptocurrencies")
        
        # Check which cryptos need data
        missing_cryptos = db.check_missing_data_since_2024(cryptos)
        
        if not missing_cryptos:
            logger.info("🎉 All cryptos have complete data since 1-1-2024!")
            return
        
        # Convert dates to Unix timestamps
        start_ts = int(START_DATE.timestamp())
        end_ts = int(END_DATE.timestamp())
        
        logger.info(f"⏰ Fetching data from {start_ts} to {end_ts}")
        
        # Fetch data for missing cryptos
        total_inserted = 0
        
        for i, crypto in enumerate(missing_cryptos):
            coingecko_id = crypto['coingecko_id']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing {coingecko_id} ({i+1}/{len(missing_cryptos)})")
            logger.info(f"{'='*60}")
            
            try:
                # Fetch data from CoinGecko
                market_data = coingecko.get_market_chart_range_data(
                    coin_id=coingecko_id,
                    from_timestamp=start_ts,
                    to_timestamp=end_ts
                )
                
                if market_data:
                    # Process and store data
                    inserted = process_and_store_data(db, crypto, market_data)
                    total_inserted += inserted
                    
                    # Rate limiting for Pro API
                    if i < len(missing_cryptos) - 1:  # Don't sleep after last crypto
                        logger.info("⏳ Rate limiting: waiting 1 second...")
                        time.sleep(1)
                else:
                    logger.warning(f"⚠️ Skipping {coingecko_id} due to fetch failure")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process {coingecko_id}: {e}")
                continue
        
        logger.info(f"\n🎉 Data fetch completed!")
        logger.info(f"📊 Total records inserted: {total_inserted}")
        logger.info(f"🎯 Processed {len(missing_cryptos)} cryptos")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        raise

if __name__ == "__main__":
    main()
