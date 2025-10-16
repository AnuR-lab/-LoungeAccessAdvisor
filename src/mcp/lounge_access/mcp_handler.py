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
        return {
            "user_id": user_data.get("user_id"),
            "name": user_data.get("name"),
            "home_airport": user_data.get("home_airport"),
            "memberships": user_data.get("memberships", [])
        }
    
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
