#!/usr/bin/env python3
"""
Integration test runner for risk management module.
"""

import sys
import os
import pytest
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run integration tests for risk management module."""
    print("🧪 Running Risk Management Integration Tests")
    print("=" * 50)
    
    # Test file path
    test_file = Path(__file__).parent / "test_integration.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    # Run tests with verbose output
    args = [
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    print(f"📁 Test file: {test_file}")
    print(f"🔧 Arguments: {' '.join(args)}")
    print()
    
    # Run pytest
    exit_code = pytest.main(args)
    
    print()
    if exit_code == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed!")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 