"""
Core data models for the Paper Trading Engine
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

from .enums import SignalType, OrderType, OrderSide


@dataclass
class TradingSignal:
    """Trading signal from MTS pipeline"""
    asset: str
    signal_type: SignalType
    price: float
    confidence: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Order:
    """Trading order"""
    asset: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: float
    timestamp: datetime
    signal_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ExecutionResult:
    """Result of trade execution"""
    order_id: str
    asset: str
    side: OrderSide
    quantity: float
    execution_price: float
    fees: float
    slippage: float
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Position:
    """Portfolio position"""
    asset: str
    quantity: float = 0.0
    average_price: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Current market value of position"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis of position"""
        return self.quantity * self.average_price


@dataclass  
class Trade:
    """Completed trade record"""
    asset: str
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    pnl: float
    fees: float
    timestamp: datetime
    signal_id: str
    order_id: str
    execution_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class PortfolioState:
    """Portfolio state snapshot"""
    timestamp: datetime
    initial_capital: float
    cash: float
    positions: Dict[str, Dict[str, float]]
    total_value: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: float