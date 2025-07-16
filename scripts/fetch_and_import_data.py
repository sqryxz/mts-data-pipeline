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
from api.binance_client import BinanceClient
from api.bybit_client import BybitClient
from api.fred_client import FREDClient
from data.sqlite_helper import CryptoDatabase
from data.realtime_storage import RealtimeStorage
from data.realtime_models import OrderBookLevel

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
YEAR = 2025

# --- HELPERS ---
def get_year_unix_range():
    start = int(datetime(YEAR, 1, 1).timestamp())
    end = int(datetime(YEAR, 12, 31, 23, 59, 59).timestamp())
    return start, end

COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
if not COINGECKO_API_KEY:
    print('Warning: COINGECKO_API_KEY not set in .env file. CoinGecko API calls may fail or be rate-limited.')

def main():
    print(f"Fetching and importing all data types for {YEAR}...")
    db = CryptoDatabase(DB_PATH)
    rt_storage = RealtimeStorage(DB_PATH)
    cg = CoinGeckoClient(api_key=COINGECKO_API_KEY)
    binance = BinanceClient()
    bybit = BybitClient()
    fred = FREDClient()
    start_ts, end_ts = get_year_unix_range()

    # --- 1. OHLCV Data (CoinGecko) ---
    print("Fetching OHLCV data from CoinGecko...")
    for asset in ASSETS:
        try:
            print(f"Requesting CoinGecko OHLCV for asset: {asset}")
            print(f"From: {start_ts}, To: {end_ts}")
            ohlcv = cg.get_market_chart_range_data(asset, start_ts, end_ts)
            prices = ohlcv.get('prices', [])
            volumes = {v[0]: v[1] for v in ohlcv.get('total_volumes', [])}
            ohlcv_daily = {}
            for p in prices:
                ts = int(p[0] // 1000)  # ms to s
                dt = datetime.utcfromtimestamp(ts).replace(hour=0, minute=0, second=0, microsecond=0)
                date_str = dt.strftime('%Y-%m-%d')
                # Only keep the first price for each day (should be daily already)
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
            inserted = db.insert_crypto_data(list(ohlcv_daily.values()))
            print(f"Inserted {inserted} OHLCV records for {asset}")
        except Exception as e:
            print(f"Failed to fetch/insert OHLCV for {asset}: {e}")

    # --- 2. Macro Indicators (FRED) ---
    print("Fetching macro indicators from FRED...")
    for indicator in MACRO_INDICATORS:
        try:
            macro_data = fred.get_series_data(indicator, f"{YEAR}-01-01", f"{YEAR}-12-31")
            # Add 'indicator' field to each record
            for record in macro_data:
                record['indicator'] = indicator
            inserted = db.insert_macro_data(macro_data)
            print(f"Inserted {inserted} macro records for {indicator}")
        except Exception as e:
            print(f"Failed to fetch/insert macro for {indicator}: {e}")

    # --- 3. Order Book, Funding, and Spread Data (Exchanges) ---
    print(f"Fetching order book, funding, and spread data from exchanges at 00:00 UTC for each day in {YEAR}...")
    
    # Generate each day of the year
    current_date = datetime(YEAR, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(YEAR, 12, 31, tzinfo=timezone.utc)
    
    while current_date <= end_date:
        print(f"Processing {current_date.strftime('%Y-%m-%d %H:%M')} UTC...")
        ts_ms = int(current_date.timestamp() * 1000)
        
        # For each exchange and symbol, fetch order book, funding, and spread data
        for exchange in EXCHANGES:
            symbols = BINANCE_SYMBOLS if exchange == 'binance' else BYBIT_SYMBOLS
            client = binance if exchange == 'binance' else bybit
            
            for symbol in symbols:
                try:
                    # Order Book (current snapshot)
                    ob = client.get_order_book(symbol)
                    if ob and 'bids' in ob and 'asks' in ob:
                        bids = ob['bids'][:5]  # Top 5 bids
                        asks = ob['asks'][:5]  # Top 5 asks
                        
                        # Convert to order book levels and store
                        ob_levels = []
                        for level, (price, qty) in enumerate(bids):
                            ob_levels.append(OrderBookLevel(
                                exchange=exchange,
                                symbol=symbol,
                                timestamp=ts_ms,
                                side='bid',
                                level=level,
                                price=float(price),
                                quantity=float(qty)
                            ))
                        for level, (price, qty) in enumerate(asks):
                            ob_levels.append(OrderBookLevel(
                                exchange=exchange,
                                symbol=symbol,
                                timestamp=ts_ms,
                                side='ask',
                                level=level,
                                price=float(price),
                                quantity=float(qty)
                            ))
                        rt_storage.batch_store_orderbook(ob_levels, csv_backup=False)
                        
                    # Funding Rate (current, timestamped as 00:00 UTC)
                    if hasattr(client, 'get_funding_rate'):
                        fr = client.get_funding_rate(symbol)
                        if fr:
                            from data.realtime_models import FundingRate
                            funding_rate = FundingRate(
                                exchange=exchange,
                                symbol=symbol,
                                timestamp=ts_ms,
                                funding_rate=float(fr.get('lastFundingRate', fr.get('fundingRate', 0.0))),
                                predicted_rate=float(fr.get('predictedFundingRate', 0.0)),
                                funding_time=ts_ms
                            )
                            rt_storage.store_funding_rate(funding_rate, csv_backup=False)
                    # Bid-Ask Spread (from order book)
                    if ob and bids and asks:
                        from data.realtime_models import BidAskSpread
                        bid_price = float(bids[0][0]) if bids else 0.0
                        ask_price = float(asks[0][0]) if asks else 0.0
                        spread_abs = ask_price - bid_price
                        spread_pct = (spread_abs / bid_price) * 100 if bid_price else 0.0
                        mid_price = (bid_price + ask_price) / 2 if (bid_price and ask_price) else 0.0
                        spread = BidAskSpread(
                            exchange=exchange,
                            symbol=symbol,
                            timestamp=ts_ms,
                            bid_price=bid_price,
                            ask_price=ask_price,
                            spread_absolute=spread_abs,
                            spread_percentage=spread_pct,
                            mid_price=mid_price
                        )
                        rt_storage.batch_store_spreads([spread], csv_backup=False)
                        
                except Exception as e:
                    print(f"Error fetching {exchange} data for {symbol}: {e}")
                    continue
                    
        # Move to next day
        current_date += timedelta(days=1)
        time.sleep(0.1)  # Small delay to avoid rate limits
    
    print(f"All data fetching and import for {YEAR} complete.")

if __name__ == "__main__":
    main() 