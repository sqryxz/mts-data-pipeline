"""
Integration tests for the Risk Management Module.

This module tests the complete risk assessment flow and
integration between all components.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime

from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, SignalType
)
from src.risk_management.core.risk_orchestrator import RiskOrchestrator


class TestRiskManagementIntegration(unittest.TestCase):
    """Test the complete risk management integration flow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = RiskOrchestrator()
        
        # Create test signal
        self.test_signal = TradingSignal(
            signal_id="integration-test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        # Create test portfolio
        self.test_portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.05,
            daily_pnl=100.0,
            positions={"BTC": 0.1},
            cash=9000.0,
            timestamp=datetime.now()
        )
    
    def test_complete_risk_assessment_flow(self):
        """Test the complete risk assessment flow."""
        # Perform risk assessment
        assessment = self.orchestrator.assess_trade_risk(self.test_signal, self.test_portfolio)
        
        # Verify assessment structure
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.signal_id, "integration-test-1")
        self.assertEqual(assessment.asset, "BTC")
        self.assertEqual(assessment.signal_type, SignalType.LONG)
        self.assertEqual(assessment.signal_price, 50000.0)
        self.assertEqual(assessment.signal_confidence, 0.8)
        
        # Verify position sizing
        self.assertGreater(assessment.recommended_position_size, 0)
        self.assertIsInstance(assessment.position_size_method, str)
        
        # Verify risk management
        self.assertGreater(assessment.stop_loss_price, 0)
        self.assertGreater(assessment.take_profit_price, 0)
        self.assertGreater(assessment.risk_reward_ratio, 0)
        
        # Verify risk metrics
        self.assertGreaterEqual(assessment.position_risk_percent, 0)
        self.assertGreaterEqual(assessment.portfolio_heat, 0)
        
        # Verify validation results
        self.assertIsInstance(assessment.is_approved, bool)
        self.assertIsInstance(assessment.risk_warnings, list)
        
        # Verify risk level
        self.assertIsNotNone(assessment.risk_level)
        
        # Verify processing metadata
        self.assertGreaterEqual(assessment.processing_time_ms, 0)
    
    def test_low_risk_scenario(self):
        """Test risk assessment for low risk scenario."""
        # Create low risk portfolio
        low_risk_portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.02,  # Low drawdown
            daily_pnl=200.0,        # Positive P&L
            positions={"BTC": 0.05}, # Small position
            cash=9500.0
        )
        
        assessment = self.orchestrator.assess_trade_risk(self.test_signal, low_risk_portfolio)
        
        # Should be approved and low risk
        self.assertTrue(assessment.is_approved)
        self.assertIn(assessment.risk_level.value, ["LOW", "MEDIUM"])
        self.assertEqual(len(assessment.risk_warnings), 0)
    
    def test_high_risk_scenario(self):
        """Test risk assessment for high risk scenario."""
        # Create high risk portfolio
        high_risk_portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.15,  # High drawdown
            daily_pnl=-300.0,       # Negative P&L
            positions={"BTC": 0.2},  # Large position
            cash=8000.0
        )
        
        assessment = self.orchestrator.assess_trade_risk(self.test_signal, high_risk_portfolio)
        
        # Should have higher risk level
        self.assertIn(assessment.risk_level.value, ["HIGH", "CRITICAL"])
        self.assertGreater(len(assessment.risk_warnings), 0)
    
    def test_short_signal_assessment(self):
        """Test risk assessment for SHORT signal."""
        short_signal = TradingSignal(
            signal_id="integration-test-short",
            asset="BTC",
            signal_type=SignalType.SHORT,
            price=50000.0,
            confidence=0.7,
            timestamp=datetime.now()
        )
        
        assessment = self.orchestrator.assess_trade_risk(short_signal, self.test_portfolio)
        
        # Verify SHORT signal handling
        self.assertEqual(assessment.signal_type, SignalType.SHORT)
        self.assertEqual(assessment.signal_price, 50000.0)
        self.assertEqual(assessment.signal_confidence, 0.7)
        
        # For SHORT, stop loss should be above entry price
        self.assertGreater(assessment.stop_loss_price, short_signal.price)
    
    def test_different_assets(self):
        """Test risk assessment for different assets."""
        eth_signal = TradingSignal(
            signal_id="integration-test-eth",
            asset="ETH",
            signal_type=SignalType.LONG,
            price=3000.0,
            confidence=0.6,
            timestamp=datetime.now()
        )
        
        assessment = self.orchestrator.assess_trade_risk(eth_signal, self.test_portfolio)
        
        # Verify different asset handling
        self.assertEqual(assessment.asset, "ETH")
        self.assertEqual(assessment.signal_price, 3000.0)
        self.assertEqual(assessment.signal_confidence, 0.6)
    
    def test_confidence_impact(self):
        """Test how confidence affects position sizing."""
        # High confidence signal
        high_confidence_signal = TradingSignal(
            signal_id="integration-test-high-conf",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.9,
            timestamp=datetime.now()
        )
        
        high_conf_assessment = self.orchestrator.assess_trade_risk(high_confidence_signal, self.test_portfolio)
        
        # Low confidence signal
        low_confidence_signal = TradingSignal(
            signal_id="integration-test-low-conf",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.3,
            timestamp=datetime.now()
        )
        
        low_conf_assessment = self.orchestrator.assess_trade_risk(low_confidence_signal, self.test_portfolio)
        
        # Higher confidence should result in larger position
        self.assertGreater(
            high_conf_assessment.recommended_position_size,
            low_conf_assessment.recommended_position_size
        )
    
    def test_portfolio_size_impact(self):
        """Test how portfolio size affects position sizing."""
        # Large portfolio
        large_portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=1000.0,
            positions={"BTC": 0.1},
            cash=90000.0
        )
        
        large_assessment = self.orchestrator.assess_trade_risk(self.test_signal, large_portfolio)
        
        # Small portfolio
        small_portfolio = PortfolioState(
            total_equity=1000.0,
            current_drawdown=0.05,
            daily_pnl=10.0,
            positions={"BTC": 0.1},
            cash=900.0
        )
        
        small_assessment = self.orchestrator.assess_trade_risk(self.test_signal, small_portfolio)
        
        # Larger portfolio should result in larger position
        self.assertGreater(
            large_assessment.recommended_position_size,
            small_assessment.recommended_position_size
        )
    
    def test_error_handling(self):
        """Test error handling in integration flow."""
        # Test with invalid signal
        invalid_signal = TradingSignal(
            signal_id="integration-test-invalid",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=-1000.0,  # Invalid negative price
            confidence=0.8,
            timestamp=datetime.now()
        )
        
        # Should handle gracefully and return error assessment
        assessment = self.orchestrator.assess_trade_risk(invalid_signal, self.test_portfolio)
        
        self.assertIsNotNone(assessment)
        self.assertFalse(assessment.is_approved)
        self.assertIsNotNone(assessment.rejection_reason)
    
    def test_configuration_impact(self):
        """Test how configuration changes affect assessment."""
        # Create custom configuration
        custom_config = {
            "risk_limits": {
                "max_drawdown_limit": 0.10,  # More conservative
                "daily_loss_limit": 0.02,
                "per_trade_stop_loss": 0.01
            },
            "position_sizing": {
                "base_position_percent": 0.01,  # Smaller positions
                "min_position_usd": 5.0,
                "max_position_percent": 0.05
            }
        }
        
        # Create orchestrator with custom config
        custom_orchestrator = RiskOrchestrator(config=custom_config)
        
        # Perform assessment with custom config
        custom_assessment = custom_orchestrator.assess_trade_risk(self.test_signal, self.test_portfolio)
        
        # Perform assessment with default config
        default_assessment = self.orchestrator.assess_trade_risk(self.test_signal, self.test_portfolio)
        
        # Custom config should result in smaller position
        self.assertLess(
            custom_assessment.recommended_position_size,
            default_assessment.recommended_position_size
        )
    
    def test_risk_level_distribution(self):
        """Test risk level distribution across different scenarios."""
        scenarios = [
            # (portfolio_state, expected_risk_levels)
            (
                PortfolioState(total_equity=10000.0, current_drawdown=0.02, daily_pnl=100.0),
                ["LOW", "MEDIUM"]
            ),
            (
                PortfolioState(total_equity=10000.0, current_drawdown=0.10, daily_pnl=-100.0),
                ["MEDIUM", "HIGH"]
            ),
            (
                PortfolioState(total_equity=10000.0, current_drawdown=0.18, daily_pnl=-500.0),
                ["HIGH", "CRITICAL"]
            )
        ]
        
        for portfolio_state, expected_levels in scenarios:
            assessment = self.orchestrator.assess_trade_risk(self.test_signal, portfolio_state)
            self.assertIn(assessment.risk_level.value, expected_levels)


if __name__ == '__main__':
    unittest.main() 