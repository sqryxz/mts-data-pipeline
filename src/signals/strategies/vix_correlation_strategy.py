import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging

from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength, SignalDirection
from src.data.sqlite_helper import CryptoDatabase
from src.data.realtime_price_service import RealtimePriceService


class VIXCorrelationStrategy(SignalStrategy):
    """
    Strategy that generates trading signals based on VIX-crypto correlation analysis.
    
    Logic:
    - LONG signals when VIX-crypto correlation < strong_negative threshold (e.g., -0.6)
    - SHORT signals when VIX-crypto correlation > strong_positive threshold (e.g., 0.6)
    - Uses rolling correlation windows to capture changing market dynamics
    """
    
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
        self.database = CryptoDatabase()
        self.realtime_price_service = RealtimePriceService()
        
        # Extract configuration parameters
        self.assets = self.config.get('assets', ['bitcoin', 'ethereum', 'binancecoin'])
        self.correlation_thresholds = self.config.get('correlation_thresholds', {
            'strong_negative': -0.6,
            'strong_positive': 0.6
        })
        self.lookback_days = self.config.get('lookback_days', 30)
        self.position_size = self.config.get('position_size', 0.02)
        # Enhanced configuration for BTC/ETH optimization
        self.correlation_windows = self.config.get('correlation_windows', [14, 21, 30])
        self.lag_range = self.config.get('lag_range', [-3, -2, -1, 0, 1, 2, 3])
        self.min_agreement_windows = self.config.get('min_agreement_windows', 2)
        self.use_dynamic_thresholds = self.config.get('use_dynamic_thresholds', True)
        self.dynamic_threshold_quantiles = self.config.get('dynamic_threshold_quantiles', {
            'negative': 0.2,
            'positive': 0.8
        })
        # VIX spike trigger configuration (rate-of-change and MA bands)
        self.vix_spike_config = self.config.get('vix_spike', {
            'enabled': True,
            'ma_window': 10,
            'std_mult': 1.5,
            'roc_window': 3,
            'roc_up_threshold': 0.10,
            'roc_down_threshold': -0.10,
            'use_bands': True,
            'use_roc': True,
            'correlation_secondary': True
        })
        self.vix_filters = self.config.get('vix_filters', {
            'min_vix_for_long': 18.0,
            'min_vix_for_short': 20.0
        })
        self.rsi_filter = self.config.get('rsi_filter', {
            'enabled': True,
            'long_max_rsi': 45,
            'short_min_rsi': 55
        })
        self.drawdown_filter = self.config.get('drawdown_filter', {
            'enabled': True,
            'min_drawdown_for_long': 0.05,
            'min_drawup_for_short': 0.05
        })
        self.asset_overrides = self.config.get('asset_overrides', {})
        
        self.logger.info(f"VIX Correlation Strategy initialized with {len(self.assets)} assets, "
                        f"{self.lookback_days} day lookback")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze VIX-crypto correlations for all configured assets.
        
        Args:
            market_data: Historical snapshot data (preferred for backtests). If not provided
                         or incomplete, falls back to database for live analysis.
            
        Returns:
            Dict containing correlation analysis results for each asset
        """
        analysis_results = {
            'timestamp': datetime.now(),
            'strategy_name': self.config.get('name', 'VIX_Correlation_Strategy'),
            'correlation_analysis': {},
            'signal_opportunities': []
        }
        
        for asset in self.assets:
            try:
                # Prefer using provided historical snapshot (for backtests)
                df = None
                try:
                    if market_data and isinstance(market_data.get('crypto_data'), dict):
                        df = self._build_df_from_historical_data(asset, market_data)
                except Exception as e:
                    self.logger.debug(f"Falling back to DB for {asset} due to formatting issue: {e}")
                    df = None

                # Fallback: Get combined crypto + VIX data from database (live) with real-time price validation
                if df is None or df.empty:
                    # Use real-time price service to ensure fresh data
                    fresh_market_data = self.realtime_price_service.get_fresh_market_data([asset], self.lookback_days)
                    if asset in fresh_market_data and not fresh_market_data[asset].empty:
                        # Get combined analysis data and update with fresh prices
                        df = self.database.get_combined_analysis_data(asset, days=self.lookback_days)
                        fresh_data = fresh_market_data[asset]
                        if not fresh_data.empty:
                            latest_fresh = fresh_data.iloc[-1]
                            if not df.empty:
                                latest_df = df.iloc[-1]
                                # Update the latest price if significantly different
                                price_diff_percent = abs(latest_fresh['close'] - latest_df['close']) / latest_df['close']
                                if price_diff_percent > 0.01:  # 1% threshold
                                    self.logger.info(f"Updating {asset} price from ${latest_df['close']:,.2f} to ${latest_fresh['close']:,.2f}")
                                    df.iloc[-1, df.columns.get_loc('close')] = latest_fresh['close']
                    else:
                        df = self.database.get_combined_analysis_data(asset, days=self.lookback_days)
                
                # If VIX missing in snapshot, fallback to DB for that asset
                if df is not None and not df.empty and ('vix_value' not in df.columns or df['vix_value'].isna().all()):
                    db_df = self.database.get_combined_analysis_data(asset, days=self.lookback_days)
                    if db_df is not None and not db_df.empty:
                        df = db_df
                
                if df.empty:
                    self.logger.warning(f"No data available for {asset}")
                    continue
                
                # Calculate correlations
                correlation_data = self._calculate_correlations(df, asset)
                analysis_results['correlation_analysis'][asset] = correlation_data
                
                # Check for signal opportunities (even if correlation is None, allow regime fallback)
                signal_opportunity = self._evaluate_signal_opportunity(asset, correlation_data)
                if signal_opportunity:
                    analysis_results['signal_opportunities'].append(signal_opportunity)
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {asset}: {e}")
                continue
        
        self.logger.info(f"Analyzed {len(analysis_results['correlation_analysis'])} assets, "
                        f"found {len(analysis_results['signal_opportunities'])} signal opportunities")
        
        return analysis_results

    def _build_df_from_historical_data(self, asset: str, market_data: Dict[str, Any]) -> pd.DataFrame:
        """Build analysis DataFrame from backtester-provided historical data structure."""
        import pandas as pd  # local import ensures pandas available
        price_records = (market_data.get('crypto_data', {}).get(asset, {}) or {}).get('price_data', [])
        vix_records = market_data.get('vix_data', []) or []

        if not price_records:
            return pd.DataFrame()

        prices_df = pd.DataFrame(price_records)
        prices_df = prices_df.rename(columns={'date': 'date_str'})
        # Ensure required columns
        if 'close' not in prices_df.columns:
            return pd.DataFrame()
        prices_df['high'] = prices_df.get('high', prices_df['close'])
        prices_df['low'] = prices_df.get('low', prices_df['close'])

        vix_df = pd.DataFrame(vix_records)
        if not vix_df.empty:
            vix_df = vix_df.rename(columns={'date': 'date_str'})
        else:
            vix_df = pd.DataFrame(columns=['date_str', 'vix_value'])

        merged = pd.merge(prices_df, vix_df[['date_str', 'vix_value']], on='date_str', how='left')

        # Create timestamp column from date_str
        try:
            merged['timestamp'] = pd.to_datetime(merged['date_str']).astype('int64') // 10**6
        except Exception:
            merged['timestamp'] = pd.to_datetime(merged['date_str']).astype('int64') // 10**6

        # Keep only the most recent lookback_days worth of rows
        if len(merged) > self.lookback_days:
            merged = merged.iloc[-self.lookback_days:]

        return merged
    
    def _calculate_correlations(self, df: pd.DataFrame, asset: str) -> Dict[str, Any]:
        """Calculate VIX-crypto correlations with multiple timeframes and lags"""
        
        # Ensure we have both VIX and price data
        if 'vix_value' not in df.columns or df['vix_value'].isna().all():
            self.logger.warning(f"No VIX data available for {asset} correlation analysis")
            return {
                'current_correlation': None,
                'correlation_strength': 'INSUFFICIENT_DATA',
                'data_points': len(df),
                'vix_availability': 0.0
            }
        # Normalize to daily frequency if intraday rows are present (avoid repeated VIX values)
        try:
            if 'date_str' in df.columns:
                df['day'] = df['date_str'].astype(str).str.slice(0, 10)
                rows_per_day = df.groupby('day').size().median()
                if rows_per_day and rows_per_day > 1:
                    daily_df = df.groupby('day').agg({
                        'close': 'last',
                        'high': 'max',
                        'low': 'min',
                        'vix_value': 'last'
                    }).reset_index().rename(columns={'day': 'date_str'})
                    df = daily_df
        except Exception as e:
            self.logger.debug(f"Daily normalization skipped for {asset}: {e}")

        # Clean data - remove rows where either VIX or price is missing
        clean_df = df.dropna(subset=['vix_value', 'close']).copy()
        
        if len(clean_df) < 10:  # Need minimum data points for correlation
            self.logger.warning(f"Insufficient clean data for {asset}: {len(clean_df)} points")
            return {
                'current_correlation': None,
                'correlation_strength': 'INSUFFICIENT_DATA',
                'data_points': len(clean_df),
                'vix_availability': len(clean_df) / len(df)
            }
        
        # Compute returns for correlation calculations
        clean_df['price_return'] = clean_df['close'].pct_change()
        clean_df['vix_return'] = pd.Series(clean_df['vix_value']).pct_change()

        # Calculate correlations across windows and lags
        correlations = {}
        best_abs_corr = None
        best_corr_value = None
        best_window = None
        best_lag = 0
        dynamic_neg_threshold = None
        dynamic_pos_threshold = None

        for window in self.correlation_windows:
            if len(clean_df) >= window + max(0, max(self.lag_range)):
                for lag in self.lag_range:
                    vix_series = clean_df['vix_return'].shift(lag)
                    rolling_corr_series = clean_df['price_return'].rolling(window=window).corr(vix_series)
                    corr_value = rolling_corr_series.iloc[-1]
                    if corr_value is not None and not np.isnan(corr_value):
                        correlations[f'{window}d_lag{lag}'] = float(corr_value)
                        if best_abs_corr is None or abs(corr_value) > best_abs_corr:
                            best_abs_corr = abs(corr_value)
                            best_corr_value = float(corr_value)
                            best_window = window
                            best_lag = lag

                    if self.use_dynamic_thresholds and rolling_corr_series.dropna().shape[0] > 20:
                        neg_q = self.dynamic_threshold_quantiles.get('negative', 0.2)
                        pos_q = self.dynamic_threshold_quantiles.get('positive', 0.8)
                        current_neg = float(np.nanquantile(rolling_corr_series.values, neg_q))
                        current_pos = float(np.nanquantile(rolling_corr_series.values, pos_q))
                        dynamic_neg_threshold = current_neg if dynamic_neg_threshold is None else min(dynamic_neg_threshold, current_neg)
                        dynamic_pos_threshold = current_pos if dynamic_pos_threshold is None else max(dynamic_pos_threshold, current_pos)

        # Fallback to simple correlation if enhanced calc failed
        if best_corr_value is None:
            fallback_window = min(max(self.correlation_windows), len(clean_df))
            rolling_corr = clean_df['close'].rolling(window=fallback_window).corr(clean_df['vix_value'])
            best_corr_value = float(rolling_corr.iloc[-1]) if not np.isnan(rolling_corr.iloc[-1]) else None
            best_window = fallback_window
            best_lag = 0

        correlation_strength = self._classify_correlation_strength(best_corr_value)

        # Compute filters: RSI and drawdown/drawup and volatility
        rsi_series = self._calculate_rsi_series(clean_df['close'], period=14)
        latest_rsi = float(rsi_series.iloc[-1]) if len(rsi_series) else None
        rolling_high_14 = clean_df['high'].rolling(window=14, min_periods=1).max()
        rolling_low_14 = clean_df['low'].rolling(window=14, min_periods=1).min()
        drawdown_from_14d_high = (rolling_high_14 - clean_df['close']) / rolling_high_14
        drawup_from_14d_low = (clean_df['close'] - rolling_low_14) / rolling_low_14
        latest_drawdown = float(drawdown_from_14d_high.iloc[-1]) if len(drawdown_from_14d_high) else None
        latest_drawup = float(drawup_from_14d_low.iloc[-1]) if len(drawup_from_14d_low) else None
        volatility_14d = float(clean_df['price_return'].rolling(window=14, min_periods=1).std().iloc[-1])

        # VIX percentile within lookback
        try:
            vix_series = clean_df['vix_value'].astype(float)
            vix_rank_pct = vix_series.rank(pct=True)
            # Use the latest non-null percentile rather than the last row blindly
            vix_percentile = float(vix_rank_pct.dropna().iloc[-1] * 100.0) if not vix_rank_pct.dropna().empty else None
        except Exception:
            vix_percentile = None

        # VIX spike metrics (MA bands and ROC)
        try:
            ma_window = int(self.vix_spike_config.get('ma_window', 10))
            std_mult = float(self.vix_spike_config.get('std_mult', 1.5))
            roc_window = int(self.vix_spike_config.get('roc_window', 3))

            vix_ma = vix_series.rolling(window=ma_window, min_periods=1).mean()
            vix_std = vix_series.rolling(window=ma_window, min_periods=1).std().fillna(0.0)
            upper_band = vix_ma + std_mult * vix_std
            lower_band = vix_ma - std_mult * vix_std
            latest_vix = float(vix_series.iloc[-1]) if len(vix_series) else None
            latest_ma = float(vix_ma.iloc[-1]) if len(vix_ma) else None
            latest_std = float(vix_std.iloc[-1]) if len(vix_std) else 0.0
            latest_upper = float(upper_band.iloc[-1]) if len(upper_band) else None
            latest_lower = float(lower_band.iloc[-1]) if len(lower_band) else None
            band_zscore = (latest_vix - latest_ma) / latest_std if latest_std and latest_std > 0 else 0.0

            # Rate-of-change over roc_window days
            vix_roc = vix_series.pct_change(periods=roc_window)
            latest_roc = float(vix_roc.iloc[-1]) if len(vix_roc) else None

            vix_spike = {
                'upper_band_breach': bool(latest_vix is not None and latest_upper is not None and latest_vix > latest_upper),
                'lower_band_breach': bool(latest_vix is not None and latest_lower is not None and latest_vix < latest_lower),
                'band_zscore': float(band_zscore),
                'roc_value': latest_roc,
                'ma_value': latest_ma,
                'upper_band': latest_upper,
                'lower_band': latest_lower
            }
        except Exception:
            vix_spike = {
                'upper_band_breach': False,
                'lower_band_breach': False,
                'band_zscore': 0.0,
                'roc_value': None,
                'ma_value': None,
                'upper_band': None,
                'lower_band': None
            }

        return {
            'current_correlation': best_corr_value,
            'correlation_strength': correlation_strength,
            'correlations_by_window': correlations,
            'best_window': best_window,
            'best_lag': best_lag,
            'data_points': len(clean_df),
            'vix_availability': len(clean_df) / len(df),
            'latest_vix': clean_df['vix_value'].iloc[-1] if not clean_df.empty else None,
            'latest_price': self._get_current_price(asset, clean_df),
            'vix_percentile': vix_percentile,
            'vix_spike': vix_spike,
            'dynamic_thresholds': {
                'negative': dynamic_neg_threshold,
                'positive': dynamic_pos_threshold
            },
            'filters': {
                'rsi_14': latest_rsi,
                'drawdown_from_14d_high': latest_drawdown,
                'drawup_from_14d_low': latest_drawup,
                'volatility_14d': volatility_14d
            }
        }
    
    def _get_current_price(self, asset: str, clean_df: pd.DataFrame) -> float:
        """Get current price, using fresh data if VIX data is stale"""
        if clean_df.empty:
            return None
            
        # Check if VIX data is stale (older than 2 days)
        latest_vix_date = clean_df.iloc[-1]['date_str']
        from datetime import datetime as dt
        vix_date = dt.strptime(latest_vix_date, '%Y-%m-%d')
        days_old = (dt.now() - vix_date).days
        
        if days_old > 2:
            # Get fresh crypto price from crypto_ohlcv table
            try:
                fresh_crypto = self.database.get_crypto_data(asset, days=3)
                if not fresh_crypto.empty:
                    current_price = fresh_crypto['close'].iloc[-1]
                    self.logger.info(f"Using fresh {asset} price ${current_price:,.2f} (VIX data {days_old} days old)")
                    return current_price
            except Exception as e:
                self.logger.warning(f"Could not get fresh price for {asset}: {e}")
        
        # Fall back to price from combined dataset
        return clean_df['close'].iloc[-1]
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength based on absolute value"""
        if correlation is None or np.isnan(correlation):
            return 'INSUFFICIENT_DATA'
        
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return 'VERY_STRONG'
        elif abs_corr >= 0.5:
            return 'STRONG'
        elif abs_corr >= 0.3:
            return 'MODERATE'
        elif abs_corr >= 0.1:
            return 'WEAK'
        else:
            return 'NEGLIGIBLE'

    def _calculate_rsi_series(self, price_series: pd.Series, period: int = 14) -> pd.Series:
        if len(price_series) < period + 1:
            return pd.Series([50.0] * len(price_series), index=price_series.index)
        delta = price_series.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        avg_gain = gains.rolling(window=period, min_periods=1).mean()
        avg_loss = losses.rolling(window=period, min_periods=1).mean()
        rs = avg_gain / avg_loss.replace({0.0: np.nan})
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)
    
    def _evaluate_signal_opportunity(self, asset: str, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if current correlation presents a trading opportunity with filters and regimes"""
        correlation = correlation_data['current_correlation']

        # Spike-based triggers first (primary basis)
        vix_spike_cfg = self.vix_spike_config if isinstance(self.vix_spike_config, dict) else {}
        spike_enabled = bool(vix_spike_cfg.get('enabled', True))
        use_bands = bool(vix_spike_cfg.get('use_bands', True))
        use_roc = bool(vix_spike_cfg.get('use_roc', True))
        roc_up_th = float(vix_spike_cfg.get('roc_up_threshold', 0.10))
        roc_down_th = float(vix_spike_cfg.get('roc_down_threshold', -0.10))
        corr_secondary = bool(vix_spike_cfg.get('correlation_secondary', True))

        signal_type = None
        spike_meta = correlation_data.get('vix_spike') or {}
        if spike_enabled:
            band_long = use_bands and spike_meta.get('upper_band_breach', False)
            band_short = use_bands and spike_meta.get('lower_band_breach', False)
            roc_val = spike_meta.get('roc_value')
            roc_long = use_roc and (roc_val is not None and roc_val >= roc_up_th)
            roc_short = use_roc and (roc_val is not None and roc_val <= roc_down_th)

            if band_long or roc_long:
                signal_type = SignalType.LONG
            elif band_short or roc_short:
                signal_type = SignalType.SHORT

        # If no spike signal, optionally fall back to correlation logic
        if not signal_type and (correlation is None or np.isnan(correlation)):
            if not corr_secondary:
                return None
        
        # Determine thresholds (per-asset overrides or dynamic) for correlation secondary path
        overrides = self.asset_overrides.get(asset, {}) if isinstance(self.asset_overrides, dict) else {}
        thresholds = overrides.get('correlation_thresholds', self.correlation_thresholds)
        strong_negative = thresholds.get('strong_negative', self.correlation_thresholds.get('strong_negative', -0.6))
        strong_positive = thresholds.get('strong_positive', self.correlation_thresholds.get('strong_positive', 0.6))

        if self.use_dynamic_thresholds:
            dyn = correlation_data.get('dynamic_thresholds') or {}
            if dyn.get('negative') is not None:
                strong_negative = float(dyn['negative'])
            if dyn.get('positive') is not None:
                strong_positive = float(dyn['positive'])

        # Agreement across multiple windows
        agree_count_neg = 0
        agree_count_pos = 0
        for _, value in (correlation_data.get('correlations_by_window') or {}).items():
            if value is None or np.isnan(value):
                continue
            if value <= strong_negative:
                agree_count_neg += 1
            if value >= strong_positive:
                agree_count_pos += 1

        # Base signal determination
        if not signal_type:
            if correlation is not None and not np.isnan(correlation):
                if agree_count_neg >= self.min_agreement_windows and correlation <= strong_negative:
                    signal_type = SignalType.LONG
                elif agree_count_pos >= self.min_agreement_windows and correlation >= strong_positive:
                    signal_type = SignalType.SHORT

        if not signal_type:
            # Optional regime fallback on VIX percentile
            vix_pct = correlation_data.get('vix_percentile')
            if vix_pct is not None:
                if vix_pct >= 60:
                    signal_type = SignalType.LONG
                elif vix_pct <= 40:
                    signal_type = SignalType.SHORT
            if not signal_type:
                return None

        # Regime and technical filters
        vix_level = correlation_data.get('latest_vix')
        filters = correlation_data.get('filters') or {}
        rsi_14 = filters.get('rsi_14')
        dd = filters.get('drawdown_from_14d_high')
        du = filters.get('drawup_from_14d_low')

        vix_filters = overrides.get('vix_filters', self.vix_filters)
        rsi_filter = overrides.get('rsi_filter', self.rsi_filter)
        drawdown_filter = overrides.get('drawdown_filter', self.drawdown_filter)

        # VIX regime requirements
        if vix_level is None:
            return None
        if signal_type == SignalType.LONG and vix_level < float(vix_filters.get('min_vix_for_long', 18.0)):
            return None
        if signal_type == SignalType.SHORT and vix_level < float(vix_filters.get('min_vix_for_short', 20.0)):
            return None

        # RSI filter
        if rsi_filter.get('enabled', True) and rsi_14 is not None:
            if signal_type == SignalType.LONG and rsi_14 > float(rsi_filter.get('long_max_rsi', 45)):
                return None
            if signal_type == SignalType.SHORT and rsi_14 < float(rsi_filter.get('short_min_rsi', 55)):
                return None

        # Drawdown/Drawup filters
        if drawdown_filter.get('enabled', True):
            if signal_type == SignalType.LONG and dd is not None and dd < float(drawdown_filter.get('min_drawdown_for_long', 0.05)):
                return None
            if signal_type == SignalType.SHORT and du is not None and du < float(drawdown_filter.get('min_drawup_for_short', 0.05)):
                return None

        # Confidence scaled by spike intensity or correlation
        if spike_enabled and spike_meta:
            # Use band z-score and ROC intensity for confidence
            z = abs(float(spike_meta.get('band_zscore') or 0.0))
            roc = spike_meta.get('roc_value')
            roc_norm = 0.0
            if roc is not None:
                if signal_type == SignalType.LONG and roc_up_th > 0:
                    roc_norm = max(0.0, min(1.0, roc / roc_up_th))
                elif signal_type == SignalType.SHORT and roc_down_th < 0:
                    roc_norm = max(0.0, min(1.0, abs(roc / roc_down_th)))
            base_conf = max(0.5, min(1.0, 0.5 * (min(z / max(self.vix_spike_config.get('std_mult', 1.5), 1e-6), 1.0) + roc_norm)))
        elif correlation is not None and not np.isnan(correlation):
            if signal_type == SignalType.LONG:
                base_conf = min(abs(correlation) / max(abs(strong_negative), 1e-6), 1.0)
            else:
                base_conf = min(correlation / max(strong_positive, 1e-6), 1.0)
        else:
            base_conf = 0.6  # default confidence for regime fallback

        vix_scale = max(0.6, min(1.0, 25.0 / max(vix_level, 10.0)))
        confidence = max(0.0, min(1.0, base_conf * vix_scale))
        signal_strength = SignalStrength.STRONG if confidence > 0.75 else (SignalStrength.MODERATE if confidence > 0.5 else SignalStrength.WEAK)

        return {
            'asset': asset,
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'confidence': confidence,
            'correlation': correlation,
            'latest_price': correlation_data['latest_price'],
            'latest_vix': vix_level,
            'best_window': correlation_data.get('best_window'),
            'best_lag': correlation_data.get('best_lag'),
            'filters': filters,
            'vix_spike': spike_meta
        }
    
    def generate_signals(self, analysis_results: Dict[str, Any]) -> List[TradingSignal]:
        """
        Generate trading signals based on correlation analysis.
        
        Args:
            analysis_results: Results from analyze() method
            
        Returns:
            List of TradingSignal objects
        """
        signals = []
        
        for opportunity in analysis_results.get('signal_opportunities', []):
            try:
                # Calculate risk management parameters
                current_price = opportunity['latest_price']
                vix_level = opportunity['latest_vix']
                
                # Adjust position size by VIX and recent volatility
                vix_adjustment = max(0.5, min(1.0, 25.0 / max(vix_level, 10.0)))
                vol = opportunity.get('filters', {}).get('volatility_14d') or 0.0
                vol_adjustment = 1.0 if vol <= 0 else max(0.5, min(1.0, 0.02 / float(vol)))
                adjusted_position_size = self.position_size * vix_adjustment * vol_adjustment
                
                # Volatility-aware stop loss and take profit
                risk_unit = max(0.03, min(0.12, (opportunity.get('filters', {}).get('volatility_14d') or 0.04) * 3))
                if opportunity['signal_type'] == SignalType.LONG:
                    stop_loss = current_price * (1 - risk_unit)
                    take_profit = current_price * (1 + risk_unit * 2)
                elif opportunity['signal_type'] == SignalType.SHORT:
                    stop_loss = current_price * (1 + risk_unit)
                    take_profit = current_price * (1 - risk_unit * 2)
                else:
                    stop_loss = None
                    take_profit = None
                
                # Create trading signal
                signal = TradingSignal(
                    symbol=opportunity['asset'],
                    signal_type=opportunity['signal_type'],
                    direction=SignalDirection.BUY if opportunity['signal_type'] == SignalType.LONG else SignalDirection.SELL,
                    timestamp=analysis_results['timestamp'],
                    price=current_price,
                    strategy_name=analysis_results['strategy_name'],
                    signal_strength=opportunity['signal_strength'],
                    confidence=opportunity['confidence'],
                    position_size=adjusted_position_size,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    max_risk=0.02,  # Maximum 2% risk per trade
                    correlation_value=opportunity['correlation'],
                    analysis_data={
                        'vix_level': vix_level,
                        'correlation_strength': self._classify_correlation_strength(opportunity['correlation']),
                        'vix_adjustment_factor': vix_adjustment,
                        'best_window': opportunity.get('best_window'),
                        'best_lag': opportunity.get('best_lag'),
                        'filters': opportunity.get('filters', {})
                    }
                )
                
                signals.append(signal)
                
                corr_val = opportunity.get('correlation')
                corr_str = f"{corr_val:.3f}" if isinstance(corr_val, (int, float)) and not np.isnan(corr_val) else "None"
                self.logger.info(
                    f"Generated {signal.signal_type.value} signal for {signal.symbol} "
                    f"(correlation: {corr_str}, confidence: {signal.confidence:.3f})"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to generate signal for {opportunity.get('asset', 'unknown')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(signals)} trading signals")
        return signals
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters for logging/optimization"""
        return {
            'strategy_name': self.config.get('name', 'VIX_Correlation_Strategy'),
            'assets': self.assets,
            'correlation_thresholds': self.correlation_thresholds,
            'lookback_days': self.lookback_days,
            'position_size': self.position_size,
            'correlation_windows': self.correlation_windows,
            'lag_range': self.lag_range,
            'min_agreement_windows': self.min_agreement_windows,
            'use_dynamic_thresholds': self.use_dynamic_thresholds,
            'vix_spike': self.vix_spike_config,
            'vix_filters': self.vix_filters,
            'rsi_filter': self.rsi_filter,
            'drawdown_filter': self.drawdown_filter,
            'version': '2.1.0'
        } 