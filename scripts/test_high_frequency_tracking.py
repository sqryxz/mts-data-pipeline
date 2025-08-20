#!/usr/bin/env python3
"""
Test High-Frequency Tracking Configuration
Verifies that XRP and SUI are properly configured for high-frequency tracking.
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

def test_config_settings():
    """Test that XRP and SUI are in the real-time symbols configuration."""
    print("🔧 Testing Configuration Settings...")
    
    try:
        config = Config()
        
        # Check real-time symbols
        print(f"   📡 Real-time symbols: {config.REALTIME_SYMBOLS}")
        
        # Check if XRP and SUI are included
        xrp_included = 'XRPUSDT' in config.REALTIME_SYMBOLS
        sui_included = 'SUIUSDT' in config.REALTIME_SYMBOLS
        
        print(f"   ✅ XRPUSDT included: {xrp_included}")
        print(f"   ✅ SUIUSDT included: {sui_included}")
        
        return xrp_included and sui_included
        
    except Exception as e:
        print(f"   ❌ Error testing config settings: {e}")
        return False

def test_multi_tier_scheduler():
    """Test that XRP and SUI are in the high-frequency assets."""
    print("\n📊 Testing Multi-Tier Scheduler...")
    
    try:
        scheduler = MultiTierScheduler()
        
        print(f"   🚀 High-frequency assets: {scheduler.high_frequency_assets}")
        print(f"   ⏰ Hourly assets: {scheduler.hourly_assets}")
        
        # Check if XRP and SUI are in high-frequency
        xrp_high_freq = 'ripple' in scheduler.high_frequency_assets
        sui_high_freq = 'sui' in scheduler.high_frequency_assets
        
        # Check if they're not in hourly (should be moved to high-frequency)
        xrp_not_hourly = 'ripple' not in scheduler.hourly_assets
        sui_not_hourly = 'sui' not in scheduler.hourly_assets
        
        print(f"   ✅ XRP in high-frequency: {xrp_high_freq}")
        print(f"   ✅ SUI in high-frequency: {sui_high_freq}")
        print(f"   ✅ XRP not in hourly: {xrp_not_hourly}")
        print(f"   ✅ SUI not in hourly: {sui_not_hourly}")
        
        return xrp_high_freq and sui_high_freq and xrp_not_hourly and sui_not_hourly
        
    except Exception as e:
        print(f"   ❌ Error testing multi-tier scheduler: {e}")
        return False

def test_enhanced_scheduler():
    """Test that XRP and SUI are in the enhanced scheduler high-frequency assets."""
    print("\n🚀 Testing Enhanced Multi-Tier Scheduler...")
    
    try:
        scheduler = EnhancedMultiTierScheduler()
        
        print(f"   🚀 High-frequency assets: {scheduler.high_frequency_assets}")
        print(f"   ⏰ Hourly assets: {scheduler.hourly_assets}")
        
        # Check if XRP and SUI are in high-frequency
        xrp_high_freq = 'ripple' in scheduler.high_frequency_assets
        sui_high_freq = 'sui' in scheduler.high_frequency_assets
        
        # Check if they're not in hourly (should be moved to high-frequency)
        xrp_not_hourly = 'ripple' not in scheduler.hourly_assets
        sui_not_hourly = 'sui' not in scheduler.hourly_assets
        
        print(f"   ✅ XRP in high-frequency: {xrp_high_freq}")
        print(f"   ✅ SUI in high-frequency: {sui_high_freq}")
        print(f"   ✅ XRP not in hourly: {xrp_not_hourly}")
        print(f"   ✅ SUI not in hourly: {sui_not_hourly}")
        
        return xrp_high_freq and sui_high_freq and xrp_not_hourly and sui_not_hourly
        
    except Exception as e:
        print(f"   ❌ Error testing enhanced scheduler: {e}")
        return False

def test_optimized_collection_config():
    """Test the optimized collection configuration file."""
    print("\n📋 Testing Optimized Collection Configuration...")
    
    try:
        config_path = 'config/optimized_collection.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        high_freq_assets = config['collection_strategy']['tiers']['high_frequency']['assets']
        hourly_assets = config['collection_strategy']['tiers']['hourly']['assets']
        
        print(f"   🚀 High-frequency assets: {high_freq_assets}")
        print(f"   ⏰ Hourly assets: {hourly_assets}")
        
        # Check if XRP and SUI are in high-frequency
        xrp_high_freq = 'ripple' in high_freq_assets
        sui_high_freq = 'sui' in high_freq_assets
        
        # Check if they're not in hourly
        xrp_not_hourly = 'ripple' not in hourly_assets
        sui_not_hourly = 'sui' not in hourly_assets
        
        print(f"   ✅ XRP in high-frequency: {xrp_high_freq}")
        print(f"   ✅ SUI in high-frequency: {sui_high_freq}")
        print(f"   ✅ XRP not in hourly: {xrp_not_hourly}")
        print(f"   ✅ SUI not in hourly: {sui_not_hourly}")
        
        return xrp_high_freq and sui_high_freq and xrp_not_hourly and sui_not_hourly
        
    except Exception as e:
        print(f"   ❌ Error testing optimized collection config: {e}")
        return False

def test_real_time_signal_aggregator():
    """Test that XRP and SUI are in the real-time signal aggregator."""
    print("\n📡 Testing Real-Time Signal Aggregator...")
    
    try:
        from services.realtime_signal_aggregator import RealTimeSignalAggregator
        
        aggregator = RealTimeSignalAggregator()
        
        print(f"   📡 Monitored symbols: {sorted(aggregator.monitored_symbols)}")
        
        # Check if XRP and SUI are included
        xrp_included = 'XRPUSDT' in aggregator.monitored_symbols
        sui_included = 'SUIUSDT' in aggregator.monitored_symbols
        
        print(f"   ✅ XRPUSDT included: {xrp_included}")
        print(f"   ✅ SUIUSDT included: {sui_included}")
        
        return xrp_included and sui_included
        
    except Exception as e:
        print(f"   ❌ Error testing real-time signal aggregator: {e}")
        return False

def main():
    """Run all high-frequency tracking tests."""
    print("🚀 High-Frequency Tracking Test Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration Settings", test_config_settings),
        ("Multi-Tier Scheduler", test_multi_tier_scheduler),
        ("Enhanced Scheduler", test_enhanced_scheduler),
        ("Optimized Collection Config", test_optimized_collection_config),
        ("Real-Time Signal Aggregator", test_real_time_signal_aggregator)
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
    print("=" * 60)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! XRP and SUI are properly configured for high-frequency tracking.")
        print("\nHigh-Frequency Tracking Configuration:")
        print("✅ XRP and SUI added to real-time symbols (XRPUSDT, SUIUSDT)")
        print("✅ XRP and SUI moved to high-frequency assets (15-minute intervals)")
        print("✅ XRP and SUI removed from hourly assets")
        print("✅ Real-time signal aggregator includes XRP and SUI")
        print("\nNext steps:")
        print("1. Start the high-frequency tracking:")
        print("   python3 main_enhanced.py --background")
        print("2. Or use the optimized pipeline:")
        print("   python3 main_optimized.py --background")
        print("3. Monitor the logs to see XRP and SUI data collection")
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main()
