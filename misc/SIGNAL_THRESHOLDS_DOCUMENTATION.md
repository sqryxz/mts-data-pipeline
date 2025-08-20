# MTS Pipeline Signal Thresholds Documentation

## Overview

This document outlines all the thresholds that need to be met for signals to be generated and sent to Discord in the MTS (Multi-Tier Scheduler) pipeline. The pipeline uses multiple strategies with different thresholds, and signals must pass through several filtering layers before being sent as alerts.

## 🎯 Signal Generation Flow

```
Market Data → Strategy Analysis → Signal Generation → Aggregation → Discord Alerts
     ↓              ↓                    ↓              ↓              ↓
   Raw Data    Threshold Check    Signal Creation   Confidence    Final Alert
```

## 📊 Strategy-Specific Thresholds

### 1. VIX Correlation Strategy (`vix_correlation_strategy.py`)

**Configuration File**: `config/strategies/vix_correlation.json`

#### Correlation Thresholds
- **Strong Negative Correlation**: `-0.6` (LONG signals)
- **Strong Positive Correlation**: `0.6` (SHORT signals)
- **Lookback Period**: `30 days`
- **Position Size**: `2%` of portfolio

#### Signal Generation Logic
```python
# LONG Signal Conditions
if correlation <= -0.6:
    signal_type = SignalType.LONG
    confidence = min(abs(correlation) / abs(-0.6), 1.0)

# SHORT Signal Conditions  
if correlation >= 0.6:
    signal_type = SignalType.SHORT
    confidence = min(correlation / 0.6, 1.0)
```

#### Data Requirements
- **Minimum Data Points**: `10` for correlation calculation
- **VIX Data Availability**: Must have VIX data for correlation analysis
- **Asset Coverage**: bitcoin, ethereum, binancecoin

### 2. Mean Reversion Strategy (`mean_reversion_strategy.py`)

**Configuration File**: `config/strategies/mean_reversion.json`

#### Primary Thresholds
- **VIX Spike Threshold**: `25` (VIX must be > 25)
- **Drawdown Threshold**: `10%` (crypto must be down > 10% from high)
- **Lookback Period**: `14 days`
- **Position Size**: `2.5%` of portfolio

#### Signal Generation Logic
```python
# Signal Conditions (BOTH must be true)
if current_vix > 25 AND drawdown_from_high > 0.10:
    signal_type = SignalType.LONG  # Mean reversion opportunity
    confidence = calculated_based_on_multiple_factors
```

#### Confidence Calculation Factors
1. **VIX Spike Magnitude**: `(current_vix - 25) / 10` (normalized 0-1)
2. **Drawdown Magnitude**: `(drawdown - 0.10) / 0.10` (normalized 0-1)
3. **VIX Percentile**: `vix_percentile / 100` (0-1)
4. **RSI Oversold**: `max(0, (30 - rsi) / 30)` (RSI < 30 is oversold)

#### Data Requirements
- **Minimum Data Points**: `5` for analysis
- **VIX Data**: Must have VIX data available
- **Price Data**: Must have sufficient price history for drawdown calculation

## 🔧 Signal Aggregation Thresholds

### Signal Aggregator (`signal_aggregator.py`)

#### Confidence Thresholds
- **Minimum Confidence**: `0.1` (10% confidence to include signal)
- **Discord Min Confidence**: `0.6` (60% confidence for Discord alerts)
- **Discord Min Strength**: `WEAK` (minimum signal strength)

#### Position Size Limits
- **Maximum Position Size**: `10%` of portfolio
- **Minimum Position Size**: `0.5%` of portfolio
- **Default Position Size**: `2%` of portfolio

#### Conflict Resolution
- **Weighted Average**: Used when strategies disagree
- **Majority Agreement**: Optional (disabled by default)
- **Signal Timeout**: `24 hours` (signals expire after 24h)

## 📢 Discord Alert Thresholds

### Discord Configuration (`.env` file)

#### Alert Settings
- **Discord Alerts Enabled**: `true` (must be enabled)
- **Minimum Confidence**: `0.6` (60% confidence)
- **Minimum Strength**: `WEAK` (WEAK, MODERATE, or STRONG)
- **Rate Limit**: `60 seconds` between alerts
- **Enabled Assets**: `bitcoin`, `ethereum`
- **Enabled Signal Types**: `LONG`, `SHORT`

#### Alert Filtering
```python
# Discord Alert Conditions (ALL must be true)
if (signal.confidence >= 0.6 AND
    signal.signal_strength >= SignalStrength.WEAK AND
    signal.asset in ['bitcoin', 'ethereum'] AND
    signal.signal_type in ['LONG', 'SHORT']):
    send_discord_alert(signal)
```

## 🚨 Why No Signals Are Generated

Based on your logs, here are the likely reasons why no signals are being generated:

### 1. **VIX Correlation Strategy**
- **Issue**: Correlation values may not be reaching the ±0.6 threshold
- **Current Market**: VIX-crypto correlation might be in neutral range (-0.6 to +0.6)
- **Solution**: Lower thresholds or wait for more extreme correlation periods

### 2. **Mean Reversion Strategy**
- **Issue**: VIX may not be spiking above 25 OR crypto drawdowns may not be > 10%
- **Current Market**: VIX at normal levels or crypto not in significant drawdown
- **Solution**: Lower VIX threshold or drawdown threshold

### 3. **Data Availability Issues**
- **Issue**: `binancecoin` has no data available
- **Impact**: Reduces signal opportunities
- **Solution**: Ensure data collection is working for all assets

### 4. **Confidence Thresholds**
- **Issue**: Even if signals are generated, they may not meet 60% confidence for Discord
- **Solution**: Lower Discord confidence threshold or improve signal quality

## 🔧 How to Adjust Thresholds

### 1. Lower VIX Correlation Thresholds
Edit `config/strategies/vix_correlation.json`:
```json
{
  "correlation_thresholds": {
    "strong_negative": -0.4,  // Changed from -0.6
    "strong_positive": 0.4    // Changed from 0.6
  }
}
```

### 2. Lower Mean Reversion Thresholds
Edit `config/strategies/mean_reversion.json`:
```json
{
  "vix_spike_threshold": 20,     // Changed from 25
  "drawdown_threshold": 0.05,    // Changed from 0.10 (5% instead of 10%)
  "position_size": 0.025
}
```

### 3. Lower Discord Confidence Threshold
Edit `.env` file:
```env
DISCORD_MIN_CONFIDENCE=0.4  # Changed from 0.6 (40% instead of 60%)
```

### 4. Lower Signal Aggregator Threshold
Edit the signal aggregator configuration:
```python
'min_confidence_threshold': 0.05,  # Changed from 0.1 (5% instead of 10%)
```

## 📈 Current Market Conditions Check

To understand why no signals are being generated, check:

### 1. **VIX Level**
```bash
# Check current VIX level
python3 -c "import requests; print('VIX:', requests.get('https://api.coingecko.com/api/v3/simple/price?ids=volatility-index&vs_currencies=usd').json())"
```

### 2. **Crypto Drawdowns**
```bash
# Check current crypto prices vs recent highs
python3 -c "import requests; data = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true').json(); print('BTC:', data.get('bitcoin', {})); print('ETH:', data.get('ethereum', {}))"
```

### 3. **Database Data Availability**
```bash
# Check data in your SQLite database
python3 -c "import sqlite3; conn = sqlite3.connect('data/crypto_data.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM crypto_prices WHERE asset = \"bitcoin\"'); print('Bitcoin records:', cursor.fetchone()[0]); conn.close()"
```

## 🎯 Recommended Threshold Adjustments

For more frequent signals, consider these adjustments:

### Conservative (Fewer, Higher Quality Signals)
- VIX Correlation: ±0.5
- VIX Spike: 22
- Drawdown: 8%
- Discord Confidence: 0.5

### Moderate (Balanced Signal Frequency)
- VIX Correlation: ±0.4
- VIX Spike: 20
- Drawdown: 6%
- Discord Confidence: 0.4

### Aggressive (More Frequent Signals)
- VIX Correlation: ±0.3
- VIX Spike: 18
- Drawdown: 4%
- Discord Confidence: 0.3

## 📊 Monitoring Signal Generation

To monitor why signals aren't being generated, add debug logging:

```python
# In your strategy files, add debug logging
self.logger.debug(f"Current VIX: {current_vix}, Threshold: {self.vix_spike_threshold}")
self.logger.debug(f"Current correlation: {correlation}, Threshold: {self.correlation_thresholds}")
self.logger.debug(f"Current drawdown: {drawdown}, Threshold: {self.drawdown_threshold}")
```

## 🔍 Troubleshooting Steps

1. **Check Data Availability**: Ensure all assets have sufficient data
2. **Monitor Market Conditions**: Check if current market meets strategy criteria
3. **Adjust Thresholds**: Lower thresholds for more frequent signals
4. **Enable Debug Logging**: Add detailed logging to understand signal generation
5. **Test Individual Strategies**: Run strategies separately to isolate issues

## 📝 Summary

The MTS pipeline has multiple layers of thresholds that must be met for signals to be generated and sent to Discord:

1. **Strategy-Level Thresholds**: VIX correlation ±0.6, VIX spike >25, drawdown >10%
2. **Aggregation-Level Thresholds**: Minimum 10% confidence, position size limits
3. **Discord-Level Thresholds**: Minimum 60% confidence, WEAK+ strength

To generate more signals, consider lowering these thresholds based on your risk tolerance and market conditions. 