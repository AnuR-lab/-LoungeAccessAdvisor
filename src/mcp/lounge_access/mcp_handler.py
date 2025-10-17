"""
This module defines tools that interact with an external API client.
"""

from typing import Optional, Dict, Any

from src.mcp.lounge_access.deployment.api_client import LoungeAccessClient

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

def get_lounges_with_access_rules(
    airport_code: str, 
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enhanced to automatically apply user preferences if user_id provided
    """
    try:
        if not api_client:
            api_client = LoungeAccessClient()
            
        print(f"[MCP_HANDLER] Getting lounges for {airport_code}, user: {user_id or 'guest'}")
        
        # Get basic lounge data
        result = api_client.get_lounges_by_airport(airport_code)
        
        # If user provided, enhance with personalization
        if user_id:
            try:
                # Get user profile
                user_profile = api_client.get_user(user_id)
                if user_profile and 'preferences' in user_profile:
                    # Apply personalization to results
                    result = apply_user_preferences(result, user_profile)
                    result['personalized'] = True
                    result['user_context'] = {
                        'username': user_profile.get('name', 'User'),
                        'memberships': user_profile.get('memberships', []),
                        'home_airport': user_profile.get('home_airport')
                    }
            except Exception as e:
                print(f"[MCP_HANDLER] Personalization failed, using basic results: {e}")
                result['personalized'] = False
        
        return result
        
    except Exception as e:
        error_msg = f"Error getting lounges: {str(e)}"
        print(f"[MCP_HANDLER] ERROR: {error_msg}")
        return {"error": error_msg, "airport": airport_code}

def apply_user_preferences(lounge_data: dict, user_profile: dict) -> dict:
    """Simple preference application - just add user context to response"""
    
    preferences = user_profile.get('preferences', {})
    memberships = user_profile.get('memberships', [])
    
    # Add user-specific context to each lounge
    for lounge in lounge_data.get('lounges', []):
        # Check access with user's memberships
        lounge_providers = lounge.get('access_providers', [])
        lounge['user_can_access'] = any(
            membership.lower() in provider.lower() 
            for membership in memberships 
            for provider in lounge_providers
        )
        
        # Simple preference matching
        priority_amenities = preferences.get('priority_amenities', [])
        lounge_amenities = lounge.get('amenities', [])
        
        matched_amenities = [
            amenity for amenity in lounge_amenities 
            if any(pref.lower() in amenity.lower() for pref in priority_amenities)
        ]
        lounge['matches_preferences'] = matched_amenities
        
        # Add simple recommendation score
        score = 0
        if lounge['user_can_access']:
            score += 50
        score += len(matched_amenities) * 10
        score += lounge.get('rating', 0) * 5
        
        lounge['recommendation_score'] = score
    
    # Sort lounges by recommendation score
    lounge_data['lounges'] = sorted(
        lounge_data.get('lounges', []), 
        key=lambda x: x.get('recommendation_score', 0), 
        reverse=True
    )
    
    return lounge_data

def get_lounges_with_access_rules1(airport, api_client, user_id=None):
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
    


