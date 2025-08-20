#!/usr/bin/env python3
"""
Test Correlation Discord Integration
Tests the Discord webhook functionality for correlation analysis alerts.
"""

import sys
import os
import json
from datetime import datetime

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_discord_config():
    """Test Discord configuration loading."""
    print("🔧 Testing Discord Configuration")
    print("=" * 50)
    
    config_path = "config/correlation_analysis/discord_config.json"
    
    if not os.path.exists(config_path):
        print(f"❌ Discord config file not found: {config_path}")
        print("💡 Create the config file with your Discord webhook URL")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        webhook_url = config.get('discord_webhook_url', '')
        
        if not webhook_url:
            print("❌ No Discord webhook URL configured")
            print("💡 Add your Discord webhook URL to the config file")
            return False
        
        print(f"✅ Discord webhook URL configured: {webhook_url[:20]}...")
        print(f"✅ Mosaic alerts enabled: {config.get('enabled_alerts', {}).get('mosaic_alerts', False)}")
        print(f"✅ Breakdown alerts enabled: {config.get('enabled_alerts', {}).get('correlation_breakdowns', False)}")
        print(f"✅ Daily summaries enabled: {config.get('enabled_alerts', {}).get('daily_summaries', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading Discord config: {e}")
        return False

def test_discord_integration():
    """Test Discord integration module."""
    print("\n🔗 Testing Discord Integration Module")
    print("=" * 50)
    
    try:
        from src.correlation_analysis.alerts.discord_integration import CorrelationDiscordIntegration
        
        # Test with sample config
        config = {
            'discord_webhook_url': 'https://discord.com/api/webhooks/test/test',
            'enabled_alerts': {
                'mosaic_alerts': True,
                'correlation_breakdowns': True,
                'daily_summaries': True
            }
        }
        
        discord_integration = CorrelationDiscordIntegration(config=config)
        
        if discord_integration.discord:
            print("✅ Discord integration initialized successfully")
        else:
            print("❌ Discord integration failed to initialize")
            return False
        
        # Test embed creation
        sample_mosaic_data = {
            'correlation_matrix': {
                'summary': {
                    'total_pairs': 22,
                    'significant_correlations': 15,
                    'average_correlation_strength': 0.45,
                    'strong_correlations': 8
                }
            },
            'key_findings': [
                'Strong correlation detected between BTC and ETH',
                'ENA shows low correlation with major assets',
                'Market volatility increased in the last 24 hours'
            ],
            'recommendations': [
                'Consider hedging BTC/ETH positions',
                'ENA provides good diversification opportunity',
                'Monitor volatility levels closely'
            ],
            'market_insights': [
                'Low correlation environment suggests good diversification',
                'Found 3 negative correlations - potential hedging opportunities',
                'Strongest correlations: BTC_ETH (30d: 0.823)'
            ]
        }
        
        embed = discord_integration._create_mosaic_embed(sample_mosaic_data)
        
        if embed and 'title' in embed:
            print("✅ Mosaic embed creation successful")
            print(f"   Title: {embed['title']}")
            print(f"   Fields: {len(embed.get('fields', []))}")
        else:
            print("❌ Mosaic embed creation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Discord integration: {e}")
        return False

def test_mosaic_alert_system():
    """Test mosaic alert system with Discord integration."""
    print("\n🎨 Testing Mosaic Alert System")
    print("=" * 50)
    
    try:
        from src.correlation_analysis.alerts.mosaic_alert_system import MosaicAlertSystem
        
        # Load Discord config
        config_path = "config/correlation_analysis/discord_config.json"
        discord_config = None
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                discord_config = json.load(f)
        
        # Initialize mosaic alert system
        alert_system = MosaicAlertSystem(discord_config=discord_config)
        
        if alert_system.discord_integration.discord:
            print("✅ Mosaic alert system initialized with Discord integration")
        else:
            print("⚠️ Mosaic alert system initialized without Discord integration")
        
        # Test daily mosaic alert generation
        print("📊 Testing daily mosaic alert generation...")
        alert_path = alert_system.generate_daily_mosaic_alert(force_regeneration=True)
        
        if alert_path:
            print(f"✅ Daily mosaic alert generated: {alert_path}")
            
            # Check if Discord alert was sent
            if alert_system.discord_integration.discord:
                print("✅ Discord alert should have been sent (check your Discord channel)")
            else:
                print("⚠️ Discord alert not sent (no webhook configured)")
        else:
            print("❌ Failed to generate daily mosaic alert")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing mosaic alert system: {e}")
        return False

def test_correlation_monitor():
    """Test correlation monitor with Discord integration."""
    print("\n📊 Testing Correlation Monitor")
    print("=" * 50)
    
    try:
        from src.correlation_analysis.core.correlation_monitor import CorrelationMonitor
        
        # Load Discord config
        config_path = "config/correlation_analysis/discord_config.json"
        discord_config = None
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                discord_config = json.load(f)
        
        # Create monitor config with Discord integration
        monitor_config = {
            'correlation_windows': [7, 14, 30],
            'min_data_points': 20,
            'z_score_threshold': 2.0,
            'monitoring_interval_minutes': 15,
            'data_lookback_days': 60,
            'alert_on_breakout': True,
            'store_correlation_history': True,
            'store_breakout_history': True
        }
        
        if discord_config:
            monitor_config['discord_config'] = discord_config
        
        # Initialize correlation monitor
        monitor = CorrelationMonitor('BTC_ETH', monitor_config)
        
        if monitor.discord_integration.discord:
            print("✅ Correlation monitor initialized with Discord integration")
        else:
            print("⚠️ Correlation monitor initialized without Discord integration")
        
        print("✅ Correlation monitor test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing correlation monitor: {e}")
        return False

def main():
    """Run all Discord integration tests."""
    print("🚀 Correlation Discord Integration Test Suite")
    print("=" * 60)
    print(f"⏰ Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Discord Configuration", test_discord_config),
        ("Discord Integration Module", test_discord_integration),
        ("Mosaic Alert System", test_mosaic_alert_system),
        ("Correlation Monitor", test_correlation_monitor)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Discord integration is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Add your Discord webhook URL to config/correlation_analysis/discord_config.json")
        print("   2. Run the correlation analysis system")
        print("   3. Check your Discord channel for alerts")
    else:
        print("⚠️ Some tests failed. Check the configuration and try again.")
        print("\n💡 To enable Discord alerts:")
        print("   1. Create a Discord webhook in your server")
        print("   2. Add the webhook URL to config/correlation_analysis/discord_config.json")
        print("   3. Restart the correlation analysis system")

if __name__ == "__main__":
    main()
