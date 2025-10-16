"""
This module defines tools that interact with an external API client.
Enhanced with flight information for context-aware lounge recommendations.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import FlightService with Lambda compatibility
try:
    from flight_service import FlightService
except ImportError:
    import flight_service
    FlightService = flight_service.FlightService

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


def get_flight_aware_lounge_recommendations(
    flight_number: str,
    departure_date: str,
    user_memberships: List[str],
    api_client,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get intelligent lounge recommendations based on specific flight information.
    
    Args:
        flight_number (str): Flight number (e.g., 'AA123')
        departure_date (str): Departure date in YYYY-MM-DD format
        user_memberships (List[str]): User's credit cards and loyalty memberships
        api_client: The API client instance for lounge data
        preferences (dict, optional): User preferences (quiet zones, food, etc.)
        
    Returns:
        dict: Flight-aware lounge recommendations with timing and logistics
    """
    try:
        flight_service = FlightService()
        
        # Get real-time flight information
        flight_info = flight_service.get_flight_status(flight_number, departure_date)
        
        if flight_info.get("status") != "found":
            return {
                "flight_number": flight_number,
                "status": "flight_not_found",
                "message": "Could not retrieve flight information",
                "recommendations": []
            }
        
        departure_airport = flight_info["departure"]["airport"]
        departure_terminal = flight_info["departure"].get("terminal")
        scheduled_departure = flight_info["departure"]["scheduled_time"]
        estimated_departure = flight_info["departure"].get("estimated_time", scheduled_departure)
        
        # Get lounges at departure airport
        lounges_data = api_client.get_lounges_by_airport(departure_airport)
        
        if not lounges_data or not lounges_data.get("lounges"):
            return {
                "flight_number": flight_number,
                "departure_airport": departure_airport,
                "status": "no_lounges_found",
                "recommendations": []
            }
        
        # Calculate optimal lounge timing
        departure_time = datetime.fromisoformat(estimated_departure.replace('Z', '+00:00'))
        current_time = datetime.now(departure_time.tzinfo)
        
        # Recommend arriving at gate 45 minutes before departure for domestic, 60 for international
        gate_arrival_buffer = timedelta(minutes=60)  # Conservative estimate
        latest_lounge_exit = departure_time - gate_arrival_buffer
        
        # Filter and rank lounges
        recommendations = []
        
        for lounge in lounges_data.get("lounges", []):
            # Check access eligibility
            lounge_providers = lounge.get("access_providers", [])
            user_access = []
            
            for membership in user_memberships:
                for provider in lounge_providers:
                    if membership.lower() in provider.lower():
                        user_access.append(provider)
            
            if not user_access:
                continue  # Skip lounges user can't access
            
            # Calculate recommendation score
            score = 0
            reasons = []
            
            # Terminal proximity bonus
            lounge_terminal = lounge.get("terminal", "")
            if departure_terminal and lounge_terminal == departure_terminal:
                score += 50
                reasons.append(f"Same terminal ({departure_terminal})")
            elif lounge_terminal:
                score += 20
                reasons.append(f"Terminal {lounge_terminal}")
            
            # Timing considerations
            lounge_hours = lounge.get("hours", "")
            if lounge_hours:
                # Simple check if lounge is likely open (would need more sophisticated parsing)
                score += 10
                reasons.append("Operating hours available")
            
            # Amenity matching
            amenities = lounge.get("amenities", [])
            if preferences:
                if preferences.get("quiet") and any("quiet" in amenity.lower() for amenity in amenities):
                    score += 15
                    reasons.append("Quiet zones available")
                if preferences.get("food") and any("buffet" in amenity.lower() or "dining" in amenity.lower() for amenity in amenities):
                    score += 15
                    reasons.append("Food service available")
                if preferences.get("wifi") and any("wifi" in amenity.lower() for amenity in amenities):
                    score += 10
                    reasons.append("WiFi available")
                if preferences.get("showers") and any("shower" in amenity.lower() for amenity in amenities):
                    score += 20
                    reasons.append("Shower facilities available")
            
            # Crowding considerations
            avg_wait = lounge.get("avg_wait_minutes", 0)
            if avg_wait < 10:
                score += 15
                reasons.append("Typically low wait times")
            elif avg_wait > 20:
                score -= 10
                reasons.append("May have longer wait times")
            
            # Rating bonus
            rating = lounge.get("rating", 0)
            if rating >= 4.5:
                score += 20
                reasons.append("Highly rated lounge")
            elif rating >= 4.0:
                score += 10
                reasons.append("Well-rated lounge")
            
            recommendation = {
                "lounge": lounge,
                "access_methods": user_access,
                "recommendation_score": score,
                "reasons": reasons,
                "timing": {
                    "latest_entry": (latest_lounge_exit - timedelta(minutes=30)).isoformat(),
                    "latest_exit": latest_lounge_exit.isoformat(),
                    "recommended_duration": "1-2 hours"
                }
            }
            
            recommendations.append(recommendation)
        
        # Sort by recommendation score
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return {
            "flight_number": flight_number,
            "departure_airport": departure_airport,
            "departure_terminal": departure_terminal,
            "scheduled_departure": scheduled_departure,
            "estimated_departure": estimated_departure,
            "status": "success",
            "total_lounges_available": len(recommendations),
            "recommendations": recommendations[:5],  # Top 5 recommendations
            "timing_advice": {
                "current_time": current_time.isoformat(),
                "latest_lounge_exit": latest_lounge_exit.isoformat(),
                "gate_arrival_recommendation": (departure_time - gate_arrival_buffer).isoformat()
            }
        }
        
    except Exception as e:
        return {
            "flight_number": flight_number,
            "status": "error",
            "error": str(e),
            "recommendations": []
        }


def analyze_layover_lounge_strategy(
    connecting_flights: List[Dict[str, str]],
    user_memberships: List[str],
    api_client,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze multi-flight itinerary and recommend optimal lounge strategy for layovers.
    
    Args:
        connecting_flights: List of flight segments with flight_number, departure_date
        user_memberships: User's access credentials
        api_client: API client for lounge data
        preferences: User preferences
        
    Returns:
        dict: Comprehensive layover lounge strategy
    """
    try:
        flight_service = FlightService()
        layover_strategies = []
        
        for i in range(len(connecting_flights) - 1):
            current_flight = connecting_flights[i]
            next_flight = connecting_flights[i + 1]
            
            # Get flight information
            current_info = flight_service.get_flight_status(
                current_flight["flight_number"], 
                current_flight["departure_date"]
            )
            next_info = flight_service.get_flight_status(
                next_flight["flight_number"],
                next_flight["departure_date"]
            )
            
            if (current_info.get("status") != "found" or 
                next_info.get("status") != "found"):
                continue
            
            # Calculate layover time
            arrival_time = datetime.fromisoformat(
                current_info["arrival"]["scheduled_time"].replace('Z', '+00:00')
            )
            departure_time = datetime.fromisoformat(
                next_info["departure"]["scheduled_time"].replace('Z', '+00:00')
            )
            
            layover_duration = departure_time - arrival_time
            
            # Get connection airport lounges
            connection_airport = current_info["arrival"]["airport"]
            lounges_data = api_client.get_lounges_by_airport(connection_airport)
            
            strategy = {
                "connection_airport": connection_airport,
                "arrival_flight": current_flight["flight_number"],
                "departure_flight": next_flight["flight_number"],
                "layover_duration": str(layover_duration),
                "layover_minutes": int(layover_duration.total_seconds() / 60),
                "arrival_terminal": current_info["arrival"].get("terminal"),
                "departure_terminal": next_info["departure"].get("terminal"),
                "recommendation": "no_time"  # Default
            }
            
            # Determine strategy based on layover duration
            layover_minutes = strategy["layover_minutes"]
            
            if layover_minutes < 90:
                strategy["recommendation"] = "no_lounge"
                strategy["advice"] = "Layover too short for lounge visit - proceed directly to next gate"
            elif layover_minutes < 180:
                strategy["recommendation"] = "quick_visit"
                strategy["advice"] = "Quick lounge visit possible - choose lounge closest to departure gate"
                # Find closest lounges
                if lounges_data and lounges_data.get("lounges"):
                    strategy["suggested_lounges"] = _find_quick_access_lounges(
                        lounges_data["lounges"], 
                        user_memberships,
                        next_info["departure"].get("terminal")
                    )
            else:
                strategy["recommendation"] = "full_experience"
                strategy["advice"] = "Sufficient time for full lounge experience"
                # Get full recommendations
                if lounges_data and lounges_data.get("lounges"):
                    strategy["suggested_lounges"] = _rank_lounges_for_layover(
                        lounges_data["lounges"],
                        user_memberships,
                        preferences,
                        layover_minutes
                    )
            
            layover_strategies.append(strategy)
        
        return {
            "status": "success",
            "total_connections": len(layover_strategies),
            "layover_strategies": layover_strategies
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "layover_strategies": []
        }


def _find_quick_access_lounges(lounges: List[Dict], memberships: List[str], departure_terminal: str) -> List[Dict]:
    """Helper function to find lounges suitable for quick visits"""
    quick_lounges = []
    
    for lounge in lounges:
        # Check access
        lounge_providers = lounge.get("access_providers", [])
        has_access = any(
            membership.lower() in provider.lower() 
            for membership in memberships 
            for provider in lounge_providers
        )
        
        if not has_access:
            continue
        
        # Prefer same terminal
        score = 0
        if lounge.get("terminal") == departure_terminal:
            score += 50
        
        # Prefer low wait times
        if lounge.get("avg_wait_minutes", 0) < 15:
            score += 20
        
        quick_lounges.append({
            "lounge": lounge,
            "quick_visit_score": score,
            "estimated_time_needed": "45-60 minutes"
        })
    
    return sorted(quick_lounges, key=lambda x: x["quick_visit_score"], reverse=True)[:3]


def _rank_lounges_for_layover(
    lounges: List[Dict], 
    memberships: List[str], 
    preferences: Optional[Dict], 
    layover_minutes: int
) -> List[Dict]:
    """Helper function to rank lounges for longer layovers"""
    ranked_lounges = []
    
    for lounge in lounges:
        # Check access
        lounge_providers = lounge.get("access_providers", [])
        has_access = any(
            membership.lower() in provider.lower() 
            for membership in memberships 
            for provider in lounge_providers
        )
        
        if not has_access:
            continue
        
        score = 0
        amenity_matches = []
        
        # Amenity scoring
        amenities = lounge.get("amenities", [])
        if preferences:
            if preferences.get("food") and any("buffet" in a.lower() for a in amenities):
                score += 20
                amenity_matches.append("Food service")
            if preferences.get("showers") and any("shower" in a.lower() for a in amenities):
                score += 25
                amenity_matches.append("Shower facilities")
            if preferences.get("quiet") and any("quiet" in a.lower() for a in amenities):
                score += 15
                amenity_matches.append("Quiet zones")
        
        # Rating bonus
        rating = lounge.get("rating", 0)
        score += rating * 10
        
        ranked_lounges.append({
            "lounge": lounge,
            "layover_score": score,
            "amenity_matches": amenity_matches,
            "recommended_duration": f"{min(layover_minutes - 60, 180)} minutes"
        })
    
    return sorted(ranked_lounges, key=lambda x: x["layover_score"], reverse=True)[:5]
