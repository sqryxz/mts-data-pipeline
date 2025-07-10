import unittest
import tempfile
import os
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.signals.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.data.signal_models import TradingSignal, SignalType, SignalStrength


class TestMeanReversionStrategy(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_config.write('''
        {
            "name": "Mean_Reversion_Strategy",
            "assets": ["bitcoin", "ethereum"],
            "vix_spike_threshold": 25,
            "drawdown_threshold": 0.10,
            "lookback_days": 14,
            "position_size": 0.025
        }
        ''')
        self.temp_config.close()
        
        # Create mock database
        self.mock_database = Mock()
        
    def tearDown(self):
        """Clean up test fixtures"""
        os.unlink(self.temp_config.name)
    
    def _create_mock_data_with_conditions(self, vix_level=30, drawdown_pct=0.15):
        """Create mock data with specific VIX spike and drawdown conditions"""
        dates = pd.date_range(start='2024-01-01', periods=14, freq='D')
        
        # Create price series with drawdown
        high_price = 50000
        # Start high, then decline to create drawdown
        prices = np.linspace(high_price, high_price * (1 - drawdown_pct), len(dates))
        # Add some noise
        prices = prices + np.random.normal(0, 100, len(dates))
        
        # Create VIX series with spike
        vix_values = np.full(len(dates), vix_level)
        # Add some variation
        vix_values = vix_values + np.random.normal(0, 2, len(dates))
        
        df = pd.DataFrame({
            'date_str': dates.strftime('%Y-%m-%d'),
            'timestamp': (dates.astype(np.int64) // 10**6).astype(int),
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.uniform(1000000, 5000000, len(dates)),
            'vix_value': vix_values,
            'fed_funds_rate': np.full(len(dates), 5.0),
            'treasury_10y_rate': np.full(len(dates), 4.0),
            'dollar_index': np.full(len(dates), 105.0)
        })
        
        return df
    
    def _create_mock_data_no_conditions(self):
        """Create mock data that doesn't meet mean reversion conditions"""
        dates = pd.date_range(start='2024-01-01', periods=14, freq='D')
        
        # Normal VIX levels (below threshold)
        vix_values = np.full(len(dates), 20.0) + np.random.normal(0, 2, len(dates))
        
        # Stable crypto prices (no significant drawdown)
        base_price = 50000
        prices = base_price + np.random.normal(0, 500, len(dates))
        
        df = pd.DataFrame({
            'date_str': dates.strftime('%Y-%m-%d'),
            'timestamp': (dates.astype(np.int64) // 10**6).astype(int),
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.uniform(1000000, 5000000, len(dates)),
            'vix_value': vix_values,
            'fed_funds_rate': np.full(len(dates), 5.0),
            'treasury_10y_rate': np.full(len(dates), 4.0),
            'dollar_index': np.full(len(dates), 105.0)
        })
        
        return df
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_strategy_initialization(self, mock_db_class):
        """Test strategy initialization with config"""
        mock_db_class.return_value = self.mock_database
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        
        self.assertEqual(strategy.assets, ["bitcoin", "ethereum"])
        self.assertEqual(strategy.vix_spike_threshold, 25)
        self.assertEqual(strategy.drawdown_threshold, 0.10)
        self.assertEqual(strategy.lookback_days, 14)
        self.assertEqual(strategy.position_size, 0.025)
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_analyze_with_mean_reversion_conditions(self, mock_db_class):
        """Test analysis with VIX spike and crypto drawdown (Task 5 requirement)"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with VIX=30 and crypto down 15% (as per task requirements)
        mock_data = self._create_mock_data_with_conditions(vix_level=30, drawdown_pct=0.15)
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        
        self.assertIn('market_analysis', analysis)
        self.assertIn('signal_opportunities', analysis)
        
        # Should have analysis for both assets
        self.assertEqual(len(analysis['market_analysis']), 2)
        
        # Check that conditions are met
        for asset in ['bitcoin', 'ethereum']:
            self.assertIn(asset, analysis['market_analysis'])
            asset_analysis = analysis['market_analysis'][asset]
            
            # Verify VIX spike detected
            self.assertTrue(asset_analysis['vix_spike_detected'])
            self.assertGreater(asset_analysis['current_vix'], 25)
            
            # Verify drawdown condition met
            self.assertTrue(asset_analysis['drawdown_condition_met'])
            self.assertGreater(asset_analysis['drawdown_from_high'], 0.10)
            
            # Verify overall criteria met
            self.assertTrue(asset_analysis['meets_criteria'])
        
        # Should find signal opportunities
        self.assertGreater(len(analysis['signal_opportunities']), 0)
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_generate_long_signals_when_conditions_met(self, mock_db_class):
        """Test generation of LONG signals when VIX>25 AND drawdown>10%"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data with mean reversion conditions
        mock_data = self._create_mock_data_with_conditions(vix_level=30, drawdown_pct=0.15)
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should generate LONG signals for assets meeting conditions
        self.assertGreater(len(signals), 0)
        
        for signal in signals:
            self.assertIsInstance(signal, TradingSignal)
            self.assertEqual(signal.signal_type, SignalType.LONG)  # Mean reversion always generates LONG
            self.assertIn(signal.asset, ["bitcoin", "ethereum"])
            self.assertGreater(signal.confidence, 0.0)
            self.assertLessEqual(signal.confidence, 1.0)
            
            # Check risk management parameters
            self.assertIsNotNone(signal.stop_loss)
            self.assertIsNotNone(signal.take_profit)
            self.assertLess(signal.stop_loss, signal.price)  # Stop loss below entry for LONG
            self.assertGreater(signal.take_profit, signal.price)  # Take profit above entry for LONG
            
            # Verify analysis data contains expected fields
            self.assertIn('vix_level', signal.analysis_data)
            self.assertIn('drawdown_from_high', signal.analysis_data)
            self.assertIn('price_rsi', signal.analysis_data)
            self.assertIn('vix_percentile', signal.analysis_data)
            
            # Verify VIX and drawdown conditions
            self.assertGreater(signal.analysis_data['vix_level'], 25)
            self.assertGreater(signal.analysis_data['drawdown_from_high'], 0.10)
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_no_signals_when_conditions_not_met(self, mock_db_class):
        """Test that no signals are generated when mean reversion conditions are not met"""
        mock_db_class.return_value = self.mock_database
        
        # Create mock data without mean reversion conditions
        mock_data = self._create_mock_data_no_conditions()
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Should not generate any signals when conditions are not met
        self.assertEqual(len(signals), 0)
        
        # Check that conditions are not met in analysis
        for asset in analysis['market_analysis']:
            asset_analysis = analysis['market_analysis'][asset]
            # Either VIX spike or drawdown condition (or both) should be false
            self.assertFalse(asset_analysis['meets_criteria'])
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_task_5_specific_conditions(self, mock_db_class):
        """Test specific Task 5 requirement: VIX=30 and crypto down 15%"""
        mock_db_class.return_value = self.mock_database
        
        # Create exact conditions from task requirements
        mock_data = self._create_mock_data_with_conditions(vix_level=30, drawdown_pct=0.15)
        self.mock_database.get_combined_analysis_data.return_value = mock_data
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        analysis = strategy.analyze({})
        signals = strategy.generate_signals(analysis)
        
        # Verify LONG signals are generated as per task requirements
        self.assertGreater(len(signals), 0, "Should generate LONG signals with VIX=30 and crypto down 15%")
        
        for signal in signals:
            self.assertEqual(signal.signal_type, SignalType.LONG, "Should generate LONG signals for mean reversion")
            self.assertGreaterEqual(signal.analysis_data['vix_level'], 25, "VIX should be above threshold")
            self.assertGreaterEqual(signal.analysis_data['drawdown_from_high'], 0.10, "Drawdown should be above threshold")
    
    @patch('src.signals.strategies.mean_reversion_strategy.CryptoDatabase')
    def test_get_parameters(self, mock_db_class):
        """Test get_parameters method"""
        mock_db_class.return_value = self.mock_database
        
        strategy = MeanReversionStrategy(self.temp_config.name)
        params = strategy.get_parameters()
        
        self.assertIn('strategy_name', params)
        self.assertIn('assets', params)
        self.assertIn('vix_spike_threshold', params)
        self.assertIn('drawdown_threshold', params)
        self.assertIn('lookback_days', params)
        self.assertIn('position_size', params)
        
        self.assertEqual(params['assets'], ["bitcoin", "ethereum"])
        self.assertEqual(params['vix_spike_threshold'], 25)
        self.assertEqual(params['drawdown_threshold'], 0.10)


if __name__ == '__main__':
    unittest.main() 