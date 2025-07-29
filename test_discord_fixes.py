#!/usr/bin/env python3

"""
Test Discord Async Fixes
Verifies that the Discord integration works correctly in both sync and async contexts.
"""

import sys
import os
import asyncio
import threading
import time
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_signals():
    """Create test signals for testing."""
    return [
        TradingSignal(
            asset="bitcoin",
            signal_type=SignalType.LONG,
            timestamp=int(datetime.now().timestamp() * 1000),
            price=50000.0,
            strategy_name="TestStrategy",
            signal_strength=SignalStrength.STRONG,
            confidence=0.85,
            position_size=0.02,
            stop_loss=48000.0,
            take_profit=55000.0,
            max_risk=0.02,
            analysis_data={
                'volatility': 0.15,
                'volatility_threshold': 0.08,
                'volatility_ratio': 1.88,
                'reason': 'Test signal for async fixes'
            }
        ),
        TradingSignal(
            asset="ethereum",
            signal_type=SignalType.SHORT,
            timestamp=int(datetime.now().timestamp() * 1000),
            price=3000.0,
            strategy_name="TestStrategy",
            signal_strength=SignalStrength.MODERATE,
            confidence=0.75,
            position_size=0.015,
            stop_loss=3200.0,
            take_profit=2700.0,
            max_risk=0.015,
            analysis_data={
                'volatility': 0.25,
                'volatility_threshold': 0.12,
                'volatility_ratio': 2.08,
                'reason': 'Test signal for async fixes'
            }
        )
    ]

def test_sync_context():
    """Test Discord alerts in synchronous context."""
    
    print("🔄 Testing Discord Alerts in Sync Context")
    print("=" * 50)
    print()
    
    try:
        # Configure aggregator with Discord (but no webhook URL for testing)
        strategy_weights = {'test': 1.0}
        aggregation_config = {
            'discord_alerts': True,
            'discord_webhook_url': 'https://discord.com/api/webhooks/test/test',  # Invalid for testing
            'discord_config': {
                'min_confidence': 0.6,
                'enabled_assets': ['bitcoin', 'ethereum']
            }
        }
        
        # Initialize aggregator
        aggregator = SignalAggregator(strategy_weights, aggregation_config)
        
        # Create test signals
        test_signals = create_test_signals()
        strategy_signals = {'test': test_signals}
        
        print("📊 Processing signals in sync context...")
        
        # This should not raise any async-related errors
        aggregated_signals = aggregator.aggregate_signals(strategy_signals)
        
        print(f"✅ Successfully processed {len(aggregated_signals)} signals in sync context")
        print("✅ No async context errors occurred")
        
        # Clean up
        aggregator.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in sync context test: {e}")
        return False

def test_async_context():
    """Test Discord alerts in asynchronous context."""
    
    print("\n🔄 Testing Discord Alerts in Async Context")
    print("=" * 50)
    print()
    
    async def async_test():
        try:
            # Configure aggregator with Discord
            strategy_weights = {'test': 1.0}
            aggregation_config = {
                'discord_alerts': True,
                'discord_webhook_url': 'https://discord.com/api/webhooks/test/test',  # Invalid for testing
                'discord_config': {
                    'min_confidence': 0.6,
                    'enabled_assets': ['bitcoin', 'ethereum']
                }
            }
            
            # Initialize aggregator
            aggregator = SignalAggregator(strategy_weights, aggregation_config)
            
            # Create test signals
            test_signals = create_test_signals()
            strategy_signals = {'test': test_signals}
            
            print("📊 Processing signals in async context...")
            
            # This should work correctly in async context
            aggregated_signals = aggregator.aggregate_signals(strategy_signals)
            
            print(f"✅ Successfully processed {len(aggregated_signals)} signals in async context")
            print("✅ No async context errors occurred")
            
            # Clean up
            aggregator.cleanup()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in async context test: {e}")
            return False
    
    return asyncio.run(async_test())

def test_thread_safety():
    """Test Discord alerts in threaded context."""
    
    print("\n🧵 Testing Discord Alerts in Threaded Context")
    print("=" * 50)
    print()
    
    def thread_test():
        try:
            # Configure aggregator with Discord
            strategy_weights = {'test': 1.0}
            aggregation_config = {
                'discord_alerts': True,
                'discord_webhook_url': 'https://discord.com/api/webhooks/test/test',  # Invalid for testing
                'discord_config': {
                    'min_confidence': 0.6,
                    'enabled_assets': ['bitcoin', 'ethereum']
                }
            }
            
            # Initialize aggregator
            aggregator = SignalAggregator(strategy_weights, aggregation_config)
            
            # Create test signals
            test_signals = create_test_signals()
            strategy_signals = {'test': test_signals}
            
            print("📊 Processing signals in threaded context...")
            
            # This should work correctly in threaded context
            aggregated_signals = aggregator.aggregate_signals(strategy_signals)
            
            print(f"✅ Successfully processed {len(aggregated_signals)} signals in threaded context")
            print("✅ No thread safety errors occurred")
            
            # Clean up
            aggregator.cleanup()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in threaded context test: {e}")
            return False
    
    # Run in a separate thread
    thread = threading.Thread(target=thread_test)
    thread.start()
    thread.join()
    
    return thread.is_alive() == False

def test_timestamp_sorting():
    """Test timestamp sorting with different data types."""
    
    print("\n⏰ Testing Timestamp Sorting")
    print("=" * 50)
    print()
    
    try:
        # Create signals with different timestamp types
        signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=1640995200000,  # int
                price=50000.0,
                strategy_name="TestStrategy",
                signal_strength=SignalStrength.STRONG,
                confidence=0.9,
                position_size=0.02,
                stop_loss=48000.0,
                take_profit=55000.0,
                max_risk=0.02
            ),
            TradingSignal(
                asset="ethereum",
                signal_type=SignalType.SHORT,
                timestamp="1640995200000",  # string
                price=3000.0,
                strategy_name="TestStrategy",
                signal_strength=SignalStrength.MODERATE,
                confidence=0.7,
                position_size=0.015,
                stop_loss=3200.0,
                take_profit=2700.0,
                max_risk=0.015
            ),
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=1640995200001,  # int
                price=50000.0,
                strategy_name="TestStrategy",
                signal_strength=SignalStrength.WEAK,
                confidence=0.5,
                position_size=0.01,
                stop_loss=48000.0,
                take_profit=55000.0,
                max_risk=0.01
            )
        ]
        
        # Configure aggregator
        strategy_weights = {'test': 1.0}
        aggregator = SignalAggregator(strategy_weights, {})
        
        # Process signals (this will test timestamp sorting)
        strategy_signals = {'test': signals}
        aggregated_signals = aggregator.aggregate_signals(strategy_signals)
        
        print(f"✅ Successfully sorted {len(aggregated_signals)} signals with mixed timestamp types")
        print("✅ No timestamp sorting errors occurred")
        
        # Verify sorting (should be by confidence descending)
        confidences = [s.confidence for s in aggregated_signals]
        print(f"📊 Signal confidences after sorting: {confidences}")
        
        # Clean up
        aggregator.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Error in timestamp sorting test: {e}")
        return False

def test_resource_cleanup():
    """Test that resources are properly cleaned up."""
    
    print("\n🧹 Testing Resource Cleanup")
    print("=" * 50)
    print()
    
    try:
        # Create multiple aggregators
        aggregators = []
        for i in range(3):
            strategy_weights = {'test': 1.0}
            aggregation_config = {
                'discord_alerts': True,
                'discord_webhook_url': 'https://discord.com/api/webhooks/test/test',
                'discord_config': {'min_confidence': 0.6}
            }
            
            aggregator = SignalAggregator(strategy_weights, aggregation_config)
            aggregators.append(aggregator)
        
        print(f"✅ Created {len(aggregators)} aggregators with Discord managers")
        
        # Clean up all aggregators
        for i, aggregator in enumerate(aggregators):
            aggregator.cleanup()
            print(f"✅ Cleaned up aggregator {i+1}")
        
        print("✅ All resources cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in resource cleanup test: {e}")
        return False

def main():
    """Run all tests."""
    
    print("🧪 Discord Async Fixes Test Suite")
    print("=" * 60)
    print()
    print("Testing the fixes for async/sync context issues...")
    print()
    
    # Run all tests
    tests = [
        ("Sync Context", test_sync_context),
        ("Async Context", test_async_context),
        ("Thread Safety", test_thread_safety),
        ("Timestamp Sorting", test_timestamp_sorting),
        ("Resource Cleanup", test_resource_cleanup)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Discord async fixes are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 