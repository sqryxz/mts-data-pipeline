import csv
import os
from datetime import datetime
from typing import List, Set, Optional
from .models import OHLCVData
from .macro_models import MacroIndicatorRecord


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
    
    def save_macro_indicator_data(self, indicator_key: str, records: List[MacroIndicatorRecord]) -> None:
        """
        Save macro indicator data to CSV file, preventing duplicates.
        
        Args:
            indicator_key: Macro indicator key (e.g., "VIX")
            records: List of MacroIndicatorRecord objects to save
        """
        if not records:
            return
        
        # Create macro directory if it doesn't exist
        macro_dir = os.path.join(self.data_dir, "macro")
        os.makedirs(macro_dir, exist_ok=True)
        
        # Get current year for filename
        current_year = datetime.now().year
        filename = f"{records[0].series_id.lower()}_{current_year}.csv"
        filepath = os.path.join(macro_dir, filename)
        
        # Get existing dates to check for duplicates
        existing_dates = self._get_existing_macro_dates(filepath)
        
        # Filter out duplicates based on date
        new_records = [record for record in records if record.date.strftime('%Y-%m-%d') not in existing_dates]
        
        if not new_records:
            return  # No new data to save
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(filepath)
        
        # Open file in append mode
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header if file is new
            if not file_exists:
                writer.writerow(['date', 'value', 'series_id', 'indicator_name', 'units', 'is_interpolated', 'is_forward_filled', 'source'])
            
            # Write new macro data
            for record in new_records:
                writer.writerow([
                    record.date.strftime('%Y-%m-%d'),
                    record.value,
                    record.series_id,
                    record.indicator_name,
                    record.units,
                    record.is_interpolated,
                    record.is_forward_filled,
                    record.source
                ])
    
    def _get_existing_macro_dates(self, filepath: str) -> Set[str]:
        """Get set of existing dates from macro CSV file."""
        existing_dates = set()
        
        if not os.path.exists(filepath):
            return existing_dates
        
        try:
            with open(filepath, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                # Skip header
                next(reader, None)
                for row in reader:
                    if row:  # Skip empty rows
                        try:
                            date_str = row[0]
                            existing_dates.add(date_str)
                        except IndexError:
                            # Skip malformed rows
                            continue
        except (IOError, OSError):
            # File read error, return empty set
            pass
        
        return existing_dates
    
    def load_macro_indicator_data(self, indicator_key: str, series_id: str, year: int = None) -> List[MacroIndicatorRecord]:
        """
        Load macro indicator data from CSV file.
        
        Args:
            indicator_key: Macro indicator key (e.g., "VIX")
            series_id: FRED series ID (e.g., "VIXCLS")
            year: Year to load data for (defaults to current year)
            
        Returns:
            List of MacroIndicatorRecord objects
        """
        # Use current year if not specified
        if year is None:
            year = datetime.now().year
        
        # Create file path
        macro_dir = os.path.join(self.data_dir, "macro")
        filename = f"{series_id.lower()}_{year}.csv"
        filepath = os.path.join(macro_dir, filename)
        
        # Handle missing file gracefully
        if not os.path.exists(filepath):
            return []
        
        records = []
        
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
                        date_str = row[0]
                        value = float(row[1]) if row[1] else None
                        series_id_csv = row[2]
                        indicator_name = row[3]
                        units = row[4]
                        is_interpolated = row[5].lower() == 'true'
                        is_forward_filled = row[6].lower() == 'true'
                        source = row[7]
                        
                        # Parse date
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Create MacroIndicatorRecord object
                        record = MacroIndicatorRecord(
                            date=date,
                            value=value,
                            series_id=series_id_csv,
                            indicator_name=indicator_name,
                            units=units,
                            is_interpolated=is_interpolated,
                            is_forward_filled=is_forward_filled,
                            source=source
                        )
                        
                        records.append(record)
                        
                    except (ValueError, IndexError) as e:
                        # Skip malformed rows
                        continue
                        
        except (IOError, OSError):
            # File read error, return empty list
            return []
        
        return records 