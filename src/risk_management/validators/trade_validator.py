"""
Trade validation components.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ..models.risk_models import TradingSignal, PortfolioState

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of trade validation."""
    is_valid: bool
    rejection_reason: Optional[str] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TradeValidator:
    """
    Validates trades against risk limits.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize trade validator with configuration.
        
        Args:
            config: Risk management configuration
        """
        self.config = config
        self.max_drawdown_limit = config.get('risk_limits', {}).get('max_drawdown_limit', 0.20)
        self.daily_loss_limit = config.get('risk_limits', {}).get('daily_loss_limit', 0.05)
        self.per_trade_stop_loss = config.get('risk_limits', {}).get('per_trade_stop_loss', 0.02)
        
        logger.info(f"Trade validator initialized:")
        logger.info(f"  Max drawdown limit: {self.max_drawdown_limit:.1%}")
        logger.info(f"  Daily loss limit: {self.daily_loss_limit:.1%}")
        logger.info(f"  Per trade stop loss: {self.per_trade_stop_loss:.1%}")
    
    def validate_trade(self, signal: TradingSignal, portfolio_state: PortfolioState, position_size: float) -> ValidationResult:
        """
        Validate a trade against all risk limits.
        
        Args:
            signal: Trading signal to validate
            portfolio_state: Current portfolio state
            position_size: Proposed position size
            
        Returns:
            Validation result with approval/rejection decision
        """
        try:
            # Validate inputs
            if signal is None:
                return ValidationResult(False, "Signal cannot be None")
            
            if portfolio_state is None:
                return ValidationResult(False, "Portfolio state cannot be None")
            
            if position_size <= 0:
                return ValidationResult(False, f"Position size must be positive, got {position_size}")
            
            warnings = []
            
            # Check drawdown limit
            drawdown_result = self.validate_drawdown_limit(signal, portfolio_state, position_size)
            if not drawdown_result.is_valid:
                return drawdown_result
            
            # Check daily loss limit
            daily_loss_result = self.validate_daily_loss_limit(signal, portfolio_state, position_size)
            if not daily_loss_result.is_valid:
                return daily_loss_result
            
            # Collect warnings from all validations
            warnings.extend(drawdown_result.warnings)
            warnings.extend(daily_loss_result.warnings)
            
            return ValidationResult(True, warnings=warnings)
            
        except Exception as e:
            logger.error(f"Error in trade validation: {e}")
            return ValidationResult(False, f"Validation failed: {str(e)}")
    
    def validate_drawdown_limit(self, signal: TradingSignal, portfolio_state: PortfolioState, position_size: float) -> ValidationResult:
        """
        Check if trade would exceed maximum drawdown limit.
        
        Args:
            signal: Trading signal
            portfolio_state: Current portfolio state
            position_size: Proposed position size
            
        Returns:
            Validation result
        """
        try:
            # Validate portfolio state
            if not hasattr(portfolio_state, 'current_drawdown'):
                return ValidationResult(False, "Portfolio state missing current_drawdown attribute")
            
            if not hasattr(portfolio_state, 'total_equity'):
                return ValidationResult(False, "Portfolio state missing total_equity attribute")
            
            if portfolio_state.total_equity <= 0:
                return ValidationResult(False, f"Invalid portfolio equity: {portfolio_state.total_equity}")
            
            # Calculate potential loss as percentage of equity
            potential_loss_amount = position_size * self.per_trade_stop_loss
            potential_loss_pct = potential_loss_amount / portfolio_state.total_equity
            
            # Calculate potential new drawdown (both as percentages)
            current_drawdown = portfolio_state.current_drawdown
            potential_new_drawdown = current_drawdown + potential_loss_pct
            
            # Check if this would exceed the limit
            if potential_new_drawdown > self.max_drawdown_limit:
                rejection_reason = (
                    f"Trade would exceed maximum drawdown limit. "
                    f"Current: {current_drawdown:.1%}, "
                    f"Potential: {potential_new_drawdown:.1%}, "
                    f"Limit: {self.max_drawdown_limit:.1%}"
                )
                return ValidationResult(False, rejection_reason)
            
            # Check if approaching the limit (warning)
            warning_threshold = self.max_drawdown_limit * 0.8  # 80% of limit
            if potential_new_drawdown > warning_threshold:
                warnings = [
                    f"Approaching drawdown limit: {potential_new_drawdown:.1%} "
                    f"(limit: {self.max_drawdown_limit:.1%})"
                ]
                return ValidationResult(True, warnings=warnings)
            
            return ValidationResult(True)
            
        except Exception as e:
            logger.error(f"Error in drawdown validation: {e}")
            return ValidationResult(False, f"Drawdown validation failed: {str(e)}")
    
    def validate_daily_loss_limit(self, signal: TradingSignal, portfolio_state: PortfolioState, position_size: float) -> ValidationResult:
        """
        Check if trade would exceed daily loss limit.
        
        Args:
            signal: Trading signal
            portfolio_state: Current portfolio state
            position_size: Proposed position size
            
        Returns:
            Validation result
        """
        try:
            # Validate portfolio state
            required_attrs = ['daily_pnl', 'total_equity']
            for attr in required_attrs:
                if not hasattr(portfolio_state, attr):
                    return ValidationResult(False, f"Portfolio state missing required attribute: {attr}")
            
            if portfolio_state.total_equity <= 0:
                return ValidationResult(False, f"Invalid portfolio equity: {portfolio_state.total_equity}")
            
            # Calculate potential loss from this trade
            potential_loss = position_size * self.per_trade_stop_loss
            
            # Get current daily P&L (negative values are losses)
            current_daily_pnl = portfolio_state.daily_pnl
            current_daily_loss = abs(min(0, current_daily_pnl))  # Only count losses
            
            # Calculate potential new daily loss
            potential_new_daily_loss = current_daily_loss + potential_loss
            
            # Calculate daily loss limit in absolute terms
            daily_loss_limit_amount = portfolio_state.total_equity * self.daily_loss_limit
            
            # Check if this would exceed the limit
            if potential_new_daily_loss > daily_loss_limit_amount:
                rejection_reason = (
                    f"Trade would exceed daily loss limit. "
                    f"Current daily loss: ${current_daily_loss:.2f}, "
                    f"Potential new loss: ${potential_new_daily_loss:.2f}, "
                    f"Limit: ${daily_loss_limit_amount:.2f}"
                )
                return ValidationResult(False, rejection_reason)
            
            # Check if approaching the limit (warning)
            warning_threshold = daily_loss_limit_amount * 0.8  # 80% of limit
            if potential_new_daily_loss > warning_threshold:
                warnings = [
                    f"Approaching daily loss limit: ${potential_new_daily_loss:.2f} "
                    f"(limit: ${daily_loss_limit_amount:.2f})"
                ]
                return ValidationResult(True, warnings=warnings)
            
            return ValidationResult(True)
            
        except Exception as e:
            logger.error(f"Error in daily loss validation: {e}")
            return ValidationResult(False, f"Daily loss validation failed: {str(e)}") 