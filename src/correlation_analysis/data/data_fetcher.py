"""
Data fetcher for correlation analysis module.
Connects to existing MTS database to retrieve crypto price data and macro indicators.
"""

import logging
from typing import List, Dict, Optional
import pandas as pd

from src.data.sqlite_helper import CryptoDatabase


class DataFetcher:
    """
    Real-time data fetcher integrated with MTS pipeline.
    """
    
    def __init__(self):
        """Initialize the data fetcher with MTS database connection."""
        self.logger = logging.getLogger(__name__)
        self.crypto_database = CryptoDatabase()
        
    def get_crypto_prices(self, symbols: List[str], days: int, price_column: str = 'close') -> pd.DataFrame:
        """
        Get crypto prices from existing MTS database.
        
        Args:
            symbols: List of cryptocurrency symbols (e.g., ['bitcoin', 'ethereum'])
            days: Number of days to retrieve
            price_column: Which price to use ('open', 'high', 'low', 'close')
            
        Returns:
            pd.DataFrame: Price data for all symbols, aligned by timestamp
        """
        try:
            all_data = {}
            unique_symbols = list(set(symbols))  # Remove duplicates
            
            for symbol in unique_symbols:
                df = self.crypto_database.get_crypto_data(symbol, days)
                
                # Validate data quality
                if (df.empty or 
                    'timestamp' not in df.columns or 
                    price_column not in df.columns or 
                    df[price_column].isna().all()):
                    self.logger.warning(f"Invalid data for symbol {symbol}")
                    continue
                
                # Prepare data
                symbol_data = df[['timestamp', price_column]].copy()
                symbol_data.rename(columns={price_column: symbol}, inplace=True)
                
                # Validate timestamp format
                try:
                    symbol_data.set_index('timestamp', inplace=True)
                    all_data[symbol] = symbol_data
                except Exception as e:
                    self.logger.warning(f"Invalid timestamp format for {symbol}: {e}")
                    continue
            
            if not all_data:
                self.logger.warning("No valid data found for any symbols")
                return pd.DataFrame()
            
            # Use outer join with forward fill to handle missing data
            result = pd.concat(all_data.values(), axis=1, join='outer')
            result = result.ffill()  # Use new pandas syntax
            # Keep all data - let correlation analysis handle NaN values
            
            self.logger.info(f"Retrieved data for {len(all_data)} symbols over {days} days")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get crypto prices: {e}")
            return pd.DataFrame()  # Return empty DataFrame instead of raising
    
    def get_macro_data(self, indicators: List[str], days: int = 30) -> pd.DataFrame:
        """
        Get macro indicators from existing MTS database.
        
        Args:
            indicators: List of macro indicator names (e.g., ['VIXCLS', 'DGS10'])
            days: Number of days to retrieve
            
        Returns:
            pd.DataFrame: Macro data for all indicators, aligned by date
        """
        try:
            all_data = {}
            unique_indicators = list(set(indicators))  # Remove duplicates
            
            for indicator in unique_indicators:
                df = self.get_macro_data_for_indicator(indicator, days)
                
                # Validate data quality
                if (df.empty or 
                    'date' not in df.columns or 
                    'value' not in df.columns or 
                    df['value'].isna().all()):
                    self.logger.warning(f"Invalid data for indicator {indicator}")
                    continue
                
                # Prepare data
                indicator_data = df[['date', 'value']].copy()
                indicator_data.rename(columns={'value': indicator}, inplace=True)
                
                # Convert date to timestamp for consistency
                try:
                    indicator_data['timestamp'] = pd.to_datetime(indicator_data['date']).astype(int) // 10**6
                    indicator_data.set_index('timestamp', inplace=True)
                    indicator_data.drop('date', axis=1, inplace=True)
                    all_data[indicator] = indicator_data
                except Exception as e:
                    self.logger.warning(f"Invalid date format for {indicator}: {e}")
                    continue
            
            if not all_data:
                self.logger.warning("No valid data found for any indicators")
                return pd.DataFrame()
            
            # Use outer join with forward fill to handle missing data
            result = pd.concat(all_data.values(), axis=1, join='outer')
            result = result.ffill()  # Use new pandas syntax
            
            self.logger.info(f"Retrieved data for {len(all_data)} indicators over {days} days")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get macro data: {e}")
            return pd.DataFrame()
    
    def get_macro_data_for_indicator(self, indicator: str, days: int = 30) -> pd.DataFrame:
        """
        Get macro data for a specific indicator.
        
        Args:
            indicator: Macro indicator name (e.g., 'VIXCLS', 'DGS10')
            days: Number of days to retrieve
            
        Returns:
            pd.DataFrame: Macro data for the indicator
        """
        try:
            # Calculate the cutoff date
            import time
            from datetime import datetime, timedelta
            current_date = datetime.now()
            cutoff_date = (current_date - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query_sql = """
                SELECT 
                    date,
                    value,
                    is_interpolated,
                    is_forward_filled
                FROM macro_indicators 
                WHERE indicator = ? 
                AND date >= ?
                ORDER BY date ASC
            """
            
            df = self.crypto_database.query_to_dataframe(query_sql, (indicator, cutoff_date))
            
            self.logger.debug(f"Retrieved {len(df)} records for {indicator} over {days} days")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get macro data for {indicator}: {e}")
            return pd.DataFrame()
    
    def get_crypto_data_for_correlation(self, primary: str, secondary: str, days: int = 30) -> pd.DataFrame:
        """
        Get crypto data specifically formatted for correlation analysis.
        
        Args:
            primary: Primary cryptocurrency symbol or macro indicator
            secondary: Secondary cryptocurrency symbol or macro indicator
            days: Number of days to retrieve
            
        Returns:
            pd.DataFrame: DataFrame with aligned price data for correlation
        """
        # Determine if we're dealing with crypto or macro data
        crypto_symbols = [primary, secondary]
        macro_indicators = []
        
        # Check if any are macro indicators
        available_macro_indicators = [
            'VIXCLS', 'DGS10', 'DEXCHUS', 'DFF', 'SOFR', 'RRPONTSYD', 
            'BAMLH0A0HYM2', 'DEXUSEU', 'DTWEXBGS'
        ]
        
        for item in [primary, secondary]:
            if item in available_macro_indicators:
                macro_indicators.append(item)
                crypto_symbols.remove(item)
        
        all_data = {}
        
        # Get crypto data if we have crypto symbols
        if crypto_symbols:
            crypto_data = self.get_crypto_prices(crypto_symbols, days)
            if not crypto_data.empty:
                all_data.update(crypto_data.to_dict('series'))
        
        # Get macro data if we have macro indicators
        if macro_indicators:
            macro_data = self.get_macro_data(macro_indicators, days)
            if not macro_data.empty:
                all_data.update(macro_data.to_dict('series'))
        
        if not all_data:
            self.logger.warning(f"No data found for {primary} and {secondary}")
            return pd.DataFrame()
        
        # Combine all data
        result = pd.DataFrame(all_data)
        result = result.ffill()  # Forward fill missing values
        
        return result
