# Correlation Analysis Alert Reduction Summary

## Problem
Correlation analysis alerts were sending too frequently, including minor fluctuations that created noise in Discord notifications.

## Changes Made

### 1. Alert Thresholds (`config/correlation_analysis/alert_thresholds.json`)
**Made thresholds much more restrictive for major fluctuations only**

- **z_score_threshold**: `3.5` → `4.5` (much higher statistical significance required)
- **significance_level**: `0.001` → `0.0001` (10x more stringent p-value requirement)
- **min_duration_minutes**: `30` → `60` (must persist for 1 hour)
- **confirmation_windows**: `3` → `5` (requires 5 consecutive confirmations)

### 2. Discord Configuration (`config/correlation_analysis/discord_config.json`)
**Increased filtering and reduced alert types**

- **min_correlation_change**: `0.1` → `0.3` (30% correlation change required)
- **min_significance**: `0.05` → `0.001` (much more stringent significance)
- **send_mosaic_alerts**: `true` → `false` (disabled daily mosaic alerts)
- **send_daily_summaries**: `true` → `false` (disabled daily summaries)
- **max_alerts_per_hour**: `10` → `2` (dramatically reduced)
- **max_alerts_per_day**: `50` → `10` (dramatically reduced)
- **cooldown_minutes**: `5` → `30` (5x longer cooldown)

### 3. Correlation Engine Defaults (`src/correlation_analysis/core/correlation_engine.py`)
**Updated default z-score threshold**

- **z_score_threshold**: `3.5` → `4.5` (higher default threshold)

### 4. Discord Integration Impact Levels (`src/correlation_analysis/alerts/discord_integration.py`)
**Made impact assessment more restrictive**

- **Color thresholds**: Now requires 0.5+ change for red (major), 0.3+ for orange (significant)
- **Impact descriptions**: Added "Critical Impact" for 0.7+ changes, removed "Minimal Impact"

## Result

### Before Changes
- **z-score threshold**: 3.5 (moderate statistical significance)
- **p-value requirement**: 0.001 (1 in 1000 chance)
- **Correlation change**: 10% change triggered alerts
- **Duration**: 30 minutes persistence
- **Confirmations**: 3 consecutive confirmations
- **Rate limiting**: 10 alerts/hour, 50/day
- **Alert types**: All types enabled (breakdowns, mosaics, summaries)

### After Changes
- **z-score threshold**: 4.5 (very high statistical significance)
- **p-value requirement**: 0.0001 (1 in 10,000 chance)
- **Correlation change**: 30% change required
- **Duration**: 60 minutes persistence
- **Confirmations**: 5 consecutive confirmations
- **Rate limiting**: 2 alerts/hour, 10/day
- **Alert types**: Only breakdown alerts enabled

## Expected Impact

1. **Dramatically Reduced Alerts**: Only extreme correlation breakdowns will trigger alerts
2. **Higher Quality**: Only statistically very significant changes (p < 0.0001)
3. **Major Fluctuations Only**: Requires 30%+ correlation change
4. **Persistent Changes**: Must persist for 1 hour with 5 confirmations
5. **No Daily Spam**: Disabled mosaic and summary alerts
6. **Strict Rate Limiting**: Maximum 2 alerts per hour, 10 per day

## Statistical Significance

The new thresholds mean:
- **z-score ≥ 4.5**: Extremely rare statistical event (99.99%+ confidence)
- **p-value < 0.0001**: 1 in 10,000 chance of false positive
- **30% correlation change**: Major market regime shift
- **5 confirmations**: Ensures the change is persistent, not noise

## Configuration

These changes are applied automatically when the correlation analysis system restarts. No additional configuration needed.

## Monitoring

You can monitor the reduced alert frequency by:
- Checking Discord for significantly fewer correlation alerts
- Reviewing logs for correlation breakdown detection
- Monitoring the alert generation metrics

## Further Adjustments

If you need to adjust the strictness:

- **More restrictive**: Increase z-score to 5.0, decrease p-value to 0.00001
- **Less restrictive**: Decrease z-score to 4.0, increase p-value to 0.001
- **Change correlation threshold**: Modify min_correlation_change in discord_config.json
- **Adjust rate limits**: Modify max_alerts_per_hour/day in discord_config.json
