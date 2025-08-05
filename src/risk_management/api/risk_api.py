"""
Risk management API endpoints.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from ..core.risk_orchestrator import RiskOrchestrator
from ..models.risk_models import TradingSignal, PortfolioState, SignalType

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize risk orchestrator
risk_orchestrator = RiskOrchestrator()

def parse_timestamp(timestamp_str):
    """Safely parse timestamp string."""
    if not timestamp_str:
        return datetime.now()
    try:
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")

def safe_float(value, field_name, default=0.0):
    """Safely convert to float with error context."""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value for {field_name}: {value}")

def parse_signal_type(signal_type_str):
    """Safely parse signal type enum."""
    try:
        return SignalType(signal_type_str or 'LONG')
    except ValueError:
        valid_types = [e.value for e in SignalType]
        raise ValueError(f"Invalid signal_type: {signal_type_str}. Valid types: {valid_types}")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'risk-management',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/assess-risk', methods=['POST'])
def assess_risk():
    """
    Assess risk for a trading signal.
    
    Expected JSON payload:
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
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'error'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'signal' not in data:
            return jsonify({
                'error': 'Missing signal data',
                'status': 'error'
            }), 400
        
        if 'portfolio_state' not in data:
            return jsonify({
                'error': 'Missing portfolio state data',
                'status': 'error'
            }), 400
        
        # Parse signal data with validation
        signal_data = data['signal']
        signal = TradingSignal(
            signal_id=signal_data.get('signal_id', 'unknown'),
            asset=signal_data.get('asset', 'unknown'),
            signal_type=parse_signal_type(signal_data.get('signal_type')),
            price=safe_float(signal_data.get('price'), 'price'),
            confidence=safe_float(signal_data.get('confidence', 0.5), 'confidence'),
            timestamp=parse_timestamp(signal_data.get('timestamp'))
        )
        
        # Parse portfolio state data with validation
        portfolio_data = data['portfolio_state']
        portfolio_state = PortfolioState(
            total_equity=safe_float(portfolio_data.get('total_equity'), 'total_equity'),
            current_drawdown=safe_float(portfolio_data.get('current_drawdown'), 'current_drawdown'),
            daily_pnl=safe_float(portfolio_data.get('daily_pnl'), 'daily_pnl'),
            positions=portfolio_data.get('positions', {}),
            cash=safe_float(portfolio_data.get('cash'), 'cash')
        )
        
        # Perform risk assessment
        assessment = risk_orchestrator.assess_trade_risk(signal, portfolio_state)
        
        # Convert assessment to JSON-serializable format
        assessment_dict = {
            'signal_id': assessment.signal_id,
            'asset': assessment.asset,
            'signal_type': assessment.signal_type.value if hasattr(assessment.signal_type, 'value') else str(assessment.signal_type),
            'signal_price': assessment.signal_price,
            'signal_confidence': assessment.signal_confidence,
            'timestamp': assessment.timestamp.isoformat() if assessment.timestamp else None,
            
            # Position sizing
            'recommended_position_size': assessment.recommended_position_size,
            'position_size_method': assessment.position_size_method,
            
            # Risk management
            'stop_loss_price': assessment.stop_loss_price,
            'take_profit_price': assessment.take_profit_price,
            
            # Risk metrics
            'risk_reward_ratio': assessment.risk_reward_ratio,
            'position_risk_percent': assessment.position_risk_percent,
            'portfolio_heat': assessment.portfolio_heat,
            'risk_level': assessment.risk_level.value if hasattr(assessment.risk_level, 'value') else str(assessment.risk_level),
            
            # Validation results
            'is_approved': assessment.is_approved,
            'rejection_reason': assessment.rejection_reason,
            'risk_warnings': assessment.risk_warnings or [],
            
            # Market conditions
            'market_volatility': assessment.market_volatility,
            'correlation_risk': assessment.correlation_risk,
            
            # Portfolio impact
            'portfolio_impact': assessment.portfolio_impact or {},
            'current_drawdown': assessment.current_drawdown,
            'daily_pnl_impact': assessment.daily_pnl_impact,
            
            # Configuration used
            'risk_config_snapshot': assessment.risk_config_snapshot or {},
            
            # Processing metadata
            'processing_time_ms': assessment.processing_time_ms
        }
        
        logger.info(f"Risk assessment completed for {signal.asset} {signal.signal_type}")
        
        return jsonify({
            'status': 'success',
            'assessment': assessment_dict
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            'error': f'Validation error: {str(e)}',
            'status': 'error'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in risk assessment: {e}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current risk management configuration."""
    try:
        config = risk_orchestrator.config
        return jsonify({
            'status': 'success',
            'config': config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({
            'error': f'Error retrieving configuration: {str(e)}',
            'status': 'error'
        }), 500


@app.route('/config', methods=['POST'])
def update_config():
    """Update risk management configuration."""
    try:
        if not request.is_json:
            return jsonify({
                'error': 'Request must be JSON',
                'status': 'error'
            }), 400
        
        new_config = request.get_json()
        
        # Validate config structure here if needed
        
        # Update orchestrator with new config
        global risk_orchestrator
        risk_orchestrator = RiskOrchestrator(config=new_config)  # ✅ Actually use the config
        
        logger.info("Risk management configuration updated")
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return jsonify({
            'error': 'Error updating configuration',
            'status': 'error'
        }), 500


if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 