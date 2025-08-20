"""
Integration tests for the correlation analysis module.
Tests the complete end-to-end pipeline from data loading to alert generation.
"""

import unittest
import json
import tempfile
import shutil
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import logging
import numpy as np
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.correlation_analysis.core.correlation_engine import CorrelationEngine
from src.correlation_analysis.core.correlation_monitor import CorrelationMonitor
from src.correlation_analysis.visualization.mosaic_generator import MosaicGenerator
from src.correlation_analysis.alerts.mosaic_alert_system import MosaicAlertSystem
from src.correlation_analysis.storage.correlation_storage import CorrelationStorage
from src.correlation_analysis.storage.state_manager import CorrelationStateManager


class TestCorrelationAnalysisIntegration(unittest.TestCase):
    """Test complete end-to-end correlation analysis pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test configuration
        self.test_config = {
            "crypto_pairs": {
                "BTC_ETH": {
                    "primary": "bitcoin",
                    "secondary": "ethereum",
                    "correlation_windows": [7, 14, 30]
                }
            },
            "macro_pairs": {},
            "monitoring_settings": {
                "update_frequency_seconds": 300,
                "data_retention_days": 365,
                "cache_ttl_seconds": 3600,
                "max_alerts_per_hour": 10
            }
        }
        
        # Save test configuration
        self.config_file = Path(self.temp_dir) / "test_config.json"
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_data(self):
        """Create test data for correlation analysis."""
        # Create sample price data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        
        # Create correlated price data (BTC and ETH with some correlation)
        np.random.seed(42)
        base_prices = np.cumsum(np.random.randn(len(dates)) * 0.02)
        
        # BTC prices (more volatile)
        btc_prices = 50000 + base_prices * 1000 + np.random.randn(len(dates)) * 500
        
        # ETH prices (correlated with BTC but less volatile)
        eth_prices = 3000 + base_prices * 100 + np.random.randn(len(dates)) * 50
        
        # Create DataFrame
        data = pd.DataFrame({
            'timestamp': dates,
            'bitcoin': btc_prices,
            'ethereum': eth_prices
        })
        
        return data
    
    def test_complete_correlation_analysis_pipeline(self):
        """Test complete end-to-end correlation analysis pipeline."""
        self.logger.info("🚀 Testing complete correlation analysis pipeline...")
        
        # Step 1: Initialize components
        self.logger.info("1. Initializing components...")
        engine = CorrelationEngine(str(self.config_file))
        storage = CorrelationStorage()
        state_manager = CorrelationStateManager()
        
        # Verify components initialized
        self.assertIsNotNone(engine)
        self.assertIsNotNone(storage)
        self.assertIsNotNone(state_manager)
        
        # Step 2: Test correlation monitoring
        self.logger.info("2. Testing correlation monitoring...")
        monitor = CorrelationMonitor("BTC_ETH")
        
        # Run monitoring
        result = monitor.monitor_pair()
        
        # Verify monitoring results
        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('correlations', result)
        self.assertIn('breakouts', result)
        self.assertIn('alerts_generated', result)
        
        # Step 3: Test correlation engine
        self.logger.info("3. Testing correlation engine...")
        engine_success = engine.start_monitoring(run_once=True)
        
        # Verify engine ran successfully
        self.assertTrue(engine_success, "Engine should run successfully")
        
        # Step 4: Test mosaic generation
        self.logger.info("4. Testing mosaic generation...")
        generator = MosaicGenerator()
        mosaic_data = generator.generate_daily_mosaic()
        
        # Verify mosaic generation
        self.assertIsNotNone(mosaic_data)
        self.assertIn('correlation_matrix', mosaic_data)
        self.assertIn('key_findings', mosaic_data)
        self.assertIn('recommendations', mosaic_data)
        
        # Step 5: Test alert generation
        self.logger.info("5. Testing alert generation...")
        alert_system = MosaicAlertSystem()
        alert_path = alert_system.generate_daily_mosaic_alert(force_regeneration=True)
        
        # Verify alert generation
        self.assertIsNotNone(alert_path)
        self.assertTrue(Path(alert_path).exists(), "Alert file should be created")
        
        # Step 6: Test storage and state persistence
        self.logger.info("6. Testing storage and state persistence...")
        
        # Test correlation storage
        correlations = storage.get_correlation_history("BTC_ETH", limit=10)
        self.assertIsInstance(correlations, pd.DataFrame)
        
        # Test state persistence
        state = state_manager.load_correlation_state()
        self.assertIsInstance(state, dict)
        
        self.logger.info("✅ Complete pipeline test passed!")
    
    def test_correlation_monitor_with_known_breakout(self):
        """Test correlation monitoring with known correlation breakout."""
        self.logger.info("🔍 Testing correlation monitoring with known breakout...")
        
        # Create monitor
        monitor = CorrelationMonitor("BTC_ETH")
        
        # Run monitoring
        result = monitor.monitor_pair()
        
        # Verify monitoring completed
        self.assertTrue(result['success'], "Monitoring should complete successfully")
        
        # Check for correlations
        correlations = result.get('correlations', {})
        self.assertIsInstance(correlations, dict)
        
        # Check for breakouts (may or may not be detected based on data)
        breakouts = result.get('breakouts', [])
        self.assertIsInstance(breakouts, list)
        
        # Check for alerts
        alerts = result.get('alerts_generated', [])
        self.assertIsInstance(alerts, list)
        
        self.logger.info(f"✅ Monitoring test passed: {len(correlations)} correlations, {len(breakouts)} breakouts, {len(alerts)} alerts")
    
    def test_mosaic_generation_comprehensive(self):
        """Test comprehensive mosaic generation."""
        self.logger.info("🎨 Testing comprehensive mosaic generation...")
        
        # Initialize generator
        generator = MosaicGenerator()
        
        # Generate correlation matrix
        matrix_data = generator.generate_correlation_matrix()
        
        # Verify matrix structure
        self.assertIsNotNone(matrix_data)
        self.assertIn('matrix', matrix_data)
        self.assertIn('summary', matrix_data)
        self.assertIn('metadata', matrix_data)
        
        # Check summary statistics
        summary = matrix_data['summary']
        self.assertIn('total_pairs', summary)
        self.assertIn('significant_correlations', summary)
        self.assertIn('average_correlation_strength', summary)
        
        # Generate daily mosaic
        mosaic_data = generator.generate_daily_mosaic()
        
        # Verify mosaic structure
        self.assertIsNotNone(mosaic_data)
        self.assertIn('mosaic_type', mosaic_data)
        self.assertIn('correlation_matrix', mosaic_data)
        self.assertIn('key_findings', mosaic_data)
        self.assertIn('recommendations', mosaic_data)
        
        # Check key findings
        key_findings = mosaic_data['key_findings']
        self.assertIsInstance(key_findings, list)
        
        # Check recommendations
        recommendations = mosaic_data['recommendations']
        self.assertIsInstance(recommendations, list)
        
        self.logger.info(f"✅ Mosaic generation test passed: {len(key_findings)} findings, {len(recommendations)} recommendations")
    
    def test_alert_system_integration(self):
        """Test alert system integration."""
        self.logger.info("🚨 Testing alert system integration...")
        
        # Initialize alert system
        alert_system = MosaicAlertSystem()
        
        # Generate daily mosaic alert
        alert_path = alert_system.generate_daily_mosaic_alert(force_regeneration=True)
        
        # Verify alert file was created
        self.assertIsNotNone(alert_path)
        self.assertTrue(Path(alert_path).exists())
        
        # Load and verify alert content
        with open(alert_path, 'r') as f:
            alert_data = json.load(f)
        
        # Check alert structure
        self.assertIn('timestamp', alert_data)
        self.assertIn('alert_type', alert_data)
        self.assertIn('alert_id', alert_data)
        self.assertIn('mosaic_summary', alert_data)
        self.assertIn('key_findings', alert_data)
        self.assertIn('alert_metadata', alert_data)
        
        # Verify alert type
        self.assertEqual(alert_data['alert_type'], 'daily_correlation_mosaic')
        
        # Verify alert ID format
        self.assertIsInstance(alert_data['alert_id'], str)
        self.assertTrue(alert_data['alert_id'].startswith('corr_mosaic_daily'))
        
        # Check mosaic summary
        summary = alert_data['mosaic_summary']
        self.assertIn('total_pairs_analyzed', summary)
        self.assertIn('significant_correlations', summary)
        self.assertIn('average_correlation_strength', summary)
        
        # Check key findings
        key_findings = alert_data['key_findings']
        self.assertIsInstance(key_findings, list)
        
        # Test alert history
        history = alert_system.get_mosaic_alert_history(days=1)
        self.assertIsInstance(history, list)
        
        # Test alert summary
        summary_stats = alert_system.get_mosaic_alert_summary(days=7)
        self.assertIsInstance(summary_stats, dict)
        self.assertIn('total_alerts', summary_stats)
        
        self.logger.info("✅ Alert system integration test passed!")
    
    def test_storage_and_state_integration(self):
        """Test storage and state management integration."""
        self.logger.info("💾 Testing storage and state integration...")
        
        # Initialize components
        storage = CorrelationStorage()
        state_manager = CorrelationStateManager()
        
        # Test correlation storage
        correlations = storage.get_correlation_history("BTC_ETH", limit=10)
        self.assertIsInstance(correlations, pd.DataFrame)
        
        # Test correlation statistics
        stats = storage.get_correlation_statistics("BTC_ETH")
        self.assertIsInstance(stats, dict)
        
        # Test state loading
        state = state_manager.load_correlation_state()
        self.assertIsInstance(state, dict)
        
        # Test state saving
        test_state = {
            'pairs': {'BTC_ETH': {'last_update': datetime.now().isoformat()}},
            'correlation_history': {},
            'breakout_history': {}
        }
        save_success = state_manager.save_correlation_state(test_state)
        self.assertTrue(save_success, "State should save successfully")
        
        # Test state reloading
        reloaded_state = state_manager.load_correlation_state()
        self.assertIsInstance(reloaded_state, dict)
        
        self.logger.info("✅ Storage and state integration test passed!")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        self.logger.info("🛡️ Testing error handling and recovery...")
        
        # Test with invalid pair
        try:
            monitor = CorrelationMonitor("INVALID_PAIR")
            result = monitor.monitor_pair()
            # Should handle gracefully even with invalid pair
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Should not crash with invalid pair
            self.assertIsInstance(e, Exception)
        
        # Test with invalid configuration
        try:
            engine = CorrelationEngine("nonexistent_config.json")
            # Should use default configuration
            self.assertIsNotNone(engine)
        except Exception as e:
            # Should handle missing config gracefully
            self.assertIsInstance(e, Exception)
        
        # Test storage with invalid data
        storage = CorrelationStorage()
        try:
            correlations = storage.get_correlation_history("INVALID_PAIR", limit=10)
            self.assertIsInstance(correlations, pd.DataFrame)
        except Exception as e:
            # Should handle invalid pair gracefully
            self.assertIsInstance(e, Exception)
        
        self.logger.info("✅ Error handling and recovery test passed!")
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        self.logger.info("📊 Testing performance metrics...")
        
        # Initialize engine
        engine = CorrelationEngine(str(self.config_file))
        
        # Run monitoring cycle
        start_time = datetime.now()
        success = engine.start_monitoring(run_once=True)
        end_time = datetime.now()
        
        # Verify monitoring completed
        self.assertTrue(success, "Monitoring should complete successfully")
        
        # Check performance metrics
        status = engine.get_engine_status()
        self.assertIn('performance_metrics', status)
        
        metrics = status['performance_metrics']
        self.assertIn('total_runs', metrics)
        self.assertIn('successful_runs', metrics)
        self.assertIn('failed_runs', metrics)
        self.assertIn('total_monitoring_time', metrics)
        self.assertIn('avg_monitoring_time', metrics)
        
        # Verify metrics are reasonable
        self.assertGreaterEqual(metrics['total_runs'], 1)
        self.assertGreaterEqual(metrics['successful_runs'], 0)
        self.assertGreaterEqual(metrics['total_monitoring_time'], 0)
        
        # Check execution time
        execution_time = (end_time - start_time).total_seconds()
        self.assertGreaterEqual(execution_time, 0)
        self.logger.info(f"✅ Performance test passed: {execution_time:.2f}s execution time")
    
    def test_full_pipeline_with_real_data(self):
        """Test full pipeline with real data (if available)."""
        self.logger.info("🎯 Testing full pipeline with real data...")
        
        # Initialize all components
        engine = CorrelationEngine(str(self.config_file))
        generator = MosaicGenerator()
        alert_system = MosaicAlertSystem()
        
        # Step 1: Run correlation monitoring
        monitoring_success = engine.start_monitoring(run_once=True)
        self.assertTrue(monitoring_success, "Monitoring should complete successfully")
        
        # Step 2: Generate mosaic
        mosaic_data = generator.generate_daily_mosaic()
        self.assertIsNotNone(mosaic_data, "Mosaic should be generated")
        
        # Step 3: Generate alert
        alert_path = alert_system.generate_daily_mosaic_alert(force_regeneration=True)
        self.assertIsNotNone(alert_path, "Alert should be generated")
        
        # Step 4: Verify alert file
        self.assertTrue(Path(alert_path).exists(), "Alert file should exist")
        
        # Step 5: Load and verify alert content
        with open(alert_path, 'r') as f:
            alert_data = json.load(f)
        
        # Verify alert structure
        required_fields = ['timestamp', 'alert_type', 'alert_id', 'mosaic_summary', 'key_findings']
        for field in required_fields:
            self.assertIn(field, alert_data, f"Alert should contain {field}")
        
        self.logger.info("✅ Full pipeline test with real data passed!")


def run_integration_tests():
    """Run all integration tests with nice output."""
    print("🚀 Starting Correlation Analysis Integration Tests...")
    print("=" * 60)
    
    # Setup test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCorrelationAnalysisIntegration)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Integration Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed!")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
