# Alert Frequency Reduction Summary

## Problem
The aggregated strategy alerts were sending every 5 minutes, creating too much noise in Discord notifications.

## Changes Made

### 1. Signal Generation Interval
**Changed from 5 minutes to 1 hour**

- **File**: `src/services/enhanced_multi_tier_scheduler.py`
- **File**: `main_enhanced.py` 
- **File**: `scripts/main_enhanced.py`
- **Change**: `signal_generation_interval=300` → `signal_generation_interval=3600`

### 2. Discord Alert Filtering
**Increased filtering thresholds to reduce noise**

- **File**: `.env.example`
- **Changes**:
  - `DISCORD_MIN_CONFIDENCE=0.6` → `DISCORD_MIN_CONFIDENCE=0.8` (80% confidence required)
  - `DISCORD_MIN_STRENGTH=WEAK` → `DISCORD_MIN_STRENGTH=MODERATE` (moderate strength required)
  - `DISCORD_RATE_LIMIT_SECONDS=60` → `DISCORD_RATE_LIMIT_SECONDS=300` (5 minutes between alerts per asset)

## Result

### Before Changes
- **Signal Generation**: Every 5 minutes
- **Alert Frequency**: Very high (potentially 12+ alerts per hour)
- **Confidence Threshold**: 60%
- **Strength Threshold**: WEAK
- **Rate Limit**: 1 minute per asset

### After Changes
- **Signal Generation**: Every 1 hour
- **Alert Frequency**: Significantly reduced (max 1 alert per hour)
- **Confidence Threshold**: 80% (higher quality signals only)
- **Strength Threshold**: MODERATE (stronger signals only)
- **Rate Limit**: 5 minutes per asset (prevents spam)

## Expected Impact

1. **Reduced Noise**: Alerts will only be sent for high-confidence, moderate-strength signals
2. **Better Quality**: Only the most significant trading opportunities will trigger alerts
3. **Less Spam**: Rate limiting prevents multiple alerts for the same asset in short time periods
4. **Hourly Cadence**: Signal generation now happens once per hour instead of every 5 minutes

## Configuration

To apply these changes to your environment:

1. Copy the updated values from `.env.example` to your `.env` file:
   ```bash
   DISCORD_MIN_CONFIDENCE=0.8
   DISCORD_MIN_STRENGTH=MODERATE
   DISCORD_RATE_LIMIT_SECONDS=300
   ```

2. Restart the enhanced pipeline:
   ```bash
   python3 main_enhanced.py --background
   ```

## Monitoring

You can monitor the alert frequency by:
- Checking Discord for reduced alert volume
- Reviewing logs for signal generation frequency
- Monitoring the `signals_generated` and `discord_alerts_sent` metrics in the scheduler status

## Further Adjustments

If you need to adjust the frequency further:

- **More restrictive**: Increase `DISCORD_MIN_CONFIDENCE` to 0.9 or change `DISCORD_MIN_STRENGTH` to STRONG
- **Less restrictive**: Decrease `DISCORD_MIN_CONFIDENCE` to 0.7 or change `DISCORD_MIN_STRENGTH` back to WEAK
- **Change signal generation**: Modify `signal_generation_interval` in the scheduler (in seconds)
