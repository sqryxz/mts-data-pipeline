"""
Multi-Webhook Discord Manager for Strategy-Specific Signal Routing
Sends signals from different strategies to different Discord webhooks.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from src.data.signal_models import TradingSignal
from src.utils.discord_webhook import DiscordAlertManager


class MultiWebhookDiscordManager:
    """
    Manages multiple Discord webhooks for different strategy signals.
    Allows routing signals from specific strategies to dedicated Discord channels.
    """
    
    def __init__(self, strategy_webhook_config: Dict[str, Dict[str, Any]]):
        """
        Initialize multi-webhook Discord manager.
        
        Args:
            strategy_webhook_config: Dictionary mapping strategy names to Discord config
                Format: {
                    "strategy_name": {
                        "webhook_url": "https://discord.com/api/webhooks/...",
                        "min_confidence": 0.5,
                        "enabled_assets": ["bitcoin", "ethereum"],
                        "enabled_signal_types": ["LONG", "SHORT"]
                    }
                }
        """
        self.logger = logging.getLogger(__name__)
        self.strategy_webhook_config = strategy_webhook_config
        self.discord_managers: Dict[str, DiscordAlertManager] = {}
        self._discord_executor = ThreadPoolExecutor(
            max_workers=4, 
            thread_name_prefix="multi-discord-alerts"
        )
        
        # Initialize Discord managers for each strategy
        self._initialize_discord_managers()
        
        self.logger.info(f"MultiWebhookDiscordManager initialized with {len(self.discord_managers)} strategy webhooks")
    
    def _initialize_discord_managers(self):
        """Initialize Discord alert managers for each configured strategy."""
        for strategy_name, config in self.strategy_webhook_config.items():
            try:
                webhook_url = config.get('webhook_url')
                if not webhook_url:
                    self.logger.warning(f"No webhook URL configured for strategy: {strategy_name}")
                    continue
                
                # Create Discord alert manager for this strategy
                discord_config = {
                    'min_confidence': config.get('min_confidence', 0.6),
                    'min_strength': config.get('min_strength', 'WEAK'),
                    'enabled_assets': config.get('enabled_assets', ['bitcoin', 'ethereum']),
                    'enabled_signal_types': config.get('enabled_signal_types', ['LONG', 'SHORT']),
                    'rate_limit': config.get('rate_limit', 60),
                    'batch_alerts': config.get('batch_alerts', True)
                }
                
                manager = DiscordAlertManager(webhook_url, discord_config)
                self.discord_managers[strategy_name] = manager
                
                self.logger.info(f"Initialized Discord manager for strategy: {strategy_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Discord manager for {strategy_name}: {e}")
    
    async def send_strategy_signals(self, strategy_signals: Dict[str, List[TradingSignal]]) -> Dict[str, Dict[str, int]]:
        """
        Send signals from each strategy to their respective Discord webhooks.
        
        Args:
            strategy_signals: Dictionary mapping strategy names to their signals
            
        Returns:
            Dict with results per strategy
        """
        results = {}
        
        for strategy_name, signals in strategy_signals.items():
            if not signals:
                continue
                
            if strategy_name not in self.discord_managers:
                self.logger.warning(f"No Discord webhook configured for strategy: {strategy_name}")
                continue
            
            try:
                manager = self.discord_managers[strategy_name]
                
                # Add strategy name to signal metadata for Discord display
                enhanced_signals = []
                for signal in signals:
                    # Create a copy with enhanced metadata
                    enhanced_signal = signal
                    if enhanced_signal.metadata is None:
                        enhanced_signal.metadata = {}
                    enhanced_signal.metadata['strategy_source'] = strategy_name
                    enhanced_signals.append(enhanced_signal)
                
                # Send signals to this strategy's Discord channel
                strategy_results = await manager.process_signals(enhanced_signals)
                results[strategy_name] = strategy_results
                
                self.logger.info(f"Sent {strategy_results.get('sent', 0)} signals from {strategy_name} to Discord")
                
            except Exception as e:
                self.logger.error(f"Failed to send {strategy_name} signals to Discord: {e}")
                results[strategy_name] = {'total': len(signals), 'sent': 0, 'failed': len(signals)}
        
        return results
    
    def send_strategy_signals_sync(self, strategy_signals: Dict[str, List[TradingSignal]]) -> Dict[str, Dict[str, int]]:
        """
        Synchronous wrapper for sending strategy signals to Discord.
        
        Args:
            strategy_signals: Dictionary mapping strategy names to their signals
            
        Returns:
            Dict with results per strategy
        """
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.send_strategy_signals(strategy_signals))
            finally:
                loop.close()
        
        future = self._discord_executor.submit(run_async)
        return future.result()
    
    def get_configured_strategies(self) -> List[str]:
        """Get list of strategies with configured Discord webhooks."""
        return list(self.discord_managers.keys())
    
    def add_strategy_webhook(self, strategy_name: str, webhook_config: Dict[str, Any]):
        """
        Add a new strategy webhook configuration.
        
        Args:
            strategy_name: Name of the strategy
            webhook_config: Discord webhook configuration
        """
        self.strategy_webhook_config[strategy_name] = webhook_config
        
        # Initialize Discord manager for this strategy
        try:
            webhook_url = webhook_config.get('webhook_url')
            if webhook_url:
                discord_config = {
                    'min_confidence': webhook_config.get('min_confidence', 0.6),
                    'min_strength': webhook_config.get('min_strength', 'WEAK'),
                    'enabled_assets': webhook_config.get('enabled_assets', ['bitcoin', 'ethereum']),
                    'enabled_signal_types': webhook_config.get('enabled_signal_types', ['LONG', 'SHORT']),
                    'rate_limit': webhook_config.get('rate_limit', 60),
                    'batch_alerts': webhook_config.get('batch_alerts', True)
                }
                
                manager = DiscordAlertManager(webhook_url, discord_config)
                self.discord_managers[strategy_name] = manager
                
                self.logger.info(f"Added Discord manager for strategy: {strategy_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add Discord manager for {strategy_name}: {e}")
    
    def shutdown(self):
        """Shutdown the multi-webhook Discord manager."""
        if self._discord_executor:
            self._discord_executor.shutdown(wait=True)
        self.logger.info("MultiWebhookDiscordManager shutdown complete")
