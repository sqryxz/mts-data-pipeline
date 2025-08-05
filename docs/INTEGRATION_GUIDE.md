# Risk Management Module Integration Guide

## Overview

This guide explains how to integrate the Risk Management Module into the existing MTS pipeline.

## Quick Integration

### Direct Module Integration

```python
from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import TradingSignal, PortfolioState, SignalType

# Initialize risk orchestrator
risk_orchestrator = RiskOrchestrator()

def process_signal_with_risk(signal_data, portfolio_data):
    """Process trading signal with risk management."""
    
    # Convert to risk management models
    signal = TradingSignal(
        signal_id=signal_data['id'],
        asset=signal_data['asset'],
        signal_type=SignalType(signal_data['type']),
        price=signal_data['price'],
        confidence=signal_data['confidence']
    )
    
    portfolio = PortfolioState(
        total_equity=portfolio_data['total_equity'],
        current_drawdown=portfolio_data['current_drawdown'],
        daily_pnl=portfolio_data['daily_pnl']
    )
    
    # Perform risk assessment
    assessment = risk_orchestrator.assess_trade_risk(signal, portfolio)
    
    return {
        'approved': assessment.is_approved,
        'position_size': assessment.recommended_position_size,
        'stop_loss': assessment.stop_loss_price,
        'risk_level': assessment.risk_level.value
    }
```

### API Integration

```python
import requests

def assess_risk_via_api(signal_data, portfolio_data):
    """Assess risk using the API endpoint."""
    
    request_data = {
        "signal": signal_data,
        "portfolio_state": portfolio_data
    }
    
    response = requests.post(
        'http://localhost:5000/assess-risk',
        json=request_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        return response.json()['assessment']
    else:
        raise Exception(f"API request failed: {response.status_code}")
```

## Integration Examples

### Signal Processing Integration

```python
class SignalProcessor:
    def __init__(self):
        self.risk_orchestrator = RiskOrchestrator()
    
    def process_signal(self, signal):
        """Process signal with risk management."""
        
        portfolio_state = self.get_portfolio_state()
        risk_signal = self.convert_to_risk_signal(signal)
        assessment = self.risk_orchestrator.assess_trade_risk(risk_signal, portfolio_state)
        
        if assessment.is_approved:
            return self.execute_signal(signal, assessment)
        else:
            self.log_rejected_signal(signal, assessment)
            return None
```

### Execution Engine Integration

```python
class ExecutionEngine:
    def __init__(self):
        self.risk_orchestrator = RiskOrchestrator()
    
    def execute_signal(self, signal):
        """Execute signal with risk management validation."""
        
        portfolio_state = self.get_portfolio_state()
        assessment = self.risk_orchestrator.assess_trade_risk(signal, portfolio_state)
        
        if assessment.is_approved:
            execution_params = {
                'position_size': assessment.recommended_position_size,
                'stop_loss': assessment.stop_loss_price,
                'take_profit': assessment.take_profit_price,
                'risk_level': assessment.risk_level.value
            }
            return self.execute_trade(signal, execution_params)
        else:
            self.log_rejection(signal, assessment)
            return None
```

## Configuration

### Environment-Based Configuration

```python
def get_risk_config(environment):
    """Get risk configuration for environment."""
    
    configs = {
        'development': {
            "risk_limits": {
                "max_drawdown_limit": 0.30,
                "daily_loss_limit": 0.10
            }
        },
        'production': {
            "risk_limits": {
                "max_drawdown_limit": 0.20,
                "daily_loss_limit": 0.05
            }
        }
    }
    
    return configs.get(environment, configs['production'])

# Usage
risk_config = get_risk_config('production')
risk_orchestrator = RiskOrchestrator(config=risk_config)
```

## Error Handling

```python
def safe_risk_assessment(signal, portfolio_state):
    """Safely perform risk assessment with error handling."""
    
    try:
        risk_orchestrator = RiskOrchestrator()
        return risk_orchestrator.assess_trade_risk(signal, portfolio_state)
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        return RiskAssessment(
            signal_id=signal.signal_id,
            asset=signal.asset,
            signal_type=signal.signal_type,
            signal_price=signal.price,
            signal_confidence=signal.confidence,
            is_approved=False,
            rejection_reason=f"Risk assessment error: {str(e)}",
            risk_level=RiskLevel.CRITICAL
        )
```

## Testing

```python
def test_risk_integration():
    """Test risk management integration."""
    
    signal_processor = SignalProcessor()
    test_signal = create_test_signal()
    result = signal_processor.process_signal(test_signal)
    
    assert hasattr(result, 'risk_assessment')
    assert result.risk_assessment.is_approved in [True, False]
    assert result.risk_assessment.risk_level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    print("Risk management integration test passed")
```

## Performance Optimization

```python
from functools import lru_cache

class OptimizedRiskOrchestrator:
    def __init__(self):
        self.orchestrator = RiskOrchestrator()
    
    @lru_cache(maxsize=1000)
    def assess_trade_risk_cached(self, signal_hash, portfolio_hash):
        """Cached risk assessment for performance."""
        return self.orchestrator.assess_trade_risk(signal, portfolio)
    
    def batch_assessment(self, signals, portfolio_state):
        """Perform batch risk assessment."""
        assessments = []
        
        for signal in signals:
            try:
                assessment = self.orchestrator.assess_trade_risk(signal, portfolio_state)
                assessments.append(assessment)
            except Exception as e:
                logger.error(f"Assessment failed for signal {signal.signal_id}: {e}")
                assessments.append(create_error_assessment(signal, str(e)))
        
        return assessments
```

## Health Check

```python
def health_check_risk_management():
    """Health check for risk management module."""
    
    try:
        risk_orchestrator = RiskOrchestrator()
        
        test_signal = TradingSignal(
            signal_id="health-check",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=0.8
        )
        
        test_portfolio = PortfolioState(
            total_equity=10000.0,
            current_drawdown=0.05,
            daily_pnl=100.0
        )
        
        assessment = risk_orchestrator.assess_trade_risk(test_signal, test_portfolio)
        
        assert assessment is not None
        assert hasattr(assessment, 'is_approved')
        assert hasattr(assessment, 'risk_level')
        
        return True
        
    except Exception as e:
        logger.error(f"Risk management health check failed: {e}")
        return False
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the risk management module is in the Python path
2. **Configuration Issues**: Verify configuration file format and permissions
3. **API Connection**: Check API server is running and accessible
4. **Performance Issues**: Monitor assessment times and optimize if needed

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def debug_risk_assessment(signal, portfolio_state):
    """Debug risk assessment with detailed logging."""
    
    logger.debug(f"Input signal: {signal}")
    logger.debug(f"Portfolio state: {portfolio_state}")
    
    assessment = risk_orchestrator.assess_trade_risk(signal, portfolio_state)
    
    logger.debug(f"Assessment result: {assessment}")
    logger.debug(f"Risk level: {assessment.risk_level.value}")
    logger.debug(f"Approved: {assessment.is_approved}")
    
    return assessment
```

## Summary

This integration guide provides instructions for integrating the Risk Management Module into your existing MTS pipeline. The module can be integrated using direct module calls or REST API endpoints.

Key integration points:
- Signal processing pipeline
- Portfolio state management
- Execution engine
- Configuration management
- Error handling and logging
- Performance optimization
- Testing and monitoring

For additional support, refer to the API documentation and examples provided with the module. 