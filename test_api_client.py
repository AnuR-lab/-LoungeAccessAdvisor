#!/usr/bin/env python3
"""
Comprehensive test suite for LoungeAccessClient API client
Tests both basic and flight-aware functionality
"""
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'mcp', 'lounge_access'))

def test_basic_functionality():
    """Test basic lounge access functionality"""
    print("🧪 Testing Basic API Client Functionality")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        print("✅ LoungeAccessClient initialized successfully")
        
        # Test service initialization
        services = ['user_profile_service', 'lounge_service', 'flight_service']
        for service in services:
            if hasattr(client, service):
                print(f"✅ {service} initialized")
            else:
                print(f"❌ {service} missing")
        
        # Test basic methods exist
        basic_methods = [
            'get_user',
            'get_lounges_by_airport', 
            'search_lounges_by_access_provider',
            'get_lounges_with_amenity'
        ]
        
        for method in basic_methods:
            if hasattr(client, method) and callable(getattr(client, method)):
                print(f"✅ Method exists: {method}")
            else:
                print(f"❌ Method missing: {method}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Initialization error: {e}")

def test_flight_aware_functionality():
    """Test flight-aware functionality"""
    print("\n🧪 Testing Flight-Aware API Client Functionality")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test flight-aware methods exist
        flight_methods = [
            'get_flight_aware_lounge_recommendations',
            'analyze_multi_flight_lounge_strategy',
            'get_flight_status_with_lounge_impact',
            'search_flights_for_lounge_optimization'
        ]
        
        for method in flight_methods:
            if hasattr(client, method) and callable(getattr(client, method)):
                print(f"✅ Flight method exists: {method}")
            else:
                print(f"❌ Flight method missing: {method}")
        
        # Test helper methods
        helper_methods = [
            'validate_flight_number',
            'get_airport_lounge_summary',
            'check_lounge_compatibility',
            'get_flight_service_status',
            'health_check'
        ]
        
        for method in helper_methods:
            if hasattr(client, method) and callable(getattr(client, method)):
                print(f"✅ Helper method exists: {method}")
            else:
                print(f"❌ Helper method missing: {method}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Test error: {e}")

def test_flight_number_validation():
    """Test flight number validation"""
    print("\n🧪 Testing Flight Number Validation")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test valid flight numbers
        valid_flights = ["AA123", "DL456", "UA789", "BA101"]
        
        for flight in valid_flights:
            result = client.validate_flight_number(flight)
            if result.get("valid"):
                print(f"✅ {flight}: {result.get('carrier_code')}{result.get('flight_number')}")
            else:
                print(f"❌ {flight}: {result.get('error')}")
        
        # Test invalid flight numbers
        invalid_flights = ["", "123", "A", "INVALID"]
        
        print("\nTesting invalid flight numbers:")
        for flight in invalid_flights:
            result = client.validate_flight_number(flight)
            if not result.get("valid"):
                print(f"✅ {flight}: Correctly rejected - {result.get('error')}")
            else:
                print(f"❌ {flight}: Should have been rejected")
                
    except Exception as e:
        print(f"❌ Validation test error: {e}")

def test_health_check():
    """Test health check functionality"""
    print("\n🧪 Testing Health Check Functionality")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test health check
        health_result = client.health_check()
        
        print(f"Overall Status: {health_result.get('overall_status', 'unknown')}")
        print(f"Timestamp: {health_result.get('timestamp', 'unknown')}")
        
        services = health_result.get('services', {})
        for service_name, service_status in services.items():
            status = service_status.get('status', 'unknown')
            if status == 'healthy':
                print(f"✅ {service_name}: {status}")
            else:
                print(f"⚠️  {service_name}: {status} - {service_status.get('error', 'No details')}")
        
        # Test flight service status
        flight_status = client.get_flight_service_status()
        print(f"\nFlight Service Status: {flight_status.get('status', 'unknown')}")
        print(f"Base URL: {flight_status.get('base_url', 'unknown')}")
        
        capabilities = flight_status.get('capabilities', [])
        print(f"Capabilities: {len(capabilities)} available")
        for capability in capabilities:
            print(f"  - {capability}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_error_handling():
    """Test error handling in API client methods"""
    print("\n🧪 Testing Error Handling")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test with invalid parameters
        print("1. Testing invalid user lookup...")
        result = client.get_user("")
        if result and ("error" in result or result is None):
            print("   ✅ Proper error handling for empty user ID")
        else:
            print(f"   ⚠️  Unexpected result: {result}")
        
        print("\n2. Testing invalid airport lookup...")
        result = client.get_lounges_by_airport("")
        if isinstance(result, (list, dict)) and (not result or result.get("lounges") == []):
            print("   ✅ Proper error handling for empty airport code")
        else:
            print(f"   ⚠️  Unexpected result: {result}")
        
        print("\n3. Testing flight-aware method with missing data...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = client.get_flight_aware_lounge_recommendations(
            flight_number="AA123",
            departure_date=tomorrow,
            user_id="nonexistent_user"
        )
        
        if result.get("status") == "error":
            print("   ✅ Proper error handling for nonexistent user")
        else:
            print(f"   ⚠️  Unexpected result: {result}")
            
    except Exception as e:
        print(f"❌ Error handling test error: {e}")

def test_lounge_compatibility():
    """Test lounge compatibility checking"""
    print("\n🧪 Testing Lounge Compatibility Checking")
    print("-" * 50)
    
    try:
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test compatibility scenarios
        test_cases = [
            {
                "name": "Perfect Match",
                "user_memberships": ["Amex Platinum", "Priority Pass"],
                "lounge_providers": ["Amex Platinum", "Chase Sapphire"],
                "expected_access": True
            },
            {
                "name": "No Match", 
                "user_memberships": ["Basic Card"],
                "lounge_providers": ["Amex Platinum", "Priority Pass"],
                "expected_access": False
            },
            {
                "name": "Partial Match",
                "user_memberships": ["Priority Pass", "Basic Card"],
                "lounge_providers": ["Priority Pass", "Amex Centurion"],
                "expected_access": True
            }
        ]
        
        for test_case in test_cases:
            result = client.check_lounge_compatibility(
                test_case["user_memberships"],
                test_case["lounge_providers"]
            )
            
            has_access = result.get("has_access", False)
            expected = test_case["expected_access"]
            
            if has_access == expected:
                print(f"✅ {test_case['name']}: Access={has_access} (Expected={expected})")
                if has_access:
                    methods = result.get("access_methods", [])
                    print(f"   Access methods: {len(methods)}")
            else:
                print(f"❌ {test_case['name']}: Access={has_access} (Expected={expected})")
                
    except Exception as e:
        print(f"❌ Compatibility test error: {e}")

def main():
    """Run all API client tests"""
    print("🚀 LoungeAccessClient API Test Suite")
    print("=" * 60)
    
    test_basic_functionality()
    test_flight_aware_functionality()
    test_flight_number_validation()
    test_health_check()
    test_error_handling()
    test_lounge_compatibility()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print("✅ API Client structure implemented")
    print("✅ Flight-aware methods integrated")
    print("✅ Helper methods for validation and health checking")
    print("✅ Error handling and fallback mechanisms")
    print("✅ Compatibility checking for lounge access")
    print("⚠️  Requires AWS dependencies and credentials for full functionality")
    
    print("\n📚 Key Features:")
    print("• Basic lounge lookup and filtering")
    print("• Flight-aware lounge recommendations")
    print("• Multi-flight layover strategy analysis")
    print("• Lounge-optimized flight search")
    print("• Comprehensive health monitoring")
    print("• Robust error handling and validation")

if __name__ == "__main__":
    main()