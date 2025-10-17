"""
Test module for flight schedule functionality
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
import sys
import os

# Ensure the tests can import modules from this package directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from flights_api_client import FlightsApiClient
from lambda_handler import lambda_handler
from types import SimpleNamespace


def make_context(tool_name=None):
    """Create a lightweight mock Lambda context with optional tool name."""
    client_context = None
    if tool_name is not None:
        client_context = SimpleNamespace(custom={"bedrockAgentCoreToolName": tool_name})
    return SimpleNamespace(client_context=client_context)


class TestFlightsApiClient(unittest.TestCase):
    
    def setUp(self):
        self.client = FlightsApiClient()
    
    def test_validate_flight_parameters_valid(self):
        """Test flight parameter validation with valid inputs"""
        result = self.client.validate_flight_parameters("AA", "1234", "2025-12-25")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["errors"], [])
    
    def test_validate_flight_parameters_invalid_carrier(self):
        """Test flight parameter validation with invalid carrier code"""
        result = self.client.validate_flight_parameters("A", "1234", "2025-12-25")
        self.assertFalse(result["is_valid"])
        self.assertIn("Carrier code must be exactly 2 characters", result["errors"])
    
    def test_validate_flight_parameters_invalid_flight_number(self):
        """Test flight parameter validation with invalid flight number"""
        result = self.client.validate_flight_parameters("AA", "ABC", "2025-12-25")
        self.assertFalse(result["is_valid"])
        self.assertIn("Flight number must contain only numeric characters", result["errors"])
    
    def test_validate_flight_parameters_invalid_date(self):
        """Test flight parameter validation with invalid date format"""
        result = self.client.validate_flight_parameters("AA", "1234", "25-12-2025")
        self.assertFalse(result["is_valid"])
        self.assertIn("Scheduled departure date must be in YYYY-MM-DD format", result["errors"])
    
    def test_validate_flight_parameters_multiple_errors(self):
        """Test flight parameter validation with multiple invalid inputs"""
        result = self.client.validate_flight_parameters("", "ABC", "invalid-date")
        self.assertFalse(result["is_valid"])
        self.assertEqual(len(result["errors"]), 3)
    
    @patch("flights_api_client.boto3.client")
    @patch("flights_api_client.requests.post")
    @patch("flights_api_client.requests.get")
    def test_get_flight_schedule_success(self, mock_get, mock_post, mock_boto_client):
        """Test successful flight schedule retrieval"""
        # Mock secrets manager
        mock_secrets_client = MagicMock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret'
            })
        }
        
        # Mock OAuth token response
        mock_post.return_value.json.return_value = {'access_token': 'test_token'}
        mock_post.return_value.raise_for_status = MagicMock()
        
        # Mock flight schedule response
        mock_flight_response = {
            "data": [{
                "flightDesignator": {"carrierCode": "AA", "flightNumber": "1234"},
                "departure": {"iataCode": "JFK", "scheduledTime": "2025-12-25T10:00:00"},
                "arrival": {"iataCode": "LAX", "scheduledTime": "2025-12-25T13:00:00"},
                "aircraft": {"code": "32B"},
                "operatingCarrier": {"carrierCode": "AA"}
            }]
        }
        mock_get.return_value.json.return_value = mock_flight_response
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = self.client.get_flight_schedule("AA", "1234", "2025-12-25")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["carrier_code"], "AA")
        self.assertEqual(result["flight_number"], "1234")
        self.assertEqual(result["departure_airport"], "JFK")
        self.assertEqual(result["arrival_airport"], "LAX")
    
    @patch("flights_api_client.boto3.client")
    def test_get_flight_schedule_credentials_error(self, mock_boto_client):
        """Test flight schedule retrieval with credentials error"""
        mock_secrets_client = MagicMock()
        mock_boto_client.return_value = mock_secrets_client
        mock_secrets_client.get_secret_value.side_effect = Exception("Credentials not found")
        
        result = self.client.get_flight_schedule("AA", "1234", "2025-12-25")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result)


class TestFlightScheduleLambdaHandler(unittest.TestCase):
    
    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.get_flight_schedule")
    def test_get_flight_schedule_success(self, mock_get_flight_schedule, mock_client_cls):
        """Test successful flight schedule Lambda handler"""
        # Arrange
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        expected_result = {
            "flight_info": {
                "carrier_code": "AA",
                "flight_number": "1234",
                "scheduled_departure_date": "2025-12-25",
                "departure_airport": "JFK",
                "arrival_airport": "LAX",
                "status": "success"
            },
            "departure_airport": "JFK",
            "arrival_airport": "LAX",
            "status": "success"
        }
        mock_get_flight_schedule.return_value = expected_result
        
        ctx = make_context("get_flight_schedule")
        event = {
            "carrier_code": "AA",
            "flight_number": "1234",
            "scheduled_departure_date": "2025-12-25"
        }
        
        # Act
        resp = lambda_handler(event=event, context=ctx)
        
        # Assert
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["result"], expected_result)
        mock_get_flight_schedule.assert_called_once_with(
            carrier_code="AA",
            flight_number="1234",
            scheduled_departure_date="2025-12-25",
            api_client=mock_client,
            operational_suffix=None
        )
    
    @patch("lambda_handler.LoungeAccessClient")
    def test_get_flight_schedule_missing_parameters(self, mock_client_cls):
        """Test flight schedule Lambda handler with missing parameters"""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        ctx = make_context("get_flight_schedule")
        event = {"carrier_code": "AA"}  # Missing flight_number and scheduled_departure_date
        
        resp = lambda_handler(event=event, context=ctx)
        
        self.assertEqual(resp["statusCode"], 400)
        body = json.loads(resp["body"])
        self.assertIn("Missing required parameters", body["error"])
    
    @patch("lambda_handler.LoungeAccessClient")
    @patch("lambda_handler.get_flight_schedule")
    def test_get_flight_schedule_with_suffix(self, mock_get_flight_schedule, mock_client_cls):
        """Test flight schedule Lambda handler with operational suffix"""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        expected_result = {
            "flight_info": {
                "carrier_code": "AA",
                "flight_number": "1234",
                "operational_suffix": "A",
                "status": "success"
            },
            "status": "success"
        }
        mock_get_flight_schedule.return_value = expected_result
        
        ctx = make_context("get_flight_schedule")
        event = {
            "carrier_code": "AA",
            "flight_number": "1234",
            "scheduled_departure_date": "2025-12-25",
            "operational_suffix": "A"
        }
        
        resp = lambda_handler(event=event, context=ctx)
        
        self.assertEqual(resp["statusCode"], 200)
        body = json.loads(resp["body"])
        self.assertEqual(body["result"], expected_result)
        mock_get_flight_schedule.assert_called_once_with(
            carrier_code="AA",
            flight_number="1234",
            scheduled_departure_date="2025-12-25",
            api_client=mock_client,
            operational_suffix="A"
        )


if __name__ == "__main__":
    unittest.main()