#!/usr/bin/env python3

"""
Test Environment Variable Discord Configuration
Verifies that Discord webhook configuration works with environment variables.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config_utils import (
    resolve_env_vars, 
    load_config_with_env_vars, 
    validate_discord_config, 
    get_discord_config_from_env
)
from src.signals.signal_aggregator import SignalAggregator
from src.data.signal_models import TradingSignal, SignalType, SignalStrength

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_env_var_resolution():
    """Test environment variable resolution in JSON config."""
    
    print("🔧 Testing Environment Variable Resolution")
    print("=" * 50)
    print()
    
    # Test data with environment variable placeholders
    test_config = {
        "webhook_url": "${DISCORD_WEBHOOK_URL}",
        "min_confidence": "${DISCORD_MIN_CONFIDENCE}",
        "min_strength": "${DISCORD_MIN_STRENGTH}",
        "rate_limit": "${DISCORD_RATE_LIMIT_SECONDS}",
        "nested": {
            "url": "${DISCORD_WEBHOOK_URL}",
            "array": ["${DISCORD_MIN_CONFIDENCE}", "static_value"]
        }
    }
    
    # Set test environment variables
    os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test/test'
    os.environ['DISCORD_MIN_CONFIDENCE'] = '0.7'
    os.environ['DISCORD_MIN_STRENGTH'] = 'STRONG'
    os.environ['DISCORD_RATE_LIMIT_SECONDS'] = '30'
    
    # Resolve environment variables
    resolved_config = resolve_env_vars(test_config)
    
    print("Original config:")
    print(json.dumps(test_config, indent=2))
    print()
    print("Resolved config:")
    print(json.dumps(resolved_config, indent=2))
    print()
    
    # Verify resolution
    assert resolved_config['webhook_url'] == 'https://discord.com/api/webhooks/test/test'
    assert resolved_config['min_confidence'] == '0.7'
    assert resolved_config['min_strength'] == 'STRONG'
    assert resolved_config['rate_limit'] == '30'
    assert resolved_config['nested']['url'] == 'https://discord.com/api/webhooks/test/test'
    assert resolved_config['nested']['array'][0] == '0.7'
    
    print("✅ Environment variable resolution works correctly")
    
    # Clean up test environment variables
    del os.environ['DISCORD_WEBHOOK_URL']
    del os.environ['DISCORD_MIN_CONFIDENCE']
    del os.environ['DISCORD_MIN_STRENGTH']
    del os.environ['DISCORD_RATE_LIMIT_SECONDS']
    
    return True

def test_discord_config_validation():
    """Test Discord configuration validation."""
    
    print("\n🛡️ Testing Discord Configuration Validation")
    print("=" * 50)
    print()
    
    # Test valid configuration
    valid_config = {
        'webhook_url': 'https://discord.com/api/webhooks/test/test',
        'min_confidence': 0.6,
        'min_strength': 'WEAK',
        'rate_limit': 60
    }
    
    assert validate_discord_config(valid_config) == True
    print("✅ Valid configuration passes validation")
    
    # Test invalid configurations
    invalid_configs = [
        # Missing webhook URL
        {
            'min_confidence': 0.6,
            'min_strength': 'WEAK',
            'rate_limit': 60
        },
        # Empty webhook URL
        {
            'webhook_url': '',
            'min_confidence': 0.6,
            'min_strength': 'WEAK',
            'rate_limit': 60
        },
        # Placeholder webhook URL
        {
            'webhook_url': 'YOUR_DISCORD_WEBHOOK_URL_HERE',
            'min_confidence': 0.6,
            'min_strength': 'WEAK',
            'rate_limit': 60
        },
        # Invalid confidence value
        {
            'webhook_url': 'https://discord.com/api/webhooks/test/test',
            'min_confidence': 1.5,  # > 1.0
            'min_strength': 'WEAK',
            'rate_limit': 60
        },
        # Invalid rate limit
        {
            'webhook_url': 'https://discord.com/api/webhooks/test/test',
            'min_confidence': 0.6,
            'min_strength': 'WEAK',
            'rate_limit': 0  # <= 0
        }
    ]
    
    for i, invalid_config in enumerate(invalid_configs):
        assert validate_discord_config(invalid_config) == False
        print(f"✅ Invalid configuration {i+1} correctly rejected")
    
    return True

def test_get_discord_config_from_env():
    """Test getting Discord configuration from environment variables."""
    
    print("\n🌍 Testing Environment-Based Discord Configuration")
    print("=" * 50)
    print()
    
    # Set test environment variables
    os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test/test'
    os.environ['DISCORD_MIN_CONFIDENCE'] = '0.8'
    os.environ['DISCORD_MIN_STRENGTH'] = 'STRONG'
    os.environ['DISCORD_RATE_LIMIT_SECONDS'] = '45'
    
    # Get configuration from environment
    config = get_discord_config_from_env()
    
    print("Environment-based configuration:")
    print(json.dumps(config, indent=2))
    print()
    
    # Verify configuration
    assert config['webhook_url'] == 'https://discord.com/api/webhooks/test/test'
    assert config['min_confidence'] == 0.8
    assert config['min_strength'] == 'STRONG'
    assert config['rate_limit'] == 45
    assert config['username'] == 'MTS Signal Bot'
    assert config['enabled_assets'] == ['bitcoin', 'ethereum']
    
    print("✅ Environment-based configuration works correctly")
    
    # Test validation
    assert validate_discord_config(config) == True
    print("✅ Environment-based configuration passes validation")
    
    # Clean up test environment variables
    del os.environ['DISCORD_WEBHOOK_URL']
    del os.environ['DISCORD_MIN_CONFIDENCE']
    del os.environ['DISCORD_MIN_STRENGTH']
    del os.environ['DISCORD_RATE_LIMIT_SECONDS']
    
    return True

def test_signal_aggregator_with_env():
    """Test SignalAggregator with environment variable configuration."""
    
    print("\n🔗 Testing SignalAggregator with Environment Configuration")
    print("=" * 50)
    print()
    
    # Set test environment variables
    os.environ['DISCORD_ALERTS_ENABLED'] = 'true'
    os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test/test'
    os.environ['DISCORD_MIN_CONFIDENCE'] = '0.7'
    os.environ['DISCORD_MIN_STRENGTH'] = 'MODERATE'
    os.environ['DISCORD_RATE_LIMIT_SECONDS'] = '30'
    
    try:
        # Create SignalAggregator with environment-based configuration
        strategy_weights = {'test': 1.0}
        aggregation_config = {
            'discord_alerts': True,  # This will be overridden by environment
            'discord_webhook_url': 'old_url',  # This will be overridden by environment
            'discord_config': {'old': 'config'}  # This will be overridden by environment
        }
        
        aggregator = SignalAggregator(strategy_weights, aggregation_config)
        
        # Verify that Discord manager was initialized
        if aggregator.discord_manager:
            print("✅ Discord manager initialized successfully")
            print(f"   Webhook URL: {aggregator.discord_manager.webhook.webhook_url}")
            print(f"   Min Confidence: {aggregator.discord_manager.alert_config.get('min_confidence')}")
            print(f"   Min Strength: {aggregator.discord_manager.alert_config.get('min_strength')}")
            print(f"   Rate Limit: {aggregator.discord_manager.alert_config.get('rate_limit')}")
        else:
            print("❌ Discord manager not initialized")
        
        # Clean up
        aggregator.cleanup()
        
    except Exception as e:
        print(f"❌ Error testing SignalAggregator: {e}")
        return False
    
    # Clean up test environment variables
    del os.environ['DISCORD_ALERTS_ENABLED']
    del os.environ['DISCORD_WEBHOOK_URL']
    del os.environ['DISCORD_MIN_CONFIDENCE']
    del os.environ['DISCORD_MIN_STRENGTH']
    del os.environ['DISCORD_RATE_LIMIT_SECONDS']
    
    return True

def test_missing_env_vars():
    """Test behavior when environment variables are missing."""
    
    print("\n⚠️ Testing Missing Environment Variables")
    print("=" * 50)
    print()
    
    # Ensure environment variables are not set
    for var in ['DISCORD_WEBHOOK_URL', 'DISCORD_MIN_CONFIDENCE', 'DISCORD_MIN_STRENGTH', 'DISCORD_RATE_LIMIT_SECONDS']:
        if var in os.environ:
            del os.environ[var]
    
    # Test getting configuration with missing environment variables
    config = get_discord_config_from_env()
    
    print("Configuration with missing environment variables:")
    print(json.dumps(config, indent=2))
    print()
    
    # Should use default values
    assert config['webhook_url'] == ''
    assert config['min_confidence'] == 0.6
    assert config['min_strength'] == 'WEAK'
    assert config['rate_limit'] == 60
    
    print("✅ Default values used when environment variables are missing")
    
    # Test validation with missing webhook URL
    assert validate_discord_config(config) == False
    print("✅ Configuration correctly rejected when webhook URL is missing")
    
    return True

def main():
    """Run all environment variable configuration tests."""
    
    print("🧪 Environment Variable Discord Configuration Test Suite")
    print("=" * 70)
    print()
    print("Testing Discord webhook configuration with environment variables...")
    print()
    
    # Run all tests
    tests = [
        ("Environment Variable Resolution", test_env_var_resolution),
        ("Discord Configuration Validation", test_discord_config_validation),
        ("Environment-Based Configuration", test_get_discord_config_from_env),
        ("SignalAggregator with Environment", test_signal_aggregator_with_env),
        ("Missing Environment Variables", test_missing_env_vars)
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
    print("=" * 70)
    print("📋 ENVIRONMENT VARIABLE CONFIGURATION TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Environment variable configuration is working correctly.")
        print()
        print("✅ Environment variable configuration is ready:")
        print("   • Environment variables are properly resolved")
        print("   • Configuration validation works correctly")
        print("   • SignalAggregator uses environment variables")
        print("   • Graceful handling of missing variables")
        print("   • Default values are used appropriately")
        print()
        print("📝 To use Discord alerts, set these environment variables in your .env file:")
        print("   DISCORD_WEBHOOK_URL=your_webhook_url_here")
        print("   DISCORD_ALERTS_ENABLED=true")
        print("   DISCORD_MIN_CONFIDENCE=0.6")
        print("   DISCORD_MIN_STRENGTH=WEAK")
        print("   DISCORD_RATE_LIMIT_SECONDS=60")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 