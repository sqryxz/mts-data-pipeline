"""
Basic position size calculator.
"""

import logging
from typing import Optional
from ..models.risk_models import TradingSignal, PortfolioState

logger = logging.getLogger(__name__)


class PositionCalculator:
    """
    Basic position size calculator using fixed percentage of account equity.
    """
    
    def __init__(self, 
                 base_position_percent: float = 0.02,
                 max_position_percent: float = 0.10,
                 min_position_usd: float = 10.0):
        """
        Initialize the position calculator.
        
        Args:
            base_position_percent: Percentage of account equity to use for position sizing (default: 2%)
            max_position_percent: Maximum position size as percentage of equity (default: 10%)
            min_position_usd: Minimum position size in USD (default: $10)
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        if not 0 < base_position_percent <= 1:
            raise ValueError(f"base_position_percent must be between 0 and 1, got {base_position_percent}")
        
        if not 0 < max_position_percent <= 1:
            raise ValueError(f"max_position_percent must be between 0 and 1, got {max_position_percent}")
            
        if base_position_percent > max_position_percent:
            raise ValueError(f"base_position_percent ({base_position_percent}) cannot exceed max_position_percent ({max_position_percent})")
        
        if min_position_usd < 0:
            raise ValueError(f"min_position_usd must be non-negative, got {min_position_usd}")
        
        self.base_position_percent = base_position_percent
        self.max_position_percent = max_position_percent
        self.min_position_usd = min_position_usd
        
        logger.info(f"Position calculator initialized:")
        logger.info(f"  Base position: {self.base_position_percent:.1%}")
        logger.info(f"  Max position: {self.max_position_percent:.1%}")
        logger.info(f"  Min position: ${self.min_position_usd}")
    
    def calculate_position_size(self, 
                               signal: TradingSignal, 
                               portfolio_state: PortfolioState) -> float:
        """
        Calculate position size based on fixed percentage of account equity.
        
        Args:
            signal: Trading signal containing asset and price information
            portfolio_state: Current portfolio state with total equity
            
        Returns:
            Recommended position size in USD
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if signal is None:
            raise ValueError("Signal cannot be None")
        
        if portfolio_state is None:
            raise ValueError("Portfolio state cannot be None")
        
        if not hasattr(signal, 'confidence'):
            raise ValueError("Signal must have confidence attribute")
            
        if not hasattr(signal, 'asset'):
            raise ValueError("Signal must have asset attribute")
        
        if not hasattr(portfolio_state, 'total_equity'):
            raise ValueError("Portfolio state must have total_equity attribute")
        
        # Validate values
        if portfolio_state.total_equity <= 0:
            logger.warning(f"Invalid total equity: {portfolio_state.total_equity}")
            return 0.0
        
        if not 0 <= signal.confidence <= 1:
            raise ValueError(f"Signal confidence must be between 0 and 1, got {signal.confidence}")
        
        try:
            # Calculate base position size as percentage of total equity
            base_position_size = portfolio_state.total_equity * self.base_position_percent
            
            # Apply signal confidence adjustment
            confidence_adjusted_size = base_position_size * signal.confidence
            
            # Apply maximum position limit
            max_allowed_size = portfolio_state.total_equity * self.max_position_percent
            position_size = min(confidence_adjusted_size, max_allowed_size)
            
            # Apply minimum position threshold
            if position_size < self.min_position_usd:
                logger.info(f"Position size ${position_size:.2f} below minimum ${self.min_position_usd}, setting to 0")
                position_size = 0.0
            
            logger.info(f"Position size calculation for {signal.asset}:")
            logger.info(f"  Total equity: ${portfolio_state.total_equity:,.2f}")
            logger.info(f"  Base position percent: {self.base_position_percent:.1%}")
            logger.info(f"  Signal confidence: {signal.confidence:.2f}")
            logger.info(f"  Before limits: ${confidence_adjusted_size:,.2f}")
            logger.info(f"  Final position size: ${position_size:,.2f}")
            
            return position_size
            
        except (AttributeError, TypeError) as e:
            logger.error(f"Invalid input data structure: {e}")
            raise ValueError(f"Invalid input data: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calculating position size: {e}")
            raise
    
    def calculate_position_size_simple(self, 
                                     account_equity: float, 
                                     confidence: float = 1.0) -> float:
        """
        Simple position size calculation for testing.
        
        Args:
            account_equity: Total account equity in USD
            confidence: Signal confidence (0.0 to 1.0)
            
        Returns:
            Position size in USD
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if account_equity <= 0:
            raise ValueError(f"Account equity must be positive, got {account_equity}")
        
        if not 0 <= confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
        
        # Calculate position size
        base_position_size = account_equity * self.base_position_percent
        confidence_adjusted_size = base_position_size * confidence
        
        # Apply limits
        max_allowed_size = account_equity * self.max_position_percent
        position_size = min(confidence_adjusted_size, max_allowed_size)
        
        # Apply minimum threshold
        if position_size < self.min_position_usd:
            position_size = 0.0
        
        return position_size
    
    def get_max_position_size(self, account_equity: float) -> float:
        """Get maximum allowed position size for given equity."""
        if account_equity <= 0:
            return 0.0
        return account_equity * self.max_position_percent
    
    def get_min_position_size(self) -> float:
        """Get minimum position size threshold."""
        return self.min_position_usd 