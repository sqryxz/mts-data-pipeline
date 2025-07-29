#!/usr/bin/env python3

"""
Discord Alerts Demonstration
Shows how Discord webhook integration works with signal alerts.
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signals.strategies.volatility_strategy import VolatilityStrategy
from src.data.sqlite_helper import CryptoDatabase
from src.utils.discord_webhook import DiscordWebhook, DiscordAlertManager
from src.signals.signal_aggregator import SignalAggregator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_discord_config():
    """Load Discord configuration from file."""
    config_path = "config/discord_alerts.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check if webhook URL is configured
        if config.get('webhook_url') == 'YOUR_DISCORD_WEBHOOK_URL_HERE':
            print("⚠️  Discord webhook URL not configured!")
            print("Please update config/discord_alerts.json with your Discord webhook URL")
            return None
        
        return config
        
    except FileNotFoundError:
        print(f"❌ Discord config file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in Discord config: {e}")
        return None

async def test_discord_webhook():
    """Test basic Discord webhook functionality."""
    
    print("🔗 Testing Discord Webhook Integration")
    print("=" * 50)
    print()
    
    config = load_discord_config()
    if not config:
        print("❌ Cannot test Discord webhook without configuration")
        return False
    
    try:
        # Initialize Discord webhook
        webhook = DiscordWebhook(config['webhook_url'], config)
        
        print("📡 Sending test message to Discord...")
        success = await webhook.send_test_message()
        
        if success:
            print("✅ Test message sent successfully!")
            print("Check your Discord channel for the test message.")
        else:
            print("❌ Failed to send test message")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing Discord webhook: {e}")
        return False

async def test_discord_alert_manager():
    """Test Discord alert manager with filtering."""
    
    print("\n🎯 Testing Discord Alert Manager")
    print("=" * 50)
    print()
    
    config = load_discord_config()
    if not config:
        print("❌ Cannot test Discord alert manager without configuration")
        return False
    
    try:
        # Initialize alert manager
        alert_manager = DiscordAlertManager(config['webhook_url'], config)
        
        print("📡 Sending test alert...")
        success = await alert_manager.send_test_alert()
        
        if success:
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Failed to send test alert")
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing Discord alert manager: {e}")
        return False

async def test_signal_aggregator_with_discord():
    """Test signal aggregator with Discord alerts enabled."""
    
    print("\n🔄 Testing Signal Aggregator with Discord Alerts")
    print("=" * 60)
    print()
    
    config = load_discord_config()
    if not config:
        print("❌ Cannot test with Discord alerts without configuration")
        return False
    
    try:
        # Configure signal aggregator with Discord alerts
        strategy_weights = {'volatility': 1.0}
        aggregation_config = {
            'discord_alerts': True,
            'discord_webhook_url': config['webhook_url'],
            'discord_config': config
        }
        
        # Initialize signal aggregator
        aggregator = SignalAggregator(strategy_weights, aggregation_config)
        
        print("📊 Generating signals with Discord alerts...")
        
        # Generate some test signals
        from src.data.signal_models import TradingSignal, SignalType, SignalStrength
        
        test_signals = [
            TradingSignal(
                asset="bitcoin",
                signal_type=SignalType.LONG,
                timestamp=int(datetime.now().timestamp() * 1000),
                price=50000.0,
                strategy_name="VolatilityStrategy",
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
                    'reason': 'Volatility breakout detected'
                }
            ),
            TradingSignal(
                asset="ethereum",
                signal_type=SignalType.SHORT,
                timestamp=int(datetime.now().timestamp() * 1000),
                price=3000.0,
                strategy_name="VolatilityStrategy",
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
                    'reason': 'Extreme volatility detected'
                }
            )
        ]
        
        # Process signals through aggregator
        strategy_signals = {'volatility': test_signals}
        aggregated_signals = aggregator.aggregate_signals(strategy_signals)
        
        print(f"✅ Generated {len(aggregated_signals)} aggregated signals")
        print("📡 Discord alerts should be sent automatically...")
        
        # Wait a moment for async Discord alerts to process
        await asyncio.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing signal aggregator with Discord: {e}")
        return False

async def test_real_signals_with_discord():
    """Test Discord alerts with real signals from volatility strategy."""
    
    print("\n🚀 Testing Real Signals with Discord Alerts")
    print("=" * 60)
    print()
    
    config = load_discord_config()
    if not config:
        print("❌ Cannot test with Discord alerts without configuration")
        return False
    
    try:
        # Initialize volatility strategy
        strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
        database = CryptoDatabase()
        
        # Get market data
        market_data = database.get_strategy_market_data(['bitcoin', 'ethereum'], 30)
        
        # Generate signals
        analysis_results = strategy.analyze(market_data)
        signals = strategy.generate_signals(analysis_results)
        
        if not signals:
            print("❌ No signals generated for Discord testing")
            return False
        
        print(f"📊 Generated {len(signals)} real signals")
        
        # Configure signal aggregator with Discord alerts
        strategy_weights = {'volatility': 1.0}
        aggregation_config = {
            'discord_alerts': True,
            'discord_webhook_url': config['webhook_url'],
            'discord_config': config
        }
        
        aggregator = SignalAggregator(strategy_weights, aggregation_config)
        
        # Process signals through aggregator (this will trigger Discord alerts)
        strategy_signals = {'volatility': signals}
        aggregated_signals = aggregator.aggregate_signals(strategy_signals)
        
        print(f"✅ Processed {len(aggregated_signals)} signals through aggregator")
        print("📡 Real Discord alerts should be sent...")
        
        # Wait for async Discord alerts
        await asyncio.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing real signals with Discord: {e}")
        return False

def show_discord_config_help():
    """Show help for configuring Discord alerts."""
    
    print("\n📋 Discord Configuration Help")
    print("=" * 40)
    print()
    print("To enable Discord alerts, you need to:")
    print()
    print("1. Create a Discord webhook:")
    print("   • Go to your Discord server")
    print("   • Right-click on the channel you want alerts in")
    print("   • Select 'Edit Channel' → 'Integrations' → 'Webhooks'")
    print("   • Click 'New Webhook' and copy the webhook URL")
    print()
    print("2. Update the configuration:")
    print("   • Edit config/discord_alerts.json")
    print("   • Replace 'YOUR_DISCORD_WEBHOOK_URL_HERE' with your webhook URL")
    print()
    print("3. Configure alert settings:")
    print("   • min_confidence: Minimum confidence for alerts (default: 0.6)")
    print("   • min_strength: Minimum signal strength (WEAK/MODERATE/STRONG)")
    print("   • enabled_assets: Which assets to send alerts for")
    print("   • rate_limit: Seconds between alerts per asset (default: 60)")
    print()
    print("4. Test the integration:")
    print("   • Run this script to test Discord alerts")
    print("   • Check your Discord channel for test messages")
    print()

async def main():
    """Main demonstration function."""
    
    print("🎯 Discord Alerts Integration Demo")
    print("=" * 50)
    print()
    print("This demonstration shows Discord webhook integration")
    print("for sending trading signal alerts to Discord channels.")
    print()
    
    # Check if Discord is configured
    config = load_discord_config()
    if not config:
        show_discord_config_help()
        return
    
    # Test 1: Basic webhook functionality
    print("Test 1: Basic Discord Webhook")
    print("-" * 30)
    webhook_success = await test_discord_webhook()
    
    # Test 2: Alert manager
    print("\nTest 2: Discord Alert Manager")
    print("-" * 30)
    manager_success = await test_discord_alert_manager()
    
    # Test 3: Signal aggregator integration
    print("\nTest 3: Signal Aggregator Integration")
    print("-" * 30)
    aggregator_success = await test_signal_aggregator_with_discord()
    
    # Test 4: Real signals
    print("\nTest 4: Real Signals with Discord")
    print("-" * 30)
    real_signals_success = await test_real_signals_with_discord()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DISCORD ALERTS DEMO SUMMARY")
    print("=" * 50)
    print(f"✅ Webhook Test: {'Passed' if webhook_success else 'Failed'}")
    print(f"✅ Alert Manager: {'Passed' if manager_success else 'Failed'}")
    print(f"✅ Aggregator Integration: {'Passed' if aggregator_success else 'Failed'}")
    print(f"✅ Real Signals: {'Passed' if real_signals_success else 'Failed'}")
    print()
    
    if all([webhook_success, manager_success, aggregator_success, real_signals_success]):
        print("🎉 All Discord alert tests passed!")
        print()
        print("Discord alerts are now integrated with your MTS Pipeline!")
        print("• Signals will be automatically sent to Discord")
        print("• Rich embeds with signal details and risk metrics")
        print("• Configurable filtering and rate limiting")
        print("• Error handling and retry logic")
    else:
        print("⚠️  Some tests failed. Check the configuration and try again.")
        show_discord_config_help()

if __name__ == "__main__":
    asyncio.run(main()) 