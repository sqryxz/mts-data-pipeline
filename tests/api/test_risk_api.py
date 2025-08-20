"""
API tests for the Risk Management Module.

This module tests the Flask API endpoints for the risk management system.
"""

import unittest
import json
import requests
from datetime import datetime
from unittest.mock import patch

# Import the API module
from src.risk_management.api.risk_api import app


class TestRiskAPI(unittest.TestCase):
    """Test the Risk Management API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Test data
        self.valid_signal = {
            "signal_id": "api-test-1",
            "asset": "BTC",
            "signal_type": "LONG",
            "price": 50000.0,
            "confidence": 0.8,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        self.valid_portfolio = {
            "total_equity": 10000.0,
            "current_drawdown": 0.05,
            "daily_pnl": 100.0,
            "positions": {"BTC": 0.1},
            "cash": 9000.0
        }
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.app.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'risk-management')
        self.assertIn('timestamp', data)
    
    def test_assess_risk_valid_request(self):
        """Test risk assessment with valid request."""
        request_data = {
            "signal": self.valid_signal,
            "portfolio_state": self.valid_portfolio
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('assessment', data)
        
        assessment = data['assessment']
        self.assertEqual(assessment['signal_id'], 'api-test-1')
        self.assertEqual(assessment['asset'], 'BTC')
        self.assertEqual(assessment['signal_type'], 'LONG')
        self.assertEqual(assessment['signal_price'], 50000.0)
        self.assertEqual(assessment['signal_confidence'], 0.8)
        self.assertGreater(assessment['recommended_position_size'], 0)
        self.assertGreater(assessment['stop_loss_price'], 0)
        self.assertGreater(assessment['take_profit_price'], 0)
        self.assertGreater(assessment['risk_reward_ratio'], 0)
        self.assertIn('risk_level', assessment)
        self.assertIsInstance(assessment['is_approved'], bool)
        self.assertIsInstance(assessment['risk_warnings'], list)
    
    def test_assess_risk_short_signal(self):
        """Test risk assessment with SHORT signal."""
        short_signal = self.valid_signal.copy()
        short_signal['signal_type'] = 'SHORT'
        
        request_data = {
            "signal": short_signal,
            "portfolio_state": self.valid_portfolio
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        assessment = data['assessment']
        self.assertEqual(assessment['signal_type'], 'SHORT')
        self.assertEqual(assessment['signal_price'], 50000.0)
    
    def test_assess_risk_invalid_signal_type(self):
        """Test risk assessment with invalid signal type."""
        invalid_signal = self.valid_signal.copy()
        invalid_signal['signal_type'] = 'INVALID_TYPE'
        
        request_data = {
            "signal": invalid_signal,
            "portfolio_state": self.valid_portfolio
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Invalid signal_type', data['error'])
    
    def test_assess_risk_invalid_price(self):
        """Test risk assessment with invalid price."""
        invalid_signal = self.valid_signal.copy()
        invalid_signal['price'] = 'not_a_number'
        
        request_data = {
            "signal": invalid_signal,
            "portfolio_state": self.valid_portfolio
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Invalid price', data['error'])
    
    def test_assess_risk_missing_signal(self):
        """Test risk assessment with missing signal."""
        request_data = {
            "portfolio_state": self.valid_portfolio
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_assess_risk_missing_portfolio(self):
        """Test risk assessment with missing portfolio."""
        request_data = {
            "signal": self.valid_signal
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_assess_risk_invalid_json(self):
        """Test risk assessment with invalid JSON."""
        response = self.app.post(
            '/assess-risk',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_get_config(self):
        """Test getting configuration."""
        response = self.app.get('/config')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('config', data)
        
        config = data['config']
        self.assertIn('risk_limits', config)
        self.assertIn('position_sizing', config)
        self.assertIn('risk_assessment', config)
    
    def test_update_config_valid(self):
        """Test updating configuration with valid data."""
        new_config = {
            "risk_limits": {
                "max_drawdown_limit": 0.15,
                "daily_loss_limit": 0.03
            }
        }
        
        response = self.app.post(
            '/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('message', data)
    
    def test_update_config_invalid(self):
        """Test updating configuration with invalid data."""
        invalid_config = {
            "risk_limits": {
                "max_drawdown_limit": "not_a_number"
            }
        }
        
        response = self.app.post(
            '/config',
            data=json.dumps(invalid_config),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_assess_risk_different_assets(self):
        """Test risk assessment with different assets."""
        assets = ["BTC", "ETH", "ADA", "SOL"]
        
        for asset in assets:
            signal = self.valid_signal.copy()
            signal['asset'] = asset
            signal['signal_id'] = f"api-test-{asset}"
            
            request_data = {
                "signal": signal,
                "portfolio_state": self.valid_portfolio
            }
            
            response = self.app.post(
                '/assess-risk',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            assessment = data['assessment']
            self.assertEqual(assessment['asset'], asset)
    
    def test_assess_risk_confidence_range(self):
        """Test risk assessment with different confidence levels."""
        confidence_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for confidence in confidence_levels:
            signal = self.valid_signal.copy()
            signal['confidence'] = confidence
            signal['signal_id'] = f"api-test-conf-{confidence}"
            
            request_data = {
                "signal": signal,
                "portfolio_state": self.valid_portfolio
            }
            
            response = self.app.post(
                '/assess-risk',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            assessment = data['assessment']
            self.assertEqual(assessment['signal_confidence'], confidence)
    
    def test_assess_risk_portfolio_scenarios(self):
        """Test risk assessment with different portfolio scenarios."""
        scenarios = [
            # (portfolio_state, expected_risk_levels)
            (
                {"total_equity": 10000.0, "current_drawdown": 0.02, "daily_pnl": 200.0},
                ["LOW", "MEDIUM"]
            ),
            (
                {"total_equity": 10000.0, "current_drawdown": 0.10, "daily_pnl": -100.0},
                ["MEDIUM", "HIGH"]
            ),
            (
                {"total_equity": 10000.0, "current_drawdown": 0.18, "daily_pnl": -500.0},
                ["HIGH", "CRITICAL"]
            )
        ]
        
        for portfolio_state, expected_levels in scenarios:
            request_data = {
                "signal": self.valid_signal,
                "portfolio_state": portfolio_state
            }
            
            response = self.app.post(
                '/assess-risk',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            assessment = data['assessment']
            self.assertIn(assessment['risk_level'], expected_levels)
    
    def test_error_handling_malformed_request(self):
        """Test error handling for malformed requests."""
        # Test with empty request
        response = self.app.post(
            '/assess-risk',
            data='{}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        
        # Test with missing required fields
        incomplete_request = {
            "signal": {"signal_id": "test"}
        }
        
        response = self.app.post(
            '/assess-risk',
            data=json.dumps(incomplete_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
    
    def test_timestamp_parsing(self):
        """Test timestamp parsing with different formats."""
        timestamp_formats = [
            "2024-01-01T12:00:00Z",
            "2024-01-01T12:00:00",
            "2024-01-01 12:00:00"
        ]
        
        for timestamp in timestamp_formats:
            signal = self.valid_signal.copy()
            signal['timestamp'] = timestamp
            signal['signal_id'] = f"api-test-{timestamp}"
            
            request_data = {
                "signal": signal,
                "portfolio_state": self.valid_portfolio
            }
            
            response = self.app.post(
                '/assess-risk',
                data=json.dumps(request_data),
                content_type='application/json'
            )
            
            # Should handle timestamp parsing gracefully
            self.assertIn(response.status_code, [200, 400])


if __name__ == '__main__':
    unittest.main() 