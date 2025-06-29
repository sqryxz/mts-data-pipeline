import csv
import os
from datetime import datetime
from typing import List, Set, Optional
from .models import OHLCVData


class CSVStorage:
    """CSV storage handler for OHLCV data."""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = data_dir
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_ohlcv_data(self, crypto_id: str, ohlcv_data: List[OHLCVData]) -> None:
        """
        Save OHLCV data to CSV file, preventing duplicates.
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            ohlcv_data: List of OHLCVData objects to save
        """
        if not ohlcv_data:
            return
        
        # Get current year for filename
        current_year = datetime.now().year
        filename = f"{crypto_id}_{current_year}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # Get existing timestamps to check for duplicates
        existing_timestamps = self._get_existing_timestamps(filepath)
        
        # Filter out duplicates
        new_data = [data for data in ohlcv_data if not self._record_exists(data.timestamp, existing_timestamps)]
        
        if not new_data:
            return  # No new data to save
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(filepath)
        
        # Open file in append mode
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Write new OHLCV data
            for data in new_data:
                writer.writerow([
                    data.timestamp,
                    data.open,
                    data.high,
                    data.low,
                    data.close,
                    data.volume
                ])
    
    def _record_exists(self, timestamp: int, existing_timestamps: Set[int]) -> bool:
        """Check if a record with the given timestamp already exists."""
        return timestamp in existing_timestamps
    
    def _get_existing_timestamps(self, filepath: str) -> Set[int]:
        """Get set of existing timestamps from CSV file."""
        existing_timestamps = set()
        
        if not os.path.exists(filepath):
            return existing_timestamps
        
        try:
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header
                next(reader, None)
                for row in reader:
                    if row:  # Skip empty rows
                        try:
                            timestamp = int(row[0])
                            existing_timestamps.add(timestamp)
                        except (ValueError, IndexError):
                            # Skip malformed rows
                            continue
        except (IOError, OSError):
            # File read error, return empty set
            pass
        
        return existing_timestamps
    
    def load_ohlcv_data(self, crypto_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[OHLCVData]:
        """
        Load OHLCV data from CSV file with optional date range filtering.
        
        Args:
            crypto_id: Cryptocurrency identifier (e.g., "bitcoin")
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            List of OHLCVData objects
        """
        # Get current year for filename
        current_year = datetime.now().year
        filename = f"{crypto_id}_{current_year}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # Handle missing file gracefully
        if not os.path.exists(filepath):
            return []
        
        ohlcv_data = []
        
        try:
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if not row:  # Skip empty rows
                        continue
                    
                    try:
                        # Parse CSV row
                        timestamp = int(row[0])
                        open_price = float(row[1])
                        high = float(row[2])
                        low = float(row[3])
                        close = float(row[4])
                        volume = float(row[5])
                        
                        # Create OHLCVData object
                        data = OHLCVData(
                            timestamp=timestamp,
                            open=open_price,
                            high=high,
                            low=low,
                            close=close,
                            volume=volume
                        )
                        
                        # Apply date range filtering if specified
                        if self._is_in_date_range(data, start_date, end_date):
                            ohlcv_data.append(data)
                            
                    except (ValueError, IndexError):
                        # Skip malformed rows
                        continue
                        
        except (IOError, OSError):
            # File read error, return empty list
            return []
        
        return ohlcv_data
    
    def _is_in_date_range(self, data: OHLCVData, start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
        """Check if OHLCV data falls within the specified date range."""
        if start_date is None and end_date is None:
            return True
        
        data_datetime = data.to_datetime()
        
        if start_date and data_datetime < start_date:
            return False
        
        if end_date and data_datetime > end_date:
            return False
        
        return True 