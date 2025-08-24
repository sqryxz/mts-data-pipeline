"""
Discord integration for correlation analysis alerts.
Sends mosaic alerts and correlation notifications to Discord webhooks.
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.utils.discord_webhook import DiscordWebhook


class CorrelationDiscordIntegration:
    """
    Discord integration for correlation analysis alerts.
    """
    
    def __init__(self, webhook_url: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize Discord integration.
        
        Args:
            webhook_url: Discord webhook URL
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.webhook_url = webhook_url
        self.config = config or {}
        
        # Load webhook URL from config if not provided
        if not self.webhook_url:
            self.webhook_url = self.config.get('discord_webhook_url')
        
        # Initialize Discord webhook
        if self.webhook_url:
            self.discord = DiscordWebhook(self.webhook_url)
            self.logger.info("Discord integration initialized with webhook")
        else:
            self.discord = None
            self.logger.warning("No Discord webhook URL provided - Discord alerts disabled")
    
    def send_mosaic_alert(self, mosaic_data: Dict[str, Any], alert_filepath: str = "") -> bool:
        """
        Send mosaic alert to Discord.
        
        Args:
            mosaic_data: Mosaic data dictionary
            alert_filepath: Path to alert file (optional)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.discord:
            self.logger.warning("Discord integration not available")
            return False
        
        try:
            # Create Discord embed
            embed = self._create_mosaic_embed(mosaic_data, alert_filepath)
            
            # Send to Discord
            success = self.discord.send_embed(embed)
            
            if success:
                self.logger.info("✅ Mosaic alert sent to Discord successfully")
            else:
                self.logger.error("❌ Failed to send mosaic alert to Discord")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending mosaic alert to Discord: {e}")
            return False
    
    def send_correlation_breakdown_alert(self, pair: str, correlation_data: Dict[str, Any]) -> bool:
        """
        Send correlation breakdown alert to Discord.
        
        Args:
            pair: Correlation pair (e.g., "BTC_ETH")
            correlation_data: Correlation breakdown data
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.discord:
            self.logger.warning("Discord integration not available")
            return False
        
        try:
            # Create Discord embed
            embed = self._create_breakdown_embed(pair, correlation_data)
            
            # Send to Discord
            success = self.discord.send_embed(embed)
            
            if success:
                self.logger.info(f"✅ Correlation breakdown alert sent to Discord for {pair}")
            else:
                self.logger.error(f"❌ Failed to send correlation breakdown alert to Discord for {pair}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending correlation breakdown alert to Discord: {e}")
            return False
    
    def send_daily_summary(self, summary_data: Dict[str, Any]) -> bool:
        """
        Send daily correlation summary to Discord.
        
        Args:
            summary_data: Daily summary data
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.discord:
            self.logger.warning("Discord integration not available")
            return False
        
        try:
            # Create Discord embed
            embed = self._create_daily_summary_embed(summary_data)
            
            # Send to Discord
            success = self.discord.send_embed(embed)
            
            if success:
                self.logger.info("✅ Daily correlation summary sent to Discord")
            else:
                self.logger.error("❌ Failed to send daily correlation summary to Discord")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary to Discord: {e}")
            return False
    
    def _create_mosaic_embed(self, mosaic_data: Dict[str, Any], alert_filepath: str = "") -> Dict[str, Any]:
        """Create Discord embed for mosaic alert."""
        try:
            # Extract key data
            correlation_matrix = mosaic_data.get('correlation_matrix', {})
            summary = correlation_matrix.get('summary', {})
            key_findings = mosaic_data.get('key_findings', [])
            recommendations = mosaic_data.get('recommendations', [])
            market_insights = mosaic_data.get('market_insights', [])

            # Extract notable pairs from key findings
            notable_pairs = self._extract_notable_pairs_from_findings(key_findings)

            # Create embed
            embed = {
                "title": "🎨 Daily Correlation Mosaic Alert",
                "description": "Comprehensive correlation analysis for today's market conditions",
                "color": 0x00ff00,  # Green
                "timestamp": datetime.now().isoformat(),
                "fields": []
            }

            # Add summary fields
            embed["fields"].extend([
                {
                    "name": "📊 Summary",
                    "value": f"**Total Pairs:** {summary.get('total_pairs', 0)}\n"
                            f"**Significant Correlations:** {summary.get('significant_correlations', 0)}\n"
                            f"**Average Strength:** {summary.get('average_correlation_strength', 0.0):.3f}\n"
                            f"**Strong Correlations:** {summary.get('strong_correlations', 0)}",
                    "inline": True
                }
            ])

            # Add pairs worth watching section
            if notable_pairs:
                pairs_text = []
                if notable_pairs.get('strong_positive'):
                    pairs_text.append(f"🔥 **Strong Positive:** {', '.join(notable_pairs['strong_positive'][:2])}")
                if notable_pairs.get('strong_negative'):
                    pairs_text.append(f"🛡️ **Strong Negative:** {', '.join(notable_pairs['strong_negative'][:2])}")
                if notable_pairs.get('high_significance'):
                    pairs_text.append(f"📊 **Highly Significant:** {', '.join(notable_pairs['high_significance'][:2])}")
                if notable_pairs.get('correlation_changes'):
                    pairs_text.append(f"⚡ **Major Changes:** {', '.join(notable_pairs['correlation_changes'][:2])}")

                if pairs_text:
                    embed["fields"].append({
                        "name": "👀 Pairs Worth Watching",
                        "value": "\n".join(pairs_text),
                        "inline": False
                    })

            # Add market insights
            embed["fields"].append({
                "name": "📈 Market Insights",
                "value": "\n".join(market_insights[:3]) if market_insights else "Low correlation environment suggests good diversification opportunities",
                "inline": False
            })

            # Add key findings (filter out the specific pair findings since we show them separately)
            general_findings = [f for f in key_findings if not any(keyword in f.lower() for keyword in ['strong positive', 'strong negative', 'highly significant', 'correlation changes'])]
            if general_findings:
                embed["fields"].append({
                    "name": "🔍 Analysis",
                    "value": "\n".join(f"• {finding}" for finding in general_findings[:3]),
                    "inline": False
                })

            # Add recommendations
            if recommendations:
                embed["fields"].append({
                    "name": "💡 Recommendations",
                    "value": "\n".join(f"• {rec}" for rec in recommendations[:3]),
                    "inline": False
                })

            # Add footer with file path
            if alert_filepath:
                embed["footer"] = {
                    "text": f"Detailed report: {Path(alert_filepath).name}"
                }

            return embed

        except Exception as e:
            self.logger.error(f"Error creating mosaic embed: {e}")
            return {
                "title": "🎨 Correlation Mosaic Alert",
                "description": "Daily correlation analysis completed",
                "color": 0xff0000,  # Red for error
                "timestamp": datetime.now().isoformat()
            }

    def _extract_notable_pairs_from_findings(self, key_findings: List[str]) -> Dict[str, List[str]]:
        """Extract notable pairs from key findings."""
        notable_pairs = {
            'strong_positive': [],
            'strong_negative': [],
            'high_significance': [],
            'correlation_changes': []
        }

        try:
            for finding in key_findings:
                finding_lower = finding.lower()

                if 'strong positive correlations:' in finding_lower:
                    # Extract pairs like "BTC_XRP (60d: 0.448), ETH_XRP (30d: 0.239)"
                    pairs_text = finding.split(': ', 1)[1]
                    pairs = [pair.strip() for pair in pairs_text.split(', ')]
                    notable_pairs['strong_positive'] = pairs

                elif 'strong negative correlations:' in finding_lower:
                    pairs_text = finding.split(': ', 1)[1]
                    pairs = [pair.strip() for pair in pairs_text.split(', ')]
                    notable_pairs['strong_negative'] = pairs

                elif 'highly significant pairs:' in finding_lower:
                    pairs_text = finding.split(': ', 1)[1]
                    pairs = [pair.strip() for pair in pairs_text.split(', ')]
                    notable_pairs['high_significance'] = pairs

                elif 'notable correlation changes:' in finding_lower:
                    pairs_text = finding.split(': ', 1)[1]
                    pairs = [pair.strip() for pair in pairs_text.split(', ')]
                    notable_pairs['correlation_changes'] = pairs

        except Exception as e:
            self.logger.error(f"Error extracting notable pairs from findings: {e}")

        return notable_pairs
    
    def _create_breakdown_embed(self, pair: str, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Discord embed for correlation breakdown alert."""
        try:
            # Extract correlation data
            current_correlation = correlation_data.get('current_correlation', 0.0)
            previous_correlation = correlation_data.get('previous_correlation', 0.0)
            change = current_correlation - previous_correlation
            # Display p-value if available (more interpretable for significance)
            significance = correlation_data.get('p_value', correlation_data.get('significance', 0.0))
            
            # Determine color based on change (more restrictive thresholds)
            if abs(change) > 0.5:
                color = 0xff0000  # Red for major change
            elif abs(change) > 0.3:
                color = 0xffa500  # Orange for significant change
            else:
                color = 0x00ff00  # Green for minor change (won't be sent due to other filters)
            
            # Create embed
            embed = {
                "title": f"⚠️ Correlation Breakdown Alert: {pair}",
                "description": f"Significant change detected in correlation between {pair}",
                "color": color,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Correlation Change",
                        "value": f"**Previous:** {previous_correlation:.3f}\n"
                                f"**Current:** {current_correlation:.3f}\n"
                                f"**Change:** {change:+.3f}\n"
                                f"**p-value:** {significance:.3f}",
                        "inline": True
                    },
                    {
                        "name": "🎯 Impact",
                        "value": self._get_breakdown_impact(change, pair),
                        "inline": True
                    }
                ]
            }
            
            return embed
            
        except Exception as e:
            self.logger.error(f"Error creating breakdown embed: {e}")
            return {
                "title": f"⚠️ Correlation Breakdown: {pair}",
                "description": "Correlation breakdown detected",
                "color": 0xff0000,
                "timestamp": datetime.now().isoformat()
            }
    
    def _create_daily_summary_embed(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Discord embed for daily correlation summary."""
        try:
            # Extract summary data
            total_pairs = summary_data.get('total_pairs', 0)
            alerts_generated = summary_data.get('alerts_generated', 0)
            breakouts_detected = summary_data.get('breakouts_detected', 0)
            average_correlation = summary_data.get('average_correlation', 0.0)
            
            # Create embed
            embed = {
                "title": "📈 Daily Correlation Summary",
                "description": "End-of-day correlation analysis summary",
                "color": 0x0099ff,  # Blue
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "📊 Daily Statistics",
                        "value": f"**Pairs Monitored:** {total_pairs}\n"
                                f"**Alerts Generated:** {alerts_generated}\n"
                                f"**Breakouts Detected:** {breakouts_detected}\n"
                                f"**Avg Correlation:** {average_correlation:.3f}",
                        "inline": True
                    }
                ]
            }
            
            return embed
            
        except Exception as e:
            self.logger.error(f"Error creating daily summary embed: {e}")
            return {
                "title": "📈 Daily Correlation Summary",
                "description": "Daily correlation analysis completed",
                "color": 0xff0000,
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_breakdown_impact(self, change: float, pair: str) -> str:
        """Get impact description for correlation breakdown."""
        if abs(change) > 0.7:
            return "🚨 **Critical Impact** - Extreme correlation shift"
        elif abs(change) > 0.5:
            return "🚨 **High Impact** - Major correlation shift"
        elif abs(change) > 0.3:
            return "⚠️ **Medium Impact** - Significant change"
        else:
            return "📊 **Low Impact** - Moderate change"
