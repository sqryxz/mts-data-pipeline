from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class MacroIndicatorRecord:
    """Data model for macro economic indicators"""
    date: datetime
    value: Optional[float]
    series_id: str
    indicator_name: str
    units: str
    is_interpolated: bool = False
    is_forward_filled: bool = False
    source: str = 'FRED'
    
    def to_dict(self) -> Dict:
        """Convert record to dictionary format"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'value': self.value,
            'series_id': self.series_id,
            'indicator_name': self.indicator_name,
            'units': self.units,
            'is_interpolated': self.is_interpolated,
            'is_forward_filled': self.is_forward_filled,
            'source': self.source
        } 