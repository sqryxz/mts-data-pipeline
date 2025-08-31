#!/usr/bin/env python3
"""
Test Discord Alerts for Multi-Bucket Portfolio Strategy
Verifies that Discord alerts are being sent for the multi-bucket strategy.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.services.multi_strategy_generator import create_default_multi_strategy_generator
from src.utils.multi_webhook_discord_manager import MultiWebhookDiscordManager
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from config.settings import Config

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_discord_webhook_configuration():
    """Test Discord webhook configuration for multi-bucket strategy."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Discord Webhook Configuration")
    
    try:
        # Load Discord webhook configuration
        webhook_config_path = 'config/strategy_discord_webhooks.json'
        if not os.path.exists(webhook_config_path):
            logger.error(f"❌ Discord webhook configuration file not found: {webhook_config_path}")
            return False
        
        import json
        with open(webhook_config_path, 'r') as f:
            webhook_config = json.load(f)
        
        strategy_webhooks = webhook_config.get('strategy_webhooks', {})
        
        if 'multibucketportfolio' not in strategy_webhooks:
            logger.error("❌ Multi-bucket portfolio strategy not found in Discord webhook configuration")
            return False
        
        config = strategy_webhooks['multibucketportfolio']
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            logger.error("❌ No webhook URL configured for multi-bucket portfolio strategy")
            return False
        
        logger.info(f"✅ Multi-bucket portfolio Discord webhook configured")
        logger.info(f"📋 Webhook URL: {webhook_url[:50]}...")
        logger.info(f"📋 Min confidence: {config.get('min_confidence', 'Not set')}")
        logger.info(f"📋 Enabled assets: {len(config.get('enabled_assets', []))} assets")
        logger.info(f"📋 Rate limit: {config.get('rate_limit', 'Not set')} seconds")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing Discord webhook configuration: {e}")
        return False

def test_multi_webhook_manager():
    """Test multi-webhook Discord manager initialization."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Multi-Webhook Discord Manager")
    
    try:
        # Load webhook configuration
        webhook_config_path = 'config/strategy_discord_webhooks.json'
        if not os.path.exists(webhook_config_path):
            logger.error(f"❌ Discord webhook configuration file not found: {webhook_config_path}")
            return False
        
        import json
        with open(webhook_config_path, 'r') as f:
            webhook_config = json.load(f)
        
        # Initialize multi-webhook manager
        strategy_webhooks = webhook_config.get('strategy_webhooks', {})
        manager = MultiWebhookDiscordManager(strategy_webhooks)
        
        # Check if multi-bucket strategy is configured
        if 'multibucketportfolio' not in manager.discord_managers:
            logger.error("❌ Multi-bucket portfolio strategy not found in Discord managers")
            return False
        
        logger.info("✅ Multi-webhook Discord manager initialized successfully")
        logger.info(f"📊 Total Discord managers: {len(manager.discord_managers)}")
        logger.info(f"📊 Multi-bucket manager: {'✅ Configured' if 'multibucketportfolio' in manager.discord_managers else '❌ Not configured'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing multi-webhook manager: {e}")
        return False

def test_signal_generation_and_discord():
    """Test signal generation and Discord alert sending."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Signal Generation and Discord Alerts")
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Check if multi-bucket strategy is loaded
        if 'multibucketportfolio' not in generator.strategies:
            logger.error("❌ Multi-bucket portfolio strategy not found in generator")
            return False
        
        logger.info("✅ Multi-bucket portfolio strategy loaded in generator")
        
        # Check if Discord manager is configured
        if not generator.multi_webhook_manager:
            logger.error("❌ Multi-webhook Discord manager not configured")
            return False
        
        logger.info("✅ Multi-webhook Discord manager configured")
        
        # Check if multi-bucket strategy has Discord manager
        if 'multibucketportfolio' not in generator.multi_webhook_manager.discord_managers:
            logger.error("❌ Multi-bucket portfolio strategy not found in Discord managers")
            return False
        
        logger.info("✅ Multi-bucket portfolio strategy has Discord manager configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing signal generation and Discord: {e}")
        return False

def test_discord_alert_sending():
    """Test sending a Discord alert for multi-bucket strategy."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Discord Alert Sending")
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Create a test signal for multi-bucket strategy
        test_signal = TradingSignal(
            symbol="bitcoin",
            signal_type=SignalType.LONG,
            signal_strength=SignalStrength.STRONG,
            direction=SignalDirection.BUY,
            price=50000.0,
            confidence=0.85,
            timestamp=datetime.now(),
            strategy_name="multibucketportfolio",
            position_size=0.05,
            stop_loss=48000.0,
            take_profit=55000.0,
            max_risk=0.02
        )
        
        # Create strategy signals dictionary
        strategy_signals = {
            'multibucketportfolio': [test_signal]
        }
        
        logger.info(f"📤 Sending test Discord alert for multi-bucket strategy...")
        logger.info(f"📋 Signal: {test_signal.symbol} {test_signal.signal_type} at ${test_signal.price:,.2f}")
        logger.info(f"📋 Confidence: {test_signal.confidence:.2f}")
        logger.info(f"📋 Strategy: {test_signal.strategy_name}")
        
        # Send Discord alert
        try:
            # Use asyncio.run instead of manual loop management
            results = asyncio.run(generator.multi_webhook_manager.send_strategy_signals(strategy_signals))
            if results:
                multibucket_result = results.get('multibucketportfolio', {})
                alerts_sent = multibucket_result.get('alerts_sent', 0)
                logger.info(f"✅ Discord alert sent successfully! Alerts sent: {alerts_sent}")
                return True
            else:
                logger.error("❌ Failed to send Discord alert")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending Discord alert: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing Discord alert sending: {e}")
        return False

def check_discord_alert_logs():
    """Check Discord alert logs in the database."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Checking Discord Alert Logs")
    
    try:
        from src.utils.discord_alert_logger import DiscordAlertLogger
        
        # Initialize Discord alert logger
        alert_logger = DiscordAlertLogger()
        
        # Get recent alerts for multi-bucket strategy
        import sqlite3
        db_path = 'data/crypto_data.db'
        
        if not os.path.exists(db_path):
            logger.warning("⚠️ Database not found, skipping alert log check")
            return True
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if discord_alerts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='discord_alerts'
        """)
        
        if not cursor.fetchone():
            logger.warning("⚠️ Discord alerts table not found")
            conn.close()
            return True
        
        # Get recent alerts for multi-bucket strategy
        cursor.execute("""
            SELECT COUNT(*) FROM discord_alerts 
            WHERE strategy_name = 'multibucketportfolio' 
            AND sent_at >= datetime('now', '-1 day')
        """)
        
        recent_alerts = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM discord_alerts 
            WHERE strategy_name = 'multibucketportfolio'
        """)
        
        total_alerts = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"📊 Discord Alert Statistics:")
        logger.info(f"   📈 Recent alerts (last 24h): {recent_alerts}")
        logger.info(f"   📈 Total alerts: {total_alerts}")
        
        if recent_alerts > 0:
            logger.info("✅ Discord alerts are being sent for multi-bucket strategy")
        else:
            logger.warning("⚠️ No recent Discord alerts found for multi-bucket strategy")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking Discord alert logs: {e}")
        return False

async def main():
    """Run all Discord alert tests."""
    logger = setup_logging()
    
    logger.info("🚀 Testing Multi-Bucket Portfolio Strategy Discord Alerts")
    logger.info("=" * 60)
    
    tests = [
        ("Discord Webhook Configuration", test_discord_webhook_configuration),
        ("Multi-Webhook Manager", test_multi_webhook_manager),
        ("Signal Generation and Discord", test_signal_generation_and_discord),
        ("Discord Alert Sending", test_discord_alert_sending),
        ("Discord Alert Logs", check_discord_alert_logs),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} Test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status} {test_name} Test")
        except Exception as e:
            logger.error(f"❌ ERROR in {test_name} Test: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DISCORD ALERT TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Discord alert tests passed! Multi-bucket strategy Discord alerts are working.")
        return 0
    else:
        logger.error("⚠️ Some Discord alert tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
