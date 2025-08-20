#!/usr/bin/env python3
"""
Risk Management Module Examples
"""

import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.risk_management.models.risk_models import (
    TradingSignal, PortfolioState, SignalType
)
from src.risk_management.core.risk_orchestrator import RiskOrchestrator


def example_basic_risk_assessment():
    """Example 1: Basic Risk Assessment"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Risk Assessment")
    print("=" * 60)
    
    orchestrator = RiskOrchestrator()
    
    signal = TradingSignal(
        signal_id="example-1",
        asset="BTC",
        signal_type=SignalType.LONG,
        price=50000.0,
        confidence=0.8,
        timestamp=datetime.now()
    )
    
    portfolio = PortfolioState(
        total_equity=10000.0,
        current_drawdown=0.05,
        daily_pnl=100.0,
        positions={"BTC": 0.1},
        cash=9000.0
    )
    
    assessment = orchestrator.assess_trade_risk(signal, portfolio)
    
    print(f"Signal: {assessment.signal_id} - {assessment.asset} {assessment.signal_type.value}")
    print(f"Price: ${assessment.signal_price:,.2f}")
    print(f"Confidence: {assessment.signal_confidence:.1%}")
    print()
    print(f"Position Size: ${assessment.recommended_position_size:,.2f}")
    print(f"Stop Loss: ${assessment.stop_loss_price:,.2f}")
    print(f"Take Profit: ${assessment.take_profit_price:,.2f}")
    print(f"Risk/Reward: {assessment.risk_reward_ratio:.2f}")
    print()
    print(f"Risk Level: {assessment.risk_level.value}")
    print(f"Approved: {assessment.is_approved}")
    print(f"Processing Time: {assessment.processing_time_ms:.2f}ms")


def example_risk_scenarios():
    """Example 2: Different Risk Scenarios"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Different Risk Scenarios")
    print("=" * 60)
    
    orchestrator = RiskOrchestrator()
    
    base_signal = TradingSignal(
        signal_id="scenario-test",
        asset="BTC",
        signal_type=SignalType.LONG,
        price=50000.0,
        confidence=0.8
    )
    
    scenarios = [
        ("Low Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.02, daily_pnl=200.0)),
        ("Medium Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.08, daily_pnl=-50.0)),
        ("High Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.15, daily_pnl=-300.0)),
        ("Critical Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.18, daily_pnl=-600.0))
    ]
    
    for name, portfolio in scenarios:
        assessment = orchestrator.assess_trade_risk(base_signal, portfolio)
        print(f"{name}: Risk Level = {assessment.risk_level.value}, Approved = {assessment.is_approved}")


def example_confidence_impact():
    """Example 3: Impact of Signal Confidence"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Impact of Signal Confidence")
    print("=" * 60)
    
    orchestrator = RiskOrchestrator()
    portfolio = PortfolioState(total_equity=10000.0, current_drawdown=0.05, daily_pnl=100.0)
    
    print("Confidence | Position Size | Risk Level | Approved")
    print("-" * 50)
    
    for confidence in [0.1, 0.3, 0.5, 0.7, 0.9]:
        signal = TradingSignal(
            signal_id=f"conf-{confidence}",
            asset="BTC",
            signal_type=SignalType.LONG,
            price=50000.0,
            confidence=confidence
        )
        
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        print(f"{confidence:6.1%}    | ${assessment.recommended_position_size:8,.0f} | "
              f"{assessment.risk_level.value:9} | {assessment.is_approved}")


def example_short_signals():
    """Example 4: SHORT Signal Analysis"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: SHORT Signal Analysis")
    print("=" * 60)
    
    orchestrator = RiskOrchestrator()
    
    short_signal = TradingSignal(
        signal_id="short-example",
        asset="BTC",
        signal_type=SignalType.SHORT,
        price=50000.0,
        confidence=0.7
    )
    
    portfolio = PortfolioState(total_equity=10000.0, current_drawdown=0.05, daily_pnl=100.0)
    assessment = orchestrator.assess_trade_risk(short_signal, portfolio)
    
    print(f"Signal Type: {assessment.signal_type.value}")
    print(f"Entry Price: ${assessment.signal_price:,.2f}")
    print(f"Stop Loss: ${assessment.stop_loss_price:,.2f}")
    print(f"Take Profit: ${assessment.take_profit_price:,.2f}")
    print(f"Position Size: ${assessment.recommended_position_size:,.2f}")
    print(f"Risk Level: {assessment.risk_level.value}")


def example_custom_configuration():
    """Example 5: Custom Configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Custom Configuration")
    print("=" * 60)
    
    conservative_config = {
        "risk_limits": {"max_drawdown_limit": 0.10, "daily_loss_limit": 0.02},
        "position_sizing": {"base_position_percent": 0.01, "max_position_percent": 0.05}
    }
    
    aggressive_config = {
        "risk_limits": {"max_drawdown_limit": 0.30, "daily_loss_limit": 0.08},
        "position_sizing": {"base_position_percent": 0.05, "max_position_percent": 0.20}
    }
    
    signal = TradingSignal(
        signal_id="config-test",
        asset="BTC",
        signal_type=SignalType.LONG,
        price=50000.0,
        confidence=0.8
    )
    
    portfolio = PortfolioState(total_equity=10000.0, current_drawdown=0.05, daily_pnl=100.0)
    
    conservative_orchestrator = RiskOrchestrator(config=conservative_config)
    conservative_assessment = conservative_orchestrator.assess_trade_risk(signal, portfolio)
    
    aggressive_orchestrator = RiskOrchestrator(config=aggressive_config)
    aggressive_assessment = aggressive_orchestrator.assess_trade_risk(signal, portfolio)
    
    print("Configuration Comparison:")
    print("-" * 40)
    print(f"Position Size: ${conservative_assessment.recommended_position_size:,.0f} vs "
          f"${aggressive_assessment.recommended_position_size:,.0f}")
    print(f"Risk Level: {conservative_assessment.risk_level.value} vs "
          f"{aggressive_assessment.risk_level.value}")
    print(f"Approved: {conservative_assessment.is_approved} vs {aggressive_assessment.is_approved}")


def main():
    """Run all examples."""
    print("RISK MANAGEMENT MODULE EXAMPLES")
    print("=" * 60)
    
    example_basic_risk_assessment()
    example_risk_scenarios()
    example_confidence_impact()
    example_short_signals()
    example_custom_configuration()
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main() 