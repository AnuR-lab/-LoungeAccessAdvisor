import json

import boto3
from botocore.exceptions import ClientError
from user_profile_service import UserProfileService
from lounge_service import LoungeService
from flights_api_client import FlightsApiClient


class LoungeAccessClient:
    def __init__(self):
        self.api_client = self._get_client()
        self.user_profile_service = UserProfileService()
        self.lounge_service = LoungeService()
        self.flights_api_client = FlightsApiClient()

    def _get_client(self):
        api_client = None
        return api_client
    
    def get_user(self, user_id: str):
        """
        Retrieves user information by user_id from DynamoDB UserProfile table.
        
        Args:
            user_id (str): The unique identifier for the user
            
        Returns:
            dict: User information containing user_id, name, home_airport, and memberships
                 Returns None if user not found or error occurs
        """
        return self.user_profile_service.get_user(user_id)
    
    def create_sample_users(self):
        """
        Creates sample users in the DynamoDB UserProfile table for testing.
        Delegates to the UserProfileService.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.user_profile_service.create_sample_users()
    
    def get_lounges_by_airport(self, airport_code: str):
        """
        Retrieves all lounges available at a specific airport.
        
        Args:
            airport_code (str): The 3-letter airport code (e.g., 'LAX', 'JFK', 'ORD')
            
        Returns:
            list: List of lounge information for the specified airport.
                 Each lounge contains: airport, lounge_id, name, terminal, 
                 access_providers, amenities, hours, peak_hours, avg_wait_minutes,
                 crowd_level, and rating.
                 Returns empty list if no lounges found or error occurs.
        """
        if not airport_code or not isinstance(airport_code, str) or not airport_code.strip():
            return []

        return self.lounge_service.get_lounges_with_access_rules(airport_code)

    def get_lounge_by_id(self, airport_code: str, lounge_id: str):
        """
        Retrieves a specific lounge by airport and lounge ID.
        
        Args:
            airport_code (str): The 3-letter airport code
            lounge_id (str): The unique lounge identifier
            
        Returns:
            dict: Lounge information or None if not found
        """
        if not airport_code or not lounge_id:
            return None
        
        return self.lounge_service.get_lounge_by_id(airport_code, lounge_id)
    
    def create_sample_lounges(self):
        """
        Creates sample lounges in the DynamoDB Lounges table for testing.
        Delegates to the LoungeService.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.lounge_service.create_sample_lounges()
    
    def search_lounges_by_access_provider(self, airport_code: str, access_provider: str):
        """
        Searches for lounges at a specific airport that accept a particular access provider.
        
        Args:
            airport_code (str): The 3-letter airport code
            access_provider (str): The access provider to search for (e.g., 'Amex Platinum', 'Priority Pass')
            
        Returns:
            list: Filtered list of lounges that accept the specified access provider
        """
        if not airport_code or not access_provider:
            return []
        
        all_lounges = self.lounge_service.get_lounges_by_airport(airport_code)
        
        # Filter lounges by access provider
        matching_lounges = []
        for lounge in all_lounges:
            access_providers = lounge.get('access_providers', [])
            if any(access_provider.lower() in provider.lower() for provider in access_providers):
                matching_lounges.append(lounge)
        
        return matching_lounges
    
    def get_lounges_with_amenity(self, airport_code: str, amenity: str):
        """
        Searches for lounges at a specific airport that offer a particular amenity.
        
        Args:
            airport_code (str): The 3-letter airport code
            amenity (str): The amenity to search for (e.g., 'Showers', 'Buffet', 'WiFi')
            
        Returns:
            list: Filtered list of lounges that offer the specified amenity
        """
        if not airport_code or not amenity:
            return []
        
        all_lounges = self.lounge_service.get_lounges_by_airport(airport_code)
        
        # Filter lounges by amenity
        matching_lounges = []
        for lounge in all_lounges:
            amenities = lounge.get('amenities', [])
            if any(amenity.lower() in amenity_item.lower() for amenity_item in amenities):
                matching_lounges.append(lounge)
        
        return matching_lounges
    
    def get_flight_schedule(self, carrier_code: str, flight_number: str, scheduled_departure_date: str, operational_suffix: str = None):
        """
        Get flight schedule information using Amadeus API
        
        Args:
            carrier_code (str): IATA carrier code (e.g., 'AA', 'DL', 'UA')
            flight_number (str): Flight number (e.g., '1234')
            scheduled_departure_date (str): Departure date in YYYY-MM-DD format (local to departure airport)
            operational_suffix (str, optional): Operational suffix like 'A' or 'B'
        
        Returns:
            dict: Flight schedule information or error details
        """
        return self.flights_api_client.get_flight_schedule(
            carrier_code=carrier_code,
            flight_number=flight_number,
            scheduled_departure_date=scheduled_departure_date,
            operational_suffix=operational_suffix
        )
    
    def validate_flight_parameters(self, carrier_code: str, flight_number: str, scheduled_departure_date: str):
        """
        Validate flight schedule parameters
        
        Args:
            carrier_code (str): IATA carrier code
            flight_number (str): Flight number
            scheduled_departure_date (str): Departure date in YYYY-MM-DD format
        
        Returns:
            dict: Validation result with is_valid boolean and error messages if any
        """
        return self.flights_api_client.validate_flight_parameters(
            carrier_code=carrier_code,
            flight_number=flight_number,
            scheduled_departure_date=scheduled_departure_date
        )
