"""
Data normalizer for correlation analysis module.
Aligns timestamps and normalizes prices for correlation analysis.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


class DataNormalizer:
    """
    Normalizes and aligns data for correlation analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the data normalizer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.config = {
            'outlier_method': 'iqr',
            'iqr_multiplier': 3.0,
            'zscore_threshold': 4.0,
            'max_fill_gap_hours': 4,
            'min_data_points': 20,
            'stationarity_threshold': 0.05
        }
        
        if config:
            self.config.update(config)
        
    def normalize_and_align(self, crypto_data: pd.DataFrame) -> pd.DataFrame:
        """
        Align timestamps and normalize prices for correlation analysis.
        
        Args:
            crypto_data: DataFrame with price data (timestamp index, symbol columns)
            
        Returns:
            pd.DataFrame: Clean, aligned data ready for correlation analysis
        """
        try:
            if crypto_data.empty:
                self.logger.warning("Input data is empty")
                return pd.DataFrame()
            
            # Step 1: Parse and validate timestamps
            normalized_data = self._parse_timestamps(crypto_data)
            if normalized_data is None:
                return pd.DataFrame()
            
            # Step 2: Handle missing values with gap limits
            normalized_data = self._handle_missing_values(normalized_data)
            
            # Step 3: Remove outliers
            normalized_data = self._remove_outliers(normalized_data)
            
            # Step 4: Align timestamps (resample if needed)
            normalized_data = self._align_timestamps(normalized_data)
            
            # Step 5: Final validation
            if len(normalized_data) < self.config['min_data_points']:
                self.logger.warning(f"Insufficient data after normalization: {len(normalized_data)} < {self.config['min_data_points']}")
                return pd.DataFrame()
            
            self.logger.info(f"Normalized data: {len(normalized_data)} rows, {len(normalized_data.columns)} columns")
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Data normalization failed: {e}")
            return pd.DataFrame()
    
    def _parse_timestamps(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Parse timestamps and ensure proper datetime index.
        
        Args:
            df: DataFrame with timestamp index
            
        Returns:
            pd.DataFrame: DataFrame with proper datetime index
        """
        try:
            # If already datetime, return as-is
            if isinstance(df.index, pd.DatetimeIndex):
                return df.copy()
            
            # Try different timestamp formats
            try:
                # Try milliseconds first
                timestamps = pd.to_datetime(df.index, unit='ms')
            except (ValueError, OSError):
                try:
                    # Try seconds
                    timestamps = pd.to_datetime(df.index, unit='s')
                except (ValueError, OSError):
                    # Try parsing as string
                    timestamps = pd.to_datetime(df.index)
            
            # Create new DataFrame with proper datetime index
            result = df.copy()
            result.index = timestamps
            
            self.logger.debug(f"Parsed timestamps: {len(result)} rows from {result.index.min()} to {result.index.max()}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to parse timestamps: {e}")
            return None
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values with gap size limits.
        
        Args:
            df: DataFrame with datetime index
            
        Returns:
            pd.DataFrame: DataFrame with missing values filled (limited by gap size)
        """
        result = df.copy()
        missing_before = result.isna().sum().sum()
        
        if missing_before > 0:
            max_gap = pd.Timedelta(hours=self.config['max_fill_gap_hours'])
            
            for column in result.columns:
                series = result[column]
                missing_mask = series.isna()
                
                if missing_mask.any():
                    # Find consecutive missing periods
                    missing_groups = missing_mask.ne(missing_mask.shift()).cumsum()
                    
                    for group_id in missing_groups[missing_mask].unique():
                        group_mask = (missing_groups == group_id) & missing_mask
                        gap_start = group_mask.idxmax()
                        gap_end = group_mask[::-1].idxmax()
                        gap_duration = gap_end - gap_start
                        
                        if gap_duration <= max_gap:
                            # Fill small gaps with forward fill only
                            result.loc[group_mask, column] = series.ffill().loc[group_mask]
                        else:
                            # Log large gaps and leave as NaN
                            self.logger.warning(f"Large gap in {column}: {gap_duration} at {gap_start}")
            
            # Drop rows where all columns are NaN after selective filling
            result = result.dropna(how='all')
            
            filled_count = missing_before - result.isna().sum().sum()
            if filled_count > 0:
                self.logger.info(f"Filled {filled_count} missing values, dropped large gaps")
        
        return result
    
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove outliers using specified method.
        
        Args:
            df: DataFrame with price data
            method: 'iqr', 'zscore', or 'none'
            
        Returns:
            pd.DataFrame: DataFrame with outliers removed
        """
        method = self.config['outlier_method']
        if method == 'none':
            return df
        
        result = df.copy()
        outliers_removed = 0
        
        for column in df.columns:
            if df[column].dtype in ['float64', 'int64']:
                series = df[column].dropna()
                
                if method == 'iqr':
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    # Use configurable multiplier for crypto data
                    lower_bound = Q1 - self.config['iqr_multiplier'] * IQR
                    upper_bound = Q3 + self.config['iqr_multiplier'] * IQR
                    
                    outliers = (series < lower_bound) | (series > upper_bound)
                    outlier_count = outliers.sum()
                    
                    if outlier_count > 0:
                        # Replace outliers with NaN (will be handled by missing value logic)
                        result.loc[result.index.isin(series[outliers].index), column] = np.nan
                        outliers_removed += outlier_count
                        self.logger.debug(f"Removed {outlier_count} outliers from {column}")
                
                elif method == 'zscore':
                    from scipy import stats
                    z_scores = np.abs(stats.zscore(series))
                    outliers = z_scores > self.config['zscore_threshold']
                    outlier_count = outliers.sum()
                    
                    if outlier_count > 0:
                        result.loc[result.index.isin(series[outliers].index), column] = np.nan
                        outliers_removed += outlier_count
                        self.logger.debug(f"Removed {outlier_count} outliers from {column}")
        
        if outliers_removed > 0:
            self.logger.info(f"Removed {outliers_removed} outliers total")
        
        return result
    
    def _align_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Align timestamps and handle large gaps.
        
        Args:
            df: DataFrame with datetime index
            
        Returns:
            pd.DataFrame: DataFrame with aligned timestamps
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        # Detect and handle large gaps
        time_diffs = result.index.to_series().diff()
        large_gaps = time_diffs[time_diffs > pd.Timedelta(hours=24)]
        
        if len(large_gaps) > 0:
            self.logger.info(f"Found {len(large_gaps)} large timestamp gaps")
            
            # For large gaps, we could either:
            # 1. Remove the gap period (if it's a weekend/holiday)
            # 2. Interpolate across the gap
            # 3. Keep as-is and let correlation handle it
            
            # For now, we'll keep the data as-is but log the gaps
            for gap_start, gap_duration in large_gaps.items():
                self.logger.debug(f"Large gap at {gap_start}: {gap_duration}")
        
        return result
    
    def _check_stationarity(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Check stationarity for correlation analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            Dict[str, bool]: Stationarity results for each column
        """
        results = {}
        
        try:
            from statsmodels.tsa.stattools import adfuller
        except ImportError:
            self.logger.warning("statsmodels not available, skipping stationarity test")
            return {col: True for col in df.columns}
        
        for column in df.columns:
            series = df[column].dropna()
            
            if len(series) > 20:
                try:
                    adf_stat, p_value = adfuller(series)[:2]
                    is_stationary = p_value < self.config['stationarity_threshold']
                    results[column] = is_stationary
                    
                    if not is_stationary:
                        self.logger.info(f"{column} not stationary (p={p_value:.4f})")
                except Exception as e:
                    self.logger.warning(f"Stationarity test failed for {column}: {e}")
                    results[column] = False
            else:
                results[column] = False
        
        return results
    
    def prepare_for_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data specifically for correlation analysis.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            pd.DataFrame: Data ready for correlation analysis
        """
        # First normalize
        clean_data = self.normalize_and_align(df)
        
        if clean_data.empty:
            return clean_data
        
        # Check stationarity
        stationarity = self._check_stationarity(clean_data)
        non_stationary = [col for col, is_stat in stationarity.items() if not is_stat]
        
        if non_stationary:
            self.logger.info(f"Converting to returns for stationarity: {non_stationary}")
            # Use returns for correlation
            returns = clean_data.pct_change().dropna()
            returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
            return returns
        else:
            return clean_data
    
    def normalize_for_correlation(self, primary: str, secondary: str, days: int = 30) -> pd.DataFrame:
        """
        Normalize data specifically for correlation analysis between two assets.
        
        Args:
            primary: Primary cryptocurrency symbol
            secondary: Secondary cryptocurrency symbol
            days: Number of days to retrieve
            
        Returns:
            pd.DataFrame: Normalized data ready for correlation
        """
        from .data_fetcher import DataFetcher
        
        # Get raw data
        fetcher = DataFetcher()
        raw_data = fetcher.get_crypto_data_for_correlation(primary, secondary, days)
        
        if raw_data.empty:
            self.logger.warning("No data retrieved for correlation")
            return pd.DataFrame()
        
        # Prepare data for correlation (includes stationarity testing)
        normalized_data = self.prepare_for_correlation(raw_data)
        
        if not normalized_data.empty:
            self.logger.info(f"Normalized correlation data: {len(normalized_data)} rows")
        
        return normalized_data
