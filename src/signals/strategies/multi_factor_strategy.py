"""Multi-Factor Signal Strategy - Three-layer signal system."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.data.sqlite_helper import CryptoDatabase
from src.signals.strategies.base_strategy import SignalStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalDirection


class MultiFactorStrategy(SignalStrategy):
    """Multi-Factor Signal Strategy combining macro regime, momentum, and mean reversion."""
    
    def __init__(self, config_path: str = "config/strategies/multi_factor.json"):
        super().__init__(config_path)
        self.db = CryptoDatabase('data/crypto_data.db')
        self.excluded = self.config.get('excluded_assets', ['tether', 'usdt'])
        self.weights = self.config.get('layer_weights', {'macro': 0.3, 'trend': 0.4, 'reversion': 0.3})
        self.thresholds = self.config.get('alert_thresholds', {'strong_long': 0.6, 'lean_long': 0.3, 'lean_short': -0.3, 'strong_short': -0.6})
        self.betas = self.config.get('asset_betas', {})
        self.windows = self.config.get('indicator_windows', {'sma_short': 20, 'sma_long': 50, 'sma_200': 200, 'rsi': 14})
        self.logger = logging.getLogger(__name__)
        
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info("Starting Multi-Factor analysis")
        
        results = {'signals': [], 'macro_analysis': {}, 'asset_analysis': {}}
        
        # Layer 1: Macro
        macro_score, macro_details = self._calc_macro_regime()
        results['macro_score'] = macro_score
        results['macro_analysis'] = macro_details
        
        # Assets to analyze
        assets = [a for a in self._get_assets() if a.lower() not in [x.lower() for x in self.excluded]]
        
        for asset in assets:
            data = market_data.get(asset, {}).get('dataframe')
            if data is None or len(data) < 50:
                continue
            
            # Layer 2: Trend & Reversion
            trend, trend_d = self._calc_trend(data)
            rev, rev_d = self._calc_reversion(data)
            
            # Composite
            beta = self.betas.get(asset, 1.0)
            adj_macro = max(-1, min(1, macro_score * beta))
            composite = self.weights['macro'] * adj_macro + self.weights['trend'] * trend + self.weights['reversion'] * rev
            
            # Gate check
            gate = self._check_gate(adj_macro, trend, rev)
            direction = self._get_direction(composite, gate)
            
            results['asset_analysis'][asset] = {
                'trend_score': trend, 'reversion_score': rev, 
                'composite': composite, 'direction': direction, 'gate': gate
            }
            
            if direction and direction != 'NEUTRAL':
                sig = self._make_signal(asset, direction, composite)
                if sig:
                    results['signals'].append(sig)
            
            self._log_to_db(asset, adj_macro, trend, rev, composite, direction, gate, macro_details)
        
        self.logger.info(f"Multi-Factor complete: {len(results['signals'])} signals")
        return results
    
    def _calc_macro_regime(self):
        details = {}
        scores = []
        
        # Get latest macro data
        macro = self._get_macro_latest()
        vix = macro.get('VIXCLS')
        
        if vix:
            if vix < 16:
                scores.append(1.0)
            elif vix > 25:
                scores.append(-1.0)
            details['vix'] = vix
        
        # DXY
        dxy = macro.get('DTWEXBGS')
        if dxy:
            dxy_ma = self._get_sma('DTWEXBGS', 20)
            if dxy_ma and dxy < dxy_ma:
                scores.append(1.0)
            elif dxy_ma and dxy > dxy_ma:
                scores.append(-1.0)
        
        # HY Spread
        hy = macro.get('BAMLH0A0HYM2')
        if hy:
            if hy < 3.0:
                scores.append(1.0)
            elif hy > 5.0:
                scores.append(-1.0)
        
        # Yield curve
        d10 = macro.get('DGS10')
        d2 = macro.get('DGS2')
        if d10 and d2:
            spread = d10 - d2
            if spread > 0.3:
                scores.append(1.0)
            elif spread < 0:
                scores.append(-1.0)
        
        score = sum(scores) / len(scores) if scores else 0.0
        return max(-1, min(1, score)), details
    
    def _calc_trend(self, df: pd.DataFrame) -> tuple:
        close = df['close']
        w = self.windows
        scores = []
        
        # SMA cross
        sma20 = close.rolling(w.get('sma_short', 20)).mean()
        sma50 = close.rolling(w.get('sma_long', 50)).mean()
        if sma20.iloc[-1] > sma50.iloc[-1]:
            scores.append(1.0)
        elif sma20.iloc[-1] < sma50.iloc[-1]:
            scores.append(-1.0)
        
        # Price vs SMA200
        sma200 = close.rolling(w.get('sma_200', 200)).mean()
        if close.iloc[-1] > sma200.iloc[-1]:
            scores.append(0.5)
        elif close.iloc[-1] < sma200.iloc[-1]:
            scores.append(-0.5)
        
        # ROC
        roc_period = w.get('roc_period', 14)
        if len(close) >= roc_period:
            roc = (close.iloc[-1] - close.iloc[-roc_period]) / close.iloc[-roc_period] * 100
            if roc > 5:
                scores.append(1.0)
            elif roc > 0:
                scores.append(0.5)
            elif roc < -5:
                scores.append(-1.0)
            elif roc < 0:
                scores.append(-0.5)
        
        return sum(scores)/len(scores) if scores else 0.0, {'scores': scores}
    
    def _calc_reversion(self, df: pd.DataFrame) -> tuple:
        close = df['close']
        w = self.windows
        scores = []
        
        # RSI
        rsi_period = w.get('rsi', 14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi.iloc[-1] < 30:
            scores.append(1.0)
        elif rsi.iloc[-1] < 45:
            scores.append(0.5)
        elif rsi.iloc[-1] > 70:
            scores.append(-1.0)
        elif rsi.iloc[-1] > 55:
            scores.append(-0.5)
        
        return sum(scores)/len(scores) if scores else 0.0, {'rsi': rsi.iloc[-1]}
    
    def _check_gate(self, macro, trend, rev) -> bool:
        dirs = [
            'long' if macro > 0 else 'short' if macro < 0 else 'neutral',
            'long' if trend > 0 else 'short' if trend < 0 else 'neutral',
            'long' if rev > 0 else 'short' if rev < 0 else 'neutral'
        ]
        return dirs.count('long') >= 2 or dirs.count('short') >= 2
    
    def _get_direction(self, composite, gate) -> Optional[str]:
        if not gate:
            return None
        if composite > self.thresholds['strong_long']:
            return 'STRONG_LONG'
        elif composite > self.thresholds['lean_long']:
            return 'LONG'
        elif composite < self.thresholds['strong_short']:
            return 'STRONG_SHORT'
        elif composite < self.thresholds['lean_short']:
            return 'SHORT'
        return 'NEUTRAL'
    
    def _make_signal(self, asset, direction, score):
        try:
            return TradingSignal(
                symbol=asset.upper(),
                signal_type=SignalType.MOMENTUM,
                direction=SignalDirection.LONG if 'LONG' in direction else SignalDirection.SHORT,
                confidence=min(0.95, 0.5 + abs(score) * 0.5),
                strength=abs(score),
                timestamp=int(datetime.now().timestamp() * 1000),
                source='multi_factor',
                metadata={'composite': score}
            )
        except:
            return None
    
    def _get_macro_latest(self) -> Dict:
        q = "SELECT indicator, value FROM macro_indicators WHERE (indicator, date) IN (SELECT indicator, MAX(date) FROM macro_indicators GROUP BY indicator)"
        df = self.db.query_to_dataframe(q)
        return dict(zip(df['indicator'], df['value']))
    
    def _get_sma(self, indicator, days) -> Optional[float]:
        q = f"SELECT AVG(value) as sma FROM (SELECT value FROM macro_indicators WHERE indicator = ? ORDER BY date DESC LIMIT ?)"
        df = self.db.query_to_dataframe(q, (indicator, days))
        return float(df['sma'].iloc[0]) if not df.empty and df['sma'].iloc[0] else None
    
    def _get_assets(self) -> List[str]:
        df = self.db.query_to_dataframe("SELECT DISTINCT cryptocurrency FROM crypto_ohlcv")
        return df['cryptocurrency'].tolist()
    
    def _log_to_db(self, asset, macro, trend, rev, comp, direction, gate, macro_details):
        try:
            import sqlite3
            conn = sqlite3.connect('data/crypto_data.db')
            conn.execute("""INSERT INTO multi_factor_signals 
                (timestamp, asset, macro_score, trend_score, reversion_score, composite_score, signal_direction, confirmation_gate_passed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (int(datetime.now().timestamp()*1000), asset, macro, trend, rev, comp, direction, 1 if gate else 0))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"DB log error: {e}")
    
    def generate_signals(self, df: pd.DataFrame, asset: str) -> List[TradingSignal]:
        result = self.analyze({asset: {'dataframe': df}})
        return result.get('signals', [])
    
    def get_parameters(self) -> Dict[str, Any]:
        return {'name': 'Multi-Factor', 'weights': self.weights, 'thresholds': self.thresholds}
