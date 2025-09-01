#!/usr/bin/env python3
"""
Debug script to test VIX correlation strategy and see what prices it's using
"""

import sys
sys.path.append('.')
from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy

def debug_vix_strategy():
    print("🔍 Testing VIX Correlation Strategy")
    print("=" * 50)
    
    # Test the VIX strategy directly
    config_path = 'config/strategies/vix_correlation.json'
    strategy = VIXCorrelationStrategy(config_path)

    print(f"Assets configured: {strategy.assets}")
    print(f"Lookback days: {strategy.lookback_days}")
    print()

    # Test analysis
    try:
        results = strategy.analyze({})
        print("✅ Analysis completed")
        print(f"Signal opportunities found: {len(results.get('signal_opportunities', []))}")
        print()
        
        for i, opp in enumerate(results.get('signal_opportunities', []), 1):
            print(f"🎯 Signal Opportunity #{i}")
            print(f"   Asset: {opp['asset']}")
            print(f"   Signal Type: {opp['signal_type']}")
            print(f"   Price: ${opp['latest_price']:,.2f}")
            print(f"   Confidence: {opp['confidence']:.3f}")
            print(f"   Correlation: {opp['correlation']:.6f}")
            print(f"   VIX Level: {opp.get('latest_vix', 'N/A')}")
            print("   ---")
            
        # Test signal generation
        print("\n🚀 Testing Signal Generation")
        signals = strategy.generate_signals(results)
        print(f"Signals generated: {len(signals)}")
        
        for i, signal in enumerate(signals, 1):
            print(f"📊 Signal #{i}")
            print(f"   Symbol: {signal.symbol}")
            print(f"   Type: {signal.signal_type}")
            print(f"   Price: ${signal.price:,.2f}")
            print(f"   Confidence: {signal.confidence:.3f}")
            print(f"   Timestamp: {signal.timestamp}")
            print("   ---")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vix_strategy()
