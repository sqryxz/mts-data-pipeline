from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class SignalType(Enum):
    """Enumeration for trading signal types"""
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


class SignalStrength(Enum):
    """Enumeration for signal strength levels"""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


@dataclass
class TradingSignal:
    """Data model for trading signals with risk management parameters"""
    
    # Core signal information
    asset: str                          # Asset identifier (e.g., "bitcoin", "ethereum")
    signal_type: SignalType            # LONG, SHORT, HOLD, CLOSE
    timestamp: int                     # Unix timestamp in milliseconds
    price: float                       # Entry price for the signal
    
    # Signal metadata
    strategy_name: str                 # Name of strategy that generated the signal
    signal_strength: SignalStrength    # WEAK, MODERATE, STRONG
    confidence: float                  # Confidence score (0.0 to 1.0)
    
    # Risk management parameters
    position_size: float               # Position size (percentage of portfolio, e.g., 0.02 = 2%)
    stop_loss: Optional[float] = None  # Stop loss price
    take_profit: Optional[float] = None # Take profit price
    max_risk: Optional[float] = None   # Maximum risk per trade (percentage)
    
    # Analysis context
    analysis_data: Optional[Dict[str, Any]] = None  # Supporting analysis data
    correlation_value: Optional[float] = None       # For correlation-based signals
    
    # Metadata
    signal_id: Optional[str] = None    # Unique identifier for the signal
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate fields after initialization"""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if self.position_size < 0.0 or self.position_size > 1.0:
            raise ValueError("Position size must be between 0.0 and 1.0")
        
        if self.price <= 0.0:
            raise ValueError("Price must be positive")
        
        if self.max_risk is not None and (self.max_risk <= 0.0 or self.max_risk > 1.0):
            raise ValueError("Max risk must be between 0.0 and 1.0")
        
        # Set created_at if not provided
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # Generate signal_id if not provided
        if self.signal_id is None:
            self.signal_id = f"{self.strategy_name}_{self.asset}_{self.timestamp}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary format for JSON serialization"""
        return {
            'signal_id': self.signal_id,
            'asset': self.asset,
            'signal_type': self.signal_type.value,
            'timestamp': self.timestamp,
            'price': self.price,
            'strategy_name': self.strategy_name,
            'signal_strength': self.signal_strength.value,
            'confidence': self.confidence,
            'position_size': self.position_size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'max_risk': self.max_risk,
            'analysis_data': self.analysis_data,
            'correlation_value': self.correlation_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingSignal':
        """Create TradingSignal from dictionary"""
        # Convert enum values
        signal_type = SignalType(data['signal_type'])
        signal_strength = SignalStrength(data['signal_strength'])
        
        # Convert datetime
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        return cls(
            signal_id=data.get('signal_id'),
            asset=data['asset'],
            signal_type=signal_type,
            timestamp=data['timestamp'],
            price=data['price'],
            strategy_name=data['strategy_name'],
            signal_strength=signal_strength,
            confidence=data['confidence'],
            position_size=data['position_size'],
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            max_risk=data.get('max_risk'),
            analysis_data=data.get('analysis_data'),
            correlation_value=data.get('correlation_value'),
            created_at=created_at
        )
    
    def to_datetime(self) -> datetime:
        """Convert timestamp to datetime object"""
        return datetime.fromtimestamp(self.timestamp / 1000)
    
    def calculate_risk_reward_ratio(self) -> Optional[float]:
        """Calculate risk/reward ratio if stop loss and take profit are set"""
        if self.stop_loss is None or self.take_profit is None:
            return None
        
        if self.signal_type == SignalType.LONG:
            risk = abs(self.price - self.stop_loss)
            reward = abs(self.take_profit - self.price)
        elif self.signal_type == SignalType.SHORT:
            risk = abs(self.stop_loss - self.price)
            reward = abs(self.price - self.take_profit)
        else:
            return None
        
        return reward / risk if risk > 0 else None 