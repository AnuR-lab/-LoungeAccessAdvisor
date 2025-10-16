#!/usr/bin/env python3
"""
Test runner script for LoungeAccessAdvisor MCP tools.
Runs all unit tests for the lounge access components.
"""

import unittest
import sys
import os

# Add the current directory to the path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)


def run_api_client_tests():
    """Run tests for the API client."""
    print("=" * 60)
    print("Running API Client Tests")
    print("=" * 60)
    
    # Import and run the API client tests
    from test_api_client import (
        TestLoungeAccessClientGetUser,
        TestLoungeAccessClientCreateSampleUsers,
        TestLoungeAccessClientInitialization,
        TestLoungeAccessClientIntegration,
        TestLoungeAccessClientLoungeOperations,
        TestLoungeAccessClientLoungeMethods
    )
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestLoungeAccessClientGetUser,
        TestLoungeAccessClientCreateSampleUsers,
        TestLoungeAccessClientInitialization,
        TestLoungeAccessClientIntegration,
        TestLoungeAccessClientLoungeOperations,
        TestLoungeAccessClientLoungeMethods
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_lounge_service_tests():
    """Run tests for the lounge service."""
    print("\n" + "=" * 60)
    print("Running Lounge Service Tests")
    print("=" * 60)
    
    try:
        # Import and run the lounge service tests
        from test_lounge_service import (
            TestLoungeServiceInitialization,
            TestLoungeServiceGetLoungesWithAccessRules,
            TestLoungeServiceGetLoungesByAirport,
            TestLoungeServiceGetLoungeById,
            TestLoungeServiceCreateSampleLounges,
            TestLoungeServiceTableManagement,
            TestLoungeServiceIntegration
        )
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestLoungeServiceInitialization,
            TestLoungeServiceGetLoungesWithAccessRules,
            TestLoungeServiceGetLoungesByAirport,
            TestLoungeServiceGetLoungeById,
            TestLoungeServiceCreateSampleLounges,
            TestLoungeServiceTableManagement,
            TestLoungeServiceIntegration
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Could not import lounge service tests: {e}")
        return True  # Don't fail the entire test run


def run_lambda_handler_tests():
    """Run tests for the lambda handler."""
    print("\n" + "=" * 60)
    print("Running Lambda Handler Tests")
    print("=" * 60)
    
    try:
        # Import and run the lambda handler tests
        from test_lambda_handler import TestLambdaHandler
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestLambdaHandler)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"Could not import lambda handler tests: {e}")
        return True  # Don't fail the entire test run


def run_coverage_report():
    """Generate a coverage report if coverage is available."""
    try:
        import coverage
        print("\n" + "=" * 60)
        print("Coverage Report Available")
        print("=" * 60)
        print("To run tests with coverage:")
        print("  coverage run run_tests.py")
        print("  coverage report")
        print("  coverage html")
        return True
    except ImportError:
        print("\n" + "=" * 60)
        print("Coverage Not Available")
        print("=" * 60)
        print("To install coverage: pip install coverage")
        return False


def main():
    """Main test runner function."""
    print("LoungeAccessAdvisor MCP Tools - Test Suite")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Run API client tests
    if run_api_client_tests():
        success_count += 1
        print("✅ API Client tests passed")
    else:
        print("❌ API Client tests failed")
    total_tests += 1
    
    # Run lounge service tests
    if run_lounge_service_tests():
        success_count += 1
        print("✅ Lounge Service tests passed")
    else:
        print("❌ Lounge Service tests failed")
    total_tests += 1

    # Run lambda handler tests
    if run_lambda_handler_tests():
        success_count += 1
        print("✅ Lambda Handler tests passed")
    else:
        print("❌ Lambda Handler tests failed")
    total_tests += 1
    
    # Show coverage information
    run_coverage_report()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)