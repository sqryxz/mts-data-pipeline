"""
Daily Report Generator for Macro Indicators and Bond Yields

Generates a daily report with:
- Macro indicators with daily values and 7/14/30-day % change
- Bond yields yield curve with 7/14/30-day % change

Output: JSON file at data/daily_reports/{date}.json
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from pathlib import Path

from ..data.sqlite_helper import CryptoDatabase
from config.macro_settings import MACRO_INDICATORS

logger = logging.getLogger(__name__)


# Macro indicators to include in report (excluding bond yields which are handled separately)
MACRO_INDICATOR_LIST = [
    'VIXCLS',   # VIX
    'DFF',      # Fed Funds Rate
    'DTWEXBGS', # Dollar Index
    'DEXUSEU',  # USD/EUR
    'DEXCHUS',  # USD/CNY
    'BAMLH0A0HYM2',  # High Yield Spread
    'RRPONTSYD',      # Reverse Repo
    'SOFR',           # Secured Overnight Financing Rate
]

# Bond yield series (DGS = Treasury Constant Maturity Rates)
BOND_YIELD_SERIES = [
    'DGS1',   # 1-Year
    'DGS2',   # 2-Year
    'DGS5',   # 5-Year
    'DGS10',  # 10-Year
    'DGS20',  # 20-Year
    'DGS30',  # 30-Year
]

# Mapping to friendly names
INDICATOR_NAMES = {
    'VIXCLS': 'CBOE Volatility Index',
    'DFF': 'Federal Funds Effective Rate',
    'DTWEXBGS': 'US Dollar Index',
    'DEXUSEU': 'USD/EUR Exchange Rate',
    'DEXCHUS': 'USD/CNY Exchange Rate',
    'BAMLH0A0HYM2': 'High Yield Credit Spread',
    'RRPONTSYD': 'Overnight Reverse Repo',
    'SOFR': 'Secured Overnight Financing Rate',
    'DGS1': '1-Year Treasury Yield',
    'DGS2': '2-Year Treasury Yield',
    'DGS5': '5-Year Treasury Yield',
    'DGS10': '10-Year Treasury Yield',
    'DGS20': '20-Year Treasury Yield',
    'DGS30': '30-Year Treasury Yield',
}


class DailyReportGenerator:
    """Generates daily macro and bond yield reports."""
    
    def __init__(self, db_path: str = 'data/crypto_data.db'):
        """Initialize the report generator."""
        self.db = CryptoDatabase(db_path)
        self.reports_dir = Path('data/daily_reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def get_latest_value(self, indicator: str) -> Optional[Dict]:
        """Get the latest value for a macro indicator."""
        try:
            query = """
                SELECT date, value 
                FROM macro_indicators 
                WHERE indicator = ? AND value IS NOT NULL
                ORDER BY date DESC 
                LIMIT 1
            """
            df = self.db.query_to_dataframe(query, (indicator,))
            if df.empty:
                return None
            return {
                'date': df.iloc[0]['date'],
                'value': float(df.iloc[0]['value'])
            }
        except Exception as e:
            logger.error(f"Error getting latest value for {indicator}: {e}")
            return None
    
    def get_value_at_date(self, indicator: str, target_date: str) -> Optional[float]:
        """Get the value for a macro indicator at a specific date."""
        try:
            query = """
                SELECT value 
                FROM macro_indicators 
                WHERE indicator = ? AND date = ? AND value IS NOT NULL
                LIMIT 1
            """
            df = self.db.query_to_dataframe(query, (indicator, target_date))
            if df.empty:
                return None
            return float(df.iloc[0]['value'])
        except Exception as e:
            logger.error(f"Error getting value for {indicator} at {target_date}: {e}")
            return None
    
    def get_value_on_or_before(self, indicator: str, target_date: str) -> Optional[float]:
        """Get the value for a macro indicator on or before a specific date."""
        try:
            query = """
                SELECT value 
                FROM macro_indicators 
                WHERE indicator = ? AND date <= ? AND value IS NOT NULL
                ORDER BY date DESC 
                LIMIT 1
            """
            df = self.db.query_to_dataframe(query, (indicator, target_date))
            if df.empty:
                return None
            return float(df.iloc[0]['value'])
        except Exception as e:
            logger.error(f"Error getting value for {indicator} on or before {target_date}: {e}")
            return None
    
    def calculate_percentage_change(self, current_value: float, past_value: float) -> Optional[float]:
        """Calculate percentage change between two values."""
        if past_value is None or past_value == 0:
            return None
        return ((current_value - past_value) / past_value) * 100
    
    def get_indicator_report(self, indicator: str) -> Optional[Dict]:
        """Generate report for a single macro indicator with all timeframes."""
        # Get latest value
        latest = self.get_latest_value(indicator)
        if not latest:
            return None
        
        current_value = latest['value']
        current_date = latest['date']
        
        # Calculate past dates
        date_7d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        date_14d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=14)).strftime('%Y-%m-%d')
        date_30d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get values at each timeframe
        value_7d = self.get_value_on_or_before(indicator, date_7d)
        value_14d = self.get_value_on_or_before(indicator, date_14d)
        value_30d = self.get_value_on_or_before(indicator, date_30d)
        
        # Calculate percentage changes
        change_7d = self.calculate_percentage_change(current_value, value_7d)
        change_14d = self.calculate_percentage_change(current_value, value_14d)
        change_30d = self.calculate_percentage_change(current_value, value_30d)
        
        return {
            'indicator': indicator,
            'name': INDICATOR_NAMES.get(indicator, indicator),
            'value': round(current_value, 4),
            'date': current_date,
            'change_7d_pct': round(change_7d, 2) if change_7d is not None else None,
            'change_14d_pct': round(change_14d, 2) if change_14d is not None else None,
            'change_30d_pct': round(change_30d, 2) if change_30d is not None else None,
        }
    
    def generate_macro_report(self) -> List[Dict]:
        """Generate report for all macro indicators."""
        report = []
        for indicator in MACRO_INDICATOR_LIST:
            indicator_report = self.get_indicator_report(indicator)
            if indicator_report:
                report.append(indicator_report)
        return report
    
    def generate_bond_yields_report(self) -> List[Dict]:
        """Generate report for bond yields (yield curve)."""
        report = []
        
        # Get latest date across all bond yields
        latest_date = None
        for series in BOND_YIELD_SERIES:
            latest = self.get_latest_value(series)
            if latest:
                if latest_date is None or latest['date'] > latest_date:
                    latest_date = latest['date']
        
        if not latest_date:
            return report
        
        current_value = None
        
        for series in BOND_YIELD_SERIES:
            # Get current value
            latest = self.get_latest_value(series)
            if not latest:
                continue
            
            if current_value is None:
                current_value = latest['value']
                current_date = latest['date']
            
            # Calculate past dates
            date_7d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
            date_14d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=14)).strftime('%Y-%m-%d')
            date_30d = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')
            
            value_7d = self.get_value_on_or_before(series, date_7d)
            value_14d = self.get_value_on_or_before(series, date_14d)
            value_30d = self.get_value_on_or_before(series, date_30d)
            
            change_7d = self.calculate_percentage_change(latest['value'], value_7d)
            change_14d = self.calculate_percentage_change(latest['value'], value_14d)
            change_30d = self.calculate_percentage_change(latest['value'], value_30d)
            
            # Maturity mapping
            maturity_map = {
                'DGS1': '1Y',
                'DGS2': '2Y',
                'DGS5': '5Y',
                'DGS10': '10Y',
                'DGS20': '20Y',
                'DGS30': '30Y',
            }
            
            report.append({
                'maturity': maturity_map.get(series, series),
                'indicator': series,
                'yield': round(latest['value'], 4),
                'date': latest['date'],
                'change_7d_pct': round(change_7d, 2) if change_7d is not None else None,
                'change_14d_pct': round(change_14d, 2) if change_14d is not None else None,
                'change_30d_pct': round(change_30d, 2) if change_30d is not None else None,
            })
        
        return report
    
    def generate_report(self) -> Dict:
        """Generate the complete daily report."""
        # Get current time in HKT (UTC+8)
        now_utc = datetime.now(timezone.utc)
        # HKT is UTC+8
        hkt_offset = timezone(timedelta(hours=8))
        now_hkt = now_utc.astimezone(hkt_offset)
        
        report = {
            'generated_at': now_hkt.isoformat(),
            'generated_utc': now_utc.isoformat(),
            'report_date': now_hkt.strftime('%Y-%m-%d'),
            'macro_indicators': self.generate_macro_report(),
            'bond_yields': self.generate_bond_yields_report(),
        }
        
        return report
    
    def save_report(self, report: Dict) -> Path:
        """Save report to JSON file."""
        report_date = report['report_date']
        filename = f"{report_date}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {filepath}")
        return filepath
    
    def generate_and_save(self) -> Path:
        """Generate and save the daily report."""
        report = self.generate_report()
        return self.save_report(report)


def generate_daily_report(db_path: str = 'data/crypto_data.db') -> Path:
    """Convenience function to generate and save daily report."""
    generator = DailyReportGenerator(db_path)
    return generator.generate_and_save()


if __name__ == '__main__':
    # Test the report generator
    generator = DailyReportGenerator()
    report = generator.generate_report()
    print(json.dumps(report, indent=2))
