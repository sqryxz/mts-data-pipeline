# MTS Cryptocurrency Data Pipeline

A quantitative trading infrastructure that collects multi-source market data, generates trading signals, runs backtests, and executes paper trades.

## What It Does

| Component | Description |
|-----------|-------------|
| **Data Collection** | Fetches OHLCV from Binance, macro data from FRED, order books, funding rates |
| **Signal Generation** | Multiple strategies: VIX correlation, mean reversion, momentum, volatility, etc. |
| **Backtesting** | Event-driven backtesting engine with portfolio simulation |
| **Paper Trading** | Simulated trade execution from signals with P&L tracking |
| **Alerts** | Discord webhooks for signal notifications |

## Quick Start

```bash
# Clone
git clone https://github.com/sqryxz/mts-data-pipeline.git
cd mts-data-pipeline

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Environment (see API Keys below)
cp .env.example .env
```

## Running the Pipeline

```bash
# Data collection only
python3 main_optimized.py --background

# With signal generation + Discord alerts
python3 main_enhanced.py --background

# Collect specific date range
python3 scripts/update_historical_data_and_analytics.py --start-date 2025-01-01 --end-date 2025-12-31
```

## API Keys Required

| Service | Variable | Status |
|---------|----------|--------|
| **FRED** | `FRED_API_KEY` | Required |
| **Binance** | (none) | Free tier |
| **CoinGecko** | `COINGECKO_API_KEY` | ⚠️ Requires paid plan |
| **Discord** | `DISCORD_WEBHOOK_URL` | Optional (alerts) |

Get keys:
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html
- CoinGecko: https://www.coingecko.com/en/api
- Discord: Server Settings → Integrations → Webhooks

## Data

**Database:** `data/crypto_data.db` (SQLite)

Tables:
- `crypto_ohlcv` — Daily OHLCV for ~25 cryptocurrencies
- `crypto_volatility` — Rolling volatility calculations
- `macro_indicators` — VIX, Treasury yields (DGS1-DGS30), Dollar Index, SOFR, FX rates, etc.
- `funding_rates` — Exchange funding rates
- `correlation_history` — Asset correlation data

## Project Structure

```
├── main.py                  # CLI entry point
├── main_optimized.py        # Multi-tier scheduler (86% API reduction)
├── main_enhanced.py          # Signal generation + Discord alerts
├── scripts/                 # One-off scripts
│   ├── update_historical_data_and_analytics.py
│   ├── start_complete_system.py
│   └── ...
├── src/
│   ├── api/                 # Exchange API clients
│   ├── data/                # Storage, models, validators
│   ├── services/            # Collectors, schedulers
│   ├── signals/             # Trading strategies
│   └── analytics/            # Macro analytics
├── paper_trading_engine/    # Paper trading system
├── backtesting-engine/      # Backtesting system
└── config/                  # JSON configs
```

## Troubleshooting

**CoinGecko 401 errors:** API key is invalid or expired. Use Binance instead (free).

**Missing data:** Run backfill:
```bash
python3 scripts/update_historical_data_and_analytics.py --start-date 2025-09-01
```

**Check data freshness:**
```bash
sqlite3 data/crypto_data.db "SELECT cryptocurrency, MAX(timestamp) FROM crypto_ohlcv GROUP BY cryptocurrency;"
```

## Transferring to New Server

```bash
# 1. Clone repo
git clone <repo-url>

# 2. Copy database
scp user@old-server:/path/to/data/crypto_data.db ./data/

# 3. Copy .env (update API keys)
scp user@old-server:/path/to/.env ./

# 4. Install deps & run
pip install -r requirements.txt
python3 main_optimized.py --background
```

## License

MIT
