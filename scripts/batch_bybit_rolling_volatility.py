import requests
import sqlite3
from datetime import datetime, timedelta, timezone
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from services.collector import RollingVolatilityCalculator

BYBIT_BASE_URL = "https://api.bybit.com"
KLINE_ENDPOINT = "/v5/market/kline"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "TAOUSDT", "FETUSDT", "AGIXUSDT", "RNDRUSDT", "OCEANUSDT"]
INTERVAL = "1"  # 1-minute
WINDOW_MINUTES = 15
DB_PATH = "data/crypto_data.db"

# Bybit returns up to 1000 klines per request
MAX_LIMIT = 1000


def fetch_klines(symbol, start_ts, end_ts):
    """Fetch 1m klines for symbol from Bybit between start_ts and end_ts (both in seconds)."""
    klines = []
    next_end = end_ts * 1000  # Bybit expects ms
    while True:
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": INTERVAL,
            "end": int(next_end),
            "limit": MAX_LIMIT
        }
        resp = requests.get(BYBIT_BASE_URL + KLINE_ENDPOINT, params=params)
        data = resp.json()
        if data.get("retCode") != 0 or "result" not in data or "list" not in data["result"]:
            print(f"Error fetching klines for {symbol}: {data}")
            break
        batch = data["result"]["list"]
        if not batch:
            break
        # Bybit returns klines in reverse chronological order
        klines.extend(batch)
        earliest = int(batch[-1][0]) // 1000  # ms to s
        if earliest <= start_ts:
            break
        next_end = int(batch[-1][0]) - 1  # ms
        time.sleep(0.2)  # avoid rate limit
    # Combine and filter
    klines = [k for k in klines if int(k[0]) // 1000 >= start_ts and int(k[0]) // 1000 <= end_ts]
    klines = sorted(klines, key=lambda x: int(x[0]))
    return klines


def main():
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=7)
    start_ts = int(start_dt.timestamp())
    end_ts = int(now.timestamp())

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for symbol in SYMBOLS:
        print(f"Fetching klines for {symbol}...")
        klines = fetch_klines(symbol, start_ts, end_ts)
        print(f"Fetched {len(klines)} klines for {symbol}")
        if not klines:
            continue
        # Use close prices for volatility
        closes = [(int(k[0]) // 1000, float(k[4])) for k in klines]  # (timestamp, close)
        vol_calc = RollingVolatilityCalculator(window_size=WINDOW_MINUTES)
        for ts, close in closes:
            vol = vol_calc.update(close)
            if vol is not None:
                c.execute(
                    "INSERT INTO crypto_volatility (symbol, timestamp, window_minutes, volatility) VALUES (?, ?, ?, ?)",
                    (f"{symbol}_BYBIT", ts, WINDOW_MINUTES, vol)
                )
        conn.commit()
        print(f"Inserted rolling volatility for {symbol}")
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main() 