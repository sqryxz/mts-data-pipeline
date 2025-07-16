import sqlite3
import json
from datetime import datetime

DB_PATH = "data/crypto_data.db"

# Mapping for price table
PRICE_SYMBOLS = {
    'BTCUSDT_BINANCE': ('bitcoin', 'binance'),
    'BTCUSDT_BYBIT': ('bitcoin', 'bybit'),
    'ETHUSDT_BINANCE': ('ethereum', 'binance'),
    'ETHUSDT_BYBIT': ('ethereum', 'bybit'),
}

VOL_SYMBOLS = {
    'BTCUSDT': 'binance',
    'BTCUSDT_BYBIT': 'bybit',
    'ETHUSDT': 'binance',
    'ETHUSDT_BYBIT': 'bybit',
}

ASSETS = ['BTC', 'ETH']
EXCHANGES = ['binance', 'bybit']

# Helper to get nearest price
def get_nearest_price(conn, asset, exchange, target_ts):
    # asset: 'bitcoin' or 'ethereum'
    # exchange: 'binance' or 'bybit' (not used in price table, but could be if you update ingestion)
    c = conn.cursor()
    # Find the price with the minimum absolute difference in timestamp (1-minute window)
    c.execute('''
        SELECT close, timestamp FROM crypto_ohlcv
        WHERE cryptocurrency = ?
        ORDER BY ABS(timestamp - ?) ASC LIMIT 1
    ''', (asset, target_ts * 1000))  # volatility ts is in seconds, price ts in ms
    row = c.fetchone()
    return float(row[0]) if row else None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Find most recent aligned timestamp for both Binance and Bybit volatility
    c.execute('''
        SELECT timestamp FROM crypto_volatility WHERE symbol = 'BTCUSDT_BYBIT'
        INTERSECT
        SELECT timestamp FROM crypto_volatility WHERE symbol = 'BTCUSDT'
        ORDER BY timestamp DESC LIMIT 1
    ''')
    row = c.fetchone()
    if not row:
        print("No aligned timestamp found.")
        return
    ts = row[0]
    dt_utc = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')
    # Get volatility for all
    result = {
        "timestamp": ts,
        "datetime_utc": dt_utc,
        "BTC": {},
        "ETH": {}
    }
    # BTC volatility
    c.execute("SELECT volatility FROM crypto_volatility WHERE symbol = 'BTCUSDT' AND timestamp = ?", (ts,))
    result["BTC"]["volatility_15m_binance"] = c.fetchone()[0]
    c.execute("SELECT volatility FROM crypto_volatility WHERE symbol = 'BTCUSDT_BYBIT' AND timestamp = ?", (ts,))
    result["BTC"]["volatility_15m_bybit"] = c.fetchone()[0]
    # ETH volatility
    c.execute("SELECT volatility FROM crypto_volatility WHERE symbol = 'ETHUSDT' AND timestamp = ?", (ts,))
    result["ETH"]["volatility_15m_binance"] = c.fetchone()[0]
    c.execute("SELECT volatility FROM crypto_volatility WHERE symbol = 'ETHUSDT_BYBIT' AND timestamp = ?", (ts,))
    result["ETH"]["volatility_15m_bybit"] = c.fetchone()[0]
    # Prices (nearest neighbor)
    for asset, asset_name in [("BTC", "bitcoin"), ("ETH", "ethereum")]:
        for exch in EXCHANGES:
            price = get_nearest_price(conn, asset_name, exch, ts)
            result[asset][f"price_{exch}"] = price
    print(json.dumps(result, indent=2))
    conn.close()

if __name__ == "__main__":
    main() 