"""
Mosaic alert system for correlation analysis module.
Generates and manages daily mosaic alerts with comprehensive summaries.
"""

import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .alert_templates import AlertTemplates
from .discord_integration import CorrelationDiscordIntegration
from ..visualization.mosaic_generator import MosaicGenerator


class MosaicAlertSystem:
    """
    Dedicated system for generating and managing mosaic alerts.
    """
    
    def __init__(self, alert_directory: str = "data/correlation/alerts", discord_config: Optional[Dict] = None):
        """
        Initialize the mosaic alert system.
        
        Args:
            alert_directory: Directory to store alert files
            discord_config: Discord configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.alert_directory = Path(alert_directory)
        self.templates = AlertTemplates()
        self.mosaic_generator = MosaicGenerator()
        
        # Initialize Discord integration
        self.discord_integration = CorrelationDiscordIntegration(config=discord_config)
        
        # Ensure alert directory exists
        self.alert_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Mosaic alert system initialized with directory: {self.alert_directory}")
        if self.discord_integration.discord:
            self.logger.info("Discord integration enabled for mosaic alerts")
        else:
            self.logger.info("Discord integration disabled - no webhook URL provided")
    
    def generate_daily_mosaic_alert(self, force_regeneration: bool = False) -> str:
        """
        Generate daily mosaic alert with comprehensive summary.
        
        Args:
            force_regeneration: If True, regenerate even if alert exists for today
            
        Returns:
            str: Filepath of saved alert file
        """
        try:
            self.logger.info("Starting daily mosaic alert generation")
            
            # Check if alert already exists for today
            today = datetime.now().strftime('%Y-%m-%d')
            existing_alert = self._find_existing_daily_alert(today)
            
            if existing_alert and not force_regeneration:
                self.logger.info(f"Daily mosaic alert already exists for {today}: {existing_alert}")
                return str(existing_alert)
            
            # Generate daily mosaic
            mosaic_data = self.mosaic_generator.generate_daily_mosaic()
            
            if not mosaic_data:
                self.logger.error("Failed to generate daily mosaic data")
                return ""
            
            # Enhance mosaic data with additional insights
            enhanced_mosaic = self._enhance_mosaic_data(mosaic_data)
            
            # Generate alert using templates
            alert = self.templates.create_mosaic_alert_template(enhanced_mosaic)
            
            if not alert:
                self.logger.error("Failed to generate mosaic alert template")
                return ""
            
            # Generate filename
            filename = self._generate_filename("daily_mosaic")
            filepath = self.alert_directory / filename
            
            # Save alert atomically
            if not self._save_alert_atomic(alert, filepath):
                return ""
            
            # Send to Discord if integration is enabled
            if self.discord_integration.discord:
                self.logger.info("Sending mosaic alert to Discord...")
                discord_success = self.discord_integration.send_mosaic_alert(enhanced_mosaic, str(filepath))
                if discord_success:
                    self.logger.info("✅ Mosaic alert sent to Discord successfully")
                else:
                    self.logger.warning("⚠️ Failed to send mosaic alert to Discord")
            
            self.logger.info(f"Generated daily mosaic alert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to generate daily mosaic alert: {e}")
            return ""
    
    def send_correlation_breakdown_alert(self, pair: str, correlation_data: Dict[str, Any]) -> bool:
        """
        Send correlation breakdown alert to Discord.
        
        Args:
            pair: Correlation pair (e.g., "BTC_ETH")
            correlation_data: Correlation breakdown data
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.discord_integration.discord:
            self.logger.warning("Discord integration not available for breakdown alerts")
            return False
        
        try:
            self.logger.info(f"Sending correlation breakdown alert to Discord for {pair}")
            success = self.discord_integration.send_correlation_breakdown_alert(pair, correlation_data)
            
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
        if not self.discord_integration.discord:
            self.logger.warning("Discord integration not available for daily summary")
            return False
        
        try:
            self.logger.info("Sending daily correlation summary to Discord")
            success = self.discord_integration.send_daily_summary(summary_data)
            
            if success:
                self.logger.info("✅ Daily correlation summary sent to Discord")
            else:
                self.logger.error("❌ Failed to send daily correlation summary to Discord")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary to Discord: {e}")
            return False
    
    def _enhance_mosaic_data(self, mosaic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance mosaic data with additional insights and analysis.
        
        Args:
            mosaic_data: Raw mosaic data
            
        Returns:
            Dict[str, Any]: Enhanced mosaic data
        """
        try:
            enhanced_data = mosaic_data.copy()
            
            # Extract correlation matrix summary
            correlation_matrix = mosaic_data.get('correlation_matrix', {})
            summary = correlation_matrix.get('summary', {})
            
            # Add enhanced summary
            enhanced_data.update({
                'total_pairs': summary.get('total_pairs', 0),
                'significant_correlations': summary.get('significant_correlations', 0),
                'average_correlation_strength': summary.get('average_correlation_strength', 0.0),
                'strong_correlations': summary.get('strong_correlations', 0),
                'weak_correlations': summary.get('weak_correlations', 0),
                'negative_correlations': summary.get('negative_correlations', 0),
                'breakdown_events': 0,  # Will be calculated from correlation monitor
                'divergence_signals': 0,  # Will be calculated from correlation monitor
                'key_findings': enhanced_data.get('key_findings', []),
                'recommendations': enhanced_data.get('recommendations', []),
                'json_report_path': enhanced_data.get('file_locations', {}).get('json_report', ''),
                'html_report_path': '',  # Placeholder for future HTML reports
                'heatmap_path': ''  # Placeholder for future heatmap images
            })
            
            # Add market insights
            enhanced_data['market_insights'] = self._generate_market_insights(correlation_matrix)
            
            # Add portfolio recommendations
            enhanced_data['portfolio_recommendations'] = self._generate_portfolio_recommendations(correlation_matrix)
            
            # Add risk warnings
            enhanced_data['risk_warnings'] = self._generate_risk_warnings(correlation_matrix)
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"Failed to enhance mosaic data: {e}")
            return mosaic_data
    
    def _generate_market_insights(self, correlation_matrix: Dict[str, Any]) -> List[str]:
        """Generate market insights from correlation matrix."""
        insights = []
        
        try:
            summary = correlation_matrix.get('summary', {})
            matrix = correlation_matrix.get('matrix', {})
            
            average_correlation = summary.get('average_correlation_strength', 0.0)
            strong_correlations = summary.get('strong_correlations', 0)
            negative_correlations = summary.get('negative_correlations', 0)
            total_pairs = summary.get('total_pairs', 0)
            
            # Market structure insights
            if abs(average_correlation) < 0.3:
                insights.append("Low correlation environment suggests good diversification opportunities")
            
            if average_correlation > 0.6:
                insights.append("High correlation environment - consider reducing portfolio concentration")
            
            if strong_correlations > total_pairs * 0.3:
                insights.append("Strong correlations detected - market may be trending")
            
            if negative_correlations > 0:
                insights.append(f"Found {negative_correlations} negative correlations - potential hedging opportunities")
            
            # Extract specific insights from matrix
            strong_pairs = []
            for pair, correlations in matrix.items():
                for window, data in correlations.items():
                    correlation = data.get('correlation', 0.0)
                    if abs(correlation) >= 0.8 and not self._is_nan(correlation):
                        strong_pairs.append(f"{pair} ({window}: {correlation:.3f})")
            
            if strong_pairs:
                insights.append(f"Strongest correlations: {', '.join(strong_pairs[:3])}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate market insights: {e}")
            insights.append("Error generating market insights")
        
        return insights
    
    def _generate_portfolio_recommendations(self, correlation_matrix: Dict[str, Any]) -> List[str]:
        """Generate portfolio recommendations from correlation matrix."""
        recommendations = []
        
        try:
            summary = correlation_matrix.get('summary', {})
            average_correlation = summary.get('average_correlation_strength', 0.0)
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 0)
            
            # Portfolio recommendations
            if strong_correlations > 0:
                recommendations.append("Consider correlation-based trading strategies for strongly correlated pairs")
            
            if abs(average_correlation) < 0.3:
                recommendations.append("Low average correlation suggests good diversification opportunities")
            
            if average_correlation > 0.5:
                recommendations.append("High average correlation - consider reducing portfolio concentration")
            
            recommendations.append("Monitor correlation breakdowns for trading opportunities")
            recommendations.append("Review correlation trends for portfolio rebalancing decisions")
            
            # Risk management recommendations
            if strong_correlations > total_pairs * 0.2:
                recommendations.append("Consider increasing position sizing for strongly correlated assets")
            
            if summary.get('negative_correlations', 0) > 0:
                recommendations.append("Negative correlations detected - consider hedging strategies")
            
        except Exception as e:
            self.logger.error(f"Failed to generate portfolio recommendations: {e}")
            recommendations.append("Error generating portfolio recommendations")
        
        return recommendations
    
    def _generate_risk_warnings(self, correlation_matrix: Dict[str, Any]) -> List[str]:
        """Generate risk warnings from correlation matrix."""
        warnings = []
        
        try:
            summary = correlation_matrix.get('summary', {})
            average_correlation = summary.get('average_correlation_strength', 0.0)
            strong_correlations = summary.get('strong_correlations', 0)
            total_pairs = summary.get('total_pairs', 0)
            
            # Risk warnings
            if average_correlation > 0.7:
                warnings.append("⚠️ High correlation environment - increased portfolio risk")
            
            if strong_correlations > total_pairs * 0.5:
                warnings.append("⚠️ Majority of assets show strong correlations - limited diversification")
            
            if summary.get('significant_correlations', 0) < total_pairs * 0.2:
                warnings.append("⚠️ Few significant correlations - may indicate market instability")
            
            # Add general risk warnings
            warnings.append("Monitor for correlation breakdowns that may signal regime changes")
            warnings.append("Consider correlation-adjusted position sizing")
            
        except Exception as e:
            self.logger.error(f"Failed to generate risk warnings: {e}")
            warnings.append("Error generating risk warnings")
        
        return warnings
    
    def _is_nan(self, value) -> bool:
        """Check if value is NaN."""
        import math
        return isinstance(value, float) and math.isnan(value)
    
    def _find_existing_daily_alert(self, date: str) -> Optional[Path]:
        """Find existing daily alert for a specific date."""
        try:
            for alert_file in self.alert_directory.glob("*.json"):
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    if (alert_data.get('alert_type') == 'daily_correlation_mosaic' and 
                        alert_data.get('date') == date):
                        return alert_file
                        
                except Exception as e:
                    self.logger.debug(f"Failed to read alert file {alert_file}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to find existing daily alert: {e}")
            return None
    
    def _generate_filename(self, alert_type: str) -> str:
        """Generate filename for mosaic alert."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        return f"{alert_type}_{timestamp}.json"
    
    def _save_alert_atomic(self, alert: Dict, filepath: Path) -> bool:
        """Save alert atomically to prevent corruption."""
        try:
            # Write to temporary file first
            temp_filepath = filepath.with_suffix('.tmp')
            
            with open(temp_filepath, 'w') as f:
                json.dump(alert, f, indent=2, default=str)
            
            # Atomic rename
            temp_filepath.rename(filepath)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save alert atomically: {e}")
            return False
    
    def get_mosaic_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get mosaic alert history for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List[Dict[str, Any]]: List of mosaic alerts
        """
        try:
            alerts = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for alert_file in self.alert_directory.glob("*.json"):
                try:
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    if alert_data.get('alert_type') == 'daily_correlation_mosaic':
                        alert_date = datetime.strptime(alert_data.get('date', ''), '%Y-%m-%d')
                        if alert_date >= cutoff_date:
                            alert_data['filepath'] = str(alert_file)
                            alerts.append(alert_data)
                    
                except Exception as e:
                    self.logger.debug(f"Failed to read alert file {alert_file}: {e}")
                    continue
            
            # Sort by date (newest first)
            alerts.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            self.logger.info(f"Found {len(alerts)} mosaic alerts in last {days} days")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get mosaic alert history: {e}")
            return []
    
    def get_mosaic_alert_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get summary of mosaic alerts for the specified number of days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict[str, Any]: Summary of mosaic alerts
        """
        try:
            alerts = self.get_mosaic_alert_history(days)
            
            if not alerts:
                return {
                    'total_alerts': 0,
                    'date_range': f"Last {days} days",
                    'average_correlations': 0.0,
                    'total_findings': 0,
                    'average_recommendations': 0.0
                }
            
            # Calculate summary statistics
            total_alerts = len(alerts)
            total_correlations = sum(alert.get('mosaic_summary', {}).get('total_pairs_analyzed', 0) for alert in alerts)
            total_findings = sum(len(alert.get('key_findings', [])) for alert in alerts)
            total_recommendations = sum(len(alert.get('recommendations', [])) for alert in alerts)
            
            average_correlations = total_correlations / total_alerts if total_alerts > 0 else 0
            average_findings = total_findings / total_alerts if total_alerts > 0 else 0
            average_recommendations = total_recommendations / total_alerts if total_alerts > 0 else 0
            
            return {
                'total_alerts': total_alerts,
                'date_range': f"Last {days} days",
                'average_correlations': average_correlations,
                'average_findings': average_findings,
                'average_recommendations': average_recommendations,
                'latest_alert': alerts[0] if alerts else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get mosaic alert summary: {e}")
            return {}
