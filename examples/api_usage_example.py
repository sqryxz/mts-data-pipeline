#!/usr/bin/env python3
"""
Risk Management API Usage Example

This script demonstrates how to use the Risk Management API
for risk assessment and configuration management.
"""

import requests
import json
from datetime import datetime


def test_health_check():
    """Test the health check endpoint."""
    print("=" * 60)
    print("HEALTH CHECK")
    print("=" * 60)
    
    try:
        response = requests.get('http://localhost:5000/health')
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data['status']}")
            print(f"Service: {data['service']}")
            print(f"Timestamp: {data['timestamp']}")
        else:
            print(f"Health check failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("Make sure the server is running on http://localhost:5000")
        return False
    
    return True


def test_basic_risk_assessment():
    """Test basic risk assessment."""
    print("\n" + "=" * 60)
    print("BASIC RISK ASSESSMENT")
    print("=" * 60)
    
    # Prepare request data
    request_data = {
        "signal": {
            "signal_id": "api-example-1",
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
    
    try:
        response = requests.post(
            'http://localhost:5000/assess-risk',
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            assessment = data['assessment']
            
            print(f"Signal: {assessment['signal_id']} - {assessment['asset']} {assessment['signal_type']}")
            print(f"Price: ${assessment['signal_price']:,.2f}")
            print(f"Confidence: {assessment['signal_confidence']:.1%}")
            print()
            print(f"Position Size: ${assessment['recommended_position_size']:,.2f}")
            print(f"Stop Loss: ${assessment['stop_loss_price']:,.2f}")
            print(f"Take Profit: ${assessment['take_profit_price']:,.2f}")
            print(f"Risk/Reward: {assessment['risk_reward_ratio']:.2f}")
            print()
            print(f"Risk Level: {assessment['risk_level']}")
            print(f"Approved: {assessment['is_approved']}")
            print(f"Processing Time: {assessment['processing_time_ms']:.2f}ms")
            
            if assessment['risk_warnings']:
                print("\nRisk Warnings:")
                for warning in assessment['risk_warnings']:
                    print(f"  - {warning}")
                    
        else:
            print(f"Risk assessment failed: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def test_short_signal():
    """Test SHORT signal assessment."""
    print("\n" + "=" * 60)
    print("SHORT SIGNAL ASSESSMENT")
    print("=" * 60)
    
    request_data = {
        "signal": {
            "signal_id": "api-example-short",
            "asset": "BTC",
            "signal_type": "SHORT",
            "price": 50000.0,
            "confidence": 0.7,
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
    
    try:
        response = requests.post(
            'http://localhost:5000/assess-risk',
            json=request_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            assessment = data['assessment']
            
            print(f"Signal Type: {assessment['signal_type']}")
            print(f"Entry Price: ${assessment['signal_price']:,.2f}")
            print(f"Stop Loss: ${assessment['stop_loss_price']:,.2f}")
            print(f"Take Profit: ${assessment['take_profit_price']:,.2f}")
            print(f"Position Size: ${assessment['recommended_position_size']:,.2f}")
            print(f"Risk Level: {assessment['risk_level']}")
            print(f"Approved: {assessment['is_approved']}")
            
        else:
            print(f"SHORT signal assessment failed: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def test_different_assets():
    """Test risk assessment for different assets."""
    print("\n" + "=" * 60)
    print("DIFFERENT ASSETS")
    print("=" * 60)
    
    assets = ["BTC", "ETH", "ADA", "SOL"]
    
    for asset in assets:
        request_data = {
            "signal": {
                "signal_id": f"api-example-{asset}",
                "asset": asset,
                "signal_type": "LONG",
                "price": 50000.0 if asset == "BTC" else 3000.0 if asset == "ETH" else 0.5,
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
        
        try:
            response = requests.post(
                'http://localhost:5000/assess-risk',
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                assessment = data['assessment']
                
                print(f"{asset}: Risk Level = {assessment['risk_level']}, "
                      f"Position Size = ${assessment['recommended_position_size']:,.0f}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {asset}: {e}")


def test_confidence_impact():
    """Test impact of confidence levels."""
    print("\n" + "=" * 60)
    print("CONFIDENCE IMPACT")
    print("=" * 60)
    
    print("Confidence | Position Size | Risk Level | Approved")
    print("-" * 50)
    
    for confidence in [0.1, 0.3, 0.5, 0.7, 0.9]:
        request_data = {
            "signal": {
                "signal_id": f"api-example-conf-{confidence}",
                "asset": "BTC",
                "signal_type": "LONG",
                "price": 50000.0,
                "confidence": confidence,
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
        
        try:
            response = requests.post(
                'http://localhost:5000/assess-risk',
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                assessment = data['assessment']
                
                print(f"{confidence:6.1%}    | ${assessment['recommended_position_size']:8,.0f} | "
                      f"{assessment['risk_level']:9} | {assessment['is_approved']}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for confidence {confidence}: {e}")


def test_portfolio_scenarios():
    """Test different portfolio scenarios."""
    print("\n" + "=" * 60)
    print("PORTFOLIO SCENARIOS")
    print("=" * 60)
    
    scenarios = [
        ("Low Risk", {"total_equity": 10000.0, "current_drawdown": 0.02, "daily_pnl": 200.0}),
        ("Medium Risk", {"total_equity": 10000.0, "current_drawdown": 0.08, "daily_pnl": -50.0}),
        ("High Risk", {"total_equity": 10000.0, "current_drawdown": 0.15, "daily_pnl": -300.0}),
        ("Critical Risk", {"total_equity": 10000.0, "current_drawdown": 0.18, "daily_pnl": -600.0})
    ]
    
    for name, portfolio_state in scenarios:
        request_data = {
            "signal": {
                "signal_id": f"api-example-{name.lower().replace(' ', '-')}",
                "asset": "BTC",
                "signal_type": "LONG",
                "price": 50000.0,
                "confidence": 0.8,
                "timestamp": "2024-01-01T12:00:00Z"
            },
            "portfolio_state": portfolio_state
        }
        
        try:
            response = requests.post(
                'http://localhost:5000/assess-risk',
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                assessment = data['assessment']
                
                print(f"{name}: Risk Level = {assessment['risk_level']}, "
                      f"Approved = {assessment['is_approved']}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {name}: {e}")


def test_configuration():
    """Test configuration management."""
    print("\n" + "=" * 60)
    print("CONFIGURATION MANAGEMENT")
    print("=" * 60)
    
    # Get current configuration
    try:
        response = requests.get('http://localhost:5000/config')
        
        if response.status_code == 200:
            data = response.json()
            config = data['config']
            
            print("Current Configuration:")
            print(f"  Max Drawdown Limit: {config['risk_limits']['max_drawdown_limit']:.1%}")
            print(f"  Daily Loss Limit: {config['risk_limits']['daily_loss_limit']:.1%}")
            print(f"  Base Position Percent: {config['position_sizing']['base_position_percent']:.1%}")
            
        else:
            print(f"Failed to get configuration: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Update configuration
    new_config = {
        "risk_limits": {
            "max_drawdown_limit": 0.15,
            "daily_loss_limit": 0.03
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/config',
            json=new_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nConfiguration updated: {data['message']}")
            
        else:
            print(f"Failed to update configuration: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def test_error_handling():
    """Test error handling."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING")
    print("=" * 60)
    
    # Test invalid signal type
    invalid_request = {
        "signal": {
            "signal_id": "error-test",
            "asset": "BTC",
            "signal_type": "INVALID_TYPE",
            "price": 50000.0,
            "confidence": 0.8
        },
        "portfolio_state": {
            "total_equity": 10000.0,
            "current_drawdown": 0.05,
            "daily_pnl": 100.0
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/assess-risk',
            json=invalid_request,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Invalid signal type test: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"Error message: {data['error']}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    # Test missing required fields
    incomplete_request = {
        "signal": {"signal_id": "incomplete"}
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/assess-risk',
            json=incomplete_request,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Incomplete request test: {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"Error message: {data['error']}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def main():
    """Run all API examples."""
    print("RISK MANAGEMENT API USAGE EXAMPLES")
    print("=" * 60)
    print("This script demonstrates how to use the Risk Management API.")
    print("Make sure the API server is running on http://localhost:5000")
    print()
    
    # Test server connection first
    if not test_health_check():
        print("\nCannot connect to API server. Please start the server first:")
        print("python src/risk_management/api/risk_api.py")
        return
    
    # Run all examples
    test_basic_risk_assessment()
    test_short_signal()
    test_different_assets()
    test_confidence_impact()
    test_portfolio_scenarios()
    test_configuration()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("API EXAMPLES COMPLETE")
    print("=" * 60)
    print("These examples demonstrate:")
    print("- Health check and server connectivity")
    print("- Basic risk assessment workflow")
    print("- SHORT signal processing")
    print("- Multiple asset support")
    print("- Confidence level impact")
    print("- Portfolio scenario testing")
    print("- Configuration management")
    print("- Error handling and validation")


if __name__ == '__main__':
    main() 