import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.fred_client import FREDClient
from data.sqlite_helper import CryptoDatabase

# --- CONFIG ---
with open(os.path.join(os.path.dirname(__file__), '../config/monitored_macro_indicators.json')) as f:
    MACRO_CONFIG = json.load(f)["macro_indicators"]
MACRO_INDICATORS = [m["fred_series_id"] for m in MACRO_CONFIG]
DB_PATH = 'data/crypto_data.db'

import argparse
parser = argparse.ArgumentParser(description='Fetch macro data for all indicators for a given year.')
parser.add_argument('--year', type=int, default=2024, help='Year to fetch macro data for (default: 2024)')
args = parser.parse_args()
YEAR = args.year

if __name__ == "__main__":
    print(f"Fetching macro indicators from FRED for {YEAR}...")
    db = CryptoDatabase(DB_PATH)
    fred = FREDClient()
    for indicator in MACRO_INDICATORS:
        try:
            macro_data = fred.get_series_data(indicator, f"{YEAR}-01-01", f"{YEAR}-12-31")
            for record in macro_data:
                record['indicator'] = indicator
            inserted = db.insert_macro_data(macro_data)
            print(f"Inserted {inserted} macro records for {indicator}")
        except Exception as e:
            print(f"Failed to fetch/insert macro for {indicator}: {e}")
    print(f"Macro data fetch for {YEAR} complete.") 