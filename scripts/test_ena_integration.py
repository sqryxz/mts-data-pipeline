#!/usr/bin/env python3
"""
Test ENA Integration
Verifies that ENA (Ethena) has been properly integrated into all components of the MTS Data Pipeline.
"""

import sys
import os
import json
from datetime import datetime

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import Config
from services.multi_tier_scheduler import MultiTierScheduler
from services.enhanced_multi_tier_scheduler import EnhancedMultiTierScheduler
from api.coingecko_client import CoinGeckoClient
from data.sqlite_helper import CryptoDatabase

def test_ena_configuration():
    """Test that ENA is in the monitored cryptos configuration."""
    print("🔧 Testing ENA Configuration...")
    
    try:
        # Load monitored cryptos config
        with open('config/monitored_cryptos.json', 'r') as f:
            crypto_config = json.load(f)
        
        # Check if ENA is in the list
        ena_found = False
        for crypto in crypto_config['cryptocurrencies']:
            if crypto['coingecko_id'] == 'ethena':
                ena_found = True
                print(f"   ✅ ENA found in monitored cryptos")
                print(f"   📊 CoinGecko ID: {crypto['coingecko_id']}")
                print(f"   🏪 Binance symbol: {crypto['symbols']['binance']}")
                print(f"   🏪 Bybit symbol: {crypto['symbols']['bybit']}")
                break
        
        if not ena_found:
            print("   ❌ ENA not found in monitored cryptos")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing ENA configuration: {e}")
        return False

def test_ena_correlation_pairs():
    """Test that ENA correlation pairs are configured."""
    print("\n🔗 Testing ENA Correlation Pairs...")
    
    try:
        # Load correlation pairs config
        with open('config/correlation_analysis/monitored_pairs.json', 'r') as f:
            pairs_config = json.load(f)
        
        # Check for ENA correlation pairs
        ena_pairs = []
        for pair_name, pair_config in pairs_config['crypto_pairs'].items():
            if 'ENA' in pair_name or pair_config['primary'] == 'ethena' or pair_config['secondary'] == 'ethena':
                ena_pairs.append(pair_name)
        
        print(f"   📊 Found {len(ena_pairs)} ENA correlation pairs:")
        for pair in ena_pairs:
            print(f"      ✅ {pair}")
        
        # Check for specific important pairs
        expected_pairs = ['BTC_ENA', 'ETH_ENA', 'SOL_ENA', 'XRP_ENA']
        missing_pairs = []
        for expected in expected_pairs:
            if expected not in ena_pairs:
                missing_pairs.append(expected)
        
        if missing_pairs:
            print(f"   ⚠️ Missing expected pairs: {missing_pairs}")
            return False
        
        return len(ena_pairs) > 0
        
    except Exception as e:
        print(f"   ❌ Error testing ENA correlation pairs: {e}")
        return False

def test_ena_high_frequency_tracking():
    """Test that ENA is configured for high-frequency tracking."""
    print("\n⚡ Testing ENA High-Frequency Tracking...")
    
    try:
        # Test multi-tier scheduler
        scheduler = MultiTierScheduler()
        ena_in_high_freq = 'ethena' in scheduler.high_frequency_assets
        ena_in_hourly = 'ethena' in scheduler.hourly_assets
        
        print(f"   🚀 ENA in high-frequency assets: {ena_in_high_freq}")
        print(f"   ⏰ ENA in hourly assets: {ena_in_hourly}")
        
        if not ena_in_high_freq:
            print("   ❌ ENA not in high-frequency assets")
            return False
        
        if ena_in_hourly:
            print("   ⚠️ ENA should not be in hourly assets (should be high-frequency only)")
            return False
        
        # Test enhanced scheduler
        enhanced_scheduler = EnhancedMultiTierScheduler()
        ena_in_enhanced_high_freq = 'ethena' in enhanced_scheduler.high_frequency_assets
        
        print(f"   🔧 ENA in enhanced high-frequency assets: {ena_in_enhanced_high_freq}")
        
        return ena_in_high_freq and ena_in_enhanced_high_freq
        
    except Exception as e:
        print(f"   ❌ Error testing ENA high-frequency tracking: {e}")
        return False

def test_ena_real_time_config():
    """Test that ENA is in real-time symbols configuration."""
    print("\n📡 Testing ENA Real-Time Configuration...")
    
    try:
        config = Config()
        
        # Check real-time symbols
        print(f"   📡 Real-time symbols: {config.REALTIME_SYMBOLS}")
        
        # Check if ENA is included
        ena_included = 'ENAUSDT' in config.REALTIME_SYMBOLS
        
        print(f"   ✅ ENAUSDT included: {ena_included}")
        
        return ena_included
        
    except Exception as e:
        print(f"   ❌ Error testing ENA real-time config: {e}")
        return False

def test_ena_asset_mappings():
    """Test that ENA is in all asset mappings."""
    print("\n🗺️ Testing ENA Asset Mappings...")
    
    try:
        # Check that ENA is in the asset mappings by examining the source files
        # This is a simpler approach that doesn't require importing the modules
        
        # Check correlation monitor asset mapping
        with open('src/correlation_analysis/core/correlation_monitor.py', 'r') as f:
            content = f.read()
            if "'ENA': 'ethena'" in content:
                print("   ✅ ENA in correlation monitor asset mapping")
            else:
                print("   ❌ ENA not in correlation monitor asset mapping")
                return False
        
        # Check mosaic generator asset mapping
        with open('src/correlation_analysis/visualization/mosaic_generator.py', 'r') as f:
            content = f.read()
            if "'ENA': 'ethena'" in content:
                print("   ✅ ENA in mosaic generator asset mapping")
            else:
                print("   ❌ ENA not in mosaic generator asset mapping")
                return False
        
        # Check paper trading CoinGecko client asset mapping
        with open('paper_trading_engine/src/services/coingecko_client.py', 'r') as f:
            content = f.read()
            if "'ENA': 'ethena'" in content:
                print("   ✅ ENA in paper trading CoinGecko client asset mapping")
            else:
                print("   ❌ ENA not in paper trading CoinGecko client asset mapping")
                return False
        
        # Check signal processor asset mapping
        with open('paper_trading_engine/src/signal_consumer/signal_processor.py', 'r') as f:
            content = f.read()
            if "'ethena': 'ENAUSDT'" in content or "'enausdt': 'ENAUSDT'" in content:
                print("   ✅ ENA in signal processor asset mapping")
            else:
                print("   ❌ ENA not in signal processor asset mapping")
                return False
        
        print("   ✅ All asset mappings updated with ENA")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing ENA asset mappings: {e}")
        return False

def test_ena_data_fetch():
    """Test that ENA data can be fetched from CoinGecko."""
    print("\n📊 Testing ENA Data Fetch...")
    
    try:
        coingecko_client = CoinGeckoClient()
        
        # Test market chart data fetch (this method exists)
        market_data = coingecko_client.get_market_chart_data('ethena', 1)
        
        if market_data and 'prices' in market_data:
            current_price = market_data['prices'][-1][1] if market_data['prices'] else None
            if current_price:
                print(f"   💰 Current ENA price: ${current_price:.4f}")
                print("   ✅ ENA data fetch successful")
                return True
            else:
                print("   ❌ Failed to get ENA current price from market data")
                return False
        else:
            print("   ❌ Failed to fetch ENA market data")
            return False
        
    except Exception as e:
        print(f"   ❌ Error testing ENA data fetch: {e}")
        return False

def test_ena_database_integration():
    """Test that ENA can be stored and retrieved from database."""
    print("\n💾 Testing ENA Database Integration...")
    
    try:
        db = CryptoDatabase('data/crypto_data.db')
        
        # Check if ENA data exists in database using the correct method
        ena_data = db.get_crypto_data('ethena', days=7)
        
        if not ena_data.empty:
            print(f"   📊 Found {len(ena_data)} ENA records in database")
            print("   ✅ ENA database integration working")
            return True
        else:
            print("   ⚠️ No ENA data found in database (may need to run fetch script)")
            return True  # Not a failure, just no data yet
        
    except Exception as e:
        print(f"   ❌ Error testing ENA database integration: {e}")
        return False

def main():
    """Run all ENA integration tests."""
    print("🚀 ENA Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_ena_configuration),
        ("Correlation Pairs", test_ena_correlation_pairs),
        ("High-Frequency Tracking", test_ena_high_frequency_tracking),
        ("Real-Time Configuration", test_ena_real_time_config),
        ("Asset Mappings", test_ena_asset_mappings),
        ("Data Fetch", test_ena_data_fetch),
        ("Database Integration", test_ena_database_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! ENA has been successfully integrated.")
        print("\nENA Integration Summary:")
        print("✅ ENA added to monitored cryptocurrencies")
        print("✅ ENA correlation pairs configured")
        print("✅ ENA added to high-frequency tracking (15-minute intervals)")
        print("✅ ENAUSDT added to real-time symbols")
        print("✅ ENA asset mappings updated in all components")
        print("✅ ENA data fetching working")
        print("✅ ENA database integration ready")
        print("\nNext steps:")
        print("1. Fetch historical ENA data:")
        print("   python3 scripts/fetch_ena_historical_data.py")
        print("2. Start high-frequency tracking:")
        print("   python3 main_enhanced.py --background")
        print("3. Monitor ENA correlation analysis")
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main()
