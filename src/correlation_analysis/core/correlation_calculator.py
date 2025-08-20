"""
Correlation calculator for correlation analysis module.
Provides statistical correlation calculations.
"""

import logging
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Tuple
from scipy import stats


class CorrelationCalculator:
    """
    Statistical correlation calculations for correlation analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the correlation calculator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = {
            'min_data_points': 10,
            'significance_threshold': 0.05,
            'default_correlation_method': 'pearson'
        }
        
        if config:
            self.config.update(config)
        
    def calculate_correlation(self, data: pd.DataFrame, asset1: str, asset2: str, window_days: int) -> float:
        """
        Calculate Pearson correlation for single window.
        
        Args:
            data: DataFrame with price data (timestamp index, symbol columns)
            asset1: First asset column name
            asset2: Second asset column name
            window_days: Number of days for correlation window
            
        Returns:
            float: Pearson correlation coefficient (-1 to 1)
        """
        try:
            if data.empty:
                self.logger.warning("Empty data for correlation calculation")
                return np.nan
            
            # Validate that both assets exist in the data
            if asset1 not in data.columns or asset2 not in data.columns:
                self.logger.warning(f"Assets not found in data: {asset1}, {asset2}")
                return np.nan
            
            # Get time-based window data
            recent_data = self._get_window_data(data, window_days)
            
            if recent_data.empty:
                self.logger.warning(f"No data available for {window_days}-day window")
                return np.nan
            
            # Ensure we have enough data points
            if len(recent_data) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient data points for correlation: {len(recent_data)} < {self.config['min_data_points']}")
                return np.nan
            
            # Remove any NaN values
            clean_data = recent_data[[asset1, asset2]].dropna()
            
            if len(clean_data) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient clean data points: {len(clean_data)} < {self.config['min_data_points']}")
                return np.nan
            
            # Check for zero variance (constant values) to avoid division by zero
            asset1_var = clean_data[asset1].var()
            asset2_var = clean_data[asset2].var()
            
            if asset1_var == 0 or asset2_var == 0 or np.isnan(asset1_var) or np.isnan(asset2_var):
                self.logger.warning(f"Zero or invalid variance detected: {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return np.nan
            
            # Additional check for very small variance that could cause numerical issues
            if asset1_var < 1e-10 or asset2_var < 1e-10:
                self.logger.warning(f"Very small variance detected (numerical instability): {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return np.nan
            
            # Calculate Pearson correlation with warning suppression for division by zero
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                correlation = clean_data[asset1].corr(clean_data[asset2], method='pearson')
            
            self.logger.debug(f"Calculated correlation for {asset1}-{asset2}: {correlation:.4f} (window: {window_days} days)")
            
            return correlation
            
        except Exception as e:
            self.logger.error(f"Correlation calculation failed: {e}")
            return np.nan
    
    def calculate_spearman_correlation(self, data: pd.DataFrame, asset1: str, asset2: str, window_days: int) -> float:
        """
        Calculate Spearman correlation for single window.
        
        Args:
            data: DataFrame with price data (timestamp index, symbol columns)
            asset1: First asset column name
            asset2: Second asset column name
            window_days: Number of days for correlation window
            
        Returns:
            float: Spearman correlation coefficient (-1 to 1)
        """
        try:
            if data.empty:
                self.logger.warning("Empty data for correlation calculation")
                return np.nan
            
            # Validate that both assets exist in the data
            if asset1 not in data.columns or asset2 not in data.columns:
                self.logger.warning(f"Assets not found in data: {asset1}, {asset2}")
                return np.nan
            
            # Get time-based window data
            recent_data = self._get_window_data(data, window_days)
            
            if recent_data.empty:
                self.logger.warning(f"No data available for {window_days}-day window")
                return np.nan
            
            # Ensure we have enough data points
            if len(recent_data) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient data points for correlation: {len(recent_data)} < {self.config['min_data_points']}")
                return np.nan
            
            # Remove any NaN values
            clean_data = recent_data[[asset1, asset2]].dropna()
            
            if len(clean_data) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient clean data points: {len(clean_data)} < {self.config['min_data_points']}")
                return np.nan
            
            # Check for zero variance (constant values) to avoid division by zero
            asset1_var = clean_data[asset1].var()
            asset2_var = clean_data[asset2].var()
            
            if asset1_var == 0 or asset2_var == 0 or np.isnan(asset1_var) or np.isnan(asset2_var):
                self.logger.warning(f"Zero or invalid variance detected: {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return np.nan
            
            # Additional check for very small variance that could cause numerical issues
            if asset1_var < 1e-10 or asset2_var < 1e-10:
                self.logger.warning(f"Very small variance detected (numerical instability): {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return np.nan
            
            # Calculate Spearman correlation with warning suppression for division by zero
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                correlation = clean_data[asset1].corr(clean_data[asset2], method='spearman')
            
            self.logger.debug(f"Calculated Spearman correlation for {asset1}-{asset2}: {correlation:.4f} (window: {window_days} days)")
            
            return correlation
            
        except Exception as e:
            self.logger.error(f"Spearman correlation calculation failed: {e}")
            return np.nan
    
    def calculate_correlation_with_significance(self, data: pd.DataFrame, asset1: str, asset2: str, window_days: int) -> Dict[str, float]:
        """
        Calculate correlation with statistical significance test.
        
        Args:
            data: DataFrame with price data (timestamp index, symbol columns)
            asset1: First asset column name
            asset2: Second asset column name
            window_days: Number of days for correlation window
            
        Returns:
            Dict[str, float]: Dictionary with correlation, p-value, and significance
        """
        try:
            if data.empty:
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Validate that both assets exist in the data
            if asset1 not in data.columns or asset2 not in data.columns:
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Get time-based window data
            recent_data = self._get_window_data(data, window_days)
            
            if recent_data.empty:
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Ensure we have enough data points
            if len(recent_data) < self.config['min_data_points']:
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Remove any NaN values
            clean_data = recent_data[[asset1, asset2]].dropna()
            
            if len(clean_data) < self.config['min_data_points']:
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Check for zero variance (constant values) to avoid division by zero
            asset1_var = clean_data[asset1].var()
            asset2_var = clean_data[asset2].var()
            
            if asset1_var == 0 or asset2_var == 0 or np.isnan(asset1_var) or np.isnan(asset2_var):
                self.logger.warning(f"Zero or invalid variance detected: {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Additional check for very small variance that could cause numerical issues
            if asset1_var < 1e-10 or asset2_var < 1e-10:
                self.logger.warning(f"Very small variance detected (numerical instability): {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
            
            # Calculate correlation and p-value with warning suppression for division by zero
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                correlation, p_value = stats.pearsonr(clean_data[asset1], clean_data[asset2])
            
            # Determine significance
            significant = p_value < self.config['significance_threshold']
            
            result = {
                'correlation': correlation,
                'p_value': p_value,
                'significant': significant
            }
            
            self.logger.debug(f"Correlation with significance: {correlation:.4f}, p={p_value:.4f}, significant={significant}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Correlation with significance calculation failed: {e}")
            return {'correlation': np.nan, 'p_value': np.nan, 'significant': False}
    
    def calculate_rolling_correlations(self, data: pd.DataFrame, asset1: str, asset2: str, windows: List[int]) -> Dict[int, pd.Series]:
        """
        Calculate rolling correlations for multiple windows.
        
        Args:
            data: DataFrame with price data (timestamp index, symbol columns)
            asset1: First asset column name
            asset2: Second asset column name
            windows: List of window sizes in days
            
        Returns:
            Dict[int, pd.Series]: Dictionary with window size -> correlation time series
        """
        try:
            if data.empty:
                self.logger.warning("Empty data for rolling correlation calculation")
                return {}
            
            # Validate that both assets exist in the data
            if asset1 not in data.columns or asset2 not in data.columns:
                self.logger.warning(f"Assets not found in data: {asset1}, {asset2}")
                return {}
            
            # Ensure we have a datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                self.logger.error("Data index must be DatetimeIndex for rolling correlations")
                return {}
            
            results = {}
            
            for window_days in windows:
                try:
                    # Calculate rolling correlation for this window
                    rolling_corr = self._calculate_rolling_correlation(data, asset1, asset2, window_days)
                    
                    if not rolling_corr.empty:
                        results[window_days] = rolling_corr
                        self.logger.debug(f"Calculated rolling correlation for {window_days}-day window: {len(rolling_corr)} points")
                    else:
                        self.logger.warning(f"No rolling correlation data for {window_days}-day window")
                        
                except Exception as e:
                    self.logger.error(f"Failed to calculate rolling correlation for {window_days}-day window: {e}")
                    continue
            
            self.logger.info(f"Calculated rolling correlations for {len(results)} windows: {list(results.keys())}")
            return results
            
        except Exception as e:
            self.logger.error(f"Rolling correlation calculation failed: {e}")
            return {}
    
    def _calculate_rolling_correlation(self, data: pd.DataFrame, asset1: str, asset2: str, window_days: int) -> pd.Series:
        """
        Calculate rolling correlation for a single window size.
        
        Args:
            data: DataFrame with price data (timestamp index, symbol columns)
            asset1: First asset column name
            asset2: Second asset column name
            window_days: Window size in days
            
        Returns:
            pd.Series: Rolling correlation time series
        """
        try:
            # Get clean data for the two assets
            clean_data = data[[asset1, asset2]].dropna()
            
            if len(clean_data) < 20:  # Minimum data requirement
                self.logger.warning(f"Insufficient data for rolling correlation: {len(clean_data)} < 20")
                return pd.Series(dtype=float)
            
            # Check overall variance before rolling calculation
            asset1_var = clean_data[asset1].var()
            asset2_var = clean_data[asset2].var()
            
            if asset1_var == 0 or asset2_var == 0 or np.isnan(asset1_var) or np.isnan(asset2_var):
                self.logger.warning(f"Zero or invalid variance in rolling correlation: {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return pd.Series(dtype=float)
            
            # Check for very small variance
            if asset1_var < 1e-10 or asset2_var < 1e-10:
                self.logger.warning(f"Very small variance in rolling correlation: {asset1}_var={asset1_var}, {asset2}_var={asset2_var}")
                return pd.Series(dtype=float)
            
            # Use simple window sizes that work with the data
            # For high-frequency data, use reasonable window sizes
            if window_days == 7:
                window_size = 168  # 7 days * 24 hours
            elif window_days == 14:
                window_size = 336  # 14 days * 24 hours
            elif window_days == 30:
                window_size = 720  # 30 days * 24 hours
            else:
                window_size = window_days * 24  # Default assumption
            
            # Ensure window size doesn't exceed data length
            window_size = min(window_size, len(clean_data) // 2)
            min_periods = max(window_size // 2, 10)
            
            self.logger.debug(f"Window calculation: {window_days} days = {window_size} data points, min_periods={min_periods}")
            
            # Calculate rolling correlation with warning suppression for division by zero
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=RuntimeWarning, message='invalid value encountered in divide')
                rolling_corr = clean_data[asset1].rolling(window=window_size, min_periods=min_periods).corr(clean_data[asset2])
            
            # Remove NaN and infinite values
            rolling_corr = rolling_corr.replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(rolling_corr) > 0:
                self.logger.debug(f"Rolling correlation calculated: {len(rolling_corr)} points for {window_days}-day window")
            
            return rolling_corr
            
        except Exception as e:
            self.logger.error(f"Rolling correlation calculation failed for {window_days}-day window: {e}")
            return pd.Series(dtype=float)
    
    def _get_window_data(self, data: pd.DataFrame, window_days: int) -> pd.DataFrame:
        """
        Get data for the specified time window.
        
        Args:
            data: DataFrame with datetime index
            window_days: Number of days for the window
            
        Returns:
            pd.DataFrame: Data for the specified time window
        """
        if data.empty:
            return pd.DataFrame()
        
        # Ensure we have a datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.error("Data index must be DatetimeIndex for time-based windows")
            return pd.DataFrame()
        
        # Calculate the start date for the window
        end_date = data.index.max()
        start_date = end_date - pd.Timedelta(days=window_days)
        
        # Get data for the window
        window_data = data[data.index >= start_date]
        
        self.logger.debug(f"Window data: {len(window_data)} rows from {start_date} to {end_date}")
        
        return window_data
