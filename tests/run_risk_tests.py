#!/usr/bin/env python3
"""
Test runner for the Risk Management Module.

This script runs all tests for the risk management system.
"""

import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def run_unit_tests():
    """Run unit tests."""
    print("Running unit tests...")
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'unit')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_integration_tests():
    """Run integration tests."""
    print("Running integration tests...")
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'integration')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_api_tests():
    """Run API tests."""
    print("Running API tests...")
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'api')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RISK MANAGEMENT MODULE TEST SUITE")
    print("=" * 60)
    
    # Run unit tests
    unit_success = run_unit_tests()
    print()
    
    # Run integration tests
    integration_success = run_integration_tests()
    print()
    
    # Run API tests
    api_success = run_api_tests()
    print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Unit Tests: {'PASSED' if unit_success else 'FAILED'}")
    print(f"Integration Tests: {'PASSED' if integration_success else 'FAILED'}")
    print(f"API Tests: {'PASSED' if api_success else 'FAILED'}")
    
    overall_success = unit_success and integration_success and api_success
    print(f"Overall Result: {'PASSED' if overall_success else 'FAILED'}")
    print("=" * 60)
    
    return overall_success

def run_specific_test(test_type):
    """Run a specific type of test."""
    if test_type == 'unit':
        return run_unit_tests()
    elif test_type == 'integration':
        return run_integration_tests()
    elif test_type == 'api':
        return run_api_tests()
    else:
        print(f"Unknown test type: {test_type}")
        print("Available types: unit, integration, api")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        success = run_specific_test(test_type)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1) 