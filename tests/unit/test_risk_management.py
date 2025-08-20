"""
Unit tests for the Risk Management Module.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock

from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, RiskAssessment, 
    SignalType, RiskLevel, ValidationResult
)
from src.risk_management.calculators.position_calculator import PositionCalculator
from src.risk_management.calculators.risk_level_calculator import RiskLevelCalculator
from src.risk_management.validators.trade_validator import TradeValidator
from src.risk_management.core.risk_orchestrator import RiskOrchestrator


class TestRiskModels(unittest.TestCase):
    """Test the risk management data models."""
    
    def test_trading_signal_creation(self):
        """Test TradingSignal creation with valid data."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        self.assertEqual(signal.signal_id, "test-1")
        self.assertEqual(signal.asset, "BTC")
        self.assertEqual(signal.signal_type, SignalType.LONG)
        self.assertEqual(signal.price, 50000.0)
        self.assertEqual(signal.confidence, 0.8)
        self.assertIsInstance(signal.timestamp, datetime)
    
    def test_portfolio_state_creation(self):
        """Test PortfolioState creation with valid data."""
        portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.05,
            daily_pnl=100.0
        )
        
        self.assertEqual(portfolio.total_equity, 10000.0)
        self.assertEqual(portfolio.current_drawdown, 0.05)
        self.assertEqual(portfolio.daily_pnl, 100.0)
    
    def test_risk_assessment_creation(self):
        """Test RiskAssessment creation with valid data."""
        assessment = RiskAssessment(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            signal_price=50000.0,
            signal_confidence=0.8,
            recommended_position_size=160.0,
            stop_loss_price=49000.0,
            take_profit_price=51000.0,
            risk_reward_ratio=2.0,
            position_risk_percent=0.016,
            portfolio_heat=0.016,
            risk_level=RiskLevel.LOW,
            is_approved=True
        )
        
        self.assertEqual(assessment.signal_id, "test-1")
        self.assertEqual(assessment.asset, "BTC")
        self.assertEqual(assessment.risk_level, RiskLevel.LOW)
        self.assertTrue(assessment.is_approved)


class TestPositionCalculator(unittest.TestCase):
    """Test the PositionCalculator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "position_sizing": {
                "base_position_percent": 0.02,
                "min_position_usd": 10.0,
                "max_position_percent": 0.10
            }
        }
        self.calculator = PositionCalculator(self.config)
    
    def test_calculate_position_size_basic(self):
        """Test basic position size calculation."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        portfolio = PortfolioState(total_equity=10000.0)
        
        position_size = self.calculator.calculate_position_size(signal, portfolio)
        
        # Expected: 10000 * 0.02 * 0.8 = 160
        self.assertEqual(position_size, 160.0)
    
    def test_calculate_position_size_minimum_limit(self):
        """Test position size respects minimum limit."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.1  # Very low confidence
        )
        portfolio = PortfolioState(total_equity=1000.0)  # Small portfolio
        
        position_size = self.calculator.calculate_position_size(signal, portfolio)
        
        # Should be at least min_position_usd
        self.assertEqual(position_size, 10.0)


class TestRiskLevelCalculator(unittest.TestCase):
    """Test the RiskLevelCalculator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "risk_limits": {
                "max_drawdown_limit": 0.20,
                "daily_loss_limit": 0.05
            }
        }
        self.calculator = RiskLevelCalculator(self.config)
    
    def test_calculate_risk_level_low(self):
        """Test risk level calculation for low risk."""
        assessment = RiskAssessment(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            signal_price=50000.0,
            signal_confidence=0.8,
            position_risk_percent=0.02,  # Low position risk
            portfolio_heat=0.03,          # Low portfolio heat
            current_drawdown=0.05,        # Low drawdown
            market_volatility=0.02,       # Low volatility
            correlation_risk=0.01         # Low correlation
        )
        
        risk_level = self.calculator.calculate_risk_level(assessment)
        self.assertEqual(risk_level, RiskLevel.LOW)
    
    def test_calculate_risk_level_critical(self):
        """Test risk level calculation for critical risk."""
        assessment = RiskAssessment(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            signal_price=50000.0,
            signal_confidence=0.8,
            position_risk_percent=0.25,  # Critical position risk
            portfolio_heat=0.30,          # Critical portfolio heat
            current_drawdown=0.25,        # Critical drawdown
            market_volatility=0.20,       # Critical volatility
            correlation_risk=0.15         # Critical correlation
        )
        
        risk_level = self.calculator.calculate_risk_level(assessment)
        self.assertEqual(risk_level, RiskLevel.CRITICAL)


class TestTradeValidator(unittest.TestCase):
    """Test the TradeValidator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "risk_limits": {
                "max_drawdown_limit": 0.20,
                "daily_loss_limit": 0.05,
                "per_trade_stop_loss": 0.02
            }
        }
        self.validator = TradeValidator(self.config)
    
    def test_validate_drawdown_limit_acceptable(self):
        """Test drawdown validation for acceptable trade."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.10  # 10% current drawdown
        )
        position_size = 100.0  # Small position
        
        result = self.validator.validate_drawdown_limit(signal, portfolio, position_size)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.rejection_reason)
    
    def test_validate_drawdown_limit_exceeds_limit(self):
        """Test drawdown validation when trade would exceed limit."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.18  # 18% current drawdown
        )
        position_size = 2000.0  # Large position that would exceed limit
        
        result = self.validator.validate_drawdown_limit(signal, portfolio, position_size)
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.rejection_reason)


class TestRiskOrchestrator(unittest.TestCase):
    """Test the RiskOrchestrator component."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = RiskOrchestrator()
    
    def test_assess_trade_risk_basic(self):
        """Test basic trade risk assessment."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.05,
            daily_pnl=100.0
        )
        
        assessment = self.orchestrator.assess_trade_risk(signal, portfolio)
        
        self.assertIsInstance(assessment, RiskAssessment)
        self.assertEqual(assessment.signal_id, "test-1")
        self.assertEqual(assessment.asset, "BTC")
        self.assertEqual(assessment.signal_type, SignalType.LONG)
        self.assertGreater(assessment.recommended_position_size, 0)
        self.assertGreater(assessment.stop_loss_price, 0)
        self.assertGreater(assessment.take_profit_price, 0)
        self.assertGreater(assessment.risk_reward_ratio, 0)
        self.assertIsInstance(assessment.risk_level, RiskLevel)
    
    def test_calculate_stop_loss_price_long(self):
        """Test stop loss calculation for LONG position."""
        signal = TradingSignal(
            signal_id="test-1",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        position_size = 100.0
        
        stop_loss = self.orchestrator._calculate_stop_loss_price(signal, position_size)
        
        # For LONG, stop loss should be below entry price
        self.assertLess(stop_loss, signal.price)
        self.assertGreater(stop_loss, 0)


if __name__ == '__main__':
    unittest.main() 