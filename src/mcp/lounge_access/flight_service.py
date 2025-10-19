"""
Flight Service for LoungeAccessAdvisor
Integrates Amadeus API for real-time flight information
Uses the same implementation as AutoRescue project
"""
import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


# Amadeus API Configuration - Same as AutoRescue
AMADEUS_BASE_URL = "https://test.api.amadeus.com"

# Secrets cache (Lambda container reuse) - Same pattern as AutoRescue
_secrets_cache = {
    'amadeus_credentials': None,
    'fetched_at': None
}

# Token cache (Lambda container reuse) - Same pattern as AutoRescue
_token_cache = {
    'access_token': None,
    'expiry': None
}


def _get_amadeus_credentials() -> Dict[str, str]:
    """
    Fetch Amadeus credentials from AWS Secrets Manager with caching
    Uses the same secret name as AutoRescue project
    """
    # Return cached credentials if recently fetched (within 1 hour)
    if _secrets_cache['amadeus_credentials'] and _secrets_cache['fetched_at']:
        elapsed = datetime.now() - _secrets_cache['fetched_at']
        if elapsed.total_seconds() < 3600:
            return _secrets_cache['amadeus_credentials']
    
    # Fetch from Secrets Manager - Same secret name as AutoRescue
    secret_name = "autorescue/amadeus/credentials"
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        # Cache the credentials
        _secrets_cache['amadeus_credentials'] = secret
        _secrets_cache['fetched_at'] = datetime.now()
        
        return secret
    except Exception as e:
        raise RuntimeError(f"Failed to fetch Amadeus credentials from Secrets Manager: {str(e)}")


def _get_amadeus_token() -> str:
    """
    Get Amadeus OAuth2 token with caching
    Identical implementation to AutoRescue
    """
    now = datetime.now()
    
    # Return cached token if still valid
    if _token_cache['access_token'] and _token_cache['expiry'] and now < _token_cache['expiry']:
        return _token_cache['access_token']
    
    # Get credentials from Secrets Manager
    credentials = _get_amadeus_credentials()
    
    # Request new token
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": credentials['client_id'],
        "client_secret": credentials['client_secret']
    }
    
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    _token_cache['access_token'] = token_data['access_token']
    # Amadeus tokens expire in 1799 seconds, cache for 25 minutes to be safe
    _token_cache['expiry'] = now + timedelta(seconds=1500)
    
    return _token_cache['access_token']


class FlightService:
    """Service for retrieving flight information via Amadeus API"""
    
    def __init__(self):
        # Use the same base URL as AutoRescue
        self.base_url = AMADEUS_BASE_URL
    
    def get_flight_status(self, flight_number: str, departure_date: str, operational_suffix: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time flight status information using Amadeus Schedule API
        
        Args:
            flight_number: Flight number (e.g., 'AA123')
            departure_date: Date in YYYY-MM-DD format (local to departure airport)
            operational_suffix: Optional suffix like "A" or "B" for flight variants
            
        Returns:
            Flight status information including delays, gates, terminals
        """
        try:
            access_token = _get_amadeus_token()
            
            # Parse flight number to extract carrier code and flight number
            # Handle various formats: AA123, AA 123, American123, etc.
            flight_number = flight_number.strip().upper()
            
            # Extract carrier code (first 2-3 characters that are letters)
            carrier_code = ""
            flight_num = ""
            
            for i, char in enumerate(flight_number):
                if char.isalpha():
                    carrier_code += char
                else:
                    flight_num = flight_number[i:].strip()
                    break
            
            # Validate carrier code (should be 2 characters for IATA)
            if len(carrier_code) < 2:
                return {
                    "flight_number": flight_number,
                    "status": "error",
                    "error": "Invalid flight number format. Expected format: AA123"
                }
            
            # Take only first 2 characters for IATA code
            carrier_code = carrier_code[:2]
            
            # Remove any non-numeric characters from flight number
            flight_num = ''.join(filter(str.isdigit, flight_num))
            
            if not flight_num:
                return {
                    "flight_number": flight_number,
                    "status": "error", 
                    "error": "No flight number found in input"
                }
            
            # Build API request - Using exact parameters from Amadeus documentation
            url = f"{self.base_url}/v2/schedule/flights"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "carrierCode": carrier_code,
                "flightNumber": flight_num,
                "scheduledDepartureDate": departure_date
            }
            
            # Add operational suffix if provided
            if operational_suffix:
                params["operationalSuffix"] = operational_suffix
            
            print(f"[FLIGHT_SERVICE] Calling Amadeus API: {url}")
            print(f"[FLIGHT_SERVICE] Parameters: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            print(f"[FLIGHT_SERVICE] API Response: {json.dumps(data, indent=2)}")
            
            if not data.get('data') or len(data['data']) == 0:
                return {
                    "flight_number": flight_number,
                    "carrier_code": carrier_code,
                    "flight_num": flight_num,
                    "departure_date": departure_date,
                    "status": "not_found",
                    "message": f"No flight found for {carrier_code}{flight_num} on {departure_date}"
                }
            
            # Process the first flight result
            flight_data = data['data'][0]
            
            # Extract flight designator information
            flight_designator = flight_data.get('flightDesignator', {})
            departure_info = flight_designator.get('departure', {})
            arrival_info = flight_designator.get('arrival', {})
            
            # Extract operational information (gates, terminals, actual times)
            departure_ops = flight_data.get('departure', {})
            arrival_ops = flight_data.get('arrival', {})
            
            return {
                "flight_number": flight_number,
                "carrier_code": carrier_code,
                "flight_num": flight_num,
                "departure_date": departure_date,
                "status": "found",
                "departure": {
                    "airport": departure_info.get('iataCode'),
                    "terminal": departure_ops.get('terminal'),
                    "gate": departure_ops.get('gate'),
                    "scheduled_time": departure_info.get('scheduledTime'),
                    "estimated_time": departure_ops.get('estimatedTime'),
                    "actual_time": departure_ops.get('actualTime')
                },
                "arrival": {
                    "airport": arrival_info.get('iataCode'),
                    "terminal": arrival_ops.get('terminal'),
                    "gate": arrival_ops.get('gate'),
                    "scheduled_time": arrival_info.get('scheduledTime'),
                    "estimated_time": arrival_ops.get('estimatedTime'),
                    "actual_time": arrival_ops.get('actualTime')
                },
                "aircraft": flight_data.get('aircraft', {}),
                "operating_carrier": flight_data.get('operatingCarrier', {}),
                "flight_designator": flight_designator,
                "raw_data": flight_data  # Include raw data for debugging
            }
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = f" - {error_response.get('error_description', str(error_response))}"
            except:
                error_detail = f" - HTTP {e.response.status_code}"
                
            return {
                "flight_number": flight_number,
                "status": "error",
                "error": f"Amadeus API error{error_detail}"
            }
        except Exception as e:
            return {
                "flight_number": flight_number,
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def search_flights_for_lounge_planning(
        self, 
        origin: str, 
        destination: str, 
        departure_date: str,
        return_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search flights specifically for lounge access planning
        Uses the same Amadeus Flight Offers API as AutoRescue
        
        Args:
            origin: Origin airport code
            destination: Destination airport code  
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Optional return date for round trips
            
        Returns:
            Flight options with terminal and timing information for lounge planning
        """
        try:
            access_token = _get_amadeus_token()
            
            url = f"{self.base_url}/v2/shopping/flight-offers"
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDate": departure_date,
                "adults": "1",
                "max": "10",
                "currencyCode": "USD"
            }
            
            if return_date:
                params["returnDate"] = return_date
            
            print(f"[FLIGHT_SERVICE] Searching flights: {origin} -> {destination} on {departure_date}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get('data'):
                return {
                    "origin": origin,
                    "destination": destination,
                    "flights": [],
                    "message": "No flights found"
                }
            
            # Process flights for lounge planning context - Same format as AutoRescue
            processed_flights = []
            for offer in data['data'][:10]:
                flight_info = {
                    "id": offer['id'],
                    "price": {
                        "total": offer['price']['total'],
                        "currency": offer['price']['currency']
                    },
                    "itineraries": []
                }
                
                for itinerary in offer['itineraries']:
                    segments = []
                    for segment in itinerary['segments']:
                        # Enhanced segment info for lounge planning
                        segments.append({
                            "departure": {
                                "airport": segment['departure']['iataCode'],
                                "terminal": segment['departure'].get('terminal'),
                                "time": segment['departure']['at']
                            },
                            "arrival": {
                                "airport": segment['arrival']['iataCode'],
                                "terminal": segment['arrival'].get('terminal'),
                                "time": segment['arrival']['at']
                            },
                            "carrier": segment['carrierCode'],
                            "flight_number": segment['number'],
                            "duration": segment['duration'],
                            "aircraft": segment.get('aircraft', {}),
                            # Additional info for lounge planning
                            "full_flight_number": f"{segment['carrierCode']}{segment['number']}"
                        })
                    
                    flight_info['itineraries'].append({
                        "duration": itinerary['duration'],
                        "segments": segments
                    })
                
                processed_flights.append(flight_info)
            
            return {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "flights": processed_flights,
                "total_found": len(processed_flights),
                "status": "success"
            }
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_response = e.response.json()
                error_detail = f" - {error_response.get('error_description', str(error_response))}"
            except:
                error_detail = f" - HTTP {e.response.status_code}"
                
            return {
                "origin": origin,
                "destination": destination,
                "flights": [],
                "status": "error",
                "error": f"Amadeus API error{error_detail}"
            }
        except Exception as e:
            return {
                "origin": origin,
                "destination": destination,
                "flights": [],
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }