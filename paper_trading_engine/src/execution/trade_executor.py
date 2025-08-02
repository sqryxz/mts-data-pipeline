"""
Trade execution simulation
"""

import random
from datetime import datetime
from typing import Dict, Optional

from ..core.models import Order, ExecutionResult
from ..core.enums import OrderType, OrderSide
from ..services.market_data_service import MarketDataService


class TradeExecutor:
    """Simulates trade execution with slippage and fees"""
    
    # Configuration constants
    SLIPPAGE_SIZE_THRESHOLD = 1000000  # $1M threshold for size impact
    SLIPPAGE_VOLATILITY_FACTOR = 0.5   # 50% of volatility as slippage
    DEFAULT_FEE_RATE = 0.001           # 0.1% fee
    MAX_SLIPPAGE = 0.01                # 1% max slippage
    BASE_SPREAD = 0.001                # 0.1% base spread
    
    def __init__(self):
        self.slippage_model = SlippageModel()
        self.execution_cost_model = ExecutionCostModel()
        self.market_data = MarketDataService()
    
    def execute_order(self, order: Order, current_market_price: Optional[float] = None) -> ExecutionResult:
        """Execute a trade order with realistic market simulation"""
        
        try:
            # Get current market price if not provided
            if current_market_price is None:
                current_market_price = self.market_data.get_current_price(order.asset)
            
            # Determine execution price based on order type
            if order.order_type == OrderType.MARKET:
                # Market order: use current market price
                base_price = current_market_price
            else:
                # Limit order: use order price (if market reaches it)
                base_price = order.price
            
            # Validate execution price
            if base_price <= 0:
                return ExecutionResult(
                    order_id=order.id,
                    asset=order.asset,
                    side=order.side,
                    quantity=0.0,
                    execution_price=0.0,
                    fees=0.0,
                    slippage=0.0,
                    timestamp=datetime.now(),
                    success=False,
                    error="Invalid execution price"
                )
            
            # Get market conditions for this asset
            market_conditions = self.market_data.get_market_conditions(order.asset)
            
            # Calculate slippage
            slippage = self.slippage_model.calculate_slippage(order, base_price, market_conditions)
            
            # Calculate execution price with slippage
            execution_price = self._calculate_execution_price(base_price, slippage, order.side)
            
            # Calculate fees
            fees = self.execution_cost_model.calculate_fees(order, execution_price)
            
            # Create execution result
            return ExecutionResult(
                order_id=order.id,
                asset=order.asset,
                side=order.side,
                quantity=order.quantity,
                execution_price=execution_price,
                fees=fees,
                slippage=slippage,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            return ExecutionResult(
                order_id=order.id,
                asset=order.asset,
                side=order.side,
                quantity=0.0,
                execution_price=0.0,
                fees=0.0,
                slippage=0.0,
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
    
    def _calculate_execution_price(self, base_price: float, slippage: float, side: OrderSide) -> float:
        """Calculate execution price with slippage"""
        if side == OrderSide.BUY:
            return base_price * (1 + slippage)  # Buy at higher price
        else:
            return base_price * (1 - slippage)  # Sell at lower price


class SlippageModel:
    """Models slippage based on order size and market conditions"""
    
    def calculate_slippage(self, order: Order, base_price: float, market_conditions: Dict[str, float]) -> float:
        """Calculate slippage using additive model (more realistic)"""
        
        # Base slippage from spread
        base_slippage = market_conditions.get('spread', 0.001)
        
        # Size impact (additive, not multiplicative)
        order_value = order.quantity * base_price
        size_impact = min(order_value / 1000000, 0.005)  # Max 0.5% size impact
        
        # Volatility impact (additive)
        volatility = market_conditions.get('volatility', 0.02)
        volatility_impact = volatility * 0.5  # 50% of volatility as slippage
        
        # Liquidity impact
        liquidity = market_conditions.get('liquidity', 'medium')
        liquidity_multiplier = {
            'high': 1.0,
            'medium': 1.5,
            'low': 2.0
        }.get(liquidity, 1.5)
        
        # Total slippage (additive model)
        total_slippage = (base_slippage + size_impact + volatility_impact) * liquidity_multiplier
        
        # Cap at maximum slippage
        return min(total_slippage, 0.01)  # Cap at 1%


class ExecutionCostModel:
    """Models execution costs (fees, etc.)"""
    
    def calculate_fees(self, order: Order, execution_price: float) -> float:
        """Calculate trading fees"""
        trade_value = order.quantity * execution_price
        fee_rate = 0.001  # 0.1% fee
        return trade_value * fee_rate 