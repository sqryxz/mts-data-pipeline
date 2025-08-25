#!/usr/bin/env python3
"""
Test Config class environment variable loading
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loading():
    print("🔧 Testing Config Class Environment Variable Loading")
    print("=" * 60)
    
    # Test 1: Direct environment variable access
    print("Test 1: Direct environment variable access")
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    alerts_enabled = os.getenv('DISCORD_ALERTS_ENABLED')
    print(f"   Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
    print(f"   Alerts Enabled: {alerts_enabled}")
    print()
    
    # Test 2: Config class loading
    print("Test 2: Config class loading")
    try:
        from config.settings import Config
        config = Config()
        
        print(f"   Config loaded successfully")
        print(f"   Environment: {config.ENVIRONMENT.value}")
        print(f"   Discord Webhook URL: {'✅ Set' if config.DISCORD_WEBHOOK_URL else '❌ Not set'}")
        print(f"   Discord Alerts Enabled: {config.DISCORD_ALERTS_ENABLED}")
        print(f"   Discord Min Confidence: {config.DISCORD_MIN_CONFIDENCE}")
        print(f"   Discord Min Strength: {config.DISCORD_MIN_STRENGTH}")
        print(f"   Discord Rate Limit: {config.DISCORD_RATE_LIMIT_SECONDS}")
        
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
    print()
    
    # Test 3: Signal aggregator configuration
    print("Test 3: Signal aggregator configuration")
    try:
        from src.utils.config_utils import get_discord_config_from_env
        discord_config = get_discord_config_from_env()
        
        print(f"   Discord config loaded successfully")
        print(f"   Webhook URL: {'✅ Set' if discord_config.get('webhook_url') else '❌ Not set'}")
        print(f"   Min Confidence: {discord_config.get('min_confidence')}")
        print(f"   Min Strength: {discord_config.get('min_strength')}")
        print(f"   Rate Limit: {discord_config.get('rate_limit')}")
        
    except Exception as e:
        print(f"   ❌ Discord config loading failed: {e}")
    print()

if __name__ == "__main__":
    test_config_loading()
