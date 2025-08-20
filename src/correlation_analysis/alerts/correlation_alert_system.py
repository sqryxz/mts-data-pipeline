"""
Correlation alert system for correlation analysis module.
Generates and saves correlation breakdown alerts.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .alert_templates import AlertTemplates


class CorrelationAlertSystem:
    """
    Alert generation and distribution system for correlation analysis.
    """
    
    def __init__(self, alert_directory: str = "data/correlation/alerts"):
        """
        Initialize the correlation alert system.
        
        Args:
            alert_directory: Directory to store alert files
        """
        self.logger = logging.getLogger(__name__)
        self.alert_directory = Path(alert_directory)
        self.templates = AlertTemplates()
        
        # Ensure alert directory exists
        self.alert_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Alert system initialized with directory: {self.alert_directory}")
    
    def _validate_inputs(self, pair: str, data: Dict) -> bool:
        """
        Validate input parameters for alert generation.
        
        Args:
            pair: Asset pair name
            data: Alert data dictionary
            
        Returns:
            bool: True if inputs are valid
        """
        if not pair or not isinstance(pair, str) or not pair.strip():
            self.logger.error("Invalid pair parameter")
            return False
        
        if not data or not isinstance(data, dict):
            self.logger.error("Invalid data parameter")
            return False
        
        return True
    
    def _generate_filename(self, alert_type: str, pair: str = None) -> str:
        """
        Generate unique filename for alert.
        
        Args:
            alert_type: Type of alert (e.g., 'correlation_breakdown')
            pair: Asset pair name (optional)
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Add microseconds
        
        if pair:
            pair_clean = pair.lower().replace('_', '-').replace(' ', '-')
            return f"{alert_type}_{pair_clean}_{timestamp}.json"
        else:
            return f"{alert_type}_{timestamp}.json"
    
    def _save_alert_atomic(self, alert: Dict, filepath: Path) -> bool:
        """
        Save alert file atomically to prevent corruption.
        
        Args:
            alert: Alert data to save
            filepath: Target filepath
            
        Returns:
            bool: True if save successful
        """
        try:
            # Write to temporary file first
            temp_filepath = filepath.with_suffix('.tmp')
            
            with open(temp_filepath, 'w') as f:
                json.dump(alert, f, indent=2, default=str)
            
            # Atomic rename (OS-level atomic operation)
            temp_filepath.rename(filepath)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save alert atomically: {e}")
            return False
    
    def generate_breakdown_alert(self, pair: str, correlation_data: Dict) -> str:
        """
        Generate and save correlation breakdown alert.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            correlation_data: Dictionary containing correlation analysis results
            
        Returns:
            str: Filepath of saved alert file
        """
        try:
            # Validate inputs
            if not self._validate_inputs(pair, correlation_data):
                return ""
            
            # Generate alert using templates
            alert = self.templates.create_breakdown_alert_template(pair, correlation_data)
            
            if not alert:
                self.logger.error(f"Failed to generate alert template for {pair}")
                return ""
            
            # Generate filename
            filename = self._generate_filename("correlation_breakdown", pair)
            filepath = self.alert_directory / filename
            
            # Save alert atomically
            if not self._save_alert_atomic(alert, filepath):
                return ""
            
            self.logger.info(f"Generated breakdown alert for {pair}: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to generate breakdown alert for {pair}: {e}")
            return ""
    
    def generate_divergence_alert(self, pair: str, divergence_data: Dict) -> str:
        """
        Generate and save divergence signal alert.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            divergence_data: Dictionary containing divergence analysis results
            
        Returns:
            str: Filepath of saved alert file
        """
        try:
            # Validate inputs
            if not self._validate_inputs(pair, divergence_data):
                return ""
            
            # Generate alert using templates
            alert = self.templates.create_divergence_alert_template(pair, divergence_data)
            
            if not alert:
                self.logger.error(f"Failed to generate divergence alert template for {pair}")
                return ""
            
            # Generate filename
            filename = self._generate_filename("divergence_signal", pair)
            filepath = self.alert_directory / filename
            
            # Save alert atomically
            if not self._save_alert_atomic(alert, filepath):
                return ""
            
            self.logger.info(f"Generated divergence alert for {pair}: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to generate divergence alert for {pair}: {e}")
            return ""
    
    def generate_mosaic_alert(self, mosaic_data: Dict) -> str:
        """
        Generate and save daily mosaic alert.
        
        Args:
            mosaic_data: Dictionary containing mosaic analysis results
            
        Returns:
            str: Filepath of saved alert file
        """
        try:
            # Validate inputs
            if not mosaic_data or not isinstance(mosaic_data, dict):
                self.logger.error("Invalid mosaic data parameter")
                return ""
            
            # Generate alert using templates
            alert = self.templates.create_mosaic_alert_template(mosaic_data)
            
            if not alert:
                self.logger.error("Failed to generate mosaic alert template")
                return ""
            
            # Generate filename
            filename = self._generate_filename("daily_mosaic")
            filepath = self.alert_directory / filename
            
            # Save alert atomically
            if not self._save_alert_atomic(alert, filepath):
                return ""
            
            self.logger.info(f"Generated daily mosaic alert: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to generate mosaic alert: {e}")
            return ""
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent alerts from the alert directory.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[Dict[str, Any]]: List of recent alert data
        """
        try:
            recent_alerts = []
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            
            # Scan alert directory for recent files
            for alert_file in self.alert_directory.glob("*.json"):
                try:
                    # Check file modification time
                    file_mtime = alert_file.stat().st_mtime
                    if file_mtime < cutoff_time:
                        continue
                    
                    # Load alert data
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    # Add file metadata
                    alert_data['filepath'] = str(alert_file)
                    alert_data['file_size'] = alert_file.stat().st_size
                    alert_data['modified_time'] = file_mtime
                    
                    recent_alerts.append(alert_data)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to load alert file {alert_file}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            recent_alerts.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
            self.logger.info(f"Found {len(recent_alerts)} recent alerts in last {hours} hours")
            return recent_alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def cleanup_expired_alerts(self, max_age_hours: int = 168) -> int:
        """
        Clean up expired alert files.
        
        Args:
            max_age_hours: Maximum age of alerts to keep (default: 1 week)
            
        Returns:
            int: Number of files deleted
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for alert_file in self.alert_directory.glob("*.json"):
                try:
                    file_mtime = alert_file.stat().st_mtime
                    if file_mtime < cutoff_time:
                        alert_file.unlink()
                        deleted_count += 1
                        self.logger.debug(f"Deleted expired alert: {alert_file}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to delete expired alert {alert_file}: {e}")
                    continue
            
            self.logger.info(f"Cleaned up {deleted_count} expired alert files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired alerts: {e}")
            return 0
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored alerts.
        
        Returns:
            Dict[str, Any]: Alert statistics
        """
        try:
            stats = {
                'total_alerts': 0,
                'breakdown_alerts': 0,
                'divergence_alerts': 0,
                'mosaic_alerts': 0,
                'total_size_bytes': 0,
                'oldest_alert': None,
                'newest_alert': None
            }
            
            oldest_timestamp = float('inf')
            newest_timestamp = 0
            
            # Process files in batches to avoid memory issues
            alert_files = list(self.alert_directory.glob("*.json"))
            
            for alert_file in alert_files:
                try:
                    # Get file stats first
                    file_stats = alert_file.stat()
                    stats['total_size_bytes'] += file_stats.st_size
                    
                    # Only load small files for type counting (skip large files)
                    if file_stats.st_size > 1024 * 1024:  # Skip files > 1MB
                        self.logger.warning(f"Skipping large alert file: {alert_file} ({file_stats.st_size} bytes)")
                        stats['total_alerts'] += 1
                        continue
                    
                    # Load alert data for type counting
                    with open(alert_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    alert_type = alert_data.get('alert_type', 'unknown')
                    timestamp = alert_data.get('timestamp', 0)
                    
                    # Count by type
                    if alert_type == 'correlation_breakdown':
                        stats['breakdown_alerts'] += 1
                    elif alert_type == 'divergence_signal':
                        stats['divergence_alerts'] += 1
                    elif alert_type == 'daily_correlation_mosaic':
                        stats['mosaic_alerts'] += 1
                    
                    stats['total_alerts'] += 1
                    
                    # Track timestamps
                    if timestamp > 0:
                        if timestamp < oldest_timestamp:
                            oldest_timestamp = timestamp
                        if timestamp > newest_timestamp:
                            newest_timestamp = timestamp
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process alert file {alert_file}: {e}")
                    continue
            
            # Convert timestamps to readable format
            if oldest_timestamp != float('inf'):
                stats['oldest_alert'] = datetime.fromtimestamp(oldest_timestamp / 1000).isoformat()
            if newest_timestamp > 0:
                stats['newest_alert'] = datetime.fromtimestamp(newest_timestamp / 1000).isoformat()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}
