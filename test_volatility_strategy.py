#!/usr/bin/env python3

"""
Test script for the Volatility Strategy implementation.
Demonstrates how to use the volatility-based signal generation module.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.signals.strategies.volatility_strategy import VolatilityStrategy
from src.data.sqlite_helper import CryptoDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_volatility_strategy():
    """Test the volatility strategy with real market data."""
    
    print("=== Volatility Strategy Test ===\n")
    
    try:
        # Initialize the strategy
        config_path = "config/strategies/volatility_strategy.json"
        strategy = VolatilityStrategy(config_path)
        
        print(f"Strategy initialized with parameters:")
        params = strategy.get_parameters()
        for key, value in params.items():
            print(f"  {key}: {value}")
        print()
        
        # Get market data
        database = CryptoDatabase()
        market_data = database.get_strategy_market_data(
            assets=params['assets'], 
            days=params['historical_days']
        )
        
        print(f"Retrieved market data for {len(market_data)} assets:")
        for asset, df in market_data.items():
            if asset in ['bitcoin', 'ethereum'] and not df.empty:
                print(f"  {asset}: {len(df)} records from {df['date_str'].min()} to {df['date_str'].max()}")
        print()
        
        # Run analysis
        print("Running volatility analysis...")
        analysis_results = strategy.analyze(market_data)
        
        print(f"Analysis complete. Found {len(analysis_results['opportunities'])} opportunities")
        print()
        
        # Display volatility metrics
        print("Volatility Metrics:")
        for asset, metrics in analysis_results['volatility_metrics'].items():
            print(f"  {asset}:")
            print(f"    Current Volatility: {metrics['current_volatility']:.2%}")
            print(f"    Historical Threshold: {metrics['historical_threshold']:.2%}")
            print(f"    Extreme Threshold: {metrics['extreme_threshold']:.2%}")
            print(f"    Volatility Percentile: {metrics['volatility_percentile']:.1f}%")
            print()
        
        # Generate signals
        print("Generating trading signals...")
        signals = strategy.generate_signals(analysis_results)
        
        print(f"Generated {len(signals)} trading signals:")
        for i, signal in enumerate(signals, 1):
            print(f"  Signal {i}:")
            print(f"    Asset: {signal.asset}")
            print(f"    Type: {signal.signal_type.value}")
            print(f"    Price: ${signal.price:,.2f}")
            print(f"    Strength: {signal.signal_strength.value}")
            print(f"    Confidence: {signal.confidence:.3f}")
            print(f"    Position Size: {signal.position_size:.1%}")
            if signal.stop_loss:
                print(f"    Stop Loss: ${signal.stop_loss:,.2f}")
            if signal.take_profit:
                print(f"    Take Profit: ${signal.take_profit:,.2f}")
            
            # Display analysis data
            if signal.analysis_data:
                print(f"    Volatility: {signal.analysis_data['volatility']:.2%}")
                print(f"    Threshold: {signal.analysis_data['volatility_threshold']:.2%}")
                print(f"    Reason: {signal.analysis_data['reason']}")
            print()
        
        return signals
        
    except Exception as e:
        print(f"Error testing volatility strategy: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_strategy_integration():
    """Test the strategy integration with the multi-strategy generator."""
    
    print("=== Strategy Integration Test ===\n")
    
    try:
        from src.services.multi_strategy_generator import MultiStrategyGenerator
        
        # Create strategy configuration
        strategy_configs = {
            'volatility': {
                'config_path': 'config/strategies/volatility_strategy.json'
            }
        }
        
        # Create aggregator configuration
        aggregator_config = {
            'strategy_weights': {
                'volatility': 1.0
            },
            'aggregation_config': {
                'max_position_size': 0.05,
                'conflict_resolution': 'weighted_average'
            }
        }
        
        # Initialize multi-strategy generator
        generator = MultiStrategyGenerator(strategy_configs, aggregator_config)
        
        print("Multi-strategy generator initialized successfully")
        print()
        
        # Generate aggregated signals
        print("Generating aggregated signals...")
        signals = generator.generate_aggregated_signals(days=30)
        
        print(f"Generated {len(signals)} aggregated signals")
        for signal in signals:
            print(f"  {signal.signal_type.value} {signal.asset} at ${signal.price:,.2f} "
                  f"(confidence: {signal.confidence:.3f})")
        
        return signals
        
    except Exception as e:
        print(f"Error testing strategy integration: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("Testing Volatility Strategy Implementation\n")
    
    # Test 1: Basic strategy functionality
    print("Test 1: Basic Strategy Functionality")
    print("=" * 50)
    signals1 = test_volatility_strategy()
    
    print("\n" + "=" * 50 + "\n")
    
    # Test 2: Strategy integration
    print("Test 2: Strategy Integration")
    print("=" * 50)
    signals2 = test_strategy_integration()
    
    print("\n" + "=" * 50)
    print("Testing Complete!")
    print(f"Total signals generated: {len(signals1) + len(signals2)}") 