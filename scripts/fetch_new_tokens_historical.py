#!/usr/bin/env python3
"""
Fetch Historical Data for New Strategy Tokens

This script fetches historical data for the newly added strategy tokens:
- hype (HYPE)
- dogecoin (DOGE) 
- chainlink (LINK)
- sui (SUI)
- uniswap (UNI)

Data is fetched back to January 1, 2024 to ensure sufficient historical data
for strategy analysis and backtesting.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from api.binance_client import BinanceClient
from api.bybit_client import BybitClient
from data.sqlite_helper import CryptoDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/new_tokens_historical_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# New tokens to fetch
NEW_TOKENS = [
    'hype',
    'dogecoin', 
    'chainlink',
    'sui',
    'uniswap'
]

# Start date for historical data
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime.now()

def setup_clients():
    """Initialize API clients."""
    try:
        coingecko = CoinGeckoClient()
        binance = BinanceClient()
        bybit = BybitClient()
        db = CryptoDatabase()
        
        logger.info("✅ API clients initialized successfully")
        return coingecko, binance, bybit, db
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize clients: {e}")
        raise

def fetch_coingecko_historical_data(coingecko: CoinGeckoClient, token: str, start_date: datetime, end_date: datetime):
    """Fetch historical data from CoinGecko."""
    try:
        logger.info(f"📊 Fetching CoinGecko data for {token} from {start_date.date()} to {end_date.date()}")
        
        # Convert dates to Unix timestamps
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        
        # Fetch daily data using the correct method name
        data = coingecko.get_market_chart_range_data(
            coin_id=token,
            from_timestamp=start_ts,
            to_timestamp=end_ts
        )
        
        if data and 'prices' in data:
            logger.info(f"✅ Fetched {len(data['prices'])} price points for {token}")
            return data
        else:
            logger.warning(f"⚠️ No data returned for {token}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to fetch CoinGecko data for {token}: {e}")
        return None

def fetch_exchange_historical_data(binance: BinanceClient, bybit: BybitClient, token: str, start_date: datetime, end_date: datetime):
    """Fetch historical data from exchanges."""
    try:
        logger.info(f"🏪 Fetching exchange data for {token}")
        
        # Get symbol mappings
        symbol_mappings = {
            'hype': {'binance': 'HYPEUSDT', 'bybit': 'HYPEUSDT'},
            'dogecoin': {'binance': 'DOGEUSDT', 'bybit': 'DOGEUSDT'},
            'chainlink': {'binance': 'LINKUSDT', 'bybit': 'LINKUSDT'},
            'sui': {'binance': 'SUIUSDT', 'bybit': 'SUIUSDT'},
            'uniswap': {'binance': 'UNIUSDT', 'bybit': 'UNIUSDT'}
        }
        
        exchange_data = {}
        
        # Fetch from Binance
        try:
            binance_symbol = symbol_mappings[token]['binance']
            # Format dates as strings for Binance API
            start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_date.strftime('%Y-%m-%d %H:%M:%S')
            
            binance_data = binance.get_historical_klines(
                symbol=binance_symbol,
                interval='1d',
                start_time=start_str,
                end_time=end_str
            )
            if binance_data:
                exchange_data['binance'] = binance_data
                logger.info(f"✅ Fetched {len(binance_data)} Binance records for {token}")
        except Exception as e:
            logger.warning(f"⚠️ Binance fetch failed for {token}: {e}")
        
        # Note: Bybit client doesn't have get_historical_klines method
        # We'll skip Bybit for now and focus on CoinGecko and Binance
        
        return exchange_data
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch exchange data for {token}: {e}")
        return {}

def store_data_in_database(db: CryptoDatabase, token: str, coingecko_data: Dict, exchange_data: Dict):
    """Store fetched data in the database."""
    try:
        logger.info(f"💾 Storing data for {token} in database")
        
        # Store CoinGecko data
        if coingecko_data and 'prices' in coingecko_data:
            for price_point in coingecko_data['prices']:
                timestamp, price = price_point
                date = datetime.fromtimestamp(timestamp / 1000)
                
                # Store in database (you may need to adjust this based on your schema)
                db.store_crypto_data(
                    cryptocurrency=token,
                    timestamp=date,
                    price=price,
                    source='coingecko'
                )
        
        # Store exchange data
        for exchange, data in exchange_data.items():
            for candle in data:
                # Parse OHLCV data (adjust based on your exchange data format)
                timestamp, open_price, high, low, close, volume = candle[:6]
                date = datetime.fromtimestamp(timestamp / 1000)
                
                db.store_crypto_data(
                    cryptocurrency=token,
                    timestamp=date,
                    price=close,
                    volume=volume,
                    source=exchange
                )
        
        logger.info(f"✅ Successfully stored data for {token}")
        
    except Exception as e:
        logger.error(f"❌ Failed to store data for {token}: {e}")

def main():
    """Main execution function."""
    logger.info("🚀 Starting historical data fetch for new strategy tokens")
    logger.info(f"📅 Date range: {START_DATE.date()} to {END_DATE.date()}")
    logger.info(f"🎯 Tokens: {', '.join(NEW_TOKENS)}")
    
    try:
        # Setup clients
        coingecko, binance, bybit, db = setup_clients()
        
        # Fetch data for each token
        for token in NEW_TOKENS:
            logger.info(f"\n{'='*50}")
            logger.info(f"Processing {token.upper()}")
            logger.info(f"{'='*50}")
            
            try:
                # Fetch from CoinGecko
                coingecko_data = fetch_coingecko_historical_data(
                    coingecko, token, START_DATE, END_DATE
                )
                
                # Fetch from exchanges
                exchange_data = fetch_exchange_historical_data(
                    binance, bybit, token, START_DATE, END_DATE
                )
                
                # Store in database
                store_data_in_database(db, token, coingecko_data, exchange_data)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to process {token}: {e}")
                continue
        
        logger.info("\n🎉 Historical data fetch completed!")
        logger.info(f"📊 Processed {len(NEW_TOKENS)} tokens")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        raise

if __name__ == "__main__":
    main()
