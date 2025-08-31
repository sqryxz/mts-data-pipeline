#!/usr/bin/env python3
"""
Test Aggregated Signal Discord Alert
Tests that Discord alerts for aggregated signals show contributing strategies.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.utils.discord_webhook import DiscordWebhook

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

async def test_aggregated_signal_discord():
    """Test Discord alert for aggregated signal with contributing strategies."""
    logger = setup_logging()
    
    logger.info("🚀 Testing Aggregated Signal Discord Alert")
    logger.info("=" * 60)
    
    try:
        # Create a test aggregated signal with contributing strategies
        aggregated_analysis = {
            'aggregation_method': 'weighted_average',
            'strategies_combined': ['multibucketportfolio', 'vixcorrelation', 'meanreversion'],
            'strategy_weights': {
                'multibucketportfolio': 0.2,
                'vixcorrelation': 0.25,
                'meanreversion': 0.2
            },
            'signal_conflict_analysis': {
                'has_opposing': False,
                'dominant_weight': 0.65
            },
            'total_effective_weight': 0.65,
            'original_signals_count': 3,
            'relevant_signals_count': 3,
            'combined_data': {}
        }
        
        aggregated_signal = TradingSignal(
            symbol="bitcoin",
            signal_type=SignalType.SHORT,
            signal_strength=SignalStrength.WEAK,
            direction=SignalDirection.SELL,
            price=108547.14,
            confidence=1.0,
            timestamp=datetime.now(),
            strategy_name="Aggregated_Signal",
            position_size=0.02,
            stop_loss=113974.50,
            take_profit=97692.42,
            max_risk=0.02,
            analysis_data=aggregated_analysis
        )
        
        logger.info(f"📋 Created aggregated signal:")
        logger.info(f"   Symbol: {aggregated_signal.symbol}")
        logger.info(f"   Signal Type: {aggregated_signal.signal_type}")
        logger.info(f"   Price: ${aggregated_signal.price:,.2f}")
        logger.info(f"   Confidence: {aggregated_signal.confidence:.1%}")
        logger.info(f"   Strategy: {aggregated_signal.strategy_name}")
        logger.info(f"   Contributing Strategies: {aggregated_analysis['strategies_combined']}")
        
        # Create Discord webhook (using test configuration)
        discord_config = {
            'username': 'MTS Signal Bot',
            'avatar_url': None,
            'embed_color': 0x00ff00,
            'include_risk_metrics': True,
            'include_volatility_metrics': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }
        
        # Use a test webhook URL (you can replace this with your actual webhook for testing)
        test_webhook_url = "https://discord.com/api/webhooks/1408273388753129504/_w8oTulee_396ULSikz3My0yImCp-c2kyciTNCWJQIbM8uV35ZNuIRC4y0p6m6HionPT"
        
        webhook = DiscordWebhook(test_webhook_url, discord_config)
        
        # Test the embed creation
        embed = webhook._create_signal_embed(aggregated_signal)
        
        logger.info(f"📊 Discord Embed Created:")
        logger.info(f"   Title: {embed.get('title', 'N/A')}")
        logger.info(f"   Footer: {embed.get('footer', {}).get('text', 'N/A')}")
        
        # Check if the footer shows contributing strategies
        footer_text = embed.get('footer', {}).get('text', '')
        if 'Strategies:' in footer_text:
            logger.info("✅ SUCCESS: Discord embed shows contributing strategies!")
            logger.info(f"   Footer text: {footer_text}")
            return True
        else:
            logger.error("❌ FAILED: Discord embed does not show contributing strategies")
            logger.error(f"   Footer text: {footer_text}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing aggregated signal Discord alert: {e}")
        return False

async def test_individual_signal_discord():
    """Test Discord alert for individual strategy signal."""
    logger = setup_logging()
    
    logger.info("\n🧪 Testing Individual Strategy Signal Discord Alert")
    logger.info("=" * 60)
    
    try:
        # Create a test individual strategy signal
        individual_signal = TradingSignal(
            symbol="ethereum",
            signal_type=SignalType.LONG,
            signal_strength=SignalStrength.STRONG,
            direction=SignalDirection.BUY,
            price=3500.0,
            confidence=0.85,
            timestamp=datetime.now(),
            strategy_name="multibucketportfolio",
            position_size=0.05,
            stop_loss=3300.0,
            take_profit=3800.0,
            max_risk=0.02
        )
        
        logger.info(f"📋 Created individual strategy signal:")
        logger.info(f"   Symbol: {individual_signal.symbol}")
        logger.info(f"   Signal Type: {individual_signal.signal_type}")
        logger.info(f"   Strategy: {individual_signal.strategy_name}")
        
        # Create Discord webhook
        discord_config = {
            'username': 'MTS Signal Bot',
            'avatar_url': None,
            'embed_color': 0x00ff00,
            'include_risk_metrics': True,
            'include_volatility_metrics': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }
        
        test_webhook_url = "https://discord.com/api/webhooks/1408273388753129504/_w8oTulee_396ULSikz3My0yImCp-c2kyciTNCWJQIbM8uV35ZNuIRC4y0p6m6HionPT"
        
        webhook = DiscordWebhook(test_webhook_url, discord_config)
        
        # Test the embed creation
        embed = webhook._create_signal_embed(individual_signal)
        
        logger.info(f"📊 Discord Embed Created:")
        logger.info(f"   Title: {embed.get('title', 'N/A')}")
        logger.info(f"   Footer: {embed.get('footer', {}).get('text', 'N/A')}")
        
        # Check if the footer shows the individual strategy name
        footer_text = embed.get('footer', {}).get('text', '')
        if individual_signal.strategy_name in footer_text:
            logger.info("✅ SUCCESS: Discord embed shows individual strategy name!")
            logger.info(f"   Footer text: {footer_text}")
            return True
        else:
            logger.error("❌ FAILED: Discord embed does not show individual strategy name")
            logger.error(f"   Footer text: {footer_text}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing individual signal Discord alert: {e}")
        return False

async def main():
    """Run all Discord alert tests."""
    logger = setup_logging()
    
    # Test aggregated signal
    aggregated_success = await test_aggregated_signal_discord()
    
    # Test individual signal
    individual_success = await test_individual_signal_discord()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DISCORD ALERT TEST SUMMARY")
    logger.info("=" * 60)
    
    if aggregated_success and individual_success:
        logger.info("🎉 SUCCESS: Both aggregated and individual signal Discord alerts work correctly!")
        logger.info("📢 Aggregated signals will now show contributing strategies")
        logger.info("📢 Individual signals will show their specific strategy names")
        return 0
    else:
        logger.error("⚠️ Some Discord alert tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
