"""
Data validator for correlation analysis module.
Validates price data completeness and quality.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class DataValidator:
    """
    Validates price data quality for correlation analysis.
    """
    
    def __init__(self, expected_frequency: str = 'D'):
        """
        Initialize the data validator.
        
        Args:
            expected_frequency: Expected frequency ('D', 'H', '5T', etc.)
        """
        self.logger = logging.getLogger(__name__)
        self.expected_frequency = expected_frequency
        
        # Set appropriate gap thresholds based on frequency
        frequency_gaps = {
            'D': pd.Timedelta(days=2),      # Daily: 2 days max gap
            'H': pd.Timedelta(hours=3),     # Hourly: 3 hours max gap
            '5T': pd.Timedelta(minutes=15), # 5-minute: 15 minutes max gap
            'T': pd.Timedelta(minutes=5),   # 1-minute: 5 minutes max gap
        }
        self.max_gap = frequency_gaps.get(expected_frequency, pd.Timedelta(hours=24))
        
    def _parse_timestamps(self, df: pd.DataFrame) -> Optional[pd.DatetimeIndex]:
        """
        Safely parse timestamps regardless of format.
        
        Args:
            df: DataFrame with timestamp index
            
        Returns:
            pd.DatetimeIndex or None: Parsed timestamps
        """
        try:
            # If already datetime, return as-is
            if isinstance(df.index, pd.DatetimeIndex):
                return df.index
            
            # Try different formats
            try:
                # Try milliseconds first
                return pd.to_datetime(df.index, unit='ms')
            except (ValueError, OSError):
                try:
                    # Try seconds
                    return pd.to_datetime(df.index, unit='s')
                except (ValueError, OSError):
                    # Try parsing as string
                    return pd.to_datetime(df.index)
        except Exception as e:
            self.logger.warning(f"Could not parse timestamps: {e}")
            return None
    
    def _detect_outliers(self, series: pd.Series, method: str = 'iqr') -> pd.Series:
        """
        Detect outliers using multiple methods.
        
        Args:
            series: Price series
            method: 'iqr', 'zscore', or 'percentage'
            
        Returns:
            pd.Series: Boolean series indicating outliers
        """
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            # Use 3.0 instead of 1.5 for crypto data (less aggressive)
            lower_bound = Q1 - 3.0 * IQR
            upper_bound = Q3 + 3.0 * IQR
            return (series < lower_bound) | (series > upper_bound)
        
        elif method == 'percentage':
            # Flag extreme percentage changes (>500% in one period)
            pct_change = series.pct_change().abs()
            return pct_change > 5.0  # 500% change threshold
        
        elif method == 'zscore':
            from scipy import stats
            z_scores = np.abs(stats.zscore(series.dropna()))
            return z_scores > 4  # 4 standard deviations
        
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    def _check_correlation_readiness(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Check if data is suitable for correlation analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            Dict[str, bool]: Correlation-specific validation results
        """
        results = {}
        
        for column in df.columns:
            series = df[column].dropna()
            
            # Check for constant values
            is_constant = series.nunique() <= 1
            results[f'{column}_constant'] = not is_constant
            
            # Check for sufficient variance
            has_variance = series.var() > 1e-10
            results[f'{column}_variance'] = has_variance
            
            # Check for reasonable data distribution
            has_distribution = len(series.unique()) > len(series) * 0.1
            results[f'{column}_distribution'] = has_distribution
            
            if is_constant:
                self.logger.warning(f"Column {column} has constant values - correlation will be NaN")
            if not has_variance:
                self.logger.warning(f"Column {column} has insufficient variance for correlation")
        
        return results
        
    def validate_price_data(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Validate price data completeness and quality.
        
        Args:
            df: DataFrame with price data (timestamp index, symbol columns)
            
        Returns:
            Dict[str, bool]: Validation results with status for each check
        """
        validation_results = {
            'has_data': False,
            'no_missing_values': False,
            'no_outliers': False,
            'consistent_timestamps': False,
            'valid_prices': False,
            'sufficient_data_points': False,
            'correlation_ready': False
        }
        
        try:
            # Check if DataFrame has data
            if df.empty:
                self.logger.warning("DataFrame is empty")
                return validation_results
            
            validation_results['has_data'] = True
            
            # Check for missing values
            missing_count = df.isna().sum().sum()
            if missing_count == 0:
                validation_results['no_missing_values'] = True
            else:
                self.logger.warning(f"Found {missing_count} missing values")
            
            # Check for outliers using improved method
            outliers_found = False
            for column in df.columns:
                if df[column].dtype in ['float64', 'int64']:
                    outliers = self._detect_outliers(df[column], method='iqr')
                    outlier_count = outliers.sum()
                    if outlier_count > 0:
                        outliers_found = True
                        self.logger.warning(f"Found {outlier_count} outliers in {column}")
            
            if not outliers_found:
                validation_results['no_outliers'] = True
            
            # Check for consistent timestamps using improved parsing
            timestamps = self._parse_timestamps(df)
            if timestamps is not None and not timestamps.empty:
                time_diffs = timestamps.diff().dropna()
                large_gaps = time_diffs[time_diffs > self.max_gap]
                
                if len(large_gaps) == 0:
                    validation_results['consistent_timestamps'] = True
                else:
                    self.logger.warning(f"Found {len(large_gaps)} large timestamp gaps (max allowed: {self.max_gap})")
            
            # Check for valid prices (positive values)
            negative_prices = (df < 0).sum().sum()
            if negative_prices == 0:
                validation_results['valid_prices'] = True
            else:
                self.logger.warning(f"Found {negative_prices} negative price values")
            
            # Check for sufficient data points (at least 20 for correlation)
            min_data_points = 20
            if len(df) >= min_data_points:
                validation_results['sufficient_data_points'] = True
            else:
                self.logger.warning(f"Insufficient data points: {len(df)} < {min_data_points}")
            
            # Check correlation readiness
            correlation_checks = self._check_correlation_readiness(df)
            if all(correlation_checks.values()):
                validation_results['correlation_ready'] = True
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return validation_results
    
    def get_validation_summary(self, validation_results: Dict[str, bool]) -> str:
        """
        Get a summary of validation results.
        
        Args:
            validation_results: Results from validate_price_data()
            
        Returns:
            str: Human-readable validation summary
        """
        passed_checks = sum(validation_results.values())
        total_checks = len(validation_results)
        
        summary = f"Data validation: {passed_checks}/{total_checks} checks passed\n"
        
        for check, passed in validation_results.items():
            status = "✅" if passed else "❌"
            summary += f"  {status} {check.replace('_', ' ').title()}\n"
        
        return summary
    
    def validate_correlation_data(self, df: pd.DataFrame, min_correlation_points: int = 20) -> bool:
        """
        Validate data specifically for correlation analysis.
        
        Args:
            df: DataFrame with price data for correlation
            min_correlation_points: Minimum data points required for correlation
            
        Returns:
            bool: True if data is suitable for correlation analysis
        """
        validation_results = self.validate_price_data(df)
        
        # For correlation, we need at least 2 columns and sufficient data points
        has_multiple_columns = len(df.columns) >= 2
        has_sufficient_data = validation_results['sufficient_data_points']
        has_valid_data = validation_results['has_data']
        is_correlation_ready = validation_results['correlation_ready']
        
        is_valid = (has_multiple_columns and has_sufficient_data and 
                   has_valid_data and is_correlation_ready)
        
        if is_valid:
            self.logger.info("Data is suitable for correlation analysis")
        else:
            self.logger.warning("Data is not suitable for correlation analysis")
            
        return is_valid
