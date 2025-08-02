"""
Order Manager for generating orders from signals
"""

from datetime import datetime
from typing import Optional

from ..core.models import Order, TradingSignal
from ..core.enums import OrderType, OrderSide, SignalType
from ..portfolio.portfolio_manager import PortfolioManager
from ..services.market_data_service import MarketDataService


class OrderManager:
    """
    Generates and manages trading orders based on signals
    """
    
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.position_sizer = PositionSizer()
        self.order_validator = OrderValidator()
        self.market_data = MarketDataService()
    
    def generate_order(self, signal: TradingSignal) -> Optional[Order]:
        """Generate order from trading signal"""
        
        try:
            # Get current market price for position sizing
            current_price = self.market_data.get_current_price(signal.asset)
            
            # Calculate position size based on portfolio value
            portfolio_value = self.portfolio_manager.get_total_value()
            position_size = self.position_sizer.calculate_size(
                signal, portfolio_value, current_price
            )
            
            # Get current position quantity
            current_quantity = 0
            if signal.asset in self.portfolio_manager.positions:
                current_quantity = self.portfolio_manager.positions[signal.asset].quantity
            
            # Calculate target quantity based on signal type
            if signal.signal_type == SignalType.LONG:
                target_quantity = position_size  # position_size is already in quantity
            elif signal.signal_type == SignalType.SHORT:
                target_quantity = -position_size  # Negative for short
            elif signal.signal_type == SignalType.EXIT:
                target_quantity = 0  # Close position
            else:
                print(f"Unknown signal type: {signal.signal_type}")
                return None
            
            # Apply confidence adjustment
            target_quantity *= signal.confidence
            
            # Calculate order quantity (difference between target and current)
            order_quantity = abs(target_quantity - current_quantity)
            
            # Check minimum order size
            MIN_ORDER_VALUE = 10.0  # $10 minimum
            order_value = order_quantity * current_price
            if order_value < MIN_ORDER_VALUE:
                print(f"Order too small: ${order_value:.2f} < ${MIN_ORDER_VALUE}")
                return None
            
            # Check if order quantity is effectively zero
            if order_quantity < 1e-8:
                print(f"Order quantity too small: {order_quantity}")
                return None
            
            # Determine order side
            if signal.signal_type == SignalType.LONG:
                order_side = OrderSide.BUY
            elif signal.signal_type == SignalType.SHORT:
                order_side = OrderSide.SELL
            elif signal.signal_type == SignalType.EXIT:
                order_side = OrderSide.SELL  # Close position
            else:
                print(f"Unknown signal type: {signal.signal_type}")
                return None
            
            # Create order (market order with price=None)
            order = Order(
                asset=signal.asset,
                order_type=OrderType.MARKET,
                side=order_side,
                quantity=order_quantity,
                price=None,  # Market order
                timestamp=signal.timestamp,
                signal_id=signal.id,
                metadata={'validation_price': current_price}
            )
            
            # Validate order
            if not self.order_validator.validate(order, self.portfolio_manager, current_price):
                print(f"Order validation failed for {signal.asset}")
                return None
            
            print(f"Generated order: {order.side} {order.quantity} {order.asset} @ {order.price}")
            return order
            
        except Exception as e:
            print(f"Error generating order: {e}")
            return None
    



class PositionSizer:
    """
    Calculates position sizes based on portfolio value and risk parameters
    """
    
    def calculate_size(self, signal: TradingSignal, portfolio_value: float, 
                      current_price: float, target_percentage: float = 0.02) -> float:
        """Calculate position size based on target percentage of portfolio using current market price"""
        
        try:
            # Calculate target position value
            target_value = portfolio_value * target_percentage
            
            # Calculate quantity based on current market price
            quantity = target_value / current_price
            
            # Apply confidence adjustment (reduce size if confidence is low)
            if signal.confidence < 0.7:
                quantity *= signal.confidence  # Reduce size for low confidence signals
            
            return quantity
            
        except ZeroDivisionError:
            print(f"Error: Current price is zero for {signal.asset}")
            return 0


class OrderValidator:
    """
    Validates orders before execution
    """
    
    def validate(self, order: Order, portfolio_manager: PortfolioManager, current_price: float) -> bool:
        """Validate order before execution"""
        
        try:
            # Basic validation
            if order.quantity <= 0:
                print(f"Invalid quantity: {order.quantity}")
                return False
            
            if current_price <= 0:
                print(f"Invalid current price: {current_price}")
                return False
            
            # Check minimum order size
            MIN_ORDER_VALUE = 10.0  # $10 minimum
            order_value = order.quantity * current_price
            if order_value < MIN_ORDER_VALUE:
                print(f"Order value too small. Value: {order_value:.2f}, Minimum: {MIN_ORDER_VALUE}")
                return False
            
            # Estimate fees (0.1% of trade value)
            estimated_fees = order.quantity * current_price * 0.001
            
            # Check cash requirements for buy orders
            if order.side == OrderSide.BUY:
                required_cash = order.quantity * current_price + estimated_fees
                if portfolio_manager.cash < required_cash:
                    print(f"Insufficient cash. Required: {required_cash:.2f}, Available: {portfolio_manager.cash:.2f}")
                    return False
            
            # Check position limits and short selling validation
            current_quantity = 0
            if order.asset in portfolio_manager.positions:
                current_quantity = portfolio_manager.positions[order.asset].quantity
            
            # Calculate new position size
            if order.side == OrderSide.BUY:
                new_quantity = current_quantity + order.quantity
            else:  # SELL
                new_quantity = current_quantity - order.quantity
                
                # Check if this is a short sale (selling more than we have)
                if order.quantity > current_quantity:
                    short_quantity = order.quantity - current_quantity
                    short_fees = short_quantity * current_price * 0.001
                    required_margin = short_quantity * current_price * 0.5 + short_fees  # 50% margin + fees
                    if portfolio_manager.cash < required_margin:
                        print(f"Insufficient margin for short sale. Required: {required_margin:.2f}, Available: {portfolio_manager.cash:.2f}")
                        return False
            
            # Check position limits (10% max per position) - distinguish long and short
            if new_quantity >= 0:
                # Long position
                position_value = new_quantity * current_price
                position_type = "long"
            else:
                # Short position
                position_value = abs(new_quantity) * current_price
                position_type = "short"
            
            max_position_value = portfolio_manager.get_total_value() * 0.1
            
            if position_value > max_position_value:
                print(f"{position_type.title()} position would exceed 10% limit. Value: {position_value:.2f}, Limit: {max_position_value:.2f}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating order: {e}")
            return False 