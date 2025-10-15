"""
This module defines tools that interact with an external API client.
"""

def tool_example_1(api_client):
    """
    Example tool that interacts with the API client to retrieve a list of domains.
    """
    domains = api_client.get_tool_example_1()
    if domains:
        return [{"name": domain['name'], "id": domain['id']} for domain in domains]
    return []


def tool_example_2(parameter_1, parameter_2, api_client):
    """
    Example tool that takes two parameters and interacts with the API client.
    """
    #assets = datazone_client.get_assets(domain_id=domain_id, project_id=project_id)
    tool_response = api_client.get_tool_example_2(parameter_1, parameter_2)
    
    if tool_response:
        return {"parameter_1": parameter_1, "parameter_2": parameter_2, "tool_response": tool_response}
    return {"parameter_1": parameter_1, "parameter_2": parameter_2, "tool_response": None}


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

