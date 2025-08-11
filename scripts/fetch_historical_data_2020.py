#!/usr/bin/env python3
"""
Historical Data Fetch and Analytics Update Script

This script fetches all crypto and macro indicator data from January 1, 2020 to present,
and then updates all corresponding analytics.
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
from api.fred_client import FREDClient
from data.sqlite_helper import CryptoDatabase
from data.realtime_storage import RealtimeStorage
from data.realtime_models import OrderBookLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_data_fetch.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIG ---
# Load monitored cryptos from config file
with open(os.path.join(os.path.dirname(__file__), '../config/monitored_cryptos.json')) as f:
    CRYPTO_CONFIG = json.load(f)["cryptocurrencies"]
ASSETS = [c["coingecko_id"] for c in CRYPTO_CONFIG]
BINANCE_SYMBOLS = [c["symbols"]["binance"] for c in CRYPTO_CONFIG if "binance" in c["symbols"]]
BYBIT_SYMBOLS = [c["symbols"]["bybit"] for c in CRYPTO_CONFIG if "bybit" in c["symbols"]]
EXCHANGES = ['binance', 'bybit']

# Load macro indicators from config file
with open(os.path.join(os.path.dirname(__file__), '../config/monitored_macro_indicators.json')) as f:
    MACRO_CONFIG = json.load(f)["macro_indicators"]
MACRO_INDICATORS = [m["fred_series_id"] for m in MACRO_CONFIG]

DB_PATH = 'data/crypto_data.db'
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime.now()

# API Keys
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
if not COINGECKO_API_KEY:
    logger.warning('COINGECKO_API_KEY not set in .env file. CoinGecko API calls may fail or be rate-limited.')

def get_date_range_unix():
    """Get Unix timestamps for the date range"""
    start_ts = int(START_DATE.replace(tzinfo=timezone.utc).timestamp())
    end_ts = int(END_DATE.replace(tzinfo=timezone.utc).timestamp())
    return start_ts, end_ts

def fetch_crypto_ohlcv_data():
    """Fetch historical OHLCV data for all cryptocurrencies"""
    logger.info("=" * 80)
    logger.info("FETCHING CRYPTO OHLCV DATA")
    logger.info("=" * 80)
    
    db = CryptoDatabase(DB_PATH)
    cg = CoinGeckoClient(api_key=COINGECKO_API_KEY)
    start_ts, end_ts = get_date_range_unix()
    
    total_inserted = 0
    
    for asset in ASSETS:
        try:
            logger.info(f"Fetching OHLCV data for {asset} from {START_DATE.date()} to {END_DATE.date()}")
            
            # CoinGecko API has rate limits, so we'll fetch in chunks
            chunk_size = 90  # days per chunk
            current_start = start_ts
            asset_inserted = 0
            
            while current_start < end_ts:
                current_end = min(current_start + (chunk_size * 24 * 3600), end_ts)
                
                logger.info(f"  Fetching chunk: {datetime.fromtimestamp(current_start)} to {datetime.fromtimestamp(current_end)}")
                
                ohlcv = cg.get_market_chart_range_data(asset, current_start, current_end)
                prices = ohlcv.get('prices', [])
                volumes = {v[0]: v[1] for v in ohlcv.get('total_volumes', [])}
                
                ohlcv_daily = {}
                for p in prices:
                    ts = int(p[0] // 1000)  # ms to s
                    dt = datetime.utcfromtimestamp(ts).replace(hour=0, minute=0, second=0, microsecond=0)
                    date_str = dt.strftime('%Y-%m-%d')
                    
                    # Only keep the first price for each day
                    if date_str not in ohlcv_daily:
                        close = float(p[1])
                        ohlcv_daily[date_str] = {
                            'cryptocurrency': asset,
                            'timestamp': int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000),
                            'date_str': date_str,
                            'open': close,
                            'high': close,
                            'low': close,
                            'close': close,
                            'volume': float(volumes.get(p[0], 0.0))
                        }
                
                if ohlcv_daily:
                    inserted = db.insert_crypto_data(list(ohlcv_daily.values()))
                    asset_inserted += inserted
                    logger.info(f"    Inserted {inserted} records for {asset}")
                
                current_start = current_end
                time.sleep(1)  # Rate limiting
            
            total_inserted += asset_inserted
            logger.info(f"✅ Completed {asset}: {asset_inserted} total records")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch/insert OHLCV for {asset}: {e}")
    
    logger.info(f"CRYPTO OHLCV COMPLETE: {total_inserted} total records inserted")
    return total_inserted

def fetch_macro_indicator_data():
    """Fetch historical macro indicator data"""
    logger.info("=" * 80)
    logger.info("FETCHING MACRO INDICATOR DATA")
    logger.info("=" * 80)
    
    db = CryptoDatabase(DB_PATH)
    fred = FREDClient()
    
    total_inserted = 0
    
    for indicator in MACRO_INDICATORS:
        try:
            logger.info(f"Fetching macro data for {indicator} from {START_DATE.date()} to {END_DATE.date()}")
            
            # FRED API can handle longer date ranges, but let's be conservative
            chunk_size = 365  # days per chunk
            current_start = START_DATE
            indicator_inserted = 0
            
            while current_start < END_DATE:
                current_end = min(current_start + timedelta(days=chunk_size), END_DATE)
                
                logger.info(f"  Fetching chunk: {current_start.date()} to {current_end.date()}")
                
                macro_data = fred.get_series_data(
                    indicator, 
                    current_start.strftime('%Y-%m-%d'), 
                    current_end.strftime('%Y-%m-%d')
                )
                
                # Add 'indicator' field to each record
                for record in macro_data:
                    record['indicator'] = indicator
                
                if macro_data:
                    inserted = db.insert_macro_data(macro_data)
                    indicator_inserted += inserted
                    logger.info(f"    Inserted {inserted} records for {indicator}")
                
                current_start = current_end
                time.sleep(0.5)  # Rate limiting
            
            total_inserted += indicator_inserted
            logger.info(f"✅ Completed {indicator}: {indicator_inserted} total records")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch/insert macro for {indicator}: {e}")
    
    logger.info(f"MACRO INDICATORS COMPLETE: {total_inserted} total records inserted")
    return total_inserted

def update_analytics():
    """Update all analytics after data fetch"""
    logger.info("=" * 80)
    logger.info("UPDATING ANALYTICS")
    logger.info("=" * 80)
    
    try:
        # Import analytics services
        from services.macro_analytics_service import MacroAnalyticsService
        from correlation_analysis.core.correlation_engine import CorrelationEngine
        from correlation_analysis.data.data_fetcher import DataFetcher
        
        # Update macro analytics
        logger.info("Updating macro analytics...")
        macro_service = MacroAnalyticsService()
        supported_indicators = macro_service.get_supported_indicators()
        timeframes = ['1d', '1w', '1m']
        
        macro_analytics_count = 0
        for indicator in supported_indicators:
            try:
                result = macro_service.analyze_indicator(indicator=indicator, timeframes=timeframes)
                if result and 'metrics' in result:
                    macro_analytics_count += len(result['metrics'])
                    logger.info(f"  ✅ {indicator}: {len(result['metrics'])} analytics updated")
            except Exception as e:
                logger.error(f"  ❌ {indicator}: {e}")
        
        logger.info(f"Macro analytics complete: {macro_analytics_count} analytics updated")
        
        # Update correlation analysis
        logger.info("Updating correlation analysis...")
        data_fetcher = DataFetcher()
        correlation_engine = CorrelationEngine()
        
        # Default pairs for correlation
        crypto_symbols = ['bitcoin', 'ethereum', 'solana']
        macro_indicators = ['VIXCLS', 'DGS10', 'DTWEXBGS']
        
        correlation_count = 0
        for crypto in crypto_symbols:
            for macro in macro_indicators:
                try:
                    data = data_fetcher.get_crypto_data_for_correlation(
                        primary=crypto, secondary=macro, days=365
                    )
                    if not data.empty:
                        corr = correlation_engine.calculate_correlation(
                            data=data, asset1=crypto, asset2=macro, window_days=30
                        )
                        correlation_count += 1
                        logger.info(f"  ✅ {crypto}-{macro}: correlation calculated")
                except Exception as e:
                    logger.error(f"  ❌ {crypto}-{macro}: {e}")
        
        logger.info(f"Correlation analysis complete: {correlation_count} correlations updated")
        
        return macro_analytics_count + correlation_count
        
    except Exception as e:
        logger.error(f"Analytics update failed: {e}")
        return 0

def main():
    """Main execution function"""
    logger.info("=" * 80)
    logger.info("HISTORICAL DATA FETCH AND ANALYTICS UPDATE")
    logger.info("=" * 80)
    logger.info(f"Start Date: {START_DATE.date()}")
    logger.info(f"End Date: {END_DATE.date()}")
    logger.info(f"Crypto Assets: {len(ASSETS)}")
    logger.info(f"Macro Indicators: {len(MACRO_INDICATORS)}")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    try:
        # Step 1: Fetch historical data
        crypto_records = fetch_crypto_ohlcv_data()
        macro_records = fetch_macro_indicator_data()
        
        # Step 2: Update analytics
        analytics_count = update_analytics()
        
        # Calculate total time
        total_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("HISTORICAL DATA FETCH COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Execution Time: {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
        logger.info(f"Crypto Records: {crypto_records}")
        logger.info(f"Macro Records: {macro_records}")
        logger.info(f"Analytics Updated: {analytics_count}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise

if __name__ == "__main__":
    main()
