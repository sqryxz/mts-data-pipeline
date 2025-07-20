"""
Macro Analytics Calculator

Integrates Rate of Change (ROC) and Z-Score calculations with timeframe analysis
for comprehensive macro indicator analytics.
"""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

from .rate_of_change import RateOfChangeCalculator
from .z_score_engine import ZScoreEngine
from .timeframe_analyzer import TimeframeAnalyzer


class MacroCalculator:
    """
    Main calculator class that integrates ROC and z-score engines with timeframe analysis.
    
    This class provides a unified interface for calculating macro indicator metrics
    across different timeframes with proper data handling and validation.
    """
    
    def __init__(self, 
                 repository: Optional['AnalyticsRepository'] = None,
                 roc_calculator: Optional[RateOfChangeCalculator] = None,
                 z_score_engine: Optional[ZScoreEngine] = None,
                 timeframe_analyzer: Optional[TimeframeAnalyzer] = None):
        """
        Initialize the macro calculator with dependencies.
        
        Args:
            repository: Analytics repository for data access
            roc_calculator: Rate of change calculator (auto-created if None)
            z_score_engine: Z-score calculation engine (auto-created if None)
            timeframe_analyzer: Timeframe analysis engine (auto-created if None)
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize repository
        self.repository = repository
        
        # Initialize ROC calculator
        if roc_calculator is None:
            self.roc_calculator = RateOfChangeCalculator()
            self.logger.info("Created default RateOfChangeCalculator")
        else:
            self.roc_calculator = roc_calculator
            self.logger.info("Using provided RateOfChangeCalculator")
        
        # Initialize Z-score engine
        if z_score_engine is None:
            self.z_score_engine = ZScoreEngine()
            self.logger.info("Created default ZScoreEngine")
        else:
            self.z_score_engine = z_score_engine
            self.logger.info("Using provided ZScoreEngine")
        
        # Initialize timeframe analyzer
        if timeframe_analyzer is None:
            self.timeframe_analyzer = TimeframeAnalyzer(repository)
            self.logger.info("Created default TimeframeAnalyzer")
        else:
            self.timeframe_analyzer = timeframe_analyzer
            self.logger.info("Using provided TimeframeAnalyzer")
        
        # Validate dependencies
        self._validate_dependencies()
        
        self.logger.info("MacroCalculator initialized successfully")
    
    def _check_pandas_available(self) -> bool:
        """
        Check if pandas is available for calculations.
        
        Returns:
            bool: True if pandas is available
        """
        try:
            import pandas as pd
            return True
        except ImportError:
            self.logger.error("pandas is required but not available")
            return False
    
    def _validate_dependencies(self) -> None:
        """
        Validate that all required dependencies are properly initialized.
        
        Raises:
            ValueError: If any dependency is invalid
        """
        if not isinstance(self.roc_calculator, RateOfChangeCalculator):
            raise ValueError("roc_calculator must be an instance of RateOfChangeCalculator")
        
        if not isinstance(self.z_score_engine, ZScoreEngine):
            raise ValueError("z_score_engine must be an instance of ZScoreEngine")
        
        if not isinstance(self.timeframe_analyzer, TimeframeAnalyzer):
            raise ValueError("timeframe_analyzer must be an instance of TimeframeAnalyzer")
        
        self.logger.debug("All dependencies validated successfully")
    
    def _validate_data_for_calculation(self, 
                                      data: 'pd.DataFrame', 
                                      metric: str,
                                      value_column: str = 'value') -> bool:
        """
        Validate data meets requirements for calculation.
        
        Args:
            data: DataFrame with indicator data
            metric: Metric to calculate
            value_column: Name of the value column
            
        Returns:
            bool: True if data is valid for calculation
        """
        if not self._check_pandas_available():
            return False
        
        try:
            import pandas as pd
        except ImportError:
            self.logger.error("pandas is required for data validation")
            return False
        
        if data.empty:
            self.logger.error("Data is empty")
            return False
        
        if value_column not in data.columns:
            self.logger.error(f"Value column '{value_column}' not found in data columns: {list(data.columns)}")
            return False
        
        values = data[value_column]
        
        # Check for minimum data requirements
        min_points = {
            'roc': 2, 
            'z_score': 1, 
            'rolling_roc': 24, 
            'rolling_z_score': 30
        }
        required = min_points.get(metric, 1)
        
        valid_values = values.dropna()
        if len(valid_values) < required:
            self.logger.error(f"Insufficient data for {metric}: need {required}, got {len(valid_values)}")
            return False
        
        # Check for data type consistency
        if not pd.api.types.is_numeric_dtype(values):
            self.logger.error(f"Value column '{value_column}' is not numeric: {values.dtype}")
            return False
        
        return True
    
    def _format_result(self, data: Any, metric: str, **metadata) -> Dict[str, Any]:
        """
        Standardize result format across all calculations.
        
        Args:
            data: Calculation result data
            metric: Metric type
            **metadata: Additional metadata
            
        Returns:
            Dict with standardized result format
        """
        is_array = hasattr(data, '__iter__') and not isinstance(data, (str, bytes))
        
        result = {
            'data': data.tolist() if hasattr(data, 'tolist') else data,
            'metric': metric,
            'is_array': is_array,
            'metadata': metadata,
            'calculated_at': datetime.now().isoformat()
        }
        
        return result
    
    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes.
        
        Returns:
            List of supported timeframe strings
        """
        return self.timeframe_analyzer.get_supported_timeframes()
    
    def get_calculator_info(self) -> Dict[str, Any]:
        """
        Get information about the calculator and its components.
        
        Returns:
            Dict with calculator information
        """
        return {
            'calculator_type': 'MacroCalculator',
            'repository_available': self.repository is not None,
            'roc_calculator': type(self.roc_calculator).__name__,
            'z_score_engine': type(self.z_score_engine).__name__,
            'timeframe_analyzer': type(self.timeframe_analyzer).__name__,
            'supported_timeframes': self.get_supported_timeframes(),
            'initialized_at': datetime.now().isoformat()
        }
    
    def validate_indicator(self, indicator: str) -> bool:
        """
        Validate that an indicator can be processed.
        
        Args:
            indicator: Indicator name to validate
            
        Returns:
            bool: True if indicator is valid
        """
        if not indicator or not isinstance(indicator, str):
            self.logger.error(f"Invalid indicator: {indicator}")
            return False
        
        # Additional validation can be added here (e.g., check if indicator exists in repository)
        return True
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate that a timeframe is supported.
        
        Args:
            timeframe: Timeframe to validate
            
        Returns:
            bool: True if timeframe is supported
        """
        return self.timeframe_analyzer.validate_timeframe(timeframe)
    
    def get_available_metrics(self) -> List[str]:
        """
        Get list of available metrics that can be calculated.
        
        Returns:
            List of available metric names
        """
        return [
            'roc',           # Rate of Change
            'z_score',       # Z-Score
            'rolling_roc',   # Rolling Rate of Change
            'rolling_z_score' # Rolling Z-Score
        ]
    
    def _calculate_single_metric(self, 
                                indicator: str, 
                                timeframe: str,
                                value_column: str = 'value',
                                **kwargs) -> Optional[Dict[str, Any]]:
        """
        Calculate ROC and z-score for one timeframe.
        
        Args:
            indicator: Indicator name
            timeframe: Timeframe for calculation
            value_column: Name of the value column in data
            **kwargs: Additional parameters for calculations
            
        Returns:
            Optional[Dict]: Dictionary with both ROC and z-score values
        """
        try:
            # Get data for the timeframe
            data = self.timeframe_analyzer.get_timeframe_data(indicator, timeframe)
            if data is None or data.empty:
                self.logger.error(f"No data available for {indicator} at {timeframe}")
                return None
            
            # Validate data for calculations
            if not self._validate_data_for_calculation(data, 'roc', value_column):
                return None
            
            values = data[value_column]
            
            # Ensure numeric data and handle conversion errors
            try:
                import pandas as pd
                values = pd.to_numeric(values, errors='coerce')
                values = values.dropna()
            except Exception as e:
                self.logger.error(f"Data conversion error: {e}")
                return None
            
            # Calculate ROC
            roc_result = None
            if len(values) >= 2:
                try:
                    roc_value = self.roc_calculator.calculate_roc(values.iloc[-2], values.iloc[-1])
                    roc_result = self._format_result(roc_value, 'roc')
                except Exception as e:
                    self.logger.error(f"ROC calculation error: {e}")
            else:
                self.logger.warning(f"Insufficient data for ROC calculation: {len(values)} values")
            
            # Calculate z-score
            z_score_result = None
            if len(values) >= 1:
                try:
                    latest_value = float(values.iloc[-1])
                    data_list = values.tolist()
                    z_score_value = self.z_score_engine.calculate_z_score_from_data(latest_value, data_list)
                    z_score_result = self._format_result(z_score_value, 'z_score')
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Z-score calculation error: {e}")
            else:
                self.logger.warning(f"Insufficient data for z-score calculation: {len(values)} values")
            
            # Prepare result
            result = {
                'indicator': indicator,
                'timeframe': timeframe,
                'calculations': {}
            }
            
            if roc_result is not None:
                result['calculations']['roc'] = roc_result
            
            if z_score_result is not None:
                result['calculations']['z_score'] = z_score_result
            
            # Add metadata
            result['metadata'] = {
                'data_points': len(values),
                'value_column': value_column,
                'calculation_time': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating single metric for {indicator} at {timeframe}: {e}")
            return None
    
    def _calculate_specific_metric(self, 
                                 data: 'pd.DataFrame', 
                                 metric: str,
                                 value_column: str = 'value',
                                 **kwargs) -> Optional[Dict[str, Any]]:
        """
        Calculate a specific metric on the provided data.
        
        Args:
            data: DataFrame with indicator data
            metric: Metric to calculate
            value_column: Name of the value column
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict]: Calculation results
        """
        if not self._check_pandas_available():
            return None
        
        try:
            import pandas as pd
            
            if data.empty:
                return None
            
            # Extract the value column
            if value_column not in data.columns:
                self.logger.error(f"Value column '{value_column}' not found in data")
                return None
            
            values = data[value_column]
            
            # Ensure numeric data
            try:
                values = pd.to_numeric(values, errors='coerce')
                values = values.dropna()
            except Exception as e:
                self.logger.error(f"Data conversion error: {e}")
                return None
            
            if metric == 'roc':
                # Validate sufficient data for ROC
                if len(values) < 2:
                    self.logger.error("Insufficient data for ROC calculation (need at least 2 values)")
                    return None
                
                # Calculate simple ROC
                try:
                    result = self.roc_calculator.calculate_roc(values.iloc[-2], values.iloc[-1])
                    return self._format_result(result, 'single_roc')
                except Exception as e:
                    self.logger.error(f"ROC calculation error: {e}")
                    return None
            
            elif metric == 'z_score':
                # Calculate z-score for the latest value
                try:
                    latest_value = float(values.iloc[-1])
                    data_list = values.tolist()
                    result = self.z_score_engine.calculate_z_score_from_data(latest_value, data_list)
                    return self._format_result(result, 'single_z_score')
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Z-score calculation error: {e}")
                    return None
            
            elif metric == 'rolling_roc':
                # Calculate rolling ROC
                period = kwargs.get('period', 24)
                try:
                    result = self.roc_calculator.calculate_rolling_roc(values, period)
                    return self._format_result(result, 'rolling_roc', period=period)
                except Exception as e:
                    self.logger.error(f"Rolling ROC calculation error: {e}")
                    return None
            
            elif metric == 'rolling_z_score':
                # Calculate rolling z-scores
                window = kwargs.get('window', 30)
                try:
                    result = self.z_score_engine.calculate_rolling_z_scores(values, window)
                    return self._format_result(result, 'rolling_z_score', window=window)
                except Exception as e:
                    self.logger.error(f"Rolling z-score calculation error: {e}")
                    return None
            
            else:
                self.logger.error(f"Unknown metric: {metric}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error calculating metric {metric}: {e}")
            return None
    
    def calculate_metrics(self, 
                         indicator: str, 
                         timeframes: List[str] = None,
                         value_column: str = 'value',
                         **kwargs) -> Optional[Dict[str, Any]]:
        """
        Calculate metrics for multiple timeframes.
        
        Args:
            indicator: Indicator name
            timeframes: List of timeframes to calculate (defaults to all supported)
            value_column: Name of the value column in data
            **kwargs: Additional parameters for calculations
            
        Returns:
            Optional[Dict]: Dictionary with results for each timeframe
        """
        # Validate indicator
        if not self.validate_indicator(indicator):
            return None
        
        # Use default timeframes if none provided
        if timeframes is None:
            timeframes = self.get_supported_timeframes()
        
        # Validate timeframes
        invalid_timeframes = [tf for tf in timeframes if not self.validate_timeframe(tf)]
        if invalid_timeframes:
            self.logger.error(f"Invalid timeframes: {invalid_timeframes}")
            return None
        
        # Prepare result structure
        result = {
            'indicator': indicator,
            'timeframes': timeframes,
            'calculations': {},
            'metadata': {
                'total_timeframes': len(timeframes),
                'value_column': value_column,
                'calculation_time': datetime.now().isoformat()
            }
        }
        
        # Calculate metrics for each timeframe
        successful_calculations = 0
        failed_calculations = 0
        
        for timeframe in timeframes:
            try:
                self.logger.debug(f"Calculating metrics for {indicator} at {timeframe}")
                
                # Calculate single metric (both ROC and z-score)
                timeframe_result = self._calculate_single_metric(
                    indicator, timeframe, value_column, **kwargs
                )
                
                if timeframe_result is not None:
                    result['calculations'][timeframe] = timeframe_result
                    successful_calculations += 1
                    self.logger.debug(f"Successfully calculated metrics for {timeframe}")
                else:
                    failed_calculations += 1
                    self.logger.warning(f"Failed to calculate metrics for {timeframe}")
                
            except Exception as e:
                failed_calculations += 1
                self.logger.error(f"Error calculating metrics for {timeframe}: {e}")
        
        # Add summary metadata
        result['metadata'].update({
            'successful_calculations': successful_calculations,
            'failed_calculations': failed_calculations,
            'success_rate': successful_calculations / len(timeframes) if timeframes else 0
        })
        
        # Return None if no successful calculations
        if successful_calculations == 0:
            self.logger.error(f"No successful calculations for {indicator}")
            return None
        
        self.logger.info(f"Completed multi-timeframe calculation for {indicator}: "
                        f"{successful_calculations} successful, {failed_calculations} failed")
        
        return result
    
    def calculate_single_metric(self, 
                               indicator: str, 
                               timeframe: str,
                               metric: str = None,
                               value_column: str = 'value',
                               **kwargs) -> Optional[Dict[str, Any]]:
        """
        Calculate a single metric or both ROC and z-score for an indicator at a specific timeframe.
        
        Args:
            indicator: Indicator name
            timeframe: Timeframe for calculation
            metric: Specific metric to calculate ('roc', 'z_score', or None for both)
            value_column: Name of the value column in data
            **kwargs: Additional parameters for the calculation
            
        Returns:
            Optional[Dict]: Calculation results with standardized structure or None if error
        """
        # Sanitize inputs
        if indicator:
            indicator = str(indicator).strip()
        if timeframe:
            timeframe = str(timeframe).strip()
        if metric:
            metric = str(metric).strip().lower()
        
        # Validate inputs
        if not self.validate_indicator(indicator):
            return None
        
        if not self.validate_timeframe(timeframe):
            return None
        
        try:
            # Get data once
            data = self.timeframe_analyzer.get_timeframe_data(indicator, timeframe)
            if data is None or data.empty:
                self.logger.error(f"No data available for {indicator} at {timeframe}")
                return None
            
            # Route calculation based on metric parameter
            if metric is None:
                # Calculate both ROC and z-score
                calculations = {}
                
                # Try ROC calculation
                if self._validate_data_for_calculation(data, 'roc', value_column):
                    roc_result = self._calculate_specific_metric(data, 'roc', value_column, **kwargs)
                    if roc_result is not None:
                        calculations['roc'] = roc_result
                        self.logger.debug(f"Successfully calculated ROC for {indicator} at {timeframe}")
                    else:
                        self.logger.warning(f"Failed to calculate ROC for {indicator} at {timeframe}")
                else:
                    self.logger.warning(f"Data validation failed for ROC calculation")
                
                # Try z-score calculation
                if self._validate_data_for_calculation(data, 'z_score', value_column):
                    z_score_result = self._calculate_specific_metric(data, 'z_score', value_column, **kwargs)
                    if z_score_result is not None:
                        calculations['z_score'] = z_score_result
                        self.logger.debug(f"Successfully calculated z-score for {indicator} at {timeframe}")
                    else:
                        self.logger.warning(f"Failed to calculate z-score for {indicator} at {timeframe}")
                else:
                    self.logger.warning(f"Data validation failed for z-score calculation")
                
                # Return standardized structure for both calculations
                result = {
                    'indicator': indicator,
                    'timeframe': timeframe,
                    'calculations': calculations,
                    'metadata': {
                        'calculation_time': datetime.now().isoformat(),
                        'data_points': len(data),
                        'value_column': value_column,
                        'calculation_type': 'both_metrics',
                        'successful_calculations': len(calculations),
                        'total_attempted': 2
                    }
                }
                
            else:
                # Calculate specific metric
                if metric not in self.get_available_metrics():
                    self.logger.error(f"Unsupported metric: {metric}")
                    return None
                
                # Validate data for the specific metric
                if not self._validate_data_for_calculation(data, metric, value_column):
                    return None
                
                # Calculate the specific metric
                calc_result = self._calculate_specific_metric(data, metric, value_column, **kwargs)
                if calc_result is None:
                    self.logger.error(f"Failed to calculate {metric} for {indicator} at {timeframe}")
                    return None
                
                # Return standardized structure for single calculation
                result = {
                    'indicator': indicator,
                    'timeframe': timeframe,
                    'calculation': calc_result,  # Single calculation
                    'metadata': {
                        'calculation_time': datetime.now().isoformat(),
                        'data_points': len(data),
                        'value_column': value_column,
                        'calculation_type': 'single_metric',
                        'metric': metric,
                        'successful_calculations': 1,
                        'total_attempted': 1
                    }
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calculating {metric or 'all metrics'} for {indicator} at {timeframe}: {e}")
            return None
    
    def get_calculation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the calculator's capabilities and status.
        
        Returns:
            Dict with calculator summary
        """
        return {
            'calculator_info': self.get_calculator_info(),
            'available_metrics': self.get_available_metrics(),
            'supported_timeframes': self.get_supported_timeframes(),
            'repository_available': self.repository is not None,
            'pandas_available': self._check_pandas_available(),
            'status': 'ready'
        }


# Type hints for better IDE support
if __name__ == "__main__":
    # Example usage
    print("=== MacroCalculator Example ===")
    
    # Create calculator with default components
    calculator = MacroCalculator()
    
    # Get calculator info
    info = calculator.get_calculator_info()
    print(f"Calculator Info: {info}")
    
    # Get available metrics
    metrics = calculator.get_available_metrics()
    print(f"Available Metrics: {metrics}")
    
    # Get supported timeframes
    timeframes = calculator.get_supported_timeframes()
    print(f"Supported Timeframes: {timeframes}")
    
    print("=== Example completed ===") 