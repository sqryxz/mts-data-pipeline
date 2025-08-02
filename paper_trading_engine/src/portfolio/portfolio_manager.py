"""
Portfolio Manager for tracking cash, positions, and portfolio value
"""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ..core.models import ExecutionResult, Trade, PortfolioState, Position
from ..core.enums import OrderSide
from ..analytics.performance_calculator import PerformanceCalculator, PerformanceMetrics


class InsufficientFundsError(Exception):
    """Raised when insufficient cash for trade"""
    pass


class PositionLimitExceededError(Exception):
    """Raised when position limit exceeded"""
    pass


class PortfolioManager:
    """
    Manages portfolio state, positions, and overall portfolio metrics
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        """Initialize portfolio manager"""
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.portfolio_history: List[Dict] = []
        
        # Performance tracking
        self.realized_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        
        # Performance calculator
        self.performance_calculator = PerformanceCalculator()
    
    def initialize(self):
        """Initialize portfolio with initial capital"""
        print(f"Portfolio initialized with {self.initial_capital} USDT")
        self._save_portfolio_snapshot()
    
    def process_execution(self, execution: ExecutionResult):
        """Process trade execution and update portfolio state"""
        
        try:
            # Store old values before updates for PnL calculation
            old_quantity = 0
            old_avg_price = 0
            if execution.asset in self.positions:
                old_quantity = self.positions[execution.asset].quantity
                old_avg_price = self.positions[execution.asset].average_price
            
            # Validate execution before processing
            self._validate_execution(execution)
            
            # Update position
            position = self._update_position(execution)
            
            # Update cash
            self._update_cash(execution)
            
            # Record trade with old values for correct PnL calculation
            trade = self._create_trade_record(execution, old_quantity, old_avg_price)
            self.trade_history.append(trade)
            
            # Update P&L tracking
            self._update_pnl_tracking(trade)
            
            # Save portfolio snapshot
            self._save_portfolio_snapshot()
            
            print(f"Portfolio updated - Cash: {self.cash:.2f}, Positions: {len(self.positions)}")
            
        except Exception as e:
            print(f"Error processing execution: {e}")
            raise
    
    def _update_pnl_tracking(self, trade: Trade):
        """Update P&L tracking metrics"""
        
        # Update realized P&L
        if trade.pnl != 0:
            self.realized_pnl += trade.pnl
            
            # Update win/loss counts
            if trade.pnl > 0:
                self.win_count += 1
            elif trade.pnl < 0:
                self.loss_count += 1
    
    def _update_position(self, execution: ExecutionResult) -> Optional[Position]:
        """Update position based on execution"""
        
        asset = execution.asset
        
        # Get or create position
        if asset not in self.positions:
            position = Position(asset=asset)
            self.positions[asset] = position
        else:
            position = self.positions[asset]
        
        # Store old quantity BEFORE updating for correct average price calculation
        old_quantity = position.quantity
        
        # Update quantity
        if execution.side == OrderSide.BUY:
            position.quantity += execution.quantity
        else:
            position.quantity -= execution.quantity
        
        # Update average price with correct old_quantity
        self._update_average_price(position, execution, old_quantity)
        
        # Remove position if quantity is zero
        if self._is_zero_quantity(position.quantity, asset):
            del self.positions[asset]
            return None
        
        return position
    
    def _update_average_price(self, position: Position, execution: ExecutionResult, old_quantity: float):
        """Update average price for position"""
        
        # New position
        if old_quantity == 0:
            position.average_price = execution.execution_price
            return
        
        # Position will be closed - keep existing average
        if abs(position.quantity) < 1e-8:
            return
        
        # Same direction trade (increasing position size)
        if (old_quantity > 0 and execution.side == OrderSide.BUY) or \
           (old_quantity < 0 and execution.side == OrderSide.SELL):
            total_cost = abs(old_quantity) * position.average_price + \
                        execution.quantity * execution.execution_price
            position.average_price = total_cost / abs(position.quantity)
        
        # Position reversal
        elif (old_quantity > 0 and position.quantity < 0) or \
             (old_quantity < 0 and position.quantity > 0):
            position.average_price = execution.execution_price
    
    def _validate_execution(self, execution: ExecutionResult):
        """Validate execution before processing"""
        
        # Input validation
        if execution.execution_price <= 0:
            raise ValueError(f"Invalid execution price: {execution.execution_price}")
        if execution.quantity <= 0:
            raise ValueError(f"Invalid quantity: {execution.quantity}")
        
        # Validate cash requirement for buy orders
        if execution.side == OrderSide.BUY:
            required_cash = execution.quantity * execution.execution_price + execution.fees
            if self.cash < required_cash:
                raise InsufficientFundsError(
                    f"Insufficient funds. Required: {required_cash:.2f}, Available: {self.cash:.2f}"
                )
        
        # Validate position limits (10% max per position)
        current_quantity = 0
        if execution.asset in self.positions:
            current_quantity = self.positions[execution.asset].quantity
        
        if execution.side == OrderSide.BUY:
            new_quantity = current_quantity + execution.quantity
            position_value = abs(new_quantity * execution.execution_price)
        else:  # SELL
            new_quantity = current_quantity - execution.quantity
            # Only check position limits if going short (negative quantity)
            if new_quantity < 0:
                position_value = abs(new_quantity * execution.execution_price)
            else:
                position_value = 0  # Not creating a short position
        
        # Use initial capital for position limits to avoid circular dependency
        max_position_value = self.initial_capital * 0.1
        
        if position_value > max_position_value:
            position_type = "long" if execution.side == OrderSide.BUY else "short"
            raise PositionLimitExceededError(
                f"{position_type.title()} position would exceed 10% limit. Value: {position_value:.2f}, Limit: {max_position_value:.2f}"
            )
    
    def _is_zero_quantity(self, quantity: float, asset: str) -> bool:
        """Check if quantity is effectively zero for the asset"""
        # Use asset-specific precision (8 for crypto, 2 for stocks)
        precision = 8 if asset in ['BTC', 'ETH'] else 2
        return abs(quantity) < (10 ** -precision)
    
    def _update_cash(self, execution: ExecutionResult):
        """Update cash balance based on execution"""
        if execution.side == OrderSide.BUY:
            # Buying costs money
            cost = execution.quantity * execution.execution_price + execution.fees
            self.cash -= cost
        else:
            # Selling generates money
            proceeds = execution.quantity * execution.execution_price - execution.fees
            self.cash += proceeds
    
    def _create_trade_record(self, execution: ExecutionResult, old_quantity: float, old_avg_price: float) -> Trade:
        """Create trade record from execution with enhanced PnL calculation"""
        
        # Calculate PnL using old values for accuracy
        pnl = 0.0
        
        if execution.side == OrderSide.SELL and old_quantity > 0:
            # Selling long position - calculate PnL for the portion that closes long position
            closing_quantity = min(execution.quantity, old_quantity)
            pnl = closing_quantity * (execution.execution_price - old_avg_price)
            
        elif execution.side == OrderSide.BUY and old_quantity < 0:
            # Covering short position - calculate PnL for the portion that closes short position
            closing_quantity = min(execution.quantity, abs(old_quantity))
            pnl = closing_quantity * (old_avg_price - execution.execution_price)
        
        return Trade(
            asset=execution.asset,
            side=execution.side,
            quantity=execution.quantity,
            entry_price=execution.execution_price,
            exit_price=execution.execution_price if execution.side == OrderSide.SELL else None,
            pnl=pnl,
            fees=execution.fees,
            timestamp=execution.timestamp,
            signal_id="",  # Will be set from order
            order_id=execution.order_id,
            execution_id=execution.id
        )
    
    def get_total_value(self) -> float:
        """Calculate total portfolio value"""
        positions_value = 0.0
        for pos in self.positions.values():
            if pos.current_price is None or pos.current_price <= 0:
                # Use average price as fallback
                positions_value += pos.quantity * pos.average_price
            else:
                positions_value += pos.quantity * pos.current_price
        return self.cash + positions_value
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """Update current prices for positions and calculate unrealized P&L"""
        
        for asset, current_price in current_prices.items():
            if asset in self.positions:
                position = self.positions[asset]
                position.current_price = current_price
                
                # Calculate unrealized P&L for this position
                if position.quantity > 0:  # Long position
                    position.unrealized_pnl = position.quantity * (current_price - position.average_price)
                elif position.quantity < 0:  # Short position
                    position.unrealized_pnl = abs(position.quantity) * (position.average_price - current_price)
                else:
                    position.unrealized_pnl = 0.0
    
    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L for all open positions"""
        return sum(getattr(pos, 'unrealized_pnl', 0.0) for pos in self.positions.values())
    
    def get_win_rate(self) -> float:
        """Calculate win rate based on profitable trades"""
        total_trades = self.win_count + self.loss_count
        if total_trades == 0:
            return 0.0
        return self.win_count / total_trades
    
    def get_state(self) -> PortfolioState:
        """Get current portfolio state"""
        unrealized_pnl = self.get_unrealized_pnl()
        win_rate = self.get_win_rate()
        
        return PortfolioState(
            timestamp=datetime.now(),
            initial_capital=self.initial_capital,
            cash=self.cash,
            positions={
                asset: {
                    'quantity': pos.quantity,
                    'average_price': pos.average_price,
                    'current_price': pos.current_price or pos.average_price,
                    'unrealized_pnl': getattr(pos, 'unrealized_pnl', 0.0)
                } for asset, pos in self.positions.items()
            },
            total_value=self.get_total_value(),
            total_pnl=self.realized_pnl + unrealized_pnl,  # Total P&L = realized + unrealized
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized_pnl,
            trade_count=len(self.trade_history),
            win_count=self.win_count,
            loss_count=self.loss_count,
            win_rate=win_rate
        )
    
    def _save_portfolio_snapshot(self):
        """Save current portfolio state to history"""
        state = self.get_state()
        self.portfolio_history.append({
            'timestamp': state.timestamp.isoformat(),
            'total_value': state.total_value,
            'cash': state.cash,
            'total_pnl': state.total_pnl,
            'realized_pnl': state.realized_pnl,
            'unrealized_pnl': state.unrealized_pnl,
            'trade_count': state.trade_count,
            'win_rate': state.win_rate
        })
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics"""
        return self.performance_calculator.calculate_metrics(self)
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary report"""
        metrics = self.get_performance_metrics()
        return self.performance_calculator.generate_summary_report(metrics)
    
    def get_basic_metrics(self) -> Dict[str, float]:
        """Calculate key performance metrics"""
        total_value = self.get_total_value()
        total_return = (total_value - self.initial_capital) / self.initial_capital
        
        # Calculate average trade P&L
        avg_trade_pnl = 0.0
        largest_win = 0.0
        largest_loss = 0.0
        
        if self.trade_history:
            pnls = [trade.pnl for trade in self.trade_history]
            avg_trade_pnl = sum(pnls) / len(pnls)
            largest_win = max(pnls) if pnls else 0.0
            largest_loss = min(pnls) if pnls else 0.0
        
        return {
            'total_return': total_return,
            'total_value': total_value,
            'cash_ratio': self.cash / total_value,
            'position_count': len(self.positions),
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.get_unrealized_pnl(),
            'win_rate': self.get_win_rate(),
            'trade_count': len(self.trade_history),
            'avg_trade_pnl': avg_trade_pnl,
            'largest_win': largest_win,
            'largest_loss': largest_loss
        } 