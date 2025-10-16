import json
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ClientError
from user_profile_service import UserProfileService
from lounge_service import LoungeService
from flight_service import FlightService


class LoungeAccessClient:
    def __init__(self):
        self.api_client = self._get_client()
        self.user_profile_service = UserProfileService()
        self.lounge_service = LoungeService()
        self.flight_service = FlightService()

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
    
    # ===== FLIGHT-AWARE LOUNGE METHODS =====
    
    def get_flight_aware_lounge_recommendations(
        self,
        flight_number: str,
        departure_date: str,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get intelligent lounge recommendations based on specific flight information.
        
        Args:
            flight_number (str): Flight number (e.g., 'AA123')
            departure_date (str): Departure date in YYYY-MM-DD format
            user_id (str): User ID to get membership information
            preferences (dict, optional): User preferences
            
        Returns:
            dict: Flight-aware lounge recommendations
        """
        try:
            # Get user memberships
            user_data = self.get_user(user_id)
            if not user_data or user_data.get("error"):
                return {
                    "status": "error",
                    "error": "User not found or no membership information available"
                }
            
            user_memberships = user_data.get("memberships", [])
            
            # Get flight information
            flight_info = self.flight_service.get_flight_status(flight_number, departure_date)
            
            if flight_info.get("status") != "found":
                return {
                    "flight_number": flight_number,
                    "status": "flight_not_found",
                    "message": "Could not retrieve flight information. Please check flight number and date."
                }
            
            departure_airport = flight_info["departure"]["airport"]
            
            # Get lounges at departure airport
            lounges_response = self.get_lounges_by_airport(departure_airport)
            
            if not lounges_response or not lounges_response.get("lounges"):
                return {
                    "flight_number": flight_number,
                    "departure_airport": departure_airport,
                    "status": "no_lounges_found",
                    "message": f"No lounges found at {departure_airport}"
                }
            
            # Use the enhanced MCP handler function
            from mcp_handler import get_flight_aware_lounge_recommendations
            
            return get_flight_aware_lounge_recommendations(
                flight_number=flight_number,
                departure_date=departure_date,
                user_memberships=user_memberships,
                api_client=self,
                preferences=preferences
            )
            
        except Exception as e:
            return {
                "flight_number": flight_number,
                "status": "error",
                "error": str(e)
            }
    
    def analyze_multi_flight_lounge_strategy(
        self,
        flights: List[Dict[str, str]],
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze complete itinerary and provide lounge strategy for multi-flight journeys.
        
        Args:
            flights (List[Dict]): List of flights with flight_number and departure_date
            user_id (str): User ID for membership information
            preferences (dict, optional): User preferences
            
        Returns:
            dict: Complete itinerary lounge strategy
        """
        try:
            # Get user memberships
            user_data = self.get_user(user_id)
            if not user_data or user_data.get("error"):
                return {
                    "status": "error",
                    "error": "User not found or no membership information available"
                }
            
            user_memberships = user_data.get("memberships", [])
            
            # Use the enhanced MCP handler function
            from mcp_handler import analyze_layover_lounge_strategy
            
            return analyze_layover_lounge_strategy(
                connecting_flights=flights,
                user_memberships=user_memberships,
                api_client=self,
                preferences=preferences
            )
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_flight_status_with_lounge_impact(
        self,
        flight_number: str,
        departure_date: str
    ) -> Dict[str, Any]:
        """
        Get flight status and analyze impact on lounge access timing.
        
        Args:
            flight_number (str): Flight number
            departure_date (str): Departure date in YYYY-MM-DD format
            
        Returns:
            dict: Flight status with lounge timing recommendations
        """
        try:
            flight_info = self.flight_service.get_flight_status(flight_number, departure_date)
            
            if flight_info.get("status") != "found":
                return flight_info
            
            # Calculate lounge timing impact
            from datetime import datetime, timedelta
            
            scheduled_departure = flight_info["departure"]["scheduled_time"]
            estimated_departure = flight_info["departure"].get("estimated_time", scheduled_departure)
            
            scheduled_dt = datetime.fromisoformat(scheduled_departure.replace('Z', '+00:00'))
            estimated_dt = datetime.fromisoformat(estimated_departure.replace('Z', '+00:00'))
            
            delay_minutes = int((estimated_dt - scheduled_dt).total_seconds() / 60)
            
            # Add lounge timing advice
            flight_info["lounge_impact"] = {
                "delay_minutes": delay_minutes,
                "status": "on_time" if delay_minutes <= 15 else "delayed",
                "lounge_advice": self._generate_delay_lounge_advice(delay_minutes),
                "recommended_lounge_exit_time": (estimated_dt - timedelta(minutes=60)).isoformat()
            }
            
            return flight_info
            
        except Exception as e:
            return {
                "flight_number": flight_number,
                "status": "error",
                "error": str(e)
            }
    
    def _generate_delay_lounge_advice(self, delay_minutes: int) -> str:
        """Generate lounge advice based on flight delay"""
        if delay_minutes <= 15:
            return "Flight is on time - proceed with normal lounge timing"
        elif delay_minutes <= 60:
            return f"Flight delayed {delay_minutes} minutes - you have extra time for lounge visit"
        elif delay_minutes <= 120:
            return f"Significant delay of {delay_minutes} minutes - consider extended lounge stay or meal"
        else:
            return f"Major delay of {delay_minutes} minutes - perfect opportunity for lounge amenities like showers or workspace"
    
    def search_flights_for_lounge_optimization(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        user_id: str,
        return_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search flights with lounge access optimization in mind.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            departure_date (str): Departure date
            user_id (str): User ID for membership information
            return_date (str, optional): Return date for round trips
            
        Returns:
            dict: Flight options ranked by lounge access opportunities
        """
        try:
            # Get user memberships
            user_data = self.get_user(user_id)
            user_memberships = user_data.get("memberships", []) if user_data else []
            
            # Search flights
            flight_results = self.flight_service.search_flights_for_lounge_planning(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date
            )
            
            if flight_results.get("flights"):
                # Enhance each flight with lounge access information
                enhanced_flights = []
                
                for flight in flight_results["flights"]:
                    # Get lounge information for departure airport
                    departure_airport = flight["itineraries"][0]["segments"][0]["departure"]["airport"]
                    lounges_data = self.get_lounges_by_airport(departure_airport)
                    
                    # Count accessible lounges
                    accessible_lounges = 0
                    if lounges_data and lounges_data.get("lounges"):
                        for lounge in lounges_data["lounges"]:
                            lounge_providers = lounge.get("access_providers", [])
                            if any(membership.lower() in provider.lower() 
                                   for membership in user_memberships 
                                   for provider in lounge_providers):
                                accessible_lounges += 1
                    
                    flight["lounge_access"] = {
                        "departure_airport": departure_airport,
                        "accessible_lounges": accessible_lounges,
                        "has_lounge_access": accessible_lounges > 0
                    }
                    
                    enhanced_flights.append(flight)
                
                # Sort by lounge access opportunities (then by price)
                enhanced_flights.sort(
                    key=lambda x: (
                        -x["lounge_access"]["accessible_lounges"],  # More lounges first
                        float(x["price"]["total"])  # Then by price
                    )
                )
                
                flight_results["flights"] = enhanced_flights
            
            return flight_results
            
        except Exception as e:
            return {
                "origin": origin,
                "destination": destination,
                "flights": [],
                "error": str(e)
            }