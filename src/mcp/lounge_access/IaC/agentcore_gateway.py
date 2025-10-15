"""
IaC: Create an AgentCore Gateway with Cognito Authorizer and Lambda Target
"""

from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import logging
import json

aws_region = 'us-east-1'


# setup the client
def get_agentcore_toolkit_client(region_name=aws_region):
    client = GatewayClient(region_name=aws_region)
    client.logger.setLevel(logging.DEBUG)
    return client

def get_target_payload(file_name=None):
    with open(file_name, 'r') as file:
        return json.load(file)

if __name__ == "__main__":
    client = get_agentcore_toolkit_client(aws_region)

    # create cognito authorizer
    cognito_response = client.create_oauth_authorizer_with_cognito("LoungeAccessMCPServerAuth")

    # create the gateway
    gateway = client.create_mcp_gateway(name="lounge-access-mcp-server",
                                        role_arn=None,
                                        authorizer_config=cognito_response["authorizer_config"])

    # create a lambda target
    target_payload = get_target_payload("./target_payload.json")
    lambda_target = client.create_mcp_gateway_target(gateway=gateway,
                                                     target_type="lambda",
                                                     target_payload=target_payload)

    print(f"MCP Endpoint: {gateway}")
    print(f"OAuth Credentials:")
    print(f"  Client ID: {cognito_response['client_info']['client_id']}")
    print(f"  Scope: {cognito_response['client_info']['scope']}")


