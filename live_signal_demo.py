#!/usr/bin/env python3

"""
Live Signal Demonstration - Volatility Strategy
Shows real signal outputs from live data over multiple time periods.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signals.strategies.volatility_strategy import VolatilityStrategy
from src.data.sqlite_helper import CryptoDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_historical_signals(days_list=[7, 14, 30, 60, 90]):
    """Generate signals for different historical periods."""
    
    print("🔍 Generating Historical Signals from Live Data")
    print("=" * 60)
    print()
    
    strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
    database = CryptoDatabase()
    
    all_signals = []
    
    for days in days_list:
        print(f"📊 Analyzing {days} days of historical data...")
        
        try:
            # Get market data
            market_data = database.get_strategy_market_data(
                assets=['bitcoin', 'ethereum'], 
                days=days
            )
            
            # Run analysis
            analysis_results = strategy.analyze(market_data)
            
            # Generate signals
            signals = strategy.generate_signals(analysis_results)
            
            print(f"✅ Generated {len(signals)} signals for {days}-day period")
            
            # Display signals
            for i, signal in enumerate(signals, 1):
                print(f"  Signal {i}:")
                print(f"    📈 Asset: {signal.asset.capitalize()}")
                print(f"    🎯 Type: {signal.signal_type.value}")
                print(f"    💰 Price: ${signal.price:,.2f}")
                print(f"    💪 Strength: {signal.signal_strength.value}")
                print(f"    🎯 Confidence: {signal.confidence:.1%}")
                print(f"    📊 Position Size: {signal.position_size:.1%}")
                
                if signal.analysis_data:
                    print(f"    📈 Volatility: {signal.analysis_data['volatility']:.2%}")
                    print(f"    📊 Threshold: {signal.analysis_data['volatility_threshold']:.2%}")
                    print(f"    📈 Ratio: {signal.analysis_data['volatility_ratio']:.2f}x")
                    print(f"    💡 Reason: {signal.analysis_data['reason']}")
                
                print()
            
            all_signals.extend(signals)
            
        except Exception as e:
            print(f"❌ Error analyzing {days}-day period: {e}")
            continue
    
    return all_signals

def get_detailed_volatility_analysis():
    """Perform detailed volatility analysis with metrics."""
    
    print("📊 Detailed Volatility Analysis")
    print("=" * 50)
    print()
    
    strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
    database = CryptoDatabase()
    
    # Get 60 days of data for comprehensive analysis
    market_data = database.get_strategy_market_data(['bitcoin', 'ethereum'], 60)
    
    # Run analysis
    analysis_results = strategy.analyze(market_data)
    
    print("📈 Volatility Metrics by Asset:")
    print()
    
    for asset, metrics in analysis_results['volatility_metrics'].items():
        print(f"🔸 {asset.capitalize()}:")
        print(f"   Current Volatility: {metrics['current_volatility']:.2%}")
        print(f"   Historical Mean: {metrics['historical_volatility_mean']:.2%}")
        print(f"   Historical Std: {metrics['historical_volatility_std']:.2%}")
        print(f"   Normal Threshold (95%): {metrics['historical_threshold']:.2%}")
        print(f"   Extreme Threshold (98%): {metrics['extreme_threshold']:.2%}")
        print(f"   Current Percentile: {metrics['volatility_percentile']:.1f}%")
        
        # Calculate volatility ratio
        if metrics['historical_volatility_mean'] > 0:
            ratio = metrics['current_volatility'] / metrics['historical_volatility_mean']
            print(f"   Volatility Ratio: {ratio:.2f}x historical mean")
        
        print()
    
    return analysis_results

def get_signal_statistics(signals):
    """Analyze signal statistics."""
    
    print("📊 Signal Statistics")
    print("=" * 40)
    print()
    
    if not signals:
        print("❌ No signals generated")
        return
    
    # Group by asset
    asset_signals = {}
    for signal in signals:
        if signal.asset not in asset_signals:
            asset_signals[signal.asset] = []
        asset_signals[signal.asset].append(signal)
    
    print(f"📈 Total Signals: {len(signals)}")
    print()
    
    for asset, asset_sigs in asset_signals.items():
        print(f"🔸 {asset.capitalize()}: {len(asset_sigs)} signals")
        
        # Count by signal type
        long_signals = [s for s in asset_sigs if s.signal_type.value == 'LONG']
        short_signals = [s for s in asset_sigs if s.signal_type.value == 'SHORT']
        
        print(f"   LONG: {len(long_signals)}")
        print(f"   SHORT: {len(short_signals)}")
        
        # Average confidence
        avg_confidence = sum(s.confidence for s in asset_sigs) / len(asset_sigs)
        print(f"   Avg Confidence: {avg_confidence:.1%}")
        
        # Average position size
        avg_position = sum(s.position_size for s in asset_sigs) / len(asset_sigs)
        print(f"   Avg Position Size: {avg_position:.1%}")
        
        print()
    
    # Overall statistics
    signal_types = [s.signal_type.value for s in signals]
    long_count = signal_types.count('LONG')
    short_count = signal_types.count('SHORT')
    
    print(f"📊 Overall Statistics:")
    print(f"   LONG Signals: {long_count} ({long_count/len(signals)*100:.1f}%)")
    print(f"   SHORT Signals: {short_count} ({short_count/len(signals)*100:.1f}%)")
    
    avg_confidence = sum(s.confidence for s in signals) / len(signals)
    print(f"   Average Confidence: {avg_confidence:.1%}")
    
    avg_position = sum(s.position_size for s in signals) / len(signals)
    print(f"   Average Position Size: {avg_position:.1%}")

def demonstrate_real_time_simulation():
    """Simulate real-time signal generation over multiple periods."""
    
    print("🔄 Real-Time Signal Simulation")
    print("=" * 50)
    print()
    
    strategy = VolatilityStrategy("config/strategies/volatility_strategy.json")
    database = CryptoDatabase()
    
    # Simulate multiple time periods
    periods = [
        {"name": "Last Week", "days": 7},
        {"name": "Last 2 Weeks", "days": 14},
        {"name": "Last Month", "days": 30},
        {"name": "Last 2 Months", "days": 60},
        {"name": "Last 3 Months", "days": 90}
    ]
    
    all_period_signals = []
    
    for period in periods:
        print(f"⏰ {period['name']} Analysis:")
        print("-" * 30)
        
        try:
            # Get market data for this period
            market_data = database.get_strategy_market_data(
                assets=['bitcoin', 'ethereum'], 
                days=period['days']
            )
            
            # Run analysis
            analysis_results = strategy.analyze(market_data)
            signals = strategy.generate_signals(analysis_results)
            
            print(f"📊 Found {len(analysis_results['opportunities'])} opportunities")
            print(f"🎯 Generated {len(signals)} signals")
            
            # Show signal details
            for i, signal in enumerate(signals, 1):
                print(f"  Signal {i}: {signal.signal_type.value} {signal.asset.capitalize()}")
                print(f"    Price: ${signal.price:,.2f}")
                print(f"    Confidence: {signal.confidence:.1%}")
                print(f"    Position: {signal.position_size:.1%}")
                
                if signal.analysis_data:
                    print(f"    Volatility: {signal.analysis_data['volatility']:.2%}")
                    print(f"    Ratio: {signal.analysis_data['volatility_ratio']:.2f}x")
            
            all_period_signals.extend(signals)
            print()
            
        except Exception as e:
            print(f"❌ Error in {period['name']}: {e}")
            print()
    
    return all_period_signals

def main():
    """Main demonstration function."""
    
    print("🎯 Live Signal Demonstration - Volatility Strategy")
    print("=" * 70)
    print()
    print("This demonstration shows real signal outputs from live data")
    print("across multiple time periods and analysis scenarios.")
    print()
    
    # Demo 1: Historical signals
    print("Demo 1: Historical Signal Generation")
    print("=" * 50)
    historical_signals = get_historical_signals()
    
    print("\n" + "=" * 70 + "\n")
    
    # Demo 2: Detailed volatility analysis
    print("Demo 2: Detailed Volatility Analysis")
    print("=" * 50)
    volatility_analysis = get_detailed_volatility_analysis()
    
    print("\n" + "=" * 70 + "\n")
    
    # Demo 3: Real-time simulation
    print("Demo 3: Real-Time Signal Simulation")
    print("=" * 50)
    realtime_signals = demonstrate_real_time_simulation()
    
    print("\n" + "=" * 70 + "\n")
    
    # Demo 4: Signal statistics
    print("Demo 4: Signal Statistics")
    print("=" * 50)
    all_signals = historical_signals + realtime_signals
    get_signal_statistics(all_signals)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 LIVE DEMONSTRATION SUMMARY")
    print("=" * 70)
    print(f"✅ Historical Signals: {len(historical_signals)}")
    print(f"✅ Real-Time Signals: {len(realtime_signals)}")
    print(f"✅ Total Signals Generated: {len(all_signals)}")
    print(f"✅ Volatility Analysis: Complete")
    print(f"✅ Signal Statistics: Calculated")
    print()
    print("🎉 Live demonstration completed successfully!")
    print()
    print("The volatility strategy is generating real signals based on:")
    print("• Live market data from your database")
    print("• Historical volatility thresholds")
    print("• Dynamic position sizing")
    print("• Risk-adjusted stop losses and take profits")

if __name__ == "__main__":
    main() 