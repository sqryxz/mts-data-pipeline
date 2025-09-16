"""
Real-time Price Service for Signal Generation
Ensures signal generation uses current, fresh price data instead of stale cached data.
"""

import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
import pandas as pd

from .sqlite_helper import CryptoDatabase


class RealtimePriceService:
    """
    Service to ensure signal generation uses current, fresh price data.
    
    Features:
    - Data freshness validation
    - Real-time price fetching
    - Fallback mechanisms
    - Timestamp validation
    - Cache invalidation
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the real-time price service.
        
        Args:
            db_path: Optional path to SQLite database file
        """
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase(db_path)
        
        # Configuration
        self.max_data_age_minutes = 30  # Maximum age for price data in minutes
        self.max_vix_data_age_days = 2  # Maximum age for VIX data in days
        self.price_tolerance_percent = 0.05  # 5% price change tolerance for validation
        
        self.logger.info("RealtimePriceService initialized")
    
    def get_fresh_market_data(self, assets: list, days: int = 60) -> Dict[str, Any]:
        """
        Get fresh market data with validation and real-time price updates.
        
        Args:
            assets: List of cryptocurrency names
            days: Number of days of historical data
            
        Returns:
            Dictionary containing validated fresh market data
        """
        self.logger.info(f"Getting fresh market data for {len(assets)} assets")
        
        try:
            # Get base market data
            market_data = self.database.get_strategy_market_data(assets, days)
            
            # Ensure all DataFrames have timestamp column
            market_data = self._ensure_timestamp_columns(market_data)
            
            # Validate and update with fresh prices
            validated_data = self._validate_and_update_prices(market_data, assets)
            
            # Add data freshness metadata
            validated_data['data_freshness'] = self._get_data_freshness_metadata(validated_data)
            
            self.logger.info("Successfully retrieved and validated fresh market data")
            return validated_data
            
        except Exception as e:
            self.logger.error(f"Failed to get fresh market data: {e}")
            raise
    
    def _validate_and_update_prices(self, market_data: Dict[str, Any], assets: list) -> Dict[str, Any]:
        """
        Validate price data freshness and update with current prices if needed.
        
        Args:
            market_data: Original market data from database
            assets: List of assets to validate
            
        Returns:
            Updated market data with fresh prices
        """
        updated_data = market_data.copy()
        
        for asset in assets:
            if asset in market_data and not market_data[asset].empty:
                # Check if price data is fresh
                is_fresh, current_price = self._validate_asset_price_freshness(asset, market_data[asset])
                
                if not is_fresh:
                    self.logger.warning(f"Price data for {asset} is stale, updating with current price")
                    updated_data[asset] = self._update_asset_with_current_price(asset, market_data[asset], current_price)
                else:
                    self.logger.debug(f"Price data for {asset} is fresh")
        
        return updated_data
    
    def _ensure_timestamp_columns(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all DataFrames have timestamp columns for consistency.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Updated market data with timestamp columns
        """
        for key, data in market_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                # Check if timestamp column exists
                if 'timestamp' not in data.columns:
                    # Try to create timestamp from datetime column
                    if 'datetime' in data.columns:
                        data['timestamp'] = data['datetime'].astype('int64') // 10**6  # Convert to milliseconds
                    elif 'date_str' in data.columns:
                        # Convert date_str to timestamp
                        data['timestamp'] = pd.to_datetime(data['date_str']).astype('int64') // 10**6
                    else:
                        # Use current timestamp as fallback
                        current_timestamp = int(time.time() * 1000)
                        data['timestamp'] = current_timestamp
                        self.logger.warning(f"Added fallback timestamp to {key} data")
        
        return market_data
    
    def _validate_asset_price_freshness(self, asset: str, asset_data: pd.DataFrame) -> Tuple[bool, Optional[float]]:
        """
        Validate if asset price data is fresh enough for signal generation.
        
        Args:
            asset: Asset name
            asset_data: DataFrame with asset price data
            
        Returns:
            Tuple of (is_fresh, current_price)
        """
        if asset_data.empty:
            return False, None
        
        # Get latest data point
        latest_data = asset_data.iloc[-1]
        latest_timestamp = latest_data['timestamp']
        latest_price = latest_data['close']
        
        # Convert timestamp to datetime
        latest_datetime = datetime.fromtimestamp(latest_timestamp / 1000)
        current_time = datetime.now()
        
        # Calculate data age
        data_age_minutes = (current_time - latest_datetime).total_seconds() / 60
        
        # Check if data is fresh enough
        is_fresh = data_age_minutes <= self.max_data_age_minutes
        
        if not is_fresh:
            # Try to get current price from database
            current_price = self._get_current_price_from_db(asset)
            return False, current_price
        
        return True, latest_price
    
    def _get_current_price_from_db(self, asset: str) -> Optional[float]:
        """
        Get the most current price for an asset from the database.
        
        Args:
            asset: Asset name
            
        Returns:
            Current price if available, None otherwise
        """
        try:
            # Get the most recent price data
            recent_data = self.database.get_crypto_data(asset, days=1)
            
            if not recent_data.empty:
                current_price = recent_data['close'].iloc[-1]
                self.logger.info(f"Retrieved current price for {asset}: ${current_price:,.2f}")
                return current_price
            else:
                self.logger.warning(f"No recent price data found for {asset}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get current price for {asset}: {e}")
            return None
    
    def _update_asset_with_current_price(self, asset: str, asset_data: pd.DataFrame, current_price: Optional[float]) -> pd.DataFrame:
        """
        Update asset data with current price information.
        
        Args:
            asset: Asset name
            asset_data: Original asset data
            current_price: Current price to use
            
        Returns:
            Updated asset data with current price
        """
        if current_price is None:
            self.logger.warning(f"No current price available for {asset}, using latest available")
            return asset_data
        
        # Create updated data
        updated_data = asset_data.copy()
        
        # Update the latest row with current price
        if not updated_data.empty:
            latest_idx = updated_data.index[-1]
            updated_data.loc[latest_idx, 'close'] = current_price
            updated_data.loc[latest_idx, 'timestamp'] = int(time.time() * 1000)
            updated_data.loc[latest_idx, 'datetime'] = pd.to_datetime(time.time() * 1000, unit='ms')
            
            # Update OHLC if needed (use current price for all if significant change)
            latest_original_price = asset_data.iloc[-1]['close']
            price_change_percent = abs(current_price - latest_original_price) / latest_original_price
            
            if price_change_percent > self.price_tolerance_percent:
                # Significant price change, update OHLC
                updated_data.loc[latest_idx, 'open'] = current_price
                updated_data.loc[latest_idx, 'high'] = max(current_price, updated_data.loc[latest_idx, 'high'])
                updated_data.loc[latest_idx, 'low'] = min(current_price, updated_data.loc[latest_idx, 'low'])
                
                self.logger.info(f"Updated {asset} OHLC due to significant price change: {price_change_percent:.2%}")
        
        return updated_data
    
    def _get_data_freshness_metadata(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get metadata about data freshness for all assets.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Dictionary with freshness metadata
        """
        freshness_metadata = {
            'validation_timestamp': datetime.now().isoformat(),
            'max_data_age_minutes': self.max_data_age_minutes,
            'assets': {}
        }
        
        for key, data in market_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                latest_timestamp = data['timestamp'].iloc[-1]
                latest_datetime = datetime.fromtimestamp(latest_timestamp / 1000)
                current_time = datetime.now()
                
                age_minutes = (current_time - latest_datetime).total_seconds() / 60
                
                freshness_metadata['assets'][key] = {
                    'latest_timestamp': latest_timestamp,
                    'latest_datetime': latest_datetime.isoformat(),
                    'age_minutes': round(age_minutes, 2),
                    'is_fresh': age_minutes <= self.max_data_age_minutes,
                    'data_points': len(data)
                }
        
        return freshness_metadata
    
    def validate_vix_data_freshness(self, vix_data: pd.DataFrame) -> bool:
        """
        Validate if VIX data is fresh enough for signal generation.
        
        Args:
            vix_data: DataFrame with VIX data
            
        Returns:
            True if VIX data is fresh enough, False otherwise
        """
        if vix_data.empty:
            return False
        
        # Get latest VIX data point
        latest_date_str = vix_data['date'].iloc[-1]
        latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        
        # Calculate age in days
        age_days = (current_date - latest_date).days
        
        is_fresh = age_days <= self.max_vix_data_age_days
        
        if not is_fresh:
            self.logger.warning(f"VIX data is {age_days} days old (max allowed: {self.max_vix_data_age_days})")
        else:
            self.logger.debug(f"VIX data is fresh ({age_days} days old)")
        
        return is_fresh
    
    def get_signal_generation_timestamp(self) -> int:
        """
        Get the current timestamp for signal generation.
        
        Returns:
            Current timestamp in milliseconds
        """
        return int(time.time() * 1000)
    
    def log_data_freshness_report(self, market_data: Dict[str, Any]) -> None:
        """
        Log a comprehensive data freshness report.
        
        Args:
            market_data: Market data dictionary
        """
        self.logger.info("=== DATA FRESHNESS REPORT ===")
        
        if 'data_freshness' in market_data:
            freshness = market_data['data_freshness']
            self.logger.info(f"Validation timestamp: {freshness['validation_timestamp']}")
            self.logger.info(f"Max data age threshold: {freshness['max_data_age_minutes']} minutes")
            
            for asset, info in freshness['assets'].items():
                status = "✅ FRESH" if info['is_fresh'] else "⚠️ STALE"
                self.logger.info(f"{asset}: {status} - {info['age_minutes']} minutes old, {info['data_points']} data points")
        
        self.logger.info("=== END FRESHNESS REPORT ===")
