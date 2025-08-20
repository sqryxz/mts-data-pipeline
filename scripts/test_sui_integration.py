#!/usr/bin/env python3
"""
Test SUI Integration Script
Verifies that SUI has been properly added to the monitored cryptocurrencies
and can fetch data successfully.
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta, timezone
import time

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.coingecko_client import CoinGeckoClient
from data.sqlite_helper import CryptoDatabase

def get_sui_current_price():
    """Get current SUI price using CoinGecko simple price API."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'sui',
            'vs_currencies': 'usd'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['sui']['usd']
    except Exception as e:
        raise Exception(f"Failed to fetch SUI price: {e}")

def test_sui_configuration():
    """Test that SUI is properly configured in the monitored cryptos file."""
    print("🔍 Testing SUI Configuration...")
    
    # Load monitored cryptos configuration
    config_path = 'config/monitored_cryptos.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Check if SUI is in the list
    sui_found = False
    for crypto in config['cryptocurrencies']:
        if crypto['coingecko_id'] == 'sui':
            sui_found = True
            print(f"✅ SUI found in configuration:")
            print(f"   CoinGecko ID: {crypto['coingecko_id']}")
            print(f"   Binance Symbol: {crypto['symbols']['binance']}")
            print(f"   Bybit Symbol: {crypto['symbols']['bybit']}")
            break
    
    if not sui_found:
        print("❌ SUI not found in monitored cryptos configuration")
        return False
    
    return True

def test_sui_data_fetching():
    """Test fetching SUI data from CoinGecko API."""
    print("\n📊 Testing SUI Data Fetching...")
    
    # Initialize CoinGecko client
    coingecko_api_key = os.getenv('COINGECKO_API_KEY')
    cg = CoinGeckoClient(api_key=coingecko_api_key)
    
    try:
        # Test current price
        print("   Fetching current SUI price...")
        price = get_sui_current_price()
        print(f"   ✅ Current SUI price: ${price:.4f}")
        
        # Test historical data (last 7 days)
        print("   Fetching historical SUI data...")
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=7)).timestamp())
        
        ohlcv = cg.get_market_chart_range_data('sui', start_ts, end_ts)
        prices = ohlcv.get('prices', [])
        
        if prices:
            print(f"   ✅ Retrieved {len(prices)} price points")
            print(f"   📈 Price range: ${min(p[1] for p in prices):.4f} - ${max(p[1] for p in prices):.4f}")
        else:
            print("   ❌ No price data received")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error fetching SUI data: {e}")
        return False

def test_sui_database_integration():
    """Test that SUI data can be stored in the database."""
    print("\n💾 Testing SUI Database Integration...")
    
    try:
        # Initialize database
        db = CryptoDatabase('data/crypto_data.db')
        
        # Create sample SUI data
        now = datetime.now()
        sample_data = [{
            'cryptocurrency': 'sui',
            'timestamp': int(now.replace(tzinfo=timezone.utc).timestamp() * 1000),
            'date_str': now.strftime('%Y-%m-%d'),
            'open': 1.50,
            'high': 1.55,
            'low': 1.48,
            'close': 1.52,
            'volume': 1000000.0
        }]
        
        # Insert test data
        inserted = db.insert_crypto_data(sample_data)
        print(f"   ✅ Successfully inserted {inserted} SUI records into database")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error with database integration: {e}")
        return False

def test_correlation_configuration():
    """Test that SUI correlation pairs are properly configured."""
    print("\n🔗 Testing SUI Correlation Configuration...")
    
    # Load correlation pairs configuration
    config_path = 'config/correlation_analysis/monitored_pairs.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Check for SUI correlation pairs
    sui_pairs = []
    for pair_name, pair_config in config['crypto_pairs'].items():
        if 'SUI' in pair_name:
            sui_pairs.append(pair_name)
    
    if sui_pairs:
        print(f"   ✅ Found {len(sui_pairs)} SUI correlation pairs:")
        for pair in sui_pairs:
            print(f"      - {pair}")
    else:
        print("   ❌ No SUI correlation pairs found")
        return False
    
    return True

def main():
    """Run all SUI integration tests."""
    print("🚀 SUI Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_sui_configuration),
        ("Data Fetching", test_sui_data_fetching),
        ("Database Integration", test_sui_database_integration),
        ("Correlation Configuration", test_correlation_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! SUI has been successfully integrated.")
        print("\nNext steps:")
        print("1. Run the main data collection script to fetch SUI data:")
        print("   python3 scripts/fetch_and_import_data.py")
        print("2. Start the correlation analysis to monitor SUI correlations:")
        print("   python3 -m src.correlation_analysis")
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main()
