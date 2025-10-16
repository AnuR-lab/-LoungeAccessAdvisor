"""
Unit tests for the LoungeService class.
Tests the lounge service methods and DynamoDB integration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the current directory to the path to import local modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from lounge_service import LoungeService


class TestLoungeServiceInitialization(unittest.TestCase):
    """Test cases for LoungeService initialization."""

    @patch('lounge_service.boto3.resource')
    def test_initialization_creates_dynamodb_resource(self, mock_boto3_resource):
        """Test that initialization creates DynamoDB resource and tables."""
        # Arrange
        mock_dynamodb = Mock()
        mock_lounges_table = Mock()
        mock_providers_table = Mock()
        mock_boto3_resource.return_value = mock_dynamodb
        mock_dynamodb.Table.side_effect = [mock_lounges_table, mock_providers_table]

        # Mock the _ensure_table_exists method to avoid actual table operations
        with patch.object(LoungeService, '_ensure_table_exists'):
            # Act
            service = LoungeService()

            # Assert
            mock_boto3_resource.assert_called_once_with("dynamodb")
            self.assertEqual(service.lounges_table_name, "Lounges")
            self.assertEqual(service.providers_table_name, "AccessProviders")
            self.assertEqual(mock_dynamodb.Table.call_count, 2)

    @patch('lounge_service.boto3.resource')
    def test_initialization_with_custom_table_names(self, mock_boto3_resource):
        """Test initialization with custom table names."""
        # Arrange
        mock_dynamodb = Mock()
        mock_boto3_resource.return_value = mock_dynamodb

        with patch.object(LoungeService, '_ensure_table_exists'):
            # Act
            service = LoungeService(lounges_table="CustomLounges", providers_table="CustomProviders")

            # Assert
            self.assertEqual(service.lounges_table_name, "CustomLounges")
            self.assertEqual(service.providers_table_name, "CustomProviders")


class TestLoungeServiceGetLoungesWithAccessRules(unittest.TestCase):
    """Test cases for get_lounges_with_access_rules method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('lounge_service.boto3.resource'):
            with patch.object(LoungeService, '_ensure_table_exists'):
                self.service = LoungeService()
                self.service.lounges_table = Mock()
                self.service.providers_table = Mock()
                self.service.dynamodb = Mock()

    def test_get_lounges_with_access_rules_success(self):
        """Test successful retrieval of lounges with access rules."""
        # Arrange
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "access_providers": ["Delta SkyMiles", "Amex Platinum"]
            }
        ]
        mock_providers = [
            {
                "provider_name": "Delta SkyMiles",
                "guest_policy": "Varies by status",
                "conditions": "Flying Delta same day",
                "notes": "Status-dependent benefits"
            },
            {
                "provider_name": "Amex Platinum",
                "guest_policy": "2 guests free",
                "conditions": "Must be traveling same day",
                "notes": "Primary cardholder must be present"
            }
        ]

        self.service.lounges_table.query.return_value = {"Items": mock_lounges}
        self.service.dynamodb.batch_get_item.return_value = {
            "Responses": {
                "AccessProviders": mock_providers
            }
        }

        # Act
        result = self.service.get_lounges_with_access_rules("JFK")

        # Assert
        self.assertEqual(result["airport"], "JFK")
        self.assertEqual(len(result["lounges"]), 1)
        lounge = result["lounges"][0]
        self.assertEqual(len(lounge["access_details"]), 2)
        self.assertEqual(lounge["access_details"][0]["provider_name"], "Delta SkyMiles")
        self.assertEqual(lounge["access_details"][1]["provider_name"], "Amex Platinum")

    def test_get_lounges_with_access_rules_no_lounges(self):
        """Test behavior when no lounges found for airport."""
        # Arrange
        self.service.lounges_table.query.return_value = {"Items": []}

        # Act
        result = self.service.get_lounges_with_access_rules("XYZ")

        # Assert
        self.assertEqual(result["airport"], "XYZ")
        self.assertEqual(result["lounges"], [])

    def test_get_lounges_with_access_rules_case_normalization(self):
        """Test that airport code is normalized to uppercase."""
        # Arrange
        self.service.lounges_table.query.return_value = {"Items": []}

        # Act
        result = self.service.get_lounges_with_access_rules("jfk")

        # Assert
        self.assertEqual(result["airport"], "JFK")
        # Verify query was called with uppercase airport code
        from boto3.dynamodb.conditions import Key
        expected_key_condition = Key("airport").eq("JFK")
        self.service.lounges_table.query.assert_called_once()

    def test_get_lounges_with_access_rules_exception_handling(self):
        """Test exception handling in get_lounges_with_access_rules."""
        # Arrange
        self.service.lounges_table.query.side_effect = Exception("DynamoDB error")

        # Act
        result = self.service.get_lounges_with_access_rules("JFK")

        # Assert
        self.assertEqual(result["airport"], "JFK")
        self.assertEqual(result["lounges"], [])

    def test_get_lounges_with_access_rules_missing_providers(self):
        """Test behavior when some providers are missing from providers table."""
        # Arrange
        mock_lounges = [
            {
                "airport": "LAX",
                "lounge_id": "LAX_TEST_LOUNGE",
                "name": "Test Lounge",
                "access_providers": ["Provider1", "Provider2", "Provider3"]
            }
        ]
        # Only return data for Provider1 and Provider2, Provider3 is missing
        mock_providers = [
            {
                "provider_name": "Provider1",
                "guest_policy": "Free",
                "conditions": "None",
                "notes": "Test provider 1"
            },
            {
                "provider_name": "Provider2",
                "guest_policy": "Paid",
                "conditions": "Some conditions",
                "notes": "Test provider 2"
            }
        ]

        self.service.lounges_table.query.return_value = {"Items": mock_lounges}
        self.service.dynamodb.batch_get_item.return_value = {
            "Responses": {
                "AccessProviders": mock_providers
            }
        }

        # Act
        result = self.service.get_lounges_with_access_rules("LAX")

        # Assert
        lounge = result["lounges"][0]
        self.assertEqual(len(lounge["access_details"]), 3)
        
        # Check that missing provider has empty details
        provider3_details = next(detail for detail in lounge["access_details"] 
                               if detail["provider_name"] == "Provider3")
        self.assertIsNone(provider3_details["guest_policy"])
        self.assertIsNone(provider3_details["conditions"])
        self.assertIsNone(provider3_details["notes"])


class TestLoungeServiceGetLoungesByAirport(unittest.TestCase):
    """Test cases for get_lounges_by_airport method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('lounge_service.boto3.resource'):
            with patch.object(LoungeService, '_ensure_table_exists'):
                self.service = LoungeService()
                self.service.lounges_table = Mock()

    def test_get_lounges_by_airport_success(self):
        """Test successful retrieval of lounges by airport."""
        # Arrange
        mock_lounges = [
            {"airport": "JFK", "lounge_id": "JFK_LOUNGE_1", "name": "Lounge 1"},
            {"airport": "JFK", "lounge_id": "JFK_LOUNGE_2", "name": "Lounge 2"}
        ]
        self.service.lounges_table.query.return_value = {"Items": mock_lounges}

        # Act
        result = self.service.get_lounges_by_airport("JFK")

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result, mock_lounges)

    def test_get_lounges_by_airport_no_lounges(self):
        """Test behavior when no lounges found."""
        # Arrange
        self.service.lounges_table.query.return_value = {"Items": []}

        # Act
        result = self.service.get_lounges_by_airport("XYZ")

        # Assert
        self.assertEqual(result, [])

    def test_get_lounges_by_airport_exception(self):
        """Test exception handling."""
        # Arrange
        self.service.lounges_table.query.side_effect = Exception("DynamoDB error")

        # Act
        result = self.service.get_lounges_by_airport("JFK")

        # Assert
        self.assertEqual(result, [])

    def test_get_lounges_by_airport_case_normalization(self):
        """Test airport code normalization."""
        # Arrange
        self.service.lounges_table.query.return_value = {"Items": []}

        # Act
        self.service.get_lounges_by_airport("lax")

        # Assert
        # Verify that the airport code was normalized to uppercase
        from boto3.dynamodb.conditions import Key
        self.service.lounges_table.query.assert_called_once()


class TestLoungeServiceGetLoungeById(unittest.TestCase):
    """Test cases for get_lounge_by_id method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('lounge_service.boto3.resource'):
            with patch.object(LoungeService, '_ensure_table_exists'):
                self.service = LoungeService()
                self.service.lounges_table = Mock()

    def test_get_lounge_by_id_success(self):
        """Test successful retrieval of specific lounge."""
        # Arrange
        mock_lounge = {
            "airport": "JFK",
            "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
            "name": "Delta Sky Club Terminal 4"
        }
        self.service.lounges_table.get_item.return_value = {"Item": mock_lounge}

        # Act
        result = self.service.get_lounge_by_id("JFK", "JFK_DELTA_SKY_CLUB_T4")

        # Assert
        self.assertEqual(result, mock_lounge)
        self.service.lounges_table.get_item.assert_called_once_with(
            Key={"airport": "JFK", "lounge_id": "JFK_DELTA_SKY_CLUB_T4"}
        )

    def test_get_lounge_by_id_not_found(self):
        """Test behavior when lounge not found."""
        # Arrange
        self.service.lounges_table.get_item.return_value = {}

        # Act
        result = self.service.get_lounge_by_id("JFK", "NONEXISTENT_LOUNGE")

        # Assert
        self.assertIsNone(result)

    def test_get_lounge_by_id_exception(self):
        """Test exception handling."""
        # Arrange
        self.service.lounges_table.get_item.side_effect = Exception("DynamoDB error")

        # Act
        result = self.service.get_lounge_by_id("JFK", "JFK_DELTA_SKY_CLUB_T4")

        # Assert
        self.assertIsNone(result)

    def test_get_lounge_by_id_case_normalization(self):
        """Test airport code normalization."""
        # Arrange
        self.service.lounges_table.get_item.return_value = {}

        # Act
        self.service.get_lounge_by_id("lax", "LAX_LOUNGE_1")

        # Assert
        self.service.lounges_table.get_item.assert_called_once_with(
            Key={"airport": "LAX", "lounge_id": "LAX_LOUNGE_1"}
        )


class TestLoungeServiceCreateSampleLounges(unittest.TestCase):
    """Test cases for create_sample_lounges method."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('lounge_service.boto3.resource'):
            with patch.object(LoungeService, '_ensure_table_exists'):
                self.service = LoungeService()
                self.service.lounges_table = Mock()
                self.service.providers_table = Mock()

    def test_create_sample_lounges_success(self):
        """Test successful creation of sample lounges."""
        # Arrange
        mock_lounges_batch_writer = Mock()
        mock_providers_batch_writer = Mock()
        
        # Mock context managers properly
        mock_lounges_context = Mock()
        mock_providers_context = Mock()
        mock_lounges_context.__enter__ = Mock(return_value=mock_lounges_batch_writer)
        mock_lounges_context.__exit__ = Mock(return_value=None)
        mock_providers_context.__enter__ = Mock(return_value=mock_providers_batch_writer)
        mock_providers_context.__exit__ = Mock(return_value=None)
        
        self.service.lounges_table.batch_writer.return_value = mock_lounges_context
        self.service.providers_table.batch_writer.return_value = mock_providers_context

        # Act
        result = self.service.create_sample_lounges()

        # Assert
        self.assertTrue(result)
        # Verify batch writers were used
        self.service.lounges_table.batch_writer.assert_called_once()
        self.service.providers_table.batch_writer.assert_called_once()
        # Verify put_item was called for each sample item
        self.assertTrue(mock_lounges_batch_writer.put_item.called)
        self.assertTrue(mock_providers_batch_writer.put_item.called)

    def test_create_sample_lounges_exception(self):
        """Test exception handling during sample creation."""
        # Arrange
        self.service.lounges_table.batch_writer.side_effect = Exception("DynamoDB error")

        # Act
        result = self.service.create_sample_lounges()

        # Assert
        self.assertFalse(result)

    def test_create_sample_lounges_data_content(self):
        """Test that sample data contains expected content."""
        # Arrange
        mock_lounges_batch_writer = Mock()
        mock_providers_batch_writer = Mock()
        
        # Mock context managers properly
        mock_lounges_context = Mock()
        mock_providers_context = Mock()
        mock_lounges_context.__enter__ = Mock(return_value=mock_lounges_batch_writer)
        mock_lounges_context.__exit__ = Mock(return_value=None)
        mock_providers_context.__enter__ = Mock(return_value=mock_providers_batch_writer)
        mock_providers_context.__exit__ = Mock(return_value=None)
        
        self.service.lounges_table.batch_writer.return_value = mock_lounges_context
        self.service.providers_table.batch_writer.return_value = mock_providers_context

        # Act
        result = self.service.create_sample_lounges()

        # Assert
        self.assertTrue(result)
        
        # Check that lounges were created
        lounges_calls = mock_lounges_batch_writer.put_item.call_args_list
        self.assertGreater(len(lounges_calls), 0)
        
        # Check that at least one lounge has expected structure
        first_lounge_call = lounges_calls[0]
        lounge_item = first_lounge_call[1]['Item']  # Extract the Item parameter
        required_fields = ['airport', 'lounge_id', 'name', 'terminal', 'access_providers', 'amenities']
        for field in required_fields:
            self.assertIn(field, lounge_item)

        # Check that providers were created
        providers_calls = mock_providers_batch_writer.put_item.call_args_list
        self.assertGreater(len(providers_calls), 0)
        
        # Check that at least one provider has expected structure
        first_provider_call = providers_calls[0]
        provider_item = first_provider_call[1]['Item']
        required_provider_fields = ['provider_name', 'guest_policy', 'conditions', 'notes']
        for field in required_provider_fields:
            self.assertIn(field, provider_item)


class TestLoungeServiceTableManagement(unittest.TestCase):
    """Test cases for table management methods."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_dynamodb = Mock()
        self.mock_table = Mock()

    @patch('lounge_service.boto3.resource')
    def test_ensure_table_exists_table_found(self, mock_boto3_resource):
        """Test _ensure_table_exists when table already exists."""
        # Arrange
        mock_boto3_resource.return_value = self.mock_dynamodb
        self.mock_dynamodb.Table.return_value = self.mock_table
        self.mock_table.load.return_value = None  # No exception means table exists

        # Act
        service = LoungeService()

        # Assert
        self.mock_table.load.assert_called()

    @patch('lounge_service.boto3.resource')
    def test_ensure_table_exists_table_not_found(self, mock_boto3_resource):
        """Test _ensure_table_exists when table doesn't exist."""
        # Arrange
        from botocore.exceptions import ClientError
        mock_boto3_resource.return_value = self.mock_dynamodb
        self.mock_dynamodb.Table.return_value = self.mock_table
        
        # Mock table.load() to raise ResourceNotFoundException
        error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
        self.mock_table.load.side_effect = ClientError(error_response, 'DescribeTable')
        
        # Mock create_table to return a mock table with wait_until_exists
        mock_created_table = Mock()
        self.mock_dynamodb.create_table.return_value = mock_created_table

        # Act
        service = LoungeService()

        # Assert
        self.mock_dynamodb.create_table.assert_called()
        mock_created_table.wait_until_exists.assert_called()

    @patch('lounge_service.boto3.resource')
    def test_ensure_table_exists_other_error(self, mock_boto3_resource):
        """Test _ensure_table_exists with other client errors."""
        # Arrange
        from botocore.exceptions import ClientError
        mock_boto3_resource.return_value = self.mock_dynamodb
        self.mock_dynamodb.Table.return_value = self.mock_table
        
        # Mock table.load() to raise a different error
        error_response = {'Error': {'Code': 'AccessDeniedException'}}
        self.mock_table.load.side_effect = ClientError(error_response, 'DescribeTable')

        # Act
        service = LoungeService()

        # Assert
        # Should not call create_table for other errors
        self.mock_dynamodb.create_table.assert_not_called()


class TestLoungeServiceIntegration(unittest.TestCase):
    """Integration tests for LoungeService with multiple method interactions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        with patch('lounge_service.boto3.resource'):
            with patch.object(LoungeService, '_ensure_table_exists'):
                self.service = LoungeService()
                self.service.lounges_table = Mock()
                self.service.providers_table = Mock()
                self.service.dynamodb = Mock()

    def test_full_workflow_integration(self):
        """Test a full workflow of creating samples and retrieving data."""
        # Arrange - Mock successful sample creation
        mock_lounges_batch_writer = Mock()
        mock_providers_batch_writer = Mock()
        
        # Mock context managers properly
        mock_lounges_context = Mock()
        mock_providers_context = Mock()
        mock_lounges_context.__enter__ = Mock(return_value=mock_lounges_batch_writer)
        mock_lounges_context.__exit__ = Mock(return_value=None)
        mock_providers_context.__enter__ = Mock(return_value=mock_providers_batch_writer)
        mock_providers_context.__exit__ = Mock(return_value=None)
        
        self.service.lounges_table.batch_writer.return_value = mock_lounges_context
        self.service.providers_table.batch_writer.return_value = mock_providers_context

        # Mock data retrieval
        mock_lounges = [
            {
                "airport": "JFK",
                "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                "name": "Delta Sky Club Terminal 4",
                "access_providers": ["Delta SkyMiles"]
            }
        ]
        mock_providers = [
            {
                "provider_name": "Delta SkyMiles",
                "guest_policy": "Varies by status",
                "conditions": "Flying Delta same day"
            }
        ]

        self.service.lounges_table.query.return_value = {"Items": mock_lounges}
        self.service.lounges_table.get_item.return_value = {"Item": mock_lounges[0]}
        self.service.dynamodb.batch_get_item.return_value = {
            "Responses": {"AccessProviders": mock_providers}
        }

        # Act - Test full workflow
        create_result = self.service.create_sample_lounges()
        lounges_result = self.service.get_lounges_by_airport("JFK")
        lounge_result = self.service.get_lounge_by_id("JFK", "JFK_DELTA_SKY_CLUB_T4")
        detailed_result = self.service.get_lounges_with_access_rules("JFK")

        # Assert
        self.assertTrue(create_result)
        self.assertEqual(len(lounges_result), 1)
        self.assertEqual(lounge_result["lounge_id"], "JFK_DELTA_SKY_CLUB_T4")
        self.assertEqual(len(detailed_result["lounges"]), 1)
        self.assertEqual(len(detailed_result["lounges"][0]["access_details"]), 1)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)