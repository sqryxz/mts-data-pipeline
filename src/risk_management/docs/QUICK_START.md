# Risk Management Module - Quick Start Guide

## Getting Started

This guide will help you quickly set up and use the Risk Management Module.

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

1. **Clone the repository** (if not already done):
```bash
git clone <repository-url>
cd MTS-data-pipeline
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Basic Usage

### 1. Simple Risk Assessment

```python
from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import TradingSignal, PortfolioState, SignalType

# Initialize the risk orchestrator
orchestrator = RiskOrchestrator()

# Create a trading signal
signal = TradingSignal(
    signal_id="my-signal-1",
    asset="BTC",
    signal_type=SignalType.LONG,
    price=50000.0,
    confidence=0.8
)

# Create portfolio state
portfolio = PortfolioState(
    total_equity=10000.0,
    current_drawdown=0.05,
    daily_pnl=100.0
)

# Assess the risk
assessment = orchestrator.assess_trade_risk(signal, portfolio)

# Check the results
print(f"Risk Level: {assessment.risk_level.value}")
print(f"Approved: {assessment.is_approved}")
print(f"Position Size: ${assessment.recommended_position_size:.2f}")
print(f"Stop Loss: ${assessment.stop_loss_price:.2f}")
```

### 2. Using the API

Start the API server:
```bash
python src/risk_management/api/risk_api.py
```

Make a risk assessment request:
```python
import requests

# Prepare the request
data = {
    "signal": {
        "signal_id": "api-test",
        "asset": "BTC",
        "signal_type": "LONG",
        "price": 50000.0,
        "confidence": 0.8,
        "timestamp": "2024-01-01T12:00:00Z"
    },
    "portfolio_state": {
        "total_equity": 10000.0,
        "current_drawdown": 0.05,
        "daily_pnl": 100.0,
        "positions": {"BTC": 0.1},
        "cash": 9000.0
    }
}

# Send request
response = requests.post(
    "http://localhost:5000/assess-risk",
    json=data
)

# Check response
if response.status_code == 200:
    result = response.json()
    assessment = result['assessment']
    print(f"Risk Level: {assessment['risk_level']}")
    print(f"Approved: {assessment['is_approved']}")
else:
    print(f"Error: {response.text}")
```

## Configuration

### Default Configuration

The module uses a default configuration that provides conservative risk limits:

- **Max Drawdown**: 20%
- **Daily Loss Limit**: 5%
- **Per Trade Stop Loss**: 2%
- **Max Position Size**: 10%

### Custom Configuration

Create a custom configuration file:

```json
{
  "risk_limits": {
    "max_drawdown_limit": 0.15,
    "daily_loss_limit": 0.03,
    "per_trade_stop_loss": 0.015
  },
  "position_sizing": {
    "base_position_percent": 0.015,
    "min_position_size": 0.001
  }
}
```

Update the configuration via API:
```python
import requests

new_config = {
    "risk_limits": {
        "max_drawdown_limit": 0.15,
        "daily_loss_limit": 0.03
    }
}

response = requests.post(
    "http://localhost:5000/config",
    json=new_config
)
```

## Understanding Risk Levels

The module classifies risk into four levels:

| Risk Level | Composite Score | Description |
|------------|-----------------|-------------|
| **LOW** | ≤ 8% | Safe for trading |
| **MEDIUM** | ≤ 12% | Proceed with caution |
| **HIGH** | ≤ 18% | High risk, consider reducing position |
| **CRITICAL** | > 18% | Very high risk, avoid trading |

## Key Components

### Risk Assessment Output

The `RiskAssessment` object contains:

- **Position Sizing**: Recommended position size and method
- **Risk Management**: Stop loss and take profit prices
- **Risk Metrics**: Risk/reward ratio, position risk percentage
- **Validation**: Approval status and rejection reasons
- **Risk Level**: Overall risk classification
- **Warnings**: Risk factor warnings

### Validation Rules

The module validates trades against:

1. **Drawdown Limits**: Prevents exceeding maximum drawdown
2. **Daily Loss Limits**: Prevents exceeding daily loss limits
3. **Position Size Limits**: Ensures reasonable position sizes
4. **Risk/Reward Ratios**: Ensures favorable risk/reward

## Error Handling

### Common Errors

1. **Validation Errors**: Invalid input data
   ```python
   # Fix: Ensure all required fields are present and valid
   signal = TradingSignal(
       signal_id="valid-id",
       asset="BTC",
       signal_type=SignalType.LONG,  # Must be LONG or SHORT
       price=50000.0,  # Must be positive number
       confidence=0.8   # Must be between 0 and 1
   )
   ```

2. **Configuration Errors**: Invalid configuration
   ```python
   # Fix: Ensure configuration values are within valid ranges
   config = {
       "risk_limits": {
           "max_drawdown_limit": 0.20,  # Must be between 0 and 1
           "daily_loss_limit": 0.05     # Must be between 0 and 1
       }
   }
   ```

3. **API Errors**: Network or server issues
   ```python
   # Fix: Check server status and network connectivity
   response = requests.get("http://localhost:5000/health")
   ```

## Testing

### Run Basic Tests

```bash
# Test the risk orchestrator
python -c "
from src.risk_management.core.risk_orchestrator import RiskOrchestrator
orchestrator = RiskOrchestrator()
print('Risk orchestrator initialized successfully')
"

# Test the API (if server is running)
python -c "
import requests
response = requests.get('http://localhost:5000/health')
print(f'API health check: {response.status_code}')
"
```

### Test Different Scenarios

```python
# Test low risk scenario
low_risk_portfolio = PortfolioState(
    total_equity=10000.0,
    current_drawdown=0.02,  # Low drawdown
    daily_pnl=100.0         # Positive P&L
)

# Test high risk scenario
high_risk_portfolio = PortfolioState(
    total_equity=10000.0,
    current_drawdown=0.15,  # High drawdown
    daily_pnl=-400.0        # Negative P&L
)

# Test critical risk scenario
critical_risk_portfolio = PortfolioState(
    total_equity=10000.0,
    current_drawdown=0.18,  # Very high drawdown
    daily_pnl=-600.0        # Large negative P&L
)
```

## Next Steps

1. **Review the full documentation** in `README.md`
2. **Explore the API endpoints** for integration
3. **Customize the configuration** for your risk tolerance
4. **Add monitoring and logging** for production use
5. **Implement error handling** for your specific use case

## Support

For issues and questions:

1. Check the troubleshooting section in the main documentation
2. Review the error messages for specific guidance
3. Test with the provided examples
4. Verify configuration values are within valid ranges

## Production Deployment

For production use, consider:

1. **Authentication**: Add API authentication
2. **Rate Limiting**: Implement request rate limiting
3. **HTTPS**: Use HTTPS for secure communication
4. **Monitoring**: Add comprehensive logging and monitoring
5. **Backup**: Implement configuration backup and recovery 