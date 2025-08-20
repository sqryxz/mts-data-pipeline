"""
Alert templates for correlation analysis module.
Defines JSON alert schemas and template rendering.
"""

import logging
import json
import hashlib
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class AlertTemplates:
    """
    JSON alert templates for correlation analysis.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the alert templates.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        
        # Default configuration
        self.default_config = {
            'alert_expiration_hours': {
                'correlation_breakdown': 1,
                'divergence_signal': 2,
                'daily_correlation_mosaic': 24
            },
            'severity_thresholds': {
                'low': 2.5,
                'medium': 3.0,
                'high': 3.5,
                'extreme': 4.0
            },
            'alert_id_prefix': 'corr',
            'timezone': 'UTC',
            'macro_indicators': ['dxy', 'yield', 'spread', 'vix', 'gold', 'oil'],
            'deduplication_window_minutes': 30
        }
        
        if self.config:
            self.default_config.update(self.config)
        
        # Track recent alerts for deduplication
        self._recent_alerts = {}
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict: Configuration dictionary
        """
        if not config_path:
            return {}
        
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Configuration file not found: {config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return {}
    
    def _validate_correlation_data(self, data: Dict) -> bool:
        """
        Validate correlation data structure and types.
        
        Args:
            data: Correlation data dictionary
            
        Returns:
            bool: True if data is valid
        """
        try:
            required_fields = ['current_correlation', 'z_score', 'p_value']
            
            for field in required_fields:
                if field not in data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
                
                value = data[field]
                if not isinstance(value, (int, float)):
                    self.logger.error(f"Invalid value for {field}: {value}")
                    return False
                
                # Handle special cases for p_value
                if field == 'p_value':
                    if np.isnan(value):
                        self.logger.error(f"Invalid value for {field}: {value}")
                        return False
                    # Accept p_value of 0.0 (perfect correlation case)
                    if value < 0.0 or value > 1.0:
                        self.logger.error(f"P-value out of range: {value}")
                        return False
                elif np.isnan(value):
                    self.logger.error(f"Invalid value for {field}: {value}")
                    return False
            
            # Validate correlation range
            if not -1 <= data['current_correlation'] <= 1:
                self.logger.error(f"Correlation out of range: {data['current_correlation']}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return False
    
    def _validate_divergence_data(self, data: Dict) -> bool:
        """
        Validate divergence data structure and types.
        
        Args:
            data: Divergence data dictionary
            
        Returns:
            bool: True if data is valid
        """
        try:
            required_fields = ['divergence_type', 'correlation_strength']
            
            for field in required_fields:
                if field not in data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate correlation_strength range
            if not -1 <= data['correlation_strength'] <= 1:
                self.logger.error(f"Correlation strength out of range: {data['correlation_strength']}")
                return False
            
            # Validate divergence_type values
            valid_types = ['price_momentum', 'price_divergence', 'momentum_divergence']
            if data['divergence_type'] not in valid_types:
                self.logger.error(f"Invalid divergence type: {data['divergence_type']}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Divergence data validation failed: {e}")
            return False
    
    def _validate_mosaic_data(self, data: Dict) -> bool:
        """
        Validate mosaic data structure and types.
        
        Args:
            data: Mosaic data dictionary
            
        Returns:
            bool: True if data is valid
        """
        try:
            required_fields = ['total_pairs', 'significant_correlations']
            
            for field in required_fields:
                if field not in data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
                
                value = data[field]
                if not isinstance(value, (int, float)) or value < 0:
                    self.logger.error(f"Invalid value for {field}: {value}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Mosaic data validation failed: {e}")
            return False
    
    def _is_duplicate_alert(self, alert_type: str, pair: str, severity: str) -> bool:
        """
        Check if similar alert was generated recently.
        
        Args:
            alert_type: Type of alert
            pair: Asset pair
            severity: Alert severity
            
        Returns:
            bool: True if duplicate alert
        """
        try:
            key = f"{alert_type}_{pair}_{severity}"
            now = datetime.now()
            
            if key in self._recent_alerts:
                time_diff = (now - self._recent_alerts[key]).total_seconds()
                dedup_window = self.default_config['deduplication_window_minutes'] * 60
                
                if time_diff < dedup_window:
                    self.logger.debug(f"Duplicate alert suppressed: {key}")
                    return True
            
            self._recent_alerts[key] = now
            return False
            
        except Exception as e:
            self.logger.error(f"Duplicate check failed: {e}")
            return False
    
    def _generate_alert_id(self, alert_type: str, pair: str) -> str:
        """
        Generate unique alert ID with collision handling.
        
        Args:
            alert_type: Type of alert
            pair: Asset pair
            
        Returns:
            str: Unique alert ID
        """
        try:
            # Include milliseconds to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            
            # Clean pair name
            pair_clean = pair.replace('_', '-').replace(' ', '-').lower()
            
            # Create base ID
            base_id = f"{self.default_config['alert_id_prefix']}_{alert_type}_{pair_clean}_{timestamp}"
            
            # Add hash for additional uniqueness
            hash_suffix = hashlib.md5(base_id.encode()).hexdigest()[:8]
            
            return f"{base_id}_{hash_suffix}"
            
        except Exception as e:
            self.logger.error(f"Failed to generate alert ID: {e}")
            return f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_breakdown_alert_template(self, pair: str, correlation_data: Dict) -> Dict[str, Any]:
        """
        Create JSON template for correlation breakdown alert.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            correlation_data: Dictionary containing correlation analysis results
            
        Returns:
            Dict[str, Any]: Formatted correlation breakdown alert
        """
        try:
            # Validate input data
            if not self._validate_correlation_data(correlation_data):
                self.logger.error("Invalid correlation data provided")
                return {}
            
            # Check for duplicate alert
            severity = correlation_data.get('severity', 'low')
            if self._is_duplicate_alert('correlation_breakdown', pair, severity):
                self.logger.info(f"Duplicate breakdown alert suppressed for {pair}")
                return {}
            
            # Generate unique alert ID
            alert_id = self._generate_alert_id('breakdown', pair)
            
            # Calculate expiration time
            expiration_hours = self.default_config['alert_expiration_hours']['correlation_breakdown']
            expires_at = int((datetime.now() + timedelta(hours=expiration_hours)).timestamp() * 1000)
            
            alert = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "alert_type": "correlation_breakdown",
                "alert_id": alert_id,
                "pair": pair,
                "pair_type": self._determine_pair_type(pair),
                "breakdown_details": {
                    "current_correlation": float(correlation_data.get('current_correlation', 0.0)),
                    "historical_average_correlation": float(correlation_data.get('historical_average', 0.0)),
                    "z_score": float(correlation_data.get('z_score', 0.0)),
                    "significance_level": float(correlation_data.get('p_value', 0.0)),
                    "threshold_exceeded": bool(correlation_data.get('breakout_detected', False)),
                    "breakdown_direction": str(correlation_data.get('direction', 'none')),
                    "severity": str(correlation_data.get('severity', 'low')),
                    "duration_minutes": int(correlation_data.get('duration_minutes', 0))
                },
                "market_context": {
                    "asset1_price": float(correlation_data.get('asset1_price', 0.0)),
                    "asset1_24h_change": float(correlation_data.get('asset1_24h_change', 0.0)),
                    "asset2_price": float(correlation_data.get('asset2_price', 0.0)),
                    "asset2_24h_change": float(correlation_data.get('asset2_24h_change', 0.0)),
                    "market_volatility": str(correlation_data.get('market_volatility', 'normal'))
                },
                "statistical_analysis": {
                    "correlation_windows": dict(correlation_data.get('correlation_windows', {})),
                    "confidence_interval": dict(correlation_data.get('confidence_interval', {})),
                    "p_value": float(correlation_data.get('p_value', 0.0)),
                    "sample_size": int(correlation_data.get('sample_size', 0))
                },
                "recommended_actions": self._generate_recommended_actions(correlation_data),
                "alert_metadata": {
                    "severity": str(correlation_data.get('severity', 'low')),
                    "category": "correlation_analysis",
                    "expires_at": expires_at,
                    "related_pairs": list(correlation_data.get('related_pairs', []))
                }
            }
            
            self.logger.debug(f"Created breakdown alert template for {pair}: {alert_id}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Failed to create breakdown alert template: {e}")
            return {}
    
    def create_divergence_alert_template(self, pair: str, divergence_data: Dict) -> Dict[str, Any]:
        """
        Create JSON template for divergence signal alert.
        
        Args:
            pair: Asset pair name (e.g., 'BTC_ETH')
            divergence_data: Dictionary containing divergence analysis results
            
        Returns:
            Dict[str, Any]: Formatted divergence signal alert
        """
        try:
            # Validate divergence data
            if not self._validate_divergence_data(divergence_data):
                self.logger.error("Invalid divergence data provided")
                return {}
            
            # Check for duplicate alert
            severity = divergence_data.get('severity', 'medium')
            if self._is_duplicate_alert('divergence_signal', pair, severity):
                self.logger.info(f"Duplicate divergence alert suppressed for {pair}")
                return {}
            
            # Generate unique alert ID
            alert_id = self._generate_alert_id('divergence', pair)
            
            # Calculate expiration time
            expiration_hours = self.default_config['alert_expiration_hours']['divergence_signal']
            expires_at = int((datetime.now() + timedelta(hours=expiration_hours)).timestamp() * 1000)
            
            alert = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "alert_type": "divergence_signal",
                "alert_id": alert_id,
                "pair": pair,
                "pair_type": self._determine_pair_type(pair),
                "divergence_details": {
                    "divergence_type": str(divergence_data.get('divergence_type', 'unknown')),
                    "correlation_strength": float(divergence_data.get('correlation_strength', 0.0)),
                    "price_divergence": dict(divergence_data.get('price_divergence', {})),
                    "momentum_divergence": dict(divergence_data.get('momentum_divergence', {})),
                    "significance": str(divergence_data.get('significance', 'weak'))
                },
                "price_data": {
                    "asset1_price": float(divergence_data.get('asset1_price', 0.0)),
                    "asset2_price": float(divergence_data.get('asset2_price', 0.0)),
                    "asset1_24h_change": float(divergence_data.get('asset1_24h_change', 0.0)),
                    "asset2_24h_change": float(divergence_data.get('asset2_24h_change', 0.0)),
                    "correlation_24h": float(divergence_data.get('correlation_24h', 0.0))
                },
                "technical_indicators": {
                    "rsi_divergence": bool(divergence_data.get('rsi_divergence', False)),
                    "macd_divergence": bool(divergence_data.get('macd_divergence', False)),
                    "volume_confirmation": bool(divergence_data.get('volume_confirmation', False))
                },
                "recommended_actions": self._generate_divergence_actions(divergence_data),
                "alert_metadata": {
                    "severity": str(divergence_data.get('severity', 'medium')),
                    "category": "correlation_analysis",
                    "expires_at": expires_at,
                    "related_pairs": list(divergence_data.get('related_pairs', []))
                }
            }
            
            self.logger.debug(f"Created divergence alert template for {pair}: {alert_id}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Failed to create divergence alert template: {e}")
            return {}
    
    def create_mosaic_alert_template(self, mosaic_data: Dict) -> Dict[str, Any]:
        """
        Create JSON template for daily correlation mosaic alert.
        
        Args:
            mosaic_data: Dictionary containing mosaic analysis results
            
        Returns:
            Dict[str, Any]: Formatted daily mosaic alert
        """
        try:
            # Validate mosaic data
            if not self._validate_mosaic_data(mosaic_data):
                self.logger.error("Invalid mosaic data provided")
                return {}
            
            # Generate unique alert ID
            alert_id = self._generate_alert_id('mosaic', 'daily')
            
            # Calculate expiration time
            expiration_hours = self.default_config['alert_expiration_hours']['daily_correlation_mosaic']
            expires_at = int((datetime.now() + timedelta(hours=expiration_hours)).timestamp() * 1000)
            
            alert = {
                "timestamp": int(datetime.now().timestamp() * 1000),
                "alert_type": "daily_correlation_mosaic",
                "alert_id": alert_id,
                "date": datetime.now().strftime('%Y-%m-%d'),
                "mosaic_summary": {
                    "total_pairs_analyzed": int(mosaic_data.get('total_pairs', 0)),
                    "significant_correlations": int(mosaic_data.get('significant_correlations', 0)),
                    "breakdown_events": int(mosaic_data.get('breakdown_events', 0)),
                    "divergence_signals": int(mosaic_data.get('divergence_signals', 0)),
                    "average_correlation_strength": float(mosaic_data.get('average_correlation', 0.0))
                },
                "key_findings": list(mosaic_data.get('key_findings', [])),
                "file_locations": {
                    "json_report": str(mosaic_data.get('json_report_path', '')),
                    "html_report": str(mosaic_data.get('html_report_path', '')),
                    "heatmap_image": str(mosaic_data.get('heatmap_path', ''))
                },
                "alert_metadata": {
                    "severity": "info",
                    "category": "correlation_analysis",
                    "report_type": "daily_summary",
                    "expires_at": expires_at
                }
            }
            
            self.logger.debug(f"Created daily mosaic alert template: {alert_id}")
            return alert
            
        except Exception as e:
            self.logger.error(f"Failed to create mosaic alert template: {e}")
            return {}
    
    def _determine_pair_type(self, pair: str) -> str:
        """
        Determine the type of asset pair.
        
        Args:
            pair: Asset pair string
            
        Returns:
            str: Pair type ('crypto_crypto', 'crypto_macro', etc.)
        """
        pair_lower = pair.lower()
        
        # Use configurable macro indicators
        macro_indicators = self.default_config.get('macro_indicators', ['dxy', 'yield', 'spread', 'vix', 'gold', 'oil'])
        
        # Check if pair contains macro indicators
        for macro in macro_indicators:
            if macro in pair_lower:
                return 'crypto_macro'
        
        # Default to crypto-crypto
        return 'crypto_crypto'
    
    def _generate_recommended_actions(self, correlation_data: Dict) -> List[str]:
        """
        Generate recommended actions based on correlation breakdown.
        
        Args:
            correlation_data: Correlation analysis results
            
        Returns:
            List[str]: List of recommended actions
        """
        actions = []
        
        direction = correlation_data.get('direction', 'none')
        severity = correlation_data.get('severity', 'low')
        z_score = abs(correlation_data.get('z_score', 0))
        
        # Generate context-specific recommendations
        if direction == 'positive':
            if z_score > 2.5:
                actions.append("Strong positive correlation breakout detected")
                actions.append("Consider momentum-based trading strategies")
            else:
                actions.append("Monitor for potential trend convergence")
                actions.append("Consider correlation-based trading strategies")
        elif direction == 'negative':
            if z_score > 2.5:
                actions.append("Strong negative correlation breakdown detected")
                actions.append("Consider hedging strategies immediately")
            else:
                actions.append("Monitor for potential trend divergence")
                actions.append("Consider hedging strategies")
        
        if severity in ['high', 'extreme']:
            actions.append("High severity correlation change - monitor closely")
            actions.append("Watch for correlation normalization")
            actions.append("Consider position adjustments")
        elif severity == 'medium':
            actions.append("Moderate correlation change - monitor related pairs")
        
        actions.append("Monitor related asset pairs")
        
        return actions
    
    def _generate_divergence_actions(self, divergence_data: Dict) -> List[str]:
        """
        Generate recommended actions based on divergence signal.
        
        Args:
            divergence_data: Divergence analysis results
            
        Returns:
            List[str]: List of recommended actions
        """
        actions = []
        
        divergence_type = divergence_data.get('divergence_type', 'unknown')
        significance = divergence_data.get('significance', 'weak')
        correlation_strength = abs(divergence_data.get('correlation_strength', 0))
        
        # Generate context-specific recommendations
        if divergence_type == 'price_momentum':
            if significance == 'strong':
                actions.append("Strong price-momentum divergence detected")
                actions.append("High probability correlation breakdown imminent")
                actions.append("Consider immediate position adjustments")
            else:
                actions.append("Monitor for potential correlation breakdown")
                actions.append("Consider pair trading opportunities")
        elif divergence_type == 'price_divergence':
            if correlation_strength > 0.7:
                actions.append("Strong correlation with price divergence")
                actions.append("Consider mean reversion strategies")
            else:
                actions.append("Watch for momentum convergence")
                actions.append("Consider mean reversion strategies")
        elif divergence_type == 'momentum_divergence':
            actions.append("Momentum divergence detected")
            actions.append("Monitor for trend reversal signals")
        
        if significance == 'strong':
            actions.append("High probability divergence signal")
            actions.append("Consider immediate position adjustments")
        elif significance == 'weak':
            actions.append("Weak divergence signal - monitor for confirmation")
        
        actions.append("Monitor for divergence resolution")
        
        return actions
    
    def validate_alert_schema(self, alert: Dict[str, Any]) -> bool:
        """
        Validate alert schema for required fields and data types.
        
        Args:
            alert: Alert dictionary to validate
            
        Returns:
            bool: True if alert is valid
        """
        try:
            # Check required fields
            required_fields = ['timestamp', 'alert_type', 'alert_id']
            for field in required_fields:
                if field not in alert:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate timestamp
            if not isinstance(alert['timestamp'], int):
                self.logger.error("Timestamp must be integer")
                return False
            
            # Validate alert type
            valid_types = ['correlation_breakdown', 'divergence_signal', 'daily_correlation_mosaic']
            if alert['alert_type'] not in valid_types:
                self.logger.error(f"Invalid alert type: {alert['alert_type']}")
                return False
            
            # Validate alert ID format
            if not isinstance(alert['alert_id'], str) or len(alert['alert_id']) < 10:
                self.logger.error("Invalid alert ID format")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Alert validation failed: {e}")
            return False
    
    def format_alert_for_storage(self, alert: Dict[str, Any]) -> str:
        """
        Format alert for storage as JSON string.
        
        Args:
            alert: Alert dictionary
            
        Returns:
            str: Formatted JSON string
        """
        try:
            if not self.validate_alert_schema(alert):
                return ""
            
            return json.dumps(alert, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Failed to format alert for storage: {e}")
            return ""
