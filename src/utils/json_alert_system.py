"""
JSON Alert System for Volatility Signals
Generates timestamped JSON alerts when volatility spikes above thresholds.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.data.signal_models import TradingSignal, SignalType, SignalStrength


class JSONAlertSystem:
    """
    Generates timestamped JSON alerts for volatility signals.
    
    Features:
    - Timestamped JSON alerts
    - Configurable alert thresholds
    - File-based alert storage
    - Real-time alert generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JSON alert system.
        
        Args:
            config: Configuration for alert system
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = config or {
            'alert_directory': 'data/alerts',
            'volatility_threshold_percentile': 90,  # 90th percentile as requested
            'time_window_hours': 24,  # 24-hour window as requested
            'enabled_assets': ['bitcoin', 'ethereum'],
            'alert_format': 'json',
            'include_momentum': True,
            'position_direction_logic': 'momentum_based'
        }
        
        # Ensure alert directory exists
        self.alert_dir = Path(self.config['alert_directory'])
        self.alert_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"JSON Alert System initialized with {self.config['volatility_threshold_percentile']}th percentile threshold")
    
    def generate_volatility_alert(self, 
                                 asset: str, 
                                 current_price: float, 
                                 volatility_value: float, 
                                 volatility_threshold: float,
                                 volatility_percentile: float,
                                 signal_type: SignalType,
                                 timestamp: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a timestamped JSON alert for volatility spike.
        
        Args:
            asset: Asset name (e.g., 'bitcoin', 'ethereum')
            current_price: Current asset price
            volatility_value: Current volatility value
            volatility_threshold: Historical threshold (90th percentile)
            volatility_percentile: Current percentile
            signal_type: Signal type (LONG/SHORT)
            timestamp: Optional timestamp (uses current time if None)
            
        Returns:
            Dict containing the JSON alert
        """
        if timestamp is None:
            timestamp = int(datetime.now().timestamp() * 1000)
        
        # Determine position direction based on momentum
        position_direction = self._determine_position_direction(signal_type, volatility_percentile)
        
        alert = {
            "timestamp": timestamp,
            "asset": asset,
            "current_price": current_price,
            "volatility_value": volatility_value,
            "volatility_threshold": volatility_threshold,
            "volatility_percentile": volatility_percentile,
            "position_direction": position_direction,
            "signal_type": signal_type.value if hasattr(signal_type, 'value') else str(signal_type),
            "alert_type": "volatility_spike",
            "threshold_exceeded": volatility_percentile >= self.config['volatility_threshold_percentile']
        }
        
        return alert
    
    def _determine_position_direction(self, signal_type: SignalType, volatility_percentile: float) -> str:
        """
        Determine position direction based on momentum and volatility.
        
        Args:
            signal_type: The signal type
            volatility_percentile: Current volatility percentile
            
        Returns:
            Position direction string
        """
        if signal_type == SignalType.LONG:
            if volatility_percentile >= 95:
                return "STRONG_BUY"
            elif volatility_percentile >= 90:
                return "BUY"
            else:
                return "WEAK_BUY"
        elif signal_type == SignalType.SHORT:
            if volatility_percentile >= 98:
                return "STRONG_SELL"
            elif volatility_percentile >= 95:
                return "SELL"
            else:
                return "WEAK_SELL"
        else:
            return "HOLD"
    
    def save_alert(self, alert: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save alert to JSON file.
        
        Args:
            alert: Alert dictionary to save
            filename: Optional filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.fromtimestamp(alert['timestamp'] / 1000)
            filename = f"volatility_alert_{alert['asset']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.alert_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(alert, f, indent=2)
            
            self.logger.info(f"Alert saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
            raise
    
    def save_bulk_alerts(self, alerts: List[Dict[str, Any]]) -> List[str]:
        """
        Save multiple alerts to JSON files.
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        
        for alert in alerts:
            try:
                filepath = self.save_alert(alert)
                saved_files.append(filepath)
            except Exception as e:
                self.logger.error(f"Failed to save alert for {alert.get('asset', 'unknown')}: {e}")
                continue
        
        return saved_files
    
    def generate_alerts_from_signals(self, signals: List[TradingSignal]) -> List[Dict[str, Any]]:
        """
        Generate JSON alerts from trading signals.
        
        Args:
            signals: List of TradingSignal objects
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        for signal in signals:
            if signal.asset not in self.config['enabled_assets']:
                continue
            
            # Extract volatility data from signal analysis
            volatility_value = 0.0
            volatility_threshold = 0.0
            volatility_percentile = 0.0
            
            if signal.analysis_data:
                volatility_value = signal.analysis_data.get('volatility', 0.0)
                volatility_threshold = signal.analysis_data.get('volatility_threshold', 0.0)
                volatility_percentile = signal.analysis_data.get('volatility_percentile', 0.0)
            
            # Only generate alerts if volatility exceeds threshold
            if volatility_percentile >= self.config['volatility_threshold_percentile']:
                alert = self.generate_volatility_alert(
                    asset=signal.asset,
                    current_price=signal.price,
                    volatility_value=volatility_value,
                    volatility_threshold=volatility_threshold,
                    volatility_percentile=volatility_percentile,
                    signal_type=signal.signal_type,
                    timestamp=signal.timestamp
                )
                alerts.append(alert)
        
        return alerts
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent alerts from the last N hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent alerts
        """
        alerts = []
        cutoff_time = datetime.now().timestamp() * 1000 - (hours * 3600 * 1000)
        
        try:
            for filepath in self.alert_dir.glob("volatility_alert_*.json"):
                try:
                    with open(filepath, 'r') as f:
                        alert = json.load(f)
                    
                    if alert.get('timestamp', 0) >= cutoff_time:
                        alerts.append(alert)
                        
                except Exception as e:
                    self.logger.error(f"Failed to read alert file {filepath}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
        
        return alerts
    
    def clear_old_alerts(self, days: int = 7) -> int:
        """
        Clear alerts older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now().timestamp() * 1000 - (days * 24 * 3600 * 1000)
        deleted_count = 0
        
        try:
            for filepath in self.alert_dir.glob("volatility_alert_*.json"):
                try:
                    with open(filepath, 'r') as f:
                        alert = json.load(f)
                    
                    if alert.get('timestamp', 0) < cutoff_time:
                        filepath.unlink()
                        deleted_count += 1
                        self.logger.debug(f"Deleted old alert: {filepath}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to process alert file {filepath}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to clear old alerts: {e}")
        
        self.logger.info(f"Cleared {deleted_count} old alert files")
        return deleted_count 