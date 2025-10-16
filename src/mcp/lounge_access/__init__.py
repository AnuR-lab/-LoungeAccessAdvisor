"""
Lounge Access MCP Package

This package provides MCP (Model Context Protocol) tools for lounge access recommendations
and flight-aware lounge optimization.
"""

# Make key components available at package level
# Use absolute imports for Lambda compatibility
try:
    from api_client import LoungeAccessClient
except ImportError:
    import api_client
    LoungeAccessClient = api_client.LoungeAccessClient

try:
    from mcp_handler import (
        get_user,
        get_lounges_with_access_rules, 
        get_flight_aware_lounge_recommendations,
        analyze_layover_lounge_strategy
    )
except ImportError:
    import mcp_handler
    get_user = mcp_handler.get_user
    get_lounges_with_access_rules = mcp_handler.get_lounges_with_access_rules
    get_flight_aware_lounge_recommendations = mcp_handler.get_flight_aware_lounge_recommendations
    analyze_layover_lounge_strategy = mcp_handler.analyze_layover_lounge_strategy

__version__ = "1.0.0"
__all__ = [
    'LoungeAccessClient',
    'get_user', 
    'get_lounges_with_access_rules',
    'get_flight_aware_lounge_recommendations',
    'analyze_layover_lounge_strategy'
]