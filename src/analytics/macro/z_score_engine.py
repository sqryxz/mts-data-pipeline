import math
import numpy as np
from typing import Optional, Union, List, TYPE_CHECKING

# Type checking imports
if TYPE_CHECKING:
    import pandas as pd

class ZScoreEngine:
    """
    Calculates z-scores (standard deviations from mean) with robust error handling.
    Formula: z = (x - μ) / σ
    """
    
    def __init__(self, min_std_dev: float = 1e-10):
        """
        Initialize z-score engine.
        
        Args:
            min_std_dev: Minimum standard deviation to avoid division by zero
        """
        self.min_std_dev = min_std_dev
    
    def _check_numpy_available(self) -> bool:
        """Check if numpy is available for import."""
        try:
            import numpy as np
            return True
        except ImportError:
            return False
    
    def _is_valid_number(self, value: Union[float, int]) -> bool:
        """Check if value is a valid finite number."""
        if value is None:
            return False
        try:
            num = float(value)
            return math.isfinite(num)
        except (ValueError, TypeError):
            return False
    
    def calculate_z_score(self, 
                         value: Union[float, int], 
                         mean: Union[float, int], 
                         std_dev: Union[float, int],
                         precision: int = 4) -> Optional[float]:
        """
        Calculate z-score for a single value.
        
        Args:
            value: The value to calculate z-score for
            mean: The mean of the distribution
            std_dev: The standard deviation of the distribution
            precision: Decimal places for rounding result
            
        Returns:
            Optional[float]: Z-score or None if calculation not possible
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not self._is_valid_number(value):
            raise ValueError(f"Invalid value: {value}")
        if not self._is_valid_number(mean):
            raise ValueError(f"Invalid mean: {mean}")
        if not self._is_valid_number(std_dev):
            raise ValueError(f"Invalid std_dev: {std_dev}")
        
        # Convert to float for calculation
        x = float(value)
        mu = float(mean)
        sigma = float(std_dev)
        
        # Handle zero or very small standard deviation
        if abs(sigma) < self.min_std_dev:
            return None  # Cannot calculate z-score with zero variance
        
        # Calculate z-score
        z_score = (x - mu) / sigma
        
        # Check for invalid results
        if math.isinf(z_score) or math.isnan(z_score):
            return None
        
        return round(z_score, precision)
    
    def calculate_z_score_from_data(self, 
                                   value: Union[float, int], 
                                   data: List[Union[float, int]],
                                   precision: int = 4) -> Optional[float]:
        """
        Calculate z-score for a value using statistics from a dataset.
        
        Args:
            value: The value to calculate z-score for
            data: List of values to calculate mean and std from
            precision: Decimal places for rounding result
            
        Returns:
            Optional[float]: Z-score or None if calculation not possible
        """
        if not self._check_numpy_available():
            raise ImportError("numpy is required for calculate_z_score_from_data method")
        
        import numpy as np
        
        # Input validation
        if not self._is_valid_number(value):
            raise ValueError(f"Invalid value: {value}")
        
        if not data or len(data) < 2:
            return None  # Need at least 2 data points for std calculation
        
        # Convert data to numpy array and filter out invalid values
        try:
            data_array = np.array(data, dtype=float)
            valid_mask = np.isfinite(data_array)
            
            if not np.any(valid_mask) or np.sum(valid_mask) < 2:
                return None  # Not enough valid data points
            
            valid_data = data_array[valid_mask]
            
            # Calculate statistics
            mean = np.mean(valid_data)
            std_dev = np.std(valid_data, ddof=1)  # Sample standard deviation
            
            # Use the main calculate_z_score method
            return self.calculate_z_score(value, mean, std_dev, precision)
            
        except (ValueError, TypeError, RuntimeError) as e:
            return None
    
    def get_z_score_category(self, z_score: Optional[float]) -> str:
        """
        Categorize z-score magnitude for quick interpretation.
        
        Args:
            z_score: Z-score value (can be None)
            
        Returns:
            Category string describing the magnitude
        """
        if z_score is None:
            return "Invalid"
        
        # Handle special float values
        if math.isnan(z_score) or math.isinf(z_score):
            return "Invalid"
        
        abs_z = abs(z_score)
        
        if abs_z < 0.5:
            return "Near Mean"
        elif abs_z < 1.0:
            return "Within 1σ"
        elif abs_z < 1.5:
            return "Moderate Deviation"
        elif abs_z < 2.0:
            return "Significant Deviation"
        elif abs_z < 3.0:
            return "Large Deviation"
        else:
            return "Extreme Deviation"
    
    def is_outlier(self, z_score: Optional[float], threshold: float = 2.0) -> bool:
        """
        Check if z-score indicates an outlier.
        
        Args:
            z_score: Z-score value
            threshold: Number of standard deviations for outlier detection
            
        Returns:
            bool: True if z-score exceeds threshold
        """
        if z_score is None:
            return False
        
        return abs(z_score) > threshold
    
    def calculate_percentile_from_z_score(self, z_score: Optional[float]) -> Optional[float]:
        """
        Convert z-score to percentile rank (0-100).
        
        Args:
            z_score: Z-score value
            
        Returns:
            Optional[float]: Percentile rank or None if invalid
        """
        if z_score is None or math.isnan(z_score) or math.isinf(z_score):
            return None
        
        try:
            # Use normal CDF to convert z-score to percentile
            percentile = (1 + math.erf(z_score / math.sqrt(2))) / 2 * 100
            return round(percentile, 2)
        except (ValueError, OverflowError):
            return None

    def calculate_rolling_z_scores(self, 
                                 series: 'pd.Series',
                                 window: int = 30,
                                 min_periods: int = 2,
                                 precision: int = 4) -> 'pd.Series':
        """
        Calculate rolling z-scores for a pandas Series.
        
        Args:
            series: pandas Series with numeric values
            window: Rolling window size for mean/std calculation
            min_periods: Minimum number of observations required
            precision: Decimal places for rounding result
            
        Returns:
            pandas Series with z-scores (first window-1 values will be NaN)
            
        Raises:
            ImportError: If pandas is not installed
            ValueError: If inputs are invalid
        """
        if not self._check_numpy_available():
            raise ImportError("numpy is required for calculate_rolling_z_scores method")
        
        import pandas as pd
        
        # Input validation
        if not isinstance(series, pd.Series):
            raise ValueError(f"Expected pandas Series, got: {type(series)}")
        
        if window <= 1:
            raise ValueError(f"Window must be > 1, got: {window}")
        
        if min_periods < 2:
            raise ValueError(f"min_periods must be >= 2, got: {min_periods}")
        
        if series.empty:
            return pd.Series(dtype=float)
        
        if len(series) < min_periods:
            return pd.Series([float('nan')] * len(series), index=series.index)
        
        try:
            # Calculate rolling mean and standard deviation
            rolling_mean = series.rolling(window=window, min_periods=min_periods).mean()
            rolling_std = series.rolling(window=window, min_periods=min_periods).std(ddof=1)
            
            # Calculate z-scores
            z_scores = (series - rolling_mean) / rolling_std
            
            # Handle division by zero (when std dev is too small)
            z_scores = z_scores.where(rolling_std >= self.min_std_dev, float('nan'))
            
            # Handle infinite and NaN values
            z_scores = z_scores.replace([float('inf'), float('-inf')], float('nan'))
            
            # Round to specified precision
            z_scores = z_scores.round(precision)
            
            return z_scores
            
        except Exception as e:
            # Return series of NaN if calculation fails
            return pd.Series([float('nan')] * len(series), index=series.index)

    def calculate_rolling_z_scores_with_lookback(self, 
                                               series: 'pd.Series',
                                               lookback_period: int = 30,
                                               precision: int = 4) -> 'pd.Series':
        """
        Calculate z-scores using a fixed lookback period for each point.
        
        Args:
            series: pandas Series with numeric values
            lookback_period: Number of periods to look back for statistics
            precision: Decimal places for rounding result
            
        Returns:
            pandas Series with z-scores (first lookback_period values will be NaN)
            
        Raises:
            ImportError: If pandas is not installed
            ValueError: If inputs are invalid
        """
        if not self._check_numpy_available():
            raise ImportError("numpy is required for calculate_rolling_z_scores_with_lookback method")
        
        import pandas as pd
        
        # Input validation
        if not isinstance(series, pd.Series):
            raise ValueError(f"Expected pandas Series, got: {type(series)}")
        
        if lookback_period <= 1:
            raise ValueError(f"lookback_period must be > 1, got: {lookback_period}")
        
        if series.empty:
            return pd.Series(dtype=float)
        
        if len(series) < lookback_period + 1:
            return pd.Series([float('nan')] * len(series), index=series.index)
        
        try:
            z_scores = pd.Series(index=series.index, dtype=float)
            
            # Calculate z-score for each point using lookback window
            for i in range(lookback_period, len(series)):
                lookback_data = series.iloc[i-lookback_period:i].values
                current_value = series.iloc[i]
                
                # Filter out NaN values
                valid_data = lookback_data[pd.notna(lookback_data)]
                
                if len(valid_data) >= 2:
                    mean_val = np.mean(valid_data)
                    std_val = np.std(valid_data, ddof=1)
                    
                    if std_val >= self.min_std_dev:
                        z_score = (current_value - mean_val) / std_val
                        if math.isfinite(z_score):
                            z_scores.iloc[i] = round(z_score, precision)
                        else:
                            z_scores.iloc[i] = float('nan')
                    else:
                        z_scores.iloc[i] = float('nan')
                else:
                    z_scores.iloc[i] = float('nan')
            
            return z_scores
            
        except Exception as e:
            # Return series of NaN if calculation fails
            return pd.Series([float('nan')] * len(series), index=series.index)


# Usage Examples
if __name__ == "__main__":
    engine = ZScoreEngine()
    
    # Test basic z-score calculation
    z_score = engine.calculate_z_score(110, 100, 10)
    print(f"Z-score for 110 (mean=100, std=10): {z_score}")
    print(f"Category: {engine.get_z_score_category(z_score)}")
    print(f"Is outlier (threshold=2): {engine.is_outlier(z_score, 2)}")
    print(f"Percentile: {engine.calculate_percentile_from_z_score(z_score)}%")
    
    # Test with data
    data = [95, 98, 102, 105, 108, 110, 112, 115, 118, 120]
    z_from_data = engine.calculate_z_score_from_data(125, data)
    print(f"Z-score for 125 from data: {z_from_data}") 