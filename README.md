# Event-Driven Backtesting Engine

A modular, event-driven backtesting engine for quantitative trading strategies, integrated with the MTS data pipeline.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run a Backtest from the Command Line

```bash
python main.py --symbols bitcoin --start 2023-01-01 --end 2023-01-30 --strategy BuyHoldStrategy --capital 100000
```

- Use `--symbols` for one or more assets (e.g. bitcoin ethereum)
- Use `--start` and `--end` for the date range (YYYY-MM-DD)
- Use `--strategy` for the strategy name (must be available)
- Use `--capital` to set initial capital (default: 100000)
- Add `--verbose` to print trade details

### 3. Run a Backtest from Python

See [`examples/simple_backtest.py`](examples/simple_backtest.py):

```python
from datetime import datetime, timedelta
from backtesting_engine.src.core.backtest_engine import BacktestEngine
from backtesting_engine.config.backtest_settings import BacktestConfig

start_date = datetime(2023, 1, 1)
end_date = start_date + timedelta(days=29)
config = BacktestConfig(
    start_date=start_date,
    end_date=end_date,
    initial_capital=100000.0,
    strategies=["BuyHoldStrategy"],
    symbols=["bitcoin"]
)
engine = BacktestEngine(config)
result = engine.run_backtest()
print(result)
```

### 4. Run Tests

```bash
pytest
```

- Unit tests: `backtesting-engine/tests/unit/`
- Integration tests: `backtesting-engine/tests/integration/`

## 📂 Project Structure

- `main.py` — Command-line entry point
- `examples/` — Example scripts
- `backtesting-engine/` — Core engine code
- `tests/` — Unit and integration tests
- `requirements.txt` — Python dependencies

## 📝 Documentation

- All public methods and classes have docstrings.
- See `examples/` for usage patterns.
- For advanced configuration, see `backtesting_engine/config/backtest_settings.py`.

## 🛠️ Troubleshooting

- If you see errors about missing strategies or symbols, use the CLI with no arguments or check available strategies/symbols in your data.
- For database errors, ensure your SQLite database is accessible and up to date.

## 📣 Contributing

Pull requests and issues are welcome! 

## 🔑 Environment Variables & API Keys

This project uses a `.env` file for sensitive configuration, including API keys. You must create a `.env` file in the project root with the following variables:

```
COINGECKO_API_KEY=your_actual_coingecko_api_key
FRED_API_KEY=your_actual_fred_api_key
```

- **Never hardcode API keys in scripts.**
- All scripts and services will load these automatically.

## 🛠️ Data Fetching Scripts

- `scripts/fetch_and_import_2024_data.py` — Fetches and imports all crypto, macro, and order book data for a given year.
- `scripts/fetch_macro_only.py` — Fetches and imports macroeconomic data for all configured indicators for a given year (default: 2024). Does not touch crypto or order book data.

  Example usage:
  ```bash
  python3 scripts/fetch_macro_only.py --year 2024
  ``` 