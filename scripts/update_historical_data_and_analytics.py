#!/usr/bin/env python3
"""
Historical Data and Analytics Update Script

This script fetches all crypto and macro indicator data from a specified start date
and updates all corresponding analytics. Can be run periodically to maintain
historical data completeness.
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from api.fred_client import FREDClient
from data.sqlite_helper import CryptoDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_data_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_configs():
    """Load configuration files"""
    # Load monitored cryptos
    with open(os.path.join(os.path.dirname(__file__), '../config/monitored_cryptos.json')) as f:
        crypto_config = json.load(f)["cryptocurrencies"]
    assets = [c["coingecko_id"] for c in crypto_config]
    
    # Load macro indicators
    with open(os.path.join(os.path.dirname(__file__), '../config/monitored_macro_indicators.json')) as f:
        macro_config = json.load(f)["macro_indicators"]
    macro_indicators = [m["fred_series_id"] for m in macro_config]
    
    return assets, macro_indicators

def fetch_crypto_data(start_date: datetime, end_date: datetime, assets: List[str]):
    """Fetch historical crypto OHLCV data"""
    logger.info("=" * 80)
    logger.info("FETCHING CRYPTO OHLCV DATA")
    logger.info("=" * 80)
    
    db = CryptoDatabase('data/crypto_data.db')
    cg = CoinGeckoClient(api_key=os.getenv('COINGECKO_API_KEY'))
    
    start_ts = int(start_date.replace(tzinfo=timezone.utc).timestamp())
    end_ts = int(end_date.replace(tzinfo=timezone.utc).timestamp())
    
    total_inserted = 0
    
    for asset in assets:
        try:
            logger.info(f"Fetching OHLCV data for {asset} from {start_date.date()} to {end_date.date()}")
            
            # Fetch in chunks to respect rate limits
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
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                    date_str = dt.strftime('%Y-%m-%d')
                    
                    # Only keep the first price for each day
                    if date_str not in ohlcv_daily:
                        close = float(p[1])
                        ohlcv_daily[date_str] = {
                            'cryptocurrency': asset,
                            'timestamp': int(dt.timestamp() * 1000),
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

def fetch_macro_data(start_date: datetime, end_date: datetime, macro_indicators: List[str]):
    """Fetch historical macro indicator data"""
    logger.info("=" * 80)
    logger.info("FETCHING MACRO INDICATOR DATA")
    logger.info("=" * 80)
    
    db = CryptoDatabase('data/crypto_data.db')
    fred = FREDClient()
    
    total_inserted = 0
    
    for indicator in macro_indicators:
        try:
            logger.info(f"Fetching macro data for {indicator} from {start_date.date()} to {end_date.date()}")
            
            # Fetch in chunks
            chunk_size = 365  # days per chunk
            current_start = start_date
            indicator_inserted = 0
            
            while current_start < end_date:
                current_end = min(current_start + timedelta(days=chunk_size), end_date)
                
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

def generate_analytics_report():
    """Generate comprehensive analytics report"""
    logger.info("=" * 80)
    logger.info("GENERATING ANALYTICS REPORT")
    logger.info("=" * 80)
    
    import pandas as pd
    import numpy as np
    
    db = CryptoDatabase('data/crypto_data.db')
    
    # Get database statistics
    stats = db.get_health_status()
    
    # Calculate crypto performance metrics
    crypto_symbols = ['bitcoin', 'ethereum', 'solana', 'ripple', 'tether']
    crypto_metrics = {}
    
    for crypto in crypto_symbols:
        try:
            data = db.get_crypto_data(crypto, days=365*5)  # 5 years
            
            if not data.empty and 'close' in data.columns:
                prices = data['close'].dropna()
                
                if len(prices) > 1:
                    returns = prices.pct_change().dropna()
                    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
                    volatility = returns.std() * (252 ** 0.5)
                    sharpe_ratio = (returns.mean() * 252) / volatility if volatility > 0 else 0
                    
                    # Calculate max drawdown
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    max_drawdown = drawdown.min()
                    
                    # Additional metrics
                    avg_annual_return = returns.mean() * 252
                    var_95 = np.percentile(returns, 5)
                    skewness = returns.skew()
                    kurtosis = returns.kurtosis()
                    
                    crypto_metrics[crypto] = {
                        'total_return': total_return,
                        'volatility': volatility,
                        'sharpe_ratio': sharpe_ratio,
                        'max_drawdown': max_drawdown,
                        'avg_annual_return': avg_annual_return,
                        'var_95': var_95,
                        'skewness': skewness,
                        'kurtosis': kurtosis,
                        'data_points': len(prices)
                    }
                    
                    logger.info(f"✅ {crypto.upper()}: Return: {total_return:.2%}, Vol: {volatility:.2%}, Sharpe: {sharpe_ratio:.2f}")
                    
        except Exception as e:
            logger.error(f"Error calculating metrics for {crypto}: {e}")
    
    # Calculate macro indicator statistics
    macro_indicators = ['VIXCLS', 'DGS10', 'DTWEXBGS', 'DFF', 'DEXUSEU', 'DEXCHUS', 'BAMLH0A0HYM2', 'RRPONTSYD', 'SOFR']
    macro_stats = {}
    
    for indicator in macro_indicators:
        try:
            query = f"""
            SELECT date, value 
            FROM macro_indicators 
            WHERE indicator = ? 
            ORDER BY date ASC
            """
            
            df = db.query_to_dataframe(query, (indicator,))
            
            if not df.empty:
                values = pd.to_numeric(df['value'], errors='coerce').dropna()
                
                if len(values) > 0:
                    macro_stats[indicator] = {
                        'count': len(values),
                        'mean': values.mean(),
                        'std': values.std(),
                        'min': values.min(),
                        'max': values.max(),
                        'current': values.iloc[-1],
                        'first_date': df['date'].iloc[0],
                        'last_date': df['date'].iloc[-1]
                    }
                    
                    logger.info(f"✅ {indicator}: Count: {len(values)}, Current: {values.iloc[-1]:.4f}")
                    
        except Exception as e:
            logger.error(f"Error calculating stats for {indicator}: {e}")
    
    # Generate summary report
    report = {
        'generated_at': datetime.now().isoformat(),
        'data_range': {
            'start_date': '2020-01-01',
            'end_date': datetime.now().strftime('%Y-%m-%d')
        },
        'database_stats': stats,
        'crypto_metrics': crypto_metrics,
        'macro_stats': macro_stats,
        'summary': {
            'total_crypto_assets': len(crypto_metrics),
            'total_macro_indicators': len(macro_stats),
            'data_completeness': 'Historical data updated successfully'
        }
    }
    
    # Save report
    report_path = f'data/analytics_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Analytics report saved to: {report_path}")
    return report_path

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Update historical data and analytics')
    parser.add_argument('--start-date', type=str, default='2020-01-01', 
                       help='Start date for data fetch (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date for data fetch (YYYY-MM-DD, defaults to today)')
    parser.add_argument('--crypto-only', action='store_true',
                       help='Only fetch crypto data')
    parser.add_argument('--macro-only', action='store_true',
                       help='Only fetch macro data')
    parser.add_argument('--analytics-only', action='store_true',
                       help='Only generate analytics report')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime.now()
    
    logger.info("=" * 80)
    logger.info("HISTORICAL DATA AND ANALYTICS UPDATE")
    logger.info("=" * 80)
    logger.info(f"Start Date: {start_date.date()}")
    logger.info(f"End Date: {end_date.date()}")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    try:
        # Load configurations
        assets, macro_indicators = load_configs()
        logger.info(f"Crypto Assets: {len(assets)}")
        logger.info(f"Macro Indicators: {len(macro_indicators)}")
        
        # Fetch data
        crypto_records = 0
        macro_records = 0
        
        if not args.macro_only and not args.analytics_only:
            crypto_records = fetch_crypto_data(start_date, end_date, assets)
        
        if not args.crypto_only and not args.analytics_only:
            macro_records = fetch_macro_data(start_date, end_date, macro_indicators)
        
        # Generate analytics report
        if not args.crypto_only and not args.macro_only:
            report_path = generate_analytics_report()
        
        # Calculate total time
        total_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("UPDATE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total Execution Time: {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
        logger.info(f"Crypto Records: {crypto_records}")
        logger.info(f"Macro Records: {macro_records}")
        if not args.crypto_only and not args.macro_only:
            logger.info(f"Analytics Report: {report_path}")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise

if __name__ == "__main__":
    main()
