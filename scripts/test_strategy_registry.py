#!/usr/bin/env python3
"""
Test Strategy Registry
Debug script to check what strategies are available in the registry.
"""

import sys
import os

# Add src and root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.signals.strategies.strategy_registry import StrategyRegistry
from src.services.multi_strategy_generator import create_default_multi_strategy_generator

def test_strategy_registry():
    """Test the strategy registry to see what strategies are available."""
    print("🔍 Testing Strategy Registry")
    print("=" * 50)
    
    try:
        # Create strategy registry
        registry = StrategyRegistry()
        
        # Load strategies from directory
        strategies_dir = "src/signals/strategies"
        print(f"📁 Loading strategies from: {strategies_dir}")
        registry.load_strategies_from_directory(strategies_dir)
        
        # List available strategies
        strategies = registry.list_strategies()
        print(f"\n📊 Available strategies: {list(strategies.keys())}")
        
        for name, strategy_class in strategies.items():
            print(f"   ✅ {name}: {strategy_class.__name__}")
        
        return strategies
        
    except Exception as e:
        print(f"❌ Error testing strategy registry: {e}")
        return None

def test_multi_strategy_generator():
    """Test the multi-strategy generator."""
    print("\n🔧 Testing Multi-Strategy Generator")
    print("=" * 50)
    
    try:
        # Create multi-strategy generator
        generator = create_default_multi_strategy_generator()
        
        # Get strategy status
        status = generator.get_strategy_status()
        
        print(f"📊 Total strategies: {status['total_strategies']}")
        print(f"📋 Loaded strategies: {status['loaded_strategies']}")
        print(f"📋 Registry strategies: {status['registry_strategies']}")
        
        return generator
        
    except Exception as e:
        print(f"❌ Error testing multi-strategy generator: {e}")
        return None

def main():
    """Run all tests."""
    print("🚀 Strategy Registry Test Suite")
    print("=" * 60)
    
    # Test strategy registry
    strategies = test_strategy_registry()
    
    if strategies:
        print(f"\n✅ Strategy registry test passed. Found {len(strategies)} strategies.")
    else:
        print("\n❌ Strategy registry test failed.")
        return
    
    # Test multi-strategy generator
    generator = test_multi_strategy_generator()
    
    if generator:
        print(f"\n✅ Multi-strategy generator test passed.")
    else:
        print("\n❌ Multi-strategy generator test failed.")

if __name__ == "__main__":
    main()
