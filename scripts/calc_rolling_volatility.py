import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from api.binance_client import BinanceClient
from data.sqlite_helper import CryptoDatabase
import sqlite3
from api.bybit_client import BybitClient

DB_PATH = 'data/crypto_data.db'
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'TAOUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'OCEANUSDT']
BYBIT_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'TAOUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'OCEANUSDT']
INTERVAL = '1m'
WINDOW_MINUTES = 15

# Ensure the crypto_volatility table exists
def ensure_vol_table(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS crypto_volatility (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            window_minutes INTEGER NOT NULL,
            volatility REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

# Fetch 1m OHLCV from Binance
def fetch_binance_ohlcv(symbol, start_time, end_time):
    client = BinanceClient()
    klines = client.get_historical_klines(symbol, INTERVAL, start_time, end_time)
    # kline: [open_time, open, high, low, close, volume, ...]
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close'] = df['close'].astype(float)
    df = df[['open_time', 'close']]
    return df

# Fetch 1m OHLCV from Bybit
def fetch_bybit_ohlcv(symbol, start_time, end_time):
    client = BybitClient()
    # Bybit API expects ISO8601 timestamps
    # We'll fetch in 1-day chunks due to API limits
    all_klines = []
    start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    delta = timedelta(days=1)
    first_chunk = True
    while start_dt < end_dt:
        chunk_end = min(start_dt + delta, end_dt)
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': '1',
            'start': int(start_dt.timestamp()),
            'end': int(chunk_end.timestamp()),
            'limit': 1440  # 1m bars per day
        }
        url = client.base_url + '/v5/market/kline'
        resp = client.session.get(url, params=params, timeout=10)
        if first_chunk:
            print(f"Bybit API response for {symbol} {start_dt} - {chunk_end}:")
            print(resp.text[:1000])
            first_chunk = False
        resp.raise_for_status()
        data = resp.json()
        if data.get('retCode') == 0 and 'result' in data and 'list' in data['result']:
            klines = data['result']['list']
            all_klines.extend(klines)
        start_dt = chunk_end
        time.sleep(0.2)
    # Bybit returns: [open_time, open, high, low, close, volume, turnover]
    df = pd.DataFrame(all_klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'turnover'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='s')
    df['close'] = df['close'].astype(float)
    df = df[['open_time', 'close']]
    return df

# Calculate rolling volatility
def calc_rolling_vol(df, window):
    df = df.copy()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    df['volatility'] = df['log_return'].rolling(window).std() * np.sqrt(window)
    return df[['open_time', 'volatility']].dropna()

# Store in DB
def store_volatility(db_path, symbol, vol_df, window):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for _, row in vol_df.iterrows():
        ts = int(row['open_time'].timestamp())
        c.execute('''
            INSERT INTO crypto_volatility (symbol, timestamp, window_minutes, volatility)
            VALUES (?, ?, ?, ?)
        ''', (symbol, ts, window, row['volatility']))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    ensure_vol_table(DB_PATH)
    from datetime import timezone
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)
    start_str = start.strftime('%Y-%m-%d %H:%M:%S')
    end_str = end.strftime('%Y-%m-%d %H:%M:%S')
    print(f"Actual UTC range: {start_str} to {end_str}")
    for symbol in SYMBOLS:
        print(f"Fetching {symbol} 1m OHLCV from {start_str} to {end_str}")
        df = fetch_binance_ohlcv(symbol, start_str, end_str)
        print(f"Calculating 15m rolling volatility for {symbol}")
        vol_df = calc_rolling_vol(df, WINDOW_MINUTES)
        print(f"Storing {len(vol_df)} volatility records for {symbol}")
        store_volatility(DB_PATH, symbol, vol_df, WINDOW_MINUTES)
    # Bybit
    for symbol in BYBIT_SYMBOLS:
        print(f"Fetching {symbol} 1m OHLCV from Bybit from {start_str} to {end_str}")
        df = fetch_bybit_ohlcv(symbol, start_str, end_str)
        print(f"Calculating 15m rolling volatility for {symbol}_BYBIT")
        vol_df = calc_rolling_vol(df, WINDOW_MINUTES)
        print(f"Storing {len(vol_df)} volatility records for {symbol}_BYBIT")
        store_volatility(DB_PATH, symbol + '_BYBIT', vol_df, WINDOW_MINUTES)
    # --- Test Bybit fetch with only limit parameter ---
    print("Testing Bybit 1m kline fetch with only limit parameter (no start/end)...")
    import requests
    url = "https://api.bybit.com/v5/market/kline"
    params = {'category': 'linear', 'symbol': 'BTCUSDT', 'interval': '1', 'limit': 10}
    resp = requests.get(url, params=params, timeout=10)
    print("Bybit API response (limit only):")
    print(resp.text[:2000])
    print("Done.") 