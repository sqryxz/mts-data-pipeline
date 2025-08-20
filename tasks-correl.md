# Correlation Analysis MVP Build Plan

## Phase 1: Foundation Setup

### Task 1: Create Directory Structure
**Start**: Empty project  
**End**: All required directories exist  
**Test**: Verify all directories in `src/correlation_analysis/` exist with `__init__.py` files

### Task 2: Create Base Configuration Files
**Start**: Empty config directory  
**End**: Basic JSON config files with minimal structure  
**Test**: Load and parse all 3 config files without errors

```json
// config/correlation_analysis/monitored_pairs.json
{
  "crypto_pairs": {
    "BTC_ETH": {
      "primary": "bitcoin",
      "secondary": "ethereum",
      "correlation_windows": [7, 14, 30]
    }
  }
}
```

### Task 3: Create Data Storage Directories
**Start**: No data/correlation directory  
**End**: All data storage directories exist  
**Test**: Verify `data/correlation/{state,alerts,mosaics,cache}` directories exist

## Phase 2: Core Data Layer

### Task 4: Build Basic Data Fetcher
**Start**: Empty `data_fetcher.py`  
**End**: Function to fetch crypto prices from existing MTS database  
**Test**: Successfully retrieve BTC and ETH prices for last 30 days

```python
def get_crypto_prices(symbols: List[str], days: int) -> pd.DataFrame:
    # Connect to existing MTS SQLite database
    # Return OHLCV data for symbols
```

### Task 5: Build Data Validator
**Start**: Empty `data_validator.py`  
**End**: Function to validate price data completeness  
**Test**: Detect missing data points and return validation status

```python
def validate_price_data(df: pd.DataFrame) -> Dict[str, bool]:
    # Check for missing values, outliers, timestamp gaps
    # Return validation results
```

### Task 6: Build Data Normalizer
**Start**: Empty `data_normalizer.py`  
**End**: Function to align timestamps and normalize prices  
**Test**: Input misaligned data, output synchronized DataFrame

```python
def normalize_and_align(crypto_data: pd.DataFrame) -> pd.DataFrame:
    # Align timestamps, handle missing values
    # Return clean, aligned data
```

## Phase 3: Core Correlation Engine

### Task 7: Build Basic Correlation Calculator
**Start**: Empty `correlation_calculator.py`  
**End**: Function to calculate Pearson correlation for single window  
**Test**: Calculate correlation between BTC/ETH for 30-day window

```python
def calculate_correlation(data: pd.DataFrame, window_days: int) -> float:
    # Calculate rolling correlation
    # Return single correlation value
```

### Task 8: Build Rolling Correlation Calculator
**Start**: Single correlation function  
**End**: Function to calculate rolling correlations for multiple windows  
**Test**: Return correlation time series for [7, 14, 30] day windows

```python
def calculate_rolling_correlations(data: pd.DataFrame, windows: List[int]) -> Dict:
    # Calculate rolling correlations for each window
    # Return dict with window -> correlation series
```

### Task 9: Build Statistical Analyzer
**Start**: Empty `statistical_analyzer.py`  
**End**: Function to calculate z-scores for correlation changes  
**Test**: Calculate z-score when correlation changes significantly

```python
def calculate_correlation_zscore(current: float, historical: List[float]) -> float:
    # Calculate z-score for correlation change
    # Return z-score value
```

## Phase 4: Alert System

### Task 10: Build Alert Templates
**Start**: Empty `alert_templates.py`  
**End**: JSON template for correlation breakdown alert  
**Test**: Generate valid JSON alert with test data

```python
def create_breakdown_alert_template(pair: str, correlation_data: Dict) -> Dict:
    # Create JSON alert structure
    # Return formatted alert dict
```

### Task 11: Build Basic Alert System
**Start**: Empty `correlation_alert_system.py`  
**End**: Function to generate and save correlation breakdown alert  
**Test**: Generate alert file in `data/correlation/alerts/`

```python
def generate_breakdown_alert(pair: str, correlation_data: Dict) -> str:
    # Generate alert using template
    # Save to file, return filepath
```

### Task 12: Build Breakout Detector
**Start**: Empty `breakout_detector.py`  
**End**: Function to detect 2-sigma correlation breakouts  
**Test**: Detect breakout when z-score > 2.0

```python
def detect_correlation_breakout(z_score: float, threshold: float = 2.0) -> bool:
    # Check if z-score exceeds threshold
    # Return breakout status
```

## Phase 5: State Management

### Task 13: Build State Manager
**Start**: Empty `state_manager.py`  
**End**: Functions to save/load correlation state to JSON  
**Test**: Save state, restart, load state successfully

```python
def save_correlation_state(state: Dict) -> None:
    # Save state to data/correlation/state/correlation_state.json

def load_correlation_state() -> Dict:
    # Load state from JSON file
```

### Task 14: Build Basic Storage
**Start**: Empty `correlation_storage.py`  
**End**: Function to store correlation history in SQLite  
**Test**: Store correlation data, query it back

```python
def store_correlation_history(pair: str, timestamp: int, correlation: float) -> None:
    # Store in SQLite database
```

## Phase 6: Core Engine Integration

### Task 15: Build Correlation Monitor
**Start**: Empty `correlation_monitor.py`  
**End**: Class to monitor single pair for correlation changes  
**Test**: Monitor BTC/ETH, detect and alert on breakout

```python
class CorrelationMonitor:
    def monitor_pair(self, pair: str) -> None:
        # Fetch data, calculate correlation, check for breakouts
        # Generate alerts if needed
```

### Task 16: Build Main Correlation Engine
**Start**: Empty `correlation_engine.py`  
**End**: Engine that orchestrates monitoring for all configured pairs  
**Test**: Run engine, verify it monitors all pairs from config

```python
class CorrelationEngine:
    def start_monitoring(self) -> None:
        # Load config, start monitoring all pairs
        # Coordinate all components
```

## Phase 7: Basic Mosaic Generation

### Task 17: Build Simple Mosaic Generator
**Start**: Empty `mosaic_generator.py`  
**End**: Function to generate correlation matrix as JSON  
**Test**: Generate daily correlation matrix for all pairs

```python
def generate_correlation_matrix() -> Dict:
    # Calculate correlations for all pairs
    # Return correlation matrix as dict
```

### Task 18: Build Mosaic Alert
**Start**: Basic mosaic generator  
**End**: Generate daily mosaic alert with summary  
**Test**: Create mosaic alert file with key findings

## Phase 8: Integration & Testing

### Task 19: Build Simple CLI Interface
**Start**: No CLI  
**End**: Basic CLI to run correlation analysis manually  
**Test**: Run `python -m correlation_analysis --run-once`

```python
def main():
    engine = CorrelationEngine()
    engine.run_analysis()
```

### Task 20: Build Integration Test
**Start**: Individual component tests  
**End**: End-to-end test that runs full pipeline  
**Test**: Run pipeline, verify alerts generated for test data

```python
def test_full_pipeline():
    # Load test data with known correlation breakout
    # Run engine, verify correct alert generated
```

## MVP Completion Criteria

**Working System That:**
1. Monitors BTC/ETH correlation in real-time
2. Detects 2-sigma correlation breakouts
3. Generates JSON alerts to `data/correlation/alerts/`
4. Produces daily correlation mosaic
5. Persists state across restarts
6. Integrates with existing MTS data pipeline

**Test Coverage:**
- Each component has unit tests
- End-to-end integration test passes
- Manual CLI execution works
- Alert generation verified with test data