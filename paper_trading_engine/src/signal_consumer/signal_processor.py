"""
Signal processing and conversion for MTS alerts
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from src.core.models import TradingSignal
from src.core.enums import SignalType
from src.utils.logger import get_logger

logger = get_logger('signal_consumer.processor')


class SignalProcessor:
    """Processes and converts MTS alerts to TradingSignal objects"""
    
    # Class constants for confidence calculation
    BASE_CONFIDENCE = 0.5
    MAX_VOLATILITY_BONUS = 0.5
    MAX_THRESHOLD_BONUS = 0.2
    THRESHOLD_MULTIPLIER = 0.1
    DEFAULT_CONFIDENCE = 0.5
    
    # Required fields for alert validation
    REQUIRED_FIELDS = [
        'asset', 'signal_type', 'timestamp', 'current_price',
        'volatility_value', 'volatility_threshold', 'volatility_percentile'
    ]
    
    def __init__(self):
        self.asset_mapping = {
            'bitcoin': 'BTCUSDT',
            'ethereum': 'ETHUSDT',
            'btcusdt': 'BTCUSDT',
            'ethusdt': 'ETHUSDT',
            'ethena': 'ENAUSDT',
            'enausdt': 'ENAUSDT'
        }
    
    def process_volatility_alert(self, alert_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Convert MTS volatility alert to TradingSignal
        
        Args:
            alert_data: Validated MTS alert data
            
        Returns:
            TradingSignal object or None if processing fails
        """
        try:
            # Validate required fields
            if not self._validate_required_fields(alert_data):
                return None
            
            # Validate numeric fields
            if not self._validate_numeric_fields(alert_data):
                return None
            
            # Map asset name to trading pair
            asset = self.asset_mapping.get(alert_data['asset'].lower())
            if not asset:
                logger.error(f"Unsupported asset: {alert_data['asset']}")
                return None
            
            # Convert signal type with validation
            signal_type = self._convert_signal_type(alert_data['signal_type'])
            if not signal_type:
                return None
            
            # Convert timestamp with timezone (milliseconds to UTC datetime)
            timestamp = self._convert_timestamp(alert_data['timestamp'])
            if not timestamp:
                return None
            
            # Calculate confidence based on volatility percentile
            confidence = self._calculate_confidence(alert_data)
            
            # Create TradingSignal
            signal = TradingSignal(
                asset=asset,
                signal_type=signal_type,
                price=float(alert_data['current_price']),
                confidence=confidence,
                timestamp=timestamp,
                source='mts_volatility',
                metadata={
                    'volatility_value': alert_data['volatility_value'],
                    'volatility_threshold': alert_data['volatility_threshold'],
                    'volatility_percentile': alert_data['volatility_percentile'],
                    'position_direction': alert_data.get('position_direction', 'UNKNOWN'),
                    'alert_type': alert_data.get('alert_type', 'volatility_spike'),
                    'threshold_exceeded': alert_data.get('threshold_exceeded', True),
                    'original_asset': alert_data['asset']
                }
            )
            
            logger.info(f"Processed volatility alert: {asset} {signal_type.value} @ ${alert_data['current_price']:.2f}")
            logger.debug(f"Signal confidence: {confidence:.3f}, volatility: {alert_data['volatility_value']:.3f}")
            
            return signal
            
        except KeyError as e:
            logger.error(f"Missing required field in alert data: {e}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid data type in alert: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing volatility alert: {e}")
            return None
    
    def _calculate_confidence(self, alert_data: Dict[str, Any]) -> float:
        """
        Calculate signal confidence based on alert data
        
        Args:
            alert_data: MTS alert data
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Normalize volatility percentile to 0-1 range
            volatility_pct = alert_data['volatility_percentile']
            if volatility_pct > 1:
                volatility_pct = volatility_pct / 100  # Convert 0-100 to 0-1
            
            # Base confidence from volatility percentile
            base_confidence = self.BASE_CONFIDENCE + (volatility_pct * self.MAX_VOLATILITY_BONUS)
            
            # Adjust based on how much threshold was exceeded (with division by zero protection)
            volatility_threshold = alert_data['volatility_threshold']
            if volatility_threshold == 0:
                logger.warning("Volatility threshold is zero, using default ratio")
                volatility_ratio = 1.0
            else:
                volatility_ratio = alert_data['volatility_value'] / volatility_threshold
            
            # Calculate threshold bonus (up to MAX_THRESHOLD_BONUS)
            threshold_bonus = min(
                self.MAX_THRESHOLD_BONUS, 
                max(0, (volatility_ratio - 1.0) * self.THRESHOLD_MULTIPLIER)
            )
            
            # Final confidence (capped at 1.0)
            confidence = min(1.0, base_confidence + threshold_bonus)
            
            return round(confidence, 3)
            
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error calculating confidence: {e}")
            return self.DEFAULT_CONFIDENCE
        except Exception as e:
            logger.error(f"Unexpected error calculating confidence: {e}")
            return self.DEFAULT_CONFIDENCE
    
    def process_signal_alert(self, alert_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Process other types of MTS signals (future expansion)
        
        Args:
            alert_data: MTS alert data
            
        Returns:
            TradingSignal object or None
        """
        logger.info("Generic signal processing not yet implemented")
        return None
    
    def validate_and_process(self, alert_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Main processing entry point - validates then processes alert
        
        Args:
            alert_data: Raw MTS alert data
            
        Returns:
            TradingSignal object or None if validation/processing fails
        """
        try:
            # Determine alert type and process accordingly
            alert_type = alert_data.get('alert_type', '')
            
            if alert_type == 'volatility_spike':
                return self.process_volatility_alert(alert_data)
            else:
                logger.warning(f"Unsupported alert type: {alert_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error in validate_and_process: {e}")
            return None
    
    def _validate_required_fields(self, alert_data: Dict[str, Any]) -> bool:
        """Validate that all required fields are present"""
        missing_fields = [field for field in self.REQUIRED_FIELDS if field not in alert_data]
        if missing_fields:
            logger.error(f"Missing required fields: {missing_fields}")
            return False
        return True
    
    def _validate_numeric_fields(self, alert_data: Dict[str, Any]) -> bool:
        """Validate that numeric fields contain valid numbers"""
        try:
            # Validate timestamp
            timestamp = alert_data['timestamp']
            if not isinstance(timestamp, (int, float)) or timestamp <= 0:
                logger.error(f"Invalid timestamp: {timestamp}")
                return False
            
            # Validate price
            price = alert_data['current_price']
            if not isinstance(price, (int, float)) or price <= 0:
                logger.error(f"Invalid current_price: {price}")
                return False
            
            # Validate volatility values
            volatility_value = alert_data['volatility_value']
            if not isinstance(volatility_value, (int, float)) or volatility_value < 0:
                logger.error(f"Invalid volatility_value: {volatility_value}")
                return False
            
            volatility_threshold = alert_data['volatility_threshold']
            if not isinstance(volatility_threshold, (int, float)) or volatility_threshold < 0:
                logger.error(f"Invalid volatility_threshold: {volatility_threshold}")
                return False
            
            volatility_percentile = alert_data['volatility_percentile']
            if not isinstance(volatility_percentile, (int, float)) or volatility_percentile < 0:
                logger.error(f"Invalid volatility_percentile: {volatility_percentile}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating numeric fields: {e}")
            return False
    
    def _convert_signal_type(self, signal_type_str: str) -> Optional[SignalType]:
        """Convert string signal type to SignalType enum"""
        try:
            if signal_type_str == 'LONG':
                return SignalType.LONG
            elif signal_type_str == 'SHORT':
                return SignalType.SHORT
            else:
                logger.error(f"Invalid signal type: {signal_type_str}")
                return None
        except Exception as e:
            logger.error(f"Error converting signal type: {e}")
            return None
    
    def _convert_timestamp(self, timestamp_ms: float) -> Optional[datetime]:
        """Convert millisecond timestamp to UTC datetime"""
        try:
            # Convert milliseconds to seconds and create UTC datetime
            timestamp_seconds = timestamp_ms / 1000
            return datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Error converting timestamp {timestamp_ms}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error converting timestamp: {e}")
            return None