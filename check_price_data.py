#!/usr/bin/env python3
"""
Script to check latest BTC price data and compare with alert prices
"""

from src.data.sqlite_helper import CryptoDatabase
from datetime import datetime

def check_price_data():
    print("🔍 Checking BTC Price Data")
    print("=" * 40)
    
    # Get latest data
    db = CryptoDatabase()
    data = db.get_strategy_market_data(['bitcoin'], days=1)
    
    if 'bitcoin' in data and not data['bitcoin'].empty:
        latest = data['bitcoin'].iloc[-1]
        alert_price = 112831.22
        
        print(f"📊 Latest BTC Data:")
        print(f"   Price: ${latest['close']:,.2f}")
        print(f"   Date: {latest['date_str']}")
        print(f"   Time: {latest['datetime']}")
        print(f"   Timestamp: {latest['timestamp']}")
        
        print(f"\n📈 Alert Price Comparison:")
        print(f"   Alert Price: ${alert_price:,.2f}")
        print(f"   Current Price: ${latest['close']:,.2f}")
        print(f"   Difference: ${latest['close'] - alert_price:,.2f}")
        print(f"   Percentage: {((latest['close'] - alert_price) / alert_price * 100):.2f}%")
        
        # Check if price is stale
        time_diff = datetime.now() - latest['datetime']
        print(f"\n⏰ Data Freshness:")
        print(f"   Time since last update: {time_diff}")
        print(f"   Data is {'fresh' if time_diff.total_seconds() < 3600 else 'stale'}")
        
        # Show recent price history
        print(f"\n📋 Recent Price History (last 5 records):")
        recent_data = data['bitcoin'].tail()
        for _, row in recent_data.iterrows():
            print(f"   {row['datetime']}: ${row['close']:,.2f}")
            
    else:
        print("❌ No BTC data found in database")

if __name__ == "__main__":
    check_price_data()
