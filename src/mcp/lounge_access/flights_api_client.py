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
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("flights_api_client")


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
                logger.debug("Using cached Amadeus credentials (age=%ss)", int(elapsed.total_seconds()))
                return self._secrets_cache['amadeus_credentials']
        
        # Fetch from Secrets Manager
        secret_name = "autorescue/amadeus/credentials"
        region_name = os.getenv('AWS_REGION', 'us-east-1')
        
        client = boto3.client('secretsmanager', region_name=region_name)
        
        try:
            start = datetime.now()
            response = client.get_secret_value(SecretId=secret_name)
            duration_ms = int((datetime.now() - start).total_seconds() * 1000)
            secret = json.loads(response['SecretString'])
            logger.debug("Fetched Amadeus credentials from Secrets Manager in %dms", duration_ms)
            self._secrets_cache['amadeus_credentials'] = secret
            self._secrets_cache['fetched_at'] = datetime.now()
            return secret
        except Exception as e:
            logger.error("Error fetching Amadeus credentials: %s", e, exc_info=LOG_LEVEL=="DEBUG")
            raise RuntimeError(f"Failed to fetch Amadeus credentials from Secrets Manager: {str(e)}")
    
    def _get_amadeus_token(self) -> str:
        """
        Get Amadeus OAuth2 token with caching
        """
        now = datetime.now()
        
        # Return cached token if still valid
        if self._token_cache['access_token'] and self._token_cache['expiry'] and now < self._token_cache['expiry']:
            remaining = int((self._token_cache['expiry'] - now).total_seconds())
            logger.debug("Using cached Amadeus token (remaining=%ss)", remaining)
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
        logger.debug("Requesting new Amadeus token: POST %s", url)
        response = requests.post(url, headers=headers, data=data)
        logger.debug("Token response status: %s", response.status_code)
        response.raise_for_status()
        token_data = response.json()
        self._token_cache['access_token'] = token_data['access_token']
        self._token_cache['expiry'] = now + timedelta(seconds=1500)
        logger.debug("Obtained new Amadeus token; cached until %s", self._token_cache['expiry'])
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
            logger.debug("Starting get_flight_schedule carrier=%s flight=%s date=%s suffix=%s", carrier_code, flight_number, scheduled_departure_date, operational_suffix)
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
            logger.debug("Schedule API response status: %s", response.status_code)
            response.raise_for_status()
            flight_data = response.json()
            if "data" in flight_data and flight_data["data"]:
                flight_info = flight_data["data"][0]
                flight_points = flight_info.get("flightPoints", [])
                segments = flight_info.get("segments", [])
                legs = flight_info.get("legs", [])
                departure_airport = None
                arrival_airport = None
                if flight_points:
                    if len(flight_points) >= 1 and "iataCode" in flight_points[0]:
                        departure_airport = flight_points[0]["iataCode"]
                    if len(flight_points) >= 2 and "iataCode" in flight_points[-1]:
                        arrival_airport = flight_points[-1]["iataCode"]
                departure_timings = []
                arrival_timings = []
                if flight_points:
                    for idx, fp in enumerate(flight_points):
                        if idx == 0 and fp.get("departure", {}).get("timings"):
                            departure_timings = fp["departure"]["timings"]
                        if idx == len(flight_points) - 1 and fp.get("arrival", {}).get("timings"):
                            arrival_timings = fp["arrival"]["timings"]
                aircraft_type = None
                if legs:
                    ae = legs[0].get("aircraftEquipment", {})
                    aircraft_type = ae.get("aircraftType")
                operating_carrier = None
                if segments:
                    partnership = segments[0].get("partnership", {})
                    operating_flight = partnership.get("operatingFlight", {})
                    if operating_flight:
                        operating_carrier = {
                            "carrierCode": operating_flight.get("carrierCode"),
                            "flightNumber": operating_flight.get("flightNumber")
                        }
                result = {
                    "status": "success",
                    "meta": {
                        "count": flight_data.get("meta", {}).get("count"),
                        "links": flight_data.get("meta", {}).get("links", {})
                    },
                    "requested": {
                        "carrier_code": carrier_code.upper(),
                        "flight_number": flight_number,
                        "scheduled_departure_date": scheduled_departure_date,
                        "operational_suffix": operational_suffix
                    },
                    "flight_designator": flight_info.get("flightDesignator", {}),
                    "departure_airport": departure_airport,
                    "arrival_airport": arrival_airport,
                    "departure_timings": departure_timings,
                    "arrival_timings": arrival_timings,
                    "segments": segments,
                    "legs": legs,
                    "aircraft_type": aircraft_type,
                    "operating_carrier": operating_carrier,
                    "raw": flight_info
                }
                logger.debug(
                    "Flight schedule mapped: carrier=%s flight=%s dep=%s arr=%s STD=%s STA=%s",
                    carrier_code.upper(),
                    flight_number,
                    departure_airport,
                    arrival_airport,
                    departure_timings[0]["value"] if departure_timings else None,
                    arrival_timings[0]["value"] if arrival_timings else None
                )
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
            status_code = e.response.status_code if e.response is not None else "unknown"
            logger.warning("HTTP error from schedule API status=%s carrier=%s flight=%s date=%s", status_code, carrier_code, flight_number, scheduled_departure_date)
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
                # Invalidate token cache for next call
                self._token_cache['access_token'] = None
                self._token_cache['expiry'] = None
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
            logger.error("Unexpected error in get_flight_schedule: %s", e, exc_info=LOG_LEVEL=="DEBUG")
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