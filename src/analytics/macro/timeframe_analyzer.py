from typing import Optional, Dict, Any, TYPE_CHECKING, Union, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Type checking imports
if TYPE_CHECKING:
    import pandas as pd
    from src.analytics.storage.analytics_repository import AnalyticsRepository

class TimeframeType(Enum):
    """Enum for timeframe types to avoid string comparison issues."""
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1m"
    
    @classmethod
    def from_string(cls, timeframe_str: str) -> Optional['TimeframeType']:
        """Convert string to TimeframeType enum."""
        for tf_type in cls:
            if tf_type.value == timeframe_str:
                return tf_type
        return None

@dataclass
class TimeframeConfig:
    """Configuration for a specific timeframe."""
    key: str
    pandas_period: str
    description: str
    lookback_periods: int
    analysis_periods: int
    min_data_points: int
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.lookback_periods <= 0:
            raise ValueError(f"Lookback periods must be positive, got: {self.lookback_periods}")
        if self.analysis_periods <= 0:
            raise ValueError(f"Analysis periods must be positive, got: {self.analysis_periods}")
        if self.min_data_points <= 0:
            raise ValueError(f"Min data points must be positive, got: {self.min_data_points}")

class TimeframeAnalyzer:
    """
    Analyzes macro indicators across different timeframes with data resampling.
    """
    
    # Enhanced timeframe configurations with calculated relationships
    _TIMEFRAME_CONFIGS = {
        TimeframeType.HOUR_1.value: TimeframeConfig(
            key="1h",
            pandas_period="1H",
            description="1 Hour",
            lookback_periods=168,  # 1 week of hourly data
            analysis_periods=24,   # 24 hours for analysis
            min_data_points=10
        ),
        TimeframeType.HOUR_4.value: TimeframeConfig(
            key="4h", 
            pandas_period="4H",
            description="4 Hours",
            lookback_periods=168,  # 4 weeks of 4-hour data
            analysis_periods=42,   # 1 week of 4-hour periods
            min_data_points=10
        ),
        TimeframeType.DAY_1.value: TimeframeConfig(
            key="1d",
            pandas_period="1D", 
            description="1 Day",
            lookback_periods=90,   # 3 months of daily data
            analysis_periods=30,   # 30 days for analysis
            min_data_points=5
        ),
        TimeframeType.WEEK_1.value: TimeframeConfig(
            key="1w",
            pandas_period="1W",
            description="1 Week", 
            lookback_periods=52,   # 1 year of weekly data
            analysis_periods=12,   # 12 weeks for analysis
            min_data_points=4
        ),
        TimeframeType.MONTH_1.value: TimeframeConfig(
            key="1m",
            pandas_period="1M",
            description="1 Month",
            lookback_periods=24,   # 2 years of monthly data
            analysis_periods=6,    # 6 months for analysis
            min_data_points=3
        )
    }
    
    def __init__(self, repository: Optional['AnalyticsRepository'] = None):
        """
        Initialize timeframe analyzer with repository.
        
        Args:
            repository: Analytics repository for data access (optional for config-only usage)
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
        
        # Validate repository if provided
        if repository is not None:
            if not hasattr(repository, 'get_indicator_data'):
                raise ValueError("Repository must implement 'get_indicator_data' method")
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframe keys.
        
        Returns:
            List of supported timeframe strings
        """
        return list(self._TIMEFRAME_CONFIGS.keys())
    
    def get_timeframe_configs(self) -> Dict[str, TimeframeConfig]:
        """
        Get all timeframe configurations.
        
        Returns:
            Dict mapping timeframe keys to their configurations
        """
        return self._TIMEFRAME_CONFIGS.copy()
    
    def is_timeframe_supported(self, timeframe: str) -> bool:
        """
        Check if a timeframe is supported.
        
        Args:
            timeframe: Timeframe key to check
            
        Returns:
            bool: True if timeframe is supported
        """
        if timeframe is None or not isinstance(timeframe, str):
            return False
        return timeframe in self._TIMEFRAME_CONFIGS
    
    def get_timeframe_config(self, timeframe: str) -> Optional[TimeframeConfig]:
        """
        Get configuration for a specific timeframe.
        
        Args:
            timeframe: Timeframe key
            
        Returns:
            Optional[TimeframeConfig]: Timeframe configuration or None if not supported
        """
        return self._TIMEFRAME_CONFIGS.get(timeframe)
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate timeframe and log warning if not supported.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.is_timeframe_supported(timeframe):
            supported = list(self._TIMEFRAME_CONFIGS.keys())
            self.logger.warning(f"Unsupported timeframe: '{timeframe}'. "
                               f"Supported timeframes: {supported}")
            return False
        return True
    
    def get_lookback_periods(self, timeframe: Optional[str] = None) -> Union[Dict[str, int], Optional[int]]:
        """
        Get lookback periods for timeframes.
        
        Args:
            timeframe: Specific timeframe to get period for, or None for all
            
        Returns:
            Dict of all lookback periods or specific period value
        """
        if timeframe is None:
            return {tf: config.lookback_periods for tf, config in self._TIMEFRAME_CONFIGS.items()}
        
        config = self.get_timeframe_config(timeframe)
        return config.lookback_periods if config else None
    
    def get_analysis_periods(self, timeframe: Optional[str] = None) -> Union[Dict[str, int], Optional[int]]:
        """
        Get analysis periods for timeframes.
        
        Args:
            timeframe: Specific timeframe to get period for, or None for all
            
        Returns:
            Dict of all analysis periods or specific period value
        """
        if timeframe is None:
            return {tf: config.analysis_periods for tf, config in self._TIMEFRAME_CONFIGS.items()}
        
        config = self.get_timeframe_config(timeframe)
        return config.analysis_periods if config else None
    
    def get_pandas_period(self, timeframe: str) -> Optional[str]:
        """
        Get pandas resampling period string for timeframe.
        
        Args:
            timeframe: Timeframe key
            
        Returns:
            Optional[str]: Pandas period string or None if not supported
        """
        config = self.get_timeframe_config(timeframe)
        return config.pandas_period if config else None
    
    def get_min_data_points(self, timeframe: str) -> Optional[int]:
        """
        Get minimum required data points for reliable analysis.
        
        Args:
            timeframe: Timeframe key
            
        Returns:
            Optional[int]: Minimum data points or None if not supported
        """
        config = self.get_timeframe_config(timeframe)
        return config.min_data_points if config else None
    
    def calculate_date_range(self, timeframe: str, end_date: Optional[datetime] = None) -> Optional[Dict[str, datetime]]:
        """
        Calculate start and end dates for analysis based on timeframe.
        
        Args:
            timeframe: Timeframe key
            end_date: End date for analysis (defaults to now)
            
        Returns:
            Optional[Dict]: Dict with 'start' and 'end' datetime objects
        """
        if not self.validate_timeframe(timeframe):
            return None
        
        config = self.get_timeframe_config(timeframe)
        if not config:
            return None
        
        if end_date is None:
            end_date = datetime.now()
        
        # Convert string to enum for consistent comparison
        timeframe_type = TimeframeType.from_string(timeframe)
        if not timeframe_type:
            self.logger.error(f"Could not convert timeframe '{timeframe}' to enum")
            return None
        
        # Calculate start date based on lookback periods and timeframe
        if timeframe_type == TimeframeType.HOUR_1:
            start_date = end_date - timedelta(hours=config.lookback_periods)
        elif timeframe_type == TimeframeType.HOUR_4:
            start_date = end_date - timedelta(hours=config.lookback_periods * 4)
        elif timeframe_type == TimeframeType.DAY_1:
            start_date = end_date - timedelta(days=config.lookback_periods)
        elif timeframe_type == TimeframeType.WEEK_1:
            start_date = end_date - timedelta(weeks=config.lookback_periods)
        elif timeframe_type == TimeframeType.MONTH_1:
            # More accurate month calculation using dateutil.relativedelta
            try:
                from dateutil.relativedelta import relativedelta
                start_date = end_date - relativedelta(months=config.lookback_periods)
            except ImportError:
                # Fallback to approximate calculation if dateutil not available
                self.logger.warning("dateutil not available, using approximate month calculation")
                start_date = end_date - timedelta(days=config.lookback_periods * 30)
        else:
            self.logger.error(f"Date calculation not implemented for timeframe: {timeframe}")
            return None
        
        return {
            'start': start_date,
            'end': end_date,
            'lookback_periods': config.lookback_periods
        }
    
    def get_timeframe_summary(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive summary of timeframe configuration.
        
        Args:
            timeframe: Timeframe key
            
        Returns:
            Optional[Dict]: Complete timeframe information
        """
        config = self.get_timeframe_config(timeframe)
        if not config:
            return None
        
        return {
            'timeframe': config.key,
            'description': config.description,
            'pandas_period': config.pandas_period,
            'lookback_periods': config.lookback_periods,
            'analysis_periods': config.analysis_periods,
            'min_data_points': config.min_data_points,
            'is_supported': True
        }
    
    def validate_data_sufficiency(self, timeframe: str, data_count: int) -> bool:
        """
        Check if available data is sufficient for analysis.
        
        Args:
            timeframe: Timeframe key
            data_count: Number of available data points
            
        Returns:
            bool: True if data is sufficient
        """
        # Enhanced input validation
        if not isinstance(data_count, int) or data_count < 0:
            self.logger.error(f"Invalid data_count: {data_count}. Must be non-negative integer.")
            return False
        
        config = self.get_timeframe_config(timeframe)
        if not config:
            self.logger.error(f"No configuration found for timeframe: {timeframe}")
            return False
        
        is_sufficient = data_count >= config.min_data_points
        
        if not is_sufficient:
            self.logger.warning(f"Insufficient data for {timeframe} analysis. "
                               f"Got {data_count}, need at least {config.min_data_points}")
        else:
            self.logger.debug(f"Sufficient data for {timeframe}: {data_count} >= {config.min_data_points}")
        
        return is_sufficient

    def _verify_no_nan_values(self, data: 'pd.DataFrame') -> bool:
        """
        Verify that the output DataFrame has no NaN values in numeric columns.
        
        Args:
            data: DataFrame to check
            
        Returns:
            bool: True if no NaN values found, False otherwise
        """
        if data is None or data.empty:
            return True
        
        try:
            import pandas as pd
            
            # Check numeric columns for NaN values
            numeric_columns = data.select_dtypes(include=['number']).columns
            if len(numeric_columns) == 0:
                return True  # No numeric columns to check
            
            nan_counts = data[numeric_columns].isna().sum()
            total_nans = nan_counts.sum()
            
            if total_nans > 0:
                self.logger.warning(f"Found {total_nans} NaN values in output data:")
                for col, count in nan_counts.items():
                    if count > 0:
                        self.logger.warning(f"  Column '{col}': {count} NaN values")
                return False
            else:
                self.logger.debug("No NaN values found in output data")
                return True
                
        except Exception as e:
            self.logger.error(f"Error checking for NaN values: {e}")
            return False

    def get_timeframe_data(self, 
                          indicator: str, 
                          timeframe: str,
                          end_date: Optional[datetime] = None,
                          interpolate: bool = True,
                          value_column: str = 'value') -> Optional['pd.DataFrame']:
        """
        Fetch and resample data for a specific timeframe.
        
        Args:
            indicator: Indicator name to fetch data for
            timeframe: Timeframe key (must be supported)
            end_date: End date for data fetch (defaults to now)
            interpolate: Whether to interpolate missing values
            value_column: Name of the value column in raw data
            
        Returns:
            Optional[pd.DataFrame]: Resampled data or None if error
            
        Raises:
            ValueError: If timeframe is not supported or required parameters missing
            ImportError: If pandas is not available
        """
        # Input validation
        if not indicator or not isinstance(indicator, str):
            raise ValueError("Indicator must be a non-empty string")
        
        if not self.validate_timeframe(timeframe):
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        if not self._check_pandas_available():
            raise ImportError("pandas is required for get_timeframe_data method")
        
        if self.repository is None:
            self.logger.error("Repository not available for data fetching")
            return None
        
        # Validate repository has required method
        if not hasattr(self.repository, 'get_indicator_data'):
            self.logger.error("Repository must implement 'get_indicator_data' method")
            return None
        
        try:
            # Calculate date range for data fetch
            date_range = self.calculate_date_range(timeframe, end_date)
            if not date_range:
                self.logger.error(f"Could not calculate date range for timeframe: {timeframe}")
                return None
            
            start_date = date_range['start']
            end_date_actual = date_range['end']
            
            # Convert to string format for repository
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date_actual.strftime('%Y-%m-%d')
            
            # Fetch raw data from repository
            self.logger.info(f"Fetching {indicator} data for {timeframe} from {start_str} to {end_str}")
            raw_data = self.repository.get_indicator_data(indicator, start_str, end_str, interpolate)
            
            # Validate raw data
            if raw_data is None:
                self.logger.error(f"Repository returned None for {indicator}")
                return None
            
            if raw_data.empty:
                self.logger.warning(f"No data found for {indicator} in specified date range")
                return pd.DataFrame()  # Return empty DataFrame consistently
            
            # Prepare data for resampling
            processed_data = self._prepare_data_for_resampling(raw_data, value_column, interpolate)
            if processed_data is None or processed_data.empty:
                self.logger.error("Failed to prepare data for resampling")
                return pd.DataFrame()
            
            # Resample data to timeframe frequency
            pandas_period = self.get_pandas_period(timeframe)
            if not pandas_period:
                self.logger.error(f"Could not get pandas period for timeframe: {timeframe}")
                return None
            
            # Perform resampling
            resampled_data = self._resample_data(processed_data, pandas_period, timeframe, indicator)
            
            if resampled_data is None or resampled_data.empty:
                self.logger.warning(f"No data after resampling for {indicator} at {timeframe}")
                return pd.DataFrame()
            
            # Validate data sufficiency
            data_count = len(resampled_data)
            if data_count == 0:
                self.logger.warning(f"No data points after processing for {indicator} at {timeframe}")
                return pd.DataFrame()
            
            # Verify no NaN values in output
            if not self._verify_no_nan_values(resampled_data):
                self.logger.warning(f"Output data contains NaN values for {indicator} at {timeframe}")
            
            # Log sufficiency check (but don't fail on insufficient data)
            self.validate_data_sufficiency(timeframe, data_count)
            
            self.logger.info(f"Successfully processed {data_count} data points for {indicator} at {timeframe}")
            return resampled_data
            
        except Exception as e:
            self.logger.error(f"Error fetching timeframe data for {indicator} at {timeframe}: {e}")
            return None

    def _prepare_data_for_resampling(self, 
                                     raw_data: 'pd.DataFrame', 
                                     value_column: str = 'value',
                                     interpolate: bool = True) -> Optional['pd.DataFrame']:
        """
        Prepare raw data for resampling by ensuring proper datetime index and columns.
        
        Args:
            raw_data: Raw data from repository
            value_column: Name of the value column
            interpolate: Whether to interpolate missing values
            
        Returns:
            Optional[pd.DataFrame]: Prepared data or None if error
        """
        if not self._check_pandas_available():
            return None
        
        import pandas as pd
        
        try:
            data = raw_data.copy()
            
            # Identify date column
            date_column = None
            possible_date_columns = ['date', 'timestamp', 'datetime', 'time']
            
            for col in possible_date_columns:
                if col in data.columns:
                    date_column = col
                    break
            
            # If no standard date column, check if index is already datetime
            if date_column is None:
                if isinstance(data.index, pd.DatetimeIndex):
                    # Index is already datetime, good to go
                    pass
                else:
                    # Try to convert index to datetime
                    try:
                        data.index = pd.to_datetime(data.index)
                    except (ValueError, TypeError):
                        self.logger.error("No valid date column found and index cannot be converted to datetime")
                        return None
            else:
                # Convert date column to datetime and set as index
                try:
                    data[date_column] = pd.to_datetime(data[date_column])
                    data = data.set_index(date_column)
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Error converting date column to datetime: {e}")
                    return None
            
            # Ensure we have the value column
            if value_column not in data.columns:
                # Try to find a numeric column
                numeric_columns = data.select_dtypes(include=['number']).columns
                if len(numeric_columns) == 0:
                    self.logger.error("No numeric columns found for resampling")
                    return None
                elif len(numeric_columns) == 1:
                    # Rename the single numeric column to our expected name
                    data = data.rename(columns={numeric_columns[0]: value_column})
                    self.logger.info(f"Renamed column '{numeric_columns[0]}' to '{value_column}'")
                else:
                    # Multiple numeric columns, use the first one
                    data = data.rename(columns={numeric_columns[0]: value_column})
                    self.logger.warning(f"Multiple numeric columns found, using '{numeric_columns[0]}'")
            
            # Sort by index
            data = data.sort_index()
            
            # Remove duplicates in index
            if data.index.duplicated().any():
                self.logger.warning("Duplicate timestamps found, keeping last occurrence")
                data = data[~data.index.duplicated(keep='last')]
            
            # Handle missing values through interpolation
            if interpolate:
                data = self._interpolate_missing_values(data, value_column)
                if data is None:  # Handle interpolation failure
                    self.logger.error("Interpolation failed, returning None")
                    return None
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error preparing data for resampling: {e}")
            return None

    def _interpolate_missing_values(self, 
                                   data: 'pd.DataFrame', 
                                   value_column: str = 'value') -> Optional['pd.DataFrame']:
        """
        Interpolate missing values in the dataset.
        
        Args:
            data: DataFrame with datetime index
            value_column: Name of the value column to interpolate
            
        Returns:
            Optional[pd.DataFrame]: Data with interpolated missing values or None if error
        """
        if not self._check_pandas_available():
            return None
        
        import pandas as pd
        
        try:
            # Validate that value_column exists
            if value_column not in data.columns:
                self.logger.error(f"Value column '{value_column}' not found in data")
                return None
            
            # Check for missing values
            missing_count = data[value_column].isna().sum()
            if missing_count == 0:
                self.logger.debug("No missing values found, skipping interpolation")
                return data
            
            self.logger.info(f"Found {missing_count} missing values, applying interpolation")
            
            # Create a copy to avoid modifying original data
            interpolated_data = data.copy()
            
            # Get numeric columns for interpolation
            numeric_columns = interpolated_data.select_dtypes(include=['number']).columns
            
            for col in numeric_columns:
                if interpolated_data[col].isna().any():
                    # Apply interpolation with different methods based on data characteristics
                    original_missing = interpolated_data[col].isna().sum()
                    
                    # Try linear interpolation first
                    interpolated_data[col] = interpolated_data[col].interpolate(
                        method='linear', 
                        limit_direction='both',
                        limit=10  # Limit interpolation to 10 consecutive values
                    )
                    
                    # Fill remaining gaps with forward fill, then backward fill
                    # Using new pandas 2.0+ syntax
                    interpolated_data[col] = interpolated_data[col].ffill()
                    interpolated_data[col] = interpolated_data[col].bfill()
                    
                    # Log interpolation results
                    remaining_missing = interpolated_data[col].isna().sum()
                    interpolated_count = original_missing - remaining_missing
                    
                    if interpolated_count > 0:
                        self.logger.info(f"Interpolated {interpolated_count} missing values in column '{col}'")
                    
                    if remaining_missing > 0:
                        self.logger.warning(f"Could not interpolate {remaining_missing} values in column '{col}'")
            
            # Verify no NaN values remain in numeric columns
            final_missing = interpolated_data[numeric_columns].isna().sum().sum()
            if final_missing == 0:
                self.logger.info("All missing values successfully interpolated")
            else:
                self.logger.warning(f"Still have {final_missing} missing values after interpolation")
            
            return interpolated_data
            
        except Exception as e:
            self.logger.error(f"Error during interpolation: {e}")
            return None  # Return None to indicate failure

    def _resample_data(self, 
                       data: 'pd.DataFrame', 
                       pandas_period: str, 
                       timeframe: str,
                       indicator: str) -> Optional['pd.DataFrame']:
        """
        Resample data to specified frequency.
        
        Args:
            data: Prepared data DataFrame with datetime index
            pandas_period: Pandas resampling period string
            timeframe: Timeframe key for logging
            indicator: Indicator name for metadata
            
        Returns:
            Optional[pd.DataFrame]: Resampled data or None if error
        """
        if not self._check_pandas_available():
            return None
        
        import pandas as pd
        
        try:
            # Ensure we have a datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                self.logger.error("Data must have datetime index for resampling")
                return None
            
            # Determine which columns to resample
            numeric_columns = data.select_dtypes(include=['number']).columns.tolist()
            if not numeric_columns:
                self.logger.error("No numeric columns found for resampling")
                return None
            
            # Perform resampling based on timeframe
            if timeframe in ['1h', '4h']:
                # For high-frequency timeframes, use OHLC if we have enough data
                resampled_dict = {}
                
                for col in numeric_columns:
                    # Check if we have multiple values per period for OHLC
                    sample_period = data.resample(pandas_period)[col]
                    if sample_period.count().max() > 1:
                        # Multiple values per period, use OHLC
                        ohlc_data = data[col].resample(pandas_period).ohlc()
                        resampled_dict[f'{col}_open'] = ohlc_data['open']
                        resampled_dict[f'{col}_high'] = ohlc_data['high']
                        resampled_dict[f'{col}_low'] = ohlc_data['low']
                        resampled_dict[f'{col}_close'] = ohlc_data['close']
                        resampled_dict[col] = ohlc_data['close']  # Use close as primary value
                    else:
                        # Single value per period, use last
                        resampled_dict[col] = data[col].resample(pandas_period).last()
                
                resampled = pd.DataFrame(resampled_dict)
                
            elif timeframe in ['1d', '1w', '1m']:
                # For lower frequency, use simple aggregation
                agg_dict = {}
                for col in numeric_columns:
                    agg_dict[col] = 'last'  # Use last value in period
                
                resampled = data[numeric_columns].resample(pandas_period).agg(agg_dict)
                
            else:
                # Default to last value for any other timeframes
                resampled = data[numeric_columns].resample(pandas_period).last()
            
            # Remove completely empty rows
            resampled = resampled.dropna(how='all')
            
            if resampled.empty:
                self.logger.warning(f"No data remaining after resampling for {timeframe}")
                return pd.DataFrame()
            
            # Reset index to get datetime as column but keep as datetime
            resampled = resampled.reset_index()
            
            # Add metadata
            resampled['indicator'] = indicator
            resampled['timeframe'] = timeframe
            
            # Rename index column to 'date' if it's the datetime index
            if resampled.columns[0] in ['date', 'timestamp', 'datetime']:
                resampled = resampled.rename(columns={resampled.columns[0]: 'date'})
            elif isinstance(resampled.iloc[:, 0].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_any_dtype(resampled.iloc[:, 0]):
                resampled = resampled.rename(columns={resampled.columns[0]: 'date'})
            
            return resampled
            
        except Exception as e:
            self.logger.error(f"Error resampling data for {timeframe}: {e}")
            return None

    def _check_pandas_available(self) -> bool:
        """Check if pandas is available for import."""
        try:
            import pandas as pd
            return True
        except ImportError:
            self.logger.warning("pandas is not available - data operations will not work")
            return False

    def get_data_summary(self, data: 'pd.DataFrame') -> Dict[str, Any]:
        """
        Get summary statistics for resampled data.
        
        Args:
            data: Resampled DataFrame
            
        Returns:
            Dict with summary statistics
        """
        if data is None or data.empty:
            return {'status': 'empty', 'count': 0}
        
        try:
            import pandas as pd
            numeric_cols = data.select_dtypes(include=['number']).columns
            summary = {
                'status': 'success',
                'count': len(data),
                'date_range': {
                    'start': data['date'].min() if 'date' in data.columns else None,
                    'end': data['date'].max() if 'date' in data.columns else None
                },
                'columns': list(data.columns),
                'numeric_columns': list(numeric_cols)
            }
            
            if len(numeric_cols) > 0:
                summary['statistics'] = data[numeric_cols].describe().to_dict()
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating data summary: {e}")
            return {'status': 'error', 'message': str(e)}


# Usage Examples
if __name__ == "__main__":
    # Mock repository for testing
    class MockRepository:
        def __init__(self):
            self.name = "MockRepository"
    
    print("=== Enhanced Timeframe Analyzer Test ===")
    
    # Test without repository (config-only usage)
    analyzer = TimeframeAnalyzer()
    print(f"Supported timeframes: {analyzer.get_supported_timeframes()}")
    
    # Test with repository
    repository = MockRepository()
    analyzer_with_repo = TimeframeAnalyzer(repository)
    
    # Test timeframe operations
    timeframe = "1h"
    print(f"\n=== Testing timeframe: {timeframe} ===")
    print(f"Is supported: {analyzer.is_timeframe_supported(timeframe)}")
    print(f"Config: {analyzer.get_timeframe_config(timeframe)}")
    print(f"Pandas period: {analyzer.get_pandas_period(timeframe)}")
    print(f"Lookback periods: {analyzer.get_lookback_periods(timeframe)}")
    print(f"Analysis periods: {analyzer.get_analysis_periods(timeframe)}")
    print(f"Min data points: {analyzer.get_min_data_points(timeframe)}")
    
    # Test date range calculation
    date_range = analyzer.calculate_date_range(timeframe)
    if date_range:
        print(f"Date range: {date_range['start']} to {date_range['end']}")
    
    # Test comprehensive summary
    summary = analyzer.get_timeframe_summary(timeframe)
    print(f"Summary: {summary}")
    
    # Test data sufficiency
    print(f"Data sufficient (5 points): {analyzer.validate_data_sufficiency(timeframe, 5)}")
    print(f"Data sufficient (15 points): {analyzer.validate_data_sufficiency(timeframe, 15)}")
    
    # Test invalid timeframe
    print(f"\n=== Testing invalid timeframe ===")
    invalid_result = analyzer.validate_timeframe("2h")
    print(f"2h validation result: {invalid_result}") 