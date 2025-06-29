from typing import List, Dict, Any, Optional
from .models import OHLCVData


class DataValidator:
    """Validator class for checking data quality before storage."""
    
    def validate_ohlcv_data(self, data: List[List[float]]) -> bool:
        """
        Validate OHLCV data from API response.
        
        Args:
            data: List of OHLCV arrays [timestamp, open, high, low, close, volume]
            
        Returns:
            True if data is valid, False otherwise
        """
        if not data:
            return False
        
        for entry in data:
            if not self._validate_single_ohlcv_entry(entry):
                return False
        
        return True
    
    def _validate_single_ohlcv_entry(self, entry: List[float]) -> bool:
        """Validate a single OHLCV entry."""
        # Check structure
        if not isinstance(entry, list) or len(entry) != 5:
            return False
        
        # Check for null/missing values
        if any(value is None for value in entry):
            return False
        
        try:
            timestamp, open_price, high, low, close = entry
            
            # Check that all values are numeric
            for value in entry:
                if not isinstance(value, (int, float)):
                    return False
            
            # Check for negative values (except timestamp)
            if open_price < 0 or high < 0 or low < 0 or close < 0:
                return False
            
            # Check logical price relationships
            if high < low:
                return False
            
            if open_price > high or open_price < low:
                return False
            
            if close > high or close < low:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def validate_cryptocurrency_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate cryptocurrency market data.
        
        Args:
            data: Dictionary containing cryptocurrency information
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['id', 'symbol', 'name']
        
        # Check required fields exist and are not empty
        for field in required_fields:
            if field not in data or not data[field] or not str(data[field]).strip():
                return False
        
        return True 