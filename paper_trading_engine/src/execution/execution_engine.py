"""
Execution engine for processing trading signals
"""

import logging
import time
from datetime import datetime
from typing import Optional

from ..core.models import TradingSignal, ExecutionResult
from ..core.enums import SignalType
from ..portfolio.portfolio_manager import PortfolioManager
from .order_manager import OrderManager
from .trade_executor import TradeExecutor
from ..services.market_data_service import MarketDataService


class ExecutionEngine:
    """Orchestrates the execution of trading signals"""
    
    def __init__(self, portfolio_manager: PortfolioManager):
        self.portfolio_manager = portfolio_manager
        self.order_manager = OrderManager(portfolio_manager)
        self.trade_executor = TradeExecutor()
        self.market_data = MarketDataService()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Track processed signals to prevent duplicates
        self.processed_signals = set()
        
        # Execution metrics
        self.execution_stats = {
            'signals_processed': 0,
            'orders_executed': 0,
            'execution_failures': 0,
            'total_slippage': 0.0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0
        }
    
    def process_signal(self, signal: TradingSignal) -> Optional[ExecutionResult]:
        """Process a trading signal through the execution pipeline"""
        
        start_time = time.time()
        
        try:
            # Validate signal first
            if not self._validate_signal(signal):
                return None
            
            # Check for duplicate signals
            signal_id = f"{signal.asset}_{signal.timestamp}_{signal.signal_type}"
            if signal_id in self.processed_signals:
                self.logger.warning(f"Duplicate signal ignored: {signal_id}")
                return None
            
            self.logger.info(f"Processing signal: {signal.asset} {signal.signal_type} @ {signal.price}")
            
            # Generate order from signal
            order = self.order_manager.generate_order(signal)
            if order is None:
                self.logger.warning(f"No order generated for signal: {signal.asset}")
                return None
            
            # Get current market price for execution
            current_market_price = self.market_data.get_current_price(signal.asset, signal.timestamp)
            
            # Execute the order
            execution_result = self.trade_executor.execute_order(order, current_market_price)
            
            if execution_result.success:
                # Update portfolio with execution result
                self.portfolio_manager.process_execution(execution_result)
                
                # Update execution metrics
                self._update_execution_metrics(execution_result, time.time() - start_time)
                
                # Track processed signal
                self.processed_signals.add(signal_id)
                
                self.logger.info(f"Trade executed successfully: {execution_result.asset} {execution_result.side} "
                               f"{execution_result.quantity} @ {execution_result.execution_price}")
            else:
                self.logger.error(f"Trade execution failed: {execution_result.error}")
                self.execution_stats['execution_failures'] += 1
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Error processing signal: {e}")
            self.execution_stats['execution_failures'] += 1
            return None
    
    def _validate_signal(self, signal: TradingSignal) -> bool:
        """Validate signal before processing"""
        
        # Check signal age (reject stale signals)
        signal_age = datetime.now() - signal.timestamp
        if signal_age.total_seconds() > 300:  # 5 minutes max age
            self.logger.warning(f"Signal too old: {signal_age.total_seconds()}s")
            return False
        
        # Check price validity
        if signal.price <= 0:
            self.logger.warning(f"Invalid signal price: {signal.price}")
            return False
        
        # Check asset validity
        if not signal.asset or not self.market_data.validate_asset(signal.asset):
            self.logger.warning(f"Invalid asset: {signal.asset}")
            return False
        
        # Check confidence validity
        if not (0.0 <= signal.confidence <= 1.0):
            self.logger.warning(f"Invalid confidence: {signal.confidence}")
            return False
        
        # Check signal type validity
        if signal.signal_type not in [SignalType.LONG, SignalType.SHORT, SignalType.EXIT]:
            self.logger.warning(f"Invalid signal type: {signal.signal_type}")
            return False
        
        return True
    
    def _update_execution_metrics(self, execution_result: ExecutionResult, execution_time: float):
        """Update execution statistics"""
        
        self.execution_stats['signals_processed'] += 1
        self.execution_stats['orders_executed'] += 1
        self.execution_stats['total_slippage'] += execution_result.slippage
        self.execution_stats['total_execution_time'] += execution_time
        
        # Update average execution time
        if self.execution_stats['orders_executed'] > 0:
            self.execution_stats['avg_execution_time'] = (
                self.execution_stats['total_execution_time'] / self.execution_stats['orders_executed']
            )
    
    def get_execution_summary(self) -> dict:
        """Get summary of execution engine state"""
        
        portfolio_state = self.portfolio_manager.get_state()
        
        # Calculate success rate
        total_attempts = self.execution_stats['orders_executed'] + self.execution_stats['execution_failures']
        success_rate = (self.execution_stats['orders_executed'] / total_attempts * 100) if total_attempts > 0 else 0
        
        # Calculate average slippage
        avg_slippage = (self.execution_stats['total_slippage'] / self.execution_stats['orders_executed'] * 100) if self.execution_stats['orders_executed'] > 0 else 0
        
        return {
            # Portfolio metrics
            'portfolio_value': portfolio_state.total_value,
            'cash': portfolio_state.cash,
            'positions_count': len(portfolio_state.positions),
            'trade_count': portfolio_state.trade_count,
            'total_pnl': portfolio_state.total_pnl,
            
            # Execution metrics
            'signals_processed': self.execution_stats['signals_processed'],
            'orders_executed': self.execution_stats['orders_executed'],
            'execution_failures': self.execution_stats['execution_failures'],
            'execution_success_rate': success_rate,
            'avg_slippage_percent': avg_slippage,
            'avg_execution_time_ms': self.execution_stats['avg_execution_time'] * 1000,
            'processed_signals_count': len(self.processed_signals)
        }
    
    def reset_metrics(self):
        """Reset execution metrics (useful for testing)"""
        self.execution_stats = {
            'signals_processed': 0,
            'orders_executed': 0,
            'execution_failures': 0,
            'total_slippage': 0.0,
            'total_execution_time': 0.0,
            'avg_execution_time': 0.0
        }
        self.processed_signals.clear() 