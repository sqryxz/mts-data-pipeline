"""Integration tests for the complete risk management workflow."""

import sys
import os
import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, SignalType, RiskLevel, RiskAssessment
)
from src.risk_management.validators.trade_validator import TradeValidator
from src.risk_management.calculators.position_calculator import PositionCalculator
from src.risk_management.calculators.risk_level_calculator import RiskLevelCalculator


class TestRiskManagementIntegration:
    """Test complete end-to-end risk assessment workflow."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_trading_signals(self):
        """Create sample trading signals for testing."""
        return {
            'long_btc': TradingSignal(
                signal_id="test-long-btc-001",
                asset="BTC",
                signal_type=SignalType.LONG,
                price=50000.0,
                confidence=0.85,
                timestamp=datetime.now()
            ),
            'short_eth': TradingSignal(
                signal_id="test-short-eth-001",
                asset="ETH",
                signal_type=SignalType.SHORT,
                price=3000.0,
                confidence=0.75,
                timestamp=datetime.now()
            ),
            'high_confidence': TradingSignal(
                signal_id="test-high-conf-001",
                asset="BTC",
                signal_type=SignalType.LONG,
                price=50000.0,
                confidence=0.95,
                timestamp=datetime.now()
            ),
            'low_confidence': TradingSignal(
                signal_id="test-low-conf-001",
                asset="ETH",
                signal_type=SignalType.LONG,
                price=3000.0,
                confidence=0.45,
                timestamp=datetime.now()
            )
        }
    
    @pytest.fixture
    def sample_portfolio_states(self):
        """Create sample portfolio states for testing."""
        return {
            'healthy': PortfolioState(
                total_equity=100000.0,
                current_drawdown=0.05,
                daily_pnl=500.0,
                positions={'BTC': 0.5, 'ETH': 0.3},
                cash=20000.0
            ),
            'high_drawdown': PortfolioState(
                total_equity=80000.0,
                current_drawdown=0.25,
                daily_pnl=-2000.0,
                positions={'BTC': 0.8, 'ETH': 0.6},
                cash=5000.0
            ),
            'low_equity': PortfolioState(
                total_equity=5000.0,
                current_drawdown=0.10,
                daily_pnl=100.0,
                positions={'BTC': 0.1},
                cash=4500.0
            ),
            'excellent': PortfolioState(
                total_equity=200000.0,
                current_drawdown=0.02,
                daily_pnl=2000.0,
                positions={'BTC': 0.3, 'ETH': 0.2},
                cash=140000.0
            )
        }
    
    def test_complete_risk_assessment_workflow(self, sample_trading_signals, sample_portfolio_states):
        """Test complete end-to-end risk assessment workflow."""
        # Initialize risk orchestrator
        orchestrator = RiskOrchestrator()
        
        # Test signal with healthy portfolio
        signal = sample_trading_signals['long_btc']
        portfolio = sample_portfolio_states['healthy']
        
        # Perform risk assessment
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        # Verify assessment structure
        assert assessment is not None
        assert isinstance(assessment, RiskAssessment)
        assert assessment.signal_id == signal.signal_id
        assert assessment.asset == signal.asset
        assert assessment.signal_type == signal.signal_type
        assert assessment.signal_price == signal.price
        assert assessment.signal_confidence == signal.confidence
        
        # Verify assessment has required fields
        assert hasattr(assessment, 'is_approved')
        assert hasattr(assessment, 'risk_level')
        assert hasattr(assessment, 'recommended_position_size')
        assert hasattr(assessment, 'stop_loss_price')
        assert hasattr(assessment, 'take_profit_price')
        assert hasattr(assessment, 'risk_reward_ratio')
        
        # Verify risk level is valid
        assert assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Verify position size is reasonable
        assert assessment.recommended_position_size >= 0
        assert assessment.recommended_position_size <= portfolio.total_equity * 0.1  # Max 10% of equity
        
        # Verify stop loss is reasonable
        if assessment.stop_loss_price > 0:
            if signal.signal_type == SignalType.LONG:
                assert assessment.stop_loss_price < signal.price
            else:
                assert assessment.stop_loss_price > signal.price
    
    def test_risk_assessment_with_different_portfolio_states(self, sample_trading_signals, sample_portfolio_states):
        """Test risk assessment with different portfolio states."""
        orchestrator = RiskOrchestrator()
        signal = sample_trading_signals['long_btc']
        
        # Test with healthy portfolio
        healthy_assessment = orchestrator.assess_trade_risk(signal, sample_portfolio_states['healthy'])
        assert healthy_assessment is not None
        
        # Test with high drawdown portfolio
        high_dd_assessment = orchestrator.assess_trade_risk(signal, sample_portfolio_states['high_drawdown'])
        assert high_dd_assessment is not None
        
        # Test with low equity portfolio
        low_equity_assessment = orchestrator.assess_trade_risk(signal, sample_portfolio_states['low_equity'])
        assert low_equity_assessment is not None
        
        # Test with excellent portfolio
        excellent_assessment = orchestrator.assess_trade_risk(signal, sample_portfolio_states['excellent'])
        assert excellent_assessment is not None
        
        # Verify that high drawdown portfolio has higher risk level
        if high_dd_assessment.is_approved and healthy_assessment.is_approved:
            assert high_dd_assessment.risk_level.value >= healthy_assessment.risk_level.value
    
    def test_risk_assessment_with_different_signal_types(self, sample_trading_signals, sample_portfolio_states):
        """Test risk assessment with different signal types."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        
        # Test LONG signal
        long_signal = sample_trading_signals['long_btc']
        long_assessment = orchestrator.assess_trade_risk(long_signal, portfolio)
        assert long_assessment is not None
        
        # Test SHORT signal
        short_signal = sample_trading_signals['short_eth']
        short_assessment = orchestrator.assess_trade_risk(short_signal, portfolio)
        assert short_assessment is not None
        
        # Verify both assessments have valid structure
        for assessment in [long_assessment, short_assessment]:
            assert hasattr(assessment, 'is_approved')
            assert hasattr(assessment, 'risk_level')
            assert hasattr(assessment, 'recommended_position_size')
            assert hasattr(assessment, 'stop_loss_price')
    
    def test_risk_assessment_with_different_confidence_levels(self, sample_trading_signals, sample_portfolio_states):
        """Test risk assessment with different confidence levels."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        
        # Test high confidence signal
        high_conf_signal = sample_trading_signals['high_confidence']
        high_conf_assessment = orchestrator.assess_trade_risk(high_conf_signal, portfolio)
        assert high_conf_assessment is not None
        
        # Test low confidence signal
        low_conf_signal = sample_trading_signals['low_confidence']
        low_conf_assessment = orchestrator.assess_trade_risk(low_conf_signal, portfolio)
        assert low_conf_assessment is not None
        
        # Verify that high confidence signals generally get better assessments
        if high_conf_assessment.is_approved and low_conf_assessment.is_approved:
            # High confidence should generally result in larger position sizes
            assert high_conf_assessment.recommended_position_size >= low_conf_assessment.recommended_position_size
    
    def test_json_output_integration(self, sample_trading_signals, sample_portfolio_states):
        """Test JSON output integration."""
        orchestrator = RiskOrchestrator()
        signal = sample_trading_signals['long_btc']
        portfolio = sample_portfolio_states['healthy']
        
        # Perform risk assessment
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        # Convert to JSON
        json_output = orchestrator.to_json(assessment)
        
        # Verify JSON is valid
        assert json_output is not None
        assert isinstance(json_output, str)
        
        # Parse JSON and verify structure
        json_data = json.loads(json_output)
        
        # Verify required fields
        required_fields = [
            'signal_id', 'asset', 'signal_type', 'signal_price', 'signal_confidence',
            'is_approved', 'risk_level', 'recommended_position_size', 'stop_loss_price',
            'take_profit_price', 'risk_reward_ratio'
        ]
        
        for field in required_fields:
            assert field in json_data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(json_data['signal_id'], str)
        assert isinstance(json_data['asset'], str)
        assert isinstance(json_data['signal_type'], str)
        assert isinstance(json_data['signal_price'], (int, float))
        assert isinstance(json_data['signal_confidence'], (int, float))
        assert isinstance(json_data['is_approved'], bool)
        assert isinstance(json_data['risk_level'], str)
        assert isinstance(json_data['recommended_position_size'], (int, float))
        assert isinstance(json_data['stop_loss_price'], (int, float))
        assert isinstance(json_data['take_profit_price'], (int, float))
        assert isinstance(json_data['risk_reward_ratio'], (int, float))
    
    def test_error_handling_integration(self, sample_portfolio_states):
        """Test error handling in risk assessment."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        
        # Test with invalid signal (missing required fields)
        invalid_signal = TradingSignal(
            signal_id="invalid-signal",
            asset="",  # Empty asset
            signal_type=SignalType.LONG,
            price=-100.0,  # Negative price
            confidence=1.5  # Invalid confidence > 1
        )
        
        # Should handle gracefully
        assessment = orchestrator.assess_trade_risk(invalid_signal, portfolio)
        assert assessment is not None
        assert isinstance(assessment, RiskAssessment)
        
        # Test with invalid portfolio (negative equity)
        invalid_portfolio = PortfolioState(
            total_equity=-1000.0,  # Negative equity
            current_drawdown=0.05,
            daily_pnl=100.0
        )
        
        valid_signal = TradingSignal(
            signal_id="valid-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        # Should handle gracefully
        assessment = orchestrator.assess_trade_risk(valid_signal, invalid_portfolio)
        assert assessment is not None
        assert isinstance(assessment, RiskAssessment)
    
    def test_batch_assessment_integration(self, sample_trading_signals, sample_portfolio_states):
        """Test batch assessment functionality."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        
        # Create multiple signals
        signals = [
            sample_trading_signals['long_btc'],
            sample_trading_signals['short_eth'],
            sample_trading_signals['high_confidence']
        ]
        
        # Perform batch assessment
        assessments = []
        for signal in signals:
            assessment = orchestrator.assess_trade_risk(signal, portfolio)
            assessments.append(assessment)
        
        # Verify all assessments are valid
        assert len(assessments) == len(signals)
        for assessment in assessments:
            assert assessment is not None
            assert isinstance(assessment, RiskAssessment)
            assert hasattr(assessment, 'is_approved')
            assert hasattr(assessment, 'risk_level')
    
    def test_risk_limit_enforcement_integration(self, sample_trading_signals):
        """Test that risk limits are properly enforced."""
        orchestrator = RiskOrchestrator()
        
        # Test with portfolio that exceeds drawdown limit
        high_drawdown_portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.25,  # 25% drawdown (above 20% limit)
            daily_pnl=-5000.0,
            positions={'BTC': 0.8, 'ETH': 0.6},
            cash=5000.0
        )
        
        signal = sample_trading_signals['long_btc']
        assessment = orchestrator.assess_trade_risk(signal, high_drawdown_portfolio)
        
        # Should either reject or assign high risk level
        assert assessment is not None
        if not assessment.is_approved:
            assert assessment.rejection_reason is not None
        else:
            assert assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_position_sizing_integration(self, sample_trading_signals, sample_portfolio_states):
        """Test position sizing calculations."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        signal = sample_trading_signals['long_btc']
        
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        # Verify position sizing is reasonable
        assert assessment.recommended_position_size >= 0
        assert assessment.recommended_position_size <= portfolio.total_equity * 0.1  # Max 10%
        
        # Test with different portfolio sizes
        small_portfolio = PortfolioState(
            total_equity=5000.0,
            current_drawdown=0.05,
            daily_pnl=100.0
        )
        
        large_portfolio = PortfolioState(
            total_equity=500000.0,
            current_drawdown=0.05,
            daily_pnl=5000.0
        )
        
        small_assessment = orchestrator.assess_trade_risk(signal, small_portfolio)
        large_assessment = orchestrator.assess_trade_risk(signal, large_portfolio)
        
        # Position sizes should be proportional to portfolio size
        if small_assessment.is_approved and large_assessment.is_approved:
            assert small_assessment.recommended_position_size < large_assessment.recommended_position_size
    
    def test_stop_loss_calculation_integration(self, sample_trading_signals, sample_portfolio_states):
        """Test stop loss calculations."""
        orchestrator = RiskOrchestrator()
        portfolio = sample_portfolio_states['healthy']
        
        # Test LONG signal
        long_signal = sample_trading_signals['long_btc']
        long_assessment = orchestrator.assess_trade_risk(long_signal, portfolio)
        
        if long_assessment.stop_loss_price > 0:
            # For LONG signals, stop loss should be below entry price
            assert long_assessment.stop_loss_price < long_signal.price
            
            # Stop loss should be reasonable (not too close, not too far)
            stop_loss_percent = (long_signal.price - long_assessment.stop_loss_price) / long_signal.price
            assert 0.01 <= stop_loss_percent <= 0.10  # 1% to 10%
        
        # Test SHORT signal
        short_signal = sample_trading_signals['short_eth']
        short_assessment = orchestrator.assess_trade_risk(short_signal, portfolio)
        
        if short_assessment.stop_loss_price > 0:
            # For SHORT signals, stop loss should be above entry price
            assert short_assessment.stop_loss_price > short_signal.price
            
            # Stop loss should be reasonable
            stop_loss_percent = (short_assessment.stop_loss_price - short_signal.price) / short_signal.price
            assert 0.01 <= stop_loss_percent <= 0.10  # 1% to 10%


class TestRiskManagementCLI:
    """Test command-line interface for risk management."""
    
    def test_cli_basic_functionality(self):
        """Test basic CLI functionality."""
        # This would test the CLI interface
        # For now, we'll create a mock test
        assert True  # Placeholder for CLI tests


if __name__ == "__main__":
    pytest.main([__file__]) 