#!/usr/bin/env python3
"""
Simple test runner for lounge functionality without AWS dependencies.
Tests the business logic without actual DynamoDB calls.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the current directory to the path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Import and test the API client with proper mocking
def test_lounge_api_client():
    """Test lounge API client methods with mocked services."""
    print("Testing Lounge API Client...")
    
    with patch('api_client.UserProfileService') as mock_user_service, \
         patch('api_client.LoungeService') as mock_lounge_service:
        
        # Setup mocks
        mock_user_instance = Mock()
        mock_lounge_instance = Mock()
        mock_user_service.return_value = mock_user_instance
        mock_lounge_service.return_value = mock_lounge_instance
        
        # Import after mocking
        from api_client import LoungeAccessClient
        
        client = LoungeAccessClient()
        
        # Test get_lounges_by_airport
        expected_lounges = {
            "airport": "JFK",
            "lounges": [
                {
                    "airport": "JFK",
                    "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                    "name": "Delta Sky Club Terminal 4",
                    "access_providers": ["Delta SkyMiles", "Amex Platinum"],
                    "amenities": ["Buffet", "WiFi", "Showers"],
                    "rating": 4.2
                }
            ]
        }
        mock_lounge_instance.get_lounges_with_access_rules.return_value = expected_lounges
        
        result = client.get_lounges_by_airport("JFK")
        assert result == expected_lounges
        mock_lounge_instance.get_lounges_with_access_rules.assert_called_once_with("JFK")
        print("✅ get_lounges_by_airport test passed")
        
        # Test get_lounge_by_id
        expected_lounge = {
            "airport": "JFK",
            "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
            "name": "Delta Sky Club Terminal 4"
        }
        mock_lounge_instance.get_lounge_by_id.return_value = expected_lounge
        
        result = client.get_lounge_by_id("JFK", "JFK_DELTA_SKY_CLUB_T4")
        assert result == expected_lounge
        mock_lounge_instance.get_lounge_by_id.assert_called_once_with("JFK", "JFK_DELTA_SKY_CLUB_T4")
        print("✅ get_lounge_by_id test passed")
        
        # Test search_lounges_by_access_provider
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "access_providers": ["Delta SkyMiles", "Amex Platinum"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_AMEX_CENTURION_T4",
                "name": "American Express Centurion Lounge Terminal 4",
                "access_providers": ["Amex Platinum", "Amex Centurion"]
            }
        ]
        mock_lounge_instance.get_lounges_by_airport.return_value = mock_lounges
        
        result = client.search_lounges_by_access_provider("JFK", "Amex Platinum")
        assert len(result) == 2
        print("✅ search_lounges_by_access_provider test passed")
        
        # Test get_lounges_with_amenity
        result = client.get_lounges_with_amenity("JFK", "WiFi")
        # This would filter based on amenities (mocked data doesn't have amenities, so empty result expected)
        assert isinstance(result, list)
        print("✅ get_lounges_with_amenity test passed")
        
        # Test validation logic
        result = client.get_lounges_by_airport("")
        assert result == []
        print("✅ Empty airport code validation test passed")
        
        result = client.get_lounge_by_id("", "test")
        assert result is None
        print("✅ Empty parameter validation test passed")
        
        print("🎉 All Lounge API Client tests passed!")
        return True

def test_lounge_search_logic():
    """Test the search and filtering logic."""
    print("\nTesting Lounge Search Logic...")
    
    with patch('api_client.UserProfileService') as mock_user_service, \
         patch('api_client.LoungeService') as mock_lounge_service:
        
        mock_user_instance = Mock()
        mock_lounge_instance = Mock()
        mock_user_service.return_value = mock_user_instance
        mock_lounge_service.return_value = mock_lounge_instance
        
        from api_client import LoungeAccessClient
        client = LoungeAccessClient()
        
        # Test data with various access providers and amenities
        test_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "access_providers": ["Delta SkyMiles", "American Express Platinum Card"],
                "amenities": ["Buffet", "High-Speed WiFi", "Showers", "Business Center"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_AMEX_CENTURION_T4",
                "name": "American Express Centurion Lounge Terminal 4",
                "access_providers": ["American Express Platinum", "American Express Centurion"],
                "amenities": ["Fine Dining", "WiFi", "Showers", "Spa Services"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_PRIORITY_PASS_T1",
                "name": "Priority Pass Lounge Terminal 1",
                "access_providers": ["Priority Pass"],
                "amenities": ["WiFi", "Snacks", "Quiet Zones"]
            }
        ]
        
        mock_lounge_instance.get_lounges_by_airport.return_value = test_lounges
        
        # Test partial matching for access providers
        result = client.search_lounges_by_access_provider("JFK", "Express")
        print(f"Debug: Found {len(result)} lounges with 'Express' in access providers")
        for lounge in result:
            print(f"  - {lounge['name']}: {lounge.get('access_providers', [])}")
        assert len(result) == 2  # Should match both Express lounges
        print("✅ Partial access provider matching test passed")
        
        # Test case-insensitive search
        result = client.search_lounges_by_access_provider("JFK", "priority pass")
        assert len(result) == 1
        assert result[0]["lounge_id"] == "JFK_PRIORITY_PASS_T1"
        print("✅ Case-insensitive access provider search test passed")
        
        # Test amenity search
        result = client.get_lounges_with_amenity("JFK", "Showers")
        assert len(result) == 2  # Delta and Amex Centurion have showers
        print("✅ Amenity search test passed")
        
        # Test partial amenity matching
        result = client.get_lounges_with_amenity("JFK", "wifi")
        assert len(result) == 3  # All have some form of WiFi
        print("✅ Partial amenity matching test passed")
        
        # Test no matches
        result = client.search_lounges_by_access_provider("JFK", "Nonexistent Provider")
        assert len(result) == 0
        print("✅ No matches test passed")
        
        print("🎉 All Lounge Search Logic tests passed!")
        return True

def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\nTesting Edge Cases...")
    
    with patch('api_client.UserProfileService') as mock_user_service, \
         patch('api_client.LoungeService') as mock_lounge_service:
        
        mock_user_instance = Mock()
        mock_lounge_instance = Mock()
        mock_user_service.return_value = mock_user_instance
        mock_lounge_service.return_value = mock_lounge_instance
        
        from api_client import LoungeAccessClient
        client = LoungeAccessClient()
        
        # Test with lounges that have missing fields
        incomplete_lounges = [
            {
                "airport": "ORD",
                "lounge_id": "ORD_MINIMAL_LOUNGE",
                "name": "Minimal Lounge"
                # Missing access_providers and amenities
            }
        ]
        mock_lounge_instance.get_lounges_by_airport.return_value = incomplete_lounges
        
        result = client.search_lounges_by_access_provider("ORD", "Any Provider")
        assert len(result) == 0  # Should handle missing access_providers gracefully
        print("✅ Missing access_providers field test passed")
        
        result = client.get_lounges_with_amenity("ORD", "Any Amenity")
        assert len(result) == 0  # Should handle missing amenities gracefully
        print("✅ Missing amenities field test passed")
        
        # Test various invalid inputs
        invalid_inputs = [None, "", "   ", 123, []]
        for invalid_input in invalid_inputs:
            result = client.get_lounges_by_airport(invalid_input)
            print(f"Debug: Input '{invalid_input}' (type: {type(invalid_input)}) returned: {result}")
            assert result == []
            print(f"✅ Invalid input '{invalid_input}' handled correctly")
        
        print("🎉 All Edge Cases tests passed!")
        return True

def main():
    """Main test function."""
    print("=" * 60)
    print("Lounge Tests - Business Logic Testing")
    print("=" * 60)
    
    try:
        success = True
        success &= test_lounge_api_client()
        success &= test_lounge_search_logic()
        success &= test_edge_cases()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Lounge API Client functionality working correctly")
            print("✅ Search and filtering logic working correctly")
            print("✅ Edge cases handled properly")
        else:
            print("❌ Some tests failed")
        print("=" * 60)
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)