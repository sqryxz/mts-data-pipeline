"""
Error handling utilities for risk management module.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorType(Enum):
    """Types of errors that can occur in risk management."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DATA_ERROR = "DATA_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class RiskManagementError:
    """Structured error information for risk management."""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    traceback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            'error_type': self.error_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback,
            'context': self.context
        }


class RiskManagementErrorHandler:
    """Centralized error handler for risk management operations."""
    
    def __init__(self):
        self.error_count = 0
        self.error_log = []
    
    def handle_error(
        self,
        error: Exception,
        error_type: ErrorType,
        severity: ErrorSeverity,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False
    ) -> RiskManagementError:
        """
        Handle an error and create structured error information.
        
        Args:
            error: The exception that occurred
            error_type: Type of error
            severity: Severity level
            context: Additional context information
            reraise: Whether to re-raise the error after handling
            
        Returns:
            Structured error information
        """
        # Create error details
        error_details = {
            'error_class': type(error).__name__,
            'error_message': str(error),
            'error_args': getattr(error, 'args', []),
        }
        
        # Get traceback if available
        tb = traceback.format_exc() if traceback else None
        
        # Create structured error
        risk_error = RiskManagementError(
            error_type=error_type,
            severity=severity,
            message=str(error),
            details=error_details,
            timestamp=datetime.now(),
            traceback=tb,
            context=context or {}
        )
        
        # Log the error
        self._log_error(risk_error)
        
        # Store in error log
        self.error_log.append(risk_error)
        self.error_count += 1
        
        # Re-raise if requested
        if reraise:
            raise error
        
        return risk_error
    
    def _log_error(self, error: RiskManagementError) -> None:
        """Log error with appropriate level based on severity."""
        log_message = f"[{error.error_type.value}] {error.message}"
        
        if error.context:
            log_message += f" | Context: {error.context}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors handled."""
        error_counts = {}
        for error in self.error_log:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': self.error_count,
            'error_counts': error_counts,
            'recent_errors': [
                error.to_dict() for error in self.error_log[-10:]  # Last 10 errors
            ]
        }
    
    def clear_error_log(self) -> None:
        """Clear the error log."""
        self.error_log.clear()
        self.error_count = 0


def safe_execute(
    func,
    *args,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        error_type: Type of error if exception occurs
        severity: Severity level
        context: Additional context
        default_return: Default return value if function fails
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return if error occurs
    """
    error_handler = RiskManagementErrorHandler()
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(
            error=e,
            error_type=error_type,
            severity=severity,
            context=context
        )
        return default_return


def validate_input(
    value: Any,
    expected_type: type,
    field_name: str,
    allow_none: bool = False,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None
) -> None:
    """
    Validate input parameters with comprehensive error handling.
    
    Args:
        value: Value to validate
        expected_type: Expected type
        field_name: Name of the field for error messages
        allow_none: Whether None values are allowed
        min_value: Minimum allowed value (for numeric types)
        max_value: Maximum allowed value (for numeric types)
        
    Raises:
        ValueError: If validation fails
    """
    # Check for None
    if value is None:
        if not allow_none:
            raise ValueError(f"{field_name} cannot be None")
        return
    
    # Check type
    if not isinstance(value, expected_type):
        raise ValueError(
            f"{field_name} must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
    
    # Check numeric bounds
    if isinstance(value, (int, float)) and (min_value is not None or max_value is not None):
        if min_value is not None and value < min_value:
            raise ValueError(f"{field_name} must be >= {min_value}, got {value}")
        if max_value is not None and value > max_value:
            raise ValueError(f"{field_name} must be <= {max_value}, got {value}")
    
    # Check string length
    if isinstance(value, str):
        if len(value.strip()) == 0:
            raise ValueError(f"{field_name} cannot be empty")


def create_error_assessment(
    signal,
    portfolio_state,
    error: Exception,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR
) -> 'RiskAssessment':
    """
    Create a risk assessment for error cases.
    
    Args:
        signal: Trading signal (may be None)
        portfolio_state: Portfolio state (may be None)
        error: The error that occurred
        error_type: Type of error
        
    Returns:
        Risk assessment with error information
    """
    from ..models.risk_models import RiskAssessment, RiskLevel
    
    # Safe attribute access
    signal_id = getattr(signal, 'signal_id', 'unknown') if signal else "unknown"
    asset = getattr(signal, 'asset', 'unknown') if signal else "unknown"
    signal_type = getattr(signal, 'signal_type', None) if signal else None
    signal_price = getattr(signal, 'price', 0.0) if signal else 0.0
    signal_confidence = getattr(signal, 'confidence', 0.0) if signal else 0.0
    timestamp = getattr(signal, 'timestamp', None) if signal else None
    
    return RiskAssessment(
        signal_id=signal_id,
        asset=asset,
        signal_type=signal_type,
        signal_price=signal_price,
        signal_confidence=signal_confidence,
        timestamp=timestamp,
        
        # Error status
        is_approved=False,
        rejection_reason=f"Assessment failed: {str(error)}",
        risk_warnings=[f"Error during assessment: {str(error)}"],
        risk_level=RiskLevel.CRITICAL,
        
        # Default values
        recommended_position_size=0.0,
        position_size_method="Error",
        stop_loss_price=0.0,
        take_profit_price=0.0,
        risk_reward_ratio=0.0,
        position_risk_percent=0.0,
        portfolio_heat=0.0,
        market_volatility=0.0,
        correlation_risk=0.0,
        portfolio_impact={'error': True, 'error_type': error_type.value},
        current_drawdown=0.0,
        daily_pnl_impact=0.0,
        risk_config_snapshot={},
        processing_time_ms=0.0
    )


def handle_configuration_error(config_path: str, error: Exception) -> Dict[str, Any]:
    """
    Handle configuration loading errors.
    
    Args:
        config_path: Path to configuration file
        error: The error that occurred
        
    Returns:
        Default configuration
    """
    logger.error(f"Failed to load configuration from {config_path}: {error}")
    logger.info("Using default configuration")
    
    return {
        'risk_limits': {
            'max_drawdown_limit': 0.20,
            'daily_loss_limit': 0.05,
            'per_trade_stop_loss': 0.02,
            'max_position_size': 0.10
        },
        'position_sizing': {
            'base_position_percent': 0.02,
            'min_position_size': 0.001
        },
        'risk_assessment': {
            'default_risk_reward_ratio': 2.0,
            'confidence_threshold': 0.5,
            'processing_timeout_ms': 5000
        }
    }


def handle_validation_error(field_name: str, value: Any, expected: str) -> str:
    """
    Handle validation errors with detailed messages.
    
    Args:
        field_name: Name of the field that failed validation
        value: The invalid value
        expected: Description of what was expected
        
    Returns:
        Detailed error message
    """
    return f"Validation failed for {field_name}: got {value} ({type(value).__name__}), expected {expected}"


def handle_calculation_error(operation: str, inputs: Dict[str, Any], error: Exception) -> str:
    """
    Handle calculation errors with context.
    
    Args:
        operation: Name of the calculation operation
        inputs: Input values used in calculation
        error: The calculation error
        
    Returns:
        Detailed error message
    """
    input_str = ", ".join([f"{k}={v}" for k, v in inputs.items()])
    return f"Calculation error in {operation} with inputs ({input_str}): {str(error)}"


# Global error handler instance
error_handler = RiskManagementErrorHandler() 