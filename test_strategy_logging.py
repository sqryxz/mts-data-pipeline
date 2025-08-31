#!/usr/bin/env python3
"""
Test Strategy Logging Display
Demonstrates the strategy information that will be shown in system startup logs.
"""

import sys
import os
import logging

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.services.multi_strategy_generator import create_default_multi_strategy_generator
from config.settings import Config

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_strategy_logging():
    """Test the strategy logging functionality."""
    logger = setup_logging()
    
    logger.info("🎯 Strategy Configuration Check")
    logger.info("=" * 50)
    
    try:
        # Load configuration
        config = Config()
        logger.info("📊 Checking Strategy Registry...")
        
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Get strategy information
        strategies = list(generator.strategies.keys())
        strategy_weights = generator.aggregator_config.get('strategy_weights', {})
        
        logger.info(f"✅ Strategy Registry: {strategies}")
        logger.info(f"✅ Loaded Strategies: {strategies}")
        logger.info(f"📊 Strategy Weights: {strategy_weights}")
        
        # Display strategy information like in the enhanced scheduler
        logger.info("📊 Active Strategies:")
        
        strategy_descriptions = {
            'multibucketportfolio': '🎯 Multi-Bucket Portfolio (Cross-sectional momentum, residual analysis, mean-reversion)',
            'vixcorrelation': '📈 VIX Correlation (Market regime detection, volatility analysis)',
            'meanreversion': '🔄 Mean Reversion (Overextended moves, drawdown analysis)',
            'volatility': '📊 Volatility (Breakout detection, volatility regime analysis)',
            'ripple': '🌊 Ripple (Specialized XRP analysis, momentum detection)'
        }
        
        for strategy in strategies:
            weight = strategy_weights.get(strategy, 0.0)
            weight_pct = weight * 100
            description = strategy_descriptions.get(strategy, f'📋 {strategy.title()} Strategy')
            
            # Check Discord webhook status
            discord_status = "📢" if _has_discord_webhook(strategy) else "🔇"
            
            logger.info(f"    {discord_status} {strategy.title()}: {weight_pct:.1f}% weight - {description}")
        
        # Log aggregation configuration
        agg_config = generator.aggregator_config.get('aggregation_config', {})
        conflict_resolution = agg_config.get('conflict_resolution', 'weighted_average')
        max_position_size = agg_config.get('max_position_size', 0.10) * 100
        
        logger.info(f"🔧 Aggregation: {conflict_resolution} conflict resolution, {max_position_size:.1f}% max position size")
        
        # Check Discord integration
        logger.info("📢 Checking Discord Integration...")
        webhook_config_path = 'config/strategy_discord_webhooks.json'
        if os.path.exists(webhook_config_path):
            import json
            with open(webhook_config_path, 'r') as f:
                webhook_config = json.load(f)
            
            strategy_webhooks = webhook_config.get('strategy_webhooks', {})
            configured_strategies = list(strategy_webhooks.keys())
            
            logger.info(f"✅ Discord Webhooks: {len(configured_strategies)} strategies configured")
            for strategy in configured_strategies:
                config = strategy_webhooks[strategy]
                webhook_configured = "✅" if config.get('webhook_url') else "❌"
                min_confidence = config.get('min_confidence', 'Not set')
                enabled_assets = len(config.get('enabled_assets', []))
                logger.info(f"   {webhook_configured} {strategy}: confidence≥{min_confidence}, {enabled_assets} assets")
        
        # Display strategy summary
        logger.info("📋 Strategy Summary:")
        logger.info("   🎯 Multi-Bucket Portfolio: Cross-sectional momentum, residual analysis, mean-reversion")
        logger.info("   📈 VIX Correlation: Market regime detection and volatility analysis")
        logger.info("   🔄 Mean Reversion: Overextended moves and drawdown analysis")
        logger.info("   📊 Volatility: Breakout detection and volatility regime analysis")
        logger.info("   🌊 Ripple: Specialized XRP analysis and momentum detection")
        logger.info("   📢 Discord Alerts: Real-time notifications for all strategies")
        
        logger.info("✅ Strategy logging test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in strategy logging test: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")

def _has_discord_webhook(strategy_name: str) -> bool:
    """Check if a strategy has Discord webhook configured"""
    try:
        webhook_config_path = 'config/strategy_discord_webhooks.json'
        if os.path.exists(webhook_config_path):
            import json
            with open(webhook_config_path, 'r') as f:
                webhook_config = json.load(f)
            
            strategy_webhooks = webhook_config.get('strategy_webhooks', {})
            return strategy_name in strategy_webhooks and strategy_webhooks[strategy_name].get('webhook_url')
        
        return False
    except Exception:
        return False

if __name__ == "__main__":
    test_strategy_logging()
