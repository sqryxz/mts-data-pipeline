import unittest
import tempfile
import os
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.signals.strategies.vix_correlation_strategy import VIXCorrelationStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength


class TestVIXCorrelationStrategy(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write('''
        {
            "name": "VIX_Correlation_Strategy",
            "assets": ["bitcoin", "ethereum"],
            "correlation_thresholds": {
                "strong_negative": -0.6,
                "strong_positive": 0.6
            },
            "lookback_days": 30,
            "position_size": 0.02
        }
        ''')
        self.temp_config.close()
        
        # Create mock database
        self.mock_database = Mock()
        
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_config.name)
    
    def _create_mock_data(self, correlation_type='negative'):
        """Create mock data with specific correlation patterns"""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        
        if correlation_type == 'negative':
            # Strong negative correlation: when VIX goes up, crypto goes down
            vix_values = np.random.normal(20, 5, 30)
            crypto_prices = 50000 - (vix_values - 20) * 1000 + np.random.normal(0, 500, 30)
        elif correlation_type == 'positive':
            # Strong positive correlation: when VIX goes up, crypto goes up
            vix_values = np.random.normal(20, 5, 30)
            crypto_prices = 50000 + (vix_values - 20) * 1000 + np.random.normal(0, 500, 30)
        else:  # no correlation
            vix_values = np.random.normal(20, 5, 30)
            crypto_prices = np.random.normal(50000, 2000, 30)
        
        df = pd.DataFrame({
            'date_str': dates.strftime('%Y-%m-%d'),
            'timestamp': (dates.astype(np.int64) // 10**6).astype(int),
            'open': crypto_prices * 0.99,
            'high': crypto_prices * 1.01,
            'low': crypto_prices * 0.98,
            'close': crypto_prices,
            'volume': np.random.uniform(1000000, 5000000, 30),
            'vix_value': vix_values,
            'fed_funds_rate': np.full(30, 5.0),
            'treasury_10y_rate': np.full(30, 4.0),
            'dollar_index': np.full(30, 105.0)
        })
        
        return df
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_strategy_initialization(self, mock_db_class):
        """Test strategy initialization with config"""
        mock_db_class.return_value = self.mock_database
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        
        self.assertEqual(strategy.assets, ["bitcoin", "ethereum"])
        self.assertEqual(strategy.correlation_thresholds['strong_negative'], -0.6)
        self.assertEqual(strategy.correlation_thresholds['strong_positive'], 0.6)
        self.assertEqual(strategy.lookback_days, 30)
        self.assertEqual(strategy.position_size, 0.02)
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_analyze_with_negative_correlation(self, mock_db_class):
        """Test analysis with strong negative correlation"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with strong negative correlation
        mock_data = self._create_mock_data('negative')
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        
        self.assertIn('correlation_analysis', analysis)
        self.assertIn('signal_opportunities', analysis)
        
        # Should have analysis for both assets
        self.assertEqual(len(analysis['correlation_analysis']), 2)
        
        # Check that correlations were calculated
        for asset in ['bitcoin', 'ethereum']:
            self.assertIn(asset, analysis['correlation_analysis'])
            asset_analysis = analysis['correlation_analysis'][asset]
            self.assertIsNotNone(asset_analysis['current_correlation'])
            self.assertLess(asset_analysis['current_correlation'], -0.5)  # Should be negative
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_analyze_with_positive_correlation(self, mock_db_class):
        """Test analysis with strong positive correlation"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with strong positive correlation
        mock_data = self._create_mock_data('positive')
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        
        # Check that positive correlations were detected
        for asset in ['bitcoin', 'ethereum']:
            if asset in analysis['correlation_analysis']:
                asset_analysis = analysis['correlation_analysis'][asset]
                if asset_analysis['current_correlation'] is not None:
                    self.assertGreater(asset_analysis['current_correlation'], 0.5)
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_generate_long_signals(self, mock_db_class):
        """Test generation of LONG signals from negative correlation"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with strong negative correlation
        mock_data = self._create_mock_data('negative')
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should generate signals for assets with strong negative correlation
        self.assertGreater(len(signals), 0)
        
        for signal in signals:
            self.assertIsInstance(signal, TradingSignal)
            self.assertEqual(signal.signal_type, SignalType.LONG)
            self.assertIn(signal.asset, ["bitcoin", "ethereum"])
            self.assertIsNotNone(signal.correlation_value)
            self.assertLess(signal.correlation_value, -0.6)  # Strong negative correlation
            self.assertGreater(signal.confidence, 0.0)
            self.assertLessEqual(signal.confidence, 1.0)
            
            # Check risk management parameters
            self.assertIsNotNone(signal.stop_loss)
            self.assertIsNotNone(signal.take_profit)
            self.assertLess(signal.stop_loss, signal.price)  # Stop loss below entry for LONG
            self.assertGreater(signal.take_profit, signal.price)  # Take profit above entry for LONG
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_generate_short_signals(self, mock_db_class):
        """Test generation of SHORT signals from positive correlation"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with strong positive correlation
        mock_data = self._create_mock_data('positive')
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should generate signals for assets with strong positive correlation
        for signal in signals:
            if signal.signal_type == SignalType.SHORT:
                self.assertIsInstance(signal, TradingSignal)
                self.assertIn(signal.asset, ["bitcoin", "ethereum"])
                self.assertIsNotNone(signal.correlation_value)
                self.assertGreater(signal.correlation_value, 0.6)  # Strong positive correlation
                
                # Check risk management for SHORT signals
                self.assertIsNotNone(signal.stop_loss)
                self.assertIsNotNone(signal.take_profit)
                self.assertGreater(signal.stop_loss, signal.price)  # Stop loss above entry for SHORT
                self.assertLess(signal.take_profit, signal.price)  # Take profit below entry for SHORT
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_no_signals_with_weak_correlation(self, mock_db_class):
        """Test that no signals are generated with weak correlation"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with no correlation
        mock_data = self._create_mock_data('none')
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should not generate any signals with weak correlation
        self.assertEqual(len(signals), 0)
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_handle_missing_data(self, mock_db_class):
        """Test handling of missing VIX data"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with missing VIX values
        mock_data = self._create_mock_data('negative')
        mock_data['vix_value'] = np.nan  # All VIX data missing
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should handle missing data gracefully
        self.assertEqual(len(signals), 0)
        
        # Check that analysis indicates insufficient data
        for asset in analysis['correlation_analysis']:
            asset_analysis = analysis['correlation_analysis'][asset]
            self.assertEqual(asset_analysis['correlation_strength'], 'INSUFFICIENT_DATA')
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_vix_adjustment_factor(self, mock_db_class):
        """Test that position size is adjusted based on VIX level"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with high VIX (should reduce position size)
        mock_data = self._create_mock_data('negative')
        mock_data['vix_value'] = 50.0  # High VIX level
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Position size should be adjusted down due to high VIX
        for signal in signals:
            self.assertLess(signal.position_size, strategy.position_size)
            self.assertIn('vix_adjustment_factor', signal.analysis_data)
            self.assertLess(signal.analysis_data['vix_adjustment_factor'], 1.0)
    
    @patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase')
    def test_get_parameters(self, mock_db_class):
        """Test get_parameters method"""
        mock_db_class.return_value = self.mock_database
        
        strategy = VIXCorrelationStrategy(self.temp_config.name)
        params = strategy.get_parameters()
        
        self.assertIn('strategy_name', params)
        self.assertIn('assets', params)
        self.assertIn('correlation_thresholds', params)
        self.assertIn('lookback_days', params)
        self.assertIn('position_size', params)
        self.assertIn('version', params)
        
        self.assertEqual(params['assets'], ["bitcoin", "ethereum"])
        self.assertEqual(params['lookback_days'], 30)
    
    def test_correlation_strength_classification(self):
        """Test correlation strength classification"""
        # Create strategy for testing helper method
        with patch('src.signals.strategies.vix_correlation_strategy.CryptoDatabase'):
            strategy = VIXCorrelationStrategy(self.temp_config.name)
        
        # Test different correlation values
        self.assertEqual(strategy._classify_correlation_strength(0.8), 'VERY_STRONG')
        self.assertEqual(strategy._classify_correlation_strength(-0.7), 'VERY_STRONG')
        self.assertEqual(strategy._classify_correlation_strength(0.6), 'STRONG')
        self.assertEqual(strategy._classify_correlation_strength(-0.5), 'STRONG')
        self.assertEqual(strategy._classify_correlation_strength(0.4), 'MODERATE')
        self.assertEqual(strategy._classify_correlation_strength(0.2), 'WEAK')
        self.assertEqual(strategy._classify_correlation_strength(0.05), 'NEGLIGIBLE')
        self.assertEqual(strategy._classify_correlation_strength(None), 'INSUFFICIENT_DATA')
        self.assertEqual(strategy._classify_correlation_strength(np.nan), 'INSUFFICIENT_DATA')


if __name__ == '__main__':
    unittest.main() 