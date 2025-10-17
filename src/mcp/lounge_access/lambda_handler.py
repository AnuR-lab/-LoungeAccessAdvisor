import json
import os
from datetime import datetime

from mcp_handler import get_user, get_lounges_with_access_rules, get_flight_schedule
from api_client import LoungeAccessClient


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def lambda_handler(event, context):
    """
    Lambda function to handle tool invocations based on the tool name provided in the event.
        Args:
            event (dict): The event payload containing tool invocation details.
            context: Lambda context object.
        Returns:
            dict: A response dictionary with status code and result or error message.
    """

    tool_name = None
    if context.client_context and context.client_context.custom:
        tool_name = context.client_context.custom.get("bedrockAgentCoreToolName")
    tool = tool_name.split("___")[-1] if tool_name and "___" in tool_name else tool_name

    payload = event

    lounge_access_client = LoungeAccessClient()

    print(f"tool: {tool}, payload: {payload}")

    match tool:
        case "search_lounges":
            airport = payload.get("airport", None)
            if not airport:
                return {"statusCode": 400,
                        "body": json.dumps({"error": "Missing required parameter: airport"})}
            try:
                result = get_lounges_with_access_rules(airport,lounge_access_client)
                return {
                    "statusCode": 200,
                    "body": json.dumps({"result": result}, cls=DateTimeEncoder)
                }
            except Exception as e:
                return {"statusCode": 500,
                        "body": json.dumps({"error": str(e)})}
        case "get_user":
            user_id = payload.get("user_id", None)
            if not user_id:
                return {"statusCode": 400, "body": json.dumps({"error": "Missing required parameter: user_id"})}
            try:
                result = get_user(user_id, lounge_access_client)
                return {"statusCode": 200, "body": json.dumps({"result": result}, cls=DateTimeEncoder)}
            except ValueError as e:
                return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

        case "get_flight_schedule":
            # Required parameters
            carrier_code = payload.get("carrier_code", None)
            flight_number = payload.get("flight_number", None) 
            scheduled_departure_date = payload.get("scheduled_departure_date", None)
            
            if not carrier_code or not flight_number or not scheduled_departure_date:
                return {
                    "statusCode": 400,
                    "body": json.dumps({
                        "error": "Missing required parameters: carrier_code, flight_number, scheduled_departure_date"
                    })
                }
            
            # Optional parameter
            operational_suffix = payload.get("operational_suffix", None)
            
            try:
                result = get_flight_schedule(
                    carrier_code=carrier_code,
                    flight_number=flight_number,
                    scheduled_departure_date=scheduled_departure_date,
                    api_client=lounge_access_client,
                    operational_suffix=operational_suffix
                )
                return {
                    "statusCode": 200,
                    "body": json.dumps({"result": result}, cls=DateTimeEncoder)
                }
            except Exception as e:
                return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

        case _:
            return {"statusCode": 400, "body": json.dumps({"error": "Unknown tool"})}

