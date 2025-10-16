import json
import os
from datetime import datetime

from mcp_handler import tool_example_1, tool_example_2, get_user, get_lounges_with_access_rules
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

        case _:
            return {"statusCode": 400, "body": json.dumps({"error": "Unknown tool"})}

