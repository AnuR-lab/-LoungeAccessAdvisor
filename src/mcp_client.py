import requests
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient


class McpClient:
    """
    Client for interacting with the Agent Core Gateway API.
    This class provides methods to authenticate with the AgentCore Gateway and retrieve an MCP client instance.
    """

    def __init__(self, mcp_gateway_url, client_id=None, client_secret=None, token_url=None):
        """
        Initialize the AgentCoreGatewayClient.

        Args:
            mcp_gateway_url: URL of the Agent Core Gateway
            client_id: OAuth client ID (defaults to class constant if None)
            client_secret: OAuth client secret (defaults to class constant if None)
            token_url: OAuth token URL (defaults to class constant if None)
        """
        self.mcp_url = mcp_gateway_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token = None


    def _fetch_access_token(self):
        """
        Fetch an OAuth access token from the token endpoint.
        Returns:
            str: The access token
        """
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

