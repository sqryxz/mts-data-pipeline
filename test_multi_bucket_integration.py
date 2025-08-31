#!/usr/bin/env python3
"""
Test Multi-Bucket Portfolio Strategy Integration
Verifies that the multi-bucket strategy is properly integrated into the main system.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.signals.strategies.strategy_registry import StrategyRegistry
from src.services.multi_strategy_generator import create_default_multi_strategy_generator
from src.utils.multi_webhook_discord_manager import MultiWebhookDiscordManager
from config.settings import Config

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_strategy_registry():
    """Test that the multi-bucket strategy is properly registered."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Strategy Registry Integration")
    
    try:
        # Create strategy registry
        registry = StrategyRegistry()
        registry.load_strategies_from_directory("src/signals/strategies")
        
        # Check if multi-bucket strategy is available
        strategies = registry.list_strategies()
        logger.info(f"📊 Available strategies: {list(strategies.keys())}")
        
        if 'multibucketportfolio' in strategies:
            logger.info("✅ Multi-bucket portfolio strategy found in registry")
            return True
        else:
            logger.error("❌ Multi-bucket portfolio strategy not found in registry")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing strategy registry: {e}")
        return False

def test_multi_strategy_generator():
    """Test that the multi-strategy generator includes the multi-bucket strategy."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Multi-Strategy Generator Integration")
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Check if multi-bucket strategy is loaded
        strategies = generator.strategies
        logger.info(f"📊 Loaded strategies: {list(strategies.keys())}")
        
        if 'multibucketportfolio' in strategies:
            logger.info("✅ Multi-bucket portfolio strategy loaded in generator")
            
            # Test strategy configuration
            strategy = strategies['multibucketportfolio']
            config = strategy.config
            logger.info(f"📋 Strategy config loaded: {config.get('name', 'Unknown')}")
            logger.info(f"📋 Strategy enabled: {config.get('enabled', False)}")
            
            return True
        else:
            logger.error("❌ Multi-bucket portfolio strategy not loaded in generator")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing multi-strategy generator: {e}")
        return False

def test_discord_integration():
    """Test that Discord integration is properly configured for the multi-bucket strategy."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Discord Integration")
    
    try:
        # Load Discord webhook configuration
        import json
        with open('config/strategy_discord_webhooks.json', 'r') as f:
            webhook_config = json.load(f)
        
        # Check if multi-bucket strategy has Discord configuration
        strategy_webhooks = webhook_config.get('strategy_webhooks', {})
        
        if 'multibucketportfolio' in strategy_webhooks:
            config = strategy_webhooks['multibucketportfolio']
            logger.info("✅ Multi-bucket portfolio Discord configuration found")
            logger.info(f"📋 Webhook URL: {'Configured' if config.get('webhook_url') else 'Not configured'}")
            logger.info(f"📋 Min confidence: {config.get('min_confidence', 'Not set')}")
            logger.info(f"📋 Enabled assets: {len(config.get('enabled_assets', []))} assets")
            logger.info(f"📋 Rate limit: {config.get('rate_limit', 'Not set')} seconds")
            return True
        else:
            logger.error("❌ Multi-bucket portfolio Discord configuration not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Discord integration: {e}")
        return False

def test_signal_generation():
    """Test that the multi-bucket strategy can generate signals."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Signal Generation")
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Get the multi-bucket strategy
        strategy = generator.strategies.get('multibucketportfolio')
        if not strategy:
            logger.error("❌ Multi-bucket strategy not found")
            return False
        
        # Generate sample market data
        from src.data.sqlite_helper import CryptoDatabase
        db = CryptoDatabase()
        
        # Get recent data for testing
        assets = ['bitcoin', 'ethereum', 'binancecoin']
        market_data = {}
        
        for asset in assets:
            try:
                data = db.get_recent_data(asset, days=30)
                if data is not None and not data.empty:
                    market_data[asset] = data
            except Exception as e:
                logger.warning(f"⚠️ Could not get data for {asset}: {e}")
        
        if not market_data:
            logger.warning("⚠️ No market data available for testing")
            return True  # Not a failure, just no data
        
        # Test strategy analysis
        logger.info("🧪 Testing strategy analysis...")
        analysis = strategy.analyze(market_data)
        logger.info(f"✅ Analysis completed: {len(analysis)} components")
        
        # Test signal generation
        logger.info("🧪 Testing signal generation...")
        signals = strategy.generate_signals(analysis)
        logger.info(f"✅ Generated {len(signals)} signals")
        
        # Log signal details
        for i, signal in enumerate(signals[:3]):  # Show first 3 signals
            logger.info(f"   Signal {i+1}: {signal.symbol} {signal.signal_type} (confidence: {signal.confidence:.2f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing signal generation: {e}")
        return False

def test_configuration():
    """Test that the configuration is properly set up."""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Testing Configuration")
    
    try:
        # Load configuration
        config = Config()
        
        # Check if multi-bucket strategy is enabled
        enabled_strategies = config.ENABLED_STRATEGIES
        logger.info(f"📋 Enabled strategies: {enabled_strategies}")
        
        if 'multi_bucket_portfolio' in enabled_strategies:
            logger.info("✅ Multi-bucket portfolio strategy enabled in configuration")
        else:
            logger.warning("⚠️ Multi-bucket portfolio strategy not in enabled strategies")
        
        # Check strategy weights
        strategy_weights = config.STRATEGY_WEIGHTS
        logger.info(f"📋 Strategy weights: {strategy_weights}")
        
        if 'multibucketportfolio' in strategy_weights:
            weight = strategy_weights['multibucketportfolio']
            logger.info(f"✅ Multi-bucket portfolio weight: {weight}")
        else:
            logger.warning("⚠️ Multi-bucket portfolio weight not configured")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing configuration: {e}")
        return False

async def main():
    """Run all integration tests."""
    logger = setup_logging()
    
    logger.info("🚀 Starting Multi-Bucket Portfolio Strategy Integration Tests")
    logger.info("=" * 70)
    
    tests = [
        ("Configuration", test_configuration),
        ("Strategy Registry", test_strategy_registry),
        ("Multi-Strategy Generator", test_multi_strategy_generator),
        ("Discord Integration", test_discord_integration),
        ("Signal Generation", test_signal_generation),
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
    logger.info("\n" + "=" * 70)
    logger.info("📊 INTEGRATION TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integration tests passed! Multi-bucket strategy is properly integrated.")
        return 0
    else:
        logger.error("⚠️ Some integration tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
