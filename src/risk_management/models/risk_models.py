"""
Core data models for risk management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class SignalType(Enum):
    """Trading signal types."""
    LONG = "LONG"
    SHORT = "SHORT"


class RiskLevel(Enum):
    """Risk levels for assessments."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class TradingSignal:
    """Represents a trading signal."""
    signal_id: str
    asset: str
    signal_type: SignalType
    price: float
    confidence: float = 0.7  # More conservative default
    timestamp: datetime = field(default_factory=datetime.now)
    take_profit_price: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PortfolioState:
    """Represents the current portfolio state."""
    total_equity: float
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    cash: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment for a trading signal."""
    signal_id: str
    asset: str
    signal_type: SignalType
    signal_price: float  # Added missing field
    signal_confidence: float  # Added missing field
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Position sizing
    recommended_position_size: float = 0.0
    position_size_method: str = ""
    
    # Risk management
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    
    # Risk metrics
    risk_reward_ratio: float = 0.0
    position_risk_percent: float = 0.0
    portfolio_heat: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW  # Use the enum
    
    # Validation results
    is_approved: bool = False
    rejection_reason: Optional[str] = None
    risk_warnings: List[str] = field(default_factory=list)
    
    # Market conditions
    market_volatility: float = 0.0
    correlation_risk: float = 0.0
    
    # Portfolio impact
    portfolio_impact: Dict[str, Any] = field(default_factory=dict)
    current_drawdown: float = 0.0
    daily_pnl_impact: float = 0.0
    
    # Configuration used
    risk_config_snapshot: Dict[str, Any] = field(default_factory=dict)
    
    # Processing metadata
    processing_time_ms: float = 0.0 