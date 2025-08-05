# Risk Management Module Documentation

## Overview

The Risk Management Module provides comprehensive risk assessment and validation for trading signals in the MTS pipeline. It ensures that all trades meet risk management criteria before execution.

## Architecture

```
src/risk_management/
├── api/                    # API endpoints
│   └── risk_api.py        # Flask API for risk assessment
├── calculators/           # Risk calculation components
│   ├── position_calculator.py
│   └── risk_level_calculator.py
├── config/               # Configuration files
│   └── risk_config.json
├── core/                 # Core orchestration
│   └── risk_orchestrator.py
├── models/               # Data models
│   └── risk_models.py
├── validators/           # Validation components
│   └── trade_validator.py
└── docs/                # Documentation
    └── README.md
```

## Core Components

### 1. Risk Orchestrator (`core/risk_orchestrator.py`)

The main coordinator that processes trading signals and produces comprehensive risk assessments.

**Key Features:**
- Position sizing calculations
- Stop loss and take profit calculations
- Risk/reward ratio analysis
- Trade validation against risk limits
- Risk level classification
- Integration with all risk components

**Usage:**
```python
from src.risk_management.core.risk_orchestrator import RiskOrchestrator

# Initialize orchestrator
orchestrator = RiskOrchestrator()

# Assess trade risk
assessment = orchestrator.assess_trade_risk(signal, portfolio_state)
```

### 2. Position Calculator (`calculators/position_calculator.py`)

Calculates appropriate position sizes based on account equity, signal confidence, and risk limits.

**Features:**
- Fixed percentage position sizing
- Confidence-based adjustments
- Maximum/minimum position limits
- Comprehensive input validation

### 3. Risk Level Calculator (`calculators/risk_level_calculator.py`)

Determines risk levels (LOW/MEDIUM/HIGH/CRITICAL) based on multiple risk metrics.

**Risk Metrics:**
- Position risk percentage
- Portfolio heat
- Current drawdown
- Market volatility
- Correlation risk

**Risk Levels:**
- **LOW**: Composite score ≤ 8%
- **MEDIUM**: Composite score ≤ 12%
- **HIGH**: Composite score ≤ 18%
- **CRITICAL**: Composite score > 18%

### 4. Trade Validator (`validators/trade_validator.py`)

Validates trades against risk management limits.

**Validation Rules:**
- Maximum drawdown limit (20%)
- Daily loss limit (5%)
- Position size limits
- Warning thresholds (80% of limits)

### 5. Data Models (`models/risk_models.py`)

Core data structures for the risk management system.

**Key Models:**
- `TradingSignal`: Represents incoming trading signals
- `PortfolioState`: Current portfolio state
- `RiskAssessment`: Comprehensive risk assessment output
- `SignalType`: Enum for LONG/SHORT signals
- `RiskLevel`: Enum for risk levels

## API Documentation

### Health Check
```
GET /health
```
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "risk-management",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Risk Assessment
```
POST /assess-risk
```

**Request Body:**
```json
{
  "signal": {
    "signal_id": "unique-id",
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
```

**Response:**
```json
{
  "status": "success",
  "assessment": {
    "signal_id": "unique-id",
    "asset": "BTC",
    "signal_type": "LONG",
    "signal_price": 50000.0,
    "signal_confidence": 0.8,
    "timestamp": "2024-01-01T12:00:00Z",
    "recommended_position_size": 160.0,
    "position_size_method": "Fixed Percentage",
    "stop_loss_price": 49000.0,
    "take_profit_price": 51000.0,
    "risk_reward_ratio": 2.0,
    "position_risk_percent": 0.016,
    "portfolio_heat": 0.016,
    "risk_level": "LOW",
    "is_approved": true,
    "rejection_reason": null,
    "risk_warnings": [],
    "market_volatility": 0.0,
    "correlation_risk": 0.0,
    "portfolio_impact": {
      "drawdown_impact": 0.0,
      "exposure_increase": 0.016
    },
    "current_drawdown": 0.05,
    "daily_pnl_impact": 0.0,
    "risk_config_snapshot": {
      "max_drawdown_limit": 0.2,
      "daily_loss_limit": 0.05,
      "per_trade_stop_loss": 0.02,
      "max_position_size": 0.1
    },
    "processing_time_ms": 45.2
  }
}
```

### Get Configuration
```
GET /config
```
Returns current risk management configuration.

### Update Configuration
```
POST /config
```
Updates risk management configuration.

**Request Body:**
```json
{
  "risk_limits": {
    "max_drawdown_limit": 0.20,
    "daily_loss_limit": 0.05,
    "per_trade_stop_loss": 0.02
  }
}
```

## Configuration

### Risk Configuration (`config/risk_config.json`)

```json
{
  "risk_limits": {
    "max_drawdown_limit": 0.20,
    "daily_loss_limit": 0.05,
    "per_trade_stop_loss": 0.02,
    "max_position_size": 0.10,
    "max_single_asset_exposure": 0.15,
    "max_sector_exposure": 0.30,
    "max_correlation_risk": 0.80,
    "volatility_threshold": 0.05,
    "drawdown_warning_level": 0.15
  },
  "position_sizing": {
    "base_position_percent": 0.02,
    "min_position_size": 0.001
  },
  "risk_assessment": {
    "default_risk_reward_ratio": 2.0,
    "confidence_threshold": 0.5,
    "processing_timeout_ms": 5000
  },
  "market_conditions": {
    "volatility_warning_threshold": 0.04,
    "low_liquidity_threshold": 1000000,
    "correlation_lookback_days": 30
  },
  "reporting": {
    "enable_json_output": true,
    "enable_logging": true,
    "log_level": "INFO"
  }
}
```

## Usage Examples

### Basic Risk Assessment

```python
from src.risk_management.core.risk_orchestrator import RiskOrchestrator
from src.risk_management.models.risk_models import TradingSignal, PortfolioState, SignalType

# Initialize orchestrator
orchestrator = RiskOrchestrator()

# Create trading signal
signal = TradingSignal(
    signal_id="test-1",
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

# Assess risk
assessment = orchestrator.assess_trade_risk(signal, portfolio)

# Check results
print(f"Risk level: {assessment.risk_level.value}")
print(f"Is approved: {assessment.is_approved}")
print(f"Position size: ${assessment.recommended_position_size:.2f}")
```

### API Usage

```python
import requests
import json

# Risk assessment request
request_data = {
    "signal": {
        "signal_id": "api-test-1",
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
    json=request_data,
    headers={'Content-Type': 'application/json'}
)

# Process response
if response.status_code == 200:
    result = response.json()
    assessment = result['assessment']
    print(f"Risk level: {assessment['risk_level']}")
    print(f"Is approved: {assessment['is_approved']}")
else:
    print(f"Error: {response.text}")
```

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "Validation error: Invalid signal_type: INVALID_TYPE. Valid types: ['LONG', 'SHORT']",
  "status": "error"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "status": "error"
}
```

### Error Scenarios

1. **Invalid Signal Type**: Non-existent signal type
2. **Invalid Numeric Values**: Non-numeric price, confidence, etc.
3. **Malformed Timestamps**: Invalid timestamp format
4. **Missing Required Fields**: Missing signal or portfolio data
5. **Invalid Configuration**: Malformed configuration updates

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
python -m pytest tests/unit/test_risk_management.py
```

### Integration Tests

Test the complete risk assessment flow:

```bash
python -m pytest tests/integration/test_risk_integration.py
```

### API Tests

Test API endpoints:

```bash
python -m pytest tests/api/test_risk_api.py
```

## Deployment

### Requirements

- Python 3.8+
- Flask
- Required dependencies in `requirements.txt`

### Installation

```bash
pip install -r requirements.txt
```

### Running the API Server

```bash
python src/risk_management/api/risk_api.py
```

The server will start on `http://localhost:5000`

### Environment Variables

- `RISK_CONFIG_PATH`: Path to risk configuration file
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 5000)

## Monitoring and Logging

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational information
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations

### Key Metrics

- Risk assessment processing time
- Approval/rejection rates
- Risk level distribution
- Configuration update frequency
- API request volume

## Security Considerations

1. **Input Validation**: All inputs are validated and sanitized
2. **Error Handling**: Sensitive information is not exposed in error messages
3. **Rate Limiting**: Consider implementing rate limiting for API endpoints
4. **Authentication**: Add authentication for production deployments
5. **HTTPS**: Use HTTPS in production environments

## Troubleshooting

### Common Issues

1. **Configuration Loading Errors**: Check file permissions and JSON syntax
2. **API Connection Errors**: Verify server is running and port is accessible
3. **Validation Errors**: Check input data format and required fields
4. **Performance Issues**: Monitor processing times and optimize calculations

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Follow the coding protocol in `coding_protocol.md`
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all validations are properly implemented
5. Test error scenarios thoroughly

## Version History

- **v1.0.0**: Initial risk management module implementation
- **v1.1.0**: Added comprehensive validation and error handling
- **v1.2.0**: Integrated risk level calculator and API endpoints 