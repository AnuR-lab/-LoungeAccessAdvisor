"""
Unit tests for the LoungeAccessClient class.
Tests the get_user method and its integration with UserProfileService.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the current directory to the path to import local modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from api_client import LoungeAccessClient


class TestLoungeAccessClientGetUser(unittest.TestCase):
    """Test cases for the get_user method in LoungeAccessClient."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock both UserProfileService and LoungeService to avoid actual AWS calls
        with patch('api_client.UserProfileService') as mock_user_service_class, \
             patch('api_client.LoungeService') as mock_lounge_service_class:
            
            self.mock_service_instance = Mock()
            self.mock_lounge_service_instance = Mock()
            mock_user_service_class.return_value = self.mock_service_instance
            mock_lounge_service_class.return_value = self.mock_lounge_service_instance
            
            self.client = LoungeAccessClient()

    def test_get_user_success(self):
        """Test successful user retrieval."""
        # Arrange
        expected_user = {
            "user_id": "LAA_001",
            "name": "John Doe",
            "home_airport": "JFK",
            "memberships": ["priority_pass", "amex_platinum"]
        }
        self.mock_service_instance.get_user.return_value = expected_user

        # Act
        result = self.client.get_user("LAA_001")

        # Assert
        self.assertEqual(result, expected_user)
        self.mock_service_instance.get_user.assert_called_once_with("LAA_001")

    def test_get_user_not_found(self):
        """Test user retrieval when user doesn't exist."""
        # Arrange
        self.mock_service_instance.get_user.return_value = None

        # Act
        result = self.client.get_user("NONEXISTENT_USER")

        # Assert
        self.assertIsNone(result)
        self.mock_service_instance.get_user.assert_called_once_with("NONEXISTENT_USER")

    def test_get_user_empty_string(self):
        """Test user retrieval with empty string user_id."""
        # Arrange
        self.mock_service_instance.get_user.return_value = None

        # Act
        result = self.client.get_user("")

        # Assert
        self.assertIsNone(result)
        self.mock_service_instance.get_user.assert_called_once_with("")

    def test_get_user_none_parameter(self):
        """Test user retrieval with None as user_id."""
        # Arrange
        self.mock_service_instance.get_user.return_value = None

        # Act
        result = self.client.get_user(None)

        # Assert
        self.assertIsNone(result)
        self.mock_service_instance.get_user.assert_called_once_with(None)

    def test_get_user_whitespace_parameter(self):
        """Test user retrieval with whitespace-only user_id."""
        # Arrange
        self.mock_service_instance.get_user.return_value = None

        # Act
        result = self.client.get_user("   ")

        # Assert
        self.assertIsNone(result)
        self.mock_service_instance.get_user.assert_called_once_with("   ")

    def test_get_user_service_exception(self):
        """Test user retrieval when service raises an exception."""
        # Arrange
        self.mock_service_instance.get_user.side_effect = Exception("Database connection error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.client.get_user("LAA_001")

        self.assertEqual(str(context.exception), "Database connection error")
        self.mock_service_instance.get_user.assert_called_once_with("LAA_001")

    def test_get_user_multiple_calls(self):
        """Test multiple user retrievals to ensure service is called correctly."""
        # Arrange
        user1 = {
            "user_id": "LAA_001",
            "name": "John Doe",
            "home_airport": "JFK",
            "memberships": ["priority_pass", "amex_platinum"]
        }
        user2 = {
            "user_id": "LAA_002",
            "name": "Jane Smith",
            "home_airport": "LAX",
            "memberships": ["chase_sapphire", "priority_pass"]
        }
        
        # Configure mock to return different users based on input
        def mock_get_user(user_id):
            if user_id == "LAA_001":
                return user1
            elif user_id == "LAA_002":
                return user2
            return None
        
        self.mock_service_instance.get_user.side_effect = mock_get_user

        # Act
        result1 = self.client.get_user("LAA_001")
        result2 = self.client.get_user("LAA_002")
        result3 = self.client.get_user("LAA_999")

        # Assert
        self.assertEqual(result1, user1)
        self.assertEqual(result2, user2)
        self.assertIsNone(result3)
        
        # Verify all calls were made
        expected_calls = [
            unittest.mock.call("LAA_001"),
            unittest.mock.call("LAA_002"),
            unittest.mock.call("LAA_999")
        ]
        self.mock_service_instance.get_user.assert_has_calls(expected_calls)
        self.assertEqual(self.mock_service_instance.get_user.call_count, 3)

    def test_get_user_partial_data(self):
        """Test user retrieval with partial user data."""
        # Arrange
        partial_user = {
            "user_id": "LAA_003",
            "name": "Mike Johnson",
            "home_airport": None,  # Missing home airport
            "memberships": []  # Empty memberships
        }
        self.mock_service_instance.get_user.return_value = partial_user

        # Act
        result = self.client.get_user("LAA_003")

        # Assert
        self.assertEqual(result, partial_user)
        self.assertIsNone(result["home_airport"])
        self.assertEqual(result["memberships"], [])
        self.mock_service_instance.get_user.assert_called_once_with("LAA_003")

    def test_get_user_special_characters(self):
        """Test user retrieval with special characters in user_id."""
        # Arrange
        special_user_id = "LAA_001@#$%^&*()"
        expected_user = {
            "user_id": special_user_id,
            "name": "Special User",
            "home_airport": "JFK",
            "memberships": ["priority_pass"]
        }
        self.mock_service_instance.get_user.return_value = expected_user

        # Act
        result = self.client.get_user(special_user_id)

        # Assert
        self.assertEqual(result, expected_user)
        self.mock_service_instance.get_user.assert_called_once_with(special_user_id)

    def test_get_user_long_user_id(self):
        """Test user retrieval with very long user_id."""
        # Arrange
        long_user_id = "LAA_" + "A" * 1000  # Very long user ID
        self.mock_service_instance.get_user.return_value = None

        # Act
        result = self.client.get_user(long_user_id)

        # Assert
        self.assertIsNone(result)
        self.mock_service_instance.get_user.assert_called_once_with(long_user_id)


class TestLoungeAccessClientCreateSampleUsers(unittest.TestCase):
    """Test cases for the create_sample_users method in LoungeAccessClient."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock both UserProfileService and LoungeService to avoid actual AWS calls
        with patch('api_client.UserProfileService') as mock_user_service_class, \
             patch('api_client.LoungeService') as mock_lounge_service_class:
            
            self.mock_service_instance = Mock()
            self.mock_lounge_service_instance = Mock()
            mock_user_service_class.return_value = self.mock_service_instance
            mock_lounge_service_class.return_value = self.mock_lounge_service_instance
            
            self.client = LoungeAccessClient()

    def test_create_sample_users_success(self):
        """Test successful creation of sample users."""
        # Arrange
        self.mock_service_instance.create_sample_users.return_value = True

        # Act
        result = self.client.create_sample_users()

        # Assert
        self.assertTrue(result)
        self.mock_service_instance.create_sample_users.assert_called_once()

    def test_create_sample_users_failure(self):
        """Test failed creation of sample users."""
        # Arrange
        self.mock_service_instance.create_sample_users.return_value = False

        # Act
        result = self.client.create_sample_users()

        # Assert
        self.assertFalse(result)
        self.mock_service_instance.create_sample_users.assert_called_once()

    def test_create_sample_users_exception(self):
        """Test create_sample_users when service raises an exception."""
        # Arrange
        self.mock_service_instance.create_sample_users.side_effect = Exception("DynamoDB error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.client.create_sample_users()

        self.assertEqual(str(context.exception), "DynamoDB error")
        self.mock_service_instance.create_sample_users.assert_called_once()


class TestLoungeAccessClientInitialization(unittest.TestCase):
    """Test cases for LoungeAccessClient initialization."""

    @patch('api_client.UserProfileService')
    def test_initialization_creates_service_instance(self, mock_service_class):
        """Test that initialization creates a UserProfileService instance."""
        # Arrange
        mock_service_instance = Mock()
        mock_service_class.return_value = mock_service_instance

        # Act
        client = LoungeAccessClient()

        # Assert
        mock_service_class.assert_called_once()
        self.assertEqual(client.user_profile_service, mock_service_instance)

    @patch('api_client.UserProfileService')
    def test_initialization_calls_get_client(self, mock_service_class):
        """Test that initialization calls _get_client method."""
        # Arrange & Act
        with patch.object(LoungeAccessClient, '_get_client', return_value=None) as mock_get_client:
            client = LoungeAccessClient()

        # Assert
        mock_get_client.assert_called_once()
        self.assertIsNone(client.api_client)


class TestLoungeAccessClientIntegration(unittest.TestCase):
    """Integration tests for LoungeAccessClient (with minimal mocking)."""

    def test_method_delegation_integration(self):
        """Test that methods properly delegate to UserProfileService."""
        # This test uses more realistic mocking to test the integration
        with patch('api_client.UserProfileService') as mock_service_class:
            # Create a mock service instance with realistic behavior
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance
            
            # Configure realistic return values
            test_user = {
                "user_id": "LAA_001",
                "name": "John Doe",
                "home_airport": "JFK",
                "memberships": ["priority_pass", "amex_platinum"]
            }
            mock_service_instance.get_user.return_value = test_user
            mock_service_instance.create_sample_users.return_value = True
            
            # Create client
            client = LoungeAccessClient()
            
            # Test get_user delegation
            result = client.get_user("LAA_001")
            self.assertEqual(result, test_user)
            
            # Test create_sample_users delegation
            result = client.create_sample_users()
            self.assertTrue(result)
            
            # Verify calls were delegated properly
            mock_service_instance.get_user.assert_called_once_with("LAA_001")
            mock_service_instance.create_sample_users.assert_called_once()


class TestLoungeAccessClientLoungeOperations(unittest.TestCase):
    """Test cases for lounge-related methods in LoungeAccessClient."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock both UserProfileService and LoungeService
        with patch('api_client.UserProfileService') as mock_user_service_class, \
             patch('api_client.LoungeService') as mock_lounge_service_class:
            
            self.mock_user_service_instance = Mock()
            self.mock_lounge_service_instance = Mock()
            mock_user_service_class.return_value = self.mock_user_service_instance
            mock_lounge_service_class.return_value = self.mock_lounge_service_instance
            
            self.client = LoungeAccessClient()

    def test_get_lounges_by_airport_success(self):
        """Test successful lounge retrieval by airport."""
        # Arrange
        expected_lounges = {
            "airport": "JFK",
            "lounges": [
                {
                    "airport": "JFK",
                    "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                    "name": "Delta Sky Club Terminal 4",
                    "terminal": "Terminal 4",
                    "access_providers": ["Delta SkyMiles", "Amex Platinum"],
                    "amenities": ["Buffet", "WiFi", "Showers"],
                    "rating": 4.2
                }
            ]
        }
        self.mock_lounge_service_instance.get_lounges_with_access_rules.return_value = expected_lounges

        # Act
        result = self.client.get_lounges_by_airport("JFK")

        # Assert
        self.assertEqual(result, expected_lounges)
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_called_once_with("JFK")

    def test_get_lounges_by_airport_empty_airport_code(self):
        """Test lounge retrieval with empty airport code."""
        # Act
        result = self.client.get_lounges_by_airport("")

        # Assert
        self.assertEqual(result, [])
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_not_called()

    def test_get_lounges_by_airport_none_airport_code(self):
        """Test lounge retrieval with None airport code."""
        # Act
        result = self.client.get_lounges_by_airport(None)

        # Assert
        self.assertEqual(result, [])
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_not_called()

    def test_get_lounges_by_airport_invalid_type(self):
        """Test lounge retrieval with non-string airport code."""
        # Act
        result = self.client.get_lounges_by_airport(123)

        # Assert
        self.assertEqual(result, [])
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_not_called()

    def test_get_lounge_by_id_success(self):
        """Test successful specific lounge retrieval."""
        # Arrange
        expected_lounge = {
            "airport": "JFK",
            "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
            "name": "Delta Sky Club Terminal 4",
            "terminal": "Terminal 4",
            "access_providers": ["Delta SkyMiles", "Amex Platinum"],
            "amenities": ["Buffet", "WiFi", "Showers"],
            "rating": 4.2
        }
        self.mock_lounge_service_instance.get_lounge_by_id.return_value = expected_lounge

        # Act
        result = self.client.get_lounge_by_id("JFK", "JFK_DELTA_SKY_CLUB_T4")

        # Assert
        self.assertEqual(result, expected_lounge)
        self.mock_lounge_service_instance.get_lounge_by_id.assert_called_once_with("JFK", "JFK_DELTA_SKY_CLUB_T4")

    def test_get_lounge_by_id_not_found(self):
        """Test lounge retrieval when lounge doesn't exist."""
        # Arrange
        self.mock_lounge_service_instance.get_lounge_by_id.return_value = None

        # Act
        result = self.client.get_lounge_by_id("JFK", "NONEXISTENT_LOUNGE")

        # Assert
        self.assertIsNone(result)
        self.mock_lounge_service_instance.get_lounge_by_id.assert_called_once_with("JFK", "NONEXISTENT_LOUNGE")

    def test_get_lounge_by_id_empty_parameters(self):
        """Test lounge retrieval with empty parameters."""
        # Test empty airport code
        result1 = self.client.get_lounge_by_id("", "JFK_DELTA_SKY_CLUB_T4")
        self.assertIsNone(result1)

        # Test empty lounge ID
        result2 = self.client.get_lounge_by_id("JFK", "")
        self.assertIsNone(result2)

        # Test both empty
        result3 = self.client.get_lounge_by_id("", "")
        self.assertIsNone(result3)

        # Assert service was not called
        self.mock_lounge_service_instance.get_lounge_by_id.assert_not_called()

    def test_get_lounge_by_id_none_parameters(self):
        """Test lounge retrieval with None parameters."""
        # Test None airport code
        result1 = self.client.get_lounge_by_id(None, "JFK_DELTA_SKY_CLUB_T4")
        self.assertIsNone(result1)

        # Test None lounge ID
        result2 = self.client.get_lounge_by_id("JFK", None)
        self.assertIsNone(result2)

        # Assert service was not called
        self.mock_lounge_service_instance.get_lounge_by_id.assert_not_called()

    def test_create_sample_lounges_success(self):
        """Test successful creation of sample lounges."""
        # Arrange
        self.mock_lounge_service_instance.create_sample_lounges.return_value = True

        # Act
        result = self.client.create_sample_lounges()

        # Assert
        self.assertTrue(result)
        self.mock_lounge_service_instance.create_sample_lounges.assert_called_once()

    def test_create_sample_lounges_failure(self):
        """Test failed creation of sample lounges."""
        # Arrange
        self.mock_lounge_service_instance.create_sample_lounges.return_value = False

        # Act
        result = self.client.create_sample_lounges()

        # Assert
        self.assertFalse(result)
        self.mock_lounge_service_instance.create_sample_lounges.assert_called_once()

    def test_create_sample_lounges_exception(self):
        """Test create_sample_lounges when service raises an exception."""
        # Arrange
        self.mock_lounge_service_instance.create_sample_lounges.side_effect = Exception("DynamoDB error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.client.create_sample_lounges()

        self.assertEqual(str(context.exception), "DynamoDB error")
        self.mock_lounge_service_instance.create_sample_lounges.assert_called_once()

    def test_search_lounges_by_access_provider_success(self):
        """Test successful search by access provider."""
        # Arrange
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "access_providers": ["Delta SkyMiles", "Amex Platinum", "Priority Pass"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_AMEX_CENTURION_T4",
                "name": "American Express Centurion Lounge Terminal 4",
                "access_providers": ["Amex Platinum", "Amex Centurion"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_PRIORITY_PASS_T1",
                "name": "Priority Pass Lounge Terminal 1",
                "access_providers": ["Priority Pass"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.search_lounges_by_access_provider("JFK", "Amex Platinum")

        # Assert
        self.assertEqual(len(result), 2)  # Should return 2 lounges with Amex Platinum access
        self.assertEqual(result[0]["lounge_id"], "JFK_DELTA_SKY_CLUB_T4")
        self.assertEqual(result[1]["lounge_id"], "JFK_AMEX_CENTURION_T4")
        self.mock_lounge_service_instance.get_lounges_by_airport.assert_called_once_with("JFK")

    def test_search_lounges_by_access_provider_case_insensitive(self):
        """Test search by access provider is case insensitive."""
        # Arrange
        mock_lounges = [
            {
                "airport": "LAX",
                "lounge_id": "LAX_PRIORITY_PASS_TBIT",
                "name": "Priority Pass Lounge TBIT",
                "access_providers": ["Priority Pass", "Star Alliance Gold"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.search_lounges_by_access_provider("LAX", "priority pass")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["lounge_id"], "LAX_PRIORITY_PASS_TBIT")

    def test_search_lounges_by_access_provider_no_matches(self):
        """Test search by access provider with no matches."""
        # Arrange
        mock_lounges = [
            {
                "airport": "ORD",
                "lounge_id": "ORD_UNITED_CLUB_T1",
                "name": "United Club Terminal 1",
                "access_providers": ["United Club", "Chase Sapphire Reserve"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.search_lounges_by_access_provider("ORD", "Amex Platinum")

        # Assert
        self.assertEqual(len(result), 0)

    def test_search_lounges_by_access_provider_empty_parameters(self):
        """Test search by access provider with empty parameters."""
        # Test empty airport code
        result1 = self.client.search_lounges_by_access_provider("", "Amex Platinum")
        self.assertEqual(result1, [])

        # Test empty access provider
        result2 = self.client.search_lounges_by_access_provider("JFK", "")
        self.assertEqual(result2, [])

        # Assert service was not called
        self.mock_lounge_service_instance.get_lounges_by_airport.assert_not_called()

    def test_get_lounges_with_amenity_success(self):
        """Test successful search by amenity."""
        # Arrange
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "amenities": ["Buffet", "WiFi", "Showers", "Business Center"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_AMEX_CENTURION_T4",
                "name": "American Express Centurion Lounge Terminal 4",
                "amenities": ["Fine Dining", "WiFi", "Showers", "Spa"]
            },
            {
                "airport": "JFK",
                "lounge_id": "JFK_BASIC_LOUNGE_T2",
                "name": "Basic Lounge Terminal 2",
                "amenities": ["WiFi", "Snacks"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.get_lounges_with_amenity("JFK", "Showers")

        # Assert
        self.assertEqual(len(result), 2)  # Should return 2 lounges with showers
        lounge_ids = [lounge["lounge_id"] for lounge in result]
        self.assertIn("JFK_DELTA_SKY_CLUB_T4", lounge_ids)
        self.assertIn("JFK_AMEX_CENTURION_T4", lounge_ids)
        self.mock_lounge_service_instance.get_lounges_by_airport.assert_called_once_with("JFK")

    def test_get_lounges_with_amenity_case_insensitive(self):
        """Test search by amenity is case insensitive."""
        # Arrange
        mock_lounges = [
            {
                "airport": "LAX",
                "lounge_id": "LAX_WIFI_LOUNGE_TBIT",
                "name": "WiFi Lounge TBIT",
                "amenities": ["WiFi", "Business Center", "Quiet Zones"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.get_lounges_with_amenity("LAX", "wifi")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["lounge_id"], "LAX_WIFI_LOUNGE_TBIT")

    def test_get_lounges_with_amenity_no_matches(self):
        """Test search by amenity with no matches."""
        # Arrange
        mock_lounges = [
            {
                "airport": "ORD",
                "lounge_id": "ORD_BASIC_LOUNGE_T1",
                "name": "Basic Lounge Terminal 1",
                "amenities": ["WiFi", "Snacks"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result = self.client.get_lounges_with_amenity("ORD", "Showers")

        # Assert
        self.assertEqual(len(result), 0)

    def test_get_lounges_with_amenity_empty_parameters(self):
        """Test search by amenity with empty parameters."""
        # Test empty airport code
        result1 = self.client.get_lounges_with_amenity("", "WiFi")
        self.assertEqual(result1, [])

        # Test empty amenity
        result2 = self.client.get_lounges_with_amenity("JFK", "")
        self.assertEqual(result2, [])

        # Assert service was not called
        self.mock_lounge_service_instance.get_lounges_by_airport.assert_not_called()

    def test_lounges_service_exception_handling(self):
        """Test handling of exceptions from lounge service."""
        # Arrange
        self.mock_lounge_service_instance.get_lounges_with_access_rules.side_effect = Exception("DynamoDB connection error")

        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.client.get_lounges_by_airport("JFK")

        self.assertEqual(str(context.exception), "DynamoDB connection error")

    def test_multiple_lounge_operations(self):
        """Test multiple lounge operations in sequence."""
        # Arrange
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_TEST_LOUNGE",
                "name": "Test Lounge",
                "access_providers": ["Amex Platinum"],
                "amenities": ["WiFi"]
            }
        ]
        mock_single_lounge = {
            "airport": "JFK",
            "lounge_id": "JFK_TEST_LOUNGE",
            "name": "Test Lounge"
        }

        self.mock_lounge_service_instance.get_lounges_with_access_rules.return_value = {"airport": "JFK", "lounges": mock_lounges}
        self.mock_lounge_service_instance.get_lounge_by_id.return_value = mock_single_lounge
        self.mock_lounge_service_instance.create_sample_lounges.return_value = True
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result1 = self.client.get_lounges_by_airport("JFK")
        result2 = self.client.get_lounge_by_id("JFK", "JFK_TEST_LOUNGE")
        result3 = self.client.create_sample_lounges()
        result4 = self.client.search_lounges_by_access_provider("JFK", "Amex")

        # Assert
        self.assertEqual(result1["airport"], "JFK")
        self.assertEqual(result2["lounge_id"], "JFK_TEST_LOUNGE")
        self.assertTrue(result3)
        self.assertEqual(len(result4), 1)

        # Verify all calls were made
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_called_once_with("JFK")
        self.mock_lounge_service_instance.get_lounge_by_id.assert_called_once_with("JFK", "JFK_TEST_LOUNGE")
        self.mock_lounge_service_instance.create_sample_lounges.assert_called_once()
        self.mock_lounge_service_instance.get_lounges_by_airport.assert_called_once_with("JFK")


class TestLoungeAccessClientLoungeMethods(unittest.TestCase):
    """Additional test cases for lounge functionality and edge cases."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('api_client.UserProfileService') as mock_user_service_class, \
             patch('api_client.LoungeService') as mock_lounge_service_class:
            
            self.mock_user_service_instance = Mock()
            self.mock_lounge_service_instance = Mock()
            mock_user_service_class.return_value = self.mock_user_service_instance
            mock_lounge_service_class.return_value = self.mock_lounge_service_instance
            
            self.client = LoungeAccessClient()

    def test_search_with_partial_provider_name_match(self):
        """Test that partial matches work for access providers."""
        # Arrange
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_AMEX_LOUNGE",
                "name": "American Express Lounge",
                "access_providers": ["American Express Platinum Card"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act - search with partial name
        result = self.client.search_lounges_by_access_provider("JFK", "Express")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["lounge_id"], "JFK_AMEX_LOUNGE")

    def test_search_with_partial_amenity_match(self):
        """Test that partial matches work for amenities."""
        # Arrange
        mock_lounges = [
            {
                "airport": "LAX",
                "lounge_id": "LAX_BUSINESS_LOUNGE",
                "name": "Business Lounge",
                "amenities": ["High-Speed WiFi", "Business Center"]
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act - search with partial amenity name
        result = self.client.get_lounges_with_amenity("LAX", "Business")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["lounge_id"], "LAX_BUSINESS_LOUNGE")

    def test_lounge_operations_with_missing_fields(self):
        """Test lounge operations when data has missing fields."""
        # Arrange
        mock_lounges = [
            {
                "airport": "ORD",
                "lounge_id": "ORD_MINIMAL_LOUNGE",
                "name": "Minimal Lounge"
                # Missing access_providers and amenities
            }
        ]
        self.mock_lounge_service_instance.get_lounges_by_airport.return_value = mock_lounges

        # Act
        result1 = self.client.search_lounges_by_access_provider("ORD", "Any Provider")
        result2 = self.client.get_lounges_with_amenity("ORD", "Any Amenity")

        # Assert - should return empty lists when fields are missing
        self.assertEqual(len(result1), 0)
        self.assertEqual(len(result2), 0)

    def test_airport_code_normalization(self):
        """Test that airport codes are passed correctly to the service."""
        # Arrange
        expected_lounges = {"airport": "LAX", "lounges": []}
        self.mock_lounge_service_instance.get_lounges_with_access_rules.return_value = expected_lounges

        # Act - test with different case variations
        result1 = self.client.get_lounges_by_airport("lax")
        result2 = self.client.get_lounges_by_airport("LAX")
        result3 = self.client.get_lounges_by_airport("LaX")

        # Assert - all should be passed to service as provided (service handles normalization)
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_any_call("lax")
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_any_call("LAX")
        self.mock_lounge_service_instance.get_lounges_with_access_rules.assert_any_call("LaX")


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)