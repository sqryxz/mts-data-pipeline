#!/usr/bin/env python3

import sqlite3
import pandas as pd
from datetime import datetime

def analyze_granularity():
    conn = sqlite3.connect('data/crypto_data.db')
    cursor = conn.cursor()
    
    # Get recent Bitcoin data
    cursor.execute('''
        SELECT timestamp, date_str, open, high, low, close, volume 
        FROM crypto_ohlcv 
        WHERE cryptocurrency = "bitcoin" 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''')
    btc_data = cursor.fetchall()
    
    # Get recent Ethereum data
    cursor.execute('''
        SELECT timestamp, date_str, open, high, low, close, volume 
        FROM crypto_ohlcv 
        WHERE cryptocurrency = "ethereum" 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''')
    eth_data = cursor.fetchall()
    
    conn.close()
    
    print("=== BTC/ETH Data Granularity Analysis ===\n")
    
    # Analyze Bitcoin data
    print("Bitcoin Data:")
    print(f"Total records: {len(btc_data)}")
    if btc_data:
        print(f"Most recent: {btc_data[0][1]} ({btc_data[0][0]})")
        print(f"Oldest in sample: {btc_data[-1][1]} ({btc_data[-1][0]})")
        
        # Calculate intervals
        intervals = []
        for i in range(len(btc_data)-1):
            interval = btc_data[i][0] - btc_data[i+1][0]
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            print(f"Average interval: {avg_interval/1000/60:.1f} minutes")
            print(f"Min interval: {min(intervals)/1000/60:.1f} minutes")
            print(f"Max interval: {max(intervals)/1000/60:.1f} minutes")
    
    print("\n" + "="*50 + "\n")
    
    # Analyze Ethereum data
    print("Ethereum Data:")
    print(f"Total records: {len(eth_data)}")
    if eth_data:
        print(f"Most recent: {eth_data[0][1]} ({eth_data[0][0]})")
        print(f"Oldest in sample: {eth_data[-1][1]} ({eth_data[-1][0]})")
        
        # Calculate intervals
        intervals = []
        for i in range(len(eth_data)-1):
            interval = eth_data[i][0] - eth_data[i+1][0]
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            print(f"Average interval: {avg_interval/1000/60:.1f} minutes")
            print(f"Min interval: {min(intervals)/1000/60:.1f} minutes")
            print(f"Max interval: {max(intervals)/1000/60:.1f} minutes")
    
    print("\n" + "="*50 + "\n")
    
    # Check CSV files
    print("CSV File Analysis:")
    try:
        btc_csv = pd.read_csv('data/raw/bitcoin_2025.csv')
        print(f"Bitcoin CSV: {len(btc_csv)} records")
        print(f"Columns: {list(btc_csv.columns)}")
        
        # Convert timestamp to datetime
        btc_csv['datetime'] = pd.to_datetime(btc_csv['timestamp'], unit='ms')
        print(f"Date range: {btc_csv['datetime'].min()} to {btc_csv['datetime'].max()}")
        
        # Calculate intervals
        btc_csv = btc_csv.sort_values('timestamp')
        intervals = btc_csv['timestamp'].diff().dropna()
        print(f"Average interval: {intervals.mean()/1000/60:.1f} minutes")
        print(f"Min interval: {intervals.min()/1000/60:.1f} minutes")
        print(f"Max interval: {intervals.max()/1000/60:.1f} minutes")
        
    except Exception as e:
        print(f"Error reading Bitcoin CSV: {e}")
    
    print("\n" + "="*50 + "\n")
    
    try:
        eth_csv = pd.read_csv('data/raw/ethereum_2025.csv')
        print(f"Ethereum CSV: {len(eth_csv)} records")
        print(f"Columns: {list(eth_csv.columns)}")
        
        # Convert timestamp to datetime
        eth_csv['datetime'] = pd.to_datetime(eth_csv['timestamp'], unit='ms')
        print(f"Date range: {eth_csv['datetime'].min()} to {eth_csv['datetime'].max()}")
        
        # Calculate intervals
        eth_csv = eth_csv.sort_values('timestamp')
        intervals = eth_csv['timestamp'].diff().dropna()
        print(f"Average interval: {intervals.mean()/1000/60:.1f} minutes")
        print(f"Min interval: {intervals.min()/1000/60:.1f} minutes")
        print(f"Max interval: {intervals.max()/1000/60:.1f} minutes")
        
    except Exception as e:
        print(f"Error reading Ethereum CSV: {e}")

if __name__ == "__main__":
    analyze_granularity() 