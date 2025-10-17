"""
Flights API Client for Amadeus Flight Schedule API
Handles authentication and API calls for flight schedule information
"""
import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class FlightsApiClient:
    """Client for Amadeus Flight Schedule API"""
    
    def __init__(self):
        self.base_url = "https://test.api.amadeus.com"
        self._secrets_cache = {'amadeus_credentials': None, 'fetched_at': None}
        self._token_cache = {'access_token': None, 'expiry': None}
    
    def _get_amadeus_credentials(self) -> Dict[str, str]:
        """
        Fetch Amadeus credentials from AWS Secrets Manager with caching
        """
        # Return cached credentials if recently fetched (within 1 hour)
        if self._secrets_cache['amadeus_credentials'] and self._secrets_cache['fetched_at']:
            elapsed = datetime.now() - self._secrets_cache['fetched_at']
            if elapsed.total_seconds() < 3600:
                return self._secrets_cache['amadeus_credentials']
        
        # Fetch from Secrets Manager
        secret_name = "autorescue/amadeus/credentials"
        region_name = os.getenv('AWS_REGION', 'us-east-1')
        
        client = boto3.client('secretsmanager', region_name=region_name)
        
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response['SecretString'])
            
            # Cache the credentials
            self._secrets_cache['amadeus_credentials'] = secret
            self._secrets_cache['fetched_at'] = datetime.now()
            
            return secret
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Amadeus credentials from Secrets Manager: {str(e)}")
    
    def _get_amadeus_token(self) -> str:
        """
        Get Amadeus OAuth2 token with caching
        """
        now = datetime.now()
        
        # Return cached token if still valid
        if self._token_cache['access_token'] and self._token_cache['expiry'] and now < self._token_cache['expiry']:
            return self._token_cache['access_token']
        
        # Get credentials from Secrets Manager
        credentials = self._get_amadeus_credentials()
        
        # Request new token
        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": credentials['client_id'],
            "client_secret": credentials['client_secret']
        }
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self._token_cache['access_token'] = token_data['access_token']
        # Amadeus tokens expire in 1799 seconds, cache for 25 minutes to be safe
        self._token_cache['expiry'] = now + timedelta(seconds=1500)
        
        return self._token_cache['access_token']
    
    def get_flight_schedule(
        self,
        carrier_code: str,
        flight_number: str,
        scheduled_departure_date: str,
        operational_suffix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get flight schedule information for a specific flight
        
        Args:
            carrier_code (str): IATA carrier code (e.g., 'AA', 'DL', 'UA')
            flight_number (str): Flight number (e.g., '1234')
            scheduled_departure_date (str): Departure date in YYYY-MM-DD format (local to departure airport)
            operational_suffix (str, optional): Operational suffix like 'A' or 'B'
        
        Returns:
            dict: Flight schedule information or error details
        """
        try:
            # Get access token
            token = self._get_amadeus_token()
            
            # Prepare the API call
            url = f"{self.base_url}/v2/schedule/flights"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Build query parameters
            params = {
                "carrierCode": carrier_code.upper(),
                "flightNumber": flight_number,
                "scheduledDepartureDate": scheduled_departure_date
            }
            
            if operational_suffix:
                params["operationalSuffix"] = operational_suffix
            
            # Make the API call
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            flight_data = response.json()
            
            # Extract relevant information
            if "data" in flight_data and flight_data["data"]:
                flight_info = flight_data["data"][0]  # Take first result
                
                # Extract key information
                result = {
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "scheduled_departure_date": scheduled_departure_date,
                    "operational_suffix": operational_suffix,
                    "flight_designator": flight_info.get("flightDesignator", {}),
                    "departure": flight_info.get("departure", {}),
                    "arrival": flight_info.get("arrival", {}),
                    "aircraft": flight_info.get("aircraft", {}),
                    "operating_carrier": flight_info.get("operatingCarrier", {}),
                    "status": "success"
                }
                
                # Add departure and arrival airport codes if available
                if "departure" in flight_info and "iataCode" in flight_info["departure"]:
                    result["departure_airport"] = flight_info["departure"]["iataCode"]
                if "arrival" in flight_info and "iataCode" in flight_info["arrival"]:
                    result["arrival_airport"] = flight_info["arrival"]["iataCode"]
                
                return result
            else:
                return {
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "scheduled_departure_date": scheduled_departure_date,
                    "status": "no_flights_found",
                    "message": "No flight data found for the specified criteria"
                }
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                return {
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "scheduled_departure_date": scheduled_departure_date,
                    "status": "error",
                    "error": "Invalid request parameters",
                    "details": str(e)
                }
            elif e.response.status_code == 401:
                return {
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "scheduled_departure_date": scheduled_departure_date,
                    "status": "error",
                    "error": "Authentication failed",
                    "details": "Invalid or expired Amadeus API credentials"
                }
            else:
                return {
                    "carrier_code": carrier_code.upper(),
                    "flight_number": flight_number,
                    "scheduled_departure_date": scheduled_departure_date,
                    "status": "error",
                    "error": f"HTTP {e.response.status_code}",
                    "details": str(e)
                }
        except Exception as e:
            return {
                "carrier_code": carrier_code.upper(),
                "flight_number": flight_number,
                "scheduled_departure_date": scheduled_departure_date,
                "status": "error",
                "error": "Unexpected error",
                "details": str(e)
            }
    
    def validate_flight_parameters(
        self,
        carrier_code: str,
        flight_number: str,
        scheduled_departure_date: str
    ) -> Dict[str, Any]:
        """
        Validate flight schedule parameters
        
        Args:
            carrier_code (str): IATA carrier code
            flight_number (str): Flight number
            scheduled_departure_date (str): Departure date in YYYY-MM-DD format
        
        Returns:
            dict: Validation result with is_valid boolean and error messages if any
        """
        errors = []
        
        # Validate carrier code
        if not carrier_code or not isinstance(carrier_code, str):
            errors.append("Carrier code is required and must be a string")
        elif len(carrier_code) != 2:
            errors.append("Carrier code must be exactly 2 characters (IATA code)")
        elif not carrier_code.isalpha():
            errors.append("Carrier code must contain only alphabetic characters")
        
        # Validate flight number
        if not flight_number or not isinstance(flight_number, str):
            errors.append("Flight number is required and must be a string")
        elif not flight_number.isdigit():
            errors.append("Flight number must contain only numeric characters")
        
        # Validate departure date
        if not scheduled_departure_date or not isinstance(scheduled_departure_date, str):
            errors.append("Scheduled departure date is required and must be a string")
        else:
            try:
                # Try to parse the date
                datetime.strptime(scheduled_departure_date, "%Y-%m-%d")
            except ValueError:
                errors.append("Scheduled departure date must be in YYYY-MM-DD format")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }