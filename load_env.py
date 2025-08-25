#!/usr/bin/env python3
"""
Test environment variable loading
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    print("🔧 Testing Environment Variable Loading")
    print("=" * 50)
    
    # Method 1: Direct from .env file
    print("Method 1: Direct from .env file")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    print(f"   {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
    else:
        print("   ❌ .env file not found")
    print()
    
    # Method 2: Using python-dotenv
    print("Method 2: Using python-dotenv")
    try:
        load_dotenv()
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        alerts_enabled = os.getenv('DISCORD_ALERTS_ENABLED')
        min_confidence = os.getenv('DISCORD_MIN_CONFIDENCE')
        min_strength = os.getenv('DISCORD_MIN_STRENGTH')
        rate_limit = os.getenv('DISCORD_RATE_LIMIT_SECONDS')
        
        print(f"   Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
        print(f"   Alerts Enabled: {alerts_enabled}")
        print(f"   Min Confidence: {min_confidence}")
        print(f"   Min Strength: {min_strength}")
        print(f"   Rate Limit: {rate_limit}")
    except ImportError:
        print("   ❌ python-dotenv not installed")
    print()
    
    # Method 3: Manual loading
    print("Method 3: Manual loading")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        alerts_enabled = os.getenv('DISCORD_ALERTS_ENABLED')
        min_confidence = os.getenv('DISCORD_MIN_CONFIDENCE')
        min_strength = os.getenv('DISCORD_MIN_STRENGTH')
        rate_limit = os.getenv('DISCORD_RATE_LIMIT_SECONDS')
        
        print(f"   Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
        print(f"   Alerts Enabled: {alerts_enabled}")
        print(f"   Min Confidence: {min_confidence}")
        print(f"   Min Strength: {min_strength}")
        print(f"   Rate Limit: {rate_limit}")
    else:
        print("   ❌ .env file not found")

if __name__ == "__main__":
    test_env_loading()
