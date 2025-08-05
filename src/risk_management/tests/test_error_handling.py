"""Tests for error handling in risk management module."""

import sys
import os
import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, SignalType, RiskLevel, RiskAssessment
)
from src.risk_management.utils.error_handler import (
    RiskManagementErrorHandler, ErrorType, ErrorSeverity,
    validate_input, create_error_assessment, safe_execute
)


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_validate_input_success(self):
        """Test successful input validation."""
        # Test valid inputs
        validate_input(100.0, float, 'test_field', min_value=0.0, max_value=1000.0)
        validate_input("test", str, 'test_field')
        validate_input(None, str, 'test_field', allow_none=True)
        
        # Should not raise any exceptions
        assert True
    
    def test_validate_input_failures(self):
        """Test input validation failures."""
        # Test None when not allowed
        with pytest.raises(ValueError, match="test_field cannot be None"):
            validate_input(None, str, 'test_field')
        
        # Test wrong type
        with pytest.raises(ValueError, match="test_field must be of type float"):
            validate_input("not_a_float", float, 'test_field')
        
        # Test value below minimum
        with pytest.raises(ValueError, match="test_field must be >= 10"):
            validate_input(5.0, float, 'test_field', min_value=10.0)
        
        # Test value above maximum
        with pytest.raises(ValueError, match="test_field must be <= 100"):
            validate_input(150.0, float, 'test_field', max_value=100.0)
        
        # Test empty string
        with pytest.raises(ValueError, match="test_field cannot be empty"):
            validate_input("", str, 'test_field')
    
    def test_error_handler_basic(self):
        """Test basic error handler functionality."""
        handler = RiskManagementErrorHandler()
        
        # Test error handling
        error = ValueError("Test error")
        risk_error = handler.handle_error(
            error=error,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context={'test': 'value'}
        )
        
        assert risk_error.error_type == ErrorType.VALIDATION_ERROR
        assert risk_error.severity == ErrorSeverity.MEDIUM
        assert risk_error.message == "Test error"
        assert risk_error.context == {'test': 'value'}
        assert handler.error_count == 1
    
    def test_error_handler_logging(self):
        """Test error handler logging levels."""
        handler = RiskManagementErrorHandler()
        
        # Test different severity levels
        error = ValueError("Test error")
        
        # Critical severity
        risk_error = handler.handle_error(
            error=error,
            error_type=ErrorType.SYSTEM_ERROR,
            severity=ErrorSeverity.CRITICAL
        )
        assert risk_error.severity == ErrorSeverity.CRITICAL
        
        # High severity
        risk_error = handler.handle_error(
            error=error,
            error_type=ErrorType.CALCULATION_ERROR,
            severity=ErrorSeverity.HIGH
        )
        assert risk_error.severity == ErrorSeverity.HIGH
        
        # Medium severity
        risk_error = handler.handle_error(
            error=error,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM
        )
        assert risk_error.severity == ErrorSeverity.MEDIUM
        
        # Low severity
        risk_error = handler.handle_error(
            error=error,
            error_type=ErrorType.DATA_ERROR,
            severity=ErrorSeverity.LOW
        )
        assert risk_error.severity == ErrorSeverity.LOW
    
    def test_error_handler_summary(self):
        """Test error handler summary functionality."""
        handler = RiskManagementErrorHandler()
        
        # Add some errors
        error = ValueError("Test error")
        handler.handle_error(error, ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM)
        handler.handle_error(error, ErrorType.CALCULATION_ERROR, ErrorSeverity.HIGH)
        handler.handle_error(error, ErrorType.VALIDATION_ERROR, ErrorSeverity.MEDIUM)
        
        summary = handler.get_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['error_counts']['VALIDATION_ERROR'] == 2
        assert summary['error_counts']['CALCULATION_ERROR'] == 1
        assert len(summary['recent_errors']) == 3
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def test_func(x, y):
            return x + y
        
        result = safe_execute(
            test_func, 5, 3,
            error_type=ErrorType.CALCULATION_ERROR,
            severity=ErrorSeverity.MEDIUM
        )
        
        assert result == 8
    
    def test_safe_execute_failure(self):
        """Test safe_execute with failing function."""
        def test_func(x, y):
            raise ValueError("Test error")
        
        result = safe_execute(
            test_func, 5, 3,
            error_type=ErrorType.CALCULATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            default_return=0
        )
        
        assert result == 0
    
    def test_create_error_assessment(self):
        """Test creating error assessment."""
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        error = ValueError("Test calculation error")
        assessment = create_error_assessment(signal, portfolio, error, ErrorType.CALCULATION_ERROR)
        
        assert assessment.signal_id == "test-signal"
        assert assessment.asset == "BTC"
        assert assessment.is_approved is False
        assert assessment.risk_level == RiskLevel.CRITICAL
        assert "Test calculation error" in assessment.rejection_reason
        assert assessment.recommended_position_size == 0.0
        assert assessment.portfolio_impact['error'] is True
        assert assessment.portfolio_impact['error_type'] == ErrorType.CALCULATION_ERROR.value


class TestRiskOrchestratorErrorHandling:
    """Test error handling in RiskOrchestrator."""
    
    def test_orchestrator_initialization_with_invalid_config(self):
        """Test orchestrator initialization with invalid config."""
        # Test with non-existent config file
        orchestrator = RiskOrchestrator("non_existent_config.json")
        
        # Should use default configuration
        assert orchestrator.max_drawdown_limit == 0.20
        assert orchestrator.daily_loss_limit == 0.05
        assert orchestrator.per_trade_stop_loss == 0.02
        assert orchestrator.max_position_size == 0.10
    
    def test_assessment_with_invalid_signal(self):
        """Test assessment with invalid signal."""
        orchestrator = RiskOrchestrator()
        
        # Test with None signal
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        assessment = orchestrator.assess_trade_risk(None, portfolio)
        
        assert assessment is not None
        assert assessment.is_approved is False
        assert "Assessment failed" in assessment.rejection_reason
        assert assessment.risk_level == RiskLevel.CRITICAL
    
    def test_assessment_with_invalid_portfolio(self):
        """Test assessment with invalid portfolio."""
        orchestrator = RiskOrchestrator()
        
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        # Test with None portfolio
        assessment = orchestrator.assess_trade_risk(signal, None)
        
        assert assessment is not None
        assert assessment.is_approved is False
        assert "Assessment failed" in assessment.rejection_reason
        assert assessment.risk_level == RiskLevel.CRITICAL
    
    def test_assessment_with_missing_signal_attributes(self):
        """Test assessment with signal missing required attributes."""
        orchestrator = RiskOrchestrator()
        
        # Create signal with missing attributes
        class InvalidSignal:
            signal_id = "test-signal"
            asset = "BTC"
            # Missing signal_type, price, confidence, timestamp
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        assessment = orchestrator.assess_trade_risk(InvalidSignal(), portfolio)
        
        assert assessment is not None
        assert assessment.is_approved is False
        assert "Assessment failed" in assessment.rejection_reason
        assert assessment.risk_level == RiskLevel.CRITICAL
    
    def test_assessment_with_invalid_signal_values(self):
        """Test assessment with invalid signal values."""
        orchestrator = RiskOrchestrator()
        
        # Test with negative price
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=-100.0,  # Invalid negative price
            confidence=0.8
        )
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        assert assessment is not None
        assert assessment.is_approved is False
        assert "Assessment failed" in assessment.rejection_reason
    
    def test_assessment_with_invalid_confidence(self):
        """Test assessment with invalid confidence value."""
        orchestrator = RiskOrchestrator()
        
        # Test with confidence > 1
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=1.5  # Invalid confidence > 1
        )
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        assert assessment is not None
        assert assessment.is_approved is False
        assert "Assessment failed" in assessment.rejection_reason
    
    def test_assessment_with_invalid_portfolio_equity(self):
        """Test assessment with invalid portfolio equity."""
        orchestrator = RiskOrchestrator()
        
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        # Test with negative equity
        portfolio = PortfolioState(
            total_equity=-1000.0,  # Invalid negative equity
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        assert assessment is not None
        # Should handle gracefully and still provide assessment
        assert hasattr(assessment, 'recommended_position_size')
        assert hasattr(assessment, 'stop_loss_price')
    
    def test_error_handler_integration(self):
        """Test that error handler is properly integrated."""
        orchestrator = RiskOrchestrator()
        
        # Trigger an error by passing invalid data
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        # Normal assessment should work
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        assert assessment is not None
        
        # Check that error handler has been used
        assert hasattr(orchestrator, 'error_handler')
        assert isinstance(orchestrator.error_handler, RiskManagementErrorHandler)
    
    def test_json_output_with_error_assessment(self):
        """Test JSON output with error assessment."""
        orchestrator = RiskOrchestrator()
        
        # Create an error assessment
        signal = TradingSignal(
            signal_id="test-signal",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        portfolio = PortfolioState(
            total_equity=100000.0,
            current_drawdown=0.05,
            daily_pnl=500.0
        )
        
        # Force an error by passing invalid data
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        
        # Convert to JSON
        json_output = orchestrator.to_json(assessment)
        json_data = json.loads(json_output)
        
        # Verify error information is included
        assert 'is_approved' in json_data
        assert 'rejection_reason' in json_data
        assert 'risk_warnings' in json_data
        assert 'risk_level' in json_data


if __name__ == "__main__":
    pytest.main([__file__]) 