import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from src.data.sqlite_helper import CryptoDatabase


class TestStrategyMarketData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create database instance
        self.db = CryptoDatabase(self.db_path)
        
        # Insert test data
        self._insert_test_data()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _insert_test_data(self):
        """Insert test crypto and VIX data"""
        # Generate test dates - make them recent relative to current time
        # Start from 65 days ago to ensure we have enough data for 60-day queries
        base_date = datetime.now() - timedelta(days=65)
        test_dates = [base_date + timedelta(days=i) for i in range(60)]
        
        # Insert crypto data for multiple assets
        crypto_data = []
        asset_prices = {}  # Track prices per asset
        
        for asset in ['bitcoin', 'ethereum', 'binancecoin']:
            base_price = {'bitcoin': 50000, 'ethereum': 3000, 'binancecoin': 400}[asset]
            asset_prices[asset] = base_price
            
            for i, date in enumerate(test_dates):
                # Create realistic price movements with some volatility
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                
                if i == 0:
                    price = base_price
                else:
                    # Use previous price for this asset
                    price = asset_prices[asset] * (1 + price_change)
                
                # Add some drawdown scenarios
                if i == 25:  # Mid-period drawdown
                    price *= 0.85  # 15% drop
                elif i == 45:  # Late-period drawdown
                    price *= 0.90  # 10% drop
                
                # Update tracked price for this asset
                asset_prices[asset] = price
                
                crypto_data.append({
                    'cryptocurrency': asset,
                    'timestamp': int(date.timestamp() * 1000),
                    'date_str': date.strftime('%Y-%m-%d'),
                    'open': price * 0.99,
                    'high': price * 1.02,
                    'low': price * 0.98,
                    'close': price,
                    'volume': np.random.uniform(1000000, 5000000)
                })
        
        # Insert VIX data with some spikes
        vix_data = []
        for i, date in enumerate(test_dates):
            # Base VIX around 20, with spikes
            vix_value = 20 + np.random.normal(0, 5)
            
            # Add VIX spikes aligned with crypto drawdowns
            if i == 25:  # VIX spike during first drawdown
                vix_value = 35
            elif i == 45:  # VIX spike during second drawdown
                vix_value = 30
            elif i in [26, 27, 46, 47]:  # Extended spike periods
                vix_value = max(25, vix_value)
            
            vix_data.append({
                'indicator': 'VIXCLS',
                'date': date.strftime('%Y-%m-%d'),
                'value': max(10, vix_value),  # Keep VIX above 10
                'is_interpolated': False,
                'is_forward_filled': False
            })
        
        # Insert other macro indicators
        other_macro_data = []
        for indicator in ['DFF', 'DGS10', 'DTWEXBGS']:
            base_value = {'DFF': 5.0, 'DGS10': 4.0, 'DTWEXBGS': 105.0}[indicator]
            for date in test_dates:
                other_macro_data.append({
                    'indicator': indicator,
                    'date': date.strftime('%Y-%m-%d'),
                    'value': base_value + np.random.normal(0, 0.1),
                    'is_interpolated': False,
                    'is_forward_filled': False
                })
        
        # Insert all data
        self.db.insert_crypto_data(crypto_data)
        self.db.insert_macro_data(vix_data + other_macro_data)
    
    def test_get_strategy_market_data_basic(self):
        """Test basic functionality of get_strategy_market_data"""
        assets = ['bitcoin', 'ethereum', 'binancecoin']
        result = self.db.get_strategy_market_data(assets, days=30)
        
        # Check basic structure
        self.assertIsInstance(result, dict)
        self.assertIn('vix_data', result)
        self.assertIn('crypto_data', result)
        self.assertIn('market_summary', result)
        self.assertIn('timestamp_range', result)
        
        # Check each asset has its own data
        for asset in assets:
            self.assertIn(asset, result)
            self.assertIsInstance(result[asset], pd.DataFrame)
    
    def test_task_6_requirements(self):
        """Test specific Task 6 requirements: VIX data, crypto OHLCV, rolling highs, aligned timestamps"""
        assets = ['bitcoin', 'ethereum', 'binancecoin']
        result = self.db.get_strategy_market_data(assets, days=30)
        
        # Requirement 1: VIX data (current level, historical)
        self.assertIn('vix_data', result)
        self.assertFalse(result['vix_data'].empty)
        self.assertIn('vix_value', result['vix_data'].columns)
        
        # VIX summary should include current level
        vix_summary = result['market_summary']['vix_summary']
        self.assertIn('current_vix', vix_summary)
        self.assertIsNotNone(vix_summary['current_vix'])
        
        # Requirement 2: Crypto OHLCV data for all assets
        for asset in assets:
            if not result[asset].empty:
                asset_df = result[asset]
                required_ohlcv = ['open', 'high', 'low', 'close', 'volume']
                for col in required_ohlcv:
                    self.assertIn(col, asset_df.columns)
        
        # Requirement 3: Rolling highs for drawdown calculation
        for asset in assets:
            if not result[asset].empty:
                asset_df = result[asset]
                # Check multiple rolling high periods
                rolling_high_cols = ['rolling_high_7d', 'rolling_high_14d', 'rolling_high_30d']
                for col in rolling_high_cols:
                    self.assertIn(col, asset_df.columns)
                
                # Check drawdown calculations from rolling highs
                drawdown_cols = ['drawdown_from_7d_high', 'drawdown_from_14d_high', 'drawdown_from_30d_high']
                for col in drawdown_cols:
                    self.assertIn(col, asset_df.columns)
        
        # Requirement 4: Aligned timestamps
        self.assertIn('timestamp_range', result)
        self.assertIn('start_timestamp', result['timestamp_range'])
        self.assertIn('end_timestamp', result['timestamp_range'])
        
        # Check that crypto data timestamps are within expected range
        combined_df = result['crypto_data']
        if not combined_df.empty:
            min_timestamp = combined_df['timestamp'].min()
            max_timestamp = combined_df['timestamp'].max()
            self.assertGreaterEqual(min_timestamp, result['timestamp_range']['start_timestamp'])
            self.assertLessEqual(max_timestamp, result['timestamp_range']['end_timestamp'])
    
    def test_vix_data_structure(self):
        """Test VIX data structure and analysis columns"""
        assets = ['bitcoin', 'ethereum']
        result = self.db.get_strategy_market_data(assets, days=30)
        
        vix_df = result['vix_data']
        self.assertFalse(vix_df.empty)
        
        # Check required VIX columns
        expected_vix_columns = [
            'date', 'vix_value', 'vix_percentile', 'vix_ma_10', 'vix_ma_20',
            'vix_spike', 'vix_extreme', 'vix_regime'
        ]
        for col in expected_vix_columns:
            self.assertIn(col, vix_df.columns)
        
        # Check VIX spike detection
        self.assertTrue(vix_df['vix_spike'].any())  # Should have some spikes in test data
        
        # Check VIX regime classification
        self.assertIn('vix_regime', vix_df.columns)
        self.assertTrue(vix_df['vix_regime'].isin(['Low', 'Normal', 'High', 'Extreme']).all())
    
    def test_crypto_data_technical_indicators(self):
        """Test that crypto data includes technical indicators"""
        assets = ['bitcoin', 'ethereum']
        result = self.db.get_strategy_market_data(assets, days=30)
        
        # Check bitcoin data has technical indicators
        btc_df = result['bitcoin']
        self.assertFalse(btc_df.empty)
        
        # Check rolling highs and lows
        rolling_high_columns = [
            'rolling_high_7d', 'rolling_high_14d', 'rolling_high_30d',
            'rolling_low_7d', 'rolling_low_14d', 'rolling_low_30d'
        ]
        for col in rolling_high_columns:
            self.assertIn(col, btc_df.columns)
        
        # Check drawdown calculations
        drawdown_columns = [
            'drawdown_from_7d_high', 'drawdown_from_14d_high', 'drawdown_from_30d_high'
        ]
        for col in drawdown_columns:
            self.assertIn(col, btc_df.columns)
            # Drawdowns should be non-negative
            self.assertTrue((btc_df[col] >= 0).all())
        
        # Check moving averages
        ma_columns = ['ma_7', 'ma_14', 'ma_30']
        for col in ma_columns:
            self.assertIn(col, btc_df.columns)
        
        # Check RSI
        self.assertIn('rsi_14', btc_df.columns)
        # RSI should be between 0 and 100
        self.assertTrue((btc_df['rsi_14'] >= 0).all())
        self.assertTrue((btc_df['rsi_14'] <= 100).all())
    
    def test_market_summary_structure(self):
        """Test market summary structure and content"""
        assets = ['bitcoin', 'ethereum', 'binancecoin']
        result = self.db.get_strategy_market_data(assets, days=30)
        
        market_summary = result['market_summary']
        
        # Check basic summary structure
        self.assertIn('assets_analyzed', market_summary)
        self.assertIn('assets_with_data', market_summary)
        self.assertIn('total_data_points', market_summary)
        self.assertIn('date_range', market_summary)
        self.assertIn('vix_summary', market_summary)
        self.assertIn('asset_summaries', market_summary)
        
        # Check asset counts
        self.assertEqual(market_summary['assets_analyzed'], 3)
        self.assertGreater(market_summary['assets_with_data'], 0)
        self.assertGreater(market_summary['total_data_points'], 0)
        
        # Check VIX summary
        vix_summary = market_summary['vix_summary']
        self.assertIn('current_vix', vix_summary)
        self.assertIn('average_vix', vix_summary)
        self.assertIn('max_vix', vix_summary)
        self.assertIn('min_vix', vix_summary)
        self.assertIn('vix_above_25_days', vix_summary)
        self.assertIn('vix_above_35_days', vix_summary)
        
        # Check asset summaries
        asset_summaries = market_summary['asset_summaries']
        for asset in assets:
            self.assertIn(asset, asset_summaries)
            if 'error' not in asset_summaries[asset]:
                asset_summary = asset_summaries[asset]
                self.assertIn('current_price', asset_summary)
                self.assertIn('current_drawdown_14d', asset_summary)
                self.assertIn('rsi_14', asset_summary)
                self.assertIn('volatility_14d', asset_summary)
    
    def test_drawdown_calculation_accuracy(self):
        """Test accuracy of drawdown calculations"""
        assets = ['bitcoin']
        result = self.db.get_strategy_market_data(assets, days=60)
        
        btc_df = result['bitcoin']
        self.assertFalse(btc_df.empty)
        
        # Check that rolling highs are indeed the maximum over their windows
        for i in range(7, len(btc_df)):
            window_high = btc_df['high'].iloc[i-6:i+1].max()
            calculated_high = btc_df['rolling_high_7d'].iloc[i]
            self.assertAlmostEqual(window_high, calculated_high, places=2)
        
        # Check drawdown calculation
        for i in range(len(btc_df)):
            if pd.notna(btc_df['rolling_high_7d'].iloc[i]):
                expected_drawdown = (btc_df['rolling_high_7d'].iloc[i] - btc_df['close'].iloc[i]) / btc_df['rolling_high_7d'].iloc[i]
                actual_drawdown = btc_df['drawdown_from_7d_high'].iloc[i]
                self.assertAlmostEqual(expected_drawdown, actual_drawdown, places=4)


if __name__ == '__main__':
    unittest.main() 