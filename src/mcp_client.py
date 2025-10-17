import json
import os

import requests
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient


class McpClient:
    """
    Client for interacting with the Agent Core Gateway API.
    This class provides methods to authenticate with the AgentCore Gateway and retrieve an MCP client instance.
    """

    def __init__(self, config_file="./etc/gateway_config.json"):
        """
        Initialize the AgentCoreGatewayClient.

        Args:
            mcp_gateway_url: URL of the Agent Core Gateway
            client_id: OAuth client ID (defaults to class constant if None)
            client_secret: OAuth client secret (defaults to
            class constant if None)
            token_url: OAuth token URL (defaults to class constant if None)
        """

        self.mcp_gateway_config = self._get_config(config_file)

        if self.mcp_gateway_config:
            self.mcp_url = self.mcp_gateway_config.get("gateway_url", None)
            self.client_id = self.mcp_gateway_config["client_info"]["client_id"]
            # Prefer secret from environment; fall back to config if present (for backward compatibility)
            self.client_secret = os.getenv("MCP_CLIENT_SECRET") or \
                                 self.mcp_gateway_config["client_info"].get("client_secret")
            self.token_url = self.mcp_gateway_config["client_info"]["token_endpoint"]

        self.access_token = None


    def _get_config(self, config_file="./etc/gateway_config.json"):
        """
        Load configuration from a JSON file.
        Args:
            config_file: Path to the configuration file
        Returns:
            dict: Configuration data
        """

        mcp_gateway_config = None
        try:
            with open(config_file, "r") as f:
                mcp_gateway_config = json.load(f)
        except FileNotFoundError:
            print("❌ Error: gateway_config.json not found!")

        return mcp_gateway_config


    def _fetch_access_token(self):
        """
        Fetch an OAuth access token from the token endpoint.
        Returns:
            str: The access token
        """
        if not self.client_secret or str(self.client_secret).startswith("${"):
            raise RuntimeError("MCP_CLIENT_SECRET environment variable is not set. Please export MCP_CLIENT_SECRET before running.")
        response = requests.post(
            self.token_url,
            data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(
                client_id=self.client_id,
                client_secret=self.client_secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        return response.json()['access_token']

    def get_mcp_client(self) -> MCPClient:
        """
        Get the MCP client for the Agent Core Gateway.
        Returns:
            MCPClient: An instance of the MCPClient configured for the Agent Core Gateway.
        """
        self.access_token = self._fetch_access_token()

        mcp_client = MCPClient(transport_callable=lambda: streamablehttp_client(url=self.mcp_url,
                                                                                headers={"Authorization": f"Bearer {self.access_token}"}))
        return mcp_client

