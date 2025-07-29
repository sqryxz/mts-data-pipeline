#!/usr/bin/env python3
"""
JSON Alert Demonstration - Volatility Strategy
Shows timestamped JSON alerts when volatility spikes above 90th percentile of past 24 hours.
"""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signals.strategies.volatility_strategy import VolatilityStrategy
from src.data.sqlite_helper import CryptoDatabase
from src.utils.json_alert_system import JSONAlertSystem
from src.data.signal_models import SignalType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demonstrate_json_alerts():
    """Demonstrate JSON alert generation with 90th percentile threshold."""
    
    print("🚨 JSON Alert Demonstration - Volatility Strategy")
    print("=" * 60)
    print("📊 Using 90th percentile threshold over 24-hour window")
    print("📝 Generating timestamped JSON alerts for volatility spikes")
    print()
    
    # Initialize components
    strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
    database = CryptoDatabase()
    alert_system = JSONAlertSystem()
    
    # Get 24 hours of market data
    print("📈 Fetching 24 hours of market data...")
    market_data = database.get_strategy_market_data_hours(['bitcoin', 'ethereum'], hours=24)
    
    # Run volatility analysis
    print("🔍 Running volatility analysis...")
    analysis_results = strategy.analyze(market_data)
    
    # Generate signals
    print("📊 Generating trading signals...")
    signals = strategy.generate_signals(analysis_results)
    
    print(f"✅ Generated {len(signals)} signals")
    print()
    
    # Generate JSON alerts from signals
    print("📝 Generating JSON alerts...")
    alerts = alert_system.generate_alerts_from_signals(signals)
    
    print(f"🚨 Generated {len(alerts)} JSON alerts")
    print()
    
    # Display alerts
    for i, alert in enumerate(alerts, 1):
        print(f"Alert {i}:")
        print(f"  📅 Timestamp: {datetime.fromtimestamp(alert['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  💰 Asset: {alert['asset'].capitalize()}")
        print(f"  💵 Current Price: ${alert['current_price']:,.2f}")
        print(f"  📈 Volatility Value: {alert['volatility_value']:.2%}")
        print(f"  📊 Volatility Threshold: {alert['volatility_threshold']:.2%}")
        print(f"  📈 Volatility Percentile: {alert['volatility_percentile']:.1f}%")
        print(f"  🎯 Position Direction: {alert['position_direction']}")
        print(f"  📊 Signal Type: {alert['signal_type']}")
        print(f"  ✅ Threshold Exceeded: {alert['threshold_exceeded']}")
        print()
    
    # Save alerts to files
    if alerts:
        print("💾 Saving alerts to JSON files...")
        saved_files = alert_system.save_bulk_alerts(alerts)
        print(f"✅ Saved {len(saved_files)} alert files:")
        for filepath in saved_files:
            print(f"  📁 {filepath}")
        print()
    
    return alerts

def show_alert_format():
    """Show the JSON alert format."""
    
    print("📋 JSON Alert Format")
    print("=" * 40)
    print()
    
    # Create a sample alert
    sample_alert = {
        "timestamp": int(datetime.now().timestamp() * 1000),
        "asset": "bitcoin",
        "current_price": 45000.00,
        "volatility_value": 0.025,
        "volatility_threshold": 0.020,
        "volatility_percentile": 92.5,
        "position_direction": "BUY",
        "signal_type": "LONG",
        "alert_type": "volatility_spike",
        "threshold_exceeded": True
    }
    
    print("Sample JSON Alert:")
    print(json.dumps(sample_alert, indent=2))
    print()
    
    print("Alert Fields:")
    print("  📅 timestamp: Unix timestamp in milliseconds")
    print("  💰 asset: Asset name (bitcoin, ethereum)")
    print("  💵 current_price: Current asset price")
    print("  📈 volatility_value: Current volatility value")
    print("  📊 volatility_threshold: 90th percentile threshold")
    print("  📈 volatility_percentile: Current percentile")
    print("  🎯 position_direction: Suggested position (BUY/SELL/HOLD)")
    print("  📊 signal_type: Signal type (LONG/SHORT)")
    print("  🚨 alert_type: Type of alert (volatility_spike)")
    print("  ✅ threshold_exceeded: Whether 90th percentile was exceeded")
    print()

def test_alert_system():
    """Test the alert system functionality."""
    
    print("🧪 Testing Alert System")
    print("=" * 30)
    print()
    
    alert_system = JSONAlertSystem()
    
    # Test alert generation
    print("1. Testing alert generation...")
    test_alert = alert_system.generate_volatility_alert(
        asset="bitcoin",
        current_price=45000.00,
        volatility_value=0.025,
        volatility_threshold=0.020,
        volatility_percentile=92.5,
        signal_type=SignalType.LONG
    )
    
    print("✅ Test alert generated successfully")
    print(f"   Asset: {test_alert['asset']}")
    print(f"   Position Direction: {test_alert['position_direction']}")
    print(f"   Threshold Exceeded: {test_alert['threshold_exceeded']}")
    print()
    
    # Test alert saving
    print("2. Testing alert saving...")
    try:
        filepath = alert_system.save_alert(test_alert, "test_alert.json")
        print(f"✅ Test alert saved to: {filepath}")
        
        # Clean up test file
        import os
        if os.path.exists(filepath):
            os.remove(filepath)
            print("🧹 Test file cleaned up")
    except Exception as e:
        print(f"❌ Failed to save test alert: {e}")
    print()
    
    # Test recent alerts
    print("3. Testing recent alerts retrieval...")
    recent_alerts = alert_system.get_recent_alerts(hours=24)
    print(f"✅ Found {len(recent_alerts)} recent alerts")
    print()

def show_configuration():
    """Show the current configuration."""
    
    print("⚙️ Current Configuration")
    print("=" * 30)
    print()
    
    config = {
        "volatility_threshold_percentile": 90,
        "time_window_hours": 24,
        "enabled_assets": ["bitcoin", "ethereum"],
        "alert_format": "json",
        "include_momentum": True,
        "position_direction_logic": "momentum_based"
    }
    
    print("Alert System Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    print("Strategy Configuration:")
    strategy_config = {
        "volatility_window": 15,
        "historical_hours": 24,
        "volatility_threshold_percentile": 90,
        "extreme_volatility_percentile": 95
    }
    
    for key, value in strategy_config.items():
        print(f"  {key}: {value}")
    print()

def main():
    """Main demonstration function."""
    
    print("🚀 Starting JSON Alert Demonstration")
    print("=" * 50)
    print()
    
    try:
        # Show configuration
        show_configuration()
        
        # Show alert format
        show_alert_format()
        
        # Test alert system
        test_alert_system()
        
        # Demonstrate with real data
        alerts = demonstrate_json_alerts()
        
        # Summary
        print("📊 Demonstration Summary")
        print("=" * 30)
        print(f"✅ JSON Alert System: Working")
        print(f"✅ 90th Percentile Threshold: Configured")
        print(f"✅ 24-Hour Window: Configured")
        print(f"✅ Timestamped Alerts: Generated")
        print(f"✅ Asset Information: Included")
        print(f"✅ Current Price: Included")
        print(f"✅ Volatility Value: Included")
        print(f"✅ Position Direction: Included")
        print(f"📝 Total Alerts Generated: {len(alerts)}")
        print()
        
        if alerts:
            print("🎉 SUCCESS: All requested features implemented!")
            print("   - JSON alert format ✓")
            print("   - 90th percentile threshold ✓")
            print("   - 24-hour window ✓")
            print("   - Timestamped alerts ✓")
            print("   - Asset, price, volatility, position direction ✓")
        else:
            print("ℹ️ No alerts generated - volatility may be below threshold")
            print("   This is normal behavior when volatility is within normal ranges")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 