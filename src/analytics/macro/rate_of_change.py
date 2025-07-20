import math
from typing import Optional, Union, TYPE_CHECKING
from enum import Enum

# Type checking imports
if TYPE_CHECKING:
    import pandas as pd

class ZeroHandlingStrategy(Enum):
    """Strategies for handling zero previous values."""
    RAISE_ERROR = "raise_error"
    RETURN_NONE = "return_none"
    RETURN_INF = "return_inf"
    USE_ABSOLUTE = "use_absolute"  # Use absolute change when previous is zero

class RateOfChangeCalculator:
    """
    Calculates percentage rate of change between two values with robust error handling.
    Formula: ((current - previous) / previous) * 100
    """
    def __init__(self, zero_strategy: ZeroHandlingStrategy = ZeroHandlingStrategy.RETURN_NONE):
        """
        Initialize calculator with zero handling strategy.
        
        Args:
            zero_strategy: How to handle cases where previous_value is zero
        """
        self.zero_strategy = zero_strategy

    def calculate_roc(self, 
                     current_value: Union[float, int], 
                     previous_value: Union[float, int],
                     precision: int = 2) -> Optional[float]:
        """Calculate rate of change as percentage."""
        if not self._is_valid_number(current_value):
            raise ValueError(f"Invalid current_value: {current_value}")
        if not self._is_valid_number(previous_value):
            raise ValueError(f"Invalid previous_value: {previous_value}")
        
        current = float(current_value)
        previous = float(previous_value)
        
        if previous == 0.0:
            return self._handle_zero_previous(current, previous)
        
        roc = ((current - previous) / previous) * 100
        
        if math.isinf(roc) or math.isnan(roc):
            return None
            
        return round(roc, precision)

    def _is_valid_number(self, value: Union[float, int]) -> bool:
        """Check if value is a valid finite number."""
        if value is None:
            return False
        try:
            num = float(value)
            return math.isfinite(num)
        except (ValueError, TypeError):
            return False

    def _handle_zero_previous(self, current: float, previous: float) -> Optional[float]:
        """Handle case where previous value is zero based on strategy."""
        if self.zero_strategy == ZeroHandlingStrategy.RAISE_ERROR:
            raise ZeroDivisionError("Cannot calculate ROC: previous value is zero")
        elif self.zero_strategy == ZeroHandlingStrategy.RETURN_NONE:
            return None
        elif self.zero_strategy == ZeroHandlingStrategy.RETURN_INF:
            if current > 0:
                return float('inf')
            elif current < 0:
                return float('-inf')
            else:
                return 0.0
        elif self.zero_strategy == ZeroHandlingStrategy.USE_ABSOLUTE:
            return current
        return None

    def calculate_roc_series(self, values: list[Union[float, int]]) -> list[Optional[float]]:
        if not values or len(values) < 2:
            return [None] * len(values) if values else []
        roc_series = [None]
        for i in range(1, len(values)):
            try:
                roc = self.calculate_roc(values[i], values[i-1])
                roc_series.append(roc)
            except (ValueError, ZeroDivisionError):
                roc_series.append(None)
        return roc_series

    def calculate_annualized_roc(self, 
                                current_value: Union[float, int],
                                previous_value: Union[float, int],
                                periods: int,
                                periods_per_year: int = 252) -> Optional[float]:
        if periods <= 0:
            raise ValueError("Periods must be positive")
        if not self._is_valid_number(current_value) or not self._is_valid_number(previous_value):
            return None
        current = float(current_value)
        previous = float(previous_value)
        if previous <= 0:
            return None
        try:
            annualized_return = (current / previous) ** (periods_per_year / periods) - 1
            return round(annualized_return * 100, 2)
        except (ValueError, ZeroDivisionError, OverflowError):
            return None

    def get_roc_category(self, roc: Optional[float]) -> str:  # FIXED: Optional[float]
        """
        Categorize ROC magnitude for quick interpretation.
        
        Args:
            roc: Rate of change percentage (can be None)
            
        Returns:
            Category string describing the magnitude and direction
        """
        if roc is None:
            return "Invalid"
        
        # Handle special float values
        if math.isnan(roc) or math.isinf(roc):
            return "Invalid"
        
        abs_roc = abs(roc)
        
        if abs_roc == 0:
            return "No Change"
        elif abs_roc < 1:
            return "Minimal" + (" Increase" if roc > 0 else " Decrease")
        elif abs_roc < 5:
            return "Small" + (" Increase" if roc > 0 else " Decrease")
        elif abs_roc < 15:
            return "Moderate" + (" Increase" if roc > 0 else " Decrease")
        elif abs_roc < 30:
            return "Large" + (" Increase" if roc > 0 else " Decrease")
        else:
            return "Extreme" + (" Increase" if roc > 0 else " Decrease")

    def _check_pandas_available(self) -> bool:
        """Check if pandas is available for import."""
        try:
            import pandas as pd
            return True
        except ImportError:
            return False

    def calculate_period_roc(self, 
                           series: 'pd.Series',  # FIXED: String annotation for forward reference
                           period: int,
                           precision: int = 2) -> Optional[float]:
        """
        Calculate rate of change between current value and value from 'period' periods ago.
        
        Args:
            series: pandas Series with numeric values
            period: number of periods to look back (must be positive)
            precision: decimal places for rounding result
            
        Returns:
            Optional[float]: ROC percentage or None if calculation not possible
            
        Raises:
            ValueError: If period is invalid, series is invalid, or pandas not available
            ImportError: If pandas is not installed
        """
        # Check pandas availability
        if not self._check_pandas_available():
            raise ImportError("pandas is required for calculate_period_roc method")
        
        import pandas as pd
        
        # Input validation
        if period <= 0:
            raise ValueError(f"Period must be positive, got: {period}")
        
        if series is None:
            raise ValueError("Series cannot be None")
        
        if not isinstance(series, pd.Series):
            raise ValueError(f"Expected pandas Series, got: {type(series)}")
        
        if series.empty:
            raise ValueError("Series cannot be empty")
        
        if len(series) < period + 1:
            return None  # Not enough data points - this is expected, not an error
        
        try:
            # Get current value (last in series) and previous value (period ago)
            current_value = series.iloc[-1]
            previous_value = series.iloc[-(period + 1)]
            
            # Validate extracted values
            if pd.isna(current_value) or pd.isna(previous_value):
                return None  # Cannot calculate with NaN values
            
            # Use existing calculate_roc method for consistency
            return self.calculate_roc(current_value, previous_value, precision)
            
        except IndexError:
            # This shouldn't happen given our length check, but just in case
            return None
        except (ValueError, TypeError) as e:
            # Re-raise validation errors from calculate_roc
            if "Invalid" in str(e):
                return None  # Invalid data, return None instead of crashing
            raise  # Re-raise other unexpected errors

    def calculate_rolling_roc(self, 
                            series: 'pd.Series',
                            period: int,
                            precision: int = 2) -> 'pd.Series':
        """
        Calculate rolling ROC for entire series.
        
        Args:
            series: pandas Series with numeric values
            period: number of periods to look back
            precision: decimal places for rounding
            
        Returns:
            pandas Series with ROC values (first 'period' values will be NaN)
            
        Raises:
            ImportError: If pandas is not installed
            ValueError: If inputs are invalid
        """
        if not self._check_pandas_available():
            raise ImportError("pandas is required for calculate_rolling_roc method")
        
        import pandas as pd
        
        if not isinstance(series, pd.Series):
            raise ValueError(f"Expected pandas Series, got: {type(series)}")
        
        if period <= 0:
            raise ValueError(f"Period must be positive, got: {period}")
        
        if series.empty:
            return pd.Series(dtype=float)
        
        # Calculate ROC using pandas shift for efficiency
        try:
            shifted_series = series.shift(period)
            roc_series = ((series - shifted_series) / shifted_series) * 100
            
            # Handle special cases based on zero strategy
            if self.zero_strategy == ZeroHandlingStrategy.RETURN_NONE:
                # Set infinite values to NaN
                roc_series = roc_series.replace([float('inf'), float('-inf')], float('nan'))
            elif self.zero_strategy == ZeroHandlingStrategy.USE_ABSOLUTE:
                # Replace infinite values with absolute change
                mask_inf = roc_series == float('inf')
                mask_neg_inf = roc_series == float('-inf')
                roc_series.loc[mask_inf | mask_neg_inf] = series.loc[mask_inf | mask_neg_inf]
            
            # Round to specified precision
            roc_series = roc_series.round(precision)
            
            return roc_series
            
        except Exception as e:
            # Return series of NaN if calculation fails
            return pd.Series([float('nan')] * len(series), index=series.index) 