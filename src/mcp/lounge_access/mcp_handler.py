"""
This module defines tools that interact with an external API client.
"""

def get_user(user_id, api_client):
    """
    Retrieves user information including home airport and memberships.
    
    Args:
        user_id (str): The unique identifier for the user
        api_client: The API client instance for data retrieval
        
    Returns:
        dict: User information containing user_id, name, home_airport, and memberships
    """
    user_data = api_client.get_user(user_id)
    
    if user_data:
        return user_data
        
    
    return {
        "user_id": user_id,
        "name": None,
        "home_airport": None,
        "memberships": [],
        "error": "User not found"
    }


def get_lounges_with_access_rules(airport, api_client):
    """
    Retrieves lounges for a given airport with detailed access rules.
    
    Args:
        airport (str): The airport code (e.g., 'LAX', 'JFK')
        api_client: The API client instance for data retrieval
        
    Returns:
        dict: Airport lounges with access rules and detailed information
    """
    try:
        lounges_data = api_client.get_lounges_by_airport(airport)
        
        if lounges_data:
            return {
                "airport": airport,
                "lounges": lounges_data.get("lounges", []),
                "total_lounges": len(lounges_data.get("lounges", [])),
                "status": "success"
            }
        
        return {
            "airport": airport,
            "lounges": [],
            "total_lounges": 0,
            "status": "no_lounges_found"
        }
        
    except Exception as e:
        return {
            "airport": airport,
            "lounges": [],
            "total_lounges": 0,
            "status": "error",
            "error": str(e)
        }


def get_flight_schedule(carrier_code, flight_number, scheduled_departure_date, api_client, operational_suffix=None):
    """
    Retrieves flight schedule information for a specific flight.
    
    Args:
        carrier_code (str): IATA carrier code (e.g., 'AA', 'DL', 'UA')
        flight_number (str): Flight number (e.g., '1234')
        scheduled_departure_date (str): Departure date in YYYY-MM-DD format (local to departure airport)
        api_client: The API client instance for data retrieval
        operational_suffix (str, optional): Operational suffix like 'A' or 'B'
        
    Returns:
        dict: Flight schedule information with departure/arrival details and airport codes
    """
    try:
        flight_data = api_client.get_flight_schedule(
            carrier_code=carrier_code,
            flight_number=flight_number,
            scheduled_departure_date=scheduled_departure_date,
            operational_suffix=operational_suffix
        )
        
        if flight_data and flight_data.get("status") == "success":
            # Extract airport codes for potential lounge lookup
            departure_airport = flight_data.get("departure_airport")
            arrival_airport = flight_data.get("arrival_airport")
            
            # Enhance the response with lounge availability hints
            result = {
                "flight_info": flight_data,
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "status": "success"
            }
            
            # Optionally add lounge availability information
            if departure_airport:
                try:
                    departure_lounges = api_client.get_lounges_by_airport(departure_airport)
                    result["departure_lounges_available"] = bool(departure_lounges.get("lounges"))
                except:
                    result["departure_lounges_available"] = None
            
            if arrival_airport:
                try:
                    arrival_lounges = api_client.get_lounges_by_airport(arrival_airport)
                    result["arrival_lounges_available"] = bool(arrival_lounges.get("lounges"))
                except:
                    result["arrival_lounges_available"] = None
            
            return result
        
        return {
            "flight_info": flight_data,
            "status": flight_data.get("status", "error"),
            "message": flight_data.get("message", "No flight data available")
        }
        
    except Exception as e:
        return {
            "carrier_code": carrier_code,
            "flight_number": flight_number,
            "scheduled_departure_date": scheduled_departure_date,
            "status": "error",
            "error": str(e)
        }
