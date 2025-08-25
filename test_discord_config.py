#!/usr/bin/env python3
"""
Test Discord configuration to identify username issues
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_discord_configs():
    print("🔍 Testing Discord Configurations")
    print("=" * 50)
    
    # Test 1: Environment variables
    print("1️⃣ Environment Variables:")
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    print(f"   Webhook URL: {'✅ Set' if webhook_url else '❌ Not set'}")
    if webhook_url:
        print(f"   URL: {webhook_url[:50]}...")
    print()
    
    # Test 2: Main Discord config
    print("2️⃣ Main Discord Config (config/discord_alerts.json):")
    try:
        with open('config/discord_alerts.json', 'r') as f:
            config = json.load(f)
        print(f"   Username: {config.get('username', 'Not set')}")
        print(f"   Webhook URL: {config.get('webhook_url', 'Not set')}")
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
    print()
    
    # Test 3: Strategy Discord config
    print("3️⃣ Strategy Discord Config (config/strategy_discord_webhooks.json):")
    try:
        with open('config/strategy_discord_webhooks.json', 'r') as f:
            config = json.load(f)
        print(f"   Fallback webhook: {config.get('fallback_webhook', {}).get('webhook_url', 'Not set')[:50]}...")
        for strategy, cfg in config.get('strategy_webhooks', {}).items():
            print(f"   {strategy}: {cfg.get('webhook_url', 'Not set')[:50]}...")
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
    print()
    
    # Test 4: Correlation Discord config
    print("4️⃣ Correlation Discord Config (config/correlation_analysis/discord_config.json):")
    try:
        with open('config/correlation_analysis/discord_config.json', 'r') as f:
            config = json.load(f)
        print(f"   Webhook URL: {config.get('discord_webhook_url', 'Not set')[:50]}...")
        print(f"   Enabled alerts: {config.get('enabled_alerts', {})}")
    except Exception as e:
        print(f"   ❌ Error reading config: {e}")
    print()
    
    # Test 5: Check for any other Discord configs
    print("5️⃣ Other Discord Configurations:")
    discord_files = list(Path('.').rglob('*discord*.json')) + list(Path('.').rglob('*Discord*.json'))
    for file_path in discord_files:
        if 'node_modules' not in str(file_path) and '.git' not in str(file_path):
            print(f"   Found: {file_path}")
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                if 'username' in config:
                    print(f"     Username: {config['username']}")
                if 'webhook_url' in config or 'discord_webhook_url' in config:
                    url = config.get('webhook_url') or config.get('discord_webhook_url')
                    print(f"     Webhook: {url[:50]}..." if url else "     Webhook: Not set")
            except Exception as e:
                print(f"     ❌ Error reading: {e}")
    print()
    
    # Test 6: Check for any running processes that might be sending Discord alerts
    print("6️⃣ Running Discord-Related Processes:")
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        discord_processes = [line for line in lines if 'discord' in line.lower() or 'correlation' in line.lower()]
        for process in discord_processes[:5]:  # Show first 5
            print(f"   {process}")
    except Exception as e:
        print(f"   ❌ Error checking processes: {e}")
    print()

if __name__ == "__main__":
    test_discord_configs()
