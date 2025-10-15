import json
import os
from datetime import datetime

from mcp_handler import tool_example_1, tool_example_2
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
        case "tool_example_1":
            result = tool_example_1(lounge_access_client)
            return {"statusCode": 200, "body": json.dumps({"result": result})}

        case "tool_example_2":
            parameter_1 = payload.get("parameter_1", None)
            parameter_2 = payload.get("parameter_2", None)
            if not parameter_1 and not parameter_2:
                return {"statusCode": 400, "body": json.dumps({"error": "Missing input parameters"})}
            try:
                result = tool_example_2(parameter_1, parameter_2, lounge_access_client)
                return {"statusCode": 200, "body": json.dumps({"result": result})}
            except ValueError as e:
                return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

        case _:
            return {"statusCode": 400, "body": json.dumps({"error": "Unknown tool"})}

