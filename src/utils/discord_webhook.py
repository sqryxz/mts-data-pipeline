"""
Discord Webhook Integration for Signal Alerts
Sends trading signal alerts to Discord channels via webhooks.
"""

import logging
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from src.data.signal_models import TradingSignal


class DiscordWebhook:
    """
    Discord webhook client for sending trading signal alerts.
    
    Features:
    - Async webhook sending
    - Rich embed formatting for signals
    - Configurable alert settings
    - Error handling and retry logic
    """
    
    def __init__(self, webhook_url: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Discord webhook client.
        
        Args:
            webhook_url: Discord webhook URL
            config: Optional configuration for webhook behavior
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = config or {
            'username': 'MTS Signal Bot',
            'avatar_url': None,
            'embed_color': 0x00ff00,  # Green for signals
            'include_risk_metrics': True,
            'include_volatility_metrics': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }
        
        self.logger.info("Discord webhook initialized")
    
    async def send_signal_alert(self, signal: TradingSignal) -> bool:
        """
        Send a single signal alert to Discord.
        
        Args:
            signal: TradingSignal object to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            embed = self._create_signal_embed(signal)
            payload = self._create_webhook_payload(embed)
            
            success = await self._send_webhook(payload)
            
            if success:
                self.logger.info(f"Signal alert sent to Discord: {signal.signal_type.value} {signal.symbol}")
            else:
                self.logger.error(f"Failed to send signal alert to Discord: {signal.signal_type.value} {signal.symbol}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending signal alert to Discord: {e}")
            return False
    
    async def send_bulk_signals(self, signals: List[TradingSignal]) -> Dict[str, int]:
        """
        Send multiple signal alerts to Discord.
        
        Args:
            signals: List of TradingSignal objects to send
            
        Returns:
            Dict with success/failure counts
        """
        results = {
            'total': len(signals),
            'success': 0,
            'failed': 0
        }
        
        for signal in signals:
            success = await self.send_signal_alert(signal)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        self.logger.info(f"Bulk signal alerts sent: {results['success']}/{results['total']} successful")
        return results
    
    def _create_signal_embed(self, signal: TradingSignal) -> Dict[str, Any]:
        """
        Create a rich embed for the signal alert.
        
        Args:
            signal: TradingSignal object
            
        Returns:
            Discord embed dictionary
        """
        # Determine color based on signal type
        if signal.signal_type.value == 'LONG':
            color = 0x00ff00  # Green
            emoji = "📈"
        elif signal.signal_type.value == 'SHORT':
            color = 0xff0000  # Red
            emoji = "📉"
        else:
            color = 0xffff00  # Yellow
            emoji = "⚠️"
        
        # Create embed
        embed = {
            "title": f"{emoji} {signal.signal_type.value} Signal: {signal.symbol.capitalize()}",
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {
                    "name": "💰 Price",
                    "value": f"${signal.price:,.2f}",
                    "inline": True
                },
                {
                    "name": "💪 Strength",
                    "value": signal.signal_strength.value,
                    "inline": True
                },
                {
                    "name": "🎯 Confidence",
                    "value": f"{signal.confidence:.1%}",
                    "inline": True
                },
                {
                    "name": "📊 Position Size",
                    "value": f"{signal.position_size:.1%}",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Strategy: {signal.strategy_name} | MTS Pipeline"
            }
        }
        
        # Add risk management fields
        if self.config.get('include_risk_metrics', True):
            risk_fields = []
            
            if signal.stop_loss:
                risk_fields.append({
                    "name": "🛑 Stop Loss",
                    "value": f"${signal.stop_loss:,.2f}",
                    "inline": True
                })
            
            if signal.take_profit:
                risk_fields.append({
                    "name": "🎯 Take Profit",
                    "value": f"${signal.take_profit:,.2f}",
                    "inline": True
                })
            
            if signal.max_risk:
                risk_fields.append({
                    "name": "⚠️ Max Risk",
                    "value": f"{signal.max_risk:.1%}",
                    "inline": True
                })
            
            embed["fields"].extend(risk_fields)
        
        # Add volatility metrics if available
        if self.config.get('include_volatility_metrics', True) and signal.analysis_data:
            vol_data = signal.analysis_data
            
            if 'volatility' in vol_data:
                embed["fields"].append({
                    "name": "📈 Volatility",
                    "value": f"{vol_data['volatility']:.2%}",
                    "inline": True
                })
            
            if 'volatility_ratio' in vol_data:
                embed["fields"].append({
                    "name": "📊 Volatility Ratio",
                    "value": f"{vol_data['volatility_ratio']:.2f}x",
                    "inline": True
                })
            
            if 'reason' in vol_data:
                embed["fields"].append({
                    "name": "💡 Reason",
                    "value": vol_data['reason'],
                    "inline": False
                })
        
        return embed
    
    def _create_webhook_payload(self, embed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the webhook payload.
        
        Args:
            embed: Discord embed dictionary
            
        Returns:
            Webhook payload dictionary
        """
        payload = {
            "embeds": [embed]
        }
        
        if self.config.get('username'):
            payload["username"] = self.config['username']
        
        if self.config.get('avatar_url'):
            payload["avatar_url"] = self.config['avatar_url']
        
        return payload
    
    async def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Send webhook payload to Discord.
        
        Args:
            payload: Webhook payload dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.webhook_url,
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 204:
                            return True
                        else:
                            self.logger.warning(f"Discord webhook returned status {response.status}")
                            return False
                            
            except Exception as e:
                self.logger.warning(f"Discord webhook attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        return False
    
    async def send_test_message(self) -> bool:
        """
        Send a test message to verify webhook configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        test_embed = {
            "title": "🧪 MTS Signal Bot Test",
            "description": "Discord webhook integration is working correctly!",
            "color": 0x0099ff,
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "MTS Pipeline - Signal Bot"
            }
        }
        
        payload = self._create_webhook_payload(test_embed)
        return await self._send_webhook(payload)
    
    def send_embed(self, embed: Dict[str, Any]) -> bool:
        """
        Send a custom embed to Discord (synchronous wrapper).
        
        Args:
            embed: Discord embed dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run async send_embed_async
            return loop.run_until_complete(self.send_embed_async(embed))
            
        except Exception as e:
            self.logger.error(f"Error in send_embed: {e}")
            return False
    
    async def send_embed_async(self, embed: Dict[str, Any]) -> bool:
        """
        Send a custom embed to Discord (async version).
        
        Args:
            embed: Discord embed dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = self._create_webhook_payload(embed)
            success = await self._send_webhook(payload)
            
            if success:
                self.logger.info("Custom embed sent to Discord successfully")
            else:
                self.logger.error("Failed to send custom embed to Discord")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending custom embed to Discord: {e}")
            return False


class DiscordAlertManager:
    """
    Manager for Discord signal alerts with configuration and filtering.
    """
    
    def __init__(self, webhook_url: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Discord alert manager.
        
        Args:
            webhook_url: Discord webhook URL
            config: Alert configuration
        """
        self.webhook = DiscordWebhook(webhook_url, config)
        self.logger = logging.getLogger(__name__)
        
        # Alert configuration
        self.alert_config = config or {
            'min_confidence': 0.6,
            'min_strength': 'WEAK',
            'enabled_assets': ['bitcoin', 'ethereum'],
            'enabled_signal_types': ['LONG', 'SHORT'],
            'rate_limit': 60,  # seconds between alerts
            'batch_alerts': True
        }
        
        self.last_alert_time = {}  # Track last alert time per asset
        
    async def process_signals(self, signals: List[TradingSignal]) -> Dict[str, int]:
        """
        Process and send signal alerts based on configuration.
        
        Args:
            signals: List of TradingSignal objects
            
        Returns:
            Dict with processing results
        """
        filtered_signals = self._filter_signals(signals)
        
        if not filtered_signals:
            self.logger.info("No signals passed filtering criteria")
            return {'total': len(signals), 'filtered': 0, 'sent': 0}
        
        # Send alerts
        if self.alert_config.get('batch_alerts', True):
            results = await self.webhook.send_bulk_signals(filtered_signals)
        else:
            results = {'total': len(filtered_signals), 'success': 0, 'failed': 0}
            for signal in filtered_signals:
                success = await self.webhook.send_signal_alert(signal)
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
        
        self.logger.info(f"Processed {len(signals)} signals, sent {results['success']} alerts")
        return {
            'total': len(signals),
            'filtered': len(filtered_signals),
            'sent': results['success'],
            'failed': results['failed']
        }
    
    def _filter_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """
        Filter signals based on configuration criteria.
        
        Args:
            signals: List of TradingSignal objects
            
        Returns:
            Filtered list of signals
        """
        filtered = []
        
        for signal in signals:
            # Check confidence threshold
            if signal.confidence < self.alert_config.get('min_confidence', 0.6):
                continue
            
            # Check strength threshold
            min_strength = self.alert_config.get('min_strength', 'WEAK')
            strength_order = ['WEAK', 'MODERATE', 'STRONG']
            if strength_order.index(signal.signal_strength.value) < strength_order.index(min_strength):
                continue
            
            # Check asset filter
            if signal.symbol not in self.alert_config.get('enabled_assets', ['bitcoin', 'ethereum']):
                continue
            
            # Check signal type filter
            if signal.signal_type.value not in self.alert_config.get('enabled_signal_types', ['LONG', 'SHORT']):
                continue
            
            # Check rate limiting
            if not self._check_rate_limit(signal.symbol):
                continue
            
            filtered.append(signal)
        
        return filtered
    
    def _check_rate_limit(self, asset: str) -> bool:
        """
        Check if asset is within rate limit.
        
        Args:
            asset: Asset name
            
        Returns:
            bool: True if within rate limit
        """
        rate_limit = self.alert_config.get('rate_limit', 60)
        current_time = datetime.now()
        
        if asset in self.last_alert_time:
            time_diff = (current_time - self.last_alert_time[asset]).total_seconds()
            if time_diff < rate_limit:
                return False
        
        self.last_alert_time[asset] = current_time
        return True
    
    async def send_test_alert(self) -> bool:
        """
        Send a test alert to verify configuration.
        
        Returns:
            bool: True if successful
        """
        return await self.webhook.send_test_message() 