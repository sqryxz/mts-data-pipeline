#!/usr/bin/env python3
"""
Simple Discord Alert Test for Multi-Bucket Portfolio Strategy
Tests sending a Discord alert to verify the system is working.
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
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection

def setup_logging():
    """Setup logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

async def test_discord_alert():
    """Test sending a Discord alert for multi-bucket strategy."""
    logger = setup_logging()
    
    logger.info("🚀 Testing Multi-Bucket Portfolio Strategy Discord Alert")
    logger.info("=" * 60)
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Check if multi-bucket strategy is loaded
        if 'multibucketportfolio' not in generator.strategies:
            logger.error("❌ Multi-bucket portfolio strategy not found in generator")
            return False
        
        logger.info("✅ Multi-bucket portfolio strategy loaded")
        
        # Check if Discord manager is configured
        if not generator.multi_webhook_manager:
            logger.error("❌ Multi-webhook Discord manager not configured")
            return False
        
        logger.info("✅ Multi-webhook Discord manager configured")
        
        # Check if multi-bucket strategy has Discord manager
        if 'multibucketportfolio' not in generator.multi_webhook_manager.discord_managers:
            logger.error("❌ Multi-bucket portfolio strategy not found in Discord managers")
            return False
        
        logger.info("✅ Multi-bucket portfolio strategy has Discord manager")
        
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
        
        logger.info(f"📤 Sending test Discord alert...")
        logger.info(f"📋 Signal: {test_signal.symbol} {test_signal.signal_type} at ${test_signal.price:,.2f}")
        logger.info(f"📋 Confidence: {test_signal.confidence:.2f}")
        logger.info(f"📋 Strategy: {test_signal.strategy_name}")
        
        # Send Discord alert
        results = await generator.multi_webhook_manager.send_strategy_signals(strategy_signals)
        
        if results:
            multibucket_result = results.get('multibucketportfolio', {})
            alerts_sent = multibucket_result.get('alerts_sent', 0)
            logger.info(f"✅ Discord alert sent successfully! Alerts sent: {alerts_sent}")
            
            # Show detailed results
            for strategy, result in results.items():
                logger.info(f"📊 {strategy}: {result}")
            
            return True
        else:
            logger.error("❌ Failed to send Discord alert")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error testing Discord alert: {e}")
        return False

async def main():
    """Run the Discord alert test."""
    success = await test_discord_alert()
    
    if success:
        print("\n🎉 SUCCESS: Multi-bucket portfolio strategy Discord alerts are working!")
        print("📢 Check your Discord channel for the test alert.")
        return 0
    else:
        print("\n❌ FAILED: Discord alert test failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
