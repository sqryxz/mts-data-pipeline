#!/usr/bin/env python3
"""
Fetch Historical Data for ENA (Ethena)
This script fetches historical price data for ENA from CoinGecko API.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from data.sqlite_helper import CryptoDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ena_historical_data_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_ena_historical_data():
    """Fetch historical data for ENA from CoinGecko."""
    
    try:
        # Initialize clients
        coingecko_client = CoinGeckoClient()
        db = CryptoDatabase('data/crypto_data.db')
        
        logger.info("Starting ENA historical data fetch")
        
        # ENA asset configuration
        ena_config = {
            'coingecko_id': 'ethena',
            'symbols': {
                'binance': 'ENAUSDT',
                'bybit': 'ENAUSDT'
            }
        }
        
        # Get current timestamp
        end_timestamp = int(datetime.now().timestamp())
        
        # Start from January 1, 2024 (ENA was launched in 2024)
        start_timestamp = int(datetime(2024, 1, 1).timestamp())
        
        logger.info(f"Fetching ENA data from {datetime.fromtimestamp(start_timestamp)} to {datetime.fromtimestamp(end_timestamp)}")
        
        # Fetch historical data from CoinGecko
        historical_data = coingecko_client.get_market_chart_range_data(
            coin_id='ethena',
            from_timestamp=start_timestamp,
            to_timestamp=end_timestamp
        )
        
        if not historical_data or 'prices' not in historical_data:
            logger.error("No historical data received for ENA")
            return False
        
        # Process and store data
        prices = historical_data['prices']
        market_caps = historical_data.get('market_caps', [])
        volumes = historical_data.get('total_volumes', [])
        
        logger.info(f"Received {len(prices)} price points for ENA")
        
        # Convert to OHLCV format for database insertion
        crypto_data = []
        for i, price_point in enumerate(prices):
            timestamp_ms, price = price_point
            
            # Convert timestamp to datetime
            date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            date_str = date.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get volume if available
            volume = volumes[i][1] if i < len(volumes) else 0.0
            
            # Create OHLCV record (using same price for OHLC since we only have close price)
            crypto_record = {
                'cryptocurrency': 'ethena',
                'timestamp': int(timestamp_ms),
                'date_str': date_str,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': volume
            }
            crypto_data.append(crypto_record)
        
        # Insert into database
        inserted_count = db.insert_crypto_data(crypto_data)
        
        logger.info(f"Successfully inserted {inserted_count} ENA price records")
        
        # Verify data in database
        ena_data = db.get_crypto_data('ethena', days=7)
        if not ena_data.empty:
            logger.info(f"Sample ENA data from database:")
            for _, record in ena_data.head(5).iterrows():
                logger.info(f"  {record['date_str']}: ${record['close']:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error fetching ENA historical data: {e}")
        return False

def main():
    """Main function to fetch ENA historical data."""
    print("🚀 ENA Historical Data Fetch")
    print("=" * 50)
    
    success = fetch_ena_historical_data()
    
    if success:
        print("✅ ENA historical data fetch completed successfully")
        print("\nENA is now configured for:")
        print("  📊 Historical data collection")
        print("  🔗 Correlation analysis")
        print("  ⚡ High-frequency tracking (15-minute intervals)")
        print("  📈 Real-time monitoring")
    else:
        print("❌ ENA historical data fetch failed")
        print("Please check the logs for details")

if __name__ == "__main__":
    main()
