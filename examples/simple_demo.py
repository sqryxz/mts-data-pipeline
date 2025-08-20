#!/usr/bin/env python3
"""
Simple Risk Management Demo

A quick demonstration of the Risk Management Module functionality.
"""

import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.risk_management.models.risk_models import TradingSignal, PortfolioState, SignalType
from src.risk_management.core.risk_orchestrator import RiskOrchestrator


def demo_basic_usage():
    """Demonstrate basic usage of the risk management module."""
    print("RISK MANAGEMENT MODULE DEMO")
    print("=" * 50)
    
    # Initialize the risk orchestrator
    orchestrator = RiskOrchestrator()
    
    # Create a trading signal
    signal = TradingSignal(
        signal_id="demo-signal",
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
    
    # Perform risk assessment
    assessment = orchestrator.assess_trade_risk(signal, portfolio)
    
    # Display results
    print(f"Signal: {signal.asset} {signal.signal_type.value} @ ${signal.price:,.2f}")
    print(f"Confidence: {signal.confidence:.1%}")
    print()
    print(f"Position Size: ${assessment.recommended_position_size:,.2f}")
    print(f"Stop Loss: ${assessment.stop_loss_price:,.2f}")
    print(f"Take Profit: ${assessment.take_profit_price:,.2f}")
    print(f"Risk/Reward: {assessment.risk_reward_ratio:.2f}")
    print()
    print(f"Risk Level: {assessment.risk_level.value}")
    print(f"Approved: {assessment.is_approved}")
    
    if assessment.risk_warnings:
        print("\nWarnings:")
        for warning in assessment.risk_warnings:
            print(f"  - {warning}")


def demo_risk_levels():
    """Demonstrate different risk levels."""
    print("\n" + "=" * 50)
    print("RISK LEVEL DEMONSTRATION")
    print("=" * 50)
    
    orchestrator = RiskOrchestrator()
    
    # Test different portfolio scenarios
    scenarios = [
        ("Low Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.02, daily_pnl=200.0)),
        ("Medium Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.08, daily_pnl=-50.0)),
        ("High Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.15, daily_pnl=-300.0)),
        ("Critical Risk", PortfolioState(total_equity=10000.0, current_drawdown=0.18, daily_pnl=-600.0))
    ]
    
    signal = TradingSignal(
        signal_id="risk-demo",
        asset="BTC",
        signal_type=SignalType.LONG,
        price=50000.0,
        confidence=0.8
    )
    
    for name, portfolio in scenarios:
        assessment = orchestrator.assess_trade_risk(signal, portfolio)
        print(f"{name}: {assessment.risk_level.value} (Approved: {assessment.is_approved})")


def demo_confidence_impact():
    """Demonstrate impact of confidence levels."""
    print("\n" + "=" * 50)
    print("CONFIDENCE IMPACT DEMONSTRATION")
    print("=" * 50)
    
    orchestrator = RiskOrchestrator()
    portfolio = PortfolioState(total_equity=10000.0, current_drawdown=0.05, daily_pnl=100.0)
    
    print("Confidence | Position Size | Risk Level")
    print("-" * 40)
    
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
              f"{assessment.risk_level.value}")


def demo_short_signals():
    """Demonstrate SHORT signal analysis."""
    print("\n" + "=" * 50)
    print("SHORT SIGNAL DEMONSTRATION")
    print("=" * 50)
    
    orchestrator = RiskOrchestrator()
    portfolio = PortfolioState(total_equity=10000.0, current_drawdown=0.05, daily_pnl=100.0)
    
    # LONG signal
    long_signal = TradingSignal(
        signal_id="long-demo",
        asset="BTC",
        signal_type=SignalType.LONG,
        price=50000.0,
        confidence=0.8
    )
    
    long_assessment = orchestrator.assess_trade_risk(long_signal, portfolio)
    
    # SHORT signal
    short_signal = TradingSignal(
        signal_id="short-demo",
        asset="BTC",
        signal_type=SignalType.SHORT,
        price=50000.0,
        confidence=0.8
    )
    
    short_assessment = orchestrator.assess_trade_risk(short_signal, portfolio)
    
    print("LONG Signal:")
    print(f"  Entry: ${long_signal.price:,.2f}")
    print(f"  Stop Loss: ${long_assessment.stop_loss_price:,.2f} (below entry)")
    print(f"  Take Profit: ${long_assessment.take_profit_price:,.2f} (above entry)")
    print()
    print("SHORT Signal:")
    print(f"  Entry: ${short_signal.price:,.2f}")
    print(f"  Stop Loss: ${short_assessment.stop_loss_price:,.2f} (above entry)")
    print(f"  Take Profit: ${short_assessment.take_profit_price:,.2f} (below entry)")


def main():
    """Run the demo."""
    try:
        demo_basic_usage()
        demo_risk_levels()
        demo_confidence_impact()
        demo_short_signals()
        
        print("\n" + "=" * 50)
        print("DEMO COMPLETE")
        print("=" * 50)
        print("This demo showed:")
        print("- Basic risk assessment workflow")
        print("- Different risk levels based on portfolio state")
        print("- Impact of signal confidence on position sizing")
        print("- LONG vs SHORT signal analysis")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("Make sure all dependencies are installed and the module is properly configured.")


if __name__ == '__main__':
    main() 