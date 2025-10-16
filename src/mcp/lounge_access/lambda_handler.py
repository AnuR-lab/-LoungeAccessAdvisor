import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from mcp_handler import (
    get_user, 
    get_lounges_with_access_rules,
    get_flight_aware_lounge_recommendations,
    analyze_layover_lounge_strategy
)
from api_client import LoungeAccessClient


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def lambda_handler(event, context):
    """
    Enhanced Lambda function to handle flight-aware lounge tool invocations.
    
    Supports both basic lounge lookup and advanced flight-aware recommendations.
    
    Args:
        event (dict): The event payload containing tool invocation details.
        context: Lambda context object.
        
    Returns:
        dict: A response dictionary with status code and result or error message.
    """
    
    # Enhanced logging for debugging
    print(f"[LAMBDA_HANDLER] ===== NEW REQUEST =====")
    print(f"[LAMBDA_HANDLER] Request ID: {context.request_id}")
    print(f"[LAMBDA_HANDLER] Function ARN: {context.invoked_function_arn}")
    print(f"[LAMBDA_HANDLER] Received event: {json.dumps(event)}")
    
    # Extract tool name from context
    tool_name = None
    if context.client_context and context.client_context.custom:
        tool_name = context.client_context.custom.get("bedrockAgentCoreToolName")
    tool = tool_name.split("___")[-1] if tool_name and "___" in tool_name else tool_name
    
    print(f"[LAMBDA_HANDLER] Extracted tool: {tool}")
    
    # Parse payload - handle different event formats
    if 'body' in event and isinstance(event['body'], str):
        payload = json.loads(event['body'])
    elif 'body' in event and isinstance(event['body'], dict):
        payload = event['body']
    else:
        payload = event
    
    print(f"[LAMBDA_HANDLER] Parsed payload: {json.dumps(payload)}")
    
    # Initialize API client
    lounge_access_client = LoungeAccessClient()
    
    try:
        match tool:
            # ===== BASIC LOUNGE TOOLS =====
            case "search_lounges" | "getLoungesWithAccessRules":
                return handle_search_lounges(payload, lounge_access_client)
            
            case "getUser":
                return handle_get_user(payload, lounge_access_client)
            
            # ===== FLIGHT-AWARE TOOLS =====
            case "getFlightLoungeRecs":
                return handle_flight_aware_recommendations(payload, lounge_access_client)
            
            case "analyzeLayoverStrategy":
                return handle_layover_strategy(payload, lounge_access_client)
            
            case "searchFlightsOptimized":
                return handle_optimized_flight_search(payload, lounge_access_client)
            
            case _:
                error_msg = f"Unknown tool: {tool}"
                print(f"[LAMBDA_HANDLER] ERROR: {error_msg}")
                return {
                    "statusCode": 400, 
                    "body": json.dumps({"error": error_msg, "available_tools": [
                        "getUser", "getLoungesWithAccessRules", "getFlightLoungeRecs", 
                        "analyzeLayoverStrategy", "searchFlightsOptimized"
                    ]})
                }
                
    except Exception as e:
        error_msg = f"Lambda handler error: {str(e)}"
        print(f"[LAMBDA_HANDLER] ERROR: {error_msg}")
        import traceback
        print(f"[LAMBDA_HANDLER] Traceback: {traceback.format_exc()}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }


def handle_search_lounges(payload: Dict[str, Any], client: LoungeAccessClient) -> Dict[str, Any]:
    """Handle basic lounge search requests"""
    print(f"[SEARCH_LOUNGES] Processing request: {payload}")
    
    airport = payload.get("airport")
    if not airport:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameter: airport"})
        }
    
    try:
        result = get_lounges_with_access_rules(airport, client)
        print(f"[SEARCH_LOUNGES] Success: Found {result.get('total_lounges', 0)} lounges")
        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}, cls=DateTimeEncoder)
        }
    except Exception as e:
        error_msg = f"Search lounges error: {str(e)}"
        print(f"[SEARCH_LOUNGES] ERROR: {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }


def handle_get_user(payload: Dict[str, Any], client: LoungeAccessClient) -> Dict[str, Any]:
    """Handle user profile requests"""
    print(f"[GET_USER] Processing request: {payload}")
    
    user_id = payload.get("user_id")
    if not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing required parameter: user_id"})
        }
    
    try:
        result = get_user(user_id, client)
        print(f"[GET_USER] Success: Retrieved user {user_id}")
        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}, cls=DateTimeEncoder)
        }
    except Exception as e:
        error_msg = f"Get user error: {str(e)}"
        print(f"[GET_USER] ERROR: {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }


def handle_flight_aware_recommendations(payload: Dict[str, Any], client: LoungeAccessClient) -> Dict[str, Any]:
    """Handle flight-aware lounge recommendations"""
    print(f"[FLIGHT_LOUNGE_RECS] Processing request: {payload}")
    
    # Validate required parameters
    flight_number = payload.get("flight_number")
    departure_date = payload.get("departure_date")
    user_id = payload.get("user_id")
    
    if not all([flight_number, departure_date, user_id]):
        missing = [p for p in ["flight_number", "departure_date", "user_id"] 
                  if not payload.get(p)]
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Missing required parameters: {', '.join(missing)}"
            })
        }
    
    try:
        # Extract optional parameters
        preferences = payload.get("preferences", {})
        operational_suffix = payload.get("operational_suffix")
        
        # Call the enhanced API client method
        result = client.get_flight_aware_lounge_recommendations(
            flight_number=flight_number,
            departure_date=departure_date,
            user_id=user_id,
            preferences=preferences
        )
        
        print(f"[FLIGHT_LOUNGE_RECS] Success: {result.get('status', 'unknown')}")
        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}, cls=DateTimeEncoder)
        }
        
    except Exception as e:
        error_msg = f"Flight-aware recommendations error: {str(e)}"
        print(f"[FLIGHT_LOUNGE_RECS] ERROR: {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }


def handle_layover_strategy(payload: Dict[str, Any], client: LoungeAccessClient) -> Dict[str, Any]:
    """Handle layover strategy analysis"""
    print(f"[LAYOVER_STRATEGY] Processing request: {payload}")
    
    # Validate required parameters
    connecting_flights = payload.get("connecting_flights", [])
    user_id = payload.get("user_id")
    
    if not connecting_flights or not user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Missing required parameters: connecting_flights (array), user_id"
            })
        }
    
    # Validate flight format
    for i, flight in enumerate(connecting_flights):
        if not flight.get("flight_number") or not flight.get("departure_date"):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Flight {i+1} missing required fields: flight_number, departure_date"
                })
            }
    
    try:
        preferences = payload.get("preferences", {})
        
        # Call the enhanced API client method
        result = client.analyze_multi_flight_lounge_strategy(
            flights=connecting_flights,
            user_id=user_id,
            preferences=preferences
        )
        
        print(f"[LAYOVER_STRATEGY] Success: Analyzed {len(connecting_flights)} flights")
        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}, cls=DateTimeEncoder)
        }
        
    except Exception as e:
        error_msg = f"Layover strategy error: {str(e)}"
        print(f"[LAYOVER_STRATEGY] ERROR: {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }


def handle_optimized_flight_search(payload: Dict[str, Any], client: LoungeAccessClient) -> Dict[str, Any]:
    """Handle lounge-optimized flight search"""
    print(f"[OPTIMIZED_SEARCH] Processing request: {payload}")
    
    # Validate required parameters
    origin = payload.get("origin")
    destination = payload.get("destination")
    departure_date = payload.get("departure_date")
    user_id = payload.get("user_id")
    
    if not all([origin, destination, departure_date, user_id]):
        missing = [p for p in ["origin", "destination", "departure_date", "user_id"] 
                  if not payload.get(p)]
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Missing required parameters: {', '.join(missing)}"
            })
        }
    
    try:
        return_date = payload.get("return_date")
        
        # Call the enhanced API client method
        result = client.search_flights_for_lounge_optimization(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            user_id=user_id,
            return_date=return_date
        )
        
        flight_count = len(result.get("flights", []))
        print(f"[OPTIMIZED_SEARCH] Success: Found {flight_count} flights")
        return {
            "statusCode": 200,
            "body": json.dumps({"result": result}, cls=DateTimeEncoder)
        }
        
    except Exception as e:
        error_msg = f"Optimized flight search error: {str(e)}"
        print(f"[OPTIMIZED_SEARCH] ERROR: {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }

