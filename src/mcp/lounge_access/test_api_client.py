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
        # Mock the UserProfileService to avoid actual DynamoDB calls
        with patch('api_client.UserProfileService') as mock_service_class:
            self.mock_service_instance = Mock()
            mock_service_class.return_value = self.mock_service_instance
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
        # Mock the UserProfileService to avoid actual DynamoDB calls
        with patch('api_client.UserProfileService') as mock_service_class:
            self.mock_service_instance = Mock()
            mock_service_class.return_value = self.mock_service_instance
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


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)