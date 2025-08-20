# Optimized Pipeline Configuration Changes

## User Request
User requested changing other cryptocurrency collection from **daily** to **every 60 minutes** while keeping:
- BTC & ETH at 15-minute intervals
- Macro indicators at daily intervals

## Changes Made

### ✅ Updated Collection Strategy

| **Asset Type** | **Previous** | **Updated** | **Daily API Calls** |
|----------------|--------------|-------------|-------------------|
| BTC & ETH | Every 15 min | Every 15 min | 192 (unchanged) |
| Other Cryptos | Daily | **Every 60 min** | 8 → **192** |
| Macro Indicators | Daily | Daily | 9 (unchanged) |
| **Total** | **209/day** | **393/day** | **+184 calls** |

### 📊 API Usage Impact

- **Previous optimization**: 93% reduction (209 vs 2880 calls)
- **New optimization**: 86% reduction (393 vs 2880 calls)
- **Rate limit usage**: Still well within limits (~20% vs 50% max)

### 🔧 Technical Changes

#### 1. Multi-Tier Scheduler (`src/services/multi_tier_scheduler.py`)
- Changed `AssetTier.DAILY` → `AssetTier.HOURLY` for other cryptos
- Updated interval: `24 * 60 * 60` → `60 * 60` seconds
- Updated daily calculation: `assets * 1` → `assets * 24`
- Updated logging and variable names

#### 2. Main Script (`main_optimized.py`)
- Updated collection strategy messages
- Adjusted API usage estimates and rate limit compliance
- Updated status display for hourly collections

#### 3. Configuration (`config/optimized_collection.json`)
- Changed daily tier to hourly tier
- Updated API call estimates: 210 → 393
- Updated reduction percentage: 93% → 86%
- Adjusted rate limit utilization calculations

#### 4. Start Script (`scripts/start_optimized_pipeline.sh`)
- Updated configuration display messages
- Adjusted API call estimates in help text

## ✅ Verification

Test run confirms:
```
✅ Configuration valid - 19 tasks configured
📡 Estimated daily API usage: 393 calls
✅ All tests passed!
```

### Collection Schedule
- **High frequency assets**: 2 assets × 96 collections = 192 calls/day
- **Hourly assets**: 8 assets × 24 collections = 192 calls/day  
- **Macro indicators**: 9 indicators × 1 collection = 9 calls/day
- **Total**: 393 API calls/day

## 🚀 Ready to Use

The optimized pipeline now provides:
- ✅ **BTC & ETH every 15 minutes** (high-frequency pairs)
- ✅ **Other cryptos every 60 minutes** (as requested)
- ✅ **Macro indicators daily** (economic data)
- ✅ **86% API reduction** vs all-15min collection
- ✅ **Background operation** with full monitoring

Start with: `./scripts/start_optimized_pipeline.sh start` 